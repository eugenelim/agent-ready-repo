# Changelog

All notable changes to `jsonl-otlp-exporter` are recorded here. This project
follows semantic versioning. While the version is 0.x the profile format is
provisional, and any change to it is called out under its release.

## 0.1.0 — unreleased

First release.

### Added

- `jsonl-otlp-export`, a console script that reads a JSONL file and sends its
  records to an OpenTelemetry Collector as OTLP logs over HTTP/JSON.
- Declarative profiles: a TOML file names the timestamp field and its format,
  the severity field and its mapping, the record identity, and an allowlist of
  fields that may be sent. Profiles are read as data, never imported or
  evaluated, and none is bundled — without `--profile` the command refuses to
  run rather than guess what may be sent.
- Resumable runs. `--report-cursor` prints an opaque one-line JSON cursor on
  stdout; `--from-cursor` takes it back and resumes from it, so a repeated run
  sends only what is new. The cursor pairs the byte offset with the input's
  device and inode, so a rotated or truncated file resets to the start instead
  of seeking into the middle of a record, and an offset that does not land on a
  record boundary is refused. The caller stores the cursor between runs: this
  command still writes no durable state of its own.
- Off by default. With no endpoint resolvable from the two `OTEL_EXPORTER_*`
  variables or `--config`, the command says so on stderr and exits 0 without
  opening a socket.
- Destination policy: `https` at any host with the chain and hostname verified;
  plaintext only when every resolved address is loopback, with the request
  issued to the verified address rather than re-resolving the name. Redirects
  are never followed, and an endpoint carrying user-info is refused.
- Bounded everywhere: 64 KiB per input line, 512 records and 8 MiB per request,
  1 MiB of response read, three send attempts per run, 30 seconds per request
  and 120 seconds per run, all on a monotonic clock.
- Streaming: no run holds more than one batch resident, whatever the input size.
- An exit-code contract of exactly 0, 1 and 130, leaving 2 through 9 free for a
  calling program's own credential taxonomy.

### Known limitations

- Delivery is at least once. No position is checkpointed, so a repeated run
  resends records the receiver already accepted; deduplicate on the fields named
  in the profile's `identity`.
- Authenticated endpoints are not supported. The target is a Collector you run,
  which is why plaintext is confined to loopback.
