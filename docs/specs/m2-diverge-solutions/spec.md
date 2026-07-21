# Spec: m2-diverge-solutions

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (M2 · Strategic Shaping; M2.3 option-generation step); known-unknowns resolved 2026-07-18 (`explore-options` vs `diverge-solutions`: coexist, different output contracts — see RFC-0064 § Known Unknowns); Sub-RFC pe-pack-strategic-shaping (RFC-00XX) not yet accepted — this spec proceeds under resolved constraints and may require minor revision on sub-RFC acceptance.
- **Brief:** none
- **Contract:** none — prompt-only skill (Charter Principle 3); no machine interface
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A PE or PM holding an opportunity assessment from step 2 (`identify-opportunities`)
— or a clear understanding of the opportunity at hand — runs `diverge-solutions`
to generate ≥3 structured, comparable solution options for seizing that opportunity.
The skill produces a **Solution Options** typed artifact that:
(1) lays out ≥3 options, each carrying an approach description, the key bets that
must hold for that option to succeed, and relative trade-offs,
(2) retains rejected and parked options with rationale so they remain revivable,
and (3) names a recommended option while leaving the final selection to the PE.

The artifact is committed to `<output_dir>/shaping/<slug>/solution-options.md` and
becomes the input to validation (`de-risk-intent`, step 4) and ultimately `place-bet`
(step 5). The skill is step 3 of the PE six-step shaping sequence
(`frame-situation` → `identify-opportunities` → `diverge-solutions` → validate
→ `place-bet` → `map-capabilities`).

When no step-2 artifact is provided, the skill offers to run `identify-opportunities`
first and describes what step 2 provides; if the user proceeds without it, the
skill continues with a degraded artifact that names the missing input and its
impact on option quality.

**Scope:** initiative-level and capability-level opportunity spaces. Feature-scope
divergence is redirected to `explore-options`.

## Boundaries

### Always do

- **Generate ≥3 options** spanning meaningfully different approaches — not trivial
  variations on one idea. Options must differ in at least one of: mechanic (how
  the opportunity is seized), scope (breadth of what is addressed), or bet
  (what must be true for the approach to succeed).
- **For each option, carry:** name (short title), approach (one paragraph), key
  bets (1–3 assumptions that must hold), trade-offs (relative to the other options),
  and status (`recommended` | `parked` | `rejected`). The skill sets one option to
  `recommended`; the PE sets `selected` after making the final call — the skill
  never sets `selected`.
- **Retain rejected and parked options with rationale** — never delete them.
  Non-recommended options stay revivable; deletion re-creates the myopic-commitment
  risk divergence exists to prevent.
- **Recommend one option** with a one-sentence rationale; leave the final
  selection to the PE.
- **Offer to run `identify-opportunities` first** when no step-2 artifact is
  provided: if the skill is available, offer to run it; if absent, explain what
  step 2 provides. If the user proceeds without step 2, include a "Step 2
  readiness" section in the artifact naming the missing input and its impact on
  option quality.
- **Emit `solution-options.md`** at `<output_dir>/shaping/<slug>/solution-options.md`
  with stable marker (`type: solution-options`) carrying the options array,
  recommendation, residual bets, and — when applicable — the Step 2 readiness note.
- **Resolve the write path via config-driven three-tier procedure**
  (repo-scope `agentbundle-layout.toml [product]` → user-scope → two-branch
  elicitation). Realpath-expand; reject `..` escapes and any symlink chain that
  exits the intended root; surface the resolved absolute path before writing.
- **Redirect to `explore-options` in two cases:** (a) when the input is clearly
  feature-scoped (below capability level), name the altitude mismatch and offer to
  redirect; (b) when the user wants freeform brainstorm without structured comparable
  options, name the output-contract difference and offer to redirect. When altitude
  is genuinely ambiguous, ask — never force one level.
- **Suggest a `[shaping_queue]` entry** — print the TOML snippet for the user to
  add; direct to `capture-work` or manual edit. Do not write to `workspace.toml`.

### Ask first

- Before generating fewer than 3 options (the minimum is a discipline against
  myopic commitment; surface any genuine constraint first).
- Before any write path that resolves outside the repo tree or via a
  realpath-escaped symlink.

### Never do

- **Never** commit to one option on behalf of the PE — recommend and present;
  the PE selects.
- **Never** write to `workspace.toml` directly.
- **Never** write to a literal hardcoded path — always resolve via three-tier config.
- **Never** delete rejected or parked options from the artifact.
- **Never** produce a brief directly — `place-bet` and `author-brief` own the
  brief hand-off.
- **Never** exceed 100 lines in SKILL.md.
- **Never** ship an engine, script, runtime hook, or validator in this skill.

## Testing Strategy

This is a prompt-only skill (Charter Principle 3) — no compressible invariant
logic. Verification is goal-based for structure and manual QA for judgment.

- **Skill file and lint gates: goal-based.** File at the conventional path,
  `tools/lint-skill-spec.py` passes, `lint-packs` passes, <100 lines, valid
  frontmatter.
- **Option generation and artifact structure: manual QA.** Walk the worked
  example end to end; confirm ≥3 options produced, each carrying the required
  fields; record the observed artifact in the implementing PR.
- **AC6 (path-safety): manual QA.** Walk the path-resolution flow; confirm the
  skill surfaces the resolved absolute path before writing and refuses an escaping
  path (a `..` in the configured `output_dir`, or a symlink chain that exits the
  root). Record the observed prompt in the implementing PR.
- **Degrade branch (AC4) and redirect branches (AC8): goal-based grep.** The
  SKILL.md body must contain prose specifying all branches. Pinned assertions
  (unique phrases; must return ≥1 match each):
  AC4 degrade: `grep -F "Step 2 readiness"` (the artifact section that names the
  missing input and its impact); AC8 altitude redirect: `grep -F "altitude mismatch"`;
  AC8 ambiguous-ask: `grep -F "genuinely ambiguous"`;
  AC8 output-contract redirect: `grep -F "output-contract difference"` (the
  freeform-brainstorm → `explore-options` redirect branch — unique in branch
  body, not in frontmatter description). Pin to unique phrases — a count-only
  OR-grep would pass vacuously.
  AC6 path-safety: `grep -F "symlink chain that exits the root"` (the escape-
  refusal prose in the emit step — guards against silent removal of the
  confinement clause).
  Note: the "offer to run `identify-opportunities` first" branch (AC4, if-skill-
  available path) is not exercisable in this PR — `identify-opportunities` is not
  yet shipped. Only the "skill absent / explain what step 2 provides" path is
  walkable. The SKILL.md body must specify both paths; QA covers only the absent path.
- **Diátaxis guide: goal-based for file existence, manual QA for accuracy.**
  Guide at `docs/guides/product-engineering/how-to/generate-solution-options.md`;
  reads accurately against the shipped skill.
- **Projection: goal-based.** `lint-packs`, `validate`, and `build` exit 0.
  Adopter-cleanliness verified by grep (no RFC-NNNN, no `agent-ready-repo` in
  SKILL.md body). `make build-self` not used — PE pack is user-scope, excluded
  from `_DEFAULT_SELF_HOST_PACKS`.

## Acceptance Criteria

- [x] **AC1.** `diverge-solutions` ships at
  `packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md` — <100
  lines, valid frontmatter, passes `tools/lint-skill-spec.py` and `lint-packs`.

- [x] **AC2.** Given an opportunity (as a step-2 artifact or free-form description),
  the skill generates ≥3 solution options that differ in at least one of mechanic,
  scope, or bet. Each option carries: name, approach (one paragraph), key bets
  (1–3 assumptions), trade-offs relative to other options, and status
  (`recommended` | `parked` | `rejected`).

- [x] **AC3.** The skill recommends one option with a one-sentence rationale.
  Non-recommended options are retained in the artifact as `rejected` or `parked`
  with rationale — never deleted.

- [x] **AC4.** When no step-2 artifact is provided: the skill checks whether
  `identify-opportunities` is in the available skill roster — if present, it offers
  to run it and pauses for the user's decision (verbal hand-off; it does not
  auto-invoke); if absent, it explains what step 2 provides (JTBD: functional,
  emotional, social jobs). In both cases, if the user proceeds without step 2, the
  artifact includes a "Step 2 readiness" section naming the missing input and its
  impact on option quality (options may miss JTBD grounding). The SKILL.md body
  contains explicit prose specifying both the available and the absent path.

- [x] **AC5.** The skill emits `<output_dir>/shaping/<slug>/solution-options.md`
  with stable marker (`type: solution-options`) carrying: options array (≥3
  entries with all required fields), recommendation (option name + rationale),
  residual bets, and — when applicable — the Step 2 readiness note. A second run
  for a different slug writes to a different path; no collision.

- [x] **AC6.** The skill resolves the write path via the config-driven three-tier
  procedure (repo-scope → user-scope → two-branch elicitation); realpath-expands
  and symlink-resolves the path; rejects `..` escapes and any symlink chain that
  exits the intended root; surfaces the resolved absolute path before writing.

- [x] **AC7.** After the artifact is written, the skill suggests a `shape`-typed
  `[shaping_queue]` workspace.toml entry — without writing to `workspace.toml`.
  The suggestion includes the derived slug and directs the user to `capture-work`
  or manual edit.

- [x] **AC8.** The skill redirects to `explore-options` in two cases: (a) when
  the input is feature-scoped, it names the altitude mismatch and offers to
  redirect; (b) when the user wants freeform brainstorm without structured
  comparable options, it names the output-contract difference and offers to
  redirect. When altitude is genuinely ambiguous, the skill asks rather than
  forcing one level. The SKILL.md body contains explicit prose specifying all three
  paths (altitude redirect, output-contract redirect, ambiguous-ask).

- [x] **AC9.** A worked example ships at
  `packs/product-engineering/.apm/skills/diverge-solutions/examples/`
  demonstrating the happy path: opportunity description → ≥3 structured options
  → recommendation → `solution-options.md` artifact. Adopter-clean (no RFC-NNNN,
  no `agent-ready-repo`).

- [x] **AC10.** A how-to guide ships at
  `docs/guides/product-engineering/how-to/generate-solution-options.md` covering:
  when to reach for `diverge-solutions` vs `explore-options` (scope/context
  decision); how to read a step-2 opportunity and generate spanning options; how
  to select one and what makes a sound rationale; what to do with the
  workspace.toml suggestion.

- [x] **AC11.** `lint-packs`, `validate`, `build`, and `packages/agentbundle`
  tests exit 0. Adopter-cleanliness grep clean (no RFC-NNNN, no `agent-ready-repo`
  in SKILL.md body). `make build-self` stays drift-free (PE pack user-scope,
  excluded from `_DEFAULT_SELF_HOST_PACKS`; confirmed in plan).

## Assumptions

- Technical: Charter Principle 3 mandates prompt-only — no engine, script, or
  validator (source: `docs/CHARTER.md` § Principles, Principle 3)
- Technical: PE pack skills at
  `packs/product-engineering/.apm/skills/<skill>/SKILL.md`; SKILL.md ≤ 100 lines
  (source: `docs/specs/m2-frame-situation/spec.md` AC1)
- Technical: `make build-self` does not project the PE pack; user-scope, excluded
  from `_DEFAULT_SELF_HOST_PACKS` (source: `docs/specs/m2-frame-situation/plan.md`)
- Technical: `identify-opportunities` not yet shipped — no
  `packs/product-engineering/.apm/skills/identify-opportunities/` directory
  (source: filesystem check 2026-07-21)
- Technical: Artifact output path follows sibling per-slug convention
  `<output_dir>/shaping/<slug>/solution-options.md` (source: `docs/specs/m2-frame-situation/spec.md` AC5;
  artifact name confirmed by user 2026-07-21)
- Process: RFC-0064 M2.3 anchors this skill; `explore-options` vs
  `diverge-solutions` boundary resolved 2026-07-18: `explore-options` is freeform
  brainstorm (no minimum, no forced structure, any context); `diverge-solutions` is
  formal step-3 requiring ≥3 structured comparable options that `place-bet` can
  reason against (source: `docs/rfc/0064-ini-001-ai-native-ecosystem.md` § Known
  Unknowns resolved 2026-07-18)
- Process: Phase-slice doctrine — guide ships with skill in same PR
  (source: `docs/specs/m2-frame-situation/plan.md` § Constraints)
- Process: workspace.toml write-back is `capture-work`'s responsibility; this skill
  suggests verbally (source: `docs/specs/m2-frame-situation/spec.md` § Boundaries)
- Process: Step 4 (validate) = `de-risk-intent`; step 5 = `place-bet`
  (source: `docs/rfc/0064-ini-001-ai-native-ecosystem.md` § Known Unknowns resolved)
- Product: Solution option schema: name, approach, key-bets (1–3), trade-offs,
  status (source: user confirmation 2026-07-21)
- Product: Guide at `docs/guides/product-engineering/how-to/generate-solution-options.md`
  (source: user confirmation 2026-07-21)
- Product: Degrade behavior — offer to run `identify-opportunities` first, degrade
  gracefully with impact note if user skips (source: user confirmation 2026-07-21)
