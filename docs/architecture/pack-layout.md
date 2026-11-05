# Pack layout

> Every pack under `packs/<name>/` has the same on-disk shape, and the bundler
> refuses anything that does not conform. The pack directory is the ownership
> boundary. `.apm/` and `seeds/` are the only projected trees: `.apm/` reaches
> installed agent runtimes, and `seeds/` reaches the repo root.

This page maps each directory and file to its role. The authoritative format
spec is [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md).
Contributor rules for what goes where are in
[§ The source-of-truth split](#the-source-of-truth-split).

## The shape

```
packs/<name>/
├── pack.toml                       # metadata, scope rules, contract version
├── .claude-plugin/plugin.json      # Claude Code plugin manifest (hand-authored)
├── .apm/                           # primitives, projected by the build
│   ├── skills/<skill>/SKILL.md     # + scripts/, references/, assets/, evals/
│   ├── agents/<agent>.md
│   ├── hooks/<name>.{py,sh}        # hook bodies
│   ├── hook-wiring/<event>.toml    # body-to-event bindings
│   ├── commands/<name>.md
│   ├── kiro-ide-hooks/<name>.kiro.hook
│   └── shared-libs/, adapter-root-bins/, user-libs/
├── okf/<bundle>/                   # OKF authoring source, never projected
├── .okf-generated.json             # compiler manifest, only where okf/ exists
├── tests/                          # implementation tests, never projected
└── seeds/                          # governance seeds, projected to the repo root
```

Which pack carries which directory is a property of the pack, not a rule:

- every pack ships `.apm/skills/`;
- eight packs also ship `.apm/agents/`;
- only `core` ships hooks, hook-wiring, commands, and `kiro-ide-hooks`;
- only `credential-brokers` ships `shared-libs` and `user-libs`;
- only `core` and `credential-brokers` ship `adapter-root-bins`;
- only `agent-skill-engineering`, `architect`, `core`, and the `_okf-pilot-*`
  pack ship `okf/` and `.okf-generated.json`;
- only `core`, `repo-governance`, and `monorepo-extras` ship `seeds/`.[^1]

## Boundaries

**`tests/` is owned by the pack and never projected.** A catalogue archive walks
`packs/**`, so tests are visible in an archive. The installer reads only `.apm/`
and `seeds/`, so tests cannot reach an adopter's tree.

A test never lives under
`.apm/`, even where the current installer would ignore the path, because an
adapter that copied `.apm/**` wholesale would otherwise ship it.

**Evals are skill-local content.** They live at `.apm/skills/<skill>/evals/` and
project with the skill, because a fixture means something only beside the skill
it exercises. A pack is the ownership and test-execution boundary.

A skill is
the evaluation-fixture boundary.

**One pytest process runs per skill test directory.** Two skills may each ship a
`render.py` and a `test_render.py`. In one run, duplicate test basenames make
pytest error.

A duplicate subject module is the silent failure: a `sys.path`
sibling import binds one skill's `render.py` for both suites and both pass.

`tools/lint-pack-test-boundary.py` enforces all of this against runner call
sites and not against the tree, because overlapping basenames across directories
are the correct end state. It fails in three cases:

- test content appears under any pack's `.apm/`;
- test content appears in a projected skill;
- a skill test directory is neither named by a runner nor declared unrun with a
  reason.

Its self-test `tools/test-lint-pack-test-boundary.py` is falsified in both
directions, and both run in the `docs` workflow. The lint lives in `tools/`
because behaviour that reads every pack belongs to no pack.[^2]

The normative rules for tests, evals, fixture hygiene, and dependency separation
are in
[`catalogue-authoring-standards.md` § 4](../../guides/_shared/reference/catalogue-authoring-standards.md#4-pack-layout),
which ships to adopters.

**OKF authoring bundles** live under a pack-owned `okf/<bundle>/` root. The
`agentbundle show <pack> --format json` summarises them. They are
excluded from `list-packs`, marketplace projections, and `catalogue-index.json`.

The `compile-okf` skill in `catalogue-curation` projects canonical OKF source into ordinary
`.apm/skills/` router and procedure skills and a pack-local `.okf-generated.json`
manifest. Those files are replaceable compiler output, not a pack primitive.

## `pack.toml` and `plugin.json`

`pack.toml` is schema-enforced and `.claude-plugin/plugin.json` is read directly
by the bundler. The schema requires `[pack]` with `name` and `version`. Two
tables shape installation:[^3]

- **`[pack.adapter-contract]`** carries `version`, the adapter-contract version
  the pack targets. A pack with no declaration, or with `0.1`, resolves to repo
  scope and ignores `[pack.install]`. The current contract version is in
  [`contracts/adapter.toml`](../../contracts/adapter.toml).
- **`[pack.install]`** carries `default-scope` (`repo` or `user`),
  `allowed-scopes`, optional `user-scope-hooks`, and optional `allowed-adapters`,
  the user-scope-capable adapters in fallback order. The schema enforces
  `default-scope ∈ allowed-scopes` and the array's shape. The Python validator
  enforces that every `allowed-adapters` entry is both shipped and
  user-scope-capable.
  [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md) fixed
  the default-plus-allowance shape.

The enriched metadata fields and how they project are in
[`pack-manifest.md`](pack-manifest.md).

## Primitives

The adapter contract declares the pack-authored primitives.[^4]

| Primitive | On-disk path | Notes |
| --- | --- | --- |
| `skill` | `.apm/skills/<name>/SKILL.md` + optional `scripts/`, `references/`, `assets/`, `evals/` | [agentskills.io](https://agentskills.io/specification)-compliant. `evals/` holds `eval_queries.json` (Tier-A activation) and `evals/evals.json` + `evals/files/<fixture>` (Tier-B output quality). `references/` may carry an authored machine-read block a sibling script parses |
| `agent` | `.apm/agents/<name>.md` | Frontmatter declares `name`, `description`, `tools`, `model`, and source-only `metadata`, stripped at the Claude Code projection seam. The body is the system prompt |
| `hook-body` | `.apm/hooks/<name>.{py,sh}` | The executable, projected to each harness's hook directory |
| `hook-wiring` | `.apm/hook-wiring/<name>.toml` | Declarative binding of a body to an editor event |
| `command` | `.apm/commands/<name>.md` | Slash command. Claude Code natively, other harnesses degrade per the contract |
| `kiro-ide-hook` | `.apm/kiro-ide-hooks/<name>.kiro.hook` | Native Kiro IDE event hook. The `kiro-ide` adapter projects it. Every other adapter declares it `dropped` or omits it |
| `shared-libs`, `adapter-root-bins`, `user-libs` | `.apm/<primitive>/` | Source paths with no per-adapter projection rules. Their targets are the scope-fenced `<scope-root>/.agentbundle/` roots |

Two shipped cases have ownership that is easy to guess wrong:

- The **work-loop activation reminder** is a matched pair: portable
  `UserPromptSubmit` hook wiring plus an input-free hook body. The body prints a
  fixed reminder and reads no prompt, environment, file, or network input, which
  keeps it portable across every harness that takes the wiring.
- The **`digital-experience-contract` reference** belongs to the
  `frontend-engineering` pack. Core delegates the whole frontend-engineering
  skill to that pack, and the reference travels with it.

### The flat `agent` file

An agent is one file, not a directory. The contract gives it no `references/`,
`scripts/`, or `assets/`, and no adapter projects a subdirectory under
`.apm/agents/`. Each adapter walks the directory's top-level files and emits one
flat output per agent: Markdown for most, a Codex `.toml`, a Kiro CLI `.json`.

Even the Markdown routes rewrite the frontmatter rather than copy the file.

An agent that reuses a skill's rubric therefore **inlines a copy** so that it
works standalone. Inlining is the self-contained baseline. Architect's
`design-reviewer` also reads `architect-review`'s `references/rubric-*.md` where
that skill is co-installed, and both Kiro adapters inject skill-resource paths
into the projected agent, because a Kiro custom agent does not inherit
`.kiro/skills` auto-discovery.

The inlined copy is kept in step by hand, guarded by
`packs/architect/tests/pack/test_design_reviewer_rubric_parity.py`. The guard
checks a hand-maintained token allowlist, so a reword that keeps a token as a
substring passes. `tests/roster/test_architect_design_reviewer_projection.py`
checks that a `design-reviewer*` path appears under each of architect's seven
`allowed-adapters`, and it compares no projected content with the source.[^8]

The read-only contract has no single shape across projections. `tools: Read,
Grep, Glob` is the source declaration. Cursor subagents have no per-agent tool
allowlist, so the Cursor projection drops `tools` and derives `readonly: true`
for a non-mutating agent.

The projection test searches for the substring
`readonly`, which `readonly: false` also satisfies.

## Generated: `.eval-workspace/`

`agentbundle pack evals run` writes Tier-A activation results to a
repo-relative, gitignored `.eval-workspace/`. It is distinct from the temporary
directory the pack is projected into for discovery.

```
.eval-workspace/<pack>/
└── iteration-<N>/
    ├── <skill>/<query-id>/with_skill/run-<r>/outputs/   # captured model result
    └── summary.json                                      # per-skill trigger_rate and pass counts
```

These are run artifacts, never pack source, and authors never commit them. The
layout follows the agentskills.io evaluating-skills convention and reserves
slots for Tier-B grading (`without_skill/`, per-run `timing.json` and
`grading.json`, `benchmark.json`) without restructuring the Tier-A output.

## `seeds/`

Seeds are governance content the pack drops at the repo root on install. Every
seed file is **Tier-1** under the
[file-safety contract](../../guides/_shared/explanation/file-safety-contract.md):
collisions land as `*.upstream.<ext>` companions, never silent overwrites.
Typical contents are `AGENTS.md`, `docs/CHARTER.md`, `docs/README.md`, and
quadrant READMEs.

A pack whose `allowed-scopes` includes `user` cannot ship a non-empty `seeds/`.
`check_seeds` in `build/scope_rails.py` refuses to build one. The same module
refuses `.apm/hooks/` and `.apm/hook-wiring/` on such a pack unless it sets
`[pack.install] user-scope-hooks = true`.

A seed file whose name starts with `_`, such as `_agents-footer.md`, is a
composition fragment. The `composite-agents-md.toml` recipe merges the footers of
every contributing pack, in recipe order, into the per-instance `AGENTS.md`
managed block. Fragments are not projected as standalone files.

## How the bundler reads a pack

1. [`agentbundle/catalogue.py`](../../packages/agentbundle/agentbundle/catalogue.py)
   globs `packs/*/`, validates each `pack.toml` against
   `_data/pack.schema.json`, and rejects pack-internal name collisions before any
   adapter runs.
2. The build dispatcher reads [`contracts/adapter.toml`](../../contracts/adapter.toml)
   to learn which projection mode applies to each primitive per adapter.
3. [`build/adapters/`](../../packages/agentbundle/agentbundle/build/adapters/)
   projects `.apm/<primitive>/` into the per-tool output directory using the
   [`build/projections/`](../../packages/agentbundle/agentbundle/build/projections/)
   handlers.
4. [`build/recipes/`](../../packages/agentbundle/agentbundle/build/recipes/)
   sequences which adapter targets run for which output route. See
   [`distribution-routes.md`](distribution-routes.md#2-build-dispatch-reads-the-contract-route-code-lives-in-three-modules).

## The source-of-truth split

Bundle content lives under `packs/<pack>/`. `.apm/` is the upstream for every
adapter-projected primitive. `seeds/` is the upstream for every seed-projected
path.

The pipeline regenerates each projected path from its upstream, and
`make build-check` rejects a direct edit with a message naming the source path and
the regeneration command. The split is the catalogue's load-bearing convention,
and the CI drift gate enforces it.[^5]

To change a projected path, edit its upstream, run `make build-self` (with
`FORCE=1` if the working tree is dirty), then commit and push.

| Category | Paths | Upstream |
| --- | --- | --- |
| Adapter-driven primitives | The adapter's skills, agents, commands, and local settings targets, with exact paths owned by the adapter contract | `.apm/<primitive>/` |
| Adapter-independent runtime primitives | `.agentbundle/bin/<name>.py` and `.agentbundle/lib/<module>/` | `.apm/adapter-root-bins/` and `.apm/user-libs/`. These rails share the self-host drift gate though they sit outside every adapter's discovery tree |
| Seed-projected | `docs/AGENTS.md`, `governance/manifest.example.yaml`, and the agent-rule files a pack seeds | `seeds/` |
| Aggregated | `.claude-plugin/marketplace.json` | Every user-capable pack's `plugin.json` |
| Recreated | The `CLAUDE.md → AGENTS.md` symlink | The pipeline |

`AGENT_RULES.md`, `docs/CHARTER.md`, `docs/README.md`, the seed READMEs under
`docs/<area>/` and `packages/_example/` are **Manual**
placeholders. Adopters receive the placeholder on first install and own the
content afterwards. `EXCLUDED_PATTERNS` decides membership, and a seed it does not
match stays Projected.

**One gap.** Hook bodies project to `tools/hooks/<name>.<ext>`, and the `hooks`
settings key is adapter-driven, but `tools/**` is in `EXCLUDED_PATTERNS`. That
list gates both seed projection and the drift comparison, so no gate catches a
hand edit to `tools/hooks/<name>.<ext>`.

Edit the source anyway. The rule holds
and the enforcement does not.

### Managed generated output

A *managed* tree is one a compiler owns end to end. The compiler writes every
file in it, records each in a manifest beside the pack, and refuses to proceed if
the tree holds anything the manifest does not list. `compile-okf` is the current
example: it owns `.apm/skills/<router>/` and records it in `.okf-generated.json`.

- **Author the source, never the output.** Edit the canonical input, for OKF
  `packs/<pack>/okf/<bundle>/`, and recompile. A hand edit to managed output is
  drift, not a change.
- **A managed directory may not hold unmanaged files.** The compiler cannot tell
  an authored file from a stale one it should delete, so it refuses. Keep
  hand-authored content in a sibling directory.
- **Check mode is the gate and write mode is the authoring step.** Check
  re-renders and compares against committed bytes, so it verifies without
  writing. That matters where the confined write path is unavailable.
- **Retargeting output is a rename, not a deletion.** Pointing a bundle at a new
  output directory hands the old one back to its author only when the source is
  still declared and its target changed. Removing a source is a removal, and its
  former output stays managed until cleaned up.

Managed output is projected like any other content: edit the source, run
`make build-self`, commit both.

## Install scope is per pack

Each pack declares `repo` (project-local), `user` (shared across every repo the
adopter opens), or both in `[pack.install]`. The author picks the dimension, and
adopters override within the declared set with `--scope`. Of the 23 packs shipped
(underscore-prefixed directories are authoring assets, not payload), 14 default to
`user` and 9 to `repo`.[^6]

User scope requires portable content: no hooks wired into a specific repo's
surface and no seeds that name a particular project. The schema holds
`default-scope ∈ allowed-scopes` only where `allowed-scopes` is declared, because
the array is optional and a `contains` constraint on an absent array is vacuous.
`agentbundle install` re-runs the user-scope rails (seeds, hooks, marker) against
the resolved pack content at install time, which closes the widen-after-publish
gap.

### Portability of shipped pack material

Shipped pack material states its rules directly. It does not cite this
catalogue's RFCs, ADRs, or acceptance criteria, and it does not send a reader to a
path only this repository has. A `tools/lint-*` script exists here and nowhere an
adopter can reach.

Hook bodies project into an adopter's own `tools/hooks/`, so
`tools/` as a whole is not catalogue-local. Two carve-outs stay valid: IETF RFC
references and illustrative examples drawn from an adopter's own situation.
[`packs/AGENTS.md`](../../packs/AGENTS.md) § *Shipped pack content carries no
internal-governance citations* states the rule.

Only part of it is mechanically caught. The catalogue-leak host checks in
`tools/catalogue/verify_host_checks.py` run two scans:

| Scan | Reach | Patterns |
| --- | --- | --- |
| `seeds/` | Every pack declaring `lint-seeds = true`, any file type | The catalogue name, `RFC-00NN` and `K-00NN` numbers, and a hand-listed set of catalogue spec slugs |
| `.apm/` | Core's `skills/` only, Markdown only | The catalogue name, `RFC-00NN`, and `K-00NN`, without the slug list |

Neither scan has a pattern for a `tools/` path, an internal ADR number, or an
acceptance criterion, and no scan reads `pack.toml`. Files under `packs/` outside
test trees still name `tools/lint-*` scripts in hook wiring, skill scripts, and a
`pack.toml`. Those are violations of the stated rule and nothing reports them.[^7]

## Where to read next

- [`pack-manifest.md`](pack-manifest.md): how `pack.toml` metadata projects into
  manifests.
- [`agentbundle.md`](agentbundle.md): how the bundler turns this shape into
  `dist/<route>/<pack>/`.
- [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md):
  the authoritative format spec.
- [`pack-catalogue.md`](../../guides/_shared/explanation/pack-catalogue.md): the
  adopter-facing companion.

[^1]: Directory inventory of `packs/*/.apm/` and `packs/*/seeds/` at the verified commit; `contracts/adapter.toml` (`[primitive.*]`).

[^2]: `tools/lint-pack-test-boundary.py`, `tools/test-lint-pack-test-boundary.py`, `.github/workflows/docs.yml`.

[^3]: `contracts/pack.schema.json`; `packages/agentbundle/agentbundle/commands/validate.py` (`_allowed_scopes`, `_validate_allowed_adapters`).

[^4]: `contracts/adapter.toml` (`[primitive.*]`).

[^5]: `Makefile` (`build-check`, `build-self`); `packages/agentbundle/agentbundle/build/self_host.py`.

[^6]: `packs/*/pack.toml` `[pack.install] default-scope`, counted over non-underscore pack directories.

[^7]: `tools/catalogue/verify_host_checks.py` (`_APM_PATTERNS`, `_SEED_PATTERNS`); `packages/agentbundle/agentbundle/catalogue_tooling/lint.py` (CAT-L029, opt-in via `lint-seeds`).

[^8]: `packs/architect/tests/pack/test_design_reviewer_rubric_parity.py`; `tests/roster/test_architect_design_reviewer_projection.py`.
