# Plan: jira-story-actionability

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Three deliverables, all prose primitives (choreography `SKILL.md` files), no new
executable logic:

1. **Quality gate** — a targeted edit to `packs/atlassian/.apm/skills/jira/SKILL.md`
   inserting a "Repo grounding and pre-create quality gate" sub-section in Step 5,
   before the first `create-issue` example. The gate fires on `create-issue` intent
   only, not on `update-issue`. It augments the existing "confirm intent + show
   payload" instruction; it does not replace it.

2. **`jira-story-triage` skill** — a new directory under
   `packs/atlassian/.apm/skills/jira-story-triage/`. An audit tool: given a JQL
   scope, it scores stories against the five-question bar and tier rubric from the
   spec and produces a table. Read-only; no hand-off.

3. **`jira-team-status` skill** — a new directory under
   `packs/atlassian/.apm/skills/jira-team-status/`. A session-entry-point tool
   modelled on `workspace-status`'s pattern: shows the scored snapshot then offers
   a pick-up hand-off — start delivery on a Tier A story, or shape a Tier C/Blocked
   story into something workable. Reads from Jira for the snapshot; with explicit
   user consent in the shaping hand-off, calls `update-issue` once on the story
   being rewritten. The update-issue path is conditional and gated — the skill
   confirms the full rewritten payload before writing.

**Canonical tier rubric anchor:** the five-question bar and tier rubric (pre-check +
A/B/C total function) live in `spec.md` only. All three deliverables reproduce the
bar text and tier table verbatim — no paraphrasing. The consistency grep in T4
enforces this mechanically.

Riskiest aspects:
- **Tier rubric divergence** across the three deliverables. Mitigated by the
  spec-anchored tier table and the cross-file grep gate.
- **Trigger collision**: `jira-story-triage` vs `jira-team-status` vs `workspace-status`.
  Mitigated by mutual-exclusion false-positive sets in evals for all three pairings.
- **Blocked pre-check ordering**: the pre-check must short-circuit scoring; any
  implementation that scores first and then checks the pre-check produces wrong tiers.

Declined temptations:
- A separate `jira-story-gate` skill the user must invoke explicitly: the gate fires
  on every `create-issue` intent — user memory should not be required.
- Auto-rewriting story content in the gate or triage: the gate pauses to elicit; it
  never edits without explicit user instruction.
- Any integration with workspace.toml or local queue files: Jira is external; results
  stay in the agent session.
- Extracting a shared prose include or reference file across the three SKILL.md bodies
  to DRY the bar text: skills are flat single files by pack convention; the bar text
  is short enough to reproduce verbatim, and a shared include would introduce a new
  cross-skill dependency boundary this spec does not authorize.
- Writing a Python scoring helper for the tier classification: no new executable logic
  ships in this spec; the scoring is an instruction to the agent (prose), not compiled
  logic.

## Constraints

- No governance constraint for atlassian-pack workflow skills. Binding precedent:
  `jira-brief-intake` (same by-name dispatch, same manifest `deps` shape, same
  reference-docs layout) and `jira-defect-flow` (graceful-degradation pattern).
- atlassian is user-scope-default: gate is `lint-packs` + `validate` + `build` +
  package pytest, not `build-self`/`pre-pr`.
- No new executable code ships: all three deliverables are prose primitives.

## Construction tests

No new executable logic — no per-task unit tests. All verification is goal-based +
manual dry-run.

**Goal-based gates (run per-task as each task's `Done when:`):**
1. `lint-packs` green for the atlassian pack after every task that edits pack files.
2. `grep "self-contained code/config/doc change"` returns matches in all four files:
   spec.md, `jira/SKILL.md`, `jira-story-triage/SKILL.md`, `jira-team-status/SKILL.md`.
   Run at T4 (after T1–T3 complete).
3. `agentbundle validate` + `make build` with no marketplace drift. Run at T4.

**Manual dry-runs (one per deliverable):**
1. **Gate (T1)**: gate text appears before the first `create-issue` example; six checks
   are present each with bar-question mapping (Q1–Q5), failure mode, and elicitation
   prompt; gate is explicitly `create-issue`-only; "Don't" bullet present.
2. **`jira-story-triage` (T2)**: reading-level pass against 12 stories (3×Tier A,
   2×Tier B, 3×Tier C via Q5 fail, 2×Tier C via content fail, 2×Blocked) — Blocked
   pre-check fires first and short-circuits scoring on the two Blocked stories;
   tier table produced; invocation-repo header present.
3. **`jira-team-status` (T3)**: four output sections in order; pick-up hand-off offered
   after snapshot; invocation-repo in summary; no local file reference; trigger phrases
   distinct from `workspace-status` and from `jira-story-triage`.

## Tasks

### T1: Story quality gate added to `jira/SKILL.md`

**Depends on:** none (the bar text is locked in spec.md, not in any task output)

**Tests:**
- `lint-packs` passes for the atlassian pack after the edit.
- `grep "pre-create quality gate" packs/atlassian/.apm/skills/jira/SKILL.md` returns
  a match.
- `grep "create-issue intent only" packs/atlassian/.apm/skills/jira/SKILL.md` returns
  a match (gate scope boundary).
- Manual dry-run above passes.

**Approach:**
In `packs/atlassian/.apm/skills/jira/SKILL.md`, within the existing `### Step 5:
Creating and updating issues` section, insert a new sub-section
`#### Repo grounding and pre-create quality gate` immediately after the opening
paragraph ("Writes are real and visible…") and before the `create-issue` command
examples. Content:

**Sub-section 1 — Repo grounding:**
Detect `git remote -v` in the working directory. If a URL is found, label it
"Invocation repo: `<URL>`" — this is the repo the agent is running from; not
every story in the queue necessarily targets this repo. If not in a git repo (or
no remote configured), surface: "Optionally supply a repo URL or name — this
helps the agent verify the story's scope and write clearer acceptance criteria.
Enter to skip." Proceed with "Invocation repo: unknown" if the user declines.

**Sub-section 2 — Five-question actionability bar (verbatim from spec.md):**
Before the six-check table, insert the bar text verbatim:

> A story is actionable when all five are true:
> (Q1) it is a **self-contained code/config/doc change** — not discovery, design, or coordination work;
> (Q2) it names a **reachable repo or file scope** so the change can be located without a follow-up meeting;
> (Q3) its **acceptance criteria are checkable by diff review alone** — no "TBD", "coordinate with", "decide on", or "prototype";
> (Q4) **no human decision is needed mid-flight** — no open design question, no external approval gate that cannot be confirmed before work starts;
> (Q5) it is **right-sized for one PR** — the scope is an enumerable set of files or PRs a single person or agent can produce without decomposing into sub-stories.

This is the canonical bar text that T4's consistency grep will verify against all four files.

**Sub-section 3 — Six-point pre-create checklist** (applies to `create-issue`
intent only; skip for `update-issue`):

| # | Check | Bar Q | Signal the gate looks for | Failure mode | Elicitation prompt |
|---|---|---|---|---|---|
| 1 | Summary specificity | Q1/Q2 | Summary names the specific change, not just a domain | "Add telemetry", "Update agents", "Fix things" | "The summary is too broad — name the specific change. E.g. 'Add dotenv support to telemetry dashboard'" |
| 2 | Repo/file scope in description | Q2 | Description names a repo URL, repo name, or file path | Blank description or no code anchor | "Which repo or file does this change touch? This makes the story executable without a meeting." |
| 3 | ACs present and binary | Q3 | Description or ACs field contains testable, diff-checkable criteria | No ACs, or ACs contain "TBD", "coordinate with", "decide on", "prototype" | "Add acceptance criteria checkable from a diff alone — each should be verifiable without a meeting." |
| 4 | No discovery/coordination language; issuetype is implementation work | Q1 | Summary and description free of "define how", "explore", "assess", "design the approach", "discuss", "align with", "determine"; issuetype is Story/Task/Bug/Sub-task | Discovery language or discovery issuetype | "This reads like discovery or design work. Should this be a shaping item, or can you reframe it as a concrete change?" |
| 5 | No mid-flight approval gate | Q4 | No open design question or unnamed approval pending | "pending decision from", "TBD — awaiting alignment", "blocked on" | "Is there a specific person who can confirm this decision now? If so, name them and the decision. Otherwise this story is Tier B until they do." |
| 6 | Right-sized for one PR | Q5 | Story scope is an enumerable set of files or PRs one person or agent can produce; story-points field (if present) is within the team's single-story threshold | Multi-week scope, cross-team dependency, story-points well above threshold, or "multiple repos" language | "This looks too large for one PR. Can you split it into one bounded change per story? Jira stories are a capacity-allocation unit — an agent or engineer needs a PR-sized scope to execute without decomposition." |

Gate behaviour: on any failed check, surface the failure with its elicitation prompt
and wait. If the user supplies the missing signal, incorporate it and continue. If
the user overrides ("proceed anyway"), proceed and note the override in the payload
confirmation summary. Never silently bypass.

**Add to the existing `### Don't` list:**
> - Don't skip the pre-create quality gate on `create-issue` calls. The gate is the
>   minimum bar for a story an agent or engineer can act on without a meeting or a
>   follow-up question.

**Done when:** `lint-packs` green, gate sub-section present in correct position,
all six checks named with bar-question mapping, gate explicitly marked as
`create-issue`-only, "Don't" bullet present.

---

### T2: `jira-story-triage` skill authored and well-formed

**Depends on:** T1 (the bar text and tier rubric are spec-anchored, but T1 must exist
first to establish the gate's six-check structure before T2 mirrors it in scoring)

**Tests:**
- `lint-packs` green for atlassian.
- `grep "self-contained code/config/doc change" packs/atlassian/.apm/skills/jira-story-triage/SKILL.md`
  returns a match.
- `ls packs/atlassian/.apm/skills/jira-story-triage/` shows all four required files.
- Manual dry-run: Blocked pre-check fires first on image-only/empty/discovery stories
  before the tier scoring loop runs; tier table produced with invocation-repo header;
  12-story scenario passes.

**Approach:**
Create `packs/atlassian/.apm/skills/jira-story-triage/` with:

`SKILL.md`:
- Frontmatter: `name: jira-story-triage`, trigger description: "Use this skill to
  audit a Jira backlog or sprint for agent-readiness — score each story against the
  five-question actionability bar and output a Tier A / B / C / Blocked table. Triggers
  on: 'score the backlog', 'which tickets are ready to ship', 'triage sprint for
  actionability', 'classify PROJ backlog by tier', 'what's agent-ready in PROJ',
  'run a backlog health audit'. Do NOT use for: showing team sprint status with a
  pick-up hand-off (use `jira-team-status`), creating or updating issues (use `jira`),
  turning an epic into specs (use `jira-brief-intake`), or fixing a defect (use
  `jira-defect-flow`)."
- Preamble: read-only audit over the `jira` skill; no hand-off; no writes.
- Prerequisites: `jira: check` (hard dependency; exit 2 → stop, tell user to
  authenticate).
- Repo grounding: identical logic and labelling to T1 ("Invocation repo").
- Lifecycle — five stages:
  1. **Intake**: accept a JQL query, sprint/board ID, or default open-sprint JQL.
  2. **Fetch**: `jira search --fields "summary,description,issuetype,status,priority,labels,customfield_*"` with auto-pagination.
  3. **Pre-check (runs first, short-circuits)**: for each story — description empty or image-only → Blocked; issuetype is discovery artifact → Blocked. Do not score Blocked stories.
  4. **Score non-Blocked stories**: apply Q1–Q5 from the spec's five-question bar verbatim. Use word-boundary matching for keyword detection (English only; unknown issuetypes → "type unknown — manual review" label).
  5. **Classify** using the spec's tier rubric (total function): A / B / C — pre-check already handled Blocked.
  6. **Complexity scoring** (applied to non-Blocked, non-Tier-C stories before output):
     - **Quick**: story-points ≤ 2 (or points absent + description ≤ 100 words + ≤ 2 ACs)
     - **Standard**: story-points 3–5 (or points absent + moderate description)
     - **Involved**: story-points > 5 (or points absent + description > 200 words or > 5 ACs)
     If story-points field is absent or zero, fall back to description length + AC count.

  7. **Output**: header line "Invocation repo: `<URL>`" or "Invocation repo: unknown"; Markdown table sorted A→B→C→Blocked. **Within the Tier A block, rows are sub-grouped by complexity: Quick first, then Standard, then Involved** (with a sub-header per group). Columns: `Key`, `Summary (truncated 60 chars)`, `Tier`, `Complexity` (Tier A rows only), `Blocking issue / gate` (Tier B rows only); footer: "Agent-ready: <n>. Gated: <g>. Need shaping: <s>. Blocked: <b>." (count tokens, not tier letters).
- Don't: no Jira write verbs; no story rewriting; no reference to local repo files.
- Examples pointer to `references/examples.md`.

`manifest.json`: id `jira-story-triage`; category `workflows`; deps.skills = `jira` (hard, this pack).

`evals/eval_queries.json`:
- ≥8 `should_trigger: true`: "score our Jira backlog for agent-readiness", "triage this sprint for actionability", "which tickets are ready to ship", "classify PROJ backlog by tier", "what's agent-ready in PROJ", "run a backlog health audit", "score these 20 stories", "which stories in sprint 12 can we execute"
- ≥8 `should_trigger: false` including:
  - ≥3 team-status-shaped (e.g. "show team sprint status and pick one up", "what's our sprint health and what should we start", "team backlog overview with hand-off") → `jira-team-status`
  - ≥4 primitive-jira-shaped (e.g. "show me my open Jira issues", "create a story for the login bug", "turn PROJ-100 into specs", "fix the bug in PROJ-99")
  - ≥1 workspace-status-shaped (e.g. "what should I work on next session")

`references/examples.md`: two worked examples — (1) a 12-story mixed-tier sprint audit showing pre-check short-circuiting; (2) an invocation-repo-unknown scenario.

**Done when:** all four files exist; `lint-packs` green; greps pass; manual dry-run passes.

---

### T3: `jira-team-status` skill authored and well-formed

**Depends on:** T2 (tier definitions are spec-anchored; T2 must be complete first so
the classification logic is established and T3 can reference it as a precedent)

**Tests:**
- `lint-packs` green for atlassian.
- `grep "self-contained code/config/doc change" packs/atlassian/.apm/skills/jira-team-status/SKILL.md`
  returns a match.
- `grep -iE "workspace\.toml|workspace-status" packs/atlassian/.apm/skills/jira-team-status/SKILL.md`
  returns no match (note: the `Do NOT use for` clause may name `workspace-status` as
  the routing alternative — this is allowed; the test blocks any reference to
  workspace.toml or its internal structure).
- Manual dry-run: four output sections in correct order; pick-up hand-off offered;
  invocation-repo in summary; trigger phrases distinct from both `workspace-status`
  and `jira-story-triage`.

**Approach:**
Create `packs/atlassian/.apm/skills/jira-team-status/` with:

`SKILL.md`:
- Frontmatter: `name: jira-team-status`, trigger description: "Use this skill to
  get your team's Jira sprint or backlog status scored for agent-readiness, then
  pick up a story to deliver or shape. Triggers on: 'show team backlog', 'team sprint
  status', 'what can we ship this sprint', 'plan the sprint backlog', 'which stories
  are agent-ready for the team', 'team backlog health check', 'score our sprint and
  pick one up'. Do NOT use for: local workspace queue or session orientation (use
  `workspace-status`), a bulk backlog audit without hand-off (use `jira-story-triage`),
  creating or updating issues (use `jira`), or fixing a defect (use `jira-defect-flow`)."
- Preamble: session-entry-point pattern modelled on `workspace-status` — displays
  a scored Jira snapshot then offers a hand-off. Reads from Jira only. Complements
  `jira-story-triage` (triage = bulk audit; team-status = sprint-cadence entry point
  with pick-up).
- Prerequisites: `jira: check` (hard dependency).
- Repo grounding: identical logic to T1/T2 ("Invocation repo" label).
- Inputs: Jira project key (required); sprint scope (default: open sprints); optional
  team name or JQL filter.
- Lifecycle — six stages:
  1. **Fetch**: open/in-progress/backlog issues via `jira search` with sprint scope;
     include all stories not Done or Closed.
  2. **Pre-check (first, short-circuits)**: same as T2 — Blocked for empty/image-only
     or discovery issuetype.
  3. **Score and classify non-Blocked stories**: same five-question bar and tier rubric
     as T2 (spec-anchored).
  4. **Output — four sections** (in this order, always):

     **§1 — Agent-ready (Tier A)** — grouped by complexity within the section
     Stories that can be handed to an agent or engineer now. Complexity signal:
     story-points field (primary); description length + AC count (fallback).
     `Quick` (≤ 2pts): mechanical changes, can be started in a short window.
     `Standard` (3–5pts): implementation task with moderate scope.
     `Involved` (> 5pts): larger change still within one-PR scope.
     Table (one sub-group header per complexity band): `Key | Summary | Priority | Complexity | Invocation repo match?`
     If none: "No Tier A stories in this scope — see §3 Needs shaping to improve the backlog."

     **§2 — Parallel batching candidates**
     Tier A stories with mutually distinct repo scopes (no explicit dependency
     language between them). Presented as: "Can run concurrently: PROJ-101,
     PROJ-103, PROJ-107." If no parallelism detected: omit this section.

     **§3 — Gated (Tier B)**
     Table: `Key | Summary | Gate (what must resolve first) | Owner hint`

     **§4 — Needs shaping (Tier C + Blocked)**
     Table: `Key | Summary | Tier | Specific gap (which Q failed or content absent)`
     Footer: "These N stories need shaping before they can be executed."

  5. **Summary line**: "Sprint snapshot: <n> total. Agent-ready: <a>. Gated: <g>. Need
     shaping: <s+b>. Invocation repo: `<URL or unknown>`." (count tokens, not tier letters)

  6. **Pick-up hand-off** (after the snapshot, always): "Ready to pick one up?"
     Offer two options:
     - If §1 has stories: "Start delivery on `<highest-priority Quick story or highest-priority Tier A story if no Quick exists>`?
       [yes / pick another / skip]" → yes: for Bug issuetypes route to `jira-defect-flow`;
       for Task/Story issuetypes offer a `new-spec` session scoped to the story.
     - If §4 has stories: "Shape `<highest-priority Tier C/Blocked story key>` into
       a workable story? [yes / pick another / skip]" → yes: read the story's current
       content aloud, walk through each failed Q, and rewrite each field collaboratively
       with the user (using the five-question bar as the acceptance criterion for the
       rewrite), then offer to `update-issue` the story with the revised content.
     Both offers can be declined with "skip" — the skill does not force a hand-off.

- Don't: no Jira write verbs except when the user explicitly accepts the shaped-story
  `update-issue` in the pick-up flow; no local file reads; no reference to workspace.toml.
- Examples pointer to `references/examples.md`.

`manifest.json`: id `jira-team-status`; category `workflows`; deps.skills:
- `jira` (hard, this pack — all reads + the conditional `update-issue` call in the shaping hand-off)
- `jira-defect-flow` (soft, this pack — routed to when a Tier A story's issuetype is Bug/Defect; skill degrades gracefully if absent, surfaces an install hint)
- `new-spec` (soft, core pack — routed to when a Tier A story's issuetype is Story/Task; skill degrades gracefully if absent, surfaces an install hint)

`evals/eval_queries.json`:
- ≥8 `should_trigger: true`: "show team backlog for PROJ sprint 12", "team sprint
  status for PLATFORM team", "what can we ship this sprint", "plan the sprint
  backlog", "which stories are agent-ready for the team", "team backlog health
  check", "score our sprint and pick one up", "what should we start this sprint"
- ≥8 `should_trigger: false` including:
  - ≥4 workspace-status-shaped (e.g. "what's next in the workspace queue",
    "orient me to this repo", "where am I", "what should I work on today")
  - ≥3 triage-shaped (e.g. "triage the backlog by tier", "score these 20 stories",
    "run a backlog health audit for PROJ")
  - ≥1 primitive-jira-shaped (e.g. "show me my open Jira issues")

`references/examples.md`: one complete sprint snapshot (8 stories across all
four sections plus the pick-up hand-off exchange), one no-Tier-A scenario
(all stories in §3/§4, pick-up offers shaping only).

**Done when:** all four files exist; `lint-packs` green; greps pass; manual dry-run
passes.

---

### T4: Cross-file tier rubric consistency verified + pack metadata bumped

**Depends on:** T1, T2, T3

**Tests:**
- `grep "self-contained code/config/doc change" docs/specs/jira-story-actionability/spec.md packs/atlassian/.apm/skills/jira/SKILL.md packs/atlassian/.apm/skills/jira-story-triage/SKILL.md packs/atlassian/.apm/skills/jira-team-status/SKILL.md`
  returns 4 matches (one per file). Verifies AC8.
- `agentbundle validate` passes. Verifies AC10/AC12.
- `make build` produces no marketplace drift. Verifies AC10.
- Agentbundle package pytest passes. Verifies AC12 ("package pytest" is the CI-level
  behavioral test — if the local test runner can invoke it, run it here; otherwise
  note it as CI-only).

**Approach:**
- Run the four-file grep above; fix any file that missed the bar text before
  proceeding.
- `packs/atlassian/pack.toml`: bump version `0.4.1` → `0.5.0`; extend description
  to name both new workflow skills; add `jira-story-triage` and `jira-team-status`
  to `[pack.evals].skills`.
- `packs/atlassian/.claude-plugin/plugin.json`: sync version + description.
- Run `make build`.
- Run agentbundle package pytest (or note as CI-only if not available locally).

**Done when:** grep returns 4 matches, `validate` clean, `make build` no drift,
version is `0.5.0` in both toml + json, package pytest clean (or noted CI-only).

---

### T5: Docs suite and changelog updated

**Depends on:** T1, T2, T3

**Tests:**
- `grep "jira-story-triage\|jira-team-status" docs/guides/atlassian/how-to/work-with-jira.md` returns matches.
- `grep "jira-story-triage" docs/guides/atlassian/reference/atlassian-skills.md` returns a match.
- `grep "jira-team-status" docs/guides/atlassian/reference/atlassian-skills.md` returns a match.
- `grep "jira-story-triage\|jira-team-status" docs/guides/atlassian/README.md` returns matches.
- `grep "jira-story-triage\|jira-team-status" docs/guides/atlassian/explanation/atlassian-pack.md` returns matches.
- `grep "jira-story-triage\|jira-team-status" packs/atlassian/README.md` returns matches.
- `grep "jira-story-triage\|jira-team-status\|story quality\|pre-create gate" docs/product/changelog.md` returns a match in `[Unreleased]`.

**Approach:**

`docs/guides/atlassian/how-to/work-with-jira.md` — add `## Write actionable stories`
after "Create an issue": introduce the five-question bar and Q5 right-sizing (~200
words); note the `jira` skill applies the gate automatically on `create-issue`; link
to `jira-story-triage` (bulk audit) and `jira-team-status` (sprint entry point).

`docs/guides/atlassian/reference/atlassian-skills.md` — add `## jira-story-triage`
and `## jira-team-status` sections (Purpose / Primary inputs / Outputs / Required
credentials / Source) mirroring each skill's frontmatter `description`, placed after
`jira-brief-intake`.

`docs/guides/atlassian/README.md` — how-to list: add entries for both skills; pack
description: extend to name backlog management skills.

`docs/guides/atlassian/explanation/atlassian-pack.md` — "The skills that build on top"
section: add bullets for both new skills.

`packs/atlassian/README.md` — "What's inside" bullets: add both skills under
the workflow-skills bullet.

`docs/product/changelog.md` — under `[Unreleased]` → `Added`:
- `atlassian: story quality gate — six-point pre-create checklist with repo grounding (Q5 right-sizing) added to jira skill create-issue path`
- `atlassian: jira-story-triage — audit a Jira backlog by JQL against the five-question actionability bar; outputs Tier A/B/C/Blocked table`
- `atlassian: jira-team-status — team sprint backlog scored for agent-readiness with pick-up hand-off; four-section output modelled on workspace-status session-entry-point pattern`

**Done when:** all seven greps return matches, changelog entry present.

## Rollout

Pure catalogue content — no infra, no migration, no deployment sequencing. All three
deliverables ship when the PR merges; adopters get them on next `agentbundle install`/
`upgrade` of the atlassian pack. Fully reversible (revert the PR). The gate is additive
to `jira/SKILL.md` — existing `create-issue` patterns continue to work.

## Risks

- **Criterion drift** across four files. Mitigated by the four-file grep gate in T4.
- **Blocked pre-check ordering** — implementation must apply pre-check before tier
  scoring, not after. Verified by the T2/T3 manual dry-run against Blocked stories.
- **Trigger collision** (`jira-story-triage` vs `jira-team-status` vs `workspace-status`).
  Mitigated by mutual-exclusion eval false-positive sets and explicit "Do NOT use for"
  clauses in trigger descriptions.
- **Marketplace drift.** Mitigated by T4 running `make build` after all skills are
  authored (T4 `Depends on` ordering enforces this).
- **Reference-guide frontmatter drift** (T5). Mitigated by hand-checking the reference
  entries against the skill frontmatter descriptions.
- **Pick-up flow update-issue risk** — the jira-team-status shaping hand-off ends with
  an offer to `update-issue` the rewritten story. The existing `jira/SKILL.md` already
  requires confirming the issue key, fields, and payload before any update. The
  team-status flow must respect this by confirming the full rewritten payload with the
  user before calling `update-issue`. Mitigated by the "Ask first" boundary in the spec.

## Changelog

- 2026-07-23: initial plan.
- 2026-07-23: revised to fix adversarial-review blockers (tier rubric as total function
  anchored in spec; gate mapped to five-question bar + Q5 right-sizing; Blocked pre-check
  ordering explicit); incorporated user right-sizing requirement (Q5); added pick-up
  hand-off to jira-team-status; added mutual-exclusion evals for all three skill pairings;
  fixed declined-temptations register (DRY extraction, Python helper); added invocation-repo
  label discipline; T4 now includes cross-file consistency grep.
- 2026-07-23: added complexity grouping within Tier A (Quick/Standard/Involved) to both
  triage and team-status output per user request; pick-up hand-off defaults to Quick group first.
