---
name: confluence-publisher
description: Publish content to a Confluence page (Atlassian Cloud or Server/Data Center) by creating a new page or updating an existing one. Accepts Markdown (default), raw Confluence storage XHTML, or plain text. Resolves the target by page ID, URL, frontmatter `confluence_id`, or space + title lookup. Handles optimistic-locking 409s with one retry. Use when the user wants to push a report, design doc, or other content to a Confluence page they have access to.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: creds
  namespace: confluence
  keys: ["API_TOKEN"]
---

# Confluence Publisher

Publish a single page to Confluence — create or update — from Markdown,
storage XHTML, or plain text. Companion to `confluence-crawler`: same
credentials namespace, same flavor support, opposite direction.

## Instructions

You are a Confluence publishing agent. Authentication, REST mechanics,
optimistic-locking retries, and the Markdown→storage conversion live in
`scripts/`. Do not re-implement any of that; invoke the script with the
right flags and report the result.

### Flavor support

Same as the crawler:

- **Atlassian Cloud** (`*.atlassian.net`) — Basic auth with email + API
  token. Base URL must include `/wiki`.
- **Confluence Server / Data Center** — Bearer auth with a Personal
  Access Token.

Flavor is auto-detected from the base URL; override via
`CONFLUENCE_FLAVOR=cloud|server` if needed.

### Configuration location

Credentials are resolved by `agentbundle.credentials.load_credentials`
through Tier 1 (env) → Tier 2 (OS keyring) → Tier 3 dotfile. The
dotfile lives at `~/.agentbundle/credentials.env`. The declared schema
is at `references/creds-schema.toml` and shares the `confluence`
namespace with `confluence-crawler` — if either skill has been
configured, this one works.

| Key | Required | Notes |
|---|---|---|
| `CONFLUENCE_BASE_URL` | yes | Cloud: `https://<site>.atlassian.net/wiki`. Server: `https://confluence.corp.example.com`. |
| `CONFLUENCE_API_TOKEN` | yes | Cloud API token or Server PAT. |
| `CONFLUENCE_EMAIL` | Cloud only | Atlassian account email. |
| `CONFLUENCE_FLAVOR` | no | `cloud` or `server`. Auto-detected from URL host. |

Populate any tier by running `agentbundle creds setup confluence`.

### Security rules (non-negotiable)

- Secrets live only in `~/.agentbundle/credentials.env`
  (mode 0600 on POSIX; DACL-restricted on Windows), the OS keyring,
  or process environment variables.
  **Never** read that file, print it, or echo the token.
- **Never** put the token on the command line. The primitive
  refuses flags like `--token` / `--api-token` / `--bearer` /
  `--pat` / `--password` and exits — do not work around it.
- If `--check` reports missing or invalid creds, tell the user to run
  `agentbundle creds setup confluence` themselves.
  It's interactive — do not run it for them.

### Step 1: Verify the environment

```bash
python -m pip install -r requirements.txt
python scripts/publish_page.py --check
```

- Exit code 0 → authenticated, proceed.
- Exit code 2 → credentials missing or invalid. Tell the user to run
  `agentbundle creds setup confluence` themselves (interactive — they
  run it, not you). Stop here.

### Step 2: Decide how to identify the target page

In order of robustness — use whichever the user gave:

1. **By page ID or URL** (preferred).
   `--page-id 12345` or `--url https://acme.atlassian.net/wiki/spaces/ENG/pages/12345/Some+Title`.
   The page ID is parsed out of the URL. Idempotent.
2. **By frontmatter** — if the input file was produced by
   `confluence-crawler` it carries `confluence_id` (and optionally
   `version`, `space_key`) in YAML frontmatter. `--from-frontmatter`
   reads it. This is the **round-trip case** (crawl → edit → publish
   back).
3. **By space + title** — `--space ENG --title "My Page" [--parent-id 999]`.
   Looks up by title; if found, updates; if not, creates. Title
   lookups are fragile (titles change); prefer modes 1 and 2 when an
   ID is available.

If none of these are supplied, the script exits 2 and asks which. Do
not guess.

### Step 3: Publish

Pick the form that matches the user's request:

```bash
# Update an existing page by ID, from Markdown:
python scripts/publish_page.py --page-id 12345 --input report.md

# Same, but from a Confluence URL:
python scripts/publish_page.py --url 'https://acme.atlassian.net/wiki/spaces/ENG/pages/12345/Foo' --input report.md

# Round-trip case — the markdown came from confluence-crawler:
python scripts/publish_page.py --from-frontmatter --input crawled/eng-handbook.md

# Lookup-then-upsert by title:
python scripts/publish_page.py --space ENG --title "Q2 Report" --parent-id 999 --input report.md

# Plain text body (one paragraph per line):
python scripts/publish_page.py --page-id 12345 --input - --input-format text   # stdin

# Already-rendered storage XHTML:
python scripts/publish_page.py --page-id 12345 --input snippet.xhtml --input-format storage

# Dry-run — print what would be sent, do not call write APIs:
python scripts/publish_page.py --page-id 12345 --input report.md --dry-run
```

Flags:

| Flag | Meaning |
|---|---|
| `--check` | Verify credentials and connectivity, then exit. |
| `--page-id ID` | Update this page (preferred). |
| `--url URL` | Parse page ID from a Confluence URL. |
| `--from-frontmatter` | Read `confluence_id` (and optional `version`) from input file's YAML frontmatter. |
| `--space KEY --title TITLE` | Lookup-then-upsert by title. `--parent-id ID` optional. |
| `--input PATH` or `-` | Source file (or `-` for stdin). Required. |
| `--input-format` | `markdown` (default), `storage`, `text`. |
| `--version-comment TEXT` | Recorded on the new page version. Defaults to a generic message. |
| `--attach PATH` (repeatable) | Upload file as a page attachment; Markdown image refs whose target filename matches an attachment get rewritten to `<ac:image>`. |
| `--label LABEL` (repeatable) | Apply labels after publish. |
| `--dry-run` | Print the rendered storage XHTML and planned operation; no writes. |
| `--insecure` | Disable TLS verification (Server/DC w/ self-signed). User-requested only. |
| `--verbose` | Debug logging. |

### Step 4: Interpret the output

On success the script prints:

```
OK: <create|update> page 12345 (version 8) — https://acme.atlassian.net/wiki/spaces/ENG/pages/12345/Foo
```

On a 409 (someone else edited between read and write) the script
re-reads the page once and retries with the new version number. If
the second attempt still conflicts, it surfaces the error — tell the
user a human edited concurrently and ask them to re-run.

### Behavior notes

- **Update vs create.** `--page-id`/`--url` always updates; never
  creates a new page at a specific ID. `--from-frontmatter` updates the
  page named in the frontmatter. `--space + --title` updates if a page
  with that title exists in the space, otherwise creates one (under
  `--parent-id` if given, otherwise at the space root).
- **Title.** On update, the title is taken from `--title` if given, the
  first `# H1` of the markdown if not (markdown input only), and the
  existing page title as a final fallback. On create, `--title` is
  required (or the first H1 if `--input-format markdown`). Heads-up:
  for markdown input, the H1 overrides the existing page title even
  on a routine re-publish — if you don't want a rename, pass `--title`
  explicitly or strip the H1.
- **Attachment ordering.** On an update of an existing page,
  attachments upload **before** the body update so `<ac:image>`
  references resolve immediately. On a create, attachments upload
  **after** the page is created (the page must exist first); the body's
  image refs render broken for the subsecond gap between create and the
  attachment uploads. **Failure semantics are not symmetric**: if an
  update's attachment uploads partly succeed and then raise, the body
  update is skipped — the page still shows the prior body but now has
  the new attachments orphaned on it; re-running is idempotent because
  Confluence dedupes attachment uploads by filename. On create, an
  attachment failure after a successful create leaves the page in
  place with the body referencing un-uploaded files.
- **Version comment.** Recorded on the new version; helps reviewers see
  why an agent edited. Default: `Published by confluence-publisher`.
- **Markdown conversion.** Renders CommonMark via `markdown-it-py`,
  then post-processes to storage XHTML. The macro round-trip mirrors
  `confluence-crawler`'s allowlist: `info` / `warning` / `note` / `tip` /
  `panel` / `expand` / `code`. Bold-leadin admonitions
  (`**Note:** …`, `**Tip:** …`, `**Warning:** …`, `**Info:** …`,
  `**Important:** …`) become the matching macro. Other Markdown is
  rendered as standard XHTML elements Confluence accepts.
- **Attachments.** `--attach` uploads each file as a page attachment.
  After upload, Markdown image references in the input whose target
  filename matches an attached filename are rewritten to
  `<ac:image><ri:attachment ri:filename="…"/></ac:image>`. Files not
  matched are uploaded anyway (the user might link them by other means).
- **Labels.** Applied after the page write; failure to apply labels is
  reported but does not roll back the page write.
- **Mermaid / PlantUML.** Out of scope. Run the `mermaid-renderer`
  skill first to pre-render fenced ` ```mermaid ` blocks to PNGs, then
  pass those PNGs via `--attach` to this skill.

### Don't

- Don't read `~/.agentbundle/credentials.env` from skill body.
- Don't print or log the token.
- Don't run `agentbundle creds setup confluence` non-interactively or pipe the token into it.
- Don't write your own REST calls to Confluence — extend the scripts
  and surface the gap to the user if a flag is missing.
- Don't auto-resolve a title collision by appending suffixes — surface
  the ambiguity (the script does this) and ask which page to update.
- Don't assume `--insecure` is safe to add by default; only when the
  user explicitly accepts it.
- Don't pass `--force` to bypass a 409 — there is no such flag.
  Concurrent edits need human attention.

### Edge cases

- **Page moved between spaces** between when the user got the URL and
  when you publish: the page ID still resolves; the publish targets
  the page in its current space.
- **Title collision** in lookup mode: if `GET /rest/api/content?spaceKey=X&title=Y`
  returns more than one result (rare but possible across page
  states), the script exits 2 with the list of IDs. Ask the user which
  to target via `--page-id`.
- **Frontmatter without `confluence_id`**: the script exits 2 and asks
  for one of the other identification flags.
- **Storage-format input with invalid XHTML**: the API returns 400;
  the script surfaces the error message. Don't try to fix it
  client-side — ask the user.
- **Network failure mid-publish.** Reads (the version probe) are
  retried by the client. Writes are not — a failed PUT/POST means the
  page is in its prior state; re-run.
- **Large pages.** Confluence soft-caps storage at ~5 MB. Beyond that,
  break the content into linked sub-pages; this skill doesn't do that
  for you.
