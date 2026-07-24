# Plan: jira-activation-reframe

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is entirely prompt/skill content and documentation — no executable code.
It reshapes two existing skills so they activate from the language delivery leads and
POs actually use, pins the boundary between them in their evals, documents the
"ready to pull" rule, and syncs every mirrored description surface, then bumps the
pack and regenerates the marketplace.

Order of operations: `jira-story-triage` first (it becomes the owner of the
improve→approve→write path, so `jira-team-status` can route to it by name), then
`jira-team-status` (read-only snapshot + ready-to-pull rule + status dimensions),
then a consistency pass to keep the five-question bar text byte-identical across both
`SKILL.md` files, then the documentation surfaces (per `new-guide` doctrine), then the
version/changelog/build machinery. The riskiest part is the disambiguation boundary:
the broadened triggers ("what is blocked?" vs "which stories are not ready?", "entire
backlog" vs "clean up the backlog") sit close, so the evals must carry the
cross-boundary negatives that pin each phrase to exactly one skill.

## Constraints

- No RFC/ADR/spec citations inside `.apm/**` (shipped pack content).
- Descriptions are hand-mirrored across six surfaces + the marketplace; the reference
  guide for this pack uses a Purpose/Inputs/Outputs shape (not byte-verbatim
  frontmatter), so sync meaning, not bytes, there.
- The bump PR is the release; `marketplace.json` must be regenerated via `build-self`.

## Construction tests

**Integration tests:** none beyond per-task checks (no executable code).

**Manual verification (phrase-trace, AC-linked):** for each of the 13 named phrases,
confirm (a) it is a `should_trigger: true` case in the intended skill's eval file and
absent-or-negative in the sibling's, and (b) the activated skill body has a section or
flow that answers it. Recorded at DECIDE.

## Design (LLD)

### Design decisions

- **Boundary rule — surface-state vs. assess-quality.** `jira-team-status` *surfaces
  state and points* — a read-only dashboard of where work stands and what to pick up,
  including a coarse "needs detail" bucket that answers "which items need attention".
  `jira-story-triage` *assesses readiness with reasons and improves* — a depth review
  against the five-question bar plus write-after-approval. The verbal test that routes
  a phrase: *know the situation / pick something up / who needs attention* →
  team-status; *judge whether items are ready for engineering, or fix them* → triage.
  So "which items need product attention?" → team-status (surfacing); "which stories
  are not ready for engineering?" → triage (readiness judgment). Traces to: AC4.
- **The orchestrated improvement write flow lives in triage only.** Only
  `jira-story-triage` orchestrates a shaping/improvement write (draft ACs → approve →
  `update-issue`); team-status routes "shape this" to triage by name and keeps its
  read-only *start-delivery* hand-off. team-status's one remaining write is a **bare
  pass-through** to the `jira` skill's `update-issue` when the user explicitly asks to
  set a field — never its own multi-step rewrite flow. Alternative (two orchestrated
  write flows) rejected — they drift. Traces to: AC9, AC12.
- **Eligible-state default = `statusCategory = "To Do"`.** Portable across instances
  (stable 3-value enum), cleanly separates ready-to-pull from in-progress; teams
  override with explicit statuses. Alternative (`statusCategory != Done`) rejected — it
  includes in-progress work, which is not "pick up next". Traces to: AC6.
- **"Blocked" disambiguation.** Today the pre-check calls unscoreable stories
  (empty/image-only/discovery-type) "Blocked"; the user's "what is blocked?" means
  *impediment*-blocked. Rename the unscoreable bucket to **Needs detail** and reserve
  **Blocked** for impediment/flag/blocked-by/blocked-status. Traces to: AC7, AC8.

### Behavior & rules

- **Ready-to-pull rule (canonical, in `jira-team-status`).** An item is *ready to
  pull* when all four hold: (1) it belongs to the selected team scope; (2) it is in an
  eligible backlog state — default `statusCategory = "To Do"`, team-overridable by
  naming explicit statuses/fields; (3) it has no known unresolved blocker; (4) it meets
  the team's story-readiness bar (the five-question bar). If any clause is
  undeterminable → **needs confirmation** (never asserted ready or not-ready). Traces
  to: AC6, AC7.
- **Blocker signal (feeds ready-to-pull clause 3 and the "Blocked" dimension).** An
  item counts as blocked when any of: (a) the "Flagged"/impediment field is set; (b) it
  has an unresolved outward "is blocked by" issuelink; (c) its status is in a
  team-declared blocked set (none by default). When none of the three can be read from
  the fetched fields, the blocker state is undeterminable → the item is **needs
  confirmation**, not asserted blocked or unblocked. Traces to: AC6, AC7.
- **Five-question readiness bar (shared engine, byte-identical in both skills).**
  Q1 self-contained change · Q2 reachable repo/file scope · Q3 acceptance criteria
  checkable by diff review · Q4 no mid-flight human decision · Q5 right-sized for one
  PR. Traces to: AC13.
- **Reason-first triage output.** Every not-ready item names *which question failed*
  and the *specific gap* (e.g. "Q3: no acceptance criteria; Q2: no repo named"), not a
  bare tier label. Traces to: AC11.

## Tasks

### T1: `jira-story-triage` reviews with reasons and improves weak items after approval

**Depends on:** none

**Tests:**
- Trace AC2/AC4/AC11/AC12/AC13: the six triage phrases each appear as `should_trigger:
  true` in `evals/eval_queries.json`; the boundary negatives ("What is blocked?", "What
  can the team pick up next?", "team status for stand-up", "Which items need product
  attention?", "Show me the entire ATLAS backlog") appear as `should_trigger: false`.
- No-regression (AC5): every existing `should_trigger: true` phrasing is retained and
  existing negatives preserved.
- Body has a read-only review flow whose output states the failed question + specific
  gap per not-ready item (reason-first), and a separate improve flow that drafts ACs /
  clarifies the outcome, shows the drafted payload, and only calls `update-issue` after
  explicit approval.
- `references/examples.md` shows a reason-first review and an approve-then-write
  improvement.
- `manifest.json` description + output + `deps` reflect the write path; `version` →
  `1.1.0`; `SKILL.md` `metadata.version` → `1.1`.

**Approach:**
- Rewrite frontmatter `description` to the confirmed text (readiness review + improve
  weak items; write only after approval), ensuring each new trigger phrase's key terms
  appear in the description (anti-tautology).
- Reframe headline from "agent-readiness / Tier A/B/C" to "ready for engineering /
  needs detail"; keep the five-question bar wording verbatim. Rename the unscoreable
  "Blocked" pre-check bucket to "Needs detail".
- **Reverse the read-only lock explicitly:** excise the `## Don't` bullets "Don't write
  any Jira verb other than `search` and `get-issue`… read-only" and "rewriting is for
  the `jira-team-status` shaping hand-off" (`SKILL.md:192-195`), replacing them with the
  approval-gated write contract.
- Add the improve→draft→approve→`update-issue` flow; keep the read-only review as the
  default entry.
- Update `evals/eval_queries.json`, `manifest.json` (drop "never a write verb"; `jira`
  purpose now includes `update-issue` after approval), `references/examples.md`.

**Done when:** the six phrases are positive evals, the five boundary phrases are
negative, existing triggers are not regressed, output is reason-first, the write flow is
approval-gated, and all four triage artifacts agree.

### T2: `jira-team-status` is a read-only status snapshot with a documented ready-to-pull rule

**Depends on:** T1 (routes "shape this" to `jira-story-triage` by name)

**Tests:**
- Trace AC1/AC4: the seven team-status phrases each appear as `should_trigger: true`;
  the boundary negatives ("Clean up the weak items in the backlog", "Make these tickets
  actionable", "Draft acceptance criteria for the top five", "Which stories are not
  ready for engineering?") appear as `should_trigger: false`.
- No-regression: existing `should_trigger: true`/`false` phrasings retained.
- Body defines the four-clause ready-to-pull rule with the `statusCategory = "To Do"`
  default + team-override note + "needs confirmation" fallback (AC6, AC7).
- Output is organized by Ready to pull / In progress / Blocked / Unassigned / Needs
  detail + a recently-changed note; intake fetches `assignee`, `updated`, status
  category, and blocker signals, and supports a full-backlog (sprint-less) scope for
  "show me the entire backlog" (AC8).
- Body is read-only by default; routes shaping to `jira-story-triage`; retains the
  read-only start-delivery hand-off to `jira-defect-flow`/`new-spec`; writes only on
  explicit user update request with a confirmed payload (AC9, AC10).
- `references/examples.md` shows the dimension-organized snapshot; `manifest.json`
  reflects read-only + the triage route + surviving deps; `version` → `1.1.0`;
  `SKILL.md` `metadata.version` → `1.1`.

**Approach:**
- Rewrite frontmatter `description` to the confirmed text, ensuring each new trigger
  phrase's key terms appear in the description (anti-tautology).
- Replace the four readiness-tier sections with the five status dimensions + recently-
  changed note; fold complexity grouping into "Ready to pull". Support a full-backlog
  scope (drop the `sprint in openSprints()` default when the user asks for the whole
  backlog).
- Add the ready-to-pull rule + blocker-signal + intake field list; keep the
  five-question bar wording verbatim (matching T1).
- **Reverse the write-bearing shaping flow explicitly:** replace stage-6 Option B
  (the collaborative rewrite + `update-issue`, `SKILL.md:170-186`) with a route to
  `jira-story-triage` by name; update the `## Don't` bullet "Read-only outside the
  shaping hand-off" (`SKILL.md:202`) to "read-only by default; improvement is
  `jira-story-triage`'s job"; keep Option A (start-delivery routing) intact.
- Excise the collaborative-rewrite-and-`update-issue` walkthrough from
  `references/examples.md` (Example 1, lines ~115-157) and replace with the read-only
  snapshot + triage route.
- Update `evals/eval_queries.json`, `manifest.json` (add `jira-story-triage` soft dep;
  keep `jira`/`jira-defect-flow`/`new-spec`).

**Done when:** the seven phrases are positive evals, the four boundary phrases are
negative, existing triggers are not regressed, the ready-to-pull rule +
needs-confirmation fallback are documented, output is dimension-organized, the
start-delivery hand-off survives, and the skill is read-only by default.

### T3: five-question bar text is byte-identical across both skills

**Depends on:** T1, T2

**Tests:**
- `diff` of the bar blockquote between the two `SKILL.md` files is empty (AC13).

**Approach:**
- After T1 and T2, reconcile the bar blockquote so both files carry identical text.

**Done when:** the bar block matches byte-for-byte in both skills.

### T4: documentation surfaces speak the reader's language and document ready-to-pull

**Depends on:** T1, T2, T3

**Tests:**
- `grep` finds no surviving "Tier A / B / C" or "agent-readiness"-as-headline framing
  in `reference/atlassian-skills.md`, `explanation/atlassian-pack.md`,
  `docs/guides/atlassian/README.md`, `packs/atlassian/README.md`, or the journey card
  (AC3, AC14).
- `work-with-jira.md` documents "ready to pull" (or cross-references the canonical
  definition) and points to the two skills in the reader's language (AC15).
- The two skills' entries in `reference/atlassian-skills.md` match the new purposes
  (AC14).

**Approach:**
- Revise per `new-guide` doctrine: reference entries, explanation bullets, both
  READMEs, journey card, and the `work-with-jira.md` "Write actionable stories" /
  cross-reference sections.
- Add the ready-to-pull definition to `work-with-jira.md` (canonical prose home for
  the concept in docs), cross-referenced from the skill.

**Done when:** grep is clean of stale framing, ready-to-pull is documented once, and
all doc surfaces reflect the new split.

### T5: pack bumped to 0.6.0, changelog updated, marketplace regenerated

**Depends on:** T1, T2, T3, T4

**Tests:**
- `pack.toml` and `plugin.json` both read `0.6.0`; `marketplace.json` reflects `0.6.0`
  (AC16). Both reshaped skills' `manifest.json` `version` = `1.1.0` and `SKILL.md`
  `metadata.version` = `1.1`.
- `docs/product/changelog.md` has an `[Unreleased]` entry for atlassian 0.6.0.
- `make build-check` (pack build gate) passes; `lint-spec-status.py` clean (AC17).

**Approach:**
- Bump `pack.toml` + `plugin.json` to `0.6.0` (per-skill version bumps land in T1/T2).
- Add the changelog entry under `[Unreleased]`.
- Run `build-self` to regenerate `marketplace.json`; run the build gate.

**Done when:** versions agree (pack + both skills), changelog carries the entry, and the
build gate passes.

## Rollout

Pure content/docs change. Delivery: the version-bump PR is the release (marketplace
aggregate). No infrastructure, no external-system integration, no migration. Reversible
by revert. No irreversible step.

## Risks

- **Boundary bleed at the router.** The two skills' broadened triggers are adjacent;
  if the evals don't carry the cross-boundary negatives, the router may fire the wrong
  skill. Mitigation: AC4 pins the negatives explicitly.
- **Description-lie drift.** A broadened description that promises a dimension the body
  can't answer. Mitigation: T2 fetches the fields its sections need; the phrase-trace
  at DECIDE checks deliverability, not just activation.
- **Mirror drift.** Six mirrored surfaces + marketplace; missing one ships stale.
  Mitigation: AC12 enumerates them; T4/T5 sync all.

## Changelog

- 2026-07-23: initial plan.
