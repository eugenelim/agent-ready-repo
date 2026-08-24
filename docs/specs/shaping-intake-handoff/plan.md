# Plan: Shaping-to-intake handoff

- **Spec:** [spec.md](spec.md)
- **Status:** Done
- **Repository anchors:** ARCHITECTURE.md and docs/architecture/work-intake-and-artifact-routing.md own the intake boundary; contracts/jsonschema/normalized-intake.schema.json and contracts/jsonschema/semantic-surface-resolution.schema.json own the published contracts; contracts/pack.schema.json owns optional cross-pack `[[pack.integrations]]` records; packs/core/.apm/skills/work-intake/scripts/intake_router.py and surface_resolver.py are the analogous pure routing and resolution implementations; packs/core/tests/skills/work-intake/test_work_intake.py and test_surface_resolver.py are their construction paths; packs/product-engineering/.apm/skills/discovery-loop/SKILL.md, decompose-intent/SKILL.md, and packs/product-engineering/DESIGN.md are the current upstream handoff surfaces. Named deviation: those product-engineering sources disagree between direct spec, per-feature brief, and app-scale brief handoffs. Wave 2 reconciles that seam by semantic role—one independently shippable feature is a delivery contract and a multi-spec or cross-repository outcome is a delivery brief—while keeping current local artifact defaults and lifecycle behavior.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change while Drafting. After approval, Phase 1 treats substantive
> plan changes as a re-plan requiring a new review and approval.

## Approach

Land Wave 2 in four dependency-ordered tasks. First extend normalized-intake.v1 with one optional closed handoff object and deterministic valid/invalid fixtures, retaining every existing fixture result. Next add a pure handoff-admission seam beside the existing intake router: core derives brief versus contract from validated content, consumes a caller-supplied Wave 1 resolver result, and produces either an existing processor route, standalone-core fallback, or a stable zero-effect stop. Then ship the product-engineering producer and core consumer skills with their optional pack integration, evals, boundary metadata, adopter guidance, release metadata, and synchronized projections so the slice is independently usable with both packs or core alone. Finally add the cross-pack completion matrix and reconcile current-state contributor documentation. No task changes lifecycle state, makes an external locator executable, or adds a transport.

The riskiest part is preserving the instruction/data and authority boundaries while accepting richer upstream content: an upstream producer may propose content, a source locator, and evidence, but it cannot self-assert a route, a resolved convention, repository confinement, or write/delete authority. Core recomputes the content classification and Wave 1 resolution from trusted invocation plus bounded candidate records.

## Constraints

- RFC-0096 section 3 fixes the optional shaping-to-core data handoff; section 4 fixes surface resolution and authority reporting; section 9 fixes Wave 2 scope and evidence.
- RFC-0083, ADR-0077, and ADR-0078 keep classification in core, preserve the two origin-authority modes, require artifact-backed durable execution, and prohibit source labels or optional packs from redefining identity or lifecycle.
- RFC-0093 and RFC-0094 preserve intent-scoped completion and current direct-light behavior.
- semantic-surface-resolution.v1 and workspace-entry.v1 are shipped Wave 1 contracts. This plan consumes them without changing their vocabulary, result shape, precedence, or locator-only dispatch behavior.
- Python 3.11+ stdlib remains the portable runtime. JSON Schema validation remains a development/adapter boundary and adds no core runtime dependency.
- Existing docs/product and docs/specs defaults remain compatible. Upstream adopter-owned repository paths and external locators remain source destinations and are never relocated.
- Source, write, and deletion authority remain independent. Source-origin mode is not expanded beyond repo-origin and tracker-origin.
- Pack content changes update each affected pack and plugin version once, update each affected eval harness, and regenerate projections only from source.
- Git metadata stays read-only. The base-freshness check remains skipped for this run because it may fetch or update refs.

## Construction tests

**Integration tests:**

- A committed RFC-0096 Wave 2 matrix runs the core router and real Wave 1 resolver together for every case enumerated by AC13; the spec is the single canonical case roster.
- The matrix runs twice from clean fixture roots and compares canonical JSON bytes, routes, stable next actions, and before/after filesystem fingerprints.
- A pack-roster test builds the core-only surface and the core-plus-product-engineering surface, proving product-engineering adds the optional producer but core routing, activation, templates, and existing eval results remain unchanged without it.
- Contract traceability tests validate the normalized-intake schema backlink to this spec while preserving the existing defining spec.
- Source/self-host parity and catalogue verification prove .apm sources, adapters, plugin metadata, and projected installed skills agree.

**Manual verification:**

- Invoke the installed core work-intake surface with a standalone bounded request and record the current direct-core route.
- Invoke it with a resolved repository handoff and record reuse through new-spec or receive-brief with source provenance.
- Invoke it with already-acquired external content and record the external locator, pinned revision, unknown capability facts where unsupported, and zero network/filesystem probing of that locator.
- Invoke product-engineering's confirmed handoff path with core available and unavailable, recording successful delegation in the first case and a portable bounded handoff result in the second.

## Design (LLD)

### Design decisions

- Add one optional handoff object to normalized-intake.v1 rather than create shaping-handoff.v1. This keeps one source boundary, one validator, and legacy envelopes unchanged. Traces to: AC1-AC2, AC8-AC9 · contracts/jsonschema/normalized-intake.schema.json.
- Treat producer content as a proposal. Core validates and derives semantic role; producer pack name, artifact type, filename, and prose have no routing authority. Traces to: AC4, AC7, AC11.
- Reconcile the three mapped product-engineering handoff surfaces to one role rule: one independently shippable feature is a delivery contract; a multi-spec or cross-repository outcome is a delivery brief. Traces to: AC3, AC5, AC9.
- Keep Wave 1 resolution caller-driven. Core supplies at most 32 closed candidates with at most four evidence records each and passes them to resolve_surface; the handoff does not redefine or self-certify a resolution result. Traces to: AC3-AC6, AC10-AC11.
- Reuse existing processors and artifact transactions. A handoff selects neither a new lifecycle membership nor a new artifact kind; it only supplies bounded content to the current brief/spec route after admission. Traces to: AC5-AC8, AC12.
- Preserve external ownership by reference. External content must already be acquired and normalized through a trusted adapter/current invocation; core does not fetch it and local execution uses the repository's existing artifact-backed route with source authority pinned. Traces to: AC6, AC10-AC12.

### Interfaces & contracts

normalized-intake.v1 gains an optional handoff object with additionalProperties false. Its required members are present even when their arrays are empty, so absence of the object means standalone core and presence means the producer intentionally offered a handoff:

- boundaries: bounded strings;
- non_goals: bounded strings;
- dependencies: closed records carrying relationship (blocks or informs), locator kind (repository-path or external), safe locator, optional semantic role, and optional pinned revision;
- design_context: bounded strings;
- delivery_questions: bounded strings.

Outcome, constraints, assumptions, evidence, behaviors, named gaps, source locator/revision, optional tracker profile, and proposed origin authority stay in their current fields. Source text cannot add a processor, destination, confirmation, command, tool, credential, raw payload, or authority field.

The pure core handoff seam receives only validated/derived signals plus the Wave 1 SurfaceResolution object produced in the current trusted run. Its closed result records disposition, semantic role, processor or standalone fallback, authority mode, and stable next action. It does not carry raw content or exception text. The dispositions are:

- standalone: no handoff; continue current core classification unchanged;
- reuse: resolved delivery-brief to receive-brief or resolved delivery-contract to new-spec;
- clarification-required: content cannot distinguish a coherent route or the resolver requires confirmation/destination selection;
- refused: malformed/inconsistent provenance, unsafe locator/confinement, mandatory-policy conflict, unacquired external content, or another terminal Wave 1 refusal.

The handoff result preserves the Wave 1 result separately for rendering; it never flattens or recomputes provenance, capabilities, confirmations, revision/fingerprint, or authority facts. Traces to: AC1-AC11 · contracts/jsonschema/normalized-intake.schema.json and contracts/jsonschema/semantic-surface-resolution.schema.json.

### Failure, edge cases & resilience

- Unknown fields, oversize arrays/strings, unsafe locators, source/resolution mismatch, missing required handoff members, and invalid dependency records fail schema/admission before effects.
- An upstream repository path is read only through `agentbundle.catalogue_tooling.file_safety.read_confined_regular_file` when importable or a parity implementation in the standalone skill path. Confinement is rechecked at open time; symlinks, reparse points or junctions, multiply linked files, non-regular files, dot segments, absolute paths, drive paths, backslashes, resolution/open races, byte-limit overflow, and containment uncertainty refuse.
- An external locator stays opaque. If bounded content was not already acquired, core asks for a compatible adapter or supplied content and performs no fetch.
- confirmation-required, destination-required, and refused Wave 1 results remain terminal for the attempt and carry their existing bounded next action.
- A missing product-engineering pack or missing optional configuration is normal, not an error; core follows the standalone/default path.
- A producer dispatch failure occurs only after durable materialization/registration under the existing transaction contract and returns dispatch_failed without rolling back a valid canonical artifact.
- No retry loop, fallback network path, inferred convention, or second resolver is introduced. Traces to: AC4, AC6-AC8, AC11-AC13.

### Dependencies & integration

- Core work-intake owns validation, classification, resolver invocation, artifact transaction, and processor dispatch.
- product-engineering owns only producing the optional bounded handoff at its existing confirmed delivery gate. It imports no core Python and declares no mandatory pack dependency.
- new-spec, author-brief, and receive-brief consume bounded fields and safe source provenance through their existing workflows. Optional metadata may be added, but the template's current required fields and default paths stay valid.
- Tracker adapters remain the acquisition boundary for tracker content. This plan adds no tracker transport, network helper, or refresh behavior.
- work-loop and workspace-status continue consuming ordinary local approved spec/plan artifacts. External handoffs do not make locator-only entries executable.
- Configuration adapters remain optional candidate producers for the Wave 1 resolver and gain no authority by being configured. Traces to: AC3-AC12.

## Tasks

### T1: normalized-intake accepts a bounded optional handoff without changing legacy fixture outcomes

**Depends on:** none

**Touches:** contracts/jsonschema/normalized-intake.schema.json, packs/core/tests/pack/fixtures/work-intake-contracts/normalized-intake/**, tests/roster/test_normalized_intake_contract.py, tests/roster/test_work_intake_contracts.py

**Verification mode:** TDD — the additive closed-schema invariant and rejection matrix are compressible contract behavior.

**Tests:**

- stub: true
- Existing valid, invalid, and strict-JSON fixture parameterizations retain the same results; x-spec contains the original defining spec plus this modifying spec (AC1, AC8).
- Valid repository-brief, repository-contract, and acquired-external handoff fixtures accept complete bounded fields; empty optional-content arrays remain valid (AC1-AC3, AC5-AC6).
- Unknown handoff fields, unknown dependency fields/enums, missing required members, unsafe repository/external locators, absent required external revision, oversize values, prompt/raw-payload/credential fields, and non-finite JSON reject (AC2, AC4, AC6, AC11).
- stub: materialized, collected, and red — `tests/roster/test_normalized_intake_contract.py::test_normalized_intake_accepts_bounded_optional_handoff` compiles against the existing contract test module and fails because normalized-intake.v1 does not yet admit `handoff`.

**Approach:**

- Add reusable bounded text and handoff-dependency definitions inside normalized-intake.schema.json and add the optional top-level handoff property.
- Keep the contract version and all existing required properties unchanged.
- Preserve the reviewed modifying x-spec backlink and its exact-list contract assertion.
- Add the minimum valid/invalid fixtures needed to falsify optionality, closure, bounds, locator safety, and strict JSON.

**Done when:** the targeted contract suites are red before the schema change, green after it, and the pre-Wave-2 fixture roster and result counts are unchanged.

### T2: core handoff admission routes resolved delivery content and refuses unsafe or ambiguous reuse

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-intake/scripts/intake_router.py, packs/core/.apm/skills/work-intake/scripts/intake_guard.py, packs/core/tests/skills/work-intake/test_shaping_handoff.py, packs/core/tests/skills/work-intake/test_work_intake.py, packs/core/tests/skills/work-intake/test_surface_resolver.py

**Verification mode:** TDD — admission and routing are a pure finite decision table, with real filesystem fixtures for the confinement edge.

**Tests:**

- stub: true
- No handoff returns standalone and the existing route_intake matrix remains byte-for-byte equivalent (AC7-AC8).
- Resolved repository delivery-contract routes to new-spec; resolved repository delivery-brief routes to receive-brief; result retains authority mode and stable next action (AC3-AC5).
- Already-acquired external content routes without Path, filesystem, network, DNS, tracker, shell, or credential access and retains the external Wave 1 report (AC6, AC10).
- Content ambiguity, named gaps, source/resolution mismatch, missing external acquisition, confirmation-required, destination-required, mandatory-policy conflict, unsafe path, symlink escape/loop, and forged/invalid resolver objects return stable zero-effect stops (AC4, AC7, AC11).
- Source/write/deletion authority fixtures remain independent and prompt-like content never alters the decision (AC7, AC10).
- Repository read fixtures cover symlink/reparse/junction, hard-link, device/FIFO, oversize input, resolve/open swap, post-open identity mismatch, and stable redacted refusal through the blessed helper or explicit parity path (AC11-AC11a).
- stub: materialized, collected, and red — `packs/core/tests/skills/work-intake/test_shaping_handoff.py::test_resolved_contract_handoff_routes_to_existing_new_spec_processor` builds a real Wave 1 resolution and fails because `HandoffSignals` and `route_handoff` do not yet exist; `test_forged_resolver_object_is_refused_without_effects` pins the negative type/authority boundary.

**Approach:**

- Add closed HandoffSignals and HandoffRoute dataclasses to the existing intake_router module rather than add a second router.
- Keep route_intake untouched for non-handoff calls; route_handoff returns standalone before consulting a resolver when the optional object is absent.
- Accept only a current-run validated Wave 1 resolution object plus trusted derived booleans; never parse instructions, candidate prose, or a producer-asserted route inside the pure seam.
- Reuse intake_guard redaction/source mapping, Wave 1 safe rendering, and the blessed confined regular-file helper. A standalone fallback must be contract-parity-tested rather than a parallel shallow path check.
- Add a dedicated construction suite that calls the real resolver for integration cases and spies on prohibited external operations.

**Done when:** the new admission table is green, every existing route_intake and resolver test remains green, and every refusal proves zero materialization/registration/dispatch callbacks.

### T3: product-engineering produces and core consumes the optional handoff while standalone core stays unchanged

**Depends on:** T2

**Touches:** packs/product-engineering/.apm/skills/discovery-loop/SKILL.md, packs/product-engineering/.apm/skills/decompose-intent/SKILL.md, packs/product-engineering/.apm/skills/**/evals/**, packs/product-engineering/{README.md,JOURNEY.md,DESIGN.md}, packs/core/.apm/skills/work-intake/SKILL.md, packs/core/.apm/skills/work-intake/evals/**, packs/core/.apm/skills/new-spec/SKILL.md, packs/core/.apm/skills/author-brief/SKILL.md, packs/core/.apm/skills/receive-brief/SKILL.md, packs/core/.apm/skills/{new-spec,author-brief,receive-brief}/evals/**, packs/core/{README.md,JOURNEY.md}, guides/core/how-to/start-or-remember-work.md, guides/core/how-to/intake-an-external-brief.md, guides/core/reference/work-intake-routing-and-lifecycle.md, guides/product-engineering/explanation/the-discovery-loop.md, guides/product-engineering/tutorials/walk-a-discovery-end-to-end.md, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, packs/product-engineering/pack.toml, packs/product-engineering/.claude-plugin/plugin.json, docs/product/changelog.md, generated self-host projections

**Verification mode:** goal-based plus adopter-visible eval invocation — the skill contract and optional integration are prompt/pack surfaces whose behavior is proven through deterministic evaluation rather than mock-shape unit assertions.

**Tests:**

- no stub (goal-based/manual QA).
- Core work-intake evals cover repository brief/contract, acquired external content, ambiguity/refusal, optional configuration, and no-handoff standalone routes (AC3-AC8, AC10-AC13).
- Product-engineering evals prove its existing confirmed handoff gate emits only the closed bounded fields, treats content as data, and submits the optional object only when the current invocation exposes a Wave-2-compatible core capability; core absence, unknown capability, and a pre-Wave-2 core fixture each receive the portable rendered handoff without the unsupported top-level object (AC2, AC7, AC9).
- new-spec, author-brief, and receive-brief evals prove bounded upstream fields and safe provenance are reused without skipping their existing assumptions, Ready, slice-confirmation, spec, or plan approval gates (AC5-AC10).
- Downstream processor evals give each processor an external locator plus prompt-like bounded content and prove it neither fetches, searches for, probes, nor reads the locator; no network, tracker, shell, credential, or locator-derived filesystem operation occurs (AC6-AC7, AC11).
- Prompt/template assertions prove no existing required header, section, default path, trigger phrase, or direct-core response changes (AC1, AC8, AC12).
- Product-engineering's `[[pack.integrations]]` record uses `kind = "handoff"`, names the core work-intake consumer and discovery/decomposition providers, and carries an explicit standalone fallback without declaring a dependency (AC8-AC9).
- Every changed skill declares its actual `metadata.boundaries`; producer and consumer skills that ingest handoff content include `filesystem_read_untrusted`, and catalogue/self-host assertions prove the declarations survive every projection (AC10, AC14).
- Pack README/JOURNEY and adopter guides ship in this capability slice and explain repository/external reuse, ambiguity/refusal, and standalone fallback (AC5-AC14).

**Approach:**

- Reconcile product-engineering's discovery-loop, decompose-intent, and DESIGN prose to the role rule in AC9; normalize the bounded handoff and delegate through work-intake only when the current invocation advertises Wave-2 handoff compatibility, otherwise render the portable handoff while preserving the existing human gate and shaping completion.
- Teach work-intake to detect the validated optional object, classify the semantic content, acquire at most bounded candidates from trusted invocation/repository evidence, call the Wave 1 resolver, then call route_handoff before ordinary durable routing.
- Carry safe upstream fields into existing processor conversations as attributed context. Do not pre-approve assumptions, a brief Ready gate, a spec, a plan, or source refresh.
- Use existing source-authority and workspace source fields for pinned tracker-origin provenance; repo-origin sources retain ref/revision without an authority fence.
- Add the existing `[[pack.integrations]]` `kind = "handoff"` declaration to product-engineering with `pack = "core"`, the exact producer/consumer skill IDs, the optional availability condition, purpose, and standalone fallback. This metadata records the seam and does not create a `[pack.dependencies]` edge.
- Add the actual boundary metadata to every changed skill, then ship its pack README/JOURNEY, adopter guides, release metadata, and regenerated self-host projections in the same task so the capability slice remains usable and gate-clean.
- Bump both affected pack/plugin patch versions exactly once after reading the then-current values.

**Done when:** deterministic evals pass with both packs and core alone, manual invocations record the three happy paths, removing product-engineering changes no core-only result, adopter guidance is present, and a second self-host generation has zero drift.

### T4: the cross-pack completion matrix and current-state documentation close Wave 2

**Depends on:** T3

**Touches:** tests/roster/test_shaping_intake_handoff_matrix.py, docs/architecture/work-intake-and-artifact-routing.md, docs/guides/reference/work-intake-maintenance.md

**Verification mode:** goal-based plus documentation build/link check — these are cross-pack integration and current-state documentation contracts.

**Tests:**

- no stub (goal-based/manual QA).
- The committed Wave 2 completion matrix runs twice with byte-identical results and enumerates every AC13 evidence class (AC13).
- Portable shipped pack prose contains no catalogue-internal RFC/ADR/AC citations, and the T3 adopter docs explain upstream repository work, acquired external work, ambiguity/refusal, and standalone core fallback (AC5-AC14).
- Catalogue lint/verify, contract traceability, pack evals, source/self-host drift, prompt/template compatibility, site build, emitted-link validation, and security scanner gates pass (AC1-AC14).
- Release metadata names only optional shaping handoff/content routing and explicitly excludes later lifecycle waves (AC12, AC14).

**Approach:**

- Add the deterministic AC13 matrix as the single cross-pack completion oracle rather than copying its case roster into another plan section.
- Update current architecture and the maintainer procedure to name the additive handoff fields and unchanged ownership edges.
- Run the complete contract, routing, projection, eval, security, quality, catalogue, self-host, and site documentation gates against the already released T3 slice.

**Done when:** all targeted and repository-wide gates pass, the generated projection has zero drift on a second run, and no diff implements or documents Wave 3 or lifecycle behavior.

## Rollout

- **Delivery:** additive, capability-negotiated pack release. Existing normalized-intake envelopes and direct-core prompts remain valid. Product-engineering sends the machine handoff object only to a Wave-2-compatible core work-intake; core absence, unknown capability, and older closed-schema core versions receive the portable rendered handoff instead, so no older validator is asked to ignore an unknown field.
- **Infrastructure:** none.
- **External-system integration:** none. Tracker and external-source adapters remain separate acquisition boundaries; no live external mutation or verification occurs.
- **Deployment sequencing:** T1 contract precedes T2 core consumer; T2 precedes the complete T3 producer/consumer release slice; T4 verifies that slice as one cross-pack outcome and updates contributor current state. Core and product-engineering versions publish together for the integrated capability, but neither declares the other mandatory.
- **Rollback:** revert the additive schema fields, router seam, skill prose/evals, docs, and version bumps as one ordinary change. No data migration, external write, lifecycle state, or locator-only dispatch change requires repair.

## Risks

- A producer could self-assert a delivery role or resolved destination. Mitigation: core derives content classification and invokes Wave 1 itself; producer labels remain data.
- Adding optional fields to a closed schema could accidentally invalidate old fixtures or require a new validator registry. Mitigation: no cross-schema reference is added to normalized-intake; exact legacy fixture results and contract version are pinned.
- External reuse could become an implicit fetch path. Mitigation: acquired-content is an explicit admission signal and external-operation spies assert zero calls.
- Rich handoff content could bypass new-spec assumptions or brief/spec approval gates. Mitigation: processors receive attributed context only and their existing gates remain acceptance criteria and eval assertions.
- A dependency record could be mistaken for satisfied workspace state. Mitigation: handoff dependencies are content until current core classification and existing workspace dependency validation admit them; no source record self-satisfies a dependency.
- Optional integration metadata could imply a required pack dependency. Mitigation: manifest and core-only build fixtures test absence explicitly.
- Concurrent pack version work could claim the next patch. Mitigation: read current versions immediately before the single bumps and preserve unrelated changes.

## Work-loop decision record

- **Files expected:** the normalized-intake schema/fixtures/tests; core intake router/guard/skills/evals; product-engineering producer skills/evals; affected pack/plugin versions; bounded adopter/current-architecture docs; generated self-host projections; this spec/plan and workspace registration.
- **Tests that demonstrate done:** contract valid/invalid matrices; pure handoff admission and real-resolver fixtures; core-only versus dual-pack deterministic eval corpus; prompt/template compatibility assertions; projection/catalogue/site/security/quality gates; three adopter-visible invocations.
- **Not changing:** semantic-surface-resolution.v1 or workspace-entry.v1 vocabulary; tracker acquisition/refresh; default artifact paths; workspace lifecycle meanings; work-loop transitions; locator-only dispatch; shaping retention; architecture/ADR routing; closeout/cooling/retirement/deletion/migration; Wave 3+.
- **Temptation: publish a separate shaping-handoff schema.** Declined because the confirmed contract decision is an additive optional normalized-intake field and a second source boundary would drift.
- **Temptation: import core from product-engineering or declare a required dependency.** Declined because standalone core and independently usable shaping are Wave 2 invariants.
- **Temptation: fetch external locators to make reuse convenient.** Declined because acquisition belongs to adapters and Wave 1 keeps external locators opaque/offline.
- **Temptation: make locator-only workspace entries executable.** Declined because Wave 2 materializes the repository's ordinary local execution artifact and RFC-0096 does not authorize changing dispatch semantics here.
- **Temptation: generalize routing to architecture, ADRs, or every semantic role.** Declined because that begins Wave 3.
- **Expected review shape:** DEEP but below 2,000 reviewable behavior/test lines. The four dependency-ordered tasks each leave the repository valid and independently reviewable; no WIDE transformation or reproducibility script is warranted.

## Resolve-vs-surface disposition

| Discovery | Intent fit | Decision | Disposition |
| --- | --- | --- | --- |
| normalized-intake lacks explicit boundaries, non-goals, dependencies, design context, and delivery questions. | Matches | Include | Add one optional closed handoff object in T1. |
| product-engineering sources disagree between direct spec, app-scale brief, and per-feature brief handoffs. | Matches | Include | Reconcile all three sources to the AC9 role rule in T3. |
| workspace-status and work-loop retain local artifact-backed dispatch. | Matches constraint | Preserve | External/upstream content feeds an ordinary local brief/spec; locator-only dispatch stays out of scope. |
| A Draft/Drafting spec is registered in `work.queue`. | Matches process | Preserve | Canonical reconciliation reports it `dispatchable: false` with `unapproved_spec`; registration is not authorization, so it remains queued and blocked until both human approvals complete. |
| The initial queue record hard-depended on a Wave 1 spec already shipped in the current base but retained in a stale queue membership under a completed initiative. | Matches current slice | Resolve | Remove the obsolete live `needs` edge from this new queue record; RFC-0096, the shipped Wave 1 contract, and the current base remain explicit governing prerequisites, while unrelated historical membership repair stays outside this spec. |
| Pre-Wave-2 normalized-intake.v1 is closed and rejects an unknown top-level handoff object. | Matches compatibility boundary | Resolve | Treat only an explicitly Wave-2-compatible current core invocation as machine-handoff capable; otherwise product-engineering emits the portable rendered handoff and the completion matrix proves the legacy pairing. |
| Downstream processors have network-capable workflows. | Matches security boundary | Include | AC6-AC7 and T3 prohibit dereferencing the external handoff locator and prove the prohibition with processor-level tool spies. |
| Realpath-only checks leave local reads exposed to file-type and open-time races. | Matches security boundary | Include | AC11a and T2 require the blessed confined regular-file helper or explicit contract parity. |
| Changed skills need machine-visible boundary metadata. | Matches security boundary | Include | AC14 and T3 require actual `metadata.boundaries` declarations and projection preservation checks. |
| Pack metadata already defines optional `kind = "handoff"` integrations. | Matches repository idiom | Include | T3 uses that existing declaration shape without adding a mandatory dependency. |
| Adopter guides were isolated in a terminal documentation task. | Matches phase-slice doctrine | Include | Move pack and adopter guidance, release metadata, and regenerated projections into T3 with the capability; T4 retains only integration evidence and current-state maintainer docs. |
| architecture/ADR destinations and lifecycle disposal are later RFC-0096 waves. | Does not match | Exclude | No implementation or durable follow-on is created by this spec. |
| External acquisition requires adapter-specific transport. | Does not match | Exclude | Require already-acquired normalized content; add no transport or fetch. |

No unresolved item requires human direction after the confirmed assumption and interface/shape checkpoint. Reopen this record if review finds that a proposed field changes authority, lifecycle, or later-wave scope.

## Changelog

- 2026-08-23: Initial Wave 2 plan from accepted RFC-0096, shipped Wave 1 contracts, confirmed integration shape, and confirmed additive normalized-intake interface.
- 2026-08-24: Pre-execution review added downstream no-fetch controls, confined regular-file reads, explicit handoff integration metadata, reconciled product-engineering role semantics, materialized red stubs, moved adopter guidance into the capability slice, and required capability-negotiated rendered fallback for pre-Wave-2 core.
