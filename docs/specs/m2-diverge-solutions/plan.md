# Plan: m2-diverge-solutions

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The whole deliverable is a single new **prompt-only skill** —
`packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md` — plus its
worked example, a how-to guide, and lint/build verification. No engine, script,
or contract file (Charter Principle 3).

The shape mirrors `frame-situation` (same pack, same pattern): skill body defines
the procedure and artifact schema; the agent following it produces the typed
artifact; path resolution is config-driven three-tier. The key difference:
`frame-situation` classifies and routes a signal; `diverge-solutions` takes a
known opportunity and fans it out into ≥3 structured options that `place-bet`
can reason against — the structured output contract is the skill's whole point.

`make build-self` is **not** a verification gate for this spec — the PE pack is
user-scope and excluded from `_DEFAULT_SELF_HOST_PACKS`. Verification uses
`lint-packs`, `validate`, `build`, and `packages/agentbundle` tests instead,
matching the sibling pattern from `frame-situation`.

Order of operations: author SKILL.md (T1), author worked example (T2) and
how-to guide (T3) in parallel after T1, then lint/build (T4).

## Constraints

- **RFC-0064 M2.3** — `diverge-solutions` is step-3 of the PE shaping sequence;
  it takes an opportunity (step-2 output) and produces ≥3 structured comparable
  options that `place-bet` can reason against.
- **RFC-0064 § Known Unknowns resolved 2026-07-18** — `explore-options` vs
  `diverge-solutions` boundary decided: `explore-options` = freeform brainstorm
  (no minimum, no forced structure, any context); `diverge-solutions` = formal
  step-3, ≥3 options, structured output contract. Making `diverge-solutions` a
  wrapper over `explore-options` was explicitly rejected.
- **Charter Principle 3** — prompt-only; no runtime engine, script, or file-path
  generator wired here.
- **PE pack style** — SKILL.md <100 lines; depth in `references/` only if needed.
- **Phase-slice doctrine** — skill ships WITH its guide in the same PR (AC10).
- **File-per-slug path** — `<output_dir>/shaping/<slug>/solution-options.md`;
  slug in the path prevents collision on multiple runs, and the `shaping/<slug>/`
  directory accumulates sibling artifacts as the shaping chain progresses.
- **No workspace.toml write** — deferred to `capture-work`; this skill suggests
  verbally only.

## Construction tests

**Integration tests:** none beyond per-task tests
**Manual verification:** walk the worked example end to end; record observed
`solution-options.md` artifact content in the implementing PR (confirms AC2, AC3,
AC4 degrade path, AC5 artifact shape, AC7 workspace suggestion, AC6 resolved-path
display — confirm skill surfaces the absolute path and refuses an escaping path).

## Design (LLD)

**Shape:** mixed. Pruned to: design decisions, data & schema, dependencies.

### Design decisions

- **≥3 options is a hard floor, not a guideline.** The discipline against
  myopic-greedy commitment requires forcing more than one alternative. The floor
  is 3 — below it, the agent must surface the constraint and ask. Traces to: AC2.
- **Options must span meaningfully different approaches.** "Three names for the
  same mechanic" doesn't count. The spec requires difference in mechanic, scope,
  or bet. The worked example demonstrates span. Traces to: AC2.
- **Inline artifact schema as compact prose — no `references/` file and no full
  markdown template.** The schema must be described in compact field-name + section-
  name form (≤10 lines), not as a full rendered template — `frame-situation` hit 72
  lines by using 5 compact prose lines for its schema. The full template in this
  plan's Data & schema section is a *design reference* for the implementer; the
  SKILL.md body inlines only the compact field list and section names. Exceeding
  100 lines (AC1) is the risk if the full template is inlined verbatim. Traces
  to: AC1, AC5.
- **Degrade on absent step-2, not hard-fail.** Options can be generated without a
  formal opportunity assessment — the skill degrades with a named impact note
  rather than blocking. This preserves utility when `identify-opportunities` hasn't
  shipped yet (it hasn't) while making the gap visible. Traces to: AC4.
- **Redirect to `explore-options` at feature scope.** The altitude boundary is the
  same one `frame-situation` enforces: initiative/capability vs feature. Below
  capability, `explore-options` (freeform, no structure contract) is the right
  tool. Traces to: AC8.
- **config-driven path (same as `frame-situation`).** Re-uses the established
  three-tier convention; no second path-resolution model in the pack. Traces to: AC6.

### Data & schema

`solution-options.md` — the typed artifact:

Frontmatter fields: `type: solution-options`, `slug`, `opportunity` (one-line
description), `date`, `recommendation` (the `name` of the recommended option —
same value as the option's `name` field, not a separate slug). Sections: Opportunity,
Options (≥3 entries), Recommendation, Residual bets, Step 2 readiness (conditional),
Suggested workspace.toml entry.

Each option entry carries: `name` (short title), `approach` (one paragraph),
`key-bets` list (1–3), `trade-offs` prose, `status` (`recommended` | `parked` |
`rejected`). The skill sets exactly one option to `recommended`; `selected` is the
PE's post-emission action and is never set by the skill.

Full option shape (design reference — inline only the compact field list in SKILL.md):

```markdown
### Option: <name>

**Approach:** <one paragraph>
**Key bets:**
- <what must be true for this option to succeed>
**Trade-offs:** <relative to the other options>
**Status:** recommended | parked | rejected
**Rationale:** <why recommended / why retained>
```

### Dependencies

- **`identify-opportunities`** — step-2 skill; detect-and-offer if absent (AC4).
  Not yet shipped (no `packs/product-engineering/.apm/skills/identify-opportunities/`).
- **`explore-options`** — sibling skill; feature-scope redirect target (AC8).
  Already shipped: `packs/product-engineering/.apm/skills/explore-options/SKILL.md`.
- **`de-risk-intent`** — step-4 downstream consumer of this artifact.
- **`place-bet`** — step-5 downstream; the structured option output is designed
  to give `place-bet` enough signal to run the betting table.
- **`agentbundle-layout.toml`** — config-tier read; same three-tier as `frame-situation`.
- **`capture-work`** — downstream workspace.toml write; named in the suggested-entry
  output; not a runtime dependency.

## Tasks

### T1 — Author SKILL.md

**Depends on:** none

**Touches:** `packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md`

**Tests:**
- `tools/lint-skill-spec.py packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md`
  exits 0 (AC1)
- `wc -l .../diverge-solutions/SKILL.md` ≤ 100 (AC1)
- `grep -F "Step 2 readiness" .../diverge-solutions/SKILL.md` returns ≥1 match (AC4
  degrade branch present)
- `grep -F "altitude mismatch" .../diverge-solutions/SKILL.md` returns ≥1 match (AC8
  altitude-redirect branch present)
- `grep -F "genuinely ambiguous" .../diverge-solutions/SKILL.md` returns ≥1 match (AC8
  ask-don't-force branch present)
- `grep -F "output-contract difference" .../diverge-solutions/SKILL.md` returns ≥1
  match (AC8 output-contract redirect branch present — unique in branch body, not
  in frontmatter description)
- `grep -F "symlink chain that exits the root" .../diverge-solutions/SKILL.md`
  returns ≥1 match (AC6 path-safety escape-refusal prose present)

**Approach:**

Author `packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md` with:

**Frontmatter:**
- `name: diverge-solutions`
- `description:` one sentence — when to invoke (initiative/capability-scope
  opportunity → ≥3 structured comparable solution options), what it produces
  (`solution-options.md` with options array + recommendation), what NOT to use it
  for (freeform brainstorm → `explore-options`; committing a bet → `place-bet`;
  feature-scope → `explore-options`).

**When to invoke (5–7 lines):**
- Confirm input is an opportunity at initiative/capability scope (not a feature).
- Feature-scope → name the altitude mismatch, redirect to `explore-options`; ambiguous → ask.
- User wants freeform brainstorm without structured comparable options → name the
  output-contract difference, offer to redirect to `explore-options`.
- No step-2 artifact → offer to run `identify-opportunities` first (if available)
  or explain what it provides (if absent). If user proceeds, degrade gracefully.

**Procedure (numbered steps, inline):**

1. **Intake.** Read the opportunity (step-2 artifact or free-form description).
   Confirm altitude in one sentence; proceed once confirmed. If feature-scoped,
   name the altitude mismatch and offer to redirect to `explore-options`. If
   altitude is genuinely ambiguous, ask.

2. **Step 2 readiness check.** If no `identify-opportunities` artifact is provided:
   check if `identify-opportunities` is in available skills. If present, offer to
   run it first and pause for the user's decision (verbal hand-off; do not
   auto-invoke). If absent, explain what step 2 provides (JTBD: functional,
   emotional, social jobs). In both cases, if the user proceeds without step 2,
   emit the "Step 2 readiness" section naming the missing input and its impact.
   Note: `identify-opportunities` is not yet shipped, so only the absent-path
   is walkable in QA for this PR — the SKILL.md body must nonetheless specify
   both paths (AC4).

3. **Generate ≥3 options.** For each option, produce: name (short descriptive title),
   approach (one paragraph on mechanic and scope), key bets (1–3 — what must be
   true for this option to succeed), trade-offs (relative to the other options).
   Options must span meaningfully different approaches — at least one of mechanic,
   scope, or bet must differ. If all options collapse to trivial variations, name
   the constraint and ask before reducing to fewer than 3.

4. **Recommend one option.** State the recommended option and one-sentence rationale.
   Tag non-recommended options as `rejected` (definitively out) or `parked`
   (revisable). Do not delete any option.

5. **Emit `solution-options.md`.** Resolve `output_dir` via config-driven three-tier
   procedure (repo-scope `agentbundle-layout.toml [product]` → user-scope →
   two-branch elicitation). Realpath-expand; reject `..` escapes and symlinks that
   exit the root; surface the resolved absolute path before writing. Write to
   `<output_dir>/shaping/<slug>/solution-options.md`.

6. **Suggest workspace.toml entry.** Print the TOML snippet. Direct the user to
   add via `capture-work` or manually. Do not write to `workspace.toml`.

**Anti-patterns to refuse** (inline, 3–4 lines):
- Committing to an option on behalf of the PE. Generating fewer than 3 without
  surfacing the constraint. Deleting non-selected options. Writing to workspace.toml
  or a literal hardcoded path.

Inline the `solution-options.md` artifact schema (frontmatter + body sections)
so the agent knows exactly what to emit.

**Done when:** `tools/lint-skill-spec.py` exits 0; `lint-packs` green;
`wc -l` ≤ 100; all three pinned greps return ≥1 match each.

---

### T2 — Author worked example

**Depends on:** T1

**Touches:** `packs/product-engineering/.apm/skills/diverge-solutions/examples/`

**Tests:**
- File exists at `packs/product-engineering/.apm/skills/diverge-solutions/examples/`
  (goal-based; AC9)
- Manual QA: example walks a coherent end-to-end narrative; ≥3 options present,
  each with all required fields; recommendation named with rationale; artifact
  shape matches schema from T1 (AC9)
- `grep -rn "RFC-0064\|agent-ready-repo\|RFC-00" .../diverge-solutions/examples/`
  returns 0 matches (adopter-clean; AC9)

**Approach:**

Author an example at
`packs/product-engineering/.apm/skills/diverge-solutions/examples/opportunity-to-options.md`
using a synthetic but realistic opportunity:

> "The team has confirmed that PEs spend 60–80% of shaping time re-explaining
> context to agents at each session start, with no durable per-initiative memory
> of prior framing decisions."

Demonstrate:
- **Opportunity description:** session-context loss degrading PE throughput
- **Option A — Structured shaping log** (mechanic: structured journal; scope:
  per-initiative; key bet: PEs will maintain a freeform log consistently;
  status: `parked`)
- **Option B — Workspace.toml shaping section** (mechanic: structured data; scope:
  initiative + cross-session; key bets: TOML is low-friction enough for PEs;
  agents can reliably parse and surface it; status: `recommended`)
- **Option C — Agent session-start orientation skill** (mechanic: active synthesis;
  scope: whole workspace; key bet: synthesis quality is high enough to replace
  manual re-briefing; status: `parked`)
- **Recommendation:** Option B — `recommendation: Workspace.toml shaping section`
  in frontmatter (byte-identical to Option B's `name`); rationale in `## Recommendation` section
- **Residual bets** across all options
- **`## Step 2 readiness` section** — the example uses a free-form opportunity
  description (no `identify-opportunities` artifact), which triggers AC4's degrade
  path; this section must appear in the example naming the missing step-2 input
  and its impact on JTBD grounding
- **`solution-options.md` artifact stub** with correct frontmatter
- **workspace.toml suggestion** TOML snippet

**Done when:** example file exists, is adopter-clean, reads as a coherent
end-to-end narrative with all required option fields present.

---

### T3 — Author how-to guide

**Depends on:** T1

**Touches:** `docs/guides/product-engineering/how-to/generate-solution-options.md`

**Tests:**
- File exists at
  `docs/guides/product-engineering/how-to/generate-solution-options.md`
  (goal-based; AC10)
- Manual QA: guide covers all four topics in AC10; reads accurately against the
  shipped SKILL.md (AC10)

**Approach:**

Author `docs/guides/product-engineering/how-to/generate-solution-options.md`
as a Diátaxis how-to (task-oriented; reader knows the goal they want to reach).

Cover:
1. **When to reach for `diverge-solutions` vs `explore-options`** — the
   scope/context decision: initiative/capability-scope opportunity with a structured
   output need → `diverge-solutions`; freeform brainstorm or feature-scope →
   `explore-options`. Include the altitude signal (what distinguishes initiative/
   capability from feature scope).
2. **How to read a step-2 opportunity and generate spanning options** — what
   "spanning" means (mechanic, scope, bet); how the JTBD from step 2 informs
   the key-bets field; what to do when only two distinct approaches come to mind.
3. **How to select one option and what makes a sound rationale** — the rationale
   is not "it's the best"; it names the dominant bet and why the team is willing
   to take it; how to tag rejected vs parked.
4. **What to do with the workspace.toml suggestion** — add via `capture-work` or
   manually; what happens next (step 4: `de-risk-intent` on the selected option).

Length: ~1–2 pages. No internal-catalogue references (RFC-NNNN, `agent-ready-repo`).

**Done when:** file exists at the correct Diátaxis path.

---

### T4 — Lint and build verification

**Depends on:** T1, T2, T3

**Tests:**
- `make lint-packs` exits 0 (AC1, AC11)
- `make validate` exits 0 (AC11)
- `make build` exits 0 (AC11)
- `pytest packages/agentbundle` exits 0 (AC11)
- Adopter-cleanliness grep returns 0 matches (AC11):
  ```bash
  grep -rn "RFC-0064\|agent-ready-repo\|RFC-00" \
    packs/product-engineering/.apm/skills/diverge-solutions/
  ```
- AC4/AC8 pinned greps each return ≥1 match (already verified in T1 tests, but
  run again as final gate):
  ```bash
  grep -F "Step 2 readiness" \
    packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md
  grep -F "altitude mismatch" \
    packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md
  grep -F "genuinely ambiguous" \
    packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md
  grep -F "output-contract difference" \
    packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md  # AC8: unique in branch body
  grep -F "symlink chain that exits the root" \
    packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md  # AC6: path-safety escape-refusal
  ```

**Approach:**

```bash
make lint-packs
make validate
make build
pytest packages/agentbundle
grep -rn "RFC-0064\|agent-ready-repo\|RFC-00" \
  packs/product-engineering/.apm/skills/diverge-solutions/
wc -l packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md
grep -F "output-contract difference" \
  packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md  # AC8: unique in branch body
grep -F "symlink chain that exits the root" \
  packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md  # AC6: path-safety escape-refusal
```

Note: `make build-self` runs as a drift check (no unexpected self-host projection
change) but does **not** project this skill — PE pack is user-scope, excluded from
`_DEFAULT_SELF_HOST_PACKS`. `lint-seeds` is irrelevant (no seeds). `lint-agent-
artifacts.py` covers projected packs only; adopter-cleanliness verified by the
direct grep above.

**Done when:** all commands exit 0; adopter-cleanliness grep clean; AC4/AC8 greps
return ≥1 match each; SKILL.md ≤ 100 lines.

## Rollout

Prompt-only skill in a user-scope pack. No infra, no migration, no deployment
sequencing. Ships as a pack version bump in `packs/product-engineering/` via
the standard build + PR flow.

## Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-07-21 | Initial plan + spec authored | First pass |
