# Plan: verify entries

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, self-host, eval harness, no internal citations); `tests/AGENTS.md` (roster placement and its three wiring edits); `docs/specs/work-loop-evidence-modes/` and its `test_evidence_modes_contract.py` as the analogous section-scoped guidance delivery; `tests/roster/test_evidence_store_schema_parity.py` as the analogous schema-validation roster test; `docs/product/research/product-run-docs-survey.md` for the detection order and default name. Deviation: `tests/roster/test_cognitive_load_repository_contract.py` pins root `AGENT_RULES.md` byte-identical to the seed and row-free, which forbids any adopter row in this repository; T5 relaxes both pins for the root file to "seed bytes, then table rows".

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open, and
> the run continues with every finished task still finished. Execution
> observations belong in `docs/specs/<feature>/notes/verification-ledger.md` (or
> the adopter's equivalent). A genuine error in a protected section follows the
> controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place, before or after approval, while no
> attempt is open.

## Approach

The doctrine lands first (T1), because every other task points at it: the routing sentences, the seeding paragraph, the guide, the dogfood entry, and the receipt test all cite its anchor or parse its stated fields. The release (T8) lands before the live run (T6), so the run drives the tree that ships. The dogfood is the riskiest part: its entry must run live against the real CLI and yield a receipt the unchanged schema accepts. The spike before review showed `install` then `diff` exits 0 on a clean scratch install and 1 with the tampered file named. T5 also relaxes two roster pins on root `AGENT_RULES.md` without loosening what they protect: the seed's preamble and header, and one-hop routing. Checks that compare against a moving merge base run once at closeout and live in the ledger, never in a standing suite.

## Constraints

- ADR-0144: the supervisor owns procedure and commits gate evidence directly; this delivery adds no evidence-store writer and no script edit.
- `evidence-receipt.v1` is consumed unchanged; `observation.type`, `outcome`, and `producer.class` are free strings whose admissible values come from each criterion's `required_observations`.
- The architecture's legacy projection reserves `manual-observation` for a named human authority, so an agent's drive is a `command-result`; a criterion whose policy requires a human observation is not discharged by a verify-entry receipt.
- The seed `AGENT_RULES.md` table ships empty, and the catalogue lint admits only `.agents/rules/*.md` read targets in pack-shipped rows. Self-host projects core seeds onto this repository's root unless `EXCLUDED_PATTERNS` in `packages/agentbundle/agentbundle/build/self_host.py` marks the path seeded-once; root `AGENT_RULES.md` joins `docs/README.md` and the other seeded-once paths there, because the seed itself says an adopter adds the rows it needs.
- `test_evidence_modes_contract.py` reads `verification-modes.md` from `## Behavior pin` to `## Measurement`, and from `## Measurement` to end of file; the new section goes before `## Behavior pin` so neither region changes.
- A standing test never compares against the merge base: on main the merge base is `HEAD`, so such a test checks nothing, and a later legitimate change turns it red.
- The supervisor protects the spec directory during a worker attempt, so ledger records are controller commits between attempts.
- The concurrent run-based finding settlement change edits `work-loop` FIX and review-assessment scripts; this change edits neither.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** T6's live and failing runs of the dogfood entry.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Maintainer procedure | T1, T2, T3 | `test_verify_entries_contract.py` green | suite green at the delivery commit |
| Interface compatibility | T4, T8 closeout | `test_verify_entry_receipts.py` green | schema diff recorded empty in the ledger |
| User-facing promise | T7 | roster guide assertion | guide reads as stated |
| Operations | T5, T6, T8 closeout | roster entry assertions; ledger records | live run's commit check recorded |
| Decision rationale | none — survey already committed | survey file | cited from spec `Discovery:` |
| Release history | T8 | version-equality assertion; fragment | `check-core-release.py` exit 0 recorded |

## Design (LLD)

### Design decisions

Owned by: T1, T4, T5, T6, T8, T9, T11.

**Section shape.** `## Verify entries` sits between `## Exploratory / visual fuzz` and `## Behavior pin`. Its sub-headings, in order: When an entry is needed, Where entries live, Building an entry, Proving an entry, Recording and promoting, Drift, Fields, Rules, Grades, Receipt mapping, Placeholders and trust. Each section criterion lives under exactly one sub-heading, so a test reads one sub-section.

**Receipt mapping.** Under `### Receipt mapping`, a three-column table `| Grade | observation.type | outcome |`: `live-verified`, `build-only`, `blocked`, and `failed` map to `command-result`; `test-verified` maps to `test-result`; `failed` from a targeted test also maps to `test-result`, so `failed` has one row per type. A `blocked` receipt records the command that could not complete (a failed doctor or launch); a surface blocked on an unanswered offer records no receipt, because nothing ran. Below the table, one line each states `schema_version` (`1`), `receipt_id` (`verify:<surface>:<run-id>`), `freshness_mode` (`exact-subject`), and `producer` (`{"class": "verify-entry", "identity": "verify:<surface>"}`), each in a code span the test extracts. `acceptance_fingerprint` is the supervised run's current fingerprint, or `git:<commit>` of the tree driven when no supervisor runs; no exact-subject policy matches the latter, so a light-mode receipt is audit-only. `lineage.criterion_ref` and `selector.term` come from the task. A policy lists the satisfying grade in a term's `outcomes` and names `failed` in its contradiction rule; `blocked` satisfies nothing.

**Mutation proof, not receipt.** The failing proof run fills `mutation-proof.md`'s record with the entry's evidence check as its catching test and one deliberate break of the driven subject as its exact mutation, the break standing in for that reference's revert to the pre-fix implementation. It reports no grade and no receipt, so it can never contradict the real subject.

**Locating the file.** "Covers the surface" means the file already states how to launch or drive that surface. Agent instruction files (`AGENTS.md` and host equivalents) and host skills are sources to map, never entry homes: a seeded `AGENTS.md` loads `AGENT_RULES.md`, so a row routing back to it would loop, and every session would pay for the entry. The offer names the file and the fields to add; on acceptance the entry is written there under a `## Verify: <surface>` heading. While the offer is unanswered the run grades the surface `blocked` and names the pending offer. One `AGENT_RULES.md` row routes to the file, under the same acceptance, with a `when` naming verification of those surfaces. The verify file never mentions `AGENT_RULES.md`, so routing stays one hop.

**Placeholders.** Raw transcripts stay in an evidence directory version control ignores. Anything copied into a committed record replaces absolute paths with `<checkout>`, `<scratch>`, or `<evidence-dir>`, and drops hostnames, usernames, and credential values.

**Template.** `assets/verify-entry.md` is one `## Verify: <surface>` block with a `### <Field>` heading per field and an angle-bracket placeholder under each. It carries no link, so a copy has nothing to dangle; the section names the template.

**Dogfood entry.** `docs/VERIFICATION.md` holds `## Verify: agentbundle CLI`. Launch is the checkout's own module, `PYTHONPATH=<checkout>/packages/agentbundle python3 -m agentbundle` (written `<ab>` below), so the run drives the tree under change. Doctor: `<ab> --version` exits 0. Ready: `install` exits 0 and `<scratch>/repo/.agentbundle-state.toml` exists. Drive, in order: `<ab> render <checkout>/packs/core --output <scratch>/render` (its evidence is exit 0 and `<scratch>/render/apm/core/.apm/skills/work-loop/SKILL.md` present; a direct-install adapter target such as `codex` selects no distribution recipe and writes nothing); `git init <scratch>/repo`; `<ab> install <checkout> --pack core --scope repo --adapter codex --yes --output <scratch>/repo`; `<ab> diff --root <scratch>/repo --scope repo <checkout>/packs/core`. Evidence: each command, exit status, and output written to `<evidence-dir>` = `.context/verify/agentbundle-cli/<run-id>/`, ignored by Git. Cleanup removes only `<scratch>`, the directory the run created with `mktemp -d`, then checks `<evidence-dir>` still holds the transcript. Proof limits: `diff` proves the install matches a fresh render, not that installed skills behave. Stand-in gap: Codex is the one adapter driven; the other adapters stay uncovered.

**`AGENT_RULES.md` pins.** Two assertions in `tests/roster/test_cognitive_load_repository_contract.py` pin root `AGENT_RULES.md`: the byte comparison of the root file with the seed, and `rows == []` over the root file's table rows. Today the seed is row-free only because the root must equal it, so T5 adds a new assertion that reads the seed file and finds no table rows. For the root file both existing assertions change to: the root starts with the seed's bytes, and every non-blank line after them is a three-cell table row whose `read` cell is one backticked repository-relative path that exists and whose target does not mention `AGENT_RULES.md`.

**Roster receipt test.** `tests/roster/test_verify_entry_receipts.py` parses the mapping table and the four code-span field forms from the shipped section, fills `<surface>` and `<run-id>`, adds placeholder `criterion_ref` (`criterion-placeholder`), `term` (`verify`), and fingerprint (`git:0000000`), and validates each receipt with `jsonschema`'s `Draft202012Validator`. It validates every fenced `json` block under the ledger's `## Receipts` heading, and scans `docs/VERIFICATION.md` and the ledger for the AC-0037 path and email patterns.

**Delivery-time checks.** The supervisor records the commits it makes, so the branch is not rebased while the run is open. Once the run is terminal, the controller fetches `origin`, rebases, and repeats the entry's live drive on the rebased tree, recording that run and its receipt in the ledger. Right after it, the controller runs the schema diff (AC-0023), the live-run commit check (AC-0026), the unedited-suites diff (AC-0029), `tools/check-core-release.py --base "$(git merge-base origin/main HEAD)"` (AC-0038), and self-host followed by `git diff --exit-code` (AC-0031), and records each command and exit status in the ledger. A non-zero result, or a further upstream move before the PR, goes back through T8 (version and fragment) and then T6.

## Tasks

Every pack test function in `packs/core/tests/skills/work-loop/test_verify_entries_contract.py` is named for its task (`test_t1_…`, `test_t2_…`, `test_t3_…`, `test_t8_…`, `test_t9_…`), so each `Done when` selects one task's tests with `-k tN_`.

### T1: Verify-entry doctrine and template

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/references/verification-modes.md`, `packs/core/.apm/skills/work-loop/assets/verify-entry.md`, `packs/core/tests/skills/work-loop/test_verify_entries_contract.py`

**Tests:** no stub (goal-based — content check)
- AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0032, AC-0033: each test reads one sub-section of `## Verify entries` (design: Section shape) and asserts its statements.
- AC-0013: reads the template's `### ` headings in order against the AC-0011 field list, and asserts every non-heading line is a `<…>` placeholder.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_verify_entries_contract.py -q -k t1_` exits 0.

### T2: Route from PLAN and the finish checklist

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/tests/skills/work-loop/test_verify_entries_contract.py`

**Tests:** no stub (goal-based — content check)
- AC-0019: PLAN step 7's task-zero paragraph, read from `**Confirm the mechanism exists before claiming the mode` to `8. **Design construction tests up front.`
- AC-0034: the finish checklist's "Verification passed" item, read from `- [ ] **Verification passed.**` to `- [ ] **Review passed, residuals surfaced.**`.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_verify_entries_contract.py -q -k t2_` exits 0.

### T3: Seeding and eval cases

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/adapt-to-project/SKILL.md`, `packs/core/.apm/skills/work-loop/evals/evals.json`, `packs/core/.apm/skills/adapt-to-project/evals/eval_queries.json`, `packs/core/tests/skills/work-loop/test_verify_entries_contract.py`

**Tests:** no stub (goal-based — content check)
- AC-0020: the `### Compose without taking ownership` section of `adapt-to-project` SKILL.md, to `## Pre-flight`.
- AC-0021: the three new case ids in `evals.json` with their fields.
- AC-0035: one query in `eval_queries.json` containing `verify entr` with `should_trigger` true.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_verify_entries_contract.py -q -k t3_` exits 0.

### T4: Receipt fit roster test

**Depends on:** T1

**Touches:** `tests/roster/test_verify_entry_receipts.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`, `.workspace-prune-protected.toml`

**Tests:** no stub (goal-based — schema validation)
- AC-0022: design: Roster receipt test, the mapping half.
- Wiring: a named build-check step above the bulk `pytest tests/ -q` step, a `LOCAL("test-after-build-check")` disposition and phase entry in `lint-ci-parity.py`, and `docs/specs/verify-entries` in `.workspace-prune-protected.toml`, because the test names the ledger path.

**Done when:** `python3 -m pytest tests/roster/test_verify_entry_receipts.py -q -k mapping` exits 0, and `python3 tools/lint-ci-parity.py` exits 0.

### T5: This repository's entry and route

**Depends on:** T1, T4

**Touches:** `docs/VERIFICATION.md`, `AGENT_RULES.md`, `tests/roster/test_cognitive_load_repository_contract.py`, `tests/roster/test_verify_entry_receipts.py`

**Tests:** no stub (goal-based — content check)
- AC-0024: the entry's twelve field headings.
- AC-0036: the Drive field holds the `render`, `install … --adapter codex`, and `diff` commands of design: Dogfood entry.
- AC-0037: the path and email scan over `docs/VERIFICATION.md` and, once it exists, the ledger.
- AC-0025: design: `AGENT_RULES.md` pins.

**Done when:** `python3 -m pytest tests/roster/test_verify_entry_receipts.py tests/roster/test_cognitive_load_repository_contract.py -q -k "not ledger"` exits 0.

### T6: Prove the entry live and failing

**Depends on:** T5, T8

**Touches:** `docs/specs/verify-entries/notes/verification-ledger.md`

**Approach:** the controller drives the entry and commits the ledger between attempts; the attempt itself carries any entry correction the run found and the ledger tests. The rebased-tree rerun belongs to closeout.

**Tests:** visual / manual QA — drive `docs/VERIFICATION.md`'s entry from the checkout as written.
- AC-0026: one full run graded `live-verified`, with each command, exit status, and placeholder-redacted output, and its receipt in a fenced `json` block under `## Receipts`.
- AC-0027: one mutation-proof record: append a line to `<scratch>/repo/.agents/skills/work-loop/SKILL.md`, observe `diff` exit 1 naming that path.

**Done when:** `python3 -m pytest tests/roster/test_verify_entry_receipts.py -q` exits 0 with the ledger tests included.

### T7: Adopter-facing explanation

**Depends on:** T1

**Touches:** `guides/core/explanation/core-pack.md`, `tests/roster/test_core_onboarding_documentation.py`

**Tests:** no stub (goal-based — content check)
- AC-0028: the guide's `## Why the loop` section.

**Done when:** `python3 -m pytest tests/roster/test_core_onboarding_documentation.py -q` exits 0.

### T8: Release and projection

**Depends on:** T1, T2, T3, T7

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a new fragment under `docs/product/changelog.d/` from `tools/changelog.py new`, adapter projections via self-host, `packs/core/tests/skills/work-loop/test_verify_entries_contract.py`

**Tests:** no stub (goal-based — version and exit status)
- AC-0030: `test_t8_…` asserts both version fields are equal.
- AC-0029, AC-0031: the three named suites and the catalogue commands.
- AC-0023, AC-0038, and the delivery halves of AC-0026, AC-0029, and AC-0031: closeout, after the run is terminal (design: Delivery-time checks). Each command and its exit status is recorded in the ledger; a non-zero result returns the work to this task, then the rerun.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_verify_entries_contract.py packs/core/tests/skills/work-loop/test_evidence_modes_contract.py tests/roster/test_tdd_stub_lifecycle_contract.py packs/core/tests/skills/adapt-to-project/test_adapt_skill_body.py -q` exits 0, `python3 tools/changelog.py validate` exits 0, `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` exit 0, and `agentbundle catalogue self-host --root . --write && git diff --exit-code` exits 0.

### T9: Repair code-review findings

**Depends on:** T1, T3, T5, T6

**Touches:** `packs/core/.apm/skills/work-loop/references/verification-modes.md`, `packs/core/.apm/skills/work-loop/evals/evals.json`, `packs/core/tests/skills/work-loop/test_verify_entries_contract.py`, `tests/roster/test_verify_entry_receipts.py`, `tests/roster/test_cognitive_load_repository_contract.py`, `docs/specs/verify-entries/notes/verification-ledger.md`

**Approach:** the ledger rerun is a controller commit between attempts, as in T6. T9 does not run self-host: the run pins the installed skill, so the supervisor's `regenerate` step rebuilds the adapter projections after review readiness, and closeout checks AC-0031 on the result. Its new tests in `test_verify_entries_contract.py` are named `test_t9_…`.

**Tests:** no stub (goal-based — content check, plus a live rerun of the dogfood entry)
- AC-0004: `### Where entries live` states that agent instruction files and host skills are mapped but never hold an entry, and that the human-facing offer and the `docs/VERIFICATION.md` fallback apply otherwise.
- AC-0014: the grade a run stopped at run start reports — `blocked` for doc drift or a harness gap, `failed` for a product bug — is stated under `### Grades`, the sub-section AC-0014 owns; the ledger grades run r1 accordingly.
- AC-0025: a roster assertion that some root `AGENT_RULES.md` row has the read cell `` `docs/VERIFICATION.md` ``; the row check rejects an absolute, backslash, empty, `.`, or `..` segment, reads each target through `file_safety.read_confined_regular_file`, and records a missing or unsafe target as a problem instead of raising.
- AC-0026 (visual / manual QA, gated by the closeout commit check): the ledger's live run is driven from a commit that contains `docs/VERIFICATION.md` as driven, records each command verbatim (cleanup included) with its exit status and placeholder-redacted output, and its receipt's fingerprint is `git:` of that commit.
- AC-0021: the `verify-entry-missing-is-task-zero` reference answer requires a run from start to finish.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_verify_entries_contract.py tests/roster/test_verify_entry_receipts.py tests/roster/test_cognitive_load_repository_contract.py -q -k "not self_host_skill"` exits 0; the deselected projection check waits for the supervisor's `regenerate` step.

### T10: Place the run-start grade under Grades

**Depends on:** T9

**Touches:** `packs/core/.apm/skills/work-loop/references/verification-modes.md`, `packs/core/tests/skills/work-loop/test_verify_entries_contract.py`, `docs/specs/verify-entries/notes/verification-ledger.md`

**Approach:** the ledger's run r4, which replaces r3's non-verbatim record, is a controller commit made before this task's attempt.

**Tests:** no stub (goal-based — content check)
- AC-0014: the run-start grade sentence moves from `### Drift` to `### Grades`; `test_t9_drift_grades_run_start_stop` reads `### Grades`.
- AC-0026 (visual / manual QA, gated by the closeout commit check): the ledger's run r4 shows the entry's commands as written, `mktemp -d` and `git init` included.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_verify_entries_contract.py tests/roster/test_verify_entry_receipts.py -q` exits 0.

### T11: Keep root AGENT_RULES.md repository-owned

**Depends on:** T5

**Touches:** `packages/agentbundle/agentbundle/build/self_host.py`, `packages/agentbundle/tests/build_pipeline/test_self_host_check.py`, `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/pyproject.toml`, a new agentbundle fragment under `docs/product/changelog.d/`, and any test that pins the agentbundle version

**Approach:** follow the seeded-once precedent of `docs/README.md`: one `EXCLUDED_PATTERNS` literal with a comment, and a regression test that a curated root `AGENT_RULES.md` survives reprojection. The agentbundle version moves one patch, per `packages/AGENTS.md`.

**Tests:** no stub (goal-based — regression test and exit status)
- AC-0025: a reprojection over a root `AGENT_RULES.md` that carries an adopter row leaves that row in place, and `agentbundle catalogue self-host --root . --write` leaves this repository's row untouched.
- AC-0031: self-host on the delivery tree leaves no tracked change.

**Done when:** `python3 -m pytest packages/agentbundle/tests/build_pipeline/test_self_host_check.py -q` exits 0, and `agentbundle catalogue self-host --root . --write` followed by `git diff --exit-code -- AGENT_RULES.md` exits 0.

### T12: Close the agentbundle release paperwork

**Depends on:** T11

**Touches:** `docs/architecture/pack-layout.md`, `docs/specs/verify-entries/spec.md` (What Changes and Durable Outputs, working material)

**Approach:** the repair commit carries the `Engine-Change-RFC:` trailer `docs/guides/how-to/cut-a-package-release.md` requires for a range that touches `packages/agentbundle/`.

**Tests:** no stub (goal-based — exit status and content)
- AC-0031: `python3 tools/lint-catalogue-curation-guard.py --root . --base origin/main` exits 0.
- AC-0025: `docs/architecture/pack-layout.md` lists root `AGENT_RULES.md` among the seeded-once paths, not the seed-projected ones.

**Done when:** `python3 tools/lint-catalogue-curation-guard.py --root . --base origin/main` exits 0.

## Risks

- A spike install once reported drift on a fresh scratch install and did not reproduce in two retries. If it recurs in T6 it is a product bug to report, never an expected result in the entry.
- Root `AGENT_RULES.md` gains a row every session reads, so its `when` must stay narrow enough that unrelated tasks skip the verify file.

## Changelog

<!-- Approvals only. -->

- 2026-11-02: spec approved by eugenelim
- 2026-11-02: plan approved by eugenelim
- 2026-11-02: spec amendment approved by eugenelim (AC-0004: agent instruction files and host skills are mapped, never hold an entry)
- 2026-11-02: plan amendment approved by eugenelim (T9 repairs the code-review findings)
