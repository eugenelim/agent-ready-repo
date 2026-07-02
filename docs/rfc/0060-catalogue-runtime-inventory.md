# RFC-0060: Catalogue runtime inventory

- **Status:** Open
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-02
- **Date closed:**
- **Decision weight:** light
- **Related:** [ADR-0021](../adr/0021-pack-manifest-source-of-truth-and-scoped-identity.md) (`pack.toml` is the metadata source of truth; `marketplace.json` is Anthropic's format, receiving only a *projection* — a one-directional, lossy copy of the subset it understands — this RFC deliberately does *not* extend that projection), [RFC-0031](0031-catalogue-package-manager-posture.md) (the catalogue's package-manager posture — how packs are versioned, resolved, and distributed), [`docs/specs/enriched-pack-manifest/`](../specs/enriched-pack-manifest/spec.md) (the spec that first projected `pack.toml` metadata into the manifests)

## Reviewer brief

- **Decision:** Give `agentbundle` a way to answer *"what skills and agents does this pack contain?"* — derived live from the pack's directory tree, with no persisted inventory and no schema change.
- **Recommended outcome:** accept.
- **Change if accepted:**
  - New CLI verb `agentbundle show <pack>` printing the pack's skills + agents (plus the metadata it already knows), with a `--format json` for tooling/agents.
  - The inventory is computed at call time by walking the pack's `.apm/skills/*/SKILL.md` and `.apm/agents/*.md`; when the catalogue is unresolvable, an *installed* pack falls back to the inventory recorded in its state file. Nothing is written to `pack.toml`, `plugin.json`, or `marketplace.json`.
  - No changes to any schema (`pack.schema.json`, `plugin-manifest.schema.json`, or `plugin-manifest.derived.schema.json`).
- **Affected surface:** `agentbundle` CLI only (one new subcommand + a small shared directory-walk helper). No pack files, no manifests, no build output.
- **Stakes:** reversible — an additive command; removing it later leaves no residue.
- **Review focus:** (1) that deriving live — rather than populating the existing manifest arrays — is the right call; (2) the read-source rule for *installed* packs (catalogue source tree as primary, state file as offline fallback).
- **Not in scope:** any per-skill **input/output contract** (what a skill consumes and the artifacts it produces) — a larger, separate concern, deferred; and any change to the `skills`/`agents` fields in `plugin.json`/`marketplace.json`.

## The ask

- **Recommendation (BLUF):** Add `agentbundle show <pack>`, which walks the pack's `.apm/` tree at runtime and lists its skills and agents (with `--format json` for programmatic consumers). Persist nothing; change no schema.
- **Why now (SCQA):**
  - *Situation.* The catalogue (the set of packs `agentbundle` can install, resolved from a git repo or a local `packs/` tree) holds a set of packs, each a directory of skills (`.apm/skills/<name>/SKILL.md` — the pack's authoring-source layout) and agents (`.apm/agents/<name>.md`).
  - *Complication.* Nothing surfaces that inventory. `list-packs` shows name/version/description/dependencies; `list-installed` shows install rows; `pack.toml`'s only `skills = […]` line lives under `[pack.evals]` and is an *eval-coverage allowlist*, not an inventory (e.g. `core` lists 5 there but ships 9). To learn what a pack contains you must `ls` its directories.
  - *Question.* Where should the inventory come from, and how should the CLI show it — without inventing a new format or fighting the Claude plugin consumer?
- **Decisions requested:**

  | ID | Question | Recommendation | Why | Decide by | Reviewer action |
  | --- | --- | --- | --- | --- | --- |
  | D1 | Persist the inventory, or derive it live? | **Derive live at runtime** from the directory tree | Zero drift by construction; no schema/format change; respects ADR-0021 | this review | Confirm live-derive over persistence |
  | D2 | What command surface, and what shape? | **New `agentbundle show <pack>` verb + `--format json`**; leave `list-packs`/`list-installed` unchanged | Matches the universal per-package inspect verb (`pip show`, `npm view`, `brew info`, `cargo show`); keeps the list tables lean | this review | Confirm the verb + JSON shape |
  | D3 | For an *installed* pack, read the catalogue or the installed projection? | **Catalogue source tree as the authoritative primary; installed state file as the offline fallback** | The `.apm/` source tree is the canonical shape; the state file's recorded projected paths recover the inventory when the catalogue is unresolvable | this review | Rule on read-source + fallback |
  | D4 | Enumerate reviewer-internal skills too? | **Yes — full inventory** | `show` reports what exists, not what a user can invoke; filtering would misrepresent the pack | this review | Confirm full inventory |

## Problem & goals

**Diagnosis.** The pack contents (skills, agents) exist only as filesystem structure. There is no first-class way — for a human at the CLI, or for an agent/tool consuming `agentbundle` output — to ask "what's inside pack X?" The one field that looks like an answer, `[pack.evals].skills`, is a coverage allowlist and undercounts on purpose (it excludes skills loaded by a workflow discipline rather than a user prompt, like `work-loop`, and skills only ever loaded by a reviewer subagent, like `security-checklists`). Reading it as an inventory is a documented trap.

Two surfaces that *could* have carried the inventory are wrong for it:

- **`plugin.json` / `marketplace.json` `skills`/`agents` arrays.** These fields exist and validate, but in the Claude Code consumer they are **functional load-paths** — "custom paths to skill directories / agent files" that *add to* the default directory scan — not a descriptive name list. A name inventory placed there is read as paths, not found, and silently ignored. It is also the surface ADR-0021 D2 explicitly rules "not ours to own."
- **`pack.toml`** could hold a build-derived inventory field, but that means a schema change plus a drift gate to keep it honest against the tree.

**Goals.**
- Answer "what skills and agents does pack X contain?" from `agentbundle`, for humans (table) and tools/agents (JSON).
- Zero risk of the answer drifting from reality.
- No new file format; no schema change; no change to any manifest the Claude consumer reads.

**Non-goals.**
- **Declaring per-skill inputs and artifact outputs.** A real capability with real value, but a larger design (no machine-readable contract exists today; at most a stray skill ships an `output.schema.json`). Deferred to a separate RFC so this one stays a clean, shippable inventory.
- **A cross-pack "everything at once" firehose** (e.g. `list-packs --contents`). Per-pack `show` is enough for v1; the firehose is additive later if wanted.
- **Tagging skills as user-invocable vs. reviewer-internal.** The inventory is complete and untagged in v1; a `kind` distinction can follow if a consumer needs it.

## Proposal

Add one subcommand and one shared helper to `agentbundle`.

**`agentbundle show <pack>`** — resolves the pack (in the active catalogue), walks its source tree, and prints:

- the pack's existing metadata (name, version, description — the fields `list-packs` already reads from `pack.toml`), and
- its **skills** (each `<pack>/.apm/skills/<name>/SKILL.md` → `<name>`) and **agents** (each `<pack>/.apm/agents/<name>.md` → `<name>`), sorted, full inventory.

Default output is a human-readable block mirroring `list-packs`' `render_table` conventions. `--format json` emits a stable object (`{name, version, description, skills: [...], agents: [...]}`) for agents and scripts — the "self-describing catalogue" payload.

**Read source (D3).** `show` resolves the catalogue with `resolve_catalogue` (`catalogue.py`), finds the pack directory within it via `_discover_pack_dirs` (`list_packs.py`), and walks that pack's authoritative `.apm/` source tree — the full, canonical inventory. On a `CatalogueError` (unresolvable catalogue) it does not crash. The degrade behavior differs by pack state, and honestly so:

- **Catalogue pack, catalogue unresolvable:** there is no source to read, so `show` prints a one-line error and exits non-zero. (This is *not* the softer degrade `list-installed` gives — `list-installed` sources its rows from the read-only state file and only consults the catalogue to enrich a secondary LATEST/STATUS column, so it still prints its primary rows; `show` has no such state-backed primary output for a not-installed pack. The RFC does not claim parity here.)
- **Installed pack, catalogue unresolvable:** `show` falls back to the **state file** — `PackState.files` / `projected_paths()` (`config.py`) records every installed *projected* path (`.claude/skills/<name>/…`, `.claude/agents/<name>.md`) with its SHA, so the installed pack's skill/agent names are recoverable without the catalogue. This fallback is inventory-only (no `pack.toml` metadata) and is marked as derived-from-installed-state in the output. It closes the otherwise-worst case (an installed pack you can't introspect offline).

**Shared helper.** The directory walk is a small pure function factored from the pattern already in `lint_packs.py` (`skills_dir.iterdir()` / `agents_dir.iterdir()`), so enumeration lives in one place.

**No persistence.** Nothing is written to `pack.toml`, `plugin.json`, or `marketplace.json`; neither `plugin-manifest.schema.json` nor its `plugin-manifest.derived.schema.json` variant, nor `pack.schema.json`, is touched. The inventory is recomputed on each call, so it cannot drift from the tree.

There is no migration: no existing state changes shape.

## Options considered

**Axis: where the inventory lives** (source of truth for the enumeration). This axis is exhaustive along a store-vs-compute branch: an inventory is either *stored* (and if stored, in one of the files that already describe a pack — the two Claude-format manifests, which share a row below because they share one rejection rationale, or `pack.toml`) or *computed on demand*; do-nothing is the baseline.

| Option | What it is | Trade-off | Verdict |
| --- | --- | --- | --- |
| Do-nothing | Keep `ls .apm/skills/` by hand | No cost; the gap stays | Rejected — the gap is the motivation |
| Persist in `plugin.json` / `marketplace.json` (one row: both are Claude-format projections rejected for the same two reasons) | Populate the existing `skills`/`agents` arrays at build time | Consumer-visible, *but* those fields are functional load-paths (name lists silently ignored), and ADR-0021 D2 forbids owning that surface | Rejected — semantically wrong + off-limits |
| Persist in `pack.toml` | Build-derived inventory field, drift-gated | ADR-0021-aligned, offline-queryable, *but* needs a schema change + a drift gate | Rejected — schema change is avoidable |
| **Derive live at runtime** ★ | CLI walks the `.apm/` tree on each call | Zero drift, no schema/format change, respects ADR-0021; needs the source tree resolvable at call time | **Recommended** |

Prior art grounds the choices: package managers split "storage of truth" from "presentation." Cargo/npm/pip keep metadata in the manifest and *render* it on demand (`cargo show`, `npm view`, `pip show`); none re-encode a package's file listing into a second stored index for display — they read it live. Deriving the inventory at display time follows that grain.

**Axis: command surface** (a secondary decision, once "derive live" is chosen): flags on the existing list commands, a dedicated per-pack verb, or both. The dedicated verb wins on prior-art grounds — every major package manager exposes a per-package inspect verb (`pip show`, `npm view --json`, `brew info`, `cargo show --json`) distinct from its "list packages" command. Keeping `list-packs`/`list-installed` lean (they answer "which packs") and adding `show` (answers "what's in one") mirrors that split. The cross-pack firehose is deferred (a non-goal).

## Risks & what would make this wrong

- **Pre-mortem — catalogue unresolvable at call time.** *Mitigation (installed pack):* fall back to the state file's recorded projected paths (D3), yielding an inventory-only result marked as derived-from-installed-state — never a crash. *Mitigation (not-installed pack):* no source exists to read, so `show` prints a clear one-line error and exits non-zero; the RFC does not claim this matches `list-installed`'s softer, state-backed degrade.
- **Pre-mortem — the SKILL.md `name:` frontmatter disagrees with its directory name.** The walk keys on the directory name; if a skill's frontmatter `name` differs, the two could diverge. *Mitigation:* directory name is what every projector already uses as the skill identity, so it is the correct key; a separate lint (not this RFC) already governs frontmatter/name consistency.
- **Key assumptions (falsifiable):**
  1. Every skill is a `<pack>/.apm/skills/<name>/SKILL.md`, and every agent a `<pack>/.apm/agents/<name>.md` — uniform across every pack in the catalogue. (Verified true today; if some future pack nests differently, the walk under-reports.)
  2. The Claude consumer's `skills`/`agents` fields are functional paths, not descriptive names — so *not* populating them is correct. (Verified against Anthropic's docs; see Evidence.)
- **Drawbacks.** The inventory is recomputed each call rather than cached — negligible for a directory walk over tens of entries. Full metadata + inventory needs the catalogue source tree; when it is unresolvable, an installed pack still yields an inventory from the state file, but a not-installed pack yields nothing. And it adds one more command to the CLI's surface to document and maintain. All accepted as the cost of zero drift and zero schema change.

## Evidence & prior art

- **Spike / de-risk result.** The riskiest assumption was that populating the existing `plugin.json`/`marketplace.json` `skills`/`agents` arrays would be a free win. **Tested against Anthropic's plugin-marketplaces documentation: false.** Those fields are defined as *"custom paths to skill directories / agent files"* that add to the default directory scan; a bare-name inventory is read as paths, not found, and ignored ("if none of the listed paths exist, the default scan runs instead"). This — plus ADR-0021 D2 ruling `marketplace.json` "not ours to own" — is why the RFC derives live and touches no manifest. Source: [Create and distribute a plugin marketplace — Claude Code Docs](https://code.claude.com/docs/en/plugin-marketplaces) (plugin-manifest schema table: `skills`/`agents` = paths that *add to* the default directory scan — the automatic loading of skills from a plugin's `skills/` directory — with "strict mode" governing whether the plugin's own manifest or the marketplace entry is authoritative for its components).
- **Repo precedent.**
  - `docs/adr/0021-...md` D2 — `pack.toml` is the rich source of truth; `marketplace.json`/`plugin.json` receive a lossy projection and are not ours to own. Directly supports "don't persist into the Claude formats."
  - `packages/agentbundle/agentbundle/catalogue.py` (`resolve_catalogue`) + `commands/list_packs.py` (`_discover_pack_dirs`, `_extract_row`, `_print_table`) + `commands/_common.py` (`render_table`, imported by `list_packs`) — the exact helpers `show` reuses to locate a pack and render it. The `CatalogueError`→degrade block in `list_installed.py` is the error-handling pattern to mirror (not `_resolve_latest`, which builds a whole-catalogue version map and does more than `show` needs).
  - `packages/agentbundle/agentbundle/config.py` (`PackState.files`, `projected_paths()`) — the state-backed fallback source for an installed pack when the catalogue is unresolvable (D3).
  - `packages/agentbundle/agentbundle/build/lint_packs.py` (`skills_dir.iterdir()` / `agents_dir.iterdir()`) — the directory-walk logic to factor into the shared helper.
  - `packs/*/pack.toml` `[pack.evals].skills` — the trap: an eval allowlist that undercounts (`core` lists 5, ships 9). `show` reads the tree, not this field.
- **External prior art.** The per-package inspect verb is universal: [`npm view`](https://docs.npmjs.com/cli/v11/commands/npm-view/) (JSON output + field queries), [`brew info`](https://docs.brew.sh/Manpage) (lists dependencies/contents), [`cargo show --json`](https://crates.io/crates/cargo-show) (self-described as "like `pip show`, `apt-cache show`, `npm view`, `gem query`"). All separate "inspect one package" from "list packages," and all offer a JSON mode for programmatic use — the shape adopted here.

## Open questions

- **JSON payload key names.** Recommended default: `{name, version, description, skills, agents}` (mirrors the `plugin-manifest` field names already in the repo, minus the persistence). Owner: eugenelim. Decide-by: at implementation (spec stage).

## Follow-on artifacts

Filled in on acceptance:

- ADR — record the "derive live, do not persist / do not touch the Claude manifests" decision (extends ADR-0021's projection posture).
- Spec: `docs/specs/catalogue-runtime-inventory/` — the `show` subcommand contract (flags, output shapes, degrade behavior, tests) built via `new-spec` → `work-loop`.
- A `docs/product/changelog.md` `[Unreleased]` entry (new user-facing CLI command) and an `agentbundle` PyPI README update, in the implementing PR.
- A separate future RFC for per-skill input/output contracts (the deferred non-goal).
