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
├── spec.md      ← what this feature is, for users; the contract
├── plan.md      ← how we'll build it, broken into tasks
├── tasks.md     ← (optional) checklist if plan.md is too dense
└── notes/       ← (optional) research, sketches, rejected approaches
```

**`spec.md` is the contract.** It defines the externally observable behavior:
inputs, outputs, error cases, edge cases, non-goals. It is the source of truth
for what "done" means. Tests should be derivable from it.

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
refactors, anything touching shared infrastructure), use Plan Mode and
extended thinking — they catch the wrong assumption *before* it becomes
14 commits of wrong code. For routine work, skip the ceremony; the
discipline is "match thinking depth to stakes," not "always think hardest."

**Why iterate, not retry-from-scratch.** Most loops converge: gates fail,
review surfaces a finding, the next pass fixes it. Restart-from-scratch
loses the planning context. We do it the other way only when fresh context
is the *point* — which is what the Ralph harness in [`tools/ralph.sh`](../tools/ralph.sh)
is for.

**Why a hard iteration cap.** Without one, you're hoping. Five in-session
iterations is the default; if you hit it, the task is bigger than you
thought. Stop, re-plan, or split.

**Why capture learnings.** A loop that finishes without updating *some*
doc, skill, or note has wasted what it learned. The next agent (Ralph or
human) will pay for it again. The work-loop skill enumerates where each
kind of learning belongs.

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
| `docs/product/changelog.md` | `.claude/agents/spec-reviewer.md` (overhead at this size) |
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
- `spec-reviewer` subagent is worth using.

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

## When this file is wrong

If a convention here is causing friction, **say so in an RFC**. Don't quietly
deviate. The whole point of writing this down is that the rules are visible and
contestable.
