# Spec: rfc0088-round15-reference-consumer

- **Status:** Done
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0088](../../rfc/0088-web-pilot-foundation.md) — Experimental. This spec records one
    reference-consumer observation, five supporting measurements and one approver
    disposition in the amendment layer. It moves no status field, closes no blocker item,
    and creates no follow-on artifact.
  - [RFC-0093](../../rfc/0093-intent-scoped-completion.md) — the accepted intent is the
    whole round; it is delivered as one review unit in one session.
- **Contract:** none for production interfaces. This spec produces an RFC amendment-layer
  entry, one evidence note, one digest entry, one `[ini-002].work` path entry plus
  comment-only `[backlog].open` updates, and changes only the existing out-of-repository
  evidence apparatus named in the plan.

## Objective

**Open question 3's bar** waits on one thing. The 2026-08-23 amendment entry restates it
as two independent fixtures of differing render and authentication shape — measured in
round 14 — **plus one documented reference consumer an adopter runs against their own
account, as a recorded observation.** Round 14 supplied the fixture pair and an
*unauthenticated* four-surface probe. The authenticated half has never been run, because
it needs a human at a keyboard.

**This is the question-3 bar, not the whole exit.** Blocker items 1 through 6 are
untouched by this round: item 1's four unmeasured-sandboxed drivers, item 2's
unestablished DSSE signer identity, item 4's D7 disposition and item 5's argv half all
stand exactly as they stood. Both the 2026-08-22 and 2026-08-23 entries state that no
blocker item closes, and neither does this one. Whether the exit is reachable once this
bar is met is an approver judgement, not a claim this spec makes.

This round runs the observation. The operator signs in, attended, against their own
account, read-only, on **both admitted channels** — bundled Chromium and system Chrome.
The channel differential is a finding in its own right: this RFC has been corrected four
times for inferring one configuration's behaviour from another's, and the 2026-08-22
matrix admits both channels.

**Five further measurements** ride on the same attended sessions, because an attended
sign-in is the scarce resource and each has been waiting for one.

**The per-group interactive sign-in cost is the one that decides something.** The
2026-08-22 restatement makes worker policy a per-**group** control, realised as a separate
browser context. Fine grouping is the remedy for a worker-dependent destination forcing
workers on everything that shares its session — but only if drawing an extra group is
cheap. `rfc0088-destination-group-split-cost` is that slug.

**The question is whether a group can be *split*, not whether a fresh profile is
unauthenticated.** A fresh context with its own profile is unauthenticated by
construction, and `workspace.toml` already records that spike E showed as much. Measuring
only that would re-derive a known result and answer nothing. The measurement has to drive
the *sharing* arms — a context seeded from the seed group's storage state, and a second
persistent launch over a copied profile — because those are the mechanisms by which a
split could cost nothing. Only if all of them fail is the per-group cost one sign-in.

**Whether the login path registers a service worker** bounds how expensive item 6's
requirement is in practice. Its framing is deliberately *not* "the tension behind item
6": the 2026-08-22 entry dissolved that tension structurally, under the heading "Why the
tension is gone", by moving to the per-group unit. What survives is a landscape question
round 11 named as out of its own scope, and a real login path can answer it.

**Signing-identity observation #1** establishes the dated baseline a future RFC update
compares against. It cannot be closed here, which is why
`rfc0088-signing-identity-update-survival` was deferred on 2026-08-23. Round 12's arm
recorded only the requirement expression's *verdict* — no team identifier, no authority
chain, no browser version — so a vendor update that has already occurred on the measuring
machine passed with nothing comparable recorded. That is the deferral's cost, made
concrete.

**The private variant of the readable-by-identifier collection** is round 14's named
check-C residual. It needs one private identifier, which only the operator holds.

**Round 14's finding, tested against a third destination shape,** asks whether a
consumer-facing service does what two pinned containers did. It is included deliberately
and it is the highest-privacy operation in the round: it requires the operator's live
credential to transit harness memory. The controls that make that acceptable are AC10 and
AC11, and they are the reason it is in scope rather than excluded.

Separately, one carried residual needs a **disposition rather than a measurement**, and
this round records the approver's ruling on it.

### Sequencing, and what it costs

**The apparatus was built before this spec was approved; the measurement was not.** That
split is recorded rather than smoothed over. Construction (plan tasks T1-T6, plus a
loopback rehearsal the plan did not originally name) ran ahead of the approval gate at the
approver's explicit direction — "build fully, then hand you one command" — because the
attended sign-in is the scarce resource and an apparatus that is not ready when the window
opens wastes it. No repository code changed: the apparatus lives out of tree at
`~/.local/share/rfc0088-evidence`, and the only repository artifacts produced before
approval were this spec and its plan.

Three things the pre-approval construction established, which the plan as approved now
reflects: the harness cannot be agent-spawned (`/dev/tty` is `ENXIO` under a piping agent
and resolves to the agent's own channel under a pty one, so it refuses rather than falls
back); AC12's "every byte" formulation was not achievable and carries a named residual; and
cookie values are encrypted at rest while web-storage values are not, which qualifies round
14's finding by storage class.

The measurement itself is taken *after* approval, which is the ordinary order and
the opposite of round 14's. Acceptance criteria describing observed outcomes are therefore
written as **what the round must establish or name**, not as outcomes already known. A
criterion is satisfied by a measured answer or by a named residual carrying the one input
that would close it — never by prose that is true whichever way the measurement goes.

## Boundaries

### Always do

- Put every RFC hunk **below** the `## Amendments` anchor; the body above it is frozen.
- Record a residual that cannot be measured as a residual, naming the one input that
  would close it — never as a weaker claim that can be met.
- Re-run the inherited apparatus controls after touching anything shared, and the privacy
  sweep with its detector self-test, so a clean result is not a vacuous one.
- Supersede explicitly. This RFC treats the amendment layer as needing explicit
  supersession rather than chronological inference, so an entry that changes an earlier
  entry's statement must name it.

### Ask first

- Any third-party request beyond the declared allowlist AC16 fixes. The operator's own
  account is the only account touched.
- Adding any repository dependency, toolchain, or compile step.

### Never do

- **Capture anything during a sign-in window.** No screenshot, DOM read, network log,
  `recordHar`, `recordVideo`, trace, CDP session, route handler, console listener, or
  profile read. A screenshot of a login form is reach, and AD-3 is about reach.
- **Register a context init script on any context that will reach a login document.** An
  init script runs in every document in the context and Playwright exposes no removal
  API, so registering one is a capture that cannot be withdrawn.
- **Type into the login form.** The harness calls no `fill`, `type`, `insertText` or
  equivalent at any point. The operator types; the harness never holds the password.
- **Name the provider, or use its API or endpoint vocabulary.** Describe it by shape only.
  A provider's API terminology identifies it as surely as its name does, so de-naming that
  left the vocabulary in place would not have de-named anything.
- **Create a follow-on artifact.** RFC-0088 is `Experimental`: no file matching
  `docs/adr/\d+-.*\.md`, `docs/specs/rfc0088-(spec-)?[123]\b.*`, or
  `docs/specs/.*browser-session.*`.
- **Move the RFC's status field.** Acceptance is an approver act.
- **Make the reference consumer an acceptance criterion.** Ruling 9.
- **Run any of this in CI**, or add it to any gate chain. The repository never contacts a
  third party.
- Put a credential, personal identifier, account relationship, or destination origin in
  the repository or in any persisted byte. The operator's account-scoped record
  identifiers and group identifiers **are** personal identifiers: role labels, booleans
  and counts only. This rail governs its own wording — naming those identifiers in the
  destination's domain vocabulary would narrow the provider class as effectively as an
  endpoint name.
- **Record a behavioural fingerprint.** No verbatim cookie name, storage key name,
  service-worker scope, or exact byte length attributable to the destination reaches a
  persisted byte. Categorical and bucketed values only, and needle labels are positional
  (`cookie:0`) rather than the cookie's own name, so a refusal record cannot re-leak what
  the artifact refused.
- Pass any operator-supplied input through `argv` or the environment. RFC-0088 item 5
  records that the pilot's own confinement profile admits `kern.procargs2`, i.e. reading
  another process's argv, and the environment is inherited by every mutation child and by
  the browser process itself.
- Capture a fixture from the live account. Fixtures stay synthetic.
- Mutate any live account state, or enumerate identifiers against a third party.
- Put terms-of-service or case-law reasoning in any repository artifact.

## Acceptance criteria

- [ ] **AC1 — The sign-in window is a three-state sequence, and each blind-phase conjunct
  is separately asserted.** The states are **blind** (nothing read at all), **probe-only**
  (exactly one named read — the authenticated-state probe — and nothing else), then
  **instrumented**. A declared row asserts, as separately-mutated conjuncts, that on entry
  to blind: emitter listener counts are zero on page and context; `unrouteAll` has run and
  the route-handler count is zero; no CDP session exists; no init script is registered on
  any context that will reach a login document; `recordHar`, `recordVideo` and `tracing`
  are unconfigured for the run; and no `DEBUG`, `PWDEBUG` or `PLAYWRIGHT_*` variable is set
  in the harness process or any child it spawns. "No listener attached" alone does not
  satisfy this criterion — it addresses only the first conjunct.
- [ ] **AC2 — The operator's hand-back channel is named, carries no credential, and the
  harness never types.** The blind phase blocks on a keypress read directly from
  `/dev/tty`, not on the harness's stdin. `/dev/tty` alone does not establish the property:
  under an agent that allocates a pty it resolves to the agent's own channel, and under an
  agent that pipes stdio it fails `ENXIO` — measured, not assumed — whereupon the obvious
  `process.stdin` fallback would delete the control silently. So the harness **refuses to
  run** unless `/dev/tty` opens *and* its device differs from the device behind fds 0, 1
  and 2. It never falls back. A row asserts the harness invoked no
  `fill`/`type`/`insertText` for the run's lifetime.
- [ ] **AC3 — The per-group split cost is measured across three arms on both channels, and
  every arm's outcome is reachable.** The authenticated session the arms derive from is
  **the seed group**; the three arms are named for their mechanism, never "group B".
  - **Control arm** — a fresh persistent context with its own profile. Expected to require
    a sign-in; this re-derives spike E and is recorded as a control, not as the finding.
  - **Storage-state arm** — `browser.newContext({ storageState })` taken from the seed
    group. This one is observable **at the same instant** the seed group is separately
    proven authenticated, because `storageState()` reads live state safely.
  - **Copied-profile arm** — a **second `launchPersistentContext`**, not a second context:
    a user-data directory is only consumable by a second browser process. The seed group's
    browser is **closed before the copy is taken**, and `SingletonLock` and the
    `-wal`/`-shm` sidecars are handled explicitly, because copying a live profile captures
    the cookie store mid-WAL and yields an unauthenticated result indistinguishable from a
    real one — a false negative biased toward the very conclusion the round exists to
    avoid assuming. This arm's observation is therefore **post-close, not same-instant**,
    and that is recorded rather than glossed. Its copy root is inside AC13's scope.

  If any sharing arm authenticates without a sign-in, the per-group cost is zero and fine
  grouping is practical; if none does, the operator performs the second sign-in so the cost
  is demonstrated rather than predicted. The criterion fails if a probe never ran, if the
  seed group was not proven authenticated, or if the copied-profile arm cannot show its
  copy was intact.
- [ ] **AC4 — The reference-consumer observation is recorded with provenance, and asserts
  nothing about the third party in CI.** The observation carries its date, the channel,
  the surfaces exercised and their observed outcomes, in a table a reader can re-run. No
  acceptance criterion in this repository asserts the third party's behaviour, and no
  criterion for it executes in CI. AC17's grep is the check that establishes the second
  half.
- [ ] **AC5 — Whether the login path registers a service worker is measured under a
  read-back `serviceWorkers: 'allow'` context, and the halves the apparatus cannot reach
  are named.** Running under `'block'` would measure the driver's own refusal rather than
  the login path, so the option is set to `'allow'` and read back from the context.
  Registrations and their scopes are enumerated after authentication, and a document at the
  login path is checked for a controller. Two residuals are named, not glossed: whether a
  worker *mediated* the authentication request is not established, because observing it
  needs a network log inside the sign-in window; and the controller check is
  **same-session only**, because round 10 established that a persisted worker controls the
  *first document of the next session*, which a same-session check cannot see.
- [ ] **AC6 — Signing-identity observation #1 is recorded for the system channel only, as
  team identifier, authority chain and browser version — never a filesystem path.**
  `codesign` output embeds the binary path, which for a browser resolved under a home
  directory carries the operator's username. The record states that one installation
  cannot observe an update. The read runs with `cwd` set to the binary's directory passing
  a relative filename, pipes stderr, and drops every line before the authority chain, so
  neither argv nor the captured output carries a homedir-bearing path. So
  `rfc0088-signing-identity-update-survival` stays carried
  with its unblock condition unchanged. Its register comment is corrected: the 2026-08-23
  entry downgraded it from acceptance blocker to post-acceptance observation and the entry
  still reads "ACCEPTANCE BLOCKER", and it gains a pointer to the note carrying observation
  #1 so the deferral's "before" half is findable. The bundled channel carries no such
  record; digest pinning is its anchor.
- [ ] **AC7 — Every operator-supplied input is supplied out of band, never through argv
  or the environment, and is erased before any child exists.** Scope is the whole input
  set — destination host, each declared path, and the private collection identifier — not
  the identifier alone; round 14's shape was `process.env.RFC88_SPA_ORIGIN`, which is what
  an implementer reaches for by default. Each is read from `/dev/tty`
  at prompt time, or from a `0600` file outside the repository, and deleted from
  `process.env` before any mutation child is spawned or any browser is launched. The
  record states that `credbroker` is deliberately not used, because it ships no
  `[project.scripts]` and is a pure library in v1, so a Node harness cannot reach it
  without the toolchain the Ask-first rail fences.

  **Echo stays ON at these prompts, and the values are read back for confirmation before
  anything launches. Amended by the approver on 2026-08-23**, correcting an earlier form of
  this criterion that required a no-echo read. That requirement was reflex rather than
  reasoning: **no password passes through these prompts at all** — the operator types it
  into the *browser*, which is the whole point of the handshake — so what they collect is an
  origin and three URL paths, and suppressing them protects nothing. It does cost something
  real: a mistyped path fails the authenticated-state probe *after* the sign-in, so the trap
  is sprung only once the irreplaceable resource has been spent. Shoulder-surfing does not
  rescue the earlier form either, since the browser is about to display that origin, signed
  in, on the same screen. Terminal echo restoration (AC13) remains, because the harness may
  still alter terminal state on other paths. The private collection is requested
  unauthenticated and again on the authenticated session; outcomes are status codes and
  booleans. No enumeration is performed.
- [ ] **AC8 — Round 14's finding is tested against a third destination shape; the decoy is
  planted post-authentication; and absence is gated on decoy recovery.** The decoy is
  planted by `page.evaluate` on a fresh page **after** the authenticated-state probe
  returns — never by a context init script, which would run inside the login document and
  defeat AC1. **A decoy is planted per buffer class the credential can occupy** — a
  web-storage decoy and a non-`HttpOnly` decoy cookie on the destination origin — because
  recovering a leveldb decoy proves the scanner reads leveldb and says nothing about
  whether it can read the cookie store, and the absence bound is per class rather than
  global. "Bounded to buffers written post-authentication" names its mechanism: the profile
  tree is snapshotted at the instant the probe returns and only files created or modified
  after it are in scope, with the record noting that leveldb compaction makes this bound
  over-inclusive rather than under-inclusive. An at-rest **absence** is recorded only where
  that class's decoy was recovered **and at least one live-credential term was actually
  registered** — a search for nothing is not an absence — and the record carries
  `buffersRead` and `buffersSkipped` separately, any non-zero skip forcing
  absence-unverifiable, because the inherited scanner swallows read failures in a
  `catch { continue }` while still counting the file as scanned.

  **A buffer class whose values are encrypted at rest is out of reach of a byte-scan, and
  that is a measured platform property rather than a scanner failure.** Measured on this
  machine ahead of the attended run: Chromium writes cookie *names* to the profile in
  plaintext but encrypts cookie *values* under an OSCrypt `v10` tag, while web-storage
  values sit in plaintext in the leveldb log. So the decoy proves the scanner **reaches** the
  cookie store, and no value-absence claim about that class is possible by byte-scan ever.
  The row records such classes under their own verdict — never as `absence-unverifiable`,
  which would blame the apparatus for something it cannot fix and would bury the finding.
  This materially qualifies round 14's result: **its at-rest finding is storage-class
  dependent**, holding for a page-readable web-storage token and not established for an
  `HttpOnly` cookie. Encrypted at rest is not the same as safe — the key is in the OS
  keychain and a same-uid process can obtain it, which is the exposure disposition B already
  accepts. Whether the
  *issuing response* carried a cache directive is **not** measurable under this handshake,
  because reading it needs a response listener inside the sign-in window; it is recorded
  as such.
- [ ] **AC9 — The apparatus is split into a live capture layer and a pure row layer, and a
  synthetic capture-layer arm restores mutation coverage to the controls the split would
  otherwise strand.** Round 14's harness re-runs the whole driver per case; a driver that
  blocks on a human cannot be re-run per case. The row layer is a pure function from a
  recorded observation record and is mutation-tested with no browser and no sign-in. But a
  pure row layer can only flip fields the capture layer computed, which would leave the
  blind-phase enumeration, the at-rest scanner and its decoy recovery, the write gate's
  matching against a real credential, the authenticated-state probe, and each group arm's
  observation asserted by nobody — precisely round 14's "a control that cannot fail". A
  **synthetic** capture-layer arm therefore runs against a fabricated profile carrying a
  planted decoy and a planted sentinel credential, and a stub page with a known listener
  attached, contacting no third party. The arm's contract is split so the *enumeration* is
  covered and not merely the guard: `observeCaptureSurfaces(page, context) → record` is
  driven by a real stub page carrying a planted listener, route handler and CDP session,
  separately from the `enter(record)` predicate over a hand-supplied record. Synthetic
  probe and group-arm assertions are included. **`rowsFrom` schema-validates the
  observation record and throws when any field a row reads is absent**, with a case per row
  asserting rejection of a record with that field deleted — otherwise the two layers drift
  independently and a row computed over a field the capture layer silently stopped emitting
  reads `ok: true` without being evaluated. Only live-third-party-specific code remains
  uncovered, and that narrower limit is what the note states.
- [ ] **AC10 — Every declared row carries a mutation that changes that row's outcome, the
  harness throws on a stale anchor rather than skipping, and every anchor is unique within
  the mutable region.** A row that is a conjunction carries a case per load-bearing
  conjunct — AC1's blind-phase row most of all. Any row whose recorded outcome is a
  finding mutates **toward passing**. The unmutated baseline is recorded immediately before
  the harness runs, and the harness's own summary is persisted beside the results artifact.
- [ ] **AC11 — The two-pass write gate covers every byte the run persists, and the needle
  set is specified as a prohibition with an enumerated form set.** Gated surfaces are the
  results artifact, the AC9 observation record, the mutation summary and the refusal
  record — not "the artifact" alone. Record safety is stated as a **prohibition** — no
  credential, no origin, no personal identifier, no account relationship, no value read
  from a storage entry or a cookie — never as an allowlist of permitted field kinds; round
  14 tried the allowlist and it was incomplete the first time it was checked. Needle terms
  include every cookie value returned for the destination above a minimum length,
  registered at the moment it is read, with the length floor named as a number and the
  count of cookies excluded by it recorded so an exclusion is visible rather than silent
  (an `HttpOnly` session cookie is the shape this
  destination class most often uses, and it is unreadable from page script, so a
  page-storage-only needle set misses it entirely), plus `os.homedir()`,
  `os.userInfo().username` and `os.tmpdir()`. Encoded forms are enumerated and
  self-tested: utf8, utf16le, base64 at all three alignments, base64url, percent-encoded,
  JSON-escaped, and the bare registrable host as its own term. The needle set is
  **monotonic**, and every already-persisted surface is re-scanned on each registration —
  otherwise a byte persisted before the session cookie was read was gated against a needle
  set that did not yet contain it.
- [ ] **AC12 — Every byte written by harness JavaScript is scanned, and the bytes that are
  not scannable are named as a residual rather than covered by a claim that cannot hold.**
  The structural control comes first: **the harness is invoked by the operator from their
  own terminal, never spawned by the orchestrating agent**, so its streams are not attached
  to the agent's context at all. On top of that, within the harness process: no child ever
  inherits stdio; `uncaughtException` and `unhandledRejection` handlers are registered
  *before* the first browser launch, so Node's C-level fatal printer never runs, and those
  handlers cannot themselves throw; a rolling tail of `maxNeedleLength - 1` bytes is carried
  across writes, because a needle straddling two `write()` calls is invisible to a per-chunk
  scanner; and every Playwright error object is re-wrapped rather than rethrown — message
  replaced by an error class plus term labels, `stack` dropped — because a navigation or
  action timeout builds its message from the live document, including the full call log.
  **Named residual, accepted rather than papered over:** bytes written to fd 2 by code not
  executing JavaScript in this process — native crash handlers, V8 fatal errors, kernel
  signal messages, and anything written before the patch installs — are unscannable. Round
  14's mutation harness throwing `failures.join(',')` over raw child output is the specific
  in-process path this criterion closes.
- [ ] **AC13 — No temporary root survives any exit path, a survivor is fatal, and the
  removal path is recorded.** Scope is **every** temporary root the round creates,
  including the mutation harness's, not the browser user-data directory alone. Symlinks are
  unlinked first with a mechanism that cannot follow one; confinement is established
  **before** anything is unlinked; the confined removal's entry bound is raised with
  measured headroom and the observed entry count recorded, because the default bound is
  4096 and round 14's loopback profile measured 337 — a real post-authentication profile
  with a service worker, CacheStorage and code cache is a different order of magnitude, and
  a declined bound silently demotes the control to the unconfined forced path. The removal
  row distinguishes "removed by the confined path" from "removed by the forced fallback".
  Handlers cover SIGINT, SIGTERM, SIGHUP, `uncaughtException` and `unhandledRejection`.
  They are **persistent `process.on` listeners carrying an in-progress guard**, not
  `process.once` and not plainly re-entrant. `once` unregisters itself, so a second
  interrupt during a slow cleanup reaches the default action mid-removal; but a plainly
  re-entrant handler is worse — the second delivery runs the existence check while the
  first is still walking, sees the root apparently gone, and calls `process.exit(130)` out
  from under it, stranding a profile holding a live session behind a *clean interrupt*
  status. So a subsequent delivery is a no-op, the terminal existence check and exit happen
  exactly once, and a bounded escalation timer makes a hung cleanup exit non-zero rather
  than hang. Terminal echo is restored on every exit path, normal and interrupted alike.
  SIGKILL is the named residual.
- [ ] **AC14 — Both channels launch with credential-persisting browser features disabled,
  and no OS keychain item is created.** On the system channel the launched binary is the
  real vendor browser, which offers to save the operator's password and keeps its safe-storage
  key in the login keychain — neither inside the temporary profile AC13 covers. Both
  channels launch with password manager, autofill and crash reporting disabled and
  `--use-mock-keychain`, asserted **present in the launched command line** rather than
  assumed, because Playwright's default argument set is version-dependent. The keychain
  check is a before/after existence probe **by exit status only** — never `-w`, never
  `dump-keychain`, both of which would print the safe-storage key or a homedir-bearing
  path straight into an AC11 needle — and records three distinct outcomes:
  `absent -> absent`, `present -> present`, `absent -> present`. Only the third is a
  failure; the second establishes nothing and says so.
- [ ] **AC15 — Every *harness-originated* request stays inside a declared allowlist, and
  in-browser navigation is a named residual rather than a claim.** Scope is the harness's
  own `fetch` and `APIRequestContext` calls: `https` only, one declared destination host,
  an exact declared path list, `redirect: 'manual'` with per-hop re-validation — round 14's
  fetch follows redirects unconditionally, which is harmless against a pinned loopback
  container and is not harmless against a live destination carrying the operator's session.
  **In-browser navigation is explicitly out of scope and recorded as a residual**: a real
  sign-in fans out to identity-provider redirects, CDNs and fonts, and the only mechanism
  that could constrain it in-browser is the route handler AC1 forbids for the run's
  lifetime. The operator's own navigation is the compensating control. A declared row
  records that every harness-originated request stayed inside the allowlist.
- [ ] **AC16 — `rfc0088-native-addon-confinement-bypass` is re-scoped by approver ruling,
  and the amendment entry supersedes explicitly.** The approver ruled to narrow the entry
  to configurations that grant `--allow-addons`, keeping it carried. Because the
  2026-08-23 entry closes with "no other residual is relabelled", the new amendment hunk
  **names and supersedes that clause** rather than relying on chronological inference. The
  slug stays in `[backlog].open` and stays `carried` in the digest's disposition block, so
  no peer's slug-set comparison moves. The entry records what the ruling gives up: a
  carried residual no pilot work will close.
- [ ] **AC17 — The round's governance controls are green, and never-in-CI is asserted
  rather than stated.** The digest covers the new note with exactly one appended entry of
  at least 120 characters carrying asked / measured / changed and no prohibited apparatus
  figure; the decision surface carries one record per open question; every RFC hunk sits
  below the `## Amendments` anchor; the follow-on-absence detector's self-test passes and
  this round created nothing matching a follow-on shape; the disposition partition matches
  the register. Never-in-CI is asserted as an exit-code-safe **absence** check —
  `! grep -rq <pattern> <paths>` over the gate chain and workflow definitions — because a
  bare `grep` exits 1 on no-match, which a harness reads as failure rather than as the
  intended pass.
- [ ] **AC18 — The pre-existing apparatus failure is re-established as pre-existing, not
  asserted from memory.** `r12-fact-negative-tests.py` must be run against this branch and
  against a clean checkout of the default branch, and the differential recorded — round 15
  extends the shared apparatus tree, so "references nothing this round edited" is a claim
  that genuinely changes and must be re-derived. Carried as
  `rfc0088-r12-fact-negative-tests-red`. This round does not claim a green full gate chain.
- [ ] **AC19 — The round's verdict remains NOT FINAL, and residual movement is explicit.**
  No blocker item closes, no disposition is withdrawn, and the status field does not move.
  **Three** register entries change and all three are named here rather than discovered in
  a diff:
  `rfc0088-native-addon-confinement-bypass` is re-scoped per AC16, and
  `rfc0088-signing-identity-update-survival`'s stale classification is corrected per AC6.
  For `rfc0088-destination-group-split-cost`, AC3 satisfies the entry's literal unblock
  condition, so this round records the measured answer as a comment and puts the
  close-or-carry decision to the approver **with the measurement in hand** — a slug leaving
  the register changes the digest's disposition block, which is a disposition rather than a
  measurement.

## Testing strategy

Goal-based checks, one attended measurement arm, one synthetic capture-layer arm, and a
pure row layer with real mutation coverage. No production code changes, so no repository
unit surface.

| Criterion | Mode | Artifact that establishes it |
| --- | --- | --- |
| AC1, AC2 | TDD (`r15-synthetic-capture.test.mjs`, `// STUB: AC1`, `// STUB: AC2`) | Blind-phase row, one mutation per conjunct; a mutant attaching a listener, a route handler, a HAR recorder or an init script must flip it; `/dev/tty` device-differs-from-fd-0/1/2 refusal asserted |
| AC3, AC5, AC8 | Visual / manual QA (attended) | Declared rows in the results artifact, plus the synthetic arm's coverage of the scanner and probe |
| AC4, AC6 | Goal-based check | The note's observation tables |
| AC7 | TDD (`r15-inputs.test.mjs`) | Term seeded into `process.env`, `scrubEnv` called, a spawned child's inherited env and argv asserted clear |
| AC9 | TDD (`r15-synthetic-capture.test.mjs`, `r15-row-layer.test.mjs`) | Enumeration driven by a stub page; schema rejection case per row |
| AC10 | Goal-based check | Unmutated baseline recorded immediately before the run; mutation summary persisted beside the artifact |
| AC11, AC12 | TDD | Detector self-test over every enumerated encoded form; a planted needle must refuse the write and must redact the stream |
| AC13 | TDD (`r15-synthetic-capture.test.mjs`) | Planted `SingletonLock`; forced interrupt; an entry-bound decline asserting `viaForcedFallback == 1` specifically; a survivor asserted fatal |
| AC14 | Goal-based check (`// STUB: AC14` in `r15-synthetic-capture.test.mjs`) | `--use-mock-keychain` asserted present in the launched command line; before/after keychain existence by exit status, three outcomes |
| AC15 | TDD (`r15-inputs.test.mjs`) | Allowlist row; off-allowlist scheme, host, path and redirect hop each rejected. The synthetic arm issues no network request |
| AC16, AC17, AC19 | Goal-based check | Governance gate output; disposition partition |
| AC18 | Goal-based check | Differential against a clean default-branch checkout |

- **Governance controls** — `r13-digest-coverage.py` and `r13-decision-surface.py` with
  both self-tests, plus `r13-disposition-partition.py` against the pinned base.
  `r13-spec-consistency.py` hard-codes round 13's spec directory, so it exercises nothing
  of round 15's; it is run as a regression check that round 15 did not disturb round 13,
  and reporting its green result as this round's own evidence would be a skip dressed as a
  pass.
- **Inherited apparatus controls** — the archive self-tests and the privacy sweep with its
  detector self-test, because extending a shared tree has previously disabled a second
  harness silently.
- **Repository gates** — `lint-spec-status.py --root .`,
  `pytest tools/test_documentation_entry_links.py`, and `SKIP_SAST=1 make build-check`.

## Non-goals

- Taking the Experimental exit, or closing any of blocker items 1 through 6.
- Closing `rfc0088-signing-identity-update-survival`. It needs a second dated observation
  across a real vendor update.
- Closing `rfc0088-native-addon-confinement-bypass`, or commissioning a C++ toolchain to
  measure it. The approver re-scoped it; both alternatives were put and declined.
- Building the destination adapter contract the amended bar names. The 2026-08-23 entry
  moved it to Spec 1.
- Registering the new note in the figure-verifier document corpus. Doing so brings it
  under claim accounting, which this round did not commission; the note states the
  limitation.
- Dependency or CVE scanning of the out-of-tree apparatus's `node_modules`. It sits outside
  the repository, so repository CI cannot see it and no ecosystem scanner covers it. The
  gap is accepted and recorded rather than silently inherited.
- Measuring anything about a second account, a shared account, or any account that is not
  the operator's own.
