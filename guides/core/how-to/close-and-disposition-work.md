---
title: Close work without losing lasting context
summary: Verify durable context, settle live coordination, and choose a safe disposition without granting automatic deletion.
pack: core
kind: how-to
order: 12
journey: core
---

# Close work without losing lasting context

Close completed, abandoned, or superseded work only after its lasting facts have
an owner and the repository still tells a coherent story. You get a closeout
preview with blockers, evidence links, and a disposition recommendation before
anything changes.

```text
Close this work. Check that lasting product, user, architecture, decision, and
maintainer context is current as a whole. Show me the disposition and any exact
change that needs confirmation, but do not delete anything yet.
```

The agent uses `close-work` to inspect the accepted outcome, delivery evidence,
planned durable outputs, obligations, dependencies, and live coordination. It
reads the resolved files and evidence needed for that review. The preview does
not write, compact, call an external system, or delete.

## Review the closeout preview

Start with the named blockers and each durable output. A passing test proves that
the implementation can do something; it does not preserve the product promise,
the reason for a decision, ownership, or an operational obligation. Those facts
must already live in the repository's established product, user, architecture,
decision, interface, operations, maintainer, release, or project-knowledge
surface when applicable.

For every affected human-readable surface, review the page as a whole. Confirm
that a maintainer can still understand the current system, follow its pointers,
and distinguish current truth from delivery history. A file being touched is not
proof of freshness. Ask the owning workflow to update stale or missing context,
then run closeout again.

Review the plan's Design or LLD section the same way. Move substantial rationale
and trade-offs to the repository's decision history, and current ownership,
boundaries, control flow, and safety invariants to its terse architecture or
maintainer docs. Public interfaces and operational promises use their established
owners. Internal shapes that the code and tests state exactly, plus one-off build
order and scaffolding, do not need copied prose. Stop if a design fact that cannot
be reconstructed still lives only in the plan.

An established RFC series, release train, or decision lineage may be a reason to
retain or reclassify a related artifact family. Merely sharing a workspace
initiative is not. Workspace cleanup and artifact retention are separate
decisions.

## Choose the immediate disposition

`close-work` recommends one eligible intent. It does not treat that choice as
permission to act.

Disposition is intent, not deletion permission.

| Disposition | When it applies | What happens now |
| --- | --- | --- |
| `discard-local` | In-memory or tool-owned temporary state with no persisted or lasting content | The temporary state may be discarded. Removing a file still needs separate confirmation. |
| `delete-before-push` | The exact target was never sent remotely | The workflow can prepare a confirmed local removal. Evidence of a prior push forces a new choice. |
| `delete-before-merge` | A removal change exists but has not been integrated | The workflow can prepare removal before that change merges. An integrated removal uses an ordinary follow-up change. |
| `cool-30-days` | Delivered, closed work has a persistent record | Wave 5 computes the review date and enrols the record, then keeps it until a day-30 review. |
| `retain-exception` | A longer obligation requires retention | Record a bounded reason, an owner role, and a human-supplied review date. Nothing is deleted. |
| `external-advisory` | The current environment lacks authority over the target — an external system, or a local target whose deletion authority cannot be resolved | Report the target, evidence, and missing authority without probing or changing it. Resolve the authority or leave the artifact retained, then re-run; the workflow refuses rather than deleting. |

Immediate disposal is the default recommendation when no lasting fact,
obligation, dependency, or anchor remains. It is never automatic.

## Close a temporary full-mode record

Full-mode work does not have to make its spec and plan permanent. For a one-off
cleanup or other bounded PR, you may approve a local-only record that persists in
the current writable coordination surface without committing it, or a PR-only
record intended to be removed before integration. Full mode still applies its
normal plan, gate, and review rigor.

Choose local-only only when every required reader and resuming session can reach
that same surface. If another person, worktree, CI job, or external control plane
needs the record, use an established shareable surface or retain it. Keep the exact
approved locator and fingerprint; do not replace the record with session memory.

At closeout, first route lasting context and keep stable completion evidence outside
the record being removed. Then settle any temporary `workspace.toml` membership as
separate coordination residue. A never-pushed local record may qualify for
`delete-before-push`; a PR-only record removed before integration may qualify for
`delete-before-merge`. Both are recommendations and still require a fresh exact
confirmation.

## Confirm an exact change

If you want a local write, deletion, or content-removing compaction, ask to see
the exact effect first. The confirmation must bind all of these current facts:

- the non-personal actor role and the source of its grant;
- distinct proposer and human approver roles, each with evidence;
- the exact action and logical and physical resource;
- one confined regular file and its fingerprint (repeat the preview and
  confirmation separately for every additional file);
- the chosen disposition and supporting delivery and durable-output evidence;
- the current `pushed` and `removal_integrated` facts and their named evidence
  source;
- independent source, write, and deletion authority facts and evidence, including
  the deletion-specific resolver-issued authority digest and resolution evidence;
- the current host or session provenance; and
- the fresh helper-issued challenge from this preview, which makes a proof from a
  prior helper process ineligible for replay.

The human confirmation must restate the previewed fields and cite its own evidence;
the workflow cannot construct approval merely by copying its preview. Declining
leaves the target unchanged. Before acting, `close-work` reacquires a new
resolver-issued deletion authority fact, then resolves, reclassifies, confines,
enumerates, and fingerprints again. Raw policy-shaped strings or maps never satisfy
that boundary, and the authority fact consumed by the preview cannot be reused for
the effect. A rename, content change, added or
missing file, parent-directory substitution, authority change, or session change
expires the confirmation and produces no deletion. Staging uses an exclusive
no-clobber link. If the final unlink fails, rollback reopens the staging path
without following links and verifies its fingerprint, device, inode, size, and
link count immediately before any rollback effect. A surviving added link on the
confirmed inode produces `residual-hardlink`. Any other rollback identity/content
corruption or operation failure produces `rollback-failed`. Both are terminal
mutated outcomes: the report identifies bounded inode evidence when a descriptor
established the residue's identity, any `.pending` recovery residue whose path
still resolves under the validated parent handle, and — when the original was
already unlinked — the affected original path. Where identity could not be
established, or where a parent-directory substitution was proven, the report
omits that locator rather than inventing one: the inode evidence identifies the
residue without depending on a path. A rollback that refuses before that unlink
reports no original path,
because there is none; do not claim success, restoration, or an unchanged refusal.

Each such report also names the residue's identity, and you must read it before
recovering anything: `identity-confirmed` means a descriptor proved the residue is
the confirmed inode, `identity-mismatch` means a descriptor proved it is not, and
`unverified` means no descriptor could establish it.

:::caution
Restore only an `identity-confirmed` residue. Restoring an `identity-mismatch` or
`unverified` residue puts content of unknown origin back at the original path.
:::

Changed, stale, or unavailable
push/integration evidence, or drift in source, write, or deletion authority,
refuses before content is read. An effect attempt consumes the confirmation even
when it refuses, so every later attempt needs a new preview and a new confirmation.

The final unlink is verified through an open descriptor to the staged inode. A
`residual-hardlink` result means the confirmed target path was removed but a link
created during the final effect still preserves that inode. This is a terminal
mutated state, not successful disposal: report the affected target and the final
descriptor's link-count/device/inode evidence, stop, and ask
a maintainer to investigate and recover the surviving unconfirmed link before any
new disposition attempt.

On a platform without the required no-follow, nonblocking, directory-relative file
operations, the workflow refuses before it asks for confirmation. There is no
weaker path-based fallback.

Committed files leave the current tree through an ordinary reviewed change.
`close-work` never resets, rebases, filters, force-pushes, or otherwise rewrites
Git history.

## Amend the contract instead of shipping an open AC

If one accepted AC needs another session, leave the spec Implementing and resume;
session length does not narrow the outcome. If the work is genuinely separable,
pause and ask the owner to approve an amended outcome, AC set, and plan. Record the
separated item under `Follow-ons` with its owner and stable artifact or external
reference, rerun the applicable spec-stage reviews, and approve the new fingerprint
before implementation resumes.

A newly Shipped spec has every final AC checked. Do not use an unchecked
`(deferred: <slug>)` item as a shipping exception. Existing frozen specs that used
that older form remain unchanged until a separately governed migration.

## Keep workspace follow-ons terse

When `work-intake` captures the follow-on, it writes the context-owning artifact
first. Its `workspace.toml` entry contains minimal source provenance, one short
sentence naming the current outcome or next-needed condition, and hard dependencies
only. Do not add comment blocks with chronology, rationale, procedures, review
history, findings, or copied discussion. Those belong in the referenced artifact.

At closeout, remove settled live coordination rather than replacing it with a
workspace history. Legacy prose that this closeout did not touch remains for a later
migration; any entry materially updated now must use the terse form.

## Pause work instead of closing it

For work you expect to resume, say:

```text
Pause this work in its existing coordination surface and show me how to restore
the same context. Do not close or disposition it.
```

Pause keeps Ready or Implementing status and stores a restorable overlay in an
already resolved writable shaping or build surface. It does not start closeout,
select a disposition, or start a cooling clock. The overlay stores only current
contract/plan locators and fingerprints, statuses, bounded evidence references,
the coordination locator, and a structured restore action. It never embeds the
contract, plan, source, exception, transcript, credentials, identity, or
instructions, and resume reacquires and revalidates every reference. If no
compatible surface exists, the agent offers a destination and refuses to claim
that the work is resumable.

## Close an initiative

Ask `close-work` to preview initiative closure only after every child outcome is
settled. The preview reconciles shaping and build entries, durable outputs,
obligations, dependencies, and reusable findings. Live coordination can be
removed or compacted only through the same exact authority and confirmation
checks as any other persisted change.

A minimal completion receipt retains only the delivery ID, accepted outcome,
completion event, and stable evidence reference, and only while a live dependency
cites it. The receipt's `outcome` uses the closed vocabulary `completed`,
`abandoned`, or `superseded`. The receipt carries no requirements, rationale,
source payload, artifact content, or personal identity, and references an
evidence locator rather than a person. This matters because the receipt is
written into a coordination surface that is normally committed. If the
established coordination surface cannot carry that receipt, the delivery record
stays as a retained exception. `workspace.toml` remains an index; it does not
become the receipt, rationale, or cooling store.

## Next step

When the preview is clear, confirm the freshness judgment and the chosen
disposition. If an exact effect is proposed, your most likely follow-up is:

```text
Recheck the target and authority now. If every locator, fingerprint, evidence
reference, actor grant, action, resource, and session value still matches this
preview, ask me for the single-use confirmation.
```

Run `workspace-status` afterward for a read-only projection of remaining work and
next actions. See [Work-intake routing and lifecycle](../reference/work-intake-routing-and-lifecycle.md)
for the repository lifecycle and workflow ownership boundaries.
