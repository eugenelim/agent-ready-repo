# Ingest safety — the controls every fetch-and-land runs through

Grounded in the spec-stage security review of the catalogue-curation spec
(supply-chain, llm-agent, outbound-ssrf, path-and-file modules). These are
mechanical controls, not judgment — apply them every time.

## URL fetch — SSRF allowlist

A local path is read as-is (still write-jailed on land). A **URL** source:

- **Scheme allowlist:** `https` only for a raw file; `git`/`ssh` for a repo
  (`git clone` / `gh`). **Reject** `file:`, `ftp:`, `gopher:`, `data:`.
- **Host/range block:** reject any host resolving to a private, loopback,
  link-local, or cloud-metadata range — `169.254.0.0/16` (incl. `169.254.169.254`),
  `10.0.0.0/8`, `127.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`, `::1`, `fd00::/8`.
- **Redirects & rebinding (call-site, mandatory):** `ssrf_check.check_url`
  validates the *initial* URL only — it cannot see a 3xx redirect to a blocked
  host, nor a DNS-rebind between the check and the fetch (an inherent TOCTOU
  window). So the fetch itself **must disable redirects, or re-run `check_url` on
  every redirect target**, and pin/re-resolve the host at connect time. The
  scheme+range check is necessary, not sufficient — the call-site closes the gap.
- Prefer `git clone`/`gh` for repos — they avoid the raw-fetch `file://`-read
  pivot entirely.

There is no blessed SSRF-guarded fetch client in the catalogue to inherit (the
one existing fetcher reaches a constant host only), so this control is
implemented here, not assumed.

## Untrusted content — inspect raw before you trust

An assimilated **skill/agent** is instruction prose that projects into this
operator's and downstream users' agents (prompt-injection / memory-poisoning).
An assimilated **hook/script** is code that runs on git/session events. So:

- Show the **raw fetched body verbatim** for the operator to read — never
  reformat before the security judgment (reformatting can hide intent).
- **Code/hooks are a higher-scrutiny class** — require an explicit "land this
  code" confirm, distinct from prose. This confirm is also the **compensating
  control for the D6 guard's residual**: the engine/credbroker path-gate contains
  *changesets*, but a hook executes at session/commit time and could write a
  protected tree *before* a diff is gated — so an ingested hook is gated here, at
  ingest, not by the path-gate.

## Run the repo's own gates before landing

Ingestion never bypasses the gates the repo runs on its own code:

- **Lints** for the artifact kind: `lint-skill-spec`, `lint-agent-artifacts`.
- **SAST/SCA:** the repo's `.snyk` / dependency scan where runnable; CodeQL runs
  on the PR the change opens.
- A lint or scanner failure **blocks the landing** or is surfaced for an explicit
  confirm. Reuses existing tooling — no new scanner dependency.

## Write confinement — the blessed jail

Every write (assimilate *and* export) routes through the engine's
`agentbundle.safety.write_jailed` / `assert_under` — resolve the path, resolve
symlinks, verify it is under the allowed root, then write. A traversing/absolute
path or an in-source symlink cannot escape `packs/`. Never roll your own path
handling. Consuming this helper read-only is sanctioned reuse, not a D6 change.

## Residue

Fetched-but-rejected content lives in a named temp location and is purged on
completion — a single-primitive ingest from a client source leaves nothing
behind.
