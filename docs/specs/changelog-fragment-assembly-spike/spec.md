# Spec: Changelog fragment assembly — measurement spike

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0123
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

Platform Core maintainers get measured answers to four claims about the
per-update changelog design that nothing in this repository has measured: merge
independence, deterministic assembly, `/now/` parity at cutover, and site-build
cost at scale. Success is a retained spike report whose figures either supply
the delivery spec's thresholds or kill the design before a delivery contract
pins one.

## What Changes

- A spike report — `docs/product/research/changelog-fragment-assembly-spike.md`
- Merge-independence evidence, fragment arm against a monolith control arm — recorded in that report, re-derivable by `tools/measure-changelog-fragment-merges.py`
- Deterministic-assembly evidence under shuffled enumeration, with its mutation arm — recorded in that report
- `/now/` payload parity and anchor-stability evidence across a simulated cutover — recorded in that report
- Site-build cost at ten times the released-entry count — recorded in that report
- What this spike does **not** answer — ADR-0123's fifth Confirmation signal, that regeneration leaves no tracked diff, and the architecture's § 7 rows for Git cleanliness, Failure diagnosability, and Dependency and privacy posture. Those are delivery verification obligations and stay with the delivery spec, because the spike ships no production assembler for them to observe.
- The delivery spec's thresholds — not written until this report exists

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Reusable learning | Applicable — the whole deliverable is measurement | `docs/product/research/changelog-fragment-assembly-spike.md` | eugenelim | The report, plus the retained stdout of each measurement run quoted in it | The report states a verdict per measurement and names its base commit |
| Decision rationale | Already owned | `docs/adr/0123-product-changelog-per-update-sources-and-generated-views.md` | Platform Core maintainers | The accepted ADR | A kill verdict obliges a new superseding ADR; a survive verdict obliges nothing |
| Maintainer procedure | Applicable — the merge-independence figure must be re-derivable by a reader | `tools/measure-changelog-fragment-merges.py` | eugenelim | The script's module docstring stating its invocation, and its stdout quoted in the report | The script runs from a clean checkout and reproduces the report's counts |
| Current architecture | Applicable | `docs/architecture/changelog-fragment-source.md` | Platform Core maintainers | The architecture delta's `Status` line | The delta stays `Draft` on a survive verdict and is withdrawn on a kill verdict. A build-cost figure at or above the § 7 bar is neither: it leaves the delta at `Draft`, obliges the delivery spec to carry a named performance task, and Platform Core maintainers decide whether it blocks delivery |
| Release history | Not applicable | — | — | — | No released artifact changes, so no changelog entry is owed |
| User promise, product truth, interface compatibility, operations | Not applicable | — | — | — | The spike ships no production code and no user-visible behaviour |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep the throwaway assembler prototype outside the repository, matching the three prior changelog spikes, and quote its retained stdout as the evidence of record.
- Follow `tools/AGENTS.md` for the measurement script, as for any new `tools/` addition. This spike adds only that the script is tracked, documents its own invocation in its module docstring, and is wired to no gate and no Makefile target — matching `tools/measure-changelog-conflicts.py`.
- Record the base commit for every figure this spec's Acceptance Criteria require, because the changelog grows daily and a figure without a base cannot be re-derived.
- Pair each measurement with the control or mutation arm this spec names for it; report a bare treatment figure as inconclusive rather than as a result.
- State a measurement's verdict as survive or kill against the threshold its own criterion names, not as a narrative impression.

### Ask first

- Changing any threshold or corpus size stated in the Acceptance Criteria.
- Adding a fifth measurement, or dropping one because an early figure looks decisive.
- Publishing a verdict that contradicts an accepted ADR.

### Never do

- Add production code to this repository: no tracked `docs/product/changelog.d/` store, no assembler any build **in this repository** invokes, and no new top-level directory, dependency, or package. The measurement script the Always-do rule admits is not production code, and the disposable clone the build-cost measurement uses is outside this repository.
- Edit `docs/product/changelog.md`, `tools/build-site.py`, `tools/check-core-release.py`, `tools/repo/check_release_impact.py`, `.github/workflows/`, or anything under `web/`.
- Report a figure the retained stdout does not contain, or a rate from a sample that measured no rate.

## Testing Strategy

Every behaviour here is goal-based: each measurement is a run whose retained
stdout is the observable, and the report is checked against that stdout. There
is no TDD mode, because the spike ships no production logic with a compressible
invariant — the prototype is throwaway and its correctness is established by its
control and mutation arms rather than by unit tests. There is no manual-QA mode,
because no user invokes anything the spike produces.

- Merge independence: goal-based, exercised by a Git-level integration check over synthetic branches.
- Deterministic assembly: goal-based, with a mutation arm that must change the output.
- `/now/` parity and anchor stability: goal-based, compared against the payload the current parser emits.
- Site-build cost: goal-based, exercised end-to-end by the real `make site-build` in a disposable clone.

## Acceptance Criteria

Each criterion below states its own threshold. Where the threshold comes from
`docs/architecture/changelog-fragment-source.md` § 7, the criterion cites the
row that owns it; § 7 wins where the two ever disagree.

- [ ] The report records, for 20 synthetic branches that each add one `docs/product/changelog.d/<uuid>.md` fragment and nothing else, how many of the 190 unordered branch pairs `git merge-tree` classifies as conflicting on a changelog path; the figure is zero, per § 7 Mergeability.
- [ ] The report records that same figure for a control arm of 20 synthetic branches that each instead prepend one release section to `docs/product/changelog.md`; the figure is greater than zero, without which the fragment arm's zero is not a measurement.
- [ ] The report records, for each arm, how many of the 190 pairs `git merge-tree` exited non-zero on for any reason other than a conflict; the figure is zero in both arms, and a non-zero figure is a harness failure rather than a clean pair.
- [ ] The report records the number of distinct output digests produced by assembling the frozen baseline plus 20 fragments across 5 shuffled directory enumerations; the figure is 1, per § 7 Determinism.
- [ ] The report records the number of distinct output digests across those same 5 shuffled enumerations with the assembler's canonical sort removed; the figure is at least 2.
- [ ] The report records whether the model's `/now/` payload with zero fragments is byte-identical to the complete serialized payload `tools/build-site.py` emits at the named base, per § 7 Historical compatibility; group count, bullet count and the anchor list are recorded as diagnostics and are not the comparison.
- [ ] The report records how many of the 20 authored fragment Highlights bullets appear in the payload exactly once and byte-for-byte; the figure is 20, per § 7 Content integrity.
- [ ] The report records how many of the 20 fragments produce a group in the payload and how many of those groups carry an anchor matching `change-` followed by exactly 32 lowercase hexadecimal digits; both figures are 20.
- [ ] The report records how many historical anchors present in the zero-fragment payload are absent or changed in the twenty-fragment payload; the figure is zero.
- [ ] The report records the five-run median wall-clock duration of `make site-build` for a control arm and for a fragment arm, and the fragment median minus the control median divided by the control median, as a percentage; the figure is under 10%, per § 7 Build performance.
- [ ] The report records the interleaved run order of the two build-cost arms, the discarded warm-up run for each arm, and the ten retained durations.
- [ ] `python3 tools/measure-changelog-fragment-merges.py` prints both arms' conflicting-pair counts and both arms' error counts, and names the base commit it ran against.
- [ ] That same run leaves `git status --porcelain` empty.
- [ ] The report states a survive or kill verdict for each of the four measurements against the threshold its criterion names.
- [ ] The report states an overall verdict that is kill when the merge-independence, determinism, or parity measurement is recorded as kill, and survive otherwise; the build-cost measurement does not enter the aggregation.
- [ ] Every figure the criteria above require is recorded in the report beside the base commit and the corpus size it was taken at.

## Follow-ons

- eugenelim: `docs/specs/product-changelog-fragments/` (not yet created) — the delivery spec for the architecture in `docs/architecture/changelog-fragment-source.md`, authored from this report's figures, and carrying the § 7 rows and the ADR Confirmation signal this spike leaves unanswered. It is out of this spec's scope by the owner's spike-first decision, not deferred from it.

## Assumptions

- Technical: 2,910 fragments is ten times the 291 free-standing released entries the current parser reports at `5b379c51f`, so the fragment arm's model carries 3,201 entries — 11.0 times the current count, not 10.0. Which of the two readings § 7's "ten times the current release-entry count" intends is unsettled, and it would change how a borderline figure is read (settled by: Platform Core maintainers, on reading the run).
- Technical: whether a synthetic corpus of repeated bodies stands in for real prose at that scale is unsettled — it would change how much weight the build-cost figure carries (settled by: the owner, on reading the run).
