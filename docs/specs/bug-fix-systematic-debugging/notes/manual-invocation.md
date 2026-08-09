# Manual invocation evidence

- **Date:** 2026-08-09
- **Command:** `codex exec --ephemeral --sandbox read-only --color never <prompt>`
- **Exit code:** `0`
- **Projected skill selected:** `.agents/skills/bug-fix/SKILL.md`
- **Files modified:** none

## Prompt

> An order-processing flow passes locally but intermittently fails only in CI.
> A request crosses an API handler, a queue worker, and a database writer; some
> completed records lose their currency code. I need to diagnose the root cause
> and fix the existing behavior. Explain the concrete investigation and
> implementation sequence you would follow before making changes. Do not modify
> files; this is a read-only workflow check.

The prompt did not name the `bug-fix` skill. Codex selected it from the
intermittent, CI-only, existing-behavior language.

## Verification record

| Criterion | Observed evidence | Verdict |
| --- | --- | --- |
| AC1 | Began with an observable integration regression test, required it to fail against the unfixed code because currency was missing, and deferred production changes. | Pass |
| AC2 | Kept three rival hypotheses in Hypothesis / Expected / Actual / Verdict form and changed one factor per experiment. | Pass |
| AC3 | Required one correlated run across API, queue, worker, writer, and database while capturing inputs, outputs, state, and configuration before narrowing. | Pass |
| AC4 | Compared a successful order, local versus CI, and an earlier working revision across meaningful differences. | Pass |
| AC5 | Traced the persisted value backward through SQL bindings, writer and worker data, decoded and queued messages, the validated object, and the request. | Pass |
| AC6 | Treated probes as temporary diagnostics and required removal or deliberate retention as production observability. | Pass |
| AC7 | Used bounded polling of `status == completed`, reported last state on timeout, and rejected a passing retry as proof of a fix. | Pass |
| AC11 | Limited the change to the evidence-supported originating boundary, rejected blanket defaults/retries/null guards, retained the coverage-closing test, deferred adjacent cleanup, and required commit rationale. No tracker was present in the synthetic scenario. | Pass |
| AC17 composite route | Selected the projected skill from a natural-language intermittent CI-only root-cause request without a literal skill name. | Pass |

This invocation did not exercise the repeated-failure stop rule, the
environmental/external-failure outcome, or production-emergency containment.
Those branches remain covered by the separate behavior-eval scenarios; this
record makes no manual-QA claim about them.

## Final response

The response said it would not patch any layer until evidence identified the
first boundary where `currency` diverged. It made three scenario assumptions:
completed persisted currency must equal the accepted request currency, CI can
expose correlated boundary evidence, and no active incident requires immediate
containment.

It then prescribed this sequence:

1. Add an integration regression test that submits a distinctive currency,
   waits with bounded polling until the order completes, queries the database,
   and fails against unfixed behavior specifically because currency is absent.
   Record CI environment, frequency, timing, test seed, worker count,
   queue/database versions, and final state; a passing retry is evidence, not a
   fix.
2. Run one correlated reproduction across API handler, queue, worker, database
   writer, and committed row. At every boundary capture inputs and outputs plus
   schema, retry, concurrency, transaction, migration, and other relevant state
   and configuration. Narrow only after locating the first divergence.
3. Compare a successful order through the same path, local versus CI behavior,
   and an earlier working revision. Enumerate differences in shape, schema,
   retry/order, control flow, concurrency, configuration, migration state,
   timing, and subsequent writes.
4. Test three rival hypotheses: queue schema skew, retry/concurrent overwrite,
   and CI database-schema or upsert differences. For each, keep Expected /
   Actual / Verdict evidence and change only one discriminating factor.
5. Trace backward from the persisted row through SQL bindings, writer input,
   worker output, decoded message, queued bytes, validated API object, and
   request. Use history to recover intent and widen only if evidence shows the
   same cause elsewhere.
6. Name the coverage gap and retain the red integration test. Candidate gaps
   included stopping at the accepted API response, mocking serialization,
   omitting retry/partial-update paths, failing to assert persisted invariants,
   and missing CI-only concurrency or schema differences.
7. Make only the supported originating fix: event mapping/schema, merge/update
   semantics, or migration/persistence contract according to the evidence.
   Reject defaults, retries, and null guards across every layer; add boundary
   validation only where the demonstrated failure or an independent safety path
   justifies it.
8. Run the original test red then green, repeat under bounded CI-equivalent
   conditions, run relevant component and integration suites, verify retries or
   later writes cannot reproduce the loss, remove diagnostics or retain them
   deliberately as observability, and inspect the diff for symptom masking.
   Defer adjacent cleanup and document the failure, supported cause, coverage
   gap, and fix location in the commit body.

The invocation ended by confirming that it modified no files.
