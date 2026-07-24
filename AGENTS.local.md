# AGENTS.local.md

Repo-local addendum for maintainers of this checkout. Shared agent instructions belong in
`packs/core/seeds/AGENTS.md` and are projected to `AGENTS.md`. Pack-specific guidance
(version bumps, projection, skill authoring, eval coverage, plugin format) lives in
[`packs/AGENTS.md`](packs/AGENTS.md).

## Design against the adopter's projected state, not this repo's internal state

This repo is a **pack catalogue**: packs ship into other repositories via APM, Claude
plugins, and the CLI. A feature that ships inside a pack — a lint, a hook, a skill, a
gate — does its real work in the adopter's projected/installed tree, not here.

When designing or validating any pack-shipped feature:

- Validate against the **pack template/seed** (e.g. `packs/core/.apm/skills/new-spec/assets/spec.md`),
  not this repo's hand-authored examples. An adopter's `docs/specs/` are template-shaped from birth.
- This repo's own `docs/specs/`, `docs/rfc/`, `docs/adr/` are bundle-governance about the catalogue's
  evolution; this repo is merely the self-host adopter. Internal-corpus quirks never drive pack-feature
  design — they are self-host edge cases, not requirements.
- Ask: *does this happen in a fresh adopter's template-shaped tree, or only in this repo's legacy
  internal corpus?* The former is a design bug; the latter is a self-host cleanup.
- Coverage that matters is the per-adapter projected layout and the installed runtime surface (CI vs.
  lifecycle-event hooks), not what happens to be true in this checkout.

## Adopter-facing materials ship; repo-specific tooling stays local-only

Shipped primitives (anything under `.apm/` or `seeds/`) must reference and run **only** things
that install into an adopter's tree. Catalogue-internal tooling never ships and is never referenced
by a shipped primitive.

This catalogue's full enforcement gate is **repo-native, never-projected**: `tools/pre-pr-catalogue.py`
runs the 8 catalogue checks (`lint-agents-md`, `lint-agent-artifacts`, `lint-skill-spec`,
`lint-knowledge`, `lint-build`, `lint-seeds`, `lint_credentialed_skills`, `test-lint-credentialed-skills`)
then delegates to the shipped `pre-pr.py`. Do not make any shipped hook/command/template reference
`tools/lint-*`, `make build-self`, `docs/specs/`, or `.github/workflows/` — those paths don't exist
in an adopter's repo.

**Repo-gate orchestration is a `tools/` script, never an `agentbundle` package subcommand.** Adding,
removing, or renaming a `python -m agentbundle` subcommand is an adopter-surface change with a release
implication — surface it as an explicit decision before building.

### Shipped pack content carries no internal-governance citations

When authoring anything under `.apm/**` (skills, agents, commands, hooks, `scripts/`, `references/`,
`shared-libs/`, `adapter-root-bins/`), never cite this catalogue's own governance. The four types
to keep out:

1. **RFC numbers** — `RFC-0001`…`RFC-00NN`.
2. **ADR numbers** — `ADR-0001`…`ADR-00NN`.
3. **Spec/plan citations** — `spec § AC15`, `plan §T5 lines 357-362`, `docs/specs/<feature>.md § "Outputs"`.
4. **Internal doc paths** — `docs/specs/…`, `docs/adr/…`, `docs/rfc/…`, `.github/workflows/…`.

Drop the citation, keep the rule: *"Markers are repo-only per RFC-0004"* → *"Markers are repo-only"*.
Where the citation carried a "why", reword to self-contained prose ("by convention", "a known gap").

Allowed in shipped content: generic spec-driven workflow vocabulary (`spec.md`, `plan.md`, the words
"spec" / "plan" / "acceptance criteria"), real external standards (`RFC 9457`, `RFC 8259`), and
functional fixture content (e.g. `- [ ] AC1` rows in test fixtures, where `AC1` is data the parser
consumes, not a citation).

## House style for internal docs

Applies to prose that stays in this repo and never ships: this file, `docs/architecture/`, `docs/specs/`,
RFCs, ADRs, internal READMEs. The adopter-facing version ships in the `user-guide-diataxis` pack's
`new-guide` skill (`references/clear-prose.md`).

- **Write prose that reads like a person wrote it.** Cut hedges ("it's worth noting"), uniform sentence
  rhythm, em-dash overuse, throat-clearing openers, inflated verbs ("leverage", "utilize", "delve").
  Vary sentence length; one claim per sentence; concrete number or example over adjective.
- **Catch structural tells.** Check each draft: does the argument advance paragraph to paragraph, or
  restate? Does each list item earn its slot? Is there a position the text can be disagreed with?
  Is any specific detail grounded (a name, a date, a count), or only performed? Watch for: treadmill
  effect, symmetrical lists that pad a template, false precision, performative thoroughness, nice-nice
  wrap (both sides hedged, no stance).
- **State what is — don't leak rationale or identity.** Cut asides that justify mid-sentence;
  give the "why" its own sentence or drop it. No self-narration ("internally we…", "our goal here is…").
- **Soft-wrap guides.** Under `docs/guides/`, one line per paragraph, blank line between paragraphs,
  list items one line each. Older docs (README, CONVENTIONS) are hard-wrapped near 72 columns; match
  the file you're editing.

## Agents project to multiple adapters — not Claude Code only

The `agent` primitive (e.g. `adversarial-reviewer`, `quality-engineer`) projects to claude-code, kiro,
and codex today; copilot support is addable. Check `docs/contracts/adapter.toml` for the current map.

When reasoning about reviewer/agent reach, the default is "agents reach claude-code + kiro + codex
today (copilot addable)."

`AGENTS.md` is a **Manual** file — `build-self` won't regenerate it once it exists. A fix to the
agent-support statement must edit **both** `packs/core/seeds/AGENTS.md` (the seed) and the working-tree
`AGENTS.md` directly.

## AGENTS.md line caps — enforced by CI

The AGENTS.md hygiene gate enforces: root `AGENTS.md` ≤ 250 lines; every sub-directory
`AGENTS.md` ≤ 150 lines. Exceeding the cap blocks all three CI jobs. Keep files tight:
these files load into agent context; length equals token cost.

## Self-hosting drift — edit the source, not the projection

This repo is self-hosted from `packs/`. Many files are **rendered outputs**, not the source-of-truth.
Editing them directly trips `make build-check`. Full workflow: [`packs/AGENTS.md`](packs/AGENTS.md#self-hosting-projection).

**Always-projected — edit the source:**

| Target (do not edit) | Source |
|----------------------|--------|
| `AGENTS.md`, `CLAUDE.md` | `packs/core/seeds/AGENTS.md` |
| `docs/CONVENTIONS.md` | `packs/core/seeds/docs/CONVENTIONS.md` |
| All adapter skill projections | `packs/<pack>/.apm/skills/<name>/**` |
| All adapter agent / command / hook projections | `packs/<pack>/.apm/{agents,commands,hooks}/...` |

**Manual — edit directly (no build-self needed):**
`docs/CHARTER.md`, `docs/architecture/overview.md`, `docs/specs/README.md`,
`docs/knowledge/patterns.jsonl`, `docs/rfc/README.md`, `docs/adr/README.md`,
`docs/guides/**/README.md`.

**Exception: `.claude/skills/README.md` is canonical (not projected) — edit directly.**

## `docs/guides/` is organized by pack in this repo

This catalogue organizes user docs **by pack**: `docs/guides/<pack>/{tutorials,how-to,reference,explanation}/`
for pack-specific guides; `docs/guides/_shared/{quadrant}/` for cross-cutting ones. The four-type Diátaxis
discipline holds within each pack's subtree. Write guides under the owning pack, or `_shared/` if not
specific to one pack.

The adopter-facing `user-guide-diataxis` seed scaffold ships a by-quadrant `docs/guides/{quadrant}/` tree
(an adopter is one product, not a catalogue); `docs/CONVENTIONS.md` §5c is projected and stays
by-quadrant for adopters. The `new-guide` skill is layout-aware and writes per-pack when the repo
is organized that way.

## Install-test coverage rule

Tests that exercise an on-disk projection layout, the per-pack orphan scanner, or the install
handler's adapter-resolution path **must parametrize over every shipped adapter** — not just the
default. Each adapter projects to a different directory layout and the per-pack scanner's
primitive-name heuristic interacts differently with each shape.

Opt-out: tests scoped to adapter-independent logic (scope-resolution, dependency gates,
state-accumulation) may skip parametrization; the test's docstring must say so.

**Reference shape:** `packages/agentbundle/tests/integration/test_multi_pack_install.py`.
`packages/agentbundle/agentbundle/_data/adapter.toml` is the source of truth for which adapters ship;
the test module derives `_SHIPPED_ADAPTERS` from it via `scope.shipped_adapters_from_contract()` —
adding a new `[adapter.<name>]` table expands every parametrized test in the same PR.
Adapter-specific behaviour gaps are pinned as their own tests rather than silently elided.

## New tool scripts: Python, not bash

New additions to `tools/` must be pure-stdlib Python (`.py`). Existing `.sh` files stay; the rule
applies forward. Path triggers in `.github/workflows/docs.yml` must match `python3 <script>`.

## Windows / cross-OS compatibility

Applies to all new code. Production code (`packages/agentbundle/agentbundle/`) is already clean.

- **Encoding:** `Path.read_text()` / `Path.write_text()` / `open()` for text must always pass
  `encoding="utf-8"`. Exception: `read_bytes()` / `write_bytes()` are inherently correct.
- **Symlinks:** wrap `os.symlink()` in `try/except OSError: pytest.skip("symlinks not available")`.
  Production code uses `_is_equivalent_claude_md_shape()` (`self_host.py`) for three equivalent shapes.
- **POSIX-only assertions:** wrap inode checks (`st_ino`), nanosecond mtimes (`st_mtime_ns`), and
  permission-bit assertions in `if sys.platform != "win32":`. Gate `os.chmod()` with `if os.name == "posix":`.
- **Paths:** use `pathlib.Path` or `os.path.join`. No string concatenation with `/`, no
  `os.environ["HOME"]`, no hardcoded `/tmp`.
- **Subprocess:** list form only, never `shell=True`. Do not invoke `which`, `grep`, `find`, `sed`,
  `awk`, `make`, `sh`, or `bash` via subprocess in portable code.
