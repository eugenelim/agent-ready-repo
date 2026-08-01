# Expected behavior: hook-confirm gate

Documents the expected flow for AC7. The live QA session ingests
`fixtures/hook-confirm/sample-hook.sh` and verifies the confirm gate fires.

Source authority: `packs/catalogue-curation/.apm/skills/assimilate-primitive/SKILL.md`
Phase 1, step 3: "Confirm on code."

---

## Fixture bundle

The `fixtures/hook-confirm/` bundle contains two files ingested together:
- `sample-hook.sh` — the pre-commit hook (thin wrapper invoking the companion script).
- `scripts/pre-commit-checks.py` — the companion Python script. Both are executable
  code: the hook shells out to the script, so both must be reviewed before confirmation.

---

## Detection trigger and raw-body review flow

The assimilation skill must detect executable code in the bundle during Phase 1,
before confirmation. Detection fires when a file has a shebang, a `.sh` or `.py`
extension, or lives under a `hooks/` directory.

Both `sample-hook.sh` (shebang + `.sh`) and `scripts/pre-commit-checks.py`
(`.py` extension) satisfy the detection criteria.

**Phase 1 step 2 — show all raw bodies before confirmation:**

Both raw bodies must be shown to the operator before the confirmation prompt is
issued. The operator cannot consent to code they have not read. The flow is:

1. Fetch both files in the bundle.
2. Show the raw body of `sample-hook.sh` verbatim.
3. Show the raw body of `scripts/pre-commit-checks.py` verbatim.
4. Issue a single confirmation prompt covering the entire bundle.
5. Wait for explicit "yes" before proceeding.

---

## Expected confirm prompt

After showing both raw bodies, the skill must surface:

> ⚠ **This bundle contains executable code** — a bash pre-commit hook and a
> Python companion script. Both will run automatically on your machine as a
> git hook on every commit attempt.
>
> `sample-hook.sh` executes: `python scripts/pre-commit-checks.py`
> `scripts/pre-commit-checks.py`: stub that exits 0 (stub — replace with real checks).
>
> Please review both scripts above before proceeding.
>
> **Do you want to land this bundle? (yes / no)**

Requirements the prompt must satisfy:
- Identifies both files as **executable code**.
- Shows both raw bodies BEFORE the prompt.
- Asks for a single explicit `yes` or `no` covering the entire bundle.
- Does not proceed on ambiguous answers.

---

## Post-confirm landing path

**On "yes":** Confirmation is given, but it does not replace Phase 1's remaining
mandatory steps. The skill must complete Phase 1 steps 4–5 before shaping or writing.

### Phase 1 steps 4–5 (mandatory after confirmation; confirmation does not bypass them)

**Step 4 — Run the repo's own gates on the candidate:**

Run `agentbundle catalogue lint --deep` and `agentbundle catalogue verify`. These
commands validate frontmatter keys, skill layout, eval cross-references, and hook-body
reference resolution — they do NOT inspect shell script content or scan for blocked
commands. Shell content validation requires a SAST tool (e.g., shellcheck for bash,
bandit for Python) — note this in the QA session record if running a full security pass.
A gate failure **blocks landing** regardless of operator confirmation.

**Step 5 — Run the agentic-skills security review (AST01–AST10):**

For `sample-hook.sh` and `scripts/pre-commit-checks.py`, the relevant checks are:
- **AST06** — code execution: both files execute shell/Python code. Confirm the
  bundle is the claimed thin wrapper + stub; name the containment scope (execution is
  limited to the declared `scripts/pre-commit-checks.py` target, no writes or network).
- **AST10** — confirm security metadata (if any) survives to this catalogue's schema.

A blocker-level AST finding (AST01, AST05, or AST06 undeclared execution without
containment) **prevents landing**.

### Phase 2 — destination diagnosis and landing

Only after steps 4–5 pass does Phase 2 begin.

1. The skill diagnoses the destination pack (most likely `core` for a general-purpose
   quality gate, or the source pack for a workflow-specific hook).
2. Anti-pattern check: `anti-patterns.md:38-42` flags hooks doing heavy logic directly.
   `sample-hook.sh` is a thin wrapper — it clears this check.
3. The skill may recommend renaming to match git's convention (`pre-commit`, no extension).

**Important — git hooks vs. agent hooks (two distinct landing paths):**

`sample-hook.sh` is a **git pre-commit hook**, not an agent/editor hook.

- **Agent/editor hooks** (e.g., fires on `PreToolUse`) land as:
  - Hook body → `.apm/hooks/<name>.py` or `.apm/hooks/<name>.sh`
  - Hook wiring → `.apm/hook-wiring/<name>.toml` (binds body to editor event)
  - Projected via `make build-self`. Hook-wiring does NOT apply to git events.

- **Git hooks** land differently — NOT via hook-wiring. The correct landing path:
  - Write the hook body **flat** under `.apm/hooks/` (e.g.,
    `packs/core/.apm/hooks/pre-commit.sh`). **Do not create a subdirectory** such
    as `.apm/hooks/git/` — `build-self` iterates only immediate `.apm/hooks`
    children that are files (`self_host.py:721–724`); subdirectories are ignored.
  - Document manual installation: "copy or symlink both to your repo."
  - Do NOT write a `.apm/hook-wiring/<name>.toml` for git events.

**Important — companion script is not a projected primitive:**

`.apm/scripts/` is NOT a declared source path in `adapter.toml` and is not
projected by `build-self`. The companion script (`scripts/pre-commit-checks.py`)
cannot be distributed through the pack projection chain. Two options:

- **Option A (recommended):** Rewrite the hook to be self-contained — inline
  the actual check commands directly in the hook body rather than delegating
  to a companion script. This avoids the dependency on an unmanaged external file.
- **Option B:** Treat the companion script as a manually installed artifact that
  the operator copies to `scripts/` in their repo root. It is not managed by the
  pack; document this limitation clearly in the hook's README entry.

For this QA fixture, the skill should surface Option A as the preferred landing
shape and note that Option B is available if the operator prefers the thin-wrapper
pattern (with the caveat that the script must be placed manually).

4. Write the hook body via `agentbundle.safety.write_jailed`:
   - `packs/core/.apm/hooks/pre-commit.sh`
5. Add documentation for manual installation:
   ```
   # Hook body (flat under .apm/hooks/):
   cp packs/core/.apm/hooks/pre-commit.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit

   # If using Option B (thin-wrapper pattern), also place the companion:
   # cp scripts/pre-commit-checks.py <your-repo-root>/scripts/pre-commit-checks.py
   ```
6. Prompt `make build-self` to project the hook body to adapter layouts.

**On "no":** the ingest is aborted.

1. Both fetched files are discarded.
2. No files are written.
3. The skill surfaces: "Hook ingest aborted — no files written."

---

## What the QA session should verify

1. Both raw bodies are shown BEFORE the confirmation prompt — operator can read both.
2. A single confirmation prompt covers the entire bundle (not two separate prompts).
3. Answering "no" discards both primitives cleanly.
4. Answering "yes" triggers Phase 1 steps 4–5 (gates + AST review) before any
   write — confirmation does not skip these.
5. BOTH files (hook body and companion script) are written to jailed pack paths.
6. The hook body lands flat under `.apm/hooks/` (not in a subdirectory).
7. The skill does NOT create a `.apm/hook-wiring/` file for this git hook.
