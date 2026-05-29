# RFC-0015: Wave-scheduled supervisor mode for work-loop

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn -->
- **Author:** eugenelim
- **Approver:** @eugenelim (signed off 2026-05-29)
- **Date opened:** 2026-05-28
- **Date closed:** 2026-05-29
- **Related:** `work-loop` skill (§EXECUTE, `references/supervisor-mode.md`); `docs/CONVENTIONS.md` §Supervisor mode + §Multi-agent shape by profile; `new-spec` plan template (`assets/plan.md`); RFC-0014 (the answer-first format this RFC follows).

## The ask

- **Recommendation (BLUF):** Make **sequential topological ordering the
  default** for supervisor mode — schedule tasks by the `Depends on:` DAG
  every plan already declares. **Stop auto-firing parallel implementer
  fan-out**; keep the fan-out machinery only as **opt-in, gated on a
  measured safe-category + file-disjointness check**. Reviewer (read)
  fan-out is unchanged and already safe.
- **Why now (SCQA):**
  - *Situation* — supervisor mode auto-branches to parallel implementers
    whenever ≥2 tasks declare `Depends on: none`, and discards the rest of
    the dependency graph.
  - *Complication* — three failures: (1) it never checks authored order
    against declared deps, and real plans already ship forward-reference
    bugs; (2) the auto-parallel default ships **silent** semantic breaks —
    parallel writes that pass each task's own gates but break when
    integrated; (3) measured here, **only ~⅓ of declared-independent waves
    are actually file-disjoint**, so "independent in the DAG" is a weak
    safety signal.
  - *Question* — how do we use the DAG to schedule safely, on every
    adapter, without shipping silent parallel-write breakage?
- **Decisions requested:**
  1. **Sequential topological default** — compute the full DAG, detect
     cycles/forward-refs, execute in topological order, single-agent, on
     every adapter. *Recommended: yes* (the proven, zero-hazard, portable
     win). *Decide-by: this review; default if no objection: adopt.*
  2. **Flip the auto-parallel default off** — parallel implementer fan-out
     becomes opt-in, never automatic. *Recommended: yes* (today's default
     is unsafe; decision 3's gate is what makes parallel writes safe).
     *Decide-by: this review.*
  3. **Gate parallel writes on a measured safe-category list + a
     file-disjointness check** (`git merge-tree`); serialize everything
     else. *Recommended: yes.* *Decide-by: this review.*
  4. **`Depends on:` grammar** — ship a robust parser plus a cross-spec
     marker (`spec:<name>/TN`), not a strict grammar. *Recommended: yes.*
     *Decide-by: this review.*

## Problem & goals

**Diagnosis.** Supervisor mode reads only the `Depends on: none` subset and
throws the edges away, with two costs. *No ordering verification:* nothing
checks authored order against declared deps — `agent-spec-cli` T13
(`zipapp build`) declares `Depends on: … T15` (authored later);
`incompatible-hook-event-drop` T2 declares `Depends on: T1, T3, T4` while
T3/T4 are authored after it (its own narrative even contradicts the field).
*An unsafe default:* auto-firing parallel implementer fan-out is
write-parallelism, and its central failure — incompatible *implicit
decisions* between tasks editing different files — survives textual merge
and per-task gates and ships silently (Proposal §2). And the DAG is a poor
proxy for safety: only 33% of the repo's declared-independent waves are
actually file-disjoint (Evidence).

**Goals.** Correct, verified ordering on every adapter; never ship a
*silent* parallel-write break; enable parallelism only where it's
*measured*-safe; reuse existing machinery (`loop-cohort`, worktrees) — no
new subsystem.

**Non-goals** (could-have-been goals, deliberately dropped):
- *Not* a self-writing orchestration engine (the Claude Code
  dynamic-workflows regime) — a plausible goal, dropped: wrong fit, ~15×
  tokens, convergence-by-refutation instead of deterministic gates.
- *Not* optimizing for throughput. We could have aimed for maximum
  parallel speedup; we deliberately don't — the win we pursue is
  *scheduling correctness*, and the speedup ceiling is modest and
  sublinear anyway.
- *Not* standardizing on Claude Code Agent Teams as *the* substrate — a
  tempting single answer, dropped: experimental and not portable across
  adapters.

## Proposal

Generalize supervisor mode **in place** (the trigger is structural, so it
branches inside `work-loop` rather than becoming a new skill).

1. **Default: build the DAG, run it sequentially in topological order.**
   Parse every task's `Depends on:` into a graph, detect cycles and
   forward-references (a forward-ref is a PLAN error — the plan is wrong,
   not the code), order by Kahn supersteps, and **execute sequentially**
   on every adapter. Proven, zero-hazard, ~1× tokens; the win is
   *scheduling correctness*, not speed. This replaces today's auto-parallel
   branch — the `none` set is just the first topological layer.
2. **The write problem (why parallel writes are gated).** The DAG is a
   *sequencing* contract, not a *write-disjointness* one — a leaf task
   discovers new writes mid-execution. So the safe/dangerous split is by
   **which gate catches the conflict** (the detection ladder): **loud** =
   caught by `git merge` or a post-merge compile (textual collisions, and
   build/type conflicts in typed repos) → re-PLAN, no corruption;
   **silent** = survives merge + compile + per-task tests (dynamic-semantic
   interference, shared mutable state, move/extract-vs-edit, migration
   ordering, shared-fixture). Parallel writes are safe only for the *loud*
   classes; the *silent* classes must stay serial.
3. **Dispatch gate for the opt-in parallel path.** Parallelize a wave only
   when (a) its tasks are in a safe category — *cannot-collide* (pure
   per-file codemod / additive / disjoint-no-shared-symbol), *typed Group B*
   (signature/type changes in a statically-typed repo, caught by a
   post-merge typecheck), or *textual-loud* (caught by merge) — **and**
   (b) the wave passes a **measured file-disjointness check** (`git
   merge-tree`), because DAG-independence alone is a weak signal here.
4. **Substrates + isolation.** Parallel *writes* need filesystem isolation
   (a git worktree); native subagent runtimes isolate by context, not
   filesystem. Worktree hazards (`.git/config.lock` races; destructive
   `git worktree prune`) are a *shared-`.git` multi-session-driver*
   phenomenon — standalone, the loop's own worktrees are safe. Inside a
   driver (Conductor, claude-squad), don't stack: delegate isolation to the
   driver. Runtime subagents + parallel exec are GA across Codex, Kiro,
   Copilot, Cursor, Gemini, and Claude Code — parallelism is not
   platform-bound.
5. **`Depends on:` grammar.** A robust parser handles the conventions in
   use (prose, letter-suffixed IDs, ranges); a cross-spec marker
   (`spec:<name>/TN`) disambiguates the one thing a parser cannot (a
   cross-spec `TN` colliding with a local `TN`). Cross-spec deps are
   spec-sequencing, not intra-plan waves.

**Migration.** In-place; `loop-cohort` wraps verbs it already owns
(worktree add/record/merge/cleanup). The plan-template grammar touches one
existing plan (the cross-spec case); the robust parser handles the rest
with no migration.

## Options considered

*Axis: how parallel-write-aggressive the **default** is. The three points
exhaust it — never parallel / opt-in-guarded / always parallel — so it is
MECE, not a round number.*

| Option | Default behavior | Verdict |
|---|---|---|
| **A — do nothing** (keep auto-parallel on `none`) | auto-parallel writes | ❌ ships silent breaks + unverified ordering. *Cost of delay:* forward-ref and semantic breaks keep shipping every multi-task plan. |
| **★ B — sequential default + opt-in guarded parallel writes** | sequential; parallel only past the safe-category + disjointness gate | ✅ **recommended** — kills the silent-break path, keeps the ordering win, reuses existing machinery. Trade-off: a scheduler + dispatch gate to build. |
| **C — always-parallel / self-writing orchestrator** | parallel by default (dynamic-workflows regime) | ❌ ~15× tokens, sublinear speedup, and it *maximizes* the silent-break surface — the opposite of the read/write split's advice. |

*Substrate sub-axis (for B's opt-in path; MECE by who owns isolation):*
(a) loop-managed worktrees — standalone-safe; (b) delegate-to-driver —
portable, the driver owns isolation; (c) host-native subagents —
context-only isolation, insufficient for writes alone. All gated on
file-disjointness regardless of substrate.

*Grammar sub-axis (decision 4; MECE by parser strictness):* leave
prose-only (**do-nothing** — `Depends on:` stays unparseable; *cost of
delay:* no machine scheduling at all, the whole RFC is blocked) / strict
grammar (forces migrating the 13 prose-using plans — needless churn) /
**robust parser + cross-spec marker (recommended)** — handles 19 of the 20
parsed plans with zero migration; the one exception is `self-hosting`
(inside the 20; its `` `distribution-adapters` T7 `` ref collides with its
local `T7`), which the marker disambiguates. (The excluded 21st plan,
`kiro-ide-hook`, is unrelated — it just lacks `### T<n>` headings.)
Grounded in spec-kit's parseable task markers and the repo's own
`Depends on:` census.

Grounded in the read/write split (Anthropic / LangChain / Cognition), the
software-merging conflict taxonomy (Mens; Horwitz–Prins–Reps), and
AgenticFlict's measured conflict rate (Evidence).

## Risks & what would make this wrong

**Pre-mortem — assume it shipped and broke:**
- *A dangerous-category task slipped the gate and a silent semantic break
  shipped.* → mitigation: file-disjointness gate **+** safe-category
  allowlist **+** integrated gates in the primary **+** parallel-off by
  default; the gate must fail closed.
- *The grammar change broke parsing of existing plans.* → mitigation: the
  robust parser handles 19/20 plans' conventions unchanged; only the one
  cross-spec plan needs the marker.
- *Wave scheduling added complexity for no payoff.* → mitigation: the
  sequential default is ~1× tokens and its value is correctness, not speed;
  if the parallel path never proves out, the ordering win still stands.

**Key assumptions (falsifiable):**
- *Declared-independence ≈ file-disjoint.* **Already falsified** — only 33%
  of declared-independent waves are file-disjoint (Evidence). This is *why*
  decision 3 gates on measured disjointness, not the DAG.
- *Typed Group B is safe test-free.* Supported (E-safe-A); falsified if a
  typed repo's post-merge typecheck misses a signature break.
- *Sequential topological order is the high-value, low-risk win.* Supported
  (T0 caught real forward-ref bugs at ~1× cost).
- *The safe categories stay safe at scale.* Partially supported (E-safe-B/C);
  T2-live tests frequency.

**Drawbacks.** A scheduler + dispatch-gate to build and maintain in
`loop-cohort`; a one-plan grammar migration; a modest, *theoretical* speed
ceiling; the opt-in parallel path inherits the worktree hazards above.

## Evidence & prior art

**Spike / de-risk result — six deterministic experiments. The harnesses
reproduce on every run (they're in gitignored scratch today; Follow-on
promotes them to `tools/` with a frozen corpus snapshot, so the numbers
become re-runnable, not trust-me). Corpus = the **20 of 21** `docs/specs/*`
plans that declare `### T<n>` tasks (`kiro-ide-hook` uses a different
heading and is excluded):**
- **T0 (static DAG benchmark over those 20 plans):** supervisor fires today
  11/20; theoretical parallel-speedup ceiling 1.30×→2.21× (equal-cost
  *upper* bound); **2 real forward-reference bugs** found.
- **T1 / T2 (the write problem is real):** a semantic break survives
  textual merge + per-task gates and is caught by the integrated gate
  **only if a test covers it**; same-target collisions fail **loud**
  (merge-abort); shared-state-via-disjoint-files fails **silent**.
- **E-safe-A (typed Group B):** the signature break is caught **test-free**
  by a post-merge typecheck (`mypy`) → Group B is safe-to-attempt in
  statically-typed repos (dynamic Python needed a test).
- **E-safe-B/C (cannot-collide categories):** pure per-file codemod +
  additive are clean; a hidden shared-registration step turns them into an
  append-point → **loud** merge conflict (never silent).
- **Corpus / detection pass (the spec-gating result):** of **55
  declared-independent waves**, only **33% are file-disjoint**, ~**45%
  overlap** on files (a *lower* bound — tasks under-name what they touch);
  ~51% of tasks fall in dangerous categories. → gate dispatch on *measured*
  file-disjointness; the safely-parallelizable wave is a minority.

**Repo precedent.** `CONVENTIONS.md` §Supervisor mode supplies the
constraints this RFC honors (two-levels-deep; sequential merge in task-id
order; conflict⇒PLAN escalation; gates in the primary; no-redispatch; the
dry-run "Known limitation"). The `new-spec` plan template already mandates
`Depends on:`. No prior ADR/RFC covers supervisor parallelism.

**External prior art.** Topological-superstep scheduling is decades-proven
and substrate-agnostic (Make/Bazel, CI `needs:`, Airflow/Temporal/Argo) and
now GA in coding agents (Kiro CLI task-graphs, Copilot `/fleet`). The
parallel-change *conflict* space is taxonomised by the software-merging
literature — the detection ladder ([Mens, *A State-of-the-Art Survey on
Software Merging*, IEEE TSE 28:449–462, 2002](https://ieeexplore.ieee.org/document/1000449/))
and program *interference* (Horwitz, Prins & Reps, *Integrating
Non-Interfering Versions of Programs*, ACM TOPLAS 1989,
[DOI 10.1145/73337.73347](https://dl.acm.org/doi/10.1145/73337.73347)); the
classes that survive merge + compile + per-task tests (dynamic-semantic
interference; "higher-order" build/test conflicts) are exactly the
dangerous ones. The **read/write split** — parallel writers for coding is
the fragile regime — is corroborated independently by Anthropic, LangChain,
and Cognition's 2026 reversal. Empirically, **27.67%** of agentic PRs hit a
*textual* merge conflict across 142K+ PRs
([AgenticFlict, arXiv 2604.03551](https://arxiv.org/abs/2604.03551); it is
the *loud* rate — the silent semantic rate is additional and unmeasured).
Backstop ceiling: static typing catches ~**15%** of all bugs
([Gao, Bird & Barr, *To Type or Not to Type*, ICSE 2017](https://dl.acm.org/doi/10.1109/ICSE.2017.75)).
*Citation status (per RFC-0014's protocol):* AgenticFlict (27.67%/142K),
Mens, Horwitz–Prins–Reps, Gao, and the six experiment numbers are
**fetch- or harness-verified**. A "~32% of injected semantic conflicts
caught by auto-generated tests" figure surfaced in the drafting sweep but
is **dropped pending fetch-confirmation** — the qualitative claim it
supported (test-based detection is partial, not complete) stands on Gao +
the in-house T1/T2 results without it.

## Experiment / validation

**T2-live (post-acceptance; not run — frames the one thing the deterministic
canaries can't settle):**
- *Hypothesis:* live parallel implementers produce silent semantic breaks
  at a per-category rate; for the safe categories that rate is ≈ 0.
- *What we measure:* per-category integrated-gate-fail rate on real plan
  waves run parallel-but-shadow (worktrees, **never merged**) vs sequential;
  token and wall-clock ratios.
- *Success / failure:* enable parallel writes for a category iff its
  measured silent-break rate ≈ 0 and EV is positive. **Results link out to
  a spike note**, not this RFC.

## Open questions

*Both resolved at acceptance (2026-05-29) with their recommended defaults;
neither blocks implementation. The safe-**loud** categories were decided by
the experiments and ship enabled under decision 3 — never an open question.*

1. **Dangerous (silent-failing) categories + net value — RESOLVED:** stay
   serial. Dynamic-semantic interference and shared mutable state can't be
   cleared by the deterministic canaries, so they remain serial-only; the
   safe-loud path ships on, and **T2-live** (post-acceptance, non-blocking)
   measures its real-world value before any expansion. Reopen only if
   T2-live shows the opt-in path doesn't earn its complexity. *Owner:*
   @eugenelim.
2. **Opportunistic-parallel substrate — RESOLVED:** delegate-to-driver
   where a multi-session driver exists (it owns isolation, avoids stacking
   worktrees on a shared `.git`); loop-managed worktrees standalone. The
   implementation spec formalizes this; no further decision needed.
   *Owner:* @eugenelim.

## Follow-on artifacts

- ADR: record topological-ordering-as-default + parallel-writes-gated-on-
  measured-disjointness, with the read/write split as the boundary.
- Spec: `docs/specs/wave-scheduled-supervisor/` — DAG build, cycle/forward-
  ref detection, sequential execution, failure handling, **and — as a
  required acceptance criterion (this is decision 3, not optional) — the
  opt-in parallel-write dispatch gate**: a wave parallelizes only when
  every task is in a safe category (cannot-collide / typed Group B /
  textual-loud) *and* the wave passes a `git merge-tree` file-disjointness
  check; all other categories (and any wave that fails the check) run
  serial. The spec's acceptance tests must cover both the allow path and
  the serialize-on-fail path.
- Convention change: `docs/CONVENTIONS.md` §Supervisor mode (default flip +
  the disjointness gate) and §Multi-agent shape by profile.
- Plan-template change: `new-spec/assets/plan.md` + SKILL — robust
  `Depends on:` parser + cross-spec marker; companion lint feeding
  `loop-cohort check --phase plan`.
- Tools: promote the experiment harnesses to `tools/` with regression tests
  (invoked via `sys.executable`).
- T2-live spike (per the Experiment section).
