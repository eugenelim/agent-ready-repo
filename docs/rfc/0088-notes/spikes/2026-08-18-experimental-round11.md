# RFC-0088 Experimental round 11 — the binding-requirement round

**Status:** all five commissioned arms are complete. Two of them contradict the
requirement they were written to confirm, and that is reported here as the
round's principal result rather than smoothed over.

The 2026-08-18 approver dispositions answered all four decisions. Decision A
commissioned this round for one stated reason: **four of the five binding
requirements those dispositions attach are themselves unmeasured**. A requirement
no arm has exercised is a requirement, not a result. This round measures them.

**It measures the architecture and does not re-measure the apparatus.** No
coverage percentage, claim-accounting total, or mutation-harness figure is a
deliverable here — the same stopping rule rounds 9 and 10 carried, for the same
reason: round 9 established that the coverage figure moves when controls are
added, so a round that both adds facts and re-measures coverage reports its own
activity as progress.

## Reproduction identity

- Host: macOS 26.5.2, Darwin 25.5.0, arm64
- Node v26.4.0; Playwright 1.62.0 — the same versions as the promoted round-7
  evidence, verified before any measurement
- **Environment: an explicit allowlist, not the ambient environment.** Every arm
  ran under `env -i` with exactly `PATH`, `HOME`, `TMPDIR`, `LANG`,
  `PLAYWRIGHT_BROWSERS_PATH` and `RFC88_SANDBOX`. No `SSH_AUTH_SOCK`, no session
  token, no credential, no personal browser profile, no protected config. The
  runner is `run-r11.sh`, and `HOME` is a synthetic directory created per run.
- macOS only. Decision B deferred Linux and Windows out of pilot scope, so no arm
  in this round runs on Linux.

## The headline: two requirements do not hold as written

| Binding requirement | From | Round-11 result |
| --- | --- | --- |
| Service workers disabled | D / item 6 | **Does not close the case as written.** The mechanism governs new registrations; the realm it was written to close is on-disk state and survives it |
| One consumer per connection | D / item 3 | **Covers two of the three surviving classes, not three** |
| Deny `--allow-addons` | D / item 5 | **Holds**, and the denial is distinguishable from an unrelated failure |
| Destination-only enforcement without termination | C | **Holds**, with the cost measured rather than assumed |
| The two remaining macOS drivers, sandboxed | B | **Sandbox-invariant**, stated per driver |

## Arm 2 — service workers disabled (run first, and the reason why)

This arm ran first because it is the only one capable of falsifying a
disposition already recorded, and finding that out early is worth more than
finishing in the RFC's list order.

Item 6's requirement has two halves and the RFC names a live tension between
them: disabling workers closes the realm round 10 found, but some authentication
flows depend on service workers and the pilot exists to hand an
interactively-authenticated session to an agent. The RFC is explicit that this
is "an inference, and this RFC has been corrected four times for inferences of
exactly that shape".

### Half 1 — the control does not hold against a restored profile

The mechanism measured is Playwright's `serviceWorkers: 'block'`, which is a
**context** option. Whether it reaches a worker that already exists on disk is a
different question from whether it blocks registration, and it is the question
item 6 turns on.

**It does not reach it.** With the same restored profile in both arms, under
`allow` the restored profile reports a controller at document start: `true` —
reproducing round 10's finding in this run rather than by citation — and
under `block` it still reports `true` at that same instant. The profile
emits 4 UDP packets from the service-worker realm under `allow`,
and 4 under `block`. `getRegistrations()` still returns 1 registration.

The blocking is real, and that is what makes the result attributable: the
authentication arms below show registration genuinely refused under the same
setting. So the option governs **new** registrations and does not touch a
persisted one.

### The composed control that does work

Measuring one mechanism and declaring the requirement broken would be unfair to
the disposition, which says "service workers disabled", not "use Playwright's
context option". A persisted worker is on-disk state, so the mechanism that
reaches it removes that state — something a broker owning the profile directory
can straightforwardly do.

Composing both — purge the persisted registration, then block new ones —
**does** close it: purge plus block reports `false` at document start,
and 0 packets from the service-worker realm, with zero registrations
visible, and the directory actually removed is `Default/Service Worker`,
recorded from the filesystem rather than assumed from a layout.

**This is the constructive half of the finding.** Item 6's requirement is not
wrong; it is **under-specified**. Written as "disable service workers" it names a
control that governs registration. To close the realm round 10 measured it must
also require the profile's service-worker storage to be purged before the session
is handed over.

### Half 2 — whether an authentication flow survives, as a taxonomy

"Does auth break" has three different answers depending on how a flow uses a
worker, and collapsing them into one number is what makes the requirement look
either free or fatal. Three synthetic variants, each run under both settings.
Every variant completes under `allow` — the control without which a failure
under `block` would be a broken fixture rather than a consequence of suppression.

| Variant | Worker's role on the auth path | Under `block` |
| --- | --- | --- |
| `sw-absent` | none | **completes** |
| `sw-present-idle` | registers, never touches the auth path | **completes** |
| `sw-load-bearing` | the only thing that can complete the token exchange | **fails** |

`sw-absent` completes under block: `true`. `sw-present-idle` completes
under block: `true`. `sw-load-bearing` completes under block: `false`,
stopping at `token-refused:401`.

`sw-present-idle` is the informative row. A flow that merely *has* a worker is
unaffected: the cost of the requirement is confined to flows whose login path
genuinely depends on one. That narrows the RFC's open tension from "does this
break authentication?" to "does this destination's login path depend on a
worker?" — a question a pilot can answer for its own destination.

**What this does not establish**: which class real identity providers fall into.
That is a landscape question, not a fixture question, and no arm here measures
it. It is a named residual, not a result.

arm 2 records 9 of 12 rows passing; the three failing rows are declared
via `expectedFailingRows` because each failure **is** a finding.

## Arm 1 — destination-only enforcement without TLS termination

Decision C declined method policy and constrained egress by destination instead.
The RFC records the residual in its own words: destination-only enforcement "was
never measured as a standalone configuration… sound reasoning, not a promoted
arm". This is the promoted arm.

A non-terminating `CONNECT` proxy decides on the request line and then pipes
bytes. Ground truth is each destination's own receive log, never a proxy
decision: the allowed destination logs 3 receipts, the forbidden
destination logs 0 under policy, and 3 once the policy is removed.
That last figure is the control — it is the same destination, client and proxy,
with only the policy differing, so the refusal is attributable to the policy
rather than to a destination that was never reachable.

**The cost is measured, not assumed.** Every observed client-to-destination chunk
on an allowed tunnel is a TLS record: every observed chunk begins `0x16`
(22 decimal), and no HTTP method token appears in any of them. This is
precisely why method policy requires termination and destination policy does not
— the architectural fact decision C rests on, now an observation.

Because nothing terminates TLS, **no interception certificate exists anywhere in
this fixture**, which is what retires item 5's argv half for the pilot. The proxy
is asserted to be a plain `http.Server` as a runtime property of the object that
actually served the tunnels, not by pattern-matching the fixture's own text.

arm 1 records 6 of 6 rows passing.

## Arm 3 — `--allow-addons` denied

The denial holds, and — the part that matters — it is **distinguishable from an
unrelated failure**. Both arms load the same real file, which exists and is
readable and is not a valid Mach-O object: absent the flag `process.dlopen` fails
`ERR_DLOPEN_DISABLED`, and with the flag the same file fails
`ERR_DLOPEN_FAILED`. Two different codes for one file means the denial is the
gate rather than the file.

That discrimination is the whole design. "Addon loading failed" would have been
satisfied by a file that simply does not load — the stand-in defect round 10
found inside its own item-5 fixture (R10-5, where the argv probe measured "can I
exec `/bin/ps`").

The filesystem confinement survives, re-measured here rather than inherited: the
profile-only control reads it: `READ`, so the correction-9 defeat is real,
while the addons-denied arm reports `DENIED:ERR_ACCESS_DENIED`. It stays
denied in the `--allow-child-process` shape a real Playwright host needs.

Node itself emits `SecurityWarning: The flag --allow-addons must be used with
extreme caution. It could invalidate the permission model.` — the runtime, not
this round, is the source of the claim that makes the denial binding.

**Bound, not closed.** Whether a genuinely *compiled* addon loaded through an
open gate defeats the confinement is **not** measured: it needs node-gyp and a
C++ toolchain in the evidence tree, which is a new dependency and outside a
pre-acceptance spike. Carried as `rfc0088-native-addon-confinement-bypass`.

arm 3 records 8 of 8 rows passing.

## Arm 4 — one consumer per connection

Round 3 planted eight residue classes in one shared connection and found three
surviving a best-effort teardown. The planting and teardown here are **round 3's
own steps**, reconstructed from `round3-evidence-archive.md` rather than
re-derived — a re-interpretation written by this round would measure this round's
idea of the classes, not the ones round 3 measured.

In this run the shared-connection control reproduces
`contextState, download, initScript` — round 3's three survivors. Without that the unshared
arm's result would be consistent with the residue never having been planted.

Given the same planting, an unshared connection leaves `download`.

**So the requirement covers two of the three classes, not three.** The init
script and origin-scoped storage do not cross a connection boundary. The
committed download does, because it is a **filesystem** artifact rather than a
browser-connection one: separating the connection does not unlink a file already
written into the shared job root. Clearing that class needs job-root
partitioning, which is a different control from the one D/item 3 binds.

This refines the disposition rather than contradicting its direction: the
disposition says restricting sharing "sidesteps the three surviving classes". It
sidesteps two.

arm 4 records 5 of 6 rows passing; the download row is declared failing because
the failure is the finding.

## Arm 5 — the two remaining macOS drivers, sandboxed

Round 10's list of four unmeasured-sandboxed drivers lost two to decision B (both
were Linux). These are the two that remain in pilot scope. Stated **per driver**,
not as one aggregate summary:

`r4-attachment-authorization` passes 7 of 7 sandbox-off and 7 of 7 sandboxed.
`r5-deny-default-boundary` passes 11 of 11 sandbox-off and 11 of 11 sandboxed.

**Both sandbox-invariant**, with no row differing between modes in either driver.

The mode is read back rather than asserted, and a run whose observed mode
disagreed with its requested mode fails rather than reporting the other
configuration. `r4-attachment-authorization` observes the renderer sandbox
`false` off-mode and `true` sandboxed; `r5-deny-default-boundary` observes the
renderer sandbox `false` off-mode and `true` sandboxed.

Both drivers run **headless**, so — exactly as R10-2 predicted — the page
instrument goes blind and the reading comes from the OS-level argv instrument
(`ps argv (kern.procargs2 class)`). That instrument is itself the capability item
5 describes, which is why every artifact labels it.

## Follow-up arm — does the item-6 remedy preserve the session?

Commissioned by the approver on 2026-08-18, after this round recommended "purge
plus block" for item 6 and the recommendation itself turned out to be only
half-verified.

It was verified to **suppress the realm**. It was not verified to **preserve the
session** — which is the entire thing the pilot exists to hand over. A control that
silently destroys the authenticated session breaks the use case exactly as badly as
the realm it closes, and this RFC's own words about decision C were "sound
reasoning, not a promoted arm".

**Result: the remedy is safe.** Against a profile seeded by authenticating and then
registering a worker, removing only `Default/Service Worker`,
the worker purge leaves the controller `false` at document start,
with 0 registrations visible — and the server answers the restored
browser `true` on `/whoami`, the authenticated endpoint that checks the session
cookie rather than inspecting which files are on disk.

**The failable row is the control**, and it is the point of the design. An
"authenticated request still succeeds" check that could only ever pass would prove
nothing, so a second arm purges the **cookie** store instead of the worker store:
purging the COOKIE store instead answers `false`. So `/whoami` can fail, and
the row above means what it says.

Two smaller guards, both earned rather than assumed. The cookie store is a **file**,
not a directory, so a directory-only walk would have purged nothing and the control
would have passed for the wrong reason (the R11-1 shape). And the confined consumer
reads its own artifact, so a denial is confinement rather than a host whose
filesystem access is broken.

the item-6 remedy arm records 6 of 6 rows passing.

**What this does not establish**: a session carried in IndexedDB or Cache Storage
lives in a different profile store and is not measured here. The pilot's described
shape is a cookie-borne session.

## Follow-up arm — does a per-consumer job root close the third residue class?

Commissioned by the approver on 2026-08-18. Arm 4 found that one consumer per
connection clears two of the three surviving residue classes but not the committed
download, because that is a filesystem artifact and separating a browser
connection does not unlink a file.

This matters more than it sounds in this pilot's threat model: the artifact
consumer A downloaded was fetched **inside an authenticated session**. If consumer
B can read it, B obtains data derived from A's session — the session-theft shape,
arriving through the filesystem rather than through the browser.

**Result: the class is closed by partitioning the job root.** Composing
per-consumer job roots with the Node permission model — the confinement arm 3
already measured holding, including in the `--allow-child-process` shape a
Playwright host needs — a shared job root lets consumer B `READ` consumer A's
committed artifact, while a per-consumer root answers `DENIED:ERR_ACCESS_DENIED`,
while still reading its own artifact `READ`.

That last reading is the guard that makes the denial mean confinement rather than a
host whose filesystem access is broken for an unrelated reason.

**An operational requirement fell out of it, and it is easy to get wrong.** The
consumer host's own directory must **not** be an ancestor of any job root. The
first version of this fixture put both roots under the host's working directory
and granted read on that directory so the runtime could load its entry script —
which granted every job root along with it, and the partitioned arm READ consumer
A's artifact. The confinement had not failed; the grant had swallowed it. A broker
that keeps job roots underneath its own working directory gets no partitioning from
this control at all.

the item-3 remedy arm records 5 of 5 rows passing.

**What this does not establish**: the confinement is the Node permission model.
Native code loaded through an open addon gate is not mediated by it, so the
residual `rfc0088-native-addon-confinement-bypass` applies here too.

## Round-11 corrections

| # | Round-11 claim or control | What was established | Status |
| --- | --- | --- | --- |
| R11-1 | Arm 2's composed control purged the persisted service-worker registration | **It purged nothing.** The purge matched directory names only at the TOP of the user-data dir, but `launchPersistentContext` keeps profile data under `Default/`, so the real path is `Default/Service Worker`. The arm removed zero directories and reported the composed control FAILING — which a reader would have taken as "even removing the storage does not suppress the realm", the opposite of the truth. A purge that purges nothing is a control that cannot work | **Fixed.** The search is recursive and bounded, and the artifact records the directories actually removed (`Default/Service Worker`) rather than asserting a layout. With the real path removed the composed control passes: controller-at-document-start `false`, 0 packets, 0 registrations |
| R11-2 | The promoted manifest describes the tree that was promoted | **It cannot, for one member, on every promote.** `r9-promote.sh` runs `build-archive.py` FIRST and `r9-claim-accounting.py` fourth — and the accounting tool WRITES `s9/r9-claim-accounting-results.json`, a manifested member. So the manifest is computed, then a member it covers is overwritten. Dated rather than inferred: that file's mtime is `23:08:02` and `manifest-r7.sha256`'s is `23:07:59`, three seconds earlier, both from round 10's promote and both predating round 11. A manifest comparison run at any later time reports drift that no one introduced, which trains a reader to ignore exactly the check R10-3 added | **Fixed** by re-running `build-archive.py` after the s9 artifacts are written, so the manifest and the published archive digest cover the final bytes. Found by round 11's AC10 manifest comparison, which is the control that was supposed to catch this class |
| R11-3 | Round 10 fixed the drifting mutation-corpus denominator | **It fixed the instance, not the class, and the figure drifted again in the very next round.** Round 10 found this figure moving 23 → 29 as it added artifacts and patched it by excluding the `r10-` filename prefix. Round 11 added artifacts and the same figure drifted 23 → **31**, restating round 9's denominator against a corpus it never measured — the second occurrence in two rounds. A per-round exclusion list is a remedy that must be edited by every future round to keep working, which is a remedy that silently fails when someone forgets | **Fixed by removing the glob.** A live glob cannot express a historical set. The corpus is now pinned to the set round 9 RECORDED measuring, and every member is checked to exist and to sit outside `s9/`, so tampering or a vanished member fails the fact rather than shrinking it. Note also measured and rejected along the way: a `round <= 9` predicate over the artifacts' own fields does NOT work, because a re-run artifact keeps the ORIGINAL driver's round number — `r10-s1-lifecycle` reports `round: 3` and `r11-attachment-authorization` reports `round: 4`, so eight post-round-9 artifacts would have been admitted |
| R11-4 | A figure verifier pattern matches the note's prose | **Only at one line-wrapping.** Fourteen round-11 facts reported `claimed nowhere` purely because markdown wrapped the sentence between two words of the pattern, and four more because the phrase began a sentence and the pattern was lower-case. A figure silently dropping out of coverage when prose is re-wrapped is exactly what `figuresNotClaimedAnywhere` exists to catch, but it makes every future edit to the note a coverage hazard | **Fixed.** Every round-11 pattern is whitespace-tolerant (literal spaces became `\s+`), so re-wrapping the note cannot drop a figure. The four capitalised phrases were reworded to sit mid-sentence rather than weakening the patterns to case-insensitive, which would have let a genuinely different phrase match |
| R11-5 | Adding a fact to the shared verifier is safe for the controls that already use it | **It silently broke round 10's negative-test harness.** `r10-fact-negative-tests.py` carried its own hard-coded four-document corpus. Round 11's forty facts are claimed in the round-11 note, which that list does not contain, so every one of them counted as `claimed nowhere` and the harness aborted with `baseline not ok` — refusing to run its own twenty-five mutations. The round-10 controls were therefore not running at all, and the only reason this was noticed is that round 11 re-ran them rather than assuming inherited controls still worked | **Fixed structurally, not by patching both copies.** The corpus now has ONE definition (`corpus_docs.py`), which both harnesses import and which fails loudly if a named document is missing rather than silently shrinking coverage. Two copies of one list means one of them is wrong, and it is always the copy nobody remembered to update — the same shape as the privacy control that was duplicated inline in `r9-gates.sh`. Both suites verified after the change: round 10 catches 25 of 25, round 11 catches 40 of 40 |
| R11-6 | The published archive digest is reproducible by re-running the promote | **It is not, and no fixpoint exists.** `r9-claim-accounting.py` accounts for the archive's own size as one of the claims it extracts (`230,550 bytes`), and its output is itself a manifested member — so writing size *N* changes that file to size *N′*, the next pass records *N′*, and the size returns to *N*. Measured directly by iterating six passes: the digest does not converge, it settles into a **two-cycle**, alternating between two values. So a reader re-running the promote gets a digest that differs from the published one, on every run, for reasons that have nothing to do with the evidence. This is round 9's R9-23 self-reference (a tool reading a document that embeds its own output), now shown to be structural rather than incidental | **Fixed, on the approver's direction, after this note first recorded it as bounded-not-fixed.** Iterating is not the remedy and was ruled out by measurement: a loop to convergence was implemented, run, and removed, because a loop cannot converge a self-reference. The fix removes the self-reference at its source — `r9-claim-accounting.py` no longer accounts for ENVELOPE facts (archive size, digest, member count), which describe the container rather than the evidence and which `build-archive.py` already computes. **Verified by running the promote four times: runs 2, 3 and 4 produce an identical digest in both passes.** The strictly worse defect underneath it (R11-2) was fixed in the same round: the manifest covers the final bytes and matches its tree at rest, zero members disagreeing |

## Verification

Every figure quoted above is derived from a named artifact by the round-7 figure
verifier, which now takes this note as part of its corpus: **132 figures derived,
zero wrong, zero claimed-nowhere**.

**No figure here comes from a live glob.** Round 10 found this class and patched
the instance; round 11 found the patch failing again in the very next round
(R11-3), and removed the glob rather than extending its exclusion list.

**Each of the forty facts added for round 11 was mutation-tested individually** —
mutate the artifact field the fact reads, confirm the fact fails, restore. All
forty were caught and the tree restored clean. The test ships with the evidence
as `r11-fact-negative-tests.py`, because a fact not shown to fail is not a
control, and this project has produced vacuous passes exactly where that test was
missing.

No promoted round-7 or round-10 **results** member was overwritten by this round.
Every member was compared against `manifest-r7.sha256` before promotion, and the
manifest matches its tree **at rest** with zero members disagreeing — which it did
not before this round (R11-2).

**The published digest is reproducible, and was not when this note was first
written.** The archive SHA-256 quoted in the RFC used to alternate between two
values, because the accounting tool recorded the archive's own size and its output
is a member of that archive (R11-6). That self-reference is now removed and the
digest converges — verified by four consecutive promotes. Both handles hold: the
manifest matches its tree at rest, and re-running the promote reproduces the
published digest. Two
manifested driver *sources* changed deliberately —
`s1/r4-attachment-authorization.mjs` and `s2/r5-deny-default-boundary.mjs` gained
the sandbox parameterisation arm 5 needs — and both reproduce their original
artifact at its original path when `RFC88_SANDBOX` is unset, so an older
reconstruction still works and round 11's pair is opt-in.

## What is NOT done

- **The compiled-addon confinement bypass** (`rfc0088-native-addon-confinement-bypass`).
  Arm 3 measures the gate, not an addon.
- **Which class real identity providers fall into** for arm 2's taxonomy. The
  fixture establishes that the cost is confined to the load-bearing class, not
  how large that class is in practice.
- **Item 2's requirement** — a first browser-digest pin established from an
  independently verified channel — remains not measurable. It is a process
  commitment; no experiment closes trust-on-first-use, and none was invented.
- **Linux and Windows**, deferred by decision B.

No result in this note authorizes acceptance or implementation, no blocker item
is closed, and no disposition is revised. The RFC stays `Experimental`.
