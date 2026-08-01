# Expected behavior: hook-confirm gate

Documents the expected flow for AC7. The live QA session ingests
`fixtures/hook-confirm/sample-hook.sh` and verifies the confirm gate fires.

Source authority: `packs/catalogue-curation/.apm/skills/assimilate-primitive/SKILL.md`
Phase 1, step 3: "Confirm on code."

---

## Detection trigger

The assimilation skill must detect `sample-hook.sh` as executable code
during Phase 1, before any shaping work begins. Detection fires when:

1. The file has a `#!/usr/bin/env bash` shebang line (or any shebang).
2. OR the filename extension is `.sh`, `.py`, `.rb`, or any recognized
   executable extension.
3. OR the primitive is delivered under a `hooks/` directory in the source.

`sample-hook.sh` satisfies criteria 1 (shebang) and 2 (`.sh` extension).
Either alone is sufficient.

The detection must fire **before** the raw body is shown for review.
The flow is:

1. Fetch the file.
2. Detect: shebang present → flag as executable code.
3. Show the raw body (Phase 1 step 2 — raw body review always happens).
4. Issue the confirm prompt **after** showing the raw body.
5. Wait for explicit "yes" before proceeding to Phase 2.

---

## Expected confirm prompt

After showing the raw body of `sample-hook.sh`, the skill must surface:

> ⚠ **This primitive is executable code** — a bash script that will run
> automatically on your machine as a git hook on every commit attempt.
> It executes: `python scripts/pre-commit-checks.py`
>
> Please review the script above before proceeding.
>
> **Do you want to land this hook? (yes / no)**

Requirements the prompt must satisfy:
- Identifies the file as **executable code** (not just "a file").
- Names what it executes.
- Asks for an explicit `yes` or `no` — not a press-enter or implicit default.
- Does not proceed on ambiguous answers.
- Appears **after** the raw body is shown (raw body review is always first).

---

## Post-confirm landing path

**On "yes":** Phase 2 proceeds normally.

1. The skill diagnoses the destination pack (which pack should own this hook?
   Most likely `core` if it is a general-purpose quality gate, or the source
   pack if it is specific to a particular workflow).
2. Anti-pattern check: `anti-patterns.md:38-42` flags hooks doing heavy logic
   that belongs in a script. `sample-hook.sh` is a thin wrapper
   (`python scripts/pre-commit-checks.py`) — it clears this check.
3. The skill may recommend renaming the hook to match git's naming convention
   (`pre-commit` with no extension, placed under `.git/hooks/`).

**Important — git hooks vs. agent hooks (two distinct landing paths):**

`sample-hook.sh` is a **git pre-commit hook**, not an agent/editor hook. These
are different primitive types with different landing destinations:

- **Agent/editor hooks** (e.g., a hook that fires on `PreToolUse`) land as:
  - Hook body → `.apm/hooks/<name>.py` or `.apm/hooks/<name>.sh`
  - Hook wiring → `.apm/hook-wiring/<name>.toml` (binds body to the editor event)
  - Projected to each adapter via `make build-self`.
  - The `.apm/hook-wiring/` primitive is the mechanism for *editor* events
    (Claude Code, Kiro, etc.) — it does not exist for git events.

- **Git hooks** (pre-commit, post-merge, etc.) are NOT landed via hook-wiring.
  Git's event system is separate from the adapter event system. A git hook lands
  by being copied or symlinked into `.git/hooks/`. The correct landing path for
  `sample-hook.sh` is:
  - Write the hook body to a deterministic path within the pack source
    (e.g., `packs/core/.apm/hooks/git/pre-commit.sh`).
  - Document manual installation: "copy or symlink to `.git/hooks/pre-commit`".
  - Do NOT write a `.apm/hook-wiring/<name>.toml` for git events — no such
    adapter-contract binding exists for git pre-commit.

4. Write the hook body via `agentbundle.safety.write_jailed`.
5. Add a documentation note instructing the user to install manually:
   ```
   cp packs/core/.apm/hooks/git/pre-commit.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```
6. Prompt `make build-self` to project the hook body to adapter layouts.

**On "no":** the ingest is aborted.

1. The fetched working copy is discarded.
2. No files are written.
3. The skill surfaces: "Hook ingest aborted — no files written."

---

## What the QA session should verify

1. The confirm prompt fires before any write — no file lands without confirm.
2. The prompt names what executes (`python scripts/pre-commit-checks.py`).
3. Answering "no" discards the primitive cleanly.
4. Answering "yes" proceeds to Phase 2 and lands the hook body via the jailed
   write path.
5. The skill does NOT create a `.apm/hook-wiring/` file for this git hook.
6. The raw body is shown verbatim before the confirm prompt.
