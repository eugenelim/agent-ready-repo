# ADR-0137: Catalogue authentication selects one provider without fallback

- **Status:** Accepted
- **Date:** 2026-09-30
- **Areas:** credentials, distribution, security
- **Reversibility:** low
- **Decision-makers:** AgentBundle maintainers
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0134 (`credbroker` dependency and skill-runtime direction);
  ADR-0135 (exact-machine `.netrc` provider); ADR-0136 (JFrog CLI provider)

## Decision summary

- **Decision:** `credbroker` will resolve one catalogue-access provider in fixed
  order; unavailable providers permit continued resolution, while a configured
  but broken provider or a failure after selection terminates the acquisition.
- **Because:** fallback after evidence of intended authentication can silently
  change identity or downgrade a protected request to anonymous access.
- **Applies to:** `catalogue+https://` and `archive+https://`.
- **Tradeoff accepted:** broken user-local configuration can stop an acquisition
  even when a lower-precedence provider could reach the target.
- **Revisit if:** authenticated retry negotiation can preserve the same
  target-bound identity without credential confusion or downgrade.

## Context

AgentBundle supports explicit bearer authentication, URL-matched JFrog
profiles, exact-machine `.netrc` records, and anonymous HTTPS. These inputs can
coexist. The resolver needs one stable order and a precise distinction between
"not configured for this target" and "configured but unsafe or unusable."

An unavailable provider supplies no evidence that it was intended for the
target. A configured-but-broken provider does supply that evidence, but cannot
be used safely. Treating both states as absence would hide damaged
configuration and could send a lower-precedence identity—or no identity—to the
same catalogue.

## Decision

> `credbroker` will select one provider for the initial normalized catalogue
> URL and will never fall back after configured intent or provider selection is
> established.

- **D1:** Resolution will run once against the initial normalized URL before
  either descriptor or archive retrieval.
- **D2:** Provider order will be: explicit
  `AGENTBUNDLE_HTTP_BEARER_TOKEN`; matching JFrog CLI profile; exact-machine
  `.netrc`; anonymous HTTPS.
- **D3:** An unset bearer variable, an absent `jf` executable when no explicit
  JFrog server was requested, successful JFrog discovery with no URL match, an
  absent `.netrc`, or a `.netrc` with no exact machine match makes that provider
  unavailable and permits evaluation of the next provider.
- **D4:** A present but unusable bearer value; failed, timed-out, malformed, or
  ambiguous JFrog discovery; an explicit JFrog server mismatch; unsupported
  JFrog topology or version; or a malformed, unsafe, or incomplete matching
  `.netrc` record is configured-but-broken and terminates resolution.
- **D5:** Provider discovery will not send a catalogue network request.
- **D6:** The first available provider will be selected. Anonymous HTTPS is the
  final available provider when every authenticated provider is unavailable.
- **D7:** The selected provider and its target binding will be pinned for the
  complete acquisition.
- **D8:** A descriptor and its resolved archive will use the same provider.
  Standalone `archive+https://` acquisition will likewise select only once.
- **D9:** Authentication failure, HTTP failure, subprocess failure, timeout,
  redirect rejection, response-limit failure, or other retrieval failure after
  selection is terminal. No lower-precedence provider will be evaluated.
- **D10:** Diagnostics may report a non-secret provider class and stable failure
  class but will not report provider-specific identifiers such as a JFrog
  server ID, usernames, credentials, authorization values, profile contents,
  or discovery payloads.
- **D11:** Tests will distinguish unavailable, configured-but-broken, selected,
  and retrieval-failed states for every provider and will assert exactly one
  selected provider and no fallback.

## Decision drivers

- Preserve the user's intended authentication identity.
- Prevent authenticated-to-anonymous downgrade.
- Keep descriptor and archive retrieval under one credential boundary.
- Make damaged local configuration visible instead of silently bypassing it.
- Preserve transparent operation when a provider is genuinely absent.

## Consequences

**Positive:**

- Provider behavior is deterministic when several credential sources exist.
- A broken higher-precedence provider cannot silently change the request's
  identity.
- Descriptor and archive retrieval cannot switch authentication mechanisms.
- Users without protected-catalogue configuration still reach anonymous HTTPS.

**Negative:**

- Malformed JFrog or `.netrc` configuration may block a request that could have
  succeeded through another provider.
- A user must repair or remove configured intent before a lower-precedence
  provider becomes eligible.
- Provider discovery needs typed availability and failure results instead of a
  simple optional credential.

**Revisit if:** authenticated retry negotiation can preserve the same
target-bound identity without credential confusion or downgrade.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** a provider-state matrix proves the fixed order, the complete
  unavailable/configured-broken distinction, one selection per acquisition,
  descriptor/archive provider class, and zero lower-provider attempts after
  any terminal state.
- **Owner:** AgentBundle maintainers

## Alternatives considered

- **Fall back after HTTP 401 or 403:** rejected because it can change identity
  or downgrade an authenticated request to anonymous.
- **Treat malformed configuration as provider absence:** rejected because it
  hides evidence that the user intended that provider for the target.
- **Ask AgentBundle to choose separately for each request:** rejected because a
  descriptor and its archive would not share one authentication boundary.
- **Store the selected provider in `catalogue.toml`:** rejected because
  repository content must not control user-local credential selection.

## References

- [Portable catalogue authentication architecture](../architecture/portable-catalogue-authentication.md)
- [ADR-0134: Catalogue authentication resolves through credbroker](0134-catalogue-auth-resolves-through-credbroker.md)
- [ADR-0135: Catalogue `.netrc` uses exact machine matches](0135-catalogue-netrc-uses-exact-machine-matches.md)
- [ADR-0136: Catalogue JFrog authentication delegates to JFrog CLI](0136-catalogue-jfrog-auth-delegates-to-jfrog-cli.md)
