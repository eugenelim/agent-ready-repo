# Spec: AGENTS.md lost obligations

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0088](../../adr/0088-risk-triggers-have-a-single-documented-home.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** n/a — instruction-surface restoration; no application LLD

> **Spec contract:** this document defines what done means. The implementing
> change matches this spec or updates it before merge.

## Objective

PR #1049 (`db5a4ed0`) compressed nineteen `AGENTS.md` / `AGENTS.local.md` surfaces
from 1666 lines to 616. A later audit of one deleted section found eight prose-only
privacy obligations that survived nowhere; #1056 repaired that section. A full audit
of the remaining ~1000 deleted lines has now found **twenty-two further obligations
with no owner** — no linter, test, schema, canonical document, or same-commit
relocation asserts them — plus **three surviving instructions that #1049 falsified**,
one of which now instructs a CI-failing action.

Success is: every obligation this audit found unowned is stated again in the
narrowest surface that governs it, the three falsified instructions agree with the
tree, and each restoration lands inside the existing class line cap so the
progressive-disclosure discipline #1049 installed is preserved rather than undone.

Deliberately retired items are **not** restored. Four candidates were retired by a
later decision with a stated reason; re-adding them would reverse a ratified
decision. They are enumerated in Boundaries.

## Acceptance criteria

Security and refusal semantics (adopter-shipped):

- [x] AC1 — `packs/AGENTS.md` states the realpath-canonicalisation rule for reads:
  `~`-expansion and `..`-rejection alone are insufficient because a symlink inside an
  approved directory bypasses containment.
- [x] AC2 — `packs/AGENTS.md` states the instruction-vs-data boundary for files
  loaded from a **user-controlled local path** (extract expected fields; ignore
  embedded directives), distinct from the fetched-external-content case that
  `security-checklists` AST05 already covers.
- [x] AC3 — `packs/AGENTS.md` states the cross-config confirmation rule: a config
  path from a user-level config shared across projects is confirmed to belong to the
  current project before use.
- [x] AC4 — `packs/AGENTS.md` states the `.apm/` UTF-8 stream-reconfigure requirement
  as a general rule for scripts that print, not only as the six existing per-pack
  test assertions.
- [x] AC5 — `packs/AGENTS.md` states that a non-cosmetic pack update also updates the
  pack's eval harness.

Carve-outs (losing one causes over-refusal):

- [x] AC6 — `packs/AGENTS.local.md` states that illustrative examples teaching a
  skill are permitted in shipped pack content and must not be stripped, **and**
  carries the anti-inference rule that the same ordinal may be internal in one file
  and illustrative in another, judged by what it points at rather than by its number.
- [x] AC7 — root `AGENTS.md` and `packs/core/seeds/AGENTS.md` state that internal
  callers and framework guarantees are trusted, bounding the validate-at-boundaries
  rule.

Prohibitions (losing one causes a leak):

- [x] AC8 — `packages/AGENTS.local.md` states the prohibition on internal-governance
  ordinals, spec ACs, and internal spec paths in comments, docstrings, argparse
  `help=` text, and runtime messages, **with** its adopter-visibility rationale and
  the positive duty to state the rule instead of citing where it was decided.
- [x] AC9 — root `AGENTS.local.md` states the ban on spec-AC citation comments
  (`# AC10:` and similar) in `.apm/**` source, which leak spec vocabulary into
  projected adopter artifacts.

Behavioural and process obligations:

- [x] AC10 — root `AGENTS.md` and `packs/core/seeds/AGENTS.md` state the duty to push
  back when warranted and to record disagreement rather than complying silently.
- [x] AC11 — root `AGENTS.md` and `packs/core/seeds/AGENTS.md` state that a helper is
  extracted when a second caller appears, not for a single use.
- [x] AC12 — `packs/core/seeds/AGENTS.md` states the new-top-level-directory
  obligation that root `AGENTS.md` retained, removing the adopter-facing asymmetry.

Site, guide, and profile surfaces:

- [x] AC13 — `web/AGENTS.md` and `docs-site/AGENTS.md` state the manual
  install-script (`allowScripts`) review duty when the lockfile moves, which is the
  compensating control for the machine check deferred under
  `npm-allowscripts-enforcement`.
- [x] AC14 — `web/AGENTS.md` states that the viewport meta tag is defined once in
  `SiteLayout.astro` and is not duplicated elsewhere.
- [x] AC15 — `docs-site/AGENTS.md` states the post-upgrade revalidation duty against
  the vendored Starlight component contracts.
- [x] AC16 — `guides/AGENTS.md` states the in-tree link preference, because links out
  of `guides/` render as GitHub blob URLs that send the reader off-site.
- [x] AC17 — `profiles/AGENTS.md` states that a pack name appears at most once in a
  profile and that packs with a declared `conflicts` relationship do not share a
  profile.

Package surfaces:

- [x] AC18 — `packages/AGENTS.md` states the test-isolation rules: no hardcoded
  `/tmp`, no direct `os.environ["HOME"]`, `tmp_path` rather than
  `tempfile.mkdtemp()`, and the `os.symlink()` skip guard.
- [x] AC19 — `packages/credbroker/AGENTS.md` carries the credbroker-scoped test
  isolation rules that its own deletion removed.
- [x] AC20 — `packages/agentbundle/AGENTS.md` states the UTF-8 subprocess
  environment rule, the Windows symlink / execute-bit test-skip rule, and the
  root-path detection form.
- [x] AC21 — `packages/credbroker/AGENTS.local.md` and
  `packages/agentbundle/AGENTS.local.md` state their release procedures: tag
  immediately after a version-bumping merge to `main`, confirm the publish workflow
  is green, and choose the next version against the published index.
- [x] AC22 — `packages/_example/AGENTS.md` and its adopter seed
  `packs/monorepo-extras/seeds/packages/_example/AGENTS.md` prompt for the
  cross-package import boundary and the ADR-trigger categories, and remain
  byte-identical to each other.

Falsified surviving instructions:

- [x] AC23 — the `risk-triggers` marker comment in
  `packs/core/.apm/skills/work-loop/SKILL.md` agrees with ADR-0088: the skill source
  is the sole home. It no longer instructs copying the block into `AGENTS.md`,
  `packs/core/seeds/AGENTS.md`, or `docs/CONVENTIONS.md`, which
  `tools/test_lint_agents_md_risk_block.py::test_noncanonical_homes_fail` proves
  fails CI.
- [x] AC24 — check 10g's comment in `tools/lint-agents-md.py` describes what
  `rt_files` actually contains rather than the retired four-document contract.
- [x] AC25 — the rule the two shipped skills quote by name exists verbatim in
  `AGENTS.md` and `packs/core/seeds/AGENTS.md`, as a single unbroken line carrying no
  `**` markers inside the phrase, so
  `git grep -cF -- 'Grep to verify a function exists before importing it'` returns
  both files. `contract-acquisition/SKILL.md` and
  `work-loop/references/infra-verification.md` quote it in the source's own
  capitalization. Note the quotation soft-wraps inside both citing files, so it is
  matched there whitespace-tolerantly rather than by a single-line grep — the
  checkable requirement is that the phrase exists in `AGENTS.md` and that no citing
  skill quotes a variant that differs from it.

Maintainer environment:

- [x] AC26 — root `AGENTS.local.md` states that auto-merge is disabled and that
  branch protection requires the branch to be up to date with base, so a merge needs
  the branch updated and is a manual step. Verified: `allow_auto_merge: false`,
  `required_status_checks.strict: true`.

Test that could not fail (found while proving AC23):

- [x] AC30 — `tools/test_lint_agents_md_risk_block.py::test_noncanonical_homes_fail`
  detects removal of the non-canonical-home guard. Its fixture created only the
  offending file, never the canonical source, so the "source must carry one complete
  block" branch emitted the same `risk-trigger-block drift` marker and the assertion
  passed whether or not the guard existed. Disabling the guard left the test green.
  The fixture now also creates
  `packs/core/.apm/skills/work-loop/SKILL.md`, so the assertion tests the guard it
  names. This is a scope addition, taken because this spec's Testing Strategy names
  that test as AC23's mutation proof and it could not serve as one.

Mechanical invariants:

- [x] AC27 — every edited `AGENTS.md` / `AGENTS.local.md` remains within its class
  cap (`tools/lint-agents-md.py`: root 120, root-local 60, core seed 100, scoped and
  local 80, `_example` 35), and the caps themselves are unchanged.
- [x] AC28 — `tools/catalogue/sync_authoring_scaffold.py --check` exits 0, and the
  scaffold projection of `packs/AGENTS.md` and `profiles/AGENTS.md` is byte-identical
  to its source.
- [x] AC29 — pack versions are bumped for changed pack content per the
  `packs/AGENTS.md` version-bump rule, and the agentbundle version is bumped because
  the change alters bundled scaffold package data.

## Boundaries

**Not restored — retired by a later decision with a stated reason.** Re-adding any
of these reverses a ratified decision:

- "Propose new top-level directories **via RFC**." Root `AGENTS.md` retains the
  softened routing, and `CONVENTIONS.md` deliberately demotes top-level location to
  evidence that never by itself selects the artifact.
- The `README-pypi.md` current-release assertion, dropped from the gated set because
  12 of the last 25 version bumps did not touch that file.
- The package-wide `Engine-Change-RFC:` trailer scope for every PR touching
  `packages/agentbundle/**`; the linter deliberately narrowed to behavioural paths,
  excluding tests and build recipes.
- Vendor-specific projection paths in shipped seed conventions, removed because
  `contracts/adapter.toml` projects into seven different roots.

**Also excluded from this change:**

- No new linter, schema constraint, or test is added to *enforce* a restored prose
  rule. The audit found prose deletions; this change restores prose. Converting any
  of these into machine enforcement is follow-up work needing its own acceptance
  criteria, not unrequested hardening bundled here.
- The latent `_profile_lint_one` defect the audit surfaced — a duplicated pack name
  makes `index` last-wins, so `[dep, dependent, dep]` reports a false ordering
  violation — is recorded as a follow-up, not fixed here. AC17 restores the prose
  rule only.
- `docs/CONVENTIONS.md`, `_data/catalogue-scaffold/**`, `.claude/**`, `.agents/**`,
  and `.codex/**` are generated. They change only by regeneration, never by hand.

## Testing strategy

The restorations are prose, so the gate is the instruction-surface linter plus the
suites that read these files, not new unit tests:

- `python3 tools/lint-agents-md.py` — class line caps, scope declarations,
  parent/child duplication, risk-trigger single-home, scaffold byte equality.
- `python3 tools/catalogue/sync_authoring_scaffold.py --check`.
- `python3 -m pytest packs/core/tests/pack/ -q` — seed content and installed-guidance
  link contracts.
- `python3 -m pytest tools/test_lint_agents_md_risk_block.py -q` and
  `tools/test_lint_agents_md_progressive_disclosure.py -q` — the guards protecting
  AC23/AC24/AC27.
- `make lint-ruff`, `make ci`.

**Mutation proof for AC23** (the one change with an executable contract): reverting
the marker comment to its pre-#1049 wording must leave
`test_noncanonical_homes_fail` passing while the comment again instructs the
CI-failing action — so the proof is that the *lint* rejects the instructed state.
Placing the risk-trigger block into any of the three named homes must produce
`risk-trigger-block drift`; removing that rejection must make the test fail.

## Audit corrections found by running the gates

Two audit verdicts were wrong, and only running the release-coupling gates revealed
it. Both are recorded rather than quietly dropped, and neither produced a
restoration — nothing has to be undone.

- **"Gate G requires a Changelog entry in `CHANGELOG.md`" was graded LOST. It is
  ENFORCED.** The audit checked `tools/repo/check_release_impact.py`, which accepts
  any release indicator, and concluded nothing required the package changelog.
  `tests/roster/test_workspace_status_projection.py:432` does: it requires
  `## [<pyproject version>] — <date>` in `packages/agentbundle/CHANGELOG.md`, keyed
  to the version, and it failed this change until the entry existed. No AC was
  written for this finding, so no prose was restored for it.
- **The `README-pypi.md` current-release assertion is only partly retired.** The
  Boundaries entry below is accurate about
  `tools/test_guide_typed_asides.py`, which dropped it from its gated set. But
  `tests/roster/test_okf_catalogue_discovery.py` independently asserts
  `What's new in <version>` appears in `README-pypi.md`, so the obligation is live
  under a different owner. It must not be restored as prose, and it must not be
  described as unowned.

The general lesson, worth more than either correction: an "unowned" verdict reached
by checking the *obvious* owner is a hypothesis, not a finding. Both of these
survived a literal-grep sweep with passing controls and an adversarial review, and
were caught only by a gate that failed.

## Assumptions

- Restoring prose to an `AGENTS.md` does not require an RFC. #1049 itself shipped
  with `Engine-Change-RFC: n/a` for instruction-surface work, and this change
  follows that precedent.
- The audit's twenty-two LOST verdicts were each verified with literal greps carrying
  a passing control, then re-verified whitespace-tolerantly after a wrapped-phrase
  false positive was found. Two delegated false positives were corrected before this
  spec was written.
