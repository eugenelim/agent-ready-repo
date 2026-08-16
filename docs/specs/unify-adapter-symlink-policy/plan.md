# Plan: unify-adapter-symlink-policy

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `build/projections/direct_directory.py` (the one definition).
- The six adapters.
- `tests/unit/test_adapter_symlink_policy.py` (new).
- `docs/specs/install-symlink-hardening/spec.md`, `workspace.toml`.

**What demonstrates done**
- Existing adapter + hardening suites unchanged and green; new tests;
  mutation on the guard; `make ci`.

**What I am NOT changing**
- `render._collect_tree` — already correct, and it is what makes this safe.
- `build/main.py`'s `.apm`/`seeds` copytrees — same invariant, already right.
- `lint_packs.py`'s refusal of packs that ship symlinks.

## Security reasoning (inline — `security-reviewer` is a named skip)

- **The direction of this change is toward *more* preserved symlinks**, which
  looks like the wrong direction until you separate the two operations.
  *Resolving* a link materialises its target's bytes into the projection — that
  is the exfiltration. *Preserving* it copies a pointer. The invariant forbids
  the first, and this change makes all six adapters obey it.
- **Defence in depth is intact and now correctly layered.** Projection preserves
  (never materialises); the install-side read refuses to follow (never
  materialises either). Both layers now decline to produce out-of-tree bytes,
  where before four adapters solved it by deletion and two by preservation.
- **What a preserved relative link can still do:** appear in an adopter's tree as
  a dangling or upward-pointing link. It carries no content, `_collect_tree` will
  not read it, and `lint_packs` refuses any first-party pack that ships one. The
  residual is a visible artefact, not a disclosure.
- **Order mattered.** Doing this before `install-symlink-hardening` closed the
  read would have widened a live hole. That is why the first attempt was reverted
  rather than pushed through.

## Declined patterns

- **Tempted:** keep the strict policy and amend the invariant instead — it is the
  simpler rule and nothing ships symlinks. **Declined:** the operator ruled for
  consistency with the stated invariant, and the invariant's reasoning is sound
  once resolve-vs-preserve is separated. Amending a Shipped spec's security
  invariant to match four files that drifted is the wrong direction of fit.
- **Tempted:** assert `"symlinks=True" in source` per adapter. **Declined:** it
  passes while a specific call has lost the flag. Verified by mutation, twice —
  the first version of my own guard had this bug.

## Anchor-test sweep

- `tests/build_pipeline/test_adapter_codex.py::test_symlink_pass_through` — the
  test that caught the first attempt; passes unchanged, as it must.
- `tests/unit/test_nested_symlink_hardening.py` — pins the absolute case for four
  adapters; passes unchanged (its fixture is `/etc/passwd`).
- `tests/build_pipeline/test_adapter_cursor.py::test_nested_symlink_not_reproduced`
  — asserts the target is not copied; still true, since preservation copies no
  content.

## Verification log

- **AC1–AC3** six adapters import one definition; each direct-directory
  `copytree` carries `symlinks=True`.
- **AC4** `tests/build_pipeline/` + `test_nested_symlink_hardening.py` green with
  no edits — the evidence the change is behaviour-preserving under existing cover.
- **AC5/AC6** 5 new tests; mutation on the guard fails as intended after the fix
  and (revealingly) passed before it.
- **REVIEW** `adversarial-reviewer` and `security-reviewer` = named skips.
