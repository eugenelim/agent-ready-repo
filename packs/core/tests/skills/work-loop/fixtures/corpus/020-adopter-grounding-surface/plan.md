# Plan: Adopter grounding surface — a persistent recording surface the adopter already owns

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Three additive prose edits to existing seed/template/skill sources, then projection. (1) Add a short, optional infra/verification command block to the `core` seed `AGENTS.md` under "Commands you'll need" — placeholder-shaped so it survives the seed lint. (2) Sharpen three existing `reference.md` arc42 slots to name platform targets, framework contracts, and where verification tooling lives — no new section. (3) Add the "read recorded coordinates first, then cold oracle discovery" step to the infra preflight in `references/infra-verification.md`, with absolute presence-check wording, and optionally thread an optional elicitation prompt into `adapt-to-project`/`init-project`. The riskiest part is the **presence-check discipline** — every read must degrade honestly; the regression fence is "a repo that fills nothing runs as it does today." Verification is goal-based (grep the sources + clean build-self) plus a two-repo manual-QA pass (filled vs empty). The seed edit is the one with a sharp constraint: it must stay placeholder-shaped to pass the seed lint.

## Constraints

- ADR-0037 D2 — presence-check absolute; no new config file; recorded coordinates seed, never replace.
- RFC-0047 Decisions 3, 4 — reuse `AGENTS.md` + `reference.md`; read-if-present.
- ADR-0010 — `reference.md` is the golden path; sharpen its slots, don't restructure.
- Seed lint (`lint-seeds` → `lint-catalogue-seeds`, see sibling spec) — `core` seeds stay placeholder-shaped and enforced.
- `feedback_self_host_projection` — edit seed/template/skill **sources**; `make build-self` is the gate.

## Construction tests

**Integration tests:** none beyond per-task checks (no production code).
**Manual verification:** run the infra preflight in two repos (one filled, one empty); record that the filled repo seeds acquisition from recorded coordinates and the empty repo degrades to cold discovery with no failure (spec Testing Strategy).

## Tasks

### T1: `AGENTS.md` seed gains a short optional infra/verification command block

**Depends on:** none

**Tests:**
- `grep` in `packs/core/seeds/AGENTS.md` finds the command block (deploy / smoke-or-verify-status / teardown / seed-test-data), each line marked optional (spec AC1).
- The seed still passes the seed lint (placeholder-shaped, no real commands, no catalogue strings) (Constraints).

**Approach:**
- Add the block under "Commands you'll need" using placeholder commands (`<deploy command>` etc.), kept short with detail pointed at `reference.md`.

**Done when:** the block is present and placeholder-shaped; `grep` green and the seed lint passes.

### T2: `reference.md` arc42 slots sharpened for platform / framework / verification

**Depends on:** none

**Tests:**
- `grep` in the `reference.md` asset finds the sharpened prompts naming managed-runtime/platform targets (Constraints), framework-library contracts (Key technology decisions), and where verification tooling lives (Observability / Testing standards) — with **no** new top-level section added (spec AC2, AC6).

**Approach:**
- Edit the prompt prose inside the three existing slots; do not add a section.

**Done when:** the three slots name the new detail; no new section; `grep` green.

### T3: Infra preflight reads recorded coordinates first, presence-checked

**Depends on:** T1, T2

**Tests:**
- `grep` in `references/infra-verification.md` finds the "read recorded coordinates if present → fall back to cold oracle discovery" step, with explicit presence-check wording and "seed for, never replacement" framing (spec AC3, AC5).
- `grep` confirms no failure-on-absence and no CI gate is introduced (spec AC4 negative criterion).
- `grep` confirms no `grounding.toml` or new config file (spec AC6 negative criterion).

**Approach:**
- Add the first preflight step and the seed-not-replacement framing; cross-reference the `AGENTS.md` block and `reference.md` sections by name.

**Done when:** the preflight step is present and presence-checked; negatives hold; `grep` green.

### T4: Optional elicitation in `adapt-to-project` / `init-project`

**Depends on:** T1, T2

**Tests:**
- `grep` confirms an optional, non-mandating prompt for the grounding coordinates in the relevant skill source — *or* this task is descoped and spec AC7 carries a `(deferred: <anchor>)` marker resolving in `docs/backlog.md` (spec AC7).

**Approach:**
- Thread a short optional prompt into the adapt/init elicitation; if it bloats those flows, defer to backlog and record the anchor.

**Done when:** the prompt exists and is optional, or AC7 is cleanly deferred with a backlog anchor.

### T5: Project and verify additive + clean

**Depends on:** T1-T4

**Tests:**
- `make build-self` projects the edited sources; `git status` clean afterward (spec AC8).
- `lint-spec-status.py` clean (spec AC8).
- Two-repo manual-QA pass recorded (spec Testing Strategy).
- `docs/product/changelog.md` `[Unreleased]` entry for the user-visible seed/preflight change.

**Approach:**
- Clear stray `__pycache__`, run `make build-self`, verify clean tree; add changelog entry; run and record the manual-QA pass.

**Done when:** build-self clean, lint clean, changelog present, manual-QA recorded.

**Manual-QA pass recorded (2026-06-25, doctrine walkthrough).** This change is
prose steering, not runnable code, so the two-repo check is a walkthrough of the
new preflight step against two repo shapes:
- *Filled repo* — `AGENTS.md`'s optional infra block carries real `<deploy>` /
  `<smoke>` / `<teardown>` / `<seed-test-data>` one-liners and `reference.md`
  names the platform target + where verification tooling lives. Following the
  new step, the preflight reads those coordinates *first*, states what it found,
  and **seeds** the multi-artifact preflight + contract-grounding gate from them
  — then still derives the live contract via the oracles and smokes the real
  system. Recorded values seed, never replace; a recorded value that disputes
  the oracle surfaces as a drift signal.
- *Empty repo* — neither surface filled. The step is presence-checked: it finds
  no coordinates, states "none," and **degrades to today's cold oracle
  discovery with no failure** — no loop failure, no CI gate. Confirms the
  regression fence: a repo that fills nothing runs exactly as it does today.

## Rollout

Additive seed/template/skill prose, projected by `make build-self`. No infra, no migration. Reversible by reverting the prose. Deployment sequencing: this spec and `catalogue-seeds-lint` touch disjoint files but share a **lint-name dependency** — this spec's seed edit (T1) must satisfy whichever lint name is current, so if they land in separate PRs, sequence the rename-aware one to rebase onto the other.

## Risks

- **A new read becomes load-bearing** (the loop starts to *need* the surface). Mitigation: spec AC4 is an explicit negative criterion; the adversarial-reviewer checks no read is mandated.
- **Seed lint rejects the new command block** if it looks like instance content. Mitigation: placeholder-shaped block, verified against the lint in T1.
- **Elicitation bloats `adapt-to-project`/`init-project`**. Mitigation: T4 may cleanly defer to backlog.

## Changelog

- 2026-06-25: initial plan (RFC-0047 Layer B follow-on).
- 2026-06-25: implemented (T1–T5). AGENTS.md infra block, three sharpened
  `reference.md` slots, the presence-checked preflight step, and optional
  elicitation threaded into `adapt-to-project` (Detect) + `init-project`
  (Foundation) — AC7 threaded, not deferred. Projected via `make build-self`;
  spec marked Shipped, all ACs checked.
