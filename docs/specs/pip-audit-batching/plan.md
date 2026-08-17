# Plan: pip-audit-batching

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit
> (`docs/CONVENTIONS.md` § Document lifecycle).

## Approach

The whole change is inside `tools/audit-requirements.py` plus new cases in
`tools/test-audit-requirements.py`, plus one committed re-proof script. The Makefile
recipe, the argv contract, the exit codes, and `--build-system` mode are untouched.

`audit_lines()` today does four things at once: partition, report, write one temp file,
run one `pip-audit`. The change separates *deciding what to run* from *running it*. A
new pure function groups files into merge-safe sets; a new runner executes one
`pip-audit` per group with repeated `-r` flags; per-file reporting stays exactly where
it is, and each group prints a header naming the real paths it covers immediately
before it runs.

Order of operations is driven by the fact that the riskiest part is not the batching —
it is **making the gate quieter without noticing**. So the seams that could hide a
vulnerability are built and tested first, against an injected fake runner, before any
real invocation changes. T1 makes `subprocess.run` injectable and fixes the exit-code
precedence. T2 adds the merge-safety rule and the coverage-conservation invariant as
pure functions. T3 wires the batched runner behind them, including headers, flushing,
`--strict`, and the diagnostic re-run. T4 pins suppression containment on both the argv
and the Makefile. T5 commits the equivalence re-proof script. T6 measures. T7 runs the
gates and closes the spec's status and criteria.

Two facts shape the design and are already proven (probes recorded in `spec.md`
§ Assumptions, which is their single canonical home):

1. `pip-audit` resolves all `-r` files into **one** environment, so merge safety is a
   property of the pins, not of the file count.
2. `pip-audit` never names the source file of a finding in any output format, which is
   why attribution comes from headers the script prints, not from temp-file names.

## Constraints

- **ADR-0017** — `pip-audit` is the SCA gate and audits the manifests the repo owns.
  This is the constraint the merge-safety rule exists to satisfy: ADR-0017 decides the
  gate audits *the manifests*, and a merged resolution that narrowed any pin would
  audit a version combination no adopter installs — a per-manifest fidelity reduction.
  Because the rule refuses to merge any file that could narrow the resolution, the
  audited `(name, version)` set is provably identical to the per-manifest set, so this
  is an implementation detail of ADR-0017's decision rather than a sub-decision of it,
  and needs no ADR. **Had the weaker rule shipped, an ADR would have been required** —
  a lasting fidelity reduction traded for ~14s is exactly the "you'd be annoyed to
  discover this was decided without discussion" bar in `docs/CONVENTIONS.md`.
- **ADR-0086** — the SAST/SCA leg is its own `gate-sast` job and is the critical path;
  its stated consequence is that additions to it translate 1:1 into PR latency. This
  change is the inverse of that consequence and needs no amendment: it changes neither
  where the leg runs nor the provenance mechanism, only how many processes one step
  spawns.
- **ADR-0083** — the npm SCA leg travels with the same gate. Untouched.
- **`AGENTS.md` § Keeping changes minimal** — no flag or option is added to the script,
  because there is only one caller; no dependency is added; the script stays
  stdlib-only.
- **`AGENTS.md` § New tool scripts** — pure-stdlib Python, which the existing script
  already is.

## Construction tests

Per-task tests live under each task below. Every TDD task's stub is materialised in
`tools/test-audit-requirements.py` at PLAN, tagged `# STUB: AC<n>`, per
`docs/CONVENTIONS.md` § *Stub → EXECUTE handoff*.

**Integration tests:** none beyond per-task tests. The script's only integration
surface is `make sast`, covered by T6's goal-based check and by
`tools/test_build_gate_chain.py`, which already gates the chain and is unaffected
because it parses `.github/workflows/build-check.yml`, not the Makefile.

**Manual verification:**
- A local timestamped `make sast`, before and after, attributing each `>=4s` gap to the
  line after it (AC3, AC16).
- A `gh run view <run-id> --log` attribution of the `gate-sast` job, before and after,
  same method with a `>=5s` threshold (AC16).
- The resolution-equivalence proof, run via the committed script from T5 (AC15).

**Recorded baselines** (2026-08-17, method: timestamp each output line, attribute any
gap `>=4s` locally / `>=5s` in CI to the line *after* the gap):

| Surface | Total | The 7-file loop | Other 3 pip-audits | bandit | semgrep |
| --- | ---: | ---: | ---: | ---: | ---: |
| local `make sast` | 172.0s | 61.4s | 38.0s | 10.9s | 41.4s |
| CI `gate-sast` (run 32063058843) | 160s (job) | 50.6s | 25.1s | 11.0s | 50.8s |

Measured targets, for the two invocations the merge-safety rule yields today:
`tools/requirements.txt` solo at 14.3s plus the batch of six at 10.8s, **25.1s total**,
against the 61.4s baseline segment. (A single unsafe batch of all seven measured 11.1s;
the 14s difference is the price of the merge-safety rule and is deliberate.)

## Design (LLD)

Shape is `service`. Stack is the Python 3 standard library only — `re`, `subprocess`,
`tempfile`, `pathlib` — matching what `tools/audit-requirements.py` already imports.
There is no `docs/architecture/reference.md` in this repo, so the stack is taken from
the module being edited. Line length 99, target `py311`, `ruff` with `E W F I UP B SIM
C4 PIE RET PTH PLW1514` (`pyproject.toml:1-39`).

### Design decisions

- **Merge only lower-bound-constrained files.** A file joins the shared batch when
  every audited requirement line carries only lower-bound specifiers (`>=`, `>`) or no
  specifier at all, and the file has no pip option line. Any `==`, `<`, `<=`, `~=`, or
  `!=`, and any option line, sends the file to its own invocation. The soundness
  argument is short: lower bounds can only push a resolution *up*, so a batch of
  lower-bound-only files resolves each package exactly as each file would alone;
  introduce any upper bound or exclusion and the merged resolution can land on a
  version no single file would, auditing a strict subset of the per-file
  `(name, version)` pairs. Traces to: AC1, AC12 · contracts: none.
  - Rejected: keying the rule on *shared package names* (an upper bound only matters
    if the package appears in two files). Unsound — an upper bound also constrains
    packages reached **transitively** from another file's tree, which no text rule can
    see. Security review refuted the accompanying "older versions carry more CVEs, so
    the error is louder" argument: narrowing can only *remove* pairs from the audited
    set, so it is never louder, and a CVE introduced in a newer release is exactly
    what an SCA gate exists to catch.
  - Rejected: batching identical `==` pins across files (provably safe in isolation).
    Not worth a second rule branch when the sound rule is one predicate and the saving
    is a single process; `!=` also narrows *sideways*, which the simple rule handles
    and a specifier-set comparison would have to special-case.
  - The specifier parse reads the requirement's specifier text after stripping inline
    comments and environment markers, so `tomlkit==0.15.1  # workspace-status
    repair-apply` is recognised as upper-bounded.
- **A batch's failure is final; the re-run is diagnostic.** The aggregate is
  `batch_rc OR fallback_rcs`, never `fallback_rcs` alone. `pip-audit` builds one
  environment per invocation, so a resolution conflict reds the batch while every
  member re-audits clean — taking the re-run's verdict would be a fail-open on the
  most likely fallback trigger. Traces to: AC9 · contracts: none.
- **Attribution by printed headers, not temp-file names.** No `pip-audit` output format
  carries the source file, so a descriptive temp-file name would never appear in a
  finding. Every invocation — including a single-file one, whose `-r` is a temp path —
  prints the real requirements paths it covers immediately before it runs. Traces to:
  AC5, AC6 · contracts: none.
- **The exit-code contract does not change.** `main()` keeps `failed |= …` and
  `return 1 if failed else 0`. An earlier draft proposed preserving a `pip-audit` exit
  code of `2`; that was wrong — 2.10.1 exits `1` and only `1`, so there was nothing to
  preserve, and the change would have altered a contract the spec says is stable.
  Because `1` means *either* a finding *or* a collection failure, no message on the
  failure path claims a vulnerability was found. Traces to: AC7, AC10 · contracts: none.
- **`-S`/`--strict` on the nine-file audits.** Without it a dependency whose collection
  fails is skipped and the process still exits 0 — a silent partial audit, the same
  class ADR-0084 already decided to gate for Bandit. Batching widens the blast radius
  from one file to the batch, so closing it belongs to this change; it is measured free
  (11.3s with, 11.1s without). `--build-system` mode is out of scope per the spec's
  *Ask first*. Traces to: AC11 · contracts: none.
- **Batch membership derives from the reporting predicate.** The same "has non-empty
  third-party content" test decides both whether to print "no third-party requirements
  to audit" and whether the file joins a batch, so the printed reporting and the
  audited set cannot disagree. Traces to: AC8 · contracts: none.
- **Groups are keyed by index, not by label.** A dict keyed on the argv path would
  silently collapse a duplicated path into one member. `make sast` cannot produce a
  duplicate today, but the fail-closed rule in the spec's *Always do* says not to rely
  on that. Traces to: AC8 · contracts: none.
- **Injected runner over monkeypatching.** The self-test imports the script by path via
  `importlib`; a default parameter taking `subprocess.run` is the smallest seam that
  makes exit aggregation and the re-run testable without a network call. Traces to:
  AC7, AC9, AC14 · contracts: none.
- **The re-proof lives at the point of use.** `plan.md` freezes with the spec, so the
  re-proof instruction goes in a committed script plus a docstring note on the grouping
  function — where a requirements edit will actually be made — and the spec cites that
  location. Traces to: AC15 · contracts: none.

### Interfaces & contracts

No published contract. The two internal surfaces both hold unchanged:

- argv: `audit-requirements.py <requirements.txt> ...` and
  `audit-requirements.py --build-system <pyproject.toml> ...`.
- exit codes: `0` clean, `1` at least one file failed, `2` gate configuration error
  (missing file, broken first-party discovery, invalid `build-system.requires`).

### Failure, edge cases & resilience

- A file that partitions to nothing third-party prints its message and joins no group
  (today's `flow-metrics` and `credential-setup`).
- A single-member group is a normal group: it still prints its header naming the real
  path, and it needs no diagnostic re-run because one member is already unambiguous.
- The diagnostic re-run fires only for groups of two or more, is exactly one level
  deep, and never recurses.
- Every temp file created for a group is removed in one `finally`, and each re-run
  cleans up its own; a partial failure leaks nothing.
- `pip-audit` exit `1` is ambiguous between a finding and a collection failure, so the
  gate fails either way and the message says only that the audit failed.
- An argv element that is not an existing file exits `2` before any audit runs.

### Quality attributes (NFRs)

- **Performance:** the nine-file set costs two `pip-audit` processes today. Bar: the
  segment completes under 30s, against a 61.4s baseline. Traces to: AC3, AC16.
- **Security posture:** the gate stays fail-closed — no suppression crosses an
  invocation boundary (AC12), any finding fails the gate (AC7), a batch failure is
  never cleared (AC9), a collection failure fails the gate (AC11), an unprovable merge
  splits (AC1), and no file can be silently dropped (AC8).
- **Operability:** a red gate names the offending file without the operator grepping
  (AC5), and headers precede their output in a piped log (AC6).

## Tasks

### T1: Exit-code precedence is provable, and a batch failure can never be cleared

**Depends on:** none

**Touches:** tools/audit-requirements.py, tools/test-audit-requirements.py

**Tests:** `stub: true`
- A fake runner failing one member of a two-member group makes the aggregate non-zero
  (AC7). `# STUB: AC7`
- A fake runner returning `0` for every group makes the aggregate `0` (AC7).
- A fake runner that fails the **batch** and passes **every member** of the diagnostic
  re-run still produces a non-zero aggregate (AC9). `# STUB: AC9`
- No message emitted on the failure path asserts that a vulnerability was found
  (AC10). `# STUB: AC10`
- An argv element that is not an existing file exits `2` (AC13). `# STUB: AC13`
- The argv the runner receives for a group of N files contains exactly N `-r` flags and
  no `--ignore-vuln` (AC12).

**Approach:**
- Give the group-running function an injectable runner parameter defaulting to
  `subprocess.run`, so the self-test can capture argv and force return codes.
- Aggregate as `batch_rc | fallback_rc`, never `fallback_rc` alone.
- Keep `audit_lines()` as the single-group path `--build-system` uses, and keep
  `main()`'s `return 1 if failed else 0`.

**Done when:** `python3 tools/test-audit-requirements.py` passes with the new cases and
no existing case is modified.

### T2: Files that could narrow each other are split, and no file is ever dropped

**Depends on:** none

**Touches:** tools/audit-requirements.py, tools/test-audit-requirements.py

**Tests:** `stub: true`
- Two files declaring only `>=` pins group together (AC1). `# STUB: AC1`
- A file carrying `tomlkit==0.15.1  # trailing comment` is audited alone, and the
  inline comment does not defeat the specifier parse (AC1, AC12). `# STUB: AC1`
- A file carrying `foo<2`, `foo~=1.4`, or `foo!=1.5` is audited alone (AC1).
- A file whose audited half contains a pip option line (`--extra-index-url`,
  `-c constraints.txt`, `--hash=…`) is audited alone (AC1).
- The union of all group memberships equals the set of non-empty-partition files, with
  no omission, no duplicate, and no empty group — asserted over the real nine files
  **and** over a synthetic hazard-heavy input (AC8). `# STUB: AC8`
- A duplicated argv path yields two members, not one (AC8).
- The nine files as they stand produce exactly two groups: `tools/requirements.txt`
  alone and the other six together (AC1).

**Approach:**
- Add a pure function over an indexed sequence of `(label, audited_lines)` returning a
  list of groups, applying the merge-safety predicate from § Design decisions against
  specifier text stripped of inline comments and markers, reusing `_NAME`.
- Carry the re-proof note in that function's docstring, per § Design decisions.

**Done when:** the new cases pass and the current nine files group into two.

### T3: The nine-file set is audited in two processes, with reporting and headers intact

**Depends on:** T1, T2

**Touches:** tools/audit-requirements.py, tools/test-audit-requirements.py

**Tests:** `stub: true`
- Every one of the nine files' labels, skipped pins, and "no third-party requirements
  to audit" lines still appear (AC4), asserted against captured stdout.
- Each group prints a header naming the real requirements paths it covers, including
  the single-file group (AC5). `# STUB: AC5`
- Run as a **subprocess** with `stdout=PIPE` and a stub `pip_audit` on `PATH`, the
  captured bytes show each header and its per-file reporting before that group's audit
  output (AC6). A call-order assertion is insufficient — it passes without
  `flush=True`. `# STUB: AC6`
- Every group's argv contains `-S` (AC11). `# STUB: AC11`
- A group of two or more whose runner fails triggers one re-run per member, exactly
  once, with no recursion (AC9).
- A group of one whose runner fails does **not** re-run.

**Approach:**
- In `main()`, replace the `failed |= audit(...)` loop with: partition and report every
  file, collect the non-empty ones, group them via T2, then run each group through the
  T1 runner with `-S`.
- Print each group's header and flush before its runner is invoked.
- On a multi-member group failing, re-run its members one at a time through the
  existing single-group path, printing that this is diagnostic.
- Keep `audit()` and `audit_lines()` so `--build-system` and the self-test's existing
  case 7 keep working.

**Done when:** `python3 tools/audit-requirements.py tools/requirements.txt $(find packs
-name requirements.txt | sort)` prints all nine files' reporting, spawns two
`pip-audit` processes, exits 0, and a piped run shows each header above its own output.

### T4: A leaked CVE suppression fails the self-test, on both surfaces

**Depends on:** T3

**Touches:** tools/test-audit-requirements.py

**Tests:** `stub: true`
- No argv the script builds for the nine-file set contains `--ignore-vuln`, for any
  value (AC12). This is the invariant; the four current CVE ids are deliberately **not**
  enumerated, because an enumeration silently under-covers when the suppression list
  changes. `# STUB: AC12`
- Parsing the `Makefile`, every `--ignore-vuln` occurrence sits within the
  `tools/requirements-sast.txt` invocation (AC12). This is the leak path an argv
  assertion cannot see: a maintainer adding a suppression to the batched recipe line to
  unblock a red gate. `# STUB: AC12`

**Approach:**
- Extend `tools/test-audit-requirements.py` with a suppression-containment section. It
  lives here rather than in `tools/test_build_gate_chain.py` so it runs inside
  `make sast`, which a `SAST_CONFIG` diff always triggers.

**Done when:** the self-test passes, and fails when `--ignore-vuln` is added either to
the batched argv or to the Makefile's batched line (both proven by temporarily adding
one).

### T5: The equivalence proof is a committed, runnable script

**Depends on:** T2

**Touches:** tools/prove-audit-batch-equivalence.py, tools/test-audit-requirements.py

**Tests:** goal-based check — the script runs and reports identical sets (AC15).

**Approach:**
- Commit a stdlib-only script that partitions the nine files, runs the grouped audits
  and the per-file audits with `--format json`, and asserts the resolved
  `(name, version)` sets are equal, printing both on divergence.
- It is deliberately not wired into `make sast` (spec Testing Strategy); the grouping
  function's docstring points at it.

**Done when:** the script exits 0 and prints identical sets for the nine files, and the
result is cited from `spec.md` § Assumptions rather than duplicated.

### T6: The saving is measured on both surfaces, the same way as the baseline

**Depends on:** T3

**Touches:** docs/specs/pip-audit-batching/plan.md

**Tests:** none — manual QA (spec Testing Strategy).

**Approach:**
- Run `make sast` locally with per-line timestamps; attribute gaps `>=4s`.
- Push the branch, let `build-check.yml` run, and attribute the `gate-sast` step with
  `gh run view <run-id> --log` and the `>=5s` rule.
- Record before/after in the baselines table above.

**Done when:** the after-column is filled for both surfaces and the pip-audit segment
is under 30s (AC3, AC16).

### T7: The gates are green and the spec is closed

**Depends on:** T3, T4, T5

**Touches:** docs/specs/pip-audit-batching/spec.md, docs/specs/pip-audit-batching/plan.md

**Tests:** none — goal-based check (spec Testing Strategy).

**Approach:**
- Run `SKIP_SAST=1 make build-check`, `make sast`, `python3 tools/lint-ruff.py`,
  `python3 -m pytest tools/test_build_gate_chain.py -q`.
- Move `spec.md` to `Status: Implementing` before any code lands, and to
  `Status: Shipped` at the end; move `plan.md` to `Status: Done`.
- Mark every acceptance criterion `[x]` or `(deferred: <slug>)`; run
  `scripts/lint-spec-status.py`.

**Done when:** all four commands exit 0 (AC17), both Status fields are terminal, and no
criterion is left silently unchecked.

## Rollout

- **Delivery:** big bang, single PR, fully reversible — reverting the commit restores
  the per-file loop. Nothing is migrated and nothing is published, so there is no
  irreversible step.
- **Infrastructure:** none. No new CI job, no new runner, no new secret.
- **External-system integration:** `pip-audit` continues to query the same advisory
  services; two processes make fewer connections than seven, and no endpoint or
  credential changes.
- **Deployment sequencing:** none. A single script edit whose only consumer is
  `make sast` in the same commit.

## Risks

- **The batched gate could be quieter than the per-file gate.** This is the risk that
  justifies full mode. Closed rather than accepted: the merge-safety rule refuses any
  merge that could narrow the resolution, so the audited `(name, version)` set is
  provably the per-manifest set, and T5's committed script re-proves it on demand. An
  earlier draft accepted a transitive-narrowing residual; security review showed the
  argument for accepting it was false, and the sound rule costs one extra invocation.
- **The diagnostic re-run is the least-exercised code** in the change and only runs
  when the gate is already red — precisely when it must work. Tested with an injected
  runner in T1 and T3 rather than left to a live vulnerable pin, and its exit-code
  precedence is the subject of its own AC.
- **`-S`/`--strict` could red the gate for a pre-existing reason.** Measured green
  today, but a future transient collection failure now fails the gate instead of
  passing quietly. That is the intended direction; noted so the first red is not
  mistaken for a regression in this change.
- **`tools/audit-requirements.py` is in `SAST_CONFIG`** (`Makefile:194`), so every push
  on this branch runs the full `gate-sast` — the intended safety property, and also why
  CI feedback here is slow (~2.5 min/push).
- **Network variance makes timings noisy.** The isolated seven-file measurement came in
  at 72.2s while the same segment inside `make sast` measured 61.4s. Both baselines are
  recorded and the after-measurements use the same method, but a single run is not a
  benchmark; the claim is a step change, not a precise number.

## Changelog

- 2026-08-17: initial plan.
- 2026-08-17: revised after spec-mode adversarial review and spec-stage security
  review. Five substantive changes. (1) The merge-safety rule was tightened from
  "upper bound on a package named in two files" to "any non-lower-bound specifier, or
  any pip option line, forces a solo invocation" — the weaker rule missed transitive
  narrowing, and the `## Accepted residual` that waived it rested on a false
  monotonicity argument, so the residual is now closed rather than accepted. Cost: one
  extra invocation, 25.1s instead of 11.1s. (2) A batch's non-zero exit is now
  explicitly final, with the diagnostic re-run unable to clear it — the previous draft
  left the precedence unstated, which is a fail-open. (3) Coverage conservation became
  an AC with its own test; splitting reporting from running removed the structural
  guarantee that a printed label meant an audited file. (4) The exit-2 handling was
  deleted as factually wrong — `pip-audit` 2.10.1 exits `1` and only `1` — which also
  restored the unchanged exit-code contract. (5) `-S`/`--strict` was adopted, and
  stdout ordering moved from a call-order assertion to a subprocess byte-order
  assertion, which is the only form that can fail when `flush=True` is missing.
