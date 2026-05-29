# How to propose a cross-cutting change (RFC)

You have a change in mind that touches more than one package, alters a
convention, or reverses a previous decision — the kind of change where
"open a PR and see what happens" is the wrong shape. This guide walks
the path of drafting an RFC with the `new-rfc` skill: scaffolding the
file, running the per-subpoint research-and-de-risk phase before any body
sentence gets written, drafting answer-first, and circulating the proposal
after a self-review gate.

For the surrounding system — where RFCs sit relative to ADRs, specs,
and the loop that builds features once an RFC is accepted — read [the
core pack as a system](../explanation/core-pack.md). This guide is
task-oriented; it tells you what to type and what to expect back.

## RFC vs. ADR — which one fits

The two skills look adjacent but solve different problems. Get this
right before you invoke either, or you'll write the wrong artifact
twice.

| Question | RFC | ADR |
| --- | --- | --- |
| Tense | Forward-looking ("should we change X?") | Backward-facing ("we chose X over Y") |
| Lifecycle | `Draft` → `Open` → `Final Comment Period` → `Accepted` \| `Rejected` \| `Withdrawn` (optional `Experimental` while a trial runs) | `Proposed` → `Accepted` → (`Deprecated` \| `Superseded by ADR-NNNN`) |
| Body after acceptance | Frozen at acceptance (status field can change later, body cannot); stays as historical record; produces follow-on ADRs, specs, or CONVENTIONS edits | Frozen at acceptance (status field can change later, body cannot) |
| Reject path | `Rejected` is a normal terminal state — the discussion was the point | A pre-acceptance ADR that doesn't earn `Accepted` just isn't committed; there's no `Rejected` state |
| Trigger | The decision is still being debated, or affects external users | The decision is made (or is being formally proposed) and has a concrete tradeoff |

Quick rule: **RFCs propose; ADRs record.** If the discussion hasn't
happened yet, you want an RFC. If the discussion is done and you're
writing it down so the next maintainer can reconstruct it, you want an
ADR. Both are covered by the lifecycle table in
[`docs/CONVENTIONS.md` § Document lifecycle](../../CONVENTIONS.md#document-lifecycle).

If you're recording a decision that's already settled, see
[how to record a decision (ADR)](new-adr.md) instead.

## Prerequisites

> **Pack:** `governance-extras`. `new-rfc` does not ship in `core`.
> Verify with `ls .claude/skills/new-rfc/` (or the equivalent skill
> registry in your IDE — Claude Code's `/agents`, Cursor's Composer,
> etc.). If the directory is missing, install or enable
> `governance-extras` first.

- A working `docs/rfc/` directory. The skill creates one if it's
  missing, but the home for the file matters — the lifecycle rules in
  `docs/CONVENTIONS.md` only apply to RFCs at this path.
- Web search available in your agent harness (Claude Code's
  `WebSearch`, or the equivalent elsewhere). The external prior-art
  sweep degrades gracefully without it — the skill says so explicitly
  rather than fabricating citations — but you lose half the research
  phase's value.

## When `new-rfc` is the right call

Before invoking, check that the change clears at least one of these
bars, lifted from [`docs/CONVENTIONS.md` § RFC](../../CONVENTIONS.md#3-rfc--request-for-comments--docsrfc):

- It touches more than one package, or affects external users.
- It reverses a previous ADR.
- It adds, removes, or modifies a top-level directory or convention.
- You expect any reasonable contributor to want a say.

If none of these fire — the change fits in one package and preserves
public interfaces — push back on yourself. A normal PR is enough.
[`AGENTS.md`](../../../AGENTS.md) carries the same rule for
*substantive* CHARTER edits: those go through RFC, but trivial ones
(typos, broken links) ship as PRs.

> **Invoke skills by name.** Claude Code's description-based
> auto-discovery is best-effort — natural phrasings like "let's get
> input on X" usually fire the right skill, but not always. **Naming
> the skill in your request guarantees it fires.** Lead with
> `use the new-rfc skill to …` whenever you want the discipline to
> trigger reliably.

## Step 1 — Invoke `new-rfc`

Two worked invocations from genuinely different RFC shapes:

```
use the new-rfc skill to propose a new commit-message convention
requiring spec citations in every feature PR
```
(a *new* convention — adds a rule that doesn't exist yet; the
research phase will look hard for prior conventions the rule would
clash with.)

```
use the new-rfc skill to amend the work-loop iteration cap from 5
to 7 based on six months of stasis-detection data
```
(Differs from above: an *amendment* to an existing convention — the
research phase already has the target sitting in `docs/CONVENTIONS.md`,
so the proposal hinges on whether the precedent's reasoning still
holds today, not on prior-art existence.)

Natural phrasings (`propose a change to …`, `let's get input on …`,
`draft an RFC for …`) match the skill's description and often
trigger it. The explicit form is the reliable one.

## Step 2 — Watch the research + de-risk phase

The skill scaffolds `docs/rfc/NNNN-<kebab-title>.md` from the bundled
template and then **stops** before writing any body sentence. This is
the load-bearing move: a complex RFC is a tree, not one blob, so the
skill researches each *subpoint*, models its options out, and de-risks
its own riskiest assumption — rather than handing you a pile of
un-researched questions to rescue.

You'll see a `RESEARCH FINDINGS:` block in chat (not in the RFC file —
the body is gated) with these sections:

1. **Decisions / subpoints.** The proposal broken into the decisions it
   asks for. Each lists its options — *collectively exhaustive (MECE)
   along a stated axis and grounded in prior art, not a round number
   someone invented* — plus a recommendation, an owner, and a decide-by.
   This is where to push: if a subpoint shows "3 options" with no axis
   or sources, the space wasn't modelled.
2. **Prior art (in repo).** Grep hits across `docs/CHARTER.md`,
   `docs/CONVENTIONS.md`, `docs/adr/`, `docs/rfc/`, `docs/specs/`, and
   `docs/architecture/`, each with a file path. They often reveal the
   proposal touches something you didn't know was decided.
3. **Prior art (external).** Web-search results on how comparable
   projects or processes handled this shape of problem (Rust RFCs, PEPs,
   IETF BCPs). Each a markdown link. Empty here is a finding — say so —
   not an omission.
4. **De-risk.** The one assumption that, if false, sinks the proposal,
   and the result of a small spike against it (or why none was needed).

Read the recommendations carefully. For each:

- **Accept** — the recommendation folds into the body when drafting
  resumes.
- **Reject without an alternative** — the question stays in the body's
  `Open questions` section, with a recommended default + owner +
  decide-by.
- **Revise** — give the skill the alternative; it will re-thread that
  one finding into the body.

> **Do not approve the block in bulk.** A vague "looks good" doesn't
> count as sign-off on the highest-stakes recommendation. Name the
> recommendation you're accepting, especially when the skill flagged
> one as load-bearing.

## Step 3 — Drafting resumes, answer-first

Once you sign off, the skill drafts the body — leading with the decision,
then cascading detail:

- **The ask.** Answer-first: the recommendation (BLUF) + an SCQA framing
  (Situation → Complication → Question) + the numbered decisions you're
  being asked to make, each with a recommended option and a decide-by. A
  reviewer should know what they're approving from the first screen.
- **Problem & goals.** Diagnosis before solution, plus **Non-goals** —
  the could-have-been-goals deliberately dropped (not "won't crash").
- **Proposal.** The concrete shape of the change, detailed under each
  decision.
- **Options considered.** Mandatory and MECE along a stated axis, each
  option grounded in prior art and including "do nothing." The skill
  pushes back if the enumeration is a round number with no exhaustiveness
  argument.
- **Risks & what would make this wrong.** A pre-mortem (assume it shipped
  and failed), falsifiable key assumptions, and drawbacks. The skill
  pushes back on "no drawbacks."
- **Evidence & prior art.** The spike result and the prior-art citations
  from the research phase. Empty-with-explanation is valid; empty-with-no-
  explanation is not, and every citation is fetched and confirmed.
- **Open questions.** Each carries a recommended default + owner +
  decide-by.
- **Experiment / validation** (optional). Present only if the proposal
  needs an experiment — hypothesis, what's measured, success/failure
  criteria — with the *results* linked out to a spike note, not pasted
  into the RFC. Once circulating, while the trial runs the RFC sits in
  `Experimental` (see Step 5).

The file lands at `docs/rfc/NNNN-<kebab-title>.md` with status `Draft` and
an `Approver` named in the frontmatter.

## Step 4 — The pre-handoff gate

Before the RFC moves to `Open`, the skill runs a mandatory self-review gate
so you aren't the one catching obvious misses. Each check is *run, not
asserted*:

- **Citation-integrity.** Every reference is fetched and confirmed to
  actually contain the claim it's cited for — a link that merely loads
  isn't enough. Citations are challenged the same way (by fetching), never
  by eyeballing whether an identifier "looks real."
- **Verify-before-you-assert.** Self-claims the RFC makes about itself
  (counts, "lighter", "readable") are checked against the artifact.
- **Per-subpoint backing + completeness.** Each decision is backed; the
  `Approver` is named; every decision has a recommendation; do-nothing is
  present; open questions are ≤3 and owned.
- **A different-lens review.** A fresh-context `adversarial-reviewer` pass
  (and `security-reviewer` if the RFC touches a security boundary), re-run
  until clean — because a same-session self-check rationalises its own
  draft.

## Step 5 — Move through the lifecycle

The lifecycle is `Draft → Open → Final Comment Period →
Accepted | Rejected | Withdrawn`. You move the status manually as
the discussion progresses:

- **`Draft`** — still working on it; not yet circulated.
- **`Open`** — ready for reviewers. Update the frontmatter and push.
- **`Final Comment Period`** — discussion is winding down; last call
  for objections.
- **`Experimental`** (optional) — the proposal includes an
  `Experiment / validation` section and the trial is running; the RFC
  sits here, results pending in a linked spike note, until they land and
  it moves to a terminal status. Use only when an experiment is genuinely
  in flight.
- **`Accepted`** | **`Rejected`** | **`Withdrawn`** — terminal. Fill in
  `Date closed:`. The RFC freezes here (see [`CONVENTIONS.md` § Document
  lifecycle](../../CONVENTIONS.md#document-lifecycle)) — status field
  can change later (e.g. a future RFC supersedes it), the body cannot.

The skill also updates `docs/rfc/README.md` so the new file shows up
in the index.

## Step 6 — After acceptance

An accepted RFC is rarely the last artifact. It points at concrete
follow-on work, which lives in `docs/specs/<feature>/`, `docs/adr/`,
or `docs/CONVENTIONS.md`:

- **Architectural decisions → one or more ADRs.** See [how to record
  a decision (ADR)](new-adr.md).
- **Concrete features → specs.** See [how to plan and execute
  non-trivial work](plan-and-execute-non-trivial-work.md).
- **Convention changes → direct edits to `docs/CONVENTIONS.md`.** The
  change itself, not a copy of the RFC text. Cite the RFC where the
  reasoning belongs.

The RFC's job is done once the follow-on artifacts exist. It stays as
history.

## Pitfalls

> **Writing body content before the research phase clears.** The
> skill refuses to do this; if you find yourself filling sections by
> hand to "save time", you've skipped the part of the workflow that
> makes the RFC worth reading. Let the research phase emit, sign off,
> *then* let the body fill.

> **Empty `Evidence & prior art` when web search was available.** "We
> didn't look" isn't an answer — the external sweep is exactly what
> distinguishes an RFC from a wishlist. If the sweep genuinely
> returned nothing, say so explicitly under the heading and link the
> queries you ran.

> **An invented, round-number option list.** "Three categories" with no
> stated axis and no sources means the space wasn't modelled — exactly
> the failure the per-subpoint research phase exists to prevent. Push
> the skill to make each `Options considered` enumeration MECE along a
> stated axis and grounded in prior art.

> **An unverified citation.** A link that loads is not proof — the
> claim has to actually be in the source. The skill's gate fetches and
> confirms every reference (and challenges a doubtful one by fetching,
> not by judging whether the identifier "looks real"); don't wave a
> citation through on plausibility.

> **Bare open questions with no recommended default.** Every entry in
> `Open questions` should carry a recommended default + owner +
> decide-by, even if the default is "punt to reviewers." Reviewers
> reading bare questions waste a round asking for context the author
> already had.

> **Treating an RFC as a venue to relitigate an accepted ADR
> without naming it.** If you're proposing a reversal, cite the ADR
> in `Related:` and address its reasoning directly in `Problem & goals`.
> The skill's repo-sweep will surface the ADR anyway; engaging with
> it up-front saves a review round.

> **Drifting a `Draft` RFC indefinitely.** A `Draft` that never moves
> to `Open` is functionally a private note. If you're not ready to
> circulate, ask whether the proposal is actually ready to exist as
> an RFC, or whether a spike or investigation note belongs first.

## When not to use this workflow

- **A bug fix, performance improvement, or refactor that preserves
  behavior.** Just open a PR. RFCs are for proposing change to
  shared shape, not for fixing what's already agreed.
- **A new feature that fits cleanly within one package and changes
  no interface.** Write a spec, not an RFC — see [how to plan and
  execute non-trivial work](plan-and-execute-non-trivial-work.md).
- **A decision that's already settled.** That's an ADR — see [how to
  record a decision (ADR)](new-adr.md). The `new-rfc` skill
  explicitly refuses to scaffold an RFC for an already-decided thing.
- **Single-feature internals.** The contract for one feature lives in
  `docs/specs/<feature>/spec.md`, not in an RFC.

## Related

- [How to record a decision (ADR)](new-adr.md) — the inverse skill;
  use it when the discussion is done.
- [How to plan and execute non-trivial work](plan-and-execute-non-trivial-work.md) —
  what an accepted RFC's feature follow-on looks like.
- [The core pack as a system](../explanation/core-pack.md) — where
  governance-extras fits relative to `core`.
- [`new-rfc` skill](../../../packs/governance-extras/.apm/skills/new-rfc/SKILL.md) —
  authoritative procedure, including the research-phase gating rules.
- [`docs/CONVENTIONS.md` § RFC](../../CONVENTIONS.md#3-rfc--request-for-comments--docsrfc) —
  the lifecycle, filename rule, and when-to / when-not-to.
- [`docs/CONVENTIONS.md` § Document lifecycle](../../CONVENTIONS.md#document-lifecycle) —
  living vs. frozen vs. governance, and why RFCs sit in their own
  bucket.
