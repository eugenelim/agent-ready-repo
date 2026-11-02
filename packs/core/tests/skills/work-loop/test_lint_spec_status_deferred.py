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
    _captured(tmp_path, "my-item", "# Item\n\n- **Status:** Open\n- **Kind:** defect\n")
    assert _hard(tmp_path, "my-item") == []


def test_closed_captured_file_resolves_anchor(tmp_path: Path) -> None:
    _spec_deferring(tmp_path, "my-item")
    _captured(tmp_path, "my-item", "# Item\n\n- **Status:** Closed\n- **Kind:** defect\n- **Resolution:** fixed\n")
    assert _hard(tmp_path, "my-item") == []


def test_backlog_open_entry_without_captured_file_is_refused(tmp_path: Path) -> None:
    _spec_deferring(tmp_path, "my-item")
    (tmp_path / "workspace.toml").write_text(
        '[backlog]\nopen = [{slug = "my-item"}]\n', encoding="utf-8", newline="\n"
    )
    assert _hard(tmp_path, "my-item")


def test_captured_file_the_reader_rejects_does_not_resolve(tmp_path: Path) -> None:
    """A file with no valid `Kind:`, or Closed with no `Resolution:`, never resolves."""
    for index, body in enumerate((
        "# Item\n\n- **Status:** Open\n",
        "# Item\n\n- **Status:** Open\n- **Kind:** bogus\n",
        "# Item\n\n- **Status:** Closed\n- **Kind:** defect\n",
        "# Item\n\n- **Status:** Open\n- **Kind:** defect\n- **Resolution:** fixed\n",
    )):
        root = tmp_path / f"r{index}"
        _spec_deferring(root, "my-item")
        _captured(root, "my-item", body)
        assert _hard(root, "my-item"), body


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
    target.write_text("- **Status:** Open\n- **Kind:** defect\n", encoding="utf-8")
    directory = tmp_path / "docs" / "product" / "captured"
    directory.mkdir(parents=True)
    (directory / "my-item.md").symlink_to(target)
    assert _hard(tmp_path, "my-item")


def test_hard_linked_captured_file_is_refused(tmp_path: Path) -> None:
    _spec_deferring(tmp_path, "my-item")
    path = _captured(tmp_path, "my-item", "# Item\n\n- **Status:** Open\n- **Kind:** defect\n")
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
    _captured(tmp_path, _ANCHOR, "# Item\n\n- **Status:** Closed\n- **Kind:** defect\n- **Resolution:** fixed\n")
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
    _captured(tmp_path, _ANCHOR, "# Item\n\n- **Status:** Open\n- **Kind:** defect\n")
    assert _violations(tmp_path) == []


_ENGINE = _PACK_ROOT / ".apm/skills/workspace-status/scripts/workspace_status_engine.py"
_BASE = "# Item\n\n- **Status:** Open\n- **Kind:** defect\n"
_PARITY_BODIES = {
    "open": _BASE,
    "closed": "# Item\n\n- **Status:** Closed\n- **Kind:** defect\n- **Resolution:** fixed\n",
    "closed-no-resolution": "# Item\n\n- **Status:** Closed\n- **Kind:** defect\n",
    "open-with-resolution": _BASE + "- **Resolution:** fixed\n",
    "bad-resolution": "# Item\n\n- **Status:** Closed\n- **Kind:** defect\n- **Resolution:** done\n",
    "bad-status": "# Item\n\n- **Status:** Draft\n- **Kind:** defect\n",
    "no-kind": "# Item\n\n- **Status:** Open\n",
    "bad-kind": "# Item\n\n- **Status:** Open\n- **Kind:** bogus\n",
    "kind-first-word": "# Item\n\n- **Status:** Open\n- **Kind:** defect (regression)\n",
    "good-type": _BASE + "- **Type:** shape\n",
    "bad-type": _BASE + "- **Type:** bogus\n",
    "empty-type": _BASE + "- **Type:**\n",
    "good-parent": _BASE + "- **Parent intent:** intent:my-intent\n",
    "spec-parent": _BASE + "- **Parent intent:** spec:my-spec\n",
    "untyped-parent": _BASE + "- **Parent intent:** my-intent\n",
    "good-detail": _BASE + "- **Detail:** docs/product/notes/more.md\n",
    "spec-detail": _BASE + "- **Detail:** docs/specs/x/spec.md\n",
    "intent-detail": _BASE + "- **Detail:** docs/product/intents/x.md\n",
    "traversal-detail": _BASE + "- **Detail:** ../x.md\n",
    "repeated-status": _BASE + "- **Status:** Open\n",
    "repeated-type": _BASE + "- **Type:** shape\n- **Type:** shape\n",
    "fenced-kind": "# Item\n\n- **Status:** Open\n```\n- **Kind:** defect\n```\n",
    "fenced-repeat": _BASE + "```\n- **Kind:** design\n```\n",
    "after-heading": _BASE + "\n## Notes\n\n- **Type:** bogus\n",
    "comment-hidden": _BASE + "<!--\n- **Type:** bogus\n-->\n",
    "repeated-depends-on": _BASE + "- **Depends on:** a\n- **Depends on:** b\n",
    "tilde-fence": _BASE + "~~~\n- **Kind:** design\n~~~\n",
    "long-opener-short-inner": _BASE + "````\n```\n- **Kind:** design\n````\n",
    "close-with-info-string": _BASE + "```\n```js\n- **Kind:** design\n```\n",
}


def _load_engine() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("last_registry_parity_engine", _ENGINE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    import sys

    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_lint_accepts_exactly_what_the_captured_item_reader_accepts() -> None:
    """One table of bodies runs through the lint and `parse_captured_item`."""
    lint = _load_lint_module()
    engine = _load_engine()
    disagreements = [
        name
        for name, body in _PARITY_BODIES.items()
        if lint.captured_text_is_valid(body) != (engine.parse_captured_item(body)[0] is not None)
    ]
    assert disagreements == []
    verdicts = {n: lint.captured_text_is_valid(b) for n, b in _PARITY_BODIES.items()}
    assert verdicts["good-type"] and verdicts["good-parent"] and verdicts["good-detail"]
    assert verdicts["fenced-repeat"] and verdicts["comment-hidden"] and verdicts["after-heading"]
    assert not any(
        verdicts[n]
        for n in ("bad-type", "spec-parent", "untyped-parent", "spec-detail",
                  "intent-detail", "traversal-detail", "repeated-status",
                  "repeated-type", "fenced-kind", "bad-resolution", "empty-type")
    )
    assert all(
        verdicts[n]
        for n in ("repeated-depends-on", "tilde-fence", "long-opener-short-inner",
                  "close-with-info-string")
    )


def test_anchor_does_not_resolve_through_a_file_the_reader_rejects(tmp_path: Path) -> None:
    """Each field the reader rejects keeps a deferral anchor unresolved."""
    for name in ("bad-type", "spec-parent", "spec-detail", "repeated-type", "fenced-kind"):
        root = tmp_path / name
        _spec_deferring(root, "my-item")
        _captured(root, "my-item", _PARITY_BODIES[name])
        assert _hard(root, "my-item"), name


def _reader_lists_cleanly(engine: types.ModuleType, root: Path, anchor: str) -> bool:
    """True when the reader lists `<anchor>.md` as an item with no finding."""
    listing = engine.list_captured_items(root, frozenset())
    bad = {f.path for f in listing.findings}
    return any(
        item["slug"] == anchor and item["path"] not in bad for item in listing.items
    )


def test_anchor_resolution_matches_the_reader_listing(tmp_path: Path) -> None:
    """`captured_file_resolves` agrees with the reader for file bytes and anchor names."""
    lint = _load_lint_module()
    engine = _load_engine()
    cases: list[tuple[str, str, bytes, str]] = [
        ("repeated-depends-on", "my-item", _PARITY_BODIES["repeated-depends-on"].encode(), "my-item"),
        ("non-utf8", "my-item", _BASE.encode() + b"\xff\xfe\n", "my-item"),
        ("off-grammar", "my_item", _BASE.encode(), "my_item"),
        ("leading-hyphen", "-item", _BASE.encode(), "-item"),
        # Guards case-insensitive filesystems only; `upper-file` and `off-grammar`
        # carry the name check on case-sensitive ones.
        ("case-variant", "my-item", _BASE.encode(), "My-Item"),
        ("upper-file", "My-Item", _BASE.encode(), "My-Item"),
        ("plain", "my-item", _BASE.encode(), "my-item"),
    ]
    for label, file_slug, data, anchor in cases:
        root = tmp_path / label
        path = root / "docs" / "product" / "captured" / f"{file_slug}.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(data)
        assert lint.captured_file_resolves(root, anchor) == _reader_lists_cleanly(
            engine, root, anchor
        ), label
    assert lint.captured_file_resolves(tmp_path / "plain", "my-item")
    assert not lint.captured_file_resolves(tmp_path / "non-utf8", "my-item")
    assert not lint.captured_file_resolves(tmp_path / "case-variant", "My-Item")
    assert not lint.captured_file_resolves(tmp_path / "off-grammar", "my_item")


def test_captured_file_over_the_read_cap_does_not_resolve(tmp_path: Path) -> None:
    """The lint's read cap is the one accepted difference from the reader.

    The padding is a comment line, so the file is otherwise valid; no parity
    with the reader is asserted for this case.
    """
    lint = _load_lint_module()
    padding = "x" * (lint._MAX_FILE_BYTES + 1)
    data = _BASE + f"\n<!-- {padding} -->\n"
    assert lint.captured_text_is_valid(data)
    path = _captured(tmp_path, "my-item", data)
    assert path.stat().st_size > lint._MAX_FILE_BYTES
    assert not lint.captured_file_resolves(tmp_path, "my-item")
