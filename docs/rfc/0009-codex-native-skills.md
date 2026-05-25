# RFC-0009: Migrate Codex adapter from managed-block AGENTS.md to native .agents/skills/

- **Status:** Draft
- **Author:** eugenelim
- **Date opened:** 2026-05-25
- **Date closed:**
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
  - [Decision](#decision)
- [Proposal](#proposal)
  - [Adapter contract change](#adapter-contract-change)
  - [Adapter implementation change](#adapter-implementation-change)
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
| `copilot` | `.github/instructions/` | (instructions-flavored, separate shape) |
| `codex` (today) | `AGENTS.md` (managed block) | `managed-block-inline` |
| `codex` (proposed) | `.agents/skills/` | `direct-directory` |

### Decision

**Migrate to `.agents/skills/`.** Status quo deprives Codex users of
the full skill body and forces seed prose to choose between
adapter-agnostic (the path PR #101 takes, dropping all click-targets)
and adapter-aware (a path-map mechanism we'd rather not build).
Migrating closes both gaps in one move and aligns Codex with the other
adapters' native discovery model.

## Proposal

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

### Adapter implementation change

In `packages/agentbundle/agentbundle/build/adapters/codex.py`:

- The `mode == "direct-directory"` branch routes through the same
  tree-copy logic Claude Code and Kiro adapters use. The Codex adapter
  shrinks by roughly 80 lines: `_project_managed_block`,
  `_extract_description`, and `_splice_managed_block` are no longer
  reachable from the `skill` projection and become candidates for
  removal (kept if any other adapter or primitive still needs them; the
  contract validator decides).
- The delimiter-collision validation in `_project_managed_block`
  (refuse skills whose name or description contains a delimiter
  literal) is no longer needed for Codex — no managed block, no
  collision surface.
- `_iter_primitives`, the phase-order iteration, and the
  `direct-file` branch for `hook-body` are unchanged.

### Tests

Files in `packages/agentbundle/tests/` that touch Codex (grep:
`codex`):

| Test | What changes |
| --- | --- |
| `tests/unit/test_pipeline_phase_order.py:131` (`test_codex_project_iterates_in_phase_order`) | Still passes if `_iter_primitives` honors phase order; verify the recorder records the new `direct-directory` call for `skill`. |
| `tests/unit/test_list_targets_cmd.py` (`codex` alongside other adapters at lines 53, 122) | Should pass without change — `list-targets` reads the contract, not the implementation. |
| `tests/unit/test_render.py:21` (adapter-name set) | No change — set unchanged. |
| `tests/integration/test_zipapp.py:71` (round-trip for all four adapters) | Smoke-confirm `<dist>/.agents/skills/<name>/SKILL.md` lands for each fixture skill, replacing the previous AGENTS.md managed-block assertion. |

New test recommended in the follow-on spec: a fixture pack with two
skills projected through the Codex adapter should produce
`<out>/.agents/skills/<name>/SKILL.md` for each, byte-identical to the
source.

### Migration path

Adopters who installed our packs on Codex before this change have a
populated managed block in their `AGENTS.md` between the
`<!-- agent-skills:start -->` / `<!-- agent-skills:end -->`
delimiters. On the next install or `agentbundle adapt`, three options
exist:

- **M1 — clean cut, document it.** New installs emit
  `.agents/skills/<name>/SKILL.md` files; old installs keep their stale
  managed block. The block is inert under the new discovery model —
  Codex reads it as prose, not as skill discovery. Adopters delete the
  block by hand or via a one-shot future `agentbundle adapt` cleanup
  verb (out of scope for this RFC; a separate spec if demand
  materializes).
- **M2 — deprecation window.** Ship the new `direct-directory`
  projection alongside a no-op managed block (empty between delimiters)
  for one minor release, then drop the block entirely. Costs an extra
  adapter code path for the window's duration.
- **M3 — flag-gated.** Keep both projections behind a
  `--legacy-codex-skills` flag for one minor; default flips. Same
  complexity surface as M2.

**Recommendation: M1.** The stale managed block is text, not a behavior
trap; adopters can always re-run `agentbundle install codex` to get the
new layout. M2/M3 add adapter complexity for a temporary state with no
clear adopter benefit. See Unresolved questions #1 for the open
deprecation-window discussion.

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
(Unresolved questions #3). Not chosen.

## Drawbacks

- One-time adopter friction: existing Codex installs keep a now-inert
  managed block in `AGENTS.md` until manually deleted. It is visually
  noisy but functionally harmless.
- The adapter contract retains another asymmetry — Codex's `skill`
  projection mirrors Claude Code and Kiro, but the `agent` primitive
  stays `dropped` for Codex (no specialist-subagent slot in Codex
  today). Accepted: agents aren't natively discoverable on Codex; the
  asymmetry tracks the IDE capability, not our preference.
- We commit to Codex's `.agents/skills/` schema staying stable across
  releases. If OpenAI moves the layout, we migrate again. Mitigation:
  the change is isolated to one adapter-contract entry plus an
  adapter-specific function — small blast radius.

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

1. **Do we need a formal deprecation window for the managed block?**
   Author's lean: **no**. M1 (clean cut) is the default unless a
   reviewer surfaces a concrete adopter-impact scenario we missed. M2
   and M3 are documented above for reference if the lean shifts.

2. **Does `agentbundle adapt` need a "migrate-from-merged-block"
   sub-command for existing adopters?** Author's lean: **no, not for
   v1**. The managed block sits inside `AGENTS.md` alongside content
   the user owns; mechanically stripping it requires the same
   managed-block splice the adapter already does, but in reverse, on a
   tree the adopter has likely edited. Hand-deletion is safer until
   real demand appears. If demand materializes, add it as a small
   follow-on spec.

3. **Are there Codex installs or enterprise policies where
   `.agents/skills/` is unavailable, requiring fallback to the
   merged-block model?** Author's lean: **no, by Codex's own docs** —
   the directory is the documented loading mechanism, not an opt-in.
   This assumption deserves explicit confirmation from a reviewer with
   Codex enterprise-deployment context before the RFC moves out of
   Draft.

## Follow-on artifacts

Filled in on acceptance. Expected shape:

- Spec: `docs/specs/codex-native-skills/` — implementation contract.
  Tasks: (T1) flip the `[[adapter.codex.projection]]` entry in
  `docs/contracts/adapter.toml`; (T2) shrink `codex.py` to route
  `skill` through `direct-directory`; (T3) update the tests called out
  in § Tests; (T4) regenerate `dist/` and confirm
  `<dist>/codex/.agents/skills/<name>/SKILL.md` lands; (T5) changelog
  entry per RFC-0001 § upgrades-granularity.
- No ADR — the decision is small enough that the RFC plus the
  follow-on spec capture everything; an ADR would be ceremony.
- Adapter PR opens against the spec; cite this RFC and RFC-0001 as
  the contract authority.
