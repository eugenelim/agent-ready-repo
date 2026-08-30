# Declared placeholder shapes for every core seed file

- **Status:** Draft
- **Level:** feature

## Disposition — refuted 2026-08-29, no change made

**This intent's premise is false. Do not act on it.** All three files named below
already declare their placeholder shapes, at
`packages/agentbundle/agentbundle/catalogue_tooling/lint.py:378-380`. They were added
by `fd59e28c6` — the same commit this intent says introduced the files.

Measured on a clean tree at `27e7430e9` (HEAD == `origin/main`):

- `catalogue lint --root .` → `ok: catalogue lint clean (0.40.2)`
- `catalogue verify --root .` → `catalogue verify: ok`

Zero `CAT-V-002`.

**Where the phantom came from.** The bare `agentbundle` console script on `PATH`
resolves to a stale **0.40.0** wheel in the shared interpreter's `site-packages`,
whose `lint.py` contains none of the three keys. Running it reproduces exactly the
three errors verbatim. The "Verified pre-existing" claim below does not hold: the
module was loaded from `site-packages`, so which worktree was checked out never
determined which `lint.py` ran.

This is expected under ADR-0094, which accepts worktree-source-leads-installed-
distribution as "the normal state during development … a consequence to know about,
not a defect to fix". Repository-directed invocations must use
`python3 -m agentbundle` with `packages/agentbundle` on `PYTHONPATH`, as every `make`
target already does.

The original text is preserved below unchanged, because the record of what was
believed — and why it was wrong — is the useful part.

## Outcome

`agentbundle catalogue verify` passes on `packs/core/seeds/**` because every seed
file has a declared placeholder shape, so a new seed cannot ship without one.

## Opportunity

Three core seed files carry no declared shape, so `CAT-V-002` fails on each:

- `packs/core/seeds/.agents/rules/cognitive-load.md`
- `packs/core/seeds/AGENT_RULES.md`
- `packs/core/seeds/docs/AGENTS.md`

The lint is fail-loud by policy — every seed under `packs/<pack>/seeds/` must
declare its shape in `_PackRules._check_seeds:_SEEDS_REQUIRED_PLACEHOLDERS` — so
the fix is to declare the three shapes or remove the files, not to relax the
rule.

Verified pre-existing rather than assumed: running `catalogue verify` against a
detached `origin/main` worktree reproduces the same three errors, and none of the
three files appears in the diff of the change that observed them. They arrived
with `fd59e28c6` ("reduce cognitive load across agent output").

## Assumptions

- The three files are intended to ship as seeds; if any is not, removal closes
  its error instead of a declaration.
- No pack outside `core` is affected — the failures name only `packs/core/seeds/`.

## Source

- Mode: repo-origin
- Locator: packs/core/seeds
- Revision: local-2026-08-29
