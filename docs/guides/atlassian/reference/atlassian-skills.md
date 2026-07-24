# `atlassian` skills reference

Exact inputs, reads, writes, outputs, limits, and approval behavior for every skill
in the atlassian pack.

Credentials resolve in-process through a three-tier ladder (environment variable →
OS keyring → `~/.agentbundle/credentials.env` dotfile). Cleartext never reaches the
model. See [Credentialed skills](../../credential-brokers/explanation/credentialed-skills.md).

---

## Intent index

| I want to… | Use |
| --- | --- |
| See everything a team can work on | `jira-team-status` |
| Find work that is ready to pull | `jira-team-status` |
| Find blockers, stale work, or unassigned work | `jira-team-status` |
| Find stories that are not actionable | `jira-story-triage` |
| Draft better story details and acceptance criteria | `jira-story-triage` |
| Search, create, or update individual Jira issues | `jira` |
| Fix a defect end-to-end from Jira to PR | `jira-defect-flow` |
| Turn a Jira epic into engineering specs | `jira-brief-intake` |
| Turn a Jira Align feature into engineering specs | `jira-align-brief-intake` |
| Compute DORA / Flow Framework metrics | `flow-metrics` |
| Compare AI-tagged stories to control stories | `ai-adoption-report` |
| Mirror a Confluence space to Markdown | `confluence-crawler` |
| Publish Markdown to a Confluence page | `confluence-publisher` |

---

## Filter by behavior

**Read-only:** `jira-team-status` · `flow-metrics` · `confluence-crawler` · `ai-adoption-report`

**Drafts only (no Jira write until approval):** `jira-story-triage`

**Writes Jira:** `jira` · `jira-defect-flow` · `jira-story-triage` (after approval only)

**Writes Confluence:** `confluence-publisher`

**Team-level:** `jira-team-status` · `jira-story-triage` · `flow-metrics` · `ai-adoption-report`

**Issue-level:** `jira` · `jira-defect-flow` · `jira-brief-intake`

---

## `jira-team-status`

**Use it for:** A read-only status view of a team's Jira work — what can be picked up
next, what is blocked, what is unassigned, and a stand-up or sprint summary.

**Natural requests**

- "What can the Acme team pick up next in APP and API?"
- "Give me a team status for stand-up."
- "Show me the whole Acme team backlog — current sprint, open backlog, unassigned, and blocked."
- "What's blocked in APP this week?"

**Required scope**

One or more Jira project keys, plus one of: current sprint (default), a named sprint, a
team name, a JQL filter, or a whole-backlog flag.

**Reads**

Issues from `jira: search` using the resolved scope. Fields: `summary`, `status`,
`statusCategory`, `assignee`, `issuetype`, `priority`, `flagged` / impediment,
`issuelinks` (blocker links), `customfield_*` for team field and story points.

**Writes**

Nothing, by default. Its only write is a bare pass-through to `jira: update-issue`
when the user explicitly asks to set a field — with the payload confirmed first.

**Returns**

A five-section snapshot:
1. Ready to pull (grouped Quick / Standard / Involved)
2. In progress
3. Blocked
4. Unassigned
5. Needs detail (product attention)

Plus a recently-changed note, stale markers, and a summary line disclosing scope
and coverage. Followed by a read-only pick-up hand-off (start-delivery routing or
route to `jira-story-triage`).

**Coverage**

Discloses whether the result is complete, filtered, or capped. Pagination is
automatic. When Jira returns incomplete results (permission gaps, API limits), the
summary line says so.

**Limits**

Whole-backlog requests across many projects may be slow on large Jira instances.
Use `--limit` or a narrowing JQL to cap the fetch.

**Approval behavior**

Read-only by default. Any write requires an explicit user request and a payload
confirmation before `update-issue` fires.

**Team-scope resolution**

1. Direct project key(s) named by the user.
2. A Jira board with the team name in its name.
3. Issues whose Team custom field matches the team name.
4. A JQL filter the user provided.

When two scopes match, the agent asks which to use before reading.

**Ready-to-pull rule**

An item is **ready to pull** only when all four hold:
1. In the selected team scope.
2. In an eligible backlog state — default `statusCategory = "To Do"` (spans Backlog / To Do / Selected for Development / Open). Teams override by naming explicit statuses.
3. No known unresolved blocker — Flagged field set, an unresolved "is blocked by" link, or status in a team-declared blocked set.
4. Meets the five-question readiness bar.

When any condition can't be determined, the item is labelled **needs confirmation**,
not asserted ready or blocked.

**Common follow-up**

```
Which ready items have no assignee?
What changed since yesterday?
```

**Related skills:** `jira-story-triage` (to judge readiness in depth and fix weak items)

---

## `jira-story-triage`

**Use it for:** Reviewing a Jira backlog, sprint, or JQL scope for story readiness,
and improving the weak ones.

**Natural requests**

- "Which stories are not ready for engineering?"
- "Make these tickets actionable."
- "Apply the five-question bar to the items that need story work."
- "Draft acceptance criteria for the top five."

**Required scope**

A Jira project key plus one of: a sprint, a JQL filter, or a list of issue keys.

**Reads**

Issue summary, description, acceptance criteria (custom field or description section),
issuetype, status, story points, and the invoking repo URL (for Q2 scope grounding).

**Writes**

Nothing until approval. The write flow is:
1. Agent drafts a proposed improvement.
2. You review the draft.
3. You explicitly approve the exact payload.
4. Agent calls `jira: update-issue` for that one issue only.

**Returns**

Per-item findings:
- What is missing (which question failed and the specific gap)
- Why it prevents action
- The proposed improvement (description rewrite or AC addition)
- Any unresolved human question (PO decision needed)
- Expected readiness after the draft
- Confirmation that no Jira write occurred

**The five-question readiness bar**

> A story is actionable when all five are true:
> **(Q1)** it is a **self-contained code/config/doc change** — not discovery, design,
> or coordination work;
> **(Q2)** it names a **reachable repo or file scope** so the change can be located
> without a follow-up meeting;
> **(Q3)** its **acceptance criteria are checkable by diff review alone** — no "TBD",
> "coordinate with", "decide on", or "prototype";
> **(Q4)** **no human decision is needed mid-flight** — no open design question,
> no external approval gate that cannot be confirmed before work starts;
> **(Q5)** it is **right-sized for one PR** — the scope is an enumerable set of files
> or PRs a single person or agent can produce without decomposing into sub-stories.

**Readiness outcomes**

| Outcome | Condition |
| --- | --- |
| Ready for engineering | All five questions pass |
| Gated (external) | Exactly one failure, and it is a specific named external dependency (not a content gap) |
| Not ready — needs shaping | Any content failure: Q1 wrong type, Q2 missing scope, Q3 missing ACs, Q4 open design question, Q5 too large |
| Needs detail | Empty description, image-only description, or discovery issuetype with no ACs |

**Coverage**

Processes all issues in the stated scope. Discloses count and completeness. Large
scopes may be batched; batching is disclosed.

**Limits**

Items whose description is empty or image-only are flagged as "Needs detail" and
not scored.

**Approval behavior**

Each write is per-item and opt-in. The agent shows the exact field and value before
calling `update-issue`. There is no batch-approve all.

**Common follow-up**

```
Show me the approved draft for APP-219 again before I confirm.
Which items would be ready if the PO answered the open question?
```

**Related skills:** `jira-team-status` (for the read-only team state view), `jira`
(for the write path)

---

## `jira`

**Use it for:** Direct JQL search, issue fetch, create, update, transition, comment,
and attach. The underlying primitive that `jira-team-status`, `jira-story-triage`,
and `jira-defect-flow` invoke.

**Natural requests**

- "Search for all open bugs in APP created in the last 7 days."
- "Fetch APP-203 with full fields."
- "Create a story in API with summary X and description Y."
- "Transition API-92 to Done."

**Required scope**

A project key for search; an issue key for fetch, update, transition, comment, attach.

**Reads**

JQL search with auto-pagination. Fields: `summary`, `status`, `assignee`, `issuetype`,
`priority`, `created`, `updated`, `description`, `customfield_*`. Custom fields
identified by `customfield_10010`-style keys; resolve display names with `--expand names`.

**Writes**

`create-issue` — creates an issue with the fields you provide.
`update-issue` — partial PUT: only the fields you pass change.
`transition` — changes workflow state. (`status` via `update-issue` is silently ignored — use `transition`.)
`comment` — adds a comment.
`delete-issue` — requires `--yes`; no undo.

**Returns**

Issue JSON, JSONL, or CSV to stdout or `--output`. `search` returns an array; single-issue
commands return one object.

**Coverage**

`search` paginates automatically — Cloud uses `nextPageToken`, Server uses `startAt`.
For bulk exports (> 100 issues), use `--format jsonl` to stream to disk.

**Limits**

`--page-size` capped at 100 by the Jira API. Very large result sets should use
`--format jsonl --output FILE` to avoid memory pressure.

**Approval behavior**

`delete-issue` refuses without `--yes`. Writes are real and immediately visible to
everyone on the instance — confirm project and field payload before calling.

**Required credentials**

`JIRA_BASE_URL` (required), `JIRA_API_TOKEN` (required), `JIRA_EMAIL` (Cloud only).

**Auth (dual)**

`auth: sso-cookie` with a `creds` fallback. On Data Center instances behind corporate
SSO where tokens are blocked, pre-bake `references/sso-config.toml` and run
`setup_sso.py` once; subsequent reads authenticate by captured web session. Writes
via SSO cookie are refused pending XSRF design — use token auth for writes.

**Related skills:** `jira-team-status`, `jira-story-triage`, `jira-defect-flow`

---

## `jira-defect-flow`

**Use it for:** Handling a Jira defect end-to-end: pull the ticket, fix the code,
open a PR, then comment and transition the ticket.

**Natural requests**

- "Fix APP-203 — take it from Jira to a PR."

**Required scope**

A single Jira issue key.

**Reads**

The issue via `jira: get-issue`. Hands the fix to `bug-fix`. Opens a PR via `gh`.

**Writes**

Adds a comment and transitions the ticket after the PR is opened.

**Returns**

A triage brief at `.context/defects/$KEY.md`, a feature branch, a PR, and Jira
comments and transitions.

**Coverage**

Stops at PR-opened by default. A dev-deploy step runs only when the consumer repo
provides one.

**Approval behavior**

No explicit approval gate beyond the PR review. Jira writes (comment + transition)
are automatic after the PR is opened.

**Related skills:** `jira` (for the Jira read/write path), `bug-fix` (for the fix)

---

## `jira-brief-intake`

**Use it for:** Turning a Jira epic or multi-issue selection into a structured
engineering brief.

**Natural requests**

- "Turn APP-epic-42 into a product brief."
- "Pull the Acme board sprint into a brief."

**Required scope**

A Jira epic key, a board, a sprint, or a JQL selection.

**Reads**

Epic and its children via `jira: get-issue` and `search`. Maps issues onto a Shape B
product brief.

**Writes**

A brief at `docs/product/briefs/<slug>.md`. Read-only against Jira — never writes
back.

**Returns**

A Shape B product brief, then a hand-off to `receive-brief`.

**Required credentials**

None of its own — inherits through `jira`.

**Related skills:** `jira`, `receive-brief`, `jira-align-brief-intake`

---

## `jira-align-brief-intake`

**Use it for:** Turning a Jira Align Feature into a product brief.

Same pattern as `jira-brief-intake` but reads from Jira Align via `jira-align`.
Requires one-time customisation of `references/field-mapping.md` for org-specific
workflow state names. 1-way intake only — never writes to Jira Align.

**Required credentials**

`JIRAALIGN_BASE_URL`, `JIRAALIGN_API_TOKEN`.

---

## `jira-align`

**Use it for:** Reading and managing Jira Align portfolio data — epics, features,
stories, capabilities, portfolios, programs, and teams.

A separate product from Jira with separate credentials. Subcommands: `check`,
`whoami`, `get`, `list`, `search`, `create`, `update`, `delete`, `raw`.

**Required credentials**

`JIRAALIGN_BASE_URL`, `JIRAALIGN_API_TOKEN`.

---

## `flow-metrics`

**Use it for:** Computing DORA / Flow Framework metrics over a Jira project or Jira
Align program.

**Reads**

Issue changelogs via `jira` and `jira-align`. Computes cycle time, lead time,
throughput, WIP, flow load, rework rate, flow time, flow efficiency, flow
distribution, and defect ratio.

**Writes**

Nothing. Read-only.

**Returns**

Canonical JSON or CSV with `meta`, `aggregates`, optional `cohort_breakdown`, and
`notes`. Output schema pinned at `references/output.schema.json`.

**Coverage**

Date range defaults to last 90 days. Cancelled or out-of-scope issues are noted in
the `notes` section.

**Required credentials**

None of its own — inherits through `jira` (and `jira-align` for Align scope).

---

## `ai-adoption-report`

**Use it for:** Pairing `flow-metrics` outputs and rendering a Markdown comparison
report. Three modes: `baseline` (before/after two windows), `cohort` (AI-tagged vs
control within one window), `program` (roll up across many scopes).

**Reads**

Local JSON files only — no upstream calls.

**Writes**

A Markdown report and a JSON sidecar at `--output`.

**Required credentials**

None — reads only local files.

---

## `confluence-crawler`

**Use it for:** Mirroring a Confluence space or page tree to Markdown for local
analysis.

**Reads**

Page hierarchy via the Confluence REST API. Converts each page to Markdown with YAML
frontmatter (`confluence_id`, `version`, `space_key`, `updated`, `author`, `url`).

**Writes**

Local Markdown files. Nothing is written to Confluence.

**Required credentials**

`CONFLUENCE_BASE_URL`, `CONFLUENCE_API_TOKEN`, `CONFLUENCE_EMAIL` (Cloud only).
Shares the `confluence` namespace with `confluence-publisher`.

---

## `confluence-publisher`

**Use it for:** Publishing Markdown to a Confluence page — creates or updates in place.

**Reads**

The target page's current version (for optimistic-locking conflict detection).

**Writes**

Creates or updates a Confluence page. Handles optimistic-locking 409s with one retry.

**Returns**

`OK: <create|update> page <id> (version N) — <url>` on success.

**Approval behavior**

`--dry-run` prints rendered storage XHTML and the planned operation without writing.
No built-in approval gate in the CLI — the skill body requires explicit user
confirmation before calling the publisher.

**Required credentials**

Same `confluence` namespace as `confluence-crawler` — configure either and both work.
