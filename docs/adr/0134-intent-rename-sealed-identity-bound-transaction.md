# ADR-0134: Intent rename uses a sealed transaction with identity-bound recovery

- **Status:** Accepted
- **Date:** 2026-09-29
- **Areas:** product-engineering, workspace, tooling
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0108 (fresh allocation and non-reuse constraints); ADR-0129 (intent filename retirement through tombstones)

## Decision summary

- **Decision:** An intent rename is a sealed retire-and-issue transaction with independently re-derived write authority and filesystem-identity-bound recovery.
- **Because:** measured kills showed that a long-held lock, a parseable record, a digest seal, and byte-equal successor content cannot by themselves prove either completion or ownership.
- **Applies to:** renames that retire one file in `docs/product/intents/`, issue a successor under a fresh ordinal, repoint citations, and update `workspace.toml`.
- **Tradeoff accepted:** the operation carries a durable stage, explicit recovery actions, hard-link identity checks, and more refusal states than a best-effort rename.
- **Revisit if:** the repository gains a portable atomic multi-path transaction or a shared workspace-lock protocol with durable, safely reclaimable ownership.

## Context

An intent rename changes several independently stored facts: the source becomes a tombstone, a successor is created under a newly allocated ordinal, every citation is repointed, and `workspace.toml` changes. The filesystem cannot commit those paths atomically as one unit.

Five predecessor generations were reviewed in prose. Each repair introduced another interaction defect. A sixth design was then written from these measured results:

- `SIGKILL` can strand `.workspace-repair.lock` with a dead owner and no release operation.
- `os.replace` consumes its source and fails with `EXDEV` across devices.
- Path-based creation follows a swapped parent symlink; descriptor-relative no-follow traversal refuses it.
- A mid-copy kill leaves a partial orphan.
- A parseable recovery record may exist before any postimage is staged.
- A digest seal detects damage but does not grant authority when an actor can replace both record and seal.
- Equal successor bytes cannot distinguish this transaction's earlier pass from an independent concurrent admission.
- A retained inode can distinguish the transaction's successor and lock claim from byte-identical foreign files.

The operation must therefore recover after process death without trusting the process-local descriptors or the durable record that survived it. It must also keep the shared workspace lock's hold time limited to the registry read-modify-write.

## Decision

Intent rename will use a sealed retire-and-issue transaction with identity-bound recovery.

- **D1:** The operation never renumbers an intent in place. It allocates the target token's next ordinal, creates a successor, and leaves a tombstone at the vacated source name.
- **D2:** Planning derives a bounded ordered write set from the operator's request and a pinned Git snapshot. Staging writes canonical postimages and then writes a completion seal last. The seal proves stage completion and detects damage; it is not authentication or write authority.
- **D3:** Recovery treats every durable record as untrusted input. It reacquires confined no-follow descriptors, applies fixed parse and resource bounds, rejects duplicate or unknown fields and invalid types, independently re-derives the allowed paths and exact postimage bytes from the operator-supplied request and tombstone date plus the pinned snapshot, and validates every live target before its first destructive act. Record fields, including the date, are comparison data only.
- **D4:** Commit creates the successor by an exclusive hard link to its retained staged inode. It replaces ordinary targets from operation-specific same-directory temporaries. It updates `workspace.toml` last, while holding the shared workspace lock only for that live read-modify-write.
- **D5:** The registry critical section uses a retained `lock.claim`. The shared lock may be cleared after interruption only when both names identify the same inode, the bounded canonical owner PID is verifiably dead, and no alien link state exists. A live, malformed, or foreign lock refuses without mutation.
- **D6:** Forward and backward recovery share one validation barrier. Replaced targets may contain only their independently derived preimage or postimage. The successor and lock claim may occupy only their closed absent, one-link, or owned two-link states. Any alien bytes, inode, link count, entry, path, snapshot, or registry state refuses before mutation.
- **D7:** Cleanup is bounded and restartable. After independently validating an all-before or all-after terminal state, the operation writes a durable cleanup marker before removing the completion seal. A missing or invalid seal never authorizes live-path mutation: without the marker only an independently validated all-before incomplete stage may be discarded; with it only stage cleanup may continue after the terminal live state is revalidated. Cleanup removes only exact operation-owned names through confined descriptor-relative operations. Unknown entries, symlinks, foreign links, or ambiguous records are never swept.

## Decision drivers

- **Crash recovery:** a process killed at any write boundary must leave enough durable evidence to reach the complete rename or the exact pre-rename state.
- **Authority separation:** record and seal bytes may describe a transaction but cannot authorize paths or content.
- **Concurrent-writer safety:** a rename must not overwrite an independently admitted successor or another writer's registry lock.
- **Repository availability:** the shared workspace lock cannot span the transaction because one kill would block all workspace writers.
- **Filesystem confinement:** recovery must remain inside the repository even after every process-local descriptor has been lost.

## Consequences

**Positive:**

- A killed operation has two specified recovery destinations and no permitted third completed state.
- A recomputed seal or modified record cannot widen the allowed write set.
- Byte-identical concurrent successor creation is treated as a conflict rather than mistaken for an idempotent replay.
- The shared workspace lock remains limited to the registry critical section.
- Recovery refuses before mutation when any target or retained identity has become alien.

**Negative:**

- The implementation and test matrix are materially larger than a sequential rename.
- The transaction depends on hard-link identity and must fail closed on platforms where the required semantics cannot be established.
- Recovery is operator-visible and requires the original request to be supplied again.
- Recovery also requires the operator to re-supply the original tombstone date; the durable record may suggest but cannot authorize it.
- A valid stage may remain until an operator chooses forward or backward recovery.

**Revisit if:** the repository gains a portable atomic multi-path transaction or a shared workspace-lock protocol with durable, safely reclaimable ownership.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** the intent-rename suite drives injected interruptions and real `SIGKILL`s at every stage and commit checkpoint, proves both recovery directions, rejects altered records and alien live state before mutation, and verifies owned versus foreign successor and lock inodes.
- **Owner:** Core maintainers

## Alternatives considered

- **Hold the shared workspace lock from allocation through disposal:** rejected because a measured kill strands a lock no repository code can clear, blocking every workspace writer until manual deletion.
- **Stage and replace a fixed `workspace.toml` postimage:** rejected because it would overwrite unrelated valid registry changes made before lock acquisition. The registry instead has one mechanism: a locked live citation-preserving edit.
- **Treat exclusive-create plus byte equality as idempotent successor ownership:** rejected because an independent admission can create identical bytes at the same path. Equal bytes do not identify the writer.
- **Treat a parseable record or matching digest seal as recovery authority:** rejected because staging may be incomplete while the record is parseable, and an altered record with a recomputed seal still matches. Authority is independently re-derived.
- **Create and sweep transaction paths through ordinary path operations:** rejected because a swapped parent symlink escaped the repository in measurement, and a broad sweep could remove another operation's file. Descriptor-relative no-follow access and exact names are required.

## References

- ADR-0108 — fresh identifiers are allocated rather than renumbered or reused.
- ADR-0129 — a vacated intent filename remains as its tombstone.
