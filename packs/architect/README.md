# architect

Three things your agent can do for you in any project:

- **Shape a system concept** — talk a design decision through and turn it
  into a design doc.
- **Draw a system** — get a diagram of an architecture, a flow, or a data
  model.
- **Review an architecture** — hand it an existing design and get a verdict
  with specific findings.

Installed to user scope by default, so they travel across every workspace
and engagement, not just one repo. Under the hood these are peer skills plus
one review subagent (the tables below) — but you don't need to know that to
start.

| Skill | What it does |
| --- | --- |
| `architect-design` | Shapes a one-page concept first, then drafts a Google-style design doc (TL;DR → context → goals → proposal → alternatives → risks → rollout → open questions) with Mermaid inline — **well-architected by construction** for the chosen provider (AWS / Azure / GCP, primitives providers like Hetzner, or local-first) and **converged against review** (auto-resolve mechanical findings, surface the judgment calls). |
| `architect-diagram` | Produces Mermaid diagrams routed by intent (C4, flowchart, sequence, state, ER). Cloud-aware (AWS / Azure / GCP, and primitives providers like Hetzner) and agentic-platform-aware (Bedrock AgentCore, AI Foundry, Vertex Agent Engine). |
| `architect-review` | Critiques an existing design doc or diagram with severity-tagged findings, genre-aware rubric routing, and a one-line verdict (SHIP IT / SHIP WITH CHANGES / MAJOR REWRITE / WRONG ARTIFACT). Adds a **well-architected / lens mode** (concern + workload-class lenses, incl. GenAI/agentic) that emits a risk register with each finding tagged **mechanical / judgment**. Runs **inline**, in the current thread. |

| Subagent | What it does |
| --- | --- |
| `design-reviewer` | A **read-only, forked-context** sibling of `architect-review`: the same verdict + severity- and mechanical/judgment-tagged critique, but run in an isolated context that has not seen the authoring — so it cannot mark its own homework. This is the **fresh-context (preferred) rung** of `architect-design`'s convergence loop; it flags, never rewrites (tools are `Read, Grep, Glob`). Use it when an independent review matters more than an in-thread one. |

## Install

Default scope is **user** — installed under `~/.claude/skills/`
(or the equivalent for your adapter) so the skills load in every
workspace.

**Which route?** Use the **Claude plugin** route if you're in Claude Code
and haven't set up a CLI; the **CLI** (`agentbundle`) route if you want a
pinned, scriptable install; the **APM** route if your team standardizes on
APM. All three land the same skills.

```bash
# CLI route — <catalogue> is your catalogue URI: a local clone path
# or a git+https://… URL.
agentbundle install --pack architect <catalogue>

# APM route
apm install architect
```

For the Claude plugin route, add the marketplace first:

```bash
claude plugin marketplace add eugenelim/agent-ready-repo
claude plugin install architect@agent-ready-repo
```

Scope can be flipped to repo-local if you want the skills pinned to
one workspace:

```bash
agentbundle install --pack architect <catalogue> --scope repo
```

Adapters supported: `claude-code`, `codex`, `copilot`, `kiro-ide`,
`kiro-cli`, `cursor`, `gemini`. Pure-markdown `SKILL.md` surface; no
Claude-specific primitives.

## Design principles

These principles are load-bearing — the skills assume them.

- **Workspace-agnostic.** No assumptions about folder structure,
  artifact genres, ontology, or whether this is a code repo, a
  knowledge base, or a scratch directory.
- **No required configuration.** No config files, no profiles, no
  workspace-type detection beyond simple file-existence heuristics.
  Each skill works on first invocation with zero setup.
- **No required composition.** Each skill stands alone. Installing
  one doesn't require installing the others. Rubrics are duplicated
  across skills (with notes flagging the duplication) rather than
  shared via inter-skill references — skill autonomy beats DRY at
  this scale.
- **Inline-first, file-write opportunistic.** Skills produce
  artifacts in the conversation by default. Saving to disk is an
  *offer* with a suggested path based on what already exists
  nearby, never a forced step.
- **Mode detection inside each skill.** Each skill reads the user's
  input and routes; the user does not flag intent.
- **Mermaid only for diagrams.** No PlantUML, Structurizr, or Figma
  integration in this pack.
- **Progressive disclosure.** `SKILL.md` stays under ~100 lines.
  Templates, syntax cheatsheets, rubrics, and cloud / platform
  references live in `references/` and `assets/` and load on demand
  based on what the user mentions.

## What's NOT in this pack

By design — these belong elsewhere or in a later pack:

- **More subagents.** The pack ships exactly one — `design-reviewer`,
  the forked-context review lens above (RFC-0032). Design *authoring*
  and *diagramming* stay skills; only the review lens earns an isolated
  context, mirroring the code side's authoring-skill + reviewer-agent
  split. No further agents without an RFC.
- **Workspace-type profiles or `.architectrc` config files.**
- **Integration / publishing skills** (Confluence, Figma,
  Structurizr) — a separate later pack.
- **ArchiMate / TOGAF / Wardley / graph-extraction skills** — EA
  platform layer, not personal.
- **Coupling to any specific folder layout** — the pack must work
  in any workspace.

## License

Licensed under the repo's dual `MIT OR Apache-2.0` — see
[`LICENSE-MIT`](../../LICENSE-MIT) and
[`LICENSE-APACHE`](../../LICENSE-APACHE) at the repo root. The pack
ships no separate `LICENSE` file; the third-party works credited
below remain under their own (MIT) terms.

## Layout

```
packs/architect/
├── README.md
├── pack.toml
├── .claude-plugin/plugin.json
├── .apm/agents/
│   └── design-reviewer.md              # forked-context review lens (RFC-0032)
└── .apm/skills/
    ├── architect-design/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── design-doc-rubric.md
    │   │   ├── alternatives.md
    │   │   ├── nfr-checklist.md
    │   │   ├── well-architected-pillars.md
    │   │   ├── quality-attribute-scenarios.md
    │   │   ├── tradeoffs-and-sensitivity.md
    │   │   ├── cloud-primitives.md
    │   │   ├── local-dev.md
    │   │   ├── cross-cutting-questions.md
    │   │   ├── lens-genai-agentic.md
    │   │   ├── convergence-loop.md          # design-only: the loop procedure
    │   │   └── leading-edge-domains.md      # design-only: novel-domain method
    │   └── assets/
    │       ├── design-doc.md
    │       └── concept.md                   # the one-page Stage-0 concept
    ├── architect-diagram/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── notation-routing.md
    │   │   ├── diagram-rubric.md
    │   │   ├── cloud-patterns.md
    │   │   ├── mermaid-{flowchart,sequence,c4,state,er,architecture-beta}.md
    │   │   ├── cloud-{aws,azure,gcp,primitives}.md
    │   │   └── agentic-{bedrock-agentcore,ai-foundry,vertex-agent-engine}.md
    │   └── assets/
    │       └── c4-container.mmd
    └── architect-review/
        ├── SKILL.md
        ├── references/
        │   ├── rubric-{design-doc,c4-diagram,sequence-diagram,state-diagram,er-diagram,generic}.md
        │   ├── rubric-well-architected.md   # WA-mode rubric + mechanical/judgment test
        │   ├── well-architected-pillars.md  # ┐
        │   ├── quality-attribute-scenarios.md #  │ duplicated from architect-design
        │   ├── tradeoffs-and-sensitivity.md #  │ (skill autonomy beats DRY),
        │   ├── cloud-primitives.md          #  │ each with a one-line note
        │   ├── local-dev.md                 #  │
        │   ├── cross-cutting-questions.md   #  │
        │   └── lens-genai-agentic.md        # ┘
        └── assets/
            ├── critique.md
            └── risk-register.md             # WA-mode output shape
```

Rubrics and well-architected references are deliberately duplicated
between `architect-design` and `architect-review` rather than shared via
inter-skill references. Each duplicated file carries a one-line note. The
duplication is the principle, not the bug — each skill stands alone.

## Usage

Ask your agent, for example:

- "Design the architecture for a multi-tenant billing service on AWS." (`architect-design`)
- "Draw a Mermaid component diagram for this design." (`architect-diagram`)
- "Review this architecture against the well-architected rubric." (`architect-review`)

---

→ **Go deeper:** the [`architect` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/architect/).
