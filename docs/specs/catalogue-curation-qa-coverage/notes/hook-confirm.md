# Expected behavior: hook-confirm gate

Documents the expected flow for AC7. The live QA session invokes
`assimilate-primitive` with `fixtures/hook-confirm/sample-hook.sh` only —
the single fixture file named in AC7 and AC2.

Source authority: `packs/catalogue-curation/.apm/skills/assimilate-primitive/SKILL.md`
Phase 1, step 3: "Confirm on code."

---

## Fixture bundle

The `fixtures/hook-confirm/` directory contains:
- `sample-hook.sh` — the pre-commit hook (thin wrapper calling the companion at
  `python .agentbundle/bin/pre-commit-checks.py`). **This is the file ingested.**
- `scripts/pre-commit-checks.py` — companion stub (QA support material, not
  ingested as a separate primitive in this session).
- `sample-hook-notes.md` — this file (answer-key prose, not a primitive).

Pass only `fixtures/hook-confirm/sample-hook.sh` to the skill — the file named
in AC7. The companion and notes are fixture support material, not ingest targets.

---

## Detection trigger and raw-body review flow

The assimilation skill must detect executable code during Phase 1, before
confirmation. Detection fires when a file has a shebang (`#!/usr/bin/env bash`),
a `.sh` extension, or lives under a `hooks/` directory.

`sample-hook.sh` satisfies all three criteria.

**Phase 1 step 2 — show raw body before confirmation:**

The skill shows the raw body of `sample-hook.sh` verbatim before issuing the
confirmation prompt. The operator cannot consent to code they have not read.

1. Fetch `sample-hook.sh`.
2. Show the raw body verbatim.
3. Issue the confirmation prompt.
4. Wait for explicit "yes" before proceeding.

---

## Expected confirm prompt

After showing the raw body, the skill must surface:

> ⚠ **This primitive is a bash script** — executable code that will run
> automatically on your machine as a git pre-commit hook on every commit attempt.
> It invokes `python .agentbundle/bin/pre-commit-checks.py`.
>
> Raw content is shown above. Please review it before proceeding.
>
> **Do you want to land this hook? (yes / no)**

Requirements the prompt must satisfy:
- Identifies the file as executable code (not prose).
- Names what it executes: `python .agentbundle/bin/pre-commit-checks.py`.
- Shows the raw body BEFORE the prompt.
- Asks for an explicit `yes` or `no`.
- Does not proceed on ambiguous answers.

---

## Post-confirm landing path

**On "yes":** Confirmation clears step 3. The skill must still complete Phase 1
steps 4–5 before shaping or writing.

### Phase 1 steps 4–5 (mandatory after confirmation)

**Step 4 — Run the candidate's applicable gates:**

`agentbundle catalogue lint --deep` and `agentbundle catalogue verify` operate
against the destination catalogue root (`packs/`) — they do NOT inspect the
candidate file directly. For a bash script candidate, the applicable pre-landing
check is file-level linting against the explicit candidate path:
- `shellcheck fixtures/hook-confirm/sample-hook.sh` (bash script linting)

A finding from shellcheck blocks landing pending explicit operator acknowledgment.

**Step 5 — Agentic-skills security review (AST01–AST10):**

Per the source contract (`assimilate-primitive/SKILL.md:45-48`), the AST review
applies to **SKILL.md and equivalent behaviour-definition files** — not to raw
scripts. `sample-hook.sh` is a hook-body primitive (raw bash), not a behaviour
definition. The confirm gate (step 3) and shellcheck (step 4) are the applicable
Phase 1 security checks for raw scripts.

AST09 (governance/registry) still applies: the hook must be registered in
`marketplace.json` via `build-self` before use. The skill should verify that
landing the hook body will result in it being projected and tracked.

### Phase 2 — destination diagnosis and landing

Only after steps 4–5 complete does Phase 2 begin.

1. The skill diagnoses the destination pack (most likely `core` for a
   general-purpose quality gate, or the source pack for a workflow-specific hook).
2. Anti-pattern check: `anti-patterns.md:38-42` flags hooks doing heavy logic
   directly. `sample-hook.sh` is a thin wrapper — it clears this check.
3. The skill may recommend renaming to match git's convention (`pre-commit`, no
   extension).

**Important — git hooks vs. agent hooks (two distinct landing paths):**

`sample-hook.sh` is a **git pre-commit hook**, not an agent/editor hook.

- **Agent/editor hooks** (e.g., fires on `PreToolUse`) land as:
  - Hook body → `.apm/hooks/<name>.py` or `.apm/hooks/<name>.sh`
  - Hook wiring → `.apm/hook-wiring/<name>.toml` (binds body to editor event)
  - Projected via `FORCE=1 make build-self`. Hook-wiring does NOT apply to git events.

- **Git hooks** land differently — NOT via hook-wiring. The correct landing path:
  - Write the hook body **flat** under `.apm/hooks/` (e.g.,
    `packs/core/.apm/hooks/pre-commit.sh`). **Do not create a subdirectory** such
    as `.apm/hooks/git/` — `build-self` iterates only immediate `.apm/hooks`
    children that are files; subdirectories are ignored.
  - Document manual installation (see step 5 below). The companion
    (`pre-commit-checks.py`) would land via `.apm/adapter-root-bins/` if ingested
    separately (RFC-0013 §4d); it is NOT part of this QA session.
  - Do NOT write a `.apm/hook-wiring/<name>.toml` for git events.

4. Write the hook body via `agentbundle.safety.write_jailed`:
   - `packs/core/.apm/hooks/pre-commit.sh` — projected to `tools/hooks/` by
     `build-self` (Claude Code / self-host adapter).
5. Bump version **before** running `build-self` — the write makes the tree dirty
   and `build-self` requires `FORCE=1`:
   - Increment minor version in `packs/core/pack.toml`
   - Set the same version in `packs/core/.claude-plugin/plugin.json`
   - Both must match before `build-self` will accept the change.
6. Run `FORCE=1 make build-self` to project the new primitive and re-aggregate
   `marketplace.json`. Plain `make build-self` refuses on dirty trees.
7. Add a `## [core][version] — YYYY-MM-DD` changelog section in
   `docs/product/changelog.md` (the canonical post-bump record per
   `packs/AGENTS.local.md:16-19`).
8. Add documentation for manual installation. After `build-self`, the hook is
   projected to an adapter-specific path — adopters receive the projected file,
   NOT the catalogue authoring tree under `packs/core/.apm/`. The projected path
   depends on the installed adapter:
   ```
   # Claude Code / self-host adapter (projects to tools/hooks/):
   cp tools/hooks/pre-commit.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit

   # Copilot adapter (projects to .github/hooks/):
   cp .github/hooks/pre-commit.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit

   # Cursor adapter (projects to .cursor/hooks/):
   cp .cursor/hooks/pre-commit.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```
   Use the path matching the adopter's installed adapter.

**On "no":** the ingest is aborted.

1. The fetched file is discarded.
2. No files are written.
3. The skill surfaces: "Hook ingest aborted — no files written."

---

## What the QA session should verify

1. The skill is invoked with the single explicit file path `sample-hook.sh`
   (not the bundle directory; not the companion).
2. The raw body is shown BEFORE the confirmation prompt.
3. The confirm prompt identifies the file as executable code and names
   `python .agentbundle/bin/pre-commit-checks.py`.
4. Answering "no" discards the file cleanly.
5. Answering "yes" triggers Phase 1 steps 4–5 before any write.
6. At step 4, shellcheck runs against the candidate file.
7. At step 5, the skill notes that AST01–AST10 apply to SKILL.md behaviour
   definitions, not raw scripts; AST09 (registry/marketplace) is the relevant
   check for the hook primitive.
8. The hook body is written flat under `.apm/hooks/` (no subdirectory).
9. The skill does NOT create a `.apm/hook-wiring/` file for this git hook.
10. The version bump happens BEFORE `FORCE=1 make build-self`.
11. `docs/product/changelog.md` receives the new `## [core][version]` entry.
12. The manual install command uses the adapter-specific projected path (not
    `packs/core/.apm/hooks/`).
