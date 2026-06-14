# Plan: work-loop-user-level-verification

- **Spec:** [`spec.md`](spec.md)
- **Status:** Shipped

## Approach

One shipped skill, three localized edits, no new artifact. The audit
(recorded in the spec's Objective) established the gap is the *framing* of the
existing manual-QA mode, not a missing mode — so the plan broadens that mode
and adds a DECIDE checklist line, then reprojects.

Declined patterns:

- *Tempted to add a fourth "tool/CLI verification" mode; declining* — the
  reflex belongs inside manual QA, and a fourth mode would split one concept
  ("exercise the real artifact as a user would") across two modes by surface
  type. Surfaced as an Ask-first boundary.
- *Tempted to reference the `/verify` skill as a primitive; declining* — it
  isn't shipped by `core`; the only sanctioned reference is the harness-native
  command, framed as the simplify pass frames `/simplify`.
- *Tempted to write a unit test asserting the prose; declining* — goal-based
  task; grep + review + the projection lint cover it without pinning wording.

## Constraints

- Self-hosting: edit `packs/core/.apm/...` source, never the projected
  `.claude/...` copy; `make build-self` after.
- Version-bump collision: this PR and the retcon-lint PR both bump `core`;
  sequence the bumps (this one to the next patch, retcon-lint to the one after).

## Tasks

### Task 1 — broaden the manual-QA mode and add the DECIDE line

- **Depends on:** none
- **Verification mode:** goal-based
- **Done when:** the PLAN verification-mode picker's third mode names CLI /
  library API / agent as in-scope and states the exercise-and-observe doctrine
  with harness-agnostic `/verify` framing (AC1–AC4); the DECIDE checklist
  carries the refuse-until-exercised line (AC5); the EXECUTE per-mode bullet
  reinforces "exercise the artifact, record what you observed".
- **Tests:** `no stub (goal-based)`. Verify by `grep` + reading the edited
  source in context.
- **Approach:** edit `packs/core/.apm/skills/work-loop/SKILL.md` in place
  (three spots: PLAN picker, EXECUTE per-mode discipline, DECIDE checklist).

### Task 2 — reproject and bump

- **Depends on:** Task 1
- **Verification mode:** goal-based
- **Done when:** `make build-self` regenerates the projected skill with no other
  drift; `packs/core` version bumped in `pack.toml` + `plugin.json`; changelog
  `[Unreleased]` entry added; `make build-check`, `tools/lint-agent-artifacts.py`
  green; `git status` clean (AC6).
- **Tests:** `no stub (goal-based)`. `make build-check` + projection lint are
  the gate.

## Changelog

- Broadened `work-loop` manual-QA verification mode to cover any user-invoked
  artifact and made "exercise the real artifact end-to-end and record what you
  observed" a first-class expectation; added a DECIDE checklist line.
