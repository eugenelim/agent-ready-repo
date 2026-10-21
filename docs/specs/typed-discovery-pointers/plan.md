# Plan: Typed discovery pointers

- **Status:** Approved
- **Spec:** [`spec.md`](spec.md)
- **Constrained by:** RFC-0106 D2; RFC-0103; ADR-0142 D10
- **Repository anchors:** canonical adapter-root resolver and its Core resolver/copy suites; the existing close-work parent lookup; the grammar migration's writer inventory. A source-only AST probe found the existing four-kind tuple and only an `intent:` classifier branch; it establishes a reusable prefix source, not runtime consumer behavior.
- **Retention:** repository-durable spec and plan; approval records bind their fingerprints. Implementers, reviewers, resuming agents, and CI read them. Source/tests, guides, architecture, and the release entry own current truth after closeout.

## Constraints

- One slice PR targets the default branch; T1–T4 are ordered commits within it.
- Author from the prerequisite brief branch's head while its PR is unmerged; rebase onto current `main` with prerequisites present before building.
- No commit or push occurs without owner approval. Do not use bare `git stash`.
- Each task completes on its own tests. Full gates are dispatched once on the slice PR; the local gate is `make lint-ruff lint-mypy` plus the affected targeted suites.
- Expected review shape: DEEP for resolver admission and shared-check integration; WIDE for the manifest-driven sweep. The sweep's manifest, identity comparison, body-byte check, and zero-diff repeat provide its transformation proof.

## Durable-output map

| Output | Task |
| --- | --- |
| Resolver admission, current copies, consumer proof, frozen status pointers, living architecture | T1 |
| Discovery check rule and portable invocation | T2 |
| Writer forms, user documentation, sweep manifest and repeatability evidence | T3 |
| Pack versions, release entry, projections, final verification ledger | T4 |

## Design (LLD)

### Resolver boundary

**Owned by:** T1

T1 extends `_classify_discovery` in the canonical adapter-root source using the registered intent prefix set already represented by `_PARENT_INTENT_KINDS`. The resolver still resolves an admitted typed value through its existing live intent slug index; authoring validation, not this compatibility reader, enforces the target's exact registered kind. Existing `intent:` values and canonical intents paths remain readable. Canonical resolver relation and provenance identifiers remain `intent:<slug>`; the reference prefix does not rename those endpoints.

`packs/core/tests/pack/test_intent_delivery_relations_copies.py` owns the pinned set. Read it again before synchronization; do not freeze today's three-copy count in this plan. T1 adds admission coverage to the existing resolver suites and closure-parent integration to the owning close-work suite. Source docstrings/tests and the living architecture page own this boundary after delivery.

The shipped delivery spec and plan remain frozen. Their status annotations name RFC-0106 D2 and its change to the three criteria. This new spec owns the operative behavior; no old completed task is reopened and no amendment event is fired against a completed run.

### Shared check

**Owned by:** T2

T2 adds Discovery to `packs/core/.apm/skills/work-loop/scripts/lint-graph-pointers.py`. Slice 5 establishes its home and selection contract. If this source is absent because this slice lands first, create only the shared selection/index/diagnostic machinery and the Discovery rule here; do not implement the sibling fields. Reuse that source when slice 5 lands. Both slices have one check and no prerequisite on navigator publication.

A typed target is checked against the registered live intent identity. An untyped intent path or markdown link is classified lexically without opening its target; it can produce only a form violation. A bare live intent slug is also an untyped intent value. Non-intent provenance is outside the field rule. The shared check's source and construction tests own this dispatch.

The `Discovery:` violation codes are exactly these, each emitted only for an intent-valued value, so AC-0007's non-intent values never reach them:

- `discovery-untyped`: a value naming a path under `product/intents/`, as a repository path or a markdown link, or a bare slug of a live intent.
- `discovery-malformed`: a value with an intent prefix (`intent:`, `outcome:`, `opportunity:`, `capability:`) whose remainder is not a slug.
- `discovery-missing`, `discovery-retired`, `discovery-ambiguous`: a typed value whose slug names no live intent, only a retired intent, or more than one live intent.
- `discovery-wrong-kind`: a typed value naming one live intent under a kind other than its registered kind.

A `brief:` or `spec:` value is non-intent provenance here, unlike in `Parent intent:`.

### Writers and corpus

**Owned by:** T3

T3 reuses the grammar migration's source-inventory method, deriving today's Discovery writers rather than copying historical counts. Known Core surfaces are `new-spec/SKILL.md`, `new-spec/assets/spec.md`, its metadata-contract reference, and the close-out guide `guides/core/how-to/close-and-disposition-work.md`, whose refusal reasons state the accepted spec `Discovery:` forms (the `delivery-target-missing`, `delivery-reference-malformed`, `delivery-reference-unsafe`, and `artifact-not-in-graph` entries). The build-loop guide `guides/core/how-to/start-the-work.md` is not a writer; its one sentence listing the fields the work-loop checks gains `Discovery:`. Inspect the product-engineering discovery handoff as a discovery condition. Change it only if it instructs the emitted field's form; bump that pack if changed. Kill condition: a candidate requires an unrelated pack or another pointer field; stop for scope review.

The corpus sweep is reproducible working material under this spec's `notes/`. It records each selected spec path, old header value, target path, slug, registered kind, and replacement. It edits only the selected preamble value and checks unchanged bytes elsewhere. The known 31-value count is evidence from the authoring checkpoint, not a migration limit. Re-derive after rebase. Compare the resolver's relations before and after rewriting against the same widened resolver; the old resolver is not a parity oracle. A repeat run has an empty diff.

### User-documentation draft

**Owned by:** T3

For the metadata-contract reference, adapted to the close-out guide's refusal entries: “When `Discovery:` names an intent, write its registered kind and `Slug:`, such as `outcome:service-reliability`, `capability:account-management`, or `intent:account-self-service`. `Kind:` takes precedence over `Level:`. When it names a research or notes file, use its repository-relative path. New and changed specs are checked for typed, live intent targets; legacy paths remain readable. Discovery records provenance and does not itself assert a feature-delivery route.”

## Tasks

### T1: Registered Discovery forms retain delivery and closure parents

**Depends on:** none

**Verification mode:** TDD

**Tests:**
- **VI-1001.** Extend `packs/core/tests/pack/test_intent_delivery_relations.py` with a parameterized registered-prefix fixture whose `Kind` and `Level` differ. Compare its full expected direct relation with its legacy-path fixture (AC-0001).
- **VI-1002.** Extend existing resolver and hostile-target suites for non-feature resolved provenance, research/notes paths, and each new prefix's malformed, unsafe, missing, and ambiguous values. Assert the existing diagnostic codes and result shape (AC-0002, AC-0003).
- **VI-1003.** Drive the real close-work parent lookup in its owning suite with feature-level outcome fixtures for the two finding-response targets and a non-feature intent; compare before/after parent identities over the same widened resolver (AC-0004).
- **VI-1004.** Run the current copy suite after source synchronization, extending its required set only when a consumer copy has actually landed (AC-0005).

**Approach:** The existing classifier is a grounded callable seam. Its concrete red fixture is added during work-loop PLAN; no production or test file is authored during spec review. Update resolver descriptions and the architecture page, and apply status-only supersession annotations to the frozen pair in this commit.

**Done when:** T1 resolver, closure-parent, and copy tests pass.

### T2: Changed specs reject untyped or unresolved intent Discovery

**Depends on:** T1

**Verification mode:** TDD

**Tests:**
- **VI-2001.** Add Discovery fixtures to the shared check's `test_lint_graph_pointers.py`: canonical kinds, wrong kinds, retired/missing/duplicate targets, legacy paths, relative markdown links, bare live slugs, provenance paths, placeholders, and body-only edits in a disposable Git change (AC-0006, AC-0007, AC-0008).
- **VI-2002.** Run the actual shared CLI on the field's valid and invalid fixture, observing diagnostic fields and repository-byte invariance. Invocation pins cover the field's reachability through the existing work-loop and CI call sites (AC-0008).

**Done when:** T2 Discovery cases in the shared check suite pass.

### T3: Writers emit typed intent pointers and the sweep preserves targets

**Depends on:** T1, T2

**Verification mode:** goal-based check

**Tests:**
- **VI-3001.** Record the derived source-writer inventory, and add construction pins in the shared authoring suite for changed instructions/templates. Pins distinguish registered intent kinds from repository-path research/notes examples (AC-0009).
- **VI-3002.** Capture the current cohort manifest, compare each replacement's target identity, and assert unchanged nonselected headers and body bytes. Compare before/after relation sets through the widened resolver; exercise the missing-target stop on a fixture. Run the sweep twice and record the empty second diff (AC-0010, AC-0011).
- **VI-3003.** Run the named guide structure/title/portable-reference checks after applying the draft to the close-out guide and the check sentence to the build-loop guide (AC-0009; Durable Outputs).

**Done when:** T3 authoring, migration, and edited-guide checks pass.

### T4: Projected runtime and release checks pass

**Depends on:** T1, T2, T3

**Verification mode:** goal-based integration

**Tests:**
- **VI-4001.** Bump Core pack/plugin versions and any other changed pack's pair; add a free-standing release entry with Highlights. Run `agentbundle catalogue self-host --root . --write` and `agentbundle catalogue verify --root .` from live source (AC-0012; Durable Outputs).
- **VI-4002.** Invoke the projected resolver and check on the typed outcome fixture, and run the changed shipped-text citation scan from `packs/AGENTS.local.md` (AC-0012).

**Done when:** T4 projected invocation, release, and catalogue checks pass.

## Slice verification

Run the local lint gate and affected targeted suites before final review. Dispatch the full gates once on this slice PR; record run identifiers and results in the ledger. This evidence is separate from task completion. No `make ci` push precheck or full roster run occurs locally.

## Rollout

The Core patch release delivers the resolver before any newly typed writers or corpus headers become active, in the same slice PR. Each slice lands on the default branch. If navigator code lands later, its branch refresh owns taking this resolver version and updating the copy pin. Rollback restores this slice's source, preamble rewrites, and release changes together; the legacy forms remain readable throughout.

## Risks

- A fixed migration count misses pointers added after authoring. The cohort is derived after rebase and recorded explicitly.
- A missing copy can make typed authoring break only one install path. The landing-time copy test owns the required set.
- Slice branch creation and the pre-build rebase require Git metadata write access.

## Changelog

- 2026-10-08: spec and plan approved together by the repository owner, conditional on the final alignment check passing; that check passed with zero findings across both slices. Both shaping findings are refuted by the replacement adjudication; adversarial round 1 is clean. Reports are under `.context/reviews/f7835c64-6659-4e9a-9317-f7b345bb3a39/`.
- Approved reviewed revisions, before lifecycle-only approval annotations: spec SHA-256 `fd033ddf6f139b13a3d10d21f5d561e8b4ad941da83ee922e071f40ce0924586`; plan SHA-256 `cb3ba2fd580cf17d193c62d0454b993eda4323ab7bfae4cdd32df0d1ad37a966`.
- 2026-10-20: drift amendment, at the owner's request to recheck the approved contract against current `main` before building. `guides/core/how-to/write-the-contract.md` was merged into `guides/core/how-to/start-the-work.md` ("Run the build loop") on 2026-10-15; the spec's Durable Outputs row and this plan's writer list, guide draft, and VI-3003 now name that page. ADR-0142 D10, accepted 2026-10-11, is now cited with an assumption and kill condition: it qualifies a brief's `Parent intent:` only. The spec's never-do rule now says *resolver* diagnostic code, because AC-0006 with the shared check's stable-code contract requires `Discovery:` violation codes; they reuse the check's existing failure suffixes. No acceptance criterion, task, or test changed. No task has started.
- 2026-10-20: amendment review round 1 sustained two findings (owner ruling after two structurally invalid adjudications). `start-the-work.md` has no `Discovery:` text, so the writer list, guide draft, VI-3003, and the spec's Durable Outputs row now name `close-and-disposition-work.md` and limit `start-the-work.md` to its check sentence. The *Shared check* section now names the `discovery-` violation codes, and the spec's never-do rule points to them.
- 2026-10-20: spec re-approved by the repository owner with the drift amendment; round-2 adversarial review adjudicated clean.
- 2026-10-20: plan re-approved by the repository owner with the drift amendment.
