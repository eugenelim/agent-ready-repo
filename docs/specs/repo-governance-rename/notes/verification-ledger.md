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

## T3 / AC-0009: observed hint from a manual CLI run

Run on macOS on 2026-10-25 against a throwaway fixture: `governance-extras` 1.0.3 and
`iac-terraform` 0.1.12 installed for `claude-code` from a pre-rename catalogue (`pre`),
then `agentbundle upgrade --pack governance-extras --scope repo --root repo post`
against a post-rename catalogue (`post`) that carries the map. Exit code 1, no file
changed. Stderr:

```
upgrade: pack 'governance-extras' was renamed to 'repo-governance'.
Run these steps to move to it:
  1. agentbundle uninstall --pack governance-extras --scope repo --root repo
This step is a move between catalogues: 'governance-extras' was installed from /private/tmp/exp/man/pre.
  2. agentbundle install --pack repo-governance --scope repo --adapter claude-code --output repo post
This step is a move between catalogues: 'iac-terraform' was installed from /private/tmp/exp/man/pre.
  3. agentbundle upgrade --pack iac-terraform --scope repo --root repo post
```

The sentences appear because the fixture recorded both packs from `pre`, not from the
reporting catalogue. The integration suite
`packages/agentbundle/tests/integration/test_rename_hint_cli.py` covers the same-source
case on the local-path, git and release-archive shapes.
