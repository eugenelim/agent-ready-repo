# Verification ledger — jsonl-otlp-exporter

Execution observations. The spec holds the contract and the plan holds the
strategy; neither is edited to record what happened here.

## AC-0006 — the live round trip, 2026-09-13

`otel/opentelemetry-collector-contrib:0.160.0` under Colima, an `otlp` receiver
on 4318 with `debug` (detailed) and `file` exporters. The three-line fixture was
posted through the real transport and read back from what the receiver stored.

| Emitted from | Reached | Observed |
| --- | --- | --- |
| `at` = `2026-09-13T05:52:24Z` | `timeUnixNano` | `2026-09-13 05:52:24 +0000 UTC` |
| `at` = `…T05:53:10.123456789Z` | `timeUnixNano` | `…05:53:10.123456789` — nanoseconds survived |
| `at` = `…T05:54:00+02:00` | `timeUnixNano` | `2026-09-13 03:54:00 +0000 UTC` — offset applied |
| `result` = `success` | `severityNumber` | `Info(9)`, `SeverityText: success` |
| `result` = `failure` | `severityNumber` | `Error(17)`, `SeverityText: failure` |
| `result` = `wave-passed` (unmapped) | — | `Unspecified(0)`, **record still stored** |
| `budgets` (nested object) | attribute | `Map({"gates":2,"review":3})` |
| `phase_s` = `12.5` / `46` | attribute | `Double(12.5)` / `Int(46)` |
| `note` = `null` / `"second"` | attribute | absent / `Str(second)` |
| `secret` (not allowlisted) | — | absent from every record |

Three records in, three records stored, zero rejected.

## Why two tests cover AC-0005 and AC-0006, and what happened when they disagreed

The golden was produced by the encoder it checks, so it can only detect drift.
The round trip is the only check that can see whether the *names* are right,
because a payload with correct structure and wrong names returns HTTP 200 and is
stored — the failure mode is wrong data, not absent data.

Two mutations, run 2026-09-13, show them doing different jobs:

| Mutation | Golden | Round trip |
| --- | --- | --- |
| `severityNumber` → `severity_number` | **failed** | **passed** |
| attribute key `event` → `attr_event` | failed | **failed** (`KeyError: 'event'`) |

The first disagreement is correct and worth keeping. proto3 JSON accepts both a
field's original snake_case proto name and its lowerCamelCase form, so
`severity_number` is a byte-level change with no semantic difference — exactly
what `telemetry.md` § 10.3 measured. The golden caught the drift; the round trip
correctly did not call it a defect.

## Surviving mutant — recorded, not hidden

Removing `O_NONBLOCK` from `source.open_input`'s leaf open passes the entire
suite. The `S_ISREG` check already refuses a FIFO that is a FIFO when examined,
so the flag only guards the race where a path is a regular file at `lstat` and a
FIFO at `open`. That needs two processes interleaved at one instruction, which no
deterministic test here reproduces. It is reasoned protection, not tested
protection, and the code says so at the line.

## Two tests that would have hung instead of failing

Both found by mutation, both fixed, both worth remembering: a hanging test
reports a CI timeout with no diagnosis.

- The `--follow` loop spun forever under a manually-advanced fake clock when a
  mutant stopped yielding a record. The clock now self-advances, so every follow
  loop reaches its deadline.
- Opening a FIFO with no writer blocks until one appears, so the FIFO refusal
  case hung. It is now bounded by `SIGALRM`.

## AC-0014 — the real console script, 2026-09-13

Every case above runs the installed wheel's `jsonl-otlp-export`, not the test
harness. That matters: every unit case injects `connection_factory`, so the real
one is exercised only here.

| Invocation | Observed |
| --- | --- |
| no endpoint in env or `--config` | exit 0, note on stderr, nothing sent |
| `OTEL_EXPORTER_OTLP_ENDPOINT` at a live Collector | exit 0, 3 records stored |
| `--nope` | exit 1, never 2 |
| `http://example.com:4318` | exit 1, `plaintext endpoint resolves to the non-loopback address 104.20.23.154` |
| `--best-effort` against a live Collector | exit 0 |
| every line unparseable | exit 1 |

The unmapped-severity report reached stderr in the shape the decision intended,
once per distinct value with a count rather than once per record:
`severity value 'wave-passed' is not in the profile's severity_map; 1 record(s)
sent without a severity`.

## A contract collision found in EXECUTE, and how it was resolved

AC-0033 ("no endpoint resolvable -> exit 0") and AC-0052 ("no `--profile` given
-> exit 1") are both unconditional, and they collide when neither is supplied.

The CLI resolves the endpoint first, so an unconfigured run exits 0 without
demanding a profile. Off-by-default is the Boundaries' first "Always do", and
AC-0052 exists to stop a *built-in* profile deciding the payload -- a question
that does not arise when nothing is being sent. Checking the profile first would
refuse a user who has not enabled sending at all.

Both criteria still hold in the cases they were written for: with an endpoint
configured and no profile, the run exits 1. **This is recorded as a contract
observation for the owner, not a silent choice**: if the intended reading is the
opposite, AC-0052 needs the words "when an endpoint resolves" and that is a
contract amendment, not a code change.

## Implementation review — two dispositions recorded for the owner

Both arise where a criterion states an obligation unconditionally but names no
disposition for the case that cannot satisfy it. The code takes a reading; if it
is the wrong one, the criterion needs words rather than the code needing a change.

**A record missing a declared `identity` field is skipped, not emitted.** AC-0023
says every emitted record carries its identity attributes, and a consumer
deduplicates on exactly those — so a record emitted without them is a row nothing
can deduplicate, which is worse than no row. This mirrors AC-0066's disposition
for a record with no usable timestamp: skip, report, continue. The alternatives
were refusing the profile and refusing the run.

**A single record whose encoded body alone exceeds 8 MiB is refused, not sent.**
AC-0019's first conjunct is unconditional — "a request body is at most 8 MiB
measured on the encoded bytes about to be sent" — and a one-record batch cannot
be split further. It is reported with its size rather than dropped in silence.
The earlier behaviour sent it, which violated the ceiling outright.

## What the implementation review cost, and what it bought

Three Codex reviewers with disjoint focus sets raised 29 findings; neutral
adjudication sustained 25 and refuted 3, with 1 indeterminate. That is a 10%
refutation rate against 73% across the five specification rounds — traced build
defects with concrete inputs do not evaporate under scrutiny the way readings of
prose do.

Fourteen production defects and six test defects, against a suite of 152 tests
that was green and had been mutation-proved at every step. The mutations proved
the paths I had thought of. `2026-02-30T00:00:00Z`, `{"result": []}`, a
zero-count `partialSuccess`, a lowercase `retry-after` — none of those inputs was
in my head when I wrote the tests, and each of the first two killed an entire run.

Two defects shared one shape: **a repair made on one side and never wired on the
other.** `render_endpoint` was made total while its caller kept raising; a
`run_started` parameter was added to fix the run-clock anchor and no caller ever
passed it, leaving the fix inert. Both passed every test.

One repair in this pass initially had no failing control of its own — the `--for`
deadline check survived being reverted. It now has a test driving 4,000 records
through full chunks so the reader never sees an empty read, which fails when the
check is removed.

## Second implementation review — the same lesson, four times

20 findings raised, 18 sustained, 2 refuted. **16 distinct defects.**

Round 2's central result is not any individual defect. It is that the shape
round 1 named — *a repair applied to one surface and not its sibling* — happened
three more times, twice in the round-1 repairs themselves and once inside this
round's own repair:

| Where | The surface that was missed |
| --- | --- |
| round-1 repair | `_attributes` handled the new `TOO_DEEP` sentinel; the identity loop twenty lines below it did not, so the sentinel was appended as a value and `json.dumps` ended the run |
| round-1 repair | the absolute request deadline was checked *between* reads, but `http.client` re-arms the socket timeout on every byte, so one blocking read still ran without limit |
| round-1 repair | `--for` was checked once per `os.read`, not while draining the buffer that read produced, so records already in hand were yielded past the deadline |
| round-2 repair | the containment `try` wrapped only the timestamp block, so an exception from the identity loop beside it still ended the run — caught by my own new test |

The generator-level answer is a containment floor around the **whole** per-record
body, not a wider net around one statement. Four of the sixteen defects were the
same class: an untrusted value reaching a standard-library call that raises —
a 4,301-digit decimal string (CPython's integer-conversion limit), ~16,000 levels
of nesting (`RecursionError`, and 40 KB, so inside the 64 KiB line ceiling),
`10**399` (`OverflowError` from `float()`), and bare `NaN`/`Infinity`, which
`json.loads` accepts and `json.dumps` writes back as non-JSON tokens.

## Two findings measured rather than accepted

- The recursion finding named depth 2,000. Measured: 2,000 and 5,000 parse fine;
  20,000 raises. The stated trigger was wrong and the defect is real, so it was
  sustained on the corrected threshold rather than on the reviewer's number.
- The "advisory" symlinked-`--root` finding was reproduced by a probe of mine
  within minutes of the adjudication: on macOS `/tmp` and `/var` are symlinks
  into `/private`, so comparing a resolved root against a lexical input refused
  an ordinary invocation. It is not advisory; it would have broken every macOS
  user passing an absolute `--input` under `/tmp`. Only the PARENT is resolved —
  resolving the leaf as well made a symlinked leaf resolve inside the root and be
  accepted, which the suite caught immediately.

## A disposition recorded for the owner

`--follow` with no `--for` never flushed a partial batch, so a record appended
after start was held until 512 arrived and AC-0021 was never satisfied. The
reader now signals that it has caught up and the batcher flushes what it holds.
**The idle trigger itself is unspecified by the contract** — the criterion says
the record must be sent without restarting the process, and says nothing about
when. If a different trigger is wanted, that is a criterion change.

## Third implementation review — converging, and one structural answer

13 findings raised, 8 sustained, 5 refuted. Refutation rose to 38% from 10% in
both earlier rounds, which is what convergence looks like: the remaining reports
are increasingly things the code already handles.

| Round | Raised | Sustained |
| --- | ---: | ---: |
| 1 | 29 | 25 |
| 2 | 20 | 18 |
| 3 | 13 | 8 |

**All three sustained surface findings were one rule, not three defects.** The
time bounds were per-operation while the contract asks for an absolute one: DNS
resolution was outside every deadline; connect, write and header read each got
the full socket timeout independently; and a `Connection: close` response sets
`connection.sock = None`, so the per-chunk re-arm was skipped entirely. Patching
three call sites would have been the partial-surface mistake for a fifth time.

The answer is one mechanism covering every blocking phase: a watchdog that tears
the connection down at the deadline, plus a bounded resolution on a daemon
thread. `socket.getaddrinfo` and `socket.create_connection` accept no timeout, so
nothing inside the call can be bounded — abandoning the thread is strictly better
than inheriting its stall.

**The watchdog's first version did not work, and my own test caught it.** Closing
a socket another thread is blocked reading does not wake it: the descriptor is
duplicated into the response's file object, so the blocked `recv` keeps waiting.
Measured — the request blocked for the full 120-second socket timeout despite a
one-second deadline. `shutdown(SHUT_RDWR)` before the close tears the connection
down underneath the reader and the call returns. The test drives a real socket
that accepts and then says nothing, with the socket timeout set deliberately far
larger than either bound, so anything finishing in time can only have been
stopped by the watchdog.

## A short read is a real defect with a stated reachability limit

`os.read` is one `read(2)` and may return fewer bytes than requested. A prefix of
a TOML file can itself be valid TOML, so a short read let an incomplete config or
profile be accepted as complete — and the profile decides what may be sent. Both
now compare the bytes read against the `fstat` size and refuse a mismatch.

Stated honestly: this is **not reachable for a local regular file** under the
64 KiB ceiling, and I could not force a short read locally. It is reachable on a
network or FUSE-backed file. The defect is real, the severity is low, and the
check is cheaper than the argument about whether it can happen.

## A second disposition recorded for the owner

`--service-name ''` now emits an empty `service.name` rather than falling back to
the profile stem. AC-0007 says the attribute takes the *value* of the flag and
names the stem as the *default*, so a supplied empty string is a value. The
opposite reading is defensible — `config._present` deliberately treats an empty
environment variable as absent — and the criterion does not decide between them.
If the fallback reading is wanted, AC-0007 needs the words.

## Fourth implementation review — and what mutation found that review did not

8 findings raised, 7 sustained, 1 refuted.

| Round | Raised | Sustained |
| --- | ---: | ---: |
| 1 | 29 | 25 |
| 2 | 20 | 18 |
| 3 | 13 | 8 |
| 4 | 8 | 7 |

The partial-surface pattern recurred a sixth time: `_resolve_bounded` was called
from the `http` branch and never from the `https` one, so a stalled resolver ran
past both bounds on TLS endpoints — and the watchdog cannot cover it, because
during `connect` there is no socket to shut down.

The refutation is worth recording as a result in itself. The real-socket watchdog
test was challenged as passing on connection *refusal* rather than on the
watchdog firing; it does not, because the listener is bound and listening in the
same process before the destination resolves, so the kernel completes the
handshake from the backlog whatever the accept thread is doing.

## Mutation caught three controls that review did not

After repairing, each repair was reverted in turn to see whether anything failed.
Three survived — they were controls that could not fail:

| Reverted | Why nothing caught it |
| --- | --- |
| the first-read anchor, at the CLI | the transport test supplies `first_read_at` itself, so it never covers the wiring |
| the watchdog's retained socket | the existing test uses a server that never answers, so the fallback lookup still finds a socket |
| the bounded `https` lookup | no test resolved an `https` host at all |

All three now have controls that fail when the behaviour is removed. **This is
the wiring class for the third time**: a keyword argument dropped at one call
site while the function it feeds is thoroughly tested on its own.

## A test that could not fail because it never ran

The new CLI control was appended at four-space indentation after a module-level
helper, which made it a nested function inside that helper rather than a method
on the test class. `--collect-only` showed zero matches: it was never collected,
so it passed the suite by not existing. Moved into its class, it now fails when
the wiring is dropped.

Worth stating plainly because the suite gives no signal for this: a test that is
never collected looks exactly like a test that passes.

## A mutation sweep over the pattern, rather than a fifth review round

Six times across four rounds, a rule was applied at one call site and not its
sibling. Rather than look for a seventh instance by reading, the sweep in
`packages/jsonl-otlp-exporter/tests/wiring_sweep.py` removes every cross-module
keyword argument in turn and runs the suite. Anything that still passes is a
wiring with no control behind it.

**Nine survivors and one hang, over 63 mutations.**

| Surface | Unprotected |
| --- | --- |
| `cli.py` | the TLS context, the socket timeout, `--follow`, the reader's `--for`, the run-clock anchor, the unmapped-severity report |
| `transport.py` | the request headers, `diagnostics=False` on a re-encode |
| `transport.py` | `daemon=True` on the watchdog timer — removing it makes the suite HANG rather than fail |

Two structural causes, not nine accidents. **Every CLI test injects its own
`connection_factory`**, so the real one — where the TLS context and the socket
timeout live — was never exercised by anything; and **no CLI test ever passed
`--follow`**. That is why AC-0024's chain-and-hostname verification had no
control on the shipped path after four review rounds looked at this code.

Two survivors were repairs made *during* those rounds: the run-clock anchor and
the double-counting suppression. Both landed correctly and neither had a control,
which is exactly how they could have regressed without anyone noticing.

## Writing the controls reproduced the same mistake twice

The first TLS control asserted `verify_mode == CERT_REQUIRED` on the returned
connection. That **cannot fail**: with `context=` dropped, `HTTPSConnection`
builds its own default context, which verifies too. It now asserts the
connection uses the exact object it was handed — identity, not properties.

And the first oversize control asserted a CLI behaviour that cannot happen.
AC-0018 caps a line at 64 KiB and AC-0019 caps a request at 8 MiB; even at a
worst-case six-byte escape per input byte, one record reaches ~388 KiB, about
twenty times under the ceiling. **The singleton-refusal branch is unreachable
through the command** — a dominated bound. The branch stays, because
`batch_records` is public and the transport suite covers it directly, but the
CLI test now pins the *relationship*: if the line ceiling rises or the body
ceiling falls far enough for one record to exceed a request, it fails and the
unreachability claim gets revisited rather than quietly becoming false.

## The sweep's own two failures, and what they cost

The first attempt printed results only after its loop, and one mutation made the
suite hang for the full 1800-second subprocess timeout and took the script down
with it: thirty minutes for no output. Results are now flushed per case, each run
is bounded at 90 seconds, and a hang is recorded as its own outcome. A suite that
hangs gives a developer no signal at all, which is the third time that hazard has
appeared in this package.

## Two corrections from outside this spec's own review rounds

Both were found by the session implementing `loop-telemetry-export`, after this
package had merged. Both are recorded here because this ledger exists to hold
what got through, and these got through everything.

### A gate that was never pointed at the code

**mypy had never checked this package.** `tools/lint-mypy.py` carries its own
`TYPED_PACKAGES` list and passes it as positional arguments, which override
`[tool.mypy] files` in `pyproject.toml`. At this package's merge commit that list
held only `agentbundle` and `credbroker` — and `[tool.mypy] files` had not been
touched either, so this was not an attempt that failed, it was an attempt never
made. Adding the package took the gate from 139 files to 146 and immediately
found a real defect: `source.py`'s reader is annotated
`Iterator[dict[str, Any]]` while yielding the `IDLE` sentinel that drives the
follow-mode flush. The annotation was simply never true.

What it survived: four implementation review rounds, the wiring sweep below, and
35 green CI checks.

**The sweep could not have caught it, and that is the useful part.**
`wiring_sweep.py` mutates keyword arguments at call sites and asks whether
anything notices. An annotation is not a call site, and a false annotation whose
runtime behaviour is correct changes no observable a test can assert on. The
instrument that would have caught it existed the whole time; it was pointed at
two packages and not at this one.

The repair walked three surfaces and the first two attempts were each partial, in
exactly the pattern this ledger already records six times: widening the
producer's return type moved the error to `cli.py`; widening that parameter moved
it inside `batch_records`; `record is IDLE` reads as correct to a human and does
not narrow a union for a type checker, even though the `continue` beneath makes
the code sound. `isinstance(record, _Idle)` narrows, and is equivalent here
because `_Idle` has exactly one instance.

Fixed in `e2d5c146b` on the `loop-telemetry-export` branch, as part of T4 putting
this package inside the repository's gates. Deliberately not duplicated on main:
the fix already exists on that branch, and a second copy would collide mid-wave.

### A count this spec reported wrongly throughout

**The suite is 279 tests, not 410.** `pytest --co` reports "279 tests collected".
The 410 figure appears in several commit messages on the merged branch and in the
original pull-request description; the description is corrected, the commit
messages are not rewritten. The number was mine and was repeated rather than
re-measured — the failure is not the first wrong reading but that nothing ever
re-derived it.

## Why this spec's engine run is left at CODE-IMPLEMENTATION

The run (`2bc90de4-…`) never reached DONE, and that is a deliberate stop rather
than an omission.

`loop-cohort schedule check-current` refuses:

```
plan.md no longer matches the scheduled baseline
stored='0e581ed5b99a…'  current='dc2c73bb1f9d…'
```

**The cause is this spec's own ADR renumbering, not the tool's suggested one.**
The message offers "pinned before canonical hashing landed"; the truth is more
specific and is visible in git. Three merge commits touched the locked `plan.md`
after the baseline was pinned — `fce136e17`, `ae1c8e21a`, `13415caf0` — and every
one of them changed the same sentence:

```
ADR-0111 -> ADR-0112 -> ADR-0114 -> ADR-0115
```

Upstream claimed this decision's ordinal five times, and each recovery edited a
plan that was already frozen. So the cost of an ordinal collision is not only the
renumber: **it invalidates a locked plan baseline**, and nothing warns you at the
time because the rename is a correctness fix that must happen.

The recovery is a cohort reset followed by `approve-plan`, which re-pins whatever
is on disk. That is a re-approval in substance, not a repair: it clears the retry
counters and the stasis baseline that four implementation review rounds produced.

Weighed against what completing the run buys — `engine-state.json` and
`state.json` are untracked, so DONE would be recorded in a local file that is
never committed and that lives in a worktree another session is building in —
the trade is bad. **Destroying a four-round audit trail to make an untracked
local file say DONE is not worth it.** This ledger is the tracked artifact and
the durable record, so the outcome is recorded here instead.

State as left: engine `CODE-IMPLEMENTATION`, last event `findings-remain`, four
implementation review rounds applied and merged as #1293, CI green at 35 checks.
The code shipped; only the state machine is unfinished.

Anyone resuming should re-derive the baseline deliberately rather than treating
the mismatch as corruption — and should NOT run `loop-engine reset`, because
`plan-locked` is legal only from `SPEC-PLAN-APPROVED` and the engine has no
state-setting verb, so resetting strands the run.

## The sweep's three behavioural survivors, triaged

A corrected sweep run by the `loop-telemetry-export` session produced 46
mutations: 30 caught, 1 hang (the already-documented `daemon=True`), 15
survivors. Twelve have no behaviour to control — argparse display text and two
`frozen=True` dataclasses. Three were behavioural, and they resolved three
different ways, which is the point worth keeping.

**`required=True` on `--input` — a missing control, now added.** Dropping it
still failed the run, but through whatever `open_input(None)` raises rather than
as a usage error. Right exit code, wrong observable, and nothing could tell the
two apart. Mutation-verified.

**`best_effort=args.best_effort` — not a missing control, a redundant path.**
`send_batches` already applies `best_effort` internally with exactly the same
scoping, and `cli._run` applied the rule a second time afterwards. Dropping the
wiring changed nothing because the second mask converted the failure anyway. The
repair is to delete the duplicate mask, not to test the wiring: **a control over a
redundant path pins the redundancy in place.** One rule, one site, and the
argument is now load-bearing. Mutation-verified.

**`on_oversize` — unreachable, and that is the answer.** AC-0018 caps a line at
64 KiB and AC-0019 caps a request at 8 MiB, so one record reaches about 388 KiB
worst case and a batch always splits down to records that fit. The
singleton-refusal branch cannot fire from the command.
`test_the_oversize_path_is_unreachable_through_the_cli` pins the RELATIONSHIP, so
if either ceiling moves the claim fails rather than quietly becoming false. No
control is possible and none should be written.

Three survivors, three different correct answers: add a control, delete the
redundancy, or record why no control can exist. A sweep that only ever produced
"add a test" would have been wrong twice out of three.

## What I asserted without checking

Three times in this work I stated something as established that I had not
verified, and the shape was identical each time: I checked the thing I was
thinking about, not the thing I was asserting.

- "410 tests" — repeated through commit messages and a pull-request description.
  The measured count is 279.
- "events.jsonl cannot see the retry counters" — `budgets` carries all four on
  every line; the bump emits no line of its own, which is a one-transition lag,
  not blindness.
- "a verification run is in flight" — it was wrapped in `timeout`, which does not
  exist on macOS, so it had failed instantly and I reported it as running.

Each was caught by someone else. The first two changed conclusions other people
were relying on; the third only wasted a message. None was caught by a test,
because none was the kind of claim a test covers.
