# Plan: docs-cli-tab

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `guides/AGENTS.md`; `contracts/guide.schema.json`
  (frontmatter, `aliases`); `tools/build-site.py` alias redirect stubs.

## Approach

Merge by reader task, not by source page. Each new page opens with one sentence
saying what the reader can do, then commands, then sections the "On this page"
list can navigate. Old pages go; their slugs move into the absorbing page's
`aliases:` list, which the generator turns into redirect stubs.

## Tasks

### T1: The four CLI pages build, the CLI tab lists them, and every old URL redirects

**Depends on:** none
**Touches:** `guides/_shared/**`, `docs-site/astro.config.ts`, `docs-site/src/content/docs/**`, `site.toml`, `web/src/**`, `llms.txt`, `README.md`, `packs/*/README.md`, tests that pin moved URLs

**Tests:** goal-based — the gates in the spec's Testing Strategy; an AC3 command-coverage script over the deleted pages from git history.

**Done when:** all gates pass and the AC3 script reports no missing command.

## Changelog

- 2026-10-15: spec approved by eugenelim (delegated in session: "no need to ask, keep going")
- 2026-10-15: plan approved by eugenelim (same delegation)
