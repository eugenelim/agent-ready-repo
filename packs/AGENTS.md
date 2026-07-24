# AGENTS.md — `packs/`

Context for working inside any pack directory. **Max 150 lines** (AGENTS.md hygiene gate enforces it).
See `AGENTS.local.md` for broader self-host context.

## Pack anatomy

| Path | Purpose |
|------|---------|
| `pack.toml` | Pack metadata — version, description, categories, keywords |
| `.claude-plugin/plugin.json` | Claude plugin manifest source (must match `pack.toml` version, stay schema-valid) |
| `.apm/skills/<name>/SKILL.md` | Skill source of truth — projected per adapter by `make build-self` |
| `.apm/agents/<name>.md` | Agent source of truth — projected per adapter |
| `.apm/commands/<name>.md` and `.apm/hooks/` | Command and hook sources — projected per adapter |
| `seeds/` | Adopter scaffold templates (brownfield install) |

## Version bump rule

Every **non-cosmetic** change to pack content requires a version bump in both:
1. `pack.toml` → `[pack] version`
2. `.claude-plugin/plugin.json` → `"version"`

Which increment: **patch** for changed bodies/directives/conventions; **minor** for new primitives; **major** for removals. Never ride an unreleased version from another in-flight PR — two features never share one version number.

After bumping: `FORCE=1 make build-self` (re-aggregates `marketplace.json`), then add a changelog entry in `docs/product/changelog.md`.

## Self-hosting projection

All `.apm/` primitives are the **source of truth**. `make build-self` projects them to every shipped adapter's layout (see `docs/contracts/adapter.toml` for the full map). Never edit a projected output directly.

**Exception: `.claude/skills/README.md` is canonical (not projected) — edit it directly.**

Use `FORCE=1 make build-self` when the working tree is intentionally dirty. Direct equivalent:
```bash
python3 tools/build_gate_chain.py build-self --force --packs-dir packs
```

**Critical ordering:** when a session edits both seeds and non-seed pack sources (`.apm/**`, `pack.toml`), run `build-self --force` AFTER all edits — not between them. Build-self can silently revert edits made before it ran. Safe pattern: all edits → `FORCE=1 make build-self` → `git status` → `make build-check` → commit.

**Vendored copy:** `packs/credential-brokers/.apm/user-libs/credbroker/` is byte-synced from `packages/credbroker/credbroker/`. Edit the `packages/` source; never the `.apm/user-libs/` copy.

## Claude plugin JSON format

Each pack's `.claude-plugin/plugin.json` is validated against `docs/contracts/plugin-manifest.schema.json` at build time. Non-compliant manifests block publishing.

**Required:** `name` (string), `version` (string matching `pack.toml`), `description` (string).

**Allowed optional fields** — `skills`, `agents` (arrays of strings); `author` (`{name, email?}`); `license`, `homepage`, `repository`, `category`, `displayName` (strings); `keywords` (array); `source` (`{source, repo, branch, directory}`).

`additionalProperties: false` — any unknown key fails validation. Verify before adding a field: `make build && python3 tools/validate-claude-plugin-manifests.py`.

## Authoring or editing a skill

Edit `.apm/skills/<name>/SKILL.md`. Run `make build-self` to project. Run `python3 tools/lint-skill-spec.py` to confirm [agentskills.io spec](https://agentskills.io/specification) compliance.

**Spec compliance (enforced by linter):**
- Each skill is a **self-contained folder** — `SKILL.md` + optional `scripts/`, `references/`, `assets/`, `evals/`. Never import from another skill's folder or assume files outside its directory.
- **Closed frontmatter key set:** `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Anything else goes nested under `metadata:`.
- **`name`** is kebab-case (`^[a-z0-9]+(-[a-z0-9]+)*$`, 1–64 chars).
- **Path rules in body:** self-references use skill-relative paths (`scripts/foo.py`); cross-skill references use the skill name only — never `.claude/skills/<...>/` or `packs/.../skills/<...>/` prefixes.

**Craft rules (not linted — hold in head):**
- **`description` is the trigger surface** — body must not restate when to invoke.
- **Body answers what to do once invoked** — preconditions, judgment, procedure. Keep it terse.
- **Declare output rendering directives** — `## Output rendering` before the first procedural `##` for skills that surface structured output. Catalog: `docs/guides/core/reference/output-rendering.md`.
- **No internal-governance citations** — no RFC/ADR numbers or internal spec paths in any `.apm/**` content.

## Eval coverage

A non-cosmetic pack update must also update the pack's eval harness:

- **Tier-A activation** — `evals/eval_queries.json` (~8–10 should-trigger + ~8–10 near-miss) and a `[pack.evals]` block in `pack.toml` listing every user-triggered skill.
- **Tier-4 LLM-judge rubric** — `evals/evals.json` for judgment/authoring skills.
- **Tier-B-lite** — additionally an `expect` block + `evals/files/` fixture for deterministic skills.

Verify locally with `python tools/run-pack-evals.py --pack <pack> --mode judge --judge-adapter claude-code --artifacts <file>`.
