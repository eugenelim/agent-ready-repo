# Spec: local-scope-install-guards

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** `install --scope local` refuses three previously-accepted cases.
  Behaviour change; released as a minor.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Two risk triggers: security boundary (file I/O, ownership) and
public-interface change (installs that used to succeed now refuse).
`security-reviewer` is a NAMED SKIP under this session's no-subagent
instruction; reasoning is inline in the plan. Delivers AC10 and AC12b of
spec/local-scope-install, which shipped with both deferred. -->

## Objective

Local scope promises to leave no trace: files are git-invisible via an exclude
block, and uninstall restores the tree exactly. Three cases broke that promise
silently. Close them, and refuse before writing anything.

## Acceptance Criteria

- [x] **AC1 — a git-tracked target is refused (AC10a).** Writing over it makes
  the file dirty in git while the exclude block claims it is invisible, and
  uninstall would delete a file the repository owns.

- [x] **AC2 — the tracked check cannot be fooled by a glob metacharacter.**
  `git ls-files` runs with `--literal-pathspecs`. Without it a projected path
  containing `*`, `?` or `[` is read as a pathspec pattern, so `a[0].md` could
  match nothing while a real tracked file of that name exists — a false negative
  on a guard whose only job is to refuse.

- [x] **AC3 — an untracked, unowned target is refused (AC10b).** A file that
  exists and has no ownership record in the repo, user, or local state.

- [x] **AC4 — identical content does not grant ownership.** The case the
  original AC names explicitly, and the one most likely to be "simplified" away
  later: a pre-existing file whose bytes match the projection is still not ours,
  and uninstall would delete it. Tested by installing once to capture the exact
  projected bytes, uninstalling, planting those bytes, and asserting the refusal.

- [x] **AC5 — a path owned by a different repo-scope pack is refused (AC12b).**
  The existing mutual exclusion is pack-level, so it only catches the same pack
  at both scopes. Two *different* packs colliding on one projected path passed,
  and the local install silently took ownership of the repo pack's file.

- [x] **AC6 — all three refusals are `--force`-immune.** `--force` cannot make a
  deletion reversible. Asserted for the tracked case; the messages say so.

- [x] **AC7 — a refusal leaves no footprint.** It runs before the exclude block
  and before any file write. Asserted: no exclude block, no local state file,
  and the pre-existing file is byte-unchanged.

- [x] **AC8 — the guards do not refuse the ordinary cases.** A clean repo still
  installs and stays git-invisible; reinstalling over files this tool owns is
  not refused. Without this pair, AC3 would reject every legitimate reinstall —
  the files it inspects are the ones we put there.

- [x] **AC9 — mutation-verified.** Disabling the refusal branch fails all four
  AC10 tests; restoring passes all sixteen.

- [x] **AC10 — the deferred ACs are closed at source.** `spec/local-scope-install`
  AC10 and AC12b are checked, and both backlog entries removed.

- [x] **AC11 — released.** 0.36.2 → 0.37.0 (minor: installs that used to
  succeed now refuse), with an entry in both changelogs.

## Boundaries

### Never do

- Never treat content equality as ownership. AC4 is the rail.
- Never drop `--literal-pathspecs`. AC2 is the rail.
- Never let a refusal write first and roll back. Refuse before the exclude block.

## Testing Strategy

- **TDD + mutation**, integration-level against a real git repo and the fixture
  catalogue — these guards are about git and filesystem state, so a unit test
  with a mocked git would prove nothing.
