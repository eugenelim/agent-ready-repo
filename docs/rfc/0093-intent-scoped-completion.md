# RFC-0093: Intent-scoped completion

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-19
- **Date closed:** 2026-08-20
- **Decision weight:** heavy
- **Related:** [RFC-0090](0090-change-sizing-and-decomposition.md);
  [RFC-0083](0083-work-intake-and-artifact-routing.md)

## Reviewer brief

- **Decision:** Make completion answer to the original accepted intent rather
  than to one pull request, and make durable follow-on capture opt-in.
- **Recommended outcome:** Accept.
- **Change if accepted:** Define **intent fit** (whether a discovery belongs to
  the accepted intent) and dispositions; allow separate **review units**
  (independently reviewable changes) within one session; remove mandatory
  backlog capture for work not included.
- **Affected surface:** The adopter-facing conventions and the `work-loop`
  workflow that turns review findings into action or deferral.
- **Stakes:** Costly but reversible: this changes an obligation shipped to
  adopters, while retaining existing safety stops.
- **Review focus:** Whether the proposal preserves a truthful completion test
  without turning adjacent work into an automatic queue.
- **Not in scope:** A new backlog type, workspace schema field, lint, or
  durable completion artifact.

## The ask

Approve **intent-stable, review-unit-flexible, capture-by-request** (durable
follow-ons are created only when their owner asks to remember them): an accepted
intent remains the completion boundary even when delivery needs more than one
review unit, and a finding outside the chosen work is remembered only when its
owner explicitly requests capture.

The current workflow treats inability to fit a finding into the current pull
request as durable deferral. That confuses reviewer-sized delivery with whether
the accepted outcome is complete, and it manufactures follow-ons from
otherwise excluded improvements.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | What is the completion boundary? | The original accepted intent. | A review unit is a delivery boundary, not the outcome's boundary. | RFC acceptance | Approve or amend the boundary. |
| D2 | How is a discovery dispositioned? | Capture only on explicit request. | Excluding work is an acknowledgement, not an obligation to create a queue item. | RFC acceptance | Approve or amend the disposition rule. |
| D3 | Where does an included discovery land? | In the current unit when authorized by the accepted contract and eligible under RFC-0090 D6's ride-along tiers; otherwise in the next review unit of the same session. | Review safety does not require ending the session. | RFC acceptance | Approve or amend the separation. |
| D4 | What does repeated review discovery mean? | In-scope correctness remains blocking; safety caps pause for human judgment, never declare completion or create backlog automatically. | Bounded autonomy must not falsify completion. | RFC acceptance | Approve or amend the stopping rule. |
| D5 | What machinery is required? | Reuse plan/session and PR-summary surfaces; route explicit capture through `work-intake`. | A ledger would create the queue this proposal removes. | RFC acceptance | Confirm the deliberately small implementation. |

This is an RFC rather than an ADR because the owner explicitly asked to
circulate this proposal, which §3 names as an RFC trigger. It also changes an
obligation shipped to adopters; §3 routes conventions maintenance to a PR only
when it preserves an obligation, while a changed obligation uses the RFC test.

## Problem & goals

A **completion boundary** is the condition that determines whether the work the
owner accepted is complete. The current loop instead makes a single pull
request do double duty as that boundary. A **review unit** is the independently
reviewable semantic commit, pull request, or stack layer; it may be smaller
than the accepted outcome.

This causes two failures. First, a required correction that cannot safely ride
in the current pull request is treated as future work even when it still
belongs to the original outcome. Second, a legitimate but out-of-intent
improvement is automatically made durable, creating follow-on work without an
owner choosing it.

The goals are to preserve truthful completion, retain reviewable units, and
make scope disposition explicit. Non-goals are expanding an accepted intent by
proximity, weakening blocking correctness or review retry safeguards, and
creating a second queue or tracking schema.

## Proposal

The **session scope** is the set of work performed in one uninterrupted agent
run. It may contain multiple review units but cannot silently change the
original accepted intent. **Intent fit** asks whether a discovery is required
by that intent and its constraints. **Capture-by-request** means a durable
follow-on is created only when the user explicitly asks to remember it.

For every implementation or review discovery, first determine intent fit, then
make the session decision:

| Intent fit | Session decision | Disposition |
| --- | --- | --- |
| Matches | Include now | Add it to the current plan or session. |
| Matches | Do not include | Stop incomplete unless the owner explicitly narrows or waives the intent. |
| Does not match | Include now | Obtain an explicit scope change; it then becomes accepted intent. |
| Does not match | Do not include | Exclude it with no durable follow-on by default. |
| Unclear | — | Ask the owner before acting. |

Only the owner may narrow or waive an accepted intent; absent that explicit
decision, a matching discovery that is not included leaves the work incomplete.

An included discovery may stay in the current review unit only when it is
authorized by the accepted contract and qualifies under RFC-0090 D6's
reproducible, provably inert, or small hand-made ride-along tiers
([`docs/rfc/0090-change-sizing-and-decomposition.md:40`](0090-change-sizing-and-decomposition.md)). A
design call, behavior change, or distinct semantic change gets a separate
commit or pull request, but remains in the current session when it fits the
accepted intent. RFC-0090 D1 already says one specification may deliver more
than one pull request and that a specification is an objective, not a mandated
review boundary ([`docs/rfc/0090-change-sizing-and-decomposition.md:35`](0090-change-sizing-and-decomposition.md)).
For this proposal, D6's relevant condition is that ride-alongs fail closed on
design calls and behavior changes
([`docs/rfc/0090-change-sizing-and-decomposition.md:40`](0090-change-sizing-and-decomposition.md)).

A review finding that shows the current change is incorrect or unsafe remains
blocking. One required by the original intent but needing its own review unit
becomes the next unit in the same session. An out-of-intent improvement is
excluded and forgotten unless capture is requested. Review retry caps and
stasis pause for human replanning; they neither make the intent complete nor
produce a backlog entry.

Waves are execution cohorts within one review cycle, not review units: wave
routing occurs after gates, and only the final wave fires `gates-clean` and
proceeds to REVIEW ([`packs/core/.apm/skills/work-loop/SKILL.md:402-412`](../../packs/core/.apm/skills/work-loop/SKILL.md)).
Both planned multi-unit delivery and a post-review in-intent discovery use the
existing human-gate return edge for a further independently reviewed unit:
`blocker-applied` moves `CODE-HUMAN-GATE` to `CODE-IMPLEMENTATION`
([`packs/core/.apm/skills/work-loop/scripts/loop-engine.py:552`](../../packs/core/.apm/skills/work-loop/scripts/loop-engine.py)),
after which the unit runs GATES, REVIEW, and the human gate again. The
work-loop currently documents that edge only as “Changes requested”
([`packs/core/.apm/skills/work-loop/SKILL.md:553`](../../packs/core/.apm/skills/work-loop/SKILL.md)); it must also instruct its use for either kind of further in-intent review unit. Intent-scoped completion therefore needs no new engine state, transition, or guard.

The implementation uses existing plan and session surfaces for included work,
and the PR or final summary's "What did you not change?" answer for excluded
work. An explicit request to remember work is routed through `work-intake`.

## Options considered

### D1 — Completion-boundary axis

- **Current pull request:** Too narrow; it conflates reviewer readability with
  outcome completion.
- **Physical area:** Too broad; every nearby defect becomes scope.
- **Original accepted intent (recommended):** Fixes the outcome and constraints
  while permitting one or more review units.
- **Do nothing:** Preserves follow-on proliferation.

### D2 — Discovery-disposition axis

- **Mandatory capture:** Preserves an audit trail but manufactures backlog work.
- **Capture-by-request (recommended):** Leaves a durable record only for an
  explicitly owned follow-on; the PR summary acknowledges the exclusion.
- **Do nothing:** Retains mandatory deferral and backlog creation.

### D3 — Included-discovery placement axis

- **Current review unit when authorized:** Appropriate only when the accepted
  contract authorizes it and it qualifies under RFC-0090 D6's existing
  ride-along tiers.
- **Separate review unit in the same session (recommended when behavior or
  design changes):** Preserves independent review without declaring the intent
  deferred.
- **Do nothing:** Treats every separate pull request as deferred work.

### D4 — Cap-or-stasis meaning axis

The alternatives answer one exclusive question: what does a review cap or
stasis mean for completion?

- **Completion:** Treat the cap as proof that the current intent is done;
  maximally bounded, but it makes a safety control falsely determine truth.
- **Pause for human replanning (recommended):** Bound autonomy while leaving
  completion unresolved until the accepted intent is satisfied, narrowed, or
  abandoned.
- **Automatic backlog creation:** Preserve a durable follow-on automatically;
  this retains the queue-manufacturing behavior the proposal removes.
- **Do nothing:** Preserve the current stop-and-defer behavior.

### D5 — Operational-surface axis

- **New completion ledger or schema:** Durable, but creates another queue.
- **Prose only:** Lightweight, but easy to miss during operation.
- **Existing plan, session, and summary surfaces (recommended):** Makes
  inclusion operational while keeping exclusion lightweight.
- **Do nothing:** Leaves the current behavior unchanged.

## Risks & what would make this wrong

The principal risk is that separating session scope from review units becomes a
pretext for scope creep. The mitigation is the intent-fit decision table:
out-of-intent inclusion requires an explicit scope change, and unclear fit
requires owner direction.

The riskiest assumption was that RFC-0090 D6 prevents same-session completion
of a behavior-changing discovery. It is falsified: D1 permits an objective to
produce multiple review units, while D6 restricts what can share the current
unit. [Commit `4e81d407`](https://github.com/eugenelim/agent-ready-repo/commit/4e81d407) is the worked case: its
projected-AGENTS scope-declaration fix changed linter behavior by adding the
frontmatter-skipping `_body_lines` path in `tools/lint-agents-md.py` (24
changed lines: 23 additions and one deletion) and a new
`tools/test_lint_agents_md_frontmatter_scope.py` regression test, so it
correctly took its own pull request (#1054) without a backlog entry.

This is reversible by restoring mandatory capture if adopters lose important
work through non-capture. Adopter compatibility is an intentional behavior
change: adopters no longer must create a `[backlog].open` item for every
excluded finding, so the follow-on convention and its workflow instruction must
ship together. No security review applies because this changes neither a
security boundary nor a trust model. The governance choice itself is not
empirical, but whether non-capture loses work that mattered is. Observe the
existing PR or final-summary exclusions alongside `work-intake` captures and
post-closure corrections: a confirmed case where an excluded, uncaptured
finding is later required to satisfy the original accepted intent is the
signal. That result restores mandatory capture; no new ledger, schema, or
instrumentation is required.

## Evidence & prior art

The current work-loop requires each deferred item to be recorded in
`workspace.toml [backlog].open` ([`packs/core/.apm/skills/work-loop/SKILL.md:590`](../../packs/core/.apm/skills/work-loop/SKILL.md)); its review retry cap and
stasis rule instead say to stop and surface ([`packs/core/.apm/skills/work-loop/SKILL.md:601-602`](../../packs/core/.apm/skills/work-loop/SKILL.md)). This proposal changes the former obligation, not the latter safety control.

RFC-0083 defines a shipped brief as explicitly closed with no in-scope work
remaining ([`docs/rfc/0083-work-intake-and-artifact-routing.md:512`](0083-work-intake-and-artifact-routing.md)). The technical-site brief likewise defines a bounded programme and sends feature expansion outside it unless approved
([`docs/product/briefs/tech-site-completion.md:61-66`](../product/briefs/tech-site-completion.md)). Those boundaries make intent fit decidable.

[The Kanban Guide](https://kanbanguides.org/the-kanban-guide/) requires a
workflow to define work items, start and finish points, WIP control, and
explicit flow policies; it permits multiple Definitions of Workflow at different
levels. That supports distinct completion and review boundaries. [Google
Engineering Practices](https://google.github.io/eng-practices/review/reviewer/pushback.html)
requires complexity introduced by the current change to be cleaned up before
submission, while surrounding problems that cannot be addressed may be filed
separately. This RFC tightens the latter practice by making that recording
optional rather than automatic.

## Open questions

- **Q1 — How should the hardcoded `Shipped` guard interact with an intent that
  spans multiple review units?** `reviewers-clean` on the code-review edge
  requires `spec.md` to be `Shipped`
  ([`packs/core/.apm/skills/work-loop/scripts/loop-engine.py:746`](../../packs/core/.apm/skills/work-loop/scripts/loop-engine.py),
  [`packs/core/.apm/skills/work-loop/scripts/loop-engine.py:802-805`](../../packs/core/.apm/skills/work-loop/scripts/loop-engine.py),
  [`packs/core/.apm/skills/work-loop/scripts/loop-engine.py:831`](../../packs/core/.apm/skills/work-loop/scripts/loop-engine.py)),
  while RFC-0090 D1 permits one specification to deliver multiple pull requests.
  Thus a later planned or post-review unit begins after an earlier unit has
  already marked the spec `Shipped`, even when the accepted intent remains
  incomplete. This pre-existing tension is surfaced, not created, here.
  **Recommended default:** retain the guard's current behavior and carry the
  doctrine instructionally; any change to the guard is a separate decision.
  **Owner:** eugenelim. **Decide by:** the follow-on work-loop implementation.

## Follow-on artifacts

Follow-on work will update the source-of-truth
`packs/core/seeds/docs/CONVENTIONS.md` seed and
`packs/core/.apm/skills/work-loop/SKILL.md` to apply intent-scoped completion
and capture-by-request, including instructional coverage of the existing
human-gate return edge for any further in-intent review unit. It will also
perform the required core-pack version bump, changelog update, and
generated-projection regeneration. Because the retired mandatory-capture rule
is restated in adopter-facing and maintainer-facing documentation, the work
also corrects the core how-to guide's DECIDE step, the core pack design
document, and the findings registers' descriptions of how entries arrive.
Removing work-loop's own `workspace.toml [backlog].open` write moves the pinned
finish-checklist contract hash in `tools/test_workspace_status.py` with the
reviewed prose; it strengthens, rather than relaxes, the existing invariant
that `workspace-status` (not work-loop) owns `workspace.toml`
queue/active/shipped updates (AC3g invariant). Acceptance creates no backlog type,
workspace schema field, lint, or new artifact.
