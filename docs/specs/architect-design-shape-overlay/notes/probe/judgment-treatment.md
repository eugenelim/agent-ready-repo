# Blind judgment — treatment pair

Judge: `codex exec`, model `gpt-5.6-sol`, provider openai, reasoning effort high.
Blind: the judge was given the brief and two documents labelled A and B, and was
told only that both answer the same brief and were produced by two independent runs
of the same procedure. It was told nothing about an overlay, a router, or which
document carried what.

Label mapping, fixed by a recorded coin flip before the payload was built
(`a-is-A`): **Document A = `arm-a.md`, Document B = `arm-b.md`**.

Questions put, verbatim:

> Q1. List the concerns document A raises that document B does not raise
>     anywhere, in any wording. A concern is a substantive architectural issue
>     the design must address — not a phrasing, a heading, or a restatement.
>     Give each a short name and one sentence. If none, say none.
>
> Q2. The same for concerns document B raises that document A does not.
>
> Q3. For each list separately, answer: taken as a whole, is that set of
>     concerns load-bearing for this design — would a competent reviewer of the
>     other document call its absence a real gap? Answer load-bearing or not
>     load-bearing for each set, with one paragraph of reasoning.
>
> Do not compare length, polish, or writing quality. Do not say which document
> you prefer. Do not guess what distinguished the two runs.

---

## Answers

Q1.

- **Semantic drift:** The provider may change a field’s meaning without changing its shape, bypassing schema validation and causing incorrect billing interpretation.
- **Reconciliation feasibility and liveness:** The design depends on a provider API with adequate history and rate limits, plus an alarm when reconciliation stops succeeding rather than merely reports errors.
- **Downstream backpressure:** A stalled monolith can grow the outbox until shared Postgres storage is exhausted, so publication needs headroom alarms and a safe pause mechanism.
- **Field-level privacy:** Raw provider payloads require personal-data classification and a decision on redaction before being retained or archived.
- **Webhook-authentication details:** The provider’s actual signature algorithm must be confirmed before the receiver’s authentication contract is implementable.

Q2.

- **Queue payload limits:** Provider envelopes may exceed SQS’s per-message size limit, requiring a measured bound and an object-storage-pointer fallback.
- **Poison-message isolation:** Partial batch failure handling must prevent one malformed envelope from repeatedly delaying healthy messages.
- **DLQ incident policy:** Operators need a predetermined redrive-or-wait response for malformed-payload storms.
- **Legal holds:** Retention deletion must not remove evidence while an audit or legal hold is active.
- **Shared-RDS isolation threshold:** Cross-workload connection contention and SOC 2 key-scope requirements need explicit triggers for moving the event log off the monolith’s database instance.
- **Reconciler delivery priority:** The reconciler must be protected from schedule-driven descoping because it is the control that detects missing events and stale subscriptions.

Q3.

**Document A-only set — load-bearing.** Semantic drift can produce undetected misbilling, an infeasible or silently stalled reconciliation path reopens the stale-subscription incident, downstream backpressure can take ingestion down, and unresolved authentication or personal-data handling creates security and audit gaps. A competent reviewer of document B would call these omissions real gaps.

**Document B-only set — load-bearing.** Oversized or poison messages can break durable ingestion, an incorrect DLQ response can prolong an incident, legal-hold and database-isolation questions materially affect SOC 2 evidence, and allowing the reconciler to slip removes the only independent missing-event detector. A competent reviewer of document A would call the absence of this set a real gap.
