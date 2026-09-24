# Migration record — the corpus onto the two lifecycle records

Durable output of T3, required by `spec.md` § Durable Outputs (Decision
rationale). One entry per artifact that owed a status judgement, naming the
branch taken and the review or waiver it rests on.

## What the run derived

Both counts come from the pre-rule derivation T3's `Tests:` names, run against
`docs/product/intents/` before the T1 and T2 rules existed. The corpus lint
could not supply them: its refusals are T1's and T2's, so on the unmigrated
corpus it reported `clean — 150 entries` and exited 0.

| Run | Artifacts read | Refused | Of those, never `Accepted` | Exit |
| --- | ---: | ---: | ---: | ---: |
| Before the migration, on `6e89061c3` | 150 | 14 | 10 | 1 |
| After the migration | 150 | 0 | 0 | 0 |

The 14 are the set owing a record. The 10 are the subset owing a status
judgement, and they are what this record accounts for. The remaining 4 had
reached `Accepted` in their own history and owed only the record, so they carry
no entry below.

One artifact's history is not fully machine-readable, and the derivation reports
it rather than absorbing it: `rendered-page-visual-inspection` has 3 of 5
revisions predating the `Status:` field. Those three were read by hand and carry
no `Status:` line at all, so "never `Accepted`" is the correct verdict for it
rather than a parser artifact. Every revision of the other 13 parses.

## The owner decision this rests on

`FEAT-0005` § Legal transitions prices `Draft` → `Accepted` at an independent
intent-mode shaping review returning zero `MALFORMED` tokens, plus human
confirmation. **The owner waived the review half on 2026-09-24**, for this
one-off migration only, and confirmed each artifact directly.

`spec.md` § Durable Outputs admits this: the closeout condition for this file is
that each entry names "the branch taken and the review **or waiver** it rests
on". A waiver is therefore evidence the contract already contemplates, not an
exception invented here. `## Agent Rules` → *Ask first* requires the owner's
judgement before any `Status` change during the migration, and that is what was
taken.

**No `Accepted:` value on any waiver-backed artifact describes a review.** Each
says it rests on an owner waiver and points here. The defect `FEAT-0005` was
opened on was fourteen intents carrying a terminal status with nothing recording
who decided or on what evidence; writing a plausible review into those fields
would have reproduced it with better syntax.

## The two branches, and why reclassification was not available to seven

`FEAT-0005` § Intent states defines `Withdrawn` as *stopped before any
execution* and `Cancelled` as *stopped after execution evidence exists*. Both
assert the work **stopped**. Seven of the ten did not stop — they delivered, and
the delivery is verifiable in the repository today. For those, reclassification
would have been a false statement about what happened, so walking back through
`Accepted` was the only honest branch and the waiver is what paid for it.

Three of the ten did stop, and those took `Withdrawn` on their own evidence
rather than on the waiver. They need no `Accepted:` record at all: AC-0003
exempts `Withdrawn`, because abandoning an unratified bet needs no ratification.

## Entries — the three that stopped

### `core-seed-placeholder-shapes` — `Fulfilled` → `Withdrawn`

**Branch:** reclassified. **Rests on:** the artifact's own recorded disposition,
not the waiver.

Its `## Disposition — refuted 2026-08-29, no change made` records that the
premise was false and nothing was changed: the three placeholder shapes it asked
for were already declared, and the phantom came from a stale wheel on `PATH`.
No execution evidence exists because no execution happened.

### `reviewer-agent-vacuous-assertion-coverage` — `Fulfilled` → `Withdrawn`

**Branch:** reclassified. **Rests on:** the artifact's own recorded amendment,
not the waiver.

Its `## Amendment` records "Dropped 2026-09-01, before implementation", with the
reason: `docs/CONVENTIONS.md` gives `quality-engineer` exclusive ownership of
test strength, so routing the lens to `security-reviewer` would have put a
second owner on an exclusive one. The substance landed in the agent that owns
the lens. Stopped before execution, so `Withdrawn`.

### `new-spec-review-phrase-contract` — `Fulfilled` → `Withdrawn`

**Branch:** reclassified. **Rests on:** evidence gathered during this migration,
recorded in a new `## Disposition` section on the artifact.

It owed two things and delivered neither as written. The phrase half was
superseded rather than delivered: `9b9d470ef` replaced the contract, and
`test_spec_review_accepts_only_exact_clean_before_adjudication` now pins current
prose, says so in its own comment, and passes. The remote-gate half was never
started and is still open — no workflow under `.github/workflows/` runs
`packs/core/tests/skills/new-spec/`. No execution evidence exists for this
intent, so `Withdrawn` rather than `Cancelled`.

**Left behind deliberately:** the CI-coverage gap is real and outlives this
intent. It is not re-homed here, because this migration's scope is status and
records, and inventing a follow-on to carry it would be scope this contract does
not admit.

## Entries — the seven that delivered

All seven keep `Status: Fulfilled`, gain both records, and rest on the owner
waiver for `Accepted:` and on an independent verification for `Fulfilled:`. Each
`Fulfilled:` value was checked against the repository rather than against the
artifact's own account of its delivery.

| Artifact | `Accepted:` rests on | `Fulfilled:` verified against |
| --- | --- | --- |
| `STRAT-0002-platform-core` | owner waiver | already carried a 2026-09-19 independent verification; unchanged |
| `contract-amendment-pre-wave-window` | owner waiver | `loop-cohort.py:933` — `missing_evidence` is a set difference, vacuous at wave 0 |
| `credbroker-socket-budget-float-tolerance` | owner waiver | `test_sso_derivation.py:371` — `seen[-1] <= 1.0 + 1e-9` |
| `distribution-route-registry` | owner waiver | `_data/distribution-routes.toml` + schema, read via `build/route_lookup.py` |
| `frozen-record-errata-mechanism` | owner waiver | `lint-adr-shape.py` rule `ADR-S015` enforces the `## Errata` heading |
| `portable-agent-plugin-projection` | owner waiver | `_data/agent-plugin-extension-namespaces.toml` + schema |
| `rendered-page-visual-inspection` | owner waiver | spec `Shipped`; its criterion superseded by AC-0007 of `rendered-page-channel-axis` |

### `STRAT-0002-platform-core` — the one whose closure already had evidence

Worth naming separately, because it is the only artifact in the corpus whose
closure carried evidence before this migration ran. Its `### Fulfilment
evidence` table records an independent per-action verdict returning
`VERDICT: ACHIEVED`, and `## Decomposition` states the partition is closed with
no child intents expected, with the reason.

So the waiver buys less here than elsewhere. What `Draft` → `Accepted` exists to
establish — that the decomposition partitions the outcome with no gap — is
already stated on the artifact and was already checked. The gate could not have
been passed in any case: this strategy was delivered before the recursive intent
tree existed, so the gate post-dates the work it would have judged.

It keeps `Fulfilled` and gains only `Accepted:`; its existing `Fulfilled:` record
was left byte-for-byte unchanged.

## What this migration did not do

- **It did not add the presence rules.** Those are T1's and T2's. The corpus now
  conforms to rules that do not yet exist, which is the point: they land green.
- **It did not touch `Superseded`.** No intent carries it, and every supersession
  rule is deferred by `spec.md`'s *Not changed here* paragraph.
- **It did not create follow-ons** for the concerns it surfaced. The `new-spec`
  CI-coverage gap is named above and left with its finder.
