---
title: How source, artifacts, workspace state, and processors divide responsibility
summary: Understand why work intake separates incoming evidence, durable requirements, lifecycle membership, and execution.
pack: _shared
kind: explanation
---

# How source, artifacts, workspace state, and processors divide responsibility

When you say, “Start work from this issue,” the useful result is not a copied
ticket. It is a durable repository artifact, registered in the right lifecycle
state, with one named processor and a clear human decision where the route is
not yet safe.

Four records participate, and each has one job.

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
reviewed source decisions live there. A comment in `workspace.toml` cannot
replace that artifact or supply missing requirements.

For tracker-origin work, the artifact also carries the closed source-authority
record. That record says which fields are source-owned or local-owned and which
source revision has been compared or accepted. Repo-origin artifacts remain
locally authoritative; refresh reports projection drift instead of importing
tracker requirements into them.

## `workspace.toml` owns lifecycle membership

The workspace is an index. Its five-field entries point to artifacts, record
their lifecycle membership, preserve minimal provenance, and name hard
dependencies. Summary text, comments, list order, and tracker vocabulary are
display context only.

This separation makes dispatch checkable. A spec can run only when its
canonical file exists, its sibling plan exists, its status is Approved, its
membership is unique and compatible, and its dependencies are satisfied.

## The processor owns the next operation

After artifact creation and registration are durable, the selected processor
may continue. `new-spec` authors one shippable contract, `author-brief` drafts a
coherent multi-spec outcome, `bug-fix` diagnoses a cited regression, and
`workspace-status` reports or repairs workspace state. A processor cannot widen
its authority because tracker text, a comment, or an alias asked it to.

The same boundary applies to refresh. The configured profile owns acquisition;
the shared lifecycle evaluator owns whether local requirements may change; a
separate fresh confirmation authorizes one exact remote coordination action.

## Migration changes representation, not meaning

Legacy workspace entries are readable during the compatibility window but are
never dispatchable. Migration preserves the exact legacy TOML slice in a
durable ledger, links it to an already-created canonical artifact, and replaces
only the workspace representation. Rollback restores that slice without
deleting the artifact.

A person chooses the target route and authors the reviewed selection. Apply
and rollback each require a new current-session confirmation. The tooling can
show candidates and bindings, but it cannot choose or author those human
inputs.

## The practical rule

When records disagree, repair the record that owns the fact:

- source evidence is reacquired or re-normalized;
- requirements are corrected in the canonical artifact;
- lifecycle membership is reconciled in `workspace.toml`;
- processor configuration is corrected in its versioned profile;
- migration history is read from `.workspace-migrations.json`.

See [Work-intake routing and lifecycle](../reference/work-intake-routing-and-lifecycle.md)
for the exact routes and [workspace.toml schema reference](../../core/reference/workspace-toml-schema.md)
for the target and compatibility shapes.
