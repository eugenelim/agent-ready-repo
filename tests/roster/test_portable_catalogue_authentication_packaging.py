"""Packaging tests for portable-catalogue-authentication T1.

Anchored at the repository root via ``Path(__file__).resolve().parents[2]``.
Reads ``packs/`` and builds wheels, so it cannot live in the agentbundle sdist
package suite. CI registration: a named step above the bulk
``pytest tests/ -q`` step in ``.github/workflows/build-check.yml``.

Spec mapping: AC-0001 (credbroker half), AC-0002, AC-0003.
AgentBundle-wheel cases (AC-0001 agentbundle half) come in T2; the structure
here leaves a clear class boundary so T2 and T5 can add cases.

Verification mode: TDD package and integration.
"""

from __future__ import annotations

import io
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CREDBROKER_PKG = REPO_ROOT / "packages" / "credbroker"
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

        script = (
            "import sys, json\n"
            f"sys.path.append({floor_path!r})\n"
            "import credbroker\n"
            "import inspect\n"
            "results = {\n"
            "    'version': credbroker.__version__,\n"
            "    'file': credbroker.__file__,\n"
            "}\n"
            "public_names = " + repr(v06_public_names) + "\n"
            "missing = [n for n in public_names if not hasattr(credbroker, n)]\n"
            "results['missing_names'] = missing\n"
            # Check signature compatibility for plain functions (not classes —
            # C-extension exception subclasses have no introspectable signature
            # on Python 3.11 and that constraint predates 0.7).
            "sig_issues = []\n"
            "for name in public_names:\n"
            "    obj = getattr(credbroker, name, None)\n"
            "    if not inspect.isfunction(obj):\n"
            "        continue\n"
            "    try:\n"
            "        inspect.signature(obj)\n"
            "    except (ValueError, TypeError) as e:\n"
            "        sig_issues.append(f'{name}: {e}')\n"
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
