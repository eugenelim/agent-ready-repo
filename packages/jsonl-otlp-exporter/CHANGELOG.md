# Changelog

All notable changes to `jsonl-otlp-exporter` are recorded here. This project
follows semantic versioning. While the version is 0.x the profile format is
provisional, and any change to it is called out under its release.

## 0.2.0 — unreleased

First release. The version moved from 0.1.0 before publication, so no release
carries the narrower configuration surface: `--user-config` and the closed
`[telemetry]` key set are part of the first published version rather than a
change to one.

### Added

- `jsonl-otlp-export`, a console script that reads a JSONL file and sends its
  records to an OpenTelemetry Collector as OTLP logs over HTTP/JSON.
- `--user-config`, a second TOML file declaring `[telemetry]`. The two
  configuration files merge per setting: `--config` wins for each setting it
  declares, and only a setting it omits falls through. A caller holding two
  configuration scopes no longer has to read them to decide which single file to
  pass, which is what previously made invoking this command require a package.
- `[telemetry]` admits exactly `endpoint` and `service_name`, and any other key
  is refused with the file it came from named. Both files are read on every run,
  whatever supplies the endpoint, so the refusal cannot be shadowed by an
  environment variable. A configuration file is also refused when the opened
  descriptor is a reparse point or has more than one link.
- `service.name` falls back to `[telemetry].service_name` from either file when
  `--service-name` is absent, before the `--profile` filename stem.
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
