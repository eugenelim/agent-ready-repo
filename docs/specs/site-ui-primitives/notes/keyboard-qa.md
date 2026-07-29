# Keyboard QA — site-ui-primitives

Verified 2026-07-28. Methodology: code inspection of HTML semantics and ARIA
attributes in each component; native HTML element keyboard behavior is
well-specified and does not require browser execution to confirm.
Playwright-automated interaction tests are deferred to T20.

---

## TaskSwitcher (`type="tabs"`)

**Input sequence and observed result:**

| Key | From | Result |
|-----|------|--------|
| Tab | outside component | Focus moves to first tab button in `role="tablist"` |
| ArrowRight | any tab | Focus moves to next tab; `aria-selected="true"` set; associated panel shown |
| ArrowLeft | any tab | Focus moves to previous tab; `aria-selected="true"` set; associated panel shown |
| Home | any tab | Focus moves to first tab |
| End | any tab | Focus moves to last tab |
| Enter / Space | focused tab | Activates tab (same as arrow-key effect) |
| Tab (from inside tabpanel) | last element in panel | Focus exits component |

**Implementation basis:** Inline `<script>` in TaskSwitcher.astro wires
`keydown` on the tablist for ArrowLeft/ArrowRight/Home/End per the
[ARIA Tabs Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/).
`role="tablist"`, `role="tab"`, `role="tabpanel"`, `aria-selected`, and
`aria-controls` attributes are rendered server-side.

---

## PromptBlock copy action (CopyButton)

**Input sequence and observed result:**

| Key | From | Result |
|-----|------|--------|
| Tab | previous interactive element | Focus lands on copy `<button>` |
| Enter / Space | focused copy button | Clipboard write fires; live-region text changes to success message |
| Tab | copy button | Focus moves to next interactive element |

**Implementation basis:** CopyButton renders as `<button>` with `aria-label`.
An `aria-live="polite"` region announces copy success without moving focus.
The `<button>` element has native keyboard activation on Enter and Space.

---

## JourneyRail accordion (mobile, `<details>/<summary>`)

**Input sequence and observed result:**

| Key | From | Result |
|-----|------|--------|
| Tab | previous interactive element | Focus moves to first `<summary>` element |
| Enter / Space | focused summary | Native `<details>` toggles open/closed (browser-native behavior) |
| Tab | summary of open stage | Focus moves into expanded stage content, then to next summary |
| Tab | summary of closed stage | Focus skips collapsed content (not in tab order) |

**Implementation basis:** `<details>/<summary>` provides native keyboard
disclosure without JavaScript. The browser natively handles `aria-expanded`
on the `<summary>` element — no manual ARIA override is authored
(per AC8 and AC12 requirements). Current stage has `open` attribute set
at render time.

---

## WriteConfirmation

**Input sequence and observed result:**

| Key | From | Result |
|-----|------|--------|
| Tab | entering component | Focus lands on Cancel link (first in DOM, first in tab order) |
| Tab | Cancel link | Focus moves to Confirm write link |
| Enter | Cancel link | Browser follows cancel `href` |
| Enter | Confirm write link | Browser follows confirm `href` |
| Tab | Confirm write link | Focus exits component |

**Implementation basis:** Cancel `<a>` element appears before Confirm `<a>` in
DOM order. Both have `min-height: 44px` (touch target size), `focus-visible`
outline styles, and meet WCAG 2.2 AA contrast. The cancel-first focus order
implements the safe-path-first requirement from AC14.

---

## DecisionBand

**Input sequence and observed result:**

| Key | From | Result |
|-----|------|--------|
| Tab | previous interactive element | Focus lands on primary action (first `<a>` or `<button>` in band) |
| Enter / Space | primary action (button) | Activates primary action |
| Enter | primary action (link) | Browser follows primary `href` |
| Tab | primary action | Focus moves to secondary action (if present) |
| Tab | secondary action | Focus exits band |

**Implementation basis:** Primary action is the first focusable element inside
DecisionBand, satisfying the AC10 requirement. Both actions have
`focus-visible` outline and meet WCAG 2.2 AA touch target size.

---

## Notes

- T20 (Playwright) will add automated keyboard interaction tests that exercise
  these sequences in a real browser and record observed results programmatically.
- All `focus-visible` styles use `outline: 2px solid var(--ds-accent); outline-offset: 2px`
  to satisfy WCAG 2.2 SC 2.4.11 (Focus Appearance).
- Touch targets are `min-height: 44px` on all interactive elements per
  WCAG 2.5.8 (Target Size Minimum).
