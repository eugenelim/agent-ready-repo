# AGENTS.md — `packs/`

Context for working inside any pack directory. **Max 150 lines** (AGENTS.md hygiene gate enforces it).
See `AGENTS.local.md` for broader self-host context.

## Pack layout

| Path | Purpose |
|------|---------|
| `pack.toml` | Pack metadata — version, description, adapter-contract, categories |
| `.claude-plugin/plugin.json` | Claude plugin manifest source (must match `pack.toml` version, stay schema-valid) |
| `seeds/` | Adopter scaffold templates (brownfield install) |
| `docs/` | Concept anchor and pack guides — never projected or installed; travels in Artifactory packages |
| `.apm/skills/` | Skill sources → projected per adapter |
| `.apm/agents/` | Agent sources → projected per adapter |
| `.apm/hooks/` | Hook-body sources → projected per adapter |
| `.apm/hook-wiring/` | Hook-wiring sources → projected per adapter |
| `.apm/commands/` | Command sources → projected per adapter |
| `.apm/kiro-ide-hooks/` | Kiro IDE hook sources → projected per adapter |
| `.apm/shared-libs/` | Shared library sources → projected per adapter |
| `.apm/adapter-root-bins/` | Adapter root binary sources → projected per adapter |
| `.apm/user-libs/` | User library sources → projected per adapter |

## pack.toml schema map

| Table | Required fields | Notable optional fields |
|-------|----------------|------------------------|
| `[pack]` | `name`, `version`, `description`, `adapter-contract` | `display-name`, `categories`, `keywords`, `maintainers`, `links`, `readme` |
| `[pack.recipes.*]` | `description` | `steps`, `adapter` |
| `[pack.dependencies]` | — | Pack dependency declarations |
| `[pack.seeds]` | — | Seed path configuration |
| `[pack.layout]` | — | Per-scope layout overrides |
| `[pack.first-value]` | — | First-value install metadata |
| `[pack.adaptation]` | — | Adaptation inference rules |

## Primary workflow (any catalogue)

Run after any pack change. If `agentbundle` is not installed: `pip install agentbundle`.

```bash
agentbundle catalogue lint --root .
agentbundle catalogue verify --root .
agentbundle catalogue self-host --root . --write
```

Home-repository additional gate (not required for external catalogues):

```bash
make build-check   # agentbundle catalogue verify + repo governance + SAST
```

## Version bump rule

Every **non-cosmetic** change to pack content requires a version bump in both:
1. `pack.toml` → `[pack] version`
2. `.claude-plugin/plugin.json` → `"version"`

Which increment: **patch** for changed bodies/directives/conventions; **minor** for new primitives; **major** for removals. Never ride an unreleased version from another in-flight PR.

After bumping: `FORCE=1 make build-self` (re-aggregates `marketplace.json`), then add a `## [pack-name][version] — YYYY-MM-DD` section in `docs/product/changelog.md`.

## Self-hosting projection

All `.apm/` primitives are the **source of truth**. `make build-self` projects them to every shipped adapter's layout (see `docs/contracts/adapter.toml` for the full map). Never edit a projected output directly.

Use `FORCE=1 make build-self` when the working tree is intentionally dirty. Direct equivalent:
```bash
agentbundle catalogue self-host --root . --write --force
```

**Critical ordering:** when a session edits both seeds and non-seed pack sources (`.apm/**`, `pack.toml`), run `build-self --force` AFTER all edits — not between them. Safe pattern: all edits → `FORCE=1 make build-self` → `git status` → `make build-check` → commit.

## Claude plugin JSON format

Each pack's `.claude-plugin/plugin.json` is validated against `docs/contracts/plugin-manifest.schema.json` at build time. Non-compliant manifests block publishing.

**Required:** `name` (string), `version` (string matching `pack.toml`), `description` (string).

**Allowed optional fields** — `skills`, `agents` (arrays of strings); `author` (`{name, email?}`); `license`, `homepage`, `repository`, `category`, `displayName` (strings); `keywords` (array); `source` (`{source, repo, branch, directory}`).

`additionalProperties: false` — any unknown key fails validation. Verify before adding a field: `make build && python3 tools/validate-claude-plugin-manifests.py`.

## Authoring or editing a skill

Edit `.apm/skills/<name>/SKILL.md`. Run `make build-self` to project. Run `agentbundle catalogue lint --root . --deep` to confirm [agentskills.io spec](https://agentskills.io/specification) compliance (requires `pip install 'agentbundle[lint]'` for the full deep pass; shallow structural checks run without it).

Full authoring standards — frontmatter key whitelist, body structure, naming verb taxonomy, directory layout, progressive disclosure, cross-platform Python, three-tier dependency policy, and evals — live in [`guides/_shared/how-to/author-a-skill.md`](../guides/_shared/how-to/author-a-skill.md). Additional catalogue-specific craft:
- **Output rendering conventions** (status glyphs, column alignment, truncation limits, persistent command bar, delete-gate box) — [`guides/_shared/reference/skill-ux-patterns.md`](../guides/_shared/reference/skill-ux-patterns.md).
- **Script flag conventions** (`--headed`, `--yes`, `--debug`, `--raw`; `=` form for values; usage docblocks; shortcut IDs) — [`guides/_shared/reference/skill-script-conventions.md`](../guides/_shared/reference/skill-script-conventions.md).
- **Browser automation and auth handoff** (persistent Chrome profile, token interception, probe-files data layer) — [`guides/_shared/how-to/browser-automation-skill.md`](../guides/_shared/how-to/browser-automation-skill.md).

## Eval coverage

A non-cosmetic pack update must also update the pack's eval harness:

- **Tier-A activation** — `evals/eval_queries.json` (~8–10 should-trigger + ~8–10 near-miss) and a `[pack.evals]` block in `pack.toml` listing every user-triggered skill.
- **Tier-4 LLM-judge rubric** — `evals/evals.json` for judgment/authoring skills.
- **Tier-B-lite** — additionally an `expect` block + `evals/files/` fixture for deterministic skills.

Verify locally with `agentbundle pack evals run --pack <pack> --mode judge --judge-adapter claude-code --artifacts <file> --catalogue-root .`.

## Agents project to multiple adapters

The `agent` primitive projects to claude-code, kiro, and codex; copilot addable. `AGENTS.md` is **Manual** — `build-self` won't regenerate it; edit both `packs/core/seeds/AGENTS.md` and the working-tree file directly.

## Shipped pack content carries no internal-governance citations

When authoring anything under `.apm/**` (skills, agents, commands, hooks, `scripts/`, `references/`, `shared-libs/`, `adapter-root-bins/`), never cite this catalogue's own governance. The four types to keep out:

1. **RFC numbers** — `RFC-0001`…`RFC-00NN`.
2. **ADR numbers** — `ADR-0001`…`ADR-00NN`.
3. **Spec/plan citations** — `spec § AC15`, `plan §T5 lines 357-362`, `docs/specs/<feature>.md § "Outputs"`.
4. **Internal doc paths** — `docs/specs/…`, `docs/adr/…`, `docs/rfc/…`, `.github/workflows/…`.

Drop the citation, keep the rule: *"Markers are repo-only per RFC-0004"* → *"Markers are repo-only"*.

## Windows-safe Python scripts

Any script under `.apm/` that prints to stdout or stderr must include the UTF-8 reconfigure guard immediately after `import sys`, before any `print()` call:

```python
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
```
Windows CI (Python 3.11, cp1252 default) crashes on any Unicode character without this guard. `errors="strict"` on stdout surfaces encoding bugs immediately; `errors="backslashreplace"` on stderr prevents diagnostic loss.
Any `subprocess.run` call with `text=True` must also pass `encoding="utf-8"` — child scripts reconfigured to UTF-8 produce bytes undefined in cp1252.

## Authoring README.md and DESIGN.md

**README** (for adopters): states the pack's intent and the user journey it serves — not a contributor capability reference, not a skill inventory. Structure: outcome sentence → first-workflow command with mock → `| Say this | What happens |` entry points table → 2–3 terminal session mocks → cross-pack dependencies → links.

**DESIGN.md** (for contributors, living reference not proposal): create when the pack has non-obvious philosophy, a method shape skill authors must not break, or decisions that get re-litigated in PRs. Structure: ADR/RFC header → TL;DR (3–5 prose sentences) → Non-Goals bullets → numbered sections (philosophy, method, invariants, decisions) → decisions log with `Alternative considered:` per entry. Update same-PR on any conflicting skill change — drift is a bug.

## Skill reference files

No shared `references/` directory exists. References are copied per-skill; each skill stands alone.

- **Intra-pack**: source copy says `> Note: this reference is intentionally duplicated into \`<skill>\`'s \`references/<file>\`.`; receiving copy says `duplicated from`. Copies stay byte-identical except the note wording.
- **Cross-pack** (e.g. `digital-experience-contract.md`): file carries `schema-version:` in YAML frontmatter; all copies byte-identical. When updating, grep for the filename and update every copy in the same commit.

**Pack config API** — pack scripts can resolve a user-scope directory, read operator-declared config, and write structured operation log entries. See [`guides/_shared/reference/pack-config-api.md`](../guides/_shared/reference/pack-config-api.md) for the full reference: `pack_dir`, `load_pack_config`, `write_entry`, catalogue `[pack-defaults.*]` setup, and the `agentbundle pack-config` / `agentbundle oplog` CLI.
