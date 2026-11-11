# Telemetry backends

Send the lines to an OpenTelemetry Collector, never to a vendor endpoint, and
treat `run_id` as a search key, never a metric dimension. This page records what
was measured about backends and the OTLP encoding boundary for the lines
`jsonl-otlp-exporter` sends. What the lines hold, and why a pack cannot send
them, is in [telemetry](telemetry.md).

## 1. Which backends can search the attribute names

**Searching on the loop's attribute names works with no setup nearly
everywhere.** The table is a snapshot from vendor documentation dated
2026-09-10, not a maintained list. Confirm a row against the vendor's own docs
before relying on it.

| Backend | Search the loop's names, no setup | Note |
| --- | --- | --- |
| Dynatrace | Yes | DQL reads any attribute; OTLP over HTTP only, no gRPC |
| Splunk Observability Cloud | Yes | Raw traces yes; built-in breakdowns need a tag indexed first |
| Datadog | Yes | Live search is 15 minutes; older needs a retention filter |
| Elastic | Yes | Unmapped attributes land under `labels.*` |
| Azure Monitor | Yes | Reaches `customDimensions`; ingest needs a Collector and Entra auth |
| Google Cloud Trace | Stored | 1,024 attributes per span; UI filter reach not confirmed |
| ServiceNow Cloud Observability | Yes | Lightstep heritage, OTel-native |
| Honeycomb | Yes | No LLM-specific layer to fall outside of |
| Pydantic Logfire | Yes | OTel-native |
| Grafana Tempo | Yes | Dedicated columns are a speed-up, not a prerequisite |
| Jaeger | Yes | Exact match only; a Cassandra backend can be set to stop indexing tags |
| Chronosphere | Yes | Free to search; 1,000-series cap once made a metric |
| Sumo Logic | Yes | — |
| Coralogix | Yes | Mapping to its conventions recommended for built-in views |
| IBM Instana | Visible | Readable in a trace; not a first-class filter surface |
| AWS X-Ray | **No** | Metadata is not filterable; annotations are, capped at 50 per trace |
| Prometheus | **n/a** | Metrics only — not a sink for this shape |

Two things that do not move are worth writing down.

**Searching is cheap; aggregating is where cardinality costs.** Every platform
that charges or refuses does it at the same boundary — when an attribute
becomes a metric dimension, not when it is searched. Splunk runs a cardinality
check before indexing a tag.

Chronosphere caps a trace-derived metric at a
thousand series. Datadog bills custom metrics per name-and-value combination.
Prometheus advises keeping a metric's cardinality under ten.

**So `run_id` is a search key and never a dimension.** It differs on every run,
so its range has no bound. Finding one run by it is exactly its job.

Grouping
by it turns every run into its own series, which is the shape all four of those
limits exist to stop. Anything counting runs groups by spec, which is bounded.

**Prometheus is not a sink for this at all.** It stores numbered samples
against labels, with no model for an event or a bag of attributes — its OTLP
endpoint takes metrics only. These lines would have to become counts and
histograms first, losing the timestamps, the identifiers, and every attribute
not named as a dimension.

It also refuses a sample older than the newest in its
series, so replaying a recorded log is the case it least supports. It can hold
aggregates derived from these lines; that is a different job from storing them.

## 2. Getting these lines to a backend

The sender is `jsonl-otlp-exporter` ([telemetry § 2](telemetry.md#2-entrypoints)). This section records the measured
behavior of backends and of the OTLP encoding boundary, so an operator wiring up
a backend does not re-derive it. Measured 2026-09-12 unless stated.

### 2.1 Send to a Collector, never to a vendor endpoint

This is the decision everything else follows from. A Collector accepts
OTLP/HTTP with `Content-Type: application/json` on its `otlp` receiver with no
configuration, auto-detecting from the content type.

Vendors do not agree with
each other: Splunk's own OTLP endpoint requires `application/x-protobuf` and
answers JSON with **HTTP 415**, Elastic documents `proto` as its only encoding,
and Axiom refuses JSON on `/v1/metrics`. One Collector hop makes all of that
somebody else's problem and lets a sender speak one encoding.

Splunk's own documentation gives the same direction: *send to the Collector
you deployed* rather than to the backend, for one auth configuration point,
batching, and infrastructure metadata.

### 2.2 What a Splunk Observability team does next

Two facts decide the shape, and the second surprises people.

**These lines are logs, not spans.** They describe supervisor steps in time
order, which looks span-like, but nothing converts a file of events into
spans: the Collector's `filelog` receiver produces log records, the `transform`
processor cannot cross signal types, and the contrib request to add a
log-to-span path has been open since 2021 without an implementation.

**Splunk Observability Cloud does not store logs.** Logs live in Splunk
Platform — Enterprise or Cloud — and Log Observer Connect surfaces them inside
the Observability Cloud UI. So the route is:

```
work-loop → .loop-run/events.jsonl → sender (OTLP/HTTP JSON)
          → OTel Collector (otlp receiver)
          → splunk_hec exporter → Splunk Platform HEC
          → Log Observer Connect → visible beside APM
```

Concretely, the team needs: a Collector reachable from the developer machine or
CI runner; a Splunk Platform HEC token and endpoint on the `splunk_hec`
exporter; and Log Observer Connect configured if these should appear next to
APM traces. An Observability Cloud ingest token is **not** what this needs —
that is the trace/metric path.

Two Splunk-specific requirements:

- **Set `service.name`.** Splunk's GDI specification makes it a MUST; without it
  a service reads as `unknown_service`.
- **Do not index `run_id`.** Splunk APM runs a cardinality contribution analysis
  against your entitlement before permitting a tag to be indexed, and its own
  guidance is that high-cardinality ID tags belong in full-fidelity search
  instead. Unindexed attributes stay searchable in raw records; they just do not
  drive built-in breakdowns. This is § 1's rule, confirmed against the one
  vendor that enforces it at a documented gate.

### 2.3 The encoding boundary, measured

Run against `otel/opentelemetry-collector-contrib` with an `otlp` receiver and a
`debug` exporter, posting from `urllib.request`. A malformed OTLP payload is not silently discarded.

| Payload variant | HTTP | Record ingested |
| --- | --- | --- |
| Conformant | 200 | yes |
| `timeUnixNano` as a JSON number, not a quoted string | 200 | yes |
| `severity_number` — snake_case instead of lowerCamelCase | 200 | yes |
| Attribute `intValue` as a JSON number | 200 | yes |
| `traceId` base64-encoded instead of hex | **400** | no |
| `attributes` as a flat object instead of the `AnyValue` list | **400** | no |

**Structural errors fail loudly.** The two rejections returned HTTP 400 with a
parser message naming the offending byte. The receiver is tolerant exactly where
the specification says it must be — 64-bit integers are accepted as string or
number, and proto3 JSON accepts both the original field name and its
lowerCamelCase form.

So only two emission rules are load-bearing for acceptance: identifier fields
are **hex**, not base64, and attributes use the `AnyValue` wrapper list. The
remaining conventions are worth following for portability across receivers, but
a violation is not what breaks ingestion here.

What a 200 still cannot tell you is whether the data is *right*. A payload with
correct structure and wrong attribute names is accepted and stored — the failure
mode is wrong data, not absent data. That is what the round trip checks and a
response assertion cannot.

### 2.4 Two standing constraints on any sender

**Off is off.** Sending is a second, separate yes ([telemetry § 5.2](telemetry.md#52-export-is-a-separate-concern-and-it-is-off)) — but "off unless an
endpoint is configured" is a behaviour guarantee, not consent.

A capability the
adopter is never told about obtains no informed agreement either way. Any sender
ships with its documentation stating that the capability exists, what it
carries, and where it goes, while it sends nothing.

**The wire format is stable, not frozen.** OTLP/JSON has been stable since
`opentelemetry-proto` 0.20.0 (June 2023), and has still taken format-affecting
changes since — v1.10.0 carried breaking JSON changes.

Logs are the calmest
corner of it: the known breaks landed in metrics and in the experimental
profiles signal. This is why the event line carries a version.
