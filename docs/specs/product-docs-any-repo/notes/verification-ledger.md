# Verification ledger: product-docs-any-repo

## T7 — real invocation against a non-pack repository (AC11)

- **Date:** 2026-10-10
- **Subject:** a fresh implementer subagent with no session context, instructed to follow only the projected skill at `.claude/skills/author-product-docs/` and to read no other worktree file.
- **Fixture:** a throwaway repository outside the worktree: `pyproject.toml` with `[project.scripts] tidyfs = "tidyfs.cli:main"`, an argparse parser in `src/tidyfs/cli.py` (subcommands `organize` and `undo`), and a README that opens with a flag table, lists a `--verbose` flag the parser does not define, and has no `pack.toml`.
- **Request:** "Audit this project's docs."

### File-read log (as reported, in order)

1. `.claude/skills/author-product-docs/SKILL.md`
2. `.claude/skills/author-product-docs/references/surface-discovery.md`
3. `.claude/skills/author-product-docs/references/docs-journey.md`
4. `.claude/skills/author-product-docs/references/repository-ownership.md`
5. `.claude/skills/author-product-docs/references/page-contracts.md`
6. `.claude/skills/author-product-docs/references/rendered-verification.md`
7. `<fixture>/README.md`
8. `<fixture>/pyproject.toml`
9. `<fixture>/src/tidyfs/cli.py` — the argument-parser source, read before the report
10. `<fixture>/src/tidyfs/__init__.py`

### Report excerpt

- **Mode:** audit. **Surface:** "CLI. The evidence is `[project.scripts] tidyfs = "tidyfs.cli:main"` in pyproject.toml and an argparse parser in cli.py."

| Stage | Status |
| --- | --- |
| Discover and evaluate | partial |
| Install | partial |
| First success | missing |
| Daily tasks | missing |
| Look up | partial |
| Understand | missing |
| Troubleshoot | missing |
| Upgrade | missing |
| Contribute | missing |

- Each row carried file:line evidence and a next action; actions were ranked with first success first.
- Page-level finding: "`--verbose` ... is documented. The parser in cli.py:6-14 defines no `--verbose` flag ... The claim contradicts the shipped CLI." It also found the undocumented `undo` subcommand and the unstated `--by` default.
- No file was edited; no FAQ or `llms.txt` was proposed.

### Verdict

Pass. The agent named the CLI surface, opened the parser file before returning its report, and returned a nine-row journey gap report.

### Follow-up applied

The subject reported two ambiguities for audit mode: which drafting steps apply, and whether read-only checks such as `--help` may run. `SKILL.md` now states that audit and verify run Steps 2–6, 8, and 15–16, that read-only checks are allowed in every mode, and how the Step 16 items follow the audit report.
