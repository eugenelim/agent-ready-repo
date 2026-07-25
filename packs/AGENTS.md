# AGENTS.md — `packs/`

Context for working inside any pack directory. **Max 150 lines** (AGENTS.md hygiene gate enforces it).
See `AGENTS.local.md` for broader self-host context.

## Pack layout

| Path | Purpose |
|------|---------|
| `pack.toml` | Pack metadata — version, description, adapter-contract, categories |
| `.claude-plugin/plugin.json` | Claude plugin manifest source (must match `pack.toml` version, stay schema-valid) |
| `seeds/` | Adopter scaffold templates (brownfield install) |
| `.apm/skills/` | Skill sources → projected per adapter |
| `.apm/agents/` | Agent sources → projected per adapter |
| `.apm/hooks/` | Hook-body sources → projected per adapter |
| `.apm/hook-wiring/` | Hook-wiring sources → projected per adapter |
| `.apm/commands/` | Command sources → projected per adapter |
| `.apm/kiro-ide-hooks/` | Kiro IDE hook sources → projected per adapter |
| `.apm/shared-libs/` | Shared library sources → projected per adapter |
| `.apm/adapter-root-bins/` | Adapter root binary sources → projected per adapter |
| `.apm/user-libs/` | User library sources → projected per adapter |

Primitive source paths are authoritative in `docs/contracts/adapter.toml`.

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

## Pack design model

intent → user journey → stage → capability → output

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

**Exception: `.claude/skills/README.md` is canonical (not projected) — edit it directly.**

Use `FORCE=1 make build-self` when the working tree is intentionally dirty. Direct equivalent:
```bash
agentbundle catalogue self-host --root . --write --force
```

**Critical ordering:** when a session edits both seeds and non-seed pack sources (`.apm/**`, `pack.toml`), run `build-self --force` AFTER all edits — not between them. Safe pattern: all edits → `FORCE=1 make build-self` → `git status` → `make build-check` → commit.

**Vendored copy:** `packs/credential-brokers/.apm/user-libs/credbroker/` is byte-synced from `packages/credbroker/credbroker/`. Edit the `packages/` source; never the `.apm/user-libs/` copy.

## Claude plugin JSON format

Each pack's `.claude-plugin/plugin.json` is validated against `docs/contracts/plugin-manifest.schema.json` at build time. Non-compliant manifests block publishing.

**Required:** `name` (string), `version` (string matching `pack.toml`), `description` (string).

**Allowed optional fields** — `skills`, `agents` (arrays of strings); `author` (`{name, email?}`); `license`, `homepage`, `repository`, `category`, `displayName` (strings); `keywords` (array); `source` (`{source, repo, branch, directory}`).

`additionalProperties: false` — any unknown key fails validation. Verify before adding a field: `make build && python3 tools/validate-claude-plugin-manifests.py`.

## Authoring or editing a skill

Edit `.apm/skills/<name>/SKILL.md`. Run `make build-self` to project. Run `agentbundle catalogue lint --root . --deep` to confirm [agentskills.io spec](https://agentskills.io/specification) compliance (requires `pip install 'agentbundle[lint]'` for the full deep pass; shallow structural checks run without it).

**Spec compliance (enforced by linter):**
- Each skill is a **self-contained folder** — `SKILL.md` + optional `scripts/`, `references/`, `assets/`, `evals/`. Never import from another skill's folder or assume files outside its directory.
- **Closed frontmatter key set:** `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Anything else goes nested under `metadata:`.
- **`name`** is kebab-case (`^[a-z0-9]+(-[a-z0-9]+)*$`, 1–64 chars).
- **Path rules in body:** self-references use skill-relative paths (`scripts/foo.py`); cross-skill references use the skill name only — never `.claude/skills/<...>/` or `packs/.../skills/<...>/` prefixes.

**Craft rules (not linted — hold in head):**
- **`description` is the trigger surface** — body must not restate when to invoke. **Hard cap: 1024 chars** (Kiro's frontmatter parser silently truncates at the byte boundary; `agentbundle catalogue lint --deep` enforces this).
- **Body answers what to do once invoked** — preconditions, judgment, procedure. Keep it terse.
- **Declare output rendering directives** — `## Output rendering` before the first procedural `##` for skills that surface structured output. Catalog: `docs/guides/core/reference/output-rendering.md`.
- **No internal-governance citations** — no RFC/ADR numbers or internal spec paths in any `.apm/**` content.

## Personal information

**Never include personal information in pack content.** This means no real names, email addresses, usernames, account IDs, phone numbers, or any other PII in `.apm/**`, `seeds/**`, `pack.toml`, or any other in-tree file. Use placeholder values (e.g. `example@example.com`, `<your-org>`) in templates and example config. The CI credential scan (`Gate C`) blocks real bearer tokens; the same discipline applies to all personal data.

## Eval coverage

A non-cosmetic pack update must also update the pack's eval harness:

- **Tier-A activation** — `evals/eval_queries.json` (~8–10 should-trigger + ~8–10 near-miss) and a `[pack.evals]` block in `pack.toml` listing every user-triggered skill.
- **Tier-4 LLM-judge rubric** — `evals/evals.json` for judgment/authoring skills.
- **Tier-B-lite** — additionally an `expect` block + `evals/files/` fixture for deterministic skills.

Verify locally with `agentbundle pack evals run --pack <pack> --mode judge --judge-adapter claude-code --artifacts <file> --catalogue-root .`.

## Agents project to multiple adapters

The `agent` primitive (e.g. `adversarial-reviewer`, `quality-engineer`) projects to claude-code, kiro, and codex today; copilot support is addable. Check `docs/contracts/adapter.toml` for the current map.

When reasoning about reviewer/agent reach, the default is "agents reach claude-code + kiro + codex today (copilot addable)."

`AGENTS.md` is a **Manual** file — `build-self` won't regenerate it once it exists. A fix to the agent-support statement must edit **both** `packs/core/seeds/AGENTS.md` (the seed) and the working-tree `AGENTS.md` directly.

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
# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
```

Windows CI (Python 3.11, cp1252 default) crashes on any Unicode character — including ✓, ✗, →, — — without this guard. `errors="strict"` on stdout surfaces encoding bugs immediately; `errors="backslashreplace"` on stderr prevents diagnostic messages from being lost.

Any `subprocess.run` call with `text=True` must also pass `encoding="utf-8"` — child scripts reconfigured to UTF-8 produce bytes undefined in cp1252, which corrupts the parent's decoded output.
