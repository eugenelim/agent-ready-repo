# Surface audit: where the `agent-plugin` route is missing

Measured 2026-09-03 against the working tree. Phase 1A shipped the portable Agent
Plugin projection and wired the route into one route-consuming surface. This is the
evidence behind the spec's Objective and AC1, and the reconciliation target for the
branch inventory in plan task T1.

## Method

A *surface* is a site whose value determines which routes a behavior applies to.
Sites were found by searching for bare quoted route names, for route output prefixes
(`startswith(("apm/", ...))`), and for literal collections consumed by a later
membership test — the last two forms are invisible to a search for bare names, and
each accounts for sites below.

Plan task T1 later reconciled this surface list against an AST inventory at commit
`1134701ba584ce5375358943f2cbab4ea69574a0`. The inventory is broader: it also lists
every route-selective branch inside a surface. The original site column named only a
collection's definition in several rows and was therefore too short for a branch
inventory. The definition and all known decision sinks are now named below.

`packages/agentbundle/templates/install-marker.py` is excluded by contract:
`agent-plugin` declares `lifecycle-trigger = "none"`, so it has no marker and its
absence there is correct rather than a gap.

## Result — 1 of 15

| # | Surface | Site | Carries `agent-plugin` |
| --- | --- | --- | --- |
| 1 | Default build recipes | `build/main.py:402,2388` | yes |
| 2 | Pack-declarable recipes | `commands/validate.py:37,182` | no |
| 3 | Install-route emission | `commands/install.py:59,1187` | no |
| 4 | Install dist-tree detection | `commands/install.py:1380` | no |
| 5 | Install route discovery | `commands/install.py:1908` | no |
| 6 | Install pack subtree paths | `commands/install.py:2451` | no |
| 7 | Install subtree roots | `commands/install.py:2591` | no |
| 8 | Install subtree iteration | `commands/install.py:2619` | no |
| 9 | Diff dist-tree detection | `commands/diff.py:160` | no |
| 10 | Upgrade dist-tree detection | `commands/upgrade.py:84` | no |
| 11 | Render targets | `commands/render.py:136-139,156-159` | no |
| 12 | Catalogue verification roots | `catalogue_tooling/verify.py:1348,1353,1360` | no |
| 13 | Build-check output checks | `build/self_host.py:1607-1659,1713-1742` | no |
| 14 | Route capability lint | `build/lint_packs.py:517` | no |
| 15 | Byte-invariance goldens | `tests/fixtures/distribution-routes/golden.json` | no |

## What the gaps mean

- **Recipes (2).** `VALID_RECIPES` is a closed set, so a pack declaring
  `per-pack-agent-plugin` is rejected at `:182` naming a set that excludes a recipe the
  default build runs.
- **Install (3–8).** The legacy emission omits the route; its comment at `:56` records
  that as predating the route. The four iteration sites walk `("claude-plugins", "apm")`
  to discover, path, enumerate, and clean per-pack subtrees, so a portable install is
  invisible to each. `:1908` carries a comment noting its rule duplicates
  `build/main.py`.
- **Dist-tree detection (4, 9, 10).** `startswith(("apm/", "claude-plugins/"))` decides
  whether a pack was installed through the catalogue-publishing path, so `diff`,
  `upgrade`, and `install` do not recognise a portable install as one.
- **Verification (12).** `projection_roots` feeds the membership test at `:1352`, so
  CAT-V verification skips the whole `agent-plugins` tree. The route ships unverified.
- **Build-check (13).** Only the Claude and APM lifecycle artifacts are asserted.
- **Capability lint (14).** Reads `route["claude-plugins"]["component-capabilities"]`
  directly.
- **Goldens (15).** Hold `apm` (20 entries) and `claude-plugins` (13);
  `test_distribution_route_golden.py:124` asserts exactly those two keys, so no byte of
  the portable output is pinned.

## Why one change closes all fourteen

Each gap is the same defect: a hand-maintained route list that nobody updated when a
route landed. Taking each list from `contracts/distribution-routes.toml` makes the
omission impossible rather than merely fixed, which is what prevents the Codex route
repeating it.

## Completeness

This table is an enumeration of sites found by the searches above, not a proof that no
other site exists. T1's detector must account for every row here, and T1's baseline is
accepted only after its report and this table are reconciled against each other — a
detector validated solely against its own fixtures and this list would be circular.

The T1 inventory also records route-selective decisions that are not extra AC1
surfaces: the Agent Plugin extension-metadata selection at `build/main.py:701`, contract
validation and dispatch branches in `build/main.py`, plus the Claude-plugin manifest
root at `catalogue_tooling/verify.py:1228`. Those sites explain why the branch inventory
has more rows than this fifteen-surface table; they do not change the surface count.
