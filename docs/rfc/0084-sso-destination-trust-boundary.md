# RFC-0084: Single sign-on destination trust boundary

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-11
- **Date closed:** 2026-08-11
- **Decision weight:** heavy
- **Related:** [RFC-0035](0035-sso-cookie-auth-for-atlassian-pack.md),
  [RFC-0083](0083-work-intake-and-artifact-routing.md),
  [ADR-0026](../adr/0026-sso-consumer-resolution-in-credbroker.md),
  [credential architecture](../architecture/credentials.md), and the
  [`jira-check-sso-auto-login` spec](../specs/jira-check-sso-auto-login/spec.md).
  Consolidates and closes the backlog items
  `sso-destination-field-integrity`, `sso-privilege-separated-config`,
  `sso-branch2-destination-attestation`, and
  `sso-live-browser-destination-derivation`.

## Reviewer brief

- **Decision:** What destination security can the catalogue actually provide
  when installation is limited to a user-scoped Python package and projected
  skill scripts?
- **Accepted outcome:** The deployment boundary is accepted and the four
  local-enforcement proposals are retired.
- **Effect:** Generic headed single sign-on (SSO) cookie capture
  remains operator-only and explicitly unprotected from a hostile process
  running under the agent principal. No second Python package or implementation
  spec is created. Protocol-backed modes require a future proposal tied to a
  supported consumer.
- **Affected surface:** SSO-cookie security contract, credential architecture,
  the shipped `jira-check-sso-auto-login` spec, and `workspace.toml`; no runtime
  code changes.
- **Stakes:** The repository must not promise a same-principal security boundary
  it cannot deploy, but it must also avoid turning the limitation into permission
  for automated credential entry.
- **Review focus:** Whether the recorded generic-cookie limitation is more
  accurate than retaining unbuildable enforcement work.
- **Not in scope:** Adding administrator-installed software, a browser extension,
  a local service, or a new authentication protocol.

## The ask

**Recommendation (bottom line up front).** Do not build a destination enforcer
inside the current credential-brokers distribution. Everything the catalogue can
install today—the `credbroker` package, its vendored floor, `sso-broker.py`, and
skill scripts—is writable or bypassable by the same operating-system principal
as the agent. A second package, virtual environment, signed data file, or
additional in-process check would add complexity without creating independent
authority.

Keep generic headed cookie capture as an explicitly operator-invoked
compatibility mode. Keep automatic refresh headless. Preserve destination
derivation as defense in depth, but describe hostile same-principal destination
poisoning as an accepted limitation rather than deferred implementation work.

In this RFC, **capture** means navigating a browser through login, waiting for a
declared success URL, and storing the resulting cookies. A **headed** capture
shows an interactive browser in which a human can enter credentials; a
**headless** capture has no human-facing window. The **destination** is the login
journey: its initial URL, interactive origins (scheme, host, and port), and
success condition. The **agent principal** is the operating-system account under
which agent-controlled code runs. The **operator** is the human who types a
registration command and controls the visible browser; this is an action role,
not a separate operating-system identity. An **erring agent** follows supported
catalogue workflows but can make a mistake; a **hostile same-principal process**
can modify or bypass those workflows intentionally.

| ID | Question | Decision | Why | Disposition |
| --- | --- | --- | --- | --- |
| D1 | What boundary does the baseline distribution provide? | None against a hostile agent principal; retain the current erring-agent protection only. | User-scoped Python and scripts cannot constrain code running as their owner. | Accepted limitation. |
| D2 | What happens to generic headed cookie capture? | Keep it operator-only; never permit an automatic path to display login UI. | It preserves compatibility without creating a new agent-triggered credential-harvesting capability. | Baseline workflow contract. |
| D3 | What future secure modes remain possible? | Permit a new proposal only for a remotely bound authorization protocol supported by a concrete consumer, or after the deployment envelope admits a protected component. | The remote issuer or protected installation—not another Python package—would supply the missing authority. | Future intake only; no implementation authorized. |
| D4 | How is the workspace consolidated? | Remove all four entries and replace their spec and survey deferral language with an accepted limitation. | There is no actionable baseline implementation to schedule. | Closed rather than blocked. |

## Problem & goals

The SSO-cookie broker can render a browser so an operator can complete a
corporate login. The initial URL and success condition currently arrive through
`sso-config.toml`, a file editable by the installing user. The broker executable,
its Python library, and its stored profile also live under that user's authority.
Agent-controlled code running as that user can change the destination, replace
the verifier, invoke the engine directly, or launch another browser.

The browser holds authority supplied by a human login while a less-trusted
caller can name its destination. The Internet Engineering Task Force describes
the underlying cookie problem as separating designation in a URL from
authorization in ambient cookies ([RFC 6265, section 8.2](https://www.rfc-editor.org/rfc/rfc6265.html#section-8.2)).
Here the possible authority being acquired includes an identity-provider
password and multi-factor authentication, not merely an existing cookie.

The original four findings proposed integrity-protected fields, separated
configuration, another derivation branch, and live-browser derivation. Their
shared assumption was that a component inside the supported installation could
enforce the result. The installation sweep disproved that assumption.

In that installation, the **vendored floor** is the fallback copy of the
`credbroker` Python library written to `~/.agentbundle/lib/credbroker/`.
`sso-broker.py` is written to `~/.agentbundle/bin/`, and **projected skill
scripts** are catalogue-owned script files copied into the installed skills.
All are installed for, owned by, and executed as the same user account as the
agent principal.

### Goals

- State exactly what the baseline distribution does and does not protect.
- Prevent automatic code paths from rendering an agent-influenced login page.
- Retain useful mismatch detection without calling it independent authority.
- Close four unbuildable proposals instead of leaving them as misleading work.
- Define what evidence would justify a new proposal later.

### Non-goals

- Add another user-scoped Python package, virtual environment, or signed policy.
- Require administrator installation, a local service, or a browser extension.
- Replace generic SSO cookies with OAuth or OpenID Connect for deployments that
  do not support those protocols.
- Change capture, refresh, storage, or consumer behavior in this RFC.
- Defend the rest of the credential subsystem from a hostile same-principal
  process; that broader limitation remains accepted.

## Proposal

### 1. Make the deployment boundary normative

The baseline credential-brokers installation provides no destination security
boundary against hostile code running as the installing user. This is a
deployment fact, not a missing validation rule.

The following do not change that fact:

- another package or virtual environment installed by the same user;
- a root-owned or signed policy read by a user-writable verifier;
- origin comparison, server derivation, or live browser state observed by the
  same mutable engine;
- prompts, tool hooks, or instructions rendered by agent-controlled code; or
- isolating Python imports while leaving the executable and policy replaceable
  or bypassable.

A Python implementation could become a real boundary only if its code, policy,
interpreter path, and invocation contract were protected by another privilege.
That is an administrator-installed component even if its source language is
Python, and it is outside the supported installation envelope.

### 2. Retain generic cookie capture as an operator-only compatibility mode

Within supported catalogue workflows, interactive first capture remains
reachable only through an operator-typed registration action. This is a
workflow contract, not operating-system enforcement against a hostile
same-principal process. Capture retains the current derivation, HTTPS checks,
origin comparison, and success-condition validation as defense in depth. The
derivation asks the configured service for a candidate authorization origin and
compares that origin with the configured login origin; because the service and
login values are editable together, it catches mistakes but is not independent
authority. Documentation must not describe it as protection from hostile
same-principal destination poisoning.

Automatic refresh remains structurally headless and accepts only a profile
selector. If the stored browser state cannot complete authentication without a
human, refresh fails and directs the operator to the explicit registration
workflow. No automatic path may fall back to a visible login page.

This is the effort's security outcome: preserve the useful workflow while
refusing to automate the one action that could acquire credentials the agent did
not already possess.

### 3. Do not create another local enforcer package

`credbroker` is already delivered both as a pip-installed package and as a
user-scope vendored floor. `sso-broker.py` is projected to the same user's
`~/.agentbundle/bin`. Splitting destination checks into another distribution
would change packaging but not ownership, mutability, or bypassability.

The four original proposals are therefore closed as standalone work:

- destination-field integrity cannot help when the verifier can be replaced;
- privilege-separated config is not privilege-separated when installed at user
  scope;
- branch-2 attestation would add a check to the common topology in which the
  configured login and service hosts are equal, but would still compare
  agent-controlled designations; and
- live-browser derivation is not independent when the agent controls the
  browser and can launch a different one.

### 4. Treat protocol-backed authentication as a different future capability

For a service that supports it, a future `credbroker` mode could open the
system browser and receive a Proof Key for Code Exchange (PKCE)-bound
authorization response. Native-app guidance requires an external user agent and
a registered redirect back to the client
([RFC 8252](https://www.rfc-editor.org/rfc/rfc8252.html)). A device authorization
flow can instead have the user approve a short-lived code through an
authorization server while the client polls for the result
([RFC 8628](https://www.rfc-editor.org/rfc/rfc8628.html)).

In those modes, the authorization server supplies the independent binding and
returns a token. They do not generically return an arbitrary browser's Security
Assertion Markup Language (SAML) session cookies and therefore do not replace
the current cookie-capture topology.

No such mode is authorized by this RFC. A concrete consumer with protocol
support must justify a new proposal, including issuer selection, client
registration, redirect binding, token storage, migration, and fallback. If the
catalogue later permits administrator-installed or externally trusted software,
that deployment change likewise requires a new proposal.

### 5. Close the workspace items as an accepted limitation

This change removes the four original entries from `workspace.toml`'s
`[backlog].open` list of schedulable work. The
[`jira-check-sso-auto-login` spec](../specs/jira-check-sso-auto-login/spec.md)
and its
[`agent-triggered-credential-capture` survey](../specs/jira-check-sso-auto-login/agent-triggered-credential-capture-survey.md)
retain the security finding but label it an accepted limitation under RFC-0084
rather than unresolved implementation work.

No implementation spec follows from this RFC. A later protocol-backed or
privileged design starts with new evidence and its own governance artifact; it
does not silently revive one of the closed backlog solutions.

## Options considered

The options are exhaustive along the relevant deployment axis: keep the
baseline as-is, rearrange code within the same principal, rely on a remote
authorization protocol, or introduce a separately protected local or external
component.

| Option | What it buys | Cost and disposition |
| --- | --- | --- |
| **A. Do nothing and retain four backlog proposals** | Avoids deciding whether any proposal is deployable. | Rejected: it advertises work that cannot meet its own security claim. |
| **B. Accept the baseline limitation** | Preserves generic cookie compatibility and the current install model without overstating protection. | Recommended: headed capture stays operator-only and automatic refresh stays headless. |
| **C. Add another user-scoped package or verifier** | Can centralize checks and reduce accidental misconfiguration. | Rejected as a security boundary: it remains mutable and bypassable by the agent principal. Existing derivation already supplies the warranted defense in depth. |
| **D. Add protocol-backed browser or device authorization** | Uses a remote authorization server to bind approval and keeps passwords outside the client. | Viable only for supported consumers; returns protocol credentials rather than generic SAML cookies. Requires a new proposal, not baseline work. |
| **E. Add a protected local helper, browser extension, or remote service** | Can place policy and enforcement outside the agent principal. | Technically viable but rejected from the baseline because it adds a privileged install or another deployed component. Revisit only if the deployment envelope changes. |

The policy-scope question from the original findings becomes conditional rather
than actionable. If a future protected local enforcer is proposed, its minimum
policy must bind the profile selector, initial login URL, allowed interactive
origins, and success condition. No current component is authorized to claim that
role.

## Risks & what would make this wrong

### Pre-mortem

- **Accepted limitation becomes permission for unsafe automation.** Mitigation:
  automatic refresh remains headless by contract; interaction-required is a
  terminal outcome, not a fallback trigger.
- **Users mistake derivation for protection.** Mitigation: architecture and spec
  call it defense in depth and name the same-principal bypass.
- **A second package is proposed later as if packaging created privilege.**
  Mitigation: this RFC makes ownership of code, policy, interpreter, and
  invocation contract the test.
- **A protocol-backed mode is assumed to solve generic cookie capture.**
  Mitigation: any future proposal must name a concrete consumer, credential
  returned, issuer binding, and unsupported fallback behavior.
- **Removing backlog entries hides the exposure.** Mitigation: the shipped spec,
  architecture document, RFC, and follow-on ADR record it as an accepted
  limitation rather than unfinished work.

### Key assumptions

- The supported installer writes all broker code and policy under the same user
  authority. Falsifier: a supported installation path that creates an
  independently protected executable and policy.
- Generic target deployments cannot be assumed to support a native-app or device
  authorization protocol. Falsifier: a concrete supported consumer contract
  that provides registered redirect or device authorization and returns a usable
  credential.
- Operator-only headed capture does not add an automated credential-harvesting
  capability. Falsifier: a supported unattended path that can cause the operator
  to see and use the headed login page.

### Drawbacks

- Generic headed capture retains a known phishing exposure if the operator does
  not verify the displayed destination.
- The repository provides no engineering path to eliminate that exposure under
  its current deployment constraints.
- Protocol-backed authentication, if later added, will cover fewer deployments
  and may create a second credential family beside SSO cookies.
- Closing the backlog items means changed constraints must trigger new intake;
  no dormant implementation task remains to resume automatically.

## Evidence & prior art

### De-risk spike

The riskiest assumption was that a protected destination file enforced by the
current broker—or by another Python package—could close the boundary without a
new deployment class.

Supported headed calls converge at the broker's `_do_register` function before
`_capture(..., headless=False)`, so one logical gate could cover supported call
paths. The engine is nevertheless a Python script installed under the user's
home directory. The same-principal agent can modify it, bypass the register
branch, import browser automation directly, or launch another browser. The pip
package and vendored floor run under the same authority. The spike therefore
disproved the assumption: rearranging user-scoped Python cannot create
independent enforcement.

### Repository precedent

- `docs/architecture/credentials.md` accepts the same-principal limit and names
  headed credential entry as its only high-blast-radius carve-out.
- The `jira-check-sso-auto-login` acceptance criteria keep automatic refresh
  headless, record derivation as partial, and retain direct engine invocation as
  an open capability of the operator account.
- RFC-0035 made the reference SSO config adopter-editable and kept the broker
  user-scoped.
- ADR-0026 places consumer resolution in the `credbroker` library while leaving
  capture in the projected broker engine. Neither side has a separate principal.
- RFC-0083 assigns executable work to specs. Because this RFC authorizes no
  implementation, closing rather than queuing a spec preserves that boundary.

### External prior art

- [RFC 6265](https://www.rfc-editor.org/rfc/rfc6265.html#section-8.2)
  supplies the designation-versus-authority diagnosis for cookie-bearing user
  agents.
- [RFC 8252](https://www.rfc-editor.org/rfc/rfc8252.html) separates native-app
  authorization into an external browser and a registered response channel,
  with PKCE protecting the authorization response.
- [RFC 8628](https://www.rfc-editor.org/rfc/rfc8628.html) moves user approval to
  an authorization server and lets a client poll with a device code.
- [Python isolated mode](https://docs.python.org/3.11/using/cmdline.html#cmdoption-I)
  can remove user site-packages and `PYTHON*` environment influence from import
  resolution; it does not change filesystem ownership or prevent an authorized
  user from invoking different code.

## Open questions

None. Protocol support or an expanded deployment envelope is a future intake
trigger, not unfinished implementation scope in this RFC.

## Follow-on artifacts

- ADR: the baseline credential-brokers install provides no same-principal
  destination enforcer; generic headed SSO cookie capture remains operator-only.
- No implementation spec, plan, or workspace entry follows from this RFC.
- A future protocol-backed mode or protected installation class begins with a
  new proposal tied to concrete deployment evidence.
