"""Registry and selector contract for phase-scoped policy delivery.

Sole home for the family-table, selection-map and delivery-record assertions.
The four `# STUB:` blocks below are materialized unchanged from
`docs/specs/phase-policy-registry-and-selector/plan.md`; the cases after them
fill the criteria those stubs did not cover.
"""

# STUB: AC3 — the selection map is exactly the declared eleven-key mapping
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


def test_selection_map_is_the_declared_mapping():
    selection = _registry_block()["selection"]

    assert selection == {
        "SPEC-PLAN-DRAFTING": AUTHORING,
        "SPEC-PLAN-REVIEW": AUTHORING,
        "CODE-IMPLEMENTATION": IMPLEMENTING,
        "CODE-VERIFICATION": IMPLEMENTING,
        "CODE-REVIEW": IMPLEMENTING,
        "DIRECT-LIGHT": IMPLEMENTING,
        "SPEC-HUMAN-GATE": [],
        "PLAN-HUMAN-GATE": [],
        "SPEC-PLAN-APPROVED": [],
        "CODE-HUMAN-GATE": [],
        "DONE": [],
    }


# STUB: AC6 — the emitted id sequence equals the registry's declared list
# Stored and validated in PLAN's T2 Tests: subsection. Comparing against the
# registry, not against a second run, is the whole point: a deterministically
# reversed selector satisfies "stable across runs".
import json
import subprocess
import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SELECTOR = PACK_ROOT / ".apm/skills/work-loop/scripts/select-policy-families.py"
REGISTRY = PACK_ROOT / ".apm/skills/work-loop/references/policy-families.md"
REPO_ROOT = PACK_ROOT.parents[1]


def test_emitted_order_equals_declared_order():
    key = "SPEC-PLAN-DRAFTING"
    proc = subprocess.run(
        [sys.executable, str(SELECTOR), "--registry", str(REGISTRY),
         "--root", str(REPO_ROOT), key],
        capture_output=True, text=True, check=False,
    )

    assert proc.returncode == 0, proc.stderr
    emitted = [f["id"] for f in json.loads(proc.stdout)["families"]]
    declared = _registry_block()["selection"][key]
    assert emitted == declared


# STUB: AC7 — each emitted entry equals its registry record plus a real digest
# Stored and validated in PLAN's T3 Tests: subsection. Comparing tier and module
# against the registry is what a presence-only assertion misses: a selector
# reporting every family as `advisory` passes the weaker form.
import hashlib


def test_emitted_entry_equals_registry_record_with_digest():
    record = {f["id"]: f for f in _registry_block()["families"]}
    entry = _select("CODE-IMPLEMENTATION")["families"][0]
    source = record[entry["id"]]

    assert entry["tier"] == source["tier"]
    assert entry["module"] == source["module"]
    resolved = _resolve(source["module"], REPO_ROOT)
    assert entry["module_digest"] == hashlib.sha256(resolved.read_bytes()).hexdigest()


# STUB: AC8 — an unknown selection key is refused on stderr with a non-zero exit
# Stored and validated in PLAN's T4 Tests: subsection. The prefix is asserted at
# the start of the stream, not as a bare substring: the script name appears in
# argv echoes, so a substring check can pass while the message is missing.
def test_unknown_selection_key_is_refused():
    proc = subprocess.run(
        [sys.executable, str(SELECTOR), "--registry", str(REGISTRY),
         "--root", str(REPO_ROOT), "NO-SUCH-PHASE"],
        capture_output=True, text=True, check=False,
    )

    assert proc.returncode != 0
    assert proc.stderr.startswith("select-policy-families:")


# --- EXECUTE fill: construction helpers the stubs reference -------------------
#
# `_resolve` deliberately re-derives the locator search order from the spec
# rather than importing the selector's own resolver. Importing it would make
# AC7's digest assertion compare the selector against a copy of itself, and
# T3's mutation (reversing the selector's `seed:` order) would then move both
# sides and stay green. An independent second statement is the oracle.

_SKILL_ROOTS = (".claude/skills", ".agents/skills", "packs/core/.apm/skills")
_SEED_ROOTS = ("", "packs/core/seeds")

REGISTRY_ARGS = ["--registry", str(REGISTRY), "--root", str(REPO_ROOT)]


def _resolve(module: str, root: Path) -> Path:
    namespace, _, remainder = module.partition(":")
    roots = _SKILL_ROOTS if namespace == "skill" else _SEED_ROOTS
    for base in roots:
        candidate = root / base / remainder if base else root / remainder
        if candidate.is_file():
            return candidate
    raise AssertionError(f"{module!r} resolves to no file under {root}")


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SELECTOR), *args],
        capture_output=True, text=True, check=False,
    )


def _select(key: str) -> dict:
    proc = _run(*REGISTRY_ARGS, key)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _write_registry(tmp_path: Path, registry: dict, info: str = "json policy-registry.v1") -> Path:
    path = tmp_path / "policy-families.md"
    path.write_text(f"# fixture\n\n```{info}\n{json.dumps(registry, indent=2)}\n```\n",
                    encoding="utf-8")
    return path


def _refuse(registry_path: Path, key: str = "CODE-IMPLEMENTATION") -> subprocess.CompletedProcess:
    proc = _run("--registry", str(registry_path), "--root", str(REPO_ROOT), key)
    assert proc.returncode != 0, f"expected refusal, got 0:\n{proc.stdout}"
    assert proc.stderr.startswith("select-policy-families:"), proc.stderr
    return proc


# --- AC1: the carrier ---------------------------------------------------------

def test_registry_carries_one_versioned_block_whose_tokens_agree():
    text = REGISTRY.read_text(encoding="utf-8")
    tagged = re.findall(r"^```(json policy-registry\.v\d+)$", text, re.MULTILINE)

    assert tagged == ["json policy-registry.v1"]
    assert _registry_block()["schema_version"] == 1


# --- AC2: the family table ----------------------------------------------------

def test_families_are_the_declared_five_records():
    assert _registry_block()["families"] == [
        {"id": "observable-outcome", "tier": "precise",
         "module": "skill:new-spec/assets/spec.md"},
        {"id": "repository-anchoring", "tier": "precise",
         "module": "skill:new-spec/assets/plan.md"},
        {"id": "new-spec-step-5a", "tier": "advisory",
         "module": "skill:new-spec/SKILL.md"},
        {"id": "the-razor", "tier": "advisory", "module": "seed:AGENTS.md"},
        {"id": "cognitive-load", "tier": "advisory",
         "module": "seed:.agents/rules/cognitive-load.md"},
    ]


# --- AC4: the key domain comes from loop-engine.py, not from the registry -----

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


def test_selection_covers_every_legal_state_plus_the_reserved_token():
    expected = _fsm_states() | {"DIRECT-LIGHT"}

    assert set(_registry_block()["selection"]) == expected


# --- AC5: the record envelope -------------------------------------------------

def test_record_envelope_is_exact_with_a_null_assembled_digest():
    for key in _registry_block()["selection"]:
        proc = _run(*REGISTRY_ARGS, key)
        assert proc.returncode == 0, proc.stderr
        assert proc.stderr == "", f"{key}: diagnostics leaked to stderr"
        record = json.loads(proc.stdout)
        assert set(record) == {"selection_key", "families", "assembled_brief_digest"}
        assert record["selection_key"] == key
        assert record["assembled_brief_digest"] is None


# --- AC7: resolution prefers the copy an acting agent reads -------------------

def test_seed_locator_prefers_the_live_root_over_the_seed_copy():
    """The one candidate pair in this tree that actually differs.

    Every `skill:` candidate here is byte-identical, so a permutation is
    invisible; root AGENTS.md and packs/core/seeds/AGENTS.md differ, which is
    what makes the preference order observable at all.
    """
    entry = next(f for f in _select("CODE-IMPLEMENTATION")["families"]
                 if f["id"] == "the-razor")
    live = hashlib.sha256((REPO_ROOT / "AGENTS.md").read_bytes()).hexdigest()
    seeded = hashlib.sha256(
        (REPO_ROOT / "packs/core/seeds/AGENTS.md").read_bytes()).hexdigest()

    assert live != seeded, "fixture assumption broke: the two copies converged"
    assert entry["module_digest"] == live


def test_skill_locator_prefers_the_first_candidate_root(tmp_path):
    """Synthetic, because the repository tree cannot answer this.

    All three `skill:` candidates here hold identical bytes, so any order
    yields the same digest. Two deliberately different files at the first and
    third candidate paths give the order an oracle.
    """
    first = tmp_path / ".claude/skills/probe/rule.md"
    third = tmp_path / "packs/core/.apm/skills/probe/rule.md"
    for path, body in ((first, "first candidate\n"), (third, "third candidate\n")):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    registry = {
        "schema_version": 1,
        "families": [{"id": "probe", "tier": "advisory",
                      "module": "skill:probe/rule.md"}],
        "selection": {"CODE-IMPLEMENTATION": ["probe"]},
    }
    proc = _run("--registry", str(_write_registry(tmp_path, registry)),
                "--root", str(tmp_path), "CODE-IMPLEMENTATION")

    assert proc.returncode == 0, proc.stderr
    digest = json.loads(proc.stdout)["families"][0]["module_digest"]
    assert digest == hashlib.sha256(first.read_bytes()).hexdigest()


def test_every_selected_entry_matches_its_registry_record(tmp_path):
    by_id = {f["id"]: f for f in _registry_block()["families"]}
    for key in _registry_block()["selection"]:
        for entry in _select(key)["families"]:
            source = by_id[entry["id"]]
            assert entry["tier"] == source["tier"]
            assert entry["module"] == source["module"]
            resolved = _resolve(source["module"], REPO_ROOT)
            assert entry["module_digest"] == hashlib.sha256(
                resolved.read_bytes()).hexdigest()
            assert re.fullmatch(r"[0-9a-f]{64}", entry["module_digest"])


# --- AC8: the refusal set -----------------------------------------------------

def _base_registry() -> dict:
    return json.loads(json.dumps(_registry_block()))


def test_duplicate_family_id_is_refused(tmp_path):
    registry = _base_registry()
    registry["families"].append(dict(registry["families"][0]))
    _refuse(_write_registry(tmp_path, registry))


def test_selection_naming_an_unknown_family_is_refused(tmp_path):
    registry = _base_registry()
    registry["selection"]["CODE-IMPLEMENTATION"] = ["no-such-family"]
    _refuse(_write_registry(tmp_path, registry))


def test_unresolvable_module_is_refused(tmp_path):
    registry = _base_registry()
    registry["families"][3]["module"] = "seed:no/such/file.md"
    _refuse(_write_registry(tmp_path, registry))


def test_unknown_tier_is_refused(tmp_path):
    registry = _base_registry()
    registry["families"][3]["tier"] = "blocking"
    _refuse(_write_registry(tmp_path, registry))


def test_unknown_module_namespace_is_refused(tmp_path):
    registry = _base_registry()
    registry["families"][3]["module"] = "packs/core/seeds/AGENTS.md"
    _refuse(_write_registry(tmp_path, registry))


def test_selection_list_repeating_an_id_is_refused(tmp_path):
    registry = _base_registry()
    registry["selection"]["CODE-IMPLEMENTATION"] = ["the-razor", "the-razor"]
    _refuse(_write_registry(tmp_path, registry))


def test_info_string_disagreeing_with_schema_version_is_refused(tmp_path):
    # A *supported* schema_version with a mismatched info string. The obvious
    # fixture (v1 / schema_version 2) is caught by the `== 1` check once the
    # pair check is removed, so it would survive its own mutation.
    registry = _base_registry()
    _refuse(_write_registry(tmp_path, registry, info="json policy-registry.v2"))


def test_unsupported_schema_version_is_refused(tmp_path):
    # A *consistent* unsupported pair, so the pair check (which runs first)
    # does not fire and this case reaches the version check.
    registry = _base_registry()
    registry["schema_version"] = 2
    _refuse(_write_registry(tmp_path, registry, info="json policy-registry.v2"))


# --- T6: the guide's coverage half shares this suite --------------------------

def test_guide_names_every_family_and_the_reserved_token():
    guide = REPO_ROOT / "guides/core/reference/phase-scoped-policy-delivery.md"
    text = guide.read_text(encoding="utf-8")

    for family in _registry_block()["families"]:
        assert family["id"] in text, f"guide omits {family['id']}"
    assert "DIRECT-LIGHT" in text
    for heading in ("## Declaring a family", "## Classifying a family",
                    "## Troubleshooting a selection"):
        assert heading in text, f"guide omits {heading!r}"
