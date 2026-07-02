# ADR-0049: Catalogue runtime inventory — derive live, persist nothing, touch no Claude manifest

- **Status:** Accepted
- **Date:** 2026-07-02
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0060](../rfc/0060-catalogue-runtime-inventory.md), [ADR-0021](0021-pack-manifest-source-of-truth-and-scoped-identity.md), [`docs/specs/catalogue-runtime-inventory/`](../specs/catalogue-runtime-inventory/spec.md)

## Decision summary

- **Decision:** `agentbundle` answers "what skills and agents does pack X contain?" by walking the pack's `.apm/` tree at call time; it persists no inventory and touches no manifest.
- **Because:** deriving live is drift-free by construction and needs no schema or format change.
- **Applies to:** the pack inventory (skill + agent enumeration) surfaced by the CLI — not the pack metadata that already lives in `pack.toml`.
- **Tradeoff accepted:** a not-installed pack yields nothing when the catalogue is unresolvable — there is no source to read.
- **Revisit if:** a second consumer needs the inventory offline for a *not-installed* pack (which would justify persisting it), or a pack ships a skill or agent outside the uniform `.apm/skills/<name>/SKILL.md` / `.apm/agents/<name>.md` layout so the walk under-reports (a `show`-vs-`ls` mismatch surfaces it).

## Context

The catalogue holds a set of packs, each a directory of skills
(`<pack>/.apm/skills/<name>/SKILL.md`) and agents (`<pack>/.apm/agents/<name>.md`).
Nothing surfaces that inventory today: `list-packs` shows name/version/description/
dependencies, `list-installed` shows install rows, and the one field that *looks*
like an answer — `pack.toml`'s `[pack.evals].skills` — is an eval-coverage
allowlist that undercounts on purpose (`core` lists 5 there but ships 9). To learn
what a pack contains you must `ls` its directories.

RFC-0060 (Accepted) asked where that inventory should come from and how the CLI
should show it, without inventing a new format or fighting the Claude plugin
consumer. Two surfaces that could carry the inventory are wrong for it, and the
constraints are load-bearing:

- The `skills`/`agents` arrays in `plugin.json` / `marketplace.json` are, in the
  Claude Code consumer, **functional load-paths** — "custom paths to skill
  directories / agent files" that *add to* the default directory scan — not a
  descriptive name list. A bare-name inventory placed there is read as paths, not
  found, and silently ignored. This surface is also the one ADR-0021 D2 rules
  "not ours to own."
- `pack.toml` could hold a build-derived inventory field, but that means a schema
  change (`pack.schema.json`) plus a drift gate to keep it honest against the tree.

## Decision

**The pack inventory is derived live from the directory tree on each call; nothing
is persisted, and no manifest the Claude consumer reads is touched.**

Concretely:

- `agentbundle show <pack>` resolves the pack in the active catalogue and walks its
  authoritative `.apm/` source tree, enumerating skills
  (`.apm/skills/<name>/SKILL.md` → `<name>`) and agents (`.apm/agents/<name>.md` →
  `<name>`) as the full, untagged inventory, alongside the metadata `list-packs`
  already reads from `pack.toml`.
- The enumeration is recomputed on every invocation, so it cannot drift from the
  tree. Nothing is written to `pack.toml`, `plugin.json`, or `marketplace.json`,
  and no schema (`pack.schema.json`, `plugin-manifest.schema.json`, or its
  `.derived` variant) changes.
- **Read source with an honest, state-differentiated degrade.** The catalogue
  source tree is the authoritative primary. On an unresolvable catalogue the
  behavior differs by pack state and says so: an *installed* pack falls back to its
  own install-state rows (`State.rows_for_pack(<pack>)` → each row's
  `PackState.files`, unioned across adapters — not the whole-catalogue
  `State.projected_paths()` aggregate), which record every projected skill/agent
  path and so recover the inventory offline (marked as derived-from-installed-state);
  a *not-installed* pack has no source to read, so the command prints a one-line
  error and exits non-zero. This ADR does not claim
  parity with `list-installed`'s softer, state-backed degrade — `list-installed`
  has a read-only-state primary for its rows; `show` does not for a not-installed
  pack.

This decision governs the *inventory* only. It leaves ADR-0021's model intact:
`pack.toml` remains the single rich source of truth for pack *metadata*, projected
lossily per tool. The inventory is a third thing — neither stored in `pack.toml`
nor projected into a manifest, but computed from the primitive tree that is already
the source of truth for what a pack *contains*.

## Decision drivers

- **Zero drift.** The answer must never disagree with what the pack actually ships.
- **No schema or format change.** Avoid a `pack.toml` field plus its drift gate,
  and avoid inventing a new file.
- **Respect ADR-0021's projection posture.** Do not write into, or take ownership
  of, the Claude-format manifests.
- **Follow package-manager prior art.** Cargo/npm/pip keep metadata in the manifest
  and *render* a package's contents on demand (`cargo show`, `npm view`,
  `pip show`); none re-encode a package's file listing into a second stored index
  for display.

## Consequences

**Positive:**
- The inventory cannot drift — it is the tree, read at call time.
- No schema change, no new format, no drift gate to maintain, no manifest touched.
- Consistent with ADR-0021 and with how mainstream package managers separate stored
  truth from on-demand presentation.
- An installed pack stays introspectable offline via the state-file fallback.

**Negative:**
- A *not-installed* pack yields nothing when the catalogue is unresolvable — there
  is no source to read, so `show` errors and exits non-zero rather than degrading
  softly.
- The inventory is recomputed each call rather than cached (negligible for a
  directory walk over tens of entries).
- One more command to document and maintain on the CLI surface.

**Revisit if:** a second consumer needs the inventory offline for a *not-installed* pack (which would justify persisting it), or a pack ships a skill or agent outside the uniform `.apm/skills/<name>/SKILL.md` / `.apm/agents/<name>.md` layout so the walk under-reports (a `show`-vs-`ls` mismatch surfaces it).

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** the implementing diff adds a read-only walk — no write call
  (`open(..., "w")`, `.write_text`, `json.dump`, or a TOML dump) targets
  `pack.toml`, `plugin.json`, `marketplace.json`, or any `*.schema.json`, and no
  new persisted inventory file is added. The one non-CLI edit is rewiring a single
  `build/lint_packs.py` call site to the shared walk (behavior-preserving). A
  reviewer greps the diff for writes to those paths and confirms there are none.
- **Owner:** eugenelim

## Alternatives considered

- **Persist in `plugin.json` / `marketplace.json`.** Rejected against *respect
  ADR-0021's projection posture* and *zero drift*: those fields are functional
  load-paths (a name inventory is silently ignored), and the surface is ADR-0021 D2
  "not ours to own."
- **Persist in `pack.toml` (build-derived, drift-gated).** Rejected against *no
  schema or format change*: it is ADR-0021-aligned and offline-queryable, but needs
  a `pack.schema.json` change plus a drift gate — avoidable cost for a value the
  live walk delivers without it.
- **Do nothing (`ls .apm/skills/` by hand).** Rejected: the missing first-class
  answer is the whole motivation.

## References

- RFC-0060 (the accepted proposal, with the full options matrix and the
  de-risk result that the Claude-manifest arrays are functional paths).
- ADR-0021 (metadata source of truth + lossy per-tool projection; D2 "not ours to
  own").
- [Create and distribute a plugin marketplace — Claude Code Docs](https://code.claude.com/docs/en/plugin-marketplaces)
  (the `skills`/`agents` fields are paths that *add to* the default directory scan).
- Prior art: [`npm view`](https://docs.npmjs.com/cli/v11/commands/npm-view/),
  [`brew info`](https://docs.brew.sh/Manpage), `pip show`, `cargo show` — the
  universal per-package inspect verb, rendering contents on demand.
