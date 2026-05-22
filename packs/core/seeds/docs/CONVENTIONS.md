# Repository Conventions

This document is the single source of truth for **how we work in this repo**.
It exists so that contributors — human and agent — can answer "where does this
information go?" and "how do I propose a change?" without guessing.

It is deliberately opinionated. If a convention here doesn't fit your case, the
right move is to propose a change via RFC, not to ignore it.

---

## Document hierarchy

We separate documentation by **two axes**:

- **Audience.** Internal (contributors, agents working on the code) vs.
  external (users of the product).
- **Lifecycle.** *Living* (must match current reality), *frozen*
  (immutable history), or *governance* (in-flight proposals).

Mixing these is the most common source of documentation rot. The hierarchy
below assigns every kind of doc to exactly one bucket.

```
                       ┌──── CHARTER.md ────┐
                       │  Mission, scope,    │   The why. Stable for years.
                       │  principles.        │   Living, but rarely changed.
                       │  (one file)         │
                       └──────────┬──────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
   ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
   │  adr/           │   │  rfc/           │   │  specs/         │
   │  Why we chose   │   │  Should we      │   │  What a feature │
   │  X over Y.      │   │  change?        │   │  does + plan.   │
   │                 │   │                 │   │                 │
   │  Frozen history │   │  Governance     │   │  Living during  │
   │  (immutable)    │   │  (open→closed)  │   │  build; frozen  │
   │                 │   │                 │   │  after ship     │
   └─────────────────┘   └─────────────────┘   └─────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                                   │
        Internal current state             External current state
                │                                   │
   ┌────────────▼─────────────┐      ┌──────────────▼─────────────┐
   │  architecture/           │      │  product/                  │
   │  How the code is         │      │  What the product is       │
   │  organized today.        │      │  doing today.              │
   │  Living. For contributors│      │  Living. For maintainers.  │
   │                          │      │  - roadmap.md              │
   │                          │      │  - changelog.md            │
   │                          │      │  - personas.md (optional)  │
   └──────────────────────────┘      └────────────────────────────┘
                                                     │
                                       ┌─────────────▼─────────────┐
                                       │  guides/                   │
                                       │  How users use the product │
                                       │  (Diátaxis: tutorials,     │
                                       │  how-to, reference,        │
                                       │  explanation).             │
                                       │  Living. For users.        │
                                       └────────────────────────────┘
```

The bottom layers cite the upper layers; upper layers do not know about
lower layers. That's the whole point of the hierarchy.

---

## Document lifecycle

Every doc in this repo belongs to one of three lifecycle classes, and the
maintenance rules differ:

| Class | Files | Rule |
| --- | --- | --- |
| **Living** | `CHARTER.md`, `architecture/*`, `product/*`, `guides/*`, active `specs/*` | Must match current reality. Updated in the same PR as any change that affects them. Drift is a bug. |
| **Frozen** | `adr/*`, shipped `specs/*`, accepted/rejected `rfc/*` | Immutable history. Status fields can change (Accepted → Superseded), bodies cannot. |
| **Governance** | open `rfc/*` | In flight. Updated through the RFC process, not direct edits. Closes to Frozen on acceptance/rejection. |

**The most important property of this scheme** is that the frozen layer
gives you decision history *without* the burden of keeping it in sync.
Living docs can be honest about the present because they don't have to
also be a record of how we got here. That's what ADRs are for.

---

## 1. Charter — `docs/CHARTER.md`

**What:** one page. Mission, scope, and principles. The foundational
document. Modeled on the [CNCF charter pattern](https://contribute.cncf.io/maintainers/governance/charter/).

**Lifecycle:** living, but rarely changed. Substantive edits go through an
RFC. Trivial edits (typos, broken links) can be a normal PR.

**What goes here:**

- **Mission.** One sentence. What the project is, in language anyone
  could understand.
- **Scope.** What the project does, and — equally important — what it
  doesn't. The "doesn't" list is what tells contributors and agents when
  a request is out of bounds.
- **Principles.** Five to seven values that resolve ties. Each principle
  has a one-sentence elaboration with a concrete example.

**What does NOT go here:**

- Decision history → ADRs.
- Current product state → `product/`.
- Roles, voting, decision-making → `GOVERNANCE.md`, *if* the project is
  large enough to need one.
- A glossary → `guides/reference/`. Vocabulary is reference material.

**On governance docs:** small and medium projects don't need a separate
`GOVERNANCE.md`. A maintainer or small group operating by consensus is
fine. Add governance documentation when there are roles, decision
procedures, or election processes worth writing down — typically when
the project has external contributors who need clarity on how to gain
authority. Forcing governance ceremony on a project that doesn't need
it produces theater, not clarity.

---

## 2. ADR — Architecture Decision Records — `docs/adr/`

**What:** an immutable record of a decision and the context that produced it.
"We chose Postgres over DynamoDB because <reasons>, accepting <tradeoffs>."

**The key property of an ADR is that it is never edited after acceptance.**
If a decision is reversed or revised, you write a new ADR that supersedes the
old one and update the old one's status to `Superseded by ADR-NNNN`. The old
text stays. This is the difference between an ADR and documentation: ADRs are
history.

**Filename:** `NNNN-kebab-case-title.md`, e.g. `0007-use-postgres-for-primary-store.md`.
Numbers are sequential and never reused.

**Status values:** `Proposed` → `Accepted` → (`Deprecated` | `Superseded by ADR-NNNN`).

**Template:** [`docs/_templates/adr.md`](_templates/adr.md).

**When to write an ADR:**

- You're choosing between two or more reasonable options and the choice will
  be expensive to reverse.
- The reasoning involves tradeoffs a future maintainer (or agent) won't be able
  to reconstruct from the code alone.
- Someone asks "why did we do it this way?" and there's no good answer in
  writing.

**When NOT to write an ADR:**

- The decision is trivial or has only one sensible option ("we use UTF-8").
- The decision is about a single feature's internals — that's a spec, not an ADR.
- You're documenting how something works today — that's `architecture/`.

**Rule of thumb:** if you'd be annoyed to discover the decision was made without
discussion, write an ADR. If you'd shrug, don't.

---

## 3. RFC — Request For Comments — `docs/rfc/`

**What:** a proposal to change something significant — a new feature area, a
new convention, a deprecation, a breaking change to a public interface. RFCs
are *forward-looking governance*; ADRs are *backward-looking record*.

**Lifecycle:**

```
Draft → Open for comment → Final comment period → Accepted | Rejected | Withdrawn
```

Once an RFC is **Accepted**, it produces follow-on artifacts:

- Architectural decisions → one or more ADRs
- Concrete features → specs in `docs/specs/`
- Convention changes → edits to this file (the change itself, not a copy of it)

After follow-ons exist, the RFC's job is done. It stays in the repo as history.

**Filename:** `NNNN-kebab-case-title.md`. Numbers are sequential.

**Template:** [`docs/_templates/rfc.md`](_templates/rfc.md).

**When to open an RFC:**

- The change touches more than one package, or affects external users.
- The change reverses a previous ADR.
- The change adds, removes, or modifies a top-level directory or a convention.
- You expect any reasonable contributor to want a say.

**When NOT to open an RFC:**

- A bug fix, performance improvement, or refactor that preserves behavior —
  just open a PR.
- A new feature that fits cleanly within an existing package and doesn't change
  any interface — write a spec, not an RFC.

---

## 4. Specs and Plans — `docs/specs/<feature>/`

**What:** the precise definition of a single feature, sized to be built in days
or weeks (not months). Each feature gets a directory.

```
docs/specs/<feature>/
├── spec.md      ← contract (objective, boundaries, testing strategy, acceptance criteria)
├── plan.md      ← strategy + construction tests, broken into tasks
└── notes/       ← (optional) research, sketches, rejected approaches
```

**`spec.md` is the contract.** Its four sections — Objective, Boundaries,
Testing Strategy, Acceptance Criteria — together define what "done" means.
The Acceptance Criteria list the observable outcomes that close the spec
(the gate, not an afterthought); the Testing Strategy names the verification
mode for each, and the artifact that verifies it lives where that mode
directs. (Hyrum's Law: with enough callers, every observable behavior of
this contract — including ones the spec doesn't promise — will be depended
on, so the criteria pin what's actually intended.)

**`plan.md` is the implementation strategy.** It enumerates the changes —
"add a `<thing>` to package X, modify `<other thing>` in package Y, write tests
for cases A, B, C". It's the work-breakdown for the spec. It is allowed to
change as you learn things.

**Lifecycle:** specs are **living documents** for the duration of a feature's
implementation. If implementation diverges from the spec, the spec is wrong;
update it in the same PR. After the feature ships, the spec stays as
documentation of the feature's contract — but at that point the *code is the
truth*, and the spec is reference material that should be updated alongside
behavior changes.

**Template:** [`docs/_templates/spec.md`](_templates/spec.md), [`docs/_templates/plan.md`](_templates/plan.md).

**Cite upward, never downward:** a spec links to the ADRs and RFCs that
constrain it. ADRs do not link to specs (specs are too small and short-lived
to be worth citing from an ADR).

### Contract vs. construction tests

Tests are designed *up front, before any implementation*. The contract and
the artifacts that verify it have different shapes and different lifecycles:

- **The contract** lives in `spec.md` — Acceptance Criteria name the
  observable outcomes; Testing Strategy names the verification mode for
  each (TDD / goal-based check / visual / manual QA); Boundaries names the
  rails. Any valid implementation must satisfy every criterion. The
  contract is stable against *implementation* change (that's the whole
  point); it evolves with *spec* (behavioural) change during the spec's
  living phase and freezes when the spec freezes.
- **Construction tests** live in `plan.md`, attached to each task's
  `Tests:` subsection. Units, edge cases, property tests, fixtures — they
  guide the implementer through the build and verify the Acceptance
  Criteria in concrete form. They are *revisable* if one turns out to
  over-specify an internal detail the plan changed.

Within a plan task, the **Tests** subsection comes *before* Approach. Tests
drive implementation, not the other way around. Red-green-refactor: write
the failing test, make it pass, refactor — separate commits for each when
the change is non-trivial.

This is the forcing function that keeps specs honest (every Acceptance
Criterion must be testable in its declared mode) and keeps implementations
honest (you can't drift from the spec if the criteria's verification artifacts are red).

The typical mix follows the test pyramid — roughly 80% fast unit / construction
tests, 15% integration, 5% end-to-end — a target shape, not a quota.

---

## 5. Current-state docs — `docs/architecture/`, `docs/product/`, `docs/guides/`

These three directories are the *living* layer — they describe what is, not
what was decided or what's proposed. Each serves a different audience:

### 5a. `docs/architecture/` — for contributors

How the code is *currently* organized. Not why (ADRs); not what we want
(RFCs); what is.

- `overview.md` — the map of the monorepo. What's in `apps/`, `packages/`,
  `tools/`, and how they relate.
- `<subsystem>.md` — one file per non-trivial subsystem. Describes the
  structure, the entry points, and links to the ADRs that explain why.

**Why separate from ADRs:** ADRs accumulate; current state has to be
reconstructed by reading them all in order. `architecture/` is the
rolled-up snapshot — the answer to "what does this codebase look like
today" without replaying history.

### 5b. `docs/product/` — for maintainers

What the product is *currently* doing. The product-side counterpart to
`architecture/`. Without this layer, you have specs (per-feature contracts)
and ADRs (decision history) but no answer to "what's the product up to,
right now?"

- `roadmap.md` — direction for the next 2-4 quarters. Direction, not
  commitments. Reviewed quarterly. Items that haven't moved in two
  consecutive reviews are a drift signal.
- `changelog.md` — user-visible changes by release, in
  [Keep a Changelog](https://keepachangelog.com/) format. Updated in the
  same PR as any user-visible behavior change.
- `personas.md` (optional) — who we're building for. Add only if it's
  actively used to make decisions; speculative personas rot.

### 5c. `docs/guides/` — for users

The user-facing documentation, organized by [Diátaxis](https://diataxis.fr/).
Four kinds of content, each in its own subdirectory, each serving a
different user need. **Mixing kinds is the most common cause of bad
docs** — see [`guides/README.md`](guides/README.md) for the framework
in detail.

- `tutorials/` — *learning-oriented.* Lessons that take a beginner from
  nothing to a small complete success.
- `how-to/` — *task-oriented.* Recipes for solving specific problems.
- `reference/` — *information-oriented.* Authoritative, dry, complete
  description of interfaces, config, commands.
- `explanation/` — *understanding-oriented.* Why a design works the way
  it does, what concepts mean, how systems fit together.

**Each piece of content belongs in exactly one of these.** When a tutorial
wants to explain *why*, link out to an explanation page. When a how-to
wants to enumerate every option, link out to reference. The "link out"
discipline is the whole framework.

**Specs become user docs when features ship.** A shipped feature's spec
is the team's permanent record of the contract. Its *user-facing*
documentation lands in `guides/reference/` (the authoritative description),
`guides/how-to/` (if users will need recipes for it), and possibly
`guides/explanation/` (if it introduces a concept). The spec workflow is
not done until those are updated.

**Lifecycle for all three:** updated whenever the code or product changes
in a way that makes the description wrong. Keep them short — the goal is
to *orient* a reader, not to duplicate the code or the spec.

---

## Pack source-of-truth split

Bundle content (skills, agents, hooks, commands, hook-wiring, and pack
seeds) lives under `packs/<pack>/`. The split is:

- `packs/<pack>/.apm/` — the upstream for every adapter-projected
  primitive. Sub-directories: `skills/`, `agents/`, `hooks/`,
  `commands/`, `hook-wiring/`.
- `packs/<pack>/seeds/` — the upstream for every seed-projected path
  (the README / template / governance content adopters install).
  Files whose names start with `_` (e.g. `_agents-footer.md`) are
  *composition fragments* — they live in seeds for adopter
  customization but are not projected as standalone files; they're
  consumed by composite recipes.

*Projected* paths under `make build-check`'s gate (Phase 1):
- Adapter-driven primitives: `.claude/skills/<name>/`,
  `.claude/agents/<name>.md`, `.claude/commands/<name>.md`,
  `tools/hooks/<name>.<ext>`, and the `hooks` key of
  `.claude/settings.local.json`.
- Seed-projected paths: `docs/CHARTER.md`, `docs/CONVENTIONS.md`,
  `docs/APPROACH.md`, `docs/_templates/*`, seed READMEs under
  `docs/{architecture,specs,knowledge,product,guides,rfc,adr}/`, and
  the seed content under `packages/`.
- Aggregated: `.claude-plugin/marketplace.json` from every pack's
  `.claude-plugin/plugin.json`.
- Recreated: `CLAUDE.md → AGENTS.md` symlink.

The pipeline regenerates each from its `packs/*/` upstream; direct
edits to any *Projected* path are caught by `make build-check` and
bounced with a message naming the source path and regeneration
command. RFC-0002 is the authority for the source-of-truth split,
including the *Projected* and *Excluded* tables; the same RFC names
`make build-check` as the gate that enforces it. The self-hosting
spec at [`docs/specs/self-hosting/spec.md`](specs/self-hosting/spec.md)
records the Phase-1 vs Phase-2 scoping (AGENTS.md body+footer
composition and LF/mode/lstat comparison-rule strengthening remain
Phase 2).

The muscle memory: to change a *Projected* path's content, edit its
upstream under `packs/<pack>/.apm/` or `packs/<pack>/seeds/`, then run
`make build-self` (with `FORCE=1` if the working tree is dirty),
commit, push. The gate is the contract; the source-of-truth split is
the convention.

---

## Commits

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `chore`.
**Scope:** the package or area touched (`packages/foo`, `docs`, `ci`).

**Footer references:** if the commit implements a spec, end with `Spec: docs/specs/<feature>/spec.md`. If it follows from an ADR or RFC, cite it the same way.

---

## Pull requests

A PR description should answer four questions in this order:

1. **What does this change?** (Plain English. Two sentences.)
2. **Why?** (Link to the spec, ADR, RFC, or issue.)
3. **How do I verify it?** (Specific commands, manual steps, or screenshots.)
4. **What did you not change that you considered?** (The dog that didn't bark.
   This catches more bugs than any other section.)

Aim for under ~100 lines of diff. PRs that grow beyond ~400 lines should be
split unless the change is genuinely atomic (e.g. a generated file, a single
rename across many call-sites).

CI must be green. Specs must match implementation. Public-interface changes
must be noted in `CHANGELOG.md`.

---

## How we do non-trivial work

For anything beyond a one-line edit, follow the **plan → execute → verify →
review → iterate** loop. The mechanics are in the
[`work-loop`](../.claude/skills/work-loop/SKILL.md) skill; this section is
the why.

**Why a loop, not a single pass.** LLM self-assessment is unreliable: agents
declare victory when they *feel* done. Mechanical gates (lint, typecheck,
tests) plus an adversarial review pass replace "feel" with verifiable
termination. The loop keeps going until both kinds of check are satisfied —
or until it hits a hard cap.

**Why think before acting.** The cost of a wrong start is higher than the
cost of thinking. For high-stakes changes (architectural choices, multi-file
refactors, anything touching shared infrastructure), use your agent's
extended-thinking facility — it catches the wrong assumption *before* it
becomes 14 commits of wrong code. For routine work, skip the ceremony; the
discipline is "match thinking depth to stakes," not "always think hardest."

**Why iterate, not retry-from-scratch.** Most loops converge: gates fail,
review surfaces a finding, the next pass fixes it. Restart-from-scratch
loses the planning context. We do it the other way only when fresh context
is the *point* — which is what the Ralph harness in [`tools/ralph.sh`](../tools/ralph.sh)
is for.

**Why a hard iteration cap.** Without one, you're hoping. The cap lives as
data in `state.json` (see below) and is enforced by `tools/check-done.py`;
if you hit it, the task is bigger than you thought — stop, re-plan, or
split.

**Why capture learnings.** A loop that finishes without updating *some*
doc, skill, or note has wasted what it learned. The next agent (Ralph or
human) will pay for it again. The work-loop skill enumerates where each
kind of learning belongs.

### Work-loop state

A spec-driven loop carries a small amount of session-scoped state — how
many iterations have run, what budget is left, what findings the last
review surfaced. Putting that in prose ("we cap at 5 iterations…") leaves
it un-enforceable. Putting it on disk as data lets a tiny script gate
each phase. That script is [`tools/check-done.py`](../tools/check-done.py);
the data lives at `docs/specs/<feature>/state.json`, and the schema lives
at [`docs/_templates/state.json`](_templates/state.json).

**Fields:**

| Field | Meaning |
|---|---|
| `feature` | spec slug (informational) |
| `iteration_count` / `max_iterations` | how many in-session loops have run / hard cap |
| `token_budget_used_pct` / `token_budget_cap_pct` | session token budget — **advisory in Phase 1**; the kill criterion fires only if the orchestrator populates `_used_pct`, which is wired up in a later phase |
| `consecutive_same_error_count` / `consecutive_same_error_threshold` | gate-error stuck-loop counter / cap. **Advisory in Phase 1** — the SKILL doesn't yet prescribe when to increment `_count`. Threshold lives in data so a project can tune it. |
| `plan_review_status` | `pending` until the spec-mode adversarial review clears, then `approved`. Enforced as a gate on **all phases** (not just `--phase plan`) — `implement` and `review` also reject a `pending` state. |
| `last_commit_sha` | latest commit produced by the loop (informational; advisory in Phase 1) |
| `finding_fingerprints` / `previous_finding_fingerprints` | hashes of reviewer findings, rotated each REVIEW iteration; used to detect circling. Algorithm pinned in the work-loop SKILL §REVIEW. |
| `worktrees` | one entry per `implementer` subagent dispatched in the current session's supervisor pass: `{task_id, branch, path, status, report_path}` where status is `in-progress` / `ready` / `blocked` / `failed` and `report_path` points at the implementer's markdown report under `docs/specs/<feature>/notes/`. Report files are gitignored (`docs/specs/**/notes/implementer-*.md`) — session-scratch like `state.json`, not history. Entries persist with their terminal status for the rest of the loop so a future reader can reconstruct what each task did. Empty in single-agent loops. See [§ Supervisor mode](#supervisor-mode). |

**Exit contract.** `check-done.py` exits 0 when the phase is satisfied
and non-zero when it isn't, with a one-line reason on stderr. Treat
non-zero as "stop and surface" — with one deliberate exception: the
SKILL's PLAN-init step calls the script with `--phase plan` *expecting*
exit 1 with `plan not approved`. That exit-1 is the cue to run the
spec-mode reviewer, not a real stop. Any other non-zero exit terminates
the loop.

**Lifecycle.** `state.json` is **per-session scratch**, not history. The
file is gitignored (`docs/specs/**/state.json` in
[`.gitignore`](../.gitignore)); the SKILL initializes it from the
template at PLAN start. Across sessions, a fresh run re-initializes —
intentionally; a new session deserves a fresh budget.

**Atomic writes.** The orchestrator updates `state.json` mid-iteration;
`check-done.py` reads it between phases. Always write atomically
(tmp-file + `os.replace`, or shell `mv`) so a partial-write doesn't
present as malformed JSON and falsely stop the loop.

**Changing the cap.** Editing `docs/_templates/state.json` changes the
*starting point* for any **newly-initialized** spec. To change the cap
for a spec that's already running, edit that spec's own (gitignored)
`docs/specs/<feature>/state.json` — the template edit doesn't propagate
backward. The numbers move with the data, not the SKILL prose.

### Model selection

Every subagent file declares `model:` in its frontmatter explicitly. The
[`lint-agent-artifacts.sh`](../tools/lint-agent-artifacts.sh) linter
enforces this. Reasoning behind each current choice:

| Subagent | Model | Why |
|---|---|---|
| `adversarial-reviewer` | `opus` | Adversarial judgment; stakes are correctness. Output drives a hard gate. |
| `security-reviewer` | `opus` | Threat-model reasoning; stakes are security. |
| `quality-engineer` | `opus` | Maintenance lens; spec-level coverage pass. Reconsider per observation. |
| `implementer` | `sonnet` | One narrow plan task per dispatch; gates rerun in the primary; supervisor judges merge readiness. Cost beats capability here. |

Changing a subagent's model is a behaviour change, not a configuration
tweak — note the change in the PR that makes it, with a one-line
justification. If the change is reversing a previous choice in a way a
future maintainer would ask "why", surface it in the PR description.

### Supervisor mode

When a plan has multiple tasks declaring `Depends on: none`, the
work-loop enters **supervisor mode**: one primary orchestrator
dispatches `implementer` subagents in parallel, each working in its own
git worktree, then merges the results back and runs gates in the
primary. The mechanics live in the
[`work-loop` skill](../.claude/skills/work-loop/SKILL.md) §EXECUTE; this
section is the why and the boundary.

**Why a separate mode instead of a separate skill.** The trigger is
structural (the plan's shape), not a choice the user makes. Branching
inside `work-loop` means contributors never pick the wrong skill, and
the 80% overlap with single-agent flow stays single-sourced.

**Why an implementer subagent, not a recursive work-loop.** The
implementer's job is narrow — build one task, run gates, report.
Reviewing, dispatch decisions, and merge belong to the supervisor. A
recursive work-loop would let an implementer spawn its own
implementers; that's nested coordination overhead with no clear win.
Keep the tree two levels deep: supervisor → leaf implementers.

**Worktrees as the coordination primitive.** Each independent task gets
`.worktrees/<task-id>/` checked out on its own branch
(`<base-branch>-<task-id>`). Worktrees are git-native, support parallel
checkout of the same repo, and avoid lockfile contention. The directory
is gitignored ([`.gitignore`](../.gitignore)); branches live in git
history for traceability.

**Merge discipline.** The supervisor merges with `git merge --no-ff
<base>-<task-id>` into the primary branch, **sequentially in task-id
order**. The SKILL has the procedural form (including how to order
non-numeric IDs). If a sequential merge conflicts, the tasks weren't
actually independent — the plan was wrong. Surface that as a
PLAN-level escalation, not a `git mergetool` session.

**Gates run in the primary, not the worktree.** Each implementer runs
gates inside its worktree and reports the result, but those results are
**advisory**. The supervisor reruns lint / typecheck / tests against
the merged state — that's the only signal that counts.

**Escalating implementer failures.** If an implementer reports
`blocked` or `failed`, the supervisor surfaces the failure list to a
human and returns to PLAN. It does **not** redispatch the same
implementer on the same task — the assumption that produced the
failure is what needs revising, not the attempt.

**Known limitation.** This section's procedure has been validated by
prose walk-through, not by an executed end-to-end dry-run. Any change
to **pre-flight (SKILL §EXECUTE step 0)**, **worktree creation (step 1)**,
**report persistence ordering (step 3)**, **merge order (step 5)**,
**cleanup recovery (step 6)**, or the **`state.json` `worktrees`
schema** must perform an actual `git worktree add` + parallel-dispatch
round against a throwaway spec before merging — read-only walk-through
is not sufficient for those surfaces.

### Knowledge base

The repo accumulates practitioner-level lessons in
`docs/knowledge/patterns.jsonl`: patterns ("when you touch X, also
remember Y"), gotchas ("the auth middleware caches tokens for 15
minutes"), and antipatterns ("don't mock the database in integration
tests"). One JSON object per line, scoped to a file glob. The schema
and curation conventions live in
[`docs/knowledge/README.md`](knowledge/README.md).

**Why a separate bucket.** ADRs answer *why we decided X*;
`architecture/` describes *current structure*; `guides/` is for
*users*. Knowledge entries are practitioner residue — the things you
learn by building, not by deciding or documenting. They earn a home
because they're scoped to globs (an agent priming for `packages/auth`
should see the auth gotchas, not every lesson the repo ever learned)
and append-only (a lesson that stops being true gets a *new* entry
citing the old one, not an edit — which keeps history honest).

**How agents see it.** `tools/hooks/session-start.sh` reads the file
at session open and prints the entries — optionally filtered by a
path or narrower glob. Matching uses Python's `fnmatch` with the
caller's `--scope` value as the *path* argument and the entry's
stored glob as the *pattern*, so an agent working in
`packages/auth/server.ts` gets entries scoped to `packages/auth/**`
plus any repo-wide `*` entries. The work-loop SKILL's
[`Capture what was learned`](../.claude/skills/work-loop/SKILL.md#capture-what-was-learned)
section points contributors at this file as the destination for
pattern/gotcha/antipattern-shaped learnings; other shapes still go
where they already belong (AGENTS.md, skill bodies, architecture/).

### Enforcement (the triplet)

Three layered mechanisms enforce the project's discipline. They are
named together so contributors and reviewers can refer to "the
enforcement triplet" and mean the same three things:

| Layer | Mechanism | What it gates |
|---|---|---|
| Caps | [`tools/check-done.py`](../tools/check-done.py) | Iteration cap, token budget, plan approval, fingerprint stasis (see [§ Work-loop state](#work-loop-state)). |
| Artifacts | `tools/lint-agents-md.sh`, `lint-agent-artifacts.sh`, `lint-skill-deps.sh`, `lint-knowledge.sh` | Shape, manifest, and content hygiene for every `.claude/`, `AGENTS.md`, and `docs/knowledge/` artifact. |
| Aggregation | [`tools/hooks/pre-pr.sh`](../tools/hooks/pre-pr.sh) | Runs caps + artifact linters together before a PR opens. CI mirrors this — `.github/workflows/docs.yml` has a job per enforcement layer, including a `hooks` job that runs the aggregator end-to-end. Keep the local hook green and CI follows. |

The triplet is **Shift Left**: catch problems as early as possible,
locally before CI, at PLAN before EXECUTE. The
[pre-EXECUTE adversarial review](../.claude/skills/work-loop/SKILL.md) in
the work-loop skill is the same pattern at a different layer — moving
review left from after code is written to before it is.

`pre-pr.sh` is the hook downstream consumers wire into their tool's
lifecycle (see [`tools/hooks/README.md`](../tools/hooks/README.md)).
The template ships the script; it does **not** ship a committed
`.claude/settings.json` — wiring is consumer-specific.

### When to reach for Ralph

The same loop can run unattended — fresh Claude Code session per
iteration, state in files only. That's a [Ralph loop](../tools/RALPH.md).
Use it when *all* of these hold: completion is mechanical, work slices
into context-window-sized items, verification is reliable, and you've
already validated the approach in-session. Read [`tools/RALPH.md`](../tools/RALPH.md)
before running. Ralph is a sharp tool — useful, narrow, and not the answer
to most work.



Skills are workflows agents invoke for repeating tasks: scaffolding a package,
opening an ADR, running a release. They live in `.claude/skills/<name>/SKILL.md`.

Add a skill when you've done the same multi-step thing three times. Don't add
one speculatively — speculative skills bloat context and degrade adherence.

The skill index is at [`.claude/skills/README.md`](../.claude/skills/README.md).

---

## Scaling profiles — how this template adapts to different repo sizes

This template is designed for **single applications, components,
microservices, and medium-sized platforms or engines** — repos with
roughly 1 to 50 contributors. It is **not** designed for sprawling
monorepos with hundreds of contributors and SIG-style governance; if
that's your context, look at Kubernetes' or CNCF's models instead.

The structure stays the same at every supported size. What changes is
which folders you actively populate and how much ceremony each kind of
doc carries. **An empty folder is not a problem** — it's a placeholder
for content that will arrive when it's needed.

### Profile A — Microservice / single component (1-3 contributors)

The minimum viable set. Many of the template's folders sit empty until
something forces them to fill.

| Keep | Delete or leave empty |
| --- | --- |
| `AGENTS.md`, `CLAUDE.md` (symlink) | `packages/`, `apps/` (no monorepo split) |
| `docs/CHARTER.md` (a few lines is fine) | `rfc/` (almost never fires at this size) |
| `docs/CONVENTIONS.md` (trim aggressively) | `docs/architecture/` (the README is enough) |
| `docs/adr/` (write when you make a real tradeoff) | `docs/product/personas.md` |
| `docs/specs/` (one spec at a time, or none) | Per-package `AGENTS.md` (no packages) |
| `docs/product/changelog.md` | `.claude/agents/adversarial-reviewer.md` (overhead at this size) |
| `docs/guides/reference/` (API/config docs) | Other Diátaxis buckets — fill as needed |
| `.claude/skills/work-loop/` | |

**Rule of thumb:** if your README + an OpenAPI/schema file would have
been enough, you're at this profile. The template gives you ADRs and
specs *for when* a decision or feature gets non-trivial — not as
mandatory ceremony.

### Profile B — Single library or app (4-10 contributors)

Most folders start carrying content.

- All of Profile A, plus:
- `docs/architecture/overview.md` becomes useful (one file).
- `docs/specs/` typically has 1-3 active features at a time.
- `docs/guides/` grows: at least `reference/` and probably one
  `tutorials/` entry (a quickstart) and a few `how-to/` recipes.
- ADRs accumulate slowly — maybe 5-15 over the project's first year.
- `rfc/` may still be unused; PRs are enough for most decisions.
- `adversarial-reviewer` subagent is worth using. `security-reviewer` and
  `quality-engineer` are worth reaching for when a PR warrants them — see
  [`AGENTS.md § Specialist subagents`](../AGENTS.md#specialist-subagents).

### Profile C — Medium platform / engine (10-50 contributors)

This is the design target — everything in the template is in active use.

- All of Profile B, plus:
- `apps/` and/or `packages/` populated, each with its own `AGENTS.md`.
- `rfc/` actively used for cross-cutting changes.
- `docs/architecture/` contains an overview plus per-subsystem files.
- `docs/guides/` has substantive content in all four Diátaxis buckets.
- `docs/product/roadmap.md` reviewed quarterly with real stakes.
- ADRs are routine — likely 30+ in the project's history.
- Multiple specs in flight; spec/plan/review discipline carries weight.

### Multi-agent shape by profile

The mechanisms — supervisor mode, parallel reviewer dispatch, the
knowledge base — are defined in their own sections above. The mapping
below says *which of them you actually use* at each profile, so a
template adopter knows when to wire each one up.

- **Profile A** — single-agent work-loop. Supervisor mode is available
  but rarely triggers; most plans at this size have sequential
  `Depends on:` chains, and the parallel-dispatch payoff doesn't beat
  the coordination overhead. Specialist reviewers are usually skipped,
  and `adversarial-reviewer` itself is optional at this size.
- **Profile B** — [supervisor mode](#supervisor-mode) earns its keep
  when a plan produces two or more `Depends on: none` tasks. Reviewer
  fan-out follows the
  [parallel-dispatch discipline](../.claude/skills/work-loop/SKILL.md#parallel-dispatch-discipline)
  in the work-loop skill: one tool-call message, one Agent use per
  reviewer, barrier-wait, merge in the orchestrator's context.
- **Profile C** — same as B, plus the [knowledge base](#knowledge-base)
  is actively populated (`docs/knowledge/patterns.jsonl`) and the
  `session-start` hook is wired in the consumer's `.claude/settings.json`
  per [`tools/hooks/README.md`](../tools/hooks/README.md). The template
  ships the script, not the wiring.

### Above Profile C

If your repo is heading past ~50 active contributors with multiple teams
working in parallel, the template starts to underspecify what you need.
At that scale you typically need:

- A `GOVERNANCE.md` describing roles, decision processes, and how
  authority is granted.
- A formal RFC process with comment periods and final-comment-period
  rules (Rust's [RFC process](https://github.com/rust-lang/rfcs) is the
  reference).
- Sub-team boundaries (CNCF SIGs, Kubernetes-style).
- CODEOWNERS-driven review routing.

Adopt those when the friction of *not* having them exceeds the friction
of adopting them — not as a precaution.

### Anti-patterns at every size

- **Bootstrapping at Profile C when you're at Profile A.** Empty
  ceremony degrades into ignored ceremony. Start at the right profile
  and grow into the next one when you actually need it.
- **Skipping Profile A entirely because "we'll be a platform someday."**
  You'll get there faster if early decisions are recorded honestly than
  if they're hidden inside a structure too big for the team to maintain.
---

## Common rationalizations

Four lies an agent tells itself mid-loop, paired with the rebuttal that
already lives in this repo. These are the in-loop counterparts to the
[Excuses we don't accept](../AGENTS.md#excuses-we-dont-accept) table in
`AGENTS.md`, which fires *before* the work-loop loads.

| The lie | The rebuttal |
| --- | --- |
| "We'll update the spec after the PR." | Spec drift is a bug, not follow-up work — update spec and code in the same PR. See [`AGENTS.md` § How we work](../AGENTS.md#how-we-work) and the spec lifecycle rule in § 4 above. |
| "I'll verify this manually, just this once." | Verification mode — TDD, goal-based, or manual QA — is declared in the plan task, not improvised at the keyboard. If manual QA is the right mode, write it down; if it isn't, pick TDD or a goal-based check. See the PLAN phase in [`work-loop`](../.claude/skills/work-loop/SKILL.md). |
| "I can fix this while I'm here." | Out-of-scope changes need a separate PR or an explicit note in the plan. Scope creep is the most common cause of failed adversarial review. See [`AGENTS.md` § Keeping changes minimal](../AGENTS.md#keeping-changes-minimal). |
| "This decision doesn't need an ADR — it's obvious." | If you're making it, it isn't obvious to the next person. Writing an ADR now costs less than someone re-litigating the decision in six months. See § 2 above and the `new-adr` skill. |

---

## When this file is wrong

If a convention here is causing friction, **say so in an RFC**. Don't quietly
deviate. The whole point of writing this down is that the rules are visible and
contestable.
