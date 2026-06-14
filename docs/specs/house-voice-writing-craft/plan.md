# Plan: house-voice writing craft

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

Two slices, shipped as two PRs. The first is the adopter-facing change in the
`user-guide-diataxis` pack: a new on-demand reference, an expanded voice
section in `new-guide`, an optional copyedit pass, two leak fixes, a version
bump, build-self, and a changelog entry. The second is a repo-internal change:
a house-style section in `AGENTS.local.md`. The riskiest part is prose quality
and keeping external attribution and strategic intent out of tracked files —
both verified by grep and one adversarial pass. No runtime code changes, so
verification is goal-based plus review.

**Declined-pattern register.** Tempted to vendor the full Strunk text as a
12k-token reference (as the upstream skill does); declining — a tight original
checklist matches the repo's lean bias and avoids attribution. Tempted to add a
`references/clear-prose.md` reminder to all four asset templates; declining —
the SKILL voice section plus one reference is the single lever, asset edits are
scope creep. Tempted to fix the atlassian / research / conventions-check leaks
in the same PR; declining — out of this pack, surfaced as follow-ups. Tempted
to build the `.apm/**` leak lint; declining — RFC-gated new convention.

## Tasks

### T1: Adopter-facing clear-prose guidance in `user-guide-diataxis`

**Depends on:** none

**Tests:** (goal-based)
- `python3 tools/lint-skill-spec.py` passes (skill-relative path to the new `references/clear-prose.md`).
- `grep -rEi 'obra|strunk|elements of style' packs/user-guide-diataxis` returns nothing.
- `grep -rE 'RFC-[0-9]|ADR-[0-9]|make build|tools/lint' packs/user-guide-diataxis/.apm` returns nothing.
- `grep -ri 'credential-brokers' packs/user-guide-diataxis/.apm/skills/new-guide/SKILL.md` returns nothing.
- `make build-self && make build-check` → zero drift; `make lint-packs` passes.

**Approach:**
- Write `references/clear-prose.md`: tells-to-cut + habits-to-keep + a fast self-check. Original, attribution-free, adopter-generic.
- Extend the SKILL voice paragraph: keep existing rules, add the natural-prose rule set + a skill-relative pointer to the reference (read when drafting).
- Add an optional copyedit-subagent pass to the step-6 self-check, degrading to a cold self-read.
- Genericize the credential-brokers example reader; soften the `ADR-NNNN` See-also in `explanation.md`.
- Bump `pack.toml` and `plugin.json` 0.1.2 → 0.1.3; `make build-self`.
- Add a `[Unreleased]` changelog entry.

**Done when:** all T1 tests green and `make build-check` reports zero drift.

### T2: Internal-doc house style in `AGENTS.local.md`

**Depends on:** none

**Tests:** (goal-based)
- `grep -riE 'viral|virality|adoption|hacker.?news|evangelist|founder|go.viral' AGENTS.local.md` returns nothing.
- New section names natural prose, no rationale/identity leak, and soft-wrap for `docs/guides/`.

**Approach:**
- Add a "house style for our own internal docs" section: natural prose (the tells), no rationale/identity leak, soft-wrap guides. Cross-reference the pack as the adopter-facing home so the two don't duplicate. No strategic *why*.

**Done when:** section present, grep clean, file still parses (it is not a projected path, so no build-self).

## Risks

- Prose that itself reads like AI-slop would be self-refuting. Mitigation: the adversarial pass reads the new prose against its own checklist.
- Accidentally reintroducing a leak while editing the leak fixes. Mitigation: the grep tests in T1 gate it.

## Changelog

- 2026-06-13: initial plan.
