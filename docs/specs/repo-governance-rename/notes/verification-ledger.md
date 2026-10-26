# Verification ledger: repo-governance-rename

Execution observations. The spec and plan stay pinned; results land here.

## T2 / AC-0031: `zsh -n` on placeholder-bearing steps

Run on macOS (Darwin 25.5.0, zsh 5.9 arm64-apple-darwin25.0) on 2026-10-25, through
`packages/agentbundle/tests/unit/test_pack_renames.py::test_placeholder_steps_are_shell_syntax_errors[zsh]`
(passed, not skipped). Each step is rejected as a syntax error (non-zero exit),
as is `bash -n` and `sh -n`. A direct `zsh -n -c` of each form returned a non-zero exit.

| Fixture class | Result |
| --- | --- |
| Install step, no old adapter row (single install step, no `--adapter`) | rejected by `zsh -n` |
| Install step, old pack with one adapter row (`--adapter claude-code <catalogue-source>`) | rejected by `zsh -n` |
| Install steps, old pack with two adapter rows (multi-adapter) | rejected by `zsh -n` |
| Dependent upgrade step, one adapter row | rejected by `zsh -n` |
| Dependent upgrade steps, two adapter rows (`--adapter <adapter> <catalogue-source>`) | rejected by `zsh -n` |
