"""Registry content contract for phase-scoped policy delivery.

Pack-local: every path here stays inside `packs/core`. The selector's behaviour
is repository-level — it resolves `seed:` locators against the repository root —
so it lives in `tests/roster/test_policy_family_selector.py` instead, which is
what `pack-tests-stay-in-pack` requires.
"""

# STUB: AC3 — the selection map is exactly the declared eighteen-key mapping
# Stored and validated in PLAN's T1 Tests: subsection. The literal mapping is
# the durable contract surface: it is what fails when a registry keeps every
# key and selects nothing.
import json
import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
REGISTRY = PACK_ROOT / ".apm/skills/work-loop/references/policy-families.md"

AUTHORING = ["observable-outcome", "repository-anchoring", "new-spec-step-5a",
             "the-razor", "cognitive-load"]
IMPLEMENTING = ["the-razor", "cognitive-load"]


def _registry_block() -> dict:
    text = REGISTRY.read_text(encoding="utf-8")
    match = re.search(r"^```json policy-registry\.v1\n(.*?)^```", text,
                      re.MULTILINE | re.DOTALL)
    assert match, "no `json policy-registry.v1` fenced block in policy-families.md"
    return json.loads(match.group(1))


# The supervisor stage keys and the declared constants, as the registry maps them.
STAGE_SELECTION = {
    "PRE-APPROVAL": AUTHORING,
    "admitted": [],
    "implementing": IMPLEMENTING,
    "gating": IMPLEMENTING,
    "reviewing": IMPLEMENTING,
    "awaiting-human": [],
    "terminal": [],
}
DECLARED_CONSTANTS = {"DIRECT-LIGHT": IMPLEMENTING, "PRE-APPROVAL": AUTHORING}

# The upper-case phase names an earlier release keyed on. No record carries one, so
# the registry no longer does.
RETIRED_PHASE_KEYS = (
    "SPEC-PLAN-DRAFTING", "SPEC-PLAN-REVIEW", "CODE-IMPLEMENTATION", "CODE-VERIFICATION",
    "CODE-REVIEW", "SPEC-HUMAN-GATE", "PLAN-HUMAN-GATE", "SPEC-PLAN-APPROVED",
    "CODE-HUMAN-GATE", "DONE",
)


def test_selection_map_is_the_declared_mapping():
    """The stage keys and the two declared constants, exactly."""
    selection = _registry_block()["selection"]

    assert selection == {**STAGE_SELECTION, **DECLARED_CONSTANTS}


def test_no_retired_phase_name_keys_the_registry():
    assert not set(RETIRED_PHASE_KEYS) & set(_registry_block()["selection"])


# --- EXECUTE fill -------------------------------------------------------------

def test_registry_carries_one_versioned_block_whose_tokens_agree():
    text = REGISTRY.read_text(encoding="utf-8")
    # AC1 says *exactly one fenced block*, not one registry-tagged block. Counting
    # only tagged fences would leave a stray ```bash example green against a
    # criterion it violates.
    all_fences = re.findall(r"^```(.*)$", text, re.MULTILINE)
    tagged = [f for f in all_fences if f.startswith("json policy-registry.")]

    assert len(all_fences) == 2, f"expected one fence (open+close), saw {all_fences}"
    assert tagged == ["json policy-registry.v1"]
    assert _registry_block()["schema_version"] == 1


def test_families_are_the_declared_five_records():
    assert _registry_block()["families"] == [
        {"id": "observable-outcome", "tier": "precise",
         "module": "skill:new-spec/assets/spec.md"},
        {"id": "repository-anchoring", "tier": "precise",
         "module": "skill:new-spec/assets/plan.md"},
        {"id": "new-spec-step-5a", "tier": "advisory",
         "module": "skill:new-spec/SKILL.md"},
        {"id": "the-razor", "tier": "advisory", "module": "seed:AGENTS.md"},
        # Shares a module with the-razor: `module` names where a rule's text
        # lives, and both now live inline in AGENTS.md. This is the registry's
        # first duplicate module; no uniqueness constraint exists.
        {"id": "cognitive-load", "tier": "advisory", "module": "seed:AGENTS.md"},
    ]


def test_selection_covers_every_supervisor_stage_plus_the_declared_constants():
    expected = set(STAGE_SELECTION) | set(DECLARED_CONSTANTS)

    assert set(_registry_block()["selection"]) == expected
