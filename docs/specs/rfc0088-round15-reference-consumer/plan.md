# Plan: rfc0088-round15-reference-consumer

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

## Approach

Eleven tasks in dependency order, delivered as one review unit. The ordering is forced by one
scarce resource: **an attended interactive sign-in.** The operator is present for a bounded
window, four sign-ins at most, and everything needing a live authenticated session must be
ready before that window opens. So the apparatus is built and proven first against
synthetic state that contacts nobody, and the attended run happens once, in one pass, per
channel.

The second forcing fact is that **round 14's mutation harness cannot be reused as-is.** It
re-runs the entire driver per case; a driver that blocks on a human cannot be re-run per
case. T3 splits the apparatus in two so the assertion logic becomes cheap to mutate. But a
pure row layer can only flip fields the capture layer computed, and the review established
that this would strand the round's five most load-bearing controls in an uncovered layer.
T4 is the answer: a **synthetic** capture-layer arm, contacting no third party, that
restores mutation coverage to the blind phase, the at-rest scanner, the write gate, the
authenticated-state probe and the group arms. T4 is not optional scaffolding — without it
AC9 and AC10 are satisfied by a control that cannot fail.

The third is that **arms B and C of the split-cost measurement are the measurement.** Arm
A re-derives a result the register already records; only the sharing arms can show a split
costing nothing.

Constraints are not restated here. They live in the spec's Boundaries, which is their one
home; duplicating them into a second list is how two copies drift at the first edit.
Row counts, case counts, residual counts and closure tallies are likewise absent — their
canonical homes are `workspace.toml [backlog].open` and the digest's disposition block.

## Tasks

### T1 — Confirm the apparatus baseline and re-establish the pre-existing red

**Depends on:** none
**Verification mode:** goal-based check
**Tests:** no stub (goal-based). *Done when:* the out-of-tree evidence tree and the
operator-terms file are both present and **not** recreated; `s1/confined-remove.mjs` and
`s1/provenance.mjs` import cleanly; and `r12-fact-negative-tests.py` has been run against
**both** this branch and a clean detached checkout of the default branch, with the
differential recorded (AC18).

**Approach:** read before writing. The conventions this round inherits are round 14's and
are load-bearing in ways a summary loses — in-region anchor uniqueness, throw-on-stale-anchor,
pre-unlink confinement order, the two-pass write gate. Confirm each exists in the reference
driver before copying its shape.

`~/.local/share/rfc0088-operator-terms.txt` is an out-of-tree input to the privacy
detector, holding operator-specific terms that must never appear in a persisted byte. It
stays out of tree for the reason the vault handover does: naming its contents in the
repository would be the leak it exists to prevent. It is not recreated.

### T2 — Fix the input channel and the request allowlist

**Depends on:** T1
**Verification mode:** TDD
**Tests:** `~/.local/share/rfc0088-evidence/s3/r15-inputs.test.mjs` — `stub: true`,
carrying `// STUB: AC7` and `// STUB: AC15`. The stub asserts, against no browser: that a
no-echo `/dev/tty` read returns a value never present in `process.env`; that `process.env`
is clear of every supplied term before a child is spawned; and that an off-allowlist
scheme, host, or redirect hop is rejected.

**Approach:** round 14 read every input from the environment. That is safe against a pinned
loopback container and unsafe here: the environment is inherited by every mutation child
**and by the browser process talking to the live destination**, and RFC-0088 item 5 records
that the pilot's own profile admits reading another process's argv. Inputs move to a no-echo
`/dev/tty` read or a `0600` file outside the repository, and are erased from `process.env`
before the first child exists. `credbroker` is deliberately not used and the reason is
recorded: it ships no `[project.scripts]` and is a pure library in v1, so a Node harness
cannot reach it without the toolchain the spec's Ask-first rail fences.

The allowlist is `https` only, one declared host, an exact declared path list, redirects
disabled or re-validated per hop.

### T3 — Build the two-layer apparatus: live capture, pure row layer

**Depends on:** T2
**Verification mode:** TDD
**Tests:** `~/.local/share/rfc0088-evidence/s3/r15-row-layer.test.mjs` — `stub: true`,
carrying `// STUB: AC9`. The stub is the row layer's contract surface: it feeds a
synthetic observation record and asserts each declared row's outcome both ways, before any
browser or capture layer exists. It is red at PLAN because the row layer does not exist.

**Approach:** the capture layer holds everything touching the live session and emits only
sanitized primitives. Its safety is stated as a **prohibition**, not an allowlist of
permitted field kinds — round 14 tried the allowlist and it was incomplete the first time
it was checked. The at-rest scan runs inside the capture layer because it needs the
credential bytes and the profile, and emits `{found, decoyRecovered, buffersScanned}`.

The blind phase is a three-state construct, not a comment: **blind** → **probe-only**
(exactly one named read) → **instrumented**. Its entry asserts each AC1 conjunct
separately. The operator's hand-back is a keypress read from `/dev/tty`, never the
harness's stdin, so the orchestrating agent is not attached to the sign-in window's I/O.

### T4 — Build the synthetic capture-layer arm

**Depends on:** T3
**Verification mode:** TDD
**Tests:** `~/.local/share/rfc0088-evidence/s3/r15-synthetic-capture.test.mjs` —
`stub: true`, carrying `// STUB: AC9`, `// STUB: AC13`, `// STUB: AC1`, `// STUB: AC2`.
The stub asserts against a fabricated profile and a REAL page driven over loopback,
contacting no third party: a decoy is recovered per buffer class; a planted sentinel is
found and a term nobody planted is not; an unreadable buffer is counted as skipped rather
than silently counted as scanned; each blind-phase surface is *observed* when planted and
refuses entry; a planted `SingletonLock` does not demote removal to the forced path; an
entry-bound decline asserts `viaForcedFallback === 1` **specifically**; and a surviving
root is fatal. The write-gate assertion belongs to T5, which this task precedes, and is
not claimed here.

**Approach:** this arm exists because the T3 split would otherwise leave the round's
highest-consequence controls asserted by nobody. It is where the blind-phase conjuncts, the
scanner, the write gate, the probe and the group arms get real mutations. It contacts
nothing and needs no sign-in, so it can be run as often as it takes.

### T5 — Write gate, stream gate, and the removal controls

**Depends on:** T4
**Verification mode:** TDD
**Tests:** `~/.local/share/rfc0088-evidence/s3/r15-privacy.test.mjs` — `stub: true`,
carrying `// STUB: AC11`, `// STUB: AC12`. The stub asserts every enumerated encoded form
is detected — utf8, utf16le, base64 at all three alignments, base64url, percent-encoded,
JSON-escaped, bare registrable host — and that a planted needle both refuses a write and
redacts a stream.

**Approach:** the gate covers every byte the run persists, not the results artifact alone:
the observation record, the mutation summary and the refusal record are all new durable
surfaces this round creates. Needle terms are registered at the moment a value is read,
which is the only way an `HttpOnly` cookie value — unreadable from page script, and the
shape this destination class most often uses — gets a needle at all.

Stdout and stderr pass the same scanner. In an agent-driven run stderr is the orchestrating
model's transcript, and round 14's harness throws `failures.join(',')` built from raw child
output.

Removal covers every temporary root including the harness's own, raises the confined entry
bound with measured headroom above the observed count, distinguishes confined from forced,
and registers re-entrant handlers for SIGINT, SIGTERM, SIGHUP, `uncaughtException` and
`unhandledRejection`.

### T6 — Mutation harness over the row layer and the synthetic arm

**Depends on:** T5
**Verification mode:** goal-based check
**Tests:** no stub (goal-based). *Done when:* every declared row has at least one case;
each flips its row; each load-bearing conjunct of the blind-phase row has its own case; the
no-op case does not flip; a deliberately stale anchor **throws** rather than skipping; and
every anchor's in-region occurrence count is exactly one.

**Approach:** sweep every anchor's occurrence count in **one pass before** spending a run.
Rows whose recorded outcome is a finding mutate *toward passing*. Back up the driver and
baseline results before mutating — a killed harness leaves the mutant, and an untracked
file does not show up in `git status`.

### T6a — Rehearse the whole composition against a loopback fixture

**Depends on:** T6
**Verification mode:** TDD
**Tests:** `~/.local/share/rfc0088-evidence/s3/r15-rehearsal.test.mjs`. *Done when:* the
full composition runs end to end through the **same** `runObservation` entry the attended
run uses, against a loopback fixture that self-authenticates, and every declared row is
emitted with no fatal.

**Approach:** added after the plan was first drafted, because the modules were proven while
the composition between them was not — and the first attended run would have been the first
execution of that composition, at the cost of an irreplaceable sign-in. The driver is split
into a parameterised run body plus a thin terminal-backed entry point so I/O can be
injected; a rehearsal that exercised a *different* code path would prove nothing.

The fixture's login page submits its own form under script. That stands in for the human
and preserves the property that matters: the harness never types, and `waitForKey` only
waits.

This task earned itself immediately. It found that the cookie-class decoy could never be
recovered, which on investigation was not an apparatus fault but a measured platform
property — see the spec's AC8.

### T7 — Attended run, bundled Chromium

**Depends on:** T6a
**Verification mode:** visual / manual QA (attended)
**Tests:** no stub (attended). *Done when:* the arm-A/B/C sequence has completed on the
bundled channel, group A's session has been proven authenticated, and one observation
record has been written and passed the gate.

**Approach:** launch group A, navigate to the login path, **enter blind**, hand over, wait
for the `/dev/tty` keypress, transition to probe-only, confirm authenticated, then
instrument. Then arms A, B and C against an account-scoped surface. AC5, AC7 and AC8 ride on
group A's authenticated session; AC6 does not, being system-channel only.

Launch with password manager, autofill and crash reporting disabled and a basic password
store (AC14).

### T8 — Attended run, system Chrome, plus signing identity

**Depends on:** T7
**Verification mode:** visual / manual QA (attended)
**Tests:** no stub (attended). *Done when:* the same sequence has completed on
`channel: "chrome"`, the launched binary's team identifier, authority chain and version are
recorded as observation #1 with its date and **no filesystem path**, and no OS keychain
item was created.

**Approach:** identical sequence, one channel option changed, so the differential is a
differential rather than two differently-shaped runs. Never assert whether a given binary is
present — the resolver decides which binary launches, and `channel: "chrome"` is not the
engine CI judges.

### T9 — Write the note

**Depends on:** T7, T8
**Verification mode:** goal-based check
**Tests:** no stub (goal-based). *Done when:* the note exists under
`docs/rfc/0088-notes/spikes/`, follows round 14's shape (findings, apparatus, limits,
residuals named rather than glossed), names the provider by neither name nor endpoint
vocabulary, and contains no credential, origin, identifier or account relationship.

### T10 — RFC amendment, digest entry, register updates, and the gate chain

**Depends on:** T9
**Verification mode:** goal-based check
**Tests:** no stub (goal-based). *Done when:* every RFC hunk sits below the
`## Amendments` anchor and the new entry explicitly supersedes the 2026-08-23 entry's "no
other residual is relabelled" clause; the digest carries exactly one **appended** entry of
at least 120 characters with no prohibited apparatus figure; `workspace.toml` carries the
round-15 `[ini-002].work` path entry plus comment-only `[backlog].open` updates; and the
governance controls, the spec-status lint, the documentation-entry link tests and
`SKIP_SAST=1 make build-check` have each been run from the repository root with
`RFC88_REPO=$PWD` and `PYTHONDONTWRITEBYTECODE=1`, each result recorded green or named as
the carried pre-existing red.

**Approach:** append, never insert, in the digest. The two `[backlog].open` edits are
comment-only, so the slug set does not move and peers verifying against a base see nothing.
Run `r13-spec-consistency.py` from the repository root **only**; it resolves a relative
path. Check `sysctl -n vm.loadavg` before treating a `make build-check` timeout as a
failure. Judge every gate by its own exit code, never through a pipe.

## Rollout and recovery

Nothing ships to a user. Recovery from a failed attended run is to re-run it: profiles are
temporary and removed on every exit path, and the account is never mutated, so a failed run
leaves no state to unwind. If a sign-in window is interrupted, the handler removes the
profile and the run restarts from the top rather than resuming — a half-instrumented session
is not evidence.

The one irreversible thing is the operator's time. If the apparatus is not ready when the
window opens, the correct action is to close the window and rebuild, not to improvise
instrumentation while a live session is open.

## Risks

- **A capture surface survives into the blind phase.** The highest-consequence failure,
  because it is the one that reaches. Three surfaces are invisible to a naive listener
  check — `recordHar`, route handlers, and `DEBUG`/`PWDEBUG` — and an init script cannot be
  removed at all. Mitigated by AC1's separately-mutated conjuncts and by T4's synthetic arm,
  where a mutant that attaches each one must flip the row.
- **The decoy plant defeats the blind phase.** Round 14 plants it with a context init
  script, which runs in the login document. Mitigated by planting post-authentication with
  `page.evaluate` (AC8).
- **The confined removal declines on a real profile and silently becomes the forced path.**
  Default bound 4096; round 14's fixture measured 337. Mitigated by raising the bound with
  measured headroom, recording the observed count, and making the row distinguish the two
  paths.
- **A live credential reaches the model through stderr.** Mitigated by AC12.
- **All three sharing arms fail and the round only re-derives spike E.** That is still the
  answer the slug asks for, but it must be recorded as *measured across three mechanisms*
  rather than as a single fresh-context observation, or it is no stronger than what the
  register already holds.
- **The apparatus is not ready and the window is wasted.** Mitigated by T4 and T6 requiring
  a full synthetic pass before any attended run is scheduled.
