"""Package-level integration tests for portable catalogue authentication.

Tests provider-state matrix (AC-0006), configured-broken terminal failures
(AC-0007), one-resolution reuse (AC-0008), and non-HTTP source routing
(AC-0017). Uses package fixtures only — no repository paths, no real network.

Spec mapping: AC-0005, AC-0006, AC-0007, AC-0008, AC-0015, AC-0016, AC-0017.
Verification mode: goal-based (T5). Provider behaviour was delivered by T2–T4;
these tests run it through installed packages as regression evidence.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shlex
import subprocess
import sys
import tarfile
from pathlib import Path
from unittest import mock

import pytest
from agentbundle.catalogue_fetch import open_fetch_session
from agentbundle.catalogue_fetch.models import CatalogueFetchError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CATALOGUE_URL = "https://catalogue.example.test/cat/channel.json"
_ARCHIVE_URL = "https://catalogue.example.test/cat/pack.tar.gz"
_ARTF_URL = "https://artf.example.test/artifactory/"
_PLATFORM_URL = "https://artf.example.test/"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _make_tarball() -> bytes:
    """Return a small gzip tarball."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        content = b"hello"
        info = tarfile.TarInfo(name="pack/README.md")
        info.size = len(content)
        tf.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def _git_fixture_tarball() -> bytes:
    """Return a GitHub-style archive holding ``repo-main/catalogue.toml``."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        content = b'[catalogue]\nname = "fixture"\nversion = "0.0.1"\n'
        info = tarfile.TarInfo(name="repo-main/catalogue.toml")
        info.size = len(content)
        tf.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def _write_fake_jf(tmp_path: Path, *, version: str = "2.105.0") -> Path:
    """Write a POSIX #!/bin/sh jf script that serves a profile for _ARTF_URL."""
    profiles = [
        {
            "serverId": "test-srv",
            "url": _PLATFORM_URL,
            "artifactoryUrl": _ARTF_URL,
            "isDefault": True,
        }
    ]
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        f"  printf 'jf version {version}\\n'\n"
        "else\n"
        "  exit 2\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    return jf


def _write_netrc(tmp_path: Path, host: str) -> Path:
    """Write a 0600 .netrc with an exact-machine record for host."""
    netrc = tmp_path / ".netrc"
    netrc.write_text(
        f"machine {host} login <user> password <secret>\n",
        encoding="utf-8",
    )
    netrc.chmod(0o600)
    return netrc


# ---------------------------------------------------------------------------
# AC-0006: provider-state matrix — all 8 availability combinations
#
# One target (artf.example.test/artifactory/) that the fake JFrog profile
# matches.  Eight {bearer?} × {jfrog-matches?} × {netrc?} tuples tested
# exactly once each, asserting the selected provider.
# ---------------------------------------------------------------------------

# 8 tuples: (bearer_set, jfrog_matches, netrc_present, expected_provider)
_MATRIX_PARAMS = [
    pytest.param(True, True, True, "bearer", id="bearer-jfrog-netrc"),
    pytest.param(True, True, False, "bearer", id="bearer-jfrog-nonetrc"),
    pytest.param(True, False, True, "bearer", id="bearer-nojfrog-netrc"),
    pytest.param(True, False, False, "bearer", id="bearer-nojfrog-nonetrc"),
    pytest.param(False, True, True, "jfrog", id="nobearer-jfrog-netrc"),
    pytest.param(False, True, False, "jfrog", id="nobearer-jfrog-nonetrc"),
    pytest.param(False, False, True, "netrc", id="nobearer-nojfrog-netrc"),
    pytest.param(False, False, False, "anonymous", id="nobearer-nojfrog-nonetrc"),
]

# The target URL lies under the fake JFrog profile's artifactoryUrl.
_MATRIX_TARGET = f"{_ARTF_URL}cat/channel.json"


def _no_connect(*args: object, **kwargs: object) -> None:
    """Raise to prove no network activity occurs during resolution."""
    raise AssertionError(
        f"socket.create_connection called during provider discovery: {args!r}"
    )


@pytest.mark.skipif(os.name == "nt", reason="fixture requires POSIX executable bits")
@pytest.mark.parametrize(
    "bearer_set, jfrog_matches, netrc_present, expected",
    _MATRIX_PARAMS,
)
def test_provider_state_matrix(
    bearer_set: bool,
    jfrog_matches: bool,
    netrc_present: bool,
    expected: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Eight {bearer} × {jfrog-matching} × {netrc} combinations each select the right provider.

    Exactly one test per combination.  The JFrog profile always covers
    artf.example.test/artifactory/ (the matrix target); 'jfrog_matches'
    controls whether jf is placed on PATH.  AC-0006.
    """
    env: dict[str, str] = {"PATH": "/dev/null", "HOME": str(tmp_path)}

    if bearer_set:
        env["AGENTBUNDLE_HTTP_BEARER_TOKEN"] = "<token>"

    if jfrog_matches:
        # Place a matching jf on PATH.
        _write_fake_jf(tmp_path)
        env["PATH"] = str(tmp_path)

    if netrc_present:
        # netrc covers the artf target host.
        _write_netrc(tmp_path, "artf.example.test")
        env["HOME"] = str(tmp_path)

    monkeypatch.setattr("socket.create_connection", _no_connect)

    with open_fetch_session(_MATRIX_TARGET, env=env) as session:
        assert session.provider == expected, (
            f"bearer={bearer_set} jfrog={jfrog_matches} netrc={netrc_present}: "
            f"expected {expected!r}, got {session.provider!r}"
        )


# ---------------------------------------------------------------------------
# AC-0007: configured-but-broken conditions terminate resolution
# ---------------------------------------------------------------------------


class TestConfiguredButBroken:
    """Each broken condition raises CatalogueFetchError before a lower provider.

    AC-0007.
    """

    def test_invalid_bearer_env_var_is_terminal(
        self, tmp_path: Path
    ) -> None:
        """A bearer token with non-visible-ASCII chars raises CatalogueFetchError wrapping invalid_bearer. AC-0007

        ``open_fetch_session`` wraps ``HttpAccessError`` into ``CatalogueFetchError``.
        The original code and provider are on ``exc.__cause__``.
        """
        from credbroker import HttpAccessError

        env = {"AGENTBUNDLE_HTTP_BEARER_TOKEN": "bad\ttoken", "PATH": "/dev/null", "HOME": str(tmp_path)}
        with (
            pytest.raises(CatalogueFetchError) as exc_info,
            open_fetch_session(_CATALOGUE_URL, env=env),
        ):
            pass
        cause = exc_info.value.__cause__
        assert isinstance(cause, HttpAccessError), f"Expected HttpAccessError cause, got {type(cause)!r}"
        assert cause.code == "invalid_bearer", f"Expected invalid_bearer, got {cause.code!r}"
        assert cause.provider == "bearer", f"Expected provider=bearer, got {cause.provider!r}"

    @pytest.mark.skipif(os.name == "nt", reason="fixture requires POSIX permission bits")
    def test_unsafe_netrc_permissions_are_terminal(
        self, tmp_path: Path
    ) -> None:
        """Unsafe .netrc permissions raise CatalogueFetchError wrapping netrc_unsafe. AC-0007"""
        netrc = tmp_path / ".netrc"
        netrc.write_text(
            "machine catalogue.example.test login <user> password <secret>\n",
            encoding="utf-8",
        )
        netrc.chmod(0o644)  # unsafe
        env = {"PATH": "/dev/null", "HOME": str(tmp_path)}
        from credbroker import HttpAccessError

        with (
            pytest.raises(CatalogueFetchError) as exc_info,
            open_fetch_session(_CATALOGUE_URL, env=env),
        ):
            pass
        cause = exc_info.value.__cause__
        assert isinstance(cause, HttpAccessError), f"Expected HttpAccessError cause, got {type(cause)!r}"
        assert cause.code == "netrc_unsafe", f"Expected netrc_unsafe, got {cause.code!r}"
        assert cause.provider == "netrc", f"Expected provider=netrc, got {cause.provider!r}"

    @pytest.mark.skipif(os.name == "nt", reason="fixture requires POSIX executable bits")
    def test_explicit_jfrog_server_not_found_is_terminal(
        self, tmp_path: Path
    ) -> None:
        """Explicit JFROG_CLI_SERVER_ID with no match raises CatalogueFetchError wrapping jfrog_profile_mismatch. AC-0007"""
        _write_fake_jf(tmp_path)
        env = {
            "PATH": str(tmp_path),
            "HOME": str(tmp_path),
            "JFROG_CLI_SERVER_ID": "no-such-server",
        }
        from credbroker import HttpAccessError

        target = f"{_ARTF_URL}cat/channel.json"
        with (
            pytest.raises(CatalogueFetchError) as exc_info,
            open_fetch_session(target, env=env),
        ):
            pass
        cause = exc_info.value.__cause__
        assert isinstance(cause, HttpAccessError), f"Expected HttpAccessError cause, got {type(cause)!r}"
        assert cause.code == "jfrog_profile_mismatch", f"Expected jfrog_profile_mismatch, got {cause.code!r}"
        assert cause.provider == "jfrog", f"Expected provider=jfrog, got {cause.provider!r}"


# ---------------------------------------------------------------------------
# AC-0008: one resolution reused for descriptor and archive
# ---------------------------------------------------------------------------


class TestOneResolutionReuse:
    """resolve_http_access is called exactly once per catalogue+https acquisition.

    AC-0008.
    """

    def test_anonymous_resolution_called_once(self, tmp_path: Path) -> None:
        """Resolution is called once for anonymous descriptor+archive fetch."""
        archive = _make_tarball()
        digest = _sha256(archive)
        descriptor = json.dumps(
            {
                "schema": 1,
                "kind": "agentbundle-catalogue",
                "bundle": "test",
                "channel": "stable",
                "release": "1.0.0",
                "artifact": _ARCHIVE_URL,
                "sha256": digest,
            }
        ).encode()
        archive_tmp = tmp_path / "arc.tar.gz"
        archive_tmp.write_bytes(archive)

        call_count: list[int] = [0]
        import agentbundle.catalogue_fetch as _cf

        original = _cf.resolve_http_access

        def counting(url: str, *, env: object) -> object:
            call_count[0] += 1
            return original(url, env=env)  # type: ignore[arg-type]

        with (
            mock.patch.object(_cf, "resolve_http_access", side_effect=counting),
            mock.patch.object(_cf.FetchSession, "fetch_bytes", return_value=descriptor),
            mock.patch.object(_cf.FetchSession, "fetch_archive", return_value=archive_tmp),
        ):
            import shutil

            from agentbundle.https_catalogue import fetch_catalogue_archive

            result = fetch_catalogue_archive(
                f"catalogue+{_CATALOGUE_URL}",
                env={},
            )
            shutil.rmtree(str(result), ignore_errors=True)

        assert call_count[0] == 1, f"resolve_http_access called {call_count[0]} times, expected 1"


# ---------------------------------------------------------------------------
# AC-0017: local-path and git-backed sources do not call resolve_http_access
# ---------------------------------------------------------------------------


class TestNonHttpSourcesNoResolution:
    """Local-path and git sources never call resolve_http_access.

    AC-0017: these source routes execute their own transports without touching
    the HTTP access resolver.  Tests drive ``resolve_catalogue`` (not
    ``fetch_catalogue_archive``) so the transport actually runs, and spy on
    both ``agentbundle.catalogue_fetch.resolve_http_access`` and
    ``credbroker.resolve_http_access`` to assert zero calls.
    """

    def test_local_path_catalogue_resolves_without_http_access(
        self, tmp_path: Path
    ) -> None:
        """resolve_catalogue with a local path returns the path, never calls resolve_http_access. AC-0017"""
        from agentbundle.catalogue import resolve_catalogue

        cat_dir = tmp_path / "catalogue"
        cat_dir.mkdir()
        (cat_dir / "catalogue.toml").write_text(
            '[catalogue]\nname = "test"\nversion = "1.0.0"\n',
            encoding="utf-8",
        )

        ab_resolve_calls: list[int] = [0]
        cb_resolve_calls: list[int] = [0]

        def ab_spy(*args: object, **kwargs: object) -> object:
            ab_resolve_calls[0] += 1
            raise AssertionError("resolve_http_access called for local path")

        def cb_spy(*args: object, **kwargs: object) -> object:
            cb_resolve_calls[0] += 1
            raise AssertionError("credbroker.resolve_http_access called for local path")

        with (
            mock.patch("agentbundle.catalogue_fetch.resolve_http_access", side_effect=ab_spy),
            mock.patch("credbroker.resolve_http_access", side_effect=cb_spy),
        ):
            result = resolve_catalogue(str(cat_dir))

        assert isinstance(result, Path), f"Expected Path, got {type(result)!r}"
        assert result.resolve() == cat_dir.resolve(), (
            f"Expected {cat_dir}, got {result}"
        )
        assert ab_resolve_calls[0] == 0, (
            f"agentbundle.catalogue_fetch.resolve_http_access called {ab_resolve_calls[0]} times"
        )
        assert cb_resolve_calls[0] == 0, (
            f"credbroker.resolve_http_access called {cb_resolve_calls[0]} times"
        )

    def test_git_https_catalogue_transport_runs_without_http_access(
        self, tmp_path: Path
    ) -> None:
        """resolve_catalogue with a git+https source runs the git transport, never calls resolve_http_access. AC-0017

        The real ``_resolve_https`` and ``_fetch_and_extract`` run; only
        ``urllib.request.urlopen`` is replaced by a fixture tarball.
        """
        from agentbundle.catalogue import resolve_catalogue

        archive = _git_fixture_tarball()
        opened: list[str] = []
        ab_resolve_calls: list[int] = [0]
        cb_resolve_calls: list[int] = [0]

        def fake_urlopen(url: str, **kwargs: object) -> io.BytesIO:
            opened.append(url)
            return io.BytesIO(archive)

        def ab_spy(*args: object, **kwargs: object) -> object:
            ab_resolve_calls[0] += 1
            raise AssertionError("resolve_http_access called for git+https source")

        def cb_spy(*args: object, **kwargs: object) -> object:
            cb_resolve_calls[0] += 1
            raise AssertionError("credbroker.resolve_http_access called for git+https source")

        with (
            mock.patch("urllib.request.urlopen", fake_urlopen),
            mock.patch("agentbundle.catalogue_fetch.resolve_http_access", side_effect=ab_spy),
            mock.patch("credbroker.resolve_http_access", side_effect=cb_spy),
        ):
            result = resolve_catalogue("git+https://github.com/example/repo@main")

        assert len(opened) == 1, opened
        assert opened[0].startswith("https://github.com/example/repo/"), opened
        assert (result / "catalogue.toml").is_file(), f"No extracted catalogue at {result}"
        assert ab_resolve_calls[0] == 0, (
            f"agentbundle.catalogue_fetch.resolve_http_access called {ab_resolve_calls[0]} times"
        )
        assert cb_resolve_calls[0] == 0, (
            f"credbroker.resolve_http_access called {cb_resolve_calls[0]} times"
        )

    def test_git_https_subprocess_does_not_import_catalogue_fetch_or_credbroker(
        self, tmp_path: Path
    ) -> None:
        """Resolving a git+https source imports neither catalogue_fetch nor credbroker's resolver. AC-0017

        Runs the real Git transport in a clean interpreter with only
        ``urllib.request.urlopen`` replaced by a fixture tarball.
        """
        archive_path = tmp_path / "repo-main.tar.gz"
        archive_path.write_bytes(_git_fixture_tarball())

        script = (
            "import io, sys, urllib.request\n"
            f"archive = open({str(archive_path)!r}, 'rb').read()\n"
            "urllib.request.urlopen = lambda url, **kw: io.BytesIO(archive)\n"
            "from agentbundle.catalogue import resolve_catalogue\n"
            "result = resolve_catalogue('git+https://github.com/example/repo@main')\n"
            "assert (result / 'catalogue.toml').is_file(), result\n"
            "leaked = [m for m in ('agentbundle.catalogue_fetch', 'credbroker._http_access')\n"
            "          if m in sys.modules]\n"
            "assert not leaked, f'imported for a git+https source: {leaked}'\n"
        )

        repo_root = Path(__file__).resolve().parents[4]
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            env={
                **os.environ,
                "PYTHONPATH": "packages/agentbundle:packages/credbroker",
            },
        )
        if proc.returncode != 0:
            pytest.fail(
                f"Subprocess failed (exit {proc.returncode}):\n"
                f"stdout: {proc.stdout!r}\nstderr: {proc.stderr!r}"
            )

    def test_local_path_subprocess_does_not_import_catalogue_fetch_or_credbroker(
        self, tmp_path: Path
    ) -> None:
        """Resolving a local-path source does not import catalogue_fetch or credbroker. AC-0017

        Runs in a subprocess to get a clean import state.
        """
        cat_dir = tmp_path / "catalogue_sub"
        cat_dir.mkdir()
        (cat_dir / "catalogue.toml").write_text(
            '[catalogue]\nname = "sub"\nversion = "0.0.1"\n',
            encoding="utf-8",
        )

        script = (
            "import sys\n"
            "from agentbundle.catalogue import resolve_catalogue\n"
            f"result = resolve_catalogue({str(cat_dir)!r})\n"
            "assert 'agentbundle.catalogue_fetch' not in sys.modules, "
            "    f'catalogue_fetch was imported: {{list(sys.modules.keys())}}'\n"
            "assert 'credbroker._http_access' not in sys.modules, "
            "    f'credbroker._http_access was imported: {{list(sys.modules.keys())}}'\n"
        )

        # Find the repository root (4 levels up from this file).
        repo_root = Path(__file__).resolve().parents[4]

        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            env={
                **os.environ,
                "PYTHONPATH": "packages/agentbundle:packages/credbroker",
            },
        )
        if proc.returncode != 0:
            pytest.fail(
                f"Subprocess failed (exit {proc.returncode}):\n"
                f"stdout: {proc.stdout!r}\nstderr: {proc.stderr!r}"
            )
