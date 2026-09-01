"""Exclusive reviewer-lens ownership contracts."""

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
ADVERSARIAL = PACK_ROOT / ".apm/agents/adversarial-reviewer.md"
QUALITY = PACK_ROOT / ".apm/agents/quality-engineer.md"
SECURITY = PACK_ROOT / ".apm/agents/security-reviewer.md"


def _compact(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def _raw(path: Path) -> str:
    """Return prompt text without collapsing its parser-significant lines."""
    return path.read_text(encoding="utf-8")


def _finding_template(path: Path) -> str:
    """Return the fenced finding template that defines a reviewer's wire format."""
    match = re.search(r"```\n(## Blockers\n.*?)\n```", _raw(path), re.DOTALL)
    assert match is not None, path
    return match.group(1)


def test_ac_verification_belongs_to_adversarial_reviewer() -> None:
    owner = _compact(ADVERSARIAL)
    loser = _compact(QUALITY)
    assert "Acceptance Criterion verification." in owner, ADVERSARIAL
    assert "Every Acceptance Criterion has a passing verification artifact." not in loser, QUALITY
    assert "Adversarial-reviewer exclusively maps" in loser, QUALITY


def test_test_strength_belongs_to_quality_engineer() -> None:
    owner = _compact(QUALITY)
    loser = _compact(ADVERSARIAL)
    assert "You exclusively own test strength" in owner, QUALITY
    assert "assess whether they pin a real invariant or mirror the implementation" not in loser, ADVERSARIAL
    assert "Quality-engineer exclusively judges test strength" in loser, ADVERSARIAL


def test_contract_visible_errors_belong_to_adversarial_reviewer() -> None:
    owner = _compact(ADVERSARIAL)
    loser = _compact(QUALITY)
    assert "You exclusively own the caller-visible error shape" in owner, ADVERSARIAL
    assert "What does the caller see when this fails?" not in loser, QUALITY
    assert "Adversarial-reviewer owns the contract-visible error shape" in loser, QUALITY


def test_inferred_edge_cases_belong_to_quality_engineer() -> None:
    owner = _compact(QUALITY)
    loser = _compact(ADVERSARIAL)
    assert "You exclusively own the inferred enumeration" in owner, QUALITY
    assert "**Edge cases.** Empty input, max input, malformed input" not in loser, ADVERSARIAL
    assert "Quality-engineer exclusively owns inferred edge-case enumeration" in loser, ADVERSARIAL


def test_threat_findings_belong_to_security_reviewer() -> None:
    owner = _compact(SECURITY)
    loser = _compact(ADVERSARIAL)
    assert "You exclusively own every threat finding." in owner, SECURITY
    assert "What data does this touch? Is access controlled?" not in loser, ADVERSARIAL
    assert "security-reviewer exclusively owns every threat finding" in loser, ADVERSARIAL


def test_repository_idiom_splits_structure_from_living_cost() -> None:
    adversarial = _compact(ADVERSARIAL)
    quality = _compact(QUALITY)
    assert "You exclusively own structural-pattern fit." in adversarial, ADVERSARIAL
    # The realistic mutation is quality claiming the concern in adversarial's own
    # words. Its cession line says "adversarial-reviewer owns structural-pattern
    # fit", so this fires only on a genuine duplicate claim.
    assert "You exclusively own structural-pattern fit." not in quality, QUALITY
    assert "adversarial-reviewer owns structural-pattern fit" in quality, QUALITY
    assert "You exclusively own that testability, reliability, observability, and maintenance-cost assessment" in quality, QUALITY
    assert "Quality-engineer owns the testability, reliability, observability, and maintenance cost" in adversarial, ADVERSARIAL


def test_exploratory_run_oracle_belongs_to_quality_engineer_review() -> None:
    quality = _compact(QUALITY)
    adversarial = _compact(ADVERSARIAL)
    assert "Exploratory / visual fuzz runs." in quality, QUALITY
    assert "Verify the invariant is named" in quality, QUALITY
    assert "input variation is recorded or seeded reproducibly" in quality, QUALITY
    assert "An exploratory run with no stated invariant is not a verification artifact; flag it." in quality, QUALITY
    assert "Exploratory / visual fuzz runs." not in adversarial, ADVERSARIAL
    # The realistic mutation is restoring adversarial's ORIGINAL wording, which
    # never contained the heading above — pin a distinctive phrase from it.
    assert "flavors assert invariants under varied driving" not in adversarial, ADVERSARIAL
    assert "Quality-engineer also exclusively owns exploratory-run invariant checks" in adversarial, ADVERSARIAL


def test_manual_qa_result_oracle_belongs_to_adversarial_reviewer() -> None:
    owner = _compact(ADVERSARIAL)
    for loser in (_compact(QUALITY), _compact(SECURITY)):
        assert "Manual and assertion-based QA artifacts must record" not in loser
    assert "Manual and assertion-based QA artifacts must record the check performed and the result observed." in owner


def test_testing_strategy_named_artifacts_belong_to_adversarial_reviewer() -> None:
    adversarial = _compact(ADVERSARIAL)
    quality = _compact(QUALITY)
    assert "If Testing Strategy names specific artifacts by file or function" in adversarial, ADVERSARIAL
    assert "same existence-and-declared-mode check" in adversarial, ADVERSARIAL
    assert "A promised artifact that is absent is a Blocker" in adversarial, ADVERSARIAL
    assert "If Testing Strategy names specific artifacts by file or function" not in quality, QUALITY
    assert "Adversarial-reviewer exclusively maps" in quality, QUALITY
    assert "artifacts Testing Strategy names by file or function" in quality, QUALITY


def test_security_findings_are_calibrated_to_a_named_attacker() -> None:
    # Scoped to the calibration section itself. A whole-file check passes while
    # the rule is gutted, as long as the phrases survive in unrelated prose.
    raw = _raw(SECURITY)
    start = raw.index("## Calibrate to the attacker, not the catalogue")
    section = " ".join(raw[start : raw.index("\n## ", start + 1)].split())
    # Both gates must be present in the rule: a reachable path, and no easier
    # capability the attacker already holds.
    for gate in (
        "Name the attacker for every finding",
        "**Reachability.**",
        "**No easier path.**",
        "Prefer one exploitable defect to five theoretical ones.",
    ):
        assert gate in section, (SECURITY, gate)
    # The calibration must stay a severity rule. Without these it reads as a
    # licence to suppress, which is the failure mode it would introduce.
    assert "narrows **severity, never coverage.**" in section, SECURITY
    assert "an unpriced finding is a Concern, not a silence" in section, SECURITY
    for never_downgraded in (
        "trust-boundary crossing",
        "missing authentication or authorization check",
        "secret in the diff",
        "control the spec required",
    ):
        assert never_downgraded in section, (SECURITY, never_downgraded)


def test_fix_states_outcomes_and_constraints_not_mechanisms() -> None:
    for path in (ADVERSARIAL, QUALITY, SECURITY):
        text = _compact(path)
        assert "Fix: <required outcome and constraints>" in text, path
        assert "Fix: <one-sentence fix>" not in text, path
        assert "never prescribe a mechanism" in text, path


def test_reviewer_finding_wire_format_survives() -> None:
    for path in (ADVERSARIAL, QUALITY, SECURITY):
        text = _raw(path)
        compact = _compact(path)
        template = _finding_template(path)
        for number in (1, 2, 3):
            template_lines = [
                line
                for line in template.splitlines()
                if line.startswith(f"**{number}. <title>.**")
            ]
            assert len(template_lines) == 1, path
            template_line = template_lines[0]
            assert re.match(
                rf"^\*\*{number}\. <title>\.\*\* `path/to/file\.ext:line`\.",
                template_line,
            ), path
            assert "Fix: " in template_line, path
            anchors = re.findall(r"`[^`\n]+:[^`\n]+`", template_line)
            assert anchors == ["`path/to/file.ext:line`"], path
        after_template = text[text.index(f"```\n{template}\n```") + len(template) + 7 :]
        # The sentinel is byte-compared by loop-cohort.py's clean fast path, so
        # every prompt must show it unwrapped on one physical line.
        assert (
            "If everything's clean, output `Clean — ready to commit.`"
            in after_template[:160]
        ), path
        assert "Cross-lens referrals" in compact, path
        assert "using the existing severity buckets and output format" in compact, path
        assert "Never emit another lens's finding." in compact, path
    # The footer must close the template and carry a bullet. Its *content* is
    # deliberately unconstrained: footer-bearing reports always take the
    # adjudicator path, so a content rule here would be a guard that looks
    # load-bearing without being one.
    security_template = _finding_template(SECURITY).rstrip()
    footer = security_template[security_template.index("## Not checked") :]
    assert security_template.endswith(footer), SECURITY
    bullets = [ln for ln in footer.splitlines() if ln.startswith("- ")]
    assert len(bullets) == 1, SECURITY
