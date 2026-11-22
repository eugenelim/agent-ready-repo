# ADR-0186: Accept the mcp OAuth-client and wcmatch glob advisories in the SAST toolchain until Semgrep allows fixed releases

- **Status:** Accepted
- **Date:** 2026-11-22
- **Areas:** security, ci
- **Reversibility:** high
- **Decision-makers:** repository maintainers
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0131 (an advisory suppression is a governed allowlist entry), ADR-0133 (the `fixed_in` field), ADR-0146 and ADR-0149 (earlier `mcp` acceptances, same shape), ADR-0113 (`gate-sast` owns the scan)

## Decision summary

- **Decision:** Accept CVE-2026-115563 in `mcp` 1.29.0 and CVE-2026-132276 in `wcmatch` 8.5.2 as two entries in `tools/pip-audit-allowlist.toml`, and add `wcmatch` to its `allowed_packages`.
- **Because:** Every Semgrep release up to 1.186.0, the latest on 2026-11-22, declares `mcp==1.29.0` and `wcmatch~=8.3`, which exclude the fixed `mcp` 1.30.0 and `wcmatch` 11.2, so no pin or constraint here can reach them. The `mcp` advisory needs an MCP client, which `make sast` never builds. The `wcmatch` advisory needs a glob pattern with several `*` wildcards, and the only path pattern `make sast` passes matches crafted names in under a millisecond.
- **Applies to:** the `mcp` and `wcmatch` distributions that `tools/requirements-sast.txt` installs as Semgrep dependencies.
- **Tradeoff accepted:** the SCA leg reports two more advisories as accepted instead of blocking, until Semgrep permits the fixed releases.

## Context

`gate-sast` began failing on 2026-11-22 when the feed published two advisories:

- **CVE-2026-115563 (`mcp` below 1.30.0):** the OAuth client support (`mcp.client.auth`) lets the MCP server a client connects to choose where the client's OAuth credentials are sent.
- **CVE-2026-132276 (`wcmatch` below 11.2):** with default flags, a pattern holding several `*` wildcards takes polynomial time, O(n^k) for k wildcards, to reject a crafted file name.

Both reach this repository only through Semgrep, which `tools/requirements-sast.txt` installs for `make sast`. A direct pin to either fixed release makes the resolve unsatisfiable. The block hits every pull request and `main`, independent of their content.

## Decision

Add one `[[allow]]` entry per advisory with the reachability finding below as its `reason` and the Semgrep release that permits the fixed version as `unblocked_when`. Add `wcmatch` to `allowed_packages`, the file's reviewed bound.

### Reachability finding (verified 2026-11-22, against the installed Semgrep 1.186.0, mcp 1.29.0 and wcmatch 8.5.2)

- **mcp.** Semgrep imports `mcp` only from `mcp.server.*`, `mcp.shared.*` and `mcp.types`. No Semgrep module imports `mcp.client`, a client session or an OAuth client provider. `make sast` runs `tools/run-semgrep-gate.py` with `--config` flags and source paths, never `semgrep mcp`, and opens no MCP client. Nothing else in this repository imports `mcp`.
- **wcmatch.** Semgrep's `target_manager` calls `wcmatch.glob.globmatch(path, pattern, flags=GLOBSTAR | DOTGLOB)` for each include and exclude pattern against scanned paths, so file names in a scanned tree do reach it. The only path pattern `make sast` passes is `--exclude "tools/semgrep/fixtures/*/positive.py"`, which Semgrep matches as `**/tools/semgrep/fixtures/*/positive.py`, and no `.semgrepignore` exists. Measured: that pattern matches crafted names up to 250 bytes in at most 0.0006 s, while the advisory's own five-wildcard pattern takes 0.21 s on a 91-byte name with the same library, which confirms the advisory reproduces and the gate's pattern does not trigger it.

## Consequences

- `gate-sast` passes again for every pull request and `main`.
- The gate reports both advisories as accepted on every run, so they stay visible.
- When Semgrep permits a fixed release, `pip-audit` stops reporting the id and `tools/run-pip-audit-gate.py` exits 2 naming the retired entry, which forces its removal (ADR-0131's enforced retirement).
- Adding a Semgrep `--include` or `--exclude` pattern with several `*` wildcards, or a `.semgrepignore`, would bring the `wcmatch` advisory into reach.

**Revisit if:** `make sast` gains a path pattern with more than one `*` wildcard or a `.semgrepignore`, any tool here starts an MCP client, or another dependency brings `mcp` or `wcmatch` into the audited closure.

## Confirmation

- **Mode:** enforced. The gate's retirement path runs on every scan.
- **Signal:** `tools/run-pip-audit-gate.py tools/requirements-sast.txt` reports both advisories as accepted and blocks nothing, and exits 2 naming each entry once a Semgrep release lets `pip-audit` resolve a fixed version. `tools/test-run-pip-audit-gate.py` covers that retirement path.
- **Owner:** eugenelim.

## Alternatives considered

- **Pin `mcp>=1.30.0` or `wcmatch>=11.2`.** Rejected: Semgrep's pins make the resolve unsatisfiable.
- **Raise the Semgrep floor.** Rejected: every release through 1.186.0 declares the same pins.
- **Wait for a Semgrep release.** Rejected: the block stops every pull request in the meantime, and the paths are unreachable or measured harmless here.
