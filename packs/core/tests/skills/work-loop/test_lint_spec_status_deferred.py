"""Tests for lint-spec-status.py invariant (iv) — workspace.toml [backlog] resolution.

Tests:
  (a) workspace-only slug passes check()
  (c) slug-absent-from-workspace.toml is a HARD violation
  (d) absent workspace.toml → backlog_open_slugs returns empty set
  (e) malformed TOML drives through backlog_open_slugs (not just _regex helper)
  (f) _regex_backlog_slugs directly resolves slugs from [backlog].open
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path

_PACK_ROOT = Path(__file__).parents[3]
_SCRIPT = _PACK_ROOT / ".apm/skills/work-loop/scripts/lint-spec-status.py"


def _load_lint_module() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("lint_spec_status", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_workspace_only_slug_passes_check(tmp_path: Path) -> None:
    """(a) Slug in workspace.toml [backlog].open — check() has no HARD violation."""
    lint = _load_lint_module()

    workspace = tmp_path / "workspace.toml"
    workspace.write_text(
        '[backlog]\nopen = [{slug = "my-ws-only-slug"}]\n', encoding="utf-8", newline="\n"
    )

    specs = tmp_path / "docs" / "specs" / "my-spec"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        "- **Status:** Approved\n\n## Acceptance Criteria\n\n"
        "- [ ] do thing (deferred: my-ws-only-slug)\n",
        encoding="utf-8",
        newline="\n",
    )

    hard, _warn = lint.check(tmp_path, base_ref=None)
    # No HARD violation — slug resolves via workspace.toml
    assert not any("my-ws-only-slug" in v for v in hard), (
        f"Expected my-ws-only-slug to resolve; hard violations: {hard}"
    )


def test_slug_absent_from_workspace_is_hard_violation(tmp_path: Path) -> None:
    """(c) Slug absent from workspace.toml [backlog].open → HARD violation."""
    lint = _load_lint_module()

    specs = tmp_path / "docs" / "specs" / "my-spec"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        "- **Status:** Approved\n\n## Acceptance Criteria\n\n"
        "- [ ] do thing (deferred: nonexistent-slug)\n",
        encoding="utf-8",
        newline="\n",
    )
    (tmp_path / "workspace.toml").write_text(
        "[backlog]\nopen = []\n", encoding="utf-8", newline="\n"
    )

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
        newline="\n",
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


def test_canonical_entry_anchor_derivation() -> None:
    """(g) A canonical entry's `path` reduces to the anchor its slug used to be."""
    lint = _load_lint_module()

    # Non-spec artifacts anchor on the file stem, which is exactly how the
    # shaping slugs these entries replaced were already named.
    assert lint.canonical_entry_anchor(
        "docs/product/design/workspace-anchor-staleness-invariant.md"
    ) == "workspace-anchor-staleness-invariant"
    assert lint.canonical_entry_anchor(
        "docs/product/intents/selftest-untracked-plant-window.md"
    ) == "selftest-untracked-plant-window"
    # A spec or plan anchors on its owning directory, never on "spec"/"plan".
    assert lint.canonical_entry_anchor("docs/specs/my-feature/spec.md") == "my-feature"
    assert lint.canonical_entry_anchor("docs/specs/my-feature/plan.md") == "my-feature"
    # Degenerate input yields no anchor rather than a bogus one.
    assert lint.canonical_entry_anchor("") is None
    assert lint.canonical_entry_anchor("/") is None


def test_canonical_backlog_entry_resolves_deferral_anchor(tmp_path: Path) -> None:
    """(h) A canonical `{path=...}` entry resolves invariant (iv).

    Before this, only a legacy `{slug=...}` record could satisfy a deferral
    anchor, so a spec that deferred was obliged to write a legacy-shaped
    workspace record in order to pass a hard gate.
    """
    lint = _load_lint_module()

    workspace = tmp_path / "workspace.toml"
    workspace.write_text(
        "[backlog]\nopen = [\n"
        '  {path = "docs/product/captured/anchor-staleness.md", kind = "design", '
        'source = {mode = "repo-origin"}, summary = "s", needs = []},\n'
        "]\n",
        encoding="utf-8",
        newline="\n",
    )

    specs = tmp_path / "docs" / "specs" / "my-spec"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        "- **Status:** Approved\n\n## Acceptance Criteria\n\n"
        "- [ ] do thing (deferred: anchor-staleness)\n",
        encoding="utf-8",
        newline="\n",
    )

    hard, _warn = lint.check(tmp_path, base_ref=None)
    assert not any("anchor-staleness" in v for v in hard), (
        f"canonical entry should resolve the anchor; hard violations: {hard}"
    )


def test_unresolvable_anchor_still_hard_with_canonical_entries(tmp_path: Path) -> None:
    """(i) Broadening the resolver must not make invariant (iv) unfailable."""
    lint = _load_lint_module()

    workspace = tmp_path / "workspace.toml"
    workspace.write_text(
        "[backlog]\nopen = [\n"
        '  {path = "docs/product/captured/present.md", kind = "design", '
        'source = {mode = "repo-origin"}, summary = "s", needs = []},\n'
        "]\n",
        encoding="utf-8",
        newline="\n",
    )

    specs = tmp_path / "docs" / "specs" / "my-spec"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        "- **Status:** Approved\n\n## Acceptance Criteria\n\n"
        "- [ ] do thing (deferred: absent-anchor)\n",
        encoding="utf-8",
        newline="\n",
    )

    hard, _warn = lint.check(tmp_path, base_ref=None)
    assert any("absent-anchor" in v for v in hard), (
        f"expected a HARD violation for an unresolvable anchor; got: {hard}"
    )


def test_bare_status_form_warns(tmp_path: Path) -> None:
    """(j) A bare `**Status:**` warns: the workspace engine reads it as absent."""
    lint = _load_lint_module()
    (tmp_path / "workspace.toml").write_text(
        "[backlog]\nopen = []\n", encoding="utf-8", newline="\n"
    )

    for name, header in (
        ("bare-form", "**Status:** Shipped\n"),
        ("list-form", "- **Status:** Shipped\n"),
    ):
        specs = tmp_path / "docs" / "specs" / name
        specs.mkdir(parents=True)
        (specs / "spec.md").write_text(
            header + "\n## Acceptance Criteria\n\n- [x] done\n",
            encoding="utf-8",
            newline="\n",
        )

    _hard, warn = lint.check(tmp_path, base_ref=None)
    assert any("bare-form" in w and "list-item form" in w for w in warn), warn
    assert not any("list-form/spec.md" in w and "list-item form" in w for w in warn), warn


# --- AC-0035: an open intent or brief file also resolves an anchor ----------

_ANCHOR = "some-captured-item"


def _plant_spec(root: Path, anchor: str = _ANCHOR) -> None:
    spec = root / "docs" / "specs" / "my-spec"
    spec.mkdir(parents=True)
    (spec / "spec.md").write_text(
        "- **Status:** Approved\n\n## Acceptance Criteria\n\n"
        f"- [ ] do thing (deferred: {anchor})\n",
        encoding="utf-8",
        newline="\n",
    )
    (root / "workspace.toml").write_text("[backlog]\nopen = []\n", encoding="utf-8")


def _plant_file(root: Path, kind: str, text: str, anchor: str = _ANCHOR) -> Path:
    directory = root / "docs" / "product" / kind
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{anchor}.md"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _violations(root: Path, anchor: str = _ANCHOR) -> list[str]:
    hard, _warn = _load_lint_module().check(root, base_ref=None)
    return [v for v in hard if anchor in v]


def test_open_intent_file_resolves_anchor(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    _plant_file(tmp_path, "intents", "# Intent\n\n- **Status:** Draft\n\n## Body\n")
    assert _violations(tmp_path) == []


def test_open_brief_file_resolves_anchor(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    _plant_file(tmp_path, "briefs", "# Brief\n\n- **Status:** Active (2026-01-01)\n")
    assert _violations(tmp_path) == []


def test_draft_preamble_with_later_fulfilled_body_line_resolves(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    _plant_file(
        tmp_path,
        "intents",
        "# Intent\n\n- **Status:** Draft\n\n## History\n\n- **Status:** Fulfilled\n",
    )
    assert _violations(tmp_path) == []


def test_backlog_open_entry_still_resolves(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    (tmp_path / "workspace.toml").write_text(
        f'[backlog]\nopen = [{{slug = "{_ANCHOR}"}}]\n', encoding="utf-8"
    )
    assert _violations(tmp_path) == []


def test_symlinked_intent_file_does_not_resolve(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    target = tmp_path / "elsewhere.md"
    target.write_text("- **Status:** Draft\n", encoding="utf-8")
    directory = tmp_path / "docs" / "product" / "intents"
    directory.mkdir(parents=True)
    (directory / f"{_ANCHOR}.md").symlink_to(target)
    assert _violations(tmp_path)


def test_closed_intent_files_do_not_resolve(tmp_path: Path) -> None:
    for status in ("Fulfilled", "Withdrawn", "Cancelled", "Superseded"):
        root = tmp_path / status
        root.mkdir()
        _plant_spec(root)
        _plant_file(root, "intents", f"# Intent\n\n- **Status:** {status}\n")
        assert _violations(root), status


def test_closed_brief_files_do_not_resolve(tmp_path: Path) -> None:
    for status in ("Shipped", "Withdrawn", "Cancelled"):
        root = tmp_path / status
        root.mkdir()
        _plant_spec(root)
        _plant_file(root, "briefs", f"# Brief\n\n- **Status:** {status} (2026-01-01)\n")
        assert _violations(root), status


def test_tombstone_intent_file_does_not_resolve(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    _plant_file(
        tmp_path,
        "intents",
        f"- **Slug:** {_ANCHOR}\n- **Tombstone:** true\n- **Reissued:** other\n",
    )
    assert _violations(tmp_path)


def test_status_line_after_section_heading_does_not_resolve(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    _plant_file(tmp_path, "intents", "# Intent\n\n## Notes\n\n- **Status:** Draft\n")
    assert _violations(tmp_path)


def test_anchor_nothing_resolves_is_violation(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    assert _violations(tmp_path)
