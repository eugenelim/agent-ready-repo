# Live credential transcripts

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/atlassian-sso-cookie AC19](../../specs/atlassian-sso-cookie/spec.md)

## Outcome

Credential and SSO-cookie flows have the live platform evidence needed to complete their deferred validation decisions.

## Opportunity

No real credential-broker platform transcript is recorded, and the deferred live-DC result is the decision gate for a defense-in-depth SSO URL validation question.

## What this absorbs

### atlassian-sso-cookie-success-url-pattern-host-confinement

After `atlassian-sso-cookie-live-dc-read-transcript` completes, decide whether the broker capture layer should tighten `success_url_pattern` host validation. The consumer’s `_sso.validate_https_url` validates only the `https` scheme for `success_url_pattern`; it does not confine that host to `cookie_domains`. `login_url` can legitimately use an off-domain IdP, so a blanket host-in-domains rule does not apply uniformly. Cookie-send confinement is independently enforced by AC4, AC5, AC6, and AC20. This is defense in depth only under RFC-0084 and cannot become a same-principal destination boundary. `docs/specs/atlassian-sso-cookie/spec.md:220` retains deferred AC19. Unblocks when the live-DC transcript is complete.

## Assumptions

- The sibling register entry `credential-broker-contract-manual-qa` covers the
  same six platform-by-mode transcripts and was deliberately NOT absorbed here:
  `creds` × macOS, Windows, and Linux; and `sso-cookie` × macOS, Windows, and
  Linux. It records them under `docs/specs/credential-broker-contract/notes/`.
  Every row must use its real platform store and an approved corporate-SSO
  endpoint, and record PAT resolution plus `sso-broker` test exit 0.
  `docs/specs/credential-broker-contract/spec.md:258` says no
  `notes/manual-qa-*.md` transcript is recorded yet; it settles when all six
  rows are recorded. `tests/roster/test_credential_broker_contract_docs.py`
  asserts that exact slug is present in `workspace.toml`, as the oracle for AC42
  of the shipped credential-broker-contract spec; absorbing it would orphan a
  ticked criterion in a frozen body. Whichever session picks this slice up
  should settle both.

- Both items need dated live observations: six real platform-store and approved corporate-SSO transcripts for the broker contract, and the live-DC transcript to establish actual broker behavior for `success_url_pattern` hosts.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
