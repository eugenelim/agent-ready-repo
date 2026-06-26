"""T2 (RFC-0052 / ADR-0039): pure footprint-ownership verdict helpers.

Co-ownership is intra-pack + content-addressed: two adapter rows co-own a
path only when they belong to the same pack AND the SHA matches. A same-path
different-SHA clash, or any cross-pack same-path claim (even at equal SHA),
is a conflict.
"""

from __future__ import annotations

from agentbundle import config
from agentbundle.config import FootprintVerdict, PackState, State


def _state(*rows: tuple[str, str, dict[str, str]]) -> State:
    """Build a State from (pack, adapter, {relpath: sha}) triples."""
    st = State()
    for pack, adapter, files in rows:
        st.packs[(pack, adapter)] = PackState(
            installed_version="1.0.0",
            adapter=adapter,
            files={r: {"sha": sha} for r, sha in files.items()},
        )
    return st


# ---------------------------------------------------------------------------
# owner-set derivation
# ---------------------------------------------------------------------------


def test_owners_of_spans_all_rows() -> None:
    st = _state(
        ("research", "codex", {"a": "1"}),
        ("research", "cursor", {"a": "1", "b": "2"}),
        ("other", "claude-code", {"c": "3"}),
    )
    assert set(st.owners_of("a")) == {("research", "codex"), ("research", "cursor")}
    assert st.owners_of("b") == [("research", "cursor")]
    assert st.owners_of("missing") == []


# ---------------------------------------------------------------------------
# per-relpath verdict
# ---------------------------------------------------------------------------


def test_absent_path_is_new() -> None:
    st = _state(("research", "codex", {"a": "1"}))
    assert config.classify_incoming_path(st, "research", "cursor", "b", "9") == "new"


def test_same_pack_same_sha_is_coown() -> None:
    st = _state(("research", "codex", {"a": "1"}))
    assert config.classify_incoming_path(st, "research", "cursor", "a", "1") == "coown"


def test_same_row_same_sha_is_own() -> None:
    st = _state(("research", "codex", {"a": "1"}))
    assert config.classify_incoming_path(st, "research", "codex", "a", "1") == "own"


def test_same_pack_different_sha_is_conflict() -> None:
    st = _state(("research", "codex", {"a": "1"}))
    assert config.classify_incoming_path(st, "research", "cursor", "a", "2") == "conflict"


def test_cross_pack_same_path_is_conflict_even_at_equal_sha() -> None:
    st = _state(("other", "claude-code", {"a": "1"}))
    assert config.classify_incoming_path(st, "research", "codex", "a", "1") == "conflict"


# ---------------------------------------------------------------------------
# aggregate verdict
# ---------------------------------------------------------------------------


def test_all_owned_matching_is_already_installed() -> None:
    st = _state(("research", "codex", {"a": "1", "b": "2"}))
    plan = config.footprint_plan(st, "research", "codex", {"a": "1", "b": "2"})
    assert plan.verdict is FootprintVerdict.ALREADY_INSTALLED


def test_some_new_no_conflict_proceeds() -> None:
    st = _state(("research", "codex", {"a": "1"}))
    plan = config.footprint_plan(st, "research", "codex", {"a": "1", "b": "2"})
    assert plan.verdict is FootprintVerdict.PROCEED
    assert plan.per_path["b"] == "new"


def test_coown_only_proceeds_not_already_installed() -> None:
    # A sibling row owns the shared path; this row does not yet → proceed
    # (there is ownership to record), not already-installed.
    st = _state(("research", "codex", {"a": "1"}))
    plan = config.footprint_plan(st, "research", "cursor", {"a": "1"})
    assert plan.verdict is FootprintVerdict.PROCEED
    assert plan.per_path["a"] == "coown"


def test_any_conflict_refuses_and_names_paths() -> None:
    st = _state(("research", "codex", {"a": "1", "b": "2"}))
    plan = config.footprint_plan(st, "research", "cursor", {"a": "1", "b": "999"})
    assert plan.verdict is FootprintVerdict.REFUSE
    assert plan.conflicts == ["b"]


def test_disjoint_footprints_coexist_proceeds() -> None:
    # The reported bug: research for codex after claude-code. Disjoint trees.
    st = _state(("research", "claude-code", {".claude/skills/x/SKILL.md": "1"}))
    plan = config.footprint_plan(
        st, "research", "codex", {".agents/skills/x/SKILL.md": "1"}
    )
    assert plan.verdict is FootprintVerdict.PROCEED
    assert plan.per_path[".agents/skills/x/SKILL.md"] == "new"
