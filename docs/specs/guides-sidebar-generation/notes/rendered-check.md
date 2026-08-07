# Rendered check — T9

Observation record for AC14. Re-rendered at HEAD after the review fixes;
the defect section below records what changed and why.

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

## Defects found and fixed during review

**Five identical "Overview" siblings.** The first rendered pass shipped
`guides/_shared` plus its four kind-directory READMEs all labelled "Overview" —
none was in the pre-change tree, so none was in the frozen baseline, and all
fell back to the same constant. Neither AC9 (baseline pairs) nor AC2 (slugs)
could see it.

The first fix gave each its bucket's label, which traded five identical labels
for three duplicated *pairs*: a page named "How-to" beside the "How-to" bucket.
The test written to prevent that compared only slug-bearing items, so it was
blind to a page colliding with a bucket.

The actual fix was to exclude them. All four are section-authoring templates —
`guides/_shared/how-to/README.md` opens *"Writing a how-to"* — addressed to
whoever writes the guides, not to the adopter this tree serves. None was in the
pre-change sidebar, so excluding them preserves the status quo and including
them was the change. They remain mirrored: `build/docs/guides/_shared/how-to/`
renders and is reachable by URL.

Re-rendered at HEAD after the fix:

```
Cross-cutting
  Overview
  How-to  (18 pages)
  Reference  (10 pages)
  Explanation  (6 pages)
```

**Tests that documented rather than constrained.** Two reviewers independently
showed by mutation that deleting the eligibility rule, or the duplicate-slug
tie-break, left every test green while the real tree regressed. Real-tree
invariants were added — the nav-ineligible set pinned against an independent
expectation, sibling-label uniqueness asserted recursively over every generated
group, every `guides/` directory required to be declared, and the `atlassian`
cross-kind run asserted as a witness this PR did not author. Both mutations now
fail.
