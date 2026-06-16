# Plan: credential-setup credbroker guard

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Two independent changes ride in one PR. The first is the substantive one: a
`try/except` wrapper around the existing top-level `from credbroker import (...)`
in `setup.py`. The except arm narrows to `ModuleNotFoundError` whose `.name` is
exactly `credbroker`, writes one ASCII guidance line to stderr, and raises
`SystemExit(3)`; any other import failure re-raises unchanged. The success path
is byte-for-byte the same import, so the rest of the module is untouched. The
second is mechanical prose-drift cleanup in the pack's self-description
(`pack.toml`, the plugin manifest, the `README`), a version bump, a regen of the
repo-root `.claude-plugin/marketplace.json` via `make build-self` (the all-packs
aggregation is written by `self_host.py::_aggregate_marketplace`, reached only
by `build-self`; `make build` writes only `dist/`), the `SKILL.md` exit-code
line, and a changelog entry.

The riskiest part is the guard *test*: `credbroker` is installed in the test
interpreter, so the only honest way to exercise the missing-`credbroker` arm is
a subprocess of the real documented invocation with an environment where
`credbroker` resolves through none of its three discovery paths. That test is
designed first (T1).

## Constraints

- **RFC-0023** — `credbroker` is the in-process `auth: creds` resolver that
  replaced the build-projected `credentials_shim`; the prose-drift fix aligns
  the pack's self-description with this. `credentials_shim.py` is retained as
  the `sso-broker` companion loader (credbroker spec AC22b) and is not touched.
- **SKILL.md exit-code contract** (`0` / `2` / `3`) — the guard reuses the
  documented `3` ("interactive precondition unmet"); no new code, no contract
  change.
- **docs/rfc/0013** is a frozen record and is left as-is even though it names
  `credentials_shim` — it describes the contract as it was.

## Construction tests

Per-task tests live under the tasks below.

**Integration tests:** none beyond the T1 subprocess end-to-end test.
**Manual verification:** run `python setup.py jira` from a shell with
`credbroker` uninstalled (or `python -S setup.py jira` with a temp `HOME`) and
confirm the one-line hint + exit 3 by eye.

## Design (LLD)

### Design decisions

- **Narrow the except to `exc.name == "credbroker"`, re-raise otherwise.** A
  blanket `except ModuleNotFoundError` would report "credbroker not found" for
  a broken credbroker submodule or an unrelated missing module — misdirection.
  Narrowing fails closed: only the unambiguous package-absent case is handled.
  Traces to: AC1, AC3 · contracts/ none.
- **Exit `3`, not a new code.** `3` already covers "interactive precondition
  unmet" in `SKILL.md`; a missing resolver is exactly that. Avoids a contract
  amendment. Traces to: AC1, AC8 · contracts/ none.
- **Message is a fixed ASCII literal, never `str(exc)`.** Echoing the exception
  could leak `sys.path` entries (home-dir/usernames). Traces to: AC1 ·
  contracts/ none.
- **Drop `credentials_shim` from the pack's user-facing "what's inside" and
  name `credbroker`.** `credentials_shim` is now internal plumbing for the SSO
  rail, not a thing an adopter consumes; describing it as the `auth: creds`
  module is the drift. Traces to: AC6 · contracts/ none.

### Failure, edge cases & resilience

- `from credbroker import X` with the package absent → `ModuleNotFoundError`,
  `.name == "credbroker"` → handled (hint + exit 3).
- credbroker present but a submodule missing (`credbroker._core`) →
  `.name == "credbroker._core"` → re-raised.
- credbroker present but a symbol missing (wrong version) → `ImportError`, not
  `ModuleNotFoundError` → not caught, re-raised. Out of scope (version
  mismatch is not "missing"); the `requirements.txt` floor (`credbroker>=0.1.0`)
  is the version contract.

## Tasks

### T1: Missing-credbroker guard fires with a clean hint and exit 3

**Depends on:** none

**Tests:** (in `packs/credential-brokers/.apm/skills/credential-setup/scripts/test_setup.py`)
- New `test_missing_credbroker_exits_3_with_install_hint`: spawn
  `[sys.executable, "-S", setup.__file__, "jira"]` with `env` = a minimal dict
  (temp `HOME`/`USERPROFILE` under `tmp_path`, `PATH`, `SYSTEMROOT`, **no**
  `PYTHONPATH`). First assert the floor dir `<HOME>/.agentbundle/lib` does
  **not** exist (so a future env regression that leaks a real floor fails loud
  rather than silently skipping the guard — security-review nit). Then assert
  `returncode == 3`, `"pip install -e ./packages/credbroker"` in stderr,
  `"Traceback" not in stderr`. Verifies AC1, AC3, AC4.
- New `test_non_credbroker_import_error_is_reraised`: a fake `credbroker`
  package whose `__init__` imports a *different* missing module is placed first
  on the child's import path (PYTHONPATH precedes site-packages) so it shadows
  the real one; assert the guard re-raises (exit != 3, the other module's name
  + a traceback on stderr, the credbroker hint absent). Guards the `exc.name`
  narrowing branch (AC3) — mutation-checked: removing the narrowing fails it.
- Existing seven cases still pass unchanged (AC2). The import-surface invariant
  test (`test_setup_imports_credbroker_not_shim_nor_private`) still sees the
  `from credbroker import (...)` node inside the `try` (AC2).

**Approach:**
- Wrap `setup.py:37-51`'s `from credbroker import (...)` in `try:`; add
  `except ModuleNotFoundError as exc:` that `raise`s if `exc.name != "credbroker"`,
  else `sys.stderr.write(<one ASCII line>)` and `raise SystemExit(3)`.
- Message (verbatim, ASCII — the user-approved phrasing with the em-dash
  rendered as a period for the no-bootstrap ASCII constraint):
  `credbroker not found. Install it from your repository checkout:\n\n    pip
  install -e ./packages/credbroker\n\n(run from the repo root), then re-run this
  script.\n`

**Done when:** the new subprocess test is green and all of `test_setup.py`
passes with `credbroker` installed.

### T2: Wire `test_setup.py` into CI

**Depends on:** T1

**Tests:**
- Goal-based: the new `build-check.yml` step runs `python -m pytest
  test_setup.py` from the skill `scripts/` dir and exits 0. Verifies AC5.

**Approach:**
- Add a named step to the credbroker build-check job (after the existing
  `pip install -e './packages/credbroker[crypto]'` at line 155) with
  `working-directory: packs/credential-brokers/.apm/skills/credential-setup/scripts`
  running `python -m pytest test_setup.py`.

**Done when:** the step exists, is placed after the credbroker[crypto] install,
and the suite passes locally under the same conditions.

### T3: Pack self-description names credbroker; version bumped; marketplace regen

**Depends on:** none

**Tests:**
- Goal-based: `grep` finds no "`build-projected Python module` … `auth: creds`"
  `credentials_shim` framing in `pack.toml`, `.claude-plugin/plugin.json`, or
  `README.md`; the exact post-edit description clause attributing the
  `auth: creds` **resolver role** to `credbroker` is present in each of the
  three files (pinned to the literal clause, not a bare `credbroker` grep — it
  already appears elsewhere). `make build-self` regenerates the repo-root
  `.claude-plugin/marketplace.json`; `git diff` shows only the
  credential-brokers description + version change there (and no projection of
  credential-brokers primitives into `.claude/`). Verifies AC6, AC7.

**Approach:**
- `pack.toml`: rewrite the `description =` key to name `credbroker` as the
  `auth: creds` resolver; bump `version` `0.1.2` → `0.1.3`.
- `.claude-plugin/plugin.json`: mirror the `description` + bump `version`.
- `README.md`: in "What's inside", replace the `credentials_shim` bullet with a
  `credbroker` bullet (pip-installable, in-process `auth: creds` resolver), and
  note in the `credbroker`/`sso-broker` bullet that `credentials_shim` survives
  as internal `sso-broker` plumbing — don't silently drop a still-shipped file.
- `make build-self` to regen the repo-root `marketplace.json`; verify the diff
  is scoped to credential-brokers' description + version and check `git status`
  for any unexpected projection reverts before/after.

**Done when:** the grep checks hold, versions read `0.1.3`, and the repo-root
`marketplace.json` reflects the new description with no unrelated drift.

### T4: SKILL.md exit-code line + changelog entry

**Depends on:** none

**Tests:**
- Goal-based: `SKILL.md` exit-`3` list mentions `credbroker` not installed;
  `docs/product/changelog.md` has an `[Unreleased]` entry with no package-index
  or fork detail. Verifies AC8, AC9.

**Approach:**
- `SKILL.md`: add "`credbroker` not installed" to the exit-`3` enumeration.
- `docs/product/changelog.md`: add an `[Unreleased] → Changed` bullet — the
  setup script now prints a clear install hint instead of a traceback when
  `credbroker` is not installed.
- In the implementing PR (this one), flip the spec `Status: Draft →
  Shipped`, check every Acceptance Criterion, and set the plan `Status: Done`
  (AC10; spec + code land atomically). Run `lint-spec-status.py` to confirm.

**Done when:** both files reflect the change, the changelog entry names no
package index, URL, or fork, and the spec metadata is closed out.

## Rollout

Pure code + docs change, no infra. Reversible by revert. `make build-self`
regenerates the repo-root `.claude-plugin/marketplace.json` deterministically;
no migration, no external system.

## Risks

- **Wiring `test_setup.py` into CI turns on the existing seven tests too.** If
  any had a latent environment assumption it would newly red-fail CI.
  Mitigation: confirmed green locally under the CI conditions
  (`pip install -e './packages/credbroker[crypto]'` then `pytest test_setup.py`)
  before wiring.
- **`make build-self` could touch more of the repo-root `marketplace.json`
  than the credential-brokers entry, or revert an unrelated projection.**
  Mitigation: review the `git diff` on `marketplace.json` is scoped to the
  description + version, and check `git status` for unexpected projection
  reverts; surface if not.

## Changelog

- 2026-06-16: initial plan.
- 2026-06-16: corrected marketplace regen to `make build-self` (the repo-root
  `marketplace.json` is build-self-only); pinned the drift grep to the exact
  description clause; added spec-status closeout (T4/AC10) + the README
  honesty note that `credentials_shim` survives as `sso-broker` plumbing.
