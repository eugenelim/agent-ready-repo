# AGENTS.md — `web/` (Astro marketing site)

The platform-site marketing anchor, served at `/`. Approved as a new top-level
directory by [RFC-0061](../docs/rfc/0061-web-top-level-directory.md); scope,
content, and aesthetics are defined by the
[platform-site spec](../docs/specs/platform-site/spec.md).

## Dependencies (recorded per repo AGENTS.md § "Check before acting")

This directory introduces the repo's first Node.js build toolchain. New
dependencies are recorded here before they are added.

| Dependency | Version | Why |
| --- | --- | --- |
| Node.js | `>=24.0.0` (see `package.json` `engines`) | Astro build/runtime toolchain |
| [`astro`](https://astro.build) | pinned `7.1.0` (exact, not a range) | Static-site generator for the marketing pages; pinned for reproducible CI |
| [`@astrojs/sitemap`](https://docs.astro.build/en/guides/integrations-guide/sitemap/) | pinned `3.7.3` (exact, not a range) | Generates `sitemap-index.xml` + `sitemap-0.xml` at build time for SEO (Phase 4) |
| [`@fontsource-variable/inter`](https://fontsource.org/fonts/inter) | pinned `5.3.0` (exact, not a range) | Self-hosts the Inter variable font (wght 100–900), replacing the `fonts.googleapis.com` runtime call. Family registers as `'Inter Variable'` |
| [`@fontsource/jetbrains-mono`](https://fontsource.org/fonts/jetbrains-mono) | pinned `5.3.0` (exact, not a range) | Self-hosts JetBrains Mono (weights 400/500/600/700/800 — the set the components actually use) for code/mono type, replacing the `fonts.googleapis.com` runtime call |

Build-time only. This is our own site infrastructure — not a primitive or
framework prescribed to adopters (see RFC-0061's charter-neutrality analysis).
No CSS framework (Tailwind, Bootstrap, UnoCSS): the `--ds-*` token system in
`src/styles/` is the sole color/spacing authority (platform-site spec, Boundaries).

## Build

- `npm run build` emits into `../build/` (repo root), NOT `web/dist/`
  (`astro.config.ts` `outDir`).
- `astro build` cleans `outDir` on every run — Astro MUST build before MkDocs
  writes into `build/docs/`. See `.github/workflows/pages.yml`.

## Development

When starting the dev server, use background mode:

```
astro dev --background
```

Manage the background server with `astro dev stop`, `astro dev status`, and `astro dev logs`.

## Mobile viewport

The viewport meta tag (`width=device-width, initial-scale=1`) is set in
`src/components/layout/SiteLayout.astro`. Do not add it elsewhere or duplicate it.

**What to verify on every change:** check that no element causes horizontal
scroll of the page body at 375 px width. Code blocks inside `<Content />`
rendered markdown use the base `pre { overflow-x: auto }` rule — they scroll
internally, not the page.

## Links in markdown content

Links inside markdown files rendered via `<Content />` (pack and journey bodies)
**cannot** use Astro's `withBase()` — they are plain HTML after rendering.

- Use **relative paths** for cross-site links (e.g., `../../docs/guides/atlassian/`).
- Absolute paths starting with `/` are resolved against the origin root, not the
  subpath base (`/agent-ready-repo`), and will 404 on GitHub Pages.
- The `docsUrl` and `journeyUrl` frontmatter fields are the canonical navigation
  entry points and are already processed through `withBase()` by the template.

## Navigation cohesion

Every pack that has documentation must set `docsUrl` in its frontmatter. Every
pack with a journey narrative must set `journeyUrl`. These are the two navigation
entry points the pack template exposes; leave neither empty if the content exists.

## Documentation

Full documentation: https://docs.astro.build

Consult these guides before working on related tasks:

- [Adding pages, dynamic routes, or middleware](https://docs.astro.build/en/guides/routing/)
- [Working with Astro components](https://docs.astro.build/en/basics/astro-components/)
- [Adding or managing content](https://docs.astro.build/en/guides/content-collections/)
- [Adding styles](https://docs.astro.build/en/guides/styling/)
