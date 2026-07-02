# Export transform manifest — three declared lists + a gate

The whole export is declarative: what to strip, what to substitute, what packs
travel — plus a fail-closed verify. No content-regex, no DSL, no engine. Every
anchor names its **source** in the *running* catalogue, so the tooling ships
with no hardcoded upstream literal (run here it resolves to this catalogue's
identity; run in a fork, to the fork's).

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

## 4. VERIFY (fail-closed, mode-aware) — hard-fails the export
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
