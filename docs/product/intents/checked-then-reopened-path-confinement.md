# Bind checked paths to the objects later read

- **Status:** Draft
- **Level:** feature

## Outcome

Confinement-sensitive operations hold verified directory or file objects rather than reopening a path that a concurrent writer can replace.

## Opportunity

`--spec-dir` resolvers and finding-adjudicator cited-file reads check canonical paths before use but do not bind later operations to the checked object.

## What this absorbs

### loop-spec-dir-confinement-toctou

The 2026-08-29 security review of spec-dir confinement in PR #1156 found that `loop-cohort` and `loop-engine` canonicalize `--spec-dir`, prove it is below the repository root, and later use the path without binding it to the checked object. `packs/core/.apm/skills/work-loop/scripts/loop-engine.py:950` has `resolved = Path(raw).resolve()` and returns a checked path at `:961`, not a directory descriptor. A concurrent local writer can replace the checked directory with a symlink to an external path between check and use, and the operation follows the new link.

The race was not introduced by PR #1156: the same shape pre-existed in `loop-engine.py`; the PR strictly improved confinement rather than weakening it. It is the same class as `adjudicator-cited-read-toctou`. Do not use a path-level half-measure, because it would claim a boundary that does not exist. The remedy is a directory-FD redesign: `openat`-style operations with `O_NOFOLLOW`, with every downstream state read and write relative to verified descriptors. That redesign covers both resolvers and every downstream call site. Exploitation requires concurrent working-tree write access, which gives the attacker more direct options such as editing the source. Unblocks when someone takes the directory-FD redesign as its own spec.

### adjudicator-cited-read-toctou

The finding-adjudicator canonicalizes a cited path, checks confinement, and later reads the path without binding the read to the checked object. `packs/core/.apm/agents/finding-adjudicator.md:52` says `resolve the cited path to its canonical real path, then apply every check below to that resolved path`. A regular file admitted by that check can be replaced with an external symlink before the read, and the agent follows it.

The cited-file read-envelope adversarial review surfaced this race. It was not introduced by that change and was not a reason the change was held: the identical race already applies to all five orchestrator-supplied paths because the agent has always been instructed in terms of paths. The envelope added one path source, not a new exposure class. Exploitation needs concurrent working-tree write access during adjudication, which gives an attacker more direct options such as editing the source under review. Do not fix this in prose: the agent's “read file at path P” capability cannot hold a checked file object, and such an instruction is a no-op or permanently indeterminate. Provide a runtime/tool-layer stabilizing contract, or have the orchestrator snapshot admitted files into the read allowlist and supply snapshots instead of paths. Unblocks when the tool layer can express a checked-then-bound read.

## Assumptions

- The selected remediation must provide descriptor- or snapshot-bound operations; path-level validation alone does not close either race.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
