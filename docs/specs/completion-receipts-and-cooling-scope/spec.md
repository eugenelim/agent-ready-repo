# Spec: Completion receipts and cooling scope

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 §7 and §9; `close-work-extraction-and-immediate-disposition` (Shipped and frozen, live dependency — its AC17 owns the receipt contract); `thirty-day-cooling-and-retirement` (Shipped and frozen, live dependency); `status-projection-and-context-exclusion` (Shipped and frozen, live dependency — this spec closes three of its recorded follow-ons)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the completion receipt is validated inline against a field-set constant, matching the sibling coordination receipt, which has no file under `contracts/jsonschema/`
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer whose closed-out work has been compacted away still sees its live
dependants dispatch, and can tell from ordinary orientation which retained
receipts are still doing that job.

`workspace-status` projects the four-field completion receipt that `close-work`
retains on the coordination surface. A receipt for a delivery whose artifact is
no longer present satisfies a live local dependency on it, so compaction does
not strand the work that depended on the compacted delivery. A receipt no live
dependency cites is reported rather than honoured, because its retention
licence has expired. A malformed receipt is refused rather than ignored.

Cooling no longer produces two disagreeing answers inside one response. An
initiative's shipped-ness and its queue emptiness are the same question asked
twice, so they are computed once; and the affirmative instruction to invoke
`close-work` is withheld whenever the cooled set did not resolve cleanly,
because a skill that distils and disposes must not be recommended on an
incomplete reading.

`repair-plan`, `repair-apply`, and the migration paths are unaffected by
cooling. That is their settled contract, not a pending question.

The acceptance criteria below are the contract. Each names an input and the
exact observable it must produce.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| `decision-record` | Applicable: RFC-0096 §9 scopes Wave 7, and this delivery ships part of it | [`docs/rfc/0096-portable-delivery-artifact-lifecycle.md`](../../rfc/0096-portable-delivery-artifact-lifecycle.md) § Errata | Approver | A dated, Approver-signed erratum recording the Wave 7 slice split | Closeout verifies the erratum is appended and §9's body is byte-unchanged |
| `interface-contract` | Applicable, unchanged: [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) | unchanged | Wave 5 | The file's SHA-256 is unchanged by this delivery | Closeout verifies the digest is unchanged; this delivery adds no record field |
| `current-architecture` | Applicable: the Wave 6/7 boundary statement gains 7a's scope | [`docs/architecture/work-intake-and-artifact-routing.md`](../../architecture/work-intake-and-artifact-routing.md) | maintainer | Both strings pinned by `tests/roster/test_wave4_durable_outputs_and_release.py` survive, and the receipt scope is stated | Closeout verifies the pinned pair is intact |
| `user-documentation` (finding-code reference) | Applicable: two finding codes are added and the gate reads this file | [`guides/core/reference/workspace-toml-schema.md`](../../../guides/core/reference/workspace-toml-schema.md) | maintainer | A reason and a next action for each new code, plus the receipt collection's shape | Closeout verifies both rows and the shape statement |
| `user-documentation` (workflow instructions) | Applicable: the agent renders the new block and codes at runtime | [`packs/core/.apm/skills/workspace-status/SKILL.md`](../../../packs/core/.apm/skills/workspace-status/SKILL.md) | maintainer | A reason and a next action for each new code, plus the `receipts` output section | Closeout verifies both rows and the output-section entry |
| `capability-evidence` (Wave 6 live dependency) | Applicable: Wave 6 recorded four follow-ons and three close here | [`docs/specs/status-projection-and-context-exclusion/spec.md`](../status-projection-and-context-exclusion/spec.md) `**Status:**` line only | maintainer | A Status-line pointer to this spec; the frozen body is byte-unchanged | Closeout verifies the body digest is unchanged and the pointer resolves |
| `release-history` | Applicable: a shipped Core capability | [`docs/product/changelog.md`](../../product/changelog.md) | maintainer | A topmost dated `[core]` heading equal to `packs/core/pack.toml` | Closeout verifies the two agree |
| `runtime-coordination` | Applicable, unchanged: `workspace.toml` gains the receipt collection `close-work` already writes | `workspace.toml` | `close-work` | No new writer is added by `workspace-status` | Closeout verifies `workspace-status` writes no receipt |
| `project-knowledge` | Conditional and intentionally unresolved until implementation produces reusable learning | — | `project-knowledge` gate | An explicit `not applicable—no reusable learning` finding, or an accepted gate receipt | Closeout requires one of the two |

## Boundaries

### Always do

- Treat every receipt field as bounded untrusted data and revalidate it at the
  seam that acts on it, using the writer's own rule at
  `close_work._bounded_text`: a string, non-empty after stripping, at most
  `close_work.MAX_TEXT_LENGTH` characters, and free of any character whose
  ordinal is below 32 or equal to 127.
- Confine a receipt's `delivery_id` before comparing it with a dependency path,
  by canonicalizing and verifying the prefix rather than rejecting `..` alone.
- Compute an initiative's shipped-ness and its queue emptiness from one shared
  derivation, so no two consumers in one response can disagree about which
  entries a cooled set removed.
- Consult a receipt only where the dependency's sole refusal is that its target
  artifact is absent. Every other refusal — an unsafe path, an unreadable
  artifact, an invalid provenance parent, a refresh conflict, or a status that
  is present and non-terminal — stands whatever receipt names that path.

### Ask first

- Ask before changing the emitted key set of `receipts`, `cooling`, or
  `closeout`, or the subcommands that carry them.
- Ask before letting a receipt satisfy anything other than a local dependency
  whose target artifact is absent.
- Ask before adding a retrieval verb, flag, or subcommand for receipt detail.

### Never do

- Never let a receipt override a status the ordinary path established. A
  dependency whose artifact exists and is non-terminal stays unsatisfied
  however many receipts name it.
- Never write, move, rename, or delete a receipt from `workspace-status`;
  `close-work` is the only writer, through its already-shipped
  `plan_completion_receipt` and `plan_receipt_removal`.
- Never add a field to the receipt. Its complete shape is the four fields Wave 4
  AC17 fixes, and a fifth would make `workspace.toml` a lifecycle database that
  RFC-0096 §10 rejects.
- Never add a `cooling`, `review_on`, `completed_on`, or `lifecycle_record` key
  to `workspace.toml`; Wave 5's AC24 test must keep passing.
- Never add a field to the delivery-lifecycle record, and never recompute a
  review date or re-derive a cooling period.
- Never reuse an existing finding code for a receipt condition; existing codes
  carry meanings that shipped consumers already act on.
- Never add a store, resolver, fingerprint helper, dependency, scheduler, or
  background job, and never add a non-stdlib import to
  `workspace_status_engine.py`.
- Never edit a Frozen `docs/specs/*` body, including the three frozen specs this
  one depends on.
- Never classify history or prune an artifact; Wave 7b and Wave 7c own those.

## Testing Strategy

Every criterion names a concrete input and one of five observable shapes: a
named finding code at a named JSON path, a field value at a named JSON path,
an enumerated key set over a named path, identity against a named control run,
or a literal string present or absent in whitespace-normalized text.

- **Receipt validation, projection, dependency satisfaction, and the closeout
  derivation: TDD.** The fixture tree and the injected instant are arguments,
  as they are in Wave 6's suite.
- **Satisfaction is proved against an explicit control** — the identical
  fixture with the receipt removed. Every satisfaction criterion asserts the
  dependency is blocked in the control run, so a fixture that was already
  dispatchable fails loudly rather than passing vacuously.
- **The two closeout consumers are proved to agree by a single assertion over
  both**, not by two assertions that happen to match: one predicate compares
  `closeout.all_specs_shipped` with `initiatives[].queue_empty` for the same
  initiative in the same response.
- **The repair and migration decision is pinned by a control run**, because its
  outcome is "unchanged": the criterion asserts a cooled fixture produces the
  identical `repair-plan` output as the same fixture with no lifecycle record,
  so a later blanket filter has to change that line and say why.
- **Negative events name their detection.** The non-override criterion detects
  a wrongly-honoured receipt by asserting the dependency stays blocked with its
  own finding code, not by asserting the receipt was absent.
- **Frozen-body preservation: pinned digest**, so the check holds after the
  branch is gone.

## Acceptance Criteria

### The receipt collection

- [ ] **AC1 — A well-formed receipt is projected.** A `workspace.toml` whose
  top-level `completion_receipts` array holds one table with exactly
  `delivery_id`, `outcome`, `completion_event`, and `evidence_ref` puts one
  entry carrying those four values at `receipts.retained` in `status` output.
- [ ] **AC2 — The projected receipt carries exactly four keys.** Each entry at
  `receipts.retained` has the key set
  `{delivery_id, outcome, completion_event, evidence_ref}` and no other key.
- [ ] **AC3 — A receipt whose key set differs is refused.** A receipt table with
  any missing or any additional key produces `invalid_completion_receipt` at
  `canonical.findings` and contributes no entry to `receipts.retained`.
- [ ] **AC4 — A receipt field that is not bounded text is refused.** A receipt
  whose any one field is a non-string, is empty after stripping, exceeds
  `close_work.MAX_TEXT_LENGTH` characters, or contains a character whose
  ordinal is below 32 or equal to 127 produces `invalid_completion_receipt` at
  `canonical.findings` and contributes no entry to `receipts.retained`.
- [ ] **AC5 — A duplicate `delivery_id` is refused.** Two receipts sharing one
  `delivery_id` produce `invalid_completion_receipt` at `canonical.findings`
  and neither contributes an entry to `receipts.retained`.
- [ ] **AC6 — One malformed receipt does not suppress a well-formed sibling.**
  A `completion_receipts` array holding one refused receipt and one well-formed
  receipt with a distinct `delivery_id` puts exactly one entry at
  `receipts.retained`, and that entry is the well-formed one.
- [ ] **AC7 — `completion_receipts` is not a membership collection.** A receipt
  table contributes no entry to `canonical.ready`, `canonical.active`,
  `canonical.blocked`, or `canonical.legacy_memberships`.

### Dependency scope

- [ ] **AC8 — A cited receipt is in scope.** A receipt whose `delivery_id`
  equals the confined path named by some live entry's `needs` is reported at
  `receipts.retained` with no finding.
- [ ] **AC9 — An uncited receipt is reported, not honoured.** A well-formed
  receipt whose `delivery_id` no live entry's `needs` names produces
  `uncited_completion_receipt` at `canonical.findings`.
- [ ] **AC10 — An uncited receipt satisfies nothing.** In the AC9 fixture, no
  dependency becomes satisfied that is unsatisfied in the identical fixture with
  the receipt removed.
- [ ] **AC11 — A `delivery_id` that is not a confined repository-relative path
  matches no local dependency.** A receipt whose `delivery_id` is
  `delivery:wave4` — the value the shipped Wave 4 test writes — leaves every
  local dependency's satisfaction identical to the control run with the receipt
  removed.
- [ ] **AC12 — An escaping `delivery_id` is refused.** A receipt whose
  `delivery_id` resolves outside the repository root produces
  `invalid_completion_receipt` at `canonical.findings`.

### Satisfaction

- [ ] **AC13 — A receipt satisfies a dependency whose artifact is absent.** An
  entry whose `needs` names a path with no workspace membership and no file on
  disk is at `canonical.ready` when a cited, well-formed receipt names that
  path, and at `canonical.blocked` in the identical fixture with the receipt
  removed.
- [ ] **AC14 — A receipt does not override an established non-terminal status.**
  An entry whose `needs` names a spec that exists on disk with
  `Status: Implementing` stays at `canonical.blocked` with
  `unsatisfied_dependency`, whatever receipt names that path.
- [ ] **AC15 — A receipt does not override a safety refusal.** For each of
  `invalid_artifact_path`, `unreadable_artifact`, and `refresh_conflict`, an
  entry whose `needs` names a path producing that finding keeps that finding at
  `canonical.findings` when a valid, cited receipt names the same path. These
  are the three refusals that `missing_dependency` shares its decision point
  with, so a receipt consulted one branch too early replaces one of them.
- [ ] **AC16 — Satisfaction is read-free.** A sentinel string present only
  inside the body of the file at the receipt's `delivery_id` never appears in
  the emitted JSON of the run that satisfies the dependency, and does appear in
  the control run where the same file is read as an ordinary dependency target.
- [ ] **AC17 — A cooled dependency's outcome is unchanged.** A dependency whose
  target is named by a `Cooling` lifecycle record is satisfied exactly as Wave 6
  ships it, with and without a receipt naming the same path.
- [ ] **AC18 — The cross-repository path is unchanged.** A `cross-repo`
  dependency's satisfaction is identical with and without a completion receipt
  naming its `containing_brief`, because the coordination receipt's revision pin
  has no source in the four-field completion receipt.

### Closeout agreement

- [ ] **AC19 — The two closeout consumers agree.** For every initiative in one
  `status` response, `closeout.all_specs_shipped` is `true` exactly when that
  initiative's `initiatives[].queue_empty` is `true`.
- [ ] **AC20 — A cooled queue entry counts toward neither.** An initiative whose
  only `work.queue` entry is named by a `Cooling` lifecycle record reports
  `closeout.all_specs_shipped` `true` and `initiatives[].queue_empty` `true`,
  and reports both `false` in the identical fixture with the lifecycle record
  removed.
- [ ] **AC21 — A cooled active entry counts toward neither.** An initiative whose
  only `work.active` entry is named by a `Cooling` lifecycle record reports
  `closeout.all_specs_shipped` `true`, and reports `false` in the identical
  fixture with the lifecycle record removed.
- [ ] **AC22 — An incomplete cooled reading withholds the affirmative
  instruction.** When `closeout.cooling_context_visible` is `true`,
  `closeout.next_action` is not `invoke-close-work` and
  `closeout.closeout_blockers` contains `cooling-context-incomplete`.
- [ ] **AC23 — A clean cooled reading keeps the affirmative instruction.** In
  the AC20 fixture, `closeout.cooling_context_visible` is `false`,
  `closeout.next_action` is `invoke-close-work`, and
  `closeout.closeout_blockers` does not contain `cooling-context-incomplete`.
- [ ] **AC24 — `unshipped-specs` names only unshipped specs.** In the AC20
  fixture, `closeout.closeout_blockers` does not contain `unshipped-specs`.
- [ ] **AC25 — An uncooled sibling still blocks.** An initiative holding one
  cooled `work.queue` entry and one uncooled `work.queue` entry reports
  `closeout.all_specs_shipped` `false` and `initiatives[].queue_empty` `false`.

### Repair and migration scope

- [ ] **AC26 — `repair-plan` is unaffected by cooling.** A fixture whose
  `work.queue` entry is named by a `Cooling` lifecycle record produces
  `repair-plan` output identical to the same fixture with `docs/lifecycle/`
  removed.
- [ ] **AC27 — `repair-apply` is unaffected by cooling.** In the AC26 fixture,
  `repair-apply` writes the same `workspace.toml` bytes as it writes for the
  same fixture with `docs/lifecycle/` removed.
- [ ] **AC28 — Migration planning is unaffected by cooling.** A
  `repair-plan --migration-selection` invocation over a fixture whose legacy
  entry's artifact is named by a `Cooling` lifecycle record produces output
  identical to the same fixture with `docs/lifecycle/` removed.
- [ ] **AC29 — The rootless reconciliation call sites stay rootless.**
  `workspace_status.py` calls `run_canonical_reconciliation` with no repository
  root argument at exactly two sites, and neither passes a cooled set.
- [ ] **AC30 — `repair-plan` and `explain` carry no receipts block.** The
  emitted JSON of `repair-plan` and of `explain` has no `receipts` key.

### Surfaces

- [ ] **AC31 — Both new finding codes are documented where the gate looks.**
  `packs/core/.apm/skills/workspace-status/SKILL.md` and
  `guides/core/reference/workspace-toml-schema.md` each carry a row with a
  reason and a next action for `invalid_completion_receipt` and for
  `uncited_completion_receipt`.
- [ ] **AC32 — The receipt collection's shape is documented.**
  Whitespace-normalized, `guides/core/reference/workspace-toml-schema.md`
  contains `[[completion_receipts]]` and names all four field names.
- [ ] **AC33 — The skill documents the receipts output section.**
  Whitespace-normalized,
  `packs/core/.apm/skills/workspace-status/SKILL.md` contains
  `receipts.retained` and states that `close-work` is the only writer.
- [ ] **AC34 — The Wave 6/7 boundary statement keeps its pinned pair.**
  Whitespace-normalized,
  `docs/architecture/work-intake-and-artifact-routing.md` contains
  `Wave 6 has shipped ordinary-context exclusion` and `Wave 7 owns historical
  migration and pruning behavior`.
- [ ] **AC35 — The architecture surface states this delivery's scope.**
  Whitespace-normalized,
  `docs/architecture/work-intake-and-artifact-routing.md` contains
  `workspace-status projects the retained completion receipt`.
- [ ] **AC36 — RFC-0096 §9's body is unchanged.** The bytes of
  `docs/rfc/0096-portable-delivery-artifact-lifecycle.md` from the `## 9.`
  heading to the `## 10.` heading are identical to their value at this
  branch's merge base.
- [ ] **AC37 — The RFC carries a dated, signed erratum for the slice split.**
  `docs/rfc/0096-portable-delivery-artifact-lifecycle.md` § Errata contains an
  entry dated `2026-09-01` naming `Approver: eugenelim` that states Wave 7
  ships as three slices and names this spec as the first.
- [ ] **AC38 — Wave 6's frozen body is untouched.** The SHA-256 of
  `docs/specs/status-projection-and-context-exclusion/spec.md` differs from its
  merge-base value only through its `**Status:**` line; every other line is
  byte-identical.
- [ ] **AC39 — Wave 6's Status line points at this spec.**
  `docs/specs/status-projection-and-context-exclusion/spec.md`'s `**Status:**`
  line names `completion-receipts-and-cooling-scope`.
- [ ] **AC40 — The lifecycle record contract is unchanged.** The SHA-256 of
  `contracts/jsonschema/delivery-lifecycle-record.schema.json` is
  `557e3d60b8fd5647a06fbc2225de51a52cfff1b8777fd3d917e91bcebbe27878`.
- [ ] **AC41 — The release surface agrees.** `packs/core/pack.toml`'s version,
  `packs/core/.claude-plugin/plugin.json`'s `version`, and the topmost dated
  `[core]` changelog heading are one identical value strictly greater than
  `(2, 18, 2)`.

## Follow-ons

Separately scoped work this delivery does not perform. Recorded here rather than
as an inline `(deferred:)` token: `docs/CONVENTIONS.md` reserves that token for
pre-existing frozen specs. RFC-0096 §9 Wave 7, as corrected by the erratum this
delivery appends, is the register for all three.

| Slug | Outcome | Owner |
| --- | --- | --- |
| `cooling-brief-child-scope` | Decide how a cooled child spec whose brief link exists only in the artifact body contributes to its parent brief's `invalid_child_scope` verdict. Wave 6 recorded that closing it needs a readable parent link or a third finding code "which AC46's pinned pair does not admit". That second half is false: AC46 requires a documented row for each of two named codes, and the gate at `tests/roster/test_workspace_status_projection.py:488-494` asserts `set(documented_findings) >= set(engine._FINDING_NEXT_ACTIONS)` — a superset check that admits any documented code. A `child_scope_unknown` code is therefore available, and this delivery adds two codes through that same gate as proof. The remaining open question is attribution breadth, not the code. | RFC-0096 Wave 7b |
| `rfc0096-wave7b-historical-classification` | Classify the repository's delivery history: 423 `spec.md` files under `docs/specs/`, 112 `work.shipped` workspace entries, and 30 `backlog.closed` entries, each with proven outputs, dependencies, authority, and disposition, and each ambiguity an owned dated `retain-exception`. Supplies the read-free parent link that closes `cooling-brief-child-scope` exactly. | RFC-0096 Wave 7b |
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
- **Technical: the receipt's four fields are opaque bounded locators, not the
  lifecycle record's typed values.** The shipped Wave 4 tests write
  `delivery_id="delivery:wave4"`, `completion_event="work-loop:gates-clean"`,
  and `evidence_ref="evidence:current"`, none of which match the record's
  `delivery_id` pattern, `completion_event` enum, or `evidenceRef` pattern.
  Validating the projection against those record shapes would refuse what the
  writer produces. (source:
  `packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py:219-238`
  against `contracts/jsonschema/delivery-lifecycle-record.schema.json:13-20`.)
- **Technical: the coordination surface is `workspace.toml`.** Wave 4 AC17
  requires "an already established, resolved coordination surface … rather than
  inventing the Wave 5 lifecycle schema"; the shipped tests name that surface
  `runtime-coordination:workspace`; and RFC §7 says closeout "removes the live
  entry and keeps `{delivery_id, outcome, completion_event, evidence_ref}` only
  while a live dependency cites it", and the live entry is a `workspace.toml`
  entry. (source:
  `docs/specs/close-work-extraction-and-immediate-disposition/spec.md:457-465`;
  RFC-0096 §7 lines 228-230.)
- **Technical: the reader mirrors the writer's bound rather than tightening it.**
  `close_work._bounded_text` requires a string, non-empty after stripping, at
  most `MAX_TEXT_LENGTH` (512) characters, and free of characters whose ordinal
  is below 32 or equal to 127. The projection applies that same rule, so writer
  and reader cannot disagree and no Wave 4 code changes. (source:
  `packs/core/.apm/skills/close-work/scripts/close_work.py:28,392-399`.)
- **Technical: an unknown top-level `workspace.toml` key is silently ignored
  today.** A `completion_receipts` key produces no finding and no membership
  before this delivery, so the collection is additive but inert until the engine
  reads it, and a malformed receipt would be silently dropped rather than
  refused. (source: probe recorded at
  [`notes/probes.md`](notes/probes.md), 2026-09-01.)
- **Technical: a receipt is load-bearing only when the artifact is absent.**
  With no workspace membership, the dependency path builds a probe and reads the
  artifact from disk, so compaction of a workspace entry alone does not strand
  dependants; a deleted artifact does. (source:
  `workspace_status_engine._dependency_is_satisfied`, the `else` branch that
  constructs a `dependency probe` entry.)
- **Technical: a third finding code is admitted by the documentation gate.** The
  gate asserts `set(documented_findings) >= set(engine._FINDING_NEXT_ACTIONS)`,
  a superset check over the 24 codes currently declared. (source:
  `tests/roster/test_workspace_status_projection.py:488-494`.)
- **Technical: the Wave 6/7 boundary strings stay true.** This delivery ships
  neither historical classification nor pruning, so the pinned sentence
  `Wave 7 owns historical migration and pruning behavior` remains accurate and
  no shipped assertion changes. (source:
  `tests/roster/test_wave4_durable_outputs_and_release.py:156-160`.)
- **Technical: Wave 5's `cooling.is_due`, `cooling.load_record`, and the record
  schema stay byte-unchanged.** This delivery consumes them and adds no field
  and no date logic. (source: RFC §9 Wave 7 non-goals; Wave 5 is Shipped and
  frozen.)
- **Technical: no corpus of real receipts exists.** `workspace.toml` carries
  zero `completion_receipts` entries and `docs/lifecycle/` holds only
  `README.md`, so the refusal criteria AC3 through AC5 and AC12 cannot be
  calibrated against recorded real input. The nearest real corpus is the field
  values the shipped writer's own tests produce — `delivery:wave4`,
  `work-loop:gates-clean`, `evidence:current`, `completed` — and AC11 admits
  exactly those rather than refusing them. The plan's first task runs the
  refusal rules against that corpus and records the accept and reject counts
  before the criteria are final. (source: probe recorded at
  [`notes/probes.md`](notes/probes.md), 2026-09-01.)
- **Process: a shipped spec's body is frozen and its Status field is not.** The
  three frozen specs this delivery depends on receive at most a `**Status:**`
  line change. (source: `docs/CONVENTIONS.md:111-112`.)
- **Process: RFC-0096 is amended by an appended, Approver-signed erratum, not by
  a §9 body edit.** The RFC's own Errata preamble states the body is preserved
  and corrections are appended. Wave 6 edited the §9 body directly in commit
  `20c0ba50e`, which deviated from that rule; this delivery follows the stated
  rule and the erratum records the deviation. (source: RFC-0096 lines 359-360;
  user confirmation 2026-09-01.)
- **Product: a projected receipt may satisfy a dependency gate, and the trust
  posture is recorded.** A receipt is an unverified assertion honoured on the
  authority of repository write access alone — the same posture Wave 6 recorded
  for the lifecycle record. One hand-written `workspace.toml` block can unblock
  queued work whose artifact is absent, so a receipt added by a pull request
  deserves spec-level scrutiny. This is accepted because it is what makes RFC
  §10's "receipts preserve dependencies" real and is the precondition for Wave
  7c pruning. (source: user confirmation 2026-09-01.)
- **Product: Wave 7 ships as three slices.** Wave 7a is this delivery; Wave 7b
  is historical classification; Wave 7c is pruning. RFC §9 calls Wave 7 "a large
  separate release", and the corpus is 423 `spec.md` files with no lifecycle
  record yet written. (source: user confirmation 2026-09-01.)
