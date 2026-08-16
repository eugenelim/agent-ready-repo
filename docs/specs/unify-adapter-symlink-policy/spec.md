# Spec: unify-adapter-symlink-policy

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none new. Six private copies of one policy become one shared
  definition, and the four that had drifted move back to the specified rule.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Two risk triggers: security boundary (symlink handling on the
untrusted-catalogue install path) and structural (a shared definition replacing
six private ones). `security-reviewer` is a NAMED SKIP under this session's
no-subagent instruction; reasoning is inline in the plan. -->

## Objective

Six direct-directory adapters each carried a private symlink callback, and the
copies had drifted into two policies. Settle on the one the repo already
specified, and put it in one place so it cannot drift again.

## Acceptance Criteria

- [x] **AC1 — pass-through is the policy, and it is the specified one.**
  `docs/specs/codex-native-skills/spec.md`: *"the symlink-pass-through is the
  path-traversal-safety invariant; never resolve a symlink to its target at
  projection time."* `cursor`, `copilot`, `gemini` and `kiro` were dropping every
  symlink; they now drop absolute targets and preserve relative ones, matching
  `claude_code` and `codex`.

- [x] **AC2 — one definition.** `ignore_absolute_symlinks` lives in
  `build/projections/direct_directory.py`, the module whose stated job is shared
  helpers for direct-directory projections. No adapter defines its own.

- [x] **AC3 — `symlinks=True` on every direct-directory `copytree`.** Without it
  the callback is moot: `copytree` dereferences, and preservation silently
  becomes resolution — the exact failure the invariant names.

- [x] **AC4 — the change is behaviour-preserving under existing coverage.**
  Every existing symlink fixture uses an ABSOLUTE target (`/etc/passwd`, or a
  resolved `tmp_path`), which both policies drop. `tests/build_pipeline/` and
  `test_nested_symlink_hardening.py` pass unchanged. The only behaviour that
  moves is the relative case, which no test exercised and no pack ships.

- [x] **AC5 — the newly-uniform guarantee is pinned.** A test asserts an absolute
  link is dropped, a relative in-tree link survives *as a link*, and a relative
  upward link survives with its target unresolved — the distinction the invariant
  turns on. A second asserts no regular file in the output carries the
  out-of-tree bytes, which is what would happen if `symlinks=True` were lost.

- [x] **AC6 — a seventh private policy cannot appear, and neither can a lost
  `symlinks=True`.** A guard inspects each adapter's `copytree` **call**, not the
  file. Mutation-verified twice: a file-level check passed while one call had lost
  the flag (these modules contain other `copytree` calls); the call-level check
  fails.

- [x] **AC7 — safe because the read is already closed.** `spec/install-symlink-
  hardening` made `render._collect_tree` skip symlinked entries, so a preserved
  link cannot become a file on an adopter's disk. Re-admitting relative links to
  projections without that fix would have been the wrong order.

- [x] **AC8 — the backlog entry is closed and the sibling spec updated.**

## Boundaries

### Never do

- Never drop `symlinks=True` from a direct-directory `copytree`. AC3/AC6.
- Never resolve a symlink at projection time. That is the invariant itself.

## Testing Strategy

- **TDD + mutation** for AC5/AC6; **regression** for AC4 (existing suites must
  pass untouched — that is the evidence the change is behaviour-preserving).
