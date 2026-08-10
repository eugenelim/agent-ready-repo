---
name: Frontend Engineering
pluginInstallable: true
scope: user
tagline: "The implementation layer for product web surfaces."
skills:
  - frontend-engineering
  - token-architecture
  - a11y-engineering
  - fe-performance
  - rendering-strategy
  - component-contract
  - responsive-layout
  - css-architecture
  - fe-status
installCommand: "agentbundle install --pack frontend-engineering --scope user"
docsUrl: /docs/guides/frontend-engineering/
journeyUrl: /journeys/frontend-engineering/
---

Frontend Engineering is for product teams and agents building web surfaces in HTML, CSS, and JS. Say: "Build this dashboard screen from the brief and produce the frontend evidence for release review." The pack routes the work by job before it shows the skill inventory, so you can start from a new surface, an existing surface, a review-only audit, or a completed page that needs evidence.

## Create

Use create when you are building a new page, screen, or significant component. You provide the brief and constraints; the agent drafts a proportional page/screen contract, plans states and tokens, implements the surface, runs gates, and returns an evidence manifest.

Expected output: an implemented surface with a contract, gate results, screenshots or equivalent rendered evidence, and known exceptions named.

## Retrofit

Use retrofit when the surface already exists and must improve without breaking what users rely on. The agent starts with brownfield inspection: what to preserve, duplicated systems, hard-coded values, accessibility debt, responsive debt, and visual-regression risk.

Expected output: a scoped improvement path, implemented changes when authorized, and an evidence manifest that proves the change did not silently fork the existing system.

## Audit

Use audit when you want a read-only report. The agent checks applicable states, WCAG 2.2 AA expectations, Core Web Vitals targets, asset-budget categories, and brownfield risks without editing code.

Expected output: a prioritized findings list with concrete recommendations and no production writes.

## Verify

Use verify when the page is already built and needs release evidence. The agent runs structural HTML validation, accessibility audit, CSS token enforcement when configured, visual QA, and performance checks against p75 Core Web Vitals targets.

Expected output: a gate-by-gate evidence manifest that separates pass, fail, known exception, and unverified items.

## Journey

[Follow the frontend engineering journey](../../journeys/frontend-engineering/) to see the contract-to-evidence workflow: choose the job, approve the contract, implement or audit, run gates, assemble the manifest, and get an independent frontend review.

## Skill inventory

Frontend Engineering installs 9 skills covering the full build journey from design handoff to shipped component: the create/retrofit/audit/verify workflow (`frontend-engineering`), CSS token system architecture (`token-architecture`), deep accessibility engineering beyond automated tooling (`a11y-engineering`), Core Web Vitals measurement and remediation (`fe-performance`), rendering strategy selection (`rendering-strategy`), component API design (`component-contract`), responsive layout craft (`responsive-layout`), CSS architecture at scale (`css-architecture`), and surface orientation (`fe-status`). A forked-context `frontend-reviewer` agent provides a diff-level review for HTML/CSS/JS diffs covering CSS token drift, ARIA mutation completeness, state coverage regression, and the two WCAG 2.2 manual-verification items automated tooling misses.

**Co-install with `experience-design` for full genre routing.** The main `frontend-engineering` skill includes a genre-routing step that loads the appropriate XD discipline skill: `conversion-design` for marketing surfaces, `documentation-design` for docs sites, and `analytical-design` for dashboards. This step requires the `experience-design` pack. Without it, `frontend-engineering` records a named skip and proceeds; the skip is honest accounting, not a failure. Install both packs to get the full pre-flight.

**Near-miss guards:** `a11y-engineering` is for dedicated accessibility tasks: an audit, a retrofit of broken patterns, or designing a complex interaction such as a combobox, data grid, or drag-and-drop where the accessibility engineering is the central deliverable. For routine component work, use the accessibility section in `frontend-engineering`; it covers the baseline patterns. Similarly, `fe-performance` is for CWV diagnosis and remediation as the primary task, not for running Lighthouse as a gate at the end of a normal build. Use the GATES section in `frontend-engineering` for that.
