# Plan: Completion receipts and cooling scope

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/work-intake-and-artifact-routing.md`
  (routing and wave ownership) and `docs/CONVENTIONS.md` (document lifecycle
  classes). Two analogous production implementations: the coordination-receipt
  reader — `_COORDINATION_RECEIPT_FIELDS`, `_validated_receipt_match`,
  `_cross_repo_receipt_satisfied` in
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`
  — which fixes the field-set-constant validation idiom and shows that a
  receipt gets no file under `contracts/jsonschema/`; and Wave 6's cooling
  projection — `_resolve_cooled_state` plus the `cooling` and `closeout` blocks
  in `workspace_status.py` — which fixes the block-projection idiom and the
  `status`/`reconcile`-only mode gate. Their tests are
  `tests/roster/test_status_projection_and_context_exclusion.py` and
  `tools/test_workspace_status_cli.py`. Named uncertainty: the receipt's
  placement inside `_dependency_is_satisfied` is grounded by symbol, not by
  line, because that function moved twice during Wave 6.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit.

## Approach

The engine gains one reader and one decision point; everything else is
plumbing that already exists.

The reader parses `workspace.toml`'s top-level `completion_receipts` array into
a validated mapping from `delivery_id` to a four-field record, mirroring the
coordination-receipt reader's shape: one field-set constant, one per-element
validator, refusal on any deviation.

The decision point is keyed on a **finding code, not on a phase**. Probe 5 in
`notes/probes.md` disconfirmed the phase-shaped rule this plan first carried:
an absent dependency target never reaches the terminal-status test, because
`_dependency_metadata_safety_finding` refuses it first with
`missing_dependency`. That helper returns exactly one of five findings in a
fixed order, and `missing_dependency` is the only one a receipt may answer. So
the receipt is consulted when and only when that helper's returned code is
`missing_dependency`, and the four sibling refusals stand untouched by
construction rather than by a defensive check. This is what makes the spec's
non-override rails structural: there is no branch on which a receipt can
replace an existing verdict.

Two consumers then read that mapping without deciding anything: the `receipts`
block in `status` and `reconcile`, and the citation scan that decides whether a
retained receipt is still in scope.

The cooling work is smaller and separate. `all_specs_shipped` and
`queue_empty` are computed from two separate expressions in
`workspace_status.py` today, which is why Wave 6's repair could filter one and
not the other. They collapse into one derivation that both read, so the
disagreement Wave 6 reverted is no longer expressible. The affirmative
instruction gains one guard on the already-shipped `cooling_context_visible`
flag.

The repair and migration decision produces no behaviour change at all. Its
whole deliverable is a control run that pins the current outcome, so a later
blanket filter has to edit that line and justify it.

The riskiest part is the decision point's placement: a receipt consulted one
step earlier silently converts every "artifact absent" refusal into a
satisfaction, including the safety refusals. T4's tests are written against the
refusals specifically, not against the happy path.

## Constraints

- **RFC-0096 §7** fixes the receipt's four fields and its retention licence
  ("only while a live dependency cites it"); **§9** scopes Wave 7; **§10**
  rejects `workspace.toml` as a lifecycle database, which is why the receipt
  gains no fifth field.
- **`close-work-extraction-and-immediate-disposition` AC17** (Shipped, frozen)
  owns the receipt contract: minimal, dependency-scoped, on an already
  established surface, never inventing the Wave 5 lifecycle schema.
- **`thirty-day-cooling-and-retirement`** (Shipped, frozen) owns
  `cooling.is_due`, `cooling.load_record`, the record schema, and the
  `docs/lifecycle/` single-writer rule. This delivery consumes all four
  unchanged; its AC24 test forbids new cooling keys in `workspace.toml`.
- **`status-projection-and-context-exclusion`** (Shipped, frozen) owns the
  cooled-set resolution, the `cooling` and `closeout` blocks, the mode gate,
  and the read-free metadata rule for a cooled membership.
- **`docs/CONVENTIONS.md`** freezes a shipped spec directory as a unit; the
  three frozen specs above receive at most a `**Status:**` line change.

## Construction tests

Per-task tests carry the criteria. Two cross-cutting items:

**Integration tests:** one CLI-level run per emitting subcommand
(`status`, `reconcile`, `repair-plan`, `explain`) over a single fixture that
carries a valid receipt, a refused receipt, a cooled queue entry, and an
uncooled sibling — added to `tools/test_workspace_status_cli.py`, which is
where the CLI contract's 158 existing tests live. The engine-level suites
cannot catch a block emitted by `_build_json` but dropped by a subcommand's
own builder, which is the defect class Wave 6's AC35 exists for.

**Manual verification:** T11. The receipt is a surface a maintainer invokes,
so a green unit gate is not sufficient evidence.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `decision-record` / RFC-0096 § Errata | T9 | The erratum's dated, signed entry and the §9 body-range digest comparison | Erratum present; §9 body byte-unchanged |
| `interface-contract` / delivery-lifecycle record | T9 | The digest assertion in the new roster suite | Digest equals the value AC40 states |
| `current-architecture` / work-intake routing | T8 | The pinned-pair assertion in `tests/roster/test_wave4_durable_outputs_and_release.py` still passes, plus the new scope sentence | Pinned pair intact; scope sentence present |
| `user-documentation` / workspace-toml-schema reference | T8 | The finding-code documentation gate at `tests/roster/test_workspace_status_projection.py` | Both codes documented with reason and next action |
| `user-documentation` / workspace-status SKILL.md | T8 | Same gate, plus the whitespace-normalized string assertions | Both codes and the `receipts` section documented |
| `capability-evidence` / Wave 6 spec Status line | T9 | Line-level digest comparison against the merge base | Body unchanged; pointer resolves |
| `release-history` / changelog | T10 | The release-surface assertion | Three version surfaces agree |
| `runtime-coordination` / `workspace.toml` | T2, T3 | A search establishing `workspace-status` contains no receipt writer | No new writer exists |
| `project-knowledge` | T11 | The gate's receipt, or an explicit not-applicable finding | One of the two exists |

## Design (LLD)

### Design decisions

- **The receipt lives in `workspace.toml`, not in `docs/lifecycle/`.** Wave 4
  AC17 forbids folding it into the Wave 5 record, and a separate file under
  `docs/lifecycle/` would be the receipt store `close-work`'s own instructions
  forbid. `workspace.toml` is the established coordination surface whose live
  entry the receipt replaces. Rejected alternative: a fenced block in the
  citing artifact — dependency-scoped by construction, but unreadable exactly
  when the artifact is cooled or pruned, which is the case the receipt exists
  for. Traces to: AC1, AC8.
- **`delivery_id` is the join key and needs no companion field.** For a
  repository-local delivery it is the artifact's confined repository-relative
  path; a value that is not one — the shipped writer's `delivery:wave4` — simply
  matches no local dependency. Rejected alternative: a `cited_by` array, which
  would make the receipt five fields and duplicate `needs`. Traces to: AC11,
  AC12.
- **The reader mirrors the writer's bound instead of tightening it.** Wave 4's
  own tests prove the writer emits values that the lifecycle record's patterns
  reject, so validating against those patterns would refuse valid input.
  Traces to: AC4.
- **Two codes, not one.** A malformed receipt and an expired retention licence
  have different remedies — correct the block versus remove it through
  `close-work` — and a shipped consumer routes on the code. Traces to: AC3,
  AC9.

### Data & schema

The collection is a top-level TOML array of tables. No file under
`contracts/jsonschema/` is added: the sibling coordination receipt is validated
by `_COORDINATION_RECEIPT_FIELDS` alone, and a schema file would need a digest
constant and a projection of its own. The validated in-memory form is a mapping
keyed by `delivery_id`, so AC5's duplicate refusal falls out of construction
rather than needing a separate scan. Traces to: AC1-AC7 · contracts: none.

### Behavior & rules

The satisfaction rule has one precondition and one action. Precondition:
`_dependency_metadata_safety_finding` returned `missing_dependency` for this
dependency. Action: if a validated, cited receipt's `delivery_id` resolves to
the same confined path as the dependency, the dependency is satisfied and the
finding is dropped.

That helper's five returns, in its own order, are `invalid_artifact_path`
(unsafe path), `missing_dependency`, `unreadable_artifact`,
`invalid_artifact_path` (invalid provenance parent), and `refresh_conflict`.
AC15 enumerates the three distinct codes among the four a receipt may not
answer; AC14 covers the separate case where the helper returns nothing and the
terminal test refuses instead. Traces to: AC13-AC18.

### Failure, edge cases & resilience

- A `workspace.toml` whose `completion_receipts` value is not a list of tables
  yields one refusal for the collection, not a crash; the rest of
  reconciliation proceeds, matching how Wave 6 treats one bad lifecycle record.
- A receipt validated but uncited is reported and not honoured, so an expired
  licence degrades to visibility rather than to silent authority.
- `_is_bounded_text` does not reject control characters; the new validator adds
  that check itself rather than reusing the helper unchanged, because the
  projected value reaches agent context.

Traces to: AC3-AC6, AC9, AC10.

## Tasks

### T1: The refusal rules' accept and reject counts are recorded against the real corpus

**Depends on:** none

**Verification mode:** goal-based check.

**Tests:**
- `no stub (mode)`. The deliverable is a recorded measurement, not an
  assertion.

**Approach:**
- Enumerate the only real corpus that exists: the field values the shipped
  writer's tests produce, read from
  `packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py`,
  and the zero receipts currently in `workspace.toml`.
- Run the spec's validation rule over that corpus in a throwaway script and
  record accept and reject counts, per field, in `notes/probes.md`.
- If any shipped writer value is rejected, the rule is wrong and the criteria
  change before T2 — not the corpus.

**Done when:** `notes/probes.md` carries the per-field counts and states
whether any shipped writer value is refused.

### T2: A well-formed receipt is projected and a malformed one is refused

**Depends on:** T1

**Verification mode:** TDD.

**Tests:**
- The suite is a new `tests/roster/test_completion_receipts_and_cooling_scope.py`,
  built on the fixture-tree and injected-instant helpers already in
  `tests/roster/test_status_projection_and_context_exclusion.py`; reuse them
  rather than re-authoring a second fixture builder.
- The refusal cases share one parametrized fixture whose only varying part is
  the receipt table, so a validator that refuses everything fails AC6's
  well-formed sibling in the same run.
- One compilable red contract-surface assertion over the emitted
  `receipts.retained` key. `stub: true`.
- The finding-code documentation gate at
  `tests/roster/test_workspace_status_projection.py` reddens as soon as a code
  is declared and not yet documented; expect it red from here until T8.

**Approach:**
- Add the field-set constant and the per-element validator beside the
  coordination-receipt reader, so the two idioms stay adjacent.
- Declare both finding codes in `_FINDING_NEXT_ACTIONS`.
- Emit the block from the shared JSON builder, not from each subcommand.

**Done when:** the new suite's AC1-AC7 and AC12 cases pass, and
`tools/test_workspace_status.py` and `tools/test_workspace_status_cli.py` show
no new failure other than the documentation gate T8 closes.

### T3: A retained receipt is in scope only while a live entry cites it

**Depends on:** T2

**Verification mode:** TDD.

**Tests:**
- The citation scan's input is the parsed membership set, so the test asserts
  over an entry whose `needs` names the delivery — not over raw TOML text,
  which would pass while the scan read the wrong collection.
- AC10's control run is the identical fixture with the receipt removed; assert
  the same dependency verdict in both, so an uncited receipt that quietly
  satisfies is caught here rather than in T4.

**Approach:**
- Derive the cited set from the memberships already parsed for reconciliation;
  add no second walk.
- Confine each `delivery_id` before comparison, reusing the engine's existing
  confinement helper.

**Done when:** AC8-AC12 pass, and AC11's fixture uses the literal
`delivery:wave4` the shipped writer's test produces.

### T4: A receipt satisfies an absent artifact and overrides nothing else

**Depends on:** T3

**Verification mode:** TDD.

**Tests:**
- Three refusal cases first, then the satisfaction case. AC14 pins a spec that
  exists with `Status: Implementing`; AC15 pins a path that produces
  `invalid_artifact_path`; AC18 pins the cross-repository verdict.
- AC16's sentinel is planted in the body of the file at the receipt's
  `delivery_id` and asserted **present** in the control run where the same file
  is an ordinary dependency target, so a fixture that never produced it fails
  loudly.
- AC17 runs the cooled fixture twice, with and without a receipt, and asserts
  identity — this is the criterion that catches a receipt inserted above Wave
  6's cooled short-circuit.

**Approach:**
- Site the receipt consultation where `_dependency_is_satisfied` acts on
  `_dependency_metadata_safety_finding`'s result, gated on that result's code
  being `missing_dependency`. Resolve both anchors by symbol; the surrounding
  line numbers moved twice during Wave 6.
- Change no branch that already returns a verdict.
- Note there are two call sites of that helper inside
  `_dependency_is_satisfied` — the `defect` arm and the general arm. The
  `defect` arm's own refusal is a membership fact, not an artifact fact, so it
  is out of scope; the gate goes on the general arm only, and AC13's fixture
  uses a `spec` dependency.

**Done when:** AC13-AC18 pass and every pre-existing dependency test in
`packs/core/tests/skills/workspace-status/test_workspace_status_engine_autonomous.py`
still passes.

### T5: Only `status` and `reconcile` carry the receipts block

**Depends on:** T2

**Verification mode:** TDD.

**Tests:**
- One predicate over both `repair-plan` and `explain`, following Wave 6's AC35
  note that only the `repair-plan` member can break, because `explain` uses a
  builder this delivery does not touch.

**Approach:**
- Extend the existing mode gate rather than adding a second one.

**Done when:** AC30 passes and Wave 6's AC35 test still passes.

### T6: Shipped-ness and queue-emptiness are one derivation

**Depends on:** none

**Verification mode:** TDD.

**Tests:**
- AC19 is one assertion that compares the two emitted values for the same
  initiative in the same response. Two separate assertions would both pass
  against the defect Wave 6 reverted.
- AC22's fixture makes the cooled reading incomplete by the mechanism Wave 6
  already ships for it — an unreadable lifecycle record — not by monkeypatching
  the flag, which would prove nothing about the real path.
- AC25 carries the uncooled sibling, so an implementation that excludes every
  entry fails.

**Approach:**
- Replace the two expressions in `workspace_status.py` with one shared
  derivation of the cooled-excluded queue and active sets, and read both
  emitted values from it.
- Add the `cooling_context_visible` guard to the affirmative next action and
  the named blocker.

**Done when:** AC19-AC25 pass and `packs/core/tests/skills/close-work/`
still passes, including Wave 5's AC24 workspace-key test.

### T7: The repair and migration paths are pinned as unaffected by cooling

**Depends on:** none

**Verification mode:** TDD.

**Tests:**
- Each of AC26-AC28 is a control-run identity: the same fixture with and
  without `docs/lifecycle/`, asserting equal output. An assertion on the
  presence of a filter would pass against an implementation that added one and
  then ignored it.
- AC29 counts the rootless call sites by parsing `workspace_status.py`, so the
  count is read from the file rather than restated.

**Approach:**
- Add tests only. No production change belongs to this task; if one is needed,
  the decision the spec records is wrong and the spec changes first.

**Done when:** AC26-AC29 pass with no diff outside test files, and each
mutation named in the mutation table reddens its case.

### T8: The two documented surfaces carry both codes and the receipt shape

**Depends on:** T2, T6

**Verification mode:** TDD for the gate, goal-based for the prose.

**Tests:**
- The finding-code gate at `tests/roster/test_workspace_status_projection.py`
  turns green here; it is red from T2.
- AC32-AC35 use the whitespace-normalized comparison idiom already in that
  file, because every target sentence wraps in its source.

**Approach:**
- Add the two rows to `packs/core/.apm/skills/workspace-status/SKILL.md` and
  `guides/core/reference/workspace-toml-schema.md`.
- Add the `receipts` output section to the skill and the collection's shape to
  the reference.
- Add the scope sentence to
  `docs/architecture/work-intake-and-artifact-routing.md` without touching
  either pinned string.

**Done when:** AC31-AC35 pass and
`tests/roster/test_wave4_durable_outputs_and_release.py` still passes.

### T9: The governance surfaces record the slice split without a frozen-body edit

**Depends on:** T8

**Verification mode:** goal-based check.

**Tests:**
- AC36 and AC38 are digest comparisons against the merge base, computed in the
  new roster suite so they hold after the branch is gone. AC38 compares
  line-by-line rather than whole-file, because the Status line does change.
- AC40 restates the contract digest rather than importing it from the frozen
  Wave 6 spec.

**Approach:**
- Append the dated, signed erratum to RFC-0096 § Errata. Do not touch §9.
- Amend only the `**Status:**` line of Wave 6's `spec.md`.

**Done when:** AC36-AC40 pass and `lint-spec-status.py --root .` exits 0.

### T10: The release surface agrees across all three files

**Depends on:** T2-T9

**Verification mode:** goal-based check.

**Tests:**
- AC41 reads all three values and compares them, and parses the floor rather
  than pinning a literal, so a version taken by main mid-review does not
  invalidate the criterion.

**Approach:**
- Re-derive the number from `git show origin/main:packs/core/pack.toml`
  immediately before committing, not now. Main moved twice during this
  delivery's discovery.
- Bump `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json`, add the topmost dated `[core]`
  changelog heading, and regenerate the four engine projections through the
  gate chain rather than by hand.

**Done when:** AC41 passes, `SKIP_SAST=1 make build-check` exits 0 on a clean
`build/` and `dist/`, and the four engine copies are byte-identical.

### T11: A maintainer invoking the CLI sees the projected receipt

**Depends on:** T10

**Verification mode:** visual / manual QA.

**Tests:**
- `no stub (mode)`.

**Approach:**
- In a scratch fixture outside the repository tree, write a `workspace.toml`
  carrying one valid receipt cited by one entry whose target file is absent,
  and one refused receipt.
- Invoke the real CLI's `status` and `reconcile` and record stdout, the exit
  code, and the emitted `receipts` and `canonical.findings` values in
  `notes/manual-qa.md`.
- Invoke `repair-plan` on the same fixture and record that no `receipts` key is
  emitted.

**Done when:** `notes/manual-qa.md` records the observed output of all three
invocations, including exit codes.

## Rollout

Pure-logic and documentation change with one additive persistent
representation. Delivery is a single merge with no flag: a `workspace.toml`
carrying no `completion_receipts` key behaves exactly as it does today, and a
`workspace.toml` carrying one is already valid to every shipped consumer
(probe 1 in `notes/probes.md`), so there is no mixed-version window. Rollback
is a revert; nothing is irreversible, because this delivery adds no writer and
deletes nothing.

## Risks

- **The decision point placed one step too early** converts every
  artifact-absent refusal into a satisfaction, including safety refusals. This
  is the reason T4 leads with three refusal cases and only then tests the
  happy path.
- **The engine has four copies** — the pack source, two projected skill trees,
  and the packaged `_data/` tree. A hand-edited copy passes local tests and
  fails the packaged-runtime pair check, so T10 regenerates through the gate
  chain.
- **`pytest` and `build-check` cannot run concurrently**: `pytest` writes
  `.apm/__pycache__` that `build-check` rejects as unexpected output. T10
  cleans `build/` and `dist/` and runs the two in sequence.
- **A receipt is honoured on repository write access alone.** The spec records
  the posture; the residual is that a pull request adding a receipt block can
  unblock queued work whose artifact is absent, and only spec-level review
  catches it.

## Changelog

- 2026-09-01: initial plan.
