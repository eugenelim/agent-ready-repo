# Plan: run grant

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, self-host, eval harness, pack-test loader rule); `tests/AGENTS.md`; `brief-runner.py` `read_blob`, `parse_status`, `parse_spec_map`, `_hidden_text_problem`, `read_lease`, `decide_next` and `_reason` as the seams this change extends; `author-delivery-brief/scripts/brief_shape.py` `BRIEF_STATUSES` as the status vocabulary; `test_brief_runner.py` and its fixture harness as the analogous integration tests; `test_brief_runner_units.py` as the unit analogue; `build-check.yml` `gate-sast` change-detection step as the base/head diff precedent.

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

All grant logic lands in `brief-runner.py`: a pure grant judge first (T1), then the base-history binding, the Ready-only rule and the new `next` answers (T2), then the read-only `guard` verb and its build-check step (T3). Guidance, evals, the trust-model entry and the RFC link follow the code (T4), and the release is last (T5). The riskiest part is the binding in T2, because it reads history; it is tested with real commits, including a grant edited alone and a brief edited after confirmation.

No supervisor file changes. Every edit under `work-loop/scripts/` changes the supervisor's pinned digests, so each is made while no `WORK_SUPERVISOR_INTEGRATION=1` run is live in this worktree.

## Constraints

- RFC-0113 D1–D8 bind every rule; D8's property list is the security review's checklist.
- ADR-0159: the runner stays read-only and reads only committed records; ADR-0157 and RFC-0099 §7: no approval is removed, merged or inferred.
- Slice 7 boundary: no edit to the supervisor files the spec's `Never do` names, and no counter inside supervisor attempts.
- Standard library only, Python 3.11 (`tomllib`, `datetime`).

## Construction tests

**Integration tests:** the D8 property matrix in T2 runs every forged-grant case through real `next` calls; the no-widening property (AC-0014) runs over every fixture brief in that suite.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| RFC-0113 link | T4 | RFC diff | AC-0027 |
| Maintainer procedure | T4 | guidance content tests | AC-0020 to AC-0022 |
| Security architecture entry | T4 | content test | AC-0024 |
| Release history | T5 | release check | AC-0025, AC-0026 |

## Design (LLD)

### Data & schema
<!-- Owned by: T1, T2. -->

- Grant file (AC-0003, AC-0006): presence is judged with `git ls-tree` at the base for the grant path, whatever the entry type; only a regular blob within 4096 bytes is then read, size checked before decoding, hidden-text checked before `tomllib.loads`. Any other entry is `malformed` (`not-regular` or `oversize`). Datetimes compare as aware UTC values; `confirmed_at` and `expires_at` must have `utcoffset() == 0` and `microsecond == 0`. Integers are checked with `type(v) is int`.
- Record (AC-0005): evidence is any `**Run grant:**` occurrence in the raw brief bytes, comments and body included; the one valid form is a single preamble line outside any HTML comment matching `^- \*\*Run grant:\*\* required \(confirmed (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)\)$`.
- Bound form (AC-0007, AC-0018): the brief bytes with only the status token of the one preamble `Status:` line that `parse_status` reads replaced by a fixed placeholder; one helper serves both the binding and the guard.
- Binding (AC-0007): one `git log -1 --first-parent --format=%H <base> -- <grant path>` call through the runner's hardened `git`, then blob reads of the brief at the anchor and at `<anchor>^1` (for the fresh-`confirmed_at` check) and of the standing orders at the anchor and at the base.

### Interfaces & contracts
<!-- Owned by: T2, T3. -->

- `next` schema 2: `grant`, `brief_status`, actions `grant-refused` and `grant-spent`, blocked reasons `not-granted` and `brief-not-ready`, `exemption` on a pre-Ready `resume-slice` (AC-0001, AC-0002, AC-0010, AC-0012, AC-0013).
- `guard --from --to`: runs only the Git version check, no main-worktree base checks, because CI runs it on a detached checkout; it reads blobs at the merge base and `--to` (AC-0018).
- build-check: one step in the `gate-main` job, which checks out full history. It runs `git archive <base> packs/core/.apm/skills/work-loop/scripts | tar -x` into `$RUNNER_TEMP`, then runs that copy with `python3 -I`, passing the SHAs as env values, never spliced into the script (AC-0019).

### Behavior & rules
<!-- Owned by: T2. -->

- Grant state order is AC-0006's; it is judged after the Spec map and lease reads, so `invalid-spec-map` and `invalid-policy` refusals keep their place.
- `decide_next` takes the grant view: `refused`/`spent` short-circuit to their action. For `valid`, the pilot, earlier-row and in-flight count are computed over all rows first, cap `min(lease cap, 1)`; then a non-granted row is skipped when choosing `resume-slice` and `start-slice`, so the granted answer's named slice is always one the no-grant answer could name (AC-0014). Blocked reasons add `not-granted` after the slice-state reasons and `waits-on-ungranted` for a granted row held by a non-granted pilot or earlier row.
- Non-runnable briefs mark every row without a worktree not ready and allow only the exemption resume, which also requires the AC-0009 resume predicate of the existing runner (`row.gates == []`), a spec on the branch head, and `_now()` before the end-time constant.
- Clock: one `_now()` call per run, `datetime.now(timezone.utc)`; unit tests patch it. Integration fixtures build grants relative to the real clock (valid: confirmed one hour ago, expiring in one day; expired: confirmed ten days ago, expired nine days ago). Every exemption test, positive and negative, calls the runner in-process over the fixture repository with `_now()` patched, so the suite stays green after the end time.

### Failure, edge cases & resilience
<!-- Owned by: T2. -->

- A Git or blob failure while judging the binding yields `stale` with `anchor-not-found`, never `valid` and never an `internal-error` that hides gates.
- A shallow clone has no anchor, so the grant is `stale`: fail closed.

## Tasks

### T1: Grant judge

- **Depends on:** none
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/brief-runner.py`, `packs/core/tests/skills/work-loop/test_brief_runner_grant_units.py`
- **Mode:** TDD
- **Tests:** a valid grant passes; one failing case per AC-0003 key rule, including a boolean `retry_budget`, `retry_budget` 3 above a budget of 2, `max_slices_in_flight` 2, a slice not in the Spec map, a duplicate slice, an empty `slices`, an unknown `held_actions` value, a non-UTC or fractional datetime; AC-0004's unknown keys (`spend_cap`, `human_only`, `max_retries`), a table, an oversize file, a hidden character, invalid TOML, expiry not after confirmation, expiry 14 days plus one second after it, and `confirmed_at` 6 minutes in the future; AC-0005's repeated line, wrong form and timestamp mismatch; each detail is from the fixed vocabulary (AC-0009); `human_only` equals the six-entry list and a test that removes an entry from the constant fails (AC-0011).
- **Done when:** the T1 tests pass.

### T2: Binding, Ready-only and grant answers

- **Depends on:** T1
- **Touches:** `brief-runner.py`, `packs/core/tests/skills/work-loop/test_brief_runner_grant.py`, `packs/core/tests/skills/work-loop/test_brief_runner.py` (schema 2 and `brief-not-ready` updates), `test_brief_runner_units.py`, `.github/workflows/catalogue-tooling-ci-gates.yml` lane list
- **Mode:** TDD
- **Tests:** Draft brief with an Approved, dispatchable row names no `start-slice` and lists `brief-not-ready` (AC-0001); Draft brief with an in-flight slice that has a spec gets `resume-slice` with the exemption, a `drafting` row with no spec and a row with a pending gate do not, and nothing resumes once `_now()` passes the end time (AC-0002); each AC-0006 state from real commits — no evidence, record only (`missing`), grant only (`malformed`), malformed grant, brief edited after confirmation, standing orders added or edited after it, grant edited alone, both removed (no-grant), Draft brief with grant (`brief-not-ready`), Shipped brief with grant (`brief-closed`, `complete`), a symlink and an oversize entry at the grant path with no record (`malformed`), a record only inside an HTML comment (`malformed`), a comment-only grant edit together with a brief edit (`not-reconfirmed`), trailing text added to the `Status:` line (`brief-changed`) (AC-0006, AC-0007, AC-0009, AC-0015); expired and done for both `done_when` values (AC-0008); answer shapes and `schema_version` 2 (AC-0010); `grant-refused` and `grant-spent` carry pending gates and merge-ready rows and name no slice beside a resumable row (AC-0012); a non-granted row is `not-granted`, a non-granted `refused` row keeps `refused`, a granted row behind a non-granted pilot, behind a non-granted unstopped earlier row and under a cap filled by a non-granted in-flight row reads `waits-on-ungranted`, and the cap is 1 (AC-0013); the subset property over every fixture (AC-0014); store and Git state unchanged (AC-0016); `classify` with a grant budget of 0 abandons on the first failure, and refuses work under a refused grant (AC-0017).
- **Done when:** the T2 tests pass in the integration lane and the existing brief-runner suites stay green.

### T3: Guard

- **Depends on:** T2
- **Touches:** `brief-runner.py`, `test_brief_runner_grant.py`, `test_brief_runner_units.py` (the verb-set test), `references/brief-runner.md` (the refusal-code list and the guard verb row), `test_brief_runner_guidance.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py` (`STEP_DISPOSITION` entry), `tools/test-build-check-workflow.py` (posture test)
- **Mode:** TDD
- **Tests:** grant-file-only, standing-orders-only and brief-made-Ready-only changes pass; each mixed with a code file fails `grant-change-mixed`; a Ready→Executing status-only edit is not a grant change; a prose edit to a no-grant Ready brief is not one; a Draft brief edit is not one; a Spec map edit on a Ready brief is one and passes beside only the added row's Draft `spec.md` and Drafting `plan.md`, listed under `companions`, but fails beside a `docs/knowledge/` file, a `delivery/` record in the new spec directory, an Approved `spec.md`, or an ADR; a new brief committed Ready is one; a deleted grant file and a renamed one are; the two-change route (Ready to Draft plus a row, mixed with code) fails on its first change; a `Status:` line with added trailing text on a granted brief is `brief-granted`; a granted brief closed to `Shipped` with its `Cut-closed:` record beside the last slice's files is not a grant change; an unsafe path prints `withheld`; output shape, refusal codes and no writes (AC-0018, AC-0028); a posture test in `tools/test-build-check-workflow.py` asserts the step runs only on pull requests, archives the base revision's scripts, runs them with `-I`, passes SHAs through env, and picks the head copy only by reading the base tree (AC-0019).
- **Done when:** the T3 tests pass.

### T4: Guidance, evals, trust model, RFC link

- **Depends on:** T2, T3
- **Touches:** work-loop `references/brief-runner.md`, work-loop `SKILL.md`, `packs/core/.apm/skills/author-delivery-brief/SKILL.md`, both skills' `evals/evals.json`, `docs/architecture/security.md`, `docs/rfc/0113-run-grant-at-brief-ready.md`, `packs/core/tests/skills/work-loop/test_brief_runner_guidance.py`, `packs/core/tests/skills/author-delivery-brief/test_grant_path_guidance.py`
- **Mode:** goal-based
- **Tests:** content tests for every duty in AC-0020, AC-0021, AC-0022 and AC-0024 over the owning files; eval schema checks for AC-0023; RFC link present (AC-0027).
- **Done when:** the T4 tests and both eval harness checks pass.

### T5: Release

- **Depends on:** T4
- **Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/<uuid>.md`, self-host projections
- **Mode:** goal-based
- **Tests:** release version check and catalogue lint and verify (AC-0025, AC-0026).
- **Done when:** both checks exit 0 and the tree is clean after self-host.

### T6: Review round 1 repairs

- **Depends on:** T5
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/brief-runner.py`, `packs/core/.apm/skills/work-loop/references/brief-runner.md`, `packs/core/.apm/skills/author-delivery-brief/SKILL.md`, `.github/workflows/build-check.yml`, `tools/test-build-check-workflow.py`, `tools/lint-ci-parity.py`, `packs/core/tests/skills/work-loop/test_brief_runner_grant.py`, `test_brief_runner_guard.py`, `test_brief_runner_units.py`, `test_brief_runner_guidance.py`, `packs/core/tests/skills/author-delivery-brief/test_grant_path_guidance.py`
- **Mode:** TDD
- **Tests:** a real `git clone --depth 1` fixture where a grant edited alone and a brief edited after confirmation both read `stale` with `anchor-not-found`, and an unreadable anchor parent or standing-orders entry never reads as absent (AC-0007); the grant template shown in author-delivery-brief passes `judge_grant` once filled with sample values, with bare TOML offset date-times (AC-0022, AC-0003); `guard_surface` lists an installed copy's work-loop scripts, `references/brief-runner.md` and author-delivery-brief `SKILL.md` under any skills root, with no repository-specific path in shipped code (AC-0028); a filter name the hardened launcher refuses makes `guard` answer `git-unavailable`, never a fifth code (AC-0028); the build-check guard step runs before any step that executes the change's code, and the wiring guidance says so (AC-0019, AC-0020); the reference's `grant` and grant-action rows state the AC-0006 null condition, the AC-0010 key sets and every reason (AC-0010, AC-0020); a guard fixture whose `--from` moved past the fork point counts only the change's own paths and names the fork as `merge_base` (AC-0018); the subset property compares each valid-grant brief's answer with a real `next` on the same brief with its grant evidence removed (AC-0014); read-only grant-state cases share module-scoped fixture worlds; canned-row unit cases pin `not-granted`, each `waits-on-ungranted` trigger, `brief-not-ready`, the exemption filter and the cap of 1 (AC-0013, AC-0001); the tautological assertion is gone, a binding failure writes a bounded path-free reason to stderr, the guard uses `grant_path`, and `main` reads the brief and lease once.
- **Done when:** the T6 tests pass with the lint pair, the grant, guard, unit and guidance suites and `tools/test-build-check-workflow.py` green.

### T7: Author-delivery-brief projections

- **Depends on:** T6
- **Touches:** `.claude/skills/author-delivery-brief/SKILL.md`, `.claude/skills/author-delivery-brief/evals/evals.json`, `.agents/skills/author-delivery-brief/SKILL.md`, `.agents/skills/author-delivery-brief/evals/evals.json`
- **Mode:** goal-based
- **Tests:** after `agentbundle catalogue self-host --root . --write`, `agentbundle catalogue verify --root .` and `agentbundle catalogue lint --root . --deep` exit 0 and the only changed files are the four author-delivery-brief copies (AC-0026).
- **Done when:** both catalogue checks exit 0 and the work-loop copies are unchanged.

## Rollout

- **Delivery:** the grant is optional; a brief with no grant evidence behaves as today apart from the Ready-only rule. Reversal is reinstalling the prior Core release.
- **Deployment sequencing:** merge when ready and approved. When verified-infrastructure-parallelism lands first, rebase, regenerate any open supervisor run's pins, and rerun its integration suites.

## Risks

- Pin churn: editing `brief-runner.py` changes the supervisor's pinned digests, so an open run started on the prior Core release refuses `supervisor-changed` after this lands.
- Draft briefs stop starting slices (AC-0001); the exemption covers only slices already in flight.

## Changelog

- 2026-11-08: spec approved by eugenelim (scope)
- 2026-11-08: plan approved by eugenelim (build strategy)
