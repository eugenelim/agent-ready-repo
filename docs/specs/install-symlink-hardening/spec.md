# Spec: install-symlink-hardening

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none new. One symlink policy replaces six; one walk stops
  dereferencing.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Two risk triggers fire: security boundary (file I/O on an
untrusted-input path) and structural (a shared helper replacing six private
copies). `security-reviewer` cannot be dispatched under this session's
no-subagent instruction, so its absence is a NAMED SKIP and the
boundary-matching reasoning is applied inline and recorded in the plan. -->

## Objective

Close a file-exfiltration path in `agentbundle install` that two
independently-defensible layers created between them.

## Acceptance Criteria

- [x] **AC1 — one symlink policy, in one place.** Six direct-directory adapters
  each carried a private ignore callback. They live in
  `build/projections/direct_directory.py` now — the module whose stated job is
  "shared helpers for direct-directory skill projections".

- [x] **AC2 — the permissive rule's hole is closed.** `claude_code` and `codex`
  dropped only symlinks with **absolute** targets, on the stated grounds that
  "absolute symlinks always escape the tree". True, and incomplete: a relative
  symlink escapes just as well. They now drop every symlink.

- [x] **AC3 — dropping relative symlinks costs nothing real.** Measured before
  changing: zero symlinks exist anywhere under `packs/`, and `lint_packs.py`
  rejects any pack that ships one — so the "intra-skill cross-reference"
  capability the permissive rule protected cannot be exercised by a first-party
  pack. The only source of a symlink is an untrusted catalogue, which is exactly
  where preserving it is the hazard.

- [x] **AC4 — the install walk stops reading through links.** `_collect_tree`
  used `Path.is_file()`, which follows symlinks, then `read_bytes()`. A
  preserved link therefore had its *target's* bytes collected and written to an
  adopter's disk under a relpath that passes every path check — the relpath is
  innocent; only the link is not. Symlinked entries are skipped.

- [x] **AC5 — the layers that were right stay untouched.** `build/main.py`'s
  `.apm` and `seeds` copytrees keep `symlinks=True`. Preserving a link there is
  *safe*, precisely because nothing reads the target at that layer — it exists so
  a build does not dereference a pack's symlink into `dist/`. The defect was the
  composition of the two layers, not either one, so the fix is at the read.

- [x] **AC6 — every shape is tested, including the one that used to survive.**
  Absolute, relative-traversal, nested-relative-traversal, and in-tree relative
  links are all asserted dropped; regular files are asserted kept, so the filter
  is not a blanket refusal. A separate test names the relative-traversal case so
  a regression says *which* shape came back.

- [x] **AC7 — a seventh private policy cannot appear.** A test scans every
  adapter module: any `shutil.copytree(` without the shared callback, or any
  surviving private definition, fails.

- [x] **AC8 — released.** 0.36.0 → 0.36.1, with an entry in both changelogs
  stating that no behaviour changes for real packs.

- [x] **AC9 — the sibling entry is narrowed accurately, not closed.**
  `untrusted-catalogue-symlink-exfiltration` named three legs; two are closed
  here. Its remaining scope — gating install-path `render_pack` with `lint_pack`
  — is recorded, along with a note not to "fix" the deliberate `symlinks=True`
  sites.

## Boundaries

### Never do

- Never re-add `symlinks=True` to a direct-directory adapter's `copytree`.
- Never change `build/main.py`'s `.apm`/`seeds` copytrees. AC5 is the reason.

## Testing Strategy

- **TDD** for AC2/AC4/AC6/AC7. **Goal-based** (measurement) for AC3.
