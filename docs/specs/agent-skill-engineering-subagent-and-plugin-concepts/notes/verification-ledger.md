# Verification ledger

## T1 — Portability guard narrowing

The `runtime-settings-file` guard was stricter than the frozen portability
criterion it implements: it rejected the Agent Plugins specification's bare
`plugin.json` filename even though the criterion forbids runtime-owned paths.
The guard was narrowed to retain the class-as-a-rule shape while distinguishing
a runtime-owned manifest path from the specification filename. No ticked
criterion was amended.

### Base controls

Command:

```text
pytest packs/agent-skill-engineering/tests/pack/test_composition_floors.py -k "guard_admits or guard_flags"
```

The admitting control was red against the accepted base predicate, while the
runtime-owned-manifest erosion control was green:

```text
E       AssertionError: assert ['runtime-settings-file'] == []
FAILED packs/agent-skill-engineering/tests/pack/test_composition_floors.py::test_the_guard_admits_the_specification_filename
================== 1 failed, 1 passed, 18 deselected in 0.68s ==================
```

After narrowing, the full composition-floor suite passed:

```text
============================== 20 passed in 0.68s ==============================
```

### Mutation proofs

Widening mutation: replaced the narrowed expression
`\b(?:settings|hooks|mcp_config)\.json\b|(?<!\w)\.[a-z][\w.-]*/plugin\.json\b`
with `\b(?:settings|hooks|plugin|mcp_config)\.json\b`. The admitting control
failed as expected:

```text
E       AssertionError: assert ['runtime-settings-file'] == []
FAILED packs/agent-skill-engineering/tests/pack/test_composition_floors.py::test_the_guard_admits_the_specification_filename
============================== 1 failed in 0.64s ===============================
```

Non-matching mutation: replaced the narrowed expression with `(?!)`. The
runtime-owned-manifest control failed as expected:

```text
E       AssertionError: assert 'runtime-settings-file' in ['runtime-config-directory']
FAILED packs/agent-skill-engineering/tests/pack/test_composition_floors.py::test_the_guard_flags_a_runtime_owned_manifest
============================== 1 failed in 0.65s ===============================
```

Both mutations were restored by editing the expression after their observed
failure. The final restored suite result was:

```text
============================== 20 passed in 0.82s ==============================
```

## Method deviation — OKF recompilation is deferred to T8

T2, T3, T4 and T5 each state "Recompile the OKF tree" in their `Approach`. All
recompilation is instead performed once in T8, immediately before the retrieval
re-measurement. The end state is identical — the compiled tree is regenerated
from authored source before the re-measurement binds it — so no acceptance
criterion, task row, or dependency changes. This is a deviation from a task row's
literal method, recorded here rather than amended.

**Why.** `source_digest` is a sha256 over every authored source file's bytes
(`okf_compiler.py`, `_tree_digest` over the bundle's source records), and both
recorded retrieval runs pin the value the generated router publishes as
`source-digest`. Recompiling inside a body-edit task therefore reddens
`test_independent_router_results_meet_precision_and_recall_gate` and
`test_generic_negative_record_is_attributable_to_the_tree_it_measured` and leaves
them red until T8 re-measures — three waves later. Deferring the recompile keeps
each wave's test gate green and moves the digest exactly once, where new evidence
is recorded against it.

**Measured, by a reversible probe on the delegation floor.** With authored source
one sentence ahead of the generated tree, `pytest packs/agent-skill-engineering/tests`
returned `229 passed` (exit 0), while the compiler's check mode returned
`OKF011 .../ase-okf-reference/SKILL.md output drift` (exit 2). The probe sentence
was then removed and both readings restored: empty `git diff` for the floor and
`OKF000 check clean` (exit 0). The compiler check is a pre-PR and CI gate rather
than part of the per-wave test gate, so it is the one signal expected to stay red
between the first body edit and T8, and it must be clean before the PR opens.

**Bounded residual on T1's narrowed guard.** The narrowed `runtime-settings-file`
class flags a runtime manifest only beneath a dot-directory, so a hypothetical
`codex/plugin.json` with no leading dot would go unflagged. This is unreachable
for the only runtime the corpus profiles, whose manifest is
`.claude-plugin/plugin.json`, so AC4 is unaffected; it is the honest limit of the
predicate.

## Wave 1 — T3, T4, T5

Gates at the wave boundary: `pytest packs/agent-skill-engineering/tests` 241
passed; roster projection, consumer-integrations and conformance 109 passed; both
exit 0. The pack suite grew 229 → 241 as the wave's assertions landed.

### T3 — the portable delegation floor

The decision section's terminal pointer to a runtime profile is no longer the
only route: an unanswerable capability with no profile is stated as treated as
absent rather than assumed present, with the operation staying in the parent.
The construction-method section states both boundary directions. Mutations
observed: removing the absent-capability and parent-operation sentences reddened
the AC5 assertion while the absence assertion stayed green (`1 failed, 1
passed`); truncating the inbound sentence reddened only the inbound assertion
(`1 failed, 1 passed`). `topic-admission.json` needed no edit — the shipped
`observed-practice` group already covers the added practice, and its three
protected fields are byte-identical.

Independently re-checked: all eight declared subject phrases still present, the
conservative-default sentence intact, no runtime identifier in the floor, and no
internal-governance citation.

### T4 — the Claude Code profile

States `.claude-plugin/plugin.json`, the root-only non-discovery consequence, and
the runtime's `agents/`, `skills/` and `hooks/` surfaces. The admission record
gained the Claude Code plugins reference on the existing doctrine group; its
version range keeps a lower bound and an open upper bound, and the capability
ledger fixture is unchanged, so the frozen seven-row required set is untouched.

Mutation (b) is the load-bearing one and cross-confirms T1: moving the manifest
sentence into the package floor reddened the AC7 containment assertion **and**
fired the portability guard with `runtime-config-directory: '.claude'` and
`runtime-settings-file: '.claude-plugin/plugin.json'` — the narrowed class
correctly flags a runtime-owned manifest that reaches a floor. Mutation (a)
dropped the consequence and reddened only AC8; mutation (c) genericised one named
surface and reddened only that member. The temporary floor edit was restored, and
`git diff` on the package floor is empty.

### T5 — the retired leaves

Seven leaves rewritten, selected by a slug-shape predicate that excludes
`claude-code-` and asserts a selected count of exactly seven. Each now states
open extension with an admission condition naming first-party documentation
rather than a delivery slice.

Mutation (c) is the selector guard and the reason the predicate is slug-based:
stripping the word `runtime` from all seven reasons left both assertions still
selecting seven leaves and passing (`47 passed`). Had the selector keyed on the
absence prose, this task could have emptied its own population by rewriting it.
Mutations (a) and (b) each reddened exactly one assertion.

Independently re-checked against `HEAD`: 20 leaf headings before and after with
an identical heading set, exactly seven blocks changed, every other leaf
byte-identical, frontmatter unchanged, and `declared-absent-register.json` and
`topology-leaves.json` both unmodified.

## Plan error and owner authority — recompile and re-measurement must share a task

**Owner authority, 2026-09-09.** The scope owner reviewed the surfaced plan error
and authorized the restructure recorded here. No acceptance criterion changes;
only a task boundary moves.

**The error.** `test_shipped_body_matches_the_admission_record` iterates the
admission record over both the authored and the compiled body, and a doctrine
group's provenance block must appear in each. T2 adds the first doctrine group of
this slice, so it is the first task whose contract cannot be satisfied without a
fresh compiled tree. Observed with the recompile deferred:

```text
AssertionError: ('portable plugin core contract', 0)
FAILED packs/agent-skill-engineering/tests/pack/test_corpus_admission.py::test_shipped_body_matches_the_admission_record
1 failed, 252 passed
```

Both branches fail, which is what makes this a plan error rather than a method
choice. Not recompiling fails the doctrine projection, as above. Recompiling
passes it but moves `source_digest` and fails the two recorded-run digest
assertions until the retrieval re-measurement, which the approved cut places
three waves later.

**Why rescheduling alone cannot fix it.** Gates run at wave boundaries, so a wave
holding both the recompile and the re-measurement would be green. T8 depends on
T2, so no topological order places them in one wave, and T2 is alone in wave 2.
The only gate-green structure has the last authored-source edit, the recompile
and the re-measurement in a single unit.

**The authorized restructure.** T8's recompile and retrieval re-measurement merge
into the task that makes the last authored-source edit. T1, T3, T4 and T5 keep
their contracts unchanged and their landed work stands; T6, T7 and T9 keep their
contracts with dependencies re-pointed. The deferred-recompile deviation recorded
earlier in this ledger is superseded for the merged task and remains accurate for
T3, T4 and T5, none of which adds a doctrine group.

**State at the amendment.** Engine `CODE-IMPLEMENTATION`, wave index 1 of 5,
`completed_task_ids` empty because this cohort does not track per-task
completion. Wave 1's gates were green: pack 241, roster and conformance 109. T2's
three files are edited on disk with its four mutation proofs observed, including
the doctrine-source mutation that reddened the projection assertion. Nothing is
committed.

## Contract collision and owner authority — the client manifest path leaves the pack

**Owner authority, 2026-09-09.** The scope owner reviewed the surfaced collision
and chose option 1: state the divergence without naming the client's manifest
path. This amends two acceptance criteria.

**The collision.** `test_portable_tree_contains_no_adapter_or_publication_implementation`
forbids five literals anywhere under `packs/agent-skill-engineering/.apm/skills/`,
one of which is this catalogue's own manifest path. AC7 required the Claude Code
profile to state that path, and the profile compiles into that tree. Observed
after T2's recompile:

```text
AssertionError: assert '.claude-plugin/plugin.json' not in <projected pack tree>
FAILED packs/agent-skill-engineering/tests/pack/test_pack_boundary.py::test_portable_tree_contains_no_adapter_or_publication_implementation
3 failed, 250 passed
```

The recompile is what made it visible: before it the literal lived only in
authored source, which that guard does not scan.

**Why this is not the T1 case.** T1's predicate was stricter than the criterion
it implemented, so narrowing conformed code to contract. This guard instead
implements the brief's non-goal against moving AgentBundle manifests, adapters,
projection rules, versions, self-host commands, admission or publication policy
into the portable pack, and the forbidden literal is on that list because it is
this catalogue's manifest path. The foundation slice's ticked AC21 governs that
boundary and is frozen. RFC-0097's 2026-09-01 erratum separately makes discovery
location profile-eligible, so both sides carried authority and the conflict was
an owner decision rather than a defect.

**The authorized change.** The profile states that this runtime reads its plugin
manifest from a client-specific location beside the package root rather than at
the root, and names only the specification's own filename. The authoring
consequence AC8 fixes is unchanged and needs no client path to state. AC7 and
AC14 are amended to drop the client literal; AC8, AC13 and the other eleven
criteria are unchanged, and the boundary guard is untouched.

**Sequencing.** T4 is completed and its plan section is pinned, so the profile
correction is a new dependency-ordered unfinished task rather than an edit to
T4's contract. That task precedes T2 so the single recompile and retrieval
re-measurement stay in the slice's last authored-source edit.

**State at this amendment.** Engine `CODE-IMPLEMENTATION`, wave 1 of 3
post-amendment. Pack suite 3 failed, 250 passed, exit 1: this collision plus the
two recorded-run digest assertions awaiting re-measurement. `source_digest` moved
from `sha256:5b3038ca…` to `sha256:900765c2…`. Nothing committed.

## T2 — package floor, profile correction, recompile, and both retrieval runs

Gates: pack suite 254 passed, exit 0; OKF compiler check `OKF000 check clean`,
exit 0; roster projection, consumer-integrations and conformance 109 passed, exit
0. The compiler check had been red since the slice's first body edit and clears
here, which is the signal the authored and generated trees agree again.

### Content

The package floor states AC1's four specification-fixed behaviors, carries
neither AC2 sentence, and names all seven AC3 client-delegated concerns; its
seven declared subject phrases and the doctrine claim group are intact, and the
shipped `observed-practice` group's three protected fields are byte-identical.
The Claude Code profile now states the manifest divergence by location and names
only the specification's own filename — the client path appears nowhere in the
pack, authored or projected.

Mutations observed and restored by editing: paraphrasing one AC1 behavior
reddened only that behavior's assertion; restoring either AC2 sentence reddened
the absence assertion; dropping `sandboxing` reddened only that AC3 member;
dropping a cited source identity reddened the doctrine projection; restoring the
client manifest path reddened the new absence assertion; dropping the
located-elsewhere statement reddened the retargeted AC7 assertion; genericising
`hooks/` reddened the AC14 assertion.

### Retrieval re-measurement

Performed by an independent read-only subcontext navigating only the generated
router — its index, child indexes and concept bodies' routing-signal sections —
with the case fixtures' `expected_topics` withheld and the prior recorded runs
unread, so the answers were produced again rather than restated. 86 router
records and 40 generic-negative records returned, every id present exactly once,
no selection longer than three.

Floors, all against the shipped bar of 0.90: precision 1.000, recall 0.910,
exact-selection 0.907, bounded-selection 1.000. Negative set 40 prompts with 0
answered, against a cap of 2. Every admitted topic retains at least two measured
solo selections. All eight digest fields across the two runs were recomputed by
importing the suite's own helpers, so the recorded values come from the same
instrument that judges them.

### Inherited-pin re-takes

Five of the 24 pins moved and are recorded here with prior and current values, as
the re-take procedure requires:

```json
[
 [
  "authorization-at-trigger",
  [
   "framing-and-trigger-quality",
   "activation-discoverability-and-mode-wayfinding"
  ],
  [
   "framing-and-trigger-quality"
  ]
 ],
 [
  "mode-loading",
  [
   "instruction-density-and-progressive-disclosure",
   "activation-discoverability-and-mode-wayfinding"
  ],
  [
   "instruction-density-and-progressive-disclosure"
  ]
 ],
 [
  "asset-or-reference",
  [
   "resources-scripts-and-exit-contracts",
   "instruction-density-and-progressive-disclosure"
  ],
  [
   "instruction-density-and-progressive-disclosure"
  ]
 ],
 [
  "python-extension",
  [
   "python-and-pytest"
  ],
  [
   "resources-scripts-and-exit-contracts"
  ]
 ],
 [
  "node-extension",
  [
   "typescript-node-and-javascript-test-runners"
  ],
  [
   "resources-scripts-and-exit-contracts"
  ]
 ]
]
```

Three moved toward the case's authored `expected_topics` —
`authorization-at-trigger`, `python-extension` and `node-extension`, the last
two because the pins had recorded a language topic where the case expects the
resources topic. Two moved away from it: `mode-loading` and `asset-or-reference`
each lost a second topic the expectation carries.

**Instrument caveat, recorded because it bears on how this evidence should be
read.** The evaluator systematically under-selects second topics, which is why
recall is 0.910 rather than higher and why those two pins regressed. That is a
property of a single reader's judgement, not a corpus change: neither
`python-and-pytest` nor the TypeScript/Node topic was edited by this slice. The
run is recorded as measured rather than replaced by a more flattering one,
because selecting between runs by preference is how a re-take launders a result.
A later slice re-measuring these cases should expect this conservatism and judge
the two regressed pins on the router's current routing signals rather than on
this record.

## Wave 2 — T6, T7

Gates at the wave boundary: pack and integration suites 260 passed; OKF compiler
check `OKF000 check clean`; roster projection, consumer-integrations and
conformance 109 passed; all exit 0. `source_digest` still matches both recorded
runs, so T2's retrieval evidence stayed bound across this wave.

### T6 — the three surfaces

The pack README describes the floors' plugin-core content and no longer carries
its reserving sentence; its governed-topic count is still `Sixteen` against a
sixteen-topic admitted set, since this slice admitted no leaf. The architecture
document states which slice-3 surfaces exist, that runtime profiles beyond Claude
Code are retired to open extension, and that the router's claim-state reporting
belongs to the brief's `3c-r` row; it remains `PLANNED`.

Mutations observed and restored: restoring the README's reserving sentence
reddened the pack-scoped absence assertion; restoring the architecture
document's reddened the parallel assertion independently; advertising the plugin
core in the README while removing it from the floor reddened the new
body-to-README agreement assertion while the existing suite stayed green; and
deleting one of the three architecture facts reddened only that member.

Independently re-checked: no client plugin manifest path exists in either the
authored or the projected tree.

### T7 — the unavailable-mode proxy

The corpus prose was already compliant, so no corpus file changed; the task's
deliverable is the assertion. It reads the mode set from the unsupported-mode
fixture rather than a literal list, and keys on AC12's closed verb set —
`invoke`, `select`, `run`, `use`, `choose`, `package with`, and a
`should`/`must` addressed to the reader — rather than on a mode name appearing.

Mutations observed and restored: adding an invocation instruction to the accepted
specimen reddened the assertion; replacing the predicate with bare mode-name
membership reddened the accepted specimen, which is the false-positive
implementation the specimen pair exists to catch.

**Predicate walked against eight specimens** beyond the task's two, to check both
directions rather than trusting the pair. Seven behaved as expected. The eighth,
"Delegate to a subagent when the work is bounded", was expected to be rejected
and is accepted — correctly: it uses none of AC12's verbs, and it is concept
guidance the shipped delegation floor already gives. Rejecting it would be
exactly the false positive AC12 forbids the proxy from producing. The expectation
was wrong, not the predicate.

## T8 — the release surface

Both manifests carry `0.4.2`, a patch bump under `packs/AGENTS.md`: this slice
changed content and added no primitive. `docs/product/changelog.md` leads the
pack's history with `## [agent-skill-engineering][0.4.2] — 2026-09-09`, which is
what the consumer-integrations roster suite couples — the manifest version must
equal the topmost heading for the pack and exceed the recorded merge-base floor
of `0.4.0`. The spec-index row states the shipped shape and the final counts,
14 acceptance criteria and 8 tasks.

Gates: conformance 51 passed, exit 0 — that suite owns the two-manifest version
lockstep. Roster projection and consumer-integrations 58 passed, exit 0.
Spec-status lint clean across all 440 specs, exit 0, with no warning naming this
slice. Implemented directly rather than dispatched: four exact edits whose values
were already established, where a dispatch round-trip would have added nothing.

The pack is not self-hosted in this repository — absent from `catalogue.toml` and
not projected into `.claude/skills` — so `packs/AGENTS.md`'s self-host projection
step does not apply. That matches the brief, where self-host is slice 5.

## Named-reviewer readings — `foundation-corpus-reviewer`, advisory and non-gating

Each criterion below fixes a mechanical proxy; these readings are the adequacy
judgement the proxies cannot make, recorded beside the gate result so a
paraphrase that slipped past a proxy is visible to the next author. None gated
its task.

- **AC2, in T2.** The floor assigns manifest shape to no runtime profile in
  substance, not only in the two quoted sentences' absence. Its scope section now
  states the manifest as portable content and its provenance section names only
  installation, distribution, enablement, permissions, sandboxing and user
  experience as client-owned. No replacement sentence defers by other words.
- **AC14, in T2.** The packaging passage reads in this runtime's vocabulary: it
  names `hooks/` beside `agents/` and `skills/`, and refers to the manifest by
  location. A reader authoring for this runtime is addressed in the terms they
  author in, which is what the criterion is for.
- **AC13, in T4.** The delegation passage names `agents/` and `skills/` where it
  states worker boundaries. Adequate for the same reason as AC14.
- **AC10, in T5.** Each retired leaf's replacement admission condition —
  current first-party documentation establishing that runtime's named components
  and their authoring contract — is one a contributor could actually meet. It
  names evidence, not permission, and no delivery sequence gates it.
- **AC11, in T6.** No surface reserves a runtime profile for later delivery in
  different words. The README and architecture document both now state open
  extension positively rather than deferring, so there is no paraphrase to catch.
- **AC12, in T7.** The corpus prose names unavailable modes only while explaining
  concepts. The proxy's reach is genuinely narrower than the property — a
  recommendation phrased outside its verb set would pass — and no such
  recommendation is present in the current prose.

## Post-gates adversarial review — three sustained findings repaired

Independent adjudication sustained three of five findings and refuted two.

### A control that could not fail

The `claude-code-skills-subagents-hooks-and-plugins` admission record carried
`last_verified: 2026-08-31` while its body stated `Last verified: 2026-09-09` —
the only topic of sixteen whose two surfaces disagreed. The record now states
`2026-09-09`, the date its recorded retrieval evidence supports, since the
profile gained a source retrieved that day.

The parity check could not have caught it. `_assert_doctrine_projection` tested
`topic["last_verified"]` by bare containment over the whole provenance block, and
that block carries its own `Retrieved at: 2026-08-31.` source lines, which
discharged the assertion. Measured on the exact disagreement: the old predicate
returned present (green) and the repaired predicate returns absent (red). The
repair discounts one occurrence per cited source's `retrieved_at` and then
requires the concept's own date to survive.

A first repair attempt anchored the check to the literal `Last verified:` label
and was withdrawn: the `repeated-observed-failures` promotion class projects a
bare date with no label and cites no sources, so the label form broke three
shipped assertions including two controls, for a case where no shadowing is
possible. Discounting source dates targets the shadowing mechanism itself and
holds for both body shapes.

Mutation: reverting the record to `2026-08-31` reddens
`test_shipped_body_matches_the_admission_record`; restoring it returns 49 passed.

### The knowledge-capture gate

Both capture gates now have receipts: `spec-approved` at
`kco-202609-9055c22b…` and `plan-locked` at `kco-202609-3f7fc5a7…`, which is what
the Reusable-learning durable output requires.

Terminal distillation at `plan-locked` refuses through the CLI with
`{"reason_code": "strict_parse"}`, exit 2. That refusal is not this delivery's:
all nine events in the shared journal partition validate individually, the
request parses and passes `validate_work_loop_terminal_distill_request` when
those functions are called directly, and `distill_pending` returns
`{'pending': 1, 'processed': 0, 'unresolved': 1}` when the store is called
directly with the same selector. The refusal therefore sits in the CLI's own
request handling rather than in the payload or the journal. The capture remains
pending, which is the documented state for an undistilled observation. Recorded
here rather than worked around, and excluded from this slice's scope as a
discovery that does not match the accepted intent.

## Post-gates review round 2 — the parity repair completed to its class

One sustained finding, one refuted. The finding was that my own repair covered
the instance and not the class: it discounted each cited source's `retrieved_at`
but not the source's exposed version state, which may itself be a date. That is
live rather than hypothetical — the package floor's doctrine group cites a source
whose `last_updated` is `2026-08-04`, projected as
`Retrieved 2026-09-09; last updated 2026-08-04.` beside `Last verified:
2026-09-09.`, so a record claiming `2026-08-04` would have passed against a body
saying `2026-09-09`.

The check now discounts every value a cited source contributes — its retrieval
date and its exposed version state — before requiring the concept's own date to
survive. A seeded control,
`test_a_source_exposed_date_cannot_stand_in_for_the_concepts_own`, exercises both
shadowing shapes: a record whose `last_verified` equals a source's `retrieved_at`
and one equal to its `last_updated`, each against a body stating a different
date.

Mutation, observed: reverting the discount to `retrieved_at` only reddens that
control — `1 failed, 49 passed` — and the restore is byte-identical to the
pre-mutation file by `diff -q`. Restored by editing. The no-source
`repeated-observed-failures` bare-date shape still passes, which is why the
discount approach was chosen over anchoring to a `Last verified:` label.

This is the third consecutive round where a repair of mine was the next finding's
source, and the second on this one predicate. The pattern is consistent: I fix
the cited instance and not the class the instance belongs to.

The refutation: the retired-leaf assertions read the authored register rather
than the compiled one, but the compiled tree is a never-edited compiler
projection whose consistency is the `OKF000 check` gate, and the compiled-side
leaf set is already pinned by the register transcription — so no state satisfies
AC9 and AC10 in the authored register while violating them at the installed
boundary with that gate green.

## Owner decision — the doctrine projection check is uniform

**Owner authority, 2026-09-09.** The quality lens returned an
`ADJUDICATION-INDETERMINATE`, which the strict classifier reported as
`{"classification": "invalid", "reason": "indeterminate-present"}`. Per the
gateway that is a terminal stop for owner choice, so no transition, recording,
execution or mutation followed it until this decision.

**The question.** A branch I added to `test_shipped_body_matches_the_admission_record`
exempted the Claude Code profile from the compiled half of the doctrine
projection check, on the stated grounds that the recompile came later. The
recompile has since happened, the two provenance sections are byte-identical, and
the comment cited a task number the amendment renumbered — so the branch's own
condition had expired. What remained was whether the earlier decision assigning
compiled-projection consistency to the `OKF000 check` gate, recorded for the
retired-leaf assertions, extends to doctrine provenance blocks.

**The decision: it does not extend. Option A — delete the branch.** Every
doctrine group now verifies both projections. The analogy to the retired-leaf
refutation is weaker than it appears: that refutation rested on the register's
leaf set being independently pinned by the register-transcription assertion, and
doctrine provenance blocks have no equivalent second pin. No fingerprints were
recorded from the invalid adjudication artifact, since the classifier rejected
it; the repairs below return through a fresh review round.

## Quality-lens repairs — a third control that could not fail

### The reader-facing scope repair

`_body()` returns the whole concept file, and the package floor states all four
portable-core behaviors twice: once in the reader-facing
`## Scope and routing signals` section and again verbatim in the
`**portable plugin core contract:**` provenance block. Every plugin-core
assertion therefore read a body in which the provenance copy could discharge it,
so the control could not fail on the placement it claimed to guard. The same
whole-file reach let the README-agreement check satisfy its floor half from the
provenance label alone.

`_reader_facing()` now strips everything from `## Provenance and lifecycle`
onward, and the parametrized behavior assertions read that instead of the whole
file.

**Mutation, observed.** The reader-facing sentence for component-failure
isolation was taken from the file as actually wrapped — a first attempt with a
retyped line break did not match — and removed from the Scope section only,
leaving the provenance copy standing:

```text
FAILED packs/agent-skill-engineering/tests/pack/test_composition_floors.py::test_the_plugin_floor_states_each_portable_core_behavior[isolated-failure]
1 failed, 35 passed
```

**The repair changed the verdict, measured on that same state:** the old
whole-file predicate returned the sentence present (green, so the defect shipped
silently) and the reader-facing predicate returns it absent (red). Restored from
a byte copy; `36 passed` afterwards.

**Reach, carried from the adjudication rather than assumed.** The defect was
established only for the plugin-core family. The AC7, AC8 and AC14 profile
assertions are not discharged by their provenance block, whose clause differs in
case and terminal punctuation from the asserted sentences, and the delegation
floor's inbound and outbound boundary sentences have no provenance duplicate at
all. Those assertions were left alone.

**One error the gate caught.** The first placement of `_reader_facing()` landed
between `@pytest.mark.parametrize` and its function, orphaning the parameters
into `fixture 'behavior' not found` — a collection error, not a failure. The
helper was relocated above the decorator. It would have shipped had the edit been
trusted instead of run.

### The uniform doctrine projection

The per-topic exemption is deleted per the owner decision recorded above, so
every doctrine group now verifies both projections. The two provenance sections
for the profile were confirmed byte-identical by `diff` before the branch was
removed, so no assertion gained a target it cannot see.

### The pin test's compensating-control pointer

The docstring named "two of the 24 pins" re-taken and a per-slice `qa.md`. Both
were stale: five pins moved, and the record is this ledger. It now names this
file with the live count and states why the pointer is load-bearing — the
equality assertion cannot detect an unrecorded re-take, and this record is the
only control the test admits for that blind spot.

### Gates after all three repairs

Pack and integration 261 passed; conformance 51; roster projection and
consumer-integrations 58; OKF compiler check `OKF000 check clean`; spec-status
lint clean. All exit 0.

## CI failures and their correction

Eight checks failed on the first CI run against three root causes. `main` at the
rebase base was green, so all three were this change's to answer.

### Self-host projection — five of the eight

`CAT-V-015 self-host projection is out of date` cascaded into `gate-main`, both
`make build-check` jobs, `Gate D — catalogue artifact smoke`, and
`Lifecycle hooks`. The dry run found exactly one drift,
`.claude-plugin/marketplace.json`: the aggregated marketplace manifest pins each
pack's version, so the `0.4.1` to `0.4.2` bump required regenerating it.
`make build-self` resolved it and `catalogue verify` is clean.

Earlier in this delivery the pack was judged not self-hosted, on the evidence
that no `.claude/skills/ase-okf-reference` projection exists and the pack is
absent from `catalogue.toml`. That evidence was real and the conclusion drawn
from it was wrong: the marketplace manifest is a self-host output regardless of
whether the pack projects into this repository's own skills tree. The Makefile
target was used rather than the `agentbundle` on `PATH`, which resolves to a
site-packages copy outside this worktree.

### Pack-test boundary — the `Caps enforcer self-test`

Two breaches. Four hits where the architecture assertions reached above the pack
through `Path(__file__).resolve().parents[4]`, and one where
`CONCEPTS / f"{CLAUDE_CODE_PROFILE}.md"` joined a variable onto a path the linter
cannot statically prove stays in-pack. The second is fixed by globbing the owning
directory and indexing by stem, the idiom the sibling suites already use and
which this repository's own code comments document. The first is fixed by moving
that coverage to `tests/roster/test_agent_skill_engineering_subagent_and_plugin_concepts.py`,
where it runs, reddens on a restored reserving sentence, and additionally pins
the document's `PLANNED` status so the two absence checks cannot be satisfied by
a document that also claimed a status this slice may not grant.

**The rule was available before the code was written.** `packs/AGENTS.md` states
it in its second sentence -- "The pack owns its runtime export and test
boundary" -- and `tools/lint-pack-test-boundary.py` enforces it.

That file was never deliberately read. The host injected it as a scoped-guidance
reminder when a command touched `packs/`, and two of its rules were applied from
that injection -- the version bump and the ban on internal-governance citations
in shipped pack content -- while the framing sentence was not. PLAN step 1a
instructs reading the effective root and scoped `AGENTS.md` for the files in
scope; that step was skipped in favour of what the injection surfaced. The
`## Writing pack tests` section covers module naming and suite cost and does not
restate the boundary, and the standards document it routes to does not mention
it, so the sentence above the section is the authority. Relying on an injection
rather than reading the scoped file is how it was missed. The
quality lens then raised the relocation and it was refuted as a preference,
because neither `packs/AGENTS.md`'s framing sentence nor the enforcing lint was
in the authority set supplied to the adjudicator. The reviewer was right. The
incomplete brief is a second failure downstream of the first, not the cause.

### A high-severity advisory that was not this change's

`GHSA-7w5x-hrqm-74c2` (high), `smol-toml` denial of service via malformed TOML,
in `docs-site`. This change touches no lockfile and no docs-site file, and the
advisory reds any pull request once disclosed. Taken as a Tier 1 reproducible
ride-along under the bundled-fixes carve-out, with the owner's instruction to fix
CI: `npm audit fix --package-lock-only`, run in `docs-site`.

Verified against the resolved package set rather than the manifest, because a
fix group can carry a transitive major: resolved count unchanged at 590, one
package in and one out, `smol-toml` 1.7.0 to 1.8.0 within the same major, three
changed lines in one file, `package.json` untouched. `tools/audit-npm.py` then
reported `✓ docs-site: no blocking advisories`, exit 0.
