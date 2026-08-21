# Plan: worktree-cooperative-lease

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Why this plan exists separately from its predecessor

The lease was built once already, across five layers, and split out of
[`worktree-runtime-hygiene`](../worktree-runtime-hygiene/spec.md) under review
rather than landed. The implementation is preserved on branch
`eugenelim/worktree-hygience-c-lease-wip`; this plan rebuilds from it rather than
from nothing, and the known defects are enumerated in `workspace.toml`
`[backlog].open` under slug `worktree-cooperative-lease`.

The reason it was split is the reason this plan is shaped the way it is. Three
independent reviewers found failure modes the old criterion did not enumerate, in
a finished implementation with a green suite and 46 mutation proofs. The defect was
never in the code alone — it was that a one-sentence criterion cannot be falsified.
So each acceptance criterion in the spec now names a failure mode, and each task
below names the mutation that must redden it.

## Design (LLD)

**Two locks, two jobs, named so they cannot be confused.** A short-lived shared
*decision* lock makes read-other-role-then-publish-own indivisible. A long-lived
per-claim *ownership* lock answers liveness. The decision lock is never a claim's
own lock.

**Liveness is a held lock, positioned at byte zero.** Both the publishing and
probing paths seek to byte zero before locking. On POSIX `flock` covers the whole
open file description and position is irrelevant; on Windows `msvcrt.locking`
locks one byte at the current position, so a publisher that writes a payload then
locks holds a different byte than a prober opening at zero.

Measured on `windows-latest` by `tools/test_windows_lock_semantics.py`, which
landed ahead of this work for exactly this purpose:

```
MEASURED [win32 / os.name=nt] write-then-lock, probe at position 0
    -> NOT blocked (LOCK INVISIBLE)
```

All four cases passed, so the seek-to-zero invariant holds on Windows and
byte-range locking *can* carry liveness there. That measurement reversed the
design: the previous intent was to report `UNDETERMINABLE` on Windows —
surrendering the capability — purely because it could not be tested locally.

**Reclaim policy differs by role, and the difference is load-bearing.** Admission
roles (slot, ticket) are throughput counters: over-admitting by one costs memory
pressure, so they expire on a stated age budget. Worktree roles (activity,
exclusive) are safety interlocks: reclaiming a live one lets a mutator start under
an in-flight cleaner, so they never expire on age and their only path back is the
operator command. A previous round applied one rule to both and had to be split.

**The wrapper forwards the makefile, not the jobserver.** See the spec's
Limitations for the measurement and the three reasons.

## Tasks

Each task lands independently and leaves the repository working. Every new test
file gets its own Makefile pytest invocation.

### Task 1 — the claim primitive, positioned correctly

**Depends on:** none

Tests: `tools/test_coordination_lease.py` — atomic publish; a second publisher does
not overwrite; release removes only the caller's own claim; a `SIGKILL`ed holder's
claim is reclaimable using a real killed process; an unreadable payload is
undeterminable and counts as live; out-of-range identity, mismatched worktree and
out-of-window creation time each refused or clamped; digest keys do not collide for
`/mnt/a/b-c` versus `/mnt/a-b/c`; a symlinked store is refused; a claim path
escaping the store is refused; the decision lock serializes two real processes.

`Done when:` both the publish and probe paths seek to byte zero — asserted
structurally, because on POSIX the behaviour is identical either way and only
Windows can falsify it behaviourally.

### Task 2 — the two worktree roles and their interlock

**Depends on:** Task 1

Tests: `tools/test_worktree_lease_interlock.py` — `clean --apply` refuses while a
live `activity` claim exists and names the holder; proceeds when none exists and
holds `exclusive` across every deletion, observed during a real deletion; a dry run
publishes no claim and creates no store; a mutator with an unusable store warns and
proceeds while `clean --apply` refuses; **exactly one** participant wins a
contended tie, asserted as `== 1` so a symmetric abort fails; the atomicity of
read-then-publish asserted by observing the lock hold, not inferred from a race.

### Task 3 — admission, fairness, and the budgets

**Depends on:** Task 1

Tests: `tools/test_run_slot.py` — admission never exceeds the limit under real
contention; waiters admitted in registration order; a waiter whose ticket is
removed **re-registers** rather than waiting out its budget; an admission claim
expires on age while a worktree claim does not; invalid and below-one budget values
refused from the entry point that ships, not only the parsing helper; the clamp is
downward-only, host-independent in test, and reads a usable-memory figure with
headroom so the reference configuration is not clamped; the decision lock's budget
scales with the wait budget.

### Task 4 — the wrapper, the status and release commands, and the make wiring

**Depends on:** Task 2, Task 3

Tests: `tools/test_with_lease_cli.py`. The ledger below is the authoritative list;
this task's entries are the ones naming that file. Every name in the ledger is a test
that exists — the previous revision of this line described eight tests, of which three
were never written, and the plan froze at `Done` with the description in it.

Wire `lock-semantics-windows` into `build-check-windows`'s `needs` in this task,
because from here something depends on it.

### Participant matrix

The previous plan claimed `bootstrap.py` published a claim and it never did, and
that plan froze at `Done` with the wrong statement in it. So every entry point is
listed with its disposition, and each participating one carries a dropped-wrapper
mutation.

| Entry point | Disposition | Mutation that must redden |
|---|---|---|
| `make test` | wrapped | remove the wrapper; the target's own guard reddens |
| `make build-check` | wrapped | remove the wrapper; also remove the `-f` forwarding, which must redden `assert-sast-chain-reachable` |
| `make sast` | wrapped | remove the wrapper; the target's own guard reddens |
| `make ci` | **not** wrapped — its recipe only prints a verdict, and `lint-ci-parity` derives 31 dispositions from its prerequisite list | add a wrapper; the parity guard reddens |
| `frontend_runtime.py gate` | publishes an `activity` claim, takes **no** slot | remove the claim; its own test reddens |
| `tools/repo/bootstrap.py` | **not** participating. It runs `npm ci --prefix` only, which is per-worktree and concurrently safe; the globally destructive `pip install -e` is a documented manual step in a Makefile comment and has no code path to lease | none — asserted by a test that `bootstrap.py` imports no lease module, so a future claim added here is a deliberate act |

### Clause-to-mutation ledger

Structural clauses — "exactly one implementation", "single-homed", "positioned at
byte zero" where the platform makes position irrelevant — take goal-based source
checks, because a runtime assertion cannot falsify them. The ledger is a deliverable,
not a description: a clause with no entry is an unfinished task. The previous revision
of this section stated that rule and then listed nothing, which is how three AC
clauses reached `Done` with no test at all — AC7's exit-code integrity under a failing
release, AC8's stale-marker rule, and AC9's unusable-store-still-runs rule. Each row
below was run as a real mutation: the guard was confirmed green, the named clause was
broken in the source, the named check was confirmed to redden, and the source was
restored and verified byte-identical.

| AC | Clause | Mutation | Check that catches it |
|---|---|---|---|
| AC1 | liveness is a held lock, never a payload | trust the payload's pid | `test_a_forged_claim_with_a_live_pid_is_not_live` |
| AC1 | the OS releases the lock on death | `SIGKILL` the holder | `test_sigkilled_holder_claim_is_reclaimed` |
| AC1 | liveness is not inferred from age | age a live claim | `test_live_identity_is_not_reclaimed_by_age_alone` |
| AC1 | a recycled pid cannot impersonate a holder | reuse the pid | `test_recycled_pid_cannot_impersonate_lock_holder` |
| AC1 | the lock is taken at byte zero on every platform | drop the `lseek` | `test_windows_write_then_lock_hides_the_lock_from_a_probe` and `test_seeking_to_zero_in_both_paths_makes_a_held_lock_observable` on `windows-latest`; `test_claim_lock_operations_seek_to_byte_zero_structurally` is the POSIX source check, because position is unobservable there |
| AC2 | read and publish inside one uninterrupted hold | publish outside the hold | `test_racing_participants_are_never_both_admitted`, `test_scan_and_slot_publish_share_one_decision_lock_hold` |
| AC2 | exactly one participant is admitted (`== 1`) | admit both | `test_contended_roles_admit_exactly_one_participant` |
| AC2 | the two roles interlock in both directions | drop either check | `test_sequential_interlock_refuses_exclusive_while_activity_is_held`, `test_activity_waits_for_an_exclusive_claim_to_clear` |
| AC2 | the decision lock actually serialises | release it early | `test_coordination_lock_serializes_two_real_processes` |
| AC3 | the shipped deletion predicate is untouched | conditionalise it on holding a claim | `test_clean_apply_claim_spans_a_real_multi_file_deletion` plus the predecessor's own predicate tests. **Single-site mutations here are inert by design:** `.lease` is refused by both the traversal collector and `_subtree_safety_reason`, so only removing both reddens, and that is the property, not a coverage gap |
| AC3 | the store is not deletable by the cleaner | give it a non-refused suffix | the suffix guard plus `test_clean_dry_run_never_creates_a_claim_store` |
| AC4 | out-of-range, mislocated, and future payloads are refused or clamped | trust each field | `test_untrusted_payloads_are_rejected` |
| AC4 | an unreadable payload blocks rather than passes | treat it as absent | `test_unreadable_payload_is_undeterminable_and_blocks` |
| AC4 | the release command never removes a live claim | drop the liveness check | `test_release_claim_refuses_a_live_holder` |
| AC4 | it does release an undeterminable one | refuse everything | `test_release_claim_releases_an_undeterminable_claim` |
| AC4 | every state has a documented path back | render "pid unknown" for a live claim with a refused identity | `test_a_live_claim_with_a_refused_identity_is_still_actionable` |
| AC4 | waiters are ordered by a value they cannot forge | backdate a ticket | `test_backdated_ticket_cannot_overtake_a_real_waiter` |
| AC5 | re-registration keeps the original position | re-stamp on re-registration | `test_ticket_removal_reregisters_without_losing_original_position` |
| AC5 | a live waiter's record is never aged out | prune on age alone | `test_an_observably_live_waiter_record_is_never_aged_out` |
| AC6 | defaults are literal and host-independent | derive them from the host | `test_budget_defaults_and_strict_parsing_are_literal_and_host_independent` |
| AC6 | the memory clamp is downward-only with headroom | raise the divisor to 16 GiB | `test_memory_clamp_uses_twelve_gib_and_preserves_reference_headroom` |
| AC6 | the decision-lock budget scales and has a floor | fix it to a constant | `test_decision_lock_budget_scales_with_wait_budget_and_has_floor` |
| AC6 | an invalid budget refuses before touching the store | coerce it | `test_entrypoint_refuses_invalid_budget_before_store_access` |
| AC6 | the wait budget governs both waits | hardcode the default for the activity wait | `test_a_live_exclusive_claim_refuses_the_wrapper_with_the_reserved_code` — the mutant fails by *waiting ninety minutes*, so the harness treats its timeout as the detection |
| AC6 | the cap is soft only for admission roles | expire a worktree claim | `test_admission_expiry_makes_limit_soft_but_worktree_claims_do_not_expire`, `test_old_undeterminable_admission_record_expires` |
| AC6 | the real limit is never exceeded | admit past it | `test_real_concurrent_admission_never_exceeds_limit` |
| AC7 | the child's exit code is forwarded verbatim | rewrite it | `test_main_strips_argparse_remainder_separator` (propagates 19) |
| AC7 | a failing release cannot alter that code, either way | let the release exception escape | `test_a_failing_release_cannot_change_the_childs_exit_code`, parameterised over a passing and a failing child |
| AC7 | one child runner, not a second copy | add a second call site | `test_wrapper_has_exactly_one_reachable_child_runner` (parsed tree, not substring) |
| AC7 | only the nesting marker is added to the environment | add another key | `test_wrapper_only_adds_the_nesting_marker` (asserts a delta: macOS injects `LC_CTYPE` and `__CF_USER_TEXT_ENCODING`) |
| AC7 | an empty command is refused, not spawned | spawn it | `test_main_refuses_a_missing_wrapped_command` |
| AC7 | activity is held for the child's lifetime, not the queue wait | acquire activity before the slot | `test_admission_precedes_activity_so_a_queued_run_never_blocks_cleanup` |
| AC7 | every refusal exits 75 with the marker, alone on its line | drop the marker | `test_main_refuses_malformed_slot_configuration`, `test_a_live_exclusive_claim_refuses_the_wrapper_with_the_reserved_code`, `test_clean_apply_refuses_an_unusable_store_with_no_override` |
| AC7 | a queued caller says so, and behind whom | wait silently | `test_queued_wrapper_reports_its_holders` |
| AC7 | status mutates nothing and leaks no path | mutate, or print the worktree path | `test_status_is_read_only_and_emits_recovery_identifier` |
| AC8 | a nested acquisition and its release are no-ops | release the parent's slot | `test_nested_recursive_make_completes` |
| AC8 | a marker naming no *live* claim counts as absent | drop the liveness half | `test_a_marker_naming_no_live_claim_cannot_disable_the_limiter` — the marker names a real leftover file, because a marker naming nothing is caught by the existence check alone |
| AC8 | the receipt names the inherited holder, never the marker | suppress the receipt | `test_nested_receipt_names_the_holder_and_never_the_marker` |
| AC9 | an unusable store warns and runs the child | re-raise instead | `test_an_unusable_store_warns_and_still_runs_the_wrapped_child` |
| AC9 | an unresolvable worktree warns and runs the child | resolve above the handler | `test_an_unresolvable_worktree_warns_and_still_runs_the_gate`, `test_an_explicit_port_survives_an_unresolvable_worktree` |
| AC9 | only genuine contention refuses | classify a held lock as an unusable store | `test_a_held_coordination_lock_refuses_rather_than_running_unleased` |
| AC9 | a hard-link failure is a store fault, not a crash | re-raise the raw `OSError` | `test_a_publication_fault_becomes_an_unusable_store_not_a_raw_oserror` |
| AC9 | the recursive sub-make keeps the makefile in use | drop `-f` | `assert-sast-chain-reachable.py` mutation 2, `test_wrapped_targets_keep_their_lease_and_forward_the_makefile` |
| AC9 | each wrapped target is itself guarded | drop the wrapper | `test_wrapped_targets_keep_their_lease_and_forward_the_makefile`, parameterised over `test`, `build-check`, `sast` |
| AC9 | `ci` is not wrapped | wrap it | `lint-ci-parity` (31 derived dispositions) |
| matrix | the browser gate publishes activity and takes no slot | remove the claim | `test_the_browser_gate_holds_activity_and_takes_no_run_slot` |
| matrix | `bootstrap.py` participates in no lease | import the lease module | `test_bootstrap_participates_in_no_lease` |

### Windows enforcement lands in Task 1

Wiring `lock-semantics-windows` into `build-check-windows`'s `needs` is **not
sufficient to gate it**: that aggregate is `if: ${{ always() }}` and its script
checks only the AgentBundle and CredBroker results, so a failing lock job would be
ignored. Task 1 therefore adds the job to `needs`, threads its result into the
aggregate's env, and extends the script's condition — and runs the real
coordination publisher and prober on Windows rather than only the synthetic
semantics fixture, since the fixture proves the platform and not the code.

### Not changing

`scan`'s JSON schema and its pinned key set; the deletion safety predicate, which
is reused rather than modified; `ci`'s recipe and prerequisite list; the port
lease's observable behaviour and its aged-reclaim policy; `docs/CONVENTIONS.md`;
`docs/product/changelog.md`, because nothing here bumps a released artifact's version and `tools/repo/**` is repository-only.

### Tempted and declined

- Forwarding the jobserver. Declined for the three reasons in the spec's
  Limitations; the decisive one is that this wrapper holds descriptors open for the
  claim locks and would risk handing a sub-make a lock instead of a token.
- Reporting `UNDETERMINABLE` on Windows. Declined because it was measured
  unnecessary; that would have surrendered a capability to cover a blind spot.
- Making the two reclaim policies consistent. Declined: the asymmetry is the
  contract, and a future round tempted to tidy it should change the criterion first.
- Reporting lease state inside `scan --json`. Declined: it bumps `SCHEMA_VERSION`
  and breaks a pinned key set for diagnostics `lease-status` already provides.
