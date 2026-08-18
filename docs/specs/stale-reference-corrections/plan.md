# Plan: stale-reference-corrections

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `.github/workflows/build-check.yml` — one comment block relocated (AC1).
- `web/src/design-system.md` — § 6 and § 8 prose plus § 6's resolved-value table (AC2).
- `tools/lint-build.py` — one trailing comment (AC3).
- `Makefile` — one comment line in the `sast` target (AC4.1).
- `workspace.toml` — `[backlog].open` only: one entry widened (AC4.2), five deleted (AC6).
- `docs/specs/stale-reference-corrections/{spec.md,plan.md}` — this contract.

**What demonstrates done**
- Goal-based throughout. No behavior changes, so no new test earns its place: a
  test asserting a comment's line number would pin formatting, which is the exact
  antipattern `site-test-source-substring-assertions` is open against.
- `python3 tools/test-build-check-workflow.py` and `python3 tools/lint-ci-parity.py` green (AC1).
- `python3 tools/lint-build.py` green (AC3).
- `make sast` pip-audit leg green with the four suppressions byte-identical (AC4).
- `workspace-status status --root .` exits 0, five fewer open entries (AC6).
- `python3 .claude/skills/work-loop/scripts/lint-spec-status.py` green (deferral anchors intact).
- `make ci` green before the PR opens.

**What I am NOT changing**
- No executable line anywhere. Every edit is a comment, a prose sentence, a
  markdown table cell, or a `[backlog].open` array member.
- Not the `--ignore-vuln` suppressions, the manifest they scan, or their four CVE ids.
- Not `contracts`/`guides` in `RFC_AUTHORISED_DIRS` — no authorising RFC exists.
- Not § 8's known-deviations table in `design-system.md`. It is a separate claim
  about two `#ffffff` literals and needs its own verification pass; AC2 is scoped
  to the import claim and the dark-mode mechanism stated in the same sentences.
- Not `docs/backlog.md`. AC4 repoints away from the tombstone; adding a section
  to it would re-establish the split registry the tombstone exists to end.

## Declined patterns

- **Tempted:** fix § 8's two `#ffffff` known-deviation rows while the file is
  open. **Declined:** they are a different claim (token-compliance deviations,
  not the import mechanism), and I have not verified whether
  `.site-footer__brand` still sets `color` at all. An unverified "correction" is
  how this class of drift got here.
- **Tempted:** re-attribute `contracts` and `guides` in `RFC_AUTHORISED_DIRS`
  too, since they carry the same ADR-cited-as-RFC shape. **Declined:** RFC-0089
  exists and names `docs-site`; nothing authorises the other two, so the honest
  edit is unavailable and inventing an attribution is worse than the status quo.
  Recorded as a deferral.
- **Tempted:** add a lint asserting every `RFC_AUTHORISED_DIRS` comment cites an
  `RFC-` number, so AC3's class cannot recur. **Declined:** it would fail on
  `contracts` and `guides` immediately — a checker that lands red is the
  `npm-allowscripts-enforcement` trap, already open for exactly this reason.
- **Tempted:** while removing five entries, also delete the three anchor-only
  entries (`ci-gate-*-branch-protection-widening`, `starlight-migration-rfc`)
  whose work is done. **Declined:** each is retained deliberately because a
  frozen spec's `(deferred: <slug>)` marker must resolve; removing one reddens
  `lint-spec-status` invariant (iv). Their own comments say so.
- **Tempted:** convert the 150-line `packs/AGENTS.md` cap problem into a
  restructure that frees several lines. **Declined:** the pointer fits as an
  in-place word swap; reorganising a capped context file to make room for one
  sentence is a change nobody asked for.

## Tasks

### T1 — Verify every claim (no writes)
- **Mode:** goal-based. `Done when:` each of the five entries' defect claims has
  been re-checked against the tree and the evidence recorded in `spec.md`.
- **Tests:** no stub (goal-based).
- **Status:** done. All five confirmed; AC2 found the defect wider than the entry
  described (the mechanism claim and the hex table, not just the import sentence)
  and the spec records the measurement.

### T2 — AC1: relocate the build-check comment block
- **Mode:** goal-based. `Done when:` `test-build-check-workflow.py` and
  `lint-ci-parity.py` are green and the block precedes its own step.
- **Tests:** no stub (goal-based) — see the trio's note on line-number assertions.
- **Touches:** `.github/workflows/build-check.yml`.

### T3 — AC2: correct the docs-palette claims
- **Mode:** goal-based. `Done when:` the four greps in AC2 return the stated
  results and every token/hex pair in the corrected table resolves in `starlight.css`.
- **Tests:** no stub (goal-based).
- **Touches:** `web/src/design-system.md`.

### T4 — AC3 + AC4.1: re-point two stale citations
- **Mode:** goal-based. `Done when:` `lint-build.py` green and
  `grep -n "docs/backlog.md" Makefile` returns nothing.
- **Tests:** no stub (goal-based).
- **Touches:** `tools/lint-build.py`, `Makefile`.

### T5 — AC5: name the pack schema — ATTEMPTED, REVERTED, DEFERRED
- **Mode:** goal-based. `Done when:` `lint-agents-md.py` green,
  `test_catalogue_tooling_docs.py` green, `wc -l packs/AGENTS.md` = 150.
- **Tests:** no stub (goal-based) — `test_line_count` already covers the cap.
- **Touches:** none in the final diff.
- **Outcome:** the edit landed and `make ci` failed on
  `test_scaffold_projection.py::test_packs_agents_md_cites_only_paths_it_ships` —
  the authoring scaffold ships no `contracts/` directory, so the pointer dangles
  in every adopter's tree. Reverted (source files, projection, and manifest), and
  the backlog entry rewritten with the constraint and three options. The gate the
  entry did not know about is the one that decided this.

### T6 — AC4.2 + AC6: reconcile `[backlog].open`
- **Mode:** goal-based. `Done when:` `workspace-status status` exits 0 with four
  fewer open entries than the base ref, `lint-spec-status.py` green, and `git diff workspace.toml`
  shows hunks inside `[backlog]` only.
- **Tests:** no stub (goal-based).
- **Touches:** `workspace.toml`.
- **Depends on:** none of T2-T5 functionally; sequenced last so the entries are
  removed only after their fixes are in the same diff.
