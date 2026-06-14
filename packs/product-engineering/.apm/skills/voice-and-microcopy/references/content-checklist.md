# Content checklist — run before copy ships

Run this on any user-facing string before it lands. It's a fast pass, not a gate —
catch the misses and fix them. Each item is one question; a "no" is a fix.

- [ ] **Voice-consistent.** Does it sit where the voice chart places the product on
      the axes (`references/voice-axes.md`)? Is the tone right for *this* moment —
      calm in an error, warm in a success?
- [ ] **Blame-free.** Does it describe the situation without faulting the user? No
      "you entered…", "invalid", or "you failed to…".
- [ ] **Actionable.** Does the user know what to do next? An error or empty state
      with no way forward is a dead end.
- [ ] **Concise.** Is every word pulling weight? Cut filler ("please note that",
      "in order to", "simply"). *Concise here is the UI-copy cut — for the
      documentation-prose version of this rule, see `new-guide`'s `clear-prose.md`;
      this checklist doesn't restate it.*
- [ ] **Terminology-consistent.** One concept, one word, matching the voice chart's
      terminology list — the same thing reads the same way on every screen.
- [ ] **Scannable.** For labels and buttons: keyword front-loaded, no
      sentence-shaped labels, self-describing out of context.
- [ ] **Inclusive and plain.** Plain language; no idioms that don't translate, no
      jargon the user didn't bring, no assumptions about who the user is.

## How to use it

Don't treat the list as ceremony for every word. Run it deliberately on the
strings that carry weight — errors, empty states, primary buttons, destructive
confirmations — and let the rest ride on a voice that's already characterized. The
first three items (voice-consistent, blame-free, actionable) are the ones that
most change how the copy lands; never skip those.
