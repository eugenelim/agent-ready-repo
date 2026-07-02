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
(tracked at `docs/backlog.md` § `apm-leak-lint-rfc`). Until then this is a
hand-checked authoring rule.

## House style for our own internal docs

This covers prose that stays in this repo and never ships to adopters: this
file, `docs/architecture/`, `docs/specs/`, RFCs and ADRs, internal READMEs.
The adopter-facing version of this craft ships in the `user-guide-diataxis`
pack's `new-guide` skill (`references/clear-prose.md`); keep each in its own
home rather than duplicating.

- **Write prose that reads like a person wrote it.** Cut the tells that make
  text feel machine-made: hedges ("it's worth noting"), uniform sentence
  rhythm, em-dash overuse, the rule of three on a loop, throat-clearing
  openers, inflated verbs ("leverage", "utilize", "delve"). Vary sentence
  length, keep one claim per sentence, and prefer a concrete number or example
  over an adjective.
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
| `.agents/skills/<name>/**`           | `packs/<pack>/.apm/skills/<name>/**`                         |
| `.codex/agents/<name>.toml`          | `packs/<pack>/.apm/agents/<name>.md`                         |
| `.codex/hooks.json`                  | `packs/<pack>/.apm/hook-wiring/*.toml`                       |

**The workflow when you touch any of the above:**

1. Edit the seed file (under `packs/<pack>/seeds/...`), *not* the
   projected output.
2. Run `make build-self` to regenerate every projected path from its seed.
   **Gotcha:** `build-self` refuses on a dirty working tree (`is_dirty_tree`
   is true for *any* non-empty `git status --porcelain`), so editing a seed in
   step 1 always trips it. Either commit the seed edits first, or run
   `FORCE=1 make build-self` — `FORCE=1` overrides the dirty-tree check only,
   and is the right call when the tree is dirty *because* you just edited seeds.
   Direct equivalent (when Make is unavailable):
   ```bash
   python3 tools/build_gate_chain.py build-self --force --packs-dir packs
   ```
   **Critical ordering for mixed-edit sessions (seed + non-seed pack source):**
   When a session edits both seeds *and* non-seed pack source files (e.g.,
   `.apm/**` files, `pack.toml`, user-libs) in the same working tree, run
   `build-self --force` AFTER all edits are applied — not between them. Build-self
   is a full pack-build pipeline that can regenerate files in `packs/` from
   cached or templated sources, silently reverting edits made before it ran. The
   safe pattern: apply all edits → `FORCE=1 make build-self` → verify with
   `git status` that the edits survived → `make build-check` → commit.
   **Vendored copies and canonical sources (credbroker example):**
   `packs/credential-brokers/.apm/user-libs/credbroker/` is byte-synced from
   `packages/credbroker/credbroker/` (the canonical pip package source) by
   build-self; `build-check` hard-fails on any divergence. To edit these files,
   always edit `packages/credbroker/credbroker/*.py` (the canonical source) and
   let `build-self --force` propagate to the vendored copy — never edit the
   `.apm/user-libs/` copy directly.
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

## Pack versioning — non-cosmetic pack changes bump the pack version

A **non-cosmetic** update to any `packs/<pack>/` content must bump that
pack's version in **both** `packs/<pack>/pack.toml` (`[pack]` `version`, not
the separate `[pack.adapter-contract]` `version`) and
`packs/<pack>/.claude-plugin/plugin.json` (`version`), so adopters pulling
the catalogue see the change reflected. After bumping, `make build-self`
re-aggregates `marketplace.json`. *Non-cosmetic* = any change to behavior,
doctrine, or shipped prose an adopter reads (a sharpened reviewer, a new
skill step, a reworded convention). **Cosmetic-only** changes — typos,
whitespace/formatting, comment reflow with no semantic change — need no bump.
When in doubt, bump: a spurious patch bump is cheaper than a silently-stale
version.

**Bump-per-PR: take the *next* version, never ride an unreleased one.** The
version is assigned at merge, not accumulated — `pack.toml` holds the last
merged change's version, and `docs/product/changelog.md`'s single `[Unreleased]`
heading is not an accumulate-then-cut pool (each entry cites its own target
version inline). So read the current `pack.toml` version and take the next
SemVer increment; two features never share one. (PE: `0.5.1`→`0.6.0` for
product-rungs #379, then `0.6.0`→`0.7.0` for `frame-domain` — not a ride-along.)

**A user-scope pack** (anything outside `_DEFAULT_SELF_HOST_PACKS` = `core` /
`governance-extras` / `user-guide-diataxis`) bumps the same three surfaces —
`pack.toml`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` —
even though its skills don't project into `.claude/`. `marketplace.json`
aggregates the version from `plugin.json`, so run `make build-self FORCE=1` after
the bump to re-aggregate it, or `build-check` red-fails on stale drift.

> **Governance note (2026-06-12).** The `work-loop` light/full-mode
> *mechanics summary* was thinned out of the CONVENTIONS seed
> (`packs/core/seeds/docs/CONVENTIONS.md` § Light and full modes), leaving
> the principle plus a pointer to the `work-loop` skill as the sole owner of
> mode mechanics. This was an **owner-directed edit made in lieu of a
> separate `update-conventions` RFC** — recorded here per the repo's
> convention that substantive CONVENTIONS edits leave a governance trace.
> Full retirement of mode mechanics from CONVENTIONS is deferred to its own
> future RFC. (Provenance lives here, repo-internal, rather than in the seed
> itself, which ships to adopters who receive none of the governance it was
> written under.)

## Eval coverage is part of pack work — build or update the harness

A new pack, or a **non-cosmetic** update to an existing one, must also build
or update that pack's **eval harness**. This is the standing default the
[`pack-eval-coverage-rollout`](docs/backlog.md) backlog item is rolling across
the catalogue, made a rule here so it stops being a one-off. Per the
[`pack-activation-evals` spec](docs/specs/pack-activation-evals/spec.md):

- **Tier-A activation** — `evals/eval_queries.json` (~8–10 should-trigger +
  ~8–10 near-miss should-NOT-trigger queries) plus a `[pack.evals]` block
  listing **every user-triggered skill**. Exclude only reviewer-internal /
  non-prompt skills (`security-checklists`, `work-loop`), as `core` does.
- **Tier-4 LLM-judge rubric** — `evals/evals.json` (`expected_output` +
  `assertions`) for **each judgment/authoring skill** — one that produces a
  spec, diagram, critique, guide, or intent by judgment, with no deterministic
  artifact.
- **Tier-B-lite** — additionally an `expect` block + an `evals/files/` fixture
  **where the skill is deterministic** (it runs a script and emits a checkable
  artifact, as the `converters` skills do).

Then **verify the harness actually works** by running it in Tier-B light mode:

```bash
python tools/run-pack-evals.py --pack <pack> --mode judge \
  --judge-adapter claude-code --artifacts <file>
```

This points the LLM-judge — a different lens (the rubric) on the same model
running the session — at a good and a weak artifact. It is a lightweight
smoke-check that the rubric loads and discriminates (good artifact PASS, weak
artifact FAIL), **not** a calibration gate: report-only, like the rest of the
harness. The full per-pack sweep, the calibration baseline, and any
report-only→gating promotion stay the scheduled `pack-evals.yml` workflow's
job — that detail lives in the spec and the backlog item, not here.

## Authoring or editing a skill

Skills live under `packs/<pack>/.apm/skills/<name>/SKILL.md` (the seed)
and project to `.claude/skills/<name>/SKILL.md` and
`.agents/skills/<name>/SKILL.md`. Edit the seed, not the projection.
After any edit, run `make build-self` to regenerate the
projections, then `python3 tools/lint-skill-spec.py` to confirm the
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

The mechanics above are linted; the **craft** is not, so hold it in your
head while authoring — the canonical rules live in
[`.claude/skills/README.md` § Authoring skills](.claude/skills/README.md#authoring-skills):

- **The frontmatter `description` is the activation trigger surface.** It
  alone decides whether the right skill fires (and the wrong ones don't) —
  write it as a sharp, differentiable trigger, not a summary.
- **Keep the body terse — the token budget is real.** A skill loads into
  context when triggered; bloat crowds out the user's actual task. Push
  depth into `references/` the body links on demand, not the body itself.
- **Keep the body disjoint from the trigger.** It answers *what to do once
  invoked* (preconditions, judgment, procedure); it must not restate *when*
  to invoke — that is the `description`'s job.
- **No internal-governance citations** — per *Shipped pack content carries
  no internal-governance citations* above; that rule applies to every
  SKILL.md body and its `references/`, `scripts/`, and `assets/`.

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
