# product-engineering

Product-shaping skills — the upstream that turns an idea into the specs your
delivery loop already builds. Installed to **user scope** so they travel across
every workspace, like `architect` and `research`.

The pack is built on one artifact and a set of habits. The artifact is an
**`intent`**: a level-tagged statement of an outcome and the opportunity behind
it. A *capability intent* and a *feature intent* are the same artifact at
different levels — and a PRD is just a feature intent written as a document.
Intents form a recursive tree whose leaf is a shippable spec.

| Skill | What it does |
| --- | --- |
| `frame-intent` | Author an `intent` at any level — outcome (a steerable input metric, a lagging outcome, and a guardrail) + the opportunity. Resolves **Scale** (app ↔ business-unit) at intake, and offers current-state inputs (a process or journey map) only when the work is brownfield. |
| `de-risk-intent` | Name the riskiest assumption, predeclare the **kill condition** in the test's own currency, and run it under a **choosable prototype-approach** — `validate-first` (predeclare, then test) or `prototype-led` (build to learn; the build *is* the test) — to a survive/kill verdict. |
| `decompose-intent` | Break an intent into the next level down — child intents, or a spec/slice at the leaf — and project the tree **one-way** onto your tracker (`none` / Linear / Jira Align). At app scale the leaf *is* an ordinary `core` brief; at business-unit scale it **slices the feature intent per component** into one brief per repo (each carrying `parent-intent:` + a version-pinned contract reference). |
| `align-value-stream` | Stand up and keep current a **value-stream meta-repo** — a coordinating repo with no app code that holds the cross-component artifacts a polyrepo has nowhere else to put: the Backstage **federated catalog**, the shared-contract authority (referenced by version, never forked), the C4/bounded-context architecture, and the **cross-component delivery rollup**. Business-unit scale only. |

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
`new-spec` → `work-loop` take it from there, unchanged. At business-unit scale
the feature intent is **sliced per component** into one brief per repo, each
crossing into its component repo where the same loop takes over; the meta-repo
then **rolls up** whether the whole feature is delivered across all components.
The detailed wire contract is pinned later, at the spec stage, via the existing
`Contract:` seam; the pack stays behavioral. System design hands off to
`architect`.

## Design principles

- **Habits, not infrastructure.** Skills + `references/` + seeds. No engine, no
  hooks, no validators, no subagents, no runtime hub.
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

- **A runtime hub / live coverage API.** The business-unit layer is a
  coordinating *repo* you read and edit, never a service that polls component
  repos. The cross-component rollup is a **markdown snapshot, not a live feed**;
  there is **no atomic cross-repo commit and no shared release train** (the
  inherent cost of polyrepo, stated honestly, not engineered away).
- **Live tracker API sync.** The pack ships the one-way *mapping*; a live
  Linear/Jira-Align integration is a separate, later pack.
- **Wire-contract authoring.** That's the spec stage's `Contract:` seam (the
  `contracts` pack / `new-spec`), reused — not duplicated here.
- **Monorepo-vs-polyrepo structuring.** That decision lives in `monorepo-extras`
  (`new-package`); this pack meets it only at "where the shared contract lives."
- **Subagents.** The three review lenses stay capped at three; shaping is a skill.

## Layout

```
packs/product-engineering/
├── README.md
├── pack.toml
├── .claude-plugin/plugin.json
└── .apm/skills/
    ├── frame-intent/        (SKILL.md + references/ + examples/ + assets/intent-template.md)
    ├── de-risk-intent/      (SKILL.md + references/)
    ├── decompose-intent/    (SKILL.md + references/)
    └── align-value-stream/  (SKILL.md + references/ + assets/rollup-template.md)  ← business-unit scale
```

The intent and rollup **templates travel with their skills** (in each skill's
`assets/`), not as repo `seeds/` — so the pack ships no `seeds/` and stays
user-scope. The skills copy their template into the project's
`docs/product/{intents,rollups}/<slug>.md` at runtime.

## Usage

Ask your agent, for example:

- "Frame the intent for a self-serve onboarding flow." (`frame-intent`)
- "De-risk the riskiest assumption in this intent with a prototype." (`de-risk-intent`)
- "Decompose this intent into shippable specs." (`decompose-intent`)
- "Stand up a value-stream meta-repo to coordinate these components." (`align-value-stream`)
