"""Tests for lint-spec-status.py invariant (iv) -- captured-item file resolution.

A `(deferred: <slug>)` marker resolves through `docs/product/captured/<slug>.md`
(whatever its Status) or an open intent, brief or spec file; `workspace.toml`
is never read for anchors.
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


def _spec_deferring(root: Path, anchor: str) -> None:
    specs = root / "docs" / "specs" / "my-spec"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        "- **Status:** Approved\n\n## Acceptance Criteria\n\n"
        f"- [ ] do thing (deferred: {anchor})\n",
        encoding="utf-8",
        newline="\n",
    )


def _captured(root: Path, slug: str, text: str) -> Path:
    path = root / "docs" / "product" / "captured" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _hard(root: Path, anchor: str) -> list[str]:
    hard, _warn = _load_lint_module().check(root, base_ref=None)
    return [v for v in hard if anchor in v]


def test_open_captured_file_resolves_anchor(tmp_path: Path) -> None:
    _spec_deferring(tmp_path, "my-item")
    _captured(tmp_path, "my-item", "# Item\n\n- **Status:** Open\n")
    assert _hard(tmp_path, "my-item") == []


def test_closed_captured_file_resolves_anchor(tmp_path: Path) -> None:
    _spec_deferring(tmp_path, "my-item")
    _captured(tmp_path, "my-item", "# Item\n\n- **Status:** Closed\n- **Resolution:** fixed\n")
    assert _hard(tmp_path, "my-item") == []


def test_backlog_open_entry_without_captured_file_is_refused(tmp_path: Path) -> None:
    _spec_deferring(tmp_path, "my-item")
    (tmp_path / "workspace.toml").write_text(
        '[backlog]\nopen = [{slug = "my-item"}]\n', encoding="utf-8", newline="\n"
    )
    assert _hard(tmp_path, "my-item")


def test_workspace_toml_is_not_opened_for_anchors(tmp_path: Path) -> None:
    _spec_deferring(tmp_path, "my-item")
    _captured(tmp_path, "my-item", "# Item\n\n- **Status:** Open\n")
    # A directory in place of the file would raise if the lint opened it.
    (tmp_path / "workspace.toml").mkdir()
    assert _hard(tmp_path, "my-item") == []


def test_unresolved_message_names_captured_path(tmp_path: Path) -> None:
    _spec_deferring(tmp_path, "my-item")
    (violation,) = _hard(tmp_path, "my-item")
    assert "docs/product/captured/my-item.md" in violation
    assert "workspace.toml" not in violation


def test_captured_file_without_status_header_is_refused(tmp_path: Path) -> None:
    _spec_deferring(tmp_path, "my-item")
    _captured(tmp_path, "my-item", "# Item\n\nno header here\n")
    assert _hard(tmp_path, "my-item")


def test_symlinked_captured_file_is_refused(tmp_path: Path) -> None:
    _spec_deferring(tmp_path, "my-item")
    target = tmp_path / "elsewhere.md"
    target.write_text("- **Status:** Open\n", encoding="utf-8")
    directory = tmp_path / "docs" / "product" / "captured"
    directory.mkdir(parents=True)
    (directory / "my-item.md").symlink_to(target)
    assert _hard(tmp_path, "my-item")


def test_hard_linked_captured_file_is_refused(tmp_path: Path) -> None:
    _spec_deferring(tmp_path, "my-item")
    path = _captured(tmp_path, "my-item", "# Item\n\n- **Status:** Open\n")
    (tmp_path / "second-link.md").hardlink_to(path)
    assert _hard(tmp_path, "my-item")


def test_open_intent_still_resolves_anchor(tmp_path: Path) -> None:
    _spec_deferring(tmp_path, "my-item")
    directory = tmp_path / "docs" / "product" / "intents"
    directory.mkdir(parents=True)
    (directory / "my-item.md").write_text("# I\n\n- **Status:** Draft\n", encoding="utf-8")
    assert _hard(tmp_path, "my-item") == []


def test_bare_status_form_warns(tmp_path: Path) -> None:
    """(j) A bare `**Status:**` warns: the workspace engine reads it as absent."""
    lint = _load_lint_module()

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


def test_captured_file_still_resolves(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    _captured(tmp_path, _ANCHOR, "# Item\n\n- **Status:** Closed\n")
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


# --- AC-0021: an open spec file also resolves an anchor ----------------------


def _plant_open_spec(root: Path, status: str, anchor: str = _ANCHOR) -> Path:
    directory = root / "docs" / "specs" / anchor
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "spec.md"
    path.write_text(f"# Spec\n\n- **Status:** {status}\n\n## Body\n", encoding="utf-8")
    return path


def test_open_spec_files_resolve_anchor(tmp_path: Path) -> None:
    for index, status in enumerate(
        ("Draft", "Approved", "Implementing", "Implementing (2026-01-01)")
    ):
        root = tmp_path / str(index)
        root.mkdir()
        _plant_spec(root)
        _plant_open_spec(root, status)
        assert _violations(root) == [], status


def test_closed_spec_files_do_not_resolve_anchor(tmp_path: Path) -> None:
    for status in ("Shipped (2026-01-01)", "Archived"):
        root = tmp_path / status.split()[0]
        root.mkdir()
        _plant_spec(root)
        _plant_open_spec(root, status)
        assert _violations(root), status


def test_spec_status_after_heading_does_not_resolve(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    directory = tmp_path / "docs" / "specs" / _ANCHOR
    directory.mkdir(parents=True)
    (directory / "spec.md").write_text("# S\n\n## Notes\n\n- **Status:** Draft\n", encoding="utf-8")
    assert _violations(tmp_path)


def test_symlinked_spec_file_does_not_resolve_anchor(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    target = tmp_path / "elsewhere.md"
    target.write_text("- **Status:** Draft\n", encoding="utf-8")
    directory = tmp_path / "docs" / "specs" / _ANCHOR
    directory.mkdir(parents=True)
    (directory / "spec.md").symlink_to(target)
    assert _violations(tmp_path)


def test_symlinked_spec_directory_does_not_resolve_anchor(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    real = tmp_path / "elsewhere"
    real.mkdir()
    (real / "spec.md").write_text("- **Status:** Draft\n", encoding="utf-8")
    (tmp_path / "docs" / "specs" / _ANCHOR).symlink_to(real, target_is_directory=True)
    assert _violations(tmp_path)


def test_symlinked_specs_directory_does_not_resolve_anchor(tmp_path: Path) -> None:
    real = tmp_path / "elsewhere"
    _plant_open_spec(real, "Draft")
    (real / "docs").rename(tmp_path / "moved")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "specs").symlink_to(tmp_path / "moved" / "specs", target_is_directory=True)
    assert not _load_lint_module().open_spec_resolves(tmp_path, _ANCHOR)


def test_base_cases_keep_results(tmp_path: Path) -> None:
    _plant_spec(tmp_path)
    assert _violations(tmp_path)
    _captured(tmp_path, _ANCHOR, "# Item\n\n- **Status:** Open\n")
    assert _violations(tmp_path) == []
