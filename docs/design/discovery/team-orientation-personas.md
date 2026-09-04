---
type: proto-personas
slug: team-orientation-personas
status: active
surface: cross-platform
evidence_level: assumption-based, with one observational behaviour per persona where it exists
updated: 2026-09-04
---

# Proto-personas — the four readers of one page

`journey-mapping` elicits a persona inline but emits no persona artifact, so this
is hand-authored. These are **proto-personas**: composites built from the
recorded adoption journey, the repository, and 14 days of behavioural data. They
are not research-validated portraits, and each one names what would change it.

The engagement's premise is that one page must serve four audiences at once. That
is the design problem in a sentence, so the personas are written to be compared
rather than read separately.

## At a glance

| | Champion | Engineer | Platform lead | Budget holder |
| --- | --- | --- | --- | --- |
| **Reads the page** | first, and repeatedly | after being sent | after being asked | once, briefly, in a meeting |
| **Wants to know** | can I take this to my org | will this slow me down | what do I own | what does it cost and what can go wrong |
| **Decides** | whether to advocate | whether to keep using it | whether to support it | whether to fund it |
| **Kills adoption by** | not being able to explain it | reverting quietly | refusing to own the install | asking one unanswerable question |
| **Currently served by** | nothing on either surface | the install command | nothing | nothing |
| **Priority** | **primary** | secondary | secondary | tertiary on the page, decisive in the room |

Three of the four are unserved today. That is the finding the table exists to
make visible.

## The champion — primary

**Who.** Somebody inside an organisation who has been asked to evaluate this, or
who found it and wants it. They have used a coding agent daily for months. They
have not used a supervised operating model. They cannot authorise adoption and
they cannot install it at scale.

**Their job.** *When I have found something I believe would make my team better,
I want to be able to explain it accurately to three different audiences, so that
the decision does not depend on my improvising.*

**What they need from the page.** One artifact that carries the whole model and
survives leaving the page. Not a summary they have to rebuild — the thing itself.

**Observed behaviour, and the limit of it.** Twelve distinct people opened a repository link through the Microsoft Teams referrer in the 14-day window, against six referred by the entire published site. What is measured is the *referral path*. That a champion sent it, and that it was transfer, is an inference the instrument cannot support — see the traffic review's stated limits.

**Worst moment.** *"I've done three live demos and every one felt like I was
improvising. The platform is genuinely good — the demo isn't."* Recorded in the
adoption journey as the highest-opportunity pain. Still an assumption; the
[champion interview](team-orientation-champion-interview.md) is the instrument
that tests it.

**What would change this persona.** If the interview shows the champion's real
blocker is a pricing or procurement question rather than an explanatory one, the
whole dominance argument weakens and the canvas becomes secondary to a
commercial answer.

## The engineer — secondary

**Who.** The person who will run this every day. Fluent with a coding agent,
skeptical of process, and the one who decides — silently, weeks later — whether
adoption survives.

**Their job.** *When my team adopts a new workflow, I want to know exactly what
it will demand of me and where it will get in my way, so that I can judge whether
it is worth the friction.*

**What they need from the page.** The work lifecycle, stated concretely, and an
honest account of what is mechanical versus what needs their judgement. They will
check claims. The second tech-site principle exists for this reader.

**Observed behaviour.** They read the source. One raw `SKILL.md` drew 12 unique
readers; a skill reference tree drew 7; `/tree/main/docs` drew 6. Given a choice
between a rendered guide and an unrendered file that is definitely the truth,
they choose the file.

**Worst moment.** Reversion, and it is quiet. The adoption journey records it:
*"It works well when I know what spec to run. When I don't, I go back to winging
it."* Nothing on the page tells them what happens in the ambiguous case.

**What would change this persona.** If reversion turns out to be driven by tool
friction rather than by unclear guidance, the page cannot fix it and should stop
trying.

## The platform lead — secondary

**Who.** Owns the repositories, the CI, the agent tooling decision, and the
support burden. Adoption cannot happen without them and they are never the one
who wants it.

**Their job.** *When somebody proposes a new system for my repositories, I want
to know precisely what I will own and what it will do without asking me, so that
I can support it without being surprised.*

**What they need from the page.** Scope and blast radius. Which parts install per
repository and which travel with a person. What runs unattended and what stops
for a human. Whether it touches their tracker, and in which direction.

**The question that decides them,** and the page does not answer it: *does this
write back to Jira?* The answer is a real product property — the tracker is a
one-way outbound projection and status never returns — and it appears nowhere on
either surface. This is why the canvas draws the tracker as a leaf with no return
edge.

**Worst moment.** Being handed a rollout with no playbook. The adoption journey
records it: *"The platform team wants a rollout plan but I don't have one."*

**What would change this persona.** If platform teams in practice delegate the
decision to the champion rather than gatekeeping it, this reader drops to
tertiary.

## The budget holder — tertiary on the page, decisive in the room

**Who.** A CTO, engineering director, or AI-programme lead. Will spend between
sixty seconds and five minutes on this, probably while somebody else is talking.

**Their job.** *When somebody asks me to fund a change to how my engineers work,
I want to understand the shape of the commitment and the worst realistic outcome,
so that I can decide without becoming an expert.*

**What they need from the page.** The adoption arc with its costs. What the
organisation is agreeing to. And — the question that ends most of these meetings
— *what does it refuse to do on its own?*

**Worst moment.** Asking one question the champion cannot answer, and concluding
the champion does not understand it either. The adoption journey records the
symmetric pain: *"Decision makers want to see it on our code, not a toy
example."*

**What would change this persona.** If buy-in in practice follows a successful
engineer-led pilot rather than a funding conversation, this reader becomes an
audience for a case study rather than for the home page.

## What this means for the above-the-fold decision

The four jobs are not four different explanations. They are four different
**entry points into one model**:

- the champion needs the whole shape, portable;
- the engineer needs one station of it — *prove it on real work* — in detail;
- the platform lead needs its boundaries — what is per-repo, what is per-person,
  what leaves the system;
- the budget holder needs its arc and its refusals.

A page that renders the model once, whole, with the adoption arc dominant and the
work detail nested inside it, serves all four from a single artifact. That is the
structural argument for the canvas, and it is why the answer is one canvas rather
than four audience tracks.

It also fixes the priority order. The champion is primary not because they matter
most, but because they are the only reader who has to carry the other three.
