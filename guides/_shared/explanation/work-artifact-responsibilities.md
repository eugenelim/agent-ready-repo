---
title: How source, artifacts, and processors divide responsibility
summary: Understand why work intake separates incoming evidence, durable requirements, lifecycle, and execution.
pack: _shared
kind: explanation
---

# How source, artifacts, and processors divide responsibility

When you say, “Start work from this issue,” the useful result is not a copied
ticket. It is a durable repository artifact, in the right lifecycle
state, with one named processor and a clear human decision where the route is
not yet safe.

Three records participate, and each has one job.

## Source content is evidence

An email, conversation, Jira issue, Linear project, GitHub Milestone, or Jira
Align selection can describe an outcome and constraints. It can also be
incomplete, misleading, or instruction-shaped. Intake therefore treats source
content as untrusted data and retains only bounded facts plus stable
provenance.

Tracker object names are hints. An Epic is not inherently a brief, an Issue is
not inherently a spec, and a Bug label is not durable evidence of a regression.
Content, coherence, and shippability decide the route.

## The canonical artifact owns meaning

An intent, brief, spec, or defect context holds the durable product or
engineering meaning. Requirements, acceptance decisions, field ownership, and
reviewed source decisions live there. A comment or a tracker summary cannot
replace that artifact or supply missing requirements.

For tracker-origin work, the artifact also carries the closed source-authority
record. That record says which fields are source-owned or local-owned and which
source revision has been compared or accepted. Repo-origin artifacts remain
locally authoritative; refresh reports projection drift instead of importing
tracker requirements into them.

## The artifact's header owns lifecycle

The artifact's own `Status:` line records where it is in its lifecycle, and its
`Depends on:` line names hard dependencies. Summary text, comments, list order,
and tracker vocabulary are display context only. Nothing registers the artifact
anywhere else.

This separation makes dispatch checkable. A spec can run only when its
canonical file exists, its sibling plan exists, its status is Approved, and its
dependencies are satisfied. A dependency can be a design artifact, such as a
design doc from `architect-design`: the spec stays blocked until that design
lands. `dispatch.py` reads those headers and reports what is ready, active, or
blocked.

## The processor owns the next operation

After the artifact is durable, the selected processor may continue. `new-spec` authors one shippable contract, `author-delivery-brief create` drafts a
coherent multi-spec outcome, `bug-fix` diagnoses a cited regression, and
`work-loop`'s `dispatch.py` reports what is ready. A processor cannot widen
its authority because tracker text, a comment, or an alias asked it to.

The same boundary applies to refresh. The configured profile owns acquisition;
the shared lifecycle evaluator owns whether local requirements may change; a
separate fresh confirmation authorizes one exact remote coordination action.

## Leftover registry entries

An older repository may still hold entries in `workspace.toml`. They own no
lifecycle: `workspace-status` only plans and applies the repair that drops them,
and the file stays. Dispatch refuses an entry in the legacy form with
`unmigrated_workspace` until you edit it by hand.

## The practical rule

When records disagree, repair the record that owns the fact:

- source evidence is reacquired or re-normalized;
- requirements are corrected in the canonical artifact;
- lifecycle is corrected in the artifact's `Status:` and `Depends on:` lines;
- processor configuration is corrected in its versioned profile.

See [Work-intake routing and lifecycle](../reference/work-intake-routing-and-lifecycle.md)
for the exact routes. To repair an older registry, see
[Upgrade from a workspace.toml registry](../../core/how-to/upgrade-from-a-workspace-registry.md).
