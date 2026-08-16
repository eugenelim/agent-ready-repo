# Spec: install-symlink-hardening

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none new. One walk stops dereferencing symlinks.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Risk trigger: security boundary (file I/O on an untrusted-input
path). `security-reviewer` cannot be dispatched under this session's no-subagent
instruction, so its absence is a NAMED SKIP and the boundary-matching reasoning
is applied inline and recorded in the plan. -->

## Objective

Close the file-exfiltration primitive in `agentbundle install`: a symlink in a
rendered projection had its **target's** bytes read and written to an adopter's
disk under the link's own, innocent-looking relpath.

## Acceptance Criteria

- [x] **AC1 — `_collect_tree` does not read through a symlink.** It used
  `Path.is_file()`, which follows links, then `read_bytes()`. Symlinked entries
  are now skipped, so no target's bytes are collected. This is the point at which
  out-of-tree content actually becomes a file on the adopter's machine, so it is
  where the primitive dies.

- [x] **AC2 — projection is deliberately NOT changed.**
  `docs/specs/codex-native-skills/spec.md` requires
  `copytree(..., symlinks=True)` for every direct-directory projection and states
  that "the symlink-pass-through is the path-traversal-safety invariant; never
  resolve a symlink to its target at projection time".
  `test_adapter_codex.py::test_symlink_pass_through` pins it. Preserving a link
  is safe *because* nothing reads the target at that layer; `build/main.py`'s
  `.apm` and `seeds` copytrees pass `symlinks=True` for the same reason.

  Two layers, each correct alone. The composition was the defect, so the fix is
  at the read.

- [x] **AC3 — every symlink shape is covered, not just the absolute one.**
  Absolute link, relative traversal, and a symlinked *directory* (which `rglob`
  descends into, giving the primitive more reach) are each asserted to
  contribute nothing. Regular files are asserted still collected, so the skip is
  not a blanket refusal.

- [x] **AC4 — the attempt to unify adapter symlink policy was reverted, and why
  is recorded.** This spec first tried the backlog entry's proposal — lift the
  strict skip-every-symlink helper into `direct_directory.py` and adopt it in all
  six adapters. It failed `test_symlink_pass_through`, which surfaced AC2's
  invariant. The entry's premise was inverted: the four adapters that drop every
  symlink are the ones diverging from the spec, not the two that preserve them.
  Recorded as `adapter-symlink-policy-divergence`, which needs a ruling on which
  policy the invariant should state before any code moves.

- [x] **AC5 — released.** 0.36.0 → 0.36.1 with an entry in both changelogs.

- [x] **AC6 — the backlog reflects reality.**
  `nested-symlink-install-hardening` is replaced by
  `adapter-symlink-policy-divergence` (re-scoped around the conflict it hit), and
  `untrusted-catalogue-symlink-exfiltration` records that the read is closed
  while the `lint_pack` install gate remains.

## Boundaries

### Never do

- Never make projection resolve or drop symlinks without first amending the
  `codex-native-skills` invariant. AC2 is the reason.
- Never change `build/main.py`'s `.apm`/`seeds` copytrees.

## Testing Strategy

- **TDD** for AC1/AC3.
