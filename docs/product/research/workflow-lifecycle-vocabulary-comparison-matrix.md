# Workflow lifecycle vocabulary — adoption bake-off

> Discipline: applied (practitioner-pattern survey)

Commissioned 2026-09-10 after the
[OpenTelemetry envelope survey](agent-loop-otel-envelope-survey.md) established
that no LLM observability platform models a workflow phase, a gate outcome, a
retry cap, a budget limit, or a stall — while the workflow orchestrators have
modelled all five for years. The question this artifact answers is narrower and
practical: **can the work-loop adopt an existing vocabulary for those concepts
instead of defining its own?**

The answer is no for any vocabulary wholesale, and yes for two design shapes
and two terms. `core` 2.25.14 implements that conclusion; the code comments in
`loop-engine.py` cite the result rather than restating the reasoning.

Findings are labelled by evidence class. Vendor documentation, vendor blog, and
third-party analysis are distinguished throughout, and several documents from
one vendor count as one source.

---

## The rubric, derived before the candidates were read

Scoring against concepts taken from the candidates would have made the winner
whichever system was read last. These ten come from the engine's own transition
table, computed rather than recalled:

| # | Concept | In the engine |
| --- | --- | --- |
| 1–2 | Run start, run end | `init`; `done` → `DONE` |
| 3 | Phase occupied | 10 states |
| 4 | Phase transition | 15 event names, 18 distinct transitions |
| 5 | Gate arrival | 6 gate states |
| 6 | Gate outcome, three kinds | deterministic, review, human |
| 7 | Retry attempt and cap | two counters, both capped at 5 |
| 8 | Cap exceeded | guard refusal |
| 9 | Cap waived | `--allow-retry-cap-override` |
| 10 | Backward edges | **8 of 18 transitions** |

That last row decided one whole arm of the bake-off. Seven of the fifteen event
names are *exclusively* backward edges, and `contract-amendment` returns five
phases, from `CODE-IMPLEMENTATION` to `SPEC-PLAN-DRAFTING`. Rework is not an
exception path in this loop; it is 44% of the machine.

---

## Coverage

| Our concept | OTel CI/CD (RC) | Temporal | Step Functions | Airflow |
| --- | --- | --- | --- | --- |
| Phase occupied | 3 values | via history | 5 statuses | 13 states |
| Named transition events | — | 60, closed enum | — | — |
| Gate outcome ≠ error | no | no | task token | `AWAITING_INPUT` |
| Three gate kinds | no | no | no | no |
| Attempt N of M | no | `Attempt` | `MaxAttempts` | `try_number` |
| Cap exceeded | no | `RETRY_STATE_MAXIMUM_ATTEMPTS_REACHED` | timeout only | no |
| Cap waived | no | no | no | no |
| Stall | no | three-way split | `HeartbeatSeconds` | zombie → `FAILED` |
| Backward edges | n/a | yes | yes | impossible |
| Multi-vendor standard | **yes** | no | no | no |

Serverless Workflow v1.0 (CNCF) is a genuine multi-vendor spec with a retry
limit and event-driven gates, but it models authoring-time DSL rather than
observability-time telemetry, and adoption outside one implementation is thin.
It is excluded from the table for that reason, not overlooked.

---

## Three findings that decided it

### The DAG engines cannot express the majority case `[high]`

Airflow raises `CycleError` at DAG-load time; Dagster's asset and op graphs are
acyclic; and Prefect's Python `while` loop creates a *new task run object* per
iteration, so the recorded graph stays acyclic too. All three express rework as
"start a new run." None can route control back to an executed step within one
run, which is what 8 of our 18 transitions do.

### The one real standard is deliberately poorer than its sources `[high]`

OTel's CI/CD semantic conventions reached Release Candidate and were informed by
GitHub Actions and GitLab CI — then dropped `action_required`, `manual`,
`neutral`, and `stale` on the way in. Those are precisely the human-gate terms
this loop needs. `cicd.pipeline.result` carries six values
(`success`, `failure`, `error`, `timeout`, `cancellation`, `skip`) and no gate,
retry, budget, or stall concept at all.

It does have one property the orchestrators lack: it is observability-time
*attributes*, not an execution model, so it constrains no topology and our
cycles are not a problem for it. That makes it viable as a partial base where
the DAG engines are not viable at all.

### Nobody models a waiver, and nobody is filling the gap `[moderate]`

No candidate has a concept for a human deliberately lifting a limit. That is
consistent rather than surprising: a waiver is a governance concept, and none of
these systems model human authority over their own constraints.

Nor is anyone standardising this surface. The agentic semantic-convention
proposal covers structural entities — Tasks, Agents, Teams, Memory — with no run
state, gate outcome, retry cap, budget, or stall. The 2022 Workflows Community
Summit named "absence of a common vocabulary" a blocking challenge, and it is
still open. Downgraded to `[moderate]` only because proving a negative across
every working group is not possible; the searched surface is named in Sources.

---

## Adopted

| # | Taken | From | Why |
| --- | --- | --- | --- |
| A1 | Outcome and reason as orthogonal fields | Temporal's `RetryState` beside `WorkflowExecutionStatus` | One field cannot mean both "failed once, retrying" and "out of attempts" |
| A2 | `success` / `failure` result values | `cicd.pipeline.result` | Free alignment on the one part that genuinely fits |
| A3 | `awaiting_input` | Airflow 3.1+ state; GitHub's `action_required` | Two mature systems already agree; a third spelling helps nobody |

**Not taken, with reasons.** Temporal's three-way liveness split
(`schedule_to_start` / `start_to_close` / `heartbeat`) distinguishes "no worker
took it", "it is slow", and "it went silent". This loop has no worker pool or
queue, so two of those three have no referent; adopting the vocabulary would
imply distinctions the system cannot make. Airflow's `try_number` was not taken
because the engine does not own the counters — see the follow-ons in the
companion survey. And no vocabulary was adopted wholesale: `cicd.*` covers one
of our ten concepts, so adopting its namespace would mean privately extending it
for the rest while implying a conformance that does not exist.

`waived` remains ours because there is nothing to align to.

---

## Standing versus legibility

Worth separating, because it is easy to conflate. Airflow's vocabulary looks
universal — Astronomer, MWAA, Cloud Composer and Azure Managed Airflow all use
it — but only because those products *run Airflow*. Dagster's 54-member
`DagsterEventType` has been referenced in OpenLineage discussion without
ratification. Temporal's 60-member event enum is its own protobuf with no second
implementer.

So adopting `AWAITING_INPUT` buys **legibility** to people who know Airflow. It
does not buy **compliance**, because there is no body to comply with. Only A2
touches an actual standard, and that standard is Release Candidate, so even
there a rename before stabilisation is possible.

---

## Known unknowns

- **Known-unknown:** whether `cicd.*` will grow gate, retry, or budget concepts
  as the CI/CD SIG continues. Would be closed by a published SIG roadmap.
- **Known-unknown:** whether AWS Step Functions' state machines admit true
  backward edges via `Choice`. Not confirmed in the retrieved material; it
  affects only a candidate already excluded on standing.
- **Unknowable:** whether the agentic semconv proposal will eventually cover
  lifecycle states. It is in planning with no published schema, so no evidence
  settles it — and a name chosen against it today could be invalidated.

---

## Sources

**Primary.** OpenTelemetry CI/CD spans, metrics, and attribute registry;
`temporalio/api` `workflow.proto` and `event_type.proto`; Temporal retry-policy,
timeout, heartbeat, and OpenTelemetry-plugin documentation; Airflow
`airflow/utils/state.py` and the human-in-the-loop tutorial (AIP-90); Dagster
`dagster_run` and `events` sources and run-monitoring docs; Prefect states,
retries, and zombie-flow detection; AWS Step Functions task-state and execution
API; CloudEvents v1.0.2; CNCF Serverless Workflow v1.0.0; the OTel
agentic-semconv proposal.

**Secondary and third-party.** GitHub Actions and GitLab CI conclusion
vocabularies as community-documented; Astronomer's human-in-the-loop guide; the
2022 Workflows Community Summit report.

**Independence note.** Airflow's state vocabulary appears in four managed
products, but all four run Airflow itself, so they corroborate its popularity
and not its independence. They are counted as one source.
