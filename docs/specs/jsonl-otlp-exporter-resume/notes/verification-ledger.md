# Verification ledger — jsonl-otlp-exporter-resume

Execution observations. The approved `spec.md` and `plan.md` hold obligations;
this file holds what running them actually produced, including every deviation
from a task row's literal method.

## T1 — deviation from the approved stub: `resolve_start_offset` and `fd`

**Observed.** The T1 stub, materialized byte-identical from `plan.md`, failed two
of its own cases against a correct implementation:
`test_a_matching_cursor_is_honoured` and
`test_an_offset_equal_to_the_size_is_honoured`. Both called
`resolve_start_offset(cursor, info, stream=...)` with no descriptor and expected
the cursor honoured.

**Cause.** The two cases predate AC-0030. They were written in the first draft,
when identity and range were the only checks. AC-0030 — the offset must sit
immediately after a newline, proven on the descriptor — was added during the
round-2 secure-design repair, and those two cases were never revisited. A pinned
`Tests:` stub and a pinned acceptance criterion therefore contradicted each
other. The stub validator could not see it: it resolves names and keyword
arguments, not semantics.

**Disposition.** Owner decision 2026-09-15, taken rather than the controlled
amendment procedure: AC-0030 constrains *the run*, and a run always holds the
descriptor `open_input` returned, so the criterion is satisfied at the level it
speaks about. `fd` is now a required parameter rather than one defaulting to
`None`, because a default would mean a caller that forgets it silently skips a
security control. The two cases open the fixture and pass its descriptor; the
fixture is written so the offsets under test are real record boundaries.

**Controls that catch a regression here.** T4's
`test_a_misaligned_cursor_is_refused_at_the_command` drives a misaligned cursor
through the assembled command and requires exit 1, so the check must be wired,
not merely present. `tests/wiring_sweep.py` removes the `fd=` keyword at the call
site and reports a survivor if nothing notices. Making `fd` required adds a third:
a caller that omits it is a `TypeError`, not a silent skip.

**Result.** `test_cursor.py`: 29 passed.

## T1-T6 gate evidence

Recorded here so the contract amendment below can bind each completed task to a
stable reference. All measured 2026-09-16 on the tree at amendment time.

| Task | Evidence |
| --- | --- |
| T1 | `test_cursor.py` 29 cases pass; `cursor.py` implements the four cursor routes |
| T2 | `test_source.py` 41 cases pass, including the eight positioned-reader cases |
| T3 | `test_transport.py` 74 cases pass, including the six accepted-offset cases |
| T4 | `test_cli.py` passes; the assembled command resumes, refuses and reports |
| T5 | the offset-journey and write-surface cases pass |
| T6 | `test_published_contract.py` AC-0021 check passes; README and CHANGELOG authored |

Whole-package suite at amendment time: 348 collected, 347 passed, 1 skipped.
`make lint-ruff lint-mypy`: pass, 149 source files. `ruff check` on the package:
pass. `tools/test-lint-pack-test-boundary.py`: pass, 154 cases.
`lint-spec-status.py`: clean, 0 warnings on either changed spec.

## Manual QA of the installed wheel, and the specification error it found

**Method.** A wheel was built from a copy of the package outside the repository,
installed into a fresh virtual environment, and the console script
`jsonl-otlp-export` was driven through eleven scenarios against a loopback
`http.server` receiver that recorded every request body. Nothing was built or
written inside the repository, because a stale in-tree `dist/` breaks later
gates here.

**Ten scenarios behaved as the contract requires.** `--version`; the
unconfigured run; stdout empty without `--report-cursor`; one JSON cursor line
with it; incremental resume sending only records appended since; rotation
detected with the reset notice and the new inode in the reported cursor; a
misaligned offset refused; a malformed cursor refused at both endpoint states;
and an unterminated final line withheld from both the send and the cursor
(reported offset 82 against a 163-byte file).

**One scenario found a specification error.** A resumed run whose cursor sits at
the end of the input exits **1**, with
`no line yielded a valid record; nothing was sent` on stderr, while still
printing a valid cursor on stdout.

Reproduced independently of the QA harness: run one exits 0 and sends one
record, returning `offset=82`; run two with that cursor exits 1 and sends
nothing.

**Cause.** The parent contract's AC-0039 requires exit 1 when no line yields a
valid record, and `cli.py` implements it as `emitted == 0`. That predicate
cannot distinguish *every line was invalid* from *there were no lines at all*.
Before resume existed the two were nearly the same condition. With a cursor at
end of file they are opposites: the second is the normal steady state of a
polling exporter, which is exactly the consumer this feature exists to enable.
The stderr text is wrong in the same way -- it reports invalid lines when no
line was read.

So the shipped behaviour is correct against the contract, and the contract is
wrong. This is a specification error rather than an observation, so it takes the
controlled amendment procedure rather than a note here.

**Owner decision 2026-09-16.** Amend. A zero-line resumed run exits 0 and says
what actually happened. Parent AC-0039 keeps its meaning for a run that read
lines and found none valid, so the empty-input case is unchanged. The rejected
alternatives were documenting the exit-1 behaviour in the README, which pushes a
special case for the normal path onto every consumer and makes exit 1 useless
for distinguishing failure from quiet, and fixing the code without amending,
which would leave the shipped command contradicting AC-0039 as written -- the
same defect class already corrected for `--config` and `--profile`.

## The wiring sweep, and what it found

`tests/wiring_sweep.py` removes each cross-module keyword argument in turn and
re-runs the suite; a survivor is a wiring with no control behind it. First
complete run: **44 wirings mutated, 4 survived, 2 hung.**

All five keywords this change adds were caught, so each has a control that fails
on its removal:

| Keyword | Site |
| --- | --- |
| `fd=` | `cli.py:124` — `resolve_start_offset`'s boundary proof |
| `start_offset=` | `cli.py:163` — the reader's start |
| `on_position=` | `cli.py:166` — the reader's consumed position |
| `timeout=` | `cli.py:70` |

`start_offset=` on `send_batches` is caught through the transport suite.

### The HUNG verdict on `cursor.py:141` was contention, not a defect

The sweep reported `HUNG` for removing
`inode=_integer(value["inode"], "inode")`, which would mean the suite failed to
finish inside the 90-second cap. Reproduced deliberately with the same mutation
and a hard cap over the cursor module alone: **`caught`, exit 1, 1.3 seconds**,
with `TypeError: Cursor.__init__() missing 1 required positional argument`. The
mutation is caught almost instantly.

Two peer sessions were running their own pytest in other worktrees of this
repository throughout the sweep. That is the cause. Worth recording because a
`HUNG` line reads like a defect in the code under test, and here it was a
property of the machine: the same run also showed the sweep's first attempt
stalling 93 minutes before its mutation loop even opened its results file, which
a QA agent independently traced to a `pyenv init` child stuck in state `T`
inside the login shell's profile.

The other `HUNG`, `transport.py:526 daemon=True`, is genuine and documented:
`test_transport.py` states that removing it keeps the interpreter alive so the
suite hangs rather than fails.

### Two survivors in this change, both given controls

- **`cursor.py:79 separators=(",", ":")`.** Nothing asserted the rendered
  spacing, so dropping the keyword produced `{"v": 1, …}` and every check still
  passed — silently falsifying the worked example under README `## Resuming a
  run`, which a reader copies onto a command line.
  `test_render_emits_compact_json` now pins the exact string.
- **`cursor.py:62 frozen=True`.** No control behind the immutability of a value
  that is compared against a descriptor's identity and then seeked to.
  `test_a_cursor_is_immutable` now asserts assignment raises.

### Two survivors left, both pre-existing

`profile.py:65` and `transport.py:109` are both `frozen=True` on dataclasses
that shipped in #1313, in code this change does not touch. They are the same
class as the `cursor.py` one and would take the same one-line control, but
fixing them belongs to a change that owns those modules. Recorded so the next
reader of a sweep result knows the remaining two are not new.

The bar this change is held to is that it adds no new survivor.

## Pre-existing: the package suite could not collect at all

**Observed.** `python3 -m pytest packages/jsonl-otlp-exporter/ -q` — the exact
command in `Makefile:574` and in this change's gate list — failed collection on
all eight pre-existing test modules with
`ModuleNotFoundError: No module named 'jsonl_otlp_exporter'`, before any file of
this change existed.

**Cause.** `packages/jsonl-otlp-exporter/pyproject.toml` carries its own
`[tool.pytest.ini_options]`. Pytest picks the nearest configfile and stops, so
the root `pyproject.toml`'s `pythonpath` — which lists this package — never
applies to a run invoked at that path. `packages/credbroker/pyproject.toml` has
the identical table and collects fine only because credbroker is pip-installed
in this environment (`site-packages/credbroker`), while this distribution is not
installed at all.

**Disposition.** Fixed rather than deferred, under the bundled-fixes carve-out:
one line, in the package this change already touches, same concern, mechanical.
`pythonpath = ["."]` added to that table with the reason in a comment. No
backlog entry was added, because there is nothing left to defer.

**Not fixed here.** `credbroker` has the same latent omission and the same
invocation in `Makefile:573`. It passes today only because the distribution is
installed, which also means that leg of `make test` exercises the installed copy
rather than the worktree source. That is a separate finding against a package
this change does not touch.

## Amendment 2: an ordering deviation, and how it was recovered

The controlled amendment procedure says to fire `contract-amendment` **before**
editing the spec or plan. On the second amendment the edits were applied first.
The transition then refused three times in a row, each refusal catching a real
consequence: missing evidence bindings for the tasks the wave advances had
marked complete; a `plan.md` status of `Drafting` when it validates the
pre-amendment status; and finally a `plan.md` hash that no longer matched the
scheduled baseline, because the edits had already added T8.

`loop-cohort`'s own recovery text for the third refusal offers a cohort reset,
and states plainly that it clears the retry counters and the stasis baseline and
re-pins whatever is on disk — "a re-approval in substance". That was declined.
Instead the amended files were copied aside, the pre-amendment versions were
written back from the git index — which still held them, because the tree had
been staged to generate the review diffs — the transition was fired against the
baseline it expected, and the amended content was copied back. No counter was
cleared and no baseline was re-pinned silently.

Recorded because the recovery depended on an accident: the index happened to
hold the approved baseline. Fire the transition first and none of this arises.

## T8: proving the new controls could fail, and what that found

The implementation review's finding was that several cases could not fail. So
each control added in T8 was run against the exact wrong implementation the
reviewer named, before being trusted. Measured 2026-09-16, restoring between
each:

| Mutation | Control |
| --- | --- |
| `raw["v"] != 1` instead of `_integer(value["v"], "v")` | caught |
| `except json.JSONDecodeError` instead of `except Exception` | caught |
| `else:` instead of `elif out.all_accepted:` — a high-water mark | caught |
| cursor printed only when `emitted[0]` | caught |

The third needed two corrections before it caught anything, and both are worth
recording because each made the control silently useless.

**The fixture could not reach its own target.** It was built with four batches
and `statuses=[200, 200, 400, 200]`. `MAX_ATTEMPTS_PER_RUN` is 3, so the run
returns at the third batch and the fourth — the accepted-after-refused batch the
case exists to catch — is never issued. The high-water-mark defect survived the
very test written for it. Rebuilt with three batches and `[200, 400, 200]`.

**`statuses` never worked past its first element.** The shared `_factory` helper
does `_Connection(list(responses) …)`, copying the queue per connection, and
`_post` opens a connection per request. Every request therefore popped index 0
and got the same status. `_run_against_receiver` now closes over one shared
queue. This is the second, independent reason the review's
`([200], [400], [200, 400], [200, 200])` finding was right: those cases were
vacuous both because five records fit one batch and because the second status
could never have been delivered.

Neither defect was visible from reading the test. Both needed the mutation run.

## The reviewer briefs specified a format `raw-classify` rejects

`loop-cohort review raw-classify` accepts exactly two shapes: a lone line equal
to the clean sentinel, or findings matching `FINDING_LINE_RE`, which requires the
title and the `file:line` citation on ONE line as
``**1. Title** `file:line` ``. The implementation-review briefs asked for
`## Blockers` with prose bullets instead.

Consequence: the adversarial and quality reports classified `invalid`,
`finding_count: 0`, and an invalid artifact cannot be adjudicated — so acting on
its prose skips the adjudication gateway entirely, which is the failure that
gateway exists to prevent. Every finding was instead verified directly against
the source before being acted on, which is stronger evidence than the prose, but
it is not the recorded path.

No fingerprints were recorded for that round. Recording fingerprints derived
from an artifact the classifier rejected would launder the invalid report into
the audit trail.

The re-review after these repairs mandates the grammar at the top of the brief,
which is where it has to be: a reviewer cannot retrofit a format it was never
given.

## Round 2 of the implementation review: two controls still satisfiable

With the grammar fixed, both reports classified. The adversarial lens returned
the clean sentinel; the quality lens returned two findings, both sustained.

**A whitelist can name `RecursionError`.** The decoder control raised it, so an
implementation catching `(json.JSONDecodeError, RecursionError)` passed while
still violating AC-0016 for any other decoder exception. It now raises a
test-local exception class, which only a general catch can satisfy. Proven:
narrowing the catch to that pair is caught.

**An offset that equals EOF proves nothing about the offsets before it.**
`test_a_skipped_line_still_advances_the_position` asserted the final record's
offset equals the file size. The final record ends at EOF, so a reader that
reported the descriptor's own position for every record — rather than a
line-accurate tally — satisfied it, which is exactly the bug the case is named
for. A line-accounting bug *was* caught (18 against 27); the descriptor-position
bug was not. The case now also pins the delta across the skipped line. Proven:
replacing the tally with `os.lseek(fd, 0, SEEK_CUR)` is caught.

That case came from T2, a completed task, so its plan section is left as the
record of what was approved and the correction is documented under T8 — per the
amendment rule that a completed task section is never rewritten.

Both rounds' pattern is the same and worth stating once: the production code was
right in every instance. What review found, four times over, was a control that
could not fail. The mutation runs are what turned each reviewer's claim into
evidence, and twice they found a further defect the reviewer had not seen — a
fixture the attempt budget never reached, and a response queue that reset per
connection.

## Round 3 of the implementation review: four more controls a wrong build satisfied

None of these was drift from the previous round's repairs. All four were gaps in
cases the earlier tasks introduced, found on a deeper pass.

**The one that mattered.** No case verified that a resumed reader's yielded
offsets are ABSOLUTE rather than relative to its seek.
`test_a_start_offset_skips_the_records_before_it` discarded every offset it was
handed, and every other offset assertion started from byte zero. Measured by
building the bug — `position = 0` instead of `position = start_offset` — and
running the whole suite: **0 of 349 cases noticed.**

The consequence is not cosmetic. A resumed run would report an offset short by
exactly the amount it had skipped, so the next run would resume from there and
re-send. Permanent re-sending on every subsequent run is the failure resume
exists to prevent, and it would have shipped.

I predicted T7's nothing-new case would catch it. It does not: with no line
consumed, `on_position` never fires, so the CLI's `consumed` cell keeps the
`begin` it was initialised with and the carve-out still matches. The prediction
was wrong and the measurement corrected it.

The other three:

- **A matching cursor at offset 0 was never exercised**, so a boundary checker
  that always reads `offset - 1` would pread at -1 and refuse it. Byte 0 is a
  real cursor — it is what a caller stores after a reset — so it must be
  honoured. Caught now.
- **Bool rejection was pinned for `offset` only.** An implementation using exact
  typing there and bare `isinstance(value, int)` for `device` and `inode` would
  admit JSON `true` for both. Caught now.
- **The split case asserted monotonic offsets and a correct final value**, which
  a splitter giving every batch its successor's offset also satisfies — and that
  build credits unsent records as soon as an early batch is accepted and the next
  refused. Each batch's end offset is now compared to its own last record's.

**A bad mutation of my own.** The first attempt at F4's proof mutated
`offsets[-1]` to `offsets[-1] if len(offsets) > 1 else offsets[0]`, which is
`offsets[-1]` in every case — a no-op. It reported SURVIVED, and for a few
minutes that looked like a weak control rather than a weak experiment. Replaced
with the real bug the plan had warned about, passing the parent's offsets to the
first half, which the control catches. A mutation that changes nothing proves
nothing, and it fails in the direction that looks like a finding.

## Round 4 of the implementation review: five more, all pre-existing

The reviewer was asked to state, for each finding, whether it was always in the
diff or drift from one of my repair rounds. It said all five were always there.
None came from a repair, so the loop had not converged.

Two mattered:

**The byte bound's ordering was unverified.** AC-0015 requires the length check
to run *before* the decoder, which is the bound's entire reason for existing —
it keeps an arbitrarily large literal away from `json.loads`. The fixture used a
4097-digit integer, which is under CPython's 4300-digit literal limit and so
parses cleanly; a build that decoded first and measured second reported
"too long" either way. A 5000-digit fixture makes `json.loads` itself raise, so
a length-first build says "too long" and a parse-first build reports a parse
failure. Proven: reordering the two checks is now caught.

**End of file was not automatically a boundary, but nothing said so.** A build
honouring `offset == st_size` unconditionally passed the newline-terminated
fixture and the interior-misalignment case. Against a file whose tail record has
no terminator it would accept the cursor, and the reader would start past bytes
belonging to an unfinished record — losing that record once the writer completed
it. The code was already correct; nothing pinned it. Proven.

The other three:

- **A zero-count `partialSuccess` could have been accepted.** AC-0007 keys on
  the object being non-empty, not on the count. The existing case paired the
  zero with an `errorMessage`, so it could not separate the two readings; a
  build rejecting only on `> 0` or a non-empty message would have advanced the
  offset past records the receiver was reporting on.
- **Offset zero could have bypassed identity validation.** Every mismatch case
  used a nonzero offset, so an early return for `offset == 0` skipped the reset
  notice. The read position is the same either way; what is lost is the operator
  being told the input was replaced.
- **A batch accepted only after a retry need not have been credited.** Every
  other accepted-offset case answers on the first attempt, so a build updating
  only on an immediate 2xx would re-send a batch the receiver had already taken.

All five proven to catch their named implementation before being trusted.

## Round 5: one control, and the convergence judgement

One finding, again pre-existing. AC-0006 covers a batch "produced and never
issued", but the only no-issue case supplied no batch at all and every
time-bound case started at offset 0 — so a build crediting a batch when it is
*pulled*, before any request is issued, passed them both. The new case puts the
run clock past its deadline with a batch carrying a nonzero end offset. Proven:
crediting on pull is caught.

The reviewer was asked directly whether further rounds would return real
findings or invented ones, and answered that coverage is otherwise proportionate
and further rounds would likely produce diminishing or invented findings. That,
not an absence of findings, is why the loop stops here: five rounds each
returned real defects, so a clean round was never the signal to wait for.

**Totals across the implementation review.** Three reviewers, seven passes, 17
findings. Every one concerned a control that could not fail or a criterion that
was over-broad — **not one was a defect in the production logic**, which the
adversarial and security lenses both returned clean on. Eleven mutation
experiments were run to turn reviewer claims into evidence, and three of them
found a further defect the reviewer had not seen: a fixture the 3-attempt budget
never reached, a response queue that reset per connection, and one no-op
mutation of my own that read as a weak control.

The single most valuable finding was that nothing verified a resumed reader's
offsets are absolute rather than relative to its seek. Building that bug showed
0 of 349 cases noticed, and shipping it would have made every run after a resume
re-send — the exact failure the feature exists to prevent.
