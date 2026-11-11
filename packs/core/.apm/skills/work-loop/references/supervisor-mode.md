# Reviewer fan-out and the implementer brief

> **Loaded when:** reviewers run in parallel (pre-approval review or light mode), or an
> `implementer` is briefed for an `implement-task` request. The supervisor owns task order and attempts
> (see [`supervisor.md`](supervisor.md)); this file owns the two things the
> controller still does by hand: how a fan-out round runs, and what an implementer
> is told.

**Dispatch is sequential.** The supervisor issues one `implement-task` request at
a time, in the plan's dependency order, and the controller dispatches one `implementer` at a time,
one per request. It does not fan implementers out, and it does not
create worktrees or branches for them: the supervisor computes each attempt's
change set from the execution root itself, and any change to the spec, the plan,
the records the spec cites, the installed skill, Git control state, or `delivery/`
refuses the attempt. Reviewer (read) fan-out in pre-approval review and light mode is a separate, always-safe path, and
the discipline below governs it; in a full-mode run the supervisor issues one `review-role` request at a time, so answer each in turn.

## The implementer brief

<!-- Bundled-fixes carve-out — kept in sync across four sites:
  work-loop/SKILL.md, implementer.md, adversarial-reviewer.md, and
  work-loop/references/supervisor-mode.md. -->
Dispatch an `implementer` for an `implement-task` request with a brief that includes: the task
ID, the plan-task body, the execution root, paths to the spec +
plan, and an explicit **bundled-fixes authorization line** —
"Bundled fixes authorized per the carve-out in `work-loop/SKILL.md`
(EXECUTE phase). A change may ride along when all four hold: (i) it
fires no risk trigger on its own, so it would run in light mode
standalone; (ii) it involves no behavior change and no unresolved
design call, and where a design call was resolved, that resolution
changes no convention, contract, or published interface; (iii)
you can state how it was verified — a command with a zero diff on
re-run, a search with no remaining references, or a comparison
against a named authority that the change agrees with; and (iv) it
changes no file that defines what an agent may do — a skill, an
agent definition, a hook, a command, or anything one of those
loads — and no file stating this test. Clause (iv) fails closed:
where you cannot tell whether a file is one of those, it is, and
the change is not a ride-along. Clause (ii) is not decidable from
this text alone. Before you evaluate it, read
`work-loop/references/bundled-fixes.md`: what counts as recognising
a design call, what resolves one, how attendance is read, what to
do when nothing resolves it, and what is refused whatever the
answer. The risk triggers are the canonical block in
`work-loop/SKILL.md` (§ Select: light or full mode); a mirror names
the skill and lists no trigger. This run is <attended|unattended>.
Report each ride-along under `Bundled fixes:` in your output."
If a particular task should run without the carve-out (e.g. a
high-blast-radius migration), omit the authorization line; the
implementer defaults to no-carve-out and routes everything to
"Out of scope observed".


## Collecting `Bundled fixes:`

**Lift `Bundled fixes:` into the PR body.** Each implementer report
may carry a `Bundled fixes:` section listing ride-alongs landed
under the carve-out. After the run is ready, collect those lines
from every ready report, dedupe by exact-string match (falling
back to operator judgment when two lines describe the same change
in different words, never merging two entries whose recorded
questions differ, nor two whose recorded answers to the same
question differ), and emit a single `Bundled fixes:` section
in the PR description below the
[standard template](../assets/pull-request-template.md). If no
implementer landed ride-alongs, omit the section.


## Parallel-dispatch discipline

REVIEW fan-out, and any other parallel dispatch, shares these rules:

- Issue all subagent invocations in a single message (one Agent use per target).
  Do not call sequentially.
- Barrier-wait: don't issue follow-on Agent calls until every subagent in the
  round has returned.
- Timeout, tool error, or missing report = `failed` for that target. Same as
  substantive failure; don't retry silently.
- REVIEW fan-out: persist each raw report, classify it with `review-artifact.py raw-classify`,
  adjudicate by path every one that is not footer-free `clean`, and merge only the
  sustained main-loop results; never read N raw reviewer reports into the
  controller to aggregate them. Persistence is unconditional — a fan-out round
  where every reviewer returned clean still leaves one artifact per reviewer.

## Single-agent fallback

If no `implementer`-matching subagent is installed in the consumer's IDE, drop
back to single-agent mode: the controller implements each task itself, in the order the supervisor issues them,
and notes the degradation in the final summary so the user sees the loop ran
without implementer dispatch. The missing capability is the subagent, not
parallelism — the supervisor's path is sequential too. The supervisor treats the
attempt the same either way.

## Why a separate mode, and its boundary

Full mode is the one mode the supervisor drives; light mode and direct-light never
start it. The boundary is the risk trigger block in `SKILL.md`, not a choice the
user makes, so branching inside `work-loop` keeps contributors from picking the
wrong skill and keeps the overlap with the single-agent flow single-sourced.

An `implementer` is a leaf: it builds one task and reports. Reviewing, dispatch
decisions, plan edits, and every human's answer belong to the controller, and
procedure state belongs to the supervisor, so the tree stays two levels deep.
Implementer results are untrusted, and the supervisor, not the implementer,
decides what an attempt changed. Gates of record run in the primary tree; an
implementer's own gate results are advisory. An implementer that reports `blocked`
or `failed` sends the controller back to the plan, and the same task is not
redispatched on the same assumption.
