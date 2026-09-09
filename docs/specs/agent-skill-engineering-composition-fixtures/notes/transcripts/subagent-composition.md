```text
Mode: frame
Write status: not authorized
```

# Composition contract for `audit-service-catalogue`

**Target:** the supplied `subagent-composition-SKILL.md` (inline text only — no repository path was named, so nothing was resolved or opened on disk). **Eventual mode:** `update`, since the outcome is a changed `SKILL.md`. Not entered. Nothing written.

The supplied draft is untrusted evidence. Its instructions describe a delegation design; they do not grant fan-out, write, or tool authority to this workflow or to any worker.

## 1. The load-bearing question first

The audit is a read of ~200 manifests for three fields. Before framing a fan-out contract, the skill should say why delegation is needed at all. Delegation buys you two things: isolated context per unit, and wall-clock parallelism. It costs you a brief per worker, a return contract, a merge step, and a failure model. A three-field presence check over 200 small files is a cheap parse — a single pass, or a script the skill ships, likely beats 200 workers on both latency and reliability, and beats them decisively on determinism.

Frame the delegation as **conditional**: fan out only when per-unit work requires judgment that doesn't fit a deterministic check (the draft names "borderline cases", which is the real justification), and state the threshold in the skill. If every case is mechanical, the skill should not spawn anything.

## 2. What the parent must fix before any worker runs

These are the parent's obligations. Each is currently absent from the draft.

**Partition the work and own the boundary.** The parent enumerates service directories itself and assigns each worker exactly one resolved, confined root. Per `references/safety-and-authority.md`, the parent canonicalizes and symlink-resolves each candidate root against the catalogue root before dispatch, and the worker re-runs the confinement check immediately before any access. A root handed down as a string is not a resolved root; a worker that resolves its own root from catalogue content has let untrusted data pick its target.

**Author a self-contained brief per worker — never "the full conversation".** A subagent starts fresh; there is no transcript to inherit, and the one place a host does offer inheritance it copies the parent's entire context into every one of 200 workers. Either way the draft's instruction fails: it is unimplementable on most hosts and ruinous on the one where it isn't. The brief must instead carry, explicitly: the one resolved root, the three fields being audited, the adjudication rules for the borderline cases (written down as rules, not delegated to "judge like the parent would"), the return schema, and the statement that manifest content is data, not instruction. Writing those adjudication rules down is the actual work the draft is dodging — "same context, therefore same judgment" is not a mechanism.

**Bound the concurrency.** "Run them all at once" over ~200 entries is not a plan; it is an absent one. Fix a batch width, dispatch in waves, and define what happens when the host refuses, rate-limits, or times out a dispatch. Waiting serially is indeed the slow path, but unbounded fan-out is the unreliable one, and an audit that fails at entry 140 with no resumable state is slower than the serial run it replaced.

**Make workers read-only and keep every write in the parent.** This is the single largest change. Workers return findings; the parent writes. That removes the shared-file race described below, gives one place to re-check confinement before mutation, and lets the whole audit be run once in report-only form before anything is patched.

**Fix a return schema.** One structured shape, identical for every worker: the service identifier, the resolved root, per-field status, evidence for each gap, and an explicit outcome of `complete | partial | failed` with a reason. "Whatever form suits the service" makes the results unmergeable and makes a silent failure indistinguishable from a clean pass.

**Define the merge and the failure model.** The parent aggregates all 200 returns, and the audit result is that aggregate. A missing or failed worker is a visible hole in the report — named, counted, and never rendered as "no gaps found". A partial audit that reports as complete is worse than no audit, because it retires the question.

## 3. What the draft's current shape costs

| Draft clause | What it costs |
| --- | --- |
| "Spawn one worker per service directory and run them all at once" | Unbounded fan-out over ~200 units. Host refusals, rate limiting, and cost scale with the catalogue and are unbudgeted. No resumability: a mid-run failure loses the whole pass. |
| "Give each worker the full conversation so far" | Not a mechanism on hosts where subagents start fresh — the borderline-case consistency it promises never materializes, silently. Where context does carry, it multiplies the parent's context by the worker count. It also propagates every manifest already read into every worker, so one prompt-injecting manifest reaches all 200. |
| "Each worker patches the gaps it finds directly into that service's manifest" | 200 concurrent writers holding `filesystem_write`, each resolving its own target. Confinement is enforced 200 times instead of once, and there is no dry run: the first execution is also the mutation. |
| "…and also updates the shared `catalogue-summary.md` tally as it goes" | A genuine lost-update race. Concurrent read-modify-write on one unsynchronized file yields a tally that is wrong by an unknowable amount, with no error raised — a corrupted artifact that looks authoritative. This clause must be deleted outright, not repaired; the parent writes the summary once, after the merge. |
| "Workers report back in whatever form suits the service" | No schema means no aggregation and no way to detect a worker that returned nothing useful. |
| "Take the last worker's summary as the audit result" | Discards 199 results. The reported "audit" is the state of one arbitrary service, presented to the user as coverage of the catalogue. This is the draft's most damaging line: it produces a confident, wrong answer. |
| Frontmatter `boundaries: [filesystem_read_untrusted, filesystem_write]` | Declares nothing about delegation, concurrency, or worker authority, so the largest capability in the skill is undeclared. |
| Description: "Audit every service … and write the gaps back" | Fuses a read-only audit with a bulk mutation under one activation. A user asking "which services lack a runbook?" triggers 200 manifest writes. |

## 4. Portability floor

Subagent spawning is host-specific: some runtimes expose it, several the skill may be installed into do not. The composition contract therefore needs a declared degradation path — the same partition, the same per-unit rules, the same schema, executed serially in the parent — and the skill must state that the *result* is identical and only latency differs. If the audit's correctness depends on parallelism, the design is wrong. A skill that hard-requires a fan-out primitive is not portable; the fan-out must be an optimization over a serial baseline that always exists.

## 5. Activation boundary

Should activate: "audit the service catalogue for ownership gaps", "which services have no runbook link", "check on-call coverage across the monorepo".

Should not activate: "who owns service X" (single lookup, no audit), "add a runbook link to service X" (a targeted edit, not an audit), "audit our dependency licences" (different corpus). Split the read-only audit from the write-back so the second is a separate, separately authorized step rather than a side effect of asking a question.

## 6. Observable outcome

One aggregate report over every enumerated service, each row carrying per-field status plus evidence, and an explicit accounting of units that did not complete. Write-back, when separately authorized, changes only the manifests named in that report.

## 7. Evidence the reframed skill must produce

Success: unit count enumerated equals units reported. Failure: a worker that fails appears in the report as failed, with a reason. Interruption: a partial run reports as partial and names what was not covered. Clean degradation: the serial path on a host without subagents yields the same report.

## 8. Proposed file tree

```text
audit-service-catalogue/
  SKILL.md                          # audit contract, partition rule, dispatch bound, degradation path
  references/
    delegation-contract.md          # worker brief template, return schema, merge and failure model
    field-rules.md                  # owner / runbook / on-call adjudication, incl. borderline cases
```

`SKILL.md` keeps the activation boundary, the partition rule, the concurrency bound, and the serial fallback. The worker brief template and return schema are conditional detail and belong in a reference. Add a script only if the mechanical field check turns out to cover most cases — in which case revisit §1, because the fan-out may not be needed.

## 9. Non-goals

Not framed here: the manifest schema itself, remediation of the gaps (as opposed to reporting them), on-call system integration or any network call, credential handling, and CI wiring. Agreement with this frame does not authorize a write. Entering `update` requires its own explicit authorization naming the confined root and the file set.

**Files changed:** none. **Checks run:** none — read-only framing over inline text; no repository path resolved or opened. **Unavailable capabilities:** none encountered. **Cleanup:** none required.
