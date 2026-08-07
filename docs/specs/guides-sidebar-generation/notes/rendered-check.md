# Rendered check — T9

Observation record for AC14. Run on 2026-08-07 against the working tree at
commit `81744e5c1`.

## Build

```
python3 tools/build-site.py          # wrote sidebar-config.json + mirrored 185 guides
npm ci --prefix docs-site            # node_modules was absent
npm run build --prefix docs-site     # exit 0
```

`214 page(s) built in 36.75s`, pagefind indexed 214 HTML files.

**Re-run after review (2026-08-07).** The first pass skipped the `web/` build,
which is the load-bearing first step. Adversarial review flagged that as not
satisfying AC14, so the full sequence was re-run end to end:

```
npm run build --prefix web       # 45 pages
python3 tools/build-site.py
npm run build --prefix docs-site # 214 pages
```

Both `build/index.html` and `build/docs/index.html` are present, so the
documented ordering was exercised as CI runs it.

## Inspected

**Guide group presence and order.** Groups render under "Guides" as a flat list
of pack groups, in `site.toml` `[[guide_groups]]` order. Kind buckets inside
each render in the canonical sequence — verified on the first four groups:

```
Guides
  The Build Loop (core)   → Tutorials, How-to, Reference, Explanation
  Product Strategy        → Tutorials, How-to, Reference, Explanation
  Product Discovery       → Tutorials, How-to, Reference, Explanation
  Release Engineering     → …
```

None of the six `site.toml` `[[groups]]` super-group labels appears inside
Guides — nesting stayed at one group level, as AC8 requires.

**The IaC arc renders 1–3** (AC13, first half):

```
Overview                             → /docs/guides/iac-terraform/
Infrastructure in the release loop   → …/explanation/infrastructure-in-the-release-loop/
Deciding before generating           → …/explanation/deciding-before-generating/
What the preview cannot tell you     → …/explanation/what-the-preview-cannot-tell-you/
```

Reading order, not alphabetical. Alphabetical would have led with "Deciding
before generating".

**The atlassian sequence renders as a flat cross-kind run** (AC13, second half):

```
Overview
Review Your Team Backlog     order 1  (tutorial)
Work with Jira               order 2  (how-to)
Atlassian Skills             order 3  (reference)
How the Atlassian Pack Works order 4  (explanation)
Authenticate with SSO        ─┐
Crawl Confluence              │ unordered, in kind buckets
DORA Metrics                  │
Report AI Adoption            │
Measuring AI Adoption        ─┘
```

This is the post-change shape the spec predicted, not the hand-placed one: the
four ordered pages are hoisted into a run ahead of the buckets rather than
sitting one per bucket. `Work with Jira` kept its baseline label rather than
adopting its frontmatter `title:` of "Work with Jira from a conversation" —
the inverted precedence chain doing what it was inverted for.

**Previously-absent pages now render** (AC9's converse):

```
OK  guides/iac-terraform/explanation/deciding-before-generating
OK  guides/_shared/explanation/pack-workflow-design      (a _shared page)
OK  guides/github                                        (newly declared group)
OK  guides/linear                                        (newly declared group)
OK  guides/_reference/catalogue-format                   (kind-less, non-index)
```

`_reference/catalogue-format` is the file that fell through every ordering rule
before rule 3 was added. It renders as a direct group item.

**`guides/AGENTS.md`** renders at `/docs/guides/agents/` and does **not** appear
in the sidebar — the declared exception from § Intent behaving as specified:
reachable by URL, absent from reader navigation.

## Not inspected

Out of scope for this spec and unchanged by it: styling, contrast, mobile
viewport, search behaviour, and the marketing site at `/`.

## Defect found and fixed during review

The first rendered pass shipped five items labelled "Overview" in the
Cross-cutting group — `guides/_shared` plus its four kind-directory READMEs,
none of which were in the pre-change tree and so none in the frozen baseline.
Filename derivation would have read "Readme", so the constant "Overview" was
the fallback, and four indistinguishable siblings was the result. Neither AC9
(baseline pairs only) nor AC2 (slugs only) could see it.

A kind-directory index now takes its bucket's label. Re-verified in the built
output:

```
Cross-cutting
  Overview      → /docs/guides/_shared/
  Explanation   → /docs/guides/_shared/explanation/
  How-to        → /docs/guides/_shared/how-to/
  Reference     → /docs/guides/_shared/reference/
  Tutorials     → /docs/guides/_shared/tutorials/
```
