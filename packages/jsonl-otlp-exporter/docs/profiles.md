# Writing a profile

A profile tells `jsonl-otlp-export` how to read *your* records: which field is
the timestamp, which is the severity, which fields identify a record, and which
fields may be sent at all.

It is a TOML file. It is read as **data** — parsed and validated, never imported
and never evaluated — so a profile cannot run code, and the worst a malformed one
can do is be refused.

There is no built-in profile. Without `--profile` the command refuses to run,
because guessing what may leave your machine is not a decision this tool will
make for you.

## A worked example

Suppose your input file holds lines like this:

```json
{"ts":"2026-03-04T11:22:33Z","level":"error","request_id":"abc123","attempt":2,"route":"/checkout","user_email":"someone@example.com","latency_ms":412}
```

This profile sends the timing, the severity, the identity and two useful
attributes — and leaves `user_email` behind:

```toml
timestamp_field = "ts"
timestamp_format = "rfc3339"
severity_field = "level"
identity = ["request_id", "attempt"]
allowlist = ["route", "latency_ms"]

[severity_map]
debug = 5
info = 9
warn = 13
error = 17
fatal = 21
```

`user_email` is in the input and not in the `allowlist`, so it appears nowhere in
the request. That is the point of the list: it is an allowlist, not a blocklist,
so a field added to your input later is dropped until you decide to send it.

## The six keys

A profile declares exactly these six, and nothing else. A missing key is refused,
and so is an extra one — an unrecognised key is almost always a typo, and
ignoring it would silently change what you send.

### `timestamp_field`

The name of the field holding the record's time. It becomes `timeUnixNano` and is
not also sent as an attribute.

### `timestamp_format`

How to read that field. One of exactly three values:

| Value | Accepts | Example |
| --- | --- | --- |
| `rfc3339` | a string with date, time and an **explicit offset**, with up to nine fractional digits | `2026-03-04T11:22:33.123456789Z` |
| `epoch-millis` | an integer, or a string of digits | `1772623353123` |
| `epoch-seconds` | an integer, or a string of digits | `1772623353` |

Two rules are worth knowing before you pick one.

**`rfc3339` requires the offset.** A timestamp with no offset is refused rather
than assumed to be UTC. Assuming costs up to fourteen hours of silent error, and
a wrong timestamp is worse than a missing record because it looks real.

**The epoch formats take integers only.** A value like `1772623353.5` is refused
rather than rounded, because a fractional seconds value cannot represent a
nanosecond instant exactly and the rounding would be invisible downstream.

A record whose timestamp is missing, inadmissible or out of range is skipped. Its
line number is reported on stderr and the rest of the file is still sent.

### `severity_field`

The name of the field holding the record's severity. Its value is looked up in
`severity_map`; the number goes to `severityNumber` and the original string to
`severityText`. It is not also sent as an attribute.

### `severity_map`

A table mapping each value you expect in `severity_field` to an OTLP severity
number. Numbers run **1 through 24** and a value outside that range is refused.
Zero is not allowed: it means `SEVERITY_NUMBER_UNSPECIFIED`, which a backend
cannot tell apart from a field that was never set.

The usual bands:

| Band | Numbers |
| --- | ---: |
| TRACE | 1–4 |
| DEBUG | 5–8 |
| INFO | 9–12 |
| WARN | 13–16 |
| ERROR | 17–20 |
| FATAL | 21–24 |

**You do not have to map every value.** A record whose severity is absent, null,
or not named in the map is still sent, with no severity attached. The run reports
each unmapped value once with a count. This is deliberate: severity is
enrichment, not identity, and dropping records because a new status appeared in
your logs would lose exactly the records you most want to see.

### `identity`

The list of fields that together identify a record. They are always sent, whether
or not `allowlist` names them.

Delivery is at least once and no position is checkpointed, so a repeated run can
resend records the receiver already has. These are the fields a consumer
deduplicates on — choose them so that two records with the same values really are
the same record.

### `allowlist`

The list of other fields that may be sent. Everything else in your input is
dropped before the request is built.

You do not need to list the timestamp, severity or identity fields here; they are
already routed. Listing them anyway is harmless and does not duplicate them.

## How your values are converted

Each allowlisted field becomes a log-record attribute, wrapped by JSON type:

| Your JSON | Emitted as |
| --- | --- |
| string | `stringValue` |
| `true` / `false` | `boolValue` |
| whole number inside 64-bit range | `intValue`, as a quoted string |
| any other number | `doubleValue` |
| array | `arrayValue`, members converted by these same rules |
| object | `kvlistValue`, members converted by these same rules |
| `null` | *nothing* — the key is absent from the record |

A `null` emits no attribute at all rather than an empty one, because an absent key
is something you can query for and an empty value is not.

Objects and arrays nest, up to **8 levels**. A value deeper than that is dropped
and reported once, so a pathological record cannot make the encoder walk without
limit.

## What makes a profile invalid

Any of these is refused before a single request is sent, and the command exits 1:

- a missing key, or a key that is not one of the six;
- `timestamp_field` or `severity_field` that is not a string;
- `identity` or `allowlist` that is not a list of strings;
- `severity_map` with a non-integer value, or a value outside 1–24;
- a `timestamp_format` other than the three listed above;
- a file over 64 KiB, or one that does not parse as TOML.

## Checking a profile

There is no separate validate command. Run the tool with no endpoint configured:
it loads and validates everything, sends nothing, and tells you what is wrong.

```console
$ unset OTEL_EXPORTER_OTLP_ENDPOINT OTEL_EXPORTER_OTLP_LOGS_ENDPOINT
$ jsonl-otlp-export --input events.jsonl --profile my-profile.toml
```
