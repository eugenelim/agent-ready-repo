# Performance targets quick reference

Core Web Vitals targets and asset budgets for frontend surfaces.

## Core Web Vitals (CWV)

Targets at p75, evaluated separately for mobile and desktop where field data exists. Measure using Lighthouse, Chrome DevTools Performance panel, or WebPageTest.

| Metric | Target | Percentile | What it measures |
|---|---|---|---|
| **LCP** (Largest Contentful Paint) | ≤2.5s | p75 | When the main content appears — perceived load speed |
| **INP** (Interaction to Next Paint) | ≤200ms | p75 | How fast the page responds to interactions — responsiveness |
| **CLS** (Cumulative Layout Shift) | ≤0.1 | p75 | How much content moves unexpectedly — visual stability |

**Mobile and desktop:** measure both where field data (Chrome User Experience Report / CrUX) is available. Lab data (Lighthouse) is a proxy; field data is the source of truth for public production surfaces.

**What each metric tells you:**
- LCP above 2.5s: the page feels slow to load. Common causes: large hero images, render-blocking resources, slow server response, no preloading for critical resources.
- INP above 200ms: the page feels sluggish to use. Common causes: long JavaScript tasks on the main thread, layout thrashing, synchronous third-party scripts.
- CLS above 0.1: content jumps during load. Common causes: images without explicit dimensions, late-loading ads or embeds, web fonts causing FOIT/FOUT, dynamically injected content above existing content.

---

## Asset budgets by surface type

Budgets are starting points — adjust for your audience's network conditions and device capability. The seven asset budget categories to track: JS budget, images budget, fonts, third-party scripts, hydration, route-level loading, and long tasks.

### Marketing surface (public, performance-critical)

| Budget category | Target | Notes |
|---|---|---|
| JS | ≤150KB (compressed) per route | Aggressively code-split; defer analytics until after first interaction |
| images | ≤500KB per route (above-fold critical path) | WebP/AVIF; responsive `srcset`; lazy-load below-fold images |
| fonts | ≤100KB | Self-host; subset; `font-display: optional` for non-critical fonts |
| third-party scripts | ≤50KB, deferred | Facade heavy embeds (chat widgets, video); audit quarterly |
| hydration | Minimal or none (static preferred) | Use partial hydration or islands architecture |
| route-level loading | ≤50KB JS per route chunk | Each route independently cacheable |
| long tasks | 0 on initial load; ≤2 on interaction | Break up with `scheduler.yield()` |

### SaaS workspace (authenticated, interaction-heavy)

| Budget category | Target | Notes |
|---|---|---|
| JS | ≤300KB (compressed) initial; ≤100KB per route | Route-level code-splitting; tree-shake aggressively |
| images | ≤1MB per route | Lazy-load below-fold; use `loading="lazy"` |
| fonts | ≤150KB | Include weights actually used; subset by language |
| third-party scripts | ≤100KB, async | Only analytics essential; defer feature-flag SDKs |
| hydration | ≤50KB per component tree | Measure Time to Interactive delta per route |
| route-level loading | ≤100KB JS per route chunk | Prefetch likely-next routes after idle |
| long tasks | ≤5 per route | Profile with Chrome DevTools; target main-thread idle >50ms |

### Dashboard / analytics surface

| Budget category | Target | Notes |
|---|---|---|
| JS | ≤400KB (compressed) — chart libraries are large | Lazy-load chart libraries per panel |
| images | ≤500KB per dashboard | Use SVG for icons; rasterize only photography |
| fonts | ≤100KB | Monospace font for data tables; subset numerals |
| third-party scripts | ≤50KB | Avoid third-party analytics SDKs in embedded dashboards |
| hydration | ≤100KB per panel | Islands pattern preferred for data panels |
| route-level loading | ≤150KB per dashboard view | Panel-level code-splitting |
| long tasks | ≤3 per render | Virtual scrolling for large tables; async data processing |

### Documentation site

| Budget category | Target | Notes |
|---|---|---|
| JS | ≤100KB | Search and syntax highlighting only; no SPA routing |
| images | ≤300KB per page | Screenshots and diagrams; lazy-load below-fold |
| fonts | ≤80KB | Subset Latin; include only weights needed for prose + code |
| third-party scripts | ≤30KB | Minimal analytics; no heavy third-party widgets |
| hydration | 0 preferred | Static pages; no client-side hydration required |
| route-level loading | N/A (static) | Pre-generate all routes at build time |
| long tasks | 0 | Pure reading surface; no interactivity-heavy components |

---

## How to measure

```bash
# Lighthouse (local, lab data)
npx lighthouse https://example.com --output json --output-path ./lh-report.json

# Web Vitals (in-browser, real user measurement)
import {getLCP, getINP, getCLS} from 'web-vitals';
getLCP(console.log);
getINP(console.log);
getCLS(console.log);
```

Record results in the evidence manifest under `perf result`, including separate mobile and desktop values where available.

---

## Cross-reference

These targets are declared in the `frontend-engineering` skill under `## Performance targets`. See `### Mode: verify` for how to record results in the evidence manifest.
