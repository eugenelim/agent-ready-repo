# Expected behavior: hook-confirm gate

Documents the expected flow for AC7. The live QA session invokes
`assimilate-primitive` with `fixtures/hook-confirm/sample-hook.sh` only —
the single fixture file named in AC7 and AC2.

Source authority: `packs/catalogue-curation/.apm/skills/assimilate-primitive/SKILL.md`
Phase 1, step 3: "Confirm on code."

---

## Fixture file

`sample-hook.sh` is a thin-wrapper git pre-commit hook — the only file ingested
in the AC7 QA session. It delegates to `tools/pre-commit-checks.py`, a
project-local script the adopter owns (not a shipped companion from the pack).
Pass only this file to the skill.

---

## Detection trigger and raw-body review flow

The assimilation skill must detect executable code during Phase 1, before
confirmation. Detection fires when a file has a shebang (`#!/usr/bin/env bash`) or a `.sh`
extension. `sample-hook.sh` satisfies both criteria. (The directory-based trigger
— files under a `hooks/` directory — is not exercised here; the fixture lives
under `fixtures/hook-confirm/`, not a `hooks/` directory.)

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
> It invokes `python3 tools/pre-commit-checks.py`.
>
> Raw content is shown above. Please review it before proceeding.
>
> Type **`yes, land this code`** to proceed, or **`no`** to abort.

Requirements the prompt must satisfy:
- Identifies the file as executable code (not prose).
- Names what it invokes: `python3 tools/pre-commit-checks.py`.
- Shows the raw body BEFORE the prompt.
- Requires the exact contracted phrase `yes, land this code`
  (per `assimilate-primitive/SKILL.md:35-37`).
- Does not proceed on `yes` alone or any other ambiguous answer.

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

AST09 (governance/registry) does **not** apply to a raw hook-body — `marketplace.json`
registers packs, not individual hook files. The relevant check is that `build-self`
correctly projects the hook file to the adapter's hook path (verified after the write
step by running `FORCE=1 make build-self` and confirming the file appears under
`tools/hooks/` or the equivalent adapter path).

### Phase 2 — destination diagnosis and landing

Only after steps 4–5 complete does Phase 2 begin.

1. The skill diagnoses the destination pack (most likely `core` for a
   general-purpose quality gate, or the source pack for a workflow-specific hook).
2. Anti-pattern check: `anti-patterns.md:38-42` flags hooks doing heavy logic
   directly. `sample-hook.sh` delegates to `tools/pre-commit-checks.py` — a
   thin wrapper. It clears this check.
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
  - Do NOT write a `.apm/hook-wiring/<name>.toml` for git events.

4. **Present the shaped target for approval before writing** (per
   `assimilate-primitive/SKILL.md:104-107`). The skill must show the operator:
   - Destination path: `packs/core/.apm/hooks/pre-commit.sh`
   - Projected path (Claude Code / self-host): `tools/hooks/pre-commit.sh`
   - Any rename recommendation (e.g., drop `.sh` extension to match git convention)

   Wait for explicit operator approval before any write. A correct QA trace
   must include this approval step between Phase 2 diagnosis and the write.

5. Write the hook body via `agentbundle.safety.write_jailed`:
   - `packs/core/.apm/hooks/pre-commit.sh` — projected to `tools/hooks/` by
     `build-self` (Claude Code / self-host adapter).
6. Bump version **before** running `build-self` — the write makes the tree dirty
   and `build-self` requires `FORCE=1`:
   - Increment minor version in `packs/core/pack.toml`
   - Set the same version in `packs/core/.claude-plugin/plugin.json`
   - Both must match before `build-self` will accept the change.
7. Run `FORCE=1 make build-self` to project the new primitive and re-aggregate
   `marketplace.json`. Plain `make build-self` refuses on dirty trees.
8. Add a `## [core][version] — YYYY-MM-DD` changelog section in
   `docs/product/changelog.md` (the canonical post-bump record per
   `packs/AGENTS.local.md:16-19`).
9. Add documentation for manual installation. After `build-self`, the hook is
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

1. The skill is invoked with the single explicit file path `sample-hook.sh`.
2. The raw body is shown BEFORE the confirmation prompt.
3. The confirm prompt identifies the file as executable code and names the invocation (`python3 .agentbundle/bin/pre-commit-checks.py`).
4. The prompt requires the exact phrase `yes, land this code` — not just `yes`.
5. Answering anything other than `yes, land this code` aborts the ingest.
6. Answering `yes, land this code` triggers Phase 1 steps 4–5 before any write.
7. At step 4, shellcheck runs against the candidate file.
8. At step 5, the skill correctly notes AST01–AST10 apply to SKILL.md behaviour
   definitions, not raw scripts; AST09 does NOT apply to a raw hook body.
9. Before writing, the skill presents the shaped target (destination path,
   projected path, rename recommendation) and waits for operator approval.
10. The hook body is written flat under `.apm/hooks/` (no subdirectory).
11. The skill does NOT create a `.apm/hook-wiring/` file for this git hook.
12. The version bump happens BEFORE `FORCE=1 make build-self`.
13. `docs/product/changelog.md` receives the new `## [core][version]` entry.
14. The manual install command uses the adapter-specific projected path (not
    `packs/core/.apm/hooks/`).
