# Plan: Portable catalogue authentication

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
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

- ADR-0134 D1–D12 govern dependency direction, the `credbroker>=0.7,<0.8` range, the public resolver, deployment independence, and the 0.6 compatibility window.
- ADR-0135 D1–D8 govern the standard `.netrc` location, exact-machine lookup, origin binding, redirect handling, and redaction.
- ADR-0136 D1–D12 govern non-secret JFrog discovery, profile and endpoint binding, subprocess limits, and credential ownership. D8 uses 2.105.0 because JSON `config show` output is part of the selected command contract.
- ADR-0137 D1–D11 govern one-time selection, provider order, unavailable and configured-broken states, pinning, and no fallback.
- Python 3.11 and the standard library remain the runtime floor; neither package gains a new third-party runtime dependency other than AgentBundle's required dependency on `credbroker`.
- Package behavior tests stay under each package's test tree and must not read repository-only paths. Repository-level packaging and guide checks use their established build or roster surfaces.
- Non-cosmetic package changes update AgentBundle's manifest and `version.py`; `credbroker` gains a matching `version.py` source while its manifest and public `__version__` remain synchronized.
- The landing commit for the protected AgentBundle engine change carries `Engine-Change-RFC: n/a — accepted ADR-0134 through ADR-0137 govern this change; no RFC applies`.

## Construction tests

**Integration tests:**

- Build both wheels, install them into clean Python 3.11 environments, and prove the dependency, import-origin, isolated-skill, ordinary-skill, and co-location matrices for AC-0001–AC-0003.
- Run the installed AgentBundle CLI against loopback descriptor and archive fixtures for anonymous, exact `.netrc`, and compatible official JFrog CLI paths for AC-0018.
- Run an AST boundary test over the packaged AgentBundle source to prove that credential-source reads stay in `credbroker` and only `catalogue_fetch/jfrog_cli.py` invokes `jf api` for AC-0015.

**Manual verification:** none. JFrog command behavior is captured by a repeatable real-executable contract test, not a manual login or customer-system check.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Behavior contract and strategy — this directory | T1–T5 | Task-mapped tests and verification ledger | Approved baseline, checked ACs, and frozen closeout state |
| Corrected JFrog decision — `docs/adr/0136-catalogue-jfrog-auth-delegates-to-jfrog-cli.md` | T4 | Official command documentation plus real-CLI test | D8 and every current architecture reference name 2.105.0 |
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
`HttpAccessError` exposes only a provider class and stable code. The resolver
accepts an explicit environment mapping so tests and callers do not mutate or
serialize ambient credentials. This is a Python library interface, not a wire
contract. Traces to AC-0004, AC-0006–AC-0011, and AC-0015.

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
`unsupported_jfrog_topology`, `incompatible_jfrog_cli`, `netrc_unreadable`,
`netrc_unsafe`, `netrc_malformed`, and `netrc_incomplete`. Absence and no-match
states do not raise; they advance the closed selector. Fetch failures use
AgentBundle's fetch error surface and never re-enter selection. Traces to AC-0007,
AC-0008, AC-0011, and AC-0015.

The JFrog adapter uses list-form subprocess arguments, closed stdin, monotonic
deadline accounting, terminate/wait cleanup, and a temporary archive file
removed on every failure. Each reader enforces the per-stream cap and failure
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

**Touches:** `packages/credbroker/credbroker/__init__.py`, `packages/credbroker/credbroker/version.py`, `packages/credbroker/credbroker/_http_access.py`, `packages/credbroker/pyproject.toml`, `packages/credbroker/tests/unit/test_*.py`

**Verification mode:** TDD unit and isolated-package integration.

**Spec mapping:** AC-0001–AC-0004, AC-0006, AC-0007, AC-0015.

**Grounding:** The current public export list and compatibility tests are in `credbroker/__init__.py` and `test_public_surface.py`; `user_libs.py` and its projection tests ground the co-location floor. The new resolver types are fixed by this plan's library interface section.

**Tests:**

- `test_resolve_http_access_returns_public_anonymous_variant` (AC-0004, AC-0006), `stub: true`.
- Preserve every existing 0.6 public-surface, signature, and package-skeleton test; add isolated skill and 0.7-over-vendored-0.6 import tests for AC-0002 and AC-0003.
- Build the wheel and assert its declared version, public `__version__`, and new `version.py` agree (AC-0001).
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

**Approach:** Extract the facade and direct provider before moving descriptor logic. Keep `.netrc` and JFrog results rejected as unsupported internal variants until T3 and T4 land, so no partial provider set becomes user-visible.

**Done when:** AgentBundle declares `credbroker>=0.7,<0.8`, the validated stub is materialized unchanged, the baseline HTTPS corpus passes through the facade, and the boundary test proves AgentBundle reads no credential source.

### T3: Exact-machine `.netrc` access is origin-bound and fail-closed

**Depends on:** T2

**Touches:** `packages/credbroker/credbroker/_http_access.py`, `packages/credbroker/tests/unit/test_http_access_netrc.py`, `packages/agentbundle/agentbundle/catalogue_fetch/direct_http.py`, `packages/agentbundle/tests/unit/test_catalogue_fetch.py`

**Verification mode:** TDD unit and redirect integration.

**Spec mapping:** AC-0007, AC-0009, AC-0010, AC-0015, AC-0018.

**Grounding:** Python 3.11's `netrc` parser and ADR-0135 define the user-file, permission, exact-machine, and redirect contract. Existing HTTPS redirect fixtures ground AgentBundle's origin checks.

**Tests:**

- `test_netrc_exact_host_returns_origin_bound_access` (AC-0009, AC-0010), `stub: true`.
- Add the full default-port, non-default-port, host-fallback, `default`-only, missing, incomplete, malformed, unsafe-permission, same-origin redirect, and cross-origin redirect matrix (AC-0007, AC-0009, AC-0010).
- Run canary values through errors, logs, provenance, receipts, and serialized state checks (AC-0015).
- Exercise the exact-machine provider through the installed CLI loopback fixture (AC-0018).
- Stub validation: Python compilation passes; collection is intentionally red because `NetrcHttpAccess` is not yet exported.

```python
# STUB: AC-0009 — an exact machine record returns origin-bound netrc access
from pathlib import Path

from credbroker import NetrcHttpAccess, resolve_http_access


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

**Approach:** Parse only the standard user file in `credbroker`, return derived authorization with its normalized origin, and let AgentBundle's direct provider apply the same redirect hook used by explicit bearer access.

**Done when:** the validated stub is materialized unchanged, the `.netrc` matrix and redirect tests are green on supported platforms, and every hostile or terminal fixture proves zero lower-provider attempts and zero canary disclosure.

### T4: JFrog profile discovery and delegated fetches are bounded to one validated hierarchy

**Depends on:** T2

**Touches:** `packages/credbroker/credbroker/_http_access.py`, `packages/credbroker/tests/unit/test_http_access_jfrog.py`, `packages/agentbundle/agentbundle/catalogue_fetch/jfrog_cli.py`, `packages/agentbundle/tests/unit/test_catalogue_fetch_jfrog.py`, `packages/agentbundle/tests/integration/test_jfrog_cli_contract.py`, `docs/adr/0136-catalogue-jfrog-auth-delegates-to-jfrog-cli.md`, `docs/architecture/portable-catalogue-authentication.md`

**Verification mode:** TDD unit, bounded subprocess integration, and real-executable contract check.

**Spec mapping:** AC-0007, AC-0008, AC-0011–AC-0015, AC-0018.

**Grounding:** Official JFrog documentation fixes `jf config show --format=json`, `jf api <endpoint> --server-id=<id>`, `--timeout`, and the 2.105.0 floor needed by JSON output. The local `jf` executable is absent, so final argument order and binary stdout stay subject to the named real-CLI kill condition.

**Tests:**

- `test_jfrog_longest_profile_returns_pinned_binding` (AC-0011), `stub: true`.
- Add selection, explicit-ID, topology, normalization, endpoint-escape, version, timeout, aggregate-budget, cleanup, hostile-stderr, and no-fallback fixture matrices. For every stream cap defined in AC-0014, exercise exact-boundary and first-byte-over-limit cases and assert terminate/reap happens before parsing or diagnostics and partial files are absent (AC-0007, AC-0008, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015).
- Run a compatible official CLI against a disposable profile and loopback service; reject the adapter design if its arguments, output, or termination behavior differs from the planned contract (AC-0018).
- Stub validation: Python compilation passes; collection is intentionally red because `JfrogCliHttpAccess` is not yet exported.

```python
# STUB: AC-0011 — the unique longest JFrog profile is selected and pinned
import json
import os
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
    jf.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        f"profiles = json.loads({json.dumps(json.dumps(profiles))})\n"
        "if sys.argv[1:] == ['config', 'show', '--format=json']:\n"
        "    print(json.dumps(profiles))\n"
        "elif sys.argv[1:] == ['--version']:\n"
        "    print('jf version 2.105.0')\n"
        "else:\n"
        "    raise SystemExit(2)\n",
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

**Approach:** `credbroker` owns non-secret discovery and version validation; AgentBundle owns endpoint conversion and bounded `jf api` execution. T4 corrects ADR-0136 D8 and the architecture reference to 2.105.0 in the same reviewed change as the contract evidence.

**Done when:** the validated stub is materialized unchanged, all subprocess and confinement matrices pass, and the compatible real CLI proves the final argument order, streamed bytes, exit mapping, timeout termination, and cleanup without a real credential.

### T5: The complete provider selector ships through built packages with current guidance

**Depends on:** T3, T4

**Touches:** `packages/agentbundle/agentbundle/https_catalogue.py`, `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/pyproject.toml`, `packages/agentbundle/tests/integration/test_portable_catalogue_authentication.py`, `packages/agentbundle/DESIGN.md`, `packages/*/{README.md,README-pypi.md,CHANGELOG.md}`, `docs/architecture/credentials.md`, `guides/_shared/how-to/configure-catalogue-enterprise-distribution.md`, `guides/_shared/reference/agentbundle.md`, `docs/guides/how-to/enterprise-app-store.md`, `guides/credential-brokers/how-to/add-a-credentialed-skill.md`

**Verification mode:** TDD provider integration plus goal-based built-artifact and documentation checks.

**Spec mapping:** AC-0001–AC-0003, AC-0005–AC-0008, AC-0015–AC-0019.

**Grounding:** The existing HTTPS catalogue suite and package build tests own runtime compatibility; the named guide files are the current bearer-only user and maintainer surfaces. `docs/guides/explanation/release-coupling.md` governs the coordinated package releases.

**Tests:**

- `test_explicit_bearer_prevents_lower_provider_discovery` (AC-0006, AC-0008, AC-0015), `stub: true`.
- Run the complete provider-state matrix and descriptor/archive reuse tests through installed packages (AC-0005, AC-0006, AC-0007, AC-0008, AC-0015, AC-0016, AC-0017).
- Build documentation and reject the old bearer-only limitation, missing 2.105.0 setup, and credential-like examples in the changed guide regions (AC-0019).
- Run all touched package suites, local lint gates, wheel inspection, isolated and co-located package checks, and built-CLI loopback scenarios (AC-0001, AC-0002, AC-0003, AC-0018).
- Verify the landing commit carries the exact `Engine-Change-RFC:` footer defined in Constraints.
- Stub validation: Python compilation passes; collection is intentionally red because `BearerHttpAccess` is not yet exported.

```python
# STUB: AC-0006 — explicit bearer selection does not inspect lower providers
import os
from pathlib import Path

import pytest

from credbroker import BearerHttpAccess, resolve_http_access


@pytest.mark.skipif(os.name == "nt", reason="stub fixture requires POSIX executable bits")
def test_explicit_bearer_prevents_lower_provider_discovery(tmp_path: Path) -> None:
    marker = tmp_path / "jf-was-called"
    jf = tmp_path / "jf"
    jf.write_text(
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('called', encoding='utf-8')\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)
    result = resolve_http_access(
        "https://catalogue.example.test/root/catalogue.toml",
        env={
            "AGENTBUNDLE_HTTP_BEARER_TOKEN": "test-bearer-canary",
            "JFROG_CLI_SERVER_ID": "must-not-run",
            "HOME": str(tmp_path),
            "PATH": str(tmp_path),
        },
    )

    assert isinstance(result, BearerHttpAccess)
    assert result.provider == "bearer"
    assert not marker.exists()
```

**Approach:** Activate the closed selector only after both added providers pass their own task gates. Release `credbroker` 0.7 before the AgentBundle version that requires it, then update both packages and all living documentation in one compatibility-reviewed closeout.

**Done when:** the validated stub is materialized unchanged, both built-package matrices and the full provider integration suite pass, current architecture and guides agree with the behavior, package versions and changelogs are synchronized, and every spec acceptance criterion has executable evidence.

## Rollout

- **Delivery:** publish `credbroker` 0.7 first, then publish the AgentBundle release that declares `credbroker>=0.7,<0.8`. There is no feature flag or dual-run path; bearer and anonymous callers use the facade immediately, and added providers activate only when matching user-owned setup exists.
- **Infrastructure:** none. The feature adds no service, daemon, store, IAM grant, or managed secret.
- **External-system integration:** JFrog-backed use requires JFrog CLI 2.105.0 or later and an existing user-owned profile. `.netrc` use requires the standard user file with platform-appropriate permissions.
- **Deployment sequencing:** the credential-brokers user-library floor may update independently after the 0.7 compatibility suite passes. Rolling back AgentBundle restores the former bearer/anonymous behavior without changing user credentials; rolling back `credbroker` below 0.7 requires an AgentBundle version that does not declare the 0.7 range. No persistent data migration is involved.

## Risks

- JFrog CLI output or termination behavior may differ across supported platforms. The real-executable contract test is the kill condition; a mismatch returns T4 to design rather than weakening confinement.
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
