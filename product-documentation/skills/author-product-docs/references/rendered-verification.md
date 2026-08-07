# Rendered verification

Proportionate verification rules by change type. Only claim a check passed if it actually ran.

## Verification levels

### Level 1 — Content-only edits

Applies when: body copy, prose, or examples changed without altering navigation, file structure, or page layout.

Required checks:
- Link check: every link in the changed file resolves (file exists, or external URL responds).
- No broken internal references: relative links point to files that exist.
- Canonical sources verified: product claims match what the skill sources actually say.

How to run:
```bash
grep -oE '\[.*?\]\((.*?)\)' <file> | grep -v '^http' | while read link; do
  target=$(echo "$link" | sed 's/.*(\(.*\))/\1/')
  [ -f "$target" ] || echo "BROKEN: $target"
done
```

### Level 2 — Navigation changes

Applies when: a new file is added to the guide tree, a file is renamed, or an index/README is updated.

Required checks (in addition to Level 1):
- Guide index updated: if a new guide was added, the parent `README.md` or index links to it.
- Pack README updated: if the new guide changes the pack's primary entry path, the pack README is updated.
- No orphaned files: every new file is reachable from at least one index or cross-link.

### Level 3 — Page-layout changes

Applies when: section structure, heading hierarchy, or page scaffolding changes (not just prose).

Required checks (in addition to Level 2):
- Build the docs-site or web locally and inspect the rendered page.
- Heading hierarchy is valid (no skipped levels, no duplicate `#` titles).
- Table of contents (if auto-generated) renders correctly.

### Level 4 — Rendered site verification

Applies when: routes change, redirects are added, or site configuration is updated.

Required checks (in addition to Level 3):
- All routes that previously existed still resolve (no 404s).
- Old routes that should redirect do redirect.
- New routes are accessible.
- Run `make build` or equivalent; inspect the built output, not just the source.

### Level 5 — Accessibility and responsive behavior

Applies when: layout components are changed in the rendering system.

Required checks (in addition to Level 4):
- Main content is readable without JavaScript (where applicable).
- Color contrast meets WCAG 2.1 AA minimums.
- Interactive elements are keyboard-accessible.

This level is typically out of scope for documentation authoring and is the rendering system maintainer's responsibility. Note it as a known limitation when docs changes affect rendered layout.

---

## Source-versus-rendered drift

When `web/` or `docs-site/` renders content from `guides/`:
- The source file is `guides/<pack>/<kind>/<slug>.md`.
- Editing the rendered output (e.g., a built HTML file or a generated Astro page) does not fix the source.
- Always edit the canonical source and let the build regenerate the rendered output.

Reporting "verified against rendered output" requires that the renderer was actually run. If the renderer was not run, report "verified against source; rendered output not checked" instead.
