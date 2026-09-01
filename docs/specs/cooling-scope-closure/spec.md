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
about which entries a cooled set removed — while each keeps counting what it
counts today, because they are derived over different lists on purpose. When the
cooled set does not resolve cleanly, the run reports a `cooling-context-incomplete`
closeout blocker, which withholds the affirmative instruction to invoke
`close-work`: a skill that distils and disposes must not be recommended on an
incomplete reading. The agent-rendered closeout gate reads the same cooled-exclusion facts the JSON
does, so the two cannot disagree about which entries a cooled set removed or
about an incomplete reading. The gate keeps its own further checks — that the
initiative's queue is empty and that it shipped something — which the projection
does not model and which this delivery preserves rather than replaces.

`repair-plan`, `repair-apply`, `repair-rollback`, and the migration planning,
application, and rollback paths are unaffected by cooling. That is their settled
contract, not a pending question, and the two reconciliation call sites that
receive no repository root stay that way.

This delivery changes two derivations, adds one closeout-blocker token, and pins
one decision. It adds no finding code, no persistent representation, and no
projected block, and it edits no frozen document.

The acceptance criteria below are the contract. Each names an input and the
exact observable it must produce.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| `decision-record` | Applicable: RFC-0096 §9 scopes Wave 7, this delivery ships its first slice, and §9's objective does not name either follow-on closing here | [`docs/rfc/0096-portable-delivery-artifact-lifecycle.md`](../../rfc/0096-portable-delivery-artifact-lifecycle.md) § Errata | Approver | AC29, AC30 and AC33: a dated, Approver-signed erratum carrying the four-slice split with what each slice owns, the three follow-on slugs with owners, and the corrected `cooling-brief-child-scope` basis | Closeout verifies all three erratum contents and AC28's §9 body digest |
| `current-architecture` | Applicable: the wave-ownership statement gains the slice split | [`docs/architecture/work-intake-and-artifact-routing.md`](../../architecture/work-intake-and-artifact-routing.md) | maintainer | AC25 and AC26 | Closeout verifies the three pinned strings, the absent string, and the four named slices |
| `user-documentation` (reference) | Applicable: the closeout derivation a reader relies on changes | [`guides/core/reference/work-intake-routing-and-lifecycle.md`](../../../guides/core/reference/work-intake-routing-and-lifecycle.md) | maintainer | AC27 | Closeout verifies the literal statement |
| `user-documentation` (workflow instructions) | Applicable: the agent-rendered closeout gate reads the changed facts | [`packs/core/.apm/skills/workspace-status/SKILL.md`](../../../packs/core/.apm/skills/workspace-status/SKILL.md) | maintainer | AC14, AC15, AC16, AC32 | Closeout verifies the exclusion statement, the narrowed rationale, the withholding rule, and the two retained conditions |
| `capability-evidence` (frozen live dependencies) | Applicable: two frozen spec directories are depended on and neither may change | Wave 6's and Wave 5's `docs/specs/` directories | maintainer | AC23's digest table | Closeout verifies every listed digest |
| `release-history` | Applicable: a shipped Core capability | [`docs/product/changelog.md`](../../product/changelog.md) | maintainer | AC31 | Closeout verifies the three release surfaces agree |
| `project-knowledge` | Conditional and intentionally unresolved until implementation produces reusable learning | — | `project-knowledge` gate | The gate's receipt, or an explicit not-applicable finding | Closeout requires one of the two |

## Boundaries

### Always do

- Derive the projected initiative's shipped-ness and its queue emptiness from
  one cooled-exclusion pass, so no two consumers in one response can disagree
  about which entries a cooled set removed.
- Decide cooled membership for an entry through the same resolution the cooled
  set itself used, so an entry named by a record alias is treated exactly as one
  named by its locator.

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
- Never pass a second argument to either reconciliation call site that receives
  only one today.
- Never add a `cooling`, `review_on`, `completed_on`, or `lifecycle_record` key
  to `workspace.toml`; Wave 5's AC24 test must keep passing.
- Never recompute a review date, re-derive a cooling period, or change the
  delivery-lifecycle record schema.
- Never write, move, rename, or delete anything under `docs/lifecycle/`.
- Never edit a Frozen `docs/specs/*` file, body or `**Status:**` line. The
  convention's non-supersession Status pointer covers a deleted
  `workspace.toml [backlog].open` anchor; Wave 6 registered these follow-ons in
  RFC-0096 §9 instead, so no anchor disappears and that licence does not apply.
- Never open the `spec.md` or `plan.md` of a cooled artifact during `status`,
  `reconcile`, `explain`, or the MCP status tool.
- Never classify history, prune an artifact, or project a completion receipt;
  Wave 7a-ii, Wave 7b, and Wave 7c own those.

### Definitions this contract uses

- The **projected initiative** is the lexicographically first initiative whose
  status is `active` or `paused`; it is the only initiative the `closeout` block
  describes.
- `initiatives[]` carries an entry only for an initiative whose status is
  `active`. A `paused` projection therefore has no `queue_empty` value anywhere
  in the response, which is why AC11 is separate from AC1 through AC10.
- Every criterion in "The shared cooled-exclusion derivation" is measured on
  both the `status` and the `reconcile` invocation, which are the two that emit
  the `closeout` block. The gate and surface criteria read a file and have no
  invocation.
- **Cooled** means the entry's resolved artifact path is a member of the cooled
  set, which Wave 5 builds from each record's `locator` together with its
  `aliases`.

## Testing Strategy

Every criterion names a concrete input and one of six observable shapes: a field
value at a named JSON path, byte identity against a named control run, a pinned
SHA-256 digest, a version-equality comparison, a literal string present or
absent in whitespace-normalized text, or a parsed source-shape count over a
named file.

- **The shared derivation: TDD.** The fixture tree and the injected instant are
  arguments, as they are in Wave 6's suite.
- **Agreement is proved on movement and on membership, not on value equality.**
  `all_specs_shipped` is derived over queue and active while `queue_empty` is
  derived over queue alone, so the two legitimately differ and AC5 pins that
  they still do. AC3 asserts both move between the cooled fixture and its
  uncooled control; AC4 repeats that for an entry cooled through a record alias,
  because two independently written filters can agree on a locator and disagree
  on an alias.
- **The repair and migration decision is pinned by control-run identity**, so a
  later blanket filter has to change those lines and say why.
- **Preservation criteria carry a mutation, not a red stub.** AC2, AC5, AC7,
  AC11, AC17 through AC25, AC28, and AC32 assert that something already true
  stays true; each is green before the change by construction, and the plan's
  mutation table names the edit that must be shown to redden it. Which criteria
  those are was decided by running every stub and reading each failure, not by
  reasoning about it.
- **Manual QA covers the real invocation.** A maintainer runs this surface
  directly, so `notes/manual-qa.md` records the observed output of `status` and
  `reconcile` over a fully cooled fixture, with the stop point and any behaviour
  documented but not exercised.
- **Frozen-body and contract preservation: literal pinned digests**, so each
  check holds after the branch is gone. A merge-base comparison is not used: the
  merge base moves to include this delivery once it lands.

**Stub coverage**, measured against the unchanged tree with each red's failing
assertion recorded, not inferred from an exit status. Compiled red stubs, 17:
AC1, AC3, AC4, AC6, AC8, AC9, AC10, AC12, AC13, AC14, AC15, AC16, AC26, AC27,
AC29, AC30, AC33. Preservation with a mutation row, 15: AC2, AC5, AC7, AC11,
AC17-AC25, AC28, AC32. `no stub (mode)`, 1: AC31. Total 33; uncovered none.

Three drafts of this tally were wrong before it was measured criterion by
criterion: one mislabelled a red that was a `FileNotFoundError` in the fixture
helper rather than a failing assertion, one miscounted by two, and one predicted
red for AC32 and preservation for AC13 where the run showed the reverse. Every
verdict is recorded in the plan with the assertion that failed, because a red for
the wrong reason is as useless as a green for the wrong reason.

## Acceptance Criteria

### The shared cooled-exclusion derivation

- [ ] **AC1 — A cooled queue entry counts toward neither consumer.** An
  initiative whose only `work.queue` entry is cooled reports
  `closeout.all_specs_shipped` `true` and that initiative's
  `initiatives[].queue_empty` `true`.
- [ ] **AC2 — The uncooled control reports both false.** The AC1 fixture with
  `docs/lifecycle/` removed reports `closeout.all_specs_shipped` `false` and
  that initiative's `initiatives[].queue_empty` `false`.
- [ ] **AC3 — Both consumers move together.** For the projected initiative,
  identified by its slug, `closeout.all_specs_shipped` and that initiative's
  `initiatives[].queue_empty` both differ between the AC1 fixture and the AC2
  fixture.
- [ ] **AC4 — An alias-cooled entry moves both consumers.** An initiative whose
  only `work.queue` entry is named by a lifecycle record's `aliases` rather than
  its `locator` reports the same two values as AC1, and both differ from the
  same fixture with `docs/lifecycle/` removed.
- [ ] **AC5 — `queue_empty` still counts the queue alone.** An initiative with an
  empty `work.queue` and one uncooled `work.active` entry reports
  `closeout.all_specs_shipped` `false` and that initiative's
  `initiatives[].queue_empty` `true`.
- [ ] **AC6 — A cooled active entry counts toward shipped-ness.** An initiative
  whose only `work.active` entry is cooled reports
  `closeout.all_specs_shipped` `true`, and `false` in the same fixture with
  `docs/lifecycle/` removed.
- [ ] **AC7 — An uncooled sibling still blocks.** An initiative holding one
  cooled and one uncooled `work.queue` entry reports
  `closeout.all_specs_shipped` `false` and `initiatives[].queue_empty` `false`.
- [ ] **AC8 — `unshipped-specs` names only unshipped specs.** In the AC1
  fixture, `closeout.closeout_blockers` does not contain `unshipped-specs`.
- [ ] **AC9 — An incomplete cooled reading withholds the affirmative
  instruction.** The AC1 fixture with one additional lifecycle record that
  cannot be read reports `closeout.cooling_context_visible` `true`,
  `closeout.closeout_blockers` containing `cooling-context-incomplete`, and
  `closeout.next_action` not `invoke-close-work`.
- [ ] **AC10 — A clean cooled reading keeps the affirmative instruction.** In the
  AC1 fixture, `closeout.cooling_context_visible` is `false`,
  `closeout.next_action` is `invoke-close-work`, and
  `closeout.closeout_blockers` does not contain `cooling-context-incomplete`.
- [ ] **AC11 — A paused projected initiative emits closeout without
  `queue_empty`.** Where the projected initiative's status is `paused`, the
  `closeout` block is present with `paused` `true` and `next_action`
  `resume-or-keep-paused`, and `initiatives[]` carries no entry for that
  initiative.

### The retired Wave 6 pin

- [ ] **AC12 — Wave 6's residual assertion is replaced.**
  `tests/roster/test_status_projection_and_context_exclusion.py` does not define
  `test_a_fully_cooled_initiative_still_reports_unshipped_specs`, and does
  contain the literal `projection["closeout"]["all_specs_shipped"] is True`.
- [ ] **AC13 — The rest of that file is undisturbed.** In
  `tests/roster/test_status_projection_and_context_exclusion.py`, the SHA-256 of
  its `test_`-prefixed function names, sorted and joined by newlines, is
  `660b7204a2fe32f5d75ab03f43828934ad42c8b06b572b99292585bf13bbf8e6` with the
  retired name replaced by its successor — a set, not a count, so deleting an
  assertion from a different function cannot satisfy it.

### The agent-rendered closeout gate

- [ ] **AC14 — The skill states the cooled exclusion.** Whitespace-normalized,
  `packs/core/.apm/skills/workspace-status/SKILL.md` contains `the queue
  emptiness flag excludes entries named by a lifecycle record`.
- [ ] **AC15 — The raw-queue-emptiness rationale is gone.**
  Whitespace-normalized, `packs/core/.apm/skills/workspace-status/SKILL.md` does
  not contain `the raw queue emptiness flag is the authoritative check`.
- [ ] **AC16 — The skill withholds the affirmative on any closeout blocker.**
  Whitespace-normalized, `packs/core/.apm/skills/workspace-status/SKILL.md`
  contains `do not offer closeout while closeout_blockers is non-empty`.

- [ ] **AC32 — The skill keeps its two further closeout conditions.**
  Whitespace-normalized, `packs/core/.apm/skills/workspace-status/SKILL.md`
  contains `initiatives[i].queue_empty` is `true` and contains `filtered shipped
  is non-empty`.

### Repair and migration scope

- [ ] **AC17 — `repair-plan` is unaffected by cooling.** A fixture whose
  `work.queue` entry is cooled produces `repair-plan` output identical to the
  same fixture with `docs/lifecycle/` removed.
- [ ] **AC18 — `repair-apply` is unaffected by cooling.** In the AC17 fixture,
  `repair-apply` writes the same `workspace.toml` bytes as it writes for the
  same fixture with `docs/lifecycle/` removed.
- [ ] **AC19 — Migration planning is unaffected by cooling.** A
  `repair-plan --migration-selection` invocation over a fixture whose legacy
  entry's artifact is cooled produces output identical to the same fixture with
  `docs/lifecycle/` removed.
- [ ] **AC20 — Migration application is unaffected by cooling.** A
  `repair-apply --migration-selection --operation-id --confirmation-file`
  invocation over the AC19 fixture produces the same result code and the same
  `workspace.toml` bytes as the same fixture with `docs/lifecycle/` removed.
- [ ] **AC21 — Migration recovery is unaffected by cooling.** A
  `repair-apply --migration-selection` invocation over an AC20 ledger left in a
  `pending` state produces the same result code and the same `workspace.toml`
  bytes as the same fixture with `docs/lifecycle/` removed.
- [ ] **AC22 — Migration rollback is unaffected by cooling.** A
  `repair-rollback --operation-id --confirmation-file` invocation over the AC20
  fixture's post-apply state produces the same result code and the same
  `workspace.toml` bytes as the same fixture with `docs/lifecycle/` removed.
- [ ] **AC23 — Every pinned file is byte-unchanged.** The SHA-256 of each file
  below equals the value beside it.

  | File | SHA-256 |
  | --- | --- |
  | `packs/core/.apm/skills/close-work/scripts/cooling.py` | `d6bd7c6e47d5a23e45a9f5ee5a8d5506d3435b1da00facde96f1fbfba5bf061c` |
  | `contracts/jsonschema/delivery-lifecycle-record.schema.json` | `557e3d60b8fd5647a06fbc2225de51a52cfff1b8777fd3d917e91bcebbe27878` |
  | `docs/specs/status-projection-and-context-exclusion/spec.md` | `2cac21ca5f84e0f4e477a6bab432429a55034f6851dc152cfcd93611e9e3523d` |
  | `docs/specs/status-projection-and-context-exclusion/plan.md` | `93958585c454ab761a79f2e358e546f5d0cc7e7c8e722a8cf42114ab22a7c487` |
  | `docs/specs/thirty-day-cooling-and-retirement/spec.md` | `3255b1a8b12e2cfaeccc5e6c97a7047467e8ca8e001467fdefc6757318d4c95f` |
  | `docs/specs/thirty-day-cooling-and-retirement/plan.md` | `2c416277c607b9f7b2b617e06a79a58f6059f43bd2d6c2ebef35ea6af810e3e7` |

- [ ] **AC24 — The single-argument reconciliation call sites are unchanged.** In
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, exactly
  two calls to `run_canonical_reconciliation` pass exactly one argument.

### Surfaces

- [ ] **AC25 — The wave-ownership statements survive.** Whitespace-normalized,
  `docs/architecture/work-intake-and-artifact-routing.md` contains `Wave 5 has
  shipped the lifecycle record, review-date, due-state, and retirement engine`,
  `Wave 6 has shipped ordinary-context exclusion`, and `Wave 7 owns historical
  migration and pruning behavior`, and does not contain `Wave 6 and 7 own
  ordinary-context exclusion`.
- [ ] **AC26 — The architecture surface names the four slices and what each
  owns.** Whitespace-normalized,
  `docs/architecture/work-intake-and-artifact-routing.md` contains each of
  `Wave 7a-i closes`, `Wave 7a-ii projects`, `Wave 7b classifies`, and
  `Wave 7c prunes`. Each literal carries its own following word, so no slice's
  name is a prefix of another's match.
- [ ] **AC27 — The reference guide states the closeout derivation.**
  Whitespace-normalized,
  `guides/core/reference/work-intake-routing-and-lifecycle.md` contains `an
  entry named by a lifecycle record counts toward neither closeout consumer`.

### Governance

- [ ] **AC28 — RFC-0096 §9's body is unchanged.** The SHA-256 of the bytes of
  `docs/rfc/0096-portable-delivery-artifact-lifecycle.md` from the
  `## 9. Initiative waves` heading up to but excluding the
  `## 10. Risks and revisit conditions` heading is
  `e49f49f12fc7dccff4cd962cecff7be003672283d8a750097a238001b222a45e`.
- [ ] **AC29 — The erratum records the four-slice split and what each slice
  owns.** The RFC's § Errata contains an entry whose date is this delivery's
  commit date, naming `Approver: eugenelim`, stating that Wave 7 ships as Wave
  7a-i, Wave 7a-ii, Wave 7b, and Wave 7c, naming the objective each slice owns,
  and naming this spec as Wave 7a-i.
- [ ] **AC30 — The erratum registers the three open follow-ons and corrects the
  `cooling-brief-child-scope` basis.** The same erratum names
  `rfc0096-wave7a-ii-completion-receipts`,
  `rfc0096-wave7b-historical-classification`, and `rfc0096-wave7c-pruning` with
  their owning slices, and states that Wave 6's `cooling-brief-child-scope`
  entry misattributes its constraint to that spec's own AC46 pinned pair when the finding-code
  documentation gate is a superset check admitting any documented code.
- [ ] **AC33 — The erratum records both closures and the receipt slug's
  rename.** The same erratum states that `cooling-closeout-eligibility` and
  `cooling-repair-migration-scope` were closed by `cooling-scope-closure`, and
  that Wave 6's `wave6-dependency-scoped-completion-receipts` is registered here
  as `rfc0096-wave7a-ii-completion-receipts`.
- [ ] **AC31 — The release surface agrees.** `packs/core/pack.toml`'s version,
  `packs/core/.claude-plugin/plugin.json`'s `version`, and the topmost dated
  `[core]` changelog heading are one identical value whose parsed
  `(major, minor, patch)` tuple is strictly greater than `(2, 18, 2)`.

## Follow-ons

Separately scoped work this delivery does not perform. The erratum AC29 and AC30
require is the register for all four.

| Slug | Outcome | Owner |
| --- | --- | --- |
| `rfc0096-wave7a-ii-completion-receipts` (Wave 6 registered this as `wave6-dependency-scoped-completion-receipts`) | Project the dependency-scoped four-field completion receipt from its coordination surface, including the producer's spelling in `close-work`'s instructions, the satisfaction rule for an absent artifact, and whether `completion_event` and `evidence_ref` are pinned to the grammars the lifecycle record already publishes. Its load-bearing precondition is a repository state only closeout produces — entry removed and artifact removed; see probe 1. | RFC-0096 Wave 7a-ii |
| `cooling-brief-child-scope` | Wave 6's own recorded follow-on, unchanged in scope; see [`status-projection-and-context-exclusion/spec.md`](../status-projection-and-context-exclusion/spec.md) § Follow-ons for its reproduction. The erratum corrects its recorded basis. | RFC-0096 Wave 7b |
| `rfc0096-wave7b-historical-classification` | Classify the repository's delivery history with proven outputs, dependencies, authority, and disposition, and each ambiguity an owned dated `retain-exception`. Supplies the read-free parent link that closes `cooling-brief-child-scope`. | RFC-0096 Wave 7b |
| `rfc0096-wave7c-pruning` | Prune proven-eligible artifacts under reviewed plans, explicit confirmations, and no bulk deletion. Must remove a pruned artifact's workspace entry as well as its file: a surviving entry refuses at `structurally_blocked_paths` before the absent-target refusal, so a receipt is never consulted. See probe 1. | RFC-0096 Wave 7c |

## Assumptions

- **Technical: the two consumers are derived over different lists and are not
  meant to be equal.** Wave 6's follow-on requires them to agree about the
  cooled set, not to hold the same value, which is why AC3 and AC4 compare
  movement and AC5 pins that `queue_empty` still counts the queue alone.
  (source: probe 3 in [`notes/probes.md`](notes/probes.md);
  `docs/specs/status-projection-and-context-exclusion/spec.md:176`.)
- **Technical: `closeout` describes one initiative and `initiatives[]` carries
  only active ones.** A paused projection therefore has no `queue_empty`, which
  AC11 pins separately. (source: probe 2 in
  [`notes/probes.md`](notes/probes.md).)
- **Technical: one blocker is enough to withhold the affirmative.** The shipped
  projection computes eligibility as `all_specs_shipped and not blockers and not
  paused` and emits `invoke-close-work` only when eligible, so appending
  `cooling-context-incomplete` to `closeout_blockers` withholds the affirmative
  by itself. No separate guard on `cooling_context_visible` is added. (source:
  `workspace_status_engine.project_closeout_status`.)
- **Technical: `cooling-context-incomplete` needs no documentation row.** The
  finding-code documentation gate is scoped to
  `engine._FINDING_NEXT_ACTIONS`; this token is a `closeout_blockers` member,
  and no repository surface documents any blocker literal today. (source:
  `tests/roster/test_workspace_status_projection.py:488-495`.)
- **Technical: a Wave 6 roster assertion pins the inverse of AC1 and AC8, and no
  Wave 6 acceptance criterion does.**
  `test_a_fully_cooled_initiative_still_reports_unshipped_specs` asserts
  `all_specs_shipped is False` and `"unshipped-specs" in closeout_blockers`
  deliberately, as Wave 6's recorded known starting state; Wave 6's own AC31
  test uses an uncooled entry, so replacing that function creates no frozen-body
  drift. AC12 and AC13 replace it and bound the change. (source: that test; and
  `tests/roster/test_status_projection_and_context_exclusion.py:1648-1654`.)
- **Technical: cooling must not constrain repair or migration.** Those verbs are
  explicitly invoked and mutating rather than ordinary orientation, and their
  artifact reads are pre-mutation revalidation the conventions forbid cutting.
  Wave 6 decided the adjacent question the same way: a `legacy_entry` finding
  still names a cooled path, because the entry's shape is owed repair whether or
  not its artifact cooled. (source:
  `docs/specs/status-projection-and-context-exclusion/spec.md` AC20 and
  `notes/repair-plan.md` § Q16.)
- **Technical: the two single-argument call sites consume memberships only.**
  Both are inside `_migration_rollback_workspace_bytes`, which locates a byte
  slice from `canonical.memberships` and `legacy_memberships` — data the parsed
  workspace already carries, with no filesystem read — so a repository root
  would buy nothing there. The rollback path reaches that helper directly; the
  apply path reaches it only in its recovery branch, which is why AC21 exists
  alongside AC20 and AC22. (source: probe 4 in
  [`notes/probes.md`](notes/probes.md).)
- **Process: a shipped spec directory is frozen as a unit, and this delivery
  edits neither frozen dependency.** The convention's non-supersession Status
  pointer covers a deleted `workspace.toml [backlog].open` anchor; Wave 6
  registered these follow-ons in RFC-0096 §9 instead, so nothing points at a
  missing anchor and no Status edit is licensed. AC33 makes the erratum the
  durable record of closure. Wave 6's `plan.md` still carries `Status: Approved`
  rather than `Done`, so the convention's freeze predicate is not literally met
  for that directory; AC23 pins it regardless. (source:
  `docs/CONVENTIONS.md:183-199` and its § "A spec directory freezes as a unit".)
- **Process: RFC-0096 is amended by an appended, Approver-signed erratum, not by
  a §9 body edit.** The RFC's own Errata preamble states the body is preserved
  and corrections are appended. The §9 body was nonetheless edited directly in
  commit `bfd6ad428`; commit `20c0ba50e` only appended the § Errata section
  itself. (source: RFC-0096 lines 359-360;
  `git log -L 269,326:docs/rfc/0096-portable-delivery-artifact-lifecycle.md`;
  user confirmation 2026-09-01.)
- **Product: Wave 7 ships as four slices.** Wave 7a-i is this delivery; Wave
  7a-ii is the completion receipt; Wave 7b is historical classification; Wave 7c
  is pruning. RFC §9 calls Wave 7 "a large separate release", and its objective
  names none of what this slice closes, which is why the erratum must state what
  each slice owns. (source: user confirmation 2026-09-01.)
