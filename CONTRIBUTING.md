# Contributing

Thanks for thinking about contributing. This catalogue grows by *primitives* — packs, skills, subagents — and each kind of contribution has a different shape. Pick the lane that fits your change.

## Before you start

Two reads will save you time:

- [`AGENTS.md`](AGENTS.md) — how this repo expects agents and contributors to work (the plan → execute → verify → review loop, what's in scope vs out, the non-negotiables).
- [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) — the single source of truth for *how we work in this repo*: document hierarchy, commit format, PR shape, and the [pack source-of-truth split](docs/CONVENTIONS.md#pack-source-of-truth-split) that every code change in this repo lives under.

One install: the artifact and skill-spec linters parse YAML via PyYAML. Run `pip install -r tools/requirements.txt` once. The linters also print an actionable install hint with exit code 2 if the import fails, so the first lint run will remind you.

If your change is substantive — new top-level directory, new contract surface, a CHARTER edit beyond a typo — open an [RFC](docs/rfc/) first. Typo fixes and small clarifications go straight to PR.

## The pack source-of-truth split

Every adapter-projected file in this repo has an upstream under `packs/<pack>/`. You edit the upstream; the build regenerates the projection. Direct edits to projected paths (`.claude/skills/<name>/SKILL.md`, `.claude/agents/<name>.md`, `tools/hooks/<name>.*`, the `hooks` key of `.claude/settings.local.json`, etc.) are caught by `make build-check` and bounced with the message naming the source path.

The muscle memory: edit the upstream, run `make build-self` (add `FORCE=1` if your tree is dirty), commit both the upstream and the regenerated projection in the same PR.

Full rule with the projected-paths list: [`CONVENTIONS.md § Pack source-of-truth split`](docs/CONVENTIONS.md#pack-source-of-truth-split).

## Three contribution lanes

### Adding a new pack

A new pack is a coherent slice — a workflow, a reviewer lens, a document shape — packaged as a unit. The ceremony exists because a pack adds public contract surface: a name in the catalogue, a row in the `Packs` table, an install URI adopters will pin against.

Steps:

1. **Open an RFC.** New packs need RFC review — the contract surface is published, not internal. See [`docs/rfc/`](docs/rfc/) for the template and recent precedents (RFC-0004 added install-scope-per-pack; RFC-0007 added the user-scope converter pack).
2. **Create `packs/<your-pack>/`** with the directory shape:
   - `pack.toml` — manifest. Conforms to [`docs/contracts/pack.schema.json`](docs/contracts/pack.schema.json). Required tables: `[pack]`, `[pack.adapter-contract]`, `[pack.install]`. Cross-field invariant `default-scope ∈ allowed-scopes` is schema-enforced.
   - `.apm/` — upstream for adapter-projected primitives (`skills/`, `agents/`, `hooks/`, `commands/`, `hook-wiring/`).
   - `seeds/` — upstream for seed-projected files (README, governance content). Files prefixed `_` are composition fragments, not standalone.
3. **Run the pack validator.** `agentbundle validate packs/<your-pack>`. Exit codes and the failure modes are in [`docs/guides/how-to/v01-to-v02-pack-upgrade.md`](docs/guides/how-to/v01-to-v02-pack-upgrade.md).
4. **If you claim `user` scope**, justify it. The user-scope eligibility test is the falsifiable check in the migration guide — content must be project-portable (no hooks that wire into a specific repo's surface, no seeds that name *this* project).
5. **Update the `Packs` table in [`README.md`](README.md)** and the catalogue manifest (`make build-self` regenerates the latter).

### Adding or modifying a skill

Skills in this catalogue follow the [agentskills.io specification](https://agentskills.io/specification) — each skill is a **self-contained folder** with `SKILL.md` plus optional `scripts/`, `references/`, `assets/`, and `evals/` subdirectories. Self-contained is non-negotiable: a skill must not import from another skill's folder, rely on globally-installed scripts the SKILL.md doesn't name, or assume files outside its own directory are present. The skill should copy, audit, and install as one unit. Skill changes are the most common contribution.

Steps:

1. **Pick the pack.** If your skill belongs in an existing pack, edit there. If it doesn't fit any pack and you don't want to create one, that's a signal — open an issue rather than wedging it in.
2. **Edit `packs/<pack>/.apm/skills/<name>/SKILL.md`** (upstream). Never edit the projection at `.claude/skills/<name>/SKILL.md`. Put any companion code under `scripts/`, fixed reference material under `references/`, binary or static assets under `assets/`, and evaluation fixtures under `evals/` per [agentskills.io § Directory layout](https://agentskills.io/specification).
3. **Frontmatter contract.** The closed top-level key set is `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools` — anything else belongs nested under `metadata:`. `name` is kebab-case (`^[a-z0-9]+(-[a-z0-9]+)*$`, 1–64 chars). The linter at `tools/lint-skill-spec.py` enforces both rules; canonical shapes live in `packs/core/.apm/skills/work-loop/`, `new-spec/`, and `bug-fix/`.
4. **For credentialed skills** (calls an authenticated external API on the user's behalf), follow the how-to [`docs/guides/how-to/add-a-credentialed-skill.md`](docs/guides/how-to/add-a-credentialed-skill.md) — the security rules around credential handling are non-negotiable; [`packs/atlassian/.apm/skills/jira/`](packs/atlassian/.apm/skills/jira/) is a runnable reference consumer.
5. **Evaluate, if behavior is non-trivial.** Drop fixtures under `evals/files/<fixture>` and the manifest at `evals/evals.json` per [agentskills.io § Evaluating skills](https://agentskills.io/skill-creation/evaluating-skills). The linter's directory-layout check exempts `evals/` from the depth rule that applies to `scripts/`, `references/`, and `assets/`.
6. **Run `make build-self`**, commit upstream + projection together.

### Adding or modifying a subagent

A subagent is a sharp diff-review or execution lens — currently four: `adversarial-reviewer`, `security-reviewer`, `quality-engineer`, `implementer`. The bar to add a fifth is high: a new lens needs a differentiable role the existing four don't cover, with reviewer findings that wouldn't have surfaced otherwise.

Steps:

1. **Pressure-test the addition.** A subagent earns its slot by catching something the existing reviewers miss, at a frequency that justifies the runtime. If you can't name two concrete bugs the proposed lens would have caught in the last quarter of PRs, the answer is probably "extend an existing reviewer's prompt" instead of "add a new agent."
2. **Edit `packs/<pack>/.apm/agents/<name>.md`** (upstream — typically `packs/core/`). Never edit `.claude/agents/<name>.md`.
3. **Frontmatter contract.** Required: `name`, `description`. Recommended: `tools`, `model`. The description's first sentence is what other agents see when picking a reviewer, so make it differentiable in one line.
4. **Run `make build-self`**, commit upstream + projection.

## Before you open the PR

Three gates, all of which run locally:

- **`make build-self`** — regenerates every projected path from its upstream. Catches drift.
- **`make build-check`** — fails if any projected path was edited directly without the upstream moving. Run this *after* `build-self` to confirm the tree is clean.
- **`conventions-check`** — the agent-artifact and conventions linter (also runs via the `pre-pr` hook). Available as a slash command in the core pack.

Commit format is Conventional Commits — full rules in [`CONVENTIONS.md § Commits`](docs/CONVENTIONS.md#commits). If your commit implements a spec, RFC, or ADR, cite it in the footer (`Spec:`, `RFC:`, `ADR:`).

## Where to find authoritative information

| You want to know… | Look here |
| --- | --- |
| Mission, scope, principles | [`docs/CHARTER.md`](docs/CHARTER.md) |
| How we work, document hierarchy | [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) |
| Why we chose X over Y | [`docs/adr/`](docs/adr/) |
| In-flight proposals | [`docs/rfc/`](docs/rfc/) |
| Per-IDE adapter contract | [`docs/contracts/adapter.toml`](docs/contracts/adapter.toml) |
| Pack manifest schema | [`docs/contracts/pack.schema.json`](docs/contracts/pack.schema.json) |
| Catalogue model rationale | [RFC-0001](docs/rfc/0001-bundle-distribution-by-adapter-spec.md) |

## When this file is wrong

Flag the drift in your PR rather than working around it. Substantive changes to this file go through RFC; small fixes are normal PRs.

## License

Contributions are dual-licensed under MIT and Apache 2.0 — the same terms as the catalogue itself. By opening a PR you agree to those terms unless you state otherwise.
