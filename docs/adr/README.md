# Architecture Decision Records

> Immutable records of architectural decisions. See
> [`../CONVENTIONS.md`](../CONVENTIONS.md#2-adr--architecture-decision-records--docsadr)
> for what goes here and what doesn't.

| #    | Title                                       | Status   |
| ---- | ------------------------------------------- | -------- |
| 0001 | [Adopt AGENTS.md and doc hierarchy](0001-adopt-agents-md-and-doc-hierarchy.md) | Accepted |
| 0002 | [Install-scope is a per-pack default + allowance, not a per-item or adopter-only choice](0002-install-scope-per-pack-default-and-allowance.md) | Accepted |
| 0003 | [Four-broker contract for credentialed skills; in-process shim + adapter-root subprocess as the two v1 transports](0003-credential-broker-contract.md) | Accepted |
| 0004 | [Per-IDE direct writes are the repo-scope install default; dist-tree is opt-in](0004-repo-scope-per-adapter-projection.md) | Accepted |
| 0005 | [Supervisor mode — topological-order default, gated parallel writes](0005-supervisor-topological-default-and-write-gate.md) | Accepted |
| 0006 | [Doc drift — prevented by construction + judgment for adopters; mechanically gated only as catalogue governance](0006-doc-drift-construction-and-judgment.md) | Accepted |
| 0007 | [Ship the doc-drift spec-metadata lint to adopters as a work-loop skill script](0007-ship-doc-drift-lint-as-work-loop-skill-script.md) | Accepted |
| 0008 | [Contract authoring integrates via an agnostic, convention-first seam (not a core merge); contracts live in a repo-level tree](0008-contract-authoring-seam.md) | Accepted |
| 0009 | [A product-brief layer sits between roadmap and spec; the low-level design lives in the plan with a derived (never baked) stack](0009-product-brief-layer-and-plan-owned-lld.md) | Accepted |
| 0010 | [A normative `reference.md` is the repo's golden path — template-instantiated on demand, never a core seed, populated by repo context](0010-reference-architecture-foundation.md) | Accepted |
| 0011 | [Greenfield inception is a new `init-project` flow that composes existing skills — value gate over fed-in discovery, recorded foundation, then a walking skeleton; not an autonomous generator](0011-greenfield-inception-front-door.md) | Accepted |
| 0012 | [Split `kiro` into `kiro-ide` and `kiro-cli` with `kiro` as a deprecated alias, and activate `kiro-ide-hook` at contract v0.9](0012-kiro-adapter-split.md) | Accepted |
| 0013 | [Copilot is a full-parity, user-scope-capable adapter](0013-copilot-full-parity-user-scope-adapter.md) | Accepted |
| 0014 | [Rigor scales with risk — `work-loop` light/full modes](0014-rigor-scales-with-risk-work-loop-modes.md) | Accepted |
| 0015 | [Cursor is a full-parity distribution adapter](0015-cursor-full-parity-distribution-adapter.md) | Accepted |
| 0016 | [Gemini CLI is a full-parity distribution adapter](0016-gemini-cli-full-parity-adapter.md) | Accepted |
| 0017 | [Adopt Bandit + pip-audit + Semgrep as the repo's SAST/SCA gate](0017-adopt-bandit-pip-audit-semgrep-sast-gate.md) | Accepted |
| 0018 | [Shift security review left and deliver its depth via an orchestrator-loaded progressive-disclosure skill](0018-shift-security-review-left-progressive-disclosure.md) | Accepted |
| 0019 | [Product shaping is a recursive level-tagged `intent` tree; a brief is a feature-intent projected onto one repo; contracts mature by stage](0019-product-intent-ontology-and-brief-projection.md) | Accepted |
| 0020 | [Per-pack Diátaxis hierarchy for `docs/guides/` (`docs/guides/<pack>/{quadrant}/`) — amends ADR-0001's guides sub-decision; adopter seed scaffold stays type-at-top](0020-per-pack-diataxis-hierarchy-for-guides.md) | Accepted |
| 0021 | [`pack.toml` is the metadata source of truth, projected lossily per tool; pack identity is `@catalogue/pack` (RFC-0031 D2 + D7)](0021-pack-manifest-source-of-truth-and-scoped-identity.md) | Accepted |
| 0022 | [The business-unit cross-component layer — a value-stream meta-repo, per-component brief slicing with `parent-intent` provenance, and a referenced (never forked) shared contract](0022-value-stream-meta-repo-cross-component-layer.md) | Accepted |
| 0023 | [The "three reviewers" ceiling scopes the core code-review lenses, not opt-in design-side reviewers (RFC-0032 decision 2)](0023-reviewer-ceiling-scopes-core-code-review-lenses.md) | Superseded by ADR-0042 |
| 0024 | [`design-craft` serves designers as upstream design-intent authors, under strict framework-agnosticism](0024-design-craft-upstream-intent-and-agnosticism.md) | Accepted |
| 0025 | [Pack profiles are single-scope, catalogue-owned CLI manifests — not meta-packs](0025-pack-profiles-single-scope-cli-manifest.md) | Accepted |
| 0026 | [SSO-cookie consumer resolution lives in the `credbroker` library, platform-agnostic](0026-sso-consumer-resolution-in-credbroker.md) | Accepted |
| 0027 | [ADR format is MADR-aligned but lean, not full MADR (Rejected status, MADR 4.0 frontmatter, optional Decision drivers + Confirmation; decision stays answer-first)](0027-adr-format-is-madr-aligned-but-lean.md) | Accepted |
| 0028 | [Pack-level activation evals adopt the agentskills.io trigger-eval convention; coverage in `pack.toml`; runner is catalogue-internal tooling](0028-pack-activation-evals.md) | Accepted |
| 0029 | [Research pack structure — two orthogonal axes (depth × lifecycle), with a prompt-only project mode](0029-research-two-axes-depth-and-lifecycle.md) | Accepted |
| 0030 | [Consolidated, namespaced pack-output layout contract (`agentbundle-layout.toml`)](0030-consolidated-pack-output-layout-contract.md) | Accepted |
| 0031 | [Infra `work-loop` support is doctrine on existing reviewers — `quality-engineer` for operational safety, a mandatory `security-reviewer` + scanner pair for security — not a new reviewer or runtime](0031-infra-support-is-doctrine-on-existing-reviewers-not-a-new-reviewer-or-runtime.md) | Accepted |
| 0032 | [The agentic well-architected overlay is a first-class workload-class lens applied at design *and* review — a routing axis plus progressive taxonomy on the existing `architect` skills, not a new primitive](0032-agentic-overlay-is-a-design-and-review-workload-class-lens.md) | Accepted |
| 0033 | [The intent `Level` is reopened to an open recognized set (`product-vision › product-strategy › capability › feature`) and decoupled from `Scale` — a refinement of ADR-0019, prompt-only](0033-intent-level-open-recognized-set-decoupled-from-scale.md) | Accepted |
| 0034 | [Grounding the infra inner loop in platform reality is toolchain-oracle doctrine + EXECUTE-loaded craft — one new `core` skill, not executable tooling, per-vendor data, or a new agent](0034-infra-grounding-toolchain-oracle-doctrine-not-tooling-vendor-data-or-agent.md) | Accepted |
| 0035 | [Grounding the architect *design* phase in platform reality — the deferred serverless lens + a dual-consumed grounding discipline and sync-path viability check, prose-only on the existing routing axis](0035-architect-design-phase-grounded-in-platform-reality-dual-consumed-serverless-lens-and-contract-grounding.md) | Accepted |
| 0036 | [The install-source default resolves through a trusted-by-construction precedence chain — editable detection as the downstream default, no repo-scoped source, no cwd fallback](0036-install-source-resolves-through-trusted-precedence-chain-no-repo-source-no-cwd.md) | Accepted |
| 0037 | [Grounding context is adopter- and org-supplied and presence-checked — the EXECUTE contract-grounding gate generalizes from infra to framework/library through one detect-and-recommend tier, extending (not breaking) ADR-0034's no-bundled-KB rule](0037-grounding-is-adopter-and-org-supplied-and-presence-checked-one-gate-from-infra-to-framework.md) | Accepted |
| 0038 | [Rename the `design-craft` pack to `experience` — live surface renamed, frozen governance bridged, no install-time alias (the `contract-acquisition` precedent)](0038-rename-design-craft-pack-to-experience.md) | Accepted |
| 0039 | [Install identity is the content-addressed footprint, with a `shared` prefix class — co-ownership derived (not stored), conflicts refuse / `--force` drops `.upstream` (RFC-0052; pairs with ADR-0002)](0039-footprint-co-ownership-install-identity-and-shared-prefix-class.md) | Accepted |
| 0040 | [Route cohort skills (codex, cursor, gemini, copilot) to the shared `.agents/skills/` home — supersedes the skill-home sub-decision of ADR-0013/0015/0016; agent/hook/command projection stands](0040-route-cohort-skills-to-shared-agents-skills-home.md) | Accepted |
| 0041 | [ADR template gains optional first-screen summary, revisit trigger, and structured Confirmation — extends ADR-0027 (lean-compatible additions, not superseded)](0041-adr-template-optional-summary-revisit-confirmation.md) | Accepted |
| 0042 | [Agent additions are keyed to loop and work type, not a global cap (supersedes ADR-0023)](0042-agent-additions-keyed-to-loop-and-work-type.md) | Accepted |

## Adding a new ADR

```bash
# Find the next number (portable across macOS, Linux, native Windows).
N=$(python3 .claude/skills/new-adr/scripts/next-ordinal.py docs/adr)

# Create from template
cp .claude/skills/new-adr/assets/adr.md docs/adr/${N}-<kebab-title>.md
```

Or, in Claude Code, run `/new-adr "<title>"` (defined in `.claude/skills/new-adr/SKILL.md`).
