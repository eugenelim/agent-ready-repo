# Contract amendment record — 2026-10-01

This note is the durable authority and reason reference for the
`contract-amendment` transition on run `1adcfbc1-0d36-401b-9f3d-ebfc2493790a`.
It exists because the session-local review artifacts under `.context/reviews/`
are gitignored and cannot serve as a stable reference.

## Owner authority

The scope owner authorized a controlled contract amendment on 2026-10-01, in
session, after being shown the conflict recorded below and the three options
available (amend; fix the code and waive the resulting contract drift; or pause
to inspect the artifacts first). The owner selected the amendment.

## Reason: the accepted Testing Strategy specifies something a repository rule forbids

The spec's `Testing Strategy` is contract — the spec states that `Agent Rules`,
`Testing Strategy` and `Acceptance Criteria` are what a completion gate reads.
It requires AC-0012 to be "a contract-suite assertion scoped to the guide's
fenced excerpt block", which places the assertion in
`packs/experience-design/tests/skills/creative-direction/test_contract.py`.

AC-0012 is a claim about
`guides/experience-design/how-to/establish-design-intent.md`, so deciding it
requires reading a file outside `packs/experience-design/`.
`tools/lint-pack-test-boundary.py` forbids a pack test from reading above its
own pack, and `.github/workflows/docs.yml` runs that lint on `pull_request`
under path filters this change triggers.

The two requirements cannot both be satisfied. Measured on 2026-10-01:
`python3 tools/test-lint-pack-test-boundary.py` exits 1 with
`packs/experience-design/tests/skills/creative-direction/test_contract.py:353:
pack test reaches above packs/experience-design`. No placement resolves it while
the assertion stays in the contract suite, so the defect is in the accepted
Testing Strategy rather than in the implementation that followed it.

`tests/AGENTS.md` names `tests/roster/` as the repository-level home for exactly
this shape, anchored at `Path(__file__).resolve().parents[2]`.

## Sustained findings this amendment answers

Round 1, post-gates. Two reviewers, both adjudicated; 6 of 20 raw findings
sustained. Full artifacts and digests:

| Artifact | SHA-256 |
| --- | --- |
| `1-post-gates-adversarial-reviewer-raw.md` | `1dd9b2cc8e9c2e4911ecf623609df88437f4ae220ba874556e265ea974c881c7` |
| `1-post-gates-adversarial-reviewer-adjudication.md` | `f15c2257fb2f36817942dbcdc3bb239d9601642ca56184be2176acd1268b165f` |
| `1-post-gates-experience-reviewer-raw.md` | `a4eb0c7bbc9111c7048bb739bb70ca538d4ae7fabe997fdda0280fce7e1be9d6` |
| `1-post-gates-experience-reviewer-adjudication.md` | `7a446cfa0ccee1599df55517de235c8cdeada9b0f303e079a110186ddb993ed4` |

Sustained, by the surface each one changes:

1. **Blocker** — AC-0012's assertion escapes the pack test boundary and reds the
   PR gate. Requires the Testing Strategy amendment above, and relocation to
   `tests/roster/` with the two roster obligations `tests/AGENTS.md` names.
2. **Blocker** — the release roster test requires a changelog entry for whatever
   version `pack.toml` currently carries, so the next unrelated
   `experience-design` bump reds a permanently installed test. Only the
   changelog half pins to the literal release; the three-site agreement must
   keep reading the live version, as
   `tests/roster/test_wave4_durable_outputs_and_release.py` already does.
3. **Concern** — the AC-0011 assertion cannot fail on a comment stating the
   wrong reading: `unconfirmed` is already guaranteed present by the closed-set
   enumeration, so the check reduces to the word "absent" appearing anywhere.
4. **Blocker** — the `4.1.2` changelog Highlights bullet states that `converge`
   records the disposition "when writing compositional commitments". The shipped
   instruction records it unconditionally, so the published sentence describes a
   condition the artifact does not have and reads as the gating this slice
   forbids.
5. **Concern** — that same bullet is schema-led where `changelog.md`'s own header
   requires outcome-led user register.
6. **Advisory** — the guide caption states unconditional placeholder replacement
   above a conditional confirmation record. Deferred, not acted on.

## What this amendment does not change

No acceptance criterion is removed, weakened, or renumbered, and the outcome is
not narrowed. AC-0012 keeps its wording; only the Testing Strategy sentence
naming where it is asserted changes. The slice stays additive: nothing reads the
field and nothing is gated on it.

## Completed-task evidence bindings

`current_wave_index` was 3 when the amendment fired, so T1, T2 and T3 are
completed and their plan sections are immutable. Corrections to T1's assertions
therefore arrive as a new dependency-ordered task rather than edits.

| Task | Stable evidence reference |
| --- | --- |
| T1 | commit `f69606cfb` |
| T2 | commit `2e0348b39` |
| T3 | commit `15188c387` |

T4's release work is committed as `774f9e5ae`; it was the current wave rather
than a completed one, so its plan section remains amendable.

## Supplementary owner ruling — 2026-10-01, narrowing two added clauses

The § *What this amendment does not change* statement above was written before
the amendment had been reviewed. It said no acceptance criterion is removed or
weakened, and at that point none was.

The amendment's own pre-EXECUTE review then sustained findings across two
rounds, and the repair answered several of them by **adding** obligations: a
byte-identity completion check, a recorded manual register check, and two
prescribed mutations. The third round's findings were largely defects in those
additions. Adjudication of that round recorded explicitly that the
`Cut before adding` answer — narrowing or dropping the added clauses rather
than specifying them further — was unavailable to the repair, because the
statement above forbade it, and that taking it needed a fresh owner ruling.

**The owner gave that ruling on 2026-10-01:** repair the shipped changelog
bullet as a one-time correction, and drop the standing criteria the repair had
added to AC-0010. The register and conditional-framing clauses added to AC-0010
are removed. The sustained round-1 copy findings are answered by fixing the
bullet, not by carrying a criterion a completion gate cannot decide.

Scope of this ruling, stated narrowly so it is not read as a general licence:

- It removes only the two prose clauses the post-amendment repair itself added
  to AC-0010. No criterion that existed when the amendment fired is removed,
  weakened, or renumbered, and the outcome is not narrowed.
- AC-0010's released-version clause stays. That clause answers a separate
  sustained finding and is decided by the stub.
- The bullet's two defects remain required repairs. Adjudication distinguished
  them from the dropped criteria: a one-time repair condition on an
  already-shipped artifact adds no standing criterion, so T4's completion
  condition must still fail while either defect stands.
- AC-0012's assertion is tightened rather than relaxed, so that a single-line
  mutation can falsify it. Strengthening a criterion is not what the statement
  above forbids.

## Recorded process deviation — round 3's revision order

Rounds 1 and 2 of the pre-EXECUTE review followed the documented sequence: fire
`findings-remain` from `SPEC-PLAN-REVIEW` to `SPEC-PLAN-DRAFTING`, revise, then
fire `spec-ready` back to `SPEC-PLAN-REVIEW`.

Round 3's revision was made while the run was still in `SPEC-PLAN-REVIEW`, and
the transition pair was not fired. The run therefore shows two
`findings-remain`/`spec-ready` pairs for three revision rounds.

Nothing is miscounted by it: a pre-EXECUTE result does not call
`review record`, so `review_round_count` and `review_retry_count` were never
the counters tracking these rounds, and the end state —
`SPEC-PLAN-REVIEW` with revised artifacts — is the state the next reviewer pass
requires. The deviation is recorded rather than corrected because firing the
pair afterwards would assert a sequence that did not occur, and the artifacts
were already revised by then.

The round itself is fully evidenced: the raw report, the adjudication, and
their digests are in the session review directory, and the plan's Changelog
carries what changed and why.
