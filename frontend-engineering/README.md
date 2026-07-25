# frontend-engineering

The implementation layer for product web surfaces — HTML, CSS, and JS. For
engineers who write frontend code and need principled guidance from design
handoff to shipped component.

## What this pack installs

Nine skills and one reviewer agent:

| Skill | When to use |
|---|---|
| `frontend-engineering` | Primary surface skill — all four modes: create, retrofit, audit, verify |
| `token-architecture` | Design or audit a three-tier CSS token system |
| `a11y-engineering` | Dedicated accessibility task — audit, retrofit, or complex interaction design |
| `fe-performance` | CWV diagnosis or asset budget remediation |
| `rendering-strategy` | Select or audit the rendering model for a route (CSR/SSR/SSG/ISR/RSC) |
| `component-contract` | Design a shared component's public interface before writing implementation |
| `responsive-layout` | Design or debug adaptive layouts across breakpoints |
| `css-architecture` | Set up or refactor CSS at scale — cascade layers, specificity budgets, scoping strategy |
| `fe-status` | Orient to an existing surface's gate history and quality floor status |

**Reviewer:** `frontend-reviewer` — forked-context, read-only diff reviewer for
HTML/CSS/JS diffs. Covers CSS token drift, ARIA mutation completeness, state
coverage regression, and WCAG 2.2 Focus Appearance / Target Size items that
automated tooling misses.

## Co-install

For full genre routing in the frontend pre-flight (step 1b of `frontend-engineering`),
co-install with `experience-design`:

```
agentbundle install --pack frontend-engineering --scope user
agentbundle install --pack experience-design --scope user
```

If `experience-design` is absent, `frontend-engineering` records a named skip —
`XD genre routing: skipped (experience-design pack absent)` — and proceeds. The
named skip is not a failure; it is honest accounting.

## Install

```
agentbundle install --pack frontend-engineering --scope user
```

Projects to: Claude Code, Codex, Copilot, Cursor, Gemini, Kiro.

## Guides

→ [`docs/guides/frontend-engineering/`](../../docs/guides/frontend-engineering/)
