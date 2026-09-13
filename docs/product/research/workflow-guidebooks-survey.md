# Guidebooks for multi-step, chat-driven skill workflows

> Discipline: applied (practitioner-pattern survey)

Run 2026-09-11 to answer one question behind slice S7 of
[`sdlc-guide-uplift-and-learning-paths`](../briefs/sdlc-guide-uplift-and-learning-paths.md):
what does a guidebook have to carry for a first-time team to walk a pack's
journey and actually execute it, skill by skill?

Four retrievers ran in parallel, one per sub-question. Confidence uses the
applied-mode overlay: `no peer review` is not a downgrade factor in a
practitioner domain, and `survivorship bias` and `stale prior art` are.
Independence is calibrated against the practitioner surface — same vendor,
same employer cohort, or reblogs of one original all count as one source.

## The headline

**Sequential ordering organises the navigation; type separation governs the
authoring.** The two are compatible, and treating them as rivals is the
mistake. `[high]` — converged independently from Diátaxis's own
non-prescriptive stance, Canonical's implementation, the Adapting-Diátaxis
practitioner guide, and the structure retriever's reading of onboarding
research.

This repository already encodes half of it:
`contracts/guide.schema.json` describes `kind` as "Diátaxis kind — a page
contract, not a directory requirement", and `order` as a "sort weight within a
pack group for navigation generation". So the carrier exists. What is missing is
content and a consistent contract for what each step must carry.

## Finding 1 — a workflow guidebook is a spine, not a taxonomy

For a first-time reader, a goal-ordered spine outperforms a corpus organised by
document type. `[moderate]` — supported by onboarding research (drop-off
concentrated before the first meaningful outcome), by the 2025 arXiv study whose
primary intervention was adding a "Start Here: First Contribution Pathway"
signal to an otherwise type-organised document set, and by practitioner guidance
to arrange content by the reader's goal rather than by document type.
Downgraded from `[high]` because **no controlled experiment compares an ordered
mixed-type sequence against a type-grouped equivalent**, and because every
published case is success-adjacent (`survivorship bias`).

The named anti-pattern is a **quadrant-complete corpus with no usable path**.
No case study documents it, which makes this repository an unusually clean
instance rather than a laggard.

## Finding 2 — the step, not the page, is the unit of a guidebook

Operational-runbook practice converges on a four-part step: the exact thing to
run, the expected output, a verification check, and a failure path. `[high]` —
AWS Well-Architected OPS07-BP03, corroborated by two independent runbook guides
and by hierarchical task analysis, which additionally warns against both
over- and under-decomposition.

Two further step-level rules:

- **One discrete action per step**, with sub-steps nested rather than flattened.
  `[high]`, multiple independent sources plus cognitive-load research on step
  granularity.
- **Prerequisites have two schools, and the split is about the reader.**
  General SOP practice front-loads one prerequisites section; high-stakes
  runbook practice makes prerequisites per-step safety gates. `[moderate]`. For
  a first-time team the per-step gate is the better fit, and the up-front list
  is the one a mid-sequence arrival never sees.

## Finding 3 — chat-driven tools need affordances CLI docs do not

This is where a skill differs from an ordinary documented capability, and the
evidence is clear even though it is young.

- **An utterance example is not optional.** Amazon's Alexa programme required
  three example phrases for certification — a skill could not publish without
  them. `[high]` for the fact of the requirement.
- **A prompt without a response is an anti-pattern.** "Without a documented
  expected output, a reader cannot distinguish correct operation from error."
  `[high]` — stated directly by tool-engineering guidance and corroborated by
  Nielsen Norman Group's finding that first-time users lacking capability
  signals fall back on vague "Can you do X?" prompts and enter reformulation
  loops.
- **Recognition over recall.** Users plateau at low prompting skill for years
  without aids that *show* options instead of requiring recall. `[moderate]`,
  single strong practitioner source.
- **A polished single response misleads.** Confident tone and tidy formatting
  create a halo effect, and readers treat draft output as finished work.
  `[high]` — NN/G, with real-world consequences documented.
- **Implying determinism is a distinct failure.** Three independent vendors
  state output variability in prose adjacent to the example. `[high]` on the
  practice; there is **no canonical wording**, and no evidence on which wording
  calibrates readers best.
- **The sample dialog is a first-class artifact**, complementary to a flow
  diagram rather than substitutable for it: one shows a single path end to end,
  the other shows branching. `[high]`, from the voice-assistant era — flag
  `stale prior art` for the medium, though the turn-attribution problem it
  solves is unchanged.

### Marking a human decision point

Three conventions exist and none is an industry standard `[moderate]`:

| Convention | Source surface |
| --- | --- |
| A labelled "Manual approval stage" block that visibly pauses the flow | agent flow designers |
| A UML `alt` block with Approved / Rejected branches, plus a code decorator | agentic-patterns writing |
| A three-tier symbol taxonomy — Always / Ask first / Never | AI-agent spec guidance |

The third is worth noting: **this repository already uses that exact taxonomy**
in every spec's Boundaries section. The convergence is independent.

### Distinguishing what the user types from what the agent returns

Five conventions, no standard `[high]` on the absence of a standard:

1. **Speaker-column table** — "User" / persona rows. The only form that
   attributes *every* turn.
2. Role-labelled JSON (`"role": "user"` / `"role": "assistant"`).
3. XML delimiters (`<user_query>` / `<assistant_response>`).
4. Colon-prefixed script (`User:` / `Bot:`) — oldest, no specification.
5. **Contextual separation** — prompt in a code block, result described in
   surrounding prose, no label. The weakest, and the one that relies on reader
   inference.

## Finding 4 — wayfinding must live in the page body

Practitioner consensus is that page-body signals are primary and site
navigation supplementary `[moderate]`, on three independent grounds: sidebars
are missed or not rendered, breadcrumbs convey hierarchy rather than position in
a flat sequence, and readers arrive mid-sequence from search rather than at
step one. The recommended mitigation is an **embedded sequence map at the top of
each step page** with the current step marked.

The failure mode has a name — "pinball documentation": a page that ends without
telling the reader where to go.

Two adjacent facts:

- Stepper guidance converges on **3–6 steps**, with completion declining past
  seven. `[low]` — the underlying research is from form and checkout contexts,
  not prose documentation, and transferring it is a context shift that may not
  hold.
- **A "next step" link has no controlled evidence behind it.** The most-cited
  figure, a "double-digit improvement in completion rates", is asserted with no
  primary source; the one 29%→68% case study is single-vendor with undisclosed
  methodology; the one peer-reviewed abandonment study did not test navigation
  as a variable. `[low]`, and this is the single most over-claimed number in the
  area.

**Mislabelled optional steps are a documented single-point failure** `[moderate]`
— an "optional" label that is not genuinely consequence-free creates a false
sense of choice. The practitioner rule is to mark a step optional only when
skipping it has no downstream effect, and otherwise to say what skipping costs.

## The internal baseline — our own corpus, measured

Our guidebooks are a reference point, not a benchmark. Measured 2026-09-11 with
`python3 tools/audit-guide-affordances.py --ledger`, over the five packs a team
SOP needs.

| Pack | journey stages | skills | named in journey | **unreached** |
| --- | --: | --: | --: | --: |
| `desk-research` | 3 | 12 | 12 | 0 |
| `product-strategy` | 4 | 9 | 9 | 0 |
| `experience-design` | 5 | 20 | 10 | **10** |
| `product-engineering` | 6 | 15 | 6 | **9** |
| `core` | 7 | 18 | 8 | **10** |

**29 of 74 skills are named nowhere in their own pack's journey.** Stage counts
sit inside the 3–6 band; reach does not.

Guide-side affordance coverage, how-to and tutorial pages only:

| Pack | guides | prompt | example input | sample output | stated outcome | all four |
| --- | --: | --: | --: | --: | --: | --: |
| `desk-research` | 4 | 4 | 0 | 3 | 0 | 0 |
| `product-strategy` | 4 | 4 | 0 | 0 | 4 | 0 |
| `experience-design` | 2 | 0 | 1 | 0 | 1 | 0 |
| `product-engineering` | 14 | 14 | 2 | 4 | 14 | 1 |
| `core` | 18 | 18 | 2 | 5 | 13 | 1 |

Corpus-wide: 108 how-to and tutorial guides, **3** carry all four; demonstrated
input is the scarcest at **8 of 108**. Only 2 of 208 guides carry all five
measured affordances.

Flow is the worst of the four. Using the predicate *"the skill's `SKILL.md`
carries a Next / After / Then heading, a bolded Next lead, or a `run X next`
sentence"*, **6 of 74 skills name what comes next** — `experience-design` 0 of
20, `product-strategy` 0 of 9, `core` 0 of 18. The six that do are the four
`desk-research-project-*` lifecycle skills and two product-engineering skills.

**Our one ordered guidebook is not an exemplar.** `guides/atlassian/` is the
only pack using `order:` to carry a sequence, and none of its four ordered steps
carries all four affordances; its step 2 has a prompt and nothing else. So the
mechanism is proven and the content is not.

**Where our journeys are genuinely strong.** A `JOURNEY.md` stage already
carries the chat pattern the research asks for — the thing to type, a sample
agent response including the gate question, an explicit **You decide**, an
**Output**, and a **State**. Against the findings above it has two gaps: the
fenced sample mixes the typed invocation and the agent's reply in **one
unlabelled block** (convention 5, the weakest), and it carries **no variability
caveat**, which is the "implying determinism" anti-pattern. Neither gap has
reached the guides at all, because the guides do not use the pattern.

## Part 2 — the deliverable half

Added 2026-09-11 on owner direction: these skills generate artifacts, so a
guidebook must orient a reader on the deliverable's type and form, and on
reviewing the output once it exists. Three further retrievers ran. The first
part of this survey covered CLI output and chat responses; none of it covered a
conversational tool whose real product is a file on disk.

### Finding 5 — a stated form and a worked instance are both required

**Sadler's two-channel standard is the load-bearing result.** Sadler (1989)
argues that "guild knowledge keeps the concept of the standard relatively
inaccessible to the learner", and prescribes two channels *together*: verbal
descriptive statements of the criteria, **plus** worked exemplars. **Neither
alone is sufficient.** `[high]` — a primary source, corroborated by
independent university teaching guidance and by the worked-example effect, whose
mechanism is that an annotated instance supplies the expert schema a novice
would otherwise have to construct.

The matching anti-pattern is the most consistently documented failure across
education, consulting and design surfaces: **a template with no filled
example**, where a producer cannot tell what level of detail, what register, or
what belongs in a field `[high]`. A related one is **naming a deliverable
without specifying its shape**, named directly in the creative-brief literature.

Three constraints qualify it, and each changes how the obligation must be
written:

- **Do not show one polished exemplar.** Exposure to exceptional work can lead
  producers to conclude they are not capable of it and disengage `[moderate]`,
  single strong source repeatedly cited. The prescription is a range of quality
  levels, or at minimum an honest instance rather than a showcase one.
- **Do not let the exemplar map onto the reader's own task.** Copying risk; the
  guidance is short excerpts, or an instance on a different subject
  `[moderate]`.
- **Exemplars are used twice, and the two uses are different.** Hawe and Dixon
  observed producers using them at planning to understand structure, and again
  at revision to compare quality `[moderate]`, behaviourally observed rather
  than self-reported.

**And the honesty constraint.** One study found **no significant increase in
output quality** from adding an exemplar facility, despite producers valuing it
highly `[high]` on the null result itself. So the obligation is justified as
making the standard accessible, never as a quality improvement.

On timing there is a genuine split `[low]`: consulting, design-brief and most
teaching guidance put "what good looks like" *before* production, while one
teaching source argues for letting the producer grapple first where original
thinking matters. The two-phase use finding reconciles them — structure before,
quality comparison after.

### Transfer validity — why the anchoring evidence needs translating

**Owner caution, 2026-09-11, and it is correct.** Finding 5's evidence comes
overwhelmingly from education and consulting: a student's submitted assignment,
a marked essay, a signed-off deliverable schedule. Those artifacts share
properties ours do not have.

| The surveyed setting | Our setting |
| --- | --- |
| Produced once, submitted, marked | A file in a versioned repository, regenerable by re-running the skill |
| Producer and reviewer are different people | The same person produces and reviews |
| Revision is costly and often disallowed | Revision is a re-prompt, a diff, or a revert |
| The exemplar is a static copy | The exemplar can be a live artifact in the same tree |
| Failing is graded | Failing is cheap and recoverable |

Three consequences, and each is a house decision rather than a finding:

- **The exemplar should be a pointer to a real committed artifact, not an
  embedded sample.** This is the translation that matters. It satisfies Sadler's
  second channel while avoiding Finding 7's stale-output anti-pattern: an
  embedded instance is hand-maintained text and drifts by construction, whereas
  a path into the repository cannot misrepresent what the tool produces because
  it *is* what the tool produced. It also discharges the copying risk for free —
  a real artifact is on a different subject than the reader's own.
- **The intimidation effect weakens, and the re-prompt path matters more.**
  Rogers's finding concerns learners being assessed, for whom a flawless model
  answer implies an unreachable standard. A practitioner who can re-run the step
  in seconds is in a different position. The range-of-quality prescription is
  therefore downgraded here to *honest rather than showcase*, and the effort
  moves to Finding 6's failure path instead.
- **The timing split largely dissolves.** The grapple-first argument protects
  original thinking in an assessed task. Here the two-phase use finding is the
  operative one, and both phases are cheap: structure before the step, quality
  comparison after it, with a revert available if the comparison fails.

**What does transfer unchanged.** Sadler's core claim — that criteria alone
leave the standard inaccessible and need an instance beside them — is about how
a standard becomes legible, not about the medium it is printed on. The
template-with-no-filled-example anti-pattern transfers for the same reason. And
Finding 6's evidence is already digital and already about reviewing
machine-generated work in a tool, so it needs no translation.

### Finding 6 — reviewing the output is where automation bias bites

- **A single disclaimer does not work.** Regularly reminding decision-makers of
  possible system error significantly raised verification intensity, while a
  one-off disclaimer did not `[high]`. **This is why the variability caveat is a
  per-step obligation rather than a preamble.**
- **Polish suppresses scrutiny.** Developers using AI assistants wrote
  significantly less secure code *and were more likely to believe they had
  written secure code*; separately, highly aggregated presentation-quality
  output reduced verification intensity relative to rawer data `[high]`,
  independent surfaces.
- **A review with no failure path causes approval.** A reviewer who finds a
  problem and has nowhere to route it resolves the dissonance by reclassifying
  it as minor — "there is no third option called comment and forget"
  `[moderate]`. The inspection tradition's answer is older and stronger: a
  failed exit criterion triggers rework and re-inspection, never a pass.
- **Criteria that restate the generation instruction cannot work.** Reviewing
  for "does this look like what I asked for?" tests plausibility, which is
  exactly the dimension on which AI output already passes `[moderate]`,
  corroborated across two independent surfaces. A verification check must test
  the artifact against its declared form, not against the request.
- **Keep the check small.** Practitioner checklists converge on named, ordered
  passes of ten items or fewer, and attention degrades measurably past about
  twenty `[moderate]`.

**Two cautions recorded rather than buried.** One empirical study found **no
significant defect-detection difference** between checklist-based and ad hoc
code reading, so the presence of a checklist is not itself the mechanism
`[high]` on the null. And nearly all of this evidence is about **code** review,
where executable tests exist; our deliverables are prose documents, and the
transfer is an assumption this survey cannot discharge.

### Finding 7 — how file-generating tools show what landed where

- **The annotated file tree is the dominant device** `[high]` — a tree followed
  by one line per file explaining its role, across several independent
  documentation sets.
- **Mark generated artifacts where they appear in the tree**, not in a footnote
  `[moderate]` — one toolset tags them inline at the point of appearance.
- **Templated paths carry their notation inside the path string**, `{{ }}` or
  `[ ]`, with a legend nearby `[high]`. The matching anti-pattern is **showing a
  templated path as though it were literal**, which leaves the reader unable to
  tell what to substitute.
- **Show in full only the files the reader will edit** `[moderate]` — showing
  content signals "you will change this". The inverse anti-pattern is
  **explaining every generated file with equal weight**, so the reader cannot
  tell which matter.
- **A stale output tree actively misleads** `[high]`, and is structurally
  guaranteed for hand-maintained text because generator output changes per
  release. This is independent support for projecting a path from its source
  rather than restating it.
- **Naming a produced artifact without its location is a named anti-pattern**
  `[moderate]`.

**The gap we are walking into.** Only the infrastructure-as-code tools pair
their output with an inspection step — a saved plan, a command to show it, then
an apply against that exact plan, with the documentation saying to review before
applying. **No surveyed scaffolding tool documents an "inspect what was created
before proceeding" step** `[moderate]`, and the retriever found that agentic
coding tools' documentation does not present a written-file summary at all,
recording it as an unstudied area.

Our case has the IaC consequence profile rather than the scaffolder one: the
next step consumes the artifact, so a bad one propagates. Borrowing the
inspection pairing is therefore deliberate, and it is the part of this protocol
with the least precedent in the surveyed corpus.

## Part 3 — counter-research for digital forms

Commissioned 2026-09-11 on owner direction, because Part 2's anchoring evidence
comes from assessed, submitted, static work and "users aren't reviewing printed
books". Two retrievers were briefed to find the digital-native evidence and to
say plainly where it contradicts Part 2. It does, in three places, and each
changes an obligation.

### Finding 8 — an embedded static sample is the wrong mechanic

**Fischer et al. (2017) is the strongest single result in this survey.** Of 1.3
million Android applications, 15.4% contained security-related code sourced
from Stack Overflow, and **97.9% of those contained at least one insecure
snippet**, traceable to a small set of answers copied repeatedly `[high]`,
peer-reviewed. The mechanism by which a worked exemplar propagates its form is
the mechanism by which it propagates its errors.

Three further results point the same way:

- **Documentation drift is silent** — "no error logs, no alerts, no failing
  tests — just a steadily growing disconnect discovered only when a developer
  follows your instructions and gets an unexpected result" `[moderate]`.
- **Cargo-culting** from a canonical sample is documented across software and
  infrastructure-as-code surfaces `[moderate]`.
- **Progressive disclosure**: presenting full structure upfront raises error
  rates in interactive media `[moderate]`, NN/G.

**What the digital corpus favours instead is an exemplar that cannot drift**
because something fails when it does: compiled `examples/` trees, standard-library
doctests, golden files, committed dev-container definitions `[high]` on the
practices existing and being mature; `[low]` that they improve user success,
since no controlled comparison was found.

**And the insight that resolves our problem: scaffolding meets the exemplar need
by generation, not by a prior document.** A scaffolder *produces* the worked
example as its output; orientation is kinetic rather than textual `[moderate]`.
Our skills already do this — each writes a filled artifact on the reader's own
subject. So a guidebook's job was never to supply an exemplar. It is to say
what shape to expect, and how to check what arrives.

**What still supports Part 2.** A study of starter-template scaffolding found
partially-filled templates reduce cognitive load and raise self-efficacy against
blank ones — the worked-example effect holding in a digital medium, though in an
assessed educational setting `[moderate]`. And Sadler's core claim survives
unchanged: criteria alone leave the standard inaccessible. What changes is the
*form* the second channel takes, not whether one is needed.

**Against a tempting shortcut:** no evidence was found that cheap revision
reduces the anchoring need. Anchoring effects appear robust even when correction
is trivially cheap `[low]`, so "they can re-run it" is not a reason to weaken
the obligation.

### Finding 9 — a human check must exclude what a machine already checks

**Parasuraman and Manzey (2010) is peer-reviewed and decisive**: automation
complacency appears in naive and expert participants alike and is not overcome
by simple practice `[high]`. Applied to review: once an automated check passes,
people stop actively verifying and start trusting.

**The design consequence is specific and easy to get wrong.** A review list
that mixes machine-checkable items with judgement items **degrades the judgement
items** — the reader assumes the machine is watching and reads less carefully
`[moderate]`, converging from the complacency research and from practitioner
guidance that explicitly segregates the twelve human-mandatory review scenarios
from style, dependency and pattern checks, treating the mixture as a design
flaw.

So a structural check belongs to the lint and a judgement check belongs to the
reader, and the reader's list must not restate the lint's.

### Finding 10 — review effort should follow reversibility, not be uniform

The Type 1 / Type 2 distinction — irreversible decisions deserve deliberate
process, reversible ones quick judgement — is widely cited, and applying a
heavyweight model to a cheap, reversible decision is named as an organisational
anti-pattern `[moderate]`. This is decision theory applied to review by
inference, and the survey records it as such.

**But cheap revert does not replace the gate.** An industrial CI/CD study found
post-merge failures are "sticky", counted repeatedly until a fix propagates
downstream `[moderate]`. Cheap revert reduces the *severity* of an escape, not
the value of catching it. The widely-repeated "10-15x cheaper to catch early"
figure had no recoverable primary source and is not relied on here.

For AI-generated output specifically the evidence splits: diff review is
insufficient for agent *code*, because runtime behaviour decouples from the
source diff; for generated *documentation* a checklist is partially reinstated,
but as a **fast scan for known failure modes, not a formal inspection**
`[moderate]`.

### What Part 3 changes

| Obligation | Before Part 3 | After |
| --- | --- | --- |
| Row 7 | a check against the deliverable's declared form | **only the judgement a machine cannot make**; structural completeness moves to the lint |
| Rows 7 and 8 | uniform for every step | **fullest at the journey's declared decision gates**, lighter where the step is cheaply redone |
| Row 10 | a pointer to a real committed artifact | **the expected heading outline with its source declared** — compared against the skill's template asset or a real artifact where one exists, and presence plus declared authorship where none does. No embedded sample |

## Derived protocol — the guidebook step contract

Assembled from the findings, and deliberately not larger than they support. Each
row names the evidence behind it, so a reader can see which parts rest on
`[high]` findings and which are house choices closing a gap the evidence leaves
open.

| # | The step must carry | Grounded in |
| --- | --- | --- |
| 1 | **Where you are** — the sequence, with this step marked, in the page body | Finding 4, page-body primacy |
| 2 | **What you must already hold**, and what skipping it costs | Finding 2 per-step gates; Finding 4 optional-step failure |
| 3 | **What you type** — a literal utterance, projected from the owning source | Finding 3 utterance requirement; drift anti-pattern |
| 4 | **What comes back** — a representative agent response, visibly attributed as the agent's turn and separate from your input | Finding 3 prompt-without-response; convention 1 over convention 5 |
| 5 | **That output varies**, stated at this step and not once up front | Finding 3 determinism; Finding 6 — a single disclaimer does not raise verification |
| 6 | **Where you decide** — the human gate, marked | Finding 3 approval conventions; our own Always / Ask first / Never |
| 7 | **How to tell it worked** — the judgement a machine cannot make, never a restatement of the request and never a structural check the lint performs | Finding 2 runbook anatomy; Finding 6 plausibility-testing; Finding 9 complacency |
| 8 | **What to do when it does not** — a named decision: fix locally, re-prompt with the failing case, discard, step back, or escalate. Fullest at a declared decision gate | Finding 2 failure path; Finding 6 comment-and-forget; Finding 10 reversibility |
| 9 | **What you now hold** — the deliverable named, with its path, and any templated segment marked as templated | Finding 5 naming-without-shape; Finding 7 templated-path anti-pattern |
| 10 | **What to expect inside it** — the expected heading outline with its source declared; verified against the skill's template asset or a real artifact **where one exists**, and presence plus declared authorship where none does. No embedded sample | Finding 5 two channels; Finding 8 embedded-sample harm; Finding 7 templated paths |
| 11 | **What to run next** — named and linked | Finding 4 pinball anti-pattern |
| 12 | **Any concept the step depends on** — named, and linked to where it is explained; authored bounded only where no explanation exists | Finding 1 quadrant collapse; the cross-quadrant linking pattern; progressive disclosure |

**Corrected 2026-09-11 — the projection premise here was over-read.** An
earlier version of this commentary said rows 3, 4, 6 and 9 "are what a
`JOURNEY.md` stage already does". Measured per stage, that is true of
`experience-design` and false corpus-wide: across the five packs **13 of 25
stages carry an utterance, 14 carry a decision gate, 6 name a path, and four
carry neither an utterance nor a gate**. `contract.youType` exists for every
pack but is one utterance *per pack*, not one per stage, so it cannot supply
row 3 at step granularity. A contract author who followed the earlier wording
would have skipped the fallbacks the measurement requires.

So each projected row needs a **source ladder with a stated fallback**, and the
absence of a source must be representable rather than silent — silence otherwise
means both "this step has no gate" and "nobody recorded one". The ladders belong
to the consuming spec, which fixes them and checks them; this survey records only
that a single universal source does not exist.

**Row 10 is the expensive row, and its fallback is not verified.** Sadler
requires two channels, and measured over the five packs between 33 and 38 of 74
skills supply neither a template asset nor a stated shape — the figure moves with
the predicate, which is itself a finding and why no work should be sequenced on
it. Where a skill declares a shape, the outline is compared against it and drift
reds. **Where none does, the obligation is presence plus declared authorship and
nothing independently verifies the outline is correct.** That limitation is a
house choice, stated here rather than implied away. Row 9 by contrast is
projection: 63 of 74 skills already name a path.

Part 3 settles how the second channel is supplied. It is **not** an embedded
sample, which Finding 8 shows propagates its own errors and drifts silently. It
is the **expected heading outline**, which is shape without content — the
progressive-disclosure form — and which a lint can compare against the skill's
template asset or a real artifact so drift becomes a hard failure rather than a
silent one. That is the golden-file mechanic applied to prose.

The worked instance itself is the reader's own first run: the skill writes a
filled artifact on their subject, and row 7 checks what arrives. This is the
scaffolding insight, and it is why the thin real-artifact corpus in this
repository — about a dozen committed artifacts against 74 skills — does not
block the obligation.

**On row 12, where the evidence pulls both ways.** Inlining explanation into a
how-to is the most consistently documented Diátaxis anti-pattern — "content
drift", corroborated independently — and presenting full conceptual structure
upfront raises error rates under progressive disclosure. But a step whose
concept is reachable only by opening a maintainer document has failed a
first-time reader just as surely. The documented cross-quadrant pattern
resolves it: **link to the explanation rather than absorbing it**, which is the
standard practice for tutorials pointing at how-tos and how-tos pointing at
reference. `[moderate]` on the linking pattern and `[high]` on the collapse
anti-pattern it avoids.

Authoring a bounded explanation where none exists anywhere is a **house
choice**: no source in this survey addresses what to do when the concept a step
needs is undocumented, because the surveyed corpora assume the conceptual
material exists. It is bounded deliberately — a sentence or two plus a link out
— because the unbounded version is the collapse the first half of this finding
forbids.

**What this protocol must not claim.** It is a coherence and reachability
contract, not a conversion claim. The completion-rate numbers in this area are
either unsourced or single-vendor; the one controlled exemplar study found no
quality gain; and one checklist study found no defect-detection gain. So no
surface built on it may assert improved adoption, completion, task success or
first value — which also keeps it clear of this repository's standing
prohibition on unproven first-value claims.

## Known unknowns

- **Known-unknown:** whether an ordered mixed-type sequence beats a
  type-grouped corpus for a first-time reader. Would be closed by: a randomised
  comparison assigning equivalent first-time readers to each structure and
  measuring completion and abandonment. No such study exists in the practitioner
  or academic corpus.
- **Known-unknown:** whether worked prompt-and-response pairs measurably help
  first-time users of a natural-language-invoked tool. Would be closed by: an
  A/B test where half the readers see a prompt-and-response pair and half see
  prose description only.
- **Known-unknown:** which variability wording calibrates readers best — "your
  output will differ", "results may vary", or an explicit uncertainty
  statement. Would be closed by: a comparative usability study; none was found.
- **Known-unknown:** which turn-attribution convention reads best. Would be
  closed by: a comparative study of speaker-column against role-label against
  contextual separation. None exists.
- **Known-unknown:** whether Diátaxis's author considers ordered cross-quadrant
  sequences in or out of scope. Would be closed by: a primary statement in a
  talk transcript or issue thread. The official site carries none.
- **Unknowable:** the effect size of any single structural change in a real
  deployment. Documentation quality, product complexity, reader expertise and
  external support co-vary in every field setting, and isolating one factor
  would require withholding support resources.
- **Unknowable:** what a canonical "expected output" is for an open-ended
  agentic tool. Output varies with model version, context and tool-call state,
  so a fixed representative response is only representative of one execution
  environment. This is why row 5 of the protocol exists rather than an attempt
  to pin exact output.
- **Known-unknown:** whether a stated form plus a worked instance beats either
  alone for a first-time producer of a deliverable *type*. Would be closed by: a
  controlled comparison of spec-only, exemplar-only and both. The teaching
  literature tests assignment-level exemplars, not deliverable-type orientation.
- **Known-unknown:** whether naming the failure path reduces defect escape.
  Asserted by two practitioner frameworks, neither with outcome data.
- **Known-unknown:** how agentic coding tools present a written-file summary to
  a user, if at all. The retriever recorded this as an unstudied area.
- **Unknowable:** the defect rate in AI-generated prose documents without an
  independent oracle. A document that reads correctly but is subtly wrong may
  never be verified if the consumer also lacks ground truth, so the harm is
  structurally invisible.
- **Known-unknown:** whether a pointer to a live artifact anchors a producer as
  well as an embedded worked example. Would be closed by: a comparison of the
  two in a digital tool. The anchoring literature tests static exemplars only,
  because its setting has no live alternative.
- **Unknowable:** whether the code-review evidence transfers to prose-document
  review. Code has executable tests and most documents do not; no equivalent
  large-scale study of prose review exists.
- **Unknowable:** how often documentation failures caused a tool to go unused.
  Teams do not publish that, so the entire case-study corpus is
  survivorship-biased toward deployments that succeeded.

## Sources

Grouped by sub-question; primacy as returned by each retriever.

**Diátaxis and task-sequence structures** — diataxis.fr (official, primary);
Canonical's adoption write-up (primary case); Sequin's adoption write-up
(primary case); the Python community adoption discussion (primary);
Cherryleaf's documentation-and-learning-site guide describing Vonage's learning
paths (primary practitioner, single-sourced); Adapting Diátaxis for support
content (secondary); Baker, *The Tyranny of the Terrible Troika* (primary,
independent critic); Good Docs Project template releases (primary).

**Workflow guidebook structure** — AWS Well-Architected OPS07-BP03 (primary);
ACM CHI 2022 on playbook framework usability (primary); arXiv 2605.19174 on
AI-assisted onboarding restructuring (primary); cognitive-load studies on step
granularity and worked examples (primary); hierarchical task analysis overviews;
runbook-versus-playbook guides from two independent vendors; onboarding UX
pattern collections (secondary); *Optional steps in documentation, maybe don't*
(secondary); API documentation anti-pattern guide (secondary); ACM EuroPLoP
2017 on end-user documentation anti-patterns (primary).

**Chat and agentic tool affordances** — Google Conversation Design, *Write
Sample Dialogs* (primary); Alexa Skills Kit store-details requirements
(primary); Claude platform prompting best practices (primary); OpenAI prompt
engineering guide (primary); Microsoft Copilot Studio multistage approvals
(primary); Agentic Patterns human-in-the-loop approval framework (primary);
AgentPatterns.ai tool engineering (primary); NN/G *AI Chatbots Discourage Error
Checking* and *Prompt Structure in Conversations with Generative AI* (primary);
UX Tigers prompt-augmentation patterns (secondary); LLM anti-patterns handbook
(secondary); Addy Osmani, *How to Write a Good Spec for AI Agents* (secondary).

**Deliverable anchoring** — Sadler 1989 on the two-channel standard, via ERIC
and a full PDF (primary); the worked-example effect (secondary); university
teaching guidance on exemplars and rubrics from three independent institutions
(secondary); *Using Student Exemplars: A Caution* on the intimidation effect
(secondary); *From copying to learning* (primary, paywalled, reached via
secondary citation); *Setting an example* (primary, the null result); consulting
statement-of-work and deliverable-schedule guidance (secondary); a named
consultancy's four-component deliverable anatomy (secondary); pattern libraries
as deliverables (secondary); Definition-of-Done anti-pattern collections
(secondary).

**Output review** — Frontiers in Psychology on automation bias in selection
(primary); a clinical-trial protocol on behavioural nudges against LLM
diagnostic bias (primary); the Fagan inspection tradition and IEEE 1028
(tertiary for the summaries, primary for the rates); SmartBear's peer-review
practice guidance (primary); an empirical comparison of checklist-based against
ad hoc code reading (primary, the null result); *A Roadmap on Modern Code
Review* (primary); GitClear's 2025 code-quality analysis and Google's 2025 DORA
findings (primary); Codacy on automation bias in AI code review (primary); two
independent AI-PR review frameworks (primary); a documentation QA checklist for
AI-generated docs (primary); rubric-based evaluation guidance (secondary);
checklist-fatigue guidance (secondary).

**Generated-artifact documentation** — Django, Rails, Jekyll, Hugo, Sphinx,
Next.js, Vite, Yeoman, Cookiecutter, Copier, Spring Initializr, Terraform and
Pulumi documentation (all primary); a practitioner guide to Terraform plan
output (secondary); scaffolding-drift commentary (tertiary).

**Sequence wayfinding** — NN/G *Navigation: You Are Here*, *Breadcrumbs: 11
Design Guidelines*, *Local Navigation* (primary); Tom Johnson, *Building
Navigation for Your Documentation Site*, Write the Docs 2017 (primary, flag
`stale prior art` at nine years); Write the Docs documentation principles
(primary); MediaWiki tutorial pattern (primary); Divio documentation system
(primary); IEEE study on predicting abandonment in online coding tutorials
(primary, gamified-platform caveat); UXPin progress-tracker guidance
(secondary); Microsoft Learn module-completion discussion (secondary).
