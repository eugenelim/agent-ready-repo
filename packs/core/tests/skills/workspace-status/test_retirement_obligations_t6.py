"""Tests for obligation payload and age vocabulary — T6 (TDD).

Verification mode: TDD.
Spec:  docs/specs/spec-retirement-eligibility/spec.md  §§ Blocker emission
       (lasting-facts-unsettled obligation clauses), Age reporting
Plan:  docs/specs/spec-retirement-eligibility/plan.md  § T6

T6 requirements verified here
------------------------------
1.  A candidate whose directory holds a notes/ file that no surface outside
    the directory cites carries lasting-facts-unsettled with its RFC-0096 §2
    role named.  The uncited-notes/ condition is the mechanical proxy; the
    role is advisory classification.
2.  A candidate carrying a durable invariant, and one carrying non-inferable
    policy, name their distinct roles.
3.  A candidate whose claims are recoverable elsewhere (notes file cited from
    outside the spec directory) carries no obligation.
4.  A candidate whose last recorded change is newer than the cutoff carries
    recently-changed; one whose change is older does not.
5.  No emitted field is named for a lifecycle record or presents an age as a
    §6 cooling verdict (banned vocabulary: completed_on, review_on, cooling,
    due).
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

_CANDIDATES_MODULE_NAME = "workspace_status_retirement_candidates_t6"

_BANNED_VOCABULARY = frozenset({"completed_on", "review_on", "cooling", "due"})


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


# ---------------------------------------------------------------------------
# Group 1: Obligation payload — T6 requirement 1
# ---------------------------------------------------------------------------

class TestObligationPayload:
    """build_lasting_facts_obligations produces the obligation payload for uncited notes."""

    def test_uncited_notes_file_produces_obligation(self) -> None:
        """An uncited notes file produces an obligation with semantic_role and source_path.

        Spec § Blocker emission:
        'A candidate reported lasting-facts-unsettled carries an obligation
        naming the RFC-0096 §2 semantic role that fact must reach.'
        """
        mod = _load_candidates()
        notes_files = ["docs/specs/target-spec/notes/survey.md"]
        scanned: list[tuple[str, str]] = [
            ("docs/rfc/0001.md", "No citation here."),
        ]
        obligations = mod.build_lasting_facts_obligations(notes_files, scanned, "target-spec")
        assert len(obligations) == 1, (
            "One uncited notes file must produce exactly one obligation"
        )
        obl = obligations[0]
        assert "semantic_role" in obl, "Obligation must carry semantic_role"
        assert "source_path" in obl, "Obligation must carry source_path"
        assert obl["source_path"] == "docs/specs/target-spec/notes/survey.md"
        assert obl["semantic_role"] in mod.SEMANTIC_ROLE_ENUM, (
            f"semantic_role {obl['semantic_role']!r} must be one of the ten RFC-0096 §2 roles"
        )

    def test_destination_emitted_when_role_resolves(self) -> None:
        """When §4's precedence order resolves the role to a location, destination is emitted.

        Spec § Blocker emission:
        'That obligation names a destination where §4's precedence order
        resolves one, and omits the destination where it does not.'

        project-knowledge resolves to docs/knowledge/ in this repository
        per ADR-0081's per-topic model (RFC-0096 §4 and the 2026-09-13 Errata).
        """
        mod = _load_candidates()
        # A notes filename matching the project-knowledge pattern
        notes_files = ["docs/specs/target-spec/notes/knowledge-survey.md"]
        obligations = mod.build_lasting_facts_obligations(notes_files, [], "target-spec")
        assert len(obligations) == 1
        obl = obligations[0]
        if obl["semantic_role"] == "project-knowledge":
            assert "destination" in obl, (
                "project-knowledge resolves to docs/knowledge/ per ADR-0081; "
                "destination must be emitted"
            )
            assert obl["destination"], "destination must be non-empty"

    def test_destination_omitted_when_role_does_not_resolve(self) -> None:
        """When §4 does not resolve the role, destination is omitted, not guessed.

        Spec § Blocker emission:
        '[The obligation] omits the destination where it does not [resolve].'

        Emitting a guessed path would present an unmade decision as a made one.
        """
        mod = _load_candidates()
        # A notes filename suggesting current-product-truth (policy)
        # §4 does not resolve current-product-truth to a single path in this repo
        notes_files = ["docs/specs/target-spec/notes/product-policy.md"]
        obligations = mod.build_lasting_facts_obligations(notes_files, [], "target-spec")
        assert len(obligations) == 1
        obl = obligations[0]
        if obl["semantic_role"] == "current-product-truth":
            assert "destination" not in obl, (
                "current-product-truth has no resolved destination in this repo; "
                "destination must be omitted rather than guessed"
            )

    def test_no_notes_files_no_obligations(self) -> None:
        """A spec with no notes files produces an empty obligations list."""
        mod = _load_candidates()
        obligations = mod.build_lasting_facts_obligations([], [], "target-spec")
        assert obligations == []

    def test_multiple_uncited_notes_produce_multiple_obligations(self) -> None:
        """Multiple uncited notes files each produce an obligation."""
        mod = _load_candidates()
        notes_files = [
            "docs/specs/target-spec/notes/survey.md",
            "docs/specs/target-spec/notes/product-policy.md",
        ]
        obligations = mod.build_lasting_facts_obligations(notes_files, [], "target-spec")
        assert len(obligations) == 2, (
            "Each uncited notes file must produce its own obligation"
        )
        source_paths = {obl["source_path"] for obl in obligations}
        assert source_paths == {
            "docs/specs/target-spec/notes/survey.md",
            "docs/specs/target-spec/notes/product-policy.md",
        }


# ---------------------------------------------------------------------------
# Group 2: Three obligation classes distinguishable — T6 requirement 2, 3
# ---------------------------------------------------------------------------

class TestThreeObligationClasses:
    """Durable invariant, non-inferable policy, and recoverable-elsewhere are distinct.

    Done-when: the three obligation classes are distinguishable from one
    another in the output.
    """

    def test_durable_invariant_names_its_role(self) -> None:
        """A notes file representing a durable invariant names its semantic role.

        Plan § T6:
        'A candidate carrying a durable invariant ... names [its] distinct role.'
        """
        mod = _load_candidates()
        # A filename whose pattern suggests a durable architectural invariant
        notes_files = ["docs/specs/target-spec/notes/architecture-invariant.md"]
        obligations = mod.build_lasting_facts_obligations(notes_files, [], "target-spec")
        assert len(obligations) == 1
        durable_role = obligations[0]["semantic_role"]
        assert durable_role in mod.SEMANTIC_ROLE_ENUM, (
            f"Durable invariant role {durable_role!r} must be in SEMANTIC_ROLE_ENUM"
        )

    def test_non_inferable_policy_names_its_role(self) -> None:
        """A notes file representing non-inferable policy names its semantic role.

        Plan § T6:
        '... and one carrying non-inferable policy, name their distinct roles.'
        """
        mod = _load_candidates()
        notes_files = ["docs/specs/target-spec/notes/product-policy.md"]
        obligations = mod.build_lasting_facts_obligations(notes_files, [], "target-spec")
        assert len(obligations) == 1
        policy_role = obligations[0]["semantic_role"]
        assert policy_role in mod.SEMANTIC_ROLE_ENUM, (
            f"Policy role {policy_role!r} must be in SEMANTIC_ROLE_ENUM"
        )

    def test_durable_and_policy_roles_are_distinct(self) -> None:
        """A durable invariant and a non-inferable policy name different roles.

        Done-when: the three obligation classes are distinguishable from one
        another in the output.
        """
        mod = _load_candidates()
        # Durable invariant
        inv_obligations = mod.build_lasting_facts_obligations(
            ["docs/specs/target-spec/notes/architecture-invariant.md"], [], "target-spec"
        )
        # Non-inferable policy
        pol_obligations = mod.build_lasting_facts_obligations(
            ["docs/specs/target-spec/notes/product-policy.md"], [], "target-spec"
        )
        durable_role = inv_obligations[0]["semantic_role"]
        policy_role = pol_obligations[0]["semantic_role"]
        assert durable_role != policy_role, (
            f"Durable invariant ({durable_role!r}) and non-inferable policy "
            f"({policy_role!r}) must name distinct roles"
        )

    def test_recoverable_elsewhere_no_obligation(self) -> None:
        """A notes file cited from outside the spec directory produces no obligation.

        Spec § Blocker emission:
        'A candidate whose claims are recoverable elsewhere carries no obligation.'

        A cited notes file means the claim is already referenced from outside
        the spec container — the obligation is discharged.

        Done-when: the proxy case fails if the blocker fires on a directory
        whose notes/ file is cited from outside it.
        """
        mod = _load_candidates()
        notes_files = ["docs/specs/target-spec/notes/findings.md"]
        # The notes file IS cited from outside the spec directory
        scanned: list[tuple[str, str]] = [
            ("docs/rfc/0001.md", "See docs/specs/target-spec/notes/findings.md for details."),
        ]
        obligations = mod.build_lasting_facts_obligations(notes_files, scanned, "target-spec")
        assert obligations == [], (
            "A notes file cited from outside its spec directory must produce no obligation; "
            "the claims are recoverable elsewhere."
        )
        # Verify: lasting-facts-unsettled itself should also not fire
        result = mod.detect_lasting_facts_unsettled(notes_files, scanned, "target-spec")
        assert result is False, (
            "lasting-facts-unsettled must not fire when the notes file is cited from outside"
        )

    def test_mixed_cited_and_uncited_notes(self) -> None:
        """Only uncited notes files produce obligations; cited ones carry no obligation."""
        mod = _load_candidates()
        notes_files = [
            "docs/specs/target-spec/notes/survey.md",    # will be uncited
            "docs/specs/target-spec/notes/findings.md",  # will be cited
        ]
        scanned: list[tuple[str, str]] = [
            ("docs/rfc/0001.md", "See docs/specs/target-spec/notes/findings.md for details."),
        ]
        obligations = mod.build_lasting_facts_obligations(notes_files, scanned, "target-spec")
        assert len(obligations) == 1, "Only the uncited file must produce an obligation"
        assert obligations[0]["source_path"] == "docs/specs/target-spec/notes/survey.md", (
            "The obligation must name the uncited file, not the cited one"
        )

    def test_self_citation_does_not_clear_obligation(self) -> None:
        """A citation from inside the spec directory does not clear the obligation."""
        mod = _load_candidates()
        notes_files = ["docs/specs/target-spec/notes/survey.md"]
        # Only self-references — inside docs/specs/target-spec/
        scanned: list[tuple[str, str]] = [
            (
                "docs/specs/target-spec/spec.md",
                "See docs/specs/target-spec/notes/survey.md for the survey.",
            ),
        ]
        obligations = mod.build_lasting_facts_obligations(notes_files, scanned, "target-spec")
        assert len(obligations) == 1, (
            "A self-citation does not clear the obligation; "
            "the notes file must still be considered uncited from outside"
        )


# ---------------------------------------------------------------------------
# Group 3: Age reporting vocabulary — T6 requirement 4, 5
# ---------------------------------------------------------------------------

class TestAgeReportingVocabulary:
    """Age is reported from change history; no §6 cooling vocabulary appears."""

    def test_recently_changed_fires_at_cutoff(self) -> None:
        """A candidate changed exactly on the cutoff carries recently-changed.

        Spec § Blocker emission:
        'A spec whose last recorded change is newer than the emitted cutoff is
        reported recently-changed.'

        A change on the cutoff date is still "at or after" the cutoff.
        """
        mod = _load_candidates()
        # Changed on the cutoff date exactly
        assert mod.detect_recently_changed("2026-08-26", "2026-08-26") is True

    def test_recently_changed_fires_after_cutoff(self) -> None:
        """A candidate changed after the cutoff carries recently-changed."""
        mod = _load_candidates()
        assert mod.detect_recently_changed("2026-09-25", "2026-08-26") is True

    def test_recently_changed_absent_when_older(self) -> None:
        """A candidate changed before the cutoff does not carry recently-changed.

        Plan § T6:
        'A candidate whose last recorded change is newer than the cutoff
        carries recently-changed; one whose change is older does not.'
        """
        mod = _load_candidates()
        assert mod.detect_recently_changed("2020-01-01", "2026-08-26") is False
        # One day before the cutoff
        assert mod.detect_recently_changed("2026-08-25", "2026-08-26") is False

    def test_obligation_keys_contain_no_clock_vocabulary(self) -> None:
        """Obligation dict keys do not contain RFC-0096 §6 clock vocabulary.

        Spec § Age reporting:
        'No field name or enum value in the schema reuses RFC-0096 §6's clock
        vocabulary — completed_on, review_on, cooling, or due.'

        This test verifies the obligation payload produced by this module
        does not introduce any of those names as dict keys.
        """
        mod = _load_candidates()
        notes_files = ["docs/specs/target-spec/notes/knowledge-survey.md"]
        obligations = mod.build_lasting_facts_obligations(notes_files, [], "target-spec")
        assert len(obligations) == 1
        obl = obligations[0]
        for key in obl.keys():
            for banned in _BANNED_VOCABULARY:
                assert banned != key, (
                    f"Obligation key {key!r} reuses §6 clock vocabulary {banned!r}; "
                    "age is from change history, not a cooling verdict."
                )

    def test_semantic_role_enum_contains_no_clock_vocabulary(self) -> None:
        """SEMANTIC_ROLE_ENUM values do not contain RFC-0096 §6 clock vocabulary.

        The ten roles from RFC-0096 §2 are not lifecycle clock concepts; none
        should share vocabulary with §6's cooling fields.
        """
        mod = _load_candidates()
        for role in mod.SEMANTIC_ROLE_ENUM:
            for banned in _BANNED_VOCABULARY:
                assert banned not in role, (
                    f"SEMANTIC_ROLE_ENUM value {role!r} contains banned §6 vocabulary {banned!r}"
                )

    def test_semantic_role_enum_is_ten_roles(self) -> None:
        """SEMANTIC_ROLE_ENUM contains exactly the ten roles RFC-0096 §2 names.

        Spec § Contract and refusals:
        'The schema's semantic-role enum equals the ten roles RFC-0096 §2's
        "Other roles are separate" sentence names.'

        Enumerated from RFC-0096 §2's "Other roles are separate" sentence:
        current product truth, user documentation, product history, release
        history, current architecture, architecture design, decision records,
        operations, interface contracts, and project knowledge.
        """
        mod = _load_candidates()
        EXPECTED_ROLES = frozenset({
            "current-product-truth",
            "user-documentation",
            "product-history",
            "release-history",
            "current-architecture",
            "architecture-design",
            "decision-record",
            "operations",
            "interface-contract",
            "project-knowledge",
        })
        assert mod.SEMANTIC_ROLE_ENUM == EXPECTED_ROLES, (
            f"SEMANTIC_ROLE_ENUM must equal the ten RFC-0096 §2 roles.\n"
            f"Module has: {sorted(mod.SEMANTIC_ROLE_ENUM)!r}.\n"
            f"Expected:   {sorted(EXPECTED_ROLES)!r}."
        )

    def test_classify_notes_obligation_returns_valid_role(self) -> None:
        """classify_notes_obligation returns a role in SEMANTIC_ROLE_ENUM."""
        mod = _load_candidates()
        for filename in [
            "docs/specs/target-spec/notes/survey.md",
            "docs/specs/target-spec/notes/findings.md",
            "docs/specs/target-spec/notes/policy.md",
            "docs/specs/target-spec/notes/verification-ledger.md",
            "docs/specs/target-spec/notes/unknown-type.md",
        ]:
            role, destination = mod.classify_notes_obligation(filename)
            assert role in mod.SEMANTIC_ROLE_ENUM, (
                f"classify_notes_obligation({filename!r}) returned {role!r}, "
                f"which is not in SEMANTIC_ROLE_ENUM"
            )
            if destination is not None:
                assert isinstance(destination, str) and destination, (
                    f"destination must be a non-empty string, got {destination!r}"
                )
