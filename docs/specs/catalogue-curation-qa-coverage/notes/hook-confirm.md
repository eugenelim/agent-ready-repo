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
5. Wait for explicit "yes" before proceeding.

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

**On "yes":** Confirmation is given, but it does not skip Phase 1's remaining
mandatory steps. The skill must complete Phase 1 steps 4–5 before any shaping
or writing begins.

### Phase 1 steps 4–5 (mandatory after confirmation; confirmation does not bypass them)

**Step 4 — Run the repo's own gates on the candidate**
(`assimilate-primitive/SKILL.md` Phase 1, step 4):

Run `agentbundle catalogue lint --deep` and `agentbundle catalogue verify` on
the hook file. For a bash hook, lint checks at minimum that the file has a valid
shebang and is not invoking any blocked commands. A gate failure **blocks
landing** regardless of operator confirmation.

**Step 5 — Run the agentic-skills security review (AST01–AST10)**
(`assimilate-primitive/SKILL.md` Phase 1, step 5):

Evaluate the hook against the security checklist. For `sample-hook.sh` the
relevant checks are:
- **AST06** — code execution: the hook runs `python scripts/pre-commit-checks.py`.
  Confirm the companion script is in scope (see fixture bundle below) and the
  hook body is the claimed thin wrapper. The companion script
  `scripts/pre-commit-checks.py` is included in the ingest bundle alongside
  `sample-hook.sh` — the QA session should also ingest it and confirm it is a
  stub that exits 0.
- **AST10** — confirm any security metadata in the source survives the port to
  this catalogue's frontmatter schema.

A blocker-level AST finding (AST01 malicious content; AST05 external instruction
execution; AST06 undeclared code execution without containment) **prevents
landing**.

### Phase 2 — destination diagnosis and landing

Only after steps 4–5 pass does Phase 2 begin.

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
  Git's event system is separate from the adapter event system. The correct
  landing path for `sample-hook.sh` is:
  - Write the hook body **flat** under `.apm/hooks/` (e.g.,
    `packs/core/.apm/hooks/pre-commit.sh`). **Do not create a subdirectory**
    (e.g., `.apm/hooks/git/`) — `build-self` iterates only immediate `.apm/hooks`
    children that are files (`self_host.py:721–724`); subdirectories are silently
    ignored and the hook will not be projected.
  - Document manual installation: "copy or symlink to `.git/hooks/pre-commit`".
  - Do NOT write a `.apm/hook-wiring/<name>.toml` for git events — no such
    adapter-contract binding exists for git pre-commit.

4. Write the hook body via `agentbundle.safety.write_jailed`.
5. Add a documentation note instructing the user to install both files:
   ```
   # Hook body (from pack source, flat under .apm/hooks/):
   cp packs/core/.apm/hooks/pre-commit.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit

   # Companion script (must exist at repo root before activating the hook):
   # Place scripts/pre-commit-checks.py at the project root.
   ```
6. Prompt `make build-self` to project the hook body to adapter layouts.

**On "no":** the ingest is aborted.

1. The fetched working copy is discarded.
2. No files are written.
3. The skill surfaces: "Hook ingest aborted — no files written."

---

## Fixture bundle

The `fixtures/hook-confirm/` bundle contains two files that are ingested together:
- `sample-hook.sh` — the pre-commit hook (thin wrapper invoking the companion script).
- `scripts/pre-commit-checks.py` — the companion script the hook delegates to. This
  is a stub (exits 0 unconditionally) for QA purposes; in production it would contain
  real checks. During a live landing, this file must be placed at `scripts/` in the
  project root.

---

## What the QA session should verify

1. The confirm prompt fires before any write — no file lands without confirm.
2. The prompt names what executes (`python scripts/pre-commit-checks.py`).
3. Answering "no" discards the primitive cleanly.
4. Answering "yes" triggers Phase 1 steps 4–5 (gates + AST review) before any
   write — not just Phase 2. The security review must run even after confirmation.
5. The skill lands the hook body **flat** under `.apm/hooks/` (not in a `git/`
   subdirectory), so it remains visible to `build-self` projection.
6. The skill does NOT create a `.apm/hook-wiring/` file for this git hook.
7. The raw body is shown verbatim before the confirm prompt.
