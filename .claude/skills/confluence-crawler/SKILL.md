---
name: confluence-crawler
description: Crawl an authenticated Confluence space (Atlassian Cloud or on-prem Server/Data Center) by page hierarchy and convert each page to clean Markdown with frontmatter. Handles macros, attachments, internal link rewriting, depth limits, and idempotent re-crawling. Use when the user wants to mirror, export, or ingest Confluence content.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
---

# Confluence Crawler

Crawl a Confluence space (Cloud or Server/Data Center) and write each page as Markdown with YAML frontmatter.

## Instructions

You are a Confluence export agent. The heavy lifting — authentication, REST pagination, macro conversion, link rewriting, idempotency — lives in `scripts/`. Do not re-implement any of that logic; just invoke the scripts with the right arguments and report the result.

### Flavor support

The skill works against both:

- **Atlassian Cloud** (`*.atlassian.net`) — Basic auth with email + API token from `id.atlassian.com`. Base URL must include `/wiki` (setup adds it automatically).
- **Confluence Server / Data Center** — Bearer auth with a Personal Access Token from the user's Confluence profile.

Flavor is auto-detected from the base URL. Override via `CONFLUENCE_FLAVOR=cloud|server` if needed.

### Configuration location

Credentials are resolved by `agentbundle.credentials.load_credentials`
through Tier 1 (env) → Tier 2 (OS keyring) → Tier 3 dotfile. The dotfile
lives at `~/.agentbundle/credentials.env`. The declared schema is in
`references/creds-schema.toml`:

| Key | Required | Notes |
|---|---|---|
| `CONFLUENCE_BASE_URL` | yes | Cloud: `https://<site>.atlassian.net/wiki`. Server: `https://confluence.corp.example.com`. |
| `CONFLUENCE_API_TOKEN` | yes | Cloud API token or Server PAT. |
| `CONFLUENCE_EMAIL` | Cloud only | Atlassian account email. |
| `CONFLUENCE_FLAVOR` | no | `cloud` or `server`. Auto-detected from URL host when unset. |

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

Check Python dependencies are installed. If not, install them:

```bash
python -m pip install -r requirements.txt
```

Then verify connectivity:

```bash
python scripts/crawl_space.py --check
```

- Exit code 0 → authenticated, proceed.
- Exit code 2 → credentials missing or invalid. Tell the user to run `agentbundle creds setup confluence` (interactive — they run it, not you). Stop here.

### Step 2: Crawl the space

Invoke the crawler with the user's arguments. Only these flags are supported:

| Flag | Meaning |
|---|---|
| `--space KEY` | Space key, e.g. `ENG`. Required. |
| `--root PAGE_ID` | Start from a specific page (default: space homepage). |
| `--depth N` | Max hierarchy depth from root (default: unlimited). |
| `--output DIR` | Output directory (default: `./confluence-out`). |
| `--force` | Re-fetch and overwrite all pages, ignoring frontmatter version. |
| `--no-attachments` | Skip attachment downloads. |
| `--concurrency N` | Parallel requests (default: 4). |
| `--min-delay-ms N` | Minimum ms between requests (default: 100). |
| `--insecure` | Disable TLS verification. Only if the user explicitly asks. |
| `--verbose` | Debug logging. |

Example:

```bash
python scripts/crawl_space.py --space ENG --depth 3 --output ./out
```

### Step 3: Interpret the output

The script writes:

- `<output>/<slug>.md` per page, flat layout. Each file starts with YAML frontmatter carrying `confluence_id`, `version`, `space_key`, `updated`, `author`, `parent_id`, `labels`, `url`, `slug`.
- `<output>/attachments/<page_id>/<filename>` for downloaded attachments.

The final log line reports `wrote N pages (failed: X, skipped: Y)`. Relay this to the user. If any pages failed, check the log for which IDs — usually permission issues on specific pages.

### Step 4: Re-crawling

The script is idempotent. On re-run:

- It compares each page's current `version.number` against the `version` field in the existing `.md` frontmatter.
- Unchanged pages are skipped.
- Changed pages are re-fetched and overwritten.
- Pass `--force` to bypass the version check and re-fetch everything.

### Behavior notes

- **Depth** is measured in page hierarchy (parent → child), not link hops.
- **Macros** in an allowlist (`code`, `info`, `warning`, `note`, `tip`, `panel`, `expand`, `status`) are converted to Markdown equivalents. Others are replaced with a visible `*[confluence macro not rendered: NAME]*` italic marker so reviewers can spot gaps.
- **Internal links** to pages that were also crawled become relative `.md` paths. Links to pages outside the crawl set remain absolute Confluence URLs.
- **Attachments** are downloaded alongside the referencing page and linked via relative paths.

### Don't

- Don't read `~/.agentbundle/credentials.env` from skill body.
- Don't print or log the PAT.
- Don't run `agentbundle creds setup confluence` non-interactively or pipe the PAT into it.
- Don't write your own REST calls to Confluence — extend the scripts instead, and surface the gap to the user if a flag is missing.
- Don't assume `--insecure` is safe to add by default. Only when the user explicitly says they accept it.

### Edge cases

- **Cloud base URL without `/wiki`**: if the user's config somehow has `https://foo.atlassian.net` without `/wiki`, API calls will 404. The setup script appends it automatically; if the user hand-edited the config, have them re-run setup.
- **Space has no homepage**: the script exits 2 and asks for `--root PAGE_ID`. Relay this to the user.
- **Orphaned pages not in the hierarchy**: not crawled by design. If the user wants them, they need to pass `--root` for each, or request a future "full-space" mode.
- **Very large spaces**: discovery does a full hierarchy walk first (one listing call per page). Expect a minute or two for thousands of pages. Fetch and convert then runs with bounded concurrency.
- **Title changes between runs**: the old `<old-slug>.md` file remains on disk — the new run writes `<new-slug>.md` because slugs derive from the current title. Warn the user that old files may linger and let them clean up.
- **Network failures mid-crawl**: the `.part` tempfile pattern prevents half-written `.md` files. Re-running resumes cleanly.
