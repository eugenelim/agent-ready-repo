# product-engineering

Product-shaping skills — the upstream that turns an idea into the specs your
delivery loop already builds. Installed to **user scope** so they travel across
every workspace, like `architect` and `desk-research`.

The pack is built on one artifact and a set of habits. The artifact is an
**`intent`**: a level-tagged statement of an outcome and the opportunity behind
it. A *product-vision intent*, a *product-strategy intent*, a *capability
intent*, and a *feature intent* are the same artifact at different levels — and a
PRD is just a feature intent written as a document. `Level` is an **open
recognized set** (`product-vision › product-strategy › capability › feature`)
**decoupled from `Scale`**: Scale suggests a starting altitude but no longer
stamps one. Intents form a recursive tree whose leaf is a shippable spec.

| Skill | What it does |
| --- | --- |
| `frame-intent` | Author an `intent` at any altitude in the open recognized set — `product-vision` / `product-strategy` / `capability` / `feature` — outcome (a steerable input metric, a lagging outcome, and a guardrail) + the opportunity. Resolves **Scale** (app ↔ business-unit) at intake (Scale *suggests* the starting altitude, decoupled from `Level`), and offers current-state inputs (a process or journey map) only when the work is brownfield. |
| `de-risk-intent` | Name the riskiest assumption, predeclare the **kill condition** in the test's own currency, and run it under a **choosable prototype-approach** — `validate-first` (predeclare, then test) or `prototype-led` (build to learn; the build *is* the test) — to a survive/kill verdict. |
| `decompose-intent` | Break an intent into the next level down — child intents, or a spec/slice at the leaf — and project the tree **one-way** onto your tracker (`none` / Linear / Jira Align). At app scale the leaf *is* an ordinary `core` brief; at business-unit scale it **slices the feature intent per component** into one brief per repo (each carrying `parent-intent:` + a version-pinned contract reference). |
| `align-value-stream` | Stand up and keep current a **value-stream meta-repo** — a coordinating repo with no app code that holds the cross-component artifacts a polyrepo has nowhere else to put: the Backstage **federated catalog**, the shared-contract authority (referenced by version, never forked), the C4/bounded-context architecture, and the **cross-component delivery rollup**. Business-unit scale only. |
| `ux-writing` | Shape the **words a user reads** in the UI. Characterize the product's **voice** along a few axes (humor / formality / respect / enthusiasm), write the recurring UI states — **error, empty, button, label** — from blame-free, actionable formulas, and run a **content checklist** before copy ships. The content layer of the pack; a method, not a word bank. |

## Install

Default scope is **user** — installed under `~/.claude/skills/` (or your
adapter's equivalent) so the skills load in every workspace.

```bash
# <catalogue> is your catalogue URI: a local clone path or a git+https://… URL.
agentbundle install --pack product-engineering <catalogue>   # CLI route
apm install product-engineering                               # APM route
```

For the Claude plugin route, add the marketplace first:

```bash
claude plugin marketplace add eugenelim/agent-ready-repo
claude plugin install product-engineering@agent-ready-repo
```

Flip to repo scope to pin the skills to one workspace:

```bash
agentbundle install --pack product-engineering <catalogue> --scope repo
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

- **Habits, not infrastructure.** Skills + `references/` + `assets/` templates. No
  engine, no hooks, no validators, no subagents, no runtime hub.
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
    ├── align-value-stream/  (SKILL.md + references/ + assets/rollup-template.md)  ← business-unit scale
    └── ux-writing/ (SKILL.md + references/ + assets/voice-chart-template.md)  ← content layer
```

The intent, rollup, and voice-chart **templates travel with their skills** (in
each skill's `assets/`), not as repo `seeds/` — so the pack ships no `seeds/` and
stays user-scope. The skills copy their template into the project's
`docs/product/{intents,rollups,voice}/<slug>.md` at runtime.

## Usage

Ask your agent, for example:

- "Frame the intent for a self-serve onboarding flow." (`frame-intent`)
- "De-risk the riskiest assumption in this intent with a prototype." (`de-risk-intent`)
- "Decompose this intent into shippable specs." (`decompose-intent`)
- "Stand up a value-stream meta-repo to coordinate these components." (`align-value-stream`)
- "Characterize our product voice, then write the empty-state and error copy." (`ux-writing`)

## Cross-pack: `product-strategy`

The `product-strategy` pack is the **upstream provider** of the strategic context this pack consumes. Before `frame-situation` runs, a strategist using the `product-strategy` pack may have committed altitude-0 artifacts to `docs/product/shaping/`: OKR cascade (`okr-cascade.md`), market context (`macro-environment.md`, `competitive-landscape.md`), portfolio position (`portfolio-position.md`, `swot-analysis.md`), and stakeholder synthesis (`stakeholder-synthesis.md`). These are optional inputs — `frame-situation` routes strategy-typed shaping-queue entries (written by `run-okr-cascade`) into its six-step shaping sequence; `frame-intent` uses the market context as grounding when present. See the [`product-strategy` pack README](../product-strategy/README.md).

---

→ **Go deeper:** the [`product-engineering` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/product-engineering/).

---

## Cross-pack: `experience-design`

`ux-writing` is the **content layer of the design seat** — the words
live here, in `product-engineering`, while the design methods, screen flow, and
per-screen briefs live in the `experience-design` pack. The two packs read as one seat:

- **`experience-design`'s `user-flow`** produces the per-screen state matrix
  (one row per screen × state: empty / loading / error / success / partial /
  disabled / permission-denied). Pass that matrix to `ux-writing` and
  it writes copy keyed to every cell.
- **Without a screen flow**, `ux-writing` is still fully useful —
  it degrades to naming the states inline. The pairing is additive, not required.

Install both packs to run the full design-to-copy thread:

```bash
# install takes one pack per invocation — run it twice.
agentbundle install --pack experience-design <catalogue>
agentbundle install --pack product-engineering <catalogue>
```

→ See the [`experience-design` pack README](../experience-design/README.md).
