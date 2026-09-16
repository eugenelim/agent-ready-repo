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

## Amendment: the requested mode is `0o644`, not `0o666`

CodeQL on PR #1327 raised one high-severity alert,
`py/overly-permissive-file` at `initialise.py:470`: "Overly permissive mask in
open sets file to world writable."

Measured before deciding, one directory per umask:

| umask | `Path.write_bytes` (the code being replaced) | `os.open(…, 0o666)` |
| --- | --- | --- |
| `022` | `0o644` | `0o644` |
| `077` | `0o600` | `0o600` |
| `000` | `0o666` | `0o666` |

So the alert was not a regression — `Path.write_bytes` requests `0o666` too, and
CodeQL could not see it because the literal lives inside CPython. It was,
however, a true statement about the idiom: under a null umask both the old and
the new code produce a world-writable file.

The owner chose to tighten first. That closed the world-**write** half and then
moved the alert rather than clearing it.

**The first attempt, `0o644`, was wrong, and a review round caught it.** It
closes the alert, but it also drops the group-write bit — so under umask `002`,
the usual setting on a shared-group system, a catalogue tree a team shares stops
being group-editable. The shipped mode is `0o664`, which drops only the
other-write bit. Measured across six umasks against a control file written by
`Path.write_bytes` in the same directory:

| umask | old (`write_bytes`) | shipped (`0o664`) |
| --- | --- | --- |
| `022` | `0o644` | `0o644` |
| `002` | `0o664` | `0o664` |
| `077` | `0o600` | `0o600` |
| `027` | `0o640` | `0o640` |
| `007` | `0o660` | `0o660` |
| `000` | `0o666` | `0o664` |

Identical at every ordinary umask; different only where the old code was
world-writable.

The acceptance criterion was amended to match — "the bits `Path.write_bytes`
produces, with the other-write bit cleared" — and the test's comparison value
became `stat.S_IMODE(control.stat().st_mode) & 0o664`.

**The test had to start driving the umask.** The runner's own umask is `022`,
where `0o644` and `0o664` produce identical files, so a tightening mutation was
invisible. The mode case is now parametrized over all six umasks above. Three
mode mutations were then each shown to red it:

| Mutation | Umasks that red |
| --- | --- |
| mode → `0o644` | `007`, `000`, and one more (3 of 6) |
| mode → `0o666` | `000` (1 of 6) |
| mode → `0o600` | 5 of 6 |

Before parametrization, the `0o644` mutation redded nothing.

The plan's § Design decisions was corrected in place. That section is working
material under the plan's own contract, not pinned content, so the correction
needs no amendment — but it does move `plan.md` off the hash the cohort pinned
at `schedule`, and `loop-engine transition … wave-complete` runs
`schedule check-current`, so it refused. An earlier note here claimed no further
check reads that hash; that was wrong. The documented cohort recovery was run —
restore `Status: Approved` in both files, `loop-cohort reset`, `init`,
`approve-plan`, `schedule`, restore the statuses — and the wave pointer walked
forward again. The canonical hash was confirmed to exclude the `Status:` line,
so restoring the statuses afterwards does not disturb the new pin.


## The alert moved, and had to be suppressed after all

Requesting `0o664` changed CodeQL's message from "sets file to world writable"
to "**sets file to world readable**", same rule, same line. The rule objects to
the other-read bit as well as other-write, so the only modes that clear it are
owner-only — which is the `0o600` regression already rejected for breaking a
catalogue that is served, group-shared, or read by another service account.

The remaining alert is true about the literal and false about this code. A
catalogue is a published artifact: its files were world-readable at `0644`
before this change too, because `Path.write_bytes` requests `0o666`. Nothing
about readability changed here.

What did change is the part that mattered. Under a null umask:

| | old | shipped |
| --- | --- | --- |
| mode | `0o666` | `0o664` |
| world-writable | yes | **no** |
| world-readable | yes | yes |

The owner authorised a line-level suppression carrying that reasoning. It is
this repository's first — a search for `codeql[` and `lgtm[` across the tree
found none before it. The marker sits on the line immediately above the `os.open`
call, because CodeQL honours it only on the alert line or the one directly above;
the explanation sits above the marker.

There is no `.github/codeql-config.yml`; scoping the query at repository level
would have been a policy change affecting every file, which is why the
suppression is line-local.
## One suite run was spoiled by the operator, not by the code

The final full-suite run took 1696s instead of the usual ~200s and came back
`1 failed, 3016 passed, 3 skipped, 31 subtests`. The failure was
`test_local_exclude_git_cache.py::test_distinct_questions_are_not_conflated`.

Cause: a `git rev-parse --git-common-dir` inside that test's temporary repo hung
for 51 minutes. It was a child of this run's own pytest (`ppid` matched), not a
peer session. I killed the hung `git` to let the suite continue, which is what
failed the test around it.

Re-run in isolation immediately afterwards: `3 passed in 0.88s`. The file is not
in this change's diff, and the two preceding full runs of the same suite passed
at 164s and 254s. So the failing run is an artifact of the intervention, and the
isolated re-run is evidence about a different question — whether that test passes
— not a re-roll of the run that failed.

Standing evidence for the suite is therefore the `0o664` run recorded above:
`3017 passed, 3 skipped, 31 subtests, 164.38s, exit 0`. The only change since is
a comment.
