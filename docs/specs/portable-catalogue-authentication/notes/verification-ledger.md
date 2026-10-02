# Verification ledger — portable-catalogue-authentication

Execution observations for run `4bf9c822-709f-45d8-9a79-b400a705f3a8`. The
approved `spec.md` and `plan.md` hold the obligations; this file holds what
execution observed against them.

## Stub verdicts

| Task | Stub test | Materialized at | Byte identity | Observed red |
| --- | --- | --- | --- | --- |
| T1 | `test_resolve_http_access_returns_public_anonymous_variant` | `packages/credbroker/tests/unit/test_http_access.py` | `cmp` against the plan block: identical | Collection error: `ImportError: cannot import name 'AnonymousHttpAccess' from 'credbroker'` |

## Real JFrog CLI contract (T4 grounding, 2026-10-02)

**Acquired build.** JFrog CLI 2.105.0, `jfrog-cli-mac-arm64`, from
`releases.jfrog.io/artifactory/jfrog-cli/v2-jf/2.105.0/`. SHA-256
`e205e50fe5a836a87addc2290cb92dd9ea73fdca5f64e43a630a59c201662647` matches the
vendor storage API's published checksum. `jf --version` printed
`jf version 2.105.0`. For comparison, 2.124.0 (the latest published build) was
acquired the same way, SHA-256
`2c1f05ef6ae8d4cabafe3732fe0df4d0bc7bb11bedcd48b0d0c128e477dda733`. Both live in
the session scratchpad only, never on `PATH` and never committed. The probes
used a disposable profile with the dummy token `disposable-canary-token-0001`
against a self-signed loopback HTTPS service on `127.0.0.1:18443`, run with the
closed environment `PATH=/usr/bin:/bin` and a scratch `HOME`.

**Discovery 1 — `jf config show --format=json` is present in 2.105.0.**
`jf config show --help` lists `--format` with `table, json`, and the command
exits 0 with a JSON array. That settles the ADR-0136 D8 floor outright. Each
profile object carries `url`, `artifactoryUrl`, `distributionUrl`, `xrayUrl`,
`missionControlUrl`, `pipelinesUrl`, `accessToken` (masked as `***`),
`serverId`, and `isDefault`. With no profile configured, it prints `[]`.

**Discovery 2 — no descendants hold the output pipe.** On both builds, a
`jf api` blocked on a slow response had no child processes (`pgrep -P` was
empty). `SIGTERM` stopped it in under 0.01 s with exit status -15, and stdout
reached EOF straight after the reap. Termination scoped to the direct child, as
AC-0013 states, is sufficient. No amendment is owed.

**Discovery 3 — argument order and delimiting.**
`jf api --server-id=<id> -- <endpoint>` works. After `--`, an option-like
endpoint is taken as a path: `-- --verbose` requested `GET /--verbose`. A
relative endpoint gets a leading `/`. `--server-id=nosuch` exits 1 with
`Server ID 'nosuch' does not exist.` on stderr. Before every request, `jf api`
also sends a preflight `GET /artifactory/api/system/version` carrying the
profile's credential.

**Discovery 4 — exit mapping.** For a 2xx response, the exit status is 0 and
stderr holds `[Info] Http Status: 200`. For a non-2xx response (404 or 401), the
exit status is 1, stdout still carries the response body, and stderr names the
status and the full request URL. A cross-origin redirect from `127.0.0.1` to
`localhost` was followed, and `jf` dropped the credential on the second hop.

**Discovery 5 — kill condition: stdout is not byte-faithful.** `jf api` appends
one `\n` to stdout when the response body does not already end in `\n`. Both
builds behave the same way:

| Response body | Bytes on stdout |
| --- | --- |
| 1,048,576 bytes ending in `0xff` | 1,048,577 bytes ending in `0xff 0x0a` |
| `abc\n` | `abc\n` (unchanged) |
| `abc\r\n\n` | `abc\r\n\n` (unchanged) |
| empty | `\n` |

A body that ends in `\n` cannot be told apart from one where `jf` added the
newline, so stdout alone cannot reproduce the response exactly. An archive
whose last byte is not `0x0a` therefore fails SHA-256 verification. The plan
names this outcome as the adapter design's kill condition: "reject the adapter
design if its arguments, output, or termination behavior differs from the
planned contract".

**Discovery 6 — `jf api` ignores jf's own trust store.** With the loopback CA in
`$HOME/.jfrog/security/certs/`, `jf rt ping` completed TLS, but `jf api` failed
with `x509: certificate signed by unknown authority` on both builds. Setting
`SSL_CERT_FILE` made no difference on macOS. The preflight version call did
trust the CA. A private or corporate CA therefore breaks `jf api` delegation
unless the system trust store already holds it. A loopback contract test cannot
complete TLS through `jf api` without `--insecure-tls`, which the adapter must
never pass.

**Discovery 7 — `--timeout` truncates silently.** With `--timeout=3` against a
response that stalls after 1 of 10 declared bytes, `jf api` exited 0 with
stdout `x\n`. The adapter's own deadline and kill must stay the timeout control.
`jf`'s `--timeout` must not be treated as a failure signal.

**Discovery 6 on Linux.** In a `python:3.11-slim` container (linux-arm64
2.105.0, SHA-256
`6a9f96e7ae2e3eda514efa310a7dd3ca1bb96d63be789124c5472250b51ef278`, verified
against the vendor checksum), `jf api` again ignored
`$HOME/.jfrog/security/certs/`, but honoured `SSL_CERT_FILE` and returned
`abc\n` with `Http Status: 200`. The 1 MiB binary body again came back as
1,048,577 bytes. Owner decision 5 had excluded `SSL_CERT_FILE` and
`SSL_CERT_DIR` because no environment variable configures a CA for `jf`. That
premise is false for `jf api` on Linux.

## Owner decisions taken during EXECUTE

Taken by the spec owner (eugenelim) on 2026-10-02, after reviewing Discoveries
5 and 6. These are the owner authority for the controlled amendment of T4.

- **OD-1 — digest-checked trim on the JFrog path.** Keep `jf api`. For a
  JFrog-delegated archive, accept the bytes when they match the expected
  SHA-256 exactly, or when they match after removing exactly one trailing
  `0x0a`. The JSON descriptor needs no trim. The direct HTTP path keeps exact
  verification.
- **OD-2 — carry `SSL_CERT_FILE` and `SSL_CERT_DIR`.** Add both to the
  child-environment allowlist so a corporate CA reaches `jf api` on Linux.
  Record macOS, where `jf api` reads only the system keychain, as a stated
  residual. Run the real-CLI contract test and AC-0018's JFrog leg in a Linux
  container, where a loopback CA is trusted without touching the host.

## Discoveries

- **ASCII-only lowercasing is observably equivalent to `str.lower()` here.**
  The T1 resolver now lowercases only ASCII before the IDNA codec and reads the
  host from the netloc, because `urlsplit(...).hostname` applies `str.lower()`.
  An exhaustive sweep of U+0080–U+2FFFF found 0 code points where
  `("x" + c + ".example").lower().encode("idna")` differs from the codec
  applied to the raw host, since IDNA2003 nameprep case-folds the same way. The
  change aligns the code with the `Agent Rules` wording. No mutation can make
  the new test red, so the test pins the invariant itself: the compared form
  equals the codec form of the host as written.
- **Provider class strings.** The result variants expose `bearer`, `jfrog`,
  `netrc`, and `anonymous`. `HttpAccessError.provider` adds `target`. The
  architecture prose writes the `.netrc` class as `.netrc`; the code uses
  `netrc` so the value is a plain identifier.
- **Every target refusal uses `invalid_target_host`.** The closed code set has
  one target code, so a non-HTTPS scheme, user information, a missing host, a
  malformed port, and an unencodable host all raise
  `HttpAccessError("target", "invalid_target_host")`.
- **The `credential-brokers` pack moves to 0.3.4.** The vendored user library
  is `.apm/**` content, and `packs/AGENTS.md` requires a patch bump for changed
  content in `pack.toml` and `.claude-plugin/plugin.json`.

- **The vendored user-library floor is a drift-gated projection.**
  `packages/agentbundle/agentbundle/build/user_libs.py` projects
  `packages/credbroker/credbroker/` byte-faithfully into
  `packs/credential-brokers/.apm/user-libs/credbroker/` and
  `.agentbundle/lib/credbroker/`, and `make build-check` fails on drift. Any
  credbroker source change therefore regenerates both copies through
  `make build-self`, so the committed floor moves to 0.7 with this change. The
  AC-0003 co-location test cannot read its 0.6 floor from the committed tree.
  It reads the 0.6 package source from the `credbroker-v0.6.0` tag instead; the
  roster job checks out with `fetch-depth: 0`, so the tag is reachable in CI.
