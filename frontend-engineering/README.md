# frontend-engineering

Say "build this component from the design handoff" or "audit the accessibility of this surface" — and the agent works through it from token architecture to shipped, WCAG 2.2–clean HTML, CSS, and JS.

`frontend-engineering` covers the full implementation arc: the primary `frontend-engineering` skill handles creation, retrofit, audit, and verification in four modes; specialist skills go deep on tokens, accessibility, performance, rendering strategy, component contracts, responsive layout, and CSS architecture at scale. The `frontend-reviewer` agent reads diffs cold — no authoring context — and catches CSS token drift, ARIA mutation gaps, and WCAG 2.2 Focus Appearance / Target Size items that automated tooling misses.

## Skills

| Skill | When to use |
|---|---|
| `frontend-engineering` | Create, retrofit, audit, or verify a surface — four modes |
| `token-architecture` | Design or audit a three-tier CSS token system |
| `a11y-engineering` | Accessibility audit, retrofit, or complex interaction design |
| `fe-performance` | CWV diagnosis or asset budget remediation |
| `rendering-strategy` | Select or audit the rendering model for a route (CSR/SSR/SSG/ISR/RSC) |
| `component-contract` | Design a shared component's public interface before implementation |
| `responsive-layout` | Design or debug adaptive layouts across breakpoints |
| `css-architecture` | Set up or refactor CSS at scale — cascade layers, specificity budgets, scoping |
| `fe-status` | Orient to an existing surface's gate history and quality floor status |

**Reviewer:** `frontend-reviewer` — forked-context, read-only diff reviewer.

## Sole owner of `frontend-engineering`

This pack is the sole owner of the `frontend-engineering` skill. The `core` pack's resident skill was deleted in ADR-0057 (2026-07-27) to resolve a footprint-gate conflict that prevented this pack from installing alongside `core`. Load this pack's skill — it is the canonical content owner (four modes, evidence manifest, WCAG 2.2 AA, CWV targets).

## Co-install

For full genre routing in the frontend pre-flight, co-install with `experience-design`:

```
agentbundle install --pack frontend-engineering --scope user
agentbundle install --pack experience-design --scope user
```

If `experience-design` is absent, `frontend-engineering` records a named skip and proceeds.

## Install

```
agentbundle install --pack frontend-engineering --scope user
```

Projects to: Claude Code, Codex, Copilot, Cursor, Gemini, Kiro.

## Guides

→ [`guides/frontend-engineering/`](../../guides/frontend-engineering/)
