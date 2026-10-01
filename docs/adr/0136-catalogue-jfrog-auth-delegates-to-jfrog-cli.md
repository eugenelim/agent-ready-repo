# ADR-0136: Catalogue JFrog authentication delegates to JFrog CLI

- **Status:** Accepted
- **Date:** 2026-09-30
- **Areas:** credentials, distribution, security
- **Reversibility:** low
- **Decision-makers:** AgentBundle maintainers
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0134 (`credbroker` owns protected-catalogue credential
  resolution); ADR-0137 (provider precedence and terminal failures)

## Decision summary

- **Decision:** JFrog-hosted catalogue acquisition will use a URL-matched JFrog
  CLI profile by delegating each bounded request to `jf api`.
- **Because:** JFrog CLI already owns login, token refresh, proxy handling, and
  credential storage, so AgentBundle and `credbroker` should not extract or copy
  its tokens.
- **Applies to:** `catalogue+https://` descriptors and `archive+https://`
  archives whose initial normalized URL matches a supported JFrog profile.
- **Tradeoff accepted:** redirect and token handling inside the child process
  remain owned by JFrog CLI after strict profile and endpoint binding.
- **Revisit if:** JFrog removes the required CLI commands or publishes a safer
  supported library API that preserves credential ownership and target binding.

## Context

Organizations commonly provision protected Artifactory access with `jf login`
or another JFrog CLI configuration flow. The resulting profile may contain or
refresh credentials that other tools should not read. Copying a token into an
AgentBundle-specific variable would add user setup, create another secret
lifecycle, and bypass the vendor's refresh behavior.

Delegating a request to JFrog CLI preserves that ownership but moves HTTP,
proxy, and redirect behavior into a child process. AgentBundle therefore needs
a strict, non-secret discovery contract that binds the initial catalogue URL to
one profile and confines both descriptor and archive requests beneath that
profile's Artifactory base before delegation.

## Decision

> Catalogue retrieval will delegate matching Artifactory requests to a
> configured JFrog CLI profile without extracting its credentials.

- **D1:** `credbroker` will discover profiles with one bounded
  `jf config show --format=json` invocation. Unmasked credentials will never be
  requested; after bounded JSON parsing, every field except `serverId`, platform
  URL, Artifactory URL, and default-profile status will be ignored immediately.
- **D2:** A profile is eligible only when its normalized Artifactory URL is an
  exact-origin, path-segment prefix of the initial normalized catalogue URL.
- **D3:** The Artifactory URL must itself be a same-origin, path-segment
  descendant of the profile's normalized platform URL. A split-origin or
  otherwise incompatible topology is unsupported.
- **D4:** The profile with the longest matching Artifactory path prefix wins.
  Equal-length matches are ambiguous unless `JFROG_CLI_SERVER_ID` names one of
  those matches; the named profile must still satisfy every URL check.
- **D5:** Selection will pin the server identifier, platform base, and
  Artifactory base for the whole acquisition. Discovery will not be repeated
  between descriptor and archive fetches.
- **D6:** Each descriptor and archive URL will be normalized and revalidated
  beneath the pinned Artifactory base. The `jf api` endpoint will then be
  derived relative to the pinned platform base.
- **D7:** User information, query strings, fragments, dot-segment ambiguity,
  encoded path separators, backslashes, and control characters in a candidate
  URL will be rejected before any JFrog request.
- **D8:** After a profile matches, a bounded `jf --version` probe must report
  JFrog CLI 2.105.0 or later. This is the first documented version that supports
  both `jf api` and the `jf config show --format=json` discovery contract. An
  incompatible version or unsupported topology
  fails the acquisition and does not fall through to `.netrc` or anonymous
  access.
- **D9:** Subprocess limits will be 10 seconds for discovery, 5 seconds for the
  version probe, and 30 seconds for each of at most two `jf api` calls, within a
  75-second aggregate subprocess budget. Calls will not use a shell, will close
  standard input, will cap standard output and error, will terminate on timeout,
  and will sanitize diagnostics.
- **D10:** The descriptor output limit will remain 1 MiB and the archive output
  limit will remain 256 MiB. Exceeding either limit fails acquisition.
- **D11:** After target and endpoint binding, JFrog CLI owns authentication,
  token refresh, proxy behavior, TLS handling, and redirects inside its process.
- **D12:** AgentBundle and `credbroker` will never request, parse, store, log,
  or pass a JFrog access token or password.

## Decision drivers

- Reuse organization-managed JFrog login state without another user credential.
- Leave token storage and refresh with the vendor tool that created the profile.
- Bind authentication to one validated Artifactory URL hierarchy.
- Keep discovery and retrieval bounded, non-interactive, and diagnosable without
  exposing secrets.
- Fail closed when profile selection or supported topology is ambiguous.

## Consequences

**Positive:**

- A user who has already completed `jf login` needs no AgentBundle-specific
  bearer token.
- AgentBundle and `credbroker` never take custody of JFrog credentials.
- Profile selection is reproducible across descriptor and archive retrieval.
- Downstream GitLab or other organization-owned distributions can use the same
  contract without GitHub-specific authentication.

**Negative:**

- JFrog-backed acquisition requires a compatible `jf` executable in addition
  to the AgentBundle and `credbroker` Python packages.
- Split-origin JFrog topologies remain unsupported until their binding can be
  proven safely.
- JFrog CLI, not AgentBundle, controls redirects and network behavior after the
  bounded request is delegated.
- Process startup and discovery add latency, with a worst-case 75-second
  subprocess budget for one complete acquisition.

**Revisit if:** JFrog removes the required CLI commands or publishes a safer
supported library API that preserves credential ownership and target binding.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** fixtures and a compatible real JFrog CLI exercise unique,
  ambiguous, explicit-ID, longest-prefix, topology, endpoint-escape, version,
  timeout, output-limit, diagnostic-redaction, and no-fallback cases without
  exposing a credential to AgentBundle.
- **Owner:** AgentBundle maintainers

## Alternatives considered

- **Read credentials from JFrog configuration:** rejected because it makes
  AgentBundle responsible for vendor-owned secret formats and refresh behavior.
- **Require an AgentBundle bearer token:** rejected because it adds user setup
  and a second secret lifecycle for users who already have a JFrog profile.
- **Use `jf rt download`:** rejected because repository-path commands do not
  preserve the transport's existing descriptor and arbitrary archive URL model
  as directly as a bounded API endpoint does.
- **Copy a JFrog token into a direct REST request:** rejected because token
  extraction crosses the vendor-owned credential boundary and bypasses vendor
  refresh behavior.

## References

- [Portable catalogue authentication architecture](../architecture/portable-catalogue-authentication.md)
- [JFrog CLI login documentation](https://docs.jfrog.com/integrations/docs/jf-login)
- [JFrog CLI API endpoint documentation](https://docs.jfrog.com/integrations/docs/use-api-endpoints-via-cli)
