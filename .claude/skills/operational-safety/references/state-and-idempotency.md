# state-and-idempotency — convergent re-apply, state locking, single-writer

> **Loaded when:** the change provisions or mutates infrastructure, edits
> infrastructure-as-code, or drives a stateful migration of a running system —
> anything where the *write path* may be re-run after a failure.
> **Grounded in:** F1.2 (declarative + idempotent re-apply is what makes retry
> safe; imperative scripts collide), F1.3 (shared state needs a single-writer
> lock). Operational taxonomy: AWS Well-Architected Change Management; the
> Terraform/Pulumi declarative-convergence model.
> **Delegation legend:** `tool` = scanner / CI-gate-owned · `hybrid` = gate
> surfaces the signal, you judge the fix · `reason` = reviewer-only judgment.

Idempotent convergent apply is the **precondition the whole infra loop rests
on**: re-running after a fix must *converge, not collide*. A non-idempotent
imperative step is the retry-collision root cause — the thing to fix first
rather than iterate around.

## Implementation checks

- `reason` **Convergent re-apply.** Re-running the change from a partially
  applied state must reach the desired state with no duplicate creates and no
  inconsistent leftovers ("if already in desired state, no actions taken").
  Declarative definitions get this structurally; an imperative script must add
  existence-check / conditional-create guards to match it. Flag any step that
  would re-create an existing resource or error on a second run.
- `reason` **No imperative non-idempotent step on the write path.** A
  hand-rolled create/start/stop sequence with no guard is the
  "manual stop/start errors" failure mode — each failed retry is a fresh mess.
  Require the guard, or convert the step to declarative.
- `hybrid` **Single-writer lock on shared state.** When an agent and a human,
  or two agents, could apply against the same state concurrently, mutation must
  serialize through a state lock. Confirm the lock mechanism is configured;
  judge whether the concurrency window is actually closed.
- `reason` **State integrity over the retry.** A failed apply must not leave
  state and live resources diverged in a way the next apply can't reconcile.
  The next run should *read* current reality and converge, not assume the prior
  run's intent.
- `hybrid` **Terminal-failed-state is a destroy-recreate convergence case.** A
  resource can land in a state a normal re-apply **cannot** converge from —
  e.g. a CloudFormation stack in `ROLLBACK_COMPLETE` must be **deleted and
  recreated**, not updated. Treat such terminal states as a destroy-recreate
  branch of the convergence path, not a retry the next `apply` will fix. *Carve
  note:* this module **names** the terminal state as a convergence case for the
  reviewer; the sibling
  [`cloud-implementation-craft`](cloud-implementation-craft.md) module owns
  **how to author around it** at EXECUTE — the two placements are deliberate
  (convergence-case naming vs. authoring craft), not duplication.

## Persistent-state migration checks

- `reason` **Old/new reader-writer compatibility and expand/contract order.**
  State shared during rollout must remain readable and safely writable by every
  live binary version. Add representations before depending on them, tolerate
  both forms through the mixed-version window, migrate data, switch reads and
  writes, and remove the old form only after compatibility evidence proves the
  window closed. Flag a one-step destructive schema or serialization change.
- `reason` **Backfills are idempotent, resumable, batched, and concurrency-safe.**
  A retry resumes from durable progress without double-applying work; batches
  bound locks, load, and failure scope; concurrent foreground writes cannot be
  overwritten by stale backfill reads. Name the checkpoint and conflict rule.
- `reason` **Mixed-version tests cover real read/write combinations.** Exercise
  old reader/new writer, new reader/old writer, retry after partial progress,
  and foreground-write/backfill races where those combinations are possible.
  A test of only the final schema misses the deployment boundary.

## Established-pattern bypass

Resolve the repo's sanctioned convergence mechanism — the declarative IaC
module, the shared apply wrapper, the locked state backend — and flag a change
that hand-rolls an imperative provisioning sequence inline instead of extending
it. The blessed mechanism is where idempotency and single-writer locking were
already decided, once.

*Illustrative only (never normative):* a `terraform apply` against a
lock-enabled S3 backend, or a Pulumi `up` against a locked stack, exhibit this
shape — but the check is the *property* (convergent, single-writer), not any
one tool.
