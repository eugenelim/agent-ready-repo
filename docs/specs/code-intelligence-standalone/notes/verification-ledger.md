# Verification ledger: code-intelligence-standalone

## T1: A user-scope install succeeds with no packs installed

- Date: 2026-10-10
- Tests: `packs/code-intelligence/tests/pack/test_manifest.py` red before the
  manifest edit (2 failed, 10 passed), green after (12 passed, 0 failed).
- Lint: `make lint-ruff lint-mypy` passed.
- Manual install, run from an empty git repository with `HOME=<tmp>/home`:
  `agentbundle install --pack code-intelligence --scope user --adapter claude-code <catalogue>`
- Exit code: 0
- Installed skill path: `<tmp>/home/.claude/skills/code-intelligence/SKILL.md`
