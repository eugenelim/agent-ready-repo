# Live credential transcripts

- **Slug:** `live-credential-transcripts`
- **Status:** Withdrawn
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [spec/atlassian-sso-cookie AC19](../../specs/atlassian-sso-cookie/spec.md)

## Disposition — withdrawn 2026-11-05, decided: no tightening; the manual transcripts stay with their captured item

**Do not shape this intent.** The `success_url_pattern` question is decided: do not tighten host validation in the broker capture layer. Cookie sending is already confined by AC4, AC5, AC6 and AC20 of `atlassian-sso-cookie`, `login_url` may legitimately use an off-domain identity provider, and under RFC-0084 a capture-layer check is defense in depth that cannot become a same-principal boundary. The six platform transcripts need real platform stores and an approved corporate-SSO endpoint, so no agent session can record them. They stay tracked by the open captured item `credential-broker-contract-manual-qa`, which is the oracle for AC42 of `credential-broker-contract`. Two follow-ups are left for the owner, neither blocking: amend AC42 to accept a CI operating-system matrix for the `creds` rows, and mark deferred AC19 of `atlassian-sso-cookie` as won't-do. Both edit frozen spec text and the roster test `tests/roster/test_credential_broker_contract_docs.py` together. Reopen if a live-DC transcript shows the broker captured a cookie for a host outside `cookie_domains`.

## Outcome

Credential and SSO-cookie flows have the live platform evidence needed to complete their deferred validation decisions.

## Opportunity

No real credential-broker platform transcript is recorded, and the deferred live-DC result is the decision gate for a defense-in-depth SSO URL validation question.

## What this absorbs

### atlassian-sso-cookie-success-url-pattern-host-confinement

After `atlassian-sso-cookie-live-dc-read-transcript` completes, decide whether the broker capture layer should tighten `success_url_pattern` host validation. The consumer’s `_sso.validate_https_url` validates only the `https` scheme for `success_url_pattern`; it does not confine that host to `cookie_domains`. `login_url` can legitimately use an off-domain IdP, so a blanket host-in-domains rule does not apply uniformly. Cookie-send confinement is independently enforced by AC4, AC5, AC6, and AC20. This is defense in depth only under RFC-0084 and cannot become a same-principal destination boundary. `docs/specs/atlassian-sso-cookie/spec.md` retains deferred AC19. Unblocks when the live-DC transcript is complete.

## Assumptions

- The sibling captured item `docs/product/captured/credential-broker-contract-manual-qa.md` covers the
  same six platform-by-mode transcripts and was deliberately NOT absorbed here:
  `creds` × macOS, Windows, and Linux; and `sso-cookie` × macOS, Windows, and
  Linux. It tracks the six rows; the transcripts go under `docs/specs/credential-broker-contract/notes/`.
  Every row must use its real platform store and an approved corporate-SSO
  endpoint, and record PAT resolution plus `sso-broker` test exit 0.
  `docs/specs/credential-broker-contract/spec.md` (AC42) says no
  `notes/manual-qa-*.md` transcript is recorded yet; it settles when all six
  rows are recorded. `tests/roster/test_credential_broker_contract_docs.py`
  asserts that the captured item carries all six rows, as the oracle for AC42
  of the shipped credential-broker-contract spec; absorbing it would orphan a
  ticked criterion in a frozen body. Whichever session picks this slice up
  should settle both.

- Both items need dated live observations: six real platform-store and approved corporate-SSO transcripts for the broker contract, and the live-DC transcript to establish actual broker behavior for `success_url_pattern` hosts.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
