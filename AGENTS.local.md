# AGENTS.local.md

Repo-local addendum for maintainers of this checkout. Keep guidance here
specific to this repository instance; shared agent instructions belong in
`packs/core/seeds/AGENTS.md` and are projected to `AGENTS.md`.

## Self-hosting drift — check before editing any file at a projected path

This repo is self-hosted from `packs/`. Many files at `<repo>/...` paths
are **rendered outputs**, not the source-of-truth. Editing them directly
trips `make build-check` and blocks every PR.

**Always-projected paths** (drift-prone — edit the seed, not the projection):

| Projected path                       | Source of truth (seed)                                       |
| ------------------------------------ | ------------------------------------------------------------ |
| `AGENTS.md`, `CLAUDE.md`             | `packs/core/seeds/AGENTS.md` (symlinked at the projection)   |
| `docs/CHARTER.md`, `docs/CONVENTIONS.md`, `docs/APPROACH.md` | `packs/core/seeds/docs/...`                       |
| `docs/architecture/overview.md`      | `packs/core/seeds/docs/architecture/overview.md`             |
| `docs/specs/README.md`               | `packs/core/seeds/docs/specs/README.md`                      |
| `docs/rfc/README.md`                 | `packs/governance-extras/seeds/docs/rfc/README.md`           |
| `docs/adr/README.md`                 | `packs/governance-extras/seeds/docs/adr/README.md`           |
| `docs/guides/**/README.md`           | `packs/user-guide-diataxis/seeds/docs/guides/**/README.md`   |

**The workflow when you touch any of the above:**

1. Edit the seed file (under `packs/<pack>/seeds/...`), *not* the
   projected output.
2. Run `make build-self` to regenerate every projected path from its seed.
3. Run `make build-check` to confirm zero drift before committing.

**How to discover the seed for a path you're unsure about:**

```bash
# If you're not sure whether a path is projected:
find packs -path "*/seeds/<projected-path>" 2>/dev/null

# Or just edit the projected path and let make build-check tell you:
make build-check    # exits non-zero with "edit <seed-path>; run: make build-self"
```

The `make build-check` error message names the seed path you should
have edited — so if you do trip it, the fix is mechanical (edit the
seed it names, re-run `make build-self`, re-commit).

**Drift fixed twice already** (each time a CI cycle wasted):
- RFC-0007 PR (#53) added a row to `docs/rfc/README.md`; fixed by
  propagating to `packs/governance-extras/seeds/docs/rfc/README.md`.
- converters-pack spec PR (#57) added a row to `docs/specs/README.md`;
  fixed by propagating to `packs/core/seeds/docs/specs/README.md`.

If you edit any README, table, or doc under the projected paths above,
**check the seed first**.
