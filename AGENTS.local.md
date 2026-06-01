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

## Adopter-facing materials ship; repo-specific tooling stays local-only

The governing line for *what goes where*: **adopter-facing materials ship;
this repo's own projection artifacts and repo-specific tooling stay
local-only** (the `AGENTS.local.md` / `*.local.*` convention — like the
`AGENTS.local.md` footer pointer itself). A shipped primitive (anything under
a pack's `.apm/` or `seeds/`) must reference and run **only** things that
install into an adopter's tree. Catalogue-internal tooling — which enforces
*this catalogue's* conventions on *this catalogue's* own artifacts — never
ships and is never referenced by a shipped primitive.

**This catalogue's own enforcement gate is local-only.** The shipped
`pre-pr.py` runs only the work-loop caps check (`loop-cohort.py check`, which
ships) plus a wire-your-gate stub — it references none of our linters. This
repo's full gate is the **repo-native, never-projected**
`tools/pre-pr-catalogue.py`, which runs the 8 catalogue checks
(`lint-agents-md`, `lint-agent-artifacts`, `lint-skill-spec`, `lint-knowledge`,
`lint-build`, `lint-seeds`, `lint_credentialed_skills`, and the
`test-lint-credentialed-skills` self-test) and then delegates to the shipped
`pre-pr.py`. `make pre-pr`, `make build-check`, and CI's `docs.yml` `hooks` job
all run it. If you're tempted to make a shipped hook/command/template reference
`tools/lint-*` (or `make build-self`, `docs/specs/`, `.github/workflows/`),
stop: that's catalogue-internal — it breaks on arrival in an adopter's repo
(this is the issue #190 / `adopter-clean-enforcement-gate` class of bug).

### Shipped pack content carries no internal-governance citations

When you author or edit anything under a pack's `.apm/**` (skills, agents,
commands, hooks, their `scripts/`, `references/`, `shared-libs/`,
`adapter-root-bins/`), **never cite this catalogue's own governance**. Adopters
receive the artifact but none of the governance it was written under, so the
citation is dangling noise on arrival. The four types to keep out:

1. **RFC numbers** — `RFC-0001`…`RFC-00NN` (our zero-padded form).
2. **ADR numbers** — `ADR-0001`…`ADR-00NN`.
3. **Named-spec / acceptance-criterion / plan citations** — `spec § AC15`,
   `skill-secrets spec § AC24`, `credential-broker-contract T7`,
   `plan §T5 lines 357-362`, `docs/specs/flow-metrics.md § "Outputs"`.
4. **Internal doc paths** — `docs/specs/<named-feature>.md`, `docs/adr/…`,
   `docs/rfc/…`, `.github/workflows/…` (the adopter-clean rule above already
   bars these from shipped *hooks/commands*; it holds for all `.apm/**`).

Drop the citation, keep the rule: *"Markers are repo-only per RFC-0004"* →
*"Markers are repo-only"*; *"Refuses the reserved `sso` namespace (spec § AC4b)"*
→ *"Refuses the reserved `sso` namespace"*. Where the citation carried a "why",
reword to self-contained prose ("by convention", "a known gap"), never a
dangling back-reference or an orphaned connective.

**What is NOT a citation — leave it:** the generic spec-driven *workflow
vocabulary* that ships as the convention itself (`docs/specs/<feature>/spec.md`
and `plan.md` placeholders, the words "spec" / "plan" / "acceptance criteria"),
**real external standards** (IETF/W3C — `RFC 9457`, `RFC 8259` — distinguished
by the space + large number), and **functional fixture/template content** (e.g.
`- [ ] AC1` rows in the spec-status linter's test fixtures, where `AC1` is data
the parser consumes, not a citation).

Precedent: `lint-seeds` already enforces this for `seeds/**`. There is **no
automated lint for `.apm/**` skills/agents yet** — a `lint-seeds`-analogue is a
possible follow-on, but adding one is a new convention and therefore RFC-gated.
Until then this is a hand-checked authoring rule.

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

## Windows / cross-OS compatibility rules

These rules apply to all new code in this repo. Production code
(`packages/agentbundle/agentbundle/`) is already clean; the rules
exist to keep it that way and to guide test/tool code.

**Encoding — always explicit:**

- `Path.read_text()` and `Path.write_text()` must always pass
  `encoding="utf-8"`. On Windows the default codepage is CP1252, not
  UTF-8; omitting it silently corrupts or rejects markdown, JSON, and
  TOML with non-ASCII content.
- `open()` calls that process text content need `encoding="utf-8"` too.
- Exception: `read_bytes()` / `write_bytes()` are inherently correct.

**Symlinks — guard, don't assume:**

- In test code, wrap `os.symlink()` in `try/except OSError:
  pytest.skip("symlinks not available")`. Windows without Developer
  Mode denies symlink creation even for admin users.
- Production code uses the `_is_equivalent_claude_md_shape()` helper
  (`self_host.py`) which handles three equivalent representations:
  POSIX symlink, Windows content copy, and Git-for-Windows stub.

**POSIX-only assertions — gate explicitly:**

- Inode checks (`st_ino`), nanosecond mtimes (`st_mtime_ns`), and
  permission-bit assertions are POSIX-only. Wrap them in
  `if sys.platform != "win32":` inside the test body.
- `os.chmod()` in test setup must be gated with `if os.name == "posix":`.

**Paths — use pathlib, not string surgery:**

- All path construction uses `pathlib.Path` or `os.path.join`. No
  string concatenation with `/`. No `os.environ["HOME"]` (use
  `Path.home()`). No hardcoded `/tmp` for real filesystem operations
  (use `tempfile`).

**Subprocess — no shell, no Unix-only tools:**

- `subprocess` calls use list form, never `shell=True`.
- Do not invoke `which`, `grep`, `find`, `sed`, `awk`, `make`, `sh`,
  or `bash` via subprocess in portable code; use Python equivalents.

The `.github/workflows/build-check-windows.yml` CI job validates the
portable subset. A first systematic sweep (tools + test files) was
done in 2026-06.
