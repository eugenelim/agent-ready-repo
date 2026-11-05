# Extend SAST coverage and required merge protection

- **Slug:** `sast-scanner-coverage-expansion`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

Shipped JavaScript receives Semgrep and CodeQL analysis, and the repository can make CodeQL findings merge-blocking when remote branch protection permits it.

## Opportunity

JavaScript is absent from the configured Semgrep and CodeQL coverage, while CodeQL's status is not locally proven to be a required main-branch check.

## What this absorbs

### sast-javascript-coverage

- **Authority:** [spec/pack-script-root-boundary-validation](../../specs/pack-script-root-boundary-validation/spec.md)
- Shipped JavaScript is not scanned by any of the three scanners. Semgrep runs only `p/python`, `p/security-audit`, and the local `tools/semgrep/` rules, and `codeql.yml` configures only `languages: python`.
- Add JavaScript security rulesets to the Semgrep gate configuration and add `javascript-typescript` to `codeql.yml` languages.
- Triage and fix the findings that both changes turn on.

### codeql-required-check

- **Authority:** [spec/pack-script-root-boundary-validation](../../specs/pack-script-root-boundary-validation/spec.md)
- Make the CodeQL check required in branch protection so interprocedural taint findings block a merge instead of only annotating it.
- The `Makefile` comment beside `SEMGREP_EXCLUDE` records that CodeQL is not a required check on `main`, but branch-protection and ruleset requirements are remote GitHub state.

## Assumptions

- A current GitHub branch-protection or ruleset observation is required to establish whether CodeQL is presently required on `main`.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

## Current truth

Verified 2026-11-05. JavaScript is shipped: 28 `.js` and `.mjs` files outside tests under `packs/`, `docs-site` and `web`. `codeql.yml:61` has `languages: python`, and the Makefile semgrep gate loads only `p/python` and `p/security-audit`. A local run of `p/javascript` plus `p/security-audit` over those 28 files returned zero findings, and a control file with `eval` and `document.write` returned findings, so the rules load and the triage cost is nil today. Branch protection on `main` requires `make build-check`, `gate-main`, `gate-sast`, `gate-export-boundary` and `gate-credbroker`. No CodeQL check is among them.

## Readiness

- **Route:** new-spec for the JavaScript coverage slice, sequenced after `semgrep-registry-ruleset-pinning` or in its spec, because both change the same gate line.
- **First slice:** add the JavaScript ruleset to the semgrep gate and `javascript-typescript` to `codeql.yml`.
- **Agent-only proof:** `make sast` passes with a fixture that the JavaScript rule must flag.
- **Manual residue, named and non-blocking:** making the CodeQL check required is a repository setting. The owner flips it once after the JavaScript analysis has run green on `main`.

## Non-goals

- Flipping the CodeQL required-check setting; it is a remote repository setting and stays an owner follow-up.
- Pinning the Semgrep registry rulesets, owned by `semgrep-registry-ruleset-pinning`.

## Riskiest assumption

**Riskiest assumption:** CodeQL's JavaScript analysis will also come back clean. The Semgrep run found 0 findings on the 28 shipped files, but CodeQL has not run. Tested agent-only by running the CodeQL query pack locally if available, otherwise by dispatching the workflow on the branch and reading its alerts before the slice lands.
