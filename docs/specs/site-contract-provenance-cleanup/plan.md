# Plan: Site contract provenance cleanup

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

## Approach

Annotate the three frozen documents through their Status field only, proving the
allowed delta as a one-changed-line diff; correct the four living guidance
surfaces; then record the legacy lifecycle dispositions as comment-preserving
register edits. Finish by running the focused link tests and comparing a
workspace reconciliation against the pre-transaction baseline. The spec, not the
historical backlog prose, remains the present-tense implementation contract.
ADR-0085 is already Accepted, so the palette supersession work runs in this
pass.

## Constraints

- Follow RFC-0089, ADR-0055, ADR-0085, and the
  frozen-document supersession rules in `docs/CONVENTIONS.md`.
- Preserve the provenance blocks registered in `workspace.toml`.
- Do not change routes, navigation, or checker behavior.

## Construction tests

**Integration tests:** focused rendered-link tests followed by full
`workspace-status reconcile`.

**Manual verification:** review the final workspace diff to confirm that each
closed item retains its original header, vintage, and canonical target.

## Design (LLD)

### Design decisions

The transaction closes or merges membership only after the canonical target is
present. Historical prose stays historical; living guidance contains the
current operational instruction. Traces to: all acceptance criteria.

### Dependencies & integration

The frozen Phase 4b spec points upward to ADR-0055. The earlier ADR and frozen
Starlight migration spec point to RFC-0089's follow-on ADR (ADR-0085, Accepted
2026-08-17) for only their superseded palette/token scope. Living guidance points
to the existing combined checker. Traces to: AC1-AC8.

`work-intake` exposes only `start`, `remember`, and `refresh` — it has no close,
retire, or merge transaction — so a register disposition is a comment-preserving
edit to `workspace.toml` in the form the register already uses for closed items
(`Closed <date> as …` plus `Original source: …`, retaining the review header and
vintage). The Manual QA diff in T3 is the named mitigation for the
detach-provenance risk. Traces to: AC4-AC7.

AC9's route/navigation clause is NOT verified by "the diff touches no generation
input" — it does touch one. Among the generation inputs `build-site.py` mirrors
into `docs-site/src/content/docs/` are `guides/**` and `packs/*/JOURNEY.md`
(alongside `packs/*/README.md`, `docs/product/changelog.md`, and `CONTRIBUTING.md`;
this list is the set this diff could plausibly touch, not a complete inventory —
`tools/build-site.py` is the authority). This change edits `guides/AGENTS.md`, so
it does change an emitted page (`build/docs/guides/agents/index.html`).

The sound argument is path-level, not cardinality-level: every generation-input
entry in `git diff --name-status` is an `M`, with no `A`, `D`, or `R`, so no
mirrored source path was added, removed, or renamed and no emitted route can move.
A route count alone would not establish this — a rename preserves the count, and a
renamed page nothing links to would still pass the link checker. The 269-route
capture and the clean combined `check-rendered-site-links.py` run are corroborating
evidence, not the argument. `guides/AGENTS.md` is additionally in `build-site.py`'s
nav-ineligible set, so no navigation entry changes either.

AC10 is a reviewer/manual check recorded as performed-and-clean; the forbidden
term is never quoted in a tracked file, commit, or PR body. Traces to: AC9-AC10.

## Tasks

### T1: Frozen-spec and guidance construction tests pin the allowed contract

**Depends on:** none

**Touches:** docs/specs/phase4b-product-docs-completion/spec.md, docs/adr/0055-starlight-replaces-mkdocs-for-reference-docs.md, docs/specs/starlight-migration/spec.md, guides/AGENTS.md, docs-site/AGENTS.md, Makefile

**Tests:**
- Goal-based: the three frozen documents each show exactly one changed line
  (`git diff --numstat`), and each annotation carries the licensed carrier for
  its document type — the spec parenthetical for the two specs, the ADR
  `partially amended` house form for ADR-0055 (AC1-AC2).
- Goal-based: no living-guidance file claims the repository has no link checker
  or that the two generation sequences are identical, and each names the
  canonical checker entry point (AC3).

**Approach:**
- Verification is goal-based, matching the spec's Testing Strategy. A byte-level
  frozen-body construction test is deliberately not written: it could only
  anchor on a git base ref (unavailable post-merge) or a committed hash, and a
  committed hash would reject the meaning-preserving mechanical rewrites
  `docs/CONVENTIONS.md` § Superseding a frozen document explicitly licenses.
- Substring assertions over prose are avoided for the same reason the register
  records under `site-test-source-substring-assertions`: they couple unrelated
  PRs to file formatting and do not detect removal.
- Pin the exact canonical checker path rather than duplicating its algorithm.

**Done when:** the frozen diffs are one line each, and the living-guidance checks
report no stale claim.

### T2: Frozen status and living guidance describe current authority

**Depends on:** T1

**Touches:** docs/specs/phase4b-product-docs-completion/spec.md, docs/adr/0055-starlight-replaces-mkdocs-for-reference-docs.md, docs/specs/starlight-migration/spec.md, guides/AGENTS.md, docs-site/AGENTS.md, Makefile

**Tests:**
- Goal-based: run the T1 checks (AC1-AC3).
- Goal-based: run the rendered-link checker unit suite (AC9).

**Approach:**
- Amend only the Phase 4b Status line — line 3, spelled `**Status:** Shipped`
  inside the leading fence rather than as a `- **Status:**` list item.
- ADR-0085 already exists and carries the backward `Supersedes: ADR-0055 in
  part` pointer, so the forward pointer completes the both-ends rule; amend only
  ADR-0055's and the Starlight migration spec's Status lines, each scoped to the
  palette/design-token assertions alone.
- Replace obsolete link-check guidance with the two-build ordering and checker
  reference, documenting CI's split generation stages separately from the local
  full-generation sequence (`make site-link-check`). Four surfaces carry a stale
  claim: `guides/AGENTS.md` (no-checker), `docs-site/AGENTS.md` § Broken links
  (no-checker) and § Build (claims it mirrors the workflow), and `Makefile`
  (claims the local order matches the workflow).
- `docs-site/AGENTS.md` is 142 lines against a 150-line CI cap, so the edit must
  be close to net-neutral: § Broken links collapses to a pointer at the checker
  and `make site-link-check`.

**Done when:** the allowed delta and link-check guidance checks pass.

### T3: Legacy memberships close with provenance intact

**Depends on:** T2

**Touches:** workspace.toml

**Tests:**
- Goal-based: reconcile shows no duplicate, invalid, or missing membership
  caused by the transaction (AC4-AC8).
- Manual QA: diff against `git show HEAD:workspace.toml` and confirm every
  preserved comment retains its pre-transaction review header and vintage
  (AC4-AC7). This diff is the named mitigation for the detach-provenance risk.

**Approach:**
- Commit `0455eea1` already closed `web-docs-link-check-gate` — its
  `{slug = …}` object is gone, its review header, traps, vintage, and
  `Original source:` line are intact, and its own comment records that
  "canonical closure verification remains in site-contract-provenance-cleanup".
  So verify that landed closure rather than re-opening and re-closing it, and
  normalise its pointer to the repository-relative `docs/specs/rendered-site-link-debt/spec.md`
  form AC4 names.
- `site-link-check-contract-docs` never entered the register, so the
  no-duplicate half of AC5 is already true; verify the rendered-link closure
  comment records the living-guidance-docs gap as merged into it.
- Retain `starlight-migration-rfc` in `[backlog].open` and record it as
  satisfied by accepted RFC-0089. Removing the membership would red
  `lint-spec-status.py` invariant (iv), which is HARD and resolves
  `(deferred: …)` anchors against `[backlog].open` only — and the frozen
  `starlight-migration` spec's anchor cannot be edited. Widening that invariant
  is a published-interface change requiring an RFC, and the brief already
  sanctions the retention.
- Keep the shipped rendered-link spec as the canonical target.

**Done when:** all dispositions are durable, non-dispatchable as intended, and
retain provenance.

### T4: Combined contract verification is green

**Depends on:** T3

**Touches:** docs/specs/site-contract-provenance-cleanup/spec.md, docs/specs/site-contract-provenance-cleanup/plan.md, workspace.toml, docs/product/briefs/tech-site-completion.md

**Tests:**
- Goal-based: focused rendered-link tests pass (AC9).
- Goal-based: no emitted route is added, removed, or renamed. `guides/**` is a
  generation input, so this diff does alter an emitted page; the check is that
  every generation-input entry in `git diff --name-status` is an `M` — no `A`,
  `D`, or `R`. The 269-route capture and the clean combined
  `check-rendered-site-links.py` run corroborate it; a count alone would be
  rename-blind (AC9).
- Goal-based: a Type 1/2/3 reconciliation captured before the transaction and
  again after shows no NEW inconsistency — the AC8 wording. An absolute "clean"
  is neither achievable nor in scope. Two pre-existing Type 2 findings stand, and
  neither is this spec's: `tracker-intake-adapters` (`ini-008`), present at the
  baseline capture, and `ci-gate-parallelization` (`ini-002`), which arrived with
  main `823cd174` after that capture and sits Shipped in the same
  `["ini-002".work].queue` this PR edits — so a reader diffing reconciliations
  must not attribute it here. Standing canonical findings and retained legacy
  memberships are likewise out of scope (AC8).
- Manual QA: AC10 recorded as performed-and-clean without quoting the term —
  commit messages and PR bodies are permanent record under AGENTS.md § Privacy,
  so the search pattern itself is never written down (AC10).

**Approach:**
- Capture the pre-transaction reconciliation baseline before T3 edits anything,
  per the brief's Instrumentation requirement.
- Run the smallest focused test set first, then the reconciliation, and report
  the delta rather than an absolute verdict.
- Move this spec's own lifecycle: `spec.md` to `Implementing` before any edit and
  to `Shipped` at the end, every criterion checked or deferred, `plan.md` to
  `Done`, and this spec's `workspace.toml` entry from `["ini-002".work].queue` to
  `["ini-002".work].shipped` — without that move a `Shipped` status emits a fresh Type 2
  finding against the check above.
- Let `lint-brief-coverage.py` derive the brief's Spec map cell; never hand-write it.
- Moving the queue entry falsifies the brief's Spec map preamble, which says all
  eight slices are registered in the work queue. Living-doc sync is same-PR
  obligatory, so correct that sentence here — required drift repair, not a
  ride-along.

**Done when:** all spec acceptance criteria have recorded evidence.

## Rollout

This is a repository-governance and guidance change with no runtime rollout.
Rollback is a normal patch reversal, except that frozen-body integrity must
remain preserved.

## Risks

- A manual TOML edit could detach provenance from its item.
- Over-broad wording could imply that Starlight itself checks generated links.
- A frozen-spec edit could accidentally change more than its Status line.

## Changelog

- 2026-08-17: initial plan derived from the approved tech-site completion brief.
- 2026-08-17: corrected at spec-stage review, before any code. `work-intake` has
  no close transaction, so T3 now names the register's own comment-preserving
  closure form. T1's byte-level frozen-body TDD test is replaced by a goal-based
  one-line-delta check (a committed hash would reject the mechanical rewrites
  CONVENTIONS licenses). T4's "reconciliation is clean" becomes the before/after
  delta AC8 actually asks for, and gains the missing Touches plus this spec's own
  lifecycle moves. AC3's surface list grows from two files to four (`Makefile` and
  `docs-site/AGENTS.md` § Build also claim the local order matches the workflow).
  Scope is unchanged; no acceptance criterion was added, removed, or weakened.
- 2026-08-17: corrected again during implementation review. AC9's verification
  argument was reversed — it had claimed the diff touches no generation input,
  which is false for `guides/**` — and restated at path level. T4's Touches grew
  to include the brief, whose Spec map preamble the queue move falsified. The
  frozen Starlight scope gained the § Boundaries Never-do entry, and a second
  unlicensed parenthetical added there was withdrawn. Still no acceptance
  criterion added, removed, or weakened.
