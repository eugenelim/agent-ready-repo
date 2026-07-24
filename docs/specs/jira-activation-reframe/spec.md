# Spec: jira-activation-reframe

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none <!-- The activation contract for each skill is its evals/eval_queries.json (should_trigger set); it is a prompt-router contract, not a code interface, so no contracts/<type>/ file. -->
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A delivery lead or product owner asks their agent, in the language they already
use — *"what can the team pick up next?"*, *"what is blocked?"*, *"what is sitting
unassigned?"*, *"give me a team status for stand-up"*, *"which stories are not ready
for engineering?"*, *"clean up the weak items in the backlog"*, *"draft acceptance
criteria for the top five"* — and the right Atlassian skill activates **without the
user naming it**. Two skills own the split cleanly:

- **`jira-team-status`** answers *where the team's work stands* and *what to pick up
  next*. It is a read-only status snapshot organized by the dimensions people speak —
  **Ready to pull · In progress · Blocked · Unassigned · Needs detail**, plus a
  recently-changed note — with a pick-up hand-off. "Ready to pull" is a documented
  rule, not a silent `status = "To Do"`.
- **`jira-story-triage`** answers *are these items ready for engineering, and if not,
  fix them*. It reviews items against the five-question readiness bar, **explains why
  each weak item is not ready** (not merely a tier label), and can **improve** weak
  items — draft acceptance criteria, clarify the user outcome — writing the change
  back to Jira **only after the user approves the drafted payload**.

Success: each named phrase routes to the intended skill; the disambiguation boundary
between the two skills is pinned by their evals; the skill each phrase activates can
actually answer it; and the "ready to pull" rule is documented once, team-overridable,
and honest about uncertainty ("needs confirmation", never false certainty). The
five-question bar remains the readiness engine; "agent-readiness / Tier A/B/C" is
retired as the *headline* framing in favour of "ready for engineering / ready to pull
/ needs detail".

## Boundaries

### Always do

- **Lead with** the reader's language in every activation surface (descriptions,
  evals, guide pages): team, backlog, sprint, stand-up, ready, blocked, unassigned,
  stale, not ready, actionable. A documented power-user phrase from the guides (e.g.
  "apply the five-question bar") may ride along as an *additional* eval trigger, but
  the headline description prose stays in reader language.
- Keep the five-question readiness bar as the underlying engine of both skills, and
  keep its wording identical between the two skills (single source of the bar's text).
- Default `jira-team-status` to **read-only**; only write on an explicit user request
  to update a specific item, and only with a confirmed payload.
- In `jira-story-triage`, present the **why** for every not-ready item (which
  question failed and the specific gap), and draft proposed changes for review
  **before** any write.
- Keep every mirrored description in sync in the same PR (each skill's `manifest.json`,
  `reference/atlassian-skills.md`, `explanation/atlassian-pack.md`, both READMEs, the
  journey card).

### Ask first

- Any write to Jira (`update-issue`) — always gated on the user approving the exact
  drafted payload first.
- Changing the *default* eligible-state definition for "ready to pull" away from Jira
  `statusCategory = "To Do"` (teams override per-invocation; changing the shipped
  default is a design call).

### Never do

- Never add a new skill, a new module boundary, or a new pack dependency for this work
  — it reshapes two existing skills and their docs only.
- Never write to Jira without the user first approving the drafted payload.
- Never assert an item is "ready to pull" or "not ready" when the underlying signal
  (status, blocker, readiness) cannot be determined — label it **needs confirmation**.
- Never cite an RFC/ADR/spec inside shipped pack content (`.apm/**`).
- Never let a broadened description promise a capability the skill body cannot deliver
  (e.g. "unassigned" without fetching assignee).

## Testing Strategy

This change ships prompt/skill content and documentation, not executable code, so
verification is **goal-based** plus a **manual phrase-trace**:

- **Activation contract (goal-based).** Each skill's `evals/eval_queries.json` is
  self-consistent: every user phrase named in the Objective appears as a
  `should_trigger: true` case in the intended skill and, where it sits near the
  boundary, as a `should_trigger: false` case in the sibling skill. Verified by
  reading both eval files and confirming no phrase is a positive in both and no
  boundary phrase is unclaimed. (Running `tools/run-pack-evals.py` needs the live
  Skill-router / API and is not a cheap local probe; eval-file self-consistency +
  `build-check` is the local floor.)
- **Anti-tautology (goal-based).** An eval case only proves the *test* exists, not
  that the *description* carries trigger vocabulary. For each new trigger phrase,
  confirm its key terms (e.g. "unassigned", "stand-up", "blocked", "not ready",
  "acceptance criteria") also appear in the corresponding frontmatter `description`
  — so the router has real signal, not just a matching eval line.
- **Deliverability (manual QA / trace).** For each of the 13 named phrases, trace
  the activated skill's body to the section or flow that answers it — proving the
  skill can deliver, not just activate. Recorded in the plan.
- **Machinery (goal-based).** `make build-check` (or the pack build gate) passes;
  `marketplace.json` reflects `0.6.0`; version strings agree across `pack.toml`,
  `plugin.json`, `marketplace.json`; `lint-spec-status.py` clean.
- **Doc consistency (goal-based).** `grep` finds no surviving "Tier A / B / C" or
  "agent-readiness"-as-headline framing in the mirrored description surfaces, and the
  "ready to pull" rule appears once as the canonical definition with cross-references.

## Acceptance Criteria

- [x] `jira-team-status` frontmatter `description` activates on all seven of: "Show me
  the entire ATLAS backlog", "What can the team pick up next?", "What is blocked?",
  "What is sitting unassigned?", "What changed in this sprint?", "Give me a team status
  for stand-up", "Which items need product attention?" — each present as a
  `should_trigger: true` eval case.
- [x] `jira-story-triage` frontmatter `description` activates on all six of: "Which
  stories are not ready for engineering?", "Clean up the weak items in the backlog",
  "Make these tickets actionable", "Draft acceptance criteria for the top five", "Apply
  the five-question bar", "Show me what is missing before changing Jira" — each present
  as a `should_trigger: true` eval case.
- [x] Neither skill requires the user to name it; neither description leads with
  "agent-readiness" or "Tier A/B/C" as the headline framing. For each new trigger
  phrase, its key terms appear in the corresponding frontmatter `description` (not
  only in the eval file).
- [x] The disambiguation boundary is pinned. In `jira-story-triage`,
  `should_trigger: false` for: "What is blocked?", "What can the team pick up next?",
  "team status for stand-up", "Which items need product attention?", and "Show me the
  entire ATLAS backlog". In `jira-team-status`, `should_trigger: false` for: "Clean up
  the weak items in the backlog", "Make these tickets actionable", "Draft acceptance
  criteria for the top five", "Which stories are not ready for engineering?", and
  "Apply the five-question bar". No phrase is a positive trigger in both eval files. (Boundary rule: team-status
  *surfaces state and points* — including a coarse "needs detail" bucket answering
  "which need attention"; triage *assesses readiness with reasons and improves*. So
  "product attention" → team-status; "not ready for engineering" → triage.)
- [x] Activation is not regressed: every `should_trigger: true` phrasing in the current
  eval files is retained (or moved to the sibling as a negative if the boundary now
  assigns it there), and existing negatives are preserved. The reshape is additive to
  activation, not a replacement.
- [x] `jira-team-status` defines **"ready to pull"** as a four-clause rule — in the
  selected team scope + in an eligible backlog state (default `statusCategory = "To
  Do"`, team-overridable) + no known unresolved blocker + meets the team's
  story-readiness bar — and states the eligible statuses/fields are team-overridable.
- [x] When any clause of the ready-to-pull rule cannot be determined for an item,
  `jira-team-status` labels the item **needs confirmation** and does not assert ready
  or not-ready.
- [x] `jira-team-status` output is organized by the status dimensions Ready to pull /
  In progress / Blocked / Unassigned / Needs detail (plus a recently-changed note), and
  its intake fetches the fields those sections require (`assignee`, `updated`, status
  category, blocker signals).
- [x] `jira-team-status` is read-only by default; its body routes "shape/improve this"
  to `jira-story-triage` by name. It orchestrates no rewrite flow of its own; its only
  write is a bare pass-through to the `jira` skill's `update-issue` when the user
  explicitly asks to set a field, with the payload confirmed first.
- [x] `jira-team-status` retains its read-only **start-delivery** hand-off from the
  "Ready to pull" set (routing to `jira-defect-flow` for bugs, `new-spec` for
  tasks/stories); only the write-bearing *shaping* flow is removed and rerouted to
  `jira-story-triage`. The manifest `deps` reflect the surviving routes (`jira`,
  `jira-defect-flow`, `new-spec`, `jira-story-triage`).
- [x] `jira-story-triage` output explains, for every not-ready item, **which question
  failed and the specific gap** (the reason), not merely a tier/score label.
- [x] `jira-story-triage` can improve a weak item (draft acceptance criteria, clarify
  the outcome) and write it back via `update-issue` **only after the user approves the
  drafted payload**; the drafted payload is shown before any write.
- [x] The five-question bar text is identical in both `SKILL.md` files.
- [x] All mirrored description surfaces are synced: each `manifest.json`,
  `reference/atlassian-skills.md`, `explanation/atlassian-pack.md`,
  `docs/guides/atlassian/README.md`, `packs/atlassian/README.md`, and the journey card
  reflect the new purpose and split; `references/examples.md` for both skills shows the
  new output.
- [x] `work-with-jira.md` documents "ready to pull" (or cross-references the canonical
  definition) and points readers to the two skills in the reader's own language.
- [x] Pack version is `0.6.0` in `pack.toml` and `plugin.json`; `marketplace.json` is
  regenerated to match; `docs/product/changelog.md` carries an entry under
  `[Unreleased]`. Each reshaped skill's `manifest.json` `version` and `SKILL.md`
  `metadata.version` bump to `1.1` (the contract changed materially).
- [x] `make build-check` (pack build gate) passes and `lint-spec-status.py` is clean.

## Assumptions

- Technical: pack is at `0.5.0`; target `0.6.0` (source: `packs/atlassian/pack.toml`).
- Technical: both skills are in `[pack.evals]` and each ships `evals/eval_queries.json`
  with `{query, should_trigger}` objects (source: `pack.toml`, the two eval files).
- Technical: activation is measured at the Skill-router by `tools/run-pack-evals.py`,
  which needs the live router/API — not a cheap side-effect-free probe; local
  verification degrades to eval self-consistency + `build-check` (source: `pack.toml`
  evals-section comment).
- Technical: descriptions are mirrored (and stale on change) in each skill's
  `manifest.json`, `reference/atlassian-skills.md`, `explanation/atlassian-pack.md`,
  both READMEs, and `web/src/content/journeys/atlassian.md`; `marketplace.json`
  regenerates via `build-self` (source: grep across those files + memory on
  reference-guide mirroring).
- Technical: "eligible backlog state" default = Jira `statusCategory = "To Do"`, the
  stable three-value category enum (To Do / In Progress / Done) portable across
  instances; named statuses vary and are team-overridable (source: Jira REST platform
  contract; user confirmation 2026-07-23).
- Process: a pack prose change requires a `docs/product/changelog.md` entry and a
  version bump; the bump PR is the release via the marketplace aggregate; no
  RFC/ADR/spec citations inside `.apm/**` (source: memory + how atlassian 0.5.0 shipped).
- Product: the write/improve path moves to `jira-story-triage` and `jira-team-status`
  becomes read-only by default (Decision A; source: user confirmation 2026-07-23).
- Product: "agent-readiness / Tier A/B/C" is retired as the headline framing, keeping
  the five-question bar as the engine (Decision C; source: user confirmation
  2026-07-23).
- Product: `jira-team-status` output restructures into status dimensions requiring
  `assignee`/`updated`/blocker fetches (Decision D; source: user confirmation
  2026-07-23).
- Product: "the documentation skill" means the Atlassian guide pages, revised per
  `new-guide` doctrine (Decision B; source: user confirmation 2026-07-23).
