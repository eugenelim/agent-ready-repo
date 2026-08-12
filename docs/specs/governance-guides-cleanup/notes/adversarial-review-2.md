# Review round 2 — adversarial + quality + security

Run on the reconstructed branch. Two of these lenses had never been applied:
`notes/final-review.md` records `quality-engineer` as a named skip (its runtime
failed to terminate) and the experience role as unavailable. The first round's
`Clean — ready to commit.` therefore covered less than it appeared to.

The reviewers also saw material no one had reviewed: the replay hand-fixes, the
changelog commit, and the judgment record.

## Fixed

**Damaged sentence the scrub left behind.** `guides/_shared/how-to/author-a-skill.md`
read "…is available now in-harness Add an optional `expect` block…" — removing
`(RFC-0037 § Errata E3).` took the sentence terminator with it. T4's manual-QA
bullet claims to have inspected for exactly this, so AC10 and T4's Done-when
were both checked against an inspection that missed a live defect.

**Supersession statement destroyed rather than delinked.**
`guides/product-documentation/README.md`'s `## Replaces` section became
`## Package name` restating the install block eight lines above. The brief said
delink or repoint; the content was lost instead. Restored link-free.

**A `required` pin weakened so a scrubbed guide would pass.**
`tools/lint-plugin-route-docs.py` gained a `GUIDE_REPO_ONLY_REFERENCES` tuple
dropping `user-guide-diataxis` from the packs `install-routes.md` must
enumerate — because the scrub had deleted the name from that guide. The spec's
Never-do forbids exactly this. `packs/user-guide-diataxis/pack.toml` still
declares `allowed-scopes = ["repo"]`, so the enumeration was simply false
without it. Reverted the lint to its original form and restored the name.
`product-documentation` correctly does *not* belong in that list — it is
`["repo", "user"]`.

**The 18 tests ran in no gate.** `tools/test_lint_guides_no_repo_only_refs.py`
was named in neither the `Makefile` `test` target nor `build-check.yml`, and the
new `docs.yml` job runs the linter, not its tests. AC1–AC6's only verification
artifacts would never have executed again. Registered in both; AC13 and an
extended T3 now own it.

**A repo-only pointer the guard structurally cannot see.**
`guides/_shared/explanation/README.md` carried "Those are ADRs (`../../adr/`)" —
backticked, so not a Markdown link, so invisible to rule 1, and the target does
not resolve. AC7 claims *every* Type-A reference is gone. Reworded.

**Junction detection was a fail-open no-op on the supported floor.**
`_is_junction` used `getattr(path, "is_junction", None)` returning `False` when
absent, but `Path.is_junction` is Python 3.12+ and this repository supports
3.11. All four junction checks were dead code there while AC1 claimed junction
refusal. Now raises on Windows when the API is unavailable.

**External URLs would have reddened the gate.** Rule 1 matched any target whose
path carried `/rfc/` or `changelog`, with no scheme check — so a citation of
`rfc-editor.org/rfc/7231` or `keepachangelog.com` would fail with no in-repo
fix available. Exempted, with tests.

**Tests that could not fail.** The allow-marker test asserted only
`returncode == 0`, so it stayed green if the token rule became a no-op. Added
the exact-output assertion, the paired control without the marker, a
reasonless-marker case, and boundary cases pinning the `\d{2,4}` window and the
hyphen (widening to `\d+` had survived the whole suite).

**Contentless teaching example.** `governance-extras/how-to/governance-index.md`
had an "e.g." whose example was the placeholder it explained. Reworded.

**Changelog claimed guides are installed.** `guides/AGENTS.md` is explicit that
the tree is not installed into adopter repos. Rewritten, and a second entry
added for the sidebar-label change the frontmatter migration causes — an
adopter-visible effect the first entry omitted.

**Process gaps I introduced.** AC12 had no owning task (now T6) and the
`Makefile`/`build-check.yml` edits were outside the spec's Ask-first surface
(now listed). The changelog assumption cited a one-off user authorization where
`docs/CONVENTIONS.md` already requires the entry — reworded so an auditor can
tell a corrected boundary from a moved goalpost.

**Replay duplicate.** `plan.md` carried a byte-identical changelog line, the
same artifact class as the deduplicated regex and shadowed test function. An AST
comparison of the three touched Python files confirms no further duplicate
top-level definitions.

## Narrowed rather than fixed

**AC1 overstated the path controls.** Two claims did not hold: the guides-root
confinement check is tautological (the repository root is derived from the
candidate), and only the final path component is link-checked, so a symlinked
*ancestor* is followed. I implemented the canonical-path check that would close
the ancestor case and reverted it — it also rejects ordinary paths wherever a
system directory is itself a link, which is every macOS `/var` path. Shipping a
control that breaks legitimate use to satisfy an AC is the wrong trade, so AC1
now states what the code enforces and the module docstring lists the gap.

**AC8 said "every mention".** Too broad: a guide stating a fact about the
shipped pack is not a stale reference. AC8 now distinguishes references from
factual mentions, which is what the corpus actually needed.

## Accepted, not actioned

**Rule 3 is allow-by-default in both directions.** A citation of a pending spec
is invisible, and an untouched guide turns red the day someone creates a
`docs/specs/` directory colliding with an invented tutorial slug — the tutorial
ships `spec/capture-work-v2` and `spec/workspace-status-phase2`. Inverting the
`spec/` arm to an explicit teaching-slug allowlist would close both. That
changes the detection contract in AC4 and deserves its own spec, not a
late amendment to this one. Both directions are now documented in the tool
header; the pending direction is fenced by `notes/scrub-judgment.md`.

**Escape-hatch suppressions are silent.** No marker exists in the repository
today. Emitting a stderr note per suppression is worth doing before the first
one lands, but it adds behaviour and needs its own test.

**Guard misses raw HTML anchors, autolinks, bare prose paths, and lowercase
tokens.** Real bypasses, all documented in the header as limitations. Adding
`re.IGNORECASE` to the token rule would change AC3's contract and risks
overmatching; the HTML-anchor case is live in the corpus
(`frontend-engineering/tutorials/scaffold-a-component.md`) but carries no
governance reference today.

Each of these belongs in a follow-up, noted in the PR rather than dropped.

## AC12 manual QA

Read both `[Unreleased]` entries as someone who has never seen this repository:
they name what changed for a guide reader, avoid contributor framing, do not
claim the guides are installed locally, and state that no pack version changes.
