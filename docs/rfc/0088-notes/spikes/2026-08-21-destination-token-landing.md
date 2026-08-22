# RFC-0088 round 14 — destination token landing and the fixture pair

**Status:** complete measurements; open question 3's bar is amended in the RFC's
amendment layer, and question 5 stays outstanding with a new finding against it.

This round exists to answer two questions the earlier rounds could not, because both
are properties of a **destination** and every prior arm measured a synthetic issuer
this project controls. Where the token lands, and whether the response that issues it
is marked `no-store`.

## Findings

### The `no-store` precondition is absent at a real destination

Round 12 established the page-resident replay accommodation **conditionally**: it held
when the issuing response was marked `no-store`, and the otherwise identical
default-cache arm found the live token at rest in browser user-data. The condition was
never tested against anything but the synthetic issuer that supplied it.

Driven through a real browser login against a pinned container, the token-issuing
response carries **no cache directive at all** — not `no-store`, not `private`, no
`Pragma`. The precondition is not weakened; it is absent.

### The token is at rest by the destination's own storage choice

The sharper observation, and the reason this is a finding rather than a missing header.
The destination's frontend writes the issued token into a **page-readable web-storage
key**, and a scan of the closed browser profile recovers the live token from the
storage log on disk. That path does not run through the response cache, so a
destination that *did* send `no-store` would leave the token at rest here anyway.

Keeping the token page-resident does not prevent this. A consumer sets neither the
destination's cache-control nor where the destination's own frontend stores its token,
so question 5's recommended accommodation is conditional on behaviour outside the
boundary this RFC governs. That is the finding: not that the accommodation is wrong,
but that its precondition is not something any consumer can establish.

### The contrast half shows the accommodation is inapplicable, not unsafe, elsewhere

The server-rendered half of the pair issues an `HttpOnly` session cookie. Page script
cannot read it — `document.cookie` exposes no name at all — so a page-resident replay
consumer cannot capture the credential in the first place. Neither destination
therefore *satisfies* the accommodation's condition, but they fail it in opposite
directions, which is why one destination could not have established either result.

### The leading candidate was excluded on measurement, not on preference

The candidate going in was an operator-internal delivery tool whose documentation
confirms exactly the shape open question 5 names: username and password exchanged for
a JWT at a session endpoint, with `Authorization: Bearer` on subsequent API requests.
Its storage location was unverified, which is what this round set out to measure.

It never reached measurement. Its API server refuses to start without a cluster API,
exiting fatal on a missing configuration. Standing it up would mean shipping a control
plane as the CI fixture, not a pinned container, and the decision that the fixture *is*
a container is precisely what excluded it. Recorded because a documentation-confirmed
auth shape is worth nothing if the thing cannot be started the way the fixture contract
requires — and because that is only visible by trying.

## The fixture pair

Two pinned containers of deliberately opposite render and authentication shape. Both
are reached over loopback; neither origin is persisted into the results artifact.

| Half | Image | Render shape | Credential shape |
| --- | --- | --- | --- |
| SPA | `vikunja/vikunja:0.24.6` | Login form absent from the initial HTML; the password field exists only after script runs | JWT in the login response body, written to a page-readable web-storage key |
| Server-rendered | `gitea/gitea:1.22.6` | Login form present in the initial HTML, with a `<form>` element and a password input | `HttpOnly` session cookie, unreadable from page script |

The contrast is measured rather than assumed: the SPA half's login document arrives
without a `<form>` element or a password input and acquires both under script, while
the server-rendered half's arrives with each already present. That difference is the
whole point of requiring two fixtures — an adapter contract exercised only against a
server-rendered destination never has to solve "the form is not in the document yet",
and one exercised only against an SPA never has to carry a CSRF token out of the
delivered HTML.

Fixture credentials are synthetic placeholders created against the container at run
time. Nothing is recorded from a live account, and no fixture credential is written to
the repository or to the results artifact.

## Apparatus

The arm follows the round-12 page-resident driver's construction: a declared row
inventory checked against what the run actually emitted, an in-region uniqueness
assertion for every mutation anchor, and a mutation harness that **throws on a stale
anchor rather than skipping it**. That assertion fired twice while this arm was being
built — once on an anchor that occurred twice in the region, once on an anchor left
over from an earlier draft that occurred zero times. The second is the case that
matters: a zero-occurrence anchor produces an unmutated mutant whose row never flips,
which a skipping harness reports as a control that did not fail.

Every declared row carries a mutation that changes the row's outcome, and the harness
asserts the flipped value rather than merely that the mutant ran. The unmutated
baseline is recorded immediately before the harness runs, so both directions are
observed rather than one being inferred.

Two rows are **declared failing**, and the declaration is the finding rather than a
tolerance: the row asserting the issuing response is `no-store`, and the row asserting
the live token is absent from browser user-data at rest. Both mutate *toward passing*,
which is the direction that matters for a row whose recorded outcome is a finding — the
risk is not that such a row fails spuriously, it is that it could never have passed,
and a row that cannot pass is not evidence.

The at-rest scan plants a labelled decoy in the profile and requires it to be
recovered. Without a recovered plant, "token not found" is indistinguishable from a
scanner that cannot read those buffers at all, so an absence result there establishes
nothing. A privacy row asserts over the **serialized artifact bytes** that no encoded
form of either the issued token or the fixture credential appears in it, rather than
trusting the code that built the artifact to have been careful.

## Reference consumer, and what it is not

The documented reference consumer is a fantasy-football league surface an adopter runs
against their own account, read-only, and it **never runs in CI** — the repository does
not contact a third party's servers. It is a recorded observation with provenance, not
an acceptance criterion. An acceptance criterion that cannot fire is worse than an
honest observation, which is why one is not written.

Its unauthenticated surface was probed read-only to establish where the session is
actually required. Public classic leagues are readable by identifier with no
credential, and the league object returned by that endpoint carries its own privacy
field, so the distinction is visible in the response rather than having to be assumed.
A separate manager-scoped endpoint refuses an unauthenticated request outright.

**Residual, named rather than glossed:** whether a *private* mini-league's standings
endpoint specifically requires the session is **not established here**. Confirming it
needs one private league identifier, which only the operator holds, and the alternative
— probing identifiers until a private one is found — is enumeration against a third
party and was not run. What is established is that the public case is genuinely open
and that manager-scoped surfaces are genuinely gated; the private-league case sits
between them and is unmeasured.

## Limits

- Two destinations do not establish a population. They establish that the
  accommodation's precondition is not universal, which is what the conditional result
  needed testing against.
- The at-rest result holds only for buffers where the planted decoy was recovered.
  Buffers without one are absence-unverifiable and contribute no absence claim.
- This note is not registered in the figure-verifier document corpus, so its figures
  are carried by the results artifact rather than by claim accounting. Registering it
  would bring the note under the claim-accounting requirement, which this round did not
  commission.
- The arm needs both containers running and is therefore not part of the unconditional
  gate chain. It is invoked explicitly with the destinations supplied as inputs; no
  origin is an ambient default, and none is persisted.
