---
title: Work-intake routing and lifecycle
summary: Authoritative routes, states, processors, and mutation boundaries for Core work intake.
pack: core
kind: reference
order: 10
journey: core
---

# Work-intake routing and lifecycle

`work-intake` owns four user intents: start work, remember work, inspect status,
and request requirements refresh. It accepts ordinary prose, normalizes the
bounded fields it needs, and treats source content as untrusted data.

## Intent index

| User intent | Result |
| --- | --- |
| Start or do work | Select one artifact route, write it, register it, then invoke the owning processor when dispatchable |
| Remember work | Write and register a Draft, non-dispatchable artifact; stop before implementation |
| Inspect status | Return `workspace-status` lifecycle, findings, and next actions without mutation |
| Refresh requirements | Resolve the target and report refresh unavailable without mutation |

## Start routing

| Input shape | Canonical artifact | Initial lifecycle | Processor |
| --- | --- | --- | --- |
| Minimal opportunity or outcome | Intent at `docs/product/intents/<slug>.md` | Draft, non-dispatchable | None |
| One independently shippable contract | Spec at `docs/specs/<slug>/spec.md` | Ready only after approval and a sibling plan | `new-spec` |
| Coherent multi-spec outcome | Brief at `docs/product/briefs/<slug>.md` | Draft, non-dispatchable | `author-brief` |
| Cited regression or defect evidence | Defect context | Ready only after canonical context exists | `bug-fix` |
| Incomplete or ambiguous input | Draft artifact with named gaps, or one clarifying question | Non-dispatchable | None |

A Ready brief may contain zero specs. It records a viable outcome and remains
non-executable until a human confirms a slice; only then does `receive-brief`
invoke `new-spec`.

## Inputs and outputs

Input: action, bounded content, source locator and revision, constraints,
proposed authority, and a refresh target when applicable.

Output: action, repository-relative artifact path, workspace membership,
processor, authority mode, and stop point.

Workspace entries contain only path, kind, source, summary, and hard needs.
Titles, comments, list order, tracker type, and memory are not routing
authority.

## Reads and writes

Reads: normalized request fields, the repository root, configured artifact
parent, existing target, `workspace.toml`, and status output.

Writes: at most one confined canonical artifact followed by its schema-valid
workspace entry. Dispatch starts only after both are durable. If registration
fails, the artifact is rolled back when safe; otherwise it remains explicitly
non-dispatchable for reconciliation.

Limits: no network access is used by the Core-only intake surface. Paths that
are absolute, traverse directories, loop through symlinks, or resolve outside
the repository and configured artifact parent are rejected before mutation.
Refresh does not change requirements in this release.

## Compatibility alias

`capture-work` is a compatibility-only alias. It emits a deprecation notice and
forwards the same normalized request to `work-intake`; it does not keep an
independent classifier or storage format. Use `work-intake` in new guidance.

See [Start or remember work without choosing a skill](../how-to/start-or-remember-work.md)
for the common procedure.
