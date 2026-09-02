# Plan: Dependency-scoped completion receipts

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** RFC-0096 §6/§7 and [`docs/CONVENTIONS.md`](../../CONVENTIONS.md) § 4 *Contracts* govern the published shape. The cross-repository receipt is the analogous production implementation: `$defs/crossRepoNeed` in `contracts/jsonschema/workspace-entry.schema.json`, validated by `_validated_receipt_match` and `_cross_repo_receipt_satisfied` in `workspace_status_engine.py`, exercised by `packs/core/tests/skills/workspace-status/test_workspace_status_engine_autonomous.py` and `tests/roster/test_workspace_status_projection.py`. Named deviation: that analogue emits `invalid_receipt`, which this delivery must not reuse (ADR-0103 records why it cannot be broadened).

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
  (`self_host.py:88-115`). The resync therefore runs in the same task as each
  runtime edit, not once at the end — otherwise
  `tests/roster/test_workspace_status_projection.py` fails on drift and the
  layer does not leave the repository working. `run_self_host` refuses a dirty
  tree (`self_host.py:1300-1303`) and the bare target passes `--write` without
  `--force`, so the command is `FORCE=1 make build-self`. It rewrites the
  `.agents/` and `.claude/` copies too, which each task's `Touches:` names.
- Those `_data/` pairs sit under the curation guard's `ENGINE_PREFIX` with
  carve-outs only for `build/recipes/` and `/tests/` (`:82-83`), so every commit
  touching either runtime carries `Engine-Change-RFC: 0096`.
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
  `keep_membership` flag; probe A in [`notes/probes.md`](notes/probes.md) owns
  why that flag alone is the discriminator. Writing the two fixtures
  independently is how a pair silently stops discriminating.
- **AC7's entry-survival clause reads `canonical.blocked`.** Probe B in
  [`notes/probes.md`](notes/probes.md) measured the discrimination: a
  satisfaction-time dependency finding leaves the citing path in
  `canonical.blocked`, while a parse-time finding removes it from every
  collection and reports `invalid_entry` against the citing path instead.
- **AC7's non-string fixture is an unquoted TOML date.** `tomllib` yields
  `datetime.date` and `json.dumps` refuses it, so without the parser's value-type
  check the value reaches `Dependency`, the run exits 2 and emits no finding at
  all — which is why AC7 asserts the exit code alongside the code.
- **AC10's cross-repository half reuses the shipped oracle unchanged.** The
  control is `tests/roster/test_status_projection_and_context_exclusion.py`'s
  existing cross-repo fixture, whose comment already records that
  `invalid_receipt` presence is the signal that the read path was entered. No new
  baseline is captured; a captured-after-the-change baseline could not fail.

## Durable-output map

| Spec durable output | Task | Evidence |
| --- | --- | --- |
| Interface contract (`workspace-entry.schema.json`) | T1 | AC1–AC3 green |
| Maintainer procedure — the new code in both required homes | T2 | AC11 green |
| User documentation (`workspace-toml-schema.md`, `close-and-disposition-work.md`) | T4 | AC13 green |
| Maintainer procedure (`close-work/SKILL.md`) | T4 | AC13 green |
| Decision rationale (ADR-0103) | T0 | Accepted and indexed |
| Release history (`docs/product/changelog.md`) | T4 | Dated `[core]` entry at the bumped version |

## Design (LLD)

### Design decisions

The receipt is an optional object on `$defs/localNeed` rather than a third need
variant, so `Dependency.type` keeps exactly two values and no engine branch on
`local` versus `cross-repo` is disturbed.

A malformed completion receipt gets its own finding code,
`invalid_completion_receipt`; ADR-0103 records why `invalid_receipt` cannot be
broadened. Adding a code is an *Ask first* boundary in
`workspace-routing-invariants`, so T2 records that review rather than assuming
it.

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

Validation splits by kind, and the split is what keeps a bad receipt scoped to
one dependency.

**The local need's field check becomes required-plus-optional.**
`_LOCAL_NEED_FIELDS` (`:79`) is compared with `set(raw) != _LOCAL_NEED_FIELDS`
(`:761`) — exact equality — so adding `"receipt"` to that frozenset would make
the receipt *mandatory on every local need* and reject every entry in the
current `workspace.toml`. The check splits into a required set and an allowed
set.

**The parser constrains shape only.** It admits a `receipt` when its key set is
exactly the four names and every value is a `str`, storing validated strings;
anything else becomes a malformed-receipt sentinel. Nothing else reaches
`Dependency`. Every need is serialized on every run —
`canonical_repository_identity` sorts needs by `json.dumps(need, sort_keys=True)`
(`:1598-1601`) — and `tomllib` yields `datetime.date` for an unquoted date, which
`json.dumps` refuses; the `TypeError` maps to `configuration_mismatch` and exit 2,
emptying `ready`, `blocked` and `active`. `Dependency` is `frozen=True`, so a
mapping value would also make it unhashable. The shape check must not *fail* the
entry: the caller returns `None` for the whole entry on any need finding (`:869`)
and `blocks_dependencies` covers only `invalid_entry` and `invalid_artifact_path`
(`:2418-2420`), which would delete the citing entry and leave its own dependants
resolving from the file.

**Satisfaction time decides grammar, vocabulary and the sentinel.** The branch
goes *inside* the existing safety-finding guard, not after it:

```
    safety_finding = _dependency_metadata_safety_finding(...)     # :2686-2688
    if safety_finding is not None:                                # :2689
        if (not matches and dep.receipt is not None
                and safety_finding.code == "missing_dependency"):
            return _completion_receipt_satisfied(dep)
        return False, safety_finding                              # :2690
```

Placing it after `:2690` would be unreachable for the case it serves: that line
returns whenever the artifact is absent, which is AC4's fixture. It must also
stay out of `_dependency_metadata_safety_finding`, which the `defect`-kind path
at `:2658` shares. The `structurally_blocked_paths` guard at `:2604` and the
cooled return at `:2673` both stay ahead of it, which is what AC5 pins. Keeping
it *inside* the guard is what AC9 and AC10 pin: a present artifact makes
`safety_finding` `None`, so the body is never entered.

### Failure, edge cases & resilience

A receipt whose target artifact still exists is never validated and never read:
closeout writes the receipt and a later wave prunes the file, so both existing at
once is the ordinary transitional state. Gating on `missing_dependency` gives
that for free — the branch is not reached. The accepted consequence, which AC10
records: a hand-authored receipt is unchecked in exactly the window where it
could still be repaired cheaply. The producer guard (AC13) covers every receipt
`close-work` plans, and no repository gate validates the real `workspace.toml`
against its schema, so a hand-written one is caught at prune time or not at all.

### Dependencies & integration

`evidence_ref` is dual-purpose in the producer. `_mutation_binding`
(`close_work.py:474-521`) folds it into the equality check against the issued
authority fact *before* the `try` block at `:724`, so an AC12 fixture that
supplies a malformed `evidence_ref` while leaving `_authority`'s issued fact at
`evidence:current` returns `authorization-required`, not
`receipt-evidence-required`. The two must be re-issued in lockstep. That helper
is shared across 20 call sites in the close-work suite, so T3 adds a
receipt-scoped authority helper rather than changing the shared one.

## Tasks

### T0: Register the work and record the decision

**Depends on:** none

**Touches:** workspace.toml, docs/specs/README.md, docs/adr/

**Tests:** Goal-based check. No AC — this is the dispatch precondition.
- `no stub (goal-based check)`
- `workspace-status status` reports this spec in `canonical.ready`.
- `python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .` passes.

**Approach:** already discharged on this branch, before approval, because nothing dispatches from an unregistered spec. The queue entry is in `workspace.toml` under `["ini-002".work].queue`, the canonical `[backlog].open` entry names `notes/follow-ons.md` and left the legacy-shape count at 156 against a 160 ceiling, the index row is in `docs/specs/README.md`, and ADR-0103 is `Accepted` and indexed. Nothing remains; the task is recorded so the dependency order reads correctly.

**Done when:** `canonical.ready` contains `docs/specs/dependency-scoped-completion-receipts/spec.md`.

### T1: Publish the receipt shape and pin its grammars

**Depends on:** T0

**Touches:** contracts/jsonschema/workspace-entry.schema.json, tests/roster/test_workspace_entry_contract.py, tests/roster/test_dependency_scoped_completion_receipts.py

**Tests:** TDD. Verifies AC1, AC2, AC3.
- Accept/reject table over the schema: need without `receipt`; four-key `receipt`; each single-key omission; a fifth key; each vocabulary value; four rejected `outcome` strings and the empty string.
- Three-way equality read against the lifecycle record's three JSON paths. The engine and producer arms are expected red until T2 and T3.

```python
# tests/roster/test_dependency_scoped_completion_receipts.py  (stub: true)
def test_the_receipt_grammars_equal_the_lifecycle_records() -> None:  # AC3
    """The published schema's three receipt grammars equal the lifecycle record's."""
    lifecycle = _load(LIFECYCLE_SCHEMA)
    receipt = _load(WORKSPACE_ENTRY_SCHEMA)["$defs"]["localNeed"]["properties"]["receipt"]["properties"]
    assert receipt["delivery_id"]["pattern"] == lifecycle["properties"]["delivery_id"]["pattern"]
    assert receipt["completion_event"]["enum"] == lifecycle["properties"]["completion_event"]["enum"]
    assert receipt["evidence_ref"]["pattern"] == lifecycle["$defs"]["evidenceRef"]["pattern"]
```

**Approach:**
- Add `receipt` to `$defs/localNeed`; add this spec directory to `x-spec`.
- Extend the exact-equality assertion at `tests/roster/test_workspace_entry_contract.py:164-167` that pins the `x-spec` list — it is equality, not superset, so it reddens otherwise.
- Touch no runtime here. `_WORKSPACE_ENTRY_SCHEMA_DIGEST` must also follow the schema, but it lives in `workspace_status_engine.py` and its three projections, so editing it in T1 would leave the packaged-runtime byte-identity gate red in a task that runs no resync. It moves to T2.

**Done when:** AC1–AC3's schema arm is green, `pytest tests/roster/test_workspace_entry_contract.py -q` is green, and the *schema grammars equal the lifecycle record's* mutation reddens the schema arm.

### T2: Read the receipt at satisfaction time

**Depends on:** T1

**Touches:** packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py, packs/core/.apm/skills/workspace-status/SKILL.md, guides/core/reference/workspace-toml-schema.md (finding-code row only), packages/agentbundle/agentbundle/_data/workspace_status_engine.py, .agents/skills/workspace-status/**, .claude/skills/workspace-status/**, tests/roster/test_dependency_scoped_completion_receipts.py

**Tests:** TDD. Verifies AC4–AC11 and AC3's engine arm.
- One fixture generator, one `keep_membership` flag, per § Construction tests.
- AC7 additionally asserts the citing path is still in `canonical.blocked` and that both invocations exit 0.
- AC10's cross-repository half runs the shipped fixture unchanged.
- AC8 and AC9 use a target whose artifact exists and whose workspace membership is absent, which is the state that reaches the branch.

```python
# tests/roster/test_dependency_scoped_completion_receipts.py  (stub: true)
def test_a_completed_receipt_satisfies_a_pruned_dependency(tmp_path):  # AC4
    """Entry gone and file gone: a valid completed receipt resolves the edge."""
    result = _run_status(_fixture(tmp_path, keep_membership=False, outcome="completed"))
    assert DEPENDANT in {entry["path"] for entry in result["canonical"]["ready"]}
    assert _codes_for(result, DEPENDANT) == set()
```

**Approach:**
- Carry the receipt through the parser as validated strings or a malformed sentinel, per § *Behavior & rules*; decide grammar, vocabulary and the sentinel at satisfaction time.
- Add `invalid_completion_receipt` to the engine's finding table with its next action, and document it in **both** required homes in this task — `workspace-status/SKILL.md` § 1a and `guides/core/reference/workspace-toml-schema.md`. `tests/roster/test_workspace_status_projection.py:488-495` iterates both over the same code set, so splitting them across tasks leaves this task red.
- Record the *Ask first* review `workspace-routing-invariants` requires for a new finding code, and note that its § Canonical findings table does not enumerate this code.
- Update `_WORKSPACE_ENTRY_SCHEMA_DIGEST` (`:1445`) to the digest of the schema T1 changed. It is the adopter-install fallback used when the contract file is absent (`:1574-1582`), currently equal to the file byte-for-byte, and nothing in-repo compares the two, so the drift would be silent.
- Run `FORCE=1 make build-self` in this task to resync the `_data/`, `.agents/` and `.claude/` copies.

**Done when:** AC4–AC11 are green, `_WORKSPACE_ENTRY_SCHEMA_DIGEST` equals the sha256 of the shipped schema (asserted in the new suite), `pytest tests/roster/test_workspace_status_projection.py -q` is green, and each mutation row below reddens its named criterion.

### T3: Make the producer refuse what the consumer would refuse

**Depends on:** T2

**Touches:** packs/core/.apm/skills/close-work/scripts/close_work.py, packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py, packages/agentbundle/agentbundle/_data/close_work.py, .agents/skills/close-work/**, .claude/skills/close-work/**

**Tests:** TDD. Verifies AC12 and AC3's producer arm.
- Four refusal cases and one acceptance case, each through a receipt-scoped authority helper whose issued `evidence_ref` matches the value under test.

```python
# packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py  (stub: true)
def test_a_receipt_field_outside_its_grammar_is_refused() -> None:  # AC12
    """An authorized call still refuses a receipt whose field breaks its rule."""
    close_work = _close_work()
    result = _plan_receipt(close_work, completion_event="work-loop:gates-clean")
    assert result.code == "receipt-evidence-required"
```

**Approach:**
- Validate the four fields inside the existing `try`/`except ValueError` block so the refusal code is unchanged, and add the receipt-scoped authority helper described in § Dependencies & integration.
- Rewrite the one call that constructs a receipt successfully — `:222` and its `asdict` assertion at `:231-236` — whose `delivery_id` `delivery:wave4`, `completion_event` `work-loop:gates-clean` and `evidence_ref` `evidence:current` all fail their pinned grammars. Six other `plan_completion_receipt` call sites need no change: `:237`, `:244`, `:267`, `:277` and `:799` return before construction, and `:811` already asserts `receipt-evidence-required` on an empty `delivery_id`, though its `completion_event` `event:shipped` becomes a second reason.
- Run `FORCE=1 make build-self` in this task to resync the `_data/`, `.agents/` and `.claude/` copies.

**Done when:** AC12 is green and `pytest packs/core/tests/skills/close-work/ -q` is green.

### T4: Ship the adopter reference and the release surface

**Depends on:** T3

**Touches:** guides/core/reference/workspace-toml-schema.md, guides/core/how-to/close-and-disposition-work.md, packs/core/.apm/skills/close-work/SKILL.md, packs/core/pack.toml, docs/product/changelog.md

**Tests:** Goal-based check. Verifies AC13.
- `no stub (goal-based check)`
- Literal-presence greps for the receipt example, the compaction sentence, the how-to's vocabulary sentence, and the three `close-work` statements.
- `python3 tools/validate_guides.py`, `tools/check-guide-index.py`, `tools/lint-guide-titles.py`.

**Approach:**
- Document the receipt in `workspace-toml-schema.md` § *Dependencies* beside the cross-repository block, and correct its § *Compaction* so a receipt-covered `needs` edge no longer blocks entry removal. The finding-code row landed in T2.
- Replace `close-and-disposition-work.md`'s "a short outcome statement" with the closed vocabulary; it currently reproduces the contract ADR-0103 supersedes.
- Update `close-work/SKILL.md`'s receipt paragraph. The engine's stale cross-repo deferral slug is **not** renamed here: that comment describes the still-open cross-repository cooled deferral, retagging it with this delivery's closing slug would be stale on arrival, and the same spelling survives inside a frozen spec directory. It is recorded in `notes/follow-ons.md` instead.
- Bump `packs/core/pack.toml`, re-deriving from `origin/main` at that moment, and add the dated `[core]` changelog entry topmost among `[core]` headings.

**Done when:** AC13 is green, `python3 tools/validate_guides.py` and `python3 tools/check-guide-index.py` pass, and `make ci` is green.

## Mutation proofs

One row per **guard**, not per criterion: several criteria share a guard, and a
row naming a mutation no guard owns cannot kill. Each row states a single edit
and the observation that edit actually produces — three rounds of review found
predicted observations that the mutant does not emit, so a row whose observation
was reasoned rather than derived from the surrounding control flow is a defect.

AC1, AC2, AC11 and AC13 carry no row. AC1 and AC2 are schema verdicts whose
subject *is* the guard, and AC11 and AC13 are documentation checks whose failure
mode is omission rather than logic.

| Guard | Criteria it holds up | Mutation (one edit) | Observation the mutant produces |
| --- | --- | --- | --- |
| The schema's grammars equal the lifecycle record's | AC3 | Change one character of the receipt's `evidence_ref` pattern in `workspace-entry.schema.json` | The equality read fails on the schema arm |
| The engine's grammars equal the lifecycle record's | AC3 | Drop one value from the engine validator's `completion_event` set | The equality read fails on the engine arm |
| The producer's grammars equal the lifecycle record's | AC3 | Loosen the producer's `delivery_id` pattern to `.*` | The equality read fails on the producer arm |
| The local-need field check stays required-plus-optional | AC4, AC7 | Add `"receipt"` to `_LOCAL_NEED_FIELDS` instead of splitting required from allowed | Every receiptless entry in the fixture reports `invalid_entry` and vanishes from all three collections |
| The satisfaction branch exists | AC4 | Delete the branch | AC4's fixture reports `missing_dependency` and leaves `canonical.ready` |
| The branch is reached only after the ordering guards | AC5 | Hoist the receipt check to the top of `_dependency_is_satisfied`, ahead of the `structurally_blocked_paths` guard and unconditional on `matches` | AC5's fixture reports no finding instead of `unsatisfied_dependency` |
| Only `completed` satisfies | AC6 | Treat any vocabulary value as satisfying | AC6's `abandoned` and `superseded` fixtures report no finding |
| The grammars refuse at satisfaction time | AC7 | Remove the three grammar checks from the satisfaction branch | AC7's malformed-`evidence_ref` fixture carries `outcome = "completed"`, so it is satisfied and reports **no finding** rather than `invalid_completion_receipt` |
| The vocabulary refuses at satisfaction time | AC7 | Remove the vocabulary check from the satisfaction branch | AC7's `outcome = "Retired"` fixture falls through to the `completed`-only rule and reports `unsatisfied_dependency` rather than `invalid_completion_receipt` |
| The parser emits a sentinel, not a finding | AC7 | Make the parser emit a finding for a malformed receipt instead of the sentinel | AC7's citing path is absent from every canonical collection and the run reports `invalid_entry` against it |
| The parser constrains value types | AC7 | Remove the parser's value-type check so the raw mapping reaches `Dependency` | AC7's unquoted-date fixture exits 2 with `configuration_mismatch` and emits no `invalid_completion_receipt` at all |
| The receipt is consulted only when the artifact is absent | AC8, AC9 | Move the receipt check to the top of the local-dependency arm, before the metadata probe, gated only on `dep.receipt is not None` | AC8's non-terminal fixture reports no finding instead of `unsatisfied_dependency`, and AC9's fixture reports `invalid_completion_receipt` |
| The two receipt paths stay distinct | AC10 | Emit `invalid_receipt` from the completion-receipt validator | AC10's assertion that the citing entry's codes exclude `invalid_receipt` fails |
| The producer applies the same four rules | AC12 | Remove the four field checks from `plan_completion_receipt` | AC12's four invalid calls return `receipt-write-confirmation-required` |

## Rollout

The schema change is additive: every existing `local` need remains valid, and no
receipt exists anywhere in the repository today, so the tightened producer
validation cannot reject a persisted record.

This release does change every workspace's routing identity, because
`canonical_repository_identity` folds in the byte digest of
`contracts/jsonschema/workspace-entry.schema.json` (`:1731-1734`) and that file
changes. An in-flight legacy migration ledger therefore refuses with
`ledger_changed` and needs a fresh human confirmation. The owner has accepted
that consequence, and no mitigation is attempted: any change to that published
schema has the same effect, and `$defs/localNeed` carries
`additionalProperties: false`, so a new optional need field cannot avoid
changing it. `.workspace-migrations.json` does not exist in this repository, so
nothing here is in flight. It belongs in the changelog entry, not in a guard.

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
- 2026-09-02 — Rewritten after review round 1. Receipt validation moved from the
  need parser to satisfaction time; a new finding code replaced broadening
  `invalid_receipt`; `_data/` was named as a third projection home; registration
  moved to T0.
- 2026-09-02 — Round 4 measured, rather than reasoned about, the premises the
  previous round asserted, and three of them were false. `Dependency` already
  carries three optional fields defaulting to `None`, so a receiptless local need
  already serializes six keys — the identity criterion added in round 3 was
  unsatisfiable, and the convention it rested on would have licensed dropping
  those three and moving every existing identity. That criterion and the whole
  identity decision are withdrawn; § Rollout now records the identity change as
  accepted, since `additionalProperties: false` on the need means no field
  addition can avoid it. The non-string receipt case folded into AC7, whose
  observation is the exit code. Criteria renumbered 15 → 13.
- 2026-09-02 — Rebuilt § Testing Strategy, § Tasks and § Mutation proofs as one
  unit after round 3 reported that spot patches kept leaving stale companion
  statements. The mutation table is now one row per *guard* rather than per
  criterion, because several criteria share a guard and a row naming a mutation
  no guard owns cannot kill. The routing-identity decision taken this round was
  withdrawn the next one; the `_LOCAL_NEED_FIELDS` required/optional split is
  named; the schema-digest edit moved from T1 to T2, where the resync runs.
- 2026-09-02 — Patched after review round 2, which reported that the round-1
  repairs introduced more than they fixed. The repairs were kept; three of their
  consequences were not absorbed and are now: the parser constrains the receipt's
  shape after all, because carrying a raw TOML value onto `Dependency` lets an
  unquoted date fail `json.dumps` and empty the whole projection; the satisfaction
  branch moved *inside* the safety-finding guard, because after `:2690` it is
  unreachable for the absent-artifact case it exists to serve; and AC5's mutation
  was replaced, because the old one was skipped by the branch's own `not matches`
  gate and so could never redden it.
