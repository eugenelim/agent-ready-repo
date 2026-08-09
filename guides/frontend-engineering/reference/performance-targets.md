---
title: Performance Targets
summary: Reference the fixed Core Web Vitals targets and choose project-specific asset budget ceilings for a frontend surface.
pack: frontend-engineering
kind: reference
journey: frontend-engineering
---

# Performance targets

Use this when you are planning or verifying a frontend surface and need the pack's performance policy without opening the skill source. The result is a surface-specific performance target decision: fixed Core Web Vitals targets, prioritized asset-budget categories, measurement evidence, and project-owned numeric ceilings.

Start with a request like:

> Set performance targets for this documentation site using the fixed CWV thresholds and our project baseline.

This reference changes nothing by itself. When you invoke `frontend-engineering` or `fe-performance`, the agent reads the route or surface measurements you provide and may update a project spec or budget only when you authorize that write.

## Fixed Core Web Vitals targets

Evaluate field data separately for mobile and desktop wherever it exists. Use p75 for each metric.

| Metric | Target | Measures |
|---|---:|---|
| LCP (Largest Contentful Paint) | <= 2.5 seconds | Perceived load speed: when the largest visible content element renders |
| INP (Interaction to Next Paint) | <= 200 milliseconds | Responsiveness: latency of the worst interaction across the page session |
| CLS (Cumulative Layout Shift) | <= 0.1 | Visual stability: unexpected content movement |

Measure with the best evidence available for the surface: field data where it exists, then Lighthouse, Chrome DevTools Performance traces, WebPageTest, resource waterfalls, and bundle analysis as needed.

## Canonical asset-budget categories

Set numeric ceilings from product context and measured baseline. Do not use a universal byte ceiling across unrelated surfaces.

| Category | What to measure | Budget decision |
|---|---|---|
| JS | JavaScript transferred, parsed, and executed per route | Cap route and shared JS against the baseline route and the interaction cost the surface can tolerate |
| images | Total image payload per route, responsive source selection, and whether the LCP candidate is optimized | Cap by first-screen need, media density, and the required image quality for the surface |
| fonts | Web font files transferred and render behavior | Cap by required type system, subset coverage, and whether self-hosting or `font-display` prevents blocking text render |
| third-party scripts | Analytics, tags, widgets, embeds, and their main-thread cost | Cap by scripts that are essential to the user job; defer, remove, or facade the rest |
| hydration | Client-side hydration cost for SSR or islands | Cap by the interactive components that must work on first load; avoid hydrating static content |
| route-level loading | Per-route code-split chunks and cache boundaries | Cap each route to what that route needs, with shared chunks only for genuinely shared code |
| long tasks | Main-thread tasks over 50 milliseconds and interaction-blocking work | Cap by acceptable interaction delay and split or defer work that blocks INP |

## Surface-type matrix

Use the matrix to decide which categories need project-specific numeric ceilings before implementation or verification.

| Surface type | Priority | Measurement guidance | Numeric-budget decision rule |
|---|---|---|---|
| Marketing | LCP, CLS, images, fonts, third-party scripts | Measure first viewport on mobile and desktop; identify the LCP element, font behavior, tags, embeds, and any late-injected content | Set ceilings for first-screen images, fonts, and third-party scripts from the campaign baseline and conversion-critical creative; keep JS and hydration tight unless interaction is central |
| Documentation | LCP, CLS, route-level loading, JS, fonts | Measure article and reference routes separately; check code blocks, search, navigation, font loading, and static-route chunking | Set ceilings per route family, with stricter JS and hydration ceilings for mostly static pages and explicit allowances for search or interactive examples |
| Product/workspace | INP, JS, hydration, long tasks, route-level loading | Trace primary interactions, route transitions, drawers, tables, editors, and optimistic updates on representative data | Set ceilings around the primary workflow: route chunks, hydrated islands, and long-task count must fit the expected session, not just the initial page load |
| Analytical/internal | INP, long tasks, JS, route-level loading, third-party scripts | Profile large datasets, chart rendering, filters, exports, and repeated dashboard interactions; include mobile only when the product supports that use | Set ceilings from data volume and refresh cadence; define limits for chart libraries, worker/off-main-thread work, and third-party analytics separately |
| Transactional | INP, CLS, JS, third-party scripts, fonts | Measure every step in the form or checkout path; check validation, payment or identity embeds, error states, and layout stability under dynamic messages | Set ceilings for scripts and interaction work per step; require explicit approval for third-party embeds or font choices that can delay completion |

## What to record

Record the decision in the project spec, performance budget, or evidence manifest:

- **Target context:** surface type, route or route family, and whether field data exists for mobile, desktop, or both.
- **Fixed targets:** LCP <= 2.5 seconds, INP <= 200 milliseconds, CLS <= 0.1 at p75.
- **Measurements:** field data, Lighthouse, DevTools trace, WebPageTest, bundle analysis, and resource waterfall evidence used.
- **Budget categories:** which of JS, images, fonts, third-party scripts, hydration, route-level loading, and long tasks need numeric ceilings for this surface.
- **Ceilings:** project-owned numbers, source baseline, and who approved them.
- **Exceptions:** any category intentionally left without a ceiling and why.

Likely next request:

> Run `frontend-engineering` verify on this route and produce the evidence manifest with mobile and desktop CWV results.

Use `fe-performance` when a CWV target fails or an asset-budget category needs diagnosis and remediation.
