# Plan: Marketing-site press state

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/design/direction/marketing-site.md` (direction sheet: `[ruled]`, `[flat]`, `[none]`, and the three 2026-09-18 owner decisions); `web/src/styles/tokens.css` (three-tier token architecture and the measured paper ramp); analogous implementations — `JourneyContract.astro`'s `.decision-chip:hover` block, which already carries a transient ground fill with its contrast measured in a comment, and `PageHero.astro`'s primary/secondary action pair; their tests — `web/src/test/design-system-projection.test.ts` and `web/src/test/e2e/quality-assertions.ts`'s state-contrast helper. Named uncertainty: the dark close band cannot carry the paper pressed ground, and its best available ground shift is 1.94:1.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md`.

## Approach

The change is one idiom applied in one pass, plus the guard that keeps it
applied. Tokens land first because everything else references them; the static
derivation guard lands second and goes red against the unmodified components,
which is what proves it can fail; the `:active` rules then turn it green. The
browser measurement lands after the rules exist, because it reads rendered
computed styles and has nothing to read before then. Documentation and the
workspace repair close it.

The riskiest part is not the CSS. It is that the guard must derive its selector
set from the sources rather than carry a list: the recorded finding for this
work was itself stated as "0 of 28 interactive classes", that figure was wrong
when written, and two earlier CI failures on this surface came from stale
hardcoded lists. A guard that enumerates would be a fourth instance of the same defect.

The second risk is the dark close band. The chosen ground-shift idiom is strong
on paper — the pressed ground sits about 10:1 from the page ground — and weak on
the one dark band, where the dark ramp offers at most 1.94:1 while keeping link
text above the 4.5:1 floor. The plan takes that exception explicitly and records
its two measurements rather than letting a reviewer rediscover it.

## Constraints

- `docs/design/direction/marketing-site.md` — Containment `[ruled]`, Material `[flat]`, Ornament `[none]`, Motion `[still]`. No transform, scale, shadow or elevation is available, which is what removes the conventional press idioms.
- The same document's Chromatic intensity row and `tokens.css`'s own invariant: chroma means state — a refusal, a hold, a block. `--ds-clearance` has exactly two consumers and both are `HELD`. Press must not become the third.
- `tokens.css` three-tier architecture: component CSS references semantic tokens only.
- `web/AGENTS.md` — `gate-css-tokens` in `build-check.yml` is fanned into the required aggregator, so a hardcoded colour reds a pull request.
- Every vertical measure is a multiple of `--ds-rule-pitch` (8px); the 4px half-pitch is inline-only. This change adds no vertical measure.
- Build order: `tools/build-site.py`, then `npm run build --prefix web`, then `npm run build --prefix docs-site`. The web build cleans `build/`, which deletes `build/docs`.

## Construction tests

**Integration tests:** the browser press measurement in Task 4 spans every task's output — tokens, rules and the rendered page — and is the only check that reads real computed styles.

**Manual verification:** none. The browser measurement replaces it.

## Tasks

### Task 1 — The four tokens

**Touches:** `web/src/styles/tokens.css`, `web/src/design-system.md`

**Design:** One primitive, `--prim-record-700: #413c34`, placed between
`--prim-record-600` and `--prim-record-800` in declaration order so the ramp
reads monotonically. Three semantic tokens in the existing component-token
region: `--ds-cta-primary-bg-active: var(--prim-record-700)` for ink-filled
controls, `--ds-surface-pressed: var(--prim-record-200)` for paper carriers,
and `--ds-surface-pressed-dk: var(--prim-ink-700)` for the two controls on the
dark close band. Each carries its measured ratios in a comment, in the style
the surrounding declarations already use.

**Tests:** goal-based. `node scripts/generate-design-system.mjs` rewrites §1,
and `design-system-projection.test.ts` passes with the four new rows present.

**Done when:** `npx vitest run src/test/design-system-projection.test.ts` passes
and `git diff web/src/design-system.md` shows exactly the four added rows.

### Task 2 — The static derivation guard, red

**Touches:** `web/src/test/press-state-coverage.test.ts`

**Design:** Parse every non-test `.astro` under `web/src`, strip comments, and
collect each rule block whose selector carries `:hover`. For each, derive the
control's base selector and assert an `:active` rule exists for it in the same
file. The selector set is computed per run, so a control added later is covered
with no edit here. A second assertion covers the idiom: each `:active` rule's
declaration set is exactly one ground property whose value is one of the three
press tokens.

**Tests:** TDD. This task's output is the test. It must go red against the
unmodified components, naming the controls that lack a press state.

**Done when:** the guard runs, fails, and its failure message lists the
uncovered controls by file and selector.

### Task 3 — The `:active` rules

**Touches:** the 18 non-test `.astro` files under `web/src/components/` and `web/src/pages/` that carry a `:hover` rule

**Design:** Beside each hover rule, an `:active` rule setting one ground
property. Ink-filled CTAs take `--ds-cta-primary-bg-active`. Paper controls —
ghosts, chips, cards, record links, tabs and nav links — take
`--ds-surface-pressed`. The two controls on the dark close band, the footer
list links and the pack page's install copy button, take
`--ds-surface-pressed-dk`. `.install-copy-btn--success` is a state lock rather
than a hover affordance and takes no press rule; the guard must admit that
exclusion by rule, not by name.

**Tests:** the Task 2 guard turns green. No new test file.

**Done when:** the guard passes and `npm run lint:css --prefix web` reports no
new finding.

### Task 4 — The browser press measurement

**Touches:** `web/src/test/e2e/press-state.spec.ts`

**Design:** For each derived control reachable on the gate's routes, read
`getComputedStyle` at rest, then under `locator.hover()`, then while held with
`page.mouse.down()`, releasing with `page.mouse.up()` before moving on. Assert
the held value differs from the hover value. The spec asserts
`document.body`'s background computes to `rgb(247, 245, 240)` before it records
anything, because a 404ing stylesheet still renders readable HTML and every
measurement taken against it would be silently worthless.

**Tests:** visual / manual QA mode, automated. The spec is the verification.

**Done when:** the spec passes against the built site served under
`/agent-ready-repo/`, with the paper-ground sanity assertion passing first.

### Task 5 — The records

**Touches:** `docs/design/direction/marketing-site.md`, `docs/design/evidence/marketing-home-retrofit.md`

**Design:** A dated entry under Owner decisions naming the ground-shift idiom,
the two alternatives refused and why the direction sheet forbids the usual
ones, the four tokens, and the dark-band exception with its two measurements.
The evidence manifest gains the measured press triples.

**Tests:** goal-based.

**Done when:** both documents state the decision and the manifest's press row is
populated rather than absent.

### Task 6 — The workspace repair

**Touches:** `workspace.toml`

**Design:** Close the press-state finding with its re-measured figures. Repair
the lead lines that a later paragraph in the same entry already contradicts:
the `/now/` length entry, the pack structured-data entry and the route-level
matrix entry each lead with an open status that text below them closes. Each
takes a prepended current lead in the file's own newest-on-top convention, and
each stale `Unblocks when:` outside an archival "original entry" section is
retired. Register the spec under an initiative.

**Tests:** goal-based.

**Done when:** `python3 tools/lint-spec-status.py --root .` passes and
`workspace-status` reports the entry as canonical.

## Mutation evidence

The single record of what was mutated and what it killed. Stated once, here,
because an earlier pass wrote the count into three places and they disagreed.
Each mutation was applied by copying the file to `/tmp` and copying it back --
never `git checkout`, which restores to HEAD and silently deletes an uncommitted
fix.

| Mutation | Kills |
| --- | --- |
| Delete one control's `:active` rule | coverage |
| Point a press rule at the wrong carrier's token | AC3a carrier derivation |
| Repoint a press ground at its own hover ground | AC3b |
| Drop a required ink raise | unhovered floor |
| Add an ink raise the floor does not require | two-sided floor test |
| Reach `--ds-clearance` from a press rule | mark fence |
| Equalise the press and hover tokens in `tokens.css` | browser: indistinguishable |
| Retune `--ds-surface` | browser: paper-ground sanity gate |
| Remove a route from the spec's list | browser: set reconciliation |
| Remove the click suppression | browser: navigation guard |

The last is the defect the first implementation shipped with: pressing a link
navigated, and every later control was read on a different page. It now fails
naming the control that navigated.

## Risks

- **The guard's selector derivation is the whole control.** If it cannot map a hover selector to its control, it silently covers less than it claims. Mitigation: the guard reports the count it derived, and Task 2 proves it reds; a control it cannot parse is a failure, not a skip.
- **The dark band's press is weak.** 1.94:1 is a real shift but a quiet one. It is recorded rather than hidden, and the alternative — a brighter ground — drops footer link text to 4.06:1, below the floor.
- **The Playwright gate intermittently fails one route** with "finite CSS animations never stopped running". That is a declared harness precondition; the affected test is re-run rather than the site changed.

## Changelog

- 2026-09-23 — Drafted.
- 2026-09-23 — Spec approved (scope) and plan approved (build strategy) by the owner in session; baseline sealed.
- 2026-09-23 — Shipped. All seven acceptance criteria met; six gates green.
- 2026-09-23 — Controlled amendment, owner-approved in session: AC3 relaxed to admit a floor-driven ink raise, AC3a added, and a fourth semantic token (`--ds-state-warn-fg-pressed`) introduced. Cause: the warn panel's two controls have no contrast headroom for any ground shift, measured across three candidate grounds. Task 1 and Task 3 carry the extra token; Task 2's guard gains the contrast computation that makes the exception checkable.
