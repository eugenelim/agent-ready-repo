"""Construction tests for the `Depends on:` / `Dependency receipts:` header reader.

Spec: docs/specs/depends-on-headers/spec.md (AC-0001, AC-0002, AC-0004,
AC-0027, AC-0028). Verification mode: TDD.

Each test plants one case in a ``tmp_path`` repository, reads the waiting
item's header, and asserts the one finding it expects and no other.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_ENGINE_PATH = (
    Path(__file__).resolve().parents[3]
    / ".apm/skills/workspace-status/scripts/workspace_status_engine.py"
)
_MODULE_NAME = "workspace_status_engine_depends_on_headers_reader"


def _load_engine() -> ModuleType:
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _ENGINE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(_MODULE_NAME, None)
    return module


ENGINE = _load_engine()
WAITER = "docs/specs/waiter/spec.md"
BRIEFS = "docs/product/briefs"
INTENTS = "docs/product/intents"
COMPLETION = "completion d-1 completed merge pr:812"
COORDINATION = "coordination spec remote-prereq remote-rev-9"


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _waiter(*header: str, body: str = "") -> str:
    lines = "\n".join(header)
    return f"# Spec: waiter\n\n- **Status:** Approved\n{lines}\n{body}"


def _read(
    root: Path,
    *header: str,
    body: str = "",
    kinds: dict[str, str] | None = None,
    cooled: frozenset[Path] = frozenset(),
    waiting: str = WAITER,
):
    """Write the waiting item, build the index, and read its header."""
    _write(root, waiting, _waiter(*header, body=body))
    index = ENGINE.build_resolution_index(root, cooled=cooled)
    return ENGINE.read_header_dependencies(
        root, waiting, index=index, membership_kinds=kinds or {}, cooled=cooled
    )


def _deps(result) -> list[tuple[str, str, str]]:
    return [(d.type, d.kind, d.path) for d in result.dependencies]


def _codes(result) -> list[str]:
    return [f.code for f in result.findings]


def _brief(root: Path, name: str, preamble: str = "") -> None:
    _write(root, f"{BRIEFS}/{name}.md", f"# Brief\n\n- **Status:** Ready\n{preamble}")


def _intent(root: Path, name: str, preamble: str) -> None:
    _write(root, f"{INTENTS}/{name}.md", f"# Intent\n\n{preamble}\n")


def _depends(value: str) -> str:
    return f"- **Depends on:** {value}"


def _receipts(value: str) -> str:
    return f"- **Dependency receipts:** {value}"


# ── Dependency items (AC-0001, AC-0002) ──────────────────────────────────────


def test_typed_spec_reference_resolves_without_a_listing(tmp_path: Path) -> None:
    result = _read(tmp_path, _depends("spec:alpha"))
    assert _deps(result) == [("local", "spec", "docs/specs/alpha/spec.md")]
    assert _codes(result) == []


def test_none_line_contributes_no_item(tmp_path: Path) -> None:
    result = _read(tmp_path, _depends("none (nothing waits)"))
    assert _deps(result) == [] and _codes(result) == []


def test_empty_item_is_dropped(tmp_path: Path) -> None:
    result = _read(tmp_path, _depends("spec:alpha, , spec:beta,"))
    assert [d.path for d in result.dependencies] == [
        "docs/specs/alpha/spec.md",
        "docs/specs/beta/spec.md",
    ]
    assert _codes(result) == []


def test_repeated_lines_all_contribute(tmp_path: Path) -> None:
    result = _read(tmp_path, _depends("spec:alpha"), _depends("spec:beta"))
    assert [d.path for d in result.dependencies] == [
        "docs/specs/alpha/spec.md",
        "docs/specs/beta/spec.md",
    ]
    assert _codes(result) == []


def test_comment_hidden_item_is_ignored(tmp_path: Path) -> None:
    result = _read(
        tmp_path,
        _depends("spec:alpha <!-- spec:hidden -->"),
        "<!--",
        _depends("spec:also-hidden"),
        "-->",
    )
    assert [d.path for d in result.dependencies] == ["docs/specs/alpha/spec.md"]
    assert _codes(result) == []


def test_body_text_decoy_is_ignored(tmp_path: Path) -> None:
    result = _read(
        tmp_path,
        _depends("spec:alpha"),
        body="\n## Notes\n\n- **Depends on:** spec:decoy\n",
    )
    assert [d.path for d in result.dependencies] == ["docs/specs/alpha/spec.md"]
    assert _codes(result) == []


def test_fenced_decoy_is_ignored(tmp_path: Path) -> None:
    result = _read(
        tmp_path,
        _depends("spec:alpha"),
        "```",
        _depends("spec:decoy"),
        "```",
    )
    assert [d.path for d in result.dependencies] == ["docs/specs/alpha/spec.md"]
    assert _codes(result) == []


def test_path_in_place_of_spec_reference_is_invalid(tmp_path: Path) -> None:
    result = _read(tmp_path, _depends("docs/specs/alpha/spec.md"))
    assert _codes(result) == ["invalid_dependency"]
    assert _deps(result) == []
    assert result.findings[0].path == WAITER
    # A repository path to a spec meets neither grammar, so it is withheld.
    assert "alpha" not in result.findings[0].detail


def test_brief_or_intent_path_is_not_a_captured_item(tmp_path: Path) -> None:
    result = _read(
        tmp_path, _depends(f"{BRIEFS}/one.md, {INTENTS}/two.md")
    )
    assert _codes(result) == ["invalid_dependency", "invalid_dependency"]
    assert _deps(result) == []


def test_free_text_item_is_invalid_not_missing(tmp_path: Path) -> None:
    result = _read(tmp_path, _depends("the auth rework"))
    assert _codes(result) == ["invalid_dependency"]
    assert _deps(result) == []


def test_item_with_bad_slug_is_invalid(tmp_path: Path) -> None:
    result = _read(tmp_path, _depends("spec:Not_A_Slug"))
    assert _codes(result) == ["invalid_dependency"]


def test_indented_continuation_line_is_invalid(tmp_path: Path) -> None:
    result = _read(tmp_path, _depends("spec:alpha,"), "  spec:beta")
    assert _codes(result) == ["invalid_dependency"]
    assert [d.path for d in result.dependencies] == ["docs/specs/alpha/spec.md"]


def test_indented_continuation_under_receipts_is_invalid(tmp_path: Path) -> None:
    result = _read(
        tmp_path,
        _depends("spec:alpha"),
        _receipts(f"spec:alpha {COMPLETION},"),
        "\t spec:beta completion d-2 completed merge pr:1",
    )
    assert _codes(result) == ["invalid_dependency"]


# ── Brief and intent references (resolution index) ───────────────────────────


def test_brief_resolves_by_slug_field(tmp_path: Path) -> None:
    _brief(tmp_path, "file-name", "- **Slug:** `partner` <!-- c -->\n")
    result = _read(tmp_path, _depends("brief:partner"))
    assert _deps(result) == [("local", "brief", f"{BRIEFS}/file-name.md")]
    assert _codes(result) == []


def test_brief_resolves_by_stem_when_no_slug_field(tmp_path: Path) -> None:
    _brief(tmp_path, "partner")
    result = _read(tmp_path, _depends("brief:partner"))
    assert _deps(result) == [("local", "brief", f"{BRIEFS}/partner.md")]
    assert _codes(result) == []


def test_brief_stem_does_not_match_when_slug_field_differs(tmp_path: Path) -> None:
    _brief(tmp_path, "partner", "- **Slug:** other\n")
    result = _read(tmp_path, _depends("brief:partner"))
    assert _deps(result) == [("local", "brief", "brief:partner")]
    assert _codes(result) == []


def test_ambiguous_brief_slug_is_invalid(tmp_path: Path) -> None:
    _brief(tmp_path, "one", "- **Slug:** shared\n")
    _brief(tmp_path, "shared")
    result = _read(tmp_path, _depends("brief:shared"))
    assert _codes(result) == ["invalid_dependency"]
    assert _deps(result) == []


def test_intent_resolves_with_backticked_slug_and_level(tmp_path: Path) -> None:
    _intent(
        tmp_path,
        "acct",
        "- **Slug:** `account-management` <!-- c -->\n"
        "- **Level:** `capability` <!-- c -->",
    )
    result = _read(tmp_path, _depends("capability:account-management"))
    assert _deps(result) == [("local", "intent", f"{INTENTS}/acct.md")]
    assert _codes(result) == []


def test_intent_kind_comes_from_kind_field(tmp_path: Path) -> None:
    _intent(tmp_path, "goal", "- **Slug:** goal\n- **Kind:** `Outcome`")
    _intent(tmp_path, "plain", "- **Slug:** plain\n- **Kind:** outcome <!-- c -->")
    result = _read(tmp_path, _depends("outcome:plain, intent:plain"))
    assert _deps(result) == [
        ("local", "intent", f"{INTENTS}/plain.md"),
        ("local", "intent", "intent:plain"),
    ]
    assert _codes(result) == []


def test_kind_mismatched_intent_reference_is_a_missing_target(tmp_path: Path) -> None:
    _intent(tmp_path, "goal", "- **Slug:** goal\n- **Kind:** opportunity")
    result = _read(tmp_path, _depends("outcome:goal"))
    assert _deps(result) == [("local", "intent", "outcome:goal")]
    assert _codes(result) == []


def test_tombstone_and_live_intent_sharing_a_slug_resolve_to_the_live_one(
    tmp_path: Path,
) -> None:
    _intent(tmp_path, "old", "- **Slug:** shared\n- **Tombstone:** moved")
    _intent(tmp_path, "live", "- **Slug:** shared")
    result = _read(tmp_path, _depends("intent:shared"))
    assert _deps(result) == [("local", "intent", f"{INTENTS}/live.md")]
    assert _codes(result) == []


def test_names_outside_the_live_intent_pattern_are_ignored(tmp_path: Path) -> None:
    _write(tmp_path, f"{INTENTS}/.hidden.md", "- **Slug:** ghost\n")
    _write(tmp_path, f"{INTENTS}/notes.txt", "- **Slug:** ghost\n")
    _write(tmp_path, f"{INTENTS}/sub/deep.md", "- **Slug:** ghost\n")
    result = _read(tmp_path, _depends("intent:ghost"))
    assert _deps(result) == [("local", "intent", "intent:ghost")]
    assert _codes(result) == []


def test_typed_references_with_no_target_are_missing_targets(tmp_path: Path) -> None:
    result = _read(tmp_path, _depends("spec:nowhere, brief:nobody, intent:noone"))
    assert _deps(result) == [
        ("local", "spec", "docs/specs/nowhere/spec.md"),
        ("local", "brief", "brief:nobody"),
        ("local", "intent", "intent:noone"),
    ]
    assert _codes(result) == []


# ── Resolution index failures (AC-0027) ──────────────────────────────────────


def test_refused_briefs_listing_is_unreadable_not_missing(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "partner.md").write_text("# Brief\n", encoding="utf-8")
    repo = tmp_path / "repo"
    (repo / "docs/product").mkdir(parents=True)
    (repo / BRIEFS).symlink_to(outside, target_is_directory=True)
    result = _read(repo, _depends("brief:partner"))
    assert _codes(result) == ["unreadable_artifact"]
    assert _deps(result) == []


def test_unreadable_listed_brief_file_is_unreadable_not_missing(
    tmp_path: Path,
) -> None:
    _brief(tmp_path, "fine")
    (tmp_path / BRIEFS / "broken.md").mkdir()
    result = _read(tmp_path, _depends("brief:fine, brief:absent"))
    assert _codes(result) == ["unreadable_artifact", "unreadable_artifact"]
    assert _deps(result) == []


def test_refused_intents_listing_leaves_briefs_resolving(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    repo = tmp_path / "repo"
    (repo / "docs/product").mkdir(parents=True)
    (repo / INTENTS).symlink_to(outside, target_is_directory=True)
    _brief(repo, "partner")
    result = _read(repo, _depends("brief:partner, intent:goal, spec:alpha"))
    assert _codes(result) == ["unreadable_artifact"]
    assert _deps(result) == [
        ("local", "brief", f"{BRIEFS}/partner.md"),
        ("local", "spec", "docs/specs/alpha/spec.md"),
    ]


def test_symlinked_listed_brief_escaping_the_directory_is_refused(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    _brief(repo, "fine")
    (repo / "docs/specs").mkdir(parents=True)
    (repo / "docs/specs/target.md").write_text("# x\n", encoding="utf-8")
    (repo / BRIEFS / "link.md").symlink_to(repo / "docs/specs/target.md")
    result = _read(repo, _depends("brief:fine"))
    assert _codes(result) == ["unreadable_artifact"]


def test_cooled_brief_is_never_opened_and_matches_by_stem(tmp_path: Path) -> None:
    _brief(tmp_path, "cooled-one", "- **Slug:** hidden-slug\n")
    path = (tmp_path / BRIEFS / "cooled-one.md").resolve()
    original = Path.read_text

    def guarded(self: Path, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        assert self.resolve() != path, "a cooled body was opened"
        return original(self, *args, **kwargs)

    Path.read_text = guarded  # type: ignore[method-assign]
    try:
        result = _read(tmp_path, _depends("brief:cooled-one"), cooled=frozenset({path}))
    finally:
        Path.read_text = original  # type: ignore[method-assign]
    assert _deps(result) == [("local", "brief", f"{BRIEFS}/cooled-one.md")]
    assert _codes(result) == []


def test_cooled_waiting_item_is_never_opened(tmp_path: Path) -> None:
    _write(tmp_path, WAITER, _waiter(_depends("spec:alpha")))
    cooled = frozenset({(tmp_path / WAITER).resolve()})
    (tmp_path / WAITER).chmod(0)
    try:
        index = ENGINE.build_resolution_index(tmp_path, cooled=cooled)
        result = ENGINE.read_header_dependencies(
            tmp_path, WAITER, index=index, membership_kinds={}, cooled=cooled
        )
    finally:
        (tmp_path / WAITER).chmod(0o644)
    assert _deps(result) == [] and _codes(result) == []


# ── Captured-item references ─────────────────────────────────────────────────


def test_captured_item_path_takes_its_membership_kind(tmp_path: Path) -> None:
    _write(tmp_path, "docs/design/ui.md", "# D\n")
    result = _read(
        tmp_path,
        _depends("docs/design/ui.md"),
        kinds={"docs/design/ui.md": "design"},
    )
    assert _deps(result) == [("local", "design", "docs/design/ui.md")]
    assert _codes(result) == []


def test_defect_file_under_spec_notes_named_as_captured_item(tmp_path: Path) -> None:
    ref = "docs/specs/d/notes/defect-one.md"
    _write(tmp_path, ref, "# Defect\n\n- **Kind:** defect\n")
    result = _read(tmp_path, _depends(ref))
    assert _deps(result) == [("local", "defect", ref)]
    assert _codes(result) == []


def test_captured_item_with_kind_line_defect_and_no_membership(tmp_path: Path) -> None:
    _write(tmp_path, "backlog/bug.md", "# B\n\n- **Kind:** `defect` <!-- c -->\n")
    result = _read(tmp_path, _depends("backlog/bug.md"))
    assert _deps(result) == [("local", "defect", "backlog/bug.md")]
    assert _codes(result) == []


def test_membership_kind_wins_over_the_files_own_kind_line(tmp_path: Path) -> None:
    _write(tmp_path, "backlog/bug.md", "# B\n\n- **Kind:** research\n")
    result = _read(
        tmp_path, _depends("backlog/bug.md"), kinds={"backlog/bug.md": "defect"}
    )
    assert _deps(result) == [("local", "defect", "backlog/bug.md")]


def test_existing_captured_item_with_no_kind_is_invalid(tmp_path: Path) -> None:
    _write(tmp_path, "notes/idea.md", "# Idea\n\n- **Status:** Open\n")
    result = _read(tmp_path, _depends("notes/idea.md"))
    assert _codes(result) == ["invalid_dependency"]
    assert _deps(result) == []


def test_captured_item_with_no_file_and_no_membership_is_a_missing_target(
    tmp_path: Path,
) -> None:
    result = _read(tmp_path, _depends("notes/gone.md"))
    assert _deps(result) == [("local", "", "notes/gone.md")]
    assert _codes(result) == []


def test_captured_item_path_with_dot_segment_is_invalid(tmp_path: Path) -> None:
    result = _read(tmp_path, _depends("notes/../secret.md"))
    assert _codes(result) == ["invalid_dependency"]


# ── Dependency receipts (AC-0004) ────────────────────────────────────────────


def test_completion_receipt_fills_the_receipt_dict(tmp_path: Path) -> None:
    result = _read(
        tmp_path, _depends("spec:alpha"), _receipts(f"spec:alpha {COMPLETION}")
    )
    assert _codes(result) == []
    assert result.dependencies[0].receipt == {
        "delivery_id": "d-1",
        "outcome": "completed",
        "completion_event": "merge",
        "evidence_ref": "pr:812",
    }


def test_oversized_completion_receipt_field_is_the_malformed_sentinel(
    tmp_path: Path,
) -> None:
    long_ref = "x" * 600
    result = _read(
        tmp_path,
        _depends("spec:alpha"),
        _receipts(f"spec:alpha completion d-1 completed merge {long_ref}"),
    )
    assert _codes(result) == []
    assert result.dependencies[0].receipt == ENGINE._MALFORMED_COMPLETION_RECEIPT


def test_coordination_receipt_makes_a_cross_repo_dependency(tmp_path: Path) -> None:
    _brief(tmp_path, "partner")
    result = _read(
        tmp_path, _depends("brief:partner"), _receipts(f"brief:partner {COORDINATION}")
    )
    assert _codes(result) == []
    (dep,) = result.dependencies
    assert (dep.type, dep.kind) == ("cross-repo", "spec")
    assert dep.path == dep.containing_brief == f"{BRIEFS}/partner.md"
    assert (dep.receipt_id, dep.accepted_revision) == ("remote-prereq", "remote-rev-9")


def test_receipts_split_on_commas(tmp_path: Path) -> None:
    _brief(tmp_path, "partner")
    result = _read(
        tmp_path,
        _depends("spec:alpha, brief:partner"),
        _receipts(f"spec:alpha {COMPLETION}, brief:partner {COORDINATION}"),
    )
    assert _codes(result) == []
    assert [d.type for d in result.dependencies] == ["local", "cross-repo"]


def test_receipt_for_a_reference_not_in_the_header_is_invalid(tmp_path: Path) -> None:
    result = _read(
        tmp_path, _depends("spec:alpha"), _receipts(f"spec:beta {COMPLETION}")
    )
    assert _codes(result) == ["invalid_dependency"]
    assert result.dependencies[0].receipt is None


def test_second_receipt_for_one_reference_is_invalid(tmp_path: Path) -> None:
    result = _read(
        tmp_path,
        _depends("spec:alpha"),
        _receipts(f"spec:alpha {COMPLETION}, spec:alpha completion d-2 abandoned merge pr:2"),
    )
    assert _codes(result) == ["invalid_dependency"]
    assert result.dependencies[0].receipt["delivery_id"] == "d-1"


def test_unknown_receipt_keyword_is_invalid(tmp_path: Path) -> None:
    result = _read(
        tmp_path,
        _depends("spec:alpha"),
        _receipts("spec:alpha settled d-1 completed merge pr:1"),
    )
    assert _codes(result) == ["invalid_dependency"]


@pytest.mark.parametrize(
    "receipt",
    [
        "spec:alpha completion d-1 completed merge",
        "spec:alpha completion d-1 completed merge pr:1 extra",
        "spec:alpha coordination spec remote-prereq",
        "spec:alpha",
    ],
)
def test_wrong_token_count_is_invalid(tmp_path: Path, receipt: str) -> None:
    result = _read(tmp_path, _depends("spec:alpha"), _receipts(receipt))
    assert _codes(result) == ["invalid_dependency"]


def test_coordination_receipt_on_a_non_brief_reference_is_invalid(
    tmp_path: Path,
) -> None:
    result = _read(
        tmp_path, _depends("spec:alpha"), _receipts(f"spec:alpha {COORDINATION}")
    )
    assert _codes(result) == ["invalid_dependency"]
    assert [d.type for d in result.dependencies] == ["local"]


def test_completion_receipt_on_a_captured_item_is_invalid(tmp_path: Path) -> None:
    ref = "docs/design/ui.md"
    result = _read(
        tmp_path,
        _depends(ref),
        _receipts(f"{ref} {COMPLETION}"),
        kinds={ref: "design"},
    )
    assert _codes(result) == ["invalid_dependency"]
    assert result.dependencies[0].receipt is None
    assert ref in result.findings[0].detail


@pytest.mark.parametrize(
    "tail",
    [
        "spec remote#prereq remote-rev-9",
        "spec remote-prereq rev?9",
        "spec remote-prereq " + "r" * 201,
        "widget remote-prereq remote-rev-9",
    ],
)
def test_coordination_value_outside_the_token_grammar_is_refused(
    tmp_path: Path, tail: str
) -> None:
    _brief(tmp_path, "partner")
    result = _read(
        tmp_path,
        _depends("brief:partner"),
        _receipts(f"brief:partner coordination {tail}"),
    )
    assert _codes(result) == ["invalid_entry"]
    assert [d.type for d in result.dependencies] == ["local"]


# ── Echo rule (AC-0028) ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("reference", "setup"),
    [
        ("spec:alpha", None),
        ("brief:partner", "brief"),
        ("intent:goal", "intent"),
        ("docs/design/ui.md", "captured"),
    ],
)
def test_valid_references_are_echoed_verbatim(
    tmp_path: Path, reference: str, setup: str | None
) -> None:
    kinds: dict[str, str] = {}
    if setup == "brief":
        _brief(tmp_path, "partner")
    elif setup == "intent":
        _intent(tmp_path, "goal", "- **Slug:** goal")
    elif setup == "captured":
        kinds[reference] = "design"
    result = _read(
        tmp_path,
        _depends(reference),
        _receipts(f"{reference} wat"),
        kinds=kinds,
    )
    assert _codes(result) == ["invalid_dependency"]
    assert result.findings[0].path == WAITER
    assert reference in result.findings[0].detail


def test_free_text_item_is_withheld_from_the_finding(tmp_path: Path) -> None:
    result = _read(tmp_path, _depends("the auth rework"))
    assert "auth" not in result.findings[0].detail


def test_oversized_item_is_withheld(tmp_path: Path) -> None:
    ref = "notes/" + "a" * 250
    result = _read(tmp_path, _depends(f"spec:alpha, {ref}/../x"))
    assert _codes(result) == ["invalid_dependency"]
    assert "aaaa" not in result.findings[0].detail
    long_valid = "spec:" + "a" * 300
    result = _read(tmp_path, _depends(long_valid), _receipts(f"{long_valid} wat"))
    assert _codes(result) == ["invalid_dependency"]
    assert "aaaa" not in result.findings[0].detail


def test_control_character_item_is_withheld(tmp_path: Path) -> None:
    result = _read(tmp_path, _depends("notes/bad\x1bname"))
    assert _codes(result) == ["invalid_dependency"]
    assert "\x1b" not in result.findings[0].detail
    assert "bad" not in result.findings[0].detail


def test_overlong_waiting_path_is_withheld(tmp_path: Path) -> None:
    waiting = f"docs/specs/{'w' * 210}/spec.md"
    result = _read(tmp_path, _depends("nonsense item"), waiting=waiting)
    assert _codes(result) == ["invalid_dependency"]
    assert result.findings[0].path == ""


# ── Reader refuses a cooled path and an unusable waiting item ────────────────


def test_unreadable_waiting_item_gives_unreadable_artifact(tmp_path: Path) -> None:
    (tmp_path / WAITER).parent.mkdir(parents=True)
    (tmp_path / WAITER).mkdir()
    index = ENGINE.build_resolution_index(tmp_path)
    result = ENGINE.read_header_dependencies(
        tmp_path, WAITER, index=index, membership_kinds={}, cooled=frozenset()
    )
    assert _codes(result) == ["unreadable_artifact"]


def test_missing_waiting_item_reads_as_empty(tmp_path: Path) -> None:
    index = ENGINE.build_resolution_index(tmp_path)
    result = ENGINE.read_header_dependencies(
        tmp_path, WAITER, index=index, membership_kinds={}, cooled=frozenset()
    )
    assert _deps(result) == [] and _codes(result) == []


def test_index_is_built_once_and_reused(tmp_path: Path) -> None:
    _brief(tmp_path, "partner")
    index = ENGINE.build_resolution_index(tmp_path)
    assert index.briefs == {"partner": (f"{BRIEFS}/partner.md",)}
    assert not index.briefs_unreadable and not index.intents_unreadable


# ── T8: a dependency finding's path obeys AC-0028's bound ────────────────────


@pytest.mark.parametrize(
    "item",
    [
        "spec:" + "a" * 300,
        "docs/product/notes/" + "b" * 300 + ".md",
    ],
    ids=["oversized-typed", "oversized-captured"],
)
def test_oversized_dependency_path_is_withheld_and_the_code_kept(
    tmp_path: Path, item: str
) -> None:
    import tomllib

    _write(tmp_path, WAITER, _waiter(_depends(item)))
    _write(tmp_path, "docs/specs/waiter/plan.md", "# Plan\n")
    workspace = tomllib.loads(
        '["ini-001"]\nname = "F"\nstatus = "active"\nmilestone = "m1"\n\n'
        '["ini-001".work]\n'
        f'queue = [{{path = "{WAITER}", kind = "spec", source = {{mode = "repo-origin"}}, '
        'summary = "w", needs = []}]\nactive = []\nshipped = []\n'
    )
    result = ENGINE.run_canonical_reconciliation(workspace, tmp_path)
    findings = result.dispatch_by_path[WAITER].findings
    missing = [f for f in findings if f.code == "missing_dependency"]
    assert len(missing) == 1, [(f.code, f.path) for f in findings]
    assert all(len(f.path) <= 200 for f in findings)
    assert item not in {f.path for f in findings}
    assert missing[0].path == ""


def _metadata_for(root: Path, path: str, kind: str = "spec"):
    entry = ENGINE.WorkspaceEntry(
        path=path,
        kind=kind,
        source=ENGINE.SourceRecord(mode="repo-origin"),
        summary="probe",
        needs=[],
    )
    return ENGINE._metadata_from_root(root, entry)


def test_a_name_too_long_reads_as_missing(tmp_path: Path) -> None:
    metadata = _metadata_for(tmp_path, "docs/specs/" + "a" * 300 + "/spec.md")
    assert metadata is not None and metadata.exists is False


def test_an_unsearchable_parent_reads_as_unreadable_not_missing(tmp_path: Path) -> None:
    import os

    if os.name == "nt" or os.geteuid() == 0:
        pytest.skip("needs POSIX permissions enforced for the current user")
    target = tmp_path / "docs" / "specs" / "locked" / "spec.md"
    target.parent.mkdir(parents=True)
    target.write_text("- **Status:** Approved\n", encoding="utf-8")
    target.parent.chmod(0)
    try:
        metadata = _metadata_for(tmp_path, "docs/specs/locked/spec.md")
    finally:
        target.parent.chmod(0o755)
    assert metadata is not None
    assert (metadata.exists, metadata.readable) == (True, False)


def test_a_waiting_item_under_an_unsearchable_directory_is_unreadable(tmp_path: Path) -> None:
    import os

    if os.name == "nt" or os.geteuid() == 0:
        pytest.skip("needs POSIX permissions enforced for the current user")
    waiting = tmp_path / "docs" / "specs" / "waiter" / "spec.md"
    waiting.parent.mkdir(parents=True)
    waiting.write_text("- **Status:** Draft\n- **Depends on:** spec:alpha\n", encoding="utf-8")
    index = ENGINE.build_resolution_index(tmp_path)
    waiting.parent.chmod(0)
    try:
        header = ENGINE.read_header_dependencies(
            tmp_path,
            "docs/specs/waiter/spec.md",
            index=index,
            membership_kinds={},
            cooled=frozenset(),
        )
    finally:
        waiting.parent.chmod(0o755)
    assert header.dependencies == ()
    assert [f.code for f in header.findings] == ["unreadable_artifact"]
