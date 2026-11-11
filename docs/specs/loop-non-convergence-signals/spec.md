# Spec: Loop non-convergence signals

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** none — authored after the spec is approved
- **Constrained by:** none
- **Brief:** brief:loop-non-convergence-response
- **Discovery:** intent:agent-loop-escalation-recovery
- **Depends on:** none
- **Contract:** none — this slice ships a research note and no capability.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`,
> `What Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material, corrected in place.

## Outcome

The owner of the work loop learns, from committed repository history, whether the share of a review round's findings caused by the previous round's repair separates a non-converging loop from a converging one, and whether repair size predicts the next round's blockers. The answer is one of three verdicts, so the detector slice is started only on a signal that held.

## What Changes

- A research note records the source set, the rules and thresholds written before measurement, the per-history results, and the verdict — `docs/product/research/loop-non-convergence-signals.md`.
- The commands that produce every number are recorded in that note, so a reader reproduces them from a named base commit.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Reusable learning, and the gate for the brief's later slices | Applicable: the detector and routing slices read this verdict | `docs/product/research/loop-non-convergence-signals.md` | eugenelim | The note exists with the three verdict states defined and one stated | `close-work` confirms the brief's N2 Gating cell cites this verdict |
| User promise, architecture, interface, operations, release | Not applicable: no behavior, surface or release changes | none | none | none | none |

## Agent Rules

### Always do

- Write the source-set rule, the overlap definition, the qualification rule and the false-positive ceiling into the note and commit them before any result is computed.
- Read only committed files and git history. Record each command and the base commit it ran on.
- Report counts with their denominators, including histories excluded and why.

### Ask first

- Changing the false-positive ceiling or the minimum number of qualifying histories after the thresholds commit.
- Adding a source other than committed review-round files and the per-round shares the intent records.

### Never do

- Start a model process, or read the gitignored round artifacts of the 11-round or the 8-round loop.
- Edit anything under `packs/`, `packages/`, `tools/`, `tests/` or `.github/`.
- Build a detector on raw finding counts. Counts are not comparable across a change of reviewer instrument.

## Testing Strategy

Goal-based. Every behavior is checked by reading the note and re-running its recorded commands. The reproduction criterion is exercised at the recorded base commit. The ordering criterion is read from `git log`.

## Acceptance Criteria

- [ ] The note defines its source set as the committed files matching `docs/specs/*/notes/*round*`, excluding `amendment-001-grounding-paths.md` and `grounding-pass.md`, and states the count it measured them at (56 files in 13 specs, 9 specs with three or more files, on the base commit it names).
- [ ] The note states, before any result, the overlap definition (a finding is caused by the previous repair when the previous round's diff touched the file or section the finding cites), the qualification rule for a converging history, and a false-positive ceiling of one qualifying converging history in five, flagged at most.
- [ ] `git log` on the delivering branch shows the commit that adds the rules and thresholds before the commit that adds any per-history result.
- [ ] For each qualifying history the note lists every round, its finding count and its previous-repair share, and states how many of the nine candidate histories qualified and why each of the rest did not.
- [ ] The note reports, for the three repair sizes the intent records for the first loop and for every committed history where a repair diff size is available, the next round's blocker count, and states whether the relation is monotone, without a causal claim.
- [ ] The note reports whether a fixture built from the second loop's recorded shares (0/10, 3/4, 4/5, 2/5) is flagged by round 5 under the pre-registered threshold, and labels that check as fitted to the recorded data.
- [ ] The note ends with exactly one verdict from three: separates, does not separate, or cannot be validated from the repository. Fewer than five qualifying converging histories makes the verdict "cannot be validated".
- [ ] When the verdict is not "separates", the note states that the brief's detector slice is not started on this signal's strength.
- [ ] Re-running every command the note records, at its recorded base commit, reproduces each reported number.
- [ ] No file under `packs/`, `packages/`, `tools/`, `tests/` or `.github/` changes in the delivering branch.

## Follow-ons

- eugenelim: `docs/product/briefs/loop-non-convergence-response.md` — the detector slice (N2) and the routing reference (N3), each its own spec after this verdict.

## Assumptions

- Defaulted: Product: a false-positive ceiling of one in five qualifying histories — default: 20%, because the detector is advisory and a false flag costs one glance; if wrong: raise or lower the number before approval and the criteria follow (settled by: eugenelim).
- Defaulted: Technical: the minimum of five qualifying converging histories — default: five, which leaves the ceiling above at most one flag; if wrong: the "cannot be validated" bar moves (settled by: eugenelim).
- Named gap: the first and second loops' own round artifacts are gitignored and machine-local — the by-round claims for those loops rest only on the numbers the intent recorded.
