# New-spec review acceptance uses its exact clean-result contract

- **Slug:** `new-spec-review-phrase-contract`
- **Status:** Withdrawn
- **Level:** feature
- **Owner:** eugenelim

## Disposition — withdrawn 2026-09-24, overtaken in one half and never started in the other

**Do not act on the outcome below as written.** Measured on `6e89061c3`:

- **The phrase half was superseded, not delivered.** `9b9d470ef` (released core
  2.20.0) replaced the contract this intent was written against.
  `test_spec_review_accepts_only_exact_clean_before_adjudication` no longer
  requires the four phrases named below; it pins the current prose instead, says
  so in its own comment, and passes. The three "absent contracts" this intent
  asked to restore are not absent — they no longer exist to restore.
- **The remote-gate half was never started.** It is still true: no workflow under
  `.github/workflows/` runs `packs/core/tests/skills/new-spec/`. That gap is real
  and outlives this intent, but it is a CI-coverage concern rather than a phrase
  contract, so it does not belong to this outcome.

Withdrawn rather than reclassified because no execution evidence exists for this
intent: no spec was cut, and the change that moved the phrase contract was other
work. Withdrawal is the state an unratified bet that stopped before execution
takes, and it requires no `Accepted:` record. The original text is preserved
below unchanged, because the record of what was believed is the useful part.

## Outcome

The new-spec review protocol and its remote gate agree on the exact clean-result phrases that determine acceptance.

## Opportunity

`test_spec_review_accepts_only_exact_clean_before_adjudication` requires four phrases in `new-spec/SKILL.md`, but the exact-clean, do-not-persist, and non-exact-gateway phrases are absent, leaving only the repair-order phrase; no remote job currently runs this test.

## What this absorbs

### pre-existing-new-spec-exact-clean-phrase-drift

`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py:226` sets `direct = "entire returned text value is exactly \`Clean — ready to commit.\`"`. Restore the three absent contracts or update the test to the intended review protocol, and add the new-spec suite to a remote gate. The defect was pre-existing on `origin/main` and invisible to CI: Gate A-packs uses a curated suite list that omits `packs/core/tests/skills/new-spec/`, so no remote job runs this test, while local `make ci` (`test-after-build-check`) walks the whole `packs` tree and fails on it. This was confirmed in a clean `origin/main` worktree. `.github/workflows/catalogue-tooling-ci-gates.yml:176` still omits that suite.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
