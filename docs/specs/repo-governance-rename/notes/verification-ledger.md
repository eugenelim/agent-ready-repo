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

## T6 / AC-0024, AC-0029, AC-0032: observed end-to-end steps and seed survival

Run on macOS on 2026-10-25 against throwaway fixture catalogues (local paths): `governance-extras` 1.0.3 and
`iac-terraform` 0.1.12 installed for `claude-code` from `pre`, `docs/adr/README.md` edited by hand,
then the hint from `upgrade --pack governance-extras --scope repo --root <repo> post` was run step by step
with `--yes` and no `--force`. Both fixture packs ship a `seeds/docs/adr/README.md`. Paths below use `<tmp>`.

```
1. agentbundle uninstall --pack governance-extras --scope repo --root <tmp>/repo
   -> exit 0: uninstall: 2 removed, 1 kept
              uninstall: keeping adopter-edited file: docs/adr/README.md
2. agentbundle install --pack repo-governance --scope repo --adapter claude-code --output <tmp>/repo <tmp>/post
   -> exit 0: installed: repo-governance @ repo via claude-code
              install: delivered 1 seed(s) for pack repo-governance; 1 collided with your edits and were kept as *.upstream.<ext> companions
3. agentbundle upgrade --pack iac-terraform --scope repo --root <tmp>/repo <tmp>/post
   -> exit 0: upgraded: iac-terraform @ repo 0.1.12 -> 0.2.0
```

Seed survival: the Plan's risk did not occur. The uninstall keeps an adopter-edited seed, and the reinstall
leaves it untouched and writes the shipped text beside it as `docs/adr/README.upstream.md`. The edited
`README.md` still read `ADOPTER EDIT` after step 3. `test_recorded_pre_rename_archive_migrates` asserts both files.

## 2026-10-25 — Contract amendment: "no recorded source" covers a non-text value

- Review round 3 (adversarial, adjudicated) sustained that the code treats a non-text recorded source as "no recorded source" while the spec Term listed only missing, empty or `agent-ready-repo`, and that the Term's claim of matching `upgrade --all` was false (`upgrade --all` treats only a missing source and the legacy value as absent).
- The owner (eugenelim) approved on 2026-10-25 amending the Term to: "No recorded source means the recorded source is missing, empty, not text, or the legacy value `agent-ready-repo`.", removing the `upgrade --all` equivalence clause. No acceptance criterion, task or behaviour changes; the code and tests already implement the amended Term.

## 2026-10-26 — Contract amendment: AC-0025 admits a pinned golden fixture and a frozen-record path

- PR #1614 CI (merged with main at 1f9c27342) showed two files that must keep the old pack name: the digest-pinned golden fixture `packs/core/tests/skills/work-loop/fixtures/corpus/001-recorded/plan.md` (its test forbids regeneration) and the path `docs/specs/governance-extras-without-core/*` in the live `docs/specs/workspace-retirement/inventory.toml`, which names a frozen shipped spec directory.
- The owner (eugenelim) approved on 2026-10-26 adding two AC-0025 categories: digest-pinned golden fixtures whose tests forbid regeneration, and references to the path of a frozen record whose own name contains the old pack name. The completeness test admits exactly those two files by explicit path.
