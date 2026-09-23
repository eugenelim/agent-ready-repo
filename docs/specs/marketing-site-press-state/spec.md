# Spec: Marketing-site press state

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

Someone pressing a control on the marketing site sees the press acknowledged,
distinctly from resting a pointer on it. Success is that every interactive
control's computed style while held differs from its computed style on hover,
read in a browser rather than asserted from the stylesheet.

## What Changes

- Two new paper primitives — `--prim-record-700`, filling the ramp's 600→800 gap, and `--prim-record-250`, a pressed ground no hover rule already occupies — `web/src/styles/tokens.css`
- Four semantic press tokens, `--ds-cta-primary-bg-active`, `--ds-surface-pressed`, `--ds-surface-pressed-dk` and `--ds-state-warn-fg-pressed` — `web/src/styles/tokens.css`
- An `:active` rule beside every `:hover` rule that styles an interactive control — 18 files under `web/src/components/` and `web/src/pages/`
- A derived static guard that every hover-bearing control carries an `:active` sibling — `web/src/test/`
- A browser press measurement reading rest, hover and held computed styles — `web/src/test/e2e/`
- §1 of the colour-token reference, regenerated from the new tokens — `web/src/design-system.md`
- The press-state finding closed, and the marketing block's contradicted lead lines repaired — `workspace.toml`
- The press-state idiom recorded as a dated owner decision — `docs/design/direction/marketing-site.md`
- The measured press evidence recorded — `docs/design/evidence/marketing-home-retrofit.md`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — the idiom was an owner choice between three options, and the ramp gains a primitive the direction called a measured set | `docs/design/direction/marketing-site.md`, a dated entry under Owner decisions | Author | The entry names the idiom, the rejected alternatives and the dark-band exception | The entry exists and names all four tokens |
| Current product truth | Applicable — the surface gains a state it did not have | `docs/design/evidence/marketing-home-retrofit.md` | Author | Measured rest/hover/press triples and the contrast figures | The manifest's press row is populated, not "not reviewed" |
| Interface compatibility | Applicable — `design-system.md` §1 is the token reference web/ authors read | `web/src/design-system.md` | Generator | `design-system-projection.test.ts` passes with the new rows present | The committed §1 matches the generator's output |
| Reusable learning | Applicable — the dark band defeats the chosen idiom and the reason is measurable | `docs/design/direction/marketing-site.md` | Author | The dark-band exception is stated with its two contrast numbers | Stated |

## Agent Rules

### Always do

- Reference semantic tokens in component CSS; primitives only inside `tokens.css`.
- Derive the hover-bearing selector set by parsing the sources. Never write a literal list of selectors or a count into a test, a doc, or a commit message.
- Measure every contrast ratio in the browser against the rendered ground before recording it.
- Regenerate `design-system.md` §1 with `node scripts/generate-design-system.mjs` rather than editing it.
- Build in the order `tools/build-site.py`, then `web`, then `docs-site`.

### Ask first

- Adding any token beyond the four this spec names.
- Changing an existing `:hover` declaration. This change adds press; it does not retune hover.
- Giving a control a press treatment that is not the ground shift.

### Never do

- Make `:active` a consumer of `--ds-clearance` or `--ds-clearance-dk`. The mark means state — a refusal, a hold, a block — and press is not one.
- Use `transform`, `scale`, `box-shadow` or any elevation. The direction commits to `[flat]` material and `[none]` ornament.
- Hardcode a colour or a font size anywhere outside `tokens.css`.
- Re-open the three owner decisions of 2026-09-18: the mark means state only; the page is paper with the dark ground appearing exactly once in the footer; "Own the catalogue" is a light band.
- Weaken, exclude from, or narrow a gate to make it pass.

## Testing Strategy

- A static derivation guard parses every non-test `.astro` under `web/src`, collects each rule whose selector carries `:hover`, and asserts each one's control has an `:active` rule in the same file. The set is derived at run time from the sources, so a control added later is covered without editing the test.
- A browser press measurement drives the real page: for each derived control present on a route, it reads the computed style at rest, under `locator.hover()`, and while held with `page.mouse.down()`, and asserts the held style differs from the hover style. Held state is released with `page.mouse.up()` before the next control.
- The existing `design-system-projection.test.ts` covers the four new token rows in §1 with no change to that test.
- `npm run lint:css --prefix web` covers the no-hardcoded-value rule over the new declarations.
- axe runs on the routes carrying a pressed ground, covering text contrast on the two pressed grounds.
- Contrast for the dark-band pressed ground is asserted numerically against the 4.5:1 floor, because axe cannot see a state it does not enter.

## Acceptance Criteria

- [x] **AC1 — Every hover-bearing control has a press state.** The static derivation guard passes: for every rule in `web/src` whose selector carries `:hover` and whose subject is an interactive control, an `:active` rule exists for the same control. *Verified by:* the static derivation guard, run with one control's `:active` rule deleted to prove it reds.
- [x] **AC2 — The press state is visible in a browser.** For every derived control, the computed style while held differs from the computed style on hover. The measured set is reconciled against the derived set, so a control no route renders fails by name rather than being skipped, and the URL is asserted unchanged after every press so a navigation cannot be recorded as a measurement. *Verified by:* the Playwright press measurement, on pages whose `document.body` background computes to the resolved value of `--ds-surface`.
- [x] **AC3 — One idiom, applied uniformly.** Every `:active` rule sets one ground property, drawn from `--ds-cta-primary-bg-active`, `--ds-surface-pressed` or `--ds-surface-pressed-dk`. It may also set `color` where the guard computes that the new ground would otherwise drop the control's text below 4.5:1 on **either** the hovered or the unhovered press path, and `transition: none` where the control would otherwise ease into its press; the raised value is a semantic token that clears the floor. Which controls those are is computed from the resolved token values, never listed. *Verified by:* a parse of the `:active` rules that resolves every token to a colour, computes the contrast, and reds both on a press rule off the idiom and on an ink raise the floor did not require.
- [x] **AC3c — A press lands at once.** For every control, the computed style one frame after the press is applied equals its settled value. *Verified by:* the browser measurement, run without reduced-motion emulation so that a control easing into its press is visible rather than zeroed.
- [x] **AC3b — No press ground duplicates its own hover ground.** For every control, the resolved `:active` ground differs from the resolved `:hover` ground. *Verified by:* the guard's equality check, run with a press token repointed at its hover token to prove it reds.
- [x] **AC3a — The carrier class is derived, not listed.** Which of the three grounds a control takes follows from the control's own computed hover ground: an ink hover ground takes the ink press, a dark-band carrier takes the dark press, everything else takes the paper press. *Verified by:* the guard deriving the class and reding when a press rule takes a ground its carrier does not imply.
- [x] **AC4 — No press state is illegible.** Text on each pressed ground measures at least 4.5:1 against the text colour that renders on it, on both the hovered press path and the unhovered one a touch tap, a keyboard activation or a press-and-drag-off takes. *Verified by:* the numeric contrast assertion over each pressed-ground/text pair, and axe on the affected routes.
- [x] **AC5 — The token reference matches the tokens.** `design-system.md` §1 contains the four new tokens and matches the generator's output. *Verified by:* `design-system-projection.test.ts`.
- [x] **AC6 — The gates that guard this surface stay green.** `npm test --prefix web`, `npm run lint:css --prefix web`, `npx html-validate 'build/**/*.html'`, `tools/check-rendered-site-links.py`, and the Playwright site-quality gate all pass. *Verified by:* running each and recording its result.

## Assumptions

- The press state is polish, not accessibility. Every affected control already has a focus style and discloses nothing on hover alone, so no WCAG success criterion is at stake here. This sets its priority; it does not lower the quality floor the new CSS must meet.
- `--prim-record-700` at `#413c34` is an addition to a ramp the direction sheet calls "the measured set from the approved direction preview". The owner authorized this value on 2026-09-23 when choosing the idiom.
- The dark close band cannot carry the paper pressed ground: `--ds-hero-fg` on `--prim-record-200` measures 1.00:1. `--ds-surface-pressed-dk` exists for that reason and is the third semantic token, one more than the idiom decision named.
- The two controls on the `--ds-state-warn-bg` panel have no contrast headroom for any ground shift: measured on 2026-09-23, the paper pressed ground gives 4.06:1 and 3.64:1, `--prim-orange-300` gives 3.42:1 and 3.07:1, and the only ground that keeps both above the floor is the panel's own colour, which is no press at all. They take the paper ground with the ink raised, under the amended AC3. The direction sheet settles the principle: when any goal conflicts with the quality floor, the floor wins.

## Amendments

- **2026-09-23 — AC3 amended, owner-approved in session.** As approved, AC3 required every press rule to move the ground "and nothing else". Execution measured that two controls on the warn panel cannot satisfy that and the 4.5:1 text floor at the same time, and that no ground value exists that does. AC3 now permits a `color` declaration alongside the ground, only where the guard computes the floor requires it, and AC3a was added so the carrier class stays derived rather than listed. One semantic token, `--ds-state-warn-fg-pressed`, was added to carry the raised warn foreground at 6.59:1.

- **2026-09-23 — Second amendment, after review, owner-approved in session.** Four reviewers and a repaired measurement found the first implementation's evidence unsound and two of its grounds wrong.
  - `--ds-surface-pressed` moved from `--prim-record-200` to a new `--prim-record-250`. `record-200` is `--ds-border`'s value, so two controls whose hover already set `--ds-border` rendered no press at all. The new primitive prevents the collision for every paper control rather than for the two that happened to collide, and improves the paper ground shift from 1.30:1 to 1.51:1.
  - AC3's floor test now reads **both** press paths. It asked only whether the *hovered* ink cleared the pressed ground, which scored `.decision-chip` at 10.03:1 on a label it only has while hovered; unhovered it measures 1.30:1. Five controls gained a floor-driven ink raise as a result.
  - AC3b was added, because nothing asserted the one property the change exists for.
  - AC2 gained set reconciliation and a per-press URL assertion. The original measurement pressed links, navigated, and read every later control on a different page while reporting the route it believed it was on; it covered four to six controls and passed.
  - The browser measurement joined `test:e2e:gate`. It had guarded nothing.

## Follow-ons

- Whether hover itself should be retuned now that press sits beyond it on the same axis. Out of scope: this change adds a state and retunes nothing.
- **The press ground on an unpadded inline link reads as a text highlight, not a control press.** Adjudicated 2026-09-23, partly repaired and partly accepted. The idiom is right — press as a further step on the axis hover already moved is what Adobe Spectrum, Microsoft Fluent 2, IBM Carbon and Google Material 3 all do, and Spectrum states it as a rule. But none of those systems puts a ground behind an unpadded inline link; their press grounds sit on padded controls. On this surface `.nav__link` and `.now-index__link` carry `padding-block` only, `.footer__list a` carries `padding: 0`, and the catalogue record names are bare spans, so the fill paints a rectangle tight to the type — which on a paper-and-serif register is the signature of a selection or a `<mark>`.   The catalogue half was a real defect and is repaired: the press was painting the record's NAME span while the element a pointer acts on is the whole row, so the feedback drew something other than the thing pressed. It now paints `.role-record__link` and `.pack-record__link`, which carry `padding-block`, so the fill reads as a band across a record. The press target rule is now derived — a press must be on the element that receives it, never on a descendant — so the same mistake cannot be made again.
  The remaining carriers are accepted as built. A momentary fill tight to the type is what a touch platform's own tap highlight does, and `-webkit-tap-highlight-color` exists precisely to paint it; on a pointer it lasts about as long as the click. A text selection persists and arrives on drag, so the temporal signature differs completely from the thing it is said to resemble. The alternatives cost more than the concern: inline padding moves the footer column off the single left axis the direction commits to, and a second idiom for text carriers is what the owner decision refused.
- **The press ground animates at three different speeds.** Adjudicated 2026-09-23 and repaired. Measured in a browser without reduced-motion emulation, seven controls eased into their press rather than landing: `.btn-primary`, `.btn-ghost`, both `DecisionBand` actions, both `PageHero` actions and `.install-copy-btn`. A static parse found only five of them, because a modifier inherits its transition from a base class the parse cannot resolve — the browser knew the real cascade. One control read `rgba(207, 201, 188, 0.055)` on its first frame, 5.5% of the way to its pressed ground, so a click shorter than the ease showed almost none of the press. Those seven press rules now carry `transition: none`. Release still eases, because leaving `:active` uses the base rule; hover is untouched, so the scoped-out hover work stays scoped out.
- **A `--loop` journey card's left bar measures 2.33:1 against the pressed ground on the unhovered path**, against 3.26:1 at rest. Recorded rather than repaired: 1.4.11's test is the component against adjacent colours, which no press rule alters, and the bar was already marginal at rest before this change. Under a pointer press the hover rule raises it to `--ds-on-surface`, measured at 11.34:1 in Chromium.
- `PackCard.astro` has no importer anywhere in `web/src` and renders on no route, so its press rule is dead. The measurement reports it rather than hiding it. Deleting a component is not this change's to do.
- `--prim-record-700` is currently consumed only by `--ds-cta-primary-bg-active`. Whether the paper ramp wants a general 700 role is a direction-sheet question, not this change's.
