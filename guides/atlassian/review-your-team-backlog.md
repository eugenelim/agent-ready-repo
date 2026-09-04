---
title: "Review your team's Jira backlog from start to finish"
summary: "A complete walkthrough — see what the team can work on, improve weak stories, approve targeted Jira updates, and produce a stand-up summary without opening a browser."
pack: atlassian
kind: tutorial
slug: guides/atlassian/tutorials/review-your-team-backlog
journey: atlassian
order: 1
status: stable
---

**Mode: tracker-authoritative.** This tutorial assumes Jira holds the team's
real backlog. If `docs/product/` is canonical and Jira is only for reporting,
use [repo-first projection](README.md#which-mode-are-you-in) instead.

By the end of this tutorial, you will have followed a complete Atlas team workflow: seen the whole backlog, identified what is ready, improved three stories, applied two approved Jira updates, and produced a stand-up summary — all from a single conversation.

**Time:** 30 minutes. **Starts read-only** — Jira is not changed until step 10.

**Prerequisites:** `atlassian` pack installed; Jira credentials (API token, or SSO — see [Authenticate with SSO cookies](/agent-ready-repo/docs/guides/atlassian/how-to/authenticate-jira-confluence-with-sso-cookies/)); read access to APP and API projects; edit access for step 10.

---

## Stage 1 — See the work

### Step 1: Request the whole team backlog

Say exactly this, or something close:

:::tip[YOU SAY]
Show me the whole Atlas team backlog across APP and API.

Include the current sprint, open backlog, unassigned work, and blocked issues.

Group everything into:

- ready to pull
- needs story work
- blocked
- in progress

Recommend five items for the team to discuss next.

Do not change Jira.
:::

### Step 2: Respond to the scope clarification (if it appears)

The agent may ask one compact question when the team scope is ambiguous:

:::note[POSSIBLE CLARIFICATION]
I found two possible Atlas scopes:

1. The Atlas Jira board
2. Issues whose Team field is Atlas

Which should I use?
:::

Pick the one that matches your team's setup. If neither applies, say so — the agent will ask for a JQL filter or project list instead.

### Step 3: Read the scope and completeness header

Before any grouped sections, the agent shows you what it searched and whether the result is complete.

:::note[WHAT YOU GET — scope header]
**Scope searched:** APP and API projects · Team field = Atlas\
**Sprint:** APP Sprint 23 / API Sprint 12 (both active)\
**Backlog:** all open issues not in a sprint\
**Time horizon:** current sprint + open backlog\
**Total discovered:** 184 issues\
**Total inspected:** 184 issues\
**Coverage:** Complete — 184 items (APP: 127, API: 57 · Sprint 23 + open backlog · as of today)\
**Jira was not changed by this run.**
:::

**Checkpoint:** If the numbers look wrong — too few issues, wrong projects — stop here. Tell the agent what the correct scope should be before reading the grouped sections. Asking for corrections now is cheaper than reviewing the wrong backlog.

### Step 4: Read the grouped result

After the scope header, the agent groups the 184 issues:

| Group | Count | What it means |
|---|---:|---|
| Ready to pull | 17 | In scope, no blocker, enough definition to begin |
| Needs story work | 26 | Open, but missing information the team needs to start |
| Blocked | 8 | Known unresolved dependency or decision |
| In progress | 11 | Currently being worked on |
| Other open work | 122 | Open but not in the categories above |

### Step 5: Review the recommended candidates

The agent recommends five items for the team to discuss next:

1. API-104 — Rate-limit response should include Retry-After header
2. APP-206 — User cannot reset password when SSO is enabled
3. APP-312 — Session timeout on mobile
4. APP-298 — Search index rebuild throttle
5. API-117 — Deprecate v1 auth endpoint

**Checkpoint:** Do these candidates reflect your team's actual priorities? If not, tell the agent to filter by assignee, label, or component before moving on.

---

## Stage 2 — Improve weak stories

### Step 6: Request story improvements

:::tip[YOU SAY]
Take the items that need story work.

Apply our story-readiness bar and show me:

1. why each item is not actionable
2. a proposed rewrite
3. any question the product owner still needs to answer
4. whether the item would be ready after the proposed change

Draft only. Do not update Jira.
:::

### Step 7: Understand the draft output

For each of the 26 items, the agent produces a structured analysis. Here is the output for APP-206:

:::note[WHAT YOU GET — story analysis for APP-206]
**APP-206 · User cannot reset password when SSO is enabled**

**Why not actionable:** Fails the acceptance-criteria test — the description covers the happy path but does not specify what happens when the SSO provider is unreachable or returns an error. Engineering cannot begin without knowing whether to show a fallback or block the reset.

**Proposed description:**
When a user attempts to reset their password and their account is SSO-enabled:

- If the SSO provider is reachable: redirect to the SSO provider's reset flow.
- If the SSO provider is unreachable or returns an error: display "Your account uses single sign-on. Contact your IT administrator to reset your password." Do not allow direct password reset as a fallback.
- Log the provider error for the ops team.

**Proposed acceptance criteria:**
1. Given SSO-enabled user requests password reset, when SSO provider is reachable, then user is redirected to SSO provider reset flow
2. Given SSO-enabled user requests password reset, when SSO provider is unreachable, then user sees the contact-IT message and cannot set a password directly
3. Given SSO provider returns an error, then the error is logged with provider name and HTTP status

**Unresolved question:** Should the system allow a temporary bypass for locked-out SSO admins? Needs product owner decision.

**Expected readiness after draft:** APP-206 would pass the readiness bar once the product owner answers the bypass question.

**Jira was not changed by this run.**
:::

### Step 8: Work through the unresolved questions

Some issues have questions only the product owner can answer. APP-206 has one. You have two options:

- **Answer it now:** Tell the agent the answer. It will update the draft accordingly. Still read-only — nothing goes to Jira.
- **Leave it open:** The draft is preserved. APP-206 stays in "Needs story work" even after the other changes are applied. You can revisit it later.

:::note[WHAT YOU GET — API-104 analysis]
**API-104 · Rate-limit response should include Retry-After header**

**Why not actionable:** ACs mention the header but do not specify the format (seconds vs HTTP date), the value source (fixed vs dynamic), or what clients should do when the header is absent.

**Proposed acceptance criteria (additions):**
1. Given a client exceeds the rate limit, when the API returns 429, then the response includes Retry-After: \<integer seconds\>
2. Given the token-bucket drain time is known, when 429 is returned, then Retry-After value equals ceil(drain\_seconds)
3. Given drain time is unavailable, when 429 is returned, then Retry-After value is 30
4. Given any 429 response, then body contains {"error": "rate\_limited", "retry\_after\_seconds": \<integer\>}

**Unresolved question:** None.

**Expected readiness after draft:** API-104 would reach Ready to pull immediately after the draft is accepted.

**Jira was not changed by this run.**
:::

### Step 9: Select which drafts to approve

Review the drafts for APP-206, APP-219, and API-104. Decide which ones you want written to Jira.

**Checkpoint:** You are still read-only. Nothing has changed in Jira. This is the last moment to adjust or discard any draft before you confirm writes in the next stage.

---

## Stage 3 — Apply approved changes

### Step 10: Request the exact writes

This is the first step that will change Jira.

:::tip[YOU SAY]
Update APP-206, APP-219, and API-104 with the approved drafts.

Leave every other issue unchanged.

Do not change status, assignee, priority, sprint, or labels.
:::

### Step 11: Review the write preview

Before anything is written, the agent shows you the exact payload:

:::caution[WRITE PREVIEW — review before confirming]
**Issues:** APP-206, APP-219, API-104\
**Fields:** description, acceptance criteria\
**Protected (will not change):** status · assignee · sprint · priority · labels\
**Total writes:** 3

| Issue | Field | Current value | Proposed value |
|---|---|---|---|
| APP-206 | description | "User cannot reset password when SSO is enabled" | [full proposed description above] |
| APP-206 | acceptance criteria | (none) | [3 ACs above] |
| APP-219 | description | "Export to CSV drops custom field values" | [full proposed description] |
| APP-219 | acceptance criteria | (none) | [4 ACs] |
| API-104 | description | [current text] | [full proposed description] |
| API-104 | acceptance criteria | [partial existing ACs] | [4 ACs above] |

Type **confirm** to write these changes, or **cancel** to stop.
:::

**Checkpoint:** Read the proposed values for each field. If any proposed value is wrong, say "cancel" and tell the agent what to change. Confirming is permanent.

### Step 12: Confirm the writes

Type `confirm` to proceed.

### Step 13: Handle the partial failure

APP-219 fails because your token has reporter-only access. APP-206 and API-104 succeed.

:::caution[PARTIAL RESULT — action required for APP-219]
**Successful:** APP-206 · API-104\
**Failed:** APP-219 — 403 Forbidden (reporter-only access; write was blocked)\
**Protected fields:** not changed on any issue\
**Jira state:** APP-206 and API-104 now reflect the approved drafts. APP-219 is unchanged.

**Recovery:** The approved draft for APP-219 is preserved above. To apply it:
- Ask the agent: "Retry APP-219 with the same draft."
- Or ask the issue owner to apply the draft shown in step 7.
- Or get edit access to APP-219 and retry in this session.
:::

This is a normal outcome. Two of three writes succeeded. The third has a clear recovery path.

---

## Stage 4 — Share the result

### Step 14: Request the stand-up summary

:::tip[YOU SAY]
Give me a stand-up summary for the Atlas team.

Include progress, blockers, risks, and what is ready next.

Then prepare a concise weekly version suitable for the Atlas Confluence space.

Do not publish until I approve it.
:::

### Step 15: Read the stand-up summary

The agent produces a read-only summary from the backlog data you reviewed:

:::note[WHAT YOU GET — stand-up summary]
**Atlas team — stand-up summary (read-only)**

**Progress:** APP-206 and API-104 descriptions updated and accepted. APP-312, APP-298, and API-117 are ready to pull this sprint.

**Blockers:** 8 issues blocked — 3 waiting on external API access, 2 pending product decisions, 3 flagged as stale (>14 days without update).

**Risks:** APP-219 write was blocked by access permissions. Draft is ready; needs either access grant or issue-owner action.

**Ready next:** 17 items are ready to pull. Top five: API-104 · APP-206 · APP-312 · APP-298 · API-117.

*Jira was not changed by this run.*
:::

### Step 16: Review the Confluence draft

The agent also produces a Confluence-ready draft:

:::note[CONFLUENCE DRAFT — not yet published]
**Atlas team · Weekly update**

The team inspected 184 issues across APP and API this week. 17 are ready to pull; 26 needed story improvements, and 3 drafts were prepared; 2 applied. Two targeted Jira updates were applied (APP-206, API-104). One (APP-219) is pending access correction.

Blockers: 8 open. Risks flagged: APP-219 access issue.

Next: sprint planning should prioritize API-104 and APP-312.

*This is a draft. Confluence will not be updated until you approve.*
:::

**Checkpoint:** This is read-only and unpublished. Review the draft. If you want to adjust the tone, scope, or emphasis, tell the agent. Only say "publish" when the content is exactly right.

### Step 17: Stop before publishing

For this tutorial, stop here. Publishing to Confluence is a separate approved action.

When you are ready to publish in a real session, say: "Publish the Confluence draft to the Atlas space."

The agent will show you the exact page title, space, and content before writing anything.

---

## What you learned

- The whole-team backlog workflow starts read-only; scope and completeness are disclosed before any grouped data.
- "Ready to pull" is not Jira `To Do` — it means in scope, unblocked, and defined.
- Story improvements are draft-only until you explicitly approve writes.
- The exact fields, current values, and proposed values are shown before any write.
- Protected fields — status, assignee, sprint, priority, labels — are never changed.
- Partial write failures have a clear recovery path; the session preserves the approved draft.
- Confluence publishing requires a separate explicit approval.

---

## What to do next

| I want to… | Go to |
|---|---|
| Do specific tasks without the full journey | [Work with Jira from a conversation](/agent-ready-repo/docs/guides/atlassian/how-to/work-with-jira/) |
| See exact skill contracts and limits | [Atlassian skills reference](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/) |
| Understand how the workflows compose | [How the Atlassian pack works](/agent-ready-repo/docs/guides/atlassian/explanation/atlassian-pack/) |
| See the journey as a visual storyboard | [Atlassian journey](/journeys/atlassian/) |
| Return to the pack overview | [Atlassian pack](/packs/atlassian/) |
