# research

Evidence-grounded research that travels with you across every repo. Seven
skills — scoping, source curation, synthesis, adversarial review, decision
support, and rationale reconstruction — plus two read-only retrieval
subagents. The methodology is grounded in seven convergent disciplines
(STORM, PRISMA, ACH, Wikipedia V/RS/NPOV, OSINT, GIJN, GRADE).

## What's inside

- Skills for the full research loop: `research`, `source-map`,
  `build-outline`, `compare-hypotheses`, `identify-perspectives`,
  `devils-advocate`, `decision-archaeology`.
- `evidence-retriever` and `source-extractor` subagents (read-only).

## Install

`research` is **user-scope by default** — research method is portable, not
project-specific.

```
agentbundle install --pack research <catalogue>
```

It projects to every shipped adapter that supports the skill primitive
(Claude Code, Codex, Copilot, Cursor, Gemini, Kiro).

> **Claude Code only — grant web tools to the retrieval subagents.** On Claude
> Code, add **`WebSearch`** and **`WebFetch`** to your `permissions.allow` so the
> `evidence-retriever` and `source-extractor` subagents can do live web
> retrieval — a non-interactive subagent cannot surface the approval prompt, so
> without the grant those tools are denied. This is a one-time note, not
> bundle-managed machinery: `permissions.allow` is yours to own. Other adapters
> (Copilot, Cursor, Gemini, Codex, Kiro) pass the web tools through or bake them
> in at build time and need no such step.

## Usage

Ask your agent, for example:

- "Research how teams measure deployment frequency, and map the sources."
- "Synthesise these five papers into a one-page briefing with citations."
- "Run a devil's-advocate pass on the claim that X causes Y."

---

→ **Go deeper:** the [`research` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/research/).
