# Guidance placement patterns for lower cognitive load

> Discipline: applied (practitioner-pattern survey)

## Question

Where should portable agent guidance live so that it reduces cognitive load in
chat, requested inputs, code, comments, documentation, and skill-produced
artifacts without turning every `AGENTS.md` or `SKILL.md` into a prose dump?

## Core seed inventory

The core pack currently ships 14 seed files:

```text
packs/core/seeds/
├── AGENTS.md
├── _agents-footer.md
├── workspace.toml
└── docs/
    ├── CHARTER.md
    ├── CONVENTIONS.md
    ├── architecture/
    │   ├── README.md
    │   └── overview.md
    ├── knowledge/
    │   ├── README.md
    │   └── patterns.jsonl
    ├── product/
    │   ├── README.md
    │   ├── briefs/_template.md
    │   ├── changelog.md
    │   └── roadmap.md
    └── specs/README.md
```

`deliver_seeds()` already preserves arbitrary relative paths recursively. The
catalogue linter deliberately rejects an undeclared seed shape, so a new
`AGENT_RULES.md`, `.agents/rules/cognitive-load.md`, and `docs/AGENTS.md` each
need an explicit declared shape rather than special install logic. The planned
inventory is 17 delivered seed files.

## Findings

### 1. Use context files as routers, not rule stores

Nested instruction files are the most portable available mechanism for scoped
guidance. The AGENTS.md convention, GitHub Copilot CLI, Claude Code, and Gemini
CLI all describe hierarchical or path-local instruction discovery. This makes
`docs/AGENTS.md` the recognizable home for documentation, backlog, and other
prose under `docs/`. [high]

Repository-wide conversation behavior has different ownership. Keep
`AGENT_RULES.md` as a bounded route table and put full topic bodies under
`.agents/rules/`. Root `AGENTS.md` has one unconditional instruction to read the
router; the router selects `always` and activity-matched topics without testing
adapter identity. Claude follows the repository's `CLAUDE.md → AGENTS.md`
chain. Codex loads `AGENTS.md` directly. Gemini receives it through the existing
managed `context.fileName = ["AGENTS.md", "GEMINI.md"]` bridge. [high]

Sources: [AGENTS.md convention](https://agents.md/),
[GitHub Copilot CLI instructions](https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions),
[Claude Code memory](https://code.claude.com/docs/en/memory), and
[Gemini CLI context files](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md).

### 2. Codex and Gemini repositories do not establish a rules-folder convention

The sampled instrumented repositories use root context files and add nested
context files at ownership boundaries. None uses a repository-level rules
folder as a Codex or Gemini loading convention. That favors a recognizable
root router as the entry point. A hidden `.agents/rules/` directory can still
serve as catalogue-owned topic storage when the router loads it explicitly; it
must not be described as a Codex or Gemini native convention. [moderate]

| Repository sample | Observed pattern |
| --- | --- |
| [`openai/codex`](https://github.com/openai/codex/blob/main/AGENTS.md) | Root `AGENTS.md` plus a focused nested `AGENTS.md` in the TUI subtree. |
| [`openai/openai-cookbook`](https://github.com/openai/openai-cookbook/blob/main/AGENTS.md) | Root `AGENTS.md` plus a focused nested instruction file. |
| [`google-gemini/gemini-cli`](https://github.com/google-gemini/gemini-cli/blob/main/GEMINI.md) | Root `GEMINI.md` plus package-level `GEMINI.md` files. |
| [`google/adk-python`](https://github.com/google/adk-python/blob/main/AGENTS.md) | Root `AGENTS.md`; deeper procedures route into skills. |
| [`googleapis/google-cloud-python`](https://github.com/googleapis/google-cloud-python/blob/main/GEMINI.md) | One root `GEMINI.md`. |
| [`vercel/next.js`](https://github.com/vercel/next.js/blob/canary/AGENTS.md) | Root and scoped `AGENTS.md` files. |
| [`kubernetes/kubernetes`](https://github.com/kubernetes/kubernetes/blob/master/AGENTS.md) | One root `AGENTS.md`. |

This is a pattern sample, not proof that no repository uses a rules folder.
The stronger fact is contractual: Codex documents `AGENTS.md`, and Gemini
documents `GEMINI.md` plus configured context filenames. Neither documents a
repo rules directory as its native loader. [high]

Sources: [Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md/),
[Gemini CLI context files](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md),
the governing [Gemini adapter ADR](../../../adr/0016-gemini-cli-full-parity-adapter.md),
and the local [`context-filenames` contract](../../../../contracts/adapter.toml).

### 3. Native rule surfaces differ by adapter

The native surfaces are useful future projection targets, but they should not
leak adapter conditions into shared root prose.

| Adapter | Repository rule or context surface | User-wide surface | Future projection question |
| --- | --- | --- | --- |
| Claude Code | `.claude/rules/*.md` and `CLAUDE.md` | `~/.claude/rules/*.md` | Avoid loading a global rule through both the root router and a native copy. |
| Codex | root or nested `AGENTS.md` | `~/.codex/AGENTS.md` | Define safe composition for singleton context files; there is no modular rules directory. |
| Copilot | `.github/instructions/*.instructions.md` | `~/.copilot/copilot-instructions.md` for CLI | Map path scope and protect the user singleton. |
| Cursor | `.cursor/rules/*.mdc` and supported root context | Cursor settings | Map `alwaysApply` and path scope without duplicating a root-loaded rule. |
| Gemini CLI | root or nested `GEMINI.md`, or configured context names | `~/.gemini/GEMINI.md` | Use imports or managed context names without overwriting adopter content. |
| Kiro IDE and CLI | `.kiro/steering/*.md` | `~/.kiro/steering/*.md` | Map inclusion modes and scope. |

Sources: [Claude Code memory](https://code.claude.com/docs/en/memory),
[Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md/),
[GitHub Copilot customization](https://docs.github.com/en/copilot/concepts/prompting/response-customization),
[Cursor rules](https://docs.cursor.com/context/rules-for-ai),
[Gemini CLI context files](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md), and
[Kiro steering](https://kiro.dev/docs/steering/).

The future catalogue abstraction should therefore be named `rules`, with
canonical content under `.apm/rules/`. Its typed contract must own scope,
precedence, metadata, duplicate-loading prevention, singleton conflicts, the
shared `.agents/rules/` fallback, and managed `AGENT_RULES.md` route rows.
That work is captured separately in
[`catalogue-rules-primitive.md`](../../../product/intents/catalogue-rules-primitive.md).

### 4. Skills need a self-contained copy of the behavior they exercise

User-profile skills can run without the core seed and can write artifacts
outside a repository. A skill must therefore state its own conversation,
requested-input, receipt, and artifact-rendering behavior. The copy should be a
small task-relevant block, not a reference to another skill or to a repository
path. Detailed authoring guidance can remain progressively disclosed to
maintainers. [moderate]

Downgrade: `indirectness` — the sources establish progressive loading and
portable skill resources, while the exact self-contained-copy rule is a design
inference from this catalogue's independent-skill and user-scope contracts.

Sources: [Agent Skills specification](https://agentskills.io/specification),
[GitHub customization comparison](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/comparing-cli-features), and the local
`guides/_shared/reference/catalogue-authoring-standards.md` plus install model.

### 5. Synchronize repeated skill contracts mechanically

The existing `tools/add-rendering-directives.py` already maps skills to the
rendering shapes they emit, but it only inserts missing sections and edits
projections. Evolve it into a source-only update/check tool that owns a bounded
managed block. A check mode should fail on missing, stale, duplicate, or
misplaced blocks. This reduces author load while keeping every installed skill
independent. [moderate]

Downgrade: `indirectness` — this is a repository-specific design inference,
supported by the current tool, source/projection contract, and Agent Skills'
progressive-disclosure model rather than cross-project outcome studies.

### 6. Make the behavioral contract shape-first and depth-preserving

The lookup should lead with the outcome or requested action, keep one idea per
sentence, use short sections, and render repeated fields as an appropriate
structure. It should remove navigation prose and redundant restatement, not
technical substance. When the user requests depth, preserve the depth and make
it scannable. [high]

Sources: [W3C cognitive accessibility guidance](https://www.w3.org/WAI/WCAG2/supplemental/objectives/o3-clear-content/),
[Microsoft's scannable-content guidance](https://learn.microsoft.com/en-us/style-guide/scannable-content/),
[Digital.gov plain-language principles](https://digital.gov/guides/plain-language/principles), and
[GOV.UK accessible-document guidance](https://www.gov.uk/guidance/publishing-accessible-documents).

## Recommended placement

| Surface | Owning location | Treatment |
| --- | --- | --- |
| Rule router | new root seed `packs/core/seeds/AGENT_RULES.md` | Keep only `when`, `read`, and `purpose` rows; no rule bodies. |
| Cognitive-load behavior | new seed `packs/core/seeds/.agents/rules/cognitive-load.md` | Mark as `always` in the router; do not route again. |
| Session activation | root and seed `AGENTS.md` | Unconditionally require a silent read of `AGENT_RULES.md`; no adapter branch. |
| Claude loading | existing `CLAUDE.md → AGENTS.md` path | Follow the same router; `.agents/rules/` is not natively loaded. |
| Gemini loading | existing managed `context.fileName` bridge | Load `AGENTS.md`, which routes through the same table. |
| Docs, backlog, repository prose | new `packs/core/seeds/docs/AGENTS.md` | Put the compact surface-by-surface lookup here. |
| Skill chat and artifacts anywhere | each source `SKILL.md` | Inject a self-contained, applicable subset. |
| Authoring vocabulary and examples | `guides/_shared/reference/output-rendering.md` | Expand the canonical maintainer guide. |
| Synchronization and enforcement | `tools/add-rendering-directives.py` | Update source blocks and provide check mode. |
| Native rule projections | deferred `rules` primitive | Design `.apm/rules/` and adapter projections as a separate backlog item. |

`AGENT_RULES.md` and `.agents/rules/` are seed-owned lookup conventions, not new
native loaders. They work because the already-loaded root context requires the
router read. The chain is the same for Claude, Codex, Cursor, Gemini, and any
other adapter that consumes the shared root context. There is no “unless this
adapter” clause. Topic files are leaves, so the chain cannot grow beyond one
router hop.

User-profile skills still carry the self-contained block because they can run
outside a seeded repository. Adding the same prose to `docs/CONVENTIONS.md`,
templates, or each README would increase author load and create drift.

## Known unknowns and unknowables

- An `AGENTS.md` instruction to read the router and its selected topics is
  behavioral, not a native include directive. Claude, Codex, and Gemini
  fixtures therefore need to test both reads before the first response or
  unrelated tool call.
- Nested `AGENTS.md` support is not uniform across every adapter version. The
  root baseline and skill-local blocks prevent the scoped file from becoming a
  single point of failure.
- A prose contract can shape comments and generated code, but deterministic
  enforcement is language-specific. This change should not pretend to replace
  linters or formatters.

## Moderator pass

The earlier recommendation put the whole contract in `AGENT_RULES.md`, which
would make that file grow with every future concern. The revised design keeps
it as a bounded router and places cognitive load in one leaf topic. Native rule
projection remains separate; the future `rules` primitive owns migration from
the seed lookup convention and must prevent duplicate loading.
