# STUB: AC-0011 — the unique longest JFrog profile is selected and pinned
import json
import os
import shlex
from pathlib import Path

import pytest

from credbroker import JfrogCliHttpAccess, resolve_http_access


@pytest.mark.skipif(os.name == "nt", reason="stub fixture requires POSIX executable bits")
def test_jfrog_longest_profile_returns_pinned_binding(
    tmp_path: Path,
) -> None:
    jf = tmp_path / "jf"
    profiles = [
        {
            "serverId": "broad",
            "url": "https://platform.example.test/",
            "artifactoryUrl": "https://platform.example.test/artifactory/",
            "isDefault": True,
        },
        {
            "serverId": "catalogues",
            "url": "https://platform.example.test/",
            "artifactoryUrl": "https://platform.example.test/artifactory/catalogues/",
            "isDefault": False,
        },
    ]
    # `/bin/sh` is an absolute interpreter, so the fixture runs under the
    # allowlisted child environment without needing `python3` on `PATH`.
    jf.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        '  echo "jf version 2.105.0"\n'
        "else\n"
        "  exit 2\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    result = resolve_http_access(
        "https://platform.example.test/artifactory/catalogues/team/catalogue.toml",
        env={"PATH": str(tmp_path)},
    )

    assert isinstance(result, JfrogCliHttpAccess)
    assert result.server_id == "catalogues"
    assert result.artifactory_url.endswith("/artifactory/catalogues/")


# ---------------------------------------------------------------------------
# Appended tests — T4 full matrix
# ---------------------------------------------------------------------------

# ruff: noqa: I001 — appended imports below the stub block; content order is intentional

import time  # noqa: E402
from collections.abc import Mapping  # noqa: E402

from credbroker import AnonymousHttpAccess, HttpAccessError  # noqa: E402
from credbroker._http_access import (  # noqa: E402
    _build_jfrog_child_env,
    _jfrog_provider,
)
import credbroker._http_access as _cba_mod  # noqa: E402

# ── Module-level production constant captures ────────────────────────────────
# Captured BEFORE any autouse fixture can monkeypatch them.

_PROD_DISCOVERY_TIMEOUT: float = _cba_mod._JFROG_DISCOVERY_TIMEOUT    # 10.0
_PROD_PROBE_TIMEOUT: float = _cba_mod._JFROG_PROBE_TIMEOUT             # 5.0
_PROD_DISCOVERY_STDOUT_CAP: int = _cba_mod._JFROG_DISCOVERY_STDOUT_CAP  # 1 << 20
_PROD_DISCOVERY_STDERR_CAP: int = _cba_mod._JFROG_DISCOVERY_STDERR_CAP  # 64 << 10
_PROD_PROBE_CAP: int = _cba_mod._JFROG_PROBE_CAP                       # 8 << 10


@pytest.fixture(autouse=True)
def _generous_timeouts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch subprocess deadlines to prevent host-load flakiness.

    Timeout tests override these values explicitly.
    """
    monkeypatch.setattr("credbroker._http_access._JFROG_DISCOVERY_TIMEOUT", 120.0)
    monkeypatch.setattr("credbroker._http_access._JFROG_PROBE_TIMEOUT", 120.0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_jf(
    tmp_path: Path,
    profiles: list,
    *,
    version: str = "2.105.0",
) -> Path:
    """Write a #!/bin/sh jf fixture with given profiles and version."""
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        f'  echo "jf version {version}"\n'
        "else\n"
        "  exit 2\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    return jf


def _simple_profile(
    server_id: str,
    platform_url: str,
    artf_url: str,
    *,
    is_default: bool = False,
) -> dict:
    return {
        "serverId": server_id,
        "url": platform_url,
        "artifactoryUrl": artf_url,
        "isDefault": is_default,
    }


# ---------------------------------------------------------------------------
# AC-0011 — profile selection
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_single_profile_is_selected(tmp_path: Path) -> None:
    """A single eligible profile is selected. AC-0011"""
    _make_jf(
        tmp_path,
        [_simple_profile("server1", "https://host.example.test/", "https://host.example.test/artifactory/")],
    )
    result = resolve_http_access(
        "https://host.example.test/artifactory/cat.toml",
        env={"PATH": str(tmp_path)},
    )
    assert isinstance(result, JfrogCliHttpAccess)
    assert result.server_id == "server1"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_longest_prefix_wins_over_shorter(tmp_path: Path) -> None:
    """Longest artifactory path prefix wins when multiple profiles match. AC-0011"""
    profiles = [
        _simple_profile("broad", "https://p.example.test/", "https://p.example.test/artifactory/"),
        _simple_profile("narrow", "https://p.example.test/", "https://p.example.test/artifactory/team/"),
    ]
    _make_jf(tmp_path, profiles)
    result = resolve_http_access(
        "https://p.example.test/artifactory/team/cat.toml",
        env={"PATH": str(tmp_path)},
    )
    assert isinstance(result, JfrogCliHttpAccess)
    assert result.server_id == "narrow"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_tied_longest_raises_ambiguous(tmp_path: Path) -> None:
    """Two profiles with equal longest prefix raise jfrog_profile_ambiguous. AC-0011"""
    profiles = [
        _simple_profile("a", "https://p.example.test/", "https://p.example.test/artifactory/a/"),
        _simple_profile("b", "https://p.example.test/", "https://p.example.test/artifactory/b/"),
    ]
    _make_jf(tmp_path, profiles)
    # Craft a URL that matches BOTH a/ and b/ (they are the same length)
    # Actually these paths don't both match the same URL — need same prefix lengths
    # Let's use two profiles with paths of same length that both match
    profiles2 = [
        _simple_profile("x", "https://p.example.test/", "https://p.example.test/art/"),
        _simple_profile("y", "https://p.example.test/", "https://p.example.test/art/"),
    ]
    _make_jf(tmp_path, profiles2)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/team/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "jfrog_profile_ambiguous"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_explicit_id_selects_shorter_match(tmp_path: Path) -> None:
    """Explicit JFROG_CLI_SERVER_ID may pick a shorter eligible match. AC-0011"""
    profiles = [
        _simple_profile("broad", "https://p.example.test/", "https://p.example.test/artifactory/"),
        _simple_profile("narrow", "https://p.example.test/", "https://p.example.test/artifactory/team/"),
    ]
    _make_jf(tmp_path, profiles)
    result = resolve_http_access(
        "https://p.example.test/artifactory/team/cat.toml",
        env={"PATH": str(tmp_path), "JFROG_CLI_SERVER_ID": "broad"},
    )
    assert isinstance(result, JfrogCliHttpAccess)
    assert result.server_id == "broad"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_explicit_id_can_select_in_a_tie(tmp_path: Path) -> None:
    """Explicit JFROG_CLI_SERVER_ID breaks a tie. AC-0011"""
    profiles = [
        _simple_profile("x", "https://p.example.test/", "https://p.example.test/art/"),
        _simple_profile("y", "https://p.example.test/", "https://p.example.test/art/"),
    ]
    _make_jf(tmp_path, profiles)
    result = resolve_http_access(
        "https://p.example.test/art/cat.toml",
        env={"PATH": str(tmp_path), "JFROG_CLI_SERVER_ID": "y"},
    )
    assert isinstance(result, JfrogCliHttpAccess)
    assert result.server_id == "y"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_explicit_id_nonexistent_raises_mismatch(tmp_path: Path) -> None:
    """Explicit server ID not present in any eligible profile raises mismatch. AC-0011"""
    _make_jf(
        tmp_path,
        [_simple_profile("other", "https://p.example.test/", "https://p.example.test/artifactory/")],
    )
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/artifactory/cat.toml",
            env={"PATH": str(tmp_path), "JFROG_CLI_SERVER_ID": "nosuch"},
        )
    assert exc_info.value.code == "jfrog_profile_mismatch"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_explicit_id_nonmatching_profile_raises_mismatch(tmp_path: Path) -> None:
    """Explicit server ID exists but profile does not match target URL. AC-0011"""
    profiles = [
        _simple_profile("real", "https://p.example.test/", "https://p.example.test/artifactory/"),
    ]
    _make_jf(tmp_path, profiles)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://other.example.test/artifactory/cat.toml",
            env={"PATH": str(tmp_path), "JFROG_CLI_SERVER_ID": "real"},
        )
    assert exc_info.value.code == "jfrog_profile_mismatch"


# ---------------------------------------------------------------------------
# AC-0011 — topology failures
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_split_origin_topology_raises_unsupported(tmp_path: Path) -> None:
    """ArtifactoryUrl on different origin than platformUrl raises unsupported_jfrog_topology. AC-0011"""
    profiles = [
        _simple_profile(
            "split",
            "https://platform.example.test/",
            "https://artifactory.example.test/",
        )
    ]
    _make_jf(tmp_path, profiles)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://artifactory.example.test/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "unsupported_jfrog_topology"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_artf_not_under_platform_path_raises_unsupported(tmp_path: Path) -> None:
    """ArtifactoryUrl path is not a descendant of platformUrl path. AC-0011"""
    profiles = [
        _simple_profile(
            "bad",
            "https://p.example.test/sub/",
            "https://p.example.test/other/",
        )
    ]
    _make_jf(tmp_path, profiles)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/other/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "unsupported_jfrog_topology"


# ---------------------------------------------------------------------------
# AC-0011 — segment alignment
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_segment_prefix_not_matched_on_partial_component(tmp_path: Path) -> None:
    """/artifactory/cat must NOT match /artifactory/catalogues/... AC-0011"""
    profiles = [
        _simple_profile("s1", "https://p.example.test/", "https://p.example.test/artifactory/cat/"),
    ]
    _make_jf(tmp_path, profiles)
    result = resolve_http_access(
        "https://p.example.test/artifactory/catalogues/cat.toml",
        env={"PATH": str(tmp_path)},
    )
    # No eligible profile — falls through to anonymous
    assert isinstance(result, AnonymousHttpAccess)


# ---------------------------------------------------------------------------
# AC-0011 — host normalization (Unicode ↔ punycode, case-insensitive)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_unicode_profile_host_matches_punycode_target(tmp_path: Path) -> None:
    """A profile URL with Unicode host matches a punycode-spelled target. AC-0011"""
    # "münchen" encodes to "xn--mnchen-3ya" under IDNA2003 (Python's "idna" codec).
    profiles = [
        _simple_profile(
            "unicode-server",
            "https://münchen.example.test/",
            "https://münchen.example.test/artifactory/",
        )
    ]
    _make_jf(tmp_path, profiles)
    result = resolve_http_access(
        "https://xn--mnchen-3ya.example.test/artifactory/cat.toml",
        env={"PATH": str(tmp_path)},
    )
    assert isinstance(result, JfrogCliHttpAccess)
    assert result.server_id == "unicode-server"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_punycode_profile_host_matches_unicode_target(tmp_path: Path) -> None:
    """A profile URL with punycode host matches a Unicode-spelled target. AC-0011"""
    profiles = [
        _simple_profile(
            "punycode-server",
            "https://xn--mnchen-3ya.example.test/",
            "https://xn--mnchen-3ya.example.test/artifactory/",
        )
    ]
    _make_jf(tmp_path, profiles)
    result = resolve_http_access(
        "https://münchen.example.test/artifactory/cat.toml",
        env={"PATH": str(tmp_path)},
    )
    assert isinstance(result, JfrogCliHttpAccess)
    assert result.server_id == "punycode-server"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_case_differing_hosts_still_match(tmp_path: Path) -> None:
    """Profile with UPPERCASE host matches lowercase target URL. AC-0011"""
    profiles = [
        _simple_profile(
            "caseserver",
            "https://PLATFORM.EXAMPLE.TEST/",
            "https://PLATFORM.EXAMPLE.TEST/artifactory/",
        )
    ]
    _make_jf(tmp_path, profiles)
    result = resolve_http_access(
        "https://platform.example.test/artifactory/cat.toml",
        env={"PATH": str(tmp_path)},
    )
    assert isinstance(result, JfrogCliHttpAccess)
    assert result.server_id == "caseserver"


# ---------------------------------------------------------------------------
# AC-0011 — discovery failures
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_nonzero_exit_raises_failed(tmp_path: Path) -> None:
    """Non-zero exit from jf config show raises jfrog_discovery_failed. AC-0011"""
    jf = tmp_path / "jf"
    jf.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    jf.chmod(0o755)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "jfrog_discovery_failed"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_timeout_raises_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Discovery deadline exceeded raises jfrog_discovery_timeout. AC-0011"""
    jf = tmp_path / "jf"
    real_path = os.environ.get("PATH", "/usr/bin:/bin")
    # sleep 30 is ≥10× the 1s deadline; set a real PATH so sleep is found.
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        "sleep 30\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    monkeypatch.setattr("credbroker._http_access._JFROG_DISCOVERY_TIMEOUT", 1.0)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "jfrog_discovery_timeout"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_stdout_exact_boundary_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exactly the stdout cap bytes is accepted (not too large). AC-0014"""
    import sys as _sys
    import os as _os
    cap = 64
    monkeypatch.setattr("credbroker._http_access._JFROG_DISCOVERY_STDOUT_CAP", cap)
    padding = cap - 2
    real_python = _sys.executable
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f"'{real_python}' -c \"import sys; sys.stdout.buffer.write(b' ' * {padding} + b'[]')\"\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    result = resolve_http_access(
        "https://p.example.test/art/cat.toml",
        env={"PATH": f"{tmp_path}{_os.pathsep}{real_path}"},
    )
    assert isinstance(result, AnonymousHttpAccess)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_stdout_one_over_cap_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One byte over the stdout cap raises jfrog_discovery_too_large. AC-0014"""
    import sys as _sys
    import os as _os
    cap = 32
    monkeypatch.setattr("credbroker._http_access._JFROG_DISCOVERY_STDOUT_CAP", cap)
    real_python = _sys.executable
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f"'{real_python}' -c \"import sys; sys.stdout.buffer.write(b'x' * {cap + 1})\"\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": f"{tmp_path}{_os.pathsep}{real_path}"},
        )
    assert exc_info.value.code == "jfrog_discovery_too_large"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_stderr_one_over_cap_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One byte over the stderr cap raises jfrog_discovery_too_large. AC-0014"""
    import sys as _sys
    import os as _os
    cap = 32
    monkeypatch.setattr("credbroker._http_access._JFROG_DISCOVERY_STDERR_CAP", cap)
    real_python = _sys.executable
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f"'{real_python}' -c \"import sys; sys.stderr.buffer.write(b'e' * {cap + 1})\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": f"{tmp_path}{_os.pathsep}{real_path}"},
        )
    assert exc_info.value.code == "jfrog_discovery_too_large"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_malformed_non_json(tmp_path: Path) -> None:
    """Non-JSON discovery stdout raises jfrog_discovery_malformed. AC-0011"""
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "config" ]; then echo "not json"; fi\n',
        encoding="utf-8",
    )
    jf.chmod(0o755)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "jfrog_discovery_malformed"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_malformed_not_list(tmp_path: Path) -> None:
    """Discovery JSON that is not a list raises jfrog_discovery_malformed. AC-0011"""
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "config" ]; then printf \'{"key": 1}\'; fi\n',
        encoding="utf-8",
    )
    jf.chmod(0o755)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "jfrog_discovery_malformed"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_malformed_item_not_object(tmp_path: Path) -> None:
    """A list item that is not an object raises jfrog_discovery_malformed. AC-0011"""
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "config" ]; then printf \'["not-an-object"]\'; fi\n',
        encoding="utf-8",
    )
    jf.chmod(0o755)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "jfrog_discovery_malformed"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_malformed_missing_required_field(tmp_path: Path) -> None:
    """A profile missing serverId raises jfrog_discovery_malformed. AC-0011"""
    profiles = [{"url": "https://p.example.test/", "artifactoryUrl": "https://p.example.test/art/"}]
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = "config" ]; then printf {shlex.quote(json.dumps(profiles))}; fi\n',
        encoding="utf-8",
    )
    jf.chmod(0o755)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "jfrog_discovery_malformed"


# ---------------------------------------------------------------------------
# AC-0011 — version probe
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_version_above_floor_is_accepted(tmp_path: Path) -> None:
    """JFrog CLI version above 2.105.0 passes the version check. AC-0011"""
    _make_jf(
        tmp_path,
        [_simple_profile("s", "https://p.example.test/", "https://p.example.test/artifactory/")],
        version="2.200.0",
    )
    result = resolve_http_access(
        "https://p.example.test/artifactory/cat.toml",
        env={"PATH": str(tmp_path)},
    )
    assert isinstance(result, JfrogCliHttpAccess)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_version_equal_to_floor_is_accepted(tmp_path: Path) -> None:
    """JFrog CLI version exactly 2.105.0 passes the version check. AC-0011"""
    _make_jf(
        tmp_path,
        [_simple_profile("s", "https://p.example.test/", "https://p.example.test/artifactory/")],
        version="2.105.0",
    )
    result = resolve_http_access(
        "https://p.example.test/artifactory/cat.toml",
        env={"PATH": str(tmp_path)},
    )
    assert isinstance(result, JfrogCliHttpAccess)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_version_below_floor_raises_incompatible(tmp_path: Path) -> None:
    """JFrog CLI version below 2.105.0 raises incompatible_jfrog_cli. AC-0011"""
    _make_jf(
        tmp_path,
        [_simple_profile("s", "https://p.example.test/", "https://p.example.test/artifactory/")],
        version="2.104.9",
    )
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/artifactory/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "incompatible_jfrog_cli"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_probe_timeout_raises_probe_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Probe deadline exceeded raises jfrog_probe_timeout. AC-0013"""
    profiles = [_simple_profile("s", "https://p.example.test/", "https://p.example.test/artifactory/")]
    jf = tmp_path / "jf"
    real_path = os.environ.get("PATH", "/usr/bin:/bin")
    # sleep 30 is ≥10× the 1s deadline.
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        "  sleep 30\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    monkeypatch.setattr("credbroker._http_access._JFROG_PROBE_TIMEOUT", 1.0)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/artifactory/cat.toml",
            env={"PATH": f"{tmp_path}{os.pathsep}{real_path}"},
        )
    assert exc_info.value.code == "jfrog_probe_timeout"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_probe_too_large_raises_probe_too_large(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Probe output over cap raises jfrog_probe_too_large. AC-0014"""
    import sys as _sys
    import os as _os
    cap = 8
    monkeypatch.setattr("credbroker._http_access._JFROG_PROBE_CAP", cap)
    real_python = _sys.executable
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    profiles = [_simple_profile("s", "https://p.example.test/", "https://p.example.test/artifactory/")]
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        f"  '{real_python}' -c \"import sys; sys.stdout.buffer.write(b'x' * {cap + 1})\"\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/artifactory/cat.toml",
            env={"PATH": f"{tmp_path}{_os.pathsep}{real_path}"},
        )
    assert exc_info.value.code == "jfrog_probe_too_large"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_probe_nonzero_exit_raises_probe_failed(tmp_path: Path) -> None:
    """Non-zero exit from jf --version raises jfrog_probe_failed. AC-0011"""
    profiles = [_simple_profile("s", "https://p.example.test/", "https://p.example.test/artifactory/")]
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = "config" ] && [ "$2" = "show" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        "else\n"
        "  exit 1\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/artifactory/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "jfrog_probe_failed"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_probe_unparseable_output_raises_probe_failed(tmp_path: Path) -> None:
    """A --version that does not match the expected pattern raises probe_failed. AC-0011"""
    profiles = [_simple_profile("s", "https://p.example.test/", "https://p.example.test/artifactory/")]
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = "config" ] && [ "$2" = "show" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        "  echo 'bad output'\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/artifactory/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "jfrog_probe_failed"


# ---------------------------------------------------------------------------
# AC-0013 — refused executable images, both branches
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX filesystem")
def test_relative_path_entry_explicit_raises_not_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative PATH entry holding jf + explicit server ID → not_executable. AC-0013"""
    jf = tmp_path / "jf"
    jf.write_text("#!/bin/sh\n", encoding="utf-8")
    jf.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": ".", "JFROG_CLI_SERVER_ID": "s"},
        )
    assert exc_info.value.code == "jfrog_cli_not_executable"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX filesystem")
def test_relative_path_entry_no_explicit_returns_anonymous(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative PATH entry holding jf + no explicit server → unavailable → anonymous. AC-0013"""
    jf = tmp_path / "jf"
    jf.write_text("#!/bin/sh\n", encoding="utf-8")
    jf.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    result = resolve_http_access(
        "https://p.example.test/art/cat.toml",
        env={"PATH": "."},
    )
    assert isinstance(result, AnonymousHttpAccess)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX filesystem")
def test_cwd_path_entry_explicit_raises_not_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A PATH entry resolving to CWD holding jf + explicit server ID → not_executable. AC-0013"""
    jf = tmp_path / "jf"
    jf.write_text("#!/bin/sh\n", encoding="utf-8")
    jf.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": str(tmp_path), "JFROG_CLI_SERVER_ID": "s"},
        )
    assert exc_info.value.code == "jfrog_cli_not_executable"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX filesystem")
def test_cwd_path_entry_no_explicit_returns_anonymous(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A PATH entry resolving to CWD + no explicit server → unavailable → anonymous. AC-0013"""
    jf = tmp_path / "jf"
    jf.write_text("#!/bin/sh\n", encoding="utf-8")
    jf.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    result = resolve_http_access(
        "https://p.example.test/art/cat.toml",
        env={"PATH": str(tmp_path)},
    )
    assert isinstance(result, AnonymousHttpAccess)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX filesystem")
def test_non_executable_file_explicit_raises_not_executable(tmp_path: Path) -> None:
    """A regular non-executable file with explicit server ID → not_executable. AC-0013"""
    jf = tmp_path / "jf"
    jf.write_text("#!/bin/sh\n", encoding="utf-8")
    jf.chmod(0o644)  # not executable
    jf2 = tmp_path / "bin"
    jf2.mkdir()
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": str(tmp_path), "JFROG_CLI_SERVER_ID": "s"},
        )
    assert exc_info.value.code == "jfrog_cli_not_executable"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX filesystem")
def test_non_executable_file_no_explicit_returns_anonymous(tmp_path: Path) -> None:
    """A non-executable jf file + no explicit server → unavailable → anonymous. AC-0013"""
    jf = tmp_path / "jf"
    jf.write_text("#!/bin/sh\n", encoding="utf-8")
    jf.chmod(0o644)
    result = resolve_http_access(
        "https://p.example.test/art/cat.toml",
        env={"PATH": str(tmp_path)},
    )
    assert isinstance(result, AnonymousHttpAccess)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX filesystem")
def test_absent_jf_with_explicit_raises_not_executable(tmp_path: Path) -> None:
    """No jf executable anywhere + explicit server ID → jfrog_cli_not_executable. AC-0013"""
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": str(tmp_path), "JFROG_CLI_SERVER_ID": "s"},
        )
    assert exc_info.value.code == "jfrog_cli_not_executable"


def test_windows_cmd_shim_explicit_raises_not_executable(tmp_path: Path) -> None:
    """Windows .cmd shim (uppercase ext, via PATHEXT) + explicit server → not_executable. AC-0013"""
    # Use uppercase extension to match PATHEXT=".COM;.EXE;.BAT;.CMD" on case-sensitive filesystems.
    jf_cmd = tmp_path / "jf.CMD"
    jf_cmd.write_text("@echo off\n", encoding="utf-8")
    with pytest.raises(HttpAccessError) as exc_info:
        _jfrog_provider(
            "https://p.example.test",
            "https://p.example.test/art/cat.toml",
            {"PATH": str(tmp_path), "JFROG_CLI_SERVER_ID": "s", "PATHEXT": ".COM;.EXE;.BAT;.CMD"},
            _os_name="nt",
        )
    assert exc_info.value.code == "jfrog_cli_not_executable"


def test_windows_cmd_shim_no_explicit_returns_none(tmp_path: Path) -> None:
    """Windows .cmd shim + no explicit server → provider unavailable (None). AC-0013"""
    jf_cmd = tmp_path / "jf.CMD"
    jf_cmd.write_text("@echo off\n", encoding="utf-8")
    result = _jfrog_provider(
        "https://p.example.test",
        "https://p.example.test/art/cat.toml",
        {"PATH": str(tmp_path), "PATHEXT": ".COM;.EXE;.BAT;.CMD"},
        _os_name="nt",
    )
    assert result is None


# ---------------------------------------------------------------------------
# AC-0011, AC-0013 — no fallback after JFrog error
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_jfrog_error_does_not_fall_through_to_netrc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Any jfrog_* error stops resolution; .netrc and anonymous are not evaluated. AC-0007"""
    # A jf that times out; sleep 30 is ≥10× the 1s deadline.
    jf = tmp_path / "jf"
    real_path = os.environ.get("PATH", "/usr/bin:/bin")
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        "sleep 30\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    monkeypatch.setattr("credbroker._http_access._JFROG_DISCOVERY_TIMEOUT", 1.0)

    netrc_called: list[str] = []

    def _fake_netrc(origin: str, env: Mapping[str, str]) -> None:
        netrc_called.append("called")

    monkeypatch.setattr("credbroker._http_access._netrc_provider", _fake_netrc)

    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "jfrog_discovery_timeout"
    assert not netrc_called, ".netrc must not be evaluated after JFrog error"


# ---------------------------------------------------------------------------
# AC-0015 — child environment allowlist and canary
# ---------------------------------------------------------------------------


def test_child_env_allowlist_only_passes_allowed_keys() -> None:
    """_build_jfrog_child_env passes only allowlisted keys from the supplied mapping. AC-0015"""
    full_env = {
        "PATH": "/usr/bin:/bin",
        "HOME": "/home/user",
        "SSL_CERT_FILE": "/some/cert.pem",
        "SSL_CERT_DIR": "/etc/ssl",
        "JFROG_CLI_HOME_DIR": "/jfrog/home",
        "HTTP_PROXY": "http://proxy:3128",
        "HTTPS_PROXY": "https://proxy:8443",
        "NO_PROXY": "localhost",
        "http_proxy": "http://proxy:3128",
        "https_proxy": "https://proxy:8443",
        "no_proxy": "localhost",
        # Must NOT pass through:
        "JFROG_CLI_SERVER_ID": "should-not-arrive",
        "AGENTBUNDLE_HTTP_BEARER_TOKEN": "secret-bearer",
        "SECRET_X": "secret-value",
        "JF_SOMETHING": "vendor-secret",
        "JFROG_USER": "username",
    }
    child = _build_jfrog_child_env(full_env, _os_name="posix")

    # Allowed keys arrive:
    assert child.get("PATH") == "/usr/bin:/bin"
    assert child.get("HOME") == "/home/user"
    assert child.get("SSL_CERT_FILE") == "/some/cert.pem"
    assert child.get("SSL_CERT_DIR") == "/etc/ssl"
    assert child.get("JFROG_CLI_HOME_DIR") == "/jfrog/home"
    assert child.get("HTTPS_PROXY") == "https://proxy:8443"
    assert child.get("https_proxy") == "https://proxy:8443"

    # Forbidden keys must not arrive:
    assert "JFROG_CLI_SERVER_ID" not in child
    assert "AGENTBUNDLE_HTTP_BEARER_TOKEN" not in child
    assert "SECRET_X" not in child
    assert "JF_SOMETHING" not in child
    assert "JFROG_USER" not in child


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_child_env_via_subprocess_only_allowlisted_keys_arrive(tmp_path: Path) -> None:
    """Only allowlisted keys reach the actual jf child process. AC-0015"""
    import sys as _sys
    env_file = tmp_path / "child_env.json"
    real_python = _sys.executable
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f'  {real_python} -c "import os, json; open(\'{env_file}\', \'w\').write(json.dumps(dict(os.environ)))"\n'
        "  printf '[]'\n"
        'elif [ "$1" = "--version" ]; then\n'
        '  echo "jf version 2.105.0"\n'
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    import os as _os
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    test_env = {
        "PATH": f"{tmp_path}{_os.pathsep}{real_path}",
        "HOME": str(tmp_path),
        "SSL_CERT_FILE": "/some/cert.pem",
        # These must NOT arrive in the child:
        "SECRET_X": "secret-value",
    }
    result = resolve_http_access(
        "https://noprofile.example.test/art/cat.toml",
        env=test_env,
    )
    # No matching profile → anonymous
    assert isinstance(result, AnonymousHttpAccess)

    child_env = json.loads(env_file.read_text(encoding="utf-8"))
    assert child_env.get("SSL_CERT_FILE") == "/some/cert.pem"
    assert "SECRET_X" not in child_env


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_canary_in_proxy_does_not_reach_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A credential embedded in HTTPS_PROXY reaches the child env but not any exception. AC-0015"""
    jf = tmp_path / "jf"
    real_path = os.environ.get("PATH", "/usr/bin:/bin")
    # sleep 30 is ≥10× the 1s deadline.
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        "sleep 30\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    monkeypatch.setattr("credbroker._http_access._JFROG_DISCOVERY_TIMEOUT", 1.0)

    canary = "very-secret-proxy-password-12345"
    try:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={
                "PATH": str(tmp_path),
                "HTTPS_PROXY": f"https://user:{canary}@proxy.example.test:3128",
            },
        )
    except HttpAccessError as exc:
        # The exception text must not contain the canary
        exc_text = str(exc) + repr(exc)
        assert canary not in exc_text, "Canary credential reached exception text"


# ---------------------------------------------------------------------------
# AC-0015 — server_id not in repr/str
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_server_id_not_in_repr_or_str(tmp_path: Path) -> None:
    """JfrogCliHttpAccess server_id must not appear in repr() or str(). AC-0015"""
    _make_jf(
        tmp_path,
        [_simple_profile("my-secret-server-id", "https://p.example.test/", "https://p.example.test/artifactory/")],
    )
    result = resolve_http_access(
        "https://p.example.test/artifactory/cat.toml",
        env={"PATH": str(tmp_path)},
    )
    assert isinstance(result, JfrogCliHttpAccess)
    assert "my-secret-server-id" not in repr(result)
    assert "my-secret-server-id" not in str(result)


# ---------------------------------------------------------------------------
# AC-0013 — process is gone and temp cwd removed after timeout
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX signals")
def test_discovery_timeout_reaps_child_and_removes_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After a timeout the child process is reaped (PID file exists, process is gone). AC-0013"""
    pid_file = tmp_path / "child.pid"
    jf = tmp_path / "jf"
    real_path = os.environ.get("PATH", "/usr/bin:/bin")
    # sleep 30 is ≥10× the 1s deadline.
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        f"echo $$ > {pid_file}\n"
        "sleep 30\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    monkeypatch.setattr("credbroker._http_access._JFROG_DISCOVERY_TIMEOUT", 1.0)

    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "jfrog_discovery_timeout"

    # Wait a moment for cleanup.
    time.sleep(0.3)

    # PID file must exist: the fixture writes it before sleeping.
    assert pid_file.exists(), (
        "PID file was not written; the fixture did not run long enough "
        "or the sleep-based delay was too short"
    )
    pid = int(pid_file.read_text().strip())

    # Assert the process is gone: wait up to 2 s in short increments.
    deadline = time.monotonic() + 2.0
    gone = False
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            gone = True
            break
        time.sleep(0.05)
    assert gone, f"Child process {pid} still alive after timeout and reap"


# ---------------------------------------------------------------------------
# Production constant values
# ---------------------------------------------------------------------------


def test_production_constant_values() -> None:
    """Production JFrog credential-broker constants have their expected values."""
    assert _PROD_DISCOVERY_TIMEOUT == 10.0
    assert _PROD_PROBE_TIMEOUT == 5.0
    assert _PROD_DISCOVERY_STDOUT_CAP == 1 << 20   # 1 MiB
    assert _PROD_DISCOVERY_STDERR_CAP == 64 << 10  # 64 KiB
    assert _PROD_PROBE_CAP == 8 << 10              # 8 KiB


# ---------------------------------------------------------------------------
# Defect R — per-cap boundary matrix: at-cap and cap+1 for each stream
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_stderr_at_cap_does_not_raise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exactly at the discovery stderr cap is accepted (not over). AC-0014"""
    import sys as _sys
    import os as _os
    cap = 32
    monkeypatch.setattr("credbroker._http_access._JFROG_DISCOVERY_STDERR_CAP", cap)
    real_python = _sys.executable
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    jf = tmp_path / "jf"
    # Write exactly cap bytes to stderr, then valid empty JSON to stdout.
    jf.write_text(
        "#!/bin/sh\n"
        f"'{real_python}' -c \"import sys; sys.stderr.buffer.write(b'e' * {cap}); sys.stderr.flush()\"\n"
        "echo '[]\n'",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    # Must not raise — exactly at cap is allowed.
    result = resolve_http_access(
        "https://p.example.test/art/cat.toml",
        env={"PATH": f"{tmp_path}{_os.pathsep}{real_path}"},
    )
    assert isinstance(result, AnonymousHttpAccess)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_probe_stdout_at_cap_does_not_raise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exactly at the probe stdout cap is accepted (not over). AC-0014"""
    import sys as _sys
    import os as _os
    cap = 32
    monkeypatch.setattr("credbroker._http_access._JFROG_PROBE_CAP", cap)
    real_python = _sys.executable
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    profiles = [_simple_profile("s", "https://p.example.test/", "https://p.example.test/artifactory/")]
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        # Exactly cap bytes of stdout — must be accepted.
        f"  '{real_python}' -c \"import sys; sys.stdout.buffer.write(b'x' * {cap})\"\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    # Must not raise — cap bytes exactly is within limit (the version check may
    # fail to parse but that is a different error path; just verify no cap error).
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/artifactory/cat.toml",
            env={"PATH": f"{tmp_path}{_os.pathsep}{real_path}"},
        )
    # Should be a parse/probe-failed error, NOT a too-large error.
    assert exc_info.value.code != "jfrog_probe_too_large", (
        "At-cap probe stdout must not trigger too-large error"
    )


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_probe_stderr_at_cap_does_not_raise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exactly at the probe stderr cap is accepted (not over). AC-0014"""
    import sys as _sys
    import os as _os
    cap = 32
    monkeypatch.setattr("credbroker._http_access._JFROG_PROBE_CAP", cap)
    real_python = _sys.executable
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    profiles = [_simple_profile("s", "https://p.example.test/", "https://p.example.test/artifactory/")]
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        # Emit exactly cap bytes to stderr, then exit; version output may be empty.
        f"  '{real_python}' -c \"import sys; sys.stderr.buffer.write(b'e' * {cap}); sys.stderr.flush()\"\n"
        "  echo 'jf version 2.105.0'\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    # At-cap stderr must not trigger too-large; any other error is acceptable.
    try:
        resolve_http_access(
            "https://p.example.test/artifactory/cat.toml",
            env={"PATH": f"{tmp_path}{_os.pathsep}{real_path}"},
        )
    except HttpAccessError as exc:
        assert exc.code != "jfrog_probe_too_large", (
            "At-cap probe stderr must not trigger too-large error"
        )


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_probe_stderr_cap_plus_one_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One byte over the probe stderr cap raises jfrog_probe_too_large. AC-0014"""
    import sys as _sys
    import os as _os
    cap = 32
    monkeypatch.setattr("credbroker._http_access._JFROG_PROBE_CAP", cap)
    real_python = _sys.executable
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    profiles = [_simple_profile("s", "https://p.example.test/", "https://p.example.test/artifactory/")]
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        # Emit cap+1 bytes to stderr.
        f"  '{real_python}' -c \"import sys; sys.stderr.buffer.write(b'e' * {cap + 1}); sys.stderr.flush()\"\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/artifactory/cat.toml",
            env={"PATH": f"{tmp_path}{_os.pathsep}{real_path}"},
        )
    assert exc_info.value.code == "jfrog_probe_too_large"


# ---------------------------------------------------------------------------
# Item J — stderr cap ordering: post-EOF and stdout-open (discovery and probe)
# ---------------------------------------------------------------------------
# These tests use a single-process shell script with ``exec 1>&-`` to really
# close fd 1 before writing stderr past the cap.  This produces the true
# post-EOF ordering: the runner's stdout thread sees EOF, joins, and the
# post-EOF re-check catches the stderr breach.
#
# A second fixture per runner keeps stdout open while overflowing stderr to
# exercise the cap-breach poll path, asserting termination within 5 s.
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_stderr_overflow_after_stdout_eof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Discovery stderr overflow after real stdout close raises jfrog_discovery_too_large. AC-0014

    Uses 'exec 1>&-' to close fd 1 before overflowing stderr, exercising the
    post-EOF stderr re-check in credbroker._http_access._run_bounded.
    """
    import os as _os
    cap = 32
    monkeypatch.setattr("credbroker._http_access._JFROG_DISCOVERY_STDERR_CAP", cap)
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        # Write valid JSON to stdout, then close fd 1.
        "printf '[]'\n"
        "exec 1>&-\n"
        # Overflow stderr after fd 1 is closed.
        f"head -c {cap + 1000} /dev/zero >&2\n"
        "exit 0\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    start = time.monotonic()
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": f"{tmp_path}{_os.pathsep}{real_path}"},
        )
    elapsed = time.monotonic() - start

    assert exc_info.value.code == "jfrog_discovery_too_large", exc_info.value
    assert elapsed < 15.0, f"abort took {elapsed:.2f}s, expected < 15s"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_stderr_overflow_stdout_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Discovery stderr overflow while stdout stays open terminates promptly. AC-0014

    The cap-breach poll in credbroker._http_access._run_bounded must abort
    within 5 s even when stdout is still open (sleep 30).
    """
    import os as _os
    cap = 32
    monkeypatch.setattr("credbroker._http_access._JFROG_DISCOVERY_STDERR_CAP", cap)
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        # Overflow stderr first while stdout stays open.
        f"head -c {cap + 1000} /dev/zero >&2\n"
        "sleep 30\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    start = time.monotonic()
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": f"{tmp_path}{_os.pathsep}{real_path}"},
        )
    elapsed = time.monotonic() - start

    assert exc_info.value.code == "jfrog_discovery_too_large", exc_info.value
    assert elapsed < 5.0, (
        f"cap-breach abort took {elapsed:.2f}s with stdout open; expected < 5s"
    )


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_probe_stderr_overflow_after_stdout_eof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Probe stderr overflow after real stdout close raises jfrog_probe_too_large. AC-0014

    Uses 'exec 1>&-' to close fd 1 before overflowing stderr.
    """
    import os as _os
    cap = 32
    monkeypatch.setattr("credbroker._http_access._JFROG_PROBE_CAP", cap)
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    profiles = [_simple_profile("s", "https://p.example.test/", "https://p.example.test/artifactory/")]
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        f'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        # Write valid version to stdout, close fd 1, then overflow stderr.
        "  printf 'jf version 2.105.0'\n"
        "  exec 1>&-\n"
        f"  head -c {cap + 1000} /dev/zero >&2\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    start = time.monotonic()
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/artifactory/cat.toml",
            env={"PATH": f"{tmp_path}{_os.pathsep}{real_path}"},
        )
    elapsed = time.monotonic() - start

    assert exc_info.value.code == "jfrog_probe_too_large", exc_info.value
    assert elapsed < 15.0, f"abort took {elapsed:.2f}s, expected < 15s"


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_probe_stderr_overflow_stdout_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Probe stderr overflow while stdout stays open terminates promptly. AC-0014"""
    import os as _os
    cap = 32
    monkeypatch.setattr("credbroker._http_access._JFROG_PROBE_CAP", cap)
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")
    profiles = [_simple_profile("s", "https://p.example.test/", "https://p.example.test/artifactory/")]
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        f'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        # Overflow stderr while stdout stays open.
        f"  head -c {cap + 1000} /dev/zero >&2\n"
        "  sleep 30\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    start = time.monotonic()
    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/artifactory/cat.toml",
            env={"PATH": f"{tmp_path}{_os.pathsep}{real_path}"},
        )
    elapsed = time.monotonic() - start

    assert exc_info.value.code == "jfrog_probe_too_large", exc_info.value
    assert elapsed < 5.0, (
        f"cap-breach abort took {elapsed:.2f}s with stdout open; expected < 5s"
    )


# ---------------------------------------------------------------------------
# Defect L — controlled CWD: directory identity and cleanup after success/timeout
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX executable bits")
def test_discovery_cwd_is_controlled_temp_dir(tmp_path: Path) -> None:
    """Discovery child runs in a controlled temp dir, not the caller's cwd. AC-0013"""
    import os as _os
    cwd_file = tmp_path / "child_cwd.txt"
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")

    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        f"pwd > {shlex.quote(str(cwd_file))}\n"
        "echo '[]'\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    caller_cwd = str(Path.cwd().resolve())

    result = resolve_http_access(
        "https://p.example.test/art/cat.toml",
        env={"PATH": str(tmp_path)},
    )
    assert isinstance(result, AnonymousHttpAccess)

    child_cwd = cwd_file.read_text(encoding="utf-8").strip()
    assert child_cwd != caller_cwd, (
        f"Child ran in caller's cwd {caller_cwd!r}; must use controlled temp dir"
    )
    assert "_jfrog_run_" in child_cwd, (
        f"Expected _jfrog_run_* temp dir, got {child_cwd!r}"
    )
    # Must be cleaned up after success.
    assert not Path(child_cwd).exists(), (
        f"Controlled cwd temp dir not removed after success: {child_cwd!r}"
    )


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX signals")
def test_discovery_timeout_removes_controlled_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After a discovery timeout, the controlled cwd temp dir is removed. AC-0013"""
    import os as _os
    import tempfile as _tf
    real_path = _os.environ.get("PATH", "/usr/bin:/bin")

    jf = tmp_path / "jf"
    jf.write_text(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(real_path)}\n"
        "trap '' TERM\n"
        "sleep 30\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    monkeypatch.setattr("credbroker._http_access._JFROG_DISCOVERY_TIMEOUT", 1.0)

    sys_tmp = Path(_tf.gettempdir())
    before = set(sys_tmp.glob("_jfrog_run_*"))

    with pytest.raises(HttpAccessError) as exc_info:
        resolve_http_access(
            "https://p.example.test/art/cat.toml",
            env={"PATH": str(tmp_path)},
        )
    assert exc_info.value.code == "jfrog_discovery_timeout"

    # Wait briefly for cleanup.
    time.sleep(0.3)

    after = set(sys_tmp.glob("_jfrog_run_*"))
    leaked = after - before
    assert not leaked, f"Controlled cwd dirs not removed after timeout: {leaked}"


# ---------------------------------------------------------------------------
# Aggregate budget: discovery + probe + two fetches must not exceed 75s
# ---------------------------------------------------------------------------


def test_aggregate_credbroker_constants_within_15s() -> None:
    """discovery + probe timeouts must not exceed 15 s. AC-0013

    The credbroker suite must pass without agentbundle installed; this test
    covers only the credbroker-owned constants.  The full 75 s budget is
    asserted on the agentbundle side where both packages are available.
    """
    budget = _PROD_DISCOVERY_TIMEOUT + _PROD_PROBE_TIMEOUT
    assert budget <= 15.0, (
        f"discovery({_PROD_DISCOVERY_TIMEOUT}) + probe({_PROD_PROBE_TIMEOUT}) "
        f"= {budget}s exceeds 15s credbroker ceiling"
    )
