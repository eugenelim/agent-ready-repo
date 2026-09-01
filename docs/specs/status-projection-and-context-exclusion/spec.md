# Spec: Status projection and context exclusion

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 §7 and §9; `thirty-day-cooling-and-retirement` (Shipped, live dependency); `close-work-extraction-and-immediate-disposition` (Shipped, live dependency)
- **Brief:** none
- **Discovery:** none
- **Contract:** [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) (consumed unchanged)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer running `workspace-status` sees how much closed-out work is waiting
on them, and stops seeing the work that is already finished.

Ordinary orientation reports how many cooling reviews are due, names each one,
lists retention exceptions with the role that owns them and the date they are
due, and states the closeout next action. Artifacts that have finished no longer
appear as queue material and are no longer opened. A retention exception stays
visible, because someone still owes work against it.

Orientation also states whether that exclusion actually happened, so a run that
could not resolve the lifecycle records says so rather than implying a guarantee
it did not deliver.

`workspace-status` remains read-only for closeout policy: it projects
eligibility and next actions, and never distils, dispositions, confirms, or
deletes.

The acceptance criteria below are the contract. Each names an input and the
exact observable it must produce.

## Assumptions

- **"Its contents" in RFC-0096 §7 means the cooled artifact body, not the
  lifecycle record.** The record is the pointer layer and ordinary orientation
  may read it through Wave 5's bounded reader. (source:
  [`notes/mechanism-decision.md`](notes/mechanism-decision.md).)
- **`disposition` and `post_closeout_result` are two axes, not one.** Wave 5's
  `_TRANSITIONS` and its exception-review outcome map admit five reachable
  pairs, and `Retired` is reachable from both dispositions. This spec's
  predicate is stated on the pair. (source:
  `cooling._TRANSITIONS` and its exception-review outcome map in
  `packs/core/.apm/skills/close-work/scripts/cooling.py`.)
- **Excluding a `Retained` artifact is unauthorized; excluding a `Retired` one
  is an owner decision.** RFC §7 grants exclusion for cooling only, §5 defines
  `retain-exception` as a longer obligation to retain, and §6 requires status to
  signal exception review — so `("retain-exception", "Retained")` is settled by
  the text. RFC §7 is silent on `Retired` and `ExternalAdvisory`. (source:
  RFC-0096 §5, §6, §7; owner decision 2026-08-30.)
- **A lifecycle record is an unverified assertion, honoured on the authority of
  repository write access alone.** One schema-valid file removes an artifact
  from orientation. Wave 6 cannot cross-check `fingerprint`, `authority`, or
  `confirmation_proof` against the artifact, because doing so requires the read
  RFC §7 forbids. A record added by a pull request deserves spec-level scrutiny.
  (source: `cooling.load_record` cross-checks only `path.stem == delivery_id` and
  the recomputed `review_on`.)
- **`project_closeout_status` gained its first production callers in this
  wave.** Defined as `workspace_status_engine.project_closeout_status`, it was test-only
  when this spec was drafted; `workspace_status.py` now binds it and calls it
  from `_closeout_projection`. Cited by symbol: the line numbers this Assumption
  first carried drifted three times during review. The original assumption of no
  production caller no longer holds, and the closeout block is therefore shipped
  behaviour rather than an unreached projection. (source: verified by repository
  search, 2026-08-31.)
- **Wave 5's `cooling.is_due`, `cooling.load_record`, and the record schema stay
  byte-unchanged.** Wave 6 consumes them and adds no field and no date logic.
  (source: RFC §9 Wave 6 non-goals; Wave 5 is Shipped and frozen.)
- **The settled cut list holds:** no second status engine, no new date logic, no
  deletion/disposition/distillation/confirmation, no cooling state in
  `workspace.toml`, no new store, resolver, fingerprint helper, dependency,
  scheduler, or background job, no history rewrite, no new top-level directory,
  and no new retrieval verb or flag. (source: accepted before review.)
- **The schema's `post_closeout_result` enum omits `Reclassified`**, which
  RFC §5 lists. No record can carry it today. Closing that gap is Wave 5's.
  (source: `delivery-lifecycle-record.schema.json:18` against RFC-0096 §5.)

## Durable Outputs

| Semantic role | Applicability and resolved destination | Owner and closeout evidence |
| --- | --- | --- |
| `decision-record` | Applicable: [`docs/rfc/0096-portable-delivery-artifact-lifecycle.md`](../../rfc/0096-portable-delivery-artifact-lifecycle.md) | The accepted RFC owns the exclusion contract in §7 and Wave 6's scope in §9. Wave 6 adds no ADR. Closeout verifies the pin. |
| `interface-contract` | Applicable, unchanged: [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) | Wave 5 owns the record shape; Wave 6 consumes it and adds no field. Closeout verifies SHA-256 `557e3d60b8fd5647a06fbc2225de51a52cfff1b8777fd3d917e91bcebbe27878`. |
| `current-architecture` | Applicable: [`docs/architecture/work-intake-and-artifact-routing.md`](../../architecture/work-intake-and-artifact-routing.md) | Owns the Wave 6/7 boundary statement and the routing-table row at `:91`. Closeout verifies the boundary sentence names Wave 7 alone. |
| `user-documentation` (reference) | Applicable: [`guides/core/reference/work-intake-routing-and-lifecycle.md`](../../../guides/core/reference/work-intake-routing-and-lifecycle.md) | Owns the public statement of what `workspace-status` projects. Closeout verifies the visibility claim is replaced by the exclusion statement. |
| `user-documentation` (finding-code reference) | Applicable: [`guides/core/reference/workspace-toml-schema.md`](../../../guides/core/reference/workspace-toml-schema.md) | Owns the public finding-code table that the finding-code table check in `tests/roster/test_workspace_status_projection.py` gates. Closeout verifies a reason and a next action for each new code. |
| `user-documentation` (workflow instructions) | Applicable: [`packs/core/.apm/skills/workspace-status/SKILL.md`](../../../packs/core/.apm/skills/workspace-status/SKILL.md) | Owns what the agent renders at runtime, its finding-code table, and its output-section list. Closeout verifies the Wave 4 visibility sentence is gone and both new codes are documented. |
| `capability-evidence` (Wave 4 live dependency) | Applicable: [`packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py`](../../../packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py) | Owns the shipped assertion that Wave 4 could not exclude cooling context. Wave 6 replaces that one test function; the rest of the file is untouched. Closeout verifies the replacement, not a deletion. |
| `release-history` | Applicable: [`docs/product/changelog.md`](../../product/changelog.md) | Owns the shipped Core capability. Closeout verifies the topmost dated `[core]` heading equals `packs/core/pack.toml`. |
| `runtime-coordination` | Applicable, unchanged: `docs/lifecycle/` | Wave 5 owns the destination and the single-writer rule. Wave 6 reads and never writes. Closeout verifies no new writer exists. |
| `project-knowledge` | Conditional and intentionally unresolved until implementation produces reusable learning | No placeholder is created. Closeout requires either an explicit `not applicable—no reusable learning` finding or an accepted gate receipt. |

### Capability and delivery evidence

Wave 4's and Wave 5's spec/plan pairs are live dependencies and are not disposed
of here. Wave 4's `spec.md` is Frozen under
[`docs/CONVENTIONS.md:112`](../../CONVENTIONS.md) and is not edited; its *test*
files are not frozen and are amended by criterion.

## Boundaries

### Always do

- Treat every lifecycle record, locator, alias, date, and timezone as bounded
  untrusted data and revalidate it at the seam that acts on it.
- Answer dueness by calling Wave 5's `cooling.is_due(record, moment)`.
- Confine every resolved module candidate and the lifecycle directory to its
  declared root by canonicalizing and then verifying the prefix, not by
  rejecting `..` alone.
- Never let two consumers within one ordinary-orientation run disagree about
  which artifacts are cooled. The repair and migration surfaces are the named
  exception: they receive an empty set by design, stated below.

### Ask first

- Ask before changing the emitted key set of `cooling` or `closeout`, or the
  subcommands that carry them.
- Ask before reading any file under a cooled locator for any reason.
- Ask before adding a retrieval verb, flag, or subcommand for cooling detail.

### Never do

- Never open the `spec.md` or `plan.md` of a cooled artifact during `status`,
  `reconcile`, `explain`, or the MCP status tool — including through the
  dependency probes built inside
  `workspace_status_engine._dependency_is_satisfied`, which reach artifacts that
  are not workspace entries. Cited by symbol: a line range in a file this size
  drifts with every edit, and the range this criterion first carried had already
  moved into an unrelated function.
- Never write, move, rename, or delete anything under `docs/lifecycle/`.
- Never distil, disposition, confirm, or delete from `workspace-status`.
- Never recompute a review date or re-derive a cooling period.
- Never reuse an existing finding code for a cooling condition; existing codes
  carry meanings that shipped consumers already act on.
- Never add a store, resolver, fingerprint helper, dependency, scheduler, or
  background job.
- Never add a cooling, `review_on`, `completed_on`, or `lifecycle_record` key to
  `workspace.toml`; Wave 5's AC24 test must keep passing.
- Never add a non-stdlib import to `workspace_status_engine.py`, and never let
  the strings `tools.`, `packs.`, `shared-libs`, or `shared_libs` enter it.
- Never edit a Frozen `docs/specs/*` body.
- Never classify history or prune an artifact; Wave 7 owns both.

### Deferred to Wave 7

`repair-plan`, `repair-apply`, and the migration paths keep pre-Wave-6
behaviour: they receive an empty cooled set and continue to read the artifacts
they fingerprint. Two of the eight `run_canonical_reconciliation` call sites
pass no repository root and cannot resolve a cooled set at all, so this is a
mechanical boundary as well as a scope one. See [Follow-ons](#follow-ons).

## Follow-ons

Separately scoped work this delivery does not perform. Recorded here rather than
as an inline `(deferred:)` token: `docs/CONVENTIONS.md:479-486` reserves that
token for pre-existing frozen specs and directs new separable work to this
section. Both items are owned by RFC-0096 Wave 7, whose §9 entry scopes
them, so the RFC is their register — a `[backlog].open` slug entry would be
legacy-shaped and the repository ratchets against adding one. For
`wave6-dependency-scoped-completion-receipts` that register did not hold until
this wave amended it: §9 assigned receipts to Wave 6's own behaviour line and
Wave 7's entry never mentioned them, so the deferral pointed at a section that
did not carry it. Owner decision 2026-08-31: amend §9 rather than build the
projection, because the lifecycle record schema has no `outcome` field and
supplying one is a contract change this wave did not accept. The Wave 6 and
Wave 7 entries and the `workspace.toml` summary were corrected together.

| Slug | Outcome | Owner |
| --- | --- | --- |
| `cooling-repair-migration-scope` | Decide whether cooling constrains `repair-plan`, `repair-apply`, and the migration paths, including whether the two rootless `run_canonical_reconciliation` call sites gain a repository root. | RFC-0096 Wave 7 |
| `cooling-brief-child-scope` | Decide how a cooled child spec whose brief link exists only in the artifact body contributes to its parent brief's `invalid_child_scope` verdict. AC59 closes the case where the child declares `source.parent`; a body-only link is not readable read-free, so such a child is dropped from the child-state set and the empty set reads as compliance under `brief_queue.shipped` (erasing `impossible_transition` and unblocking the brief's dependants) and as a violation under `brief_queue.executing` (planting one on live work). Two conservative repairs were attempted and withdrawn: marking every brief in the workspace, then every brief in the initiative. Both refused brief dependencies whenever any ordinary parentless spec cooled -- 81 of 92 specs in `ini-002` declare no `source.parent` -- which costs more availability than the bypass it closes. Closing it needs either a readable parent link for cooled children or a finding code that says "child scope unknown", which AC46's pinned pair does not admit. | RFC-0096 Wave 7 |
| `cooling-closeout-eligibility` | Decide whether a cooled queue entry counts toward `all_specs_shipped`. It currently does, so a fully cooled initiative reports `unshipped-specs` indefinitely and never reaches `invoke-close-work`. A Wave 6 repair was attempted and reverted: filtering the count let an unverified lifecycle record drive an affirmative recommendation to run a skill that distils and disposes, while `initiatives[].queue_empty` stayed unfiltered and disagreed inside the same response. Whichever way it resolves, the two must agree. | RFC-0096 Wave 7 |
| `wave6-dependency-scoped-completion-receipts` | Project the four-field `{delivery_id, outcome, completion_event, evidence_ref}` completion receipt from its coordination surface. Wave 6 projects record completion evidence only; `outcome` has no source in the lifecycle record schema. | RFC-0096 Wave 7 |

## Testing Strategy

Every criterion names a concrete input and one of seven observable shapes: a
named finding code at a named JSON path, a field value, a byte comparison, an
enumerated key set over a named path, a named negative event with its stated
detection, identity against a named control run, or a literal string present or
absent in whitespace-normalized text.

- **Cooled-set resolution, exclusion, projection, module loading, and the
  guard: TDD.** The injected instant and the fixture tree are arguments.
- **Exclusion is proved by two independent observable classes, each with an
  explicit control** — the identical fixture with `docs/lifecycle/` removed.
  The **count class** asserts an exact delta and each of its members carries an
  uncooled sibling so an implementation that excludes everything fails: AC16
  carries `gamma` for the global scan, AC18 and AC20 carry `beta` for the
  declared scan. The **byte class** (AC13) uses the one route by which an artifact-body
  value reaches emitted JSON verbatim: a `- **Brief:**` preamble value becomes
  `metadata.parent` (`workspace_status_engine._metadata_from_root` (the `metadata.parent` assignment)) and is emitted as
  the `path` of an `invalid_artifact_path` finding when the cooled spec is a
  dependency target (`:2346`). AC13 asserts the sentinel is **present** in the
  control run and absent in the cooled run, so a fixture that never produced it
  fails loudly rather than passing vacuously.
- **Negative events name their detection.** AC9 detects a non-read by placing a
  valid record under the escaping target and asserting it contributes no member.
  AC40 detects non-execution by a marker the candidate's module body writes,
  asserted **present** in a control run where the same candidate resolves inside
  its root.
- **Delegation is proved by a zone boundary, not by substitution.** AC42 uses an
  instant that is one date in UTC and the next in the record's recorded zone.
- **AC47, AC49, and AC50 compare whitespace-normalized text**, using the idiom
  at `tests/roster/test_workspace_status_projection.py:191`, because every
  target sentence wraps in its source. Each names a literal gain string and a
  literal loss string. AC45, AC46, AC51, AC52, AC53, and AC54 use other shapes
  and carry no string pair.
- **AC35 is one predicate over two builders, and only one member can fail.**
  `explain` uses `_build_explain_json`, which the plan leaves untouched, so its
  key absence holds before and after; the `repair-plan` member is the one the
  mode gate can break, because `_build_repair_plan_json` delegates to the gated
  `_build_json`.
- **Frozen-body preservation: pinned digest**, so the check holds after the
  branch is gone.

**Stub coverage.** Compiled red stubs: AC1–AC44 and AC55–AC56 (T1–T3). AC57, AC58 and AC59 were added during review and are covered by directly authored tests rather than compiled stubs — `plan.md` is hash-pinned and names none of them; AC59 closes the attributed half of `cooling-brief-child-scope` — all covered by tests at `tests/roster/test_status_projection_and_context_exclusion.py`).
`no stub (mode)`: AC45–AC54 (T4, goal-based). Uncovered: none.

## Acceptance Criteria

### The cooled-locator set

- [x] **AC1 — Only finished work cools.** A record whose
  `(disposition, post_closeout_result)` is `("cool-30-days", "Cooling")` and
  whose `locator` is `docs/specs/alpha/spec.md` puts that path's resolved real
  path in the cooled set.
- [x] **AC2 — Aliases cool with the locator.** That record adding
  `aliases = ["docs/specs/old-alpha/spec.md"]` yields a cooled set containing
  the resolved real paths of both.
- [x] **AC3 — A live obligation stays visible.** With one
  `("retain-exception", "Retained")` and one
  `("retain-exception", "ExternalAdvisory")` record, both naming existing
  Approved queued specs, `scan.declared_spec_files_read` and `canonical.ready`
  are identical to the same fixture with `docs/lifecycle/` removed.
- [x] **AC4 — A settled exception cools.** A
  `("retain-exception", "Retired")` record naming an existing Approved queued
  spec removes it from `canonical.ready`.
- [x] **AC5 — An invalid record cools nothing and is named.**
  `docs/lifecycle/spec-bad.json` holding only
  `{"schema": "delivery-lifecycle-record.v1"}` yields an empty cooled set and
  one `canonical.findings` entry whose `code` is `invalid_lifecycle_record` and
  whose `path` is `docs/lifecycle/spec-bad.json`.
- [x] **AC6 — A non-record file is skipped silently.** With only
  `docs/lifecycle/README.md` present, the cooled set is empty and
  `canonical.findings` carries no `invalid_lifecycle_record` entry.
- [x] **AC7 — An absent directory is not an error.** With no `docs/lifecycle/`,
  the cooled set is empty and `canonical.findings` carries no
  `invalid_lifecycle_record` and no `cooling_state_unavailable` entry.
- [x] **AC8 — An unusable directory is named.** With `docs/lifecycle` present as
  a regular file, `canonical.findings` carries exactly one entry whose `code` is
  `cooling_state_unavailable`, and the run raises nothing.
- [x] **AC9 — The lifecycle directory is confined.** With `docs/lifecycle` a
  symlink resolving outside the repository root and a schema-valid `Cooling`
  record placed under that target, the cooled set is empty and
  `canonical.findings` carries one `cooling_state_unavailable` entry.
- [x] **AC10 — A symlinked record is refused.** `docs/lifecycle/spec-link.json`
  symlinked to an in-root regular file yields one `invalid_lifecycle_record`
  entry for that path and no cooled-set member from it.
- [x] **AC11 — An oversized record refuses without raising.** A record padded
  past `cooling.MAX_RECORD_BYTES` yields one `invalid_lifecycle_record` entry,
  an empty cooled set, and no exception.
- [x] **AC12 — Membership is decided on the real file.** With
  `docs/specs/alias-alpha` an in-root symlink to `docs/specs/alpha` and only
  `docs/specs/alpha/spec.md` named by a `Cooling` record, a queue entry whose
  path is `docs/specs/alias-alpha/spec.md` is absent from `canonical.ready`.

### Context exclusion

- [x] **AC13 — A cooled body never reaches the output.**
  `docs/specs/alpha/spec.md` carries `- **Brief:** COOLSENTINEL42` and is a
  declared dependency of a queued spec. With `docs/lifecycle/` removed the
  `reconcile` JSON contains `COOLSENTINEL42`; with the `Cooling` record present
  it does not.
- [x] **AC14 — A cooled local spec dependency does not block its dependant.** For the AC13
  fixture with the record present, `canonical.ready` contains exactly one item
  and its `path` is the depending spec's.
- [x] **AC15 — A cooled spec raises no Type 1 finding.** Under subcommand
  `reconcile`, for an untracked Approved `docs/specs/alpha/spec.md` named by a
  `Cooling` record, `reconciliation` contains no entry whose `spec_path` is
  `spec/alpha`; with `docs/lifecycle/` removed, exactly one such entry is
  present.
- [x] **AC16 — The global-scan counter moves by exactly one.** Under subcommand
  `reconcile`, for the AC15 fixture plus an uncooled Approved untracked
  `docs/specs/gamma/spec.md`, `scan.global_scan_spec_files_read` equals the
  control value minus one, and `reconciliation` still contains exactly one entry
  whose `spec_path` is `spec/gamma`.
- [x] **AC17 — A cooled queue entry never becomes dispatchable.** With active
  initiative `ini-002` holding `docs/specs/alpha/spec.md` in `[work].queue` and
  a `Cooling` record naming it, `canonical.ready` and `canonical.evaluations`
  each contain no item whose `path` is `docs/specs/alpha/spec.md`.
- [x] **AC18 — The declared-spec counter moves by exactly one.** For the AC17
  fixture plus an uncooled Approved queued `docs/specs/beta/spec.md`,
  `scan.declared_spec_files_read` equals the control value minus one.
- [x] **AC19 — An uncooled sibling still dispatches.** For the AC18 fixture,
  `canonical.ready` holds exactly one item and its `path` is
  `docs/specs/beta/spec.md`.
- [x] **AC20 — A legacy entry is excluded identically.** With the AC18 fixture's
  cooled entry written in the legacy `spec/alpha` form and uncooled `beta` left
  canonical, `scan.declared_spec_files_read` equals the control value minus one
  and `canonical.ready` still holds `docs/specs/beta/spec.md`. No item in
  `canonical.blocked` has the path `spec/alpha`, which the control does carry:
  a legacy entry reaches that list as a legacy membership rather than as an
  evaluation, so the scan and ready assertions alone leave it presented.
  A `legacy_entry` finding for that path is still emitted, and this is
  deliberate. Exclusion governs the *artifact*: it is not offered as work and
  its body is not opened. `legacy_entry` is a fact about the `workspace.toml`
  entry's shape, and migrating that entry is still owed whether or not the
  artifact it points at has cooled. Suppressing it would hide a live workspace
  obligation, and the migration surfaces that would otherwise act on it receive
  an empty cooled set by design.
- [x] **AC21 — Bounded mode excludes identically.** The AC17 fixture run through
  subcommand `status` yields `canonical.ready` containing no item whose `path`
  is `docs/specs/alpha/spec.md`.
- [x] **AC22 — The MCP surface inherits the exclusion and its findings.**
  `_WorkspaceStatusTool.call()` over the AC17 fixture returns `ready` containing
  no item whose `path` is `docs/specs/alpha/spec.md`. Over the AC8 fixture the
  same call returns `canonical.findings` carrying exactly one entry whose `code`
  is `cooling_state_unavailable`. Performing the exclusion and reporting why it
  could not be performed are separate obligations, and a surface that met only
  the first would claim an exclusion it never made.

### Projection

- [x] **AC23 — Due reviews are counted.** `Cooling` records `spec-a`
  (`review_on = "2026-08-01"`) and `spec-b` (`review_on = "2099-01-01"`), both
  `Asia/Singapore`, at injected instant `2026-08-30T00:00+08:00`, yield
  `cooling.due_count == 1` under subcommand `reconcile`.
- [x] **AC24 — A due review is named, not only counted.** For the AC23 fixture
  under `reconcile`, `cooling.due` is a one-element list whose object has
  exactly the keys `delivery_id`, `locator`, and `review_on`, with
  `delivery_id` equal to `spec-a`.
- [x] **AC25 — The projected record field set is closed.** Each object in
  `cooling.records` for the AC23 fixture has exactly the keys `delivery_id`,
  `locator`, `disposition`, `post_closeout_result`, `completion_event`,
  `completion_evidence_ref`, `review_on`, and `due`.
- [x] **AC26 — Completion evidence is projected.** For the AC23 fixture, the
  `spec-a` object's `completion_event` and `completion_evidence_ref` equal the
  values persisted in `docs/lifecycle/spec-a.json`.
- [x] **AC27 — An exception carries owner role and review date.** A
  `("retain-exception", "Retained")` record with
  `exception.owner_role = "maintainer"` and
  `exception.review_on = "2026-09-15"` yields one `cooling.exceptions` object
  with exactly the keys `delivery_id`, `locator`, `owner_role`, `reason`, and
  `review_on`, carrying those two values. A
  `("retain-exception", "ExternalAdvisory")` record yields a second such object,
  because it is the other live obligation someone still owes work against. The
  selection is on `post_closeout_result`, not on the presence of an exception
  block: `retain-exception` makes that block mandatory, so presence alone would
  also admit the settled record AC28 excludes.
- [x] **AC28 — Finished work is not a due review.** A
  `("retain-exception", "Retired")` record with `review_on = "2026-08-01"` at
  injected instant `2026-08-30T00:00+08:00` contributes no object to
  `cooling.due` and none to `cooling.exceptions`, and its `cooling.records`
  object carries `due` as `false`.
- [x] **AC29 — Closeout facts are projected.** For the AC23 fixture under
  `reconcile`, the `closeout` object has exactly the keys `paused`,
  `all_specs_shipped`, `closeout_blockers`, `initiative_eligible`,
  `next_action`, and `cooling_context_visible`.
- [x] **AC30 — A paused initiative changes the next action.** With the active
  initiative's pause overlay set, `closeout.next_action` is
  `resume-or-keep-paused`.
- [x] **AC31 — An unshipped spec becomes a blocker.** With one queued Approved
  spec and no pause, `closeout.closeout_blockers` contains `unshipped-specs`.
- [x] **AC32 — All-shipped unpaused work invites closeout.** With every spec in
  the active initiative Shipped, no pause, and no blockers,
  `closeout.next_action` is `invoke-close-work`.
- [x] **AC33 — The exclusion claim is earned, not declared.** Under both
  `status` and `reconcile`, `closeout.cooling_context_visible` is `false` for
  the AC23 fixture and `true` for the AC5, AC8, AC9, and AC38 fixtures.
- [x] **AC34 — An unrelated refusal does not flip the claim.** For the AC23
  fixture plus one locator-only workspace entry that yields a
  `configuration_mismatch` finding, `closeout.cooling_context_visible` is
  `false`.
- [x] **AC35 — Only ordinary orientation carries the new keys.** Neither the
  `explain` JSON nor the `repair-plan` JSON for the AC23 fixture contains a
  top-level `cooling` key or a top-level `closeout` key.
- [x] **AC36 — Explain mode excludes too.** The AC17 fixture run through
  subcommand `explain` yields `canonical.evaluations` containing no item whose
  `path` is `docs/specs/alpha/spec.md`.

### Module loading

- [x] **AC37 — The packaged runtime carries the whole closure.** Each of
  `cooling.py`, `close_work.py`, and `file_safety.py` exists under
  `packages/agentbundle/agentbundle/_data/` with bytes equal to its counterpart
  under `packs/core/.apm/skills/close-work/scripts/`.
- [x] **AC38 — Every resolution route failing is named, not silent.** With all
  four resolution routes unavailable, `canonical.findings` carries exactly one
  entry whose `code` is `cooling_state_unavailable`, `cooling.records` is an
  empty list, and no exception is raised.
- [x] **AC39 — A failed cooling resolution costs nothing else.** For the AC38
  fixture built with one shaping-ready entry, one `[backlog].open` entry, and one
  Shipped-but-queued spec, `shaping.ready`, `shaping.top_level_backlog`,
  `reconciliation.type2_cleanup_ops`, and `repair-plan`'s `automatic_operations`
  are each non-empty in the working-module control run and identical to it in the
  failed run.
- [x] **AC40 — An escaping module candidate is not executed.** For each of the
  three filesystem candidates in turn, with
  `AGENTBUNDLE_ALLOW_DEV_SOURCE_AUTHORITY` set to `1` and that candidate's module
  body writing a marker file unique to the run: the marker is absent and the
  cooled set is still resolved when the candidate's real path lands outside its
  declared root, and present when it lands inside.
- [x] **AC41 — The packaged closure opens nothing outside itself.** With
  `close_work.py` loaded from a `_data/`-shaped directory and a loadable
  `work-intake/scripts/surface_resolver.py` planted at the path its `SKILLS_DIR`
  resolves to, calling `close_work.surface_resolver()` raises `ImportError` and
  the planted module's on-import marker is not written. The same fixture in a
  `skills/<skill>/scripts` layout returns the resolver and writes the marker, so
  the criterion pins containment rather than a call that always refuses. The
  planted module defines every name the loader requires, which keeps the refusal
  attributable to the layout and not to an incomplete module.

### Delegation and the guard

- [x] **AC42 — Dueness is answered in the recorded zone.** A `Cooling` record
  with `review_on = "2026-08-31"` and `timezone = "Asia/Singapore"`, at injected
  instant `2026-08-30T16:30:00+00:00`, projects `due` as `true`.
- [x] **AC43 — The production clock path works.** With no injected instant and a
  `Cooling` record whose `review_on` is `2020-01-01`, `cooling.due_count` is 1.
- [x] **AC44 — A non-boolean visibility fact is still refused.**
  `project_closeout_status(paused=False, all_specs_shipped=True, closeout_blockers=[], cooling_context_visible="no")`
  raises `ValueError`.

### Surfaces

- [x] **AC45 — Wave 4's refusal test is replaced, not deleted.**
  `packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py`
  no longer defines `test_workspace_status_refuses_wave6_context_exclusion` and
  does define a test asserting the AC44 refusal; its other test functions are
  unchanged.
- [x] **AC46 — Both new finding codes are documented where the gate looks.**
  `packs/core/.apm/skills/workspace-status/SKILL.md` and
  `guides/core/reference/workspace-toml-schema.md` each carry a row with a
  reason and a next action for `invalid_lifecycle_record` and for
  `cooling_state_unavailable`.
- [x] **AC47 — The Wave 6/7 boundary statement is amended, not deleted.**
  Whitespace-normalized, `docs/architecture/work-intake-and-artifact-routing.md`
  contains `Wave 6 has shipped ordinary-context exclusion` and `Wave 7 owns
  historical migration and pruning behavior`, and does not contain `Wave 6 and 7
  own ordinary-context exclusion`.
- [x] **AC48 — Deleting either statement reddens the roster test.**
  `tests/roster/test_wave4_durable_outputs_and_release.py` asserts both AC47
  strings against `docs/architecture/work-intake-and-artifact-routing.md`'s text
  alone, and removing either one makes that test fail.
- [x] **AC49 — The reference guide states exclusion, not visibility.**
  Whitespace-normalized,
  `guides/core/reference/work-intake-routing-and-lifecycle.md` does not contain
  `closeout blockers, cooling visibility` and does contain `never loads a cooled
  artifact body`.
- [x] **AC50 — The skill's prose matches shipped behaviour.**
  Whitespace-normalized,
  `packs/core/.apm/skills/workspace-status/SKILL.md` does not contain `remains
  visible because ordinary-context exclusion is not part of this wave` and does
  contain `Cooling context is excluded from ordinary orientation`.
- [x] **AC51 — Both follow-ons carry a durable pointer.** `spec.md`'s
  `## Follow-ons` table names `cooling-repair-migration-scope` and
  `wave6-dependency-scoped-completion-receipts`, each with an owner, and the
  spec carries no `(deferred:` marker on any Acceptance Criterion line. The Follow-ons prose names the token to explain why this spec does not use one, so the check is per criterion line rather than per file.
- [x] **AC52 — Wave 4's frozen spec is untouched.**
  `docs/specs/close-work-extraction-and-immediate-disposition/spec.md` has
  SHA-256 `4f1b98e7fdb53a4726a65432ef2993a7f0db1f65987c46bd00763a999915de8a`.
- [x] **AC53 — The release surface agrees.** `packs/core/pack.toml`,
  `packs/core/.claude-plugin/plugin.json`, and the topmost dated `[core]`
  heading in `docs/product/changelog.md` carry one identical version whose
  parsed `(major, minor, patch)` tuple is strictly greater than `(2, 16, 1)`.
- [x] **AC54 — The projections match their source.**
  `.claude/skills/workspace-status/scripts/workspace_status_engine.py` and
  `.agents/skills/workspace-status/scripts/workspace_status_engine.py` have
  bytes equal to the `packs/core` source.

### Dependency safety

- [x] **AC55 — Cooling never satisfies a blocked dependency.** A queued spec
  declaring a dependency that is both named by a `Cooling` record and present in
  `structurally_blocked_paths` is absent from `canonical.ready`, and
  `canonical.findings` carries an `unsatisfied_dependency` entry for that path.
- [x] **AC56 — Cooling never satisfies an unclosed defect dependency.** A queued
  spec declaring a `defect`-kind dependency named by a `Cooling` record, with no
  `backlog.closed` membership, is absent from `canonical.ready`. A cooled
  dependency is otherwise satisfied from its lifecycle record whatever its kind,
  so the defect gate is the closed membership and never the kind alone.
- [x] **AC57 — A cooled cross-repo dependency is refused without a read.** A
  queued spec declaring a `cross-repo` dependency whose `containing_brief` is
  named by a `Cooling` record is absent from `canonical.ready`, and
  `canonical.findings` carries an `unsatisfied_dependency` entry for that path.
  Without the record the same fixture reports `invalid_receipt`, a code only
  `_cross_repo_receipt_satisfied` emits, and that function is not entered on the
  cooled run. Absence of the brief from disk is not evidence here: an
  unresolvable locator also leaves the cooled set. The lifecycle record
  cannot satisfy this dependency: its evidence is the four-field receipt match
  carried in the brief body, and projecting that receipt is deferred to Wave 7
  by `wave6-dependency-scoped-completion-receipts`.
- [x] **AC58 — No live initiative means no `closeout` block.** With every
  initiative `closed`, the `reconcile` and `status` JSON carry no `closeout` key
  at all, while `cooling` is still present. Synthesizing the block from the
  absent initiative reported a `closeout_blockers` entry of `unshipped-specs`
  against a workspace with no unshipped spec. Omission rather than an empty
  block keeps AC29's closed key set unchanged.

### Brief child scope under cooling

- [x] **AC59 — A cooled child a brief declares does not change either conclusion
  about that brief.** With `docs/specs/child/spec.md` in `work.shipped`
  declaring `source.parent = "docs/product/briefs/b.md"`, `b.md` in
  `brief_queue.shipped` and healthy, and a queued spec carrying a
  `kind = "brief"` dependency on `b.md`: without a lifecycle record the
  dependant is in `canonical.ready` with no finding on `b.md`; with a `Cooling`
  record for the child the dependant is absent from `canonical.ready` and
  `canonical.findings` carries `unsatisfied_dependency` for `b.md`. The record
  must not instead promote a blocked spec by fabricating the child's state from
  its collection — `_membership_status` returns `Shipped` for anything in
  `work.shipped` whatever the body says.

  The fail-closed set is exactly the briefs named by a cooled child's
  `source.parent`. A cooled spec that declares no `source.parent` marks nothing:
  with such a spec cooled, an unrelated healthy brief in the same initiative
  keeps its dependant in `canonical.ready` and carries no finding. Attributing
  those conservatively would refuse every brief dependency whenever any ordinary
  spec cooled — 81 of 92 specs in this repository's main initiative declare no
  `source.parent` — so the gap is left open and recorded as
  `cooling-brief-child-scope` rather than closed at that cost.

