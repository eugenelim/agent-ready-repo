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

**Repo-gate orchestration is a `tools/` script, never an `agentbundle` package
subcommand.** Same rule applied to *chaining* the gates: the make-free
`tools/build_gate_chain.py` (`build-self` / `build-check`, which the Makefile
targets route through) lives in `tools/` as a sibling of
`tools/pre-pr-catalogue.py` — **not** as a `python -m agentbundle.build`
subcommand — precisely because `build-check` spawns repo-only scripts
(`tools/pre-pr-catalogue.py`, the projected `.claude/skills/.../*.py` linters)
that never ship. The reusable engine (`lint-packs` / `build` / `check` / `self`)
stays in the package as public subcommands; the repo-specific wiring does not.
The deeper rule: **don't expand or change the shipped `agentbundle` package's
public CLI/API surface as a side effect of an implementation-shape choice.**
Adding, removing, or renaming a `python -m agentbundle.build` subcommand (or any
adopter-facing artifact) is an adopter-surface change with a release
implication — Surface it as an explicit decision (package-surface vs.
repo-tooling) before building, never let it ride in silently. When the
orchestration has to reach repo-only paths, `tools/` is the answer and the
package stays untouched.

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
possible follow-on, but adding one is a new convention and therefore RFC-gated
(tracked at `workspace.toml [backlog]` as slug `apm-leak-lint-rfc`). Until then this is a
hand-checked authoring rule.

## House style for our own internal docs

This covers prose that stays in this repo and never ships to adopters: this
file, `docs/architecture/`, `docs/specs/`, RFCs and ADRs, internal READMEs.
The adopter-facing version of this craft ships in the `user-guide-diataxis`
pack's `new-guide` skill (`references/clear-prose.md`); keep each in its own
home rather than duplicating.

- **Write prose that reads like a person wrote it.** Cut the vocabulary tells:
  hedges ("it's worth noting"), uniform sentence rhythm, em-dash overuse, the
  rule of three on a loop, throat-clearing openers, inflated verbs ("leverage",
  "utilize", "delve"). Vary sentence length, keep one claim per sentence, and
  prefer a concrete number or example over an adjective.
- **Also catch structural tells — these survive a vocabulary pass.** Check
  each draft against four questions: (1) does the argument advance paragraph to
  paragraph, or restate? (2) does each list item earn its slot, or pad? (3) is
  there a position the text can be disagreed with? (4) is any specific detail
  grounded (a name, a date, a count, an observation), or is specificity only
  performed? Named patterns to watch for: treadmill effect (paragraphs circle
  without arriving), symmetrical lists (identical-length bullets that pad a
  template), false precision ("research shows" with nothing behind it),
  performative thoroughness (seven points when two decide it), nice-nice wrap
  (both sides hedged, no stance), subtext vacuum (written for everyone =
  written for no one).
- **State what is — don't leak rationale or identity.** An aside that
  justifies a choice mid-sentence ("organized this way because…") reads as
  internal thinking spilling onto the page; cut it, or give the *why* its own
  sentence. Drop self-narration too ("internally we…", "our goal here is…").
- **Soft-wrap guides — one logical line per paragraph.** Under `docs/guides/`,
  don't hard-wrap mid-paragraph: one line per paragraph, a blank line between
  paragraphs, list items one line each. It renders identically on GitHub (a
  wrapped newline reads as a space) and stays clean in preview panes that treat
  a single newline as a break. The older docs (README, CONVENTIONS) are still
  hard-wrapped near 72 columns; match the file you're editing.

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

Full projection map, build-self workflow, and how to diagnose drift:
**[`packs/AGENTS.md` § Self-hosting projection](packs/AGENTS.md#self-hosting-projection)**.

**Always-projected paths** (key summary — edit the source, not the target):

| Target (do not edit) | Source |
|----------------------|--------|
| `AGENTS.md`, `CLAUDE.md` | `packs/core/seeds/AGENTS.md` |
| `docs/CONVENTIONS.md` | `packs/core/seeds/docs/CONVENTIONS.md` |
| All adapter skill projections | `packs/<pack>/.apm/skills/<name>/**` |
| All adapter agent projections | `packs/<pack>/.apm/agents/<name>.md` |
| All adapter command / hook projections | `packs/<pack>/.apm/{commands,hooks}/...` |

**Manual paths** (filled-in on disk; pack seed is a placeholder template):
`docs/CHARTER.md`, `docs/architecture/overview.md`, `docs/specs/README.md`,
`docs/knowledge/patterns.jsonl`, `docs/rfc/README.md`, `docs/adr/README.md`,
`docs/guides/**/README.md` — edit these directly, no build-self needed.

**Exception: `.claude/skills/README.md` is canonical (not projected) — edit directly.**

Drift fixed three times already (each time a CI cycle wasted):
- PR #53 — added a row to `docs/rfc/README.md` directly; should have edited the seed.
- PR #57 — added a row to `docs/specs/README.md` directly; same fix.
- PR #67 — edited `.claude/skills/new-spec/SKILL.md` directly; should have edited `packs/core/.apm/skills/new-spec/SKILL.md` then run `make build-self`.

## `docs/guides/` is organized by pack in this repo (not by quadrant)

This catalogue organizes its own user docs **by pack** —
`docs/guides/<pack>/{tutorials,how-to,reference,explanation}/` for
pack-specific guides and `docs/guides/_shared/{quadrant}/` for cross-cutting
ones (install routes, adapter support, the catalogue model, `author-a-skill`).
Per [ADR-0020](docs/adr/0020-per-pack-diataxis-hierarchy-for-guides.md), the
four-type Diátaxis discipline still holds — it just applies *within* each
pack's subtree. When you author a guide here (via `new-guide` or by hand),
write it under the owning pack, or `_shared/` if it isn't specific to one pack.

**Two adopter-facing surfaces deliberately stay organized by quadrant**, and
ADR-0020's "amend `CONVENTIONS.md §5c`" instruction is an **erratum** because
of it:

- The **`user-guide-diataxis` seed scaffold** ships an adopter a
  by-quadrant `docs/guides/{quadrant}/` tree — an adopter is one product, not
  a catalogue of packs. Unchanged on purpose.
- **`docs/CONVENTIONS.md` §5c is projected** from
  `packs/core/seeds/docs/CONVENTIONS.md` (it's in `PROJECTED_README_OVERRIDES`),
  so `make build-self` overwrites any direct edit, and whatever it said would
  **ship to adopters**. §5c therefore stays by-quadrant (adopter-correct), and
  this repo's per-pack convention lives here in `AGENTS.local.md` instead. The
  `new-guide` skill is layout-aware (it writes per-pack when the repo is
  organized that way, by-quadrant otherwise), which is the part of ADR-0020's
  §5c/skill instruction that *was* carried out.

## Pack versioning, skill authoring, eval coverage, and plugin format

All of these live in [`packs/AGENTS.md`](packs/AGENTS.md), which loads
automatically when the working path is under `packs/`.

> **Governance note (2026-06-12).** The `work-loop` light/full-mode
> *mechanics summary* was thinned out of the CONVENTIONS seed
> (`packs/core/seeds/docs/CONVENTIONS.md` § Light and full modes), leaving
> the principle plus a pointer to the `work-loop` skill as the sole owner of
> mode mechanics. This was an **owner-directed edit made in lieu of a
> separate `update-conventions` RFC** — recorded here per the repo's
> convention that substantive CONVENTIONS edits leave a governance trace.
> Full retirement of mode mechanics from CONVENTIONS is deferred to its own
> future RFC.

## Install-test coverage rule

Tests that exercise an on-disk projection layout, the per-pack orphan
scanner (`safety.scan_for_pack_artifacts`), or the install handler's
adapter-resolution path **must parametrize over every shipped
adapter** — today `claude-code`, `kiro`, `codex`, `copilot` — not just
the default. Each adapter projects to a different directory layout
(`.claude/`, `.kiro/`, `.agents/skills/`, `.github/skills/`) and
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

No more copilot orphan-scan asymmetry (docs/specs/copilot-skills-and-web):
copilot's `skill` projection flipped from a flat
`.github/instructions/<primitive>.instructions.md` (whose stem evaded the
per-pack scanner) to a first-class `.github/skills/<name>/SKILL.md` directory
tree, which the scanner's directory heuristic matches by name exactly like
every other adapter. So the cross-pack orphan tests now parametrize **both**
Direction A (skills-only pack) and Direction B (hooks pack) over the full
shipped-adapter set including copilot (`_ADAPTERS_WHERE_GOV_ORPHAN_SCAN_FIRES`
now includes `copilot`). The copilot-specific scanner pin is
`test_copilot_orphan_scan_finds_skills_and_hooks`. When new adapter-specific
orphan-scan gaps are discovered, pin the gap explicitly so it can't drift unnoticed.

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
