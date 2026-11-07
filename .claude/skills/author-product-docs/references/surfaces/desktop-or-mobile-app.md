# Desktop or mobile app documentation

Evidence narrow: help sets from Apple, Android, Figma, and Notion, plus Microsoft and Google style guides, one article opened per product in most cases. No Windows help article was opened. In-app help against web help is untested. Read each rule as a default plus its condition.

Load this file only when surface discovery names a desktop, mobile, or web app.

## First screen

The four help home pages opened start on a search box or task cards, then a contents tree. None shows a command.[^1][^2] Confidence is medium; four pages.

## First reader action

**Default:** a click path or tap in the app, as a task-titled page. Notion's "Create a page" gives the click, the keyboard shortcut, and the mobile tap in one short article.[^3] Name the app, tool, or UI location first when the reader could be confused about where to act, and keep a procedure short enough to fit on one screen.[^4] Never ask for a terminal command on a page for app users.

## Sample style

**Default:**
- Bold the UI label exactly as it appears. Write "click **Save**"; do not use a label as a verb.[^5]
- Do not use directional wording ("the left-side panel") in place of a label or a cropped image.[^5]
- Give images alt text of 155 characters or fewer, or empty alt text when the text already says it. Cover personal data with a solid overlay, not a blur.[^6]

**Option, menu-path format:** `A > B > C` can be read badly by screen readers (Microsoft: they "might skip over" the brackets). Either mark the separators for assistive technology (Google's fix is an `aria-label` of "and then") or write one step per menu.[^4][^5] Neither vendor tested real screen-reader output.

**Option, platform handling:** inline notes (Notion's "cmd/ctrl"), parallel lists (Figma's Mac and Windows bullets), or a selector (Apple's version control). Pick one and keep it across the set.[^1][^3]

**Option, screenshot density:** sparse and tightly cropped when the UI changes fast, the set has many locales, or the audience is expert. Annotated images at moments of doubt when the audience is novice and the UI is stable.[^6][^7] The case for annotated images is a 2000 study of 48 novices using printed manuals; the case for sparse images is cost, translation, and privacy, not reader benefit. State both, and do not cite a vendor percentage that has no source.

## Reference shape

No rule. The sampled sets use hand-written contents trees, and the evidence on a lookup shape is too thin to state a default. Confidence: low.

## Troubleshooting

No rule. Confidence: low. No dedicated troubleshooting section was opened for any product; the pages sampled put limits at the foot of the task page and end with a support route. Do not copy that as a pattern.

## Failures to refuse

- Directional wording in place of a label.[^5]
- Text inside screenshots, which raises translation cost.[^6]
- Bracket-only menu paths with no accessibility check.[^4][^5]
- **Named example:** Apple's "Take screenshots or screen recordings on Mac" page does not say which macOS version its steps target, although the guide has a version selector elsewhere.[^1][^8] That is a judgement from one page; state the version a task was checked against.

## Sources

[^1]: Apple, Mac User Guide, https://support.apple.com/guide/mac-help/welcome/mac, accessed 2026-11-06. Confidence: medium.
[^2]: Figma, Figma Learn, https://help.figma.com/hc/en-us, accessed 2026-11-06. Confidence: medium (currency inferred; no date shown).
[^3]: Notion, Create a page, https://www.notion.com/help/create-your-first-page, accessed 2026-11-06. Confidence: medium (one article).
[^4]: Microsoft, Writing step-by-step instructions, https://learn.microsoft.com/en-us/style-guide/procedures-instructions/writing-step-by-step-instructions, accessed 2026-11-06 and re-opened (dated 2026-03-18, updated 2026-10-15). Confidence: medium.
[^5]: Google developer documentation style guide, UI elements and interaction, https://developers.google.com/style/ui-elements, accessed 2026-11-06 and re-opened. Confidence: medium.
[^6]: Google developer documentation style guide, Diagrams, figures, and other images, https://developers.google.com/style/images, accessed 2026-11-06 and re-opened. Confidence: medium.
[^7]: H. van der Meij, The role and design of screen images in software documentation, J. Computer Assisted Learning 16(4), 2000, https://research.utwente.nl/en/publications/the-role-and-design-of-screen-images-in-software-documentation/, accessed 2026-11-06 (abstract). Confidence: low (old, printed manuals).
[^8]: Apple, Take screenshots or screen recordings on Mac, https://support.apple.com/guide/mac-help/take-a-screenshot-mh26782/mac, accessed 2026-11-06. Confidence: low as a failure example (one page).
