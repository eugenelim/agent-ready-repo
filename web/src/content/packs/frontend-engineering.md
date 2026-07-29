---
name: Frontend Engineering
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
docsUrl: /guides/frontend-engineering/
---

Frontend Engineering installs 9 skills covering the full build journey from design handoff to shipped component: the create/retrofit/audit/verify workflow (`frontend-engineering`), CSS token system architecture (`token-architecture`), deep accessibility engineering beyond automated tooling (`a11y-engineering`), Core Web Vitals measurement and remediation (`fe-performance`), rendering strategy selection (`rendering-strategy`), component API design (`component-contract`), responsive layout craft (`responsive-layout`), CSS architecture at scale (`css-architecture`), and surface orientation (`fe-status`). A forked-context `frontend-reviewer` agent provides a diff-level review for HTML/CSS/JS diffs covering CSS token drift, ARIA mutation completeness, state coverage regression, and the two WCAG 2.2 manual-verification items automated tooling misses.

**Co-install with `experience-design` for full genre routing.** The main `frontend-engineering` skill includes a genre-routing step (step 1b) that loads the appropriate XD discipline skill — `conversion-design` for marketing surfaces, `documentation-design` for docs sites, `analytical-design` for dashboards. This step requires the `experience-design` pack. Without it, `frontend-engineering` records a named skip and proceeds; the skip is honest accounting, not a failure. Install both packs to get the full pre-flight.

**Near-miss guards:** `a11y-engineering` is for dedicated accessibility tasks — an audit, a retrofit of broken patterns, or designing a complex interaction (combobox, data grid, drag-and-drop) where the a11y engineering is the central deliverable. For routine component work, use the accessibility section in `frontend-engineering` — it covers the baseline patterns. Similarly, `fe-performance` is for CWV diagnosis and remediation as the primary task, not for running Lighthouse as a gate at the end of a normal build (use the GATES section in `frontend-engineering` for that).
