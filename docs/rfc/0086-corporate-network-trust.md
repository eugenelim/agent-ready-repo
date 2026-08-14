# RFC-0086: Corporate-network trust for catalogue fetches

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-13
- **Date closed:** 2026-08-14
- **Decision weight:** heavy (changes which TLS certificates the engine trusts)
- **Related:**
  - `docs/CONVENTIONS.md` § Corporate-network requirements — requires honouring `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, and `SSL_CERT_DIR`, and refusing a verification-disabling default. Scope, stated honestly: that section addresses *credentialed primitives shipped from this catalogue*, and `agentbundle` is the installer rather than a shipped primitive. D1 applies the rule **by analogy** — the reason behind it, a corporate laptop's trust store, applies identically — rather than citing an existing mandate over the engine.
  - RFC-0035 — accepted; wired those same three variables, plus proxy variables, into the credential-broker HTTP client and made it an acceptance criterion there. Establishes the precedent D1 follows. It did not settle the add-versus-replace question D2 settles.
  - ADR-0036 — accepted; establishes that the *default* catalogue source is chosen through a fixed precedence order (explicit argument, then user configuration, then an organisation bootstrap, then editable-install detection, then a packaged default) rather than from the current working directory, so where install code comes from is decided by configuration. Relevant here only for framing: a fetched catalogue becomes executable agent instructions, which is what makes an over-trusted anchor consequential.
  - RFC-0084 — accepted; the neighbouring trust-boundary decision, covering single sign-on destinations. Context only; nothing here depends on it.
  - `docs/specs/catalogue-corporate-trust-store/` — the implementing spec and plan, carrying the acceptance criteria these decisions are verified against.

`agentbundle` is the Python command-line tool that installs **packs** — named
bundles of agent primitives, meaning the skill files, subagent definitions, and
hook scripts a coding agent reads — from a **catalogue**, the authoring checkout
that holds them. This document also calls `agentbundle` **the engine**, matching
the repository's usage: its source lives under `packages/agentbundle/`, and a
change to its behaviour must pass an automated **engine-change gate** requiring an
`Engine-Change-RFC:` commit trailer that names an RFC. That gate is why this
document exists. A **catalogue source** names where a catalogue is fetched from. Three remote source
forms exist, and which one an adopter uses decides which module performs the
fetch — the distinction this RFC turns on:

| Source form | Fetches | Handled by |
| --- | --- | --- |
| `git+https://` | a repository archive at a branch, tag, or commit (`@main` names a branch, and a branch ref is mutable) | `catalogue.py` — **the only path this RFC changes** |
| `catalogue+https://` | a catalogue descriptor from a URL | `https_catalogue.py` — unchanged |
| `archive+https://` | a pinned archive, checked against a `#sha256=` digest carried in the URL | `https_catalogue.py` — unchanged |

The filenames cut across the scheme names: `catalogue.py` serves `git+https://`,
while the `catalogue+https://` form is served by `https_catalogue.py`. Where this
document says "the two forms `https_catalogue.py` serves", it means
`catalogue+https://` and `archive+https://`. A **trust anchor** is a
certificate authority a TLS client is willing to root a certificate chain at, and
a **trust store** is the collection of them. **TLS interception** is the common
corporate arrangement where a network proxy terminates outbound HTTPS and
re-signs it with an authority the organisation controls, so that traffic can be
inspected; clients on that network must trust the organisation's authority or
every connection fails verification.

## Reviewer brief

- **Decision:** Whether, and on what terms, the engine consults trust material outside Python's own certificate file when a catalogue fetch fails verification.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - Honour `AGENTBUNDLE_CA_BUNDLE`, `SSL_CERT_FILE`, `SSL_CERT_DIR`, and `REQUESTS_CA_BUNDLE` on `git+https://` catalogue fetches.
  - Add anchors to the default trust store rather than substituting for it, diverging deliberately from the `catalogue+https://` behaviour.
  - On macOS, retry a certificate-verification failure once against the administrator keychain, announced on stderr, with an `AGENTBUNDLE_NO_SYSTEM_TRUST` opt-out.
  - Read `/Library/Keychains/System.keychain` only.
- **Affected surface:** `packages/agentbundle/agentbundle/catalogue.py` (the `git+https://` fetch), a new sibling module `system_trust.py`, and the adopter-facing reference guide `guides/_shared/reference/agentbundle.md`, whose environment-variable table and new corporate-networks section are part of this proposal. No change to `https_catalogue.py`, nor to how a default catalogue source is chosen. Local-path installs and the
`catalogue+https://` / `archive+https://` forms are untouched.
- **Stakes:** This decides which certificates the tool will trust while fetching code that becomes executable agent instructions. Cheap to reverse in code; expensive if it silently widens trust.
- **Review focus:** D4 above all — whether reading an operating-system trust store at all is acceptable on this path, and whether the administrator-only bound is the right one. Secondarily D2, which knowingly leaves one environment variable meaning two things across source forms.
- **Not in scope:** `https_catalogue.py`'s replace-the-store semantics; source precedence (ADR-0036); archive integrity or ref immutability on `git+https://`; proxy authentication.

**Unusual for this repository:** the change is already implemented and tested, on
branch `eugenelim/install-pack-triage`. It was written as an incident fix before
the engine-change gate surfaced the need for an RFC. This document is therefore
a decision record for a known-working change, not a speculative proposal; the
measurements quoted are from that implementation. Reviewers should treat the
decisions as genuinely open — the code is revertible.

## The ask

- **Recommendation (bottom line up front):** Accept all four decisions. Adopters behind TLS interception currently cannot install at all, and the documented remedy does not work on the source form they use. No code path added here disables verification, accepts an unverified peer, or removes an existing anchor; hostname checking and full chain validation apply on every attempt. Two qualifications, stated here rather than buried: a stale `SSL_CERT_FILE` empties the trust store, but that is OpenSSL resolving its own default paths before this code runs and nothing here can undo it (D1); and ignoring an administrator *Never Trust* marking disregards a revocation, the one place this work is not strictly widening (D4, *Known residual*).
- **Why now (situation–complication–question):** *Situation* — adopters install packs from a `git+https://` catalogue over the public internet. *Complication* — on a network that inspects TLS, the organisation's authority lives in the operating system's trust store, which Python does not read on macOS, so the fetch fails with `CERTIFICATE_VERIFY_FAILED` and no actionable guidance; separately, the `AGENTBUNDLE_CA_BUNDLE` variable the reference documentation offers as the remedy is read only by the two forms `https_catalogue.py` serves and ignored by `git+https://`. *Question* — does the engine consult trust material beyond its own certificate file, and under what bound?
- **Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Which configuration surfaces supply trust anchors on `git+https://`? | `AGENTBUNDLE_CA_BUNDLE`, then `SSL_CERT_FILE`, then `REQUESTS_CA_BUNDLE`; `SSL_CERT_DIR` for the directory | `CONVENTIONS.md` § Corporate-network requirements sets this rule for credentialed primitives and the same reasoning applies to the installer; RFC-0035 already made the identical wiring an acceptance criterion | This review | Confirm the precedence order. |
| D2 | Do supplied anchors add to the default store or replace it? | Add | A bundle holding only a private authority must still verify the cross-host redirect this fetch performs; pip does the same thing by default | This review | Rule on knowingly diverging from `https_catalogue.py`. |
| D3 | Does a verification failure trigger an automatic operating-system trust retry? | Yes — once, announced on stderr, with an opt-out | The explicit route helps only adopters who already hold a certificate file, which is the minority; silence would make the trust change unauditable | This review | Rule on automatic trust widening, and on the notice + opt-out as sufficient controls. |
| D4 | Which operating-system trust material is read? | `/Library/Keychains/System.keychain` only | One store satisfies both requirements at once — it needs administrator rights to write, and it holds the authority this feature must find; Apple's root program measurably adds nothing | This review | **Primary focus.** Rule on the administrator-only bound. |

## Problem & goals

**Diagnosis.** Two independent faults produce one symptom.

The first is ours and is a plain gap. `guides/_shared/reference/agentbundle.md`
documents `AGENTBUNDLE_CA_BUNDLE` as the certificate-authority bundle for HTTPS
catalogue sources. `https_catalogue.py` reads it. `catalogue.py`, which serves
`git+https://`, read no trust configuration at all — its fetch was a bare
`urllib.request.urlopen(url)`. An adopter who followed the documentation exactly
still failed. Confirmed by probe: with `AGENTBUNDLE_CA_BUNDLE` pointed at an
empty certificate file, a `git+https://` fetch still succeeded, proving the
variable was never consulted; the same file in `SSL_CERT_FILE` reproduced the
adopter's error, because OpenSSL reads that name through its own default paths
whether or not the application cooperates.

The second is environmental and platform-specific. On macOS, Python does not
consult the operating system's trust store at all:
`ssl.SSLContext.load_default_certs` carries a `win32` branch and no `darwin`
branch, so an authority an organisation installs into the login or system
keychain is invisible to `urllib`. This is the fault that leaves an adopter with
nothing to do, because the material they need is already on their machine and
already trusted by every other tool.

**Goals.**

- An adopter behind TLS interception can install without knowing what a
  certificate file is.
- The variable the reference documentation advertises works on every source form
  it claims to cover.
- Every trust decision the tool makes beyond Python's default is visible to the
  adopter at the moment it is made.
- Verification strictness is unchanged: hostname checking and full chain
  validation on every attempt.
- Behaviour is unchanged for an adopter who sets nothing and whose default store
  verifies.

**Non-goals.**

- **Reconciling `AGENTBUNDLE_CA_BUNDLE` across source forms.** Its
  replace-the-store behaviour on the two forms `https_catalogue.py` serves is a defensible pin for
  an internal artifact repository. Changing shipped enterprise behaviour with no
  defect driving it costs more than documenting the difference.
- **Making the fallback cross-platform.** Not a scoping compromise — see D4;
  Windows already reads its own store, and the remaining gap is WSL, which is a
  documentation matter.
- **Post-transport integrity for `git+https://`.** This path has no digest gate,
  and a branch ref such as `@main` is mutable, so the bytes a fetch returns can
  change between fetches. Both predate this change and neither is fixed here.
  Note the direction, because it is easy to read backwards: these absences
  *enlarge* the consequence of trusting a bad anchor, which is exactly why D4
  draws the anchor bound tightly.
- **Proxy authentication.** A proxy demanding Kerberos or NTLM is unreachable by
  `urllib` regardless of trust configuration.

## Proposal

### D1 — Trust configuration on `git+https://`

The fetch builds its TLS context from the environment. The bundle file resolves
as `AGENTBUNDLE_CA_BUNDLE`, else `SSL_CERT_FILE`, else `REQUESTS_CA_BUNDLE`; the
directory resolves as `SSL_CERT_DIR`. `AGENTBUNDLE_CA_BUNDLE` is ours and is set
by hand for this purpose, so a path that does not exist raises rather than being
absorbed — matching what `https_catalogue.py` already does with the same name. A
stale `REQUESTS_CA_BUNDLE` is ignored, because organisations set it fleet-wide
and a stale value must not harden into an install failure.

One asymmetry is documented rather than fixed, because it cannot be fixed here: a
stale `SSL_CERT_FILE` or `SSL_CERT_DIR` empties the trust store rather than
falling back to the public authorities, since OpenSSL resolves its default paths
from those names before the application sees them. Measured: 193 anchors with the
variable unset, 0 with it pointing at a missing file. Reloading the same bad path
cannot undo that, so the reference documentation tells operators to unset rather
than misdirect these two names.

### D2 — Anchors add, never replace

Contexts originate at `ssl.create_default_context()`, and resolved anchors are
loaded on top. The property matters concretely: a GitHub archive fetch redirects
`github.com` to `codeload.github.com`, so a bundle holding only a corporate
authority must not un-trust the public authorities the second hop needs.

This diverges from `https_catalogue.py`, where the same variable replaces the
store. The divergence is deliberate and asymmetric on purpose: that path fetches
from an internal artifact repository, where pinning to one authority is a
feature; this path fetches from the public internet across two hosts, where
pinning breaks the fetch. The reference documentation states which source forms
carry which meaning.

### D3 — One announced retry against operating-system trust

When and only when the first attempt raises a certificate-verification failure,
and the adopter has not set `AGENTBUNDLE_NO_SYSTEM_TRUST`, the fetch resolves
operating-system trust anchors — concretely, by running
`/usr/bin/security find-certificate` and reading the certificates it prints,
because Python exposes no macOS trust-store API. If none are available it reports that and stops.
If some are available it prints one line to stderr naming the host and the trust
source, then retries exactly once with those anchors added.

Three properties bound it. The retry is reached only for a
certificate-verification failure — never a timeout, name-resolution failure, or
HTTP error — so a transient outage cannot become doubled load. Anchors are
resolved *before* the notice is printed, so the tool never announces work it
cannot perform. And the notice is unconditional, because a trust decision an
adopter cannot see is one they cannot audit.

Anchors load one certificate at a time. OpenSSL stops at the first block it
cannot parse, and a keychain dump legitimately contains material that is not a
parseable certificate; measured, a combined load of one good certificate plus one
malformed block keeps 1 anchor when the good one is first and **0** when it is
second. Per-block loading removes that ordering dependence, so a dirty dump
cannot cause the fallback to announce itself and then silently supply nothing.

### D4 — Administrator keychain only

The fallback reads `/Library/Keychains/System.keychain` and nothing else.

Two exclusions carry the decision. The user's `login.keychain-db` is writable
without administrator rights, so an authority landing there is not an
organisational trust decision and must never become an anchor. Apple's
`SystemRootCertificates.keychain` is excluded for a different reason: the retry
context already starts from Python's default store, so the public authorities are
present, and importing Apple's separately curated root program on top would widen
trust to a second root program for no gain.

**State that claim precisely, because a loose version of it is false.** Measured
on a corporate host, reading `System.keychain` alone produced the same anchor
count — 208, against a 193-anchor baseline — as reading both. Apple's keychain
adds nothing *while Python's default store is intact*, which is the corporate
case: an intercepted machine has its public authorities and is missing exactly one
private one. It is **not** true when the default store is empty or broken. This
change's own QA record holds the counterexample — an early reproduction that
emptied the store recovered only because Apple's keychain then supplied the public
root the emptied store had removed. Dropping Apple's keychain invalidated that
reproduction, which is what motivated building a real-TLS integration test that
does not depend on the local store's shape.

Two limits on the evidence, stated rather than glossed. One host is one data
point. And equal anchor counts cannot by themselves distinguish "those
certificates were already trusted" from "that keychain read returned nothing",
because the runner turns a non-zero exit into an empty string; the reading here
rests on the administrator trust domain separately listing the organisation's
authority.

The exclusion matters because of what this path lacks. `git+https://` has no
post-transport digest check, unlike the `archive+https://` path, and `@main` is a
mutable ref; the fetched tree becomes executable agent instructions. Every
additional anchor is therefore a party who could substitute that tree, and
"contributed nothing measurable" is a sufficient reason to exclude a whole root
program.

**Why the fallback is macOS-only.** This is a property of Python, not a scope
decision. `ssl.SSLContext.load_default_certs` loads the Windows `CA` and `ROOT`
stores through `enum_certificates`, filtering on each certificate's trust
settings — which is *stricter* than what this proposal can do on macOS — and has
no `darwin` branch whatsoever. Linux resolves through OpenSSL's default paths.
So Windows adopters need no fallback and already benefit from trust-setting
filtering; Linux adopters need none once the authority is installed in
`/etc/ssl/certs`. The residual case is WSL, which reports `linux` and does not
inherit the Windows store, so an authority pushed to Windows is invisible inside
the distribution; that is addressed with documentation and a targeted diagnostic
message, tracked as the backlog entry `catalogue-trust-store-wsl-diagnosis` in
`workspace.toml`.

**Known residual.** `security find-certificate` does not consult per-certificate
trust settings, so an authority an administrator marked *Never Trust* is still
loaded. That marking is a revocation, which makes ignoring it subtractive of a
control rather than purely additive — the one place this proposal is not strictly
widening. It is bounded to a store only an administrator can write, and tracked as the
backlog entry `catalogue-trust-store-trust-settings` in `workspace.toml`. Python's Windows path is the shape to
match when it is closed.

## Options considered

Enumerated along the axis *where trust material may come from*, which is what
determines the security consequence. The axis has five positions, collectively
exhaustive over it: nothing beyond Python's own certificate file (option 1),
shipped with the application (option 2), supplied by the operator (option 3),
supplied by the operating system (options 4, 5, and 6 — which share that position
and differ in whether it is automatic, opt-in, or delegated to a library), or no
authority at all (option 7).

1. **Do nothing.** Adopters behind interception cannot install, and the
   documentation continues to promise a remedy that does not work. Rejected: the
   gap in D1 is unambiguously a defect.
2. **Bundle a certificate set with the tool** (vendor `certifi`). Rejected on two
   counts: `pyproject.toml` declares `dependencies = []` deliberately, and a
   bundled set cannot contain an authority private to the adopter's employer, so
   it does not address the problem.
3. **Operator-supplied only** — honour the environment variables and stop. This
   is D1 without D3. Correct as far as it goes, and shipped as part of this
   proposal, but it helps only an adopter who already holds a certificate file.
   Most do not; that is why the failure reaches a maintainer.
4. **Operating-system-supplied, automatic** — the recommendation. Defers to the
   trust decision the organisation already made through its device management.
5. **Operating-system-supplied, opt-in** — the same source as option 4, but
   consulted only when the adopter sets a variable such as
   `AGENTBUNDLE_SYSTEM_TRUST=1`. This is the least-widening way to reach the
   material and the honest alternative to D3. Rejected for the same reason as
   option 3: an adopter who could diagnose an interception failure well enough to
   know to set that variable could equally set `AGENTBUNDLE_CA_BUNDLE`, and would
   not need a fallback at all. It converts an automatic recovery into one more
   thing to document and fail to find. Worth revisiting if support load suggests
   the automatic form surprises people.
6. **Depend on `truststore`** to read the operating-system store properly.
   Rejected: it is a dependency, and the constraint above forbids one. Worth
   revisiting if that constraint ever relaxes, since it uses the platform APIs
   rather than shelling out and would close the *Never Trust* residual.
7. **Weaken or disable verification** — an `--insecure` flag, `verify=False`, or
   `CERT_NONE`. Rejected on principle and by rule: `CONVENTIONS.md` forbids it as
   a default and requires an opt-in flag to warn on every use. A test now scans
   every Python source file under `packages/` for those constructs, so the option
   cannot reappear as a debugging convenience.

## Evidence & prior art

**In repository.**

- `docs/CONVENTIONS.md` § Corporate-network requirements — mandates honouring
  `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, and `SSL_CERT_DIR`, and names the exact
  failure this RFC responds to: "ignoring them turns into a *works on the
  engineer's laptop only* bug."
- `packages/credbroker/credbroker/_sso.py` — `credbroker` is the sibling package
  that brokers credentials for authenticated skills, and it already met this
  problem on corporate networks. Its TLS context is the in-repository reference
  for add-don't-replace precedence with `SSL_CERT_FILE` ahead of
  `REQUESTS_CA_BUNDLE`, including the deliberate suppression of a stale path. D1
  and D2 follow it so both packages behave the same way for an adopter who sets
  these variables once.
- RFC-0035 — made the same trust-store wiring an acceptance criterion for the
  credential broker's HTTP client, so D1 extends an accepted position rather than
  opening one. It did not settle add-versus-replace; D2 is genuinely new.
- ADR-0036 — establishes that where install code comes from is decided by a fixed
  configuration precedence order rather than the working directory. It matters
  here only for framing: the tree this fetch returns becomes executable agent
  instructions, which is what makes D4's anchor bound worth arguing over.

**External.** Both sources fetched and confirmed to contain the claims below.

- [pip's HTTPS certificates documentation](https://pip.pypa.io/en/stable/topics/https-certificates/)
  — "By default system certificates are used **in addition to** certifi to verify
  HTTPS connections", default since pip 24.2, available behind
  `--use-feature=truststore` since 22.2, with `--use-deprecated=legacy-certs` to
  opt out. This is direct precedent for D2's add-don't-replace semantics and for
  D3 being *more* conservative than the ecosystem norm, since pip made
  operating-system trust the default rather than a fallback.
- [truststore's documentation](https://truststore.readthedocs.io/en/latest/) —
  exposes native trust stores through the Security framework on macOS, CryptoAPI
  on Windows, and OpenSSL on Linux; its stated rationale is automatically updated
  authorities, intermediate fetching, and revocation-list checking.

**Honest limits of that prior art.** Neither document cites corporate TLS
interception as its motivation — pip and `truststore` argue from certificate
freshness and revocation. They are cited here for the *mechanism* and for the
norm that reading operating-system trust is mainstream, not as evidence that
others solved this specific problem. No comparable tool in this problem space was
found that documents an interception-specific fallback, which is itself a finding.

## Risks & what would make this wrong

**Pre-mortem — the ways this ends badly.**

- **An anchor nobody intended becomes trusted.** The mitigation is the
  administrator-only bound in D4 and the additive-only property in D2. The
  residual is the *Never Trust* case, recorded above.
- **The fallback masks a genuine attack.** An adopter sees one stderr line and
  proceeds. Mitigated because the attacker must already hold a chain to an
  authority in a store only an administrator can write — which implies control of
  device management, at which point the install is not the weakest link.
- **The notice is not read.** Likely, in honesty. It is the floor, not a control;
  D4's bound is the control.

**Falsifiable assumptions.**

- *The corporate authority reliably lands in `System.keychain`.* If organisations
  commonly install it elsewhere, D4's exclusion makes the fallback useless.
  Tested on a corporate host: the authority was present in the administrator
  trust domain and `System.keychain` alone matched the both-keychains anchor
  count. One host is one data point.
- *Adopters prefer a self-repairing install to an accurate failure.* If wrong,
  D3 should be dropped and D1 kept.

**Drawbacks, stated plainly.** The engine now shells out to `/usr/bin/security`
on a network path, adding a module and a subprocess boundary to code that
previously had neither. It behaves differently across platforms, which makes
support conversations harder. And one environment variable now means two things
depending on source form — the price of the divergence D2 accepts, paid in
documentation rather than in code.

## Rollout

The implementation exists and is verified: unit coverage for precedence,
strictness, platform gating, and the keychain argument vector; an integration
test that stands up a throwaway authority and a TLS server, so a real failing
handshake and its recovery are exercised without network access; and a test that
scans every Python source file under `packages/` for verification-disabling constructs.

Shipping is `agentbundle` 0.35.0 — a minor bump, because the work adds a
capability and carries one behaviour change, and the package's pre-1.0 policy
allows a minor to be breaking. The contract version in `adapter.toml` stays at
0.18: no pack-facing contract moves. Adopter-facing surfaces updated in the same
change are the reference guide, the product changelog, the package changelog, and
the PyPI long description, which gains a *Corporate networks* section covering
the per-platform table and the WSL case.

One behaviour change needs calling out to adopters, and is in the changelog:
setting `AGENTBUNDLE_CA_BUNDLE` to a path that does not exist now fails a
`git+https://` install that previously succeeded, because the variable was
ignored on that path before.

## Open questions

| Question | Recommended default | Owner | Decide by |
| --- | --- | --- | --- |
| Should `AGENTBUNDLE_CA_BUNDLE` eventually mean one thing on all source forms? | Yes, but through its own RFC carrying an adopter-facing migration note, rather than folded into an incident fix. | eugenelim | 2026-09-30 |

Two questions that stood here in an earlier draft moved to *Risks & what would
make this wrong*, where they belong: whether the *Never Trust* residual should
block shipping, and whether one corporate host is enough evidence for D4. Both
are already decided and recorded — the residual is deferred with a register
entry, the exclusion ships on a measured no-op — so listing them as open would
have been theatre.

## Errata

The body above is frozen. Corrections are appended here, and where this section
disagrees with the body, this section is authoritative.

### Current state

| Decision | As accepted | In force |
| --- | --- | --- |
| D4 | Apple's `SystemRootCertificates.keychain` is never read. | Read **only** when the default trust store holds zero anchors. The administrator-keychain-only rule still governs every other case, and the login keychain is still never read. |

### History

**2026-08-14 — D4 narrowed, not reversed.** An adopter on `agentbundle` 0.35.0
reported a failing install whose diagnosis this RFC gets wrong. Their evidence:
`github.com` presented the genuine public chain with `Verify return code: 0
(ok)` — nothing was intercepting them — while their python.org macOS
interpreter reported `cafile: None` and **zero** trusted authorities, because
its `Install Certificates.command` step had never run. Every HTTPS request from
that interpreter failed, not only ones crossing a proxy.

The fallback could not repair it, by construction. `System.keychain` holds
private roots; the public root needed to verify `github.com` is in Apple's root
program, which D4 excluded. Measured on a corporate host: Apple's keychain
verifies `github.com` on its own (158 anchors), the administrator keychain does
not (21 anchors).

D4's reasoning was sound for the case it examined and too broad for the case it
did not. With an intact store, Apple's root program adds nothing measurable
while widening trust — that still holds, and it still governs. With an **empty**
store there is no trust to widen: loading Apple's curated public program is
strictly additive from nothing, and it is precisely the set the interpreter was
supposed to have. Reading it in that one state is therefore narrower in effect
than D4's blanket exclusion was in intent.

Also corrected: the failure message previously attributed an empty store to a
TLS-inspecting proxy, which sent this adopter after a cause that did not exist.
An empty store is now named as its own diagnosis, with the interpreter-level fix
as the first troubleshooting step and the proxy framing suppressed.

What did not change: verification strictness, the login-keychain exclusion, the
one-retry bound, and the administrator-only rule for any interpreter with a
working trust store.

**Standing correction to this RFC's framing.** The body treats corporate TLS
interception as the problem. The first confirmed field report was not
interception at all — it was an unconfigured interpreter. Both faults produce
the same OpenSSL string, and this RFC over-weighted the first. A future reader
should not infer from the body that interception is the common cause; on the
evidence so far, it is not the only one and may not be the more frequent.
