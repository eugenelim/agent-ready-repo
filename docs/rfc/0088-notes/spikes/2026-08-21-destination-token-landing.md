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

The claim is scoped to the half that issues a token, because only one half does. The
contrast half's credential arrives as a cookie on a response marked
`max-age=0, private, must-revalidate, no-transform`. That is a cache directive, and it
is neither evidence for the precondition nor against it — the accommodation the
precondition belongs to cannot apply there at all.

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
consumer cannot capture the credential in the first place.

**The session is proven authenticated before that claim is made**, and the arm did not
originally do this. Every cookie the row inspects is set by the login *page*, so the
assertion passed byte-identically against a session that never logged in; a reviewer
found it. A declared row now navigates to a path that requires the session and asserts
it returns 200 without redirecting to login and without a password field. Its mutation
re-runs the probe in a context that never authenticated, and the row flips.

Neither destination therefore *satisfies* the accommodation's condition, but they fail
it in opposite directions, which is why one destination could not have established
either result.

### The leading candidate was excluded on measurement, not on preference

The candidate going in was an operator-internal delivery tool whose documentation
confirms exactly the shape open question 5 names: username and password exchanged for
a JWT at a session endpoint, with `Authorization: Bearer` on subsequent API requests.
Its storage location was unverified, which is what this round set out to measure.

It never reached measurement. Its API server refuses to start without a cluster API,
exiting fatal within a second of launch on `invalid configuration: no configuration has
been provided, try setting KUBERNETES_MASTER environment variable`. The quoted line is
a generic Kubernetes client error, and it is what makes the elimination re-derivable
by anyone who runs that server entrypoint bare.

Standing it up would mean shipping a control plane as the CI fixture, not a pinned
container, and the decision that the fixture *is* a container is precisely what excluded
it. The image is not named here because it is not the fixture, and the vendor-name
boundary admits only what a fixture requires. Recorded because a documentation-confirmed
auth shape is worth nothing if the thing cannot be started the way the fixture contract
requires — and because that is only visible by trying.

## The fixture pair

Two pinned containers of deliberately opposite render and authentication shape. Both
are reached over loopback; neither origin is persisted into the results artifact.

| Half | Image, pinned by digest | Render shape | Credential shape |
| --- | --- | --- | --- |
| SPA | `vikunja/vikunja:0.24.6`<br>`@sha256:ed1f3ed467fecec0b57e9de7bc6607f8bbcbb23ffced6a81f5dfefc794cdbe3b` | Login form absent from the initial HTML; the password field exists only after script runs | JWT in the login response body, written to a page-readable web-storage key |
| Server-rendered | `gitea/gitea:1.22.6`<br>`@sha256:538658de667c5d098a274f2f63aa6ec891d88f670cdd5282cf27221ba747dda4` | Login form present in the initial HTML, with a `<form>` element and a password input | `HttpOnly` session cookie, unreadable from page script |

The digest is the pin AD-4 requires; the tag is recorded beside it only so a reader can
tell which release it is. Pulling either still contacts a registry on a cold cache —
that is a named, allowlisted egress rather than an absence of one.

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
observed rather than one being inferred, and the harness's own summary is kept beside
the results artifact so the coverage claim has a durable record rather than a
self-reported field.

**One row carries two cases**, because one case per row is not the unit that matters
when a row is a conjunction. The contrast row's first mutation flips it through the
empty-store conjunct alone and leaves the `HttpOnly` conjunct — the one the RFC's
contrast claim actually rests on — asserted by nobody. A second case anchored on the
cookie mapping covers it. A row with several load-bearing conjuncts needs a case per
conjunct.

Two rows are **declared failing**, and the declaration is the finding rather than a
tolerance: the row asserting the issuing response is `no-store`, and the row asserting
the live token is absent from browser user-data at rest. Both mutate *toward passing*,
which is the direction that matters for a row whose recorded outcome is a finding — the
risk is not that such a row fails spuriously, it is that it could never have passed,
and a row that cannot pass is not evidence.

The at-rest scan plants a labelled decoy in the profile and requires it to be
recovered. Without a recovered plant, "token not found" is indistinguishable from a
scanner that cannot read those buffers at all, so an absence result there establishes
nothing.

**The privacy control is a write gate, not only a row.** A row asserts that no encoded
form of the issued token, the fixture credential, either destination origin or the
fixture user name appears in the artifact — origins included because a navigation
timeout embeds the URL in the error text, and that text reaches the failure record. The
scan runs twice, and the split is what makes the claim true rather than nearly true:
the row's own result is part of the artifact, so a single pass over the final bytes
cannot produce the row it must contain. Pass one yields the row; pass two scans the
exact bytes about to be written and **refuses the write** on a hit, emitting a
refusal record instead — and the refusal is scanned too, because "this record cannot
leak" is the kind of claim that stops being true the moment someone adds a field to it.
An earlier form scanned a prefix and then wrote the file regardless; a detected leak
would still have landed on disk.

The redactor is built from the **same encoded forms** the detector uses, and it was not
always. Measured while under review: a plain `page.goto: … at http://<origin>/login` was
redacted, while the percent-encoded form of the same origin walked straight past a
raw-substring redactor and was caught only by the write gate. Safe either way, but the
outcome differed — a redacted line in one case, a refused run in the other — which is a
redactor disagreeing with its own detector. They now share one definition.

The mutation plants the **live token**, and the write gate is what makes that safe. An
earlier form planted a synthetic sentinel to avoid writing a credential anywhere, but
the sentinel is detected through the origin and user terms, so the credential detector
itself was exercised by nothing: removing it left every case and the no-op still
passing. That is a control that cannot fail. With the write gate refusing, the planted
token reaches no file, so the stronger plant costs nothing — and the harness now asserts
*which* term produced the refusal, not merely that something did.

**Cleanup is symlink-safe, and a surviving profile is fatal.** Chromium plants
`SingletonLock` and its siblings as symlinks in every profile root and removes them only
on a clean exit; the confined remover refuses any tree containing a symlink, by design.
Handing it a browser profile directly therefore throws on any unclean exit, and what is
left behind is the profile holding the live token. Proven rather than reasoned: with a
`SingletonLock` planted, the remover throws `refuse symlink` and the token-bearing file
survives. Symlinks are now unlinked first with a mechanism that cannot follow one, a
forced removal backs that up so a fatal outcome means "could not be removed by any
means" rather than "the confined path declined", a root that survives every path is
fatal rather than a field, and signal handlers cover the interrupt path with the same
verification, since a `finally` block does not run on a kill.

**Confinement is established before anything is unlinked**, and the first version of
this fix had that backwards. Reproduced: with a sibling directory outside the root
holding a symlink, the removal unlinked it and only *then* threw `refuse path outside
root` — a bypass of the blessed helper wearing the shape of a use of it. Both sides are
now real-pathed before the check, which also caught a second defect on the first run
after: comparing a real-pathed root against an unresolved target refuses its own
legitimate caller on a platform where the temporary directory is itself a symlink.

The sibling round-12 arms call the confined remover on browser profiles without this
pre-unlink, and are **not** exposed by it: their runner sets the temporary directory
inside the tree it cleans, and its own cleanup unlinks symlinks before the confined
removal. The exposure is specific to a driver invoked **bare**, with no runner beneath
it, which is how this arm runs.

## Reference consumer, and what it is not

The documented reference consumer is a consumer-facing hosted service an adopter runs
against their own account, read-only, and it **never runs in CI** — the repository does
not contact a third party's servers. It is a recorded observation with provenance, not
an acceptance criterion. An acceptance criterion that cannot fire is worse than an
honest observation, which is why one is not written.

The service is described by shape rather than named, and the same applies to its
endpoint vocabulary: a provider's API terminology identifies it as surely as its name
does, so de-naming that left the vocabulary in place would not have de-named anything.
Nothing below depends on which provider it is.

**Probe, 2026-08-21, unauthenticated and read-only, four requests.** The observation is
about which surfaces need the session:

| Surface | Observed |
| --- | --- |
| Bulk reference data | `200`, served without a credential |
| A collection readable by identifier, marked public in its own response | `200`, served without a credential; the response carries the privacy marking itself, so the distinction need not be assumed |
| Caller-identity endpoint | `200`, with an empty unauthenticated body rather than a refusal |
| An account-scoped endpoint | `403`, `"Authentication credentials were not provided."` |

**Residual, named rather than glossed:** whether the *private* variant of the
readable-by-identifier collection requires the session is **not established here**.
Confirming it needs one private identifier, which only the operator holds, and the
alternative — probing identifiers until a private one is found — is enumeration against
a third party and was not run. What is established is that the public variant is
genuinely open and that account-scoped surfaces are genuinely gated; the private variant
sits between them and is unmeasured.

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
- The reference-consumer probe is operator-run and has no results artifact. Its record
  is the table above, which is why the date and the status codes are in it.
- The privacy bound on the results artifact is stated as a prohibition — no origin, no
  credential, no fixture identity, no value read out of a storage entry or a cookie —
  rather than as an allowlist of recorded field classes. An allowlist was tried and was
  incomplete the first time it was checked against the artifact it described.
