# Walk — `experience-design`

Walked 2026-09-11 against the rendered site: 5 steps, 20 skills.
Method and the owner routing table are in [README.md](README.md).

This record lives beside the methodology it applies —
[`../guidebook-methodology.md`](../guidebook-methodology.md) — because a walk is
product knowledge about the pack, not a verification record for one change.

## Findings

Ordered by reader impact. Owner decides where the fix lands, not where the
symptom appeared.

| # | Dimension | Owner | Finding | State |
| --- | --- | --- | --- | --- |
| 1 | Handover | guide | Step 4 ran `information-architecture` first, but that skill's own procedure says to read the genre skill's output **before** designing hierarchy. The guide contradicted the skill it documents | Fixed — genre skills, then IA, then `interaction-design` |
| 2 | Handover | guide | Step 2 ran `copy-direction` before `tone-of-voice`, while `copy-boundary.md` — a page in the same guidebook — declares `content-design` → `tone-of-voice` → `copy-direction`. Two pages of one guidebook disagreed | Fixed to the declared chain |
| 3 | Handover | journey | **Root cause of 1 and 2.** `JOURNEY.md`'s `skills[]` entries carry `name`, `description`, `humanTouches` and nothing else. The contract cannot express run order or a dependency, so the sequence exists only in the `whatChanges` prose paragraph and the guide had to infer it | Open — see below |
| 4 | Human vs agent | guide | Seven skills carry **You decide**, but the pack declares three human gates. `service-blueprint`, `process-mapping` and `experience-status` invent gates; `experience-status` is read-only and has no decision at all | Fixed — the three now state no gate |
| 5 | Chat display | guide | **Agent returns** is a noun phrase describing the reply — "A journey map with stages, actions, emotions…" — not anything an agent says. The one surface claiming to show the interaction showed a label | Fixed — see below |
| 6 | Chat display | guide | The push-back blockquote ran the reader's words and third-person narration together with no speaker marker, while the agent's turn carried an explicit `Agent:` prefix | Fixed — both turns are attributed |
| 7 | Starting point | guide | No skill named its own input. The step states prerequisites once, so a reader entering at skill 3 of 4 could not tell what had to exist first | Fixed — the step map gained a `Needs` column |
| 8 | Result | guide | Every skill had a check; the step had none. After eight skills nothing said when you may move on | Fixed — each step closes with its own gate |
| 9 | Orientation | guide | Only step 5 said what follows the pack. Steps 1–4 named the next step but never the loop the pack sits in | Fixed — `Where this leads` names both |
| 10 | Artifact | skill | Only 8 of 20 skills ship a template defining their output. The other 12 write a file whose shape nothing declares, which is why the outline check was inert on all twelve | Open — routed to the pack |
| 12 | Human vs agent | guide | Four **You decide** markers remained against three declared gates: the second gate's trigger covers two skills, so a reader counted four decisions | Fixed — every marker now names its gate id, so the two that share one say so |
| 11 | Orientation | skill | Step 5 is "Review independently" but runs only `design-review`, the self-pass. The pack's third gate fires on the `experience-reviewer` subagent, which a reader cannot type and the page does not explain | Open — routed to the pack |

## Finding 3 — why it is the root cause, and what closing it needs

Findings 1 and 2 are the same defect twice: the guide had to guess a run order
because no machine-readable source states one. Fixing the two pages fixes the
symptom and leaves the generator intact, so the next pack's guidebook will guess
again.

The durable fix is a declared sequence in the journey contract — the schema is
`web/src/lib/journey-schema.ts`, whose `skills[]` shape is
`{ name, description, humanTouches }`. Adding a field there is a contract change
across every published pack, and a journey contract field needs a declaration in
five places, two of which fail silently if omitted. It is therefore recorded
here rather than taken inside this change.

Until it lands, a guidebook's skill order is authored, and this walk is what
checks it.


## Rewalk

Re-walked after the fixes, against the rebuilt site. Every dimension re-checked
across all 20 skills: 0 issues.

| Checked | Result |
| --- | --- |
| Every skill has a row in its step map, with what it needs | 20 / 20 |
| Every agent turn reads as a reply, not a noun phrase | 20 / 20 |
| Every push-back attributes both speakers | 20 / 20 |
| No third-person narration inside a quoted turn | 0 found |
| Every step closes with its own gate and its place in the pack | 5 / 5 |
| `You decide` markers, each naming a declared gate | 4 markers, 3 gates |
| Rendered sweep across all five position surfaces | clean |

**What the rewalk caught that the walk did not.** Retiring the three invented
gates left four markers against three declared gates, because the second gate's
trigger spans two skills. The first walk counted gates against the journey and
found seven; only after fixing did the remaining overlap become visible. That is
the argument for rewalking rather than re-reading the finding list.

**Two findings stay open**, both routed out of the guide: 10 (12 of 20 skills
ship no output template) and 11 (`experience-reviewer` is not runnable and the
step does not say how the independent review happens). Neither is fixable in a
projection.
