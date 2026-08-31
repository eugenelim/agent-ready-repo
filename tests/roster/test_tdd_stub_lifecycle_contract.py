"""Contract tests for the TDD stub lifecycle across shipped guidance.

Roster-owned rather than pack-owned: the lifecycle spans `packs/core/`,
`docs/`, `guides/`, `tools/`, and `docs-site/`, so a pack-local home would
reach above its own pack. CI does not auto-discover roster tests, so this
module is wired explicitly in `.github/workflows/build-check.yml`.
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NEW_SPEC = ROOT / "packs/core/.apm/skills/new-spec/SKILL.md"
WORK_LOOP = ROOT / "packs/core/.apm/skills/work-loop/SKILL.md"
TDD_STUBS = ROOT / "packs/core/.apm/skills/work-loop/references/tdd-stubs.md"
CONVENTIONS = ROOT / "packs/core/seeds/docs/CONVENTIONS.md"
RFC_0028 = ROOT / "docs/rfc/0028-tdd-stub-generation-in-the-core-loop.md"
RFC_INDEX = ROOT / "docs/rfc/README.md"
RFC_0028_ACCEPTED_BODY_SHA256 = "dee31e8a9d9ed998fae31d2c2783475613e5689bbe94895b992f632a8eaa8b47"
ARCHITECTURE = ROOT / "docs/architecture/loop-infrastructure.md"
HOW_TO = ROOT / "guides/core/how-to/plan-and-execute-non-trivial-work.md"
EXPLANATION = ROOT / "guides/core/explanation/core-pack.md"
NEW_SPEC_EVALS = ROOT / "packs/core/.apm/skills/new-spec/evals/evals.json"
WORK_LOOP_EVALS = ROOT / "packs/core/.apm/skills/work-loop/evals/evals.json"
LIVE_PLAN_TIME_SOURCES = (
    ROOT / "tools/test_check_docs_contrast.py",
    ROOT / "tools/test_editable_install_guard.py",
    ROOT / "tools/test-build-check-workflow.py",
    ROOT / "tools/test-pages-workflow.py",
    ROOT / "docs-site/src/plugins/rehype-scrollable-tables.test.ts",
)


def _text(path: Path) -> str:
    """Return one lifecycle contract source as UTF-8 text."""

    return path.read_text(encoding="utf-8")


def _assert_order(text: str, *needles: str) -> None:
    """Assert that each lifecycle phrase appears after the preceding phrase."""

    positions = [text.index(needle) for needle in needles]
    assert positions == sorted(positions)


def _eval_record(path: Path, record_id: str) -> dict[str, object]:
    """Return one named eval record from a shipped skill harness."""

    records = json.loads(_text(path))["evals"]
    return next(record for record in records if record["id"] == record_id)


def test_spec_authoring_and_plan_do_not_write_repository_tests() -> None:
    """PLAN proves a stub from the plan without mutating repository tests."""

    # STUB: AC1, AC2
    new_spec = _text(NEW_SPEC)
    work_loop = _text(WORK_LOOP)
    assert "pointer/self-check only" in new_spec
    assert "work-loop PLAN owns exact stub authoring" in new_spec
    assert "work-loop PLAN owns disposable red validation" in new_spec
    assert "exact stub code" in new_spec
    assert "disposable scratch" in new_spec
    assert "do not create a repository test file" in new_spec
    forbidden_plan_time_permissions = (
        "materialize a compilable red stub when a durable plan requires one",
        "materialised *at PLAN* as a compilable",
        "one stub **file per plan task**",
        "red stub written now",
        "usually the red test is then already written",
        "red stub materialised at PLAN per CONVENTIONS",
        "materialised at PLAN per CONVENTIONS",
    )
    live_sources = (new_spec, work_loop, _text(TDD_STUBS), _text(CONVENTIONS))
    live_sources += tuple(_text(path) for path in LIVE_PLAN_TIME_SOURCES)
    for source in live_sources:
        normalized_source = source.lower()
        for forbidden in forbidden_plan_time_permissions:
            assert forbidden.lower() not in normalized_source
    _assert_order(
        work_loop,
        "exact stub code in `plan.md`",
        "disposable scratch",
        "CODE-IMPLEMENTATION",
        "materialize the approved stub",
    )


def test_tdd_reference_owns_both_lifecycle_branches_and_exceptions() -> None:
    """The detailed procedure separates proof, terminal planning, and execution."""

    # STUB: AC3, AC4, AC5
    reference = _text(TDD_STUBS)
    _assert_order(
        reference,
        "PLAN stores",
        "spec-plan",
        "CODE-IMPLEMENTATION",
        "intended red",
        "green",
    )
    assert "no stub (mode)" in reference
    assert "no stub (implementation-discovered)" in reference
    assert "discovery predicate" in reference
    assert "proof obligation" in reference
    assert "spec-plan writes no repository test file" in reference
    assert "denies network access" in reference
    assert "applies a timeout" in reference
    assert "block plan approval" in reference
    assert "compile-only diagnostic" in reference
    assert "stub: draft (uncompiled)" not in reference
    assert "does **not**\nblock the plan" not in reference
    assert "exactly one terminal newline" in reference
    assert "blank payload line immediately before" in reference
    assert "Reject it" in reference


def test_convention_architecture_and_guides_share_the_phase_boundary() -> None:
    """Maintainer and adopter surfaces teach the same commit-safe sequence."""

    # STUB: AC6
    convention = _text(CONVENTIONS)
    architecture = _text(ARCHITECTURE)
    how_to = _text(HOW_TO)
    explanation = _text(EXPLANATION)
    for text in (convention, architecture, how_to, explanation):
        assert "disposable scratch" in text
        assert "CODE-IMPLEMENTATION" in text
    assert "spec-plan" in architecture
    assert "no stub (implementation-discovered)" in how_to
    assert "planning proof" in explanation


def test_frozen_rfc_records_the_correction_without_rewriting_history() -> None:
    """RFC-0028's append-only erratum and living index expose current order."""

    # STUB: AC6
    rfc = _text(RFC_0028)
    body, separator, errata = rfc.partition("\n## Errata\n")
    assert separator
    assert hashlib.sha256(body.encode("utf-8")).hexdigest() == RFC_0028_ACCEPTED_BODY_SHA256
    assert "PLAN-contained" in errata
    assert "CODE-IMPLEMENTATION" in errata
    assert "frozen body remains the historical decision" in errata
    index_row = next(
        line for line in _text(RFC_INDEX).splitlines() if line.startswith("| [0028]")
    )
    assert "PLAN-contained" in index_row
    assert "CODE-IMPLEMENTATION" in index_row


def test_skill_evals_cover_plan_proof_and_execute_materialization() -> None:
    """The shipped eval harness rejects the former PLAN-time write ordering."""

    # STUB: AC7
    records = (
        _eval_record(NEW_SPEC_EVALS, "tdd-stub-proof-belongs-to-work-loop-plan"),
        _eval_record(WORK_LOOP_EVALS, "tdd-stub-replaces-prose-or-records-no-stub-reason"),
    )
    for record in records:
        expected = str(record["expected_output"])
        assert "exact stub code" in expected
        assert "`plan.md`" in expected
        assert "disposable scratch" in expected
        assert "no repository test file" in expected
        assert "`CODE-IMPLEMENTATION`" in expected
        assert "materialize the approved stub" in expected
