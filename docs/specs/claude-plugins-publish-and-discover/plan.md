# Plan: claude-plugins-publish-and-discover

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Constraints

- No new external GitHub Actions; no changes to pack source files.
- `catalogue-curation` excluded from publish + UI (directory excluded; also stripped from `marketplace.json`).
- `claude-plugins-dist` is a dist branch — replaced atomically, not accumulated.

## Declined patterns

- Tempted to add `pluginUrl` field to each content file — declining, the URL is
  derivable from pack name (`entry.id`) and adding it to 14 content files is
  maintenance surface for no gain.
- Tempted to use `peaceiris/actions-gh-pages` for the publish step — declining,
  adds an external dependency (AGENTS.md risk trigger).
- Tempted to inline plugin install commands on each PackCard — declining, the full
  card is wrapped in an `<a>` anchor; nesting copy-blocks inside it is invalid HTML
  and broken UX. A dedicated `/plugins/` page handles this cleanly instead.
- Tempted to add a `claude://` deeplink — declining, deferred per prior decision
  (agentbundle:// needs a registered OS protocol handler).

## Tasks

### T1 — CI workflow: publish built output to `claude-plugins-dist`

**Depends on:** none
**Verification:** goal-based check
**Done when:** push to main triggers the workflow; `claude-plugins-dist` branch exists with correct structure (`.claude-plugin/plugin.json`, `.claude/skills/`, `.claude-plugin/scripts/install-marker.py`); `catalogue-curation/` directory absent from the branch; `marketplace.json` present at branch root with `catalogue-curation` entry stripped.

**Approach:**
- Create `.github/workflows/publish-claude-plugins.yml`
- Trigger: `push: branches: [main]`; `workflow_dispatch` for manual runs
- Steps: checkout (full), setup-python, install agentbundle dev, `make build`, publish script
- Publish step: worktree approach against `claude-plugins-dist`; skips commit if no changes; excludes `catalogue-curation/` directory; writes filtered `marketplace.json` (catalogue-curation entry stripped) via `_write_filtered_marketplace()`
- Permissions: `contents: write`

### T2 — Web: Claude plugin install block on pack detail page

**Depends on:** none (URL pattern is fixed; branch existence is a separate concern)
**Verification:** visual/manual QA (`npm run dev` in `web/`)
**Done when:** pack detail page for `experience` shows "Via Claude Code / Claude Desktop" install block with correct URL below the agentbundle route.

**Approach:**
- Edit `web/src/pages/packs/[pack].astro`
- Derive `packSlug = entry.id.replace(/\.md$/, '')`
- Add second install route below the agentbundle block
- URL: `https://github.com/eugenelim/agent-ready-repo/tree/claude-plugins-dist/${packSlug}`
- Uses dark `.install-block` (dark bg via hero tokens) with flex row + copy button

### T3 — Web: Dedicated `/plugins/` catalogue page

**Depends on:** none
**Verification:** visual/manual QA (`npm run dev`, navigate to `/plugins/`)
**Done when:** `/plugins/` page lists every installable pack (excluding `catalogue-curation`) with name, tagline, skills count, "View pack →" link, and a dark install block with copyable `claude plugin install` command and copy button.

**Approach:**
- Create `web/src/pages/plugins/index.astro`
- Filter out `catalogue-curation`; sort three loops first then alpha
- Dark hero zone (eyebrow, display heading, body, pack count + marketplace link)
- Plugin grid: cards with `.plugin-install` dark footer zone, clipboard copy button with 2s "Copied!" feedback

### T4 — Web: SiteNav link + packs index banner

**Depends on:** none
**Verification:** visual/manual QA
**Done when:** "Plugins" appears in desktop + mobile nav between Packs and Journeys; packs/index.astro shows an amber-accent banner linking to `/plugins/`.

**Approach:**
- Add `{ label: 'Plugins', href: withBase('/plugins/') }` to SiteNav `links` array
- Add `.packs__plugin-banner` div in `packs/index.astro` above the grid

### T5 — README: mention claude plugin install route + marketplace URL

**Depends on:** none
**Verification:** goal-based check — `grep "claude plugin install" README.md`
**Done when:** README Quick Start section mentions `claude plugin install <url>` as primary route (above agentbundle CLI), links to `/plugins/` for inventory, includes raw `marketplace.json` URL.

**Approach:**
- Add "Install via Claude Code / Claude Desktop" block above agentbundle CLI section
- Add machine-readable catalogue URL at end of Quick Start

### T6 — Bootstrap `claude-plugins-dist` branch

**Depends on:** T1
**Verification:** goal-based check — `git ls-remote --heads origin claude-plugins-dist` returns branch; `gh api "repos/eugenelim/agent-ready-repo/contents/product-engineering/.claude-plugin/plugin.json?ref=claude-plugins-dist"` returns JSON with `hooks.SessionStart`
**Done when:** branch exists on remote with current build output; `catalogue-curation/` absent; `marketplace.json` present with `catalogue-curation` entry stripped.

**Approach:**
- Build into `dist/` via `PYTHONPATH=packages/agentbundle python3 -m agentbundle.build build --packs-dir packs --output-dir dist`
- Run `python3 tools/publish-claude-plugins.py` (orphan branch path)
- Verify: `gh api` call confirms `hooks.SessionStart` in `product-engineering/.claude-plugin/plugin.json`
