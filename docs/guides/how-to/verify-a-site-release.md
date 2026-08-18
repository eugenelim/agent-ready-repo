# Verify a site release

The deterministic browser gate in `pages.yml` covers what a headless Chromium can
prove. Two things it cannot, and this page is the record for both.

Run this before approving a site release.

## What CI already proves — do not repeat it by hand

`npm run test:e2e:gate --prefix web` runs after both site builds and before the
Pages artifact is uploaded, so a failure cannot deploy.

To run it yourself, build the combined artifact first — **in this order.** The
marketing build cleans the shared artifact root, so reversing the two builds leaves
you testing a half-built site, and running the gate against a stale `build/` gives a
green that means nothing:

```bash
python3 tools/build-site.py --journeys-only   # marketing renderer inputs
npm run build --prefix web                    # writes build/, cleaning it first
python3 tools/build-site.py                   # aggregates docs content
npm run build --prefix docs-site              # writes build/docs/
npm run test:e2e:gate --prefix web
``` It exercises the approved
60-case matrix: eight marketing routes at 360, 375, 390, 414 and 1440 CSS pixels
with no theme mutation, plus `/docs/` and a nested guide route at the same five
widths in both docs themes. Each case asserts at most 1px document-level
horizontal overflow, zero serious or critical axe findings, no page or console
error, and that every same-document fragment resolves.

If that is green, responsive layout, contrast and fragment integrity are covered
on those routes. Landmark structure is NOT: the only landmark rule that fires on
this site (`landmark-unique`, from Expressive Code's unnamed code-block regions) is
moderate, and the gate fails only on serious or critical findings. Checking them again on a laptop adds
nothing.

## 1. Physical-device pass — required, and not automatable

A headless engine at a 375px viewport is not a phone. It does not reproduce touch
target ergonomics, iOS Safari's dynamic viewport and toolbar behaviour, Android
Chrome's address-bar collapse, real font rasterisation, or pinch-zoom. WCAG 2.2
target-size conformance was measured from emitted geometry (see
`docs/specs/site-browser-quality-gate/notes/docs-tap-target-audit.md`), which is
evidence about the page, not about a thumb.

Perform this on **one compact iOS browser** and **one compact Android browser**:

1. Open the deployed site root.
2. Open the marketing navigation drawer, follow one destination, and come back.
3. Open `/now/` and follow one release-notes link into the changelog.
4. Open `/docs/`, open the docs menu, and open one nested guide.
5. On that guide, scroll one wide code block and one wide table sideways.
6. Rotate to landscape and back on any one of those pages.

Tick the two boxes in
[`docs/product/release-checklist.md`](../../product/release-checklist.md) —
that file is the living release record and the one a releaser actually reads — and
record device, OS version, browser and version in the table below. If you cannot
get a device, record a blocker and an owner in both places. **Do not record a pass
you did not observe.**

| Date | Device | OS | Browser | Outcome | Notes |
| --- | --- | --- | --- | --- | --- |
| 2026-08-18 | — | — | — | **Blocked** | No physical iOS or Android device is reachable from the environment that shipped `site-browser-quality-gate`. The deterministic 60-case matrix passed; this gesture did not run. Owner: eugenelim. Must be performed before the next site release is approved. |

## 2. Print spot-check — only if print behaviour changed

The six-route print audit closed `close-stale`
(`docs/specs/site-browser-quality-gate/notes/print-audit.md`): browser defaults
are accepted and the repository ships no print CSS. Re-run it only if someone adds
print rules or changes page structure enough to affect pagination. Method matters
— measure layout at the printable width (717 CSS px for A4 with 0.4in margins),
because `emulateMedia({media: 'print'})` changes media queries without changing
the layout viewport, and measuring at a desktop width reports every full-width
section as a clipping defect that is not there.

## If the device pass fails

Classify before fixing, using
`docs/specs/site-browser-quality-gate/spec.md` § Acceptance Criteria. A
demonstrated defect returns to the spec that owns the behaviour — shared chrome to
`site-shared-chrome`, journey interaction to `journey-page-completion` — and only
becomes a new spec when it is independently shippable and owned by neither. A
preference with no observed failure is not a defect and does not justify a fix.
