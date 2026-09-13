# Deliverable-form ledger

T1a of pack-guidebook-walkability. Measured 2026-09-11 against
`ec6b94f91`, over the 74 published skills of the five SOP packs.

**This exists because a wave was once ordered on a number that moved with its
predicate.** An earlier draft of the plan called `product-strategy` the most
expensive pack for the outline obligation on the strength of "zero stated
shapes"; a wider predicate returned one, and the corpus figure moved between 33
and 38. No wave ordering may rest on a figure this ledger does not carry.

## Predicates, stated

Three independent questions, and one **cascade** for form. The cascade matters:
the earlier 33-versus-38 spread came from counting overlapping predicates
independently, so a skill declaring form two ways was counted twice.

- **path** — the `SKILL.md` body contains a backticked token containing
  `docs/`, `packs/`, `guides/`, `web/`, `.claude/` or `.agents/`, or ending in
  `.md`, `.toml`, `.json`, `.yaml` or `.yml`.
- **form** — first match wins, in this order:
  1. `asset` — a non-empty `assets/` directory beside `SKILL.md`.
  2. `heading` — a heading matching template, structure, sections, artifact
     shape, or output format/shape/structure.
  3. `fence` — a fenced block containing Markdown headings.
  4. `prose` — three or more list items naming a section, quadrant, layer,
     part, heading, box or field of the output.
  5. `—` — none of the above. The outline must be authored against what the
     skill actually writes.
- **prose hits** — the raw count for predicate 4, carried so a reader can see
  how close a `—` skill sits to the threshold.

## Totals

| Pack | skills | names a path | asset | fence | prose | **declares none** |
| --- | --: | --: | --: | --: | --: | --: |
| `desk-research` | 12 | 12 | 0 | 10 | 0 | **2** |
| `product-strategy` | 9 | 9 | 0 | 0 | 1 | **8** |
| `experience-design` | 20 | 15 | 8 | 1 | 4 | **7** |
| `product-engineering` | 15 | 13 | 6 | 6 | 0 | **3** |
| `core` | 18 | 14 | 4 | 1 | 0 | **13** |
| **total** | **74** | **63** | **18** | **18** | **5** | **33** |

No skill in any pack declares form by a `heading`, so that rung of the cascade
is unused today and is kept only because the contract admits it.

## What this changes about wave order

**`core` is the most expensive pack for the outline obligation, not
`product-strategy`.** 13 of its 18 skills declare no form, against 8 of 9 for
`product-strategy` and 7 of 20 for `experience-design`. The plan's earlier
cost claim was wrong in both directions: it named the wrong pack, and it rested
on a predicate artifact.

Wave order is unchanged, because it never rested on cost — wave 1 proves the
contract on `experience-design` because that pack is the one a reader cannot
navigate at all, and the later waves follow that dependency. This ledger's
effect is to remove a false cost justification, not to reorder the work.

`experience-design` is also the best-placed pack for the obligation: 8 of its
20 skills ship a template asset, the highest of the five, so its outlines have
a source of truth to be compared against rather than invented.

## Per-skill rows

### `desk-research`

| Skill | path | form | prose hits |
| --- | :-: | --- | --: |
| `build-outline` | yes | fence | 0 |
| `compare-hypotheses` | yes | fence | 0 |
| `decision-archaeology` | yes | fence | 0 |
| `desk-research` | yes | fence | 1 |
| `desk-research-project-check` | yes | **—** | 0 |
| `desk-research-project-digest` | yes | fence | 1 |
| `desk-research-project-start` | yes | fence | 0 |
| `desk-research-project-status` | yes | **—** | 0 |
| `desk-research-project-synthesize` | yes | fence | 1 |
| `devils-advocate` | yes | fence | 0 |
| `identify-perspectives` | yes | fence | 0 |
| `source-map` | yes | fence | 0 |

### `product-strategy`

| Skill | path | form | prose hits |
| --- | :-: | --- | --: |
| `define-content-strategy` | yes | **—** | 2 |
| `define-ux-strategy` | yes | prose | 3 |
| `run-bcg-matrix` | yes | **—** | 2 |
| `run-okr-cascade` | yes | **—** | 1 |
| `run-pestle-analysis` | yes | **—** | 0 |
| `run-porters-five-forces` | yes | **—** | 0 |
| `run-swot` | yes | **—** | 1 |
| `synthesize-stakeholder-research` | yes | **—** | 2 |
| `write-prfaq` | yes | **—** | 1 |

### `experience-design`

| Skill | path | form | prose hits |
| --- | :-: | --- | --: |
| `analytical-design` | **no** | **—** | 1 |
| `content-design` | yes | asset | 4 |
| `conversion-design` | yes | **—** | 2 |
| `copy-direction` | yes | asset | 4 |
| `creative-direction` | yes | asset | 0 |
| `design-principles` | yes | fence | 0 |
| `design-review` | yes | prose | 5 |
| `design-system` | yes | **—** | 0 |
| `documentation-design` | **no** | prose | 3 |
| `experience-status` | yes | **—** | 0 |
| `information-architecture` | yes | **—** | 1 |
| `informational-design` | **no** | prose | 3 |
| `interaction-design` | yes | prose | 4 |
| `journey-mapping` | yes | asset | 1 |
| `marketplace-design` | **no** | **—** | 0 |
| `process-mapping` | yes | asset | 2 |
| `service-blueprint` | yes | asset | 0 |
| `tone-of-voice` | yes | asset | 1 |
| `user-flow` | yes | asset | 0 |
| `workspace-design` | **no** | **—** | 0 |

### `product-engineering`

| Skill | path | form | prose hits |
| --- | :-: | --- | --: |
| `align-value-stream` | yes | asset | 0 |
| `de-risk-intent` | yes | fence | 0 |
| `decompose-intent` | yes | **—** | 1 |
| `discovery-loop` | yes | asset | 0 |
| `diverge-solutions` | yes | fence | 1 |
| `explore-options` | **no** | fence | 1 |
| `frame-domain` | yes | fence | 1 |
| `frame-intent` | yes | asset | 0 |
| `frame-situation` | yes | fence | 1 |
| `identify-opportunities` | yes | asset | 0 |
| `lean-canvas` | yes | **—** | 1 |
| `map-capabilities` | yes | asset | 0 |
| `place-bet` | yes | **—** | 0 |
| `plan-validation` | **no** | fence | 0 |
| `ux-writing` | yes | asset | 0 |

### `core`

| Skill | path | form | prose hits |
| --- | :-: | --- | --: |
| `adapt-to-project` | yes | asset | 1 |
| `author-brief` | **no** | **—** | 0 |
| `author-delivery-brief` | yes | **—** | 1 |
| `bug-fix` | **no** | **—** | 0 |
| `capture-work` | **no** | **—** | 0 |
| `close-work` | yes | **—** | 0 |
| `contract-acquisition` | yes | **—** | 0 |
| `init-project` | yes | **—** | 0 |
| `intake-intent` | yes | asset | 1 |
| `new-spec` | yes | asset | 2 |
| `operational-safety` | yes | **—** | 0 |
| `project-knowledge` | yes | **—** | 0 |
| `receive-brief` | **no** | **—** | 0 |
| `security-checklists` | yes | **—** | 1 |
| `security-checklists-reference` | yes | **—** | 0 |
| `work-intake` | yes | **—** | 0 |
| `work-loop` | yes | asset | 2 |
| `workspace-status` | yes | fence | 6 |

