# Spec: Docs-site print chrome suppression

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A reader who prints or saves a documentation page as PDF gets the page's content
and nothing else. The docs footer's Product / Docs / Project link groups are
visible on screen and absent from paper, so no printed documentation page
consists solely of navigation links. The copyright line, the page's own content,
and screen rendering at every viewport are unchanged.

Success is observable from the printed artifact: on the five documentation routes
the print audit measures, no page of a printed document consists solely of
navigation chrome, and each document's last page is content or the quiet
copyright line.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Suppress print chrome in the same stylesheet origin that sets the element's
  `display`, so the rule wins without depending on stylesheet link order.
- Verify print behaviour in a real browser under `emulateMedia({ media: 'print' })`
  at the printable width (717 CSS px for A4 portrait with 0.4in margins), never
  from source inspection or a DOM-only assertion.
- Prove every new print guard by mutation: remove the rule it guards, observe the
  guard fail, restore, observe it pass.
- Place a new browser assertion inside a spec file the CI gate already runs.

### Ask first

- Suppressing in print any element beyond the docs footer's link groups.
- Changing what the docs footer *emits*, as opposed to what it paints on paper —
  emission is `site-shared-chrome`'s contract (AC4).
- Any print rule that targets marketing (`web/`) rather than docs (`docs-site/`).
- Moving any `docs-site` rule into a CSS cascade layer. The custom sheet is
  deliberately unlayered, and layering an override component silently demotes its
  `:focus-visible` rules below it.
- Using `!important` to make `print:hidden` authoritative site-wide. It works,
  and it generalises past the demonstrated boundary this spec voluntarily
  adopts from the print audit's `shape` bar.

### Never do

- Add a new module boundary, top-level directory, dependency, or build step for
  this behaviour. It is one `@media print` block in an existing stylesheet.
- Modify vendored `docs-site/node_modules/@astrojs/starlight` components.
- Suppress anything in print that carries document content rather than
  navigation chrome.
- Assert print behaviour in `web/src/test/rendered-output.test.ts`. That suite
  runs under jsdom, which cannot resolve a cross-stylesheet print cascade; an
  assertion there passes on broken output.
- Rely on Starlight's `print:hidden` utility to suppress an element whose own
  unlayered component rule sets `display`. The utility loses that contest.

## Testing Strategy

Every acceptance criterion below names its mode.

- **AC1, AC2 — goal-based, exercised by an E2E test.** Print suppression only
  exists once a real engine resolves the cascade under print media, so it is
  unprovable below the browser boundary. One case reads
  `getComputedStyle(el).display` under both media on a built, served docs route.
- **AC3 — goal-based.** A guard in no enforced command is decoration. Checked by
  running the gate command and finding the new case named in its reporter output
  — not merely by reading `web/package.json` and the pin, which would be true the
  instant the file is edited and so could not fail independently of AC1.
- **AC4 — manual QA, recorded once.** Mutation proof is a gesture with an
  observed outcome, and its record is an artifact a reviewer can re-read. The
  rebuild between states is part of the gesture: the gate serves `build/`, so a
  mutation without a rebuild proves nothing and reports green.
- **AC5 — manual QA.** PDFs are generated for the five documentation routes and
  inspected; page-level composition is not derivable from the DOM.
- **AC6 — goal-based (grep) plus the existing TDD suite.** Absence of the print
  assertions and of the inert class is greppable; the emission assertions that
  remain are the existing suite's.
- **AC7 — goal-based, two checks.** The gate command is green or it is not; and
  a grep confirms `docs/guides/how-to/verify-a-site-release.md` describes the
  gate as the matrix plus the print case. The documentation half needs its own
  check because a green gate says nothing about the guide's wording.
- **AC8 — goal-based (grep).** The trap text is present in `docs-site/AGENTS.md`.

## Acceptance Criteria

- [x] Given a built docs route under print media at 717×900, when
      `.docs-site-footer__groups` is measured, its computed `display` is `none`.
- [x] Given the same route under screen media at 717×900, when the same element
      is measured, its computed `display` is `grid`.
- [x] The AC1 and AC2 assertions live in `web/src/test/e2e/site-quality-gate.spec.ts`,
      a file `npm run test:e2e:gate --prefix web` already runs, so they execute in
      CI without changing `tools/test-pages-workflow.py:96`'s gate-script pin or
      `tools/test_browser_gate_subset.py:341,365,375`'s matrix constants; the gate
      run reports the new case by name.
- [x] The AC1 assertion is mutation-proved: with the `@media print` rule removed
      **and the site rebuilt** (`python3 tools/build-site.py` → `npm run build
      --prefix web` → `npm run build --prefix docs-site`, because the gate serves
      `build/`) it fails reporting `grid`; with the rule restored and the site
      rebuilt again it passes. Both outcomes, including the rebuild between them,
      are recorded in
      `docs/specs/docs-site-print-chrome-suppression/notes/mutation-proof.md`.
- [x] Printed output for the five documentation routes contains no page
      consisting solely of navigation chrome; each document's final page is
      content or the copyright line.
- [x] `docs-site/src/components/Footer.astro` carries no `print:hidden` class,
      and `web/src/test/rendered-output.test.ts` contains no assertion about
      print behaviour; its existing shared-chrome emission assertions pass.
- [x] `npm run test:e2e:gate --prefix web` is green — the 60-case matrix is
      unchanged and passing, and the added 717px print case passes alongside it.
      `docs/guides/how-to/verify-a-site-release.md` describes the gate as that
      matrix plus the print case.
- [x] `docs-site/AGENTS.md` records, under its action-changing traps, three
      things: that `print:hidden` does not suppress an element whose own unlayered
      component rule sets `display`; that layering a `docs-site` rule to win that
      contest demotes the component's `:focus-visible` offset; and that
      `docs-site` now carries one `@media print` rule, naming `Footer.astro` as
      its location — so a reader who finds "no print CSS from this programme" in
      the frozen `notes/print-audit.md` is corrected at the point of use.

## Assumptions

- Technical: `.docs-site-footer__groups` and `.print\:hidden` both resolve to
  specificity `(0,1,0)` — Astro's `:where()` component scoping contributes
  nothing — and both are unlayered, so the tie falls to link order and the print
  sheet is linked first (source: emitted `build/docs/_astro/*.css`; browser probe
  reporting `display: grid` under print media)
- Technical: `docs-site` custom CSS is deliberately unlayered so it outranks
  Starlight's layered styles (source:
  `docs-site/src/styles/starlight.css:8-9`; ratified at
  `docs/specs/docs-site-design-refresh/plan.md:32`). This spec preserves that
  premise; the `@media print` rule sits in the same unlayered origin.
- Technical: layering an override component's `<style>` would demote its
  `:focus-visible` rule — `Footer.astro:80` and `PageFrame.astro:208` set
  `outline-offset: 3px` at `(0,2,0)` and would lose to
  `docs-site/src/styles/starlight.css:589`'s unlayered `(0,1,0)` `2px` — and
  `web/src/test/e2e/quality-assertions.ts:239-246` never reads `outlineOffset`,
  so no gate would see it. This is why layering is barred under *Ask first*.
- Technical: native Starlight `Pagination` is unaffected — its rules sit in
  `@layer starlight.core`, so the unlayered utility outranks them and it hides
  correctly in print (source: browser probe replicating the emitted cascade)
- Technical: `web/src/test/rendered-output.test.ts` runs under jsdom (source:
  `web/vitest.config.ts:5`), which is why print assertions belong elsewhere; the
  `JSDOM` import is at `web/src/test/rendered-output.test.ts:25`
- Technical: `test:e2e:gate` is pinned to an explicit two-file allowlist because
  the excluded specs write PNGs into tracked paths (source:
  `tools/test-pages-workflow.py:93-96`), so a new assertion joins an existing
  pinned spec file rather than adding a third
- Technical: the gate's 60-case matrix is eight marketing routes × five widths
  plus two docs routes × five widths × two themes (source:
  `web/src/test/e2e/site-quality-gate.spec.ts:45,57`;
  `docs/guides/how-to/verify-a-site-release.md:26-28`)
- Process: no changelog entry is required; the changelog is tied to a
  released-artifact version bump and this change bumps no version (source:
  `docs/CONVENTIONS.md:935`)
- Process: no ADR is written, and no upstream Starlight issue is raised —
  Starlight's cascade design is self-consistent (source: user confirmation
  2026-08-25)
- Governance: `docs/specs/site-browser-quality-gate/notes/print-audit.md` is not
  amended and not superseded. It sits inside a Shipped spec directory, so it is
  frozen, and `docs/CONVENTIONS.md:160-165` is explicit that an append is a body edit.
  No amendment is needed either: the audit's operative sentence is scoped to
  "**this programme**", and this spec carries `Brief: none` — it is its own
  programme, authored after `tech-site-completion` closed. The audit's claims
  therefore all remain true as written, including its `close-stale` disposition,
  its six measured rows, and its `## Residual` reading of surviving chrome, which
  was accurate on the axes it measured (source: `docs/CONVENTIONS.md:104,160-165`;
  user confirmation 2026-08-25)
- Governance: the observed failure would satisfy all five of the audit's `shape`
  requirements — an exact failing row, the smallest necessary rule, construction
  proof reproducing the failure, post-remediation browser evidence, and an
  independently shippable owning spec. The `shape` bar is therefore what *shaped*
  this rule, and it is why the fix is one selector in one file rather than an
  authoritative utility. It is not invoked as a disposition, because this is not
  that programme's audit to re-dispose.
- Governance: the two print debt slugs this failure sits near were both closed on
  2026-08-25, in a separate change outside this spec's scope.
  `print-audit-page-break-quality` was closed on owner review of regenerated
  print evidence; that same review found this spec's defect and carved it out
  here. `print-chrome-paint-inventory` was retired won't-do under an explicit
  owner ruling, which was needed because removing its `(deferred:)` marker from a
  frozen spec has no licensed path in `CONVENTIONS.md`. This spec discharges
  neither and depends on neither — it owns exactly the one carved-out defect, and
  it establishes no paint-level oracle and measures no break quality (source:
  `workspace.toml [backlog].closed`;
  `docs/specs/site-browser-quality-gate/spec.md` Status line).
- Governance: `site-shared-chrome` (Shipped) AC4 constrains what the footers
  *emit*; print visibility is outside it, so AC4 continues to hold (source:
  `docs/specs/site-shared-chrome/spec.md:177`)
- Product: printing docs pages has no named persona in the repository; the audit
  treats print as a quality surface without naming a user, and this spec inherits
  that framing (source:
  `docs/specs/site-browser-quality-gate/notes/print-audit.md`)
- Correction (2026-08-25): two earlier drafts of this spec named different fixes
  — a global `!important` on `.print\:hidden`, then a cascade-layer wrapper on the
  three override components — and one claimed `.pagination-links` as a second
  collision site. All were wrong. Pagination is layered and already correct; the
  layer wrapper would have silently degraded focus indicators; and the audit's
  own "smallest necessary rule targeting only the demonstrated failing boundary"
  bar described the correct fix from the outset. No implementation was written
  under any of the drafts; the two uncommitted edits present in the worktree —
  the `print:hidden` class on `Footer.astro:21` and two print assertions in
  `web/src/test/rendered-output.test.ts` — predate this spec and are undone by
  T1 and T2.
