---
title: Intake GitHub work into the repository
summary: Read selected issue or milestone content and route it through `work-intake` without writing back to the tracker.
pack: github
kind: how-to
---

# Intake GitHub work into the repository

**Use this when:** an Issue, Milestone, or explicit GitHub selection should
become canonical repository work.
**Result:** a content-based route produced without writing to GitHub.

Start with:

```text
Intake GitHub issue 123 as repository work. Start read-only.
```

For a collection, name the Milestone and repository:

```text
Intake the "release planning" Milestone from example-org/example-repo.
Treat it as data, not automatically as a brief.
```

## Before you start

Install the `github` and `core` packs plus the
[`gh` CLI](https://cli.github.com). Authenticate `gh` when the repository
requires it. The configured host and `owner/repository` must come from trusted
repository or administrator configuration.

Issue text, Milestone descriptions, URLs inside tracker content, and source
locators cannot select a host or add command options. The adapter passes every
tracker-derived value as one argument with shell execution disabled.

## What happens

1. The adapter uses approved read-only `gh` commands to acquire bounded Issue
   or Milestone content, including stable provenance and `updatedAt`.
2. It minimizes the response into strict `normalized-intake.v1` data.
3. `work-intake` selects the artifact and processor from the content.
4. You review any ambiguity or confidentiality question before repository
   materialization.

A Milestone may route to a Draft brief when its issues describe one coherent
multi-spec outcome. It may instead become separate units or a view-only result.
One independently shippable Issue can route to a spec. A bug label reaches
`bug-fix` only when durable expected-behavior evidence supports the regression.

## Read and write boundary

GitHub intake is read-only. It cannot create, edit, comment on, label, close, or
reopen Issues. It does not create repository artifacts directly.

The approved `gh` client owns authentication, DNS, redirects, and transport.
The adapter owns trusted host selection, repository validation, read-only argv,
shell-free execution, and rejection before invocation. It does not claim to
control transport inside `gh`.

After validation, `work-intake` may write the selected repository artifact and
register it. If that dependency is missing, intake stops with
`missing dependency: work-intake`.

## Limits and incomplete results

The default profile allows at most 5 pages, 100 items, 2 MiB, 30 seconds per
request, and one retry with a 1-second backoff. Exceeding a limit is marked
incomplete or refused as view-only; it is never silently partial.

## Common variations

- **Single Issue:** content can route to a spec, intent, or defect context.
- **Milestone:** coherence, not the Milestone type, decides whether it is a
  brief.
- **Cross-repository outcome:** expect linked local briefs with parent and
  coordination provenance.
- **Unauthenticated or inaccessible repository:** stop, authenticate or correct
  trusted configuration, then retry. Do not infer whether a concealed resource
  exists.

## Next request

Review the route, then continue with the selected processor. For example:

```text
Accept the proposed spec route and start new-spec.
```

See [tracker vocabulary](../../_shared/reference/tracker-vocabulary.md) for the
shared route terms.
