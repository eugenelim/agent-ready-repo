# Spec: The intent rename transaction

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0108; ADR-0033; ADR-0098; ADR-0129; ADR-0134
- **Brief:** brief:intent-identity-and-registration
- **Discovery:** docs/product/intents/FEAT-0001-intent-identity-and-registration.md
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

The retire-and-issue operation applies as one transaction: either every change
lands — the successor written, the tombstone standing at the vacated path,
every citation repointed, the registry moved in lockstep — or the repository is
recoverable to exactly one of two states, with nothing left in between. An
operator drives it from an installed `packs/core`, and a failure tells them
where they are and how to get out.

## What Changes

- The transaction itself: the phase model, what each phase may write, and what
  a kill in each phase leaves behind
- Recovery, in both directions, and what each is allowed to trust
- The citation sweep's application — the relation it applies is contracted by
  `docs/specs/intent-renumber-and-reissue/spec.md` and delivered by its plan
- The operator surface an installed `packs/core` exposes, and resolution
  through a tombstone
- Where it ships — inside `packs/core`, beside the allocator and the request
  contract it composes

## Why this is a separate slice

This began inside `intent-renumber-and-reissue` and was cut out on 2026-09-28
after the evidence became unambiguous. That slice's contract — the request
shape, the tombstone shape, the citation relation, the allocator property —
converged in nine adversarial rounds and has not changed since. Its transaction
design did not converge: five successive mechanisms were specified, and each
review round sustained a defect in the newest one, with three rounds of
`prior-round-repair` origin followed by a spec-stage security pass sustaining
ten findings, four more against the repairs to those, and six more against the
repairs to *those*.

A throwaway spike then measured the failure modes rather than arguing them, and
the measurements are inherited at `notes/verification-ledger.md`. They establish
that the difficulty is real rather than editorial: a shared lock that `SIGKILL`
strands with no recovery verb, a staging parent that a symlink swap redirects,
`os.replace` consuming the record its own recovery reads, and a kill mid-copy
leaving a partial tombstone the sibling corpus lint rejects.

The through-line in the unresolved findings is that a durable recovery record
must be trusted by a process that did not write it. That is a design problem
with its own shape, and it earns its own contract rather than another repair
inside a slice whose other four fifths were ready to build.

## Agent Rules

### Always do

- Resolve every path against a repository root established by rule, and prove
  containment against a held no-follow descriptor before each write, not once
  at plan time.
- Leave a tombstone at every filename the operation vacates.
- Refuse to a human. The operation is operator-invoked only, so every refusal
  and every interruption has a reader.
- Treat a recovery record written by a dead process as untrusted input.

### Ask first

- Moving more than one intent in a single run.
- Widening any skill's declared tool surface to make the operation runnable.
- Changing the shared workspace-writer lock protocol, which other writers share.

### Never do

- Delete an intent file. A retirement is a tombstone, not a deletion.
- Add a new top-level directory, a new module boundary, or a new dependency.
- Repair a stale citation by editing a generated projection.
- Hold the shared workspace lock across the transaction. Measured on
  2026-09-28: a kill while holding it blocks every workspace writer until a
  human clears the file.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — the transaction and recovery model is the decision this slice exists to settle | `docs/adr/` | eugenelim | An Accepted ADR stating the phase model, what recovery may trust, and the rejected alternatives | The ADR exists and this spec cites it in `Constrained by:` |
| Maintainer procedure | Applicable — recovery is operator-driven and its refusals need a story | `guides/product-engineering/how-to/` | eugenelim | A how-to covering a rename, each refusal, and both recovery directions | The page walks one real rename and one real recovery end to end |
| Current product truth | Applicable — `intake-intent` and `work-intake` both state that nothing renames an intent | the two `SKILL.md` bodies | eugenelim | Those statements point at this operation | No skill still claims an intent can never be renamed |
| Release history | Applicable — the operation ships inside `packs/core` | `docs/product/changelog.md` | eugenelim | One Core entry for the shipped operation | Entry present under the released Core version |
| Reusable learning | Applicable — the failure modes were measured, and the measurements are why this slice exists | `docs/specs/intent-rename-transaction/notes/verification-ledger.md` | eugenelim | The inherited spike measurements plus whatever this slice measures | The ledger records the measurements the design rests on |
| Current architecture | Not applicable — the operation adds no module boundary and no layer | — | — | — | — |

## Testing Strategy

- **Transactionality and recovery (AC-0003, AC-0026): TDD.** A failure injected
  at each write point, and a real kill at each, asserting the tree reaches
  exactly one of the two permitted states under each recovery direction. This
  is what the predecessor slice could not settle in prose, so it is driven by
  execution rather than by argument. Three case families sit inside this group
  rather than beside it, because each is a way the same two-state property
  fails: recovery reading an untrusted record — truncated, carrying duplicate
  or unknown fields, exceeding fixed structural bounds, disagreeing with what
  the request re-derives, or altered after the kill — must refuse before the
  first destructive act; an absent or invalid
  completion seal must never authorize Commit; every non-registry live target
  must still be its preimage or postimage; `workspace.toml` must be re-read,
  parsed, semantically transitioned and validated under the shared lock while
  preserving unrelated valid bytes and entries; a created successor and a
  stranded shared lock must be recognised by retained filesystem identity
  rather than byte equality. Clearing the lock additionally requires a bounded
  canonical owner PID proven dead; live, malformed, foreign and alien-link
  states refuse before lock mutation.
  Real kills immediately after each hard link prove recovery accepts only the
  owned two-link stage artifact and refuses an alien link. The sweep must remove a
  real orphan while leaving a symlinked candidate and another transaction's
  temporary alone; and the lock must not be strandable by a kill inside its
  critical section.
- **Citation conservation (AC-0018) and content carried across (AC-0002,
  AC-0024): TDD.** Byte-for-byte comparison before and after, so a citation
  removed rather than repointed fails even though the vacated path is gone.
- **The sweep's completeness (AC-0001): TDD.** After a rename the vacated path
  occurs in no tracked file but the named exclusions, over the parent set the
  sibling contract defines.
- **Fresh allocation (AC-0012): TDD.** A fixture where the vacated ordinal is
  free under the target token, asserting the operation still takes the
  allocator's next value.
- **The success path (AC-0013): TDD.** Both causes run to completion and the
  tombstone is read back for its `Reissued as:` value.
- **Tombstone target validity and resolution (AC-0007, AC-0008, AC-0009): TDD.**
  An absent target, a target that is itself a tombstone, a pointer resolving
  onto a tombstone, and a corpus whose tombstones already point at the source.
- **The operator surface (AC-0025): goal-based check.** A rename driven through
  the surface an installed `packs/core` exposes, not through an internal entry
  point.
- **The operator how-to: manual QA.** A person follows the page through one
  rename and one recovery; a test cannot tell whether the page is followable.

Construction-stub tally: 11/12 criteria have exact PLAN stubs. AC-0025 is
`no stub (goal-based)` because its proof is the installed operator surface.
T2's altered-record matrix is `no stub (implementation-discovered)` until T1
materializes the sealed record schema; it deepens the existing AC-0026 stub.

## Acceptance Criteria

- [ ] **AC-0003.** A failure before the rename begins applying leaves the
      working tree and the index as they were before it ran.
- [ ] **AC-0026.** An interruption while the rename is applying leaves the
      repository in one of two observable states — every change applied, or a
      partial state naming every path the rename intended to write, from which
      re-running the operation or restoring those paths ends in the complete
      rename or the pre-rename state and in no third state. Which failures
      recover automatically, and how, is design. Before the first destructive
      recovery act, the operation boundedly and confinedly reads a complete
      sealed record and independently re-derives the allowed write set and
      exact postimage bytes for every non-registry write from the operator's
      request, operator-confirmed tombstone date, and pinned repository
      snapshot. `workspace.toml` is never replayed from a staged postimage:
      recovery re-reads and parses its current bytes under the shared lock,
      applies the one semantic source-to-successor transition, validates the
      result, and preserves unrelated valid bytes and entries. Before semantic use
      or mutation, its parser rejects duplicate or unknown object keys, wrong
      scalar or container types, non-finite numbers, nesting beyond a fixed
      depth, containers beyond a fixed member count, strings beyond a fixed
      length, and any byte-budget excess, with a fixed diagnostic that echoes no
      record content. Recovery then establishes that every live target is still
      an allowed preimage or postimage. A created successor or stranded shared
      lock is this transaction's only when retained filesystem identity proves
      it; equal bytes alone never grant ownership. Clearing that same-inode
      lock also requires one bounded canonical owner PID proven dead; a live,
      malformed, foreign or alien-link lock refuses before mutation. A missing or invalid
      completion seal never authorizes a live-path mutation. Stage-only cleanup
      after seal removal requires a durable cleanup marker written after an
      independently validated terminal state.
- [ ] **AC-0001.** After a rename, the vacated path occurs in no tracked file
      except the tombstone standing at it and this spec's own
      `notes/verification-ledger.md`. The searched set is the pre-run tracked
      set plus every file the operation creates, whatever its index state, so
      an unstaged successor cannot escape the search. The relation is string
      occurrence, not a list of citation forms: enumerating forms is what
      leaves a stale citation passing, and a bare path in a `Discovery:` or
      `Brief:` header is already a form no link-target rule reaches. "After a
      rename" includes the catalogue self-host projection step: a tracked
      generated projection carries whatever its `.apm/` source carries, so the
      operation repoints the source and the projection is regenerated rather
      than edited. The criterion is evaluated after that step, which is the
      only point at which both it and the bar on editing a projection hold.
- [ ] **AC-0018.** Over AC-0001's searched set, every file that cited the
      vacated path before a rename cites the new path after it, and no other content in that file changes.
      A citation is repointed, never removed. A tracked generated projection is
      outside this criterion. The operation repoints that file's `.apm/` source
      and never writes the projection, so conservation over the projection is a
      property of the self-host step and not of the rename — a version line, a
      header, or an extension substitution would falsify it with the rename
      entirely correct. The catalogue's self-host drift gate, `CAT-V-015`, owns
      that property. AC-0001 still reaches the projection, because its relation
      is string occurrence and a repointed source plus any regeneration
      satisfies it. The renamed artifact itself is
      outside this criterion, because it becomes a tombstone; AC-0024 governs
      it.
- [ ] **AC-0024.** The successor's bytes equal the retired source's bytes
      after substituting the new path for the vacated one, and differ nowhere
      else. A source that cites its own path is the case that distinguishes
      this from plain equality: the substitution is what lets AC-0001 and this
      criterion both hold.
- [ ] **AC-0002.** After a rename the successor's `Slug:` bytes equal the
      retired source's, the tombstone carries those same bytes, and every
      unaffected intent keeps its prior `Slug:` bytes. The corpus gains an
      occurrence of that value rather than preserving a collection, so the
      mapping is stated directly.
- [ ] **AC-0012.** The new filename's ordinal is the allocator's next ordinal
      for the target token over the corpus as it stood before the rename. The
      allocator's answer is the whole requirement: carrying an ordinal across
      fails it whenever carrying and allocating differ, and where they
      coincide there is nothing to distinguish.
- [ ] **AC-0025.** A rename completes through the surface an installed
      `packs/core` exposes to an operator, exercised as an operator invokes it
      rather than through an internal entry point.
- [ ] **AC-0013.** A request satisfying the request contract in
      `docs/specs/intent-renumber-and-reissue/spec.md` whose source is registered in
      `workspace.toml` and whose affected paths are all clean succeeds,
      leaving a tombstone at the vacated path whose
      `Reissued as:` value is the new live artifact's repository-relative path.
      That spec's pre-run dirty-path criterion is the exclusion for a dirty
      path; an unregistered source is
      refused because the Outcome requires the registry to move in lockstep;
      and a corpus the allocator cannot answer for, a target filename
      already occupied, a citing file the operation cannot prove is decodable
      text, and a citing set beyond the operation's stated budget are each
      excluded and refused rather than forced to succeed. The last two are
      safety exclusions rather than correctness ones: a file whose bytes are not
      text cannot be repointed without risking corruption of content another
      gate pins, and a budget that truncated the search instead of refusing
      would leave a stale citation behind while still reporting AC-0001
      satisfied.
- [ ] **AC-0007.** Resolving a tombstone whose `Reissued as:` names a path
      that does not exist yields a diagnostic naming the tombstone and the
      missing path, on the operator surface AC-0025 names.
- [ ] **AC-0008.** Resolving a tombstone whose `Reissued as:` names a file that
      itself carries `Tombstone:` yields a diagnostic naming both paths, on
      that same operator surface.
- [ ] **AC-0009.** On the operator surface AC-0025 names, resolving a path
      that lands on a tombstone yields a
      diagnostic naming the tombstone and its `Reissued as:` target, and never
      the successor's content. Resolution stops at the tombstone rather than
      recursively following it; it may boundedly and confinedly inspect exactly
      the target preamble only to classify the AC-0007 and AC-0008 cases.

## Retired identifiers

_None yet. The identifiers above were authored in
`docs/specs/intent-renumber-and-reissue/spec.md` and moved here on 2026-09-28
when the transaction was cut into its own slice; they keep their numbers so the
review history behind their wording stays legible._

## Follow-ons

- `docs/specs/intent-renumber-and-reissue/spec.md` owns the request contract,
  the tombstone field contract, the citation relation and the allocator
  property. This slice composes them; it does not restate them. Cite that spec
  by path and its obligations by name, never by criterion number — the
  alignment lint resolves a bare `AC-####` against local criteria only.
- eugenelim: `packs/core/.apm/skills/work-intake/scripts/intake_transaction.py`
  — `.workspace-repair.lock` has no stale-owner recovery. Measured 2026-09-28
  and recorded in `notes/verification-ledger.md`. It predates both slices and
  affects every workspace writer equally; changing a shared protocol is not
  this contract's outcome either.

## Assumptions

- Technical: the spike could not produce a same-device-different-mount `EXDEV`
  case without elevation, and did not exercise Windows reparse-point semantics.
  Both are recorded as unmeasured in `notes/verification-ledger.md`

## Changelog

- 2026-09-29 — T0 completed. Strengthened AC-0026 and its verification group
  with the measured recovery-record, preimage/postimage and inode-ownership
  boundary; added the construction-stub tally.
- 2026-09-29 — added accepted ADR-0129 to the governing constraints and removed
  the stale conditional assumption about its acceptance.
- 2026-09-28 — drafted from the twelve transaction criteria cut out of
  `intent-renumber-and-reissue` with their identifiers preserved.
