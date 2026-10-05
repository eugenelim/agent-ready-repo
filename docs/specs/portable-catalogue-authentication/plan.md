# Plan: Portable catalogue authentication

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** [`docs/architecture/portable-catalogue-authentication.md`](../../architecture/portable-catalogue-authentication.md) and [`docs/architecture/credentials.md`](../../architecture/credentials.md); [`packages/agentbundle/agentbundle/https_catalogue.py`](../../../packages/agentbundle/agentbundle/https_catalogue.py) and [`packages/agentbundle/agentbundle/build/user_libs.py`](../../../packages/agentbundle/agentbundle/build/user_libs.py); [`packages/agentbundle/tests/unit/test_https_catalogue.py`](../../../packages/agentbundle/tests/unit/test_https_catalogue.py), [`packages/agentbundle/tests/build_pipeline/test_user_libs_projection.py`](../../../packages/agentbundle/tests/build_pipeline/test_user_libs_projection.py), and [`packages/credbroker/tests/unit/test_public_surface.py`](../../../packages/credbroker/tests/unit/test_public_surface.py). Named uncertainty: the exact `jf api` argument order and binary-stream behavior remain a real-CLI test obligation against JFrog CLI 2.105.0 or later.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/portable-catalogue-authentication/notes/verification-ledger.md`.
> A genuine artifact error follows the controlled-amendment path.

## Approach

Publish the lower-level `credbroker` 0.7 resolver contract first, then make
AgentBundle consume it through a new fetch-session facade while keeping JFrog
and `.netrc` unavailable until their complete providers exist. Implement the
two providers independently, converge them in the closed selector, and finish
with built-package, real-CLI, documentation, and release evidence. Unit tests
drive each rule; package and loopback integration tests prove the crossed
boundaries without real credentials or customer systems.

## Constraints

- ADR-0135 D1–D12 govern dependency direction, the `credbroker>=0.7,<0.8` range, the public resolver, deployment independence, and the 0.6 compatibility window.
- ADR-0136 D1–D8 govern the standard `.netrc` location, exact-machine lookup, origin binding, redirect handling, and redaction.
- ADR-0137 D1–D12 govern non-secret JFrog discovery, profile and endpoint binding, subprocess limits, and credential ownership. D8 uses 2.105.0 because JSON `config show` output is part of the selected command contract.
- ADR-0138 D1–D11 govern one-time selection, provider order, unavailable and configured-broken states, pinning, and no fallback.
- Python 3.11 and the standard library remain the runtime floor; neither package gains a new third-party runtime dependency other than AgentBundle's required dependency on `credbroker`.
- Package behavior tests stay under each package's test tree and must not read repository-only paths. Repository-level packaging and guide checks use their established build or roster surfaces. `packages/agentbundle/tests/` ships inside the sdist and is re-run against a package-only workspace, so AC-0001, AC-0002, AC-0003, and AC-0018 — which build wheels, install into clean environments, read the vendored floor under `packs/`, and drive the built CLI — live in `tests/roster/`, anchored at `Path(__file__).resolve().parents[2]`. Adding a roster module obliges the three further edits in `tests/AGENTS.md`: a named step above the bulk step in `.github/workflows/build-check.yml`, a matching `STEP_DISPOSITION` of `LOCAL("test-after-build-check")` in `tools/lint-ci-parity.py`, and a `.workspace-prune-protected.toml` entry only if the module names a `docs/specs/<slug>` path literally.
- Non-cosmetic package changes update AgentBundle's manifest and `version.py`; `credbroker` gains a matching `version.py` source while its manifest and public `__version__` remain synchronized.
- The landing commit for the protected AgentBundle engine change carries `Engine-Change-RFC: n/a — accepted ADR-0135 through ADR-0138 govern this change; no RFC applies`.

## Construction tests

**Integration tests:**

- From `tests/roster/test_portable_catalogue_authentication_packaging.py`: build both wheels, install them into clean Python 3.11 environments, and prove the dependency, import-origin, isolated-skill, ordinary-skill, and co-location matrices for AC-0001–AC-0003.
- From that same roster module: run the installed AgentBundle CLI against loopback descriptor and archive fixtures for anonymous and exact `.netrc` paths, for AC-0018. Its JFrog path runs in a disposable Linux container holding the built wheels and a compatible official CLI located through a test-only environment variable, with the disposable loopback CA supplied through `SSL_CERT_FILE`; outside such a container the JFrog case skips with that stated reason, and AC-0018 is not checked until the container run passes.
- Run an AST boundary test over the packaged AgentBundle source to prove that credential-source reads stay in `credbroker` and only `catalogue_fetch/jfrog_cli.py` invokes `jf api` for AC-0015.

**Manual verification:** none. JFrog command behavior is captured by a repeatable real-executable contract test, not a manual login or customer-system check.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Behavior contract and strategy — this directory | T1–T5 | Task-mapped tests and verification ledger | Approved baseline, checked ACs, and frozen closeout state |
| Corrected JFrog decision — `docs/adr/0137-catalogue-jfrog-auth-delegates-to-jfrog-cli.md` | none — already met on this branch | Official command documentation plus real-CLI test | D8 and every current architecture reference already name 2.105.0; T4 verifies D8 and edits no ADR, and its architecture edits concern only the appended-newline rule |
| Current architecture — both credential architecture documents | T1, T2, T4, T5 | Import-boundary, provider, and security tests | Architecture review reports no stale dependency or credential edge |
| AgentBundle package truth — DESIGN, manifest, version, README, CHANGELOG | T2, T5 | Wheel install, version, and built-CLI tests | Built artifact metadata and current docs agree |
| `credbroker` package truth — manifest, version, README, CHANGELOG | T1, T3, T4, T5 | Public-surface, compatibility, and resolver tests | Built artifact exposes the approved 0.7 surface |
| User and maintainer guidance — established enterprise and credential-broker guides | T5 | Documentation build and stale-claim checks | Setup, precedence, errors, and package independence match the shipped behavior |

## Design (LLD)

### Interfaces & contracts

`credbroker.__init__` exports `resolve_http_access`, `HttpAccessError`, and four
frozen result variants: `BearerHttpAccess(origin, authorization)`,
`NetrcHttpAccess(origin, authorization)`,
`JfrogCliHttpAccess(server_id, platform_url, artifactory_url)`, and
`AnonymousHttpAccess(origin)`. Each variant exposes its literal `provider`;
`HttpAccessError` exposes only a provider class and stable code. Host
normalization uses the standard library's own IDNA codec, as `Agent Rules`
requires, so no third-party distribution is needed and, on every request
AgentBundle opens, the compared form is the form the stdlib uses to open the
connection. The delegated JFrog leg is the stated exception: `jf` opens that
connection from its own configured platform base, so host identity there is the
accepted residual `Agent Rules` records rather than a property this code holds. `resolve_http_access` owns the
target check and is the single component that refuses an unencodable host: it
raises `HttpAccessError` with provider class `target` and code
`invalid_target_host` before any provider is evaluated. That is the existing
two-outcome surface, so the export count stays at six and AgentBundle's facade
performs no second target check. The resolver
accepts an explicit environment mapping so tests and callers do not mutate or
serialize ambient credentials. That mapping is the credential-source lookup
environment only; it is not handed to a child process. Each subprocess
environment is derived from it by a closed allowlist, and every variable
outside that list is dropped, including every credential-bearing one. The one
deliberate exception is a carried proxy variable, whose value may embed user
information: dropping it would break the proxy behaviour AC-0016 obliges. The
child environment is the one channel AC-0015 exempts for that value; every other
channel still excludes it, and the canary fixture asserts over emitted output,
diagnostics, exception text, logs, persisted state, provenance and receipts
rather than over the capture buffer, which is bounded and sanitized before it
becomes AgentBundle-visible. The
list is `PATH`; `HOME` on POSIX and `SystemRoot`, `USERPROFILE`, `HOMEDRIVE`,
`HOMEPATH`, `PATHEXT` on Windows; `JFROG_CLI_HOME_DIR`; `SSL_CERT_FILE` and
`SSL_CERT_DIR`; and `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` with their lowercase
spellings.

Four of those entries are deliberate, and each has a reason the vendor
documentation or the real-CLI contract test supplies. `JFROG_CLI_HOME_DIR` is carried because `jf` locates
its server profile through it or through `HOME`; dropping it would turn a
relocated-but-valid profile into a no-match, which ADR-0138 D3 treats as
*unavailable*, silently downgrading a protected fetch to anonymous. The proxy
variables are carried because JFrog documents `jf` as honouring them, and
AC-0016 obliges proxy behaviour to survive; the lowercase spellings are
carried because the CLI is a Go program and `net/http` reads them even though
JFrog documents only the uppercase forms. `SSL_CERT_FILE` and `SSL_CERT_DIR`
are carried because `jf api` ignores the CLI's own `security/certs/` trust
store and, on Linux, reads trust anchors from these two Go variables, so a
corporate CA reaches the delegated leg only through them; the verification
ledger records the real-CLI evidence. On macOS, `jf api` trusts only the system
keychain, which is a stated residual. Both variables hold file paths, not
secrets. `REQUESTS_CA_BUNDLE` stays dropped, because it is a Python `requests`
convention that no Go program reads. The in-process direct-HTTP path is unaffected by any of this,
because it is not a child process and keeps its existing proxy and CA handling.

`jf` is resolved to an absolute path by searching the allowlisted `PATH` with
the working directory and every relative or empty entry excluded, and the
resolved target must be a directly executable image rather than a `.cmd`/`.bat`
shim the platform would service through a command interpreter. A refused
resolution terminates with `jfrog_cli_not_executable` under ADR-0138 D4 only
when an explicit JFrog server was requested; with no such request it is
unavailable under D3, exactly as an absent executable is, and resolution
continues so a public catalogue still installs anonymously. Every
delegated subprocess starts in a controlled directory no catalogue, archive, or
untrusted clone content can write to. The home directory backing `.netrc` and
`jf` profile lookup is read from the supplied mapping using the platform's own
precedence — `HOME` on POSIX, `USERPROFILE` then `HOMEDRIVE`+`HOMEPATH` on
Windows — because `expanduser` ignores `HOME` on Windows. The allowlist carries
that whole Windows pair rather than `USERPROFILE` alone, so the child reaches
the same home the parent resolved a profile from; carrying only `USERPROFILE`
would reintroduce the silent no-match this allowlist exists to prevent on a host
where only `HOMEDRIVE`/`HOMEPATH` is set.

This is a Python library interface, not a wire contract. Traces to AC-0004,
AC-0006–AC-0011, and AC-0015.

AgentBundle's internal `catalogue_fetch.open_fetch_session` accepts the initial
validated HTTPS URL and environment mapping, resolves access once, and returns
a context-managed session with bounded byte and file fetch operations. Provider
modules return payload plus non-secret response metadata; descriptor parsing,
artifact resolution, digest checks, provenance, and extraction remain in
`https_catalogue.py`. Traces to AC-0005, AC-0008, AC-0010, and AC-0016–AC-0018.

Owned by: T1, T2, T3, T4, T5

### Failure, edge cases & resilience

`HttpAccessError.code` uses a closed set for configured resolver failures:
`invalid_bearer`, `jfrog_discovery_failed`, `jfrog_discovery_timeout`,
`jfrog_discovery_too_large`, `jfrog_discovery_malformed`,
`jfrog_profile_ambiguous`, `jfrog_profile_mismatch`,
`unsupported_jfrog_topology`, `incompatible_jfrog_cli`, `jfrog_probe_too_large`,
`jfrog_probe_timeout`, `jfrog_probe_failed`, `jfrog_cli_not_executable`,
`invalid_target_host`, `netrc_unreadable`,
`netrc_unsafe`, `netrc_malformed`, and `netrc_incomplete`. Absence and no-match
states do not raise; they advance the closed selector. Fetch failures use
AgentBundle's fetch error surface and never re-enter selection; that surface
gains its own stable non-secret `code` attribute. For AC-0014's AgentBundle-side
bounds the closed set is `jfrog_fetch_stderr_too_large`, `descriptor_too_large`,
`archive_too_large`, `jfrog_fetch_timeout`, and `jfrog_fetch_failed`. The same
attribute carries `redirect_not_permitted` for AC-0010's reject-before-send and
`endpoint_not_permitted` for AC-0012's confinement rejections, so no terminal
failure on that surface is left without a code to emit. Traces to AC-0007,
AC-0008, AC-0011, and AC-0015.

The JFrog adapter uses list-form subprocess arguments, closed stdin, a controlled
working directory, monotonic deadline accounting, terminate-then-kill cleanup
bounded inside the call's own deadline, and a temporary archive file removed on
every failure. The reap always runs against an already-terminated process, which
is what lets AC-0014's mandatory reap and AC-0013's deadline coexist. The adapter
never passes `jf api --timeout`: on expiry that flag exits 0 with a truncated
body, so the adapter's own deadline and kill remain the only timeout control.
`jf api` appends one `0x0a` to stdout when the response body does not already
end in one. The descriptor and archive stdout readers therefore admit their cap
plus that one byte and remove it when stdout reaches that length, so no more than
the cap is ever accepted, as AC-0014 states. https_catalogue.py verifies a JFrog
archive's digest against the admitted bytes and then against those bytes with one
trailing `0x0a` removed, and extracts only the candidate that matched, as AC-0016
states. ADR-0137 D10's limits therefore hold unchanged on the accepted bytes. Exit status 0 is the only success signal;
stderr, which carries an HTTP status line and the full request URL, is bounded
and never emitted. Each reader enforces the per-stream cap and failure
ordering defined once in AC-0014. The exact argument order and official CLI
behavior are accepted only when the real-CLI contract test passes on version
2.105.0 or later; failure of that test is the kill condition for the adapter
design. Traces to AC-0012–AC-0015 and AC-0018.

Owned by: T1, T3, T4, T5

### Dependencies & integration

AgentBundle declares `credbroker>=0.7,<0.8` and imports only its public surface
from `catalogue_fetch`. `credbroker` never imports AgentBundle. The
credential-brokers pack continues to project `credbroker` as a user-library
floor, where normal Python import precedence lets a compatible installed 0.7
replace the vendored 0.6 copy. Release order is covered in
[`Rollout`](#rollout). Traces to AC-0001–AC-0004 and AC-0015.

Owned by: T1, T2, T5

## Tasks

### T1: `credbroker` 0.7 exposes a compatible target-bound HTTP access API

**Depends on:** none

**Touches:** `packages/credbroker/credbroker/__init__.py`, `packages/credbroker/credbroker/version.py`, `packages/credbroker/credbroker/_http_access.py`, `packages/credbroker/pyproject.toml`, `packages/credbroker/tests/unit/test_*.py`, `tests/roster/test_portable_catalogue_authentication_packaging.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`

**Verification mode:** TDD unit and isolated-package integration.

**Spec mapping:** AC-0001–AC-0004, AC-0006, AC-0007, AC-0015.

**Grounding:** The current public export list and compatibility tests are in `credbroker/__init__.py` and `test_public_surface.py`; `user_libs.py` and its projection tests ground the co-location floor. The new resolver types are fixed by this plan's library interface section.

**Tests:**

- `test_resolve_http_access_returns_public_anonymous_variant` (AC-0004, AC-0006), `stub: true`.
- Preserve every existing 0.6 public-surface, signature, and package-skeleton test; keep the package-level half against fixtures in `packages/credbroker/tests/unit/`.
- Put the isolated-skill and 0.7-over-vendored-0.6 import matrices for AC-0002 and AC-0003 in `tests/roster/test_portable_catalogue_authentication_packaging.py`, anchored at `parents[2]`, because they read the vendored floor under `packs/`.
- Build the wheel in that same roster module and assert its declared version, public `__version__`, and new `version.py` agree (AC-0001).
- Register the roster module in the same task that creates it, as `tests/AGENTS.md` obliges: a named step above the bulk `pytest tests/ -q` step in `.github/workflows/build-check.yml`, and a matching `STEP_DISPOSITION` of `LOCAL("test-after-build-check")` in `tools/lint-ci-parity.py`. Registering here rather than at T5 keeps a T2–T4 failure attributed to the named step instead of the broad one. The module names no `docs/specs/<slug>` literal, so no `.workspace-prune-protected.toml` entry is owed.
- Run configured-broken and canary matrices against the public error surface (AC-0007, AC-0015).
- Stub validation: Python compilation passes; collection is intentionally red because `AnonymousHttpAccess` is not yet exported.

```python
# STUB: AC-0004 — the resolver returns the public anonymous result variant
from credbroker import AnonymousHttpAccess, resolve_http_access


def test_resolve_http_access_returns_public_anonymous_variant() -> None:
    result = resolve_http_access("https://catalogue.example.test/root/catalogue.toml", env={})

    assert isinstance(result, AnonymousHttpAccess)
    assert result.provider == "anonymous"
    assert result.origin == "https://catalogue.example.test"
```

**Approach:** Add `_http_access.py` behind public exports, and introduce `version.py` as the package's version source so the required manifest/version-source rule becomes enforceable without changing the existing `credbroker.__version__` consumer surface.

**Done when:** the credbroker unit suite and isolated/co-located package tests are green, the validated stub is materialized unchanged, and the built 0.7 wheel preserves the 0.6 public API while exposing the six new names: `resolve_http_access`, `HttpAccessError`, and the four immutable result variants.

### T2: AgentBundle's fetch-session facade preserves bearer and anonymous acquisition

**Depends on:** T1

**Touches:** `packages/agentbundle/pyproject.toml`, `packages/agentbundle/agentbundle/catalogue_fetch/*.py`, `packages/agentbundle/agentbundle/https_catalogue.py`, `packages/agentbundle/tests/unit/test_catalogue_fetch.py`, `packages/agentbundle/tests/unit/test_https_catalogue.py`, `packages/agentbundle/tests/contracts/test_catalogue_fetch_credential_boundary.py`

**Verification mode:** TDD unit and package-boundary integration.

**Spec mapping:** AC-0001, AC-0005, AC-0008, AC-0010, AC-0015–AC-0017.

**Grounding:** `https_catalogue.py` owns the baseline redirects, limits, digest, provenance, and extraction behavior. The architecture delta fixes the new module boundary; the existing `test_https_catalogue.py` corpus is the compatibility oracle.

**Tests:**

- `test_open_fetch_session_resolves_anonymous_access_once` (AC-0005, AC-0008), `stub: true`.
- Run the current bearer, anonymous, redirect, proxy, CA, descriptor, digest, extraction, and resource-limit corpus unchanged through the facade (AC-0005, AC-0010, AC-0016, AC-0017).
- Add the AST credential-boundary test and package-metadata dependency assertion (AC-0001, AC-0015).
- Stub validation: Python compilation passes; collection is intentionally red because `agentbundle.catalogue_fetch` does not yet exist.

```python
# STUB: AC-0008 — a fetch session resolves one provider for the acquisition
from agentbundle.catalogue_fetch import open_fetch_session


def test_open_fetch_session_resolves_anonymous_access_once() -> None:
    with open_fetch_session(
        "https://catalogue.example.test/root/catalogue.toml",
        env={},
    ) as session:
        assert session.provider == "anonymous"
        assert session.target_origin == "https://catalogue.example.test"
```

**Approach:** Extract the facade and direct provider before moving descriptor logic. `credbroker` exports all four result variants publicly from T1; AgentBundle simply does not yet accept the `.netrc` and JFrog variants, rejecting them as unsupported until T3 and T4 land, so no partial provider set becomes user-visible.

**Done when:** AgentBundle declares `credbroker>=0.7,<0.8`, the validated stub is materialized unchanged, the baseline HTTPS corpus passes through the facade, and the boundary test proves AgentBundle reads no credential source.

### T3: Exact-machine `.netrc` access is origin-bound and fail-closed

**Depends on:** T2

**Touches:** `packages/credbroker/credbroker/_http_access.py`, `packages/credbroker/tests/unit/test_http_access_netrc.py`, `packages/agentbundle/agentbundle/catalogue_fetch/direct_http.py`, `packages/agentbundle/tests/unit/test_catalogue_fetch.py`

**Verification mode:** TDD unit and redirect integration.

**Spec mapping:** AC-0007, AC-0009, AC-0010, AC-0015, AC-0018.

**Grounding:** Python 3.11's `netrc` parser and ADR-0136 define the user-file, permission, exact-machine, and redirect contract. Existing HTTPS redirect fixtures ground AgentBundle's origin checks.

**Tests:**

- `test_netrc_exact_host_returns_origin_bound_access` (AC-0009, AC-0010), `stub: true`.
- Add the full default-port, non-default-port, host-fallback, `default`-only, missing, incomplete, malformed, unsafe-permission, same-origin redirect, and cross-origin redirect matrix (AC-0007, AC-0009, AC-0010), plus the host-normalization cases AC-0009 names, including the lossy-folding case that asserts the compared and connected forms agree.
- Cover Windows explicitly rather than by omission: the stub carries the POSIX guard its siblings carry, and a separate Windows-only case drives home resolution through `USERPROFILE` to prove the supplied mapping reaches `.netrc` lookup where `expanduser` ignores `HOME`. The unsafe-permission leg stays POSIX-only per ADR-0136 D7.
- Run canary values through errors, logs, provenance, receipts, and serialized state checks (AC-0015).
- Exercise the exact-machine provider through the installed CLI loopback fixture (AC-0018).
- Stub validation: Python compilation passes; collection is intentionally red because `NetrcHttpAccess` is not yet exported.

```python
# STUB: AC-0009 — an exact machine record returns origin-bound netrc access
import os
from pathlib import Path

import pytest

from credbroker import NetrcHttpAccess, resolve_http_access


@pytest.mark.skipif(os.name == "nt", reason="stub fixture requires POSIX permission bits")
def test_netrc_exact_host_returns_origin_bound_access(
    tmp_path: Path,
) -> None:
    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text(
        "machine catalogue.example.test login test-user password test-secret\n",
        encoding="utf-8",
    )
    netrc_file.chmod(0o600)

    result = resolve_http_access(
        "https://catalogue.example.test/root/catalogue.toml",
        env={"HOME": str(tmp_path)},
    )

    assert isinstance(result, NetrcHttpAccess)
    assert result.origin == "https://catalogue.example.test"
```

**Approach:** Parse only the standard user file in `credbroker`, resolving the home directory from the supplied mapping with platform precedence, and return derived authorization with its normalized origin. AgentBundle's direct provider applies the same redirect hook used by explicit bearer access.

**Done when:** the validated stub is materialized unchanged, the `.netrc` matrix and redirect tests are green on supported platforms, and every hostile or terminal fixture proves zero lower-provider attempts and zero canary disclosure.

### T4: JFrog profile discovery and delegated fetches are bounded to one validated hierarchy

**Depends on:** T2

**Touches:** `packages/credbroker/credbroker/_http_access.py`, `packages/credbroker/tests/unit/test_http_access_jfrog.py`, `packages/agentbundle/agentbundle/catalogue_fetch/jfrog_cli.py`, `packages/agentbundle/agentbundle/catalogue_fetch/__init__.py`, `packages/agentbundle/agentbundle/https_catalogue.py`, `packages/agentbundle/tests/unit/test_catalogue_fetch_jfrog.py`, `packages/agentbundle/tests/integration/test_jfrog_cli_contract.py`, `docs/architecture/portable-catalogue-authentication.md`

**Verification mode:** TDD unit, bounded subprocess integration, and real-executable contract check.

**Spec mapping:** AC-0007, AC-0008, AC-0011–AC-0016, AC-0018.

**Grounding:** Official JFrog documentation fixes `jf config show --format=json`, `jf api <endpoint> --server-id=<id>`, and the 2.105.0 floor needed by JSON output. The real-CLI contract probe recorded in `notes/verification-ledger.md` grounds the rest against JFrog CLI 2.105.0: `jf api --server-id=<id> -- <endpoint>` delimits an option-like endpoint as a path; exit status 0 means a 2xx response and 1 means any other; stdout gains one trailing `0x0a` when the body lacks one; `--timeout` truncates silently with exit status 0; `jf api` ignores `security/certs/` and, on Linux, trusts `SSL_CERT_FILE`; and no descendant process holds the output pipe after the direct child is killed. The local `jf` executable is absent. T4 acquires an official JFrog CLI 2.105.0 or later through `contract-acquisition`, from the vendor's published release for the host platform, into a disposable session-local directory that is never committed and never added to the user's `PATH`; `.github/workflows/publish-catalogue.yml` already installs the same CLI and is the existing repository seam. The contract check runs as `packages/agentbundle/tests/integration/test_jfrog_cli_contract.py`, pointed at that executable through a test-only environment variable and skipped with a stated reason when it is unset. If one bounded supported acquisition attempt cannot obtain or execute a compatible CLI, T4 surfaces the AC-0018 blocker and the minimum recovery action rather than weakening confinement, substituting a mock argv assertion, or declaring the task complete. Final argument order and binary stdout stay subject to the named real-CLI kill condition.

**Tests:**

- `test_jfrog_longest_profile_returns_pinned_binding` (AC-0011), `stub: true`.
- Add selection, explicit-ID, topology, host-normalization (including an internationalized profile and target spelled differently, which must still match), refused-image on both branches (explicit server requested, so terminal; no explicit server, so unavailable and the anonymous path still completes), endpoint-escape, version, timeout, aggregate-budget, cleanup, hostile-stderr, and no-fallback fixture matrices. For every stream cap defined in AC-0014, exercise exact-boundary and first-byte-over-limit cases and assert terminate/reap happens before parsing or diagnostics and partial files are absent (AC-0007, AC-0008, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015).
- Cover the appended newline for the descriptor and archive `jf api` stdout readers: a body ending in `0x0a`, a body not ending in it, an empty body, the exact cap, the cap plus one byte ending in `0x0a` (accepted), the cap plus one byte ending in another byte (rejected), and the cap plus two bytes (rejected); assert that no more than the cap reaches parsing, digest acceptance, or extraction in every accepted case. Cover the archive digest on the exact bytes, on the trimmed bytes, and on a mismatch of both candidates; assert that the file handed to extraction is byte-identical to the candidate that matched; and prove a direct request never trims (AC-0014, AC-0016).
- Run a compatible official CLI against a disposable profile and loopback service in a disposable Linux container, with the loopback CA supplied through `SSL_CERT_FILE` and the executable located through a test-only environment variable; reject the adapter design if its arguments, output, or termination behavior differs from the contract this task row and the verification ledger record (AC-0018).
- Record the acquired build's exact version in the verification ledger and state both discoveries against that build rather than against 2.105.0 generically. First, whether that build leaves descendants holding the output pipe after the direct child is killed; AC-0013 scopes termination to the direct child, and a positive result takes the controlled-amendment path to process-group and job-object termination. Second, whether `jf config show --format=json` is present in that build. A build at or above the floor that carries the flag corroborates ADR-0137 D8 without proving 2.105.0 is the earliest such version, which is the conservative direction and needs no further action; a build that lacks it falsifies D8 and sends AC-0011's "rejects JFrog CLI versions below 2.105.0" and ADR-0137 D8 through controlled amendment to the floor the evidence supports. Acquiring exactly 2.105.0 settles the floor outright and is preferred where the vendor still publishes it.
- Stub validation: Python compilation passes; collection is intentionally red because `JfrogCliHttpAccess` is not yet exported.

```python
# STUB: AC-0011 — the unique longest JFrog profile is selected and pinned
import json
import os
import shlex
from pathlib import Path

import pytest

from credbroker import JfrogCliHttpAccess, resolve_http_access


@pytest.mark.skipif(os.name == "nt", reason="stub fixture requires POSIX executable bits")
def test_jfrog_longest_profile_returns_pinned_binding(
    tmp_path: Path,
) -> None:
    jf = tmp_path / "jf"
    profiles = [
        {
            "serverId": "broad",
            "url": "https://platform.example.test/",
            "artifactoryUrl": "https://platform.example.test/artifactory/",
            "isDefault": True,
        },
        {
            "serverId": "catalogues",
            "url": "https://platform.example.test/",
            "artifactoryUrl": "https://platform.example.test/artifactory/catalogues/",
            "isDefault": False,
        },
    ]
    # `/bin/sh` is an absolute interpreter, so the fixture runs under the
    # allowlisted child environment without needing `python3` on `PATH`.
    jf.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        '  echo "jf version 2.105.0"\n'
        "else\n"
        "  exit 2\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    result = resolve_http_access(
        "https://platform.example.test/artifactory/catalogues/team/catalogue.toml",
        env={"PATH": str(tmp_path)},
    )

    assert isinstance(result, JfrogCliHttpAccess)
    assert result.server_id == "catalogues"
    assert result.artifactory_url.endswith("/artifactory/catalogues/")
```

**Approach:** `credbroker` owns non-secret discovery and version validation; AgentBundle owns endpoint conversion and bounded `jf api` execution. ADR-0137 D8 and the architecture reference already name 2.105.0 on this branch, so that correction is met and T4 edits no ADR. T4 does update `docs/architecture/portable-catalogue-authentication.md`: the delta-table row that gives descriptor, digest, provenance, and extraction "no new provider-specific rules", the JFrog CLI delta's stdout caps, and the limits row, so that each states the JFrog-leg appended-newline rule and that the accepted bytes stay within the 1 MiB and 256 MiB limits.

**Done when:** the validated stub is materialized unchanged, all subprocess and confinement matrices pass, and the compatible real CLI proves the final argument order, streamed bytes, exit mapping, timeout termination, and cleanup without a real credential.

### T5: The complete provider selector ships through built packages with current guidance

**Depends on:** T3, T4

**Touches:** `packages/agentbundle/agentbundle/https_catalogue.py`, `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/pyproject.toml`, `packages/agentbundle/tests/integration/test_portable_catalogue_authentication.py`, `tests/roster/test_portable_catalogue_authentication_packaging.py`, `packages/agentbundle/DESIGN.md`, `packages/*/{README.md,README-pypi.md,CHANGELOG.md}`, `docs/architecture/credentials.md`, `guides/_shared/how-to/configure-catalogue-enterprise-distribution.md`, `guides/_shared/reference/agentbundle.md`, `docs/guides/how-to/enterprise-app-store.md`, `guides/credential-brokers/how-to/add-a-credentialed-skill.md`, `docs/product/changelog.md`

**Verification mode:** goal-based built-artifact and documentation checks. T5 owns no red-first family; the provider behaviour it exercises was delivered by T2–T4 and is re-run here through installed packages as regression evidence.

**Spec mapping:** AC-0001–AC-0003, AC-0005–AC-0008, AC-0015–AC-0019.

**Grounding:** The existing HTTPS catalogue suite and package build tests own runtime compatibility; the named guide files are the current bearer-only user and maintainer surfaces. `docs/guides/explanation/release-coupling.md` governs the coordinated package releases.

**Tests:**

- `no stub (goal-based)`. Once T4 lands, the facade accepts all four providers, so T5 introduces no behavioural seam a stub could drive red; T5 is verified by the built-artifact and documentation checks below.
- Run the complete provider-state matrix and descriptor/archive reuse tests through installed packages (AC-0005, AC-0006, AC-0007, AC-0008, AC-0015, AC-0016, AC-0017).
- Build documentation and reject the old bearer-only limitation, missing 2.105.0 setup, and credential-like examples in the changed guide regions (AC-0019).
- Run all touched package suites and local lint gates. Wheel inspection, the isolated and co-located package checks, and the built-CLI loopback scenarios run from `tests/roster/test_portable_catalogue_authentication_packaging.py`, because each builds artifacts or reads the repository tree (AC-0001, AC-0002, AC-0003, AC-0018). The built-CLI JFrog scenario runs that module inside a disposable Linux container with the built wheels, a compatible official CLI located through a test-only environment variable, and the disposable loopback CA supplied through `SSL_CERT_FILE`, as AC-0018 requires.
- The roster module's CI registration is T1's, not T5's; T5 adds cases to the module T1 already registered.
- Verify the landing commit carries the exact `Engine-Change-RFC:` footer defined in Constraints.
- Stub validation: not applicable. T2's Approach scopes AgentBundle's rejection of the `.netrc` and JFrog variants to "until T3 and T4 land", so every provider the facade exposes is already accepted when T5 begins. A T5 stub asserting provider acceptance would pass on arrival, and one asserting bearer precedence is already covered by T1's configured-broken matrix — neither could earn an honest red.

**Approach:** T4 completes the provider set, so T5 adds no provider behaviour; its `https_catalogue.py` work is release-facing wiring and the re-run of the complete provider-state matrix through installed packages. Release `credbroker` 0.7 before the AgentBundle version that requires it, then update both packages and all living documentation in one compatibility-reviewed closeout.

**Done when:** the roster packaging module is green, both built-package matrices and the full provider integration suite pass, current architecture and guides agree with the behavior, package versions and changelogs are synchronized, and every spec acceptance criterion has executable evidence.

## Rollout

- **Delivery:** publish `credbroker` 0.7 first, then publish the AgentBundle release that declares `credbroker>=0.7,<0.8`. There is no feature flag or dual-run path; bearer and anonymous callers use the facade immediately, and added providers activate only when matching user-owned setup exists.
- **Infrastructure:** none. The feature adds no service, daemon, store, IAM grant, or managed secret.
- **External-system integration:** JFrog-backed use requires JFrog CLI 2.105.0 or later and an existing user-owned profile. `.netrc` use requires the standard user file with platform-appropriate permissions.
- **Deployment sequencing:** the credential-brokers user-library floor may update independently after the 0.7 compatibility suite passes. Rolling back AgentBundle restores the former bearer/anonymous behavior without changing user credentials; rolling back `credbroker` below 0.7 requires an AgentBundle version that does not declare the 0.7 range. No persistent data migration is involved.

## Risks

- JFrog CLI output or termination behavior may differ across supported platforms. The real-executable contract test is the kill condition; a mismatch returns T4 to design rather than weakening confinement. The CLI is acquired through `contract-acquisition` into a disposable session-local directory, and an acquisition that fails after one bounded supported attempt surfaces the AC-0018 blocker rather than degrading the check to a mock argv assertion.
- ADR-0137 D8's 2.105.0 floor is corroborated: the official 2.105.0 build carries `jf config show --format=json`, as the verification ledger records.
- `jf api` stdout is not byte-faithful, and the appended-newline rule rests on observed vendor behaviour that JFrog does not document. If a later JFrog release stops appending the byte, exact matching still succeeds first; if it changes stdout in any other way, the digest check fails closed.
- A private CA reaches `jf api` only through `SSL_CERT_FILE` or `SSL_CERT_DIR` on Linux and only through the system keychain on macOS. A user whose CA lives only in `security/certs/` sees a terminal `jfrog_fetch_failed`, not a fallback.
- A required AgentBundle dependency can be shadowed by the repository checkout or vendored user-library floor. Clean-wheel import-origin and co-location tests make each environment visible.
- Moving mature HTTPS code behind a facade can change redirects, proxies, CA handling, or error mapping. The existing test corpus remains the compatibility oracle and runs before the new providers activate.
- Sanitization may miss a child-process or exception channel. Canary tests cover each user-visible and persisted channel, and the security review checks the trust boundary separately.

## Changelog

<!-- Approval entries are added only at their separate human gates:
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->
- 2026-10-01: spec approved by eugenelim
- 2026-10-01: plan approved by eugenelim
- 2026-10-01: amended under run 4bf9c822 from 13 adjudicated pre-EXECUTE findings (6 security, 7 adversarial); awaiting re-approval
- 2026-10-01: second consolidated amendment under run 4bf9c822 from 9 further adjudicated findings, walking each changed criterion against its sibling criteria and ADR decisions; T5 reclassified goal-based; awaiting re-approval
- 2026-10-01: spec re-approved by eugenelim after the run-4bf9c822 amendment cycle — 8 pre-EXECUTE review rounds, 31 adjudicated sustained findings repaired, both mandatory reviewers closing with no unresolved Blocker or Concern
- 2026-10-01: plan re-approved by eugenelim; baseline sealed under run 4bf9c822
- 2026-10-02: controlled amendment under run 4bf9c822 for T4, from real-CLI Discoveries 5–7 and owner decisions OD-1 (digest-checked trim on the JFrog leg) and OD-2 (carry `SSL_CERT_FILE` and `SSL_CERT_DIR`), recorded in `notes/verification-ledger.md`; T5 also gains the product changelog it owes; awaiting re-approval
- 2026-10-02: spec re-approved by eugenelim after the T4 amendment — pre-EXECUTE rounds 9–11, 5 adjudicated sustained findings repaired, both mandatory reviewers closing clean
- 2026-10-02: plan re-approved by eugenelim; baseline re-sealed under run 4bf9c822 with T1 and T2 preserved as completed
