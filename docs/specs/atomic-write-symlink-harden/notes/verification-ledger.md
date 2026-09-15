# Verification ledger — atomic-write-symlink-harden

Execution observations. The spec and plan are frozen; what happened while
running against them is recorded here.

## T1 — the hardened helper

**Red before green.** Against the unchanged `_atomic_write`, 5 of the 8 new
cases failed, including both mutation proofs. The other 3 passed, because the
current code already had the properties they guard — they are regression
guards, not new behaviour.

**Mutation proofs.** Each mutation was applied to the shipped implementation,
the suite run, and the implementation restored:

| Mutation | Test that went red | Result |
| --- | --- | --- |
| Staging name back to `dest.name + ".abtmp"` | legacy-path, staging-collision, distinct-path | 3 red |
| `O_EXCL` → `O_TRUNC` | staging-collision | 1 red |
| Mode `0o666` → `0o600` | umask-derived mode | 1 red |

Restored implementation: 8/8 green. No mutation left the suite green, so no
case in this class is a control that cannot fail.

**Full unit suite.** `python3 -m pytest packages/agentbundle/tests/unit/ -q` —
3013 tests collected, exit 0, no failure or error markers in the run output. No
existing test was modified.

**Real CLI run.** `python3 -m agentbundle catalogue init <tmp> --name qacat …
--format json`, run against the hardened code and against `HEAD`'s code, with
`PYTHONPATH` pointed at this worktree (the editable install resolves to the main
checkout, not here — the run was confirmed to import from
`…/atomic-write-harden/packages/agentbundle/agentbundle` before being trusted).

- Both runs exit 0 and report `ok: true`.
- Identical created-file list, 21 paths, same order.
- Identical summary: `create 21, already_present 0, conflict 0`.
- `diff -r` between the two produced trees: 0 lines.
- Every file in both trees is mode `0o644`, so the permission property holds
  through the CLI and not only in the unit test.

**Divergence from the frozen plan.** The plan's T1 stub writes
`def __enter__(self) -> "_FailingHandle":`. Under `from __future__ import
annotations`, `ruff` rejects the quotes (UP037), so the shipped test drops them:
`def __enter__(self) -> _FailingHandle:`. One character, no behaviour change,
and not worth a contract amendment — recorded here instead. A post-approval edit
to `plan.md` that fixed it was reverted to restore the sealed baseline, verified
by recomputing the canonical hash (`2885bf7f9b25`, matching the pin).
