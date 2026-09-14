# Loop telemetry events: six of the eight are derivable, and no new event is warranted

- **Run date:** 2026-09-13
- **Owner:** eugenelim, Platform Core maintainer
- **Against:** `core` 2.25.26, `agentbundle` 0.44.1, commit `f0a04a223`, CPython 3.13.13
- **Verdict:** **six** of the eight events named for INI-005 can be computed from
  the thirteen fields `loop-engine` already writes. The other two fail for
  different reasons, and neither is fixed by adding an event:
  - `budget-exceeded` splits. Its **time** half is derivable exactly. Its
    **token** half is not derivable, and no event would carry it, because the
    token count does not exist in the emitting process at all.
  - `gate-waived` names a fact the loop does not have. The nearest field,
    `waived`, records only that the caller passed an override flag on that
    transition.

  **No new event is proposed, and none is warranted.** A third gap is recorded as
  a finding: the per-event metadata contract is unsatisfiable as written.

## The question, and the constraint on the answer

The brief was to establish the event mapping *as measurement*: which of the
roadmap's eight events are derivable. It carried a hard constraint. **Do not
introduce new events if the measurements can come from old ones.**

So this document proposes no event. Where something does not fall out of the
envelope, it is recorded below as a finding with an owner. Adding an event is the
owner's decision, and the point was to find out whether that decision has to be
made at all. For the one undecidable case it does not, because no event would
carry the missing data.

## Where the eight come from, and who owns them

They are named in prose in three files — [`roadmap.md`](../roadmap.md), this
directory's [OTel envelope survey](agent-loop-otel-envelope-survey.md), and
[`ecosystem-overview.md`](../shaping/ecosystem-overview.md) — and **in no schema,
no code, and no test**. A grep for each of the eight names across the repository
returns only Markdown.

`roadmap.md`'s *Shaping queue — research threads* section is where they are
listed, quoted exactly:

> **Telemetry events schema.** What events matter for exception-based review:
> `spec-started`, `gate-reached`, `gate-passed`, `gate-failed`, `gate-waived`,
> `budget-exceeded`, `spec-stalled`, `spec-shipped`. What metadata each event
> carries; how events map to alert thresholds configurable per project. Feeds
> INI-005 RFC.

**`ecosystem-overview.md` is the defining source, not `roadmap.md`.** The roadmap
lists the names. [`ecosystem-overview.md` § INI-005](../shaping/ecosystem-overview.md)
says what two of them mean. Those parentheses decide two verdicts below:

> Core events: `spec-started`, `gate-reached`, `gate-passed`, `gate-failed`,
> `gate-waived`, `budget-exceeded` **(time or token)**, `spec-stalled` **(no
> progress past a threshold)**, `spec-shipped`. Each event carries: spec slug,
> milestone, agent identity, timestamp, gate name (where applicable), and outcome
> metadata.

**Which INI-005 owns them.** The identifier names two different initiatives, and
[RFC-0064](../../rfc/0064-ini-001-ai-native-ecosystem.md) records the collision:
`workspace.toml` reuses INI-003/005/006/007 for internal repository initiatives
in a namespace separate from the ecosystem overview's. These eight belong to the
**ecosystem** INI-005 — *Infra & Observability*. They are **not**
`workspace.toml`'s INI-005 (AgentBundle Portable Catalogue Tooling), which is
unstarted and tracked in no queue here. That is why the eight have no schema:
nothing has been built to carry them.

## What the envelope actually holds, measured

Measured by driving real transitions, not by reading the source. Every line of a
29-transition run carried the **same thirteen keys**, and a second 11-transition
run reproduced the count:

```
['at', 'awaiting_input', 'budgets', 'event', 'from', 'phase_s',
 'phase_started_at', 'result', 'run_id', 'seq', 'spec', 'to', 'waived']
```

`budgets` is a nested object with four keys —
`implementation_retry_count`, `max_implementation_retries`,
`review_retry_count`, `max_review_retries`. Its **values are integers or
`null`**: the snapshot is typed `dict[str, int | None]` and keeps `null` for a
counter it cannot read, so a consumer can tell "not recorded" from "zero".

Two structural facts decide most of the mapping.

**Every event goes through one emission site.** `loop-engine.py` builds a single
`pending_data` literal and writes it for every transition, so the envelope cannot
vary by event. Measured: one distinct key-set across all 29 lines.

**`result` is populated for 10 of the FSM's 15 events.** `_GATE_RESULTS` maps
five to `success` (`reviewers-clean`, `spec-approved`, `plan-approved`,
`gates-clean`, `done`) and five to `failure` (`findings-remain`,
`spec-rejected`, `plan-rejected`, `gates-failed`, `blocker-applied`). The other
five — `spec-ready`, `plan-locked`, `wave-complete`, `wave-passed`,
`contract-amendment` — emit `result: null`. Those are routine routing steps, and
they are a large minority: **11 of the 29 measured lines** carried `null`. A
consumer counting passes and failures must filter `result != null` first, or it
will read routing as failure.

## The mapping

| Roadmap event | Verdict | Computed from |
| --- | --- | --- |
| `spec-started` | Derivable | first line per `run_id` (`seq == 1`); start time is its `phase_started_at` |
| `gate-reached` | Derivable | `awaiting_input == true` for human gates; `to` for the machine gate |
| `gate-passed` | Derivable | `result == "success"` |
| `gate-failed` | Derivable | `result == "failure"` |
| `gate-waived` | **Not derivable** | `waived == true` records only that an override flag was supplied, not a waived gate verdict, and not that a cap fired — finding D1 |
| `budget-exceeded` | **Time half derivable; token half not derivable** | `phase_s` for time; nothing carries tokens — finding D2 |
| `spec-stalled` | Derivable at the consumer | absence of a later line for `run_id`, against an external clock and a threshold |
| `spec-shipped` | Derivable | `event == "done"` — **not** `to == "DONE"` |

### `spec-started` — derivable

`init` writes no line; `events.jsonl` is created empty. The run's first *line* is
therefore its first transition, `seq == 1`. Its `phase_started_at` back-dates to
what `init` wrote, so the run's true start is on the line even though `init`
emitted nothing.

**The start time is a measurement, not a lower bound — proved deliberately.**
Driving `init`, sleeping three seconds, then firing one transition:

```
init wrote last_transition_at = 2026-09-14T01:21:39Z
seq1 phase_started_at         = 2026-09-14T01:21:39Z   <- identical
seq1 at                       = 2026-09-14T01:21:43Z
seq1 phase_s                  = 4
```

The first line carries the run's real start, to the second, without `init`
emitting anything. This retires a standing recommendation to add an init event —
see *What this supersedes*.

### `gate-reached` — derivable, and "gate" has a precise meaning here

`awaiting_input` is `true` exactly when the transition's destination is one of
the three human-wait states. Measured — true on exactly three lines of 29:

| Arrived at | Via |
| --- | --- |
| `SPEC-HUMAN-GATE` | `reviewers-clean` |
| `PLAN-HUMAN-GATE` | `spec-approved` |
| `CODE-HUMAN-GATE` | `reviewers-clean` |

That is the repository's own definition of a gate — the same three states carry
the questions the engine surfaces to a control plane. For the machine
verification gate, `to == "CODE-VERIFICATION"` is the equivalent.

### `gate-passed` / `gate-failed` — derivable

`result` is the field, and it is the one the exporter's mapping profile already
routes to OTLP severity. The five `null` events are neither passes nor failures.

### `gate-waived` — not derivable as defined; a narrower fact is

`waived` is `true` on exactly one kind of line. It is set from
`--allow-retry-cap-override`, and the engine **refuses that flag on any event
except `findings-remain`**. Measured: in a run driven to the review retry cap,
exactly one line of twenty carried it:

```json
{"seq": 20, "event": "findings-remain", "from": "CODE-REVIEW",
 "to": "CODE-IMPLEMENTATION", "result": "failure", "waived": true}
```

So `waived: true` means **"the caller passed `--allow-retry-cap-override` on
this transition"**. It does **not** mean a cap was reached, it does not mean a
gate's verdict was waived, and the line carries no caller identity, so it does
not establish that a person decided anything.

**The field does not imply the cap fired — the repository's own test proves it.**
`test_waived_is_true_with_the_retry_cap_override` drives `spec-ready` then
`findings-remain --allow-retry-cap-override` at a retry count of **0 of 5**, and
asserts `waived is True`. The guard at `loop-engine.py:1375` only restricts the
flag to `findings-remain`; it does not require that anything be capped. So the
field records an *intent supplied by the caller*, not a *limit that was hit*.

`result` stays `failure` either way: the gate did not pass.

`ecosystem-overview.md`'s state-persistence paragraph asks for "gate outcomes
(what passed, what failed, **what was waived**)", which reads as a waived gate
*verdict*. **No such concept exists in this FSM** — a gate verdict cannot be
overridden; only a retry cap can.

**Finding D1 — `gate-waived` names a fact the loop does not have, and `waived`
is not a substitute. Owner: the INI-005 RFC author.** Two things are true at
once. A waived gate *verdict* does not exist in this FSM, so there is nothing to
emit and no event would help. And `waived` is weaker than it looks: it marks a
supplied flag, not a limit that was hit, so a consumer reading it as "this run
hit its cap" would be wrong on the very first transition of a run that never
came close. The options are to drop the event, or to define it as "an override
flag was supplied" and accept that narrower meaning.

### `budget-exceeded` — the time half is exact, the token half is structurally absent

`ecosystem-overview.md` defines this as **"(time or token)"**. Those two halves
have opposite answers, which is why an earlier draft of this document got the
event wrong by mapping it to the retry counters instead.

**Time — derivable, exactly.** `phase_s` is per-transition elapsed seconds. It
reconciles two independent ways on the measured corpus:

```
sum(phase_s) over all 29 lines            = 27
last `at` minus first `phase_started_at`  = 27.0
```

They agree. So a run's wall-clock consumption is on the lines, with no gaps and
no double counting. A per-project time budget is a threshold over either
expression.

**Token — not derivable, and no event could carry it.** Nothing in the thirteen
fields carries a token count, a model name, or a session identifier; a
`milestone` and an agent identity are absent too. This is not an oversight in the
envelope. `telemetry.md` § 4 has already settled this, in terms that answer the question
before it is asked: *"So a pack cannot see token use. That is settled, not
postponed. No field or flag will supply it, because the number is not visible
from where this code runs. If someone proposes adding one, this paragraph is the
answer."*

§ 1 gives the reason: a pack *"cannot record what the model did, because the tool
running the session makes the model call and a pack never sees the reply."* The
count does not exist anywhere in the emitting process, so an event carrying it
would carry a field the writer cannot populate.

**Finding D2 — the token half of `budget-exceeded` is not derivable here, and
this log is the wrong source for it. Owner: the INI-005 RFC author.** Token
accounting belongs to whatever makes the model call — the harness, per INI-003 /
INI-004 — not to a pack that never sees the reply. What would have to change is
an upstream data source, not this envelope. The constraint therefore binds in its
strongest form: not merely "do not add an event", but "an event would not work".

**Also true, and separate:** the engine refuses a transition *at* a retry cap
rather than past it, so even for retries the observable condition is **reached**,
not exceeded. Driven to 5/5, `findings-remain` was refused outright. A rule
written with `>` instead of `>=` would never fire. The retry counters are visible
on every line via `budgets`, one transition late — see below — but they are
**not** what INI-005 means by budget.

### `spec-stalled` — derivable at the consumer, and no event could do better

`ecosystem-overview.md` defines it as **"(no progress past a threshold)"**, which
is exactly a consumer-side rule. A stall is the **absence** of a next line, and
`events.jsonl` is append-only with no heartbeat. The derivation is:

> for a `run_id` whose last line has `to != "DONE"`, *now* minus that line's `at`
> exceeds a per-project threshold.

That needs an external clock and a threshold, both properly the consumer's —
`roadmap.md` already says "alert thresholds configurable per project".
`awaiting_input` refines it usefully: a run parked at a human gate is *waiting*,
which most projects will want to hold to a much longer threshold than a run that
stopped mid-implementation.

**This is the case where adding an event would be incoherent.** A stalled run is
a process that is no longer running; it cannot emit a record announcing that it
has stopped. Any stall signal must be computed by an observer from silence.

### `spec-shipped` — derivable from the event, not from the state

`event == "done"`. The transition is guarded — the engine refuses `done` unless
the spec reads `Status: Shipped` — so the line means the artifact state, not just
a state-machine edge.

**`to == "DONE"` is not an equivalent test.** In `spec-plan` mode the FSM reaches
`DONE` by a different edge, `("SPEC-PLAN-APPROVED", "plan-locked"): "DONE"`, on a
run that has no implementation and whose spec is `Approved`, not `Shipped`. That
line carries `result: null`, because `plan-locked` is not in `_GATE_RESULTS`.
Keying on the destination state would report every spec-plan run as a shipped
spec.

## A second gap: the per-event metadata contract is unsatisfiable

`ecosystem-overview.md` requires that "each event carries: spec slug, milestone,
agent identity, timestamp, gate name (where applicable), and outcome metadata."
Measured against the envelope:

| Required | Available | From |
| --- | --- | --- |
| spec slug | yes | `spec` (repo-relative spec directory) |
| timestamp | yes | `at`, plus `phase_started_at` |
| gate name | yes | `to`, with `event` for the edge |
| outcome metadata | yes | `result`, `awaiting_input`, `waived`, `budgets` |
| **milestone** | **no** | absent — it lives in `workspace.toml`, not on the line |
| **agent identity** | **no** | absent — `run_id` identifies a *run*, not an agent |

**Finding D3 — two required metadata fields are not on the line. Owner: the
INI-005 RFC author.** Both are joinable rather than missing: `spec` is a key into
`workspace.toml` for the milestone, and agent identity is properly the harness's
(INI-003 / INI-004), which is also where a session identifier would come from. No
new event is proposed; this is a note that the metadata clause needs either a
join or a narrower claim.

## What this supersedes

The [OTel envelope survey](agent-loop-otel-envelope-survey.md) piloted this
question on 2026-09-10 and reached a more pessimistic answer: it classed
`gate-waived`, `budget-exceeded` and `spec-stalled` as *"Needs an envelope
change"*, and recommended an init line for `spec-started`. **Core 2.25.14 added
`waived`, `budgets` and `phase_s` after that survey was written.** Its table
carries inline notes acknowledging the first three as closed or partly closed;
its body text was not revised and still asserts the pre-2.25.14 position. Settled
against `core` 2.25.26:

| Survey claim | Status now | Evidence |
| --- | --- | --- |
| "The retry counters are invisible to the event log" | **Superseded** | `budgets` carries all four counters on every line; measured 0 → 1 across seq 16/17 |
| "a run's true start time is recorded nowhere"; "One init line closes this" | **Superseded** | seq 1's `phase_started_at` equals `init`'s own timestamp exactly, across a deliberate 3 s gap |
| "every first-phase duration is a lower bound rather than a measurement" | **Superseded** | `phase_s` measured the full 4 s, not a truncated remainder |
| "`gate-waived` is unreachable" | **Partly superseded** | the `waived` field is reachable and was captured; but it does not carry a waived gate *verdict*, so the roadmap event still has no source — finding D1 |
| "`budget-exceeded` … needs an envelope change" | **Gap stands, remedy refuted** | the token gap is real, but no envelope change closes it: the data is not in this process at all — finding D2 |

The survey's remaining structural observation also stands and is not disputed:
the eight roadmap names cannot express `contract-amendment`, so mid-run contract
rework has no roadmap event. That is a gap in the *roadmap's* vocabulary, not in
the envelope.

**Why this matters to the constraint.** One live recommendation to add an event
existed in this repository — the init line. It is now refuted by measurement
rather than by argument.

## One limit that applies to every derivation above

**Emission is best-effort, so absence is not proof.** The outbox writes are
wrapped in exception handlers that warn to stderr and continue. The engine
completes the transition either way. Losing a state machine to a telemetry
failure would be the worse trade.

So a missing line means "either it did not happen, or the write failed". The
stall rule inherits this most sharply, since it reads silence as signal.

Recorded so a consumer does not treat the log as a complete ledger. Making it
complete is a durability change to the engine, not an event.

## The retry counters, and their one-transition lag

Not one of the eight, but load-bearing for anyone reading `budgets`.

**The bump emits no line of its own.** `loop-cohort record-attempt` and
`loop-cohort review record` mutate `state.json` and write nothing to
`events.jsonl`. Measured twice: 7 lines before `record-attempt` and 7 after; 21
before `review record` and 21 after.

**The bump surfaces on the next transition.** The counter is snapshotted when a
transition is built, and the cohort bumps it afterwards:

| seq | event | `implementation_retry_count` |
| ---: | --- | ---: |
| 16 | `gates-failed` | 0 |
| 17 | `wave-complete` | **1** |

`telemetry.md` § 5.1 already documents this ("`budgets` is a copy, not the
original … the line shows where they stood one round ago"); the measurement
confirms the documented behaviour. Attribute a counter to the *preceding* line.

## What was not measured, and why

`contract-amendment` is the one FSM event no line was captured for. Reaching it
requires a completed task carrying an evidence binding, which a scratch run
cannot produce (`contract-amendment cohort mutation failed: completed task has no
evidence binding`). Its envelope is nonetheless fixed by the single shared
emission site, and its `result: null` by its absence from `_GATE_RESULTS`. That
is a structural argument, not a measured line, and is flagged rather than
smoothed over. It affects none of the eight.

## Re-running this

Self-contained; writes only to a throwaway directory. Takes about ten seconds.

```sh
REPO_ROOT=/path/to/this/repo
S="$REPO_ROOT/packs/core/.apm/skills/work-loop/scripts"
cd "$(mktemp -d)" && mkdir -p repo/docs/specs/demo && cd repo
git init -q . && git config user.email t@e.com && git config user.name T
printf -- '- **Status:** Approved\n' > docs/specs/demo/spec.md
printf -- '- **Status:** Approved\n\n## Tasks\n\n### T1: a\n\n**Depends on:** none\n\n**Touches:** `a.py`\n\n**Tests:**\n- goal-based.\n\n**Done when:** done.\n' > docs/specs/demo/plan.md

RUN_ID=$(python3 "$S/loop-engine.py" init docs/specs/demo --mode code --json \
         | python3 -c 'import json,sys; print(json.load(sys.stdin)["run_id"])')
python3 "$S/loop-cohort.py" init docs/specs/demo --run-id "$RUN_ID"
for e in spec-ready reviewers-clean spec-approved plan-approved; do
  python3 "$S/loop-engine.py" transition docs/specs/demo "$e"
done
python3 "$S/loop-cohort.py" approve-plan docs/specs/demo --expect-run-id "$RUN_ID"
python3 "$S/loop-cohort.py" schedule     docs/specs/demo --expect-run-id "$RUN_ID"
python3 "$S/loop-engine.py" transition   docs/specs/demo plan-locked

# a failed gate, then the cohort bump that emits no line of its own
python3 "$S/loop-engine.py" transition docs/specs/demo wave-complete
python3 "$S/loop-engine.py" transition docs/specs/demo gates-failed
wc -l < .loop-run/events.jsonl                 # 7
python3 "$S/loop-cohort.py" record-attempt docs/specs/demo --phase implement \
        --cycle-id "$RUN_ID:2" --expect-run-id "$RUN_ID"
wc -l < .loop-run/events.jsonl                 # still 7 — the bump emits nothing

python3 "$S/loop-engine.py" transition docs/specs/demo wave-complete
python3 "$S/loop-engine.py" transition docs/specs/demo gates-clean
printf -- '- **Status:** Shipped\n' > docs/specs/demo/spec.md
python3 "$S/loop-engine.py" transition docs/specs/demo reviewers-clean
python3 "$S/loop-engine.py" transition docs/specs/demo done

# every line carries the same thirteen keys
python3 -c "import json;print(sorted({len(json.loads(l)) for l in open('.loop-run/events.jsonl') if l.strip()}))"
```

**What this recipe reproduces:**

- the thirteen-key envelope — the last command prints `[13]`;
- the `result` mapping across a pass and a fail;
- `awaiting_input` at the gates;
- the `event == "done"` ship line;
- the counter lag. The `wc -l` pair prints `7` twice. That is the result most
  likely to be assumed rather than checked.

**What it does not reproduce**, because each needs a different drive:

- *The 29-line corpus and the 11-of-29 `result: null` count.* Add the rejection
  edges (`findings-remain`, `spec-rejected`, `plan-rejected`, `blocker-applied`)
  and a second wave, so `wave-passed` becomes legal.
- *The delayed-init measurement.* Read `engine-state.json`'s
  `last_transition_at` **before** firing anything — the first transition
  overwrites that field with its own time — then sleep, fire one transition, and
  compare the value you saved against seq 1's `phase_started_at`.
- *The `waived: true` line.* Exhaust `max_review_retries`. Each round is a **full
  loop**, not a repeated pair — `loop-cohort review record` does not move the
  engine, so a second `wave-complete` from `CODE-REVIEW` is an illegal
  transition. Repeat five times:

  ```
  wave-complete   # CODE-IMPLEMENTATION -> CODE-VERIFICATION
  gates-clean     # CODE-VERIFICATION   -> CODE-REVIEW
  loop-cohort review record … --fingerprint <64 hex>
  findings-remain # CODE-REVIEW         -> CODE-IMPLEMENTATION
  ```

  Each `review record` increments the count, and `findings-remain` is refused
  once the new count reaches the cap. So the **fifth** round is where it stops:
  its `review record` makes the count 5, and its `findings-remain` is refused at
  5/5. Repeat that refused transition with `--allow-retry-cap-override`, which is
  accepted and writes a `waived: true` line.

  Note this is the long way round, taken to observe a *capped* run. If all you
  need is the field itself, one `findings-remain --allow-retry-cap-override`
  immediately after `spec-ready` also writes `waived: true`, at 0/5 — which is
  the point of finding D1.

## Where the three findings went

D1, D2 and D3 are all decisions for the same owner, so they are recorded together
as one shaping intent rather than three:
[`loop-telemetry-event-vocabulary`](../intents/loop-telemetry-event-vocabulary.md).
It is deliberately non-dispatchable — held by repository maintainers, with no
`workspace.toml` entry — because the initiative that will consume it has not
started.

## What this does not settle

The roadmap sentence asks two further questions this measurement does not answer:
what metadata each event carries beyond derivability (finding D3 narrows this),
and how the events map to per-project alert thresholds. Both are consumer-side
design and belong to the INI-005 RFC. What is settled is the input to that RFC. **The envelope is sufficient for six of
the eight. Of the remaining two, one needs an upstream data source and the other
names a fact the loop does not have — neither is a new event. The RFC can be
written without changing what this repository emits.**
