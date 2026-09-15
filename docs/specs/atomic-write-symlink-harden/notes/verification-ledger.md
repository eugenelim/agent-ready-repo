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

## T2 — the release surfaces

`0.46.0` → `0.46.1`, a patch bump, checked against `origin/main` immediately
before the surfaces were edited and again before the PR opened; main carried
`0.46.0` both times (`50bc1381c`).

- `tests/roster/test_okf_catalogue_discovery.py` — 5 passed in 2.93s.
- `tools/test_build_site_routing.py` — 94 passed, 1 skipped, in 6.02s. This is
  what sees the blank line required around every `## [` heading.
- The six surfaces read `0.46.1` by inspection: `version.py`, `pyproject.toml`,
  the roster `expected` literal, and the topmost headings of the package
  changelog, `docs/product/changelog.md`, and `README-pypi.md`.

## Post-implementation review

Three reviewers on the diff, run as independent Codex sessions.

**Round 1.** The adversarial pass raised one Concern — `os.fdopen` can fail
before taking ownership of the descriptor `os.open` returned, leaking it. The
quality pass raised three Concerns and one Nit. The security pass was clean.

All four Concerns were repaired: the descriptor is now closed explicitly if
`os.fdopen` raises; the two failure tests raise a sentinel instance and assert
`caught.value is sentinel` rather than only the type; and a failed cleanup
attaches an `add_note` naming the leftover staging path instead of vanishing.

**Round 2** checked only those repairs and returned clean.

**A discarded run.** The first security dispatch read a diff generated with
`git diff origin/main` rather than from the merge base, so it contained
reverse-diffs of six commits that had landed on main — `packages/AGENTS.md`,
`tests/AGENTS.md` and others appeared as deletions this change did not make.
That run returned clean, but on the wrong input, so it was discarded rather than
counted. Its artifact is kept as `7-DISCARDED-polluted-diff.txt`. The re-run
against a merge-base diff also returned clean.

## Mutation evidence, complete

Six mutations, each applied to the shipped implementation and then reverted:

| Mutation | Guard that went red |
| --- | --- |
| Staging name back to `dest.name + ".abtmp"` | legacy-path, staging-collision, distinct-path (3) |
| `O_EXCL` → `O_TRUNC` | staging-collision |
| Mode `0o666` → `0o600` | umask-derived mode |
| `os.close(fd)` dropped on `os.fdopen` failure | descriptor-closed |
| `exc.add_note(...)` dropped | cleanup-names-the-leftover |
| Re-raise a fresh `OSError` instead of propagating | both failure stages, descriptor-closed, cleanup-note (4) |

No mutation left the suite green. Restored implementation: 10/10 in the class,
and the full unit suite exits 0.

## A gate proven able to fail

`tools/lint-catalogue-curation-guard.py --base origin/main` returns `ok`, and
its path-gate layer is documented to skip silently on a local run. The commit
message was therefore amended to strip the `Engine-Change-RFC:` trailer and the
guard re-run: it failed, naming all five protected-tree paths. The trailer was
restored and the guard re-run green. The green result is the gate passing, not
the gate skipping.
