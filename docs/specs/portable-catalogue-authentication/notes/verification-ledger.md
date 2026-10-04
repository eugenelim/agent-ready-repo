# Verification ledger — portable-catalogue-authentication

Execution observations for run `4bf9c822-709f-45d8-9a79-b400a705f3a8`. The
approved `spec.md` and `plan.md` hold the obligations; this file holds what
execution observed against them.

## Stub verdicts

| Task | Stub test | Materialized at | Byte identity | Observed red |
| --- | --- | --- | --- | --- |
| T1 | `test_resolve_http_access_returns_public_anonymous_variant` | `packages/credbroker/tests/unit/test_http_access.py` | `cmp` against the plan block: identical | Collection error: `ImportError: cannot import name 'AnonymousHttpAccess' from 'credbroker'` |
| T2 | `test_open_fetch_session_resolves_anonymous_access_once` | `packages/agentbundle/tests/unit/test_catalogue_fetch.py` | `cmp` against the plan block: identical | Collection error: `ModuleNotFoundError: No module named 'agentbundle.catalogue_fetch'` |
| T3 | `test_netrc_exact_host_returns_origin_bound_access` | `packages/credbroker/tests/unit/test_http_access_netrc.py` | `cmp` against the plan block: identical | Assertion failure, not the planned collection error: `isinstance(AnonymousHttpAccess(origin='https://catalogue.example.test'), NetrcHttpAccess)` is `False` |
| T4 | `test_jfrog_longest_profile_returns_pinned_binding` | `packages/credbroker/tests/unit/test_http_access_jfrog.py` | `cmp` against the plan block: identical | Assertion failure, not the planned collection error: `isinstance(AnonymousHttpAccess(origin='https://platform.example.test'), JfrogCliHttpAccess)` is `False` |

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
exits 0 with a JSON array. That settles the ADR-0137 D8 floor outright. Each
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

**Contract test result (T4 Done when).** At commit `0e9bf4b72`,
`packages/agentbundle/tests/integration/test_jfrog_cli_contract.py` ran
against the official linux-arm64 JFrog CLI 2.105.0 inside a disposable
`python:3.11-slim` container. The loopback CA was supplied through
`SSL_CERT_FILE` and the profile carried only the dummy token. Result: 6 passed
in 6.36 s. The six tests prove:
- discovery pins the profile's server ID and both base URLs;
- descriptor stdout is the body plus exactly the one appended newline, and the
  loopback host received the profile's bearer header from `jf`, never from
  AgentBundle;
- a full `catalogue+https://` acquisition verifies and extracts a binary
  archive whose last byte is not `0x0a`;
- a 404 maps to `jfrog_fetch_failed`;
- a stalled response ends in `jfrog_fetch_timeout` within the 4 s deadline
  plus 1 s, with no live `jf api` process left;
- the token, the server ID, the `Http Status` stderr line, and the request URL
  never appear in the raised error or the DEBUG log.

In the same container run, the JFrog, `.netrc`, and fetch-session unit suites
passed alongside it: 161 passed, 1 Windows-only skip, in 15.38 s. The adapter
design passes its kill condition under the amended contract.

**Built-CLI JFrog leg (AC-0018).** At commit `98b9a76f6`,
`test_built_cli_installs_through_a_jfrog_cli_profile` in
`tests/roster/test_portable_catalogue_authentication_packaging.py` ran in the
same disposable Linux container against JFrog CLI 2.105.0. It builds both
wheels, installs AgentBundle into a clean Python 3.11 venv from those wheels
alone, writes a disposable profile with a dummy token, and runs the installed
`agentbundle install --pack test-pack --output <dir> catalogue+https://…`
console script. Result: 1 passed in 7.16 s. The CLI exited 0 and wrote its
state file. Both catalogue requests reached the loopback host with the
profile's bearer header from `jf`. The token and profile name appear in
neither the CLI output nor the state file. The anonymous and exact-machine
`.netrc` legs of the same module ran on the macOS host with a generated
loopback CA: 14 passed with the JFrog leg skipped, in 104 s.

## Documentation checks (AC-0019, 2026-10-03)

Run at commit `3d69a95fc`, after the review round's guide repairs. The checks first ran at `e525ae024`, which was amended into `3d69a95fc`; the two differ only in the two regenerated credbroker copies under `.agentbundle/lib/` and `packs/credential-brokers/.apm/user-libs/`, which no documentation check reads:

- `python3 tools/build-site.py` exited 0 (`build-site: done.`).
  `tools/validate_guides.py` (235 checked), `tools/check-guide-index.py`
  (22 packs), `tools/lint-guide-titles.py` (241 files), and
  `tools/catalogue/sync_authoring_scaffold.py --check` each exited 0.
- Stale-claim search, exit 0 with one hit:
  `grep -rniE "only (supports|path|way|through).*bearer|bearer.*(only|sole)|does not currently reuse|AGENTBUNDLE_HTTP_BEARER_TOKEN alone|empty (bearer )?token|set but empty"`
  over `guides`, `docs/guides`, both packages' `README.md` and
  `README-pypi.md`, `packages/agentbundle/DESIGN.md`, and the packaged
  scaffold guides. The only hit is
  `guides/credential-brokers/how-to/add-a-credentialed-skill.md:19`, which
  says skills may call services that take "Bearer auth". It is not a claim
  about catalogue authentication.
- JFrog CLI 2.105.0 setup is named in all five setup surfaces: the adopter
  how-to, the adopter reference, the maintainer how-to, and both AgentBundle
  READMEs.
- Credential-example search over the lines this feature added to those files
  (`git diff -U0 7a4d62ff7^ -- <files> | grep '^+'`), for `Bearer`/`Basic`
  followed by a literal value, `password <value>`, `token=<value>`, JWT,
  AWS-key, and GitHub-token shapes: zero matches (grep exit 1). Every
  credential mention is a variable name or a `<token>`, `<user>`, or `<host>`
  placeholder.

## Review round 2 repair evidence (2026-10-03)

At commit `3d69a95fc` (the same tree as the run's `e525ae024` apart from the regenerated credbroker copies, which the container suites import from `packages/credbroker/` rather than from those copies) the same disposable Linux container ran the real JFrog
CLI 2.105.0 contract suite, the JFrog, `.netrc`, and fetch-session unit
suites, the provider-matrix integration suite, and the built-CLI JFrog leg:
209 passed, 1 Windows-only skip, in 24.06 s. On the macOS host: credbroker
658 passed (105 s); the full AgentBundle package suite 5,531 passed, 57
skipped, 1 xfailed (13 min 23 s); the packaging roster 14 passed with the
JFrog leg skipped for its stated reason (67 s).

## Review round 3 repair evidence (2026-10-04)

At commit `c50ed9428` (projections included):

- **Mutation proofs, run by the controller.** For each repaired control, the
  production line was changed in place, the target tests were run, and the
  file was restored byte-for-byte; the working tree was unchanged afterwards.
  All 13 mutations turned their tests red:
  - removing `HTTPDefaultErrorHandler` (non-2xx responses);
  - skipping the decoded-segment check (`..%20`, `..%09`, `..%00`);
  - passing the whole env to the `jf api` child;
  - importing `catalogue_fetch` from `catalogue.py` (local resolution
    without the resolver modules);
  - adding a bearer `os.getenv` read to `system_trust.py`, and a `netrc`
    import to `catalogue.py` (whole-tree boundary);
  - letting `.netrc` precede JFrog (all eight provider combinations);
  - removing the post-EOF stderr re-check in each package;
  - ignoring the cap-breach event in each package (the stdout-open tests
    exceeded their 5 s bound);
  - leaving the archive temp file after success;
  - removing the delegated-timeout cap.
- **Runs.** credbroker with AgentBundle blocked from import: 660 passed, 1
  skipped (94 s). Full AgentBundle package suite: 5,560 passed, 56 skipped, 1
  xfailed (13 min 23 s). Packaging roster: 16 passed, JFrog leg skipped for
  its stated reason (57 s). Disposable Linux container with JFrog CLI 2.105.0
  (real-CLI contract, JFrog, `.netrc`, fetch-session, provider-matrix suites,
  and the built-CLI JFrog leg): 236 passed, 1 Windows-only skip (25 s). The
  documentation build and guide checks each exited 0.
- **Expired fixture certificate.** The first container run at this commit
  failed four JFrog tests. Real `jf api` stderr showed
  `x509: certificate has expired or is not yet valid`: the disposable loopback
  certificate made on 2026-10-01 had 2-day validity and expired at
  2026-10-04 04:55 UTC. A fresh throwaway certificate (30 days) passed the
  same suites unchanged. The code did not regress.
- **Termination scope kept.** The repair implementer had switched both
  bounded runners to process-group termination. That contradicts AC-0013's
  direct-child scope and owner decision 4, so the controller reverted it. The
  stuck-reader case the change targeted is handled instead by reaping the
  direct child within its grace and joining reader threads for at most
  0.2 s.

## Review round 4 repair evidence (2026-10-04)

At commit `d99affa10` (build-self changed no projections):

- **Mutation proofs, run by the controller.** Each line was changed in
  place, the target test was run, and the file was restored byte-for-byte.
  All 7 mutations turned their tests red:
  - calling the HTTP access resolver from the Git transport;
  - importing `credbroker._http_access` from the Git transport (clean
    interpreter check);
  - copying the `[jf_path, "api", ...]` invocation into `system_trust.py`;
  - removing the appended-required-parameter rule from the shared AC-0003
    signature comparison;
  - removing the direct opener's redirect handler (real same-origin 302,
    then 401);
  - dropping the `%`-after-decoding check (`%252e%252e`,
    `%25%32%65%25%32%65`);
  - dropping strict UTF-8 decoding (`%c0%ae%c0%ae`).
- **Runs.** credbroker with AgentBundle blocked from import: 660 passed, 1
  skipped (59 s). Full AgentBundle package suite: 5,564 passed, 57 skipped,
  1 xfailed (15 min 7 s). Packaging roster: 16 passed, JFrog leg skipped
  for its stated reason (80 s). Disposable Linux container with JFrog CLI
  2.105.0 (same suites as round 3): 240 passed, 1 Windows-only skip (25 s).
  The sdist gate: 84 passed (12 min 18 s). Lint, the documentation build,
  and guide checks each exited 0.

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

## ADR renumbering on merge (2026-10-04)

Updating the branch from `main` brought in ADR-0134 (intent rename), which
was accepted first. This feature's four ADRs moved from 0134–0137 to
0135–0138, unchanged except for their numbers, and every reference in this
feature's spec, plan, ledger, changelog, and tests moved with them. Commits
made before the move cite the old numbers in their `Engine-Change-RFC`
trailers.

## Discoveries

- **The T3 and T4 stubs earn a behavioural red, not a collection red.** The
  plan names each stub's intended red as `NetrcHttpAccess` (T3) or
  `JfrogCliHttpAccess` (T4) "not exported". T1's approved Done-when requires
  all six names, including all four result variants, so that import succeeds
  once T1 lands. Each stub still fails for the reason it exists to prove: the
  resolver returns `AnonymousHttpAccess` because the provider is a placeholder.
  The ledger records the observed red for each.

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
- **T2 deviation — the corpus is re-pointed, not byte-unchanged.** T2's
  Tests row says the current HTTPS corpus runs "unchanged through the facade".
  `test_https_catalogue.py` unit-tested five private transport helpers
  (`_build_opener`, `_make_request`, `_OriginLockingRedirectHandler`,
  `_fetch_bytes_limited`, `_stream_and_verify`) and patched three of them as
  seams in its end-to-end tests. One test, `test_bearer_token_passed_to_opener`,
  asserted that the raw token reached `_build_opener`. Keeping those seams
  would have meant either two transport implementations, or AgentBundle
  stripping `Bearer ` from the credbroker result to rebuild the old opener,
  which also cannot carry the `.netrc` Basic header. The transport now lives
  once, in `catalogue_fetch/direct_http.py`. Every corpus test keeps its name
  and behavioural assertion. Helper tests call the `direct_http` equivalents.
  End-to-end tests patch `FetchSession.fetch_bytes` and
  `FetchSession.fetch_archive`. The bearer test now asserts that the descriptor
  request carries `Authorization: Bearer my-secret-token` to the bound origin.
  The count is 99 before and 99 after. AC-0005's obligation (same accepted
  bytes, redirects, errors, and provenance) is unchanged.
- **Local AgentBundle suites need the documented `PYTHONPATH`.**
  `packages/agentbundle/pyproject.toml` shadows the root pytest
  configuration with `pythonpath = ["."]`, so `pytest packages/agentbundle/tests`
  imports whichever `credbroker` is installed in site-packages. Run it with
  `PYTHONPATH=packages/agentbundle:packages/credbroker`. CI is unaffected
  because `gate-main` and `gate-export-boundary` install this checkout's
  `credbroker` in editable mode. During T2, a subagent ran
  `pip install -e packages/credbroker` into the host's global Python, which
  breaks the no-install rule. The owner chose to restore the previous editable
  0.6.0 install from the main checkout, and it was restored on 2026-10-02.
- **The approved T3 stub fails ruff's import-order rule.** Its import block
  is not sorted the way the repository's isort configuration expects, so
  `test_http_access_netrc.py` carries one `# ruff: noqa: I001` line above the
  stub. The stub's own bytes are unchanged.
- **The `.netrc` lookup compares against the normalized origin's host as
  written.** Taking the host through `urlsplit(...).hostname` drops IPv6
  brackets while the normalized machine keys keep them, so a bracketed IPv6
  record never matched. `test_netrc_matches_ipv6_literal_with_port` pins the
  fix.
- **Review round 1 is a late-caught gate failure, not a reviewer finding.**
  After T5, the sdist gate (`tools/test_check_artifact_contents.py`) reported
  `1 failed, 82 passed`, but the controller read the exit status of a `tail`
  filter and fired `gates-clean` (engine seq 33). The failure was the
  explicit skip policy refusing the JFrog contract suite's environment-gated
  skip. The run returned through `wave reopen` and `findings-remain` (seq 34),
  whose required fingerprint is the SHA-256 of the saved gate log,
  `5e97e24a9091e2689ca9ac1b9828049d4b5f5a9007630f4b4d381d58c88857db`.
  The cohort therefore counts one review round that no reviewer produced. The
  repair registers the suite's exact skip message, following the precedent of
  the load-conditional entry, and adds it to the gate's own policy test.
  Moving the suite out of the package tree would contradict T4's sealed
  Touches, and making it collect nothing would hide the skip the gate exists
  to report.
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
