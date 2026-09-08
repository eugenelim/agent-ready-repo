---
title: "`atlassian` — guides"
summary: Choose the workflow for tracker intake, story improvement, team status, publishing, flow metrics, or adoption reporting.
pack: atlassian
kind: explanation
---

# `atlassian` — guides

**Mode: tracker-authoritative.** These guides assume Jira holds the team's real
backlog. If `docs/product/` is canonical and Jira is only for reporting, choose
repo-first projection below.

Jira, Jira Align, and Confluence over their REST APIs, plus flow metrics and
tracker-to-repository intake. `jira-brief-intake` and
`jira-align-brief-intake` now read tracked content into the shared
`work-intake` route; object types and hierarchy remain hints, and intake never
writes back to either tracker. Existing tracker-origin artifacts can later use
reviewed refresh; Jira offers a narrow confirmed coordination write-back path,
while Jira Align remains local-refresh only.

Start a backlog review with:

```text
Show me the Atlas Jira backlog and identify stories that are not ready for engineering.
```

## Which mode are you in?

**Repo-first projection (the product-shaping default):** Use this when product
shaping happens in `docs/product/` and the tracker is a shallow copy for
reporting and team visibility. Feature intents and slices are projected out;
the intent tree stays canonical, status never returns from the tracker, and the
[projection contract](../../packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md)
is applied by hand or through a one-shot export you operate; no exporter or
live API integration ships today.

**Tracker-authoritative:** Use this when Jira holds the team's real backlog.
The Atlassian workflows read work from Jira into the repository and can write
reviewed story improvements back to Jira after explicit approval.

Do not mix the modes. Requirements edited in two places diverge silently.

New here? Read [The `atlassian` pack as a system](how-the-atlassian-pack-works.md) first — it's the map. Then [work with Jira](work-with-jira.md) to search and mutate issues.

Delivery leads looking to measure AI adoption: start with [Measuring AI adoption with flow metrics](explanation/ai-adoption-measurement.md) for the model, then [Report AI adoption as a delivery lead](how-to/report-ai-adoption-as-a-delivery-lead.md) for the step-by-step guide.

## How-to

Task-oriented recipes for a problem you already have.

- [Work with Jira](work-with-jira.md) — JQL search with auto-pagination, plus fetch, create, and update issues through the `jira` skill. Includes the five-question story quality bar for writing actionable stories.
- [Start repository work from Jira or Jira Align](work-with-jira.md#start-repository-work-from-jira-or-jira-align) — read bounded tracker content and review the shared content-based route without changing the tracker.
- [Refresh registered Jira or Jira Align work](work-with-jira.md#refresh-registered-jira-or-jira-align-work) — review a field delta, preserve lifecycle locks, and confirm any supported Jira coordination write separately.
- [Review a Jira backlog for readiness, or get a team status](work-with-jira.md#improve-stories-that-are-not-actionable) — ask *"which stories are not ready for engineering?"* or *"make these tickets actionable"* and `jira-story-triage` reviews and improves them; ask *"what can the team pick up next?"*, *"what is blocked?"*, or *"team status for stand-up"* and `jira-team-status` gives a read-only snapshot with a pick-up hand-off. Neither needs you to name the skill.
- [Measure flow and DORA metrics](how-to/measure-flow-and-dora-metrics.md) — compute cycle time, throughput, and the rest over a Jira scope, then compare runs into a report.
- [Report AI adoption as a delivery lead](how-to/report-ai-adoption-as-a-delivery-lead.md) — set up the labeling convention, run team-level and program-level adoption reports, and convert to a shareable format.
- [Crawl and publish Confluence](how-to/crawl-and-publish-confluence.md) — mirror a space to Markdown and push Markdown back to a page.
- [Authenticate Jira and Confluence with SSO cookies](how-to/authenticate-jira-confluence-with-sso-cookies.md) — for Data Center instances that block API tokens.

## Reference

Information-oriented, dry and complete.

- [`atlassian` skills](atlassian-skills.md) — every skill in the pack: purpose, primary inputs, outputs, and required credentials.

## Explanation

Understanding-oriented — the *why* behind the design.

- [The `atlassian` pack as a system](how-the-atlassian-pack-works.md) — how the skills compose over the Atlassian REST APIs and the credentialed-skill auth model.
- [Measuring AI adoption with flow metrics](explanation/ai-adoption-measurement.md) — the self-certification model, what the metrics tell you, and the limits of Jira-based AI adoption measurement.

---

Cross-cutting topics — installing the catalogue, upgrading packs, the adapter support matrix — live in [`../_shared/`](../_shared/). The auth model the credentialed skills share lives in [`../credential-brokers/`](../credential-brokers/).
