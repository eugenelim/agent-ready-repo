# Spec: credbroker-user-scope

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0023](../../rfc/0023-credential-manager-broker.md) — **amends** it (an Approver-signed amendment recorded in the RFC): RFC-0023 chose pip over the vendored shim and deferred no-repo adopters to Phase-2 PyPI; this spec adds a **layered delivery model** (vendored floor → offline/local pip → PyPI) so user-scope/air-gapped corporate installs resolve credentials without PyPI. Completes the user-scope half of [RFC-0013](../../rfc/0013-credential-broker-contract.md)'s `~/.agentbundle/bin/` delivery (the `sso-broker` companion), which only ever shipped its self-host half. Builds on [`credbroker`](../credbroker/spec.md) (Shipped) and the projection retirement (T9/T10).
- **Brief:** none
- **Contract:** none <!-- a delivery mechanism + an on-disk layout (`~/.agentbundle/lib/`) + a sys.path precedence rule; not an openapi/asyncapi/proto/graphql/jsonschema surface. Specified inline below. -->
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A credentialed skill installed at **user scope** (`agentbundle install --pack <p> --scope user`, no repo on disk) currently resolves credentials at **env Tier-1 only**: its `_client.py` does `from credbroker import …`, but user-scope install delivers no `credbroker` and runs no `pip`, so OS-keyring (Tier-2) and dotfile/vault (Tier-3) resolution silently fall away. This is the dominant install mode for the credentialed packs, and the gap was opened by the RFC-0023 migration (T7–T9). It is the same gap that leaves `sso-broker.py` undelivered to `~/.agentbundle/bin/` on a no-repo install — the `~/.agentbundle/` user-scope delivery rail named by RFC-0013/RFC-0023 was only ever built for self-host.

This spec restores full Tier-1/2/3 resolution at user scope through **one consumer contract — `import credbroker` — and a layered delivery stack resolved by `sys.path` precedence**:

1. **Vendored floor (always present, zero-pip).** User-scope install vendors the stdlib-base `credbroker` package source to `~/.agentbundle/lib/credbroker/`, which the consumer bootstrap appends to `sys.path` at **lowest** precedence. Guarantees Tier-1/2/3 (plaintext Tier-3) everywhere, with no pip and independent of which interpreter runs the skill.
2. **Offline / local pip (corporate, no PyPI).** A built `credbroker` **wheel** lets a locked-down site `pip install` from an internal index or a local `.whl`; because pip lands it in site-packages, it **wins** over the floor and enables the encrypted `[crypto]` vault. No PyPI dependency.
3. **PyPI (open adopters).** Publishing `credbroker` to PyPI lets open environments `pip install credbroker[crypto]`; same site-packages precedence.

Success: a no-repo user-scope install resolves Tier-2/Tier-3 again via the vendored floor; a site that pip-installs `credbroker` (from PyPI, an internal mirror, or a local wheel) transparently upgrades to that copy (and the vault); and the long-missing `sso-broker` user-scope delivery is closed on the same rail. The layered model is recorded as an RFC-0023 amendment.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Make a pip-installed `credbroker` win over the vendored floor.** The bootstrap appends `~/.agentbundle/lib` to `sys.path` (lowest precedence), never prepends — so site-packages (PyPI / internal-mirror / local-wheel / editable) always takes priority and the `[crypto]` vault is reachable when installed.
- **Keep the vendored floor a byte-faithful copy of the package source.** The vendored `~/.agentbundle/lib/credbroker/` (and its self-host `<repo>/.agentbundle/lib/` staging) is projected from `packages/credbroker/credbroker/`; a drift gate fails `make build-check` if they diverge — the same discipline the retired shim projection had, but **one shared copy**, not N per-skill copies.
- **Write only under the per-scope `.agentbundle/` jail.** All new user-scope delivery goes through `safety.write_jailed(..., scope=..., allowed_prefixes=...)`; the target stays under `.agentbundle/lib/` (and `.agentbundle/bin/` for the sso-broker half), which the path-jail already permits.
- **Degrade, never crash.** A consumer whose bootstrap finds neither a pip-installed `credbroker` nor the vendored floor must fail exactly as today (runtime `ModuleNotFoundError` → the entry script's top-level handler → clean exit), never a traceback or a partial import.

### Ask first

- **Publishing to PyPI / registering the name.** The PyPI publish (layer 3) is wired as a workflow but the actual first publish + name claim is a maintainer action (RFC-0023 name-registration decision), not performed by CI on merge. Surface before triggering a real publish.
- **Auto-running `pip` from the install command** (the "active B" convenience: `agentbundle install … --with-credbroker`). Deferred; if implementation surfaces a need, surface it — interpreter/venv targeting is the open risk.
- **Touching `sso-broker.py` / the `_sso_*` backends' logic.** The sso-broker half of this spec wires *delivery only* (its existing `adapter-root-bins/` files reach `~/.agentbundle/bin/`); changing the broker's behavior is out of scope (credbroker spec Boundaries → Ask first).

### Never do

- **Never prepend the vendored floor to `sys.path`.** That would shadow a real (newer, `[crypto]`-capable) pip-installed `credbroker` with the stdlib-only floor — a silent downgrade.
- **Never add a new top-level directory or a runtime dependency to deliver the floor.** The vendored copy lands under the existing `.agentbundle/` artifact root via the existing path-jail; no new top-level tree, no new dependency in `credbroker`'s base or in `agentbundle`. (Structural boundary.)
- **Never make the encrypted `[crypto]` vault a requirement of the floor.** The vendored floor is stdlib-only (plaintext Tier-3); the vault is an upgrade that arrives only with a pip-installed `credbroker[crypto]`. Vendoring must not pull `cryptography`/`argon2`.
- **Never let a credential value reach stdout/stderr/argv/logs** on any delivery or resolution path (the RFC-0006 no-leak invariant).

## Testing Strategy

- **Vendored-floor resolution at user scope (no pip):** **goal-based check**, exercised by an **integration** test — a `$HOME`-redirected user-scope install of a credentialed pack, then assert `~/.agentbundle/lib/credbroker/` exists and a consumer entry script (clean env, no site-packages `credbroker`) resolves `import credbroker` and reaches Tier-1/2/3. Crosses install→runtime, so integration altitude.
- **`sys.path` precedence (pip-installed wins over floor):** **TDD/goal-based**, **unit/integration** — with both a site-packages `credbroker` and the vendored floor present, assert the imported module is the site-packages one (e.g. via `credbroker.__file__`), and with only the floor present, assert the floor resolves. A compressible invariant.
- **Drift gate (floor stays byte-faithful to source):** **goal-based check** — `make build-check` red-fails when `<repo>/.agentbundle/lib/credbroker/` diverges from `packages/credbroker/credbroker/`; a standing test asserts parity. Mirrors the adapter-root-bins drift gate.
- **sso-broker user-scope delivery:** **goal-based check**, **integration** — a `$HOME`-redirected user-scope install of `credential-brokers` lands `~/.agentbundle/bin/sso-broker.py` (+ the companion `credentials_shim.py` + `_sso_*` backends). This is the regression the current install silently fails.
- **Wheel build (layer 2 / corporate):** **goal-based check** — `python -m build packages/credbroker` produces a `py3-none-any` wheel; a smoke install into a clean venv imports `credbroker` and (with the extra) `credbroker[crypto]`.
- **PyPI publish (layer 3):** **goal-based check** — the release workflow validates/builds and is wired for OIDC Trusted Publishing, gated so a real publish is a manual maintainer action, not automatic on merge.
- **No-leak invariant:** carried by the consumer/credbroker suites already; re-asserted on the new delivery paths (no credential value in any new code path).

## Acceptance Criteria

- [ ] A `$HOME`-redirected **user-scope install** of a credentialed pack delivers the `credbroker` package source to `~/.agentbundle/lib/credbroker/` (stdlib-base modules; pure file projection, no pip), and a consumer entry script run with a clean environment (no site-packages `credbroker`) resolves `import credbroker` from that floor and performs env→keyring→dotfile resolution. *(Layer 1 / A′)*
- [ ] The consumer bootstrap appends `~/.agentbundle/lib` to `sys.path` at **lowest** precedence: with a site-packages `credbroker` present it is imported in preference to the floor (asserted via `credbroker.__file__`); with only the floor present the floor resolves; with neither, the entry script exits cleanly (no traceback). *(Layer 1 precedence + degrade)*
- [ ] The vendored floor is a byte-faithful projection of `packages/credbroker/credbroker/`: `make build-check` fails on divergence, and a standing test asserts parity (excluding `__pycache__`/tests). The floor pulls **no** third-party module (no `cryptography`/`argon2` at import of the base). *(Layer 1 drift + purity)*
- [ ] `python -m build ./packages/credbroker` produces a `credbroker-<v>-py3-none-any.whl`; installing that wheel (or `credbroker[crypto]`) into a clean venv imports cleanly. The corporate path — `pip install` from a local wheel or an internal index, no PyPI — is documented in the credentialed-skill guide. *(Layer 2 / B, corporate)*
- [ ] A release workflow builds + validates the `credbroker` wheel/sdist and is wired for OIDC Trusted Publishing to PyPI, **gated** so the first real publish + name claim is a manual maintainer action (not automatic on merge). *(Layer 3 / C — code wired this spec; the publish itself is the maintainer action)*
- [ ] A `$HOME`-redirected **user-scope install** of `credential-brokers` lands `~/.agentbundle/bin/sso-broker.py` plus its companion `credentials_shim.py` and the `_sso_*` backends — closing the long-missing user-scope half of the RFC-0013 `adapter-root-bins` delivery on the same rail. *(sso-broker half)*
- [ ] No credential value appears in stdout/stderr/argv/logs on any new delivery or bootstrap path (RFC-0006 no-leak), and the five API CLIs' `test_exit_codes.py` + `credential-setup`'s `test_setup.py` stay green after the bootstrap change. *(no-leak + no consumer regression)*
- [ ] RFC-0023 carries an Approver-signed **amendment** recording the layered delivery model (vendored floor → offline/local pip → PyPI) as the resolution of its deferred no-repo-adopter problem; the `credbroker-user-scope` spec is linked from it.

## Assumptions

- Technical: user-scope install today delivers **only** adapter primitives (skills/agents/…) + `state.toml`; it delivers nothing to `~/.agentbundle/bin|lib/` and runs no `pip` — `sso-broker.py` is absent after a no-repo user-scope install (source: `$HOME`-redirected install probe of `credential-brokers`, 2026-06-09; `install.py:_render_for_user_scope`).
- Technical: the user-scope path-jail already permits `.agentbundle/` writes for the user-scope adapters (`safety.py` allowed-prefixes include `.agentbundle/`), so new delivery there needs the enumerate-and-write code, not a jail change (source: `safety.py`, `_data/adapter.toml` allowed-prefixes; general-purpose trace 2026-06-09).
- Technical: `credbroker`'s base is stdlib-only and vendorable as source; `_vault.py` imports `cryptography`/`argon2` **lazily** under `[crypto]`, so vendoring the whole package source keeps the base pure (source: `packages/credbroker/pyproject.toml` `dependencies = []`; credbroker spec AC4 import-graph gate).
- Technical: the **five API CLI** entry scripts (`jira.py`, `figma.py`, `jira_align.py`, `publish_page.py`, `crawl_space.py`) carry a `__package__`-bootstrap block that manipulates `sys.path` (the natural append hook); **`credential-setup/scripts/setup.py` is the exception** — it has **no** bootstrap and imports `from credbroker import …` at **module top level**, so it needs a distinct floor-append placed *before* that import (source: the bootstrap blocks edited in T9/T10 PR #252; `setup.py:23-25` has no `sys.path` manipulation — adversarial review 2026-06-09).
- Process: the vendored floor is **additive** — the primary, highest-precedence contract is still `import credbroker` from site-packages (pip), exactly as RFC-0023 / ADR-0003's posture intends; the floor is a *fallback* for that same import, not a return to the projected-shim model. So ADR-0003's projected-shim *reversal* is **not** itself reversed (no new ADR needed); the RFC-0023 amendment records the fallback (source: adversarial review 2026-06-09; CONVENTIONS § governance).
- Technical: `release-agentbundle.yml` already builds a wheel + publishes via OIDC Trusted Publishing — the model to mirror for a `release-credbroker.yml` (source: `.github/workflows/release-agentbundle.yml`; Explore 2026-06-09).
- Process: this amends Accepted RFC-0023 under the single-maintainer self-approval model (Approver: eugenelim) — divergence from a frozen Accepted RFC is recorded in governance, not just the spec changelog (source: RFC-0023 line 5; user confirmation 2026-06-09).
- Product: user-scope is the dominant install mode for credentialed packs, and corporate environments need a no-PyPI (internal-mirror / local-wheel / zero-pip) path — all three layers are in scope, sequenced foundation→floor→PyPI (source: user confirmation 2026-06-09).
- Process: the latent `sso-broker` user-scope-delivery gap is fixed on the same rail in this spec rather than filed separately (source: user confirmation 2026-06-09).
