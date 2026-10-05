# Plan: Delivery knowledge projection

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/product/briefs/acceptance-centered-work-loop.md` at Ready content revision `sha256-bytes-v1:8e2cf33151320b16cf8a12bf852531f262e57b5470dc8105ed121087b0347410`; the reviewed ten-document architecture set at `sha256-set-v1:0ca1b837a37254fdf6279e18f4ed01c6ff96ea8fd1d207b8c780e6aa4d994d02`; the amended and approved Slice 1 spec and code-mode plan at `fd70edd51f7b45c4d0714223c07371798cca3391`, its architecture and release closure at `cc4b6eb20e2fce7c58dac8958de27eb6c8a4e146`, and its current implementing spec/plan bytes at `sha256-bytes-v1:2415a8d18a06a6ee2a23eddb82c0dcb600cbc2ba7fdfb0338cadb16a923aa054` and `sha256-bytes-v1:09dc6f51bd3656a0d9ad15e5e9e8a82bb385106704eb43e94ba50bc4e5c7f6cc`; the approved Slice 2 spec and plan at `sha256-bytes-v1:1a439feade28e344dd2555afff539c5993b7ffdcb9f7c4898b558697c0237d8d` and `sha256-bytes-v1:9b9bad24cd43ee58f6013f79b53311ceea949dc3785b4bff66a09944a80f037c`; direct owners `docs/architecture/work-loop-knowledge-handoff.md`, `docs/architecture/work-loop-acceptance-evidence.md`, `docs/architecture/work-loop-review-disposition.md`, `docs/architecture/work-loop-execution-supervisor.md`, and `docs/architecture/work-loop-authority-migration.md`; analogous knowledge lifecycle code in `packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py` and `knowledge_store.py`; construction paths in `packs/core/tests/skills/project-knowledge/`. Slice 1's contract, service, architecture, and release outputs exist, but its final post-gates hardening and review are still in flight; Slice 2 is approved but not yet implemented.

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

Add the feed and projector over committed Slice 1 semantic evidence and current Slice 2 review facts, including review-failure receipts only while predecessor currentness and supersession keep them live, then make project-knowledge the sole owner of collection and committed-store validation. Author the Slice 3 schemas only under `contracts/delivery/`; Core runtime code validates the same behavior without loading or copying them. Exclude reviewed-envelope, initial-plan-review, plan, task-projection, and mutation-classification inputs from projection. Wire optional post-commit notification and remove reusable capture gates only after pull-scan, replay, quarantine, unavailable-tooling, self-containment, and retained-work-item parity pass against the predecessor contracts.

## Constraints

- The former Ready transition `4e5f61703514f6f05b0a1876243a63c13cc2926a` and architecture revision `61624180b808f9adca70eab2ed2305adee645ce9` are historical only. The current Ready brief and reviewed architecture revisions are pinned above, and the first-three slice cut is confirmed.
- The Slice 1 revisions pinned in `Repository anchors` own the accepted authority and implemented canonical contract, callable-service, architecture, and release outputs. Its self-contained `work-loop` services exist, while final post-gates hardening and review remain in flight; Slice 3 execution waits for that closeout to freeze the predecessor surface.
- `structured-review-boundary` is approved. Its accepted contract requires atomic creation and supersession of `review-failure` receipts, predecessor-owned report and assessment currentness, and a self-contained Core runtime; Slice 3 consumes those decisions without reconstructing them.
- Slice 1 owns acceptance authority, reviewed-envelope projection, initial terminal-intent review, and side-effect-free mutation classification. Slice 4 alone owns mutable task reprojection, cancellation, dispatch, and removal of the legacy plan lock.
- No task starts until Slice 1 closeout freezes its implemented contract and service surface and Slice 2 implementation supplies conforming review contracts, currentness readers, and the review-failure receipt lifecycle required by T1. Both predecessor revisions are cited here without restating their owned contracts.
- The current engine remains authoritative; this slice neither starts Slice 4 nor moves procedure, result, acceptance, or review authority.
- The legacy whole-plan lock remains authoritative during Slice 3. `initial-plan-review.v1` supplies terminal intent but cannot authorize a task change or remove that lock before Slice 4.
- Delivery may read only predecessor-defined durable evidence and review facts. Arbitrary session prose, transient attempts, journals, and uncommitted worktree content are not projection inputs.
- `reviewed-execution-envelope.v1`, `initial-plan-review.v1`, plans, task projections, and mutation-classification results are excluded from the knowledge projection policy even when they are durable or reproducible.
- Repository guidance and the accepted predecessor namespace decide final contract paths. Approved Slice 1 fixes the canonical `contracts/delivery/` family, and approved Slice 2 fixes the review-record families and ownership that T1 must resolve against their implemented files.
- `contracts/delivery/` is the only delivery-schema source. Core feed, projection, collection, and read-validation runtime modules remain self-contained standard-library scripts, import only sibling modules in their own skill, and neither copy nor load delivery schemas at runtime.
- Slice 1 has reconciled its owned architecture pages with the implemented script seam and no-copy rule. The still-Draft review-disposition and execution-supervisor pages retain later-slice examples; Slice 2 owns their review-boundary correction, while Slice 3 updates only its knowledge-handoff and baseline knowledge-capture outputs and stops if the final predecessor owners conflict when T1 begins.
- Pi is an optional external Slice 6 compatibility target. Slice 3 imports, bundles, installs, and selects no Pi component, and its behavior and verification have no Pi gate.
- Pre-review disconfirming probe: `rg -n -i "knowledge.{0,24}(queue|cursor|retry|acknowledg|skip|admission|retention|revocation)|capture.{0,16}gate" packs/core/.apm/skills/work-loop packs/core/.apm/skills/close-work` found a current work-loop capture gate and no delivery-owned knowledge lifecycle store; T3 therefore removes the gate only after pull parity instead of planning a store migration.
- The spec and plan are repository-durable at the locators above. Implementers, independent reviewers, CI, and close-work are required readers; accepted contracts, current architecture, maintainer guidance, tests, and release history become the stable post-closeout evidence owners; the spec directory freezes after shipment.

## Construction tests

**Integration tests:** A shared conformance matrix feeds durable evidence and review fixtures through notification-delivered, notification-dropped, repeated-scan, cache-deleted, incomplete-transaction, report-replacement, assessment-replacement, receipt-superseded, source-revoked, source-deleted, valid-committed-record, invalid-merged-record, unavailable-tooling, package-unavailable, runtime-schema-read, and explicit-work-item paths. It compares observation identity and bytes, knowledge-visible candidates, admission and retention decisions, quarantine output, delivery decisions, runtime reads, and delivery-owned durable state against AC-0001 through AC-0011.

**Manual verification:** none — all accepted behavior has deterministic contract, state, or decision oracles.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility / accepted contract namespace | T1, T2, T4 | Schema, no-copy, and feed parity from T1; committed-record quarantine and producer/consumer validation from T2; compatibility and traceability closure from T4 | Canonical schemas, registry entries, committed-read validation, and runtime behavior agree at release without schema copies or runtime schema reads. |
| Current architecture / architecture sources named by the spec, including baseline `docs/architecture/knowledge-capture.md` | T1-T4 | Architecture review tied to the conformance matrix; T4 updates and verifies the baseline knowledge-capture page, including committed-store read validation and quarantine | Living architecture names final ownership, boundaries, navigation, committed-store read validation and quarantine, and the retained explicit `work-item` seam. |
| Maintainer procedure / knowledge and closeout guidance | T2-T4 | Documented commands pass on pull, quarantine, disabled-provider, and work-item fixtures | Maintainer guidance invokes supported commands without relying on this plan. |
| Release history / Core pack and changelog surfaces | T4 | Build, version-parity, clean-environment, targeted-suite, and changelog checks | Released Core projections and changelog describe the shipped boundary without a repository-package runtime dependency. |

## Design (LLD)

### Design decisions

The durable source fact is the replay source; the projector returns one deterministic observation or no observation and writes nothing. Notification is a best-effort hint after fact commit, while the project-knowledge pull collector owns every operation that requires lifecycle state. Traces to AC-0002 through AC-0004 and AC-0007 through AC-0008. Owned by: T1-T3.

### Interfaces & contracts

The accepted Slice 1 bundle owns acceptance authority, shared delivery-fact identities, semantic transactions, reviewed-envelope derivation, initial terminal-intent review, mutation classification, content safety, capability, audit, compatibility, and the canonical schema namespace. Its envelope, initial review, and mutation decision constrain delivery authority and procedure but are not projection inputs. Approved Slice 2 owns review-fact identity, lineage, currentness, acknowledgement, and the review bridge that atomically creates or supersedes `review-failure` receipts; Slice 3 consumes those receipts as Slice 1 evidence only while Slice 2 keeps their source report and assessment current. Slice 3 authors the feed and observation schemas in the canonical namespace without copying predecessor fields or loading schemas at runtime. The feed presents a stable, complete snapshot with stateless continuation, and the existing knowledge capture contract remains the owner of explicit `work-item` requests. Concrete Slice 2 imports and backward pointers are a T1 conformance result after its implementation; the kill condition is any need to redefine a predecessor-owned fact rather than cite it. Traces to AC-0001, AC-0002, AC-0005, AC-0006, AC-0010, and AC-0011. Owned by: T1-T3.

### Failure, edge cases & resilience

Snapshot drift, unsafe or unknown records, and unavailable providers refuse or quarantine without partial delivery state. Dropped notifications recover through pull scanning; repeated scans rely on deterministic identity and knowledge-owned deduplication; committed-store quarantine is disposable and never grants authority. Traces to AC-0001 and AC-0003 through AC-0007. Owned by: T1-T4.

### Dependencies & integration

Slice 1 supplies acceptance authority plus the accepted delivery-fact, semantic-transaction, reviewed-envelope, initial-review, mutation-classification, content-safety, capability, audit, and compatibility contracts through self-contained `work-loop` scripts. Slice 2 supplies the accepted current report, assessment, disposition, lineage, acknowledgement, and review-failure receipt lifecycle. Slice 4, not this slice or Slice 1, owns mutable task reprojection and plan-lock removal. Project-knowledge remains the existing capture, storage, enquiry, distillation, and lifecycle owner; work-loop and close-work retain only explicit bounded `work-item` capture. No Slice 3 runtime imports `agentbundle`, another repository package, or a contract schema. Traces to AC-0001 through AC-0011. Owned by: T1-T4.

## Tasks

### T1: The delivery feed and pure projector satisfy replay and snapshot conformance

**Depends on:** none

**Touches:** `contracts/delivery/delivery-fact-feed.v1.schema.json`, `contracts/delivery/knowledge-observation.v1.schema.json`, contract indexes, and self-contained feed/projector modules under `packs/core/.apm/skills/work-loop/scripts/`

**Verification mode:** TDD through contract and integration tests

**Tests:**
- A contract suite drives the accepted evidence and review fact readers through complete, paged, changed-snapshot, incomplete-transaction, report-replacement, assessment-replacement, receipt-supersession, unknown-version, ineligible-source, content-refusal, and delivery-control-record cases, comparing the feed result with AC-0001, AC-0002, and AC-0010; the negative corpus includes reviewed-envelope and initial-plan-review records plus plan, task-projection, mutation-classification, and superseded `review-failure` receipt inputs.
- A table-driven projector suite replays accepted source fixtures and compares canonical observation identity and bytes across fresh instances, policy changes, supersession, and refusal against AC-0002 and AC-0004.
- Schema, no-copy, and backward-pointer checks validate the canonical files, reject any delivery-schema copy outside `contracts/delivery/`, and compare the registry with this spec's final `Contract:` header.

**PLAN TDD disposition:** `no stub (implementation-discovered)`. **Discovery predicate:** Slice 2 has implemented its approved review contracts, currentness readers, and atomic `review-failure` receipt lifecycle, so T1 can resolve their concrete callable and fixture seams beside Slice 1's implemented services. **Constraint:** the first test may consume but cannot alter, copy, or replace either predecessor contract, and it cannot make Core load a schema at runtime. **Required outcome:** a contract-surface test fails on an incomplete semantic transaction or a superseded review-failure receipt before the feed/projector implementation makes both inputs ineligible. **Verification mode:** TDD through contract and integration tests. **Proof obligation:** this spec's `notes/verification-ledger.md` records the resolved predecessor seams and the first behavioral red result mapped to AC-0001, AC-0002, and AC-0010 before implementation turns it green.

**Grounding:** Use the implemented Slice 1 contract bundle and self-contained `work-loop` script seam, then resolve final imports against the implemented form of Slice 2's accepted review surface. Stop if Slice 1 closeout changes a required callable port, Slice 2 has not implemented its accepted currentness and receipt lifecycle, the accepted Slice 1 classifier writes task, cancellation, or dispatch state, or either predecessor lacks the stable fact identity, safe and authorized read boundary, content-policy and audit binding, compatibility rule, current-and-acknowledged review-fact decision, or receipt-supersession signal required by AC-0001, AC-0002, or AC-0010; amend the owning predecessor instead of inventing a Slice 3 substitute.

**Done when:** the task's contract, replay, refusal, and parity tests pass and its interface-compatible durable-output evidence exists.

### T2: Project-knowledge owns pull collection and committed-store quarantine

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py`, `packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py`, their generated skill projections, and `packs/core/tests/skills/project-knowledge/`

**Verification mode:** TDD through integration tests

**Tests:**
- Collector fixtures drop notifications, restart, rescan overlapping windows, and replay replaced reports, replaced assessments, superseded receipts, revoked facts, and deleted facts, comparing the current knowledge-visible set, per-source admission or retention decisions, duplicate usability, and delivery-owned state with AC-0003, AC-0004, and AC-0010.
- A positive committed-read fixture passes a current valid `knowledge-captured-observation.v2` record through enquiry and distillation and compares its usable result and empty quarantine view with AC-0009.
- Merge-bypass fixtures introduce malformed, unsafe, unknown-version, and policy-invalid committed records, then exercise enquiry and distillation and compare exclusion, bounded knowledge-owned quarantine reasons, and byte-identical committed source files with AC-0005.
- A delete-and-rebuild fixture removes collector and quarantine projections, reruns the scan, and compares the resulting knowledge-visible candidates and exclusions.

**PLAN TDD disposition:** `no stub (implementation-discovered)`. **Discovery predicate:** T1 has fixed the observation contract and callable feed while implementation inspection has selected the existing project-knowledge collection and committed-read validation seams to extend. **Constraint:** the first test must use the existing knowledge store and may not introduce delivery-owned lifecycle state or mutate an invalid committed record. **Required outcome:** an integration test fails because a dropped-notification rescan does not yet converge or because an invalid Git-introduced record remains usable, then passes through knowledge-owned collection or quarantine behavior. **Verification mode:** TDD through integration tests. **Proof obligation:** this spec's `notes/verification-ledger.md` records the chosen collector and committed-read seams plus the first behavioral red result mapped to AC-0003 or AC-0005 before implementation turns it green.

**Grounding:** Extend the existing project-knowledge validation, committed-read, capture, enquiry, and distillation seams rather than adding a second store. Stop if safe quarantine requires delivery to retain collector state or if the current committed-store format cannot distinguish invalid data without mutating its source.

**Done when:** the task's pull, replay, quarantine, and rebuild tests pass and the maintainer procedure records their supported commands.

### T3: Delivery notification is optional and explicit work-item capture remains bounded

**Depends on:** T1, T2

**Touches:** the accepted delivery post-commit port; `packs/core/.apm/skills/work-loop/`, its generated skill projections, and the established close-work/project-knowledge work-item path

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
- The shared conformance matrix defined in `## Construction tests` runs AC-0001 through AC-0011; this task adds no second case inventory.
- Core pack build/parity checks compare canonical contracts, generated skill projections, and runtime behavior; clean-environment and filesystem-spy fixtures prove AC-0011 without bundling schemas.
- Documentation and status checks verify the final architecture, including the baseline knowledge-capture page's projection, independent lifecycle, committed-store read validation and quarantine, and retained `work-item` account, plus maintainer commands, release versions, changelog, contract traceability, and spec/plan lifecycle state.

**Grounding:** Use the repository's existing targeted Core pack, build-self, bootstrap, contract, and spec-status gates after the accepted T1-T3 paths are known. Stop if any output requires a runtime repository package, schema copy or runtime schema load, starting Slice 4, or changing predecessor authority.

**Done when:** the cross-boundary matrix and repository gates pass, `docs/architecture/knowledge-capture.md` reflects the shipped projection, committed-store read-validation and quarantine boundary, and retained explicit `work-item` seam, and every Durable-output map row has closeout evidence.

## Rollout

- **Delivery:** Land behind the current engine and legacy plan-lock compatibility boundary. Keep existing reusable capture behavior available for parity observation until pull rescan, quarantine, and disabled-provider fixtures pass; then remove only reusable capture gates. Rollback disables projection and restores the prior gates without migrating delivery-owned state. Task reprojection and plan-lock removal remain deferred to Slice 4.
- **Infrastructure:** none — local canonical contracts, self-contained Core pack code, and existing Git-backed knowledge storage only.
- **External-system integration:** none; an installed listener is optional and cannot become a deployment prerequisite.
- **Deployment sequencing:** Slice 1 closeout, Slice 2 implementation and its accepted readers and contracts, then T1 feed/projector, T2 pull/quarantine, T3 notification and gate removal, then T4 durable outputs and release closure.

## Risks

- Slice 2's accepted review-fact and receipt semantics are not implemented yet, so exact file and callable locations may differ from the plan's working decomposition. T1 waits for conforming Slice 2 outputs and stops for a predecessor amendment if implementation cannot preserve the accepted identity, currentness, supersession, or runtime boundary.
- A partial or unacknowledged review compatibility write could leak a result that Slice 2 does not consider current. T1 admits review facts only through Slice 2's accepted currentness, lineage, and acknowledgement decision.
- A replaced report or assessment could leave an obsolete review-failure candidate usable. T1 exposes only complete Slice 1 transactions and their supersessions; T2 reconciles the resulting source status without reconstructing Slice 2 currentness.
- A projection that carries too much source content may leak protected data or instructions. The accepted content-policy boundary and refusal corpus run before observation emission and again before committed knowledge use.
- Pull rescan may miss deletions or supersessions. Complete snapshot and successor fixtures require knowledge-owned reconciliation without a delivery skip store.
- Removing reusable capture gates may accidentally remove close-time work-item capture. T3 keeps positive and negative work-item fixtures independent from observation projection.
- Quarantine may become a second authoritative store. Its view is disposable, rebuildable, knowledge-owned, and excluded from delivery readiness.
- A copied or runtime-loaded schema could couple Core execution to build tooling or a repository checkout. T1 and T4 require one canonical schema set, a no-copy scan, clean-environment execution, and zero runtime reads under `contracts/delivery/`.

## Changelog

<!-- Approval entries only:
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->
