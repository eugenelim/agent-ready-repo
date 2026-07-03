# Plan: catalogue-runtime-inventory

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Add one subcommand (`agentbundle show <pack>`) and one small pure helper to the
`agentbundle` CLI. The helper walks a pack's `.apm/` tree and returns its sorted
skill and agent names; the command resolves the pack in the active catalogue,
calls the helper, and renders either a human-readable block or a JSON object.
The riskiest part is the catalogue-unresolvable degrade: an *installed* pack
recovers its inventory from the install state file's recorded projected paths,
while a *not-installed* pack errors cleanly — this branch mirrors
`list_installed`'s existing `CatalogueError` handling and must be honest about
which case it is (`source` = `catalogue` vs `installed-state`).

Order of operations: extract the shared walk primitive first (so both the new
command and the existing `lint_packs` consume one enumeration path), then build
the command's primary path, then the degrade branch, then the end-to-end +
no-persist verification. Testing is TDD for the pure walk and the command body
(exercised through `run()` against fixture trees), with a goal-based check for
the CLI surface and no-persist invariant and a manual end-to-end run of
`agentbundle show core`.

## Constraints

- **ADR-0049** — derive live, persist nothing, touch no Claude manifest; the
  state-file fallback is inventory-only and marked derived-from-installed-state.
- **ADR-0021** — `pack.toml` is the metadata source of truth; `marketplace.json`
  / `plugin.json` are not ours to own. The inventory is neither stored in
  `pack.toml` nor projected into a manifest.
- **RFC-0060** — the accepted proposal: the verb + `--format json`, D1–D4, and the
  degrade semantics.

## Construction tests

Most tests live under the tasks below. Cross-cutting:

- **Integration:** the degrade branch (T4) is exercised through the command's
  `run()` with a fabricated `PackState`/install-state and an unresolvable
  catalogue URI — command + config-state together.
- **Manual verification:** run `agentbundle show core` and `agentbundle show core
  --format json` against the working-tree catalogue; record stdout + exit code
  (spec AC1/AC3/AC10). Pipe the JSON through a parser to confirm validity.

## Design (LLD)

Stack: the existing `agentbundle` CLI (Python, stdlib `argparse` + `pathlib`,
`tomllib` for `pack.toml`). No `docs/architecture/reference.md` in this repo, so
the design conforms to the established package structure (subparsers in `cli.py`,
`commands/<name>.py` bodies, `catalogue.py` / `config.py` primitives).

### Design decisions

- **Shared walk = raw enumeration primitive, not a semantic inventory.** The
  primitive returns sorted skill directories and sorted `agents/*.md` files; each
  caller applies its own filter. `lint_packs` lints every directory (SKILL.md or
  not); `show` counts only SKILL.md-bearing directories as skills. A shared *raw
  walk* keeps the directory traversal in one place without a behavior flag —
  avoiding the "add an option only when a second caller needs to differ" trap,
  because the two callers differ in the *filter*, not the *walk*. Concretely the
  primitive returns **raw sorted `Path` entries** (guarded by `is_dir()`), not
  names — so `lint_packs` keeps its full per-entry loop intact (it reads `SKILL.md`
  text, extracts frontmatter, and emits findings for `SKILL.md`-less directories,
  which `show` excludes). AC9's "enumeration lives in one place" is therefore the
  single guarded-`sorted(iterdir())` call the two callers share, not a semantic
  inventory both consume. Traces to: AC9 · none.
- **New neutral module `agentbundle/pack_inventory.py`.** `lint_packs` lives under
  `build/` and the command under `commands/`; a top-level pure module both import
  avoids a `build → commands` (or reverse) dependency. Alternative rejected:
  putting the helper in `commands/_common.py` (would make `build/` depend on
  `commands/`). Traces to: AC9 · none.
- **`source` field discriminates the two honest outcomes** (`catalogue` |
  `installed-state`) rather than a silent metadata gap. Traces to: AC3, AC6 · none.

### Interfaces & contracts

- **CLI verb:** `agentbundle show <pack> [--format {table,json}] [--root <path>]`.
  `<pack>` is a required positional (the pack name); `--format` defaults to `table`;
  `--root` (default `.`) locates the **repo-scope** install-state file for the
  degrade path, mirroring `list-installed`'s `--root`. Registered in `cli.py` next
  to `list-packs` via `subparsers.add_parser("show", ...)` +
  `sp.set_defaults(func=_lazy("show"))`.
- **JSON output shape** (`--format json`): a single object
  `{"name": str, "version": str|null, "description": str|null, "skills": [str],
  "agents": [str], "source": "catalogue"|"installed-state"}`, arrays sorted
  ascending. Traces to: AC3 · none.
- **Exit codes:** 0 success (primary or installed-state fallback); non-zero (1,
  mirroring `list-packs`) on unknown pack or unresolvable-catalogue-and-not-installed,
  with a one-line stderr message and empty stdout. Traces to: AC5, AC7 · none.

### Component / module decomposition

- **New** `agentbundle/pack_inventory.py` — pure walk primitive (skill dirs, agent
  files) + name-mapping helpers. New.
- **New** `agentbundle/commands/show.py` — `run(args)`: resolve catalogue → locate
  pack dir (`_discover_pack_dirs`) → enumerate → render; degrade branch on
  `CatalogueError`. New.
- **Changed** `agentbundle/cli.py` — register the `show` subparser.
- **Changed** `agentbundle/build/lint_packs.py` — consume the shared walk
  primitive (behavior-preserving).
- **Reused** `catalogue.py:resolve_catalogue`, `commands/_common` (URI resolution +
  table renderer), `config.py:State.has_pack` / `State.rows_for_pack` → per-adapter
  `PackState.files` (fallback source — *not* `State.projected_paths()`, which is a
  whole-catalogue aggregate).

### State & control flow

1. Resolve the catalogue URI (reuse `resolve_catalogue_uri` + `resolve_catalogue`).
2. On success: enumerate `_discover_pack_dirs`, then **name-match** — pick the dir
   whose `pack.toml` `[pack].name` (falling back to the dir name) equals `<pack>`;
   if none matches → one-line error, exit 1 (AC5). Else walk `.apm/`, read
   `pack.toml` metadata, render (`source: catalogue`), exit 0.
3. On `CatalogueError`: load install state from **both scopes** — repo
   (`<root>/.agentbundle-state.toml`) and user (`~/.agentbundle/state.toml` via
   `scope.resolve_user_root`; `UserScopeUnresolvable` → skip that scope) — exactly
   as `list-installed` gathers them. If `State.has_pack(<pack>)` in *either* scope
   → recover skill/agent names from the union of `State.rows_for_pack(<pack>)` rows'
   `PackState.files` across **all rows in both scopes** (deduped + sorted), render
   inventory-only (`source: installed-state`), exit 0. Else → one-line error, exit 1.

### Failure, edge cases & resilience

- Missing `.apm/skills/` or `.apm/agents/` → empty list, no crash (helper guards
  with `is_dir()`). Traces to: AC4.
- Projected-path parsing for the fallback runs over **every** adapter row of the
  pack in both scopes (`State.rows_for_pack`): **skill** name = the path segment
  immediately after a `skills/` component of a projected `SKILL.md` relpath (keys
  on the file, not the directory; layout-agnostic — spans `.claude/skills/`, the
  shared `.agents/skills/` (codex/copilot/cursor/gemini), and `.kiro/skills/`);
  **agent** name = the filename directly under an
  `agents/` component with its extension stripped by a single **extension-agnostic**
  rule — strip trailing `.agent.md` (copilot) if present, else `Path.stem`. This
  covers `.md` / `.toml` / `.json` / `.agent.md` without a hard-coded suffix list,
  so `claude` (`.md`) + `codex` (`.toml`) + `kiro` (`.json`) + `copilot`
  (`.agent.md`) rows dedupe to one entry per logical agent. Union across rows,
  dedupe + sort. The primary (catalogue) path stays authoritative — see Risks.
  Traces to: AC6.
- Unknown pack / not-installed-and-unresolvable → clean one-line stderr, non-zero
  exit, no stdout. Traces to: AC5, AC7.

### Quality attributes (NFRs)

- **Determinism:** all lists sorted ascending; output stable across runs (AC1–AC3).
- **No-persist:** the command has no write path; verified by a test asserting no
  files are written and by the diff excluding schema/manifest/`pack.toml` files
  (AC8).

## Tasks

### T1: Shared `.apm/` walk primitive

**Depends on:** none

**Touches:** packages/agentbundle/agentbundle/pack_inventory.py, packages/agentbundle/tests/*

**Tests:**
- Fixture pack tree → `skill_names(pack_dir)` returns the sorted names of
  subdirs of `.apm/skills/` that contain `SKILL.md` (spec AC2).
- A `.apm/skills/<dir>/` without a `SKILL.md` is excluded (spec AC2).
- `agent_names(pack_dir)` returns sorted stems of `.apm/agents/*.md`, ignoring
  non-`.md` entries and subdirectories (spec AC2).
- Missing `.apm/skills/` and missing `.apm/agents/` each return `[]`, no raise
  (spec AC4).

**Approach:**
- Add `agentbundle/pack_inventory.py` with the raw walk (sorted skill dirs,
  sorted `agents/*.md` files) and the `skill_names` / `agent_names` mappers.
- stdlib `pathlib` only.

**Done when:** the T1 tests are green and the module imports cleanly.

### T2: Route `lint_packs` through the shared primitive

**Depends on:** T1

**Touches:** packages/agentbundle/agentbundle/build/lint_packs.py

**Tests:**
- The existing `lint_packs` test suite stays green (behavior-preserving).
- A test asserts `pack_inventory` and the `lint_packs` walk enumerate an
  identical fixture identically (spec AC9).

**Approach:**
- Replace the inline `skills_dir.iterdir()` / `agents_dir.iterdir()` traversal in
  `_check_skill_metadata` / `_check_agent_metadata` with calls to the shared raw
  walk; keep lint's own per-entry filtering and findings unchanged.

**Done when:** the full `lint_packs` suite is green and enumeration lives in one
place (spec AC9).

### T3: `show` command — primary (catalogue) path

**Depends on:** T1

**Touches:** packages/agentbundle/agentbundle/commands/show.py, packages/agentbundle/agentbundle/cli.py

**Tests:**
- `run()` against a temp catalogue fixture: table output contains name, version,
  description, and sorted skills + agents; exit 0 (spec AC1).
- `show core` (working-tree catalogue) lists all skills under
  `packs/core/.apm/skills/`, not the `[pack.evals].skills` subset (spec AC2).
- `--format json` emits the exact-keys object with sorted arrays and
  `source: "catalogue"`; output parses as JSON (spec AC3).
- Unknown pack → one-line stderr, empty stdout, exit non-zero (spec AC5).
- `agentbundle show --help` exits 0 and documents `--format` (spec AC10).

**Approach:**
- Add `commands/show.py::run(args)` reusing `resolve_catalogue_uri`,
  `resolve_catalogue`, `_discover_pack_dirs`, `load_pack_toml`, and the shared
  table renderer. After `_discover_pack_dirs`, apply the **name-match** step
  (`[pack].name` or dir name == `<pack>`); no match → one-line stderr, exit 1 (AC5).
- Register the subparser in `cli.py` (positional `pack`, `--format` choices
  `table|json`, default `table`, `--root` default `.`) with `_lazy("show")`.

**Done when:** the T3 tests are green.

### T4: Catalogue-unresolvable degrade + state-file fallback

**Depends on:** T3

**Touches:** packages/agentbundle/agentbundle/commands/show.py, packages/agentbundle/tests/*

**Tests:**
- Unresolvable catalogue + installed pack (fabricated repo-scope state) →
  inventory-only result recovered from the pack's state rows, `source:
  "installed-state"`, `name` == the pack argument, version/description null/omitted,
  exit 0 (spec AC6).
- A pack installed under four adapters (`claude` `.md` + `codex` `.toml` + `kiro`
  `.json` + `copilot` `.agent.md` rows) → the union collapses to one entry per
  logical skill/agent, deduped and sorted — proving the extension-agnostic recovery
  across every registered agent extension (spec AC6).
- A pack installed only at **user scope** (state under the sandbox home) is still
  recovered — the fallback reads both scopes (spec AC6).
- Unresolvable catalogue + not-installed pack → empty stdout (also under
  `--format json`), one-line stderr, exit non-zero (spec AC7).

**Approach:**
- Wrap the resolve in the `CatalogueError` handler that mirrors `list_installed`;
  on catch, gather install state from **both scopes** (repo `<root>` + user via
  `scope.resolve_user_root`, `UserScopeUnresolvable` → skip), gate on
  `State.has_pack(<pack>)` in either, and recover names from the union of
  `State.rows_for_pack(<pack>)` rows' `PackState.files` across both scopes. Skill =
  segment after `skills/`; agent = filename under `agents/` with a trailing known
  suffix stripped (`.agent.md` before `.md`/`.toml`); dedupe + sort.

**Done when:** the T4 tests are green.

### T5: End-to-end + no-persist verification, changelog, README

**Depends on:** T3, T4

**Touches:** packages/agentbundle/README.md, docs/product/changelog.md, docs/specs/catalogue-runtime-inventory/spec.md

**Tests:**
- A test asserts a `show` run writes no files (spec AC8).
- Goal-based: `git diff --name-only` shows no `*.schema.json`, `pack.toml`,
  `plugin.json`, or `marketplace.json` in the diff (spec AC8).
- Manual QA: run `agentbundle show core` and `--format json` end-to-end; record
  observed stdout + exit code (spec AC10).

**Approach:**
- Add the `docs/product/changelog.md` `[Unreleased]` entry (new `show` command)
  and update the `agentbundle` PyPI README (`packages/agentbundle/README.md`) —
  both per RFC-0060's implementing-PR follow-ons.
- Flip the spec's ACs to `[x]` and Status to `Implementing` → `Shipped` as the
  build lands.

**Done when:** the real command runs green end-to-end, the no-persist checks
pass, and changelog + README are updated.

## Rollout

- **Delivery:** additive — a new subcommand. No flag, big-bang, fully reversible
  (removing it leaves no residue; nothing is persisted). No migration.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** none — ships whenever the next `agentbundle` release
  cuts (tag → PyPI). The changelog + README updates (T5) ride the same PR as the
  code.

## Risks

- **Projected-path parsing in the fallback (T4).** Different adapters project to
  different layouts (`.claude/`, `.codex/`, `.cursor/`, …). Keying on the `skills/`
  / `agents/` path components covers the common shapes, but an exotic layout could
  mis-parse. Mitigation: the catalogue path is authoritative; the fallback is a
  best-effort offline recovery, explicitly marked `source: installed-state`.
- **`lint_packs` refactor (T2).** AC9 (a single shared helper, both call sites
  through it) is **unconditional** — RFC-0060 mandates "enumeration lives in one
  place." The refactor must be behavior-preserving; the existing lint suite is the
  guard. If a behavior-preserving adoption proves impossible, that is a spec-level
  problem to surface to a human — and, only if AC9 must then ship unmet, it is
  flipped to `(deferred: <backlog-anchor>)` against a real `docs/backlog.md`
  heading per CONVENTIONS §4. It is never a de-scope the plan self-authorizes.

## Changelog

- 2026-07-02: initial plan (authored alongside spec + ADR-0049 on RFC-0060
  acceptance).
- 2026-07-02: pre-EXECUTE adversarial review closed two Blockers + concerns before
  code — specified the fallback's per-adapter name recovery (strip `.agent.md` /
  `.toml`, dedupe), the two-scope install-state read (`--root` added for repo
  scope), the AC5/AC7 empty-stdout-under-`--format json` contract, `name` = the
  pack argument on the installed-state path, the AC8 grep-the-diff no-persist check,
  and the `_discover_pack_dirs` name-match step. No approach change; sharper
  contract.
- 2026-07-02: second review round — the fallback agent-name rule is now
  **extension-agnostic** (`Path.stem` with an `.agent.md` special-case) rather than
  an enumerated suffix list, so it covers kiro/kiro-cli `.json` agents too; skill
  recovery restated as keying on the projected `SKILL.md` file relpath across the
  `.claude/` / `.agents/` / `.github/` layouts.
