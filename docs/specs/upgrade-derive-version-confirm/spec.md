# Spec: upgrade — derive target version, confirm interactively

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An operator upgrading a pack with `agentbundle upgrade` does not name a target
version. The version is a property of the catalogue they point at, not a fact
they assert: the tool resolves the catalogue URI to a single snapshot whose
`pack.toml` declares its `[pack] version`, and that declared version *is* the
upgrade target. The tool keeps no historical-version store — version history
lives in the catalogue's git, reachable by pointing the URI at an older ref —
so there is nothing for the operator to select and no value resolver to run.

Before writing anything, the command shows the operator what they have and
what they would move to — `installed → target` — and asks for confirmation.
`--yes` skips the prompt for scripted use; a non-interactive stdin without
`--yes` refuses cleanly rather than blocking on a prompt nobody can answer.
The success recap names both versions, so the result of every upgrade records
where it came from, not just where it landed.

The same change keeps the documentation honest: the agentbundle PyPI README
shows the new `upgrade` usage, and the root README gains a Quick start that
shows the handful of install/upgrade commands a new user actually reaches for.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Derive the upgrade target from the resolved catalogue's `pack.toml`
  `[pack] version`; treat that single snapshot as the source of truth.
- Show `installed → target` in both the confirmation prompt and the success
  recap, for whole-pack and per-primitive upgrades alike.
- Confirm before the first write in an interactive session; treat only a
  case-insensitive `y`/`yes` as affirmative.

### Ask first

- Any change to the `upgraded:` recap line's shape beyond adding the
  `from` version — scripts may parse it.
- Re-introducing operator-supplied version selection or a version-history
  store — that is a deliberate scope expansion, not an upgrade detail.
- Touching the Tier-1/2/3 write contract, the path-jail, or the hook-wiring
  reconciliation — out of scope here.

### Never do

- Never write any file before the confirmation is satisfied in an interactive
  session.
- Never block on `input()` when stdin is not a TTY — refuse and explain.
- Never invent or accept a target version the resolved catalogue does not
  declare.
- Never add a new runtime dependency — the prompt uses stdlib `input()` and
  `sys.stdin.isatty()` only.

## Testing Strategy

- **CLI surface (`--to` removed, `--yes` added): goal-based / TDD.** Build the
  parser and assert `upgrade` rejects `--to`, accepts `--yes`, and no longer
  requires a version positional — verified by exercising `build_parser` in a
  unit test.
- **Version derivation + `from → to` recap: TDD.** Drive `upgrade.run()`
  against the fixture catalogues and assert `installed_version` becomes the
  catalogue's declared version and the recap names both versions.
- **Confirmation accept / decline / `--yes` / non-TTY refusal: TDD.**
  Monkeypatch `builtins.input` and `sys.stdin.isatty` and assert the
  write-or-refuse behavior and exit codes.
- **Missing `[pack] version`: TDD.** A constructed catalogue whose `pack.toml`
  omits the version errors non-zero with a clear message.
- **Real artifact end-to-end: manual QA.** Run the built `agentbundle upgrade`
  against a fixture catalogue once with `--yes` and once declining the prompt,
  and record the actual stdout and exit code.

## Acceptance Criteria

- [x] `agentbundle upgrade --pack <p> <catalogue>` with no version argument
  upgrades to the version declared in the resolved catalogue's `pack.toml`;
  `state.installed_version` equals that version.
- [x] The success recap names both versions:
  `upgraded: <pack> @ <scope> <from> -> <to>` (and the per-primitive form
  `upgraded: <pack> <ptype>/<name> @ <scope> <from> -> <to>`).
- [x] In an interactive session, the command prints a prompt naming
  `from <installed> to <target>` and, on any non-affirmative reply — including
  an `EOFError` at the prompt — writes nothing and exits non-zero with
  `upgrade: aborted; no changes made`.
- [x] A case-insensitive `y` or `yes` reply proceeds with the upgrade.
- [x] `--yes` skips the prompt and proceeds without reading stdin.
- [x] When stdin is not a TTY and `--yes` is absent, the command refuses with a
  message telling the operator to pass `--yes`, writes nothing, and exits
  non-zero — it does not block on `input()`.
- [x] The `--to` flag is removed from the `upgrade` parser; per-primitive
  upgrades (`--skill`, `--agent`, `--hook`, `--seed`, `--command`) derive the
  target version and show `from → to`, where `from` is the recorded
  primitive-version override if present, else `installed_version`. The per-file
  `from-pack-version` state metadata continues to record the *target* version;
  only the recap line gains the `from` version.
- [x] A resolved catalogue whose `pack.toml` declares no usable `[pack]
  version` — the `version` key missing, non-string, or the `[pack]` table
  absent — exits non-zero with the message
  `upgrade: pack '<pack>' in catalogue declares no [pack] version; cannot determine upgrade target`,
  via guarded access (`pack_toml.get("pack", {})` then a type-checked
  `version`), never an uncaught `KeyError`/`TypeError`. This check is distinct
  from the `[pack.adapter-contract]` spec-version gate, which does not read
  `[pack] version`. (A `[pack]` key bound to a non-table is malformed TOML the
  pre-existing spec-version gate rejects upstream; that path is out of scope
  here.)
- [x] `--dry-run` resolves the target version from the catalogue, previews the
  plan, prompts nothing, and writes nothing — and short-circuits the non-TTY
  refusal, since a dry run never writes (so a non-interactive `--dry-run` with
  no `--yes` still succeeds).
- [x] The agentbundle PyPI README (`packages/agentbundle/README.md`) documents
  the `upgrade` usage with no `--to`, the `--yes` flag, the confirmation, and
  the `from → to` recap.
- [x] The root `README.md` carries a Quick Start section showing the common
  install commands for `core` (repo scope) and a user-scope pack.
- [x] The five per-primitive flags (`--skill`, `--agent`, `--hook`, `--seed`,
  `--command`) form a mutually-exclusive argparse group, so passing two at once
  is rejected by the parser instead of silently upgrading only the first.
- [x] When the installed version already equals the derived target, the command
  states it (`<pack> is already at <version>`): interactively the prompt offers
  to re-apply (repair local drift); with `--yes` it states the notice and
  re-applies.

## Assumptions

- Technical: `--to` is currently `required=True` and the CLI is argparse-based
  with no existing interactive prompt (source: `agentbundle/cli.py:377`,
  investigation grep).
- Technical: the upgrade target is the resolved catalogue's `pack.toml`
  `[pack] version`; the `from` version is `pack_state.installed_version`
  (source: `agentbundle/commands/upgrade.py`, `tests/fixtures/upgrade/`).
- Technical: runtime is Python `>=3.11`; `input()` and `sys.stdin.isatty()` are
  stdlib, so the prompt adds no dependency (source: `pyproject.toml`).
- Process: a package CLI change is a normal PR (repo-owned, not CHARTER /
  CONVENTIONS) needing a `CHANGELOG.md` entry and a version bump at release
  (source: repo memory, `packages/agentbundle/CHANGELOG.md`).
- Product: the breaking removal of `--to`, the PyPI README update, and a
  root-README Quick Start are all in scope (source: user confirmation
  2026-06-23).
