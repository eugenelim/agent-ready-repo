# Blind judgment — control pair

Judge: `codex exec`, model `gpt-5.6-sol`, provider openai, reasoning effort high.
Blind: the judge was given the brief and two documents labelled A and B, and was
told only that both answer the same brief and were produced by two independent runs
of the same procedure. It was told nothing about an overlay, a router, or which
document carried what.

Label mapping, fixed by a recorded coin flip before the payload was built
(`a-is-A`): **Document A = `arm-a.md`, Document B = `arm-c.md`**.

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

- **Database-outage intake durability:** A requires webhook acceptance to continue while Postgres is unavailable and verifies that the bounded SQS backlog can drain after recovery.
- **Provider event-history availability:** A treats the existence, history window, and usable rate limit of the provider’s events-list API as an unresolved dependency of reconciliation.
- **Semantic drift:** A identifies the risk that the provider changes a field’s meaning without changing its shape, allowing syntactically valid but incorrect billing facts.
- **Payload-data classification:** A asks which raw payload fields are personal data and whether field-level redaction is required.
- **Reconciliation credentials:** A identifies the provider API credential as a separate egress trust boundary that must be controlled.
- **Downstream backpressure:** A considers how a stalled monolith consumer could exhaust shared storage and impair capture, requiring capacity alarms and operational containment.
- **Shadow-endpoint feasibility:** A explicitly questions whether the provider can deliver simultaneously to the old and new endpoints, on which the proposed shadow rollout depends.
- **Schedule-safe partial migration:** A treats the two-engineer, nine-event-type constraint as a delivery risk and preserves a working hybrid through per-event-type cutover.
- **Forensic-query performance:** A gives the 90-day customer evidence query a measurable response-time target rather than requiring only that the query exist.

Q2.

- **Reliable precedence metadata:** B questions whether every event type supplies a monotonic sequence and identifies provider timestamps as a potentially unsafe fallback for out-of-order events.
- **Correction identity:** B explicitly requires provider corrections to arrive as new envelopes so immutable storage and event-ID deduplication do not discard them.
- **AWS ingress limits:** B calls out API Gateway integration limits and Lambda cold-start behavior as dependencies of the acknowledgement-time target.
- **Database connection pressure:** B requires Lambda concurrency to remain within the Postgres connection budget and monitors connection saturation.
- **Retention-job safety:** B addresses how expired records are actually removed through bounded deletion batches with observable progress.
- **Applicable control conventions:** B flags the absence of known SOC 2 evidence conventions, alerting standards, and prior billing architecture decisions that the implementation must follow.

Q3.

**Document A-only set: load-bearing.** The set contains direct correctness and availability obligations from the brief: B’s synchronous database-before-ack path has no demonstrated intake behavior during a subsystem Postgres outage, while unverified rollout and reconciliation dependencies could invalidate its recovery plan. Semantic drift, sensitive raw payloads, downstream backpressure, and a resource-constrained migration are also credible routes to silent billing errors, audit exposure, or an incomplete cutover, so a competent reviewer would call their absence a real gap.

**Document B-only set: load-bearing.** A relies on timestamp-based monotonic handling without establishing that every provider event has trustworthy precedence data, which can leave cancelled subscriptions stale despite successful delivery. Its acknowledgement target also lacks the platform-limit and database-connection analysis B raises, and its retention and governance obligations lack an executable purge mechanism and confirmed control conventions; together these are real correctness, capacity, and audit gaps.
