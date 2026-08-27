# Finding adjudication — round 1

Paired output for [`adversarial-review-round-1.md`](adversarial-review-round-1.md).
Only SUSTAINED findings are routed to repair. REFUTED and INDETERMINATE are
retained for audit, per the work-loop's finding-adjudication gateway.

- **Adjudicator:** `finding-adjudicator` (Read/Grep only; artifact persisted by
  the controller, which is why this file is hand-written rather than emitted)
- **Result:** 15 sustained (5 Blockers, 8 Concerns, 2 Nits), 4 refuted,
  3 indeterminate
- **Gateway state:** `ADJUDICATION-INDETERMINATE` — the three indeterminates
  each require an owner decision, not a machine-checkable evidence retry, so
  they stop here rather than re-entering review.

## Sustained — Blockers

| # | Finding | Settling evidence |
| --- | --- | --- |
| 1 | `Constrained by: none` is false; AC 3 contradicts RFC-0077 | Verified verbatim at `docs/rfc/0077-distill-knowledge.md:604-606`: "A topic matches when one of its declared scopes is the same as or an ancestor of the requested task scope." RFC-0077 is `Status: Accepted`, `Decision weight: heavy` (`:3`, `:8-10`). No amendment section; ADR-0082 records `Supersedes: none`; no ADR-0083..0089 or RFC-0090..0097 revisits it. Ancestor-only is the live contract. |
| 3 | AC 4's "result set" sentence is false; its operative clause is true | Sort key is query-independent (facet bucket, descending specificity, `topic_key`) and truncation happens after sorting (`knowledge_store.py:2156-2162`), so the top 12 of a subset can contain an entry outside the top 12 of its superset. Returned sets are not nested. Holds a priori; the reviewer's named counterexample was not re-derived and is not needed. |
| 5 | `_scope_matches` has a second, uncovered caller | Exactly two call sites: `_entry_matches_query:2045` and `_pending_from_loaded_partitions:2930-2933`, the latter passing `event["request"]["project_scope"]["paths"]`. `journal_capacity` refusal confirmed at `:2936-2937`. 17 live events across the three 2026-08 journals. ADR-0082 (`:66-72`) governs the mode isolation this would couple. |
| 7 | The version-bump AC omits the changelog | `docs/CONVENTIONS.md:661-663` and `:934-937`, RFC-0095 (`Status: Accepted`), and `packs/AGENTS.local.md:28-31` all require a `docs/product/changelog.md` entry in the same PR as a version bump. Current heading `## [core][2.12.3] — 2026-08-26` at `changelog.md:53` matches `pack.toml:3`. **Reviewer's remedy over-broad:** the marketplace assumption is correct as written and must NOT be reworded — the cited topic's three files are pack.toml, plugin.json and marketplace.json. Add the changelog; leave the assumption. |
| 8 | T4's atom-set assertion cannot detect a wrong splitter | Compares `atoms(pre)` with `atoms(split(pre))`; when both use T1's splitter the sides agree for any splitter, correct or not. Set comparison additionally hides the dedupe at `plan.md:209` — a dedupe the sanctioned writer would refuse (`knowledge_store.py:849-850`). |

## Sustained — Concerns

| # | Finding | Note |
| --- | --- | --- |
| 9 | AC 9 is a before/after process step with no record location | Retcon violation; `plan.md:180-182` names no artifact path. |
| 10 | `.` atom specificity undefined | Base reduction as written gives `.` a one-segment base, i.e. specificity 1, ranking `.`-scoped topics **above** every empty-base glob — contradicting the Objective. Corpus dependence is **4 topics, not the 2 the reviewer claimed.** |
| 11 | T4 bypasses the sanctioned write path | Skips `write_topic:1056`, `_validate_scope_list:836`, `hold_writer_lock:377`, required by RFC-0077 `:611-620`, `:635-648`. `rebuild_topic_map:1332` has no CLI mode; `project_knowledge.py:680-684` exposes only capture/distill/enquire/migrate-legacy/activate-staged. Data risk contained (splits pass `_expect_repo_path`); process risk is not. |
| 13 | Globs blessed, commas repaired, no rationale | RFC-0077 `:599-601` admits only NFC-normalized repo-relative components; a `**` segment is as far outside the grammar as a comma. **Both corpus figures independently reproduced: 55 of 76 carry a `*`, exactly 30 carry a comma.** |
| 15 | Load-bearing facts duplicated | Version-bump conclusion in 5 places; "30 topics" in 2; `enquiry_bodies=12` in 2 plus two ACs. Finding 7's repair must now land at every version-bump site at once — the drift the rule exists to prevent. |
| 16 | Retcon violations | Confirmed at `spec.md:27`, `:90-92`, `:119`. **`:30` is not a violation** — "stays reachable" is weaker than the reviewer claimed. |
| 17 | Objective's success statement yields no derivable test | "would have found by grepping by hand" has no observable post-condition and no Testing Strategy row. |
| 18 | AC 6 leaks plan-owned mechanism into the contract | "reduces to an empty base" is plan vocabulary; the spec's own contract term is "corpus-wide". |

## Sustained — Nits

- **19** — T7 cites AC 10/AC 11; actual are AC 11/AC 12.
- **22** — T2, T5, T6 declare no verification mode; T6's behavior has no Testing
  Strategy row to inherit one from.

## Refuted (retained for audit)

- **4 — "T3 is vacuous by construction."** Broken predicate: *consequence*.
  T3 asserts selection through the **production selection path**, which
  truncates to `enquiry_bodies` after a query-independent sort. The identity the
  finding proves (`base ⊑ q` by equality, so every topic *matches* its own
  derived query) is a match-level fact and does not make the selection-level
  assertion unfailable. The finding's measurement is real; its conclusion does
  not follow.
- **14 — "AC 5's count clause is unfalsifiable."** Broken predicate:
  *consequence*. T4 rewrites 76 files; losing or duplicating one during that
  rewrite is exactly what the count clause detects. It is a safety invariant.
- **20 — "16 of 76 is a sample, not the ceiling."** Broken predicate:
  *observation*. `spec.md:145-147` already attributes the figure to "eight
  representative concrete-path queries" and asserts no ceiling. The substitute
  figure (21/76 over 40 queries) was not reproduced; static enumeration of
  distinct non-empty scope bases came to ~30, not 40.
- **21 — "T7's `Touches` must not list projections."** Broken predicate:
  *existing handling*. `Touches:` declares expected file globs for
  wave-disjointness and warns that under-declaration is unsafe, so listing them
  is required. The Boundary forbids editing them *instead of* re-projecting;
  T7 re-projects via `make build-self`.

## Indeterminate — each needs an owner decision

- **2 — AC 1 and AC 6 jointly unsatisfiable.** The 14-of-76 empty-base figure
  **reproduces exactly**, but only by treating `.` as an empty base, which is
  *not* what the plan specifies — so the starvation result is computed against a
  rule the plan does not state. The 7-of-1255 result needs execution, outside a
  read-only envelope. The corpus holds 4 topics scoped `"."` and 4 scoped
  exactly `["tools"]`, so the reviewer's enumeration cannot be matched to the
  corpus as counted. **Depends on finding 1 and finding 10.**
- **6 — segment count is not closeness.** Mechanism confirmed a priori, and both
  cited topics exist at the claimed depths. But the Objective's literal contract
  only requires exact-or-close to outrank *corpus-wide*, which segment count
  satisfies, and `spec.md:162-164` records owner confirmation of specificity
  ranking. Sustaining would overturn an owner-settled design choice on
  unreproduced ranks. **Depends on finding 1.**
- **12 — undocumented scope semantics.** `docs/architecture/knowledge-capture.md`
  carries no scope-matching semantics, but the gap is recorded in the spec's
  Assumptions, not that file, so the finding's second clause misstates where.
  RFC-0077 `:599-609` already owns the grammar and matching rule. Whether
  documentation is in scope here or rides the RFC-0077 amendment is an owner
  call.
