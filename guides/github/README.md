---
title: "`github` — guides"
summary: Bring GitHub issues and milestones into your repository as planned work, read-only.
pack: github
kind: explanation
---

# `github` — guides

These guides help you bring GitHub issues and milestones into the repository as specs or briefs.

## Which mode are you in?

**Repo-first projection:** Product shaping happens in `docs/product/`, and GitHub is a shallow copy for reporting. Intents and slices go out, and status never comes back. Apply the [projection contract](../../packs/product-engineering/.apm/skills/intent/references/tracker-projection.md) by hand.

**Tracker-authoritative:** GitHub holds the team's real backlog. Intake reads Issues and Milestones. A reviewed refresh adds only a comment, label, link, or closure.

Do not mix the modes: requirements edited in two places diverge silently.

## Start here

- [Intake GitHub work into the repository](how-to/intake-a-github-milestone-as-a-brief.md) — Read selected issues or a milestone and route them through `work-intake`, with no write back.
- [Connect your tracker](../_shared/how-to/choose-a-tracker-integration.md) — Compare GitHub, Linear, and Jira intake.
