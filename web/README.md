# web/ — Astro marketing site

The platform-site marketing anchor, served at `/`. See [`AGENTS.md`](AGENTS.md)
for dependencies, the build contract (`npm run build` emits into `../build/`, not
`dist/`), and the Astro-before-MkDocs build order. Design and content are governed
by [`docs/specs/platform-site/`](../docs/specs/platform-site/spec.md); the
directory was approved by [RFC-0061](../docs/rfc/0061-web-top-level-directory.md).

```sh
npm install          # once
npm run dev          # local dev server at http://localhost:4321
npm run build        # static build into ../build/
```
