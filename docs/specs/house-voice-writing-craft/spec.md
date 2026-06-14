# Spec: house-voice writing craft

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Two readers are under-served by the catalogue's current writing guidance.
The first is an **adopter** who installs the `user-guide-diataxis` pack and
authors guides with `new-guide`: the skill teaches Diátaxis structure and a
short voice rule, but nothing about the prose tells that make docs read like a
machine wrote them. The second is **a maintainer of this repo** writing our own
internal READMEs and repo-only docs: the craft rules we apply by habit live
only in one person's head. This spec ships a generic, attribution-free
clear-prose checklist to the pack for the adopter, records the same craft as
house style for our own docs, and closes the two internal-governance leaks the
guides pack currently carries.

## Boundaries

### Always do

- Write the adopter-facing prose guidance as original text that reasons from
  what an adopter has installed. Reference only artifacts an adopter receives.
- Bump the `user-guide-diataxis` pack version (both `pack.toml` `[pack]`
  `version` and `.claude-plugin/plugin.json`) and re-aggregate via build-self.
- Edit pack content at its `.apm/` source, never the projected `.claude/` or
  `.agents/` copy; run `make build-self` then `make build-check`.

### Ask first

- Removing or rewording the *existing* voice rules already shipped in
  `new-guide` (the knowledgeable-friend rule, the `simply`/`just` and `please`
  anti-patterns). This spec adds to them; it does not replace them.
- Sweeping **all** internal-governance references across `core`'s shipped
  `.apm/**` (work-loop, `pre-pr.py`, receive-brief scripts, session-start hook,
  adapt-to-project). That systemic sweep is large and touches the most
  sensitive pack; it stays deferred to the `.apm/**` leak-lint RFC. The
  specifically-flagged leaks (atlassian `make build-self`, `core`
  `conventions-check`) **are** fixed here per owner direction (2026-06-13).

### Never do

- Name an external source (obra, Strunk, "The Elements of Style", any catalog)
  in a shipped artifact or in this repo's tracked docs. The craft is
  re-expressed in house style; provenance stays in chat and memory.
- Put adoption/virality/positioning strategy into any tracked repo file,
  including `AGENTS.local.md`. That intent lives only in local memory.
- Introduce internal-governance citations into shipped pack content (RFC-NNNN /
  ADR-NNNN zero-padded numbers, `docs/specs|rfc|adr` citation paths, `make`/
  `tools/lint-*` references, "this catalogue"/identity asides).
- Mandate this repo's idiosyncratic conventions (soft-wrap) on adopters. Those
  stay in `AGENTS.local.md`.

## Testing Strategy

Goal-based checks plus adversarial review — there is no runtime logic.

- Build mechanics: goal-based. `make build-self` re-projects, `make
  build-check` shows zero drift, `python3 tools/lint-skill-spec.py` passes
  (skill-relative path rules for the new `references/` file), `make lint-packs`
  passes.
- No-leak / no-attribution / no-strategy: goal-based, by `grep`. The added pack
  content contains no `obra`/`Strunk`/`Elements of Style`, no `RFC-NNNN`/
  `ADR-NNNN`, no `make build`/`tools/lint`; `AGENTS.local.md` contains no
  virality/adoption/Hacker-News/founder framing.
- Prose quality: manual review against the very checklist this spec ships, plus
  one `adversarial-reviewer` pass on the diff + spec.
- Build-system fix: TDD. A unit test in
  `packages/agentbundle/agentbundle/build/tests/test_self_host_check.py` asserts
  `_project_seeds` does not scaffold a by-quadrant guide README; the existing
  pinned `test_excluded_path_missing_on_disk_gets_seed` must still pass.

## Acceptance Criteria

- [x] A new on-demand reference `packs/user-guide-diataxis/.apm/skills/new-guide/references/clear-prose.md` ships a concise checklist covering the AI-prose tells (hedges, uniform rhythm, rule-of-three loop, em-dash overuse, throat-clearing, inflated verbs, heading-restating) and the habits to keep (one claim per sentence, concrete over abstract, strong verbs, omit needless words, no rationale-leak, no intent-narration).
- [x] `new-guide` SKILL.md keeps its existing voice rules and adds (a) a short inline natural-prose rule set and (b) a skill-relative pointer to `references/clear-prose.md` that says to read it when drafting, not before.
- [x] `new-guide` SKILL.md adds an *optional* copyedit pass that hands the draft + the checklist to a read-only subagent, and degrades to a cold self-read when no subagent is available.
- [x] The example reader in `new-guide` SKILL.md no longer names a sibling pack (`credential-brokers`); it is a pack-agnostic, equally concrete reader.
- [x] The `See also` example in `new-guide/assets/explanation.md` no longer uses the zero-padded `ADR-NNNN` citation form; it points generically to a decision record.
- [x] The added pack content introduces no external attribution and no internal-governance citation (verified by grep per Testing Strategy).
- [x] `user-guide-diataxis` pack version bumped 0.1.2 → 0.1.3 in `pack.toml` and `plugin.json`; `marketplace.json` re-aggregated.
- [x] `make build-self` re-projects and `make build-check` reports zero drift; `lint-skill-spec.py` and `lint-packs` pass.
- [x] `docs/product/changelog.md` `[Unreleased]` gains an entry for the new-guide clear-prose guidance.
- [x] `AGENTS.local.md` gains a "house style for our own internal docs" section covering natural prose, no rationale/identity leak, and soft-wrap for `docs/guides/`, stated as house style with no strategic rationale.
- [x] `AGENTS.local.md` contains no adoption/virality/Hacker-News/founder/positioning framing (verified by grep).
- [ ] An automated `.apm/**` leak lint is **not** built here (deferred: apm-leak-lint-rfc).

Scope expansion (owner direction, 2026-06-13) — ride-along fixes for the two items originally surfaced as follow-ups:

- [x] `make build-self` no longer scaffolds the by-quadrant guide tree in self-host: `_project_seeds` skips `docs/guides/**` (it's self-host-only; adopters get guides via `deliver_seeds`). A regression test pins it and the `test_self_host_check.py` suite passes.
- [x] `atlassian` 0.1.2 → 0.1.3: the `make build-self` remediation hint in `jira` and four `RFC-0023` comment citations in shipped `test_exit_codes.py` scripts are removed.
- [x] `core` 0.4.2 → 0.4.3: `conventions-check` no longer names `tools/lint-*` scripts or "this catalogue's own"; reframed as adopter-performable checks that degrade to manual inspection.
- [x] `research/.../retriever-interface.md` naming the `credential-brokers` pack is left as-is — a functional cross-pack capability boundary, not a governance citation (owner-reviewed 2026-06-13).
- [ ] The systemic remaining `core` `.apm/**` internal-gov references (work-loop, `pre-pr.py`, receive-brief scripts, session-start hook, adapt-to-project) are **not** swept here (deferred: apm-leak-lint-rfc).

## Assumptions

- Technical: `user-guide-diataxis` is in this repo's self-host projection set — `.claude/skills/new-guide/` and `.agents/skills/new-guide/` exist and rebuild from `.apm/` (source: probe, `ls .claude/skills/new-guide` 2026-06-13).
- Technical: skills may carry a `references/` subdir loaded on demand and referenced skill-relative; the `work-loop` skill does this (source: `packs/core/.apm/skills/work-loop/SKILL.md` references `references/*.md`).
- Process: an automated `.apm/**` leak lint is a new convention and therefore RFC-gated (source: `AGENTS.local.md` § "Shipped pack content carries no internal-governance citations", user confirmation 2026-06-13).
- Product: the AI-prose craft is universal and adopter-appropriate; the repo's strategic positioning is sensitive and stays in memory only (source: user confirmation 2026-06-13).
- Technical: `_project_seeds` runs only from `run_self_host` (`make build-self`); adopter scaffolding uses the separate `commands/install.py` → `deliver_seeds` path, so skipping `docs/guides/**` in `_project_seeds` affects self-host only and leaves adopter delivery untouched (source: probe, call-site grep 2026-06-13).
