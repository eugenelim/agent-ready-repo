# Spec: Agent Skill Engineering Languages and Execution

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`RFC-0097`](../../rfc/0097-agent-skill-engineering.md); [`Agent Skill Engineering Corpus`](../agent-skill-engineering-corpus/spec.md)
- **Brief:** docs/product/briefs/agent-skill-engineering.md
- **Discovery:** none
- **Contract:** none — the foundation semantic provider request/response contract remains unchanged.
- **Shape:** mixed

> **Hard dependency.** This slice depends on the Agent Skill Engineering Corpus
> slice's census, admission rule, taxonomy partition, and retrieval baseline.
> That dependency is recorded as satisfied in the Assumptions below. The `Status`
> field above, not this banner, carries the authorization to implement.

## Objective

Add portable depth for the language and execution questions that remain outside
the corpus slice: Python/pytest, TypeScript/Node and JavaScript test runners,
process and filesystem cost, pack and CI critical paths, and worktrees, state
locks, and shared-host admission. The topics remain task-shaped guidance for
agent-skill scripts, evaluations, packs, and their execution environments;
they do not become general language or CI handbooks.

These five leaves are admitted on the **doctrine** basis, not observed practice.
No leaf clears the inherited observed-practice rule. The doctrine evidence is
mixed, and it is recorded per claim group rather than per leaf. Three groups
rest on documented public contracts cited externally; three rest on repeated
independent internal failures carried only in the non-projected admission
fixture, because shipped content may not cite this repository's own records. One
topic carries a group of each kind. The
corpus slice implemented doctrine's field validation but deliberately left
doctrine-side body parity unimplemented as a loud failure, naming the successor
slice as its owner. This slice is that successor, so closing that gap is part of
the work rather than an incidental fix.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | The pack gains five topics, so both its topic count and its language-availability paragraph go stale. | `packs/agent-skill-engineering/README.md` | This spec | Both sentences match the admitted set, asserted by the AC7 test rather than by lint alone; `catalogue lint --deep` clean | No README sentence states a topic count or an absence the corpus no longer has |
| Current architecture | RFC-0097 requires each delivery spec to update the planned architecture with its slice's implemented names, paths, and verification evidence. | `docs/architecture/agent-skill-engineering.md` | This spec | Topology counts name 12 admitted and 24 unpopulated leaves; the slice's verification date is recorded | Architecture claims no later-slice surface |
| Release history | The pack's version bump is a released-artifact change. | `docs/product/changelog.md` — a `## [agent-skill-engineering][<version>] — <date>` entry | This spec | Entry present in the same change that bumps the manifests | Entry names the admitted topic set and the language-availability change |
| Interface compatibility | The pack's published surface is consumed externally. | `packs/agent-skill-engineering/pack.toml` and `.claude-plugin/plugin.json`, both authored and edited in lockstep under the pack version-bump rule; the aggregated marketplace manifest, which is regenerated and never hand-edited | This spec | Matching version bump per `packs/AGENTS.md`; publication and roster gates green | Both authored manifests carry the same bumped version, and the aggregate is regenerated |
| Spec index | The index row states this spec's shape and counts. | `docs/specs/README.md` | This spec | Row's criterion and task counts equal this document's | Row matches the shipped spec |
| Reusable learning | Work-loop's `spec-approved` and `plan-locked` gates capture authoring residue. | `project-knowledge` public seam | work-loop | Capture receipts, or the named skip `project-knowledge unavailable` | Receipts distilled at `plan-locked`, or the skip recorded |

## Boundaries

### Always do

- Build on the corpus slice's governed admission, topology, and measured
  retrieval baseline rather than replacing their contracts.
- Keep Python/pytest and TypeScript/Node guidance distinct while applying the
  shared language contracts RFC-0097 defines.
- Keep execution guidance limited to skill scripts, evaluations, pack tests,
  CI, worktrees, locks, shared hosts, and measured machine-load decisions.
- Give every doctrine claim group a promotion class its evidence actually
  satisfies, and, for every source a group cites, record that source's identity,
  when it was read, and its version state. A group whose class carries internal
  evidence cites no source and records that evidence in the fixture instead.
- Re-measure any recorded evidence whose covered content changed. A digest that
  moved is re-measured, never re-stamped onto the earlier observation.

### Ask first

- Changing the semantic provider request/response contract or the corpus
  slice's admission and retrieval thresholds.
- Adding a dependency, runtime-specific claim, or delivery mechanism not
  licensed by the governing RFC.
- Adding a promotion class to the inherited doctrine vocabulary. One such
  addition is authorized for this slice and recorded in the Assumptions below;
  any further one asks again. Implementing the parity check the corpus slice
  left unimplemented is not such a change: it enforces an existing requirement
  rather than widening the rule.
- Adding a known-miss exemption to a graded behavior case after seeing its
  verdict.

### Never do

- Turn a language topic into a general programming-language handbook.
- Claim a runtime profile, `runtime-package`, plugin, hook, or subagent
  capability; those are owned by later slices.
- Re-record the corpus slice's foundation retrieval pins as part of this work.
  Those pins are a non-regression gate: a measurement that moves one is a defect
  to surface, never a pin to rewrite. Their count is asserted in the owning
  fixture test, not restated here.
- Claim maturity for a topic whose governing evidence note withholds it.
- Reword an acceptance criterion, assertion, or retrieval case after seeing its
  measured result.
- Commit personal or host-identifying data in any recorded evidence field.

## Testing Strategy

- Use TDD for topic admission, doctrine-side parity, topology accounting, and
  per-case retrieval non-regression.
- Use goal-based checks for deterministic builds, staged-tree confinement, and
  portability.
- Use measured retrieval for topic distinctness and foundation non-regression.
- Use observed behavior fixtures for the pytest-suite and Node/browser-suite
  cases, and a fresh headless observation for activation, before claiming either
  kind of coverage.
- Prove every new or changed guard by mutation: state the invariant, the test
  that must catch its removal, the exact mutation, and the observed failure.
  The doctrine arm has never executed against any input, so its first exercise
  carries a mutation proof for each predicate limb it newly reaches.

## Acceptance Criteria

- [ ] **AC1 — The five named leaves are admitted.** `python-and-pytest`,
  `typescript-node-and-javascript-test-runners`, `process-and-filesystem-cost`,
  `pack-and-ci-critical-paths`, and
  `worktrees-state-locks-and-shared-host-admission` are admitted topics carrying
  the `doctrine` basis, and none of them remains in the declared-unpopulated
  register. Every taxonomy leaf stays in exactly one set, and neither set names
  a leaf the taxonomy does not have.
- [ ] **AC2 — Language depth remains specific and complete.** The
  TypeScript/Node topic separately covers each of the seven subjects RFC-0097
  assigns it: package and module contracts, lockfile-respecting clean installs,
  child-process behavior, test-runner worker models, browser-worker economics,
  cache keys, and JavaScript/TypeScript security scanning. The Python/pytest
  topic covers the collection, fixture, process-boundary, and temporary-path
  concerns RFC-0097 permits it, without collapsing into the TypeScript/Node
  topic or into a lowest-common-denominator topic. The TypeScript/Node topic
  states, in portable terms, the maturity limit its governing evidence note
  records.
- [ ] **AC3 — Execution economics is bounded.** Process, filesystem, pack/CI
  critical-path, worktree, lock, shared-host, and machine-load guidance stays
  limited to skill scripts, evaluations, packs, and their execution
  environments, and is supported by measured retrieval evidence. No free-text
  field in any artifact this slice records carries an absolute home path,
  username, hostname, or worktree name. That set is the admission record, the
  retrieval and near-miss cases, the eval declarations and their fixture
  payloads, the four re-measured result records, and both the authored and the
  compiled concept roots, whose bodies paraphrase internal incident records they
  may not cite. The host-identifying forms are part of the same shared pattern
  definition the repository-only scan uses, so the two cannot drift apart.
- [ ] **AC4 — Retrieval and baseline safety hold.** New retrieval cases are
  predeclared and measured, meet the corpus thresholds, and preserve every
  pinned foundation result. Both the retrieval record and the generic-negative
  record are re-measured against the tree they describe, since both are bound
  to the same digest triple that admitting a topic moves.
- [ ] **AC5 — Behavior evidence expands.** The pytest-suite and Node/browser
  behavior fixtures are declared and recorded through the established observed
  evaluation process, and every graded result whose pinned source digest this
  slice moves is re-measured rather than re-stamped. Every declared fixture
  payload ships as inert review material and falls inside the export-boundary
  content scan, whose covered suffixes and file floor are extended to include
  each payload this slice adds.
- [ ] **AC6 — Doctrine-side source parity is enforced, not deferred.** For every
  doctrine claim group, the group's shipped fields appear under that group's own
  labelled block inside the topic's `## Provenance and lifecycle` section and
  equal the admission record field-for-field: its clause, its source identities
  *and* dates including each source's exposed version or last-updated date or an
  explicit `none exposed`, and for a `single-ecosystem-contract` group also its
  ecosystem, its version range, and its fixture. A topic carrying more than one
  group carries one labelled block per group, reusing the bolded-label form the
  shipped bodies already use, so every check below has a decidable subject.

  The source floor is stated by promotion class, not by prose:
  `two-runtime-public-contract` and `single-ecosystem-contract` each cite at
  least one source meeting the inherited attributability shape, so an
  externality claim cannot be satisfied vacuously by citing nothing;
  `repeated-observed-failures` cites none and carries its evidence in the
  non-projected admission fixture, because shipped content may not cite this
  repository's own records; and no group in this slice declares
  `severe-safety-failure` or `controlled-measurement`.

  `single-ecosystem-contract` is admissible only for a topic the governing RFC
  classifies as language-specific, which in this slice is the two named language
  leaves. It is the cheapest class by evidence cost, so without that limit it
  would become the default escape from the two-runtime requirement for any later
  topic. Its version range states a lower bound and an explicit upper bound, open
  or closed — a bare point version does not say whether the claim is limited to
  that version or holds from it onward — and its fixture reference resolves to a
  fixture declared and graded under AC5, checked after that grading rather than
  asserted before it.

  A projected source identity takes a checkable form: a non-empty title followed
  by an absolute URL, never a bare hash, a repository path, or a relative
  reference. Every doctrine group's block carries the concept's last-verification
  date and that group's revalidation trigger, equal to the record, so a group
  citing no source still projects a checkable basis rather than nothing. Parity
  holds in both directions — within a group's block, no external reference
  appears that the group's own record entry does not carry, so a group that cites
  nothing cannot borrow a sibling group's citations — and repository-internal
  evidence reaches neither the authored nor the compiled concept root, staying in
  the non-projected admission fixture. The check replaces the corpus slice's
  unconditional failure, and each predicate limb the doctrine arm newly exercises
  carries a recorded mutation proof.
- [ ] **AC7 — Shipped language-availability statements match what shipped.**
  Every shipped statement that today describes the corpus as lacking these
  language families, or states a topic count that admission changes, agrees with
  the admitted topic set: the two workflow `SKILL.md` bodies, the
  language-extension seam reference, and both the language-availability
  paragraph and the topic-count sentence in the pack README. Because two of them
  are digest-pinned, activation is re-observed rather than reconciled by editing.
- [ ] **AC8 — Records and published surfaces are current.** The initiative's
  milestone string names the slice actually in flight; this spec is registered
  as active work while in flight and moved to shipped work at close, in the same
  commit that sets its status; the brief's derived Spec map and both workspace
  registrations that pin its digest agree; the pack version bump, its changelog
  entry, and the architecture and index records land with the change; and the
  `unsatisfied_dependency` ceiling matches the edges that actually exist.

## Assumptions

- The hard dependency on the corpus slice is satisfied. (source:
  `workspace_status.py explain --item spec/agent-skill-engineering-languages-and-execution`
  reports `dependencies: []` with the only finding `unapproved_spec`; the corpus
  spec is in `["ini-009".work].shipped` and reads `Status: Shipped`.)
- No one of the five leaves clears the inherited observed-practice rule, which
  requires two observations in two distinct packs. (source: evidence census over
  `packs/*/.apm/skills/`; the strongest candidate, state locking, has both
  implementations inside `packs/core`.)
- Of the four inherited promotion classes, one is unreachable for these leaves,
  one is unused, and two are used. `controlled-measurement` is unreachable because every row of
  the governing archaeology note is a single dated decision with no repetition
  count, and the class requires at least two repetitions. `severe-safety-failure`
  is unused because no leaf rests on a safety failure with a reproduction.
  The two language topics use `single-ecosystem-contract`;
  `pack-and-ci-critical-paths` carries both a `two-runtime-public-contract` group
  on two independent vendors and a `repeated-observed-failures` group for the
  critical-path claim no vendor states; `process-and-filesystem-cost` and
  `worktrees-state-locks-and-shared-host-admission` use
  `repeated-observed-failures` alone. (source: for the four inherited classes and
  their required fields, `test_corpus_admission.py` `DOCTRINE_CLASSES` and its
  per-class assertions; for the single-ecosystem assignment,
  `docs/rfc/0097-agent-skill-engineering.md` D8's single-ecosystem paragraph; for
  the paired failures, `docs/rfc/0097-notes/execution-economics-archaeology.md`
  chronology table.)
- The two language leaves rest on single-ecosystem evidence, which the governing
  RFC admits for a language-specific topic under a scoped exception rather than
  under the two-runtime rule: it must come from that ecosystem's authoritative
  documentation, be explicitly limited to that ecosystem and version range, carry
  a construction or behavior fixture, and never be generalized into the portable
  floor. The inherited vocabulary carries no class for that shape, so this slice
  adds `single-ecosystem-contract` with those conditions as its required fields.
  This is an *Ask first* widening of a predicate other slices inherit, and the
  repository owner authorized it in session on 2026-08-30 after being shown that
  pytest pairs only with CPython and that Node's core test runner pairs only with
  Playwright inside one ecosystem. The two behavior fixtures this slice already
  produces satisfy the exception's fixture condition. (source:
  `docs/rfc/0097-agent-skill-engineering.md` D8's single-ecosystem paragraph;
  `test_corpus_admission.py` `DOCTRINE_CLASSES`.)
- The brief's sha256 is pinned as `source.revision` in exactly two workspace
  registrations, so each status roll re-pins both. (source: `grep -c` over
  `workspace.toml` returns 2, and the digest appears in no other tracked file.)
- Admitting a topic moves the router source, router body, generated-tree, and
  case-fixture digests, so the retrieval record, the generic-negative record,
  and every graded behavior result pinned to a moved file are re-measured.
  (source: the digest assertions in `test_foundation_corpus.py` and
  `test_pack_boundary.py`.)
- Declined alternatives, recorded because the choice was contested: admitting
  four leaves and leaving TypeScript/Node unpopulated, and admitting none and
  re-declaring all five absent. The owner chose all five on doctrine, having
  been shown that the governing evidence note withholds maturity from the
  TypeScript/Node topic. The accepted risk is that this topic carries the
  weakest distinctness evidence and is the likeliest to fail measurement. A leaf
  that fails measurement is surfaced with the measurement that caused it and
  routed through an approved spec amendment before close, never reworded and
  never withdrawn in flight: the ship transition requires every criterion
  checked, and a deferral marker no longer satisfies it.

## Follow-ons

- Runtime composition profiles remain a separate slice after this one, together
  with the composition and runtime-profile leaves and the remaining two behavior
  fixtures: subagent composition and hook/plugin design.
- Provider-mode and runtime-package availability remain governed by their
  respective approved delivery contracts.
- A first-party or external TypeScript/Node pilot is the evidence that would let
  a later slice withdraw this slice's recorded maturity limit.
