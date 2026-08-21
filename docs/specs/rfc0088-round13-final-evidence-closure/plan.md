# Plan: rfc0088-round13-final-evidence-closure

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

## Approach

Ten tasks in dependency order, delivered as the four review units the spec declares.
T0 relocates the tree and proves the relocation, because every later task's evidence
is worthless if the tree vanishes mid-round. T1–T3 and T5 are apparatus corrections that
each close or bound a named register slug; T4 is documentation and rides with unit 4. **T6 is the one net-new measurement arm.**
T7–T9 are the deliverables, authored last from evidence already closed.

Slug counts and closure tallies are deliberately absent from this Approach. Their one
canonical home is `workspace.toml [backlog].open` and the disposition block the digest
carries; restating them here would drift at the first edit to either.

The round's shape differs from round 12's. Round 12 was three commissioned
measurements plus apparatus repair. Round 13 is mostly *disposition*: most open slugs
are closable by correcting the apparatus rather than by measuring the subject, and the
residue that needs new measurement is bounded to one arm.

## Constraints

- No dependency, toolchain, compile step, real credential, profile, account, live
  authenticated session, local-account creation, or administrator operation.
- The operator term file and signing requirement file are supplied by the approver as
  paths. Their values never enter an artifact, a commit, or the transcript.
- Fixtures bind loopback ephemeral ports; recorded addresses are redacted.
- The **driver** never holds the token. The issuer and the browser renderer do, and the
  default-cache negative control deliberately persists it into the profile — the earlier
  phrasing ("only in the issuer process") contradicted the very fixture that proves it
  reaches browser storage. No bearer credential enters page-resident code.
- The run temporary root is ephemeral and `0700`, on the OS temporary volume so the
  platform sweeps what a kill leaves; the signing requirement is copied in per run at
  `0600` and dies with it. Startup cleanup is lease-guarded and refuses concurrent runs;
  a run aborts before creating a token if cleanup cannot complete.
- No absolute evidence-tree path is written into any script or artifact.
- `EXPECTED_FAILING_ROW_IDS` is never edited to clear a failure.
- The RFC's frozen body — everything above `## Amendments` — is not edited.
- Heavy gates run singly and nice'd. A kill under load is "no result".

## Risks

- **The apparatus has defected against every round that touched it.** Every round
  found the previous round's instruments carrying the defect they were built to
  detect, and the rate rose once the controls rather than the evidence became the
  subject. Round 13's own pre-EXECUTE review already confirmed seven such defects in
  round 12's shipped apparatus. Every change is mutation-proved before its slug is
  called closed, and a reviewer's prescribed remedy is verified against the code
  rather than trusted — three of round 12's prescribed fixes were wrong on contact,
  and two of this round's were.
- **Widening the mutable region can silently re-target existing mutations.**
  `.replace()` takes the first occurrence in the region, and one pre-existing needle
  already occurs twice inside even the current region. The uniqueness check therefore
  has to be an in-code assertion over the sliced region, not a manual pass.
- **A phrase-level sweep can span two different components.** Two listeners carry
  similar bounds; correcting them together would import one's claim onto the other's
  accepted risk. They are corrected separately and named separately.
- **The digest is the round's largest leak surface**, and it is currently checked by
  the weaker of the two detectors in the tree. T2 fixes the authority before T7 writes
  the document.
- **Registering the digest can break an inherited harness**, and the consumer list is
  longer than the obvious three. It is derived by search, not written by hand.
- **The machine reaps long runs.** Gates run singly; a killed run is re-run rather
  than recorded.

## Rollout

Four review units, in this order. Each leaves the repository and the apparatus
working, and units 1–3 reach their human gate with the spec at `Implementing`.

| Unit | Contents | Gate before handoff |
| --- | --- | --- |
| 1 | T0 | Both-direction tree walk; the pre-correction refusal observed; all three fact-negative harnesses green from the new tree |
| 2 | T1–T3, T5 | Declared gate order through `r9-gates.sh`; every new mutation observed to flip |
| 3 | T6 | The arm's control failed in the same run that admitted it |
| 4 | T4, T7–T9 | Full chain including `make ci` with SAST enabled; every enumerated disposition-control branch observed to fire |

**Sequencing that is load-bearing, and easy to get wrong:**

1. **Copy before delete.** The old tree is the snapshot until the new one is verified.
2. **Observe the pre-correction refusal before removing the old tree.** The old tree
   holds the only surviving copy of the pre-correction form; once it is gone the
   discrimination proof cannot be reproduced. This ordering is why T0's proof is a
   task step rather than a later verification.
3. **Fix the detector authority (T2) before writing the digest (T7).** Otherwise the
   round's largest leak surface is scanned by the weaker detector.
4. **Append to the shared derivation, never insert.** The promotion path consumes it
   positionally.
5. **Build `dist` before any build-check.** On a fresh worktree `dist/` is absent and
   the drift gate's leg returns empty — a skip that reads as a pass.
6. **SAST last, unskipped.** `SKIP_SAST=1` is admissible only for an intermediate
   build-check; the terminal `make ci` runs with it unset.

## Construction tests

T0, T7, T8 and T9 are goal-based checks. T1–T6 are visual/manual QA with no red stub.
Every task, deliverable-side included, is admitted only when a mutation or planted
failure was observed to flip its control — the goal-based tasks are not exempt from
that rail, because AC13's is an absence assertion and absence is the shape most prone
to passing for the wrong reason. Gate output retains control and harness counts;
neither published document does.

## Tasks

### T0: Relocate the evidence tree and prove path independence

**Depends on:** none · **Unit:** 1
**Touches:** the evidence tree's location; `r10-fact-negative-tests.py` (root
resolution); the run temporary root's creation and sweep

**Tests:** Goal-based. Every member compared on type, size, mode and SHA-256, as sets
in both directions, with any unexpected symlink refused — name equality is not
equivalence while the source is still the only copy. With the old location renamed away,
the pre-correction root resolution refuses and the post-correction form passes — both
observed, and observed before the old tree is removed. A planted absolute tree root in a member makes the
archive builder refuse — the exemption gate fires first because the plant widens the derived
set, so the control asserts refusal rather than naming one detector. Two concurrent runs are observed to be refused
rather than one deleting the other's root. All three fact-negative harnesses pass from
the new location.

**Approach:** Copy rather than move, excluding bytecode caches whose staleness is
keyed to the old path. Assert the absolute-path anchor is unique across the whole tree
before substituting it, then replace it with the same self-resolving form its two
sibling harnesses already use — that divergence is what made this a latent break, and
it was latent rather than loud only because the outer chain never invoked the harness
that carried it.

Separate the two durability concerns, which are not the same concern. The **tree**
becomes durable; the **run temporary root** stays ephemeral and `0700` on the OS
temporary volume, so the platform sweeps whatever a kill leaves behind. `TMPDIR`
points at the run root, the drivers create browser profiles beneath it, and a measured
control proves the live token is written into those profiles — so a durable run root
would leave a live token at rest wherever a kill interrupted cleanup, which the
temporary volume at least swept.

Startup cleanup acquires an atomic parent-level lease, refuses a concurrent run rather
than queueing it, and sweeps only verified-owned direct children after proving no active
lease holds them. An unguarded "sweep stale predecessors" would delete a peer run's root
— and this host regularly has several sessions live — while the removal helper confines a
target but cannot tell stale from active. If cleanup cannot complete the run aborts
before any token exists.

Because the durable location sits under a home directory, it is newly visible to the
`/Users/` detector. No member records the tree root today, verified; the control keeps
it that way.

**Closes:** `rfc0088-evidence-tree-durability`.

### T1: Make every selector name its own set, in the direction that fails closed

**Depends on:** T0 · **Unit:** 2
**Touches:** `verify-note-figures-r7.py` (glob call sites), `r9-privacy-sweep.py`
(file-set derivation and zero-files guard)

**Tests:** Visual/manual QA. The verifier re-derives identical facts for its earlier
inputs after the globs become closed lists. Deleting the round-13 spec from the
declared source makes the sweep name it absent.

**Approach:** The two directions are opposite and conflating them is how a detector
gets quietly narrowed. The **verifier's** live globs stand in for a historical set, so
they become explicit closed member lists — the file already does this at one call site
and documents why. The **sweep's** discovery must stay greedy, because turning it into
a closed list would drop the digest and every future note from privacy scope; it gains
a positive-membership assertion and a declared minimum instead. Today the sweep's list
ends with two unconditional literals, so its zero-files guard can never fire; the
guard is recomputed over the derived portion alone.

**Closes:** `rfc0088-verifier-members-selector`.

### T2: One privacy-term reader, one detector authority

**Depends on:** T0 · **Unit:** 2
**Touches:** `r9-privacy-sweep.py`, `build-archive.py` (shared reader, pattern
authority, member-scan loop), the new shared reader module `privacy_terms.py`,
`r12-fact-negative-tests.py` (its two term-source cases asserted one merged message
that splitting the refusal reasons correctly retired), and `r9-promote.sh` plus
`r9-gates.sh` for the anchor capture step and its gate lines

**Tests:** Visual/manual QA. Each of the four inherited refusal modes proved per
consumer, **plus the two new ones** — a sanctioned-placeholder term and a
corpus-colliding term each refused, which the earlier draft required in the criterion and
tested nowhere. The collision refusal was proved empirically before the criterion was
written: the supplied term set scans clean over the corpus and the digest, and planting one
of its terms makes the sweep report the class, so the detector fires and the terms do not
collide. An
unreadable member aborts rather than skips. A planted hit per identifier class is caught
over the digest. A missing prior anchor record refuses without the first-run flag; the
same file across both consumers passes; and **substituting the term file between the two
consumers inside one chain is observed to make the anchor object** — the check that
actually establishes the anchor is load-bearing. A planted omission of the shared module
from the member roster fails the new Python import-closure check.

**Approach:** Extract one reader; leave both call sites' failure modes observably
unchanged, and add the two refusals the reader documents but does not implement.
Fixing the reader alone is not enough: the member-scan loop swallows read errors and
continues, so an unreadable member is silently never scanned while the build proceeds
— a fail-closed reader inside a fail-open loop.

Point the sweep at the richer pattern set that already exists two files away, so the
digest is checked by the stronger detector. The sweep currently cannot see per-user
temporary paths or the platform's private temp roots even though Boundaries forbid
them; both reviewers found that gap from opposite directions.

The anchor is an HMAC keyed by a run-local random key, captured once per gate chain
with both consumers asserting against that one value — comparing "across runs" would
not catch substitution between the two consumers inside a single chain, which are
minutes apart. Commit no term-derived digest: with a small declared term count a
whole-file digest is a confirmation oracle for a guessed list, not a preimage problem.

**Closes:** `rfc0088-privacy-term-reader-deduplication`. Bounds, and does not close,
`rfc0088-privacy-term-identity-anchor` — cross-round identity stays operator-trusted,
so it is carried with that reason.

### T3: Bound the scan endpoint without removing coverage

**Depends on:** T0 · **Unit:** 2
**Touches:** `s3/r12-page-resident-token.mjs` (issuer scan handler, `EXPECTED_ROW_IDS`
and case-list order)

**Tests:** Visual/manual QA. An over-cap body refused; the truncation control's own
payload still reaches the scanner and still returns truncated; a malformed body and a
schema-invalid body each refused without terminating the listener; the refusal row
observed non-zero when a request is refused. Two further observations the earlier draft
promised in the criterion but never tested: a **multibyte payload straddling the
threshold** proves the cap counts bytes rather than code units, and a **concurrent
over-budget batch** proves the aggregate in-flight bound refuses rather than
accumulating. Each has a mutation that makes the bound fail.

**The aggregate byte bound needed a correction; the request-count bound is carried as a
stated residual.** An aggregate byte bound is a claim about simultaneity, and a batch
that merely *sums* past the budget proves nothing: the first form issued whole-string
bodies through one dispatch, every one returned successfully, and the bound never fired.
The bodies are therefore streamed in slices so several genuinely coexist, and that
observation is asserted.

The **request-count** bound gets the same over-subscription and the same read-back from
the listener's own counter — a client out of sockets produces failures that look exactly
like refusals, which would be a false pass — but it is **observed and not asserted**.
Whether 385 requests are simultaneously inside the handler depends on how fast sockets
open relative to how fast the handler drains them, which is scheduling rather than the
bound: asserted, it passed standalone three times and failed twice inside the gate
chain, once on the **unmutated** run. That is the shape of a flaky gate, and a gate that
fails for reasons unrelated to what it guards gets weakened until it passes — worse than
an honest residual. So the bound is in place, its refusals are recorded as evidence in
the artifact, and the row does not depend on them. Closing it needs a mechanism that can
hold the listener at saturation deterministically, and client-side concurrency is not
that mechanism.

**Approach:** The surface scan cap bounds what is *scanned*, not what is *received* —
the scanner returns truncated for anything above it without inspecting. So the naive
fix is doubly wrong: the driver deliberately posts one byte above that cap to prove
the truncation control, and it posts whole trace, archive and profile files whose size
is unbounded, so a cap derived from the scan cap would refuse both the control's own
request and every genuinely large surface. Derive the cap from the largest observed
surface in a recorded run plus headroom, strictly above the control payload's encoded
size plus envelope.

Count bytes on summed chunk lengths before any decode — the current accumulator
concatenates buffers onto a string, which decodes per chunk and yields code units, so
a "byte cap" would not be one. Add a schema check and a handler-level catch: the
handler destructures and base64-decodes without validation, so an empty object throws
inside an async handler with no catch and takes the listener down, letting any local
process abort a measurement.

Record a refused request as a distinct third state with its own row **outside** the
declared-prior-finding list. Without that, a surface that outgrows the cap in a future
browser version stops being scanned and the only row that fails is one already
expected to fail. Bound concurrency too, since every surface is dispatched at once.

**Closes:** `rfc0088-token-scan-body-bound`.

### T4: State each loopback bound at its own code's width

**Depends on:** T7 · **Unit:** 4
**Touches:** `workspace.toml` (register entry), the RFC amendment layer, the round-13
digest

**Tests:** Visual/manual QA. The browser bind endpoint's historical wording is asserted
**unchanged**, byte for byte, in every place it occurs — the assertion is that nothing was
rewritten, which is the opposite of the earlier draft's "no remaining instance" and was the
executable instruction that still prescribed the rewrite after the Approach had abandoned
it. The issuer listener's own wording is likewise unchanged. The new-evidence paragraph is
asserted present in the evidence layer. The two listeners are asserted separately so no
sweep spans both.

**Approach:** There are two listeners and the recorded claim is only wrong about one.

The **synthetic issuer's** HTTP listener is already stated wide in the round-12 note
and spec, so there is nothing to correct and a control asserting otherwise could not
report a failure. The digest inherits that wording and adds the widening the code
supports: the unauthenticated scan route is a live oracle over the token, answering
for caller-chosen bytes, and the page route serves the run decoy.

The **browser's unconfined bind endpoint** is what the register slug and the RFC's
same-uid corrections are about, and there the bound genuinely is too narrow — that
endpoint is loopback TCP with no client authentication and the platform grants no uid
restriction on loopback TCP. **Do not correct it in place.** That phrasing sits inside an
accepted disposition's scope, so widening the actor set would retroactively treat a wider
exposure as already accepted — a ruling this round may not make, and the earlier draft's
"a width correction is not a disposition revision" was an exemption invented to permit
exactly what the rules forbid. Preserve the historical text verbatim and record the wider
fact in the evidence layer as new evidence requiring re-ruling.

No bearer credential is added. The init script is built by the driver, so any bearer
credential would make the driver hold a token-equivalent capability, contradicting the
recorded property that the driver never holds the token — and request headers are
captured into the archive and trace files that this very arm then reads back and
scans. Inventing a control that damages a measured property in order to narrow a claim
is the wrong trade.

**Bounds, and does not close,** `rfc0088-same-uid-attach-exposure`: its unblock
condition requires an authorised second-uid mechanism, which this round does not
supply. Carried with the width correction landed.

### T5: Close mutation coverage by class

**Depends on:** T3 · **Unit:** 2
**Touches:** `r9-gates.sh` (self-test callers, cross-document consistency control), `build-archive.py` (self-tests,
staged-member plant/search/restore, sentinel), `r9-promote.sh`,
`s3/r12-page-resident-token.mjs` (mutable-region boundary, `run()` uniqueness
assertion, new cases)

**Tests:** Visual/manual QA. Each mutation observed to flip. The in-code uniqueness
assertion throws on a non-unique needle — proved by feeding it one. A decoy
`--self-test-*` flag with no caller makes the meta-check fail. The staged decoy is
recovered from the promoted state in the positive-control promotion, and absent after
restore.

**Approach:** It depends on T3 because T3 adds a control row, and the driver's inventory
guard hard-fails when the row list and the case list diverge in content or order. It does
**not** depend on T4: dropping the bearer secret left T4 with no apparatus change at all,
so T4 became pure documentation and moved to unit 4 behind the digest it writes into.

Four gaps with four causes. The missing-expected-row self-test is implemented with no
caller and has therefore never run — and it is not alone: a second self-test is in
exactly the same state, which the prompt did not name. So the fix is a **meta-check**
that enumerates every self-test flag and asserts each is invoked, closing the class
rather than the two instances. The token-encoding mutation is unreachable because the
encoding table sits above the region marker; widen the region to start after the
harness function, admitting the table while still excluding the harness's own case
literals, which is what the marker exists for. The staged-member decoy search does not
exist and its per-run decoy is never published outside the issuing process, so nothing
could have searched for it.

**Measured during execution, and it changes two of those four.** The browser-store
decoy is in the region but untargeted, and a case for it was written and run: removing
both page-side decoy writes did **not** flip its row. The row asks whether the
`user-data` surface kind has any buffer with the decoy recovered, and the run recovers
it from two — the Local Storage log the write produces, and the cached page response,
whose body carries the decoy independently. No assertion depends on the writes, so
they are plant coverage rather than a control, and the round's own rule applies: ask
whether the guard is redundant before writing a fixture for it. The case is dropped
with that reasoning recorded beside the case list.

Dropping one of the five encoded forms likewise did not flip the no-store row, because
the live token sits in the cached token response as plain JSON and the raw form finds
it. One entry of a defence-in-depth table is not load-bearing. That mutation is
therefore re-aimed at the whole table, which is load-bearing and does flip the row —
proving the at-rest finding rests on the scanner matching token bytes rather than on
an assertion. Widening the region is what made either mutation *reachable*, which is
what the criterion asks for; reachability and discrimination are separate properties
and this task establishes both, separately, per case.

Make uniqueness an assertion inside the runner, counting occurrences within the sliced
region — the existing guard tests the whole source, so a needle living only above the
region passes it and silently produces an unmutated mutant. One pre-existing needle
already occurs twice within the region and gets a unique longer form here.

For the staged decoy, run the positive control first: promote with the plant in place
and assert it *is* recovered. Restoring first and then asserting absence proves
nothing, because the verified restore already guarantees it. Guard the window with a
sentinel that only a digest-verified restore removes, since the builder reads members
straight from the tree with no staging area and the promote cycle builds twice.

Where a mutation refuses to discriminate, ask whether the guard is redundant before
writing a fixture. Round 12 deleted a symlink guard that the walk already performed;
a fixture there would have manufactured coverage for a check doing nothing.

**Closes:** `rfc0088-round12-mutation-coverage`, `rfc0088-staged-member-decoy-search`.

### T6: Inventory the worker-purge blast radius

**Depends on:** T0 · **Unit:** 3
**Touches:** a new `s3` driver; `r9-gates.sh` (arm registration); `build-archive.py`
(two `MEMBERS` entries and the origin-shaped-filename detector class AC8 requires)

**Tests:** Visual/manual QA. Removed/retained inventory recorded through the
confined-removal helper, with a control that fails when the purge is removed. Two further
observations AC8 requires: an **unknown taxonomy label is refused** rather than passed
through, and a symlink-bearing tree handed to the helper is refused rather than escaped.

**Approach:** Round 12 measured that the persisted worker store is profile-wide: both
roles register beneath one shared store, so removing it for one role removes it for
both. What is unrecorded is what else goes with it. Inventory removed and retained
paths over a synthetic tree only, and say so in the artifact — otherwise a later
reader takes it for a real profile's blast radius, which this arm must not imply.

Infer nothing about credential location or survival; the whole-profile control
established no credential conclusion. State bounds at the helper's actual width: hard
links are unresolvable by stat-based validation, symlink-bearing trees are refused
rather than escaped, and the time-of-check window is a concurrent-rename window. Hold
the two preconditions the existing harnesses depend on — no symlink inside the tree
handed to the helper, and bootstrap grants as siblings rather than descendants.

Build the profile with no navigation to a non-loopback origin and emit inventory entries
from a **closed generic taxonomy that refuses an unknown label** — an unconstrained
"structural label" can carry an origin fingerprint under a renamed category, so the
taxonomy has to reject rather than pass through. Any new per-destination distinction uses
an opaque per-round alias with an operator-held mapping. Profile filenames can encode
origins; today's corpus carries none, verified, and the detector keeps it that way.

**Closes:** `rfc0088-worker-purge-blast-radius`.

### T7: Write and register the consolidated scrubbed digest

**Depends on:** T1, T2, T3, T5, T6 · **Unit:** 4
**Touches:** a new note under the notes tree, `corpus_docs.py`, and every consumer of
that derivation as enumerated by search

**Tests:** Goal-based. Both declared sets checked with a positive control each — delete
one member, observe the mismatch. The apparatus-figure boundary check is proved over the
digest rather than merely passing: **each prohibited figure class is planted in the
digest in turn, the rejection observed, and the plant removed**. Every derived consumer
passes after registration.

**Approach:** Enumerate from the tree, never from a round range. The dated rounds are
not contiguous, several have no dated note, and the spike reports and surveys are
members — and the surveys sit one directory level above the spikes, so a
spikes-only enumeration under-covers. Because the digest is written into the same
tree, exclude it by path or the set demands the digest hold an entry about itself.
A document-keyed set also cannot cover the noteless rounds, so declare a second,
explicit roster and check both.

Register by appending. Registration is the point: an unregistered note is checked by
nothing, and registering it means every fact in it must be claimed and verifiable.
Record withdrawals qualitatively with no restated numeral — a digest that restates a
figure the artifacts no longer support would fail the very verifier that registration
subjects it to, turning the honesty requirement into a gate failure.

Derive the consumer list by search and record the command and its output. The obvious
three harnesses are not all of them; the promotion path consumes the derivation too,
which is the same "a harness carried its own list" class this task's risk cites.

### T8: Assemble the approver's decision section

**Depends on:** T4, T7 · **Unit:** 4
**Touches:** the RFC amendment layer only — everything at or below `## Amendments`

**Tests:** Goal-based. Six **unique** open-question records are parsed, each with a status
drawn from the allowed vocabulary and a resolving evidence link; a missing-status control
and a missing-link control are each observed to fail. Merely asserting that six numbers
appear would pass on a section that names them and says nothing. The boundary check passes
within the section anchor and is proved scoped by planting a figure inside and outside it.
The status field is unchanged and the diff is confined to the anchor range.

**Approach:** State what is being ruled on, not what was done. Cover all six open
questions with a status each, because two of them carry no recorded ruling and a
section that silently addresses four under-covers its own claim.

Open question 4's recommended candidate is contradicted; name the per-group amendment
the approver is asked to make. Open question 5's cache directive is a construction
requirement, and absence on browser-written buffers without a recovered plant is
unverifiable rather than clean. Open question 6's anchor is signing identity with
update survival unmeasured, and its **adoption cost is named on both sides**. This was
surfaced by having to construct a requirement expression by hand for this round's own
measurement: choosing signing identity means every adopter pinning a browser channel
writes and maintains such an expression, and re-derives it if a vendor rotates a team
identifier. Choosing a digest pin moves the burden to every browser update — which is
why the question exists at all. State both costs and rule on neither; an approver
picking an anchor is picking a friction profile, and the RFC records the cost of
neither option today.

Open question 3 is presented as the choice, not as a verdict: its recommended default
*would* block acceptance, and the approver must accept that bar or lower it
explicitly. Writing the recommendation in as the operative gate would be making the
ruling this round is forbidden from making — the RFC's own stated acceptance condition
is the answered decision set, and the bar for question 3 is a recommended default.
Cite it as such.

### T9: Partition the open slugs and close the round

**Depends on:** T8 · **Unit:** 4
**Touches:** `workspace.toml` (`[backlog].open`), the RFC's round-13 amendment entry,
the digest's disposition block, the PR description

**Tests:** Goal-based. Every failure branch the partition control enumerates is planted and
observed to fire before the check is admitted; the branch list is obtained from the control
itself rather than restated here, because a count in prose is a second home and this plan
has already shipped a stale one three times. The follow-on-absence detector is
exercised against a **synthetic path-set fixture outside the repository**, never by creating
an RFC-shaped artifact in the live tree, because creating one is the exact act the
Boundaries forbid.

**Approach:** The set is pinned by slug prefix and cardinality, not by substring: one
register entry contains the string only in its source field and is not part of this
round. The two shaping-queue slugs are not in this table at all, so they are listed
separately rather than filtered by a type field the register entries do not carry.

Two slugs land in `closed-retained` rather than `closed`. Their work completes here, but
the round-12 spec's `(deferred: …)` markers resolve against `[backlog].open` only, the
frozen-document rule forbids editing that spec's body, `[backlog].closed` admits only
defects, and widening the lint invariant needs an RFC. The repository already settled this
shape — see the `starlight-migration-rfc` entry, whose comment records the same four dead
ends — so membership is retained with an annotation naming what satisfied it. Do not
attempt to check the predecessor's criteria; that is the frozen-body edit the convention
forbids, and it was this plan's own earlier mistake.

Partition a committed pre-round snapshot, because closing a slug deletes it and the
set becomes unre-derivable exactly when the round succeeds.

Record converted concerns in the amendment entry, not in the frozen body. The
follow-on-artifacts section sits above the amendment anchor, and editing what Spec 1,
2 or 3 is scoped to do is a meaning-changing body edit — and that section's own text
forbids creating those artifacts while the RFC is Experimental.

Record the verdict — **not final, and what remains** — in the digest and the amendment
entry, with the PR description pointing at them. A disposition recorded only in a PR
description rots.

## Changelog

No entry. This round changes documentation, an out-of-repository evidence apparatus,
and `workspace.toml`; the changelog is scoped to released artifacts and has never
carried a heading for repository or tooling work.
