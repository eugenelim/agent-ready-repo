# ADR-0147: Accept the opentelemetry-api tracestate advisory in the SAST toolchain until Semgrep allows a fixed release

- **Status:** Accepted
- **Date:** 2026-10-24
- **Areas:** security, ci
- **Reversibility:** high
- **Decision-makers:** repository maintainers
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0131 (an advisory suppression is a governed allowlist entry), ADR-0133 (the `fixed_in` field), ADR-0146 (the same shape for `mcp`), ADR-0113 (`gate-sast` owns the scan)

## Decision summary

- **Decision:** Accept CVE-2026-114603 (GHSA-xcq7-p3pf-p88h) in `opentelemetry-api` 1.37.0 as an entry in `tools/pip-audit-allowlist.toml`, and widen that file's `allowed_packages` to include `opentelemetry-api`.
- **Because:** Every Semgrep release up to 1.182.1, the latest on 2026-10-24, declares `opentelemetry-api~=1.37.0`, which excludes the fixed 1.45.1, so no pin or constraint here can reach it. The vulnerable parse runs only on a `tracestate` entry in a propagation carrier, and the one carrier Semgrep builds has no `tracestate` key.
- **Applies to:** the `opentelemetry-api` distribution that `tools/requirements-sast.txt` installs as a Semgrep dependency.
- **Tradeoff accepted:** the SCA leg reports one more advisory as accepted instead of blocking, until Semgrep permits `opentelemetry-api>=1.45.1`.

## Context

`gate-sast` began failing on 2026-10-23 when the feed published CVE-2026-114603 against `opentelemetry-api` below 1.45.1. The advisory is unbounded `tracestate` parsing: `TraceState.from_header` does not bound the header it is given, so a caller that passes an attacker-supplied `tracestate` can be made to consume memory and CPU without limit.

`opentelemetry-api` reaches this repository only through Semgrep, which `tools/requirements-sast.txt` installs for `make sast`. Semgrep declares `opentelemetry-api~=1.37.0`, so a direct pin to 1.45.1 makes the resolve unsatisfiable. The block hits every pull request and `main`, independent of their content.

## Decision

Add one `[[allow]]` entry for `CVE-2026-114603`, package `opentelemetry-api`, `fixed_in = "1.45.1"`, with the reachability finding below as its `reason` and the Semgrep release that permits `opentelemetry-api>=1.45.1` as `unblocked_when`. Widen `allowed_packages` to `["pyjwt", "mcp", "opentelemetry-api"]`; that list is the vehicle's bound, and widening it is the reviewed edit ADR-0131 requires.

### Reachability finding (verified 2026-10-24, against the installed Semgrep 1.182.1 and opentelemetry-api 1.37.0)

- The vulnerable function is `TraceState.from_header`, in `opentelemetry/trace/span.py`. Its only caller on the extract path is `TraceContextTextMapPropagator.extract`, in `opentelemetry/trace/propagation/tracecontext.py`, which calls it only when `getter.get(carrier, "tracestate")` returns a value. A carrier with no `tracestate` key leaves `tracestate = None` and the parse is never entered.
- Semgrep's only call to `propagate.extract` is `Telemetry.extract`, at `semgrep/telemetry.py`. It does not receive a carrier from any peer: it builds one, as `{"traceparent": f"00-{trace_id}-{span_id}-{trace_flags:02x}"}`, from the `SEMGREP_TRACE_PARENT_TRACE_ID` and `SEMGREP_TRACE_PARENT_SPAN_ID` environment variables. That dictionary has exactly one key and never a `tracestate`.
- The same call is guarded: it runs only when both of those variables are set. `make sast` sets neither, and `tools/run-semgrep-gate.py` passes `--metrics off`.
- `make sast` runs Semgrep as a command-line scanner over local paths. It starts no server and receives no HTTP request, so no inbound header reaches any propagator.
- Nothing else in this repository imports `opentelemetry`.

## Consequences

- `gate-sast` passes again for every pull request and `main`.
- The gate reports the advisory as accepted on every run, so it stays visible.
- When Semgrep permits a fixed `opentelemetry-api`, `pip-audit` stops reporting this id and `tools/run-pip-audit-gate.py` exits 2 naming the retired entry, which forces its removal (ADR-0131's enforced retirement).
- Anyone who runs this toolchain's Semgrep with `SEMGREP_TRACE_PARENT_*` set, against a trace context they do not control, is outside what this record accepts — though even then the carrier Semgrep builds carries no `tracestate`.

**Revisit if:** Semgrep starts extracting a propagation context it did not build, any tool here begins parsing inbound trace headers, or another dependency brings `opentelemetry-api` into the audited closure.

## Confirmation

- **Mode:** enforced. The gate's retirement path runs on every scan; no part of it rests on a human remembering.
- **Signal:** `tools/run-pip-audit-gate.py tools/requirements-sast.txt` reports the advisory as accepted and blocks nothing; it exits 2 naming this entry once a Semgrep release lets `pip-audit` resolve a fixed `opentelemetry-api`. `tools/test-run-pip-audit-gate.py` covers that retirement path.
- **Owner:** eugenelim.

## Alternatives considered

- **Pin `opentelemetry-api>=1.45.1`.** Rejected: Semgrep's `~=1.37.0` makes the resolve unsatisfiable.
- **Raise the Semgrep floor.** Rejected: every release through 1.182.1, the latest on 2026-10-24, declares the same `~=1.37.0`.
- **Wait for a Semgrep release.** Rejected: the block stops every pull request in the meantime, and the vulnerable path is unreachable here.
- **Replace Semgrep in `make sast`.** Rejected as disproportionate to an advisory on a code path the gate never runs.
