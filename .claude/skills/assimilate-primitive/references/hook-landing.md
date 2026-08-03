# Hook/script landing — mechanics

When the primitive is a hook or script (executable code), the landing path
differs from prose skills. Apply this after Phase 1 (including the explicit
`yes, land this code` confirm) and Phase 2 diagnosis.

## Git hooks vs. agent/editor hooks — two distinct paths

**Agent/editor hooks** (fires on `PreToolUse`, `PostToolUse`, etc.):
- Hook body → `.apm/hooks/<name>.py` or `.apm/hooks/<name>.sh`
- Hook wiring → `.apm/hook-wiring/<name>.toml` (binds body to editor event)
- Projected via `make build-self`

**Git hooks** (fires on `pre-commit`, `pre-push`, etc.):
- Write the hook body **flat** under `.apm/hooks/` (e.g.,
  `packs/core/.apm/hooks/pre-commit.py`).
- **Do not create a subdirectory** such as `.apm/hooks/git/` — `build-self`
  iterates only immediate `.apm/hooks` children that are files.
- **Do not write a `.apm/hook-wiring/<name>.toml`** for git events.
- Keep the `.py` extension in the catalogue source (`pre-commit.py`) — hook-body
  discovery recognizes only `.sh` and `.py`; an extensionless file is skipped.
  The `.py` extension is dropped only when installing into `.git/hooks/pre-commit`.

## Version bump and inventory sync — before `build-self`

After writing the hook body, bump version and update all inventory strings
**before** running `build-self` (the tree is dirty; use `FORCE=1 make build-self`):

1. Increment minor version in `pack.toml`
2. Set the same version in `.claude-plugin/plugin.json` — both must match.
3. Update the hook inventory in `pack.toml`'s `description` field.
4. Update `.claude-plugin/plugin.json`'s `description` field to match.
5. Update the pack's docs (e.g., hook count in `docs/index.md`).
6. Update `tools/hooks/README.md` if the repo projects hooks there — `build-self`
   adds the file but does not update the README.

`build-self` does not update these inventory strings — they are human-maintained
metadata.

## Run order

```
1. agentbundle catalogue lint --deep  (against packs/ root, after write + metadata edits)
2. FORCE=1 make build-self            (dirty tree; projects new primitive)
3. agentbundle catalogue verify       (after build-self — verify's self-host drift
                                       check passes only once the projection exists)
```

Running `verify` before `build-self` fails step 15 (self-host drift) — do not
reverse the order.

## Changelog

Add a `## [pack][version] — YYYY-MM-DD` entry in `docs/product/changelog.md`
after `build-self` completes (per `packs/AGENTS.local.md`).
