# Plan: credbroker-user-scope

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

One consumer contract — `import credbroker` — backed by a `sys.path`
**precedence stack**: a site-packages copy (PyPI / internal-mirror / local
wheel / editable) always wins; a **vendored floor** at
`~/.agentbundle/lib/credbroker/` answers when nothing else did. Three delivery
layers feed that stack and are built in cost/value order:

1. **Foundation (unlocks the local-pip and PyPI layers immediately).** Append
   `~/.agentbundle/lib` to `sys.path` at **lowest** precedence in the consumer
   bootstrap (tolerating the floor's absence), and stand up a
   `release-credbroker.yml` that builds + smoke-validates the `credbroker`
   wheel/sdist (OIDC publish wired but **gated**). The moment a wheel exists, a
   corporate site can `pip install` it from an internal index or a local file —
   no PyPI, no new install machinery.
2. **Vendored floor (the net-new machinery).** A build-pipeline projection
   vendors `packages/credbroker/credbroker/` into the `credential-brokers`
   pack as a new `.apm/user-libs/` primitive (drift-gated against the package
   source), and a **new install-time user-scope delivery step** writes both
   `.apm/user-libs/credbroker/` → `~/.agentbundle/lib/credbroker/` **and** the
   pre-existing `.apm/adapter-root-bins/*.py` → `~/.agentbundle/bin/` (closing
   the long-missing `sso-broker` user-scope half — the *same* gap, same rail).
3. **PyPI (separable maintainer action).** The release workflow's publish job,
   triggered manually when the maintainer owns the name + cadence.

Riskiest part: the **install-time delivery rail (layer 2)** — install reads
from a built *catalogue*, not `packs/`, so the vendored credbroker +
adapter-root-bins must be present in the pack the catalogue carries (hence the
`.apm/user-libs/` primitive, which flows pack→catalogue→install like every
other primitive), and the new step must write under the existing `.agentbundle/`
path-jail without a jail change. Reversible until layer 2 lands; the foundation
and floor are additive and degrade to today's behavior.

## Constraints

- **[RFC-0023](../../rfc/0023-credential-manager-broker.md)** — this plan
  **amends** it (Approver-signed amendment): the layered model resolves the
  RFC's deferred no-repo-adopter problem. Authored as **T5**.
- **[RFC-0013](../../rfc/0013-credential-broker-contract.md)** — the
  `adapter-root-bins` → `~/.agentbundle/bin/` user-scope delivery it named but
  only half-shipped (self-host) is completed here for `sso-broker`.
- **[`credbroker`](../credbroker/spec.md) (Shipped)** — the package whose source
  is vendored; its stdlib-base purity (AC4) is preserved by the floor.
- **CHARTER Principle 3** — no daemon/resident process/network injection;
  delivery is file projection only.

## Construction tests

**Integration tests (cross-cutting, span tasks):**
- `$HOME`-redirected user-scope install of `credential-brokers` (+ a consumer
  pack): assert `~/.agentbundle/lib/credbroker/` and `~/.agentbundle/bin/sso-broker.py`
  land, and a consumer entry script (clean env, no site-packages `credbroker`)
  resolves `import credbroker` from the floor — spans T3/T4 (exercised by T4).

**Manual verification:** none — every outcome has a goal-based or TDD check.

## Design (LLD)

Shape: **integration** (delivery wiring across build → install → runtime).
Stack (no `docs/architecture/reference.md`): Python ≥3.11, agentbundle build
pipeline (`agentbundle/build/`) + install command (`agentbundle/commands/install.py`),
`safety.write_jailed` path-jail, pytest. Sub-sections pruned to the
`integration` set.

### Design decisions
- **One shared vendored copy, not N per-skill copies.** The floor lives once at
  `~/.agentbundle/lib/credbroker/`, sourced from `packages/credbroker/credbroker/`
  via a drift-gated `.apm/user-libs/` primitive. Rejected: re-projecting into
  each skill's `scripts/` (the retired shim model — N copies, N drift points).
  Traces to: floor + drift ACs.
- **Append to `sys.path`, never prepend.** Site-packages wins so a pip-installed
  `credbroker[crypto]` upgrades the floor. Rejected: prepend (silent downgrade of
  a newer/vault-capable install). Traces to: precedence AC.
- **Vendor as a pack `.apm/` primitive, not a special install-time copy from
  the `packages/` tree.** install consumes a catalogue, not `packages/`; routing
  the floor through `.apm/user-libs/` makes it flow pack→catalogue→install like
  every primitive. Rejected: teaching install to read `packages/credbroker/`
  (couples install to the monorepo layout). Traces to: layer-1/floor delivery AC.
- **Generic user-scope `.agentbundle/` delivery step covers both `user-libs`
  and `adapter-root-bins`.** One enumerate-and-`write_jailed` loop closes the
  credbroker-`lib/` gap and the `sso-broker`-`bin/` gap. Traces to: floor AC +
  sso-broker AC.

### Dependencies & integration
- **Build pipeline:** new `agentbundle/build/user_libs.py` (mirrors
  `adapter_root_bins.py`): `collect`/`apply_projection`/`check_drift`, source
  `packages/credbroker/credbroker/`, target `<scope-root>/.agentbundle/lib/credbroker/`.
  Wired into `self_host.py` apply + build-check drift gates.
- **Install command:** a new user-scope delivery step in `install.py` (after the
  adapter projection) that writes the pack's `.apm/user-libs/**` and
  `.apm/adapter-root-bins/*.py` under `~/.agentbundle/{lib,bin}/` via
  `safety.write_jailed` (jail already permits `.agentbundle/`).
- **Consumers:** the 5 entry scripts + `setup.py` bootstrap appends `~/.agentbundle/lib`.
- **Release:** `.github/workflows/release-credbroker.yml` mirrors `release-agentbundle.yml`.

### Interfaces & contracts
The on-disk + import contract (spec's `Contract: none` — specified here):
- **Floor location:** `~/.agentbundle/lib/credbroker/` (user scope),
  `<repo>/.agentbundle/lib/credbroker/` (self-host staging).
- **Import precedence:** consumer bootstrap appends `~/.agentbundle/lib` to
  `sys.path` (lowest); site-packages resolves first.
- **Vendored shape:** byte-faithful copy of `packages/credbroker/credbroker/`
  (excluding `__pycache__`, `tests/`); stdlib-base, `_vault.py` lazy.
- **File modes:** `lib/**` written with **default** mode (importable Python, no
  exec bit); `bin/*.py` keep `0o755` on POSIX (Windows inherits DACL) — the
  `bin/` half reuses `adapter_root_bins.compute_projections`, which folds in the
  AC22b companion `credentials_shim.py` from `shared-libs/`.

### Failure, edge cases & resilience
- **Neither floor nor site-packages credbroker** → runtime `ModuleNotFoundError`
  → entry script's top-level handler → clean exit (today's behavior, preserved).
- **Floor present but stale** → drift gate red-fails `make build-check`.
- **`[crypto]` absent** → floor resolves base tiers; vault gracefully unavailable
  (`crypto_available()` False). No `cryptography` import at base.

## Tasks

### T1: consumer bootstrap appends `~/.agentbundle/lib` (lowest precedence)

**Depends on:** none

**Touches:** packs/atlassian/.apm/skills/*/scripts/jira.py, packs/atlassian/.apm/skills/*/scripts/jira_align.py, packs/atlassian/.apm/skills/*/scripts/publish_page.py, packs/atlassian/.apm/skills/*/scripts/crawl_space.py, packs/figma/.apm/skills/figma/scripts/figma.py, packs/credential-brokers/.apm/skills/credential-setup/scripts/setup.py

**Tests:** (`packages/agentbundle/tests/integration/test_credbroker_floor_precedence.py` — real subprocess invocation, no `runpy.run_path`/importlib synthesis, per `test_credential_user_scope_invocation.py`'s convention.)
- Precedence — **split by import shape** (the precedence AC's behavioral `credbroker.__file__` evidence lands where it can be observed deps-free, and is proven structurally across all 6):
  - **Source/AST guard, parametric across all 6 edited scripts** (always runs, deps-free): each script *appends* `~/.agentbundle/lib` (`.expanduser()`) and never `insert`s it, and the append is correctly placed (CLIs: after `sys.path.insert(0, str(_here.parent))`; `setup.py`: before the top-level `from credbroker import`). Because `sys.path` is searched in order and the floor is last, any earlier entry (incl. site-packages) wins — the precedence *mechanism*, proven without execution. Verifies the precedence AC + the no-insert-0 Never-do (below).
  - **Behavioral `credbroker.__file__` on `setup.py`** (the one *eager*, deps-free importer): real `python scripts/setup.py` invocation resolves a planted floor when floor-only (`-S`), and a planted earlier-`sys.path` copy (modelling a pip install) when both present — never the floor. The five API CLIs import `credbroker` *lazily* (only inside an `httpx`-requiring credential verb), so their **end-to-end floor resolution through a real consumer is T4's explicit integration test**; at T1 their precedence rests on the structural guard above (identical bootstrap edit). Verifies the precedence AC behaviorally.
- Degrade: with neither present, each entry script exits cleanly (no traceback) — the existing `test_import_guard_present` / exit-code suites stay green (goal-based). Verifies the degrade AC.
- No-insert-0 guard: the source/AST guard above asserts **no** edited script inserts the floor path at `sys.path` index 0 (only `append`) — so a stale floor can never shadow a real install (goal-based). Verifies the precedence AC's "never prepend" Never-do.

**Approach (two shapes — the scripts differ):**
- **Five API CLIs** (`jira.py`/`figma.py`/`jira_align.py`/`publish_page.py`/`crawl_space.py`): inside the existing `__package__`-bootstrap block, after `sys.path.insert(0, str(_here.parent))`, **append** `Path("~/.agentbundle/lib").expanduser()` to `sys.path` (`Path`/`pathlib` is already imported in each, so no new `import os`; guarded: only if the dir exists and not already present; the resolver import in `_client.py` is lazy, so this runs before resolution). Never insert at 0.
- **`credential-setup/scripts/setup.py`** (Blocker 1 — **no bootstrap, top-level `from credbroker import …` at line 25**): prepend a tiny stdlib block **before** that import — `_floor = pathlib.Path("~/.agentbundle/lib").expanduser(); if _floor.is_dir() and str(_floor) not in sys.path: sys.path.append(str(_floor))` (`pathlib`/`sys` already imported above it). **Append** (site-packages is already on `sys.path` at interpreter start, so append still loses to a real install) — never insert at 0.

**Done when:** parametric precedence + degrade + no-insert-0 tests green; the 5 CLIs' `test_exit_codes.py` + `credential-setup`'s `test_setup.py` stay green; grep shows an *append* (never insert-0) of the lib path in all 6 scripts.

### T2: `release-credbroker.yml` builds + validates the wheel (publish gated)

**Depends on:** none

**Tests:**
- `python -m build ./packages/credbroker` produces `credbroker-<v>-py3-none-any.whl` + sdist; a smoke step installs the wheel into a clean venv and imports `credbroker` (and `credbroker[crypto]`) (goal-based, CI). Verifies the wheel AC.
- Workflow lints/parses (actionlint or YAML load); the publish job is `workflow_dispatch`/tag-gated, not on-merge (goal-based). Verifies the publish-gated AC.

**Approach:**
- Author `.github/workflows/release-credbroker.yml` mirroring `release-agentbundle.yml`: build-and-smoke job (build wheel+sdist, install into fresh venv, import-smoke), then an OIDC Trusted-Publishing job gated behind a manual/tag trigger.
- Document the **corporate** path in `docs/guides/credential-brokers/how-to/add-a-credentialed-skill.md`: `pip install credbroker` from an internal index (`--index-url`) or a local `.whl` — no PyPI required.

**Done when:** the build-and-smoke job is green in CI; the publish job exists but does not run on merge; the guide documents the no-PyPI corporate install.

### T3: build-pipeline vendors credbroker to `.agentbundle/lib/` (drift-gated)

**Depends on:** none

**Tests:**
- Projection: `apply_projection` copies `packages/credbroker/credbroker/**` (excluding `__pycache__`/`tests`) into `<repo>/.agentbundle/lib/credbroker/` byte-faithfully (TDD, unit). Verifies the floor-source side.
- Drift gate: tampering/removing a vendored file makes `check_drift` (and `make build-check`) red; a standing parity test passes on a clean tree (goal-based). Verifies the drift AC.
- Purity: the vendored base imports no third-party module (reuse credbroker's import-graph assertion against the vendored copy) (goal-based). Verifies the purity clause.

**Approach:**
- Add `packs/credential-brokers/.apm/user-libs/` as the projection target inside the pack (the catalogue-visible primitive), sourced from `packages/credbroker/credbroker/`.
- Add `agentbundle/build/user_libs.py` mirroring `adapter_root_bins.py` (`collect_sources`/`apply_projection`/`check_drift`), and wire it into `self_host.py` apply + `run_build_check_drift_gates`.
- **Register the new primitive type (Blocker 2 — contract-bump ripple).** Declare `[primitive."user-libs"]` in **both** `adapter.toml` copies (`_data/` + `docs/contracts/`, byte-identical), and add `"user-libs"` to `safety.py:_PACK_PRIMITIVE_TYPES` — that tuple holds the `.apm/` **source-dir leaf name** (`"shared-libs"`, `"adapter-root-bins"`), so the entry is `"user-libs"` matching `.apm/user-libs/` (the orphan-scan keys off it). **No JSON-schema change** (pass-2 Nit 3): `adapter.schema.json`'s `primitive` table is open (`additionalProperties`); only the closed *projection*-level enum is fixed, and build-only primitives correctly stay out of it — there is no `KNOWN_PRIMITIVES` constant. **Establish the version precedent:** `shared-libs` + `adapter-root-bins` are build-pipeline-only primitives with **no adapter projection rules** (added in #139 as co-residing governance-bump entries). Decide if a `version` bump is even needed; if so, bump `version` + the `test_contract.py` version pin + re-aggregate marketplace. Either way, **run the full `packages/agentbundle` pytest by hand** (the contract-bump trap: lexical version compare + stale assertions live in CI-ungated test roots).

**Done when:** `make build-self` lands `<repo>/.agentbundle/lib/credbroker/`; `make build-check` green clean and red on injected drift; purity test green; `test_contract.py` + the full `packages/agentbundle` suite green (no unknown-primitive / version-pin failure).

### T4: install-time user-scope delivery rail (`lib/` floor + `bin/` sso-broker)

**Depends on:** T3, T1

**Tests:**
- `$HOME`-redirected user-scope install of `credential-brokers` lands `~/.agentbundle/lib/credbroker/__init__.py` **and** `~/.agentbundle/bin/sso-broker.py` **and** the AC22b companion `~/.agentbundle/bin/credentials_shim.py` + the `_sso_*` backends (integration). Verifies the floor-delivery AC + the sso-broker AC.
- End-to-end floor: after that install, a consumer entry script (clean env, no site-packages `credbroker`) resolves `import credbroker` from `~/.agentbundle/lib` and reaches Tier-1/2/3 — asserted on **Windows CI too** (`build-check-windows.yml`), since the lib floor must be importable cross-platform (integration). Verifies the layer-1 resolution AC.
- Jail + no-leak: the delivery refuses to write outside `.agentbundle/`, and no credential value appears on any delivery path (goal-based). Verifies the always-do jail clause + the no-leak AC.

**Approach:**
- Add a user-scope delivery step in `install.py` (after `_render_for_user_scope`) that writes, via `safety.write_jailed(scope="user", allowed_prefixes=…)`:
  - **`bin/`:** carry the AC22b *ship-both companion* `credentials_shim.py` (from `shared-libs/`) alongside the `adapter-root-bins/*.py` — a bare `adapter-root-bins/*.py` glob would **miss** the companion and land the sso-broker backends broken on macOS/Windows. **Signature note (pass-2 Concern 1):** `adapter_root_bins.compute_projections(working_tree, packs_dir)` is build-pipeline-scoped — it walks a multi-pack `packs/` root and resolves the companion via `shared_libs.collect_sources(packs_dir)`; install operates on a **single resolved catalogue `pack_dir`**. So **extract the companion-aware enumeration into a `pack_dir`-scoped helper** (reuse `collect_companion_shim`'s ship-both logic against the one pack), rather than calling `compute_projections` directly. `bin/*.py` keep `0o755` on POSIX (Windows inherits DACL).
  - **`lib/`:** enumerate the pack's `.apm/user-libs/**` → `~/.agentbundle/lib/**`. Importable Python, **not** executable — write with **default** file mode (no exec bit), unlike `bin/`.
- Source from the catalogue/dist the install consumes. (Concern 6: `build/main.py` already `copytree`s the **whole** `.apm/` tree into each dist pack, so `.apm/user-libs/` + `.apm/adapter-root-bins/` flow automatically once T3 lands them in the pack — the catalogue-confirmation test is belt-and-suspenders, not plumbing to build.)
- Extend `test_credential_brokers_pack_install.py` (it currently only checks `~/.agentbundle/` exists) with the lib/ + bin/ + companion assertions.
- **Security note (carried from T1's security review):** T1 only *appends* `~/.agentbundle/lib` to `sys.path` (append, never prepend — so a real pip-installed copy always wins). The residual surface is that *whatever* lives under the floor dir becomes importable at lowest precedence, so a writable floor is a local code-exec vector. This delivery task owns the mitigation: create `~/.agentbundle/lib/` user-owned with restrictive mode and treat a world/group-writable floor as a refuse condition on the `write_jailed` path (the floor's integrity is delivery's guarantee, which T1's bootstrap relies on).
- **Coverage note (carried from T1's quality review):** T1 proves the five API CLIs' precedence *structurally* only (they import `credbroker` lazily inside an `httpx`-gated verb, so a deps-free behavioral `__file__` probe isn't available at T1). T4's "end-to-end floor" test above is therefore **load-bearing** — keep its assertion that a real consumer entry script resolves `import credbroker` from the floor (at least one CLI, not just `setup.py`); do not drop or weaken it.

**Done when:** all three integration tests green (incl. Windows importability); install writes only under `.agentbundle/`; `~/.agentbundle/bin/sso-broker.py` + companion present after a no-repo user-scope install (the regression closed); `lib/` files carry no exec bit.

### T5: RFC-0023 amendment + docs + spec close-out

**Depends on:** T1, T2, T3, T4

**Tests:**
- RFC-0023 carries an `## Amendments` (or equivalent) entry, Approver `eugenelim`, recording the layered model and linking this spec (goal-based). Verifies the amendment AC.
- `lint-spec-status` clean; doc-drift/link lints pass; spec Status → Shipped with ACs checked/deferred (goal-based).

**Approach:**
- Add the Approver-signed amendment to `docs/rfc/0023-credential-manager-broker.md` (layered delivery: vendored floor → offline/local pip → PyPI; resolves the deferred no-repo problem). **State explicitly (Concern 5) that the floor is *additive*** — the primary, highest-precedence contract is still `import credbroker` from site-packages, so ADR-0003's projected-shim *reversal* is unchanged and **no new/annotating ADR is required**; the floor is a fallback for that same import, recorded here in the RFC.
- Guide: document the floor + the three layers; CONVENTIONS only if a credentialed-skill convention actually changes (else leave). Flip spec → Shipped; record any deferral (active `--with-credbroker` pip) in `workspace.toml [backlog]`.

**Done when:** amendment recorded; docs read the layered model; spec Shipped; lints green.

## Rollout

- **Delivery:** additive and reversible. T1 (bootstrap append) and the floor are no-ops where the floor is absent (degrade to today). Layer 2 (install rail) is the point the user-scope floor goes live; before it, consumers behave as today. PyPI publish (layer 3) is a separate manual maintainer action.
- **Infrastructure:** none new in-repo. External: a PyPI project + OIDC Trusted Publisher (Phase-3, maintainer action; name registration per RFC-0023 decision).
- **External-system integration:** none for the floor/wheel; PyPI for layer 3 only.
- **Deployment sequencing:** T3 (vendored source in the pack) before T4 (install delivers it); T1 (bootstrap) before T4's end-to-end floor test can pass.

## Risks

- **Catalogue plumbing (lower than first thought).** install reads a built catalogue, not `packs/`. But `build/main.py` `copytree`s the **whole** `.apm/` tree into each dist pack (adversarial review Concern 6), so `.apm/user-libs/` + `.apm/adapter-root-bins/` flow automatically once T3 lands them in the pack. The only real failure is T3 not landing the source — caught by T3's own drift gate. T4's catalogue-confirmation test is belt-and-suspenders.
- **`setup.py` has no bootstrap + a top-level `from credbroker import` (Blocker 1).** Unlike the 5 CLIs, the floor-append must be prepended *before* that import or it runs too late. Mitigation: T1's setup.py shape adds the append ahead of the import.
- **`sys.path` append shadowing edge cases.** A stale floor older than a site-packages install must never win. Mitigation: append-only (never insert-0) + a parametric precedence test across all 6 scripts + a no-insert-0 grep guard.
- **Re-introducing vendoring the RFC retired.** The floor is a vendored copy + drift gate — the shape RFC-0023 argued against. Mitigation: it's *one shared copy* (not N per-skill) and the *floor*, not the primary path; recorded honestly in the RFC amendment.
- **Windows delivery parity.** The user-scope rail + bootstrap must hold on Windows (path-jail, `expanduser`, drift gate). Mitigation: run the new integration test in `build-check-windows.yml`.

## Changelog

- 2026-06-09: initial plan. Layered delivery (foundation+wheel → vendored floor → PyPI) in cost/value order; install-time `.agentbundle/` delivery rail is the net-new machinery and also closes the latent `sso-broker` user-scope gap. Premise correction vs. the original framing: the `~/.agentbundle/bin/` user-scope rail does **not** exist today (probe-confirmed) — it is built here, not mirrored.
- 2026-06-09: spec-mode adversarial review fixes. T1 split into two shapes (5 CLIs append in their bootstrap; `setup.py` has no bootstrap + a top-level `from credbroker import`, so the floor-append is prepended before it) + parametric precedence test + no-insert-0 guard. T3 made the contract-primitive registration explicit (the `[primitive."user-libs"]` declaration + `_PACK_PRIMITIVE_TYPES`/validator ripple + the contract-bump-trap full-pytest, anchored on the `adapter-root-bins`/`shared-libs` build-only precedent). T4 reuses `adapter_root_bins.compute_projections` so the AC22b companion shim rides the `bin/` delivery (a bare glob would miss it), `lib/` written default-mode vs `bin/` `0o755`, + Windows importability. Catalogue risk downgraded (`build/main.py` copytrees the whole `.apm/`). Recorded the floor as *additive* (ADR-0003 posture unchanged — no new ADR).
- 2026-06-09: T1 implemented. The precedence construction test is split by import shape: a deps-free **source/AST guard parametric across all 6** scripts (append-not-insert-0 + placement — the precedence mechanism + no-insert-0 Never-do) plus a **behavioral `credbroker.__file__`** check on the one eager, deps-free importer (`setup.py`); the five API CLIs import `credbroker` lazily (inside an `httpx`-gated verb), so their end-to-end floor resolution through a real consumer is deferred to T4's integration test. Implemented with `Path(...).expanduser()` (no new `import os`; `Path`/`pathlib` already imported in every file). Test lives at `packages/agentbundle/tests/integration/test_credbroker_floor_precedence.py` and is wired into `build-check.yml` (the no-insert-0 guard is platform-agnostic, so the Linux job gates it).
- 2026-06-09: T4 implemented. The install-time user-scope delivery rail lands in
  `install.py` Step 9, gated `plan.scope == "user"`: it delivers the pack's
  `.apm/user-libs/**` → `~/.agentbundle/lib/**` (default mode, no exec bit) and
  the `.apm/adapter-root-bins/*.py` + AC22b companion `credentials_shim.py` →
  `~/.agentbundle/bin/**` (`0o755` on POSIX, DACL-inherited on Windows), all via
  `safety.write_jailed(scope="user", …)` under the existing `.agentbundle/`
  prefix (no jail change). Per the pass-2 concern, the companion-aware
  enumeration is a **new single-`pack_dir`-scoped helper**
  `adapter_root_bins.collect_pack_root_bins(pack_dir)` (reuses the ship-both
  opt-in against one resolved catalogue pack) rather than the multi-pack,
  working-tree-folding `compute_projections`. The floor is **shared, idempotent
  infrastructure** (one copy per consumer), so the delivered files are
  deliberately **not** recorded in `state.files` — uninstalling one pack must not
  strip a co-installed pack's floor. Security mitigation (carried from T1's
  review): `_assert_user_floor_dirs_safe` refuses on entry if `~/.agentbundle`,
  `…/lib`, or `…/bin` already exists group/world-writable (a writable floor is a
  local code-exec vector), and `_harden_floor_dir_modes` strips group/world
  write bits from the delivered dirs after write (defends a permissive umask);
  both no-op on Windows. The load-bearing end-to-end CLI test (`jira.py check`
  under `-S` + a stub `httpx`) proves a real API CLI resolves `import credbroker`
  from the floor and reaches the env→keyring→dotfile ladder (exit 2,
  `CredentialsMissingError`); `setup.py --help` under `-S` covers the eager
  importer; both run in `build-check-windows.yml` for cross-platform
  importability. No state-recording, no contract bump (delivery only).
  Post-implementation review (adversarial + security) hardened three things:
  the floor-safety refusal is gated to packs that actually ship floor content
  (a floor-less user install is never refused) and walks the full existing
  `.agentbundle` tree (catches a pre-existing loose *leaf*); and — since
  `install` resolves `pack_dir` from an *untrusted* catalogue — both delivery
  halves reject symlinked sources (per-file `is_symlink()` skip +
  `os.walk(followlinks=False)`) **and** a symlinked primitive *directory*
  itself, so a crafted pack can't read an out-of-tree file
  (`/etc/passwd`, `~/.ssh/id_rsa`) into the floor (the build-pipeline twin
  on the trusted in-repo `packs/` intentionally doesn't filter). Two
  follow-ons deferred to `workspace.toml [backlog]`:
  graceful floor-skip if a future adapter omits `.agentbundle/` from its
  user prefixes, and reference-counted floor removal on uninstall.
- 2026-06-09: T3 implemented. `agentbundle/build/user_libs.py` projects `packages/credbroker/credbroker/` byte-faithfully to **two** committed targets from one source: the catalogue-visible pack copy (`packs/credential-brokers/.apm/user-libs/credbroker/`, which `build/main.py` copytrees into each dist pack for T4) and the self-host floor staging (`<repo>/.agentbundle/lib/credbroker/`, mirroring the committed `.agentbundle/bin/`). `lib/` is written default-mode (no exec bit, unlike `bin/`'s `0o755`); the orphan scan skips `__pycache__`/`tests` so importing the floor (the purity test) can't masquerade as drift. Wired into `self_host.py` apply + `run_build_check_drift_gates`. **Version decision: no bump.** The `adapter-root-bins`/`shared-libs` precedent (#139, `de790fe`) added build-pipeline-only primitives — no per-adapter projection rules — *within* v0.7, not as a dedicated bump; `user-libs` is the same shape, so `[contract] version` stays `0.10`, the `test_contract.py` pin and marketplace aggregation are untouched, and the (primitive × adapter) pair count stays 20 (locked by a new `test_user_libs_is_build_pipeline_only`). `[primitive."user-libs"]` declared in both byte-identical `adapter.toml` copies; `"user-libs"` added to `safety.py:_PACK_PRIMITIVE_TYPES`. **Source-location call:** `user_libs` derives its source from `packs_dir.parent` and **no-ops when the package source is absent** (non-monorepo / fixture-packs invocations), so the existing install-marker drift-gate tests stay green; real `make build-check` (where `packs_dir.parent` is the repo root) gates fully. Full `packages/agentbundle` pytest run by hand per the contract-bump trap — no version-pin or stale-assertion breakage.
- 2026-06-09: T5 implemented — spec close-out. RFC-0023 gains an Approver-signed
  `## Amendments` entry (Approver: eugenelim) recording the layered delivery model
  (vendored floor → offline/local pip → PyPI) as the resolution of its deferred
  no-repo-adopter problem, and linking this spec; stated explicitly that the floor
  is **additive** (primary contract is still `import credbroker` from site-packages,
  appended-not-prepended, so ADR-0003's reversal is unchanged — **no new ADR**). The
  how-to (`add-a-credentialed-skill.md`) Step 9 gains a *layered model* subsection
  documenting the floor (layer 1) and how the three layers stack on `sys.path`;
  CONVENTIONS untouched (the consumer convention `import credbroker` is unchanged —
  the floor is delivery plumbing, not a convention change). Spec flipped to
  **Shipped** with all 8 ACs checked (each verified against merged T1–T4 deliverables
  in-tree), and the `credbroker-user-scope` row in `docs/specs/README.md` flipped
  Draft → Shipped. The deferred **active `--with-credbroker` pip** convenience
  (spec Boundaries → *Ask first*) recorded in `workspace.toml [backlog]` as `active-with-credbroker-pip`;
  it is not an unmet AC (the floor already gives zero-pip Tier-1/2/3). No deferred
  ACs — all eight met.
