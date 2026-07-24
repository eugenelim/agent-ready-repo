# AGENTS.md — `packs/`

Context for working inside any pack directory. Loaded automatically when
the working path is under `packs/`. See the root `AGENTS.local.md` for
broader self-host context.

## Pack anatomy

Each pack directory contains:

| Path | Purpose |
|------|---------|
| `pack.toml` | Pack metadata — version, description, categories, keywords |
| `.claude-plugin/plugin.json` | Claude plugin manifest source (must match `pack.toml` version and stay schema-valid) |
| `.apm/skills/<name>/SKILL.md` | Skill source of truth — projected per adapter by `make build-self` |
| `.apm/agents/<name>.md` | Agent source of truth — projected per adapter |
| `.apm/commands/<name>.md` | Command source of truth — projected per adapter |
| `.apm/hooks/` | Hook source of truth — projected per adapter |
| `seeds/` | Adopter scaffold templates (brownfield install) |
| `README.md` | Pack documentation |

## Version bump rule

Every **non-cosmetic** change to pack content requires a version bump. This includes
changed skill bodies, new reference files, sharpened directives, reworded
conventions, and new skills or agents. **Cosmetic-only** changes (typos,
whitespace, comment reflow with no semantic effect) need no bump.

Two files must always move together:

1. `packs/<pack>/pack.toml` → `[pack] version`
2. `packs/<pack>/.claude-plugin/plugin.json` → `"version"`

**Which increment to take:**
- Patch (`x.y.Z`) — improved skill body, added directive, reworded convention; no new primitives.
- Minor (`x.Y.0`) — new skill, new agent, new command; additive but no removal.
- Major (`X.0.0`) — removed or renamed primitive; breaking change for installed adopters.

Take the **next increment from the current `pack.toml`** — never ride an unreleased
version from another in-flight PR. Two features never share one version number.

After bumping, run `FORCE=1 make build-self` to re-aggregate `marketplace.json`,
then add a `## [Unreleased]` → Changed/Added entry in `docs/product/changelog.md`.

## Self-hosting projection

All `.apm/` primitives in this directory are the **source of truth**. `make build-self`
projects them to every shipped adapter's layout — the exact targets are adapter-specific
(see `docs/contracts/adapter.toml` for the full map). Never edit a projected output directly;
always edit the source under `.apm/` and let build-self handle all adapters.

**Exception: `.claude/skills/README.md` is canonical (not projected) — edit it directly.**

Use `FORCE=1 make build-self` when the working tree is intentionally dirty mid-session.
Direct equivalent (when Make is unavailable):

```bash
python3 tools/build_gate_chain.py build-self --force --packs-dir packs
```

**Critical ordering:** when a session edits both seeds (`packs/<pack>/seeds/`) and
non-seed pack sources (`.apm/**`, `pack.toml`) in the same working tree, run
`build-self --force` AFTER all edits are applied — not between them. Build-self
regenerates from cached sources and can silently revert edits made before it ran.
Safe pattern: apply all edits → `FORCE=1 make build-self` → `git status` (verify
edits survived) → `make build-check` → commit.

**Vendored copy:** `packs/credential-brokers/.apm/user-libs/credbroker/` is
byte-synced from `packages/credbroker/credbroker/` by build-self. Always edit
the `packages/` canonical source; never the `.apm/user-libs/` copy.

**How to discover the seed for a path you're unsure about:**

```bash
# Check if a path is projected:
find packs -path "*/seeds/<projected-path>" 2>/dev/null

# Or trip the guard and let it tell you:
make build-check    # exits non-zero with "edit <seed-path>; run: make build-self"
```

## Claude plugin JSON format

Each pack's `.claude-plugin/plugin.json` is the per-pack Claude plugin manifest.
The build chain validates it against `docs/contracts/plugin-manifest.schema.json`
via `tools/validate-claude-plugin-manifests.py` — non-compliant manifests block
publishing.

**Required fields:**
```json
{
  "name": "pack-name",
  "version": "0.1.0",
  "description": "One-line description."
}
```

**Optional fields** (all of these are allowed; nothing else is):
```json
{
  "skills":      ["skill-a", "skill-b"],
  "agents":      ["agent-name"],
  "author":      {"name": "Author Name", "email": "optional@example.com"},
  "license":     "Apache-2.0",
  "homepage":    "https://...",
  "repository":  "https://...",
  "keywords":    ["keyword"],
  "category":    "category-string",
  "displayName": "Human-Readable Pack Name",
  "source":      {"source": "...", "repo": "...", "branch": "...", "directory": "..."}
}
```

`additionalProperties: false` — **any unknown key fails validation.** This has
caused schema failures in the past; if you add a field, verify it is in the schema
first. Validate locally after editing:

```bash
make build && python3 tools/validate-claude-plugin-manifests.py
```

## Authoring or editing a skill

Edit `packs/<pack>/.apm/skills/<name>/SKILL.md`. Run `make build-self` to project.
Run `python3 tools/lint-skill-spec.py` to confirm compliance. Full ruleset:
[`.claude/skills/README.md § Authoring skills`](../.claude/skills/README.md#authoring-skills).

Key rules:
- **Trigger surface lives in frontmatter `description` alone** — body must not restate when to invoke.
- **Body answers what to do once invoked** — preconditions, judgment, procedure.
- **Keep bodies terse** — push depth into `references/` files the body links on demand.
- **Declare output rendering directives** — add `## Output rendering` before the first
  procedural `##` for skills that surface structured output. Full catalog:
  [`docs/guides/core/reference/output-rendering.md`](../docs/guides/core/reference/output-rendering.md).
- **No internal-governance citations** — no RFC/ADR numbers, no internal spec paths
  in any `.apm/**` content (skills, agents, commands, hooks, `references/`, `scripts/`).

## Eval coverage

A non-cosmetic pack update must also build or update the pack's eval harness.
Per the `pack-activation-evals` spec:

- **Tier-A activation** — `evals/eval_queries.json` (~8–10 should-trigger + ~8–10
  near-miss should-NOT-trigger queries) and a `[pack.evals]` block in `pack.toml`
  listing every user-triggered skill. Exclude reviewer-internal skills.
- **Tier-4 LLM-judge rubric** — `evals/evals.json` for judgment/authoring skills
  (those that produce a spec, diagram, critique, guide, or intent by judgment).
- **Tier-B-lite** — additionally an `expect` block + `evals/files/` fixture for
  deterministic skills (those that run a script and emit a checkable artifact).

Verify the harness locally:

```bash
python tools/run-pack-evals.py --pack <pack> --mode judge \
  --judge-adapter claude-code --artifacts <file>
```
