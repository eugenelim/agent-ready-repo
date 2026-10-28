"""Contract tests for where the TDD red test is written, across shipped guidance.

Roster-owned rather than pack-owned: the lifecycle spans `packs/core/`,
`docs/`, `guides/`, `tools/`, and `docs-site/`, so a pack-local home would
reach above its own pack. The red test is written and proven red at EXECUTE;
the plan carries behavior, boundary, and verification mode, not test code.
"""

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NEW_SPEC = ROOT / "packs/core/.apm/skills/new-spec/SKILL.md"
PLAN_TEMPLATE = ROOT / "packs/core/.apm/skills/new-spec/assets/plan.md"
SPEC_TEMPLATE = ROOT / "packs/core/.apm/skills/new-spec/assets/spec.md"
WORK_LOOP = ROOT / "packs/core/.apm/skills/work-loop/SKILL.md"
TDD_STUBS = ROOT / "packs/core/.apm/skills/work-loop/references/tdd-stubs.md"
RFC_0028 = ROOT / "docs/rfc/0028-tdd-stub-generation-in-the-core-loop.md"
RFC_INDEX = ROOT / "docs/rfc/README.md"
RFC_0028_ACCEPTED_BODY_SHA256 = "dee31e8a9d9ed998fae31d2c2783475613e5689bbe94895b992f632a8eaa8b47"
ARCHITECTURE = ROOT / "docs/architecture/loop-infrastructure.md"
ACCEPTANCE_LOOP = ROOT / "docs/architecture/acceptance-centered-work-loop.md"
HOW_TO = ROOT / "guides/core/how-to/plan-and-execute-non-trivial-work.md"
EXPLANATION = ROOT / "guides/core/explanation/core-pack.md"
REFERENCE = ROOT / "guides/core/reference/spec-shape-and-lld.md"
NEW_SPEC_EVALS = ROOT / "packs/core/.apm/skills/new-spec/evals/evals.json"
WORK_LOOP_EVALS = ROOT / "packs/core/.apm/skills/work-loop/evals/evals.json"
LIVE_PLAN_TIME_SOURCES = (
    ROOT / "tools/test_check_docs_contrast.py",
    ROOT / "tools/test_editable_install_guard.py",
    ROOT / "tools/test-build-check-workflow.py",
    ROOT / "tools/test-pages-workflow.py",
    ROOT / "docs-site/src/plugins/rehype-scrollable-tables.test.ts",
)
LIVE_SOURCES = (
    WORK_LOOP,
    TDD_STUBS,
    ROOT / "packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md",
    NEW_SPEC,
    PLAN_TEMPLATE,
    SPEC_TEMPLATE,
    ROOT / "packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md",
    ROOT / "packs/core/.apm/agents/quality-engineer.md",
    HOW_TO,
    EXPLANATION,
    REFERENCE,
    ARCHITECTURE,
    ACCEPTANCE_LOOP,
    # Beyond the spec's thirteen: shipped guidance that names the TDD timing.
    ROOT / "packs/core/.apm/skills/work-loop/references/verification-modes.md",
    ROOT / "packs/core/.apm/skills/bug-fix/SKILL.md",
)
GUIDE_AND_ARCHITECTURE_PAGES = (HOW_TO, EXPLANATION, REFERENCE, ARCHITECTURE, ACCEPTANCE_LOOP)
RETIRED_PHRASES = (
    "exact stub code",
    "exact test code",
    "approved stub",
    "approved-stub",
    "approved TDD block",
    "approved block",
    "approved code unchanged",
    "proposed test bytes",
    "land committed red stubs",
    "in-PLAN stub generation",
    "PLAN's TDD-stub generation",
    "planning proof",
    "stub: true",
    "no stub (mode)",
    "no stub (implementation-discovered)",
    "`no stub` disposition",
)
BYTE_IDENTITY = re.compile(r"byte[ -]identity")
BYTE_IDENTITY_STUB_FENCE_HOMES = (TDD_STUBS, ACCEPTANCE_LOOP)
PROTECTED_CLASSES = (
    "security boundary",
    "data loss or durability",
    "migration or persisted state",
    "public interface",
    "irreversible operation",
)
MECHANISM_CLAIM = (
    "a mechanism claim whose falsehood could move only the chosen mechanism "
    "and on which no protected class depends"
)


def _text(path: Path) -> str:
    """Return one lifecycle contract source as UTF-8 text."""

    return path.read_text(encoding="utf-8")


def _flat(path: Path) -> str:
    """Return a source with every whitespace run collapsed, lower-cased."""

    return " ".join(_text(path).split()).lower()


def _section(path: Path, start: str, end: str) -> str:
    """Return the flattened, lower-cased text from `start` up to `end`."""

    text = _text(path)
    begin = text.index(start)
    stop = text.index(end, begin + len(start))
    return " ".join(text[begin:stop].split()).lower()


def _step_8() -> str:
    """Return work-loop PLAN step 8, up to step 8a."""

    return _section(WORK_LOOP, "8. **Design construction tests", "8a.")


def _execute_modes() -> str:
    """Return EXECUTE's verification-mode list."""

    return _section(WORK_LOOP, "Match discipline to verification mode:", "**Controlled full-mode amendment")


def _routing() -> str:
    """Return new-spec's routing section, from its anchor to repository anchors."""

    return _section(NEW_SPEC, 'id="load-bearing-claim-routing"', "**Resolve repository anchors")


def _routing_rows() -> dict[str, str]:
    """Return the routing table rows, keyed by routing input name."""

    rows: dict[str, str] = {}
    for line in _text(NEW_SPEC).split("\n"):
        match = re.match(r"\s*\| `([a-z-]+)` ", line)
        if match:
            rows[match.group(1)] = " ".join(line.split()).lower()
    return rows


def _eval_record(path: Path, record_id: str) -> dict[str, object]:
    """Return one named eval record from a shipped skill harness."""

    records = json.loads(_text(path))["evals"]
    return next(record for record in records if record["id"] == record_id)


def _assert_all(text: str, *needles: str) -> None:
    """Assert every needle (lower-cased) is in the flattened text."""

    for needle in needles:
        assert needle.lower() in text, needle


@pytest.mark.parametrize("source", LIVE_SOURCES, ids=lambda path: path.name)
def test_sweep(source: Path) -> None:
    """AC-0001, AC-0002: no retired phrase; byte identity only for the stub fence."""

    assert source.is_file(), f"live source missing: {source}"
    flat = _flat(source)
    for phrase in RETIRED_PHRASES:
        assert phrase.lower() not in flat, phrase
    hits = [m.start() for m in BYTE_IDENTITY.finditer(flat)]
    if source not in BYTE_IDENTITY_STUB_FENCE_HOMES:
        assert not hits
        return
    for start in hits:
        # Same sentence (or table cell) as the supervisor's `stub` fence.
        left = max(flat.rfind(". ", 0, start), flat.rfind("|", 0, start))
        right_candidates = [i for i in (flat.find(". ", start), flat.find("|", start)) if i != -1]
        right = min(right_candidates) if right_candidates else len(flat)
        assert "`stub` fence" in flat[left + 1 : right]


def test_plan_does_not_write_repository_tests_or_permit_plan_time_stubs() -> None:
    """Live tool sources carry no PLAN-time stub permission."""

    forbidden = (
        "materialize a compilable red stub when a durable plan requires one",
        "materialised *at plan* as a compilable",
        "one stub **file per plan task**",
        "red stub written now",
        "usually the red test is then already written",
        "red stub materialised at plan per the spec-and-plan contract",
        "materialised at plan per the spec-and-plan contract",
    )
    for named in (*LIVE_SOURCES, *LIVE_PLAN_TIME_SOURCES):
        assert named.is_file(), f"live plan-time source missing: {named}"
        flat = _flat(named)
        for phrase in forbidden:
            assert phrase not in flat
    assert "pointer/self-check only" in _text(NEW_SPEC)
    assert "do not create a repository test file" in _text(NEW_SPEC)


def test_step_8_names_test_intent_and_defers_the_red() -> None:
    """AC-0003, AC-0004: PLAN step 8 carries intent; the red is written at EXECUTE."""

    step = _step_8()
    _assert_all(
        step,
        "`tests:` names the behavior, the boundary it is checked at, and the verification mode",
        "the red test is written and proven red at execute",
        "references/tdd-stubs.md",
    )


def test_execute_tdd_line_writes_the_red_at_the_real_location() -> None:
    """AC-0005: EXECUTE's TDD line."""

    modes = _execute_modes()
    _assert_all(
        modes,
        "write the red test at the real test location",
        "fails for the intended reason before production code changes",
    )


def test_reference_states_red_rules() -> None:
    """AC-0006 to AC-0010: red counting, ledger, optional fence, supervisor fence."""

    reference = _flat(TDD_STUBS)
    _assert_all(
        reference,
        "an import failure of the not-yet-written target counts as red",
        "any other collection, import, or setup error, or a timeout, does not",
        "where a spec exists, the red's command and failing output go to the verification ledger",
        "the approved plan does not require a `stub` fence",
        "where a supervisor run executes a tdd task, the plan author carries its fence in the approved task",
        "a supervisor task without a fence gets no engine-observed red proof",
        "execute's red-first rule still applies to it",
        "a fence the supervisor refuses as `stub-not-red` is either made to fail for the intended reason or removed",
        "`implementation-discovered`",
        "do not invent a helper, fixture, module, path, or symbol",
    )


def test_routing_names_protected_classes_and_splits_property_from_means() -> None:
    """AC-0011, AC-0016, AC-0017."""

    routing = _routing()
    _assert_all(routing, *PROTECTED_CLASSES)
    _assert_all(
        routing,
        "a claim about a protected class's property settles before approval",
        "the means that delivers it lives in the plan's `## design (lld)`",
    )


def test_routing_rows_admit_the_mechanism_claim() -> None:
    """AC-0012 to AC-0015, AC-0014a: two exception rows gain the claim; three rows stay."""

    rows = _routing_rows()
    assert set(rows) == {"reaches-the-contract", "unstarted-task-method", "cheap-with-an-oracle"}
    unstarted = rows["unstarted-task-method"]
    assert MECHANISM_CLAIM in unstarted
    assert unstarted.index(MECHANISM_CLAIM) < unstarted.index("**and no test can decide it directly**")
    _assert_all(
        unstarted,
        "mechanism goes in the plan's `## design (lld)` with its means marked `implementation-discovered`",
    )
    cheap = rows["cheap-with-an-oracle"]
    assert "or a reversible mechanism claim whose falsehood could move only the chosen mechanism" in cheap
    assert "on which no protected class depends" in cheap
    assert "reversible means undoing it needs no migration" in cheap
    assert "no load-bearing claim is unrouted" in rows["reaches-the-contract"]


def test_plan_template_design_section_owns_mechanism() -> None:
    """AC-0018, AC-0019."""

    design = _section(PLAN_TEMPLATE, "## Design (LLD)", "### Design decisions")
    _assert_all(
        design,
        "mechanism",
        "lives here",
        "a means no code grounds yet is marked `implementation-discovered`",
        "its chosen means and any correction go to the verification ledger",
    )


def test_spec_template_agent_rules_exclude_mechanism() -> None:
    """AC-0020."""

    rules = _section(SPEC_TEMPLATE, "## Agent Rules", "### Always do")
    _assert_all(
        rules,
        "a syscall, flag, helper name, or exact write order is mechanism that belongs in the plan's `## design (lld)`",
    )


@pytest.mark.parametrize("page", GUIDE_AND_ARCHITECTURE_PAGES, ids=lambda path: path.name)
def test_guides_and_architecture_state_the_red_is_written_at_execute(page: Path) -> None:
    """AC-0021: each guide and architecture page teaches EXECUTE-time red."""

    assert "the red test is written at execute" in _flat(page), page.name


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
    # The RFC index is generated from each record's own H1 (ADR-0112), so it no
    # longer carries a hand-written summary to assert the correction against.
    # The errata above is the record of it, and the row still resolves.
    index_row = next(
        line for line in _text(RFC_INDEX).splitlines()
        if "](0028-tdd-stub-generation-in-the-core-loop.md)" in line
    )
    assert index_row.startswith("| 0028 |")


EVAL_FILES = (WORK_LOOP_EVALS, NEW_SPEC_EVALS)
EXECUTE_RED_RECORDS = (
    (NEW_SPEC_EVALS, "tdd-stub-proof-belongs-to-work-loop-plan"),
    (WORK_LOOP_EVALS, "tdd-stub-replaces-prose-or-records-no-stub-reason"),
    (WORK_LOOP_EVALS, "tdd-stub-uses-the-stub-fence"),
)


@pytest.mark.parametrize("path", EVAL_FILES, ids=lambda path: path.parent.parent.name)
def test_evals_contain_no_retired_phrase(path: Path) -> None:
    """AC-0022: neither shipped eval harness teaches a retired phrase."""

    flat = _flat(path)
    for phrase in RETIRED_PHRASES:
        assert phrase.lower() not in flat, phrase


@pytest.mark.parametrize(
    ("path", "record_id"), EXECUTE_RED_RECORDS, ids=lambda value: getattr(value, "name", value)
)
def test_eval_records_expect_the_red_written_at_execute(path: Path, record_id: str) -> None:
    """AC-0023: each named record expects the red test written at EXECUTE."""

    expected = " ".join(str(_eval_record(path, record_id)["expected_output"]).split())
    assert "written at EXECUTE" in expected or "write the red test at EXECUTE" in expected
