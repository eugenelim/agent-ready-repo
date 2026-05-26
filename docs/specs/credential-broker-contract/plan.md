# Plan: credential-broker-contract

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this document is allowed to change as you learn. When it changes substantially (a different approach, not just a re-ordering), note why in the changelog at the bottom.

## Approach

Three phases, sequenced per RFC-0013 § 9's *sequencing rule* — the cleanup happens last so `agentbundle.credentials` remains importable throughout the migration window.

**Phase 1 — Broker contract and primitives (T1–T10).** Lands the four-broker contract (`env` / `cli` / `creds` / `sso-cookie`), the `credential-brokers` user-scope pack with both broker artefacts, the two new build-pipeline primitive classes (`shared-libs/` for the in-process shim; `adapter-root-bins/` for the SSO subprocess), the lint extensions, the `add-credentialed-skill` template variants, and the documentation surface (ADR, CONVENTIONS, ROADMAP, guide, sibling spec amendments). Atomic-ish: the contract bump and the parser change are T1 (one PR); the broker pack and its build-pipeline support are T2–T8; templates and docs are T9–T10.

**Phase 2 — In-tree consumer migration (T11–T14).** Six skills + one author-skill teaching block migrate to `from .credentials_shim import` in dependency order: `example-credentialed-skill` first as the canonical reference (T11); `figma` next as the single-pack, single-key, non-atlassian validation case (T12); the four atlassian skills bundled (T13, all share the same `creds-schema.toml` shape); the `add-credentialed-skill` SKILL.md teaching block (T14, its own task per RFC-0013 § 9 — cannot be a sub-bullet of cleanup).

**Phase 3 — Cleanup (T15).** Remove `agentbundle/credentials.py` and `agentbundle/creds/`. Bump `agentbundle` pyproject `0.1.x` → `0.2.0`. Write `packages/agentbundle/CHANGELOG.md` with the verbatim migration recipe from RFC-0013 § 9 and concrete version numbers substituted.

**Riskiest part: T4 (`shared-libs/` projection).** This is a new build-pipeline primitive class with many-to-many projection — one source file → N consumer skills' `scripts/` directories, gated by `metadata.auth: creds`. The drift gate must distinguish three outcomes (modified / missing / orphaned) and the projection must create `scripts/` if absent. This task carries the highest test surface and the highest risk of cascading drift across consumer skills. Land it before any consumer migrates.

**Parallelism opportunities.** Honouring the declared `Depends on:` graph below:

- After **T1** lands: T9 (templates) and T10 (docs / sibling amendments) are the only two tasks that can begin immediately — both depend on T1 alone. They can be dispatched concurrently via work-loop supervisor mode.
- **T2** (pack skeleton) depends on T1 and is sequential before any pack-content work.
- After **T2** lands: T3 (shim file) and T5 (sso-broker file, with its own Tier-2 helper siblings — see T5's revised Approach) can run concurrently, both depending only on T2.
- **T4** (`shared-libs/` projection) depends on T3. **T6** (`adapter-root-bins/` projection) depends on T5. **T7** (credential-setup skill) depends on T3 (it consumes the shim). **T8** (lint) depends on T4 and T6.
- **T11** (canonical reference migration — `example-credentialed-skill`) depends on T4 and T8.
- After **T11** lands: T12, T13, T14 each migrate independent consumers but must run **sequentially**, not in parallel. The reason is that each task ends with `make build-self FORCE=1` against shared sibling projection files in `packs/*/.apm/skills/<skill>/scripts/`; parallel worktrees racing this build-self step against shared-libs projections produce either non-deterministic ordering or merge-revert drift per `feedback_build_self_undoes_projection_only_edits`. The supervisor-mode fan-out option is therefore unavailable for the migration tasks; sequence them.
- **T15** (cleanup) depends on T12, T13, T14 all landing.

Phase 1 (T1–T10): one possible PR sequence is PR-A (T1 only — small, gates everything), PR-B (T2 + T3 + T4), PR-C (T5 + T6), PR-D (T7), PR-E (T8), PR-F (T9), PR-G (T10) — seven PRs, with PR-F / PR-G parallelizable to PR-B onwards as long as T1 has landed. Or combine smaller tasks (T9 + T10 in one PR; T3 + T4 + T7 in one PR) per reviewer bandwidth. The plan does not pin PR count; it pins task count and the dependency edges.

## Constraints

- **RFC-0013** — canonical proposal; every § N reference in spec ACs traces back here.
- **RFC-0006** — storage tiers, Win32 error matrix, atomic-write discipline, per-platform Tier-2 backends preserved verbatim. The shim's behaviour is byte-equivalent to today's `agentbundle.credentials.load_credentials` modulo the import path.
- **RFC-0004** — user-scope dimension; per-pack `[pack.install]` declaration; refusal rails the `credential-brokers` pack passes by construction.
- **RFC-0011** — `[pack.install] allowed-adapters` field; v0.6 baseline this spec bumps to v0.7. Already closed (Accepted 2026-05-26), so the acceptance-ordering gate is met.
- **RFC-0007** — user-scope pack precedent (no seeds, no hooks, no markers, runtime deps documented per-skill).
- **CONVENTIONS.md § Spec-driven development** — implementation diverging from the spec is a spec bug; update in the same PR.
- **`feedback_dont_hide_unshipped_rfc_paths`** memory — the `.agentbundle/` prefix non-regression (AC2) is named honestly, not collapsed into a fake "add prefix" AC.
- **`feedback_credentialed_lint_substring_trap`** memory — basename + `Path.parts` composition, never literal-string substring. Applies to both the existing AC26(c) trap and the new positive-grep targets.
- **`feedback_build_self_undoes_projection_only_edits`** memory — after every change to `packs/credential-brokers/.apm/`, run `make build-self FORCE=1` and close any drift in-PR.
- **`reference_agentbundle_two_test_roots`** memory — `packages/agentbundle/tests/` (CLI / unit / integration) vs `packages/agentbundle/agentbundle/build/tests/` (contract / schema / projection). Pick the right one per task.

## Construction tests

Most construction tests live under **Tasks** below (per-task `Tests:` subsections). This top-level section covers cross-cutting tests that span tasks.

**Integration tests:**

1. **End-to-end install of `credential-brokers` pack at user scope** (lands with T2 / T3 / T5; refined across phases). `agentbundle install --pack credential-brokers --scope user .` against a fixture `$HOME`:
   - asserts `~/.agentbundle/bin/sso-broker.py` exists with mode `0o755` on POSIX;
   - asserts the projected shim files do not land at user scope (they project per-consumer-skill, not at install time);
   - asserts the `credential-setup` skill projects to the configured adapter's skills directory (e.g. `~/.claude/skills/credential-setup/`).

2. **End-to-end `auth: creds` consumer flow** (lands with T11 — the canonical reference migration). `example-credentialed-skill` after migration:
   - asserts `make build-self` projects `credentials_shim.py`, `_keychain_macos.py`, `_credman_windows.py` into the skill's `scripts/`;
   - invokes the skill's CLI against a fixture env-var tier; asserts the credential resolves;
   - invokes the skill's CLI against a fixture macOS / Windows keychain tier (mocked Tier-2 backend); asserts the credential resolves;
   - asserts the skill never imports `agentbundle.credentials`.

3. **End-to-end `auth: sso-cookie` consumer flow** (lands with T7 — no in-tree consumer migrates to `sso-cookie`, so this exercises a fixture consumer skill the test installs at runtime). Fixture skill declares `auth: sso-cookie` + `sso_profile: fixture`; mocked `sso-broker.py` returns a path; asserts the fixture consumer reaches `Path.home() / ".agentbundle" / "bin" / "sso-broker.py"` via subprocess.

4. **Final-state pre-pr gate** (lands with T15). After every task in the sequence has landed: `python3 tools/hooks/pre-pr.py` exits 0; `make build-check` exits 0; `pytest packages/agentbundle/` exits 0; `git grep "from agentbundle.credentials"` returns no matches under `packs/` or `packages/agentbundle/`.

**Manual verification:**

- **Manual-QA matrix per RFC-0013 Drawbacks:** broker × OS combinations, recorded as transcripts in `docs/specs/credential-broker-contract/notes/manual-qa-<broker>-<os>.md` (notes directory created when the first row is recorded):
  - `creds` × macOS: real `/usr/bin/security` keychain integration with one real PAT; consuming skill resolves the token.
  - `creds` × Windows: real `advapi32.CredReadW`/`CredWriteW` integration with one real PAT.
  - `creds` × Linux: dotfile-floor path; consuming skill resolves the token.
  - `sso-cookie` × macOS: real corporate-SSO endpoint (downstream consumer environment); headed Chromium register flow completes; `test` verb returns 0 against the configured `validation_endpoint`.
  - `sso-cookie` × Windows: same against the same endpoint.
  - `sso-cookie` × Linux: file-floor path; same flow against the same endpoint.
- **`add-credentialed-skill` author-walkthrough:** invoke the skill from scratch against each broker id; assert each variant's prompts match the pinned shape; assert the `auth: creds` flow includes the explicit `make build-self` instruction.

## Tasks

The work-breakdown. Tasks are sized so each one is a coherent commit or PR.

### T1: Contract bump v0.6 → v0.7 + schema admits `metadata.auth` + frontmatter parser admits the four broker ids

**Depends on:** none

**Verification mode:** Goal-based check (for the contract version bump) + TDD (for the lint frontmatter admission).

**Tests:**
- Unit test in `packages/agentbundle/agentbundle/build/tests/test_contract_v07.py` asserts `[contract] version == "0.7"` in `_data/adapter.toml` (verifies AC1).
- Unit test in `packages/agentbundle/agentbundle/build/tests/test_contract_v07.py` asserts `allowed-prefixes.user` for each of the three adapters (`claude-code`, `kiro`, `codex`) contains `.agentbundle/` (verifies AC2 non-regression).
- Unit test in `packages/agentbundle/tests/unit/test_lint_agent_artifacts_metadata_auth.py` asserts `tools/lint-agent-artifacts.py` admits `metadata.auth` with the `ALLOWED_AUTH_BROKERS` enum under the `metadata:` escape hatch, refuses unknown values with the pinned `frontmatter key 'metadata.auth' must be one of {env, cli, creds, sso-cookie}; got '<value>'`, and refuses `metadata.credentialed: true` without `metadata.auth`. **One test file covers AC3 + AC26** — there is no separate `test_pack_schema_metadata_auth.py` because `pack.schema.json` is not touched by this task.

**Approach:**
- Edit `packages/agentbundle/agentbundle/_data/adapter.toml` and `docs/contracts/adapter.toml`: bump `[contract] version` from `"0.6"` to `"0.7"`; extend header comment in both files to name RFC-0013 alongside existing RFC pointers.
- Extend `tools/lint-agent-artifacts.py` *only* (per spec AC3 — `pack.schema.json` validates the `pack.toml` manifest, not skill frontmatter, so it is *not* touched by this task): add an `ALLOWED_AUTH_BROKERS` constant inline alongside the existing `ALLOWED_PRIMITIVE_CLASSES` (currently defined inline at `tools/lint-agent-artifacts.py:127`); admit `metadata.auth` under the `metadata:` escape hatch with that enum; require `metadata.auth` when `metadata.credentialed: true` is set; emit the pinned refusal message for unknown values.
- **Frontmatter pre-declaration on the six existing credentialed skill sources** (EXECUTE-time addition; rationale below). To keep AC26's "credentialed requires auth" rule enforceable from T1 onward without breaking `make build-check` on the live tree, T1 also adds `metadata.auth: creds` to the six in-tree credentialed `SKILL.md` sources whose import migration lands at T11–T14: `packs/atlassian/.apm/skills/{jira,jira-align,confluence-publisher,confluence-crawler}/SKILL.md`, `packs/core/.apm/skills/example-credentialed-skill/SKILL.md`, `packs/figma/.apm/skills/figma/SKILL.md`. T11–T14 still own the substantive migration (the import-line change to `from .credentials_shim import ...` plus the `metadata.namespace` and `metadata.keys` declarations); T1 only pulls the single `auth: creds` line forward so the linter's refusal rail is consistent across the whole sequence. Run `make build-self FORCE=1` to propagate the frontmatter edits into `.claude/skills/*/SKILL.md`.

**Done when:** all four tests green; `make build-check` exits 0; the six pack-source SKILL.md files carry `metadata.auth: creds` and their projected `.claude/skills/*/SKILL.md` copies match.

### T2: `credential-brokers` pack manifest + directory skeleton

**Depends on:** T1

**Verification mode:** TDD.

**Tests:**
- Integration test in `packages/agentbundle/tests/integration/test_credential_brokers_pack_install.py`: `agentbundle install --pack credential-brokers --scope user .` against a fixture `$HOME` succeeds; asserts the pack manifest validates; asserts `[pack.install] allowed-adapters = ["claude-code", "kiro", "codex"]` (verifies AC4).
- Unit test asserts the `.apm/` tree contains exactly the four declared primitive directories (`shared-libs/`, `adapter-root-bins/`, `skills/credential-setup/`, plus `pack.toml`) and **no** `seeds/`, `hooks/`, `hook-wiring/`, or extra `skills/<other>/` (verifies AC5).
- Refusal-rail test: fixture variant with an injected `seeds/` directory; install refuses with the pinned RFC-0004 stderr.

**Approach:**
- Create `packs/credential-brokers/pack.toml` per spec AC4 (verbatim `description:` from RFC-0013 § 4).
- Create the directory skeleton: `.apm/shared-libs/` (empty; T3 populates), `.apm/adapter-root-bins/` (empty; T5 populates), `.apm/skills/credential-setup/` (skeleton only; T7 populates the body).
- Run `make build-self FORCE=1` and verify no drift.

**Done when:** install integration test green; directory invariant test green; refusal-rail test green; `git status --short` clean after `make build-self`.

### T3: `credentials_shim.py` + Tier-2 backends in `shared-libs/`

**Depends on:** T2

**Verification mode:** TDD.

**Tests:**
- Golden-file unit test in `packages/agentbundle/agentbundle/build/tests/test_credentials_shim_byte_equivalence.py`: compares `packs/credential-brokers/.apm/shared-libs/credentials_shim.py` against today's `packages/agentbundle/agentbundle/creds/loader.py` byte-for-byte modulo the import-path delta (the `from agentbundle.creds.{loader,exceptions}` indirection → direct relative imports of the sibling shim's own definitions). Verifies AC6.
- Same shape for `_keychain_macos.py` and `_credman_windows.py` (byte-equivalent to `agentbundle/creds/_keychain_macos.py` and `agentbundle/creds/_credman_windows.py`).
- Stdlib-only test in `packages/agentbundle/tests/unit/test_credentials_shim_stdlib.py`: imports the shim from a fixture skill's `scripts/`; asserts `sys.modules` after import contains only stdlib modules plus the shim's own (verifies AC7).
- Round-trip test in `packages/agentbundle/tests/unit/test_credentials_shim_load_credentials.py`: invokes `load_credentials("<ns>", required_keys=[...])` against env / keychain / dotfile fixtures (mocked Tier-2 backends); asserts the same `Credentials` shape, the same `CredentialsMissingError` on missing keys, the same `Tier2HardFailError` on Win32 matrix codes — i.e. the shim's behavioural contract is byte-equivalent to today's `agentbundle.credentials.load_credentials` (verifies AC8).

**Approach:**
- Copy `packages/agentbundle/agentbundle/creds/loader.py` to `packs/credential-brokers/.apm/shared-libs/credentials_shim.py`. Rewrite the cross-module imports: previously `from agentbundle.creds.exceptions import ...` and `from agentbundle.creds._keychain_macos import ...` become local definitions or sibling-relative imports. The simplest mechanical shape: inline `exceptions.py` (69 lines) into `credentials_shim.py`'s top, and keep `_keychain_macos.py` / `_credman_windows.py` as sibling files with `from ._keychain_macos import ...` style imports.
- Copy `_keychain_macos.py` and `_credman_windows.py` byte-equivalent to `packs/credential-brokers/.apm/shared-libs/`.
- Update any `agentbundle/creds/exceptions.py` re-export inside the shim to keep `CredentialsMissingError` and `Tier2HardFailError` at the public surface.
- Verify the byte-equivalence test passes by running it once with the shim against the loader; close any diff that is not a load-bearing import-path change.

**Done when:** byte-equivalence test green for all three shim files; stdlib-only test green; round-trip test green against all three Tier fixtures.

### T4: `shared-libs/` build-pipeline primitive class + drift gate

**Depends on:** T3

**Verification mode:** TDD.

**Tests:**
- Unit test in `packages/agentbundle/agentbundle/build/tests/test_shared_libs_projection.py`: fixture pack tree with two skills (one declaring `auth: creds`, one declaring `auth: env`); asserts the shim files land in the `creds` skill's `scripts/`, do not land in the `env` skill's `scripts/`, and that the projection is byte-identical (verifies AC20 + AC25 gating).
- Unit test asserting receiving skill without a pre-existing `scripts/` directory: fixture with `SKILL.md` + `references/` only; assert projection creates `scripts/` and succeeds (verifies AC20 trailing clause).
- Three drift-gate unit tests (one per outcome — modified / missing / orphaned). Each asserts `make build-check` exits non-zero with the pinned regeneration command in stderr; each then runs `make build-self` and asserts a clean tree (verifies AC23).
- Inter-pack collision unit test: fixture with two packs both shipping `shared-libs/credentials_shim.py`; assert the build hard-errors with stderr naming both source paths (verifies AC21).

**Approach:**
- Add `shared-libs/` as a new primitive class in the build pipeline. Source rule: `packs/<pack>/.apm/shared-libs/*.py`. Target rule: for every skill in any pack whose `SKILL.md` declares `metadata.auth: creds`, project each `shared-libs/*.py` byte-identical into that skill's `scripts/` directory; create `scripts/` if absent.
- Extend `make build-check` to detect the three drift outcomes for `shared-libs/` projections.
- Extend `make build-self` to resolve all three drift outcomes (idempotent projector).
- Add the inter-pack collision check at projection time.
- Run `make build-self FORCE=1` against the live tree (no consumer migrates yet in this task; the projection has zero targets until T11 onward).

**Done when:** every test in this task green; `make build-check` exits 0 against the live tree (no `auth: creds` consumers yet).

### T5: `sso-broker.py` in `adapter-root-bins/` + bundled Tier-2 helpers

**Depends on:** T2

> **Tier-2 helper decision (resolves round-1 Blocker 5).** The broker carries its own sibling Tier-2 helpers (`packs/credential-brokers/.apm/adapter-root-bins/_sso_keychain_macos.py` and `_sso_credman_windows.py`) rather than importing T3's shim siblings via `importlib.util.spec_from_file_location` against a path the broker can't predict at install time. The bundled helpers are byte-equivalent to today's `agentbundle/creds/_keychain_macos.py` and `_credman_windows.py` modulo **filename rename only** — the keychain target-name namespace (`agentbundle:sso:<profile>` vs the existing `<namespace>:<key>` shape `_account` builds at `_keychain_macos.py:96`) is a *caller-side convention* enforced by `sso-broker.py`'s own `write_credential(...)` / `read_credential(...)` call sites, not a structural change to the helper modules themselves. The byte-equivalence is enforced by AC9b (added under the Broker surface group in spec.md). This removes the cross-task dependency on T3 and lets T3 and T5 run in parallel after T2.

**Verification mode:** TDD.

**Tests:**
- Unit tests in `packages/agentbundle/tests/unit/test_sso_broker_verbs.py` — one per verb (`register`, `get-cookies`, `test`, `refresh`, `list-profiles`, `rm`). Each mocks Playwright at the `chromium.launch_persistent_context` boundary; asserts exit codes match RFC-0013 § 4b matrix verbatim (verifies AC9).
- Profile-TOML schema test: `register` writes the canonical shape; `rm` removes; concurrent profiles for the same vendor keyed by global profile name (verifies AC10).
- Keychain integration tests (mocked Tier-2 backend; one suite per platform): `ERROR_NOT_FOUND` triggers `register` on macOS/Windows; Linux floors to 0600 file; hard-fail codes exit non-zero with stderr (verifies AC11).
- Cookie-jar continuation tests: fixture serialised jar > 2 KB splits into header + continuation credentials; fixture backend refusing continuation overflows to file (verifies AC12).
- Playwright import-guard test: invokes the broker with `playwright` not on `sys.path`; assert stderr matches the pinned `sso-broker: playwright not installed. ...` (verifies AC13).
- Env-passthrough test: asserts `subprocess.run` and the `chromium.launch_persistent_context` call both receive `env={**os.environ, ...}` (verifies AC14).
- Mid-session cookie rotation test: fixture downstream-401 sequence triggers `register` on next `test` failure; no silent in-band refresh (verifies AC15).

**Approach:**
- Write `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py` from scratch. Use `argparse` for verb dispatch; use `chromium.launch_persistent_context` for the headed flow.
- Bundle Tier-2 helpers as sibling files `_sso_keychain_macos.py` and `_sso_credman_windows.py` in `adapter-root-bins/`. Byte-equivalent to today's `agentbundle/creds/_keychain_macos.py` / `_credman_windows.py` modulo the filename rename only (the helper modules carry no `agentbundle:*` literal — the namespace is supplied by the caller; `sso-broker.py` calls `write_credential("agentbundle:sso", profile)` and equivalents). The broker imports them via standard relative imports (`from ._sso_keychain_macos import …`) — no `importlib.util.spec_from_file_location` plumbing; the broker and its helpers all land as siblings at `~/.agentbundle/bin/` via `adapter-root-bins/` projection. Per spec AC9b, a golden-file test pins the byte-equivalence; per a new T5 test, every `write_credential` / `read_credential` call site in `sso-broker.py` is asserted to construct target names of shape `agentbundle:sso:<profile>`.
- Reserve the `agentbundle:sso:*` keychain-target prefix scheme for cookie-jar continuation (AC12). Document the prefix list at the top of the file.
- Honour the corporate-network env-passthrough discipline in every subprocess call.

**Done when:** every test in this task green; the broker is executable as a standalone script (`python3 sso-broker.py --help` works without `agentbundle` on `sys.path`).

### T6: `adapter-root-bins/` build-pipeline primitive class

**Depends on:** T5

**Verification mode:** TDD.

**Tests:**
- Unit test in `packages/agentbundle/agentbundle/build/tests/test_adapter_root_bins_projection.py`: install fixture pack at user scope; assert `~/.agentbundle/bin/sso-broker.py` exists with mode `0o755 & 0o777 == 0o755` on POSIX; assert byte-equivalent to source (verifies AC22).
- Repo-scope variant: install at repo scope; assert `<repo>/.agentbundle/bin/sso-broker.py` exists.
- Path-jail compliance test: assert the projection target falls under the pack's `allowed-prefixes.user` (`.agentbundle/` — already in the v0.7 contract for the three named adapters).
- No-PATH-manipulation test: `os.environ["PATH"]` unchanged before/after `agentbundle install`.

**Approach:**
- Add `adapter-root-bins/` as a new primitive class in the build pipeline. Source rule: `packs/<pack>/.apm/adapter-root-bins/*.py`. Target rule: project to `$HOME/.agentbundle/bin/<basename>.py` at user scope; `<repo>/.agentbundle/bin/<basename>.py` at repo scope.
- Set POSIX mode bits to `0o755` after copying. Windows: rely on inherited DACL (no explicit `chmod` call).
- Update `make build-check` and `make build-self` to handle the new class.

**Done when:** every test in this task green; `make build-check` exits 0; `make build-self FORCE=1` produces a clean tree.

### T7: `credential-setup` skill body + reserved-prefix rejection

**Depends on:** T3

**Verification mode:** TDD.

**Tests:**
- `SKILL.md` frontmatter parse test asserts the verbatim `description:` phrase *"interactive, user-invoked, do not auto-run"* (verifies AC18).
- `### Security rules (non-negotiable)` block presence test asserts the broker-agnostic block per RFC-0013 § 5 (verifies AC18).
- Mock-`getpass` test invokes `scripts/setup.py` with namespace `gitlab` + key `token`; asserts the prompt is interactive; asserts `capfd.readouterr().out` does not contain the entered value (token never on stdout) (verifies AC18).
- Reserved-prefix rejection test: invoke setup with namespace `sso`; assert non-zero exit and stderr names the reserved set `{"sso"}` (verifies AC19).
- Tier-write test: setup writes the credential to the chosen tier (env-var instruction printed; keychain when `--keychain`; dotfile floor when `--allow-insecure-fallback`); preserves RFC-0006 § 3 discipline verbatim.

**Approach:**
- Write `packs/credential-brokers/.apm/skills/credential-setup/SKILL.md` with the verbatim `description:` phrase, the `### Security rules (non-negotiable)` block, and a step-by-step walkthrough mirroring today's `agentbundle creds setup` invocation guidance.
- Write `packs/credential-brokers/.apm/skills/credential-setup/scripts/setup.py` using `getpass` for the prompt and the shim's Tier-2 backends for the write. Import the shim's helpers via the projected sibling path (since the setup skill also declares `auth: creds`).
- Implement the reserved-prefix rejection at the namespace prompt.

**Done when:** every test in this task green; the setup script never prints the entered token to stdout under any code path.

### T8: Lint extension — broker-agnostic checks + per-broker AST walks

**Depends on:** T4, T6

**Verification mode:** TDD.

**Tests:**
- Broker-agnostic Don't-block presence test: one fixture skill per broker id (4 total); each missing the `### Security rules (non-negotiable)` block; assert lint fails with the pinned message (verifies AC24).
- Argv-ban test: fixture skill with `--token` in its `scripts/`; assert lint fails (verifies AC24, mirrors existing AC26(a)).
- Dotfile-substring test: fixture skill with `.agentbundle/credentials.env` in a string literal; assert lint fails unless the opt-out marker `# credentialed-primitive: reads-creds-directly` is on the same line (verifies AC24). Path-check composition uses basename + `Path.parts`; assert the lint script itself does not trip its own check.
- `auth: creds` AST test: fixture skill with `metadata.auth: creds` but no `from .credentials_shim import` in `scripts/`; assert lint fails. Inverse fixture (import present) passes (verifies AC25 / `auth: creds` line).
- `auth: env` AST test: fixture skill with `metadata.auth: env`, `metadata.namespace: foo`, `metadata.keys: ["BAR"]`, but no `os.getenv("FOO_BAR")` or `os.environ["FOO_BAR"]` read in `scripts/`; assert lint fails. Inverse fixture passes; second inverse fixture additionally reads `os.getenv("PATH")` (non-declared) — assert lint still passes (presence-only, not exhaustivity; verifies AC25 / `auth: env` line + the no-exhaustivity invariant in Boundaries).
- `auth: sso-cookie` AST test: fixture skill with `metadata.auth: sso-cookie` invoking `subprocess.run(["/some/other/path/sso-broker.py", ...])`; assert lint fails (non-`Path.home()` absolute path). Inverse fixture with `subprocess.run([sys.executable, str(Path.home() / ".agentbundle" / "bin" / "sso-broker.py"), ...])`; assert lint passes (verifies AC25 / `auth: sso-cookie` line + AC17).
- `auth: cli` no-positive-grep test: fixture skill with `metadata.auth: cli`; assert lint applies only broker-agnostic checks; no false positive on missing `from .credentials_shim` import (verifies AC25 / `auth: cli` line).
- Lint-of-self test: invoke the lint against `tools/lint-credentialed-skills.sh` (or its Python sibling) itself; assert no false positive from the lint's own search strings. Coverage extends to all four broker-specific AST checks (not just the existing dotfile check): one self-test fixture per broker-id verifies that the lint script's own source text — which inevitably contains the strings `from .credentials_shim`, `Path.home() / ".agentbundle" / "bin" / "sso-broker.py"`, `os.environ`, `os.getenv` — does not trip the script's own broker-specific rules. Composition must use basename + `Path.parts` rather than literal-string substring (per `feedback_credentialed_lint_substring_trap`); the test enforces this by running each check against the lint source.

**Approach:**
- Extend `tools/lint-credentialed-skills.sh` (or introduce a Python sibling `tools/lint_credentialed_skills.py` if AST-walk requirements exceed shell ergonomics) with the broker-agnostic and broker-specific checks. AST-walks for `auth: creds` and `auth: sso-cookie` are Python-based; `auth: env` is Python-based for the AST walk.
- The Don't-block substitutions per RFC-0013 § 5 are checked literally per broker.
- Compose path-checks via `os.path.basename` + `Path(...).parts`; never the literal full-path string.
- Add the lint to `tools/hooks/pre-pr.py` if not already wired.

**Done when:** every test in this task green; `tools/hooks/pre-pr.py` exits 0 against the current tree (no in-tree consumer has migrated yet; the new checks don't fail against `auth: env`-less or pre-migration `auth: creds`-less skills because today's existing credentialed skills don't yet declare `metadata.auth`).

### T9: `add-credentialed-skill` template variants (env, cli, creds, sso-cookie)

**Depends on:** T1

**Verification mode:** TDD.

**Tests:**
- Four template-file presence tests: `assets/credentialed-skill-SKILL-{env,cli,creds,sso-cookie}.md` exist and parse as valid SKILL.md frontmatter (verifies AC27).
- Per-template Don't-block test: each template's `### Security rules (non-negotiable)` block matches RFC-0013 § 5's per-broker substitution shape.
- Author-flow integration test: invoke `add-credentialed-skill` against a fixture; assert the broker prompt comes first; assert the correct template is copied per broker id; assert the `auth: creds` flow includes the verbatim `make build-self` instruction (RFC-0013 § 7).

**Approach:**
- Write four template files under `packs/core/.apm/skills/add-credentialed-skill/assets/`. Each template instantiates RFC-0013 § 5's broker-specific Don't-block plus the broker-agnostic invariants. **Divergence from RFC-0013 § 5 closing paragraph noted:** RFC § 5 closing says "the four substituted variants ship as labelled sections under the … existing `assets/credentialed-skill-SKILL.md` template" — i.e. one file with labelled sections. The spec / plan ship four separate files instead because (a) the `add-credentialed-skill` author flow picks broker first and copies one template, making the per-file shape simpler for the script's "copy this template" step than parsing labelled sections from one file; (b) lint of each variant is per-file rather than per-section grep; (c) the divergence is purely an implementation-detail shape (the per-broker Don't-block content is the same in either layout). The spec records this divergence in its round-1 revision changelog.
- Update the `add-credentialed-skill` SKILL.md body to ask "which broker?" first, then dispatch to the matching template.
- Update the `auth: creds` flow's user-facing prompt to include the explicit `make build-self` instruction per RFC-0013 § 7.
- Existing `primitive-class: credentialed-cli` vs `mcp-server` distinction stays orthogonal — the templates are keyed on `auth:`, not `primitive-class:`.

**Done when:** every test in this task green; the author skill walks through each broker variant interactively without error.

### T10: Documentation surface — ADR + CONVENTIONS + ROADMAP + guide + sibling spec amendments

**Depends on:** T1

**Verification mode:** Goal-based check (file presence + grep) + Manual QA (reading the prose end-to-end).

**Tests:**
- File-presence checks: `docs/adr/NNNN-credential-broker-contract.md` exists and parses as an ADR (verifies AC40).
- `docs/CONVENTIONS.md` contains a § Credentialed skills section naming the four brokers and `metadata.auth` (verifies AC41).
- `docs/ROADMAP.md` contains a `credential-broker-contract` entry with the manual-QA matrix lines (verifies AC42).
- `docs/guides/how-to/add-a-credentialed-skill.md` "pick a broker" section replaces the old "pick a primitive class" section (verifies AC43).
- `docs/specs/skill-secrets/spec.md` carries the footer note pointing AC34/AC35 invariants to the new shim (verifies AC44).
- `docs/specs/distribution-adapters/spec.md` carries a single new dated bullet under `## Changelog` matching the verbatim text from `notes/distribution-adapters-amendment.md` — no conformance-suite addition (per AC45 round-2 revision: distribution-adapters defers conformance to RFC-0003; the two primitive classes are pinned by *this* spec's ACs).
- Manual review reads the diff end-to-end and verifies internal consistency.

**Approach:**
- Write the new ADR per existing format under `docs/adr/`. Record the binding architectural choices and one-line rejections of alternatives B / D / E / F / G / H / I / J.
- Amend `docs/CONVENTIONS.md` with the new § Credentialed skills section (or extend an existing one).
- Add the `credential-broker-contract` entry to `docs/ROADMAP.md`.
- Rewrite the relevant section of `docs/guides/how-to/add-a-credentialed-skill.md`.
- Amend `docs/specs/skill-secrets/spec.md` (footer note).
- Amend `docs/specs/distribution-adapters/spec.md` with a single Changelog bullet (verbatim from `notes/distribution-adapters-amendment.md`); no conformance-suite addition.

**Done when:** every file-presence check passes; the manual read confirms internal consistency.

### T11: Migrate `example-credentialed-skill` (canonical reference, migrates first)

**Depends on:** T4, T8

**Verification mode:** TDD.

**Tests:**
- Import-shape test in `packages/agentbundle/tests/unit/test_example_credentialed_skill_migration.py`: imports `packs/core/.apm/skills/example-credentialed-skill/scripts/cli.py` (after `make build-self` projects the shim); assert no `from agentbundle.credentials` in the source; assert `from .credentials_shim import (CredentialsMissingError, Tier2HardFailError, load_credentials)` is present (verifies AC28).
- Frontmatter test: `SKILL.md` declares `metadata.auth: creds`, `metadata.namespace: example`, `metadata.keys: ["API_TOKEN"]` (verifies AC28).
- Construction test: the skill's existing test suite continues to pass after the migration (verifies AC35 for this consumer).
- Lint test: `tools/lint-credentialed-skills.sh` against this skill exits 0 (verifies AC25's `auth: creds` AST check passes against a real consumer).

**Approach:**
- Edit `packs/core/.apm/skills/example-credentialed-skill/SKILL.md` frontmatter: add `metadata.auth: creds`, `metadata.namespace: example`, `metadata.keys: ["API_TOKEN"]`.
- Edit `packs/core/.apm/skills/example-credentialed-skill/scripts/cli.py`: replace `from agentbundle.credentials import ...` with `from .credentials_shim import ...` (preserving the imported names).
- Run `make build-self FORCE=1`; verify the shim files now project into the skill's `scripts/`.
- Re-run the existing example-skill test suite; verify all green.

**Done when:** every test in this task green; `make build-check` exits 0; the skill's `scripts/` contains `credentials_shim.py`, `_keychain_macos.py`, `_credman_windows.py` after `make build-self`.

### T12: Migrate `figma` skill

**Depends on:** T11 (must land sequentially after T11 to avoid `make build-self` race against shared shim-projection targets; not parallelizable with T13/T14)

**Verification mode:** TDD.

**Tests:**
- Same shape as T11: import-shape test, frontmatter test, construction test (existing figma skill tests), lint test (verifies AC29 + AC35 for this consumer).

**Approach:**
- Same shape as T11. Frontmatter: `metadata.auth: creds`, `metadata.namespace: figma`, `metadata.keys: ["API_TOKEN"]` (matches the actual `creds-schema.toml`; spec changelog 2026-05-26 (T8/T11-T13) records the correction from the original aspirational `["token"]`).
- Edit `packs/figma/.apm/skills/figma/scripts/_client.py` import line.
- Run `make build-self FORCE=1`.

**Done when:** every test in this task green; `make build-check` exits 0; figma skill's tests all green.

### T13: Migrate the four atlassian skills (`jira`, `jira-align`, `confluence-publisher`, `confluence-crawler`)

**Depends on:** T12 (sequential after T12; same build-self race rationale)

**Verification mode:** TDD.

**Tests:**
- Per-skill (×4): import-shape test, frontmatter test, construction test, lint test (verifies AC30 + AC31 + AC32 + AC33 + AC35 for the four consumers).

**Approach:**
- Bundled into one PR because the four skills share the same pack, the same `creds-schema.toml` pattern, and the import-line change is identical across all four.
- Per skill, edit `scripts/_client.py` import line and `SKILL.md` frontmatter. Values match the actual `creds-schema.toml`s (spec changelog 2026-05-26 (T8/T11-T13) records the correction from the original aspirational lowercase / hyphenated values):
  - `jira`: `namespace: jira`, `keys: ["API_TOKEN"]`.
  - `jira-align`: `namespace: jiraalign` (no hyphen — matches `_client.py`'s `load_credentials("jiraalign", …)`), `keys: ["API_TOKEN"]`.
  - `confluence-publisher`: `namespace: confluence`, `keys: ["API_TOKEN"]`.
  - `confluence-crawler`: `namespace: confluence`, `keys: ["API_TOKEN"]`.
- Run `make build-self FORCE=1`; verify the shim files project into all four skills' `scripts/`.

**Done when:** every test in this task green; `make build-check` exits 0; all four atlassian skills' tests all green.

### T14: Migrate `add-credentialed-skill` SKILL.md teaching block

**Status (EXECUTE-time amendment, 2026-05-26):** T14's substantive surface — the `from .credentials_shim` teaching block and the broker-selection prose — landed during T9 (templates) and T10 (docs); the live tree at PR-A time already carries the post-migration shape. T14 contributes *no additional code* in PR-A. AC34's separation gate remains strict: T15 lands in a separate PR from whichever commit last modified `add-credentialed-skill/SKILL.md`. The plan changelog 2026-05-26 (T8/T11-T13) records the absorption.

**Depends on:** T13 (was: sequential after T13. The dependency is preserved for *temporal* ordering even though no additional commit lands.)

**Verification mode:** Goal-based check.

**Tests:**
- Grep test: `packs/core/.apm/skills/add-credentialed-skill/SKILL.md` no longer contains `from agentbundle.credentials`; contains `from .credentials_shim` (verifies AC34). Already satisfied at PR-A time.
- Manual-read test (Goal-based): the surrounding teaching prose walks the author through `metadata.auth` selection and the build-pipeline projection. Already satisfied.
- **Separation-gate goal-based check** (per AC34 separation gate): the teaching-block edit must predate T15's merge commit. Three-part check: (a) `git log --diff-filter=M packs/core/.apm/skills/add-credentialed-skill/SKILL.md` returns at least one commit and the **last** such commit carries the `from .credentials_shim` shape (per the AC34 rewrite to `<teaching-block-last-edit>`); (b) `git log --oneline --reverse --diff-filter=D packages/agentbundle/agentbundle/credentials.py` returns the T15 commit; (c) `git merge-base --is-ancestor <teaching-block-last-edit> <T15-merge>` exits 0.

**Approach:**
- No new edits in PR-A. The substantive teaching-block content shipped via T9/T10.
- T15 (PR-B) verifies the separation gate as part of its Done-when.

**Done when:** every test in this task green; the AC34 separation-gate query resolves cleanly when T15 lands.

### T15: Cleanup — remove `agentbundle.credentials` + `agentbundle/creds/`; bump version 0.1.x → 0.2.0; CHANGELOG

**Depends on:** T12, T13, T14

**Verification mode:** Goal-based check.

**Tests:**
- File-absence checks: `packages/agentbundle/agentbundle/credentials.py` does not exist; `packages/agentbundle/agentbundle/creds/` does not exist (verifies AC36).
- Version check: `grep '^version = "0.2.0"' packages/agentbundle/pyproject.toml` returns one line (verifies AC37).
- CHANGELOG check: `packages/agentbundle/CHANGELOG.md` exists with the verbatim migration recipe from RFC-0013 § 9; concrete versions substituted (e.g. *"adopters running `agentbundle 0.1.x` continue to receive bug-fix releases through 0.1.last; pin to `agentbundle < 0.2` until you have migrated"*) (verifies AC38).
- Grep test: `git grep "from agentbundle.credentials"` returns no matches under `packs/` or `packages/agentbundle/`.
- Aggregate test: `pytest packages/agentbundle/` exits 0; `python3 tools/hooks/pre-pr.py` exits 0; `make build-check` exits 0 (verifies AC39 + the final-state gates).

**Approach:**
- Delete `packages/agentbundle/agentbundle/credentials.py` and `packages/agentbundle/agentbundle/creds/` (the entire subpackage: `__init__.py`, `loader.py`, `exceptions.py`, `_keychain_macos.py`, `_credman_windows.py`).
- **Test files — explicit per-file disposition** (the new shim tests in T3 + per-consumer migration tests in T11-T14 cover the post-rip contract; T15 disposes of the old loader-only tests):
  - `packages/agentbundle/tests/unit/test_credentials_loader.py` — **delete** (T3's golden-file + round-trip tests against the shim cover the loader contract).
  - `packages/agentbundle/tests/unit/test_credentials_parser.py` — **delete or relocate** to a shim-side test (the `parse_env_file` / `EnvParseError` surface moves with the shim; if T3's tests don't already cover the parser surface, copy the parser tests into the shim's test file before deleting this one).
  - `packages/agentbundle/tests/unit/test_credentials_dotfile.py` — **delete or relocate** (Tier-3 dotfile behaviour moves with the shim).
  - `packages/agentbundle/tests/unit/test_credentials_fixtures.py` — **delete or relocate** (fixture-level tests for the loader's Tier walk; shim-side coverage).
  - `packages/agentbundle/tests/unit/test_credentials_schema.py` — **delete** (schema is `creds-schema.toml` consumer-side per RFC-0006; shim tests pin the contract).
  - `packages/agentbundle/tests/unit/test_credentials_no_live_writes.py` — **delete** (live-write safety asserts the loader's no-side-effect contract; shim preserves the contract under T3).
  - `packages/agentbundle/tests/unit/test_creds_helpers.py` — **delete** (helpers move with the shim).
  - `packages/agentbundle/tests/integration/test_credentials_wheel.py` — **rewrite to assert absence**: after T15 the wheel no longer exposes `agentbundle.credentials`. The test asserts `import agentbundle.credentials` raises `ImportError` against the installed wheel.
  - `packages/agentbundle/tests/integration/test_creds_cli.py` — **delete** (the `agentbundle creds` subcommand is removed alongside the module per RFC-0013 § 3).
  - `packages/agentbundle/tests/integration/test_conventions_check_creds.py` — **delete or relocate** (lint convention checks now live with `tools/lint-credentialed-skills.sh` per T8).
  - `packages/agentbundle/tests/unit/test_keychain_macos_logic.py` — **rewrite or relocate** to test the projected shim's `_keychain_macos.py` (the helper's behaviour is preserved byte-equivalent per AC6 — but the import path becomes sibling-relative inside a consumer skill's `scripts/`; the test imports from a fixture skill rather than from `agentbundle.creds`).
  - `packages/agentbundle/tests/unit/test_credman_windows_logic.py` — **rewrite or relocate** same shape as above.
  - `packages/agentbundle/tests/integration/test_keychain_macos.py` — **rewrite to a shim-side integration** (real `/usr/bin/security` exercise against the projected shim — feeds into T3 / T11 round-trip coverage) or **delete** if the round-trip test in T3 already covers the real-keychain path.
  - `packages/agentbundle/tests/integration/test_credman_windows.py` — **rewrite or delete** same shape.
  - `packages/agentbundle/tests/integration/test_example_credentialed_skill.py` — **rewrite as part of T11** (this is the canonical-reference migration's integration test; T11 already touches it for the post-migration shape; T15 just confirms it doesn't re-import the removed surface).
  Total: 15 test files explicitly disposed across T11 (1, the example-skill integration) and T15 (10 + 4 helper-logic tests = 14). Any test importing `agentbundle.creds` or `agentbundle.credentials` after T15 lands fails the AC39 grep gate.
- Bump `packages/agentbundle/pyproject.toml` `version` from `0.1.x` (whatever patch the prior PR shipped) to `0.2.0`.
- Write `packages/agentbundle/CHANGELOG.md` (create if absent) with the verbatim migration recipe from RFC-0013 § 9. Substitute the concrete prior-minor (via `git describe --tags --match 'agentbundle-v0.1.*' --abbrev=0`) and new-minor (`0.2.0`) versions.
- **Finishing ghost-CLI sweep** (handed off from PR-A per plan changelog 2026-05-26 (g)): remove or replace remaining `agentbundle creds setup <ns>` / `agentbundle creds where` / `agentbundle creds check` / `agentbundle creds rm` references in: each consumer skill's `SKILL.md` body prose; each `evals/evals.json` expected_output / grading_criteria; each `references/creds-schema.toml` header comment; the seed-side CONVENTIONS template under `packs/core/seeds/docs/CONVENTIONS.md`; the `credential-setup` skill's `## Inverse —` section heading; the `credentials_shim.py` docstring. The replacement maps the four verbs to the post-cleanup language (`setup` → `credential-setup` skill; `where` → drop or describe Tier walk; `check` → drop or describe exit code; `rm` → drop or describe `keychain`/`security` CLI direct usage).
- Verify the aggregate gates.

**Done when:** every test in this task green; the agentbundle package contains no credential-resolution surface; the final-state pre-pr gate passes.

## Rollout

**Sequencing.** Phase 1 (T1–T10) lands first. T1 alone (contract + schema + parser) can ship as a small standalone PR; T2–T10 ship as four-to-six PRs grouped by surface (broker pack + shim; sso-broker + adapter-root-bins; setup skill; lint; templates; docs). Phase 2 (T11–T14) ships next, with T11 first as the canonical reference and T12/T13/T14 sequenced or parallel depending on reviewer bandwidth. Phase 3 (T15) ships last.

**Reversibility.** Phase 1 PRs are *locally* reversible by `git revert` against the catalogue, **only as long as the `credential-brokers` pack has not yet shipped to PyPI / APM / Claude plugins**. Once `credential-brokers` is published declaring `[pack.adapter-contract] version = "0.7"`, the contract bump (AC1) becomes effectively forward-only — any adopter who has installed the pack carries a v0.7 expectation that a reverted v0.6 binary cannot honour, and the `[pack.adapter-contract]` validate-time check (per RFC-0011's contract-version gate) refuses the older binary. Phase 2 PRs are reversible per-consumer (the prior `from agentbundle.credentials` import shape is restorable while the cleanup is pending). Phase 3 (T15) is irreversible inside the 0.x window per RFC-0013 Drawbacks; mitigation is the prior `agentbundle 0.1.x` minor staying on PyPI as the rollback target.

**No feature flag.** The migration is mechanical (one import-line change per consumer); flag-gating would add surface for zero behavioural difference. The sequencing itself is the gating mechanism — `agentbundle.credentials` stays importable until the cleanup PR.

**Adopter pin policy.** Documented in T15's CHANGELOG and in the `agentbundle` package release notes. Adopters running `agentbundle 0.1.x` continue to receive bug-fix releases through the prior minor; the cleanup PR's release bumps to 0.2.0 and removes the module; adopters pin to `agentbundle < 0.2` until they migrate (the migration shape is the same one-line import change documented in the changelog).

## Risks

- **Shim byte-equivalence drift.** The carry-over from `agentbundle/creds/loader.py` to `packs/credential-brokers/.apm/shared-libs/credentials_shim.py` requires inlining the `exceptions.py` definitions and rewriting the cross-module imports. The "byte-equivalent modulo import path" claim in AC6 can become "byte-equivalent modulo import path AND inlined exceptions AND ...". Mitigation: the golden-file test in T3 pins what equivalence means; any divergence beyond the named delta is a test failure that surfaces immediately. The test fixture must be precise.
- **`shared-libs/` projection target inference.** The projection fires per skill declaring `metadata.auth: creds`. If a future skill declares `auth: creds` but lives outside the four-pack scope this RFC migrates, the projection still fires — by design. Risk: a misconfigured frontmatter (e.g. `auth: creds` without `namespace`) triggers projection without the lint catching it. Mitigation: T8's lint requires `namespace` + `keys` for `auth: creds`; T4's projection runs after build-check, which runs the lint, so a misconfigured skill fails earlier than projection.
- **`sso-broker.py` testability.** The verb-correctness tests mock Playwright at the `chromium.launch_persistent_context` boundary. A real-corp-SSO regression (e.g. a redirect-chain pattern change) is not caught in CI; only the manual-QA matrix catches it. Mitigation: the manual-QA transcripts in `notes/manual-qa-*.md` document the real-endpoint exercise; the downstream consumer environment carries the existing two `browser_auth.py` scripts to compare against.
- **CHANGELOG version substitution.** T15's CHANGELOG must substitute concrete versions for the template literals in RFC-0013 § 9. If the prior minor's last patch is unclear at PR time (because Phase 1 / Phase 2 ship multiple intermediate patch releases), the substitution can land wrong. Mitigation: Phase 1 / Phase 2 PRs do **not** bump the minor (per RFC-0013 § 9); they ship as patch releases (`0.1.1`, `0.1.2`, ...) and T15 substitutes whatever the final patch is.
- **Manual-QA matrix coverage.** The matrix has six rows (3 OS × 2 brokers); only the downstream consumer environment can exercise `sso-cookie` against a real corporate SSO. Risk: the matrix lands incomplete because the downstream environment is not always available. Mitigation: per AC42, the ROADMAP entry tracks each row's verification status; rows that ship unverified are documented as "transcript pending" rather than silently skipped.
- **Drift between `_data/adapter.toml` and `docs/contracts/adapter.toml`.** Two copies of the contract file. Today's repo carries both at v0.6; T1 bumps both to v0.7. Risk: a future contract change misses the mirror. Mitigation: the `build-check` drift gate (per `feedback_build_self_undoes_projection_only_edits`) covers this — and the implementation in T1 cross-checks both files in one test.

## Changelog

Revisions are listed most-recent-first; the Initial Draft anchors the floor.

- 2026-05-26 (T15 EXECUTE-time revision) — Cleanup PR (PR-B). **(a) `agentbundle.credentials` + `agentbundle.creds/` + `agentbundle.commands.creds` removed**; the `agentbundle creds` CLI subcommand registration unwired from `agentbundle/cli.py`. **(b) Pyproject version bumped 0.1.0 → 0.2.0**; the prior-minor concrete version resolved via `git tag --list 'agentbundle-v0.1.*'` returned empty (no agentbundle tags exist yet — the prior-minor substitution uses `0.1.0` literally per AC38). **(c) `packages/agentbundle/CHANGELOG.md` created** with the verbatim migration recipe + adopter pin policy. **(d) Test-file disposition completed per the plan's enumeration**: 14 deleted, 1 rewritten to assert-absence (`test_credentials_wheel.py`), 1 in-place updated for the shim's `_parse_schema` (`test_example_credentialed_skill.py`). The byte-equivalence test `test_credentials_shim_byte_equivalence.py` is part of the delete set — its premise (compare against `agentbundle/creds/loader.py`) is gone with the source. **(e) Finishing ghost-CLI sweep completed** (handed off from PR-A): `SKILL.md` prose, `evals/evals.json` expected-output / grading-criteria, `manifest.json` setup hints, `references/creds-schema.toml` header comments, the seed-side `CONVENTIONS.md` template's verb list (rewritten to describe the architectural rule rather than enumerate four removed verbs), and the `credentials_shim.py` docstring all updated. **(f) credential-setup skill description triggers** updated — `"agentbundle creds setup"` trigger phrase replaced with `"credential broker setup"`. The `## Inverse — agentbundle creds where <namespace>` section rewritten to describe the consumer-skill `check` verb pattern. **(g) AC34 separation gate honoured**: PR-A (T8+T11-T13, bundling the T14 absorption-acknowledgement) merged first; PR-B (this PR) is distinct.
- 2026-05-26 (T8/T11-T13 EXECUTE-time revision) — Multiple discoveries during PR-A execution. **(a) PR bundling revised.** T1's earlier EXECUTE-time amendment added `auth: creds` to all six in-tree credentialed SKILL.md sources upfront. T8's new `auth: creds` AST check (per AC25 — `from .credentials_shim import` must be present in `scripts/`) therefore refuses every pre-migration consumer. The "PR-A: T8 only" structure suggested in Rollout was viable only under the original assumption that T1 had not yet added `auth: creds`. Revised plan: PR-A bundles T8 + T11 + T12 + T13 (lint + import migrations land atomically; gates remain green throughout the diff); PR-B is T15 alone per AC34's strict separation gate. T14 (`add-credentialed-skill` teaching block) had already been absorbed into PRs covering T9 (templates) and T10 (docs) — the live tree already declares `from .credentials_shim` in the teaching prose — so T14 contributes *no additional code* in PR-A. AC34's separation-gate query (`git log --diff-filter=M packs/core/.apm/skills/add-credentialed-skill/SKILL.md`) resolves to the T9/T10 merge commit; the strict-separation requirement (the T14 commit predates the T15 commit) is honored because T15 is PR-B and lands after PR-A. Task count and dependency edges unchanged. **(b) AC29-AC33 keys/namespace amended** to match the actual `creds-schema.toml` of each consumer (see spec changelog 2026-05-26). **(c) AC25 `auth: sso-cookie` text rewritten** to describe the implemented two-coupled-check shape (module-wide path-chain survey + `subprocess.run` presence check); the original "first argument resolves to" wording refused the common `broker = str(Path.home() / …); subprocess.run([…, broker, …])` idiom. **(d) `RFC_AUTHORISED_DIRS` allowlist update for `.agentbundle/`.** T6 (already shipped at commit `df2407c`) introduced the `adapter-root-bins/` projection target at the new top-level `.agentbundle/` directory; `tools/lint-build.py`'s allowlist was not updated to admit it, leaving `make pre-pr` red on every PR touching the catalogue. Closed in PR-A: `.agentbundle` added to `RFC_AUTHORISED_DIRS` with the RFC-0013 reference. Pre-existing gap; not in this spec's ACs but inseparable from the broker-pack surface. **(e) `tools/hooks/pre-pr.py` wires the credentialed-skill lint** per T8 Approach (source: `packs/core/.apm/hooks/pre-pr.py`); previously only run on-demand via `conventions-check`. **(f) `tools/test-lint-credentialed-skills.py` shipped** — 16-case fixture-driven self-test covering all four broker variants plus lint-of-self positive and a lint-source-no-literal-traps guard (asserts the lint script's own source never carries the forbidden multi-segment path strings as one literal). **(g) Partial ghost-CLI sweep in PR-A.** Scripts users execute at runtime (`_client.py` docstrings + runtime stderr messages + the six entry-point `*.py` modules) migrated from `agentbundle creds setup <ns>` / `agentbundle creds where <ns>` / `agentbundle creds check` to the `credential-setup` skill invocation or descriptive prose (per T14 "surrounding prose updated"). The broader sweep — `SKILL.md` body text, `evals/evals.json` expected-output strings, `manifest.json` setup hints, `references/creds-schema.toml` header comments, the seed CONVENTIONS template — is **deferred to T15** (PR-B) where the CLI itself is removed; T15's task body owns the finishing sweep so the cleanup PR also ships the final adopter-facing prose update. Honest scoping: PR-A bridges only the surfaces a running consumer hits; the unmigrated SKILL.md / evals / manifest text remains valid until T15.
- 2026-05-26 (T2-T4 EXECUTE-time revision) — PR-B (T2 + T3 + T4) execution discoveries: **(a)** AC6.3 amended in spec — Tier-2 backend dispatch is carried over byte-equivalent rather than rewritten (both `from . import X as Y` and `from .X import …` are sibling-relative; the rewrite was unnecessary). **(b)** SHIM_BASENAMES exemption added to `tools/lint-credentialed-skills.sh` for AC26(c) (dotfile-substring check); the exemption is byte-anchored against the canonical source so hand-rolled files cannot bypass — spec AC24 amended to record this. **(c)** Build-self projects shim files into 6 in-tree credentialed consumer skills' `scripts/` from T4 onwards (because T1 added `auth: creds` to their SKILL.md sources); the projection lands the files but consumers still import from `agentbundle.credentials` until T11+ migrates them. **(d)** Apply_projection enhanced to remove orphans (closes AC23's "build-self resolves all three drift outcomes"); orphan rail now uses the static `KNOWN_SHIM_BASENAMES` allow-list so dropping the source pack still surfaces stale projected copies. **(e)** Added `packs/credential-brokers/.claude-plugin/plugin.json` for marketplace inclusion. **Deferred concerns (PR description tracks):** stdlib-name-shadowing rail for `shared-libs/` basenames (Concern); symlink-write hardening in `apply_projection`; lint regex/YAML divergence on quoted `auth: "creds"` form; integration test for drift-gate wiring in `run_build_check_drift_gates`; test for `[primitive."shared-libs"]` declaration in contract.
- 2026-05-26 (EXECUTE-time revision) — During T1 implementation, discovered that AC26's "metadata.credentialed: true requires metadata.auth" refusal rail breaks `make build-check` against the live tree: the six in-tree credentialed `SKILL.md` sources declare `credentialed: true` today but won't declare `auth: creds` until T11–T14's import migrations land. Resolved by extending T1's Approach with one mechanical edit per existing credentialed skill source — adding `metadata.auth: creds` only — and running `make build-self FORCE=1` to propagate. T11–T14 unchanged in substance: still responsible for the import-line change and the `namespace` + `keys` declarations. The spec's AC text is unchanged; only T1's Approach gains a bullet plus an updated Done-when clause.
- 2026-05-26 (round-3 review revision) — Round-3 findings addressed. **T10 / Tests** corrected to drop the "conformance-suite addition" reference (contradicted AC45 round-2 revision). **T15 test cleanup** extended to 14 enumerated test files (added the four `_logic` / `_keychain_macos` / `_credman_windows` integration tests and the `test_example_credentialed_skill.py` integration coordination with T11). **T14 separation-gate test** strict-aligned with AC34's distinct-PR requirement (same-PR escape parenthetical removed). **T1 Tests** consolidated to one file (`test_lint_agent_artifacts_metadata_auth.py`) covering AC3 + AC26; the phantom `test_pack_schema_metadata_auth.py` (left over from the dropped pack.schema.json reference) is removed.
- 2026-05-26 (round-2 review revision) — Round-2 findings addressed. **T1 Approach corrected** to drop `pack.schema.json` and target `tools/lint-agent-artifacts.py` only with the `ALLOWED_AUTH_BROKERS` inline constant. **T5 Tier-2 byte-equivalence allow-list corrected** to filename-rename only (no `agentbundle:*` literal delta — namespace is caller-supplied). **T15 test cleanup enumerated** per-file (delete vs. rewrite vs. relocate, ten test files explicitly named).
- 2026-05-26 (round-1 review revision) — Eight Blockers + eight Concerns + four Nits from pre-EXECUTE adversarial review addressed. **Parallelism paragraph rewritten** to match the actual `Depends on:` graph: only T9 + T10 can run in parallel after T1; T3 + T5 in parallel after T2; T4 / T6 / T7 are sequential subsequents to T3 / T5; T8 depends on T4 + T6; T11 → T12 → T13 → T14 sequential per the `make build-self` race rationale. **T5 Tier-2 helper decision** pinned: broker carries its own sibling `_sso_keychain_macos.py` / `_sso_credman_windows.py` rather than reaching across to T3's shim siblings; this removes the hidden cycle and restores T3 / T5 parallelism after T2. **T12 / T13 / T14 declared sequential** (`Depends on:` updated). **T14 separation-gate test** added per AC34. **T8 lint-of-self** extended to cover all four broker-specific AST checks. **Rollout reversibility** clarified — Phase 1 forward-only once `credential-brokers` ships. **T9 template-variant divergence** from RFC § 5 acknowledged (four files vs. one file with labelled sections); divergence rationale recorded.
- 2026-05-26 — Initial Draft. 15 tasks across three phases. T1 gates everything; subsequent dependency graph is layered. Maps to 48 ACs in `spec.md`.
