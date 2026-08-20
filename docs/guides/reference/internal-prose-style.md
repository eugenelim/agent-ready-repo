# Internal prose style

Applies to prose that stays in this repo and never ships: this file,
`docs/architecture/`, `docs/specs/`, RFCs, ADRs, and internal READMEs. The
adopter-facing version ships in the `product-documentation` pack's
`author-product-docs` skill (`references/clear-prose.md`).

- **Write prose that reads like a person wrote it.** Cut hedges ("it's worth noting"), uniform sentence rhythm, em-dash overuse, throat-clearing openers, inflated verbs ("leverage", "utilize", "delve"). Vary sentence length; one claim per sentence; concrete number or example over adjective.
- **Catch structural tells.** Check each draft: does the argument advance paragraph to paragraph, or restate? Does each list item earn its slot? Is there a position the text can be disagreed with? Is any specific detail grounded (a name, a date, a count), or only performed? Watch for: treadmill effect, symmetrical lists that pad a template, false precision, performative thoroughness, nice-nice wrap (both sides hedged, no stance).
- **State what is — don't leak rationale or identity.** Cut asides that justify mid-sentence; give the "why" its own sentence or drop it. No self-narration ("internally we…", "our goal here is…").
- **Soft-wrap guides.** Under `docs/guides/`, one line per paragraph, blank line between paragraphs, list items one line each. Older docs (README, CONVENTIONS) are hard-wrapped near 72 columns; match the file you're editing.
