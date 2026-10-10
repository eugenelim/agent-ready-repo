# Rendered verification

Proportionate verification rules by change type. Only claim a check passed if it actually ran.

## Verification levels

### Level 1 — Content-only edits

Applies when: body copy, prose, or examples changed without altering navigation, file structure, or page layout.

Required checks:
- Link check: every link in the changed file resolves (file exists, or external URL responds).
- No broken internal references: relative links point to files that exist.
- Canonical sources verified: product claims match what the product's source actually says.
- Surface checks: the docs match what ships. Compare documented commands with `--help` output; compare documented endpoints with the contract file; compare documented settings with the config schema. In a repository the user has said to trust, also run the examples or the repository's doc tests (the trust rule lives in Step 15 of the skill). [`surface-discovery.md`](surface-discovery.md) lists the check for each surface type.

How to check links: resolve each relative link against the directory of the file that contains it, and check each link separately. Skip absolute URLs, or check them with an HTTP request. When the repository has its own link checker, use it.

### Level 2 — Navigation changes

Applies when: a new file is added to the docs tree, a file is renamed, or an index/README is updated.

Required checks (in addition to Level 1):
- Docs index updated: if a new guide was added, the parent index or landing page links to it.
- README updated: if the new guide changes the product's primary entry path, the README is updated.
- No orphaned files: every new file is reachable from at least one index or cross-link.

### Level 3 — Page-layout changes

Applies when: section structure, heading hierarchy, or page scaffolding changes (not just prose).

Required checks (in addition to Level 2):
- In a trusted repository, build the docs site with the repository's own command and inspect the rendered page; otherwise report "rendered output not checked".
- Heading hierarchy is valid (no skipped levels, no duplicate `#` titles).
- Table of contents (if auto-generated) renders correctly.

### Level 4 — Rendered site verification

Applies when: routes change, redirects are added, or site configuration is updated.

Required checks (in addition to Level 3):
- All routes that previously existed still resolve (no 404s).
- Old routes that should redirect do redirect.
- New routes are accessible.
- In a trusted repository, build the docs site with the repository's own command and inspect the built output, not just the source.

### Level 5 — Accessibility and responsive behavior

Applies when: layout components are changed in the rendering system.

Required checks (in addition to Level 4):
- Main content is readable without JavaScript (where applicable).
- Color contrast meets WCAG 2.1 AA minimums.
- Interactive elements are keyboard-accessible.

This level is typically out of scope for documentation authoring and is the rendering system maintainer's responsibility. Note it as a known limitation when docs changes affect rendered layout.

---

## Source-versus-rendered drift

When a docs site renders content from source files:
- The source is the repository's docs build and the source files it reads.
- Editing the rendered output (for example a built HTML file or a generated page) does not fix the source.
- Always edit the canonical source and let the build regenerate the rendered output.

Reporting "verified against rendered output" requires that the renderer was actually run. If the renderer was not run, report "verified against source; rendered output not checked" instead.
