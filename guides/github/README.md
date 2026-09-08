---
title: "`github` — guides"
summary: Understand the fixed-host, read-only intake workflow that turns selected repository work into canonical local work.
pack: github
kind: explanation
---

# `github` — guides

**Mode: tracker-authoritative.** These guides assume GitHub holds the team's
real backlog. If `docs/product/` is canonical and GitHub is only for reporting,
choose repo-first projection below.

GitHub integration for this catalogue. The pack ships two connected skills:

- **`github-brief-intake`** — read a GitHub Issue, Milestone, or selection via
  trusted fixed-host `gh` commands, normalize it, and hand it to `work-intake`.
- **`github-refresh`** — compare an existing tracker-origin artifact and, after
  separate confirmation, perform only the declared coordination action.

Start read-only intake with:

```text
Intake the release-planning milestone from example-org/example-repo as repository work without changing GitHub.
```

## Which mode are you in?

**Repo-first projection (the product-shaping default):** Use this when product
shaping happens in `docs/product/` and GitHub is a shallow copy for reporting
and team visibility. Feature intents and slices are projected out; the intent
tree stays canonical, status never returns from GitHub, and the [projection contract](../../packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md)
is applied by hand or through a one-shot export you operate; no exporter or
live API integration ships today.

**Tracker-authoritative:** Use this when GitHub holds the team's real backlog.
Intake reads Issues and Milestones into the repository without changing
GitHub. Reviewed refresh can add only a comment, display-status label, trace
link, pull-request link, or closure after separate confirmation; it cannot
create an Issue or rewrite an Issue body.

Do not mix the modes. Requirements edited in two places diverge silently.

New here? Start with the how-to guide below.

## How-to

Task-oriented recipes for a problem you already have.

- [Intake GitHub work into the repository](how-to/intake-a-github-milestone-as-a-brief.md) — acquire read-only, review the content-based route, and continue with the selected processor.

---

Cross-cutting topics — installing the catalogue, upgrading packs, the adapter support matrix — live in [`../_shared/`](../_shared/).
