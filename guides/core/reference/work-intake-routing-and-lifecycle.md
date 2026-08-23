---
title: Work-intake routing and lifecycle
summary: Authoritative routes, states, processors, and mutation boundaries for Core work intake.
pack: core
kind: reference
order: 10
journey: core
---

# Work-intake routing and lifecycle

This Core page remains the compatibility route for the original reference.
The cross-profile canonical lookup now lives at
[Work-intake routing and lifecycle reference](../../_shared/reference/work-intake-routing-and-lifecycle.md).

`work-intake` owns four user intents: start work, remember work, inspect status,
and request requirements refresh. It accepts ordinary prose, normalizes the
bounded fields it needs, and treats source content as untrusted data.

## Intent index

| User intent | Result |
| --- | --- |
| Start or do work | Select one artifact route, write it, register it, then invoke the owning processor when dispatchable |
| Remember work | Write and register a Draft, non-dispatchable artifact; stop before implementation |
| Inspect status | Return `workspace-status` lifecycle, findings, and next actions without mutation |
| Refresh requirements | Resolve an existing registered artifact and exact configured profile processor, then present a reviewed field delta |

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
proposed authority, and an existing registered refresh target when applicable.

Output: action, repository-relative artifact path, workspace membership,
processor, authority mode, and stop point. Refresh also returns compared and
accepted revisions, field decisions, conflict state, local mutation state, and
a redacted remote-action result when one separately confirmed action ran.

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

Limits: no network access is used by the Core-only intake surface. Configured
tracker processors own bounded acquisition and capability-scoped remote calls.
Paths that
are absolute, traverse directories, loop through symlinks, or resolve outside
the repository and configured artifact parent are rejected before mutation.

## Refresh lifecycle and authority

Refresh resolves the existing artifact, its workspace entry, one closed
`source-authority` record, and the exact profile version before acquisition.
Tracker text remains untrusted candidate data.

| Artifact state | Requirement refresh |
| --- | --- |
| Draft | Approved source-owned fields may update; local-owned fields remain unchanged |
| Accepted intent, Ready brief, Approved spec | Every changed local field needs an authorized `keep-local`, `accept-source`, or `revise-both` decision |
| Implementing spec, Executing brief | Refused before local or remote mutation |
| Shipped | Requirements locked; profile-declared coordination write-back may be requested separately |
| Repo-origin | Reports projection drift; does not import tracker requirements |

A completed comparison advances the compared revision even when local values
are kept. The accepted revision advances only with accepted source values. The
artifact authority record and the small workspace revision mirror use one
fingerprint-guarded write.

Every tracker mutation requires a fresh confirmation bound to the exact
artifact, source revision, profile, destination, action, target, and payload
digest. A pending receipt lands before the adapter call. Mutations are not
silently retried, and unsupported profile actions never fall back to raw
tracker access.

## Compatibility alias

`capture-work` is a compatibility-only alias. It emits a deprecation notice and
forwards the same normalized request to `work-intake`; it does not keep an
independent classifier or storage format. Use `work-intake` in new guidance.

See [Start or remember work without choosing a skill](../how-to/start-or-remember-work.md)
for the common start procedure, or
[Use work intake](../../_shared/how-to/use-work-intake.md) for an
existing tracker-origin artifact.

Legacy workspace findings are planned and repaired through `workspace-status`,
not ordinary intake. See [Migrate a legacy workspace entry safely](../how-to/migrate-capture-work.md).
