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
