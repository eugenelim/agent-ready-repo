# Expected-behavior transcript: hook-confirm

This document captures the `hook-confirm` flow end-to-end: the detection trigger,
the confirm prompt text, and the post-confirm landing path. Use this as the
reference document when running AC7's live QA session. The fixture file exercised
in that session is `fixtures/hook-confirm/sample-hook.sh`.

---

## Detection trigger

When `assimilate-primitive` receives a primitive that is (or contains) executable
code — a hook, shell script, Python script, or other runnable file — it must flag
it as a higher-scrutiny class before any other processing. The detection fires on:

- A file with a shebang line (`#!/usr/bin/env bash`, `#!/usr/bin/env python3`, etc.)
- A file with a `.sh`, `.py`, `.js`, `.rb`, or similar executable extension in a
  `hooks/`, `scripts/`, or `.git/hooks/` path context
- A file whose content begins with `#!/` (any interpreter shebang)

For `sample-hook.sh`: the file begins with `#!/usr/bin/env bash` and is named
`sample-hook.sh` — both the extension and the shebang trigger the detection.

**Critically:** detection fires *before* the security review and *before* any
craft-shaping. The sequence is:

1. Fetch the file (SSRF-guarded for URL sources; as-is for local paths).
2. Detect code class → flag as higher scrutiny.
3. Show the raw body verbatim to the operator.
4. Require explicit confirm before proceeding.
5. (Only after confirm) Run the repo's gate suite on the candidate.
6. (Only after gates pass) Craft-shape and land.

---

## Confirm prompt text

The confirm prompt must appear after the raw body is shown and before any write
occurs. Expected form:

---

**[assimilate-primitive] Executable code detected — explicit confirm required**

The primitive you are ingesting is a shell script (`sample-hook.sh`) that will
run on your machine on every `git commit` after installation. This is a
higher-scrutiny class than prose skill files.

**Raw content displayed above.** Read it carefully.

This script:
- Calls `python -m agentbundle.build lint-packs` — reads `packs/` directory,
  no write side-effect.
- Reads staged `SKILL.md` files and checks frontmatter — read-only.
- Calls `git add docs/product/changelog.md` — **modifies and stages a tracked
  file** without further operator input. Review whether this auto-staging behavior
  is acceptable.

Type **yes, land this code** to proceed, or anything else to abort:

---

**Required elements of the confirm prompt:**
1. Explicit label: "Executable code detected" or "Higher-scrutiny class: executable
   code."
2. Summary of what the script does, including any write or staging side-effects.
3. The confirm phrase "yes, land this code" (or equivalent unambiguous affirmation).
4. An abort path for any other response.

A bare "Proceed? [y/N]" does not satisfy the confirm requirement — the longer
phrase ensures the operator is consciously approving code installation.

---

## Post-confirm landing path

After the operator types "yes, land this code":

### Step 1 — Gate suite on the raw candidate

Before any write, run the repo's gate suite over the script:

```
lint-skill-spec        (if the hook accompanies a SKILL.md — applies to the bundle)
lint-agent-artifacts   (checks for governance citation leaks in any surrounding files)
snyk test              (SCA: if a requirements.txt or package.json accompanies the hook)
```

For `sample-hook.sh` alone (no accompanying SKILL.md): `lint-skill-spec` does not
apply. `lint-agent-artifacts` scans for internal governance references in text
files — applies to any `.md` files in the bundle. SCA applies only if a manifest
file is present (none for this fixture).

If any gate fails: block the landing and surface the violation for operator review.
Do not proceed past a gate failure.

### Step 2 — Write via the blessed jail

Route the write through `agentbundle.safety.write_jailed` / `assert_under`:

- Resolve the destination path (e.g., `packs/<target-pack>/.apm/skills/<skill>/hooks/pre-commit`).
- Resolve symlinks on the path.
- Verify the resolved path is under `packs/` (the write jail).
- Write the file.
- Set the file as executable (`chmod +x` or equivalent).

If the destination path escapes the jail or resolves to a symlink pointing outside
`packs/`, block the write and surface the violation.

### Step 3 — Prompt for build-self

After the file is written:

```
Hook written to: packs/<target-pack>/.apm/skills/<skill>/hooks/pre-commit

Run `make build-self` to project the hook into adapter-specific locations.

Note: git hooks are not installed automatically. To activate this hook in your
working tree, copy the file to `.git/hooks/pre-commit` and mark it executable:

  cp packs/<target-pack>/.apm/skills/<skill>/hooks/pre-commit .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit

Review the installed hook before activating it in CI or shared environments.
```

### Step 4 — QA session outcome recording

The AC7 outcome is recorded as a row in the parent spec's QA log table:

```
| 2026-07-24 | assimilate-primitive (hook-confirm) | Ingested sample-hook.sh fixture;
  script detected as executable code; raw body shown verbatim; confirm prompt
  issued with auto-staging side-effect noted; operator confirmed with
  "yes, land this code"; gate suite passed; written via write_jailed;
  build-self prompted; manual install note emitted. | PASS |
```
