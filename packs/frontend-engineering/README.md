# frontend-engineering

Build, audit, and ship production-quality web surfaces — WCAG 2.2–clean HTML, CSS, and JS with a CWV-passing evidence manifest.

---

## Start here

Describe the task — what you're building, auditing, or improving.

```text
Build the notification panel from this design brief:
- Three states: empty, unread, overflow
- Token colors from the DS design-system foundation
- Keyboard-navigable list; focus trap in overlay mode
```

```text
Audit the accessibility of the checkout flow — I need to find
what's blocking WCAG 2.2 AA compliance.
```

The pack runs in four modes — **create**, **retrofit**, **audit**, or **verify** — and picks the mode from your description. Every create or retrofit run ends with an evidence manifest: routes, viewports, browsers, states, screenshots, a11y result, performance result, and known exceptions.

---

## Common jobs

**Create a new surface from a design handoff**
Describe the surface and point to the design brief or screen spec.
Returns a genre-route pre-flight (pick `conversion-design`, `documentation-design`, or `analytical-design` if `experience-design` is co-installed), then implement through token setup, semantic HTML, base CSS, responsive, states, a11y, and performance gates. Result: committed source files + evidence manifest. Nothing is committed until you approve.

**Retrofit an existing surface**
Say "retrofit this surface to pass WCAG 2.2 AA" or "bring this component up to the design system tokens."
Runs a brownfield inspection (what-to-preserve, a11y debt, token drift, responsive debt, visual regression risk) before any change. Proposes a plan and previews the delta before touching files. Result: committed changes + updated evidence manifest.

**Deep accessibility audit**
Say "audit the accessibility of this surface" or describe a specific interaction pattern (combobox, data grid, drag-and-drop).
Returns structured findings against WCAG 2.2 with severity (blocker / concern / suggestion) — including the two manual-verification items (Focus Appearance, Target Size) that automated tools miss. No changes are made unless you ask.

**Verify a surface before shipping**
Say "verify this surface before the release."
Runs the full gate sequence: lint, typecheck, Playwright baseline, a11y scan, CWV measurement. Returns a pass/fail verdict per gate and a completed evidence manifest you can attach to the release record. Read-only — no writes.

---

## How it works

```text
Build the notification panel from this design brief: ...

  ● Genre route: documentation-design (co-installed XD detected)
  ● Token audit: DS tokens loaded — 3 colour tokens, 1 spacing token
  ● Component contract: NotificationPanel(items, onDismiss, maxVisible)
  ● Implement: HTML structure ✓ → base CSS ✓ → responsive ✓ → states ✓
  ● A11y check: keyboard nav ✓ | focus trap ✓ | ARIA list ✓
  ● Performance: LCP 0.8s ✓ | CLS 0.01 ✓ | INP 90ms ✓

  Evidence manifest written to docs/evidence/notification-panel.md

  Review the diff? ›
  Approve and commit? ›
```

**What will be read:** your design brief, existing CSS/token files, a11y scanner output, browser performance trace.  
**What will be changed:** source HTML, CSS, JS files — only after you approve the diff.  
**Nothing is committed without your review.** The `frontend-reviewer` agent reads the diff cold (no authoring context) and catches CSS token drift, ARIA gaps, and manual WCAG 2.2 items before you confirm.

---

## Installation and trust

- **Scope:** user — installs portably across all your repos (co-install `experience-design` for full genre routing)
- **Reads:** your design briefs, existing source files, a11y scanner output, Playwright results
- **Local writes:** source files and evidence manifest — only after you approve
- **Remote reads/writes:** none (Lighthouse / axe run locally)
- **Approval:** diff shown before any file is written; evidence manifest captures every exception you acknowledge
- **Rollback:** revert the commit — the evidence manifest records what changed and why

```bash
agentbundle install --pack frontend-engineering --scope user
agentbundle install --pack experience-design --scope user   # for full genre routing
```

---

## Skills included — under the hood

| Skill | When to use |
|-------|-------------|
| `frontend-engineering` | Create, retrofit, audit, or verify a surface — four modes |
| `token-architecture` | Design or audit a three-tier CSS token system |
| `a11y-engineering` | Dedicated accessibility audit, complex interaction design |
| `fe-performance` | CWV diagnosis and asset-budget remediation |
| `rendering-strategy` | Select or audit the rendering model for a route (CSR/SSR/SSG/ISR/RSC) |
| `component-contract` | Design a shared component's public interface before implementation |
| `responsive-layout` | Design or debug adaptive layouts across breakpoints |
| `css-architecture` | Set up or refactor CSS at scale — cascade layers, specificity budgets |
| `fe-status` | Orient to an existing surface's gate history and quality floor status |

**Reviewer:** `frontend-reviewer` — forked-context, read-only diff reviewer.

---

## Sole owner of `frontend-engineering`

This pack is the sole owner of the `frontend-engineering` skill. The `core` pack's resident skill was deleted in ADR-0057 (2026-07-27) to resolve a footprint-gate conflict. Load this pack's skill — it is the canonical content owner (four modes, evidence manifest, WCAG 2.2 AA, CWV targets).

---

## Go deeper

→ [`guides/frontend-engineering/`](../../guides/frontend-engineering/)
