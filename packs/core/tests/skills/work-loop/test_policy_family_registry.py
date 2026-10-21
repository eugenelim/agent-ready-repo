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


# Pinned engine-state entries, as they stood before the stage keys landed.
ENGINE_STATE_SELECTION = {
    "SPEC-PLAN-DRAFTING": AUTHORING,
    "SPEC-PLAN-REVIEW": AUTHORING,
    "CODE-IMPLEMENTATION": IMPLEMENTING,
    "CODE-VERIFICATION": IMPLEMENTING,
    "CODE-REVIEW": IMPLEMENTING,
    "SPEC-HUMAN-GATE": [],
    "PLAN-HUMAN-GATE": [],
    "SPEC-PLAN-APPROVED": [],
    "CODE-HUMAN-GATE": [],
    "DONE": [],
}

# Supervisor stage key -> the engine states it replaces.
STAGE_KEYS = {
    "PRE-APPROVAL": ["SPEC-PLAN-DRAFTING", "SPEC-PLAN-REVIEW"],
    "admitted": ["SPEC-PLAN-APPROVED"],
    "implementing": ["CODE-IMPLEMENTATION"],
    "gating": ["CODE-VERIFICATION"],
    "reviewing": ["CODE-REVIEW"],
    "awaiting-human": ["SPEC-HUMAN-GATE", "PLAN-HUMAN-GATE", "CODE-HUMAN-GATE"],
    "terminal": ["DONE"],
}


def test_selection_map_is_the_declared_mapping():
    """VI-6040: engine entries, DIRECT-LIGHT, and the stage keys, exactly."""
    selection = _registry_block()["selection"]

    expected = dict(ENGINE_STATE_SELECTION)
    expected["DIRECT-LIGHT"] = IMPLEMENTING
    for key, states in STAGE_KEYS.items():
        expected[key] = ENGINE_STATE_SELECTION[states[0]]
    assert selection == expected


def test_vi_6040_engine_state_entries_are_unchanged():
    """VI-6040: every engine-state entry equals its pinned pre-change value."""
    selection = _registry_block()["selection"]

    for state, families in ENGINE_STATE_SELECTION.items():
        assert selection[state] == families, state


def test_vi_6040_every_stage_key_selects_what_its_engine_states_select():
    """VI-6040: selection by a mapped key equals selection by each of its states."""
    selection = _registry_block()["selection"]

    for key, states in STAGE_KEYS.items():
        for state in states:
            assert selection[key] == selection[state], (key, state)


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


def _fsm_states() -> set[str]:
    """Derive the legal state set from the engine's own transition tables.

    Keys are two-tuples `(source_state, event)`; the module comment at
    loop-engine.py:530 says `(mode, source_state, event)` and is wrong. Loading
    swaps in a throwaway TextIOWrapper because the module calls
    `sys.stdout.reconfigure` at import, which raises under pytest's captured
    stdout (the hazard `_loop_guards.py:613-621` documents).
    """
    import importlib.util
    import io
    import sys

    engine_path = PACK_ROOT / ".apm/skills/work-loop/scripts/loop-engine.py"
    spec = importlib.util.spec_from_file_location("_loop_engine_domain", engine_path)
    module = importlib.util.module_from_spec(spec)
    saved = sys.stdout
    sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    try:
        spec.loader.exec_module(module)
    finally:
        sys.stdout = saved
    states: set[str] = set()
    for table in (module._BOTH_TRANSITIONS, module._CODE_TRANSITIONS,
                  module._SPEC_PLAN_TRANSITIONS):
        for (source, _event), target in table.items():
            states.add(source)
            states.add(target)
    return states


def test_selection_covers_every_legal_state_plus_the_declared_constants_and_stage_keys():
    expected = _fsm_states() | {"DIRECT-LIGHT"} | set(STAGE_KEYS)

    assert set(_registry_block()["selection"]) == expected
