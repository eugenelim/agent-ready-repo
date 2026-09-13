# AGENTS.local.md

## This checkout

`AGENTS.md` is this self-hosted repository's live instruction surface. The generic
adopter source is `packs/core/seeds/AGENTS.md`; change it when new adopters need
the rule, without making the two files mechanically identical.

## Maintainer overlays

Maintainer-only overlays exist at `packs/AGENTS.local.md`, `packages/AGENTS.local.md`,
`packages/agentbundle/AGENTS.local.md`, and `packages/credbroker/AGENTS.local.md`.
They are insider context and are not exported by catalogue initialization.

## Commands

```bash
python -m agentbundle catalogue lint --root . --deep
python -m agentbundle catalogue verify --root .
```

## Worktree bootstrap

Never install this repo's own packages. The Makefile puts live worktree source on
`PYTHONPATH`; an editable install adds nothing and can leave a deleted-worktree path.
Once per machine, install `ruff`, `mypy`, `pytest`, and `-r tools/requirements.txt`;
a `.venv` is optional for tool-version isolation. Once per worktree, run `npm ci
--prefix docs-site`; `make test` reports that command when it is missing.
For bare `python -m agentbundle`, `pytest packages/credbroker`, or `pytest tests/`, export
`PYTHONPATH=packages/agentbundle:packages/credbroker` instead of installing.
A global install can silently shadow the tree, so a domain-looking error may be a stale import.

Once per clone, run `make bootstrap-git`. It registers the `regen` merge driver
that `.gitattributes` declares for self-host projections, so a merge settles
them instead of halting. Git config lives in the shared common directory, so one
run covers every linked worktree — but a fresh clone needs its own. Without it
git reports `Unknown merge driver: regen` and falls back to a normal conflicting
merge: degraded, never wrong.

## Sources and projections

Edit sources, not generated catalogue-scaffold projections. For changes under
`packs/` or `profiles/` that feed the scaffold, use
`tools/catalogue/sync_authoring_scaffold.py` to synchronize and check projections.

## Release coupling

See [`docs/guides/explanation/release-coupling.md`](docs/guides/explanation/release-coupling.md); per-package specifics live in `packages/AGENTS.local.md`.

## Projected source comments

Do not put `# AC10:`, `# AC36:`, or similar spec-AC citation comments in `.apm/**` source; strip the identifier and keep the invariant description.

## Landing changes

Auto-merge is disabled and branches must be current with `main`: update a behind branch before merging, then return to merge it manually. In a busy period, update it again if `main` moves.

Self-host projections carry `merge=regen`, so an update settles them instead of
halting. They are then stale, not correct — the side git kept was generated from
one branch's sources. Regenerate before committing:

```bash
git merge --no-ff origin/main   # or rebase; projections resolve silently
make build-self                 # expected to write; that is the point
git add -A                      # without this the amend drops what it wrote
git commit --amend --no-edit
```

Run `make bootstrap-git` once per clone or the driver is not registered and the
merge conflicts normally. Never pass `FORCE=1` from automation: the dirty-tree
refusal is fail-closed by design, and a scripted override defeats it. Pack
sources under `packs/*/.apm/` and `packs/*/seeds/` still conflict — those merges
carry decisions, so they are meant to reach you.
