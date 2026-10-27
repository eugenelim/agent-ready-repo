# ADR-0149: Accept three mcp client and bearer-auth advisories in the SAST toolchain until Semgrep allows a fixed mcp

- **Status:** Accepted
- **Date:** 2026-10-27
- **Areas:** security, ci
- **Reversibility:** high
- **Decision-makers:** repository maintainers
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0131 (an advisory suppression is a governed allowlist entry), ADR-0133 (the `fixed_in` field), ADR-0146 (the first `mcp` entry and its premise), ADR-0113 (`gate-sast` owns the scan)

## Decision summary

- **Decision:** Accept CVE-2026-116684 (GHSA-w4fh-qvv9-3v23), CVE-2026-116685 (GHSA-5h93-6whr-6q8j) and CVE-2026-116686 (GHSA-rwrf-2pqf-9j8j) in `mcp` 1.29.0 as three entries in `tools/pip-audit-allowlist.toml`.
- **Because:** Every Semgrep release up to 1.182.1, the latest on 2026-10-27, declares `mcp==1.29.0` exactly, which excludes the fixed 1.30.0 and 2.2.0, so no pin or constraint here can reach them. Each vulnerable path belongs to an MCP client or to an MCP server's bearer authentication, and `make sast` runs neither.
- **Applies to:** the `mcp` distribution that `tools/requirements-sast.txt` installs as a Semgrep dependency.
- **Tradeoff accepted:** the SCA leg reports three more advisories as accepted instead of blocking, until Semgrep permits `mcp>=1.30.0`.

## Context

`gate-sast` began failing on 2026-10-27 when the feed published three advisories against `mcp` below 1.30.0:

- **CVE-2026-116684.** The SDK's server-side bearer authentication cannot check a token's audience, so a server whose authorization server also issues tokens for other services accepts those tokens too.
- **CVE-2026-116685.** The SDK's Streamable HTTP and SSE client transports, and its OAuth client providers, follow redirects to any origin, sending custom headers and, on 307 or 308, the request body there.
- **CVE-2026-116686.** The SDK's client validates a `call_tool` result against a server-declared `outputSchema` with a resolver that fetches any unresolved `$ref` URL or local file, synchronously and with no timeout.

`mcp` reaches this repository only through Semgrep. `allowed_packages` already includes `mcp` (ADR-0146), so the bound does not change. The block hits every pull request and `main`, independent of their content.

## Decision

Add one `[[allow]]` entry per advisory, package `mcp`, `fixed_in = "1.30.0"`, each with the part of the reachability finding below that carries it as its `reason`, and the Semgrep release that permits `mcp>=1.30.0` as `unblocked_when`.

### Reachability finding (verified 2026-10-27, against Semgrep 1.182.1 and mcp 1.29.0)

- Semgrep imports `mcp` only from `semgrep/mcp/` and `semgrep/commands/mcp.py`. `semgrep/cli.py` imports `semgrep_mcp` to register the `mcp` subcommand, so the module loads on every run, but its code runs only when that subcommand is invoked.
- **Bearer authentication (CVE-2026-116684).** Semgrep builds `AuthSettings` and a `TokenVerifier` only inside `setup_mcp_server`, in `semgrep/commands/mcp.py`, which only the `semgrep mcp` subcommand calls. No server is started, so no bearer token is checked.
- **Redirects (CVE-2026-116685).** The redirect-following HTTP client is `create_mcp_http_client`, in `mcp/shared/_httpx_utils.py`. Its users are the client transports, `mcp/client/streamable_http.py` and `mcp/client/sse.py`, and `mcp/client/session_group.py`. Semgrep imports nothing from `mcp.client`, and from `mcp.shared` it imports only `McpError` and `resource_url_from_server_url`.
- **Output-schema fetch (CVE-2026-116686).** The vulnerable validation is in the client, `mcp/client/session.py`. Semgrep never creates a `ClientSession` and never calls `call_tool`.
- `make sast` runs `tools/run-semgrep-gate.py` with `--config` flags, `--metrics off` and source paths. It never invokes `semgrep mcp`, starts no server, and acts as no MCP client.
- Nothing else in this repository imports `mcp`.

## Consequences

- `gate-sast` passes again for every pull request and `main`.
- The gate reports the three advisories as accepted on every run, so they stay visible.
- When Semgrep permits a fixed `mcp`, `pip-audit` stops reporting these ids and `tools/run-pip-audit-gate.py` exits 2 naming each retired entry, which forces its removal (ADR-0131's enforced retirement). The same release retires the ADR-0146 entry.
- Anyone who runs this toolchain's `semgrep mcp`, as a server or alongside an MCP client, is outside what this record accepts.

**Revisit if:** `make sast` or any tool here starts invoking `semgrep mcp`, Semgrep starts acting as an MCP client during a scan, or another dependency brings `mcp` into the audited closure.

## Confirmation

- **Mode:** enforced. The gate's retirement path runs on every scan; no part of it rests on a human remembering.
- **Signal:** `tools/run-pip-audit-gate.py tools/requirements-sast.txt` reports the advisories as accepted and blocks nothing; it exits 2 naming these entries once a Semgrep release lets `pip-audit` resolve a fixed `mcp`. `tools/test-run-pip-audit-gate.py` covers that retirement path.
- **Owner:** eugenelim.

## Alternatives considered

- **Pin `mcp>=1.30.0`.** Rejected: Semgrep's exact `mcp==1.29.0` makes the resolve unsatisfiable.
- **Raise the Semgrep floor.** Rejected: every release through 1.182.1, the latest on 2026-10-27, declares the same exact pin.
- **Wait for a Semgrep release.** Rejected: the block stops every pull request in the meantime, and none of the three paths is reachable here.
- **Replace Semgrep in `make sast`.** Rejected as disproportionate to advisories on code paths the gate never runs.
