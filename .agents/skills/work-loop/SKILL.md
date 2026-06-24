---
name: work-loop
description: Use this skill whenever you're implementing a non-trivial change -- a feature, a multi-file bug fix, a refactor, a migration, a framework or dependency upgrade, a schema or API change, performance work, an infrastructure or build-system edit, or anything spec-driven. It enforces the project's plan -> execute -> self-review -> fix loop with mechanical gates (lint, typecheck, tests) and adversarial review. Default to this skill for any task larger than a one-line edit.
---

# Skill: work-loop

This is the project's standard inner loop for non-trivial work. It exists
because LLM self-assessment is unreliable: agents declare victory when they
*feel* done, not when objective gates pass. This skill replaces "feel" with
verifiable termination criteria.

> **Vocabulary.** "Surface" throughout this skill means: stop the
> current loop, emit a short description of the situation in your final
> message (what happened, what you tried, what state things are in),
> and wait for human direction. It is the project's house verb for
> "stop and report." Do not retry, do not redispatch, do not silently
> reset. (Reviewers also "surface" findings in the descriptive sense
> — "raised" — when they return their report; context disambiguates.)

## When this skill applies

- Implementing a spec from `docs/specs/`.
- Bug fixes that touch more than one file — including security patches and incident hot-fixes.
- Refactors.
- Migrations, framework or dependency upgrades, schema or API changes.
- Performance work, or infrastructure / build-system changes beyond a single config tweak.
- Reverting and re-doing a previous change.
- Any task where you'd otherwise be tempted to "just go".

For genuine one-line edits (typo, config tweak), skip the loop — the overhead
isn't worth it. That triviality test decides *whether* to run the loop; once
you're in it, **risk** (not file count) decides *which mode* runs — see
[Modes: light and full](#modes-light-and-full) below.

## The loop

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

## Modes: light and full

`work-loop` has two modes, and which one runs is chosen by the **risk of
the work, not its file count** — a familiar two-file change is light; a
one-file change to an auth path is full.

<!-- risk-triggers:start — canonical wording lives here; copied verbatim
     into AGENTS.md, packs/core/seeds/AGENTS.md, and docs/CONVENTIONS.md.
     Keep all four byte-identical (grep-equality is an acceptance
     criterion of the work-loop-light-mode spec). -->
**Risk triggers — any one routes the work to full mode:**

- **Unfamiliar** — territory you don't know well.
- **Multi-person** — more than one person builds or reviews it.
- **Multi-feature or dependent tasks** — it decomposes a multi-feature
  brief, or its tasks depend on one another.
- **Compliance, governance, or security boundary** — it touches a
  compliance or governance surface, or a security boundary (auth,
  secrets, user input, deserialization, file or network I/O).
- **Structural or public-interface change** — it changes structure (a new
  module, layer, or boundary) or a public or published interface.
- **Destructive or irreversible operation** — it deletes data,
  force-pushes, drops tables, or otherwise can't be cleanly undone.
- **New dependency** — it adds a dependency.

No trigger fires → **light mode**.
<!-- risk-triggers:end -->

**Light mode (the default for low-risk work).** Scoped to a **single
logical task** — it may touch a few files, but it carries no inter-task
dependencies. Light mode keeps the loop's spine — EXECUTE, GATES, FIX,
and the capture-learnings step are all unchanged — and trims the ceremony
around it:

- **A lean inline spec, persisted** to `docs/specs/<feature>/spec.md` (not
  chat-only), opening with a one-line mode declaration —
  `Mode: light (no risk trigger fired)` — so the judgment call leaves a
  trace: Objective + Acceptance Criteria + a short task list. The
  remaining `new-spec` sections (Boundaries, Testing Strategy, Assumptions
  in the spec; Constraints, Risks, Changelog, and `## Design (LLD)` in the
  plan) are optional in a lean fill — write them only when they earn their
  place. Run `new-spec` to scaffold; its templates annotate which sections
  are optional.
- **A single bounded `adversarial-reviewer` pass** after GATES. A surfaced
  Blocker earns **exactly one** re-review of the fix; if a Blocker
  survives that, the work **escalates to full mode** rather than iterating
  — repeated Blockers are themselves a risk signal.
- **No default `quality-engineer` pass.** (A Blocker that escalates pulls
  in the full lens with it.) **Carve-out:** if the adopter has declared, in
  their `AGENTS.md`, that this repo is judged by a strict external quality
  gate the local loop can't run (a SonarQube quality profile, a CI-only
  coverage threshold), retain the `quality-engineer` pass even in light mode
  — it is the one lens that approximates that gate. This is *adopter-declared
  policy, not repo detection*: act on the declaration, don't scan for
  `sonar-project.properties` or a coverage config. Absent the declaration,
  light mode is unchanged (the pass stays dropped by default); the EXECUTE
  simplify pass still runs either way.
- **No `loop-cohort` state machine** — light mode does not invoke
  `loop-cohort` at all (no `init`, `approve-plan`, `check`, or
  `review record`). The mechanical doc-drift check still runs:
  `lint-spec-status.py` at the finish-time checklist, since it is a
  no-subagent lint that costs ~nothing.

**Full mode (unchanged).** Reached whenever any risk trigger fires. It is
the loop exactly as the rest of this document describes — `new-spec` with
all sections, the `loop-cohort` state machine, `adversarial-reviewer`
iterated to `Clean`, the `quality-engineer` floor at the end-of-session
checklist, and the iteration cap. **Everything below this section is full
mode unless it says otherwise**; light mode reuses those steps verbatim
except for the four trims named above.

### 1. PLAN — think before acting

For anything beyond trivial, *think before you write code*. Concretely:

- If the task has a spec, read `spec.md` and `plan.md` first. The plan's task
  list is your work-breakdown — don't invent your own.
- **Pick the mode first** (see [Modes: light and full](#modes-light-and-full)).
  If any risk trigger fires, you're in full mode: **stop and use the
  `new-spec` skill first**. Implementation without a contract drifts.
  The contract is part of the spec — `Acceptance Criteria` and
  `Testing Strategy` are written *during* `new-spec`, not later. A spec with
  either section left empty is not finished. In light mode, write the lean
  inline spec described above instead — Objective + Acceptance Criteria + a
  short task list, persisted to `docs/specs/<feature>/spec.md`.
- For architecturally significant work, use extended thinking. In an
  interactive Claude Code session: enter Plan Mode (Shift+Tab twice) and add
  "think hard" or "ultrathink" to your prompt for adaptive thinking depth.
  Other agents have their own facilities — use the equivalent.
- Write down: which files you'll touch, what tests will demonstrate "done",
  and what you are *not* changing. Three sentences is enough for the trio.

  Then, in a short paragraph below the trio, **name what you were tempted
  to add and explicitly declined** — usually one to three items, each with
  a one-sentence reason. *Patterns worth naming* are the structural
  temptations agents drift toward mid-EXECUTE: new abstractions
  (factories, locators, registries), structural choices (new module, new
  layer, new boundary), framework or dependency introductions, defensive
  scaffolding (validation wrappers, error-mapping layers), and
  configurability for hypothetical futures (flags, options, env vars). The
  shape is one line per declination: *"Tempted to add a ServiceLocator;
  declining — direct construction is fine for now."* This is a commitment,
  not a checklist — naming a temptation here means REVIEW can catch drift
  toward it as self-contradiction in the diff. The trio's three-sentence
  cap doesn't bind this paragraph; brevity still does.
- **Pick the verification mode for each plan task** before writing code.
  The mode is the task's contract for "how do we know this is done":
  - **TDD** — pure functions, state machines, protocols, anything with a
    compressible invariant. The contract lives in `spec.md` (Acceptance
    Criteria + Testing Strategy); construction tests live in `plan.md`,
    `Tests:` before `Approach:`, red-green-refactor.
    Default for testable logic.
  - **Goal-based check** — build config, scaffolding, generated-code
    consumption, smoke entry points. The task's `Done when:` is the
    contract; verify with a one-liner (build command, `grep`, typecheck)
    instead of a test file. Don't write a test that just asserts what
    the compiler already proves.
  - **Visual / manual QA** — UI rendering and end-to-end UX flows, **and any
    other artifact a user invokes directly**: a CLI, a library's public API, an
    agent or skill, a service endpoint. The task records the manual check
    explicitly. **When a change ships something a user invokes, verification
    includes exercising the real built artifact end-to-end the way a user
    would — through the documented happy path — and recording what you
    observed**: the actual stdout and exit code, the returned value, the file
    written, the on-screen result. Assert on that observed result, not on
    internal state (store contents, mock-call counts, context-provider values),
    and don't let a passing unit gate stand in for the real invocation. A test
    or check that passes while the artifact, run as documented, produces the
    wrong result is mode-mismatched, regardless of which framework wrote it.
    For UI flows "what you observed" is *what the user actually sees* (rendered
    text, visible elements, navigation); for a CLI it's the command's real
    output and exit status; for a library it's the public call's result and
    effects through its documented entry point, not a private internal. This is
    **harness-agnostic doctrine** — exercise the artifact by hand on any agent;
    in Claude Code the native `/verify` and `/run` commands perform it, an
    optional accelerant and never a dependency, so adapters without them lose
    only the shortcut, not the step. Add automation when the regression cost (a
    broken invocation ships invisibly) outweighs the cost (flakiness,
    brittleness); the choice of tool is the adopter's. A third flavor —
    *exploratory / visual fuzz* — drives the UI with varied or random input and
    asserts **invariants** ("didn't crash, didn't render garbage, layout holds,
    no overflow") rather than specific outputs. Reach for it when the failure
    mode is open-ended and you can't enumerate the gestures up front.
  - **infra/deploy** — provisioning or changing infrastructure (a cloud
    deploy, an IaC apply, a stateful migration). The fourth verification
    *mode*; unlike the three above, its contract is a **layered GATES
    sequence**, not a single check — **static preflight** < **plan / preview**
    < **idempotent convergent apply** (the precondition the rest rests on —
    re-run must *converge, not collide*) < **active end-to-end smoke** (a
    multi-hop probe, not a status check) < **rollback** (a known-good re-apply
    path named *before* the first apply). It names *how we verify*, not
    deployment *sequencing* (the plan template's `## Rollout` owns that —
    cross-reference, don't duplicate). Every layer is tool-neutral (Terraform /
    Pulumi / CDK / CloudFormation / hand-rolled alike; any tool named is
    illustrative). **Full infra doctrine — the layer detail, the multi-artifact
    preflight, the EXECUTE contract-grounding gate + craft load, the
    reusable-script discipline, phased oracle fidelity (V1, the cheap-early
    oracle is necessary-not-sufficient), and the readiness-aware data-plane
    probe (V2) — is progressive-disclosure depth in
    [`references/infra-verification.md`](references/infra-verification.md),
    loaded on infra-flavored work.**

  **Confirm the mechanism exists before you claim the mode — task zero if it
  doesn't.** Picking a verification mode obligates confirming that the
  mechanism that mode depends on actually exists; if it does not, **building it
  is task zero** — a precondition task in the plan, not an afterthought — and
  the loop offers to scaffold it. This obligation is **agnostic and universal
  across light and full mode**: it applies to a TDD task whose test runner
  isn't wired, a goal-based task whose build command doesn't exist yet, and a
  manual-QA task whose artifact can't yet be run, exactly as much as to a
  missing infra smoke check. It strengthens the assumption-trio — "the
  mechanism exists" is the kind of assumption that goes unsurfaced precisely
  because it doesn't feel like one.

  For **infra/deploy** the mechanism is rarely one artifact; the preflight
  enumerates a **multi-artifact set, each its own task-zero** — a
  **verify-status** script, a **teardown** script, **test-data / mock-user
  seeding**, a **provider-appropriate policy-as-code / CSPM scanner**
  (per-provider-depth source, **mechanism-level not tool-level**, feeding both
  the static preflight and the mandatory security pass), and a **durable
  credential session** (establish once, reuse). Detail — and that none ship as
  executable tooling — in
  [`references/infra-verification.md`](references/infra-verification.md).

  Spikes and throwaway exploration are out of scope.
- **Design tests up front, before any code.** The contract lives in
  `spec.md` (Acceptance Criteria + Testing Strategy) and is written when
  the spec is written (see the `new-spec` step above). During PLAN, write
  construction tests for **every** task into `plan.md` (under each task's
  `Tests:` subsection) before EXECUTE begins. If you can't write the
  test, the task is too vague to implement — sharpen the plan first. Discovering a missing or wrong construction test
  during EXECUTE is fine, but the fix is "update plan.md, then resume
  EXECUTE", not "skip ahead".
  **For TDD-mode tasks, materialize each `Tests:` subsection as a
  compilable, validated red stub** rather than prose — see
  [`references/tdd-stubs.md`](references/tdd-stubs.md) (load it on demand).
  A stub that won't compile is the mechanical signal an AC is too vague,
  caught here instead of mid-EXECUTE. Goal-based and manual-QA tasks record
  `no stub (mode)`; light mode skips this entirely.
- **Pre-EXECUTE adversarial review.** Select a subagent matching
  `adversarial-reviewer` and ask it to review the spec + plan in
  spec/plan-review mode. Iterate to clean before EXECUTE begins when
  **either** trigger fires (fallback if no such subagent is installed:
  proceed but note the missing review in the final summary):

  1. **Spec amendment.** PLAN produced or modified a spec — you ran
     `new-spec`, or you sharpened an existing `spec.md` / `plan.md`.
  2. **Structural change.** Any plan task introduces structural surface
     area. Walk this checklist; if **any** condition matches, the
     trigger fires:
     - New module boundary — a new directory under `packages/` or
       `apps/`.
     - New dependency added to package code — especially a framework,
       ORM, or runtime.
     - New abstraction layer — a new interface mediating between two
       existing concrete things; a new factory, registry, locator, or
       service-locator pattern.
     - New top-level directory — the most expensive of the four to
       undo. Many projects already gate this through their own RFC or
       ADR process; the trigger fires here either way.

  The structural-change trigger fires even when no spec is amended in
  this PR — the trigger is the **plan's task shape**, not a spec edit.
  Both triggers route to the same reviewer mode and the same spec-stage
  checklist; what differs is the standard the reviewer measures against.
  When the structural-change trigger fires, the reviewer checks the
  plan against the spec's **Boundaries** section (defined by the
  `new-spec` skill's bundled `spec.md` template) —
  primarily `Never do` for hard structural rules and `Ask first` for
  the ones that require sign-off; `Always do` for positive defaults
  the plan must honour. If `Boundaries` is empty, that's the
  finding to surface first — an empty Boundaries section is a
  spec-stage gap, not a fallback cue. Only when the spec has no
  Boundaries section at all (an unmigrated template, say) fall back
  in order to: the PLAN step's **declined-pattern register** (above),
  and the AGENTS.md **"Check before acting"** list (when installed
  elsewhere this slug arrives as a fragment under
  `docs/AGENTS.fragments/`; merge the items the adopter wants into their
  own AGENTS.md).

  **Re-fire on mid-EXECUTE re-plan.** If EXECUTE discovers a missing or
  wrong task and updates `plan.md` per the *Design tests up front* rule
  above, re-evaluate the structural-change checklist against the
  updated plan. If a re-plan introduces any of the four conditions that
  the original plan did not, the trigger re-fires and the reviewer
  re-runs before EXECUTE resumes. This is where most over-engineering
  emerges in practice — a tempting abstraction surfaces mid-flight, not
  during the original PLAN — so the one-shot trigger is not enough.

  Cheap-to-fix-early applies harder to specs and structural decisions
  than to code — catching a vague behavior, a missing `Depends on:`,
  a mismatched verification mode, or a misplaced module boundary here
  costs a sentence; catching it post-EXECUTE costs a re-do. Gate
  mechanism is unchanged: the `loop-cohort approve-plan` verb flips
  `state.json.plan_review_status` to `approved` once the reviewer is
  clean; `loop-cohort check <spec-dir> --phase plan` unlocks EXECUTE.
  No new state fields. **Both triggers respect the Profile-A opt-out:**
  skip if the project doesn't use the reviewer at all.
- **Pre-EXECUTE secure-design review (net-new — security-boundary trigger).**
  **Doctrine: security review shifts left — it runs at spec stage on
  security-boundary work, not only as a late gate.** When the
  **security-boundary risk trigger** is present (the change touches auth,
  secrets, user input, deserialization, or file/network I/O), additionally
  select a subagent matching `security-reviewer` and dispatch it in
  **spec-stage secure-design mode** against the spec — asking, per trust
  boundary the feature crosses, whether the control is specified as an
  acceptance criterion at the right depth (confinement, not just traversal;
  scheme allowlist, not "validate the URL"; broker-mediated secrets, not
  ad-hoc reads). Inline the boundary-matching `security-checklists` modules
  into its brief in their proactive-control framing, per the
  [boundary→module routing table](#boundarymodule-routing-table) below. This
  is **net-new wiring** — distinct from the adversarial-only firing above and
  from the separate light→full escalation use of the same trigger; it
  is not a re-use of either. Same Profile-A opt-out and the same
  `approve-plan` gate apply. Fallback if no `security-reviewer` subagent is
  installed: proceed and note the missing review in the final summary.

  **For infra-flavored work this spec-stage pass is mandatory, not
  discretionary.** "Infra-flavored" is a **defined signal, not an ad-hoc
  judgement**: work that the **destructive/irreversible risk trigger** routes to
  full mode *and* whose spec matches the
  [boundary→module routing table](#boundarymodule-routing-table)'s IaC /
  deploy-config entry — the same classifier that already drives security-module
  loading (the spec-stage half keys this match on the spec; the diff-stage half
  on the diff — same routing-table entry). When that signal is present the
  `security-reviewer` runs at spec stage **regardless of** the discretionary
  security-boundary trigger, and the orchestrator **force-loads** the
  infra-relevant `security-checklists` modules (the candidate set the REVIEW
  `security-reviewer` bullet names), loaded 1–N as the spec warrants per that
  table. The matching diff-stage pass, the reviewer-plus-scanner pairing, and
  the Profile-A / missing-subagent interaction all live in that REVIEW bullet —
  this is the spec-stage half of the same non-skippable, both-stages pass.
- **Initialize the loop's state file.** Run this skill's bundled
  `scripts/loop-cohort.py init docs/specs/<feature>`; the tool copies
  the bundled `assets/state.json` template into place, sets `feature`
  to the spec slug, and writes atomically. The file is gitignored —
  session-scratch, not history. Then run `loop-cohort.py check
  docs/specs/<feature> --phase plan`; on the first invocation it will
  exit 1 with `plan not approved` — **this is the expected cue to run
  the pre-EXECUTE reviewer**, not a stop-and-surface signal. Once the
  reviewer is clean, run `loop-cohort.py approve-plan docs/specs/<feature>`
  and re-run check; exit 0 unlocks EXECUTE. Every state mutation —
  template copy, status flip, atomic write — is owned by the tool; do
  not edit `state.json` by hand. Schema reference:
  [`references/state-schema.md`](references/state-schema.md).

The output of this step is a written plan (with tests) you can return to.
Don't keep it in your head — your context will turn over and you'll lose it.

### 2. EXECUTE — make the change

Match the discipline to the verification mode you picked during PLAN:

- **TDD-mode tasks** — red-green-refactor:
  1. Write the failing test first (red). Commit it if non-trivial. If PLAN
     already produced a stub for this task
     ([`references/tdd-stubs.md`](references/tdd-stubs.md)), the red test is
     usually already written — verify it's red and fill out its deferred
     assertions, don't rewrite it from scratch.
  2. Write the minimum code to make it pass (green). Commit.
  3. Refactor with the test as your safety net. Commit.
- **Goal-based check** — write the code, then run the one-liner from
  `Done when:`. No production test file.
- **Visual / manual QA** — implement, then exercise the built artifact
  end-to-end through the documented workflow recorded in the task, and
  record what you observed (real output, not internal state).
- **infra/deploy** — implement the change, then **drive the deploy yourself
  and read the real environment output** (run the apply, smoke probe, log pull,
  teardown; read their *actual* output, don't reason about what they'd say). The
  **human-as-relay** pattern — a human pasting deploy errors back by hand — is
  the anti-pattern this removes. Harness-agnostic doctrine; Claude Code
  background tasks / `asyncRewake` / `PreToolUse` are **accelerant, never a
  dependency**. The EXECUTE-phase infra craft — the `cloud-implementation-craft`
  load (orchestrator-inlined into the implementer's brief) and the
  reusable-script discipline — is in
  [`references/infra-verification.md`](references/infra-verification.md).

**EXECUTE contract-grounding gate (infra — universal across light and full
mode).** Before generating a CLI invocation, an IaC resource, **or application
code that runs on a managed runtime**, against an **unfamiliar platform**,
acquire its contract via the
[`infra-contract-acquisition`](../infra-contract-acquisition/SKILL.md) skill —
never guess a flag, schema shape, field constraint, or packaging assumption.
It is the **infra generalization of AGENTS.md's "Grep to verify a function
exists before importing it"**, and is **universal** (fires in light mode too);
heavier infra-flavor layers fire only on the infra-flavored signal. (RFC-0044 §
Errata 2026-06-24; full detail in
[`references/infra-verification.md`](references/infra-verification.md).)

For each task, implement the smallest coherent unit of work toward the
goal. Resist the urge to fix unrelated things you notice along the way;
note them in `notes/` for later. Scope creep is the single biggest source
of plan-vs-implementation drift.

<!-- Bundled-fixes carve-out — canonical site. Mirrored by
     implementer.md (operating envelope) and adversarial-reviewer.md
     (scope check #4). Keep all three in sync. -->
**Bundled-fixes carve-out.** Same-area, same-concern, mechanical
ride-alongs land in the change — dead import, stale comment that now
contradicts the new code, unused local the change orphaned, typo in a
sibling file. *Same area* means a file in a directory that already
contains a file the change is editing — siblings in the touched
directory, not a walk-up to the parent and not a sideways jump to a
directory the change isn't editing. "The change" = the current plan
task for the executor; the merged PR diff for the reviewer. The
reviewer is loading that directory's context for the primary change;
tagging along is cheap. List ride-alongs in the PR description under
`Bundled fixes:`, one line each, so the reviewer can scan them at a
glance. The carve-out fails closed on any of: a file outside a
touched directory, a design call, a behavior change. Those still go
to `notes/` (EXECUTE-phase surplus, picked up by a future plan task);
contrast with the DECIDE-phase `Deferred:` bucket below, which holds
reviewer findings the loop chose not to fix — different lifecycle,
different reader. **Volume guard** — bundled fixes are individually small
(a line or two each). The bundle should also be visibly smaller than
the primary change: if a reviewer reading the PR couldn't immediately
tell which part is the primary change and which are ride-alongs, you
sprawled — move the surplus to `notes/`. In supervisor mode, the
dispatch brief explicitly authorizes the carve-out and restates the
gates so the implementer applies them per its own task; without that
authorization line the implementer defaults to no-carve-out.

**`Bundled fixes:` in the PR description.** The work-loop emits a
named `Bundled fixes:` section in the PR description that doesn't
appear in the project's PR template — one line per ride-along landed
under the carve-out above. Append it as a standalone section below
the standard template content; do not modify the template itself.
(See step 5 for the companion `Deferred:` section.)

**Simplify pass — reduce the diff before review.** Once this task's
GATES (step 3) are green, take one deliberate pass to shrink the diff
before it reaches REVIEW: inline a single-use helper, delete code the
change orphaned, collapse needless indirection, drop a parameter no
caller varies. Scope it to the **new code only** — leave adjacent
untouched code alone (refactoring it is the bundled-fixes carve-out's
job, under its own gates) and leave tests DAMP, since duplicated-but-
readable test setup is not "indirection to collapse". Less code is less
to smell and less to review, which is the cheapest way to clear a strict
quality floor. This is **harness-agnostic doctrine** — do the pass by
hand on any agent; in Claude Code the native `/simplify` command
performs it, an optional accelerant and never a dependency, so adapters
without it lose only the shortcut, not the step.

#### Scale with a tool, not turns

When a task spans many similar items — apply one change across N files,
extract or transform a large set, audit every module against a rule —
grinding through them item-by-item across turns exhausts context and
reliably stalls before the last item, leaving the work *looking* done
while the tail was never touched. **Reach for this whenever the work is
repetitive and larger than a single window holds.** The move: write a
small script that enumerates the items, drive them through a resumable
tracking file (per-item `pending`/`done`/`failed`), and iterate
idempotently so a re-run skips what's already done — that resumability,
not your stamina, is what guarantees 100% completion. Where a per-item
step needs judgment the script can't make, the script can shell out to
the agent once per item; the tracking file still governs completion. It
converts *"too big for my context"* into *"mechanical and resumable."*
Throwaway tools are fine; occasionally one earns a place in `tools/`.
Full playbook — tracking-file schema, idempotency and resumability, when
to shell to the agent, keep-vs-delete the tool — in
[`references/scale-with-a-tool.md`](references/scale-with-a-tool.md)
(load it on demand).

#### Parallel dispatch discipline

When this skill fans out — multiple implementers in supervisor mode, or
multiple specialist reviewers in REVIEW — the rules are the same and
they live here, single-sourced. Both call sites below reference this
discipline rather than restating it.

- **One tool-call message, one Agent use per target.** Issue all
  subagent invocations in a single message. Do not call them
  sequentially. The participants are independent, the lenses are
  independent, and sequencing tempts you to react to the first return
  before the rest land — which gives each subagent a different state.
- **Barrier-wait.** Don't issue follow-on Agent calls until every
  subagent in the round has returned.
- **Harness-level non-returns are failures.** A timeout, a tool error,
  or a missing report counts as `failed` for that target. Treat it the
  same as a substantive `failed` status; do not retry silently.
- **Merge results in your own context.** The subagents return markdown.
  You read N reports, group findings or status by your own bookkeeping
  (state.json for implementers; severity buckets for reviewers), then
  decide.

#### Supervisor mode (wave-scheduled; sequential by default)

Run `loop-cohort schedule docs/specs/<feature>` to build the plan's full
`Depends on:` DAG and get the topological order. **Execute tasks in that
order, single-agent, by default** — on every adapter. `schedule` fails
loud on a dependency **cycle** and warns on a **forward-reference** (a dep
authored later — it reorders so the dep runs first), so an ill-formed plan
is caught here, not run out of order. This is the proven, zero-hazard path;
its win is correct ordering, not speed. If tasks
declare optional `Touches:` globs, `schedule` also prints
`predicted-disjoint: yes|no|unknown` per wave — a **serialize-only screen**
(a predicted overlap is a reason to keep the wave serial; it **never**
greenlights parallel — the gate below stays authoritative).

**Parallel implementer fan-out is opt-in and gated — never automatic.** A
wave of mutually-independent tasks may run in parallel *only* when it
clears the dispatch gate (`loop-cohort dispatch-decision`): every task in
a safe category (cannot-collide / typed-Group-B / textual-loud) **and** a
clean `git merge-tree` file-disjointness check. Any other category, or any
merge-tree conflict, stays serial (fail closed). **You don't hand-classify
the categories** — omit `--category` and the verb auto-derives each from its
`--branch`'s committed diff (fail-closed: only all-added, no-danger-path,
no cross-branch basename/dir collision → `cannot-collide`); pass `--category`
only to override (the sole way to assert `typed-group-b`, which is never
auto-derived). When the gate returns
`parallel`, behavior depends on `state.json.auto_parallel` (set per-run via
`loop-cohort auto-parallel`, default off):
- **`auto_parallel` unset (default):** **present the cleared-gate opportunity
  to the human** — name the parallel-eligible wave and its tasks (the verb's
  stderr rationale gives you the line) and fan out **only on an explicit
  opt-in**; absent one, run the wave sequentially. Never fan out silently.
  Present-and-default-safe, **not** the halt-and-wait Surface verb — so, *with
  `auto_parallel` unset*, an unattended run simply proceeds sequentially rather
  than blocking.
- **`auto_parallel` set:** the human pre-authorized this run, so a
  **gate-cleared** wave fans out **without** the opt-in (this is what lets a
  plan finish unattended). **GO-approval-only** — it skips *only* the
  human-confirm step for an **already-cleared** wave; it is never a gate input,
  never parallelizes a wave the gate didn't clear, and a parallel wave that
  **fails** (merge-abort) still **Surfaces and stops** — never auto-retries.

When you do opt in (either path), select a subagent matching `implementer` per the
parallel-dispatch discipline above; **the full 7-step worktree procedure**
lives in [`references/supervisor-mode.md`](references/supervisor-mode.md) —
load it on demand. Parallel *reviewer* (read) fan-out is a separate,
always-safe path and is unaffected. The single-agent fallback (no
`implementer` subagent installed) is documented in the reference too.

### 3. GATES — mechanical verification

Run, in order, and only proceed if each passes:

```bash
<lint command>      # style and basic correctness
<typecheck command> # type safety (if applicable)
<test command>      # behavior
```

These are the project's **objective** completion criteria. If a gate fails,
go to FIX. Don't move past a failing gate by editing the gate.

> **Mechanical doc-drift check — `scripts/lint-spec-status.py`.** This skill
> ships a stdlib Python lint at `scripts/lint-spec-status.py` (sibling to
> `loop-cohort.py`) that checks spec *metadata* invariants against the contract
> pinned in `CONVENTIONS.md` § 4: (i) status vocabulary, (ii) ACs
> checked-or-deferred at the ship transition, (iii) dangling doc/code references
> (warn-only), (iv) deferral anchors resolve in `docs/backlog.md`. Where you have
> Python, **run it at the finish-time checklist** (DECIDE, below) —
> `python <skill>/scripts/lint-spec-status.py` — as the mechanical companion to
> the four drift invariants the `adversarial-reviewer` checks by judgment; it
> no-ops where Python is absent. It is *available and agent-invoked, not
> fail-closed* (there is no PR-open hook event to bind it to). **Do not** wire it
> into `pre-pr.py` (a projected hook body that would mis-fire). It can also
> run as a fail-closed CI gate. (Why a
> skill script and not a `tools/` linter: skill `scripts/` project to every
> adapter — a later correction to the original "linters don't
> project" premise.)

### 4. REVIEW — adversarial self-review

After gates pass — and after the EXECUTE **simplify pass** has shrunk the
diff (run it now if you skipped it) — run adversarial review against the
spec. Select a subagent matching `adversarial-reviewer` and pass it the diff
plus the spec path (e.g. `docs/specs/<feature>/spec.md`). Fallback if no such
subagent is installed: proceed but note the missing review in the final
summary — the gates step is the mechanical termination criterion; this
step is judgmental and the loop degrades to gates-only without it.

The subagent reads adversarially — it's looking for what you missed, not
celebrating what you did. Findings come back grouped by severity
(Blockers / Concerns / Nits), each with a one-sentence `Fix:`. Iterate
until the agent returns `Clean — ready to commit.`

**After each reviewer pass, record findings via the tool** before
iterating. Write the reviewer's report to disk, then run:

```
loop-cohort.py review record docs/specs/<feature> --report <report-path>
loop-cohort.py check docs/specs/<feature> --phase review
```

`review record` parses the report's findings (anchored on the
adversarial-reviewer's documented `**N. <title>.** \`file:line\`. … Fix: …`
format), computes `sha1("<file>|<line>|<title>")` per the canonical
algorithm, rotates `finding_fingerprints` → `previous_finding_fingerprints`,
sets the new list, increments `iteration_count`, and writes atomically —
one transaction, no by-hand JSON. If the parser surfaces zero findings on
a non-clean report it exits non-zero; pass `--fingerprint <hex>` repeated
to override. `check --phase review` then enforces stasis detection: exit
1 with `no progress` means the same findings landed two iterations in a
row; stop and surface to a human rather than spinning a third.

**Once recorded, drop the full report text from resident context.** The
on-disk report plus the `state.json` fingerprints are the durable record —
nothing load-bearing lives only in the window. When a FIX needs a finding's
detail, re-read that finding from the on-disk report rather than holding the
whole prose resident; and the *next* REVIEW pass regenerates the current
findings from scratch, so a stale full report has no reason to ride along
across iterations. (There is no pre-filtered "open findings" file — which
findings are still open is your DECIDE-phase routing call, not a stored
artifact.) This keeps a multi-loop spec's window clear without touching the
stasis/iteration guarantees above, which read from `state.json`, not from
resident prose.

**Specialist reviewers — use after adversarial-reviewer is clean.** Pick
the ones the diff actually warrants; don't run all three by default.
Select each via the same "subagent matching `<role>`" pattern as
adversarial-reviewer above; absence of any specialist subagent is a
note in the summary, not a blocker.

- Match `security-reviewer` — for diffs that cross a security boundary
  (auth, secrets, user input, deserialization, file/network I/O,
  dependencies, LLM/agent code). Current multi-framework lens (OWASP Top
  10:2025, ASVS 5.0, API Security Top 10:2023, LLM Top 10:2025, CWE Top 25)
  plus a STRIDE + LINDDUN open pass. Complements SAST/SCA scanners; does not
  replace them. **Inline its depth, don't make it self-discover:** detect
  which trust boundaries the diff crosses, load **only** the matching
  `security-checklists` modules, and inline their content into the
  subagent's brief (reusing the on-demand `references/*.md` loading the loop
  already does) — the subagent's `tools:` has no Skill tool, so loading is
  orchestrator-driven, not model-relevance-judged. Route deterministically:

  <a id="boundarymodule-routing-table"></a>

  | Trust boundary the change crosses | Inline module(s) |
  | --- | --- |
  | Authz / access-control; a new or changed endpoint, handler, RPC | `access-control` |
  | Authentication, session, login, password, MFA, tokens (JWT/API key) | `authn-session` |
  | Untrusted input → SQL / shell / template / LDAP / HTML; deserialization | `injection` |
  | Filesystem path from input, file upload, archive extraction | `path-and-file` |
  | Secrets, keys, hashing, signing, crypto, randomness | `secrets-and-crypto` |
  | Outbound HTTP / DNS / URL fetch, webhooks | `outbound-ssrf` |
  | Dependency / lockfile / manifest change, build-artifact fetch | `supply-chain` |
  | CORS, IAM, IaC, server / framework / deploy config | `config-misconfig` |
  | Error handling, retries, fallbacks, fail-open paths | `exceptional-conditions` |
  | Prompts, model / tool exposure, MCP, model-output handling | `llm-agent` |

  Load 1–3 modules for a typical change, never a flat march of all ten; an
  auth-touching endpoint pulls `access-control` and often `authn-session`.
  This same table backs the pre-EXECUTE spec-stage dispatch above.

  **Mandatory and multi-module on infra-flavored work.** When the change is
  **infra-flavored** (the destructive/irreversible trigger routed it to full
  mode *and* its diff matches the IaC / deploy-config entry above), the
  `security-reviewer` pass is **non-skippable** and runs at **both the spec
  stage and on the diff** — it keys on the existing classifier, so it **cannot
  be silently skipped**. The orchestrator force-loads the infra-relevant
  modules **1–N** (`config-misconfig` always, plus `access-control` /
  `secrets-and-crypto` / `outbound-ssrf` / `supply-chain` as the diff trips
  *that module's own* row — never a flat always-five march). **No new reviewer
  or module.** The Profile-A opt-out still applies wholesale, but where
  `security-reviewer` is in use the infra pass is **not individually skippable**,
  and a missing subagent on infra-flavored work is a **loud blocker, not a
  silent proceed**. Security on infra is a **reviewer + scanner *pair*** — the
  reviewer for failure *classes* (over-broad IAM, public exposure, secrets in
  state, metadata SSRF), the scanner for per-provider secure-config depth; run
  both. Full detail in
  [`references/infra-verification.md`](references/infra-verification.md).
- Match `quality-engineer` — testability, observability, reliability, and
  maintainability lens, applying a raised default quality floor (universal
  maintainability smells + a mutation-testing mindset) even where no static
  gate is wired. Also drafts contract or construction tests on request.
  Different lens from adversarial-reviewer — don't skip it because the spec
  already shipped.

  **Inline operational depth on infra/destructive work, don't make it
  self-discover.** When the diff is **infra-flavored** — the
  **destructive/irreversible risk trigger** routed it to full mode *and* it
  provisions, mutates, deploys, or tears down infrastructure — the
  `quality-engineer` is the consumer of a second progressive-disclosure depth
  library, [`operational-safety`](../operational-safety/SKILL.md), exactly as
  `security-reviewer` consumes `security-checklists`. Detect which operational
  failure modes the change raises, load **only** the matching
  `operational-safety` modules, and inline their content into the subagent's
  brief (reusing the same on-demand `references/*.md` loading) — the
  `quality-engineer`'s `tools:` has no Skill tool, so loading is
  orchestrator-driven, not model-relevance-judged. **No new reviewer** — this
  feeds the existing `quality-engineer` (ADR-0023). Route deterministically:

  <a id="operational-safety-routing-table"></a>

  | Operational failure mode the infra/destructive change raises | Inline module(s) |
  | --- | --- |
  | Authoring infra / a managed-runtime deployment / live interaction — permissions, timing/retry, packaging, externalized config (**also inlined into the implementer's EXECUTE brief**, above) | `cloud-implementation-craft` |
  | Provisioning or mutating infra; stateful migration; any re-runnable write path | `state-and-idempotency` |
  | Can delete or replace existing infra; destroy/teardown path; removing a prevent-destroy guard | `blast-radius` |
  | Iterating against (or able to touch) production; shared vs throwaway/staging state | `environment-isolation` |
  | Provisions billable resources; ephemeral/per-iteration infra; teardown path | `cost-and-teardown` |
  | Long-lived infra that can drift; a deploy needing a defined recovery path | `drift-and-rollback` |
  | Deploys a service / site / endpoint a user reaches; needs smoke + telemetry | `observability-and-smoke` |

  Load 1–N modules as the change warrants, **never a flat march of all seven** —
  a one-line config tweak pulls one; a new public-facing stack pulls several.
  This is the operational twin of the `security-checklists` routing table
  above, and the **reliability-vs-security carve** holds: IaC-security →
  `config-misconfig` (the `security-reviewer` pass); IaC-reliability →
  `operational-safety` (this pass). The two passes are complementary lenses on
  the same infra diff, not substitutes.

  **Independent contract re-derivation on infra-flavored work (Delivery — no
  new agent).** On infra-flavored work the orchestrator also inlines
  [`infra-contract-acquisition`](../infra-contract-acquisition/SKILL.md) into
  the `quality-engineer` brief, and the reviewer **re-derives the platform
  contract independently from the oracles** — **never trusting the implementer's
  own contract evidence** (which would reproduce the field-report blind spot).
  **No new reviewer or agent** (ADR-0023): contract-conformance rides the
  existing `quality-engineer`; the dedicated `infra-contract-reviewer` is
  deferred behind RFC-0044 Decision 8's evidence trigger, and the
  auth-flow-contradiction class is caught at spec stage by `design-reviewer`
  where the architect pack is installed. Full wiring in
  [`references/infra-verification.md`](references/infra-verification.md).

**Dispatch reviewers in parallel when you invoke more than one** per
the [Parallel dispatch discipline](#parallel-dispatch-discipline)
documented under EXECUTE — the same rules cover both fan-out sites in
this skill. Fan-out works here because reviewer output is markdown the
orchestrator reads, not a structured contract: you read N reports,
group findings by severity yourself, deduplicate where two reviewers
caught the same thing, then iterate on the merged list. Fingerprint
computation (state.json) happens once per fan-out round, not once per
reviewer. Record the round, then evict the merged prose the same way —
fingerprints and the on-disk reports are the record; the merged list does not
stay resident across FIX iterations.

If reviewing a spec-less change (a refactor, say), self-review against this
checklist instead:

- Does the diff match the plan you wrote in step 1? Note divergences.
- For each touched function: is the test coverage no worse than before?
- Did anything outside the planned scope get touched? Why?
- What's the dog that didn't bark — what *should* have changed and didn't?

### 5. DECIDE — fix or finish

Route each reviewer finding into one of two resolution modes — `apply`
(fix in this PR) or `defer` (capture as a follow-up). This is the
work-loop's interpretation of reviewer output; the reviewer keeps its
narrow Blockers / Concerns / Nits contract. Once routed, act on each
mode below, then evaluate the terminal-state bullet last.

- **Blockers** → `apply`. Re-run GATES and REVIEW after each fix.
- **Concerns** → `apply` if mechanical and in scope (default for any
  Concern whose fix meets the bundled-fixes gates above). `defer` if
  the fix would cross files outside the plan, require a design call,
  or change user-visible behavior the spec didn't authorize. Don't let
  Concerns rot in chat — every Concern resolves into one of the two.
- **Nits** → same two modes as Concerns. `apply` if they meet the
  bundled-fixes gates above (ride along in `Bundled fixes:`).
  Otherwise `defer` — one line in `Deferred:`. Every Nit resolves
  into one of the two; the `Deferred:` line *is* the acknowledgement
  that the loop saw the Nit and chose not to fix.
- **Deferred items** → record each in the durable register,
  `docs/backlog.md`, under a heading, so they don't rot. The spec criterion
  that defers carries an inline `(deferred: <anchor>)` marker pointing at that
  heading (`CONVENTIONS.md` § 4 Spec metadata contract). The PR description
  keeps only a one-line **pointer** to the register entry — append it as a
  standalone `Deferred:` section below the standard template content alongside
  the `Bundled fixes:` section from EXECUTE; do not modify the template itself.
  The register, not the PR comment, is the durable record: it's
  version-controlled and greppable, and the `(deferred:) ↔ backlog.md`
  resolution is mechanically checked (catalogue lint) or reviewer-checked
  (adopters). Mirroring an item to an issue tracker is an option where one
  exists, never assumed.
- **Gates green and review clean** → ready to ship. Walk this end-of-session
  checklist; refuse to declare done until every line is true. (**In light
  mode**, two lines relax per the [Modes](#modes-light-and-full) section: the
  `quality-engineer` floor below is dropped — a surviving Blocker escalates to
  full mode instead — and "review clean" means the single bounded
  `adversarial-reviewer` pass, with no `loop-cohort` involved. The doc-drift
  invariants and `lint-spec-status.py` still apply.)
  - GATES were clean (lint, typecheck, tests).
  - **If the change ships something a user invokes** (a CLI, a library's
    public API, an agent, a UI), the real built artifact was exercised
    end-to-end through its documented happy path and the observed result
    recorded — a passing unit gate alone does not satisfy this.
  - For each reviewer the diff warranted (`adversarial-reviewer`
    always; `security-reviewer` on security-boundary diffs;
    `quality-engineer` on every loop, plus a whole-spec pass on the
    final loop of a multi-loop spec): either the subagent returned
    `Clean — ready to commit.`, **or** no matching subagent was
    installed and the final summary names the missing review by its
    role label — e.g. `adversarial-reviewer: no matching subagent
    installed; review skipped`. *Silently skipping the reviewer is not
    allowed* — the select-or-note discipline applies here, not just at
    invocation time.
  - Whole-spec `quality-engineer` pass (final loop of a multi-loop
    spec only): same select-or-note rule. Per-task gates verify N
    contracts; this is the pass that verifies the integrated journey.
  - `git status` shows no uncommitted or untracked files (except
    gitignored scratch).
  - **Doc-drift invariants hold** (the four the `adversarial-reviewer`'s
    "Spec drift" check names, against `CONVENTIONS.md` § 4): the touched spec's
    status reflects the change; every Acceptance Criterion is `[x]` or carries
    `(deferred: <anchor>)`; each deferral resolves to a `docs/backlog.md`
    heading; intra-repo references the change touches resolve. Where you have
    Python, run `scripts/lint-spec-status.py` (this skill's sibling to
    `loop-cohort.py`) to check these mechanically — it's the agent-invoked
    companion to the judgment check; no-ops without Python.
  - Conventional commit format used; no force-push to shared branches.
  - Learnings captured per the next section (AGENTS.md, skill, or doc).
  - PR opened — or merged directly, if that's your workflow — with the
    four-question template filled in.

## FIX phase

Fixing is the same loop, scoped to a single finding:

1. Read the finding carefully. Don't fix the symptom — fix what the reviewer
   actually flagged.
2. Make the smallest change that addresses it.
3. Re-run GATES.
4. Re-run REVIEW only if the fix touched logic the reviewer hadn't already
   approved. Otherwise, you can skip review and move on.

## Termination — when to stop iterating

The loop must terminate. Iteration without termination is how unattended
loops (see below) burn money. Stop when **any** of these is true:

1. **Gates green AND review clean** — the normal exit. Ship.
2. **`scripts/loop-cohort.py check` exits non-zero.** The script is the
   mechanical side of termination, reading from `state.json` (see
   [`references/state-schema.md`](references/state-schema.md)). It
   fires on iteration cap, token-budget cap, consecutive-error counter,
   pending plan approval (PLAN phase only), and fingerprint stasis
   (REVIEW phase only). The exit message tells you which.
3. **Diff is shrinking but findings aren't** — you're spot-fixing without
   addressing root cause. This is a judgment call, not in `loop-cohort`.
   Stop and rethink the approach (back to PLAN).

If you hit any of these and the work isn't done, the task is bigger than
you thought. Stop, write down what you learned, and re-plan. Never
silently expand scope to make a finding go away.

## Capture what was learned

Before the PR is opened, ask: *what would have made this loop go faster?*
Where the answer goes depends on the *shape* of the learning:

- **Practitioner lessons** — a repeatable pattern that worked, a
  gotcha that bit you, or an antipattern that looked good but rotted.
  Check `docs/CONVENTIONS.md` for a `Knowledge base` section: if
  present, follow what it says for schema, file location, and how the
  session-start hook surfaces these on the next loop. If the section
  isn't there, fall back to a one-line note in the relevant
  `AGENTS.md` (root or per-package) — the next agent still sees it.
- "I had to grep for `<thing>` repeatedly" → add a pointer in
  `docs/architecture/<subsystem>.md`.
- "The test command for this package is unusual" → add it to the package's
  `AGENTS.md`.
- "I made the same wrong assumption twice" → if it's a
  knowledge-base-shaped lesson (a pattern/gotcha/antipattern), follow
  the routing in the first bullet; if it's project-conventions
  context, add a line to the relevant `AGENTS.md` (root or
  per-package) so the next agent doesn't repeat it. If it's a
  vocabulary issue (a term that means something specific here), it
  goes in `docs/guides/reference/` as a glossary entry.
- "This workflow is now the third time I've done it" → propose it as a new
  skill.

This is the part of the loop that makes the *project* smarter, not just the
current PR. Skipping it means the next agent (or you, next month) will
re-derive the same insight.

## Context hygiene

The loop's power — gates, iterate-to-Clean review, fingerprint stasis, the
iteration cap — is orthogonal to the resident tokens that fill the window.
Three levers shed that noise (ordered by savings), each with a no-subagent floor:

- **Reference-reads are the biggest lever** — reading an existing implementation
  just to mirror it is the largest single window draw. Where your agent supports
  delegated subagents, hand that read to a read-only one that returns a distilled
  summary (the "select a subagent matching …" facility REVIEW uses). *Floor:*
  read targeted line ranges, not whole files; never re-read a resident file.
- **Compact at task boundaries** in a multi-loop spec, with a "preserve plan,
  open findings, decisions" hint — safe because `spec.md`, `plan.md`,
  `state.json`, and `docs/backlog.md` are the externalized memory. `/compact` in
  Claude Code; elsewhere your agent's own facility or the fresh-session mode in
  [Unattended loops](#unattended-afk-loops). *Floor:* re-read plan + open findings
  from disk and let the old transcript age out.
- **Narrowest gate during FIX** — the full GATES suite still runs before
  REVIEW/finish, so the floor is re-asserted.

**Reduce, never lossily transform.** Reduce *what you load* — never
summarize-on-read, strip comments, or treat RAG chunks as the truth for an edit:
`Edit` needs exact-byte `old_string` and line numbers anchor findings, so lossy
read-compaction fails *silent*. Skeleton repo-maps are fine for orientation,
never the bytes you edit against.

**Emit less, too.** Your output becomes resident context next turn, so the
levers above apply to what you *write*: don't restate code, files, diffs, or
tool output already in the conversation — cite path and line — and skip
narrating a tool call that succeeded. This is waste reduction, not terseness:
keep the rationale, edge cases, and findings the reader needs.

## Unattended (AFK) loops

The work-loop above is an *in-session* loop: one conversation, state in
working memory plus the repo. Some agents also offer an **unattended
mode** for long-running work — overnight, weekend, AFK: a fresh instance
per iteration, with state living entirely in files (a stable task prompt,
progress notes, git history, AGENTS.md updates) and no human in the seat.
Use your agent's own facility for this; don't hand-roll a loop around the
CLI.

Reach for it only when **all** of these hold:

- The completion criterion is *fully mechanical* — tests pass, a spec
  checklist is fully ticked, a benchmark hits a threshold.
- The task slices into items each small enough for a single context
  window.
- Verification is reliable — flaky tests turn an unattended loop into a
  slot machine.
- You've already run the in-session loop above on a similar task at
  least once. An unattended loop amplifies whatever your conventions
  are; if those aren't tight, it just produces more bad code faster.

It's the wrong tool when "done" is fuzzy or aesthetic, when the task
needs human judgment mid-flight (architectural choices, ambiguous
requirements), or when it touches a sensitive surface (auth, secrets,
data deletion). Set hard caps (iteration, spend) before you start and
review every commit after — unattended doesn't mean *unconsidered*, it
means *pre-considered*.

## Anti-patterns to refuse

- **Skipping PLAN because "the task is small."** If it's truly small, the
  plan is one sentence — write it anyway. The discipline is the point.
- **Declaring an empty declined-pattern register on a non-trivial task.**
  On any non-trivial change something was tempting — a layer, a flag, a
  helper, a defensive wrapper, a tidy abstraction. A register with nothing
  in it means you weren't looking, not that there was nothing to find.
- **Skipping pre-EXECUTE review on a structural change because "the plan
  looks fine".** That's exactly when it doesn't. The cost of catching a
  misplaced module boundary or an unjustified abstraction layer at PLAN
  is a sentence; at REVIEW it's a re-do. The four structural triggers
  (new module boundary, new dependency, new abstraction layer, new
  top-level directory) are the cases where over-engineering is most
  expensive to undo — that's the whole reason the trigger exists.
- **Writing code before deciding how it'll be verified.** "I'll figure out
  the test after" is how features ship with the wrong contract. Every task
  picks its verification mode (TDD / goal-based / manual QA) during PLAN;
  for TDD-mode tasks, the test exists before the production code does.
- **Editing the test until it passes.** This makes the gate green by lying.
  If a test is wrong, fix the test in a separate commit with a justification.
- **Deferring a test because the code fails it.** The inverse of editing
  the test — same lie, opposite direction. If a red test fails because the
  code under test is wrong, fix the code; plausible-sounding rationales
  ("flaky", "out of scope for this PR", "covered elsewhere") are how
  regressions ship. (Beyoncé Rule: if you liked it, you should have put
  a test on it.) If the test is genuinely wrong, fix it in a separate
  commit with the reason; if the test is right and the code can't pass it
  this session, the task isn't done — surface it, don't bury it.
- **Declaring victory because gates pass.** Gates are necessary, not
  sufficient. Review catches what gates can't (missing edge cases, scope
  creep, spec drift).
- **Declaring spec-complete from per-task gates.** When a spec is
  decomposed into N loops, per-task gates verify N contracts — not the
  integrated journey. Before the final loop's DECIDE, run
  `quality-engineer` against the whole spec rather than just the last
  diff, so scenarios the parts test but the whole doesn't get caught.
- **Running an unattended loop on a fresh task instead of the in-session
  loop.** Unattended loops compound bad foundations. Do at least one
  in-session pass first to validate the approach.
- **Looping without capturing learnings.** Every loop that ends without
  updating *some* doc, skill, or note is a loop whose lessons are lost.
