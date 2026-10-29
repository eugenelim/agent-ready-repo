# Plan: Preservation properties from a bounded consumer map

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/core/.apm/skills/new-spec/SKILL.md` step 3
  (repository anchors, analogue rule); the conditional-reference pattern of
  `references/spec-authoring-rubric.md`; the frozen cases in
  `packs/core/.apm/skills/new-spec/evals/evals.json` and their construction
  tests in `packs/core/tests/skills/new-spec/test_repository_grounding_evals.py`;
  the loader pattern of
  `packs/core/tests/skills/work-loop/test_preservation_contract_proof.py`.

## Approach

The rules go into one reference that `new-spec` loads only when the firing
predicate holds, so an isolated change reads one extra sentence and nothing
more. The map-deletion property is already true of the shipped subject
projector for anything that lives in the plan; one pack test binds that to the
reference's rule that the map never lives in `spec.md`. The riskiest part is
behavior, which only a run can show, so the graded runs come last, against the
rebuilt projection.

## Constraints

- `packs/AGENTS.md` § Shipped pack content carries no internal-governance
  citations: the reference states its rules directly.
- `packs/AGENTS.md` § Version bump rule and § Self-hosting projection.
- `tools/lint-pack-test-boundary.py`: a pack test reads nothing above its pack.
- `assets/spec.md` § Acceptance Criteria owns criterion shape; the reference
  cites it.
- `_subject_source.project_legacy_subject` excludes the spec directory from
  the product manifest and enters `spec.md` only through the approved spec
  digest; `_subject_projection.compute_acceptance_fingerprint` excludes task
  projection provenance. `_acceptance.evaluate_verdict` decides from term,
  outcome, and acceptance fingerprint only, and a receipt bound to another
  fingerprint is not fresh (C0's recorded limits and stale-receipt case).

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** the graded runs in T4.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — the how-to guide paragraph | T1 | Guide links the reference | Link resolves to the shipped path |
| Current product truth — brief Spec map row | T3 | Row added; spec `Brief:` line | Row derives `Shipped` |
| Release history — the Core patch AC-0005 states | T3 | Manifests and fragment | AC-0005 |
| Reusable learning — verification ledger | T4 | The four graded runs recorded | The spec's Reusable learning closeout condition |

## Design (LLD)

### Behavior & rules

The reference carries six parts, in this order:

1. **When it fires.** A proposed addition or change becomes a member of a
   model, registry, graph, index, schema, namespace, or collection that existing
   generic operations can observe without explicit opt-in. It does not fire for
   a private helper with a single caller, confirmed by one reference search, or
   for a new entity whose kind every generic read path already excludes behind
   an explicit filter, confirmed by citing the filter on each path. If any
   generic path lacks the filter, the predicate fires. When it does not fire,
   the ordinary step-3 anchors apply and no consumer map is built.
2. **Behavior classes.** Direct readers and writers; selection and
   resolution; default search or presentation; ranking and traversal; full and
   alternate construction; invalidation and update; lifecycle and cleanup;
   serialization; supported public compatibility. Each is checked only when
   reachable.
3. **Discovery.** Repository-native evidence only: effective guidance, the
   substrate's definition and writers, each read path, constructors,
   serializers, update paths, tests, manifests, compilers, and gates. An
   optional code-intelligence capability may speed discovery; its absence
   removes no class and its answer is evidence, not a verdict.
4. **Stop rule.** Stop when every reachable class has a preservation criterion
   or a named gap. A class is unreachable only when the map cites the search
   that found no reader. A reachable class is not dismissed because the new
   member seems not to affect it; it gets a criterion stating the bound, or a
   gap. A named gap is written in the spec's `## Assumptions` and blocks
   review while it stands. The rule counts classes, never files or analogues.
5. **What a preservation criterion adds.** General criterion shape stays with
   `assets/spec.md` § Acceptance Criteria and the authoring rubric, which the
   reference cites. A preservation criterion adds: the old behavior it keeps;
   its allowed delta, often none; an oracle that fails if that behavior moves,
   taken from the base revision rather than the implementation under test
   where possible; and a statement that a sustained review finding against it
   contradicts it. Creation-only tests and "existing tests pass" are not
   preservation evidence. A compatibility oracle exercises the supported
   construction or destructuring surface; an "unchanged file" check forbids the
   change instead.
6. **Where the map lives, and later discoveries.** The map lives in the plan's
   `## Design (LLD)` or review notes, one row per class: class, consumer
   evidence as path and line, and the criterion ID or gap. `spec.md` cites none
   of it, so deleting or rebuilding it changes no criterion. A later discovery
   that changes accepted behavior, scope, a public contract, a durable output,
   or accepted risk takes the controlled amendment and fresh review; one that
   changes only task order, method, or test shape is a plan edit.

Traces to: AC-0001, AC-0002, AC-0003 · none.

Owned by: T1.

### Data & schema

The AC-0003 test commits one product file, `spec.md`, and `plan.md` into a
temporary git repository, following `test_subject_projection.py`'s setup, and
projects the subject with the committed spec and plan digests. Each plan
variant is a new commit. One property with one passing receipt bound to the
first fingerprint is evaluated against each variant's fingerprint. The
mutation commits the map into `spec.md`.

Traces to: AC-0003 · `contracts/delivery/delivery-subject.v1.schema.json`,
`contracts/delivery/acceptance-property.v1.schema.json`.

Owned by: T2.

## Tasks

### T1: `new-spec` loads the shared-substrate reference only when the predicate fires

**Depends on:** none

**Touches:** packs/core/.apm/skills/new-spec/SKILL.md, packs/core/.apm/skills/new-spec/references/shared-substrate-preservation.md, guides/core/how-to/plan-and-execute-non-trivial-work.md, packs/core/tests/skills/new-spec/test_shared_substrate_preservation.py

**Mode:** TDD. The content pins are written first and fail while the
reference is absent; the reference's behavior is proved by T4.

**Tests:**
- Content pins in `packs/core/tests/skills/new-spec/test_shared_substrate_preservation.py`:
  `SKILL.md` step 3 names the reference path; the reference states both
  exclusions, the class-count stop rule, that the map never lives in
  `spec.md`, the later-discovery routing, and the sustained-finding clause;
  it cites `assets/spec.md` and the authoring rubric; it names no path under
  `docs/`.
- `test_repository_grounding_evals.py` and the existing `new-spec` suites pass
  unchanged.

**Done when:** both `Tests:` bullets pass, and
`grep -c 'packs/core/.apm/skills/new-spec/references/shared-substrate-preservation.md' guides/core/how-to/plan-and-execute-non-trivial-work.md`
prints `1`.

### T2: Deleting or rebuilding a plan-resident map leaves fingerprint and verdict unchanged

**Depends on:** none

**Touches:** packs/core/tests/skills/work-loop/test_consumer_map_disposable.py

**Mode:** behavior pin. The projector already holds the property, so the pin
is green on the base; the spec-resident mutation is the failing case.

**Tests:**
- AC-0003 through `_subject_source.project_legacy_subject` over the committed
  temporary repository and `_acceptance.evaluate_verdict`, each loaded by path
  under a pack-and-skill-qualified name with the siblings they load.
- The spec-resident mutation changes the fingerprint and decides
  `insufficient`.

**Done when:** the new module passes.

### T3: Release, projection, and registration

**Depends on:** T1, T2

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.d/*, docs/product/briefs/repository-grounding-preservation.md, workspace.toml, docs/specs/workspace-retirement/inventory.toml, .agents/**, .claude/**

**Mode:** goal-based.

**Tests:**
- AC-0004, AC-0005, AC-0006 commands.
- `agentbundle catalogue self-host --root . --write` leaves no diff on re-run.
- The roster version-bump and brief-coverage checks pass.

**Done when:** every `Tests:` bullet passes.

### T4: Graded runs against the rebuilt and base projections

**Depends on:** T3

**Mode:** visual / manual QA of the rebuilt agent artifact.

**Tests:**
- AC-0001 and AC-0002 graded runs, and one baseline graded run of each case
  against the base's projection, recorded in `notes/verification-ledger.md`.

**Done when:** the ledger records all four graded runs, each with the pack
version it ran against, and the AC-0001 and AC-0002 runs hold every assertion.

## Changelog

- 2026-10-29: spec approved by the owner (Platform Core)
- 2026-10-29: plan approved by the owner (Platform Core)
- 2026-10-29: amended spec approved by the owner (Platform Core) after a controlled amendment moving the T1 guide-link check to `Done when`
- 2026-10-29: amended plan approved by the owner (Platform Core)
