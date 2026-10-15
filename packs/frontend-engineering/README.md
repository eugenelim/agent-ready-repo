# Frontend Engineering

Your agent can build, retrofit, audit, and verify web pages and components to an accessibility and performance standard, and leave an evidence manifest behind.

## Install

Install it once for your user account:

```bash
agentbundle install --pack frontend-engineering
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install frontend-engineering@agent-ready-repo
```

## What your agent can do

- Build a new page or component from a design brief, through tokens, semantic HTML, CSS, responsive layout, and states.
- Retrofit an existing page or component after it inspects what to keep, the accessibility debt, and the token drift. It shows the change before it touches files.
- Audit accessibility against WCAG 2.2 AA and report findings by severity.
- Verify a page before release by running five checks: structural HTML, accessibility, CSS tokens when stylelint is set up, a visual QA checklist, and rendered-page inspection. It writes an evidence manifest and leaves your source files alone.
- Diagnose Core Web Vitals failures and asset-budget overruns.
- Choose a rendering model for each route, and design a shared component's interface before any code.

## Skills

- **`frontend-engineering`** — Creates, retrofits, audits, or verifies a page in four modes.
- **`token-architecture`** — Designs or audits a three-tier CSS token system.
- **`a11y-engineering`** — Audits focus, ARIA, keyboard behavior, and complex widgets.
- **`fe-performance`** — Diagnoses and fixes Core Web Vitals and asset-budget problems.
- **`rendering-strategy`** — Picks CSR, SSR, SSG, ISR, or RSC for each route.
- **`component-contract`** — Designs a shared component's props, slots, and events before it is built.
- **`responsive-layout`** — Builds layouts with Grid, Flexbox, and container queries.
- **`css-architecture`** — Organizes CSS with cascade layers and specificity budgets.
- **`fe-status`** — Shows a page's gate history and where it stands against the quality floor.

Subagent: **`frontend-reviewer`** reads a diff in a fresh, read-only context and catches token drift and ARIA gaps.

## Works with

Works with Claude Code, Codex, Copilot, Kiro IDE, Kiro CLI, Cursor, and Gemini CLI. Install [Experience Design](../experience-design/README.md) to route a build through its journey, flow, and design-system work. [Figma](../figma/README.md) can supply the frames you build from. See [Build a page or component](../../guides/frontend-engineering/README.md).

## Questions

**Will it commit my changes?** No. It shows the diff first, and nothing is written until you approve.

**Does it send my code anywhere?** No. Audits and checks run locally. It makes no remote reads or writes.

**How do I undo a change?** Revert the commit. The evidence manifest records what changed and why.

**Does it need Experience Design?** No, but it is recommended. Without it you lose the genre routing by kind of screen.

## Details

Scope: user (default), repo · Version: 0.4.5 · Source: [packs/frontend-engineering](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/frontend-engineering)
