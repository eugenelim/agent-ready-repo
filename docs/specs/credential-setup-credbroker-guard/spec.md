# Spec: credential-setup credbroker guard

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0023
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A user who runs `credential-setup`'s `scripts/setup.py` without `credbroker`
importable gets a single clear message telling them how to install it, then a
clean non-zero exit — not a Python traceback. The line names the editable
install from the repository checkout and nothing else, so it reads identically
in this repository and in any downstream fork. The pack's own description of
itself (`pack.toml`, the Claude plugin manifest, and the `README`) names
`credbroker` as the `auth: creds` resolver, matching how the code actually
resolves credentials, so a reader is never told `credentials_shim` is the
mechanism it no longer is.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Print the missing-`credbroker` guidance to **stderr** in **ASCII only**
  (the file has no UTF-8 stdout/stderr bootstrap), and exit with the
  already-documented code `3`.
- Keep the `from credbroker import (...)` statement intact on the success
  path — wrap it, don't replace it — so the imported names stay bound for
  the rest of the module.
- Confine the guidance message to the editable-from-checkout install form.

### Ask first

- Adding any install path beyond the editable-from-checkout form to the
  guard message (a package-index name, a URL, an environment-specific hint).
- Changing the documented exit-code contract in `SKILL.md` (codes `0` / `2`
  / `3`) — adding a new code or repurposing an existing one.
- Editing `credentials_shim.py` itself, or any `sso-broker` companion-shim
  wiring, while fixing the prose drift.

### Never do

- **Do not add a new module, package, or dependency** to make the guard
  work — it is a `try/except` around an import that already exists.
- Do not echo the caught exception text, `sys.path`, or any environment
  detail into the message (it can carry home-directory paths / usernames).
- Do not name a package index, a published-package install command, a URL,
  or any downstream-fork or environment detail anywhere in the code, tests,
  docs, or changelog this change touches.
- Do not treat *every* `ModuleNotFoundError` as "credbroker missing" — a
  failure whose missing-module name is not exactly `credbroker` is a
  different fault and must surface unchanged.
- Do not delete `credentials_shim.py` or rewrite the frozen `docs/rfc/0013`
  record while fixing the prose drift.

## Testing Strategy

- **Guard behavior: TDD, exercised by an end-to-end subprocess test.** The
  guard only fires when `credbroker` is genuinely unresolvable, which an
  in-process import cannot simulate (the test interpreter has `credbroker`
  installed). The test spawns the real documented invocation
  (`python -S setup.py <namespace>`) with a temp `HOME` and a cleared
  environment so `credbroker` resolves through none of its three paths
  (site-packages skipped by `-S`, `~/.agentbundle/lib` floor absent under the
  temp `HOME`, `PYTHONPATH` cleared), and asserts on the observed result:
  exit code `3`, the guidance line on stderr, and no `Traceback`. This is the
  user-invokes-an-artifact case, so the real built artifact is exercised the
  way a user would hit it.
- **Prose-drift fix: goal-based check.** A `grep` confirms the stale
  "`credentials_shim` … `auth: creds`" framing is gone from `pack.toml`,
  the plugin manifest, and the `README`, and that each now attributes the
  `auth: creds` **resolver role** to `credbroker` (pinned to the exact
  post-edit description clause, not a bare `credbroker`-present grep, since
  `credbroker` already appears elsewhere in the pack); `make build-self`
  regenerates the repo-root `.claude-plugin/marketplace.json` (the all-packs
  aggregation — it advertises every pack without projecting credential-brokers
  primitives into `.claude/`) and the lint / validate gates confirm the pack
  still resolves.
- **CI wiring: goal-based check.** The skill suite runs green under the
  newly-added CI step (and locally via `python -m pytest test_setup.py`
  with `credbroker` installed).

## Acceptance Criteria

- [x] Running `python setup.py <namespace>` with `credbroker` unresolvable
  prints a clear ASCII stderr message naming the editable install
  (`pip install -e ./packages/credbroker`, run from the repo root) and exits
  `3`, with no Python traceback on stderr.
- [x] On the normal path (`credbroker` importable) `setup.py` behaves exactly
  as before — the imported names are bound and the existing seven
  `test_setup.py` cases still pass.
- [x] A `ModuleNotFoundError` whose `.name` is not exactly `credbroker`
  (e.g. a broken credbroker submodule) is re-raised unchanged, not reported
  as "credbroker not found".
- [x] A subprocess regression test in `test_setup.py` asserts the exit code
  `3`, the presence of the install guidance on stderr, and the absence of
  `Traceback`.
- [x] `test_setup.py` runs in CI via an explicit step in the credbroker
  build-check job, and that step is green.
- [x] `pack.toml`, `.claude-plugin/plugin.json`, and `README.md` attribute the
  `auth: creds` resolver role to `credbroker` (not `credentials_shim`), with
  the `README`'s "What's inside" noting `credentials_shim` survives as internal
  `sso-broker` plumbing (not silently deleted), and the repo-root
  `.claude-plugin/marketplace.json` is regenerated to match via `make build-self`.
- [x] The `credential-brokers` pack version is bumped `0.1.2` → `0.1.3` in
  both `pack.toml` and `.claude-plugin/plugin.json`.
- [x] `SKILL.md`'s exit-code list records that `credbroker` not being
  installed exits `3`.
- [x] `docs/product/changelog.md` carries an `[Unreleased]` entry describing
  the new behavior in neutral terms (no package-index or fork detail).
- [x] This spec's `Status` is flipped from `Draft` and its Acceptance Criteria
  are checked in the same (implementing) PR, per CONVENTIONS § 4.

## Assumptions

- Technical: `setup.py` imports `credbroker` eagerly at module top (line 37),
  unlike the five lazy-importing API CLIs, so the guard fires at import time
  with no import hoist needed (source: `setup.py:22-51`).
- Technical: `setup.py` has no UTF-8 stdout/stderr reconfigure block, so the
  message must be ASCII (source: grep — no `reconfigure`/`PYTHONIOENCODING`
  in `setup.py`).
- Technical: `ModuleNotFoundError.name == "credbroker"` only when the
  top-level package is absent; a broken submodule yields a different name and
  a missing symbol is `ImportError`, so re-raising on `name != "credbroker"`
  cannot mask a present-but-broken install (source: Python import semantics).
- Technical: exit `3` is `SKILL.md`'s documented "any other interactive
  precondition unmet" bucket, so reusing it changes no contract (source:
  `SKILL.md:77-79`).
- Technical: `credbroker` is pip-installed in test/CI; the guard test must use
  a subprocess with `-S` + temp `HOME` + cleared env to make it unresolvable
  (source: `test_setup.py:22` + module docstring; local run — suite passes
  7/7 only after `pip install -e ./packages/credbroker[crypto]`).
- Process: `test_setup.py` gates nowhere in CI today; the credbroker
  build-check step runs `packages/credbroker`, not the skill's `scripts/`
  (source: `.github/workflows/build-check.yml:157-159`; user confirmation
  2026-06-16 to wire it).
- Process: `credentials_shim.py` is deliberately kept as the `sso-broker`
  companion loader and is no longer the `auth: creds` resolver; the drift is
  prose-only and `docs/rfc/0013` is a frozen record left untouched (source:
  `docs/specs/credbroker/spec.md` AC22b).
- Process: a non-cosmetic pack edit bumps the pack version, `make build-self`
  regenerates the repo-root `.claude-plugin/marketplace.json`, and a
  user-visible skill change earns a changelog `[Unreleased]` entry (source:
  `docs/CONVENTIONS.md`; repo memory on non-projected pack version drift).
