# ADR-0146: Accept the mcp session-exhaustion advisory in the SAST toolchain until Semgrep allows a fixed mcp

- **Status:** Accepted
- **Date:** 2026-10-15
- **Areas:** security, ci
- **Reversibility:** high
- **Decision-makers:** repository maintainers
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0131 (an advisory suppression is a governed allowlist entry), ADR-0133 (the `fixed_in` field), ADR-0113 (`gate-sast` owns the scan)

## Decision summary

- **Decision:** Accept CVE-2026-59951 (GHSA-84m7-p3x7-pcfv) in `mcp` 1.29.0 as an entry in `tools/pip-audit-allowlist.toml`, and widen that file's `allowed_packages` from `pyjwt` to `pyjwt` and `mcp`.
- **Because:** Every Semgrep release, up to 1.181.0 (the latest on 2026-10-15), declares `mcp==1.29.0` exactly, so no pin or constraint in this repository can reach the fixed `mcp` 1.30.0. The vulnerable code serves MCP over Streamable HTTP, which `make sast` never starts.
- **Applies to:** the `mcp` distribution that `tools/requirements-sast.txt` installs as a Semgrep dependency.
- **Tradeoff accepted:** the SCA leg reports one known advisory as accepted instead of blocking, until Semgrep releases a version that permits `mcp>=1.30.0`.

## Context

`gate-sast` started failing on 2026-10-15 when the advisory feed published CVE-2026-59951 against `mcp` 1.8.0–1.29.1 (fixed in 1.30.0 and 2.2.0). The advisory is resource exhaustion: a Streamable HTTP server in stateful mode never reclaims session state, so a client that can reach the endpoint grows server memory without bound. It applies only to servers on that transport; stdio and SSE servers are not affected.

`mcp` reaches this repository only through Semgrep, which `tools/requirements-sast.txt` installs for `make sast`. Semgrep declares `mcp==1.29.0`, so a direct pin to 1.30.0 makes the resolve unsatisfiable. The block hits every pull request and `main`, independent of their content.

## Decision

Add one `[[allow]]` entry for `CVE-2026-59951`, package `mcp`, `fixed_in = "1.30.0"`, with the reachability finding below as its `reason` and the Semgrep release that permits `mcp>=1.30.0` as `unblocked_when`. Widen `allowed_packages` to `["pyjwt", "mcp"]`; that list is the vehicle's bound, and widening it is the reviewed edit ADR-0131 requires.

### Reachability finding (verified 2026-10-15)

- In Semgrep 1.175.0, the only importers of `FastMCP` and the Streamable HTTP transport are `semgrep/mcp/server.py` and `semgrep/commands/mcp.py`. `setup_mcp_server` builds the `FastMCP` object for any `semgrep mcp` run, and the Streamable HTTP endpoint is served only under `semgrep mcp --transport streamable-http`. The `semgrep mcp` subcommand is its only caller.
- `make sast` runs `tools/run-semgrep-gate.py --config p/python --config p/security-audit --config tools/semgrep/ --strict --error --quiet --metrics off …`, which executes `["semgrep", <those arguments>, --json-output=…]`. It never invokes `semgrep mcp` and starts no server, so the vulnerable session manager is never constructed.
- Nothing else in this repository imports `mcp`.

## Consequences

- `gate-sast` passes again for every pull request and `main`.
- The gate reports the advisory as accepted on every run, so it stays visible.
- When Semgrep permits a fixed `mcp`, `pip-audit` stops reporting this id and `tools/run-pip-audit-gate.py` exits 2 naming the retired entry, which forces its removal (ADR-0131's enforced retirement).
- Anyone who runs `semgrep mcp --transport streamable-http` from this toolchain is exposed; that is outside `make sast` and outside what this record accepts.

**Revisit if:** `make sast` or any tool in this repository starts invoking `semgrep mcp`, or another dependency brings in `mcp`'s Streamable HTTP server.

## Confirmation

- **Mode:** enforced. The gate's retirement path runs on every scan; no part of it rests on a human remembering.
- **Signal:** `tools/run-pip-audit-gate.py tools/requirements-sast.txt` reports the advisory as accepted and blocks nothing; it exits 2 naming this entry once a Semgrep release lets `pip-audit` resolve a fixed `mcp`. `tools/test-run-pip-audit-gate.py` covers that retirement path.
- **Owner:** eugenelim.

## Alternatives considered

- **Pin `mcp>=1.30.0`.** Rejected: Semgrep's exact `mcp==1.29.0` makes the resolve unsatisfiable.
- **Wait for a Semgrep release.** Rejected: the block stops every pull request in the meantime, and the vulnerable path is unreachable here.
- **Replace Semgrep in `make sast`.** Rejected as disproportionate to an advisory on a code path the gate never runs.
