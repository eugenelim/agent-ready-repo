# Spec: credbroker

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0023](../../rfc/0023-credential-manager-broker.md) (canonical proposal — read first; this spec is its `docs/specs/credbroker/` follow-on artifact, scoped to **Phase 1** repo-path install). Reverses [ADR-0003](../../adr/0003-credential-broker-contract.md) (projected-shim decision); the superseding ADR is a **separate** governance artifact authored in parallel — when it lands, add it here. Preserves verbatim the resolver semantics of [RFC-0006](../../rfc/0006-skill-secrets-storage.md) (three storage tiers, Win32 error matrix, atomic-write discipline, per-platform Tier-2 backends) and [RFC-0013](../../rfc/0013-credential-broker-contract.md) / the [`credential-broker-contract`](../credential-broker-contract/spec.md) spec (the `credentials_shim` public surface this package inherits); changes the resolver's *delivery* (pip library, not byte-projected shim) and adds an encrypted-vault tier, not its core tier semantics. Leaves the reserved `3–9` exit band of [`credentialed-cli-exit-code-contract`](../credentialed-cli-exit-code-contract/spec.md) **unclaimed** (credbroker ships no CLI in v1).
- **Brief:** none
- **Contract:** none <!-- credbroker exposes a Python library API (in-process import), not a REST/event/RPC/GraphQL/JSON-Schema interface surface, so new-spec step 4b is skipped; the public Python API is specified inline below. -->
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Scope: Phase 1 only, single coherent spec.** RFC-0023 phases delivery —
> **Phase 1** is repo-path install (`pip install -e ./packages/credbroker`, no
> published version, no version pinning); **Phase 2** is PyPI publication +
> version pinning, gated on the package stabilising. This spec covers Phase 1
> end-to-end: build the package (stdlib core + optional `[crypto]` vault),
> migrate the **six** in-tree consumers off the byte-projected shim, and retire
> the `shared-libs/` projection + drift gate once no consumer imports the
> vendored shim. **Phase 2 is deferred** (see Acceptance Criteria and
> [`docs/backlog.md`](../../backlog.md#credbroker)). All Phase-1 tasks live in
> one spec so the migration cannot drift between the package and its consumers —
> the same single-spec discipline the `credential-broker-contract` spec used for
> the reverse migration.

## Objective

A credentialed skill resolving secrets today imports a stdlib-only shim that the
build pipeline byte-copies into its `scripts/` and a drift gate polices. RFC-0023
replaces that machinery with **`credbroker`** — a standalone, pip-installable
Python library consumed **in-process**. For the agent and the human running a
credentialed skill, resolution behaves identically: `load_credentials(namespace,
required_keys)` resolves env → OS keyring → dotfile with the same exceptions and
the same no-leak guarantee (cleartext never crosses a process boundary to the
LLM). What changes for them: (1) installing a credentialed skill now means
`pip install -e ./packages/credbroker` (the five API CLIs already `pip install
httpx`; `credential-setup` gains its first pip dependency), and (2) where
`credbroker[crypto]` is installed, the Tier-3 floor is an **encrypted-at-rest
vault** (Argon2id → KEK → AES-256-GCM) instead of a plaintext dotfile — strong
where an OS keyring holds the master secret, modestly better than plaintext
where there is none. Success is: the six consumers resolve credentials through
`import credbroker` with no behavioural regression, the projection/drift
machinery is gone, and an adopter who cannot `pip install` at all still has the
env Tier-1 floor. **Done** is the six consumers migrated, the gate retired, and
the package's stdlib core + `[crypto]` vault tested on the graceful-degrade
matrix below.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Preserve the shim's full public surface verbatim** — every name in the shim's `__all__`: `load_credentials(namespace, required_keys)`, the `Credentials` container (immutable, value-redacting `__repr__`), the exception classes (`CredentialsMissingError`, `Tier2HardFailError`, `PermissiveAclError`, `SchemaError`, `EnvParseError`), plus `parse_env_file`, `CredsSchema`, `KeyDef`, and `DOTFILE_MAX_BYTES`. For the **five API CLIs** the migration is import-line-only. For **`credential-setup`** it is **not**: it imports the shim's *private* surface today (`_dotfile_write`, `_parse_schema`, `_tier2_backend`, `_tier2_backend_label`). credbroker must give each a **public** home (a write API, a schema-parse API, and a Tier-2-backend introspection API) so credential-setup depends on public `credbroker` symbols, not private ones — see the write-API and credential-setup acceptance criteria.
- **Keep the stdlib core dependency-free.** `credbroker` (no extra) imports only the standard library; `cryptography` + `argon2-cffi` are reachable *only* under the `[crypto]` extra and only when the encrypted-vault path is exercised.
- **Keep resolution in-process.** Consumers `from credbroker import load_credentials`; cleartext stays inside the consumer's interpreter. No subprocess that prints a token, no daemon, no network call.
- **Degrade gracefully and predictably.** Absent the `[crypto]` extra, resolution falls to keyring/plaintext-dotfile (today's floor); absent any OS keyring, the vault master falls to an env var then a 0600 file. The degrade matrix is an acceptance criterion, not an accident.
- **Migrate consumers and retire the gate in the same spec**, in dependency order: the package lands first, then the six consumers swap imports, then the `shared-libs/` projection of `credentials_shim.py` (+ siblings) and its drift gate retire once no consumer declares `auth: creds`/imports the vendored shim.

### Ask first

- **Claiming any of the reserved `3–9` exit codes.** v1 ships no CLI, so the band stays unclaimed; if implementation surfaces a need for a credbroker exit code, surface it — don't claim a number unilaterally.
- **Argon2id cost parameters and the env-vs-file master-secret precedence** in the no-keyring case. RFC-0023 decides the *model* (keyring-sourced master, per-invocation KEK); the *fine* parameters are an implementation choice with a security/latency tradeoff — propose values and get sign-off before pinning them.
- **Touching `sso-broker.py` / `adapter-root-bins/` or the `sso-cookie` broker.** SSO is a different broker with its own transport; credbroker is the `creds` resolver only. If migration appears to require an SSO-side change, stop and ask.

### Never do

- **Never add a daemon, a resident process, a subprocess that prints a credential value, or any network-layer injection.** RFC-0023 Option D (authsome's daemon + MITM proxy) is explicitly out of scope and fails CHARTER Principle 3. (Structural boundary.)
- **Never re-home credentials into `agentbundle`.** `credbroker` is a *separate* package; `agentbundle` shed `agentbundle.credentials` in 0.2.0 on purpose, and `test_credentials_wheel.py` pins that absence. (Structural boundary — no new module under `agentbundle`.)
- **Never publish to PyPI or register the name from this spec's automation.** Defensive PyPI registration and Phase-2 publication are out-of-band user actions; the spec records them, code does not perform them.
- **Never let a credential value reach stdout, stderr, argv, a log line, or an exception message** on any path — the RFC-0006 no-leak invariant the shim already upholds.
- **Never ship the `[crypto]` vault with a hand-rolled cipher** — AEAD comes from `cryptography`'s vetted primitives only.

## Testing Strategy

Each user-visible outcome from the Objective, paired with a mode and why:

- **Public-API parity (`load_credentials`, `Credentials`, exceptions, env→keyring→dotfile order):** **TDD**, exercised by **unit** tests ported from the existing `test_credentials_shim_*.py` suite. The resolution order and the redaction/immutability invariants are compressible logic with a clear pass/fail — port the shim's tests against `import credbroker` so parity is proven, not asserted.
- **Stdlib-core purity (no third-party import without `[crypto]`):** **goal-based check** — an import-graph test that fails if the base package reaches `cryptography`/`argon2`. A one-shot assertion, not a behaviour.
- **`[crypto]` vault round-trip (Argon2id→KEK→AES-256-GCM encrypt/decrypt; wrong-master → fail closed):** **TDD**, **unit** tests gated on the extra being installed (skip-marked when absent). Encryption correctness is a compressible invariant: a value written then read back equals itself; a wrong master never decrypts.
- **Graceful-degrade matrix (extra present/absent × keyring present/absent):** **goal-based check** exercised by **integration** tests that drive `load_credentials` under each environment combination and assert the resolved tier and the no-leak property. Crosses the OS-backend boundary, so it proves out at integration altitude.
- **Six-consumer migration (no behavioural regression):** **goal-based check** — resolution parity is proven by the **ported `credbroker` resolution suite** (the five CLIs ship only `test_exit_codes.py`, which exercises the exit-code taxonomy, *not* resolution, so it is not the parity guard); each CLI's `test_exit_codes.py` stays green for exit-code stability; `credential-setup` ships **no** test today and gains a **new** one (write API + schema-parse + Tier-2 introspection). An import-graph assertion confirms no consumer imports `credentials_shim` and every `_client.py` / `setup.py` imports `credbroker` (no private/underscore names).
- **Gate retirement (drift gate no longer fires, no orphaned projected copies):** **goal-based check** — `make build-check` passes with no `shared-libs`-credentials projection, and a test asserts no `credentials_shim.py` remains in any consumer `scripts/`.

## Acceptance Criteria

- [ ] `packages/credbroker/` exists as a sibling of `packages/agentbundle/` — flat layout, `pyproject.toml` declaring `name = "credbroker"`, `requires-python >= 3.11`, stdlib-only base dependencies, and an optional `[crypto]` extra pulling `cryptography` + `argon2-cffi`.
- [ ] `from credbroker import load_credentials, Credentials, CredentialsMissingError, Tier2HardFailError` resolves, and `load_credentials(namespace, required_keys)` returns the same env→OS-keyring→0600-dotfile resolution (first-hit-wins per key) with the same per-platform Tier-2 backends (`/usr/bin/security`, CredMan) as the shim.
- [ ] The shim's full public surface — every name in its `__all__`: the five exception classes (`CredentialsMissingError`, `Tier2HardFailError`, `PermissiveAclError`, `SchemaError`, `EnvParseError`), `parse_env_file`, `CredsSchema`, `KeyDef`, `DOTFILE_MAX_BYTES` — is importable from `credbroker` with the same semantics; `Credentials` is immutable and its `__repr__` redacts values. The spec pins this full set as `credbroker`'s public API; any shim name *not* re-exported is named in the plan as deliberately internal.
- [ ] `credbroker` exposes **public** replacements for the private shim symbols `credential-setup` consumes today — a schema-parse API (replacing `_parse_schema` → `CredsSchema`/`KeyDef`) and a Tier-2-backend introspection API (replacing `_tier2_backend`/`_tier2_backend_label`) — so `credential-setup` imports no underscore-prefixed `credbroker` name.
- [ ] Importing `credbroker` (without the `[crypto]` extra) imports **no** third-party module; an import-graph test fails if the base package reaches `cryptography` or `argon2`.
- [ ] With `credbroker[crypto]` installed, an encrypted-file vault (Argon2id → KEK → AES-256-GCM-wrapped DEK → encrypted values) round-trips: a value written through the library's write API is read back identical; a wrong/absent master secret fails closed (no plaintext, no partial decrypt) and never leaks the ciphertext or key to stderr.
- [ ] The vault master secret is sourced per RFC-0023's no-daemon model: from the OS keyring (via credbroker's stdlib Tier-2 backend) where one exists; from an env var, then a 0600 file, where none does. The KEK is derived per-invocation; the master is never placed in the process environment by credbroker itself.
- [ ] The graceful-degrade matrix holds: `[crypto]` absent → resolution falls to keyring/plaintext-dotfile (no crash, no import error); keyring absent → vault master falls to env→0600-file; both absent → 0600 plaintext dotfile remains the floor (no worse than today). Each cell is covered by an integration test asserting resolved tier + no leak.
- [ ] All six consumers import `credbroker`: the five API CLIs (`jira`, `jira-align`, `confluence-publisher`, `confluence-crawler`, `figma`) via their `_client.py`, and `credential-setup` directly — and **none** imports `credentials_shim`. An import-graph/grep assertion enforces this.
- [ ] The five API CLIs declare `credbroker` in their `requirements.txt` (beside `httpx`); `credential-setup` gains a `requirements.txt` (or equivalent declared dependency) naming `credbroker` as its first pip dependency.
- [ ] `credential-setup` writes through a `credbroker` library write API (not a direct dotfile write), so the same library that reads the store also writes it; the write API targets the active Tier-3 store (vault when `[crypto]`, else 0600 dotfile).
- [ ] `credential-setup` lands with a **new** regression test (it ships none today): it exercises the credbroker write API (set → read-back), the public schema-parse path, and Tier-2-backend introspection — the three surfaces it migrates onto. This test is co-landed in the migration, not deferred.
- [ ] Resolution parity for the five API CLIs is proven by the ported `credbroker` resolution suite (the unit tests lifted from the shim), **not** by their `test_exit_codes.py` (which exercises the exit-code taxonomy, not resolution). Each CLI's `test_exit_codes.py` additionally stays green after the swap (no exit-code regression).
- [ ] The `shared-libs/` projection of `credentials_shim.py` (+ `_keychain_macos.py`, `_credman_windows.py`) **into the six consumer `scripts/`** is retired: no `credentials_shim.py` remains in any consumer `scripts/`, `make build-check` passes with no `auth: creds` drift outcome, and a test asserts the absence. The `shared-libs/credentials_shim.py` **source file is kept** — it remains the projection source for the `sso-broker` companion shim (adapter-root-bins, AC22b: `_sso_*` modules import `Tier2HardFailError` from it); SSO migration is out of scope (Boundaries → Ask first), so deleting the source would red-fail `make build-check` via the companion rail.
- [ ] `test_credentials_wheel.py` still passes — `credbroker` does not resurrect `agentbundle.credentials`.
- [ ] No credential value appears in stdout, stderr, argv, logs, or any exception message on any failure path (the RFC-0006 no-leak invariant), proven by the ported redaction/`__repr__` tests and the degrade-matrix integration tests.
- [ ] The reserved `3–9` exit band stays unclaimed: credbroker ships no `setup`/`check` CLI in v1, and no consumer's exit-code constants change.
- [ ] **Phase 2 — PyPI publication + version pinning — is deferred** (deferred: credbroker-phase-2). Defensive PyPI name registration is recorded as a user action, not performed by this spec.

## Assumptions

- Technical: `credbroker` lives at `packages/credbroker/`, sibling of `agentbundle`, flat layout (no `src/`), `requires-python >= 3.11`, pytest with `tests/unit` + `tests/integration` (source: `packages/agentbundle/pyproject.toml` + layout).
- Technical: the public API to preserve is `load_credentials(namespace, required_keys)`, `Credentials`, and the five exception classes, with env→OS-keyring(macOS `/usr/bin/security`, Windows CredMan, Linux none)→`0600 ~/.agentbundle/credentials.env` resolution (source: `packs/credential-brokers/.apm/shared-libs/credentials_shim.py`).
- Technical: the six consumers are the five API CLIs (importing via `_client.py`) plus `credential-setup` (importing directly); the five CLIs carry `requirements.txt` with `httpx`, `credential-setup` carries none (source: infra survey of the skill `scripts/` directories).
- Technical: the drift gate is `packages/agentbundle/agentbundle/build/shared_libs.py` (`check_drift`/`apply_projection`), driven by `make build-check`/`build-self`, keyed on `metadata.auth: creds` in SKILL.md; it retires once no consumer declares it (source: `shared_libs.py`).
- Technical: `test_credentials_wheel.py` pins absence of `agentbundle.credentials` and stays valid for a different package (source: `packages/agentbundle/tests/integration/test_credentials_wheel.py`).
- Technical: `cryptography` + `argon2-cffi` are not installed in the dev env — they are the `[crypto]` extra's deps and vault tests skip-mark when absent (source: `python3 -c "import cryptography"` / `import argon2` probe, both ImportError).
- Process: exit-code band is `0 OK / 1 ERROR / 2 USER_ACTION`, `3–9` reserved; credbroker ships no CLI in v1 so the band stays unclaimed (source: `docs/specs/credentialed-cli-exit-code-contract/spec.md`).
- Process: no `docs/architecture/reference.md` — the LLD conforms to the detected repo stack (Python, agentbundle layout precedent) (source: `ls docs/architecture/`).
- Process: credbroker exposes a Python library API, not an openapi/asyncapi/proto/graphql/jsonschema surface, so `Contract: none` (source: no `contracts/` dir; new-spec contract-types map).
- Process: the superseding ADR (reversing ADR-0003) is a separate governance artifact authored in parallel — this spec cites RFC-0023 now and the ADR is added on landing (source: user confirmation 2026-06-03).
- Product: package name is `credbroker` (RFC open question #1, default), Phase 1 only, `[crypto]` vault in-scope but sequenced after the stdlib core, PyPI defensive registration is a user action (source: user confirmation 2026-06-03).
