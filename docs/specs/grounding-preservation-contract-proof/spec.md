# Spec: Preservation records through the acceptance evaluator

- **Status:** Shipped
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** brief:repository-grounding-preservation
- **Discovery:** none
- **Depends on:** spec:acceptance-authority-and-evidence
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Contract-fit result`,
> `Durable Outputs`, `Follow-ons` and `Assumptions` are working material.

## Outcome

Platform Core maintainers can see, from tests that run in seconds, that the
shipped acceptance evaluator represents and decides the six preservation
properties exposed by `mikeparcewski/wicked-estate` PR 207 with no
grounding-specific schema or authority path. Success is a green targeted suite
in which every valid sample is `supported`, every invalid or mutated sample
leaves `supported` for its named reason, and this spec records whether the
existing contract is sufficient.

## What Changes

- Six preservation property-and-receipt samples, their five rejection cases,
  and their single-field mutations — a new test module beside the Slice 1
  evaluator tests in `packs/core/tests/skills/work-loop/`.
- The contract-fit verdict and the evaluator's observed limits — the
  `Contract-fit result` section below.

## Contract-fit result

**Existing contract sufficient.** Tested against revision
`42d02f315f22c4f25653644212c7615ada79f1d7`, which contains acceptance-centered
Slice 1 (shipped in `9d39eae8b`). All six properties are expressible in
`acceptance-property.v1` and `evidence-receipt.v1` without a schema change, and
no upstream amendment is routed.

All six properties use exact-subject freshness, so path-set freshness is not
exercised here.

Bounded-work evidence uses the existing `command-result` observation type with
the normalized outcomes `within-budget` and `over-budget`, supplied by the
`ci-runner` producer class. The projection table in
`docs/architecture/work-loop-acceptance-evidence.md` §10 maps a goal-based check
with an exact command to `command-result`, so no new term is needed. The two
schemas list observation types only as examples and leave the field an open
string, so `benchmark-result` would also be admissible. The term choice does not
change the verdict; see the first observed limit below.

The evaluator decides a verdict from three receipt facts only: the selected
term, the normalized outcome, and the acceptance fingerprint. These limits are
observed and pinned by the suite, not changed:

- `producer.class`, `observation.type`, and a term's `count` are not read at
  verdict time. One matching receipt satisfies a term whatever its `count`.
- A receipt's `lineage.criterion_ref` binds it to its property only through the
  evidence store's per-criterion routing. A receipt passed straight to
  `evaluate_verdict` is not checked against the property.
- A required term whose receipt carries a failing outcome decides
  `insufficient`. Only a term named in the property's contradiction expression
  decides `contradicted`.
- The reserved `supported-review-failure` term counts only when the property's
  contradiction expression names it. The schema says every property includes
  it, but `validate_property_dict` accepts an expression without it, including
  `none`, and the evaluator does not add it.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | The brief's later slices read the contract-fit verdict before C1 starts. | This spec's `Contract-fit result` section and the brief's Spec map row | Platform Core | The targeted suite is green at the recorded revision | The section states the verdict and the revision, and the Spec map row derives `Shipped`. |
| Release history | Any change under `packs/core/`, tests included, ships under a new Core version. | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a fragment in `docs/product/changelog.d/` | Core pack release maintainers | Both manifests read `3.1.30`; the roster version-bump test passes | AC-0011's scope check shows no path under `packs/*/.apm/` or `packs/*/seeds/`. |

## Agent Rules

### Always do

- Drive every verdict through the shipped entry points:
  `_acceptance.evaluate_verdict`, `_acceptance.validate_property_dict`,
  `_evidence_store.validate_receipt_dict`, and
  `_evidence_store.EvidenceStore.evaluate_verdicts`.
- Load the scripts by path under a pack-and-skill-qualified module name.
- Use only the standard library and generic placeholder identities.

### Ask first

- Any change under `packs/core/.apm/**`, `packs/core/seeds/**`, or
  `contracts/**`.
- Any change to a version beyond the Core patch bump that a `packs/core/`
  change requires.
- Recording any verdict other than "existing contract sufficient".

### Never do

- Add a schema, a schema field, a grounding-specific authority path, or a new
  persistent state record.
- Add a new module boundary or dependency; the change is one test module.
- Change `new-spec`, consumer discovery, operational-safety, or reviewer
  guidance.

## Testing Strategy

- **Valid samples, rejections, mutations, and bounded work (AC-0001, AC-0002,
  AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008):** goal-based. The targeted pytest module passes. The evaluator
  already exists, so a TDD red is not available; the mutation cases are the
  proof that each verdict can fail.
- **Observed limits (AC-0009):** goal-based pins in the same module, so a later
  evaluator change that enforces a limit shows up as a failing pin.
- **Contract-fit record and scope (AC-0010, AC-0011):** goal-based. A text check
  reads this spec's `Contract-fit result` section, and AC-0011's scope check
  lists the changed paths.

## Acceptance Criteria

Terms:

- **The six properties** are: ordinary calls get no synthetic-value targets;
  default search excludes synthetic values unless asked; full and incremental
  builds give the same semantic model; a one-file edit stays within its accepted
  invalidation budget; added values are contained, reachable, updated, and
  removable; existing supported Rust consumers still compile.
- **A store verdict** is the verdict `EvidenceStore.evaluate_verdicts` returns
  after the receipts are appended through `append_receipt`.
- **A sample** is one property record plus one passing receipt for each of its
  required terms. Every sample's contradiction expression is
  `supported-review-failure`. The lifecycle sample has the four terms create,
  update, delete, and rebuild under `all`; every other sample has one term.
- **The representative receipt** of a sample is the receipt for its first
  required term.

### Valid samples

- [x] **AC-0001.** For each of the six properties, the property record passes
  `validate_property_dict`, each receipt passes `validate_receipt_dict`, and the
  store verdict is `supported` on every member of `SUPPORTED_ADAPTERS`. Those
  validators refuse a missing required field and an undeclared field. Their
  agreement with the canonical schema files is owned by
  `tests/roster/test_acceptance_schema_parity.py` and
  `tests/roster/test_evidence_store_schema_parity.py`, because a pack test may
  not read above its pack.

### Rejections

- [x] **AC-0002.** Missing required term: the lifecycle property requires the
  four terms create, update, delete, and rebuild under `all`. With the delete
  receipt absent, the store verdict is `insufficient`.
- [x] **AC-0003.** Wrong subject: a passing receipt whose `lineage.criterion_ref`
  names a different property leaves the store verdict `insufficient` with an
  empty `receipt_refs`. A passing receipt bound to a different subject's
  acceptance fingerprint also decides `insufficient` with an empty
  `receipt_refs`.
- [x] **AC-0004.** Stale receipt: for each of the six samples, when every
  receipt carries an earlier acceptance fingerprint of the same subject, the
  store verdict is `insufficient` with an empty `receipt_refs`.
- [x] **AC-0005.** Unsupported outcome: in the ordinary-calls sample, a fresh
  receipt with outcome `unknown`, which the term's `outcomes` does not list,
  decides `insufficient`, and its `receipt_id` is in `receipt_refs`.
- [x] **AC-0006.** Contradiction: in the ordinary-calls sample, a fresh
  `supported-review-failure` receipt decides `contradicted` even though the
  satisfying receipt is also fresh.

### Mutations

- [x] **AC-0007.** For each of the six valid samples, each change below, made
  alone, moves the store verdict from `supported` to the named verdict with the
  named `receipt_refs`:
  - the representative receipt's outcome set to `unknown` → `insufficient`;
    `receipt_refs` holds every receipt of the sample;
  - the representative receipt's selected term set to `unnamed-term`, which the
    property names nowhere → `insufficient`; `receipt_refs` holds every receipt
    of the sample;
  - the current acceptance fingerprint passed to `evaluate_verdicts` changed →
    `insufficient`; `receipt_refs` is empty;
  - the property's `authority_ref` emptied → `unapproved`; `receipt_refs` is
    empty;
  - one fresh `supported-review-failure` receipt added as a new record →
    `contradicted`; `receipt_refs` holds every receipt of the sample and the
    added one.

### Bounded work

- [x] **AC-0008.** The invalidation-budget property requires a `command-result`
  term with outcome `within-budget`. A receipt with `over-budget` decides
  `insufficient`.

### Observed limits

- [x] **AC-0009.** The suite pins each limit the `Contract-fit result` section
  names, on the ordinary-calls sample, through `evaluate_verdict`:
  - a receipt with a different `producer.class` decides `supported`;
  - a receipt with a different `observation.type` decides `supported`;
  - one receipt for a term whose `count` is 2 decides `supported`;
  - a receipt with a different `lineage.criterion_ref` decides `supported`;
  - a receipt with outcome `fail` decides `insufficient`, not `contradicted`;
  - with the contradiction expression `none`, and again with
    `regression-detected`, which names another term but not
    `supported-review-failure`, a fresh `supported-review-failure` receipt
    beside the satisfying receipt decides `supported`, not `contradicted`;
  - `validate_property_dict` returns `(True, "ok")` for both of those
    expressions.

### Record and scope

- [x] **AC-0010.** The `Contract-fit result` section states "Existing contract
  sufficient" and the full tested revision.
- [x] **AC-0011.** The scope check, `git diff --name-only "$(git merge-base origin/main HEAD)" HEAD`
  run after every change is committed, lists only paths under
  `packs/core/tests/`, `docs/specs/grounding-preservation-contract-proof/`,
  `docs/product/briefs/repository-grounding-preservation.md`,
  `workspace.toml`, `packs/core/pack.toml`,
  `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, and
  `docs/specs/workspace-retirement/inventory.toml`.

## Follow-ons

- Platform Core: [`docs/product/briefs/repository-grounding-preservation.md`](../../product/briefs/repository-grounding-preservation.md)
  — slices C1, C2, and C3 are confirmed there and start from this verdict.

## Assumptions

none
