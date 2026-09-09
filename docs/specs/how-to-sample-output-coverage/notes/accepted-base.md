# Accepted base: how-to sample-output coverage

Captured 2026-09-09 with:

```text
python3 tools/audit-guide-affordances.py --ledger <temporary-path>
```

This ledger freezes every in-scope `kind: how-to` guide that already carried a
literal chat input (`A`) but lacked a representative sample output (`C`). Corpus
additions do not expand the slice.

Parent S5 boundary: “Every current in-scope how-to target shows a
source-grounded representative response; reference and explanation pages and
related-intent surfaces remain excluded.” Every path below inherits the
audit-verified tuple `kind: how-to`, A present, C absent.

- `guides/_shared/how-to/choose-a-tracker-integration.md`
- `guides/_shared/how-to/install-the-whole-lifecycle.md`
- `guides/_shared/how-to/project-slices-to-a-tracker.md`
- `guides/architect/how-to/assess-a-repository.md`
- `guides/architect/how-to/shape-an-architecture-concept.md`
- `guides/atlassian/how-to/crawl-and-publish-confluence.md`
- `guides/atlassian/how-to/measure-flow-and-dora-metrics.md`
- `guides/atlassian/work-with-jira.md`
- `guides/contracts/how-to/author-an-event-contract.md`
- `guides/contracts/how-to/generate-an-api-contract.md`
- `guides/core/how-to/bug-fix.md`
- `guides/core/how-to/capture-work.md`
- `guides/core/how-to/close-and-disposition-work.md`
- `guides/core/how-to/distill-captured-project-knowledge.md`
- `guides/core/how-to/intake-an-external-brief.md`
- `guides/core/how-to/migrate-capture-work.md`
- `guides/core/how-to/orient-at-session-start.md`
- `guides/core/how-to/receive-a-product-brief-and-decompose-it-into-specs.md`
- `guides/core/how-to/record-your-foundation-during-inception.md`
- `guides/core/how-to/review-someone-elses-pr.md`
- `guides/core/how-to/start-a-project.md`
- `guides/core/how-to/start-or-remember-work.md`
- `guides/desk-research/how-to/research-pipelines.md`
- `guides/github/how-to/intake-a-github-milestone-as-a-brief.md`
- `guides/governance-extras/how-to/extension-contract.md`
- `guides/linear/how-to/linear-brief-intake-and-sync.md`
- `guides/monorepo-extras/how-to/scaffold-a-new-package.md`
- `guides/product-engineering/how-to/frame-a-product-vision.md`
- `guides/product-engineering/how-to/generate-solution-options.md`
- `guides/product-engineering/how-to/hand-an-intent-to-build.md`
- `guides/product-engineering/how-to/identify-opportunities.md`
- `guides/product-engineering/how-to/map-capabilities.md`
- `guides/product-engineering/how-to/run-a-discovery.md`
- `guides/product-engineering/how-to/shape-a-feature-intent.md`
- `guides/product-engineering/how-to/shape-a-product-strategy.md`
- `guides/product-engineering/how-to/write-product-microcopy.md`
- `guides/product-strategy/how-to/cascade-okrs-into-the-shaping-queue.md`
- `guides/product-strategy/how-to/run-a-market-and-competitive-analysis.md`
- `guides/product-strategy/how-to/set-ux-and-content-strategy.md`
- `guides/release-engineering/how-to/run-a-release.md`

How-tos without a literal chat input are not silently pulled into this output
slice; their invocation gap belongs to the invocation/outcome spec or later
intake. `guides/experience-design/**` and net-new related-intent content remain
excluded.
