# Agent skill engineering practice inventory

> Discipline: applied (repository inventory plus practitioner-pattern survey)
>
> External sources retrieved: 2026-08-26

This note classifies the knowledge surface that informed RFC-0097. It is evidence for the boundary, not the future corpus itself.

## Classification rule

| Class | Admission test | Destination |
| --- | --- | --- |
| Universal agent-skill practice | Useful without naming a runtime, repository, or catalogue tool | Portable corpus topic |
| Runtime-specific | Depends on a documented Claude, Codex, or other runtime contract | Dated runtime profile |
| Catalogue-specific | Depends on AgentBundle, this catalogue's layout, governance, or publication process | Existing catalogue/tool/guide owner |
| Ordinary Python/pytest or TypeScript/Node engineering | General language technique with no direct skill/eval use | Excluded; admit only the task-shaped subset |

## Inventory

| Practice | Classification | Evidence surface | Proposed treatment |
| --- | --- | --- | --- |
| Skill job framing and trigger/near-miss quality | Universal | Agent Skills spec; activation evals; skill authoring guides | Portable foundations and eval topics |
| Instruction density and progressive disclosure | Universal | Agent Skills and Claude skill docs; current skill warnings | Portable foundations topic |
| Deterministic scripts, dependency detection, exit contracts | Universal with language profiles | Skill scripts; catalogue tests; Agent Skills script guidance | Common contract plus Python and TypeScript/Node topics |
| Activation evals and behavioral checks | Universal with runner-specific realization | RFC-0037, pack eval manifests, fixtures | Portable evaluation topics; runner remains external |
| Fixture ownership and isolated test collection | Universal principle; pytest-specific mechanism | Pack test-boundary specs and pytest docs | Shared principle plus Python/pytest topic |
| Node module/lockfile/test-worker behavior | TypeScript/Node-specific | Converters scripts, CI backlog, Node/npm/Playwright docs | Dedicated TypeScript/Node topic |
| Process-startup, filesystem, and cache measurement | Universal when tied to skills/evals | Recent performance commits and specs | Execution-economics topics |
| CI critical-path splitting and safe batching | Universal design principles; repository implementation external | CI specs, GitHub Actions docs | Pack/CI topic for loops and reviewers |
| Worktree attribution, state locks, and machine admission | Universal operational pattern with runtime/tool realization | Work-loop specs, Git docs, POSIX locks, Make job slots | Worktree/shared-host topic |
| Skills composed with subagents | Portable capability questions; runtime-specific behavior | Claude, Codex, Copilot, Cursor, Kiro, Gemini CLI, and Antigravity first-party docs | Common-floor topic plus surface-specific profiles |
| Hooks as deterministic enforcement | Portable distinction; runtime-specific events/trust | First-party hook docs; adapter audits | Common-floor topic plus runtime profiles |
| Plugins as packaging containers | Portable cohesion/trust questions; runtime-specific manifests | Claude/OpenAI plugins, Copilot and Cursor plugins, Kiro Powers, Gemini extensions, Antigravity plugins | Common-floor topic plus runtime profiles |
| Authentication outside model context | Universal security boundary; implementation-specific realization | Repository integration and credential-resolution patterns | Portable semantic rule; implementation and product names remain external |
| Pack manifests, projection, adapter mappings, self-host, versions | Catalogue-specific | AgentBundle architecture, adapter contract, guides | Remain external to portable pack |
| OKF compilation commands and validation codes | Catalogue-specific mechanism | compile-okf and AgentBundle compiler | Remain catalogue-curation/tooling |
| Knowledge topology, provenance, applicability, retrieval terms | Universal knowledge engineering | ADR-0093, RFC-0087, OKF pilot | Same-pack governed corpus |

## Pack skill-pattern census

A local scan on 2026-08-26 covered all 131 authored `packs/*/.apm/skills/*/SKILL.md` files, including hidden `.apm` source. The future corpus should retain a machine-readable mapping from every skill to one or more pattern families, while humans review exceptions and exemplar quality. The grouping below is the initial pattern vocabulary, not a claim that similarly grouped skills are interchangeable.

| Pattern family | Evidence in current packs | Corpus treatment |
| --- | --- | --- |
| Inline procedure | Focused contract, strategy, and engineering skills | Small-skill fit and density rules |
| Progressive references | Contract, design, frontend, research, and product skills with task-shaped `references/` | Reference topology, load triggers, and context budgets |
| Explicit multi-mode | `work-loop`, `architect-assess`, `architect-diagram`, `author-product-docs`, `desk-research`, `ai-adoption-report` | Exclusive, cumulative, and orthogonal mode semantics |
| Deterministic script-backed | Converters, intake, status, governance, Jira/Linear/GitHub/Figma skills | Dependency, I/O, exit, isolation, and test contracts |
| Artifact/template producer | Spec/RFC/ADR, product-engineering, experience-design, conversion skills | Typed output, templates, destination, validation, overwrite behavior |
| Router/intake classifier | `work-intake`, brief-intake skills, generated reference routers | Deterministic versus semantic routing, bounded handoff, fallback |
| Composed workflow/family | `discovery-loop`, architect family, desk-research project lifecycle | Child ownership, progressive handoff, stop points, synthesis |
| State/status/lifecycle | `workspace-status`, work-loop state, refresh/status families | Read/write authority, transition guards, recovery, observability |
| Orientation/read model | `workspace-status`, `experience-status`, `rfc-status`, `fe-status`, research project status | Cold-start scope, bounded scanning, status-first summary, blockers, safe next action |
| Progressive presentation | Status renderers, reports, diagrams, artifact producers, machine-readable sidecars | Representation choice, information hierarchy, detail-on-demand, actionability |
| Workspace context/resumption | Work intake/status, design and research threads, loop receipts and state | Authoritative scope, session handoff, continuity without replay |
| External integration | Atlassian, GitHub, Linear, Figma, credential setup | Contract acquisition, context-isolated authentication, redaction, failure |
| Inert depth library | `operational-safety`, `security-checklists`, architecture lenses | Non-self-discovery, matched-module loading, consumer-owned authority |
| OKF knowledge provider | Architecture lenses, security checklists, cost-engineering pilot | Build-time compilation, generated index, router/search, provenance |
| Procedure/provider handoff | Security workflow plus generated security reference; architect consumers plus lenses | Authored workflow authority with generated progressive depth |
| Compatibility/deprecation | `new-guide` forwarding to `author-product-docs` | Trigger continuity, sunset, and doctrine deduplication |
| Runtime/user-profile package | Pack plugin projections plus runtime plugin/extension contracts | Cohesion, scope/precedence, versioning, policy, update/uninstall; exact mechanics stay profiled or external |

The most reusable packaging pattern is a governed knowledge provider: OKF is compiled into ordinary provider-owned references; a generated retrieval/router/search skill selects bounded topics; an optional authored workflow keeps mutation authority; and a runtime-supported plugin or extension can distribute the cohesive set. Search is limited to compiled same-pack content and returns topic identifiers and provenance. Packaging user-profile skills is a runtime-specific realization of the same distribution concern, so profile scope, precedence, conflicts, update, and uninstall behavior must be verified before recommending it.

The author/update workflow should expose a shallow `frame` mode and progressively deeper `create`, `update`, `knowledge-provider`, and `runtime-package` modes. It loads the compact pattern index first, then only selected pattern and usability topics. A mode is a workflow contract; a pattern is a construction choice within that mode. Keeping those axes separate avoids one public skill per pattern and prevents the authoring skill from loading the complete census.

## Runtime composition deltas

The initial corpus must not present this table as a permanent support guarantee. It is a source map for the profiles and must be reverified during implementation. Every resulting source record needs both the page's own version/update date when available and `retrieved_at: 2026-08-26` (or the later date on which it is reacquired).

| Surface | Initial facts to reacquire and test | Why it is not the common floor |
| --- | --- | --- |
| Claude Code | Skill preload/invocation, fresh child context, worktree isolation, no nested subagents, component hooks, plugin-agent field restrictions | Claude-specific frontmatter, tool, and plugin rules |
| Codex | Skill config inheritance/overrides, agent threads, live sandbox/approval inheritance, concurrency, plugin-hook trust | Codex configuration layers and orchestration controls |
| GitHub Copilot | Skill paths, custom agents, isolated subagents, hook policy/user/project/plugin tiers, cloud-agent sandbox/event subset | CLI, cloud agent, and IDE support differ |
| Cursor | Skill discovery and explicit-only invocation, persistent custom modes, subagents, user/workspace/team scope, local/cloud hooks, Agent Plugins and Cursor Plugins | IDE, CLI, cloud, managed, and two plugin-format behaviors differ |
| Kiro IDE | Skill discovery, custom-agent resource inheritance, IDE hook behavior, permissions, Powers | IDE and CLI share concepts but not every agent hook or packaging field |
| Kiro CLI | `skill://` resources, subagents, CLI-only embedded agent hooks, headless mode, Powers version support | CLI execution and configuration scopes differ from IDE |
| Gemini CLI | Skill precedence, preview subagents, extension components, policy tier, sanitized environment, strict JSON hook output | Gemini extension and hook contracts are product-specific |
| Google Antigravity | `.agents` skill/agent paths, clean child context, inherit/branch/share workspace modes, inherited safety scopes, nesting limit, hook events, plugins | Antigravity orchestration and workspace semantics are product-specific |

Primary sources:

- [Agent Plugins specification](https://agent-plugins.org/specification)
- [Build an Agent Plugin](https://agent-plugins.org/plugin-authors/build-an-agent-plugin)
- [Agent Plugins MCP servers](https://agent-plugins.org/plugin-authors/mcp-servers)
- [Claude Code extension overview](https://code.claude.com/docs/en/features-overview)
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code hooks](https://code.claude.com/docs/en/hooks)
- [Claude Code plugins](https://code.claude.com/docs/en/plugins-reference)
- [Codex customization](https://developers.openai.com/codex/concepts/customization)
- [Codex subagents](https://developers.openai.com/codex/multi-agent)
- [Codex advanced configuration](https://developers.openai.com/codex/config-advanced#hooks)
- [OpenAI plugin packaging](https://developers.openai.com/codex/plugins/build)
- [GitHub Copilot customization](https://docs.github.com/en/copilot/reference/customization-cheat-sheet)
- [GitHub Copilot custom agents](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [GitHub Copilot hooks](https://docs.github.com/en/copilot/reference/hooks-reference)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [Cursor customization](https://cursor.com/docs/customize-cursor)
- [Cursor hooks](https://cursor.com/docs/hooks)
- [Cursor plugins](https://cursor.com/docs/reference/plugins)
- [Kiro Agent Skills](https://kiro.dev/docs/skills/)
- [Kiro custom agents](https://kiro.dev/docs/custom-agents/configuration-reference/)
- [Kiro hooks](https://kiro.dev/docs/hooks/)
- [Kiro Powers](https://kiro.dev/docs/powers/)
- [Gemini CLI skills](https://geminicli.com/docs/cli/using-agent-skills/)
- [Gemini CLI extensions](https://geminicli.com/docs/extensions/reference/)
- [Gemini CLI hooks](https://geminicli.com/docs/hooks/reference/)
- [Google Antigravity skills](https://www.antigravity.google/docs/ide/skills/)
- [Google Antigravity subagents](https://www.antigravity.google/docs/subagents)
- [Google Antigravity hooks](https://www.antigravity.google/docs/ide/hooks)

## Existing footprint

### Catalogue-curation

`assimilate-primitive` currently carries reusable craft analysis alongside catalogue provenance and admission. The craft portion should route to the author/update and review/optimize workflows; acquisition, licensing, provenance, admission, and catalogue placement stay. `compile-okf` remains because it is an AgentBundle build mechanism. The compiler implementation and tests do not move into the new pack.

### Repository tooling

Mechanical enforcement stays with its owning tool. Examples include catalogue confinement, guide format checks, adapter projection tests, activation runners, and state-lock code. Explanatory taxonomies may shrink after the corpus is authoritative. `tools/lint-knowledge-surface-parity.py` is negative prior art: copied knowledge creates a bespoke parity obligation.

### Guides and always-loaded guidance

The root and scoped `AGENTS.md` files should retain facts that must be present before any skill activates: project ownership, commands, repository policy, security helpers, and scoped routing. General craft, execution-economics explanations, and reusable checklists can move behind the installed router. `AGENTS.local.md` keeps repository and enterprise facts, while portable worktree/locking/machine-admission reasoning moves to the corpus.

Maintainer and author guides become journeys with a seam:

1. portable skill engineering through the new workflows;
2. external catalogue packaging and publication through AgentBundle guidance.

## Candidate v1 boundary

The inventory supports two user-facing workflows, not a larger family. Corpus breadth does not justify separate public skills for scripts, evals, CI, orchestration, hooks, or plugins: those are progressively disclosed knowledge topics and may be consumed by other loops. A third public workflow should be added only after activation evidence shows a distinct user job that the two-workflow split cannot route precisely.

## Known limits

- Runtime documentation changes quickly; every source needs a retrieval date, and every profile needs a verification date and stale-state behavior.
- The repository evidence is unusually rich in Python and catalogue CI. The TypeScript/Node topic needs a real external or first-party pilot before being called mature.
- The inventory proves that duplicated knowledge exists; it does not prove which prose can be deleted. Task-level parity experiments own that decision.
