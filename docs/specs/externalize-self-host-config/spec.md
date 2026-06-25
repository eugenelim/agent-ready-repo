# Spec: Externalize the self-host pack and adapter allow-lists

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Mode:** light (no risk trigger fired)

## Objective

The self-host projection set is split across two hand-synced sources: the
`SELF_HOST_PACKS` / `SELF_HOST_ADAPTERS` constants in
`agentbundle/build/self_host.py`, and the `recipes/self-host.toml` recipe whose
`[recipe.adapters].targets` is a manual mirror of `SELF_HOST_ADAPTERS` (and
which lists no packs at all). The recipe comment even says it "keeps this list
in sync" by hand. Make the recipe the single authoritative source the code
*reads*, collapsing the duplication so the self-host set is config-driven
rather than hardcoded.

## Acceptance Criteria

- [x] AC1: `recipes/self-host.toml` declares the self-host pack allow-list under
  `[recipe.packs].include` and keeps the adapter allow-list under
  `[recipe.adapters].targets`; the adapter comment names the recipe as the
  authoritative source rather than a hand-synced mirror.
- [x] AC2: `self_host.py` derives `SELF_HOST_PACKS` and `SELF_HOST_ADAPTERS` by
  reading those recipe keys, using the same filesystem-first /
  `importlib.resources` fallback resolution pattern `build/main.py` already uses
  for recipes.
- [x] AC3: When the recipe file or a key is missing or malformed, both fall back
  to the prior built-in literals — module import never raises.
- [x] AC4: `make build-check` passes — the self-host projection is byte-identical
  (the recipe carries today's values), and the existing self-host tests
  (`test_self_host_check.py`, `test_adapter_cursor.py`, `test_adapter_gemini.py`)
  stay green.

## Tasks

1. Add `[recipe.packs].include` to `recipes/self-host.toml` with the current
   three packs; update the `[recipe.adapters]` comment to name the recipe as
   authoritative.
2. Add the recipe-reading loader to `self_host.py` and derive the two constants
   from it, keeping the constant names so all call sites and tests are unchanged.
3. Add a unit test: a pure extractor applies the defaults on empty/missing input
   and reads values when present; the module constants match the shipped recipe.

## Declined

- Tempted to thread the parsed recipe through `cmd_self` into every filter call
  site; declining — module-level derivation keeps the constant names and avoids
  editing five call sites plus their tests for no behavioral gain.
- Tempted to add a new top-level catalogue config file; declining — the
  self-host recipe already exists and is the natural home; a new top-level file
  is a heavier, RFC-shaped change.
- Tempted to remove the `SELF_HOST_*` constants entirely; declining — they are
  imported by tests and other call sites, so deriving them preserves the
  interface with the smallest diff.
