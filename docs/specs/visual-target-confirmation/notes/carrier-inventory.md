# Carrier inventory: where the visual-target rule is written

Produced 2026-09-29 by a whitespace-normalized sweep for `visual[ _-]target`
over `packs/`, `guides/`, `web/src/content/`, `tests/` and `docs/design/`.
Whitespace normalization is load-bearing: a raw line-oriented grep of the same
pattern returns 24 files and misses `frontend-reviewer.md`, where the phrase
wraps mid-line. `test_visual_authority_slice_two.py` documents the same trap.

**25 files, 59 loci.**

| Loci | File |
| ---: | --- |
| 3 | `packs/experience-design/.apm/skills/creative-direction/SKILL.md` |
| 3 | `packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md` |
| 3 | `packs/experience-design/.apm/skills/creative-direction/evals/evals.json` |
| 2 | `packs/experience-design/.apm/skills/creative-direction/references/converge.md` |
| 6 | `packs/experience-design/.apm/skills/creative-direction/references/visualize.md` |
| 4 | `packs/experience-design/.apm/skills/design-system/SKILL.md` |
| 1 | `packs/experience-design/.apm/skills/design-system/assets/token-taxonomy-template.md` |
| 1 | `packs/experience-design/.apm/skills/design-system/evals/eval_queries.json` |
| 3 | `packs/experience-design/.apm/skills/design-system/evals/evals.json` |
| 2 | `packs/experience-design/.apm/skills/design-system/references/value-derivation.md` |
| 2 | `packs/experience-design/tests/skills/creative-direction/test_contract.py` |
| 4 | `packs/experience-design/tests/skills/design-system/test_design_system_contract.py` |
| 1 | `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` |
| 2 | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` |
| 3 | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json` |
| 3 | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md` |
| 1 | `packs/frontend-engineering/JOURNEY.md` |
| 1 | `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_evidence.py` |
| 1 | `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_loop.py` |
| 3 | `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_precedence.py` |
| 6 | `guides/experience-design/how-to/establish-design-intent.md` |
| 1 | `guides/frontend-engineering/how-to/read-the-design-handoff.md` |
| 1 | `guides/frontend-engineering/tutorials/scaffold-a-component.md` |
| 1 | `web/src/content/journeys/frontend-engineering.md` |
| 1 | `tests/roster/test_frontend_visual_authority_adopter_prose.py` |

## Why this exists

Four pre-EXECUTE review rounds on the combined `visual-target-confirmation`
contract each discovered carriers the previous round had not listed: one in
round 2, two in round 3, five in round 4. Every mechanism the contract tried —
presence checks, a closed retired-phrase set, a closed surface set — assumed
the author already knew the full extent. This inventory is that extent,
measured rather than assumed, and it is the discovery input the successor
slices author against.

`value-derivation.md` states the reason the rule is multi-homed: it is "the
third place the same rule is written, because it is the one most likely to be
broken here". The duplication is deliberate, so a change to the rule is a
migration across its homes rather than an edit to one.
