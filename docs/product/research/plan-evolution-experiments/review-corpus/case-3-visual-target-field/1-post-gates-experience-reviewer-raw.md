## Verdict
SHIP WITH CHANGES

## Summary
Three copy surfaces add a `visual_target` frontmatter key: a template comment block, the same block re-derived into the published how-to, and a `/now/`-projected changelog bullet. The honesty about the field being inert is the strongest thing here, and the closed-set definition is crisp. The dominant weakness is that the copy describes the schema rather than telling an adopter what to do, and two sentences state things the rest of the pack contradicts.

## Findings

### Blockers

**1. The Highlights bullet misstates when `converge` records the disposition.** Where: `docs/product/changelog.md:105` — "`converge` records the disposition when writing compositional commitments." What's wrong: factual accuracy on a surface projected to the public `/now/` page — `.apm/skills/creative-direction/references/converge.md:56-61` records the disposition unconditionally as a product-specific field, while compositional commitments are written only when an approved visual target exists (`creative-direction-template.md:231`), so as written `visual_target: none` would never be recorded. Fix: drop the conditional clause — "`converge` records it whenever it captures a direction."

**2. "The `**Binding:**` line … binds nothing" reads as a contradiction.** Where: `creative-direction-template.md:86-88` and the mirrored `guides/experience-design/how-to/establish-design-intent.md:222-224`. What's wrong: specificity/clarity — a non-designer filling a field literally labelled *Binding* is told in the same breath that it binds nothing, with no pointer to where binding actually happens (the `## Compositional commitments` section, template line 229-235). Fix: say what each line *is* rather than what it is not — "These four lines describe the target for a human reader; what actually constrains the build is recorded under Compositional commitments."

### Concerns

**3. The Highlights bullet is schema-led, not outcome-led, and never says what the adopter must now do.** Where: `docs/product/changelog.md:105`. What's wrong: five-second scan and painkiller-first — it opens with the artifact mechanism ("Direction artifacts now carry a `visual_target` frontmatter key") and closes in contributor voice ("an additive schema change adopters author against"), which is exactly the register `changelog.md:33` and `:57` rule out ("Rewrite for users, not contributors"; "Describe what someone can now do"). A `/now/` reader who never opens the changelog learns a field name and no action. Fix: lead with the adopter's new obligation and keep the honesty second — "Every direction now states whether its visual target was confirmed by a human, so a reader can tell a confirmed target from an assumed one. Set it when you write the direction; nothing is gated on it yet."

**4. "Disposition", "closed set", "additive schema change" are contributor jargon on a public page.** Where: `docs/product/changelog.md:105`. What's wrong: anti-AI-smell / specificity — three abstract terms carry the whole bullet, and "disposition" appears again in the template (`creative-direction-template.md:13`) and guide (`:149`) without ever being defined in plain words. Fix: say "records whether the target is confirmed" and name the three values inline, once.

**5. The absent-field rule is stated but never justified, and its default contradicts the common case.** Where: `creative-direction-template.md:84-85`; `establish-design-intent.md:220-221`. What's wrong: actionability — most directions have no target at all, so an omitted key silently reads as "a target is recorded but unconfirmed", which is false for them, and the copy gives no reason for the fail-safe choice. Fix: add the reason in one clause — "An absent key reads as `unconfirmed`, because silence must never be read as confirmation. Write `none` when there is no target, rather than leaving the key off."

**6. The confirmation placeholder does not show what a valid "where" looks like, and invites a person.** Where: `creative-direction-template.md:100` — `**Confirmation record:** <YYYY-MM-DD> — <where the confirmation was recorded>`. What's wrong: the ban on names, handles, and contact details lives only in the comment above (`:89-90`), while the prompt a filler actually reads says "where the confirmation was recorded", which most people answer with "approved by <name> in review". Fix: carry the rule and an example into the prompt itself — `<the ticket, PR, or meeting record it was logged in — not a person>`.

**7. The no-names rule reaches the human but not the agent that writes the line.** Where: rule present at `creative-direction-template.md:89-90`; absent from `.apm/skills/creative-direction/references/converge.md:56-61`, which is what authors the artifact. What's wrong: cross-artifact coherence — `converge` is told to record the disposition but never told what must not appear in the confirmation record. Fix: restate the one clause in `converge.md` where the field is written.

**8. The how-to adds the field to the fenced excerpt but says nothing about it in prose.** Where: `establish-design-intent.md:149-153` and `:236` (excerpt) versus `:256` (the `converge` description, which lists what converge records and omits the visual-target disposition) and `:121` (the `approve-aesthetic-direction` gate). What's wrong: coherence — a reader scanning the page's narrative never learns the field exists, who confirms a target, or at which moment; and because the only named human gate on the page is `approve-aesthetic-direction`, confirming a visual target may be mistaken for that gate. Fix: add the disposition to the `converge` bullet at `:256`, and one sentence saying confirmation is a separate, optional record, not part of the direction gate.

**9. "Optional." now heads a section with a non-optional frontmatter key.** Where: `creative-direction-template.md:80` / `establish-design-intent.md:216` — "Optional. If no target exists, write 'none' and continue." What's wrong: the body lines are optional but the key is not, and the two instructions sit four lines apart without being reconciled. Fix: "The body lines below are optional; the frontmatter key is always recorded. With no target, set `visual_target: none`, write 'none' here, and continue."

### Nits

**10. "the canonical disposition, over `none`, `unconfirmed` and `confirmed`" reads as precedence.** Where: `creative-direction-template.md:83-84`; `establish-design-intent.md:219-220`. Fix: "takes one of three values: …".

**11. "and the confirmation record in the body says when and where" is already said below.** Where: `creative-direction-template.md:16` repeats what `:88-89` states in full. Fix: delete the trailing clause from the frontmatter comment.

**12. The changelog bullet is three sentences where the sibling 4.1.1 bullet (`changelog.md:111`) lands in two.** Fix: cut to two after the outcome-led rewrite.

## What's working

- `docs/product/changelog.md:105` states plainly that nothing reads the field and nothing is gated on it. That is the hardest thing to say in release copy and it should survive every rewrite above.
- The three-value definition at `creative-direction-template.md:14-16` distinguishes "no target" from "unconfirmed target" in one line each, with no overlap — a non-designer can pick correctly from it.
- The template excerpt in `establish-design-intent.md:136-237` is a faithful re-derivation of the template, comment text included, so the published page and the artifact cannot drift silently.
- Separating human-readable provenance from what actually binds the build is the right distinction to be drawing here; finding 2 is about its wording, not the idea.
