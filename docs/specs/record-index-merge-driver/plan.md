# Plan: Record-index merge driver

- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)

## Approach

One existing suite gains one rail, `.gitattributes` gains two anchored lines,
and three prose surfaces that state the old narrower rule are corrected.
Nothing new is created: `tools/test_gitattributes_merge_driver.py` already runs
in `gate-main` and already holds a CI-parity disposition, so the widened
equality inherits its enforcement and its local route.

The record-index rail is read out of the `build-check` chain rather than
written down. `test_spawned_script_paths_in_order` in
`tools/test_build_gate_chain.py` already establishes the harness —
`mock.patch.object(gc.subprocess, "run", …)` around `gc.build_check(...)`,
collecting each step's argv — so the rail reuses that mechanism instead of
introducing a second way to inspect the chain.

## Constraints

- The suite runs inside `gate-main`, which has a stated budget concern for the
  two merge-driver steps (`.github/workflows/build-check.yml:75`). T1 and T2
  are in-process and hermetic: no repository copy, no git operation, no
  `agentbundle` invocation. T4 does add cost the existing suite did not carry —
  a second clone plus two merge attempts and one regeneration over the full
  record corpus — so measure that delta when the case lands and record it in the
  verification ledger rather than assuming the suite absorbs it.
- T2's fixture must carry explicit record dates and pin the rendered date
  cell. The reason is the record-date fallback in the spec's Assumptions; the
  derivation is in Design decisions below.
- `AGENTS.local.md` is 58 lines against the 60-line cap `MAX_ROOT_LOCAL_LINES`
  in `tools/lint-agents-md.py:30`, enforced by `.github/workflows/docs.yml`,
  which this change triggers through its `docs/**` paths. T4 writes into two of
  its sections, so author the prose to fit — consolidate the existing sentences
  rather than appending to them.
- `.gitattributes` lines land at end of file. The `binary` macro earlier in the
  file expands to `-merge`, and a later line wins.

## Construction tests

Every test below lives in `tools/test_gitattributes_merge_driver.py` except
T4's, which lives in `tools/test_merge_driver_behaviour.py`.

**Integration tests:** T4's convergence case, which drives a real merge in a
real clone.

**Manual verification:** T3's over- and under-scope mutation check, recorded in
the verification ledger with the command run and the observed failure message;
and T4's wall-clock delta for the behaviour suite, measured before and after its
new case and recorded in the same ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current architecture / `.gitattributes` comment header | T3 | Header states the union rule, names both oracles, still names the enforcing suite, and lists the ineligible paths | `docs/specs/README.md` appears in the ineligible list, both oracles are named, and `tools/test_gitattributes_merge_driver.py` is still named as the enforcing suite |
| Current architecture / `tools/test_gitattributes_merge_driver.py` module docstring | T3 | Docstring names both spec paths and the union the assertion measures | Both paths resolve and the equality described matches the assertion below it |
| Current architecture / `Makefile` `bootstrap-git` target | T3 | All four strings describe a multi-generator driver | None names `make build-self` as the sole regenerator |
| Current architecture / `tools/test_merge_driver_behaviour.py` module docstring | T4 | Docstring names both specs and disambiguates the two AC4s | Both spec paths appear and each convergence test's criterion is unambiguous |
| Current architecture / `.github/workflows/build-check.yml` merge-driver comments | T3, T4 | Comment names this spec and the union rule | Comment cites this spec; both step-name strings unchanged, so `tools/lint-ci-parity.py:377-380` still resolves |
| Maintainer procedure / `AGENTS.local.md` § Worktree bootstrap | T4 | The sentence no longer scopes the without-bootstrap consequence to projections | Sentence covers both generators |
| Maintainer procedure / `AGENTS.local.md` § Landing changes | T4 | The sentence beginning "Self-host projections carry `merge=regen`" describes the widened set; both regeneration commands present | That sentence covers both generators, and each command runs to exit 0 when pasted from the repository root |

## Design (LLD)

### Design decisions

**Why one equality and not two.** Stated in the spec's Boundaries; the plan
consequence is that `rail_set()` grows a union member and the assertion itself
is untouched.

**Why the rail is read from the chain, not from the record directories.** The
covered set has to track what `gate-main` runs. Globbing `docs/*/README.md` or
listing the two paths would stay green after a gate step is renamed or dropped,
leaving the driver on a path nothing regenerates. Reading `--check <dir>` out of
the chain's argv means removing the gate step removes the path from the covered
set, which then reds the equality as over-scope — the correct signal, and the
property AC2 states.

**Why the derivation is split from the collection.** AC2 quantifies over chain
shapes that do not exist in this repository — a chain with no record-index step,
and a chain with three. Those are only reachable if the mapping from argv to
README paths is a pure function the test can call with a constructed list, so
the collection harness and the mapping are separate.

**Why the synthetic fixture pins its date cell.** The spec's Assumptions record
that a record with no `Date` renders an empty date cell on both sides of a
generate-then-check, so such a fixture passes while proving nothing. Asserting
the rendered cell equals the record's literal `Date:` value is what
distinguishes a fixture reading its own records from one that has silently
degraded.

### Dependencies & integration

No new dependency. `unittest.mock` and `importlib` are stdlib; `pytest` is
already this suite's runner.

## Tasks

### T1: The record-index rail set is derived from the gate chain

**Depends on:** none

**Touches:** tools/test_gitattributes_merge_driver.py

**Tests:**
- AC2: fed a constructed argv list with no `index-records.py` step, the mapping
  returns the empty set. `stub: true`
- AC2: fed a constructed argv list carrying `index-records.py --check <dir>`
  for three distinct directories, the mapping returns exactly those three
  `<dir>/README.md` paths.
- AC2: driven by the real chain's collected argv, the mapping returns
  `{docs/adr/README.md, docs/rfc/README.md}`.

**Approach:**
- Add a pure function mapping a list of argv lists to a set of README paths,
  and a separate helper that collects the real chain's argv using the
  `mock.patch.object(gc.subprocess, "run", …)` harness
  `test_spawned_script_paths_in_order` establishes.

**Done when:** the three assertions above are green.

### T2: `index-records.py --check` guards the README and can report clean

**Depends on:** none

**Touches:** tools/test_gitattributes_merge_driver.py

**Tests:**
- AC3: against a synthetic record directory whose `README.md` was produced by
  the same script, `--check` exits 0. `stub: true`
- AC3: the generated table's date cell equals the record's literal `Date:`
  value, so the fixture is reading its own records rather than rendering the
  empty cell a dateless record would produce.
- AC3: after changing only `README.md` in that directory, `--check` exits
  non-zero and its combined output names that `README.md`.

**Approach:**
- Build the directory under `tmp_path` holding one record with an explicit
  `Date:` field, and generate its `README.md` by invoking the script without
  `--check`, so the clean state is the script's own output.

**Done when:** all three assertions are green, and the date-cell assertion fails
when the record's `Date:` field is removed.

### T3: The AC1 equality covers the record-index rail

**Depends on:** T1, T2

**Touches:** tools/test_gitattributes_merge_driver.py, .gitattributes, .github/workflows/build-check.yml, Makefile

**Tests:**
- AC1: `rail_set()` includes both README paths, and the existing
  `test_merge_regen_set_equals_gate_covered_set` is green with the two new
  `.gitattributes` lines present.

**Approach:**
- Union T1's derived set into `rail_set()` alongside the existing behavioural,
  special and runtime members.
- Append `docs/adr/README.md merge=regen` and `docs/rfc/README.md merge=regen`
  at end of `.gitattributes`. Both carry a directory separator, so neither
  matches at another depth.
- Rewrite the `.gitattributes` comment header and the module docstring per the
  durable-output map, and correct the `build-check.yml` comment above the two
  merge-driver steps. Leave both step-name strings alone: they are pinned as
  literal dict keys at `tools/lint-ci-parity.py:377-380`.
- Correct the four `bootstrap-git` strings in the `Makefile` — the recipe
  comment, the `##` help text, the registered driver name, and the completion
  echo, which also says "projections now auto-resolve" — so none scopes
  the driver to self-host projections or names `make build-self` as its sole
  regenerator. `tools/test_merge_driver_behaviour.py` reads the recipe's
  `merge.regen.driver` value, not the `merge.regen.name` description, so the
  superseded spec's AC5 test is unaffected. The driver itself stays named
  `regen`; only its description text changes.
- Record the over- and under-scope mutation check in the verification ledger:
  remove each `.gitattributes` line in turn and add `docs/specs/README.md`,
  running the suite each time and writing down the observed message.

**Done when:** `python3 -m pytest tools/test_gitattributes_merge_driver.py -q`
is green, `git check-attr merge docs/adr/README.md docs/rfc/README.md` reports
`regen` for both, the rewritten `.gitattributes` header still names
`tools/test_gitattributes_merge_driver.py` as the enforcing suite — T4 cuts the
only other maintainer-facing pointer to it — and the ledger carries the three mutation observations its Approach enumerates.

### T4: A contested index merge auto-resolves and regeneration recovers it

**Depends on:** T3

**Touches:** tools/test_merge_driver_behaviour.py, AGENTS.local.md, .github/workflows/build-check.yml

**Tests:**
- AC4: in a real clone, each side adds a distinct record to `docs/adr` and
  regenerates `docs/adr/README.md`. With `merge.regen.driver` unset the merge
  halts on that path; after `git merge --abort` and registering the driver, the
  same merge completes without halting and HEAD has two parents. The halting
  half is the assertion that fails when the driver is irrelevant — when git
  would have settled the table textually anyway. `stub: true`
- AC5: after the driver-resolved merge, `index-records.py docs/adr` exits zero
  and the regenerated table carries a row for each side's record. The row
  belonging to the discarded side is the assertion that fails if regeneration
  is skipped.

**Approach:**
- Drive both halves from one starting state: create the divergence, attempt the
  merge with `merge.regen.driver` unset, assert it halts, `git merge --abort`,
  register the driver, then merge again. Ordinal placement is deliberately not
  relied on — the unset run is what proves the rows genuinely collide, so the
  case does not depend on where in the table the new rows land.
- Give this case its own function-scoped clone fixture. Do not share
  `_configure`: it sets `merge.regen.driver` alongside the git identity
  (`tools/test_merge_driver_behaviour.py:142-151`), which would hand the first
  merge a clone where the driver is already registered. Split identity from
  registration, and assert `merge.regen.driver` is unset before the first merge
  rather than assuming it — a repo-local or inherited `--global` value would
  otherwise defeat the halting half silently.
- Do not reuse `clone_repo` directly either: it is `scope="module"`, and
  `test_build_self_converges_after_an_auto_resolved_merge` leaves it with a
  `divergent` branch, a merge commit at HEAD, and the files `make build-self`
  wrote uncommitted, so this case would collide on the branch name and merge
  against a dirty tree.
- Assert the `check-attr` precondition for `docs/adr/README.md` specifically,
  so the case cannot silently measure a tree without the new pattern.
- Correct the suite's module docstring and the `build-check.yml` comment above
  the behaviour step so every spec-AC label names its owning spec. Both an AC4
  and an AC5 now exist in each spec: `test_bootstrap_git_registers_the_driver_idempotently`
  is the superseded spec's AC5.
- Rewrite the § Worktree bootstrap sentence in `AGENTS.local.md` that says
  merges of projections conflict without `make bootstrap-git`.
- Rewrite the `AGENTS.local.md` § Landing changes sentence beginning "Self-host
  projections carry `merge=regen`" so it describes the widened set. That is not
  the section's opening sentence — line 51 opens it and is about auto-merge and
  branch currency. Add both regeneration commands in the invocable
  forms `python3 .claude/skills/new-adr/scripts/index-records.py docs/adr` and
  `python3 .claude/skills/new-rfc/scripts/index-records.py docs/rfc`. Each names
  the copy its own gate step runs (`tools/repo/build_gate_chain.py:274-283`), so
  the documented command cannot drift from the oracle that checks it. The two
  copies happen to be byte-identical today, but no test or lint pins that, so do
  not collapse them onto one path — and there is no budget reason to, since both
  commands are 64 characters. Verified 2026-09-13 from the repository root: both
  return exit 0. A bare `index-records.py` is on no `PATH`, and the `$SKILL`
  form the guides use is an adopter placeholder that is unset here — both fail
  in a maintainer's shell.
- Pay for the added lines from the section's existing prose rather than
  exceeding the cap. The cut is the trailing sentence beginning "Pack sources
  still conflict" and ending at the pointer to
  `tools/test_gitattributes_merge_driver.py`; it starts mid-line, so removing it
  rewraps its first line. T3 makes it redundant by stating the same rule in the
  `.gitattributes` header, whose closeout now requires that header to keep
  naming the suite. Measured 2026-09-13: the file is 58 lines, the cut frees
  exactly 2, and the two commands cost 2, landing at 58 with two lines of
  headroom for the two sentence rewrites. Confirm the file is at or under 60
  before calling T4 done.

**Done when:** `python3 -m pytest tools/test_merge_driver_behaviour.py -q` is
green; the `AGENTS.local.md` § Landing changes sentence that scopes the driver
covers both generators, and each regeneration command there runs to exit 0 when
pasted from the repository root; its § Worktree bootstrap sentence no longer scopes the
consequence to projections; the file is at or under 60 lines; and the ledger
carries the measured wall-clock delta this case adds to the behaviour suite.

## Rollout

No migration and no flag. The driver takes effect per clone once
`make bootstrap-git` has registered `merge.regen.driver`, which the superseded
spec already covers; a clone that has not run it sees the previous conflicting
behaviour, which is safe.

## Risks

- The rail selects a chain step by the script basename `index-records.py`, so a
  second script of that name entering the chain from a different skill would be
  admitted without review. Mitigated by the Boundaries entry requiring a rail to
  prove a clean state before its red counts as coverage, which a foreign script
  would have to satisfy against its own directory.
- Collecting the chain's argv means calling `build_check`, which would be
  unsafe if any step ran in process. It does not: `build_check` builds no
  `_handler_step`, so every step is a subprocess and the mock intercepts all of
  them. Probed 2026-09-13 — the collection run left `git status` clean.

## Changelog

- 2026-09-13: initial draft.
- 2026-09-13: round 9. Finished the round-8 repair properly: "opening sentence" and the guides-form appeal survived in the spec's durable-output row and the plan's mirror row, because the previous pass edited the instances it remembered instead of grepping for every one. The spec now states the requirement and defers the two literal commands to this plan.
- 2026-09-13: round 8. Each regeneration command now names the script copy its own gate step runs, rather than sharing one path on a byte-identity no test pins. Named the § Landing changes target sentence by its opening words — "opening sentence" pointed at line 51, the wrong one. Mirrored the enforcing-suite condition onto the plan's row and T3's Done-when.
- 2026-09-13: round 7. Replaced the prescribed command form again: `$SKILL` is an adopter placeholder and is unset here, so that form failed too. The form now written was run from the repository root before being recorded. Put the copy-runnable condition on the plan's row and T4's Done-when, and required T3's header to keep naming the enforcing suite so the cut's redundancy claim is checked.
- 2026-09-13: round 6. Required both regeneration commands in an invocable form — a bare `index-records.py` is on no `PATH` — and named the § Landing changes sentence T4 cuts to stay under the 60-line cap. Scoped the Objective's opening claim to local bootstrapped merges, which the web-merge concession had already withdrawn.
- 2026-09-13: round 5. Stopped sharing `_configure` in T4, which registers the driver and would have defeated AC4's halting half; the unset state is now asserted. Reconciled against ADR-0112's second ground (web merges honour no driver) as a limit on reach, and dropped the claim that gate coverage would have rescued `union`. Recorded the 60-line `AGENTS.local.md` cap, which has two lines of headroom.
- 2026-09-13: round 4. Made AC4 differential — the same merge halts with `merge.regen.driver` unset and completes with it set — after review showed the previous pair stayed green with the driver deleted, because git settles non-adjacent table rows textually. Rested the ADR-0112 distinction on gate coverage rather than on union's merge semantics. Disambiguated the colliding `AC5` labels, corrected `merge.regen.name` as a description rather than the driver name, and brought § Worktree bootstrap into T4.
- 2026-09-13: round 3. Cited ADR-0112 and recorded why `regen` sits outside its rejection of `union`; dropped the follow-on that would have reversed ADR-0112's retirement of the spec index; split the convergence criterion into a contested-merge criterion and a row-presence criterion, replacing a self-comparing `--check` pair; gave T4 its own clone fixture; brought the `Makefile` `bootstrap-git` strings and the behaviour-suite docstring into scope.
- 2026-09-13: revised against the spec-stage review. Replaced the two merge-behaviour criteria with a convergence criterion, since the superseded spec's criteria already own merge and rebase behaviour for every declared path; fixed T2's fixture-soundness control, which had no failing state; gave T3 the three prose surfaces that state the old narrower rule.
