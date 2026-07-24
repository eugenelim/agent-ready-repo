# `atlassian` — guides

Jira, Jira Align, and Confluence over their REST APIs — plus the flow metrics and intake workflows you build on top of them. The pack ships `jira` and `jira-align` for issue and portfolio data, `confluence-crawler` and `confluence-publisher` for wiki content, `jira-defect-flow` for end-to-end defect handling, `jira-brief-intake` to turn a Jira epic into a product brief, `jira-align-brief-intake` to turn a Jira Align Feature into a product brief, `jira-story-triage` to review a backlog for readiness and improve weak items, `jira-team-status` for a read-only team status snapshot (ready to pull / blocked / unassigned / in progress / needs detail) and a pick-up hand-off, and `flow-metrics` + `ai-adoption-report` for DORA / Flow Framework measurement. The four API-touching skills are credentialed: the secret resolves in-process and never reaches the model.

New here? Read [The `atlassian` pack as a system](explanation/atlassian-pack.md) first — it's the map. Then [work with Jira](how-to/work-with-jira.md) to search and mutate issues.

Delivery leads looking to measure AI adoption: start with [Measuring AI adoption with flow metrics](explanation/ai-adoption-measurement.md) for the model, then [Report AI adoption as a delivery lead](how-to/report-ai-adoption-as-a-delivery-lead.md) for the step-by-step guide.

## How-to

Task-oriented recipes for a problem you already have.

- [Work with Jira](how-to/work-with-jira.md) — JQL search with auto-pagination, plus fetch, create, and update issues through the `jira` skill. Includes the five-question story quality bar for writing actionable stories.
- [Review a Jira backlog for readiness, or get a team status](how-to/work-with-jira.md#improve-stories-that-are-not-actionable) — ask *"which stories are not ready for engineering?"* or *"make these tickets actionable"* and `jira-story-triage` reviews and improves them; ask *"what can the team pick up next?"*, *"what is blocked?"*, or *"team status for stand-up"* and `jira-team-status` gives a read-only snapshot with a pick-up hand-off. Neither needs you to name the skill.
- [Measure flow and DORA metrics](how-to/measure-flow-and-dora-metrics.md) — compute cycle time, throughput, and the rest over a Jira scope, then compare runs into a report.
- [Report AI adoption as a delivery lead](how-to/report-ai-adoption-as-a-delivery-lead.md) — set up the labeling convention, run team-level and program-level adoption reports, and convert to a shareable format.
- [Crawl and publish Confluence](how-to/crawl-and-publish-confluence.md) — mirror a space to Markdown and push Markdown back to a page.
- [Authenticate Jira and Confluence with SSO cookies](how-to/authenticate-jira-confluence-with-sso-cookies.md) — for Data Center instances that block API tokens.

## Reference

Information-oriented, dry and complete.

- [`atlassian` skills](reference/atlassian-skills.md) — every skill in the pack: purpose, primary inputs, outputs, and required credentials.

## Explanation

Understanding-oriented — the *why* behind the design.

- [The `atlassian` pack as a system](explanation/atlassian-pack.md) — how the skills compose over the Atlassian REST APIs and the credentialed-skill auth model.
- [Measuring AI adoption with flow metrics](explanation/ai-adoption-measurement.md) — the self-certification model, what the metrics tell you, and the limits of Jira-based AI adoption measurement.

---

Cross-cutting topics — installing the catalogue, upgrading packs, the adapter support matrix — live in [`../_shared/`](../_shared/). The auth model the credentialed skills share lives in [`../credential-brokers/`](../credential-brokers/).
