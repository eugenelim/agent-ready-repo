# ADR-0160: Concurrent attempts isolate in host-contained plain directories on Git 2.41 or later

- **Status:** Proposed
- **Date:** 2026-11-05
- **Areas:** work-loop, concurrency, security
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0005 D7; ADR-0156 D2
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0156 (the admission rule this completes); ADR-0154 (the product ref results land on); spec `verified-infrastructure-parallelism` (the contract that implements it)

## Context

ADR-0156 admits concurrent `implement-task` attempts only under a verified host
attestation, and D1 requires the host to deny each concurrent attempt the Git
common directory, every shared ref, and the run store. ADR-0156 also keeps
ADR-0005 D7 standing, which says write isolation comes from a Git worktree.

The two cannot both hold for a concurrent attempt:

- A linked worktree reaches its repository through a `.git` file that names
  the common directory. Denied the common directory, an attempt in a worktree
  cannot run Git at all, and allowed it, the attempt can write every shared ref.
- The execution supervisor already owns every Git write for a result
  (ADR-0154), so an attempt does not need Git to produce one.

ADR-0156 D2 names Git 2.38 as the floor for the concurrent path, because
`git merge-tree --write-tree` arrived there. Two further facts surfaced while
specifying the apply:

- `--merge-base`, which pins the merge base to the result's source commit,
  arrived in Git 2.40. Without it Git chooses the base itself.
- `--attr-source`, which stops the checked-out `.gitattributes` from steering
  the merge, arrived in Git 2.41. Without it a `merge=union` line in the
  working tree turns a same-line conflict into a clean merge; a probe on Git
  2.56 reproduced this.

## Decision

> A concurrent attempt runs in a fresh plain directory outside the Git
> directory, the run store, and the work tree, and the concurrent path needs
> Git 2.41 or later. Sequential attempts keep the worktree rule unchanged.

- **D1:** A concurrent attempt's write root is a directory the supervisor creates empty for that attempt alone, outside the Git directory, the Git common directory, the run store, and the work tree, holding no `.git` entry and never reused. The supervisor populates it from the source tree and, after the attempt's process group has ended, reads it back into Git objects itself through the confinement helpers. This supersedes ADR-0005 D7 for concurrent attempts only; every sequential attempt keeps ADR-0005 D7.
- **D2:** The concurrent path needs Git 2.41 or later, so the apply can pin its merge base with `--merge-base` and read attributes only from an empty tree with `--attr-source`. On older Git every task runs on the sequential floor and the run is never refused. This supersedes ADR-0156 D2's Git 2.38 clause only; every other D2 condition stands.

## Consequences

**Positive:**
- ADR-0156 D1's denials are enforceable: nothing in an attempt's write root
  needs the Git common directory, the shared refs, or the run store.
- A worker cannot write a ref, an object, or Git configuration, because it has
  no Git directory to write.
- The merge base and the attribute source are fixed by the supervisor, not by
  the working tree.

**Negative:**
- Each concurrent attempt costs a full export of the source tree into a fresh
  directory, and an ingestion pass afterwards.
- The supervisor now reads a directory a possibly hostile worker wrote, so
  ingestion must refuse links out, special files, and oversized trees.
- Hosts with Git 2.38 to 2.40 run sequentially although ADR-0156 would have
  admitted them.

**Revisit if:** a supported host can contain a linked worktree while denying the shared refs and the run store, or Git gains a way to pin every attribute source, including `info/attributes`, for one command.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** the `verified-infrastructure-parallelism` corpus shows each concurrent attempt directory outside the Git directory, the run store, and the work tree with no `.git` entry, and shows that Git older than 2.41 issues nothing concurrently.
- **Owner:** Core pack maintainers

## Alternatives considered

- **Keep a linked worktree per concurrent attempt:** rejected because a worktree needs the Git common directory that ADR-0156 D1 denies.
- **A full clone per attempt:** rejected because it copies every shared ref and the configuration into a tree the worker controls, and the supervisor would then have to distrust and re-derive all of it.
- **Keep Git 2.38 and refuse any repository that has a `.gitattributes` file:** rejected because it refuses harmless attributes and still leaves the merge base to Git.

## References

- Git release notes 2.38.0 (`merge-tree --write-tree`), 2.40.0 (`--merge-base`), and 2.41.0 (`--attr-source`).
