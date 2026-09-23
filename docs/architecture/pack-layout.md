# Pack layout

Every pack in this catalogue ships the same on-disk shape — the
bundler refuses anything that doesn't conform. This page maps each
directory and file to its role. The authoritative format spec lives in
[`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md);
contributor conventions on *what goes where* live in
[§ The source-of-truth split](#the-source-of-truth-split) below.

## The shape

A pack sits under `packs/<name>/` with this skeleton:

```
packs/<name>/
├── pack.toml                       # pack metadata, scope rules, contract version
├── .claude-plugin/
│   └── plugin.json                 # Claude Code plugin manifest (hand-authored)
├── .apm/                           # primitives — projected by the build pipeline
│   ├── skills/
│   │   └── <skill-name>/SKILL.md
│   ├── agents/
│   │   └── <agent-name>.md
│   ├── hooks/                      # hook bodies (executable code)
│   │   └── <name>.{py,sh}
│   ├── hook-wiring/                # bindings of bodies to events (TOML)
│   │   └── <event>.toml
│   └── commands/
│       └── <name>.md
├── tests/                          # implementation verification — NEVER projected
│   ├── skills/<skill-name>/
│   ├── hooks/
│   └── pack/
└── seeds/                          # Tier-1 governance seeds (projected to repo root)
    ├── AGENTS.md
    ├── _agents-footer.md
    ├── .gitignore
    └── docs/
        ├── CHARTER.md
        ├── README.md
        └── ...
```

**The pack directory is the ownership boundary; `.apm/` is the runtime export
boundary.** Everything under `.apm/` is projected into an installed agent
environment. `tests/` is owned by the pack and never projected — visible in a catalogue
archive (which walks `packs/**`), but the installer reads only `.apm/` and
`seeds/`, so it cannot reach an adopter's tree. Evals are not an exception to
this — they are skill-local content: `.apm/skills/<skill>/evals/`, projected
with the skill, because a fixture only means anything beside the skill it
exercises. A pack is the ownership and test-execution boundary; a skill is the
evaluation-fixture boundary. A test therefore never lives under `.apm/`, even where the current
installer would ignore its path; the separation is structural, not incidental.
The normative rules — tests vs. evals, fixture hygiene, dependency separation —
are in [`catalogue-authoring-standards.md` § 4](../../guides/_shared/reference/catalogue-authoring-standards.md#4-pack-layout),
which ships to adopters. This section describes only what the shape is.

**Every pack now follows it, and a lint says so.** `tools/lint-pack-test-boundary.py`
fails when test content appears under any pack's `.apm/`, and — separately and
positively — when it appears in a projected skill. It also refuses a skill test
directory that no runner names and that is not declared unrun with a reason, so
"which suites actually run" is answerable from the tree rather than from a spec
note that freezes when the spec ships. The second half exists because
inferring "no tests are installed" from "the installer ignores those paths" is
the reasoning that let the violation persist for as long as it did: an adapter
that copied `.apm/**` wholesale would break the inference without breaking a
test. `tools/test-lint-pack-test-boundary.py` is its self-test, falsified in both
directions. Both run in the `docs` workflow.

The lint lives in `tools/` rather than in a pack's test tree because behaviour
that reads every pack belongs to no pack — the rule § 4 states under
*Repository-root tests*. It is not in the engine's suite either: it reads the
repository's projected tree and its runner call sites, neither of which is
`agentbundle`'s to know about.

OKF authoring bundles, when present, live under a pack-owned `okf/<bundle>/`
root and are summarized only by the pre-release `agentbundle show <pack>
--format json` single-pack discovery response. They are excluded from
`list-packs`, marketplace projections, and `catalogue-index.json`; those
surfaces do not become OKF registries or cross-pack knowledge indexes. The
pre-release `compile-okf` authoring Skill projects canonical OKF source into
ordinary `.apm/skills/` router/procedure Skills and a pack-local
`.okf-generated.json` manifest; those generated files are replaceable compiler
output, not a new pack primitive or lifecycle state.

**One pytest process per skill test directory.** Two skills may each ship a
`render.py` and a `test_render.py`. Collected into one run, the duplicate *test*
basenames make pytest error out — loud, and easy to diagnose. The duplicate
*subject* module is the one to worry about: a `sys.path` sibling import binds one
skill's `render.py` for both suites and everything passes green.
`tools/lint-pack-test-boundary.py` checks both against the runner call sites, not
against the tree — overlapping basenames *across* directories are the expected
end state, so a lint keying on the tree would fail on a correct layout.

Every pack ships `pack.toml` (schema-enforced) and a hand-authored
`.claude-plugin/plugin.json` (build-convention-required — the bundler
reads it directly). Beyond that, two orthogonal axes shape the
contents:

- **Scope**, declared in `pack.toml`'s `[pack.install]`, governs where
  the projection lands (repo's working tree vs. user-scope root). The
  three scope rails in
  [`build/scope_rails.py`](../../packages/agentbundle/agentbundle/build/scope_rails.py)
  refuse `seeds/`, `.apm/hooks/`, and `.apm/hook-wiring/` on user-scope
  packs at build time.
- **Content shape**, declared by which directories are populated. The
  `core` pack is the only one with a full `.apm/` set (skills, agents,
  hooks, hook-wiring, commands); the other repo-only packs
  (`governance-extras`, `user-guide-diataxis`, `monorepo-extras`) ship
  `.apm/skills/` plus `seeds/` and nothing else. User-scope packs
  (`converters`, `atlassian`, `figma`, `contracts`) ship `.apm/skills/`
  only. A repo-only pack omitting `seeds/` or `.apm/hooks/` is fine —
  it just didn't need them.

## What each file does

### `pack.toml`

Pack metadata, declared scope shape, and the adapter-contract version
the pack targets. Three required tables:

- **`[pack]`** — required `name`, `version`, `description`. The build
  pipeline reads these and emits derived per-tool metadata into
  `dist/apm/<pack>/apm.yml` and
  `dist/claude-plugins/<pack>/.claude-plugin/plugin.json` — for user-capable
  packs only; the Claude-plugin route installs at user scope. `[pack]` also
  accepts optional rich metadata — `readme`, `display_name`,
  `license`, `categories` (≤5, soft vocabulary), `keywords` (≤5),
  `catalogue`, an opaque `[pack.metadata.<tool>]` table, plus the
  `[[pack.maintainers]]` array and the `[pack.links]` table
  (homepage/repository/documentation/changelog/issues/icon). The build
  projects the cleanly-mappable subset (author ← first maintainer,
  `category` ← `categories[0]`, `displayName`, plus
  license/keywords/homepage/repository) into the `plugin.json` /
  `marketplace.json` entry, and copies the pack's `README.md` into each
  route — see [`pack-manifest.md`](pack-manifest.md). Every enriched field
  is optional; a pack that omits them projects exactly as before.
- **`[pack.adapter-contract]`** — `version`, must reference a
  published contract version. A pack pins the minimum behavior it needs. The
  current version lives in [`contracts/adapter.toml`](../../contracts/adapter.toml).
- **`[pack.install]`** — `default-scope` ∈ `{repo, user}`,
  `allowed-scopes`, optional `user-scope-hooks`, and optional
  `allowed-adapters` (an array of user-scope-capable adapter names like
  `["claude-code", "kiro-ide",
  "codex"]`; declared order drives the greenfield fallback). The
  `default-scope ∈ allowed-scopes` invariant is enforced in
  [`_data/pack.schema.json`](../../packages/agentbundle/agentbundle/_data/pack.schema.json)'s
  `if`/`then`; the `allowed-adapters` array's shape is enforced in
  the schema, and the cross-field constraint (every entry both
  shipped and user-scope-capable) lives in the Python validator at
  [`commands/validate.py:_validate_allowed_adapters`](../../packages/agentbundle/agentbundle/commands/validate.py).
  [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md)
  locked the per-pack default-plus-allowance shape.

### `.claude-plugin/plugin.json`

Hand-authored Claude Code plugin manifest — Source category, never
projected. The build pipeline reads it directly when emitting the
`dist/claude-plugins/<pack>/.claude-plugin/plugin.json` projection.

### `.apm/` — primitives

The pack-authored primitives declared in the adapter contract
([`contracts/adapter.toml`](../../contracts/adapter.toml)):

| Primitive | On-disk path | Notes |
| --- | --- | --- |
| `skill` | `.apm/skills/<name>/SKILL.md` (+ optional `scripts/`, `references/`, `assets/`, `evals/`) | [agentskills.io](https://agentskills.io/specification)-compliant. `evals/` holds two authored source files: `eval_queries.json` (Tier-A activation evals) and/or `evals/evals.json` + `evals/files/<fixture>` (Tier-B output-quality evals). `references/` is normally prose an agent loads, but may also carry an authored machine-read block a sibling script parses — `work-loop`'s `policy-families.md` is the shipped case. |
| `agent` | `.apm/agents/<name>.md` | Frontmatter declares `name`, `description`, `tools`, `model`, and source-only `metadata` (stripped at the Claude Code projection seam); body is the system prompt. |
| `hook-body` | `.apm/hooks/<name>.{py,sh}` | The executable. The bundler projects to each harness's hook directory. |
| `hook-wiring` | `.apm/hook-wiring/<name>.toml` | Declarative binding of a body to an editor event. |
| `command` | `.apm/commands/<name>.md` | Slash-command primitive (Claude Code today; other harnesses degrade per the contract). |

Two shipped cases are worth naming because their ownership is easy to guess
wrong.

The **work-loop activation reminder** is a matched pair: portable
`UserPromptSubmit` hook wiring plus an input-free hook body. The body prints a
fixed reminder and reads no prompt, environment, file or network input —
classifying whether a change is trivial is `work-loop`'s job, not the hook's.
Keeping the hook inputless is what makes it portable across every harness that
takes the wiring.

The **`digital-experience-contract` reference** belongs to the
`frontend-engineering` pack, not core. Core delegates the whole
frontend-engineering skill to that pack, which is its sole canonical owner, and
the reference travels with it.

One pack-authored primitive, `kiro-ide-hook`, provides native Kiro IDE-event
hooks. Its source path is `.apm/kiro-ide-hooks/<name>.kiro.hook`; the
`kiro-ide` adapter projects it; every other adapter either declares it
`dropped` or omits it. The contract also declares `shared-libs`,
`adapter-root-bins`, and `user-libs` — pack-authored source paths under
`.apm/` that carry *no* per-adapter projection rules, because their
targets are the scope-fenced `<scope-root>/.agentbundle/` roots rather
than a per-adapter path.

### Generated: `.eval-workspace/` (run artifacts, not pack source)

When `agentbundle pack evals run` runs a pack's
Tier-A activation evals, it writes a repo-relative, **gitignored**
eval-workspace — distinct from the ephemeral temp dir the pack is *projected*
into for discovery:

```
.eval-workspace/<pack>/
└── iteration-<N>/                         # one per full eval-loop pass
    ├── <skill>/<query-id>/with_skill/run-<r>/outputs/   # captured model .result
    └── summary.json                       # bounded per-skill trigger_rate + pass counts
```

These are **run artifacts, not pack source** — authors never commit them (they
hold model output and change every run). The layout follows the agentskills.io
evaluating-skills convention and reserves slots a future Tier-B grading RFC
fills (`without_skill/`, per-run `timing.json` / `grading.json`, an
`iteration-<N>/benchmark.json`) without restructuring the Tier-A output.

### `seeds/`

Governance content the pack drops at the repo root on install. Every
file under `seeds/` is **Tier-1** under the
[file-safety contract](../../guides/_shared/explanation/file-safety-contract.md) —
collisions land as `*.upstream.<ext>` companions, never silent
overwrites. Typical contents: `AGENTS.md`, `docs/CHARTER.md`,
`docs/README.md`, quadrant READMEs.

A pack with `default-scope = "user"` cannot ship seeds at all — the
contract's user-scope seeds-rail (in
[`build/scope_rails.py:check_seeds`](../../packages/agentbundle/agentbundle/build/scope_rails.py))
refuses to build a user-scope pack that declares `seeds/`.

### `_agents-footer.md` (optional)

Managed-block content the build pipeline composes into the
per-instance AGENTS.md via the `composite-agents-md.toml` recipe.
Multiple packs' footers merge in recipe order; only present in packs
that contribute to the AGENTS.md managed block.

## How the bundler reads a pack

1. [`agentbundle/catalogue.py`](../../packages/agentbundle/agentbundle/catalogue.py)
   globs `packs/*/`, validates each `pack.toml` against
   `_data/pack.schema.json`, and rejects pack-internal name collisions
   before any adapter runs.
2. The build dispatcher reads
   [`contracts/adapter.toml`](../../contracts/adapter.toml) to learn
   which projection mode applies to each primitive per adapter.
3. [`build/adapters/`](../../packages/agentbundle/agentbundle/build/adapters/)
   projects `.apm/<primitive-type>/` into the per-tool output
   directory using the
   [`build/projections/`](../../packages/agentbundle/agentbundle/build/projections/)
   handlers.
4. [`build/recipes/`](../../packages/agentbundle/agentbundle/build/recipes/)
   sequences which adapter targets to run for which output route. See
   [`agentbundle.md`](agentbundle.md) for the seven canonical recipes
   and the phases they participate in.

## Where to read next

- [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md) —
  the authoritative format spec.
- [§ The source-of-truth split](#the-source-of-truth-split) —
  why `seeds/` and `.apm/` are separate roots, and the rules for
  authoring inside each.
- [`agentbundle.md`](agentbundle.md) — how the bundler reads this
  shape into `dist/<route>/<pack>/`.
- [`pack-catalogue.md`](../../guides/_shared/explanation/pack-catalogue.md) —
  the adopter-facing companion to this page.

## The source-of-truth split

Bundle content (skills, agents, hooks, commands, hook-wiring, and pack
seeds) lives under `packs/<pack>/`. The split is:

- `packs/<pack>/.apm/` — the upstream for every adapter-projected
  primitive. Sub-directories: `skills/`, `agents/`, `hooks/`,
  `commands/`, `hook-wiring/`.
- `packs/<pack>/seeds/` — the upstream for every seed-projected path
  (the README / template / governance content adopters install).
  Files whose names start with `_` (e.g. `_agents-footer.md`) are
  *composition fragments* — they live in seeds for adopter
  customization but are not projected as standalone files; they're
  consumed by composite recipes.

*Projected* paths under `make build-check`'s gate:
- Adapter-driven primitives: the adapter's skills, agents, commands, and local
  settings targets; the adapter contract owns their exact paths. `tools/hooks/<name>.<ext>`
  and the `hooks` settings key are also adapter-driven — but `tools/**` is in
  `EXCLUDED_PATTERNS`, which gates the drift comparison as well as seed
  projection, so no gate catches a hand edit to `tools/hooks/<name>.<ext>`.
  Edit the source anyway; the rule holds, the enforcement does not.
- Adapter-independent runtime primitives: `.agentbundle/bin/<name>.py` from
  `packs/<pack>/.apm/adapter-root-bins/`, and
  `.agentbundle/lib/<module>/` from the package source vendored through
  `packs/<pack>/.apm/user-libs/`. These rails share the self-host drift gate
  even though they are outside every adapter's native discovery tree.
- Seed-projected paths: `AGENT_RULES.md`,
  `docs/AGENTS.md`, `governance/manifest.example.yaml`, and the agent-rule
  files a pack seeds. (Other seed-projected paths from earlier
  phases — `docs/CHARTER.md`, `docs/README.md`, the seed READMEs under
  `docs/<area>/`,
  `workspace.toml`, and `packages/_example/` — were reclassified as
  *Manual* with placeholder seeds; adopters receive the placeholder on
  first install via brownfield rules and own their on-disk content
  thereafter. Membership is decided by `EXCLUDED_PATTERNS`, not by this
  list: a seed whose target it does not match stays Projected.)
- Aggregated: `.claude-plugin/marketplace.json` from the `.claude-plugin/plugin.json`
  of every pack whose `[pack.install] allowed-scopes` admits `user` — and that declares `[pack.adapter-contract] version`; a pack with no
  contract version resolves `repo` regardless of what `allowed-scopes` says. The
  Claude-plugin route installs at user scope, so a repo-scoped pack is not
  listed there — it installs with `agentbundle install`.
- Recreated: `CLAUDE.md → AGENTS.md` symlink.

The pipeline regenerates each from its `packs/*/` upstream; direct
edits to any *Projected* path are caught by `make build-check` and
bounced with a message naming the source path and regeneration
command. The pack source-of-truth split is the catalogue's
load-bearing convention; CI's drift gate enforces it.

The muscle memory: to change a *Projected* path's content, edit its
upstream under `packs/<pack>/.apm/` or `packs/<pack>/seeds/`, then run
`make build-self` (with `FORCE=1` if the working tree is dirty),
commit, push. The gate is the contract; the source-of-truth split is
the convention.

### Managed generated output

A *managed* tree is one a compiler owns end to end: it writes every file in it,
records each one in a manifest beside the pack, and refuses to proceed if the
tree holds anything the manifest does not list. `compile-okf` is the current
example — it owns `.apm/skills/<router>/` and records it in
`.okf-generated.json`.

The rules:

- **Author the source, never the output.** Edit the canonical input (for OKF,
  `packs/<pack>/okf/<bundle>/`) and recompile. A hand edit to managed output is
  detected as drift, not accepted as a change.
- **A managed directory may not hold unmanaged files.** The compiler refuses a
  directory containing files its manifest does not own, because it cannot tell
  your file from a stale one it should delete. Keep hand-authored content in a
  sibling directory the compiler does not own.
- **Check mode is the gate; write mode is the authoring step.** Check re-renders
  and compares against the committed bytes, so it verifies without needing to
  write. That matters on platforms where the confined write path is
  unavailable — check mode still proves the committed output is what that
  platform produces.
- **Retargeting output is a rename, not a deletion.** Pointing a bundle at a new
  output directory hands the old one back to its author only when the source is
  still declared and its target actually changed. Removing a source is a
  removal, and its former output stays managed until cleaned up.

Managed output is projected like any other pack content, so the muscle memory
above still applies: edit the source, run `make build-self`, commit both.

### Install scope is per-pack

Each pack declares its install **scope** — `repo` (project-local), `user`
(shared across every repo the adopter opens), or both — in
`pack.toml`'s `[pack.install]` table. The pack author picks the
dimension; adopters can override within the publisher's declared set
via `--scope`. The default landing for every pack we ship today is
`repo`; user-scope eligibility requires content portability — no hooks
wired into a specific repo's surface, no seeds that name a particular
project.

Portability also governs what shipped pack prose may cite. Pack material states
its rules **directly** rather than pointing at this catalogue's internal RFCs,
ADRs, or acceptance criteria, which mean nothing in an adopter's repository.
Two carve-outs stay valid: IETF RFC references, and illustrative examples drawn
from an adopter's own situation.

Only part of this is mechanically caught. The
[catalogue-leak guard](security.md#repository-local-catalogue-leak-guard)
matches three patterns in core skill Markdown — the catalogue name, and
`RFC-00NN` / `K-00NN` numbers. A citation of an internal ADR, or of a spec's
acceptance criteria, passes it. The rest of the rule is an authoring obligation. The schema enforces `default-scope ∈ allowed-scopes` so the
rule holds outside the CLI. `agentbundle install` re-runs the
contract-level user-scope rails (seeds / hooks / marker) against the
resolved pack content at install time, closing the
widen-after-publish gap.

