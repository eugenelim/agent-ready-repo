# ADR-0152: Confined writes are path-checked on hosts without descriptor walking, and the one race they leave is accepted

- **Status:** Proposed
- **Date:** 2026-10-29
- **Areas:** work-loop, security
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0144 (D2 requires the supervisor to run on Windows); spec `acceptance-authority-and-evidence` (D4 narrows two clauses of its AC-0011 on such hosts); spec `execution-supervisor-attempt-security` (its Accepted Risk grants a worker the same-user authority this race needs); spec `windows-confined-write` (delivers this)

## Decision summary

- **Decision:** On a host without descriptor-relative directory walking but with reparse-point attributes, which in practice means Windows, the confined create, append, and replace operations check every path component, alias form, and the staged file's identity by path before writing, re-check the target and every ancestor's identity after, and report "state unknown" when the re-check fails. Untrusted code refuses on such hosts.
- **Because:** the operations refuse every write on such hosts, so the execution supervisor cannot run full mode on Windows, which ADR-0144 D2 requires.
- **Applies to:** the work-loop skill's confined-mutation helper and the supervisor's untrusted-code admission.
- **Tradeoff accepted:** for trusted runs, a same-user process that swaps an ancestor for a junction between the last check and the commit call can redirect that one write outside the root; the operation reports state unknown when the swap is still in place afterwards, cannot undo it, and misses a swap undone before the re-check.
- **Revisit if:** a worker or launch child stops running as the supervisor's own user, or a standard-library handle-relative open becomes available on Windows.

## Context

The confined-mutation helper binds each ancestor directory to an open
descriptor and creates, links, and renames relative to it. That closes the
window in which an ancestor could be swapped for a link between a check and a
write. The binding needs `dir_fd` and `O_NOFOLLOW`, which Windows does not
provide, so the helper refuses every write there with `denied-unsafe-host`. The
supervisor's first write in `start` therefore fails on Windows.

The architecture's runtime-security primitives already expect that "unsupported
operations fail closed and conformance declares each platform's exact capability
set". A handle-relative design through the NT API would close the race, at the
cost of several hundred lines of `ctypes` that only the Windows CI job could
verify. The path-checked design reuses the reviewed fallback in the repository's
file-safety writer, which already checks a created file's identity and
containment before writing a byte.

That acceptance holds only while every process able to win the race already
holds the supervisor's same-user authority. Untrusted code breaks that
premise, so untrusted runs refuse on such hosts.

`execution-supervisor-attempt-security` accepts that a deliberate worker acts
with the supervisor's full same-user authority and can rewrite the supervisor's
files and store directly. A process able to win this race already holds that
authority, so the race gives it nothing new.

## Decision

- **D1:** On a host where descriptor-relative walking is unavailable and `os.lstat` reports reparse-point attributes, the three confined operations run in a path-checked mode. Before writing, each refuses stream, device, trailing-dot, and prefixed path forms, records every ancestor's identity, refuses links and reparse points, compares case-normalised resolved paths for containment, creates its staging file exclusively, and checks that file's identity, link count, and containment before writing any byte.
- **D2:** After the commit, the operation confirms the target is the regular, singly linked file it wrote, or for append the file it has open, and that every ancestor kept its recorded identity. Any difference raises `denied-rollback-failed`, which callers already treat as state unknown. It never reports success for a write it cannot confirm.
- **D3:** The module reports whether the host's mutations are race-free, so the gap is declared rather than silent. A host with neither descriptor walking nor reparse attributes still refuses.
- **D4:** For trusted runs, the residual race in D2 is accepted. On path-checked hosts this narrows two clauses of `acceptance-authority-and-evidence` AC-0011. "Refuses … identity changes" becomes "refuses identity changes it can observe before the write, and reports state unknown when one is observed after". "A refused or interrupted mutation leaves the prior file intact" no longer holds for a `denied-rollback-failed` late detection, whose bytes may have landed in the root or outside it. Supervisor directory creation, the store directory's rename, and the recovery discard's unlink run by path on such hosts and carry the same race.
- **D5:** On a host whose mutations are not race-free, the supervisor refuses every verb whose code trust is untrusted or cannot be determined: for `start`, the trust its `--code-trust` argument would record; for every other verb, the latest approval pair committed at `HEAD`, where an absent or unparseable approvals file is undetermined. The acceptance in D4 rests on every process able to win the race already holding the supervisor's same-user authority, which untrusted code does not.

## Consequences

**Positive:**
- Full-mode work-loop runs on Windows through the same three operations POSIX uses.
- The weaker guarantee is visible in code, in the architecture page, and here.

**Negative:**
- On Windows, a same-user junction swap timed into one call can redirect that write outside the root.
- Untrusted-code runs are unavailable on Windows.

**Revisit if:** a worker or launch child stops running as the supervisor's own user, or a standard-library handle-relative open becomes available on Windows.

## Confirmation

- **Mode:** lint/CI
- **Signal:** the path-checked confined-mutation suite passes on a simulated host and on the Windows CI job, the capability query reports false there, and untrusted admission refuses.
- **Owner:** eugenelim

## Alternatives considered

- **Handle-relative opens through the NT API.** Rejected for now: several hundred lines of `ctypes` verifiable only on CI, to close a race that needs authority the worker already has.
- **Keep refusing on Windows.** Rejected: ADR-0144 D2 requires the supervisor to run there.
- **Refuse only authority-bearing writes.** Rejected: full mode would still fail on Windows.
