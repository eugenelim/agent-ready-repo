# Plan: Independent preservation evidence

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packs/core/.apm/skills/work-loop/SKILL.md`
  § Conditional-reference routing; the conditional-reference pattern of
  `packs/core/.apm/skills/new-spec/references/shared-substrate-preservation.md`
  and its pins in `packs/core/tests/skills/new-spec/test_shared_substrate_preservation.py`;
  `packs/core/.apm/skills/work-loop/references/mutation-proof.md`; the frozen
  case in `packs/core/.apm/skills/work-loop/evals/evals.json`; the loader and
  store helpers of `packs/core/tests/skills/work-loop/test_preservation_contract_proof.py`.

## Approach

The rules go into one `work-loop` reference loaded only when accepted criteria
include a preservation property, so other work reads one extra table row. The
evaluator cannot tell an independent oracle from a tautological one, so the
suite puts that check where the receipt is produced: a receipt passes only when
its oracle passes on the implementation under test and fails once that
oracle's named mutation is applied. The fixture substrate is built first, because every family's
oracle and mutant depends on its production paths; the graded runs come last,
against the rebuilt projection.

## Constraints

- `packs/AGENTS.md` § Shipped pack content carries no internal-governance
  citations, § Version bump rule, and § Self-hosting projection.
- `tools/lint-pack-test-boundary.py`: a pack test reads nothing above its pack.
- C0's recorded evaluator limits: the verdict reads only term, outcome, and
  acceptance fingerprint; `producer.class`, `observation.type`, and `count` are
  not read; a receipt binds to its criterion only through the evidence store's
  routing; a failing required term decides `insufficient`.
- Pack tests run on Python 3.11 in CI, so the compatibility snippet may use a
  `match` class pattern.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** the graded runs in T4.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — the how-to guide paragraph | T2 | Guide links the reference | Link resolves to the shipped path |
| Current product truth — brief Spec map row | T3 | Row added; spec `Brief:` line | Row derives `Shipped` |
| Release history — the Core patch AC-0016 states | T3 | Manifests and fragment | AC-0016 |
| Reusable learning — verification ledger | T4 | The graded and baseline runs recorded | The spec's Reusable learning closeout condition |

## Design (LLD)

### Behavior & rules

The reference carries five parts, in this order:

1. **When it loads.** The accepted criteria include a preservation property:
   an existing behavior kept, its allowed delta, and an oracle. `new-spec`'s
   shared-substrate preservation reference owns how such criteria are written;
   this reference owns the evidence that satisfies them.
2. **What makes evidence independent.** The oracle's expected side comes from
   something other than the implementation under test: the base revision, a
   reading of the input that does not call the implementation, or a stated
   table. The oracle is run against one named single-edit mutation of the
   implementation and seen to fail, recorded under the mutation-proof
   reference's proof record. An oracle that still passes under its mutation is
   not evidence.
3. **The five families.** Conservation runs base and head over the same inputs
   and compares results within the allowed delta. Equivalence defines semantic
   equality outside the evidence, compares full and alternate construction,
   and shows the equality can tell two graphs apart. Lifecycle drives create,
   update, delete, and rebuild through production paths and checks nothing
   dangles after removal. Compatibility exercises the supported construction
   and destructuring surface with the repository's own compiler or runtime.
   Bounded work measures a one-file edit against the bound its criterion
   states, reported as a command result within or over budget; no count is a
   universal limit.
4. **Through existing seams.** Evidence is the repository's own tests and
   gates, recorded against the current subject. No new gate, harness, or tool
   is required. An absent optional pack, code-intelligence capability, or
   benchmark tool lowers nothing: a family that cannot be produced leaves the
   property unsatisfied until the owner narrows the criterion.
5. **When the work stays incomplete.** Missing evidence; stale evidence, from
   a subject other than the current one; tautological evidence, whose expected
   side reuses the implementation or whose oracle has no failing mutation; and
   feature-only evidence, which proves the new member exists. Each leaves the
   property short of `supported`, and a property short of `supported` blocks
   completion.

Traces to: AC-0013, AC-0014, AC-0015 · none.

Owned by: T2.

### Data & schema

The fixture substrate lives in
`packs/core/tests/skills/work-loop/fixtures/preservation-substrate/` as
`base.py` and `head.py`, loaded by path under pack-and-skill-qualified names.
The corpus is a mapping of file names to lines of the form `def NAME`,
`call NAME`, and `value NAME`; the base implementation ignores `value` lines.
Nodes carry kind, file, and name; edges carry kind and their endpoints' names.
The public result type is a frozen dataclass whose new field has a default and
comes last.

Each named mutation is one exact `str.replace` over `head.py`'s source whose
old text occurs exactly once, loaded as a separate module:

| Property | Term | Mutation |
| --- | --- | --- |
| ordinary calls | differential resolver | the resolver's kind filter removed |
| default search | default query | the default for including values flipped to true |
| default search | explicit query | the explicit path drops the name match on value nodes |
| equivalence | equivalence harness | the update path skips relinking the edited file's call edges |
| lifecycle | create | the build parser skips `value` lines |
| lifecycle | update | the update path keeps the file's old value nodes |
| lifecycle | delete | removal deletes the file's definition nodes but not its value nodes |
| lifecycle | rebuild | rebuild parses the stored corpus with `value` lines skipped |
| compatibility | downstream compile | the new field's default removed |
| bounded work | invalidation count | the update path invalidates every node |

The earlier head source for the stale case is `head.py`'s source with one
trailing comment line appended. A receipt's `lineage.criterion_ref` is its
property ID, so the store's routing binds it. The tautological oracle resolves
both sides with the implementation under test. The feature test asserts that a
build holds a value node for each `value` line.

Traces to: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012 · `contracts/delivery/acceptance-property.v1.schema.json`,
`contracts/delivery/evidence-receipt.v1.schema.json`.

Owned by: T1.

## Tasks

### T1: Fixture substrate, oracles, producer, and store verdicts

**Depends on:** none

**Touches:** packs/core/tests/skills/work-loop/test_preservation_evidence.py, packs/core/tests/skills/work-loop/fixtures/preservation-substrate/base.py, packs/core/tests/skills/work-loop/fixtures/preservation-substrate/head.py

**Mode:** goal-based. The mutants are the failing cases.

**Tests:**
- AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012 in `test_preservation_evidence.py`, through
  `_evidence_store.EvidenceStore`, `_acceptance`, and `_security_capability`,
  loaded by path with the C0 module's loader and store helpers copied under
  new qualified names.
- Each mutation's old text occurs exactly once in `head.py`.
- The fixture modules import nothing outside the standard library.

**Done when:** the new module passes.

### T2: The `work-loop` preservation-evidence reference

**Depends on:** none

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/references/preservation-evidence.md, guides/core/how-to/plan-and-execute-non-trivial-work.md, packs/core/tests/skills/work-loop/test_preservation_evidence_reference.py

**Mode:** TDD. The content pins are written first and fail while the
reference is absent; the reference's behavior is proved by T4.

**Tests:**
- AC-0013 and AC-0014 as content pins in
  `test_preservation_evidence_reference.py`.
- The existing `work-loop` content suites that read `SKILL.md` pass.

**Done when:** both `Tests:` bullets pass, and
`grep -c 'packs/core/.apm/skills/work-loop/references/preservation-evidence.md' guides/core/how-to/plan-and-execute-non-trivial-work.md`
prints `1`.

### T3: Release, projection, and registration

**Depends on:** T1, T2

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.d/*, docs/product/briefs/repository-grounding-preservation.md, workspace.toml, docs/specs/workspace-retirement/inventory.toml, .agents/**, .claude/**

**Mode:** goal-based.

**Tests:**
- AC-0016 and AC-0017 commands.
- `agentbundle catalogue self-host --root . --write` leaves no diff on re-run.
- The roster version-bump and brief-coverage checks pass.

**Done when:** every `Tests:` bullet passes.

### T4: Graded runs against the rebuilt and base projections

**Depends on:** T3

**Mode:** visual / manual QA of the rebuilt agent artifact.

**Tests:**
- AC-0015 graded run, and one baseline graded run against the base's
  projection, recorded in `notes/verification-ledger.md`.

**Done when:** the ledger records both graded runs, each with the pack version
it ran against, and the AC-0015 run holds every assertion.

## Changelog
