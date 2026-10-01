# Plan: Delivery knowledge projection

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/product/briefs/acceptance-centered-work-loop.md` at Ready content revision `sha256-bytes-v1:8e2cf33151320b16cf8a12bf852531f262e57b5470dc8105ed121087b0347410`; the reviewed ten-document architecture set at `sha256-set-v1:0ca1b837a37254fdf6279e18f4ed01c6ff96ea8fd1d207b8c780e6aa4d994d02`; Approved Slice 1 spec `sha256-bytes-v1:a4d45422a5d8529c0352e231112955f5e50d49328543e354a201471b85991478` and plan `sha256-bytes-v1:b8aaadeca66402e0b2729f5a53f0f159e4fb2526dd20afea6d9b2e873296f03d`; direct owners `docs/architecture/work-loop-knowledge-handoff.md`, `docs/architecture/work-loop-acceptance-evidence.md`, `docs/architecture/work-loop-review-disposition.md`, `docs/architecture/work-loop-execution-supervisor.md`, and `docs/architecture/work-loop-authority-migration.md`; analogous knowledge lifecycle code in `packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py` and `knowledge_store.py`; construction paths in `packs/core/tests/skills/project-knowledge/`; uncertainty: Slice 2's accepted revision and final review-record surface remain unresolved.

> **Plan contract:** this is the implementation strategy. The current legacy
> whole-plan lock remains authoritative for Slice 3 until Slice 4 removes it
> through its accepted cutover. `initial-plan-review.v1` authorizes terminal
> intent and never grants task-content authority, but it does not enable mutable
> task reprojection in this slice. Substantive plan changes follow the current
> approval path while that lock remains active.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are
> working material before approval, while approval hashes the whole plan.

## Approach

Add the feed and projector over committed Slice 1 semantic evidence and current Slice 2 review facts, then make project-knowledge the sole owner of collection and committed-store validation. Exclude reviewed-envelope, initial-plan-review, plan, task-projection, and mutation-classification inputs from projection. Wire optional post-commit notification and remove reusable capture gates only after pull-scan, replay, quarantine, unavailable-tooling, and retained-work-item parity pass against the predecessor contracts.

## Constraints

- The former Ready transition `4e5f61703514f6f05b0a1876243a63c13cc2926a` and architecture revision `61624180b808f9adca70eab2ed2305adee645ce9` are historical only. The current Ready brief and reviewed architecture revisions are pinned above, and the first-three slice cut is confirmed.
- `acceptance-authority-and-evidence` is Approved at spec `sha256-bytes-v1:a4d45422a5d8529c0352e231112955f5e50d49328543e354a201471b85991478` and plan `sha256-bytes-v1:b8aaadeca66402e0b2729f5a53f0f159e4fb2526dd20afea6d9b2e873296f03d`; its `contracts/delivery/` namespace and record inventory are authoritative for this draft.
- The exact accepted revision for `structured-review-boundary` is unresolved. Its latest inspected spec `sha256-bytes-v1:aa624326320c0faccdd9ae639b9dd62368c10722443f81869175820c2b7da442` and plan `sha256-bytes-v1:062b99437fc3bcd46cf305555220bade0f0548ad3259682684ad6e5575459860` are Draft/Drafting and are not authority.
- Slice 1 owns acceptance authority, reviewed-envelope projection, initial terminal-intent review, and side-effect-free mutation classification. Slice 4 alone owns mutable task reprojection, cancellation, dispatch, and removal of the legacy plan lock.
- No task starts until both predecessor revisions are durable, `Approved` or later, and cited here without restating their owned contracts.
- The current engine remains authoritative; this slice neither starts Slice 4 nor moves procedure, result, acceptance, or review authority.
- The legacy whole-plan lock remains authoritative during Slice 3. `initial-plan-review.v1` supplies terminal intent but cannot authorize a task change or remove that lock before Slice 4.
- Delivery may read only predecessor-defined durable evidence and review facts. Arbitrary session prose, transient attempts, journals, and uncommitted worktree content are not projection inputs.
- `reviewed-execution-envelope.v1`, `initial-plan-review.v1`, plans, task projections, and mutation-classification results are excluded from the knowledge projection policy even when they are durable or reproducible.
- Repository guidance and the accepted predecessor namespace decide final contract paths. Approved Slice 1 fixes the canonical `contracts/delivery/` family; exact Slice 3 record files remain provisional until Slice 2's accepted review-record inventory can be cited.
- Pi is an optional external Slice 6 compatibility target. Slice 3 imports, bundles, installs, and selects no Pi component, and its behavior and verification have no Pi gate.
- Pre-review disconfirming probe: `rg -n -i "knowledge.{0,24}(queue|cursor|retry|acknowledg|skip|admission|retention|revocation)|capture.{0,16}gate" packs/core/.apm/skills/work-loop packs/core/.apm/skills/close-work` found a current work-loop capture gate and no delivery-owned knowledge lifecycle store; T3 therefore removes the gate only after pull parity instead of planning a store migration.
- The spec and plan are repository-durable at the locators above. Implementers, independent reviewers, CI, and close-work are required readers; accepted contracts, current architecture, maintainer guidance, tests, and release history become the stable post-closeout evidence owners; the spec directory freezes after shipment.

## Construction tests

**Integration tests:** A shared conformance matrix feeds durable evidence and review fixtures through notification-delivered, notification-dropped, repeated-scan, cache-deleted, source-superseded, source-revoked, source-deleted, valid-committed-record, invalid-merged-record, unavailable-tooling, and explicit-work-item paths. It compares observation identity and bytes, knowledge-visible candidates, admission and retention decisions, quarantine output, delivery decisions, and delivery-owned durable state against AC-0001 through AC-0010.

**Manual verification:** none — all accepted behavior has deterministic contract, state, or decision oracles.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility / accepted contract namespace | T1, T2, T4 | Schema and feed parity from T1; committed-record quarantine and producer/consumer validation from T2; compatibility and traceability closure from T4 | Canonical schemas, registry entries, committed-read validation, and projections agree at release. |
| Current architecture / architecture sources named by the spec, including baseline `docs/architecture/knowledge-capture.md` | T1-T4 | Architecture review tied to the conformance matrix; T4 updates and verifies the baseline knowledge-capture page, including committed-store read validation and quarantine | Living architecture names final ownership, boundaries, navigation, committed-store read validation and quarantine, and the retained explicit `work-item` seam. |
| Maintainer procedure / knowledge and closeout guidance | T2-T4 | Documented commands pass on pull, quarantine, disabled-provider, and work-item fixtures | Maintainer guidance invokes supported commands without relying on this plan. |
| Release history / package, pack, and changelog surfaces | T4 | Build, version-parity, targeted suites, and changelog checks | Released artifacts and changelog describe the shipped boundary. |

## Design (LLD)

### Design decisions

The durable source fact is the replay source; the projector returns one deterministic observation or no observation and writes nothing. Notification is a best-effort hint after fact commit, while the project-knowledge pull collector owns every operation that requires lifecycle state. Traces to AC-0002 through AC-0004 and AC-0007 through AC-0008. Owned by: T1-T3.

### Interfaces & contracts

The accepted Slice 1 bundle owns acceptance authority, shared delivery-fact identities, semantic transactions, reviewed-envelope derivation, initial terminal-intent review, mutation classification, content safety, capability, audit, compatibility, and namespace imports. Its envelope, initial review, and mutation decision constrain delivery authority and procedure but are not projection inputs. Slice 2 owns review-fact identity, lineage, currentness, and acknowledgement semantics; only facts that its accepted boundary makes current and eligible enter the feed. Slice 3 owns the feed and observation record fields inside the accepted namespace without copying either predecessor's fields. The feed presents a stable, complete snapshot with stateless continuation, and the existing knowledge capture contract remains the owner of explicit `work-item` requests. Final schema paths and backward pointers are a T1 discovery result whose kill condition is any need to redefine a predecessor-owned fact rather than cite it. Traces to AC-0001, AC-0002, AC-0005, and AC-0006. Owned by: T1-T3.

### Failure, edge cases & resilience

Snapshot drift, unsafe or unknown records, and unavailable providers refuse or quarantine without partial delivery state. Dropped notifications recover through pull scanning; repeated scans rely on deterministic identity and knowledge-owned deduplication; committed-store quarantine is disposable and never grants authority. Traces to AC-0001 and AC-0003 through AC-0007. Owned by: T1-T4.

### Dependencies & integration

Slice 1 supplies acceptance authority plus the accepted delivery-fact, semantic-transaction, reviewed-envelope, initial-review, mutation-classification, content-safety, capability, audit, and compatibility contracts. Slice 2 supplies the accepted current report, assessment, disposition, lineage, and acknowledgement surface. Slice 4, not this slice or Slice 1, owns mutable task reprojection and plan-lock removal. Project-knowledge remains the existing capture, storage, enquiry, distillation, and lifecycle owner; work-loop and close-work retain only explicit bounded `work-item` capture. Traces to AC-0001 through AC-0010. Owned by: T1-T4.

## Tasks

### T1: The delivery feed and pure projector satisfy replay and snapshot conformance

**Depends on:** none

**Touches:** accepted Slice 1 supervisor-service and `contracts/delivery/` locations; Slice 2 review-contract locations discovered after its approval; architecture and contract registries selected by the accepted namespace

**Verification mode:** TDD through contract and integration tests

**Tests:**
- A contract suite drives the accepted evidence and review fact readers through complete, paged, changed-snapshot, unknown-version, ineligible-source, content-refusal, and delivery-control-record cases, comparing the feed result with AC-0001 and AC-0002; the negative corpus includes reviewed-envelope and initial-plan-review records plus plan, task-projection, and mutation-classification inputs.
- A table-driven projector suite replays accepted source fixtures and compares canonical observation identity and bytes across fresh instances, policy changes, supersession, and refusal against AC-0002 and AC-0004.
- Schema-parity and backward-pointer checks compare the source contracts with every packaged projection and this spec's final `Contract:` header.

**Grounding:** Use the Approved Slice 1 contract bundle and discover the remaining final paths from the accepted Slice 2 review surface. Stop if the accepted Slice 1 classifier writes task, cancellation, or dispatch state, or if either predecessor lacks the stable fact identity, safe and authorized read boundary, content-policy and audit binding, compatibility rule, or current-and-acknowledged review-fact decision required by AC-0001 or AC-0002; amend the owning predecessor instead of inventing a Slice 3 substitute.

**Done when:** the task's contract, replay, refusal, and parity tests pass and its interface-compatible durable-output evidence exists.

### T2: Project-knowledge owns pull collection and committed-store quarantine

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py`, `packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py`, their package projections, and `packs/core/tests/skills/project-knowledge/`

**Verification mode:** TDD through integration tests

**Tests:**
- Collector fixtures drop notifications, restart, rescan overlapping windows, and replay superseded, revoked, and deleted facts, comparing the current knowledge-visible set, per-source admission or retention decisions, duplicate usability, and delivery-owned state with AC-0003, AC-0004, and AC-0010.
- A positive committed-read fixture passes a current valid `knowledge-captured-observation.v2` record through enquiry and distillation and compares its usable result and empty quarantine view with AC-0009.
- Merge-bypass fixtures introduce malformed, unsafe, unknown-version, and policy-invalid committed records, then exercise enquiry and distillation and compare exclusion, bounded knowledge-owned quarantine reasons, and byte-identical committed source files with AC-0005.
- A delete-and-rebuild fixture removes collector and quarantine projections, reruns the scan, and compares the resulting knowledge-visible candidates and exclusions.

**Grounding:** Extend the existing project-knowledge validation, committed-read, capture, enquiry, and distillation seams rather than adding a second store. Stop if safe quarantine requires delivery to retain collector state or if the current committed-store format cannot distinguish invalid data without mutating its source.

**Done when:** the task's pull, replay, quarantine, and rebuild tests pass and the maintainer procedure records their supported commands.

### T3: Delivery notification is optional and explicit work-item capture remains bounded

**Depends on:** T1, T2

**Touches:** the accepted delivery post-commit port; `packs/core/.apm/skills/work-loop/`, its generated projections, and the established close-work/project-knowledge work-item path

**Verification mode:** goal-based check through end-to-end conformance fixtures

**Tests:**
- The same delivery fixture runs with a successful listener, no listener, dropped notification, refusal, timeout, and provider failure; it compares spec, plan, review, acceptance, readiness, and closeout decisions with AC-0007.
- A state inventory after every path compares delivery-owned files and records against the forbidden lifecycle-state set in AC-0004 and AC-0008.
- Positive and negative close-time fixtures submit deliberate and inferred `work-item` candidates through the existing producer contract and compare capture, refusal, size, privacy, provenance, and observability with AC-0006.

**Grounding:** Reuse the existing work-loop/close-work producer profile and project-knowledge capture validator, and route optional notification through the accepted Slice 1 capability, effect, and audit boundary. Stop if preserving `work-item` behavior requires notification acknowledgement or any reusable-capture gate to remain part of readiness.

**Done when:** the disabled-provider and work-item conformance fixtures pass and no delivery-owned knowledge lifecycle state remains.

### T4: Cross-boundary conformance and durable outputs close the slice

**Depends on:** T1-T3

**Touches:** cross-boundary conformance fixtures, current architecture including `docs/architecture/knowledge-capture.md`, maintainer guidance, release/version surfaces, and `docs/product/changelog.md`

**Verification mode:** goal-based check through integration, build, and documentation gates

**Tests:**
- The shared conformance matrix defined in `## Construction tests` runs AC-0001 through AC-0010; this task adds no second case inventory.
- Package and Core pack build/parity checks compare canonical contracts, bundled projections, and runtime behavior.
- Documentation and status checks verify the final architecture, including the baseline knowledge-capture page's projection, independent lifecycle, committed-store read validation and quarantine, and retained `work-item` account, plus maintainer commands, release versions, changelog, contract traceability, and spec/plan lifecycle state.

**Grounding:** Use the repository's existing targeted package, Core pack, build-self, bootstrap, and spec-status gates after the accepted T1-T3 paths are known. Stop if any output requires starting Slice 4 or changing predecessor authority.

**Done when:** the cross-boundary matrix and repository gates pass, `docs/architecture/knowledge-capture.md` reflects the shipped projection, committed-store read-validation and quarantine boundary, and retained explicit `work-item` seam, and every Durable-output map row has closeout evidence.

## Rollout

- **Delivery:** Land behind the current engine and legacy plan-lock compatibility boundary. Keep existing reusable capture behavior available for parity observation until pull rescan, quarantine, and disabled-provider fixtures pass; then remove only reusable capture gates. Rollback disables projection and restores the prior gates without migrating delivery-owned state. Task reprojection and plan-lock removal remain deferred to Slice 4.
- **Infrastructure:** none — local repository contracts, package/pack code, and existing Git-backed knowledge storage only.
- **External-system integration:** none; an installed listener is optional and cannot become a deployment prerequisite.
- **Deployment sequencing:** accepted Slice 1 and Slice 2 readers and contracts, then T1 feed/projector, T2 pull/quarantine, T3 notification and gate removal, then T4 durable outputs and release closure.

## Risks

- The provisional Slice 2 draft may change a review-fact identity or exact contract file. The plan refuses implementation until its accepted revision is cited and T1 can bind its exact contracts alongside Approved Slice 1.
- A partial or unacknowledged review compatibility write could leak a result that Slice 2 does not consider current. T1 admits review facts only through Slice 2's accepted currentness, lineage, and acknowledgement decision.
- A projection that carries too much source content may leak protected data or instructions. The accepted content-policy boundary and refusal corpus run before observation emission and again before committed knowledge use.
- Pull rescan may miss deletions or supersessions. Complete snapshot and successor fixtures require knowledge-owned reconciliation without a delivery skip store.
- Removing reusable capture gates may accidentally remove close-time work-item capture. T3 keeps positive and negative work-item fixtures independent from observation projection.
- Quarantine may become a second authoritative store. Its view is disposable, rebuildable, knowledge-owned, and excluded from delivery readiness.

## Changelog

<!-- Approval entries only:
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->
