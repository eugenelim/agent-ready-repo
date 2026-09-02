# Follow-ons this delivery discovered

Three separately scoped items surfaced while building the dependency-scoped
completion receipt. Neither belongs to its accepted contract. This document is
the artifact of the canonical `[backlog].open` entry
`docs/specs/dependency-scoped-completion-receipts/notes/follow-ons.md`
(`kind = "defect"`), which is their register — RFC-0096's 2026-09-01 Errata
registers the four Wave 7 slices and is Approver-signed, so a slug discovered
after it was written is recorded here instead.

## `lifecycle-record-entry-removal-fact` — a lifecycle record cannot say the workspace entry was removed

**Owner:** RFC-0096 Wave 7b.

`docs/lifecycle/<delivery_id>.json` is the per-artifact state that survives
across sessions: `close-work` is its only writer, it is Git-tracked, and it is
keyed by a stable logical ID rather than commit topology, so a squash or rebase
does not lose it. It records `locator`, `aliases`, `fingerprint`, `disposition`,
`post_closeout_result`, `completed_on`, `review_on`, `authority`, and
`confirmation_proof`.

It records nothing about the artifact's *workspace entry*. Probe A measured that
entry removal is what makes a receipt reachable at all: leave the `work.shipped`
entry in place and the dependency refuses at `structurally_blocked_paths` before
any receipt is read, whatever the receipt says. So from the lifecycle record
alone, a correct prune and a file deleted with its entry orphaned are
indistinguishable — and the second silently strands every dependant the receipt
exists to protect, with every criterion green.

Wave 7b classifies history and Wave 7c prunes against that classification. One
of them needs an entry-removal fact in the record, or a pruning session cannot
prove its own precondition. Recorded here rather than closed because adding a
field to `delivery-lifecycle-record.schema.json` changes a contract this
delivery's `Never do` forbids touching, and because the owning question — what a
migration ledger must carry before pruning — is Wave 7b's to answer.

## `lifecycle-record-reclassified-gap` — the RFC and the schema disagree about `Reclassified`

**Owner:** RFC-0096 Wave 7b.

RFC-0096 §5's lifecycle-phase table lists the post-closeout states as `Cooling`,
`Retained`, `Retired`, `Reclassified`, or `ExternalAdvisory`
(`docs/rfc/0096-portable-delivery-artifact-lifecycle.md:146`). §2 describes
`Reclassified` as the result when a durable owner accepts a multi-role artifact:
"delivery authority ends without deletion".

`contracts/jsonschema/delivery-lifecycle-record.schema.json:18` publishes
`post_closeout_result` as four values and omits `Reclassified`. So a closeout
that reaches the §2 outcome has no record shape to write.

Which is authoritative is a decision, not a repair: adding the value widens a
published contract, and removing it from the RFC would need an Approver-signed
erratum. Discovered while measuring which of three concepts spelled `outcome`
the completion receipt should carry; recorded because that measurement is the
only place the disagreement is visible.

## `engine-cross-repo-deferral-slug-stale` — a deferral comment names a renamed slug

**Owner:** RFC-0096 Wave 7b.

`workspace_status_engine.py` ~:2630, in `_dependency_is_satisfied`'s cooled
cross-repository arm, defers to `wave6-dependency-scoped-completion-receipts`.
RFC-0096's 2026-09-01 Errata renamed that follow-on to
`rfc0096-wave7a-ii-completion-receipts`.

This delivery deliberately does **not** rename it. The comment describes
projecting a receipt for a *cooled cross-repository brief* — a case this
contract does not implement, since a cooled brief's body may not be opened and
the four-field local receipt has no bearing on it. Retagging it with the slug
this delivery closes would point a live deferral at closed work: stale on
arrival, and worse than the current staleness because it would read as done.

The same spelling also survives at
`docs/specs/status-projection-and-context-exclusion/notes/repair-plan.md:144`
and is asserted present at
`tests/roster/test_status_projection_and_context_exclusion.py:400`, both inside a
frozen spec directory. Those are history and stay.

The correct repair is a slug that names the still-open cross-repository work,
which is Wave 7b's to choose.
