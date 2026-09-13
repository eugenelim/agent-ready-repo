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
