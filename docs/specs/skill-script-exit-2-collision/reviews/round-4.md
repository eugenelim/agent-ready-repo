# Implementation review round 4

## Blockers

**1. Markdown-to-HTML dependency setup still operates on the caller's current working directory.** `packs/converters/.apm/skills/markdown-to-html/SKILL.md:55`
The skill tells agents to run bare `node -e` dependency checks and
`npm install` from the skill directory without first resolving or naming that
directory. A project-root invocation can therefore check or mutate the adopter
project instead of the installed skill. Fix: make every dependency check and
install use the resolved `<skill-dir>` explicitly via `npm --prefix`, and add a
source-contract regression rejecting bare `npm install` in this skill.

## Concerns

**1. The hostile-path test bypasses the production dependency-hint builder.** `packs/converters/tests/skills/markdown-to-html/test_invocation_contract.py:120`
The regression passes a hand-built npm argv directly to the POSIX quoting
helper, so it remains green if `loadDependencies()` later drops `--prefix`,
reorders arguments, or resumes unsafe interpolation. Fix: extract and export a
pure dependency-install-hint builder used by `loadDependencies()`, then assert
that builder's exact hostile-path output.

## Nits

None.

## Specialist results

Security reviewer: Clean — ready to commit.

## Remediation disposition

Both findings were in-scope and were applied.

1. The skill now uses the preflight-resolved `<skill-dir>` as an explicit npm
   prefix for both the dependency check and install. Its source contract
   requires the prefixed forms and rejects a line beginning with bare
   `npm install`.
2. `loadDependencies()` now calls an exported pure
   `dependencyInstallHint(skillDir, platform)` builder. The hostile-path test
   calls that production builder and asserts the exact POSIX argv order plus
   the bounded Windows refusal result.
