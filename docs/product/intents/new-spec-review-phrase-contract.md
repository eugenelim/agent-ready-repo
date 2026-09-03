# New-spec review acceptance uses its exact clean-result contract

- **Status:** Draft
- **Level:** feature

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
