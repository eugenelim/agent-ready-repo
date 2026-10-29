# Verification ledger: preservation through typed review

## Inputs, 2026-10-29

- C2 `grounding-preservation-evidence` is Shipped at squash commit `c8d1d817a`
  (Core 3.1.37).
- Acceptance-centered Slice 2 `structured-review-boundary` is Shipped; it
  merged `review-report.v1` and `finding.v1` at
  `bfe30052cc760cc0e3c79e95582c3bfc6c87cd0e`. C3 consumes both unchanged.
- Acceptance-centered Slice 4: `execution-supervisor-core`,
  `execution-supervisor-attempt-security`, and
  `execution-supervisor-review-gate` are Shipped dark;
  `execution-supervisor-cutover` is Implementing with its main T2 open. C3
  touches no file that T2 lists.

## Spec-stage review, 2026-10-29

Shaping review reached Clean in round 7 and again on the round-8 delta.
Adversarial review fell from 10 findings in round 1 to one judgement Concern and
one Nit in round 8, both repaired as wording. Findings per round, shaping then
adversarial: 11/10, 2/6, 3/5, 2/3, 2/4, 1/3, clean/3, clean/2. The owner
approved the spec and plan after round 8.

## T1 — reviewer guidance, 2026-10-29

- Red: `test_preservation_review_guidance.py` failed 15 of 15 with the reviewer
  edits reverted.
- Green: the pin module plus the 13 suites that read the reviewer files pass,
  271 tests.
- A graded run showed one finding with `schema_version` as the string `"1"`,
  which `finding.v1` refuses. Both sections now state the integer `1`, and a pin
  in AC-0002's test holds it.

## T2 — typed reports through the generic path, 2026-10-29

- `test_preservation_review.py` passes 12 tests in 3.5s through the shipped
  review modules, `EvidenceStore`, and the acceptance evaluator.
- Mutations seen to red, then restored: AC-0009's finding pointed at the
  lifecycle property; AC-0014's assessment switched to supported; AC-0011's
  clean report given a finding; AC-0015's indeterminate report swapped for a
  clean one.
- `evaluate_verdicts` returns verdicts without a property id, so the suite pairs
  them with the properties by order.

## T3 — reviewer eval cases, 2026-10-29

- Red: `test_preservation_review_eval.py` failed 5 with the cases absent.
- Green: it and the two existing eval-construction suites pass, 10 tests.
- The fixture spec line reads `- **Status:** Approved`; the pin checks that
  line.

## T4 — release and projection, 2026-10-29

- Core is 3.1.38 in both manifests, one patch above the base's 3.1.37, with
  fragment `97414e01-b22e-46c8-aeca-637b383a4df9`.
- `git diff --name-only <base> HEAD` lists nothing under `contracts/`,
  `work-loop/scripts/`, `work-loop/references/`, nor `work-loop/SKILL.md`.
- `packs/core/pack.toml` has no `[dependencies]` table.
- `agentbundle catalogue verify --root .` exits 0.
- Self-host re-run leaves no diff. `make lint-ruff lint-mypy` is clean.

## T6 — code-review repairs, 2026-10-29

- AC-0007 pin, re-observed by the controller: it fails on the pre-T6 check 35
  text, on check 35 without the named-family clause, and on check 35 without
  the "at least one artifact" condition, and passes on the shipped text.
- The implementer observed each other repaired pin red first: AC-0006 on the
  old check 10 wording; AC-0017 with `outline` renamed, with a value filter
  added to it, and with the ordinary-calls expected side made a literal;
  AC-0021 with `import yaml` appended to the eval module; AC-0008 with a
  planted "Adapt-To-Project and Code Intelligence"; AC-0002 with
  `schema_version` dropped from the caller sentence. The AC-0013 full-receipt
  comparison was not run against a mutant.
- AC-0021: `test_new_modules_import_only_stdlib_and_pytest` scans all three new
  modules by literal path and passes. The eval pin loads the fixture
  `graph.py` by path, and the fixture imports only `dataclasses`.
- The three new modules plus the T1 regression suites and the two
  eval-construction suites pass, 295 tests with 51 subtests in 12.9s.
- `make lint-ruff lint-mypy` is clean. Self-host re-run leaves no diff.
- The fixture loader sets `sys.dont_write_bytecode`, so the suite writes no
  `__pycache__` into the shipped skill tree.

## T5 — graded runs, 2026-10-29

**Method.** Each run is one fresh agent confined to a copy of the projection
and a working directory holding only the case's files, given only the case's
prompt. Head is the rebuilt Core 3.1.38 projection; base is the projection at
`c8d1d817a` (Core 3.1.37). Each copy holds only Core's projected skills and
agents, with every `evals/` directory removed and `adapt-to-project` removed;
neither Pi nor a code-intelligence capability is present. A reviewer case's
agent adopts the projected reviewer definition. Graders read only the
assertions and the outputs, labelled `output1` and `output2` in the order in
[`blind-mapping.json`](graded-runs/blind-mapping.json).

| Case | Head | Base |
| --- | --- | --- |
| `shared-substrate-change-expands-preservation-proof` | run 1: 5 of 6; run 2: 4 of 6 | 5 of 6 |
| `isolated-private-change-does-not-expand-preservation-proof` | 4 of 4 | 4 of 4 |
| `shared-substrate-feature-tests-do-not-prove-preservation` | 5 of 5 | 5 of 5 |
| `typed-review-binds-missed-consumer-to-preservation-criterion` | 6 of 6 | 4 of 6 |
| `typed-review-binds-weak-evidence-to-preservation-criterion` | 6 of 6 | 4 of 6 |

- **Both reviewer cases separate the projections.** Both base reviewers found
  the defect but returned Markdown with no typed report and no
  `affected_acceptance_criteria`, failing those two assertions. Both head
  reviewers returned one JSON block binding the finding to `CRIT-3` or `CRIT-2`.
  Neither head reviewer raised a reachability or missed-consumer finding
  against the filtered search path. The admitted head runs are the `-r3`
  outputs, run on the final reviewer guidance and graded against the final
  assertions; the `-r1` and `-r2` outputs are kept as evidence for the
  changes that replaced them.
- **The positive authoring case misses on head and base alike.** The
  `new-spec` projections are byte-identical, because C3 changes no `new-spec`
  file. Head run 1 never said the consumer map is disposable. Head run 2 also
  left bounded invalidation as a named gap instead of a criterion. The base run
  missed the invalidation assertion only. C1's single graded run of this case
  held 6 of 6 on Core 3.1.33.

- **Run inventory.** Pack versions are in the Method paragraph, and the
  Head-run replacements bullet owns what each guidance commit changed. Head
  outputs by guidance state: `-r1` ran on the guidance at `50c2019c3`; `-r2` ran
  after `fe2421c44`; `-r3` ran after `c1cf109a6`. The two unsuffixed head
  outputs (`isolated-private-change-does-not-expand-preservation-proof` and
  `shared-substrate-feature-tests-do-not-prove-preservation`) hold the
  `new-spec` and `work-loop` guidance C3 does not change after `50c2019c3`, so
  their result does not depend on that split.
  Grade files and the head output each graded: `grades-case1.md` (head),
  `grades-case2.md` (head), `grades-case3.md` and `grades-case4.md` (`-r2`; the
  `-r1` outputs of those two cases are kept ungraded), `grades-case5.md`
  (`-r1`), `grades-case5r.md` (`-r2`, one output), `grades-case3r.md` and
  `grades-case4r.md` (`-r3` against the final assertions). The base outputs of
  the two reviewer cases were graded in `grades-case3.md`/`grades-case4.md`
  against the earlier assertions and again in the `r` files against the final
  ones, with the same 4 of 6.
- **Run conditions held for every listed run.** For every head, base, and
  rerun output in `graded-runs/`, the copy held only Core's projected skills
  and agents with no `adapt-to-project`. The agent had no code-intelligence
  capability and no Pi. Each run used a general-purpose agent confined to a
  `/tmp` copy with no code-intelligence or Pi tool.
- **Head-run replacements.** The two reviewer cases' `-r2` runs replace their
  `-r1` runs. The guidance change is commit `fe2421c44`, which set the typed
  report section's finding `schema_version` to "the integer `1`". Their `-r3`
  runs replace `-r2` after commit `c1cf109a6`, which gave check 35 the
  artifact condition and the named-family clause, named spec-stage check 6 in
  check 10, and scoped the missed-consumer case's filtered-search assertion to
  reachability or missed-consumer findings. The `-r3` runs and the base runs
  are graded against those final assertions
  ([`blind-mapping-r3.json`](graded-runs/blind-mapping-r3.json)): 6 of 6 on
  head and 4 of 6 on base for both cases. The positive
  authoring case's second head run (`-r2`) is recorded only, with no pass
  requirement. Its rerun is not a replacement under the rule, because the
  `new-spec` guidance is unchanged.
- **Pass result.** The admitted head runs of AC-0022's four pass-required
  cases hold every assertion (4/4, 5/5, 6/6, 6/6). The positive authoring
  case's scores are recorded without a pass requirement, per the owner's
  amendment.

Outputs and grades: [`graded-runs/`](graded-runs/).
