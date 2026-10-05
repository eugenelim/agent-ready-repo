# Plan: Code-intelligence golden composition example

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/code-intelligence/.apm/skills/code-intelligence/SKILL.md`; `references/capability-map.md`; `references/evidence.md`; `references/gaps.md`; `references/investigation-patterns.md`; `scripts/estate_preflight.py`; `packs/code-intelligence/tests/`; `packs/code-intelligence/README.md`; `packs/AGENTS.md#version-bump-rule`.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> execution observations belong in `notes/verification-ledger.md`.

## Approach

Add one pack-owned composition reference that walks a transitive-impact
question through the existing Wicked Estate capability map, preflight, native
query, evidence discipline, source verification, and stopping rule. Pair it
with an absent or poor-fit path that uses labelled repository-native evidence
to answer the same acceptance question. Update the skill and README to route to
the example, then extend pack-local tests and behavior evaluations so the
provider-specific detail stays useful without becoming a Core contract.

## Constraints

- RFC-0079 makes `code-intelligence` the golden example but forbids treating its
  provider shape or current patterns as normative.
- RFC-0104 continues to own the provider-specific pack and its retirement
  condition; this delivery does not trigger or resolve retirement.
- Existing capability-map, evidence, gaps, investigation-pattern, preflight,
  and CLI-contract files remain the canonical homes for their details.
- `packs/AGENTS.md` and `packs/AGENTS.local.md` own version derivation and the
  complete pack release pipeline.
- FEAT-0029 and FEAT-0030 are not prerequisites. Pack-local fixtures model the
  accepted inquiry outcome without pretending to be a production Core seam.
- Core gains no dependency, provider mapping, or Wicked Estate vocabulary.

## Construction tests

**Integration tests:** pack-local evaluations run the provider-fit and fallback
stories; vocabulary tests enforce ownership labels and nonnormative wording;
the existing CLI and preflight suites remain authoritative for native details.
A bounded Core manifest check proves no dependency was added.

**Manual verification:** read the example cold and mark every statement as
Core-owned or provider-owned; any ambiguous statement blocks completion. The
separate five-reader validation hook is not claimed as executed here.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `references/composition-example.md` | T1 | Behavior evaluation and ownership-label assertions | Example links resolve and both paths remain complete |
| Pack release pipeline surfaces | T1, T3 | Version-rule derivation, manifest parity, generated marketplace, changelog, and Highlights-disposition checks | Required release surfaces agree on the target and consumer outcome |
| Skill references and pack README | T1, T2 | Vocabulary, link, and documentation checks | Public story matches shipped pack behavior |
| FEAT-0031 validation disposition | T3 | Named follow-on or explicit no-follow-on result | Closeout does not claim cold-reader validation ran |

## Design (LLD)

### Design decisions

The task-fit story uses transitive impact because the indexed graph can add
resolved relationship evidence beyond bounded text search. The fallback keeps
the question and acceptance bar stable but may provide less detail and must say
so. The example links to provider-owned references for exact mechanics; it
contains only the connective narrative and ownership labels. Traces to AC-0001,
AC-0002, AC-0003, AC-0004, AC-0008, and AC-0009. Owned by T1.

### Interfaces & contracts

No new runtime interface is introduced. The example consumes the existing
`estate_preflight.py` behavior and the exact commands documented by the
capability map and CLI-contract tests. Its reusable side is an outcome-level
inquiry narrative, not a request or result schema. Traces to AC-0001, AC-0004,
AC-0005, AC-0006, and AC-0007. Owned by T1-T2.

### Failure, edge cases & resilience

Missing binary, unsupported version, unavailable or stale index, poor semantic
fit, incomplete edges, low confidence, unresolved nodes, command failure, and
conflict with source either trigger labelled fallback or leave a named gap.
No case installs, authenticates, indexes, refreshes, or silently upgrades the
provider. Traces to AC-0001, AC-0002, AC-0003, AC-0006, AC-0007, AC-0008,
AC-0009, and AC-0010. Owned by T1-T2.

### Dependencies & integration

All provider-specific changes stay under `packs/code-intelligence/`. The pack's
existing dependency on Core is unchanged; Core does not gain a reverse
dependency. Pack-local fixtures represent the question and expected outcome in
prose, invoke only existing pack surfaces, and define no fake Core provider
adapter. Traces to AC-0005, AC-0006, AC-0007, and AC-0010. Owned by T2.

## Tasks

### T1: One worked path separates Core inquiry rules from Wicked Estate details

**Depends on:** none

**Touches:** `packs/code-intelligence/.apm/skills/code-intelligence/references/composition-example.md`, `packs/code-intelligence/.apm/skills/code-intelligence/SKILL.md`, `packs/code-intelligence/README.md`, `packs/code-intelligence/pack.toml`, `packs/code-intelligence/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md`

**Verification mode:** Goal-based documentation and release-pipeline checks plus
manual QA; the automated assertions remain in pack-local test and generated
marketplace output, while the cold-read ownership audit and release records are
captured in `notes/verification-ledger.md`.

**Tests:**
- Documentation tests require a complete provider-fit transitive-impact path and
  a complete absent or poor-fit fallback path (AC-0001, AC-0002).
- Ownership-label assertions cover every Core and provider responsibility named
  by AC-0003.
- Link and duplication checks keep native detail in its existing canonical
  reference (AC-0004).
- Vocabulary checks require nonnormative and open-pattern language (AC-0008, AC-0009).
- Pack metadata checks prove `packs/code-intelligence/pack.toml` and
  `packs/code-intelligence/.claude-plugin/plugin.json` carry the target derived
  under AC-0011; `FORCE=1 make build-self` regenerates matching marketplace
  metadata, and the release entry records the required Highlights disposition.
- Fixture-source and forbidden-content checks prove every committed example and
  evaluation artifact satisfies every AC-0012 exclusion, including real
  hostnames and customer or organization identifiers, without retaining raw
  live output.

**Done when:** a cold reader can follow both paths, each load-bearing sentence
has an unambiguous Core or provider owner, and the AC-0011 release surfaces and
disposition pass their checks.

### T2: Pack-local evaluations protect usefulness without exporting a provider contract

**Depends on:** T1

**Touches:** `packs/code-intelligence/.apm/skills/code-intelligence/evals/evals.json`, `packs/code-intelligence/.apm/skills/code-intelligence/evals/eval_queries.json`, `packs/code-intelligence/tests/pack/**`, `packs/code-intelligence/tests/skills/code-intelligence/**`

**Verification mode:** Goal-based behavior evaluations and contract tests; the
pack-local test and evaluator output is the evidence artifact.

**Tests:**
- Provider-fit evaluation requires current preflight, native invocation,
  material caveats, authoritative verification, and a stopping point (AC-0001,
  AC-0004, AC-0005, AC-0006).
- Provider-fit and fallback fixtures use only synthetic, public, or minimized
  evidence and pass every retained-evidence exclusion in AC-0012, including the
  real-hostname and customer-identifier prohibitions.
- Absence and poor-fit evaluations reach the same acceptance question through
  labelled repository-native evidence without provider setup (AC-0002, AC-0006).
- Existing CLI, preflight, skill, agent, and investigation tests remain green
  with no FEAT-0029 or FEAT-0030 artifact (AC-0005, AC-0007).
- A Core-boundary scan covers manifests, install hooks, tests, and baseline
  acceptance fixtures and finds no code-intelligence or Wicked Estate assertion,
  invocation, or dependency; provider-specific assertions remain pack-local
  (AC-0005, AC-0010).

**Done when:** the full pack-local suite passes and the reusable outcome
evaluation contains no provider-interface requirement.

### T3: The golden example passes pack builds and records its validation follow-on

**Depends on:** T1, T2

**Touches:** `docs/specs/code-intelligence-golden-composition-example/notes/**`, `workspace.toml`

**Verification mode:** Goal-based repository gates; the verification ledger is
the task's evidence boundary and carries the manual cold-read receipt from T1.

**Tests:**
- Targeted code-intelligence pack, skill, evaluation, link, and adapter suites
  pass (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007,
  AC-0008, AC-0009, AC-0010, AC-0011, AC-0012).
- Spec/plan status, traceability, and workspace checks pass.
- Release verification records the baseline versions, version-rule derivation,
  matching manifest and marketplace target, free-standing changelog entry, and
  Highlights disposition required by AC-0011.
- Diff-scoped committed-artifact review proves the AC-0012 minimization and
  untrusted-data boundary across provider-evidence-bearing examples, fixtures,
  evaluation output, authored release prose, and the verification ledger,
  including the real-hostname and customer-identifier prohibitions; the
  generated marketplace check separately proves no provider-derived or new
  identity values entered pre-existing catalogue fields.
- The local lint/type gate passes or its environment blocker is recorded.

**Done when:** the verification ledger maps every acceptance criterion named in
this task to green evidence and closeout records whether the cold-reader hook
is queued, run elsewhere, or explicitly left to CAP-0011 without claiming a
result.

## Rollout

This is documentation and evaluation behavior inside an already optional pack.
It needs no flag, infrastructure, migration, provider change, or delivery order
with sibling specs. Reverting the example and its tests leaves existing pack
runtime behavior intact.

## Risks

- Copying commands or evidence semantics into the example can create two
  normative homes; link and duplication checks must keep the reference thin.
- A graph-friendly question can imply graph preference; the example must say
  why this action fits this question and show deliberate non-graph fallback.
- Pack-local fixtures can masquerade as a Core adapter; they must remain
  narrative cases and assert outcomes rather than interface shapes.
- A single example may still cause overgeneralization; the existing validation
  hook, not this delivery, decides whether a contrasting example is needed.

## Changelog

- 2026-10-04: spec approved by eugenelim as part of the CAP-0011 feature cohort.
- 2026-10-04: plan approved by eugenelim as part of the CAP-0011 feature cohort.
