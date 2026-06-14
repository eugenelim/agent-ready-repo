# Spec: work-loop-user-level-verification

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0025 (work-loop light mode), ADR-0014
- **Brief:** none
- **Contract:** none
- **Shape:** n/a — methodology/prose change (one shipped skill's doctrine); no application LLD

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Agents running the `core` pack treat **"run it as a real user and report what
you observed"** as a first-class verification expectation for any change that
ships something a user invokes — not only for UIs.

Today the `work-loop` skill defines three verification modes (TDD / goal-based /
visual-manual-QA), but the manual-QA mode is framed almost entirely around UI
rendering and UX flows: "what the user actually sees", "rendered text, visible
elements, navigation", "UI bugs ship invisibly", "drives the UI". For
user-facing artifacts that aren't UIs — a CLI, a library's public API, an agent
or skill — the loop offers no default reflex to **actually invoke the built
artifact end-to-end through its documented workflow and record the observed
result**; it leans on unit gates, which can stay green while the real
invocation is broken.

Success is: the manual-QA mode's scope explicitly covers any user-invoked
artifact (CLI, library API, agent, service, UI), states the
exercise-the-real-artifact-and-record-what-you-observed doctrine, and the DECIDE
end-of-session checklist carries a line that refuses "done" until that
end-to-end exercise has happened when the change ships something a user invokes.
The doctrine is **harness-agnostic** and framed like the EXECUTE simplify pass:
done by hand on any agent, with an agent's own verify/run facility as an
optional accelerant, never a dependency.

The change edits the `core` pack source for the `work-loop` skill
(`packs/core/.apm/skills/work-loop/SKILL.md`) and reprojects via
`make build-self`. It adds **no executable code, no new skill, no new
verification mode, and no new artifact type**.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit the **source** at `packs/core/.apm/skills/work-loop/SKILL.md`, then run
  `make build-self` to regenerate the projected `.claude/skills/work-loop/SKILL.md`.
- Keep the change **inside the existing manual-QA mode** — broaden its scope and
  add a DECIDE checklist line; preserve the existing UI guidance (rendered text,
  visible elements, navigation) and the exploratory-fuzz flavor as the UI
  instantiation of the general doctrine.
- Run all lint surfaces before declaring done: `make build-check` (includes
  `lint-packs` and `validate`) and `python tools/lint-agent-artifacts.py`
  (projection lint, not in build-check).
- Bump `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` in
  lockstep; add a `docs/product/changelog.md` `[Unreleased]` entry.

### Ask first

- Adding a **fourth verification mode** instead of broadening the third — out
  of scope by decision; the audit found the gap is scope, not a missing mode.
- Touching any skill other than `work-loop`.

### Never do

- Reference a "verify skill" or "run skill" as a `core`-pack primitive. Neither
  is shipped by this repo; the only sanctioned references are to the Claude Code
  **native** `/verify` and `/run` commands, framed as an optional accelerant
  exactly as the simplify pass frames `/simplify`.
- Make the end-to-end exercise contingent on a particular harness, command, or
  automation tool. The doctrine must hold on an agent with no verify facility.

## Acceptance Criteria

- [x] **AC1 — manual-QA scope broadened.** The `work-loop` PLAN
  verification-mode picker's third mode explicitly names artifacts a user
  invokes beyond UIs (at minimum a CLI, a library's public API, and an
  agent/skill) as in-scope for manual QA.
- [x] **AC2 — exercise-and-observe doctrine stated.** The same mode states that
  when a change ships something a user invokes, verification includes exercising
  the real built artifact end-to-end through the documented happy path and
  recording what was observed (real output: stdout/exit code, returned value,
  file written, on-screen result) — explicitly *not* internal state
  (mock-call counts, store contents) and *not* a unit gate standing in for the
  real invocation.
- [x] **AC3 — harness-agnostic framing.** The doctrine is labelled
  harness-agnostic and framed as done by hand on any agent, naming the Claude
  Code native `/verify` / `/run` commands as an optional accelerant and never a
  dependency — mirroring the EXECUTE simplify pass. No "verify skill"
  pack-primitive reference appears.
- [x] **AC4 — UI guidance preserved.** The pre-existing UI-specific guidance
  (assert what the user sees; rendered text / visible elements / navigation) and
  the exploratory-fuzz flavor survive as the UI instantiation of the general
  doctrine; nothing UI-only is lost.
- [x] **AC5 — DECIDE checklist line.** The DECIDE end-of-session checklist
  carries a line that refuses "done" until, when the change ships something a
  user invokes, the real artifact was exercised end-to-end through its
  documented happy path and the observed result recorded — a passing unit gate
  alone does not satisfy it.
- [x] **AC6 — projection regenerated, gates green.** `make build-self`
  regenerates the projected skill; `git status` is clean; `lint-packs`,
  `validate`, and `tools/lint-agent-artifacts.py` pass; `packs/core` version is
  bumped in `pack.toml` + `plugin.json` and the changelog carries an
  `[Unreleased]` entry.

## Testing Strategy

Goal-based verification (prose/doctrine change to one shipped skill; no
executable code). "Done" is checked mechanically and by reading:

- **AC1–AC5** — `grep` the edited source for the broadened scope, the
  exercise-and-observe sentence, the `/verify` accelerant framing, the surviving
  UI clauses, and the DECIDE checklist line; read each in context to confirm
  intent (a grep hit is necessary, not sufficient).
- **AC6** — `make build-self` then `git status --porcelain` is empty after
  staging; `make build-check` green; `python tools/lint-agent-artifacts.py`
  green; `grep` the bumped version in both manifests.

No construction test file — this is a goal-based task; a unit test asserting on
prose would pin wording the linter and review already cover.

## Assumptions

- The verification-mode picker stays a **three-mode** taxonomy; the gap is the
  third mode's framing, confirmed by reading the source (manual-QA was UI-only).
- `/verify` and `/run` are Claude Code **native** commands (an agent facility),
  not `core`-pack primitives — so referencing them mirrors the sanctioned
  `/simplify` precedent already in the skill's EXECUTE simplify pass.
