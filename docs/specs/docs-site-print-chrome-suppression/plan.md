# Plan: Docs-site print chrome suppression

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs-site/AGENTS.md` (build order, styling
  invariants, vendored-Starlight rule); `web/AGENTS.md` (gate browser,
  preview-server daemonization, snapshot-staging rule);
  `docs/specs/site-shared-chrome/spec.md` (the docs footer's emission contract
  and its mutation-proved AC precedent, § Acceptance Criteria rows 7-9);
  `docs/specs/site-browser-quality-gate/notes/print-audit.md` (the accepted
  audit this amends, and the 717px measurement method it owns);
  `web/src/test/e2e/site-quality-gate.spec.ts` + `site-base.ts` (the pinned gate
  spec the new assertion joins, and its configuration-derived base);
  `tools/test-pages-workflow.py:93-96` (the gate-script pin and its rationale).

## Approach

One `@media print` block in `Footer.astro`, and one assertion added to a gate
spec file CI already runs.

`.docs-site-footer__groups` sets `display: grid` in `Footer.astro`'s scoped
`<style>`. Starlight's `print:hidden` utility declares `display: none` inside
`@media print`. Both compile unlayered and both resolve to `(0,1,0)` — Astro's
`:where()` scoping contributes no specificity — so the tie falls to source
order, and Astro links the print sheet first. `display: grid` wins inside
`@media print`, and the footer's navigation prints.

The fix declares the print rule in the same stylesheet origin that sets the
element's `display`, later in the same file. It wins on source order for the
same reason the bug exists, without depending on the order of *linked sheets*,
which the repository does not control.

Two alternatives were designed and discarded, both recorded in § Changelog
because each looked right and was not:

- **A global `!important` on `.print\:hidden`.** Wins, but generalises past the
  demonstrated boundary, contrary to the audit's `shape` bar.
- **A cascade-layer wrapper on the override components.** Would demote their
  `:focus-visible` rules below the unlayered custom sheet, flipping
  `outline-offset` 3px→2px across 228 docs pages — invisible to the gate, which
  never reads `outlineOffset`. It also inverts a ratified decision
  (`docs-site/src/styles/starlight.css:8-9`).

## Constraints

- One file changes for behaviour: `docs-site/src/components/Footer.astro`.
- The uncommitted `print:hidden` class on that file is reverted — under this
  approach it is inert, and an inert class that looks load-bearing is the trap
  that produced the original defect.
- No `docs-site` rule moves into a cascade layer.
- `web/` and marketing print behaviour are untouched.
- The docs footer's emitted markup returns to its `HEAD` state, so
  `site-shared-chrome` AC4 holds unchanged.

## Construction tests

**Mechanism confirmed against the real bundle, not a replication.** The fix rests
entirely on Astro preserving intra-file source order through compilation. It does:
in the emitted bundle, `Footer.astro`'s base `.docs-site-footer__groups` rule sits
at byte offset 120064 and its existing `@media` override at 121366 — the same
order as source lines 62 and 83. A separate browser probe reproduces the defect
(`grid` under print today) and clears it under the proposed rule, but the
order-preservation claim is anchored to the bundle rather than to that probe.

Note for any check written against this: the minifier rewrites media conditions
(`min-width: 50rem` becomes `width>=50rem`), so no verification may grep the
emitted CSS for the source spelling of a media query.

The load-bearing test is E2E, because print cascade resolution does not exist
below a real engine. `rendered-output.test.ts` runs under jsdom and cannot
evaluate a linked print stylesheet — an assertion there is satisfied by broken
output, which is exactly how the two currently-uncommitted assertions pass.

The assertion joins `web/src/test/e2e/site-quality-gate.spec.ts` rather than a
new file. `tools/test-pages-workflow.py:96` pins the gate script to an explicit
two-file allowlist precisely so a newly added spec cannot join required CI
silently; adding a third file would break that pin for no benefit, when the
assertion belongs beside the docs-route cases already there.

The guard is mutation-proved before it is trusted: remove the `@media print`
block, rebuild, observe the case fail reporting `grid`; restore, rebuild,
observe it pass. Both outcomes are written to
`notes/mutation-proof.md` so a reviewer can re-read them.

## Design (LLD)

### Design decisions

- **Suppress in the origin that owns the `display`.** The defect is a
  same-origin, same-specificity tie decided by link order. Declaring the print
  rule beside the rule it must beat removes the ambiguity locally, with no
  reliance on bundler output order and no effect on any other element.
- **Revert the `print:hidden` class rather than keep it.** Under this approach
  the class does nothing on that element. Keeping it would leave a second
  apparent mechanism that a future reader would trust.
- **Do not make the utility authoritative.** That is a real improvement and a
  real generalisation past the demonstrated boundary; the audit's decision rule
  bars it, and `!important` is now listed under spec Boundaries *Ask first* so
  the option is visible rather than forgotten.
- **Scope to the docs footer.** `PageFrame.astro` and `PageTitle.astro` set no
  `display` on a utility-bearing element, so they exhibit no defect. The general
  hazard is recorded as an `AGENTS.md` trap instead of pre-emptively patched.
- **Native `Pagination` is out of scope because it is not broken.** It sits in
  `@layer starlight.core`, so the unlayered utility already outranks it.

### Behavior & rules

`.docs-site-footer__groups` is `display: grid` on screen and `display: none` in
print. Nothing else changes: emitted markup, document content, focus behaviour,
and screen rendering are identical before and after.

### Failure, edge cases & resilience

- If Astro's emitted link order ever changes, this rule is unaffected — it wins
  within its own file rather than across sheets.
- If a future component sets `display` on a `print:hidden` element, it inherits
  the same defect. The `AGENTS.md` trap is the mitigation; the alternative
  (making the utility authoritative) stays available and is named in Boundaries.
- The change cannot hide content: the rule names one navigation container by
  class. The Never-do boundary at spec § Boundaries is what forbids widening it;
  no acceptance criterion is claimed to enforce that, because none does.

### Quality attributes (NFRs)

Screen rendering unchanged across the gate's 60-case matrix — eight marketing
routes × five widths, plus two docs routes × five widths × two themes (spec AC8).

## Tasks

### T1: Suppress the footer link groups in print

**Depends on:** none

**Touches:** docs-site/src/components/Footer.astro

**Tests:**
- Goal-based: after the full build, a browser probe at 717×900 under print media
  reports `display: none` for `.docs-site-footer__groups`, and `grid` under
  screen media. Verifies spec AC1 and AC2.
- Goal-based: `! grep -q 'print:hidden' docs-site/src/components/Footer.astro`.
  Stated as a grep rather than a `git diff`, which goes vacuous once the revert
  is committed. Verifies part of spec AC6.

**Approach:**
- Revert the uncommitted `print:hidden` class on line 21 so the element's markup
  matches `HEAD`.
- Add an `@media print` block to the component's existing `<style>`, after the
  `.docs-site-footer__groups` rule, declaring `display: none`.
- Comment it with the two facts a future reader needs: that `print:hidden` loses
  this contest at equal specificity on link order, and that wrapping this block
  in a cascade layer would demote the component's `:focus-visible` offset.

**Done when:** the probe reports `none` under print and `grid` under screen, and
the file's markup is identical to `HEAD`.

### T2: Add the print assertion to the pinned gate spec

**Depends on:** T1

**Touches:** web/src/test/e2e/site-quality-gate.spec.ts, web/src/test/rendered-output.test.ts, docs/specs/docs-site-print-chrome-suppression/notes/mutation-proof.md, docs/guides/how-to/verify-a-site-release.md

**Tests:**
- E2E: on a built, served docs route at 717×900 with the light theme,
  `.docs-site-footer__groups` computes `display: none` under
  `emulateMedia({ media: 'print' })` and `grid` under screen media.
  Verifies spec AC1 and AC2.
- Goal-based: the case runs under `npm run test:e2e:gate --prefix web` with
  `tools/test-pages-workflow.py:96`'s pin unchanged. Verifies spec AC3.
- Existing: `rendered-output.test.ts` shared-chrome emission assertions stay
  green with the two print assertions removed. Verifies the rest of spec AC6.

**Approach:**
- Remove the two print assertions from `rendered-output.test.ts` — the
  `classList.contains('print:hidden')` check and the emitted-CSS regex. Both are
  satisfied by broken output and neither can resolve a cascade under jsdom.
- Add the print case to `site-quality-gate.spec.ts` beside the existing
  docs-route cases, deriving its route from `site-base.ts` (`withDocsBase`),
  never a literal base. It is a standalone case at 717×900, not a member of the
  `WIDTHS` loop — `tools/test_browser_gate_subset.py:341,365` pins that array to
  five widths and `:375` asserts the matrix arithmetic equals 60, so the case
  must not join the loop or either pin breaks.
- Update `docs/guides/how-to/verify-a-site-release.md:26` so the gate is
  described as the 60-case matrix plus the print case; its current sentence
  enumerates four per-case assertions the print case does not make.
- Mutation-prove it, rebuilding between states, and write both outcomes to
  `notes/mutation-proof.md`. Verifies spec AC4.

**Done when:** the case passes inside the gate command, the mutation run fails it
reporting `grid`, the record exists, and `rendered-output.test.ts` is green.

### T3: Record the trap and regenerate print evidence

**Depends on:** T1, T2

**Touches:** docs-site/AGENTS.md

**Tests:**
- Manual QA: PDFs regenerated for the five documentation routes at A4 portrait,
  0.4in margins, scale 1, backgrounds off, light theme, 717×900; no page consists
  solely of navigation chrome. Verifies spec AC5.
- Goal-based: `npm run test:e2e:gate --prefix web` is green, and a grep confirms
  `docs/guides/how-to/verify-a-site-release.md` describes the gate as the 60-case
  matrix plus the print case. Verifies spec AC8, both halves.
- Goal-based: `grep` finds the trap text in `docs-site/AGENTS.md`. Verifies spec AC8.

**Approach:**
- Add an action-changing trap to `docs-site/AGENTS.md`: `print:hidden` does not
  suppress an element whose own unlayered component rule sets `display`, the
  failure is silent, and layering the component to win that contest demotes its
  `:focus-visible` offset below `src/styles/starlight.css`.
- Regenerate the print PDFs for the five documentation routes and read them.
- **Do not touch `notes/print-audit.md`.** It is inside a Shipped spec directory
  and therefore frozen; `docs/CONVENTIONS.md:170` counts an append as a body
  edit. No amendment is owed: the audit's statement is scoped to "this
  programme", and this spec carries `Brief: none`, so the audit stays true as
  written. An earlier draft of this task planned that append and was wrong.

**Done when:** the trap is recorded, the regenerated PDFs show no
navigation-only page, the gate is green, and
`git status` shows `docs/specs/site-browser-quality-gate/` untouched by this task.

### T4: Register the spec

**Depends on:** none

**Touches:** workspace.toml, docs/specs/README.md

**Tests:**
- Goal-based: `python '<work-loop skill dir>/scripts/lint-spec-status.py' --root .`
  passes.

**Approach:**
- Add the spec to `workspace.toml` and to the active list in
  `docs/specs/README.md`.

**Done when:** the spec-status lint is clean.

## Rollout

- **Delivery:** big bang; one `@media print` block. Reversible by deleting it —
  the gate case then fails, which is the intended signal.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** none beyond the repository's load-bearing build
  order (`build-site.py` → `web` → `docs-site`).

## Risks

- **The fix is narrow by design, so the general hazard survives it.** A future
  component that sets `display` on a `print:hidden` element breaks the same way.
  Mitigated by the `AGENTS.md` trap, not by code; accepted because the audit's
  decision rule bars generalising past the demonstrated boundary.
- **The audit amendment is a governance edit to an Accepted document.** Mitigated
  by naming, in the note itself, every section that stands unchanged **and
  scoping `## Decision rule` and `## Residual` to the axes they measure** —
  declaring those two unchanged would assert the reconciliation rather than
  perform it.
- **E2E print coverage is new.** The gate spec has none today. Mitigated by
  mutation-proving the case and by placing it where CI already runs.

## Changelog

- 2026-08-25 — First draft: a global `!important` on `.print\:hidden`, with
  `.pagination-links` named as a second collision site.
- 2026-08-25 — Second draft: replaced with a cascade-layer wrapper on the three
  override components, after a browser probe showed Starlight ranks with cascade
  layers and pagination is layered and already correct — so it was never a
  collision site.
- 2026-08-25 — Third and current draft: the layer wrapper was disproven in
  adversarial review. It would demote `Footer.astro:80` and `PageFrame.astro:208`
  `:focus-visible` rules below `src/styles/starlight.css:589`, flipping
  `outline-offset` 3px→2px on 228 pages with no gate able to see it, and it
  inverts the ratified unlayered-custom-CSS premise
  (`docs-site/src/styles/starlight.css:8-9`;
  `docs/specs/docs-site-design-refresh/plan.md:32`). The approach became the
  targeted `@media print` rule — which is what the audit's "smallest necessary
  rule targeting only the demonstrated failing boundary" bar described from the
  outset. No implementation was written under any of the three drafts. Two
  uncommitted edits do exist in the worktree — the `print:hidden` class on
  `Footer.astro:21` and two print assertions in `rendered-output.test.ts` — but
  they predate this spec and T1 and T2 undo them.
