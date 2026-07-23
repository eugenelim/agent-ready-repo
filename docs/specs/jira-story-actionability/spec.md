# Spec: jira-story-actionability

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0019 <!-- scoped atlassian-pack authoring-quality work to the non-core atlassian pack; `Epic:`-pointer-only cross-repo discipline applies to triage output too -->
- **Brief:** none
- **Contract:** none
- **Shape:** integration <!-- composes the existing `jira` skill for all reads/writes; ships choreography prose, not executable logic, so the plan's `## Design (LLD)` is intentionally empty -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Teams are creating Jira stories that fail a simple actionability bar — they cannot be handed to an agent or an engineer without a meeting, a missing decision, or content that is literally not text. Triaging 72 stories from a single week found only 18–20 genuinely executable: the rest were Solution Design artifacts, image-only descriptions, discovery framing disguised as implementation tasks, or stories sized for a whole team's sprint rather than a single bounded change.

Jira stories are an **old delivery-capacity allocation mechanism**: a sprint full of "stories" can mask a wide range in actual scope — from a two-line config change to a month of cross-team work. Before routing a story to an agent or an engineer who operates like one, the story must pass a right-sizing check as well as a quality check.

Four gaps drive this:

1. **No gate at story creation.** The `jira` skill's `create-issue` confirms intent and shows the payload but does not check whether the story is implementable or right-sized. A story can be created with an empty description, a vague summary, no acceptance criteria, and epic-scale scope.
2. **No backlog triage skill.** When a backlog has already accumulated non-churnable stories, there is no workflow to score them against the actionability bar and surface the agent-ready set.
3. **No team-status skill.** There is no single command that shows a team's Jira backlog scored for agent-readiness, identifying what can be parallelised vs. what needs human shaping first.
4. **No consistent tier rubric.** Without a single source-of-truth classification, a story could score differently in the gate vs. the triage skill vs. the team-status skill — defeating the point of having a bar.

This spec closes all four gaps with **a gate, two skills, and a canonical tier rubric**, all in the atlassian pack:

- **Story quality gate** — added to `jira/SKILL.md`'s `create-issue` path only (not `update-issue`): repo grounding detection, then a six-point pre-create checklist enforcing the actionability bar. No new files; a targeted edit to the existing skill.
- **`jira-story-triage` skill** — given a JQL query (or sprint/board), fetches stories via the `jira` skill, evaluates each against the five-question actionability bar, and outputs a Tier A / B / C / Blocked table the team can act on directly.
- **`jira-team-status` skill** — given a Jira project key and optional sprint/team context, shows the full team Jira backlog scored, identifies the agent-ready set, batches parallel-safe stories, and flags stories needing shaping. Modelled on `workspace-status`'s session-entry-point pattern: after displaying the scored snapshot it offers to hand off — "pick up" a Tier A story to start delivery, or a Tier C/Blocked story to shape it into an actionable form. **Reads from Jira only for the snapshot; with explicit user consent in the shaping hand-off, it may call `update-issue` once on the story the user chose to rewrite.** No local files; no repo workspace queue. Distinct from `workspace-status` (a different skill in a different pack that reads the local repo queue) by both domain and trigger vocabulary.

## The actionability bar and tier rubric

These two definitions are the **canonical source of truth** for this spec. Both new skill `SKILL.md` files must reproduce the five-question bar and the tier rubric verbatim — no paraphrasing. The gate in `jira/SKILL.md` must reproduce the five-question bar verbatim; it does not need the tier rubric table (the gate classifies only pass/fail per check, never into tiers).

### Five-question actionability bar

> A story is actionable when all five are true:
> (Q1) it is a **self-contained code/config/doc change** — not discovery, design, or coordination work;
> (Q2) it names a **reachable repo or file scope** so the change can be located without a follow-up meeting;
> (Q3) its **acceptance criteria are checkable by diff review alone** — no "TBD", "coordinate with", "decide on", or "prototype";
> (Q4) **no human decision is needed mid-flight** — no open design question, no external approval gate that cannot be confirmed before work starts;
> (Q5) it is **right-sized for one PR** — the scope is an enumerable set of files or PRs a single person or agent can produce without decomposing into sub-stories.

Q5 is new relative to the commonly cited four-question form. It exists because Jira stories are an old delivery-capacity allocation mechanism: a story sized for a full sprint or cross-team effort passes Q1–Q4 but still cannot be handed to an agent without being broken down first. Right-sizing is a separate, necessary gate. The canonical unit for Q5 is **one PR** — a story is right-sized when its scope can be described as an enumerable set of files or PRs a single person or agent can produce without decomposing into sub-stories. Story-point fields (where present in the fetched `customfield_*`) above the team's typical single-story threshold (e.g. > 5 points if the team's convention is Fibonacci) are a secondary signal; textual tells ("cross-team", "multi-week", "multiple repos") are a tertiary signal.

### Tier rubric — total function over the five-question bar

Classification is a total function: every story that passes the Blocked pre-check receives exactly one of Tier A, B, or C. The pre-check runs first and short-circuits scoring.

**Pre-check (runs before scoring; triggers → Blocked, skip scoring):**
A story is **Blocked** when its description is empty, image-only (`!image-…!` Jira wiki markup), or its `issuetype` is a discovery artifact (Solution Design, Discovery, Spike without acceptance criteria, or equivalent). Blocked stories cannot be scored meaningfully because the minimum content for evaluation is absent.

**Scored tiers (apply only after the pre-check passes):**

| Tier | Condition |
|---|---|
| **A — Turnkey** | All five bar questions pass. The story can be started immediately. |
| **B — Gated** | Exactly one bar question fails, AND that failure is an **external gate**: a specific named decision pending from a named person, credentials not yet provisioned but provisioning is confirmed, or an external dependency available on a specific future date. Content failures (missing repo scope, missing ACs, missing right-sizing) are **never** Tier B regardless of how many other questions pass. |
| **C — Needs shaping** | Any other outcome: any content dimension fails (Q1, Q2, Q3 missing/wrong), or Q4 fails with an open design question rather than a named external gate, or Q5 fails (story is too large and needs decomposition). |

Example disambiguation (the case the adversarial review flagged): a story that passes Q1/Q3/Q4/Q5 but fails Q2 (no repo scope) → Tier C, because Q2 failure is a content problem, never an external gate.

## Boundaries

### Always do

- Route every Jira read through the `jira` skill by name, never by path, never via a raw REST call.
- Apply the pre-create quality gate on **`create-issue` intent only** — not on `update-issue`. The gate is a check, not a full spec authoring workflow; it pauses to elicit the missing signal (repo, ACs, right-sizing) and stops if the story cannot be made actionable in context.
- Detect repo context automatically where available (`git remote -v` in the working directory). When not in a git repo, offer the user an opportunity to supply a repo URL or name — clearly optional, with an explanation of why it improves output quality. Label grounding as "invocation repo" in all outputs — it is the repo the agent is running from, not necessarily the target of every story. Never block indefinitely on grounding; proceed with "invocation repo: unknown" if the user declines.
- Present triage and status output as **actionable tables**, not walls of prose. Every row independently readable.
- Apply the tier rubric from this spec verbatim — pre-check first, then the tier table. Never invent partial tiers.
- In `jira-team-status`, surface the agent-ready set (Tier A) first so a delivery lead can act immediately. Within Tier A, **group by complexity** (`Quick` → `Standard` → `Involved`) so team members can self-select based on available bandwidth — a quick story for a short window, an involved story for a full-day block.

### Ask first

- Before filing a `create-issue` whose summary or description contains discovery-language signals — do not silently rewrite the story; flag the signals and ask whether the user wants to fix them or proceed with an explicit override.
- Before classifying a story with a suspected image-only description as Blocked — fetch the raw description via the `jira` skill to confirm the content is absent, not truncated.

### Never do

- Never write a raw Jira REST call inside `jira-story-triage/SKILL.md` or `jira-team-status/SKILL.md` — all reads go through the `jira` skill by name.
- Never rewrite a story's summary, description, or acceptance criteria without the user's explicit instruction.
- Never block or hard-stop on `create-issue` — the gate pauses to elicit and allows the user to override; it is an advisory gate, not a hard lock.
- Never conflate `jira-team-status` with `workspace-status` in trigger phrases, description, or documentation.
- Never score a story based solely on its summary — always read description and ACs fields.
- Never modify the `core` pack; never modify any skill outside `packs/atlassian/`.
- Never add a dependency on a package not already in `requirements.txt`.

## Acceptance Criteria

- [x] **AC1 — Quality gate wired into `jira/SKILL.md`:** a "Repo grounding and pre-create quality gate" sub-section appears in Step 5 before the first `create-issue` example and: (a) detects git remote URL when available and labels it "invocation repo"; (b) prompts the user to supply a repo URL or name when not in a git repo (optional, with explanation, non-blocking); (c) runs the six checks (summary specificity, repo/file scope, ACs present and binary, no discovery/coordination language and issuetype appropriate for Q1, no mid-flight approval gate for Q4, right-sized for one PR for Q5) before constructing the payload; (d) pauses to elicit missing signals rather than silently passing; (e) allows the user to override and proceed after explicit acknowledgment; (f) fires on `create-issue` intent only, not on `update-issue`.
- [x] **AC2 — Six-point checklist is explicit and auditable:** each check has a named signal (what the gate looks for), a named bar question it enforces (Q1–Q5), a failure mode, and an elicitation prompt. The "Don't" section reinforces the gate with a dedicated bullet.
- [x] **AC3 — `jira-story-triage` skill is authored and well-formed:** skill directory at `packs/atlassian/.apm/skills/jira-story-triage/` with `SKILL.md`, `manifest.json`, `evals/eval_queries.json`, and `references/examples.md`; `lint-packs` passes; `SKILL.md` quotes the five-question bar and tier rubric from this spec verbatim; outputs a Tier A / B / C / Blocked table per story with an "Invocation repo" header line; Tier A rows include a **Complexity** column (`Quick` / `Standard` / `Involved`) derived from story-point field (when present), number of ACs, and scope description length, so the team can self-select based on bandwidth.
- [x] **AC4 — `jira-story-triage` performs repo grounding:** git remote URL captured when available; user prompted when not in a git repo; grounding appears as "Invocation repo: `<URL>`" or "Invocation repo: unknown" in the output header.
- [x] **AC5 — `jira-team-status` skill is authored and well-formed:** skill directory at `packs/atlassian/.apm/skills/jira-team-status/` with the same four file types; `lint-packs` passes; `SKILL.md` quotes the five-question bar and tier rubric from this spec verbatim; output has four labelled sections: Agent-ready (Tier A), Parallel batching candidates, Gated (Tier B), and Needs shaping (Tier C / Blocked); **within the Agent-ready section, stories are grouped by complexity** (`Quick` / `Standard` / `Involved` — derived from story-point field if present, number of ACs, and scope description length) so team members can self-select based on bandwidth; repo grounding performed and labelled "Invocation repo" in the output summary line; after the scored snapshot the skill offers a **pick-up hand-off** — it lists the top Tier A story (from the Quick group first) and asks "start delivery on this?" and the highest-priority Tier C/Blocked story and asks "shape this into a workable story?" — routing delivery to `jira-defect-flow` (defect type) or a new-spec session (task/story type), and routing shaping to conversational story rewriting with the user; the shaping hand-off confirms the complete rewritten payload with the user **before** calling `update-issue` — the skill never writes to Jira without explicit acceptance of the specific fields being updated.
- [x] **AC6 — `jira-team-status` is unambiguously distinct from `workspace-status`:** trigger description has an explicit "Do NOT use for" clause naming orientation and local queue queries (without referencing workspace.toml internals); the `evals/eval_queries.json` false-positive set contains ≥4 queries that route to `workspace-status` (`should_trigger: false`); the skill body makes no reference to local repo files or local queues.
- [x] **AC7 — `jira-story-triage` and `jira-team-status` are mutually disambiguated:** each skill's `evals/eval_queries.json` false-positive set contains ≥3 queries shaped like the other skill's true-positive queries (`should_trigger: false`), so the harness can route them correctly.
- [x] **AC8 — Tier rubric is consistent across all three deliverables:** a grep for the first sentence of the five-question bar ("self-contained code/config/doc change") hits the spec, `jira/SKILL.md` (gate text), `jira-story-triage/SKILL.md`, and `jira-team-status/SKILL.md` — all four files. The tier rubric table (pre-check, A, B, C) appears verbatim in both new skill bodies.
- [x] **AC9 — Docs suite updated:** `docs/guides/atlassian/how-to/work-with-jira.md` has a "Write actionable stories" section including the right-sizing check; `docs/guides/atlassian/reference/atlassian-skills.md` has entries for both new skills; `docs/guides/atlassian/README.md` names both new skills; `docs/guides/atlassian/explanation/atlassian-pack.md` has bullets for both new skills; `packs/atlassian/README.md` names both new skills.
- [x] **AC10 — Pack metadata clean:** `packs/atlassian/pack.toml` version bumped to `0.5.0`; `packs/atlassian/.claude-plugin/plugin.json` synced; `make build` regenerates `.claude-plugin/marketplace.json` with no drift; both new skill names added to `[pack.evals].skills`.
- [x] **AC11 — Changelog entry:** `docs/product/changelog.md` `[Unreleased]` records all three deliverables.
- [x] **AC12 — Pack gate green:** `lint-packs`, `agentbundle validate`, `make build`, and the agentbundle package pytest all pass with no regressions.

## Testing Strategy

This change ships **prose primitives** (two `SKILL.md` files, a `manifest.json` per skill, reference docs, evals) plus a targeted edit to an existing `SKILL.md`. No new executable logic — no TDD-mode tasks.

- **Pack metadata: goal-based check.** `lint-packs` green for the whole pack; `agentbundle validate` clean; `make build` with no marketplace drift.
- **Tier-rubric consistency: grep-based.** `grep "self-contained code/config/doc change"` across all four files (spec, gate, triage, team-status) returns four matches. Verifies AC8.
- **Activation / non-activation: eval-based.** Each new skill has `evals/eval_queries.json` with ≥8 `should_trigger: true` + ≥8 `should_trigger: false`, including ≥4 workspace-status-shaped false positives (team-status) and ≥3 cross-skill false positives (each new skill vs. the other).
- **Docs completeness: grep-based.** Both new skill names appear in all five doc files named in AC9.
- **Manual dry-run — gate:** gate text appears before the first `create-issue` example; six checks are named with bar-question mapping; "Don't" bullet present; gate is explicitly `create-issue`-only. Verifies AC1, AC2.
- **Manual dry-run — `jira-story-triage`:** reading-level pass against 12 stories (3 Tier A, 2 Tier B, 3 Tier C via Q5 fail, 2 Tier C via content fail, 2 Blocked) confirms the rubric is applied in the right order (Blocked pre-check first), the tier table is produced, and the invocation-repo header is present. Verifies AC3, AC4.
- **Manual dry-run — `jira-team-status`:** four output sections in correct order; invocation-repo in summary line; no local file reference; trigger phrases distinct from workspace-status. Verifies AC5, AC6.

## Assumptions

- Technical: the `jira` skill's `search` subcommand can fetch description and ACs fields in bulk via `--fields "summary,description,issuetype,status,priority,labels,customfield_*"`, sufficient for quality-bar evaluation (source: read `jira/SKILL.md` Steps 3–4, probe 2026-07-23).
- Technical: `git remote -v` returns the repo URL reliably in standard git repos (source: standard git behaviour).
- Technical: the gate insert point (Step 5 of `jira/SKILL.md`, before `create-issue` examples) extends rather than contradicts the existing "confirm the intent" caution (source: read `jira/SKILL.md` Step 5, probe 2026-07-23).
- Product: an integrated gate on `create-issue` is preferable to a separate opt-in skill — the gate fires without the user remembering to invoke it (source: user confirmation 2026-07-23).
- Product: right-sizing (Q5) is a necessary fifth bar question because Jira stories are an old delivery-capacity allocation mechanism that can mask epic-scale scope (source: user confirmation 2026-07-23).
- Product: the `jira-team-status` name does not collide with `workspace-status` — mutually exclusive domains (Jira-external vs. local repo queue); confirmed by eval false-positive sets (source: read `workspace-status/SKILL.md`, probe 2026-07-23).
- Scope: discovery-language detection is English-only and uses word-boundary matching; non-English Jira instances and custom issuetypes outside the named set fall through to a "type unknown — manual review" label. Acknowledged limitation; out of scope for this spec.
- Scope: grounding identifies the agent's invocation repo, not necessarily the target repo of every story — labelled "invocation repo" throughout to prevent misreading.
- Process: atlassian is user-scope-default; gate is `lint-packs` + `validate` + `build` + package pytest, not `build-self`/`pre-pr`.
