# Verification ledger — work-item-capture

Execution observations from PLAN. Facts recorded here were produced by running
something, not by reading it; the spec and plan cite them rather than restating
the runs.

## The argv boundary (`spike-argv-boundary.py`)

46 cases, 8 admitted (three option-on-an-admitted-tool rows were added in round 4; all three refuse). Two rules an earlier draft asserted were refuted by
running them:

- `["cat", ".env"]` was **admitted** under a `.git/`-only rule. Replaced by a
  dot-leading-component rule.
- `["cat", "a' '-delete"]` was **admitted** under the metacharacter blocklist,
  which carries no quote and no space, so naive shell re-serialisation splits
  it into two words with an option. Replaced by a positive character class.
- `["cat", "src/a.py\n"]` was **admitted** under `^…$`, because `$` matches
  before a terminal newline. Re-anchored to `\A…\Z`. The schema's own
  `repositoryPath` pattern ends `.+$` and carries the same defect, so the rule
  is enforced with an explicitly re-anchored copy.

## The storage path (`spike-store-path.py`, `spike-store-layers.py`)

> **Status, 2026-09-20:** `spike-store-layers.py` has been **deleted**. It
> mutated a literal in `project_knowledge.py` that T1 and T3 have since
> changed, so it raised at its own no-op-patch guard — correctly, since a
> stale target is a no-op patch. Its finding below was true when taken and
> is now implemented rather than predicted, so the script had no remaining
> evidentiary value and a committed file that cannot run is worse than none.
> What it proved stands on this record. `spike-store-path.py` still runs.

Walked the real write path layer by layer against a scratch copy of the store.

| Layer | Result |
| --- | --- |
| Request validator, `project_knowledge.py` | refuses `work-item` — surfaces as `provenance` at the capture boundary |
| after widening it | accepted |
| Partition validator, `knowledge_store.py` | refuses `observations/work-item/<YYYY-MM>.jsonl` with `confinement` |
| after widening it | accepted |
| Kind enumerator, `knowledge_store.py` | a `work-item` partition is invisible to any caller that enumerates kinds |

**Capture-kind sites are five**, not the nine an earlier draft claimed: the two
schema copies, the request validator, the partition allowlist, and the kind
enumerator. **Four** further literal sets hold the same three values but are different
vocabularies — the topic synthesis kind, the proposal synthesis kind, the
legacy row kind in `knowledge_store.py`, and `lint-knowledge.py`'s own
`ALLOWED_KINDS`. The last two are distinct sets, not one. Widening those would admit `work-item` into the
distillation corpus, which § D1's complement argument forbids.

**The closed diagnostic catalog holds fifteen codes** and none of the eleven
spike-local names an earlier draft promoted into the contract. After the scope
split the additions are four record codes in the capture spec's § D4 and seven
command codes, now in the capture spec's § D4 (they were `work-item-command-contract` § D2 when this was run, before the two specs were recombined), whose
§ D6 cases uses only those seven.

**A harness note worth keeping.** The first storage harness reported
`confinement` for both the target and the control, which proved nothing:
`resolve_worktree_root` shells out to `git rev-parse --show-toplevel`, and a
bare `.git` directory is not a repository. A spike without a control is a
confident guess with output attached.

## Amendment 009 — three redundancies mutation testing found

Wiring `--reasoning-payload` meant calling controls that already existed. Each
call looked correct and each turned out to be a no-op. **Only mutation
testing found them; all three passed their own tests.**

| Control the mode called | What killed it |
| --- | --- |
| `refuse_instruction_shaped_work_item` | `_deterministic_privacy_scan` already applies the same `_INSTRUCTION_SHAPE` pattern to the same six fields. Measured across all 3 shapes × 6 fields: **0** inputs the gate refuses that the general scan admits. |
| `validate_capture_request`, called after `parse_capture_request` | `parse_capture_request` ends `return validate_capture_request(parsed)`. The second call re-validated an already-validated request. |
| the first instruction-shape test | Asserted a non-zero exit. The writer refuses instruction-shaped content anyway, so the test passed with the gate deleted — a consequence, not the property. Replaced by an assertion that **no rendered dispatch message is produced**, walked over every shape-field pair. |

`AC-0035`'s outcome still holds: nothing instruction-shaped reaches the cold
context. It holds by the general scan, not by the dedicated gate, and that is
now stated in the spec's security row rather than implied by a function name.

**The generalisable point.** Each redundancy was introduced while *closing a
finding that said a control had no production caller*. Wiring a control
without first checking whether its effect is already delivered elsewhere
produces a call site that can be deleted with every test still green — which
is the same defect the finding complained about, one layer up.

## Amendment 009 — the bundled-fixes declaration in `c38fd5fb1` was wrong

That commit declared amendment 007 and the `knowledge_store.py` refusal
routing under `Bundled fixes:`. Both are authorised work, but neither
qualifies for that carve-out: the routing change alters a caller-visible
diagnostic code, which is a behavior change, and amendment 007 changes an
Acceptance Criterion, which is contract tier.
`work-loop/references/bundled-fixes.md` § "Case: refused regardless" refuses
a change reaching a contract or published interface however settled the
authorisation. They are scope, carried by their amendment records; the PR
description states them that way and does not repeat the ride-along framing.
