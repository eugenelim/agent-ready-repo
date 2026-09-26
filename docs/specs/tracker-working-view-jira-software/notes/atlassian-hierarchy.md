# Atlassian work-type hierarchy — source extract

Read 2026-09-24 from Atlassian's own documentation,
[Configure the work type hierarchy](https://support.atlassian.com/jira-cloud-administration/docs/configure-the-issue-type-hierarchy/).
Extracted because survey F6 previously recorded Jira's hierarchy as unverified,
and this spec's acceptance basis depends on it.

## What the page states

- **Three levels by default.** Jira provides "three levels of work type
  hierarchy: a level for larger pieces of work (level 1, by default called
  **Epic**), a level for standard work items (level 0, called **Story**), and a
  level for smaller pieces of work (level -1, called **Subtask**)."
- **Both extensions are gated behind a paid plan.** Adding work types to the
  Epic level requires Jira Cloud Premium or Enterprise; creating and managing
  additional custom levels requires the same.
- **New levels extend upward.** "A new level will be created at the top of the
  work type hierarchy."
- **No maximum is stated.**
- **Terminology.** The page says "work type" throughout, not "issue type".

## Why each fact matters to this spec

The three-level default is the hierarchy a projection renders into on a
non-paid tier, so it bounds what the profile rows may assume. The paid-plan gate
means a mapping that needs a rung above Epic is not universally available.
Where it is absent the rung must **collapse** onto labels or an equivalent
carrier under ADR-0127 D3, never truncate — D3 names dropping a rung as out of
contract. Upward extension matters because a new Jira level lands above Epic, so a
canonical rung mapped there is reachable only on Premium or Enterprise. And the vocabulary shift
scopes to Jira: rows describing **Jira** objects as "Issue" use a term Atlassian
has moved off. It says nothing about Linear's `Issue`, which is Linear's own
current object name.

## What this does not settle

The Jira Epic to Jira Align **Feature** rename is a separate claim on a
different page and remains unverified; survey F6 carries it as open, and the
Jira Align slice inherits it.
