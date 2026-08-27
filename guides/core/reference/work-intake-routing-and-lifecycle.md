---
title: Work-intake routing and lifecycle
summary: Authoritative routes, states, processors, and mutation boundaries for Core work intake.
pack: core
kind: reference
order: 10
journey: core
---

# Work-intake routing and lifecycle

This Core page is authoritative for the closeout, pause, and disposition
lifecycle: the phases, the six disposition intents, and which workflow owns each
mutation. For the cross-profile *intake* routes shared with other profiles, see
[Work-intake routing and lifecycle reference](../../_shared/reference/work-intake-routing-and-lifecycle.md),
which does not cover closeout.

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
| Admit a shaping handoff | Validate bounded context, resolve its semantic destination, and continue through an existing brief or spec processor |
| Pause work | Persist a reference-only restorable overlay through `close-work`; keep Ready or Implementing status |
| Close work | Hand bounded delivery evidence to `close-work`, verify durable owners, and recommend a disposition without automatic action |

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

## Optional shaping handoff

Capability: `normalized-intake.v1#handoff`.

The optional closed object carries required arrays for boundaries, non-goals,
dependencies, design context, and delivery questions. Empty arrays are valid.
Absence means standalone Core and preserves the existing route.

| Admitted shape | Semantic role | Existing processor |
| --- | --- | --- |
| One independently shippable feature | Delivery contract | `new-spec` |
| Multi-spec or cross-repository outcome | Delivery brief | `receive-brief`, or `author-brief` when no brief exists |
| Incomplete content, source mismatch, ambiguity, policy conflict | None | Stable clarification, confirmation, or refusal stop |

The current invocation supplies bounded resolver candidates; intake does not
scan for destinations. A repository locator is read only as a confined regular
file. An external locator remains opaque and is never fetched, searched,
probed, executed, or converted into a path. Previously acquired external
content is reusable only when the trusted invocation supplies it and its
revision matches.

## Inputs and outputs

Input: action, bounded content, source locator and revision, constraints,
proposed authority, an optional validated shaping handoff, and an existing
registered refresh target when applicable.

Output: action, repository-relative artifact path, workspace membership,
processor, authority mode, and stop point. Refresh also returns compared and
accepted revisions, field decisions, conflict state, local mutation state, and
a redacted remote-action result when one separately confirmed action ran.

Workspace entries contain only path, kind, source, summary, and hard needs.
Titles, comments, list order, tracker type, and memory are not routing
authority.

For follow-ons and remembered work, `work-intake` materializes the canonical
artifact first. The `workspace.toml` entry is only a terse live pointer:
minimal provenance, one short current/next summary, and hard dependencies. It
does not store rationale, chronology, review findings, suggested order, copied
source text, or procedures.

## Completion and closeout

`work-loop` owns implementation, verification, and review. At completion it
hands `close-work` bounded references for the accepted outcome, implemented
scope, gates, durable-output status, obligations, dependencies, completion
event, and independent authority facts. The handoff is evidence, not a status
transition or deletion grant.

`close-work` alone marks Closeout-pending or Post-closeout, inventories lasting
facts and Design/LLD findings, confirms affected human-readable owners are
semantically fresh as wholes, recommends one disposition, and owns any
separately authorized persisted effect. Code and tests remain capability proof;
they do not replace product intent, rationale, user promises, ownership, or
operations guidance.

| Disposition | Wave 4 result |
| --- | --- |
| `discard-local` | Recommend discarding tool-owned temporary state; removing a file still needs confirmation |
| `delete-before-push` | Prepare one exact never-pushed local removal for fresh confirmation |
| `delete-before-merge` | Prepare removal before the removal change integrates; an integrated change needs an ordinary follow-up |
| `cool-30-days` | Classify and retain only; Wave 5 owns dates, clocks, due state, and retirement |
| `retain-exception` | Retain with a bounded reason, owner role, and human-supplied review date |
| `external-advisory` | Report evidence and missing external authority without probing or mutation |

Disposition is intent, not permission. Every write, content-removing compaction,
or deletion needs a separately resolved actor/grant/action/resource/evidence/
session authority fact. Every deletion also needs fresh human confirmation bound
to the exact locator, fingerprint, disposition, source-state evidence, and
deletion authority. Drift expires it. Committed removal is an ordinary reviewed
change; history is never rewritten.

A pause uses an existing resolved writable shaping or build surface and stores
only contract/plan locators and fingerprints, current statuses, evidence
references, coordination locator, and restore action. Resume reacquires every
reference. `workspace-status` projects pause, closeout blockers, cooling
visibility, and next action, but never distils, dispositions, confirms, or
mutates.

Initiative coordination and artifact retention are assessed independently. A
settled workspace entry may leave while an RFC/release/decision family remains
anchored. A live dependency may retain a four-field completion receipt in an
already compatible surface; absent such a surface, the delivery record remains
a retained exception. See [Close work without losing lasting context](../how-to/close-and-disposition-work.md).

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
