# Plan: rfc0088-round11-binding-requirements

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

## Approach

Five independent measurement arms, each a driver in the existing RFC-0088
evidence tree at `/private/tmp/rfc0088-round9-evidence.C5FnKi`, promoted through
the tree's existing four-step cycle (`r9-promote.sh`: build archive → regenerate
the archive note → sync the RFC digest → verify figures).

The arms are ordered by **information value, not by the RFC's list order**. Arm
2 runs first because it is the only arm capable of falsifying a disposition
already recorded (D/item 6), and finding that out early is worth more than
finishing in order. Arm 5 runs last because it is a re-run of existing drivers
and carries the least new information.

Every arm follows the shape this evidence base converged on over ten rounds:

- an **enforcing arm** and a **control arm** that removes exactly the control
  under test, in the same run under identical conditions;
- **ground truth from an independent observer** — a destination's own receive
  log, a UDP packet count, a runtime error code — never from the component whose
  decision is under test;
- **read-back rather than assertion** for any mode, platform, or state;
- a `provenance` block and per-row `ok` fields, so `build-archive.py`'s gates
  (provenance, failing-row, `expectedFatal`, import-closure, privacy) apply.

New drivers write to `s3/r11-*`, `s2/r11-*`, `s1/r11-*`, `s5/r11-*` names. No
existing member name is reused, because round 10 twice overwrote a promoted
round-7 member at its own name and changed its digest.

## Constraints

- macOS 26.5.2 arm64 only. Decision B deferred Linux and Windows out of pilot
  scope, so no arm in this round runs on Linux.
- Playwright's browsers live under `$HOME/Library/Caches/ms-playwright`; a
  synthetic `HOME` loses them, so `PLAYWRIGHT_BROWSERS_PATH` is set explicitly in
  every allowlist.
- macOS caps Unix socket paths near 104 bytes — every arm binding a socket uses a
  short `TMPDIR` or the bind fails `EINVAL`.
- Node's permission model realpaths an absolute entry script's ancestors, so
  entry scripts are passed **relative** with cwd inside the granted scope.
- The renderer sandbox mode cannot be read back from a headless browser
  (`chrome://version` returns `ERR_INVALID_URL`); the `kern.procargs2`-class argv
  instrument is used when the page instruments report `readBack: false`.
- Drivers reproduce their round-7 path when `RFC88_SANDBOX` is unset; setting it
  opts into round-10/11 paths.

## Construction tests

Per-task `Tests:` below. Every task is **visual / manual QA** mode — the
deliverable is the observed behaviour of a real browser, sandbox profile, or
Node process — so no task carries a red stub (`no stub (manual QA)`). The
construction test for each arm is its **control arm**: the arm is admitted only
if the control actually failed, which is a test that can fail by construction.

Two cross-cutting checks run after all arms:

- `r11-fact-negative-tests.py` — one mutation per new fact, extending the
  round-10 mechanism; each mutates the artifact field a fact reads, confirms the
  fact fails, and restores.
- Manifest comparison of every touched member against `manifest-r7.sha256`
  before promotion.

## Design (LLD)

### Design decisions

- **Arm 1 does not terminate TLS.** The proxy decides on the `CONNECT`
  target line and then blindly pipes bytes. This is what makes the method
  unreadable, which is the measured cost recorded by AC2 — and it is the reason
  the arm can be a standalone destination-only measurement at all.
- **Arm 2 reads the controller at document start**, via `addInitScript`, not
  after load. Round 10 (R10-7) established that reading after load makes fresh
  and restored profiles indistinguishable because the worker calls
  `clients.claim()`.
- **Arm 3 discriminates by error code**, not by success/failure. A denial that
  cannot be told apart from a missing file is the "measured on a stand-in"
  defect (R10-5).
- **Arm 4 reuses round 3's planting code** rather than re-implementing the
  residue classes, so the arm measures the classes round 3 measured.

### Failure, edge cases & resilience

- Any driver that cannot complete sets `fatal`; `build-archive.py` refuses such
  an artifact unless declared via `expectedFatal`. This gate exists because
  round 10 twice produced drivers reporting all-pass while dying early.
- A control arm that passes when it should have failed **invalidates its own
  arm** and is recorded as such — it does not silently become a pass.

### Dependencies & integration

No new dependency, package, or toolchain. Every arm uses the evidence tree's
existing Playwright 1.62.0, Node v26.4.0, `/usr/bin/openssl`, and macOS
`sandbox-exec`.

## Tasks

### T1: Arm 2 — service workers disabled, and whether an auth flow survives

**Depends on:** none

**Touches:** `s3/r11-service-worker-suppression.mjs` (new),
`s3/r11-service-worker-suppression-results.json` (new)

**Tests:** manual QA, `no stub (manual QA)`. Control arm: the same restored
profile under `serviceWorkers: 'allow'` must report a controller at document
start. If it reports `false`, the fixture failed to persist a worker and the
whole arm is invalid rather than passing. Second control: the three auth
variants must all complete under `allow`, or the variants are broken rather than
the suppression being consequential.

**Approach:** Build a profile carrying a registered service worker (reusing
`s3/r10-restored-profile-realm.mjs`'s registration and UDP-probe mechanics),
close it, then restart against it under both `serviceWorkers: 'block'` and
`'allow'`. Record, per arm: controller at document start (init script, before
any page script), controller after load, service-worker-realm UDP packet count,
page-realm UDP packet count. Then run three synthetic auth-flow variants —
worker absent; worker registered but the flow completes without it; worker
load-bearing on the callback/token-exchange path — under both settings, and
record per-variant completion. Satisfies AC3, AC4, AC5.

### T2: Arm 1 — destination-only enforcement without TLS termination

**Depends on:** none

**Touches:** `s3/r11-destination-only-nonterminating.mjs` (new),
`s3/r11-destination-only-nonterminating-results.json` (new)

**Tests:** manual QA, `no stub (manual QA)`. Control arm: with the destination
policy removed, the forbidden destination's **own receive log** must show the
request arriving. If it shows nothing, the destination was unreachable for an
unrelated reason and the enforcing arm proves nothing.

**Approach:** A `CONNECT` proxy that classifies the target with
`s3/r4-destination-policy.mjs`'s existing production rule and never terminates
TLS. Three arms: policy on with a forbidden target (refused); policy on with an
allowed target (delivered, proved by the destination's log); policy off with the
forbidden target (delivered — the control). Separately record what the proxy
observed on the wire for an allowed tunnel, asserting the method is **absent**
from the observable bytes. Satisfies AC1, AC2.

### T3: Arm 3 — `--allow-addons` denied, with confinement intact

**Depends on:** none

**Touches:** `s2/r11-addon-denial-confinement.mjs` (new),
`s2/r11-addon-denial-confinement-results.json` (new)

**Tests:** manual QA, `no stub (manual QA)`. Control arm: with `--allow-addons`
granted, `process.dlopen` must reach `ERR_DLOPEN_FAILED` — a non-policy failure.
If both arms return the same code, the fixture is not measuring the addon gate.

**Approach:** Compose the macOS `deny default` profile with the Node permission
model exactly as round 10 task 3 did, then add arms varying only
`--allow-addons`. Per arm record: the `process.dlopen` error code, and the
synthetic browser-profile read (which must stay denied). The
`ERR_DLOPEN_DISABLED` / `ERR_DLOPEN_FAILED` split is the discriminator. Record
the compiled-addon bypass as an unmeasured residual. Satisfies AC6, AC7.

### T4: Arm 4 — one consumer per connection

**Depends on:** none

**Touches:** `s5/r11-one-consumer-per-connection.mjs` (new),
`s5/r11-one-consumer-per-connection-results.json` (new)

**Tests:** manual QA, `no stub (manual QA)`. Control arm: the shared-connection
arm must reproduce round 3's result — init script, origin storage, and committed
download all surviving into consumer B. If fewer survive, the planting or
teardown differs from round 3 and the unshared arm's clean result means nothing.

**Approach:** Reconstruct `s5/s5-round3.mjs`'s planting block from
`round3-evidence-archive.md`. Consumer A plants all eight classes, each verified
as planted. Then two arms: consumer B on the **same** connection (control,
expected three survivors), and consumer B on its **own** connection (expected
zero of the three). Report per class, not as an aggregate. Satisfies AC8.

### T5: Arm 5 — the two remaining macOS drivers, sandboxed

**Depends on:** none

**Touches:** `s1/r11-attachment-authorization-{sandboxed,off}-results.json`
(new), `s2/r11-deny-default-boundary-{sandboxed,off}-results.json` (new)

**Tests:** manual QA, `no stub (manual QA)`. The failable row is the mode
read-back: a run whose observed renderer mode disagrees with its requested mode
fails rather than reporting the other configuration.

**Approach:** Run `s1/r4-attachment-authorization.mjs` and
`s2/r5-deny-default-boundary.mjs` under `RFC88_SANDBOX` on and off, adding the
read-back assertion round 10 added to its task-1 and task-2 drivers, falling
back to the argv instrument when headless. State each driver's result
separately. Compare both drivers' round-7 members against `manifest-r7.sha256`
before and after. Satisfies AC9, AC10.

### T6: Promotion, note, RFC evidence layer, and negative tests

**Depends on:** T1, T2, T3, T4, T5

**Touches:** `docs/rfc/0088-notes/spikes/2026-08-18-experimental-round11.md`
(new), `docs/rfc/0088-web-pilot-foundation.md` (evidence layer only),
`docs/rfc/0088-notes/spikes/round7-evidence-archive.md` (regenerated),
`r11-fact-negative-tests.py` (new), `workspace.toml` (backlog entries)

**Tests:** goal-based. `build-archive.py` exits 0; `verify-note-figures-r7.py`
reports zero wrong and zero claimed-nowhere with the round-11 note added to its
corpus; `r11-fact-negative-tests.py` catches every new fact; `r9-gates.sh`
reports all gates OK; the RFC status line still reads `Experimental`.

**Approach:** Write the round-11 note stating each arm's result and every arm
that contradicts its disposition. Add the round-11 layer to the RFC's evidence
section **without** touching any disposition, blocker item, or the status field.
Extend the figure verifier's corpus to the new note. Write one negative test per
new fact and record each one-line result. Register the pre-existing `CAT-V-014`
failure and the native-addon residual in `workspace.toml [backlog].open`.
Satisfies AC10 through AC14.

## Rollout

- **Delivery:** **one PR, not the six this plan first specified — a deviation from
  the commissioning brief's "promote in increments, PR each", recorded here rather
  than left for a reader to notice.** It was feasible to split: each arm could have
  promoted its own artifacts and added its own note section. It was not done because
  the note is a single narrative whose headline claim ("two requirements do not
  hold") is a statement about all five arms together, and the RFC evidence layer is
  one entry — so five PRs would each have rewritten the same two documents, and the
  intermediate states would have published a note whose conclusion contradicted the
  arms not yet landed. The cost of that choice is a larger single review surface,
  and the reviewer is owed the reason. Each arm remains independently revertible at
  the artifact level. Nothing is behind a flag because nothing ships.
- **Infrastructure:** none. All work is local to the evidence tree and the docs
  tree.
- **External-system integration:** none. No live identity provider, no network
  destination outside loopback fixtures, no account.
- **Deployment sequencing:** T1–T5 are independent and may land in any order;
  T6 depends on all five because it publishes their figures.

## Risks

- **The arm-2 control may not reproduce.** If the restored profile does not
  report a controller at document start under `allow`, round 10's finding does
  not reproduce and arm 2 is invalid. Mitigation: this is exactly the failable
  row; report it as an instrument finding, do not proceed to conclusions.
- **`serviceWorkers: 'block'` may not suppress a *persisted* worker**, because it
  is a per-context option. That result would mean the D/item 6 requirement does
  not close the case it was written for — a finding, and the round's most
  valuable outcome, not a failure.
- **Arm 4's reconstruction may drift from round 3.** Mitigation: the
  shared-connection control must reproduce three survivors before the unshared
  arm is read.
- **A re-run overwrites a promoted member.** Mitigation: manifest comparison
  before promotion, restoring from the archive on any digest move.
- **Scope pressure to close a residual an arm discovers.** Mitigation: the spec's
  *Ask first* boundary — extending the round requires sign-off.

## Changelog

- 2026-08-18 — Initial plan. Arm order set by information value (arm 2 first)
  rather than the RFC's list order.
- 2026-08-18 — Executed. Arm order held; running arm 2 first was the right call —
  it contradicted D/item 6 within the first arm, which reframed how the remaining
  four were written up.
- 2026-08-18 — **T2's origin server was rewritten to be self-contained.** The plan
  assumed arm 1 and arm 2 could reuse `services.mjs`'s `createService`. They
  cannot: its route handlers are called with no arguments and can only answer 200,
  while both arms need a request header and a 401. `services.mjs` is a manifested
  member of the promoted archive, so widening its signature would have changed a
  promoted digest to suit new fixtures. Each arm owns its origin instead, and
  reproduces the receive log that helper exists to provide.
- 2026-08-18 — **Six instrument corrections (R11-1 to R11-6), four more than the
  plan's risk section anticipated.** Two are in controls this round wrote; four are
  in inherited apparatus and were found only because this round re-ran the
  inherited controls rather than trusting them. R11-6 — the published archive
  digest cannot converge, because the archive contains an artifact recording the
  archive's own size — is **diagnosed and deliberately left unfixed**: breaking
  that self-reference is an evidence-base design decision, and the spec's *Ask
  first* boundary puts it outside a round scoped to five arms.
