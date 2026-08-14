# Spec: rendered-site-link-debt

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Every internal link and fragment in the complete generated marketing and
technical-documentation site resolves to an emitted page and anchor. The
recorded `documentation-entry-navigation` failure corpus is corrected at its
authored source or owning projection rule, and a deterministic generated-HTML
audit prevents the site from publishing new unresolved internal targets.

## Boundaries

### Always do

- Reproduce and classify the recorded failures before changing their sources.
- Correct authored guide content or the projection rule that owns generated
  content; never treat generated output as the canonical fix.
- Build the marketing site before the technical docs, then audit the combined
  `build/` tree after both builds complete.
- Keep remediation and enforcement atomic so the new gate is green when it
  first becomes required.
- Keep the checker pure-stdlib Python and deterministic across supported local
  and Pages build environments.

### Ask first

- Any published-route move, redirect policy, or link exclusion not already
  represented by a non-navigational scheme such as `mailto:` or an external URL.
- Any correction that changes a guide's product meaning rather than its route or
  fragment target.
- Any gate placement outside the existing site-build and Pages publication path.

### Never do

- Enable a required gate while any in-scope generated internal link or fragment
  remains unresolved.
- Silence failures with a broad allowlist, page-directory exclusion, or
  fragment-check bypass.
- Add a dependency, new top-level directory, or alternate site build pipeline.
- Fold `build-site-dry-run-write-free`, `catalogue-package-guides`, or unrelated
  navigation cleanup into this slice.
- Create a dependency on `m6-live-demo-guide` or modify `ini-008` or any
  work-intake artifact.

## Testing Strategy

- **Checker behavior: TDD.** Pure-stdlib unit tests cover page-route resolution,
  directory indexes, root-relative and relative links, query stripping,
  percent-decoding, fragments, duplicate anchors, external and non-navigation
  schemes, malformed HTML, and deterministic diagnostics. These are compact
  invariants with clear failing examples.
- **Complete site: goal-based end-to-end check.** `make site-build` produces the
  combined tree and the checker scans every emitted HTML file. Success means
  zero unresolved internal page or fragment targets; a missing target produces
  a non-zero exit and names its source, href, and resolved target.
- **Source ownership and gate wiring: goal-based checks.** Focused tests and diff
  inspection prove each correction lands in an authored source or projection
  rule and that Pages runs the audit after both builds and before artifact upload.

## Acceptance Criteria

- [x] **AC1.** A remediation inventory accounts for the recorded 67 failures
  across the 53,871-link, 263-page crawl: 60 originate in the legacy guide
  corpus and 7 in other unchanged pages. If the rebuilt baseline has drifted,
  the inventory reconciles every addition, removal, and changed target rather
  than forcing the historical count.
- [x] **AC2.** Every current failure in that inventory is corrected at the
  authored source or owning projection rule; no generated output is the sole
  location of a fix.
- [x] **AC3.** A pure-stdlib checker at
  `tools/check-rendered-site-links.py` accepts `--build-dir`, resolves that
  directory as the canonical build-root boundary before scanning, confines every
  discovered page and internal target to that resolved root before any target
  read, and validates internal page and fragment targets against the combined
  generated tree.
- [x] **AC4.** The checker resolves relative links, root-relative links with and
  without the configured GitHub Pages base, directory-index routes, encoded
  path components, query strings, and fragments; it ignores external URLs and
  explicitly non-navigational schemes without hiding malformed internal links.
- [x] **AC5.** The checker exits 0 with a deterministic summary when no failures
  exist, exits 1 for broken internal targets with one stable diagnostic per
  source/href/target, and exits 2 for invalid invocation or an unreadable or
  structurally invalid build tree.
- [x] **AC6.** Focused tests in `tools/test_check_rendered_site_links.py` cover
  successful and failing page/fragment cases, Pages-base normalization, path
  confinement including traversal and symlink escape attempts, deterministic
  ordering, and exit-code behavior without requiring Node or a production site
  build.
- [x] **AC7.** `make site-build` followed by the rendered-link checker reports
  zero unresolved internal links or fragments across the complete combined
  marketing and technical-docs output.
- [x] **AC8.** `.github/workflows/pages.yml` runs the checker after the docs-site
  build and before `actions/upload-pages-artifact`; its path filters include the
  checker and its focused test so changes cannot bypass the Pages job.
- [x] **AC9.** The local site-build path exposes the same audit through a named
  Make target or the existing `site-build` target, and the focused checker tests
  are part of the repository's site/documentation test gate.
- [x] **AC10.** No allowlist, page subtree exclusion, published-route move, new
  dependency, or unrelated backlog remediation is introduced.
- [x] **AC11.** `docs/specs/README.md` contains a row for this spec whose status
  matches this file's current lifecycle status.

## Assumptions

- Technical: AC1 is the canonical baseline for the recorded whole-site failure
  corpus (source:
  `docs/specs/documentation-entry-navigation/notes/verification.md`).
- Technical: the canonical combined build runs the marketing Astro build first
  and the Starlight docs build second into `build/` (source: `Makefile` and
  `.github/workflows/pages.yml`).
- Technical: new scripts under `tools/` are pure-stdlib Python (source:
  `AGENTS.md` § New tool scripts).
- Product: remediation and the generated-output gate form one atomic slice; the
  gate never lands red (source: `workspace.toml` rendered-site-link-debt comment;
  user confirmation 2026-08-13).
- Process: this is full-mode implementation work because it adds required CI
  enforcement across a published documentation surface (source: `AGENTS.md` §
  How we work; user confirmation 2026-08-13).
- Process: the slice has no dependency on `m6-live-demo-guide` and leaves
  `ini-008` and work-intake files untouched (source: user confirmation
  2026-08-13).
