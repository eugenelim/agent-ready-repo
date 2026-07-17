# Spec: claude-plugins-publish-and-discover

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Mode:** full (CI/CD structural change, user-facing website surface)
- **Constrained by:** [RFC-0008](../../rfc/0008-claude-plugins-install-route-parity.md)
  (install-marker mechanism — already Shipped);
  [`docs/specs/claude-plugins-install-route/spec.md`](../claude-plugins-install-route/spec.md)
  (Shipped; this spec adds the publish + discover layer on top).

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `agentbundle build` pipeline already produces a complete, installable
`dist/claude-plugins/<pack>/` artifact for every pack. Today that output is
gitignored and never published, so no `claude plugin install <url>` URL exists
for any pack.

This spec closes the gap: publish the built artifacts to a
`claude-plugins-dist` git branch on every push to `main`; add a dedicated
`/plugins/` catalogue page to the marketing website with per-pack install URLs
and site navigation; surface the install URL on each pack detail page; update
the README.

**Scope (in):**
- CI workflow publishing `dist/claude-plugins/` content (including `marketplace.json`) to branch `claude-plugins-dist`, excluding only `catalogue-curation/`
- `/plugins/` page listing all installable packs with `claude plugin install <url>` per pack
- Nav link to `/plugins/` in `SiteNav.astro` and a link from the packs index page
- `claude plugin install <url>` block on each pack detail page (all except `catalogue-curation` — no such page exists in the collection)
- README Quick Start update mentioning `claude plugin install <url>` and linking to `/plugins/` and the raw `marketplace.json`
- Bootstrap the `claude-plugins-dist` branch from the current build

**Scope (out):**
- `agentbundle://` or `claude://` deeplink (deferred per prior decision)
- `uvx agentbundle install` web button (tracked separately)
- APM install-route nudge parity (separate backlog item)
- Changes to agentbundle Python package source or pack source plugin.json files

## Acceptance Criteria

- [x] **AC1** — CI workflow `.github/workflows/publish-claude-plugins.yml` triggers on push to `main` (and `workflow_dispatch`) and publishes `dist/claude-plugins/` content to branch `claude-plugins-dist`, excluding only the `catalogue-curation/` subdirectory. `marketplace.json` IS included at the branch root (with `catalogue-curation` entry stripped).
- [x] **AC2** — The publish step skips committing when `git diff --cached --quiet` (no file-level changes vs previous publish); concurrent runs are cancelled by a `concurrency` group.
- [x] **AC3** — After bootstrap, `https://github.com/eugenelim/agent-ready-repo/tree/claude-plugins-dist/product-engineering` resolves and the directory contains `.claude-plugin/plugin.json` with `hooks.SessionStart`, `.claude-plugin/scripts/install-marker.py`, and `.claude/skills/`. *(Verified via `gh api` during T6 bootstrap.)*
- [x] **AC4** — A `/plugins/` page exists on the marketing site listing every installable pack (all except `catalogue-curation`) with its name, tagline, and a copyable `claude plugin install https://github.com/eugenelim/agent-ready-repo/tree/claude-plugins-dist/<pack>` block.
- [x] **AC5** — `/plugins/` is reachable from primary site navigation (SiteNav desktop + mobile) and from a link on the packs index page.
- [x] **AC6** — Each pack detail page shows a "Claude plugin" install block with the correct URL, rendered below the existing `agentbundle` install block. The block is absent for `catalogue-curation` (that pack has no detail page in the collection, so the guard is publish-side only).
- [x] **AC7** — README Quick Start mentions `claude plugin install <url>` as an alternative, links to the `/plugins/` page for the full inventory, and includes the raw `marketplace.json` URL as the machine-readable catalogue endpoint.
- [x] **AC8** — No new external GitHub Actions introduced beyond `actions/checkout` and `actions/setup-python`.
- [x] **AC9** — Existing CI gates (`build-check`, `pages`, `docs`, `lint-packs`) are unaffected and pass.

## Testing Strategy

- **AC1/AC2:** Goal-based check — workflow runs; `claude-plugins-dist` branch exists; `marketplace.json` present at root; `catalogue-curation/` absent; consecutive identical builds produce no new commit.
- **AC3:** Goal-based check — `git show claude-plugins-dist:product-engineering/.claude-plugin/plugin.json | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'hooks' in d"` exits 0.
- **AC4/AC5/AC6:** Visual/manual QA — `npm run dev` in `web/`; navigate to `/plugins/` (reachable from nav), verify all installable packs listed with correct URLs; navigate to a pack detail page, verify Claude plugin block present.
- **AC7:** Goal-based check — `grep "claude plugin install" README.md` and `grep "marketplace.json" README.md` both match.
- **AC8:** Goal-based check — `grep "uses:" .github/workflows/publish-claude-plugins.yml` returns only `actions/checkout` and `actions/setup-python`.
- **AC9:** Goal-based check — CI passes on PR.

## Boundaries

**Always do:**
- Exclude `catalogue-curation/` from the published branch (operator-only pack).
- Include `marketplace.json` at the branch root (machine-readable index).
- Run `gh auth status` before any direct branch push.

**Never do:**
- Force-push to `main` or any branch-protection-covered branch.
- Modify `packs/<pack>/.claude-plugin/plugin.json` source files (must stay hook-free per build spec AC10 gate 2).
- Add `pluginUrl` to the web content schema (URL is derivable from pack slug).
- Nest `<code>` copy-blocks inside the full-card `<a>` anchor in PackCard (invalid HTML / bad UX).

**Ask first:**
- Before renaming the `claude-plugins-dist` branch once published (would break live install URLs).
- Before adding external GitHub Actions beyond the two already used.

## Assumptions

1. `claude plugin install` resolves GitHub tree URLs of the form `https://github.com/<owner>/<repo>/tree/<branch>/<path>` — documented in Claude Code plugin docs. The slash-free `claude-plugins-dist` branch name removes any ref/path ambiguity in naive parsers.
2. The `agentbundle build` output is content-deterministic across runs on identical input (no timestamps or non-deterministic maps in generated files).
3. The GitHub Actions runner has `contents: write` permission to push to `claude-plugins-dist`.

## Design intent (pre-EXECUTE UX check)

The `/plugins/` page follows the existing dark-hero + surface-section layout pattern used by `/packs/` and `/journeys/`. The per-pack install block reuses the `.install-block` / `.install-block__code` tokens already on the detail page. No new design primitives needed; the `experience-reviewer` pass in REVIEW will verify aesthetic coherence.
