# Plan: Agent Skill Engineering Subagent and Plugin Concepts

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (runtime export boundary, version
  bump rule, no internal-governance citations under `packs/`);
  `guides/_shared/reference/catalogue-authoring-standards.md` (canonical pack
  authoring standards). Analogous production implementations:
  `docs/specs/agent-skill-engineering-composition-floors/` (admitted these
  topics and built the portability guard, and whose delivery record carries the
  pin re-take procedure) and
  `docs/specs/agent-skill-engineering-languages-and-execution/` (the last slice
  to re-measure both recorded runs). Construction path:
  `packs/agent-skill-engineering/tests/pack/` and
  `packs/agent-skill-engineering/tests/integration/`. Named uncertainty: which
  suite owns each new assertion — see T7's discovery predicate.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md`.

## Approach

The guard moves first. The shipped portability guard rejects any `plugin.json`
in a portable floor, so until it is conformed to its own frozen criterion, the
package-floor edit cannot land at all. T1 narrows it; T2 then states the plugin
core; T3 and T4 handle delegation and the runtime divergence.

The rest is ordering discipline. Six body edits land, then the declared-absent
register's retired-leaf rationale, then the repository surfaces that repeat the
retired forward pointer. Only after every body edit is final do the two recorded
retrieval runs get re-measured, because each edit moves the compiled source
digest both runs bind and a run recorded mid-sequence would have to be discarded.

Two things carry the risk. The shipped inherited-pin fixture asserts its pinned
selections against the *current* measurement, so a re-measurement that moves a
pinned selection cannot be papered over — the composition-floors and languages
slices already met this, and the owning slice's delivery record names each
re-taken pin with its prior and current value, so T2 follows that procedure rather than
inventing one. And placement: the plugin core is portable because a published
specification fixes it, while the manifest *location* Claude Code uses is not,
and putting either in the other's topic is the failure this slice corrects.

No new dependency, module, directory, or provider-seam change. One Python
predicate moves — the portability guard in T1 — and everything else is corpus
prose, recorded evidence, and the assertions over them. The release surface is a
patch bump, because the pack gains no primitive.

## Constraints

- [RFC-0097](../../rfc/0097-agent-skill-engineering.md) § *Errata*, 2026-09-01:
  a capability whose behavior a specification fixes does not take a
  runtime-profile row, and a profile covers only the unspecified and the
  delegated surfaces. This is the authority that moves the plugin core into the
  portable floor.
- RFC-0097 § *Errata*, 2026-09-04: the runtime profiles beyond Claude Code are
  retired to open extension. This is the authority for T5 and T6.
- RFC-0097 § *D8* and the 2026-08-28 erratum: each claim group declares exactly
  one basis with that basis's evidence. Its mechanical half is owned by
  `test_corpus_admission.py::test_every_claim_group_declares_a_basis_and_its_fields`;
  this plan fixes which basis each group declares, and T2 and T3 record those
  choices rather than deferring them to execution.
- `packs/AGENTS.md`: `.apm/` is the runtime export boundary and self-host runs
  after pack edits; shipped pack content carries no internal-governance
  citations; a non-cosmetic pack change bumps `pack.toml` and
  `.claude-plugin/plugin.json` in lockstep.
- **Any task that edits authored OKF source recompiles the generated tree and
  re-records both retrieval runs before it closes.** `source_digest` is a digest
  over authored source bytes, and the doctrine projection reads the compiled
  body, so a task that edits source and does neither leaves the repository red
  either way — the projection fails without a recompile, and the recorded-run
  digests fail with one until new evidence is bound. The two steps travel with
  the edit; they are not a later task.
- `docs/specs/agent-skill-engineering-composition-floors/spec.md` is Shipped and
  frozen. Its AC4 states the portability rule the guard implements and its AC5
  states the subject-coverage rule; both keep their current force. No ticked
  criterion is amended, the ledger and its lifecycle states are untouched, and
  each floor's subject count and subject phrases stay as that slice left them.

## Construction tests

**Integration tests:** one new cross-cutting check spanning T2 and T6 — a
body-to-README agreement assertion, which fails when the README advertises the
plugin core and the package floor omits it. It reads both surfaces itself rather
than relying on any existing suite's artifact set, so it holds whatever that set
becomes.

**Named-reviewer readings:** AC2, AC10, AC11, AC12 and the AC13/AC14 pair each
have a semantic neighbour a predicate cannot decide — for AC13 and AC14 it is
whether the runtime vocabulary reads naturally to an author, which the spec's
Testing Strategy assigns to the same reviewer. `foundation-corpus-reviewer`
records a reading for each in the verification ledger, beside the gate result —
AC2 and AC14 in T2, AC13 in T4, AC10 in T5, AC11 in T6, AC12 in T7. The reading
never blocks a task, because the criterion's proxy is the gate, so each of those
tasks closes on its own suites and mutations and the ledger entry is a durable
note to the next author rather than an approval.

**Manual verification:** none. The retrieval re-measurement in T2 is a recorded
gesture, not a manual check: its evidence is every digest each run binds.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise / `packs/agent-skill-engineering/README.md` | T6 | Governed-topic count agreement, absence-claim scan, and the new body-to-README agreement check green | README describes the floors' plugin-core content and promises no later-slice profile |
| Current product truth / `packs/agent-skill-engineering/tests/fixtures/` | T2, T5 | Both recorded runs bind every digest their assertions require to the edited tree; register transcription matches the compiled register | Every digest matches the tree and case fixture it names |
| Current architecture / `docs/architecture/agent-skill-engineering.md` | T6 | Section names the shipped slice-3 surfaces and where the claim-state obligation sits | Document names no committed profile beyond Claude Code and stays `PLANNED` |
| Decision rationale / RFC-0097 § *Errata* (existing) | none | This spec's `Constrained by` header cites the erratum | No new ADR or RFC was recorded |
| Spec index / `docs/specs/README.md` | T8 | Row matches the shipped spec | Row states the shipped shape and final AC and task counts |
| Release history / changelog and both manifests | T8 | Matching patch bump; topmost pack changelog entry | Both manifests carry the same version and it equals the topmost pack changelog heading |
| Execution evidence / `notes/verification-ledger.md` | every task | Ledger names the guard-narrowing rationale, each observed mutation, the re-measurement gesture, every pin re-take with prior and current values, and each named-reviewer reading | Every task has its ledger entry, carrying the gate results that admitted it |
| Reusable learning / `project-knowledge` | work-loop | Capture receipts at `spec-approved` and `plan-locked` | Receipts exist or `project-knowledge unavailable` is recorded |

## Design (LLD)

### Design decisions

- **The guard is narrowed, not worked around.** The predicate is conformed to
  the contract it implements; the spec's Assumptions record the mismatch.
  Rejected: describing the manifest without naming it, because a filename rule
  stated without the filename gives an author nothing to act on.
  *Traces to:* AC4, AC1 · no `contracts/` file.
- **The plugin core enters the portable floor as a second claim group, not as a
  rewrite of the existing one.** The shipped group's basis is observed practice
  over a censused population and the plugin core is a published specification, so
  they cannot share a group. The shipped group's observations, applicability
  limit and revalidation trigger stay byte-identical; only the new group carries
  a promotion class.
  *Traces to:* AC1, AC2 · no `contracts/` file.
- **The new group's promotion class is `two-runtime-public-contract`, and all
  four behaviors sit in it.** The single-ecosystem class is closed to this topic
  by the admission suite, deliberately: an ecosystem is a product and this claim
  is not about one. The spec's Assumptions record both the evidence split and the
  owner reading that carries three of the four behaviors. Rejected: shipping the
  core as observed practice over this catalogue's own manifests, which reinstates
  the applicability limit the specification removes and describes one runtime's
  shape rather than the specification's; and narrowing the group to the two
  restated clauses, which drops the half most useful to an author.
  *Traces to:* AC1 · no `contracts/` file.
- **The delegation floor's new claims extend the shipped `observed-practice`
  group; no doctrine group is added.** The shipped group's applicability limit
  and revalidation trigger already scope them. A doctrine group would need two
  first-party runtime sources per clause that this slice does not have, and
  inventing them is the failure the spec's `Ask first` names.
  *Traces to:* AC5, AC6 · no `contracts/` file.
- **The divergence and the runtime vocabulary land in the Claude Code profile,
  not in the floors.** A manifest location is a dated runtime fact on the
  narrowed charter's delegated surface, so it is profile-eligible and
  floor-ineligible; the same placement makes the profile the only topic that may
  carry this runtime's component names at all.
  *Traces to:* AC7, AC8, AC13, AC14 · no `contracts/` file.

### Data & schema

Three fixtures change shape-preservingly and three do not change at all.
`topic-admission.json` gains one claim group under the package-floor topic and
extends the delegation floor's shipped group; its schema version and every other
group are untouched. Both recorded-run fixtures have every digest
field they declare rewritten in T2 along with their result arrays.
`declared-absent-register.json` does **not** change: the retired leaves stay
absent, so its declared count and leaf list are already correct and only the
register's prose rationale moves. `topology-leaves.json` does not change: no leaf
is admitted, retired, or renamed. The composition-floor subject fixture does not
change either, because the plugin core is content rather than a new subject.
*Traces to:* AC1, AC9, AC10 · no `contracts/` file.

### Behavior & rules

The doctrine projection rule decides how much of T2's record reaches the topic
body: for a `two-runtime-public-contract` group the admission suite requires the
group's clause, the topic's verification date, the revalidation trigger and every
cited source identity to appear inside a provenance block labelled with the
group's own name. That is the mechanism that makes the plugin-core clause visible
to a reader rather than living only in a fixture.
*Traces to:* AC1 · no `contracts/` file.

### Failure, edge cases & resilience

Pin drift is the designed-for failure. If T2's re-measurement moves any inherited
pinned selection, the pin fixture is updated to the new measurement **and**
the ledger names each moved pin with its prior and current value — the control
against an unrecorded re-take is the naming record, not the fixture. If
re-measurement drops the aggregate below a shipped precision or recall floor, the
prose is the cause and T2-T4 are revised before the run is re-recorded; lowering
a floor is out of scope.

The guard narrowing has its own failure direction: narrowed too far, a runtime's
own manifest filename reaches a portable floor. T1's rejection specimen is the
control for that direction and its admission specimen for the other.
*Traces to:* AC1-AC8 · no `contracts/` file.

### Dependencies & integration

The compiled tree under
`packs/agent-skill-engineering/.apm/skills/ase-okf-reference/` is a projection of
the authored `okf/` tree and is regenerated by the OKF compiler, never edited.
Self-host projection runs after the pack edits per `packs/AGENTS.md`. The roster
suite for the consumer-integrations slice reads this pack's manifest version and
requires it to equal the topmost pack changelog heading and exceed a recorded
floor, so T8's manifest and changelog edits are one commit.
*Traces to:* AC1-AC14 · no `contracts/` file.

## Tasks

### T1: The portability guard admits the specification's filename and still rejects a runtime's

**Depends on:** none

**Touches:** packs/agent-skill-engineering/tests/pack/test_composition_floors.py

**Verification mode:** TDD. The predicate has a compressible invariant, so both
controls are written before the pattern moves rather than fitted to whatever the
edited regex happens to do. Only the admitting control earns red: at the base
commit the class flags both the bare and the runtime-owned filename, so the
flagging control is green before and after and is an erosion control, not a
red-first one. Requiring red from both would mean breaking the flagging control
on purpose.

**Tests:**
- Two isolating controls on the narrowed class, one per direction. Both are
  required because a guard that flags every manifest filename satisfies the
  flagging control alone and a guard that flags nothing satisfies the admitting
  control alone. The admitting control is red at the base commit, which is the
  proof it tests the predicate and not the harness.
- `stub: true` — the seam is grounded, so the contract-surface assertion is
  exact. It asserts the guard's verdict over a specimen in the idiom the suite
  already uses for a class-isolating control — which classes fire on a specimen —
  rather than reaching into one class's compiled pattern, so an equivalent
  reimplementation of the predicate keeps it passing. Compiled and earned red
  from disposable scratch at PLAN, not written to a repository test file:

  ```python
  def _fired(specimen: str) -> list[str]:
      return [name for name, pattern in FORBIDDEN_IDENTIFIER_CLASSES
              if pattern.search(specimen)]

  def test_the_guard_admits_the_specification_filename() -> None:
      # red at the accepted base: `runtime-settings-file` fires on the bare name
      assert _fired("the manifest is plugin.json at the plugin root") == []

  def test_the_guard_flags_a_runtime_owned_manifest() -> None:
      # green before and after: the erosion control on the narrowed class.
      # Membership, not equality: this specimen names a runtime directory too,
      # so `runtime-config-directory` fires on it as well, correctly and
      # irrelevantly to this control. A measured probe of the base predicate
      # returned both class names for it, which is how the first draft of this
      # stub — asserting an exact single-element list — was caught.
      assert "runtime-settings-file" in _fired(
          "its manifest lives at .claude-plugin/plugin.json"
      )
  ```

  Both assertions were run against the base predicate before approval: the
  admitting one returned `['runtime-settings-file']` where it requires `[]`, and
  the flagging one held. The shipped specimen for this class,
  `"declare the matcher in settings.json"`, also stays flagged after narrowing,
  which is why the existing class-isolating control needs no edit.
- Mutation for the rejection direction: widen the narrowed pattern back to any
  `plugin.json` and confirm the admission control reddens. Mutation for the
  admission direction: replace the pattern with one that matches nothing and
  confirm the rejection control reddens.
- The suite's existing class-count pin stays green, which is the check that
  narrowing a class did not silently drop one.

**Approach:**
- Write both controls first and record the admitting control failing at the base
  commit.
- Narrow the `runtime-settings-file` class so it matches a runtime-owned manifest
  and not the specification's bare filename, keeping the class-as-a-rule shape
  that frozen AC4 requires rather than substituting a member list.
- Record in `notes/verification-ledger.md` that the guard was stricter than the
  criterion it implements, and that no ticked criterion was amended.

**Done when:** both controls are green, the stub's red was observed before the
predicate moved, each mutation is observed to fail the opposite control, and the
verification ledger carries the rationale.

### T2: The package floor states the plugin core, corrects the profile's manifest sentences, and rebuilds the compiled tree and both recorded runs

**Depends on:** T1

**Tests:**
- The corpus-admission suite is green with the package-floor topic carrying two
  claim groups of different bases. That suite checks each group's shape and
  projection; it holds no baseline of the shipped group's prior values, so
  preservation is verified by reading the diff of `topic-admission.json` and
  confirming the shipped group's three fields are byte-identical. Naming that
  explicitly, because an earlier draft claimed the suite enforced it.
- The doctrine projection assertion is the load-bearing one: it fails unless the
  new group's clause, the topic's verification date, its revalidation trigger and
  every cited source identity appear in a provenance block labelled with the new
  group's name. Mutation: drop one source identity from the body and confirm the
  projection assertion reddens.
- One containment assertion per behavior in AC1, each written against the value
  the criterion fixes rather than against wording chosen while authoring.
  Mutation: paraphrase one behavior so the fixed value is absent, and confirm
  that behavior's assertion reddens while the other three stay green.
- An absence assertion for the manifest-deferral sentences, written against a
  literal the neighbouring client-delegated sentence does not contain. Mutation:
  restore either deferral sentence and confirm it reddens.
- One containment assertion per client-delegated concern in AC3, over the closed
  set of seven the criterion enumerates. Mutation: drop `sandboxing` from the
  floor and confirm that member reddens while the other six stay green — without
  this, every other T2 check passes on a floor missing a delegated concern,
  because the frozen subject-coverage test reads a different set of subjects.
- The frozen subject-coverage assertions stay green, which is the separate check
  that the package floor's own seven subject phrases survived the rewrite. Those
  subjects and AC3's seven concerns are different sets that happen to be the same
  size.
- Every digest assertion on both recorded runs is green against the post-edit
  tree and their case fixtures. These cannot pass against pre-edit evidence, so
  they are the proof the runs were re-taken rather than carried forward.
- The aggregate precision, recall, exact-selection and bounded-selection floors
  hold, and every admitted topic still has at least two measured solo selections.
- The inherited-pin fixture agrees with the new measurement. Where a pin moved,
  the verification ledger names it with prior and current value.
- The shipped doctrine-projection assertion is green, which it can only be once
  the compiled body carries this task's new provenance block. That assertion is
  why the recompile belongs to this task: it reads the compiled tree, so no
  later task can discharge it.
- The projected-tree boundary guard
  `test_portable_tree_contains_no_adapter_or_publication_implementation` is green.
  It scans the projected tree, so like the doctrine projection it can only be
  judged after this task's recompile — which is why the profile's manifest
  correction lands here rather than in a preceding task that would leave a gate
  boundary red.
- An absence assertion over the authored profile body for the client manifest
  path, written as the literal that guard forbids, plus the AC7 containment
  assertion retargeted to the located-elsewhere statement and the AC14 assertion
  retargeted to the manifest's location rather than its path. AC8's consequence
  assertion is unchanged: it never named a client path.
- `no stub (implementation-discovered)` for these assertions' home — see T7's
  discovery predicate.

**Approach:**
- Add the doctrine claim group to `topic-admission.json` under the package-floor
  topic, sourced to the specification and both conforming runtimes, each source
  carrying identity, retrieval date and exposed-version state.
- Rewrite the floor's scope and provenance sections so the four
  specification-fixed behaviors are stated as portable and every
  client-delegated concern AC3 enumerates stays named as client-owned.
- Rewrite the Claude Code profile's manifest sentences so the divergence is
  stated by location, naming only the specification's own filename, and retarget
  the two assertions that keyed on the client path. This correction rides in this
  task because a preceding task editing authored source could not leave its own
  wave boundary green.
- Recompile the OKF tree; do not edit the compiled copy. This is the slice's last
  authored-source edit, so the recompile lands here.
- Re-run the router cases and the generic-negative cases against the recompiled
  router tree in an independent read-only subcontext, matching the
  `evaluation_mode` both fixtures declare.
- Record the results and recompute every digest field each fixture declares,
  reading the field set from the fixtures rather than from a count stored here.
- If the aggregate drops below a shipped floor, revise this task's prose and
  re-run; do not adjust a floor.

**Done when:** the pack suites are green including the doctrine projection, the
projected-tree boundary guard, and both recorded-run digest assertions, every mutation above is observed to fail,
the diff shows the shipped claim group's three fields byte-identical, and the
ledger records the re-measurement gesture and any pin re-take. The reviewer's AC2
and AC14 readings are recorded in the ledger and neither gates this task.

### T3: The portable delegation floor resolves without a runtime profile

**Depends on:** none

**Tests:**
- Absence assertion: the unanswered-question branch is not the only route to a
  resolution. It is written against a literal the floor's existing conservative
  default does not contain, because that sentence would otherwise satisfy a
  loose check. Mutation: revert the branch and confirm it reddens.
- Containment assertion for AC5's rule itself: the floor states that an
  unanswerable capability is treated as absent, and states that the operation
  stays in the parent. Without this the absence check above passes on a floor
  where the profile pointer was simply deleted and no rule replaced it, which is
  the likeliest wrong implementation. Mutation: delete the branch and add no
  rule, and confirm this assertion reddens while the absence assertion stays
  green.
- Containment assertion for the two-direction crossing statement, against the
  fixed outbound and inbound values AC6 names. Mutation: state only the outbound
  direction and confirm the inbound member reddens on its own.
- The shipped conservative-default assertion stays green, which is the check that
  the new resolution rule was added beside it rather than over it.

**Approach:**
- Add the resolution rule to the floor's decision section, keeping the eight
  capability questions and their existing phrasing.
- State the boundary crossing in both directions in the construction-method
  section. The tool-restriction caveat needs no edit: the security-and-authority
  section already states it, under the composition-floors slice's AC5; the spec's
  Assumptions record the observation that grounds this.
- Extend the shipped `observed-practice` group's coverage in
  `topic-admission.json` only where the new claims need it; add no doctrine group
  and no new source.

**Done when:** the pack suites are green and each mutation above is observed to
fail, recorded in the verification ledger.

### T4: The Claude Code profile carries the divergence and this runtime's vocabulary

**Depends on:** none

**Tests:**
- Two containment assertions, one for the manifest path (AC7) and one for the
  non-discovery consequence (AC8), because a profile can name the path and omit
  what follows from it. Mutation: state the path alone and confirm only the
  consequence assertion reddens. Both are read in paired with the portable floors' portability guard, which is
  what stops the fact being satisfied by putting it in the wrong topic. Mutation:
  move the sentence from the profile into the package floor and confirm the
  containment assertion reddens and the guard fires.
- The profile's existing `single-ecosystem-contract` group keeps its version
  range's lower and upper-or-open bounds, which the admission suite asserts.
- One containment assertion per vocabulary criterion: AC13's `agents/` and
  `skills/` checked against the passage stating delegation, AC14's
  `.claude-plugin/plugin.json` and `hooks/` against the passage stating
  packaging. Two assertions, because a profile can state one concept in runtime
  terms and the other generically. Mutation: replace one named surface with a
  generic term and confirm that member's assertion reddens while the others stay
  green, so the check cannot pass on a body that names only some of them.

**Approach:**
- Add the divergence to the profile body with the source identity, retrieval date
  and exposed-version state from the spec's Assumptions.
- State the delegation and packaging concepts through the runtime's own component
  surfaces, so the profile is the vocabulary surface the brief's slice row names
  and the floors stay vendor-neutral.
- Extend the profile's admission record only as the projection rule requires.

**Done when:** the pack suites are green and every mutation above is observed to
fail. The reviewer's AC13 and AC14 readings are recorded in the ledger and do not
gate this task.

### T5: The retired leaves record open extension and a satisfiable condition

**Depends on:** none

**Tests:**
- Register transcription stays green with no fixture edit, which is the check
  that the leaves remain absent rather than being accidentally admitted.
- Two assertions over the register body, one per criterion, both selecting
  leaves by the slug predicate AC9 fixes. AC10's assertion reads only whether a
  delivery slice is named; whether the replacement condition is meetable is the
  reviewer's recorded reading, not a check here. Selecting by the absence prose
  instead would let this task empty its own population by rewriting that prose,
  which is the defect the criterion's slug predicate exists to prevent.
- Mutations: restore one leaf's slice-reserved reason, then separately restore
  one leaf's slice-dependent admission condition, and confirm each reddens only
  its own assertion. A third mutation guards the selector: strip every runtime
  name from the reasons and confirm both assertions still select their leaves.
- The selector reads slugs from the compiled register rather than a list in the
  test, so a leaf added later is covered without editing the test.

**Approach:**
- Rewrite those leaves' `Why absent` and `What would admit it` prose in the
  authored register; leave every other leaf's rationale byte-identical.
- Recompile; confirm `declared-absent-register.json` and `topology-leaves.json`
  need no edit.

**Done when:** the pack suites are green, every redden-mutation above is
observed to fail independently, the selector-guarding mutation is observed to
leave both assertions still selecting their leaves, and `git diff` shows no
change to either fixture. The reviewer's AC10 reading is recorded in the ledger
and does not gate this task.

### T6: No repository surface promises a later runtime profile

**Depends on:** T2, T5

**Touches:** packs/agent-skill-engineering/README.md, docs/architecture/agent-skill-engineering.md, packs/agent-skill-engineering/tests/integration/test_provider_contract.py

**Tests:**
- Extend the shipped absence-claim tuple in the provider-contract integration
  suite with the register's and README's reserving sentences, exactly as AC11
  quotes them, matched against collapsed whitespace so a reflow cannot evade the
  check — that suite records why: some of its members were already dead to hard
  wrapping.
- A parallel assertion for the architecture document's reserving sentence, which
  the pack-scoped tuple does not reach. Each of the three comparisons comes from
  AC11's quoted text rather than from a tuple the test author assembles, so a
  sentence cannot drop out of the check between approval and execution. Mutation for both: restore one forbidden sentence in each
  surface and confirm each reddens independently, since a single control would
  pass on either surface alone.
- The new body-to-README agreement assertion from `## Construction tests`.
  Mutation: state the plugin core in the README and remove it from the floor, and
  confirm the assertion reddens where the existing suite stays green.
- The governed-topic count assertion stays green with no count change, which is
  the check that this slice admitted no leaf.
- Positive containment assertions for the three architecture facts the spec's
  Durable outputs row requires — which slice-3 surfaces exist, which runtime
  profiles are retired to open extension, and where the claim-state obligation
  sits. Without these, every other T6 check passes on a document that merely
  deleted its future-profile promise and said nothing in its place. Mutation:
  delete one of the three and confirm that member reddens while the other two
  stay green.

**Approach:**
- Update the README's knowledge-grounding paragraph to describe the floors'
  plugin-core content and drop the later-slice promise.
- Refresh the architecture document's slice-3 and runtime-profile sections to
  name what exists, what is retired to open extension, and where the claim-state
  obligation sits; leave its status `PLANNED`.

**Done when:** the pack, integration and roster suites are green and every
mutation above is observed to fail independently. The reviewer's AC11 reading is
recorded in the ledger and does not gate this task.

### T7: No concept prose advertises an unavailable authoring mode

**Depends on:** T2, T3, T4

**Tests:**
- Two specimens, because AC12's proxy forbids one thing and expressly permits
  its near neighbour. The rejected specimen directs a reader to invoke a mode the
  unsupported-mode fixture names; the accepted specimen names the same mode while
  explaining a concept. A membership test over the mode set satisfies the first
  and fails the second, which is the wrong implementation this pair exists to
  catch, so the predicate keys on the direction to invoke rather than on the mode
  name appearing.
- The assertion reads the mode set from
  `packs/agent-skill-engineering/tests/fixtures/unsupported-mode-cases.json`
  rather than from a literal list. Mutations, one per direction: add an
  invocation instruction and confirm the rejection specimen reddens; replace the
  predicate with bare name membership and confirm the accepted specimen reddens.
- The proxy is the closed verb set AC12 names, not a semantic reading. A
  recommendation phrased outside that set is a miss the reviewer records; the
  criterion says so, so the gate and the claim agree.
- The existing activation-description prohibition stays green, which is the check
  that this slice did not widen the workflows' advertised surface.
- Discovery predicate for this task's and T2's, T3's, T5's assertion homes: the
  suite that already reads the same artifact at the same altitude owns the new
  assertion — authored and compiled concept bodies belong to the corpus suites
  under `packs/agent-skill-engineering/tests/pack/`, the floors' portability and
  subject rules belong to the composition-floors suite, and cross-surface shipped
  statement agreement belongs to the integration suite. Constraint: no new test
  module unless all three existing homes read a different artifact. Required
  outcome: every new assertion has exactly one home and each fails under its
  stated mutation. Verification mode: goal-based.

**Done when:** the pack suites are green and both mutations are observed to fail
their own specimen. The reviewer's AC12 reading is recorded in the ledger and does
not gate this task.

### T8: The release surface is consistent

**Depends on:** T2, T6, T7

**Touches:** packs/agent-skill-engineering/pack.toml, packs/agent-skill-engineering/.claude-plugin/plugin.json, docs/product/changelog.md, docs/specs/README.md, docs/specs/agent-skill-engineering-subagent-and-plugin-concepts/notes/verification-ledger.md

**Tests:**
- The repository conformance check that both manifests carry the same version.
- The consumer-integrations roster suite, which reads this pack's manifest
  version and requires it to equal the topmost pack changelog heading and exceed
  the recorded floor. This is why the bump and the changelog entry are one commit
  rather than two.
- The spec-status lint over this spec and plan.

**Approach:**
- Patch-bump both manifests; the pack gains no primitive.
- Add one topmost changelog entry for the pack.
- Add this spec's row to the active-spec table with its shape and final AC and
  task counts.

**Done when:** conformance, roster and lint gates are green and the spec index row
states the final counts, recorded in the verification ledger.

## Rollout

Content and guard change, shipped in one commit series with no flag and no infra.
Rollback is a revert; nothing is irreversible because no consumer contract, no
provider field and no published version outside this pack moves. Deployment
sequencing has two hard edges: the guard narrowing precedes the package-floor
edit that would otherwise be rejected, and the recompile and retrieval
re-measurement travel inside the task that makes the last authored-source edit,
because the compiled body and the recorded digests must move together with it.

## Risks

- **The guard narrowing goes too far.** A pattern conformed to the criterion can
  also stop catching a runtime's own manifest. T1's rejection specimen is the
  control, and its mutation is what proves the control can fail.
- **Re-measurement moves an inherited pin.** Handled by the recorded re-take
  procedure rather than avoided; the cost is a ledger entry per moved pin. The
  procedure exists because a prior slice already used it.
- **New prose degrades retrieval precision.** The floors gain content on subjects
  neighbouring topics also touch, so the router may start selecting two topics
  where it selected one. The aggregate floors, not the author's judgement, decide
  whether that is acceptable, and the remedy is narrower routing signals in the
  edited bodies rather than a floor change.
- **The conformance reading is contested at review.** The owner decision that a
  client's declared conformance repeats the specification's clauses is what puts
  three of AC1's four behaviors in a two-runtime group. A reviewer may read the
  promotion class as requiring restatement in each runtime's own words. There is
  no in-plan fallback: AC1 requires all four behaviors and any valid
  implementation satisfies every criterion, so a rejected reading stops execution
  and takes the reviewed spec-amendment path rather than shipping a narrower
  group.
- **An absence assertion that shadows.** Several new assertions check that a
  sentence is *gone*, and a neighbouring sentence in the same section can satisfy
  a loosely written containment check. Every absence test above names the literal
  the neighbour does not contain, and each carries a restore-mutation.

## Changelog

Entries are per-decision, not per-review-round. Per-round entries three times
pushed this plan past twice its spec's length, and which round a change came from
is not what a later reader needs. The review artifacts under
`.context/reviews/` hold the round-by-round record.

- 2026-09-09: initial plan. A read-only probe established four facts that shaped
  it: the taxonomy is a closed leaf set partitioned by exclusive-or, so stating
  these concepts on shipped topics admits nothing; the admission suite iterates
  claim groups independently, so a topic may mix bases and the shipped group need
  not be touched; the single-ecosystem promotion class is closed to this topic,
  which selects the two-runtime class; and the inherited-pin fixture compares
  against the current measurement under a named re-take procedure, which turned
  re-measurement from a blocker into a costed task. The two corpus suites were
  green at the base commit, so a later red is attributable to this slice.
- 2026-09-09: **T1 leads, as TDD.** The shipped portability guard flags any
  `plugin.json` in a portable floor while the frozen criterion it implements
  forbids only a runtime-owned path, so without narrowing it the package-floor
  edit cannot land. Its predicate has a compressible invariant and a grounded
  seam, so the task carries a compilable stub asserting on the guard's verdict
  over a specimen rather than on one class's compiled pattern. Both assertions
  were measured against the base predicate: the admitting one returns
  `['runtime-settings-file']` where it requires `[]`, and the
  `.claude-plugin/plugin.json` specimen fires `runtime-config-directory` too —
  which is why the flagging assertion tests membership rather than an exact list,
  and why only the admitting control earns red. The spec's Testing Strategy
  carries the same asymmetry: an earlier wording obliged red-first in both
  directions, which no implementation could satisfy without regressing a green
  erosion control on purpose, so the mode now names the admitting direction as
  the red-first one and the flagging specimen as an erosion control proved by its
  own mutation.
- 2026-09-09: **the tool-allowlist criterion was deleted.** The delegation floor
  already ships that caveat and the composition-floors slice's AC5 owns the
  subject, so a criterion here would hold on the tree as authored and could never
  fail. The reason is under the spec's `## Follow-ons`, grounded in its
  `## Assumptions`.
- 2026-09-09: **adequacy is separated from detectability, and is advisory.** A
  criterion over authored prose fixes the value its check reads; the semantic
  neighbour a predicate cannot decide is a reading `foundation-corpus-reviewer`
  records in the ledger beside the gate result, never a gate. An earlier design
  made that verdict blocking, which is precisely the failure the authoring
  rubric's sixth class names. Six readings are routed: AC2 in T2, AC13 and AC14
  in T4, AC10 in T5, AC11 in T6, AC12 in T7.
- 2026-09-09: **execution evidence goes to `notes/verification-ledger.md`.**
  `docs/CONVENTIONS.md` assigns an execution-produced observation to that sibling
  ledger and describes no `qa.md` in the spec-directory layout; the ini-009
  slices carrying one are drift. The maintainer-procedure durable output
  collapsed to `none` in the same move, because AC9 already puts the admission
  condition into the corpus register and the re-measurement obligation belongs to
  the recorded-run digest assertions.
- 2026-09-09: **two clauses were deleted rather than reworded a third time.** The
  `Never do` scope gloss produced a finding under two successive wordings — the
  first forbade the five surfaces the Durable Outputs table assigns, the second
  made that table the write allowlist and so forbade every topic body, fixture
  and assertion the tasks construct. The table names lasting records, not working
  surfaces; the boundary now prohibits new structure only, and what each task
  writes is named in its own Approach and Tests text, with a `Touches` line where
  one is declared. Likewise the Execution-evidence row's
  partial task list was the defect rather than its contents, since every task
  close on a ledger record: it names every task rather than a range, so inserting
  a task under an amendment cannot leave the row stale.
- 2026-09-09: six independent cold shaping rounds and three adjudicated
  adversarial rounds — 58 findings, 50 repaired and 8 refuted. Beyond the
  decisions above, the repairs clustered in two classes swept across both files
  rather than patched where cited: a sentence storing another artifact's current
  state, now a citation to the suite or section that owns it; and a repair that
  changed an approach, a selector, a criterion or an accounting row without
  changing what sat underneath it — which is how AC3's seventh delegated concern,
  AC12's permitted explanatory case, T6's three positive architecture facts, and
  the AC10 and AC13/AC14 ledger owners each went unmatched for a round. The
  refusals are recorded in the adjudication artifacts: dated pre-change
  observations belong in the spec's `## Assumptions`, which the template defines
  as the frame rather than the contract; this changelog is required by that same
  template; AC4's admitting direction is corroborated by the shipped guard and
  its two vacuous cases were not stated in reverse; a task's tests reference a
  criterion only "if any", so non-criterion outputs route through the
  durable-output map; the Rollout section and the `Depends on:` graph already
  resolve load-bearing ordering; per-behaviour verification modes are the spec's
  Testing Strategy to own; and a spec-side role resolved to `none` is an
  applicability record rather than an output needing a map row.
- 2026-09-09: **the recompile and the retrieval re-measurement moved into the
  task that makes the last authored-source edit**, under a controlled contract
  amendment with recorded owner authority. EXECUTE proved the approved cut could
  not leave the repository green: the admission record's projection is checked
  against the compiled body as well as the authored one, so the first task adding
  a doctrine group fails without a recompile, while recompiling moves
  `source_digest` and fails both recorded-run digest assertions until new
  evidence is bound. Gates run at wave boundaries, so a wave holding both steps
  would be green — but a separate re-measurement task depends on the edit and can
  never share its wave. T2 therefore absorbs both steps and the separate
  re-measurement task is gone, taking the plan from nine tasks to eight. The
  general rule is now a constraint rather than a task detail, so a later
  source-editing task cannot reintroduce the gap. T1, T3, T4 and T5 keep their
  contracts and their landed work; the amendment pinned their sections and bound
  each to its ledger evidence.
- 2026-09-09: **the client manifest path leaves the pack**, under a second
  controlled amendment with recorded owner authority. T2's recompile exposed a
  contract collision the authored tree had hidden: a shipped boundary guard
  forbids this catalogue's manifest path anywhere in the projected pack tree,
  implementing the brief's non-goal against carrying AgentBundle delivery
  mechanics, while AC7 required the profile to state that path. Both sides
  carried authority — the foundation slice's ticked AC21 governs the boundary,
  and RFC-0097's 2026-09-01 erratum makes discovery location profile-eligible —
  so the owner chose to state the divergence by location and name only the
  specification's own filename. AC7 and AC14 are amended; AC8's authoring
  consequence needed no client path and is unchanged, as are the other eleven
  criteria, and the guard is untouched. T4 is completed and its section pinned, so
  the correction moves into unfinished T2 rather than editing T4: a separate
  preceding task would itself edit authored source and could not leave its own
  wave boundary green, which is the structure the first amendment already ruled
  out. AC14's advisory reading follows the content to T2; AC13's stays with T4,
  whose delegation passage is unchanged.
