# Verification ledger: preservation properties from a bounded consumer map

## Baseline runs — 2026-10-29, Core 3.1.30 (before this change)

Each case ran once in a fresh agent that followed the unchanged
`.claude/skills/new-spec/SKILL.md` over an isolated scratch copy of the case's
`files`, given only the case's `prompt`. The agent could not read `evals/`.
Scoring below is the author's reading against the case's assertions; the
AC-0001 and AC-0002 runs use a separate grader.

### `isolated-private-change-does-not-expand-preservation-proof` — 4 of 4 held

The run declined the expansion: `_trim_label` is private with one caller
(`grep` returned the definition and one call), so no consumer map or
preservation matrix was built. It used local anchors and tests only, and did
not require adapt-to-project or code intelligence.

### `shared-substrate-change-expands-preservation-proof` — 3 of 6 held

| Assertion | Result | Observation |
| --- | --- | --- |
| Recognizes a shared-substrate change | Held | Cited the shared `Node` model and `name_index` feeding every consumer |
| Bounded consumer map over all classes | Not held | Invalidation was dismissed as "none (not node-based)" with no criterion or gap |
| Preservation criteria with allowed delta and falsifiable oracle | Not held | Oracles were stated; no criterion named an allowed delta |
| Distinct evidence for all six properties | Not held | No invalidation-bound criterion; compatibility was `git diff --exit-code` on the Rust file, which forbids change rather than compiling the supported surface |
| Map disposable; feature-only tests insufficient | Held | Map placed in plan `## Design (LLD)`; characterization tests required beyond creation |
| Repository-native evidence only | Held | Reads, `grep`, and one throwaway probe |

## T1 — reference and step-3 pointer, 2026-10-29

- Red: `test_shared_substrate_preservation.py` written first; 11 failed while
  the reference and pointer were absent.
- Green: 11 passed after the reference and the step-3 pointer landed; the
  `new-spec` suites pass (278 passed, 82 subtests).
- Plan error found: T1's pinned `Tests:` puts the guide-link pin in the pack
  test, but `tools/lint-pack-test-boundary.py` check 8 (pack-tests-stay-in-pack)
  forbids a pack test reading `guides/`. The guide paragraph is written and its
  link resolves (`grep -c` prints 1); `validate_guides.py`,
  `lint-guide-titles.py`, and `lint-guides-no-repo-only-refs.py` pass. Routed
  to a controlled amendment.

## T2 — consumer-map disposability pin, 2026-10-29

- `test_consumer_map_disposable.py`: 2 passed through
  `_subject_source.project_legacy_subject` over a temporary git repository and
  `_acceptance.evaluate_verdict`.
- Mutation: a throwaway plugin that stops `_is_excluded` from dropping the spec
  directory turns `test_plan_resident_map_is_disposable` red with three
  distinct fingerprints; the plugin was deleted after the run.

## Amendment review — deferred Nits, 2026-10-29

- Deferred: T1's `Done when` grep proves the guide names the reference path,
  not that the relative link resolves (`plan.md:139-141` against `:47`). The
  link was resolved by hand from `guides/core/how-to/` to the shipped file.
- Deferred: T1's `Mode:` line does not name the goal-based grep in its
  `Done when` (`plan.md:126-127`).

## Wave 1 accounting, 2026-10-29

T1 and T2 (wave index 0) were implemented in the controller session, not by an
`implementer` subagent. The owner directed recording them `human-directed`
after the fact. Wave-1 gates: `make lint-ruff lint-mypy` pass; targeted suites
360 passed, 82 subtests; T1's `Done when` grep prints `1`;
`tools/lint-pack-test-boundary.py` passes.

## T4 — graded runs, 2026-10-29

Each run was one fresh agent following a copy of the named projection with
`new-spec/evals/` excluded at copy time; a search of both copies found no file
naming either frozen case. Each agent got an isolated git copy of its case's
`files` and only its case's `prompt`. A separate grader agent per run read only
that run's output and the case's `assertions`.

| Run | Projection | Score |
| --- | --- | --- |
| AC-0001 — `shared-substrate-change-expands-preservation-proof` | rebuilt, Core 3.1.33 | 6 of 6 held |
| AC-0002 — `isolated-private-change-does-not-expand-preservation-proof` | rebuilt, Core 3.1.33 | 4 of 4 held |
| Baseline — shared-substrate case | merge base, Core 3.1.32 | 6 of 6 held |
| Baseline — isolated case | merge base, Core 3.1.32 | 4 of 4 held |

The AC-0001 and AC-0002 outputs were graded verbatim. The two baseline outputs
were graded from controller-condensed copies that keep every criterion, map
row, and trigger verdict but shorten the assumption blocks.

**The assertions do not separate the two projections at one run per case.**
The 3.1.30 baseline earlier the same day held 3 of 6 on the shared-substrate
case; the 3.1.32 baseline held 6 of 6. Differences visible in the outputs, not
scored by any assertion:

- The rebuilt run loaded the reference, named both exclusions and why neither
  applied, and cited the filter gap on `rank`.
- It stated an allowed delta on every preservation criterion and took every
  oracle from the base revision; the baseline named deltas on two criteria.
- It closed serialization as unreachable with a cited search, and named the
  missing Rust toolchain as a gap that blocks review; the baseline did neither.
- It stated the sustained-finding clause and that `spec.md` does not cite the
  map.
- The baseline reported that its skill had no preservation step and built its
  map from rubric class 2 unprompted.

T4 accounting: the graded runs need fresh, isolated agents, which an
`implementer` subagent cannot start, so the controller ran T4. The owner
directed recording it `human-directed`, and directed shipping on the met
criteria with the non-discrimination stated in the pull request.

## Code review, 2026-10-29

- `adversarial-reviewer`: 3 raised; adjudication refuted 2 and sustained 1 as a
  Nit. Deferred: the shipped later-discovery routing ("the plan before
  approval, or the verification ledger after") is more precise than plan
  Design (LLD) part 6 ("a plan edit"); it agrees with the work-loop
  verification-ledger rule. Citations: `shared-substrate-preservation.md:111`,
  `plan.md:96-98`.
- `experience-reviewer`: 10 raised; adjudication refuted 5 and sustained 1
  Concern and 4 Nits. Fixed in the guide paragraph: the trigger now says "adds
  or changes", the generic reading is explained in plain words, the skip cases
  are plain and say the skill confirms them, and the long sentence is split.
  Deferred: plain-words glosses for "oracle" and "analogues" in the skill
  reference (`shared-substrate-preservation.md:70,81`).

The guide repair was a controller fix under the work-loop FIX step (a small fix diagnosis hands over); the reopened wave re-records T4 as `human-directed`, as the owner directed for T4.
- `experience-reviewer` round 2: SHIP IT. Deferred: the clause "once it has
  confirmed that from the repository" sits after the second skip case only
  (guide step 2); the reference requires the proof for both. Deferred Nit:
  "shared read path" and "new item" paraphrase the reference's terms.
