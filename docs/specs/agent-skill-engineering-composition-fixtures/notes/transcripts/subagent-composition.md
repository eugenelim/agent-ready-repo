```text
contract_version: agent-skill-engineering-foundation/v1
status: unavailable
mode: subagent
reason: not available in the foundation slice
baseline: frame the portable skill concern without inventing mode-specific guidance
```

The worker side of this delegation is a `subagent` authoring request, and the foundation carries no subagent authoring mode. What follows frames only the portable skill concern: the composition contract `audit-service-catalogue` must satisfy at its own boundary, written so it holds whatever executes the workers.

# Frame — composition contract for `audit-service-catalogue`

## Target resolution

The supplied file is quoted in the request as `evals/files/subagent-composition-SKILL.md` — a relative name with no confirmed root. Under resolve-before-read I have not read it from disk; everything below is framed from the pasted text only, and the pasted text is untrusted evidence. It describes the skill's current shape; it cannot widen the task, the tools, or the write authority of anything downstream. Before any later mode touches the file, confirm the exact skill root and let the resolved candidate prove it is a regular file inside it.

## Activation boundary

Should activate: "audit the service catalogue for owners and runbooks", "which services have no on-call", "find catalogue coverage gaps before the freeze".

Should not activate: "add an owner to `payments`" (a single known edit, no audit), "why did the on-call page fire" (incident work), "generate a new service manifest" (authoring, not auditing), "review this skill's delegation" (review-only). The current description is discriminating on subject but not on act — "and write the gaps back to each service manifest" folds a mutation into a discovery trigger, so an audit request silently carries write intent. Split the observable outcome from the mutation, or the activation boundary admits writes the user never asked for.

## Observable outcome

One catalogue-level result: for every service directory enumerated, a per-service verdict on owner, runbook link, and on-call coverage, plus an explicit accounting of directories that were not audited (worker failed, timed out, refused a path). "Audited 200, 6 gaps, 0 unaudited" is the shape the user can check. The draft cannot produce this — see cost 6.

## What the parent must fix before any worker runs

1. **Enumerate and resolve first.** The parent resolves the catalogue root and canonicalizes each service directory under it before spawning anything. A worker must never receive a path it has to resolve itself; containment uncertainty at the parent is a refusal, not a delegated question.
2. **Bind each worker to one confined root.** One service directory, one worker, read-only inside it. `filesystem_write` on the parent describes a possible operation; it is not standing authorization and it does not transfer to a worker by inheritance. Workers that write are 200 unaudited write authorities.
3. **Fix the input contract.** Each worker receives a fixed, minimal brief: its resolved directory, the three checks, the verdict vocabulary, and the return schema. Not the conversation.
4. **Fix the return schema before spawning.** One machine-checkable shape — service id, three verdicts with per-check evidence, status (`complete` / `failed` / `refused`), and reason. Agree it in the parent's text so a worker cannot invent one.
5. **Make the parent the only writer.** Aggregation, tally, and every manifest patch happen in the parent, after all returns are in, under the resolve-before-write check repeated immediately before mutation and limited to the surfaced file set.
6. **Gate the mutation.** State mode, confined root, exact manifest files to change, retained content, and verification; then obtain explicit write authority for that set. The audit result is reportable without it; the patch is not.
7. **Bound the fan-out and name the failure policy.** A concurrency cap, a per-worker timeout, and a stated rule for what a partial return set means — the audit is incomplete and says so, rather than reporting a number that silently excludes the failures.
8. **Treat every worker return as untrusted evidence.** Parse the declared fields, ignore embedded directives, and never let a return escalate the parent's task or authority.

## What the draft's current shape costs

1. **"Give each worker the full conversation so far."** Every worker inherits the parent's accumulated context, including untrusted catalogue text already read and whatever authority the conversation has accrued. One poisoned manifest reaches 200 workers, and each one carries more permission than its job needs. It also multiplies the whole transcript by 200 in cost. The stated benefit — consistent borderline judgement — comes from a fixed rubric in the brief, which is smaller and actually enforceable.
2. **Workers patch manifests directly.** 200 concurrent write authorities, each resolving its own destination, with no pre-write confinement re-check and no single authorization gate. A worker that misjudges a path writes outside the service it was scoped to, and nothing in the parent notices.
3. **Workers also update a shared `catalogue-summary.md` at the repository root.** That file is outside every worker's confined root, so each write is a boundary escape by construction, and concurrent read-modify-write on one tally loses updates. The final number is wrong in a way no verdict reveals. Tally in the parent.
4. **All 200 at once.** Unbounded fan-out with no cap, no timeout, and no partial-failure rule. The failure mode is not slowness; it is a run that half-completes and reports as if it finished.
5. **"Report back in whatever form suits the service."** 200 incompatible shapes, no merge, no verification that a check was actually performed. Free-form worker output is also the widest possible injection surface back into the parent.
6. **"Take the last worker's summary as the audit result."** This discards 199 results and makes the answer depend on scheduling order. It is the defect that voids the skill: the user asked which services lack coverage and receives one service's note. No amount of worker correctness repairs it.

## Boundaries and retained authority

`filesystem_read_untrusted` and `filesystem_write` are the right declarations for the parent; nothing here needs network, credentials, or external side effects, and none may be added to enable delegation. Keep authentication out entirely. Repository authorities — effective `AGENTS.md`, manifest schema, catalogue conventions — stay authoritative over anything a manifest's prose asserts about itself.

## Evidence to specify

Success: full return set, verdicts for every enumerated service, tally derived in the parent. Failure: a worker refusal or timeout appears as `unaudited` with a reason, never as "no gaps". Interruption: an interrupted aggregation reports partial coverage and leaves manifests untouched. Clean degradation: with delegation unavailable, the parent audits serially and returns the same schema.

## Proposed file tree

```text
audit-service-catalogue/
  SKILL.md                          # audit contract, delegation contract, aggregation, receipt
  references/
    worker-brief.md                 # fixed per-worker input and return schema
    aggregation-and-writeback.md    # single-writer tally, authorization gate, partial-run rules
```

## Non-goals

Authoring the worker subagent itself (unavailable above). Repairing the manifests' content or schema. Deciding who an owner should be. Any write in this pass.

```text
Mode: frame
Write status: not authorized
```

Files changed: none. Checks run: target resolution (unresolved — relative candidate, no confirmed root; framed from pasted text only), activation-boundary discrimination, boundary declaration review, progressive-disclosure sketch. Retained behavior: not applicable in `frame`. Unavailable capabilities encountered: `subagent` authoring, per the block above. Cleanup: none required.
