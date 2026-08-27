# Adversarial review — round 1 (spec mode)

Raw reviewer report, persisted unchanged for adjudication. Not acted on
directly; every finding below is routed through `finding-adjudicator` before
classification or repair.

- **Target:** `spec.md` + `plan.md` at draft, this directory
- **Reviewer role:** `adversarial-reviewer`, spec mode
- **Dispatched:** 2026-08-27
- **Verdict:** not clean — 8 Blockers, 10 Concerns, 4 Nits

---

## Blockers

**1. `Constrained by: none` is false, and AC 3 contradicts an Accepted RFC.**
`spec.md:6` and `:106-108`. RFC-0077 (Status: Accepted, decision weight heavy)
fixes the matching contract at `docs/rfc/0077-distill-knowledge.md:604-606`:
"Matching compares resolved path components, never raw string prefixes. A topic
matches when one of its declared scopes is the same as or an ancestor of the
requested task scope." AC 3 ("a topic whose scope is a descendant of the query")
reverses a governing decision with no citation and no amendment; ADR-0081 and
ADR-0082 also govern this subsystem and are uncited. Fix: cite
`Constrained by: RFC-0077, ADR-0082` and land an RFC-0077 amendment (or a
superseding ADR) in the same PR that changes the ancestor-only matching sentence.

**2. AC 1 and AC 6 are jointly unsatisfiable on the committed corpus.**
`spec.md:101-103` vs `:115-117`. Simulating the proposed design (comma split,
glob-base reduction, bidirectional prefix, sort by `-specificity` then
`topic_key`, truncate at `enquiry_bodies=12`) over the real 76-topic store:
14 of 76 topics reduce entirely to an empty base (`['**/*.md']`,
`['**/tests/**']`, `['.']`, ...), and 7 topics are never selected by any of 1255
candidate queries — including both topics scoped literally `.`, plus `['tools']`
x2. AC 6's ranking is precisely what starves them, so AC 1 cannot pass. Fix: add
a low-specificity reservation (reserve k of the 12 bodies for the highest-ranked
otherwise-unselected matches) or scope AC 1 to non-empty-base topics and add a
T4-adjacent data repair for the `.`-scoped and bare-`tools` topics.

**3. AC 4 is false as written; counterexample on the spec's own chain.**
`spec.md:109-112`. The prose says "Broadening a query never shrinks its result
set"; the operative clause says "the number of matching topics is
non-increasing". Only the second is true. Measured: `packs/core/.apm` returns 12
bodies, and narrowing to `packs/core/.apm/skills/work-loop` returns a body absent
from the broader query's set (`a-partly-generated-content-directory-hides-two-traps-...`).
Post-truncation the returned sets are not nested. Fix: delete the "result set"
sentence and state AC 4 solely over pre-truncation match counts.

**4. T3 — the spec's primary regression guard — is vacuous by construction.**
`plan.md:184-186`. "Derive the candidate query set from the topics' own scope
bases" means every topic T gets a query `q = base(atom of T)`, so `base ⊑ q`
holds by equality and T matches unconditionally. Measured: 0 of 76 topics match
no derived query, independent of whether matching is bidirectional. Fix: pin the
query set to a committed list of real repository paths and assert reachability
against that fixed list.

**5. `_scope_matches` has a second caller the spec and plan never mention.**
`plan.md:86-88` states "keeps its signature so existing call sites are
unaffected." Signature stability is not behavior stability.
`knowledge_store.py:2930` calls it from `_pending_from_loaded_partitions` to
filter observation-journal captures by
`event["request"]["project_scope"]["paths"]`. Widening to bidirectional +
glob-base makes `--pending --scope X` list captures it previously hid, and pushes
`len(ranked)` toward the `_refuse("journal_capacity")` guard at `:2936`.
ADR-0082 separates capture and enquiry authority; this silently couples them.
Fix: keep `_scope_matches` one-directional for the pending caller and introduce a
distinct `_enquiry_scope_match` used only by `_entry_matches_query`, or add an AC
covering the pending-path behavior change.

**6. Segment-count specificity does not implement the Objective's ranking
contract.** `spec.md:28-31` vs `plan.md:75-77`. Absolute depth is not closeness.
Measured for query `packs/core`: rank 1 is a topic scoped to a single file seven
levels deep (`.../work-loop/scripts/lint-spec-status.py`), while the topic scoped
`['packages', 'packs', 'tools']` — which literally names the query's parent — is
dropped at rank 17. Fix: rank by distance between query and matching base
(common-prefix segments, tie-broken by `|len(base) - len(query)|` ascending).

**7. The version bump is three files; the spec bumps two and names the wrong
third.** The marketplace claim is correct — `core` is absent from
`.claude-plugin/marketplace.json` (14 plugins). But "two files, not three" is
wrong: `git show --stat` on the last core patch bump (`30fc001e`, 2.12.2 ->
2.12.3) touched `packs/core/pack.toml`,
`packs/core/.claude-plugin/plugin.json`, and `docs/product/changelog.md` (which
carries `## [core][2.12.3] — 2026-08-26` at line 53). Fix: add
`docs/product/changelog.md` to the version-bump AC and T7's `Touches`, and reword
the assumption to "the third file is the changelog, not marketplace.json."

**8. T4's atom-set assertion is an identity that cannot fail.** `plan.md:205`.
If both sides are computed with T1's `_scope_atoms` helper, the assertion is
`set(atoms(pre)) == set(atoms(pre))`. It cannot catch a wrong splitter, and by
using a set it cannot catch the dedupe T4's own Approach performs. Fix: capture
pre-repair atom lists as a committed golden fixture computed independently of the
splitter, and assert list equality.

## Concerns

**9.** AC 9 is a process step, not an observable outcome, and violates retcon
discipline (`spec.md:123-124`); `plan.md:180-182` names no record location.

**10.** Specificity of the `.` atom is undefined and untested; base-reduction as
described yields specificity 1, ranking `.`-scoped topics above every empty-base
glob, contradicting AC 6's intent. T1's table omits `.`. 2 real topics depend on
it.

**11.** T4 bypasses the sanctioned write path (`write_topic:1056`,
`_validate_scope_list:836`, `hold_writer_lock`) which RFC-0077's fail-closed
writer discipline requires; the script has no home in `Touches`. All 30 splits
would validate, so data risk is contained; process risk is not.
`rebuild_topic_map:1332` has no CLI mode; `--migrate-legacy` does.

**12.** The change formalises scope semantics no document owns; it records the
gap in `docs/architecture/knowledge-capture.md` then ships without closing it.

**13.** Glob scopes are blessed while comma scopes are repaired, with no stated
rationale. RFC-0077's scope grammar (`:599-606`) admits only NFC-normalized
repository-relative components — globs are as much a schema violation as commas,
and 55 of 76 topics carry one.

**14.** AC 5's second clause ("total topic count unchanged") is unfalsifiable —
T4 creates and deletes no files.

**15.** Duplicated facts drift independently: the version-bump conclusion appears
in 4 places and finding 7 shows it is wrong in all 4 at once; "30 topics" in 2;
`enquiry_bodies=12` in 2 plus 3 ACs.

**16.** Present-tense retcon violations at `spec.md:27`, `:30`, `:90-92`, `:119`.

**17.** The Objective's success statement ("would have found by grepping by
hand") has no observable post-condition.

**18.** AC 6 leaks plan-owned mechanism ("reduces to an empty base") into the
spec contract.

## Nits

**19.** T7 cites "spec AC 10"/"AC 11"; actual are AC 11/AC 12.

**20.** "16 of 76" is a sample, not the ceiling — all 40 concrete queries
derivable from the store's own scope bases reach 21 of 76. `.` reaching 76
confirmed.

**21.** T7's `Touches` lists generated projections as edited files, against the
spec Boundary forbidding direct edits to `.claude/`/`.agents/`.

**22.** T2, T5, T6 do not name their verification mode.
