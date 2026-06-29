# design-craft

A lightweight, recognizable discipline for the core design-craft loop —
**direct → systematize → structure → critique** — that travels with you
across every repo. For interaction and visual designers, design-eng hybrids,
and anyone authoring the **design intent** a UI build consumes (the
design-side twin of `product-engineering`'s product intent).

Every skill ships portable **method**, not your stack: no UI-framework code,
no styling-language syntax, no animation library, and **no values tables** (no
fixed spacing, timing, color, motion-curve, or breakpoint cheat-sheets, no
fixed token set). The skills point to the recognized standards — WCAG, the W3C
Design Tokens interchange shape — and ship the method to *derive* your values,
never the values.

## What's inside

- `aesthetic-direction` — turn a vague "vibe" into named emotional/brand
  goals, an aesthetic-direction doc downstream work references, and coherence
  arbitration (which goal wins when choices conflict).
- `design-system-foundations` — derive a token/scale taxonomy from intent:
  semantic-over-literal naming, ratio-as-concept scales, accessibility as a
  floor, atomic composition ("build systems, not pages").
- `layout-and-information-architecture` — hierarchy, depth-vs-breadth,
  reading patterns, progressive disclosure, and wayfinding as platform-neutral
  concepts.
- `design-critique` — structured heuristic evaluation: map each issue to the
  usability principle it violates, assign a severity rating, and produce a
  prioritized findings list. Applies the shared `quality-floor` checklist.
- A shared **`quality-floor` checklist** — handle all states (empty / loading
  / error / success / partial / disabled), the accessibility floor, and
  "motion communicates state, honor reduced-motion." Referenced by the
  authoring skills, applied by `design-critique`.

## Install

`design-craft` is **user-scope by default** — design method is portable, not
project-specific.

```
agentbundle install --pack design-craft <catalogue>
```

It projects to every shipped adapter that supports the skill primitive
(Claude Code, Codex, Copilot, Cursor, Gemini, Kiro).

## Usage

Ask your agent, for example:

- "Help me turn this 'calm but premium' vibe into named design goals."
- "Derive a spacing and type scale from these goals — no fixed values yet."
- "Structure this dashboard's information architecture and reading flow."
- "Run a heuristic critique of this screen and rank the findings by severity."

## What's NOT in this pack

- **No stack specifics or values tables.** No UI-framework code, no
  styling-language syntax, no animation library, no fixed
  spacing/timing/color/motion-curve/breakpoint table, no fixed token set.
  The pack ships the method to derive values; you choose your tools.
- **No `seeds/`.** Templates (the aesthetic-direction doc) ride as skill
  `assets/` and are copied into your repo at runtime, so the pack stays
  user-scope (RFC-0004 Rail A).
- **No hook, engine, in-pack validator, or reviewer subagent.** This pack is
  habits, not infrastructure. `design-critique` is an interactive **skill**,
  not a `work-loop` reviewer subagent; a forked-context `design-reviewer`
  subagent is a possible later RFC, deliberately out of v1.

---

→ **Go deeper:** the [`design-craft` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/design-craft/).
