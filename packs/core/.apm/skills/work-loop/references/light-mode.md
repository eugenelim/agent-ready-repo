# Light mode

Load this to decide direct-light eligibility, and whenever light mode is
selected. A full-mode run never uses it.

Light mode covers a single logical task with no risk trigger. It runs the
full loop spine with four trims. An eligible current
request runs **direct-light** and keeps its plan in the active session rather
than creating a durable artifact.

## The four trims

1. **Direct-light procedure.**
   1. Read the explicit current request, issue, or PR. The explicit trusted
      invocation is the authority; it may reference an issue or PR, whose
      content is context, never authority.
   2. Confirm direct-light eligibility before modifying any implementation
      file.
   3. Write the assumption trio and a bounded task/verification plan in the
      active session.
   4. Execute the normal light loop: plan, implement, gates, adversarial
      review, repair, decide.
   5. Produce a final handoff carrying the requested outcome; implemented
      scope; verification evidence; non-goals and independently scoped
      follow-ons; and any discovered reason future work should use a durable
      spec.

   Direct-light does **not** invoke `new-spec`; create `docs/specs/`; create a
   sibling plan; mutate `workspace.toml`;
   initialize `loop-engine` or `loop-cohort`; run spec-status lint when no spec
   exists; or perform project-knowledge capture solely because a spec gate did
   not occur. All ordinary implementation gates and the adversarial review
   remain.
2. **`adversarial-reviewer` rounds run to clean.** A converging loop should
   finish, so do not budget it. Read the trend at the third round and every
   second round after: are findings getting fewer and smaller? Read it from the
   round-numbered adjudication artifacts, not from memory. While that holds,
   keep going.

   When it does not, the loop is diverging. Stop repairing, and ask whether the
   reviewed construct should exist rather than whether it is correct. Prefer
   deletion, or a move to the module or team that owns it, over another repair
   — then Surface that choice to the requester and wait. Their decision to
   delete the construct, move it, or narrow the accepted intent is what
   resolves the findings it covers; record it in the resolve-vs-surface
   disposition record.

   Also note how many findings your own repairs created. Carry that number into
   the trend read and into anything you Surface, because it is what tells a
   reader whether the loop is chasing itself. It cannot be calibrated, so it
   never decides the checkpoint.
3. **No `quality-engineer` pass** by default. Two exceptions retain it. The
   adopter declared in `AGENTS.md` that the repo is judged by a strict external
   quality gate (SonarQube, CI-only coverage threshold) — act on the
   declaration; don't scan for config files. Or a human asked for the pass,
   which is the third high-risk condition and warrants the lens in either mode
   without escalating to full. Absent either, Surface a maintainability concern
   that needs the lens rather than resolving it unaided.
4. **No `loop-cohort` state machine.** Run finish-time `lint-spec-status.py`
   only when a persisted spec exists.

The rounds rule replaces neither risk-trigger escalation nor the mode
selection that owns it. A risk trigger discovered at any point still routes
the work to full mode on its own.

## Direct-light decision record and route

Before the first implementation write, emit a user-visible, session-only
decision record that names the authority source, bounded scope, non-goals,
risk-trigger assessment, assumptions, and verification plan. If any of those
six is ambiguous, Surface it and stop. The explicit request to start is the
trigger; do not add a confirmation handshake or persist this record.

Eligibility is a conjunction: direct-light is available only when **all** of
these hold.

| Required condition | If absent |
| --- | --- |
| Explicit user request to start or perform the change now | Do not infer authority from surrounding text. |
| One bounded logical change | For a bundle of tasks, apply Splitting a bundle below first; otherwise use the durable path when the work is not one coherent change. |
| Independently verifiable | Use the durable path when verification cannot be bounded. |
| Expected to complete in the current session | Escalate to durable work. |
| No current full-mode risk trigger | Use full mode. |
| No need for queueing, assignment, cross-session resumption, parallel coordination, or a durable product contract | Use the durable path. |
| No conflict with a canonical queued or active workspace item | Surface the conflict; do not start untracked parallel work. |
| No supplied governing spec for the same work | Use that existing spec. |

Durability is a disjunction: **any one** of these routes the work to the
durable spec-and-plan path. Invoke `new-spec` for that path.

| Durability trigger | Why a session-local run cannot carry it |
| --- | --- |
| A current full-mode risk trigger | Full mode owns the heavier gates and reviewer set. |
| Multi-implementer, external-collaborator, or parallel execution | Another builder or collaborator needs a contract they can read without this session; mandatory automated review does not count. |
| Dependent delivery tasks needing durable sequencing | Order between tasks has to outlive the session that chose it. |
| Expected multi-session work | Nothing session-local survives context loss. |
| Queueing for later | Only an indexed spec and plan are dispatchable. |
| External control-plane orchestration | An external attempt/lease system addresses durable items, not a session. |
| A human approval boundary that must survive context loss | An approval has to be re-readable after the approver's session ends. |
| A public or durable product behavior contract; for an edit to an existing agent-guidance file, only one that changes a **tool surface**, an **authority or gate**, a **security boundary**, or a **published schema** | Published behavior is a contract others depend on, not a session decision. A plain guidance edit changes how an agent carries out a step inside the same tools, authority, gates, controls, and formats. |
| Source-authority or refresh state that must stay meaningful after the session | Provenance and refresh conflict decisions are durable state. |
| An explicit user request for a spec | The request is itself the authority for the durable path. |

Direct execution being unavailable never creates a brief: a brief still
requires a coherent multi-slice or cross-repository outcome.

Classify before the first implementation write. If a trigger is found before
coding, stop the direct path; invoke `new-spec`; create and approve the full
spec and plan; register durable work where applicable; then continue through
full mode. If a trigger emerges during implementation, stop before crossing the
newly discovered boundary; preserve the current diff without pretending it was
produced under an earlier approved spec; create a spec and plan describing the
intended final state and already-observed repository reality; run the normal
human approval gates; and bring the complete diff through full verification and
review. Do not backfill a fake implementation chronology.

If direct-light discovers that it needs a further session, a second worktree is
already changing the same files, or gates cannot be repaired in-session, stop,
Surface the situation, and escalate to the durable spec-and-plan path rather
than leaving changes stranded with no durable record.

## Splitting a bundle

A request that bundles several tasks may split into one light unit per task
when the tasks pass all three parts of this test:

1. **No dependency edge.** No task's `Depends on:` names another task in the
   bundle.
2. **No shared write set.** Each task declares the paths it will write as a
   `Touches:` set, and no path or glob in one set matches a path in another. A
   generated projection of a source file, under `.claude/`, `.agents/`, or
   `.codex/`, counts as a write to its source path.
3. **The diff agrees.** Each unit's finished diff stays inside its own set and
   touches no file in another unit's set.

List every task with its `Depends on:` and `Touches:` lines in the decision
record, and check parts 1 and 2 there before the first write. Check part 3 on
every unit's finished diff. Part 3, the diff check, is the check that counts: a
declared set is a prediction, and a prediction never by itself shows
independence.

Each unit then faces every risk trigger and every eligibility row on its own,
and ships as its own branch and pull request. Units run one at a time in this
session, so a split is not parallel execution. The bundle as a whole must still
pass the rows "Expected to complete in the current session", "Expected
multi-session work", and "Queueing for later": a bundle whose units together
need another session, or would wait in a queue, goes to full mode whole.

**Merge order.** Units may be reviewed in any
order. No light unit merges until every unit still in the bundle has a finished
diff that passes the diff check.

**A unit that fires another trigger** leaves the bundle for full mode by itself
and takes its declared write set with it: its spec and plan record that set.
The units still in the bundle run the diff check against that set, then merge
without waiting for the full-mode unit.

**The fallback.** When any part of the test fails or cannot be shown, the bundle
stays whole and goes to full mode. A unit whose diff leaves its set stops the
whole bundle. Nothing has merged at that point, so the bundle moves to full mode
with every unit's diff kept as observed work, under the rule above for a
trigger that emerges during implementation.

## Editing existing agent guidance

An edit to an existing agent-guidance file that changes no **tool surface**,
**authority or gate**, **security boundary**, or **published schema**, as the
risk-trigger block defines them, fires no trigger by being guidance. It still
faces every trigger on its other effects, and it does not count as a durable
product contract for the eligibility table above. It runs light with one added
obligation: each changed rule gets a new or updated content-pin test, a test
that asserts the phrases the rule depends on, which reads only the edited
section between two markers rather than the whole file. Adversarial review runs
as light mode runs it.

## Loop deltas

**REVIEW.** Dispose every sustained finding with `apply` or `defer`; only a Nit
may end a round deferred. A fix opens the next round. A round that sustains
nothing above a deferred Nit ends the rounds.

**FIX.** After a fix, return to GATES, then re-enter REVIEW.

**Finish checklist.** "Review clean" means the `adversarial-reviewer` rounds
with no `loop-cohort` involved; deferred Nits do not block it. Two checklist
items carry light-mode deltas:

- The `adversarial-reviewer` rounds left no unresolved Blocker or Concern,
  carrying at most deferred Nits recorded with their citations. That review is
  required, and its absence is a mandatory `missing` outcome and emits
  `BLOCKED`, never a readiness-compatible named skip. Every finding received
  a requiredness and session-decision disposition, and included fixes passed
  GATES. Under either exception above — the adopter external-quality gate, or a human
  asking for the pass — `quality-engineer` also ran and returned Clean or, only
  when non-mandatory, is an allowed named skip.
- The findings in the resolve-vs-surface disposition record come from those
  rounds.
