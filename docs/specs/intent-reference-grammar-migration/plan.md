# Plan: Cross-artifact reference grammar and pointer migration

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`
  — `resolve_endpoint` (629) is the changed surface, `recognize_briefs` and
  `recognize_specs` are the recognizers `intent:` is modelled on.
  `packs/core/tests/skills/work-loop/test_lint_traceability.py` (48 tests, none
  reaching `resolve_endpoint`) is the construction path. Named uncertainty: no
  existing test covers orphan classification at this corpus size.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/intent-reference-grammar-migration/notes/verification-ledger.md`.
> A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

The change is a resolver change followed by two mechanical sweeps, gated on one
governance round. `resolve_endpoint` gains a refusal state and a fourth
recognizer adds `intent:` nodes; then 19 `Parent intent:` values and 34 `Brief:`
values are rewritten to `<kind>:<slug>` by a script that re-derives its own
cohort. The rewrite count is not 19: T3's recognition exposes 14 further
`Parent intent:` values, taking the builder-visible set to 37 — 25 resolvable
and therefore rewritten, and 12 link-shaped values that stay report-only. Any
figure stated before T3 runs undercounts. The riskiest part is not the sweep
but the node-set growth: adding 117
`intent:` nodes makes those files orphan- and reachability-checkable for the
first time, and `--strict` treats a structural orphan as exit 1. So the
measurement task sits between the resolver work and the sweeps, and its result
can add repair work to them rather than being read afterwards as a receipt.

## Constraints

- ADR-0033 D2 keeps `Level` an open set, so the recognized-kind table is closed
  by decision, not derived — an open namespace cannot be enumerated to prove a
  duplicate check complete. This is why AC "no two nodes share an id" is
  checked over the derived corpus rather than against a fixed kind list.
- Deriving slugs from the `Slug:` field rather than an ordinal-prefixed
  filename is RFC-0103 D2's own decision, grounded in its own reasoning: a
  series position is not a name. ADR-0108 D2, D3 and D6 govern
  acceptance-criterion and verification-item identifiers and forward adoption
  across spec directories, not intent filenames, and an earlier revision of
  this plan cited them outside that scope.
- ADR-0112 makes an index over a corpus generated or absent, so no hand-edited
  table of cohort membership is created.
- The cross-artifact reference grammar RFC supersedes the `Brief:` path pin in
  `guides/core/reference/product-brief-fields.md`. Until it is `Accepted`, every
  task below is blocked: the guide is the accepted convention and this plan
  contradicts it.
- `packs/core/.apm/` is the source for all three script copies. `make build-self`
  refuses a dirty tree, so reprojection is its own task, after the edits commit.

## Construction tests

**Integration tests:** one `lint-traceability --root . --strict` run over the
repository after every task, with node count, edge count, hard violations, and
exit code appended to the verification ledger. It is the only check that sees
the resolver, the recognizer, and both sweeps together.

**Manual verification:** that command's actual stdout, stderr, and exit code,
read rather than inferred from a green suite.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale — the grammar RFC | T1 | RFC at `Accepted` with the assigned ordinal | `Constrained by:` cites the ordinal, not a placeholder |
| Current architecture — resolver state contract | T2, T2a | `resolve_endpoint` docstring enumerates all five states | No state the function returns is unnamed |
| Interface compatibility — the `Brief:` field row and its readers | T6 | Guide row reads `brief:<slug>` and names the retained path fallback; the dispatch provenance check admits the typed form and still refuses an unrecognized one | Guide, template, both stamping skills, the coverage join, and the dispatch check agree |
| Maintainer procedure — the spec template | T6, T8 | `make build-self` output; three copies byte-identical | Byte comparison across the three paths |
| Release history | T8 | One changelog entry naming the new form and the fallback | Entry names the fallback |
| Reusable learning — brief erratum | T4 | Erratum recording the measurement method and corrected count | The brief states the method its count depends on |

## Design (LLD)

### Data & schema

A node id is `<kind>:<slug>`. `kind` comes from the closed recognized-kind set,
which the added `intent` joins. `slug` is the artifact's `Slug:` field value,
falling back to the directory name for a spec and the filename stem for a brief,
matching the two recognizers that already work that way.

Two exclusions carry the design, and measurement settled both.

`intent:` covers only the files under the intents base that `recognize_ladder`
does not already claim — 117 of 150, the other 33 being typed `outcome`,
`opportunity`, or `capability` from the same directory. Registering those 33
again would give one artifact two ids. Re-measured against the corpus on
2026-09-22 by building the graph and projecting each option over the local node
set: the repository holds 594 local nodes and 1 collision slug today; the
exclusion gives 711 nodes, 7 collision slugs, and 0 of 19 live bare
`Parent intent:` pointers ambiguous; blanket registration gives 744 nodes, 39
collision slugs — 32 of them an artifact colliding with itself — and makes all
19 live bare pointers ambiguous against their own target.

An earlier revision of this section recorded 6 collisions becoming 25 with 18
self-collisions and 7 ambiguous pointers. Those figures did not reproduce and
are superseded by the ones above; the method, not just the result, is recorded
because the figures differ by which node set is counted.

Slug identity keys off `Slug:` rather than the filename stem because 5 of the
117 filenames carry an ordinal prefix, and a stem-derived id would put an
ordinal inside a pointer value. All 117 files carry a `Slug:` field and no two
share a value.

Traces to: the `intent:` recognition, no-duplicate-id, and ordinal-refusal
criteria.
<!-- Owned by: T3. -->

### Interfaces & contracts

`resolve_endpoint(target, local_ids, rollup)` returns four states today —
`local`, `satisfied-by-reference`, `unresolvable` and `dangling` — and gains a
fifth. An earlier revision called it "a fourth state", omitting `dangling`,
which the function returns for a missing local-shaped target and which the
docstring's own "three endpoint states" opener also undercounts. The refusal is its own
state rather than a reuse of `dangling`, because `dangling` means *no* target
and its message says so; a caller that cannot tell "names nothing" from "names
several" cannot report either usefully.

Three call sites read that state, not two: `_wire_up` for producer pointers
(`:1093`), `_wire` for forward ones (`:1122`), and `resolve_sidecar_endpoints`
(`:880`). The first two route the new state to `g.dangling`, which is the seam
making the refusal exit non-zero without `--strict`. The third registers only
`satisfied-by-reference` and `unresolvable` today, so an unrouted refusal would
fall through it and report as a bare `sidecar_dangling` — the exit code would
survive but the candidate list AC-0003 requires would be lost. It is routed
too; no `_state/traceability.json` exists in this tree, so the fixture is the
only reachable case.

`_wire_up` prefers a candidate resolving `local` over an earlier one resolving
only `unresolvable`. Today the first non-dangling candidate wins and an external
stub counts, so a typed `Brief:` cannot take the in-edge from an earlier
path-shaped `Contract:` or `Discovery:`. The owner granted this under the spec's
`Ask first` on 2026-09-22, against a measured post-sweep blast radius: brief
in-edges go from 26 to 34 and no spec's in-edge moves to a field other than
`Brief:`.

Crossed boundary and its test seam: `lint-brief-coverage.py` joins a spec to a
brief on the `Brief:` value with its own implementation, separate from
`resolve_endpoint`. A green traceability suite says nothing about it, so it gets
its own test.

A third reader crosses a second boundary. `workspace_status_engine.py`
(`packages/agentbundle/`) reads the same header through a generic preamble
parser, so it never names the field and a name search does not find it. It lands
the value in the artifact's provenance parent and, for a spec, requires a
canonical local brief path — which refuses both `brief:<slug>` and a bare slug
today. Admitting the typed form there is part of this delivery; the refusal of
anything that is neither form stays, because the same helper validates
`workspace.toml` paths where the typed form is meaningless.

Traces to: the canonical-resolution, bare-slug-fallback, ambiguity-refusal,
exit-code, coverage-rollup, and producer-candidate-preference criteria.
<!-- Owned by: T2, T2a, T6. -->

## Tasks

### T1: The grammar RFC is accepted

**Depends on:** none

**Tests:**
- `python3 .claude/skills/new-rfc/scripts/next-ordinal.py --check docs/rfc`
  reports clean after the record lands, so the assigned ordinal collides with
  nothing. The checker ships with the `new-rfc` skill; there is no
  `tools/repo/next-ordinal.py` in this repository.
- The record names all four pointer fields, the `intent:` kind, and the
  superseded `Brief:` path pin in `guides/core/reference/product-brief-fields.md`.

**Approach:**
- Author it with `new-rfc`; the ordinal is assigned at authoring, never reserved
  here, because reserved ordinals in this repository have not held.
- Acceptance is a human gate. No dependent task starts until the record's
  `Status:` is `Accepted`; every later task contradicts a currently accepted
  guide until then. (`Proposed` is not in the RFC template's vocabulary —
  `Draft`, `Open` and `Final Comment Period` are the pre-acceptance states, and
  a gate naming `Proposed` would be vacuous for all three.)

**Done when:** the RFC's `Status:` is `Accepted` and `spec.md`'s
`Constrained by:` cites its ordinal.

### T0: The surface inventory is derived

**Depends on:** none

<!-- T0 gates on nothing. It reads the repository and writes a derivation
     script and its output under this spec's notes/; it changes no guide, no
     skill and no script, so it cannot contradict the convention T1 supersedes.
     An earlier revision gated it on T1 by analogy with the tasks that do edit
     governed surfaces, which would have withheld the measurement every later
     task depends on until after the governance round. -->

**Touches:** docs/specs/intent-reference-grammar-migration/notes/

**Tests:**
- A committed script at
  `docs/specs/intent-reference-grammar-migration/notes/derive-surfaces.py`
  emits, for **all four** pointer fields, every surface that touches each one,
  labelled `writes`, `states`, `reads` or `generated-copy`, to
  `notes/surface-inventory.md` — AC-0019. `stub: true` The two unmigrated
  fields are inventoried too, and their surfaces recorded as unchanged: the
  follow-on that migrates them needs the same list, and a reader like
  `lint-spec-status.py`, which independently reads `Contract:` and enforces
  contract-path resolution, is exactly the kind of consumer a later name search
  would miss again.
- Re-running it on an unchanged tree produces a zero diff.
- The inventory finds all three surface classes a name search misses, asserted
  by naming one known member of each: the generic preamble reader
  (`workspace_status_engine.py`), a generated copy (one of the three
  `workspace_status_engine.py` projections), and a template that emits
  `Parent intent:` without reading it
  (`frame-intent/assets/intent-template.md`). A derivation that returns none of
  these has reproduced the defect it exists to prevent.

**Approach:**
- Derive readers by consuming each field through the functions that read it,
  not by searching for the field's name: a generic preamble parser keys on the
  lower-cased field name and never contains the literal string.
- Derive writers by searching for the *form each field's value takes* — the
  old shape's text — rather than the field name, which finds a template that
  stamps the value without ever reading one.
- Derive generated copies by content identity across the tree, so a projection
  is never mistaken for a source.

**Done when:** the inventory exists, the script re-runs with a zero diff, and
each of the three named members appears under its correct label.

### T2: An ambiguous bare slug refuses

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/scripts/lint-traceability.py, packs/core/tests/skills/work-loop/test_lint_traceability.py

**Tests:**
- `resolve_endpoint` against a node set holding two ids sharing a suffix returns
  the refusal state, and the emitted message contains both candidate ids — AC-0003.
  `stub: true` — this is the first test in the suite to call `resolve_endpoint`.
- The same target against a one-id set still returns `local` with the canonical
  id, so the fallback is not collateral damage — AC-0002.
- A target equal to a node id returns that id without entering the suffix scan,
  pinning the fast path a later refactor could route around — AC-0001.
- `FEAT-0001` and `FEAT-0001-intent-identity-and-registration` refuse — AC-0005.
- A graph carrying one ambiguous pointer exits non-zero in default mode and
  under `--strict` — AC-0004, whose closed set is both. The repository runs in
  the cross-cutting tests and in T8 assert exit 0 over a clean corpus, so
  neither reaches a refusal and neither covers this.

- A sidecar graph carrying an ambiguous endpoint names every candidate in the
  report and exits non-zero in default mode — AC-0003, AC-0004 at the third
  call site. The existing suite already carries sidecar fixtures, so the seam
  exists; no `_state/traceability.json` is present in this tree, which is why
  the fixture is the only reachable case.

**Approach:**
- The refusal lands before T3 because it is inert until the node set grows: no
  live pointer is ambiguous either before or after T3, so ordering it first
  adds a refusal that cannot fire and cannot break the repository, and T3 then
  grows the node set against a refusal already under test.

**Done when:** every test in this task's `Tests:` list is green and the
repository run still exits 0.

### T2a: A local producer candidate wins the in-edge

**Depends on:** T2

**Touches:** packs/core/.apm/skills/work-loop/scripts/lint-traceability.py, packs/core/tests/skills/work-loop/test_lint_traceability.py

**Tests:**
- A consumer whose candidate list holds an earlier external-only pointer and a
  later locally-resolving one carries an in-edge from the local node — AC-0013.
  `stub: true`
- A consumer whose only resolving candidate is external still carries the
  external in-edge, so the existing orphan behaviour is unchanged.
- A dangling candidate is still reported in every mode regardless of where it
  sits in the candidate order, pinning the behaviour `_wire_up` already has.

**Approach:**
- The preference is expressed as a second pass over the already-resolved
  candidate states, not as a reordering of `_SPEC_UP_FIELDS`. Reordering the
  tuple would change the reported field priority for every consumer; a
  preference over resolved states changes only which of two resolving
  candidates wins, which is what was measured.

**Done when:** every test in this task's `Tests:` list is green and the
repository run's edge count is unchanged, because no `Brief:` value is typed yet at this point.

### T3: Intent files are graph nodes

**Depends on:** T2

**Touches:** packs/core/.apm/skills/work-loop/scripts/lint-traceability.py, packs/core/tests/skills/work-loop/test_lint_traceability.py

**Tests:**
- A fixture intents directory holding one ladder-typed file and one plain intent
  yields exactly one `intent:` node, keyed on the plain file's `Slug:` value — AC-0006.
  `stub: true`
- A fixture file whose filename carries an ordinal prefix and whose `Slug:` does
  not yields the `Slug:`-derived id, and no id containing the ordinal.
- A fixture file with no `Slug:` field appears in the report — AC-0014.
- That same fixture contributes no node — AC-0015. The two assert separately
  because an implementation can emit the report and still register a node: the
  fallback it would reach for is the filename stem, and 5 of the 117 stems
  carry an ordinal prefix, which AC-0005 refuses as a pointer value.
- A fixture in which two artifacts derive the same id fails the uniqueness
  check — AC-0007. The assertion runs over the **pre-insertion id sequence**,
  because `Graph.add` assigns into `self.nodes` (`:352`) and a second
  registration overwrites the first, so any check reading the built node set is
  true for every corpus including a colliding one.

- The new recognizer's paths enter parent-edge wiring, asserted by a fixture
  whose `intent:` node carries a `Parent intent:` pointer and gains the
  corresponding in-edge. Registration alone is not enough: the edge builder
  wires `Parent intent:` from the brief and ladder path maps, so a recognizer
  that returns nodes without joining that wiring leaves 14 real pointers
  unbuilt.

**Done when:** every test in this task's `Tests:` list is green, and the
repository run's derived id
sequence carries no duplicate while its cross-type collision set contains no id
whose two candidates resolve to the same file.

### T4: The corpus impact is measured and recorded

**Depends on:** T3

**Touches:** docs/specs/intent-reference-grammar-migration/notes/

**Tests:**
- A committed probe script at
  `docs/specs/intent-reference-grammar-migration/notes/corpus-probe.py`
  re-derives node count, edge count, the collision set,
  the ambiguous-pointer set, the orphan and reachability classifications, and —
  for each consumer — which candidate field supplied its winning producer, and
  writes them to the verification ledger. The field is recorded because
  `Graph.add_edge` keeps only endpoint ids, so T7's field-origin assertion has
  no other oracle.
- Re-running the probe on an unchanged tree produces a zero diff, so the numbers
  are reproducible rather than transcribed.

**Approach:**
- This sits between the resolver work and the sweeps, not after them, because its
  result can add repair work to both. 117 new nodes become orphan- and
  reachability-checkable here for the first time, and `--strict` fails on a
  structural orphan.
- If the run reports orphans, stop and Surface: the remedy is either repair work
  this plan does not carry or an accepted classification change, and neither is
  an implementer's call.

**Done when:** the ledger holds the before and after numbers, the probe re-runs
with a zero diff, and any orphan finding has been Surfaced.

### T5: Every `Parent intent:` value is typed

**Depends on:** T0, T4

**Touches:** docs/product/intents/*.md, docs/product/briefs/*.md, plus every surface the T0 inventory labels as writing or stating the `Parent intent:` form

**Tests:**
- Re-deriving the cohort after the sweep reports no resolvable `Parent intent:`
  value that is not `<kind>:<slug>` — AC-0008. The predicate is the canonical
  shape, not the absence of bare slugs: 4 of the 23 builder-visible values are
  markdown links, and a bare-slug predicate leaves them.
- Every surface the T0 inventory labels as writing or stating the
  `Parent intent:` form emits `<kind>:<slug>` after this task — AC-0020. The
  inventory finds 15 such surfaces today, including
  `frame-intent/assets/intent-template.md` and the brief seed template; without
  repointing them the swept values are re-emitted in the old form and the
  migration does not converge.
- The sweep leaves a value whose target the corpus cannot resolve untouched and
  names it in its report.
- Each rewritten value's resolved node id equals the id it resolved to before
  the sweep, so the sweep preserves every edge rather than repointing one.

**Approach:**
- A resumable script with a `pending`/`done`/`failed` tracking file, re-deriving
  the cohort each run rather than reading a recorded list — the cohort must
  include a pointer added after this plan was written, and it must be derived
  after T3, because recognizing the intent files makes 14 of their own
  `Parent intent:` pointers builder-visible and takes the cohort from 23 to 37
  — AC-0023.

**Done when:** the cohort re-derivation reports an empty remainder and the
repository run's edge count is unchanged from T4's recorded figure.

### T6: `brief:<slug>` is the canonical `Brief:` form

**Depends on:** T0, T1

**Touches:** every surface T0's inventory labels as writing, stating or reading the `Brief:` form — the list is derived, not fixed here, because four successive revisions each stated a set the next round falsified. Known members at planning time, not exhaustive: guides/core/reference/product-brief-fields.md, guides/core/how-to/write-the-contract.md, packs/core/seeds/docs/product/briefs/_template.md, packs/core/.apm/skills/new-spec/assets/spec.md, packs/core/.apm/skills/new-spec/SKILL.md, packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md, packs/core/.apm/skills/author-delivery-brief/SKILL.md, packs/core/.apm/skills/author-delivery-brief/scripts/lint-brief-coverage.py, packs/core/tests/skills/author-delivery-brief/test_lint_brief_coverage.py, packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py, packs/core/tests/skills/workspace-status/

**Tests:**
- `lint-brief-coverage.py` joins a spec whose `Brief:` value is `brief:<slug>` to
  that brief, and the brief's Spec map rolls up from it — AC-0010. `stub: true`
- The same script still joins a path-valued and a bare-slug-valued spec, so the
  two compatibility forms survive the canonical change.
- A check walks every `Brief:` surface the T0 inventory labels `writes`,
  `states` or `reads`, and fails when any one names a different canonical form
  — AC-0009. It iterates the inventory and this plan states no count, because
  three successive revisions each stated a total the next round falsified.
- The inventory contains at least `packs/core/.apm/skills/new-spec/SKILL.md`
  and `packs/core/seeds/docs/product/briefs/_template.md`, asserted by name.
  Both were missed by earlier enumerations and neither is found by searching
  for the field name in the way those enumerations did, so they are the
  regression test for the derivation itself.
- `workspace_status_engine.py` returns no provenance finding for a spec whose
  `Brief:` value is `brief:<slug>`, and none for the surviving path form —
  AC-0016. `stub: true`
- A predicate-equivalence test proves the dispatch entry point accepts exactly
  AC-0016's two forms and refuses everything else — AC-0017. It compares the
  entry point's verdict against the stated predicate over a generated input
  space (the admitted forms, plus mutations injecting each excluded character
  class at each position, plus length boundaries). A fixed list of malformed
  examples is *not* sufficient and is the defect AC-0017 names: ten cases leave
  `brief:ok!`, `brief:two:parts` and a spaced slug unasserted, and an
  implementation admitting every `brief:`-prefixed string passes them all. The
  named cases below are evidence inside that test, never the test itself.
- A case whose `brief:<slug>` target is a symlink resolving outside
  `docs/product/briefs/` but still inside the repository, and a second
  resolving outside the repository entirely, each produce a provenance finding
  and block dispatch — AC-0022. The first case is the one repo-root confinement
  alone does not catch, which is why the boundary is the briefs directory.
- A parameterized case per non-provenance call site of the shared brief-path
  rule — the `workspace.toml` entry, dependency, legacy-queue and receipt
  paths — shows a typed value and a malformed `brief:` value both still
  invalid there — AC-0018. This is the test that catches a repair which widened
  the shared helper instead of normalizing at the provenance read.
- `packs/core/tests/skills/new-spec/` and `packs/core/tests/pack/` stay green —
  five test files reference the template and pin its prose.

**Approach:**
- The guide row is the accepted convention T1 supersedes, so it is edited here
  rather than in T8: leaving it stale through the sweep would make every swept
  spec contradict the documented form while the sweep is in flight.
- The engine change admits one additional value shape at the provenance check.
  It normalizes `brief:<slug>` to `docs/product/briefs/<slug>.md` *before* the
  existing lexical checks run, so `_is_repository_relative_path` and
  `_SINGLE_SEGMENT_RE` apply unchanged and `_is_canonical_local_brief_path` is
  never relaxed. That helper also guards `workspace.toml` entry and dependency
  paths, where the typed form has no meaning and must keep failing, which is
  why the reduction sits at the provenance read rather than inside the helper.
- **Confinement is the one check that is not reused as-is.**
  `_confined_artifact_path` verifies the target stays beneath the *repository
  root*, which AC-0022 is deliberately stricter than: a brief path whose
  symlink resolves to another directory inside the repository passes repo-root
  confinement and still escapes the briefs directory. The provenance branch
  therefore canonicalizes the `docs/product/briefs/` root and the target, and
  verifies the target remains beneath that resolved root, emitting a provenance
  finding that blocks dispatch otherwise. Reusing the repo-root helper here
  would satisfy the plan's own prose while violating the criterion, which is
  the gap two review rounds caught.
- The engine has **four byte-identical copies**. The source is
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`;
  `.agents/`, `.claude/` and `packages/agentbundle/agentbundle/_data/` are
  projections that T8 regenerates. Editing the `_data/` copy directly is the
  same error this delivery exists to correct elsewhere, and `make build-self`
  would overwrite it.
- `security-reviewer` fires on the diff because the changed code is a
  validation control on the path that gates every queued spec.

**Done when:** every test group in this task's `Tests:` list is green.

### T7: Every `Brief:` value is typed

**Depends on:** T0, T2a, T5, T6

**Touches:** docs/specs/*/spec.md

**Tests:**
- Re-deriving the cohort after the sweep reports no `Brief:` value that resolves
  as an untyped path — AC-0008.
- `lint-brief-coverage.py` exits 0 over the repository, and every brief's
  rollup verdict matches the verdict recorded before the sweep.
- Every spec the re-derived cohort discovers carries a brief in-edge, with no
  remainder — the outcome T2a's preference change delivers and which sweeping
  `Brief:` alone cannot. The assertion runs over the cohort derived at run
  time, not a recorded count, because a `Brief:` value added after this plan
  was written is in scope.
- No in-edge is won by a field other than `Brief:`, read from the selected
  field T4's probe records beside each resolved endpoint. `Graph.add_edge`
  stores only `(producer, consumer)` (`:357`), so the built edge set alone
  cannot answer this and the probe is the only oracle.

**Approach:**
- Review shape is WIDE: 34 files, one mechanical substitution each. It is not
  split. Its reproducibility proof is the sweep script, its zero-diff re-run,
  and the before-and-after rollup comparison; the sampled review covers the 8
  pre-empted specs, which are uniform in outcome after T2a but are the only
  members whose in-edge reaches the brief through the preference path.

**Done when:** the cohort re-derivation reports an empty remainder, the rollup
verdicts match, and the sweep script re-runs with a zero diff.

### T8: The projections and the release surface are consistent

**Depends on:** T7

**Touches:** .agents/**, .claude/**, packages/agentbundle/agentbundle/_data/workspace_status_engine.py, docs/product/briefs/intent-identity-and-registration.md, CHANGELOG.md

**Tests:**
- The three `lint-traceability.py` copies and the three spec-template copies are
  byte-identical after `make build-self` — AC-0011.
- The four `workspace_status_engine.py` copies — the pack source plus the
  `.agents/`, `.claude/` and `packages/agentbundle/agentbundle/_data/`
  projections — are byte-identical after `make build-self`. The fourth copy is
  why this check is not covered by AC-0011's three-copy comparison.
- `make lint-ruff lint-mypy` passes.
- `python packs/core/.apm/skills/work-loop/scripts/lint-traceability.py --root . --strict`
  exits 0, with its stdout, stderr, and exit code recorded — AC-0012.
- `python .claude/skills/work-loop/scripts/lint-spec-status.py --root .` passes.
- The changelog entry names the retained bare-slug and path fallbacks, not only
  the new canonical form.
- The brief erratum states that its collision count depends on reading `Slug:`
  rather than the filename stem.

**Approach:**
- `make build-self` refuses a dirty tree, so the edits from T2 through T7 commit
  before this task runs. `tests/roster/` is dispatched on CI, never run here.

**Done when:** every check in this task's `Tests:` list passes and the recorded
command output is in the ledger.

## Rollout

- **Delivery:** big bang, in one PR, behind no flag. The resolver refusal and the
  swept values must land together: the refusal is inert without `intent:` nodes,
  and `intent:` nodes without the swept values would be the ambiguity the spec
  refuses.
- **Reversibility:** fully reversible by reverting the PR. Nothing is migrated
  outside version control, no data is transformed, and no published event or
  external system is involved.
- **Deployment sequencing:** the RFC is accepted before any code or guide edit,
  because the guide it supersedes is the currently accepted convention.
  Reprojection follows the source edits, because the build refuses a dirty tree.
- **Infrastructure and external systems:** none.


## Risks

- **Every closed surface list in this contract was wrong at least once.** Six
  review rounds grew the `Brief:` writer set from 3 to 5, the reader set from 2
  to 3, the engine copy count from 1 to 4, and found 15 unscoped
  `Parent intent:` writers. Each list had been enumerated by memory or by
  searching for a field's name, and a name search cannot see a generic parser,
  a projection, or a template that emits a form without reading it. T0 exists
  to replace that method; a criterion that names surfaces inline instead of
  citing T0's inventory has reintroduced the defect.

- **117 nodes become orphan-checkable at once.** `--strict` fails on a
  structural orphan and no existing test covers that classification at this
  size. T4 measures it before either sweep; an orphan finding Surfaces rather
  than being repaired inside this scope.
- **The brief's collision count is not reproducible from its own method.** It
  records 6 and names a set that reading `Slug:` does not reproduce exactly.
  Any task trusting the recorded number instead of re-deriving it will
  disagree with the corpus.
- **Three consumers read `Brief:`, and the third is on the dispatch path.**
  An earlier revision of this plan recorded that `workspace_status_engine.py`
  never reads the spec header, "confirmed, not assumed". Execution falsified
  that: the module parses the header generically through
  `_parse_preamble_fields`, lands the `Brief:` value in the artifact's
  provenance parent, and validates it as a canonical local brief path, so the
  typed form is refused there today. The confirmation was a search for the
  string `Brief` in that module, which a generic parser does not contain — the
  method could not have found it. Every later claim about that module is
  therefore grounded in its behaviour, driven through the real functions, not
  in a name search. Evidence and the owner decision that widened the cohort are
  in `notes/verification-ledger.md`.
- **The spec template is prose-pinned by five test files.** Editing its
  `Brief:` comment can fail `packs/core/tests/skills/new-spec/` and
  `packs/core/tests/pack/` for reasons unrelated to the grammar.

## Changelog

<!-- Approvals only. -->

- 2026-09-22: spec approved by eugenelim
- 2026-09-22: plan approved by eugenelim
<!-- Amendment authority lives in the engine's amendment history and in
     notes/verification-ledger.md, not in this changelog. -->

- 2026-09-22: amended spec approved by eugenelim
- 2026-09-22: amended plan approved by eugenelim
