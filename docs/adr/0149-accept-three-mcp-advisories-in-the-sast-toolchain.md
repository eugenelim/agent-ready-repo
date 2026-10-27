# ADR-0149: Accept three mcp advisories in the SAST toolchain until Semgrep allows a fixed release

- **Status:** Accepted
- **Date:** 2026-10-27
- **Areas:** security, ci
- **Reversibility:** high
- **Decision-makers:** repository maintainers
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0131 (an advisory suppression is a governed allowlist entry), ADR-0133 (the `fixed_in` field), ADR-0146 (the first `mcp` acceptance, same shape), ADR-0147 (the same shape for `opentelemetry-api`), ADR-0113 (`gate-sast` owns the scan)

## Decision summary

- **Decision:** Accept CVE-2026-116684 (GHSA-w4fh-qvv9-3v23), CVE-2026-116685 (GHSA-5h93-6whr-6q8j), and CVE-2026-116686 (GHSA-rwrf-2pqf-9j8j) in `mcp` 1.29.0 as three entries in `tools/pip-audit-allowlist.toml`.
- **Because:** Every Semgrep release up to 1.182.1, the latest on 2026-10-27, declares `mcp==1.29.0`, which excludes the fixed 1.30.0, so no pin or constraint here can reach it. Each advisory needs an MCP server with bearer authentication or an MCP client, and `make sast` runs neither.
- **Applies to:** the `mcp` distribution that `tools/requirements-sast.txt` installs as a Semgrep dependency.
- **Tradeoff accepted:** the SCA leg reports three more advisories as accepted instead of blocking, until Semgrep permits `mcp>=1.30.0`.

## Context

`gate-sast` began failing on 2026-10-27 when the feed published three advisories against `mcp` below 1.30.0:

- **CVE-2026-116684:** the server-side bearer authentication cannot check a token's audience, so a token issued for another service is accepted.
- **CVE-2026-116685:** the Streamable HTTP and SSE client transports, and the OAuth client providers, follow cross-origin redirects carrying custom headers and, on a 307 or 308, the request body.
- **CVE-2026-116686:** the client validates `call_tool` results against a server's `outputSchema` with a resolver that fetches any unresolved `$ref` URL.

`mcp` reaches this repository only through Semgrep, which `tools/requirements-sast.txt` installs for `make sast`. Semgrep declares `mcp==1.29.0`, so a direct pin to 1.30.0 makes the resolve unsatisfiable. `allowed_packages` already includes `mcp` (ADR-0146). The block hits every pull request and `main`, independent of their content.

## Decision

Add one `[[allow]]` entry per advisory, package `mcp`, `fixed_in = "1.30.0"`, with the reachability finding below as its `reason` and the Semgrep release that permits `mcp>=1.30.0` as `unblocked_when`. `allowed_packages` is unchanged.

### Reachability finding (verified 2026-10-27, against the installed Semgrep 1.182.1 and mcp 1.29.0)

- Semgrep uses `mcp` only as a server. Its imports of `mcp` are in `semgrep/mcp/` and `semgrep/commands/mcp.py`: `FastMCP`, server types and errors, the server `TokenVerifier`, and `AuthSettings`. No module in Semgrep imports an MCP client session or the client transports, and none calls `call_tool`.
- CVE-2026-116684 is reached only through `AuthSettings` with a `token_verifier`. Semgrep builds both only in `setup_mcp_server`, in `semgrep/commands/mcp.py`, which runs only for the `semgrep mcp` subcommand.
- CVE-2026-116685 and CVE-2026-116686 are reached only from an MCP client, and Semgrep constructs none.
- `make sast` runs `tools/run-semgrep-gate.py`, which invokes Semgrep with `--config` flags and source paths. It never invokes `semgrep mcp`, starts no server, and opens no MCP client.
- Nothing else in this repository imports `mcp`.

## Consequences

- `gate-sast` passes again for every pull request and `main`.
- The gate reports the three advisories as accepted on every run, so they stay visible.
- When Semgrep permits a fixed `mcp`, `pip-audit` stops reporting these ids and `tools/run-pip-audit-gate.py` exits 2 naming each retired entry, which forces its removal (ADR-0131's enforced retirement).
- Anyone who runs this toolchain's `semgrep mcp` server with bearer authentication is outside what this record accepts.

**Revisit if:** `make sast` or any tool here begins invoking `semgrep mcp`, Semgrep starts using an MCP client, or another dependency brings `mcp` into the audited closure.

## Confirmation

- **Mode:** enforced. The gate's retirement path runs on every scan; no part of it rests on a human remembering.
- **Signal:** `tools/run-pip-audit-gate.py tools/requirements-sast.txt` reports the three advisories as accepted and blocks nothing. It exits 2 naming each entry once a Semgrep release lets `pip-audit` resolve a fixed `mcp`. `tools/test-run-pip-audit-gate.py` covers that retirement path.
- **Owner:** eugenelim.

## Alternatives considered

- **Pin `mcp>=1.30.0`.** Rejected: Semgrep's `mcp==1.29.0` makes the resolve unsatisfiable.
- **Raise the Semgrep floor.** Rejected: every release through 1.182.1, the latest on 2026-10-27, declares the same `mcp==1.29.0`.
- **Wait for a Semgrep release.** Rejected: the block stops every pull request in the meantime, and the vulnerable paths are unreachable here.
- **Replace Semgrep in `make sast`.** Rejected as disproportionate to advisories on code paths the gate never runs.
