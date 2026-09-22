# Architecture Decision Records

| # | Title | Status | Date |
| --- | --- | --- | --- |
| 0001 | [Adopt AGENTS.md + spec/ADR/RFC governance](0001-adopt-agents-md-and-doc-hierarchy.md) | Accepted | 2026-05-03 |
| 0002 | [Install-scope is a per-pack default + allowance, not a per-item or adopter-only choice](0002-install-scope-per-pack-default-and-allowance.md) | Accepted | 2026-05-23 |
| 0003 | [Four-broker contract for credentialed skills; in-process shim + adapter-root subprocess as the two v1 transports](0003-credential-broker-contract.md) | Accepted | 2026-05-26 |
| 0004 | [Per-IDE direct writes are the repo-scope install default; dist-tree is opt-in](0004-repo-scope-per-adapter-projection.md) | Accepted | 2026-05-26 |
| 0005 | [Supervisor mode — topological-order default, gated parallel writes](0005-supervisor-topological-default-and-write-gate.md) | Accepted | 2026-05-29 |
| 0006 | [Doc drift — prevented by construction + judgment for adopters; mechanically gated only as catalogue governance](0006-doc-drift-construction-and-judgment.md) | Accepted | 2026-05-29 |
| 0007 | [Ship the doc-drift spec-metadata lint to adopters as a work-loop skill script](0007-ship-doc-drift-lint-as-work-loop-skill-script.md) | Accepted | 2026-05-29 |
| 0008 | [Contract authoring integrates via an agnostic, convention-first seam (not a core merge); contracts live in a repo-level tree](0008-contract-authoring-seam.md) | Accepted | 2026-05-31 |
| 0009 | [A product-brief layer sits between roadmap and spec; the low-level design lives in the plan with a derived (never baked) stack](0009-product-brief-layer-and-plan-owned-lld.md) | Accepted | 2026-06-01 |
| 0010 | [A normative `reference.md` is the repo's golden path — template-instantiated on demand, never a core seed, populated by repo context](0010-reference-architecture-foundation.md) | Accepted | 2026-06-01 |
| 0011 | [Greenfield inception is a new `init-project` flow that composes existing skills — a value gate over fed-in discovery, a recorded foundation, then a walking skeleton; not an autonomous generator](0011-greenfield-inception-front-door.md) | Accepted | 2026-06-01 |
| 0012 | [Split `kiro` into `kiro-ide` and `kiro-cli` with `kiro` as a deprecated alias, and activate `kiro-ide-hook` at contract v0.9](0012-kiro-adapter-split.md) | Accepted | 2026-06-01 |
| 0013 | [Copilot is a full-parity, user-scope-capable adapter](0013-copilot-full-parity-user-scope-adapter.md) | Accepted | 2026-06-04 |
| 0014 | [Rigor scales with risk — `work-loop` light/full modes](0014-rigor-scales-with-risk-work-loop-modes.md) | Accepted | 2026-06-05 |
| 0015 | [Cursor is a full-parity distribution adapter](0015-cursor-full-parity-distribution-adapter.md) | Accepted | 2026-06-11 |
| 0016 | [Gemini CLI is a full-parity distribution adapter](0016-gemini-cli-full-parity-adapter.md) | Accepted | 2026-06-11 |
| 0017 | [Adopt Bandit + pip-audit + Semgrep as the repo's SAST/SCA gate](0017-adopt-bandit-pip-audit-semgrep-sast-gate.md) | Accepted | 2026-06-12 |
| 0018 | [Shift security review left and deliver its depth via an orchestrator-loaded progressive-disclosure skill](0018-shift-security-review-left-progressive-disclosure.md) | Accepted | 2026-06-12 |
| 0019 | [Product shaping is a recursive level-tagged `intent` tree; a brief is a feature-intent projected onto one repo; contracts mature by stage](0019-product-intent-ontology-and-brief-projection.md) | Accepted | 2026-06-13 |
| 0020 | [Per-pack Diátaxis hierarchy for `guides/`](0020-per-pack-diataxis-hierarchy-for-guides.md) | Accepted | 2026-06-13 |
| 0021 | [`pack.toml` is the metadata source of truth, projected lossily per tool; pack identity is `@catalogue/pack`](0021-pack-manifest-source-of-truth-and-scoped-identity.md) | Accepted | 2026-06-13 |
| 0022 | [The business-unit cross-component layer — a value-stream meta-repo, per-component brief slicing with `parent-intent` provenance, and a referenced (never forked) shared contract](0022-value-stream-meta-repo-cross-component-layer.md) | Accepted | 2026-06-13 |
| 0023 | [The "three reviewers" ceiling scopes the core code-review lenses](0023-reviewer-ceiling-scopes-core-code-review-lenses.md) | Superseded by ADR-0042 | 2026-06-14 |
| 0024 | [`design-craft` serves designers as upstream design-intent authors, under strict framework-agnosticism](0024-design-craft-upstream-intent-and-agnosticism.md) | Accepted | 2026-06-14 |
| 0025 | [Pack profiles are single-scope, catalogue-owned CLI manifests — not meta-packs](0025-pack-profiles-single-scope-cli-manifest.md) | Accepted | 2026-06-14 |
| 0026 | [SSO-cookie consumer resolution lives in the `credbroker` library, platform-agnostic](0026-sso-consumer-resolution-in-credbroker.md) | Accepted | 2026-06-16 |
| 0027 | [ADR format is MADR-aligned but lean, not full MADR](0027-adr-format-is-madr-aligned-but-lean.md) | Accepted | 2026-06-21 |
| 0028 | [Pack-level activation evals adopt the agentskills.io trigger-eval convention; coverage in `pack.toml`; runner is catalogue-internal tooling](0028-pack-activation-evals.md) | Accepted | 2026-06-21 |
| 0029 | [Research pack structure — two orthogonal axes (depth × lifecycle), with a prompt-only project mode](0029-research-two-axes-depth-and-lifecycle.md) | Accepted | 2026-06-22 |
| 0030 | [Consolidated, namespaced pack-output layout contract (`agentbundle-layout.toml`)](0030-consolidated-pack-output-layout-contract.md) | Accepted | 2026-06-22 |
| 0031 | [Infra `work-loop` support is doctrine on existing reviewers — operational safety via `quality-engineer`, security via a mandatory `security-reviewer` + scanner pair — not a new reviewer or runtime](0031-infra-support-is-doctrine-on-existing-reviewers-not-a-new-reviewer-or-runtime.md) | Accepted | 2026-06-23 |
| 0032 | [The agentic well-architected overlay is a first-class workload-class lens applied at design *and* review — a routing axis plus progressive taxonomy on the existing `architect` skills, not a new primitive](0032-agentic-overlay-is-a-design-and-review-workload-class-lens.md) | Accepted | 2026-06-23 |
| 0033 | [The intent `Level` is reopened to an open recognized set (`product-vision › product-strategy › capability › feature`) and decoupled from `Scale` — a refinement of ADR-0019, prompt-only](0033-intent-level-open-recognized-set-decoupled-from-scale.md) | Accepted | 2026-06-23 |
| 0034 | [Grounding the infra inner loop in platform reality is toolchain-oracle doctrine + EXECUTE-loaded craft — one new `core` skill, not executable tooling, per-vendor data, or a new agent](0034-infra-grounding-toolchain-oracle-doctrine-not-tooling-vendor-data-or-agent.md) | Accepted | 2026-06-24 |
| 0035 | [Grounding the architect *design* phase in platform reality — the deferred serverless lens + a dual-consumed grounding discipline and sync-path viability check, prose-only on the existing routing axis (no new skill, reviewer, or tooling)](0035-architect-design-phase-grounded-in-platform-reality-dual-consumed-serverless-lens-and-contract-grounding.md) | Accepted | 2026-06-24 |
| 0036 | [The install-source default resolves through a trusted-by-construction precedence chain — editable detection as the downstream default, no repo-scoped source, no cwd fallback](0036-install-source-resolves-through-trusted-precedence-chain-no-repo-source-no-cwd.md) | Accepted | 2026-06-25 |
| 0037 | [Grounding context is adopter- and org-supplied and presence-checked — the EXECUTE contract-grounding gate generalizes from infra to framework/library through one detect-and-recommend tier, extending (not breaking) ADR-0034's no-bundled-KB rule](0037-grounding-is-adopter-and-org-supplied-and-presence-checked-one-gate-from-infra-to-framework.md) | Accepted | 2026-06-25 |
| 0038 | [Rename the `design-craft` pack to `experience` — live surface renamed, frozen governance bridged, no install-time alias](0038-rename-design-craft-pack-to-experience.md) | Accepted | 2026-06-25 |
| 0039 | [Install identity is the content-addressed footprint, with a `shared` prefix class](0039-footprint-co-ownership-install-identity-and-shared-prefix-class.md) | Accepted | 2026-06-26 |
| 0040 | [Route cohort skills to the shared `.agents/skills/` home](0040-route-cohort-skills-to-shared-agents-skills-home.md) | Accepted | 2026-06-26 |
| 0041 | [ADR template gains optional first-screen summary, revisit trigger, and structured Confirmation](0041-adr-template-optional-summary-revisit-confirmation.md) | Accepted | 2026-06-28 |
| 0042 | [Agent additions are keyed to loop and work type, not a global cap](0042-agent-additions-keyed-to-loop-and-work-type.md) | Accepted | 2026-06-29 |
| 0043 | [The upstream discovery coordinator is an agent + a skill + a carried sidecar-schema contract — no new runtime engine, spike-confirmed; the sidecar is the connectedness verifier](0043-the-discovery-coordinator-is-an-agent-plus-skill-plus-carried-sidecar-no-engine.md) | Accepted | 2026-06-30 |
| 0044 | [Split the build loop from a deployed-validation outer loop, and carve deploy autonomy by minimum-regret](0044-inner-outer-loop-split-and-minimum-regret-deploy-carve.md) | Accepted | 2026-06-30 |
| 0045 | [Document extraction is capability-tiered and presence-checked — a no-ML floor degrades up through agent-vision, approved-ML, and an explicit-only managed-API tier](0045-capability-tiered-document-extraction.md) | Accepted | 2026-06-30 |
| 0046 | [The `.msg` reader is `olefile` + hand-rolled MAPI parsing — permissive, no copyleft, no Python-2-broken dependency](0046-msg-reader-is-olefile-plus-hand-rolled-mapi-permissive-no-copyleft.md) | Accepted | 2026-07-01 |
| 0047 | [`experience-reviewer` is a conditional specialist reviewer in `work-loop` for user-facing surface diffs — select-or-note, full-mode only](0047-experience-reviewer-as-work-loop-gate.md) | Accepted | 2026-07-02 |
| 0048 | [Assimilation state lives in a user-scope ledger — per-run purged, per-source durable](0048-catalogue-curation-assimilation-ledger.md) | Accepted | 2026-07-02 |
| 0049 | [Catalogue runtime inventory — derive live, persist nothing, touch no Claude manifest](0049-catalogue-runtime-inventory-derive-live.md) | Accepted | 2026-07-02 |
| 0050 | [Astro for the marketing site, co-deployed with MkDocs in one GitHub Pages origin](0050-astro-marketing-site-toolchain-and-deploy.md) | Superseded by ADR-0109 | 2026-07-16 |
| 0051 | [workspace.toml: TOML format and main-branch direct spec targeting](0051-workspace-toml-toml-format-and-main-branch-coordination.md) | Accepted | 2026-07-18 |
| 0052 | [Nine experience-pack skill renames — live surface renamed, frozen governance bridged, no install-time alias](0052-nine-experience-pack-skill-renames.md) | Accepted | 2026-07-19 |
| 0053 | [product-strategy pack — scope and discipline boundaries](0053-product-strategy-pack-scope-and-discipline-boundaries.md) | Accepted | 2026-07-19 |
| 0054 | [Session-arc verb taxonomy and pack-type classification for skill naming](0054-session-arc-verb-taxonomy-and-pack-type-classification.md) | Accepted | 2026-07-20 |
| 0055 | [Wave 1 docs restructure — lift contracts/ and guides/ to repo root](0055-wave1-docs-restructure-contracts-and-guides-to-repo-root.md) | Accepted | 2026-07-26 |
| 0056 | [catalogue_tooling as the portable catalogue engine module](0056-catalogue-tooling-as-portable-engine-module.md) | Accepted | 2026-07-27 |
| 0057 | [Promote `frontend-engineering` to first-class pack; delete core resident to resolve footprint conflict](0057-frontend-engineering-pack-promotion-and-resident-deletion.md) | Accepted | 2026-07-27 |
| 0058 | [Per-pack config root (`user-root`) stored as an optional field on `PackState` adapter rows in user-scope `state.toml`](0058-per-pack-config-root-in-packstate-adapter-rows.md) | Accepted | 2026-07-28 |
| 0059 | [Pack config uses a three-source cascade baked into `_data/install-defaults.toml` at catalogue build time](0059-pack-config-cascade-via-install-defaults-baking.md) | Accepted | 2026-07-28 |
| 0060 | [`product-documentation` replaces `user-guide-diataxis` as the canonical documentation pack](0060-product-documentation-replaces-user-guide-diataxis.md) | Accepted | 2026-07-28 |
| 0061 | [Loop infrastructure Phase 1 — Option A (pure phase tracker)](0061-loop-infrastructure-phase-1.md) | Accepted | 2026-07-30 |
| 0062 | [workspace-mcp per-session-only constraint](0062-workspace-mcp-per-session-only-constraint.md) | Accepted | 2026-08-03 |
| 0063 | [Session instruction for universal elicitation interception](0063-session-instruction-universal-elicitation.md) | Accepted | 2026-08-03 |
| 0064 | [events.jsonl as the FSM event source](0064-events-jsonl-as-fsm-event-source.md) | Accepted | 2026-08-03 |
| 0065 | [elicit() tool + elicitation/create + response-file fallback](0065-elicit-elicitation-create-response-file-fallback.md) | Accepted | 2026-08-03 |
| 0066 | [Reactive git at TurnEnd](0066-reactive-git-at-turnend.md) | Accepted | 2026-08-03 |
| 0067 | [Lifecycle manifest — built-in defaults and workspace-types.d/ extension](0067-lifecycle-manifest-builtin-defaults-workspace-types-d.md) | Accepted | 2026-08-03 |
| 0068 | [Notification namespace — _agentbundle.core/](0068-notification-namespace-x-core.md) | Accepted | 2026-08-03 |
| 0069 | [Threading model — daemon threads and bounded worker pool](0069-threading-model-daemon-threads-bounded-pool.md) | Accepted | 2026-08-03 |
| 0070 | [Local scope install — `.git/info/exclude` exclusion, whole-install abort, per-worktree keyed blocks, and deferred concurrent-write lock](0070-local-scope-install-decisions.md) | Accepted | 2026-08-04 |
| 0071 | [`.apm/` is the runtime export boundary; pack tests live at `packs/<pack>/tests/`](0071-pack-runtime-export-boundary-and-test-placement.md) | Accepted | 2026-08-06 |
| 0072 | [The derived plugin manifest mirrors Claude Code's schema; the real client is the oracle](0072-derived-plugin-manifest-mirrors-upstream-schema.md) | Accepted | 2026-08-06 |
| 0073 | [Zensical is the v1 binder renderer — chosen for foundation continuity, not footprint](0073-zensical-as-the-v1-binder-renderer.md) | Accepted | 2026-08-06 |
| 0074 | [The work-loop owns its state lock; agentbundle's stays separate](0074-the-work-loop-owns-its-state-lock.md) | Accepted | 2026-08-07 |
| 0075 | [Every test has one owner — engine, catalogue, pack, or tools — and inclusion follows the owner, not the surface alone](0075-test-ownership-taxonomy-and-per-owner-inclusion.md) | Accepted | 2026-08-08 |
| 0076 | [Briefs persist; dispatch starts from specs](0076-briefs-persist-dispatch-starts-from-specs.md) | Accepted | 2026-08-08 |
| 0077 | [Feature projection is gated; tracker authority follows lifecycle](0077-feature-projection-and-tracker-authority.md) | Accepted | 2026-08-09 |
| 0078 | [Standalone intake with an artifact-backed workspace index](0078-standalone-intake-and-deterministic-workspace-index.md) | Accepted | 2026-08-09 |
| 0079 | [Executable plugin branch — dedicated publisher identity](0079-executable-plugin-branch-publisher-identity.md) | Accepted | 2026-08-10 |
| 0080 | [Generic headed SSO capture remains operator-only](0080-generic-headed-sso-capture-remains-operator-only.md) | Accepted | 2026-08-11 |
| 0081 | [Canonical project knowledge uses per-topic JSON](0081-canonical-project-knowledge-uses-per-topic-json.md) | Accepted | 2026-08-13 |
| 0082 | [Project-knowledge modes separate capture, distillation, and enquiry authority](0082-project-knowledge-modes-separate-authority.md) | Accepted | 2026-08-13 |
| 0083 | [Extend the SAST/SCA gate to npm with `npm audit` + a reasoned allowlist](0083-extend-sast-sca-gate-to-npm-with-audit-and-allowlist.md) | Accepted | 2026-08-16 |
| 0084 | [Bandit suppression reasons move behind a second `#`, and its stderr becomes a gate](0084-nosec-reason-delimiter-and-stderr-as-a-gate.md) | Accepted | 2026-08-16 |
| 0085 | [Docs rendering is site-local](0085-docs-rendering-is-site-local.md) | Accepted | 2026-08-17 |
| 0086 | [The SAST/SCA leg becomes its own CI job, and provenance is command-line origin](0086-split-the-sast-gate-into-its-own-ci-job.md) | Accepted | 2026-08-17 |
| 0087 | [Lints resolve Git-ignore status in one batched call over stdin](0087-batch-git-check-ignore-over-stdin.md) | Accepted | 2026-08-17 |
| 0088 | [Risk triggers have a single documented home](0088-risk-triggers-have-a-single-documented-home.md) | Accepted | 2026-08-19 |
| 0089 | [Decision weight trims the RFC pre-handoff gate: RFC-0054 D1 over its implementing spec](0089-decision-weight-trims-the-rfc-gate.md) | Accepted | 2026-08-19 |
| 0090 | [Distribution routes are a layer separate from runtime adapters](0090-distribution-routes-separate-from-runtime-adapters.md) | Accepted | 2026-08-20 |
| 0091 | [A Kiro Power route is justified: superseding the Kiro-route rejection only](0091-kiro-power-route-supersedes-rejection.md) | Accepted | 2026-08-20 |
| 0092 | [Direct-light execution is session-local outside workspace dispatch](0092-direct-light-execution-session-local-boundary.md) | Accepted | 2026-08-20 |
| 0093 | [OKF reference corpora remain governed build-time sources within their owning pack](0093-okf-reference-corpora-remain-governed-build-time-sources.md) | Accepted | 2026-08-21 |
| 0094 | [Per-worktree virtual environments are declined; the packages are imported from source instead](0094-no-per-worktree-virtualenv-source-imports-instead.md) | Accepted | 2026-08-22 |
| 0095 | [Level A first-value handoffs may include an optional next action](0095-level-a-first-value-optional-next-action.md) | Accepted | 2026-08-22 |
| 0096 | [Composed local CI uses an explicit post-build-check test target](0096-composed-local-ci-test-target.md) | Accepted | 2026-08-25 |
| 0097 | [Knowledge surfaces are capability-detected and OKF access is provider-mediated](0097-knowledge-access-capability-detected-provider-mediated.md) | Accepted | 2026-08-26 |
| 0098 | [Artifact admission and delivery briefs use distinct canonical owners](0098-artifact-admission-and-delivery-brief-lifecycle.md) | Accepted | 2026-08-27 |
| 0099 | [Shaping review stays stateless while delivery owns baseline replacement](0099-shaping-review-and-sealed-baseline-replacement.md) | Accepted | 2026-08-27 |
| 0100 | [Direct skill sources classify after resolution and normalize into canonical packs](0100-direct-skill-source-classification-and-normalized-lifecycle.md) | Accepted | 2026-08-27 |
| 0101 | [Pack tests are isolated by default, grouped only by a declared compatibility class](0101-pack-test-isolation-by-default-with-declared-compatibility-classes.md) | Accepted | 2026-08-28 |
| 0102 | [A Semgrep exclusion may be path-scoped for scanner performance, if it states its residual and carries a retirement trigger](0102-path-scoped-semgrep-exclusion-for-scanner-performance.md) | Accepted | 2026-08-29 |
| 0103 | [The completion receipt carries a delivery outcome, not an artifact disposition, and rides on the citing dependency edge](0103-the-completion-receipt-carries-a-delivery-outcome-not-a-disposition.md) | Accepted | 2026-09-02 |
| 0104 | [A review loop stops on divergence, not on a round budget — and a signal that cannot be calibrated advises rather than gates](0104-light-mode-review-stops-on-divergence.md) | Accepted | 2026-09-04 |
| 0105 | [Retained lifecycle records may terminate as Reclassified](0105-retained-lifecycle-records-may-terminate-as-reclassified.md) | Accepted | 2026-09-04 |
| 0106 | [Direct skill identity and upgrade revision route](0106-direct-skill-identity-and-upgrade-revision-route.md) | Accepted | 2026-09-08 |
| 0107 | [The Claude-plugin route serves non-technical adopters, as individual per-pack plugins](0107-claude-plugin-route-serves-non-technical-adopters.md) | Accepted | 2026-09-10 |
| 0108 | [Identity for loop-contract items — opaque and append-only, not positional](0108-opaque-append-only-loop-contract-identifiers.md) | Accepted | 2026-09-10 |
| 0109 | [Starlight replaces MkDocs for reference docs — Astro+Node.js only pipeline](0109-starlight-replaces-mkdocs-for-reference-docs.md) | Accepted | 2026-07-25 |
| 0110 | [A cooled child's parent scope is declared on its workspace entry, and an undeclared value fails closed rather than reading as "no parent"](0110-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md) | Accepted | 2026-09-03 |
| 0111 | [Intent review splits into a mechanical well-formedness check and a narrowed assumption attack](0111-intent-review-splits-well-formedness-from-assumption-attack.md) | Accepted | 2026-09-11 |
| 0112 | [Index tables over a document corpus are generated or absent, never hand-maintained](0112-index-tables-are-generated-or-absent.md) | Accepted | 2026-09-13 |
| 0113 | [The SAST/SCA guarantee moves from the local gate to `gate-sast`](0113-sast-guarantee-moves-from-the-local-gate-to-gate-sast.md) | Accepted | 2026-09-13 |
| 0114 | [Prune success requires a two-sided post-mutation invariant](0114-prune-success-requires-a-two-sided-post-mutation-invariant.md) | Accepted | 2026-09-13 |
| 0115 | [The loop-telemetry sender is a separately installed distribution, not pack content](0115-loop-telemetry-sender-is-a-separately-installed-distribution.md) | Accepted | 2026-09-12 |
| 0116 | [`creative-direction` writes to `direction/`, retiring `aesthetic/`](0116-creative-direction-writes-to-direction-folder-retiring-aesthetic.md) | Accepted | 2026-09-16 |
| 0117 | [ADR metadata is mechanically checkable, and the freeze binds prose, not metadata](0117-adr-metadata-is-mechanically-checkable-and-the-freeze-binds-prose.md) | Accepted | 2026-09-17 |
| 0118 | [`architect-design` authors from three scope-routed model-first templates, not one generic design doc](0118-architect-design-scope-routed-model-first-templates.md) | Accepted | 2026-09-18 |
| 0119 | [Retire the Initiative ladder into the recursive intent graph](0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md) | Accepted | 2026-09-18 |
| 0120 | [Layout-config resolution follows RFC-0096 § 4, not RFC-0040's pack-default tail](0120-layout-config-resolution-follows-rfc-0096.md) | Accepted | 2026-09-21 |
| 0121 | [A repository intent declares its altitude](0121-a-repository-intent-declares-its-altitude.md) | Accepted | 2026-09-21 |
| 0122 | [A gate-main step may carry a roster-authorized widening condition](0122-a-gate-main-step-may-carry-a-widening-condition.md) | Accepted | 2026-09-21 |
