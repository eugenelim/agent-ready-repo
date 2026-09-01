# Spec: Completion receipts and cooling scope

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 §7 and §9; `close-work-extraction-and-immediate-disposition` (Shipped and frozen, live dependency — its AC17 owns the receipt contract); `thirty-day-cooling-and-retirement` (Shipped and frozen, live dependency); `status-projection-and-context-exclusion` (Shipped and frozen, live dependency — this spec closes three of its recorded follow-ons)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the completion receipt is validated inline against a field-set constant, matching the sibling coordination receipt, which has no file under `contracts/jsonschema/`. `contracts/jsonschema/workspace-entry.schema.json` pins one `workspace.toml` *entry*; a receipt is not an entry (AC9).
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer whose closed-out work has been compacted away still sees its live
dependants dispatch, and can tell from ordinary orientation which retained
receipts are still doing that job.

`close-work` writes a four-field completion receipt to one named place in one
named shape, and `workspace-status` reads that place. A receipt for a delivery
whose artifact is no longer present, whose outcome is a completion, and which a
live dependency still cites, satisfies a local dependency on that delivery — so
compaction does not strand the work that depended on it. A receipt no live
dependency cites has spent its retention licence and is reported rather than
honoured. A malformed receipt is refused rather than ignored. A receipt never
answers a refusal other than an absent artifact.

Cooling no longer produces two disagreeing answers inside one response. The
initiative whose closeout is projected has its shipped-ness and its queue
emptiness derived from one cooled-exclusion pass, and the affirmative
instruction to invoke `close-work` is withheld whenever the cooled set did not
resolve cleanly, because a skill that distils and disposes must not be
recommended on an incomplete reading.

`repair-plan`, `repair-apply`, `repair-rollback`, and the migration paths are
unaffected by cooling. That is their settled contract, not a pending question.

The acceptance criteria below are the contract. Each names an input and the
exact observable it must produce.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| `decision-record` | Applicable: RFC-0096 §9 scopes Wave 7, and this delivery ships part of it while contradicting §9's stated precondition | [`docs/rfc/0096-portable-delivery-artifact-lifecycle.md`](../../rfc/0096-portable-delivery-artifact-lifecycle.md) § Errata | Approver | A dated, Approver-signed erratum carrying the slice split, the corrected receipt precondition, and the corrected `cooling-brief-child-scope` basis | Closeout verifies all three are recorded and §9's body digest is unchanged |
| `interface-contract` | Applicable, unchanged: [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) | unchanged | Wave 5 | The pinned SHA-256 in AC56 | Closeout verifies the digest |
| `current-architecture` | Applicable: the wave-ownership statement gains 7a's scope and the slice split | [`docs/architecture/work-intake-and-artifact-routing.md`](../../architecture/work-intake-and-artifact-routing.md) | maintainer | All three strings and the negative assertion pinned by `tests/roster/test_wave4_durable_outputs_and_release.py:154-160` survive, and the receipt scope and slice split are stated | Closeout verifies the three pinned strings, the absent string, and the two new statements |
| `user-documentation` (producer instructions) | Applicable: no shipped writer emits the receipt key today, and producer and consumer must agree on one spelling | [`packs/core/.apm/skills/close-work/SKILL.md`](../../../packs/core/.apm/skills/close-work/SKILL.md) | maintainer | The exact key, the four field names, and the `delivery_id` join rule | Closeout verifies the writer's spelling matches what the reader accepts |
| `user-documentation` (finding-code reference) | Applicable: two finding codes are added and the gate reads this file | [`guides/core/reference/workspace-toml-schema.md`](../../../guides/core/reference/workspace-toml-schema.md) | maintainer | A reason and a next action for each new code, the collection's shape, and the trust posture | Closeout verifies both rows, the shape, and the posture statement |
| `user-documentation` (workflow instructions) | Applicable: the agent renders the new block and the closeout gate reads the changed derivation | [`packs/core/.apm/skills/workspace-status/SKILL.md`](../../../packs/core/.apm/skills/workspace-status/SKILL.md) | maintainer | Both code rows, the `receipts` output section, the trust posture, and a closeout-check paragraph consistent with the shared derivation | Closeout verifies all four |
| `capability-evidence` (Wave 6 live dependency) | Applicable: Wave 6 recorded four follow-ons and three close here | [`docs/specs/status-projection-and-context-exclusion/spec.md`](../status-projection-and-context-exclusion/spec.md) `**Status:**` line only | maintainer | The pinned SHA-256 in AC53 over the file with its `**Status:**` line excluded | Closeout verifies the digest and that the pointer resolves |
| `release-history` | Applicable: a shipped Core capability | [`docs/product/changelog.md`](../../product/changelog.md) | maintainer | A topmost dated `[core]` heading equal to `packs/core/pack.toml` | Closeout verifies the three release surfaces agree |
| `runtime-coordination` | Applicable and **changed**: `workspace.toml` gains one additive persistent collection | `workspace.toml` | `close-work` | AC58's byte-identity assertion that `status` and `reconcile` leave `workspace.toml` unmodified | Closeout verifies `workspace-status` writes no receipt outside `repair-apply` |
| `project-knowledge` | Conditional and intentionally unresolved until implementation produces reusable learning | — | `project-knowledge` gate | The gate's receipt, or an explicit not-applicable finding | Closeout requires one of the two |

## Boundaries

### Always do

- Treat every receipt field as bounded untrusted data and revalidate it at the
  seam that acts on it, applying the writer's own rule: a string, non-empty
  after stripping, at most 512 characters, and free of any character whose
  ordinal is below 32 or equal to 127.
- Confine a receipt's `delivery_id` before comparing it with a dependency path,
  by canonicalizing and verifying the prefix rather than rejecting `..` alone.
- Derive the projected initiative's shipped-ness and its queue emptiness from
  one cooled-exclusion pass, so no two consumers in one response can disagree
  about which entries a cooled set removed.
- Consult a receipt only where the dependency's sole refusal is that its target
  artifact is absent.

### Ask first

- Ask before changing the emitted key set of `receipts`, `cooling`, or
  `closeout`, or the subcommands that carry them.
- Ask before letting a receipt satisfy anything other than a local dependency
  whose target artifact is absent.
- Ask before adding a retrieval verb, flag, or subcommand for receipt detail.

### Never do

- Never let a receipt answer a refusal other than an absent target artifact. The
  refusals a receipt may not answer are `invalid_artifact_path`,
  `unreadable_artifact`, `refresh_conflict`, the unknown-brief-child-scope
  refusal, the `defect`-without-closed-membership refusal, and a present
  non-terminal status.
- Never let a receipt whose `outcome` is not a completion satisfy anything.
- Never write, move, rename, or delete a receipt from `workspace-status`.
- Never add a field to the receipt. Its complete shape is the four fields Wave 4
  AC17 fixes, and a fifth would make `workspace.toml` the lifecycle database
  RFC-0096 §10 rejects.
- Never add a `cooling`, `review_on`, `completed_on`, or `lifecycle_record` key
  to `workspace.toml`; Wave 5's AC24 test must keep passing.
- Never add a field to the delivery-lifecycle record, and never recompute a
  review date or re-derive a cooling period.
- Never reuse an existing finding code for a receipt condition.
- Never add a store, resolver, fingerprint helper, dependency, scheduler, or
  background job, and never add a non-stdlib import to
  `workspace_status_engine.py`.
- Never edit a Frozen `docs/specs/*` body, including the three frozen specs this
  one depends on.
- Never classify history or prune an artifact; Wave 7b and Wave 7c own those.

### Definitions this contract uses

- A membership is **live** when its collection is not `work.shipped`,
  `brief_queue.shipped`, or `backlog.closed`, and its owning initiative's status
  is not `closed`. A `backlog.open` membership has no owning initiative and is
  live. This closed set is the one the citation criteria quantify over.
- A receipt's `outcome` is a **completion** when its value is exactly
  `completed`. The other two values the closeout workflow produces,
  `abandoned` and `superseded`, are not completions.
- The **projected initiative** is the lexicographically first initiative whose
  status is `active` or `paused`; it is the only initiative the `closeout` block
  describes.

## Testing Strategy

Every criterion names a concrete input and one of eight observable shapes: a
named finding code at a named JSON path, a field value at a named JSON path, an
enumerated key set over a named path, identity against a named control run, a
pinned SHA-256 digest, a counter comparison against a named control, a
version-equality comparison, or a literal string present or absent in
whitespace-normalized text.

- **Receipt validation, projection, dependency satisfaction, and the closeout
  derivation: TDD.** The fixture tree and the injected instant are arguments, as
  they are in Wave 6's suite.
- **Satisfaction is proved against an explicit control** — the identical fixture
  with the receipt removed. Every satisfaction criterion asserts the dependency
  is blocked in the control run, so a fixture that was already dispatchable
  fails loudly rather than passing vacuously.
- **Read-freeness is proved on the emitted counter, not on a sentinel.** A
  receipt is consulted only when its target artifact is absent, so no body
  exists in the satisfying run to plant a sentinel in. AC21 compares
  `diagnostics.spec_files_read` with a fixture whose dependency is removed, and
  with a control where the target exists and is read.
- **The two closeout consumers are proved to agree by one assertion over both**,
  scoped to the projected initiative, comparing the cooled and uncooled control
  pair rather than asserting the two values are equal.
- **The repair and migration decision is pinned by control runs**, because its
  outcome is "unchanged": each criterion asserts a cooled fixture produces
  output identical to the same fixture with no lifecycle record, so a later
  blanket filter has to change that line and say why.
- **Every non-override rail names its own refusal.** The refusal criteria assert
  the original finding code survives, not that the receipt was ignored.
- **Frozen-body and contract preservation: literal pinned digests**, so each
  check holds after the branch is gone. A merge-base comparison is not used: the
  merge base moves to include this delivery once it lands.

**Stub coverage.** Compiled red stubs: AC1-AC27, AC58, and AC28-AC41 (T2-T8) —
44 criteria. `no stub (mode)`: AC42-AC57 (T8's prose half, T9, T10; goal-based)
and T1, T11 — 16 criteria. Uncovered: none.

## Acceptance Criteria

### The receipt collection

- [ ] **AC1 — A well-formed receipt is projected in `status`.** A
  `workspace.toml` whose top-level `completion_receipts` array holds one table
  with exactly `delivery_id`, `outcome`, `completion_event`, and `evidence_ref`,
  whose `delivery_id` a live entry's `needs` names, puts one entry carrying
  those four values at `receipts.retained` in `status` output.
- [ ] **AC2 — The same receipt is projected in `reconcile`.** The AC1 fixture
  puts the identical entry at `receipts.retained` in `reconcile` output.
- [ ] **AC3 — The `receipts` object's key set is exactly `{retained}`.**
- [ ] **AC4 — The projected receipt carries exactly four keys.** Each entry at
  `receipts.retained` has the key set
  `{delivery_id, outcome, completion_event, evidence_ref}` and no other key.
- [ ] **AC5 — A receipt whose key set differs is refused.** A receipt table with
  any missing or any additional key produces `invalid_completion_receipt` at
  `canonical.findings` and contributes no entry to `receipts.retained`.
- [ ] **AC6 — A receipt field that is not bounded text is refused.** A receipt
  whose any one field is a non-string, is empty after stripping, exceeds 512
  characters, or contains a character whose ordinal is below 32 or equal to 127
  produces `invalid_completion_receipt` at `canonical.findings` and contributes
  no entry to `receipts.retained`.
- [ ] **AC7 — A duplicate `delivery_id` is refused and neither occurrence
  survives.** Two receipts sharing one `delivery_id` produce
  `invalid_completion_receipt` at `canonical.findings`, and
  `receipts.retained` carries no entry for that `delivery_id`.
- [ ] **AC8 — One malformed receipt does not suppress a well-formed sibling.** A
  `completion_receipts` array holding one refused receipt and one well-formed
  cited receipt with a distinct `delivery_id` puts exactly one entry at
  `receipts.retained`, and that entry is the well-formed one.
- [ ] **AC9 — `completion_receipts` is not a membership collection.** A receipt
  table contributes no entry to `canonical.evaluations`, `canonical.ready`,
  `canonical.active`, `canonical.blocked`, or `canonical.legacy_memberships`.
  In the same fixture, a real workspace entry whose `path` equals the receipt's
  `delivery_id` does appear at `canonical.ready`.
- [ ] **AC10 — A `completion_receipts` value that is not a list of tables is
  refused once.** A `completion_receipts` whose value is a string, a table, or a
  list containing a non-table produces exactly one
  `invalid_completion_receipt` at `canonical.findings`, contributes no entry to
  `receipts.retained`, and leaves every other value in the emitted JSON
  identical to the same fixture with the key absent.
- [ ] **AC11 — An empty `completion_receipts` array is not an error.**
  `completion_receipts = []` puts no entry at `receipts.retained` and produces
  no finding.

### The producer's spelling

- [ ] **AC12 — The writer's instructions name the exact key and fields.**
  Whitespace-normalized, `packs/core/.apm/skills/close-work/SKILL.md` contains
  `[[completion_receipts]]` and each of `delivery_id`, `outcome`,
  `completion_event`, and `evidence_ref`.
- [ ] **AC13 — The writer's instructions bind `delivery_id` to the join key.**
  Whitespace-normalized, `packs/core/.apm/skills/close-work/SKILL.md` states
  that for a repository-local delivery, `delivery_id` is the repository-relative
  path of the delivered artifact that a citing entry's `needs` names.

### Dependency scope

- [ ] **AC14 — A cited receipt is in scope.** A receipt whose `delivery_id`
  equals the confined path named by some live entry's `needs` is reported at
  `receipts.retained` with no finding.
- [ ] **AC15 — An uncited receipt is reported, not retained.** A well-formed
  receipt whose `delivery_id` no live entry's `needs` names produces
  `uncited_completion_receipt` at `canonical.findings` and contributes no entry
  to `receipts.retained`.
- [ ] **AC16 — A receipt cited only by a non-live entry is uncited.** A receipt
  whose `delivery_id` is named only by the `needs` of an entry in
  `work.shipped`, `brief_queue.shipped`, `backlog.closed`, or any collection of
  a `closed` initiative produces `uncited_completion_receipt`, and that entry's
  dependency verdict is identical to the same fixture with the receipt removed.
- [ ] **AC17 — A `delivery_id` naming no artifact and no dependency matches
  nothing.** A receipt whose `delivery_id` is `delivery:wave4` leaves every
  local dependency's satisfaction identical to the control run with the receipt
  removed, in a fixture that also carries a live entry whose `needs` names an
  absent artifact at a different path.
- [ ] **AC18 — An escaping `delivery_id` is refused.** A receipt whose
  `delivery_id` fails repository-relative validation, or canonicalizes outside
  the repository root, produces `invalid_completion_receipt` at
  `canonical.findings`.

### Satisfaction

- [ ] **AC19 — A completion receipt satisfies a dependency whose artifact is
  absent.** An entry whose `needs` names a path with no workspace membership and
  no file on disk is at `canonical.ready` when a cited, well-formed receipt with
  `outcome` `completed` names that path, and at `canonical.blocked` in the
  identical fixture with the receipt removed.
- [ ] **AC20 — A non-completion receipt satisfies nothing.** In the AC19
  fixture, a receipt whose `outcome` is `abandoned`, and separately one whose
  `outcome` is `superseded`, leaves the entry at `canonical.blocked` with
  `missing_dependency`, and each is still reported at `receipts.retained`
  without a finding.
- [ ] **AC21 — Satisfaction reads no artifact.**
  `diagnostics.spec_files_read` in the AC19 satisfying run equals its value in
  the same fixture with the dependency removed, and is strictly lower than its
  value in a control where the target exists on disk and is read as an ordinary
  dependency.
- [ ] **AC22 — A receipt does not override an established non-terminal status.**
  An entry whose `needs` names a spec that exists on disk with
  `Status: Implementing` stays at `canonical.blocked` with
  `unsatisfied_dependency`, whatever receipt names that path.
- [ ] **AC23 — A receipt does not override a safety refusal.** For each of
  `invalid_artifact_path`, `unreadable_artifact`, and `refresh_conflict`, an
  entry whose `needs` names a path producing that finding keeps that finding at
  `canonical.findings` when a valid, cited, completion receipt names the same
  path.
- [ ] **AC24 — A receipt does not answer an unknown brief child scope.** A
  `brief` dependency whose path is in the cooled-children set and whose artifact
  is absent stays at `canonical.blocked` with `missing_dependency` when a valid,
  cited, completion receipt names that path.
- [ ] **AC25 — A receipt does not answer a defect without closed membership.** A
  `defect` dependency with no `backlog.closed` membership and an absent artifact
  stays at `canonical.blocked` with `missing_dependency` when a valid, cited,
  completion receipt names its path.
- [ ] **AC58 — Projection writes nothing.** For every fixture in AC1 through
  AC27, `workspace.toml`'s bytes after a `status` run and after a `reconcile`
  run are identical to their value before the run.
- [ ] **AC26 — A cooled dependency's outcome is unchanged.** A dependency whose
  target is named by a `Cooling` lifecycle record is satisfied exactly as Wave 6
  ships it, with and without a receipt naming the same path.
- [ ] **AC27 — The cross-repository path is unchanged.** A `cross-repo`
  dependency's satisfaction is identical with and without a completion receipt
  naming its `containing_brief`.

### Closeout agreement

- [ ] **AC28 — The two closeout consumers agree about the cooled set.** For the
  projected initiative, the set of `work.queue` paths excluded from
  `closeout.all_specs_shipped`'s derivation equals the set excluded from that
  initiative's `initiatives[].queue_empty` derivation, measured as the
  difference between a cooled fixture and the identical fixture with
  `docs/lifecycle/` removed.
- [ ] **AC29 — A cooled queue entry counts toward neither.** An initiative whose
  only `work.queue` entry is named by a `Cooling` lifecycle record reports
  `closeout.all_specs_shipped` `true` and `initiatives[].queue_empty` `true`,
  and reports both `false` in the identical fixture with the lifecycle record
  removed.
- [ ] **AC30 — A cooled active entry counts toward shipped-ness.** An initiative
  whose only `work.active` entry is named by a `Cooling` lifecycle record
  reports `closeout.all_specs_shipped` `true`, and `false` in the identical
  fixture with the lifecycle record removed.
- [ ] **AC31 — An incomplete cooled reading withholds the affirmative
  instruction.** When `closeout.cooling_context_visible` is `true`,
  `closeout.next_action` is not `invoke-close-work` and
  `closeout.closeout_blockers` contains `cooling-context-incomplete`.
- [ ] **AC32 — A clean cooled reading keeps the affirmative instruction.** In
  the AC29 fixture, `closeout.cooling_context_visible` is `false`,
  `closeout.next_action` is `invoke-close-work`, and
  `closeout.closeout_blockers` does not contain `cooling-context-incomplete`.
- [ ] **AC33 — `unshipped-specs` names only unshipped specs.** In the AC29
  fixture, `closeout.closeout_blockers` does not contain `unshipped-specs`.
- [ ] **AC34 — An uncooled sibling still blocks.** An initiative holding one
  cooled and one uncooled `work.queue` entry reports
  `closeout.all_specs_shipped` `false` and `initiatives[].queue_empty` `false`.

### Repair and migration scope

- [ ] **AC35 — `repair-plan` is unaffected by cooling.** A fixture whose
  `work.queue` entry is named by a `Cooling` lifecycle record produces
  `repair-plan` output identical to the same fixture with `docs/lifecycle/`
  removed.
- [ ] **AC36 — `repair-apply` is unaffected by cooling.** In the AC35 fixture,
  `repair-apply` writes the same `workspace.toml` bytes as it writes for the
  same fixture with `docs/lifecycle/` removed.
- [ ] **AC37 — Migration planning is unaffected by cooling.** A
  `repair-plan --migration-selection` invocation over a fixture whose legacy
  entry's artifact is named by a `Cooling` lifecycle record produces output
  identical to the same fixture with `docs/lifecycle/` removed.
- [ ] **AC38 — Migration application is unaffected by cooling.** A
  `repair-apply --migration-selection --operation-id --confirmation-file`
  invocation over the AC37 fixture produces the same result code and the same
  `workspace.toml` bytes as the same fixture with `docs/lifecycle/` removed.
- [ ] **AC39 — Migration rollback is unaffected by cooling.** A
  `repair-rollback --operation-id --confirmation-file` invocation over the AC38
  fixture's post-apply state produces the same result code and the same
  `workspace.toml` bytes as the same fixture with `docs/lifecycle/` removed.
- [ ] **AC40 — The rootless reconciliation call sites stay rootless.**
  `workspace_status.py` calls `run_canonical_reconciliation` with no repository
  root argument at exactly two sites, and neither passes a cooled set.
- [ ] **AC41 — `repair-plan` and `explain` carry no receipts block.** The
  emitted JSON of `repair-plan` and of `explain` has no `receipts` key.

### Surfaces

- [ ] **AC42 — Both new finding codes are documented where the gate looks.**
  `packs/core/.apm/skills/workspace-status/SKILL.md` and
  `guides/core/reference/workspace-toml-schema.md` each carry a row with a
  reason and a next action for `invalid_completion_receipt` and for
  `uncited_completion_receipt`.
- [ ] **AC43 — The receipt collection's shape is documented.**
  Whitespace-normalized, `guides/core/reference/workspace-toml-schema.md`
  contains `[[completion_receipts]]` and all four field names.
- [ ] **AC44 — The skill documents the receipts output section.**
  Whitespace-normalized, `packs/core/.apm/skills/workspace-status/SKILL.md`
  contains `receipts.retained` and states that `close-work` is the only writer.
- [ ] **AC45 — Both documented surfaces state the trust posture.**
  Whitespace-normalized, `packs/core/.apm/skills/workspace-status/SKILL.md` and
  `guides/core/reference/workspace-toml-schema.md` each state that a completion
  receipt is honoured on the authority of repository write access alone and
  warrants spec-level review.
- [ ] **AC46 — The agent-rendered closeout gate matches the shared derivation.**
  Whitespace-normalized, `packs/core/.apm/skills/workspace-status/SKILL.md` does
  not contain `the raw queue emptiness flag is the authoritative check`, and
  states that the queue-emptiness flag excludes cooled entries.
- [ ] **AC47 — The wave-ownership statements survive.** Whitespace-normalized,
  `docs/architecture/work-intake-and-artifact-routing.md` contains `Wave 5 has
  shipped the lifecycle record, review-date, due-state, and retirement engine`,
  `Wave 6 has shipped ordinary-context exclusion`, and `Wave 7 owns historical
  migration and pruning behavior`, and does not contain `Wave 6 and 7 own
  ordinary-context exclusion`.
- [ ] **AC48 — The architecture surface states this delivery's scope and the
  slice split.** Whitespace-normalized,
  `docs/architecture/work-intake-and-artifact-routing.md` contains
  `workspace-status projects the retained completion receipt` and names Wave 7a,
  Wave 7b, and Wave 7c.

### Governance and frozen records

- [ ] **AC49 — RFC-0096 §9's body is unchanged.** The SHA-256 of the bytes of
  `docs/rfc/0096-portable-delivery-artifact-lifecycle.md` from the
  `## 9. Initiative waves` heading up to but excluding the
  `## 10. Risks and revisit conditions` heading is
  `e49f49f12fc7dccff4cd962cecff7be003672283d8a750097a238001b222a45e`.
- [ ] **AC50 — The erratum records the slice split.** The RFC's § Errata
  contains an entry whose date is this delivery's commit date, naming
  `Approver: eugenelim`, stating that Wave 7 ships as Wave 7a, Wave 7b, and
  Wave 7c, and naming this spec as Wave 7a.
- [ ] **AC51 — The erratum corrects §9's receipt precondition.** The same
  erratum states that the delivery-lifecycle record was never the completion
  receipt's source and that a record-schema change is not a precondition for
  projecting the four-field receipt.
- [ ] **AC52 — The erratum corrects the `cooling-brief-child-scope` basis.** The
  same erratum states that a third finding code is admitted by the finding-code
  documentation gate, so the recorded reason that no third code is available
  does not hold.
- [ ] **AC53 — Wave 6's frozen body is untouched.** The SHA-256 of
  `docs/specs/status-projection-and-context-exclusion/spec.md` with every line
  beginning `- **Status:**` removed is
  `1ab7c01e349f4c2d3e4ba37ec6314371e8eb1a889352d87c5fc771b7a28d3cf3`.
- [ ] **AC54 — Wave 6's Status line carries the convention's pointer form.**
  `docs/specs/status-projection-and-context-exclusion/spec.md`'s `**Status:**`
  value names `wave6-dependency-scoped-completion-receipts`,
  `cooling-closeout-eligibility`, and `cooling-repair-migration-scope`, links
  this spec, and states that it is not a supersession.
- [ ] **AC55 — Wave 5's frozen body is untouched.** The SHA-256 of
  `docs/specs/thirty-day-cooling-and-retirement/spec.md` is
  `3255b1a8b12e2cfaeccc5e6c97a7047467e8ca8e001467fdefc6757318d4c95f`.
- [ ] **AC56 — The lifecycle record contract is unchanged.** The SHA-256 of
  `contracts/jsonschema/delivery-lifecycle-record.schema.json` is
  `557e3d60b8fd5647a06fbc2225de51a52cfff1b8777fd3d917e91bcebbe27878`.
- [ ] **AC57 — The release surface agrees.** `packs/core/pack.toml`'s version,
  `packs/core/.claude-plugin/plugin.json`'s `version`, and the topmost dated
  `[core]` changelog heading are one identical value strictly greater than
  `(2, 18, 2)`.

## Follow-ons

Separately scoped work this delivery does not perform. RFC-0096 §9 Wave 7, as
corrected by the erratum AC50 through AC52 require, is the register for all
four.

| Slug | Outcome | Owner |
| --- | --- | --- |
| `cooling-brief-child-scope` | Wave 6's own recorded follow-on, unchanged in scope; see [`status-projection-and-context-exclusion/spec.md`](../status-projection-and-context-exclusion/spec.md) § Follow-ons for its reproduction. Its recorded reason that no third finding code is available does not hold, and the erratum records the correction. | RFC-0096 Wave 7b |
| `cooling-cross-repo-receipt-refusal` | Decide whether a cooled `cross-repo` dependency can be satisfied. AC27 leaves Wave 6's refusal in place: the coordination receipt's evidence is a revision-pinned match carried in the brief body, and the four-field completion receipt carries no revision, so it cannot stand in. | RFC-0096 Wave 7b |
| `rfc0096-wave7b-historical-classification` | Classify the repository's delivery history — every `spec.md` under `docs/specs/`, every `work.shipped` workspace entry, and every `backlog.closed` entry — with proven outputs, dependencies, authority, and disposition, and each ambiguity an owned dated `retain-exception`. Supplies the read-free parent link that closes `cooling-brief-child-scope`. | RFC-0096 Wave 7b |
| `rfc0096-wave7c-pruning` | Prune proven-eligible artifacts under reviewed plans, explicit confirmations, and no bulk deletion. Depends on Wave 7b's classification and on this delivery's receipt projection, which is what preserves a pruned delivery's live dependants. | RFC-0096 Wave 7c |

## Assumptions

- **Technical: the receipt is not the lifecycle record, and `outcome` needs no
  schema change.** `close-work` already constructs the exact four-field
  `CompletionReceipt` with `outcome` as a closeout argument. Wave 6 deferred the
  projection because "the lifecycle record carries no `outcome` field"; the
  record was never the receipt's source, and RFC §6 closes the record's field
  list and excludes requirements from it. (source:
  `packs/core/.apm/skills/close-work/scripts/close_work.py:688-735`; RFC-0096
  §6 lines 184-190.)
- **Technical: no shipped writer emits the receipt key.** `close_work.py`
  contains no write of any kind, `plan_completion_receipt` returns a plan
  requiring confirmation, and `close-work/SKILL.md` names an "established
  compatible surface" without naming a key or a shape. Wave 4 AC17 is
  conditional and fixes no key, so the writer's spelling was never discharged.
  This delivery adds it, which is why AC12 and AC13 exist. (source:
  `close_work.py:688-769`; `close-work/SKILL.md:183-190`;
  `close-work-extraction-and-immediate-disposition/spec.md:457-465`; probe 7 in
  [`notes/probes.md`](notes/probes.md).)
- **Technical: the receipt's four fields are opaque bounded locators, not the
  lifecycle record's typed values.** The shipped Wave 4 tests write
  `delivery_id="delivery:wave4"`, `completion_event="work-loop:gates-clean"`,
  and `evidence_ref="evidence:current"`, none of which match the record's
  `delivery_id` pattern, `completion_event` enum, or `evidenceRef` pattern.
  Validating the projection against those record shapes would refuse what the
  writer produces. (source:
  `packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py:219-238`
  against `contracts/jsonschema/delivery-lifecycle-record.schema.json:13-20,37`.)
- **Technical: the coordination surface is `workspace.toml`.** Wave 4 AC17
  requires "an already established, resolved coordination surface … rather than
  inventing the Wave 5 lifecycle schema"; the shipped tests name that surface
  `runtime-coordination:workspace`; and RFC §7 says closeout "removes the live
  entry and keeps `{delivery_id, outcome, completion_event, evidence_ref}` only
  while a live dependency cites it", and the live entry is a `workspace.toml`
  entry. (source:
  `close-work-extraction-and-immediate-disposition/spec.md:457-465`; RFC-0096
  §7 lines 228-230.)
- **Technical: the reader mirrors the writer's bound rather than tightening it.**
  `close_work._bounded_text` requires a string, non-empty after stripping, at
  most 512 characters, and free of characters whose ordinal is below 32 or equal
  to 127. The projection applies that same rule, so writer and reader cannot
  disagree and no Wave 4 code changes. (source: `close_work.py:28,392-399`.)
- **Technical: only a completion may satisfy.** The ordinary dependency path
  satisfies on a successful terminal status alone — `spec` requires `Shipped`,
  `defect` requires a closed membership with `resolution == "fixed"` — so
  honouring an `abandoned` or `superseded` receipt would unblock work the same
  engine refuses when the artifact is present. `close_work.project_lifecycle`
  fixes the three-value vocabulary. (source:
  `workspace_status_engine.py:1428-1435,2540-2543`; `close_work.py`
  `project_lifecycle`; RFC-0096 §1 line 55.)
- **Technical: an absent dependency target is refused before any terminal-status
  test, and two further refusals follow that helper.**
  `_dependency_metadata_safety_finding` returns one of five findings in a fixed
  order, of which `missing_dependency` is the only one a receipt may answer;
  `_dependency_is_satisfied` then carries the unknown-brief-child-scope refusal
  and the terminal-status refusal after it. Both are refusals a receipt may not
  answer, which is why AC24 and AC22 exist. (source: probes 5 and 8 in
  [`notes/probes.md`](notes/probes.md).)
- **Technical: an unknown top-level `workspace.toml` key is silently ignored
  today.** A `completion_receipts` key produces no finding and no membership
  before this delivery, so the collection is additive but inert until the engine
  reads it, and a malformed receipt would be silently dropped rather than
  refused. (source: probe 1 in [`notes/probes.md`](notes/probes.md).)
- **Technical: a receipt is load-bearing only when the artifact is absent.**
  With no workspace membership, the dependency path builds a probe and reads the
  artifact from disk, so compaction of a workspace entry alone does not strand
  dependants; a deleted artifact does. (source: probe 5 in
  [`notes/probes.md`](notes/probes.md).)
- **Technical: `closeout` describes one initiative.** `_closeout_projection`
  sorts the initiatives whose status is `active` or `paused` by slug and
  projects `active[0]`; `initiatives[].queue_empty` is emitted per initiative.
  The agreement criterion is therefore scoped to that one initiative. (source:
  `workspace_status.py:749-761,793-803`.)
- **Technical: a third finding code is admitted by the documentation gate.** The
  gate asserts `set(documented_findings) >= set(engine._FINDING_NEXT_ACTIONS)`,
  a superset check over the 24 codes currently declared. The gate is scoped to
  finding codes and does not reach `closeout_blockers` members, so
  `cooling-context-incomplete` needs no documentation row. (source:
  `tests/roster/test_workspace_status_projection.py:488-495`.)
- **Technical: the architecture pin is three strings and one negative
  assertion.** `tests/roster/test_wave4_durable_outputs_and_release.py:154-160`
  asserts the Wave 5, Wave 6, and Wave 7 statements are present and that
  `Wave 6 and 7 own ordinary-context exclusion` is absent. This delivery ships
  neither historical classification nor pruning, so the Wave 7 sentence remains
  accurate and no shipped assertion changes. (source: that test.)
- **Technical: Wave 5's `cooling.is_due`, `cooling.load_record`, and the record
  schema stay byte-unchanged.** (source: RFC §9 Wave 7 non-goals; Wave 5 is
  Shipped and frozen.)
- **Technical: no corpus of real receipts exists.** `workspace.toml` carries zero
  `completion_receipts` entries and `docs/lifecycle/` holds only `README.md`, so
  the refusal criteria cannot be calibrated against recorded real input. The
  nearest real corpus is the field values the shipped writer's own tests
  produce, and probe 7 records the per-field accept and reject counts of this
  contract's rules against it. Those counts were taken before approval, so the
  criteria are final at approval. (source: probe 7 in
  [`notes/probes.md`](notes/probes.md).)
- **Process: a shipped spec's body is frozen and its Status field is not.** The
  three frozen specs this delivery depends on receive at most a `**Status:**`
  line change, and each is pinned by a literal digest — Wave 6 by AC53, Wave 5
  by AC55, and Wave 4 by the live assertion at
  `tests/roster/test_status_projection_and_context_exclusion.py:421-423`.
  (source: `docs/CONVENTIONS.md:111-112`.)
- **Process: RFC-0096 is amended by an appended, Approver-signed erratum, not by
  a §9 body edit.** The RFC's own Errata preamble states the body is preserved
  and corrections are appended. Wave 6 edited the §9 body directly in commit
  `20c0ba50e`, which deviated from that rule; this delivery follows the stated
  rule. (source: RFC-0096 lines 359-360; user confirmation 2026-09-01.)
- **Process: a criterion change after sealing is a material amendment.**
  RFC-0099 §7, as recorded in RFC-0096's own Errata, parks delivery, invalidates
  the baseline, and requires reapproval and resealing. No criterion here is
  provisional. (source: RFC-0096 lines 362-370.)
- **Product: a projected receipt may satisfy a dependency gate, and the trust
  posture is recorded.** A receipt is an unverified assertion honoured on the
  authority of repository write access alone — the same posture Wave 6 recorded
  for the lifecycle record. One hand-written `workspace.toml` block can unblock
  queued work whose artifact is absent, so a receipt added by a pull request
  deserves spec-level scrutiny. AC45 puts the posture on both documented
  surfaces. (source: user confirmation 2026-09-01.)
- **Product: Wave 7 ships as three slices.** Wave 7a is this delivery; Wave 7b
  is historical classification; Wave 7c is pruning. RFC §9 calls Wave 7 "a large
  separate release", and no lifecycle record has yet been written in this
  repository. (source: user confirmation 2026-09-01.)
