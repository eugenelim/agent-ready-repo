# `atlassian` — guides

Jira, Jira Align, and Confluence over their REST APIs — plus the flow metrics you build on top of them. The pack ships seven skills: `jira` and `jira-align` for issue and portfolio data, `confluence-crawler` and `confluence-publisher` for wiki content, `jira-defect-flow` for end-to-end defect handling, and `flow-metrics` + `ai-adoption-report` for DORA / Flow Framework measurement. The four API-touching skills are credentialed: the secret resolves in-process and never reaches the model.

New here? Read [The `atlassian` pack as a system](explanation/atlassian-pack.md) first — it's the map. Then [work with Jira](how-to/work-with-jira.md) to search and mutate issues.

## How-to

Task-oriented recipes for a problem you already have.

- [Work with Jira](how-to/work-with-jira.md) — JQL search with auto-pagination, plus fetch, create, and update issues through the `jira` skill.
- [Measure flow and DORA metrics](how-to/measure-flow-and-dora-metrics.md) — compute cycle time, throughput, and the rest over a Jira scope, then compare runs into a report.
- [Crawl and publish Confluence](how-to/crawl-and-publish-confluence.md) — mirror a space to Markdown and push Markdown back to a page.

## Reference

Information-oriented, dry and complete.

- [`atlassian` skills](reference/atlassian-skills.md) — every skill in the pack: purpose, primary inputs, outputs, and required credentials.

## Explanation

Understanding-oriented — the *why* behind the design.

- [The `atlassian` pack as a system](explanation/atlassian-pack.md) — how the skills compose over the Atlassian REST APIs and the credentialed-skill auth model.

---

Cross-cutting topics — installing the catalogue, upgrading packs, the adapter support matrix — live in [`../_shared/`](../_shared/). The auth model the credentialed skills share lives in [`../credential-brokers/`](../credential-brokers/).
