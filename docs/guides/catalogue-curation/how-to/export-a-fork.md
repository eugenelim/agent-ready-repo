# Export a white-label or domain fork

**Use this when:** You want to produce a redistributable white-label or attributed derivative of the catalogue for an org rebrand or domain re-purpose.
**Prerequisites:** The `export-catalogue` skill available; a target path outside this repo; identity anchors (URL, email, slug, owner) ready for substitution.
**Result:** A verified catalogue copy at the target path with upstream identity stripped or credited, fail-closed against any surviving upstream trace.

`export-catalogue` produces a redistributable derivative of the catalogue at a
target path — for an organization rebrand, or to re-purpose the machinery into a
different domain (a creative-writing or investment-research catalogue). One
mechanism, two modes.

## Pick a mode

- **`white-label`** (default) — strip *all* upstream identity; zero trace. For a
  private/org fork or anything that must not disclose where it came from.
- **`attributed`** — strip governance and colliding branding, but keep a declared
  credit block naming the upstream. Use this for a *public* derivative you want
  to tie back to the origin, to grow the ecosystem.

> Export a white-label copy of this catalogue to `../our-fork`.

## What it does

1. **Validates the target** (non-empty, not nested in this repo) and jails every
   write.
2. **Strips** catalogue governance (RFCs/ADRs/specs/backlog), the repo's own
   charter/conventions, the internal doc site, and build/scan tooling — in
   **both** modes.
3. **Substitutes** the four identity anchors (URL, email, slug, owner) from *this*
   catalogue's own markers, so the tooling carries no hardcoded upstream literal.
4. **Chooses the include-set** — which packs travel. Drop the SDLC packs for a
   creative-writing catalogue; always keep the engine, a `core`, and
   `catalogue-curation` itself so the fork can curate itself.
5. **Persists the fork's own defaults** — its default adapter and self-host set —
   into the target copy, so every future user of the fork inherits them. After
   export, add `[organization].preferred_adapter` to `_data/install-defaults.toml`
   in the fork's packaged wheel to set a default adapter for every developer who
   installs from your fork — no `--adapter` or personal `agentbundle config set`
   required (see [Org adapter default](../../_shared/reference/agentbundle.md#org-adapter-default)).
6. **Verifies, fail-closed** — greps the target for any surviving upstream
   identity (case-insensitive, text files, declared literals). In white-label
   mode a single hit **hard-fails the export**; in attributed mode a hit is
   allowed only inside the declared credit block. Omit, never leak.

## After the first export

The fork is a catalogue in its own right — it has `catalogue-curation`, so it can
assimilate, propose packs, and even re-export. To pull later upstream changes,
run `assimilate-repo` in the fork pointed at its upstream; the same strip rules
keep governance and internal docs out.

For the full transform manifest (strip globs, anchor sources, verify bounds),
see [The ledger and the engine guard](../reference/ledger-and-guard.md) and the
skill's own `transform-manifest` reference.
