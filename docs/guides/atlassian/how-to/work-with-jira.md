# Work with Jira

Search, fetch, create, and update Jira issues through the [`jira`](../../../../packs/atlassian/.apm/skills/jira/) skill. The skill wraps the Jira REST API behind a CLI and handles Cloud vs Server / Data Center, pagination, ADF wrapping, and output formatting for you.

This is for Jira the issue tracker, not Jira Align — those are separate skills with separate credentials.

## Before you start

The `jira` skill is credentialed. Verify connectivity first:

```bash
python scripts/jira.py check
```

Exit 0 means authenticated — proceed. Exit 2 means you must act: run the `credential-setup` skill to enter `JIRA_BASE_URL`, `JIRA_API_TOKEN`, and (on Cloud) `JIRA_EMAIL`. The model never sees the token — see [Credentialed skills](../../credential-brokers/explanation/credentialed-skills.md).

## Search with JQL

JQL filters issues. Quote the whole expression so the shell doesn't split it. The `search` subcommand paginates automatically — Cloud uses `nextPageToken`, Server uses `startAt`.

```bash
python scripts/jira.py search "project = PROJ AND status = \"In Progress\""
```

Narrow the payload with `--fields` and cap the result count with `--limit`:

```bash
python scripts/jira.py search \
  "project = PROJ AND issuetype = Bug ORDER BY created DESC" \
  --fields "summary,status,priority,created" \
  --limit 50
```

Common JQL shapes:

- `assignee = currentUser() AND resolution = Unresolved`
- `text ~ "login bug"` (full-text)
- `labels in (urgent, security)`
- `"Epic Link" = PROJ-100`

On Cloud, user-valued clauses need an `accountId`, not a username. Look one up with `list-users --query "<email or name>"`.

## Export in bulk

For more than ~100 records, stream to disk as JSON Lines. `--format json` buffers the whole list in memory; `jsonl` does not.

```bash
python scripts/jira.py search \
  "project = PROJ AND created >= -7d" \
  --fields "summary,status,created" \
  --format jsonl --output recent.jsonl
```

`--format csv` is also available for spreadsheet-bound exports.

## Fetch one issue

```bash
python scripts/jira.py get-issue PROJ-123 --fields "summary,status,assignee"
```

Custom fields come back as `customfield_10010`-style keys. Resolve their display names with `--expand names`, or pull the full catalog with `python scripts/jira.py raw GET field`.

## Create an issue

Writes are real and visible to everyone on the instance. Confirm the project, fields, and payload before you send. Required fields are almost always `project`, `summary`, and `issuetype`. `--field` values are JSON-parsed when possible, so objects and arrays work:

```bash
python scripts/jira.py create-issue \
  --field 'project={"key":"PROJ"}' \
  --field summary="Onboarding revamp" \
  --field 'issuetype={"name":"Task"}' \
  --field description="Migrate the welcome flow to the new tour."
```

On Cloud, `description` and `environment` need ADF — the CLI auto-wraps a plain string for those two fields. For richer formatting (lists, code blocks, mentions) pass a pre-built ADF document via `--data-file`.

## Update an issue

`update-issue` sends a partial `PUT` — only the fields you pass change, and the API merges rather than replaces:

```bash
python scripts/jira.py update-issue PROJ-123 \
  --field summary="Onboarding revamp (Q3)"
```

Workflow state is the exception. `status` set through `update-issue` is silently ignored — use `transition`:

```bash
python scripts/jira.py list-transitions PROJ-123
python scripts/jira.py transition PROJ-123 --to "In Progress"
```

## Pitfalls

- **A 401** means the credential is invalid or expired (exit 2) — regenerate the token and re-run `credential-setup`.
- **A 403** means authenticated but forbidden (missing permission) — relay the message, don't retry.
- **`delete-issue` refuses to run without `--yes`**, and there is no undo. Only add `--yes` when you explicitly mean to delete.
- **A JQL parse error** comes back as a 400 naming the offending token. Quote string literals inside the JQL with double quotes and shell-quote the whole expression.

For the complete subcommand and flag surface, see the [`atlassian` skills reference](../reference/atlassian-skills.md).
