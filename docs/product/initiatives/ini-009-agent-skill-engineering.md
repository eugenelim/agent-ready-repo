# Initiative: Agent Skill Engineering

- **ID:** `INI-009`
- **Name:** Agent Skill Engineering
- **Status:** Active
- **Appetite:** 1–2 quarters
- **Owner:** Repository maintainers
- **workspace.toml section:** `["ini-009"]` in `workspace.toml`

## Outcome

Authors and agent loops can use one portable, progressively disclosed engineering knowledge system to create, evaluate, review, and optimize agent skills across Python and TypeScript/Node contexts, including safe composition with subagents, hooks, plugins, skill/evaluation CI, worktrees, and shared hosts. This repository self-hosts that capability and measurably reduces duplicated guidance without losing repository-specific policy, enforcement, or external AgentBundle adapter mechanics.

## Scope

**In scope:**

- A portable `agent-skill-engineering` pack with author/update and review/optimize workflows.
- A governed same-pack OKF corpus and non-self-discovering provider router.
- Portable capability floors plus retrieval-dated profiles for Claude Code, Codex, GitHub Copilot, Cursor, Kiro IDE, Kiro CLI, Gemini CLI, and Google Antigravity.
- Python/pytest and TypeScript/Node script and evaluation topics.
- A census-backed catalogue of current pack skill patterns, including knowledge providers, progressive authoring modes, orientation/workspace resumption, and result-presentation usability.
- Skill-, pack-, skill/evaluation-CI-, worktree-, and shared-host execution economics.
- Runtime-neutral security including untrusted-input handling, least authority, and authentication/secret resolution outside model context without coupling portable guidance to the repository's credential implementation.
- Optional work-loop and architect-design integrations, with a path for later explicit consumers.
- Self-host installation and evidence-gated reduction of duplicated catalogue-curation, tooling explanation, `AGENTS.local.md`, scoped guidance, and maintainer/author guides.
- Backlog disposition and an external non-AgentBundle portability pilot.

**Non-goals / out of scope:**

- Moving AgentBundle manifests, adapters, projection, self-host commands, versions, admission, or publication into portable pack content.
- A generic CI, pytest, Node, Git, or developer-productivity pack.
- Runtime OKF lookup, direct cross-pack raw OKF resolution, hosted retrieval, or executable knowledge.
- Treating Claude or Codex extension behavior as universal.
- Removing mechanical enforcement or always-loaded repository safety rules.

## Capability areas

| Capability | Description | Status |
| --- | --- | --- |
| Portable workflows | Author/update and review/optimize agent skills with task-shaped retrieval | Shaping |
| Governed knowledge | Same-pack OKF source, secure deterministic compilation, and bounded provider routing | Shaping |
| Languages and evaluation | Shared script/eval contracts with separate Python/pytest and TypeScript/Node depth | Shaping |
| Execution economics | Measurement-led optimization across local scripts, packs, skill/evaluation CI, worktrees, and shared hosts | Shaping |
| Security and authentication isolation | Treat inputs as untrusted, preserve least authority, and keep raw credentials outside model context | Shaping |
| Runtime composition | Common floors and retrieval-dated enterprise runtime profiles for subagents, hooks, and plugins | Shaping |
| Consumer integration | Optional work-loop, architect-design, and future provider-mediated retrieval | Shaping |
| Repository adaptation | Self-host, guide and guidance migration, catalogue-curation reduction, tooling rationale consolidation | Shaping |
| Evidence and maintenance | Promotion thresholds, provenance, revalidation, pilots, and backlog closeout | Shaping |

## Milestone sequence

| Milestone | Scope summary | Target quarter |
| --- | --- | --- |
| M0 | Accept RFC-0097, record the provider-mediated knowledge ADR, and approve delivery specs | Q3 2026 |
| M1 | Ship portable `frame`/`create`/`update` modes, secure compiled router, foundational corpus, authentication-isolation guidance, and foundation activation/behavior evals | Q3 2026 |
| M2 | Expand router/evals; activate `knowledge-provider` and `runtime-package`; add Python/pytest, TypeScript/Node, execution-economics, skill-pattern/usability topics, subagent, hook, plugin, and eight enterprise runtime profiles | Q3–Q4 2026 |
| M3 | Integrate work-loop and architect-design; self-host the pack in this repository | Q4 2026 |
| M4 | Update author/maintainer journeys and collapse duplicated guidance through measured parity gates | Q4 2026 |
| M5 | Complete the external portability pilot, disposition backlog items, publish maintenance ownership, verify every planned architecture section, change its status to `CURRENT` with the verifying commit, and close the initiative | Q4 2026 |

## Delivery rules

- RFC-0097 is the accepted governing decision. Implementation remains non-dispatchable until its canonical specs are approved and registered under this initiative.
- Every implementation slice gets a canonical spec before it is added to `["ini-009".work]`.
- Corpus content and AgentBundle delivery mechanics are reviewed as separate boundaries even when one spec touches both.
- Portable authentication guidance defines context isolation and bounded capability use; it does not name or depend on this repository's credential implementation.
- Shipping a runtime knowledge profile does not claim AgentBundle projection support for that runtime; adapter changes remain separately governed.
- Footprint deletion is gated by cold-agent task parity and retrieval measurements; a failed gate retains the old owner.
- Runtime claims carry a first-party source, date retrieved, exposed source version/update date, and verification date. Stale capability claims roll the profile to `needs-revalidation`; operative guidance is withheld rather than guessed.
- The planned architecture remains `PLANNED` until every described section is implemented and verified; M5 records the verifying commit when promoting it to `CURRENT`.

## Links

- `workspace.toml` initiative section: `["ini-009"]`
- Governing RFC: [RFC-0097](../../rfc/0097-agent-skill-engineering.md)
- Planned architecture: [agent skill engineering](../../architecture/agent-skill-engineering.md)
- Evidence: [practice inventory](../../rfc/0097-notes/practice-inventory.md), [execution-economics archaeology](../../rfc/0097-notes/execution-economics-archaeology.md)
- Parent: none
- Briefs: none; RFC-0097 is the approved shaping input
- Shaping artifacts: RFC-0097 and its notes
