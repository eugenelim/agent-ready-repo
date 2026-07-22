# Export transform manifest — five declared operations + a gate

The whole export is declarative: what to strip, what to substitute, what packs
travel, which guides travel, what tools are projected — plus a fail-closed
verify. No content-regex, no DSL, no engine. Every anchor names its **source**
in the *running* catalogue, so the tooling ships with no hardcoded upstream
literal (run here it resolves to this catalogue's identity; run in a fork, to
the fork's).

## 0. SEEDS (planted after Strip; fresh scaffold, not stripped)
For each projected tool (core, governance-extras) and any include-set pack
with a `seeds/` directory, copy the seed tree to the target root **after**
the Strip pass so seeds land cleanly without being stripped. Establishes the
workflow scaffold the skills navigate: `AGENTS.md`, `workspace.toml`,
`docs/CONVENTIONS.md`, `docs/architecture/`, `docs/knowledge/`,
`docs/product/`, `docs/specs/`, `docs/adr/README.md`, `docs/rfc/README.md`.
Seeds are read from the live pack source at export time — auto-syncs when the
pack changes. **`docs/CHARTER.md` collision:** the seed plants a blank
template; the MISSION CAPTURE step (below) overwrites it immediately. The
substitution pass (section 2) covers all seed content.

## 0a. MISSION CAPTURE (overwrites seed `docs/CHARTER.md`)
Elicited from the operator at export time. Accepts: a bare keyword (`PKM`,
`legal`), a sentence, or a path to an existing CHARTER.md. Overwrites the
seed template in the target (never modifies the running catalogue). Serves as
the charter anchor for future `assimilate-repo` runs from within the fork.

## 1. STRIP (deny-by-default; mode-independent)
Path/glob globs, removed in **both** `white-label` and `attributed` modes —
attribution never re-admits governance:
- Catalogue-governance: `docs/rfc/`, `docs/adr/`, `docs/specs/`, `docs/backlog.md`.
- The catalogue's own working `docs/CHARTER.md`, `docs/CONVENTIONS.md`,
  `AGENTS.local.md`, `CONTRIBUTING.md`. (A *projected* CONVENTIONS template that
  ships to adopters via the self-host recipe is a different artifact — it rides
  with the recipe; keep it.)
- Build/scan/release tooling: `Makefile`, `.snyk`, scanner config, release
  workflows, `tools/*` self-tests.
- Provenance-only comments citing a stripped governance doc (keep comments that
  explain *why the code does what it does*).

## 2. SUBSTITUTE (anchor → value; each names its SOURCE and SCOPE)

| Anchor | Source in the running catalogue | Scope | Blanket-safe? |
| --- | --- | --- | --- |
| Full repo URL | `.adapt-discovery.toml [markers].repo-url` | any occurrence | yes (compound) |
| Full maintainer email | `pack.toml [[pack.maintainers]].email` + git config | any occurrence | yes (compound) |
| Slug | `.adapt-discovery.toml [markers].project-name` | path/glob-scoped, coupled to every `pack.toml catalogue =` + fixtures | no (bare-token blanket replace corrupts text) |
| Owner | `.adapt-discovery.toml [markers].owner` | path/glob-scoped | no |

Ride-along rewrites: `pip install <pkg>` → `pip install -e .` (a fork is
editable-only); a `CLAUDE.md` symlink → a real file with resolved `AGENTS.md`
content.

### RE-HOME transforms (persisted fork defaults — target copy only)
Applied only to the export *target*, at these declared anchors, never the
running engine (so not a D6 change): blank `install-defaults.toml` `source`; set
`scope.py DEFAULT_ADAPTER` to the fork's default; set `self-host.toml`
`[recipe.adapters].targets` + `[recipe.packs].include`.

## 3. INCLUDE-SET (operator choice)
Always keep: the engine, a `core` (or a lighter re-based core for a non-SDLC
catalogue), and `catalogue-curation` itself so the fork can self-curate. Drop any
pack the derivative doesn't want (e.g. SDLC packs for a creative-writing
catalogue) — this is the domain-repurposing lever.

## 4. GUIDES (per-pack, with _shared always)
For each pack in the include-set, copy `docs/guides/<pack-name>/` into the
target at the same path. Always copy `docs/guides/_shared/` (agentbundle
infrastructure guides; adopter-facing, not catalogue-internal). Guides for
packs outside the include-set are **omitted** (omit-not-leak). The SUBSTITUTE
pass applies to all staged guide content; any identity references in `_shared/`
guides survive into the target only in substituted form.

## 5. TOOL PROJECTION (core + governance-extras + catalogue-curation)
After all content writes, project the three required packs from this
catalogue's `packs/<name>/.apm/skills/` into the target's `.claude/skills/`
and `.agents/skills/` directories. These travel as *local installed tools* (not
as catalogue packs in the fork's own `packs/`), so the fork can self-curate
without inheriting the upstream pack catalogue. The SUBSTITUTE pass applies to
projected files before they are written.

## 6. VERIFY (fail-closed, mode-aware) — hard-fails the export
- Grep the target for surviving upstream **URL, email, slug, owner** (all four
  substitute anchors) — **case-insensitive**, over **text files** (binary out of
  scope, declared), matching declared **literals only** after a normalization
  pass (not case-folded-split / encoded / base64 derived forms; that blind spot
  is stated, so the guarantee is honest).
  - `white-label`: **zero** hits anywhere.
  - `attributed`: hits allowed **only** inside the declared attribution surface.
- No dangling symlink (`CLAUDE.md` is a real file).
- Target `install-defaults.toml` `source` is blank/absent.
- All writes went through `agentbundle.safety.write_jailed`; the target path was
  validated (non-empty, not overlapping the running repo).
