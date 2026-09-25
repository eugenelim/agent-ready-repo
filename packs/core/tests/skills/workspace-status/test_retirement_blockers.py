"""Tests for blocker detection — T5 (TDD).

Verification mode: TDD.
Spec:  docs/specs/spec-retirement-eligibility/spec.md  §§ Blocker emission,
       Status vocabulary, Age reporting
Plan:  docs/specs/spec-retirement-eligibility/plan.md  § T5

T5 requirements verified here
------------------------------
1.  One fixture per blocker code, enumerated from the module's BLOCKER_CODES
    constant (which T7 will pin to the schema enum), each asserting the code
    fires and the candidate is not eligible due only to that code.
2.  A candidate with two workspace dependents lists both, and each entry
    carries the needs edge that clears it.
3.  One fixture per needs shape (list of tables, bare string, empty list, key
    absent) asserting none is refused; plus a table pointing outside docs/specs/
    asserting it yields no edge.
4.  Removing every declaring edge from a fixture clears the needed-by blocker;
    removing only one of two does not.
5.  A candidate cited from a governance surface carries inbound-cited naming
    that surface.
6.  A candidate free of every blocker is eligible with an empty list.
7.  ``Shipped (2026-05-26)`` is classified terminal, not refused.
8.  The recognised status set equals lint-spec-status.py's.
9.  An unrecognised collection name is classified "unrecognised".
10. cutoff_date equals run_date minus stale_after_days.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module loading
# ---------------------------------------------------------------------------

_PACK_ROOT = Path(__file__).resolve().parents[3]
_CANDIDATES_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "workspace-status"
    / "scripts"
    / "workspace_status_retirement_candidates.py"
)
_RETIREMENT_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "workspace-status"
    / "scripts"
    / "workspace_status_retirement.py"
)

_CANDIDATES_MODULE_NAME = "workspace_status_retirement_candidates_t5"
_RETIREMENT_MODULE_NAME = "workspace_status_retirement_t5"


def _load_candidates():
    """Load the candidates module under a unique name."""
    if _CANDIDATES_MODULE_NAME in sys.modules:
        return sys.modules[_CANDIDATES_MODULE_NAME]
    spec = importlib.util.spec_from_file_location(
        _CANDIDATES_MODULE_NAME, _CANDIDATES_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {_CANDIDATES_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_CANDIDATES_MODULE_NAME] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_retirement():
    """Load the retirement module under a unique name."""
    if _RETIREMENT_MODULE_NAME in sys.modules:
        return sys.modules[_RETIREMENT_MODULE_NAME]
    spec = importlib.util.spec_from_file_location(
        _RETIREMENT_MODULE_NAME, _RETIREMENT_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {_RETIREMENT_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_RETIREMENT_MODULE_NAME] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def _clean_candidate() -> dict:
    """Return a candidate dict with all conditions clean (no blockers)."""
    return {
        "slug": "target-spec",
        "eligible": True,
        "blockers": [],
        "held_back_by": [],
    }


def _clean_workspace_data() -> dict:
    """Return a workspace.toml dict with target-spec in work.shipped (terminal)."""
    return {
        "ini-001": {
            "work": {
                "shipped": [
                    {"path": "docs/specs/target-spec/spec.md", "needs": []},
                ],
            },
        },
    }


# ---------------------------------------------------------------------------
# Group 1: Status vocabulary — T5 requirement 7, 8
# ---------------------------------------------------------------------------

class TestStatusVocabulary:
    """Status line parsing: both formats, leading token, terminal/non-terminal."""

    def test_list_format_recognised(self) -> None:
        """The majority list-item format is parsed correctly."""
        mod = _load_candidates()
        result = mod.parse_spec_status("- **Status:** Shipped\n")
        assert result is not None
        token, raw = result
        assert token == "Shipped"

    def test_bare_format_recognised(self) -> None:
        """The bare bold-line format (16 specs in corpus) is parsed correctly."""
        mod = _load_candidates()
        result = mod.parse_spec_status("**Status:** Shipped\n")
        assert result is not None
        token, raw = result
        assert token == "Shipped"

    def test_annotated_value_classified_by_leading_token(self) -> None:
        """'Shipped (2026-05-26)' is classified terminal, not refused.

        Spec § Status vocabulary:
        'A Status: value is reduced to its leading token before comparison,
        so an annotated value such as Shipped (2026-05-26) is classified by
        Shipped.'
        """
        mod = _load_candidates()
        result = mod.parse_spec_status("- **Status:** Shipped (2026-05-26)\n")
        assert result is not None, (
            "parse_spec_status must not refuse an annotated Shipped value"
        )
        token, raw = result
        assert token == "Shipped", (
            f"Leading token must be 'Shipped', got {token!r}. "
            "Annotated values must be classified by their leading token."
        )
        assert token in mod.TERMINAL_STATUSES, (
            "Shipped (2026-05-26) must be classified terminal, not refused."
        )

    def test_no_status_line_returns_none(self) -> None:
        """A spec with no Status line returns None."""
        mod = _load_candidates()
        result = mod.parse_spec_status("# Spec\n\nNo status here.\n")
        assert result is None

    def test_draft_is_non_terminal(self) -> None:
        """Draft is a recognised non-terminal status."""
        mod = _load_candidates()
        result = mod.parse_spec_status("- **Status:** Draft\n")
        assert result is not None
        token, _ = result
        assert token == "Draft"
        assert token in mod.CANONICAL_STATUSES
        assert mod.detect_status_not_terminal(token) is True

    def test_shipped_is_terminal(self) -> None:
        """Shipped is a terminal status — detect_status_not_terminal returns False."""
        mod = _load_candidates()
        assert mod.detect_status_not_terminal("Shipped") is False

    def test_archived_is_terminal(self) -> None:
        """Archived is also terminal."""
        mod = _load_candidates()
        assert mod.detect_status_not_terminal("Archived") is False

    def test_implementing_is_non_terminal(self) -> None:
        """Implementing is non-terminal."""
        mod = _load_candidates()
        assert mod.detect_status_not_terminal("Implementing") is True

    def test_status_set_equals_lint_spec_status(self) -> None:
        """The module's CANONICAL_STATUSES equals lint-spec-status.py's set.

        Spec § Status vocabulary:
        'The recognised set this capability compares against is identical to
        the set lint-spec-status enforces, and a test fails when the two diverge.'
        """
        import importlib.util as _ilu
        import sys as _sys
        lint_path = (
            _PACK_ROOT
            / ".apm"
            / "skills"
            / "work-loop"
            / "scripts"
            / "lint-spec-status.py"
        )
        lint_mod_name = "lint_spec_status_t5_check"
        if lint_mod_name not in _sys.modules:
            lint_spec = _ilu.spec_from_file_location(lint_mod_name, lint_path)
            if lint_spec is None or lint_spec.loader is None:
                pytest.skip(f"Cannot load lint-spec-status.py from {lint_path}")
            lint_mod = _ilu.module_from_spec(lint_spec)
            _sys.modules[lint_mod_name] = lint_mod
            lint_spec.loader.exec_module(lint_mod)
        else:
            lint_mod = _sys.modules[lint_mod_name]

        mod = _load_candidates()
        expected = lint_mod.CANONICAL_STATUSES
        actual = mod.CANONICAL_STATUSES
        assert actual == expected, (
            f"CANONICAL_STATUSES diverges from lint-spec-status.py:\n"
            f"  candidates module: {sorted(actual)}\n"
            f"  lint-spec-status:  {sorted(expected)}\n"
            "Update CANONICAL_STATUSES in workspace_status_retirement_candidates.py."
        )

    def test_html_comment_stripped_before_tokenisation(self) -> None:
        """Trailing HTML comment is stripped, e.g. 'Approved <!-- Draft | ... -->' → 'Approved'."""
        mod = _load_candidates()
        body = "- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->\n"
        result = mod.parse_spec_status(body)
        assert result is not None
        token, _ = result
        assert token == "Approved", (
            f"Expected 'Approved' after stripping comment, got {token!r}"
        )


# ---------------------------------------------------------------------------
# Group 2: Cutoff computation — T5 requirement 10
# ---------------------------------------------------------------------------

class TestCutoffComputation:
    """cutoff_date equals run_date minus stale_after_days."""

    def test_cutoff_is_correct(self) -> None:
        """compute_cutoff_date returns run_date − stale_after_days."""
        mod = _load_candidates()
        result = mod.compute_cutoff_date("2026-09-25", 30)
        assert result == "2026-08-26", (
            f"Expected '2026-08-26', got {result!r}. "
            "cutoff_date must equal run_date − stale_after_days."
        )

    def test_cutoff_zero_days(self) -> None:
        """stale_after_days=0 returns the run_date itself."""
        mod = _load_candidates()
        assert mod.compute_cutoff_date("2026-09-25", 0) == "2026-09-25"

    def test_cutoff_default_thirty_days(self) -> None:
        """Default stale_after_days is 30; test a concrete calculation."""
        mod = _load_candidates()
        # 30 days before 2026-10-01 is 2026-09-01
        assert mod.compute_cutoff_date("2026-10-01", 30) == "2026-09-01"

    def test_cutoff_returns_calendar_date(self) -> None:
        """Emitted cutoff_date is always a YYYY-MM-DD calendar date."""
        mod = _load_candidates()
        result = mod.compute_cutoff_date("2026-09-25", 30)
        import re
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", result), (
            f"cutoff_date must be a calendar date, got {result!r}"
        )

    def test_cutoff_negative_days_raises(self) -> None:
        """Negative stale_after_days raises ValueError."""
        mod = _load_candidates()
        with pytest.raises(ValueError):
            mod.compute_cutoff_date("2026-09-25", -1)

    def test_cutoff_invalid_run_date_raises(self) -> None:
        """An invalid run_date raises ValueError."""
        mod = _load_candidates()
        with pytest.raises(ValueError):
            mod.compute_cutoff_date("not-a-date", 30)


# ---------------------------------------------------------------------------
# Group 3: needs parsing — T5 requirement 3
# ---------------------------------------------------------------------------

class TestNeedsParsing:
    """All four needs shapes recognised; none refused; edges derived correctly."""

    def test_list_of_tables_yields_edges(self) -> None:
        """A list of tables each naming a spec path yields dependency edges."""
        mod = _load_candidates()
        needs = [
            {"type": "local", "kind": "spec", "path": "docs/specs/other-spec/spec.md"},
        ]
        result = mod.parse_needs_edges(needs)
        assert result is not None, "List of tables must not be refused"
        assert len(result) == 1
        slug, edge = result[0]
        assert slug == "other-spec"
        assert "docs/specs/other-spec/spec.md" in edge

    def test_bare_string_spec_yields_edge(self) -> None:
        """A bare string 'work:spec/<slug>' yields one dependency edge."""
        mod = _load_candidates()
        result = mod.parse_needs_edges("work:spec/direct-skill-lifecycle")
        assert result is not None, "Bare string must not be refused"
        assert len(result) == 1
        slug, edge = result[0]
        assert slug == "direct-skill-lifecycle"

    def test_empty_list_yields_no_edges(self) -> None:
        """An empty list yields no edges and is not refused."""
        mod = _load_candidates()
        result = mod.parse_needs_edges([])
        assert result is not None, "Empty list must not be refused"
        assert result == []

    def test_absent_key_yields_no_edges(self) -> None:
        """None (key absent) yields no edges and is not refused."""
        mod = _load_candidates()
        result = mod.parse_needs_edges(None)
        assert result is not None, "Absent key (None) must not be refused"
        assert result == []

    def test_table_pointing_outside_docs_specs_yields_no_edge(self) -> None:
        """A needs table pointing outside docs/specs/ yields no edge (not refused).

        Spec § Blocker emission:
        'A fixture entry whose needs table points outside docs/specs/ yields no
        needed-by edge, since it names no spec.'
        """
        mod = _load_candidates()
        needs = [
            {"type": "local", "kind": "brief", "path": "docs/product/briefs/foo.md"},
        ]
        result = mod.parse_needs_edges(needs)
        assert result is not None, (
            "A needs table pointing outside docs/specs/ must not be refused"
        )
        assert result == [], (
            "A needs table pointing outside docs/specs/ must yield no edge"
        )

    def test_unrecognised_needs_shape_returns_none(self) -> None:
        """An unrecognised needs shape (e.g. integer) returns None."""
        mod = _load_candidates()
        result = mod.parse_needs_edges(42)
        assert result is None, "An unrecognised needs shape must return None"

    def test_bare_string_non_spec_kind_yields_no_edge(self) -> None:
        """A bare string with non-spec kind yields no edge (not refused)."""
        mod = _load_candidates()
        result = mod.parse_needs_edges("work:brief/foo-brief")
        assert result is not None, "Bare string with non-spec kind must not be refused"
        assert result == []

    def test_list_with_non_dict_element_returns_none(self) -> None:
        """A list containing a non-dict element returns None (unrecognised)."""
        mod = _load_candidates()
        result = mod.parse_needs_edges(["docs/specs/foo/spec.md"])
        assert result is None, (
            "A list with a non-dict element must return None (unrecognised shape)"
        )


# ---------------------------------------------------------------------------
# Group 4: needed-by detection — T5 requirements 2, 4
# ---------------------------------------------------------------------------

class TestNeededByDetection:
    """needed-by fires on workspace needs edges; clearability verified."""

    def _make_workspace_with_needs(
        self, target_slug: str, dependent_slugs: list[str]
    ) -> dict:
        """Build a workspace dict where each dependent_slug needs target_slug."""
        return {
            "ini-001": {
                "work": {
                    "active": [
                        {
                            "path": f"docs/specs/{dep}/spec.md",
                            "needs": [
                                {
                                    "type": "local",
                                    "kind": "spec",
                                    "path": f"docs/specs/{target_slug}/spec.md",
                                }
                            ],
                        }
                        for dep in dependent_slugs
                    ],
                    "shipped": [
                        {"path": f"docs/specs/{target_slug}/spec.md", "needs": []},
                    ],
                },
            },
        }

    def test_single_dependent_creates_needed_by(self) -> None:
        """A spec that one workspace entry needs carries needed-by."""
        mod = _load_candidates()
        workspace = self._make_workspace_with_needs("target-spec", ["dep-a"])
        needed_by_map, _ = mod.build_needed_by_index(workspace)
        declaring = mod.detect_needed_by("target-spec", needed_by_map)
        assert len(declaring) == 1, (
            f"Expected 1 declaring entry, got {declaring!r}"
        )
        assert "target-spec" in declaring[0], (
            "Declaring entry must name the needs edge to remove"
        )

    def test_two_dependents_list_both(self) -> None:
        """A candidate with two dependents lists both declaring entries.

        Spec § Blocker emission:
        'A needed-by blocker names every entry declaring the dependency and,
        for each, the needs edge a maintainer removes to clear it.'
        """
        mod = _load_candidates()
        workspace = self._make_workspace_with_needs(
            "target-spec", ["dep-a", "dep-b"]
        )
        needed_by_map, _ = mod.build_needed_by_index(workspace)
        declaring = mod.detect_needed_by("target-spec", needed_by_map)
        assert len(declaring) == 2, (
            f"Expected 2 declaring entries, got {declaring!r}"
        )

    def test_both_declaring_entries_carry_the_edge(self) -> None:
        """Each declaring entry carries the needs edge a maintainer removes."""
        mod = _load_candidates()
        workspace = self._make_workspace_with_needs(
            "target-spec", ["dep-a", "dep-b"]
        )
        needed_by_map, _ = mod.build_needed_by_index(workspace)
        declaring = mod.detect_needed_by("target-spec", needed_by_map)
        for entry in declaring:
            assert "docs/specs/target-spec/spec.md" in entry, (
                f"Declaring entry must name the needs edge to remove: {entry!r}"
            )

    def test_removing_both_edges_clears_blocker(self) -> None:
        """Removing all declaring edges leaves the spec no longer needed-by.

        Spec § Blocker emission:
        'A spec whose declaring edges have all been removed is no longer
        reported needed-by.'
        """
        mod = _load_candidates()
        # Workspace with no needs edges for target-spec
        workspace = {
            "ini-001": {
                "work": {
                    "active": [
                        {"path": "docs/specs/dep-a/spec.md", "needs": []},
                    ],
                    "shipped": [
                        {"path": "docs/specs/target-spec/spec.md", "needs": []},
                    ],
                },
            },
        }
        needed_by_map, _ = mod.build_needed_by_index(workspace)
        declaring = mod.detect_needed_by("target-spec", needed_by_map)
        assert declaring == [], (
            "No needs edges → needed-by must be empty (blocker cleared)"
        )

    def test_removing_only_one_of_two_does_not_clear(self) -> None:
        """Removing only one of two declaring edges does not clear the blocker.

        Spec § Blocker emission:
        'removing only one of two does not.'
        """
        mod = _load_candidates()
        # Two dependents, but only one remains
        workspace = {
            "ini-001": {
                "work": {
                    "active": [
                        {
                            "path": "docs/specs/dep-b/spec.md",
                            "needs": [
                                {
                                    "type": "local",
                                    "kind": "spec",
                                    "path": "docs/specs/target-spec/spec.md",
                                }
                            ],
                        },
                    ],
                    "shipped": [
                        {"path": "docs/specs/target-spec/spec.md", "needs": []},
                    ],
                },
            },
        }
        needed_by_map, _ = mod.build_needed_by_index(workspace)
        declaring = mod.detect_needed_by("target-spec", needed_by_map)
        assert len(declaring) == 1, (
            "One remaining edge must still fire the needed-by blocker"
        )

    def test_bare_string_needs_yields_edge(self) -> None:
        """A bare string needs value yields a dependency edge."""
        mod = _load_candidates()
        workspace = {
            "ini-001": {
                "work": {
                    "active": [
                        {
                            "path": "docs/specs/dep-a/spec.md",
                            "needs": "work:spec/target-spec",
                        },
                    ],
                    "shipped": [
                        {"path": "docs/specs/target-spec/spec.md", "needs": []},
                    ],
                },
            },
        }
        needed_by_map, _ = mod.build_needed_by_index(workspace)
        declaring = mod.detect_needed_by("target-spec", needed_by_map)
        assert len(declaring) == 1, (
            f"Bare string needs must yield one declaring entry, got {declaring!r}"
        )

    def test_no_needs_key_yields_no_edges(self) -> None:
        """An entry with no needs key yields no dependency edges."""
        mod = _load_candidates()
        workspace = {
            "ini-001": {
                "work": {
                    "active": [
                        {
                            "path": "docs/specs/dep-a/spec.md",
                            # no 'needs' key at all
                        },
                    ],
                },
            },
        }
        needed_by_map, _ = mod.build_needed_by_index(workspace)
        declaring = mod.detect_needed_by("target-spec", needed_by_map)
        assert declaring == [], (
            "Entry with no needs key must yield no edges for any target"
        )


# ---------------------------------------------------------------------------
# Group 5: Collection classification + inflight — T5 requirement 9
# ---------------------------------------------------------------------------

class TestCollectionClassification:
    """Collection names classify as terminal, non-terminal, or unrecognised."""

    def test_work_shipped_is_terminal(self) -> None:
        """work.shipped is a terminal collection."""
        mod = _load_candidates()
        assert mod.classify_collection("work.shipped") == "terminal"

    def test_initiative_scoped_work_shipped_is_terminal(self) -> None:
        """ini-002.work.shipped is terminal (initiative prefix stripped)."""
        mod = _load_candidates()
        assert mod.classify_collection("ini-002.work.shipped") == "terminal"

    def test_work_queue_is_non_terminal(self) -> None:
        """work.queue is non-terminal (inflight)."""
        mod = _load_candidates()
        assert mod.classify_collection("work.queue") == "non-terminal"

    def test_work_active_is_non_terminal(self) -> None:
        """work.active is non-terminal."""
        mod = _load_candidates()
        assert mod.classify_collection("work.active") == "non-terminal"

    def test_backlog_open_is_non_terminal(self) -> None:
        """backlog.open is non-terminal."""
        mod = _load_candidates()
        assert mod.classify_collection("backlog.open") == "non-terminal"

    def test_unknown_collection_is_unrecognised(self) -> None:
        """An unknown collection name is 'unrecognised' — must not be defaulted.

        Spec § Blocker emission:
        'A collection name the run cannot classify as terminal or non-terminal
        is refused as collection-unrecognised rather than defaulted to either.'
        """
        mod = _load_candidates()
        assert mod.classify_collection("custom.something") == "unrecognised", (
            "An unrecognised collection name must not be defaulted to terminal or non-terminal"
        )

    def test_initiative_unknown_suffix_is_unrecognised(self) -> None:
        """ini-001.custom.whatever is unrecognised (suffix not known)."""
        mod = _load_candidates()
        assert mod.classify_collection("ini-001.custom.whatever") == "unrecognised"


class TestInflightDetection:
    """detect_inflight returns True when spec is in a non-terminal collection."""

    def test_spec_in_work_active_is_inflight(self) -> None:
        """A spec in work.active is inflight."""
        mod = _load_candidates()
        # build_inflight_index walks workspace.toml data
        workspace = {
            "ini-001": {
                "work": {
                    "active": [
                        {"path": "docs/specs/target-spec/spec.md", "needs": []},
                    ],
                },
            },
        }
        slug_collections, _ = mod.build_inflight_index(workspace)
        assert mod.detect_inflight("target-spec", slug_collections) is True

    def test_spec_in_work_shipped_is_not_inflight(self) -> None:
        """A spec in work.shipped is terminal and therefore not inflight."""
        mod = _load_candidates()
        workspace = {
            "ini-001": {
                "work": {
                    "shipped": [
                        {"path": "docs/specs/target-spec/spec.md", "needs": []},
                    ],
                },
            },
        }
        slug_collections, _ = mod.build_inflight_index(workspace)
        assert mod.detect_inflight("target-spec", slug_collections) is False

    def test_spec_not_in_workspace_is_not_inflight(self) -> None:
        """A spec not in workspace.toml at all is not inflight."""
        mod = _load_candidates()
        slug_collections, _ = mod.build_inflight_index({})
        assert mod.detect_inflight("target-spec", slug_collections) is False

    def test_entry_with_file_inside_spec_dir_does_not_make_inflight(self) -> None:
        """An entry whose path names a file inside a spec directory does not
        make that spec inflight.

        Spec § Blocker emission:
        'An entry whose path names a file inside a spec directory rather than
        the spec itself does not make that spec inflight.'
        """
        mod = _load_candidates()
        workspace = {
            "backlog": {
                "open": [
                    # path names a notes file inside the spec dir, not spec.md
                    {"path": "docs/specs/target-spec/notes/foo.md"},
                ],
            },
        }
        slug_collections, _ = mod.build_inflight_index(workspace)
        assert mod.detect_inflight("target-spec", slug_collections) is False, (
            "A path to a file inside the spec dir (not spec.md) must not make that spec inflight"
        )


# ---------------------------------------------------------------------------
# Group 6: inbound-cited detection — T5 requirement 5
# ---------------------------------------------------------------------------

class TestInboundCitedDetection:
    """inbound-cited fires on literal references from governance surfaces."""

    def test_governance_citation_fires_blocker(self) -> None:
        """A spec cited from docs/rfc/ carries inbound-cited naming that surface.

        Spec § Blocker emission:
        'A candidate cited from a governance surface carries inbound-cited
        naming that surface.'
        """
        mod = _load_candidates()
        scanned = [
            ("docs/rfc/0001-foo.md", "See docs/specs/target-spec for details."),
        ]
        surfaces = mod.detect_inbound_cited("target-spec", scanned)
        assert len(surfaces) > 0, "A governance citation must fire inbound-cited"
        assert any("rfc" in s for s in surfaces), (
            f"Surface label must name docs/rfc, got {surfaces!r}"
        )

    def test_no_citation_no_blocker(self) -> None:
        """A spec not cited from any surface carries no inbound-cited blocker."""
        mod = _load_candidates()
        scanned = [
            ("docs/rfc/0001-foo.md", "No reference to the target spec here."),
        ]
        surfaces = mod.detect_inbound_cited("target-spec", scanned)
        assert surfaces == []

    def test_self_reference_not_counted(self) -> None:
        """A citation inside the spec's own directory is not counted."""
        mod = _load_candidates()
        scanned = [
            (
                "docs/specs/target-spec/plan.md",
                "See docs/specs/target-spec/spec.md",
            ),
        ]
        surfaces = mod.detect_inbound_cited("target-spec", scanned)
        assert surfaces == [], "Self-references must not be counted as inbound citations"

    def test_prefix_discrimination(self) -> None:
        """A spec whose slug is a strict prefix of another slug is not cited by
        the longer slug's citations alone.

        Spec § Blocker emission:
        'A spec whose slug is a strict prefix of another spec's slug is not
        reported inbound-cited on the longer slug's citations alone.'
        """
        mod = _load_candidates()
        # "foo" is a prefix of "foo-extended"
        scanned = [
            (
                "docs/rfc/0001.md",
                "See docs/specs/foo-extended for details.",
            ),
        ]
        surfaces = mod.detect_inbound_cited("foo", scanned)
        assert surfaces == [], (
            "A citation of docs/specs/foo-extended must not fire inbound-cited for docs/specs/foo"
        )

    def test_path_with_fragment_is_cited(self) -> None:
        """A link with a fragment (docs/specs/<slug>#section) is recognised."""
        mod = _load_candidates()
        scanned = [
            ("docs/adr/0001.md", "See [section](docs/specs/target-spec#criteria)."),
        ]
        surfaces = mod.detect_inbound_cited("target-spec", scanned)
        assert len(surfaces) > 0, "A citation with a fragment must be recognised"

    def test_path_with_trailing_slash_is_cited(self) -> None:
        """A link ending with a trailing slash is recognised."""
        mod = _load_candidates()
        scanned = [
            ("docs/product/roadmap.md", "docs/specs/target-spec/"),
        ]
        surfaces = mod.detect_inbound_cited("target-spec", scanned)
        assert len(surfaces) > 0, "A citation with a trailing slash must be recognised"


# ---------------------------------------------------------------------------
# Group 7: shipped-brief-member detection
# ---------------------------------------------------------------------------

class TestShippedBriefMemberDetection:
    """shipped-brief-member fires when spec is in a shipped brief's Spec map."""

    def _shipped_brief_body(self, slugs: list[str]) -> str:
        """Build a brief body with Status Shipped and the given slugs in Spec map."""
        rows = "\n".join(f"| {s} | Shipped |" for s in slugs)
        return (
            "- **Status:** Shipped\n\n"
            "## Spec map\n\n"
            "| Spec | Status |\n"
            "| --- | --- |\n"
            f"{rows}\n\n"
            "## Provenance\n"
        )

    def test_spec_in_shipped_brief_fires_blocker(self) -> None:
        """A spec in a Shipped brief's Spec map carries shipped-brief-member."""
        mod = _load_candidates()
        entries = [
            ("docs/product/briefs/my-brief.md", self._shipped_brief_body(["target-spec"])),
        ]
        briefs = mod.detect_shipped_brief_member("target-spec", entries)
        assert len(briefs) == 1
        assert "my-brief.md" in briefs[0]

    def test_spec_not_in_brief_no_blocker(self) -> None:
        """A spec not in any brief's Spec map carries no shipped-brief-member."""
        mod = _load_candidates()
        entries = [
            ("docs/product/briefs/my-brief.md", self._shipped_brief_body(["other-spec"])),
        ]
        briefs = mod.detect_shipped_brief_member("target-spec", entries)
        assert briefs == []

    def test_spec_in_brief_names_the_brief(self) -> None:
        """The shipped-brief-member blocker names the brief that holds the spec."""
        mod = _load_candidates()
        entries = [
            ("docs/product/briefs/alpha.md", self._shipped_brief_body(["target-spec"])),
            ("docs/product/briefs/beta.md", self._shipped_brief_body(["other-spec"])),
        ]
        briefs = mod.detect_shipped_brief_member("target-spec", entries)
        assert len(briefs) == 1
        assert "alpha.md" in briefs[0]


# ---------------------------------------------------------------------------
# Group 8: protected + xspec-pinned detection
# ---------------------------------------------------------------------------

class TestProtectedDetection:
    """protected fires when the slug is in the manifest."""

    def test_slug_in_manifest_fires_blocker(self) -> None:
        """A slug in the protected manifest carries protected."""
        mod = _load_candidates()
        assert mod.detect_protected("target-spec", frozenset({"target-spec"})) is True

    def test_slug_absent_no_blocker(self) -> None:
        """A slug absent from the manifest carries no protected blocker."""
        mod = _load_candidates()
        assert mod.detect_protected("target-spec", frozenset({"other-spec"})) is False

    def test_extract_protected_slugs_from_manifest(self) -> None:
        """extract_protected_slugs extracts the slug from each path entry."""
        mod = _load_candidates()
        manifest = {"protected": ["docs/specs/alpha", "docs/specs/beta"]}
        slugs = mod.extract_protected_slugs(manifest)
        assert "alpha" in slugs
        assert "beta" in slugs


class TestXspecPinnedDetection:
    """xspec-pinned fires when the slug is named by x-spec in any contract."""

    def test_slug_in_xspec_fires_blocker(self) -> None:
        """A slug named by x-spec carries xspec-pinned."""
        mod = _load_candidates()
        assert mod.detect_xspec_pinned("target-spec", frozenset({"target-spec"})) is True

    def test_slug_absent_no_blocker(self) -> None:
        """A slug not named by any x-spec carries no xspec-pinned blocker."""
        mod = _load_candidates()
        assert mod.detect_xspec_pinned("target-spec", frozenset({"other-spec"})) is False

    def test_extract_xspec_slugs_from_schema(self) -> None:
        """extract_xspec_slugs extracts slugs from x-spec keys in JSON."""
        mod = _load_candidates()
        schema = {"x-spec": ["docs/specs/target-spec/"]}
        slugs = mod.extract_xspec_slugs(schema)
        assert "target-spec" in slugs

    def test_extract_xspec_slugs_list_value(self) -> None:
        """x-spec as a list of strings yields all contained slugs."""
        mod = _load_candidates()
        schema = {"x-spec": ["docs/specs/alpha/", "docs/specs/beta"]}
        slugs = mod.extract_xspec_slugs(schema)
        assert "alpha" in slugs
        assert "beta" in slugs


# ---------------------------------------------------------------------------
# Group 9: recently-changed + history-missing
# ---------------------------------------------------------------------------

class TestRecentlyChanged:
    """recently-changed fires when last_touched >= cutoff_date."""

    def test_recent_change_fires_blocker(self) -> None:
        """A spec changed at or after the cutoff carries recently-changed."""
        mod = _load_candidates()
        # cutoff = 2026-08-26; last_touched = 2026-09-01 (newer)
        assert mod.detect_recently_changed("2026-09-01", "2026-08-26") is True

    def test_change_on_cutoff_fires_blocker(self) -> None:
        """A spec changed exactly on the cutoff is still recently-changed."""
        mod = _load_candidates()
        assert mod.detect_recently_changed("2026-08-26", "2026-08-26") is True

    def test_old_change_no_blocker(self) -> None:
        """A spec changed before the cutoff carries no recently-changed blocker."""
        mod = _load_candidates()
        assert mod.detect_recently_changed("2026-08-01", "2026-08-26") is False


class TestHistoryMissing:
    """history-missing fires when last_touched is None."""

    def test_none_fires_blocker(self) -> None:
        """None last_touched fires history-missing."""
        mod = _load_candidates()
        assert mod.detect_history_missing(None) is True

    def test_resolved_date_no_blocker(self) -> None:
        """A resolved last_touched date does not fire history-missing."""
        mod = _load_candidates()
        assert mod.detect_history_missing("2026-09-01") is False


# ---------------------------------------------------------------------------
# Group 10: lasting-facts-unsettled
# ---------------------------------------------------------------------------

class TestLastingFactsUnsettled:
    """lasting-facts-unsettled fires when a notes file is uncited from outside."""

    def test_uncited_notes_file_fires_blocker(self) -> None:
        """A notes file not cited from outside the spec directory fires the blocker."""
        mod = _load_candidates()
        notes_files = ["docs/specs/target-spec/notes/findings.md"]
        # Scanned corpus does not cite the notes file
        scanned = [
            ("docs/rfc/0001.md", "Some text with no notes reference."),
        ]
        result = mod.detect_lasting_facts_unsettled(
            notes_files, scanned, "target-spec"
        )
        assert result is True

    def test_cited_notes_file_no_blocker(self) -> None:
        """A notes file cited from outside its directory does not fire the blocker."""
        mod = _load_candidates()
        notes_files = ["docs/specs/target-spec/notes/findings.md"]
        # Scanned corpus DOES cite the notes file
        scanned = [
            (
                "docs/rfc/0001.md",
                "See docs/specs/target-spec/notes/findings.md for details.",
            ),
        ]
        result = mod.detect_lasting_facts_unsettled(
            notes_files, scanned, "target-spec"
        )
        assert result is False

    def test_no_notes_files_no_blocker(self) -> None:
        """A spec with no notes files carries no lasting-facts-unsettled blocker."""
        mod = _load_candidates()
        result = mod.detect_lasting_facts_unsettled([], [], "target-spec")
        assert result is False

    def test_self_citation_does_not_count(self) -> None:
        """A citation from within the spec's own directory does not satisfy the requirement."""
        mod = _load_candidates()
        notes_files = ["docs/specs/target-spec/notes/findings.md"]
        # Only the spec's own files cite the notes file
        scanned = [
            (
                "docs/specs/target-spec/plan.md",
                "See docs/specs/target-spec/notes/findings.md",
            ),
        ]
        result = mod.detect_lasting_facts_unsettled(
            notes_files, scanned, "target-spec"
        )
        assert result is True, (
            "A citation from within the spec's own directory must not satisfy the citation requirement"
        )


# ---------------------------------------------------------------------------
# Group 11: references-unresolved
# ---------------------------------------------------------------------------

class TestReferencesUnresolved:
    """references-unresolved fires when a spec names a path that does not resolve."""

    def test_broken_link_fires_blocker(self) -> None:
        """A spec with a markdown link to a non-existent path is references-unresolved."""
        mod = _load_candidates()
        body = "See [contract](docs/specs/nonexistent/spec.md) for details."
        existing = frozenset({"docs/specs/target-spec/spec.md"})
        unresolved = mod.detect_references_unresolved("target-spec", body, existing)
        assert len(unresolved) > 0, "A broken link must fire references-unresolved"

    def test_valid_link_no_blocker(self) -> None:
        """A spec with valid links carries no references-unresolved blocker."""
        mod = _load_candidates()
        body = "See [plan](docs/specs/other-spec/spec.md) for details."
        existing = frozenset({"docs/specs/target-spec/spec.md", "docs/specs/other-spec/spec.md"})
        unresolved = mod.detect_references_unresolved("target-spec", body, existing)
        assert unresolved == []

    def test_url_not_checked(self) -> None:
        """HTTP URLs are not checked for resolution."""
        mod = _load_candidates()
        body = "See [external](https://example.com/foo) for details."
        existing: frozenset[str] = frozenset()
        unresolved = mod.detect_references_unresolved("target-spec", body, existing)
        assert unresolved == []

    def test_relative_parent_path_resolved(self) -> None:
        """A ../ relative path is resolved relative to the spec's directory."""
        mod = _load_candidates()
        # spec is at docs/specs/target-spec/spec.md
        # link is ../other-spec which resolves to docs/specs/other-spec
        body = "See [other](../other-spec/spec.md) for details."
        existing = frozenset({"docs/specs/other-spec/spec.md"})
        unresolved = mod.detect_references_unresolved("target-spec", body, existing)
        assert unresolved == [], (
            "A ../ link resolving to an existing path must not fire references-unresolved"
        )


# ---------------------------------------------------------------------------
# Group 12: Free candidate is eligible — T5 requirement 6
# ---------------------------------------------------------------------------

class TestFreeCandidate:
    """A candidate free of every blocker condition is reported eligible."""

    def test_clean_candidate_is_eligible(self) -> None:
        """A candidate with no blockers has an empty blocker list.

        Spec § Blocker emission:
        'A candidate free of every condition named below, suppressed by no
        refusal, is reported eligible with an empty blocker list.'
        """
        mod = _load_candidates()
        # All detection functions return "no blocker" for the clean inputs
        assert mod.detect_status_not_terminal("Shipped") is False
        assert mod.detect_protected("target-spec", frozenset()) is False
        assert mod.detect_xspec_pinned("target-spec", frozenset()) is False
        assert mod.detect_history_missing("2020-01-01") is False
        assert mod.detect_recently_changed("2020-01-01", "2026-08-26") is False

        # needs: no dependents
        workspace = {"ini-001": {"work": {"shipped": [
            {"path": "docs/specs/target-spec/spec.md", "needs": []}
        ]}}}
        needed_by_map, _ = mod.build_needed_by_index(workspace)
        assert mod.detect_needed_by("target-spec", needed_by_map) == []

        # inflight: in work.shipped
        slug_collections, _ = mod.build_inflight_index(workspace)
        assert mod.detect_inflight("target-spec", slug_collections) is False

        # inbound: no citations
        assert mod.detect_inbound_cited("target-spec", []) == []

        # brief: not in any shipped brief
        assert mod.detect_shipped_brief_member("target-spec", []) == []

        # notes: no notes files
        assert mod.detect_lasting_facts_unsettled([], [], "target-spec") is False

        # references: no links
        assert mod.detect_references_unresolved("target-spec", "", frozenset()) == []


# ---------------------------------------------------------------------------
# Group 13: Sole-reason fixture for every blocker code — T5 requirement 1
# ---------------------------------------------------------------------------

class TestSoleReasonFixtures:
    """Every blocker code in BLOCKER_CODES has a sole-reason fixture.

    'One fixture candidate per blocker code, enumerated from the module's
    BLOCKER_CODES constant, each asserting that its code appears and that
    the candidate is not eligible. A code added to the enum without a fixture
    fails the case rather than being silently uncovered.'
    """

    def _all_clean(self, mod) -> dict:
        """Return a dict of all detection inputs that produce no blocker."""
        return {
            "status_token": "Shipped",
            "protected_slugs": frozenset(),
            "xspec_slugs": frozenset(),
            "last_touched": "2020-01-01",
            "cutoff_date": "2026-08-26",
            "workspace_data": {
                "ini-001": {
                    "work": {
                        "shipped": [
                            {"path": "docs/specs/target-spec/spec.md", "needs": []},
                        ],
                    },
                },
            },
            "scanned_files": [],  # no inbound citations
            "shipped_briefs": [],  # not in any shipped brief
            "notes_files": [],  # no notes files
            "existing_paths": frozenset({"docs/specs/target-spec/spec.md"}),
            "spec_body": "# Spec\n- **Status:** Shipped\n",
        }

    def _run_detectors(self, mod, inputs: dict) -> list[str]:
        """Run all detectors and return list of blocker codes that fired."""
        blockers: list[str] = []
        if mod.detect_status_not_terminal(inputs["status_token"]):
            blockers.append("status-not-terminal")
        if mod.detect_protected("target-spec", inputs["protected_slugs"]):
            blockers.append("protected")
        if mod.detect_xspec_pinned("target-spec", inputs["xspec_slugs"]):
            blockers.append("xspec-pinned")
        if mod.detect_history_missing(inputs["last_touched"]):
            blockers.append("history-missing")
        elif mod.detect_recently_changed(inputs["last_touched"], inputs["cutoff_date"]):
            blockers.append("recently-changed")

        needed_by_map, _ = mod.build_needed_by_index(inputs["workspace_data"])
        if mod.detect_needed_by("target-spec", needed_by_map):
            blockers.append("needed-by")

        slug_collections, _ = mod.build_inflight_index(inputs["workspace_data"])
        if mod.detect_inflight("target-spec", slug_collections):
            blockers.append("inflight")

        if mod.detect_inbound_cited("target-spec", inputs["scanned_files"]):
            blockers.append("inbound-cited")
        if mod.detect_shipped_brief_member("target-spec", inputs["shipped_briefs"]):
            blockers.append("shipped-brief-member")
        if mod.detect_lasting_facts_unsettled(
            inputs["notes_files"], inputs["scanned_files"], "target-spec"
        ):
            blockers.append("lasting-facts-unsettled")
        if mod.detect_references_unresolved(
            "target-spec", inputs["spec_body"], inputs["existing_paths"]
        ):
            blockers.append("references-unresolved")
        return blockers

    def _make_sole_reason_fixture(self, mod, code: str) -> dict:
        """Build a fixture where exactly *code* fires."""
        inputs = self._all_clean(mod)
        if code == "evidence-unread":
            # evidence-unread is set by apply_refusals (T0c), not a detector here.
            # Return a marker so the test below handles it separately.
            inputs["_evidence_unread_only"] = True
            return inputs
        if code == "status-not-terminal":
            inputs["status_token"] = "Implementing"
        elif code == "protected":
            inputs["protected_slugs"] = frozenset({"target-spec"})
        elif code == "xspec-pinned":
            inputs["xspec_slugs"] = frozenset({"target-spec"})
        elif code == "history-missing":
            inputs["last_touched"] = None
        elif code == "recently-changed":
            # last_touched is after the cutoff
            inputs["last_touched"] = "2026-09-25"  # after 2026-08-26
        elif code == "needed-by":
            inputs["workspace_data"] = {
                "ini-001": {
                    "work": {
                        "active": [
                            {
                                "path": "docs/specs/dep-a/spec.md",
                                "needs": [
                                    {
                                        "type": "local",
                                        "kind": "spec",
                                        "path": "docs/specs/target-spec/spec.md",
                                    }
                                ],
                            }
                        ],
                        "shipped": [
                            {"path": "docs/specs/target-spec/spec.md", "needs": []},
                        ],
                    }
                }
            }
        elif code == "inflight":
            inputs["workspace_data"] = {
                "ini-001": {
                    "work": {
                        "active": [
                            {"path": "docs/specs/target-spec/spec.md", "needs": []},
                        ],
                    }
                }
            }
        elif code == "inbound-cited":
            inputs["scanned_files"] = [
                ("docs/rfc/0001.md", "See docs/specs/target-spec for details."),
            ]
        elif code == "shipped-brief-member":
            inputs["shipped_briefs"] = [
                (
                    "docs/product/briefs/my-brief.md",
                    (
                        "- **Status:** Shipped\n\n"
                        "## Spec map\n\n"
                        "| Spec | Status |\n"
                        "| --- | --- |\n"
                        "| target-spec | Shipped |\n\n"
                        "## Provenance\n"
                    ),
                ),
            ]
        elif code == "lasting-facts-unsettled":
            inputs["notes_files"] = ["docs/specs/target-spec/notes/findings.md"]
            # scanned_files already empty, so no citation from outside
        elif code == "references-unresolved":
            inputs["spec_body"] = (
                "# Spec\n"
                "- **Status:** Shipped\n"
                "See [missing](docs/specs/nonexistent/spec.md) for details.\n"
            )
        return inputs

    @pytest.mark.parametrize(
        "code",
        sorted(_load_candidates().BLOCKER_CODES),
    )
    def test_sole_reason_fixture(self, code: str) -> None:
        """Every blocker code has a fixture where it is the sole reason."""
        mod = _load_candidates()
        inputs = self._make_sole_reason_fixture(mod, code)

        if inputs.get("_evidence_unread_only"):
            # evidence-unread: apply a refusal to a clean candidate
            retirement_mod = _load_retirement()
            candidate = {"eligible": True, "blockers": []}
            candidates = {"target-spec": candidate}
            refusal = retirement_mod.Refusal(
                code="input-unreadable",
                path="workspace.toml",
                suppresses=["target-spec"],
            )
            retirement_mod.apply_refusals(candidates, [refusal])
            assert candidate["eligible"] is False, (
                "Candidate must not be eligible after evidence-unread"
            )
            assert "evidence-unread" in candidate["blockers"], (
                "evidence-unread must appear in blockers"
            )
            return

        # Run all detectors on the fixture
        fired = self._run_detectors(mod, inputs)

        assert code in fired, (
            f"Blocker code '{code}' must fire on its sole-reason fixture. "
            f"Fired codes: {fired!r}"
        )
        assert fired == [code], (
            f"Only '{code}' must fire on its sole-reason fixture, "
            f"but these also fired: {sorted(set(fired) - {code})!r}"
        )

    def test_blocker_codes_constant_is_nonempty(self) -> None:
        """BLOCKER_CODES is non-empty (guards against an accidental clear)."""
        mod = _load_candidates()
        assert len(mod.BLOCKER_CODES) > 0

    def test_evidence_unread_not_in_detector_suite(self) -> None:
        """evidence-unread is in BLOCKER_CODES but set by apply_refusals, not detectors.

        A clean candidate with no refusals applied has no evidence-unread blocker.
        """
        mod = _load_candidates()
        inputs = self._all_clean(mod)
        fired = self._run_detectors(mod, inputs)
        assert "evidence-unread" not in fired, (
            "evidence-unread must not fire from the pure detector suite; "
            "it is set by apply_refusals when a corpus cannot be read."
        )
