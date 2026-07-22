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
2. **Strip** (deny-by-default, both modes) — catalogue-governance-about-itself
   (`docs/rfc/`, `docs/adr/`, `docs/specs/`, `docs/backlog.md`), the repo's own
   working `CHARTER`/`CONVENTIONS`/`AGENTS.local.md`, the internal doc site, and
   build/scan/release tooling. Governance is stripped in **both** modes.
3. **Substitute** the four identity anchors from *this* catalogue's own sources
   (URL + slug + owner from `.adapt-discovery.toml`; email from `pack.toml`
   maintainer + git) — so the tooling carries no hardcoded upstream literal. URL
   and email are blanket-safe; slug and owner are path/glob-scoped (a bare-token
   blanket replace corrupts text).
4. **Choose the include-set** — which packs travel (drop SDLC packs for a
   creative-writing catalogue; always keep the engine, a `core`, and
   `catalogue-curation` itself so the fork can self-curate).
5. **Persist the fork's defaults** into the *target copy only* — `scope.py`
   `DEFAULT_ADAPTER`, `self-host.toml` `[recipe.adapters].targets` +
   `[recipe.packs].include`, and blank `install-defaults.toml` `source`. A
   bounded re-home transform on declared anchors of the *target*; it never
   touches this repo's engine, so it is not a D6 change.
6. **Verify, fail-closed.** Grep the target for surviving upstream **URL, email,
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
  re-home transform on the **target copy's** declared anchors (step 5) is the
  sanctioned exception, never a change to the running catalogue.
- Ship any upstream identity outside the attribution surface (white-label: none).
- Write outside `agentbundle.safety.write_jailed`, or to an unvalidated target.

_Depends on `core` + `governance-extras`. Repo-scope; not in any default profile._
