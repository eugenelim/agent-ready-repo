---
title: "`atlassian` — guides"
summary: Choose the workflow for tracker intake, story improvement, team status, publishing, flow metrics, or adoption reporting.
pack: atlassian
kind: explanation
---

# `atlassian` — guides

These guides help you read Jira and Confluence, improve stories, and measure delivery from your agent.

## Which mode are you in?

**Repo-first projection:** Product shaping happens in `docs/product/`, and Jira is a shallow copy for reporting. Intents and slices go out, and status never comes back. Apply the [projection contract](../../packs/product-engineering/.apm/skills/intent/references/tracker-projection.md) by hand.

**Tracker-authoritative:** Jira holds the team's real backlog. The workflows read work from Jira and write reviewed story updates back after you approve.

Do not mix the modes: requirements edited in two places diverge silently.

## Start here

- [Measure delivery](how-to/measure-flow-and-dora-metrics.md) — Get cycle time, lead time, and throughput from Jira.

## More

### How-to guides

- [Work with Jira from a conversation](work-with-jira.md) — Do common Jira tasks without writing JQL.
- [Review your team's Jira backlog from start to finish](review-your-team-backlog.md) — Review the backlog and approve story updates.
- [How the Atlassian pack works](how-the-atlassian-pack-works.md) — How the workflows fit together.
- [Authenticate Jira and Confluence with an SSO web session](how-to/authenticate-jira-confluence-with-sso-cookies.md) — Sign in through your SSO web session.
- [Crawl and publish Confluence](how-to/crawl-and-publish-confluence.md) — Mirror a space to Markdown, or publish back.
- [Read Epic outcomes beside delivery in Jira](how-to/read-epic-outcomes-in-jira.md) — See what each Epic delivered.
- [Report AI adoption as a delivery lead](how-to/report-ai-adoption-as-a-delivery-lead.md) — Report AI adoption with its caveats.
- [Atlassian skills reference](atlassian-skills.md) — What each skill reads, writes, and asks you to approve.

### Explanation

- [Measuring AI adoption with flow metrics](explanation/ai-adoption-measurement.md) — What flow comparisons can and cannot show.
