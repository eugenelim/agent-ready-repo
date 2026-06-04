# Plan: credbroker

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

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
- **[`credentialed-cli-exit-code-contract`](../credentialed-cli-exit-code-contract/spec.md)** — the reserved `3–9` band stays unclaimed; no consumer's exit *constants* change. But the migration **amends** its "unprojected shim `ModuleNotFoundError` → exit 1" clause: a missing `credbroker` (now a pip dependency) is a missing dependency → exit **2** via the import guard PR #230 standardized. T7 records the amendment on that spec; the clause's residual scope is the `sso-broker` companion path.
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
- Create `packages/credbroker/` mirroring `packages/agentbundle/` layout: `pyproject.toml` (`name = "credbroker"`, `requires-python = ">=3.11"`, base `dependencies = []`, `[project.optional-dependencies] crypto = ["cryptography", "argon2-cffi"]`), `credbroker/__init__.py`, `tests/unit/`, `tests/integration/`, `conftest.py`.
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

**Touches:** packs/atlassian/.apm/skills/*/scripts/_client.py, packs/atlassian/.apm/skills/*/requirements.txt, packs/figma/.apm/skills/figma/scripts/_client.py, packs/figma/.apm/skills/figma/requirements.txt, docs/specs/credentialed-cli-exit-code-contract/spec.md

**Tests:**
- Resolution parity proven by the ported `credbroker` suite (T2), not by the CLIs' own tests; each CLI's `test_exit_codes.py` additionally stays green after the swap (goal-based). Verifies the five-CLI parity AC + the exit-code-stable AC. *(Note: PR #230 rewrote these five test files — canonical-six argv-ban loop + source guards + forced UTF-8; the swap must keep them green against the newer files.)*
- A missing `credbroker` (uninstalled) yields **exit 2** + "run pip install", not a traceback or exit 1 — exercised per CLI by forcing the import to fail (goal-based). Verifies the missing-`credbroker`→2 AC.
- Import-graph/grep assertion: each `_client.py` imports from `credbroker`, none imports `credentials_shim` (goal-based). Verifies AC8.

**Approach:**
- In each skill's `_client.py`, swap `from .credentials_shim import …` → `from credbroker import …`. The CLI entry-point already wraps `from ._client import (… load_credentials …)` in an import guard (PR #230); since `_client.py`'s failure propagates to that guard, a missing `credbroker` is caught there → exit 2 + "run pip install -r requirements.txt". Verify the guard still catches it (no path where the `credbroker` import escapes the guard as a raw `ModuleNotFoundError`/exit 1).
- Append `credbroker` to each skill's **skill-root** `requirements.txt` (beside `httpx`) — `packs/atlassian/.apm/skills/{jira,jira-align,confluence-publisher,confluence-crawler}/requirements.txt` and `packs/figma/.apm/skills/figma/requirements.txt`. All five already exist; none lives under `scripts/`.
- **Record the exit-code-contract amendment**: add a dated `## Changelog` (or `## Errata`) entry to `docs/specs/credentialed-cli-exit-code-contract/spec.md` noting that the "unprojected shim `ModuleNotFoundError` → exit 1" clause no longer applies to the five migrated CLIs (a missing `credbroker` → exit 2, the missing-dependency class); residual scope is the `sso-broker` companion path. Don't silently drift a shipped spec.

**Done when:** the five `test_exit_codes.py` suites green; ported resolution suite green; missing-`credbroker`→2 verified per CLI; grep shows zero `credentials_shim` imports in the five CLIs; `credbroker` in all five skill-root requirements files; the exit-code-contract amendment recorded.

### T8: `credential-setup` imports credbroker and writes through its vault API

**Depends on:** T2, T4

**Touches:** packs/credential-brokers/.apm/skills/credential-setup/scripts/setup.py, packs/credential-brokers/.apm/skills/credential-setup/scripts/test_setup.py, packs/credential-brokers/.apm/skills/credential-setup/requirements.txt

**Tests (new — credential-setup ships none today):**
- A new `test_setup.py`: credbroker write API set → read-back; public schema-parse path (`CredsSchema`/`KeyDef`); Tier-2-backend introspection returns the expected label per platform (TDD/unit). Verifies the credential-setup-test AC, AC9, the credential-setup-public-surface AC.
- Grep/import-graph: `setup.py` imports `credbroker`, imports **no** `credentials_shim` and **no** underscore-prefixed `credbroker` name (goal-based). Verifies AC8.

**Approach:**
- `setup.py` today imports the shim's **private** surface: `_dotfile_write`, `_parse_schema`, `_tier2_backend`, `_tier2_backend_label` (plus `PermissiveAclError`, `SchemaError`, `Tier2HardFailError`). Swap each onto credbroker's **public** equivalents: writes → the write API (T4); `_parse_schema` → the public schema-parse API (T2); `_tier2_backend`/`_tier2_backend_label` → the public Tier-2 introspection API (T2); exceptions → the re-exported public classes.
- This is the only consumer whose migration is more than an import swap — it's a private→public surface rebind plus a new write path.
- Add `requirements.txt` at the **skill root** (`packs/credential-brokers/.apm/skills/credential-setup/requirements.txt`) naming `credbroker` — its first pip dependency.

**Done when:** new `test_setup.py` green; grep shows the write path through `credbroker` and zero private/`credentials_shim` imports; skill-root `requirements.txt` present.

### T9: retire the `auth: creds` shared-libs projection + its drift gate

**Depends on:** T7, T8

**Touches:** packages/agentbundle/agentbundle/build/shared_libs.py, packages/agentbundle/agentbundle/build/tests/test_shared_libs_projection.py, packs/atlassian/.apm/skills/*/scripts/credentials_shim.py, packs/figma/.apm/skills/figma/scripts/credentials_shim.py, packs/credential-brokers/.apm/skills/credential-setup/scripts/

**Tests:**
- No `credentials_shim.py` (or `_keychain_macos.py`/`_credman_windows.py`) remains in any of the six consumer `scripts/` dirs (goal-based). Verifies AC11.
- `make build-check` passes with no `auth: creds` drift outcome; `test_shared_libs_projection.py` updated to reflect the retired creds projection (goal-based). Verifies AC11.
- `test_credentials_shim_bin_load_degradation.py` still passes, still bound to the surviving `shared-libs/credentials_shim.py` source (goal-based). Verifies the source-kept AC.
- `test_credentials_wheel.py` still passes (goal-based). Verifies AC12.

**Approach:**
- Since the six consumers no longer declare `auth: creds` (their resolution moved to the `credbroker` pip dep), the `shared-libs/` projector stops targeting them. Remove the projected shim copies from the six `scripts/` dirs; if the `auth: creds` SKILL.md frontmatter is what drives projection, drop/adjust it per the migration so the projector and drift gate no longer fan the shim into `scripts/`.
- **Sharp edge (confirmed, see Risks): KEEP `packs/credential-brokers/.apm/shared-libs/credentials_shim.py` (+ `_keychain_macos.py`/`_credman_windows.py`).** It is the projection source for the `sso-broker` companion shim — `_sso_keychain_macos.py` / `_sso_credman_windows.py` do `from .credentials_shim import Tier2HardFailError`, and `adapter_root_bins.py::_assert_shim_companion_present` hard-fails `make build-check` if the source is gone. SSO migration is out of scope (spec Boundaries → Ask first). This task retires the **creds-consumer projection**, not the source file.
- Update `shared_libs.py` orphan/known-basenames logic + `test_shared_libs_projection.py` so retiring the creds projection while keeping the source (for the companion rail) is the expected, tested state — not a drift error.

**Done when:** no shim copy in the six consumer `scripts/`; `make build-check` green; bin-load + wheel tests green; the source file is retained and the companion rail still passes.

### T10: docs, conventions, and backlog reflect the migration

**Depends on:** T7, T8, T9

**Touches:** docs/guides/how-to/add-a-credentialed-skill.md, docs/CONVENTIONS.md, docs/backlog.md

**Tests:**
- `docs/backlog.md` carries a literal `### credbroker-phase-2` heading (the kebab anchor verbatim, matching the spec's `(deferred: credbroker-phase-2)` marker) under a `## credbroker` section (goal-based). Verifies the deferred-AC anchor invariant (`lint-spec-status`).
- Doc-drift / link lints pass (goal-based).

**Approach:**
- `docs/guides/how-to/add-a-credentialed-skill.md`: Step 6 → `import credbroker`; Step 8 → `pip install credbroker[crypto]` (per RFC-0023 follow-on).
- `docs/CONVENTIONS.md` § Credentialed skills: `auth: creds` resolves via `import credbroker`, not the vendored shim. **This implements the change RFC-0023 already authorized as a named follow-on** — not a fresh convention; trace the edit to RFC-0023 in the PR body.
- `docs/backlog.md`: add a `## credbroker` section with a `### credbroker-phase-2` sub-heading (PyPI publication, version pinning, plugin-adopter cutover) and the defensive-PyPI-registration user action.

**Done when:** backlog anchor resolves; guide + CONVENTIONS read `import credbroker`; doc lints green.

## Rollout

- **Delivery:** big-bang within the repo, but internally sequenced — package (T1–T6) → consumer cutover (T7–T8) → gate retirement (T9) → docs (T10). Reversible until T9: before the projection is removed, the shim and `credbroker` can coexist (a consumer reverts by restoring its import line). T9 is the point of no easy return for the in-repo consumers.
- **Infrastructure:** none new in-repo. External: defensive PyPI name registration is a **user action** (out of scope for automation, spec Boundaries → Never do); Phase 2 PyPI publication is deferred.
- **External-system integration:** none for Phase 1 (repo-path install only). Phase 2 introduces the PyPI dependency for plugin adopters who have no repo.
- **Deployment sequencing:** consumers must import `credbroker` (T7/T8) **before** the projection is retired (T9), or the build breaks; the package (T2) must exist before any consumer imports it.

## Risks

- **`sso-broker` companion-shim coupling.** `shared-libs/credentials_shim.py` is also the projection source for the `sso-broker` companion shim (adapter-root-bins, AC22b: `from .credentials_shim import Tier2HardFailError`). The `creds`-consumer migration does **not** migrate SSO (out of scope, spec Boundaries → Ask first), so retiring the `auth: creds` projection may leave the **source file** alive solely for the companion projection. T9 must distinguish "retire the creds projection" from "delete the source" and surface the latter rather than assume it.
- **`[crypto]` extra absent in CI or dev.** Vault tests must skip cleanly (not fail) when `cryptography`/`argon2-cffi` aren't installed; the degrade matrix must still exercise the no-extra cells. Mitigation: skip-markers + an explicit `[crypto]`-installed CI cell.
- **Verbatim-lift drift.** A subtle semantic change during the lift (T2) that the ported tests don't cover. Mitigation: lift the *tests* alongside the code unchanged; diff the lifted module against the shim source for non-cosmetic deltas.

## Changelog

- 2026-06-04: initial plan. Phase-1 scope (per RFC-0023 + user confirmation); `[crypto]` sequenced after the stdlib core; sso-broker companion-shim coupling flagged as the T9 sharp edge.
- 2026-06-04: post-rebase onto PR #230. Folded in the exit-code reclassification — a missing `credbroker` (now a pip dependency) resolves to exit 2 via the import guard #230 standardized, amending the exit-code-contract spec's "unprojected shim → 1" clause for the five migrated CLIs (residual scope: the sso-broker companion path). Refined T7 (import-guard placement + record the amendment); added the missing-`credbroker`→2 AC.
