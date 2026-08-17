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
`tools/test-audit-requirements.py`. The Makefile recipe, the argv contract, and
`--build-system` mode are untouched.

`audit_lines()` today does four things at once: partition, report, write one temp file,
run one `pip-audit`. The change splits reporting from running. A new pure function
groups the nine files into batches; a new runner executes one `pip-audit` per batch
with repeated `-r` flags; the per-file reporting stays exactly where it is and simply
happens for all nine files before any audit runs.

Order of operations matters because the riskiest part is not the batching — it is
**making the gate quieter without noticing**. So the seam that could hide a
vulnerability is built and tested first, against an injected fake runner, before any
real `pip-audit` invocation changes. T1 makes `subprocess.run` injectable so exit-code
aggregation and fallback are testable at all. T2 adds the hazard rule as a pure
function. T3 wires the batched runner behind them. T4 adds the suppression-containment
and attribution cases the spec requires. T5 is the measurement pass.

Two facts shape the design and are already proven (probes recorded in `spec.md`
Assumptions): `pip-audit` never names the source file of a finding in any output
format, which is why attribution is restored by re-running per file rather than by
labelling temp files; and the merged resolution currently equals the union of the
per-file resolutions, which is what makes batching safe today.

**Equivalence re-proof command** (for when the requirements files change — not wired
into `make sast`, per the spec's Testing Strategy):

```bash
# 1. write each file's partitioned lines to its own temp file, then:
python3 -m pip_audit -r f1.txt -r f2.txt ... --format json -o merged.json
for f in f*.txt; do python3 -m pip_audit -r "$f" --format json -o "per-$f.json"; done
# 2. assert the merged (name, version) set equals the union of the per-file sets
```

## Constraints

- **ADR-0017** — `pip-audit` is the SCA gate and audits the manifests the repo owns:
  `tools/requirements.txt`, the two packages, and the shipped per-skill
  `requirements.txt` files. The set of audited files does not shrink here, only the
  number of processes that audit them. The scanners stay CI-only dev dependencies.
- **ADR-0086** — the SAST/SCA leg is its own `gate-sast` job and is the critical path;
  its stated consequence is that additions to it translate 1:1 into PR latency. This
  change is the inverse of that consequence and needs no ADR amendment: it changes
  neither where the leg runs nor the provenance mechanism, only how many processes one
  step spawns.
- **ADR-0083** — the npm SCA leg travels with the same gate. Untouched.
- **`AGENTS.md` § Keeping changes minimal** — no flag or option is added, because there
  is only one caller; no dependency is added; the script stays stdlib-only.
- **`AGENTS.md` § New tool scripts** — pure-stdlib Python, which the existing script
  already is.

## Construction tests

Per-task tests live under each task below. Cross-cutting:

**Integration tests:** none beyond per-task tests. The script's only integration
surface is `make sast`, covered by the goal-based check in T5 and by
`tools/test_build_gate_chain.py`, which already gates the chain.

**Manual verification:**
- A local timestamped `make sast`, before and after, attributing each `>=4s` gap to the
  line after it. Baseline recorded below.
- A `gh run view <run-id> --log` attribution of the `gate-sast` job, before and after,
  same method. Baseline recorded below.
- A piped run's line ordering, to confirm each label precedes its own audit output
  (spec AC3).
- The resolution-equivalence proof above, run once against the nine files as they stand.

**Recorded baselines** (2026-08-17, method: timestamp each output line, attribute any
gap `>=4s` locally / `>=5s` in CI to the line *after* the gap):

| Surface | Total | The 7-file loop | Other 3 pip-audits | bandit | semgrep |
| --- | ---: | ---: | ---: | ---: | ---: |
| local `make sast` | 172.0s | 61.4s | 38.0s | 10.9s | 41.4s |
| CI `gate-sast` (run 32063058843) | 160s (job) | 50.6s | 25.1s | 11.0s | 50.8s |

Isolated: today's nine-file call takes 72.2s; the same seven files batched into one
invocation take 11.1s.

## Design (LLD)

Shape is `service`; the sub-sections below are the ones that shape selects. Stack is
Python 3 standard library only — `re`, `subprocess`, `tempfile`, `pathlib` — matching
what `tools/audit-requirements.py` already imports. There is no
`docs/architecture/reference.md` in this repo, so the stack is taken from the module
being edited.

### Design decisions

- **Batch, then fall back to per-file on failure.** The green path costs one process;
  the red path costs one plus the old seven and reproduces today's per-file output
  exactly. Rejected: emitting a package→file map, because it covers only direct pins
  and a transitive finding (the `urllib3`-via-`httpx` shape observed in probe #1) maps
  to nothing; and batching with no attribution at all, which ships a faster gate whose
  failures nobody can locate. Traces to: AC5 · contracts: none.
- **Attribution by re-running, not by naming temp files.** No `pip-audit` output format
  carries the source file, so a descriptive temp-file name would never appear in a
  finding. Traces to: AC5 · contracts: none.
- **A textual merge-hazard rule, not a resolver.** Detecting narrowing properly needs
  per-file resolution, which is the cost being removed. The text rule is sound for
  directly-declared pins; the transitive residual is documented in `spec.md`
  § Accepted residual rather than left implicit. Rejected: asserting equivalence inside
  `make sast`, which needs both a batched and a serial run and cancels the saving.
  Traces to: AC7 · contracts: none.
- **`--build-system` mode keeps calling the single-group path unchanged.** It already
  aggregates both pyprojects into one audit. Traces to: AC1 · contracts: none.
- **Injected runner over monkeypatching in the test.** The self-test imports the script
  by path via `importlib`; a default parameter taking `subprocess.run` is the smallest
  seam that makes exit aggregation and fallback testable without a network call.
  Traces to: AC4, AC5, AC8 · contracts: none.

### Interfaces & contracts

No published contract. The two internal surfaces both hold:

- argv: `audit-requirements.py <requirements.txt> ...` and
  `audit-requirements.py --build-system <pyproject.toml> ...`.
- exit codes: `0` clean, `1` at least one finding, `2` gate configuration error
  (missing file, broken first-party discovery, invalid `build-system.requires`).

### Failure, edge cases & resilience

- A file that partitions to nothing third-party prints its message and joins no batch
  (today's `flow-metrics` and `credential-setup`).
- A single-member batch is just a batch of one; no special case, and no fallback re-run
  is needed for it because the one `-r` file already identifies the source. The
  fallback fires only for batches with two or more members.
- A hazard splits files into separate batches; a file is never dropped.
- `pip-audit` exiting `2` (its own internal error, distinct from a finding) must not be
  laundered into `1`; the aggregate stays non-zero either way, and the fallback re-run
  surfaces the real message.
- Temp files are removed in a `finally`, as today.

### Quality attributes (NFRs)

- **Performance:** the nine-file set costs one `pip-audit` process. Bar: the pip-audit
  segment of `make sast` drops from 61.4s to roughly 11s locally. Traces to: AC1, AC11.
- **Security posture:** the gate stays fail-closed — no suppression crosses an
  invocation boundary (AC6), any finding fails the gate (AC4), and an unprovable merge
  splits rather than merges (AC7).
- **Operability:** a red gate names the offending file without the operator grepping
  (AC5), and labels precede their output in a piped log (AC3).

## Tasks

### T1: Exit-code aggregation and the runner seam are provable without a network call

**Depends on:** none

**Touches:** tools/audit-requirements.py, tools/test-audit-requirements.py

**Tests:**
- A fake runner returning `1` for one member of a two-member batch makes the
  aggregate return non-zero (spec AC4).
- A fake runner returning `0` for every batch makes the aggregate return `0`.
- A fake runner returning `2` does not get laundered into `1`; the aggregate is
  non-zero (spec AC4, `Failure, edge cases & resilience`).
- The argv the runner receives for a batch of N files contains exactly N `-r` flags and
  no `--ignore-vuln` (spec AC6).

**Approach:**
- Give the audit-running function an injectable runner parameter defaulting to
  `subprocess.run`, so the self-test can capture argv and force return codes.
- Keep `audit_lines()` as the single-group path that `--build-system` uses.

**Done when:** `python3 tools/test-audit-requirements.py` passes with the four new
cases, and no existing case is modified.

### T2: Files that could narrow each other's resolution are split, provably

**Depends on:** none

**Touches:** tools/audit-requirements.py, tools/test-audit-requirements.py

**Tests:**
- Two files declaring `httpx>=0.27` identically batch together (spec AC7).
- Two files declaring `foo<2` and `foo>=1` land in different batches (spec AC7).
- A file carrying `tomlkit==0.15.1` where no other file mentions `tomlkit` still
  batches with the others — an upper bound alone is not a hazard (spec AC7).
- A package upper-bounded in one file and present in another batches separately
  (spec AC7).
- The nine files as they stand produce exactly one batch (spec AC1, AC7).

**Approach:**
- Add a pure function over `{label: audited_lines}` returning a list of batches,
  applying the two-clause rule from spec AC7 against PEP 503-canonical names, reusing
  `_canonical()` and `_NAME`.

**Done when:** the new cases pass and the current nine files group into one batch.

### T3: The nine-file set is audited by one `pip-audit` process, with per-file reporting intact

**Depends on:** T1, T2

**Touches:** tools/audit-requirements.py, tools/test-audit-requirements.py

**Tests:**
- Every one of the nine files' labels, skipped pins, and "no third-party requirements
  to audit" lines still appear (spec AC2), asserted against captured stdout.
- Each label and its skipped-pin lines are emitted before the runner for its batch is
  invoked (spec AC3).
- A batch of two or more whose runner returns non-zero triggers a per-file re-run,
  once per member (spec AC5), asserted by counting runner calls.
- A batch of one whose runner returns non-zero does **not** re-run (no redundant
  audit).

**Approach:**
- In `main()`, replace the `failed |= audit(...)` loop with: partition and report every
  file, collect the non-empty ones, group them via T2, then run each batch through the
  T1 runner.
- Print each label with an explicit flush before the batch runs, fixing the piped
  ordering.
- On a multi-member batch failing, re-run its members one at a time through the
  existing single-group path to restore attribution, and print a line saying that is
  what is happening.
- Keep `audit()` and `audit_lines()` so `--build-system` and the self-test's existing
  case 7 keep working.

**Done when:** `python3 tools/audit-requirements.py tools/requirements.txt $(find packs
-name requirements.txt | sort)` prints all nine files' reporting, spawns one
`pip-audit`, exits 0, and a piped run shows each label above its own output.

### T4: A leaked CVE suppression fails the self-test

**Depends on:** T3

**Touches:** tools/test-audit-requirements.py

**Tests:**
- No batch built from the nine files includes `tools/requirements-sast.txt`
  (spec AC6).
- The argv for every batch is free of `--ignore-vuln`, asserted over the four CVE ids
  the Makefile suppresses — `CVE-2026-52870`, `CVE-2026-52869`, `CVE-2026-59950`,
  `PYSEC-2026-2132` — so the case fails if any is ever added to the batched path
  (spec AC6).
- The module exposes no helper that would let a caller pass `--ignore-vuln` into the
  batched runner.

**Approach:**
- Extend `tools/test-audit-requirements.py` with a suppression-containment section
  naming the four ids explicitly, so the test reads as the invariant it protects.

**Done when:** the self-test passes, and fails if `--ignore-vuln` is added to the
batched argv (proven by temporarily adding one).

### T5: The saving is measured on both surfaces, the same way as the baseline

**Depends on:** T3

**Touches:** docs/specs/pip-audit-batching/plan.md

**Tests:** none — measurement task, verification mode is manual QA (spec Testing
Strategy).

**Approach:**
- Run `make sast` locally with per-line timestamps; attribute gaps `>=4s`.
- Run the resolution-equivalence proof once against the nine files.
- Push the branch, let `build-check.yml` run, and attribute the `gate-sast` step with
  `gh run view <run-id> --log` and the `>=5s` rule.
- Record before/after in the table above.

**Done when:** the after-column of the baseline table is filled for both surfaces, the
pip-audit segment shows one invocation, and the equivalence proof is recorded as
identical.

### T6: The gates the spec names are green

**Depends on:** T3, T4

**Touches:** none (verification only)

**Tests:** none — goal-based check (spec Testing Strategy).

**Approach:** run `SKIP_SAST=1 make build-check`, `make sast`,
`python3 tools/lint-ruff.py`, `python3 -m pytest tools/test_build_gate_chain.py -q`.

**Done when:** all four exit 0 (spec AC12).

## Rollout

- **Delivery:** big bang, single PR, fully reversible — reverting the commit restores
  the per-file loop. Nothing is migrated and nothing is published, so there is no
  irreversible step.
- **Infrastructure:** none. No new CI job, no new runner, no new secret.
- **External-system integration:** `pip-audit` continues to query the same advisory
  services over the network; one process makes fewer connections than seven, and no
  endpoint or credential changes.
- **Deployment sequencing:** none. The change is a single script edit whose only
  consumer is `make sast` in the same commit.

## Risks

- **The batched gate could be quieter than the per-file gate** if a merged resolution
  narrows to a version whose CVEs differ. Mitigated by the T2 hazard rule, bounded by
  the recorded equivalence proof, and the residual is written down in `spec.md`
  § Accepted residual rather than left implicit. This is the risk that justifies full
  mode and the `security-reviewer` pass.
- **A `pip-audit` exit code of `2` could be mistaken for a finding**, hiding a broken
  audit behind a plausible-looking failure. Covered by a T1 test.
- **The fallback path is the least-exercised code** in the change, and it only runs
  when the gate is already red — precisely when it must work. It is tested with an
  injected runner in T3 rather than left to a live vulnerable pin.
- **`tools/audit-requirements.py` is in `SAST_CONFIG`** (`Makefile:194`), so every push
  on this branch runs the full `gate-sast`. That is the intended safety property, and
  it also means CI feedback on this change is slow — expect ~2.5 minutes per push.
- **Network variance makes timings noisy.** The isolated nine-file measurement came in
  at 72.2s while the same segment inside `make sast` measured 61.4s. Both baselines are
  recorded and the after-measurements use the same method, but a single run is not a
  benchmark; the claim is a step change, not a precise number.

## Changelog

- 2026-08-17: initial plan.
