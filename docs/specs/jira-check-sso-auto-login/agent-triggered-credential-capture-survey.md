# Agent-triggered credential capture — secure alternatives to a reachable `--register`

> Discipline: applied (practitioner-pattern survey)

**Question.** A CLI invoked by an AI agent can trigger a headed-browser SSO login
whose destination URL comes from a config file the same agent can edit. Is there
a secure alternative to putting that capability on an agent-reachable flag?

**Scope.** Prior art on binding/attesting the destination; out-of-band human
confirmation for agent-triggered credential operations; confused-deputy
mitigations. Feeds the `--register` decision in
[`spec.md`](./spec.md) AC15 / AC32.

---

## Findings

### F1. This is a textbook confused deputy, and the canonical fix is to remove the argument, not validate it `[high]`

The classic 1988 formulation: a compiler with legitimate write authority to a
billing directory was passed a billing-file *name* as its debug-output
destination. The name and the right travelled separately — designation arrived
without authority, and the deputy applied its own ambient authority to a target
the caller chose.

The capability-security answer is **"No Designation Without Authority"** (*Capability Myths Demolished*, property A): the caller passes an unforgeable
reference that already carries the authority, never a name the deputy resolves
against an ambient pool. Applied here — validating `login_url` after reading it
is ACL-style thinking and fails the moment the allowlist itself lives in the
file being guarded. The structural fix is that the automatic path must not
*accept* a destination at all.

This is precisely what `refresh_sso_session(profile)` already does. The gap is
only first-run.

Sources: Wikipedia *Confused deputy problem* (primary); *Capability Myths Demolished* (primary); *a capability-security retrospective* (primary). Two share an author, so they count as one under the practitioner-independence rule.

### F2. AWS solved the identical problem by decoupling *which tenant* from *which host* `[high]`

`aws sso login` reads `sso_start_url` from `~/.aws/config` — a plaintext file any
process running as the user can edit. Structurally identical to our
`sso-config.toml`.

The mitigation is that **the browser's authorization endpoint is not derived from
the config-supplied URL**. It is always `oidc.{sso_region}.amazonaws.com`
(PKCE, default since CLI v2.22.0) or `device.sso.{sso_region}.amazonaws.com`
(device flow) — i.e. always `*.amazonaws.com`, derived from `sso_region`.
`sso_start_url` selects *which SSO portal on AWS's own back end*, not *which host
the browser visits*. Poisoning it cannot redirect the browser to attacker
infrastructure.

The generalisable pattern: **let the config name the tenant; pin or derive the
host.** Every major CLI surveyed does some version of this —
`gcloud auth login` hardcodes `accounts.google.com`; `az login` hardcodes
`login.microsoftonline.com` with only the tenant parameterised;
`gh auth login` hardcodes `github.com` with `--hostname` as a *flag*, not a
config read.

Downgrade note: AWS docs are vendor-sourced and count as one source under
practitioner-independence; corroborated by independent practitioner analysis
(the independent practitioner analysis) which confirms no issuer validation exists but also confirms the host
derivation.

Sources: AWS CLI IAM Identity Center docs (primary, vendor);
*MITMing AWS IAM Identity Center OIDC Authentication* (primary, practitioner);
Google/Microsoft/GitHub CLI docs (primary, vendor).

### F3. "Config file is a trust boundary" is a documented CVE class, not a hypothetical `[high]`

**CVE-2024-52006 / CVE-2024-50349** (Git, Dec 2024): crafted URLs with encoded
newlines injected via `.gitmodules` caused the credential helper to fetch
credentials for one host and transmit them to an attacker's. The advisory
(GHSA-qm7j-c969-7j4q) states the failure in exactly our terms —
*"configuration-file-supplied URLs receive the same credential access as
explicitly user-provided URLs, despite having different trustworthiness
profiles."* **CVE-2025-23040** (GitHub Desktop) is the same class.

Sources: git/git security advisory (primary); GitHub Desktop advisory (primary).

### F4. In-prompt confirmation is the named anti-pattern; the approval channel must be one the agent cannot write `[high]`

**OWASP Top 10 for Agentic Applications 2026, ASI09 — Human-Agent Trust
Exploitation**: *"this risk targets the human approval step that other controls
depend on"*, requiring *"forced, explicit confirmations that show the raw action
rather than the agent's summary."* **ASI02 — Tool Misuse** is the framing for
argument-supplied targeting. **OWASP Agentic Skills AST03 — Over-Privileged
Skills** requires *"explicit operator consent for persistent state changes …
must not be auto-applied from injected instructions."*

The documented defeat: routing approval through a surface the agent controls.
Auth0 states it plainly — *"the approval question reaches the user through the
same chat surface that may already be compromised."* Slack/webhook approvals
without message signing fail the same way.

**This retroactively validates rejecting the TTY gate** — but for a reason
different from the UX one: a TTY the agent owns is not out-of-band.

Sources: OWASP ASI 2026 (primary); OWASP AST03 (primary); Auth0 (secondary,
vendor); a practitioner CIBA writeup (secondary). Vendor-heavy — see *Known unknowns*.

### F5. CIBA is the production out-of-band pattern, and it does not fit this case `[moderate]`

Client-Initiated Backchannel Authentication (OpenID Connect) pushes approval to
the user's separately-authenticated device; the agent cannot write that channel.
Shipped by Auth0, Okta, MuleSoft; banking deployments under PSD2 SCA bind the
approval cryptographically to the specific transaction. An IETF draft
(`draft-klrc-aiagent-auth-01`, Ping/OpenAI/AWS/Zscaler, March 2026) extends it
for agents.

**It does not apply here.** CIBA presumes an authorization server issuing tokens
to a registered client. Our flow captures a *browser session cookie jar* from a
headed browser against an arbitrary corporate IdP — there is no authorization
server in the loop and nothing to push. Recorded so the option is closed
explicitly rather than silently.

Downgrade: `[moderate]` — the pattern is well-evidenced, its
*inapplicability here* is my inference, not a sourced claim.

Sources: Auth0, WorkOS, a practitioner CIBA writeup, agentlair.dev (all secondary;
three of four vendor-authored — counts as weak independence).

### F6. TOFU fails exactly where we need it, confirming the rejection of a host-drift baseline `[high]`

*Why Trust-On-First-Use Doesn't Work*: a MitM during first connection
establishes false trust permanently, and subsequent change-warnings are
routinely defeated by users deleting `known_hosts` on IT advice. Alert fatigue
compounds it.

This independently confirms the round-2 reasoning for deleting the host-drift
control: its baseline would be recorded *after* the poisoned registration, so the
attacker's host becomes the reference.

Sources: the TOFU critique (primary); Wikipedia *Trust on first use* (secondary).

### F7. Habituation degrades any confirmation control over time `[moderate]`

Anthropic autonomy data cited in the intent-verification writeup shows users sliding from ~20%
full-auto-approval to >40% after ~750 sessions — the agent analogue of MFA
push-bombing fatigue. Relevant because a per-invocation confirmation on `check`
would be trained away precisely on the machines that use it most.

Downgrade: single secondary source citing the underlying data; not independently
triangulated.

Source: the intent-verification writeup (secondary).

---

## What this implies for `--register`

Three options, ranked. All are structural (F1) rather than validation-based.

### Option A — derive the destination from the server, don't read it from config

> **Superseded 2026-08-05.** Two corrections, from the spike and round 4:
> derivation works from `/login.jsp`, **not** `base_url`; and because `base_url`
> lives in the same agent-writable file, derivation is **defence in depth**, not
> a control. Consent for `--register` rests on it being operator-typed.
> See spec AC15 + AC32.

Follow F2's pattern: stop treating `login_url` as an input. An unauthenticated
request to `base_url` on a DC instance behind SSO **302-redirects to the IdP** —
so the *server* designates the destination, not the config. `base_url` is
already confined by `cookie_domains` and the existing `credbroker` primitives.

- **Strongest fix.** Removes the unbound designator entirely (F1), and mirrors
  the mechanism every surveyed CLI uses (F2).
- **Cost.** A behaviour change to the engine, and it inverts the deliberate
  `follow_redirects=False` posture on the cookie path — which exists for a good
  reason and would need care to relax safely for the *pre-auth, no-cookie* case
  only. Not all DC + SSO topologies redirect predictably.
- **Confidence in applicability:** `[moderate]` — the redirect behaviour is
  standard but I could not verify it against a real DC instance (see gaps).

### Option B — ephemeral browser context for `--register`

The reason the sub-second auto-SSO makes disclosure useless is
`launch_persistent_context(user_data_dir=…/browser-state/<profile>)`. For
`register`, launch a **fresh context** instead: first-run then genuinely requires
interactive sign-in on a visible page, restoring the URL bar as a real
confirmation surface — the *only* out-of-band channel available here that the
agent cannot write (F4).

- **Cheap, local, no new dependency.** Persistence stays where it earns its keep
  (`refresh`), and is removed where it destroys the confirmation surface
  (`register`).
- **Does not fix the destination**, only makes a poisoned one visible to a human
  who is present. Subject to habituation (F7).

### Option C — keep first-run out of agent reach

`--register` requires an out-of-band signal the agent doesn't naturally produce,
or first-run reverts to `setup_sso.py` only.

- **Simplest and most certain.** Costs the one-command first run.
- Consistent with AST03's "explicit operator consent … must not be auto-applied".

---

## Known unknowns

- **CLOSED 2026-08-05 by research + live spike.** `GET base_url` does **not**
  redirect — `/secure/Dashboard.jspa` returned `200`, confirming JRASERVER-66554
  (SAML redirection fires only from `login.jsp`). The working derivation is
  `GET {base_url}/login.jsp` with redirects unfollowed: observed
  `302 → Location: https://auth.atlassian.com/authorize?…` on a live Seraph
  instance. It returns `302` only in **forced-SSO** mode; in
  SSO-with-local-fallback it returns `200` with a button. Option A is therefore
  viable *with an explicit cannot-derive branch* — see spec AC32.
- **Known-unknown:** does Playwright's non-persistent context reliably force a
  visible interactive sign-in against an IdP that may itself hold a
  Kerberos/desktop-SSO session? Would be closed by: one observed run on a
  domain-joined machine. This gates Option B's core claim.
- **Unknowable (as posed):** whether operators would actually *read* a disclosed
  destination under Option B. The habituation data (F7) is from a different
  interaction shape, and no public study measures destination-verification rates
  in agent-triggered browser logins.
- **Unknowable:** whether any adopter has been hit by this. Config-poisoning
  incidents against SSO CLIs are not separately reported — the CVE class exists
  (F3) but incident data does not.

## Evidence quality caveats

- The out-of-band-approval literature (F4, F5) is **vendor-dominated** — Auth0,
  Okta, WorkOS, Teleport. Under the practitioner-independence rule these compress
  toward one source. No independent post-mortem of a CIBA-protected agent
  deployment being compromised exists publicly, which is itself a survivorship
  signal.
- The IETF agent-auth draft is ~7 months old and pre-RFC; treat as direction, not
  standard.
- F1, F3 and F6 rest on primary sources (capability literature, CVE advisories,
  the TOFU critique) and are the load-bearing findings. F2 is vendor-primary but corroborated
  by independent practitioner analysis.


---

## Addendum — prior-art sweep of agent-credential projects (2026-08-05)

Three repos supplied by the owner, plus a wider sweep. **No project found solves
this shape**: a *browser session capture* whose *destination comes from an
agent-editable config file*.

### F8. A shipping product has our exact unaddressed bug `[high]`

`authsome` is a zero-knowledge credential proxy (SKILL.md only — no
source visible, so implementation depth is unverified). Its agent-facing verb is
`authsome login <provider>` — **the agent supplies the argument that selects the
OAuth destination**, the identical confused-deputy shape, and their docs do not
discuss it. Their stated human-in-the-loop is "the browser opens on their
machine; they complete OAuth without touching the terminal" — the same
confirmation-surface claim this survey already falsified for the warm-profile
case (F2 rationale). Useful as evidence the problem is under-recognised, not as a
solution.

### F9. Proxy-injection removes the secret but not the destination choice `[high]`

`agent-vault` (Infisical) (~2k stars, real code) runs a MITM proxy: the agent
points `HTTPS_PROXY` at it and **never receives the credential** — it is injected
into outbound requests by host-matching rules. That is genuinely stronger than
handing over a value, and its egress filtering is the closest thing found to
structural destination control. Two limits: it addresses **API egress, not
browser session capture**, and the docs do not say who may write the service
rules — if the agent can, the protection collapses the same way ours does.
`agent-secrets` (real Go daemon, age-encrypted, TTL-bounded leases over
a Unix socket) solves storage and leasing only; its `--client-id` is an audit
label, not an access-control primitive, and it has no HITL and no browser flow.

### F10. Two transferable ideas we do not currently have `[moderate]`

1. **Derive the destination from the browser's live state, not from config.**
   1Password's extension model injects a credential only when the browser is
   *already on* the URL matching the saved item's origin, and approval is a
   **Touch ID / biometric** prompt — a system-level channel that is genuinely
   out of an agent's reach, unlike a TTY or a settings file. This is the only
   out-of-band approval channel found that survives our threat model.
2. **OS-level privilege separation is the only mechanism that actually protects
   the config file.** a practitioner `gh` hardening writeup documents our exact problem
   — `gh auth setup-git` writes the credential helper into an agent-writable git
   config — and mitigates with `sudo`-gated wrapper scripts (zero-second cache),
   *not* with validation. It corroborates directly: you cannot validate your way
   out when the allowlist shares a trust boundary with the attacker.

### F11. The literature confirms validation-moves-the-trust `[high]`

*Capability Gates Are Not Authorization* (arXiv 2606.28679) tested LangChain /
LangGraph, LlamaIndex and the Stripe Agent Toolkit: all ship capability gating
only, so a **well-formed** argument naming an attacker destination passes. Its
proposed ScopeGate assumes the policy file is protected from agent writes — the
same limitation we hit, unresolved. MCP's RFC 9728 adoption moves the
authorization-server URL from client config to server metadata, but the spec
itself notes issuer validation *"provides no protection if the expected issuer
was obtained from an unvalidated source"* — i.e. it moves the problem one hop,
exactly what round 6 found about our `base_url`. HashiCorp Vault's Agent Registry
+ Rich Authorization Requests is the principled version — the permitted paths and
parameter values are bound into the JWT **at issuance by a human**, so the agent
cannot widen them at call time — but it is M2M only and does not reach browser
sessions.

**Net effect on this spec:** nothing found contradicts the design. Parameter
elimination (our AC1) is the named correct fix; no source treats prompt-level
confirmation as a real control, which is why AC15 records it as a non-control.
F10's live-browser and privilege-separated mechanisms would require a browser or
administrator-installed component outside the supported user-scope deployment.
RFC-0084 therefore closes them as baseline work and records destination
poisoning as an accepted limitation.

`ASM (Agent Skill Manager)` was also checked: it is an Agent Skill Manager with **no
credential broker** — the comparison premise did not hold. Its one transferable
idea is orthogonal: a pre-install scan of third-party skill files for embedded
credentials, a supply-chain layer this spec does not address.
