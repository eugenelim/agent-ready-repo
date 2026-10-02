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

**This section states the position when the amendment fired. Two of its claims
were later superseded by the supplementary rulings below; read it with those.**

No acceptance criterion is removed, weakened, or renumbered, and the outcome is
not narrowed. AC-0012 keeps its wording; only the Testing Strategy sentence
naming where it is asserted changes. The slice stays additive: nothing reads the
field and nothing is gated on it.

Superseded, in order:

- *"No acceptance criterion is removed"* — the first supplementary ruling
  removed the two prose clauses the post-amendment repair itself had added to
  AC-0010. No criterion predating the amendment was touched.
- *"AC-0012 keeps its wording"* — no longer true. AC-0012 was later **tightened**
  under that same ruling: it now pins two lines and requires each to occur
  exactly once in the selected fence, which is what makes it falsifiable by a
  single-line mutation. Strengthening a criterion is not what the paragraph
  above forbids, but the sentence as written is stale and a reader stopping here
  would take a false statement about the current spec.

The additive claim and the no-narrowing claim both still hold.

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

## Supplementary owner ruling — 2026-10-01, a scoped intended-red waiver for T5

The fourth pre-EXECUTE pass sustained a blocker against the plan for citing this
note as authority for departing from `tdd-stubs.md` § *Validate*'s intended-red
requirement. The citation was wrong: nothing above granted that. Adjudication of
that pass returned `ADJUDICATION-INDETERMINATE` on the question behind it —
whether a mutation red obtained at PLAN time satisfies § *Validate*'s
non-vacuity requirement, or whether only an unmutated red does — and recorded
that neither `tdd-stubs.md` nor `mutation-proof.md` decides it. That is an owner
question, so it stopped there.

**The owner ruled on 2026-10-01: record an explicit waiver rather than reinterpret
the requirement.** The reasoning preferred naming the departure over redefining
"intended red" to admit evidence already in hand, which would have set a
precedent for every future stub whose asserted property is already present.

### What is waived

§ *Validate*'s requirement of a recorded **intended red** against the unmutated
tree, for **T5's two stub blocks only**. Nothing else in § *Validate* is waived:
the syntax/compile pass is recorded as that section requires, and the two legal
dispositions remain the only ones this plan uses.

### Why the red cannot exist

Both T5 assertions check material T1 already shipped and committed
(`f69606cfb`): the template carries the pinned absent-field phrase, and the
guide's `type: creative-direction` fence carries both pinned lines. An
assertion over an already-satisfied property is green on first run. Obtaining a
red would mean removing shipped content, which is not a draft-stub state but a
regression.

### The substitute evidence, measured 2026-10-01

Both prescribed mutations were applied in throwaway git worktrees cut from
`HEAD`, with the real tree left untouched and no `git checkout`, `reset` or
`stash` used. Observed:

| Assertion | Unmutated | Under its prescribed mutation |
| --- | --- | --- |
| AC-0012, roster module | green | **red** on the `KEY_LINE` exactly-once assertion |
| AC-0011, replaced assertion in the contract suite | green | **red** on the pinned-phrase assertion |

The AC-0011 mutation also establishes the stronger claim, which is the whole
reason that assertion was replaced: with the comment still carrying both
`absent` and `unconfirmed` but no longer as the pinned contiguous run, the
**superseded** co-occurrence assertion still passes while the **replacement**
fails. The replacement therefore catches a defect the old form could not.

The AC-0011 block is a function-body fragment and does not compile standalone;
its syntax was validated by splicing it into a disposable copy of its host
module, which then compiled clean. The plan's § *Stub validation record* states
it that way rather than claiming a bare `py_compile` pass.

### Scope limit

This waiver covers T5's two blocks in this spec. It is not a general licence,
does not reach any other task or spec, and does not decide the open question of
whether a PLAN-time mutation red satisfies § *Validate* in general — that
question remains undecided, and a future task needing the same relief needs its
own ruling. The EXECUTE-time ledger entry T5's `Done when` gates on is still
owed; this waiver concerns plan approval only.

## Supplementary owner ruling — 2026-10-01, the waiver extends to the Lifecycle red

The waiver above closed with "this waiver concerns plan approval only". The
fifth pre-EXECUTE pass sustained a concern against that limit: the plan's
substitution claim reached EXECUTE, where `tdd-stubs.md` § *Lifecycle*
separately requires "materialize the approved block unchanged at the real test
path, verify byte identity, **and prove the intended red**" — a requirement
`work-loop/SKILL.md` repeats for the full-mode engine after
`CODE-IMPLEMENTATION`. The overreach was removed from the plan under the
adjudicated ruling that removing an overreach needs no grant, leaving the
underlying question open.

**The owner ruled on 2026-10-01: extend the waiver to cover § *Lifecycle*'s
EXECUTE-time intended red, for the same two T5 blocks, on the same reason.**

### Why the same reason holds one phase later

The EXECUTE-time red is unobtainable for exactly the cause that makes the
plan-approval one unobtainable: both assertions check material T1 already
committed at `f69606cfb`. Obtaining a literal red at EXECUTE would mean
deleting shipped template or guide content, which is a regression rather than a
draft-stub state. Nothing about reaching `CODE-IMPLEMENTATION` changes that.

### The substitute, and why it discharges the obligation

T5's `Done when` requires both prescribed mutation proofs, performed in-tree and
recorded in the verification ledger with the complete field set
`mutation-proof.md` § *Proof record* requires. Adjudication of the fifth pass
established that this supplies the EXECUTE-time non-vacuity evidence **in
substance**: a mutation shows the assertion detects removal of the property it
names, which is the same function the intended red performs. What that
adjudication found missing was only the authority to substitute it. This ruling
supplies that authority and nothing else.

### Scope limit

Unchanged in kind from the waiver it extends. It covers T5's two blocks in this
spec, at plan approval and at EXECUTE. It is not a general licence, reaches no
other task or spec, and does not decide whether a mutation proof satisfies
§ *Validate* or § *Lifecycle* in general — that question stays open, and a
future task needing the same relief needs its own ruling. The ledger entries
remain owed: this ruling permits the substitution, it does not perform it, and
T5 is not met until both proofs are recorded.
