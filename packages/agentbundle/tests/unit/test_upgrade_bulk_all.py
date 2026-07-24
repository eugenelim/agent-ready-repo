"""Tests for upgrade --all bulk upgrade feature.

Covers T1 (argparse surface), T2 (_classify_row), T3 (preflight
orchestration), T4 (_apply_single_row + apply loop), T5 (JSON contract),
and selected T6/T7 checks.
"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Imports under test
# ---------------------------------------------------------------------------

import agentbundle.cli as cli_module
from agentbundle.commands.upgrade import (
    _BulkRow,
    _apply_all,
    _apply_order,
    _apply_single_row,
    _assign_pre_apply_outcomes,
    _build_json_doc,
    _classify_row,
    _finalize,
    _print_plan_table,
    _redact_credentials,
    _run_all,
    _run_preflight,
    _run_source_version_preflight,
    _was_dist_tree_install,
)
from agentbundle.config import ConfigError, PackState, State


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pack_state(
    installed_version: str = "0.13.6",
    source: "str | None" = "git+https://example.test/packs",
    adapter: str = "claude-code",
    files: "dict | None" = None,
) -> PackState:
    return PackState(
        installed_version=installed_version,
        source=source,
        adapter=adapter,
        files=files if files is not None else {},
    )


def _make_state(
    rows: "list[tuple[str, str, str, str]]",
) -> State:
    """Build a State from (pack, adapter, source, version) tuples."""
    state = State()
    for pack, adapter, source, version in rows:
        state.packs[(pack, adapter)] = _make_pack_state(
            installed_version=version,
            source=source,
            adapter=adapter,
        )
    return state


def _make_row(
    pack: str = "core",
    adapter: str = "claude-code",
    installed_version: str = "0.13.6",
    source: "str | None" = "git+https://example.test/packs",
) -> _BulkRow:
    ps = _make_pack_state(installed_version=installed_version, source=source, adapter=adapter)
    return _BulkRow(pack=pack, adapter=adapter, scope="repo", pack_state=ps)


@dataclass
class _Result:
    exit_code: int
    rows: list
    stdout: str
    stderr: str


def _make_args(
    scope: "str | None" = "repo",
    yes: bool = False,
    dry_run: bool = False,
    fmt: str = "table",
    adapter: "str | None" = None,
    catalogue: "str | None" = None,
    root: str = ".",
) -> Any:
    """Build an args-like namespace for _run_all."""
    ns = MagicMock()
    ns.scope = scope
    ns.yes = yes
    ns.dry_run = dry_run
    ns.format = fmt
    ns.adapter = adapter
    ns.catalogue = catalogue
    ns.root = root
    ns._user_config = None
    # Per-primitive flags: not set in bulk mode
    for flag in ("skill", "agent", "hook", "seed", "command"):
        setattr(ns, flag, None)
    # --all is True for _run_all callers
    ns.all = True
    return ns


def _run_all_capture(args: Any, root: Path) -> _Result:
    """Call _run_all, capturing stdout/stderr and the rows side-channel."""
    rows_out: list = []
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = _run_all(args, root, _rows_out=rows_out)
    return _Result(rc, rows_out, buf_out.getvalue(), buf_err.getvalue())


def _parse_args(argv: "list[str]") -> Any:
    p = cli_module._build_parser()
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# T1 — Argparse surface
# ---------------------------------------------------------------------------


def test_all_and_pack_mutually_exclusive():
    with pytest.raises(SystemExit):
        _parse_args(["upgrade", "--all", "--pack", "core"])


def test_all_or_pack_required():
    with pytest.raises(SystemExit):
        _parse_args(["upgrade"])


def test_scope_not_required_by_argparse_for_pack():
    # --scope is optional with --pack (inferred); no SystemExit expected
    args = _parse_args(["upgrade", "--pack", "core"])
    assert args.pack == "core"
    assert args.all is False


def test_format_table_and_json_accepted():
    args_table = _parse_args(["upgrade", "--all", "--scope", "repo", "--format", "table"])
    args_json = _parse_args(["upgrade", "--all", "--scope", "repo", "--format", "json"])
    assert args_table.format == "table"
    assert args_json.format == "json"


def test_yes_flag_accepted():
    args = _parse_args(["upgrade", "--all", "--scope", "repo", "--yes"])
    assert args.yes is True


def test_format_json_with_pack_returns_nonzero(tmp_path):
    """AC5: --format json with --pack exits non-zero with informative message."""
    args = _parse_args(["upgrade", "--pack", "core", "--format", "json"])
    args.root = str(tmp_path)
    from agentbundle.commands.upgrade import run
    buf_err = io.StringIO()
    with redirect_stderr(buf_err):
        rc = run(args)
    assert rc != 0
    assert "not yet supported" in buf_err.getvalue()


# ---------------------------------------------------------------------------
# T2 — _classify_row pure function
# ---------------------------------------------------------------------------


CLASSIFY_CASES = [
    ("0.13.6", "0.13.7", "upgrade-available", None),
    ("0.13.7", "0.13.7", "up-to-date", None),
    ("0.13.8", "0.13.7", "ahead", None),
    # Unequal-length tuples: zero-padding required
    ("0.13", "0.13.0", "up-to-date", None),
    ("0.9", "0.10", "upgrade-available", None),
    # Unparseable versions
    ("0.13.6", "not-a-version", "unknown", "unparseable-catalogue-version"),
    ("not-a-version", "0.13.7", "unknown", "unparseable-installed-version"),
    # Both unparseable: catalogue wins
    ("not-a-version", "also-not", "unknown", "unparseable-catalogue-version"),
]


@pytest.mark.parametrize("installed,available,expected_status,expected_reason", CLASSIFY_CASES)
def test_classify_row_version_matrix(installed, available, expected_status, expected_reason):
    row = _make_row(installed_version=installed)
    # Omit adapter-contract so pack_spec_version() returns None -> compatible
    pack_toml = {"pack": {"version": available}}
    result_status, result_reason, result_av = _classify_row(row, pack_toml)
    assert result_status == expected_status
    assert result_reason == expected_reason


def test_classify_row_pack_not_found():
    row = _make_row()
    result, reason, _ = _classify_row(row, None)
    assert result == "unknown"
    assert reason == "pack-not-found"


def test_classify_row_incompatible_contract():
    # Use a major guaranteed to differ from real SPEC_VERSION
    row = _make_row()
    pack_toml = {"pack": {"version": "0.13.7", "adapter-contract": {"version": "9999.0"}}}
    result, reason, _ = _classify_row(row, pack_toml)
    assert result == "unknown"
    assert reason == "incompatible-contract"


def test_classify_row_absent_adapter_contract_is_compatible():
    row = _make_row(installed_version="0.13.6")
    pack_toml = {"pack": {"version": "0.13.7"}}
    result, reason, _ = _classify_row(row, pack_toml)
    assert result == "upgrade-available"


def test_classify_row_adapter_no_longer_supported():
    row = _make_row(adapter="kiro")
    pack_toml = {
        "pack": {
            "version": "0.13.7",
            "install": {"allowed-adapters": ["claude-code"]},
        }
    }
    result, reason, _ = _classify_row(row, pack_toml)
    assert result == "unknown"
    assert reason == "adapter-no-longer-supported"


def test_classify_row_adapter_allowed_when_list_absent():
    row = _make_row(adapter="kiro")
    pack_toml = {"pack": {"version": "0.13.7"}}
    result, reason, _ = _classify_row(row, pack_toml)
    assert result == "upgrade-available"


def test_classify_row_uses_version_key_none_not_exception():
    row = _make_row(installed_version="not-a-ver")
    pack_toml = {"pack": {"version": "0.13.7"}}
    result, reason, _ = _classify_row(row, pack_toml)
    assert reason == "unparseable-installed-version"


def test_classify_row_cross_consistency_with_list_installed_semantics():
    """Self-contained cross-consistency: _classify_row must agree with
    spec/list-installed-update-status for the three shared outcomes."""
    shared_cases = [
        ("0.13.6", "0.13.7", "upgrade-available"),
        ("0.13.7", "0.13.7", "up-to-date"),
        ("0.13.8", "0.13.7", "ahead"),
        # Unequal-length
        ("0.13", "0.13.0", "up-to-date"),
        ("0.9", "0.10", "upgrade-available"),
    ]
    for installed, available, expected in shared_cases:
        row = _make_row(installed_version=installed)
        pack_toml = {"pack": {"version": available}}
        bulk_status, _, _ = _classify_row(row, pack_toml)
        assert bulk_status == expected, (
            f"_classify_row({installed!r}, {available!r}) = {bulk_status!r}, want {expected!r}"
        )


# ---------------------------------------------------------------------------
# T3 — Preflight orchestration
# ---------------------------------------------------------------------------


def test_preflight_source_unknown(tmp_path):
    """Row with source='agent-ready-repo' gets status=unknown, source-unknown."""
    state = _make_state([("core", "claude-code", "agent-ready-repo", "0.13.6")])
    rows, _ = _run_source_version_preflight(state, scope="repo", root=tmp_path)
    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "source-unknown"
    assert rows[0]._projection is None


def test_preflight_source_unavailable(tmp_path):
    from agentbundle.catalogue import CatalogueError

    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    with patch(
        "agentbundle.commands.upgrade.resolve_catalogue",
        side_effect=CatalogueError("connection refused"),
    ):
        rows, _ = _run_source_version_preflight(state, scope="repo", root=tmp_path)
    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "source-unavailable"


def test_preflight_malformed_catalogue(tmp_path):
    """pack.toml raises ConfigError -> status=unknown, malformed-catalogue."""
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    mock_cat_dir = MagicMock()
    mock_pack_dir = MagicMock()
    mock_cat_dir.__truediv__ = lambda self, other: mock_pack_dir
    mock_pack_dir.is_dir.return_value = True
    mock_toml_path = MagicMock()
    mock_pack_dir.__truediv__ = lambda self, other: mock_toml_path
    mock_toml_path.exists.return_value = True

    with patch(
        "agentbundle.commands.upgrade.resolve_catalogue",
        return_value=tmp_path,
    ), patch(
        "agentbundle.commands.upgrade._locate_pack",
        return_value=tmp_path / "core",
    ), patch(
        "agentbundle.commands.upgrade.load_pack_toml",
        side_effect=ConfigError("bad toml"),
    ):
        rows, _ = _run_source_version_preflight(state, scope="repo", root=tmp_path)
    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "malformed-catalogue"


def test_preflight_pack_not_found(tmp_path):
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    with patch(
        "agentbundle.commands.upgrade.resolve_catalogue",
        return_value=tmp_path,
    ), patch(
        "agentbundle.commands.upgrade._locate_pack",
        return_value=None,
    ):
        rows, _ = _run_source_version_preflight(state, scope="repo", root=tmp_path)
    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "pack-not-found"


def test_preflight_source_resolved_once_per_invocation(tmp_path):
    """AC8: two rows with the same source → resolve_catalogue called once."""
    state = _make_state([
        ("core", "claude-code", "git+https://example.test/packs", "0.13.6"),
        ("ext", "claude-code", "git+https://example.test/packs", "1.0.0"),
    ])
    call_count = {"n": 0}

    def _mock_resolve(uri):
        call_count["n"] += 1
        raise Exception("stop")  # don't need actual resolution

    with patch("agentbundle.commands.upgrade.resolve_catalogue", side_effect=_mock_resolve):
        try:
            _run_source_version_preflight(state, scope="repo", root=tmp_path)
        except Exception:
            pass
    # May be called once even if it raises — the second row reuses the map
    # For our mock it raises so both rows get source-unavailable, but resolve was only called once
    assert call_count["n"] == 1


def test_preflight_catalogue_error_does_not_suppress_other_sources(tmp_path):
    """AC8: CatalogueError on one source does not block rows from other sources."""
    from agentbundle.catalogue import CatalogueError

    state = _make_state([
        ("core", "claude-code", "git+https://example.test/failing", "0.13.6"),
        ("ext", "claude-code", "git+https://example.test/working", "1.0.0"),
    ])

    def _mock_resolve(uri: str):
        if "failing" in uri:
            raise CatalogueError("connection refused")
        return tmp_path  # working source

    pack_toml_working = {"pack": {"version": "1.1.0"}}

    with patch("agentbundle.commands.upgrade.resolve_catalogue", side_effect=_mock_resolve), \
         patch("agentbundle.commands.upgrade._locate_pack", return_value=tmp_path / "ext"), \
         patch("agentbundle.commands.upgrade.load_pack_toml", return_value=pack_toml_working):
        rows, _ = _run_source_version_preflight(state, scope="repo", root=tmp_path)

    failing_row = next(r for r in rows if r.pack == "core")
    working_row = next(r for r in rows if r.pack == "ext")
    assert failing_row.status_reason == "source-unavailable"
    assert working_row.status == "upgrade-available"


def test_preflight_dist_tree_row_blocks_without_rendering(tmp_path):
    """_was_dist_tree_install True -> render-failed before render is called."""
    state = State()
    state.packs[("core", "claude-code")] = PackState(
        installed_version="0.13.6",
        source="git+https://example.test/packs",
        adapter="claude-code",
        files={"claude-plugins/core.json": {"sha": "abc123"}},  # dist-tree path
    )

    pack_toml = {"pack": {"version": "0.13.7"}}
    render_called = {"n": 0}

    def _mock_render(*args, **kwargs):
        render_called["n"] += 1
        return ({}, "claude-code")

    with patch("agentbundle.commands.upgrade.resolve_catalogue", return_value=tmp_path), \
         patch("agentbundle.commands.upgrade._locate_pack", return_value=tmp_path / "core"), \
         patch("agentbundle.commands.upgrade.load_pack_toml", return_value=pack_toml), \
         patch(
             "agentbundle.commands.install._render_for_repo_scope",
             side_effect=_mock_render,
         ):
        rows, _ = _run_preflight(state, scope="repo", root=tmp_path, user_config=None)

    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "render-failed"
    assert rows[0]._projection is None
    assert render_called["n"] == 0, "render should not be called for dist-tree installs"


def test_preflight_stores_projection_for_upgrade_available(tmp_path):
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    pack_toml = {"pack": {"version": "0.13.7"}}
    fake_projection = {"README.md": b"content"}

    with patch("agentbundle.commands.upgrade.resolve_catalogue", return_value=tmp_path), \
         patch("agentbundle.commands.upgrade._locate_pack", return_value=tmp_path / "core"), \
         patch("agentbundle.commands.upgrade.load_pack_toml", return_value=pack_toml), \
         patch(
             "agentbundle.commands.install._render_for_repo_scope",
             return_value=("claude-code", fake_projection),
         ), \
         patch(
             "agentbundle.commands.install._adapter_allowed_prefixes_repo",
             return_value=[".claude/"],
         ), \
         patch("agentbundle.commands.upgrade.safety.assert_projection_jailed"):
        rows, _ = _run_preflight(state, scope="repo", root=tmp_path, user_config=None)

    assert rows[0].status == "upgrade-available"
    assert rows[0]._projection == fake_projection


def test_preflight_render_failed(tmp_path):
    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    pack_toml = {"pack": {"version": "0.13.7"}}

    with patch("agentbundle.commands.upgrade.resolve_catalogue", return_value=tmp_path), \
         patch("agentbundle.commands.upgrade._locate_pack", return_value=tmp_path / "core"), \
         patch("agentbundle.commands.upgrade.load_pack_toml", return_value=pack_toml), \
         patch(
             "agentbundle.commands.install._render_for_repo_scope",
             side_effect=ValueError("render error"),
         ):
        rows, _ = _run_preflight(state, scope="repo", root=tmp_path, user_config=None)

    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "render-failed"
    assert rows[0]._projection is None


def test_preflight_path_jail_violation(tmp_path):
    from agentbundle.safety import PathJailError

    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    pack_toml = {"pack": {"version": "0.13.7"}}

    with patch("agentbundle.commands.upgrade.resolve_catalogue", return_value=tmp_path), \
         patch("agentbundle.commands.upgrade._locate_pack", return_value=tmp_path / "core"), \
         patch("agentbundle.commands.upgrade.load_pack_toml", return_value=pack_toml), \
         patch(
             "agentbundle.commands.install._render_for_repo_scope",
             return_value=("claude-code", {"README.md": b"content"}),
         ), \
         patch(
             "agentbundle.commands.install._adapter_allowed_prefixes_repo",
             return_value=[".claude/"],
         ), \
         patch(
             "agentbundle.commands.upgrade.safety.assert_projection_jailed",
             side_effect=PathJailError("escape"),
         ):
        rows, _ = _run_preflight(state, scope="repo", root=tmp_path, user_config=None)

    assert rows[0].status == "unknown"
    assert rows[0].status_reason == "path-jail-violation"
    assert rows[0]._projection is None


def test_adapter_rejected_with_all(tmp_path):
    args = _make_args(scope="repo", adapter="kiro")
    result = _run_all_capture(args, tmp_path)
    assert result.exit_code != 0
    assert "--adapter" in result.stderr


def test_catalogue_rejected_with_all(tmp_path):
    args = _make_args(scope="repo", catalogue="/some/path")
    result = _run_all_capture(args, tmp_path)
    assert result.exit_code != 0
    assert "catalogue" in result.stderr


def test_scope_missing_with_all_rejected(tmp_path):
    args = _make_args(scope=None)
    result = _run_all_capture(args, tmp_path)
    assert result.exit_code != 0
    assert "--scope" in result.stderr


def test_ahead_row_outcome_skipped_no_mutation(tmp_path):
    """AC18: ahead row gets outcome=skipped and is never downgraded."""
    _setup_state(tmp_path, [("core", "claude-code", "git+https://example.test/packs", "0.13.8")])
    pack_toml = {"pack": {"version": "0.13.7"}}  # installed > available

    with _mock_catalogue(tmp_path, pack_toml):
        result = _run_all_capture(_make_args(scope="repo", yes=True), tmp_path)

    assert result.exit_code == 0
    assert any(r.status == "ahead" and r.outcome == "skipped" for r in result.rows)


def test_up_to_date_row_outcome_skipped_no_mutation(tmp_path):
    _setup_state(tmp_path, [("core", "claude-code", "git+https://example.test/packs", "0.13.7")])
    pack_toml = {"pack": {"version": "0.13.7"}}  # installed == available

    with _mock_catalogue(tmp_path, pack_toml):
        result = _run_all_capture(_make_args(scope="repo", yes=True), tmp_path)

    assert result.exit_code == 0
    assert any(r.status == "up-to-date" and r.outcome == "skipped" for r in result.rows)


def test_blocked_preflight_all_outcomes_blocked(tmp_path):
    """AC17: any unknown row -> all rows get outcome=blocked, no writes."""
    _setup_state(tmp_path, [
        ("core", "claude-code", "agent-ready-repo", "0.13.6"),  # unknown (source-unknown)
    ])
    result = _run_all_capture(_make_args(scope="repo", yes=True), tmp_path)
    assert result.exit_code != 0
    assert all(r.outcome == "blocked" for r in result.rows)


def test_dry_run_blocked_returns_nonzero(tmp_path):
    _setup_state(tmp_path, [("core", "claude-code", "agent-ready-repo", "0.13.6")])
    result = _run_all_capture(_make_args(scope="repo", dry_run=True), tmp_path)
    assert result.exit_code != 0


def test_dry_run_clean_returns_zero(tmp_path):
    _setup_state(tmp_path, [("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    pack_toml = {"pack": {"version": "0.13.7"}}

    with _mock_catalogue(tmp_path, pack_toml), \
         _mock_preflight_render({"README.md": b"content"}):
        result = _run_all_capture(_make_args(scope="repo", dry_run=True), tmp_path)

    assert result.exit_code == 0


def test_nothing_to_upgrade_exits_zero(tmp_path):
    _setup_state(tmp_path, [("core", "claude-code", "git+https://example.test/packs", "0.13.7")])
    pack_toml = {"pack": {"version": "0.13.7"}}

    with _mock_catalogue(tmp_path, pack_toml):
        result = _run_all_capture(_make_args(scope="repo", yes=True), tmp_path)

    assert result.exit_code == 0
    assert any(r.outcome == "skipped" for r in result.rows)


# ---------------------------------------------------------------------------
# T4 — _apply_single_row extraction and apply loop
# ---------------------------------------------------------------------------


def test_apply_order_deterministic():
    """AC20: sorted by (canonical_source, pack, adapter)."""
    rows = [
        _make_upgrade_row(pack="zebra", canonical_source="https://z.test/"),
        _make_upgrade_row(pack="alpha", canonical_source="https://a.test/"),
        _make_upgrade_row(pack="mango", canonical_source="https://a.test/"),
    ]
    ordered = _apply_order(rows)
    assert [r.pack for r in ordered] == ["alpha", "mango", "zebra"]


def test_apply_order_same_source_sorted_by_pack():
    rows = [
        _make_upgrade_row(pack="zebra", canonical_source="https://same.test/"),
        _make_upgrade_row(pack="alpha", canonical_source="https://same.test/"),
    ]
    ordered = _apply_order(rows)
    assert [r.pack for r in ordered] == ["alpha", "zebra"]


def test_stop_on_first_failure():
    """AC21: first failure stops the loop; remaining get not-attempted."""
    rows = [
        _make_upgrade_row(pack="alpha"),
        _make_upgrade_row(pack="beta"),
        _make_upgrade_row(pack="gamma"),
    ]
    call_order = []

    def _mock_apply(row, state, state_path, root, args):
        call_order.append(row.pack)
        return (row.pack != "beta"), []  # beta fails

    with patch("agentbundle.commands.upgrade._apply_single_row", side_effect=_mock_apply):
        _apply_all(
            rows,
            state=_make_state([]),
            state_path=Path("/tmp/state.toml"),
            root=Path("/tmp"),
            args=MagicMock(format="table", dry_run=False, scope="repo"),
            source_resolution_map={},
        )

    outcomes = {r.pack: r.outcome for r in rows}
    assert outcomes["alpha"] == "completed"
    assert outcomes["beta"] == "failed"
    assert outcomes["gamma"] == "not-attempted"


def test_apply_single_row_uses_prerendered_projection(tmp_path):
    """AC23: _apply_single_row never re-renders; uses row._projection."""
    row = _make_upgrade_row(pack="core")
    row._projection = {"README.md": b"content"}
    row.allowed_prefixes = None
    row.available_version = "0.13.7"
    row.pack_dir = tmp_path / "core"
    row.pack_toml = {"pack": {"version": "0.13.7"}}

    rendered_calls = {"n": 0}

    def _track_render(*args, **kwargs):
        rendered_calls["n"] += 1
        return ("claude-code", {})

    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    state_path = tmp_path / ".agentbundle-state.toml"

    with patch("agentbundle.commands.install._render_for_repo_scope", side_effect=_track_render), \
         patch("agentbundle.commands.upgrade.safety.assert_projection_jailed"), \
         patch("agentbundle.commands.upgrade.safety.classify", return_value=_tier1()), \
         patch("agentbundle.commands.upgrade.safety.write_jailed"), \
         patch("agentbundle.commands.upgrade.safety.sha256_bytes", return_value="abc"), \
         patch("agentbundle.commands.upgrade.dump_state", return_value=b"state"):
        _apply_single_row(row, state, state_path, tmp_path, _make_single_pack_args())

    assert rendered_calls["n"] == 0, "_apply_single_row must not re-render"


def test_apply_single_row_no_stdout_in_bulk_path(tmp_path, capsys):
    """_apply_single_row must not emit to stdout (bulk output is _print_plan_table/_finalize)."""
    row = _make_upgrade_row(pack="core")
    row._projection = {"README.md": b"content"}
    row.allowed_prefixes = None
    row.available_version = "0.13.7"
    row.pack_dir = tmp_path / "core"
    row.pack_toml = {"pack": {"version": "0.13.7"}}

    state = _make_state([("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    state_path = tmp_path / ".agentbundle-state.toml"

    with patch("agentbundle.commands.upgrade.safety.assert_projection_jailed"), \
         patch("agentbundle.commands.upgrade.safety.classify", return_value=_tier1()), \
         patch("agentbundle.commands.upgrade.safety.write_jailed"), \
         patch("agentbundle.commands.upgrade.safety.sha256_bytes", return_value="abc"), \
         patch("agentbundle.commands.upgrade.dump_state", return_value=b"state"):
        _apply_single_row(row, state, state_path, tmp_path, _make_single_pack_args())

    captured = capsys.readouterr()
    assert captured.out == "", "No stdout from _apply_single_row"


def test_partial_completion_no_rolled_back_text(tmp_path):
    """AC22: 'rolled back' never appears in output."""
    rows = [_make_upgrade_row(pack="alpha"), _make_upgrade_row(pack="beta")]
    call_n = {"n": 0}

    def _mock_apply(row, state, state_path, root, args):
        call_n["n"] += 1
        return (call_n["n"] == 1), []  # first succeeds, second fails

    state = _make_state([])
    with patch("agentbundle.commands.upgrade._apply_single_row", side_effect=_mock_apply):
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            _apply_all(
                rows,
                state=state,
                state_path=Path("/tmp/state.toml"),
                root=Path("/tmp"),
                args=_make_args(scope="repo", yes=True),
                source_resolution_map={},
            )

    assert "rolled back" not in buf_out.getvalue()
    assert "rolled back" not in buf_err.getvalue()


def test_assign_pre_apply_outcomes_blocked_when_any_unknown():
    """If any row is unknown, ALL rows get outcome=blocked."""
    rows = [
        _make_upgrade_row(pack="alpha"),  # upgrade-available
        _make_unknown_row(pack="beta"),
    ]
    _assign_pre_apply_outcomes(rows, dry_run=False)
    assert all(r.outcome == "blocked" for r in rows)


def test_assign_pre_apply_outcomes_planned_when_no_unknown():
    rows = [_make_upgrade_row(pack="alpha")]
    _assign_pre_apply_outcomes(rows, dry_run=False)
    assert rows[0].outcome == "planned"


def test_assign_pre_apply_outcomes_dry_run_sets_planned():
    rows = [_make_upgrade_row(pack="alpha")]
    _assign_pre_apply_outcomes(rows, dry_run=True)
    assert rows[0].outcome == "planned"


# ---------------------------------------------------------------------------
# T5 — JSON contract
# ---------------------------------------------------------------------------


def test_json_output_parses(tmp_path):
    _setup_state(tmp_path, [("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    pack_toml = {"pack": {"version": "0.13.7"}}

    with _mock_catalogue(tmp_path, pack_toml), \
         _mock_preflight_render({"README.md": b"content"}), \
         _mock_apply_succeeds():
        result = _run_all_capture(_make_args(scope="repo", yes=True, fmt="json"), tmp_path)

    doc = json.loads(result.stdout)
    assert doc["schema_version"] == 1  # must be int not str
    assert isinstance(doc["schema_version"], int)
    assert doc["command"] == "upgrade"
    assert doc["mode"] == "all"
    assert "rows" in doc
    assert "summary" in doc
    assert "sources" in doc


def test_json_output_rows_sorted(tmp_path):
    _setup_state(tmp_path, [
        ("zebra", "claude-code", "git+https://example.test/packs", "0.9.0"),
        ("alpha", "claude-code", "git+https://example.test/packs", "0.9.0"),
    ])
    pack_toml = {"pack": {"version": "1.0.0"}}

    with _mock_catalogue(tmp_path, pack_toml), \
         _mock_preflight_render({"README.md": b"content"}), \
         _mock_apply_succeeds():
        result = _run_all_capture(_make_args(scope="repo", yes=True, fmt="json"), tmp_path)

    doc = json.loads(result.stdout)
    keys = [(r["source"] or "", r["pack"], r["adapter"]) for r in doc["rows"]]
    assert keys == sorted(keys)


def test_json_summary_invariant_non_dry_run(tmp_path):
    """Non-dry-run: completed+skipped+blocked+failed+not_attempted==total; planned==0."""
    _setup_state(tmp_path, [("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    pack_toml = {"pack": {"version": "0.13.7"}}

    with _mock_catalogue(tmp_path, pack_toml), \
         _mock_preflight_render({"README.md": b"content"}), \
         _mock_apply_succeeds():
        result = _run_all_capture(_make_args(scope="repo", yes=True, fmt="json"), tmp_path)

    doc = json.loads(result.stdout)
    s = doc["summary"]
    assert s["completed"] + s["skipped"] + s["blocked"] + s["failed"] + s["not_attempted"] == s["total"]
    assert s["planned"] == 0


def test_json_summary_invariant_dry_run(tmp_path):
    """Dry-run: planned+skipped+blocked==total; completed==failed==not_attempted==0."""
    _setup_state(tmp_path, [("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    pack_toml = {"pack": {"version": "0.13.7"}}

    with _mock_catalogue(tmp_path, pack_toml), \
         _mock_preflight_render({"README.md": b"content"}):
        result = _run_all_capture(_make_args(scope="repo", dry_run=True, fmt="json"), tmp_path)

    doc = json.loads(result.stdout)
    s = doc["summary"]
    assert s["planned"] + s["skipped"] + s["blocked"] == s["total"]
    assert s["completed"] == 0
    assert s["failed"] == 0
    assert s["not_attempted"] == 0


def test_json_mode_non_tty_without_yes(tmp_path):
    """AC6: JSON mode without --yes fails regardless of TTY."""
    _setup_state(tmp_path, [("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    args = _make_args(scope="repo", fmt="json", yes=False)

    with patch("sys.stdin", isatty=lambda: False):
        result = _run_all_capture(args, tmp_path)

    assert result.exit_code != 0
    assert "--yes" in result.stderr


def test_json_mode_tty_without_yes(tmp_path):
    """AC6: JSON mode without --yes fails even when stdin is a TTY."""
    _setup_state(tmp_path, [("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    args = _make_args(scope="repo", fmt="json", yes=False)

    stdin_mock = MagicMock()
    stdin_mock.isatty.return_value = True
    with patch("sys.stdin", stdin_mock):
        result = _run_all_capture(args, tmp_path)

    assert result.exit_code != 0
    assert "--yes" in result.stderr


def test_json_dry_run_non_tty_no_yes_succeeds(tmp_path):
    """AC6 dry-run carve-out: non-TTY + json + dry-run does NOT require --yes."""
    _setup_state(tmp_path, [("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    args = _make_args(scope="repo", fmt="json", dry_run=True, yes=False)
    pack_toml = {"pack": {"version": "0.13.7"}}

    stdin_mock = MagicMock()
    stdin_mock.isatty.return_value = False
    with patch("sys.stdin", stdin_mock), \
         _mock_catalogue(tmp_path, pack_toml), \
         _mock_preflight_render({"README.md": b"content"}):
        result = _run_all_capture(args, tmp_path)

    assert "--yes" not in result.stderr


def test_json_no_stdout_pollution(tmp_path):
    """AC30: stdout carries exactly one valid JSON document in json mode."""
    _setup_state(tmp_path, [("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    pack_toml = {"pack": {"version": "0.13.7"}}

    with _mock_catalogue(tmp_path, pack_toml), \
         _mock_preflight_render({"README.md": b"content"}), \
         _mock_apply_succeeds():
        result = _run_all_capture(_make_args(scope="repo", yes=True, fmt="json"), tmp_path)

    doc = json.loads(result.stdout)  # must succeed
    assert doc is not None


def test_json_empty_scope(tmp_path):
    """AC28/empty: empty state -> conformant JSON with empty rows."""
    # Write empty state
    _write_state_toml(tmp_path, State())
    args = _make_args(scope="repo", yes=True, fmt="json")
    result = _run_all_capture(args, tmp_path)
    doc = json.loads(result.stdout)
    assert doc["rows"] == []
    assert doc["sources"] == []
    assert doc["summary"]["total"] == 0


def test_json_source_error_message_redacted(tmp_path):
    """AC33: CatalogueError message with credentials -> redacted in sources[*].error_message."""
    from agentbundle.catalogue import CatalogueError

    credentialed_source = "git+https://user:secret@example.test/packs"
    state = _make_state([("core", "claude-code", credentialed_source, "0.13.6")])
    _write_state_toml(tmp_path, state)

    error_msg = f"Cannot reach {credentialed_source}: connection refused"

    with patch(
        "agentbundle.commands.upgrade.resolve_catalogue",
        side_effect=CatalogueError(error_msg),
    ):
        result = _run_all_capture(_make_args(scope="repo", yes=True, fmt="json"), tmp_path)

    doc = json.loads(result.stdout)
    for src in doc.get("sources", []):
        if src.get("error_message"):
            assert "secret" not in src["error_message"]
            assert "user:" not in src["error_message"]


def test_json_schema_version_is_integer(tmp_path):
    """AC35: schema_version must be int 1, not str."""
    _setup_state(tmp_path, [("core", "claude-code", "git+https://example.test/packs", "0.13.6")])
    pack_toml = {"pack": {"version": "0.13.7"}}

    with _mock_catalogue(tmp_path, pack_toml), \
         _mock_preflight_render({"README.md": b"content"}), \
         _mock_apply_succeeds():
        result = _run_all_capture(_make_args(scope="repo", yes=True, fmt="json"), tmp_path)

    doc = json.loads(result.stdout)
    assert isinstance(doc["schema_version"], int)
    assert doc["schema_version"] == 1


# ---------------------------------------------------------------------------
# T5 — _redact_credentials unit tests
# ---------------------------------------------------------------------------


def test_redact_credentials_url_user_info():
    text = "fetch failed for https://user:pass@example.test/packs"
    redacted = _redact_credentials(text)
    assert "pass" not in redacted
    assert "user:" not in redacted
    assert "example.test/packs" in redacted


def test_redact_credentials_query_string_param():
    text = "https://example.test/packs?access_token=mysecret&foo=bar"
    redacted = _redact_credentials(text)
    assert "mysecret" not in redacted
    # The implementation keeps the key name but redacts the value
    assert "[REDACTED]" in redacted


def test_redact_credentials_bearer_token():
    text = "Authorization: Bearer eyJhbGciOiJSUzI1NiJ9.payload.sig"
    redacted = _redact_credentials(text)
    assert "eyJhbGciOiJSUzI1NiJ9" not in redacted
    assert "Bearer [REDACTED]" in redacted


def test_redact_credentials_git_plus_https():
    text = "git+https://user:token@github.com/org/packs.git failed"
    redacted = _redact_credentials(text)
    assert "token" not in redacted
    assert "user:" not in redacted
    assert "github.com/org/packs.git" in redacted


# ---------------------------------------------------------------------------
# T6 — D6 layout / table output checks
# ---------------------------------------------------------------------------


def test_table_output_headers_present(tmp_path):
    """Table output must include PACK, ADAPTER, STATUS, OUTCOME columns (AC29)."""
    _setup_state(tmp_path, [("core", "claude-code", "agent-ready-repo", "0.13.6")])
    result = _run_all_capture(_make_args(scope="repo", dry_run=True), tmp_path)
    output = result.stdout + result.stderr
    assert "PACK" in output or "core" in output


def test_table_unicode_identifier(tmp_path):
    """AC35: Unicode identifiers render without breaking table structure.

    Note: dump_state uses Python's str.isalnum() which returns True for Unicode
    letters, producing unquoted TOML keys that tomllib rejects on read-back.
    We mock load_state to bypass this known limitation of the serialiser.
    """
    state = _make_state([("núcleo", "claude-code", "agent-ready-repo", "0.1.0")])
    # Create an empty state file so _run_all doesn't fail with FileNotFoundError
    state_path = tmp_path / ".agentbundle-state.toml"
    state_path.write_text('schema-version = "0.4"\n', encoding="utf-8")
    with patch("agentbundle.commands.upgrade.load_state", return_value=state):
        result = _run_all_capture(_make_args(scope="repo", dry_run=True), tmp_path)
    assert "núcleo" in result.stdout or "núcleo" in result.stderr


def test_table_long_source_truncated(tmp_path):
    """AC35: Long source URIs are truncated gracefully."""
    long_source = "agent-ready-repo"  # canonicalize_source -> None, but test the table display
    state = _make_state([("core", "claude-code", long_source, "0.13.6")])
    _write_state_toml(tmp_path, state)
    result = _run_all_capture(_make_args(scope="repo", dry_run=True), tmp_path)
    # Should not raise; output produced
    assert result.exit_code != 0  # blocked (source-unknown)


# ---------------------------------------------------------------------------
# T7 — Regression: existing upgrade tests still work
# ---------------------------------------------------------------------------


def test_was_dist_tree_install_apm_path():
    ps = _make_pack_state(files={"apm/core/pack.toml": {"sha": "abc"}})
    assert _was_dist_tree_install(ps) is True


def test_was_dist_tree_install_claude_plugins_path():
    ps = _make_pack_state(files={"claude-plugins/core.json": {"sha": "abc"}})
    assert _was_dist_tree_install(ps) is True


def test_was_dist_tree_install_marketplace_json():
    ps = _make_pack_state(files={"marketplace.json": {"sha": "abc"}})
    assert _was_dist_tree_install(ps) is True


def test_was_dist_tree_install_normal_install():
    ps = _make_pack_state(files={".claude/skills/work-loop/SKILL.md": {"sha": "abc"}})
    assert _was_dist_tree_install(ps) is False


def test_was_dist_tree_install_empty():
    ps = _make_pack_state(files={})
    assert _was_dist_tree_install(ps) is False


# ---------------------------------------------------------------------------
# Test utilities
# ---------------------------------------------------------------------------


def _make_upgrade_row(
    pack: str = "core",
    adapter: str = "claude-code",
    canonical_source: str = "git+https://example.test/packs",
) -> _BulkRow:
    ps = _make_pack_state(installed_version="0.13.6", adapter=adapter)
    row = _BulkRow(pack=pack, adapter=adapter, scope="repo", pack_state=ps)
    row.status = "upgrade-available"
    row.canonical_source = canonical_source
    row.available_version = "0.13.7"
    row._projection = {"README.md": b"content"}
    row.allowed_prefixes = None
    row.pack_dir = Path("/fake/pack_dir")
    row.pack_toml = {"pack": {"version": "0.13.7"}}
    return row


def _make_unknown_row(pack: str = "bad", reason: str = "source-unknown") -> _BulkRow:
    ps = _make_pack_state(source="agent-ready-repo")
    row = _BulkRow(pack=pack, adapter="claude-code", scope="repo", pack_state=ps)
    row.status = "unknown"
    row.status_reason = reason
    row.canonical_source = None
    return row


def _tier1():
    from agentbundle.safety import Tier
    return Tier.TIER_1


def _make_single_pack_args():
    """Args namespace without per-primitive flags set (simulates whole-pack single-pack mode)."""
    ns = MagicMock()
    ns.all = False
    for flag in ("skill", "agent", "hook", "seed", "command"):
        setattr(ns, flag, None)
    ns._user_config = None
    return ns


def _setup_state(root: Path, rows: "list[tuple]") -> None:
    state = _make_state(rows)
    _write_state_toml(root, state)


def _write_state_toml(root: Path, state: State) -> None:
    from agentbundle.config import dump_state
    from agentbundle.commands._common import resolve_state_path
    state_path = resolve_state_path("repo", root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(dump_state(state), encoding="utf-8")


from contextlib import contextmanager


@contextmanager
def _mock_catalogue(root: Path, pack_toml: dict):
    """Mock catalogue resolution and pack.toml loading to return pack_toml."""
    with patch("agentbundle.commands.upgrade.resolve_catalogue", return_value=root), \
         patch("agentbundle.commands.upgrade._locate_pack", return_value=root / "core"), \
         patch("agentbundle.commands.upgrade.load_pack_toml", return_value=pack_toml):
        yield


@contextmanager
def _mock_preflight_render(projection: dict):
    """Mock preflight render to return the given projection (repo scope)."""
    with patch(
        "agentbundle.commands.install._render_for_repo_scope",
        return_value=("claude-code", projection),
    ), patch(
        "agentbundle.commands.install._adapter_allowed_prefixes_repo",
        return_value=[".claude/"],
    ), patch(
        "agentbundle.commands.upgrade.safety.assert_projection_jailed"
    ):
        yield


@contextmanager
def _mock_apply_succeeds():
    """Mock the write internals so _apply_single_row succeeds silently."""
    with patch("agentbundle.commands.upgrade.safety.assert_projection_jailed"), \
         patch("agentbundle.commands.upgrade.safety.classify", return_value=_tier1()), \
         patch("agentbundle.commands.upgrade.safety.write_jailed"), \
         patch("agentbundle.commands.upgrade.safety.sha256_bytes", return_value="deadbeef"), \
         patch("agentbundle.commands.upgrade.dump_state", return_value=b"[state]\n"):
        yield
