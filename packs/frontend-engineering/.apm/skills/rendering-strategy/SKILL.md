---
name: rendering-strategy
description: Select and implement the correct rendering model (CSR/SSR/SSG/ISR/RSC) for each route based on data-access patterns, performance targets, and personalization requirements.
---

# Skill: rendering-strategy

Load this skill when selecting or auditing the rendering architecture of a
route or surface. Do not load it for routine component authoring — the
rendering model of a surface is already decided during component work.
Load `rendering-strategy` when:

- Designing the rendering architecture for a new product or surface
- Auditing an existing surface's rendering choices for CWV or caching problems
- Deciding how to handle a new route type that doesn't fit the current pattern
- Debugging a TTFB or caching anomaly that traces back to rendering mode

---

## Rendering model decision framework

| Model | When to use | CWV profile | Data pattern | Personalization | Key tradeoffs |
|---|---|---|---|---|---|
| **SSG** (Static Site Generation) | Content that does not change per-request and has no per-user customization | Best LCP (CDN-served HTML) | Build-time fetch; no runtime data | None — same HTML for all users | Stale content between builds; rebuild required for updates |
| **ISR** (Incremental Static Regeneration) | Mostly static content that updates periodically (docs, blogs, product listings) | Near-SSG (CDN with TTL) | Build-time + periodic revalidation | None (or edge-level A/B only) | Stale window between revalidations; `stale-while-revalidate` semantics |
| **SSR** (Server-Side Rendering) | Content that must be fresh per-request; authenticated content; content that varies by request parameters | Good LCP if TTFB is fast; INP depends on JS payload | Runtime fetch on every request | Full — user-specific HTML | TTFB cost per request; harder to cache; scales with traffic |
| **CSR** (Client-Side Rendering) | Highly interactive, authenticated surfaces where SEO is not a requirement and data updates continuously | Poor LCP on slow networks; INP good after load | Client-side fetch after hydration | Full — all data fetched client-side | Bad LCP; no SEO; blank initial HTML |
| **RSC** (React Server Components) | Surfaces mixing static and dynamic content in the same component tree | LCP as good as SSR for server components; INP reduced by smaller client bundle | Server components fetch at render time; client components hydrate independently | Partial — server components can be personalized; only interactive shells hydrate | Framework-specific; requires React 18+; mental model cost |

---

## The three wrong defaults to avoid

**Wrong default 1 — SSR everything:**
SSR incurs a per-request server render. For marketing pages, documentation,
and product listings that don't change per-user, SSR defeats caching and
increases TTFB unnecessarily. Use SSG for static content; ISR for content
that updates periodically.

**Wrong default 2 — CSR everything:**
CSR sends a mostly-empty HTML document and requires JS execution before any
meaningful content is visible. On slow networks or low-end devices, this
produces poor LCP and a blank page during load. CSR is appropriate for
authenticated, highly interactive surfaces (dashboards, editors) where
SEO is not a requirement.

**Wrong default 3 — SSG without ISR for updated content:**
SSG with no revalidation strategy means users see stale content until the
next full build and deploy. For content that updates more than once per
deploy cycle, ISR or SSR is the correct model.

---

## Hydration cost

Hydration is the process of attaching JS event listeners to server-rendered
HTML. It is a main-thread cost that runs after the HTML is painted.

**Why it matters for INP:** a page that is fully SSR-rendered but ships 400KB
of JS to hydrate still has poor INP during the hydration window. The user can
see the page but interactions may not respond until hydration completes.

**The islands pattern** is the preferred solution: only components that are
truly interactive ship client-side JS; static content ships as plain HTML with
no JS overhead. An island is a self-contained interactive component embedded
in a static HTML context.

**When full-page hydration is acceptable:** highly interactive surfaces
(text editors, spreadsheets, complex forms) where nearly every element is
interactive — the islands savings are minimal and the complexity of selectively
hydrating is not worth it.

---

## Edge cases

**Authenticated routes:**
- CSR or SSR — never SSG. A static page cannot be per-user.
- Prefer CSR for dashboards and tools where SEO is not a requirement and
  interaction density is high.
- Prefer SSR for authenticated pages where the initial content (e.g., a
  profile summary) should be visible immediately without a loading state.

**Real-time data:**
- SSR with streaming (if the framework supports it) for content that needs to
  be fresh on every request but can begin rendering before all data is available.
- CSR with `stale-while-revalidate` (SWR/React Query pattern) for data that
  can show a cached state immediately and update in the background.

**Marketing pages:**
- SSG always. Marketing pages must have fast LCP (CDN-served HTML), must be
  SEO-indexed, and their content does not change per-user. There is no reason
  to use SSR or CSR for a marketing page.

**Documentation:**
- SSG with ISR for edited content. Documentation is static (SSG is right) but
  may be edited frequently without a full site rebuild (ISR solves this).
  Verify the ISR TTL matches the acceptable staleness window for the content.

---

## Framework-agnostic language

This skill names concepts, not framework APIs. Map each concept to the
framework used in the project:

| Concept | Example framework implementations |
|---|---|
| SSG | Next.js `generateStaticParams` + no `revalidate`, Astro static output, Nuxt `routeRules: { prerender: true }` |
| ISR | Next.js `revalidate: N` in `fetch()`, Astro on-demand rendering with cache headers |
| SSR | Next.js default server component, SvelteKit `load()`, Remix `loader` |
| CSR | Any SPA (Vite + React, Nuxt client-side, Astro client components) |
| RSC | Next.js App Router server components (React 18+) |
| Islands | Astro component islands, Qwik resumability, Eleventy + Alpine |

The decision framework above applies regardless of which framework implements it.
