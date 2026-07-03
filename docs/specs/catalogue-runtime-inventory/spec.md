# Spec: catalogue-runtime-inventory

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0049, ADR-0021, RFC-0060
- **Contract:** none <!-- a CLI verb + a JSON output shape; not one of the recognized contract types (openapi/asyncapi/proto/graphql/jsonschema). The JSON shape is documented inline in Acceptance Criteria. -->
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer at the CLI — or an agent/tool consuming `agentbundle` output — can
ask "what skills and agents does pack X contain?" and get a truthful answer. The
new verb `agentbundle show <pack>` resolves the pack in the active catalogue,
walks its `.apm/` source tree at call time, and prints the pack's metadata
(name, version, description) alongside the full, sorted list of its skills and
agents. `--format json` emits the same as a stable object — including a `source` field
recording whether the answer came from the catalogue tree or the install-state
fallback — for programmatic consumers. The answer is derived live, so it cannot
drift from what the pack actually ships; nothing is persisted and no manifest is
touched. When the catalogue is unresolvable, an *installed* pack still yields its
inventory from the install state file (marked `source: installed-state`); a
not-installed pack fails with a clear one-line error rather than a crash.

## Boundaries

### Always do

- Derive the inventory live by walking `.apm/` on each call — recompute, never
  persist or cache.
- Reuse the existing helpers named in the plan (`resolve_catalogue`,
  `_discover_pack_dirs`, `State.rows_for_pack` / `PackState.files`, the shared
  table renderer) and mirror `list_installed`'s `CatalogueError` degrade pattern.
- Keep skill and agent lists sorted ascending and output deterministic across
  runs.

### Ask first

- Any change to `list-packs` or `list-installed` behavior or output — RFC-0060
  leaves both unchanged.
- Adding a cross-pack "everything at once" firehose (e.g. `list-packs
  --contents`) — a deferred non-goal.
- Tagging skills as user-invocable vs. reviewer-internal — a deferred non-goal;
  v1 is complete and untagged.

### Never do

- Never write the inventory to `pack.toml`, `plugin.json`, or `marketplace.json`,
  and never change any schema (`pack.schema.json`, `plugin-manifest.schema.json`,
  or its `.derived` variant).
- Never add a new third-party dependency — the walk is stdlib `pathlib`.
- Never filter the inventory — `show` reports what exists, not what a user can
  invoke.

## Testing Strategy

- **Enumeration + rendering (AC1–AC5):** TDD. The directory-walk helper is a pure
  function over a fixture pack tree; the command body is exercised through its
  `run()` entry point against a temp catalogue fixture, asserting on the observed
  stdout and exit code.
- **Degrade / fallback (AC6, AC7):** TDD, exercised through `run()` with a
  fabricated install-state file and an unresolvable catalogue URI — an
  integration-level test (command + config-state together), not a unit of the
  walk.
- **No-persist invariant (AC8):** goal-based check — assert the diff touches no
  schema/manifest/`pack.toml` file, and a test confirms a `show` run writes no
  files.
- **Shared helper (AC9):** TDD — `lint_packs`' existing tests stay green after the
  refactor, and a test asserts both call sites enumerate an identical fixture
  identically.
- **CLI surface + real invocation (AC10):** goal-based (`agentbundle show --help`
  exits 0 and documents `--format`) plus manual QA — run `agentbundle show core`
  and `agentbundle show core --format json` end-to-end and record the observed
  output (stdout + exit code) in the implementing PR's *How to verify* section (the
  real-artifact happy path the work-loop requires for a user-invoked CLI).

## Acceptance Criteria

- [x] `agentbundle show <pack>` against a resolvable catalogue exits 0 and prints
  a human-readable block containing the pack's name, version, and description, and
  its skills and agents, each list sorted ascending.
- [x] The skills list is every `<pack>/.apm/skills/<name>/` directory containing a
  `SKILL.md` (→ `<name>`); the agents list is every `<pack>/.apm/agents/<name>.md`
  file (→ `<name>`). The inventory is the full, untagged set: `show core` lists
  every skill present under `packs/core/.apm/skills/`, not the subset in
  `[pack.evals].skills`.
- [x] `--format json` emits a single JSON object on stdout with exactly the keys
  `name`, `version`, `description`, `skills`, `agents`, `source`; `skills` and
  `agents` are sorted arrays of strings; `source` is `"catalogue"` on the primary
  path. The output parses as valid JSON.
- [x] A pack with no `.apm/skills/` directory (or no `.apm/agents/` directory)
  shows an empty list for that kind and does not error.
- [x] `show <unknown-pack>` against a resolvable catalogue prints a one-line error
  to stderr, writes nothing to stdout, and exits non-zero — including under
  `--format json`, where stdout stays empty (a programmatic consumer distinguishes
  success from failure by the exit code, not by parsing an error object on stdout).
- [x] When the catalogue is unresolvable and `<pack>` is installed
  (`State.has_pack` in **either** the user or repo scope — the fallback reads both,
  mirroring `list-installed`, and unions across scopes as well as adapters), `show`
  recovers the inventory from the install state — the union of skill and agent
  names across **all** of the pack's adapter rows in both scopes
  (`State.rows_for_pack(<pack>)`, each row's `PackState.files`), deduped and sorted
  — and exits 0. Names are recovered from the projected relpaths **independent of
  adapter extension**: a **skill** is the path segment immediately after a `skills/`
  component of a projected `SKILL.md` relpath — the rule is layout-agnostic and
  spans every skill home (`.claude/skills/<n>/SKILL.md`, the shared
  `.agents/skills/<n>/SKILL.md` used by codex/copilot/cursor/gemini, and
  `.kiro/skills/<n>/SKILL.md` → `<n>`); an **agent** is the filename
  directly under an `agents/` component with its extension stripped by a single
  **extension-agnostic** rule — strip the trailing `.agent.md` (copilot's
  double-suffix) if present, else `Path.stem` (the single final extension). This
  recovers `<n>` uniformly across `.claude/agents/<n>.md`, `.codex/agents/<n>.toml`,
  `.kiro/agents/<n>.json`, and `.github/agents/<n>.agent.md` — never `<n>.agent` or
  `<n>.json` — so co-installed rows dedupe to a single entry. The result
  is marked derived-from-installed-state: JSON carries `source: "installed-state"`;
  the table prints a `source: installed-state (catalogue unavailable)` line and
  omits the version/description rows. `name` in the output is the pack argument
  passed to `show`; `version` and `description` are `null` in JSON — never
  fabricated from the install row's `installed_version` — and omitted from the table.
- [x] When the catalogue is unresolvable and `<pack>` is not installed (in neither
  scope), `show` prints a one-line error to stderr, writes nothing to stdout
  (including under `--format json`, same exit-code contract as the unknown-pack
  path), and exits non-zero.
- [x] `show` persists nothing and touches no manifest. Verified two ways: (a) a
  `show` run over a temp catalogue writes no files under the run root (runtime
  assertion); and (b) per ADR-0049's Confirmation signal, the implementing diff
  adds no write call (`open(..., "w")`, `.write_text`, `json.dump`, or a TOML dump)
  targeting — and changes no — `pack.schema.json`, `plugin-manifest*.schema.json`,
  `pack.toml`, `plugin.json`, or `marketplace.json` (goal-based grep of the diff).
- [x] The directory walk is a single shared helper; `build/lint_packs.py` and the
  `show` command both enumerate through it, and `lint_packs`' existing behavior is
  unchanged.
- [x] `agentbundle show --help` exits 0 and documents the verb and
  `--format {table,json}`; the verb is registered in `cli.py` alongside the other
  subcommands.

## Assumptions

- Technical: the `agentbundle` CLI is Python; subcommands register in `cli.py` via
  `subparsers.add_parser(...)` + `sp.set_defaults(func=_lazy("<name>"))`, and each
  command body lives in `commands/<name>.py` with a `run(args)` entry point
  (source: `packages/agentbundle/agentbundle/cli.py:192`, `commands/list_packs.py`).
- Technical: the cited helpers exist — `resolve_catalogue` (`catalogue.py:55`),
  `_discover_pack_dirs` (`list_packs.py:82`), the per-pack install-state accessors
  `State.has_pack` / `State.rows_for_pack` (`config.py:164,168`) reaching each row's
  `PackState.files` (`config.py:126`), and the skills/agents walk pattern
  (`build/lint_packs.py:281`) (source: repo grep, verified 2026-07-02). Note
  `State.projected_paths()` (`config.py:203`) is a whole-catalogue aggregate, not
  per-pack, so the fallback uses `rows_for_pack`, not `projected_paths`.
- Technical: pack layout is uniform — skills are `.apm/skills/<name>/SKILL.md`,
  agents are `.apm/agents/<name>.md` — across every pack in the catalogue (source:
  RFC-0060 key assumption 1; `lint_packs` walks exactly this shape).
- Technical: the Claude `skills`/`agents` manifest fields are functional
  load-paths, not a descriptive name inventory, so not populating them is correct
  (source: RFC-0060 Evidence; Claude Code plugin-marketplaces docs).
- Process: the design is fixed by RFC-0060 (D1–D4) and ADR-0049; the JSON key
  names and the fallback `source` marker were the two items RFC-0060 deferred to
  the spec stage and are decided here per its recommendation (source: RFC-0060
  Open questions; ADR-0049).
- Process: the `docs/product/changelog.md` `[Unreleased]` entry and the
  `agentbundle` PyPI README update land in the implementing PR, not this authoring
  PR (source: RFC-0060 Follow-on artifacts; `docs/CONVENTIONS.md` changelog rule).
- Product: the consumers are humans at the CLI (the table form) and agents/tools
  (the JSON form) (source: RFC-0060 Problem & goals).
