# The spec and plan contract

What a spec is, what a plan is, and the metadata a gate reads. Relocated here
from the retired repository conventions document, which was the only home for
these rules.

**What:** the precise definition of a single feature, sized to be built in days
or weeks (not months). Each feature gets a directory.

```
docs/specs/<feature>/
├── spec.md      ← contract (objective, boundaries, testing strategy, acceptance criteria)
├── plan.md      ← strategy + construction tests, broken into tasks
└── notes/       ← (optional) research, sketches, rejected approaches, and
                    verification-ledger.md when execution produces an observation
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
for cases A, B, C". It may change substantively only while `Drafting`; once
approved, both it and `spec.md` are pinned except for lifecycle bookkeeping. See
§ *A spec directory freezes as a unit, when the spec ships*.

**Durable outputs own lasting truth.** A durable spec identifies the semantic
owners it expects to create or update before implementation starts: user
documentation, current product truth, current architecture, decision rationale,
interface or operations contracts, maintainer procedure, release history, and
reusable learning when applicable. The spec/plan pair may be retained as frozen
delivery history, but it is not a substitute for those living owners. Tests and
source remain executable capability proof; they do not preserve product intent,
rationale, authority, ownership, or non-executable operational promises.

**Lifecycle:** specs are **living documents** until the plan is approved. If
implementation diverges from the spec, the spec is wrong — but from approval
onward the correction is the controlled-amendment path, not an in-flight edit,
and an observation produced by execution goes to the verification ledger. After
the feature ships the spec **freezes**: at that point the *code is the truth*,
and the spec becomes the record of what was agreed, not a description of
current behaviour. A later behaviour change is recorded where it belongs — in
the code, and in an ADR if it reverses a decision — never by rewriting the
shipped spec. When a later decision reverses part of one, annotate its Status
field; see § *Superseding a frozen document*.

**Rigor and retention are separate.** Full-mode work may still use a
local-only or PR-only spec/plan when the approved record is confined,
fingerprinted, available to every required participant, and has an independent
post-closeout evidence owner. That choice affects where the live delivery
container may reside, not the approval, gate, or review standard. If another
person, worktree, CI job, or external control plane must read the contract,
session-local memory is not enough; use an established shareable surface or
retain the record. After implementation, `close-work` settles durable outputs
and workspace coordination before any delivery container can be removed.

Guards, pre-checks, and invariant-enforcement added during implementation are
ACs, not implementation details — if they affect observable behavior (exit
codes, refusals, error messages), they belong in the spec when they're added
to the code.

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
  vocabulary, `Drafting | Approved | Executing | Done` — a separate field, separate set.)
  Approved means the spec/plan contract has received human approval. In `spec.md` it means the scope is accepted; in `plan.md` it means the implementation strategy is accepted. Before code changes begin, an implementation run moves `spec.md` to `Implementing`.
  There is **no `Superseded` token**, and `Archived` is not a substitute — a
  superseded spec usually shipped and is still live. A supersession is recorded
  as a parenthetical *annotation* on the existing token
  (`Shipped (superseded in part by ADR-NNNN — …)`). A parenthetical on that
  token is the **only edit a frozen spec accepts**, and it carries exactly two
  licensed shapes: that supersession pointer, and a pointer recording that a
  `[backlog].open` anchor the body names has been closed. Form and rules for
  both: [§ Superseding a frozen document](#superseding-a-frozen-document).
  The linter reads only the leading token — it truncates at the first ` (`,
  ` →`, or `<!--` — so annotated statuses satisfy the vocabulary rule.
- **Acceptance Criteria notation.** Each criterion is a GitHub task-list item:
  `- [ ]` when open, `- [x]` when met. "Done" is the checklist, not an opinion.
- **Acceptance Criteria opt-out.** A spec that intentionally has no
  Acceptance-Criteria section carries
  `- **Acceptance Criteria:** none — <one-line reason>` in its metadata header;
  the field name `Acceptance Criteria` and value `none` use that exact casing,
  the separator is an em dash (U+2014), and the reason is required. The linter
  applies this gate to new specs and to specs whose section is removed in the
  current diff; existing sectionless specs are grandfathered. A reasonless or
  malformed marker, or a marker alongside a real section, is a hard violation.
- **No new shipped acceptance debt.** A spec newly transitioning to `Shipped`
  has every final accepted criterion checked. If required accepted work remains,
  the spec stays `Implementing` across sessions. If the owner agrees that work
  is separable, amend the spec/plan, remove it from the final AC set, and
  record it under `## Follow-ons` with an owner and stable work-intake artifact
  or external evidence reference. The amended fingerprint receives the normal
  review and human approval before implementation resumes.
- **Historical deferral token.** Frozen specs may still contain older inline
  `(deferred: <slug>)` markers. While they exist, the marker's `<slug>` must
  resolve to an entry in `workspace.toml [backlog].open` of *either* shape: a
  legacy record's `slug` field, or a canonical record's `path` through
  `lint-spec-status.canonical_entry_anchor`, which anchors a spec or plan path
  on its owning directory and any other artifact on its file stem. New entries
  take the canonical shape. A canonical `[backlog].open` entry must name an
  artifact that exists *and* whose `Status` is `Draft`, unless its `kind` is
  `defect`, which admits any carrier that is not `Closed`. A deferral with no
  artifact of its own therefore takes a Draft artifact of its own; it cannot
  point at the shipped document that records it, because a shipped or accepted
  carrier and an open backlog membership cannot coexist. Do not use this marker
  as a new shipping exception: a marker left in a body that later freezes pins
  its entry in `[backlog].open` permanently, since the frozen body cannot be
  edited to retire it. A follow-on recorded only in a PR comment rots; the
  register or external artifact is the stable pointer. Run `workspace-status`
  to see open backlog items.
- **Brief back-link (optional).** A spec derived from a product brief carries a
  `- **Brief:**` header naming that brief by its repository-relative path
  (`docs/product/briefs/<slug>.md` — the brief file's real path, which
  `workspace-status` reconciliation matches against the queue entry's
  `source.parent`; a bare slug fails that check and blocks dispatch). It
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

**Stub → EXECUTE handoff.** For TDD-mode tasks, PLAN carries the exact test code
as the task's compilable, validated red **stub** — as much of the real failing
test as the AC and contract honestly determine, never less than a compiling
assertion on the contract surface, never a bare `TODO`. PLAN compiles and earns
the red from disposable scratch; it does not create a repository test file.
After the state machine enters `CODE-IMPLEMENTATION`, EXECUTE materializes the
approved code unchanged in the real test location, proves byte identity and the
intended red, then completes red-green-refactor. A `spec-plan` run therefore
ends with documents only and no intentionally failing test in the repository.
The full procedure and the closed no-stub exceptions live in the `work-loop`
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

This is distinct from `contracts/` (adapter schemas) and from the
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

### A spec directory freezes as a unit, when the spec ships

`shipped specs/*` above means the whole directory — `spec.md` **and** `plan.md`.
This needs saying because the plan template's own contract line reads "Unlike
the spec, this document is allowed to change as you learn", which sounds like a
standing exemption and is not one. That licence is **phase-scoped**: it holds
only while the plan is `Drafting`, and ends when the plan is approved. From
approval, both `spec.md` and `plan.md` are pinned in substance. Only lifecycle
bookkeeping — the preamble status token and task-progress checkboxes — may still
be written. An observation produced by execution belongs in the sibling
`notes/verification-ledger.md`, never in either approved artifact.

There are therefore **two stages, not one.** At plan approval the pair is
*pinned in substance*: the contract stops moving so implementation cannot drift
it, while lifecycle bookkeeping is still written. Once the plan is `Done` and
the spec is `Shipped`, the work is over, both documents are history, and the
whole directory is *frozen* — the retention rule the `Frozen` class above
names. Pinned protects the contract during the build; frozen protects the
record afterwards.

A plan that stayed substantively editable after approval would be a second,
unversioned account of what we did, competing with the ADR that records why. A
genuine error in either approved artifact follows the controlled-amendment path.
