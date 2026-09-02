"""Guard the verification-ledger contract against post-approval drift."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
_MUTABILITY_MESSAGE = (
    "post-approval mutability guidance must agree with the approved-artifact hash guards"
)


def _read(relative: str) -> str:
    """Read one UTF-8 repository surface."""
    return (ROOT / relative).read_text(encoding="utf-8")


def _section(text: str, heading: str, level: int = 2) -> str:
    """Return one Markdown heading section without neighbouring guidance."""
    marker = "#" * level
    match = re.search(
        rf"^{re.escape(marker)} {re.escape(heading)}\n(.*?)(?=^{re.escape(marker)} |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"missing {heading!r} section"
    return match.group(0)


def _between(text: str, start: str, end: str) -> str:
    """Return the bounded source region between two stable markers."""
    start_index = text.index(start)
    end_index = text.find(end, start_index)
    if end_index == -1:
        end_index = len(text)
    return text[start_index:end_index]


def test_hash_guard_pins_both_approved_artifacts_while_executing_is_legal() -> None:
    """Prove the executable guard, not prose, defines the frozen baseline."""
    guard = _read("packs/core/.apm/skills/work-loop/scripts/_loop_guards.py")
    canonical = _between(guard, "def sha256_canonical_contract", "# ── run-id validation")
    legality = _between(guard, "_LEGAL_AFTER_APPROVAL =", "@contained_reason\ndef assert_status_legal")
    check = _between(
        guard, "def check_plan_current(", "def check_schedule_current("
    )

    assert "def sha256_canonical_contract(path: Path)" in canonical
    assert "canonical_contract(" in canonical
    assert "return _sha256_bytes(canonical.encode(\"utf-8\"))" in canonical
    assert '"spec.md": ("Approved", "Implementing", "Shipped")' in legality
    assert '"plan.md": ("Approved", "Executing", "Done")' in legality
    assert "current_spec_hash = sha256_canonical_contract(spec_path)" in check
    assert 'state.get("approved_spec_hash") != current_spec_hash' in check
    assert "current_plan_hash = sha256_canonical_contract(plan_path)" in check
    assert 'state.get("approved_plan_hash") != current_plan_hash' in check


def test_closed_rule_sources_reject_executing_time_substantive_edits() -> None:
    """Keep every closed rule-bearing source aligned with the executable freeze."""
    guard = _read("packs/core/.apm/skills/work-loop/scripts/_loop_guards.py")
    assert "approved_spec_hash" in guard and "approved_plan_hash" in guard
    assert '"plan.md": ("Approved", "Executing", "Done")' in guard

    convention = _section(
        _read("packs/core/seeds/docs/CONVENTIONS.md"),
        "A spec directory freezes as a unit, when the spec ships",
        3,
    )
    template = _read("packs/core/.apm/skills/new-spec/assets/plan.md").split(
        "<!-- Existing plans", 1
    )[0]
    lifecycle = _section(
        _read("packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md"),
        "Verification ledger",
    )
    explanation = _section(
        _read("guides/core/explanation/why-the-plan-owns-the-lld.md"),
        "The shape of the answer",
    )
    pre_execute = _section(
        _read("packs/core/.apm/skills/work-loop/references/pre-execute-review.md"),
        "Mid-EXECUTE re-plan — Phase-1 note",
    )
    schema = _between(
        _read("packs/core/.apm/skills/work-loop/references/state-schema.md"),
        "**What the pin covers.**",
        "\n##",
    )

    required = {
        "convention": (convention, ("only while the plan is `Drafting`", "both `spec.md` and `plan.md` are pinned in substance", "Only lifecycle", "bookkeeping —")),
        "template": (template, ("only while its Status is `Drafting`", "After approval, `spec.md` and `plan.md` are pinned in substance", "only lifecycle bookkeeping is permitted")),
        "lifecycle": (lifecycle, ("approved `spec.md` and `plan.md` retain obligations only", "not hash-pinned", "controlled amendment procedure")),
        "explanation": (explanation, ("allowed to change as you learn while it is `Drafting`", "after approval, follow", "plan-and-execute how-to")),
        "pre-execute": (pre_execute, ("immutable in substance", "Any *substantive* edit to `spec.md` or `plan.md` after", "still causes a refusal", "surface to the human and stop")),
        "state schema": (schema, ("Everything else stays pinned", "acceptance-criterion text", "task text", "`Depends on:` edges")),
    }
    for source, (section, evidence) in required.items():
        normalized = " ".join(section.split())
        assert all(clause in normalized for clause in evidence), (
            f"{source}: {_MUTABILITY_MESSAGE}"
        )
        assert not re.search(
            r"(?:only |allowed )?(?:to )?(?:change|edit|mutable).*?`Executing`|`Executing`.*?(?:change|edit|mutable)",
            normalized,
            flags=re.IGNORECASE | re.DOTALL,
        ), f"{source}: {_MUTABILITY_MESSAGE}"


def test_how_to_keeps_immutability_and_ledger_destination() -> None:
    """Keep the public how-to's retained rule and its execution-observation route."""
    section = _section(
        _read("guides/core/how-to/plan-and-execute-non-trivial-work.md"),
        "Spec amendment mid-flight",
        3,
    )

    assert "the approved plan is immutable in substance" in section
    assert "Anything else" in section and "invalidates it" in section
    assert "verification-ledger procedure" in section
    assert "delivery-contract-lifecycle.md#verification-ledger" in section


def test_work_loop_uses_a_pointer_without_a_second_ledger_rule() -> None:
    """Keep Step 2 as a resolvable pointer to the lifecycle-owned procedure."""
    execute = _section(
        _read("packs/core/.apm/skills/work-loop/SKILL.md"), "Step 2. EXECUTE"
    )
    pointer = (
        "**Execution observations:** follow the [verification-ledger procedure]"
        "(references/delivery-contract-lifecycle.md#verification-ledger)."
    )

    assert pointer in execute
    assert execute.count("verification-ledger procedure") == 1
