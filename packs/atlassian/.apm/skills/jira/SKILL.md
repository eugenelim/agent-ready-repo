---
name: jira
description: Read and mutate Jira (Atlassian Cloud or self-hosted Server / Data Center) via the REST API. Supports JQL search with auto-pagination, fetching issues / projects / users, creating and updating issues, applying workflow transitions, adding comments and attachments, deleting issues, listing projects, looking up users, and an arbitrary raw escape hatch. Streams results as JSON, JSONL, or CSV. Handles Cloud (REST v3, basic auth with email + API token, ADF, nextPageToken) vs Server/DC (REST v2, bearer Personal Access Token, plain text, startAt) differences automatically. Use when the user wants to read, search, export, create, update, or transition Jira data.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: sso-cookie
  auth-fallback: creds
  namespace: jira
  keys: ["API_TOKEN"]
---

# Jira Client

A thin, uniform interface to the Jira REST API. Works against both
Atlassian Cloud (`*.atlassian.net`) and self-hosted Server / Data Center
installs. **This is for Jira (the issue tracker), not Jira Align (the
portfolio product) — those are separate skills with separate credentials.**

## Instructions

You are a Jira query agent. Authentication, pagination, retries, ADF
wrapping, and output formatting live in `scripts/`. Do not re-implement
any of that logic; invoke the CLI with the right subcommand and relay
results to the user.

### Flavor support

The CLI auto-detects Cloud vs Server/DC from the base URL host:

- `*.atlassian.net`, `*.jira.com`, `*.jira-dev.com` → Cloud.
- Anything else → Server / Data Center.

Auth schemes differ:

| Flavor | Auth | API prefix | JQL endpoint | Description body |
|---|---|---|---|---|
| Cloud | Basic `base64(email:api_token)` | `/rest/api/3` | `POST /search/jql` (nextPageToken) | ADF (auto-wrapped) |
| Server/DC | `Bearer <PAT>` | `/rest/api/2` | `GET /search` (startAt) | Plain string / wiki markup |

The CLI handles both transparently. Plain-string `description` /
`environment` fields you pass via `--field` are auto-wrapped to ADF on
Cloud.

### Configuration location

Credentials are resolved by the build-projected `credentials_shim.load_credentials`
through the Tier 1 (env) → Tier 2 (OS keyring) → Tier 3 dotfile ladder.
The dotfile lives at `~/.agentbundle/credentials.env` (mode 0600 on
POSIX; DACL-restricted on Windows). The declared schema is in
`references/creds-schema.toml`:

| Key | Required | Notes |
|---|---|---|
| `JIRA_BASE_URL` | yes | Cloud: `https://<site>.atlassian.net`. Server: your Jira URL. |
| `JIRA_EMAIL` | Cloud only | Atlassian account email — used as Basic auth username. |
| `JIRA_API_TOKEN` | yes | Cloud API token (`id.atlassian.com` → API tokens) or Server PAT. |
| `JIRA_FLAVOR` | no | `cloud` or `server`. Auto-detected from URL host when unset. |

Populate any tier by running `credential-setup` skill — the CLI
walks the schema interactively and writes the values where you choose.

### Security rules (non-negotiable)

- Secrets live only in `~/.agentbundle/credentials.env`
  (mode 0600 on POSIX; DACL-restricted on Windows), the OS keyring,
  or process environment variables.
  **Never** read that file, print it, or echo the token.
- **Never** put the token on the command line. The primitive
  refuses flags like `--token` / `--api-token` / `--bearer` /
  `--pat` / `--password` and exits — do not work around it.
- If `check` exits with the "missing credentials" code, tell the
  user to run `credential-setup` skill themselves.
  It's interactive — do not run it for them.

This skill is **dual-auth** (`auth: sso-cookie` with a `creds` fallback): on a
Data Center instance behind corporate SSO it authenticates by a captured web
session (cookie jar) resolved through the `sso-broker`; everywhere else it uses
the token (`creds`) path above. On the SSO-cookie path:

- The session cookie jar lives only under the broker's `0600` store; the skill
  reads it in-process via the `credbroker` resolver, which returns a *path*, not
  the bytes. **Never** read the jar file directly, print its contents, or echo
  cookie values.
- **Never** put a session cookie on the command line. The skill attaches cookies
  to its HTTP client internally and sends no `Authorization` header on this path.
- If the SSO session is missing or expired, tell the user to run
  `python scripts/setup_sso.py` (which drives `sso-broker register`) themselves —
  it opens a browser for interactive sign-in, so do not run any setup helper for
  them.

### Step 1: Verify the environment

Ensure dependencies are installed:

```bash
python -m pip install -r requirements.txt
```

Then verify connectivity:

```bash
python scripts/jira.py check
```

- Exit code 0 → authenticated, proceed.
- Exit code 2 → the user must act (credentials missing/invalid/expired). Tell
  the user to run `credential-setup` skill themselves (interactive — they run
  it, not you). Stop here.
- Any other non-zero → see *When a request fails*.

### When a request fails

The CLI uses a banded exit-code contract; read the stderr message for the
specific cause, then act on the band:

| Exit | Band | What to do |
|---|---|---|
| 0 | success | proceed |
| 1 | functional error — server 5xx, transport, keychain hard-fail, unexpected | surface the message to the user; don't loop or retry blindly |
| 2 | user must act — credentials missing/invalid/expired, 401/403 | tell the user to run `credential-setup` themselves (interactive — do not run it for them), then re-run `check` |

- A **401** means the credential is invalid or expired → exit 2 → re-auth via
  `credential-setup`.
- A **403** means authenticated but forbidden (missing scope/permission) →
  exit 2 → the user regenerates the token with the right scope; don't retry.
- `Tier2HardFailError` (OS keyring locked/unavailable) or a missing credential
  shim surface as exit 1 with a message naming the cause (e.g. reinstall the
  pack to restore the shim).

### Step 2: Dispatch to the right subcommand

| Intent | Command |
|---|---|
| Who am I? | `python scripts/jira.py whoami` |
| Fetch one issue | `python scripts/jira.py get-issue PROJ-123 [--fields ... --expand ...]` |
| JQL search | `python scripts/jira.py search "<JQL>" [--fields ... --limit ...]` |
| Create an issue | `python scripts/jira.py create-issue --field KEY=VALUE ...` (or `--data-file body.json`) |
| Update an issue | `python scripts/jira.py update-issue PROJ-123 --field KEY=VALUE ...` (PUT, partial) |
| Delete an issue | `python scripts/jira.py delete-issue PROJ-123 --yes` |
| List transitions | `python scripts/jira.py list-transitions PROJ-123` |
| Apply transition | `python scripts/jira.py transition PROJ-123 --to "In Progress"` |
| Add a comment | `python scripts/jira.py comment PROJ-123 --body "text"` |
| Attach a file | `python scripts/jira.py attach PROJ-123 --file ./screenshot.png` |
| Fetch a project | `python scripts/jira.py get-project PROJ` |
| List projects | `python scripts/jira.py list-projects [--query KW]` |
| Fetch a user | `python scripts/jira.py get-user --account-id ABC` (Cloud) **or** `--username jdoe` (Server) |
| Search users | `python scripts/jira.py list-users --query "ada"` |
| Endpoint not wrapped above | `python scripts/jira.py raw GET <path> [--param k=v ...]` |

Global flags:

| Flag | Meaning |
|---|---|
| `--format json\|jsonl\|csv` | Output format (default: `json`). Use `jsonl` or `csv` for bulk exports. |
| `--output FILE` | Write to file instead of stdout. Recommended for >100 records. |
| `--verbose` | Debug logging. |
| `--insecure` | Disable TLS verification. Only if the user explicitly asks (common on self-signed Server installs). |

### Step 3: JQL — the primary query language

JQL (Jira Query Language) is how you filter issues. Quote the entire
expression so the shell doesn't split it.

Common patterns:

- `project = PROJ AND status = "In Progress"`
- `assignee = currentUser() AND resolution = Unresolved`
- `project = PROJ AND created >= -7d ORDER BY created DESC`
- `text ~ "login bug"` (full-text)
- `labels in (urgent, security)`
- `"Epic Link" = PROJ-100`

Cloud requires `accountId` for user-valued JQL clauses where Server
accepts username, e.g. on Cloud: `assignee = "5b10ac8d82e05b22cc7d4ef5"`;
on Server: `assignee = jdoe`.

The `search` subcommand handles pagination automatically — Cloud uses
`nextPageToken`-based pagination on `POST /search/jql` (no total count
returned), Server uses `startAt` + `maxResults` on `GET /search`. Pass
`--limit N` to cap the total, `--page-size N` (≤ 100) to control batch
size.

### Step 4: Field references

- `--fields "summary,status,assignee"` — comma-separated list. Use
  `*all` for every field, `-comment` to exclude. Custom fields are
  `customfield_10010`-style ids; resolve their human names with
  `raw GET field`.
- `--expand "renderedFields,names,transitions,changelog"` — comma list.
  Common values: `renderedFields` (HTML-rendered description / comments),
  `names` (custom field id → display name map), `schema`, `transitions`,
  `changelog`.

### Step 5: Creating and updating issues

Writes are real and visible to every user of the instance. Treat them
the same way you would a git push: confirm the intent, show the payload
when practical, and prefer narrow updates over wholesale replacement.

- `create-issue` sends `POST /rest/api/<v>/issue`. Required fields are
  almost always `project`, `summary`, and `issuetype`. The body may be
  flat (`--field summary=...`) or pre-wrapped (`--data-file` containing
  `{"fields": {...}}`).
- `--field` values are JSON-parsed when possible. So
  `--field 'project={"key":"PROJ"}'` sends a JSON object,
  `--field 'labels=["urgent"]'` sends an array, `--field summary="text"`
  sends a string.
- `update-issue` sends `PUT /issue/{key}` with **only the fields you
  pass** — the API merges, it does not replace. Pass `--no-notify` to
  suppress watcher emails on bulk edits.
- ADF: on Cloud v3, `description` and `environment` must be Atlassian
  Document Format (a JSON document). The CLI auto-wraps a plain string
  for those two fields, so `--field description="hello"` works on both
  flavors. For richer formatting (lists, code blocks, mentions) pass a
  pre-built ADF doc via `--data-file`.
- `delete-issue` refuses to run without `--yes`. If the issue has
  subtasks, add `--delete-subtasks` (otherwise the call 400s). **Do not
  add `--yes` unless the user explicitly asked to delete.**

### Step 6: Transitions

Workflow state changes go through `transition`, not through `update-issue`
(setting `status` directly does not work). Two ways to specify the target:

- `--to "In Progress"` — looks up the transition by name on that issue
  and resolves to the id automatically.
- `--id 31` — direct transition id (use `list-transitions PROJ-123` to
  discover available ids).

You can also set fields during a transition (e.g. resolution on the
"Done" transition) by repeating `--field KEY=VALUE`.

### Step 7: User references differ by flavor

| Flavor | Identifier | Example field value |
|---|---|---|
| Cloud | `accountId` (24-char opaque) | `--field 'assignee={"accountId":"5b10..."}'` |
| Server/DC | `name` (username) | `--field 'assignee={"name":"jdoe"}'` |

If the user gives you an email or display name, look up the accountId
first with `list-users --query "<email or name>"` on Cloud, or with
`get-user --username jdoe` on Server.

### Examples

Three canonical patterns inline. For everything else (whoami, get-issue,
update-issue, comment, attach, list-projects, list-users, raw, delete-issue,
worklog) see [`references/examples.md`](references/examples.md), loaded
on demand.

```bash
# JQL: 50 most recently created bugs in PROJ, as JSONL on disk
python scripts/jira.py search \
  "project = PROJ AND issuetype = Bug ORDER BY created DESC" \
  --fields "summary,status,priority,created" \
  --limit 50 --format jsonl --output bugs.jsonl

# Create a Task in PROJ
python scripts/jira.py create-issue \
  --field 'project={"key":"PROJ"}' \
  --field summary="Onboarding revamp" \
  --field 'issuetype={"name":"Task"}' \
  --field description="Migrate the welcome flow to the new tour."

# Apply a transition by name
python scripts/jira.py transition PROJ-123 --to "In Progress"
```

### Don't

- Don't read `~/.agentbundle/credentials.env` from skill body.
- Don't print or log the API token / PAT.
- Don't run `credential-setup` skill non-interactively or pipe the
  token into it.
- Don't write your own REST calls to Jira — extend the scripts instead,
  and surface the gap to the user if a subcommand is missing.
- Don't assume `--insecure` is safe to add by default. Only when the
  user explicitly says they accept it (most relevant for self-signed
  Server installs).
- Don't issue `create-issue`, `update-issue`, `delete-issue`,
  `transition`, or `comment` calls speculatively. Confirm the issue
  key, fields, and payload with the user first if any of them were
  inferred rather than explicitly stated.
- Don't add `--yes` to a `delete-issue` invocation unless the user
  explicitly asked to delete. There is no undo.
- Don't try to set `status` directly through `update-issue` — that's
  what `transition` is for. The `status` field on `update-issue` is
  silently ignored by Jira.
- Don't invent a Cloud `accountId` for a user — look it up with
  `list-users --query` first.
- Don't confuse this skill with `jira-align`. They target different
  products, different APIs, and different credentials.

### Edge cases

- **Unknown issue key**: API returns 404; CLI exits 3 and echoes the
  server response. Confirm the project key and number with the user.
- **Token expired or revoked**: 401 Unauthorized → exit 2. Cloud tokens
  can be regenerated at `id.atlassian.com → API tokens`; Server PATs in
  the user's Profile → Personal Access Tokens. Tell the user to
  re-run `credential-setup` skill after generating a new one.
- **Permission denied for a project / issue** (403): exit 3. Token is
  valid but the user's role does not cover the resource — relay the
  message, don't retry. On Cloud, a 403 with header
  `X-Seraph-LoginReason: AUTHENTICATION_DENIED` means a CAPTCHA was
  triggered; the user must log in via the web UI to clear it.
- **Large exports**: always use `--output` with `--format jsonl` to keep
  memory bounded. `--format json` buffers the full list before writing.
- **Custom fields**: appear in responses as `customfield_10010`-style
  keys. Resolve to display names with `raw GET field` (returns the full
  field catalog) or use `--expand names` on `get-issue` /  `search`.
- **ADF for rich content**: the CLI only auto-wraps plain strings for
  `description` and `environment`. For comments with formatting, lists,
  code blocks, or @-mentions, build the ADF doc yourself and pass it
  via `--data-file` to `comment` (use `raw POST issue/<key>/comment`
  with a custom body).
- **JQL parse errors**: come back as 400 with a server message naming
  the offending token. Quote string literals with double quotes inside
  JQL (`status = "In Progress"`), and shell-quote the whole expression.
- **Pagination on Cloud `/search/jql`**: no `total` field is returned
  any more — the CLI handles this and stops when `isLast` is true or no
  `nextPageToken` is returned. Don't ask "how many issues match?" —
  call `search ... --limit 1` if you only need to know whether any do,
  or count from a streamed export.
