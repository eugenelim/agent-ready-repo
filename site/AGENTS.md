# AGENTS.md — `site/` (MkDocs documentation site)

The documentation site served at `/docs/`, built with MkDocs Material.
Source files live in `docs/guides/` at the repo root; `make site-sync`
copies them to `site/docs/` before the build.

## Mobile viewport

MkDocs Material handles responsive layout automatically. Do not add a custom
viewport meta — the theme owns it.

**What to verify on every change:** Open the rendered page at a 375 px width
(browser dev-tools device emulation) and confirm no code block or table causes
horizontal scroll of the page body. Code blocks scroll internally — that is
intentional and correct.

## Broken links

Run `mkdocs build --strict --config-file site/mkdocs.yml` (or `make build-check`)
before committing. In strict mode, any broken link or unresolved anchor is a
build error.

**Anchor slugging rule.** MkDocs slugifies headings by stripping non-word
characters and collapsing whitespace/hyphens into a single `-`. The heading
`## Roll up to program / value stream level` becomes
`#roll-up-to-program-value-stream-level` (single hyphen around `/`), not
`#roll-up-to-program--value-stream-level` (double hyphen). Verify anchors
against the actual heading text before linking.

## Navigation cohesion

Every file under `docs/guides/<pack>/` must appear in the `nav:` section of
`site/mkdocs.yml`. Files missing from nav are reachable by direct URL but are
not discoverable through navigation — treat that as a broken surface.

When adding a guide file, add a nav entry in the same PR.
