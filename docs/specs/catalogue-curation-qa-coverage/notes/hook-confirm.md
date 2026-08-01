# Expected behavior: hook-confirm gate

Documents the expected flow for AC7. The live QA session invokes
`assimilate-primitive` with the full bundle directory
`fixtures/hook-confirm/` (not just `sample-hook.sh` alone) so that both
files in the bundle are discovered and presented for review and consent.

Source authority: `packs/catalogue-curation/.apm/skills/assimilate-primitive/SKILL.md`
Phase 1, step 3: "Confirm on code."

---

## Fixture bundle

The `fixtures/hook-confirm/` bundle contains two files ingested together:
- `sample-hook.sh` — the pre-commit hook (thin wrapper invoking the companion
  script at its projected path `.agentbundle/bin/pre-commit-checks.py`).
- `scripts/pre-commit-checks.py` — the companion Python script (source content;
  the assimilation skill lands it at `.apm/adapter-root-bins/`, which projects
  to `.agentbundle/bin/` via `build-self`). Both are executable code: the hook
  shells out to the script, so both must be reviewed before confirmation.

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
> `sample-hook.sh` executes: `python .agentbundle/bin/pre-commit-checks.py`
> `scripts/pre-commit-checks.py`: stub that exits 0 (replace with real checks).
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
  bundle is the claimed thin wrapper + stub; name the containment scope (execution
  is limited to the declared `.agentbundle/bin/pre-commit-checks.py` target).
- **AST10** — confirm security metadata (if any) survives to this catalogue's schema.

A blocker-level AST finding **prevents landing**.

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
    children that are files; subdirectories are ignored.
  - Write the companion script to `.apm/adapter-root-bins/pre-commit-checks.py`
    (RFC-0013 §4d — this path projects to `.agentbundle/bin/pre-commit-checks.py`
    in the adopter's repo root, which is the path the hook body calls).
  - Document manual installation for the hook only (the companion projects automatically).
  - Do NOT write a `.apm/hook-wiring/<name>.toml` for git events.

4. Write both files via `agentbundle.safety.write_jailed`:
   - `packs/core/.apm/hooks/pre-commit.sh` — the hook body (projected to `tools/hooks/`)
   - `packs/core/.apm/adapter-root-bins/pre-commit-checks.py` — the companion
     (projected to `.agentbundle/bin/pre-commit-checks.py` at repo scope)
5. Add documentation for manual installation of the hook body only:
   ```
   # Hook body (flat under .apm/hooks/, install manually):
   cp packs/core/.apm/hooks/pre-commit.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   # The companion script is projected by build-self to .agentbundle/bin/.
   ```
6. Run `make build-self` to project both primitives to adapter layouts.
7. **Version bump required** — landing a new hook primitive in `core` is a non-cosmetic
   change. Before committing, increment the minor version in both:
   - `packs/core/pack.toml` (`version = "X.Y.Z"` → `"X.(Y+1).0"`)
   - `packs/core/.claude-plugin/plugin.json` (`"version": "X.Y.Z"` → `"X.(Y+1).0"`)
   And add an `[Unreleased]` changelog entry to the core pack's changelog
   (see `packs/AGENTS.md:63-70` and `packs/AGENTS.local.md:12-18`).

**On "no":** the ingest is aborted.

1. Both fetched files are discarded.
2. No files are written.
3. The skill surfaces: "Hook ingest aborted — no files written."

---

## What the QA session should verify

1. The skill is invoked with the full bundle directory path, not just `sample-hook.sh`.
2. Both raw bodies are shown BEFORE the confirmation prompt.
3. A single confirmation prompt covers the entire bundle (not two separate prompts).
4. Answering "no" discards both primitives cleanly.
5. Answering "yes" triggers Phase 1 steps 4–5 (gates + AST review) before any
   write — confirmation does not skip these.
6. BOTH files are written: hook body to `.apm/hooks/` (flat), companion to
   `.apm/adapter-root-bins/`.
7. The skill does NOT create a `.apm/hook-wiring/` file for this git hook.
8. The skill surfaces the version-bump requirement before completing.
