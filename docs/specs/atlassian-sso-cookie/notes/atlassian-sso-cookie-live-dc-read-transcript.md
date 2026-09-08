# Atlassian SSO-cookie live Data Center read transcript

This packet preserves the deferred live evidence identified by
`atlassian-sso-cookie-live-dc-read-transcript`. It requires an approved
corporate-SSO Atlassian Data Center target and therefore cannot be settled with
a synthetic or public endpoint.

## Authorized operator run

In a supported environment, perform the frozen read-only flow: headed
registration, `get-cookies`, an authenticated Jira JQL read, and the
`sso-broker test` command. Record a redacted transcript containing:

- the tested repository revision and tool versions;
- the Data Center product and sanitized host classification;
- evidence that registration was headed and user-authorized;
- successful cookie retrieval and a successful authenticated JQL response;
- `sso-broker test` exit status zero; and
- expiry or recapture observations relevant to the run.

Do not record cookies, tokens, credentials, account identities, ticket content,
or private hostnames. After a successful transcript, separately decide whether
the observed `success_url` host behavior warrants hardening; this evidence
packet does not pre-authorize that product change.

