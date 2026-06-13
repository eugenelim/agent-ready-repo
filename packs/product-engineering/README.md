# product-engineering

Product-shaping skills — the upstream that turns an idea into the specs your
delivery loop already builds. Installed to **user scope** so they travel across
every workspace, like `architect` and `research`.

The pack is built on one artifact and three habits. The artifact is an
**`intent`**: a level-tagged statement of an outcome and the opportunity behind
it. A *capability intent* and a *feature intent* are the same artifact at
different levels — and a PRD is just a feature intent written as a document.
Intents form a recursive tree whose leaf is a shippable spec.

| Skill | What it does |
| --- | --- |
| `frame-intent` | Author an `intent` at any level — outcome (a steerable input metric, a lagging outcome, and a guardrail) + the opportunity. Resolves **Scale** (app ↔ business-unit) at intake, and offers current-state inputs (a process or journey map) only when the work is brownfield. |
| `de-risk-intent` | Name the riskiest assumption, predeclare the **kill condition** in the test's own currency, and run it under a **choosable prototype-approach** — `validate-first` (predeclare, then test) or `prototype-led` (build to learn; the build *is* the test) — to a survive/kill verdict. |
| `decompose-intent` | Break an intent into the next level down — child intents, or a spec/slice at the leaf — and project the tree **one-way** onto your tracker (`none` / Linear / Jira Align). At app scale the leaf *is* an ordinary `core` brief. |

## Install

Default scope is **user** — installed under `~/.claude/skills/` (or your
adapter's equivalent) so the skills load in every workspace.

```bash
agentbundle install product-engineering     # CLI route
claude plugin install product-engineering    # Claude plugin route
apm install product-engineering               # APM route
```

Flip to repo scope to pin the skills to one workspace:

```bash
agentbundle install product-engineering --scope repo
```

Adapters: `claude-code`, `kiro-ide`, `codex`, `copilot`, `cursor`, `gemini`.
Pure-markdown `SKILL.md` surface; no adapter-specific primitives.

## How it composes

The pack is the **upstream** of the delivery loop, not a replacement for it. A
feature intent at app scale *is* a `core` **brief** — `receive-brief` →
`new-spec` → `work-loop` take it from there, unchanged. The detailed wire
contract is pinned later, at the spec stage, via the existing `Contract:` seam;
the pack stays behavioral. System design hands off to `architect`.

## Design principles

- **Habits, not infrastructure.** Skills + `references/` + a seed. No engine, no
  hooks, no validators, no subagents.
- **One artifact, every level.** The recursive `intent` spans solo→business-unit;
  decomposition is recursive and assumptions are de-risked per intent at its level.
- **Modes are lightweight.** One global axis — **Scale** — resolved at intake;
  **maturity**, **reversibility**, and the **prototype-approach** are per-intent
  flags, never global ceremony.
- **Never mandate a schema.** The `intent` template is a prompt sheet; a
  half-formed intent is normal input.
- **Progressive disclosure.** `SKILL.md` stays under 100 lines; the intent model,
  intake, mode tables, and projection profiles live in `references/`.

## What's NOT in this pack

By design — these belong elsewhere or in a later phase:

- **The business-unit, cross-component value-stream layer** — a coordinating
  meta-repo, cross-repo shared contracts, and the cross-component rollup. Phase 2.
- **Live tracker API sync.** The pack ships the one-way *mapping*; a live
  Linear/Jira-Align integration is a separate, later pack.
- **Wire-contract authoring.** That's the spec stage's `Contract:` seam (the
  `contracts` pack / `new-spec`), reused — not duplicated here.
- **Subagents.** The three review lenses stay capped at three; shaping is a skill.

## Layout

```
packs/product-engineering/
├── README.md
├── pack.toml
├── .claude-plugin/plugin.json
├── .apm/skills/
│   ├── frame-intent/      (SKILL.md + references/ + examples/)
│   ├── de-risk-intent/    (SKILL.md + references/)
│   └── decompose-intent/  (SKILL.md + references/)
└── seeds/docs/product/intents/   (_template.md)
```
