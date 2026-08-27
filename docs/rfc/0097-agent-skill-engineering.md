# RFC-0097: Agent skill engineering

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-26
- **Date closed:** 2026-08-26
- **Decision weight:** heavy
- **Related:** [future architecture](../architecture/agent-skill-engineering.md), [ADR-0093](../adr/0093-okf-reference-corpora-remain-governed-build-time-sources.md), [RFC-0037](0037-pack-activation-evals.md), [RFC-0076](0076-catalogue-contracts-composition-semantics-discovery.md), [RFC-0087](0087-okf-knowledge-projection.md), [RFC-0092](0092-first-class-distribution-routes.md), [INI-009](../product/initiatives/ini-009-agent-skill-engineering.md)

## Reviewer brief

- **Decision:** Establish a portable agent-skill-engineering pack whose two user-facing workflows and one integration-facing knowledge router are backed by a governed, same-pack Open Knowledge Format (OKF) corpus.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - Add focused author/update and review/optimize workflows, plus a non-self-discovering reference router that other installed agent loops may invoke.
  - Consolidate reusable skill, script, evaluation, orchestration, hook, plugin, and execution-economics practice into progressively disclosed knowledge topics with a portable floor and dated, sourced enterprise runtime profiles.
  - Self-host the pack in this repository, then shrink duplicated guidance and catalogue-curation content only after routed parity is demonstrated.
- **Affected surface:** A new portable pack; work-loop and architect-design integrations; skill and pack authoring journeys; selected `AGENTS*.md`, guide, catalogue-curation, and tooling guidance; backlog ownership under INI-009.
- **Stakes:** Reversible at the workflow and integration layers, but costly if the corpus becomes a second platform manual or if source guidance is deleted before retrieval parity is proven.
- **Review focus:** Portability boundary, knowledge retrieval precision, authority and trust, runtime-profile maintenance, evidence thresholds, and the staged footprint reduction.
- **Not in scope:** AgentBundle manifest or projection mechanics inside the portable content, a generic CI framework, a runtime OKF loader, hosted retrieval, or immediate deletion of existing enforcement and repository-specific rules.

## The ask

### Recommendation

Accept a new `agent-skill-engineering` pack with two active workflows—**author/update** and **review/optimize**—and one inert, integration-facing reference router compiled from a same-pack OKF corpus. The corpus should be useful beyond direct skill authoring: work-loop, architect-design, skill/evaluation CI design, and later explicitly integrated loops may retrieve bounded knowledge topics without searching raw OKF or loading a handbook.

The portable floor should cover principles that survive runtime changes. Topics whose facts vary by runtime—especially subagent/skill composition, hooks, and plugin packaging—must live in clearly labeled, dated runtime profiles. The initial enterprise profile set is Claude Code, Codex, GitHub Copilot, Cursor, Kiro IDE, Kiro CLI, Gemini CLI, and Google Antigravity. AgentBundle remains the external catalogue and projection mechanism that packages and integrates the portable content; the pack must not teach an “AgentBundle way” as general agent engineering.

### Why now

Reusable practice has accumulated across catalogue guidance, individual specifications, local repository instructions, tooling, and Codex's platform-specific skill creator. The practice is now broad enough to improve skill authoring, review, skill/evaluation CI design, and agent-loop architecture, but it is duplicated, hard to retrieve precisely, and mixed with catalogue-specific mechanics. Recent repository work also exposed a connected execution-economics body of knowledge: process startup cost, CI critical-path splitting, safe batching, fixture isolation, worktree attribution, state locks, and shared-machine admission all affect whether agent skills and their evaluations remain usable at scale.

At the same time, the surrounding extension surfaces are diverging. Agent Skills provide a portable authoring substrate, while subagents, hooks, and plugin packages differ materially among Claude Code, Codex, GitHub Copilot, Cursor, Kiro IDE and CLI, Gemini CLI, and Google Antigravity. Universalizing any one runtime's behavior would make the new pack misleading. Keeping all of the material in catalogue-curation or work-loop would make those packs generic knowledge retrievers and deny other loops a reusable, user-facing authoring workflow.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | What owns reusable agent-skill engineering practice? | A new portable pack with two workflows and one same-pack generated reference router. | It gives authors a usable workflow while keeping the knowledge reusable by other loops. | 2026-09-09 | Accept or propose a smaller capability boundary. |
| D2 | How may other loops consume the corpus? | Through explicit optional integrations that invoke the installed provider router; never by searching raw OKF. | This preserves authority, progressive disclosure, and ADR-0093's build-time boundary. | 2026-09-09 | Confirm the provider-mediated pattern. |
| D3 | How should portable and runtime-specific guidance coexist? | A capability-keyed common floor plus sourced, retrieval-dated profiles for eight initial enterprise runtime surfaces. | Subagents, hooks, and plugins have no sufficiently uniform cross-runtime contract. | 2026-09-09 | Confirm the profile topology and update policy. |
| D4 | Where do AgentBundle mechanisms belong? | Outside the portable pack, in catalogue metadata, adapters, tooling, and maintainer guidance. | A delivery mechanism must not become universal engineering doctrine. | 2026-09-09 | Reject any portable topic that requires AgentBundle vocabulary to be useful. |
| D5 | How broad is execution optimization? | Include measurement-led skill, pack, CI, worktree, and shared-host economics; exclude generic developer productivity. | Local and CI costs interact, but relevance must remain tied to agent skills, scripts, and evals. | 2026-09-09 | Confirm the relevance test and safety constraints. |
| D6 | What existing footprint should collapse? | Migrate duplicated explanatory practice to the corpus in stages; retain repository facts, enforcement, and adapter mechanics at their owners. | Deletion without routed parity creates discoverability and authority regressions. | 2026-09-09 | Confirm the retain/migrate/retire map. |
| D7 | How is delivery governed? | Create INI-009, disposition related backlog items, and require an ADR plus staged specs before implementation. | The work crosses packs, guides, adapters, and repository self-hosting. | 2026-09-09 | Approve the initiative and backlog ownership map. |
| D8 | What evidence, trust, and privacy controls govern the corpus? | Require retrieval-dated provenance, explicit profile lifecycles, passive handling of untrusted inputs, least-authority execution, and redacted/minimized promoted evidence. | Knowledge, hooks, plugins, and observations cross instruction, code, and enterprise-data trust boundaries. | 2026-09-09 | Confirm the admission and lifecycle controls. |

## Problem & goals

### Diagnosis

The repository has four kinds of material interleaved today:

1. **Portable practice:** trigger quality, instruction density, progressive disclosure, deterministic scripts, evaluation design, isolation, and evidence-based optimization.
2. **Runtime-specific practice:** how Claude or Codex exposes skills to subagents, isolates work, loads hooks, packages plugins, and applies permissions.
3. **Catalogue-specific mechanics:** `packs/<pack>/`, `pack.toml`, projection contracts, version bumps, self-host synchronization, admission, and publication.
4. **Ordinary language/tool engineering:** Python, pytest, TypeScript, Node.js, and CI techniques that are useful only when connected to a skill script or evaluation contract.

Because these categories are not consistently separated, authors must read broad guides or copy recent examples; review criteria drift across skills; optimization lessons remain buried in specifications and commits; and always-loaded guidance grows to carry procedural material that should be retrieved only when relevant. Catalogue-curation contains reusable craft knowledge that is not catalogue-specific, while work-loop and architect-design cannot access the same corpus without duplicating it.

Subagents, hooks, and plugins make the boundary more important. The portable question is not “which frontmatter key does Claude or Codex use?” but “what context, skills, permissions, isolation, lifecycle enforcement, and packaging capabilities does this design require?” A runtime profile may then answer how a particular adapter currently realizes or lacks those capabilities.

### Terms used in this RFC

- **Agent Skill:** A directory whose `SKILL.md` describes a reusable workflow or body of expertise, with optional scripts and references, following the open Agent Skills format.
- **Open Knowledge Format (OKF):** The governed source format used here to author structured knowledge. It is compiled at build time into ordinary Markdown references; an agent does not execute or query raw OKF at runtime.
- **Capability floor:** Runtime-neutral questions and safety properties a design must address before choosing product-specific syntax.
- **Runtime profile:** Retrieval-dated, product-and-surface-specific facts that map the capability floor to one runtime. A profile is evidence, not a portability guarantee.
- **Provider router:** The integration-facing skill that accepts a bounded semantic request and returns selected compiled topic identifiers, guidance, status, and warnings without taking mutation authority.
- **Skill pattern:** A reusable arrangement of trigger, instructions, resources, scripts, state, composition, and output contract. Patterns guide design choices; they are not mandatory templates or catalogue projection formats.
- **Activation evaluation:** A test of whether the intended skill is selected for positive prompts and not selected for near misses. A **behavioral check** tests the resulting workflow behavior; a **construction check** tests the static shape of an artifact such as metadata, links, or files.
- **Adapter and projection:** An adapter maps portable source primitives to one runtime; a projection is the generated runtime-specific artifact. Both are external AgentBundle delivery mechanics in this proposal.
- **Self-host:** Install this catalogue's own published pack sources back into this repository's runtime-specific agent directories so maintainers exercise what the catalogue ships.
- **Admission:** The catalogue-owned decision that a pack or primitive satisfies repository governance and may be published.
- **Architecture decision record (ADR):** A durable record of an accepted architecture choice. **INI-009** is the initiative record grouping the delivery milestones; `M0`, `M1`, and later labels are its ordered milestones.
- **Static application security testing (SAST):** Source-code scanning for security weakness patterns.
- **Knowledge-parity linter:** A repository check that keeps duplicated knowledge taxonomies synchronized; this RFC treats needing such a check as a sign that one taxonomy should instead be owned once and routed.

### Goals

- Give skill authors one portable workflow for framing and updating skills and another for evidence-led review and optimization.
- Encode the reusable skill-pattern families present across this repository's packs, with examples, fit/non-fit criteria, and progressively disclosed construction guidance.
- Make reusable engineering knowledge retrievable in small, task-shaped topics by those workflows and by other explicitly integrated agent loops.
- Define a portable capability floor for skill/subagent composition, hooks, and plugin packaging without flattening real differences across the initial enterprise runtime set.
- Cover Python/pytest and TypeScript/Node skill scripts and evaluations as separate language topics under shared contracts.
- Treat performance as execution economics across script, pack, CI, worktree, and shared-host scopes, while preserving semantics, isolation, and security.
- Promote practice only from reproducible external contracts or repeated observed failures, with provenance and applicability limits.
- Self-host the pack and reduce duplicated repository guidance without moving repository-specific mechanics or enforcement into it.

### Non-goals

- Defining or implementing AgentBundle manifests, projections, versioning, self-host commands, catalogue lint, publication, or adapter support inside portable pack content.
- Making hooks, subagents, or plugins portable by assertion; the corpus describes a common capability floor and honest runtime deltas.
- Building a generic pytest, Node, CI, Git worktree, or developer-productivity collection unrelated to skills and evaluations.
- Replacing linters, test runners, state locks, admission controls, or managed enterprise policy with prose.
- Giving OKF runtime authority, executable semantics, network retrieval, cross-pack raw-source resolution, or a central core loader.
- Removing existing guidance before the replacement route is installed, tested, and observed to answer the same maintainer tasks.

## Proposal

### D1 — Pack shape and owned workflows

The new pack owns three skills in its portable content:

```text
agent-skill-engineering
├── author-or-update-agent-skill       user-facing workflow
├── review-or-optimize-agent-skill     user-facing workflow
└── agent-skill-engineering-reference  integration-facing, non-self-discovering router
```

The names are provisional implementation names; the behavioral split is the decision. A future spec may shorten them if activation evaluation shows a clearer naming set.

The **author/update** workflow owns:

- job and trigger framing, positive and near-miss boundaries;
- instruction architecture, density, progressive disclosure, and resource placement;
- deterministic helper design, dependency detection, portability, and exit contracts;
- evaluation topology, fixtures, isolation, and initial execution budget;
- composition decisions: main-context skill, isolated subagent, event hook, plugin package, or a deliberate combination;
- a runtime capability check before using a runtime-specific extension.

It exposes progressive modes rather than separate top-level authoring skills:

| Mode | Use | Loads |
| --- | --- | --- |
| `frame` | Clarify the job, trigger boundary, authority, and likely pattern without editing | Portable framing plus the compact pattern index |
| `create` | Build a new skill from one or more selected patterns | The selected pattern modules, relevant language topic, and eval contract |
| `update` | Change an existing skill while preserving or intentionally revising its activation and behavior contracts | Detected current patterns, observed failures, and only affected construction topics |
| `knowledge-provider` | Build or revise a governed corpus, retrieval/router/search skill, or author-owned procedure-to-reference handoff | Knowledge-provider patterns, provenance, retrieval evals, and security boundaries |
| `runtime-package` | Prepare skills or knowledge providers for a runtime plugin, extension, Power, or user-profile distribution route | Portable packaging floor plus one exact runtime profile; external delivery mechanics remain external |

Modes share one workflow identity and may progress from `frame` into a construction mode. They are not cumulative by default: the workflow records the selected mode and pattern identifiers, loads only those modules, and asks before crossing from advisory framing into file mutation or runtime packaging. `runtime-package` may describe a portable package boundary, but exact Claude plugin, OpenAI plugin, Copilot plugin, Cursor/Agent Plugin, Kiro Power, Gemini extension, Antigravity plugin, or AgentBundle publication steps come from the dated runtime profile or external delivery owner.

Mode availability follows delivery evidence. M1 advertises `frame`, `create`, and `update` for the foundation patterns only. The pack may use its own compiled router internally at M1, but it does not advertise `knowledge-provider` as an authoring mode until the M2 provider-pattern fixtures pass. `runtime-package` is likewise absent from advertised modes until M2's package-lifecycle claims and profile gates pass. An unavailable mode is omitted from activation metadata and returns a versioned `unavailable-mode` result if addressed explicitly; it is never presented as partially complete.

The **review/optimize** workflow owns:

- activation, behavioral, construction, and regression review;
- observed-failure classification and root-cause evidence;
- script safety, portability, determinism, and authority review;
- measured local, pack, and CI cost analysis;
- orchestration review for duplicated work, context leakage, conflicting writes, and unbounded concurrency;
- optimization that preserves contracts, with before/after evidence and a reversal path.

The **reference router** is not a third authoring workflow. It uses an **integration-only activation profile**: ordinary user prompts and generic knowledge questions are negative activation fixtures, while a consuming workflow addresses the provider by its exact installed identity and passes the semantic request below. Some runtimes cannot hide an installed skill or guarantee that metadata never auto-activates; on those runtimes the adapter may still expose the router, but its description must state “explicit workflow invocation only,” near-miss activation must be tested, and a spurious activation returns `out-of-scope` without reading topic bodies. The router first routes by task and capability, then reads generated indexes or topic bodies. It returns knowledge; it does not claim authority to mutate files, spawn agents, install packages, or change permissions.

### D2 — Multi-consumer knowledge integration

The same-pack OKF source is compiled into ordinary reference files owned by `agent-skill-engineering`, following ADR-0093. Raw OKF is a governed build-time source only. The generated router reads the compiled same-pack indexes; it never dynamically interprets raw OKF.

Other packs consume the installed router through explicit optional integrations:

```text
author/update ───────┐
review/optimize ─────┤
work-loop ───────────┼─ explicit provider invocation
architect-design ────┤              │
future agent loop ───┘              ▼
                         agent-skill-engineering-reference
                                      │
                                      ▼
                           generated same-pack indexes
                                      │
                                      ▼
                              bounded topic selection
```

The provider-mediated integration has five rules:

1. A consumer decides when its task directly concerns a skill, skill script/evaluation CI, agent-loop orchestration, hook, or plugin and requests a bounded topic or question. Generic CI and developer-productivity requests are out of scope.
2. The provider router selects no more material than the question requires and reports the selected topic identifiers.
3. The provider is read-only and inert. The calling workflow retains all mutation and decision authority.
4. If the provider is absent, the consumer reports the unavailable optional augmentation and continues with its pre-existing baseline workflow; it does not search for raw OKF or claim profile-backed validation. Provider absence never blocks an initial consumer in this RFC.
5. Integration declarations and adapter projection are external packaging concerns. Portable instructions describe the semantic request, not `pack.toml` syntax or AgentBundle commands.

The portable request/response envelope is semantic rather than transport-specific. A consuming workflow supplies:

| Request field | Contract |
| --- | --- |
| `contract_version` | `agent-skill-engineering-reference/v1` |
| `task_kind` | One of `skill-authoring`, `skill-review`, `skill-eval-ci`, or `agent-extension-design` |
| `question` | One bounded natural-language question with no embedded authority change |
| `capabilities` | Zero or more capability terms such as `activation`, `pytest`, `node`, `subagents`, `hooks`, `plugins`, `worktrees`, or `ci-critical-path` |
| `runtime` | Optional exact runtime/surface profile; never inferred when the distinction affects safety |
| `max_topics` | Integer 1–3; default 3 |

The provider returns `contract_version`, `status` (`ok`, `out-of-scope`, `unavailable`, or `stale-profile`), zero to three `topic_ids`, the selected compiled guidance, profile state and provenance dates where applicable, and warnings. It returns no commands to execute and no mutation instruction. Malformed, generic, authority-changing, or over-broad requests return `out-of-scope` without topic bodies. A consumer's **documented fallback** is its own behavior when the optional provider is absent; it must be named in the external integration declaration and tested without this pack installed.

This is not direct cross-pack OKF resolution. The owning pack compiles and serves its own ordinary references. The follow-on ADR must record this provider-mediated multi-consumer pattern and its relationship to ADR-0093 before consumer integrations ship.

Initial consumers are:

| Consumer | Retrieval use | Authority retained by consumer |
| --- | --- | --- |
| Author/update workflow | Framing, structure, scripts, evals, composition, runtime profile | Authoring decisions and edits |
| Review/optimize workflow | Review rubric, failure classification, measurements, safe optimization | Findings, remedies, and edits |
| work-loop | Test topology, CI economics, worktree/shared-host safety, skill-related task guidance | Planning, execution, verification, and review gates |
| architect-design | Agent extension boundaries, capability-floor comparison, runtime deltas, and skill/evaluation CI architecture | Architecture analysis and decisions |
| Later loops | Only a declared task-shaped integration | Their existing workflow authority |

### D3 — Corpus topology: portable floor, language topics, and runtime profiles

The corpus is organized by semantic questions, not by the repository files that happened to teach them first. The initial topology is:

```text
foundations/
  framing-and-trigger-quality
  instruction-density-and-progressive-disclosure
  resources-scripts-and-exit-contracts
patterns/
  inline-and-progressive-reference-skills
  multimode-artifact-and-script-backed-skills
  routers-composed-workflows-and-lifecycle-skills
  depth-libraries-and-okf-knowledge-providers
  compatibility-and-runtime-package-patterns
usability/
  activation-discoverability-and-mode-wayfinding
  workspace-orientation-status-and-resumption
  progressive-result-presentation-and-next-actions
evaluation/
  activation-and-near-miss-evals
  behavioral-and-construction-checks
  fixtures-isolation-and-execution-economics
languages/
  python-and-pytest
  typescript-node-and-javascript-test-runners
execution/
  process-and-filesystem-cost
  pack-and-ci-critical-paths
  worktrees-state-locks-and-shared-host-admission
composition/
  skills-and-subagents-common-floor
  hooks-common-floor
  plugin-package-common-floor
runtimes/
  claude-code-skills-subagents-hooks-and-plugins
  codex-skills-subagents-hooks-and-plugins
  github-copilot-skills-subagents-hooks-and-plugins
  cursor-skills-subagents-hooks-and-plugins
  kiro-ide-skills-agents-hooks-and-powers
  kiro-cli-skills-subagents-hooks-and-powers
  gemini-cli-skills-subagents-hooks-and-extensions
  google-antigravity-skills-subagents-hooks-and-plugins
security-and-authority/
  trust-boundaries-and-instruction-provenance
  authentication-and-secret-context-isolation
  permissions-sandboxes-and-side-effects
maintenance/
  repository-pattern-census-and-exemplar-selection
  evidence-promotion-and-applicability
  measurement-regression-and-retirement
```

#### Pack-derived skill patterns

The initial corpus must classify every authored skill under `packs/*/.apm/skills/` against at least one pattern family or record a reviewed exception. This is a maintained census, not a demand that every skill be rewritten. The first families evidenced by the current packs are:

| Pattern family | Construction question | Current exemplars |
| --- | --- | --- |
| Inline procedure | Can the complete safe workflow remain in one concise `SKILL.md`? | Focused contract and strategy skills |
| Progressive reference | Which references are loaded only after a task or concern is selected? | Contract, design, and frontend skills |
| Explicit multi-mode | Are modes mutually exclusive, cumulative stages, or orthogonal axes, and how is the choice recorded? | `work-loop`, `architect-assess`, `architect-diagram`, `author-product-docs`, `desk-research` |
| Deterministic script-backed | Which operations require stable parsing, rendering, state, or exit codes rather than model improvisation? | Converter, status, intake, governance, and integration skills |
| Artifact/template producer | What typed artifact, template, output path, and validation contract does the skill own? | Specification, RFC/ADR, product-engineering, design, and conversion skills |
| Router or intake classifier | Can routing be deterministic, bounded, and independently tested before another workflow acts? | `work-intake`, brief-intake, and reference-router skills |
| Composed workflow or skill family | Which child skill owns each stage, what is passed between them, and who synthesizes? | `discovery-loop`, research-project lifecycle, and architect workflows |
| State/status/lifecycle | Is durable state necessary, who owns transitions, and what are recovery and read-model contracts? | `workspace-status`, work-loop infrastructure, refresh/status skill families |
| Orientation/read model | What does a cold or returning user need to understand the workspace, active thread, blockers, and safe next action without reading all source artifacts? | `workspace-status`, `experience-status`, `rfc-status`, `fe-status`, research-project status |
| Progressive presentation | Which representation—short answer, status-first list, key/value record, table, flow, detailed artifact, or machine-readable sidecar—makes the result easiest to act on at this stage? | Workspace and domain status skills, reports, diagrams, converter proofs |
| Workspace context and resumption | Which local context is authoritative, how is scope resolved, and what receipt lets a later session resume without replaying the whole workflow? | Work intake/status, design and research threads, loop state |
| Integration/credential boundary | Which API or external tool contract is crossed, and how are credentials kept outside model context? | Atlassian, GitHub, Linear, Figma, and credential-setup skills |
| Inert depth library | How can another workflow load only matched checklists while preventing ordinary prompt activation? | `operational-safety`, `security-checklists`, architecture lenses |
| OKF knowledge provider | How are governed OKF sources compiled into ordinary references and exposed through a bounded retrieval, router, or search skill? | Architecture lenses, security checklists, and the cost-engineering pilot |
| Procedure plus generated-reference handoff | Which authored procedure retains authority while generated knowledge supplies selected depth? | `security-checklists` with `security-checklists-reference`; architect consumers with architecture lenses |
| Compatibility/deprecation | How does an old trigger route users to a replacement without preserving duplicate doctrine? | `new-guide` compatibility skill |
| Runtime/user-profile package | Which skills and provider assets form a cohesive plugin-like unit, at what user/project scope, with what install/update/uninstall behavior? | Catalogue plugin projections plus the dated Claude, Codex, Copilot, Cursor, Kiro, Gemini, and Antigravity profiles |

Each pattern topic contains: problem and fit signals; near-miss and anti-pattern signals; minimum contract; context-loading shape; script/reference/assets topology where relevant; activation, behavior, and construction checks; authority and failure boundaries; at least one repository exemplar; and applicability limits. Repository-specific file paths and AgentBundle commands remain evidence annotations or external links, not portable instructions.

Usability patterns apply across construction patterns. An author should make the skill discoverable at the user's vocabulary, declare its mode and current scope early, orient cold and returning users from a bounded read model, present status before detail, choose a representation that fits the relationship being explained, surface one safe next action, and preserve a resumable receipt when work spans sessions. Progressive disclosure applies to outputs as well as instructions: begin with the decision, state, or artifact the user needs; reveal provenance, diagnostics, and advanced controls when requested or required by risk. These are behavior contracts with usability fixtures, not visual-style preferences.

The **OKF knowledge-provider pattern** receives dedicated depth because it composes several reusable ideas: governed knowledge sources; deterministic build-time compilation; generated progressive indexes; an inert retrieval/router/search skill; optional active consumer workflows; and distribution as a cohesive runtime package. A bounded search variant may search only compiled, provider-owned references and must return topic IDs and provenance; it may not discover raw OKF or arbitrary other packs. A procedure-plus-reference variant keeps action authority in an authored workflow and treats the generated provider as inert depth.

Runtime packaging is a separate final layer. Where the target supports it, a project or user-profile skill collection may be published as a Claude plugin, OpenAI agent plugin, Copilot plugin, Cursor or portable Agent Plugin, Kiro Power, Gemini extension, Antigravity plugin, or another dated runtime package. The profile must cover scope and precedence, component discovery, namespacing, version/update behavior, policy controls, disable/uninstall recovery, and whether a user-profile source can be safely converted into a package without losing ownership or provenance. AgentBundle may implement publication or projection for supported routes, but those commands and manifests stay outside the portable pattern.

#### Shared language contracts

Python/pytest and TypeScript/Node are separate retrieval topics because their dependency, module, subprocess, test-discovery, isolation, and CI behaviors differ. They share higher-level contracts:

- declare or detect dependencies before execution;
- prefer deterministic helpers when model reasoning adds no value;
- make working-directory and input/output assumptions explicit;
- use stable exit codes and concise diagnostics;
- isolate mutable state and make fixture ownership visible;
- measure process, filesystem, network, and cache costs before optimizing;
- preserve behavior and security boundaries when batching or moving work in-process.

The Python topic may teach pytest collection, fixtures, parametrization, process boundaries, and temporary-path behavior where they directly support skill scripts or evals. The TypeScript/Node topic must separately cover package and module contracts, lockfile-respecting clean installs, child-process behavior, test-runner worker models, browser-worker economics, cache keys, and JavaScript/TypeScript security scanning. Neither topic becomes a general language handbook.

#### Skills and subagents

The portable common floor asks capability questions before runtime syntax:

- Is the work better in the main context or an isolated context?
- Which skill knowledge must the delegated agent receive: metadata, full instructions, selected references, or a summarized brief?
- Does the runtime inherit skills automatically, preload named skills, or require explicit paths?
- Does the subagent share a filesystem or worktree, and who owns writes?
- Which permission and tool restrictions survive delegation?
- Is nested delegation supported, bounded, or prohibited?
- What concurrency cap, token budget, waiting behavior, result contract, and synthesis owner apply?
- How are duplicate exploration, conflicting writes, partial failures, and cancellation handled?

The default portable guidance is conservative: delegate bounded, independent work; prefer read-heavy parallelism; assign explicit ownership before parallel writes; pass only the skill context needed; cap concurrency; require structured results; and keep final synthesis and authority in the parent loop.

Runtime profiles then state current behavior. The profiles are separate even when two products share an engine or file format, because enterprise surfaces differ in discovery, policy, execution environment, and release cadence:

| Profile | Minimum initial coverage |
| --- | --- |
| Claude Code | Skill preloading versus invocation, isolated subagent context, worktree isolation, nesting limits, component-scoped hooks, plugin-agent restrictions, and managed hook policy |
| Codex | Instruction-driven delegation, inherited versus explicitly configured skills, sandbox/approval inheritance, shared-workspace coordination, concurrency controls, custom-agent configuration, parent synthesis, and plugin-hook trust |
| GitHub Copilot | Project/personal skill locations, custom-agent and subagent behavior by CLI/cloud/IDE surface, hook event and policy tiers, cloud sandbox differences, and plugin availability |
| Cursor | Project/user/team skill discovery, manual-only activation and custom modes, isolated subagents, IDE/CLI/cloud deltas, local and managed hooks, Agent Plugins versus Cursor Plugins, and permission degradation |
| Kiro IDE | Skill discovery, custom-agent resources and default inheritance, IDE hook support, permissions, and Power packaging/activation |
| Kiro CLI | Skill resource URIs, subagent orchestration, CLI-only agent hook fields, headless behavior, permissions, and Power version support |
| Gemini CLI | Skill discovery precedence, preview subagents, hook JSON I/O and exit semantics, extension packaging, policy tiers, and environment-variable sanitization |
| Google Antigravity | Skill paths, clean-context subagents, workspace modes including worktrees, permission inheritance, nesting, hook contracts, and plugin packaging |

Every runtime claim carries the source URI, **date retrieved**, source-published/updated date or product version when exposed, claim scope, and last verification result. Unsupported, preview, contradictory, or uncertain behavior is labeled, never filled in from another runtime. Capability-claim freshness is independent of the portable floor.

Each required capability claim has an explicit state:

| State | Entry condition | Router behavior |
| --- | --- | --- |
| `verified` | Official source acquired within the profile's declared window (never more than 90 days), no known contradictory newer release, and the claim's contract fixture or bounded manual probe passed | Return guidance and permit a support claim with dates |
| `experimental` | Official source and retrieval date exist, but execution behavior is preview-only or has not been independently probed | Return sourced facts with an experimental warning; no verified support claim |
| `stale` | Verification window elapsed, a relevant release landed, or a source changed without revalidation | Return `stale-profile`, identifiers and provenance only; do not return operative runtime guidance |
| `unavailable` | Sources conflict materially, the capability is absent, or safe verification cannot be performed | Return the known limit and provenance; do not synthesize behavior |

Profiles roll up separately. A profile is `complete-current` when every required capability row exists, has current first-party evidence, and is honestly classified as `verified`, `experimental`, or `unavailable`; an absent capability recorded as `unavailable` is a useful enterprise delta and does not fail the profile. Any `stale` required row makes the profile `needs-revalidation`; a missing required row makes it `incomplete`. The router returns the state of each selected claim and the profile roll-up, never a more favorable aggregate.

The M1 experimental foundation release is blocked on the portable workflows and router, not on runtime-profile completion. M2 is not complete until all eight profiles are `complete-current`; any capability advertised as supported must be `verified`. This lets the corpus include every requested enterprise surface without turning an unprobed or absent capability into doctrine.

A knowledge profile is not an AgentBundle adapter-support claim. The profile may guide a directly installed portable skill even when this repository has no projection adapter for that surface. AgentBundle's current adapter contract remains the sole owner of projection support; adding or widening an adapter, including any future Antigravity route, requires its own governed change and tests outside this pack.

#### Hooks

The common hook topic distinguishes:

- deterministic enforcement from model-interpreted guidance;
- lifecycle observation from authority-changing interception;
- pre-action blocking from post-action diagnostics;
- component-scoped from repository, user, plugin, or managed hooks;
- trusted executable code from untrusted repository instructions;
- stable event/input/output contracts from runtime-specific envelopes.

Hooks are not a portable guarantee. Runtime profiles own event names, matcher semantics, configuration scopes, output protocols, trust prompts, managed-policy restrictions, subagent events, and plugin loading behavior. A skill may recommend a hook only when the target runtime supports the required capability; otherwise it must state the degradation and keep enforcement at the real owning boundary.

#### Plugins and agent packages

The common floor treats a plugin as a distribution container that may bundle skills and adjacent capabilities, not as a universal manifest. It covers component cohesion, least authority, dependency disclosure, install-time trust, update/version provenance, namespace collision, and independent disable/recovery. Claude Code plugins, OpenAI plugins, GitHub Copilot plugins, Cursor/Agent Plugins, Kiro Powers, Gemini CLI extensions, and Antigravity plugins are profiled as separate product contracts even when they share Agent Skills or Agent Plugins concepts.

Agent Plugins v1 is a portable package-floor topic in its own right: it standardizes a root manifest, Agent Skills, optional MCP configuration, confinement, versioning, and component-level failure isolation while leaving installation, distribution, enablement, permissions, sandboxing, and user experience to clients. Its portable core currently covers skills and MCP servers, not a universal hook or subagent manifest. Client extension namespaces and runtime-native packages therefore remain profile-specific. Authentication also remains client-managed; portable plugin material must not embed secrets or invent a cross-runtime credential field.

AgentBundle is a third, external delivery mechanism, not a runtime profile inside the portable pack. Maintainer documentation may map portable capabilities onto AgentBundle primitives and projections, but the corpus must remain understandable and useful when installed from another catalogue or copied directly into any Agent Skills-compatible runtime.

### D4 — AgentBundle and catalogue boundary

The repository wrapper around the portable pack necessarily contains catalogue metadata and tests. That wrapper is not the reusable doctrine.

| Portable pack content | External AgentBundle/catalogue ownership |
| --- | --- |
| Workflow intent and semantic steps | `packs/<pack>/` source layout |
| Agent Skills structure and activation principles | `pack.toml`, schema versions, allowed adapters |
| Capability questions for agents, hooks, and plugins | Primitive projection and frontmatter remapping |
| Runtime-neutral script and eval contracts | Catalogue lint/build/verify commands |
| Sourced, retrieval-dated runtime behavior profiles | Self-host synchronization and generated projections |
| Knowledge provenance and applicability | Pack version bumps, changelog, admission, publication |
| Graceful degradation when a capability is absent | Integration declaration syntax and adapter warnings |

Catalogue-curation continues to own assimilation, pack admission, OKF compilation, and catalogue governance. It should invoke or recommend the new workflows for skill craft instead of carrying its own parallel craft handbook. `compile-okf` remains in catalogue-curation because compilation is an AgentBundle catalogue mechanism; the new pack owns the knowledge that is compiled, not the compiler.

### D5 — Execution economics from local skill to CI fleet

The corpus adopts **execution economics** as the disciplined measurement of time, processes, filesystem work, memory, network use, cache behavior, contention, and failure amplification across five scopes:

| Scope | Representative questions |
| --- | --- |
| Skill script | Is process startup dominating useful work? Can a deterministic operation be batched or moved in-process without changing isolation or security? |
| Pack suite | Does collection match ownership? Are fixtures isolated? Does “one process per skill” preserve dependency or import boundaries that batching would erase? |
| Repository CI | What is the critical path? Which gates can split safely? Which checks may batch, and which must retain distinct environments? |
| Worktree | Are temporary files, caches, ports, state, and cleanup attributable to one worktree? Do concurrent runs collide? |
| Shared host/fleet | Are CPU, memory, browser workers, ports, and state locks admitted against real capacity? Can stale ownership be recovered safely? |

Optimization follows this sequence:

1. Capture a reproducible baseline and identify the dominant cost.
2. State the semantic boundary that must not change: environment, permissions, failure attribution, isolation, ordering, or output.
3. Choose the smallest optimization at the correct layer.
4. Test behavior preservation and failure paths, not only elapsed time.
5. Measure before/after under comparable load.
6. Record applicability limits, reversal conditions, and any new contention surface.

The repository's history supplies positive and negative patterns: collapsing tens of thousands of shell startups into one process, batching one repeated Git query, moving read-only transition guards in-process, splitting CI behind a stable aggregator, preserving manifest-isolated security scans, avoiding blind browser-worker increases, and eliminating duplicate composed-CI work. These lessons are detailed in the [execution-economics archaeology](0097-notes/execution-economics-archaeology.md).

For worktrees and managed sandboxes, the corpus must distinguish coordination from wishful isolation:

- Git worktrees share repository administration and refs; a Git worktree lock protects administrative pruning/moving, not arbitrary build or agent activity.
- A state lock is a transaction over read/decide/write, not merely an atomic final rename. Ownership tokens, liveness, stale recovery, and loss detection are part of the contract.
- Multiple agents sharing one filesystem need explicit file ownership or isolated worktrees; neither model context isolation nor a subagent label prevents write conflicts.
- Temporary roots, caches, ports, browser workers, and state directories need worktree identity and bounded cleanup.
- Machine-load detection is an admission signal, not permission to exceed policy or a substitute for hard concurrency caps.
- Managed permission profiles and exposed tools remain authoritative. Local configuration, hooks, skills, or subagents cannot bypass enterprise policy.

### D6 — Self-hosting and footprint migration

The repository should self-host the new pack before deleting duplicated guidance. Migration has four stages:

1. **Add:** ship the pack, compiled router, source provenance, and activation/behavior tests while existing guidance remains authoritative.
2. **Integrate:** declare optional work-loop and architect-design provider integrations; install the pack into this repository's self-hosted projections; verify absence/fallback behavior.
3. **Route and compare:** update maintainer and authoring guides to route reusable questions to the pack, then run task fixtures against old and new routes to demonstrate coverage and retrieval precision.
4. **Collapse:** remove duplicated explanatory practice only where parity evidence exists; retain repository facts, mechanical commands, policy, enforcement, and external adapter mechanics.

#### Guidance disposition

| Existing surface | Retain locally | Migrate to corpus | Candidate to retire after parity |
| --- | --- | --- | --- |
| Root `AGENTS.md` | Project overview, canonical-source routing, repository commands, scoped guidance, blessed security helpers | General advice on skill evaluation, scripts, orchestration, and execution economics when present | Duplicated procedural teaching that is not required every session |
| `AGENTS.local.md` | Checkout topology, enterprise/local constraints, release coupling, self-host facts, exact repository recovery commands | General worktree attribution, locks, machine admission, and optimization principles | Long explanations whose only local role becomes “invoke the installed reference” |
| `packs/AGENTS.md` and scoped pack guidance | `.apm` ownership, test placement, versioning, portability gates, self-host rules | General trigger, instruction-density, progressive-disclosure, script, eval, and orchestration craft | Duplicated checklists replaced by the installed author/review workflow |
| Maintainer/skill-author guides | AgentBundle commands, file locations, publication, repository policy | Skill framing, scripts, evals, runtime capability selection, optimization | Repeated handbook sections after links/routes and task fixtures are live |
| Catalogue-curation skills | Assimilation provenance, admission, compiler, manifest, publication | Craft analysis and remediation of the acquired skill | Inline craft rubric duplicated by the author/review workflows |
| Repository tooling | Machine-verifiable invariants, schemas, security checks, performance gates | Explanations and remediation rationale | Knowledge-parity linters whose duplicated taxonomy is no longer necessary |

“Collapse” means replace duplicated prose with a short repository-specific rule and an explicit semantic route. It does not mean remove always-on safety constraints, delete frozen history, weaken tests, or make an installed optional pack the only location of a rule required before activation.

#### Changed authoring journeys

The maintainer and public authoring guides should describe two connected but separate journeys.

**Create or update a skill:**

1. Invoke the author/update workflow.
2. Frame the job, activation boundary, authority, and required runtime capabilities.
3. Route to only the relevant corpus topics, including Python/pytest or TypeScript/Node.
4. Produce or update the portable skill and its tests/evals.
5. If this repository is the host, hand the result to external AgentBundle maintainer guidance for manifest, version, projection, self-host, and publication work.
6. Run the review/optimize workflow against observed behavior and costs.

**Create or update a pack:**

1. Use catalogue-owned pack proposal/admission guidance to establish the pack boundary.
2. Use the agent-skill-engineering workflows for every skill's craft and for cross-skill activation, script, eval, and execution topology.
3. Use runtime-profile topics only for claimed runtime extensions such as subagents, hooks, or plugins.
4. Return to catalogue-owned guidance for dependencies, integrations, adapter claims, versioning, projections, self-host, and publication.

The guides must not imply that installing AgentBundle is required to apply the portable skill-engineering practice.

### D7 — INI-009 and backlog disposition

[INI-009](../product/initiatives/ini-009-agent-skill-engineering.md) is the targeted delivery initiative for the new pack and the adaptation of this repository's existing footprint. The initiative begins at M0 with this Draft RFC; implementation work is not dispatchable until the RFC is accepted and follow-on artifacts are created.

Acceptance approves the following backlog **disposition policy**, not a state change. INI-009 must verify each item's current owner and state against its canonical backlog record, link the decisive implementation or resolution evidence, and obtain that owner's review before moving, narrowing, absorbing, or closing it. If that evidence contradicts this planning map, the canonical backlog owner wins and INI-009 records the variance.

| Backlog item | Disposition after acceptance | Reason |
| --- | --- | --- |
| `okf-index-title-interpolation-unescaped` | Prerequisite to corpus production; promote into the corpus/router foundation spec. | Generated indexes are a trust boundary. |
| `okf012-nondeterminism-guard-untested` | Prerequisite to corpus production; promote into the foundation spec. | The pack relies on deterministic repeat compilation. |
| `security-checklists-okf-router-regression` | Candidate to close only after its owner links the existing resolving change and verifies the regression test; otherwise keep open. Import the verified lesson into router tests. | The inventory indicates a resolution, but this RFC is not the authority for its state. |
| `codex-skill-description-budget` | Absorb as a measured runtime-profile and activation-eval work item. | Description budgets affect retrieval and activation precision. |
| `pre-existing-skill-spec-lint-warnings` | Keep open, cross-link as migration-baseline evidence, and narrow only after the new workflows remediate covered warnings. | It is broader than the new pack and currently non-blocking. |
| `skill-governance-inventory-gap` | Keep open as an external governance dependency; reference from the trust topic. | Per-skill install provenance belongs to distribution/governance, not portable content. |
| `pack-eval-coverage-rollout` and `pack-evals-converters-gate-consolidation` | Keep open; cross-link their measured lessons and avoid duplicating their runner work. | They own catalogue rollout and gate consolidation. |
| `pack-js-ci-workflow` and `sast-javascript-coverage` | Keep open; use them as the first TypeScript/Node and CI-security application cases. | They are repository implementation work, not corpus authoring. |
| `pytest-tmpdir-worktree-attribution` | Keep open; make it an application case for worktree attribution. | It changes repository tooling and needs separate acceptance. |
| `agentbundle-catalogue-test-command` | Keep open as an external AgentBundle mechanism; consume corpus contracts when designed. | The portable pack must not own the CLI. |
| `architect-okf-bundle-root-missing-license` | Keep separately owned by architect and require it before architect becomes the integration pilot. | It is a concrete pack-content defect, not a new-pack feature. |

No backlog item is closed, reassigned, or otherwise mutated merely because this RFC names it. Each move must preserve its original provenance and record the artifact, evidence, owner review, and date that satisfies it.

### D8 — Governance, provenance, and validation

The intake inventory may classify candidates as portable, language-specific, runtime-specific, catalogue-specific, or ordinary engineering. Catalogue-specific and unrelated ordinary-engineering candidates are routed out and are **not** compiled concepts. A narrowly scoped boundary concept may state what remains external, but it must not teach the external mechanism.

Each admitted compiled knowledge concept must carry:

- a stable semantic identifier and retrieval terms;
- classification as portable, language-specific, runtime-specific, security/authority, execution-economics, or an explicit external-boundary statement;
- source provenance, a per-source `retrieved_at` date, any exposed source version or last-updated date, and the concept's last verification date;
- applicability and known limits;
- confidence or maturity based on evidence;
- review owner and revalidation trigger;
- explicit authority: advisory knowledge, never an executable instruction.

Promotion into durable doctrine requires one of:

- a stable public contract supported by at least two relevant runtimes;
- repeated independent observed failures with the same mechanism;
- one severe, reproducible safety failure whose boundary is clear; or
- a controlled measurement with preserved semantics and repeatable benefit.

A stable single-ecosystem contract may support a language-specific topic when it comes from that ecosystem's authoritative documentation, is explicitly limited to that ecosystem and version range, and has a construction or behavior fixture. It cannot be generalized into the portable floor without the broader evidence above. Runtime profiles follow the same scoped exception and must be revalidated when their contract changes.

A single local preference may be recorded in research notes but must not be promoted as portable doctrine. `retrieved_at` records when the maintainer actually acquired material and is mandatory even when a page exposes its own update date; those dates answer different questions.

Security rules:

- Treat installed skills, compiled references, repository-provided skills, hooks, subagent definitions, and plugins as instruction or code supply-chain inputs.
- Escape and bound generated index metadata; prevent path traversal and unexpected links; compile with confinement and deterministic output.
- Do not let knowledge text grant tools, network, credentials, filesystem access, or permissions.
- Keep authentication and secret resolution outside model context. A skill may request a bounded capability, invoke a trusted tool that attaches credentials beyond the model boundary, or consume a redacted result; it must not ask the model to read, copy, persist, transform, or print raw credentials. The portable topic specifies this semantic separation without naming or requiring this repository's credential implementation.
- Hooks that enforce policy remain executable code under runtime and enterprise trust controls; corpus advice cannot claim enforcement.
- Subagents inherit or receive only the least authority needed, and parent workflows remain responsible for approvals and synthesis.
- A runtime profile must say when managed policy can narrow or disable local hooks, plugins, skills, or subagents.
- Candidate skills, scripts, hooks, subagent definitions, plugins, OKF, and external pages are untrusted data during intake and review. Read them through confined passive inspection; do not follow their instructions merely because they are being analyzed.
- Static inspection precedes execution. The workflows never automatically install, activate, or run candidate dependencies, scripts, hooks, plugins, or subagents. Execution requires explicit user approval in the active managed sandbox, declared network/dependency needs, least authority, no credentials unless the task separately authorizes a brokered path, and a bounded target.
- Promoted evidence is minimized and redacted before commit. Published concepts and fixtures use generic placeholders; exclude secrets, credentials, raw prompts/session logs, personal identifiers, usernames, absolute home paths, hostnames, private service names, and unrelated enterprise details. Sensitive raw research stays outside the published corpus.

## Options considered

| Option | Advantages | Drawbacks | Decision |
| --- | --- | --- | --- |
| Portable pack plus same-pack OKF corpus | User-facing workflow, reusable across loops, precise retrieval, clear owner | More initial integration and migration work | **Selected** |
| Work-loop reference library only | Smaller first change | Couples knowledge to core, lacks an authoring product, encourages generic retrieval in work-loop | Rejected |
| Expand catalogue-curation only | Reuses an existing maintainer pack | Makes portable practice catalogue-specific and unavailable to ordinary skill authors | Rejected |
| One broad “agent engineering” workflow | Simple discovery | Weak trigger precision, handbook-sized context, conflates authoring/review/CI/architecture | Rejected |
| Separate runtime-specific packs | Exact local mechanics | Duplicates the portable floor and fragments evidence across eight initial enterprise surfaces | Rejected for v1; use profiles inside one corpus |
| Runtime OKF search service | Potentially flexible retrieval | New authority, availability, security, and cross-pack dependency surface contrary to ADR-0093 | Rejected |
| Do nothing | No migration cost | Duplication, retrieval debt, and unowned execution lessons continue growing | Rejected |

## Risks & what would make this wrong

| Failure mode or falsifiable assumption | Signal that makes the proposal wrong | Mitigation or reversal |
| --- | --- | --- |
| The corpus becomes a generic engineering encyclopedia. | Any admitted topic lacks a named direct skill, eval, agent-loop, hook, or plugin use; or more than 5% of a fixed 40-prompt generic-engineering negative set returns topic bodies. | Reject or move the topic to its natural owner; tighten admission and negative routing fixtures. |
| Retrieval is less precise than current guides. | Median routed context grows, task completion falls, or authors repeatedly open the whole corpus. | Split concepts, improve routing terms, or retain the old guide section; the generated router is reversible. |
| Runtime profiles go stale. | Contract checks or user reports contradict a profile after a runtime release. | Date and source every claim, add scheduled/manual revalidation, mark affected claims `stale`, and roll the profile to `needs-revalidation` rather than guessing. |
| “Common floor” hides capability loss. | A projected workflow silently drops isolation, permissions, hooks, skill availability, or plugin components. | Require capability-by-capability support claims and explicit degradation; keep adapter tests external. |
| The provider router creates cross-pack authority. | Consumers start treating returned text as an instruction to mutate or bypass their own gates. | Keep the router read-only, return topic IDs, and preserve consumer authority in integration contracts. |
| Self-host collapse removes essential always-on guidance. | A cold agent misses a repository safety rule before the pack activates. | Retain repository-specific safety and commands; delete only after task fixtures prove routed parity. |
| Optimization changes semantics. | Faster runs merge environments, weaken isolation, hide failures, or increase flakiness. | Require semantic-boundary statements, behavior tests, comparable measurements, and reversal conditions. |
| Parallel agents overload or corrupt shared resources. | Conflicting writes, duplicate test runs, lock theft, CPU/memory saturation, or stranded temp state. | Default to read-heavy delegation, explicit write ownership, caps, worktree identity, durable locks, and admission checks. |
| Generated knowledge becomes an injection vector. | Untrusted metadata changes links, routing, or instructions in compiler-owned output. | Close the known interpolation defect before production, confine compilation, and security-review fixtures. |
| AgentBundle leaks into the portable layer. | A workflow cannot be understood or executed without `pack.toml` or AgentBundle commands. | Fail portability review; move the material to catalogue maintainer guidance. |

The largest honest drawback is maintenance: a useful runtime-profile corpus creates an obligation to track change. If no owner can revalidate the eight initial enterprise surfaces, M1 may ship the portable floor, but M2 remains incomplete; affected claims and profiles must use the lifecycle and roll-up states above rather than publishing false currency.

## Evidence & prior art

The supporting [practice inventory](0097-notes/practice-inventory.md) classifies the current repository knowledge surface and the [execution-economics archaeology](0097-notes/execution-economics-archaeology.md) reconstructs the optimization rationale from commits.

External contracts support the main boundaries:

- The [Agent Skills specification](https://agentskills.io/specification) defines a portable `SKILL.md`-based substrate, while the [script guidance](https://agentskills.io/skill-creation/using-scripts) treats scripts as deterministic helpers. GitHub Copilot and Gemini CLI both document Agent Skills support, strengthening the portable-floor case.
- Anthropic's [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) documents progressive disclosure and runtime-dependent execution constraints. Claude Code's [extension overview](https://code.claude.com/docs/en/features-overview), [subagent reference](https://code.claude.com/docs/en/sub-agents), [hooks reference](https://code.claude.com/docs/en/hooks), and [plugin reference](https://code.claude.com/docs/en/plugins-reference) show that skills, subagents, hooks, and plugins compose but have distinct context, trust, and packaging behavior.
- OpenAI's [Codex customization overview](https://developers.openai.com/codex/concepts/customization), [subagent reference](https://developers.openai.com/codex/multi-agent), [advanced hook configuration](https://developers.openai.com/codex/config-advanced#hooks), and [plugin packaging guide](https://developers.openai.com/codex/plugins/build) document a different composition and distribution contract, including explicit skill configuration for custom agents, inherited sandbox controls, and separately trusted plugin hooks.
- GitHub's [customization comparison](https://docs.github.com/en/copilot/reference/customization-cheat-sheet), [custom-agent reference](https://docs.github.com/en/copilot/reference/custom-agents-configuration), and [hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference) show material differences across Copilot CLI, cloud agent, and IDE surfaces, including enterprise policy hooks and cloud-only execution constraints.
- Cursor's [Agent Skills](https://cursor.com/docs/skills), [customization overview](https://cursor.com/docs/customize-cursor), [hooks](https://cursor.com/docs/hooks), and [plugin reference](https://cursor.com/docs/reference/plugins) document progressive skill loading, explicit-only activation, persistent custom modes, user/workspace/team scopes, subagents, local/cloud/managed hook differences, and both portable Agent Plugins and Cursor-specific plugin components.
- The [Agent Plugins 1.0 specification](https://agent-plugins.org/specification), [authoring guide](https://agent-plugins.org/plugin-authors/build-an-agent-plugin), and [MCP guidance](https://agent-plugins.org/plugin-authors/mcp-servers) define a vendor-neutral skills/MCP package floor, confinement and failure isolation, and client-managed installation, permissions, and authentication. They support packaging knowledge-provider skills without turning client-specific hooks, policy, or credential handling into portable claims.
- Kiro's [Agent Skills](https://kiro.dev/docs/skills/), [custom-agent configuration](https://kiro.dev/docs/custom-agents/configuration-reference/), [hooks](https://kiro.dev/docs/hooks/), and [Powers](https://kiro.dev/docs/powers/) document shared IDE/CLI concepts alongside surface-specific fields and packaging behavior; IDE and CLI therefore receive separate profiles.
- Gemini CLI's [skill management](https://geminicli.com/docs/cli/using-agent-skills/), [extension reference](https://geminicli.com/docs/extensions/reference/), and [hooks reference](https://geminicli.com/docs/hooks/reference/) document discovery precedence, extension-bundled components, preview subagents, policy contributions, environment sanitization, and strict hook output contracts.
- Google Antigravity's [skills](https://www.antigravity.google/docs/ide/skills/), [subagents](https://www.antigravity.google/docs/subagents), and [hooks](https://www.antigravity.google/docs/ide/hooks) document another distinct skill path, asynchronous-agent, worktree, permission-inheritance, nesting, and event contract.
- [pytest good practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html), [pytest fixture guidance](https://docs.pytest.org/en/stable/how-to/fixtures.html), and [pytest-xdist distribution modes](https://pytest-xdist.readthedocs.io/en/stable/distribution.html) support explicit test layout, isolation, and chosen parallel semantics.
- [Node package/module rules](https://nodejs.org/api/packages.html), [child process behavior](https://nodejs.org/api/child_process.html), [`npm ci`](https://docs.npmjs.com/cli/commands/npm-ci/), and [Playwright parallelism](https://playwright.dev/docs/test-parallel) support a separate TypeScript/Node execution topic rather than Python-shaped universal guidance.
- [Git worktree](https://git-scm.com/docs/git-worktree.html), [POSIX file locks](https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap03.html), [GNU Make job slots](https://www.gnu.org/software/make/manual/html_node/Job-Slots.html), and [GitHub Actions concurrency](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency) distinguish administrative locks, application locks, cooperative capacity, and CI admission.
- GitHub's [job dependency model](https://docs.github.com/en/enterprise-cloud@latest/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs) and [dependency caching model](https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching) support critical-path and cache-key reasoning without prescribing repository-specific workflows.

All external sources in this RFC and its notes were retrieved on **2026-08-26** unless an individual citation says otherwise. Repository prior art includes the generated `security-checklists-reference` router, architect's same-pack OKF bundle, optional `pack.integrations`, the negative lesson from a router regression, and the negative maintenance cost of `tools/lint-knowledge-surface-parity.py`, which exists because one taxonomy was copied instead of owned once and routed.

## Experiment / validation

Delivery uses four validation gates.

Each fixture is versioned with its expected result before the implementation under test runs. Automated checks enforce construction and deterministic behavior; an independent reviewer evaluates task-quality judgments against the fixture checklist. A changed expectation is a reviewed fixture change, not an implementation-time exception.

### 1. Corpus and router

- **Hypothesis:** A bounded router selects the correct concept set without loading the corpus.
- **M1 measure:** A versioned set of at least 20 foundation prompts spanning skill framing, author/update, review, triggers, progressive references, deterministic scripts, security/authority, and near misses. Each fixture declares one exact expected topic set and, only where two decompositions are intentionally equivalent, one pre-approved alternative set. Precision and recall are computed against the declared set; an alternative counts as exact for that fixture.
- **M1 success:** At least 90% of fixtures select their exact or pre-approved alternative set, at least 90% return no more than three concepts, and two clean compiles produce byte-identical output. To prove runtime independence from raw OKF, the test stages only the built install tree in a fresh temporary root, asserts no authoring-source file or path is present, runs every router fixture with the source checkout unavailable, and fails on any attempted open outside the staged tree or declared temporary output. Every hostile metadata fixture must produce a non-zero compile result or documented refusal status, a stable diagnostic, no output outside the declared build directory, no mutation of source input, and no unsafe path or link in retained output.
- **M2 expanded measure:** Expand the versioned set to at least 40 prompts by adding Python/pytest, TypeScript/Node, skill/evaluation CI, execution economics, worktrees/shared hosts, subagents, hooks, plugins, runtime profiles, knowledge-provider/package modes, usability patterns, and their near misses.
- **M2 expanded success:** The expanded set meets the same precision, topic-count, confinement, determinism, and hostile-input thresholds as M1, and unavailable-mode fixtures prove that M2-only modes were not advertised by the M1 build.

### 2. Workflow behavior

- **Hypothesis:** Two workflows cover the observed practice inventory without becoming generic.
- **M1 measure:** Four versioned foundation fixtures—new skill, skill update, activation failure, and deterministic script failure—plus negative activation fixtures. Each declares required output fields, applicable foundation checklist items, and seeded defects before execution.
- **M1 success:** Construction checks confirm every declared field and artifact; an independent reviewer confirms every applicable checklist item; every seeded portability, authority, or script-contract defect is reported; and no negative activation fixture selects either user-facing workflow.
- **M2 expanded measure:** At least eleven versioned representative task fixtures: the four foundation cases plus pytest suite, Node/browser suite, subagent composition, hook/plugin design, cold-start workspace orientation, cross-session resumption, and progressive result presentation. Each fixture declares applicable pattern identifiers and expanded checklist items. A repository census additionally maps every authored pack skill to one or more pattern families or a reviewed exception.
- **M2 expanded success:** Every expanded fixture passes construction and independent-review checks; every seeded measurement, composition, orientation, or presentation defect is reported; and every census entry resolves to an existing pattern topic or reviewed exception with an owner and rationale.

### 3. Runtime profiles and degradation

- **Hypothesis:** Capability-keyed profiles accurately describe the eight initial enterprise runtime surfaces without leaking one into the common floor.
- **Measure:** A claim ledger for all eight profiles covering skill visibility, subagent context, permissions, isolation, hook trust/events, and plugin components. Every package format covered by `runtime-package` also requires rows and a reproducible fixture or bounded manual probe for scope/precedence, namespace and collision behavior, source provenance or integrity verification, install/update/disable/uninstall recovery, managed policy, and authentication/secret handling. Each claim names its first-party source, retrieval and verification dates, capability-claim state, and evidence record.
- **Success:** Every operative support claim is `verified`; `experimental`, `stale`, and `unavailable` claims produce the lifecycle-table response and cannot be presented as support. A package recommendation is withheld unless all package-lifecycle rows are present and current, and no test may leave hooks, executable components, permissions, writable state, or shadowing user/team entries after disable or uninstall. External adapter projection tests pass independently. M2 additionally requires all eight profile documents to be `complete-current`; an honestly unavailable capability does not fail that roll-up, while a stale or missing required row does.

### 4. Self-host footprint

- **Hypothesis:** Installed routing lets the repository shorten duplicated guidance without losing task success.
- **Measure:** Before/after line and duplication inventory plus cold-agent fixtures for maintainer setup, skill authoring, pack authoring, CI optimization, worktree conflict, and runtime-extension selection. Before migration, each fixture records a fixed correctness checklist, baseline files opened, bytes loaded, always-loaded guidance lines, and expected error severities. A `critical` error is predeclared as omitting or contradicting an always-on safety constraint, assigning authority to the wrong owner, recommending an unsafe command, or preventing completion of the fixture's primary task; all other fixture-specific severities are also declared before the run.
- **Success:** Every post-migration fixture satisfies all baseline checklist items with no new predeclared critical error; always-loaded guidance lines decrease; no executable enforcement or repository fact moves from its owner; and the median bytes loaded across the fixed fixtures is lower than the baseline handbook path.

The M1 slices of Gates 1 and 2 block the M1 pack release. The expanded M2 slices of Gates 1 and 2 plus Gate 3 block M2; a failing profile cannot be `verified`, and M2 remains incomplete until the eight-profile condition passes, without retroactively blocking the portable M1 release. Gate 4 blocks only the affected guidance deletion or footprint collapse. A failing optional consumer integration may remain disabled without blocking the provider pack, but its integration cannot ship or be used as parity evidence. No failed gate permits deletion of the guidance or fallback it was meant to replace.

## Open questions

| Question | Recommended default | Owner | Decide by |
| --- | --- | --- | --- |
| Which product versions form the initial verified profile baseline? | Pin the latest available Claude Code, Codex, Copilot, Cursor, Kiro IDE, Kiro CLI, Gemini CLI, and Antigravity versions when the profile spec begins; record exact versions and retrieval dates without promising indefinite compatibility. | INI-009 runtime-profile spec owner | Before M2 implementation |
| Which external repository should provide the portability pilot? | Use one non-AgentBundle catalogue with at least one TypeScript/Node skill and no repository-specific integration assumptions. | INI-009 owner | Before M4 closeout |

## Follow-on artifacts

If this RFC is accepted, delivery proceeds through the following post-acceptance artifacts and gates. They are not prerequisites to accepting this RFC; each is required before its affected implementation or migration milestone. The already-created INI-009 owns their sequence and remains non-dispatchable until the RFC is accepted.

1. **ADR:** Record the provider-mediated, same-pack compiled knowledge ownership pattern; clarify that it does not authorize direct cross-pack raw OKF resolution or a runtime loader.
2. **Spec — foundation:** Create the portable pack, two workflows, reference router, OKF source, compiler security prerequisites, activation/behavior evals, and external AgentBundle wrapper.
3. **Spec — corpus:** Populate portable foundations, Python/pytest, TypeScript/Node, eval, execution-economics, worktree/shared-host, security, and evidence-maintenance topics.
4. **Spec — runtime composition profiles:** Add skills-plus-subagents, hooks, and plugins common-floor topics and sourced, retrieval-dated profiles for Claude Code, Codex, GitHub Copilot, Cursor, Kiro IDE, Kiro CLI, Gemini CLI, and Google Antigravity, with capability and degradation tests.
5. **Spec — consumer integrations:** Add optional work-loop and architect-design provider integrations and absence/fallback tests; permit later consumers only through the same contract.
6. **Spec — self-host and footprint adaptation:** Install the pack here; update `AGENTS.local.md`, scoped pack guidance, catalogue-curation, maintainer/skill-author guides, tooling explanations, and authoring journeys using the staged parity process.
7. **Spec — pilot and closeout:** Run the non-AgentBundle pilot, measure retrieval and footprint outcomes, disposition the named backlog items, and publish maintenance ownership.

Tracking already exists under [INI-009](../product/initiatives/ini-009-agent-skill-engineering.md). Add canonical spec entries to `workspace.toml` only after each spec exists and is approved.

The [planned architecture document](../architecture/agent-skill-engineering.md) is the cross-spec target view. Each delivery spec must update it with implemented names, paths, dependency edges, and verification evidence for its slice. It remains `PLANNED` until every section it describes is implemented and verified; only then does it become `CURRENT`. This RFC remains the decision record rather than the living operational reference.
