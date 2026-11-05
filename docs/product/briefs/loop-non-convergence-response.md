# Brief: a work loop notices it is not converging and returns to the right artifact

- **Slug:** `loop-non-convergence-response`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Parent intent:** intent:agent-loop-escalation-recovery
- **Status:** Draft
- **Source / provenance:** Repository origin. The intent `docs/product/intents/agent-loop-escalation-recovery.md` records one 11-round spec-authoring loop and one 8-round checker loop that did not converge. Slice sizing follows [`agent-authoring-input-quality.md`](agent-authoring-input-quality.md) § "Sizing discipline".

## Outcome

When a review-and-repair loop stops converging, the work loop says so from facts it already holds, and the controller has one stated rule for which artifact to return to. A loop that is repairing the same class of defect round after round is shown to the controller before round eight, not after round eleven.

## Success metrics

- Replayed on committed review-round histories (the one source set: files matching `docs/specs/*/notes/*round*`, excluding `amendment-001-grounding-paths.md` and `grounding-pass.md`, which are not review rounds) and on fixtures built from the per-round counts the intent records for its two loops, the repair-size signal flags the first fixture (raw counts only, so no previous-repair share exists for it) by round 7, the previous-repair share flags the second fixture by round 5, and the detector stays silent on every converging committed history. The two loops' own round artifacts are gitignored and are not a replay source.
- The routing rule names a return level (plan, spec, brief, intent, or retire the construct) for each discovery class in the intent's table.
- Each shipped rule carries an activation point and a test that tells activation from presence.

## Scope / Non-goals

**In scope:**

- Measuring which signals separate a non-converging loop from a slow converging one, from git history only.
- An advisory detector in the supervisor's `status` output.
- A routing reference in `work-loop` that maps what a discovery invalidated to the artifact level to return to, including a terminal "retire the construct" branch.

**Non-goals:**

- Blocking a loop on a derived signal. Blocking on derived review signals was measured and killed in [work-loop review economics](../intents/work-loop-review-economics.md).
- A fixed round cap. The intent's H1 has no justified N, and the spike decides whether any threshold exists.
- Classifying findings by judgement (H2's composition signal). Only signals computed from diffs and finding locations are in scope.
- Running fresh live loops to test hypotheses H5 and H6. Those stay research questions until a real loop supplies the case.

## Constraints / Appetite

- Appetite: three small specs, one session each. Slice N1 is research and ships no capability.
- The review-round artifacts are gitignored and machine-local. N1 reads git history and committed review records only, so its answer is reproducible.
- Edits to `work-loop` scripts and references ship outside any supervised integration run. N2 and N3 each need a core release; N1 ships none.

## Assumptions / Risks

- **Riskiest assumption:** the share of a round's findings caused by the previous round's repair (a finding that cites a line the previous diff touched) separates the two recorded loops from converging ones. On the second loop it was 0/10, 3/4, 4/5, 2/5: up for three rounds, then down and has not been tested on a converging loop. N1 tests it on the committed history of merged specs and stops the brief if it does not separate. The control set is thin. The glob `docs/specs/*/notes/*round*` (case-insensitive), less the two excluded files, matches 56 committed files in 13 specs, and 9 of those specs have three or more files (50 files). Few findings cite a line, so N1 defines overlap by cited file and section and reports how many histories qualify. **Stop condition:** if fewer than 5 converging histories qualify, N1 reports that the signal cannot be validated from the repository and N2 and N3 are not started on its strength.
- Counts are not comparable across a change of reviewer instrument, so no detector may be built on raw finding counts.
- A detector that stops healthy work is worse than none, which is why the surface is advisory.

## Proposed slices

Each AC number is a ceiling and a stall threshold, never a floor.

| # | Slice | Owning surface | Verification | Guide | AC ceiling | Gating |
| --- | --- | --- | --- | --- | --- | --- |
| N1 | Signal spike: repair-size bound and previous-repair share, measured from committed history, with pre-registered thresholds and a stated false-positive rate on converging loops; the spec first names the converging control set, drawn from that same source set | `docs/product/research/loop-non-convergence-signals.md` and its reproducing command | The note's arithmetic recomputes from the recorded command on the committed history; thresholds are written before the replay | none, ships no capability | 6 | none |
| N2 | Advisory detector in `work-supervisor.py status`: rounds with findings and previous-repair share, no effect on `next`; the spec decides whether `status` or the review-gate refusal text is the surface | `packs/core/.apm/skills/work-loop/scripts/` supervisor status output | Construction tests over journal fixtures built from N1's cases; a mutation of the threshold flips the output; `next` output is byte-identical with the detector removed | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 8 | after N1, and only if N1's signal separates the cases |
| N3 | Routing reference: discovery class to return level, with the retire-the-construct branch available once a mechanism has failed at the same seam twice | `packs/core/.apm/skills/work-loop/references/` plus one pointer in `SKILL.md` | Rule-name pin in the pack suite; a pin test that the reference names a return level for every row of the intent's table and an activation point; no live-model eval is in this slice | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | 6 | after N1 only to reuse its recorded cases as the table's worked examples; otherwise independent of N2 |

Dependency order is N1, then N2 and N3 in either order.

**Named non-blocking follow-ups:** a live-model eval that the controller routes each class correctly (it needs a model run), and calibrating the retire-the-construct threshold on live loops, once N2 has run on real work for a stated period. It carries no date and blocks nothing here.

## Ready gaps (Draft only)

None open.

## Rabbit holes

- Re-deriving finding classes. N1 uses diff and location overlap only.
- Making N2 blocking. A block needs its own intent and a measured false-positive rate.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Source: repository origin, `docs/product/intents/agent-loop-escalation-recovery.md`. Its six competing hypotheses are narrowed here to the two signals that can be measured without a live loop (H3, and the previous-repair share under H2) and the routing table.
