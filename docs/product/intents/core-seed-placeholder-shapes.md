# Declared placeholder shapes for every core seed file

- **Status:** Draft
- **Level:** feature

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
