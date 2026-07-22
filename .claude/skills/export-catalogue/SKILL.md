---
name: export-catalogue
description: Use to produce a redistributable derivative of this catalogue at a target path — an organization rebrand or a domain re-purposing (a non-SDLC catalogue) — in white-label mode (zero upstream trace) or attributed mode (credit upstream, to grow a public ecosystem), with a fail-closed leak check. Triggers on "export a white-label copy", "make an unbranded fork", "produce a <domain> catalogue from this", "export an attributed derivative". Do NOT use to ingest units (use assimilate-primitive) or to add a pack (use propose-catalogue-pack).
metadata:
  boundaries: [filesystem_write]
---

# Skill: export-catalogue

Produce a **redistributable derivative** of this catalogue at a target path —
for an organization rebrand or a domain re-purposing — in one of two modes, with
a **fail-closed** leak check. One mechanism; the transform is three declared
lists + a gate. Full manifest:
[`references/transform-manifest.md`](references/transform-manifest.md).

## Modes

- **`white-label`** (default) — strip *all* upstream identity; zero trace. For
  private/org forks and anything that must not disclose provenance.
- **`attributed`** — strip governance + colliding branding, but keep a declared
  attribution-back credit (a `NOTICE`/README block). The ecosystem-growth lever:
  a public re-purposed catalogue credits its origin. Attribution lives **only**
  in the sanctioned notice surface.

## Procedure

1. **Validate the target.** The operator-supplied target path is non-empty and
   does not overlap/nest in the running repo tree; all writes go through
   `agentbundle.safety.write_jailed`.
2. **Choose the include-set** — which packs travel (drop SDLC packs for a
   creative-writing catalogue; always keep the engine, a `core`, and
   `catalogue-curation` itself so the fork can self-curate). Determines which
   seeds to plant (step 4) and which guides to stage (step 5).
3. **Strip** (deny-by-default, both modes) — copy the running-repo pack content
   while excluding: catalogue-governance (`docs/rfc/`, `docs/adr/`,
   `docs/specs/`, `docs/backlog.md`), the running repo's own
   `CHARTER`/`CONVENTIONS`/`AGENTS.local.md`, the internal doc site, and
   build/scan/release tooling. Strip runs on the running-repo content copy only;
   seeds (step 4) are planted fresh afterward and are not affected.
4. **Plant seeds.** For each projected tool (core, governance-extras) and any
   pack in the include-set with a `seeds/` directory, copy the seed tree to the
   target repo root. Establishes the scaffold the skills navigate: `AGENTS.md`,
   `workspace.toml`, `docs/CONVENTIONS.md`, `docs/architecture/`,
   `docs/knowledge/`, `docs/product/`, `docs/specs/`, `docs/adr/README.md`,
   `docs/rfc/README.md`. Seeds are read from the live pack source at export time
   — auto-syncs when the pack changes. The seed `docs/CHARTER.md` is a blank
   template; step 5 overwrites it immediately.
5. **Capture the fork's mission.** Elicit from the operator: "What is this fork
   for? One phrase, sentence, or path to a CHARTER.md file." Accept any of: a
   bare keyword (`PKM`, `legal`, `marketing`), a sentence, or a file path to an
   existing CHARTER.md — expand keywords to a one-sentence mission if needed.
   Write `docs/CHARTER.md` in the target, overwriting the seed template. This
   anchors all future `assimilate-repo` runs from within the fork.
6. **Stage transportable guides.** For each pack in the include-set, copy
   `docs/guides/<pack-name>/` into the target. Always include
   `docs/guides/_shared/`. Guides for packs outside the include-set are
   omitted (omit-not-leak). The four-anchor substitution pass in step 7 covers
   any identity references inside staged guide content.
7. **Substitute** the four identity anchors from *this* catalogue's own sources
   (URL + slug + owner from `.adapt-discovery.toml`; email from `pack.toml`
   maintainer + git) — so the tooling carries no hardcoded upstream literal. URL
   and email are blanket-safe (compound tokens; replace in all files). Slug and
   owner require two passes: (a) path/glob-scoped replace in `.toml`/`.json`
   source files; (b) code-block-safe replace in `.md` files — target command-line
   examples, quoted identifiers, and TOML snippets embedded in prose (e.g.
   `agentbundle install --pack X slug`, `catalogue = "slug"`, `/plugin add
   owner/slug`). A bare-text paragraph replace is still unsafe; scope to known
   identifier patterns. Substitution applies across all content: seeds, skill
   files, pack configs, and staged guides.
8. **Persist the fork's defaults** into the *target copy only* — `scope.py`
   `DEFAULT_ADAPTER`, `self-host.toml` `[recipe.adapters].targets` +
   `[recipe.packs].include`, and blank `install-defaults.toml` `source`. A
   bounded re-home transform on declared anchors of the *target*; it never
   touches this repo's engine, so it is not a D6 change.
9. **Project required tools into the target.** Copy core, governance-extras, and
   catalogue-curation (from this catalogue's `packs/<name>/.apm/skills/`) into
   the target's installed-skill directories (Claude Code and Agents skill trees).
   These travel as *local installed tools* — not as catalogue packs in the fork's
   own catalogue — so the fork can self-curate from day one without inheriting
   agent-ready-repo's pack catalogue. Apply the four-anchor substitution to any
   projected file that still carries upstream identity.
10. **Verify, fail-closed.** Grep the target for surviving upstream **URL, email,
    slug, and owner** (the same four anchors, so verify and substitute agree),
    **case-insensitively**, over **text files** (binary out of scope, declared),
    matching declared **literals only** after a normalization pass. In
    `white-label` mode: zero hits anywhere. In `attributed` mode: hits only inside
    the declared attribution surface. Also fail on a dangling `CLAUDE.md` symlink
    or a non-blank target `install-defaults.toml` source. Any hit **hard-fails the
    export** — omit-not-leak.

## Never do

- Write under this repo's `packages/agentbundle/**` or `packs/credential-brokers/**`
  (RFC-0059 D6). This refusal is scoped to *this* repo's engine tree; the bounded
  re-home transform on the **target copy's** declared anchors (step 8 persist) is the
  sanctioned exception, never a change to the running catalogue.
- Ship any upstream identity outside the attribution surface (white-label: none).
- Write outside `agentbundle.safety.write_jailed`, or to an unvalidated target.

_Depends on `core` + `governance-extras`. Repo-scope; not in any default profile._
