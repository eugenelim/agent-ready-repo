# Plan: new-rfc fresh-context readability + decidable-in-chat decisions

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

All four changes are prose edits to one skill plus its template, eval, guide,
and version metadata — no code logic. The shape mirrors the two shipped
readability waves (`new-rfc-readability` / B-narrow, `new-rfc-two-humans`): edit
the pack source, `make build-self`, sync the Living how-to guide, update the
Tier-4 eval, bump the pack, add a changelog entry, run both lint surfaces.

The riskiest part is **not weakening the frozen contract** while adding to it:
the no-context readability check must read as *additive* to the mandatory
adversarial pass (never a substitute), and the fresh-context principle must be
satisfiable inline (define-on-first-use) so it doesn't smuggle in a new
mandatory body section that would revise RFC-0014's frozen section set. The edits
are landed source-first, then projected once at the end; the per-task tests are
`grep`-shaped goal checks plus a manual coherence read, because the behavioral
contract is the produced RFC, covered by the eval.

## Constraints

- **RFC-0014** — the answer-first spine, fixed section set, and research→draft→
  gate flow are frozen; this plan adds discipline and one gate check without
  touching them.
- **RFC-0054** — the `Decision weight` field, `## Reviewer brief`, and
  decisions-as-table are frozen; untouched here.
- **B-narrow precedent** (`docs/specs/new-rfc-readability/`) — the established
  shape for a readability-polish spec on this skill (source-edit → build-self →
  guide sync → eval → pack bump → both lints); this plan follows it.

## Construction tests

Most verification is per-task (below). Cross-cutting:

**Integration tests:** none beyond per-task tests.
**Manual verification:**
- Read the regenerated `.claude/skills/new-rfc/SKILL.md` end-to-end and confirm
  the four additions are internally consistent with the surrounding unchanged
  procedure (AC1–AC4); and spot-confirm the Tier-4 eval assertions describe the
  skill's *observable output*, not its internal steps (AC7).
- Run the no-context check once for real: dispatch a generic context-denied
  subagent against a sample RFC (e.g. RFC-0053) with only the RFC text and a
  do-not-read-project-docs instruction, and record its output (the named
  unresolved terms) in the PR notes — the behavioral anchor for AC3.

## Design (LLD)

Shape is `mixed` but the design surface is small (prose in one skill). The
load-bearing design decisions:

### Design decisions

- **Fresh-context = inline define-on-first-use, not a new section.** Glossing
  coined terms where they first appear keeps the RFC readable in flow and avoids
  revising the frozen section set. Rejected: a mandatory `## Glossary` section
  (revises RFC-0014's section set → RFC work; also splits the definition from its
  use). Traces to: AC1.
- **Decidable handoff = enrich the existing step-4 chat block, not a new
  artifact.** The research/de-risk checkpoint already emits a `RESEARCH FINDINGS`
  block to chat; this expands the per-decision shape rather than adding a second
  handoff. Traces to: AC2.
- **No-context check = a second dispatch in step 6, parallel to the adversarial
  pass, of a *generic* subagent with a context-denial prompt — not a new agent
  role.** The adversarial-reviewer loads project conventions by design, so it
  cannot be the cold-reader instrument; a generic subagent given only the RFC
  text and told not to read project docs/sibling RFCs is the right tool. Defining
  a *new* cold-reader persona would trip the `Never do` "new module" boundary and
  needs an RFC — rejected. The result (or a noted skip when no dispatch exists)
  lands in the `REVIEW READINESS` handoff. Traces to: AC3.

### Component / module decomposition

Files touched (all under `packs/governance-extras/` unless noted):
- `.apm/skills/new-rfc/SKILL.md` — steps 4, 5, 6 + Anti-patterns (AC1–AC5).
- `.apm/skills/new-rfc/assets/rfc.md` — cold-reader cue comment (AC1).
- `.apm/skills/new-rfc/evals/evals.json` — fresh-context assertion on the
  existing eval + a new eval entry for the decidable handoff (AC7).
  (`eval_queries.json` is trigger-only and stays unchanged.)
- `pack.toml` + `.claude-plugin/plugin.json` — version bump (AC9).
- `docs/guides/governance-extras/how-to/new-rfc.md` — Steps 3 & 5 sync (AC6).
- `docs/product/changelog.md` — `[Unreleased]` entry (AC9).
- generated: `.claude/` + `.agents/` skill copies + `marketplace.json` via
  `make build-self` (AC8).

## Tasks

### T1: Skill prose — the four behavior changes land in SKILL.md

**Depends on:** none

**Touches:** packs/governance-extras/.apm/skills/new-rfc/SKILL.md, packs/governance-extras/.apm/skills/new-rfc/assets/rfc.md

**Tests:**
- `grep` SKILL.md step 5 for the fresh-context define-on-first-use principle
  (coined term / acronym / sibling-RFC back-reference glossed on first use). (AC1)
- `grep` SKILL.md step 4 for the expanded decision block carrying, per decision,
  question + options-with-trade-offs + recommendation-with-why + cost-of-each;
  confirm the fenced **chat block** (the emitted `RESEARCH FINDINGS` block, not
  `assets/rfc.md`) shows the self-contained shape. (AC2)
- `grep` SKILL.md step 6 for the **generic** context-denied dispatch (denied
  project docs / sibling RFCs), the "in addition to" / non-substitution clause
  vs. the adversarial pass, and that the result/skip is recorded in the
  `REVIEW READINESS` block. (AC3)
- `grep` the Anti-patterns list for the two new entries (undefined sibling-RFC
  jargon; too-terse decision handoff); confirm each is non-duplicative of the
  existing entries, and `grep` the skill confirms no prose states the list's
  cardinality. (AC4)
- `grep` `assets/rfc.md` near the top for the cold-reader cue comment. (AC1)
- Manual diff: each RFC-0014 pre-handoff check's load-bearing clause survives in
  step 6 (citations *fetched* / *actually contain*; verify *executed … never
  self-certified*; adversarial dispatch *mandatory*). (AC5)

**Approach:**
- Add the fresh-context principle to step 5 (the draft step), next to the
  existing body-as-argument and short-title guidance.
- Expand step 4's `RESEARCH FINDINGS` fenced **chat block** (the emitted-to-chat
  handoff, not `assets/rfc.md`) so each decision is self-contained/decidable;
  keep the existing headings.
- Add the no-context readability check to step 6's gate list as a distinct
  bullet, immediately after the existing different-lens (adversarial) bullet,
  stating it is a generic context-denied dispatch and additive; add one line to
  the `REVIEW READINESS` block recording the cold-reader result or noted skip
  (extending a chat-only handoff, not a frozen RFC body/template section).
- Add the two anti-patterns to the refuse list.
- Add the cold-reader cue comment to `assets/rfc.md` line ~1.

**Done when:** all six tests above pass against the source files; no RFC-0014/
RFC-0054 frozen surface is touched (AC5).

### T2: Eval coverage for both new behaviors (evals.json only)

**Depends on:** T1

**Touches:** packs/governance-extras/.apm/skills/new-rfc/evals/evals.json

**Tests:**
- `python -c "import json; json.load(open(...))"` parses `evals.json` clean. (AC7)
- `grep` `evals.json` for a new assertion on the existing draft-the-RFC eval that
  the produced RFC reads from zero prior context (coined terms/acronyms/
  back-references glossed on first use); confirm the pre-existing assertions are
  still present. (AC7)
- `grep` `evals.json` for a **new eval entry** whose prompt exercises the
  research/de-risk handoff and whose assertions check each decision is
  self-contained (question + options-with-trade-offs + recommendation-with-why +
  cost-of-each). (AC7)
- `git diff` shows `eval_queries.json` unchanged (it is trigger/activation only —
  it cannot observe a chat handoff). (AC7)

**Approach:**
- Add one assertion string to the existing eval's `assertions` array in
  `evals.json` (fresh-context readability of the produced RFC).
- Add a second eval object to `evals.json`'s `evals` array (next `id`) whose
  `prompt` asks the skill to research and present the decisions for the user to
  decide (don't draft yet), with `expected_output` + `assertions` judging the
  per-decision self-containedness of the emitted handoff.
- Leave `eval_queries.json` untouched.

**Done when:** `evals.json` parses; the new assertion + new eval entry are
present; existing coverage is intact; `eval_queries.json` is unchanged.

### T3: How-to guide sync

**Depends on:** T1

**Touches:** docs/guides/governance-extras/how-to/new-rfc.md

**Tests:**
- `grep` Step 3 of the guide for the decidable-in-chat decision handoff
  description; `grep` Step 5 for the no-context readability check. (AC6)
- `git diff` shows no drift outside Steps 3 and 5. (AC6)

**Approach:**
- Update Step 3 ("Watch the research + de-risk phase") to describe the
  self-contained per-decision handoff.
- Update Step 5 ("The pre-handoff gate") to describe the no-context readability
  check alongside the adversarial pass.

**Done when:** both Steps describe the new behavior; no other drift.

### T4: Build, version bump, changelog, lints

**Depends on:** T1, T2, T3

**Touches:** packs/governance-extras/pack.toml, packs/governance-extras/.claude-plugin/plugin.json, docs/product/changelog.md

**Tests:**
- `grep` `pack.toml` and `.claude-plugin/plugin.json` both show `0.5.0`. (AC9)
- `grep` `docs/product/changelog.md` `[Unreleased]` for the new entry. (AC9)
- `make build-self` then `git status` shows no residual drift; the projected
  `.claude/` + `.agents/` new-rfc copies carry all four T1 changes. (AC8)
- `lint-packs` and `python tools/lint-agent-artifacts.py` exit clean. (AC8)

**Approach:**
- Bump `governance-extras` 0.4.0 → 0.5.0 in both files.
- Add a user-facing `[Unreleased]` changelog entry describing the two
  reader-facing improvements + the new gate check.
- Run `make build-self`; clear any stray `__pycache__` first so the drift gate
  isn't tripped by a prior projected-script run.
- Run both lint surfaces.

**Done when:** versions match at 0.5.0, the changelog entry exists, the tree is
clean after build-self, and both lints pass.

## Rollout

Pure prose/skill change — no infra, no flag, no migration. Forward-only: the
skill behaves the new way on its next invocation; existing RFCs are not
retrofitted. The pack release (publishing 0.5.0) is the operator's call after
merge, surfaced per the release-on-package-work habit.

## Risks

- **Smuggling a frozen-decision change.** Mitigated by the `Ask first` /
  `Never do` boundaries and AC5's load-bearing-clause check; the fresh-context
  principle is deliberately inline, not a new section.
- **Local build-check false-positive.** The Conductor worktree's
  `make build-check` runs the sibling (main) editable install, not local edits;
  the authoritative gate is a clean tree after `make build-self` plus both lints
  by hand (memory: local-make-build-check-uses-site-packages, stray-pycache).

## Changelog

- 2026-06-30: initial plan.
- 2026-06-30: spec-mode adversarial review — moved the decidable-handoff eval
  coverage from `eval_queries.json` (trigger-only) to a new `evals.json` entry;
  reframed the no-context check from a "matching role" to a *generic*
  context-denied dispatch (no new persona) recorded in `REVIEW READINESS`; added
  a behavioral anchor (one real cold-reader dispatch) and a non-duplication /
  no-count-coupling check for the anti-patterns.
