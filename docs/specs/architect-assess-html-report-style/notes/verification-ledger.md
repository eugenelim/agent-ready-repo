# Verification ledger: architect-assess HTML report style

Rendered from `testdata/html-style-sample.md` (Meridian orders platform, 6 subsystems, 4 evidence classes, 8-row heat map) with Microsoft Edge headless driven over the DevTools protocol, light and dark emulated through `prefers-color-scheme`. Screenshots sit under `/private/tmp/qa/shots/` and are not committed; each row below states what was measured.

## Real-browser criteria

| Criterion | Observation | Result |
| --- | --- | --- |
| First screen at 320×640 and 1280×800, light and dark | Title, snapshot line, unconfirmed banner and the first margin head are all inside the viewport in all four runs. At 320 the closed contents control is shown and the rail list is hidden. At 1280 the rail list is shown and the control is hidden. | Met |
| 320 px reflow | `scrollWidth` equals `clientWidth` in light and dark; prose column 272 px; tables scroll inside their own regions. | Met |
| 1024 px prose width | Prose column 512 px in light and dark. With a targeted section (12 px padding plus 3 px bar) and a 15 px classic scrollbar the derived width is 482 px. | Met |
| 1280 / 1680 / 2560 margin heads and sticky rail | Rail list shown as its own track at every width, no page-level horizontal scroll, prose 600 px at 1280 and above. The frontend reviewer scrolled the page and confirmed the rail stayed in view. | Met |
| First Tab at 320 and 1280 | Focus lands on the skip link (112×32 px) with a 2 px solid outline in both themes at both widths. | Met |
| Evidence pills and heat ramp | Four pills with bar glyphs render. Computed heat fills in dark are `rgb(22,24,29)`, `rgb(32,36,44)`, `rgb(38,43,53)` for low, medium, high; unknown matches low and is italic with a `?` glyph. The 1280 light and 320 dark heat-map screenshots were read. | Met |
| Design and experience review | An independent `experience-reviewer` pass over the 1280 light, 1680 light, 1280 dark, 320 dark and 1024 light heat-map screenshots found both earlier Majors resolved (heat order, contents hidden at 1280) and one new Major: the table clipped at 1280. Tables now span the margin track, and the 1280 light screenshot shows all eight columns. Minor: `? unknown` wrapped; fixed with `white-space: nowrap`. Open Minors: medium and high glyph heights look alike; adjacent high cells merge into a band because the high fill equals the row rule colour. | Met, two Minors left |

## Print (frontend-reviewer findings, fixed)

Print emulation at 720 px: the heat table's right edge was 918 px (clipped) and dark users got light grey text. After the fix the right edge is 696 px and body colour is black in both themes.

## Review findings not applied

- Scroll regions take the nearest preceding heading of any level as their name, so a subsystem Sources table is named for the subsystem. The spec states that rule, so the code follows it.
- Two source regions under one heading share a name; the spec fixes the label format.
- Every table and source block is a tab stop even when it does not scroll; the renderer cannot measure layout. Kept as a known cost.
- The stylesheet filter is a second layer behind the CSP; it is not a complete fetch block.
