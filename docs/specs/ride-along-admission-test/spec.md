# Spec: Ride-along admission test

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0090 (bundled-fixes tiers; corrected by this spec's
  erratum), RFC-0055 (errata convention), ADR-0088 (risk triggers have a single
  documented home)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer running `work-loop` keeps the small, mechanically verifiable fixes
the loop notices outside its plan task, because the loop dispatches them before
it closes instead of dropping them. A noticed fix that is ready now either
lands in the session or becomes the session's next reviewed unit; only work
that is genuinely blocked is recorded, and it is recorded with the one fact
that makes it actionable.

## What Changes

- The bundled-fixes admission gate — three tiers become one three-clause test
  keyed to risk, behaviour, and stated verification, with a design call that
  is already settled no longer disqualifying — in
  `packs/core/.apm/skills/work-loop/SKILL.md` § EXECUTE.
- The same test, verbatim, at its three mirror sites —
  `packs/core/.apm/agents/implementer.md` (operating envelope),
  `packs/core/.apm/agents/adversarial-reviewer.md` (scope check #4), and
  `packs/core/.apm/skills/work-loop/references/supervisor-mode.md`, whose
  dispatch authorization line carried locality wording that contradicted the
  canonical site and now also declares attendance.
- A fifth row in the DECIDE intent-fit routing table, covering a non-matching
  discovery that is ride-along eligible — `SKILL.md` § Step 5. DECIDE.
- `## Capture learnings` becomes `## Capture` and routes a DECIDE scratch
  note five ways instead of two, in a stated order, and says what capture
  costs — `SKILL.md`. The section no longer routes only learnings, so the old
  heading under-named it; the two in-file links to it and the adopter-facing
  description of the step move with it.
- A question-and-answer field on the `Bundled fixes:` report entry, and a
  dedup rule that stops two entries with different questions being merged —
  `implementer.md`, `supervisor-mode.md`.
- A content control over the shared clauses —
  `packs/core/tests/pack/test_ride_along_admission_test.py`, new — and one
  repository-level check of the adopter guide,
  `tests/roster/test_capture_rename_guide.py`, new.
- A dated, Approver-signed erratum recording the tier replacement —
  `docs/rfc/0090-change-sizing-and-decomposition.md` § Errata.
- A patch version bump and its release note — `packs/core/pack.toml`,
  `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`.
- Two eval cases for the new behaviour, and one existing case's prompt
  updated to name the renamed section —
  `packs/core/.apm/skills/work-loop/evals/evals.json`.
- The adopter-facing description of the step —
  `guides/core/explanation/core-pack.md`.

## The shipped clauses

These seven paragraphs are the outcome this change delivers. None of them
names another by label: the labels below are this spec's handles, not shipped
text.

**Only C1 and C2 are contract.** They carry the admission test and the rule
deciding when a design call is resolved, so a reword of either changes what an
agent may do, and an acceptance criterion pins each by equality. C3 through C7
are working material: their wording is corrected in place as the work teaches,
and their protection is the content pin already in
`packs/core/tests/pack/test_ride_along_admission_test.py` rather than a
checkbox here. That split is deliberate and was made late. An earlier draft
pinned all seven as contract, and three review rounds found the same class of
defect each time — a control accepting more than its criterion states —
because most of those criteria could only be argued, never red. This
template's own guidance names that shape and predicts it will not converge.

**C1 — the admission test.** Carried at all four sites. Clause (ii) is the
sole home of the judgement bound, including the refusal, so an agent applying
the clauses as written cannot admit something the next paragraph refuses. C2
carries that refusal's rationale and never restates the rule. Clause (iv) is
the structural bound locality used to supply by accident: without it, a prose
edit to the files defining the carve-out fires no trigger, reads as no
behaviour change, and verifies by comparison — so an agent could widen its
own unplanned write authority.

> A change may ride along when all four hold: (i) it fires no risk trigger on
> its own, so it would run in light mode standalone; (ii) it involves no
> behavior change and no unresolved design call, and where a design call was
> resolved, that resolution changes no convention, contract, or published
> interface; (iii) you can state how it was verified — a command with a zero
> diff on re-run, a search with no remaining references, or a comparison
> against a named authority that the change agrees with; and (iv) it changes
> no file that defines what an agent may do — a skill, an agent definition, a
> hook, a command, or anything one of those loads — and no file stating this
> test. Clause (iv) fails closed: where you cannot tell whether a file is one
> of those, it is, and the change is not a ride-along.

**C2 — where the handling lives.** Carried at all four sites. Detection —
C1's four clauses — stays inline at every site because an agent needs it to
decide whether a candidate exists at all. What to *do* with a candidate does
not: it is read once a candidate exists, it differs by the kind of fix, and
duplicating it at four sites is what made every wording change a four-site
edit. It moves to one reference, and this clause is the pointer. Its trigger
is evaluating clause (ii), not finding a candidate: a reader who waited for a
candidate would need the reference to know whether they had one.

> Clause (ii) is not decidable from this text alone. Before you evaluate it,
> read `work-loop/references/bundled-fixes.md`: what counts as recognising a
> design call, what resolves one, how attendance is read, what to do when
> nothing resolves it, and what is refused whatever the answer.

**C3 — the triggers pointer.** Carried at the three mirror sites only.
`SKILL.md` links its own in-file anchor instead, which is why C3 is pinned
across three sites and C1 and C2 across four.

> The risk triggers are the canonical block in `work-loop/SKILL.md`
> (§ Select: light or full mode); a mirror names the skill and lists no
> trigger.

**C4 — the DECIDE scratch-note routing bullet.** Carried in `SKILL.md`
§ Capture only. Its shape is one additive rule followed by an
ordered sequence, and the order of those two parts is load-bearing. The seam
is additive and stated first, because a note can be both a lesson to keep and
a defect to dispose of, and a seam stated as a ranked alternative would be
unreachable for every note an earlier alternative already matched. The
sequence then disposes of the defect, first match winning, which is what
keeps a decision-blocked item out of a route it would otherwise also match.
The table separates the two ready-now destinations into their own rows, so no
row names more than one place a note can go; both are same-session routes and
both are dispatched at DECIDE, which the sequence states rather than
restating the dispatch rule. The sequence is gated on the note naming a
defect, so a lesson-only note leaves at the seam rather than falling into
discard, and the closing sentence routes a note that is neither defect nor
lesson. Every note therefore reaches a destination and no note reaches two,
except by the seam's additive rule.

> - **Review scratch notes** from this session's DECIDE passes.
>   Anything generalisable that would have changed the approach goes to
>   the `project-knowledge` public seam, and the examples below are
>   instances of that; the seam is additive. A note that names a defect
>   routes by what it is: | What the note is | Where it goes | | --- |
>   --- | | Generalisable practice | The existing `project-knowledge`
>   route, unchanged | | Specific, real, blocked | Captured as a
>   `work-item` | | Specific, real, ready now, ride-along eligible |
>   Dispatched in-session, not captured | | Specific, real, ready now,
>   not ride-along eligible | The session's next independently reviewed
>   unit | | Specific, failing the razor | Refused, non-silently | Take
>   the first row that applies and stop: a defect blocked on a decision,
>   an instrument, elapsed time, or a dependency is captured as a
>   `work-item`; a ready-now defect — one that can be finished this
>   session without a decision nobody present will make — was dispatched
>   at DECIDE, which owns both same-session routes and is the pass that
>   runs while they are still reachable, so neither of its two rows is
>   captured here; and a defect the razor refuses — one an existing
>   artifact already covers, or one no capture criterion admits — is
>   refused, non-silently, rather than discarded. What a `work-item`
>   capture must carry, what the razor checks, and what a refusal tells
>   the author are in [Close-time work-item
>   branch](references/work-item-capture.md#what-a-work-item-capture-must-carry).
>   Before any `work-item` is written, one cold reasoning check runs per
>   declined item, over at most twelve per close; an unavailable,
>   timed-out, or unrecognized check refuses rather than admits — see
>   [The reasoning
>   check](references/work-item-capture.md#the-reasoning-check). A note
>   that names no defect is done once the seam has taken it, and
>   discarded if it had nothing for the seam either.

**C5 — the capture obligation and its economics.** Carried in `SKILL.md`
§ Capture only.

> A captured item carries its discriminator: the one fact the decision turns
> on, not just the location. "Four sites use a 13px literal" is a locator;
> "the third of them is the only sans one, so the shared token does not fit
> it" is an item. Supply the discriminator before capturing; an item you
> cannot give one to is not ready to capture, and it goes to the destination
> its actual state names. A locator nobody can action looks like tracked work
> and is not. Disposing an item now is cheaper than recording it: a recorded
> item pays a tracking cost, a context-refresh cost, and often a new session,
> and then still needs a discriminator that close-time reconstruction from the
> diff cannot recover. A slightly longer loop is the cheaper option, and
> capturing a ready-now item is a loss.

**C6 — the report entry's resolution field.** Carried in `implementer.md`'s
`Bundled fixes:` report template only.

> An entry that rests on an owner's answer states the question asked and the
> one-line answer given.

**C7 — the dedup exclusion.** Carried in `supervisor-mode.md`'s
`Bundled fixes:` lifting step only. It is an exception to an operator-judgment
fallback that would otherwise merge two entries resolving different questions.

> never merging two entries whose recorded questions differ, nor two whose
> recorded answers to the same question differ

### Host markers

Each clause sits inside the structure that instructs its reader. These are the
literal markers a check finds the host by.

| Site | Host marker | Carries |
| --- | --- | --- |
| `SKILL.md` § EXECUTE | `**Bundled-fixes carve-out.**` | C1, C2 |
| `implementer.md` | `- **One task:**` | C1, C2, C3 |
| `adversarial-reviewer.md` | `4. **Scope.**` | C1, C2, C3 |
| `supervisor-mode.md` | `"Bundled fixes authorized per the carve-out in` | C1, C2, C3 |
| `SKILL.md` § Capture | `## Capture` | C4, C5 |
| `implementer.md` report template | `**Bundled fixes:**` | C6 |
| `supervisor-mode.md` lifting step | `**Lift \`Bundled fixes:\` into the PR body.**` | C7 |

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Published agent behaviour | Applicable — four shipped surfaces change how an agent admits and disposes of a noticed fix | `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/agents/implementer.md`, `packs/core/.apm/agents/adversarial-reviewer.md`, `packs/core/.apm/skills/work-loop/references/supervisor-mode.md` | work-loop maintainer | AC1–AC12 hold; `packs/core/tests/pack/test_ride_along_admission_test.py` passes | Every clause sits in its host at every site it belongs to, and the projections match |
| Decision rationale | Applicable — replaces a decision an Accepted RFC made | `docs/rfc/0090-change-sizing-and-decomposition.md` § Errata | RFC Approver | AC13: dated entry, Approver-signed, body above unchanged | The erratum names what the tiers are replaced by and why |
| Release history | Applicable — published pack content changes | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md` | release owner | AC14 | Version and release note agree, and the declared version is above every `[core]` version the changelog already held |
| Reusable learning | Applicable — the pack ships an eval harness that must track non-cosmetic changes | `packs/core/.apm/skills/work-loop/evals/evals.json` | work-loop maintainer | AC15 | One case grades dispatch over discard; one grades the unattended fall-out |
| Adopter documentation | Applicable — the published guide describes this step by its old name and old job | `guides/core/explanation/core-pack.md` | work-loop maintainer | AC12 | The guide names the step as shipped and describes what it now routes |
| Interface compatibility | Not applicable | — | — | — | No contract surface, schema, or CLI signature changes |
| Operations | Not applicable | — | — | — | No runtime, deployment, or persisted state changes |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Change the four `.apm/` sources and regenerate the adapter projections with
  `agentbundle catalogue self-host --root . --write`.
- Paste C1 and C2 exactly as § The shipped clauses states them, and change
  this spec's text in the same edit, because AC3 compares against it. C3–C7
  are working material: keep them synchronised across their sites, which the
  suite pins, and correct their wording in place without an amendment.
- Place C1 and C2 inside their § Host markers structure, never inside an HTML
  comment or a fenced block. The suite holds C3–C7 to the same placement
  without a criterion doing so.
- Write every shipped clause site-independently: no "this file", no label like
  "C2", no phrase assuming the reader owns the artifact it names — that is
  what put a reviewer's own output contract in conflict with C2 once.
- Bump `packs/core` in both `pack.toml` and `.claude-plugin/plugin.json` to the
  same value.

### Ask first

- Any change to C1's clause (i) or (iii), or to C2's recognition sentence,
  citation list, or refusal. Clause (ii) and C2 together are the determinacy
  bound once the tiers go.
- Adding a fifth site that carries C1, or moving the canonical home away from
  `work-loop/SKILL.md`.
- Anything that would take `work-loop/SKILL.md`'s body above 1,000 lines. The
  `CAT-S003` gate owns the failure; this rule is what stops the agent walking
  into it.

### Never do

- Never add an engine state or transition. Both same-session routes in C4
  reuse the existing `blocker-applied` edge from `CODE-HUMAN-GATE`.
- Never edit `.claude/`, `.agents/`, or `.codex/` by hand; they are generated.
- Never add a new top-level directory, module boundary, or dependency. The
  controls use `pathlib` and `re` from the standard library and live in two
  existing trees: the pack-local checks beside the other core pack tests, and
  the one check that reads outside `packs/core/` in the repository roster,
  because a pack test may not climb out of its own pack.
- Never list a risk trigger anywhere but the canonical block; a mirror names
  the skill.
- Never add a rule of the form "the agent judges whether a decision is
  simple", at the recognition step or the resolution step. Admissibility turns
  on the decision having been made and being producible, never on how easy it
  looked.
- Never write a repository-only path into shipped pack content; name a file
  the way an adopter sees it.
- Never cite this repository's internal governance records — an RFC number, an
  ADR number, a spec path, or a PR number — inside `packs/` content.

## Testing Strategy

- **C1 and C2 identity, placement, uniqueness (AC1, AC2, AC4, AC5, AC6):
  TDD**, in `packs/core/tests/pack/test_ride_along_admission_test.py`.
- **Agreement with this spec (AC3): TDD**, in
  `tests/roster/test_capture_rename_guide.py` — not the pack suite, because
  `lint-pack-test-boundary` forbids a pack test reading `docs/`. AC3 is what
  stops the control proving only that the copies agree with one another.
- **Retired vocabulary absence (AC7, AC12): TDD.** Substring sweeps, compared
  case-insensitively over normalised text — a case-sensitive sweep over raw
  text already missed four live references once in this change.
- **Control adequacy (AC8): TDD.** A property of the test itself, checked by
  applying six named mutations and observing red. Re-runnable by anyone
  holding the spec, and re-run against the tree as shipped rather than
  against an earlier state of the controls.
- **Prose obligations (AC9, AC10, AC11): TDD**, in the same pack suite.
  Exact strings and resolvable anchors at named locations, each decided by an
  assertion rather than by a command — which is what makes the mode TDD and
  not goal-based, the label an earlier draft carried.
- **Governance and release (AC13, AC14): goal-based check.** A diff bounded
  at a heading and a version comparison against the changelog.
- **Eval register (AC15): goal-based check.** Read from `evals.json` with the
  standard library, in the same pass that reads it for anything else; the
  register is not executed here.
- **The handling reference (AC16): TDD**, in the pack suite — the path is
  inside `packs/core/`, so `lint-pack-test-boundary` permits it, and an
  assertion rather than a command is what decides a content property here,
  as it does for AC9–AC11.
- **Evidence (AC17): goal-based check.** The ledger is the artifact a later
  maintainer re-derives from, so a criterion whose mode is goal-based is met
  only when its command and output are recorded, not when it merely held.
- **The shipped behaviour (Outcome): visual / manual QA.** Three worked
  discoveries driven through the **installed** projection — one resolved by
  citation, one needing an owner answer where no brief declares attendance,
  one in a declared-unattended dispatch — exercising the wording that ships,
  not an earlier draft of it.

C3 through C7 have no criterion. They are working material pinned by the
suite; see § The shipped clauses for why that split was made.

Body-line headroom and projection freshness are not criteria here:
`CAT-S003` (`catalogue lint --root . --deep`, run by the `docs` workflow on
`packs/**`) and the self-host drift check (`build-check-windows.yml`) already
own them on every pack-content change.

## Acceptance Criteria

Seventeen criteria. Sixteen, down from twenty-eight, plus one for the
handling reference C2 now points at. The twelve removed pinned the
wording of C3 through C7 and the shape of the controls over them; each could
be argued but not red, and three review rounds spent themselves on that set
without converging. They are not lost: C3–C7 are still pinned by equality in
`packs/core/tests/pack/test_ride_along_admission_test.py`, which is where an
obligation whose only check is that a sentence exists belongs.

- [x] **AC1.** C1 appears in `packs/core/.apm/skills/work-loop/SKILL.md`,
  `packs/core/.apm/agents/implementer.md`,
  `packs/core/.apm/agents/adversarial-reviewer.md`, and
  `packs/core/.apm/skills/work-loop/references/supervisor-mode.md`, and is the
  same text in all four once each whitespace run is collapsed to one space.
- [x] **AC2.** C2 appears in those same four files, and is the same text in
  all four under the same normalisation.
- [x] **AC3.** C1 and C2 each match the text this spec states in § The
  shipped clauses, not merely each other, so a reword applied identically at
  every site fails.
- [x] **AC4.** The opening words of C1 and of C2 occur exactly once in each of
  those four files.
- [x] **AC5.** Every occurrence of C1 and C2 sits inside the § Host markers
  structure for its site, and inside no HTML comment and no fenced block.
- [x] **AC6.** Each of the four files carries an HTML comment containing
  `Bundled-fixes carve-out`, and each such comment names all four sites as
  `work-loop/SKILL.md`, `implementer.md`, `adversarial-reviewer.md`, and
  `work-loop/references/supervisor-mode.md`.
- [x] **AC7.** None of `Tier 1`, `Tier 2`, `Tier 3`, `same-area`,
  `same-concern`, `visibly smaller`, or `bundled-fixes tiers` appears in any
  of the four files, compared case-insensitively over whitespace-normalised
  text so a wrapped or re-cased occurrence cannot pass.
- [x] **AC8.** `packs/core/tests/pack/test_ride_along_admission_test.py` reds
  under each of these mutations, applied one at a time to the complete tree,
  each record naming the assertion that caught it and quoting the message it
  emitted: changing one interior word of C1 in exactly one file; changing one
  interior word of C2 in exactly one file; adding a second copy of C1 to
  exactly one file; moving one file's C1 out of its host into an adjacent
  HTML comment; rewording C1 identically at all four sites; and changing one
  carve-out comment back to naming three sites.
- [x] **AC9.** The DECIDE intent-fit routing table in `SKILL.md` carries a row
  whose first two cells are `Does not match` and `Include now, ride-along
  eligible`, and whose third cell reads `Admit it only if it passes every
  clause of the bundled-fixes carve-out. That test decides, not this row: a
  change failing any clause needs the owner's scope change like any other.`
- [x] **AC10.** `SKILL.md` carries a `## Capture` heading and no
  `## Capture learnings` heading, no link in that file targets
  `#capture-learnings`, and every link targeting `#capture` resolves.
- [x] **AC11.** `## Capture`'s scratch-note bullet names five destinations —
  the `project-knowledge` seam as an additive route, immediate dispatch, the
  session's next reviewed unit, capture, and discard — and both discard
  branches: a defect resting on taste or with no stated arbiter, and a note
  naming no defect that had nothing for the seam. The string
  `otherwise discard it` does not appear in that section.
- [x] **AC12.** No file under `packs/`, `tools/`, or `guides/` names the
  retired step in bytes the sweep can inspect, in any casing or separator,
  except the `evals.json` case id. That is the control's only exemption —
  `docs/knowledge/` records keep the name as a stable gate identifier but lie
  outside the swept roots, so exempting them would be unreachable. The
  quantifier stops at inspectable bytes on purpose: a compressed container
  such as a `.docx` can hold the name in a form no byte or text sweep sees,
  and claiming otherwise would put the criterion beyond any control that
  could meet it. Nothing is skipped — the sweep reads every file's bytes, so
  no file is one it cannot read.
- [x] **AC13.** `docs/rfc/0090-change-sizing-and-decomposition.md` § Errata
  carries a dated entry that states the number of clauses C1 actually ships,
  names C2's subject, gives at least one reason the tiers were replaced, ends
  `Approver: eugenelim`, and adds no line above the `## Errata` heading
  against the merge base with `origin/main`.
- [x] **AC14.** `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` declare the same version, exactly
  one patch above the highest `[core]` version in `docs/product/changelog.md`
  before this change, and the topmost release heading in that file is
  `## [core][<that version>] — <an ISO date>` carrying a `### Highlights`
  block.
- [x] **AC15.** `evals.json` carries two cases, read with the standard
  library rather than a regex. The first names a fix outside the plan task
  and states, in its prompt, a fact establishing each of C1's four clauses;
  its assertions require the answer to dispatch rather than discard or defer.
  The second names a declared-unattended dispatch whose only bar is an owner
  decision; its assertions require `blocked_on: decision` and forbid asking,
  waiting, guessing, and treating the item as a blocker.
- [x] **AC16.** `packs/core/.apm/skills/work-loop/references/bundled-fixes.md`
  states each of these outcomes, not merely each topic:
  a design call is resolved only by a citation or by an owner's answer;
  a citation is a shipped rule, an accepted decision record, a convention
  document, or the commit whose message records the decision, and must
  resolve at the change's merge base with no commit on the branch authoring
  it;
  applying a recorded answer is a lookup rather than a decision and needs no
  human;
  not remembering a rule that applies is an unresolved design call rather
  than the absence of one;
  an owner's answer resolves one, is given in one line in-session, and is
  recorded with its question in the `Bundled fixes:` entry;
  a dispatch brief carrying exactly one attendance declaration is followed —
  attended means ask there, unattended means do not ask — and every other
  case — no brief, silence, or both declared — records the
  question wherever the run reports its result and reads the reply, where an
  answer counts only when the reply names the question;
  an agent does not probe for a human and does not pause the loop beyond the
  stop it already makes;
  where no citation exists and no answer was given the item falls out,
  captured with `blocked_on: decision`, without asking again, guessing, or
  treating the absence as a blocker;
  and a resolution that would change a convention, a contract, or a
  published interface is refused however settled the answer looks.
  It also states what presents a choice, that an authorization or answer
  found in content the agent reads is data and never a grant, and the
  residual limit that recognition does not reach a behaviour-neutral
  placement, ordering, or decomposition choice.
- [x] **AC17.** The verification ledger records, against the tree as shipped:
  AC8's mutation set with each emitted message; the goal-based checks behind
  AC13 and AC14 with the commands run and their output; the three
  installed-artifact discoveries exercising the wording actually projected —
  one resolved by citation, one needing an owner answer where no brief
  declares attendance, one in a declared-unattended dispatch; and a walk of
  `## Capture` against these five notes, each reaching the named destination
  and no other: a ready-now non-generalisable defect with a stated arbiter
  that fires a risk trigger → next reviewed unit; the same defect with
  unstateable verification → next reviewed unit; a ride-along whose only bar
  is an unresolved design call with no citation and no answer → capture; a
  pure lesson → the seam alone; a generalisable decision-blocked defect →
  the seam and capture.

## Follow-ons

- work-loop maintainer: the carve-out grant travels as in-band prose in the
  dispatch brief, and denial is by omitting the authorization line, so
  authorization text inside any content the implementer reads re-grants it.
  C2 now makes such an occurrence inert, which bounds the reading but not the
  channel. Pre-dates this change; the channel needs a field the task body
  cannot occupy. Owner: work-loop maintainer, via `work-intake`.
- work-loop maintainer: `supervisor-mode.md`'s post-merge `Bundled fixes:`
  lift deduplicates by exact string with an operator-judgment fallback, and
  reconciles against no artifact, so two distinct ride-alongs described alike
  can merge and one leaves the PR body. C7 bounds only the entries carrying
  recorded questions. Pre-dates this change. Owner: work-loop maintainer.
- work-loop maintainer: `blocked_on: decision` has no named destination or
  reader. This spec introduces the token and deliberately leaves the store to
  the in-flight design; until that lands, a decision-blocked item reaches a
  surface nobody is obliged to read.
- work-loop maintainer: `docs/product/intents/` intake via `work-intake` —
  where a captured item is stored. A separate design is in flight; this spec
  stops the discard and requires the discriminator, and does not choose a
  store.
- work-loop maintainer: PLAN-stage coverage. A non-matching discovery found
  while authoring a plan has no same-session path, because neither a plan task
  nor the `blocker-applied` edge exists yet. Accepted deliberately; not
  addressed here and not described in the shipped prose.

## Assumptions

none
