# T5 verification — catalogue Wave 6 technical docs IA

Recorded 2026-10-21 on the T1–T4 branch head (887ef7c83).

## 1. Merge base

- `git fetch origin main`; `git merge-base HEAD origin/main`
- Observed: `d714ab829cc4f1121295f67fb55f0ce0ddc37332` (called MB below).

## 2. AC-0005 — rendered link check

- `make site-link-check` (rebuilds the branch site first)
- Observed: exit 0; Astro `289 page(s) built`; summary line
  `rendered-site-links: 36033 links across 624 pages; clean`.

## 3. AC-0007 — page set against the merge base

- Branch: `cd build/docs && find . -name index.html | sort` -> 291 paths.
- `git worktree add /tmp/w6-mb-worktree $MB`; there: `make bootstrap-sites` (exit 0),
  `make site-build` (exit 0, `287 page(s) built`); same `find` -> 289 paths.
- `diff <MB list> <branch list>`:

  ```
  289a290,291
  > ./reference/pack-toml/index.html
  > ./reference/skill-frontmatter/index.html
  ```

- Exactly the two expected pages were added; nothing was removed.
- `git worktree remove --force /tmp/w6-mb-worktree`; `git worktree list` no longer
  lists it and `/tmp/w6-mb-worktree` does not exist.

## 4. AC-0003 — former Author and Catalogue System slugs

- Slugs taken from the `Author` and `Catalogue System` groups of
  `git show $MB:docs-site/astro.config.ts` (lines 204–240): 21.
- Slugs taken from `FORMER_AUTHOR_AND_CATALOGUE_SYSTEM_URLS` in
  `web/src/test/rendered-output.test.ts` (base path and trailing `/` stripped): 21.
- Sorted lists compared with `diff`: no difference. Equal, 21 = 21.

## 5. AC-0016 — 375 px width

- `build/` served statically (`python3 -m http.server 8765` over a temp dir holding the
  symlink `agent-ready-repo -> <repo>/build`); Playwright Chromium, viewport 375 x 812.
- `/agent-ready-repo/docs/reference/pack-toml/`: scrollWidth 375, innerWidth 375.
- `/agent-ready-repo/docs/reference/skill-frontmatter/`: scrollWidth 375, innerWidth 375.
- No horizontal document overflow on either page. (At 1440 x 900 both pages and the
  docs home also measured scrollWidth = innerWidth = 1440.) Server stopped afterwards.

## 6. Walkthrough from the built docs home

Docs home h1: `Intro`. Its link "Build or evaluate a catalogue" goes to
`/agent-ready-repo/docs/guides/_shared/how-to/create-a-catalogue/` (h1 `How a catalogue works`).
The ten Build a Catalogue top-level routes, first link of each, read from the built sidebar:

| # | Sidebar label | Landing URL (under `/agent-ready-repo/docs/`) | h1 |
| --- | --- | --- | --- |
| 1 | Create a catalogue | `guides/_shared/how-to/create-a-catalogue/` | How a catalogue works |
| 2 | Catalogue authoring standards | `guides/_shared/reference/catalogue-authoring-standards/` | Catalogue authoring standards |
| 3 | Author a pack | `guides/_shared/how-to/build-an-org-stack-pack/` | Build a pack |
| 4 | Author a skill | `guides/_shared/how-to/author-a-skill/` | Author a skill |
| 5 | Optional pack integrations | `guides/_shared/reference/catalogue-authoring-standards/#11-optional-pack-integrations` | Catalogue authoring standards |
| 6 | Author a profile | `guides/_shared/how-to/design-a-profile/` | Design a profile |
| 7 | Journey format | `guides/_shared/reference/pack-journey-format/` | Pack JOURNEY.md format |
| 8 | Contract and schema reference | `reference/pack-toml/` | pack.toml fields |
| 9 | Verify and test | `guides/_shared/reference/catalogue-ci-contract/` | Catalogue CI contract |
| 10 | Package and publish | `guides/_shared/reference/catalogue-ci-contract/#agentbundle-catalogue-package` | Catalogue CI contract |

Routes 5 and 10 are fragment links into pages routes 2 and 9 already open, so they share an h1 by design.

## Re-check after rebase onto `73c77ed71` (2026-10-21)

- New merge base: `73c77ed71`. `git diff --name-status --diff-filter=ADR d714ab829 73c77ed71 -- guides packs docs-site` lists one file, `packs/core/tests/skills/close-work/test_closure_typed_discovery_parent.py`, which is not a page; `docs-site/astro.config.ts` is unchanged between the two bases. The merge-base page set and the AC-0003 slug set are therefore unchanged.
- `make site-link-check`: exit 0, `rendered-site-links: 36072 links across 625 pages; clean`.
- Branch page list: 291 `index.html` paths, identical to the pre-rebase list (289 base + `reference/pack-toml/` + `reference/skill-frontmatter/`).
- `npm test --prefix web`: 24 files, 238 tests passed.
