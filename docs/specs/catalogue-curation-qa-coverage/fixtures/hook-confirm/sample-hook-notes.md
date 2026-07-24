# Hook fixture notes: sample-hook.sh

## What the hook does

`sample-hook.sh` is a git pre-commit hook that runs three checks before any
commit is allowed to proceed:

1. **Lint gate.** Runs `python -m agentbundle.build lint-packs` over the `packs/`
   directory and fails the commit if any violation is reported.

2. **Frontmatter version check.** For any staged `SKILL.md` file, verifies that a
   `version:` field is present in the YAML frontmatter. A missing field fails the
   commit.

3. **Changelog stamp.** If any `SKILL.md` was staged, inserts a datestamp comment
   into the `[Unreleased]` section of `docs/product/changelog.md` and stages the
   updated file. This ensures every skill-touching commit leaves a trace in the
   changelog.

## Why this requires explicit operator confirm

An ingested hook is executable code that runs on the operator's machine on every
`git commit` — it is not inert prose like a SKILL.md. The risks specific to this
hook:

- **Arbitrary command execution at commit time.** The hook calls
  `python -m agentbundle.build` and `sed -i`, which modify the filesystem and
  stage additional files without further operator input. A malicious or buggy hook
  in this position could exfiltrate data, corrupt the working tree, or silently
  stage attacker-controlled content.

- **Auto-staging behavior.** Step 3 calls `git add "$CHANGELOG"` — the hook
  modifies a tracked file and stages it as part of the commit without the operator
  seeing the change. This is a silent write that bypasses the normal review-before-
  stage workflow.

- **D6 residual gap.** As noted in the parent spec, the engine path-gate contains
  *changesets*, but a hook executes at session/commit time before a diff is visible.
  The hook-confirm gate is the compensating control: the operator must explicitly
  approve before this code is installed.

## Expected confirm prompt

When `assimilate-primitive` detects that the ingested primitive is (or contains)
executable code, it must flag it as a higher-scrutiny class and require a distinct
explicit confirm before landing. The expected confirm interaction looks like:

---

**[assimilate-primitive] Code detected — explicit confirm required**

The primitive you are ingesting includes executable code (`sample-hook.sh`), which
will run on your machine on every `git commit` after installation.

**Raw content shown above.** Review it carefully before proceeding.

This hook:
- Runs `python -m agentbundle.build lint-packs` (modifies nothing, read-only lint).
- Reads staged `SKILL.md` files and checks for a `version:` frontmatter field.
- Calls `git add docs/product/changelog.md` to stage an auto-generated datestamp
  (this modifies a tracked file and stages it without further input).

Type **yes, land this code** to proceed with ingest, or anything else to abort:

---

The confirm phrase "yes, land this code" (or an equivalent unambiguous affirmative)
must be typed by the operator. A bare "yes" or "y" is insufficient — the longer
phrase ensures the operator is consciously affirming code installation, not
reflexively confirming a prompt.

## Post-confirm landing path

After the operator confirms:

1. The hook file is written to the destination under the skill's `scripts/` or
   `hooks/` directory (depending on the pack layout), routed through
   `agentbundle.safety.write_jailed` to confirm the path is within `packs/`.
2. The repo's gate suite is run on the hook file (`lint-skill-spec`,
   `lint-agent-artifacts` for the surrounding skill; SAST/SCA via `.snyk` where
   applicable).
3. The operator is prompted to run `make build-self` to project the updated pack
   into the adapter-specific locations.
4. The operator is reminded that the hook must be manually installed by copying
   the file to `.git/hooks/pre-commit` and marking it executable — agentbundle
   does not auto-install git hooks.
