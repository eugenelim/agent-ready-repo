# Plan: Dependency-scoped completion receipts

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** RFC-0096 §6/§7 and [`docs/CONVENTIONS.md`](../../CONVENTIONS.md) § 4 *Contracts* govern the published shape. The cross-repository receipt is the analogous production implementation: `$defs/crossRepoNeed` in `contracts/jsonschema/workspace-entry.schema.json`, validated by `_validated_receipt_match` and `_cross_repo_receipt_satisfied` in `workspace_status_engine.py`, exercised by `packs/core/tests/skills/workspace-status/test_workspace_status_engine_autonomous.py` and `tests/roster/test_workspace_status_projection.py`. Two named deviations: that analogue stores its payload in a fenced block in a separate brief because the *remote* artifact was never readable, while this receipt stores its payload inline because the *local* artifact is gone and no second file survives to hold it; and it emits `invalid_receipt`, which this delivery must not reuse.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit.

## Approach

Registration first so the work can dispatch, then four layers, each leaving the
repository working: the published shape, the consumer that reads it, the
producer that must not emit what the consumer would refuse, then the records.

The consumer lands after the schema because the schema is what an adopter writes
by hand and what the engine's validator must agree with. The producer lands
after the consumer because tightening `plan_completion_receipt` rewrites a
shipped Wave 4 fixture, and doing that before the consumer exists would leave a
window where the fixture asserts a grammar nothing reads.

## Constraints

- `plan.md` is hash-pinned once `loop-cohort approve-plan` persists it. No task
  may require writing to this file afterwards. Observed mutation results go to
  [`notes/mutation-proofs.md`](notes/mutation-proofs.md), which is not pinned.
- Three projection homes, not two. `packs/core/.apm/` is the source of truth;
  `.agents/` and `.claude/` are ordinary projections; and
  `packages/agentbundle/agentbundle/_data/` holds packaged runtime *pairs* for
  both edited scripts, synced only on `make build-self`'s real-write path
  (`self_host.py:88-114`). `make build-self` therefore runs in the same task as
  each runtime edit, not once at the end — otherwise
  `tests/roster/test_workspace_status_projection.py` fails on drift and the
  layer does not leave the repository working.
- Those `_data/` pairs sit under the curation guard's `ENGINE_PREFIX` with
  carve-outs only for `build/recipes/` and `/tests/`, so every commit touching
  either runtime carries `Engine-Change-RFC: 0096`.
- `docs/specs/close-work-extraction-and-immediate-disposition/` is frozen
  (`plan.md` `Done`, `spec.md` `Shipped`). No task edits it. Its quoted fixture
  values are history, and the running fixture lives only in
  `packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py`.
- Re-derive the next core version from `origin/main:packs/core/pack.toml`
  immediately before the commit; a peer worktree may have bumped it meanwhile.

## Construction tests

New suite: `tests/roster/test_dependency_scoped_completion_receipts.py`, collected
by `make test`'s `pytest tests/ -q` sweep. Producer assertions extend the shipped
`packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py` rather
than opening a second home for `plan_completion_receipt`'s contract.

Four mechanisms the criteria do not give away:

- **AC3's comparison values are read, not written, in all three homes.** The test
  opens `contracts/jsonschema/delivery-lifecycle-record.schema.json`, reads the
  three named JSON paths, and compares each against the published schema, the
  engine's validator constants, and the producer's. A literal copied into the
  test would pass while the homes disagreed.
- **AC4 and AC5 share one fixture generator with one variable.** The generator
  builds a workspace whose citing entry is `Approved` with an `Approved` sibling
  plan — so its only possible refusal is its dependency — and takes a single
  `keep_membership` flag. Probe A in [`notes/probes.md`](notes/probes.md)
  re-measured that the flag alone flips `missing_dependency` to
  `unsatisfied_dependency`; writing the two fixtures independently is how a pair
  silently stops discriminating. That probe also records why AC5 asserts the
  dependant's finding rather than an empty finding list: the kept-membership run
  legitimately emits a second `missing_artifact` against the target path.
- **AC7's second clause needs its own read.** "The citing entry itself remains
  present in the projection" is asserted against `canonical.blocked` plus
  `canonical.ready`, because the defect it guards against —
  `_parse_membership_entry` discarding the entry — removes the path from every
  collection at once and would otherwise look like a clean refusal.
- **AC9's cross-repository half reuses the shipped oracle unchanged.** The
  control is `tests/roster/test_status_projection_and_context_exclusion.py`'s
  existing cross-repo fixture, whose comment already records that
  `invalid_receipt` presence is the signal that the read path was entered. No new
  baseline is captured; a captured-after-the-change baseline could not fail.

## Durable-output map

| Spec durable output | Task | Evidence |
| --- | --- | --- |
| Interface contract (`workspace-entry.schema.json`) | T1 | AC1–AC3 green |
| Maintainer procedure (`workspace-status/SKILL.md`) | T2 | AC12's second clause green |
| Maintainer procedure (`close-work/SKILL.md`) | T4 | AC12's first clause green |
| User documentation (`guides/core/reference/workspace-toml-schema.md`) | T4 | AC11 green |
| Decision rationale (ADR-0103) | T0 | Accepted and indexed |
| Release history (`docs/product/changelog.md`) | T4 | Dated `[core]` entry at the bumped version |

## Design (LLD)

### Design decisions

The receipt is an optional object on `$defs/localNeed` rather than a third need
variant, so `Dependency.type` keeps exactly two values and no engine branch on
`local` versus `cross-repo` is disturbed.

A malformed completion receipt gets its own finding code,
`invalid_completion_receipt`. Reusing `invalid_receipt` would falsify a ticked
criterion in a frozen spec — `status-projection-and-context-exclusion` AC57
states it is "a code only `_cross_repo_receipt_satisfied` emits" — and would
blunt the oracle at `test_status_projection_and_context_exclusion.py:1007-1009`,
which reads that uniqueness as proof the cross-repo read path was entered.

### Data & schema

`receipt` is an object with `additionalProperties: false` and all four
properties required when present. The three identifier grammars appear as values
rather than a `$ref`, because a cross-file `$ref` would couple two independently
versioned `contract_version` documents; AC3's three-way equality read is what
keeps the copies honest.

### Interfaces & contracts

`contracts/jsonschema/workspace-entry.schema.json` gains the `receipt` object and
an `x-spec` entry naming this spec directory.

### Behavior & rules

Validation happens at **satisfaction time**, never in the need parser.
`_parse_dependency`'s caller returns `None` for the whole entry as soon as any
need yields a finding (`workspace_status_engine.py:866-868`), and
`blocks_dependencies` covers only `invalid_entry` and `invalid_artifact_path`
(`:2418-2420`) — so a parser-emitted receipt finding would delete the citing
entry from the projection *and* leave its path out of
`structurally_blocked_paths`, letting that entry's own dependants resolve from
the file. The parser therefore carries the receipt through unvalidated, as
opaque bounded text.

The new branch sits in `_dependency_is_satisfied` at the call site after the
safety check (`:2686-2690`), gated on `not matches` and on that check having
returned `missing_dependency`. It must not go inside
`_dependency_metadata_safety_finding`, which the `defect`-kind path at `:2658`
also reaches. Placement after the `structurally_blocked_paths` guard at `:2604`
and after the cooled return at `:2673` is what AC5 pins.

### Failure, edge cases & resilience

A receipt whose target artifact still exists is never validated and never read:
closeout writes the receipt and a later wave prunes the file, so both existing at
once is the ordinary transitional state. Gating validation on the
`missing_dependency` outcome gives that for free — the branch is not reached.

### Dependencies & integration

`evidence_ref` is dual-purpose in the producer. `_mutation_binding`
(`close_work.py:474-521`) folds it into the equality check against the issued
authority fact *before* the `try` block at `:724`, so an AC10 fixture that
supplies a malformed `evidence_ref` while leaving `_authority`'s issued fact at
`evidence:current` returns `authorization-required`, not
`receipt-evidence-required`. The two must be re-issued in lockstep. That helper
is shared across 17 call sites in the close-work suite, so T3 adds a
receipt-scoped authority helper rather than changing the shared one.

## Tasks

### T0: Register the work and record the decision

**Depends on:** none

**Touches:** workspace.toml, docs/specs/README.md, docs/adr/

**Tests:** Goal-based check. No AC — this is the dispatch precondition.
- `no stub (goal-based check)`
- `workspace-status status` reports this spec in `canonical.ready`.
- `python tools/lint-spec-status.py --root .` passes.

**Approach:**
- Add the spec to `["ini-002".work].queue` and to `docs/specs/README.md`.
- Register the canonical `[backlog].open` entry whose `path` is `notes/follow-ons.md`, without raising the ratcheted legacy-shape count.
- ADR-0103 is written and indexed here, so the spec's `Constrained by:` link resolves before approval.

**Done when:** `canonical.ready` contains `docs/specs/dependency-scoped-completion-receipts/spec.md`.

### T1: Publish the receipt shape and pin its grammars

**Depends on:** T0

**Touches:** contracts/jsonschema/workspace-entry.schema.json, tests/roster/test_dependency_scoped_completion_receipts.py

**Tests:** TDD. Verifies AC1, AC2, AC3.
- Accept/reject table over the schema: need without `receipt`; four-key `receipt`; each single-key omission; a fifth key; each vocabulary value; four rejected `outcome` strings and the empty string.
- Three-way equality read against the lifecycle record's three JSON paths. The engine and producer arms are expected red until T2 and T3.

```python
# tests/roster/test_dependency_scoped_completion_receipts.py  (stub: true)
def test_the_receipt_grammars_equal_the_lifecycle_records(...):  # AC3
    """The published schema's three receipt grammars equal the lifecycle record's."""
    lifecycle = _load(LIFECYCLE_SCHEMA)
    receipt = _load(WORKSPACE_ENTRY_SCHEMA)["$defs"]["localNeed"]["properties"]["receipt"]["properties"]
    assert receipt["delivery_id"]["pattern"] == lifecycle["properties"]["delivery_id"]["pattern"]
    assert receipt["completion_event"]["enum"] == lifecycle["properties"]["completion_event"]["enum"]
    assert receipt["evidence_ref"]["pattern"] == lifecycle["$defs"]["evidenceRef"]["pattern"]
```

**Approach:**
- Add `receipt` to `$defs/localNeed`; add this spec directory to `x-spec`.

**Done when:** AC1–AC3's schema arm is green and the AC3 mutation reddens it.

### T2: Read the receipt at satisfaction time

**Depends on:** T1

**Touches:** packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py, packs/core/.apm/skills/workspace-status/SKILL.md, packages/agentbundle/agentbundle/_data/workspace_status_engine.py, tests/roster/test_dependency_scoped_completion_receipts.py

**Tests:** TDD. Verifies AC4, AC5, AC6, AC7, AC8, AC9, and AC3's engine arm and AC12's second clause.
- One fixture generator, one `keep_membership` flag, per § Construction tests.
- AC7 additionally asserts the citing path is still present across `canonical.ready` and `canonical.blocked`.
- AC9's cross-repository half runs the shipped fixture unchanged.

```python
# tests/roster/test_dependency_scoped_completion_receipts.py  (stub: true)
def test_a_completed_receipt_satisfies_a_pruned_dependency(tmp_path):  # AC4
    """Entry gone and file gone: a valid completed receipt resolves the edge."""
    result = _run_status(_fixture(tmp_path, keep_membership=False, outcome="completed"))
    assert _codes_for(result, DEPENDANT) == set()
```

**Approach:**
- Carry the receipt through the need parser as opaque bounded text; validate only at satisfaction time, at the call site after `:2690`.
- Add `invalid_completion_receipt` to the engine's finding table with its next action, and document it in `workspace-status/SKILL.md` § 1a.
- Run `make build-self` in this task to resync the `_data/` pair.

**Done when:** AC4–AC9 are green and each mutation row below reddens its named criterion.

### T3: Make the producer refuse what the consumer would refuse

**Depends on:** T2

**Touches:** packs/core/.apm/skills/close-work/scripts/close_work.py, packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py, packages/agentbundle/agentbundle/_data/close_work.py

**Tests:** TDD. Verifies AC10 and AC3's producer arm.
- Four refusal cases and one acceptance case, each through a receipt-scoped authority helper whose issued `evidence_ref` matches the value under test.

```python
# packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py  (stub: true)
def test_a_receipt_field_outside_its_grammar_is_refused() -> None:  # AC10
    """An authorized call still refuses a receipt whose field breaks its rule."""
    close_work = _close_work()
    result = _plan_receipt(close_work, completion_event="work-loop:gates-clean")
    assert result.code == "receipt-evidence-required"
```

**Approach:**
- Validate the four fields inside the existing `try`/`except ValueError` block so the refusal code is unchanged, and add the receipt-scoped authority helper described in § Dependencies & integration.
- Rewrite the one shipped call that reaches receipt construction (`test_pause_receipts_and_initiative.py:219-236`) and its `asdict` assertion: `delivery_id` `delivery:wave4`, `completion_event` `work-loop:gates-clean`, and `evidence_ref` `evidence:current` all fail their pinned grammars. The two calls at `:267-291` return `authorization-required` before validation is reached and need no change.
- Run `make build-self` in this task to resync the `_data/` pair.

**Done when:** AC10 is green and `pytest packs/core/tests/skills/close-work/ -q` is green.

### T4: Ship the adopter reference and the release surface

**Depends on:** T3

**Touches:** guides/core/reference/workspace-toml-schema.md, packs/core/.apm/skills/close-work/SKILL.md, packs/core/pack.toml, docs/product/changelog.md

**Tests:** Goal-based check. Verifies AC11 and AC12's first clause.
- `no stub (goal-based check)`
- Literal-presence greps for the receipt example, the finding-code row, and the three `close-work` statements.
- `python3 tools/validate_guides.py`, `tools/check-guide-index.py`, `tools/lint-guide-titles.py`.
- `tests/roster/test_workspace_status_projection.py` passes, which is what proves the new code is documented in both required homes.

**Approach:**
- Document the receipt in the guide's § *Dependencies* beside the cross-repository block, add the finding-code row, and correct § *Compaction* so a receipt-covered `needs` edge no longer blocks entry removal.
- Update `close-work/SKILL.md`'s receipt paragraph; correct the stale deferral slug in the engine's cross-repo comment from `wave6-dependency-scoped-completion-receipts` to `rfc0096-wave7a-ii-completion-receipts`.
- Bump `packs/core/pack.toml`, re-deriving from `origin/main` at that moment, and add the dated `[core]` changelog entry topmost among `[core]` headings.

**Done when:** AC11 and AC12 are green and `make ci` is green.

## Mutation proofs

Every guard names the mutation that must redden it. Observed results are
recorded in [`notes/mutation-proofs.md`](notes/mutation-proofs.md), never here.

| Criterion | Invariant | Mutation | Expected failure |
| --- | --- | --- | --- |
| AC3 | The grammars equal the lifecycle record's | Change one character of the receipt's `evidence_ref` pattern in the schema | The three-way equality assertion fails on `evidence_ref` |
| AC4 | A valid completed receipt satisfies an absent dependency | Delete the satisfaction branch | AC4's fixture reports `missing_dependency` |
| AC5 | A surviving membership wins before the receipt is read | Move the branch above the `structurally_blocked_paths` guard | AC5's fixture reports no finding |
| AC6 | A non-landed outcome still refuses | Accept any vocabulary value as satisfying | AC6's `abandoned` and `superseded` fixtures report no finding |
| AC7a | A receipt missing a field refuses | Skip the required-field check | AC7's omission fixture reports no finding |
| AC7b | A receipt with an extra key refuses | Skip the exact-field-set check | AC7's fifth-key fixture reports no finding |
| AC7c | A receipt breaking a grammar refuses | Skip the three grammar checks | AC7's malformed-`evidence_ref` fixture reports no finding |
| AC7d | An `outcome` outside the vocabulary refuses | Skip the vocabulary check | AC7's `outcome = "Retired"` fixture reports no finding |
| AC7e | A bad receipt does not remove its entry | Move validation into the need parser | AC7's citing path is absent from every canonical collection |
| AC8 | A present artifact never consults the receipt | Validate the receipt before the artifact-existence check | AC8's present-target fixture with a malformed receipt reports `invalid_completion_receipt` |
| AC9 | The two receipt paths stay distinct | Emit `invalid_receipt` from the completion-receipt validator | AC9's assertion that the citing entry's codes exclude `invalid_receipt` fails |
| AC10 | The producer applies the same rules | Remove the four field checks from `plan_completion_receipt` | AC10's four invalid calls return `receipt-write-confirmation-required` |

## Rollout

No migration and no deployed data: no receipt exists anywhere in the repository
today, so the tightened producer validation cannot reject a persisted record.
The schema change is additive — every existing `local` need remains valid.

## Risks

- **The grammar copies drift.** Mitigated by AC3 reading the lifecycle record at
  test time in all three homes.
- **The consumer has no producer until a later wave prunes anything.** Accepted:
  a maintainer can write a receipt by hand today, and Wave 7c's fixtures need
  this contract to exist before they can be real rather than hypothetical.
- **A new untrusted-input parse path.** The receipt is attacker-influenced only
  to the extent `workspace.toml` is, but it is a new parse of unvalidated text
  rendered into agent context. A `security-reviewer` pass on the diff is
  warranted and is recorded here as the routing decision, with
  `path-and-file` and `exceptional-conditions` as the boundary modules.

## Changelog

- 2026-09-02 — Initial plan.
- 2026-09-02 — Rewritten after the first spec-stage review round. Four changes of
  substance, each from a measured finding: receipt validation moves from the need
  parser to satisfaction time, because a parser finding discards the whole citing
  entry; a malformed completion receipt gets its own finding code, because
  broadening `invalid_receipt` would falsify a ticked AC in a frozen spec and
  blunt a shipped oracle; `packages/agentbundle/agentbundle/_data/` is named as a
  third projection home, which makes `make build-self` per-task and obliges an
  `Engine-Change-RFC: 0096` trailer; and registration moves to T0, because
  nothing dispatches from an unregistered spec. The frozen
  `close-work-extraction-and-immediate-disposition` plan is no longer touched —
  it does not contain the fixture text the earlier draft attributed to it.
