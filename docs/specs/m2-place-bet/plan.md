# Plan: m2-place-bet

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The whole deliverable is a single new **prompt-only skill** —
`packs/product-engineering/.apm/skills/place-bet/SKILL.md` — plus a worked
example covering both the happy path (options artifact present) and the degrade
path (no artifact → offer → decline → free-form), a how-to guide, and
lint/build verification. No engine, script, or contract file (Charter Principle 3).

Shape mirrors `frame-situation` (same pack, same pattern): skill body defines
the procedure and artifact schema; the agent following it produces `bet.md`; path
resolution is config-driven three-tier. The key difference from `frame-situation`:
`place-bet` is a commitment gate, not an analysis step — it reads upstream
artifacts and emits a structured decision, not a classification.

The riskiest authoring decision is getting the degrade branch right — the skill
must offer `diverge-solutions`, name the impact precisely, and continue gracefully
on decline. Both goal-based greps (AC4) and the worked example (AC10 path b) verify
this branch. Author and verify the degrade branch explicitly in T1.

`make build-self` is **not** a verification gate — the PE pack is user-scope and
excluded from `_DEFAULT_SELF_HOST_PACKS`. Verification uses `lint-packs`,
`validate`, `build`, and `packages/agentbundle` pytest.

Order of operations: T1 SKILL.md → T2 worked example and T3 guide in parallel →
T4 lint/build.

## Constraints

- **RFC-0064 M2.4** — `place-bet` is the bet-commitment gate; output is a
  committed bet artifact that anchors `map-capabilities` (M2.5).
- **RFC-0064 "Resolved 2026-07-18"** — `de-risk-intent` (step 3.5) vs
  `place-bet` (step 5): sequential, not overlapping. Do not conflate.
- **RFC-0064 Amendment #3 + `docs/specs/capture-work/`** — workspace.toml
  write-back is `capture-work`'s responsibility; skill suggests verbally.
- **Sub-RFC pe-pack-strategic-shaping (RFC-00XX) not yet accepted** — proceed
  under resolved constraints; may require minor revision on acceptance.
- **Charter Principle 3** — prompt-only; no runtime engine, script, or
  file-path generator.
- **PE pack style** — SKILL.md <100 lines; no `references/` unless needed.
- **Phase-slice doctrine** — skill ships WITH its guide (AC10).
- **validation-notes.md deferred** — convention not yet established; skill reads
  if present, never requires it.

## Construction tests

**Integration tests:** none beyond per-task tests — each task's goal-based greps
are independent; end-to-end is covered by the T2 worked example walk-through.

**Manual verification:** T2 walk-through — read the worked example with options
artifact present; confirm `bet.md` is coherent and all common fields are populated.

## Design (LLD)

**Shape:** mixed. Pruned sub-sections: no service interface, no UI, no
NFR-with-a-bar. Retaining: design decisions, data & schema, dependencies.

### Design decisions

- **Offer-then-degrade, not hard-gate.** When no options artifact is found, the
  skill offers `diverge-solutions` and names the impact rather than blocking — the
  PE may have a valid reason to bet without structured options (e.g. already ran
  `explore-options` informally). Traces to: AC4.
- **Any options source accepted, not just `diverge-solutions`.** Parallel to how
  `frame-situation` does not require `identify-opportunities` as input — the skill
  reads what it finds and accepts free-form otherwise. Traces to: AC5.
- **`validation-notes.md` is opportunistic.** The convention is deferred to the
  M2 sub-RFC; reading it when present and folding findings in is the safest forward
  posture without over-specifying the convention. Traces to: AC6.
- **kill-condition is optional.** Not every PE will have run `de-risk-intent`
  before betting. When `validation-notes.md` surfaces a kill condition, it's
  folded in. Otherwise the field is left blank. Traces to: AC7.
- **File-per-slug path prevents collision.** `<output_dir>/shaping/<slug>/bet.md`
  — matches `frame-situation` pattern; allows multiple shaping artifacts to
  accumulate under the same slug directory. Traces to: AC7, AC8.
- **No workspace.toml write.** Deferred to `capture-work` per RFC-0064 Amendment
  #3. This skill is scoped to analysis + commitment artifact; workspace coordination
  belongs to its owner. Traces to: AC9.

### Data & schema

`bet.md` — the committed bet artifact:

```markdown
---
type: bet
slug: <derived-from-shaping-context>
date: <ISO date>
option: <chosen option name or one-line summary>
option-source: <path to artifact | "explore-options" | "free-form">
confidence: high | medium | low
appetite: <time budget, e.g. "2 weeks" | "open">
---

# Bet: <slug>

## Option chosen
<Name and one-line description of the chosen option>

## Rationale
<Why this option over the alternatives — reference the options considered>

## Risks accepted
- <risk 1>
- <risk 2>

## Assumptions
<What must be true for this bet to pay off>
- <assumption>

## Kill condition _(optional)_
<The result that would reverse this decision, in the test's own currency.
Omit when not available.>

## Next step
`map-capabilities` — use this bet as the anchor for the capability map.

## Suggested workspace.toml transition
<TOML snippet + direction to apply via `capture-work` or manually>
```

### Dependencies

- **`diverge-solutions`** — step 3; optional artifact input. Detect and offer-
  to-run if absent (AC3). Not yet shipped — skill reads canonical path if
  present, does not import or invoke.
- **`de-risk-intent`** — step 3.5; may produce `validation-notes.md`. Read if
  present at the shaping slug path (AC5). Not a runtime dependency.
- **`map-capabilities`** — step 6; the downstream consumer of `bet.md`. Named in
  the `next-step` pointer; not invoked by this skill.
- **`agentbundle-layout.toml`** — config-tier read; same three-tier as
  `frame-situation` and `frame-intent`.
- **`capture-work`** — downstream workspace.toml write; named in the suggested-
  transition output; not a runtime dependency.

## Tasks

### T1 — Author SKILL.md

**Depends on:** none

**Touches:** `packs/product-engineering/.apm/skills/place-bet/SKILL.md`

**Tests:**
- `tools/lint-skill-spec.py .../place-bet/SKILL.md` exits 0 (AC1)
- `wc -l .../place-bet/SKILL.md` ≤ 100 (AC1)
- `grep -F "structured comparable options" .../place-bet/SKILL.md` returns ≥1 match (AC4 offer)
- `grep -F "continue with free-form" .../place-bet/SKILL.md` returns ≥1 match (AC4 degrade)
- `grep -F "validation-notes.md" .../place-bet/SKILL.md` returns ≥1 match (AC6 present-case)
- `grep -F "absent — continue" .../place-bet/SKILL.md` returns ≥1 match (AC6 absent-case)
- `grep -F "reject" .../place-bet/SKILL.md` returns ≥1 match (AC8 path-safety)
- SKILL.md body describes betting table field set in compact prose, not as a full
  template (the full template lives in plan.md Data & schema only — mirrors the
  `frame-situation` sibling where the artifact schema is described in
  `~8 lines of structured prose`, not a markdown code block)

**Approach:**

Author `packs/product-engineering/.apm/skills/place-bet/SKILL.md` with:

**Frontmatter:**
- `name: place-bet`
- `description:` one sentence — step 5 of the PE six-step shaping sequence;
  reads diverge-solutions artifact if present (offers to run it if absent),
  accepts any prior options input, emits `bet.md` with full betting table;
  do NOT use to generate options (use `diverge-solutions` or `explore-options`)
  or to validate assumptions (use `de-risk-intent`).

**When to invoke (4–6 lines):**
- Confirm options have been generated in some form; if not, offer `diverge-solutions`.
- Confirm at step 5 (after any validation work, before `map-capabilities`).

**Procedure (the steps, inline):**

1. **Intake.** Resolve `output_dir` via the three-tier config procedure (same as
   `frame-situation`). Resolve the shaping slug: reuse the active `[shaping_queue]`
   item slug; when invoked standalone, ask which slug to write to. Never invent a
   new slug; surface multiple candidates when ambiguous. Look for
   `<output_dir>/shaping/<slug>/` — check for a diverge-solutions artifact (any
   `*solution*` or `*options*` file); check for `validation-notes.md`. When
   `validation-notes.md` is absent — continue without it.

2. **Options intake.** If a solutions artifact is found: surface its options as
   the structured set; ask the PE to select or override. If absent: offer to run
   `diverge-solutions` first — name the impact: *"Without structured comparable
   options, the rationale and risks-accepted in the betting table are less
   defensible."* If PE declines, continue with free-form: ask for the options
   considered and the chosen direction. Accept any prior options source
   (`diverge-solutions`, `explore-options`, external research, or informal notes).
   Lookup heuristic for the solutions artifact: look for any `*solution*` or
   `*options*` file at `<output_dir>/shaping/<slug>/`. Document this heuristic
   explicitly in the SKILL — when `diverge-solutions` ships, both skills must
   agree on the canonical filename in the same PR. (deferred: see Risks).

3. **Populate the betting table.** With the PE:
   - **option**: chosen direction name/summary
   - **option-source**: artifact path or source description
   - **confidence**: high / medium / low
   - **appetite**: time budget the team is willing to spend
   - **rationale**: why this option over the alternatives
   - **risks-accepted**: explicit list; fold in any validation-notes findings
   - **assumptions**: what must be true for the bet to pay off
   - **kill-condition** (optional): the result that would reverse this decision;
     fold in from `validation-notes.md` if found, else leave blank

4. **Emit `bet.md`.** Resolve `output_dir` via config-driven three-tier
   procedure (same as `frame-situation`): repo-scope
   `agentbundle-layout.toml [product]` → user-scope → two-branch elicitation.
   Realpath-expand; symlink-resolve; reject `..` and symlinks that exit the root.
   Surface the resolved absolute path before writing. Write to
   `<output_dir>/shaping/<slug>/bet.md`.

5. **Suggest workspace.toml transition.** Print the TOML snippet (move the
   shaping_queue item to active or note its hand-off to `map-capabilities`).
   Direct the user to `capture-work` or manual edit. Do not write to
   `workspace.toml`.

**Anti-patterns (inline, 3–4 lines):**
- Writing to `workspace.toml` or a literal path. Running `diverge-solutions`
  inline. Producing a brief. Blocking when no options artifact exists — offer
  and degrade instead.

**Done when:** lint-skill-spec.py exits 0; `lint-packs` green; `wc -l` ≤ 100;
all five goal-based greps return ≥1 match.

---

### T2 — Author worked example

**Depends on:** T1

**Touches:** `packs/product-engineering/.apm/skills/place-bet/examples/`

**Tests:**
- Manual QA: read both paths; confirm `bet.md` shape is coherent with all common
  fields; confirm degrade path names the impact and shows free-form continuation
- Adopter-cleanliness: `grep -rn "RFC-0064\|agent-ready-repo\|RFC-00" .../place-bet/examples/` returns 0 matches (AC10)

**Approach:**

Author `packs/product-engineering/.apm/skills/place-bet/examples/placing-a-bet.md`
using a synthetic but realistic shaping context.

**Path (a) — happy path:** a diverge-solutions artifact is present at the slug
path with three structured options. The PE selects option B. Demonstrate the full
betting table populated from the structured options, validation-notes folded in
for risks-accepted, and the completed `bet.md` stub.

**Path (b) — degrade path:** no solutions artifact at the slug path. Skill offers
`diverge-solutions` and names the impact. PE declines. Skill accepts free-form
description of two options considered and the chosen direction. `bet.md` emitted
with `option-source: free-form`.

**Done when:** both paths present; example is adopter-clean; reads as a coherent
narrative in each path.

---

### T3 — Author Diátaxis how-to guide

**Depends on:** T1

**Touches:** `docs/guides/product-engineering/how-to/place-a-bet.md`

**Tests:**
- Goal-based: file exists at correct path (AC11)
- Manual QA: guide accurately describes the shipped skill; no internal-catalogue
  references (`grep -n "RFC-\|agent-ready-repo" .../place-a-bet.md` returns 0)

**Approach:**

Author `docs/guides/product-engineering/how-to/place-a-bet.md` as a Diátaxis
how-to (task-oriented; reader knows their goal). Cover:

1. When to reach for `place-bet` vs `de-risk-intent` — step 3.5 validates the
   riskiest assumption before validation; step 5 commits direction after it.
2. What inputs `place-bet` needs (options in any form; validation notes if
   available) and where to find them.
3. How to fill each betting table field — especially `kill-condition` (pull from
   `de-risk-intent` output if available) and `appetite` (name a budget rather
   than leaving "open" if at all possible).
4. How to hand the `bet.md` to `map-capabilities`.

Length: ~1–2 pages. No internal-catalogue references.

**Done when:** file exists at the correct Diátaxis path; reads accurately against
the shipped skill.

---

### T4 — Lint and build verification

**Depends on:** T1, T2, T3

**Touches:** none beyond what prior tasks touched

**Tests:**
- `make lint-packs` exits 0
- `make validate` exits 0
- `make build` exits 0
- `pytest packages/agentbundle` exits 0
- `grep -rn "RFC-0064\|agent-ready-repo\|RFC-00" packs/product-engineering/.apm/skills/place-bet/` returns 0 matches (AC12)
- All pinned greps from T1 return ≥1 match (re-check after T2/T3)
- `wc -l packs/product-engineering/.apm/skills/place-bet/SKILL.md` ≤ 100

**Approach:**

```bash
make lint-packs
make validate
make build
pytest packages/agentbundle
# Adopter-cleanliness
grep -rn "RFC-0064\|agent-ready-repo\|RFC-00" \
  packs/product-engineering/.apm/skills/place-bet/
# Pinned greps (AC4 offer + degrade)
grep -F "structured comparable options" \
  packs/product-engineering/.apm/skills/place-bet/SKILL.md
grep -F "continue with free-form" \
  packs/product-engineering/.apm/skills/place-bet/SKILL.md
# Pinned greps (AC6 present + absent)
grep -F "validation-notes.md" \
  packs/product-engineering/.apm/skills/place-bet/SKILL.md
grep -F "absent — continue" \
  packs/product-engineering/.apm/skills/place-bet/SKILL.md
# Pinned grep (AC8 path safety)
grep -F "reject" \
  packs/product-engineering/.apm/skills/place-bet/SKILL.md
# Line count
wc -l packs/product-engineering/.apm/skills/place-bet/SKILL.md
```

Note: `make build-self` still runs as a drift check (confirms no unexpected change
to self-host projection), but does **not** project this skill — PE pack is user-scope
(`_DEFAULT_SELF_HOST_PACKS` = core / governance-extras; `product-engineering`
excluded).

**Done when:** all commands exit 0; adopter-cleanliness grep clean; AC3/AC5 greps
return ≥1 match each; SKILL.md ≤ 100 lines.

## Rollout

New skill in the PE pack. No infrastructure, no data migration, no external system
integration. Big-bang delivery: T1–T4 land in one PR. Reversible — a skill can be
removed or revised in a follow-on PR without downstream impact.

## Risks

- **`diverge-solutions` artifact path not yet canonical** — `diverge-solutions`
  hasn't shipped; the skill must look for any `*solutions*` or `*options*` file
  at the slug path rather than a pinned filename. Risk: path convention drifts
  when `diverge-solutions` ships. Mitigation: document the lookup heuristic in
  the SKILL.md; when `diverge-solutions` ships, update both skills in the same PR
  to agree on the canonical filename.
- **SKILL.md line count** — the offer-and-degrade branch and the full betting
  table schema are verbose. Keep anti-patterns to 3–4 lines; inline the schema
  tightly. The 100-line cap is a hard gate.

## Changelog

- 2026-07-21: initial plan authored
