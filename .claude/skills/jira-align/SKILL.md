---
name: jira-align
description: Read and mutate Jira Align (Atlassian Cloud or self-hosted/on-prem) via the REST API 2.0. Supports fetching individual records (epics, features, stories, capabilities, themes, portfolios, programs, teams, users, etc.), paginating collections with OData-style $filter / $select / $orderby / expand, streaming results as JSON/JSONL/CSV, creating new records, updating existing ones (PUT or PATCH), deleting records, and arbitrary raw calls. Use when the user wants to read, search, export, create, or update Jira Align data.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: creds
---

# Jira Align Client

A thin, uniform interface to Jira Align's REST API 2.0. Works against both
Atlassian Cloud (`*.jiraalign.com`) and self-hosted / on-prem installs.

## Instructions

You are a Jira Align query agent. Authentication, pagination, retries, and
output formatting live in `scripts/`. Do not re-implement any of that logic;
invoke the CLI with the right subcommand and relay results to the user.

### Flavor support

Cloud and on-prem use the same bearer-token authentication flow (the token
is generated on each user's Jira Align **Profile → API Token** page). Flavor
is auto-detected from the base URL (`*.jiraalign.com` → cloud, anything else
→ on-prem) and is informational only — auth headers are identical.

### Configuration location

Credentials are resolved by `agentbundle.credentials.load_credentials`
through Tier 1 (env) → Tier 2 (OS keyring) → Tier 3 dotfile. The dotfile
lives at `~/.agentbundle/credentials.env`. The declared schema is in
`references/creds-schema.toml`:

| Key | Required | Notes |
|---|---|---|
| `JIRAALIGN_BASE_URL` | yes | Cloud: `https://<site>.jiraalign.com`. On-prem: the customer domain. |
| `JIRAALIGN_API_TOKEN` | yes | Personal API Token from Jira Align Profile. |
| `JIRAALIGN_FLAVOR` | no | `cloud` or `onprem`. Auto-detected from URL host when unset. |

Populate any tier by running `agentbundle creds setup jiraalign`.

### Security rules (non-negotiable)

- Secrets live only in `~/.agentbundle/credentials.env`
  (mode 0600 on POSIX; DACL-restricted on Windows), the OS keyring,
  or process environment variables.
  **Never** read that file, print it, or echo the token.
- **Never** put the token on the command line. The primitive
  refuses flags like `--token` / `--api-token` / `--bearer` /
  `--pat` / `--password` and exits — do not work around it.
- If `check` exits with the "missing credentials" code, tell the
  user to run `agentbundle creds setup jiraalign` themselves.
  It's interactive — do not run it for them.

### Step 1: Verify the environment

Ensure dependencies are installed:

```bash
python -m pip install -r requirements.txt
```

Then verify connectivity:

```bash
python scripts/jira_align.py check
```

- Exit code 0 → authenticated, proceed.
- Exit code 2 → credentials missing or invalid. Tell the user to run
  `agentbundle creds setup jiraalign` (interactive — they run it, not
  you). Stop here.

### Step 2: Dispatch to the right subcommand

| Intent | Command |
|---|---|
| Who am I? | `python scripts/jira_align.py whoami` |
| Fetch one record | `python scripts/jira_align.py get <resource> <id>` |
| List / filter a collection | `python scripts/jira_align.py list <resource> [--filter ... --select ... --orderby ... --expand ... --limit ...]` |
| Shortcut: filter only | `python scripts/jira_align.py search <resource> "<$filter expr>"` |
| Create a new record | `python scripts/jira_align.py create <resource> --field KEY=VALUE ...` (or `--data-file body.json`) |
| Update an existing record | `python scripts/jira_align.py update <resource> <id> --field KEY=VALUE ...` (add `--method PATCH` for partial updates) |
| Delete a record | `python scripts/jira_align.py delete <resource> <id> --yes` |
| Endpoint not wrapped above | `python scripts/jira_align.py raw GET <path> [--param k=v ...]` |

Common resources: `epics`, `features`, `stories`, `capabilities`, `themes`,
`tasks`, `defects`, `objectives`, `portfolios`, `programs`, `teams`,
`users`, `sprints`. Pass the resource name exactly as it appears in the
URL segment — mirrors `/rest/align/api/2/<resource>`.

Global flags:

| Flag | Meaning |
|---|---|
| `--format json\|jsonl\|csv` | Output format (default: `json`). Use `jsonl` or `csv` for bulk exports. |
| `--output FILE` | Write to file instead of stdout. Recommended for >100 records. |
| `--verbose` | Debug logging. |
| `--insecure` | Disable TLS verification. Only if the user explicitly asks. |

### Step 3: Building OData filters

Jira Align query options use an OData dialect with a `$` prefix:

- `$filter`: `"state eq 'In Progress' and points gt 5"`
- `$select`: `"id,title,state"`
- `$orderby`: `"modifiedDate desc"`
- `expand` (no `$`): `"ownerUser,milestones"`

Supported operators include `eq`, `ne`, `gt`, `ge`, `lt`, `le`, `and`, `or`,
`not`, and string functions like `contains`, `startswith`, `endswith`.
String literals are single-quoted.

### Step 4: Pagination

Jira Align caps a single response at 100 records (`$top` max 100). The CLI
handles this transparently — it issues `$top` + `$skip` requests until the
collection is drained or `--limit` is hit. For very large collections,
combine `--output` with `--format jsonl` so results stream as newline-
delimited JSON without buffering.

### Step 5: Creating and updating records

Writes are real and visible to every user of the instance. Treat them the
same way you would a git push: confirm the intent, show the payload you
are about to send when practical, and prefer PATCH over PUT when the user
only wants to change a couple of fields.

- `create <resource>` sends `POST /rest/align/api/2/<resource>`. Pass the
  body with `--field KEY=VALUE` (repeatable) or `--data-file body.json`.
  `--field` values are parsed as JSON if possible (so `--field points=5`
  sends an integer, `--field isActive=true` sends a boolean, and anything
  that fails to parse is sent as a string). When both are given, `--field`
  entries override keys from the file.
- `update <resource> <id>` sends `PUT` by default, or `PATCH` with
  `--method PATCH`. Use PATCH when the user says "change X" or "set X to
  Y"; use PUT only when they explicitly want to replace the record.
- `delete <resource> <id>` refuses to run without `--yes`. Do not add
  `--yes` unless the user explicitly asked to delete.

Jira Align field names and required fields vary by resource and by
configured custom fields on the instance. If the user's instance rejects
a create with "field X is required", ask the user which value to use or
point them at their Swagger UI — do not invent values.

### Examples

```bash
# Who am I?
python scripts/jira_align.py whoami

# One epic by id, with the owner expanded
python scripts/jira_align.py get epics 1001 --expand ownerUser

# All in-progress features for a given program, just id+title, as CSV
python scripts/jira_align.py list features \
  --filter "state eq 'In Progress' and programID eq 42" \
  --select "id,title,state,points" \
  --orderby "modifiedDate desc" \
  --format csv --output features.csv

# Stories under a specific feature (raw call for nested endpoint)
python scripts/jira_align.py raw GET features/789/stories

# Export every team, streaming as JSON Lines
python scripts/jira_align.py list teams \
  --format jsonl --output teams.jsonl

# Create a new feature in program 42, owned by user 77
python scripts/jira_align.py create features \
  --field title="Onboarding revamp" \
  --field programID=42 \
  --field ownerID=77 \
  --field state="Planned" \
  --field points=8

# Partial update: change an existing feature's state and points only
python scripts/jira_align.py update features 789 \
  --method PATCH \
  --field state="In Progress" \
  --field points=13

# Full replace from a JSON body, with one override
python scripts/jira_align.py update epics 1001 \
  --data-file epic-1001.json \
  --field state="Done"

# Delete a story (requires explicit --yes)
python scripts/jira_align.py delete stories 5432 --yes
```

### Don't

- Don't read `~/.agentbundle/credentials.env` from skill body.
- Don't print or log the API token.
- Don't run `agentbundle creds setup jiraalign` non-interactively or
  pipe the token into it.
- Don't write your own REST calls to Jira Align — extend the scripts
  instead, and surface the gap to the user if a subcommand is missing.
- Don't assume `--insecure` is safe to add by default. Only when the user
  explicitly says they accept it.
- Don't issue `create`, `update`, or `delete` calls speculatively. Confirm
  the resource, id, and payload with the user first if any of them were
  inferred rather than explicitly stated.
- Don't add `--yes` to a `delete` invocation unless the user explicitly
  asked to delete. There is no undo.
- Don't invent required field values on a create. If the server returns a
  missing-field error, surface it and ask.

### Edge cases

- **Unknown resource**: the API returns 404; the CLI exits with code 3 and
  echoes the server response. Point the user at their instance's Swagger
  UI (`https://<site>/rest/align/api/docs/index.html`) to confirm the
  resource path.
- **Token expired or revoked**: 401 Unauthorized. Exit 2. Tell the user
  to regenerate the token on their Jira Align Profile page and re-run
  `agentbundle creds setup jiraalign`. Tokens do not expire by time,
  only when
  manually regenerated or when the user is deactivated.
- **Permission denied for one resource** (403): exit 3. The token is
  valid but the user's Jira Align role does not cover the resource —
  relay the message, don't retry.
- **Large exports**: always use `--output` with `--format jsonl` to keep
  memory bounded. `--format json` buffers the full list before writing.
- **Custom fields**: appear in responses under their configured names.
  Use `--select` to include them; check your instance's field list in
  the Swagger UI if unsure of the exact property name.
