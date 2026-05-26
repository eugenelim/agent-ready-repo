# RFC-0009: Migrate Codex adapter from managed-block AGENTS.md to native .agents/skills/

- **Status:** Accepted
- **Author:** eugenelim
- **Date opened:** 2026-05-25
- **Date closed:** 2026-05-25
- **Related:** [RFC-0001](0001-bundle-distribution-by-adapter-spec.md)
  introduced the per-IDE adapter contract this RFC modifies.
  [RFC-0005](0005-user-scope-hook-support.md) is precedent for the same
  shape of change (flip a `[[adapter.<name>.projection]]` entry, shrink
  the adapter, update tests). Complements PR #101 (drop `.claude/`
  click-targets from seed prose).

## Contents

- [Summary](#summary)
- [Motivation](#motivation)
  - [Current state](#current-state)
  - [New capability](#new-capability)
- [Proposal](#proposal)
  - [Decision](#decision)
  - [Adapter contract change](#adapter-contract-change)
  - [Adapter implementation change](#adapter-implementation-change)
  - [Failure modes](#failure-modes)
  - [Tests](#tests)
  - [Migration path](#migration-path)
- [Alternatives considered](#alternatives-considered)
- [Drawbacks](#drawbacks)
- [Secondary benefits](#secondary-benefits)
- [Prior art](#prior-art)
- [Unresolved questions](#unresolved-questions)
- [Follow-on artifacts](#follow-on-artifacts)

## Summary

Codex now natively discovers skills at `.agents/skills/<name>/SKILL.md`
via filesystem scan + YAML description-match — the same model Claude
Code (`.claude/skills/`) and Kiro (`.kiro/skills/`) already use. Our
adapter currently inlines a one-line description per skill into a
managed block in Codex's `AGENTS.md`, dropping the body. Propose
flipping the `skill` primitive's Codex projection from
`managed-block-inline` to `direct-directory` (target `.agents/skills/`)
so Codex receives the full skill body the same way Claude Code and Kiro
do. No code changes in this PR; this RFC is the decision artifact.

## Motivation

### Current state

The Codex adapter
(`packages/agentbundle/agentbundle/build/adapters/codex.py`,
`docs/contracts/adapter.toml` § `[[adapter.codex.projection]]`)
projects the `skill` primitive as:

```toml
[[adapter.codex.projection]]
primitive = "skill"
mode = "managed-block-inline"
target-path = "AGENTS.md"
managed-block-delimiter-start = "<!-- agent-skills:start -->"
managed-block-delimiter-end = "<!-- agent-skills:end -->"
on-conflict = "preserve-outside-block"
```

`_project_managed_block` in `codex.py` reads each pack's
`skills/<name>/SKILL.md`, extracts the YAML `description` field, sorts
the resulting list, and splices `- **{name}** — {description}` lines
into AGENTS.md between the delimiters. The full skill body
(instructions, scripts, references) lands in `dist/` only as the
description teaser; Codex users never see the actual workflow content
that the other adapters' users do.

The `agent` primitive is `dropped` for Codex (no specialist-subagent
slot in Codex at time of writing); `hook-body` is `direct-file`;
`hook-wiring` and `command` are `dropped`. This RFC touches only the
`skill` projection entry.

### New capability

Per [Codex's skills documentation](https://developers.openai.com/codex/skills),
Codex now discovers skills at `.agents/skills/<name>/SKILL.md` using
filesystem scan + YAML frontmatter description-match. The frontmatter
shape Codex expects (`name:`, `description:`, free-form Markdown body)
matches what our existing skill primitive already produces — confirmed
by spot-comparing `packs/core/.apm/skills/work-loop/SKILL.md` and the
extractor in `codex.py:_extract_description` against the schema in the
linked docs. No per-skill rewrite is required; the migration is
adapter-side only.

This converges three of the four target IDEs on the same filesystem
discovery model:

| Adapter | `skill` projection target | Mode |
| --- | --- | --- |
| `claude-code` | `.claude/skills/` | `direct-directory` |
| `kiro` | `.kiro/skills/` | `direct-directory` |
| `copilot` | `.github/instructions/` | `instruction-file` |
| `codex` (today) | `AGENTS.md` (managed block) | `managed-block-inline` |
| `codex` (proposed) | `.agents/skills/` | `direct-directory` |

## Proposal

### Decision

**Migrate to `.agents/skills/`.** Status quo deprives Codex users of
the full skill body and forces seed prose to choose between
adapter-agnostic (the path PR #101 takes, dropping all click-targets)
and adapter-aware (a path-map mechanism we'd rather not build).
Migrating closes both gaps in one move and aligns Codex with the other
adapters' native discovery model. The proposal pairs the contract
flip with a one-shot adapter-side cleanup that empties the legacy
`AGENTS.md` managed block on the first post-migration install (see
§ Migration path); this avoids the "stale block drifts from
`.agents/skills/` reality forever" failure mode the merged-block-only
or both-surfaces alternatives suffer.

### Adapter contract change

In `docs/contracts/adapter.toml`, replace:

```toml
[[adapter.codex.projection]]
primitive = "skill"
mode = "managed-block-inline"
target-path = "AGENTS.md"
managed-block-delimiter-start = "<!-- agent-skills:start -->"
managed-block-delimiter-end = "<!-- agent-skills:end -->"
on-conflict = "preserve-outside-block"
```

with:

```toml
[[adapter.codex.projection]]
primitive = "skill"
mode = "direct-directory"
target-path = ".agents/skills/"
on-conflict = "prompt-then-preserve"
```

This entry is structurally identical (modulo target path) to the
existing Claude Code and Kiro entries — no new `mode` value, no schema
extension. The `managed-block-delimiter-start` / `-end` fields stay in
the contract schema because the `managed-block-inline` mode itself
remains valid for other primitives or future adapters.

**Pre-existing `.agents/skills/` content.** `prompt-then-preserve`
fires per-file the same way Claude Code's `.claude/skills/` entry
does — if the adopter has authored their own `SKILL.md` at a colliding
path, the install prompts and preserves the existing file by default.
No tree-level prompt; granularity matches every other
`direct-directory` projection in the contract. Adopters who want pack
skills to win can re-run install with the documented overwrite flag
(same one the other `direct-directory` adapters use).

### Adapter implementation change

In `packages/agentbundle/agentbundle/build/adapters/codex.py`
(149 lines today):

- The follow-on spec **adds a `direct-directory` branch** that calls
  the same tree-copy logic Claude Code and Kiro use
  (`shutil.copytree(..., symlinks=True)` per `claude_code.py:63-72`
  and `kiro.py:303-309`). The symlink-pass-through is a
  path-traversal-safety invariant the spec pins explicitly — it does
  not get reinvented on the Codex side.
- The `skill`-side managed-block path becomes unreachable. The
  follow-on spec removes `_project_managed_block` (codex.py:66-112,
  47 lines, including the delimiter-collision guard inline at
  91-99) and `_extract_description` (codex.py:115-132, 18 lines) —
  65 lines of function body across the two — in the same change.
- `_splice_managed_block` (codex.py:135-149) is **retained for one
  minor release** as the engine of the one-shot strip described in
  § Migration path. It is removed in the release that drops the
  migration cleanup itself. The legacy delimiter literals
  (`<!-- agent-skills:start -->` / `<!-- agent-skills:end -->`) are
  hardcoded in `codex.py` during the transition; they are not
  re-introduced into the contract.
- `project_packs` has external callers today —
  `packages/agentbundle/agentbundle/build/self_host.py:219`
  invokes it during self-host AGENTS.md composition, and
  `packages/agentbundle/agentbundle/build/tests/test_adapter_codex.py`
  exercises it directly (lines 103-126). The follow-on spec must
  pick: keep `project_packs` as the multi-pack public entry point
  (changing only what it dispatches to internally), or migrate
  `self_host.py:219` to call a different surface and update the test
  sites. The author leans "keep `project_packs` as the entry point";
  the spec freezes the choice.
- `_iter_primitives`, the phase-order iteration, and the
  `direct-file` branch for `hook-body` are unchanged.

### Failure modes

These are cases the merged-block path masks today and that the
follow-on spec must explicitly land on — either by handling them or
by declaring them out of scope and documenting the limit:

- **Orphan-skill cleanup.** `managed-block-inline` rewrites the entire
  block every run, so a skill removed from a pack disappears
  automatically. `direct-directory` does not — a skill projected in
  run N and removed before run N+1 leaves a stale `<out>/.agents/
  skills/<old-name>/SKILL.md` that Codex's filesystem scan continues
  to find. This is a cross-cutting gap: Claude Code and Kiro
  adapters have it today (`grep _project_direct_directory` confirms
  no orphan sweep), and merging Codex into the same shape inherits
  the gap rather than introducing it. The follow-on spec must pick:
  add a shared "scan target-dir, delete entries not in source set"
  step (with a test that asserts orphans are removed), or document
  the leak as a known limitation and file a follow-on for all three
  adapters in one shot.
- **Same-name skill across two packs.** Today's merged-block path
  concatenates lists across packs and sorts, producing two
  `- **same-name** — ...` lines (ugly but not destructive). Under
  `direct-directory`, the second pack's tree silently overwrites the
  first via `shutil.rmtree` + `copytree`. The analogous case for
  Kiro agents is **documented as a known limitation** at
  `packages/agentbundle/agentbundle/commands/install.py:1201` —
  silent overwrite, not an install-time error. So there is no
  enforcement precedent to copy. The follow-on spec must pick: (a)
  install-time error (changes both Codex skills and the Kiro-agent
  precedent in one move), (b) deterministic last-wins with a pinned
  ordering rule and a test (matches the Kiro-agent status quo,
  documents it consistently), or (c) accept the silent overwrite
  and inherit the known limitation. The author leans (b) — fix the
  observability via the deterministic rule rather than enforcement
  — but the choice belongs in the spec, not here.
- **Symlink / path-traversal safety.** The delimiter-collision
  validator goes away; the replacement guarantee is "uses
  `shutil.copytree(..., symlinks=True)` like the Claude Code and
  Kiro adapters" (so symlinks copy through as symlinks, not as
  dereferenced bodies). The follow-on spec pins this as an
  invariant and adds a fixture-based test (a symlinked skill body
  does not dereference at install time).
- **Hand-edited content between legacy delimiters is lost.** The
  one-shot strip (§ Migration path) rewrites the entire region
  between `<!-- agent-skills:start -->` and `<!-- agent-skills:end -->`
  to empty before deleting the delimiters themselves — adopter
  notes intermingled with the auto-generated list are destroyed.
  This is **continuous with the pre-migration behaviour** — the
  managed block has always been wholesale-rewritten on every
  install (`codex.py:_splice_managed_block`) — so adopters who
  followed the documented "edit outside the block" rule lose
  nothing. The follow-on spec's strip-step test must include a
  fixture with non-list content between the delimiters to make
  the loss explicit and intentional; Unresolved questions #4 (the
  `--keep-legacy-codex-block` escape hatch) addresses adopters who
  knowingly broke the rule.

### Tests

Existing Codex coverage spans **two test roots**: behaviour and
contract tests at `packages/agentbundle/agentbundle/build/tests/`,
plus the CLI / integration tests at
`packages/agentbundle/tests/`. The first root contains real
projection-output assertions that the follow-on spec must update,
not introduce.

**Tests removed by the migration** (managed-block-specific):

| Test | Currently asserts |
| --- | --- |
| `build/tests/test_adapter_codex.py::test_skill_description_appears_in_managed_block` | The `- **{name}** — {description}` line for each skill appears between the delimiters in projected `AGENTS.md`. |
| `build/tests/test_adapter_codex.py::test_outside_block_preserved` | Content outside the delimiters survives an install. |
| `build/tests/test_adapter_codex.py::test_idempotent` | Two consecutive installs produce byte-identical `AGENTS.md`. |
| `build/tests/test_adapter_codex.py::test_project_packs_aggregates_skills_before_splicing` (lines 103-126) | `project_packs` aggregates skills from multiple pack source-dirs into the same managed block, sorted, idempotent. |
| `build/tests/test_security.py::test_skill_description_with_end_marker_is_rejected` (lines 80-93) | A skill whose description carries a delimiter literal raises `ValueError`. |

These assertions are tightly coupled to the managed-block shape and
have no analogue post-migration. They go away in the same change
that removes `_project_managed_block`.

**Tests retained without behavioural change**:

| Test | Why it survives |
| --- | --- |
| `tests/unit/test_pipeline_phase_order.py::test_codex_project_iterates_in_phase_order` | The recorder captures **primitive names**, not modes (`test_pipeline_phase_order.py:83-86` — `recorded.append(primitive)`); the test pins the iteration order of primitives through the adapter, which the migration does not change. The post-migration assertion that `skill` projects through `direct-directory` lives in the new byte-identical projection-output test below, not here. |
| `tests/unit/test_list_targets_cmd.py` (codex at lines 53, 122) | `list-targets` reads the contract, not the implementation. |
| `tests/unit/test_render.py::test_list_adapters_matches_runtime_registry` (lines 16-23) | The four-adapter set is unchanged. |
| `tests/integration/test_zipapp.py:71` | CLI smoke for `list-targets`; unrelated to projection output. |

**Required new tests in the follow-on spec** (non-negotiable
Acceptance Criteria, not "recommended"):

- **Byte-identical projection.** A fixture pack with two skills,
  projected through the Codex adapter, must produce, at
  `<out>/.agents/skills/<name>/SKILL.md` for each skill, a file
  whose `read_bytes()` equals the source `read_bytes()`. This is
  the only test that pins the migration's stated motivation (the
  full body reaches Codex users).
- **Symlink pass-through.** A fixture pack whose skill body
  contains a symlink projects through the Codex adapter without
  dereferencing the symlink at install time (per § Failure modes —
  symlink safety; mirrors `shutil.copytree(..., symlinks=True)`
  semantics from Claude Code and Kiro adapters).
- **Migration strip — happy path.** A fixture `AGENTS.md`
  containing the legacy managed block has, after one install:
  (a) no `<!-- agent-skills:start -->` substring remaining; (b) no
  `<!-- agent-skills:end -->` substring remaining; (c) all content
  outside the original delimiter region preserved verbatim.
- **Migration strip — already-clean.** A fixture `AGENTS.md` with
  no delimiters is byte-identical after install — the strip step
  is a no-op when there is nothing to strip.
- **Migration strip — idempotency.** Two consecutive installs
  against a fixture `AGENTS.md` containing the legacy block
  produce byte-identical output, with the second install a
  pure no-op.
- **Migration strip — non-list content lost (explicit).** A
  fixture `AGENTS.md` containing hand-edited prose **between** the
  legacy delimiters has, after install: no remaining trace of the
  inter-delimiter prose (the loss is documented in § Failure modes
  and tested here so it cannot accidentally regress to silent
  preservation).

**Optional but recommended observability check.** Extend
`lint-agents-md.py` (or the closest existing adapter linter under
`tools/`) with a warning when `<!-- agent-skills:start -->` is
present in a projected `AGENTS.md` whose Codex `skill` projection
is `direct-directory` — closes the inconsistent-state observability
gap the merged-block path leaves behind for adopters between the
contract flip and the next install.

### Migration path

Adopters who installed our packs on Codex before this change have a
populated managed block in their `AGENTS.md` between the
`<!-- agent-skills:start -->` / `<!-- agent-skills:end -->`
delimiters. The adapter cannot truthfully claim the block is "inert"
after migration — Codex reads `AGENTS.md` as prose alongside the
filesystem-scanned `.agents/skills/`, so a stale list of skill
descriptions would drift from `.agents/skills/` reality permanently.
The proposal owns this by pairing the contract flip with a one-shot
adapter-side cleanup:

**On the first install after migration**, if
`<!-- agent-skills:start -->` is present in the projected
`AGENTS.md`, the Codex adapter strips the block in place (delimiters
and all) before doing any `direct-directory` projection. Mechanics:
the existing `_splice_managed_block` helper is repurposed to splice
**empty** content between the delimiters, then a follow-up pass
deletes the empty-delimiter pair. The operation is idempotent — a
second install finds no delimiters and is a no-op. After one minor
release the cleanup step itself is removed; `_splice_managed_block`
follows it.

This is a single committed migration story, not a menu. For
reference, two paths were rejected:

- **Leave the block as-is.** Promised "inert" but the block keeps
  reading as prose to Codex; the drift accumulates with every pack
  update. Rejected for the inconsistency it bakes in.
- **Support both surfaces — managed block AND `.agents/skills/` for
  one minor.** Adopters who notice both copies have to ask which is
  authoritative; the adapter has to regenerate the block on every
  refresh; cost > benefit. Rejected.

The adapter strip is intentionally narrow: it touches the
delimiter-bounded region only, leaves everything else in `AGENTS.md`
alone, and runs at install time when adopter consent is already in
play. It is not a generalised "rewrite my AGENTS.md" verb.

## Alternatives considered

**Status quo — keep merging into AGENTS.md.** Pros: zero migration
cost, no adopter surprise on existing installs. Cons: Codex users
permanently receive a description-only teaser, never the workflow body;
seed prose continues to need adapter-aware rewriting (or the workaround
PR #101 takes, dropping click-targets entirely). Status quo locks
Codex into a strictly worse model than its own native capability now
supports — not chosen.

**Support both — project to `.agents/skills/` AND maintain the managed
block.** Pros: graceful migration, both old and new discovery surfaces
work. Cons: doubles the projection work, requires regenerating the
block on every refresh, and adopters who notice both copies will
reasonably ask which is authoritative. Cost > benefit unless we learn
Codex installs exist where `.agents/skills/` is unavailable
(Unresolved questions #1). Not chosen.

## Drawbacks

- **Adapter mutates `AGENTS.md` once on migration.** The strip step
  (§ Migration path) writes to a file the adapter no longer normally
  touches. Adopters who keep their `AGENTS.md` under tight diff
  review will see a one-time `AGENTS.md` change in the migration
  install. Mitigated by: the strip is narrowly scoped to the
  delimiter region, idempotent, and ships behind the same install
  consent surface as every other adapter file change.
- **Migration helper retained for one minor.** `_splice_managed_block`
  stays in `codex.py` until the strip step itself is removed in the
  following release. Until then, "the adapter doesn't speak managed
  blocks" is an approximation, not the full truth.
- **Codex schema commitment.** We commit to Codex's
  `.agents/skills/<name>/SKILL.md` shape staying stable. If OpenAI
  moves the layout, we migrate again. Mitigated by: the change is
  isolated to one adapter-contract entry plus an adapter-specific
  function — small blast radius.
- **Cross-cutting failure modes inherited.** Adopting
  `direct-directory` brings Codex into the orphan-skill-cleanup and
  same-name-collision gaps Claude Code and Kiro silently have today
  (§ Failure modes). The Codex-side behaviour is decided by
  Unresolved questions #2 (lean: deterministic last-wins) and #3
  (lean: shared cleanup for all three adapters); resolving them may
  leave Codex's gap shape different from the Claude Code / Kiro
  status quo until those adapters get a follow-on. This RFC's
  contribution is to surface the gaps, not resolve them
  adapter-by-adapter.

## Secondary benefits

- Eliminates the "links in AGENTS.md pointing to merged-block content
  nobody can actually click" path-map case that PR #101 worked around
  by dropping click-targets entirely. This RFC and PR #101 together
  erase two of the path-map RFC's largest scope drivers (per-IDE link
  rewriting for skill references; the awkward "AGENTS.md links to its
  own merged-block content" case).
- Mental model collapses from "four adapters, four `skill` shapes" to
  "three converged on `direct-directory`, plus Copilot's
  instructions-flavored variant". Simpler for both adopters and
  maintainers.

## Prior art

- [RFC-0001](0001-bundle-distribution-by-adapter-spec.md) (Accepted,
  2026-05-22) introduced the per-IDE adapter contract this RFC
  modifies. The `mode` enum (`direct-directory`, `direct-file`,
  `managed-block-inline`, `merge-json`, `dropped`) was deliberately
  extensible for this kind of evolution.
- [RFC-0005](0005-user-scope-hook-support.md) (Accepted) reshaped
  `hook-body` and `hook-wiring` projections with the same change shape
  this RFC proposes: flip an `[[adapter.<name>.projection]]` entry,
  shrink the adapter, update the touching tests, regenerate `dist/`.
  Precedent for the migration mechanics.
- [Codex skills docs](https://developers.openai.com/codex/skills) —
  the `.agents/skills/<name>/SKILL.md` discovery model this RFC aligns
  with. Frontmatter schema matches our existing skill primitive.
- [Claude Code skills](https://code.claude.com/docs/en/skills) and
  [Kiro skills](https://kiro.dev/docs/skills/) — both consume the same
  filesystem-scan + YAML model. After this RFC, Codex joins them.
- [GitHub Copilot custom instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
  — different shape (`.github/instructions/` with `applyTo:`
  frontmatter); intentionally not converged with the other three.

## Unresolved questions

1. **Are there Codex installs or enterprise policies where
   `.agents/skills/` is unavailable, requiring fallback to the
   merged-block model?** Author's lean: **no, by Codex's own docs** —
   the directory is the documented loading mechanism, not an opt-in.
   This assumption deserves explicit confirmation from a reviewer with
   Codex enterprise-deployment context before the RFC moves out of
   Draft.

2. **Same-name skill collisions across packs — error, deterministic
   last-wins, or accept the silent overwrite?** Surfaced in § Failure
   modes. The analogous Kiro-agent case at
   `packages/agentbundle/agentbundle/commands/install.py:1201` is
   today a *documented known limitation* (silent overwrite), not an
   enforcement, so there is no parity case to mirror as-is. Author's
   lean: **deterministic last-wins with a pinned ordering rule and a
   test** — fixes Codex's observability problem without
   simultaneously changing the Kiro precedent in this RFC's scope.
   Reviewers with pack-composition use cases should weigh in before
   the follow-on spec freezes the behaviour. Reviewers should also
   weigh in on whether the Kiro case gets the same fix in a
   follow-on PR.

3. **Cross-cutting orphan-skill cleanup — one PR or three?** Surfaced
   in § Failure modes. The gap is shared with Claude Code and Kiro
   today. Author's lean: **one shared cleanup helper introduced in
   the Codex follow-on spec, applied to all three `direct-directory`
   adapters in the same PR.** Open for reviewer pushback if "ship
   Codex first, retrofit the others later" is preferred.

4. **Migration cleanup behind a flag?** The one-shot strip in
   § Migration path runs unconditionally on the next post-migration
   install. Author's lean: **unconditional is correct** — adopters who
   want to preserve their stale block can copy it elsewhere before
   the install — but a `--keep-legacy-codex-block` escape hatch is
   trivial to add if a reviewer surfaces a use case.

## Follow-on artifacts

Filled in on acceptance. Expected shape:

- Spec: `docs/specs/codex-native-skills/` — implementation contract.
  Provisional tasks (the spec author decides final shape and
  decomposition):
  - **T1.** Flip the `[[adapter.codex.projection]]` entry for `skill`
    in `docs/contracts/adapter.toml` to `direct-directory`.
  - **T2.** Rewrite `codex.py` to route `skill` through the shared
    `direct-directory` path (with `shutil.copytree(...,
    symlinks=True)` invariant pinned per § Failure modes); collapse
    or remove `project_packs` per § Adapter implementation change;
    retain `_splice_managed_block` for T3.
  - **T3.** Add the one-shot migration cleanup that strips the
    legacy managed block on first post-migration install
    (§ Migration path) — includes the idempotency and fixture-based
    tests called out in § Tests.
  - **T4.** Add the required byte-identical projection-output test
    (§ Tests) as a non-negotiable Acceptance Criterion.
  - **T5.** Pick and implement the same-name-collision policy
    (§ Unresolved questions #2) with the corresponding test.
  - **T6.** Land the cross-cutting orphan-cleanup helper across the
    three `direct-directory` adapters, or document the limit and
    file a separate follow-on per § Unresolved questions #3.
  - **T7.** Optional but recommended: extend `lint-agents-md.py`
    with the observability check called out in § Tests.
  - **T8.** Regenerate `dist/` and confirm
    `<dist>/codex/.agents/skills/<name>/SKILL.md` lands for each
    fixture skill; changelog entry per RFC-0001
    § upgrades-granularity.
- No ADR — the decision is small enough that the RFC plus the
  follow-on spec capture everything; an ADR would be ceremony.
- Adapter PR opens against the spec; cite this RFC and RFC-0001 as
  the contract authority.
