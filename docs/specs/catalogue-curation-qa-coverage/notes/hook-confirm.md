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
3. OR the primitive is delivered in a location that suggests it is a hook
   (e.g., under a `hooks/` directory in the source, or named
   `pre-commit`, `post-merge`, etc.).

`sample-hook.sh` satisfies criteria 1 (shebang) and 2 (`.sh` extension).
Both independently trigger the gate; either alone is sufficient.

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
>
> It executes the following commands:
> - `ruff format --check .`
> - `ruff check .`
> - `mypy packages/ --ignore-missing-imports`
> - `python3 -m pytest packages/ -q --tb=short -m "not integration"`
>
> Please review the script above before proceeding.
>
> **Do you want to land this hook? (yes / no)**

Requirements the prompt must satisfy:
- Identifies the file as **executable code** (not just "a file").
- Names the commands that will run on the operator's machine.
- Asks for an explicit `yes` or `no` — not a press-enter or implicit default.
- Does not proceed on ambiguous answers.
- Appears **after** the raw body is shown (raw body review is always first).

---

## Post-confirm landing path

**On "yes":** Phase 2 proceeds normally.

1. The skill diagnoses the destination pack (which pack should own this hook?
   most likely `core` if it is a general-purpose quality gate, or the source
   pack if it is specific to a particular workflow).
2. Anti-pattern check: hooks that trigger another skill (anti-pattern #1) are
   caught here even after confirm. `sample-hook.sh` does not trigger a skill,
   so it clears this check.
3. Reshape: the skill may recommend renaming the hook to match the target pack's
   hook-naming convention (e.g., `pre-commit` with no extension, placed under
   `.apm/hooks/` in the target pack).
4. Write via `agentbundle.safety.write_jailed` to the destination path.
5. Prompt `make build-self`.

**On "no":** the ingest is aborted.

1. The fetched working copy is discarded.
2. No files are written.
3. The skill surfaces: "Hook ingest aborted — no files written."

**On ambiguous answer ("maybe", "ok", "sure"):** the skill treats this as
"no" and re-surfaces the prompt, or aborts and asks the operator to restart
with a clear yes/no.

---

## What the QA session should verify

1. The confirm prompt fires before any write — no file lands without confirm.
2. The prompt names the commands (ruff, mypy, pytest) — not just "this is a
   script".
3. Answering "no" discards the primitive cleanly.
4. Answering "yes" proceeds to Phase 2 and eventually writes via the jailed
   write path.
5. The raw body is shown verbatim before the confirm prompt — not after.
