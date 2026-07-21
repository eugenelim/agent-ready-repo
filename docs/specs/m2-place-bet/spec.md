# Spec: m2-place-bet

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (M2 · Strategic Shaping; M2.4 bet-commitment gate); RFC-0064 "Resolved 2026-07-18" (de-risk-intent vs place-bet: sequential, not overlapping — de-risk-intent = step 3.5; place-bet = step 5 after validation); Sub-RFC pe-pack-strategic-shaping (RFC-00XX) not yet accepted — spec proceeds under resolved constraints, may require minor revision on acceptance.
- **Brief:** none
- **Contract:** none — prompt-only skill (Charter Principle 3); no machine interface
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A product engineer or PM who has evaluated options and completed or deliberately
skipped validation runs `place-bet` and gets a **committed bet artifact** —
`bet.md` — that records the chosen direction as an explicit, traceable commitment
the next step in the shaping chain (`map-capabilities`) can reason against.

The skill looks for a diverge-solutions artifact at `<output_dir>/shaping/<slug>/`
and reads it when present; when absent, it offers to run `diverge-solutions` first
(naming the tradeoff: without structured comparable options the betting table is
reasoned from free-form description), then degrades gracefully if the PE declines.
The PE may place a bet from any prior options work — `diverge-solutions`,
`explore-options`, external research, or informal notes; `diverge-solutions` is not
required. The skill similarly reads `validation-notes.md` from the same path if
present, folding findings into the `risks-accepted` and `kill-condition` fields.

`bet.md` is committed to `<output_dir>/shaping/<slug>/bet.md` with the common
betting table field set: `option`, `option-source`, `confidence`, `appetite`,
`rationale`, `risks-accepted`, `assumptions`, `kill-condition` (optional), and
`next-step`. The skill then suggests (but does not write) the `workspace.toml`
shaping-queue transition.

**Scope:** step 5 of the PE six-step shaping sequence — after validation, before
`map-capabilities`. Does not run option generation or validation itself.

## Boundaries

### Always do

- **Reuse the active shaping slug** — when working a `[shaping_queue]` item the
  slug is the item's slug; when invoked standalone, ask the PE which slug path to
  write to. Never invent a new slug; the shaping chain's traceability depends on
  all artifacts (`situation-framing.md`, solution options, `bet.md`) landing in
  the same `<output_dir>/shaping/<slug>/` directory. When multiple candidate slug
  paths exist, surface them and ask before proceeding.
- **Check for and read a diverge-solutions artifact** at `<output_dir>/shaping/<slug>/`
  when one is present — surface its options as the structured input to the
  betting table so the PE selects from a presented set.
- **Offer to run `diverge-solutions` first when no options artifact is found** —
  name the impact: without structured comparable options, the rationale and
  risks-accepted are less defensible. Continue with free-form input if the PE
  declines.
- **Accept options input from any prior source** — `diverge-solutions`,
  `explore-options`, external research, or informal notes; do not gate on
  `diverge-solutions` specifically.
- **Read `validation-notes.md` if present** at the same shaping slug path —
  surface relevant findings into `risks-accepted` and `kill-condition`. When
  absent, continue without requiring it.
- **Emit `bet.md`** at `<output_dir>/shaping/<slug>/bet.md` with stable marker
  (`type: bet`) and the full common betting table: `option`, `option-source`,
  `confidence` (high / medium / low), `appetite` (time budget or "open"),
  `rationale`, `risks-accepted` (list), `assumptions` (what must be true for
  the bet to pay off), `kill-condition` (optional — the result that would
  reverse this decision), `next-step` (pointer to `map-capabilities`).
- **Resolve the write path via config-driven three-tier procedure** (repo-scope
  `agentbundle-layout.toml [product]` → user-scope → two-branch elicitation).
  Realpath-expand and symlink-resolve; reject `..` escapes and any symlink chain
  that exits the intended root. Surface the resolved absolute path before writing.
- **Suggest a `workspace.toml` shaping-queue transition** — print the TOML
  snippet; direct the user to `capture-work` or manual edit. Do not write to
  `workspace.toml`.

### Ask first

- Before skipping the bet artifact and handing directly to `map-capabilities`
  (the `bet.md` is the audit trail; proceeding without it loses traceability).
- Before writing to any path that resolves outside the repo tree or via a
  realpath-escaped symlink.
- Before committing a bet when no options have been generated or described
  in any form — name the missing step and ask whether the PE wants to proceed
  or generate options first.
- Before committing a bet when no validation evidence is present in any form
  (no `validation-notes.md`, no `de-risk-intent` output, no stated validation)
  — name the gap and ask whether the PE wants to proceed. The purpose of step 5
  is post-validation commitment; an unvalidated bet is an accepted risk, not a
  silent default.

### Never do

- **Never** write to `workspace.toml` directly — suggest the transition; the
  user commits it.
- **Never** write to a literal hardcoded path — always resolve via the three-tier
  config procedure; `docs/product/` is the designed default, not a constant.
- **Never** run option generation or validation inside this skill — if the PE
  has not generated options, offer `diverge-solutions`; do not run it inline.
- **Never** produce a brief — brief authoring is downstream of `map-capabilities`.
- **Never** exceed 100 lines in `SKILL.md`.
- **Never** ship an engine, script, runtime hook, or validator in this skill.

## Testing Strategy

Prompt-only skill (Charter Principle 3) — no compressible invariant logic.
Verification is goal-based for structure, manual QA for judgment.

- **Skill file and lint gates: goal-based.** File at correct path, <100 lines,
  `tools/lint-skill-spec.py` passes, `lint-packs` passes.
- **Happy path (diverge-solutions artifact present): manual QA.** Walk the
  worked example end-to-end with a solutions artifact present; record the
  observed `bet.md` content in the implementing PR.
- **Offer-and-degrade branch (no options artifact): goal-based grep.** SKILL.md
  must contain prose specifying the offer and the continue-path.
  Pinned phrases (each must return ≥1 match):
  `grep -F "structured comparable options"` (offer + impact);
  `grep -F "continue with free-form"` (degrade continuation).
- **Validation-notes read branch (both paths): goal-based grep.** Two pinned
  phrases, each must return ≥1 match:
  `grep -F "validation-notes.md"` (present-case — file named);
  `grep -F "absent — continue"` (absent-case — graceful continuation stated).
- **Diátaxis guide: goal-based for file existence, manual QA for accuracy.**
  Guide at `docs/guides/product-engineering/how-to/place-a-bet.md`.
- **Path-resolution security: goal-based grep.** SKILL.md body must contain
  prose specifying `..` rejection and symlink-chain escape rejection.
  Pinned phrase: `grep -F "reject"` on the path-safety block.
- **Projection: goal-based.** `lint-packs`, `validate`, `build`, and
  `packages/agentbundle` pytest exit 0. Adopter-cleanliness: grep over SKILL.md
  body confirms no RFC-NNNN or `agent-ready-repo` references. PE pack is
  user-scope — `make build-self` does not project this skill.

## Acceptance Criteria

- [x] **AC1.** `place-bet` ships at
  `packs/product-engineering/.apm/skills/place-bet/SKILL.md`
  — <100 lines, valid frontmatter, passes `tools/lint-skill-spec.py` and
  `lint-packs`.

- [x] **AC2.** The skill reuses the active shaping slug from the
  `[shaping_queue]` item context or asks the PE to confirm the slug path when
  invoked standalone. It never mints a new slug. When multiple candidate slug
  paths exist under `<output_dir>/shaping/`, the skill surfaces them and asks
  before writing. All artifacts for a shaping chain land in the same
  `<output_dir>/shaping/<slug>/` directory.

- [x] **AC3.** When a diverge-solutions artifact exists at
  `<output_dir>/shaping/<slug>/`, the skill reads it and surfaces its options
  as structured input to the betting table. The PE selects or overrides.

- [x] **AC4.** When no options artifact is present, the skill offers to run
  `diverge-solutions` first and names the impact (rationale and risks-accepted
  less defensible without structured comparable options). If the PE declines,
  the skill continues with free-form input. The SKILL.md body specifies both
  paths (goal-based grep: `structured comparable options`; `continue with
  free-form`; each must return ≥1 match).

- [x] **AC5.** The skill accepts options input from any prior source —
  `diverge-solutions`, `explore-options`, external research, or informal notes —
  without requiring `diverge-solutions`.

- [x] **AC6.** When `validation-notes.md` exists at `<output_dir>/shaping/<slug>/`,
  the skill reads it and folds relevant findings into `risks-accepted` and
  `kill-condition`. When absent — continue without requiring it. The SKILL.md body
  specifies both paths (goal-based grep: `validation-notes.md` for the present-case;
  `absent — continue` for the absent-case; each must return ≥1 match).

- [x] **AC7.** The skill emits `bet.md` at `<output_dir>/shaping/<slug>/bet.md`
  with stable marker (`type: bet`) and all common betting table fields: `option`,
  `option-source`, `confidence` (high/medium/low), `appetite` (time budget or
  "open"), `rationale`, `risks-accepted` (list), `assumptions` (what must be true
  for the bet to pay off), `kill-condition` (optional), `next-step` (pointer to
  `map-capabilities`). Re-running `place-bet` on an existing slug overwrites the
  prior `bet.md`; this is the intended revision flow. Distinct slugs write to
  distinct paths.

- [x] **AC8.** The skill resolves the write path via the config-driven three-tier
  procedure (repo-scope → user-scope → two-branch elicitation); realpath-expands
  and symlink-resolves; rejects `..` escapes and any symlink chain that exits the
  intended root; surfaces the resolved absolute path before writing. The SKILL.md
  body contains explicit prose for the rejection clause (goal-based grep:
  `grep -F "reject"` returns ≥1 match on the path-safety block).

- [x] **AC9.** After `bet.md` is written, the skill suggests a `workspace.toml`
  shaping-queue transition — without writing to `workspace.toml` itself. The
  suggestion includes the slug and directs to `capture-work` or manual edit.

- [x] **AC10.** A worked example ships at
  `packs/product-engineering/.apm/skills/place-bet/examples/` demonstrating:
  (a) happy path — diverge-solutions artifact present → betting table from
  structured options → `bet.md` emitted; and (b) degrade path — no artifact →
  offer to run `diverge-solutions` → PE declines → free-form continuation →
  `bet.md` emitted. Adopter-clean (no RFC-NNNN, no `agent-ready-repo`).

- [x] **AC11.** A Diátaxis how-to guide ships at
  `docs/guides/product-engineering/how-to/place-a-bet.md` covering: when to run
  `place-bet` vs `de-risk-intent` (step 3.5 validates a riskiest assumption; step
  5 commits direction after validation); what makes a well-reasoned betting table
  (all common fields; `kill-condition` from `de-risk-intent` when available); and
  how to hand the `bet.md` to `map-capabilities`.

- [x] **AC12.** `lint-packs`, `validate`, `build`, and the `packages/agentbundle`
  pack/contract tests exit 0. Grep over SKILL.md body confirms no adopter-facing
  internal-catalogue references. `make build-self` stays drift-free (PE pack is
  user-scope, excluded from `_DEFAULT_SELF_HOST_PACKS` — same gate as
  `frame-situation`).

## Assumptions

- **A1.** Sub-RFC pe-pack-strategic-shaping not yet accepted. Spec proceeds under
  RFC-0064 "Resolved 2026-07-18": `de-risk-intent` (step 3.5) vs `place-bet`
  (step 5) are sequential and non-overlapping. May require minor revision on
  sub-RFC acceptance. (source: docs/specs/m2-frame-situation/spec.md A1)
- **A2.** Six-step sequence anchored in RFC-0064 and stable enough to name in the
  skill body without the sub-RFC. (source: docs/rfc/0064-ini-001-ai-native-ecosystem.md)
- **A3.** Artifact path `<output_dir>/shaping/<slug>/bet.md` — the filename
  `bet.md` is confirmed by the PE journey doc mermaid diagram; the `<slug>/`
  subdirectory convention is inherited from the `frame-situation` sibling pattern.
  (source: docs/product/journeys/product-engineer-shapes-initiative.md:112;
  docs/specs/m2-frame-situation/spec.md AC5)
- **A4.** Betting table field set derived from: RFC-0064 (option, confidence,
  rationale, risks-accepted), RFC-0030 (appetite/time-box), intent-model.md
  (assumptions = "what must be true for the bet to pay off"), de-risk-intent
  (kill-condition vocabulary), plus option-source and next-step for traceability.
  (source: packs/product-engineering/.apm/skills/frame-intent/references/intent-model.md; docs/rfc/0030-product-engineering-pack.md; user confirmation 2026-07-21)
- **A5.** `validation-notes.md` convention deferred to M2 sub-RFC; skill reads if
  present, does not require it. (source: docs/product/journeys/product-engineer-shapes-initiative.md:185)
- **A6.** PE pack is user-scope, excluded from `_DEFAULT_SELF_HOST_PACKS`; lint
  gates are `lint-packs` + `validate` + `build`, not `build-self`.
  (source: docs/specs/m2-frame-situation/plan.md)
- **A7.** `docs/guides/product-engineering/how-to/` exists; `place-a-bet.md`
  does not yet exist there. (source: filesystem check 2026-07-21)
- **A8.** workspace.toml write-back is `capture-work`'s responsibility per
  RFC-0064 Amendment #3. (source: docs/specs/m2-frame-situation/spec.md A5)
