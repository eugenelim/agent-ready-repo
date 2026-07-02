# RFC-0059 notes — the strip / substitute / verify transform, distilled

A redacted, generalized distillation of the maintainer's hand-run white-label
migration playbook (repo-private, gitignored, never shipped). Its purpose here
is to make RFC-0059's claim — *the export transform is fully expressible
declaratively, no novel mechanism* — **checkable by a reviewer**. This brief is
governance-about-the-catalogue and is itself stripped from any export.

## The transform is three declared lists + one gate

### 1. STRIP (deny-by-default; mode-independent)
Path/glob globs, never regex over content. Removed in **both** `white-label`
and `attributed` modes — attribution never re-admits governance:

- Catalogue-governance-about-itself: `docs/rfc/`, `docs/adr/`, `docs/specs/`,
  `docs/backlog.md`.
- The repo's own working `docs/CHARTER.md`, `docs/CONVENTIONS.md`,
  `AGENTS.local.md`, `CONTRIBUTING.md`. (The *projected* CONVENTIONS template
  that ships to adopters via the self-host recipe is a different artifact and
  rides along with the recipe — keep that one.)
- Build/scan/release tooling: `Makefile`, `.snyk`, bandit config,
  `.github/workflows/release-*.yml`, `tools/*.sh`.
- In-code comments that cite an upstream RFC/ADR/spec number purely as
  provenance, when the cited doc is itself stripped. Keep any comment that
  explains *why the code does what it does*.

### 2. SUBSTITUTE (anchor → value; each anchor names its SOURCE and its SCOPE)

| Anchor | Source in the running catalogue | Scope | Blanket-safe? |
| --- | --- | --- | --- |
| Full repo URL (`https://github.com/<owner>/<slug>`, keep `/tree/…` `/blob/…` suffix) | `.adapt-discovery.toml [markers].repo-url` | any occurrence | **yes** (compound) |
| Full maintainer email | `pack.toml [[pack.maintainers]].email` + git config | any occurrence | **yes** (compound) |
| Slug (`<slug>`, e.g. the catalogue's own name) | `.adapt-discovery.toml [markers].project-name` | path/glob-scoped, **and coupled** to every `pack.toml catalogue =` field + test fixtures | **no** — bare-token blanket replace is unsafe; slug is a *contract value* |
| Owner (bare) | `.adapt-discovery.toml [markers].owner` | path/glob-scoped | **no** — bare-token blanket replace is unsafe |

There is **no email marker** in `.adapt-discovery.toml`; email is sourced from
the pack maintainer field / git config. Only the two **compound** anchors (full
URL, full email) are safe to replace anywhere; the slug and owner are bare
tokens and are replaced only in declared paths, because a blanket replace of a
bare token corrupts unrelated text.

Mechanical rewrites that ride along: `pip install <pkg>` → `pip install -e .`
(a fork is editable-only); a `CLAUDE.md` symlink → a real file with the resolved
`AGENTS.md` content.

### 2b. RE-HOME transforms (persisted fork defaults — target copy only)
Applied only to the export *target*, at these declared anchors, never to the
running catalogue's engine (so they don't trip the D6 guard):

| Anchor | Where | Effect |
| --- | --- | --- |
| `install-defaults.toml [defaults].source` | copied engine | **blanked** — fork never defaults to the upstream URL |
| `scope.py DEFAULT_ADAPTER` | copied engine | set to the fork's chosen default adapter (distribution-wide, "forever"; per-machine `config set adapter` still overrides at runtime) |
| `self-host.toml [recipe.adapters].targets` | copied recipe | which adapters the fork projects onto itself |
| `self-host.toml [recipe.packs].include` | copied recipe | which packs the fork self-hosts (= the include-set) |

These are the playbook's Module-1 (default-adapter lever) and Module-6
(self-host set) steps, promoted from hand-patched to declared export inputs.

### 3. INCLUDE-SET (operator choice — which packs travel)
Always keep: the engine, a `core` (or a lighter re-based core for a non-SDLC
catalogue), and `catalogue-curation` itself (so the fork can self-curate). Drop
any pack the derivative doesn't want (e.g. SDLC packs for a creative-writing
catalogue). This is the domain-repurposing lever.

### 4. VERIFY (fail-closed, mode-aware) — the gate that hard-fails the export
- `grep` the target for surviving upstream **URL**, **email**, **slug**, **owner**
  (all four substitute anchors) → in `white-label` mode: **zero** hits allowed
  anywhere; in `attributed` mode: hits allowed **only** inside the declared
  attribution notice surface. Owner is only scope-substituted but is verified
  everywhere, because it ships bare as `[[pack.maintainers]] name`.
- No dangling symlink (`CLAUDE.md` must be a real file).
- `install-defaults.toml` source is blank/absent (a fork must not default to the
  upstream catalogue URL).
- If full-slug substitution was chosen: the slug survives only in intentional
  keeps, and every `pack.toml catalogue =` + test fixture carries the new slug
  consistently (the contract coupling).

## Why this de-risks the RFC
Every step above is a declared list or a grep — no content-regex, no DSL, no
engine. The hand-run playbook has executed this transform before; promoting it
to `export-catalogue` changes *who runs it and how it's verified*, not *what the
transform is*. The one correction this brief makes over a naive reading: email
has no marker (source it from the maintainer field), and the slug is a
scoped/coupled anchor, not a blanket one.
