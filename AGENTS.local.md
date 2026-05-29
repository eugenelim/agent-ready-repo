# AGENTS.local.md

Repo-local addendum for maintainers of this checkout. Keep guidance here
specific to this repository instance; shared agent instructions belong in
`packs/core/seeds/AGENTS.md` and are projected to `AGENTS.md`.

## Pack-shipped features run in adopters' repos — design against projected/installed state

This repo is a **pack catalogue**: packs (`core`, `governance-extras`,
`user-guide-diataxis`, `monorepo-extras`) are projected and **installed
into other people's repositories** via APM / Claude plugins / the CLI.
A feature that ships inside a pack — a lint, a hook, a skill, a gate —
does its real work in the *adopter's* projected/installed tree, not here.

**When you design or validate any pack-shipped feature, reason about the
end-user projected/installed pack state, not this repo's internal state.**
Concretely:

- The contract an adopter's artifacts follow is the **pack template /
  seed** (e.g. `packs/core/.apm/skills/new-spec/assets/spec.md`), not
  this repo's hand-authored examples. An adopter's `docs/specs/` are
  template-shaped from birth (canonical status vocabulary, `- [ ]`
  acceptance-criteria checkboxes); validate the feature against *that*
  shape.
- This repo's own `docs/specs/`, `docs/rfc/`, `docs/adr/` are
  **bundle-governance** about the catalogue's own evolution, and this
  repo is merely the **self-host adopter** (`make build-self`). Much of
  that internal corpus pre-dates the canonical formats and is
  heterogeneous. Do **not** let internal-corpus quirks drive
  pack-feature design — they are at most a self-host edge case to keep
  the local build green, never the requirement.
- Before concluding "the feature breaks / false-positives / needs a
  migration," ask: *does this happen in a fresh adopter's template-shaped
  tree, or only in this repo's legacy internal corpus?* The former is a
  design bug; the latter is a self-host cleanup.
- Coverage that matters is **per-adapter projected layout** (see the
  Install-test coverage rule below) and the installed runtime surface
  (CI vs. lifecycle-event hooks), not what happens to be true in this
  checkout.

## Agents PROJECT — they are not "Claude Code only" (stop getting this wrong)

The `agent` primitive (e.g. `adversarial-reviewer`, `quality-engineer`)
projects to **three of four** shipped adapters. Verified against
`docs/contracts/adapter.toml` *and* each tool's docs (checked 2026-05):

| Adapter | agent mode | target | Ships? |
| --- | --- | --- | --- |
| claude-code | `direct-file` | `.claude/agents/` | ✓ |
| kiro | `direct-file` (`kiro-agent-frontmatter`) | `.kiro/agents/` | ✓ |
| codex | `codex-agent-toml` (`codex-agent-frontmatter`) | `.codex/agents/` | ✓ |
| copilot | `dropped` | — | ✗ (see below) |

All three consuming tools genuinely support subagents as of 2026:
[Codex subagents GA 2026-03-16](https://developers.openai.com/codex/subagents),
[Kiro custom subagents (IDE 0.9, Feb 2026)](https://kiro.dev/docs/chat/subagents/).
**Copilot's `dropped` is a contract-lag, not a capability ceiling** —
Copilot itself added custom subagents in 2026
([GitHub Copilot custom agents](https://docs.github.com/en/copilot/how-tos/copilot-sdk/use-copilot-sdk/custom-agents)),
so copilot agent support is *addable* when we choose to.

**Corrected 2026-05-29:** `packs/core/seeds/AGENTS.md` previously read
"Codex and Copilot drop the agent primitive" — wrong (codex projects
agents via `codex-agent-toml`); fixed to "where your tool supports
them". Note the root `AGENTS.md` is a **Manual** file — `build-self`
won't regenerate it (`_compose_agents_md` returns early when it exists),
so the seed and the working-tree `AGENTS.md` are maintained
*independently*; a fix like this must edit **both** surfaces.

When reasoning about reviewer/agent reach, the correct default is
"agents reach claude-code + kiro + codex today (copilot addable)," not
"Claude Code only."

## Self-hosting drift — check before editing any file at a projected path

This repo is self-hosted from `packs/`. Many files at `<repo>/...` paths
are **rendered outputs**, not the source-of-truth. Editing them directly
trips `make build-check` and blocks every PR.

**Always-projected paths** (drift-prone — edit the seed, not the projection):

| Projected path                       | Source of truth (seed)                                       |
| ------------------------------------ | ------------------------------------------------------------ |
| `AGENTS.md`, `CLAUDE.md`             | `packs/core/seeds/AGENTS.md` (symlinked at the projection)   |
| `docs/CONVENTIONS.md`                | `packs/core/seeds/docs/CONVENTIONS.md`                       |

After the 2026-05-25 amendment to RFC-0002, the following paths are
**Manual** (filled-in on disk; pack seed is placeholder template
adopters receive on first install via brownfield rules):

| Manual path (this repo's living instance) | Pack seed (placeholder)                                      |
| ----------------------------------------- | ------------------------------------------------------------ |
| `docs/CHARTER.md`                         | `packs/core/seeds/docs/CHARTER.md` (placeholder template)    |
| `docs/architecture/overview.md`           | `packs/core/seeds/docs/architecture/overview.md`             |
| `docs/specs/README.md`                    | `packs/core/seeds/docs/specs/README.md`                      |
| `docs/knowledge/patterns.jsonl`           | `packs/core/seeds/docs/knowledge/patterns.jsonl` (empty)     |
| `docs/rfc/README.md`                      | `packs/governance-extras/seeds/docs/rfc/README.md`           |
| `docs/adr/README.md`                      | `packs/governance-extras/seeds/docs/adr/README.md`           |
| `docs/guides/**/README.md`                | `packs/user-guide-diataxis/seeds/docs/guides/**/README.md`   |
| `.claude/skills/<name>/**`           | `packs/<pack>/.apm/skills/<name>/**` (e.g. `packs/core/.apm/skills/new-spec/SKILL.md`) |
| `.claude/agents/<name>.md`           | `packs/<pack>/.apm/agents/<name>.md`                         |
| `.claude/commands/<name>.md`         | `packs/<pack>/.apm/commands/<name>.md`                       |
| `.claude/hooks/...`                  | `packs/<pack>/.apm/hooks/...`                                |

**The workflow when you touch any of the above:**

1. Edit the seed file (under `packs/<pack>/seeds/...`), *not* the
   projected output.
2. Run `make build-self` to regenerate every projected path from its seed.
3. Run `make build-check` to confirm zero drift before committing.

**How to discover the seed for a path you're unsure about:**

```bash
# If you're not sure whether a path is projected:
find packs -path "*/seeds/<projected-path>" 2>/dev/null

# Or just edit the projected path and let make build-check tell you:
make build-check    # exits non-zero with "edit <seed-path>; run: make build-self"
```

The `make build-check` error message names the seed path you should
have edited — so if you do trip it, the fix is mechanical (edit the
seed it names, re-run `make build-self`, re-commit).

**Drift fixed three times already** (each time a CI cycle wasted):
- RFC-0007 PR (#53) added a row to `docs/rfc/README.md`; fixed by
  propagating to `packs/governance-extras/seeds/docs/rfc/README.md`.
- converters-pack spec PR (#57) added a row to `docs/specs/README.md`;
  fixed by propagating to `packs/core/seeds/docs/specs/README.md`.
- new-spec subagent-matching PR (#67) edited `.claude/skills/new-spec/SKILL.md`
  directly; fixed by propagating to `packs/core/.apm/skills/new-spec/SKILL.md`.
  Note: `.claude/skills/` and `.claude/agents/` project from
  `packs/<pack>/.apm/...`, **not** from `packs/<pack>/seeds/...`.

If you edit any README, table, or doc under the projected paths above,
**check the seed first**.

## Authoring or editing a skill

Skills live under `packs/<pack>/.apm/skills/<name>/SKILL.md` (the seed)
and project to `.claude/skills/<name>/SKILL.md`. Edit the seed, not the
projection. After any edit, run `make build-self` to regenerate the
projection, then `python3 tools/lint-skill-spec.py` to confirm the
[agentskills.io spec](https://agentskills.io/specification) checks pass.

The linter walks both roots, so a seed/projection drift surfaces as
either an error or a `make build-check` failure — whichever fires
first. The path rules (skill-relative for own files, name-only for
other skills, no `.claude/skills/<...>/` or
`packs/.../.apm/skills/<...>/` prefixes in bodies) are the most common
authoring mistake; the linter catches them, but it's faster to write
them right the first time. See
[`.claude/skills/README.md`](.claude/skills/README.md#spec-compliance)
for the full ruleset.

## Install-test coverage rule

Tests that exercise an on-disk projection layout, the per-pack orphan
scanner (`safety.scan_for_pack_artifacts`), or the install handler's
adapter-resolution path **must parametrize over every shipped
adapter** — today `claude-code`, `kiro`, `codex`, `copilot` — not just
the default. Each adapter projects to a different directory layout
(`.claude/`, `.kiro/`, `.agents/skills/`, `.github/instructions/`) and
the per-pack scanner's primitive-name heuristic interacts differently
with each shape; coverage at one adapter does not prove coverage at
the others.

The rule scopes to tests that interact with the *projection or
scanner*; tests deliberately scoped to scope-resolution, dependency
gates, or state-accumulation (which are adapter-independent by
construction) may opt out, and the test's docstring should say so —
see `test_user_scope_multi_pack_accumulates_state` for the shape.

**The reference shape** is `packages/agentbundle/tests/integration/test_multi_pack_install.py`:
`packages/agentbundle/agentbundle/_data/adapter.toml` is the source of
truth for which adapters ship; the test module derives
`_SHIPPED_ADAPTERS` from it via
`scope.shipped_adapters_from_contract()` so adding a new
`[adapter.<name>]` table to the contract expands every parametrized
test in the same PR. Adapter-specific behaviour gaps are pinned as
their own tests rather than silently elided. The
`_skill_path(adapter, skill_name)` helper hand-mirrors the
`[[adapter.<name>.projection]]` table — when a new adapter ships,
both the contract entry and `_skill_path` must change in the same PR.

A known coverage asymmetry pinned by `test_copilot_orphan_scan_finds_hooks_but_not_instructions`:
copilot's flat `.github/instructions/<primitive>.instructions.md`
projection has a stem (`<primitive>.instructions`) that matches none
of the scanner's heuristic conditions, so the per-pack scanner
returns `[]` for copilot's instructions directory. The scanner still
fires at copilot for packs that ship `tools/hooks/` files (copilot's
`allowed-prefixes.repo` includes both surfaces), so cross-pack tests
parametrize Direction A (force-installing a skills-only pack) over a
narrower adapter set and Direction B (force-installing a pack with
hooks) over the full set. When new adapter-specific orphan-scan gaps
are discovered, follow this pattern — pin the gap explicitly so it
can't drift unnoticed.

## New tool scripts: Python, not bash

When adding a new tool, self-test, or hook under `tools/`, write it in
pure-stdlib Python (`.py`), not bash (`.sh`). Existing `.sh` files stay
where they are — the rule applies forward, not retroactively — but new
additions need to run on Windows without an MSYS shell or WSL. The
companion Windows-CI work expects every new script to be `python3
<script>` rather than `bash <script>`, and the path triggers in
`.github/workflows/docs.yml` should match that. Bash is fine for
*existing* gates we haven't ported yet; for anything new, default to
Python first.
