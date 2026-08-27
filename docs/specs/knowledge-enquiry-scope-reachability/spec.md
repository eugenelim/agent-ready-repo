# Spec: Knowledge enquiry scope reachability

- **Status:** Archived <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0077](../../rfc/0077-distill-knowledge.md), [ADR-0081](../../adr/0081-canonical-project-knowledge-uses-per-topic-json.md), [ADR-0082](../../adr/0082-project-knowledge-modes-separate-authority.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Withdrawn 2026-08-27 — the problem was data, not code.** This spec proposed
> a matcher change to fix enquiry reachability. Repairing the malformed scopes
> instead — splitting 30 comma-joined strings and reducing glob segments to
> repository-relative paths, none of which RFC-0077's grammar admits — took
> reachability from 21 of 76 to **76 of 76 with the production matcher
> unmodified**. No code change was needed. The body below is retained unedited
> as the record of what was proposed and why it was wrong.
>
> One genuine defect the spec identified survives and is **not** fixed by the
> data repair: with scopes now matching, a query returns 18-35 matches against a
> 12-body envelope, and selection truncates by `topic_key` alphabetically
> because there is no relevance ranking (`knowledge_store.py:2156-2162`). That
> is a separate, smaller change and needs its own spec.
>
> The review record in [`notes/`](notes/) is kept deliberately: two adversarial
> rounds, an adjudication that refuted 4 of 22 findings, and a round-2
> origin-tagging pass that found 8 of 15 findings were defects introduced by the
> round-1 repairs. That evidence is useful independently of this spec.

## Objective

A maintainer or agent asking `project-knowledge --enquire` "what should I know
about `<path>`?" is matched against every topic whose declared scope covers that
path. Scope matching reads the three forms the store holds — a plain path, a
glob, and a comma-joined legacy string — and resolves each to the path region it
names, so a query for `packs/core` is matched by a topic scoped `packs/**` as
readily as by one scoped `packs`. Matching follows RFC-0077: a topic matches when
one of its declared scopes is the same as, or an ancestor of, the requested
scope.

Because a scoped query is matched by more topics than the bounded envelope
returns, the envelope carries the most specifically scoped matches: a topic whose
scope names the queried region closely outranks one that applies corpus-wide.
Ties within a specificity tier resolve deterministically.

Success for the user is that no topic is invisible to the seam because of how its
scope happens to be written. Which of the matched topics fit the envelope is a
budget decision, stated below and bounded, not a matching failure.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Measure reachability with the production matcher and the production selection
  path, never a re-implementation of either inside the test.
- Keep the enquiry envelope bounded by the existing `enquiry_bodies` budget;
  widening which topics *match* never widens how many bodies are *returned*.
- Repair a legacy scope string by splitting it verbatim on commas, preserving
  each segment's text and order.
- Rebuild `topics.index.json` through the store's own rebuild path after any
  topic-file change.
- Re-project into `.claude/` and `.agents/` and confirm the three copies of
  `knowledge_store.py` are byte-identical before declaring done.

### Ask first

- Changing `enquiry_bodies` or any other value in the budget contract.
- Changing a legacy topic's scope to anything other than a verbatim comma split.
- Introducing a scope form the store does not already hold, or any matching
  direction beyond the ancestor relation RFC-0077 fixes.

### Never do

- Add a dependency. Glob-base reduction and specificity ranking are string
  operations over path segments; `fnmatch`, `pathspec`, and a globbing library
  are all unnecessary.
- Add a new module, package, or top-level directory.
- Touch a filesystem or run `git` to decide whether a scope matches. Matching is
  a pure function of the query string and the stored scope strings.
- Change the scope semantics used by the capture and distill pending path.
  ADR-0082 separates those authorities from enquiry; the enquiry matcher is
  distinct from the pending matcher.
- Weaken any existing enquiry exclusion — audience, lifecycle, freshness,
  `review_after`, or competency facet — to make a topic reachable.
- Edit `.claude/` or `.agents/` copies directly instead of re-projecting from
  the canonical `packs/core/.apm/` source.

## Testing Strategy

- **Scope resolution (comma splitting, glob-base reduction, the `.` root):**
  TDD. A pure function with a compressible invariant; a table of
  (stored scope, expected atoms, expected base, expected specificity) cases pins
  it, and each case fails independently.
- **Ancestor matching:** TDD. A table of (query, stored scope, expected) cases,
  including a negative control and a case asserting the descendant direction
  does **not** match.
- **Specificity ranking and tie-breaking:** TDD. Ranking is a total order; a
  fixture of competing scopes asserts the emitted sequence, not set membership.
- **Corpus match reachability:** TDD at integration surface, driving the
  production matcher over the committed store. This is the primary regression
  guard and the AC 1 check.
- **Envelope bound and composition:** TDD, driving the production selection path
  so truncation and ranking are exercised together.
- **Enquiry exclusions:** TDD, one independently failing case per exclusion.
- **Legacy scope repair:** goal-based check over the repaired data.
- **Projection parity and version bump:** goal-based checks.

## Acceptance Criteria

- [ ] Every active topic in the committed store is matched by at least one
      concrete repository path query; no active topic is matched only by the `.`
      wildcard.
- [ ] A query for `packs/core` is matched by a topic scoped `packs/**`, and by a
      topic scoped `packs`.
- [ ] Matching is the ancestor relation RFC-0077 fixes: a topic whose scope is
      the same as, or an ancestor of, the query matches; a topic whose scope is a
      strict descendant of the query does not.
- [ ] The number of topics matching a query is non-increasing as the query
      narrows along a nested path chain, measured before the envelope truncates.
- [ ] No topic file contains a comma inside any `scopes` list entry, and the set
      of scope atoms each topic declares is unchanged by the repair.
- [ ] The number of topic files is unchanged by the repair.
- [ ] Where matches exceed the envelope, the returned bodies are the most
      specifically scoped matches; a topic that applies corpus-wide is returned
      only when fewer than `enquiry_bodies` path-bounded matches exist.
- [ ] Ties within a specificity tier resolve deterministically, so repeating a
      query returns the same bodies in the same order.
- [ ] The enquiry envelope returns no more than `enquiry_bodies` topic bodies for
      any query.
- [ ] Audience, lifecycle, freshness, `review_after`, and competency-facet
      exclusions each still suppress a topic that scope matching alone would
      match; one independently failing case per exclusion.
- [ ] `project-knowledge --distill --pending` selects the same captures for a
      given scope as it does today; the enquiry matcher change does not reach the
      pending path.
- [ ] `packs/core/tests/skills/project-knowledge` passes in full.
- [ ] `knowledge_store.py` is byte-identical across its canonical location and
      its `.claude/` and `.agents/` projections.
- [ ] `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, and
      `docs/product/changelog.md` carry the same bumped patch version in one PR.
- [ ] `docs/architecture/knowledge-capture.md` documents the scope atom, base,
      and specificity contract this spec relies on.

## Assumptions

- Technical: runtime is Python >=3.11; this worktree runs 3.13.13 (source:
  `packages/agentbundle/pyproject.toml`; probe `python3 -V`)
- Technical: RFC-0077 fixes matching to the ancestor relation — "A topic matches
  when one of its declared scopes is the same as or an ancestor of the requested
  task scope" (source: `docs/rfc/0077-distill-knowledge.md:604-606`, Status
  Accepted, decision weight heavy, unamended)
- Technical: scope values are validated as repository paths only; no glob,
  comma, ordering, or specificity semantics exist in the validator (source:
  `_validate_scope_list`, `knowledge_store.py:836`)
- Technical: the enquiry matcher is shared with the distill pending path at
  `knowledge_store.py:2930`, whose refusal guard sits at `:2936`; ADR-0082
  separates those authorities, so this spec gives enquiry its own matcher
  (source: call-site audit — exactly two callers, `:2045` and `:2930`)
- Technical: no live capture carries a glob or comma in `project_scope.paths`
  (0 of 24 values across 17 captures), so the pending path's behaviour is
  unchanged in fact as well as by construction (source: probe over
  `docs/knowledge/observations/*/*.jsonl`)
- Technical: measured over the committed 76-topic store, the current matcher
  reaches 21 of 76 across 32 candidate concrete queries; the `.` wildcard
  reaches 76. Ancestor matching plus glob-base reduction plus comma splitting
  reaches 76 of 76 at match level (source: probe driving the production
  `_scope_matches`, then the proposed resolution)
- Technical: 55 of 76 topics carry a glob scope; exactly 30 carry a comma-joined
  scope string, all from `producer: legacy-import` (source: probe over
  `docs/knowledge/topics/*.json`; independently reproduced during review)
- Technical: `packs/core` is absent from `.claude-plugin/marketplace.json`
  (14 plugins, none named `core`), because the Claude plugin marketplace is the
  user-profile install route and `core` is repo-scope (source: probe;
  `docs/adr/0002-install-scope-per-pack-default-and-allowance.md:34`,
  `docs/adr/0004-repo-scope-per-adapter-projection.md:41`). The third file in a
  core version bump is therefore `docs/product/changelog.md`, required by
  `docs/CONVENTIONS.md:661-663` and RFC-0095, not the marketplace manifest.
- Process: the core pack's eval harness is an activation eval — 20
  `should_trigger` query strings — and this change alters no activation
  phrasing (source:
  `packs/core/.apm/skills/project-knowledge/evals/eval_queries.json`)
- Product: ranking is by scope specificity rather than alphabetical truncation
  (source: user confirmation 2026-08-27)
- Product: a corpus-wide scope stays matchable and ranks last (source: user
  confirmation 2026-08-27)
- Product: legacy comma-joined scopes are split verbatim; no scope's meaning is
  re-derived here (source: user confirmation 2026-08-27)
- Product: AC 1 is stated at match level rather than selection level. Measured
  over the committed store, 69 of 76 topics are also *returned* by some query;
  the residual 7 are starved by the envelope because 25 topics apply corpus-wide
  and 20 share the base `tools`, so a single specificity tier exceeds
  `enquiry_bodies`. That is a scope-granularity property of the corpus, not a
  matcher defect, and no ranking rule resolves it within the budget (source:
  selection-level simulation over the committed store, 2026-08-27)
