# ADR-0134: Catalogue authentication resolves through credbroker

- **Status:** Accepted
- **Date:** 2026-09-30
- **Areas:** credentials, distribution, packaging
- **Reversibility:** low
- **Decision-makers:** AgentBundle maintainers
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0003 (credentialed skills use broker contracts without an
  AgentBundle runtime); ADR-0026 (`credbroker` extension precedent); ADR-0135
  (exact-machine `.netrc` provider); ADR-0136 (JFrog CLI provider); ADR-0137
  (provider precedence and terminal failures)

## Decision summary

- **Decision:** AgentBundle will use a required `credbroker` dependency for
  protected catalogue acquisition, while credential-aware skills use
  `credbroker` directly and never depend on AgentBundle.
- **Because:** the first protected fetch must work before a pack can be
  installed, without giving AgentBundle a second credential implementation or
  making it part of the skill runtime.
- **Applies to:** authentication for `catalogue+https://` and
  `archive+https://`, plus the dependency direction between AgentBundle,
  `credbroker`, and installed skills.
- **Tradeoff accepted:** AgentBundle and credential-aware skill environments
  may carry independently managed `credbroker` copies, while a co-located
  Python install can make AgentBundle's copy override the skill's vendored
  floor and therefore requires a compatibility window.
- **Revisit if:** a provider-neutral platform credential API can satisfy first
  fetch and skill-runtime use without a package dependency or duplicated
  credential logic.

## Context

AgentBundle is an installation and catalogue tool. It is not a runtime for the
skills it installs. Ordinary skills must continue to run without AgentBundle or
`credbroker`, while a skill that manages credentials needs `credbroker` as its
own lower-level runtime component.

Protected catalogue acquisition happens before any pack can be installed. The
`credential-brokers` pack therefore cannot bootstrap authentication for the
first protected fetch. AgentBundle needs the credential resolver in its own
tool environment, including when a package manager such as `pipx` or `uv tool`
isolates that environment from every skill runtime.

This decision does not apply to a catalogue source acquired from a local path
or Git repository. Those transports retain their own authentication behavior,
including Git credential helpers and SSH. A public `catalogue+https://` or
`archive+https://` source still traverses the HTTPS fetch path, but uses
anonymous access when no user-local credential provider matches; it requires no
authentication setup.

The portable catalogue authentication design originally proposed a narrow
direct credential-boundary exception inside AgentBundle. That would duplicate
credential selection and secret-handling logic already owned by `credbroker`.
This record resolves that open point in favor of a standalone `credbroker`
public API shared by two independent consumers.

## Decision

> AgentBundle will depend on `credbroker` and use its target-bound HTTP-access
> resolver for every protected HTTPS catalogue fetch; skills will use
> `credbroker` directly and will never require AgentBundle at runtime.

- **D1:** The AgentBundle distribution will declare `credbroker>=0.7,<0.8` as a
  required runtime dependency. Installing AgentBundle through a Python package
  manager therefore installs a compatible `credbroker` in the same tool
  environment without a second user action.
- **D2:** `credbroker` will remain a standalone lower-level package. It must not
  import, invoke, discover, or otherwise depend on AgentBundle.
- **D3:** A skill must not import, invoke, discover, or otherwise depend on
  AgentBundle at runtime. Installing a skill through AgentBundle does not make
  AgentBundle part of that skill's execution contract.
- **D4:** Only credential-aware skills require `credbroker`. Ordinary skills
  require neither AgentBundle nor `credbroker` at runtime.
- **D5:** The `credential-brokers` pack, or an equivalent organization-owned
  deployment, will supply `credbroker` to a credential-aware skill runtime
  independently of AgentBundle's tool environment.
- **D6:** The AgentBundle tool environment and the skill runtime are logically
  separate deployment contexts. They may be isolated, or they may be
  physically co-located in one Python environment. In the co-located shape, a
  `site-packages` installation of `credbroker` takes precedence over the
  credential-brokers pack's user-library floor.
- **D7:** `credbroker` will expose
  `resolve_http_access(target_url, *, env)`. Its closed typed result will
  represent explicit target-bound bearer authentication, JFrog CLI delegation,
  exact-machine `.netrc` Basic authentication, or anonymous access. A separate
  provider-selection decision owns precedence and failure semantics.
- **D8:** A non-secret provider class may appear in diagnostics. A
  provider-specific identifier such as a JFrog server ID, credentials,
  authorization values, and authentication material will not be written to
  catalogue configuration, lock state, provenance, receipts, or logs.
- **D9:** The installing package manager owns AgentBundle's environment.
  AgentBundle will not mutate or silently upgrade that environment while it is
  running. A fresh install receives the newest compatible `credbroker`; an
  existing compatible version may remain until the package manager upgrades it
  or an AgentBundle release raises the minimum required version.
- **D10:** A required compatibility or security fix will be carried by a
  `credbroker` release and, when existing AgentBundle installations must take
  it, an AgentBundle release that raises the dependency floor. The
  credential-aware skill deployment will update its own copy through its pack
  or organization-owned release path.
- **D11:** The `credbroker` 0.7 series will preserve the skill-facing public API
  shipped by 0.6 while any supported credential-brokers pack can be co-located
  with AgentBundle's `credbroker>=0.7,<0.8` dependency. A future breaking
  skill-facing API requires either import isolation or a new compatibility
  decision before AgentBundle can raise its dependency range.
- **D12:** Architecture fitness tests will exercise three deployment shapes:
  an isolated AgentBundle installation with `credbroker` installed as its
  dependency; an isolated credential-aware skill runtime with `credbroker`
  present and AgentBundle absent; and a co-located environment in which the
  newest compatible AgentBundle dependency overrides a vendored 0.6 floor
  while an existing credential-aware skill still runs.

## Decision drivers

- Protected catalogues must work on the first fetch, before pack installation.
- Credential resolution and secret handling need one implementation owner.
- Skills must remain portable across installers and must not acquire an
  AgentBundle runtime dependency.
- Standard package managers should handle AgentBundle's dependency without
  new per-user setup.
- Tool and skill environments must remain independently deployable and
  upgradeable.
- Co-located Python environments must not break existing credential-aware
  skills when `site-packages` overrides the vendored user-library floor.

## Consequences

**Positive:**

- AgentBundle gains transparent protected-catalogue authentication without
  owning another credential store or resolver.
- Credential-aware skills use the same lower-level contract without importing
  the installer that delivered them.
- `pip`, `pipx`, `uv`, and downstream Python distributions can resolve the
  AgentBundle-side dependency through ordinary package metadata.
- Tests can prove that skills remain independent by omitting AgentBundle from
  the skill-runtime environment.

**Negative:**

- AgentBundle is no longer a dependency-free Python distribution.
- A downstream mirror that publishes AgentBundle must also publish a
  compatible `credbroker` distribution.
- AgentBundle and a credential-aware skill may carry separate copies whose
  patch releases move on different schedules.
- The 0.7 series must retain the prior skill-facing API for the supported
  co-location window even when AgentBundle itself needs only the new HTTP
  access API.
- A security fix that must reach both contexts requires two release paths: the
  AgentBundle package dependency and the skill-runtime deployment.

**Revisit if:** a provider-neutral platform credential API can satisfy first
fetch and skill-runtime use without a package dependency or duplicated
credential logic.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** package metadata installs `credbroker` into a clean isolated
  AgentBundle environment; a credential-aware skill runs with `credbroker`
  present and AgentBundle absent; and a co-located test proves the newest
  compatible AgentBundle dependency still serves a skill written against the
  vendored 0.6 public API.
- **Owner:** AgentBundle maintainers

## Alternatives considered

- **Implement credential resolution directly in AgentBundle:** rejected because
  it creates a second blessed credential boundary and duplicates secret-handling
  behavior.
- **Make `credbroker` an optional AgentBundle extra:** rejected because protected
  catalogue access would fail until each user or organization installed an
  additional feature, defeating transparent reuse of existing credentials.
- **Vendor `credbroker` inside the AgentBundle wheel:** rejected because it
  creates a second code copy and obscures dependency and security-update
  ownership.
- **Rely on the `credential-brokers` pack:** rejected because a pack cannot
  authenticate the protected fetch needed to acquire itself.
- **Make skills call AgentBundle for credentials:** rejected because it turns an
  installer into a skill runtime and makes skills less portable.

## References

- [Portable catalogue authentication architecture](../architecture/portable-catalogue-authentication.md)
- [Credential subsystem architecture](../architecture/credentials.md)
