---
title: "`experience-design` — guides"
summary: Start from the outcome a user is trying to reach, derive the screens it needs, design them completely, and get an independent review before engineering builds.
pack: experience-design
kind: explanation
---

# `experience-design` — guides

**Use this when** you have an experience or a surface to design and you want to
finish holding design intent someone can build. You leave with a journey you
approved, a screen for every moment it implies, a named visual direction those
screens are held to, every state each screen can be in — not just the happy one
— and findings from a reviewer that never watched the design being made.

**Start like this.** Ordinary language, in an agent session with this pack
installed. You do not have to pick a skill first.

```text
Our first-time workspace experience is losing people before they connect their first account. Design the experience from the customer journey through reviewed screen intent.
```

Name the user, the outcome they are after, where it breaks today, and any
constraint you already hold — a brand, an existing design system, the platform.
The agent runs the method each stage needs and says which one it ran. Skill
names stay available when you want to enter at one particular point; they are
not something to learn before you can begin.

Coming back to work you started earlier? Ask for the design-thread status. That
reads the artifacts already on disk, says which part of the thread is missing,
and names the next fitting skill. It writes nothing and decides nothing — there
is no workflow state behind it, only the files themselves.

## Where this fits

This pack works in the *Shape it* stage, next to Product Engineering. You
usually arrive with an approved intent or a strategy direction. You leave with
a reviewed design set, and the build loop writes its spec against it. [Where
the design goes next](#where-the-design-goes-next) lists everyone who uses what
you made. [See the whole flow](../_shared/explanation/the-three-loops.md#the-handoff-chain).

## Walk the guidebook

Five stages, in order. Each step shows what you type, what comes back, one turn
where you push back and the agent adjusts, where you decide, and an excerpt of
what you actually get.

1. [Map the customer journey](how-to/map-the-customer-journey.md) — what the user is trying to achieve, and the moments the current experience breaks.
2. [Derive the screen flow](how-to/derive-the-screen-flow.md) — what each surface has to communicate, then the screens, transitions, error routes, and the set of states each screen owes.
3. [Establish design intent](how-to/establish-design-intent.md) — the arbitration rules the journey's pains imply, the named visual direction, and the token roles that follow from that direction.
4. [Design each screen](how-to/design-each-screen.md) — structure suited to the screen's job, then behaviour for every state it can be in.
5. [Review independently](how-to/review-independently.md) — your own critique first, then a reviewer that reads the set cold.

The walk is a spine with branches, not a conveyor belt. [The spine and its
branches](#the-spine-and-its-branches) says which parts nothing downstream can
reconstruct, and when each branch is worth the detour.

## Where you decide

Three gates. The agent runs everything between them and stops at each one.

| You decide | At | The call you are making | Roughly |
| --- | --- | --- | --: |
| Approve the journey and the screens derived from it | End of step 2 | Does the journey name the outcome the user wants, rather than the tasks today's product makes them perform — and does every screen trace to a moment in it? | 10–15 min |
| Approve the aesthetic direction | Step 3 | Does the direction name a specific character with referents behind it, or could it describe any product? This covers the token roles too — one decision, not two. | 5–10 min |
| Disposition the review findings | Step 5 | Which findings block, which you accept as they are, and whether the set is ready to feed realization. | 15–25 min |

**The first gate closes after step 2, not step 1, and that is deliberate.**
`journey-mapping` produces the journey — stages, emotions, pains, opportunities,
and the frontstage actions. It does not propose screens; a journey with one
stage per screen is something the skill refuses. The screen list arrives in step
2, from `user-flow`. So the thing you approve is one thing seen whole: the
journey *and* the screens derived from it, where the check that earns the gate
is whether each screen traces back to a moment in the journey. Approving the
journey alone would leave the derivation — the part that can go wrong — unread.

A useful rejection sounds specific. "These stages are our current settings
screens with new names — regroup them as phases of what the customer is trying
to do" is a redirect the agent can act on. "Screens 4 and 5 aren't implied by
anything in the journey; either they come out or the journey is missing a
moment" is another. The agent proposes, and writes it down. It does not decide
what the experience should be.

## The spine and its branches

Two different things get called required here, and the difference is worth two
minutes.

**The spine** is the part nothing downstream can reconstruct. Drop one of these
and the thread breaks rather than thins:

1. The journey — the outcome and the failure moments (step 1).
2. The screen flow and the per-screen briefs (step 2).
3. At least one craft pass per screen: structure, then behaviour (step 4).
4. The independent review (step 5).

**Two more are required in a different sense** — the thread survives without
them, but each leaves a named gap rather than a broken chain:

- **The content brief** (step 2) settles what a surface has to communicate and
  to whom, before the screens are sequenced. Without it the flow is arranged
  around the functional path and a guess about the message.
- **The aesthetic direction** (step 3) is what every later craft decision is
  held to. Without it each screen looks reasonable alone and the set has
  nothing holding it together, and the reviewer flags every screen for the same
  missing constraint.

**Everything else is a branch**, worth running when its condition arrives:

| Branch | Worth running when |
| --- | --- |
| Brand register | Copy is being written on more than one surface and you have no shared answer for what wins when two copy goals disagree. |
| Per-surface copy goals | The surface is a marketing or acquisition page, where the copy carries the persuasion rather than labelling the controls. |
| Service blueprint | Screen actions depend on people, systems, or handoffs behind the line of visibility, and you need to know what backs each one. |
| Process mapping | The internal operation behind the experience is itself the problem — handoffs, waste, or nobody owning a decision. |
| Design principles | The same design argument keeps recurring and you want a rule that settles it next sprint too. |
| Token taxonomy | The direction is approved and someone is about to name colours, spacing, and type — and you want those names to trace to the direction. |

A branch you skip is a decision you have made. Its input travels forward as an
assumption nobody chose, which is the cost worth knowing before you skip it.
[Choose how much design a surface owes](how-to/choose-the-depth.md) covers the
same trade at the level of depth rather than breadth.

## How the method changes with the surface

A dashboard, a pricing page, and a sustained work tool are different structural
problems, not the same one at different sizes. You do not pick between them from
a menu. One skill designs structure, and it selects the matching method from the
surface genre declared on the screen's brief — analytical, marketing,
documentation, informational, marketplace, or workspace. A step-by-step
transactional journey is the seventh value, and it routes to the behaviour
work's wizard-and-stepper patterns instead of to a structure method of its own.
A brief that declares no genre does not fall back to something generic: the
agent asks which kind of surface this is before it arranges anything, because
the genre is what supplies the structural vocabulary.

Genre routes two things. It picks the **structural vocabulary** — a widget
hierarchy and its business questions for an analytical surface, an above-fold
contract and a scroll story for a marketing one, content typing and a
navigation tier for documentation. It also picks the **rubric the review runs**,
which is why a marketing surface and a documentation surface are reviewed in
separate passes rather than one: their rubrics ask incompatible questions.

Genre reaches the aesthetic direction too, but narrowly: it keys the starting
set for the direction's *precedent* referent — the surfaces studied as craft
examples — so the bar is set by work of the same kind. The direction's other
grounds — the persona it serves, the standards it respects, and the target
surface's platform conventions — are unaffected. What genre does not change at all is the
journey, the states each screen owes, and the floor — those are the same either
way. You declare it once, in step 2, and it routes the work from there.

## What every screen owes

A screen is not designed if only its happy path exists. One shared floor runs
under every artifact in this pack, and no skill may ship output that defers it
to later:

- **Every state it can be in** — empty, loading, error, success, partial, and
  disabled, plus `permission/denied` when the surface sits behind
  authorization. Empty splits further: never-had-data wants orientation and a
  first action, while a filter that emptied the view wants a way back.
- **The accessibility floor** — WCAG at the conformance level your context
  requires, with the criteria read from the standard rather than eyeballed. The
  independent reviewer treats an accessibility miss as at least a major finding,
  and raises it to a blocker on a core flow.
- **Motion that carries meaning, with a reduced-motion path** — every animation
  answers "what does this tell the user?", and the reduced-motion version keeps
  the information the movement was carrying.

This is a design obligation, not implementation cleanup. The states are settled
in step 2, where each screen's brief names which of them apply; step 4 designs
the behaviour between them. Depth changes how much evidence a surface owes, and
never whether someone can use it — the accessibility commitments hold at every
depth. The [skill and reviewer reference](reference/experience-design.md) is the
reader-facing version of the floor, and it names the file inside the pack that
is canonical when the two ever disagree.

## What you end with

Everything lands under one design output directory. Four placeholders appear in
the paths below: `<output_dir>` is that directory, which the agent resolves from
your layout configuration — this repository's first, then your personal one —
and surfaces to you before the first write; `<slug>` is the short
name you give this piece of work; `<screen>` is one screen as its brief names
it; and `<surface-slug>` names one acquisition surface.

| What you get | Where it lands |
| --- | --- |
| The customer journey | `<output_dir>/journeys/<slug>.md` |
| The screen flow, and one self-contained brief per screen | `<output_dir>/screens/<slug>-flow.md` and `<output_dir>/screens/<slug>/<screen>.md` |
| The structure for a screen | `<output_dir>/screens/<slug>-ia.md` |
| The aesthetic direction | `<output_dir>/direction/<slug>.md` |
| Design principles, token roles | `<output_dir>/principles/<slug>.md`, `<output_dir>/tokens/<slug>.md` |
| Content intent, brand register, per-surface copy goals | `<output_dir>/content/<slug>.md`, `<output_dir>/copy/brand-register.md`, `<output_dir>/copy/<surface-slug>.md` |
| Service blueprint, internal process map | `<output_dir>/blueprints/<slug>.md`, `<output_dir>/processes/<slug>.md` |

**The per-screen brief is the one to keep if you keep only one.** `user-flow`
writes it, and the behaviour design enriches that same file in place rather than
emitting its own, so the brief ends up carrying the screen's job, its states,
and how it behaves together. It also references the shared design contract —
the direction, the navigation model, the floor — instead of copying it, which is
what keeps a set of separately designed screens coherent.

Review findings are deliberately not on this list. Both reviews return in the
session and are acted on there; neither writes to disk.

## Where the design goes next

Design intent does not have one downstream owner. It fans out, and each
consumer takes a different part of what you produced.

| Design output | What happens next |
| --- | --- |
| The aesthetic direction, the per-screen briefs, and the token roles | `frontend-engineering`'s design pre-flight reads all three under the same slug before it writes any code. A slot you left empty is not an error — it resolves from a lower rung of the pre-flight's visual-authority precedence and records which rung supplied it. |
| The state matrix inside each brief | `product-engineering`'s `ux-writing` writes a UI string per screen × state, keyed to that matrix. It is the one copy boundary that crosses packs. |
| The brand register | `ux-writing` loads it as the voice those strings are written in. |
| The service blueprint's backstage column | Point `architect`'s design work at it before anyone proposes a backend: it names the frontstage obligations the backend has to meet. |
| The reviewed design set as a whole | `core`'s build loop specs against it — each screen brief becomes acceptance criteria rather than being restated. Continue at [write the contract](../core/how-to/write-the-contract.md). |

**The handoff moves the work, not the authority.** Nothing downstream is
approved by finishing here, and this pack's three gates stay yours.

## Two kinds of review, and why both

`design-review` runs in your session, with you, while the work is still moving.
It is how you improve a design you are shaping — it applies the floor, walks
usability heuristics, runs the genre rubric, and critiques taste against the
direction you approved.

The `experience-reviewer` is a different thing. It runs in a forked context with
no access to your session: it sees the artifacts, the grounded direction, and
the constraints, and never the reasoning that produced them. That absence is the
point — a reviewer who knows what you meant reads gaps charitably. It is
read-only by construction: it flags, and never rewrites. Its findings are the
last check before design intent feeds realization, and the third gate is you
dispositioning them.

It is a reviewer role rather than something you type, and it will not review a
code diff or an architecture document — it returns `WRONG ARTIFACT` and names
the reviewer that should have it.

## Leave the pack at the discipline boundary

- Market, audience, positioning, adoption, and organization-level direction
  belong to product strategy.
- Framing, appetite, risks, scope, solution options, and bet commitment belong
  to product-engineering shaping.
- HTML, CSS, components, data bindings, and build evidence belong to frontend
  engineering, after the design is approved.

## How-to

Recipes for a problem you already have, once the walk is familiar.

- [Thread a feature from journey to screens](how-to/author-design-intent.md) —
  the whole connective path end to end, in one continuous run.
- [Choose how much design a surface owes](how-to/choose-the-depth.md) —
  pick the depth for this run, and see which states every depth still owes.
- [Choose the right copy mode](how-to/copy-boundary.md) —
  which of the copy modes owns a task, and where `ux-writing` begins.

## Reference

- [The skills, the reviewer, and the quality floor](reference/experience-design.md) —
  what each skill and the `experience-reviewer` accept, return, read and write,
  the artifact layout, and the shared floor they all clear.

## Explanation

Read this after walking the guidebook, not before.

- [The experience thread](explanation/the-experience-thread.md) — how the
  connective and craft skills compose, why the discipline is framework-agnostic,
  the macro/micro carve between flow and interaction, and how design intent
  reaches the build.

---

Installing and upgrading live in [`../_shared/`](../_shared/).
