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
