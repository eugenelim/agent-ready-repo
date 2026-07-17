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
   │  - overview.md (map;     │      │  - roadmap.md              │
   │    descriptive)          │      │  - briefs/<slug>.md        │
   │  - reference.md (golden  │      │  - changelog.md            │
   │    path; normative)      │      │  - personas.md (optional)  │
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

Inside `architecture/`, the two docs play opposite roles. `overview.md` is
**descriptive** — the map of how the code is organized today, read to find
things. `reference.md` is **normative** — the golden path (stack, building
blocks, component stereotypes, cross-cutting standards) that new work conforms
to, the target a feature's low-level design steers by. The map tells you where
things are; the golden path tells you how new things should be shaped. A thin
repo has only the map; the golden path appears once there are real architecture
decisions to hold work to.

The bottom layers cite the upper layers; upper layers do not know about
lower layers. That's the whole point of the hierarchy.

**The brief altitude.** A *brief* (`product/briefs/<slug>.md`) sits between
the roadmap and the specs — it is where an externally-authored, multi-feature
product handoff (a PRD, a solution packet) lands when it's too big to be one
spec. The altitude reads `roadmap → brief → spec → AC`: the roadmap names
themes, a brief records one received outcome and the specs that deliver it, a
spec is the engineering contract for one feature, and an acceptance criterion
is the testable unit. A brief owns only **this repo's slice**; an optional
`Epic:` field points up to an external coordinator when the work spans repos.
A derived spec links back to its brief with a `Brief:` field (see § 4), and
the brief's coverage map rolls up automatically from those specs' `Status:`
fields. Use the `receive-brief` skill to receive, decompose, and execute a
brief; it never mandates a schema.

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

**Status values:** `Proposed` → `Accepted` or `Rejected`. An `Accepted` ADR may
later become `Deprecated` (the decision no longer applies and nothing replaces
it) or `Superseded by ADR-NNNN` (a specific later ADR replaces it). A `Rejected`
ADR is kept as a record, never deleted.

**Template:** `assets/adr.md` in the `new-adr` skill that creates ADRs from it.

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
Draft → Open → Final Comment Period → Accepted | Rejected | Withdrawn
```

**Optional `Experimental` status.** An RFC that proposes running an
experiment — using the optional `Experiment / validation` section of the
`new-rfc` template — may sit in `Experimental` while the trial runs and
results are pending, instead of being forced to a premature Accept or Reject.
Results live in a linked spike note (or a follow-up RFC / superseding ADR),
not the RFC body; when they land, the RFC moves to `Accepted | Rejected |
Withdrawn`. An `Experimental` RFC is still in-flight (Governance class, not
Frozen). Use it only when an experiment is genuinely running.

Once an RFC is **Accepted**, it produces follow-on artifacts:

- Architectural decisions → one or more ADRs
- Concrete features → specs in `docs/specs/`
- Convention changes → edits to this file (the change itself, not a copy of it)

After follow-ons exist, the RFC's job is done. It stays in the repo as history.

**Optional `NNNN-notes/` companion.** An RFC may carry a sibling
`docs/rfc/NNNN-notes/` folder for promoted research and supporting material —
sketches, evidence, a distilled research brief lifted from a sustained
investigation — mirroring the optional `notes/` folder a spec carries (§4). It
is optional and informal; the RFC body remains the contract.

**Filename:** `NNNN-kebab-case-title.md`. Numbers are sequential.

**Template:** `assets/rfc.md` in the `new-rfc` skill that creates RFCs from it.

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

**Template:** `assets/spec.md` and `assets/plan.md` in the `new-spec` skill that creates the pair.

**Cite upward, never downward:** a spec links to the ADRs and RFCs that
constrain it. ADRs do not link to specs (specs are too small and short-lived
to be worth citing from an ADR).

### Spec metadata contract

A spec's *metadata* — the few machine-checkable fields below — is pinned so the
new-spec template, the `adversarial-reviewer` drift check, and the work-loop's
finish-time checklist all measure against one source. This contract is
**metadata-only**: it governs the shape of status, criteria, and deferrals, not
whether the spec matches the code. Detecting *semantic* spec↔code drift remains
the `adversarial-reviewer`'s judgment call (its "Spec drift" check), not a
mechanical rule.

- **Status vocabulary.** A spec's `- **Status:**` field is exactly one of
  `Draft | Approved | Implementing | Shipped | Archived`. (Plans carry their own
  vocabulary, `Drafting | Executing | Done` — a separate field, separate set.)
- **Acceptance Criteria notation.** Each criterion is a GitHub task-list item:
  `- [ ]` when open, `- [x]` when met. "Done" is the checklist, not an opinion.
- **Deferral token.** A criterion that ships *unmet on purpose* is not left
  unchecked and silent — it carries an inline `(deferred: <anchor>)` marker whose
  `<anchor>` resolves to a heading in `docs/backlog.md`, the durable register of
  open work. Form: `- [ ] <outcome> (deferred: <backlog-anchor>)`. A deferral
  recorded only in a PR comment rots; the register is version-controlled and
  greppable.
- **Brief back-link (optional).** A spec derived from a product brief carries a
  `- **Brief:**` header naming that brief (`product/briefs/<slug>.md`). It
  records *product provenance* and is distinct from `Constrained by:` (which
  cites the ADRs/RFCs that govern the spec). The field is additive and optional
  — a spec authored directly omits it and stays valid. The brief's coverage map
  rolls up from these back-links automatically; never hand-write a spec's status
  into the brief.
- **Discovery up-edge (optional).** A spec descended from an upstream
  product-discovery artifact (a decision brief or intent produced by an upstream
  discovery process) carries a `- **Discovery:**` header naming that artifact by
  its stable id. Like `Brief:` it records *upstream provenance* — the producer
  edge a traceability check walks from the discovery side into the spec — and is
  additive and optional: a spec authored directly omits it (or `none`) and stays
  valid. The discovery-side producer artifacts themselves (intents, screens,
  journeys, blueprints) carry a **rendered bold-body field marker** naming their
  kind — `- **Type:** screen-brief` for a screen brief, the container-embedded
  `- **Action:** <slug>` / `- **Service:** <slug>` for journey/blueprint entries,
  and `- **Kind:** outcome|opportunity` / `- **Level:** capability` for
  intent-ladder rungs — so a traceability check recognizes them **by marker, not
  path** (the lint matches the rendered `**Label:**` field, not a YAML frontmatter
  key). (`frame-domain` additionally stamps a document-level frontmatter
  `type: domain-framing` / `type: scope-boundary`; that is a discover-by-marker
  *anchor*, not one of the chain recognizers' fields.) This is a **format**
  convention — the field grammar — not doctrine about *when* discovery runs.
- **Story trace (optional).** When the brief carries user stories (Shape B), an
  acceptance criterion that satisfies a story appends a `Satisfies: US-n` marker
  so coverage is story-granular. Optional — omit it for a no-stories brief or a
  directly-authored spec.
- **Shape (optional).** A spec may carry a `- **Shape:**` header — one of
  `ui | service | data | integration | mixed` — naming the *kind* of work. It
  selects which `## Design (LLD)` sub-sections the plan scaffolds, so a narrower
  shape keeps the plan thin. Stack-neutral: it names the kind, never a framework.
  Additive and optional — a spec omits it (or sets `mixed`) and stays valid.

### Low-level design lives in the plan

The plan — not the spec — is the home for low-level design. `spec.md` stays the
contract (objective, boundaries, testing strategy, acceptance criteria); the
*how* lives in the plan's optional, shape-pruned `## Design (LLD)` section, built
from stack-neutral category headings:

- **Nine design categories** scaffold as `## Design (LLD)` sub-headings — design
  decisions; data & schema; interfaces & contracts; component / module
  decomposition; state & control flow; behavior & rules; failure, edge cases &
  resilience; quality attributes (NFRs); dependencies & integration. The plan
  scaffolds only the ones the spec's `Shape:` selects; a one-file change keeps
  the section thin or empty.
- **The tenth category — rollout & deployment — is not a Design sub-heading.** It
  is realized by the plan's expanded `## Rollout` (infrastructure, external-system
  integration, deployment sequencing). Cross-link it; never duplicate it.
- **Each sub-section traces to the acceptance criteria it satisfies and the
  contracts it implements** — the design is always anchored to something
  verifiable. No acceptance criterion lives in the design; the spec keeps the
  contract. A user-visible UI state (phrased state / trigger / outcome) and an
  NFR with a pass/fail bar each rise to the spec as acceptance criteria; the
  per-screen and per-NFR design itself sits in the plan.
- **The categories are stack-neutral; the stack is derived, never baked.** The
  headings are universal; the prose under them names a concrete stack, derived
  from a reference-architecture document (`docs/architecture/reference.md`) when
  one is present — the design conforms to it, referencing its components and
  standards by name — and degrading to detection from the established repo
  (lockfiles, build files, imports) or elicitation when it is absent.

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

**Stub → EXECUTE handoff.** For TDD-mode tasks, the construction test is
materialised *at PLAN* as a compilable, validated red **stub** — as much of the
real failing test as the AC and contract honestly determine, never less than a
compiling assertion on the contract surface, never a bare `TODO`. The stub
carries a `# STUB: AC<n>` (or `// STUB: AC<n>`) comment in the test and a
`stub: true` field in the task's `Tests:` subsection, so EXECUTE's red step
starts from the pre-written stub rather than re-deriving it. A stub that won't
compile is the mechanical signal an AC is under-specified, caught at PLAN
instead of mid-implementation. The full procedure lives in the `work-loop`
skill's `references/tdd-stubs.md`.

This is the forcing function that keeps specs honest (every Acceptance
Criterion must be testable in its declared mode) and keeps implementations
honest (you can't drift from the spec if the criteria's verification artifacts are red).

The typical mix follows the test pyramid — roughly 80% fast unit / construction
tests, 15% integration, 5% end-to-end — a target shape, not a quota.

### Contracts — `contracts/<type>/`

API contracts are **long-lived, repo-level, single-source-of-truth** artifacts —
not per-feature files. They live at the repo root, grouped by contract type:

```
contracts/
  openapi/      # REST — .yaml
  asyncapi/     # event-driven APIs — descriptor + standalone event-payload schemas
  proto/        # gRPC / protobuf — buf-style versioned package dirs
  graphql/      # GraphQL SDL
  jsonschema/   # standalone JSON Schema
  jsonrpc/      # JSON-RPC service descriptors
  mcp/          # Model Context Protocol tool/resource schemas
```

This is distinct from `docs/contracts/` (adapter schemas) and from the
`contracts` *pack* of authoring skills; the API tree is unambiguously repo-root
`contracts/`.

**Naming.** One contract per logical API/service/domain, kebab-case by domain
(`contracts/openapi/orders.yaml`). Proto follows buf's convention — versioned
package directories (`contracts/proto/payments/v1/payments.proto`) and
`lower_snake_case.proto` filenames.

**Versioning.** Minor/patch track in-contract (`info.version`) plus git history;
a breaking **major** that must be served alongside the old one gets a parallel
file/dir (`orders.v2.yaml`, `…/v2/`).

**Bidirectional traceability.** A contract and the specs that define or modify it
point at each other:

- **Forward (spec → contract):** the spec header `- **Contract:**` names the
  contract file(s) the spec defines or touches.
- **Backward (contract → spec):** the contract carries an `x-spec` vendor
  extension naming its defining/modifying specs (OpenAPI/AsyncAPI:
  `x-spec: [docs/specs/orders/]`); for extensionless formats (proto, graphql) a
  top-level `contracts/REGISTRY.md` map is the fallback.

Both sides are repo-scope artifacts, so forward/backward agreement is checkable
by an in-repo lint — the **traceability invariant** in `lint-spec-status.py`
(warn-only, and a no-op where no `contracts/` tree exists). Contract ↔ spec
Acceptance Criteria ↔ implementation must agree; changing one without the others
is drift. A contract is authored through its type's skill when one is installed
(so the active API standard's compatibility rules catch breaking changes);
absent a skill, it is hand-authored into the same conventional location.

> The repo-root `contracts/` directory is a new top-level directory; proposing
> it, and any substantive change to this convention, routes through your RFC
> process (see § 3).

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
- `briefs/<slug>.md` (optional) — a received, externally-authored
  multi-feature product brief and its auto-rolled-up coverage map. Created by
  the `receive-brief` skill; one file per brief. See the brief altitude under
  *Document hierarchy*.
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

*Projected* paths under `make build-check`'s gate:
- Adapter-driven primitives: `.claude/skills/<name>/`,
  `.claude/agents/<name>.md`, `.claude/commands/<name>.md`,
  `tools/hooks/<name>.<ext>`, and the `hooks` key of
  `.claude/settings.local.json`.
- Seed-projected paths: `docs/CONVENTIONS.md`. (Other seed-projected
  paths from earlier phases — `docs/CHARTER.md`, the seed READMEs
  under `docs/<area>/`, and `packages/_example/` — were reclassified
  as *Manual* with placeholder seeds; adopters receive the placeholder
  on first install via brownfield rules and own their on-disk content
  thereafter.)
- Aggregated: `.claude-plugin/marketplace.json` from every pack's
  `.claude-plugin/plugin.json`.
- Recreated: `CLAUDE.md → AGENTS.md` symlink.

The pipeline regenerates each from its `packs/*/` upstream; direct
edits to any *Projected* path are caught by `make build-check` and
bounced with a message naming the source path and regeneration
command. The pack source-of-truth split is the catalogue's
load-bearing convention; CI's drift gate enforces it.

The muscle memory: to change a *Projected* path's content, edit its
upstream under `packs/<pack>/.apm/` or `packs/<pack>/seeds/`, then run
`make build-self` (with `FORCE=1` if the working tree is dirty),
commit, push. The gate is the contract; the source-of-truth split is
the convention.

### Install scope is per-pack

Each pack declares its install **scope** — `repo` (project-local), `user`
(shared across every repo the adopter opens), or both — in
`pack.toml`'s `[pack.install]` table. The pack author picks the
dimension; adopters can override within the publisher's declared set
via `--scope`. The default landing for every pack we ship today is
`repo`; user-scope eligibility requires content portability — no hooks
wired into a specific repo's surface, no seeds that name a particular
project. The schema enforces `default-scope ∈ allowed-scopes` so the
rule holds outside the CLI. `agentbundle install` re-runs the
contract-level user-scope rails (seeds / hooks / marker) against the
resolved pack content at install time, closing the
widen-after-publish gap.

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
`work-loop` skill; this section is
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
is the *point* — an unattended, fresh-session-per-iteration loop (see the
work-loop skill).

**Why a hard iteration cap.** Without one, you're hoping. The cap lives as
data in `state.json` (see below) and is enforced by `loop-cohort check`
at `.claude/skills/work-loop/scripts/loop-cohort.py`; if you hit it, the
task is bigger than you thought — stop, re-plan, or split.

**Why capture learnings.** A loop that finishes without updating *some*
doc, skill, or note has wasted what it learned. The next agent (or a
human) will pay for it again. The work-loop skill enumerates where each
kind of learning belongs.

### Light and full modes

**Rigor scales with risk, not file count.** `work-loop` has two modes —
**light mode**, the default for low-risk work, and **full mode**, with every
gate, reviewer iteration, and the state machine. The `work-loop` skill is the
single owner of what each mode trims and how it runs; this section keeps only
the principle and the risk triggers, so the mechanics live in one place rather
than two. Work escalates to full mode the moment it trips a risk trigger:

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

**Why risk, not file count.** A familiar two-file change is cheap to get right
and cheap to undo; a one-file change to an auth path or a published interface is
neither. Each trigger maps to a gate the repo already maintains, so the set is
the boundary's exhaustiveness argument. The mechanics of what light mode trims
and how full mode runs live in the `work-loop` skill.

### Two front doors

Work enters this loop through one of two front doors, depending on whether the
repo already exists:

- **Greenfield — a brand-new repo from an idea.** The `init-project` skill is
  the front door. It runs a trigger gate (throwaways and one-off scripts skip
  the flow), a value gate over fed-in discovery, records a foundation (an ADR
  plus `docs/architecture/reference.md`), authors a walking-skeleton spec via
  `new-spec`, and hands the build to `work-loop`.
- **Brownfield — an existing repo.** The `adapt-to-project` skill is the front
  door, run after installing a pack to fit the conventions to what's already
  there — including harvesting a `reference.md` from the existing code.

Both converge on the same downstream loop: `brief → reference.md → spec →
low-level design → work-loop`. Neither is mandatory ceremony — the greenfield
trigger gate sends a throwaway straight to scaffolding, and a small change in an
existing repo just opens a PR.

### Work-loop state

The work-loop's `state.json` schema, exit contract, lifecycle, and
atomic-write discipline live with the skill that consumes them —
see `references/state-schema.md` in the `work-loop` skill.
The template at `assets/state.json` in the `work-loop` skill
is the starting point `loop-cohort init` copies in. Every state mutation
(init, plan-approval, fingerprint rotation, worktree coordination) is
owned by the `loop-cohort` tool;
SKILL prose calls each verb at the appropriate phase rather than
mutating JSON by hand.

### Model selection

Every subagent file declares `model:` in its frontmatter explicitly. The
[`lint-agent-artifacts.py`](../tools/lint-agent-artifacts.py) linter
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

**Supervisor mode is wave-scheduled and sequential by default.** The
work-loop builds the plan's full `Depends on:` DAG
(`loop-cohort schedule`) and runs tasks in topological order, single-agent,
on every adapter — failing loud on a cycle and warning on a
forward-reference. Parallel `implementer` fan-out is **opt-in and gated**,
never automatic: a wave runs in parallel only when every task is in a safe
category (cannot-collide / typed-Group-B / textual-loud) **and** passes a
`git merge-tree` file-disjointness check (`loop-cohort dispatch-decision`),
each in its own worktree, merged back with gates run in the primary; any
other category or merge conflict stays serial. The trigger and concept live
in the `work-loop` skill §EXECUTE; the step-by-step worktree procedure
lives in the skill's `references/supervisor-mode.md`. This section is the
why and the boundary.

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
order**. The procedure file
(`references/supervisor-mode.md` in the `work-loop` skill)
has the executable form (including how to order non-numeric IDs). If a
sequential merge conflicts, the tasks weren't actually independent —
the plan was wrong. Surface that as a PLAN-level escalation, not a
`git mergetool` session.

**Gates run in the primary, not the worktree.** Each implementer runs
gates inside its worktree and reports the result, but those results are
**advisory**. The supervisor reruns lint / typecheck / tests against
the merged state — that's the only signal that counts.

**Escalating implementer failures.** If an implementer reports
`blocked` or `failed`, the supervisor surfaces the failure list to a
human and returns to PLAN. It does **not** redispatch the same
implementer on the same task — the assumption that produced the
failure is what needs revising, not the attempt.

**Known limitation.** The procedure has been validated by prose
walk-through, not by an executed end-to-end dry-run. Any change to
**pre-flight (procedure step 0)**, **worktree creation (step 1)**,
**report persistence ordering (step 3)**, **merge order (step 5)**,
**cleanup recovery (step 6)**, or the **`state.json` `worktrees`
schema** must perform an actual `git worktree add` + parallel-dispatch
round against a throwaway spec before merging — read-only walk-through
is not sufficient for those surfaces. Step numbers refer to the
procedure at `references/supervisor-mode.md` in the `work-loop` skill.

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

**How agents see it.** `tools/hooks/session-start.py` reads the file
at session open and prints the entries — optionally filtered by a
path or narrower glob. Matching uses Python's `fnmatch` with the
caller's `--scope` value as the *path* argument and the entry's
stored glob as the *pattern*, so an agent working in
`packages/auth/server.ts` gets entries scoped to `packages/auth/**`
plus any repo-wide `*` entries. The work-loop SKILL's
*Capture what was learned*
section points contributors at this file as the destination for
pattern/gotcha/antipattern-shaped learnings; other shapes still go
where they already belong (AGENTS.md, skill bodies, architecture/).

### Enforcement

Two layered mechanisms enforce discipline before a PR opens:

| Layer | Mechanism | What it gates |
|---|---|---|
| Caps | `scripts/loop-cohort.py check` in the `work-loop` skill | Iteration cap, token budget, plan approval, fingerprint stasis (see `references/state-schema.md` in the `work-loop` skill). The same tool owns every state mutation upstream of the check. |
| Your gate | `tools/hooks/pre-pr.py` | Runs the caps check, then **your project's own** lint / typecheck / test commands — wire them into the stub in `pre-pr.py` (or let the `adapt-to-project` skill fill them in from your detected build commands). |

This is **Shift Left**: catch problems as early as possible, locally
before CI, at PLAN before EXECUTE. The pre-EXECUTE adversarial review
in the work-loop skill is the same pattern at a different layer —
moving review left from after code is written to before it is.

`session-start.py` is shipped pre-wired by the install pipeline: the
SessionStart binding lands in `.claude/settings.local.json`
automatically, no manual paste. `pre-pr.py` stays consumer-wired,
because Claude Code has no PR-open lifecycle event (`Stop` fires after
every agent turn — wrong semantics). Wire `pre-pr.py` via
`.git/hooks/pre-push` if you want it automatic, or run it by hand
before opening a PR. See [`tools/hooks/README.md`](../tools/hooks/README.md)
for both surfaces.

### When to reach for an unattended loop

The same loop can run unattended — a fresh agent session per iteration,
state in files only. Some agents ship a native mode for this. Use it when
*all* of these hold: completion is mechanical, work slices into
context-window-sized items, verification is reliable, and you've already
validated the approach in-session. It's a sharp tool — useful, narrow, and
not the answer to most work; the work-loop skill covers when it fits.



Skills are workflows agents invoke for repeating tasks: scaffolding a package,
opening an ADR, running a release. They live in `.claude/skills/<name>/SKILL.md`.

Add a skill when you've done the same multi-step thing three times. Don't add
one speculatively — speculative skills bloat context and degrade adherence.

The skill index is generated at the bottom of `AGENTS.md`.

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
- **Profile B** — [supervisor mode](#supervisor-mode) runs every
  multi-task plan in topological order (sequential by default); its
  parallel-write fan-out earns its keep only when a wave of independent
  tasks clears the safe-category ∧ `git merge-tree` gate. Reviewer
  fan-out follows the
  *Parallel dispatch discipline* section
  in the work-loop skill: one tool-call message, one Agent use per
  reviewer, barrier-wait, merge in the orchestrator's context.
- **Profile C** — same as B, plus the [knowledge base](#knowledge-base)
  is actively populated (`docs/knowledge/patterns.jsonl`). The
  `session-start` hook is shipped pre-wired by the install pipeline,
  so the knowledge base shows up in Claude Code session context out
  of the box; see [`tools/hooks/README.md`](../tools/hooks/README.md)
  for what lands and where.

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
| "I'll verify this manually, just this once." | Verification mode — TDD, goal-based, or manual QA — is declared in the plan task, not improvised at the keyboard. If manual QA is the right mode, write it down; if it isn't, pick TDD or a goal-based check. See the PLAN phase in the `work-loop` skill. |
| "I can fix this while I'm here." | Out-of-scope changes need a separate PR or an explicit note in the plan. Scope creep is the most common cause of failed adversarial review. See [`AGENTS.md` § Keeping changes minimal](../AGENTS.md#keeping-changes-minimal). |
| "This decision doesn't need an ADR — it's obvious." | If you're making it, it isn't obvious to the next person. Writing an ADR now costs less than someone re-litigating the decision in six months. See § 2 above and the `new-adr` skill. |

---

## Credentialed skills

Skills that call external authenticated APIs follow a tighter set of
rules than plain skills, because the moment a credential reaches the
LLM as a tool argument the architecture has already failed.
This section is the in-loop reminder of the shape every credentialed
skill must respect.

### Two-layer architecture

Skills do not hold credentials. A *credentialed primitive* — a Python
module, an MCP server, or a CLI wrapper packaged as a primitive —
owns the secret on disk and constructs the API call inside its own
process. The skill body invokes the primitive without ever touching
the token. A how-to on adding a credentialed skill walks authors
through broker selection and the verbatim security-rules blocks; the
shipped `jira` / `figma` skills are runnable references.

### Frontmatter declarations

A credentialed skill declares three project-specific flags under the
`metadata:` block of its `SKILL.md` frontmatter:

```yaml
---
name: your-skill-name
description: <what triggers it>
metadata:
  credentialed: true
  primitive-class: credentialed-cli   # or mcp-server
  auth: creds                         # env / cli / creds / sso-cookie
  # auth-fallback: creds              # optional: dual-auth — the broker to fall
  #                                   #   back to when the active one can't resolve
  #                                   #   (e.g. sso-cookie with a creds fallback)
  # broker-specific extras follow:
  # namespace: <ns>                   # required for auth: creds and auth: env
  # keys: ["<KEY>"]                   # required for auth: creds and auth: env
  # sso_profile: <profile>            # required for auth: sso-cookie
---
```

The keys live under `metadata:` rather than at top level because the
[agentskills.io specification](https://agentskills.io/specification)
pins the top-level frontmatter set to `name`, `description`,
`license`, `compatibility`, `metadata`, `allowed-tools` and reserves
`metadata:` as the project-specific escape hatch. `tools/lint-agent-artifacts.py`
refuses any top-level key outside that set; `tools/lint_credentialed_skills.py`
scopes its checks to skills with `metadata.credentialed: true`.

`metadata.auth-fallback` is optional and names a second broker a **dual-auth**
skill falls back to when the active one can't resolve (e.g. an `auth: sso-cookie`
skill that drops to `creds` on a non-SSO instance). When present, the skill's
Security section must satisfy **both** brokers' don't-block phrase sets.

### Four brokers — pick one per skill

`metadata.auth` names the broker that resolves the credential. The
four ids are pinned by
[ADR-0003](adr/0003-credential-broker-contract.md) and
<!-- seed-content-lint-ignore: canonical RFC pointer for the four-broker contract -->
[RFC-0013](rfc/0013-credential-broker-contract.md):

- **`env`** — the credential is a plain environment variable
  (`<NAMESPACE>_<KEY>`). Catalogue contributes naming convention and
  lint; no runtime resolver.
- **`cli`** — the primitive shells out to a vendor-authenticated
  binary (`gh`, `aws`, `kubectl`, `gcloud`). Vendor CLI owns the
  credential.
- **`creds`** — static token via the three-tier model (env → OS
  keychain → 0600 dotfile floor). Resolved via the `credbroker`
  library (`pip install credbroker`), imported in-process; the
  build-projected `credentials_shim` it replaced is retired for
  `creds` consumers (the four-broker taxonomy above is unchanged).
- **`sso-cookie`** — session cookie acquired via a headed-browser SSO
  flow. The skill resolves the session through the `credbroker` SSO
  resolver (`from credbroker import load_sso_cookies`), which
  subprocess-invokes `~/.agentbundle/bin/sso-broker.py` (projected by the
  `credential-brokers` pack at user scope) — mirroring how `creds` moved
  broker resolution into `credbroker`. A skill that still resolves the
  broker in its own `scripts/` is also accepted.

The broker-agnostic invariants below apply to every credentialed
primitive regardless of broker. Broker-specific lint extensions layer
on top (`auth: creds` requires a credential-resolver import in
`scripts/` — `from credbroker import …`, or the legacy
`from .credentials_shim …`; `auth: env` requires each declared `<NAMESPACE>_<KEY>` to
be read at least once; `auth: sso-cookie` requires either a credbroker SSO import
(`from credbroker import load_sso_cookies`) or subprocess-invocation of the
canonical `Path.home() / ".agentbundle" / "bin" / "sso-broker.py"` path; `auth:
cli` falls through to broker-agnostic checks only).

### Three storage tiers

Credentials resolve in this order, first-hit-wins per key:

1. **Tier 1 — env var.** `<NAMESPACE>_<KEY>` from `os.environ`
   (e.g. `JIRA_API_TOKEN`). Composes with Vault Agent / `op run --`
   wrappers without further changes; the only path that does.
2. **Tier 2 — OS keyring.** macOS Keychain via `/usr/bin/security`
   (token via child stdin, never argv); Windows Credential Manager
   via in-process `ctypes` against `advapi32`. Linux falls through
   to Tier 3 in v1 — a `libsecret` backend is deferred to a v2 RFC.
3. **Tier 3 — dotfile.** `~/.agentbundle/credentials.env`, mode
   `0600` on POSIX, DACL-verified via `icacls` on Windows. The
   fallback floor.

Changing the order, or adding a new tier, is an `Ask first` action
in the spec's Boundaries section — the corporate-network constraints
that justified the precedence are non-obvious.

### The argv ban

Credentialed-CLI-class primitives must refuse the value-shaped flags
`--token`, `--api-token`, `--api-key`, `--bearer`, `--pat`,
`--password`. The CLI verb's `setup` subparser registers these as
*tombstone arguments* whose action emits the verbatim sentinel
`tokens cannot be passed via argv` and exits non-zero; the
`tools/lint_credentialed_skills.py` lint refuses any primitive's
script that declares one of the banned names in an
`argparse.ArgumentParser.add_argument` call. MCP-server-class
primitives may accept *header-naming* flags (`--bearer-header`,
`--auth-header`, `--header-prefix`) because those name *which* header
to consult per-request, not the value.

### Anti-pattern register

Five anti-patterns rejected by name:

- **Tokens in skill argv** — defeats the architecture rule.
- **A `get` verb that returns a cleartext token** — any verb that
  prints the resolved token to stdout enables capture from a skill
  body. The `credential-setup` skill writes; a consumer's `check`
  verb reads (resolves and returns 0/non-0 only); no skill or shim
  surface returns the cleartext token to a caller other than the
  in-process credentialed primitive that owns the API call.
- **Per-skill dotfiles** — one well-known per-user file per the spec
  AC13 path; per-skill files multiply the wipe-on-rotation surface.
- **`SSL_VERIFY=false` defaults** — `--insecure` is opt-in only and
  must emit a stderr warning.
- **Vendored copies of third-party API skills** — pin upstream and
  audit; do not fork to silence a vendor's lint.

### Corporate-network requirements

Credentialed primitives ship from this catalogue running on corporate
laptops; the network they live on imposes constraints the primitive
must respect:

- **Honor `HTTPS_PROXY` / `NO_PROXY` from the environment.** No
  hard-coded `requests.get(...)` without proxy resolution.
- **Honor the system trust store via `REQUESTS_CA_BUNDLE`,
  `SSL_CERT_FILE`, `SSL_CERT_DIR`.** Corporate MITM CAs land here;
  ignoring them turns into a "works on the engineer's laptop only"
  bug.
- **Refuse `--insecure` / `verify=False` as a default.** Opt-in flag
  only; primitive emits a stderr warning whenever it fires.

---

## When this file is wrong

If a convention here is causing friction, **say so in an RFC**. Don't quietly
deviate. The whole point of writing this down is that the rules are visible and
contestable.
