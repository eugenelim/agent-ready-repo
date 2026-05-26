# architect

Solution-architecture skills — three peer skills installed to user
scope so they travel across every workspace and engagement, not just
one repo.

| Skill | What it does |
| --- | --- |
| `architect-design` | Drafts Google-style design docs (TL;DR → context → goals → proposal → alternatives → risks → rollout → open questions) with Mermaid diagrams inline where structure needs a picture. |
| `architect-diagram` | Produces Mermaid diagrams routed by intent (C4, flowchart, sequence, state, ER). Cloud-aware (AWS / Azure / GCP) and agentic-platform-aware (Bedrock AgentCore, AI Foundry, Vertex Agent Engine). |
| `architect-review` | Critiques an existing design doc or diagram with severity-tagged findings, genre-aware rubric routing, and a one-line verdict (SHIP IT / SHIP WITH CHANGES / MAJOR REWRITE / WRONG ARTIFACT). |

## Install

Default scope is **user** — installed under `~/.claude/skills/`
(or the equivalent for your adapter) so the skills load in every
workspace.

```bash
# CLI route
agentbundle install architect

# Claude plugin route
claude plugin install architect

# APM route
apm install architect
```

Scope can be flipped to repo-local if you want the skills pinned to
one workspace:

```bash
agentbundle install architect --scope repo
```

Adapters supported: `claude-code`, `kiro`, `codex`. Pure-markdown
`SKILL.md` surface; no Claude-specific primitives.

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

- **Subagents.** Code-side reviewers cover code; design-side review
  is a skill, not a subagent.
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
└── .apm/skills/
    ├── architect-design/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── design-doc-rubric.md
    │   │   ├── alternatives.md
    │   │   └── nfr-checklist.md
    │   └── assets/
    │       └── design-doc.md
    ├── architect-diagram/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── notation-routing.md
    │   │   ├── diagram-rubric.md
    │   │   ├── cloud-patterns.md
    │   │   ├── mermaid-{flowchart,sequence,c4,state,er,architecture-beta}.md
    │   │   ├── cloud-{aws,azure,gcp}.md
    │   │   └── agentic-{bedrock-agentcore,ai-foundry,vertex-agent-engine}.md
    │   └── assets/
    │       └── c4-container.mmd
    └── architect-review/
        ├── SKILL.md
        ├── references/
        │   ├── rubric-design-doc.md
        │   ├── rubric-c4-diagram.md
        │   ├── rubric-sequence-diagram.md
        │   ├── rubric-state-diagram.md
        │   ├── rubric-er-diagram.md
        │   └── rubric-generic.md
        └── assets/
            └── critique.md
```

Rubrics are deliberately duplicated between `architect-design`'s
self-check rubric and `architect-review`'s critique rubrics. Each
duplicated rubric carries a one-line note. The duplication is the
principle, not the bug.
