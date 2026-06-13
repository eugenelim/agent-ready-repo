# Crawl and publish Confluence

Mirror a Confluence space to Markdown with [`confluence-crawler`](../../../../packs/atlassian/.apm/skills/confluence-crawler/), and push Markdown back to a page with [`confluence-publisher`](../../../../packs/atlassian/.apm/skills/confluence-publisher/). The two skills are opposite directions over the same `confluence` credential namespace — configure either and both work.

## Before you start

Both skills are credentialed. Verify connectivity:

```bash
python scripts/crawl_space.py --check     # crawler
python scripts/publish_page.py --check    # publisher
```

Exit 0 means proceed. Exit 2 means run `credential-setup` yourself to enter `CONFLUENCE_BASE_URL`, `CONFLUENCE_API_TOKEN`, and (on Cloud) `CONFLUENCE_EMAIL`. On Cloud the base URL must end in `/wiki` — setup adds it. The model never sees the token — see [Credentialed skills](../../credential-brokers/explanation/credentialed-skills.md).

## Crawl a space to Markdown

Point the crawler at a space key. It walks the page hierarchy and writes one Markdown file per page:

```bash
python scripts/crawl_space.py --space ENG --depth 3 --output ./out
```

`--depth` is measured in page hierarchy (parent to child), not link hops, and defaults to unlimited. The crawl starts at the space homepage unless you pass `--root PAGE_ID`.

The output:

- `<output>/<slug>.md` per page, flat layout. Each file opens with YAML frontmatter carrying `confluence_id`, `version`, `space_key`, `updated`, `author`, `parent_id`, `labels`, `url`, and `slug`.
- `<output>/attachments/<page_id>/<filename>` for downloaded attachments. Pass `--no-attachments` to skip them.

The final log line reports `wrote N pages (failed: X, skipped: Y)`. If pages failed, the log names the IDs — usually permission issues on specific pages.

Macros in an allowlist (`code`, `info`, `warning`, `note`, `tip`, `panel`, `expand`, `status`) convert to Markdown. Others become a visible `*[confluence macro not rendered: NAME]*` marker so you can spot gaps.

## Re-crawl incrementally

The crawler is idempotent. On re-run it compares each page's current version against the `version` in the existing `.md` frontmatter, skips unchanged pages, and re-fetches changed ones. Pass `--force` to re-fetch everything regardless.

## Publish Markdown to a page

The publisher creates a new page or updates an existing one. Identify the target the most robust way you can:

```bash
# By page ID (preferred, idempotent):
python scripts/publish_page.py --page-id 12345 --input report.md

# By Confluence URL (the page ID is parsed out):
python scripts/publish_page.py \
  --url 'https://acme.atlassian.net/wiki/spaces/ENG/pages/12345/Foo' \
  --input report.md

# Lookup-then-upsert by title (updates if found, creates if not):
python scripts/publish_page.py --space ENG --title "Q2 Report" \
  --parent-id 999 --input report.md
```

Input defaults to Markdown. Pass `--input-format storage` for raw Confluence storage XHTML or `--input-format text` for plain text, and `--input -` to read from stdin. `--attach PATH` (repeatable) uploads a file as an attachment; Markdown image references whose filename matches an attachment get rewritten to `<ac:image>`. `--label LABEL` (repeatable) applies labels after the write.

Preview before writing with `--dry-run` — it prints the rendered storage XHTML and planned operation, and calls no write APIs:

```bash
python scripts/publish_page.py --page-id 12345 --input report.md --dry-run
```

On success the script prints the operation, page ID, new version, and URL.

## Round-trip: crawl, edit, publish back

A crawled file carries `confluence_id` in its frontmatter, so the publisher can target the same page without you supplying an ID:

```bash
python scripts/publish_page.py --from-frontmatter --input out/eng-handbook.md
```

Edit the crawled Markdown, then publish it straight back.

## Pitfalls

- **The H1 overrides the page title** on Markdown input, even on a routine re-publish. Pass `--title` explicitly or strip the H1 if you don't want a rename.
- **A 409 conflict** (someone edited between read and write) triggers one automatic re-read and retry. A second conflict surfaces the error — a human edited concurrently; re-run. There is no `--force` to bypass it.
- **Mermaid and PlantUML are out of scope** for the publisher. Pre-render fenced blocks to PNGs with the `mermaid-renderer` skill, then pass them via `--attach`.
- **A title collision in lookup mode** exits 2 with the candidate IDs. Re-target with `--page-id`.

For the full flag surface of both skills, see the [`atlassian` skills reference](../reference/atlassian-skills.md).
