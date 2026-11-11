# ADR-0136: Catalogue `.netrc` uses exact machine matches

- **Status:** Accepted
- **Date:** 2026-09-30
- **Areas:** credentials, security
- **Reversibility:** low
- **Decision-makers:** AgentBundle maintainers
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0135 (`credbroker` owns protected-catalogue credential
  resolution); ADR-0138 (provider precedence and terminal failures)

## Decision summary

- **Decision:** Protected catalogue access through `.netrc` will use only an
  exact machine key derived from the normalized target URL.
- **Because:** the `.netrc` `default` record is too broad for a fetch that
  selects executable agent content and records its provenance.
- **Applies to:** direct HTTP acquisition for `catalogue+https://` and
  `archive+https://` when `credbroker` selects `.netrc` authentication.
- **Tradeoff accepted:** a user whose credentials exist only in a `default`
  record must add an explicit host entry.
- **Revisit if:** a standard target-bound credential mechanism replaces
  `.netrc` for portable HTTP catalogue access.

## Context

`.netrc` is a standard user-owned source of HTTP Basic credentials. Many tools
already consult it, so using it lets AgentBundle work with organization-provided
credentials without adding AgentBundle-specific settings or putting secrets in
`catalogue.toml`.

A `.netrc` file may also contain a `default` record that applies whenever no
machine name matches. Catalogue acquisition determines which skills and agent
instructions enter a workspace. Sending a broad fallback credential during
that fetch would bind a secret to less context than the catalogue target itself.

## Decision

> `credbroker` will resolve `.netrc` credentials only through exact machine
> keys derived from the normalized target URL.

- **D1:** `credbroker` will inspect only the standard per-user `.netrc` location
  selected by Python's `netrc` contract. It will not inspect a repository-local
  file, the current working directory, or a path supplied by catalogue content.
- **D2:** For an HTTPS URL with a non-default port, lookup order will be the
  exact `host:port` key followed by the exact `host` key. For default port 443,
  only the exact `host` key will be checked.
- **D3:** The `.netrc` `default` record will never authenticate a catalogue
  request.
- **D4:** An exact record is usable only when both `login` and `password` are
  present. The optional `account` field will not affect authentication.
- **D5:** The resulting HTTP Basic authorization value may be sent only to the
  normalized origin from which it was derived.
- **D6:** Same-origin HTTPS redirects may retain authorization. A cross-origin
  redirect or a redirect to a non-HTTPS scheme will be rejected before the
  redirected request is sent.
- **D7:** An absent file or absent exact match makes this provider unavailable.
  A malformed file, unsafe POSIX permissions, or an incomplete exact record is
  a configured-but-broken condition that terminates provider resolution rather
  than making this provider unavailable.
- **D8:** `.netrc` paths, machine names, login names, passwords, derived
  authorization values, and provider-specific identifiers will not appear in
  catalogue state, provenance, receipts, or logs. Diagnostics may name the
  non-secret `.netrc` provider class.

## Decision drivers

- Reuse a credential source users and organization tooling already maintain.
- Bind every credential to a specific requested network target.
- Keep secrets out of repository configuration and generated catalogue state.
- Preserve the existing same-origin redirect boundary for direct HTTP fetches.

## Consequences

**Positive:**

- Users with an exact host entry gain protected catalogue access without new
  AgentBundle-specific configuration.
- A broad `default` record cannot leak credentials to a newly configured or
  mistyped catalogue host.
- Non-default ports can have distinct credentials without making the common
  host-only record unusable.

**Negative:**

- Existing tools that accept `.netrc` `default` may work where AgentBundle
  deliberately refuses authentication.
- Users relying only on `default` must add an exact machine entry.
- A malformed or insecure user file stops the selected authenticated fetch
  rather than falling back to anonymous access.

**Revisit if:** a standard target-bound credential mechanism replaces
`.netrc` for portable HTTP catalogue access.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** isolated-home fixtures cover default port, non-default port,
  host fallback, `default`-only, incomplete, malformed, unsafe-permission, and
  redirect cases, and assert that no sensitive value reaches diagnostics or
  persisted state.
- **Owner:** AgentBundle maintainers

## Alternatives considered

- **Accept the `.netrc` `default` record:** rejected because it is not bound to
  the catalogue target.
- **Read a repository-local `.netrc`:** rejected because repository content must
  not select credentials used to acquire executable agent content.
- **Add username and password fields to AgentBundle settings:** rejected because
  it creates a new secret store and risks committing credentials.
- **Support only JFrog CLI profiles:** rejected because portable catalogues also
  need standard HTTP authentication outside JFrog-managed environments.

## References

- [Portable catalogue authentication architecture](../architecture/portable-catalogue-authentication.md)
- [Python `netrc` documentation](https://docs.python.org/3/library/netrc.html)
