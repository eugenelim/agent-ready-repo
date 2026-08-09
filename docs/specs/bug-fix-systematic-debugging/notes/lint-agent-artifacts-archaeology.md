# Decision archaeology — standalone agent-artifact lint command

## Terminal artifact

- Commit `96232e6` dated 2026-07-26 deletes
  `tools/lint-agent-artifacts.py` while folding standalone catalogue checks into
  `agentbundle catalogue lint` and `agentbundle catalogue verify`. The commit
  introduces deep lint for agentskills.io compliance and routes artifact
  verification through the catalogue CLI.

## Chronology

1. **2026-05-24** — commit `8b2c994` creates the Python standalone linter as
   part of the Windows-parity port from shell scripts. One Python implementation
   avoids shell/PowerShell parity drift.
2. **2026-07-26** — commit `96232e6` deletes the standalone agent-artifact
   linter and related invocation and test paths while moving the owning checks
   behind catalogue subcommands. The companion shipped spec explicitly rejects
   a compatibility shim and assigns agent-artifact checks to catalogue
   verification.
3. **2026-08-04** — commit `62f4faf` adds the already-deleted command to
   `AGENTS.local.md`. The local patch names no replacement and does not restore
   the script. Its rationale for reviving the obsolete entry is not established
   by the local artifact trail.

## Rationale chain

- The current command surface is the catalogue CLI because artifact lint is a
  catalogue concern and the fold removes duplicated invocation and test paths
  (`96232e6`; `docs/specs/fold-standalone-linters-into-cli/spec.md`).
- The standalone Python file had replaced a shell implementation for Windows
  parity, not because a separate command path was a durable requirement
  (`8b2c994`).
- The later documentation-only reintroduction does not reverse the deletion or
  its no-shim boundary. Treating it as a reversal would leave guidance pointing
  to a nonexistent file. [synthesis]

## Alternatives considered

- **Keep the standalone linter** — rejected when catalogue lint and verification
  became the owning command surface (`96232e6`).
- **Add a compatibility shim at the old path** — explicitly out of scope in
  `docs/specs/fold-standalone-linters-into-cli/spec.md`; the migration deletes
  old call sites instead.

## Revival candidates

None. The catalogue CLI exists in the current tree and its help exposes
`catalogue lint --deep`; catalogue verification retains the projected
agent-artifact check. The reasons for rejecting a duplicate standalone path
still hold.

## Open questions

- The local commit trail does not establish why the deleted command was added
  back to `AGENTS.local.md` on 2026-08-04. Any explanation beyond a stale-source
  mistake would be inference.
