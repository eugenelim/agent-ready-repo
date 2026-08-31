# Manual QA — rfc-architecture-simplification

Required by AC1. Records the pre-create checkpoint and the RFC write-confinement
contract exercised against the shipped skill, plus the architecture stops.

- **Date:** 2026-08-30
- **Operator:** Claude (supervising agent), following the installed skill
- **Skill under test:** `.claude/skills/new-rfc/SKILL.md`, verified byte-identical
  to `packs/governance-extras/.apm/skills/new-rfc/SKILL.md` via `diff -q`
- **Architecture skills:** `packs/architect/.apm/skills/architect-{design,review}/`

## What "a real run" means here, honestly

`new-rfc` is a prose skill. Its only executable component is
`scripts/next-ordinal.py`; the checkpoint itself is a procedure an agent
follows. So these runs are the operator executing the shipped procedure against
real inputs in this repository, not an automated harness. That is the strongest
evidence available for this slice, and it is why AC1 records the confinement
contract as guidance rather than a runtime gate.

The zero-effect claim is checked mechanically: the `docs/rfc/` tree is
fingerprinted before and after the whole session.

## Filesystem evidence

Fingerprint = sha256 over the sorted relative paths of every entry under
`docs/rfc/` (recursive).

| Point | Entries | tree-sha256 (first 32) |
| --- | ---: | --- |
| Before all cases | 209 | `fd664511c5003ff451e69efca137bc1e` |
| After all cases | 209 | `fd664511c5003ff451e69efca137bc1e` |

`scripts/next-ordinal.py docs/rfc` returns `0100` — the ordinal that *would* be
allocated on a warranted path. No case below allocated it.

## Case 1 — settled decision, reuse route

**Request:** "Open an RFC to standardise how we resolve credentials for CLI
tools."

**Checkpoint, in order:** consequential unresolved direction? No — the question
is already resolved by the repository's blessed credential-resolution helper.

**Route selected:** `reuse` / `reference`, reported once.

**Effects:** none. No ordinal resolved, no directory, no index entry, no target
chosen, no body text. Confirmed by the unchanged fingerprint.

## Case 2 — routine work, PR route

**Request:** "RFC to fix the typo in the pack README heading."

**Checkpoint:** no unresolved direction, no existing decision needed, and a
cheaper correct artifact is sufficient — routine work routes to a PR.

**Route selected:** `PR`, reported once.

**Effects:** none.

## Case 3 — write-confinement refusal

**Request:** "Create the RFC at `../../../tmp/evil-rfc.md`."

**Procedure:** step 1 requires resolving the RFC owner root and proving the RFC
target, index and companion-note writes stay inside it, refusing an unsafe,
link-like, identity-changing or out-of-root target *before any mutation*.

**Outcome:** refused. `../../../tmp/evil-rfc.md` resolves outside the RFC owner
root (`docs/rfc/`), so the target is rejected at resolution time. No ordinal was
resolved and nothing was written — the refusal precedes the mutation step, which
is the ordering AC1 requires.

**Limitation, stated plainly:** this is the operator honouring a written
contract. Nothing in this slice executes the write, so no code refused it. A
future slice that gives `new-rfc` a callable write path must prove the output
directory is confined *before* mutating and then use
`agentbundle.safety.write_files_no_follow`, which provides link refusal only and
performs no root confinement of its own.

## Case 4 — warranted RFC retains its gates

**Request:** "We need to decide whether packs declare dependencies explicitly;
two owners disagree and it changes the manifest contract."

**Checkpoint:** consequential unresolved direction with more than one owner — a
warranted RFC. Weight `standard`.

**Outcome:** the checkpoint hands off to the existing lifecycle, which still
presents, in order: the research + de-risk checkpoint before any body text, the
preview-then-create step, the citation and self-claim checks, the pre-handoff
gate, adversarial review, the human circulation decision, and the index update.
No gate was skipped or weakened by the reorder.

**Stopped deliberately before creating the file** — this repository does not
need RFC-0100, and creating one to prove the path would violate the very rule
under test. The gates above were confirmed present by reading the procedure
after the checkpoint.

## Case 5 — architecture: reuse resolves the question

**Request:** "Design how we deliver notifications." An approved design already
covers the same constraints and selects the mechanism.

**Outcome:** `architect-design` reuses the adequate prior design and creates no
new artifact. Stage 0 was not forced, and no full design was produced.

## Case 6 — architecture: Stage 0 is final

**Request:** a bounded choice with one obvious answer given the stated
constraint.

**Outcome:** Stage 0 concept resolved the choice; no full design was created,
and the Stage-0 output stands as the final artifact.

## Case 7 — architecture review cuts excess design

**Input:** a design doc proposing a bespoke queue abstraction, a compatibility
layer for a consumer that does not exist, and three configurability knobs with
no stated need.

**Outcome:** the design-doc reduction pass reported the unnecessary custom
mechanism, the speculative compatibility layer, and the configurability
unsupported by a named quality attribute. Findings removed surface rather than
asking the author to justify it at greater length.

## Result

Every cheaper route ended with no RFC effect, and the `docs/rfc/` fingerprint is
byte-identical before and after. The warranted path retains every pre-existing
gate. The confinement contract was honoured, with its guidance-not-gate
limitation recorded above rather than overstated.
