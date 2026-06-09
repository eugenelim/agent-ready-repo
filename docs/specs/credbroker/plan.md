# Plan: credbroker

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Build `packages/credbroker/` as a sibling of `packages/agentbundle/`, then cut
the six consumers over to it, then retire the projection machinery — in that
order so exactly one resolver is authoritative at every step (the same
sequencing discipline the `credential-broker-contract` spec used for the reverse
migration). The package starts as a near-verbatim lift of the existing
`credentials_shim.py` + its two Tier-2 sibling backends into a real Python
package with a stdlib-only base and an optional `[crypto]` extra; the unit tests
port across with it, so parity is proven on day one. The `[crypto]` vault is
genuinely new code (Argon2id → KEK → AES-256-GCM) and the riskiest part — it is
**sequenced after** the stdlib core so the core + the five-CLI migration can land
without waiting on it. Consumer migration is a mechanical import swap (five CLIs
share one shape via `_client.py`; `credential-setup` is the one that also needs
the vault write API and a new `requirements.txt`). Gate retirement is last and
has a sharp edge: the `shared-libs/credentials_shim.py` source is **also** the
projection source for the `sso-broker` companion shim (adapter-root-bins, AC22b),
so retiring the `auth: creds` projection does **not** automatically license
deleting the source file — see Risks and T9.

## Constraints

- **[RFC-0023](../../rfc/0023-credential-manager-broker.md)** — the canonical proposal; this plan is its Phase-1 implementation. Phase 2 (PyPI) is deferred.
- **Reverses [ADR-0003](../../adr/0003-credential-broker-contract.md)** — the projected-shim decision; the superseding ADR is authored as a separate parallel governance artifact (cite it here when it lands).
- **[RFC-0006](../../rfc/0006-skill-secrets-storage.md)** — storage tiers, Win32 error matrix, atomic-write discipline, and per-platform Tier-2 backends are preserved **verbatim**; this plan changes delivery + adds a vault tier, not the core tier semantics.
- **[RFC-0013](../../rfc/0013-credential-broker-contract.md) / [`credential-broker-contract`](../credential-broker-contract/spec.md)** — the `credentials_shim` public surface and the `shared-libs/` projection mechanism this plan inherits and partially retires.
- **[`credentialed-cli-exit-code-contract`](../credentialed-cli-exit-code-contract/spec.md)** — the reserved `3–9` band stays unclaimed; no consumer's exit constants change. The migration is **import-line-only** for the five CLIs and **does not touch this contract**: the resolver import is lazy (inside `load_credentials()`), so a missing `credbroker` surfaces at runtime → exit 1, the same outcome a missing shim produces today. (Earlier drafts claimed a 1→2 reclassification via the PR #230 import guard; that was wrong — the lazy import never reaches that guard. See Changelog + Risks.)
- **CHARTER Principle 3** — no daemon, no resident process, no network injection (RFC-0023 Option D out of scope).

## Construction tests

**Integration tests:**
- Graceful-degrade matrix (`[crypto]` present/absent × keyring present/absent), driving `load_credentials` per cell and asserting resolved tier + no-leak — spans T2/T5 (cross-cutting; listed here, exercised by T6).
- Six-consumer regression: each migrated consumer's existing suite green after the import swap — spans T7/T8 (each consumer's own test run; no new cross-suite harness).

**Manual verification:** none — every outcome has a goal-based or TDD check.

## Design (LLD)

Shape: **service**. Stack detected from the repo (no `docs/architecture/reference.md`): Python ≥3.11, flat package layout per `packages/agentbundle/`, pytest with `tests/unit` + `tests/integration`, stdlib-only base. Sub-sections pruned to the `service` set.

### Design decisions
- **Verbatim lift of the resolver, not a rewrite.** Tier-1/2/3 logic, the Win32 error matrix, atomic-write, and the `Credentials`/exception surface move byte-for-meaning from `credentials_shim.py`; the alternative (re-derive from spec) risks silent semantic drift the ported tests can't catch. Traces to: AC2, AC3 · contracts: none.
- **`[crypto]` as an optional extra, vault as the Tier-3 implementation when present.** The vault replaces the *plaintext dotfile* at Tier-3; it does not add a tier. Rejected: a fourth tier (complicates first-hit-wins; the floor is still "one dotfile location"). Traces to: AC5, AC7 · contracts: none.
- **No CLI in v1 (pure library).** `credential-setup` stays the interactive write surface; each consumer's own `check` verifies. Rejected: a `credbroker setup` CLI (would claim the `3–9` band prematurely). Traces to: AC15 · contracts: none.

### Interfaces & contracts
The public Python surface (the spec's `Contract: none` — specified here, not under `contracts/`):
- `credbroker.load_credentials(namespace: str, required_keys: list[str]) -> Credentials` — env → OS keyring → Tier-3 (vault if `[crypto]` + present, else plaintext dotfile), first-hit-wins per key.
- `credbroker.Credentials` — immutable attribute-access container, value-redacting `__repr__`.
- `credbroker.{CredentialsMissingError, Tier2HardFailError, PermissiveAclError, SchemaError, EnvParseError}` — re-exported with identical semantics.
- A write API for `credential-setup` — `set`/`store(namespace, key, value)` writing to the active Tier-3 store (vault when `[crypto]`, else 0600 dotfile). Exact name pinned in T4. Replaces credential-setup's private `_dotfile_write`.
- A public **schema-parse** API (`CredsSchema`/`KeyDef` + a parse entry point replacing private `_parse_schema`) and a public **Tier-2 introspection** API (backend handle + label, replacing private `_tier2_backend`/`_tier2_backend_label`) — the other two private surfaces credential-setup consumes. Names pinned in T2/T8. Traces to: AC2, AC3, the credential-setup-public-surface AC, AC9 · contracts: none.

**Import-gating mechanism (load-bearing for AC4 stdlib purity).** `credbroker/__init__.py` and `_core.py` import **only** stdlib. `_vault.py` (which imports `cryptography`/`argon2`) is imported **lazily**, inside the Tier-3 dispatch path of `load_credentials` (and inside the write API), guarded by a `try: import` that raises a clear "install `credbroker[crypto]`" error if absent — never at module top level. So the base import graph provably never reaches a third-party module; the purity test (AC4/T3) asserts against exactly this boundary (`__init__` + `_core` + backends, excluding `_vault`).

### Data & schema
- **Plaintext dotfile** — unchanged: `~/.agentbundle/credentials.env`, mode 0600, `<NAMESPACE>_<KEY>=value` lines.
- **Encrypted vault file** (`[crypto]`) — Argon2id(master, salt) → KEK; AES-256-GCM-wrapped DEK; per-value AES-256-GCM ciphertext + nonce + tag. File location, header/version byte, and salt/nonce layout pinned in T4. Master secret: OS keyring → env var → 0600 file (no-keyring case). Traces to: AC5, AC6 · contracts: none.

### Failure, edge cases & resilience
- **Degrade matrix** is the resilience contract (AC7): missing extra, missing keyring, both missing — each a defined fall-through, none a crash.
- **Wrong/absent master** → fail closed, no partial decrypt, no leak (AC5).
- **Tier-2 hard-fail** (Win32 error matrix) → `Tier2HardFailError`, exit 1 at the consumer, clean stderr (AC2, AC13). Traces to: AC5, AC7, AC13 · contracts: none.

### Quality attributes (NFRs)
- **No-leak invariant** (AC13): no credential value to stdout/stderr/argv/logs/exception text on any path — verified by ported redaction tests + degrade-matrix integration tests.
- **Stdlib-core purity** (AC4): base import graph reaches no third-party module — import-graph test. Traces to: AC4, AC13 · contracts: none.

## Tasks

### T1: `packages/credbroker/` package skeleton exists and installs

**Depends on:** none

**Tests:**
- `pip install -e ./packages/credbroker` succeeds in a clean venv (goal-based).
- `python -c "import credbroker"` succeeds; `pip install -e './packages/credbroker[crypto]'` resolves `cryptography` + `argon2-cffi` (goal-based). Verifies AC1.

**Approach:**
- Create `packages/credbroker/` mirroring `packages/agentbundle/` layout: `pyproject.toml` (`name = "credbroker"`, `requires-python = ">=3.11"`, base `dependencies = []`, `[project.optional-dependencies] crypto = ["cryptography", "argon2-cffi"]`), `credbroker/__init__.py`, `tests/unit/`. (The `tests/integration/` tree + any `conftest.py` arrive with the integration tests they hold — the degrade matrix, T6 — not pre-created as empty scaffolding.)
- No logic yet — just the importable shell + the extra wired.

**Done when:** both installs succeed and `import credbroker` works in CI's matrix; AC1 checkbox justified.

### T2: stdlib core resolves credentials with the shim's public API verbatim

**Depends on:** T1

**Tests:**
- Port `test_credentials_shim_load_credentials.py`, `test_credentials_shim_stdlib.py` against `import credbroker`: env→keyring→dotfile order, first-hit-wins, `Credentials` immutability + `__repr__` redaction, every exception class importable with identical semantics (TDD, unit). Verifies AC2, AC3, AC13.
- Public-surface test: all 11 `__all__` names (`load_credentials`, `Credentials`, the 5 exceptions, `parse_env_file`, `CredsSchema`, `KeyDef`, `DOTFILE_MAX_BYTES`) import from `credbroker` (goal-based, unit). Verifies AC3.
- Import-graph test: base `credbroker` reaches no third-party module (goal-based, unit). Verifies AC4.
- Note: `test_credentials_shim_bin_load_degradation.py` is **not** ported — it pins the AC22c degradation of the *shared-libs* shim under `~/.agentbundle/bin/` and stays bound to the surviving `shared-libs/credentials_shim.py` source (it's part of the sso-broker companion contract, not credbroker's). See T9.

**Approach:**
- Lift `credentials_shim.py` + `_keychain_macos.py` + `_credman_windows.py` into `credbroker/` (`credbroker/_core.py` + `credbroker/_keychain_macos.py` + `credbroker/_credman_windows.py`), re-exporting the full `__all__` from `credbroker/__init__.py`.
- Promote the schema-parse and Tier-2-introspection surfaces credential-setup needs (today `_parse_schema`/`_tier2_backend`/`_tier2_backend_label`) to **public** names so T8 imports no underscore-prefixed symbol.
- Preserve the Win32 error matrix, atomic-write, DACL check, and Tier-2 dispatch-at-load exactly. Keep `_tier2_backend = None` on Linux.

**Done when:** ported suites green; public-surface + import-graph tests green; `grep` shows the full `__all__` re-exported from `__init__` and a public schema/introspection surface present.

### T3: stdlib-purity gate is a standing test

**Depends on:** T2

**Tests:**
- The import-graph test from T2 is promoted to a named regression test that fails loudly if any base-package module gains a `cryptography`/`argon2` import (goal-based). Verifies AC4.

**Approach:**
- Walk `credbroker`'s base modules' import graph (AST or `importlib`), assert the third-party set is empty unless the module is under the crypto-gated path.

**Done when:** test green; deliberately adding a top-level `import cryptography` to a base module turns it red (verified once, then reverted).

### T4: `[crypto]` vault encrypts and decrypts; wrong master fails closed

**Depends on:** T2

**Tests:**
- Round-trip: a value written via the write API and read back equals itself (TDD, unit, `[crypto]`-gated/skip-marked when absent). Verifies AC5, AC9.
- Wrong/absent master → fail closed: no plaintext, no partial decrypt, no ciphertext/key on stderr (TDD, unit). Verifies AC5, AC13.

**Approach:**
- Add `credbroker/_vault.py` (only imported under `[crypto]`): Argon2id(master, salt)→KEK; AES-256-GCM-wrapped DEK; per-value AES-256-GCM. Use `cryptography`'s AEAD only — no hand-rolled cipher.
- Define the write API (`set`/`store`) and the vault file format (version byte, salt, wrapped DEK, entries). **Surface Argon2id cost parameters for sign-off (spec Boundaries → Ask first) before pinning.**

**Done when:** round-trip + fail-closed tests green with the extra installed; tests skip cleanly without it.

### T5: vault master-secret unlock follows the no-daemon model; vault is Tier-3 when present

**Depends on:** T4

**Tests:**
- Master sourced from OS keyring where present; falls to env var then 0600 file where absent; KEK derived per-invocation; master never placed in process env by credbroker (TDD/goal-based, unit, `[crypto]`-gated). Verifies AC6.
- With `[crypto]` present, `load_credentials` Tier-3 reads the vault, not the plaintext dotfile (integration). Verifies AC5, AC7.

**Approach:**
- Wire the unlock chain (keyring→env→0600 file) into vault open; derive KEK per call.
- Make `load_credentials`'s Tier-3 dispatch to the vault when `[crypto]` is installed and a vault exists, else the plaintext dotfile. **Surface env-vs-file precedence for sign-off (spec Boundaries → Ask first).**

**Done when:** unlock-source tests green; Tier-3-reads-vault integration test green.

### T6: graceful-degrade matrix holds across all four cells

**Depends on:** T5

**Tests:**
- Integration tests for `[crypto]` present/absent × keyring present/absent: assert resolved tier and no-leak per cell; both-absent → 0600 plaintext floor, no crash (goal-based, integration). Verifies AC7, AC13.

**Approach:**
- Parametrize an integration harness that simulates each environment (extra import availability, keyring backend presence) and drives `load_credentials`.

**Done when:** all four cells pass; removing the extra in CI still resolves via keyring/dotfile.

### T7: the five API CLIs import credbroker and declare the dependency

**Depends on:** T2

**Touches:** packs/atlassian/.apm/skills/*/scripts/_client.py, packs/atlassian/.apm/skills/*/requirements.txt, packs/figma/.apm/skills/figma/scripts/_client.py, packs/figma/.apm/skills/figma/requirements.txt

**Tests:**
- Resolution parity proven by the ported `credbroker` suite (T2), not by the CLIs' own tests; each CLI's `test_exit_codes.py` additionally stays green after the swap (goal-based). Verifies the five-CLI parity AC + the exit-code-stable AC. *(Note: PR #230 rewrote these five test files — canonical-six argv-ban loop + source guards + forced UTF-8; the swap must keep them green against the newer files.)*
- Behaviour-preservation: with `credbroker` uninstalled, invoking a command exits **1** (the top-level `except Exception`) with a clean message and no traceback — identical to a missing projected shim today — exercised per CLI by forcing the resolver import to fail (goal-based). Verifies the exit-1-preserved AC.
- Import-graph/grep assertion: each `_client.py` imports from `credbroker`, none imports `credentials_shim` (goal-based). Verifies AC8.

**Approach:**
- In each skill's `_client.py`, swap the **lazy** `from .credentials_shim import …` (inside `load_credentials()`, e.g. `jira/_client.py:652`) → `from credbroker import …`. **The import stays lazy** — `_client.py`'s module body imports only stdlib + `httpx`, and the resolver is imported at call time inside `load_credentials()` (a deliberate design so the CLI parses args / shows `--help` without the resolver, and the test harness can stub it). A missing `credbroker` therefore surfaces at **runtime** → the top-level `except Exception` → exit 1, the same path a missing projected shim takes today. **No exit-code-contract change**: the contract's "missing resolver → 1" outcome is preserved; this migration does not move it to exit 2 and does not touch the entry-script import guard.
- Append `credbroker` to each skill's **skill-root** `requirements.txt` (beside `httpx`) — `packs/atlassian/.apm/skills/{jira,jira-align,confluence-publisher,confluence-crawler}/requirements.txt` and `packs/figma/.apm/skills/figma/requirements.txt`. All five already exist; none lives under `scripts/`.
- *(Out of scope / see Risks: making a missing `credbroker` exit 2 with a "pip install" hint — for parity with the top-level `httpx` guard — would require hoisting the resolver import to module level, a deliberate structural change against the lazy-import design. Not done here; a decision item, not a silent change.)*
- **Update the `auth: creds` resolver-import lint** (re-plan discovery, 2026-06-08): `tools/lint_credentialed_skills.py` (AC25 broker walk) required `from .credentials_shim import …` for every `auth: creds` skill; swapping the five CLIs to `from credbroker import …` trips it. Add `has_credbroker_import` and accept **either** the credbroker import (RFC-0023) or the legacy shim import (consumers migrate skill-by-skill; `credential-setup` keeps the shim until T8). Add a positive test case to `tools/test-lint-credentialed-skills.py`. `make build-check` red-fails without this.

**Done when:** the five `test_exit_codes.py` suites green (with runtime deps installed); ported resolution suite green; grep shows zero `credentials_shim` imports in the five CLIs; `credbroker` in all five skill-root requirements files; `make build-check` green (the resolver-import lint accepts credbroker).

### T8: `credential-setup` imports credbroker and writes through its vault API

**Depends on:** T2, T4

**Touches:** packages/credbroker/credbroker/{__init__.py, _core.py, _vault.py}, packages/credbroker/tests/unit/test_write_api.py (new), packs/credential-brokers/.apm/skills/credential-setup/scripts/setup.py, packs/credential-brokers/.apm/skills/credential-setup/scripts/test_setup.py (new), packs/credential-brokers/.apm/skills/credential-setup/requirements.txt (new)

**Public write API added to credbroker** (the surface credential-setup's private imports map onto; `parse_schema`/`tier2_backend_label`/exceptions already public since T2). All non-interactive — the library never prompts; credential-setup owns the interactive policy:
- `keyring_available() -> bool` — a Tier-2 backend is loaded (replaces `_tier2_backend is None`). _core (stdlib).
- `store_in_keyring(namespace, key, value) -> None` — write via the Tier-2 backend; raises `Tier2HardFailError`/`PermissiveAclError`; raises if no backend (replaces `_tier2_backend.write_credential`). _core (stdlib).
- `store_in_dotfile(namespace, key, value, *, allow_permissive_acl=False) -> None` — public Tier-3 plaintext write (public name for `_dotfile_write`). _core (stdlib).
- `crypto_available() -> bool` — the `[crypto]` extra is importable (`importlib.util.find_spec`; stdlib, doesn't import cryptography). _core.
- `source_vault_master() -> str | None` — public wrapper of the keyring→env→file sourcing (T5). _core (stdlib).
- `store_vault_master(master) -> None` — persist the vault master so a later `load_credentials` Tier-3 read can re-source it. **Keyring-first** (pre-EXECUTE review Concern 2): write to the OS keyring when `keyring_available()`, else the `0600` `vault.master` file (atomic, `fchmod 0o600` *before* `os.replace`, so it round-trips with `_source_vault_master`'s reject-on-group/other-readable check). Never writes the master to disk when a keyring exists — matches the keyring→env→file precedence. The master only lands on disk on a genuinely no-keyring box, the same posture AC6 already blessed for the file tier. _core (stdlib).
- `store_in_vault(namespace, key, value, *, master) -> None` — encrypted Tier-3 write; **lazily** imports `_vault` (crypto-gated) so base purity (AC4) holds. It is the *sole* public write entry point for the vault; `_vault.set_credential` stays private-by-convention (not re-exported — Concern 4).

**Naming (Concern 5, settled):** the write surface is `store_in_<tier>` (names the tier); the read side stays the inherited `load_credentials` (one resolver-read). The verb asymmetry (one `load_credentials`, per-tier `store_in_*`) is **intentional**, not drift.

**credential-setup orchestration — decision (a), full encrypted-setup UX** (signed off 2026-06-08):
- `keyring_available()` and not `--allow-insecure-fallback` → `store_in_keyring` (Tier-2 default). *(unchanged)*
- else (no keyring, or `--allow-insecure-fallback`) → Tier-3 fallback:
  - if `crypto_available()`: `master = source_vault_master()`; if `None` → **prompt** (getpass, no echo) for a new master and `store_vault_master(master)`; then `store_in_vault(...)`; report "wrote to encrypted vault".
  - else → `store_in_dotfile(...)`; report "wrote to dotfile (plaintext — install `credbroker[crypto]` for an encrypted floor)".
- `_parse_schema`→`parse_schema`, `_tier2_backend_label`→`tier2_backend_label`, exceptions → re-exported public classes.

**Tests:**
- `test_write_api.py` (credbroker unit): `keyring_available`/`store_in_keyring` (fake backend + hard-fail path), `store_in_dotfile` round-trip, `crypto_available`, `source_vault_master`/`store_vault_master` round-trip (asserts `0600`), `store_in_vault` round-trip ([crypto]-gated). Purity gate still green (additions are stdlib; `store_in_vault` lazy).
- `test_setup.py` (new): the three orchestration paths — keyring write (fake backend); no-keyring+`[crypto]` → vault write with a mocked master prompt establishing `vault.master`; no-keyring+no-`[crypto]` → dotfile. Plus a grep/import assertion: `setup.py` imports `credbroker`, **no** `credentials_shim`, **no** underscore-prefixed `credbroker` name. Verifies the credential-setup-test AC, the public-surface AC, AC8, AC9.

**Done when:** the public write API is exported + unit-tested (purity gate still green); `setup.py` rebinds onto it (zero private/`credentials_shim` imports); the no-keyring+`[crypto]` path prompts→establishes→uses the vault master; `test_setup.py` green; skill-root `requirements.txt` (naming `credbroker`) present; `make build-check` green.

### T9: retire the `auth: creds` shared-libs projection + its drift gate

**Depends on:** T7, T8

**Touches:** packages/agentbundle/agentbundle/build/shared_libs.py, packages/agentbundle/agentbundle/build/self_host.py, packages/agentbundle/agentbundle/build/tests/test_shared_libs_projection.py, packages/agentbundle/agentbundle/_data/adapter.toml, packs/atlassian/.apm/skills/*/scripts/credentials_shim.py, packs/figma/.apm/skills/figma/scripts/credentials_shim.py, packs/credential-brokers/.apm/skills/credential-setup/scripts/, packs/credential-brokers/.apm/skills/credential-setup/SKILL.md

**Tests:**
- No `credentials_shim.py` (or `_keychain_macos.py`/`_credman_windows.py`) remains in any of the six consumer `scripts/` dirs (goal-based). Verifies AC11.
- `make build-check` passes with no `auth: creds` drift outcome; `test_shared_libs_projection.py` updated to reflect the retired creds projection (goal-based). Verifies AC11.
- `test_credentials_shim_bin_load_degradation.py` still passes, still bound to the surviving `shared-libs/credentials_shim.py` source (goal-based). Verifies the source-kept AC.
- `test_credentials_wheel.py` still passes (goal-based). Verifies AC12.

**Approach:**
- **Premise correction (EXECUTE-time, 2026-06-09 — see Changelog).** The six consumers **still declare `auth: creds`** after T7/T8, and that is correct: they are still `creds`-broker skills (the credentialed-skill lint, extended in T7, now accepts the `credbroker` import for an `auth: creds` skill, and the CONVENTIONS broker taxonomy still defines `creds`). So T9 does **not** drop the `auth: creds` frontmatter. Instead it **retires the skill-scripts projection mechanism itself**: the projection is no longer driven, the consumers resolve via the `credbroker` pip dep.
- Retire the *skill-scripts projection half* of `shared_libs.py` — `find_creds_consumers`, `compute_projections`, `apply_projection`, `check_drift`, `_enumerate_existing_projections`, `_skill_declares_auth_creds`, `_AUTH_CREDS_RE`, `KNOWN_SHIM_BASENAMES`, `SharedLibProjection`. **Keep `collect_sources` + `SOURCE_SUBDIR`** — they are the *only* surviving role of the module: `adapter_root_bins.py` calls `shared_libs.collect_sources` and reads `shared_libs.SOURCE_SUBDIR` for the AC22b companion-shim projection + the inter-pack collision rail.
- Remove the two `self_host.py` call sites: `_shared_libs_apply(packs_dir)` (build-self projection step) and `_shared_libs_check_drift(packs_dir)` (build-check drift gate). After removal `make build-self` no longer fans the shim into skill `scripts/`, and `make build-check` reports no `auth: creds` drift.
- `git rm` the 18 projected copies (6 consumer `scripts/` × `credentials_shim.py` + `_keychain_macos.py` + `_credman_windows.py`). Build-self will no longer re-create them.
- Reword the now-stale `[primitive."shared-libs"]` comment in `_data/adapter.toml` (it asserts the projection-into-`auth: creds`-skills behaviour that is being retired) to describe its surviving role: the source for the adapter-root-bins companion shim.
- Reword the stale "build-projected `credentials_shim`" sentence in `credential-setup/SKILL.md` § "Inverse — verifying resolution" (the consumer's `check` now resolves through `import credbroker`, not the projected sibling).
- **Sharp edge (confirmed, see Risks): KEEP `packs/credential-brokers/.apm/shared-libs/credentials_shim.py` (+ `_keychain_macos.py`/`_credman_windows.py`).** It is the projection source for the `sso-broker` companion shim — `_sso_keychain_macos.py` / `_sso_credman_windows.py` do `from .credentials_shim import Tier2HardFailError`, and `adapter_root_bins.py::_assert_shim_companion_present` hard-fails `make build-check` if the source is gone. SSO migration is out of scope (spec Boundaries → Ask first). This task retires the **creds-consumer projection**, not the source file.
- Rewrite `test_shared_libs_projection.py` for the retired state: keep the `collect_sources` enumeration + inter-pack-collision tests (the surviving surface), drop every test of the retired projection/drift/orphan machinery, and add a **standing real-tree absence test** — no `credentials_shim.py`/`_keychain_macos.py`/`_credman_windows.py` in any `packs/*/.apm/skills/*/scripts/` (the AC's "a test asserts the absence"), plus an assertion the `shared-libs/` **source** is retained for the companion rail. This absence test replaces the retired orphan-drift gate as the standing net.

**Done when:** no shim copy in the six consumer `scripts/`; `make build-check` green; bin-load + wheel tests green; the source file is retained and the companion rail still passes.

### T10: docs, conventions, and backlog reflect the migration

**Depends on:** T7, T8, T9

**Touches:** docs/guides/how-to/add-a-credentialed-skill.md, docs/CONVENTIONS.md, docs/backlog.md

**Tests:**
- `docs/backlog.md` carries a literal `### credbroker-phase-2` heading (the kebab anchor verbatim, matching the spec's `(deferred: credbroker-phase-2)` marker) under a `## credbroker` section (goal-based). Verifies the deferred-AC anchor invariant (`lint-spec-status`).
- Doc-drift / link lints pass (goal-based).

**Approach:**
- `docs/guides/how-to/add-a-credentialed-skill.md` (repo-owned, edit directly): rewrite **every** stale shim/projection site, not only Step 6/8 (pre-EXECUTE review Blocker 2). Known sites: line 5 (intro "projected `credentials_shim`"), Step 1 `creds` bullet (~line 23), Step 6 (~90–99, 127 → `pip install credbroker` + `from credbroker import …`, drop "build pipeline projects … into your scripts/"), Step 8 `ModuleNotFoundError: credentials_shim` failure guidance (~239–242, 261–263 → `ModuleNotFoundError: credbroker` → `pip install`), **Step 9 retired** (~278–284 — "run `make build-self` projects credentials_shim" is obsolete for `auth: creds`; the resolver now arrives via `pip install credbroker` from `requirements.txt`), Step 11 lint description (~311) and Common-pitfalls (~321–322). Add the `[crypto]` extra note per RFC-0023.
- `packs/core/seeds/docs/CONVENTIONS.md` § Credentialed skills (**edit the seed, not the projected `docs/CONVENTIONS.md`** — it is the one seed-projected doc; then `make build-self`): (a) the `creds` bullet (~1051–1054) → "Resolved via the `credbroker` library (`pip install credbroker`), imported in-process (RFC-0023)" with a one-line forward-pointer so a reader doesn't take ADR-0003's projected-shim mechanism as current (Concern 5); (b) the broker-agnostic lint parenthetical (~1062) → "`auth: creds` requires a credential-resolver import (`from credbroker import …` (RFC-0023) or the legacy projected `credentials_shim`)" to match the T7-extended lint (Blocker 3). Leave the ADR-0003 four-broker *taxonomy* attribution (~1041) untouched — RFC-0023 reverses the delivery, not the taxonomy. **This implements the change RFC-0023 already authorized as a named follow-on** — trace the edit to RFC-0023 in the PR body; note the superseding ADR is pending.
- `docs/backlog.md`: **verify** (not add — Concern 4) the existing `## credbroker` section + `### credbroker-phase-2` heading (landed in #242) still resolves the spec's `(deferred: credbroker-phase-2)` marker; confirm the listed items remain accurate.
- **Closing step — ship the spec atomically (Blocker 1).** In this same PR flip `spec.md` Status `Implementing` → `Shipped` and resolve every remaining `- [ ]` AC: check the import/projection-retired/wheel-test/3–9-band ACs as `- [x]`, and leave the Phase-2 AC carrying its `(deferred: credbroker-phase-2)` marker. T9/T10 are the terminal Phase-1 tasks, so spec + code ship together — not a forward-claim.
- **Deferred docs (record in PR body, Concern 6):** `docs/architecture/credentials.md` and `docs/guides/how-to/install-agentbundle-from-clone.md` carry stale shim/projection prose but are out of this plan's named T10 scope and not same-directory ride-alongs; defer with a one-line reason. Check `docs/architecture/overview.md:86` — if T9 makes its one-liner about `credentials.md` factually wrong, fix that single line as a same-area ride-along.

**Done when:** backlog anchor resolves (`lint-spec-status` green); guide + CONVENTIONS seed read `import credbroker` with no stale projection text; `docs/CONVENTIONS.md` regenerated via `make build-self`; spec Status `Shipped` with all ACs checked/deferred; doc lints green.

## Rollout

- **Delivery:** big-bang within the repo, but internally sequenced — package (T1–T6) → consumer cutover (T7–T8) → gate retirement (T9) → docs (T10). Reversible until T9: before the projection is removed, the shim and `credbroker` can coexist (a consumer reverts by restoring its import line). T9 is the point of no easy return for the in-repo consumers.
- **Infrastructure:** none new in-repo. External: defensive PyPI name registration is a **user action** (out of scope for automation, spec Boundaries → Never do); Phase 2 PyPI publication is deferred.
- **External-system integration:** none for Phase 1 (repo-path install only). Phase 2 introduces the PyPI dependency for plugin adopters who have no repo.
- **Deployment sequencing:** consumers must import `credbroker` (T7/T8) **before** the projection is retired (T9), or the build breaks; the package (T2) must exist before any consumer imports it.

## Risks

- **`sso-broker` companion-shim coupling.** `shared-libs/credentials_shim.py` is also the projection source for the `sso-broker` companion shim (adapter-root-bins, AC22b: `from .credentials_shim import Tier2HardFailError`). The `creds`-consumer migration does **not** migrate SSO (out of scope, spec Boundaries → Ask first), so retiring the `auth: creds` projection may leave the **source file** alive solely for the companion projection. T9 must distinguish "retire the creds projection" from "delete the source" and surface the latter rather than assume it.
- **`[crypto]` extra absent in CI or dev.** Vault tests must skip cleanly (not fail) when `cryptography`/`argon2-cffi` aren't installed; the degrade matrix must still exercise the no-extra cells. Mitigation: skip-markers + an explicit `[crypto]`-installed CI cell.
- **Verbatim-lift drift.** A subtle semantic change during the lift (T2) that the ported tests don't cover. Mitigation: lift the *tests* alongside the code unchanged; diff the lifted module against the shim source for non-cosmetic deltas.
- **Exit-code inconsistency for a missing resolver (decision item, deliberately deferred).** After migration, a missing top-level dep (`httpx`) exits 2 ("pip install") via the entry-script guard, but a missing `credbroker` — imported lazily inside `load_credentials()` — exits 1 at runtime. Both are "clean exit, no traceback", but the codes differ. Making them consistent (missing `credbroker` → 2) requires hoisting the resolver import to module level, which (a) breaks the deliberate lazy-import design (args/`--help`/test-stubbing without the resolver) and (b) would be a real behaviour change to a shipped contract. **Not done in Phase 1** — surfaced as a decision; if pursued it gets its own task + an explicit, dated amendment to the exit-code-contract spec, not a silent ride-along.

## Changelog

- 2026-06-04: initial plan. Phase-1 scope (per RFC-0023 + user confirmation); `[crypto]` sequenced after the stdlib core; sso-broker companion-shim coupling flagged as the T9 sharp edge.
- 2026-06-09: T9/T10 EXECUTE-time premise correction. The original T9 approach assumed the migration would leave the six consumers no longer declaring `auth: creds`; the as-built T7/T8 (correctly) kept the `auth: creds` frontmatter (they remain `creds`-broker skills; the T7-extended credentialed-skill lint accepts the `credbroker` import). T9's mechanism is therefore *retire the skill-scripts projection in `shared_libs.py` + remove the two `self_host.py` call sites + `git rm` the 18 copies*, **not** drop the frontmatter; `collect_sources`/`SOURCE_SUBDIR` survive for the `adapter_root_bins` companion rail. Added `self_host.py`, `_data/adapter.toml`, and `credential-setup/SKILL.md` to Touches. Governance note: the superseding ADR (reversing ADR-0003) has **not** landed; the T10 `CONVENTIONS.md` delivery-prose edit traces to the Accepted RFC-0023 and is surfaced as a flagged decision, with the ADR-0003 *taxonomy* attribution left untouched.
- 2026-06-04: post-rebase onto PR #230. Initially folded in an exit-code "reclassification" (missing `credbroker` → exit 2 via #230's import guard). **Reverted same day** — adversarial re-review showed the premise was false: each `_client.py` imports the resolver *lazily inside `load_credentials()`*, so a missing `credbroker` surfaces at runtime → exit 1 (top-level handler), never reaching the entry-script guard. Corrected to: import-line-only, exit-1 preserved, **no** exit-code-contract amendment. The exit-2 "pip install" UX would need a deliberate import hoist (Risks → decision item), not part of this migration.
