# Extend SAST coverage and required merge protection

- **Status:** Draft
- **Level:** feature

## Outcome

Shipped JavaScript receives Semgrep and CodeQL analysis, and the repository can make CodeQL findings merge-blocking when remote branch protection permits it.

## Opportunity

JavaScript is absent from the configured Semgrep and CodeQL coverage, while CodeQL's status is not locally proven to be a required main-branch check.

## What this absorbs

### sast-javascript-coverage

- **Authority:** [spec/pack-script-root-boundary-validation](../../specs/pack-script-root-boundary-validation/spec.md)
- Shipped JavaScript is not scanned by any of the three scanners. Semgrep runs only `p/python` and `p/security-audit`, and `codeql.yml` configures only `languages: python`.
- Add JavaScript security rulesets to the Semgrep gate configuration and add `javascript-typescript` to `codeql.yml` languages.
- Triage and fix the findings that both changes turn on.

### codeql-required-check

- **Authority:** [spec/pack-script-root-boundary-validation](../../specs/pack-script-root-boundary-validation/spec.md)
- Make the CodeQL check required in branch protection so interprocedural taint findings block a merge instead of only annotating it.
- `Makefile` line 272 records that CodeQL is not a required check on `main`, but branch-protection and ruleset requirements are remote GitHub state.

## Assumptions

- A current GitHub branch-protection or ruleset observation is required to establish whether CodeQL is presently required on `main`.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
