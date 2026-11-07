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

- [Measure delivery](how-to/measure-flow-and-dora-metrics.md) — Get cycle time, lead time, throughput, and other delivery measures from your Jira history, and compare two periods.

## More

### How-to guides

- [Work with Jira from a conversation](work-with-jira.md) — Common Jira tasks — from reviewing the whole team backlog to applying approved story updates — without writing JQL or selecting skills manually.
- [Review your team's Jira backlog from start to finish](review-your-team-backlog.md) — A complete walkthrough — see what the team can work on, improve weak stories, approve targeted Jira updates, and produce a stand-up summary without opening a browser.
- [How the Atlassian pack works](how-the-atlassian-pack-works.md) — The mental model behind the Atlassian pack — how focused workflows compose into a safe, readable team backlog experience without you selecting skills manually.
- [Authenticate Jira and Confluence with an SSO web session](how-to/authenticate-jira-confluence-with-sso-cookies.md) — Configure read-only Jira and Confluence skills to authenticate through a securely stored corporate SSO browser session.
- [Crawl and publish Confluence](how-to/crawl-and-publish-confluence.md) — Mirror a documentation space to Markdown, publish reviewed Markdown back, or complete a controlled round trip.
- [Read Epic outcomes beside delivery in Jira](how-to/read-epic-outcomes-in-jira.md) — Group a Jira project's work by Epic and see, for each one, what it delivered beside what that work was meant to change.
- [Report AI adoption as a delivery lead](how-to/report-ai-adoption-as-a-delivery-lead.md) — Turn consistent cohort or before-and-after flow measurements into a caveated stakeholder-ready adoption report.
- [Atlassian skills reference](atlassian-skills.md) — Exact read, write, coverage, limit, and approval contracts for every skill in the Atlassian pack.

### Explanation

- [Measuring AI adoption with flow metrics](explanation/ai-adoption-measurement.md) — Understand what delivery-flow comparisons can and cannot establish about AI-assisted engineering adoption.
