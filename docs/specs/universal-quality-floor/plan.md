# Plan: universal-quality-floor

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Doctrine-only change across two `packs/core/.apm/` source files plus three repo
governance/version files — no runtime code. The shape: sharpen the reviewer
(`quality-engineer.md`), add the simplify pass and the light-mode carve-out to
the `work-loop` `SKILL.md`, thin the now-duplicated mechanics summary out of
`CONVENTIONS.md` (leaving the principle + a pointer), then bump the core pack
version, codify the version-bump rule in `AGENTS.local.md`, and re-project with
`make build-self`. The riskiest part is **not introducing contradictions** —
the new bullets must sit beside the retained rule-of-three (#21), DAMP-in-tests
(#4), and "do not demand 100% coverage" stance without fighting them — and
**not breaking the byte-identical risk-trigger block** when editing CONVENTIONS.
Verification is goal-based: `grep` for presence/absence of each doctrine
element, and a clean `git status` after `make build-self`.

## Constraints

- No ADR/RFC constrains this; the `CONVENTIONS.md` thinning rides this spec as an
  owner-approved edit with a governance note, in lieu of a separate
  `update-conventions` RFC (spec Assumptions, user confirmation 2026-06-12).
- Self-hosting projection rule: edit `packs/core/.apm/` sources, never projected
  `.claude/...` paths; `make build-self` regenerates projections + `marketplace.json`.
- Tool-agnostic / stack-agnostic / threshold-free doctrine (spec Boundaries §
  Never do).

## Construction tests

Per-task `grep` checks live under each task. Cross-cutting:

**Integration tests:** none beyond per-task checks.
**Manual verification:**
- `make build-self` then `git status --porcelain` is empty (projection drift gate).
- Read-through consistency pass: the four new bullets do not contradict #21, #4,
  or the "do not demand 100% coverage" stance (recorded in the adversarial +
  quality-engineer review).

## Design (LLD)

Intentionally thin — this is review/loop doctrine, not a runtime component.

### Design decisions

- **Reviewer, not implementer-prose, is the home for the universal smells.**
  Keeps `AGENTS.md` ≤200 lines and honours "the linter is the source of truth,
  not prose"; the reviewer is the stack-agnostic backstop for when the strict
  gate runs only in CI. Traces to: AC 1–5 · no contract.
- **Simplify pass is harness-agnostic doctrine + an optional native accelerant.**
  The behavior is written for every adapter; Claude Code's `/simplify` is named
  as the way to perform it there, never a dependency. Traces to: AC 6–7.
- **Light-mode carve-out is adopter-declared policy, not detection.** Mirrors the
  "use your agent's native facility" / adopter-set-policy pattern; no repo scan.
  Traces to: AC 8–9.
- **CONVENTIONS keeps the principle, work-loop owns the mechanics.** The smallest
  step of the user's "move away from CONVENTIONS" direction that stays inside this
  scope; the risk-trigger block is untouched. Traces to: AC 10–11.

## Tasks

### T1: Sharpen `quality-engineer` — universal smells + mutation headline

**Depends on:** none

**Touches:** packs/core/.apm/agents/quality-engineer.md

**Tests:**
- `grep` in `quality-engineer.md` Maintainability section finds all four smells:
  bounded-complexity (split-not-comment), nesting-depth (guard clauses /
  pattern matching / early returns, *not* mandating early-return), duplicated
  production blocks past the rule-of-three, magic-literals/fn-param-bloat. (AC 1)
- `grep` finds the reframing phrase that the lens approximates a strict
  static-analysis gate "applied whether or not such a gate is wired". (AC 2)
- Absence-`grep`: the four bullets contain no programming-language name as a
  requirement and no numeric threshold. (AC 3)
- `grep` confirms Test Design now **opens with** "a test must be able to fail"
  framed as the substitute for chasing a coverage number; the existing
  "do not demand 100% coverage" line is still present. (AC 4)
- Read-check: duplication bullet exempts test code (DAMP, #4); abstraction
  guidance still defers to rule-of-three (#21) — no contradiction. (AC 5)

**Approach:**
- In the **Maintainability** section (#20–23), extend with the four bullets,
  phrased as smell *shapes* and severity-graded judgments (mostly Concern/Nit).
- Add a one-line section preface naming the strict-gate-approximation framing.
- In **Test Design**, promote "a test must be able to fail" to the lead, citing
  the mutation-testing mindset; leave the existing coverage stance intact.

**Done when:** all five greps/read-checks above pass on the source file.

### T2: Add the simplify pass to `work-loop` EXECUTE/REVIEW

**Depends on:** none

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md

**Tests:**
- `grep` finds a simplify-pass step in EXECUTE/REVIEW: a deliberate reduce-the-diff
  step after gates are green (inline single-use, delete dead code, collapse
  indirection), scoped to **new code only**, tests stay DAMP, adjacent untouched
  code not refactored. (AC 6)
- `grep` finds the note that Claude Code's native `/simplify` performs the pass
  and the explicit "harness-agnostic; not a dependency" framing. (AC 7)

**Approach:**
- Add a short simplify-pass paragraph anchored in EXECUTE (post-GATES-green) and
  referenced from REVIEW, using the existing "use your agent's native facility"
  phrasing pattern. Bound it: new code only, no adjacent cleanup, tests DAMP.

**Done when:** both greps pass on the source file.

### T3: Light-mode carve-out — retain quality lens when an external gate is declared

**Depends on:** T2 (same file; serialize to avoid a merge against `SKILL.md`)

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md

**Tests:**
- `grep` in the § Modes light-mode list finds the carve-out: retain the
  `quality-engineer` pass when the adopter declares (in AGENTS.md) a strict
  external quality gate the local loop can't run; default (no declaration)
  unchanged. (AC 8)
- Read-check: the carve-out is adopter-declared policy — no detection/scan logic,
  no per-stack table named. (AC 9)

**Approach:**
- Amend the "No default `quality-engineer` pass" bullet in § Modes to carry the
  adopter-declared exception, cross-referencing the simplify pass and the spec's
  Objective. Keep it to one bullet + a sub-clause.

**Done when:** the grep + read-check pass.

### T4: Thin the CONVENTIONS **seed** § Light/full modes + governance note

**Depends on:** T3 (the mechanics must live in work-loop before removing the duplicate summary)

**Touches:** packs/core/seeds/docs/CONVENTIONS.md

**Tests:**
- `grep` confirms the duplicated mechanics summary ("a lean inline spec … no
  default `quality-engineer` pass") is **gone** from the seed CONVENTIONS,
  replaced by the principle + an explicit pointer to the `work-loop` skill as the
  owner. (AC 10)
- **Four-file byte-identical check** (run in T6 after `make build-self`): extract
  the `risk-triggers:start … :end` block from `AGENTS.md`,
  `packs/core/seeds/AGENTS.md`, the seed `docs/CONVENTIONS.md`, and
  `work-loop/SKILL.md`, and `diff` all four — must be identical (grep-equality AC
  of `work-loop-light-mode` preserved). (AC 10)
- `grep` finds the one-line governance note recording the owner-directed edit in
  lieu of a separate RFC. (AC 11)

**Approach:**
- Edit the **seed** (`packs/core/seeds/docs/CONVENTIONS.md`), **never** the
  projected `docs/CONVENTIONS.md` — the latter is regenerated by `make build-self`
  (AGENTS.local.md:146); editing it directly would be reverted by the drift gate.
- Replace the mechanics-summary sentence in § Light/full modes with a principle +
  pointer. Leave the risk-trigger block and its sync comment **untouched**.
- Add the governance note (date + "owner-directed, this conversation").

**Done when:** the seed greps pass; the four-file block `diff` is empty (checked in T6).

### T5: Bump core pack version + codify the version-bump rule in `AGENTS.local.md`

**Depends on:** T1, T2, T3, T4

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, AGENTS.local.md

**Tests:**
- `grep` shows the `[pack]` `version` key in `packs/core/pack.toml` is `0.3.0`
  and the `[contract]` `version` key is still `0.12` (untouched); `plugin.json`
  `version` is `0.3.0`. (AC 12) — match on the key/section, not a line number.
- `grep` in `AGENTS.local.md` finds the standing rule: non-cosmetic `packs/<pack>/`
  updates must bump that pack's version; cosmetic changes exempt. (AC 13)

**Approach:**
- Bump `[pack]` version in `pack.toml` and `plugin.json` 0.2.0 → 0.3.0; leave the
  `[contract]` version alone.
- Add a short section to `AGENTS.local.md` (near the self-hosting-drift section)
  stating the version-bump rule and the cosmetic-change carve-out.

**Done when:** both greps pass.

### T6: Re-project, changelog, drift-clean

**Depends on:** T1, T2, T3, T4, T5

**Touches:** docs/product/changelog.md, projected `.claude/...`, marketplace.json

**Tests:**
- After committing T1–T5, `make build-self` then `git status --porcelain` is
  empty — projections + `marketplace.json` agree with sources, no drift. (AC 14)
- Projected `.claude/agents/quality-engineer.md` and `.claude/skills/work-loop/SKILL.md`
  reflect the T1–T3 source edits (`grep` a distinctive new phrase in each). (AC 14)
- The four-file risk-trigger block `diff` (T4) is empty. (AC 10)
- `grep` in `docs/product/changelog.md` `[Unreleased]` finds the doctrine entry,
  and **not** in the wheel changelog `packages/agentbundle/CHANGELOG.md` (adopter
  changelog only — don't double-log). (AC 15)

**Approach:**
- Add the `[Unreleased]` changelog entry to `docs/product/changelog.md` describing
  the reviewer sharpening, simplify pass, light-mode carve-out, CONVENTIONS
  thinning, and version bump.
- `make build-self` **refuses on a dirty tree** (AGENTS.local.md build-self gotcha):
  commit T1–T5 first (or run `FORCE=1 make build-self` if iterating), then run it.
- Confirm clean tree; if `__pycache__` artifacts appear, clean them and re-confirm
  against a fresh tree.

**Done when:** `git status` is clean post-build-self, the four-file block diff is
empty, and the changelog grep passes.

## Rollout

Pure doctrine/version change — no infra, no migration, no deployment sequencing.
Ships as one PR. Reversible by revert. The only "published" surface is the bumped
core pack version (0.3.0) in `marketplace.json`, which adopters pull on next
install/update — no irreversible step.

## Risks

- **Contradiction with existing reviewer doctrine.** The four new bullets could
  read as fighting rule-of-three / DAMP / the coverage stance. Mitigated by the
  T1 read-check and the adversarial + quality-engineer review passes.
- **CONVENTIONS edit disturbs the byte-identical block.** Mitigated by T4's
  byte-identical absence-check; the edit is confined to prose outside the block.
- **`make build-self` reverts a projection-only slip.** If any projected path was
  edited directly by mistake, build-self silently reverts it; T6's clean-tree
  check catches divergence. Edit only sources.
- **Version-assertion sweep.** A bump can trip a stale pinned assertion elsewhere;
  T5's grep + T6's clean tree surface it.

## Changelog

- 2026-06-12: initial plan.
- 2026-06-12: implemented. **T4 divergence:** the AC11 governance note did
  **not** land in the CONVENTIONS seed (as T4's `Touches:` line implied) — an
  owner-directed-edit provenance note in the adopter-facing seed would violate
  the "Shipped pack content carries no internal-governance citations" rule
  (`AGENTS.local.md`). The note was placed in `AGENTS.local.md` instead
  (repo-internal, never projected), folded into T5's edit to that file. AC11 is
  satisfied there; the seed carries only the thinned principle + pointer.
