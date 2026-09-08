# Brief: agents load this repository's topology instead of rediscovering it by failing gates

- **Slug:** `internal-repo-topology`
- **Received:** 2026-09-03
- **Owner:** Repository maintainers
- **Status:** Draft
- **Source / provenance:** delivery experience on
  [`universal-implementer-dispatch`](universal-implementer-dispatch.md) slice U1

> **Skeleton.** Logged to shape, not to build. Sections below are deliberately
> thin; § "Ready gaps" carries what a Ready review must settle.

## Outcome

An agent authoring or implementing a change knows this repository's structural
facts before it acts: which files are generated and which are sources, which
tests pin which file's content, which trees are published, and which fields
want a bare identifier rather than a link. Today it learns them by tripping a
gate and reading the failure.

## Current-state evidence

Every item below is a real failure from one delivery (slice U1 of
`universal-implementer-dispatch`, 2026-09-03). Each cost at least one gate
cycle; several cost a CI round trip.

| Fact the agent lacked | How it surfaced |
| --- | --- |
| `docs/CONVENTIONS.md` is a self-host projection; the seed is the source | edited the projection; the gate chain reverted it |
| `packages/agentbundle/tests/` is a published tree run inside an sdist | new test resolved `packs/core`, failed `gate-export-boundary` and `build-and-smoke` |
| Spec-map cells take a bare slug, not a markdown link | `lint-brief-coverage` reported the spec `missing`, twice |
| `Brief:` takes a bare repository path, not a markdown link | fail-closed lifecycle check, in CI |
| `.claude-plugin/plugin.json` pins the pack version | `rg` skips dot-directories, so the version sweep missed it |
| `test_reference_routing.py` pins six prose substrings in a file being rewritten | the § 8a sweep pattern list does not catch plain `in` assertions |
| `build-self` refuses a dirty tree; `build-check` verifies `dist/` rather than rebuilding it | two separate red runs on stale artifacts |
| `make lint-ruff` is a CI leg outside the named gate set | `gate-main` failed on import sorting |

**[Inferred]** None of these is a code-comprehension problem. They are
repository conventions a maintainer holds and an agent cannot infer from the
code it is reading.

## Scope / Non-goals

**In scope (provisional):**

- A topology an agent can load for the files a change touches.
- Delivery through the existing phase-scoped policy mechanism rather than a new
  one: this is a policy family, and
  [`phase-scoped-policy-delivery`](phase-scoped-policy-delivery.md)'s D1 already
  owns phase-keyed selection and inlining.

**Non-goals:**

- A general code-understanding or semantic-search capability.
- An external repository-intelligence dependency. The facts above are
  repository-specific; a third-party tool would not know that a Spec-map cell
  wants a bare slug.
- **A hand-maintained index.** A curated list of structural facts is another
  drift surface, and drift is the problem this exists to remove.

## Constraints / Appetite

- **It must not be a file someone keeps current by hand.** This is the owner's
  binding constraint. Two candidate mechanisms, not yet chosen between:
  - **Derived** — spider what the repository already encodes. Source→projection
    edges are in the `Makefile` and `self-host`; content pins are in the test
    bodies; published trees are in packaging config; ignored trees are in
    `.gitignore`. This is regenerable, so it cannot drift.
  - **Accreted** — grow from agent learnings, the way a session memory does,
    but repository-scoped and committed, so the next agent starts where the
    last one stopped.
  - **[Inferred]** the answer is probably both: derive what is derivable, and
    accrete only what no artifact encodes.
- Whatever ships must be cheaper to run than the failures it prevents.

## Assumptions / Risks

- **[Inferred]** Deriving source→projection and content-pin edges is tractable;
  both are already machine-readable. Accreted knowledge is the harder half and
  carries the staleness risk the derived half avoids.
- **[Inferred]** Loading topology for touched files only keeps the context cost
  bounded; loading it wholesale would not.
- **Risk:** an accreted store becomes a second place to be wrong. It needs an
  expiry or verification story, or it reproduces the drift it replaces.
- **Risk:** the derived half can only reach facts some artifact already states.
  A convention that lives only in maintainers' heads stays invisible.

## Ready gaps (Draft only)

- No shaping review, no owner Ready confirmation.
- **Derived versus accreted is unchosen**, and it is the decision that
  determines whether this is a build or a habit.
- The consumption surface is unchosen: a policy family delivered by D1, a
  reference the controller inlines, or something the `spec-author` agent reads.
- No measurement. The evidence above is one delivery's failures; a second
  sample would show whether the same classes recur or whether U1 was unusual.
- Relationship to session memory is unexamined — several of these facts were
  already in a personal memory store and still did not reach the work.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |
