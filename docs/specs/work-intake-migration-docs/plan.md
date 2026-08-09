# Plan: Work-intake migration, compatibility, and documentation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Freeze the RFC-acceptance legacy corpus first, define a small lossless
migration manifest, and extend Group 3's reconciliation/repair seams to plan,
apply, and roll back human-approved conversions. Build the cross-profile
routing matrix from Groups 4-6, then run a source-first documentation and
navigation audit. The initial delivery ends with the dual reader, target
writers, migration and rollback tooling, published guidance, routing
evaluations, and a dated compatibility record. Alias/legacy-reader removal is a
distinct later task gated canonically by AC14 and the approved root-workspace
backlog entry; neither can be satisfied by task ordering alone.

## Constraints

- RFC-0083 fixes the supported legacy shapes, human-routing boundary,
  reader-first/write-new sequence, compatibility duration, rollback ownership,
  documentation surfaces, and removal gates.
- Approval requires the two accepted Group 1 ADRs named in `spec.md`.
- Group 2 owns `contracts/jsonschema/normalized-intake.schema.json` and
  `contracts/jsonschema/workspace-entry.schema.json`; this plan consumes them.
- Group 3 owns workspace parsing, reconciliation findings, fail-closed
  dispatch, and repair-plan/apply mechanics.
- Group 4 owns `work-intake` and the `capture-work` forwarding alias.
- Group 5 owns canonical cross-profile acquisition/routing fixtures; Group 6
  owns refresh-state fixtures.
- `contracts/jsonschema/work-intake-migration-manifest.schema.json` records
  reversible migration facts only; it does not become another requirements
  store.
- `packs/core/seeds/docs/CONVENTIONS.md` is the source for projected
  `docs/CONVENTIONS.md`.
- `guides/` is the public source. `docs-site/src/content/docs/guides/`,
  generated `web/src/content/{packs,journeys}`,
  `.claude-plugin/marketplace.json`, and adapter projections are generated.
- No new dependency or top-level directory is introduced.
- Alias removal is a major core-pack change and cannot land in the initial
  delivery.

## Construction tests

**Integration tests:**

- Run every accepted legacy fixture through parse → finding → human-approved
  plan → manifest → apply → target reconciliation → rollback → legacy
  reconciliation.
- Inject failures at manifest staging, manifest replace, artifact creation,
  workspace staging, workspace replace, and rollback; assert only complete
  reviewed states survive.
- Run the shared routing corpus across the supported Jira, Jira Align, Linear,
  and GitHub profiles and compare byte-normalized results across two clean
  workspaces.
- Generate the docs site from source, build web before docs-site, and verify
  canonical and alias routes.

**Manual verification:**

- Review one conversion proposal for each legacy shape and one
  unknown-extension refusal.
- Inspect a rollback transcript and confirm newly created canonical artifacts
  remain.
- Record the cold-reader pass in
  `docs/specs/work-intake-migration-docs/notes/adopter-route-walkthrough.md`,
  including scope, fixture/build inputs, observed routes/results, run/session
  boundary, reviewer, and date.
- Record the initial AC14/backlog evidence state in
  `docs/specs/work-intake-migration-docs/notes/initial-compatibility-review.md`
  with the same evidence fields. Deferred removal review remains unavailable
  and non-dispatchable from this plan.

## Design (LLD)

### Design decisions

Migration extends the existing reconciliation/repair surface rather than
adding a second workspace parser or public migration skill. The manifest is a
durable, schema-validated operation ledger because rollback must survive
session loss. It records representation changes, not requirements.
Documentation remains source-first, and the routing-evaluation corpus is
versioned beside the public `work-intake` behavior it measures.

The compatibility bridge and alias removal are separate release events. The
initial delivery deliberately retains both readers and the forwarding alias.
The later removal follow-up remains outside this executable task graph until
AC14 and the approved root-workspace backlog entry are satisfied.

Traces to: AC1-AC14, AC19-AC25 · implements
`contracts/jsonschema/work-intake-migration-manifest.schema.json`.

### Data & schema

The migration manifest contains a schema version; operation ID;
repository-relative workspace path; pre-apply workspace fingerprint; exact
legacy TOML slice and membership; approved target entry and membership;
created-artifact paths with pre-existing flags; operation state; applied
fingerprint; rollback state; and review metadata. It excludes source payloads
and requirements.

The exact legacy slice preserves comments and punctuation that parsed TOML
cannot round-trip. Apply validates the target entry against the Group 2
workspace-entry Schema. Rollback validates the applied fingerprint and restores
only the recorded slice; canonical artifacts are never rollback targets.

Traces to: AC1-AC10 · implements all three JSON Schemas named by the spec.

### Interfaces & contracts

`workspace-status` reconciliation emits typed legacy findings. Its repair-plan
surface accepts a human-selected route and emits a manifest-backed operation.
Repair-apply verifies fingerprints, writes the manifest first, then performs
the guarded conversion. Rollback consumes the same manifest and refuses stale
or already-diverged state. Exit/output shapes stay deterministic and
machine-readable.

`capture-work` remains a public alias into `work-intake` during the window and
emits a deprecation notice. It owns no routing behavior. The initial delivery
records a non-dispatchable backlog anchor for a later human-approved removal
artifact instead of scheduling removal here.

Migration authorization resolves from repository policy; alias-removal
authorization resolves from RFC-0083's Approver metadata. Both are
check-before-effect and record identity, role, timestamp, and authorization
source. Missing, ambiguous, stale, or insufficient authorization rejects before
mutation.

Traces to: AC2-AC14, AC25 · implements the workspace-entry and migration-manifest
Schemas.

### State & control flow

A legacy entry moves through:

`detected → non-dispatchable finding → route selected → manifest staged →
conversion applied → target reconciled`.

Failure before complete apply leaves the legacy state. A completed apply may
move through `rollback requested → guard checked → legacy representation
restored`; canonical artifacts remain. Unknown extensions stop at a manual
finding.

Compatibility progresses independently:

`initial compatibility evidence → approved non-dispatchable backlog anchor →
AC14 predicates satisfied → later human-approved planning → removal`.

Traces to: AC2-AC14, AC20.

### Behavior & rules

Only the human-selected artifact kind controls conversion. Comments and
summary are display evidence, never classifiers. Missing specs/plans remain
findings. Unknown extensions remain unchanged. New writers always emit target
entries. Removal remains fail-closed until both canonical sources—AC14 and the
approved root-workspace backlog entry—are satisfied.

Traces to: AC2-AC5, AC11-AC14, AC17, AC23-AC25.

### Failure, edge cases & resilience

Realpath confinement prevents workspace, manifest, or created-artifact paths
from leaving the repository through `..` or symlinks. Fingerprints prevent an
approved plan from overwriting later edits. Operation IDs and manifest state
make apply/rollback idempotent. Unknown entries and malformed manifests fail
closed. Generated docs are rebuilt, never repaired in place.

A clock or release gate that cannot be proven is false. An incomplete audit,
authorization failure, or missing Approver decision retains the alias. Rollback
during the window returns writers to the previous dual-reader release and
never removes target artifacts.

Traces to: AC4-AC14, AC21-AC25.

### Quality attributes (NFRs)

Determinism is checked by byte-equivalent normalized results across two clean
runs. Safety is checked by failure injection, stale-fingerprint refusal,
path-confinement tests, and zero artifact deletion. Documentation completeness
is checked by explicit source, route, link, build, and semantic-search gates.
Privacy is checked across manifest, stdout, stderr, and logs.

Traces to: AC7-AC10, AC17, AC20-AC24.

### Dependencies & integration

The implementation consumes the complete Group 2-6 chain. Migration relies on
Group 2 encodings, Group 3 findings/repair, Group 4 writers/alias, Group 5
profile convergence, and Group 6 authority/refresh fixtures. Public docs are
built by `tools/build-site.py`; site order remains web then docs-site. Pack
metadata and projections follow the catalogue version/self-host rules.

Rollout sequencing and the externally gated removal are defined in
`## Rollout`.

Traces to: AC1-AC25 · consumes all three Schemas.

## Tasks

### T1: Legacy fixtures and the reversible manifest Schema validate

**Depends on:** spec:normalized-intake-workspace-contracts/T4, spec:workspace-routing-invariants/T4, spec:work-intake-surface/T6, spec:tracker-intake-adapters/T7, spec:tracker-refresh-writeback/T6

**Touches:** contracts/jsonschema/work-intake-migration-manifest.schema.json, contracts/README.md, packs/core/tests/skills/workspace-status/fixtures/work-intake-migration/**, tools/test_workspace_status.py, tools/test_workspace_status_cli.py

**Verification mode:** TDD

**Tests:**

**Stub:** draft (uncompiled) — the Group 2 Schema bindings and Group 3 legacy
finding modules are created by upstream RFC-0083 work and are unavailable at
PLAN. First EXECUTE materializes the listed pytest cases as compilable failing
tests before any production edit.

- Add one exact fixture for each RFC-supported legacy shape and
  malformed/missing-artifact variants. Verifies AC1-AC4.
- Add unknown/private-extension fixtures and assert byte-stable manual
  findings. Verifies AC5.
- Add valid/invalid manifest fixtures for every required field, path form,
  fingerprint, created-artifact flag, and operation state. Verifies AC6-AC7.
- Add a schema registry/back-pointer check for the new contract.

**Approach:**

- Copy the released acceptance-time representations into a versioned fixture
  corpus without normalizing punctuation or comments.
- Define a JSON Schema for lossless reversible operation facts, not
  requirements.
- Add the contract to `contracts/README.md` with its owning spec.
- Use repository-relative paths and fixed digest/operation-state vocabularies.

**Done when:** all accepted shapes are pinned, unknown extensions are
characterized, and the manifest validation suite passes without implementation
conversion logic.

### T2: Migration planning is deterministic and human-gated

**Depends on:** T1

**Touches:** packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py, packs/core/.apm/skills/workspace-status/scripts/workspace_status.py, packs/core/.apm/skills/workspace-status/SKILL.md, packs/core/tests/skills/workspace-status/**, tools/test_workspace_status.py, tools/test_workspace_status_cli.py

**Verification mode:** TDD

**Tests:**

**Stub:** draft (uncompiled) — the Group 3 repair types and T1 migration
manifest module are created by upstream or local RFC-0083 work and are
unavailable at PLAN. First EXECUTE materializes the listed pytest cases as
compilable failing tests before any production edit.

- Assert each legacy shape produces a typed non-dispatchable finding with exact
  source, membership, candidate routes, and smallest safe next action. Verifies
  AC2-AC5.
- Assert no plan exists until a human-selected kind/path/membership is
  supplied. Verifies AC3-AC4.
- Assert plans validate target entries against the Group 2 Schema and reject
  out-of-repository paths, symlink escape, duplicates, stale provenance, or
  impossible membership. Verifies AC7-AC8.
- Assert migration authorization is resolved from the configured repository
  role source, records approver identity, role, timestamp, and source, and
  rejects missing, ambiguous, stale, or insufficient authorization before a
  manifest or workspace effect. Verifies AC3, AC25.
- Run planning twice and assert byte-equivalent normalized output. Verifies
  AC20.

**Approach:**

- Extend Group 3's finding and repair-plan types with legacy migration
  operations.
- Keep route selection outside heuristics; comments may appear as quoted
  review context only.
- Build the manifest operation from the exact fixture slice and confirmed
  target.
- Reuse existing CLI JSON/result conventions and exit bands.

**Done when:** every supported legacy fixture produces the same safe plan or
finding on repeated runs and no plan can infer or apply a route without human
input.

### T3: Apply and rollback survive interruption without deleting artifacts

**Depends on:** T2

**Touches:** packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py, packs/core/.apm/skills/workspace-status/scripts/workspace_status.py, packs/core/tests/skills/workspace-status/**, tools/test_workspace_status_cli.py

**Verification mode:** TDD

**Tests:**

**Stub:** draft (uncompiled) — the T1 manifest module and T2 migration
operation types are created by this RFC-0083 work and are unavailable at PLAN.
First EXECUTE materializes the listed pytest cases as compilable failing tests
before any production edit.

- Inject failure before/after manifest stage, manifest replace, artifact
  creation, workspace stage, and workspace replace. Verifies AC8-AC9.
- Re-run apply against pre-state, complete target state, stale state, and
  partially recovered state; assert no duplicate entry, artifact, or operation.
  Verifies AC9.
- Roll back every accepted legacy shape and assert exact legacy
  slice/membership restoration, comment preservation, and canonical artifact
  retention. Verifies AC10.
- Assert stale fingerprints, out-of-repo/symlink paths, changed artifacts, and
  malformed manifests refuse without mutation. Verifies AC7-AC10.
- Assert apply and rollback each re-resolve the repository migration role,
  record authorized identity, role, timestamp, and source, and reject missing,
  ambiguous, stale, or insufficient authorization before any effect. Verifies
  AC3, AC10, AC25.
- Assert stdout, stderr, and logs contain no prohibited data. Verifies AC7.

**Approach:**

- Persist and fsync/replace the manifest before workspace conversion.
- Reuse comment-preserving guarded mutation from Group 3.
- Mark created artifacts with pre-existence facts; rollback never deletes
  either pre-existing or newly created artifacts.
- Make operation state transitions monotonic and compare fingerprints before
  every write.

**Done when:** the full apply/rollback matrix and every failure-injection case
pass, with only complete reviewed workspace states observable.

### T4: The cross-profile routing evaluation matrix converges

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-intake/evals/evals.json, packs/core/.apm/skills/work-intake/evals/eval_queries.json, packs/core/.apm/skills/work-intake/evals/files/routing/**, packs/core/pack.toml, packs/atlassian/.apm/skills/**/evals/**, packs/github/.apm/skills/**/evals/**, packs/linear/.apm/skills/**/evals/**, tools/test-run-pack-evals.py

**Verification mode:** TDD and goal-based check

**Tests:**

**Stub:** draft (uncompiled) — the Group 4-6 router, profile, and refresh
modules are created by upstream RFC-0083 work and are unavailable at PLAN.
First EXECUTE materializes the listed pytest cases as compilable failing tests
before any production edit.

- Add direct-spec, multi-spec brief, cross-repo, incoherent collection/view,
  defect, remember, and status fixtures. Verifies AC19.
- Add Draft, Accepted, Ready, Approved, Implementing, Executing, and Shipped
  refresh fixtures from Group 6. Verifies AC19.
- Assert artifact kind/path, lifecycle membership, processor, authority mode,
  dispatchability, and next action across Jira, Jira Align, Linear, and GitHub.
  Verifies AC19-AC20.
- Run every fixture twice in clean roots and compare normalized outputs.
  Verifies AC20.
- Add near-miss activation cases separating intake, status/triage, refresh,
  defect, and migration intents.

**Approach:**

- Keep canonical expected routing in the core `work-intake` eval corpus.
- Let profile fixtures supply only versioned source mappings and capabilities.
- Use the actual Group 2 schemas and Group 3-6 engines rather than duplicating
  expected logic in the runner.

**Done when:** the complete matrix passes across every supported profile and
two clean runs produce identical results and next actions.

### T5: Adopter documentation teaches one current route

**Depends on:** T2, T4

**Touches:** guides/_shared/how-to/use-work-intake.md, guides/_shared/explanation/work-artifact-responsibilities.md, guides/_shared/reference/work-intake-routing-and-lifecycle.md, guides/_shared/how-to/choose-a-tracker-integration.md, guides/_shared/reference/tracker-vocabulary.md, guides/core/how-to/capture-work.md, guides/core/how-to/migrate-capture-work.md, guides/core/reference/workspace-toml-schema.md, guides/core/explanation/why-a-brief-layer.md, guides/core/how-to/intake-an-external-brief.md, guides/core/how-to/receive-a-product-brief-and-decompose-it-into-specs.md, guides/core/how-to/orient-at-session-start.md, guides/{atlassian,github,linear}/**, guides/README.md, packs/{core,atlassian,github,linear,product-engineering}/{README.md,JOURNEY.md}, guide-nav-baseline.toml, docs/specs/work-intake-migration-docs/notes/adopter-route-walkthrough.md

**Verification mode:** Goal-based check with manual rendered review

**Tests:**

**Stub:** no stub (goal-based check with manual rendered review).

- Search current adopter sources for comment-backed spec reconstruction,
  unconditional feature-to-brief projection, universal one-way tracker claims,
  and non-alias `capture-work` invocation. Verifies AC15-AC17.
- Validate required frontmatter, duplicate slugs, index coverage, existing
  links, aliases, and non-orphaned pages. Verifies AC15-AC17, AC21.
- Trace one cold-reader route from landing/index to start, defer, status,
  refresh, and migration. Verifies AC15-AC16, AC21.
- Record that pass in
  `docs/specs/work-intake-migration-docs/notes/adopter-route-walkthrough.md`
  with scope, fixture/build inputs, observed routes/results, run/session
  boundary, reviewer, and date. Verifies AC15-AC16, AC21-AC22.
- Compare every capability claim with the owning skill/profile source.
  Verifies AC16-AC17.

**Approach:**

- Use `author-product-docs` in retrofit mode.
- Update or create the minimum complete how-to, explanation, reference, and
  migration pages required by RFC-0083.
- Preserve `guides/core/how-to/capture-work.md` as compatibility guidance or
  an alias route during the window.
- Update tracker pages, pack landing pages, and journeys from their canonical
  sources; change the navigation baseline only for deliberate route changes.

**Done when:** current adopter sources contain one consistent work-intake
model, all pages are reachable, no stale semantic search hit remains
unexplained, and the dated adopter-route walkthrough contains every required
evidence field.

### T6: Maintainer docs, site output, and initial compatibility release gates pass

**Depends on:** T3, T5

**Touches:** workspace.toml, packs/core/seeds/docs/CONVENTIONS.md, docs/CONVENTIONS.md, docs/architecture/work-intake-and-artifact-routing.md, docs/architecture/overview.md, docs/guides/**, docs/product/journeys/{pm-intakes-from-tracker,engineer-runs-work-loop,agent-executes-spec}.md, docs/adr/0019-product-intent-ontology-and-brief-projection.md, packs/core/.apm/skills/capture-work/SKILL.md, packs/core/seeds/workspace.toml, packs/{core,atlassian,github,linear}/pack.toml, packs/{core,atlassian,github,linear}/.claude-plugin/plugin.json, docs/product/changelog.md, site.toml, tools/build-site.py, tools/test_build_site_*.py, docs/specs/work-intake-migration-docs/notes/initial-compatibility-review.md, .claude-plugin/marketplace.json

**Verification mode:** Goal-based check with manual compatibility review

**Tests:**

**Stub:** no stub (goal-based check with manual compatibility review).

- Verify conventions, architecture, internal
  adapter/migration/reconciliation/eval guidance, journeys, and ADR metadata
  match the accepted model. Verifies AC18, AC23.
- Audit every supported writer and seed and assert target-only output; assert
  `capture-work` forwards and emits the deprecation notice. Verifies AC11.
- Run manifest-backed rollback against the designated dual-reader release
  fixtures. Verifies AC12.
- Run guide validation, guide-index coverage, site dry run, catalogue gates,
  and the full web-before-docs-site production build. Verifies AC21-AC24.
- Inspect built canonical and alias routes and confirm generated output has no
  hand-authored diff. Verifies AC21-AC22.
- Create
  `docs/specs/work-intake-migration-docs/notes/initial-compatibility-review.md`
  with scope, fixture/build inputs, observed results, run/session boundary,
  reviewer, date, and the initial evidence state against AC14 and the approved
  root-workspace backlog entry. Verifies AC13-AC14.
- Resolve compatibility-policy authorization from repository policy and assert
  the record contains approver identity, role, timestamp, and source; missing,
  ambiguous, stale, or insufficient authorization must fail before release,
  checklist, or workspace effects. Keep the deferred removal's separate RFC
  Approver fields explicitly unsatisfied. Verifies AC3, AC13-AC14, AC25.
- Assert root `workspace.toml` contains one non-dispatchable
  `capture-work-alias-removal` item under `[backlog].open`, conforms to the
  canonical AC14/AC24 contract, and does not invent or dispatch a future spec
  identifier. Verifies AC14, AC24.

**Approach:**

- Edit `packs/core/seeds/docs/CONVENTIONS.md`, then regenerate its projection.
- Update current-state architecture and maintainer guidance after behavior and
  public docs are stable.
- Complete pack metadata/version/changelog changes and self-host after all
  source edits.
- Publish the initial delivery with the dual reader and alias intact.
- Record rollback and release evidence without marking the alias-removal gate
  complete.
- Preserve and validate the approved root `workspace.toml` backlog anchor
  `capture-work-alias-removal`; AC14 and that entry remain canonical and the
  item stays non-dispatchable until a separately approved follow-up is planned.

**Done when:** the initial migration delivery passes all code, catalogue,
eval, guide, link, and site gates; rollback is demonstrated; the compatibility
record and both QA notes are dated and complete; and `capture-work` plus the
legacy reader remain installed.

## Rollout

- **Initial delivery:** T1-T6 only. Ship the reader-first-compatible migration
  path, target writers, reversible manifest/apply/rollback, routing matrix,
  complete documentation, and dated compatibility record. Keep the alias and
  legacy reader.
- **Compatibility window:** maintain the evidence required by AC14 and the
  approved root-workspace backlog entry; neither source is weakened here.
- **Later removal:** outside this executable plan. T6 leaves a non-dispatchable
  root-workspace backlog anchor; a later human-approved spec/task may be
  created only after AC14 and the approved backlog entry are satisfied.
- **Infrastructure:** none. Migration is local, explicit, and
  repository-confined.
- **External-system integration:** no tracker read or write is required to
  migrate or reconcile a workspace. Routing evals use fixtures.
- **Rollback:** disable target writers and return to the prior dual-reader
  release; use the manifest to restore legacy entries without deleting
  canonical artifacts.
- **Irreversibility:** the published removal release is a major
  public-interface change, but repository artifacts and migration manifests
  remain durable.

## Risks

- The legacy fixture corpus may normalize away comments or punctuation needed
  for exact rollback. T1 stores exact TOML slices.
- Migration repair code may drift from Group 3 parsing. Extending the existing
  finding/repair seams keeps one parser.
- A long compatibility period can leave the checklist stale. The deferred
  follow-up must re-run every audit rather than trusting old evidence.
- Group 7 can become a dumping ground for documentation omitted by earlier
  groups. AC23 makes missing phase docs blocking findings.
- Renamed guide routes can silently break because Starlight lacks a native
  link-failure gate. Explicit route/link checks and alias inspection cover the
  gap.
- Pack README-only changes still require version metadata; alias removal
  requires a major core bump.

## Changelog

- 2026-08-09: Initial plan drafted from accepted RFC-0083 with confirmed
  assumptions; the initial migration delivery ends at T6 and records later
  alias removal as a non-dispatchable backlog follow-up.
