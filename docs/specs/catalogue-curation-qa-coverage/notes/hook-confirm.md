# Expected behavior: hook-confirm gate

Documents the expected flow for AC7. The live QA session invokes
`assimilate-primitive` with the **two executable files explicitly**:
- `fixtures/hook-confirm/sample-hook.sh`
- `fixtures/hook-confirm/scripts/pre-commit-checks.py`

Pass both file paths to the skill, not the bundle directory — the directory
also contains `sample-hook-notes.md`, which is a prose answer-key document,
not an executable primitive, and would be included in an unfiltered directory
ingest.

Source authority: `packs/catalogue-curation/.apm/skills/assimilate-primitive/SKILL.md`
Phase 1, step 3: "Confirm on code."

---

## Fixture bundle

The `fixtures/hook-confirm/` bundle contains two executable files ingested together:
- `sample-hook.sh` — the pre-commit hook (thin wrapper invoking the companion
  at its projected path: `python .agentbundle/bin/pre-commit-checks.py`).
- `scripts/pre-commit-checks.py` — the companion Python script (source content;
  the assimilation skill lands it at `.apm/adapter-root-bins/`, which projects
  to `.agentbundle/bin/` via `FORCE=1 make build-self`). Both are executable
  code: the hook shells out to the script, so both must be reviewed before
  confirmation.

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

1. Fetch both files.
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
- Names what executes: `python .agentbundle/bin/pre-commit-checks.py`.
- Shows both raw bodies BEFORE the prompt.
- Asks for a single explicit `yes` or `no` covering the entire bundle.
- Does not proceed on ambiguous answers.

---

## Post-confirm landing path

**On "yes":** Confirmation is given, but it does not replace Phase 1's remaining
mandatory steps. The skill must complete Phase 1 steps 4–5 before shaping or writing.

### Phase 1 steps 4–5 (mandatory after confirmation; confirmation does not bypass them)

**Step 4 — Run the candidate's applicable gates:**

`agentbundle catalogue lint --deep` and `agentbundle catalogue verify` operate
against the destination catalogue root (`packs/`) — they do NOT inspect the
candidate files directly. For hook and script candidates, the applicable pre-landing
checks are file-level linters run against the explicit candidate paths:
- `shellcheck fixtures/hook-confirm/sample-hook.sh` (bash script linting)
- `bandit fixtures/hook-confirm/scripts/pre-commit-checks.py` (Python SAST)
- Or equivalent SAST tools available in the repo's tool chain

A finding from these tools (e.g., shellcheck error, bandit HIGH severity) blocks
landing pending explicit operator acknowledgment.

**Step 5 — Run the agentic-skills security review (AST01–AST10):**

For `sample-hook.sh` and `scripts/pre-commit-checks.py`:
- **AST06** — code execution: the hook executes Python with the operator's host
  authority and full filesystem access. Naming the companion script path
  (`.agentbundle/bin/pre-commit-checks.py`) is NOT sufficient containment —
  AST06 requires a sandbox, temp-directory scope, or explicit egress boundary.
  The skill should surface this as a concern: "These scripts run with host
  authority. No sandbox is declared. Verify the companion is trustworthy; operator
  must acknowledge before proceeding." If the operator cannot name a containment
  scope, AST06 remains a concern (not cleared) in the session record.
- **AST10** — confirm security metadata (if any) survives to this catalogue's schema.

Note: the CONFIRM gate (step 3) fires BEFORE AST06 (step 5). The QA session
successfully exercises the confirm gate regardless of AST06 outcome. The session
record should capture both: confirm fired ✓, AST06 concern surfaced (acknowledged
by operator / blocked by operator choice).

### Phase 2 — destination diagnosis and landing

Only after steps 4–5 complete (or concerns are acknowledged) does Phase 2 begin.

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
  - Projected via `FORCE=1 make build-self`. Hook-wiring does NOT apply to git events.

- **Git hooks** land differently — NOT via hook-wiring. The correct landing path:
  - Write the hook body **flat** under `.apm/hooks/` (e.g.,
    `packs/core/.apm/hooks/pre-commit.sh`). **Do not create a subdirectory** such
    as `.apm/hooks/git/` — `build-self` iterates only immediate `.apm/hooks`
    children that are files; subdirectories are ignored.
  - Write the companion script to `.apm/adapter-root-bins/pre-commit-checks.py`
    (RFC-0013 §4d — this projects to `.agentbundle/bin/pre-commit-checks.py`
    in the adopter's repo root, which is the path the hook body calls).
  - Document manual installation for the hook only (the companion projects via build-self).
  - Do NOT write a `.apm/hook-wiring/<name>.toml` for git events.

4. Write both files via `agentbundle.safety.write_jailed`:
   - `packs/core/.apm/hooks/pre-commit.sh` — the hook body (projected to `tools/hooks/`)
   - `packs/core/.apm/adapter-root-bins/pre-commit-checks.py` — the companion
     (projected to `.agentbundle/bin/pre-commit-checks.py` at repo scope)
5. Bump version **before** running `build-self` — both files in the working tree make
   it dirty and `build-self` requires `FORCE=1` on dirty trees:
   - Increment minor version in `packs/core/pack.toml`
   - Set the same version in `packs/core/.claude-plugin/plugin.json`
   - Both must match before `build-self` will accept the change.
6. Run `FORCE=1 make build-self` to project both new primitives and re-aggregate
   `marketplace.json`. Plain `make build-self` refuses on dirty trees.
7. Add a `## [core][version] — YYYY-MM-DD` changelog section in
   `docs/product/changelog.md` (the canonical post-bump record per
   `packs/AGENTS.local.md:16-19`).
8. Add documentation for manual installation of the hook body:
   ```
   # Hook body (flat under .apm/hooks/, install manually after build-self):
   cp packs/core/.apm/hooks/pre-commit.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   # The companion is projected by build-self to .agentbundle/bin/.
   ```

**On "no":** the ingest is aborted.

1. Both fetched files are discarded.
2. No files are written.
3. The skill surfaces: "Hook ingest aborted — no files written."

---

## What the QA session should verify

1. The skill is invoked with the two explicit file paths (not the directory).
2. Both raw bodies are shown BEFORE the confirmation prompt.
3. The confirm prompt names `.agentbundle/bin/pre-commit-checks.py` (not `scripts/`).
4. A single confirmation prompt covers the entire bundle (not two separate prompts).
5. Answering "no" discards both primitives cleanly.
6. Answering "yes" triggers Phase 1 steps 4–5 before any write.
7. At step 5, AST06 concern is surfaced (host-authority execution, no sandbox declared).
8. BOTH files are written: hook body to `.apm/hooks/` (flat), companion to
   `.apm/adapter-root-bins/`.
9. The skill does NOT create a `.apm/hook-wiring/` file for this git hook.
10. The version bump happens BEFORE `FORCE=1 make build-self`.
11. `docs/product/changelog.md` receives the new `## [core][version]` entry.
