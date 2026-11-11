# Loop concurrency and plan width

**STATUS: §§ 1 and 2 implemented; § 3 proposes plan-width levers, none built.**

Full-mode `work-loop` runs one request at a time. The
[execution supervisor](work-loop-execution-supervisor.md) owns that procedure.
A policy opt-in lets it run several tasks at once, but no shipped host can
support it, so every adopter runs one at a time. This page states what keeps
one run consistent, when a task may run beside another, and the plan-shape
facts that bound how much parallelism a plan could offer.

## 1. Concurrency inside one run

The supervisor is the only writer of procedure state
([ADR-0144](../adr/0144-work-loop-supervisor-owns-procedure.md) D1). Four rules
keep one run consistent; each has one home.

- **One request at a time:** [request order](work-loop-execution-supervisor.md#request-order).
- **One run lock:** [the run lock](loop-infrastructure.md#the-run-lock).
- **An open attempt freezes trusted files:** [attempts](work-loop-execution-supervisor.md#attempts).
- **Recovery re-derives from commits:** [failure and recovery](work-loop-execution-supervisor.md#failure-and-recovery).

### Retired mechanisms

The transition protocol, the cohort effect registry, and the wave-decision
screen are retired. Their replacements are recorded once, in
[authority migration](work-loop-authority-migration.md) and
[ADR-0144](../adr/0144-work-loop-supervisor-owns-procedure.md).

## 2. Parallel scheduling ships off

Plans declare dependencies, isolation, and read and write sets, not waves.
[ADR-0156](../adr/0156-work-loop-concurrency-needs-attested-read-coverage.md)
is the governing record. It admits two concurrent modes beside the
`sequential` floor, `enforced-allowlist` and `complete-trace`. Each needs a
host attestation, verified by the supervisor, of the attempt's isolation and
every read it makes. The record supersedes ADR-0061 D5's parallel clause and
ADR-0005 D3 and D4.

**The admission rule.** `supervisor-policy.json` ships `concurrency: sequential`. Under
a concurrent mode, one `run-concurrent` request names the first tasks, in the order the
sequential loop would issue them, that are all of these:

- ready, with every dependency landed;
- declaring `Reads:` and `Writes:` with well-formed entries, and no `stub` fence;
- on a run that pinned a launcher, on a POSIX host with Git 2.41 or later and no `merge.*` setting;
- not yet at the reprojection bound; and
- not meeting one another: no task's reads or writes meet another's writes.

The batch holds at most `max_concurrent_attempts` tasks (2 to 8). Any task that fails a
condition runs on the floor, with one reason code in the journal and in `status`. Results land
one at a time, in sequential order, through a pinned three-way apply
([result integration](work-loop-result-integration.md)).

**Known limit.** No shipped host can attest isolation or reads, so every adopter runs on the
sequential floor. The concurrent path is proven only against a test-only fixture launcher.

RFC-0015's 2026-09-25 erratum *"a measurement on nested worktrees"* records the
nested-worktree destruction path and binds no layout constraint, because doing
so would narrow ADR-0005 D7. A constraint requiring task worktrees to be peers
needs a record superseding ADR-0005 in part.

## 3. Plan width

How much a plan could run in parallel is a property of its `**Depends on:**`
graph. These levers are proposals; none is built.

**Two effects are easy to confuse.** `Depends on:` decides **scheduled width**:
which tasks could be ready together.

`**Touches:**` decides **usable width**:
which of those could safely run together. A lever acts on one, never both.

**How the supervisor reads the fields.** The task projector reads
`Depends on:` through the shared plan grammar in `_loop_guards.py`. Cross-spec
forms such as `spec:<slug>/T<n>` are recorded but never scheduled against.

`Touches:` is a pinned field: it is part of a task's revision, so editing it
re-requests that task. Nothing reads `Touches:` to decide order. `Reads:` and `Writes:`
are pinned the same way, and they are what concurrent admission reads (§ 2).

### Scheduled width

- **Report width during authoring.** An author sees a plan's shape only by
  reading it. A read-only width report, as a `new-spec` lint or a supervisor
  status field, is a change this design owes and has not specified.
- **Ask for a reason on each `Depends on:` edge.** The reason goes in the
  parenthetical the parser already drops at `(`, which the template allows
  today. An unparenthesised trailing reason is unsafe: a reason naming any
  `T<n>` invents an edge. `Depends on: none` need not carry one. This does not
  reverse RFC-0015's `Depends on:` grammar decision, whose axis is parser
  strictness. RFC-0015's 2026-09-25 erratum *"decision N is ambiguous"* records
  that the RFC numbers two lists and that a citation must name its own.

### Usable width

**Make `Touches:` mandatory.** This widens nothing. It makes a disjointness
check able to run at all, which it cannot for most tasks.

Completing the
field can also show overlap: RFC-0015 found about 45% file overlap among 55
declared-independent waves, as a lower bound, so a mandate is expected to
*narrow* usable width on a large minority. A finding at authoring still beats a collision at merge. The
field stays a serialise-only input, never a write authority, because tasks
under-name what they touch.

| Contract | Owner | Proposed change |
| --- | --- | --- |
| `Touches:` optionality | `packs/core/.apm/skills/new-spec/assets/plan.md` | optional becomes required for new plans |
| Plan-authoring obligations | `packs/core/.apm/skills/new-spec/SKILL.md` | the width report becomes an authoring step |

No lever removes an edge automatically. A false "ordered" costs throughput; a
false "independent" ships a break.

## Open questions

| Question | Who decides |
| --- | --- |
| Whether the measured nesting hazard reopens RFC-0015 open question 2, whose substrate choice is already resolved as delegate-to-driver | RFC-0015 approver |
| Whether task-cutting guidance belongs in the plan template | `new-spec` owner |
| Where the read-only width report lives — a `new-spec` lint or a supervisor status field | `new-spec` owner |

## Evidence

Probes against this repository on git 2.50.1 on 2026-09-22, none recorded as a
re-runnable harness.

**Worktree topology.** All worktrees are peers on one common `.git`. One
worktree measured 89 MB over 6,521 files.

**Dependency shape**, over 392 plans and 2,543 tasks: 1,083 tasks declare exactly
one dependency; 681 of those (62.9%) name the immediately preceding task in
authoring order, which is 26.8% of all tasks; 1,438 (56.5%) declare no
`Touches:`. These are historical plans, so the figures measure authoring habit.

**Graph width**, over the 359 plans carrying a complete dependency declaration.
Width is the most tasks that could be ready at once.

| | actual | if previous-task edges dropped |
| --- | ---: | ---: |
| median maximum width | 2 | 3 |
| median depth | 4 | 3 |
| plans that cannot parallelise at all | 23.7% | 0.8% |
| plans whose width would increase | — | 65.2% |

The second column is a ceiling, not a forecast: it assumes every previous-task
edge inside these 359 plans is spurious, and some are genuinely sequential work
written in order. The two cases produce identical text.
