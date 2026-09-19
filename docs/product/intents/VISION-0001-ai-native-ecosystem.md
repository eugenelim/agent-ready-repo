# AI-native ecosystem

- **Slug:** `ai-native-ecosystem` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Accepted:** 2026-09-19 by eugenelim, after an independent intent-mode shaping review returned no `MALFORMED` token on revision `78dde5e299649f58`.

- **Nonmaterial correction 2026-09-19 by eugenelim, lifecycle owner.** `Unresolved questions`, `Projection` and `Source` were backfilled to meet ADR-0098 D2's admission contract, which this family met only in part because it was framed by `frame-intent` and never admitted through `intake-intent`. `intake-intent` classes a change to projection, unresolved questions or source authority as material, which would return this intent to `Draft`; the lifecycle owner recorded it as nonmaterial because the sections record open matters and provenance that already existed in the artifact, and decide nothing new. Prior review evidence stands.
- **Kind:** outcome <!-- chain rung: the North Star / chain root; orthogonal to Level -->
- **Level:** product-vision
- **Scale:** business-unit
- **Maturity:** brownfield
- **Parent intent:** none <!-- deliberate entry at product-vision altitude; an ABSENT field means legacy or unclassified -->

## Outcome

- **Steerable input:** The share of work at each organisational layer that reaches done without a human gating it, and the time work spends waiting on a human gate.
- **Lagging outcome:** Autonomy increases across **every layer of product delivery** — engineering, product, design and research alike, not engineering alone: each layer can act on what the surrounding layers decided without a human re-explaining it first, and an organisation can own the whole model rather than rent it.
- **Guardrail:** Accountability does not degrade — every layer can still answer what was decided, by whom, and on what basis. Human judgement is relocated, never eliminated. No layer is forced to adopt a particular model, runtime or tracker in order to participate. And the people doing the remaining human work are not left worse off: more loaded, more error-prone, or deskilled.

## Opportunity

- **Functional job:** Let a layer of the organisation act on what the layer around it has decided, without a human re-establishing the context first or approving each unit of work.
- **Emotional job:** Delegate with confidence — trust that work will proceed correctly without watching it, and that if it goes wrong the reason will be recoverable rather than lost. Not the confidence of having skimmed it; the confidence of not having needed to.
- **Social job:** Show that autonomy at scale is defensible rather than reckless: that the organisation can account for what its agents did and why, at any layer, when asked.
- **Struggling moment:** The bottleneck has moved and the organisation has not. Execution is no longer scarce, so the constraint has landed on human attention — shaping work going in and reviewing work coming out. Every layer waits on a person to read, understand and approve, and that person is re-deriving context that already exists somewhere. Adding agents lengthens the queue in front of that person rather than relieving it.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this vision's outcome and the only party who may accept it.

## Unresolved questions

- Whether a harness-agnostic, tracker-agnostic coordination layer stays adoptable without becoming lowest-common-denominator. Carried as an open assumption.
- Gustafson's objection to the attention-constraint bet is recorded in the De-risk record as unrefuted rather than answered.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Boundary

Includes: the coordination and context layer that lets each organisational layer act on what the surrounding layers decided — declared intent, accepted decisions, delivery state, and the workflows that move work between layers — across engineering and non-engineering layers alike.

Non-goals:

- **Real-time execution state.** That lives in whichever harness or platform runs the agents, not in this layer.
- **Prescribing a model, harness, or runtime.** The platform stays agnostic; a layer that has already chosen keeps its choice.
- **Becoming the tracker.** Organisations keep the trackers they run; the canonical model projects outward one way and never adopts a tracker's hierarchy as its own.
- **Removing human judgement.** Autonomy relocates and concentrates judgement; it does not eliminate it, and a design that optimises the last human out has failed this vision's guardrail rather than achieved its outcome.
- **Raising the altitude of human attention as the mechanism for autonomy.** Autonomy comes from shrinking the reviewed unit and moving detection into machines whose liveness is tested — not from having people survey more at lower resolution.
- **Per-domain vertical products.** This is the layer beneath them.
- **Layers outside product delivery.** Commercial, operational and finance layers are not served by this vision. The ambition of an agentic company is larger than this repository, and claiming those layers here would be a partition this vision cannot deliver.
- **The execution and supervision substrate.** Coding-CLI adapters, remote agent runtime, infrastructure and observability, and the control plane are **depended upon and not owned**. They are delivered in other repositories under the same owner. They are not children of this vision, because this repository does no work on them, and naming them as children would put work in the partition that nothing here will carry.

## Product-vision fields

- **Customer-shaped pitch:** The operating system for an agentic company — coherent workflows and shared context that let every layer act autonomously and still account for itself.
- **The change:** Intent, decisions and delivery state become durable, interconnected context any layer can read, so autonomy at one layer does not require a human to brief the next. Review moves up an altitude instead of scaling with output.
- **The job + struggling moment:** Act autonomously on what the surrounding layers have decided; it bites when work arrives for approval and the approver must re-derive context that already exists, making human attention the queue everything waits in.
- **Who, by circumstance:** An organisation whose models already sustain multi-step work, where the observable limit has become how fast people can shape and review rather than how fast work can be produced.
- **Existing alternatives:** Per-session prompting, tracker hygiene by hand, and tribal memory. They serve one agent adequately and degrade sharply as agent count rises.
- **Narrowest wedge:** One layer — a single repository and the team around it — where work completes without per-unit human gating and the layer above can still answer what happened and why. If autonomy cannot be made accountable in one repository, it cannot be made accountable across a company.
- **Demand evidence:** Not yet established. The maturity-ladder framing is the working hypothesis and is explicitly marked for adopter-persona research in the source material.
- **Open assumptions (tiered):**
  - *must-test-before-shipping:* that the bottleneck is coordination rather than model capability, for the teams this targets.
  - *accept-as-bet:* that harness-agnostic and tracker-agnostic is worth its cost in expressiveness.
  - *will-monitor-post-ship:* whether gate density can fall as a team matures without review quality falling with it.
- **Counter-metrics:** Coordination artifacts that cost more to maintain than the rediscovery they replace; gates that are followed ritually rather than because they catch anything.

## Source

Extracted from two existing artifacts rather than authored fresh:

- [`docs/rfc/0064-ini-001-ai-native-ecosystem.md`](../../rfc/0064-ini-001-ai-native-ecosystem.md) — its Problem, Goals and Non-goals.
- [`docs/product/shaping/product-vision-INI-001.md`](../shaping/product-vision-INI-001.md) — its Headline, Problem and Solution, including the maturity ladder and the four interlocking layers.

Both were shaped 2026-07-18 and predate most of what this repository has since shipped. The de-risk record states which of their claims still hold.

## De-risk record

- **Level kind:** product-vision, so the pack maps the dominant bet to **market-existence** — will anyone want this at all (market desirability) *and* can it be a business (viability). That is categorically distinct from feature-level desirability, and it is tested once here rather than re-litigated per capability beneath.
- **Reversibility triage:** one-way door, and unusually so. The pack catalogue, the three loops, `workspace.toml`, the shaping room and every capability beneath this vision are built on its premise. If the premise is wrong, the platform has no reason to exist — this is not a bet that can be unwound behind a flag. Triage therefore defaults the approach to `validate-first`.
- **Prototype-approach:** `validate-first`. No probe is built; the cheapest thing that can fail is to ask whether the repository already holds evidence bearing on the bet, and to take the answer.

### Riskiest assumption

Of the assumptions this intent carries, one dominates on risk times absence of evidence:

**The bottleneck for the teams this targets is coordination, not model capability.**

Its own source marks it as a working hypothesis awaiting adopter-persona research, and the vision's demand evidence is *absent* rather than weak. If it is wrong the consequence is not a weaker product — it is that the correct strategy for these teams is to wait for better models, and every layer beneath this vision is solving a problem that dissolves on its own.

What would have to be true: teams at the maturity step this targets must experience coordination as their binding constraint, must recognise it as such, and must be unable to resolve it with what they already have.

### Kill condition, predeclared

Declared before any evidence was read, and with three outcomes rather than two, because a market bet that repository evidence cannot reach must be allowed to come back unresolved rather than be forced into a verdict.

- **Killed** if the repository's own adopter-facing research contradicts the hypothesis — if it finds the targeted teams are limited principally by something else (model capability, cost, trust, skills, permission), or that they do not recognise coordination as their problem.
- **Survived** only if that research affirmatively supports the hypothesis with evidence about real adopters — behaviour or stated constraint from people outside this repository, not inference from the repository's own design.
- **Unresolved** if no such research exists, or it exists and does not address the question. In that case the honest output is a `to-validate` hook and no verdict. Desk-grounding is not validation, and an unresolved market bet must not be dressed as a surviving one.

The viability half is declared the same way: **killed** if evidence shows the coordination layer is something teams expect free or build themselves; **survived** only on evidence of willingness to adopt or pay; **unresolved** otherwise.

### The probe

`validate-first`, run 2026-09-18 against the repository's three adopter-facing research documents — [`adopter-persona-brief.md`](../research/adopter-persona-brief.md), [`adopter-persona-comparison-matrix.md`](../research/adopter-persona-comparison-matrix.md), and [`platform-adoption-evaluation-survey.md`](../research/platform-adoption-evaluation-survey.md). The adopter-persona work open-codes six adopter segments across 13 sources and includes a **binding constraint × segment matrix**, which is the question this bet turns on.

Four results:

- **The word "coordination" does not appear once in any of the three documents.** Zero occurrences across the entire adopter-facing corpus, including a matrix built specifically to name each segment's binding constraint.
- **The constraints the research does name all sit upstream of coordination.** Solo engineers: installation friction inside a 15-minute activation window. AI-naive professionals: cognitive load. Enterprise champions: trust and product-maturity signals, 12+ months of production evidence, board-ready proof. FDE clients and governance adopters: preview-confirm friction. The research states these are *not additive* — each segment has exactly one primary binding constraint, and solving several at once is not possible without tracking separation.
- **The single largest measured effect is human, not tooling.** FDE-mediated deployments achieve 60–80% automation; self-service achieves ~20%. The research calls the gap structural rather than marginal, and names the primary variable as whether a human specialist is present during deployment.
- **95% of GenAI pilots fail to produce measurable business value**, which for the enterprise champion is career-consequential and drives the 12-month evidence bar.

Evidence quality, stated plainly: these are secondary and desk-research sources, not participant observation, and the research says so itself. It also records participant observation and practitioner interviews as open known-unknowns.

### Verdict — RETRACTED. The probe measured the wrong thing.

The kill recorded here on 2026-09-18 was **withdrawn the same day as invalid**, on the owner's challenge. The reasoning is kept rather than deleted, because the error is instructive and a future reader must not re-run it.

**The category error.** The hypothesis is about what limits an *organisation* running agentic workflows across its teams — many actors, high interdependence, work flowing between them. The probe measured something else entirely: what stops an *individual adopter* installing this pack set and reaching first value. Installation friction inside a 15-minute activation window is a real finding about product onboarding. It says nothing about whether coordination binds a department running many agents in its second year. Different population, different time horizon, different phenomenon.

**The kill condition was the defect, not the evidence.** It named the adopter-persona corpus as its oracle. That corpus was never designed to answer this question — it open-codes adoption segments, so "coordination" was never a candidate answer and its absence carries no information. A kill condition must name an instrument that could have returned either result. This one could only return one, which makes the verdict an artefact of the instrument rather than a finding about the world.

**What the retraction does not restore.** The assumption is **untested**, not supported. The probe produced no evidence either way, and the original state — a working hypothesis with absent demand evidence — is unchanged.

### The bet, restated by the owner 2026-09-18

The original wording — *the bottleneck is coordination, not model capability* — was too loose to test. The owner's sharper statement:

> **Human attention and thinking time is the bottleneck now.** Agents have removed the execution constraint. What remains is humans shaping items and reviewing items, and the response is to move human attention to more strategic layers rather than reviewing every line as models improve.

This is a different and better claim in three ways. It names *which* resource binds (human attention, not an abstract coordination gap). It names *why now* (execution stopped being the constraint). And it names the expected response (raise the altitude of human attention), which makes it falsifiable — an organisation that tried that and reverted would count against it.

Structurally it is Amdahl's Law applied to an organisation: if agents drive execution cost toward zero, total throughput is bounded by the fraction that stays human. It is also the Theory of Constraints prediction that automating a non-constraint relocates the constraint rather than removing it.

### Kill condition for the restated bet, predeclared

Declared before any evidence was sought. Unlike the retracted probe, the instrument must be able to return either result: the applied literature on what happens when throughput is automated has documented cases of the constraint landing on human decision **and** cases of it landing elsewhere, so both outcomes are reachable.

**Killed** if applied evidence shows any of:

- **Wrong location.** When execution is automated, the constraint reliably lands somewhere other than human attention — on integration, verification, rework from quality loss, or coordination between automated units — rather than on the humans shaping and approving.
- **Reverted response.** Organisations that moved human attention up-altitude, to exception-based or sampled review instead of reviewing every unit, found outcomes degraded enough that they went back to detailed review.
- **Never binds.** Human review effort per unit of output falls fast enough as altitude rises that attention does not become the limit — in which case the constraint is self-resolving and needs no coordination substrate.

**Survived** if applied evidence from several independent domains shows that automating throughput relocates the constraint onto human decision and review, and that the durable response is raising the altitude of human attention with exception handling rather than adding reviewers.

**Unresolved** if the evidence exists only for software-with-AI, which is too young to carry the claim, and nothing from the older automation literature transfers.

### Verdict — the bet splits: constraint survives, mechanism killed

Probe run 2026-09-18 as a desk pass over organisational and operational evidence — aviation flight deck, air traffic control, aircraft certification, radiology screening, content moderation, financial-crime surveillance, code review, statistical quality control, audit and nuclear oversight — plus the queueing literature. Recorded in [the graph-powered SDLC survey](../research/graph-powered-sdlc-survey.md).

**Half one — human attention becomes the binding constraint once execution is automated. SURVIVES, moderate confidence.** Independent domains show it. Radiology screening: an AI reader removed 44% of human reading workload across a 105,934-woman randomised trial, so reading was the binding load. Content moderation: 100% human review was never affordable, and the operating model is built around that. Queueing theory predicts it mechanically — Little's Law caps throughput at the slowest station, and Kingman's formula says a high-variance human decision step suffers the utilisation penalty harder than a machine does.

Three qualifications, all real. It is **not universal**: Google runs ~20,000 changes a workday at a median of one reviewer and under four hours end-to-end, so review need not become the constraint. **Gustafson's objection is unrefuted** — if cheap upstream capacity is spent on *bigger units* rather than *more units*, the human step does not bind; nobody has measured which regime applies here, and it is answerable with our own instrumentation. And applied Theory-of-Constraints evidence naming the post-automation constraint could not be reached in either direction, which is a gap rather than a finding.

**Half two — the durable response is raising the altitude of human attention. KILLED, high confidence, under the predeclared reverted-response clause.** Two documented reversions, both by regulators holding the best data in their domains, both legislated or mandated rather than merely recommended:

- **Aircraft certification.** FAA delegation rose from 28 of 87 tasks in 2013 to 79 of 91 by late 2016, with safety-critical items reclassified downward mid-project. Two hulls were lost. The Aircraft Certification, Safety and Accountability Act of December 2020 legislated the altitude back down — a **non-delegable safety-critical class**, FAA **personnel authority over the delegates**, and **embedded reviewers**.
- **Flight deck.** After automation-induced skill degradation appeared in over 60% of in-scope accidents, FAA SAFO 13002 told operators to **promote manual flying in normal operations**, deliberately foregoing automation's benefit to preserve capability. The AF447 recommendations go further and add a *manual action* to re-engage the flight director.

**Bainbridge pre-refuted the mechanism by name in 1983**, and thirty-four years later the field's own review is titled "Still Unresolved After All These Years":

> "There is therefore no way in which the human operator can check in real-time that the computer is following its rules correctly. One can therefore only expect the operator to monitor the computer's decisions at some meta-level… The human monitor has been given an impossible task."

Her mechanisms compound against altitude-raising. Monitoring capability is produced by the doing that automation removes, so the reviewer degrades. The residual job needs *more* skill and *less* load, not less skill. Succession is the bomb: the first cohort of high-altitude reviewers learned by doing the work, and the second will not exist. And oversight is added load, not removed load — vigilance is high-workload with a measured sensitivity decrement of 0.73 across 42 studies.

Two further findings sharpen where the damage lands. Automation that **analyses** while the human chooses is comparatively cheap in situation awareness; automation that **chooses** while the human approves is where the cost lands — and policy-level oversight sits on the expensive side by construction. And **higher reliability makes oversight worse**: constant-reliability automation produced substantially worse failure detection than variable, while human detection also degrades as defects get rarer. The better execution gets, the faster oversight rots.

### The mechanism that does work, and it is not what we wrote

Every case in the survey that succeeded has the same shape, and it is the opposite of sampling at a higher altitude:

> **The human looks at full detail on a much smaller, better-selected unit, while a machine carries the detection load — and the machine's liveness is deliberately tested.**

- **Radiology.** CAD decorated unchanged human reading and made it *worse* — recall 10.1%→13.2%, AUC 0.919→0.871, invasive cancer detection down 12% across 222,135 women. The AI screening trial that worked **replaced one of two human readers**; the remaining human read at full detail. Same domain, opposite result, and the difference is whether the machine carries real load.
- **Code review.** Not fewer reviewers looking at more. **One** reviewer looking at a 24-line median change, with 110 automated analyzers holding the mechanical floor, explicit directory ownership deciding routing, and per-language readability certification encoding standing judgement **once** instead of re-deriving it every review.
- **Certification.** Not re-reviewing everything: a non-delegable class, personnel authority, embedded reviewers.
- **Audit.** When full-population inspection became cheap, the standard-setter moved *toward* full population and began governing it, rather than defending sampling.

And the warning that binds any exception surface: an FCA peer review found three banks whose automated surveillance detectors were **dead for over three years** — one whose news feed was never switched on — while the firms believed they were covered because other models produced true positives. **A sampled or automated control that emits plausible output is indistinguishable from a working one without deliberate testing.**

### What this changes

The **outcome stands**: autonomy across all layers, with coherent workflows and context as the connective tissue. Nothing here contradicts it.

The **route to it changes**. Autonomy is not bought by moving humans up to survey more at lower resolution. It is bought by shrinking what a human must look at, moving detection into machines whose liveness is tested, and **encoding standing judgement once so it leaves the per-unit path entirely** — which is a decision graph, an ownership and routing structure, and a gate, not a dashboard.

That reframing is unusually kind to this vision's own strategy. Encoding standing judgement once is `CAP-0002 Decision graph`. Explicit ownership and routing is `CAP-0001 Repository work graph`. Tested liveness is the dangling-edge CI gate the survey already ranks third. The strategy was already building the mechanism that survives; the vision was describing the one that does not.

Two design rules the evidence supports directly, and neither is in the vision today. **Give an overseeing human one thing to watch and nothing else to do** — single-task monitoring was efficient and unaffected by automation reliability; complacency is a multi-task-load effect, so handing one person N parallel agent streams engineers the documented failure condition. And **watch the ratchet, not the level** — no single delegation step caused the certification failure; the share crept up over three years, and the countermeasure the evidence endorses is a structurally non-delegable class rather than a periodically-reviewed percentage.

### The lens this bet actually needs

Not agentic prior art. That field is too young to have the evidence, which is why both research passes kept returning "no published evaluation exists" on exactly the questions that matter.

The claim is an **organisational** one: as the number of interacting actors and the interdependence between them rise, coordination cost rises faster than output, and eventually binds. That is not a new question and it is not short of evidence — organisational behaviour, coordination theory, the information-processing view of the firm, and the long literature on how information flows through organisations have studied it for decades against human actors. Agents change the actor count and the tempo; they do not obviously change the mechanism.

So the honest re-test asks whether the coordination-cost curve that literature describes applies when a large share of the actors are agents, and where it starts to bind. That is a question with real prior art behind it, and it is the one this vision is actually making a bet on.

### Validation hook

```
validation_hook:
  assumption: The bottleneck for the teams this targets is coordination, not model capability.
  kill_condition: The repository's own adopter-facing research finds the targeted teams limited principally by something other than coordination.
  activity: to-validate. The 2026-09-18 probe was retracted as invalid, so nothing has been tested. The re-test is a desk pass over organisational
    coordination evidence — coordination cost against actor count and interdependence, the information-processing view of the firm, and how information
    flow degrades as organisations scale — asking whether the mechanism holds when a large share of actors are agents, and where it begins to bind.
    Its kill condition must be set before it runs and must name an instrument capable of returning either result. The viability half needs its own line:
    evidence of willingness to adopt or pay, which no current source provides.
```

## Assumptions

- **The durable response is raising the altitude of human attention.** **Killed 2026-09-18** on two legislated reversions and Bainbridge's 1983 refutation. The mechanism that survives is the opposite: full detail on a smaller unit, machines carrying detection with tested liveness, and standing judgement encoded once so it leaves the per-unit path.
- A harness-agnostic, tracker-agnostic coordination layer is adoptable without becoming lowest-common-denominator. **Untested.**
- **Knowledge surface:** in-repo doc set (`docs/rfc/`, `docs/product/shaping/`). No MCP knowledge tool or internal CLI was present.

**Partially de-risked.** The constraint half survived; the mechanism half is killed, and the outcome and non-goals reflect that. The viability half is unresolved. See the de-risk record.

The bet that human attention is the binding constraint is no longer listed here: it was tested, and the **De-risk record** above owns it, including the retracted first probe, the owner's restatement, and the split verdict that killed the mechanism while the constraint survived.


## Decomposition

The outcome is autonomy across every layer of product delivery, so the partition is by layer plus the connective tissue and the reach mechanism. Four strategies, each with work in this repository, no overlap and no gap.

- [Graph-powered SDLC](STRAT-0001-graph-powered-sdlc.md) — the **model** of work, decisions and delivery that every layer reads and writes.
- [Platform Core](STRAT-0002-platform-core.md) — the **loops** that act on that model, and the packs and shaping room that carry them.
- [Autonomous product-team operating model](STRAT-0003-autonomous-product-team-operating-model.md) — autonomy for the **non-engineering layers**: product, design, experience, research. This is what makes "not engineering alone" true.
- [Trustworthy organisation-owned catalogues](STRAT-0004-trustworthy-org-owned-catalogues.md) — how the model **reaches** an organisation and is trusted once there.

### Decomposition decisions

- **2026-09-18 — only strategies with work in this repository are children.** An earlier partition named eight, adding coding-CLI adapters, remote agent runtime, infrastructure and observability, and a control plane as members delivered elsewhere. They were removed. A child is a commitment this artifact's tree will carry; naming work no one here will do puts a promise in the partition that nothing backs. They are recorded in the non-goals as depended upon and not owned.
- **2026-09-18 — the outcome was scoped to match what the children deliver.** It previously claimed all layers of the organisation, which no partition available here could cover: commercial, operational and finance layers had no strategy and would have had none. Scoping to product delivery keeps the load-bearing claim — that autonomy reaches past engineering into product, design and research — while making the partition honest. The larger company-wide ambition is not abandoned; it is simply not this repository's to promise.
- **2026-09-18 — three overlaps were drawn out rather than left implicit.** Governance records: Platform Core owns **authoring** them, Graph-powered SDLC owns **reading them as constraints**. Harness portability: Platform Core owns the skill surface being harness-agnostic, while per-harness adapters are external. Gates: the risk-calibrated ladder is doctrine owned by the product-team model, and the loops that execute it are Platform Core's.
- **2026-09-18 — an independent intent-mode shaping review drove this shape.** It returned `MALFORMED(children)` across four rounds against successively larger partitions; enlarging the partition was the wrong response, and scoping the outcome to the work that exists was the right one.
