"""Packaging tests for portable-catalogue-authentication T1 and T5.

Anchored at the repository root via ``Path(__file__).resolve().parents[2]``.
Reads ``packs/`` and builds wheels, so it cannot live in the agentbundle sdist
package suite. CI registration: a named step above the bulk
``pytest tests/ -q`` step in ``.github/workflows/build-check.yml``.

Spec mapping: AC-0001 (credbroker half), AC-0001 (agentbundle half),
AC-0002, AC-0003, AC-0018.

Verification mode: TDD package and integration.
"""

from __future__ import annotations

import contextlib
import hashlib
import http.server
import inspect
import io
import json
import os
import pathlib
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import threading
import zipfile

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CREDBROKER_PKG = REPO_ROOT / "packages" / "credbroker"
AGENTBUNDLE_PKG = REPO_ROOT / "packages" / "agentbundle"
PACKS_DIR = REPO_ROOT / "packs"
VENDORED_FLOOR = PACKS_DIR / "credential-brokers" / ".apm" / "user-libs" / "credbroker"


def _clean_env() -> dict[str, str]:
    """Return the current environment without PYTHONPATH.

    Subprocess calls that test package isolation must not inherit the test
    runner's ``PYTHONPATH``, which typically includes ``packages/agentbundle``
    and ``packages/credbroker`` source trees and would falsify the check.
    """
    return {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}


# ── Python 3.11 interpreter resolution ───────────────────────────────────────


def _find_python311() -> str:
    """Return a path to a Python 3.11 interpreter.

    Resolution order:
    1. ``PORTABLE_CATALOGUE_AUTH_PYTHON`` env var (explicit override).
    2. ``sys.executable`` when it is already Python 3.11.
    3. ``python3.11`` found on ``PATH``.
    4. ``pytest.fail`` with a clear message — never silently skip.

    Returns:
        Absolute path to a Python 3.11 interpreter.
    """
    override = os.environ.get("PORTABLE_CATALOGUE_AUTH_PYTHON")
    if override:
        return override

    if sys.version_info[:2] == (3, 11):
        return sys.executable

    found = shutil.which("python3.11")
    if found:
        # Verify the executable works — pyenv shims may exist but not be active.
        probe = subprocess.run(
            [found, "--version"], capture_output=True, text=True, check=False
        )
        if probe.returncode == 0 and "3.11" in (probe.stdout + probe.stderr):
            return found

    pytest.fail(
        "Python 3.11 not found. Set the PORTABLE_CATALOGUE_AUTH_PYTHON "
        "environment variable to a Python 3.11 interpreter path, or ensure "
        "python3.11 is on PATH. The CI gate uses Python 3.11 (gate-main's "
        "actions/setup-python step sets python-version: '3.11')."
    )


# ── Wheel build helper ────────────────────────────────────────────────────────


def _build_credbroker_wheel(dest: pathlib.Path) -> pathlib.Path:
    """Build the credbroker wheel into ``dest`` without network access.

    Uses ``pip wheel --no-deps --no-build-isolation`` so the already-installed
    setuptools is reused and no index is contacted.

    Returns:
        Path to the built ``.whl`` file.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "--no-index",
            "--wheel-dir",
            str(dest),
            str(CREDBROKER_PKG),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"credbroker wheel build failed (exit {result.returncode}):\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    wheels = list(dest.glob("credbroker-*.whl"))
    if not wheels:
        pytest.fail(f"No credbroker wheel found in {dest!r} after build")
    return wheels[0]


def _wheel_metadata_version(wheel: pathlib.Path) -> str:
    """Read the ``Version:`` field from the wheel's METADATA file."""
    with zipfile.ZipFile(wheel) as zf:
        meta_names = [n for n in zf.namelist() if n.endswith("/METADATA") or n == "METADATA"]
        # The wheel name prefix matches the dist-info directory name.
        for name in meta_names:
            content = zf.read(name).decode("utf-8")
            m = re.search(r"^Version:\s*(.+)$", content, re.MULTILINE)
            if m:
                return m.group(1).strip()
    pytest.fail(f"Could not read Version: from wheel METADATA in {wheel!r}")


def _build_agentbundle_wheel(dest: pathlib.Path) -> pathlib.Path:
    """Build the agentbundle wheel into ``dest`` without network access.

    Uses ``pip wheel --no-deps --no-build-isolation`` so the already-installed
    setuptools is reused and no index is contacted.

    Returns:
        Path to the built ``.whl`` file.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "--no-index",
            "--wheel-dir",
            str(dest),
            str(AGENTBUNDLE_PKG),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"agentbundle wheel build failed (exit {result.returncode}):\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    wheels = list(dest.glob("agentbundle-*.whl"))
    if not wheels:
        pytest.fail(f"No agentbundle wheel found in {dest!r} after build")
    return wheels[0]


def _venv_pip_exe(venv_dir: pathlib.Path) -> str:
    """Return the pip executable path inside *venv_dir*."""
    for candidate in (
        venv_dir / "bin" / "pip",
        venv_dir / "bin" / "pip3",
        venv_dir / "Scripts" / "pip.exe",
    ):
        if candidate.exists():
            return str(candidate)
    pytest.fail(f"Could not find pip executable in venv {venv_dir!r}")


def _venv_python_exe(venv_dir: pathlib.Path) -> str:
    """Return the Python executable path inside *venv_dir*."""
    for candidate in (
        venv_dir / "bin" / "python3",
        venv_dir / "bin" / "python",
        venv_dir / "Scripts" / "python.exe",
    ):
        if candidate.exists():
            return str(candidate)
    pytest.fail(f"Could not find Python executable in venv {venv_dir!r}")


def _venv_agentbundle_exe(venv_dir: pathlib.Path) -> str:
    """Return the agentbundle console script path inside *venv_dir*."""
    for candidate in (
        venv_dir / "bin" / "agentbundle",
        venv_dir / "Scripts" / "agentbundle.exe",
    ):
        if candidate.exists():
            return str(candidate)
    pytest.fail(
        f"agentbundle console script not found in venv {venv_dir!r} — "
        "pip install may have failed or not created the entry point"
    )


def _minimal_catalogue_archive() -> tuple[bytes, str]:
    """Return ``(archive_bytes, sha256_hex)`` for a minimal installable catalogue.

    The archive contains one pack (``test-pack/``) with a valid ``pack.toml``
    and a stub skill.  The pack declares ``[pack.adapter-contract] version = "0.8"``
    and ``[pack.install] default-scope = "repo" allowed-scopes = ["repo"]`` so
    that ``agentbundle install --pack test-pack`` at repo scope completes without
    scope-resolution errors.
    """
    pack_toml = (
        b"[pack]\n"
        b'name = "test-pack"\n'
        b'version = "1.0.0"\n'
        b"[pack.adapter-contract]\n"
        b'version = "0.8"\n'
        b"[pack.install]\n"
        b'default-scope = "repo"\n'
        b'allowed-scopes = ["repo"]\n'
    )

    skill_md = (
        b"---\n"
        b"name: test-skill\n"
        b"description: Minimal fixture skill for AC-0018.\n"
        b"---\n"
        b"Fixture skill for AC-0018.\n"
    )

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        info = tarfile.TarInfo("packs/test-pack/pack.toml")
        info.size = len(pack_toml)
        tf.addfile(info, io.BytesIO(pack_toml))

        info2 = tarfile.TarInfo(
            "packs/test-pack/.apm/skills/test-skill/SKILL.md"
        )
        info2.size = len(skill_md)
        tf.addfile(info2, io.BytesIO(skill_md))

    data = buf.getvalue()
    sha256_hex = hashlib.sha256(data).hexdigest()
    return data, sha256_hex


# ── Loopback HTTPS server for AC-0018 ────────────────────────────────────────


class _AuthServer(http.server.ThreadingHTTPServer):
    """ThreadingHTTPServer with daemon threads so tests don't hang on exit."""

    daemon_threads = True


class _AuthHandler(http.server.BaseHTTPRequestHandler):
    """Serve fixed routes; optionally require Basic auth; record all requests."""

    # Subclasses (created via ``type()``) set class-level attributes.
    routes: dict[str, bytes] = {}
    require_basic_auth: bool = False
    seen: list[tuple[str, str | None]] = []

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET: optionally enforce Basic auth, serve route or 404."""
        auth = self.headers.get("Authorization")
        self.seen.append((self.path, auth))

        if self.require_basic_auth and not (auth and auth.startswith("Basic ")):
            body = b"Unauthorized"
            self.send_response(401)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        body = self.routes.get(self.path)
        if body is None:
            err = b"not found"
            self.send_response(404)
            self.send_header("Content-Length", str(len(err)))
            self.end_headers()
            self.wfile.write(err)
            return

        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: D102
        pass  # Suppress access log to keep test output clean.


@contextlib.contextmanager
def _loopback_https(
    routes: dict[str, bytes],
    cert_path: pathlib.Path,
    key_path: pathlib.Path,
    *,
    require_basic_auth: bool = False,
):
    """Serve *routes* over loopback HTTPS; yield ``(base_url, handler_class)``.

    The handler class has a ``seen`` list of ``(path, Authorization)`` tuples
    recorded for every GET request.  ``base_url`` is
    ``"https://127.0.0.1:<port>/"``.  The server shuts down cleanly when the
    context exits.
    """
    handler_cls = type(
        "_BoundHandler",
        (_AuthHandler,),
        {
            "routes": dict(routes),
            "require_basic_auth": require_basic_auth,
            "seen": [],
        },
    )
    server = _AuthServer(("127.0.0.1", 0), handler_cls)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        yield f"https://127.0.0.1:{port}/", handler_cls
    finally:
        server.shutdown()
        server.server_close()


def _install_built_agentbundle(
    venv_dir: pathlib.Path, python311: str, both_wheels: pathlib.Path
) -> pathlib.Path:
    """Create *venv_dir* and install AgentBundle from *both_wheels* only (no index)."""
    result = subprocess.run(
        [python311, "-m", "venv", str(venv_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"venv creation failed: {result.stderr}")
    pip = _venv_pip_exe(venv_dir)
    install_result = subprocess.run(
        [
            pip,
            "install",
            "--no-index",
            f"--find-links={both_wheels}",
            "agentbundle",
        ],
        capture_output=True,
        text=True,
        env=_clean_env(),
        check=False,
    )
    if install_result.returncode != 0:
        pytest.fail(
            f"pip install agentbundle failed:\n"
            f"{install_result.stdout}\n{install_result.stderr}"
        )
    return venv_dir


# ── AC-0001 (credbroker half): wheel version agreement ───────────────────────


class TestCredbrokerWheelVersion:
    """Build the credbroker wheel and assert all version sources agree."""

    def test_wheel_version_agrees_with_pyproject_and_version_py(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Wheel METADATA version == pyproject version == version.py == 0.7.0.

        AC-0001 (credbroker half).
        """
        wheel = _build_credbroker_wheel(tmp_path)
        wheel_ver = _wheel_metadata_version(wheel)

        # pyproject.toml version.
        pyproject = CREDBROKER_PKG / "pyproject.toml"
        pyproject_text = pyproject.read_text(encoding="utf-8")
        pyproject_match = re.search(
            r'^version\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE
        )
        assert pyproject_match, "Could not find version in pyproject.toml"
        pyproject_ver = pyproject_match.group(1)

        # version.py.
        version_py = CREDBROKER_PKG / "credbroker" / "version.py"
        version_py_text = version_py.read_text(encoding="utf-8")
        version_py_match = re.search(
            r'^__version__\s*(?::\s*\S+\s*)?=\s*"([^"]+)"', version_py_text, re.MULTILINE
        )
        assert version_py_match, "Could not find __version__ in version.py"
        version_py_ver = version_py_match.group(1)

        assert wheel_ver == "0.7.0", (
            f"Wheel METADATA version is {wheel_ver!r}, expected 0.7.0"
        )
        assert pyproject_ver == "0.7.0", (
            f"pyproject.toml version is {pyproject_ver!r}, expected 0.7.0"
        )
        assert version_py_ver == "0.7.0", (
            f"version.py __version__ is {version_py_ver!r}, expected 0.7.0"
        )
        # Cross-check all three agree.
        assert wheel_ver == pyproject_ver == version_py_ver, (
            f"Version mismatch: wheel={wheel_ver!r} pyproject={pyproject_ver!r} "
            f"version.py={version_py_ver!r}"
        )


# ── AC-0002: isolated-install isolation tests ─────────────────────────────────


class TestIsolatedInstall:
    """Create clean venvs and prove package isolation boundaries.

    AC-0002: credential-aware skill surface works with only credbroker;
    neither package is importable in an ordinary-skill environment.
    """

    @pytest.fixture(scope="class")
    def python311(self) -> str:
        """Python 3.11 interpreter path (fails with clear message if absent)."""
        return _find_python311()

    @pytest.fixture(scope="class")
    def credbroker_wheel(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        """Built credbroker 0.7 wheel (built once per class)."""
        dest = tmp_path_factory.mktemp("wheel")
        return _build_credbroker_wheel(dest)

    def _make_venv(
        self, parent: pathlib.Path, python: str, name: str
    ) -> pathlib.Path:
        """Create a clean venv under ``parent / name``."""
        venv_dir = parent / name
        result = subprocess.run(
            [python, "-m", "venv", "--without-pip", str(venv_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.fail(
                f"venv creation failed (exit {result.returncode}):\n"
                f"{result.stderr}"
            )
        return venv_dir

    def _venv_python(self, venv_dir: pathlib.Path) -> str:
        """Return the Python executable inside the venv."""
        candidate = venv_dir / "bin" / "python3"
        if candidate.exists():
            return str(candidate)
        candidate = venv_dir / "Scripts" / "python.exe"
        if candidate.exists():
            return str(candidate)
        pytest.fail(f"Could not find Python executable in venv {venv_dir!r}")

    def _install_wheel_no_pip(
        self, wheel: pathlib.Path, venv_dir: pathlib.Path
    ) -> None:
        """Install a wheel into the venv by unpacking it into site-packages.

        Uses the stdlib ``zipfile`` module — no pip required so the venv can
        be created with ``--without-pip``.
        """
        # Find site-packages inside the venv (clean env: no PYTHONPATH).
        venv_python = self._venv_python(venv_dir)
        result = subprocess.run(
            [venv_python, "-c",
             "import site; print(site.getsitepackages()[0])"],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=True,
        )
        site_pkg = pathlib.Path(result.stdout.strip())
        site_pkg.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(wheel) as zf:
            for member in zf.infolist():
                # Skip the .dist-info directory (not needed for import).
                if ".dist-info/" in member.filename:
                    continue
                zf.extract(member, path=site_pkg)

    def test_credbroker_only_venv_resolves_public_surface(
        self,
        tmp_path: pathlib.Path,
        python311: str,
        credbroker_wheel: pathlib.Path,
    ) -> None:
        """credential-setup skill exits 3/stdin-not-tty in a credbroker-only venv.

        Runs
        ``packs/credential-brokers/.apm/skills/credential-setup/scripts/setup.py``
        inside a credbroker-only venv. With stdin closed (not a TTY) and a valid
        creds-schema.toml fixture, the script parses the schema via the public
        ``parse_schema`` surface and then hits the tty guard, exiting 3 with
        ``stdin-not-tty`` in stderr. The ``credbroker not found`` branch also
        exits 3, so the negative assertion distinguishes the two paths.
        agentbundle must not be importable in the same venv. AC-0002.
        """
        venv_dir = self._make_venv(tmp_path, python311, "credbroker_only")
        self._install_wheel_no_pip(credbroker_wheel, venv_dir)
        venv_python = self._venv_python(venv_dir)

        # Also verify the public resolve_http_access surface works in this venv.
        surface_script = (
            "from credbroker import ("
            "    resolve_http_access, AnonymousHttpAccess,"
            "    BearerHttpAccess, HttpAccessError,"
            "    load_credentials, CredentialsMissingError,"
            ")\n"
            "result = resolve_http_access("
            "    'https://catalogue.example.test/', env={}"
            ")\n"
            "assert isinstance(result, AnonymousHttpAccess), "
            "    f'Expected AnonymousHttpAccess, got {type(result)!r}'\n"
            "assert result.provider == 'anonymous'\n"
            "print('credbroker_surface_ok')\n"
        )
        surface_result = subprocess.run(
            [venv_python, "-c", surface_script],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=False,
        )
        assert surface_result.returncode == 0, (
            f"credbroker public surface failed in isolated venv:\n"
            f"stdout: {surface_result.stdout!r}\nstderr: {surface_result.stderr!r}"
        )
        assert "credbroker_surface_ok" in surface_result.stdout

        # Write a minimal creds-schema.toml fixture for namespace "example".
        # Format: [namespace] table + [[namespace.keys]] entry per required key.
        schema_path = tmp_path / "creds-schema.toml"
        schema_path.write_text(
            "[namespace]\n"
            'name = "example"\n'
            "\n"
            "[[namespace.keys]]\n"
            'name = "API_TOKEN"\n'
            'label = "Example API token"\n'
            "secret = true\n",
            encoding="utf-8",
        )

        # Run the credential-setup skill script with stdin closed (DEVNULL) and
        # HOME redirected to an empty tmp dir so ~/.agentbundle/lib cannot provide
        # a real user-level credbroker floor that would mask a missing-package bug.
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir(exist_ok=True)
        setup_script = (
            PACKS_DIR
            / "credential-brokers"
            / ".apm"
            / "skills"
            / "credential-setup"
            / "scripts"
            / "setup.py"
        )
        skill_env = {
            **_clean_env(),
            "HOME": str(fake_home),
            "USERPROFILE": str(fake_home),
        }
        setup_result = subprocess.run(
            [
                venv_python,
                str(setup_script),
                "example",
                "--schema-path",
                str(schema_path),
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            env=skill_env,
            check=False,
        )
        assert setup_result.returncode == 3, (
            f"setup.py expected exit 3 (stdin-not-tty), "
            f"got {setup_result.returncode}:\n"
            f"stdout: {setup_result.stdout!r}\nstderr: {setup_result.stderr!r}"
        )
        assert "stdin-not-tty" in setup_result.stderr, (
            f"stderr does not contain 'stdin-not-tty':\n{setup_result.stderr!r}"
        )
        # Negative assertion: distinguishes successful schema parse from the
        # "credbroker not installed" error path, which also exits 3.
        assert "credbroker not found" not in setup_result.stderr, (
            "stderr contains 'credbroker not found' — credbroker is not importable "
            f"in this venv:\n{setup_result.stderr!r}"
        )

        # Prove agentbundle is NOT importable in this venv.
        check_agentbundle = subprocess.run(
            [venv_python, "-c", "import agentbundle; print('SHOULD_NOT_REACH')"],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=False,
        )
        assert check_agentbundle.returncode != 0, (
            "agentbundle must not be importable in a credbroker-only venv "
            f"(got stdout: {check_agentbundle.stdout!r})"
        )
        assert "SHOULD_NOT_REACH" not in check_agentbundle.stdout

    def test_empty_venv_imports_neither_package(
        self,
        tmp_path: pathlib.Path,
        python311: str,
    ) -> None:
        """Ordinary (stdlib-only) skill runs in an empty venv; neither package importable.

        Runs
        ``packs/atlassian/.apm/skills/jira-defect-flow/scripts/branch_name.py``
        inside a venv with neither agentbundle nor credbroker installed. The
        script is stdlib-only; it must exit 0 and print the deterministic branch
        name without touching any installed package. Neither agentbundle nor
        credbroker is importable in the same venv. AC-0002.
        """
        venv_dir = self._make_venv(tmp_path, python311, "empty")
        venv_python = self._venv_python(venv_dir)

        # Prove neither package is importable in this venv.
        isolation_script = (
            "results = {}\n"
            "for pkg in ('agentbundle', 'credbroker'):\n"
            "    try:\n"
            "        __import__(pkg)\n"
            "        results[pkg] = 'importable'\n"
            "    except ImportError:\n"
            "        results[pkg] = 'not_importable'\n"
            "unexpected = {k: v for k, v in results.items() if v != 'not_importable'}\n"
            "if unexpected:\n"
            "    raise SystemExit(f'Packages unexpectedly importable: {unexpected}')\n"
            "print('isolation_ok')\n"
        )
        isolation_result = subprocess.run(
            [venv_python, "-c", isolation_script],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=False,
        )
        assert isolation_result.returncode == 0, (
            f"Package isolation check failed:\n"
            f"stdout: {isolation_result.stdout!r}\nstderr: {isolation_result.stderr!r}"
        )
        assert "isolation_ok" in isolation_result.stdout

        # Run the ordinary (stdlib-only) jira-defect-flow branch_name.py script.
        # Expected branch name derivation:
        #   slugify("Fix the login redirect", max_words=6)
        #     lower:       "fix the login redirect"
        #     re.sub:      "fix-the-login-redirect"
        #     parts[:6]:   ["fix", "the", "login", "redirect"]  (4 ≤ 6)
        #     slug:        "fix-the-login-redirect"
        #   build_branch_name("PROJ-123", ..., prefix="fix", max_words=6)
        #     base   = "fix/proj-123"
        #     result = "fix/proj-123-fix-the-login-redirect"
        expected_branch = "fix/proj-123-fix-the-login-redirect"
        branch_script = (
            PACKS_DIR
            / "atlassian"
            / ".apm"
            / "skills"
            / "jira-defect-flow"
            / "scripts"
            / "branch_name.py"
        )
        branch_result = subprocess.run(
            [
                venv_python,
                str(branch_script),
                "PROJ-123",
                "Fix the login redirect",
            ],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=False,
        )
        assert branch_result.returncode == 0, (
            f"branch_name.py exited {branch_result.returncode}:\n"
            f"stdout: {branch_result.stdout!r}\nstderr: {branch_result.stderr!r}"
        )
        assert branch_result.stdout == expected_branch, (
            f"Expected branch name {expected_branch!r}, "
            f"got {branch_result.stdout!r}"
        )


# ── AC-0003: 0.7 installed wins over vendored 0.6 floor ──────────────────────


class TestVersionPrecedence:
    """0.7 installed wheel takes precedence over the vendored 0.6 floor.

    The credential-brokers pack carries a vendored copy of the credbroker
    source as a user-library floor (~/.agentbundle/lib/credbroker/).
    When a compatible installed 0.7 and the vendored 0.6 floor co-exist,
    normal Python import precedence (site-packages earlier than appended
    sys.path floor) selects 0.7. AC-0003.
    """

    @pytest.fixture(scope="class")
    def python311(self) -> str:
        """Python 3.11 interpreter path."""
        return _find_python311()

    @pytest.fixture(scope="class")
    def credbroker_wheel(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        """Built credbroker 0.7 wheel."""
        dest = tmp_path_factory.mktemp("wheel_v07")
        return _build_credbroker_wheel(dest)

    @pytest.fixture(scope="class")
    def floor_v0_6_dir(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        """Extract the credbroker 0.6 package source from the git tag.

        The committed vendored copy is being regenerated to 0.7 by this
        change, so the 0.6 source is read from the ``credbroker-v0.6.0`` git
        tag, which is the last commit that contained the 0.6 package.

        If the tag is unreachable, this fixture fails with a clear message —
        never silently skips — because the CI gate job checks out the
        repository with ``fetch-depth: 0``.
        """
        dest = tmp_path_factory.mktemp("floor_v06")
        pkg_dir = dest / "credbroker"

        # git archive: extract packages/credbroker/credbroker/ from the tag.
        result = subprocess.run(
            [
                "git",
                "archive",
                "credbroker-v0.6.0",
                "packages/credbroker/credbroker/",
            ],
            capture_output=True,
            check=False,
            cwd=str(REPO_ROOT),
        )
        if result.returncode != 0:
            pytest.fail(
                "credbroker-v0.6.0 tag is not accessible — CI checks out with "
                "fetch-depth: 0, so this tag must be reachable. "
                f"git exit {result.returncode}: {result.stderr.decode('utf-8', 'replace')}"
            )

        # Unpack the tar stream, stripping the "packages/credbroker/credbroker/"
        # prefix so the resulting layout is: dest/credbroker/__init__.py, etc.
        prefix = "packages/credbroker/credbroker/"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(result.stdout)) as tar:
            for member in tar.getmembers():
                if not member.name.startswith(prefix):
                    continue
                rel = member.name[len(prefix):]
                if not rel:
                    continue
                member_copy = tarfile.TarInfo(name=rel)
                member_copy.size = member.size
                member_copy.mode = member.mode
                member_copy.type = member.type
                if member.isdir():
                    (pkg_dir / rel).mkdir(parents=True, exist_ok=True)
                elif member.isreg():
                    f = tar.extractfile(member)
                    if f is not None:
                        dest_file = pkg_dir / rel
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        dest_file.write_bytes(f.read())

        assert (pkg_dir / "__init__.py").is_file(), (
            f"credbroker 0.6 __init__.py not found under {pkg_dir!r} — "
            "extraction from git archive may have failed"
        )
        return dest  # sys.path.append(str(dest)) makes `import credbroker` resolve here

    def test_installed_07_wins_over_floor_06(
        self,
        tmp_path: pathlib.Path,
        python311: str,
        credbroker_wheel: pathlib.Path,
        floor_v0_6_dir: pathlib.Path,
    ) -> None:
        """0.7 installed in site-packages wins over 0.6 on appended sys.path.

        Asserts:
        - import credbroker resolves to 0.7 site-packages copy.
        - __version__ == "0.7.0".
        - __file__ is under the venv site-packages, not the floor.
        - Every public 0.6 name is present (backward compatibility).
        - inspect.signature of public 0.6 callables is compatible.

        AC-0003.
        """
        # Reuse the same install helper from the other class.
        venv_dir = tmp_path / "colocation_venv"
        result = subprocess.run(
            [python311, "-m", "venv", "--without-pip", str(venv_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.fail(f"venv creation failed: {result.stderr}")

        # Find venv Python.
        venv_python = str(venv_dir / "bin" / "python3")
        if not pathlib.Path(venv_python).exists():
            venv_python = str(venv_dir / "Scripts" / "python.exe")

        # Install 0.7 wheel into the venv by unpacking (clean env: no PYTHONPATH).
        site_result = subprocess.run(
            [venv_python, "-c", "import site; print(site.getsitepackages()[0])"],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=True,
        )
        site_pkg = pathlib.Path(site_result.stdout.strip())
        site_pkg.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(credbroker_wheel) as zf:
            for member in zf.infolist():
                if ".dist-info/" in member.filename:
                    continue
                zf.extract(member, path=site_pkg)

        # The 0.6 floor is appended at lowest precedence (simulate bootstrap).
        floor_path = str(floor_v0_6_dir)

        # Read the 0.6 __all__ from the extracted source.
        floor_init = floor_v0_6_dir / "credbroker" / "__init__.py"
        floor_source = floor_init.read_text(encoding="utf-8")

        # Extract the __all__ list from the 0.6 source text.
        all_match = re.search(
            r"^__all__\s*=\s*\[(.+?)\]", floor_source, re.DOTALL | re.MULTILINE
        )
        if not all_match:
            pytest.fail("Could not extract __all__ from 0.6 credbroker source")
        all_body = all_match.group(1)
        v06_all_names = re.findall(r'"([^"]+)"', all_body)
        # Filter __version__ (dunder); we check public names.
        v06_public_names = [n for n in v06_all_names if not n.startswith("__")]

        floor_init_path = str(floor_v0_6_dir / "credbroker" / "__init__.py")
        floor_pkg_dir = str(floor_v0_6_dir / "credbroker")
        script = (
            "import sys, json, importlib.util, inspect\n"
            # 0.7 is in site-packages (already on sys.path via venv).
            "import credbroker\n"
            # Load 0.6 without shadowing 0.7 in sys.modules.
            # submodule_search_locations lets relative imports (from ._core)
            # resolve under the floor package directory.
            # Register in sys.modules BEFORE exec_module so relative imports work.
            f"_spec06 = importlib.util.spec_from_file_location('_credbroker_v06', {floor_init_path!r}, submodule_search_locations=[{floor_pkg_dir!r}])\n"
            "_mod06 = importlib.util.module_from_spec(_spec06)\n"
            "sys.modules['_credbroker_v06'] = _mod06\n"
            "_spec06.loader.exec_module(_mod06)\n"
            "results = {\n"
            "    'version': credbroker.__version__,\n"
            "    'file': credbroker.__file__,\n"
            "}\n"
            "public_names = " + repr(v06_public_names) + "\n"
            "missing = [n for n in public_names if not hasattr(credbroker, n)]\n"
            "results['missing_names'] = missing\n"
            # Compare 0.6 and 0.7 signatures element-by-element for callables.
            # C-extension exception subclasses may have no introspectable signature
            # on Python 3.11; skip those (the 'not isfunction' guard covers them).
            # Run the same comparison the unit tests below exercise.
            + inspect.getsource(_compare_signatures_07_vs_06)
            + "sig_issues = []\n"
            "for name in public_names:\n"
            "    sig_issues.extend(_compare_signatures_07_vs_06(\n"
            "        name, getattr(credbroker, name, None), getattr(_mod06, name, None)))\n"
            "results['sig_issues'] = sig_issues\n"
            "print(json.dumps(results))\n"
        )
        run = subprocess.run(
            [venv_python, "-c", script],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=False,
        )
        if run.returncode != 0:
            pytest.fail(
                f"Co-location test script failed (exit {run.returncode}):\n"
                f"stdout: {run.stdout!r}\nstderr: {run.stderr!r}"
            )

        import json
        data = json.loads(run.stdout.strip())

        assert data["version"] == "0.7.0", (
            f"Expected 0.7.0, got {data['version']!r} — 0.6 floor shadowed 0.7 install"
        )

        # File must be under site-packages (not the floor).
        cb_file = pathlib.Path(data["file"])
        floor_dir = pathlib.Path(floor_path) / "credbroker"
        assert not cb_file.resolve().is_relative_to(floor_dir.resolve()), (
            f"credbroker resolved from floor {floor_dir!r}, not site-packages: "
            f"{cb_file!r}"
        )

        assert not data["missing_names"], (
            f"Names from 0.6 __all__ missing in 0.7: {data['missing_names']}"
        )
        assert not data["sig_issues"], (
            f"Signature incompatibilities with 0.6 callable surfaces: "
            f"{data['sig_issues']}"
        )


# ── AC-0003 signature-comparison helper (no venv needed) ─────────────────────


def _compare_signatures_07_vs_06(
    name: str, obj07: object, obj06: object
) -> list[str]:
    """Return a list of backward-incompatibility messages for *name*.

    Compares the signatures of two callables (0.7 and 0.6 versions of a public
    name).  Detects:
    - Positional/keyword parameter name or kind changes.
    - A 0.6 parameter that had a default losing its default in 0.7.
    - An extra 0.7 parameter beyond the 0.6 list that has no default.
    - Fewer parameters in 0.7 than in 0.6.

    Returns an empty list when the signatures are compatible.
    """
    import inspect

    _VARIADIC = {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
    issues: list[str] = []

    if not (inspect.isfunction(obj07) and inspect.isfunction(obj06)):
        return issues  # non-callables are not compared here

    try:
        sig07 = inspect.signature(obj07)
        sig06 = inspect.signature(obj06)
    except (ValueError, TypeError) as exc:
        issues.append(f"{name}: cannot inspect signature: {exc}")
        return issues

    params07 = list(sig07.parameters.items())
    params06 = list(sig06.parameters.items())

    # Element-by-element name+kind comparison over the shared prefix.
    for i, ((n07, p07), (n06, p06)) in enumerate(zip(params07, params06, strict=False)):
        if n07 != n06 or p07.kind != p06.kind:
            issues.append(
                f"{name}: param[{i}] 0.6={n06!r}/{p06.kind.name}"
                f" vs 0.7={n07!r}/{p07.kind.name}"
            )
        # A 0.6 default must remain a default in 0.7.
        if (
            p06.default is not inspect.Parameter.empty
            and p07.default is inspect.Parameter.empty
            and p07.kind not in _VARIADIC
        ):
            issues.append(
                f"{name}: param[{i}] {n06!r} had a default in 0.6 but not in 0.7"
            )

    # 0.7 must not have fewer params than 0.6.
    if len(params07) < len(params06):
        issues.append(
            f"{name}: 0.7 has {len(params07)} params, 0.6 had {len(params06)}"
        )

    # Extra 0.7 params must all have defaults (or be variadic).
    for extra_n, extra_p in params07[len(params06):]:
        if extra_p.default is inspect.Parameter.empty and extra_p.kind not in _VARIADIC:
            issues.append(
                f"{name}: extra 0.7 param {extra_n!r} has no default — breaks 0.6 callers"
            )

    return issues


def test_signature_comparison_detects_added_required_param() -> None:
    """_compare_signatures_07_vs_06 reports one appended required parameter. AC-0003"""

    def func06(a: int, b: int = 0) -> None:
        pass

    def func07(a: int, b: int = 0, *, c: int) -> None:
        pass

    issues = _compare_signatures_07_vs_06("f", func07, func06)
    assert issues == [
        "f: extra 0.7 param 'c' has no default — breaks 0.6 callers"
    ], issues


def test_signature_comparison_detects_removed_default() -> None:
    """_compare_signatures_07_vs_06 reports a parameter that lost its default. AC-0003"""

    def func06(a: int, b: int = 0) -> None:
        pass

    def func07(a: int, b: int) -> None:
        pass

    issues = _compare_signatures_07_vs_06("f", func07, func06)
    assert any("default" in msg or "had a default" in msg for msg in issues), (
        f"Expected a 'default' issue for b, got: {issues}"
    )


# ── AC-0001 (agentbundle half): pip installs agentbundle + credbroker ────────


class TestAgentbundleWheelInstall:
    """Build both wheels; pip install agentbundle pulls credbroker 0.7.0.

    AC-0001 (agentbundle half): pip install resolves credbroker 0.7.0 as the
    declared dependency.  Both ``agentbundle.__file__`` and
    ``credbroker.__file__`` resolve inside the venv's site-packages, not the
    repository source tree.
    """

    @pytest.fixture(scope="class")
    def python311(self) -> str:
        """Python 3.11 interpreter path (fails with clear message if absent)."""
        return _find_python311()

    @pytest.fixture(scope="class")
    def both_wheels(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> pathlib.Path:
        """Build credbroker 0.7.0 and agentbundle 0.51.0 wheels (once per class)."""
        dest = tmp_path_factory.mktemp("both_wheels_ab")
        _build_credbroker_wheel(dest)
        _build_agentbundle_wheel(dest)
        return dest

    @pytest.fixture(scope="class")
    def venv_with_agentbundle(
        self,
        tmp_path_factory: pytest.TempPathFactory,
        python311: str,
        both_wheels: pathlib.Path,
    ) -> pathlib.Path:
        """Create a clean 3.11 venv with agentbundle + credbroker installed via pip."""
        venv_dir = tmp_path_factory.mktemp("venv_ab_half") / "venv"
        result = subprocess.run(
            [python311, "-m", "venv", str(venv_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.fail(f"venv creation failed: {result.stderr}")
        pip = _venv_pip_exe(venv_dir)
        install_result = subprocess.run(
            [
                pip,
                "install",
                "--no-index",
                f"--find-links={both_wheels}",
                "agentbundle",
            ],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=False,
        )
        if install_result.returncode != 0:
            pytest.fail(
                f"pip install agentbundle failed (exit {install_result.returncode}):\n"
                f"stdout:\n{install_result.stdout}\nstderr:\n{install_result.stderr}"
            )
        return venv_dir

    def test_credbroker_070_installed_as_dependency(
        self,
        venv_with_agentbundle: pathlib.Path,
    ) -> None:
        """credbroker 0.7.0 is installed as a dependency of agentbundle. AC-0001."""
        venv_python = _venv_python_exe(venv_with_agentbundle)
        script = (
            "import importlib.metadata, json\n"
            "try:\n"
            "    ver = importlib.metadata.version('credbroker')\n"
            "except importlib.metadata.PackageNotFoundError:\n"
            "    ver = 'NOT_FOUND'\n"
            "print(json.dumps({'version': ver}))\n"
        )
        run = subprocess.run(
            [venv_python, "-c", script],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=False,
        )
        assert run.returncode == 0, (
            f"Version check failed: stdout={run.stdout!r} stderr={run.stderr!r}"
        )
        data = json.loads(run.stdout.strip())
        assert data["version"] == "0.7.0", (
            f"Expected credbroker 0.7.0, got {data['version']!r}"
        )

    def test_both_packages_resolve_inside_venv_site_packages(
        self,
        venv_with_agentbundle: pathlib.Path,
    ) -> None:
        """agentbundle and credbroker __file__ resolve inside venv, not repo. AC-0001."""
        venv_python = _venv_python_exe(venv_with_agentbundle)
        script = (
            "import agentbundle, credbroker, json\n"
            "print(json.dumps({"
            "'ab': agentbundle.__file__, 'cb': credbroker.__file__"
            "}))\n"
        )
        run = subprocess.run(
            [venv_python, "-c", script],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=False,
        )
        assert run.returncode == 0, (
            f"Import check failed: stdout={run.stdout!r} stderr={run.stderr!r}"
        )
        data = json.loads(run.stdout.strip())
        venv_str = str(venv_with_agentbundle.resolve())
        repo_str = str(REPO_ROOT.resolve())
        for name, path in (("agentbundle", data["ab"]), ("credbroker", data["cb"])):
            assert path.startswith(venv_str), (
                f"{name}.__file__ not inside venv: {path!r}"
            )
            assert not path.startswith(repo_str), (
                f"{name}.__file__ resolves to repo source tree: {path!r}"
            )


# ── AC-0018: installed CLI end-to-end HTTPS catalogue acquisition ─────────────


class TestBuiltCliHttpsInstall:
    """Use the installed agentbundle CLI to fetch catalogue+https:// end-to-end.

    AC-0018: tests anonymous, .netrc Basic-auth, and (skipped unless env vars
    present) JFrog CLI scenarios.  Each scenario runs the installed console
    script (not python -m) so the packaging boundary is exercised.
    """

    @pytest.fixture(scope="class")
    def python311(self) -> str:
        """Python 3.11 interpreter path (fails with clear message if absent)."""
        return _find_python311()

    @pytest.fixture(scope="class")
    def both_wheels(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> pathlib.Path:
        """Build credbroker + agentbundle wheels (once per class)."""
        dest = tmp_path_factory.mktemp("ac18_wheels")
        _build_credbroker_wheel(dest)
        _build_agentbundle_wheel(dest)
        return dest

    @pytest.fixture(scope="class")
    def installed_venv(
        self,
        tmp_path_factory: pytest.TempPathFactory,
        python311: str,
        both_wheels: pathlib.Path,
    ) -> pathlib.Path:
        """Create a 3.11 venv with agentbundle + credbroker installed via pip."""
        return _install_built_agentbundle(
            tmp_path_factory.mktemp("ac18_venv") / "venv", python311, both_wheels
        )

    @pytest.fixture(scope="class")
    def tls_cert_key(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> tuple[pathlib.Path, pathlib.Path]:
        """Generate a self-signed cert + key for 127.0.0.1 with SAN."""
        if not shutil.which("openssl"):
            pytest.fail(
                "openssl is required to generate the loopback certificate for "
                "the built-CLI scenarios; CI runners provide it"
            )
        tls_dir = tmp_path_factory.mktemp("ac18_tls")
        cert = tls_dir / "cert.pem"
        key = tls_dir / "key.pem"
        result = subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-days",
                "1",
                "-subj",
                "/CN=127.0.0.1",
                "-addext",
                "subjectAltName=IP:127.0.0.1",
                "-keyout",
                str(key),
                "-out",
                str(cert),
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.fail(
                f"openssl cert generation failed:\n"
                f"{result.stderr.decode('utf-8', 'replace')}"
            )
        return cert, key

    @pytest.fixture(scope="class")
    def catalogue_routes(self) -> dict[str, bytes]:
        """Build the minimal descriptor + archive route map."""
        archive_bytes, sha256_hex = _minimal_catalogue_archive()
        descriptor = json.dumps(
            {
                "schema": 1,
                "kind": "agentbundle-catalogue",
                "bundle": "test",
                "channel": "stable",
                "release": "1.0.0",
                "artifact": "archive.tar.gz",
                "sha256": sha256_hex,
            }
        ).encode("utf-8")
        return {
            "/channel.json": descriptor,
            "/archive.tar.gz": archive_bytes,
        }

    def _run_install(
        self,
        installed_venv: pathlib.Path,
        catalogue_url: str,
        output_dir: pathlib.Path,
        cert: pathlib.Path,
        *,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        """Run ``agentbundle install`` from the installed venv's console script."""
        agentbundle_bin = _venv_agentbundle_exe(installed_venv)
        env: dict[str, str] = {
            **_clean_env(),
            # Direct-HTTPS path: trust the self-signed cert.
            "AGENTBUNDLE_CA_BUNDLE": str(cert),
            # Strip any real credential env vars so tests are isolated.
        }
        env.pop("AGENTBUNDLE_HTTP_BEARER_TOKEN", None)
        env.pop("JFROG_CLI_SERVER_ID", None)
        env.pop("JFROG_CLI_HOME_DIR", None)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [
                agentbundle_bin,
                "install",
                "--pack",
                "test-pack",
                "--output",
                str(output_dir),
                catalogue_url,
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_anonymous_install_exits_zero(
        self,
        tmp_path: pathlib.Path,
        installed_venv: pathlib.Path,
        tls_cert_key: tuple[pathlib.Path, pathlib.Path],
        catalogue_routes: dict[str, bytes],
    ) -> None:
        """Anonymous catalogue install exits 0 and writes state. AC-0018."""
        cert, key = tls_cert_key
        output_dir = tmp_path / "repo"
        output_dir.mkdir()
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with _loopback_https(catalogue_routes, cert, key) as (base_url, handler):
            result = self._run_install(
                installed_venv,
                f"catalogue+{base_url}channel.json",
                output_dir,
                cert,
                extra_env={
                    # Redirect HOME so the real user's .netrc is not consulted.
                    "HOME": str(fake_home),
                    "USERPROFILE": str(fake_home),
                },
            )

        assert result.returncode == 0, (
            f"Anonymous install failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )
        # Observable installed result: state file written.
        state_file = output_dir / ".agentbundle-state.toml"
        assert state_file.exists(), (
            "State file not written after anonymous install"
        )
        # No credential canary: no Basic or Bearer token in CLI output.
        combined = result.stdout + result.stderr
        assert "Basic " not in combined, (
            "Credential token visible in CLI output for anonymous scenario"
        )

    def test_netrc_install_sends_basic_auth_to_loopback(
        self,
        tmp_path: pathlib.Path,
        installed_venv: pathlib.Path,
        tls_cert_key: tuple[pathlib.Path, pathlib.Path],
        catalogue_routes: dict[str, bytes],
    ) -> None:
        """.netrc credentials produce Basic auth on the loopback origin. AC-0018."""
        if os.name == "nt":
            pytest.skip(".netrc chmod 0o600 is not enforced on Windows")

        cert, key = tls_cert_key
        output_dir = tmp_path / "repo"
        output_dir.mkdir()
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        # Start server first so we know the dynamic port.
        with _loopback_https(
            catalogue_routes, cert, key, require_basic_auth=True
        ) as (base_url, handler):
            # Extract the port from the base URL and write host:port .netrc key.
            port = int(base_url.rstrip("/").rsplit(":", 1)[1])
            netrc_path = fake_home / ".netrc"
            # Use host:port key so it matches the non-default port exactly.
            netrc_path.write_text(
                f"machine 127.0.0.1:{port} login testuser password testpass\n",
                encoding="utf-8",
            )
            netrc_path.chmod(0o600)

            result = self._run_install(
                installed_venv,
                f"catalogue+{base_url}channel.json",
                output_dir,
                cert,
                extra_env={
                    "HOME": str(fake_home),
                    "USERPROFILE": str(fake_home),
                },
            )

        assert result.returncode == 0, (
            f".netrc install failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )
        # Server must have received a Basic auth header.
        auth_values = [
            auth
            for _, auth in handler.seen
            if auth and auth.startswith("Basic ")
        ]
        assert auth_values, (
            f"No Basic auth header reached the loopback server.\n"
            f"handler.seen: {handler.seen!r}\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )
        # Basic header must not appear verbatim in CLI stdout/stderr.
        for auth_val in auth_values:
            assert auth_val not in result.stdout, (
                f"Auth header value found in stdout: {auth_val!r}"
            )
            assert auth_val not in result.stderr, (
                f"Auth header value found in stderr: {auth_val!r}"
            )
        # Observable installed result: state file written, carrying no
        # credential or credential-derived value.
        state_file = output_dir / ".agentbundle-state.toml"
        assert state_file.exists(), (
            "State file not written after .netrc install"
        )
        state_text = state_file.read_text(encoding="utf-8")
        for secret in ("testpass", *auth_values, *(a.split(" ", 1)[1] for a in auth_values)):
            assert secret not in state_text
            assert secret not in result.stdout + result.stderr


_JF_EXECUTABLE = os.environ.get("AGENTBUNDLE_TEST_JF_EXECUTABLE", "")
_JF_CA_CERT = os.environ.get("AGENTBUNDLE_TEST_JF_CA_CERT", "")
_JF_CA_KEY = os.environ.get("AGENTBUNDLE_TEST_JF_CA_KEY", "")


@pytest.mark.skipif(
    not (_JF_EXECUTABLE and _JF_CA_CERT and _JF_CA_KEY),
    reason=(
        "AGENTBUNDLE_TEST_JF_EXECUTABLE, AGENTBUNDLE_TEST_JF_CA_CERT, and "
        "AGENTBUNDLE_TEST_JF_CA_KEY must all be set to run the JFrog leg of "
        "AC-0018; it runs in a disposable Linux container, where jf api trusts "
        "the loopback CA through SSL_CERT_FILE"
    ),
)
def test_built_cli_installs_through_a_jfrog_cli_profile(
    tmp_path: pathlib.Path,
) -> None:
    """The installed CLI acquires a catalogue through a real JFrog CLI profile. AC-0018"""
    token = "disposable-roster-token-0001"
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    _build_credbroker_wheel(wheels)
    _build_agentbundle_wheel(wheels)
    venv_dir = _install_built_agentbundle(tmp_path / "venv", _find_python311(), wheels)

    archive_bytes, sha256_hex = _minimal_catalogue_archive()
    descriptor = json.dumps(
        {
            "schema": 1,
            "kind": "agentbundle-catalogue",
            "bundle": "test",
            "channel": "stable",
            "release": "1.0.0",
            "artifact": "archive.tar.gz",
            "sha256": sha256_hex,
        }
    ).encode("utf-8")
    routes = {
        "/artifactory/cat/channel.json": descriptor,
        "/artifactory/cat/archive.tar.gz": archive_bytes,
    }
    home = tmp_path / "home"
    home.mkdir()
    jf_home = tmp_path / "jfrog-home"
    jf_home.mkdir()
    output_dir = tmp_path / "repo"
    output_dir.mkdir()

    with _loopback_https(
        routes, pathlib.Path(_JF_CA_CERT), pathlib.Path(_JF_CA_KEY)
    ) as (base_url, handler):
        jf_env = {
            "PATH": str(pathlib.Path(_JF_EXECUTABLE).parent),
            "HOME": str(home),
            "JFROG_CLI_HOME_DIR": str(jf_home),
            "SSL_CERT_FILE": _JF_CA_CERT,
        }
        subprocess.run(
            [
                _JF_EXECUTABLE,
                "config",
                "add",
                "roster-profile",
                f"--url={base_url}",
                f"--artifactory-url={base_url}artifactory/",
                f"--access-token={token}",
                "--interactive=false",
            ],
            env=jf_env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
            timeout=60,
        )
        cli_env = {
            key: value
            for key, value in _clean_env().items()
            if not key.startswith(("AGENTBUNDLE_", "JFROG_", "JF_"))
        }
        cli_env.update(jf_env)
        cli_env["PATH"] = os.pathsep.join(
            [jf_env["PATH"], str(pathlib.Path(_venv_agentbundle_exe(venv_dir)).parent), "/usr/bin", "/bin"]
        )
        result = subprocess.run(
            [
                _venv_agentbundle_exe(venv_dir),
                "install",
                "--pack",
                "test-pack",
                "--output",
                str(output_dir),
                f"catalogue+{base_url}artifactory/cat/channel.json",
            ],
            capture_output=True,
            text=True,
            env=cli_env,
            cwd=tmp_path,
            check=False,
        )

    assert result.returncode == 0, (
        f"JFrog install failed (exit {result.returncode}):\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    state_file = output_dir / ".agentbundle-state.toml"
    assert state_file.exists(), "State file not written after JFrog install"
    assert {path for path, _ in handler.seen} >= set(routes)
    assert all(auth == f"Bearer {token}" for path, auth in handler.seen if path in routes)
    state_text = state_file.read_text(encoding="utf-8")
    for secret in (token, "roster-profile"):
        assert secret not in result.stdout + result.stderr
        assert secret not in state_text
