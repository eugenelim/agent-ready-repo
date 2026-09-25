# Verification ledger — catalogue package sync

Manual QA for AC-0099 and AC-0100, run 2026-09-24 against the implementation
at T8. Every command below ran against a constructed vendored fixture. None
ran against this worktree, which § Agent Rules § Never do forbids: the
worktree is this machine's editable install root, and manual QA is exactly
where an unverified refusal would write for real.

## Fixture

`agentbundle catalogue init <t9>/derived --source . --preset self-hosted
--tooling vendored --pack core` produced a 890-file derived tree carrying both
halves of the `agentbundle` destination — `.agentbundle/tooling/agentbundle/`
and `.agentbundle/tooling/packs/` — and **no `.git`**. That last fact is what
makes the fixture discriminating: `_detect_editable_source` is bounded by an
enclosing git repository, so AC-0083 input 1 is blind here and only input 2
can fire.

One vendored file was then edited by hand, to give the plan something to say.

## AC-0099 — a scoped apply writes exactly what its plan named

`catalogue sync <target> --source . --tooling vendored --package agentbundle
--dry-run` printed 239 `would-update` rows, **every one** under
`.agentbundle/tooling/`. Zero rows named a pack, profile, guide or
derivation-wide path, so `--package` scopes as AC-0081 requires.

Its counts line read `would-update=888 … compared=889 uncompared=0`. The gap
between 888 counted and 239 printed is not a defect: AC-0088 preserves phase
2's convention that the seven counts stay computed over the **full replayed
selection** while the printed rows are scope-narrowed.

The apply then ran with `--yes` and exited 0, reporting `tree-modified: yes`.

## AC-0089 — the discriminator, observed on two runs

Re-running the same apply exited **1** and reported `tree-modified: no`.

That is the pair the field exists for. Both runs end non-zero-or-zero on
different rows, and only the field distinguishes them: the first changed the
tree, the second found its companion destination occupied by the first run's
own output, declined it per AC-0070, and changed nothing. A caller deciding
whether a retry is safe reads `no` and stops. Before this phase, both runs
looked the same from the exit code alone.

The companion itself landed as `version.upstream.py` beside the adopter's
edited `version.py`, which is AC-0034's non-replacing publish working.

## AC-0100 — the self-replacement refusal, against a real tree

The fixture's own vendored engine was put on `PYTHONPATH` and used to run the
sync, so the running `agentbundle` resolved to
`<target>/.agentbundle/tooling/agentbundle/agentbundle/__init__.py` — the
target supplying the running engine, which is the condition AC-0083 names.

    EXIT=3
    error: refusing to sync the agentbundle package: the running agentbundle
    executes from this target's vendored tooling root

A sha256 walk of all 951 files was taken before and after a second refusing
run: **identical**. The refusal writes nothing.

This is input 2 alone. The fixture carries no `.git`, so input 1 returned
nothing — which is precisely the fail-open this phase added input 2 to close,
now demonstrated on a real tree rather than argued from the detector's source.

## What the plan-versus-walk comparison cannot discriminate

Recorded because this ledger's AC-0099 evidence looked conclusive and was not.
Comparing the printed plan against a before/after walk agrees **for the wrong
reason** when the run's scope is wider than the flag asked for: an unscoped run
prints an unscoped plan and then faithfully writes it, so plan and walk match
while `--package` has been ignored entirely.

That is exactly the defect adversarial review found after this ledger was
first written — `_run_apply` declared `package` and never read it, so an apply
scoped `--package credbroker` rewrote the whole tree while `--dry-run` scoped
correctly. Nothing in this ledger could see it.

The discriminating artifact is at the command boundary, not here:
`test_apply_package_scope_reaches_the_write_set_at_the_command_boundary` drives
`--package` through `run()` on an apply and asserts the resolved value reaches
the write-set selector. That is what would have failed before the repair.

Its escape assertion — nothing admitted outside the destination — is currently
**vacuous**, because that fixture's source plans no path under
`packages/credbroker/`, so the admitted set is empty. It still guards the
regression, since an unscoped run would make the set non-empty and fail it, but
it does not establish that the scope admits the right paths. The test asserts
its own emptiness so the vacuity is visible rather than assumed.

## A sixth release surface, found by CI and not by this ledger

The release-surface derivation reported five surfaces and AC-0097 quantified
over them. It missed a sixth: `tests/roster/test_okf_catalogue_discovery.py`
pins the release version and asserts **position** — that the topmost changelog
and readme headings name it — so the 0.50.0 bump left it asserting 0.49.0 and
the roster suite failed.

Nothing run locally could have caught it. The unit suite is scoped to
`packages/agentbundle/tests/`, and the roster suite is outside that path; the
five surfaces the derivation did report are all inert text, so no test
exercised them. It took a dispatch-only CI workflow.

The surface is now in the derivation, which is the fix that generalises: the
next bump reads six, not five. The residue is that the derivation's list is
maintained by hand, so a seventh surface added upstream is still silent — the
script's own docstring says so.

## What this ledger does not establish

- The `credbroker` destination was not exercised end to end. The fixture
  selects `--pack core`, not `credential-brokers`, so that destination was
  never present. Its behaviour rests on unit coverage.
- AC-0083 input 1 was not exercised end to end either. Doing so needs a target
  that is both a git repository and an editable install root, which this
  fixture deliberately is not.
- No run here measured the AC-0076 snapshot bound against the widened write
  set. The spec carries that as a follow-on.
