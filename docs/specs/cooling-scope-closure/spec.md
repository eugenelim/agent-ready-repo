# Spec: Cooling scope closure

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 §7 and §9; `status-projection-and-context-exclusion` (Shipped and frozen, live dependency — this spec closes two of its recorded follow-ons); `thirty-day-cooling-and-retirement` (Shipped and frozen, live dependency)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — this delivery adds no interface surface and no finding code
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer whose initiative has fully cooled reaches closeout instead of
reading `unshipped-specs` forever, and never sees two answers to the same
question inside one response.

The initiative whose closeout is projected has its shipped-ness and its queue
emptiness derived from one cooled-exclusion pass, so the two cannot disagree
about which entries a cooled set removed. The affirmative instruction to invoke
`close-work` is withheld whenever the cooled set did not resolve cleanly,
because a skill that distils and disposes must not be recommended on an
incomplete reading. The agent-rendered closeout gate reads the same derivation
the JSON does.

`repair-plan`, `repair-apply`, `repair-rollback`, and the migration planning,
application, and rollback paths are unaffected by cooling. That is their settled
contract, not a pending question, and the two reconciliation call sites that
receive no repository root stay that way.

This delivery adds no finding code, no persistent representation, and no
projected block. It changes two derivations and pins one decision.

The acceptance criteria below are the contract. Each names an input and the
exact observable it must produce.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| `decision-record` | Applicable: RFC-0096 §9 scopes Wave 7 and this delivery ships the first slice of it | [`docs/rfc/0096-portable-delivery-artifact-lifecycle.md`](../../rfc/0096-portable-delivery-artifact-lifecycle.md) § Errata | Approver | A dated, Approver-signed erratum carrying the four-slice split and the corrected `cooling-brief-child-scope` basis | Closeout verifies both are recorded and §9's body digest is unchanged |
| `current-architecture` | Applicable: the wave-ownership statement gains the slice split | [`docs/architecture/work-intake-and-artifact-routing.md`](../../architecture/work-intake-and-artifact-routing.md) | maintainer | The three statements and the negative assertion pinned by `tests/roster/test_wave4_durable_outputs_and_release.py:154-160` survive, and the split is stated | Closeout verifies the three strings, the absent string, and the split |
| `user-documentation` (reference) | Applicable: the closeout derivation a reader relies on changes | [`guides/core/reference/work-intake-routing-and-lifecycle.md`](../../../guides/core/reference/work-intake-routing-and-lifecycle.md) | maintainer | The statement that a cooled entry counts toward neither closeout consumer | Closeout verifies the statement |
| `user-documentation` (workflow instructions) | Applicable: the agent-rendered closeout gate reads the changed derivation | [`packs/core/.apm/skills/workspace-status/SKILL.md`](../../../packs/core/.apm/skills/workspace-status/SKILL.md) | maintainer | A closeout-check paragraph consistent with the shared derivation, with the raw-queue-emptiness rationale removed | Closeout verifies both halves |
| `capability-evidence` (Wave 6 live dependency) | Applicable: Wave 6 recorded four follow-ons and two close here | [`docs/specs/status-projection-and-context-exclusion/spec.md`](../status-projection-and-context-exclusion/spec.md) `**Status:**` block only | maintainer | The pinned SHA-256 in AC27 over the file with its `**Status:**` block excluded | Closeout verifies the digest and that the pointer resolves |
| `release-history` | Applicable: a shipped Core capability | [`docs/product/changelog.md`](../../product/changelog.md) | maintainer | A topmost dated `[core]` heading equal to `packs/core/pack.toml` | Closeout verifies the three release surfaces agree |
| `project-knowledge` | Conditional and intentionally unresolved until implementation produces reusable learning | — | `project-knowledge` gate | The gate's receipt, or an explicit not-applicable finding | Closeout requires one of the two |

## Boundaries

### Always do

- Derive the projected initiative's shipped-ness and its queue emptiness from
  one cooled-exclusion pass, so no two consumers in one response can disagree
  about which entries a cooled set removed.
- Answer dueness by calling Wave 5's `cooling.is_due(record, moment)`.
- Withhold the affirmative closeout instruction whenever the cooled set did not
  resolve cleanly.

### Ask first

- Ask before changing the emitted key set of `closeout` or `cooling`, or the
  subcommands that carry them.
- Ask before changing what `initiatives[].queue_empty` counts beyond the cooled
  exclusion this delivery adds.
- Ask before letting cooling constrain any repair or migration path.

### Never do

- Never add a finding code, a projected block, or a persistent representation.
  This delivery adds none of the three.
- Never let cooling change the output of `repair-plan`, `repair-apply`,
  `repair-rollback`, or any migration path.
- Never pass a repository root or a cooled set to the two reconciliation call
  sites that receive neither today.
- Never add a `cooling`, `review_on`, `completed_on`, or `lifecycle_record` key
  to `workspace.toml`; Wave 5's AC24 test must keep passing.
- Never recompute a review date, re-derive a cooling period, or change the
  delivery-lifecycle record schema.
- Never write, move, rename, or delete anything under `docs/lifecycle/`.
- Never edit a Frozen `docs/specs/*` body, including the two frozen specs this
  one depends on.
- Never open the `spec.md` or `plan.md` of a cooled artifact during `status`,
  `reconcile`, `explain`, or the MCP status tool.
- Never classify history, prune an artifact, or project a completion receipt;
  Wave 7a-ii, Wave 7b, and Wave 7c own those.

### Definitions this contract uses

- The **projected initiative** is the lexicographically first initiative whose
  status is `active` or `paused`; it is the only initiative the `closeout` block
  describes.
- `initiatives[]` carries an entry only for an initiative whose status is
  `active`. Where the projected initiative is `paused`, it has no
  `initiatives[]` entry and no `queue_empty` value, which is why AC3 and AC8
  are separate criteria.

## Testing Strategy

Every criterion names a concrete input and one of five observable shapes: a
field value at a named JSON path, byte identity against a named control run,
a pinned SHA-256 digest, a version-equality comparison, or a literal string
present or absent in whitespace-normalized text.

- **The shared derivation: TDD.** The fixture tree and the injected instant are
  arguments, as they are in Wave 6's suite.
- **The agreement criterion compares direction, not equality.**
  `all_specs_shipped` is derived over queue and active while `queue_empty` is
  derived over queue alone, so the two legitimately differ. AC3 asserts that
  both move in the same direction between a cooled fixture and the identical
  fixture with `docs/lifecycle/` removed, which is the only shape readable from
  two booleans.
- **The repair and migration decision is pinned by control-run identity**, so a
  later blanket filter has to change those lines and say why.
- **Preservation criteria carry a mutation, not a red stub.** AC4, AC12-AC21,
  AC24, AC27, AC29, and AC30 assert that something already true stays true; each
  is green before the change by construction, and the plan's mutation table
  names the edit that reddens it. Which criteria those are was decided by
  running every stub, not by reasoning about it.
- **Frozen-body and contract preservation: literal pinned digests**, so each
  check holds after the branch is gone. A merge-base comparison is not used: the
  merge base moves to include this delivery once it lands.

**Stub coverage**, measured against the unchanged tree rather than asserted.
Compiled red stubs, 12: AC1, AC2, AC3, AC5, AC6, AC7, AC8, AC9, AC10, AC11,
AC22, AC23. Preservation with a mutation row, 15: AC4, AC12-AC21, AC24, AC27,
AC29, AC30. `no stub (mode)`, 4: AC25, AC26, AC28, AC31. Total 31; uncovered
none. AC4 and AC21 were drafted as red stubs and moved to preservation because
the stub run showed both green on the unchanged tree, and AC3's first stub
passed vacuously — `False == False` — until it was strengthened to require both
values to move.

## Acceptance Criteria

### The shared cooled-exclusion derivation

- [ ] **AC1 — A cooled queue entry counts toward neither consumer.** An
  initiative whose only `work.queue` entry is named by a `Cooling` lifecycle
  record reports `closeout.all_specs_shipped` `true` and that initiative's
  `initiatives[].queue_empty` `true`, and reports both `false` in the identical
  fixture with `docs/lifecycle/` removed.
- [ ] **AC2 — A cooled active entry counts toward shipped-ness.** An initiative
  whose only `work.active` entry is named by a `Cooling` lifecycle record
  reports `closeout.all_specs_shipped` `true`, and `false` in the identical
  fixture with `docs/lifecycle/` removed.
- [ ] **AC3 — Both consumers move together.** For the projected initiative,
  identified by its slug, `closeout.all_specs_shipped` and that initiative's
  `initiatives[].queue_empty` **both** differ between the AC1 cooled fixture and
  the identical fixture with `docs/lifecycle/` removed.
- [ ] **AC4 — An uncooled sibling still blocks.** An initiative holding one
  cooled and one uncooled `work.queue` entry reports
  `closeout.all_specs_shipped` `false` and `initiatives[].queue_empty` `false`.
- [ ] **AC5 — `unshipped-specs` names only unshipped specs.** In the AC1
  fixture, `closeout.closeout_blockers` does not contain `unshipped-specs`.
- [ ] **AC6 — An incomplete cooled reading withholds the affirmative
  instruction.** In a fixture whose `docs/lifecycle/` holds one record that
  cannot be read, `closeout.cooling_context_visible` is `true`,
  `closeout.next_action` is not `invoke-close-work`, and
  `closeout.closeout_blockers` contains `cooling-context-incomplete`.
- [ ] **AC7 — A clean cooled reading keeps the affirmative instruction.** In the
  AC1 fixture, `closeout.cooling_context_visible` is `false`,
  `closeout.next_action` is `invoke-close-work`, and
  `closeout.closeout_blockers` does not contain `cooling-context-incomplete`.
- [ ] **AC8 — A paused projected initiative emits closeout without
  `queue_empty`.** Where the projected initiative's status is `paused`, the
  `closeout` block is present with `paused` `true` and `next_action`
  `resume-or-keep-paused`, and `initiatives[]` carries
  no entry for that initiative.

### The retired Wave 6 pin

- [ ] **AC9 — Wave 6's residual assertion is replaced, not deleted.**
  `tests/roster/test_status_projection_and_context_exclusion.py` no longer
  asserts `all_specs_shipped is False` for a fully cooled initiative, does
  define a test asserting `all_specs_shipped is True` and no `unshipped-specs`
  blocker for that same fixture, and its other test functions are unchanged.

### The agent-rendered closeout gate

- [ ] **AC10 — The skill's closeout gate matches the shared derivation.**
  Whitespace-normalized, `packs/core/.apm/skills/workspace-status/SKILL.md`
  states that the queue-emptiness flag excludes entries named by a lifecycle
  record.
- [ ] **AC11 — The raw-queue-emptiness rationale is gone.**
  Whitespace-normalized, `packs/core/.apm/skills/workspace-status/SKILL.md` does
  not contain `the raw queue emptiness flag is the authoritative check`.

### Repair and migration scope

- [ ] **AC12 — `repair-plan` is unaffected by cooling.** A fixture whose
  `work.queue` entry is named by a `Cooling` lifecycle record produces
  `repair-plan` output identical to the same fixture with `docs/lifecycle/`
  removed.
- [ ] **AC13 — `repair-apply` is unaffected by cooling.** In the AC12 fixture,
  `repair-apply` writes the same `workspace.toml` bytes as it writes for the
  same fixture with `docs/lifecycle/` removed.
- [ ] **AC14 — Migration planning is unaffected by cooling.** A
  `repair-plan --migration-selection` invocation over a fixture whose legacy
  entry's artifact is named by a `Cooling` lifecycle record produces output
  identical to the same fixture with `docs/lifecycle/` removed.
- [ ] **AC15 — Migration application is unaffected by cooling.** A
  `repair-apply --migration-selection --operation-id --confirmation-file`
  invocation over the AC14 fixture produces the same result code and the same
  `workspace.toml` bytes as the same fixture with `docs/lifecycle/` removed.
- [ ] **AC16 — Migration rollback is unaffected by cooling.** A
  `repair-rollback --operation-id --confirmation-file` invocation over the AC15
  fixture's post-apply state produces the same result code and the same
  `workspace.toml` bytes as the same fixture with `docs/lifecycle/` removed.
- [ ] **AC17 — The rootless reconciliation call sites stay rootless.**
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` calls
  `run_canonical_reconciliation` with no repository root argument at exactly two
  sites.
- [ ] **AC18 — Neither rootless call site receives a cooled set.** Neither of
  AC17's two sites passes a second or third positional argument and neither
  passes a `cooled` keyword argument.
- [ ] **AC19 — Wave 5's cooling module is byte-unchanged.** The SHA-256 of
  `packs/core/.apm/skills/close-work/scripts/cooling.py` is unchanged by this
  delivery.
- [ ] **AC20 — The lifecycle record contract is unchanged.** The SHA-256 of
  `contracts/jsonschema/delivery-lifecycle-record.schema.json` is
  `557e3d60b8fd5647a06fbc2225de51a52cfff1b8777fd3d917e91bcebbe27878`.

### Surfaces

- [ ] **AC21 — The wave-ownership statements survive.** Whitespace-normalized,
  `docs/architecture/work-intake-and-artifact-routing.md` contains `Wave 5 has
  shipped the lifecycle record, review-date, due-state, and retirement engine`,
  `Wave 6 has shipped ordinary-context exclusion`, and `Wave 7 owns historical
  migration and pruning behavior`, and does not contain `Wave 6 and 7 own
  ordinary-context exclusion`.
- [ ] **AC22 — The architecture surface states the slice split.**
  Whitespace-normalized, `docs/architecture/work-intake-and-artifact-routing.md`
  names Wave 7a-i, Wave 7a-ii, Wave 7b, and Wave 7c.
- [ ] **AC23 — The reference guide states the closeout derivation.**
  Whitespace-normalized,
  `guides/core/reference/work-intake-routing-and-lifecycle.md` states that an
  entry named by a lifecycle record counts toward neither closeout consumer.

### Governance and frozen records

- [ ] **AC24 — RFC-0096 §9's body is unchanged.** The SHA-256 of the bytes of
  `docs/rfc/0096-portable-delivery-artifact-lifecycle.md` from the
  `## 9. Initiative waves` heading up to but excluding the
  `## 10. Risks and revisit conditions` heading is
  `e49f49f12fc7dccff4cd962cecff7be003672283d8a750097a238001b222a45e`.
- [ ] **AC25 — The erratum records the four-slice split.** The RFC's § Errata
  contains an entry whose date is this delivery's commit date, naming
  `Approver: eugenelim`, stating that Wave 7 ships as Wave 7a-i, Wave 7a-ii,
  Wave 7b, and Wave 7c, and naming this spec as Wave 7a-i.
- [ ] **AC26 — The erratum corrects the `cooling-brief-child-scope` basis.** The
  same erratum states that Wave 6's `cooling-brief-child-scope` entry
  misattributes its constraint to AC46's pinned pair, and that the finding-code
  documentation gate is a superset check admitting any documented code.
- [ ] **AC27 — Wave 6's frozen body is untouched.** The SHA-256 of
  `docs/specs/status-projection-and-context-exclusion/spec.md` with its
  `**Status:**` block removed — the `- **Status:**` line plus every following
  line up to but excluding the next line beginning `- **` — is
  `1ab7c01e349f4c2d3e4ba37ec6314371e8eb1a889352d87c5fc771b7a28d3cf3`.
- [ ] **AC28 — Wave 6's Status block carries the convention's pointer form.**
  `docs/specs/status-projection-and-context-exclusion/spec.md`'s `**Status:**`
  block names `cooling-closeout-eligibility` and
  `cooling-repair-migration-scope`, links this spec, and states that it is not a
  supersession.
- [ ] **AC29 — Wave 5's frozen body is untouched.** The SHA-256 of
  `docs/specs/thirty-day-cooling-and-retirement/spec.md` is
  `3255b1a8b12e2cfaeccc5e6c97a7047467e8ca8e001467fdefc6757318d4c95f`.
- [ ] **AC30 — Wave 6's frozen plan is untouched.** The SHA-256 of
  `docs/specs/status-projection-and-context-exclusion/plan.md` is unchanged by
  this delivery.
- [ ] **AC31 — The release surface agrees.** `packs/core/pack.toml`'s version,
  `packs/core/.claude-plugin/plugin.json`'s `version`, and the topmost dated
  `[core]` changelog heading are one identical value strictly greater than
  `(2, 18, 2)`.

## Follow-ons

Separately scoped work this delivery does not perform. RFC-0096 §9 Wave 7, as
corrected by the erratum AC25 and AC26 require, is the register for all four.

| Slug | Outcome | Owner |
| --- | --- | --- |
| `rfc0096-wave7a-ii-completion-receipts` | Project the dependency-scoped four-field completion receipt from its coordination surface, including the producer's spelling in `close-work`'s instructions, the satisfaction rule for an absent artifact, and the decision whether `completion_event` and `evidence_ref` are pinned to the grammars the lifecycle record already publishes. | RFC-0096 Wave 7a-ii |
| `cooling-brief-child-scope` | Wave 6's own recorded follow-on, unchanged in scope; see [`status-projection-and-context-exclusion/spec.md`](../status-projection-and-context-exclusion/spec.md) § Follow-ons for its reproduction. The erratum corrects its recorded basis. | RFC-0096 Wave 7b |
| `rfc0096-wave7b-historical-classification` | Classify the repository's delivery history with proven outputs, dependencies, authority, and disposition, and each ambiguity an owned dated `retain-exception`. Supplies the read-free parent link that closes `cooling-brief-child-scope`. | RFC-0096 Wave 7b |
| `rfc0096-wave7c-pruning` | Prune proven-eligible artifacts under reviewed plans, explicit confirmations, and no bulk deletion. Must remove a pruned artifact's workspace entry as well as its file: a surviving entry refuses at `structurally_blocked_paths` before any receipt is consulted. | RFC-0096 Wave 7c |

## Assumptions

- **Technical: the two consumers are derived over different lists and are not
  meant to be equal.** `all_specs_shipped` is `not (work.queue or work.active)`
  and `queue_empty` is `len(work.queue) == 0`, so an initiative with an empty
  queue and one active entry legitimately reports them differently. Wave 6's
  follow-on requires the two to agree about the cooled set, not to hold the same
  value, which is why AC3 compares direction. (source:
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py:761,802`;
  `docs/specs/status-projection-and-context-exclusion/spec.md:176`.)
- **Technical: `closeout` describes one initiative and `initiatives[]` carries
  only active ones.** `_closeout_projection` sorts the initiatives whose status
  is `active` or `paused` by slug and projects the first; `initiatives[]` skips
  every non-`active` initiative. A paused projection therefore has no
  `queue_empty`, which AC8 pins separately. (source:
  `workspace_status.py:749-759,793-795`.)
- **Technical: the affirmative instruction is gated on an already-shipped
  flag.** Wave 6 emits `closeout.cooling_context_visible`, `false` only when the
  cooled set resolved cleanly. Gating on it needs no new field and answers the
  objection that reverted Wave 6's repair — an unverified lifecycle record must
  not drive an affirmative recommendation to run a skill that distils and
  disposes. (source: `docs/specs/status-projection-and-context-exclusion/spec.md`
  AC33; `packs/core/.apm/skills/workspace-status/SKILL.md` § closeout.)
- **Technical: a Wave 6 roster assertion pins the inverse of AC1 and AC5.**
  `tests/roster/test_status_projection_and_context_exclusion.py`'s
  `test_a_fully_cooled_initiative_still_reports_unshipped_specs` asserts
  `all_specs_shipped is False` and `"unshipped-specs" in closeout_blockers` for a
  fully cooled initiative, deliberately, as Wave 6's recorded known starting
  state. AC9 replaces it rather than deleting it. (source: that test.)
- **Technical: cooling must not constrain repair or migration.** Those verbs are
  explicitly invoked and mutating rather than ordinary orientation, and their
  artifact reads are pre-mutation revalidation that the conventions forbid
  cutting. Wave 6 already decided the adjacent question the same way: a
  `legacy_entry` finding still names a cooled path, because the entry's shape is
  owed repair whether or not its artifact cooled. (source:
  `docs/specs/status-projection-and-context-exclusion/spec.md` AC20 and
  `notes/repair-plan.md` § Q16.)
- **Technical: the two rootless call sites are inside one helper reached by two
  paths.** Both are inside `_migration_rollback_workspace_bytes`, which the
  migration apply path and the migration rollback path both call, so AC15 and
  AC16 exercise them and AC17 and AC18 pin their shape. Giving them a repository
  root would supply a cooled set they must then ignore. (source:
  `workspace_status.py:1692,1727,1931,2061`.)
- **Technical: a pruned artifact whose entry survives never reaches the
  receipt.** A live membership with an absent artifact raises `missing_artifact`
  in `_structural_findings`, which puts the path in
  `structurally_blocked_paths`, and `_dependency_is_satisfied` refuses there
  before the absent-target refusal. This is why the Wave 7c follow-on row
  carries the obligation to remove the entry as well as the file. (source: probe
  1 in [`notes/probes.md`](notes/probes.md).)
- **Process: a shipped spec directory is frozen as a unit and its Status field
  is not.** Wave 6 receives a `**Status:**` block change only, pinned by AC27
  and AC30; Wave 5 is pinned by AC29. (source: `docs/CONVENTIONS.md:111-112` and
  its § "A spec directory freezes as a unit".)
- **Process: RFC-0096 is amended by an appended, Approver-signed erratum, not by
  a §9 body edit.** The RFC's own Errata preamble states the body is preserved
  and corrections are appended. Wave 6 edited the §9 body directly in commit
  `20c0ba50e`, which deviated from that rule. (source: RFC-0096 lines 359-360;
  user confirmation 2026-09-01.)
- **Product: Wave 7 ships as four slices.** Wave 7a-i is this delivery; Wave
  7a-ii is the completion receipt; Wave 7b is historical classification; Wave 7c
  is pruning. RFC §9 calls Wave 7 "a large separate release". The receipt was
  separated from this contract after two review rounds established that its
  criteria and this delivery's do not interact: a single combined contract drew
  52 sustained findings in round 1 and 29 in round 2, of which 19 were caused by
  the round-1 repair, while the cooling half drew 3 across both rounds. (source:
  `.context/reviews/wave7a-r1/` and `.context/reviews/wave7a-r2/`; user
  confirmation 2026-09-01.)
