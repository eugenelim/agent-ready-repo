# Verification ledger

Observed, not intended: this records what actually ran, on this machine, on
2026-09-17.

## T2: Decide the size ceiling on the complete file

### Repair

`packages/jsonl-otlp-exporter/jsonl_otlp_exporter/config.py`, inside
`read_config_file`'s existing `try` block:

1. `os.read(fd, MAX_CONFIG_BYTES)` -> `os.read(fd, MAX_CONFIG_BYTES + 1)`.
2. A new check inserted between that read and the existing short-read
   comparison: re-sample `os.fstat(fd)` and refuse with a new message
   ("config file grew from X to Y bytes during the read: ...") when the
   re-sampled size differs from the size sampled before the read. No
   existing `ConfigRefused` message was reworded.

### New cases, and their observed red

Each case below was run against the build with the repair entirely absent
(the un-repaired `read_config_file`, still reading `MAX_CONFIG_BYTES` bytes
with no re-sample), then again after the repair landed.

| Case | File | Red (unrepaired) | Green (repaired) |
| --- | --- | --- | --- |
| `TestExactCeilingGrowthRace::test_growth_between_the_sample_and_the_read_is_refused` — growth the read sees, armed at exactly `MAX_CONFIG_BYTES`, appended through a second descriptor between the `fstat` sample and the `read` | `test_config.py` | `Failed: DID NOT RAISE ConfigRefused` | passed |
| `TestExactCeilingGrowthRace::test_growth_a_short_read_hides_is_still_caught_by_the_resample` — a substituted read returns a ceiling-length prefix of a file already grown past it | `test_config.py` | `Failed: DID NOT RAISE ConfigRefused` | passed |
| `TestExactCeilingGrowthRace::test_growth_the_resample_cannot_see_because_fstat_is_stale` — a substituted post-read `fstat` reports the pre-growth size even though a real, substituted `os.read` already grew the file for real; only the extra byte in the buffer catches this one | `test_config.py` | `Failed: DID NOT RAISE ConfigRefused` (accepted and parsed) | passed |
| `TestReviewRegressions::test_a_growing_configuration_file_is_refused_with_nothing_sent` — CLI-level: growing `--config` file, asserts exit 1 and the transport seam (`connection_factory`) is never constructed | `test_cli.py` | The `exploding` connection factory fired (`AssertionError: a connection was constructed for a refused configuration`) — the command actually attempted to send | passed, exit 1, no connection constructed |
| `TestHostileContentIsEscaped::test_every_refusal_escapes_a_hostile_path[grown]` — the new message's own arm in the escaping control, walking `config.py`'s (now eleven) raise sites | `test_two_scope_config.py` | `Failed: DID NOT RAISE ConfigRefused` | passed |

The pre-existing, non-growing neighbour case,
`TestConfigFileAcquisition::test_a_file_at_exactly_the_ceiling_is_accepted`
(`test_config.py`), was green both before and after: it already covers "a
file at exactly the ceiling that does not grow must still parse," so no new
case was written to duplicate it, per the plan's instruction to reuse it.

### The fifth arm, and why it exists

The first mutation pass below (before this arm existed) showed that
reverting the `MAX_CONFIG_BYTES + 1` buffer alone, while keeping the
re-sample, killed none of the first four new cases: every one of them grows
the file for real on disk, and the re-sample's `os.fstat` call genuinely
observes that growth regardless of how many bytes `os.read` was asked for.
That left the buffer — the registered remedy — as a production change with
no case that fails without it.

The coordinator's follow-up named the gap this leaves unverified and
supplied the technique used to close it: substitute `os.fstat` itself, not
just `os.read`. `test_growth_the_resample_cannot_see_because_fstat_is_stale`
arms a file at exactly `MAX_CONFIG_BYTES`, substitutes `os.read` to append a
real byte and then perform a genuine read, and substitutes `os.fstat` so its
*first* call (the sample before the read) returns the genuine result while
its *second* call (the re-sample after the read) returns a stale result
still reporting the original ceiling size — the cached-metadata divergence a
real `fstat` and a real `read` can have against each other on a network or
FUSE mount. With the re-sample seeing nothing, only the extra byte landing
in `raw` — caught by the pre-existing short-read comparison, not by the
"grew" message — refuses the file.

### Mutation proof: each repair statement killed the cases it alone covers

Both repair statements were reverted individually (one at a time, the other
kept), and all five new cases plus the neighbouring accepted case were rerun
against each mutant. This table is the corrected one, after the fifth arm
(`test_growth_the_resample_cannot_see_because_fstat_is_stale`) was added; see
below for the first pass, which this superseded.

**Mutation 1 — revert the buffer only** (`os.read(fd, MAX_CONFIG_BYTES + 1)`
reverted to `os.read(fd, MAX_CONFIG_BYTES)`; the re-sample check kept).

| Case | Result |
| --- | --- |
| `test_growth_between_the_sample_and_the_read_is_refused` | passed (not killed) |
| `test_growth_a_short_read_hides_is_still_caught_by_the_resample` | passed (not killed) |
| `test_growth_the_resample_cannot_see_because_fstat_is_stale` | **`Failed: DID NOT RAISE ConfigRefused`** — killed |
| CLI arm (`test_a_growing_configuration_file_is_refused_with_nothing_sent`) | passed (not killed) |
| `[grown]` escaping-control arm | passed (not killed) |
| non-growing accepted case | passed (correct — no false positive) |

The fifth arm is the one case that dies under this mutation, exactly as
predicted: its substituted `os.fstat` makes the re-sample's second call
report the pre-growth size, so with the buffer reverted to
`MAX_CONFIG_BYTES` the real, substituted `os.read` call returns only
`MAX_CONFIG_BYTES` bytes (capped at the smaller request) — matching both the
stale re-sample and the original sample — and the file is silently accepted
and parsed. That is the fail-open the buffer exists to close, and now it has
its own killing case.

The other four cases still don't die under this mutation, for the reason
recorded in the first pass below: each of them grows the file for real on
disk, so the re-sample's genuine `fstat` call catches the growth on its own,
independent of the buffer.

**Mutation 2 — revert the re-sample only** (the new `os.fstat`-and-compare
block removed; the `MAX_CONFIG_BYTES + 1` read kept).

| Case | Result |
| --- | --- |
| `test_growth_between_the_sample_and_the_read_is_refused` | killed — wrong message ("read returned...", not "grew") |
| `test_growth_a_short_read_hides_is_still_caught_by_the_resample` | killed — `Failed: DID NOT RAISE ConfigRefused` |
| `test_growth_the_resample_cannot_see_because_fstat_is_stale` | passed (not killed) |
| CLI arm | killed — wrong message |
| `[grown]` escaping-control arm | killed — wrong message |
| non-growing accepted case | passed (correct — no false positive) |

The fifth arm does not die under this mutation, and that is expected and
correct: it was built to prove the buffer is load-bearing, and the buffer is
still present in this mutant (only the re-sample was reverted), so the
buffer alone still catches it — the real read of `MAX_CONFIG_BYTES + 1`
bytes on the actually-grown file returns 65537 bytes, which the pre-existing
short-read comparison (`len(raw) != info.st_size`) flags regardless of what
the re-sample would have said.

The other four cases died, by two distinct failure modes: the short-read
arm dies with `DID NOT RAISE` (the substituted read hides growth entirely
with no re-sample to catch it), and the remaining three still raise
`ConfigRefused` — via the old short-read comparison, because a real read on
the grown file returns more bytes than the pre-growth sample — but with the
pre-existing message ("config file read returned 65537 of 65536 bytes: ...")
rather than the new one, so each case's assertion on its own message
(`"grew" in ...`) failed. This is the exact defect the Design's ordering
note describes: without the re-sample, a grown file is still refused by the
short-read comparison in these three cases, but with a message that reads as
truncation rather than growth.

The non-growing accepted case stayed green under both mutations.

#### First pass (superseded) — before the fifth arm existed

Recorded for the record, since it is what motivated the fifth arm. Mutation
1, run against only the first four new cases, killed none of them: the
re-sample compares `os.fstat(fd)` taken after the read against the size
sampled before it, and because those four cases all grow the file for real
on disk (through a second descriptor or a real write), the re-sampled
`fstat` sees the true current size regardless of how many bytes `os.read`
was asked for or returned. That left the buffer — the registered remedy —
verified by no case, which is the gap the coordinator's follow-up named and
the fifth arm now closes.

### Whole-package regression

`python3 -m pytest packages/jsonl-otlp-exporter/` — never with `-q`, since the
package's `pyproject.toml` already sets `addopts = "-q"` and a second `-q`
would double to `-qq` and suppress the summary line.

- Before this delivery touched the file (observed at the start of this task):
  **417 passed, 1 skipped** (the single skip is pre-existing and unrelated —
  `test_live_collector.py`, no receiver on 4318). This differs from the 411
  baseline the task brief stated; not re-derived here, reported as observed.
- After the repair, with the first four new cases added: **421 passed, 1
  skipped** (417 + 4 new cases, no regressions, same single pre-existing
  skip).
- After the fifth arm was added (this follow-up): **422 passed, 1 skipped**
  (421 + 1, no regressions, same single pre-existing skip).

### Gates

- `make lint-ruff lint-mypy`: clean (`All checks passed!` /
  `Success: no issues found in 148 source files`).
- `ruff check .`: `All checks passed!`.

## T3: Bound configuration acquisition

### Repair

`packages/jsonl-otlp-exporter/jsonl_otlp_exporter/config.py`:

1. `_CONFIG_TIMEOUT_SECONDS = 5` (private), cited to AC-0077.
2. `read_config_file`'s body split into `_read_config_file(path, deadline)`
   (takes an already-established deadline) and `_acquire_bytes(path,
   deadline)` (the open, the descriptor checks and the read, run inside a
   nested `_do`). `read_config_file` itself became a one-line wrapper that
   establishes its own deadline (`time.monotonic() + _CONFIG_TIMEOUT_SECONDS`)
   and calls `_read_config_file` — its signature and `__all__`'s membership
   are both unchanged.
3. `_run_bounded(func, path, deadline)`: runs `func` on a daemon
   `threading.Thread`, joins with `deadline - time.monotonic()`, raises
   `ConfigRefused` naming the bound when the worker is still alive, re-raises
   the worker's own exception otherwise, and raises without starting a worker
   when the deadline has already passed. Reused by shape from
   `transport._resolve_bounded`, not by import.
4. `_scope_settings` gained a `deadline` parameter and calls
   `_read_config_file` instead of `read_config_file`; `resolve_telemetry`
   establishes one deadline before either scope is read and passes it to
   both `_scope_settings` calls.

No existing `ConfigRefused` message was reworded; the one new message —
`"config file acquisition exceeded the {N}s bound: {path}"` — names a fact
none of the other ten states.

**Follow-up (post-review): the message's two raise sites were folded into
one.** `_run_bounded` raises this message from two branches — `remaining <=
0` (the deadline was already spent before this file) and `worker.is_alive()`
(the join timed out) — and both constructed the identical f-string inline.
Extracted to `_acquisition_bound_refused(path) -> ConfigRefused`, called from
both branches, following the same move `_shown` already makes in this module:
one place for a fact several call sites would otherwise each restate. This
did not change control flow, only where the message is built.

### New cases, and their observed red

Each of the three substitution cases was first observed as a **hang** against
the unrepaired build (T1+T2's committed state, i.e. `HEAD` for this file),
via an ad hoc script outside the suite that calls `read_config_file` with one
of `os.open`/`os.fstat`/`os.read` monkeypatched to block indefinitely,
launched as a subprocess under a `subprocess.run(..., timeout=3)` harness so
the observation itself terminates. All three timed out at the full 3s bound
with only `"calling read_config_file, mode=<x>"` printed and no further
output — the call itself never returned:

| Substituted call | Observed against unrepaired build |
| --- | --- |
| `os.open` | `subprocess.TimeoutExpired` at 3.01s (hung) |
| `os.fstat` | `subprocess.TimeoutExpired` at 3.01s (hung) |
| `os.read` | `subprocess.TimeoutExpired` at 3.01s (hung) |

Then, against the same unrepaired build, `pytest` was run over the actual
new cases (`TestAcquisitionBound` in `test_config.py`, the CLI case in
`test_cli.py`, the `[acquisition-timeout]` arm in
`test_two_scope_config.py`): every one failed at fixture setup with
`AttributeError: module 'jsonl_otlp_exporter.config' has no attribute
'_CONFIG_TIMEOUT_SECONDS'`, because the constant the repair introduces does
not exist yet. That is also a red, though a different shape from the raw
hang above — recorded as observed, not reshaped to look like the hang.

After the repair landed, the same ad hoc script returns/raises promptly
(`ConfigRefused("config file acquisition exceeded the 5s bound: ...")` at
t=5.00s against the real 5-second default), and the full pytest suite is
green:

| Case | File | Result after repair |
| --- | --- | --- |
| `TestAcquisitionBound::test_a_blocking_open_is_refused_within_the_bound` | `test_config.py` | passed |
| `TestAcquisitionBound::test_a_blocking_descriptor_proof_is_refused_within_the_bound` | `test_config.py` | passed |
| `TestAcquisitionBound::test_a_blocking_read_is_refused_within_the_bound` | `test_config.py` | passed |
| `TestAcquisitionBound::test_the_bound_covers_both_files_together_not_one_each` | `test_config.py` | passed |
| `TestReviewRegressions::test_a_blocking_configuration_read_ends_the_run_within_the_bound` | `test_cli.py` | passed, exit 1, `"bound"` on stderr |
| `TestHostileContentIsEscaped::test_every_refusal_escapes_a_hostile_path[acquisition-timeout]` | `test_two_scope_config.py` | passed |

Every substituted call in every case above blocks on a `threading.Event` the
test sets in its own `finally`, so no abandoned worker outlives its case.

### The seventh case: a branch none of the above reaches

A review pass found that `_run_bounded` has **two** ways to refuse, not one:
`remaining <= 0` (the deadline was already spent before this file's worker
would even start) and `worker.is_alive()` (the join timed out). All six
cases above drive the second branch only. The reviewer measured the gap
directly: replacing `if remaining <= 0:` with `if False:` (join kept
well-formed via `max(remaining, 0.05)`) left the suite at 428 passed / 1
skipped — unchanged. That branch carries AC-0002's actual subject — one
shared deadline, so a second file cannot buy a fresh budget — and nothing
tested it.

`test_a_deadline_already_spent_refuses_the_second_file_without_a_worker`
(`test_config.py::TestAcquisitionBound`) closes this. Reaching the branch by
real elapsed time is a race the join forbids — the first file would have to
overrun the budget and still succeed — so the clock is substituted instead,
the same technique the other cases use on `cfg.os.read`/`cfg.os.fstat`:
`cfg.time.monotonic` is patched to return real time for its first two calls
(the deadline `resolve_telemetry` establishes, then the repository file's
own `_run_bounded` check) and a time 3,600 seconds past the deadline from the
third call onward (the user file's `_run_bounded` check). `os.open` is also
patched to raise `AssertionError` if ever called for the user file, so the
case fails loudly if a worker starts at all. The refusal is asserted to name
the **user** file's path (`cfg._shown(user) in message`) and not the
repository file's (`cfg._shown(repo) not in message`) — that is what proves
the budget was shared rather than reset.

Verified the same way the reviewer measured the gap:

- **Red against the branch-1 mutation** (`if remaining <= 0:` replaced with
  `if False:`, join kept well-formed with `max(remaining, 0.05)`): the new
  case failed with `AssertionError: a worker was started for the user file
  after its shared deadline had already passed` — `os.open` really was
  called for the user file, because the branch that should have refused
  first no longer exists. All other cases in the suite stayed green; total
  **1 failed, 428 passed, 1 skipped**.
- **Green after restoring the real file**: **429 passed, 1 skipped** (428 +
  this one case, no regressions).

This was re-verified against the file's current, post-extraction shape (the
mutation and the restore were re-run after `_acquisition_bound_refused` was
added — same result both times).

### Mutation proof: each syscall's move onto the worker is individually load-bearing

Three mutants of `_acquire_bytes`, each moving exactly one of the three
blocking syscalls back off the worker while leaving the other two bounded
(`config.py` was swapped for each mutant against its current, post-extraction
shape; the six cases above plus the two-file case *and* the new
deadline-already-spent case were rerun under `pytest --timeout=15`; the real
file was restored and the full suite reconfirmed green at 429 passed / 1
skipped before and after every mutation):

**Mutation OPEN — `os.open` moved off the worker, run synchronously before it
starts.**

| Case | Result |
| --- | --- |
| `test_a_blocking_open_is_refused_within_the_bound` | **killed** — `Failed: Timeout (>15.0s) from pytest-timeout` |
| `test_the_bound_covers_both_files_together_not_one_each` | **killed** — same timeout (the user file's blocked `os.open` is exactly what this case drives) |
| `test_a_deadline_already_spent_refuses_the_second_file_without_a_worker` | **killed** — `AssertionError: a worker was started for the user file after its shared deadline had already passed`. Genuine, not incidental: this mutant moves `os.open` to run unconditionally *before* `_run_bounded` is ever called, so the `remaining <= 0` check no longer gates the open at all — the user file's `os.open` fires whether or not the deadline has passed. |
| `test_a_blocking_descriptor_proof_is_refused_within_the_bound` | passed (not killed) |
| `test_a_blocking_read_is_refused_within_the_bound` | passed (not killed) |
| CLI case | passed (not killed) |
| `[acquisition-timeout]` escaping-control arm | passed (not killed) |

**Mutation FSTAT — both `os.fstat` calls (the initial descriptor proof and
the post-read re-sample) moved off the worker, run synchronously; `os.open`
and `os.read` each kept their own separate `_run_bounded` call.**

| Case | Result |
| --- | --- |
| `test_a_blocking_descriptor_proof_is_refused_within_the_bound` | **killed** — `Failed: Timeout (>15.0s) from pytest-timeout` |
| `test_a_deadline_already_spent_refuses_the_second_file_without_a_worker` | **killed, but not cleanly** — see below |
| `test_a_blocking_open_is_refused_within_the_bound` | passed (not killed) |
| `test_the_bound_covers_both_files_together_not_one_each` | passed (not killed) |
| `test_a_blocking_read_is_refused_within_the_bound` | passed (not killed) |
| CLI case | passed (not killed) |
| `[acquisition-timeout]` escaping-control arm | passed (not killed) |

**Mutation READ — the read and its re-sample `fstat` moved off the worker,
run synchronously; `os.open` and the initial descriptor proof kept their
`_run_bounded` call.**

| Case | Result |
| --- | --- |
| `test_a_blocking_read_is_refused_within_the_bound` | **killed** — `Failed: Timeout (>15.0s) from pytest-timeout` |
| CLI case | **killed** — same timeout |
| `[acquisition-timeout]` escaping-control arm | **killed** — same timeout |
| `test_a_blocking_open_is_refused_within_the_bound` | passed (not killed) |
| `test_a_blocking_descriptor_proof_is_refused_within_the_bound` | passed (not killed) |
| `test_the_bound_covers_both_files_together_not_one_each` | passed (not killed) |
| `test_a_deadline_already_spent_refuses_the_second_file_without_a_worker` | passed (not killed) |

No syscall-substitution case survived the mutation it was written to catch,
and none of the six original cases died under a mutation it does not
concern — each kills exactly the mutant that moves its own syscall off the
worker, and only that mutant.

**Reported as observed, not adjusted to fit: the new deadline-already-spent
case is also killed by Mutation OPEN and Mutation FSTAT, for two different
reasons, only one of which is the property that case claims to test.**

- Under **Mutation OPEN**, the kill is genuine and expected: that mutant
  makes `os.open` run unconditionally before `_run_bounded` exists at all
  for the open step, so the deadline no longer gates it — precisely the
  "second file gets its own budget" failure AC-0002 forbids, just reached
  through the open path instead of through `remaining <= 0` directly. This
  is a real, meaningful kill.
- Under **Mutation FSTAT**, the kill is an artifact of the test's own
  technique, not evidence about the fstat mutation. That mutant restructures
  `_acquire_bytes` into *two* separate `_run_bounded` calls per file (one for
  open, one for read) instead of one. The new case's clock substitution
  assumes exactly one `_run_bounded` call per file (true of the real,
  delivered code) — it lets the first two `time.monotonic()` calls see real
  time and jumps every call after that. Under Mutation FSTAT the *second*
  such call is the **repository** file's own read step, not the user file's
  open step, so the clock jumps a call early and the repository file's read
  is refused instead — the assertion fails because the message names `repo`,
  not because the mutation broke anything about the shared deadline. This is
  reported rather than smoothed over per the instruction not to adjust a
  mutation (or, here, a case) to fit after the fact: the deliberately-targeted
  mutation for this case is the `if remaining <= 0:` → `if False:` edit above,
  which is the one that isolates the property cleanly, and that one kills
  only this case.

### Whole-package regression

`python3 -m pytest packages/jsonl-otlp-exporter/` — never with `-q`.

- Before this task (T1+T2 already landed): **422 passed, 1 skipped** (same
  pre-existing, unrelated skip — `test_live_collector.py`, no receiver on
  4318).
- After T3's repair and its first six new cases: **428 passed, 1 skipped**
  (422 + 6, no regressions, same single pre-existing skip).
- After the seventh case (the deadline-already-spent case) and the
  `_acquisition_bound_refused` extraction: **429 passed, 1 skipped**
  (428 + 1, no regressions, same single pre-existing skip).

### Gates

- `make lint-ruff lint-mypy`: clean (`All checks passed!` /
  `Success: no issues found in 148 source files`).
- `ruff check .`: `All checks passed!`.

## T4: Published surface and registration

### Authored changes

- `packages/jsonl-otlp-exporter/README-pypi.md`'s `## Limits` table gained one
  row naming the configuration-acquisition bound, placed after `Whole run |
  120 seconds` and before the existing file-size row, stating the behaviour
  ("5 seconds, from before the first file is opened") rather than the private
  `_CONFIG_TIMEOUT_SECONDS` symbol.
- `packages/jsonl-otlp-exporter/CHANGELOG.md`'s `## 0.2.0 — unreleased`
  section, under `### Added`, gained two separate bullets: one for the
  exact-ceiling growth-race repair, one for the acquisition bound. No new
  version heading was added and no version was bumped — the section is
  correct as `unreleased` because nothing has been published.
- `workspace.toml`'s `[backlog].open` lost both
  `pre-existing-config-exact-ceiling-growth-race` and
  `pre-existing-config-io-outside-every-deadline` entries, each together with
  its multi-line `#` comment block. `sender-cannot-explain-its-effective-configuration`
  was left untouched, per the spec's `Follow-ons` section.

### AC-0004's checks

- `grep -n "Configuration acquisition" packages/jsonl-otlp-exporter/README-pypi.md`
  — matched line 150 (the new `## Limits` row).
- Two separate greps scoped to the `## 0.2.0 — unreleased` section: one for
  `"complete file"` (the exact-ceiling change) and one for `"5 second"` (the
  acquisition bound) — both matched, on separate bullets.
- `grep -q "pre-existing-config-exact-ceiling-growth-race" workspace.toml` and
  `grep -q "pre-existing-config-io-outside-every-deadline" workspace.toml` —
  both exit 1 (absent), confirmed with the `!`-safe form rather than
  `grep -c` (which exits 1 on no-match and would misreport as a harness
  failure).
- `python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))"` —
  parses clean after the removal.

### Whole-package regression (run in the order the plan pins)

1. `python3 -m pytest packages/jsonl-otlp-exporter/` (never `-q`): **429
   passed, 1 skipped** — matches the baseline recorded at the top of this
   task exactly (the single skip is the same pre-existing, unrelated one —
   `test_live_collector.py`, no receiver on 4318). T4 touches no test or
   production file in this package, so an unchanged count is the expected
   result, not a coincidence.
2. `python3 -m pytest tests/roster/ -q`: **1685 passed, 6 skipped, 46
   subtests passed** in 402.60s, exit 0.
3. `python3 tools/test-lint-pack-test-boundary.py`: `ok — 154 cases passed`,
   exit 0.
4. `python3 packages/jsonl-otlp-exporter/tests/wiring_sweep.py`, run against
   the merge base first (`d071874fa`, checked out into a scratch worktree via
   `git worktree add`, never `git stash`) and then against the change:

   **Merge base** (418 tests collected): `45 wirings mutated, 3 survived`.

   | Verdict | Site | Keyword |
   | --- | --- | --- |
   | SURVIVED | `cli.py:184` | `size_at_open=info.st_size` |
   | SURVIVED | `profile.py:65` | `frozen=True` |
   | SURVIVED | `transport.py:109` | `frozen=True` |
   | HUNG | `transport.py:526` | `daemon=True` |

   **Change** (430 tests collected): `47 wirings mutated, 4 survived`.

   | Verdict | Site | Keyword |
   | --- | --- | --- |
   | SURVIVED | `cli.py:184` | `size_at_open=info.st_size` |
   | SURVIVED | `config.py:242` | `daemon=True` (new) |
   | SURVIVED | `profile.py:65` | `frozen=True` |
   | SURVIVED | `transport.py:109` | `frozen=True` |
   | HUNG | `transport.py:526` | `daemon=True` |

   Both lists match the task brief's stated baseline (`profile.py:65`,
   `transport.py:109`, `cli.py:184`, `transport.py:526`) exactly at the merge
   base, confirming none of those four is newly introduced.

   **The one new site, judged rather than assumed:** `config.py:242`'s
   `daemon=True` is on `_run_bounded`'s worker thread, added by T3 and
   documented in its own docstring as "Reused by shape from
   `transport._resolve_bounded`, not by import" — the two functions are
   structurally identical (`threading.Thread(target=..., daemon=True)`,
   `.start()`, `.join(remaining)`, refuse if still alive). `transport.py`'s
   own instance of this same construct is the line that **hangs** under
   mutation (`transport.py:526`), not one that survives — so the two are not
   the same call site behaving differently, they are two *different*
   equivalent call sites, and only one of the two test suites happens to
   drive its worker into a genuine unreleased hang.
   Read `packages/jsonl-otlp-exporter/tests/unit/test_config.py:332-448`:
   every substituted blocking call in `TestAcquisitionBound` blocks on a
   `threading.Event` that the test itself sets before the case ends ("so no
   worker outlives the case" — this is AC-0002's own stated design, not an
   incidental gap). Because every test releases its worker before the test
   ends, the worker always completes whether or not it was started with
   `daemon=True`; removing the flag cannot make any of these tests hang, so
   the mutation survives. This is the same class of gap as the three
   pre-existing survivors (a construction-time flag — `frozen=True` on a
   dataclass, `size_at_open` read but not cross-checked against a second
   read — that is not itself part of any behavioural assertion the suite
   makes), not a new functional regression. Judgement: **accepted**, on the
   same basis as the three carried-forward survivors, and consistent with
   the task brief's own prediction that a new survivor here was "plausible."
   No code in `config.py` or its tests was touched to reach this judgement —
   T4's `Touches` does not include either, and T3 is complete.
5. `python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root .`:
   `spec metadata clean (3 of 479 spec(s) changed against origin/main)`, exit
   0 — no dangling deferral anchor.
6. `make lint-ruff lint-mypy`: clean (`All checks passed!` /
   `Success: no issues found in 148 source files`). `ruff check .`: `All
   checks passed!`.

## Gate failure and repair — the new wiring-sweep survivor

T4's regression found a **new** survivor that the merge base does not carry:
`config.py:242`'s `daemon=True`, on the acquisition worker T3 added. The bar for
this delivery is no new survivor, so this was routed as a gate failure
(`gates-failed`, implementation_retry_count=1) rather than recorded as an
accepted residue.

**Why nothing could see it.** Every case in `TestAcquisitionBound` releases its
substituted blocking call through a `threading.Event` at teardown — deliberately,
so no abandoned worker outlives a case. That is correct test hygiene and it is
also exactly why none of those cases can observe the flag: by interpreter
shutdown the worker has already finished, daemon or not. The flag only has an
effect in the state the bound exists for, a call that never returns.

**The repair.** `test_an_abandoned_worker_does_not_stop_the_process_exiting`
drives a real child process whose substituted `os.read` is never released, so the
worker is genuinely abandoned, and asserts the child *exits*. The subprocess
`timeout` is what turns the mutant's hang into a failed assertion instead of a
hung suite.

**Measured, both arms:**

| Build | Result |
| --- | --- |
| shipped (`daemon=True`) | child exits, rc=0, 0.42s, having printed `REFUSED` |
| mutant (`daemon=True` removed) | child never exits; the case fails at its 30s timeout with the diagnostic naming the flag |

**Sweep comparison, after the repair** — survivors now identical to the merge
base `d071874fa`, so no new survivor remains:

| Site | Merge base | After the change |
| --- | --- | --- |
| `cli.py:184` `size_at_open=info.st_size` | SURVIVED | SURVIVED |
| `profile.py:65` `frozen=True` | SURVIVED | SURVIVED |
| `transport.py:109` `frozen=True` | SURVIVED | SURVIVED |
| `transport.py:526` `daemon=True` | HUNG | HUNG |
| `config.py:242` `daemon=True` | — | **killed** (was SURVIVED before this repair) |

Merge base: 45 mutated, 3 survived. After: 47 mutated, 3 survived, 431 tests
collected. The three carried-forward survivors and the one hang are pre-existing
and out of this delivery's scope.

**The lesson, not the incident.** Teardown discipline that releases every
substituted blocking call is right, and it blinds the suite to any behaviour that
only appears when a call is *not* released. A flag whose whole purpose is to
govern abandonment needs a case that actually abandons something — which means a
child process, because the observable is interpreter shutdown, and a test cannot
observe its own.

## Post-gates review fixes

Five adjudicated findings, applied after T4's gates were green. Baseline going
in: **430 passed, 1 skipped**. Baseline going out: **432 passed, 1 skipped**
(two new cases; no regressions; the one skip is the same pre-existing,
unrelated `test_live_collector.py`).

### Finding 1 (blocker) — a stale re-sample plus a read capped at the sampled
size still accepted a prefix

**Repair.** One more `os.read(fd, 1)` added to `_acquire_bytes`'s `_do`, after
the existing short-read comparison, inside the same bounded worker. At genuine
EOF it returns `b""`; any other result means the descriptor still has an unread
byte, which means the file held more than the reader just accepted. New
message: `"config file has bytes beyond the {len(raw)} obtained during the
read: {path}"`. No existing message reworded, no loop, `MAX_CONFIG_BYTES`
unchanged.

**New cases:**
- `TestExactCeilingGrowthRace::test_growth_hidden_by_a_capped_read_and_a_stale_resample_is_caught_by_the_probe`
  (`test_config.py`) — a file armed at exactly the ceiling, a substituted
  `os.read` that grows the file for real through a second descriptor and then
  caps its own return at the sampled length (`cfg.MAX_CONFIG_BYTES`), and a
  substituted `os.fstat` whose second call (the re-sample) reports the stale,
  pre-growth size. Both existing checks pass; only the probe catches it.
- `TestHostileContentIsEscaped::test_every_refusal_escapes_a_hostile_path[growth-residue]`
  (`test_two_scope_config.py`) — the same construction on a hostile-named file,
  proving the new message escapes the path and is reached by its own site
  (twelfth arm, twelfth raise site).

**Mutation proof** (probe removed, everything else kept): both new cases
failed with `Failed: DID NOT RAISE ConfigRefused` — the file was silently
accepted and parsed, reproducing the finding exactly. Restored: both pass, and
the full package suite is green at 432 passed / 1 skipped. `make lint-ruff
lint-mypy` and `ruff check .` clean on both the mutant and the restored file
(same output as below).

### Finding 2 (concern) — the growth message misreported shrinkage

**Repair.** Reworded the message this delivery already added (not a
pre-existing `ConfigRefused` message, so the `Ask first` entry on existing
message text does not apply): `"config file grew from X to Y bytes..."` →
`"config file size changed from X to Y bytes..."`. True in both directions.

**Updated assertions**, all four sites the finding named, plus one comment
that quoted the old fragment (`test_config.py:281`, found by grepping `"grew"`
across the package):
- `test_config.py::TestExactCeilingGrowthRace::test_growth_between_the_sample_and_the_read_is_refused`
  — `assert "grew"` → `assert "changed"`.
- `test_config.py::TestExactCeilingGrowthRace::test_growth_a_short_read_hides_is_still_caught_by_the_resample`
  — same.
- `test_config.py::TestExactCeilingGrowthRace::test_growth_the_resample_cannot_see_because_fstat_is_stale`
  — `assert "grew" not in ...` → `assert "changed" not in ...`.
- `test_cli.py::test_a_growing_configuration_file_is_refused_with_nothing_sent`
  — same rename.
- `test_two_scope_config.py::test_every_refusal_escapes_a_hostile_path[grown]`
  — same rename.

No new case added for a pure shrink: the branch (`grown.st_size !=
info.st_size`) is direction-agnostic and its mutation-load-bearing-ness is
already established (Mutation 2 in T2's section above kills it regardless of
direction); a shrink-only case would exercise the same branch and comparison
operator a growth case already drives, so it was judged not to add
distinguishing coverage.

### Finding 3 (concern) — released workers were not waited for

**Repair.** Added `packages/jsonl-otlp-exporter/tests/unit/conftest.py` with
`await_released_workers(before, timeout=5.0)`: snapshots `threading.enumerate()`
before the blocking call starts, and after `release.set()` joins every thread
that appeared since, asserting none is still alive. Test-only; no production
surface added.

**Applied** at the four sites named: `test_config.py`'s
`test_a_blocking_open_is_refused_within_the_bound`,
`test_a_blocking_descriptor_proof_is_refused_within_the_bound`,
`test_a_blocking_read_is_refused_within_the_bound`, and
`test_the_bound_covers_both_files_together_not_one_each`; and
`test_two_scope_config.py`'s `[acquisition-timeout]` arm of
`test_every_refusal_escapes_a_hostile_path`. Each now captures
`before_threads = set(threading.enumerate())` before starting, and calls
`await_released_workers(before_threads)` in the same `finally` block right
after `release.set()`. `test_an_abandoned_worker_does_not_stop_the_process_exiting`
is untouched, per the finding — it deliberately never releases its worker.

Strengthened the `TestAcquisitionBound` class docstring to say the case joins
the released worker, not only that it releases it — the docstring's existing
claim is now what the mechanism actually establishes, so it was not narrowed.

All five sites pass with the join in place; the full package suite stays
green at 432 passed / 1 skipped.

### Finding 4 (nit) — the spent-deadline case was pinned to an ordinal call
count

**Repair.** `test_a_deadline_already_spent_refuses_the_second_file_without_a_worker`
(`test_config.py`) no longer counts `time.monotonic()` calls. It now
monkeypatches `cfg._run_bounded` with a thin, fully-delegating wrapper that
tags which `path` is in flight (`current_path["value"] = path`) *before*
calling the real function; the `time.monotonic` substitute reads that tag
instead of an ordinal count — real time whenever the tagged path is not the
user file (however many internal calls the repository file's acquisition
makes), a clock jumped 3,600s past the deadline only when the tagged path is
the user file. The proof stays at the `resolve_telemetry` two-scope surface;
`_run_bounded` is wrapped, not replaced, so the real `remaining <= 0` branch
still runs and still decides the outcome.

**Re-verified, per the finding's instruction:** `if remaining <= 0:` mutated to
`if False:` (join kept well-formed via `remaining = max(remaining, 0.05)`).
Result: **1 failed, 431 passed, 1 skipped** — the single failure was exactly
`test_a_deadline_already_spent_refuses_the_second_file_without_a_worker`,
failing with `AssertionError: a worker was started for the user file after its
shared deadline had already passed` (the assertion inside `exploding_open`,
meaning a worker really was started for the user file this time). No other
case failed. Restored: **432 passed, 1 skipped**, matching the pre-mutation
baseline exactly.

### Gates (this pass)

- `make lint-ruff lint-mypy`: clean (`All checks passed!` /
  `Success: no issues found in 148 source files`).
- `ruff check .`: `All checks passed!`.
- `python3 -m pytest packages/jsonl-otlp-exporter/` (never `-q`): **432
  passed, 1 skipped** (430 baseline + 2 new cases, no regressions, same
  single pre-existing skip).

## Round 2 of post-gates review, and the owner's disposition

Three findings sustained. One was repaired; two were accepted by the owner.

**Repaired — the sixth site the first repair missed.** The round-1 worker-join
fix applied `await_released_workers` to five `release.set()` sites and missed the
sixth, in `test_cli.py`. The finding named five siblings and the omission; the
walk afterwards enumerated **every** `release.set()` call site rather than the
ones the finding listed, and found six call sites in total, all now paired with a
join. Three further textual matches are prose inside docstrings, not call sites —
counting them would have reported nine sites and a phantom gap.

**Accepted by the owner — the pinned fields now understate what shipped.** The
review repairs added a probe case, a twelfth escaping arm and `conftest.py`, none
of which appear in T2's `Tests`, T2's `Done when`, T3's `Touches` or AC-0001's
Testing Strategy. Two mechanics make this unfixable in place rather than merely
unfixed: `approve-plan` recorded `approved_plan_hash=39569cc8777e`, and the
controlled-amendment path forbids editing a completed task's section at all — a
correction there is a new task, not an edit.

The owner's decision, recorded on 2026-09-17, is to leave the pinned fields as
they are. Disposition `accept-as-proportionate`. What that costs, stated plainly
rather than implied: no coverage is missing and every added case runs in the
suite with its own mutation evidence recorded above, but if one of those added
cases were later deleted, no *pinned* field would notice — only the suite would.
The exposure is a future deletion going unremarked, not a present gap.

## Manual QA — the shipped artifact, not `cli.main`

A wheel was built from this tree, installed into a fresh virtual environment, and
the **console script** driven against a real HTTP receiver on `127.0.0.1:4318`.
Measured 2026-09-17. The installed copy was confirmed to carry all three repairs
(`MAX_CONFIG_BYTES + 1` read, post-read re-sample, one-byte probe), with
`_CONFIG_TIMEOUT_SECONDS = 5` and `__all__` unchanged — so the public surface is
the same as before this delivery.

| # | Invocation | Observed |
| --- | --- | --- |
| 1 | documented happy path, configuration split across both scopes | `EXIT=0`; receiver saw `POST /v1/logs`, `application/json`, `service.name=manual-qa-sender` from the **repository** scope with the endpoint from the **user** scope, 1 record |
| 2 | `--config` at **exactly** 65,536 bytes, not growing | `EXIT=0`, record delivered, `service.name=exactly-at-the-ceiling` — the paired negative, on the real binary; an off-by-one repair would fail here |
| 3 | `--config` at 65,537 bytes | `EXIT=1`, `config file is 65537 bytes, over the 65536-byte ceiling: '…'` |
| 4 | `--config` carrying an inadmissible `[telemetry]` key | `EXIT=1`, `[telemetry] settings this command cannot receive: 'bogus_key' (from repository '…') (admitted: endpoint, service_name)` — the refusal the fail-open was converting into a silent accept |

Case 1 also re-establishes that a configuration file **outside** `--root` is
accepted while a profile outside it is refused: the first attempt refused the
profile with `input path is outside --root`, which is AC-0062's carve-out and
AC-0048's confinement behaving as separately specified.

### What manual QA could not stage, and why that is not a gap

**The growth race itself is not reproducible from outside the process on a local
filesystem.** Sixty runs were attempted against the shipping binary with a
concurrent appender writing an inadmissible key in a tight loop. All sixty were
refused by the **sampled-size** check — `config file is 65978 bytes, over the
…ceiling` — because an external writer cannot be timed into the microsecond
window between the command's `fstat` and its `read`. Not one run reached the
branch under repair.

That is evidence about the instrument, not about the defect. It is the same
reason the registered entry was found by review rather than in the field, and the
reason every case for this branch substitutes the seam: a test that can only be
driven by winning a microsecond race is a test that reports flaky green. The
branch's proof is the substituted-seam cases and their individual mutation reds,
recorded above.

**The acquisition bound is likewise not stageable through the console script** on
local disk: no local regular-file read blocks, and a FIFO is refused as
non-regular before any read happens. Its real-process evidence is the
child-process case, which drives a genuine abandoned worker in a real interpreter
and asserts the process still exits — measured at 0.42s shipped versus never with
`daemon=True` removed.
