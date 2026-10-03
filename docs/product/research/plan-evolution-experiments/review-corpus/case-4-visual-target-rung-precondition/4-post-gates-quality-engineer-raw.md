## Blockers

**1. Pre-T15 carry rules still allow answer-key leakage.** `.context/experiments/codex-headless-sol-loop-confirmation-r1/sealed/integration-carry-restriction.json:13`. The carry restriction still says the substitute attestation may include invariant and field classes, and the human integration steps omit checkpoint 04 even though the JSON withhold list includes it, so a T14 integrator can still place credited answer-key material in the worker sandbox. Fix: the pre-T15 carry contract and integration instructions must forbid invariant/field classes and list checkpoint 04 with the three sealed answer-key files.

**2. The review-policy summary contradicts the governing verdict caveat.** `.context/codex-headless-sol-loop-confirmation-result.md:35`. The top summary says the verdict turns mostly on inherited damage, while the verdict caveat says the governing severe term turns on one repair-origin residual whose interval includes zero. Fix: every verdict summary must state the governing term’s actual basis and uncertainty consistently.

## Concerns

**3. The central arm-adjustment repair record is still unrecomputable.** `.context/experiments/codex-headless-sol-loop-confirmation-r1/sealed/amendment-003-post-review-repairs.json:11`. The amendment still says adjusted values recompute from raw `by_class` counts carried per cell, while the emitted handoff says `by_class` is not carried and names different fields. Fix: the central repair record must name only carried fields or be explicitly superseded by the carried-field definition.

**4. The self-consistency lint is not evidence for the current handoff’s consistency.** `.context/codex-headless-sol-loop-confirmation-result.md:12`. The report still prints stale two-round and 35-finding text beside the current three-round and 76-finding status, while `state/handoff-lint.json` reports clean and the embedded lint summary is from a different run. Fix: the lint and embedded summary must cover review-count/status contradictions for the emitted bytes.

**5. Synthetic controls are not separated from historical launch evidence.** `.context/codex-headless-sol-loop-confirmation-result.md:24`. The report presents the cap and frame refusals as exercised controls even though no process launched after the amendment and the 920 branch is forced-only for this block’s prior total. Fix: post-collection self-tests must be labelled separately from evidence about the 95 historical starts.

**6. The Markdown overstates reproducibility compared with the JSON boundary.** `.context/codex-headless-sol-loop-confirmation-result.md:10`. The Markdown says it reproduces every number without the experiment directory, but the JSON says mutation proofs, grades, scans, frame bindings, and regrade inputs are recorded-only or withheld. Fix: the Markdown must carry the same recomputability boundary as the JSON.

**7. The unbound-tool count is internally inconsistent.** `.context/codex-headless-sol-loop-confirmation-result.md:439`. The report lists nine never-bound tools and then says four analysis-side tools were never in scope, while the review-status JSON repeats four. Fix: use one taxonomy and count for frozen, broken, analysis, reporting, and repair-only tools.
