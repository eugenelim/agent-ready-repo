# Verification record

Verified 2026-08-12 against the authored sources in this change.

## Passed

- `README.md` is 65 lines; the negative-content check found no testimonial,
  all-packs table, adapter matrix, full three-loop walkthrough, or adopt-by-fork
  instruction.
- `workspace.toml` parses with Python `tomllib`; Wave 8 is archived, this spec
  is shipped, and the Wave 6–9 dependency chain retains its future work.
- `python3 tools/validate_guides.py` exits 0 with 0 errors. Its 161 frontmatter
  migration warnings are pre-existing corpus-wide warnings rather than failures.
- `python3 tools/check-guide-index.py` exits 0 and confirms direct guide-home
  coverage for all 20 active packs.
- `python3 tools/test_check_guide_index.py` exercises successful and missing-pack
  exit codes and rejects links that are not direct guide-home routes.
- `python3 tools/test_catalogue_navigation.py` confirms all 20 active packs have
  an outcome, both marketing surfaces import the shared map, role anchors
  resolve, and the guide and technical-doc entry pages retain the seven outcome
  labels.
- `python3 tools/test_documentation_entry_links.py` resolves the edited
  README, contribution, guide, technical-doc, architecture, and spec links
  against authored local files, source-backed GitHub Pages docs routes,
  source-backed marketing routes, and homepage anchors.
- `python3 tools/test_build_site_link_rewrites.py` confirms mirrored
  same-directory, parent-index, cross-pack, frontmatter-slug, and
  contributing-to-guide links become base-qualified technical-doc routes rather
  than nesting under the current rendered page. Its corpus case rewrites every
  guide plus `CONTRIBUTING.md` and confirms every emitted technical-guide link
  resolves to a canonical projected route.
  The same suite confirms guide route metadata rejects `..`, non-guide paths,
  and non-string slugs before frontmatter can influence generated routes.
- `ruff check --no-cache tools/build-site.py tools/check-guide-index.py
  tools/test_check_guide_index.py tools/test_catalogue_navigation.py
  tools/test_documentation_entry_links.py tools/test_build_site_link_rewrites.py`
  exits 0.
- `git diff --check` exits 0.
- The complete writable build (`make site-build`) succeeds. A generated-HTML
  crawl resolves 3,098 internal links and fragments across the 12 changed entry,
  contributor, catalogue, core, changelog, and immediate Get Started pages with
  zero failures.
- The same whole-site crawl checked 53,871 internal links across 263 pages and
  isolated 67 older failures in unchanged pages (60 legacy-guide, 7 other).
  Their source remediation plus a rendered-link CI gate is captured atomically
  as `rendered-site-link-debt`; they are not represented as regressions or as
  passed by this change.
- The complete catalogue grid remains data-driven through
  `getCollection('packs')`; the editorial outcome maps do not replace it.
- Homepage and catalogue outcome membership, role routes, and anchors share
  `web/src/lib/catalogue-navigation.ts`; the two surfaces cannot silently assign
  different packs to the same outcome.
- The catalogue grid routes to pack detail pages without duplicating install
  commands; those mechanics remain at the detail layer.
- Contextual journey links remain in loop and pack surfaces after Journeys was
  removed from primary navigation.

## Environment-blocked

- `python3 tools/build-site.py --dry-run` is not currently side-effect-free: it
  attempts to create `docs-site/src/content/docs/packs` before route generation,
  and this workspace rejects that write. The defect is captured as
  `build-site-dry-run-write-free` in the repository backlog.
- Full marketing and technical-site builds required user-run generated-output
  writes; the user completed the final build successfully and the rendered
  output was audited afterward.
- Pytest cannot initialize because its output capture asks `tempfile` for a
  writable directory. The pure-stdlib construction suites run directly instead;
  they pass.
- Browser-based responsive and visual QA is unavailable because this session
  exposes no browser-control runtime.

The blocked gates are not represented as passed. Source-level route, anchor,
inventory, syntax, lint, and link checks cover the changed navigation contract.
