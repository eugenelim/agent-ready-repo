# SSO-cookie lint wording matches the check carve-out

- **Slug:** `sso-cookie-lint-contract-wording`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **De-risked:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

Catalogue lint wording accurately forbids automatic SSO setup while preserving the shipped non-mutating check carve-out.

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

This intent absorbs sso-cookie-lint-phrase-amendment. The currently pinned phrase says not to run any setup helper, while the shipped check carve-out permits the non-mutating check path, so the literal guidance contradicts the enforced behavior.

## Assumptions

- This is a wording and test-contract correction, not authorization for a new credential operation.
- A protected AgentBundle change requires accepted Engine-Change-RFC authority at landing time.


## Source

- Mode: repo-origin
- Locator: docs/specs/jira-check-sso-auto-login/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

## Current truth

Verified 2026-11-05: the phrase `do not run any setup helper for them` is pinned in four places, not one: `packages/agentbundle/agentbundle/catalogue_tooling/lint.py:839`, `packs/atlassian/.apm/skills/jira/SKILL.md:169`, `packs/atlassian/.apm/skills/confluence-crawler/SKILL.md:140`, and the test `packs/atlassian/tests/skills/confluence-crawler/test_check_sso_login.py:670`. All four change together.

## Readiness

- **Route:** direct-light. One work-loop session, no spec.
- **First slice:** amend the phrase to carve out the non-mutating check path, in all four places.
- **Agent-only proof:** the confluence-crawler check test and the catalogue lint test pass; a grep finds no old phrase.
- **Manual dependency:** none. The change reaches `packs/` and `packages/agentbundle`, so it needs a pack version bump and the protected-tree RFC trailer.

## Riskiest assumption

**Riskiest assumption:** the four pin sites (`lint.py`, two `SKILL.md` files, one test) are the only ones. Tested agent-only by grepping the whole tree for the old phrase after the edit and running the catalogue lint and confluence-crawler tests.

## De-risk result

2026-11-05. Ran `grep -rIn "do not run any setup helper"` over the whole worktree (excluding `.git`, `node_modules`). Result: exactly four pin sites outside docs: `packages/agentbundle/agentbundle/catalogue_tooling/lint.py`, `packs/atlassian/.apm/skills/jira/SKILL.md`, `packs/atlassian/.apm/skills/confluence-crawler/SKILL.md`, and `test_check_sso_login.py`; the other two hits are this intent and the shipped spec text. No generated or installed copy carries the phrase. Verdict: supported. The four sites are the complete edit list.
