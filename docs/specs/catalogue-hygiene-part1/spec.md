# Spec: catalogue-hygiene-part1

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->

Mode: light (no risk trigger fired — deletion is git-recoverable; AGENTS.md files are docs, not code)

> Note: The "destructive operation" trigger was considered for the AGENTS.md deletions. Because these
> files are checked into git and recoverable via `git checkout`, and the user approved the deletions
> explicitly after reviewing the full content, light mode is appropriate.

## Objective

Establish the export-boundary convention (`AGENTS.local.md` = insider-only, never exported) across
`packages/` and `packs/` before `agentbundle catalogue init` is built. Four tasks: delete stale
migration history, split insider content into `AGENTS.local.md` files, split README files for
PyPI vs fork consumers, and extend the strip rules in the `export-catalogue` skill.

## Acceptance Criteria

- [x] **AC-1** `packs/desk-research/AGENTS.md` and `packs/experience-design/AGENTS.md` are deleted.
      No replacement files created.
- [x] **AC-2** AGENTS.local.md split complete:
  - `packages/agentbundle/AGENTS.md` retains Windows portability + Concurrent install race sections only.
    New `packages/agentbundle/AGENTS.local.md` contains PyPI publishing + Engine-Change-RFC requirement.
  - `packages/AGENTS.md` retains Install-test coverage, Windows/cross-OS, Test conventions.
    New `packages/AGENTS.local.md` contains Release Coupling section.
  - New `packages/credbroker/AGENTS.md` covers package purpose + cross-OS/test rules.
    New `packages/credbroker/AGENTS.local.md` covers credbroker-v* tagging + PyPI publish workflow.
  - `packs/AGENTS.md` has the "Vendored copy" bullet removed from the Self-hosting projection section.
    New `packs/AGENTS.local.md` contains the vendored-copy bullet plus marketplace/release pipeline context.
- [x] **AC-3** README split for both packages:
  - `packages/agentbundle/README-pypi.md` exists (current README verbatim).
  - `packages/agentbundle/README.md` is fork-friendly (no badges; `pip install -e packages/agentbundle`;
    credbroker link points to `../credbroker/README.md`).
  - `packages/agentbundle/pyproject.toml` `readme = "README-pypi.md"`.
  - Same pattern for `packages/credbroker/`.
- [x] **AC-4** Strip rules extended in both skill files (byte-identical change):
  - `AGENTS.local.md` → `**/AGENTS.local.md`
  - `**/README-pypi.md` added to strip list

## Verification

```bash
agentbundle catalogue lint --root .
agentbundle catalogue verify --root .
```

Both must exit 0. No `AGENTS.local.md` path appears inside `.apm/**` content.
The two strip-rule files agree on the extended patterns.
