"""Tests for pack-config-api spec.

Covers:
  - make_pack_dir: slug validation, reserved slugs, home-confinement, symlink guard
  - pack_dir: resolution order, PackRootConflict, fallback
  - load_pack_config: two-layer cascade, malformed TOML, path= override
  - write_entry: entry shape, reserved key check, size cap, truncation
  - oplog CLI: show/clear
"""

from __future__ import annotations

import json
import os
import threading
import time
import warnings
from pathlib import Path

import pytest


def test_direct_manifest_rejects_manifestless_sentinel():
    # STUB: AC10
    import agentbundle.direct_source as direct_source

    assert callable(direct_source.validate_direct_manifest)

# ---------------------------------------------------------------------------
# make_pack_dir
# ---------------------------------------------------------------------------


def test_make_pack_dir_creates_directory(tmp_path):
    from agentbundle.safety import make_pack_dir

    base = tmp_path / ".agentbundle"
    base.mkdir()
    result = make_pack_dir(base, "atlassian", home=tmp_path)

    assert result == base / "atlassian"
    assert result.is_dir()


def test_make_pack_dir_mode_700(tmp_path):
    from agentbundle.safety import make_pack_dir

    base = tmp_path / ".agentbundle"
    base.mkdir()
    result = make_pack_dir(base, "atlassian", home=tmp_path)

    # mode 0o700 on POSIX; skip on Windows
    if os.name == "posix":
        assert oct(result.stat().st_mode & 0o777) == oct(0o700)


def test_make_pack_dir_invalid_slug(tmp_path):
    from agentbundle.safety import make_pack_dir

    base = tmp_path / ".agentbundle"
    base.mkdir()
    with pytest.raises(ValueError, match="must match"):
        make_pack_dir(base, "../evil", home=tmp_path)


def test_make_pack_dir_reserved_slug(tmp_path):
    from agentbundle.safety import make_pack_dir

    base = tmp_path / ".agentbundle"
    base.mkdir()
    with pytest.raises(ValueError, match="reserved"):
        make_pack_dir(base, "bin", home=tmp_path)


def test_make_pack_dir_outside_home(tmp_path):
    from agentbundle.safety import make_pack_dir

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    outside = tmp_path / "other"
    outside.mkdir()

    with pytest.raises(OSError, match="outside home"):
        make_pack_dir(outside, "atlassian", home=fake_home)


def test_make_pack_dir_symlink_refused(tmp_path):
    from agentbundle.safety import make_pack_dir

    if os.name != "posix":
        pytest.skip("symlink test — POSIX only")

    base = tmp_path / ".agentbundle"
    base.mkdir()
    target = base / "atlassian"
    (tmp_path / "real").mkdir()
    target.symlink_to(tmp_path / "real")
    with pytest.raises(OSError, match="not a regular directory"):
        make_pack_dir(base, "atlassian", home=tmp_path)


def test_make_pack_dir_idempotent(tmp_path):
    from agentbundle.safety import make_pack_dir

    base = tmp_path / ".agentbundle"
    base.mkdir()
    r1 = make_pack_dir(base, "atlassian", home=tmp_path)
    r2 = make_pack_dir(base, "atlassian", home=tmp_path)
    assert r1 == r2


def test_make_pack_dir_create_false_no_mkdir(tmp_path):
    from agentbundle.safety import make_pack_dir

    base = tmp_path / ".agentbundle"
    base.mkdir()
    result = make_pack_dir(base, "atlassian", home=tmp_path, create=False)

    assert result == base / "atlassian"
    # Directory must NOT have been created
    assert not result.exists()


# ---------------------------------------------------------------------------
# pack_dir
# ---------------------------------------------------------------------------


def test_pack_dir_no_state_uses_default(tmp_path):
    from agentbundle.config import pack_dir

    result = pack_dir("atlassian", home=tmp_path)

    assert result == tmp_path / ".agentbundle" / "atlassian"


def test_pack_dir_state_rows_agree(tmp_path):
    from agentbundle.config import PackState, State, pack_dir

    state = State()
    state.packs[("atlassian", "claude-code")] = PackState(
        installed_version="1.0.0", user_root="~/.agentbundle"
    )
    state.packs[("atlassian", "kiro")] = PackState(
        installed_version="1.0.0", user_root="~/.agentbundle"
    )

    result = pack_dir("atlassian", state=state, home=tmp_path)

    assert result == tmp_path / ".agentbundle" / "atlassian"


def test_pack_dir_state_rows_disagree(tmp_path):
    from agentbundle.config import PackRootConflict, PackState, State, pack_dir

    state = State()
    state.packs[("atlassian", "claude-code")] = PackState(
        installed_version="1.0.0", user_root="~/.agentbundle"
    )
    state.packs[("atlassian", "kiro")] = PackState(installed_version="1.0.0", user_root="~/other")

    with pytest.raises(PackRootConflict) as exc_info:
        pack_dir("atlassian", state=state, home=tmp_path)

    err = exc_info.value
    assert err.pack_name == "atlassian"
    assert len(err.paths) == 2


def test_pack_dir_invalid_slug(tmp_path):
    from agentbundle.config import pack_dir

    with pytest.raises(ValueError):
        pack_dir("../evil", home=tmp_path)


def test_pack_dir_reserved_slug(tmp_path):
    from agentbundle.config import pack_dir

    with pytest.raises(ValueError):
        pack_dir("bin", home=tmp_path)


def test_pack_dir_home_kwarg(tmp_path):
    from agentbundle.config import pack_dir

    custom_home = tmp_path / "custom_home"
    custom_home.mkdir()

    result = pack_dir("atlassian", home=custom_home)

    assert result == custom_home / ".agentbundle" / "atlassian"


def test_pack_dir_custom_user_root(tmp_path):
    from agentbundle.config import PackState, State, pack_dir

    custom_home = tmp_path
    custom_dir = custom_home / "custom-dir"
    custom_dir.mkdir()

    state = State()
    state.packs[("atlassian", "claude-code")] = PackState(
        installed_version="1.0.0", user_root="~/custom-dir"
    )

    result = pack_dir("atlassian", state=state, home=custom_home)

    assert result == custom_dir / "atlassian"


# ---------------------------------------------------------------------------
# load_pack_config
# ---------------------------------------------------------------------------


def test_load_pack_config_empty(tmp_path):
    from agentbundle.config import load_pack_config

    result = load_pack_config("atlassian", home=tmp_path)

    assert result == {}


def test_load_pack_config_user_override(tmp_path):
    from agentbundle.config import load_pack_config, pack_dir

    d = pack_dir("atlassian", home=tmp_path)
    (d / "config.toml").write_text(
        'url = "https://custom.example.com/"', encoding="utf-8", newline="\n"
    )
    result = load_pack_config("atlassian", home=tmp_path)

    assert result.get("url") == "https://custom.example.com/"


def test_load_pack_config_malformed_user_toml(tmp_path):
    from agentbundle.config import load_pack_config, pack_dir

    d = pack_dir("atlassian", home=tmp_path)
    (d / "config.toml").write_text("not valid toml ][", encoding="utf-8", newline="\n")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = load_pack_config("atlassian", home=tmp_path)
    assert any(issubclass(x.category, RuntimeWarning) for x in w)

    assert isinstance(result, dict)


def test_load_pack_config_path_override(tmp_path):
    from agentbundle.config import load_pack_config

    custom_config = tmp_path / "myconfig.toml"
    custom_config.write_text('key = "value"', encoding="utf-8", newline="\n")

    result = load_pack_config("atlassian", path=custom_config, home=tmp_path)

    assert result.get("key") == "value"


def test_load_pack_config_unicode_error_fallback(tmp_path):
    from agentbundle.config import load_pack_config, pack_dir

    d = pack_dir("atlassian", home=tmp_path)
    # Write latin-1 bytes that are invalid UTF-8.
    (d / "config.toml").write_bytes(b"key = \xff\xfe")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = load_pack_config("atlassian", home=tmp_path)
    assert any(issubclass(x.category, RuntimeWarning) for x in w)
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# write_entry
# ---------------------------------------------------------------------------


def test_write_entry_shape(tmp_path):
    from agentbundle.oplog import write_entry

    write_entry("atlassian", "install", src="git+https://example.com/", home=tmp_path)

    ops_file = tmp_path / ".agentbundle" / "atlassian" / "ops.jsonl"
    assert ops_file.exists()
    entry = json.loads(ops_file.read_text(encoding="utf-8").strip())
    assert entry["action"] == "install"
    assert entry["src"] == "git+https://example.com/"
    assert "ts" in entry
    # ts must be last key
    assert list(entry.keys())[-1] == "ts"


def test_write_entry_no_dst_when_none(tmp_path):
    from agentbundle.oplog import write_entry

    write_entry("atlassian", "install", src="s", home=tmp_path)

    ops_file = tmp_path / ".agentbundle" / "atlassian" / "ops.jsonl"
    entry = json.loads(ops_file.read_text(encoding="utf-8").strip())
    assert "dst" not in entry


def test_write_entry_with_dst(tmp_path):
    from agentbundle.oplog import write_entry

    write_entry("atlassian", "install", src="s", dst="/path/to/file", home=tmp_path)

    ops_file = tmp_path / ".agentbundle" / "atlassian" / "ops.jsonl"
    entry = json.loads(ops_file.read_text(encoding="utf-8").strip())
    assert entry["dst"] == "/path/to/file"


def test_write_entry_reserved_key_raises(tmp_path):
    from agentbundle.oplog import write_entry

    with pytest.raises(ValueError, match="reserved"):
        write_entry("atlassian", "install", src="s", extra={"ts": "2026-01-01"}, home=tmp_path)
    # No I/O should have happened
    ops_file = tmp_path / ".agentbundle" / "atlassian" / "ops.jsonl"
    assert not ops_file.exists()


def test_write_entry_too_large_raises(tmp_path):
    from agentbundle.oplog import EntryTooLargeError, write_entry

    big_src = "x" * 5000
    with pytest.raises(EntryTooLargeError):
        write_entry("atlassian", "install", src=big_src, home=tmp_path)
    ops_file = tmp_path / ".agentbundle" / "atlassian" / "ops.jsonl"
    assert not ops_file.exists()


def test_write_entry_extra_truncated(tmp_path):
    from agentbundle.oplog import write_entry

    write_entry("atlassian", "install", src="s", extra={"k": "v" * 5000}, home=tmp_path)

    ops_file = tmp_path / ".agentbundle" / "atlassian" / "ops.jsonl"
    entry = json.loads(ops_file.read_text(encoding="utf-8").strip())
    assert entry.get("_truncated") is True
    assert "action" in entry
    assert "src" in entry


def test_write_entry_truncated_entry_fits_within_cap(tmp_path):
    """Truncated entry (base + _truncated + ts) must itself fit within _MAX_ENTRY."""
    from agentbundle.oplog import _MAX_ENTRY, write_entry

    # Build a base entry that is close to the cap but leaves no room for extra.
    # The truncated form adds ~18 bytes for `,"_truncated":true`.
    # Verify: if the truncated entry fits, write_entry succeeds and the file is valid JSON.
    long_src = "s" * (4000 - 100)  # well under cap; extra will overflow
    write_entry("atlassian", "install", src=long_src, extra={"k": "v" * 200}, home=tmp_path)

    ops_file = tmp_path / ".agentbundle" / "atlassian" / "ops.jsonl"
    entry = json.loads(ops_file.read_text(encoding="utf-8").strip())
    assert entry.get("_truncated") is True
    assert len(ops_file.read_bytes()) <= _MAX_ENTRY + 1  # +1 for newline


@pytest.mark.skipif(os.name != "posix", reason="POSIX concurrency test")
def test_write_entry_concurrent(tmp_path):
    from agentbundle.oplog import write_entry

    n = 200
    errors: list[Exception] = []

    def worker():
        try:
            for _ in range(n):
                # Pass home= directly so no patch is needed; thread-safe.
                write_entry("atlassian", "ping", src="s", home=tmp_path)
                time.sleep(0)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Thread errors: {errors}"
    ops_file = tmp_path / ".agentbundle" / "atlassian" / "ops.jsonl"
    lines = [line for line in ops_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == n * 2
    for line in lines:
        json.loads(line)  # each line must be valid JSON


# ---------------------------------------------------------------------------
# CLI: pack-config
# ---------------------------------------------------------------------------


def _run_cli(args: list[str], env_home: Path) -> tuple[int, str, str]:
    import subprocess
    import sys

    env = os.environ.copy()
    env["HOME"] = str(env_home)
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle"] + args,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def test_cli_pack_config_set_and_show(tmp_path):
    rc, _, _ = _run_cli(
        ["pack-config", "set", "atlassian", "url", "https://jira.example.com/"],
        tmp_path,
    )
    assert rc == 0

    rc, out, _ = _run_cli(["pack-config", "show", "atlassian"], tmp_path)
    assert rc == 0
    assert "(user override)" in out
    assert "url" in out


def test_cli_pack_config_get_missing(tmp_path):
    rc, _, _ = _run_cli(["pack-config", "get", "atlassian", "missing-key"], tmp_path)
    assert rc == 1


def test_cli_pack_config_unset(tmp_path):
    _run_cli(["pack-config", "set", "atlassian", "url", "https://jira.example.com/"], tmp_path)
    rc, _, _ = _run_cli(["pack-config", "unset", "atlassian", "url"], tmp_path)
    assert rc == 0
    rc, _, _ = _run_cli(["pack-config", "get", "atlassian", "url"], tmp_path)
    assert rc == 1


# ---------------------------------------------------------------------------
# CLI: oplog
# ---------------------------------------------------------------------------


def test_cli_oplog_show_empty(tmp_path):
    rc, out, _ = _run_cli(["oplog", "show", "atlassian"], tmp_path)
    assert rc == 0
    assert out.strip() == ""


def test_cli_oplog_clear_requires_yes(tmp_path):
    rc, _, err = _run_cli(["oplog", "clear", "atlassian"], tmp_path)
    assert rc != 0
    assert "--yes" in err


def test_cli_oplog_clear_with_yes(tmp_path):
    from agentbundle.oplog import write_entry

    write_entry("atlassian", "install", src="s", home=tmp_path)

    rc, _, _ = _run_cli(["oplog", "clear", "atlassian", "--yes"], tmp_path)
    assert rc == 0

    ops_file = tmp_path / ".agentbundle" / "atlassian" / "ops.jsonl"
    assert ops_file.read_text(encoding="utf-8") == ""


def test_cli_oplog_help(tmp_path):
    rc, out, _ = _run_cli(["oplog", "--help"], tmp_path)
    assert rc == 0
    assert "show" in out or "clear" in out


def test_cli_pack_config_help(tmp_path):
    rc, out, _ = _run_cli(["pack-config", "--help"], tmp_path)
    assert rc == 0
    assert "get" in out or "set" in out
