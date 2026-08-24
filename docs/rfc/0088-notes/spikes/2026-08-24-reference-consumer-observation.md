# RFC-0088 round 15 — reference-consumer observation and per-group split-cost measurement

**Status:** measurements complete; residuals and decision surface carried to the approver; RFC
amended 2026-08-24.

This round runs the attended observation the 2026-08-23 amendment entry declared as the
open-question-3 bar. An operator signs in to a hosted consumer-facing service against their own
account, read-only, on both admitted channels — bundled Chromium and system Chrome. Five further
measurements ride on the same attended sessions.

## Findings

### The authentication oracle does not discriminate on this destination class

The per-group split-cost measurement ran the three declared arms on both channels, with the seed
group signed in. On both channels, the authenticated-state oracle used to determine whether a
context carried the session returned a non-discriminating result.

On the bundled channel, the oracle returned "authenticated" for a fresh, never-signed-in context
used as the control arm. A probe that cannot distinguish authenticated from unauthenticated cannot
determine whether a sharing arm carried the session, so the storage-state and copied-profile arms
are void.

On the system channel, two consecutive unauthenticated renders of the account-scoped surface
produced different response bodies. The rendered-comparison oracle depends on a stable
unauthenticated baseline; with an unstable one, no rendered comparison is trustworthy and the arms
are void by the same reasoning.

The measured answer is that the three-arm method produces a null result on this destination class
— not because the arms failed to run, but because no discriminating oracle could be established on
either channel. The `rfc0088-destination-group-split-cost` unblock condition reads "a spike
measures the per-group interactive sign-in cost". An attended spike ran the three-arm measurement
against a real destination. The measured result is null. Whether that null satisfies the spirit of
the unblock condition, and therefore whether the slug closes or remains carried, is put to the
approver with the measurement in hand.

The second sign-in demonstration on the system channel was skipped by the operator. Since the
oracle was void on both channels, the demonstration would have confirmed nothing additional.

### No service worker registered at the login path, on either channel

Both attended runs recorded zero service worker registrations after authentication, and no
controller was present at a document loaded from the login path. The service worker option was set
to `allow` and read back from the context on each run.

Two residuals are named. Whether a worker *mediated* the authentication request is not
established, because observing it requires a network log inside the sign-in window, which the
blind-phase prohibition forbids. Whether a worker registered during one session controls the *first
document of the next session* — which round 10 established as the meaningful surface — is not
established by a same-session check.

### The at-rest finding is storage-class dependent, confirmed on both channels

A decoy was planted per buffer class after authentication, and a registered credential term was
scanned for in each class.

**Web storage** (leveldb): the decoy was recovered on both channels, and the registered credential
term was found. The at-rest presence finding from round 14 extends to this destination class for
this storage class.

**Cookie store** (SQLite): the planted decoy cookie was not recovered on either channel. Chromium
encrypts cookie *values* under the platform's protected-storage scheme on macOS, while cookie
*names*, domains, and paths remain in plaintext. The at-rest scan cannot recover a decoy planted
as a cookie value and cannot make a byte-scan absence claim against that class. A registered
credential term was found in the cookie store on both channels — indicating the term appeared in
plaintext-accessible metadata rather than in a decrypted value, consistent with the cookie store
holding the credential under an encrypted form the harness cannot read but whose plaintext metadata
the scan reached.

Round 14's at-rest finding is therefore qualified by storage class: it holds for page-readable
storage where values are written in plaintext and is not established for the cookie class where
values are encrypted at rest. That is a platform property rather than a scanner limitation.

### The private variant of the readable-by-identifier collection is gated at the body level

Round 14 named this residual: the private variant requires one identifier the operator holds, and
probing identifiers to find a private one is enumeration against a third party, which was not run.

On both channels, the authenticated and unauthenticated requests to the private surface both
returned status 200. The response bodies differed: the authenticated response was larger. The
surface is access-controlled at the body level, not at the HTTP status level. The residual is
closed.

### Signing identity observation #1 (system channel)

| Field | Value |
| --- | --- |
| Team identifier | `EQHXZ8M8AV` |
| Authority chain | Developer ID Application: Google LLC (EQHXZ8M8AV) → Developer ID Certification Authority → Apple Root CA |
| Browser version | 151.0.7922.170 |
| Observed at | 2026-08-24 |

No OS keychain item was created: the before/after existence probe recorded `absent → absent`. The
binary was resolved by the Playwright channel resolver; no filesystem path is recorded.

One installation cannot observe a vendor update. `rfc0088-signing-identity-update-survival` stays
carried with its unblock condition unchanged until a second dated observation is taken across a
real update.

## Apparatus

Two attended runs, one per channel. Each follows the same three-state sequence: **blind** (nothing
read) → **probe-only** (exactly one authenticated-state probe) → **instrumented**. The operator
signs in during the blind phase; the harness never types. Inputs are supplied at prompts from the
operator's own terminal (`/dev/tty`, device confirmed to differ from fds 0, 1 and 2) and erased
from the environment before the first child is spawned or any browser is launched.

The apparatus is split into a live capture layer and a pure row layer. The capture layer emits
only sanitised primitives to the row layer, which is a pure function of the observation record. A
synthetic capture arm, contacting no third party, runs a fabricated profile with planted decoys and
known surface attachments; it restores mutation coverage to the controls the two-layer split would
otherwise leave unasserted. The mutation harness certified the four mutable modules before the
attended runs: `result: "ok"`, 22 mutation cases, no-op detected.

Temporary roots: both runs removed 3 roots each, all via the confined path (0 forced fallback).
Entry counts observed: 1,239 (bundled channel), 1,119 (system channel). No root survived any exit
path.

Privacy: a two-pass write gate covered every persisted byte. Needle terms registered: 62 (bundled),
63 (system), including every cookie value above the minimum length, `os.homedir()`,
`os.userInfo().username`, and `os.tmpdir()`. Eight cookies fell below the length floor on each
channel; the exclusion count is recorded so the exclusion is visible rather than silent. No refusal
was triggered on either run. Stdout and stderr were not attached to the orchestrating agent's
channel — the harness is invoked by the operator from their own terminal.

The signing identity read ran with `cwd` set to the resolved binary's directory and passed a
relative filename; stderr was piped and every line before the authority chain was dropped, so
neither argv nor the captured output carried a path that includes the operator's home directory.

## Limits

- **The oracle does not discriminate.** The split-cost measurement produced a null result on this
  destination class. This is a property of the destination, not of the apparatus; a different
  destination with a stable, discriminating authenticated-state signal might yield a non-null
  result.
- **One destination class.** The null oracle result and the storage-class differential do not
  generalise to other destination classes.
- **Service worker mediation is not established.** The blind-phase prohibition forecloses the
  network log needed to observe whether a worker mediated the authentication request.
- **Next-session controller is not established.** The apparatus can check for a controller in the
  current session only; round 10 established that the relevant surface is the first document of
  the *next* session, which a same-session check cannot see.
- **Cookie-store absence cannot be claimed.** Cookie values are encrypted at rest under the
  platform's protected-storage scheme. The recovered plaintext-metadata presence finding confirms
  the scanner reaches those files; it says nothing about whether a plaintext value absence would
  be detectable there.
- **A single signing identity observation cannot observe update survival.** The slug stays carried
  until a second observation crosses a real vendor update.
- **In-browser navigation is outside the request allowlist scope.** The allowlist covers
  harness-originated requests only; the operator's own navigation during sign-in fans out to
  identity-provider redirects, CDNs and fonts that the harness never constrains.
- **The second sign-in demonstration was skipped.** The system channel's harness offered to
  confirm the per-group cost by a live demonstration; the operator skipped it. Since the oracle
  was void, the demonstration would not have established the split cost.
- **This note is not registered in the figure-verifier document corpus.** Its figures are carried
  by the results artifacts rather than by claim accounting; registering it would bring it under the
  claim-accounting requirement, which this round did not commission.
- **Dependency scanning of the out-of-tree apparatus is not in scope.** The apparatus resides
  outside the repository and is not covered by repository CI or any ecosystem scanner.
