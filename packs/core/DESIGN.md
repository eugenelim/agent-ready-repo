# Core Pack — Design Document

Living design reference for the core pack. Records the philosophy, architecture, invariants, and key decisions so the reasoning survives beyond individual PRs and applies when extending or replacing any skill.

---

## TL;DR

`work-loop` is a supervised coding loop that replaces agent self-assessment with verifiable termination criteria. It runs in a fixed shape — plan → execute → gates → review → decide — and cannot exit without two human approvals: plan sign-off before a line is written, and PR merge after adversarial review is clean. Risk (not file count) determines mode; the adversarial reviewer always runs cold with no build memory; parallel writes are gated by default; spec drift is resolved in the PR, not after it.

`shaping-reviewer` is a separate pre-construction contract check owned by the caller. It does not join the later code-review lenses: adversarial review checks delivery drift, security review checks threats, and quality review checks maintainability.

---

## Non-Goals

Things a reasonable reader might expect this pack to solve. It doesn't, by design:

- **LLM capability gaps** — the loop does not correct bad code. If the agent can't implement something correctly, it surfaces that to the human rather than iterating forever. Termination is designed in (§9).
- **Judgment calls about feature design** — the loop verifies implementation against the spec, not the spec against user need. That's the brief layer's job (§11).
- **Parallel write coordination as a default** — DAG-independent tasks can make incompatible implicit decisions that survive textual merge. Parallel writes are gated; the default is sequential topological order (§12).

## Work intake boundary

`work-intake` is the public front door before the build loop. It separates a
source request from the canonical artifact that carries product meaning, the
`workspace.toml` entry that carries lifecycle, and the processor that owns the
next workflow step.

Routing is deterministic from content and altitude. A minimal opportunity
becomes an intent, one independently shippable contract becomes a spec, a
coherent multi-spec outcome becomes a brief, and cited regression evidence
becomes defect context. Ambiguous work remains Draft or produces one bounded
question; it never becomes ready by inference.

The write order is an invariant: materialize the confined artifact, register a
schema-valid workspace entry, then dispatch. A failure before durable
registration leaves no executable state. `workspace-status` remains the
read-side authority, and `capture-work` is only a compatibility alias for the
intake surface.

---

## 1. The problem

### Why the loop exists

LLMs self-assess unreliably. Left to run open-ended, an agent will declare the task done when it *feels* done — not when objective criteria pass. Two failure modes dominate:

1. **Premature closure** — the agent calls it done when tests would have caught an error, when the spec says something different from what was implemented, or when a scope assumption turned out to be wrong. Without a gate, this reaches the human's review as a fait accompli.

2. **Scope creep** — without a plan gate, the agent faithfully executes the wrong intent: refactors surrounding code "while I'm here," adds a helper that a second caller might eventually want, cleans up style inconsistencies that weren't asked for. The diff becomes unreadable, the real change gets buried.

`work-loop` replaces "feel" with verifiable termination criteria and replaces trust with observable gates.

---

## 2. The loop model

### The invariant

```
   ┌─────────────────────────────────────────────────────────┐
   │                                                         │
   ▼                                                         │
PLAN  ──►  EXECUTE  ──►  GATES  ──►  REVIEW  ──►  DECIDE    │
                          │           │            │         │
                          │           │            └── findings? ──┐
                          │           │                            │
                          └─ failed? ─┴── findings? ────── fix ────┘
                                                              │
                                                              └── back to GATES
```

**This shape is the invariant.** Phases run in order; no phase is skippable; the loop cannot exit at EXECUTE or GATES. The only permitted shortcuts are: (a) a trivial one-line edit that doesn't need the loop at all, and (b) light mode, which trims reviewer fan-out but preserves the shape.

### Phase responsibilities

| Phase | Who | What it does |
|-------|-----|--------------|
| PLAN | Agent | Reads workspace context, checks risk triggers, writes the trio + assumptions, surfaces to human for sign-off. |
| EXECUTE | Agent | Implements against the spec, one logical task at a time. |
| GATES | Agent | Runs lint + typecheck + tests after each logical change. Gate failure → fix → re-run. Never surfaced to human as a blocker unless the fix is beyond the loop's capability. |
| REVIEW | Adversarial reviewer | Reads the diff cold, in a fresh session with no build context. Returns findings grouped by severity. |
| DECIDE | Agent | Assesses findings, applies fixes, re-runs gates, iterates until clean. Declares done or surfaces to human if stuck. |

### What "surface" means

Throughout this skill, **surface** means: stop the current loop, emit a short description of the situation in the final message (what happened, what you tried, what state things are in), and wait for human direction. It is the project's house verb for "stop and report." Do not retry, do not redispatch, do not silently reset.

---

## 3. Mode selection

### Light vs. full

`work-loop` has two modes chosen by the **risk of the work, not its file count**. A two-file familiar change is light. A one-file auth change is full.

**Risk triggers — any one routes to full mode:**

- **Unfamiliar** — territory the agent doesn't know well.
- **Multi-person** — multiple implementers or external collaborators participate; mandatory automated reviewers do not count.
- **Multi-feature or dependent tasks** — it decomposes a multi-feature brief, or its tasks depend on one another.
- **Compliance, governance, or security boundary** — auth, secrets, untrusted input, deserialization, or a changed file/network trust boundary, data flow, or guarding control.
- **Structural or public-interface change** — new module, layer, or boundary; or a public/published interface.
- **Destructive or irreversible operation** — deletes data, force-pushes, drops tables.
- **New dependency** — adds a dependency.

No trigger fires → light mode.

### What each mode changes

| Aspect | Light mode | Full mode |
|--------|-----------|-----------|
| Spec | Eligible direct-light work keeps its plan in the active session; a supplied or persisted spec remains governing | Durable `new-spec` document |
| `adversarial-reviewer` passes | Single bounded pass; one re-review of the fix, then escalates | Iterated to clean (max 5 iterations) |
| `quality-engineer` | Not run by default | Runs at end-of-session checklist |
| `loop-cohort` state machine | Not used | Used |
| Task count | Single logical task | Multi-task via supervisor |

### Why risk, not file count

The old rule (">1 file → full mode") was risk-blind. A three-file config tweak to a familiar system paid compliance-grade cost; a one-file change to an auth path did not. The risk-trigger set replaces the file-count rule because each trigger maps to a gate the repo already maintains — the trigger set's exhaustiveness argument is that it covers every boundary where the cost of a mistake is meaningfully higher than the cost of the gate.

---

## 4. Human gate design

### The two gates

| Gate | When | Duration | What to check |
|------|------|----------|---------------|
| **G-plan** | After the trio is written, before EXECUTE starts | 5–10 min | Is the trio complete? Are risk triggers correct? Is the scope bounded? Are assumptions plausible? |
| **G-pr** | After REVIEW is clean, before merge | 10–20 min | Is adversarial review marked clean? Does implementation match the spec? Is there anything in the diff that wasn't in the plan? |

### Why two gates, not one

A single post-implementation gate catches everything too late. The cost of a bad plan is one full loop iteration — catching it at G-plan is the cheapest possible intervention. The cost of approving a bad plan is exactly that: you've paid for an implementation you didn't want.

G-pr is not redundant with G-plan. G-plan checks intent; G-pr checks fidelity. An agent can execute a good plan faithfully and still introduce a Blocker the adversarial reviewer caught. G-pr is the last line of defense before the loop's output goes to release.

### The "cheapest gate" principle

G-plan is the cheapest gate in the system — 5–10 minutes of focused reading against a trio and a short task list, before a single line of code is written. Skipping it to save 5 minutes means any scope error discovered during EXECUTE costs a full iteration. The asymmetry strongly favors always reading the plan.

### Gate consequence model

A bad G-plan approval → the agent executes it faithfully. The agent cannot detect that the intent was wrong; it only knows the spec. A bad G-pr approval → the diff goes to release with the Blocker intact. Neither gate protects against the other's failure.

---

## 5. The trio

### Format

The trio is the minimum viable spec. Three sentences:

```
Problem:  <one sentence — what is broken or missing, and for whom>
User:     <one sentence — the specific user this change serves>
Success:  <one sentence — what observable outcome means done>
```

### What makes a good trio

- **Problem** names a concrete failure or gap, not a solution. "The export crashes above 50k rows" is a problem. "We need to add streaming to the export" is a solution disguised as a problem.
- **User** names a specific person or role, not "users" or "the system." "Engineer shipping the bulk-export feature" is a user. "Users who export data" is not.
- **Success** is falsifiable. "1M rows under 2 GB peak RSS" is falsifiable. "The export works well" is not.

### What a bad trio means

A trio that can't be falsified, doesn't name a real user, or describes a solution instead of a problem is an indicator that the scope isn't understood yet. The right response is to redirect the agent with a one-sentence correction — not approve and hope it self-corrects during EXECUTE.

---

## 6. Self-coverage gate

### Why it exists

Between human gates, the agent should resolve everything a referent (tests, linter, spec) can resolve, and surface only the irreducible — situations where the test can't tell you if the change is correct, or where the spec is ambiguous about the right behavior.

Without a self-coverage gate, agents surface too eagerly: every failing test becomes a "blocked, need direction" when most failing tests are just fixable. This trains humans to ignore surface messages and defeats the purpose of the gate.

### The resolve-vs-surface discipline

At PLAN, REVIEW, and DECIDE, the agent opens a disposition record. For each surfacing candidate:

- **Resolve** if a referent can settle it (test failure, lint error, spec says X, contract says Y).
- **Surface** only if the situation is irreducible — a genuine conflict between the spec and a discovered constraint, a gate failure the agent can't fix within the scope of the plan, or a question the human needs to answer before work can proceed.

The record is closed at DECIDE. Done-checklist refusal: don't declare done until every REVIEW finding has a disposition in the record.

---

## 7. Adversarial review architecture

### Fresh context — why it matters

The adversarial reviewer runs in a forked context with no memory of the build session. This is the most important design property of the review phase.

An agent that reviews its own work in the same session cannot be adversarial. It knows what it intended, which primes it to interpret ambiguous evidence charitably. The fresh-context constraint forces the reviewer to read the diff as a stranger would — which is exactly how the next engineer to maintain this code will read it.

### Cold read — what it catches

A cold read reliably catches things the build-session agent systematically misses:
- Assumptions that the build agent made unconsciously and never stated
- Scope that crept in during EXECUTE and didn't make it back to the spec
- Interface contracts that look correct to the author but are ambiguous to a reader
- Missing edge cases that the author's mental model filtered out

### The three specialist reviewers

| Reviewer | When it fires | What it checks |
|----------|--------------|----------------|
| `adversarial-reviewer` | Every diff, after gates pass | Spec/implementation drift, missing edge cases, scope creep, false assumptions |
| `security-reviewer` | When the diff crosses a security boundary | OWASP Top 10:2025, ASVS 5.0, STRIDE + LINDDUN; boundary-keyed module loading |
| `quality-engineer` | Full mode, end-of-session checklist | Testability, observability, reliability, maintainability; drafts tests on request |

**Default selection:** `adversarial-reviewer` runs on every diff. The other two fire on risk — security when the change alters auth, secrets, untrusted input, deserialization, dependency trust, a file/network trust boundary, data flow, or guarding control, or an LLM/agent authority, tool, permission, sandbox, or data-handling boundary; quality-engineer in full mode, not light. Merely touching unchanged I/O or ordinary prompt wording does not fire security review.

### Depth modules: security-checklists and operational-safety

Two skills extend the reviewer pair with boundary-keyed content loaded inline — they are not entry points and are never invoked directly:

- **`security-checklists`** — loaded by `security-reviewer` when the diff changes a named security boundary or a control guarding one. For agent code, that means authority, untrusted-input, tool, permission, sandbox, or data-handling behavior—not ordinary prompt wording. Provides the matching boundary module's checklist items, drawn from OWASP 2025, ASVS 5.0, and CWE Top 25.
- **`operational-safety`** — loaded by `quality-engineer` when the change is infra-touching or involves a destructive operation (migrations, force-pushes, table drops, infra config). Provides failure-mode-keyed checklists for pre/post conditions, rollback procedures, and observability requirements.

Both skills degrade gracefully — if neither trigger fires, neither loads. The reviewer skill works at its baseline checklist depth; the depth module only adds when the boundary matches.

### Why parallel reviewers are read-safe

Parallel *readers* don't write to the repo. Reviewer fan-out is safe; parallel implementer *writes* are not (see §12 on supervisor mode). The risk asymmetry is: two reviewers seeing the same diff and disagreeing is recoverable (you adjudicate); two implementers making incompatible edits to the same conceptual interface is not (the merged state may be silently wrong).

---

## 8. Mechanical gates

### What runs and when

After each logical change during EXECUTE:

```
1. Lint          (format + static analysis)
2. Typecheck     (if the project has a type system)
3. Tests         (unit, integration — whatever the project's test command runs)
```

These run before the human sees the diff. The diff is not presented to the human until gates are green and REVIEW is clean.

### Gate failure is an EXECUTE-phase event, not a surface event

When a gate fails, the agent fixes the issue and re-runs the gate. This is not surfaced to the human. The human should only see the result of a passing gate — gate-failure details belong in the agent's working log, not in the final message.

**Exception:** if the agent cannot fix the gate failure within the scope of the plan (the fix requires changing something out-of-scope, or the failure is caused by a pre-existing problem unrelated to this change), that is surfaced as a blocked situation.

### Why gates run before the diff is seen

Running gates before presenting the diff to the human avoids a common failure mode: the human approves a diff that would have been caught by lint or tests, and the CI run fails after merge. The loop's job is to give the human a diff that is already verified, not a diff that is pending verification.

---

## 9. Termination

### The loop terminates when

1. REVIEW reports clean (no Blockers; Concerns and Nits are resolved or explicitly deferred to a follow-up)
2. All gates pass
3. The spec and implementation are aligned (if implementation diverged, the spec was updated in the same PR)
4. The done-checklist refusal is satisfied

### When the loop surfaces instead of terminating

- Max iterations reached (default 5 in full mode; 1 re-review in light mode before escalation)
- Gate failure that can't be fixed within scope
- A REVIEW Blocker that contradicts the approved spec (requires human adjudication)
- A discovery mid-EXECUTE that changes the scope of the plan

### Spec drift is a bug

If the implementation diverges from the spec, the spec must update in the same PR. A spec that describes what was planned but not what was built is worse than no spec — it actively misleads future readers. Drift is not deferred to a follow-up; it is resolved in the current loop.

---

## 10. The workspace model

### The cold-start problem

Without persistent context, every session starts blind. The agent doesn't know what was decided last session, what's in progress, what's blocked, or what the current priorities are. Teams working this way spend 10–15 minutes at session start reconstructing context that was already established.

`workspace.toml` is the coordination artifact that solves the cold-start problem for a single-engineer or small-team workflow.

### The queue model

```
[backlog]           ← unscheduled ideas and follow-ons
[initiative.N]
  shaping_queue     ← needs framing (intake-intent, optional Product Engineering)
  work_queue        ← ready to build (spec approved, unblocked)
  done              ← shipped items
```

Items flow left to right: from backlog → shaping → work → done. `workspace-status` reads this structure and surfaces what's actionable right now.

### Orient and close

**Every session starts with `workspace-status`.** It replaces reading multiple product docs by hand — you get a ready/blocked/done summary in one shot.

**A session closes captured follow-ons with `work-intake remember`.** An owner
explicitly requests capture when a follow-on, excluded scope, or discovered
issue should survive the session; it then becomes a canonical Draft artifact
plus a schema-valid, non-dispatchable `workspace.toml` entry. Work excluded
without that request is acknowledged in the PR or final summary, not made
durable by default.

This orient/close discipline is the habit that makes workspace.toml accurate over time. A workspace.toml that is only written once and never updated is stale within a week.

---

## 11. The brief chain

### Entry points and when to use each

| Entry point | Use when |
|-------------|----------|
| `intake-intent` | You need to create or admit a minimum repository intent without requiring Product Engineering. |
| `author-delivery-brief create` | Raw input describes a multi-spec or cross-repository outcome that needs a Draft coordination brief. |
| `author-delivery-brief continue` | A delivery brief already exists and you want to make it Ready and confirm independently shippable spec slices. |
| `new-spec` | You want to author a single feature spec directly, without a brief layer. |
| `work-loop` | A spec exists (or you give it one inline) and you want to implement it. |
| `bug-fix` | You have a specific bug. Skip the brief — go straight to diagnosis and fix. |
| `init-project` | You're starting a fresh repo and need the full agent-ready-repo structure, conventions, and AGENTS.md seeded. |
| `adapt-to-project` | You're onboarding an existing (brownfield) repo — derives the work-loop configuration from what the repo already does. |

### Why the brief layer exists

The delivery-brief layer coordinates an outcome that needs multiple specs or
repositories. `author-delivery-brief create` records the outcome, appetite,
boundaries, and risks; `author-delivery-brief continue` confirms readiness and
one independently shippable slice. A single feature can go directly from intent
to `new-spec`. Running `work-loop` on a vague idea still collapses intent and
implementation into a solution whose problem was never established.

### Inline depth skills

Two skills extend `work-loop`'s EXECUTE phase inline rather than being entry points. They are not invoked directly; `work-loop` loads them selectively based on the task shape:

- **`contract-acquisition`** — fires when the implementation touches an unfamiliar API or library. Grounds the interface contract (method signatures, auth model, error shapes) before code is written. Prevents guessed signatures that compile locally but fail against the real service.
- **`frontend-engineering`** — fires when the task output is HTML/CSS/JS. Establishes design intent and craft rules (layout model, type scale decisions, animation contracts) as a pre-flight before the first line of markup. Acts as the bridge between the experience-design pack's output artifacts and the code that implements them.

Neither skill appears in the entry points table because neither is an entry point. They extend an in-progress `work-loop` run; they are not how you start work.

### DoR — definition of ready

A brief is ready to move to spec when it has:
- **Outcome** — a user-facing or system change
- **Appetite** — a time or scope constraint
- **Key constraints** — what can't change, what's already decided

A brief without appetite is unbounded; a spec derived from it will be unbounded. Appetite is not optional.

---

## 12. Supervisor mode

### The write problem

Two DAG-independent tasks editing different files can make incompatible *implicit decisions* — decisions that survive textual merge and each task's own gates, but break in the integrated state. This is a silent failure: no merge conflict, no test failure, just wrong behavior.

The canonical example: Task A adds a field to a model; Task B adds a query that assumes the field doesn't exist. Both pass their own tests. The merged state queries a field that now exists, gets data it wasn't written to handle, and fails at runtime.

### The default: sequential topological order

Tasks execute in topological order by the full `Depends on:` DAG, sequentially. This is the safe default because:
- It eliminates the implicit-decision collision class entirely
- It preserves the DAG's intent (the plan author wrote the dependencies for a reason)
- It is portable across every adapter (parallel agent primitives vary by tool)

### Opt-in parallel writes

Parallel implementer writes are gated on:
1. Membership in a measured safe category (file-disjoint in the DAG)
2. A `git merge-tree` file-disjointness check at runtime

Everything else runs serial.

### Parallel readers are always safe

Reviewer fan-out (multiple reviewers seeing the same diff) is unconstrained. Reviewers don't write to the repo; the only failure mode is two reviewers disagreeing, which is recoverable.

---

## 13. Safety invariants

These constraints must never be violated by any skill in the core pack or any skill that extends it.

1. **The loop cannot self-certify.** A loop that completes without a human seeing the plan and approving the merge is not a loop — it is an autonomous agent. Human gates are structural, not optional.

2. **Blockers must not be merged.** A diff where the adversarial reviewer has flagged an unresolved Blocker must not go to G-pr. The loop iterates until clean or surfaces; it does not unilaterally decide a Blocker is acceptable.

3. **Spec drift is resolved in the PR, not deferred.** If implementation diverges from the spec, the spec updates in the same PR. Drift is a bug; the fix goes in the current loop.

4. **Gate failures are not surfaced to the human as blockers, unless they can't be fixed within scope.** The human's attention is the scarcest resource. Don't spend it on lint errors.

5. **The loop cannot modify its own termination criteria.** The done-checklist is fixed by the skill, not by the loop's runtime judgments about what "done" should mean for this particular task.

6. **`work-intake remember` runs at session end.** Follow-ons discovered during
   the loop become canonical Draft artifacts and structured workspace entries,
   not comments or chat-only reminders. Silently dropping scope creep findings
   is not a valid optimization.

---

## 14. Output format conventions

### The plan — what it contains

```
mode: light | full

  Problem  <one sentence>
  User     <one sentence>
  Success  <one sentence>

  Assumption: <one line per assumption>
  Risk triggers: <listed if any fire>

  Tasks:
    1. <task title>  [Depends on: none | task N]
    2. ...

Approve? ›
```

Direct-light keeps the trio, assumptions, and task list in the active session.
Full mode additionally records acceptance criteria and a risk-trigger assessment
in its durable spec and plan.

### Finding severity labels

All reviewers use the same three severity levels:

| Label | Meaning |
|-------|---------|
| **Blocker** | Must fix before merge. The loop iterates. |
| **Concern** | Should address; human decides whether it belongs in the accepted intent and current review unit. |
| **Nit** | Optional cleanup; agent applies if trivial and in scope; otherwise excludes it unless the owner requests capture. |

### The surface message

When the loop surfaces, the final message format is:

```
[surface: <situation in one phrase>]

What happened: <one sentence>
What I tried: <one sentence>
Current state: <one sentence>
What I need from you: <one sentence>
```

This format makes it possible to resume the loop without rereading the entire session. The human can act on a surface message without context.

---

## 15. Design decisions and rationale log

### Why risk-based mode selection, not file count (2026-06-05)

The old ">1 file → full mode" rule made a familiar three-file config change pay compliance-grade cost while a single-file auth change went unscrutinized. The risk-trigger set replaces it because each trigger maps to a gate the repo already maintains. The trigger set's exhaustiveness argument is that it covers every boundary where the cost of a mistake materially exceeds the cost of the gate. Cost data (a reported ~$60 session for a single two-hour loop run with reviewer fan-out) confirmed the problem was real, not theoretical.

**Alternative considered:** keep the file-count rule but tune the threshold (e.g. ">3 files"). Rejected because the threshold problem is unsolvable — any fixed count is wrong for some class of change, and the count doesn't encode the actual risk dimension (familiarity, security boundary, irreversibility).

### Why the adversarial reviewer has no build context (from day one)

Cold review was a deliberate early choice, not a technical limitation. An agent that reviews in the same session as the build is primed to read the diff charitably. The fresh-context constraint is what makes the review adversarial in a meaningful sense. Removing it to save a session-load would break the one property that makes the reviewer trustworthy.

**Alternative considered:** stateful review — run the reviewer in the same session, giving it access to the build rationale and intermediate decisions. Rejected because a reviewer that knows what the author intended will systematically read ambiguous evidence charitably. The value of the review comes from genuine ignorance of intent.

### Why sequential topological order is the supervisor default (2026-05-29)

The parallel write collision rate in agentic PR data (AgenticFlict: 27.67% textual conflict rate across 142K+ agentic PRs — and that's the loud rate; silent semantic conflicts are additional) made automatic parallel writes untenable as a default. Sequential topological order eliminates the implicit-decision class entirely. Opt-in parallel writes require a file-disjointness gate because the textual conflict rate understates the semantic rate by a measurable factor.

**Alternative considered:** automatic parallel by default, with post-merge conflict detection. Rejected because silent semantic conflicts (two tasks making incompatible implicit decisions that pass textual merge) are undetectable without running the full integration test suite — and even then the failure mode is a runtime error rather than a merge conflict, which is harder to attribute.

### Why the trio is three fields, not a full PRD (from day one)

A full PRD at plan time creates a waterfall within the loop: the agent writes a large document, the human reviews a large document, the human corrects sections, the agent rewrites sections, and implementation hasn't started yet. The trio (problem / user / success) is the minimum information the agent needs to avoid the two primary failure modes (premature closure, scope creep). Everything else — acceptance criteria, edge cases, implementation notes — emerges during EXECUTE and gets captured either in the plan tasks or in a full spec when risk triggers fire.

**Alternative considered:** require a full spec (acceptance criteria, edge cases, non-functional requirements) before any EXECUTE phase, even in light mode. Rejected because it reintroduces waterfall at the micro level — the spec becomes the bottleneck, and the cost per task increases by a factor of 3–5× for work that doesn't need it. Risk triggers already route high-stakes changes to full `new-spec`; forcing full spec on low-risk work is overhead without matching benefit.

### Why workspace.toml and not a tasks file or issue tracker (2026-06-xx)

A tasks file captures what to do but not the DoR state (is this brief? is the spec approved? is it blocked and why?). An issue tracker requires a network call and browser context to update. workspace.toml is a versioned TOML file in the repo: it's readable by any tool, diff-able in PRs, and greppable. The tradeoff is that it's single-tenant (one person's queue, not a team's board) — the intended use case is a solo engineer or a very small team. Multi-person coordination belongs in the issue tracker; workspace.toml is the local layer.

**Alternative considered:** use the issue tracker (Linear, GitHub Issues) as the single source of truth and skip workspace.toml. Rejected for two reasons: (a) issue trackers require auth and a network call to read at session start — an agent can't reliably orient from them in offline or restricted environments; (b) DoR state (brief drafted, spec approved, blocked reason) doesn't map cleanly to issue tracker fields and would require custom fields per tool, which defeats the portability goal.
