# Plan: Knowledge enquiry scope reachability

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Withdrawn:** 2026-08-27 — see the spec header; the reachability problem was
  repaired in the data, so this plan's T1-T3 and T5 are moot. T4 (the scope
  repair) shipped, executed through `write_topic` rather than a new script.
- **Repository anchors:** `packs/AGENTS.md` (runtime export boundary is
  `.apm/`; version bump rule; no tests under `.apm/`), `packs/core/AGENTS.md`,
  `packs/AGENTS.local.md:28-31` (pack release pipeline),
  `docs/rfc/0077-distill-knowledge.md:599-620` (scope grammar, matching rule,
  writer discipline), `docs/adr/0082-project-knowledge-modes-separate-authority.md:66-72`
  (mode authority separation), `docs/CONVENTIONS.md:661-663` (changelog
  obligation). Analogous implementation: `_committed_topic_paths`
  (`knowledge_store.py:1222`); test neighbours in
  `packs/core/tests/skills/project-knowledge/`. Named uncertainty: the `scopes`
  field has no documented format, which T8 closes.

All measured figures in this plan are stated once in the spec's Assumptions and
referenced from here rather than restated, per the one-canonical-home rule.

## Approach

Scope resolution is a pure function over strings, in three steps. Split a stored
scope entry into atoms on commas. Reduce each atom to its base — the leading
path segments before the first segment containing `*`, with the root atom `.`
reducing to the empty base. Match a query against a base using the ancestor
relation RFC-0077 fixes: the base is the same as, or an ancestor of, the query.
An empty base is corpus-wide and matches every query.

Specificity is the segment count of the matching base, so an empty base scores
zero and ranks last. Selection sorts by competency-facet bucket (unchanged),
then descending specificity, then `topic_key` as a deterministic tiebreak, and
only then truncates to `enquiry_bodies`.

The enquiry matcher is introduced as a function distinct from the existing
`_scope_matches`, which stays exactly as it is. ADR-0082 separates capture and
distill authority from enquiry authority, and the existing matcher has a second
caller on the distill pending path; giving enquiry its own matcher keeps that
separation intact by construction rather than by care.

The legacy data repair is a separate mechanical pass over the 30 affected topic
files, splitting each stored scope string on commas in place and rebuilding
`topics.index.json`.

**Why globs are resolved but commas are repaired.** Neither form is admitted by
RFC-0077's scope grammar. They are treated differently because their intent is
recoverable to different degrees: a glob names a path region unambiguously and
its author meant a region, so resolving it preserves intent; a comma-joined
string is a serialisation accident from `legacy-import` that names several
regions in one slot, and leaving it encoded would keep a malformed shape alive
in the store. The matcher tolerates commas so the store stays readable during
the repair; the repair removes them so that tolerance becomes dead code.
Formalising the glob form is recorded in T8's documentation rather than left
implicit.

## Constraints

- No new dependency, module, or top-level directory.
- Matching stays a pure function of strings: no filesystem access, no `git`.
- `enquiry_bodies` is unchanged; only the ordering feeding truncation changes.
- `_scope_matches` and the distill pending path are not modified.
- Canonical source is `packs/core/.apm/skills/project-knowledge/scripts/`;
  `.claude/` and `.agents/` are `make build-self` outputs.
- Version bump surface for this pack: `packs/core/pack.toml`,
  `packs/core/.claude-plugin/plugin.json`, and `docs/product/changelog.md`.

## Construction tests

Per task below. The primary regression guard is T3's corpus match-reachability
test.

## Design (LLD)

### Design decisions

- **Reduce globs to a base prefix rather than evaluating them.** Base reduction
  answers the only question matching asks — does the stored region cover the
  query — without needing a filesystem to be meaningful.
- **Ancestor-only, per RFC-0077.** The descendant direction was considered and
  dropped: measurement showed it adds nothing to reachability, so it would have
  bought an authority change for no gain.
- **Specificity is the segment count of the matching base.** Cheap, total, and
  explainable. Its known limit is recorded under Risks.
- **A separate enquiry matcher.** Behaviour isolation for the pending path is
  structural, not a promise.

### Data & schema

No schema change. `scopes` stays `list[str]`; the repair changes values, not
shape. `topics.index.json` is regenerated.

### Interfaces & contracts

`_scope_matches` is untouched. A new enquiry-only function returns the matching
specificity, or `None` for no match; `_entry_matches_query` calls it and
selection reuses the returned specificity for ranking.

### Behavior & rules

- A query of `.` matches everything; an atom of `.` reduces to the empty base
  and matches everything at specificity 0.
- Comma splitting applies to stored scopes, never to the query.
- Ranking never changes which topics match, only which fit the envelope.

### Failure, edge cases & resilience

- An empty atom after splitting is dropped, so a trailing comma cannot
  globalise a topic.
- An atom that is only a glob segment reduces to an empty base and is
  corpus-wide.
- Ties at equal specificity fall back to `topic_key`, preserving determinism.

### Quality attributes (NFRs)

O(atoms) string work per topic, no I/O. The enquiry path's cost stays dominated
by the existing committed-blob reads.

### Dependencies & integration

None added.

## Tasks

### T1: Scope atoms, bases, and specificity resolve correctly

**Depends on:** none
**Verification mode:** TDD
**Touches:** packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py, packs/core/tests/skills/project-knowledge/test_scope_resolution.py

**Tests:**
- Atom table: `"a,b"` -> `[a, b]`; `" a , b "` -> `[a, b]`; `"a,,b"` -> `[a, b]`;
  `""` -> `[]`; `"packs,"` -> `[packs]` and NOT corpus-wide.
- Base table: `packs/**` -> `packs`; `tools/repo/**` -> `tools/repo`;
  `**/*.py` -> `` ; `**` -> `` ; `packs/core` -> `packs/core`; `.` -> `` .
- Specificity table: base `packs/core/.apm` -> 3; `packs` -> 1; `` -> 0;
  `.` -> 0.

**Approach:** three module-private helpers beside the new enquiry matcher; all
pure and total, none raising on malformed input.

**Done when:** the three tables pass and no existing test changes.

### T2: Enquiry matching is glob-aware and ancestor-only

**Depends on:** T1
**Verification mode:** TDD
**Touches:** packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py, packs/core/tests/skills/project-knowledge/test_scope_resolution.py

**Tests:**
- Query `packs/core` matches a topic scoped `packs/**` (spec AC 2).
- Query `packs/core` matches a topic scoped `packs` (spec AC 2).
- Descendant control: query `packs` does NOT match a topic scoped
  `packs/core/.apm/skills/work-loop` (spec AC 3, second clause — this asserts
  the RFC-0077 boundary and must not be relaxed).
- Negative control: query `tools` does not match a topic scoped `web`.
- Monotonicity over the chain `packs`, `packs/core`, `packs/core/.apm`,
  `packs/core/.apm/skills/work-loop`, measured pre-truncation (spec AC 4).

**Approach:** implement the enquiry matcher over T1's helpers; leave
`_scope_matches` untouched.

**Done when:** all five pass, including both controls, and the existing suite is
green.

### T3: Every committed topic is matched by a concrete path query

**Depends on:** T2
**Verification mode:** TDD (integration surface)
**Touches:** packs/core/tests/skills/project-knowledge/test_scope_reachability.py

**Tests:**
- Over the committed store, every active topic is matched by at least one
  concrete repository path query, driving the production matcher (spec AC 1).
- No active topic is matched only by the `.` wildcard.

**Approach:** derive the candidate query set from the topics' own non-empty
scope bases plus the repository's real top-level directories. This derivation
was challenged as self-satisfying and the challenge was refuted: the same
derivation distinguishes the pre-fix matcher (21 of 76) from the post-fix
matcher (76 of 76), so the test discriminates.

**Done when:** the reachability test passes, and it fails when the enquiry
matcher is reverted to the pre-fix semantics.

### T4: Legacy comma-joined scopes are split verbatim

**Depends on:** T2
**Verification mode:** goal-based check
**Touches:** docs/knowledge/topics/*.json, docs/knowledge/topics.index.json, tools/repair-legacy-topic-scopes.py, packs/core/tests/skills/project-knowledge/fixtures/pre_repair_scope_atoms.json

**Tests:**
- `Done when:` no topic file contains a comma inside any `scopes` entry
  (spec AC 5).
- `Done when:` the topic-file count is unchanged (spec AC 6) — this catches a
  file lost or duplicated during a 76-file rewrite.
- Assert each repaired topic's scope atom **list** equals a committed golden
  fixture whose expected values are literal, authored independently of the
  splitter under test, so a wrong splitter cannot satisfy both sides.

**Approach:**
- Write the golden fixture first, by hand, from the 30 pre-repair values.
- Repair through the store's locking writer (`write_topic`) so
  `_validate_scope_list` and `hold_writer_lock` both apply, per RFC-0077's
  writer discipline. Note `_validate_scope_list` refuses duplicates, so the
  repair must not dedupe; splitting is verbatim.
- Rebuild the index through the store's rebuild path.
- Edit JSON through a parser, never a string replace.

**Done when:** both goal-based checks pass and the golden fixture matches.

### T5: The envelope carries the most specific matches, deterministically

**Depends on:** T2
**Verification mode:** TDD
**Touches:** packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py, packs/core/tests/skills/project-knowledge/test_scope_resolution.py

**Tests:**
- Given more matches than the envelope holds, the returned bodies are the most
  specifically scoped (spec AC 7).
- A corpus-wide topic is returned only when path-bounded matches do not fill the
  envelope (spec AC 7, second clause).
- Repeating a query returns the same bodies in the same order (spec AC 8).
- The envelope returns no more than `enquiry_bodies` bodies (spec AC 9).

**Approach:** add specificity to the sort key ahead of `topic_key`, leaving the
facet bucket first.

**Done when:** all four pass and the envelope size is unchanged.

### T6: Existing enquiry exclusions still exclude

**Depends on:** T2, T5
**Verification mode:** TDD
**Touches:** packs/core/tests/skills/project-knowledge/test_scope_resolution.py

**Tests:** one independently failing case per exclusion — audience, lifecycle,
freshness, `review_after`, competency facet — each on a topic that scope
matching alone would match (spec AC 10).

**Approach:** fixture per exclusion, driving the production selection path.

**Done when:** all five cases pass.

### T7: The distill pending path is unchanged

**Depends on:** T2
**Verification mode:** TDD
**Touches:** packs/core/tests/skills/project-knowledge/test_pending_selection.py

**Tests:**
- For a representative set of scopes, `--distill --pending` selects the same
  capture set before and after the change (spec AC 11).
- `_scope_matches` retains one-directional, non-glob semantics: a golden table
  asserts its behaviour directly, so a future edit that widens it fails here.

**Approach:** assert against the existing pending selection path; add no
production change.

**Done when:** both pass.

### T8: The scope contract is documented

**Depends on:** T1
**Verification mode:** goal-based check
**Touches:** docs/architecture/knowledge-capture.md

**Tests:** `Done when:` the document states the atom, base, specificity, and
ancestor-matching contract, and names RFC-0077 as the matching authority
(spec AC 15).

**Approach:** add a scope-semantics subsection to the owning architecture doc.

**Done when:** the section exists and the spec's undocumented-format assumption
no longer holds.

### T9: Projections and the release surface are resynced

**Depends on:** T1-T8
**Verification mode:** goal-based check
**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md, .claude/skills/project-knowledge/scripts/knowledge_store.py (make build-self output), .agents/skills/project-knowledge/scripts/knowledge_store.py (make build-self output)

**Tests:**
- `Done when:` canonical `knowledge_store.py` and both projections are
  byte-identical (spec AC 13).
- `Done when:` `pack.toml`, `plugin.json`, and the topmost `## [core][x.y.z]`
  changelog heading carry the same bumped patch version (spec AC 14).

**Approach:** bump 2.12.3 -> 2.12.4 in both manifests, add the changelog entry
as the topmost core heading, then `make build-self`.

**Done when:** both checks pass and `make build-check` is green.

## Rollout

- **Delivery:** single PR, reversible by revert. The data repair is idempotent
  and pre-repair values are recoverable from git history.
- **Infrastructure:** none. **External-system integration:** none.
- **Deployment sequencing:** T4's repair is safe before or after the matcher
  change because the matcher tolerates the malformed form; sequencing it after
  T2 keeps the repo readable at every commit.

## Risks

- **Specificity is depth, not distance to the query.** A topic scoped seven
  levels deep can outrank one naming the query's own parent. Accepted for now:
  under ancestor-only matching a deeper base is always closer to the query than
  a shallower one, because only ancestors match — the pathological case the
  reviewer constructed required the descendant direction, which this plan
  drops.
- **A single specificity tier can exceed the envelope.** 20 topics share the
  base `tools` and 25 apply corpus-wide, so a `tools` query has 20 tied matches
  for 12 slots and the tiebreak decides. No ranking rule fixes this; it is a
  scope-granularity property of the corpus. Recorded in the spec's Assumptions
  and left for a curation follow-up.
- **Base reduction is coarser than glob evaluation.** A topic scoped
  `tools/**/*.sh` matches a query for `tools/repo` even with no shell script
  there. Over-inclusion inside the right subtree is the safe direction.

## Changelog

- 2026-08-27: Initial plan.
- 2026-08-27: Revised against 15 sustained review findings. Dropped the
  descendant matching direction after measurement showed it adds no reachability
  and contradicts RFC-0077. Split the enquiry matcher from `_scope_matches` to
  preserve ADR-0082's mode separation. Added the changelog to the version-bump
  surface, a golden fixture for the repair, the `.` atom's specificity, the
  glob-versus-comma rationale, T7 (pending-path invariance), and T8
  (scope-contract documentation). Restated AC 1 at match level after a
  selection-level simulation showed 7 topics starved by the envelope.
