# Expected behavior: hook-confirm gate

Documents the expected flow for AC7. The live QA session invokes
`assimilate-primitive` with `fixtures/hook-confirm/sample-hook.py` only —
the single fixture file named in AC7 and AC2.

Source authority: `packs/catalogue-curation/.apm/skills/assimilate-primitive/SKILL.md`
Phase 1, step 3: "Confirm on code."

---

## Fixture file

`sample-hook.py` is a self-contained git pre-commit hook — the only file ingested
in the AC7 QA session. It blocks commits when a `.env` file is staged. Pass
only this file to the skill.

---

## Detection trigger and raw-body review flow

The assimilation skill must detect executable code during Phase 1, before
confirmation. Detection fires when a file has an executable shebang (`#!/usr/bin/env ...`)
or a known script extension. `sample-hook.py` has a `#!/usr/bin/env python3`
shebang. **Why `python3` for a git hook:** git invokes the hook via the OS
`execve` system call, which resolves the shebang interpreter through
`/usr/bin/env` — shell aliases (e.g. `alias python=python3`) are never
consulted. `python3` is the portable choice for POSIX: it is present on all modern
macOS and Linux systems. `python` fails on most modern macOS/Linux where
the `python` binary was removed with Python 2. Windows installation is
out of scope — see the POSIX-only installation note in step 10. This is distinct from
agent lifecycle hooks (e.g. `packs/core/.apm/hooks/pre-pr.py`), which are
invoked via wiring commands that specify the interpreter explicitly
(e.g. `python tools/hooks/pre-pr.py`) — the shebang is not used for that
path, so `tools/hooks/README.md:3-8`'s `python` guidance applies only to
those invocation commands, not to git hook shebangs. (The directory-based
trigger — files under a `hooks/` directory — is not exercised here; the
fixture lives under `fixtures/hook-confirm/`, not a `hooks/` directory.)

**Phase 1 step 2 — show raw body before confirmation:**

The skill shows the raw body of `sample-hook.py` verbatim before issuing the
confirmation prompt. The operator cannot consent to code they have not read.

1. Fetch `sample-hook.py`.
2. Show the raw body verbatim.
3. Issue the confirmation prompt.
4. Wait for the exact phrase `yes, land this code` before proceeding.

---

## Expected confirm prompt

After showing the raw body, the skill must surface:

> ⚠ **This primitive is a Python script** — executable code that, if installed
> as a git hook, will run automatically on your machine on every commit attempt.
> It blocks commits when a `.env` file is staged.
>
> Raw content is shown above. Please review it before proceeding.
>
> Type **`yes, land this code`** to proceed, or **`no`** to abort.

Requirements the prompt must satisfy:
- Identifies the file as executable code (not prose).
- Describes what it does (blocks staged `.env` files).
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

Per `assimilate-primitive/SKILL.md:38-43`, all applicable gates run before any
write. For a raw Python hook body, the applicable pre-landing checks are:

- `agentbundle catalogue lint --deep` and `agentbundle catalogue verify` — these
  inspect the candidate in a **temporary catalogue** (a minimal packs/ scaffold
  containing only the **raw candidate file, byte-for-byte**, and its parent pack
  stub) before any shaping or real write. The raw file is used because shaping
  begins only in Phase 2 (`assimilate-primitive/SKILL.md:14-15`); gates must
  accept the raw candidate as safe before transformation. They are NOT run against
  the existing packs/ root (that would check only already-landed content).
- `bandit -c bandit.yaml --severity-level medium --confidence-level medium -q <candidate>` —
  LOW-severity findings (B404, B607, B603) do not block; only MEDIUM+ blocks.
  `sample-hook.py` has no MEDIUM+ bandit findings. The `-c bandit.yaml` flag
  preserves the repo's configured suppression list (e.g., B101 skipped globally).
- `semgrep --config p/python --config p/security-audit --config tools/semgrep/ --error --quiet --metrics off <SEMGREP_EXCLUDE> <candidate>` —
  with the candidate file path appended, `--metrics off` to suppress telemetry,
  and the repo's `SEMGREP_EXCLUDE` rules (from `Makefile`) applied so intentionally
  suppressed rules don't block compliant candidates.

All gates complete during Phase 1, before any shaping or writing begins. A
MEDIUM+ bandit finding, any semgrep `--error` hit, or a catalogue lint/verify
failure blocks landing pending explicit operator acknowledgment.

**Step 5 — Agentic-skills security review (AST01–AST10):**

Per the source contract (`assimilate-primitive/SKILL.md:45-48`), the AST review
applies to **SKILL.md and equivalent behaviour-definition files** — not to raw
scripts. `sample-hook.py` is a hook-body primitive (raw Python script), not a behaviour
definition. The confirm gate (step 3) and bandit SAST (step 4) are the applicable
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
   directly. `sample-hook.py` is one grep check — minimal, single-purpose. It
   clears this check.
3. The skill may note git's convention of extensionless hook names. The catalogue
   source ALWAYS keeps the `.py` extension (`pre-commit.py`) — extensionless files
   are excluded from hook-body discovery and upgrade matching. Only the manually
   installed copy (`cp ... .git/hooks/pre-commit`) drops the extension.

**Important — git hooks vs. agent hooks (two distinct landing paths):**

`sample-hook.py` is a **git pre-commit hook**, not an agent/editor hook.

- **Agent/editor hooks** (e.g., fires on `PreToolUse`) land as:
  - Hook body → `.apm/hooks/<name>.py` or `.apm/hooks/<name>.sh`
  - Hook wiring → `.apm/hook-wiring/<name>.toml` (binds body to editor event)
  - Projected via `FORCE=1 make build-self`. Hook-wiring does NOT apply to git events.

- **Git hooks** land differently — NOT via hook-wiring. The correct landing path:
  - Write the hook body **flat** under `.apm/hooks/` (e.g.,
    `packs/core/.apm/hooks/pre-commit.py`). **Do not create a subdirectory** such
    as `.apm/hooks/git/` — `build-self` iterates only immediate `.apm/hooks`
    children that are files; subdirectories are ignored.
  - Do NOT write a `.apm/hook-wiring/<name>.toml` for git events.

4. **Present the shaped target for approval before writing** (per
   `assimilate-primitive/SKILL.md:104-107`). The skill must show the operator:
   - Destination path: `packs/core/.apm/hooks/pre-commit.py`
   - Projected path (Claude Code / self-host): `tools/hooks/pre-commit.py`
   - Rename note: keep `pre-commit.py` as the catalogue path — `build-self`
     must project a `.py` file (hook-body discovery recognizes only `.sh` and
     `.py`; an extensionless file is skipped). The operator drops the extension
     only in the `cp` step when installing into `.git/hooks/pre-commit`.

   Wait for explicit operator approval before any write. A correct QA trace
   must include this approval step between Phase 2 diagnosis and the write.

5. Write the hook body via `agentbundle.safety.write_jailed`:
   - `packs/core/.apm/hooks/pre-commit.py` — projected to `tools/hooks/` by
     `build-self` (Claude Code / self-host adapter). Python is required here;
     `AGENTS.md:238-241` prohibits new bash scripts under `tools/`.
6. Bump version and update hook inventories **before** running `build-self` —
   the write makes the tree dirty and `build-self` requires `FORCE=1`:
   - Increment minor version in `packs/core/pack.toml`
   - Set the same version in `packs/core/.claude-plugin/plugin.json`
   - Both must match before `build-self` will accept the change.
   - Update the hook inventory in `packs/core/pack.toml`'s `description` field
     to include `pre-commit` alongside the existing hook list
     (`pre-pr, session-start + work-loop-check hooks`).
   - Update `packs/core/.claude-plugin/plugin.json`'s `description` field
     to match — `build-self` aggregates the plugin description as-is;
     stale metadata in `plugin.json` produces stale marketplace entries.
   - Update `packs/core/docs/index.md`: change `**Hooks (3):**` to
     `**Hooks (4):**` and add `pre-commit` to the hook list.
   - Update `tools/hooks/README.md`'s "What's here" section to document
     the new `pre-commit.py` hook and its installation behavior — `build-self`
     adds the file to `tools/hooks/` but does not update the README.
   (`build-self` does not update these inventory strings — they are
   human-maintained metadata that must be kept in sync manually.)
7. Run `agentbundle catalogue lint --deep` against the real `packs/` root
   after the write and metadata edits (per `packs/AGENTS.md:50-58`). This
   validates the integrated `packs/core` tree structure, not the pre-write temp
   catalogue. `lint --deep` passes at this point.
   **Do NOT run `agentbundle catalogue verify` yet** — verify step 15
   (`check_self_host`) will fail because `tools/hooks/pre-commit.py` and
   `.claude-plugin/marketplace.json` have not been regenerated. Run
   `build-self` first (step 8), then verify (step 8b).
8. Run `FORCE=1 make build-self` to project the new primitive and re-aggregate
   `marketplace.json`. Plain `make build-self` refuses on dirty trees.
8b. Run `agentbundle catalogue verify` against the real `packs/` root after
   `build-self`. Now that the self-host projection and marketplace are
   regenerated, verify's self-host drift step (step 15) passes clean.
9. Add a `## [core][version] — YYYY-MM-DD` changelog section in
   `docs/product/changelog.md` (the canonical post-bump record per
   `packs/AGENTS.local.md:16-19`).
10. Add documentation for manual installation. After `build-self`, the hook is
   projected to an adapter-specific path — adopters receive the projected file,
   NOT the catalogue authoring tree under `packs/core/.apm/`. The projected path
   depends on the installed adapter.

   **Installation (POSIX — macOS and Linux).** The hook uses a `python3`
   shebang and requires `python3` ≥ 3.11 on PATH, standard on modern systems.
   Native Windows cmd/PowerShell does not support POSIX shebangs; Windows users
   should use WSL or limit to POSIX environments for this hook.

   ```
   # Claude Code / self-host adapter (build-self projects to tools/hooks/).
   # Resolve the active hooks directory via Git — works in worktrees and
   # respects core.hooksPath; `.git/hooks` is wrong in linked worktrees.
   HOOKS_DIR="$(git rev-parse --git-path hooks)"
   if [ -e "$HOOKS_DIR/pre-commit" ] || [ -L "$HOOKS_DIR/pre-commit" ]; then
     echo "Warning: pre-commit hook already exists — back up or compose before overwriting."
   else
     cp tools/hooks/pre-commit.py "$HOOKS_DIR/pre-commit"
     chmod +x "$HOOKS_DIR/pre-commit"
   fi
   ```
   `FORCE=1 make build-self` only produces `tools/hooks/` (self-host targets
   Claude Code and Codex only). Adopters using Copilot or Cursor adapters
   must install those adapters and run their respective build steps first;
   the hook file then appears under the adapter's projected hooks directory.

**On "no":** the ingest is aborted.

1. No files are written to the catalogue.
2. Local source files (e.g., `fixtures/hook-confirm/sample-hook.py`) are NOT
   deleted — the skill only purges tool-created temporary copies; it never
   deletes caller-owned local inputs (per `SKILL.md:23-24`).
3. The skill surfaces: "Hook ingest aborted — no files written."

---

## What the QA session should verify

1. The skill is invoked with the single explicit file path `sample-hook.py`.
2. The raw body is shown BEFORE the confirmation prompt.
3. The confirm prompt identifies the file as executable code and describes what it does (blocks staged `.env` files).
4. The prompt requires the exact phrase `yes, land this code` — not just `yes`.
5. Answering anything other than `yes, land this code` prevents the skill from
   proceeding. A valid implementation may re-prompt for clarification rather than
   immediately aborting. Only an explicit `no` triggers mandatory abort.
   (The skill contract requires the exact phrase before proceeding — it does not
   mandate abort on every non-matching response.)
6. Answering `yes, land this code` triggers Phase 1 steps 4–5 before any write.
7. At step 4, all gates run PRE-WRITE during Phase 1. Catalogue lint/verify
   run against a **temporary catalogue** containing only the **raw candidate
   file (byte-for-byte)** and its parent pack stub — not the existing packs/
   root, and not the shaped form (shaping is Phase 2 only). Bandit (MEDIUM+
   threshold) and semgrep (with the candidate path appended) run against the
   candidate file.
   The fixture has no MEDIUM+ bandit findings and no semgrep errors; all gates pass.
8. At step 5, the skill correctly notes AST01–AST10 apply to SKILL.md behaviour
   definitions, not raw scripts; AST09 does NOT apply to a raw hook body.
9. Before writing, the skill presents the shaped target (destination path,
   projected path, rename recommendation) and waits for operator approval.
10. The hook body is written flat under `.apm/hooks/` (no subdirectory).
11. The skill does NOT create a `.apm/hook-wiring/` file for this git hook.
12. The version bump AND hook inventory updates happen BEFORE the post-write
    catalogue gates and `FORCE=1 make build-self`
    (pack.toml description + plugin.json description + docs/index.md hook count + tools/hooks/README.md + both version fields).
12b. After the write and metadata edits, `agentbundle catalogue lint --deep`
    runs against the real `packs/` root (not the pre-write temp catalogue)
    before `build-self`. `agentbundle catalogue verify` runs AFTER
    `build-self` (step 8b) — verify's self-host drift step (step 15) fails
    if called before the self-host projection is regenerated.
13. `docs/product/changelog.md` receives the new `## [core][version]` entry.
14. The manual install command uses the adapter-specific projected path (not
    `packs/core/.apm/hooks/`).
