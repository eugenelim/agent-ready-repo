# Spec: Cooling brief child scope closure

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 §6 and §7 and its 2026-09-03 Errata, which scope Wave 7b to the read-free parent link; [ADR-0106](../../adr/0106-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md), which decides the three answers and licenses the `Status` pointer this delivery writes; `status-projection-and-context-exclusion`, Shipped and frozen, which owns the child-state set and the AC59 half ADR-0106 supersedes; `workspace-routing-invariants`, Shipped and frozen, whose § *Ask first* governs a new finding code and whose § *Always do* requires the smallest safe next action; `thirty-day-cooling-and-retirement`, Shipped and frozen, which owns what cooling means
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/jsonschema/workspace-entry.schema.json` — read, not modified
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A cooled spec's workspace entry answers "is this spec a child, and of what?"
without opening the artifact, which is the one thing cooling forbids.
`source.parent` carries three answers. [ADR-0106](../../adr/0106-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md)
§ *The decision, stated as the three answers* is their one home and states each answer
with its consequence; this spec does not restate them.

Unknown scope is a fact about one entry, and declaring a value clears it. A
maintainer closing out an artifact declares `source.parent` as part of that
closeout; the question is asked only of entries that have cooled, so no bulk
migration exists. That obligation reaches a maintainer in three places: the adopter closeout
procedure, the `parent` field's reference entry, and the finding's own next
action.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — reversing part of a ticked criterion in a frozen spec is licensed only by an ADR pointer, and admitting a finding code is an `Ask first` boundary | [ADR-0106](../../adr/0106-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md); `notes/ask-first-review.md` | Approver | *The pointer takes the licensed form* | The ADR is Accepted and the pointer resolves |
| Current architecture | Applicable — a reader arriving at the frozen Wave 6 spec must not follow a rule the repository no longer keeps | `docs/specs/status-projection-and-context-exclusion/spec.md`, `Status` token only | Spec owner | *The frozen body is otherwise unchanged*; *Both sites pinning the edited file carry its new digest*; *The three superseded Wave 6 cases are updated, not deleted* | The frozen body is unchanged apart from that line |
| Interface compatibility | Applicable — `cooled_child_scope_unknown` joins the public refusal contract | `packs/core/.apm/skills/workspace-status/SKILL.md`; `guides/core/reference/workspace-toml-schema.md` | `workspace-status` owner | *The code is documented where the gate looks*; *The next action says when the empty answer is correct* | Both rows resolve and the documentation gate is green |
| Reusable learning | Applicable — the derivation basis these criteria are read off | `notes/probes.md` | Spec owner | Each probe records the construction that produced it, runnable from the repository root | Every probe's construction re-runs; a probe's recorded output is the engine state at the time it ran, which this delivery deliberately changes for several of them |
| Release history | Applicable — a non-cosmetic core pack change | `docs/product/changelog.md`, topmost dated `[core]` heading | Release owner | *This delivery moved the release surface* | The heading is topmost and the release surfaces agree |
| User documentation | Applicable — the adopter `cool-30-days` procedure gains a precondition, and the `parent` field's reference entry gains a cooling interaction | `guides/core/how-to/close-and-disposition-work.md`; `guides/core/reference/workspace-toml-schema.md` | `workspace-status` owner | *The adopter closeout procedure states the precondition*; *The `parent` field's reference entry states the cooling interaction* | Both surfaces state the obligation |
| Operations, current product truth | Not applicable — reconciliation stays offline, adds no filesystem read, and no runtime or deployment surface changes | — | — | — | — |

## Boundaries

### Always do

- Decide a cooled entry's parent scope from `source.parent` and the brief memberships in `workspace.toml`, never from the artifact body or the collection. `workspace-routing-invariants` § *Never do* owns the general rail over comments, `summary`, list order, tracker labels, nearby prose and prior-session memory; this line adds only the two sources specific to a cooled artifact.
- Fail closed when scope is unestablished, and name the entry that needs repair with its smallest safe next action.
- Treat any value `_normalized_optional_artifact_value` reduces to empty as the empty answer, so the entry and the body normalize alike.
- Leave in place every precedence that already decides a dependency ahead of this refusal. The cooling-relevant ones are a `cross-repo` receipt, a cooled brief's own lifecycle record, and a metadata-safety finding for a brief that is missing, unreadable, or invalid-path; a `kind` mismatch also returns earlier. The rail is that none of them moves, not that there are exactly three.
- Ship every projection byte-equal to its source in the commit that changes the source, and carry an `Engine-Change-RFC: 0096` trailer on whichever commit touches `packages/agentbundle/`.

### Ask first

- Add a finding code. Granted 2026-09-03 for `cooled_child_scope_unknown`; recorded in `notes/ask-first-review.md`.
- Reverse any part of a ticked criterion in a frozen spec. Granted 2026-09-03 for AC59's undeclared half; recorded in ADR-0106.
- Change an acceptance criterion belonging to a live sibling delivery. Granted 2026-09-04 for `cooling-scope-closure`'s AC23 digest row naming `status-projection-and-context-exclusion/spec.md`, which the `Status`-line edit necessarily invalidates; recorded in `notes/owner-decisions.md`.
- Change an existing finding code's meaning or its set of emitters.
- Attribute an unknown cooled child to a named brief by inference rather than declaration.
- Modify `contracts/jsonschema/workspace-entry.schema.json`.

### Never do

- Read a cooled artifact's body, or restore a body-dependent predicate for a cooled entry.
- Emit the new finding from a site that adds the entry to `structurally_blocked_paths`; that widens the refusal past `kind = "brief"`. `plan.md` § *Constraints* names the site.
- Broaden `invalid_receipt`, whose single-emitter property `status-projection-and-context-exclusion` AC57 asserts as a ticked criterion.
- Edit a frozen spec's body — `spec.md`, `plan.md`, or `notes/` — in `status-projection-and-context-exclusion`, `thirty-day-cooling-and-retirement`, `close-work-extraction-and-immediate-disposition`, `workspace-routing-invariants`, or `dependency-scoped-completion-receipts`. The `Status` token is the sole exception, under the grant above.
- Change any part of `cooling-scope-closure` other than the one AC23 digest row named in the grant above. That spec is `Implementing`, so `docs/CONVENTIONS.md:119-129` pins it in substance even though it is not frozen.
- Add a module, layer, dependency, or top-level directory. Adding a field to `contracts/jsonschema/workspace-entry.schema.json` is governed by the `Ask first` entry above, which is the single rail for that file; no other schema gains a field.
- Edit `delivery-lifecycle-record.schema.json`, which RFC-0096's 2026-09-03 Errata implicates through `lifecycle-record-reclassified-gap`, or `close_work.py` and `cooling.py`, which the concurrent Wave 7c delivery holds and has not accepted work on from this delivery.
- Claim what a shipped function emits without constructing it and printing the result.

## Testing Strategy

Criteria fall in three groups, each with its own mode, observable and evidence
home.

**Group 1 — parent-scope resolution (the read-free parent scope criteria): TDD.**

- Each criterion states its whole fixture: the brief's collection and body
  status, and for each spec its collection, body status, body brief link and raw
  `source.parent`, plus which locators carry a `Cooling` record, any dependency's
  kind, and whether a sibling `plan.md` exists. Those axes determine the
  observable, so each is a literal.
- Observable shapes: a named finding code at a named path, or membership of
  `canonical.ready`.
- `notes/probes.md` probe 14 records the construction and unfiltered output of
  every one of these fixtures; the criteria are transcribed from it rather than
  citing it. Evidence home: the new suite at
  `tests/roster/test_cooling_brief_child_scope_closure.py`.
- Every criterion in this group carries a control that is a neighbouring value
  of the same axis, never the absence of the change. A control producible only by
  removing the change under test proves nothing about it.
- No criterion in this group is satisfied by an absence alone, because the defect
  being closed is an empty set reading as compliance. One asserting a finding is
  absent names the code whose presence falsifies it, so the assertion has a
  failing state.
- Every refusal in this group is paired with a positive path — a representative
  valid input that must succeed — so the contract is not one-sided.

**Group 2 — the supersession and the surfaces: goal-based.**

- Observable shapes: a digest or byte comparison, a literal string in a named
  file, a parsed version tuple, or a set-uniqueness property.
- Each is checkable by one command over committed state, so the evidence home is
  the gate output recorded in the pull request rather than a fixture. Three of
  them compare against this branch's merge base with `origin/main`.
- These criteria carry no fixture and therefore no neighbouring-axis control;
  their controls are the merge-base and pre-edit values they compare against.

**Group 3 — the built artifact: goal-based, over a subprocess.**

- `workspace_status.py reconcile` runs from inside the checkout, against a
  fixture carrying an unestablished cooled child. The run location is part of the
  observable, so the criterion drives the shipped script as a subprocess under
  `sys.executable` and reads its exit code and parsed stdout — the pattern three
  shipped roster suites already use. Evidence home: the suite. Nothing here is
  attested by hand: a criterion whose only witness is a written note cannot fail
  once the pull request closes.

## Acceptance Criteria

Every fixture places the brief at `docs/product/briefs/brief-1.md`, gives every
spec a sibling `plan.md`, and uses `("cool-30-days", "Cooling")` records.

Three fixtures are shared, and are named rather than numbered so that
renumbering a criterion cannot silently redirect another criterion's inputs. All
three place the brief in `brief_queue.shipped` with body `Status: Shipped`; put
`docs/specs/child/spec.md` in `work.shipped` with body `Status: Shipped`; put
`docs/specs/dependant/spec.md` in `work.queue` with body `Status: Approved`, body
brief `none`, entry omitting `source.parent`, and a `kind = "brief"` dependency on
the brief; and carry one `Cooling` record naming the child. They differ only in
the child's declaration:

| Fixture | Child's entry `source.parent` | Child's body brief |
| --- | --- | --- |
| **Declared** | the brief | the brief |
| **Empty** | `none` | `none` |
| **Absent** | the key is omitted | `none` |

A criterion below states its fixture by name plus every axis it changes. Where a
criterion removes the dependant, it says *the dependant entry is absent* — the
entry is not present with an empty `needs`, which is a different fixture.

### Read-free parent scope

- [ ] **AC1 — A declared, resolving parent marks its brief.** The **Declared**
  fixture: the queued spec is absent from `canonical.ready` and
  `canonical.findings` carries `unsatisfied_dependency` at the brief's path.
  Without the `Cooling` record the queued spec is present and
  `canonical.findings` is empty.
- [ ] **AC2 — A declared empty parent marks nothing.** The **Empty** fixture:
  the queued spec is present in `canonical.ready` and `canonical.findings` is
  empty.
- [ ] **AC3 — An absent parent on a cooled entry is named.** The **Absent**
  fixture: `canonical.findings` carries exactly one
  `cooled_child_scope_unknown`, at `docs/specs/child/spec.md`.
- [ ] **AC4 — Unestablished scope refuses a brief dependency.** For the
  **Absent** fixture the queued spec is absent from `canonical.ready` and
  `canonical.findings` carries `unsatisfied_dependency` at the brief's path. For
  the **Empty** fixture it is present.
- [ ] **AC5 — The parent is read from the entry, never the body.** The
  **Absent** fixture with the child's body brief set to the brief and the
  dependant entry absent: `canonical.findings` carries exactly one
  `cooled_child_scope_unknown`, at the child's path.
- [ ] **AC6 — A declared parent resolving to no membership is unestablished.**
  The **Absent** fixture with the child's entry `source.parent` set to
  `docs/product/briefs/Brief-1.md` while the registered membership is
  `docs/product/briefs/brief-1.md`: `canonical.findings` carries exactly one
  `cooled_child_scope_unknown`, at the child's path.
- [ ] **AC7 — The answer is per entry.** The **Empty** fixture plus
  `docs/specs/other/spec.md` in `work.shipped`, body `Status: Shipped`, body
  brief `none`, entry omitting `source.parent`, with `Cooling` records naming
  both specs and the dependant entry absent: `canonical.findings` carries
  exactly one `cooled_child_scope_unknown`, at `docs/specs/other/spec.md`.
- [ ] **AC8 — Unestablished scope does not refuse a non-brief dependency.** The
  **Absent** fixture with its queued spec replaced by `docs/specs/second/spec.md` in
  `work.queue`, body `Status: Approved`, body brief `none`, entry omitting
  `source.parent`, carrying a `kind = "spec"` dependency on
  `docs/specs/child/spec.md`: `canonical.ready` contains
  `docs/specs/second/spec.md`.
- [ ] **AC9 — Unestablished scope reports itself and suppresses nothing.** Brief
  in `brief_queue.executing`, body `Status: Executing`. Child in `work.shipped`,
  body `Status: Approved`, body brief `none`, entry omitting `source.parent`. `docs/specs/dependant/spec.md` in `work.queue`, body
  `Status: Approved`, body brief `none`, entry omitting `source.parent`, carrying
  a `kind = "brief"` dependency on the brief. A record naming the child. `canonical.findings` carries one
  `cooled_child_scope_unknown` at the child's path and one
  `impossible_transition` at the brief's. With the child's body brief and entry
  `source.parent` both set to the brief instead, it carries neither.
- [ ] **AC10 — An attributed cooled child still suppresses its parent's
  violation.** Brief in `brief_queue.executing`, body `Status: Executing`. Child
  in `work.shipped`, body `Status: Approved`, body brief and entry
  `source.parent` the brief. `docs/specs/second/spec.md` in `work.queue`, body
  `Status: Approved`, body brief and entry `source.parent` the brief. A record
  naming the child, and no dependency anywhere. `canonical.findings` carries no
  `impossible_transition` at the brief's path. Without the record it carries
  exactly one there.
- [ ] **AC11 — A cooled brief is satisfied ahead of the refusal.** The
  **Absent** fixture with a second `Cooling` record naming the brief: the queued
  spec is present in `canonical.ready`.
- [ ] **AC12 — An uncooled entry disagreeing with its body is named.** The
  **Absent** fixture with the child's body brief set to the brief and **no**
  `Cooling` record, and again with the child's entry `source.parent` set to
  `none` instead of omitted: `canonical.findings` carries one
  `provenance_mismatch` at the child's path and no
  `cooled_child_scope_unknown`.
- [ ] **AC13 — An uncooled entry agreeing with its body is not named.** The
  **Empty** fixture with **no** `Cooling` record: `canonical.findings` carries no
  `provenance_mismatch` entry at the child's path.

### The Wave 6 supersession

- [ ] **AC14 — The pointer takes the licensed form.**
  `docs/specs/status-projection-and-context-exclusion/spec.md`'s
  `- **Status:**` line reads `Shipped (superseded in part by ADR-0106 — ` then a
  clause naming `AC59`, then `; everything else stands)`.
- [ ] **AC15 — The frozen body is otherwise unchanged.** Substituting that
  file's `- **Status:**` line with the content that line has at this branch's
  merge base with `origin/main` yields a file byte-identical to that merge-base
  content.
- [ ] **AC16 — Both sites pinning the edited file carry its new digest.**
`cooling-scope-closure`'s AC23 pins file digests in two
  places — the dict in `tests/roster/test_cooling_scope_closure.py` and the table
  in `docs/specs/cooling-scope-closure/spec.md`. Both hold, for
  `docs/specs/status-projection-and-context-exclusion/spec.md`, that file's
  SHA-256 after its `Status`-line edit; neither retains
  `2cac21ca5f84e0f4e477a6bab432429a55034f6851dc152cfcd93611e9e3523d`, and
  `tests/roster/test_cooling_scope_closure.py` passes.
- [ ] **AC17 — The three superseded Wave 6 cases are updated, not deleted.**
  `tests/roster/test_status_projection_and_context_exclusion.py` still defines
  `test_a_cooled_parentless_spec_leaves_an_unrelated_brief_alone`,
  `test_cooled_parentless_child_scope_residual_is_pinned` and
  `test_unrelated_cooled_spec_does_not_affect_different_initiative_brief`; none
  carries the string `the residual is closed`; and against that file's
  merge-base content the only changed regions are those three function bodies
  and the two fixture helpers this delivery extends, `_brief_workspace` and
  `_cool_child`.

### Surfaces

- [ ] **AC18 — The code is documented where the gate looks.**
  `packs/core/.apm/skills/workspace-status/SKILL.md` and
  `guides/core/reference/workspace-toml-schema.md` each carry a row for
  `cooled_child_scope_unknown` with a reason and a next action.
- [ ] **AC19 — The next action says when the empty answer is correct.** That
  code's value in `_FINDING_NEXT_ACTIONS` in
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`,
  and both documentation rows'
  next actions each contain the literal
  `only when that spec has no parent brief`.
- [ ] **AC20 — Every projection matches its source.** Every file
  `FORCE=1 make build-self` writes for the `workspace-status` skill is byte-equal
  to its counterpart under `packs/core/.apm`, and re-running that command
  produces no further change.
- [ ] **AC21 — This delivery moved the release surface.** `packs/core/pack.toml`,
  `packs/core/.claude-plugin/plugin.json` and the topmost dated `[core]` heading
  in `docs/product/changelog.md` carry one identical version, whose
  `(major, minor, patch)` tuple is strictly greater than the tuple in
  `packs/core/pack.toml` at this branch's merge base with `origin/main`.
- [ ] **AC22 — The eval harness names the code.**
  `packs/core/.apm/skills/workspace-status/evals/evals.json` carries an eval
  whose `expected_output` names `cooled_child_scope_unknown`.
- [ ] **AC23 — The eval ids stay distinct.** Every `id` in that file's `evals`
  list occurs exactly once.

- [ ] **AC24 — The adopter closeout procedure states the precondition.**
  `guides/core/how-to/close-and-disposition-work.md`'s `cool-30-days` row
  contains the literal `declare source.parent on its workspace entry`.
- [ ] **AC25 — The shipped command emits the finding.**
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py reconcile
  --root <fixture>`, run from inside this checkout against the **Absent**
  fixture, exits 0 and its stdout carries a `canonical.findings` entry whose
  `code` is `cooled_child_scope_unknown`. Probe 16 establishes both halves of
  that shape against the shipped script: exit 0 holds with a finding present, and
  the code is reachable at `canonical.findings[].code`.
- [ ] **AC26 — The `parent` field's reference entry states the cooling
  interaction.** `guides/core/reference/workspace-toml-schema.md`'s `parent` row
  contains the literal `unestablished once the spec has cooled`.

## Follow-ons

| Slug | Outcome | Owner |
| --- | --- | --- |
| `cooled-parent-scope-declaration-writer` | Decide which workflow stamps `source.parent` at closeout while the body is still readable, and whether it refuses an empty value that contradicts a body-declared brief — which is what would make the empty answer verified rather than trusted. `close-work` is the natural home, and this delivery may not edit it. | Unassigned; routed through `work-intake` at the `[backlog].open` entry whose `path` is `notes/follow-ons.md` |

## Assumptions

- Technical: a parsed work entry retains `source.parent`'s raw value, so a declared empty value and an absent key are distinguishable without a schema change (source: `notes/probes.md` probe 1)
- Technical: the published `workspace-entry.schema.json` already admits every value these criteria use (source: `notes/probes.md` probe 2)
- Technical: an entry that declares no parent while its body declares one is already a live `provenance_mismatch` while uncooled, and that check is suppressed once the artifact cools (source: `notes/probes.md` probe 4)
- Technical: a declared value resolving to no brief membership escapes the refusal exactly as an absent key would, so resolution against memberships is part of the predicate (source: `notes/probes.md` probe 7)
- Technical: emitting the finding from a site that populates `structurally_blocked_paths` refuses non-brief dependants (source: `notes/probes.md` probe 8)
- Technical: `docs/lifecycle/` holds no records, so nothing has cooled and the refusal costs nothing on this checkout (source: `ls docs/lifecycle`)
- Technical: a finding's `detail` field reaches no consumer, so the two unestablished causes cannot be distinguished by it (source: `notes/probes.md` probe 10)
- Process: a new finding code needs a reason and a next action in both documentation homes in the same commit, because the shipped gate checks a superset over `set(engine._FINDING_NEXT_ACTIONS)` across both (source: `tests/roster/test_workspace_status_projection.py`)
- Process: reversing part of a ticked criterion in a frozen spec is licensed only by a `Status`-token parenthetical citing an ADR (source: `docs/CONVENTIONS.md:111` and `:143-185` § *Superseding a frozen document*; granted by the owner 2026-09-03, recorded in ADR-0106)
- Process: `tests/roster/` sits outside the frozen unit, which `docs/CONVENTIONS.md:119-121` scopes to the spec directory, so the three superseded Wave 6 cases may be updated
- Product: `cooled_child_scope_unknown` is the accepted code name (source: `notes/owner-decisions.md` § *2026-09-03 — `cooled_child_scope_unknown` is the code's name*)
