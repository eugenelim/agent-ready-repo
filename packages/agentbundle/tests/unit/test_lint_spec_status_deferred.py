"""TDD stubs for lint-spec-status.py invariant (iv) dual-source rewrite.

Tests:
  (a) workspace-only slug passes check() — red until T4b wires the union in check()
  (b) tombstone heading slug resolves — passes via existing backlog_anchors()
  (c) slug-in-neither is a HARD violation
  (d) absent workspace.toml → backlog_open_slugs returns empty set
  (e) malformed TOML drives through backlog_open_slugs (not just _regex helper)
  (f) _regex_backlog_slugs directly resolves slugs from [backlog].open
"""
from __future__ import annotations

import importlib.util
import types
from pathlib import Path

_REPO_ROOT = Path(__file__).parents[4]
_SCRIPT = _REPO_ROOT / "packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py"


def _load_lint_module() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("lint_spec_status", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_workspace_only_slug_passes_check(tmp_path: Path) -> None:
    """(a) Slug present only in workspace.toml [backlog].open — check() has no HARD violation."""
    lint = _load_lint_module()

    workspace = tmp_path / "workspace.toml"
    workspace.write_text('[backlog]\nopen = [{slug = "my-ws-only-slug"}]\n', encoding="utf-8")

    backlog = tmp_path / "docs" / "backlog.md"
    backlog.parent.mkdir(parents=True)
    backlog.write_text("# tombstone\n", encoding="utf-8")  # no heading with that slug

    specs = tmp_path / "docs" / "specs" / "my-spec"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        "- **Status:** Approved\n\n## Acceptance Criteria\n\n"
        "- [ ] do thing (deferred: my-ws-only-slug)\n",
        encoding="utf-8",
    )

    hard, _warn = lint.check(tmp_path, base_ref=None)
    # No HARD violation — slug resolves via workspace.toml
    assert not any("my-ws-only-slug" in v for v in hard), (
        f"Expected my-ws-only-slug to resolve; hard violations: {hard}"
    )


def test_tombstone_heading_slug_passes(tmp_path: Path) -> None:
    """(b) Slug from a docs/backlog.md heading resolves (tombstone backward-compat)."""
    lint = _load_lint_module()

    backlog = tmp_path / "docs" / "backlog.md"
    backlog.parent.mkdir(parents=True)
    backlog.write_text("### credbroker-phase-2\n\nsome text\n", encoding="utf-8")

    anchors = lint.backlog_anchors(backlog.read_text())
    assert "credbroker-phase-2" in anchors


def test_slug_in_neither_is_hard_violation(tmp_path: Path) -> None:
    """(c) Slug absent from both workspace.toml and backlog.md → HARD violation."""
    lint = _load_lint_module()

    specs = tmp_path / "docs" / "specs" / "my-spec"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        "- **Status:** Approved\n\n## Acceptance Criteria\n\n"
        "- [ ] do thing (deferred: nonexistent-slug)\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "backlog.md").write_text("# tombstone\n", encoding="utf-8")
    (tmp_path / "workspace.toml").write_text("[backlog]\nopen = []\n", encoding="utf-8")

    hard, _warn = lint.check(tmp_path, base_ref=None)
    assert any("nonexistent-slug" in v for v in hard)


def test_absent_workspace_toml_returns_empty_slugs(tmp_path: Path) -> None:
    """(d) workspace.toml absent → backlog_open_slugs returns empty set."""
    lint = _load_lint_module()
    slugs = lint.backlog_open_slugs(tmp_path / "workspace.toml")
    assert slugs == set()


def test_malformed_toml_falls_back_via_backlog_open_slugs(tmp_path: Path) -> None:
    """(e) Malformed TOML — backlog_open_slugs catches parse error, falls back to regex."""
    lint = _load_lint_module()

    workspace = tmp_path / "workspace.toml"
    # Well-formed enough for regex to find the slug line, but invalid as TOML
    workspace.write_text(
        '[backlog]\nopen = [\n  {slug = "alpha"},\n  invalid syntax here\n]\n',
        encoding="utf-8",
    )
    slugs = lint.backlog_open_slugs(workspace)
    assert "alpha" in slugs


def test_regex_backlog_slugs_helper(tmp_path: Path) -> None:
    """(f) _regex_backlog_slugs directly resolves slugs from [backlog].open."""
    lint = _load_lint_module()

    text = '[backlog]\nopen = [\n  {slug = "alpha"},\n  {slug = "beta"},\n]\n'
    slugs = lint._regex_backlog_slugs(text)
    assert "alpha" in slugs
    assert "beta" in slugs
