# ATLASSIAN

**Run Jira and Confluence from a conversation**

See what the team can work on, start repository work from Jira or Jira Align,
improve weak stories, apply only approved Jira changes, and prepare team updates
without starting from JQL or internal skill names.

**Starts read-only.** Jira data does not change until you confirm the exact fields.

---

Try this:

```
Show me the whole Atlas team backlog across APP and API. Include the sprint,
open backlog, blocked work, and unassigned issues. Group into ready to pull,
needs story work, blocked, and in progress. Do not change Jira.
```

You get: 184 issues inspected · 17 ready to pull · 26 need story work · 8 blocked · 11 in progress — with scope, completeness, and recommended next candidates.

---

## What you can do

### Start repository work from tracked content

```text
Intake Jira issue PROJ-123 as repository work. Start read-only.
```

Get: a bounded normalized record routed by content to an intent, brief, spec,
defect, separate units, or view-only result. Jira object types and hierarchy are
profile hints, not artifact identities. Intake never writes to Jira or Jira
Align; `work-intake` owns any later repository materialization.

For an existing tracker-origin artifact, ask for a refresh. Jira and Jira Align
both support reviewed local comparison. Token-authenticated Jira can also
comment, transition display status, or close after one fresh confirmation per
mutation. Jira SSO cookies remain read-only for every non-GET/HEAD request, and
the Jira Align refresh profile declares no remote write-back actions.

### 1. See what the team can work on

```
Show me the whole Atlas team backlog.
```

Get: a grouped, annotated view of the sprint and open backlog — ready to pull, needs story work, blocked, in progress — with scope and completeness disclosed upfront. **Read-only.** Nothing changes in Jira.

### 2. Make the backlog actionable

```
Improve the stories that need work. Draft only, do not update Jira.
```

Get: per-story analysis — which readiness question failed, a proposed description and acceptance criteria rewrite, any unresolved human question, and expected readiness after the draft. **Draft-only.** Nothing changes in Jira until you approve.

### 3. Update Jira safely

```
Update APP-206 and API-104 with the approved drafts.
Do not change status, assignee, priority, sprint, or labels.
```

Get: a preview of the exact fields, current and proposed values, and protected fields — then confirmation before any write. **Writes only after you confirm.** Protected fields are never touched.

### 4. Share the result

```
Give me a stand-up summary and a Confluence-ready draft.
Do not publish until I approve.
```

Get: a read-only stand-up summary, then a Confluence draft shown to you before publishing. **Confluence is never published automatically.**

---

## The common journey

```
Orient (read-only)  →  Improve (draft-only)  →  Approve and act  →  Communicate
```

Each stage is optional. You can stop after the backlog review, improve only selected stories, or skip directly to publishing a summary.

---

## Install

`atlassian` is **user-scope by default** — your Atlassian credentials are yours, not a project's.

```bash
agentbundle install --pack atlassian --scope user <catalogue>
```

Or install via the Claude plugin registry:

```
claude plugin install atlassian@agent-ready-repo
```

## Set up credentials

The Jira and Confluence skills authenticate with either an API token (Atlassian Cloud personal access token) or SSO credentials (for enterprise instances that enforce corporate single sign-on instead of personal tokens).

Install the `credential-brokers` pack, then say **"set up credentials"** — the agent prompts for the right credential type and stores it in your OS keychain (or a `0600` dotfile on Linux). Secrets never go on the command line and never enter the repo. See the [`credential-brokers` README](../credential-brokers/README.md).

If your organisation uses SSO-only access, see the [SSO authentication guide](/agent-ready-repo/docs/guides/atlassian/how-to/authenticate-jira-confluence-with-sso-cookies/) for the SSO-broker setup.

## Scope and permissions

- Read access is required to all projects you query.
- Write access is required only for the specific issues you approve updating.
- Confluence publish requires write access to the target space.
- SSO-protected instances: see [Authenticate with SSO](/agent-ready-repo/docs/guides/atlassian/how-to/authenticate-jira-confluence-with-sso-cookies/).

---

## Skills included — under the hood

You do not need to select these manually. They are named here for reference.

| Skill | Purpose |
|---|---|
| `jira-team-status` | Read-only team backlog snapshot — grouped by readiness, with scope and completeness disclosure |
| `jira-story-triage` | Story readiness review, draft improvements, optional write-back after approval |
| `jira` | Read and write individual Jira issues; canonical write target for approved updates |
| `confluence-publisher` | Publish Markdown reports to Confluence pages — always preview before write |
| `confluence-crawler` | Mirror a Confluence space to Markdown |
| `flow-metrics` | DORA / Flow Framework metrics from Jira changelogs — read-only |
| `ai-adoption-report` | Compare flow-metrics outputs; produce an adoption report |
| `jira-brief-intake` | Read Jira work into shared content-based repository intake |
| `jira-align-brief-intake` | Read Jira Align work into shared content-based repository intake |
| `jira-refresh` | Review Jira source changes; optionally comment, transition, or close through confirmed token-authenticated writes |
| `jira-align-refresh` | Review Jira Align source changes; remote write-back is unsupported |
| `jira-defect-flow` | Fix a Jira defect end-to-end — pull, fix, PR, transition |
| `jira-align` | Read and write Jira Align portfolio data |

---

→ [Full tutorial — Review your team backlog from start to finish](/agent-ready-repo/docs/guides/atlassian/tutorials/review-your-team-backlog/)\
→ [How-to — common Jira tasks](/agent-ready-repo/docs/guides/atlassian/how-to/work-with-jira/)\
→ [How-to — refresh tracked work safely](/agent-ready-repo/docs/guides/_shared/how-to/use-work-intake/)\
→ [Skills reference — exact read, write, and approval contracts](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/)\
→ [How the pack works — composition model](/agent-ready-repo/docs/guides/atlassian/explanation/atlassian-pack/)\
→ [Journey — four-stage visual storyboard](/journeys/atlassian/)
