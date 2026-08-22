# RFC-0088 round-13 consolidated evidence digest

> Discipline: consolidation of prior evidence. This document introduces no
> measurement of its own.

**Purpose.** Carry every prior RFC-0088 round and spike in one document, so an
approver can read the evidence base without walking the notes tree. One entry per
enumerated member, withdrawals and reversals included. "Readable in one sitting" is
the intent; the observable is the coverage of the two declared sets below.

**Status.** RFC-0088 remains `Experimental`. This digest decides nothing, closes no
blocker item, and revises no disposition. Where it records a wider fact than a prior
disposition assumed, it says so and asks for re-ruling rather than treating the wider
fact as accepted.

**What this document deliberately does not contain.** No coverage percentage, no
claim-accounting total, no mutation-corpus size, and no harness count. Those are
apparatus figures; they live in gate output and in the artifacts, and restating them
here would create a second home for a value whose only home is a control's own
enumeration.

## The two declared sets, and why there are two

Coverage is checked against two sets, because either one alone under-covers.

**Set one — the recursive document set.** Every Markdown document under the notes
tree, at any depth, **excluding this digest by path**. The exclusion is structural,
not a convenience: this digest is written into the tree it enumerates, so without it
the set would require the digest to carry an entry about itself.

The recursion matters. Four surveys sit one directory level *above* the spikes
directory, so a spikes-only enumeration silently under-covers by exactly those four.

**Set two — the explicit rounds roster.** A document-keyed set structurally cannot
cover a round that has no dated note of its own, and several rounds have none: the
first run's evidence is the six S-spike notes, rounds five and six share one
document, and rounds seven, eight and nine share another. The roster is therefore
declared explicitly rather than derived from filenames.

Each set has its own positive control: delete one member and the mismatch is
reported.

---

## Set one — the enumerated documents

### Surveys and imported evidence

**`cross-pack-consumer-pressure-test.md`** — Asked whether the proposed pack shape
survives contact with a consumer that did not design it. Applied an architecture
pressure test rather than a measurement. Changed the framing of the consumer
boundary; it is evidence about design pressure, not about runtime behaviour.

**`playwright-contract-and-browser-landscape-survey.md`** — Asked what the browser
automation contract actually guarantees about ownership, handoff, and dependency.
Surveyed practitioner patterns. Grounded the RFC's browser-ownership and handoff
decisions; it is prior art, not a run.

**`plugin-contract-distribution-and-reference-adapter-survey.md`** — Asked how
adapter contracts, distribution, and construction fixtures are handled in practice.
Surveyed practitioner patterns. Grounded the provider-pack and distribution
decisions.

**`web-connectors-and-aggregation-survey.md`** — Asked what the connector and
aggregation boundary looks like at the destination scope. Imported architectural
conclusions from a source survey and adapted them. Preserved those conclusions
without re-deriving them; the adaptation is the contribution.

### First-run spikes

Each of the six carries its own verdict line, and those verdicts are the first run's
ledger. They are recorded here as they stand, including the blocked ones.

**`spikes/s1-persistent-bind-lifecycle.md`** — Asked whether a persistent bind
lifecycle could be established. Blocked; the Experimental exit is closed on this
axis. Changed nothing by measurement, and its blocked state is load-bearing: later
rounds inherit it.

**`spikes/s2-artifact-host-and-dependency-gate.md`** — Asked whether artifact and
host construction, and the dependency gate, hold. Partial: construction passed and
the dependency gate was blocked. Split one question into a passing and a blocked
half.

**`spikes/s3-safety-rail-limits.md`** — Asked where the safety rails stop. Partial:
local file and data rails passed; the browser and network corpus was blocked.
Established the rail boundary that later rounds measured against.

**`spikes/s4-oss-substitution-check.md`** — Asked whether a reproducible open-source
substitution is available. Blocked: a bounded inventory was recorded, executable
conformance was not available. Recorded the inventory as the outcome rather than
claiming a substitution.

**`spikes/s5-cross-pack-provider-vertical.md`** — Asked whether the cross-pack
provider vertical composes. Partial: the pack and grant vertical passed; the
same-browser row was blocked by S1. Made the S1 dependency explicit.

**`spikes/s6-browser-session-taxonomy.md`** — Asked whether a credentialed-skill
browser-session taxonomy is feasible. Passed for prototype feasibility, with the
production convention explicitly unchanged. Established feasibility without moving
the convention.

### Round notes

**`spikes/2026-08-16-experimental-rerun.md`** — Asked whether the second run's
received handoff package reconciles against the RFC's evidence contract. Preserved
the received package unchanged for audit and reconciled it. Became authoritative
over the handoff's headline verdicts.

**`spikes/2026-08-16-experimental-round3.md`** — Asked whether the round-2 verdicts
survive re-measurement. Re-measured, and recorded a scope caveat that applies to
every proxy-based verdict in it. Retained the browser automation choice
provisionally; a decision was explicitly not reopened, and one spike stayed blocked.
Authoritative over round two where they disagree.

**`spikes/2026-08-16-experimental-round4.md`** — Asked whether the round-3 verdicts
hold. Re-measured and closed blocker items on measurement. Authoritative over round
three where they disagree.

**`spikes/2026-08-16-experimental-round5.md`** — Covers rounds five and six. Asked
whether the round-4 verdicts hold, then ran a correction pass. Carries its own
corrections table. Authoritative over round four where they disagree; round six's
own headline was later reversed, which is recorded below.

**`spikes/2026-08-17-experimental-round7.md`** — Covers rounds seven, eight and
nine. Asked whether the rounds-5-and-6 verdicts hold, then turned the instruments
themselves into the subject: round nine measured a different subject from every
round before it, examining the apparatus rather than the architecture. Carries the
largest corrections table in the tree. Authoritative over rounds five and six where
they disagree.

**`spikes/2026-08-17-experimental-round10.md`** — Asked four named bounded
questions. All four completed, with two arms reported as sandbox-invariant and the
invariance stated per driver rather than as one blanket claim. Wrote up what was
outstanding as outstanding rather than deferring the write-up.

**`spikes/2026-08-18-experimental-round11.md`** — Asked whether five binding
requirements hold. All five arms completed, and **two contradicted the requirement
they were written to confirm** — reported as the round's principal result rather
than smoothed over. One remedy was shown safe against a profile seeded by
authenticating; one class was closed by partitioning the job root.

**`spikes/2026-08-19-experimental-round12.md`** — Asked the consumer-shaped residual
questions. Complete measurements, and **no RFC decision or disposition changed**.
Established that registration blocking is destination-scopable only by partitioning
destinations into separate contexts, with shared-session scoping not demonstrated;
and that a page-resident init script receives the token while the driver does not,
with the shim's removal leaving the same page without it.

**`spikes/2026-08-18-front-door-worker-landscape-probe.md`** — Asked what the
front-door service-worker landscape looks like. **Exploratory: not a promoted arm,
not a manifest member, and not part of any round's evidence.** Recorded because it
materially narrows a residual round eleven left open, and so that a reader who finds
that residual also finds this. Its status as non-evidence is the entry.

### Evidence archives

Each archive note preserves the manifested, redacted evidence for its runs, so a
reviewer can reconstruct rather than trust.

**`spikes/experimental-fixture-source-archive.md`** — Preserves the bounded,
synthetic source inputs the fixtures consume. Makes the inputs auditable
independently of the runs.

**`spikes/experimental-rerun-evidence-archive.md`** — Asked whether the second run's
received handoff could be audited rather than taken on trust. Preserved the received
package as a manifested, redacted set, unchanged. Changed what the handoff's headline
verdicts rest on: a reviewer can reconstruct the inputs instead of accepting a summary
of them.

**`spikes/round3-evidence-archive.md`** — Asked whether round three's re-measurement
could be reproduced independently. Preserved its manifested, redacted artifacts and the
manifest that binds them. Changed the standing of the round's verdicts from asserted to
reconstructable, which is the property every later round's archive inherits.

**`spikes/round4-evidence-archive.md`** — Asked the same reproducibility question for
round four, the round that closed blocker items on measurement. Preserved its manifested,
redacted artifacts. Changed what those closures rest on: the closure claims can be
re-derived from the archive rather than read out of the note.

**`spikes/round5-evidence-archive.md`** — Asked the reproducibility question across
rounds five and six together, one of which was a correction pass over the other.
Preserved both rounds' manifested, redacted artifacts in one set. Changed how the
correction is auditable: the corrected and correcting artifacts sit side by side, so a
reader can see what moved rather than trusting that something did.

**`spikes/round7-evidence-archive.md`** — Preserves the manifested evidence for
rounds seven, eight and nine, and carries the archive digest the RFC's amendment
entry cites. This is the archive the later rounds' apparatus continues to build.

**`spikes/2026-08-21-destination-token-landing.md`** — Asked where a real
destination's issued token actually lands, and whether the response that issues it is
marked `no-store`. Measured against two pinned containers of deliberately opposite
render and authentication shape, each driven through a real browser login: on the half
that issues a token, that response carries no cache directive at all, and the
destination's own frontend writes the token into a page-readable web-storage key from
which it reaches browser user-data on disk. The contrast half issues no token and its
cookie arrives on a `private`-marked response, so it neither supports the precondition
nor refutes it. Changed open question 5 from an accommodation with an untested
precondition into one whose precondition no consumer can establish, and supplied the
measured fixture pair that the amended open-question-3 bar names.

---

## Set two — the rounds roster

Declared explicitly, because filenames cannot express it.

| Round | Where its evidence lives |
| --- | --- |
| First | The six S-spike notes; no dated round note of its own |
| Second | The rerun note and the rerun evidence archive |
| Third | The round-3 note and archive |
| Fourth | The round-4 note and archive |
| Fifth | The rounds-5-and-6 note and archive |
| Sixth | The same document as the fifth; no note of its own |
| Seventh | The rounds-7-8-9 note and archive |
| Eighth | The same document as the seventh; no note of its own |
| Ninth | The same document as the seventh; no note of its own |
| Tenth | The round-10 note |
| Eleventh | The round-11 note |
| Twelfth | The round-12 note |
| Thirteenth | This digest, and the round-13 amendment entry |

Round fourteen is deliberately absent from this roster. The roster is a projection of the coverage checker's declared tuple, which stops at the thirteenth and which round fourteen did not extend; set one carries the round through its own dated note. Having a dated note is not itself the reason — the tenth through thirteenth each have one and a roster row both.

---

## Withdrawals, reversals and narrowings

Recorded qualitatively. **No figure is restated here**: a digest that repeated a
number the current artifacts no longer support would fail the very verifier that
registering this document subjects it to, which would turn an honesty requirement
into a gate failure.

- **Round seven's "first round in four to close on measurement rather than correct
  its predecessor" was withdrawn.** The audit trail records earlier rounds closing
  blockers on measurement, and round seven did correct its predecessor — it reversed
  round six's profile-minimum claim. What holds is a narrower statement.
- **Round seven's wider "shipping configuration" claim was withdrawn by round
  eight.** Only a minority of drivers were parameterised for the sandboxed comparison —
  the lifecycle corpus and several rail drivers were not re-run sandboxed at all. What
  is established is narrower than the original wording. The count is deliberately not
  restated here; it lives in the round-seven note's own corrections table.
- **A trust conclusion was reversed.** Trust is establishable without a store, but
  the mechanism suppresses errors rather than validating, the driver anchor is
  issuer-wide, the composition with method enforcement is unmeasured, and there is
  no Linux arm. The reversal is a narrowing, not a replacement.
- **Round nine opened and closed no blocker item.** It withdrew the basis on which
  one item's closure had been stated — a destination check had compared a log
  against the policy that produced it, and a visibility field was a literal — then
  re-measured both properly. Its subject was the round's *claims*, not its closures.
- **A selective-purge measurement was withdrawn by its author pending
  re-measurement**, because its figures did not come from a post-purge filesystem
  read. Round twelve re-measured the property properly, and round thirteen
  inventories its consequence.
- **A raw-egress containment wording was withdrawn.** Containment for a capable
  adapter host requires an OS-level boundary that the language runtime's permission
  model does not supply, and which must never be described as a malicious-code
  sandbox. An environment allowlist is likewise not an exhaustive description of a
  child process's inputs.

## The two loopback bounds, each at its own code's width

There are two listeners, and the recorded claim is only wrong about one. They are
stated separately so that no phrase-level correction spans both.

**The synthetic issuer's HTTP listener.** Its bound is *already* recorded as "any
local process able to connect", in both the round-12 note and the round-12 spec, so
nothing is rewritten for it. This digest inherits that wording and adds the widening
the code supports: the unauthenticated scan route is a live **oracle**, answering
for caller-chosen bytes, and the page route serves the run decoy.

The bound is completed by stating what the exposure *is not*. The issuer's token is
a synthetic per-run value with no meaning outside the run, so the exposure carries no
confidentiality consequence. What it bounds is **measurement validity** — whether
another local process could have influenced the observation — and not secrecy. This
round therefore abandons, explicitly, any reading in which that fixture models a real
credential boundary. It models the architecture only, and the abandonment is recorded
here rather than left implicit.

**The browser's unconfined bind endpoint.** This is the subject of the register slug
and of the RFC's same-uid corrections, and its recorded bound is narrower than the
exposure: that endpoint is also loopback TCP with no client authentication, and the
platform grants no uid restriction on loopback TCP.

**Its narrow phrasing is nevertheless preserved verbatim, and deliberately so.** That
phrasing sits inside an accepted disposition's scope, and widening an accepted actor
set would retroactively treat a wider exposure as already accepted — a ruling this
round may not make. The wider factual bound is therefore recorded here as **new
evidence requiring re-ruling**, and the historical text is left exactly as it stands.

No bearer credential is added to either listener. The init script is built by the
driver, so any such credential would make the driver hold a token-equivalent
capability, contradicting the recorded property that the driver never holds the
token — and request headers are captured into the trace and archive files that the
same arm then reads back and scans.

## Round thirteen's own additions

Round thirteen is a disposition round: most open slugs were closable by correcting
the apparatus rather than by measuring the subject, and the residue needing new
measurement was bounded to one arm.

- **The evidence tree was relocated** to a durable per-user location, with
  equivalence proven per member in both directions, and path independence proven by
  observing the pre-correction form refuse under a simulated sweep before the old
  tree was removed.
- **Every selector was made to name the set its claim is about**, in the direction
  that fails closed: the figure verifier's live globs became closed member lists,
  while the privacy sweep kept greedy discovery and gained a positive-membership
  assertion instead.
- **The two privacy-term readers became one**, with named refusal reasons proved per
  consumer, and a collision refusal replacing an arbitrary minimum term length.
- **The sweep was pointed at the stronger of the two detectors** in the tree, so this
  digest — the round's largest leak surface — is checked by the richer identifier set
  rather than the poorer one.
- **The measurement scan endpoint was bounded** without removing scan coverage or
  breaking the truncation control.
- **Mutation coverage was closed by class rather than by instance**, including a
  meta-check that asserts every implemented self-test is actually invoked.
- **The worker-purge blast radius was inventoried** over a synthetic tree, with
  bounds stated at the width the removal helper's code supports.

## Disposition block

Every open register slug ends in exactly one of four declared states. This block is
the **single home** for that partition: a control reads it from here and checks it
against a committed pre-round snapshot, because closing a slug removes it from the
register and the set would otherwise be unre-derivable the moment the round succeeds.

`closed` — work complete, the slug leaves the register. `closed_retained` — work
complete, but membership is retained because a frozen predecessor spec pins the slug
with a deferral marker that resolves against the open register only; the entry's own
summary asserts satisfaction and retention, on the precedent the repository already
settled for this deadlock. `converted` — not a measurable residual; it leaves the
register as a named implementation concern owned by a follow-on artifact.
`carried` — still open, with its unblock condition recorded on the register entry.

```json disposition
{
  "carried": [
    "rfc0088-destination-group-split-cost",
    "rfc0088-native-addon-confinement-bypass",
    "rfc0088-privacy-term-identity-anchor",
    "rfc0088-same-uid-attach-exposure",
    "rfc0088-signing-identity-update-survival"
  ],
  "closed": [
    "rfc0088-evidence-tree-durability",
    "rfc0088-privacy-term-reader-deduplication",
    "rfc0088-token-scan-body-bound",
    "rfc0088-verifier-members-selector",
    "rfc0088-worker-purge-blast-radius"
  ],
  "closed_retained": [
    "rfc0088-round12-mutation-coverage",
    "rfc0088-staged-member-decoy-search"
  ],
  "converted": [
    "rfc0088-confined-removal-toctou"
  ]
}
```

**Two closures are `closed_retained`, and that is a fourth declared state rather than
a hedge.** The round-12 spec carries live deferral markers naming both slugs, and that
spec is frozen: the marker resolves against the open register only, the closed
register admits defects alone, the frozen-document rule forbids editing the marker
out, and widening the lint invariant would be a published-interface change needing its
own RFC. All four escapes are closed, so retention is the settled form. The state is
admitted only for a slug that is *all three of* still present, named by a deferral
marker in a frozen spec, and carrying a register annotation asserting satisfaction —
presence alone would admit every undispositioned slug, and a marker alone says nothing
about whether the work happened.

**Two slugs live in the shaping queue, not this register, and are listed separately**
rather than filtered by a field the register entries do not carry:
`rfc0088-token-replay-consumer-contract` and `rfc0088-destination-scoped-policy-axis`.
They are shaping follow-ups, not evidence residuals.

## Verdict

**Not final.** Round thirteen was commissioned as the final evidence round, and it
does not reach that bar. It says so here rather than at the end of a reader's
patience.

What remains is a materially shorter tail than the round started with: most open
slugs end in a closing disposition, one becomes a named implementation concern
against the follow-on artifact that will own it, and a residue is **carried** —
two because their own unblock conditions are unmet, two because no single round can
measure them, and one because measuring it needs a toolchain that would be a new
dependency.

The per-slug partition, in its four declared states, is recorded in the disposition
block below and checked mechanically against a committed pre-round snapshot. The
approver's decision surface is the round-13 amendment entry in the RFC, not this
document.
