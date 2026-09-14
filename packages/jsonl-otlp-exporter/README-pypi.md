# jsonl-otlp-exporter

Send JSONL records to an OpenTelemetry Collector as OTLP logs.

You point it at a file of one-JSON-object-per-line records and a profile that
says which field is the timestamp, which is the severity, and which fields may
leave the machine. It sends those records and nothing else.

Standard library only. No runtime dependencies.

```console
$ pip install jsonl-otlp-exporter
$ export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
$ jsonl-otlp-export --input events.jsonl --profile my-profile.toml
```

## What this sends

It reads the file you name with `--input` and sends its records to an
OpenTelemetry Collector as **OTLP logs** over HTTP, encoded as JSON.

**The tool sends nothing until an endpoint is configured.** With no endpoint set,
it writes one line to stderr saying so and exits 0. Configuring an endpoint is a
deliberate act, through one of three sources, in this order:

1. `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` — used exactly as given.
2. `OTEL_EXPORTER_OTLP_ENDPOINT` — `/v1/logs` is appended.
3. `[telemetry].endpoint` in the TOML file you pass to `--config` — `/v1/logs`
   is appended.

**What goes in the payload is decided by your profile, not by this tool.** A
field reaches the Collector only if the profile's `allowlist` names it, or if the
profile declares it as the timestamp, the severity, or part of the record
identity. Every other field in your input is dropped before the request is built.
There is no built-in profile: without `--profile` the command refuses to run
rather than guess what may be sent.

Where it goes is constrained too. `https` is accepted at any host with the
certificate chain and hostname verified. Plain `http` is accepted **only** when
every address the host resolves to is a loopback address — and the request is
then issued to that verified address, so a name that resolves differently a
moment later cannot redirect it. Redirects are never followed.

## Writing a profile

A profile is a small TOML file with six keys; it is read as data and never
imported or evaluated. The full guide, with a worked example you can copy, is
[`docs/profiles.md`](https://github.com/eugenelim/agent-ready-repo/blob/main/packages/jsonl-otlp-exporter/docs/profiles.md)
— an absolute link, because this page is rendered on PyPI where a relative one
does not resolve.

## Options

| Flag | Meaning |
| --- | --- |
| `--input PATH` | the JSONL file to read (required) |
| `--profile PATH` | the TOML profile (required; there is no default) |
| `--root DIR` | the directory `--input` and `--profile` must resolve inside; defaults to the working directory |
| `--config PATH` | TOML file declaring `[telemetry].endpoint` |
| `--service-name NAME` | `service.name` on the emitted records; defaults to the `--profile` filename stem |
| `--follow` | keep reading lines appended after start |
| `--for SECONDS` | end the run this many seconds after the first read |
| `--best-effort` | exit 0 even when sending fails |

## Exit codes

| Code | Meaning |
| ---: | --- |
| 0 | records sent; or no endpoint configured; or some lines invalid and the rest sent; or a send failure under `--best-effort` |
| 1 | unreadable or refused input; every line invalid; usage or configuration error; refused endpoint; send failure after the retry budget; or a non-empty `partialSuccess` |
| 130 | interrupted by SIGINT |

Codes 2 through 9 are never returned. They are left free so a calling program can
use that range for its own credential or authentication taxonomy without
colliding with this tool.

## Limits

Fixed, and chosen so a malformed or hostile input cannot make the tool
allocate or wait without bound.

| Limit | Value |
| --- | --- |
| Input line length | 64 KiB, measured before decoding |
| Records per request | 512 |
| Request body | 8 MiB, measured on the encoded bytes; larger batches are split, never dropped |
| Response body read | 1 MiB |
| Send attempts per run | 3 |
| `Retry-After` honoured up to | 30 seconds |
| Single request | 30 seconds |
| Whole run | 120 seconds |
| `--config` and `--profile` file size | 64 KiB each |

Records are processed as a stream: no run holds more than one batch in memory,
whatever the size of the input file.

## What it will not do

- Write anything. The input file is never modified, and no checkpoint, position
  file or other durable state is written — so restarting re-reads from the start.
- Follow an HTTP redirect.
- Send to a plaintext endpoint that is not loopback.
- Send a field your profile does not declare.
- Retry a request the receiver answered with a non-empty `partialSuccess`. Those
  records were refused on their content; sending them again produces the same
  refusal.

## Delivery semantics

Delivery is **at least once**. There is no checkpoint, so a run that fails partway
and is repeated will resend records the receiver already accepted. Declare the
fields that identify a record in your profile's `identity` so a consumer can
deduplicate on them.

## Compatibility

This project follows semantic versioning.

Note that the profile format is provisional while the version is 0.x: the
six-key shape may change in a minor release, and such a change will be called
out in the changelog. The command-line interface and the exit-code contract are
stable within a major version.
