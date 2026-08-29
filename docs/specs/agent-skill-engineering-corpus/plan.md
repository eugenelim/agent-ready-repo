# Plan: Agent Skill Engineering Corpus

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/rfc/0097-agent-skill-engineering.md` (D3 topology
  at 207-254, D8 promotion classes at 496-506 and security rules at 507-519,
  Gate 1/2 measures at 577-591, the encyclopedia falsifier at 536) and
  `packs/AGENTS.md` (export boundary, version-bump rule, no repository-only
  citations in shipped pack content). Analogous implementations:
  `packs/agent-skill-engineering/` as shipped by
  `docs/specs/agent-skill-engineering-foundation/` — the same OKF bundle,
  router, and fixture topology this slice extends — and
  `packs/catalogue-curation/.apm/skills/compile-okf/` as the governed compiler
  that owns generation. Corresponding tests:
  `packs/agent-skill-engineering/tests/` and `tests/roster/` for anything that
  walks outside one pack. Named uncertainty: how many of the 17 candidate
  leaves can evidence either basis is not knowable before T5-T7 run, so
  the plan gates on the rule rather than on a topic count.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially, note why in the changelog at
> the bottom. Once it is `Done` and the spec is `Shipped`, the directory freezes
> as a unit.

## Approach

The corpus is built evidence-first and in that order: the census, the taxonomy
transcription, and the admission harness all land before any new topic body
exists, and the harness is green against the three already-shipped topics
first. That inverts the tempting order — write the topics the taxonomy names,
then justify them — and it is what makes the rule mechanical rather than
aspirational.

What the harness can and cannot prove is now settled rather than assumed.
RFC-0097's 2026-08-28 erratum rules that D8's promotion classes gate a topic's
*doctrine claims*, not the topic's existence, and that observed practice is
admissible under an explicit applicability limit. So the harness asserts that a
claim group declares a basis and carries that basis's fields, and a named
reviewer judges whether the evidence supports the claim. Three review rounds
established that the second half is not mechanizable: a gate over declared
expectations, then over a class label, then over a contract citation, was each
satisfiable without the substance. Stopping at form-plus-named-reviewer is the
honest boundary, and the erratum is what makes it legitimate rather than a
concession.

The harness still reads *measured* retrieval rather than declared
expectations, because an author writes `expected_topics` and only a recorded
run writes `actual_topics`. Applying the rule retroactively to the three
shipped topics is deliberate: it proves the rule on content that already exists
before any new content depends on it. Those three carry no external source of
any kind, so under the erratum they are `observed-practice` and T5 gives them
the applicability limits they are missing — the erratum's retroactive clause,
owned here.

The riskiest part is retrieval regression. Adding topics to a router that
scored 24 of 24 can only move that number one way, and a rate over a larger
suite hides it, so the foundation cases are pinned as `(id, measured_topics)`
pairs in a fixture no re-recording step writes.

## Constraints

- A pack test may not resolve a path outside its owning pack
  (`tools/lint-pack-test-boundary.py` check 6). Anything walking every pack
  lives in `tests/roster/`.
- Nothing the pack ships — hand-authored `.apm/**` or compiled output — carries
  a repository-only path, an acceptance criterion, or an internal governance
  citation. Repository-specific evidence lives in
  `packs/agent-skill-engineering/tests/fixtures/`, outside the export boundary.
- The OKF compiler's only input is the bundle root and every managed output is
  under `.apm/skills/ase-okf-reference/`, so any record that must both feed the
  harness and ship to users originates in the bundle root.
- `agent-skill-engineering` is not in the self-host include list, so its
  `.apm/` edits produce no `.claude/` or `.agents/` drift.
- This slice touches no `packs/core` surface, no workspace-status engine code,
  and no ratchet. The executing-clause deletion is a separate change.
- `[backlog].open`'s legacy-shape ceiling is at its maximum and forbids being
  raised; only `path`-bearing canonical entries are exempt.
- The router skill's name and activation description are pinned by a recorded
  measurement. Neither changes.
- A `tests/roster/` module needs no wiring: the suite target and the
  build-check workflow both run pytest over `tests/`, which collects that tree.
- The recorded retrieval fixture is bound to one
  source/router/generated-tree digest triple recomputed from the current tree
  and asserts that its result set equals its case set, so every corpus change
  invalidates every prior result. Measurement is therefore a whole-suite
  re-record, never an incremental append.
- No new dependency, module boundary, artifact-kind home, or top-level directory.

## What `Touches` means here

A task's `Touches` line is its intended surface, not a proven-exhaustive file
manifest. Four review rounds each found one more file a task would move — a
recorded fixture invalidated by a recompile, a digest pin, a generated
projection — and enumerating harder does not close that class, because the
authoritative answer is what the gates say after the edit.

Two standing obligations close it instead, and they bind every task:

1. **Regenerate every projection through its owning command.** If an edit moves
   a generated or aggregated artifact, that artifact is regenerated in the same
   task by the command that owns it, whether or not the task's `Touches` line
   named it.
2. **Run each owning gate directly.** A gate is satisfied by invoking it, never
   by inferring from a chained target that it must have run.

A file discovered missing from a `Touches` line during EXECUTE is added to that
line in the same commit that touches it, so the plan converges on reality
rather than the reverse.

## What this plan does not contain

The acceptance criteria are the checklist. This plan does not restate them.

An earlier revision tried to: it carried a prose bullet for each conjunct of
each criterion, so the plan alone stated every property that would be checked.
That is a second home for 122 facts with nothing keeping the two in sync, and
four consecutive repair passes each left a different conjunct behind — the
defect was the mirror, not the passes. A 122-conjunct audit taken at that point
read 104 covered, 7 uncovered, 11 uncertain.

What lives here instead:

- **Strategy** — approach, layer map, dependency order, design decisions that
  are not derivable from the spec.
- **Mechanism an implementer cannot infer** — which suite proves a property and
  where it lives, which fixture carries which join key, which shipped assertion
  a change will move. That is the only thing a `Tests:` bullet is for here.
- **Red stubs** for the six criteria the spec's Testing Strategy declares TDD,
  and a `no stub (mode)` record for the rest.

Verification happens at GATES, by running things. The QA record captures what
was observed, after the fact. Where a criterion's conjunct needs no mechanism
beyond reading the criterion, this plan is silent about it on purpose.

## Construction tests

Written before the implementation they verify. The load-bearing one is the
admission harness in T6, mutation-proven on each conjunct independently: a
claim group with no declared basis; a `doctrine` group missing `retrieved_at`
on one source; a `repeated-observed-failures` group whose failures name
different mechanisms; an `observed-practice` group whose observations share a
pack; an `observed-practice` limit carrying its population phrase but not its
scope-bound statement; a topic with a declared but unmeasured exclusive case;
and a topic body
authored to reproduce the compiled unpopulated record's marker and section
shape, which must still be iterated and must still redden, because the harness
excludes that record by its exact identity and never by a property a topic body
could copy. A conjunction that only fails when every half is missing is a
fraction of a check.

What no construction test attempts is whether the evidence supports the claim.
The erratum assigns that to a named reviewer recorded per topic, because three
review rounds showed each mechanical proxy for it was satisfiable without the
substance.

## Layer map

| Layer | Tasks | State at layer close | Reviewed as |
| --- | --- | --- | --- |
| L1 records | T1, T2 | Successor authored and registered; records current | One unit |
| L2 harness | T3, T4, T5, T6 | Baseline pinned; harness green against the three shipped topics | One unit |
| L3 corpus | T7, T8, T9 | Topics admitted and measured; taxonomy accounted for | One unit |
| L4 mode | T10, T11 | Fixtures pass, then the mode is advertised | One unit |
| L5 evidence | T12, T13 | Behavior record observed and bound | One unit |
| L6 publication | T14 | Manifests, changelog, README, architecture current | One unit |

Each layer leaves the repository with the gates green for the surfaces it
touched. The pack's publication obligations — manifest bump, eval harness,
changelog entry — close once at L6 before the change is proposed for merge,
which is the granularity the spec's Always-do states.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `packs/agent-skill-engineering/README.md` | T14 | Mode list equals advertised modes; `catalogue lint --deep` exit 0 | README names four modes and the admitted groups |
| `docs/architecture/agent-skill-engineering.md` §3, §9, §11 | T14 | Topology lists admitted and unpopulated leaves; §11 dated | Still `PLANNED`; claims no later-slice surface |
| `docs/product/changelog.md` | T14 | `## [agent-skill-engineering][<version>] — <date>` entry | Entry names the mode change and admitted groups |
| Pack manifest pair | T14 | Matching bump; roster and publication gates green | Both manifests same version |
| Delivery-cut variance | T2 | Distinct INI-009 section; brief slice-table rows | Brief's slice 2 reader reaches the split and the deferral |
| Guide deferral held open | T14 | `agent-skill-engineering-guide-and-docsurl` still in `[backlog].open`; `GUIDE_OPTIONAL_PACKS` unchanged | One command confirms both |
| `project-knowledge` receipts | work-loop gates | Capture receipts or named skip | Distilled at `plan-locked`, or skip recorded |

## Design (LLD)

### Design decisions

**The census proves coverage; the admission fixture admits.** They are separate
files because they answer separate questions and the governing RFC positions
them differently — the census is Gate 2's coverage instrument, while admission
rests on D8's promotion classes. Conflating them was the round-2 defect.

**Independence is defined mechanically and scoped**: two observations are
independent when they name skills at distinct paths in distinct packs. It is
required of an `observed-practice` group, which rests on observations, and is
not required of a `doctrine` group, which rests on a contract, failures, a
safety failure, or a measurement. The earlier draft demanded it universally,
which the three shipped class-free topics could not have satisfied.

**The unpopulated record originates in the bundle root**, not in a test
fixture, because the compiler reads only the bundle root and writes only under
`ase-okf-reference/`. The harness reads the compiled output. That gives the
fact one home and needs no parity test — the mirror-plus-parity shape was
rejected for the same reason a second admitted-topics list was.

**The foundation three are reclassified, not back-filled into doctrine.**
RFC-0097:555 sources the Agent Skills specification for a portable `SKILL.md`
substrate and for scripts as deterministic helpers — not for trigger-quality or
instruction-density heuristics. Claiming class 1 for all three would have cited
a contract that does not govern their claims, which is the vacuity the third
review round identified. Under the erratum they are `observed-practice` and
gain the applicability limits they lack. A `doctrine` group inside any of them
must name the contract clause that governs it.

**The parity check is deliberate, and differs from the mirror this plan
rejected.** The unpopulated record has one home because the compiler can
project it. Provenance cannot work that way: the harness needs structured data
a test can read, and a consuming agent only ever reads the shipped body. Both
must exist, so a field-for-field parity assertion is what keeps them one fact.

### Data & schema

`skill-census.json`: `{schema_version, taken_at, population_size, entries: [
{skill, pack, families: [...], exception: {owner, rationale} | null} ]}`.
Exactly one of non-empty `families` or `exception` per entry. `owner` is a role
or generic placeholder, never a person, and `reviewer` in
`topic-admission.json` carries the same form for the same reason — the
repository's privacy rule reaches every file, and its author-decider carve-out
does not extend to a pack test fixture.

`topic-admission.json`: per topic — `{topic, claim_groups: [...],
last_verified, reviewer}`. Each claim group carries `basis` of `doctrine` or
`observed-practice`.
A `doctrine` group carries `promotion_class` (one of D8's four) and `evidence`
shaped by it: `public-contract` → `{contract, clause, runtimes: [>=2 each
documenting that clause], sources}`; `repeated-observed-failures` →
`{mechanism, failures: [>=2]}` with one shared mechanism, since D8:499 requires
repeated failures *with the same mechanism* and per-failure mechanisms would be
singletons; `severe-safety-failure` → `{failure, boundary, reproduction}`;
`controlled-measurement` → `{setup, preserved_semantics, before, after,
repetitions}`, carrying the two conjuncts D8:501 names beside the measurement.
Every cited source is `{name, url, retrieved_at, source_version_or_last_updated
| "none exposed"}`. A `doctrine` group also carries `revalidation_trigger`:
RFC-0097:493 binds it to every admitted concept, and the erratum narrowed only
the promotion basis.
An `observed-practice` group carries `{observations: [>=2 at distinct skill
paths in distinct packs], applicability_limit, revalidation_trigger}` and no
promotion class. The limit carries both conjuncts the criterion states — the
population it names and the statement that the claim is not established beyond
it — asserted at T5's seam rather than by decomposing the field.

`topology-leaves.json`: names, `source_ref`, `expected_count: 36`. Nothing
else — a leaf's admitted-or-unpopulated state is read from the compiled tree
and the compiled unpopulated record, so it has one home.

`generic-negatives.json`: `{schema_version, expected_count: 40,
prompts: [{prompt_id, prompt}]}` — identified per prompt, mirroring
`router-cases.json`, because the equality below needs a join key and bare
strings do not supply one. `generic-negatives-results.json`:
`{schema_version, evaluation_mode, source_digest, router_digest,
generated_tree_digest, run, results: [{prompt_id, returned_body: bool}]}`. The
two `prompt_id` sets are asserted equal, and the prompt count is asserted
against `expected_count`, so the falsifier's denominator is pinned on both
sides. Two files, because an equality inside one file compares a list with
itself.

`foundation-retrieval-pins.json`: 24 `(id, measured_topics)` pairs, read from
`router-results.json`'s `actual_topics` **before** any corpus change and never
rewritten. The field is deliberately not called `expected_topics`: that name
belongs to author declarations in `router-cases.json`, and this fixture holds
measurements — the distinction AC4 and AC8 exist to keep.

### Interfaces & contracts

Unchanged. The semantic provider request/response, its `contract_version`, and
the `task_kind` vocabulary are exactly as the foundation shipped them.
`knowledge-provider` is an authoring-workflow mode, not a provider task kind.

### Component / module decomposition

No new modules. Topic bodies and the unpopulated record are added under the
bundle root and compiled by the existing governed compiler. Mode modules are
added under `.apm/skills/author-or-update-agent-skill/references/`.

### State & control flow

`frame` remains the default and only entry point. `knowledge-provider` is
reachable only by explicit user transition from `frame`, begins read-only, and
requires a second transition before any write — the two-gate shape `create` and
`update` already use — with one difference this mode cannot inherit: their
shipped sentence gates at the moment of writing, not at entry, so
`knowledge-provider` needs its own read-only entry sentence and a separate
write-authorizing transition. The common contract's safety-and-authority module
governs every read and write in every mode.

### Behavior & rules

A request routed to an unpopulated leaf reports the gap by name, applies
admitted guidance that does apply, and returns no body for that leaf — the
behavior the foundation shipped for the language seams, generalized.

### Failure, edge cases & resilience

T10's four provider-pattern fixtures are this slice's added failure surface,
and they pass before T11 advertises the mode.

### Quality attributes (NFRs)

Retrieval: >=90% exact-set, >=90% at most three topics, 24 of 24 foundation
cases exact per case against pinned pairs, <=5% of a fixed 40-prompt
generic-engineering negative set returning any body. Two clean compiles
byte-identical. Staged-tree runs read nothing outside the staged tree.

**Joint closure of the M2 retrieval measure.** RFC-0097:582 sets at least 40
prompts and defines their topical coverage across pytest, Node, execution
economics, subagents, hooks, plugins, and runtime profiles. This slice
contributes the 24 foundation cases plus at least two exact-set cases per
admitted topic plus near misses; slice 2b adds the pytest, Node, and
execution-economics prompts for its 5 leaves; slice 3 adds the subagent, hook,
plugin, and runtime-profile prompts for its 11. The 40-prompt count is reached
within this slice; the topical coverage the RFC describes closes only when all
three have landed, and no single slice claims the whole gate.

### Dependencies & integration

None added.

## Tasks

### T1: The successor slice has a real spec and plan

**Depends on:** none

**Touches:** docs/specs/agent-skill-engineering-languages-and-execution/spec.md, docs/specs/agent-skill-engineering-languages-and-execution/plan.md

**Tests:**
- `lint-spec-status.py --root .` exits 0 with the new pair present. (AC15)
- The pair's `Status` values are `Draft` and `Drafting`, which `work.queue`
  admits.

- `no stub (goal-based)` — the artifacts are two authored documents; the check
  is that `lint-spec-status.py` accepts them.

**Approach:**
- Author the 2b spec and plan covering its 5 topology leaves, the pytest-suite
  and Node/browser behavior fixtures, and its retrieval prompts. Scope only.
- Back-link the brief and state the hard dependency on this spec.

**Done when:** the pair exists, lints clean, and is registrable canonically.

### T2: The workspace, brief, initiative, and index name the slices actually in flight

**Depends on:** T1

**Touches:** workspace.toml, docs/product/briefs/agent-skill-engineering.md, docs/product/initiatives/ini-009-agent-skill-engineering.md, docs/specs/README.md

**Tests:**
- Reconciliation resolves this spec as active and 2b as queued, both
  canonically shaped; no collection gains a legacy-shaped entry. (AC15)
- The brief's Spec map and slice table, and every `docs/specs/README.md` row
  this change touches, mirror their spec's `Status` — including the foundation
  row currently reading `Implementing` against a `Shipped` spec. (AC15)
- INI-009 carries a distinct `Delivery-cut variances` section naming both
  departures **and the authority for each** — the criterion requires the
  authority, not only the departure; a grep for that heading and the brief's
  slice-table rows succeeds. (AC16)
- `lint-spec-status.py` and `lint-brief-coverage.py` exit 0.

- `no stub (goal-based)` — the check is reconciliation output plus two linters,
  not a compressible predicate.

**Approach:**
- Correct `["ini-009"].milestone`, which still names foundation implementation
  as queued.
- Register both specs canonically as `{path, kind, source, summary, needs}`,
  with 2b declaring its dependency on this spec.
- Add a `Delivery-cut variances` section to INI-009 rather than appending to
  `Backlog disposition variances`, whose scope is RFC-0097 D7.
- Measure `unsatisfied_dependency` after registration. If 2b's true edge would
  exceed the ceiling, **surface to the owner under *Ask first* before raising
  it**; do not raise it unilaterally and do not drop the edge.

**Done when:** reconciliation shows the intended memberships with no new legacy
entry, both linters exit 0, and the ratchet suite is green.

### T3: The census resolves every authored skill, and its test actually runs

**Depends on:** none

**Touches:** packs/agent-skill-engineering/tests/fixtures/skill-census.json, tests/roster/test_skill_census.py

**Tests:**
- No `exception.owner` value is a person.
- The new roster module is reachable by a gate CI runs — observed under
  `pytest tests/ --collect-only`, not assumed. (AC18)

- PLAN-time red stub (`tests/roster/test_skill_census.py`):

  ```python
  # STUB: AC1 — every authored skill resolves in the census, and the recorded
  # population equals live discovery.
  import json, pathlib

  REPO = pathlib.Path(__file__).resolve().parents[2]
  CENSUS = REPO / "packs/agent-skill-engineering/tests/fixtures/skill-census.json"

  def test_census_resolves_every_authored_skill() -> None:
      census = json.loads(CENSUS.read_text(encoding="utf-8"))
      discovered = {
          f"{p.relative_to(REPO).parts[1]}/{p.parent.name}"
          for p in REPO.glob("packs/*/.apm/skills/*/SKILL.md")
      }
      recorded = {f"{e['pack']}/{e['skill']}" for e in census["entries"]}
      assert recorded == discovered, (
          "census out of date; re-take it and update population_size"
      )
      assert census["population_size"] == len(discovered)
      for entry in census["entries"]:
          assert bool(entry.get("families")) ^ bool(entry.get("exception"))
  ```

  `stub: true` — validated by execution against the live tree, not only parsed:
  it reports the live discovered-skill count and fails on the absent fixture,
  which is the
  right red. The key is relative to the repository root; `p.parts[1]` on the
  absolute path yields `Users`, which collapses every pack and makes the
  equality unsatisfiable. EXECUTE adds the owner-is-not-a-person assertion and
  the routing failure message.

**Approach:**
- Take the census by reading each skill and classifying it under review — not
  by pattern-matching. A regex census counts inherited boilerplate as designed
  structure: an "Output rendering" section appears in most skills without any
  of them having chosen a presentation pattern.
- Fixture in the pack tree, live-discovery assertion in `tests/roster/`.
- **Add no Makefile wiring.** The suite target and the build-check workflow
  both run pytest over `tests/`, which collects `tests/roster/`, so the module runs without being named. Naming it would double-run it
  and force a re-pin of two hard-pinned digests for no coverage. An earlier
  draft did exactly that, on a `grep` for `tests/roster` in the Makefile that
  returned nothing because collection is by directory.

**Done when:** the roster test is green, every entry resolves, and it is
observed running under `pytest tests/` rather than assumed to.

### T4: The pre-change retrieval baseline and the taxonomy are pinned

**Depends on:** none

**Touches:** packs/agent-skill-engineering/tests/fixtures/topology-leaves.json, packs/agent-skill-engineering/tests/fixtures/foundation-retrieval-pins.json, packs/agent-skill-engineering/tests/pack/test_corpus_admission.py (created here)

**Tests:**

- PLAN-time red stub (`packs/agent-skill-engineering/tests/pack/test_corpus_admission.py`):

  ```python
  # STUB: AC5, AC8 — the taxonomy transcription is complete at 36 leaves and the
  # foundation pins hold 24 measured pairs.
  import json, pathlib

  FIX = pathlib.Path(__file__).resolve().parents[1] / "fixtures"

  def test_topology_transcription_is_complete() -> None:
      leaves = json.loads((FIX / "topology-leaves.json").read_text(encoding="utf-8"))
      assert leaves["expected_count"] == 36
      assert len(leaves["leaves"]) == 36
      assert len(set(leaves["leaves"])) == 36

  def test_foundation_pins_hold_the_shipped_cases() -> None:
      pins = json.loads((FIX / "foundation-retrieval-pins.json").read_text(encoding="utf-8"))
      assert len(pins["pins"]) == 24
      assert all("measured_topics" in pin for pin in pins["pins"])
  ```

  `stub: true` for AC5. AC8's pin counts ride along in the same block rather
  than carrying their own stub: the spec declares AC8 goal-based, and the count
  is a pure predicate over one fixture, so it costs nothing to assert here.
  EXECUTE adds the source-reference assertion; the counts are final and are what
  fail if the transcription is partial.

**Approach:**
- Transcribe RFC-0097 D3's 36 leaves with a `source_ref`.
- Derive the pins now, from the current `router-results.json`, **before T7
  touches the corpus**. Deriving them afterwards would capture a moved value
  and make the per-case gate pass trivially.

**Done when:** both fixtures exist and their count assertions are green.

### T5: The three shipped topics declare their basis and state their limits

**Depends on:** T3, T4

**Touches:** packs/agent-skill-engineering/tests/fixtures/topic-admission.json, packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/, packs/agent-skill-engineering/.apm/skills/ase-okf-reference/references/okf/, packs/agent-skill-engineering/.okf-generated.json, packs/agent-skill-engineering/tests/fixtures/router-results.json, packs/agent-skill-engineering/tests/pack/test_corpus_admission.py, packs/agent-skill-engineering/tests/pack/test_foundation_corpus.py

**Tests:**
- Each recorded and shipped `applicability_limit` contains its scope-bound
  statement, not the population phrase alone. Truthiness on the fixture side and
  substring parity into the body both read green on a limit missing it, and this
  is the clause that keeps an `observed-practice` claim from reading as portable
  doctrine. (AC2, AC3)
- No shipped provenance-and-lifecycle section contains any `reviewer` value from
  `topic-admission.json` — an absence assertion over the bundle-root bodies and
  the compiled tree, scoped to the role-or-placeholder form the schema pins, so
  it is discriminating rather than liable to fire on ordinary prose. Nothing
  else catches it: AC9's forbidden set is paths, AC citations, and governance
  records, and an identity field is none of those. (AC3)
- No shipped applicability limit contains a pack path, a skill path, or a pack
  name: it names its population in portable terms. This is the clause that
  keeps parity from pushing repository structure across the export
  boundary. (AC3, AC9)
- Each of the 24 pinned pairs still holds after this task's re-record. (AC8)
  T5 edits the three shipped bodies, so it is the first task that can move a
  foundation case; waiting until T7 to notice would lose the attribution.
- Whether that clause actually governs the group's claims is the named
  reviewer's judgment, recorded with the topic; no test asserts it, because the
  erratum places it outside what a gate can prove.

- PLAN-time red stub (`packs/agent-skill-engineering/tests/pack/test_corpus_admission.py`):

  ```python
  # STUB: AC2, AC3 — each shipped topic declares a basis and its body agrees
  # with the admission record, per claim group.
  import json, pathlib

  PACK = pathlib.Path(__file__).resolve().parents[2]
  ADMISSION = PACK / "tests/fixtures/topic-admission.json"
  CONCEPTS = PACK / "okf/agent-skill-engineering-foundation/concepts"

  def test_every_claim_group_declares_a_basis_and_its_fields() -> None:
      record = json.loads(ADMISSION.read_text(encoding="utf-8"))
      for topic in record["topics"]:
          assert topic["reviewer"] and topic["last_verified"]
          for group in topic["claim_groups"]:
              assert group["basis"] in {"doctrine", "observed-practice"}
              assert group["revalidation_trigger"]
              if group["basis"] == "observed-practice":
                  assert len(group["observations"]) >= 2
                  assert group["applicability_limit"]

  def test_shipped_body_matches_the_admission_record() -> None:
      record = json.loads(ADMISSION.read_text(encoding="utf-8"))
      for topic in record["topics"]:
          body = (CONCEPTS / f"{topic['topic']}.md").read_text(encoding="utf-8")
          for group in topic["claim_groups"]:
              if group["basis"] == "observed-practice":
                  assert group["applicability_limit"] in body
  ```

  `stub: true` — EXECUTE adds the doctrine-side source parity, the distinct-pack
  independence check, and a `reviewer`-matches-the-role-or-placeholder-form
  assertion, the sibling of T3's owner-is-not-a-person check. Without it the
  form the absence assertion is scoped to rests on nothing.

**Approach:**
- Classify the three under the erratum. They cite no external source today, so
  the default is `observed-practice`; give each the applicability limit it
  lacks, naming the population it was drawn from **in portable terms** — the
  authored agent skills of the catalogue this pack is developed in, their
  count, the census date, **and that the claim is not established beyond that
  population** — the second conjunct the criterion requires and the round-4
  refutation's own example carried — with no pack or skill path. The concrete
  observation paths stay in the non-projected fixture, which is what lets the
  parity check hold without exporting repository structure.
- Do not claim `public-contract` for trigger-quality or instruction-density:
  RFC-0097:555 sources the Agent Skills specification for the `SKILL.md`
  substrate and for scripts as deterministic helpers, not for those heuristics.
  A scripts-related group may cite it where the clause governs the claim.
- Recompile after editing the bundle-root bodies; the compiled tree and the
  ownership manifest are tracked and digest-asserted.
- Record the classification outcome in this plan's changelog rather than the
  spec, so the task writes only files it lists.

**Done when:** all three declare a basis with complete fields, the parity check
is green, the compiled tree is regenerated, and the retrieval record is
re-recorded under the new digest triple by an independent read-only sub-context, the evaluation mode the shipped fixture pins — editing the bundle moves all three
digests, so leaving the prior record in place would redden the suite this layer
must close green.

### T6: A topic cannot enter the corpus without a declared basis, its fields, and measured distinguishability

**Depends on:** T5

**Touches:** packs/agent-skill-engineering/tests/pack/test_corpus_admission.py

**Tests:**

- PLAN-time red stub (`packs/agent-skill-engineering/tests/pack/test_corpus_admission.py`):

  ```python
  # STUB: AC2, AC4, AC5 — admitted implies declared basis with its fields, and
  # measured exclusive retrieval; every leaf sits in exactly one set.
  import json, pathlib

  PACK = pathlib.Path(__file__).resolve().parents[2]
  FIX = PACK / "tests/fixtures"

  def test_admitted_topics_are_measurably_distinguishable() -> None:
      results = json.loads((FIX / "router-results.json").read_text(encoding="utf-8"))
      admitted = _admitted_topics_from_compiled_tree()
      for topic in admitted:
          exclusive = [r for r in results["results"] if r["actual_topics"] == [topic]]
          assert len(exclusive) >= 2, topic

  def test_every_leaf_is_in_exactly_one_set() -> None:
      leaves = json.loads((FIX / "topology-leaves.json").read_text(encoding="utf-8"))
      admitted = _admitted_topics_from_compiled_tree()
      unpopulated = _unpopulated_leaves_from_compiled_record()
      for leaf in leaves["leaves"]:
          assert (leaf in admitted) ^ (leaf in unpopulated), leaf
  ```

  `stub: true` — `_admitted_topics_from_compiled_tree` excludes the unpopulated
  record by its exact compiled path, never by a shape a topic body could copy;
  EXECUTE writes both helpers and the seven mutations.

**Approach:**
- Derive the admitted set from the compiled tree, never a hand-maintained list.
- Read measured results from `router-results.json`, not `router-cases.json`.
- Land green at the three shipped topics, which T5 made satisfiable.
- Assert form only. Whether the evidence supports the claim is the named
  reviewer's judgment under the erratum, and no assertion pretends otherwise.

**Mutation proofs, each alone:** a claim group with no declared basis; a
`doctrine` group missing `retrieved_at` on one source; a
`repeated-observed-failures` group whose two failures name different
mechanisms; an `observed-practice` group whose two observations share a pack; an `observed-practice` limit carrying its population phrase but not its
scope-bound statement; a topic with a declared but unmeasured exclusive case;
and a topic body reproducing the compiled unpopulated record's marker and
section shape at a non-root path, which must still be iterated. Each must
redden. Restore by
editing bytes and verifying a hash.

**Done when:** the pack suite is green at the three shipped topics and all seven
mutations redden it.

### T7: The corpus carries the topics whose basis can be evidenced

**Depends on:** T6

**Touches:** packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/, packs/agent-skill-engineering/tests/fixtures/topic-admission.json, packs/agent-skill-engineering/tests/fixtures/router-cases.json, packs/agent-skill-engineering/tests/fixtures/router-results.json, packs/agent-skill-engineering/.apm/skills/ase-okf-reference/references/okf/, packs/agent-skill-engineering/.okf-generated.json, packs/agent-skill-engineering/tests/pack/test_foundation_corpus.py, packs/agent-skill-engineering/tests/pack/test_pack_boundary.py, packs/agent-skill-engineering/tests/integration/test_provider_contract.py

**Tests:**
- The admission harness is green after the re-measurement that closes this
  task. (AC2, AC4)
- Each body carries the sections the foundation contract already requires, and
  each shipped provenance section matches its admission record. (AC3)
- Nothing under `.apm/**` or the compiled tree contains a repository-only path,
  an acceptance-criterion citation, or an internal governance record. (AC9)
- The pinned foundation pairs still hold at this task's close. (AC8)

- `no stub (goal-based)` for the admission re-run and the measurement — both are
  commands over an assembled tree.
- PLAN-time regression guard (`packs/agent-skill-engineering/tests/pack/test_pack_boundary.py`):

  ```python
  # GUARD (not a red stub): AC9 — nothing the pack ships names a repository-only path, an
  # acceptance criterion, or an internal governance record.
  import pathlib, re

  PACK = pathlib.Path(__file__).resolve().parents[2]
  FORBIDDEN = (
      re.compile(r"\bdocs/(specs|rfc|adr)/"),
      re.compile(r"\bAC\d+\b"),
      re.compile(r"\bworkspace\.toml\b"),
  )

  SUFFIXES = {".md", ".json", ".toml", ".py"}

  def test_shipped_content_names_no_repository_only_reference() -> None:
      for path in (p for p in (PACK / ".apm").rglob("*") if p.suffix in SUFFIXES):
          text = path.read_text(encoding="utf-8")
          for pattern in FORBIDDEN:
              assert not pattern.search(text), f"{path}: {pattern.pattern}"
  ```

  `no stub (goal-based regression guard)`, with a non-vacuity floor and a
  positive control beside it: assert the walk visited at least as many files as
  the pack ships under `.apm` today, and that a seeded `docs/specs/` string is
  detected — otherwise a wrong root, an unlisted suffix, or an empty walk is
  indistinguishable from compliance, which is the trap this session's
  "7/7 compile-clean" report fell into. Executed at PLAN against the live tree
  it **passes**, because nothing under `.apm/` names a repository-only
  path today. It is therefore a guard that must keep passing as T7 and T11 add
  content, not a red stub; the spec classes AC9 goal-based and this records that
  honestly rather than mislabelling a green test. The suffix set matches the
  durable forbidden-string table in the same module, which walks
  `{.md, .json, .toml}`; `.py` is added because `.apm/` ships one. EXECUTE
  reconciles the two walks rather than adding a second.

**Approach:**
- Author a body only for a candidate whose basis can be evidenced; record the
  evidence first, then the body. A candidate that cannot is routed to T8.
- **Measure once, at the task's close, as a whole-suite re-record**,
  transcribed from an observed run by an independent read-only sub-context with
  the run named in the record — the evaluation mode the shipped fixture pins,
  and the same provenance T5 and T9 state. The
  recorded fixture binds to a single digest triple and asserts its result set
  equals its case set, so every corpus change invalidates every prior result;
  a per-topic re-measurement would produce superseded intermediates. T9 then
  performs the third and final whole-suite re-record. There are three in this
  slice, not two: T5's recompile moves the digest triple as surely as T7's.
- Update the exact-set pins in `test_foundation_corpus.py`, the `okf-reference`
  count assertion, and the response vocabulary in `test_provider_contract.py`
  as the admitted set grows, and regenerate the compiled tree and manifest.

**Done when:** every authored topic passes the harness against the closing
measurement, the portability assertion holds, and the foundation pins still
match.

### T8: Leaves the evidence cannot support are declared absent

**Depends on:** T7

**Touches:** packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/, packs/agent-skill-engineering/tests/fixtures/topology-leaves.json, packs/agent-skill-engineering/tests/fixtures/router-cases.json, packs/agent-skill-engineering/.apm/skills/ase-okf-reference/references/okf/, packs/agent-skill-engineering/.okf-generated.json, packs/agent-skill-engineering/tests/pack/test_foundation_corpus.py

**Tests:**
- That case's declared `expected_topics` is the applicable admitted topics, up
  to the shipped three-topic cap the suite asserts over every case, so it is
  **not** a zero-expectation case and cannot exceed the bound the measurement is
  held to. Declaring it `[]` would fail the
  shipped assertion that every zero-expectation case returns nothing, and every
  relief route is closed: AC7 pins that assertion as must-not-weaken, AC6
  forbids re-authoring an expectation after the measuring run, and the Never-do
  forbids weakening a declared expectation to make a record agree with
  itself. (AC5)

- `no stub (goal-based)` — the fallback is exercised by a declared retrieval
  case measured at T9, not by a unit predicate.

**Approach:**
- Author the unpopulated record under the bundle root as the single source and
  let the compiler project it; the harness reads the compiled output.
- The record lives at `concepts/<subdir>/` under the bundle root, which the
  compiler projects and the generated per-directory index routes to, and which
  the shipped topic-set assertion does not reach because it globs the concept
  root non-recursively. Name the subdirectory and the record's compiled `kind`.
- **Split that loop's three assertions, not two.** It pins the topic-set
  identity, then an exact closed-key frontmatter equality, then the
  `executor:`/`attester:`/`remote:`/`tools:` refusal. Only the token refusal
  goes recursive: the identity assertion stays non-recursive, as the nested home
  intends, and the frontmatter equality stays with it, because this record
  carries its own `kind` and a recursive equality pinned to `type: "Reference"`
  would redden on its first run. Without that split this record is the one
  agent-read body in the pack with no inertness control; with a two-way split it
  would be the one with no frontmatter-shape control either.
- The admission harness excludes that record **by its exact identity** — one
  record, at that known compiled path — and never by a marker field, section
  shape, or name pattern a topic body could reproduce. State the exclusion
  that way where the harness derives the admitted set, and give the
  `okf-reference` count assertion its determinate new value.
- Add the fallback case to `router-cases.json` before T9's re-record, so its
  measured outcome lands in the one recorded fixture under the same digest
  binding as every other case. Declare its expected set as the applicable
  admitted topics, authored after T7's admission and before T9 measures — never
  as `[]`.
- Keep the language and execution leaves unpopulated; they belong to 2b.

**Done when:** every leaf is accounted for, and the fallback case is authored
and committed.

**Recorded-fixture state at this task's close.** T8 edits the bundle root and
the compiled tree and adds a retrieval case, so it moves the digest triple and
breaks result-set-equals-case-set. That is knowingly accepted: no T8
done-condition reads the recorded fixture, and the fallback's measured outcome
lands at T9's re-record. This is why the bound is three re-records, not four —
T8 defers to T9 rather than re-measuring.

### T9: Retrieval improves for the new topics without regressing the old ones

**Depends on:** T7, T8

**Touches:** packs/agent-skill-engineering/tests/fixtures/router-cases.json, packs/agent-skill-engineering/tests/fixtures/router-results.json, packs/agent-skill-engineering/tests/fixtures/generic-negatives.json, packs/agent-skill-engineering/tests/fixtures/generic-negatives-results.json, packs/agent-skill-engineering/tests/pack/test_foundation_corpus.py

**Tests:**
- AC6's rates are computed by the shipped suite
  (`packs/agent-skill-engineering/tests/pack/test_foundation_corpus.py`), which
  already asserts exact-set, bounded-selection, precision and recall and caps
  every case at three topics. This task extends that suite rather than adding a
  second one, and raises its `len(cases) >= 20` floor. (AC6)
- The negatives results fixture's three digests and `evaluation_mode` are
  asserted equal to values recomputed from the current tree, in the shape the
  shipped guard already uses for the retrieval record. Without it a stale
  negatives record satisfies both its other assertions forever, and the
  falsifier reads pass against a tree it never measured. (AC7)
- The negatives prompt fixture asserts a count of exactly 40, and the negatives
  results fixture asserts that its result set equals that prompt set — pinned on
  both sides, as the taxonomy transcription already is. Equality alone proves
  the results complete against whatever was authored, leaving the falsifier's
  denominator free to shrink. The retrieval pair's
  result-set-equals-case-set guard does not reach this fixture. (AC7)
- Each of the 24 pinned `(id, measured_topics)` pairs has a measured result
  equal to its pinned pair — per case, read from the T4 fixture this task does
  not write. (AC8)
- Two clean compiles byte-identical; the staged tree carries no authoring-source
  bytes and no checkout-relative path into that source; the staged run reads
  nothing outside it. (AC9)
- The hostile-metadata properties are proven by the compiler's own suite, not
  this pack's: run `pytest packs/catalogue-curation/tests/skills/compile-okf/`
  as a command — `test_apply.py` carries the refusal-before-mutation, the
  rejection of writes resolving outside the output root, and the read-only
  drift check, and `test_parser.py` carries stable diagnostic identity. `catalogue-curation`'s own
  `hostile-title` fixtures cover index-entry escaping, a different property, and
  the same command runs them. Run it; do not import it, and do not assume it. (AC9)
- The provider-side security fixtures inherited from the foundation still pass
  and are unmodified by this change. (AC9)

- `no stub (goal-based)` — every bar is a measured rate over an assembled tree;
  the assertions extend the shipped suite's existing rate checks.

**Approach:**
- Author and commit every new case's `expected_topics` **before** the run that
  measures it, so an expectation cannot be tuned to the observation.
- Add near misses for the new vocabulary and the fixed negative set.
- Raise the shipped `len(cases) >= 20` floor to the 40 AC6 now states.
- Perform one whole-suite re-record under a single digest triple, transcribed
  from an observed run by an independent read-only sub-context, with the run
  named in the record.

**Done when:** every bar is met per case against the pinned pairs.

### T10: The knowledge-provider pattern's failure surface is covered

**Depends on:** T7

**Touches:** packs/agent-skill-engineering/tests/fixtures/provider-pattern-cases.json, packs/agent-skill-engineering/tests/integration/

**Tests:**
- A corpus with no governed source, an ambiguous router selection, a retrieval
  evaluation declaring no negatives, and a handoff granting the generated half
  mutation authority each declare their refusal class and bounded diagnostic,
  and each declared response conforms to the contract's rules. The fixture
  carries a schema version, as the criterion's "versioned" requires and the
  pack's other fixtures do. (AC12)

- `no stub (goal-based)` — fixture conformance over declared responses, in the
  shape the pack's provider-contract suite already uses.

**Approach:**
- Declare each expected outcome before the conformance predicate exists.
- This is fixture conformance in the shape `test_provider_contract.py` already
  uses, not the execution of a runtime guard: the mode is instructions, not
  code, so there is no guard to make fail. The plan says so plainly rather than
  claiming a proof it cannot perform.

**Done when:** all four conform as declared — which is what licenses T11.

### T11: The authoring workflow offers `knowledge-provider` and nothing more

**Depends on:** T10

**Touches:** packs/agent-skill-engineering/.apm/skills/author-or-update-agent-skill/SKILL.md, .../references/, packs/agent-skill-engineering/tests/fixtures/unsupported-mode-cases.json, packs/agent-skill-engineering/tests/pack/test_pack_boundary.py, packs/agent-skill-engineering/tests/skills/author_or_update/test_contract.py

**Tests:**
- The mode loads exactly its four mode-specific modules — the knowledge-provider
  pattern, provenance, retrieval-evaluation, and security-boundary modules,
  named rather than counted — and no other mode-specific module, while the
  common contract's safety-and-authority module still governs every read and
  write. (AC10)
- `SKILL.md` gains a distinct `knowledge-provider` entry sentence establishing
  read-only entry, and a separate write-authorizing transition. The shipped
  sentence reads "Move to `create` or `update` only after an explicit mode
  transition and immediately before the first write" — one gate at the moment of
  writing, which cannot express the two-gate shape this mode needs, so adding
  the mode to that sentence alone would satisfy the assertion while contradicting
  read-only entry. `_transition_sentence` is scoped to the new sentence.
- Entering the mode begins read-only, and a write requires an explicit user
  transition. These are the write-gate properties of the one writable mode this
  slice adds, and they were carried as design prose with nothing verifying
  them. (AC10)
- Nothing under `.apm/**` contains a repository-only path, an
  acceptance-criterion citation, or an internal governance record — re-asserted
  here because this task authors the four mode modules, the highest-risk
  hand-authored surface, after T7's check ran. (AC9)
- A durable table-driven positive control: each forbidden surface form —
  including plural, space-separated, and hyphen-split spellings — is detected,
  and a reworded opening naming no mode is not. (AC11)

- PLAN-time red stub (`packs/agent-skill-engineering/tests/skills/author_or_update/test_contract.py`):

  ```python
  # STUB: AC10 — the mode contract. A backticked match anywhere in the file is
  # already satisfied by the sentence declaring the mode UNAVAILABLE
  # (SKILL.md:31), so these read the Modes list and the unavailable block as
  # separate regions and compare them.
  import pathlib

  SKILL = (
      pathlib.Path(__file__).resolve().parents[3]
      / ".apm/skills/author-or-update-agent-skill/SKILL.md"
  )

  def test_mode_is_advertised_and_not_declared_unavailable() -> None:
      text = SKILL.read_text(encoding="utf-8")
      advertised = _mode_bullet_names(text)
      assert advertised == {"frame", "create", "update", "knowledge-provider"}
      assert "knowledge-provider" not in _unavailable_modes(text)

  def test_mode_entry_is_read_only_and_write_is_gated() -> None:
      text = SKILL.read_text(encoding="utf-8")
      entry = _mode_bullet(text, "knowledge-provider")
      assert "read-only" in entry
      assert "knowledge-provider" in _transition_sentence(text)

  def test_mode_specific_modules_are_exactly_four() -> None:
      assert _modules_for("knowledge-provider") == {
          "knowledge-provider-pattern.md",
          "provenance.md",
          "retrieval-evaluation.md",
          "security-boundaries.md",
      }
  ```

  `stub: true`, and red today for the right reason: `_mode_bullet_names` returns
  three, and the mode is present in the unavailable block. EXECUTE writes the
  five helpers, each scoped to a named region: `_modules_for` reads the mode's
  own bullet's `references/` links, and `_mode_bullet` reads that mode's
  own bullet in the Modes list, never the section opener, because
  "`frame` is the default and is read-only" would otherwise satisfy the
  read-only assertion for every mode. Widening any helper's scope must redden
  the mutation below. The mode contract is one of the six criteria the spec
  declares TDD and was the only one without a stub.
- PLAN-time red stub (`packs/agent-skill-engineering/tests/pack/test_pack_boundary.py`):

  ```python
  # STUB: AC11 — the mode matcher still detects every forbidden surface form.
  import pytest

  DETECTED = [
      ("runtime-package", "use for runtime-package work"),
      ("runtime-package", "use for knowledge providers and runtime packages"),
      ("subagent", "handles sub-agents too"),
      ("plugin", "use for plugins, hooks, and subagents"),
      ("hook", "use for plugins, hooks, and subagents"),
  ]

  @pytest.mark.parametrize("mode,description", DETECTED)
  def test_matcher_detects_forbidden_forms(mode: str, description: str) -> None:
      assert _names_mode(description, mode)

  def test_matcher_does_not_fire_on_neutral_prose() -> None:
      assert not _names_mode("Use when a user asks", "plugin")

  def test_mode_fixture_holds_the_reduced_enumeration() -> None:
      # Red today: the shipped floor is six.
      assert len(_unsupported_modes()) == 5
  ```

  `stub: true` — the matcher table is a **positive control**, and executed
  against the shipped `_names_mode` it passes today, so it is not the red half.
  The count floor is: the live assertion is `len(modes) == 6`, so
  `test_mode_fixture_holds_the_reduced_enumeration` is red at PLAN and goes
  green only when this task removes `knowledge-provider` from the fixture. That
  is the stub's failing assertion; the control is the durable half the guard has
  never had.

**Approach:**
- Add the mode and its four modules. **Author the distinct
  `knowledge-provider` read-only entry sentence and its separate
  write-authorizing transition; do not extend the shipped sentence.** That
  sentence gates `create` and `update` at the first write, so adding this mode
  to it would satisfy the assertion while contradicting read-only entry.
- Remove `knowledge-provider` from `unsupported-mode-cases.json`. The count
  floor **relocates** into the stub's
  `test_mode_fixture_holds_the_reduced_enumeration`; delete the inline
  `assert len(modes) == 6`, do not edit it in place, so the number is stated
  once.
- Update `test_contract.py` in the same commit. Three of its assertions move:
  the exact six-mode set; the hardcoded unavailable-modes tuple, which still
  lists `` `knowledge-provider` `` and would otherwise keep passing for the
  wrong reason once the mode joins the Modes list — the same
  backticked-substring weakness this task's stub repudiates; and
  `AUTHOR_ROUTES`, an exact tuple that reddens the moment the four new
  `references/` modules land. The fixture's `reason` and `baseline` strings and
  their `SKILL.md` counterparts move together.
- Keep the token-run matcher unchanged and add the positive control beside it.

**Mutation proofs:** weaken `_names_mode` to return `False` unconditionally —
the AC11 positive control must fail. Separately widen `_mode_bullet` to return
the whole Modes section, and separately widen `_transition_sentence` to return the FIRST sentence
containing "transition", which is the shipped one naming only `create` and
`update` — each must fail, because the
section opener names `frame` as read-only and would otherwise satisfy it for
every mode. Restore by editing.

**Done when:** the mode is advertised, the five remaining modes are proven
absent, and the matcher's detection half is asserted durably.

### T12: Behavior evidence covers this slice's cases

**Depends on:** T7, T11

**Touches:** packs/agent-skill-engineering/.apm/skills/author-or-update-agent-skill/evals/, packs/agent-skill-engineering/.apm/skills/review-or-optimize-agent-skill/evals/, packs/agent-skill-engineering/tests/fixtures/behavior-results.json

**Tests:**
- Fixtures cover the four foundation cases plus cold-start orientation,
  cross-session resumption, and progressive result presentation. (AC13)
- A `knowledge-provider` case asserts the mode marker and the not-authorized
  write marker, matching how the shipped evals already verify `frame` and
  `update`. This is deliberately **not** tagged to an acceptance criterion: the
  governing gate's eleven M2 fixtures contain no knowledge-provider case, AC13
  enumerates seven of those eleven faithfully, and AC10 already binds the
  mode's read-only entry and write transition. The case is added because a
  writable mode should not rest on prose assertions alone, and it is recorded
  here as work this slice chooses rather than work the contract compels.
- Recorded assertion counts equal declared counts; each result's `source_files`
  is an exact set. (AC13)

- `no stub (manual QA)` — behaviour fixtures are declared before a run and
  graded by an operator-attested runner.

**Approach:**
- Declare markers, checklist items, and seeded defects before running anything.
- Extend the existing digest bindings; do not weaken the equality checks the
  foundation arrived at.

**Done when:** the expanded record passes every binding the foundation enforces.

### T13: Review-case grading is observed, and every observed failure is attributed

**Depends on:** T12

**Touches:** packs/agent-skill-engineering/tests/fixtures/behavior-results.json, packs/agent-skill-engineering/tests/skills/review_or_optimize/test_contract.py, docs/specs/agent-skill-engineering-corpus/qa.md

**Tests:**
- The review results carry all five emitted values — `produces_ok`,
  `output_ok`, `assertions_ok`, `errored`, `passed` — transcribed from a named
  run, so a failure can be attributed. (AC14)
- No per-marker value is recorded. (AC14)
- The QA record carries AC17's five fields for every `tools/` failure this
  slice observed, and drops none. This plan does not restate the fields; AC17
  is the checklist. (AC17)

- `no stub (manual QA)` — the values are transcribed from an observed graded
  run; there is no predicate to write first.

**Approach:**
- Seed with `python3 -m agentbundle pack evals run --pack
  agent-skill-engineering --check behavior --prepare-workspace
  <SKILL>/<EVAL_ID>`, then grade with `--mode in-harness --reports <driver
  payload>`, both from the repository root with the checkout on `PYTHONPATH`.
  A bare `agentbundle` resolves through whatever install is on PATH and would
  grade code outside this worktree. The default `--mode headless` ignores
  `--reports` and grades nothing.
- Transcribe the observed values and name the run.
- Record that the `Mode: review` declaration is enforced at run time and is not
  re-checkable from the committed artifact — the predecessor's disclosure
  carried forward, not closed with an unmeasured value.

**Done when:** the record carries measured values, the run is named, no derived
value appears, and every `tools/` failure this slice observed is present in the
record with AC17's five fields filled.

### T14: The pack's surfaces are current everywhere CI looks

**Depends on:** T9, T11, T13

**Touches:** packs/agent-skill-engineering/pack.toml, packs/agent-skill-engineering/.claude-plugin/plugin.json, packs/agent-skill-engineering/README.md, packs/agent-skill-engineering/.apm/skills/author-or-update-agent-skill/evals/, packs/agent-skill-engineering/.apm/skills/review-or-optimize-agent-skill/evals/, docs/product/changelog.md, docs/architecture/agent-skill-engineering.md, .claude-plugin/marketplace.json, web/src/lib/now-highlights.generated.json

**Tests:**
- Conformance metadata contract passes; both agent-plugin roster enumerations,
  the catalogue navigation map, and the publication roster accept the pack,
  each verified by running its owning gate. (AC18)
- `docs/product/changelog.md` carries a
  `## [agent-skill-engineering][<version>] — <date>` entry matching both
  manifests. (AC18)
- Every test this change added is reachable by a gate CI runs, observed rather
  than assumed. (AC18)
- `agent-skill-engineering-guide-and-docsurl` is still in `[backlog].open` and
  `GUIDE_OPTIONAL_PACKS` is unchanged.
- Both regenerated projections are byte-identical to what their owning
  commands produce, and the site's staleness gate passes. (AC18)
- `catalogue verify` and `catalogue lint --deep` exit 0.

- `no stub (goal-based)` — every check is a gate invocation or a membership
  fact one command answers.

**Approach:**
- Bump `pack.toml` and `.claude-plugin/plugin.json` together, update both eval
  harnesses, and add the changelog entry in the same change.
- **Regenerate both committed projections the bump restales.** The aggregated
  marketplace pins this pack's version, and the `/now/` highlights file is
  projected from every released changelog entry declaring `Highlights` and is
  staleness-gated. Run the repository's release-pipeline regeneration for the
  aggregate and the site projection rather than hand-editing either.
- **Record the `Highlights` disposition** for this release — bullets, or an
  explicit "none, because …" — which the maintainer guidance requires as a
  decision rather than an omission.
- No task in this change alters a command line in either normalized dry-run
  plan, so the shared-test command-plan digests are untouched.
- Update the README's mode and topic-group statements and the architecture
  document's topology, verification, and last-verified sections.
- The self-host recipe does two things: it overlays the include-list packs, and
  it aggregates `.claude-plugin/marketplace.json` across user-capable packs.
  This pack is outside the include list, so no `.claude/` or `.agents/`
  projection results from it — but the aggregate carries this pack's version
  and its parity gate reddens on the bump, so the release-pipeline regeneration
  runs here, alongside the site build that regenerates the `/now/` highlights
  projection. Run both by their owning commands rather than editing either file.

**Done when:** every named gate passes when run directly, not by inference from
a chained target.

## Rollout

Single branch, one PR stack ordered by the layer map. Reversal is per layer:
the corpus layers revert by removing the added bodies and recompiling, since
the compiler is deterministic; the mode layer reverts by restoring
`knowledge-provider` to the unavailable fixture and the count floor to six;
the record layers revert by restoring the prior `workspace.toml` entries. No
layer writes durable state outside the repository, and no migration runs.

## Risks

| Risk | Signal | Mitigation |
| --- | --- | --- |
| Too few leaves can evidence a basis | The admitted set is very small | Accepted: the spec gates on the rule, not a topic count, and T8 records the remainder honestly rather than lowering the bar |
| A shipped topic fits neither basis | T5 cannot state an applicability limit or a governing clause for one of the three | Stop and surface under *Ask first*; do not admit it anyway or weaken the rule |
| The named reviewer becomes a rubber stamp | Every topic records the same reviewer with no recorded reasoning | Accepted and disclosed: the erratum makes soundness a judgment, and the QA record names who made it per topic rather than implying a test proved it |
| Retrieval regresses as the corpus grows | A pinned foundation pair's measured set moves | Per-case gate against a fixture no re-record writes |
| The admission harness is satisfied by construction | It stays green under a topic added without evidence | Seven independent mutation proofs, one per conjunct, including a `doctrine` group missing `retrieved_at` and a body copying the unpopulated record's shape |
| The corpus becomes an encyclopedia | The generic-engineering negative set returns bodies | The RFC's own 5%-of-40 falsifier is a gate |
| The census records boilerplate as evidence | A family's count is dominated by inherited sections | The census is taken under review, not by pattern match |
| Gates pass locally and fail in CI | A surface is absent from an enumeration no local target reaches | T14 runs each owning gate directly, and the three long suites are named and run explicitly: `pytest packs/agent-skill-engineering/tests`, `pytest packs/catalogue-curation/tests/skills/compile-okf/`, and `pytest tests/` |
| 2b's registration trips a ratchet with no headroom | `unsatisfied_dependency` exceeds its ceiling | Measured in T2; surfaced to the owner under *Ask first* before any raise |
| A mode is advertised before its evidence exists | The mode ships with T10 incomplete | T11 depends on T10, so the fixtures pass first |
| A required gate arrives red from the base | A `tools/` test reproduces on the base and this slice cannot make it green | Attributed `inherited` under AC17 and recorded against its owner with the unblocking event named; never absorbed and never re-pinned by this slice |

## Changelog

- 2026-08-28: initial plan. Six dependency-ordered layers; review shape DEEP.
- 2026-08-28: revised against 30 adjudicated round-1 findings.
- 2026-08-28: revised against 25 adjudicated round-2 findings and two owner
  decisions. The workspace-status engine change left this slice entirely —
  measured at 0 true positives and 2 false positives, it dragged core's
  manifest pair, eval harness, packaged `_data` copy, marketplace aggregate,
  self-host projection, changelog, `/now/` projection, and two hard-pinned
  roster tests into a corpus spec, and registering this spec as active clears
  the finding under the existing predicate anyway. Admission was rebuilt on
  RFC-0097 D8's promotion classes with per-class evidence shapes, because the
  census is Gate 2's coverage instrument and cannot admit anything on its own;
  the three shipped topics are back-filled rather than grandfathered.
  Measurement moved into T7 so the admission gate has measured results to read;
  the foundation pins became `(id, measured_topics)` pairs in a fixture no
  re-record writes; the unpopulated record moved to the bundle root, the only
  input the compiler reads; the provider-pattern fixtures now precede the
  mode's advertisement; and the portability assertion covers hand-authored
  `.apm/**` as well as compiled output. (Superseded on the roster point: see the
  round-5 entry — nothing needed wiring, because pytest collects `tests/` by
  directory.)
- 2026-08-28: revised against round 3 and the RFC-0097 erratum of the same
  date. Three rounds of review established that admission's soundness half is
  not mechanizable — a gate over declared expectations, then a class label,
  then a contract citation, was each satisfiable without the substance — so the
  erratum rules that D8's classes gate doctrine claims rather than a topic's
  existence, observed practice is admissible under an explicit applicability
  limit, and a named reviewer owns soundness. AC2 was rebuilt on that rule and
  the three shipped topics are reclassified as `observed-practice` rather than
  claiming a contract that does not govern their heuristics. Also: the
  foundation retrieval pins are now derived in T4 before any corpus change,
  since deriving them after T7 would have captured a moved value; measurement
  is stated as a bounded whole-suite re-record, because the recorded fixture
  binds one digest triple and asserts result-set equals case-set; the census
  roster module is explicitly wired into a gate, because nothing globs
  `tests/roster/` and an unwired module never runs; `topology-leaves.json` lost
  its per-leaf state so the fact has one home; and the body-to-record parity
  check is kept with its rationale stated rather than left as an unexplained
  contradiction of the plan's own mirror rejection.
- 2026-08-28: revision 4, against 21 adjudicated round-4 findings and two owner
  decisions. The workspace-status engine change left this slice entirely and
  became a separate Follow-on; admission was rebuilt on RFC-0097 D8's promotion
  classes; the three shipped topics were back-filled rather than grandfathered.
- 2026-08-28: revision 5, against the RFC-0097 erratum committed the same day.
  Three review rounds established that admission's soundness half is not
  mechanizable — a gate over declared expectations, then a class label, then a
  contract citation, was each satisfiable without the substance — so the
  erratum rules that D8's classes gate doctrine claims rather than a topic's
  existence, observed practice is admissible under an explicit applicability
  limit, and a named reviewer owns soundness. The three shipped topics became
  `observed-practice` rather than claiming a contract that does not govern
  their heuristics.
- 2026-08-28: revision 6, against 17 adjudicated findings, including two
  reversions of this plan's own earlier fixes. The census roster module needed
  no Makefile wiring after all: `pytest tests/` collects that tree by
  directory, and the earlier claim rested on a `grep` that could not see
  directory-level collection — so the wiring, its digest re-pin, and the
  digest-pin file left T3. The 40 generic-engineering negatives were pulled
  back out of `router-cases.json`, because the shipped suite asserts zero
  tolerance for any zero-expectation case returning a topic, which is stricter
  than the 5% falsifier and must not be weakened; they now carry their own
  prompt and results fixtures under the same digest triple, and AC6's bars are
  scoped to the retrieval list alone.
- 2026-08-28: revision 7, against 12 adjudicated round-6 findings. Three were
  residue from the two reversions above — a task still asserting the reverted
  work as fact, two test bullets still demanding the reverted vocabulary, and a
  spec-side fix that never reached the plan. The remaining substantive gaps:
  every task now carries a PLAN-time red stub or a `no stub (mode)` record, six
  of which are compilable and validated; the admission harness's newest
  conjunct gained the sixth mutation it was missing; the unpopulated record
  gained a stated home at `concepts/<subdir>/`, which the compiler projects and
  routes to and which the shipped topic-set assertion does not reach; and the
  negatives results fixture gained, **in the spec**, the completeness assertion
  its digest binding alone did not supply. The plan-side bullet for it landed in
  revision 8, not here.
- 2026-08-28: revision 8. Contract amendment, run through the full cycle after
  an earlier attempt edited the approved plan out of band: `approve-plan`
  refused, its message offered two readings, and the recovery steps scoped to
  the second were applied to the first — preserving the hashes but not the
  gates. `contract-amendment` turned out to be unavailable here, since it
  requires a completed-task evidence binding and no task has run, so both state
  machines were reset and the planning gates re-walked under a new run id.
  Three acceptance-criterion clauses gained plan-side implementation (T5, T8,
  T9), and a scoped re-review then found the amendment had itself implemented
  two of three AC3 obligations and one of two AC2 conjuncts.
  A 122-conjunct coverage audit across all 18 criteria — 104 covered, 7
  uncovered, 11 uncertain — established that the defect was structural rather
  than incidental: the plan had been maintaining a hand-built mirror of every
  conjunct, which four passes each left one short. This revision therefore
  stops mirroring. A task's `Tests:` now name the mechanism and cite the
  criterion as the checklist, and a task closes only when every conjunct of each
  criterion it cites has been walked and evidenced in the QA record. The
  mechanisms the audit found genuinely absent are named in the tasks: the
  reviewer identity's absence from shipped bodies, AC2's scope-bound conjunct,
  the fallback case's three-topic bound, the negatives results fixture and its
  40-prompt count pinned on both sides, AC9's three unimplemented
  hostile-metadata properties, AC10's two write-gate properties for the one
  writable mode this slice adds, AC16's authority requirement, and AC12's
  fixture versioning.
- 2026-08-28: revision 9. Reduction. Revision 8's standing rule was itself
  defective — it bound whole-criterion closure to the first task citing a
  criterion, which the layer split makes unsatisfiable for T1, T4 and T7, and
  its evidence ledger lived in a file only T13 touches. Rather than repair the
  rule governing the mirror, the mirror is gone: `## What this plan does not
  contain` states that the acceptance criteria are the checklist and that a
  `Tests:` bullet exists only to name a mechanism an implementer cannot infer.
  Twenty-two restatement bullets were removed from T3-T6, T8, T9 and T11; the
  mechanism they surrounded stayed, mostly in the Approach sections where it
  already lived. Added: the AC10 red stub, which the spec's own Testing Strategy
  required and which was the one missing of six; the negatives fixtures' join
  key and count, because an equality between a bare-string list and an
  identified list has no defined key; the module path and command that actually
  prove AC9's hostile-metadata properties, which live in the compiler's pack and
  whose `hostile-title` fixtures cover index-entry escaping instead; and the shipped suite
  that already computes AC6's rates, so it is extended rather than duplicated.
  Two changes from revision 8 were reverted as over-reach after adjudication:
  decomposing `applicability_limit` into subfields, where an assertion at T5's
  existing seam suffices, and restating the repository-wide privacy rule locally
  under a carve-out that does not reach a pack fixture.
  The file did not get shorter: 22 restatement bullets left (-47 lines) while a
  red stub, four mechanism notes and this entry landed (+61). That is the
  intended direction even so — prose asserting obligations went down, executable
  claims went up, and the seventh stub is code that compiles and fails rather
  than a sentence that cannot. The spec has not changed since approval.
- 2026-08-28: revision 10. Fix-verification pass on revision 9's eleven fixes,
  which returned four blockers — every one the same defect: a fact stated at
  several sites, corrected at one. "Six mutations" lived at four sites and moved
  at one; the `Touches` obligation covered three tasks and landed on two; the
  two-gate claim lived at three sites and one was corrected while the Design
  section and T11's Approach still directed the reuse the new Tests bullet
  forbids. An adjudication record compounded it by recording the `Touches` fix
  as applied to all three when it reached two; that record now carries its own
  correction. This revision applies each fix at every site and shows the
  before/after counts rather than asserting completion.
  Substantive changes beyond the multi-site sweep: T8's split is three
  assertions, not two — only the grant-token refusal goes recursive, because the
  frontmatter equality is pinned to `type: "Reference"` and would redden on the
  unpopulated record's own `kind`; T11 names the two shipped assertions it
  breaks, the hardcoded unavailable-modes tuple and the exact `AUTHOR_ROUTES`
  tuple; the AC11 count floor relocates into the stub rather than being edited
  in place, so the number is stated once; the `_transition_sentence` mutation
  gains its own kill condition, since the shared one explained only the
  `_mode_bullet` widening; `reviewer` gains the form assertion its absence check
  is scoped to; and the AC9 guard gains a non-vacuity floor and a positive
  control, because a green absence-only walk is indistinguishable from a wrong
  root — the same trap the earlier "7/7 compile-clean" report fell into.
- 2026-08-28: revision 11. AC17 amended to reality after wave 0. The criterion
  pinned four `tools/` failures; by the time the slice reached them upstream had
  fixed two, and a fifth had arrived from the base. It now states no count and
  no list, and instead sorts every observed failure into three classes —
  owned-elsewhere-and-unreached (route and record),
  inherited-and-reached (report as blocking, because a required gate is red for
  a reason this change did not create and absorbing it would make this slice's
  green a lie), and caused-here (fix). That distinction was collapsed before:
  `Makefile:471` names `test_local_ci_shared_test_deduplication.py` explicitly,
  so main's node-count regression is inside this change's gate chain, while the
  two `test_guide_typed_asides.py` ledger tests are named nowhere and are not.
- 2026-08-29: revision 13. AC17's classification procedure is deleted, on the
  owner's authority, and the criterion collapses to a form obligation: the QA
  record names every observed `tools/` failure and carries five fields for each
  — reproducing invocation, base commit, attribution, attributor, and routing —
  with correctness of the attribution left to the named attributor. The reason
  is that the procedure was not converging. Revision 12's own fixes produced
  revision 13's blockers: the set-equality check it added was unsatisfiable
  against the classes the same spec required, because an owned-elsewhere
  failure is by definition invoked by no gate in the chain and so can appear in
  no chain transcript; narrowing observation to "while taking this slice's
  gates" made that class vacuous outright; the transcript artifact the check
  quantified over is produced by no task; and "unchanged tree" read as the base
  tree would have routed every genuine regression to a register instead of
  fixing it, because the class was applied first. Revision 12's headline repair
  was also worthless — redefining "reached" to include required workflow jobs
  replaced the criterion's one mechanizable term, a search of the Makefile,
  with branch-protection state that is not in the tree, and the counter-example
  that motivated it, `tools/test_windows_lock_semantics.py`, is still unreached
  under the new definition because `lock-semantics-windows` is not a required
  check. Decomposed, the old criterion asked a build-time checker to decide one
  term it cannot read, three that exist only in an observation, and one that is
  a causal judgment. This is the same trajectory this plan already records at
  revision 6 for topic admission, where a gate over declared expectations, then
  a class label, then a contract citation were each satisfiable without the
  substance; the resolution there was the RFC-0097 erratum's seam — form
  checked mechanically, soundness by a named reviewer — and AC17 now sits on
  that seam alongside AC2. The class names survive as an enumerated field
  value, which costs nothing, and "no observed failure is dropped" survives as
  the completeness half. The plan's two restatements of the classes are reduced
  to citations of AC17, since four independent copies is what drifted in both
  rounds.
- 2026-08-28: revision 12. Review of revision 11 sustained nine findings, and
  the amendment did not survive its own review intact. Three defects were
  structural. The three-class sort was not total: a red that is environmental
  or non-reproducible was neither inherited nor caused here, so it fell to the
  default reading and would have been reported as blocking — the classes are
  now four, applied in a stated order, with reproducibility tested first.
  "Reached" was grounded in Makefile naming alone, which the repository
  disproves — `tools/test_windows_lock_semantics.py` appears zero times in the
  `Makefile` and runs at `.github/workflows/build-check-windows.yml:163` — so
  the chain is now defined once, as the Makefile targets this slice runs plus
  the required workflow jobs. And AC17's verification row still greped for a
  known-skip block the amended criterion had deleted, which no more
  discriminates a correct sort from any sort than a count did; it now requires
  the transcripts' failing set and the record's classified set to be equal.
  Three further sites carried the old framing after revision 11 claimed the
  correction was complete — T13's heading, T13's Done-when predicate, and the
  Testing Strategy row — which is the fourth time on this change that a
  multi-site edit reached some sites and not all; the sweep is now run over
  both files for every phrase the edit retires, not over the sites the edit
  intended. The routing target was also wrong: `[backlog].open` was declined on
  ceiling grounds, but `workspace.toml:257` already carries
  `guide-blockquote-ledger-has-no-regenerator` on the same subject, and
  extending an existing entry's summary adds no legacy-shaped entry, so the
  ceiling never applied. The blocking class gained the owner, disposition, and
  Risks row it lacked. Revision 11's spec body also narrated its own revision
  history at three sites, which the retcon rule forbids; that history is here,
  where it belongs.
  Amendment record, preserved here because the cohort's machine copy could not
  survive the repair: the contract amended was spec `30c41a9e0a6a` / plan
  `e99576e90cbc` (`4d577d76a`), the completed work at amendment time was T1, T3
  and T4, and the authority and reason are
  `https://github.com/eugenelim/agent-ready-repo/pull/1157#issuecomment-5459816900`.
  The `contract-amendment` transition was fired against that state and
  succeeded, but `wave advance` had been run while the plan was reverted to
  `4d577d76a`, so it pinned T3's pre-execution text rather than the text T3
  executed against — T3's stub note lost its `135` count mid-wave, when the
  live tree measured 137. The pin was therefore unsatisfiable without writing a
  false count back into a completed section, and no re-pin primitive exists.
  The pins are re-taken by re-approving the amended contract rather than by
  replaying the approval gates against superseded content, which would mean
  re-asserting an owner approval rather than obtaining one. T1, T3 and T4 are
  re-pinned as completed at that re-approval; they are not re-executed.
  The count was corrected at all three sites it lived at — AC17, the Follow-on,
  and the Assumption — plus T13's implementing bullet; only the historical note
  explaining why no count is pinned still says "four".
