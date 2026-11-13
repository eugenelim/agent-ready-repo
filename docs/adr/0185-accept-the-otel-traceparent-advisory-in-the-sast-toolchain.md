# ADR-0185: Accept the opentelemetry-api traceparent advisory in the SAST toolchain until Semgrep allows a fixed release

- **Status:** Accepted
- **Date:** 2026-11-13
- **Areas:** security, ci
- **Reversibility:** high
- **Decision-makers:** repository maintainers
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0131 (an advisory suppression is a governed allowlist entry), ADR-0133 (the `fixed_in` field), ADR-0147 (the sister tracestate advisory, same package and same shape), ADR-0113 (`gate-sast` owns the scan)

## Decision summary

- **Decision:** Accept CVE-2026-126360 in `opentelemetry-api` 1.37.0 as an entry in `tools/pip-audit-allowlist.toml`. The file's `allowed_packages` already names `opentelemetry-api`.
- **Because:** Every Semgrep release up to 1.185.0, the latest installed from `tools/requirements-sast.txt` on 2026-11-13, declares `opentelemetry-api~=1.37.0`, which excludes the fixed 1.45.2, so no pin or constraint here can reach it. The vulnerable parse runs on a `traceparent` value in a propagation carrier, and the one carrier Semgrep builds takes its value from two environment variables that `make sast` never sets.
- **Applies to:** the `opentelemetry-api` distribution that `tools/requirements-sast.txt` installs as a Semgrep dependency.
- **Tradeoff accepted:** the SCA leg reports one more advisory as accepted instead of blocking, until Semgrep permits `opentelemetry-api>=1.45.2`.

## Context

`gate-sast` began failing on every pull request when the feed published CVE-2026-126360 against `opentelemetry-api` below 1.45.2. The advisory is a regular-expression slowdown: `TraceContextTextMapPropagator.extract` takes quadratic time on a crafted `traceparent` value made of a trace-context prefix, a long run of whitespace and an embedded newline. It matters only where attacker-controlled input reaches that propagator through a carrier that keeps embedded newlines, such as a JSON field.

`opentelemetry-api` reaches this repository only through Semgrep, which `tools/requirements-sast.txt` installs for `make sast`. Semgrep declares `opentelemetry-api~=1.37.0`, so a direct pin to 1.45.2 makes the resolve unsatisfiable. The block hits every pull request and `main`, independent of their content.

## Decision

Add one `[[allow]]` entry for `CVE-2026-126360`, package `opentelemetry-api`, `fixed_in = "1.45.2"`, with the reachability finding below as its `reason` and the Semgrep release that permits `opentelemetry-api>=1.45.2` as `unblocked_when`.

### Reachability finding (verified 2026-11-13, against the installed Semgrep 1.185.0 and opentelemetry-api 1.37.0)

- The vulnerable function is `TraceContextTextMapPropagator.extract`, in `opentelemetry/trace/propagation/tracecontext.py`. It parses the `traceparent` value of whatever carrier it is given.
- Semgrep's only call to `propagate.extract` is `Telemetry.extract`, in `semgrep/telemetry.py`. It does not receive a carrier from any peer: it builds `{"traceparent": f"00-{trace_id}-{span_id}-{trace_flags:02x}"}` from the `SEMGREP_TRACE_PARENT_TRACE_ID` and `SEMGREP_TRACE_PARENT_SPAN_ID` environment variables, and runs only when both are set.
- `make sast` sets neither variable, and `tools/run-semgrep-gate.py` passes `--metrics off`. The gate runs Semgrep as a command-line scanner over local paths, starts no server and receives no message or header, so no inbound text reaches any propagator.
- The only other import of `opentelemetry.propagate.extract` in the installed closure is `opentelemetry/instrumentation/utils.py`, a helper that no code path of the scanner calls with a carrier. Nothing else in this repository imports `opentelemetry`.

## Consequences

- `gate-sast` passes again for every pull request and `main`.
- The gate reports the advisory as accepted on every run, so it stays visible.
- When Semgrep permits a fixed `opentelemetry-api`, `pip-audit` stops reporting this id and `tools/run-pip-audit-gate.py` exits 2 naming the retired entry, which forces its removal (ADR-0131's enforced retirement).
- Anyone who runs this toolchain's Semgrep with `SEMGREP_TRACE_PARENT_*` set to values they do not control is outside what this record accepts.

**Revisit if:** Semgrep starts extracting a propagation context it did not build, any tool here begins parsing inbound trace metadata, or another dependency brings `opentelemetry-api` into the audited closure.

## Confirmation

- **Mode:** enforced. The gate's retirement path runs on every scan; no part of it rests on a human remembering.
- **Signal:** `tools/run-pip-audit-gate.py tools/requirements-sast.txt` reports the advisory as accepted and blocks nothing; it exits 2 naming this entry once a Semgrep release lets `pip-audit` resolve a fixed `opentelemetry-api`. `tools/test-run-pip-audit-gate.py` covers that retirement path.
- **Owner:** eugenelim.

## Alternatives considered

- **Pin `opentelemetry-api>=1.45.2`.** Rejected: Semgrep's `~=1.37.0` makes the resolve unsatisfiable.
- **Raise the Semgrep floor.** Rejected: every release through 1.185.0 declares the same `~=1.37.0`.
- **Wait for a Semgrep release.** Rejected: the block stops every pull request in the meantime, and the vulnerable path is unreachable here.
- **Replace Semgrep in `make sast`.** Rejected as disproportionate to an advisory on a code path the gate never runs.
