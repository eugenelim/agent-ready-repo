# Spec: ci-gate-credbroker

- **Status:** Shipped (reconciled 2026-08-25: AC12's post-merge measurement and AC13's required-check widening are complete; their frozen-body tokens were removed under owner authorization) <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0086
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`build-check.yml` runs the `packages/credbroker` suite in its own `gate-credbroker`
job rather than inside `gate-main`. The user is a contributor waiting on a PR: with
branch protection `strict: true` and no merge queue, merge throughput is bounded by
the slowest job in the workflow.

The change is accepted **on its mechanism**: `gate-main` is a serial step list, and
the moved step costs 27 s with zero variance across five runs, so removing it
shortens that job by 27 s by construction.

Timing is *not* an acceptance criterion, because no honest one exists here.
`gate-main` ranges 159–193 s — a spread larger than the effect — so a single-run
threshold would already pass today with the step still in place. `gate-sast` also
skips its scan (~31 s) on diffs touching no scanned path, so "the critical path
becomes gate-sast" is false for those runs. What a single run *can* settle is in
AC12; the throughput question is an open measurement with a stop condition and a
consequence (§ `ci-gate-credbroker-critical-path-measurement`).

The ceiling on further extraction is `gate-sast` (mean 160 s), which is why this
spec extracts the cheapest step that reaches that ceiling and stops.

## Boundaries

### Always do

- Keep `working-directory: packages/credbroker` on the moved step — it is what makes
  bare `python -m pytest` resolve the suite through that package's `testpaths`.
  `PINNED_JOB_STATEMENTS` pins this value alongside the step's statements, so a
  dropped or altered `working-directory` fails `job-statements-pinned[gate-credbroker]`.
  Before that pin its loss failed loudly only incidentally — the repo has no root
  pytest config, so a dropped value collects the monorepo and exits 2 at collection,
  a backing any future root pytest config would remove.
- Install the `[crypto]` extra **and prove it landed in the step that runs the
  suite**. A bogus extra warns and exits 0, and 21 `test_vault.py` tests plus 11
  `@requires_crypto` decorators would skip silently.
- Carry a `STEP_DISPOSITION` entry for every step of the new job; keep every *named*
  step's name unique across `build-check.yml`. The checkout stays unnamed, keyed
  `<unnamed step in gate-credbroker>`.
- Update `tools/test-build-check-workflow.py` and `tools/fixtures/build-check-good.yml`
  in the same commit as the workflow. The coupling is deliberate.
- Verify the job graph from a real run's per-job and per-step timings, not by
  deriving them from step counts.

### Ask first

- Any change to `main`'s branch-protection required-status-check set. Reading is
  routine; writing is not.
- Adding an **assertion or a mutation** to `tools/test-build-check-workflow.py`; a
  new one needs a named unpinned layer. AC6's `add-work-job-unwired` is the one
  approved exception (2026-08-17). This boundary governs that file only — not a line
  in a workflow `run:` body.
- Extracting any further step from `gate-main`.

### Never do

- Extract `pytest catalogue-test carve-out destinations (RFC-0082)`. Four revisions
  of `docs/specs/ci-gate-parallelization/spec.md` failed to enumerate its coupling
  graph by inspection.
- Add a dependency, a cache action, or any third-party action to `build-check.yml`.
- Relax a `PINNED_*` comparison, a `_body_is_straight_line` allowlist, or a `_key_re`
  matcher to make a check pass. A failing pin means the workflow changed; update the
  pin, never the comparison.
- Give `gate-credbroker` a job-level `if:`, `env:`, `needs:`, `permissions:`,
  `concurrency:`, or `container:`.
- Remove `Install credbroker (editable, with crypto extra)` from `gate-main` — four
  later steps in that job depend on it.
- Remove or narrow either of AC4's two controls, or key its grep to specific skip
  reasons. `PINNED_JOB_STATEMENTS` enforces this mechanically —
  `job-statements-pinned[gate-credbroker]` compares the whole body as an ordered
  list plus the step's `working-directory` — so the boundary states the intent and
  the pin carries it. Measured before the pin existed: deleting both controls,
  deleting `working-directory`, and `-k "not vault"` (which DESELECTS, emitting no
  `SKIPPED` line and exiting 0) all audited clean. Update the pin when the step
  legitimately changes; never relax it to make a check pass.
- Apply the branch-protection widening from inside this loop; with
  `PUT …/branches/main/protection` (clears every field it omits); or with the
  deprecated `contexts` field (see AC13).

## Testing Strategy

Every behavior here is a configuration or graph property; nothing has a compressible
invariant, so no behavior is TDD-mode.

- **Job graph shape and posture** — goal-based, via
  `python3 tools/test-build-check-workflow.py`. Its embedded `--self-test` re-derives
  the aggregator's guard body from the work-job list and fails closed when a job is
  added unwired.
- **That the derivation stays load-bearing** — goal-based, via a new mutation
  splicing an unwired fifth job into the fixture. Nothing currently mutates the
  job-set *input* to `guard-body-exact`; both its existing mutations alter the guard
  *body*.
- **That the new job's gate cannot be quietly narrowed** — goal-based, via
  `PINNED_JOB_STATEMENTS`, which compares the moved step's body as an ordered exact
  list *and* its `working-directory` in one assertion. They are one control: split
  apart, neither check can fail on the bypass the other covers.
- **Step-disposition completeness** — goal-based, via `tools/lint-ci-parity.py` and
  `tools/test-lint-ci-parity.py`.
- **That the suite verifies what it verified inside `gate-main`** — goal-based, via
  two standing in-step controls (AC4): an import probe naming the precondition, and a
  reason-agnostic zero-skip assertion. The pair mirrors `gate-export-boundary`'s tree probe plus `^SKIPPED` grep; a probe proves only what it names.
- **The measured outcome** — manual QA, reading per-job and per-step timings from
  `gh api …/actions/runs/<id>/jobs`, each computed as **`completed_at - started_at`**
  (named so a later reader does not substitute the web UI's duration). Not a gate: no
  assertion in this repo can measure wall-clock.

## Acceptance Criteria

- [x] **AC1 — `build-check.yml` declares a `gate-credbroker` job** with `name:` equal
      to its id, `runs-on: ubuntu-latest`, a `timeout-minutes:`, and no job-level
      `if:`, `env:`, `needs:`, `permissions:`, `concurrency:`, or `container:`. Steps:
      an unnamed `actions/checkout` at the pinned SHA; `actions/setup-python` at the
      pinned SHA with `python-version: "3.11"`; one editable install of
      `./packages/credbroker[crypto]` plus `pytest`; and the
      `pytest credbroker (RFC-0023 Phase 1)` step carrying
      `working-directory: packages/credbroker`.
- [x] **AC1a — the checkout is shallow.** Its `with:` mapping is exactly
      `{persist-credentials: false}`, mirroring the carve-out on the aggregator's own checkout (the step whose comment
      reads "AC12 exempts this job from fetch-depth"); `packages/credbroker` invokes git nowhere. Because
      `PINNED_CHECKOUT_WITH` is a set-equality pin this is decided here, and the
      reason travels in the workflow comment.
- [x] **AC2 — the step moved rather than being copied.** `gate-main` no longer
      contains it, and `build-check.yml` contains exactly one step by that name —
      asserted as a count equality and independently enforced by `lint-ci-parity`'s
      cross-job `duplicates` check.
- [x] **AC3 — the aggregator gates the new job.** `needs:` lists `gate-credbroker`;
      the guard step binds `GATE_CREDBROKER_RESULT: ${{ needs.gate-credbroker.result }}`;
      the guard body carries the line `_comparison_line("gate-credbroker")` derives,
      `::error::` annotation included.
- [x] **AC4 — the `[crypto]` extra is proven and the collection is proven not to have
      shrunk.** Under `set -euo pipefail`, the step runs
      `python -c "import cryptography, argon2"`, then
      `python -m pytest -rs 2>&1 | tee "$RUNNER_TEMP/credbroker-out.txt"`, then
      `! grep -Eq "^SKIPPED" "$RUNNER_TEMP/credbroker-out.txt"`. The probe omits
      `credbroker`: under `working-directory` it resolves from the source tree
      regardless of the install, so that term could not fail. The tee target is
      job-distinct so the step shares no literal with fixture mutations. The step
      carries a comment naming the two known non-crypto `^SKIPPED` triggers —
      `.agentbundle/bin/sso-broker.py` becoming untracked, and any new module-scope
      `importorskip` — so a cross-domain red is self-diagnosing rather than inviting
      the edit the Never-do forbids.
- [x] **AC4a — the moved step's body and `working-directory` are pinned by
      equality.** `PINNED_JOB_STATEMENTS` emits `job-statements-pinned[<job>]`,
      comparing the step's `run:` body as an ordered exact list and its
      `working-directory` value together. Verified against the real workflow by five
      bypasses, each of which audited **clean** before the pin and is caught after:
      deleting both AC4 controls; deleting either one alone; deleting
      `working-directory`; `-k "not vault"` (deselects rather than skips, so no
      `SKIPPED` line and exit 0); and pointing the grep at a file nothing writes.
      The label is parameterised so `_family` collapses it — a future work job adds
      a dict entry, not an assertion, and costs no further mutation.
- [x] **AC5 — `python3 tools/test-build-check-workflow.py` exits 0**, which requires
      its `--self-test` to pass: baseline clean, every mutation caught, every
      evaluated family mutated, every differential guard body agreeing with bash.
- [x] **AC6 — the job-set input to the guard-body derivation is mutated.** A mutation
      splices a bare fifth work job into the fixture without adding its `needs:`,
      `env:` binding or comparison, and `--self-test` reports `guard-body-exact`
      catching it. It targets an existing assertion, so it adds no family.
- [x] **AC7 — the fixture stays shape-representative.** It carries a fourth work job
      mirroring the real shape, declared **fourth** so the placement-sensitive
      mutations keep their first matches, with guard-body comparisons in
      `REQUIRED_WORK_JOBS` order (what `_differential_failures()` splices against).
- [x] **AC8 — `tools/lint-ci-parity.py` and `tools/test-lint-ci-parity.py` exit 0**,
      with a disposition per new step and no duplicate step name across jobs.
- [x] **AC9 — the workflow header's per-job local-reproduction block names
      `gate-credbroker`** and its command, `make test` (which runs
      `pytest packages/credbroker/ -q` among others), preserving the one-to-many
      addressability model inherited from `spec/ci-gate-parallelization` AC16.
- [x] **AC10 — `SKIP_SAST=1 make build-check` and `python3 tools/lint-ruff.py` exit
      0**, each read from its own exit code rather than through a pipe.
- [x] **AC11 — every check on a real PR run concludes `success`**, read from
      `gh pr checks <n>` rather than inferred from local gates.
- [x] **AC12 — the move is confirmed on a real post-merge run.**
      On the push-to-main run following the merge,
      `pytest credbroker (RFC-0023 Phase 1)` appears in `gate-credbroker`'s step list
      and not in `gate-main`'s, and `gate-credbroker` completes in ≤ 90 s. Both close
      on a single run.
- [x] **AC13 — `gate-credbroker` joins `main`'s required checks with its app pinning intact.**
      Applied by the owner after the post-merge run has reported the check,
      via `PATCH /repos/{owner}/{repo}/branches/main/protection/required_status_checks`
      with `{"strict": true, "checks": [<the current set> + gate-credbroker]}`, where
      **the current set comes from a `GET` taken immediately before the write, not
      from this document** — `checks[]` is REPLACE-semantics and this is applied after
      `spec.md` freezes, so a transcribed set would silently revert any interval
      change. The recorded five names, `app_id: 15368` and `strict: true` are the
      **expectation to diff that read against**; any mismatch stops the write and
      returns to the owner. Forbidden: `PUT …/protection`, the deprecated `contexts`
      array, and any read-back checking only names. Closed by a `GET` asserting, order
      independently, `strict: true`, the exact five-name context set, and
      `app_id: 15368` on every entry.

**Why `contexts` is forbidden.** GitHub documents it under a Closing down notice
("Use checks instead of contexts for more fine-grained control") and documents
`checks[].app_id` as "Omit this field to automatically select the GitHub App that has
recently provided this check, **or any app if it was not set by a GitHub App**. Pass
-1 to explicitly allow any app." So an omitted `app_id` is auto-select, not "any app"
— but where provenance is absent or non-App it resolves to any app. The explicit pin
buys two different things: **risk reduction** for `gate-credbroker`, whose provenance
at write time is one run old and ageing against an undefined recency window; and
**determinism** for the four existing checks, whose continuous Actions provenance
would almost certainly auto-select correctly — there the pin makes the result a
function of the request rather than of server-side history, keeping the read-back a
confirmation of intent.

**Accepted residual.** The read-back cannot see a change made between the pre-write
`GET` and the `PATCH`; its expectation equals the writer's intent. The diff shrinks
that window from months to seconds and cannot close it — this endpoint is *believed*
(not verified) to offer no `If-Match`/ETag conditional write. Accepted because a
single maintainer performs all four steps in one sitting.

## Assumptions

- Technical: the suite imports only stdlib, `pytest`, `credbroker`, and
  `cryptography`/`argon2` from the `[crypto]` extra (source: `grep -rhE '^\s*(import|from) '`
  over `packages/credbroker/`; `pyproject.toml [project.optional-dependencies]`)
- Technical: 505 tests collected, **all pass with zero `SKIPPED`** on a POSIX host
  with the extra present; 21 (`test_vault.py`) sit behind module-scope
  `importorskip`, and 11 `@requires_crypto` decorators (1 + 7 + 3) gate more (source:
  `python -m pytest -rs` → `505 passed in 31.94s`; `grep -rc '^@requires_crypto'`)
- Technical: **AC4's zero-skip assertion holds on `ubuntu-latest` by enumeration, not
  by a Linux run.** There are **ten** non-crypto skip sites. Eight are platform-gated
  and unreachable on a POSIX runner — `test_vault.py:213`,
  `test_master_sourcing.py:80`, `test_sso_lock_wiring.py:245` and `:271`,
  `test_sso_profile_lock.py:177`, `:186` and `:237` (all `os.name != "posix"`), plus
  `test_sso_recapture.py:143` inside the Windows `tasklist` branch. The other two are
  the ones worth knowing: `test_sso_broker_verbs.py:259` is **inverse-gated**, skipping
  when `playwright` *is* importable, which nothing in this job installs; and
  `test_sso_broker_verbs.py:64` is gated on `.agentbundle/bin/sso-broker.py` being
  present — a **repository-tree** property, not a platform one. That file is
  git-tracked, matches no ignore rule, and is a projected artifact under the self-host
  drift gate, so untracking it reddens `gate-main` *and* trips AC4's `^SKIPPED`
  assertion here. It is called out because it is the site a reader auditing "can AC4
  actually go red?" most needs to see (source: reading every site; `git ls-files
  --error-unmatch`; `git check-ignore -v`)
- Technical: an unrecognised extra is not an error —
  `pip install --dry-run -e './packages/credbroker[typo]'` warns, prints
  `Would install credbroker-0.6.0`, and **exits 0**. This is AC4's premise (source:
  measured, pip 26.2.1)
- Technical: `packages/credbroker` invokes git nowhere (source: `grep -rn '\bgit\b'`,
  no matches); bare `python -m pytest` resolves via `testpaths = ["tests"]` (source:
  `packages/credbroker/pyproject.toml`)
- Technical: `make test` runs `pytest packages/credbroker/ -q`, so the moved step's
  `LOCAL("test")` disposition stays true and is AC9's local command (source:
  `Makefile:332`)
- Technical: the `[crypto]` floors are SCA-covered by a **hand-mirror** of the extra
  piped into `pip-audit`; a floor bump needs two edits (source: `Makefile:266-273`,
  the claim resting on `:273`)
- Technical: per-job durations across the five runs since the three-job split, each
  `completed_at - started_at`, **with event class** — `build-check.yml` is not
  event-neutral (`:689`), so a mixed-class baseline is not a valid comparator:

  | run | event | gate-main | gate-sast | gate-export-boundary |
  | --- | --- | ---: | ---: | ---: |
  | 32068790012 | pull_request | 180 | 163 | 134 |
  | 32067545724 | push | 159 | 167 | 136 |
  | 32067163259 | pull_request | 193 | 31 *(scan skipped)* | 140 |
  | 32065059820 | pull_request | 164 | 149 | 136 |
  | 32063058843 | push | 184 | 160 | 123 |

  `gate-main` means: 179 (`pull_request`, n=3), 171.5 (`push`, n=2). The moved step
  cost exactly 27 s on all five. The register entry `ci-gate-credbroker-critical-path-measurement` carries these
  same rows and is the home that OUTLIVES this spec's freeze; re-derive from there
  (source: `gh api …/actions/runs/<id>` and `/jobs`, 2026-08-17)
- Process: `main` requires `make build-check`, `gate-main`, `gate-sast`,
  `gate-export-boundary`, `strict: true`, **each pinned to `app_id: 15368`** — the
  GitHub Actions app (source: `gh api …/required_status_checks` → `.checks[]`;
  `gh api /apps/github-actions`, 2026-08-17)
- Process: `main` has no merge queue, `enforce_admins: false`, no required reviews —
  the absent queue is half the throughput premise (source: `gh api …/protection`)
- Reference, **documented not measured**: the `contexts` Closing down notice and the
  `checks[].app_id` semantics quoted above. Neither is verifiable here — confirming
  them would require the destructive write this spec forbids (source:
  `https://docs.github.com/en/rest/branches/branch-protection?apiVersion=2022-11-28`,
  fetched 2026-08-17)
- Process: this change **narrows** `ci-gate-parallelization-required-workflow-pinned-ref`.
  Branch protection anchors at job granularity: today the suite is a step whose
  deletion, with its roster row, leaves both gates green; after AC13 it owns a job
  whose disappearance makes a required check never report. The merge→AC13 window is
  neutral, not weakened — `make build-check` is required, `needs: gate-credbroker`,
  and its comparison fails closed (source: ADR-0086 § Consequences; the aggregator's `needs:` list and its
  `GATE_CREDBROKER_RESULT` comparison in `build-check.yml`)
- Process: ADR-0086 already decides that a leg of `build-check.yml` may become its own
  job; this applies that decision, so no new ADR (source: `docs/adr/0086-…md`)
- Process: branch-protection writes are the owner's to apply; PRs #993 and #994
  predate this branch and go pending on the fifth check, named in the AC13 handoff
  rather than rebased from inside this loop (source: user confirmation 2026-08-17;
  `gh pr list`)
