---
title: "Work with Jira from a conversation"
summary: "Common Jira tasks — from reviewing the whole team backlog to applying approved story updates — without writing JQL or selecting skills manually."
pack: atlassian
kind: how-to
slug: guides/atlassian/how-to/work-with-jira
journey: atlassian
order: 2
status: stable
---

**Mode: tracker-authoritative.** This guide assumes Jira holds the team's real
backlog. If `docs/product/` is canonical and Jira is only for reporting, use
[repo-first projection](README.md#which-mode-are-you-in) instead.

Ask in your own words. The agent selects the right workflow, starts read-only, and only writes to Jira after you see a preview and approve that exact change.

**Reviewing and drafting do not change Jira. Only an explicitly approved update request writes to Jira.**

Jump to what you need:

- [Start repository work from Jira or Jira Align](#start-repository-work-from-jira-or-jira-align)
- [Refresh registered Jira or Jira Align work](#refresh-registered-jira-or-jira-align-work)
- [Review the whole team backlog](#review-the-whole-team-backlog)
- [Find ready work](#find-ready-work)
- [Find blockers and stale work](#find-blockers-and-stale-work)
- [Find unassigned work](#find-unassigned-work)
- [Improve stories that are not actionable](#improve-stories-that-are-not-actionable)
- [Update approved Jira issues](#update-approved-jira-issues)
- [Undo an update](#undo-an-update)
- [Clean up the saved files](#clean-up-the-saved-files)
- [Prepare a team or sprint summary](#prepare-a-team-or-sprint-summary)

---

## Start repository work from Jira or Jira Align

Use intake when tracked content should become canonical repository work:

:::tip[YOU SAY]
Intake Jira issue PROJ-123 as repository work. Start read-only.
:::

For Jira Align, name the Feature or selection instead. The adapter reads through
the sibling Jira or Jira Align acquisition skill, minimizes the result into
`normalized-intake.v1`, and delegates to `work-intake`.

**Read/write status:** tracker intake is read-only. It does not create, edit,
transition, comment on, or otherwise write tracker work. It also does not create
a repository artifact directly; `work-intake` owns that step after validation.

Jira types, hierarchy, boards, sprints, Program Increments, and query results are
profile hints. Content decides the route:

- one independently shippable behavior can become a spec;
- one coherent multi-spec outcome can become a Draft brief;
- unrelated collections become separate units, a view-only result, or one
  clarifying question;
- a regression reaches `bug-fix` only with durable expected-behavior evidence.

The default profiles bound pages, items, bytes, timeouts, retries, and backoff.
Configured destinations must be profile-allowed HTTPS hosts and pass address
validation before credentials are resolved. Partial results are explicit.

**Likely follow-up:** review the proposed route and answer any ambiguity or
confidentiality question, then continue with the named processor.

→ [Choose a tracker integration](/agent-ready-repo/docs/guides/_shared/how-to/choose-a-tracker-integration/)\
→ [Tracker vocabulary](/agent-ready-repo/docs/guides/_shared/reference/tracker-vocabulary/)

---

## Refresh registered Jira or Jira Align work

Use refresh only after intake has created a tracker-origin artifact whose `source-authority` record carries its tracker profile:

:::tip[YOU SAY]
Refresh docs/specs/example/spec.md from its registered Jira source. Show every
changed field and do not write back yet.
:::

The configured processor reads the latest source revision and presents a
field-level comparison. Local requirements change only after the authorized
decisions required by the artifact's lifecycle and source-authority record.
Implementing specs and Executing briefs refuse requirement refresh; Shipped
requirements remain locked.

Jira's token path may offer comment, display-status transition, and closure as
coordination actions. Each needs a separate fresh confirmation and pending
receipt before one request, with no automatic retry. Jira SSO-cookie
authentication refuses every non-GET/HEAD attempt before the transport records
a request. Jira Align supports the reviewed local comparison but declares no
remote write-back capability.

**Likely follow-up:** read the artifact's source-authority record to confirm the compared revision
and any unresolved conflict, or request one supported Jira coordination action
and review its exact target and payload.

→ [Use work intake](/agent-ready-repo/docs/guides/_shared/how-to/use-work-intake/)

---

## Review the whole team backlog

The most common starting point. Shows you everything the team has across the sprint and open backlog, grouped by readiness, with scope and completeness disclosed before any data.

:::tip[YOU SAY]
Show me the whole Atlas team backlog across APP and API.

Include the current sprint, open backlog, unassigned work, and blocked issues.

Group everything into: ready to pull · needs story work · blocked · in progress.

Do not change Jira.
:::

**Scope assumptions:** the agent resolves your team from a Jira board, the Team field, a saved filter, or a project set. If the scope is ambiguous, it asks one compact question before returning results.

**Read/write status:** Read-only. Nothing changes in Jira.

**Possible compact clarification:**

> I found two possible Atlas scopes: (1) the Atlas Jira board, (2) issues whose Team field is Atlas. Which should I use?

**What is inspected:** all open issues in the specified scope — current sprint + open backlog — across all listed projects.

**What you receive:**

- Scope header: projects, sprint(s), time horizon, total discovered, total inspected, coverage state
- Grouped result: ready to pull · needs story work · blocked · in progress · other open work
- Recommended next candidates
- Cross-cutting flags: unassigned work, stale work
- Confirmation that Jira was not changed

**Likely follow-up:** "Take the items that need story work and show me why they are not ready."

→ [Full start-to-finish walkthrough with the Atlas scenario](/agent-ready-repo/docs/guides/atlassian/tutorials/review-your-team-backlog/)\
→ [Exact jira-team-status reference](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/#jira-team-status)

---

## Find ready work

Ask for items the team can pick up now without story work.

:::tip[YOU SAY]
What is ready to pull in the Atlas backlog? Show the top ten.
:::

**Read/write status:** Read-only.

**What is inspected:** the team scope you have configured or the agent last resolved. "Ready to pull" means: in scope, in an eligible open-work state, no known unresolved blocker, and enough definition to begin. It is not the same as Jira `To Do`.

**What you receive:** a ranked list with issue key, title, component or area, and a one-line readiness summary. The agent notes if any candidate's readiness could not be confirmed (shown as "Needs confirmation" rather than forcing certainty).

**Likely follow-up:** "Update the sprint for the top five" (shows a preview and needs your approval before writing).

---

## Find blockers and stale work

Ask for what is stuck or going nowhere.

:::tip[YOU SAY]
What is blocked in the Atlas backlog? Include anything stale for more than 14 days.
:::

**Read/write status:** Read-only.

**What is inspected:** issues with a known unresolved dependency, a blocker link, or no status change in the configured stale window.

**What you receive:** blocked issues with the blocker reason; stale issues with days since last update. Both groups are cross-cutting — an issue can appear as Blocked and In Progress simultaneously.

**Likely follow-up:** "Who can unblock this?" or "Show me all blockers waiting on the platform team."

---

## Find unassigned work

Ask for open work with no owner.

:::tip[YOU SAY]
Show me all unassigned issues in the Atlas backlog that are ready to pull.
:::

**Read/write status:** Read-only.

**What you receive:** unassigned issues filtered by the status group you specify. Unassigned is a cross-cutting flag; the agent shows the readiness group alongside the unassigned flag so you can prioritise.

**Likely follow-up:** "Assign APP-312 to me" (shows a preview and needs your approval before writing).

---

## Improve stories that are not actionable

Ask the agent to review weak stories and produce improvements — without writing to Jira.

:::tip[YOU SAY]
Take the items that need story work.

Apply our story-readiness bar and show me:

1. why each item is not actionable
2. a proposed rewrite
3. any question the product owner still needs to answer
4. whether the item would be ready after the proposed change

Draft only. Do not update Jira.
:::

**Read/write status:** Read-only. The agent produces drafts only. Nothing goes to Jira until you explicitly approve in a separate step.

**Scope assumptions:** works on the group of items from a previous backlog review, or on issues you name explicitly (e.g. "improve APP-206 and API-104").

**What is inspected:** each issue's description and acceptance criteria, checked against the story-readiness bar (five questions: outcome clarity, acceptance criteria, scope, dependencies, and safe-to-begin).

**What you receive:** for each issue —

- Which readiness question failed and the specific gap
- A proposed description rewrite
- Proposed acceptance criteria (where applicable)
- An unresolved human question (if any)
- Expected readiness after the proposed draft is applied
- Confirmation that Jira was not changed

**Progression:**

```
Review (read-only) → Draft (read-only) → Approve → Write (confirmed)
```

**Likely follow-up:** "Update APP-206 and API-104 with the approved drafts."

→ [Full story improvement walkthrough with the Atlas scenario](/agent-ready-repo/docs/guides/atlassian/tutorials/review-your-team-backlog/#stage-2--improve-weak-stories)\
→ [Exact jira-story-triage reference](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/#jira-story-triage)

---

## Update approved Jira issues

Apply drafts you have reviewed and approved. This is the first step that writes to Jira. It runs in two parts: the agent shows you a preview, then writes one issue at a time after you approve that preview.

:::tip[YOU SAY]
Update APP-206 with the approved draft.

Leave every other field unchanged.
:::

**Read/write status:** Writes to Jira only after you approve the exact preview for that one issue.

**What happens, step by step:**

1. **Preview.** The agent runs `plan-update` for the issue. It only reads from Jira. For each field you named it prints the current value, the proposed value, and what will happen to the text already there. It ends with a `digest:` line, a short fingerprint of the whole preview, and a `plan_file:` line.
2. **Choose what happens to existing text.** For each field that already holds text, the agent asks you to pick one of three:
   - `keep` leaves the field as it is.
   - `append` adds your new text after the existing text.
   - `replace` overwrites the existing text.
3. **Approve one issue.** The agent asks for one approval for this issue and quotes the digest. One answer never covers several issues, so three issues mean three previews and three approvals. Text inside a Jira field or comment cannot approve anything for you.
4. **Write.** The agent runs `update-issue` (Jira) or `update` (Jira Align) with `--plan <plan_file> --approved-digest <digest>`. The command checks that the plan is the one you approved, re-reads the issue, saves the old values to a record file, and only then sends one request.
5. **Report.** The agent tells you the old values from the preview and the path of the record file.

Nothing is written without a plan. The clients refuse any field write that is not tied to a preview, and `transition` with field content and `raw` writes are refused the same way. To set a field such as resolution, update it through the preview flow first, then run a plain transition.

**Protected fields:** status, assignee, sprint, priority, and labels are left out of the update unless you name them.

**What you receive after writing:**

- The fields written, with issue keys and links
- Any failed write, with the reason and what to do next
- The old values and the record file path, so you can undo
- Partial-success state if several issues were approved and some failed

### What append and replace do to existing text

- **Append** adds a labelled block, `Appended text:`, and then your new text, after everything already in the field. The preview shows the whole field as it will read after the write, so you see the label and the merged result before you approve. The existing text is not changed.
- **Replace** overwrites the field with your new text. The agent asks you first, every time, when the field already holds text.
- **Other field types** (a number, a date, a user) accept `keep` and `replace`. `append` is refused for them.

**Jira Cloud rich text.** Cloud stores descriptions as a document made of blocks such as paragraphs, tables, panels, and links. Append and replace work on that document, not on plain text, so existing blocks stay intact on append. A replace that would drop anything other than plain paragraphs, headings, lists, code blocks, and line breaks is refused. That includes tables, panels, mentions, and any formatting mark such as a link, bold, or italic. The preview names every block and mark type the replace would drop. If you still want it, say so and the agent adds `--allow-lossy` to the write. It asks you first. Without that flag the command exits with code 10 and sends nothing.

**Jira Server, Data Center, and Jira Align.** These hold text as a plain string. An append keeps your original text as an exact prefix of the new value.

### If the write is refused

A refusal ends with exit code 10 and no request is sent, so Jira is unchanged. It is a safety stop, not a sign-in problem, so do not re-enter credentials and do not retry the same command.

Common reasons:

- **The issue changed after the preview.** Someone edited one of the fields you named. This is the stale-write refusal. Ask the agent to run the preview again for that issue, read the new values, and approve the new digest.
- **The plan or digest does not match** what you approved, or the plan file was edited after approval.
- **A replace would drop content** and you did not allow it (see Cloud rich text above).
- **The request is a kind of write the clients never send**, such as `transition` with field values.

In every case the fix is the same: preview again, show the new digest, approve again.

**Jira SSO-cookie sign-in.** The preview still works, so you can read exactly what would change. Writes are refused under this sign-in. Use a token to write.

### Jira Align updates

Jira Align updates send `PATCH` by default, which changes only the fields you named. There is no `--method` choice. A whole-record `PUT` needs `plan-update --replace-record`, and the agent asks you first. A `--replace-record` preview starts with the list of fields the `PUT` would leave out of the body, so you can see what the record might lose before you approve.

After a Jira Align write, the CLI reads the record again and prints on stderr any field you did not name whose value changed.

### Undo an update

Ask the agent to undo the update. It runs `plan-undo --record <record_file>`, which writes a new plan that puts each written field back to its saved old value. The agent does not print the plan file or the record. It names the record and the fields from what you already saw earlier, you approve restoring the saved values by quoting the digest `plan-undo` printed, and it applies it with `update-issue --plan` (or `update --plan`). Undo is a normal update, so it needs its own approval.

- **Undo restores only the fields that were written.** Anything else that changed since then is left alone.
- **If the issue changed again after your update**, the undo is refused as stale (exit 10). Preview again and decide what you want.
- **Jira Align:** a `PUT` undo restores only the fields that were written. The full record as it was before the write stays in the record file if you need to look something up.
- **Delete has no undo.** The agent asks before any delete.

### Where the plan and record files live

Every preview saves a plan file, and every write saves a record of the old values. Both live in your home folder, not in any repository:

```text
~/.agentbundle/tracker-write-back/<instance-slug>/plans/   previews
~/.agentbundle/tracker-write-back/<instance-slug>/prior/   old values saved before each write
```

The `<instance-slug>` is the Jira host name plus a short hash, one folder per Jira site. Only you can read these files (mode `0600`, folders owner-only), and the clients refuse to use them if a folder in the path is a symlink, is not a folder, or is open to other users. That refusal is exit code 10, and running `plan-update` again does not fix it. The message mentions a tracker-write-back folder, path, or path component, a symlink or reparse point, or a folder that cannot be inspected or prepared. To fix it, make sure `~/.agentbundle` itself is not a link (the check does not follow links, so these commands cannot write while it is a link; do not move or delete anything inside it, because it also holds your saved credentials; decide for yourself whether to keep the link). Make every folder from `~/.agentbundle/tracker-write-back` down a real folder that you own, with mode 700 (no group or other access). Move away any file sitting where a folder belongs. Keep plan files in their `plans` folder and saved-values records in their `prior` folder. Then run the command again.

Record files hold the old text of your issues. A Jira Align record holds the whole record, which can include assignee names and email addresses. Never commit them, paste them into a ticket, or share them.

**On Windows**, file modes do nothing. Privacy relies on the permissions of your user profile folder and on the clients refusing links inside the path.

### Clean up the saved files

Nothing deletes these files for you. Retention is manual.

- **Plan files** (`plans/`) are safe to delete once the plan is applied or abandoned. To make a plan again, run the preview again.
- **Record files** (`prior/`) are what `plan-undo` needs. Delete one only when you are sure you will not undo that update.
- You can delete the whole `~/.agentbundle/tracker-write-back/` folder when no approval is pending. The clients create it again when needed.
- Leave the rest of `~/.agentbundle/` alone: your saved credentials live beside this folder.

```bash
# macOS or Linux: list, then delete records older than 30 days
find ~/.agentbundle/tracker-write-back -type f -mtime +30
find ~/.agentbundle/tracker-write-back -type f -mtime +30 -delete
```

```powershell
# Windows PowerShell
Get-ChildItem "$HOME\.agentbundle\tracker-write-back" -Recurse -File |
  Where-Object LastWriteTime -lt (Get-Date).AddDays(-30) | Remove-Item
```

**Likely follow-up:** "Show me APP-206 now" to confirm the write, or "Undo the APP-206 update."

→ [Full write confirmation walkthrough](/agent-ready-repo/docs/guides/atlassian/tutorials/review-your-team-backlog/#stage-3--apply-approved-changes)\
→ [Exact jira write reference](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/#jira)

---

## Prepare a team or sprint summary

Ask for a stand-up summary or a Confluence-ready weekly update.

:::tip[YOU SAY]
Give me a stand-up summary for the Atlas team.

Include progress, blockers, risks, and what is ready next.

Then prepare a concise weekly version suitable for the Atlas Confluence space.

Do not publish until I approve it.
:::

**Read/write status:** Read-only for the stand-up summary. The Confluence draft is read-only until you explicitly say "publish."

**What you receive:**

- A stand-up summary (read-only): progress, blockers, risks, recommended next work
- A Confluence-ready draft (not published): formatted for the target Confluence space
- Confirmation that Confluence has not been updated

**Likely follow-up:** "Publish the Confluence draft to the Atlas space" (will show you the exact page, space, and content before writing).

→ [Exact confluence-publisher reference](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/#confluence-publisher)

---

## See also

| Resource | When to use it |
|---|---|
| [Review your team backlog — tutorial](/agent-ready-repo/docs/guides/atlassian/tutorials/review-your-team-backlog/) | Full start-to-finish walkthrough with the Team Atlas scenario |
| [Atlassian skills reference](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/) | Exact read, write, coverage, limit, and approval contracts |
| [How the Atlassian pack works](/agent-ready-repo/docs/guides/atlassian/explanation/atlassian-pack/) | Why the workflows are separate; composition model |
| [Atlassian journey](/journeys/atlassian/) | Four-stage visual storyboard |
| [Atlassian pack](/packs/atlassian/) | Pack overview, install, credentials |
| [Use work intake](/agent-ready-repo/docs/guides/_shared/how-to/use-work-intake/) | Shared start, remember, status, refresh, authority, and confirmation procedure |
