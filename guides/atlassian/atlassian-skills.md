---
title: "Atlassian skills reference"
summary: "Exact read, write, coverage, limit, and approval contracts for every skill in the Atlassian pack."
pack: atlassian
kind: reference
slug: guides/atlassian/reference/atlassian-skills
journey: atlassian
order: 3
status: stable
---

**Mode: tracker-authoritative.** This reference assumes Jira holds the team's
real backlog. If `docs/product/` is canonical and Jira is only for reporting,
use [repo-first projection](README.md#which-mode-are-you-in) instead.

Look up what a skill reads, what it writes, what requires confirmation, and what its limits are. Use the intent index to find the right skill by what you want to accomplish.

:::tip[TRY ASKING]
Show me the whole Atlas team backlog across APP and API. Do not change Jira.
:::

## Intent index

| I want to… | Use |
|---|---|
| See everything a team can work on — sprint, backlog, blocked, unassigned | [jira-team-status](#jira-team-status) |
| Find work ready to pull | [jira-team-status](#jira-team-status) |
| Find blockers, stale work, or unassigned work | [jira-team-status](#jira-team-status) |
| Find stories that are not actionable | [jira-story-triage](#jira-story-triage) |
| Draft improved stories and acceptance criteria | [jira-story-triage](#jira-story-triage) |
| Search, create, or update individual Jira issues | [jira](#jira) |
| Apply approved story improvements to Jira | [jira](#jira) |
| Prepare or publish a Confluence result | [confluence-publisher](#confluence-publisher) |
| Crawl a Confluence space to Markdown | [confluence-crawler](#confluence-crawler) |
| Compute cycle time, throughput, WIP, DORA metrics | [flow-metrics](#flow-metrics) |
| Compare flow metrics before and after a change | [ai-adoption-report](#ai-adoption-report) |
| Start repository work from Jira | [jira-brief-intake](#jira-brief-intake) |
| Start repository work from Jira Align | [jira-align-brief-intake](#jira-align-brief-intake) |
| Refresh registered Jira work | [jira-refresh](#jira-refresh) |
| Refresh registered Jira Align work | [jira-align-refresh](#jira-align-refresh) |
| Fix a defect end-to-end from a Jira ticket | [jira-defect-flow](#jira-defect-flow) |
| Read or write Jira Align portfolio data | [jira-align](#jira-align) |

---

## jira-team-status

**Use it for:** a read-only snapshot of what the team can work on — sprint status, stand-up orientation, blocked work, unassigned work, stale issues.

**Natural requests:**

- "Show me the whole Atlas team backlog across APP and API."
- "What can the team pick up next sprint?"
- "What is blocked in the Atlas backlog?"
- "Give me a stand-up summary for the platform team."

**Required scope:** at minimum, a team name, project key, board identifier, saved filter, or explicit JQL. The agent resolves scope in this preference order: named board → project set → Team field → saved filter → explicit JQL.

**Reads:** Jira issues via REST (search with JQL, auto-paginated); issue fields including status, assignee, priority, sprint, labels, description, acceptance criteria, blocker links, and last-updated timestamp. Does not read attachments or comments.

**Writes:** Nothing. Read-only always. No Jira data is changed.

**Returns:**

- Scope header (projects, sprint(s), time horizon, total discovered, total inspected, coverage state, Jira-unchanged confirmation)
- Grouped result: Ready to pull · Needs story work · Blocked · In progress · Other open work
- Recommended next candidates (up to five)
- Cross-cutting flags: unassigned work, stale work (age-based)

**Coverage:** paginated automatically; coverage state is always disclosed before grouped results. States: Complete (all items returned) · Filtered (date or label filter applied) · Cap reached (result set truncated) · Permission-limited (some items inaccessible) · Partial (request failed mid-fetch).

**Limits:** cloud instances do not return a total until the full page set is fetched — if the result is large, coverage may show "Fetching…" before showing the final count. Server/Data Center instances return a total immediately.

**Approval behavior:** none — no writes occur. No confirmation required.

**Team readiness vs agent-execution readiness:** "Ready to pull" is the default — it means in scope, unblocked, and defined enough for the team to begin. The optional coding-agent execution readiness lens (five-question bar) is applied **only when explicitly requested** ("agent-ready work", "one-PR tasks", "coding-agent candidates"). Do not equate the two.

**Common follow-up:** "Take the items that need story work and improve them." → use [jira-story-triage](#jira-story-triage).

**Related skills:** [jira-story-triage](#jira-story-triage) (improve weak stories), [jira](#jira) (apply approved updates), [confluence-publisher](#confluence-publisher) (publish the summary).

---

## jira-story-triage

**Use it for:** reviewing work items for story readiness, explaining why items are not actionable, drafting improvements, and writing approved changes back to Jira.

**Natural requests:**

- "Which stories are not ready for engineering in the Atlas backlog?"
- "Improve these weak stories but do not update Jira yet."
- "Apply the story-readiness bar to APP-206, APP-219, and API-104."
- "Draft better acceptance criteria for the items that need story work."

**Required scope:** a list of issues (by key or group), or a team scope from a previous backlog review.

**Reads:** issue description, acceptance criteria, status, priority, assignee, sprint, labels. Applies a five-question readiness bar: (1) clear outcome, (2) acceptance criteria present and specific, (3) scope bounded, (4) dependencies identified, (5) safe to begin without additional information.

**Writes:** Nothing by default. Draft-only until you approve. When you approve, writes description and/or acceptance criteria via [jira](#jira) after showing the exact payload and receiving explicit confirmation.

**Returns:** for each issue —

- Which readiness question failed and the specific gap
- Proposed description rewrite (where applicable)
- Proposed acceptance criteria (where applicable)
- Unresolved human questions (questions only the product owner can answer)
- Expected readiness after the draft is applied
- Confirmation that Jira was not changed

**Coverage:** processes all items in the supplied scope. No cap by default; very large sets (>50 items) may prompt for a prioritised subset.

**Limits:** does not create new issues, transition statuses, change assignees, or touch sprint membership. For any of those, use [jira](#jira) directly.

**Approval behavior:** shows the exact description and acceptance criteria payload — current values and proposed values — for each issue before writing. Writes issue-by-issue only after you confirm. Protected fields (status, assignee, sprint, priority, labels) are never changed.

**Partial write failure:** if a write fails for one issue (e.g. permission error), the others proceed. The failed draft is preserved with a clear recovery action.

**Common follow-up:** "Update APP-206 and API-104 with the approved drafts." → use [jira](#jira).

**Related skills:** [jira-team-status](#jira-team-status) (find the weak items first), [jira](#jira) (apply the approved writes).

---

## jira

**Use it for:** reading, searching, creating, updating, transitioning, or deleting individual Jira issues. Also the canonical write target when jira-team-status or jira-story-triage route approved changes here.

**Natural requests:**

- "Search APP for all open P1 bugs assigned to me."
- "Create a new story in API with the title and description I give you."
- "Update APP-206 description and acceptance criteria with the approved draft."
- "Transition API-104 to In Review."

**Required scope:** project key, issue key, JQL, or a description of what you want to find or change.

**Reads:** JQL search (auto-paginated), individual issue fetch (all standard and configured custom fields), project list, user lookup.

**Writes:** create issue, update fields (description, ACs, custom fields), apply workflow transition, add comment, add attachment, delete issue. Every write shows the exact payload before executing and requires explicit confirmation.

**Returns:** search results as a structured list or JSON; individual issue detail; write result (success/failure with affected keys).

**Coverage:** search results are paginated automatically. Large result sets are returned in pages; the agent discloses when a result is partial.

**Limits:** cannot bulk-transition issues in a single call; each transition is a separate confirmed write. Cannot create subtasks of subtasks. Custom field writes require the field ID or a configured alias.

**Approval behavior:** shows exact issue key, field name, current value, and proposed value before any write. Confirmation required per-write or per-batch (agent will clarify). Protected fields in story-triage flows (status, assignee, sprint, priority, labels) are excluded from the payload unless you explicitly name them.

**Common follow-up:** "Show me APP-206 now" (to confirm the write was applied).

---

## confluence-publisher

**Use it for:** pushing a Markdown report, summary, or draft to a Confluence page — creating a new page or updating an existing one.

**Natural requests:**

- "Publish the Atlas team summary to the Atlas Confluence space."
- "Update the Sprint 23 retrospective page with the summary above."
- "Create a new page in the ENG space with this architecture note."

**Required scope:** target Confluence space key or URL, and page title or existing page ID.

**Reads:** resolves the target page by ID, URL, space + title lookup, or frontmatter `confluence_id`.

**Writes:** creates or updates a Confluence page. Always shows the exact page title, space, and full content before writing. Requires explicit confirmation. Handles optimistic-locking retries automatically (one retry on 409).

**Returns:** the published page URL and page ID; or the exact failure reason if the write is blocked.

**Coverage:** single-page write per call. For multi-page updates, each page is a separate confirmed write.

**Limits:** does not update page restrictions, parent page hierarchy, or space permissions. Cannot delete pages. Does not write to Confluence Data Center instances with SSO if credentials are not pre-configured.

**Approval behavior:** shows page title, space, full markdown content, and target page state (new vs update) before writing. Confirmation required. **Confluence publishing is never automatic.** A stand-up summary is always read-only until you explicitly request a publish.

**Common follow-up:** "Show me the published page URL."

---

## confluence-crawler

**Use it for:** mirroring a Confluence space (or subtree) to Markdown files for ingestion, analysis, or offline reference.

**Natural requests:**

- "Crawl the ENG Confluence space and summarise the onboarding pages."
- "Mirror the Atlas design decisions space to Markdown."

**Reads:** Confluence pages via REST — page hierarchy, body content, attached metadata. Converts to clean Markdown with frontmatter.

**Writes:** Nothing to Confluence. Writes Markdown files to a local output directory.

**Limits:** does not crawl attachment binaries. Handles macro-heavy pages with best-effort conversion.

---

## flow-metrics

**Use it for:** computing DORA / Flow Framework metrics from Jira data.

**Natural requests:**

- "What is our cycle time this quarter for the PLATFORM project?"
- "Give me throughput and WIP for the Atlas team."
- "Compare flow efficiency before and after the AI-pairing rollout."

**Reads:** Jira changelogs and issue metadata. Read-only; never transitions or writes Jira data.

**Writes:** nothing to Jira. Outputs metrics as JSON (optionally also as Markdown).

**Returns:** cycle time (p50/p75/p90), lead time, throughput, WIP, flow load, rework rate, flow efficiency, flow distribution, defect ratio.

---

## ai-adoption-report

**Use it for:** comparing two `flow-metrics` outputs and producing a Markdown adoption report.

**Natural requests:**

- "How do our flow metrics now compare to pre-AI?"
- "Within Q4, did AI-tagged tickets behave differently from untagged?"

**Reads:** two `flow-metrics` JSON files. Makes no upstream API calls.

**Writes:** a Markdown comparison report and optional JSON sidecar. Never writes to Jira or Confluence.

**Limits:** requires two `flow-metrics` runs as input; does not fetch Jira data itself.

---

## jira-brief-intake

**Use it for:** reading Jira work into the shared content-based repository route.

**Natural requests:**

- "Intake Jira issue PROJ-123 as repository work. Start read-only."
- "Route this Jira board from its content, not its hierarchy."

**Reads:** bounded source data via `jira`, after profile destination validation.

**Writes:** none to Jira and none directly to the repository. Emits
`normalized-intake.v1`; `work-intake` owns classification and materialization.

**Limits:** 5 pages, 250 items, 2 MiB, 30 seconds, and two bounded retries by
default. Exhaustion is explicit.

---

## jira-align-brief-intake

**Use it for:** reading Jira Align work into the shared content-based repository
route. The versioned organization profile supplies hints; a Feature is not
automatically a brief.

**Writes:** none to Jira Align and none directly to the repository.

---

## jira-refresh

**Use it for:** comparing an existing tracker-origin artifact with its latest
Jira revision through the shared lifecycle and authority rules.

**Reads:** the exact `jira-default` profile, registered artifact provenance,
and bounded Jira source data. Token destinations are HTTPS-only, host-scoped,
and pinned before credentials or transport.

**Writes:** approved local fields through `work-intake`. Optional Jira
coordination write-back is limited to comment, display-status transition, and
closure. Each remote mutation needs its own fresh exact confirmation and
pending receipt and is never retried automatically.

**Authentication:** token-authenticated writes use the guarded Jira client.
SSO-cookie non-GET/HEAD actions refuse before any request.

---

## jira-align-refresh

**Use it for:** comparing an existing tracker-origin artifact with its latest
Jira Align revision through the shared lifecycle and authority rules.

**Writes:** approved local fields through `work-intake`. The current profile
declares no Jira Align remote write-back actions; unsupported requests produce
no payload or transport call.

---

## jira-defect-flow

**Use it for:** handling a Jira defect end-to-end — pull the ticket, fix the code, open a PR, comment and transition the ticket.

**Use only for defects.** For stories and features, use `new-spec` or `jira-brief-intake`.

---

## jira-align

**Use it for:** reading or writing Jira Align portfolio data (epics, features, stories, capabilities, themes, programs, teams).

---

## See also

| Resource | When to use it |
|---|---|
| [Work with Jira — how-to](/agent-ready-repo/docs/guides/atlassian/how-to/work-with-jira/) | Task-by-task guidance for common Jira workflows |
| [Review your team backlog — tutorial](/agent-ready-repo/docs/guides/atlassian/tutorials/review-your-team-backlog/) | Full walkthrough with the Team Atlas scenario |
| [How the Atlassian pack works](/agent-ready-repo/docs/guides/atlassian/explanation/atlassian-pack/) | Composition model and why the workflows are separate |
| [Atlassian journey](/journeys/atlassian/) | Four-stage visual storyboard |
| [Atlassian pack](/packs/atlassian/) | Pack overview, install, credentials |
| [Use work intake](/agent-ready-repo/docs/guides/_shared/how-to/use-work-intake/) | Shared intake, refresh lifecycle, and confirmation contract |
