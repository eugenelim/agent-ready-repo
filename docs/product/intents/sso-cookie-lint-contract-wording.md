# SSO-cookie lint wording matches the check carve-out

- **Slug:** `sso-cookie-lint-contract-wording`
- **Status:** Fulfilled
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Fulfilled:** 2026-11-12 eugenelim: aligned the lint, both consumer skills, tests and evals on the manual-setup prohibition while preserving headless recovery; 211 targeted tests pass.
- **Shaping-reviewed:** 2026-11-05
- **De-risked:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

Catalogue lint wording forbids interactive or manual SSO setup on the user's behalf while preserving the shipped setup-helper check allowance and consumer checks' headless recovery policy.

## Boundary

- The pinned SSO-cookie guidance phrase and the contract tests that enforce it.
- Credential behavior, automatic-refresh policy, capture commands, and unrelated lint rules remain outside this intent.

## Owner

- eugenelim, with AgentBundle catalogue-lint maintainers.

## Unresolved questions

- None recorded. The shipped check carve-out remains authoritative.

## Projection

- One direct-light implementation after acceptance that amends the phrase and its exact contract tests without changing runtime behavior.

## Opportunity

This intent absorbs sso-cookie-lint-phrase-amendment. The former phrase said not to run any setup helper, while the shipped check carve-out permits the non-mutating check path, so the literal guidance contradicts the enforced behavior. Consumer checks may recover an expired session headlessly; they are not necessarily non-mutating.

## Assumptions

- This is a wording and test-contract correction, not authorization for a new credential operation.
- A protected AgentBundle change requires accepted Engine-Change-RFC authority at landing time.


## Source

- Mode: repo-origin
- Locator: docs/specs/jira-check-sso-auto-login/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

## Current truth

Verified 2026-11-12: the four original pin sites use the identical phrase `do not run interactive or manual setup for them`: `packages/agentbundle/agentbundle/catalogue_tooling/lint.py`, both Atlassian consumer `SKILL.md` files, and `packs/atlassian/tests/skills/confluence-crawler/test_check_sso_login.py`. Catalogue lint tests cover acceptance and rejection of that phrase. Both consumer eval harnesses cover headless recovery before user-run manual capture. The setup-helper check allowance and consumer recovery behavior remain unchanged.

## Readiness

- **Route:** direct-light. One work-loop session, no spec.
- **First slice:** align all four phrase pins, add lint acceptance/rejection coverage, and update both consumer eval harnesses without changing credential behavior.
- **Agent-only proof:** 211 tests pass across catalogue lint and the two consumer check suites; a search finds no old phrase in authored runtime sources or tests. Generated projections are checked after integration regenerates them.
- **Manual dependency:** none. The change reaches `packs/` and `packages/agentbundle`, so it needs a pack version bump and the protected-tree RFC trailer.

## Riskiest assumption

**Riskiest assumption:** the four original pin sites (`lint.py`, two `SKILL.md` files, one test) must move together, with lint regression tests and both consumer eval harnesses. Tested agent-only by searching authored runtime sources and tests for the old phrase after the edit and running the catalogue lint and confluence-crawler tests.

## De-risk result

2026-11-05. Ran `grep -rIn "do not run any setup helper"` over the whole worktree (excluding `.git`, `node_modules`). Result: exactly four pin sites outside docs: `packages/agentbundle/agentbundle/catalogue_tooling/lint.py`, `packs/atlassian/.apm/skills/jira/SKILL.md`, `packs/atlassian/.apm/skills/confluence-crawler/SKILL.md`, and `test_check_sso_login.py`; the other two hits are this intent and the shipped spec text. No generated or installed copy carries the phrase. Verdict: supported. Those four sites were the phrase pins; the implementation also needs catalogue lint coverage and both consumer eval harnesses.
