# Verification ledger — visual-target rung precondition

Observations recorded during implementation, in task order. Each entry names the
task that produced it and the date it was taken.

---

## T1: Re-measure the carrier extent

**Date:** 2026-10-01
**Method:** Python script run outside the repository tree, sweeping `packs/`,
`guides/`, `web/src/content/`, `tests/`, and `docs/design/` with whitespace
normalized before matching (`" ".join(text.split())`). The script is recorded
in the session scratchpad and is not part of the repository.

### Carrier extent

| Dimension | Plan states | Measured | Agrees? |
| --- | --- | --- | --- |
| Total carrier files | 27 | 27 | Yes |
| Markdown carriers | 15 | 15 | Yes |
| Non-Markdown carriers | 12 | 12 | Yes |
| Total loci | 105 | 105 | Yes |

**Result: agrees exactly with the plan inventory (27 files, 105 loci, 15 Markdown
and 12 non-Markdown carriers, measured 2026-10-02).**

### Markdown carriers (15)

| File | Loci |
| --- | ---: |
| `guides/experience-design/how-to/establish-design-intent.md` | 11 |
| `guides/frontend-engineering/how-to/read-the-design-handoff.md` | 1 |
| `guides/frontend-engineering/tutorials/scaffold-a-component.md` | 1 |
| `packs/experience-design/.apm/skills/creative-direction/SKILL.md` | 3 |
| `packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md` | 8 |
| `packs/experience-design/.apm/skills/creative-direction/references/converge.md` | 7 |
| `packs/experience-design/.apm/skills/creative-direction/references/visualize.md` | 6 |
| `packs/experience-design/.apm/skills/design-system/SKILL.md` | 4 |
| `packs/experience-design/.apm/skills/design-system/assets/token-taxonomy-template.md` | 1 |
| `packs/experience-design/.apm/skills/design-system/references/value-derivation.md` | 2 |
| `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | 1 |
| `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | 2 |
| `packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md` | 3 |
| `packs/frontend-engineering/JOURNEY.md` | 1 |
| `web/src/content/journeys/frontend-engineering.md` | 1 |

### Non-Markdown carriers (12)

| File | Loci |
| --- | ---: |
| `packs/experience-design/.apm/skills/creative-direction/evals/evals.json` | 4 |
| `packs/experience-design/.apm/skills/design-system/evals/eval_queries.json` | 1 |
| `packs/experience-design/.apm/skills/design-system/evals/evals.json` | 3 |
| `packs/experience-design/tests/skills/creative-direction/test_contract.py` | 21 |
| `packs/experience-design/tests/skills/design-system/test_design_system_contract.py` | 4 |
| `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json` | 3 |
| `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_evidence.py` | 1 |
| `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_loop.py` | 1 |
| `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_precedence.py` | 3 |
| `tests/roster/test_frontend_visual_authority_adopter_prose.py` | 1 |
| `tests/roster/test_visual_target_guide_excerpt.py` | 6 |
| `tests/roster/test_visual_target_release_surface.py` | 5 |

### AC-0006 property: violation count

The AC-0006 property logic (from T4's stub): for each Markdown sentence that
contains a `visual[ _-]target` reference in its unstripped text, strip both name
forms (`approved[ -]visual[ -]target`) for the cue test, and check for a
confirmation cue (`confirm` or `approved`) in the stripped text. If the sentence
passes both tests but lacks the literal `visual_target`, it is a violation.

| Dimension | Plan states | Measured | Agrees? |
| --- | --- | --- | --- |
| Violation sentences (migration owed) | 14 | 14 | Yes |
| Files containing violations | 12 | 12 | Yes |

**Result: agrees exactly with the plan's stated migration target (14 sentences
across 12 Markdown files).**

Observation: the sweep found 21 total sentences matching the firing predicate.
The other 7 already contain `visual_target` and are compliant. The plan's "14"
is the violation count (sentences missing `visual_target`), not the total firing
count. Both figures are recorded here for completeness.

#### 14 violation sentences (no `visual_target`, migration owed)

1. `packs/frontend-engineering/JOURNEY.md` — JOURNEY bullet that resolves visual
   authority; cue fires via "confirmed" further in the sentence (the full
   whitespace-normalized sentence runs past the 200-char display limit).
2. `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` — "an approved
   visual target with no recorded human confirmation behind it" (table/list
   sentence; NAME_FORMS strips "approved visual target", but "approved" remains
   from "no recorded human confirmation").
3. `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` —
   "`approved-visual-target` — the direction artifact step 0 read, when it records
   a human-confirmed composition." Cue: "confirmed".
4. `packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md`
   — the full precedence table row; condition cell is `recorded-human-confirmation`.
5. `packs/experience-design/.apm/skills/design-system/SKILL.md` (sentence 1) —
   the rung table row containing "`approved-visual-target` | The confirmed
   composition". Cue: "confirmed".
6. `packs/experience-design/.apm/skills/design-system/SKILL.md` (sentence 2) —
   the routing table row "A route must resolve values, or a visual target is
   present"; cue fires from "confirmed" appearing later in the collapsed table.
7. `packs/experience-design/.apm/skills/creative-direction/references/visualize.md`
   — "**Approved visual target** — a composition the human has confirmed as a
   structural reference". Cue: "confirmed".
8. `packs/experience-design/.apm/skills/design-system/references/value-derivation.md`
   — "An approved visual target is a confirmed composition."
9. `packs/experience-design/.apm/skills/design-system/assets/token-taxonomy-template.md`
   — the `**Route:**` HTML comment block collapsed into one sentence; cue:
   "approved" from "approved direction".
10. `guides/frontend-engineering/how-to/read-the-design-handoff.md` —
    "`approved-visual-target` — your `direction/<slug>.md` records that a person
    confirmed the composition".
11. `guides/frontend-engineering/tutorials/scaffold-a-component.md` —
    "no confirmed visual target, no direction or taxonomy".
12. `guides/experience-design/how-to/establish-design-intent.md` (sentence 1) —
    the run-on beginning "confirm the shape against what you get back.*" that
    runs through a heading, comment, and prompt block. Cue: "confirm".
13. `guides/experience-design/how-to/establish-design-intent.md` (sentence 2) —
    the `**Route:**` block (same structure as token-taxonomy-template.md).
14. `web/src/content/journeys/frontend-engineering.md` — same JOURNEY bullet as
    item 1 (projection).

#### 7 compliant firing sentences (already contain `visual_target`)

These are in scope of the firing predicate but are not violations:

- `packs/experience-design/.apm/skills/creative-direction/references/converge.md`
  — "Record the approved visual target disposition into the `visual_target`
  frontmatter key…" (1 sentence)
- `packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md`
  — three sentences mentioning `visual_target:` disposition, key name, and absent
  value (3 sentences)
- `guides/experience-design/how-to/establish-design-intent.md` — same three
  template sentences mirrored in the guide (3 sentences)

### Non-Markdown carrier count

| Dimension | Plan states | Measured | Agrees? |
| --- | --- | --- | --- |
| Non-Markdown carrier count | 12 | 12 | Yes |

The floor `NON_MARKDOWN_CARRIER_FLOOR = 12` stated in T4's stub block is
confirmed by this measurement.

### Discoveries

None. All three measured figures (27 files / 105 loci / 15+12 split; 14
violations / 12 files; 12 non-Markdown carriers) agree exactly with the plan's
stated inventory. No further discovery is recorded.
