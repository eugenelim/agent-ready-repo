# RFC-0053: the discovery loop — `discovery-lead`, the typed sidecar, and the no-engine coordinator contract (spine prototype-confirmed; D1–D6 extensions specified-in-shape)

- **Status:** Open <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-26
- **Date closed:**
- **Decision weight:** heavy <!-- light | standard | heavy — sets the upstream orchestration contract the whole operating model hangs from, ships a new agent + skill + a versioned sidecar schema, and carries a security/integrity + data-classification surface; explicit Approver sign-off is warranted. -->
- **Related:** [RFC-0048](0048-autonomous-product-team-operating-model.md) (the foundation — this is **child 5**, the coordinator spike→RFC for Decisions 7 + 8; the provisional foundation this drift-aligns back to) · [RFC-0049](0049-the-release-loop-and-company-os.md) (the sibling *downstream* outer loop — `release-lead` + `release-loop`, the same agent-def + skill + harness pattern this RFC establishes upstream; both build on the same RFC-0048 substrate (the sidecar + the gate arc), and this RFC specifies the sidecar schema RFC-0049's release loop would also consume) · [RFC-0051](0051-the-self-coverage-gate.md) (the self-coverage gate — RFC-0051 owns the goal + seam and specifies the full seven-module design-convergence instantiation; `discovery-loop` is that instantiation's **primary home**, carrying its **own** co-scoped copy of all seven modules as its pre-G2 phase, wired here — whereas `work-loop` adopts only the net-new slice) · [RFC-0050](0050-the-experience-pack.md) (the `experience` lens this loop detect-and-degrades on) · [RFC-0041](0041-infra-aware-work-loop.md) + ADR-0031 (the *doctrine + reference library + reuse, no engine/no new reviewer* precedent the framing rests on) · RFC-0025 (`work-loop` light/full + the iteration cap this loop's outer cap mirrors) · RFC-0040 (the three-tier layout resolution the sidecar paths obey) · RFC-0019 (`receive-brief` — the brief→spec join at G3; its coverage lint child-4's traceability lint generalizes) · [ADR-0022](../adr/0022-value-stream-meta-repo-cross-component-layer.md) (the cross-repo reference-by-version mechanism the traceability slot reuses) · [`docs/specs/traceability-lint/`](../specs/traceability-lint/spec.md) (child-4 — the lint that consumes the traceability slot) · promoted research + the empirical prototype in [`0053-notes/`](0053-notes/); [`0048-notes/09`](0048-notes/09-gap-resolutions.md) (the paper resolutions this spike confirms) and [`0048-notes/02`](0048-notes/02-worked-example-flow-trace.md) (the worked example it was run against)

## Reviewer brief

- **The gap this fills.** Agents already build software well *once someone has decided what to build*. This RFC defines the missing **upstream** half: turning a raw product idea into a ratified, build-ready brief — researching the domain, mapping the user journey, sketching the architecture, and pausing at a few human sign-off points.
- **What "the coordinator contract" means (the core term).** The **coordinator** is the thing that runs that process end-to-end: an AI **"discovery lead"** that decides what to do next, when to pause for a human, and when it's done. The **contract** is the **precise written rulebook for how it behaves** — what working state it keeps, when it stops for sign-off, how it recovers when a human says "no," when it gives up, and who does the work — written so that *any* harness can run it the same way, not tied to one vendor's tool. **This RFC *is* that rulebook**, confirmed by a working prototype; the six decisions below are its clauses.
- **What "no engine / no new software to run" means — and why it's a hard constraint.** "No engine" = we ship only **text the AI reads** (an agent definition, a skill, file templates), **not** a running service — no scheduler, message bus, or orchestration daemon. It matters two ways. *Philosophy:* the catalogue ships *ways of working* any harness can run, not infrastructure we would have to host, secure, and maintain (CHARTER Principle 3) — and the same instructions then run unchanged on whatever tool an adopter already uses. *Evidence:* multi-agent systems built *as* coordinator engines (a "manager" agent routing other agents) measurably thrash — a 2025 study across 7 frameworks found **41–86% failure rates** — whereas a single coordinator reasoning over shared files does not. So "no engine" is both a charter rule and a reliability choice. (See § Evidence & prior art; MAST, arXiv:2503.13657 — fuller references to follow.)
- **What we're deciding.** Whether to adopt that process as a defined contract — the six decisions **D1–D6** below — confirmed by a working prototype.
- **Recommendation:** accept all six. D1–D5 are the core loop (the prototype confirmed its **spine** — the gate + ripple + cascade + connectedness lint; the multi-verdict steer space, recursion, resume, and bounds added this session are confirmed in **shape**, modelled-not-yet-run); **D6** adds an up-front "explore several product directions before committing" step and a rule that the loop's output is a *hypothesis to validate with real customers*, not a finished answer. D6 wraps D1–D5 without changing them and adds no new software. (Promoted from the skill-coverage pressure test + the dogfood runs in [note 11](0053-notes/11-second-example-divergence-and-provisional-spine.md) / [note 12](0053-notes/12-third-example-science-hardware-divergence.md).)
- **What changes if we accept.** A new `discovery-lead` agent and `discovery-loop` skill are added to the `product-engineering` pack. They keep their working state in **a few plain, typed files** — a shared discovery-workspace the loop reasons over (the design-so-far, the open questions, how things link together, a decision log) — carried with the skill, not in the shared `core` pack. Other tools (the traceability lint, `work-loop`, the release loop) only *read* those files. Nothing new runs as a service.
- **What's at stake.** This sets the contract the whole upstream operating model depends on, and it handles sensitive product data plus human sign-off — so it's **costly to reverse**. It's proven on a few worked examples, not yet at scale (named honestly in Risks). **Adoption risk is real too** — there are many new concepts here — so the implementing spec **gates on a full user-guide set** (Diátaxis explanation/how-to/tutorial/reference); building the pack is not enough (see Follow-on artifacts).
- **What to check.** (1) Is it genuinely "just instructions" — no hidden need for a new engine? (2) Are the safety + data rules strong enough — can the loop forge a human's approval, tamper with the decision log, or run away without stopping?
- **Out of scope.** Building the harness that runs it; putting the file format in the shared `core` pack (it's deliberately carried with the skill so it runs anywhere, even outside a code repo); a full at-scale validation (owed later).

## The ask

*In plain terms: adopt the discovery-lead's rulebook (Decisions 1–6), ship it as instruction files
rather than software, and trust it because a hand-run prototype already walked the loop's **spine**
with no engine — the D1–D6 extensions added since (recursion, the verdict set, resume, the bounds, the
divergence/validation scaffold) are confirmed in **shape**, modelled-not-yet-run.*

**Recommendation (BLUF).** Adopt the **coordinator contract** the RFC-0048 Decision-7 spike
was meant to validate — and **ship it the way RFC-0041/0049 ship their loops: a
`discovery-lead` agent definition + a `discovery-loop` skill (content, like `implementer`)
+ the typed sidecar *schema* as a carried contract in the producing skill — no new runtime engine.** A timeboxed
**empirical prototype** ([`0053-notes/`](0053-notes/)) ran the loop against the worked
example ([`0048-notes/02`](0048-notes/02-worked-example-flow-trace.md)) on the form
`omnigent` stores (worktree files). On that **one worked example, walked once by a single
operator** (not replicated — the honest limit, flagged in the spike's Threats), every
transition — altitude descent, the answer-each-other ripple, gate rejection/recovery with
cascade-invalidation, saturation, and the outer cap *modelled* (it converged early and the
stall path was not hit live) — was performed by **one reasoning context editing four plain
files**, with a single ~60-line *lint* (not a coordinator) as the only executable. That
lint is the **reproducible** artifact: it flagged the injected defects pre-recovery and
reported converged after. The framing the prototype supports — *no engine is needed* — thus
moves from RFC-0048's stated hypothesis to a demonstration on one example plus a
reproducible connectedness check, which is what closes (with the residual scale risk named)
the one assumption RFC-0048's spike section left open for the coordinator.

**Why now.** *In plain terms: RFC-0048 designed the coordinator on paper but deliberately built
nothing, leaving one open question — can it really run with no engine? This RFC answers it by running
a prototype and writing the rulebook down. (Structured below as Situation · Complication · Question.)*

*Situation:* RFC-0048 decided the operating model and **resolved the
coordinator's design blockers on paper** ([`0048-notes/09`](0048-notes/09-gap-resolutions.md):
O11 rejection/recovery, O12 outer cap, A1 checkpoint/resume, A2 decision schema, A3 team
composition, O5 live lenses, O6 saturation), then deliberately *built nothing* — it
authorized a **spike, not a build** (D7), because the coordinator's Principle-3 fit was the
initiative's riskiest assumption and the only one demonstrated *for RFC-0048's D1–D6 but merely
hypothesized for the coordinator*. *Complication:* a paper resolution is not a confirmation;
RFC-0048 is explicit that the spike's job is to **confirm the resolutions empirically via a
prototype on `omnigent`** — and until that runs, "the coordinator is doctrine, not an
engine" is an assertion, and the contract an adopter or a bespoke harness must implement is
unspecified. *Question:* does the convergence loop + its typed state survive contact with the
worked example as engine-free content, and what exactly is the harness-neutral contract?

**Decisions requested.**

Each is decided by accepting this RFC. *(Terms used: an **agent**/**skill** are markdown
instruction files an AI reads, not running software; the **discovery-workspace** (technical name: the
*sidecar*) is the few plain typed files the loop reasons over — durable, not throwaway; a **lens** is the loop wearing one discipline's hat — research, product, UX,
architecture, safety.)*

| ID | The decision, in plain terms | Recommended | Why it's the call |
| --- | --- | --- | --- |
| **D1** | Ship the discovery process as **instructions, not software** — add an AI "discovery lead" + a "discovery-loop" playbook to the product pack; an existing harness runs them, with **no new engine, scheduler, or service**. | **Adopt** | The prototype ran the whole loop as edits to plain files + one small checker — nothing needed a custom engine, and this is the backbone everything upstream sits on. |
| **D2** | Keep the loop's working state in **a few plain, typed files** (the design-so-far, the open questions, how everything links together, a decision log), carried *with the skill* rather than in the shared `core` pack. | **Adopt** | That typed state is what lets a tiny checker verify "the design actually holds together," and carrying it with the skill keeps the loop usable outside a code repo. |
| **D3** | Define **how the loop pauses for human sign-off and handles the verdict** — it pauses at sign-off points and resumes after the answer, where the answer is a **typed set** (approve / approve-with-constraint / redirect / explore-alternatives / park / abandon / extend-override), and any answer that changes things **shows its blast radius first** and is recorded before the loop proceeds. | **Adopt** | The prototype did this as simple file edits; tracking what-depends-on-what scopes the blast radius, and a typed verdict lets the human steer (not just yes/no) without the loop jumping ahead. |
| **D4** | Give the loop **bounds** (round cap + cost budget, per-initiative *and* per-node), where hitting any bound **pauses and asks** — extend / narrow / park / abandon — never a silent stop or silent continue; plus a concentration + depth/breadth guard so one deep sub-idea can't drain the budget. | **Adopt** (a round cap, a budget, and a concentration fraction — all spec-tunable; defaults in D4) | A safety valve that can neither churn forever *nor* dead-end; pausing for confirm/override keeps the human in control of spend and scope (shape **C**, note 13). |
| **D5** | Let **one** discovery lead run it, scaling to **a small team of specialist "lenses"** only when needed — **inside the loop** they coordinate through the shared discovery-workspace, not free-form chat-to-consensus. (*Across* loops / at company-OS scale, coordination is via durable contract artifacts and structured agent protocols / an agentic mesh — the harness's layer; this contract ships the **stable-id substrate** a mesh consumes — not a full mesh-readiness claim (a mesh must still add capability discovery) — not the mesh.) | **Adopt** | Free-form chat-to-consensus is the multi-agent failure mode; a blackboard is the right *structured* pattern for interdependent convergence — and structured protocols (A2A/ACP) handle scale (note 14). |
| **D6** | **Explore several product directions before narrowing, and label the result as a hypothesis to validate** — first generate a handful of candidate product shapes and pick one, then run the loop, then hand off a brief that flags exactly what still needs real-customer validation. | **Adopt** (new this round) | Dogfood runs showed the loop otherwise locks onto the first idea and misses better ones — and a "finished" design is still a coherent guess until real users test it. Adds **two thin new skills** (`explore-options`, `plan-validation`) but no new engine, agent, or reviewer. |

## Problem & goals

**In plain terms.** RFC-0048 worked out the design on paper but didn't *prove* it or write it down
precisely enough to build against. This RFC does both: runs the prototype, and specifies the rulebook.

**Diagnosis.** RFC-0048 did the hard *design* work for the coordinator and recorded it
honestly as **resolved-on-paper** (note 09). What it could not do — by its own choice to
spike rather than build — is **confirm those resolutions empirically** and **specify the
contract** that survives. Two concrete gaps remain after RFC-0048:

1. **The no-engine claim for the coordinator was a hypothesis, not a demonstration.**
   RFC-0048's Evidence section is explicit: the no-engine verdict is *demonstrated for
   RFC-0048's D1–D6* (they add only markdown, a reference library, a typed artifact, and a lint) but
   for the **coordinator** it is *a hypothesis* — "`loop-cohort` covers none of O1/O2/O3/O5/O7
   today, so the doctrine-not-engine fit is exactly what the Decision-7 spike must confirm."
   Nothing had been run.
2. **The contract was unspecified.** "A typed sidecar", "rejection/recovery transitions",
   "an outer cap", "checkpoint/resume" name *what* must exist; an adopter — or a future
   bespoke harness — needs the *schema and the transitions* written down, harness-neutrally,
   to implement against. Note 09 resolved the design; it did not write the contract.

This RFC closes both: it **runs the prototype** (Decision 1; [`0053-notes/`](0053-notes/))
and **writes the contract** (Decisions 2–5) — the spine the prototype walked, plus the design
extensions added this session (the verdict set, recursion, resume, the bound-pause) confirmed in
*shape*, modelled-not-yet-run.

**Goals.**
- **Confirm the no-engine framing for the coordinator empirically**, against the worked
  example, on the form the reference harness stores — turning RFC-0048's hypothesis into a
  result.
- **Specify the harness-neutral contract**: the sidecar schema, the gate state machine, the
  outer cap, the supervisor topology — concrete enough that an adopter or a bespoke harness
  implements it without re-deriving it.
- Ship as the **RFC-0041 idiom** — doctrine + an agent def + a skill + a schema, with the
  design-time lens roster RFC-0048's authoritative roster table fixes (its own
  `discovery-threat-reviewer` / `discovery-reliability-reviewer`, not `work-loop`'s code
  reviewers) — so the capability is a *way of working*, not a runtime (CHARTER Principle 3).
- Keep `discovery-loop` **useful at the floor** (product-only discovery with just
  `product-engineering` + `core`) and **progressively enhanced** as lens packs install.

**Non-goals** (could-have-been goals, deliberately dropped).
- *A new orchestration runtime / engine / daemon / service.* The thing the spike was
  designed to prove unnecessary — and did (Decision 1; CHARTER Principle 3; RFC-0048 Option
  C).
- *Building or forking the harness.* `omnigent` exists and is the reference runtime; we
  ship the contract it (or a successor) enforces, not the harness (RFC-0048 non-goal;
  RFC-0041 P4 harness-neutrality).
- *The `experience`, `architect`, and `research` **lens skills themselves.*** Those are
  RFC-0050 (child-1) and reused packs; this RFC wires them as *optional detect-and-degrade
  lenses*, it does not author them. (The security/compliance and reliability floors are **not**
  in this optional set — they are carried by `product-engineering`'s **required** discovery
  reviewers (`discovery-threat-reviewer` / `discovery-reliability-reviewer`, required at G2 per
  RFC-0048's roster table) and degrade only in *depth*, never to nothing.)
- *The traceability lint.* Child-4 (`docs/specs/traceability-lint/`) builds the lint; this
  RFC defines the **traceability slot** the lint reads and the **cascade-invalidation**
  transition that walks its edges. The spike's `check_sidecar.py` is a *demonstrator*, not
  the shipped lint.
- *The self-coverage gate's modules.* RFC-0051 (child-3) owns the self-coverage **goal + seam**
  and specifies the **full seven-module design-convergence instantiation**. **`discovery-loop` is
  that instantiation's primary home** — this RFC names it as `discovery-loop`'s pre-G2 phase,
  carrying its **own** co-scoped copy of all seven modules in `product-engineering`, right-sized by
  this loop's own progressive mode. This is the altitude the battery is built for: a design artifact
  is being converged and myopic-greedy commitment is the live risk. (Per RFC-0051's reframe,
  `work-loop` does **not** carry the full seven — most of the gate already lives in `work-loop`, so
  it adopts only the net-new slice; the release loop realizes the same goal through a deploy
  composite per RFC-0049. Each loop conforms to the same cross-loop seam with a **loop-appropriate
  share**.)
- *The downstream / deploy loop.* `work-loop` (G3–G5 build) is unchanged; the
  release/deploy outer loop is RFC-0049's `release-lead`. This RFC is the **upstream**
  (G0–G2) coordinator only; the two loops hand off at G3 and must not be conflated.
- *Cross-initiative portfolio statefulness.* One `discovery-loop` run converges one initiative to one
  decision brief = one backlog (note 08) — but **recursively inside**: a sub-idea (e.g. recipe
  integration) can spawn its own divergence → convergence → validation sub-walk as a node on the same
  blackboard (per-node status + a sub-idea index — see the Decision 1 recursion pressure test). What
  stays out of scope is the **portfolio/concurrency layer** — scheduling and resuming *many*
  initiatives or long-parked threads across sessions — which is the harness's (loop-cohort / omnigent's
  documented gap), not this contract's.

## Proposal

Cascaded under the requested decisions. The detail and the worked artifacts live in
[`0053-notes/`](0053-notes/); this section states the contract.

### What is looped to convergence — and how it parallels `work-loop`

`work-loop` is legible because it has a running referent: *plan → execute → self-review → fix,
looping until tests + gates are green and adversarial review is clean.* The artifact converging is
the **diff**; the verifier is **executable** (tests); "fix" means make a failing test pass.

`discovery-loop` runs **one altitude up, before any code exists**, so it cannot loop against tests.
What it loops to convergence is **the blackboard itself** — the whole web of typed slots (Decision 2:
the intents, domain-framing, scope-boundary, journey, blueprint, screens, architecture, contracts,
plus the open-questions / traceability / decision-log). The blackboard *is* the
product-as-designed-so-far, held as one connected graph. Because there is no test oracle upstream,
"converged" is the three-part **saturation** condition O6 fixes
([`0048-notes/09`](0048-notes/09-gap-resolutions.md)) — all **non-executable** — which is exactly
*why* this contract ships a connectedness lint + human consent gates (they substitute for the tests a
build loop would have); the **self-coverage gate runs as the pre-G2 phase that must complete *before*
this check is run**, not as a member of the converged-means set:

| | `work-loop` (downstream) | `discovery-loop` (this RFC) |
| --- | --- | --- |
| Artifact converging | the diff | the **blackboard** (the whole design graph) |
| Verifier | tests + lint/typecheck + adversarial review | **connectedness lint** (traceability + open-questions) + **human consent gates**, with the **self-coverage gate as the pre-G2 phase** that gates entry to the check |
| "Converged" means (O6) | gates green, review clean | (1) open-questions queue **empty** · (2) traceability graph **fully connected** root→leaf, no orphans *(reachability is enforced mechanically only once child-4's lint ships its root→leaf pass; the current demonstrator checks edge **presence** only, so until then (2) rests on presence + the human's eye)* · (3) **saturation** — a full pass invalidates no slot |
| One iteration (a *round*) | edit code → run gates → fix | run the next **lens** → it writes slots + raises open-questions → route each to the discipline that answers it → that lens edits its slot → if the edit breaks a downstream slot, **cascade-invalidate along traceability edges** + re-run only the affected lenses → re-check the three conditions |
| "Fix" means | make a failing test pass | **answer an open question** or **close an orphan edge** |
| Bound | iteration cap | **outer round cap + cost budget** (Decision 4); on cap-with-unconverged → stall record + surface to the human |

The **answer-each-other ripple** (O5; Decision 3) is the engine of a round: a lens raising a question
forces another lens to edit, until the ripples die out (saturation) and nothing dangles
(connectedness). The consent gates (G0/G1.5/G2) are the *value/scope* verifier the lint cannot be —
they decide what a connectedness check never can (is this the right bet, is it in appetite, who
accepts this irreversible risk). This is the single frame the five core-loop decisions (D1–D5) below
instantiate (Decision 6 wraps them, unchanged):
**Decision 2** is the typed state that makes conditions (1)–(2) checkable; **Decision 3** is how a
round advances and recovers; **Decision 4** is the bound; **Decision 5** is who runs the lenses.

**Converged is not validated — the spine is provisional by construction.** The three conditions
verify *internal coherence*: the design hangs together, nothing dangles, coverage passes. They
**cannot** verify *external truth* — whether the bet is right, whether the domain framing matches how
real people actually behave, whether the altitude is the one customers will pay for. Those are
knowable only through **real-world activities desk-grounding cannot substitute for**: customer
interviews, contextual observation, usability tests, a live pilot (the primary-research gap the
§ Skill-coverage pressure test names — the agent can *scaffold* an interview guide and *synthesize*
transcripts, but a human runs the sessions, and neither the agent nor the human knows the full space
without them). So `discovery-loop` emits a **provisional spine, not a finished answer**: the decision
brief is a *connected hypothesis* whose load-bearing assumptions each carry a **validation hook** —
the `de-risk-intent` kill condition **plus the real-world activity that would confirm or enrich it**
— turning the brief's assumption ledger into a validation plan, and stating plainly that
desk-grounding ≠ validation. This is the discovery analogue of `work-loop` shipping behind a feature
flag: the loop produces the thing to *try*; reality is the verifier the loop structurally lacks.
Where no referent exists at all (a value/scope call, an unobserved customer behavior) the loop
**surfaces** rather than asserts; where a referent exists but only real users can confirm the agent's
read of it, the loop **marks a validation hook** rather than claiming the question closed. The
exploratory phase (Decision 6) generates the *candidate* spines; this principle governs how the
*chosen* spine is emitted — labelled by what is grounded, what is surfaced, and what awaits the
world.

### Decision 1 — the no-engine coordinator contract (the shape, confirmed)

**In plain terms.** The discovery lead and its playbook are just instruction files added to the
product pack — the same shape as the existing `implementer` agent. Shipping instructions is not
shipping software; the harness an adopter already runs executes them. The prototype proved the loop
needs no custom engine.

`discovery-lead` ships as an **agent definition** and `discovery-loop` as a **skill**, both
in `product-engineering` (an opt-in product capability — `discovery-loop` is
product-discipline-specific, so it ships in the product pack an adopter chooses, not the
universal `core`; the *sidecar schema* it carries lives in the `discovery-loop` skill, not `core`). This is precisely the
`implementer`-shape precedent: shipping an agent def + a loop skill is shipping **content**,
not a runtime — what Principle 3 forbids is the harness, which we do not ship.

`discovery-lead` is the human-facing **upstream supervisor**, a *peer* of `work-loop`'s
supervisor and `implementer`. It runs `discovery-loop` (intents → frame-domain →
blackboard convergence → decision brief at consent gates → emits briefs/specs), holds the
blackboard in **one reasoning context**, fans out only to disjoint workers, and talks to the
human at the consent gates. It is **not** `work-loop`'s supervisor: `work-loop` supervises
the *downstream* spec→build loop; `discovery-lead` supervises the *upstream* vision→brief
loop; they **hand off at G3**.

*What the prototype confirmed.* The riskiest assumption — that orchestrating the loop needs
a runtime engine — is **refuted**. Walking the worked example G0→G2 as one context, with the
two named failure modes (over-scope; an unbacked security-sensitive screen) deliberately
injected, every transition was a file edit plus, at most, a lint. See Evidence and
[`0053-notes/01-spike-report.md`](0053-notes/01-spike-report.md).

**Pressure test — does recursion need a state machine?** Real product work is *recursive*: a
top-level idea ("household EA") contains sub-ideas ("add recipe integration"), and each sub-idea can
warrant its **own** divergence → convergence → validation walk — not just the top category. (The
opportunity-solution tree is recursive by construction — opportunities break into sub-opportunities
into experiments; Torres 2021.) Does that nesting force a runtime state-machine engine, threatening
the no-engine claim? **No — research says it *strengthens* it.** The proven pattern for recursive
decomposition is **Hierarchical-Task-Network planning over a blackboard**: a *plan tree* held as
data, walked depth-first by a **single controller** that decomposes the next node and updates state
on the blackboard (arXiv:2508.12683; HTN literature) — which is exactly `discovery-lead` (controller)
walking a tree of `intent` slots. The "state machine" is **status fields per node**
(`draft → diverging → converging → ratified | stale`) + the decision log — *data the controller
reads*, not an executed engine. The opposite choice — an explicit **nested/hierarchical finite-state
machine** — is precisely what *fails* to scale: HFSMs "shift the modularity problem to inner layers"
and adding/removing states is hard (arXiv:2405.16137), which is why robotics moved to behaviour-trees
/ data-driven control. So recursion is handled with **no new engine**: the blackboard's `intent`
slots are recursive (a node may carry its own divergence/convergence sub-slots), and one controller
descends them under the same gate ladder + outer cap. What recursion *does* add is **data, not
runtime**: per-node status + a lightweight **sub-idea index** (which sub-walks are open / parked /
done) so "recipe integration" is a first-class, resumable node. That data is **not left implicit**:
the `discovery-loop` skill ships a **plan-tree template** (a carried *asset* — the recursive
intent-node scaffold with its status lifecycle + the sub-idea index, Decision 2) the controller
**instantiates and fills in** per initiative. That is what makes "HTN-over-blackboard, no engine"
concrete rather than hand-wavy — there is a defined, lint-checkable structure to *fill*, not a
planner to *run*. **Honest risk:** what the *controller* still does in-context — choose the next node,
account spend per branch, decide descend-vs-surface — is itself a form of scheduling, and the spike's
single solo example does not evidence it **at depth**; so the no-engine win is a **defensible bet on a
shallow tree**, gated conservatively by D4's depth/breadth bounds until a recursive walk is actually
run (named in Risks). **Scheduling many concurrent or
long-parked threads, and resuming them across sessions, stays the harness's job** — the same division
as `loop-cohort` scheduling `work-loop` tasks (omnigent's documented gap), not this contract's. This
refines the "one run = one brief" framing in Non-goals: *one initiative is recursive **inside**; the
portfolio **across** initiatives is the harness's.* (Full research — OST recursion · HTN-over-blackboard
· behavior-trees-vs-FSM — and the resource-management/budget analysis are in
[note 13](0053-notes/13-recursion-and-resource-management-research.md).)

### Decision 2 — the typed sidecar schema (carried contract in the producing skill)

**In plain terms.** The loop keeps its work in a few plain, typed files — the shared *discovery-workspace*:
what's been designed so far, the open questions, how everything links together, and a log of
decisions. The file *format* travels with the skill (so the loop works even outside a code repo);
other tools (the traceability lint, `work-loop`, the release loop) just *read* those files. ("Sidecar"
is just the name for this set of files alongside the work.)

> **Revised per RFC-0048 § Amendments 2026-06-26 (scope-decoupling).** This decision
> originally shipped the schema as **`core` doctrine**. Because `discovery-loop`'s owning
> pack `product-engineering` is user-scope and must run portably (Obsidian vault / non-repo),
> the schema *definition* is now a `references/` file **carried in the `discovery-loop`
> skill**, not single-sourced in repo-scope `core`. There is no shared cross-pack layer (the
> skills spec has none): downstream consumers — the traceability lint, `work-loop`, the
> release loop — **read the produced `_state/` instances by convention + a `schema_version`
> stamp**, they do not import the definition. "Versioned contract" = the instances carry
> `schema_version` and consumers check compatibility. The slot field-set below is unchanged.

The typed state both loops share, its *definition* carried in the producing `discovery-loop`
skill (harness-neutral); the *store* is the harness's (omnigent's git-worktree). The slots,
with their schemas as the prototype instantiated them ([`0053-notes/spike/`](0053-notes/spike/)):

- **blackboard** — the typed artifact slots (= the artifact inventory, note 04), each
  `{id, type, lens, status ∈ draft|proposed|ratified|stale|rejected, version, produced_by,
  path?, round_last_touched, parent_id?}` — the optional `parent_id` is what makes the
  `intent` slots **nest into a recursive tree** (Decision 1's recursion pressure test) — plus a
  `meta` block carrying the round counter, the cost budget, the gate, and the saturation state.
- **open-questions** — the queue lenses answer each other through:
  `{id, raised-by, target-discipline, question, status ∈ open|routed|resolved|surfaced,
  resolution, round}`.
- **traceability** — the `outcome→…→component` edge set the lint checks (orphan = defect):
  typed `nodes` (each with a `kind` and a `backed_by ∈ file|container|ladder` — the child-4
  reconciliation that four chain rungs are intent-ladder rungs or journey/blueprint-embedded
  entries, not files) and `edges`, with a `root` and `leaf_kind`. Node ids are stable,
  location-independent markers (slug / `contract@version` / Backstage `kind:namespace/name`),
  so the chain crosses repo boundaries by convention not path (the ADR-0022 reuse RFC-0048's
  amendment already recorded).
- **decision-log** — `{ts, gate, decision, ratified-by ∈ human|discovery-lead,
  reversibility-class, rationale}` (canonical field order, used in the body and the spike
  artifacts alike); a **decision record** that becomes the audit trail the high-stakes /
  regulated case needs (RFC-0048 D1 stakes-density) **only with the integrity properties the
  implementing spec must carry** — append-only, an attested ratifier (a `human` row the
  controller cannot forge), tamper-evidence, and a trusted timestamp (see § Security &
  integrity contract). As a plain mutable file it is a record, not yet an audit trail; the
  contract names the gap rather than implying the schema closes it.
- **plan-tree template** (a carried *asset*, not just a field-list) — the **instantiable scaffold**
  for the recursive intent tree (Decision 1): a node = an `intent` slot + `parent_id` (so the tree
  nests) + a per-node **status lifecycle** (`draft → diverging → converging → ratified | stale`),
  plus a **sub-idea index** listing the open / parked / done sub-walks. It also carries the
  **Decision 6** shapes: at a divergence point a node holds a **candidate set** (N sibling candidate
  shapes under a `diverging` parent) + a **selection** that promotes one to `converging` while
  **retaining the not-chosen as `rejected` / `parked` with rationale** — not deleted, so they stay
  revivable (D3 persistence + `decision-archaeology`); and each node (or its assumptions) carries a
  **validation status + hook** (`hypothesis → validating → validated | refuted`, with the
  kill-condition + the real-world activity), so *converged ≠ validated* is a **structural property of
  the tree** — and a resumed node knows what is still unvalidated. `discovery-lead` copies this
  template to start an initiative and fills it in as the loop runs. It is what makes the
  HTN-over-blackboard recursion a *concrete artifact the controller fills and the traceability lint
  walks* — **no planner engine**; the template is the mechanism. (Distinct from the field-list
  *schema* above: the schema types each slot; the template is the starter tree the controller
  instantiates. The implementing spec fixes the exact file shape; that a template is **shipped** is
  decided here.)

*Three status namespaces, not one drifting enum.* The statuses above live on **distinct fields** (the
implementing spec partitions them): a **slot status** (`draft|proposed|ratified|stale|rejected`); the
plan-tree **node lifecycle** (`draft→diverging→converging→ratified|stale`, plus `parked`/`abandoned`)
and its **validation status** (`hypothesis→validating→validated|refuted`); and a **meta gate-state**
(`awaiting-human` / `paused-at-bound` / `stalled-at-cap`). They are not a single set, and a single
verdict transition typically writes across more than one (e.g. `abandon` sets a node `abandoned` *and*
its slots `stale`): the **per-verdict cross-namespace write-set is an implementing-spec table** — the
RFC fixes the partition, the spec fixes the writes.

The sidecar is the **connectedness verifier**: the prototype's `check_sidecar.py`
(child-4's lint shape) read the traceability + open-questions slots and reported orphans
pre-recovery and CONVERGED after — connectedness is checkable in ~60 lines, no engine
(Decision 2's load-bearing empirical claim). Paths obey RFC-0040's three tiers; each
producing skill creates its dir lazily on first write.

*Checkpointing / mid-session commits.* The **discovery-workspace** is the loop's **working surface, not an
ephemeral one** — it is durably checkpointed, not thrown away (which is why it is *not* called a
"scratchpad"). The state must be **durably
checkpointed at each round and each consent gate** (not per keystroke) — that is what makes the loop resumable (D3 checkpoint/resume,
D1's resumable recursive nodes) and crash-recoverable, and it is what turns the **decision-log into a
real audit trail**: a commit history is naturally append-only, hash-chained, timestamped, and
attributable — exactly the integrity properties the § Security & integrity contract requires. Two
guardrails: (1) checkpoints go to the **harness's own store / branch** (omnigent's git-worktree),
**never the product repo's main line**; (2) they are subject to the **data-classification + redaction**
controls (a `sensitive`/`regulated` fact is not committed verbatim to a shared/remote store), and the
state branch must be **protected against history rewrite** (the add-only assertion in the security
contract) or the "audit trail" is repudiable. The exact commit *cadence and location* are the
harness's to implement (the store is the harness's); the **requirement** — durable per-round/per-gate
checkpoint, on the harness store not main, under the data controls — is the contract's.

*Cardinality & file layout.* **One plan-tree per initiative — not a single master tree.** An
initiative (one top-level idea) has one recursive plan-tree whose **sub-ideas are nodes** (Decision 1,
via `parent_id`), so "add recipe integration" is a *node*, not a second tree. The repo therefore holds
a **forest — one committed tree per initiative — not** one monolithic tree the loop walks (which would
re-create the "one big coupled state" anti-pattern and collide with the harness-owns-concurrency
line). Initiatives that relate **cross-link by stable ids** (slug / `contract@version` / Backstage
`kind:namespace/name` — the ADR-0022 convention the traceability slot already uses), never by sharing
a tree. **Layout** (paths resolved by RFC-0040's three tiers — an adopter `[discovery]` layout key,
else a `.context/discovery/` default, else elicited; dirs created lazily on first write): **one
directory per initiative**, `<discovery-root>/<initiative-slug>/` (repo mode: `docs/discovery/<slug>/`,
the worked example's home; DRIFT-C owns the layout-key reconciliation), with a **`_state/` subdir** for
the working sidecar (Tier 1: `plan-tree`, `blackboard`, `open-questions`, `traceability`,
`decision-log`, `meta`) and the **committed durable artifacts** beside it (Tier 2: `domain-framing`,
`scope-boundary`, `journey-map`, `service-blueprint`, `screens/`, `decision-brief`, `backlog` — the
parked/ordered sub-ideas). A **portfolio index across initiatives** is **not** a contract file — it is
the harness's (concurrency/scheduling) or an adopter roadmap. Exact filenames/extensions are an
implementing-spec detail; the conventions decided here are *one tree per initiative*, the
*per-initiative directory* under the RFC-0040 discovery root, the *`_state/` working vs
committed-durable split*, lazy creation, and *stable-id cross-linking instead of a master tree*.

*Schema home.* The schema *definition* ships as a **`references/` file carried in the
producing `discovery-loop` skill** (`product-engineering`, user scope) — the
`security-checklists/references/` reference shape, **not** a self-discovered skill and **not**
a repo-scope `core` doctrine file. There is **no shared cross-pack schema layer**: downstream
consumers — child-4's traceability lint, RFC-0049's release loop, and `work-loop` — **do not
import the definition**; they read the produced `_state/` instances by convention (the slot
field-names) and check `schema_version` compatibility. The exact file layout is a spec-time
detail; that the home is the carried `discovery-loop` reference (not duplicated prose in
`work-loop`, not a `core` doctrine file, not a skill an agent must choose to load) is decided
here, per RFC-0048 § Amendments 2026-06-26.

*Ownership (one owner; many writers and readers of the instances).*

- **Owner — `discovery-loop` (the skill).** It carries **both** the schema *definition*
  (`references/`) **and** the plan-tree *template* (`assets/`) — the **single source of truth**.
  There is no shared `core` or cross-pack copy.
- **Driver — `discovery-lead` (the agent).** It *instantiates and fills* the discovery-workspace (copies the
  template, writes/promotes slots) by **running `discovery-loop`** — it uses the asset, it does not
  own a second copy.
- **Other skills need the *instances*, not the definition — by convention + `schema_version`:**
  - *Writers:* the lens skills (`map-customer-journey`, `blueprint-service`, `map-screen-flow`,
    `frame-domain`, …) and the D6 skills (`explore-options` writes `intent`-variant slots,
    `plan-validation` writes the validation-plan slot) **propose** slots that conform to the schema;
    only the controller promotes/ratifies (D5 lens-write integrity). They are *conformers*, not
    owners.
  - *Readers:* child-4's traceability lint, `work-loop`, the release loop, and the self-coverage
    gate read the produced `_state/` instances by the slot field-names + the `schema_version` stamp.
- **Self-contained vs shared.** The **asset (definition + template) is self-contained in one skill**;
  the **produced instances are the shared interface** many skills and tools touch — deliberately
  decoupled by the "read instances by convention, never import the definition" rule (RFC-0048
  scope-decoupling), so there is one source of truth without cross-pack import coupling.

*How writers stay aware, and how drift is prevented.* The would-be writers are **not all in one
pack** — the lens skills span `experience` / `architect` / `contracts` — so **same-pack co-location
cannot be the consistency guarantee**. Drift is prevented structurally instead:

1. **The controller is the principal writer of the typed slots.** Cross-pack lenses emit their
   **native artifacts** (a journey map, a blueprint, a C4 model) and *propose* through the
   open-questions queue; **`discovery-lead` (running `discovery-loop`, the schema's owner) is what
   translates those into schema-conforming slots.** A cross-pack lens therefore **never touches the
   schema — it cannot drift what it does not write.** (This sharpens D5's "lens proposes / controller
   promotes" + the lens-write-integrity AC: a lens's output is *advisory data the controller records*,
   not a direct cross-pack write.)
2. **The only direct slot-writers are same-pack.** The skills that *do* write slots themselves — the
   D6 pair `explore-options` / `plan-validation` and `frame-domain` — all live in
   `product-engineering` beside `discovery-loop`, so they read the **carried template + schema
   in-pack** (one source of truth, no cross-pack import). *So yes: every direct writer is same-pack;
   cross-pack participants are mediated.*
3. **A `schema_version` stamp + a conformance check are the mechanical backstop.** Every instance is
   stamped; readers check compatibility; the traceability lint already walks the produced instances,
   so a slot that doesn't conform (or carries a stale `schema_version`) is **flagged, not silently
   accepted**. The schema lives in one skill, so a bump moves the definition + the producing skill
   **atomically** (no multi-pack version skew).

So the anti-drift guarantee is **single-owner + controller-mediated writes + same-pack direct writers
+ a version stamp + a conformance lint** — *not* blanket same-pack co-location, which the cross-pack
lenses make impossible anyway.

### Decision 3 — the gate state machine (checkpoint/resume + rejection/recovery)

**In plain terms.** This is how the loop stops for a human and how it backs out of a bad call. At a
sign-off point it writes up its recommendation, pauses, and waits; when the human answers, it
resumes. The answer is **not just yes/no** — the human can **approve, approve with a scope limit,
steer in a new direction, ask to see alternatives, park it, or abandon it** — and any answer that
changes things **first shows what it will invalidate** before doing it, and the loop **never advances
past the gate without an explicit answer**. (A "gate" = a sign-off point; "cascade-invalidation" =
the stale-marking that follows the chain of what-depended-on-what.)

*Consent checkpoint/resume (A1/A2).* A consent gate (G0, G1.5, G2; G5 is RFC-0049's) is a
pause, not a special runtime: `discovery-lead` writes the **decision brief** to the
blackboard, sets `status=awaiting-human`, and emits an **option card** —
`{gate, summary, decisions-requested, recommended, reversibility-class, artifacts}` (A2). The
harness surfaces it (omnigent's human-in-the-loop pause; a Claude-Code plan-mode-style
read-only state); the human's verdict — a **typed value** (the verdict set below), with its
rationale — is written to the (append-only, attested) decision log; the next round reads
the log and resumes. Non-consent gates auto-advance unless a risk trigger (RFC-0025) fires.

*Rejection/recovery with cascade-invalidation (O11).* A rejection (a human "no" at a
consent gate, or a lens invalidating a prior slot) runs, in the controller's own context:

1. emit `reason → correction`; re-enter that gate's phase;
2. **cascade-invalidate downstream blackboard slots by walking the traceability out-edges**
   from the rejected node — mark each `stale`, drop its edges from the active matrix;
3. re-run **only the affected lenses** on the reduced surface.

The edge set *scopes the blast radius* — the whole reason the matrix is typed. The
prototype ran this for the fulfillment over-scope: the human rejected
`cap.external-fulfillment` at G1.5, the walk marked `screen:fulfillment` +
`service:fulfillment` stale and dropped their edges, and only the UX lens re-ran (see
[`0053-notes/spike/loop-trace.md`](0053-notes/spike/loop-trace.md) §O11). This is the
LangGraph-checkpointer / plan-mode reject→revise shape (note 09 O11), realized as a state
edit, not a framework call.

*The verdict is a typed set, not yes/no (the human-steer space).* A consent gate is where the human
exercises the irreducible value/accountability acts, and those are richer than approve/reject. The
verdict is a **typed enum**, each with its own transition — and the binary "reject → cascade-invalidate"
above is just **one row** of it; every row that changes the blackboard **reuses** the cascade mechanism
(walk edges → mark `stale` → re-run only the affected lenses), always gated by the two integrity guards
below:

| Verdict | What the human means | Transition (no-engine — status edits + a recorded verdict) |
| --- | --- | --- |
| **approve** | proceed as recommended | promote the gate's slots to `ratified`; advance |
| **approve-with-constraint** | OK, but with a scope cut / condition that **must be honoured before proceeding, not jumped past** | record the constraint into the **Scope Boundary**; re-run only the lenses it touches; **do not advance** until the reduced surface re-converges |
| **redirect / steer** | not this — go *this* way | record the new direction as an `intent` steer; **surface the impact** (which slots it obsoletes); on confirm, cascade-invalidate that scoped set and re-enter convergence with the steer as input |
| **explore-alternatives** | show me other paths first | route **back to the divergence phase (Decision 6)** — `explore-options` regenerates candidate shapes around the steer, then converge the chosen one |
| **abandon** | kill it | record the kill + rationale (the `de-risk-intent` kill-condition shape); cascade-invalidate the whole subtree to `abandoned`; close the node |
| **park / defer** | not now | set the node `parked` in the sub-idea index (Decision 1); resumable later; advance siblings |
| **extend / override** | keep going past a bound | grant more `round_cap` / `cost_budget` (or lift a structural bound) and resume — the verdict used at a **paused-at-bound** gate (Decision 4); records the new bound + rationale |

**Two integrity guards bind every row** — this is what "protect the blast radius *and* the process"
means in the contract:
1. **Impact-before-blast.** Any verdict that would invalidate or change slots **first shows the
   affected set (the blast radius) and waits for confirmation** before cascading — the same
   surface-don't-auto-cascade posture as the high-fan-out circuit-breaker (§ Security & integrity
   contract). The human steers *seeing* the consequences, not blind.
2. **No jumping ahead.** The loop **does not advance past a gate without an explicit typed verdict**;
   a scope limitation is honoured before proceeding (never silently overrun); and the verdict + its
   type + rationale are written to the **append-only, attested** decision log (the forged-consent
   control). Abandonment and redirect are first-class recorded outcomes, not dead ends.

*Persistence — how parked and abandoned ideas are remembered (two tiers).* The `park` verdict is only
useful if a deferred idea is actually remembered, so persistence is explicit:

- **Tier 1 — the working store (`_state/`), durable while the initiative is active.** The whole
  plan-tree, including `parked` nodes in the sub-idea index (Decision 1), is **durably checkpointed to
  the harness's `_state/` store** at each gate/round (the Decision 2 commit cadence). A run can pause
  (`awaiting-human`) and **resume across sessions** — the next run reads `_state/` and continues. So
  *within* an initiative, deferred ideas persist by construction.
- **Tier 2 — committed repo artifacts, durable beyond the run (this is how "the repo remembers").**
  When a run ends or the working store is torn down, the loop **promotes the durable record into
  committed artifacts**: the **decision log** records every `park` / `abandon` + rationale
  (append-only); the **backlog bridge** (note 08) carries `parked` sub-ideas as **first-class entries**
  (not just ready-to-build items); and the **intent tree** persists as committed discovery docs. The
  durable home of a deferred idea is therefore the **committed backlog + intent + decision log in the
  repo** — distinct from the harness's working `_state/`.

A parked idea is then **resumable** (re-instantiate its node from the committed entry), and
`research`'s `decision-archaeology` **revival check** can later flag a parked/abandoned idea whose
original deferral rationale no longer holds — so "remembering" is *revisitable*, not a passive
archive. This is the **in-scope half** of the portfolio line in Non-goals: the **durable record** of
deferred ideas is the contract's; **scheduling/resuming many threads across initiatives** stays the
harness's.

*Resume design (the other half of "checkpoint/resume").* Checkpointing writes durable state; **resuming
reads it back and re-enters at the right place** — and the RFC named resume without specifying it.
The contract, no-engine (a load + a status read, not a runtime):

1. **Entry point (two ways in).** Either `discovery-lead` is invoked **on an existing initiative id**
   (*"resume the household-EA discovery"* / *"resume the recipe-integration sub-idea"*) and loads it
   directly; **or**, on a *fresh start* request, the skill's **first action is to scan the discovery
   root for in-progress / parked initiatives and offer to resume them before scaffolding a new
   plan-tree** — so a start never silently duplicates or orphans an existing discovery. (Scan finds
   nothing → proceed to G0 intake. See § Usage for the prompt/response flow.)
2. **State reconstruction (two sources, mirroring the two tiers).** If the working `_state/` (Tier 1)
   is present, load it directly (it carries the live plan-tree + slot statuses + the `meta` block —
   gate, round, cost). If `_state/` was torn down, **re-hydrate from the committed Tier-2 record** —
   the intent tree + decision log + the backlog's parked entry carry the node, its status, its decision
   history, and its place in the tree (via stable ids), enough to **reconstruct a working node**.
   **But the live `meta` counters (round, `cost_spent`, saturation) and per-node slot statuses are
   Tier-1 state** — for a faithful resume Tier-2 must carry a **per-gate snapshot of `meta` + per-node
   status** (cheap: written into the decision-log option card / the backlog entry at each gate commit).
   *Absent that snapshot, cross-teardown resume is **gate-granularity only** — it re-enters at the last
   committed gate with the round/cost counters **reset**, not mid-convergence.* Which of the two
   (faithful snapshot vs. gate-granularity reset) is an **implementing-spec AC**; the default
   recommended here is the per-gate snapshot, since D4's bounds and "resume where it stopped" depend on
   the counters surviving.
3. **Re-entry point.** The plan-tree's **per-node status says exactly where to resume**: `awaiting-human`
   → read the verdict from the decision log and apply its D3 transition; `parked` → re-activate the node
   and re-enter its phase; `stalled-at-cap` (D4) → resume after the human adjusts budget/scope;
   `converging` → continue the convergence loop where it stopped.
4. **Integrity on resume (don't trust a resume blindly).** On load the loop **(a)** checks
   `schema_version` (an older discovery-workspace → migrate or flag, never silently mis-read);
   **(b)** re-runs the connectedness lint before continuing (resume must not skip the verifier);
   **(c)** re-attests any human verdict it acts on through the harness-attested channel — a *resumed*
   `ratified-by: human` row is no more forgeable than a fresh one (§ Security & integrity
   verdict-write-authority); and **(d)** is **idempotent** — re-applying a verdict or cascade already in
   the append-only log is a no-op, not a double-apply.

Who *triggers* a resume is a human (invoking `discovery-lead` on the id) or the harness (scheduling a
parked thread — its concurrency call, per Non-goals); the **contract supplies the resume mechanism**,
the harness decides *when*.

*The answer-each-other ripple (O5).* Lenses bounce off each other **through the
open-questions queue and the blackboard**, never by chat. The reconcile lens runs
`product-engineering`'s **own user-scope design reviewers** (the discovery security/quality
lenses — distinct names from `core`'s code reviewers, degrading to `core`'s depth library when
present; RFC-0048 § Amendments 2026-06-26, revising the original "core reviewers in a mode"
reading of O5) over the journey/blueprint mid-loop. The prototype's OQ-3 settled
security→product→tech→ux→design
as queue-status + blackboard edits with **zero agent-to-agent negotiation** — the MAST
guardrail held by topology (Decision 5).

### Decision 4 — the outer cap + cost budget (O12)

**In plain terms.** Bounds so the loop can't churn forever — a cap on rounds and a cost budget — but
hitting a bound is **never a silent stop or a silent continue**: the loop **pauses and asks** whether
to extend (grant more budget), narrow the scope, park it, or abandon it. Under recursion the bounds
also keep one deep sub-idea from quietly eating the whole budget.

`discovery-loop`'s `meta` block (and each plan-tree node) carries `round` / `round_cap` and
`cost_budget` / `cost_spent`; the controller increments them — **data counters, no runtime**. The
shape (option **C** in [note 13](0053-notes/13-recursion-and-resource-management-research.md), chosen
because a depth-first single controller discovers sub-ideas *as it goes*, so pre-allocating per-branch
sub-budgets — option B — is guesswork):

- **Per-initiative enforcement** — one `cost_budget` + `round_cap` for the whole tree.
- **Per-node convergence round cap** — each sub-walk's convergence loop is bounded too; the
  initiative cap bounds the whole.
- **Per-node spend (observability)** — each node records its `cost_spent`, so it is visible *which*
  branch is consuming the budget.
- **Concentration bound** — when one sub-walk's spend exceeds a configurable fraction (~40%) of the
  budget, the loop reacts *before* it drains the rest.
- **Structural bounds** — a max sub-walk **depth** and max **open sub-ideas** (breadth) guard against
  nesting explosion (the HFSM-scalability lesson, note 13 §2).

**Every one of these bounds is a pause-and-confirm/override gate, not an auto-terminal.** On hitting
any bound the loop sets `status: paused-at-bound` (a *paused-awaiting-human* state, **not** a terminal
`stalled` walk-away), writes a decision-log option card, and **surfaces the choice** — **extend /
override** (grant more budget/rounds or lift the bound), **narrow** (`approve-with-constraint`),
**park**, or **abandon** — the D3 verdict set, of which **`extend / override`** is the row used here. A paused-at-bound
initiative therefore **resumes** once the human overrides or narrows (D3 resume): the cap is just
another consent gate, not a dead end.

*Honest gap:* the prototype converged early (round 4 of 12, $6.40 of $25), so the bound transition was
**modelled, not run live** — a spec-time test must force a bound hit. The transition is a
counter-compare grounded in `work-loop`'s cap + omnigent's `cost_budget`; no runtime.

### Decision 5 — the supervisor topology (solo / lens-team; loop-scoped roster)

**In plain terms.** Usually one discovery lead runs the whole thing. For a big, multi-discipline
effort it can fan out to a few specialist "lenses" (research, product, UX, architecture, safety) —
but **within the loop** they coordinate by writing to the shared discovery-workspace, not by
**free-form chatting to consensus** (which is where multi-agent systems thrash). That's the right
pattern for *this* shape — interdependent lenses converging one artifact; coordination *across* loops
and at company-OS scale is different (see the scope note below). ("Topology" = who-talks-to-whom;
"roster" = which lenses are on the team.)

`discovery-lead` right-sizes:
- **Solo** (small discovery) — holds the blackboard in one context, switches lenses itself
  (cheap, no coordination cost). The prototype ran solo.
- **Lens-team** (large, multi-discipline) — dispatches **parallel lens-agents** that each
  supervise their domain (research/analyst · product · UX/design · architecture ·
  security/compliance) and **bounce off each other through the blackboard** (the
  open-questions ripple), with `discovery-lead` as controller — the proven supervisor +
  blackboard topology (LangGraph supervisor; omnigent Polly + cross-vendor review), **not
  chat negotiation**. This extends autonomy and parallelism without MAST thrash, because the
  thrash is the *other* pattern (agents negotiating to consensus via chat), which the
  blackboard + controller mediation never does.

*Scope of the "no chat" rule — it is intra-loop, and the invariant is structure, not silence.* The
rule above governs coordination **inside one discovery loop** (interdependent lenses, order unknown —
the blackboard's research-confirmed sweet spot). It is **not** a claim that agents never communicate
at scale: the 2026 landscape (A2A — 150+ orgs, Linux Foundation; MCP / ACP / ANP) makes structured
agent-to-agent communication standard and enterprise-grade. The real invariant is **structured
coordination + verification, never free-form chat-negotiation-to-consensus** — and the right
*mechanism* depends on the shape ([note 14](0053-notes/14-coordination-topology-and-scale-research.md)):
- **Intra-loop convergence → the blackboard** (this Decision).
- **Inter-loop handoff → durable contract artifacts** (RFC-0048's "seams are artifacts, not calls" —
  plus event-driven for long-running async work).
- **Company-OS scale → structured agent protocols + an agentic mesh** (capability directory + A2A/ACP
  + an event bus) — teams *do* discover and interact dynamically, defensibly, **because it is
  typed/contract-bound/verified**, the opposite of free-form chat.
The mesh / protocol layer is the **harness's / platform's (CHARTER Principle 3)**: this RFC ships
blackboard-coordinated loop-teams **+ the stable-id substrate a mesh would need** (the briefs /
`contract@version` ids / backlogs a mesh resolves against), **not** the mesh itself. This is **not** a
full mesh-readiness claim: a mesh layer must still add what this contract does not specify — a
capability advertisement / discovery descriptor and a typed binding interface (the stable ids are
necessary, not sufficient).

The discovery roster is **loop-scoped** and authoritatively defined by RFC-0048's roster
table — this RFC adds no roster of its own. The discovery **security/compliance** and
**quality/reliability** lenses are *design-time* roles (threat-modeling + regulated-domain
compliance, and reliability/operability, over the journey/blueprint/architecture), carried
by `product-engineering`'s **`discovery-threat-reviewer`** and
**`discovery-reliability-reviewer`** — **distinct agents from `work-loop`'s code
`security-reviewer` / `quality-engineer`**, by exact name (the collision-hardening RFC-0048's
table requires). So the charter's "three reviewers is the ceiling" is a
`work-loop`/code-review constraint; the discovery loop carries its own design-time lens
roster (RFC-0048's roster table — disciplined, not a marketplace; the CHARTER's reviewer
ceiling itself stays a `work-loop`/code-review cap, recorded as a tracked RFC-0048 amendment
by this child — see Follow-on artifacts). **Lens conflicts:** factual disagreement →
`discovery-lead` arbitrates via referents on the blackboard; *value* disagreement (security
says no, product says ship) → the human at G2 (the conflict-adjudication act). **Progressive
enhancement (A3):** hard deps are `product-engineering`'s intent skills + the carried
versioned sidecar-schema contract (harness-neutral, travels with its producer pack — RFC-0048
§ Amendments 2026-06-26) + the G3 handoff + the two `product-engineering` discovery reviewers,
**required at G2 reconcile** and degrading only in *depth* (their own baseline checklists when
`core`'s `security-checklists` / `operational-safety` + `quality-engineer` depth is absent,
never to nothing). The `research` / `experience` / `architect` lenses are the optional
detect-and-degrade set — product-only discovery alone, lighting up as packs install. The
"team" is the installed lens-packs + a thin team-manifest; omnigent YAML agent-defs are the
harness expression.

### Decision 6 — the exploratory scaffold (divergence → convergence → validation) + its skill/agent inventory

The convergence loop (D1–D5) *narrows*; run alone it commits early. A dogfood run on a second
example — a household executive-assistant ([note 11](0053-notes/11-second-example-divergence-and-provisional-spine.md))
— reproduced **myopic-greedy commitment** live: with no divergence stage the loop locked onto the
first coherent framing (a narrow kitchen "draft-and-approve" assistant) and missed both a *higher
altitude* (a real top EA runs the **whole household** — calendar, travel, vendors, budget,
home-maintenance; the kitchen is one slice) and a *deeper sub-domain* (meal→recipe→ingredient→store
sourcing). And on the other side, a converged blackboard is internally coherent but **not
validated**. Decision 6 wraps the loop in a **three-stage scaffold**:

1. **Divergence (pre-G1.5).** `discovery-lead` generates **N candidate product shapes** across two
   axes — **altitude** (narrow-slice ↔ whole-domain) and **mechanic** (draft-and-approve /
   coordination-layer / knowledge-graph-first / ambient-capture) — recorded as `intent`-variant
   blackboard slots, each with its riskiest assumption, *before* convergence narrows. Selection is an
   explicit compare-and-choose; the altitude bet is **surfaced at G1.5** (it is a value/scope call).
2. **Convergence (G1.5→G2).** The existing D1–D5 loop on the chosen spine. **Unchanged.**
3. **Provisional-spine emission (G2).** The decision brief is emitted as a *connected hypothesis*:
   each load-bearing assumption carries a **validation hook** — its `de-risk-intent` kill condition
   **plus the real-world activity that would confirm or enrich it** (interview / diary / Wizard-of-Oz
   pilot / usability test) — turning the assumption ledger into a **validation plan**, and stating
   plainly that desk-grounding ≠ validation. Every node is labelled **grounded** (a referent exists),
   **surfaced** (value/scope call → human gate), or **to-validate** (only real users can confirm).
   (See § *What is looped to convergence* → *Converged is not validated*.)

**Plan-tree implications (Decision 2).** Both new stages are *structural, not just prose*: divergence
adds a **candidate set + selection** to a node (the not-chosen retained as `rejected`/`parked` with
rationale, so they stay revivable), and validation adds a **per-node validation status + hook**
(`hypothesis → validating → validated | refuted`). Both extend the **plan-tree template** (D2) — data,
no engine.

**Skill & agent inventory to achieve it.** Run against the repo's add-a-skill gate (*agnostic? not
duplicated? a discipline, not scaffolding? needed ≥3 times?*), **two thin PE skills earn their place**
— pretending the scaffold is free was an under-call:

| Goal | Reuse (genuinely) | Net-new (earned) | New agent? |
| --- | --- | --- | --- |
| **Divergence** — generate + select candidate shapes | `compare-hypotheses`'s ACH matrix to *select* among shapes; `devils-advocate` to pressure each; `de-risk-intent` to risk each; the self-coverage gate's **scenario-variation** module | **new PE skill `explore-options`** — *generate* candidate shapes across altitude × mechanic. (`identify-perspectives` / `decompose-intent` are adjacent but **wrong-shaped** — research-camp enumeration and convergent breakdown, **not** product-solution ideation; "assemble from them" was the under-call.) | **no** |
| **Convergence** | the D1–D5 loop, the lens roster (D5), the sidecar (D2) | none | none |
| **Validation plan + hooks** | `de-risk-intent` (kill conditions); `research` desk patterns | **new PE skill `plan-validation`** — turn assumptions into a validation plan (assumption → the real-world activity that confirms it) **and scaffold the primary-research instruments** (interview guide, usability-test plan, transcript synthesis). `de-risk-intent` gains a **validation-hook field**. | **no** |
| **The activities themselves** (running interviews/pilots) | — | **out of charter** — `plan-validation` *scaffolds + synthesizes*; a human runs the sessions (the GAP-1 boundary, § Skill-coverage pressure test) | **no** |

So Decision 6 is still **content, not runtime** — but it is **not free**, and the earlier
"reuse + at most one thin skill" framing **under-called it**. Two thin new PE skills are warranted —
`explore-options` (divergence) and `plan-validation` (validation) — plus two extensions
(`de-risk-intent` gains a validation-hook field; `decompose-intent` optionally gains the
prioritization/ranking step the § Skill-coverage pressure test flagged) and one new typed slot (the
validation plan). Both **structurally-different** dogfood walks (notes 11 + 12) needed both new stages,
and the spike — which ran *neither* — is the **negative evidence** (its myopic-greedy commitment is the
failure their absence causes); so the recurrence is **evidenced across both walks**, not asserted. This makes the `product-engineering` intent
suite **more coherent, not more bloated**: today it covers *shape* (`frame-intent`) → *test an
assumption* (`de-risk-intent`) → *break down* (`decompose-intent`) → *ground* (`frame-domain`), but
has **no home for the two stages D6 adds** — generating options, and planning validation — which is
exactly why the divergence walks kept straining the existing skills. Still **no new agent, no new
reviewer, no engine**. The exact skill boundaries are an implementing-spec detail; **that two PE
skills are warranted is decided here**.

### Usage — how to invoke the loop

`discovery-loop` is **designed to run from a single high-level prompt** (the gated tutorial demonstrates the end-to-end walk): name the idea and
ask `discovery-lead` to scaffold it; the loop walks G0→G2 and **pauses at the consent gates**
(G0 vision, G1.5 altitude/MVP, G2 the "what") where your input is the referent. You do **not** need
to break it into pieces up front.

**The one-prompt form (recommended start):**

> *Use the discovery-loop to scaffold the product vision for **a household executive-assistant AI** —
> an assistant that helps a household run food, calendar, vendors, and budget by drafting and acting
> only on approval. Diverge on the product shape first, then converge to a decision brief, and flag
> what needs real-world validation.*

That single prompt exercises the whole scaffold: the loop **diverges** (Decision 6) into candidate
shapes, **surfaces** the altitude bet to you at G1.5, **converges** the one you pick, and **emits a
provisional spine** with validation hooks. You answer at the three gates; the loop does the rest.

**Targeted phase prompts (when you want to redo or deepen one stage):**

> - *Diverge only: give me 4–5 candidate product shapes for the household EA across altitude × mechanic, each with its riskiest assumption — don't converge yet.*
> - *Recurse into a sub-idea: run a full divergence walk on **recipe integration** as a sub-idea of the household EA (build vs. integrate an ontology vs. partner) — it becomes a resumable node on the same blackboard, not a separate project.*
> - *Frame the domain for the **whole-household chief-of-staff** shape (real estate-manager practice + the food sub-domain), and mark what's groundable vs. needs a human checkpoint.*
> - *Take the chosen spine to a decision brief, and emit the validation plan (each assumption → kill condition → the real-world activity that would confirm it).*

**Resuming — the skill checks before it starts.** On a *start* request, `discovery-lead`'s **first
action is to scan the discovery root for in-progress or parked discoveries and offer to resume them
before scaffolding a new tree** — so starting never silently duplicates or orphans an existing
discovery. The flow:

> **You:** *Start a discovery for a household executive-assistant.*
> **Skill:** *Before we start — you have **1 discovery in progress**: `household-EA` (paused at G2,
> round 4, awaiting your sign-off) and **2 parked sub-ideas** (`recipe-integration`,
> `budget-module`). Resume one, or start a new discovery?*
> **You:** *Resume household-EA.* → it loads the discovery-workspace, re-runs the connectedness lint,
> and drops you back at the G2 decision brief awaiting your verdict.

Direct forms when you already know what you want:

> - *Resume the `household-EA` discovery.* (loads `_state/`, or re-hydrates from the committed record if it was torn down)
> - *Resume the parked `recipe-integration` sub-idea.* (re-activates that node in its parent tree)
> - *What discoveries are open or parked?* (a read-only status list — gate, round, last-touched — no scaffolding)

If the scan finds nothing, the skill just proceeds to G0 intake on the new idea.

**Which to use.** Start with the **one-prompt form** — the loop is designed to surface the right
questions to you at the gates, so you rarely need to pre-group. Reach for **targeted phase prompts**
when a gate's output was wrong and you want to re-run just that stage, or when you want to force a
wider divergence before committing. Describing the idea richly (who it's for, the core mechanic, the
appetite) sharpens G0; everything else the loop elicits.

### How the lens skills compose — the lens→artifact→blackboard contract

The skills are not invoked free-form; `discovery-lead` drives them along the gate ladder, each
**reading the typed slots its predecessors wrote and writing its own** as blackboard slots
(Decision 2). The authoritative phase→skill→artifact roster is RFC-0048 § rollout; stated here as
the contract this loop runs:

- **G0 Intake** — `frame-intent` (PE) → a level-tagged `intent` slot. Human ratifies the value seed.
- **G1 Strategy** — `de-risk-intent` (PE) → an `assumption-test` slot (riskiest assumption + kill
  condition); `decompose-intent` (PE) → child `intent` slots. The intent recursion viewed whole *is*
  the opportunity-solution tree ([`0048-notes/04`](0048-notes/04-artifact-inventory.md)).
- **G1.5 Domain & MVP** — `frame-domain` (PE, wrapping `research` applied) → `domain-framing` +
  `scope-boundary` slots. The Scope Boundary is the referent the scope-creep guard and the human
  reject over-scope against. Human ratifies the MVP boundary.
- **Convergence loop** — the lens skills run as **parallel writers onto the blackboard**, bouncing
  off each other only through the open-questions queue (never chat):
  - *product:* `decompose-intent` → feature `intent` slots;
  - *UX/experience* (RFC-0050, if installed): `map-customer-journey` → `journey-map`;
    `blueprint-service` → `service-blueprint` (the slicing instrument); `map-screen-flow` →
    `screen-inventory` + per-screen briefs; `aesthetic-direction` / `design-critique`
    (experience) + `voice-and-microcopy` (PE, cross-linked) → taste + copy slots;
  - *tech* (architect / contracts, if installed): `architect-design` / `architect-diagram` → C4 +
    domain model; `api`/`event-contract` → contract slots;
  - *reconcile:* the discovery reviewer roster (`discovery-threat-reviewer` +
    `discovery-reliability-reviewer`, required; `experience-reviewer` / `design-reviewer` if
    installed) fires as live lenses; the self-coverage gate runs its pre-G2 pass; the traceability
    lint flags orphans.
- **G2 Convergence** — `discovery-lead` renders the blackboard → a `decision-brief` slot. Human
  ratifies the "what" and adjudicates conflicts.
- **G3 handoff** — `decompose-intent` emits per-feature briefs; the backlog bridge orders them;
  `work-loop` takes over.

Two properties make this a **contract, not a hard-wired pipeline**: (1) any optional lens may be
absent — the `research` / `experience` / `architect` lenses detect-and-degrade, leaving product-only
discovery at the floor (Decision 5); (2) every write is a typed slot, so a downstream lens reads its
upstream's output **by slot-name + `schema_version`, never by calling the producing skill**
(Decision 2). That decoupling is exactly what lets the lenses run in parallel without
agent-to-agent chat (the MAST guardrail of Decision 5).

### Skill-coverage pressure test — is the lens set sufficient?

The lens set above was pressure-tested against the canonical product-discovery frameworks the
operating model already cites — Torres's continuous discovery / opportunity-solution tree, SVPG's
four discovery risks (value · usability · feasibility · **viability**), the Double-Diamond /
Design-Sprint *divergence-before-convergence* rule, NN/g service design, and Shape Up — grounded in
the promoted research in [`0048-notes/01`](0048-notes/01-research-consolidation.md). (This is a
**repo-internal pressure-test against already-confirmed sources**, not a fresh external survey.)
Most canonical activities map cleanly: intent/OST → `frame-intent` + `decompose-intent`; assumption
testing → `de-risk-intent`; domain → `frame-domain`; journey / blueprint / screens → the experience
trio; feasibility → architect; taste / copy → experience + `voice-and-microcopy`; convergence → this
loop. The test surfaced the following, **routed rather than silently absorbed**:

- **The one genuine design gap — no divergence phase (→ Decision 6).** Every phase of the gate
  ladder is *convergent* (G0→G1→G1.5→convergence→G2 each narrows). No skill *generates multiple
  candidate solution approaches* before the loop commits to one: `decompose-intent` breaks down a
  *chosen* approach, and `devils-advocate` *critiques* a produced artifact — neither forces
  solution-space exploration. The Double Diamond and Design Sprint treat forced divergence as
  non-optional, and the loop's own headline risk — myopic-greedy commitment
  ([`0048-notes/03`](0048-notes/03-autonomy-and-gate-economics.md)) — is exactly what an absent
  divergence phase invites. The multi-agent evidence cuts both ways (convergent pipelines like
  MetaGPT work for *coding*; product discovery is more open-ended, and a blackboard+supervisor
  topology has no structural divergence mechanism). **Promoted to Decision 6** (the exploratory scaffold).
- **Two low-cost adds that belong in the brief/sidecar, not new skills.**
  - *Success-metrics definition.* `frame-intent` / `decompose-intent` already name outcomes + a
    North Star ([`0048-notes/04`](0048-notes/04-artifact-inventory.md) lists "Outcomes & metrics" ✓
    as the traceability root) — but they are **not yet a required, structured slot** in the
    `decision-brief` the build loop consumes, so a brief can reach G3 without a done-criterion the
    build loop can iterate against. The fix is to **elevate metrics to a required brief-template
    slot** (the implementing spec owns the template), not a new skill; the *instrumentation*
    implementation stays downstream / out of charter
    ([`0048-notes/01`](0048-notes/01-research-consolidation.md)).
  - *Prioritization.* `frame-intent` appetite + the Scope Boundary do constraint-setting, not
    multi-criteria ranking across opportunities (note 05 type-5 names "objective function + decision
    matrix" as the mechanism but ships none). A lightweight ranking step (the adopter's RICE /
    Torres / custom rubric) is a candidate **`decompose-intent` enhancement**, routed to the PE
    pack — not this RFC.
- **Intentional exclusions (confirmed, not gaps).** Primary user-research *facilitation* (the agent
  scaffolds an interview guide + synthesizes provided transcripts; a human runs the sessions), live
  usability-test facilitation, full business-viability / market-sizing / pricing, and GTM/PMM are
  deliberately out of a code-building catalogue's charter (note 01's "deliberately NOT building";
  RFC-0048 non-goals). The discovery-phase *design* of a usability test or a lightweight viability
  canvas is in-scope-if-wanted, but is PE/experience-pack lens work, not coordinator-contract work.

**Net:** the coordinator contract (D1–D5) is **unchanged** by this pressure test — it orchestrates
whatever lenses are installed and degrades cleanly when they are absent. The findings route to (a)
Decision 6 (the exploratory scaffold — divergence + provisional-spine emission), (b) the implementing spec's brief template
(the success-metrics slot), and (c) the `product-engineering` / `experience` packs (a prioritization
step; optional research-synthesis and viability-canvas lenses) — none of which this RFC must resolve
to ship the contract.

### Security & integrity contract (spec-stage acceptance criteria)

**In plain terms.** Because the loop runs largely unattended and records human approvals, this section
lists the safety rules the build must enforce — so the loop **can't forge a human's sign-off, can't
quietly tamper with the decision log, and can't run away**. Each is written as a test ("acceptance
criterion") the implementing spec must pass; this RFC names the controls, it doesn't write the code.

The coordinator orchestrates an autonomous, multi-lens loop that designs LLM/agent products
and holds the human-gate (value/accountability) acts RFC-0048 D1 says are irreducibly human.
A spec-stage secure-design pass surfaced controls that must be **first-class parts of the
contract**, named here and carried as **acceptance criteria in the implementing spec** (this
RFC ships no code, so it specifies the controls, it does not implement them):

- **Verdict write-authority (no forged consent).** Because the *same* reasoning context both
  sets `status=awaiting-human` and reads the decision log to resume, the contract must
  prevent the controller (or a poisoned lens) from writing its own `ratified-by: human` row
  and auto-advancing a consent gate the human never saw. **AC:** the human verdict is written
  through a **harness-attested channel the agent has no token for** (omnigent's HITL pause
  writing the verdict), and resume is gated on a verdict whose `human` provenance is
  harness-attested, not self-asserted in a file the agent also writes. **This is a hard
  harness-conformance precondition, not a demonstrated property:** in the spike the agent maintained the
  worktree files *by hand* (it wrote the decision-log itself), and omnigent is confirmed only to
  *pause* for HITL — that its pause writes the verdict into a store the agent has no token for is
  **required, not established**. An adopter whose harness cannot provide an agent-untokened verdict
  channel **cannot run the loop unattended safely**; the implementing-spec AC must test the *channel*
  (the agent provably cannot forge the row), not merely the slot's append-only-ness.
- **Decision-log as a real audit trail.** **AC:** the decision-log slot is **append-only**
  with **per-row actor attestation** and **tamper-evidence** (content-hash-chained rows, or
  the integrity delegated to a harness-provided immutable log) and a **trusted timestamp**.
  Append-only is partly mechanically checkable (a lint/CI assertion that the slot's commits
  are add-only), so pair the AC with that wiring.
- **Security/compliance lens is non-degradable on a security boundary.** The
  `discovery-threat-reviewer` is a hard dep (required at G2; it ships in `product-engineering`,
  the floor) and degrades only in *depth* — never silently skipped. But its baseline checklist
  must not silently stand in for full depth on a security-relevant product (the worked
  example's whole ripple is an OWASP LLM-01/08 prompt-injection-self-modification finding).
  **AC:** tie the lens's *depth* to a **risk trigger** (mirroring RFC-0025 / the surfacing
  predicate) — when an intent or artifact crosses a security boundary (auth,
  untrusted-input-to-memory, regulated data) and `core`'s `security-checklists` depth is absent
  (only the reviewer's baseline checklist is available), the loop **surfaces to the human**
  ("security-relevant boundary crossed, only baseline security depth installed") rather than
  degrading silently.
- **Lens-write integrity (no blackboard poisoning).** In lens-team mode, lens-agents write
  the blackboard the controller trusts for convergence and cascade-invalidation; a lens that
  ingests untrusted external content (web `research`, adopter docs) is an injection sink.
  **AC:** a lens may only **propose** (`status: proposed`); **only the controller promotes**
  to `ratified`; lens-asserted traceability edges are **advisory until the controller
  validates** them; any lens ingesting untrusted external content is a trust boundary whose
  output is **data, not instructions**, to the controller.
- **Cascade-invalidation circuit-breaker.** O11's edge-walk *scopes* a rejection, but the
  same primitive is a denial-of-convergence lever (spurious edges from a high-fan-out node
  could invalidate the whole blackboard and burn the budget). **AC:** cascade re-runs count
  against the cost budget, and an invalidation exceeding a fan-out threshold **surfaces to
  the human** rather than auto-cascading.
- **`reversibility-class` is an enumeration, not free text.** It gates consent stakes, so an
  agent must not under-classify a one-way door as `reversible`. **AC:** enumerate the classes
  (`reversible` / `costly-to-reverse` / `one-way-door`) and bind `one-way-door` to a
  mandatory consent gate regardless of which gate it arose at.
- **Sidecar data-handling / classification (not just integrity).** The slots above carry
  product strategy, personas, security findings, customer/domain facts, and consent
  rationale — sensitive product and (potentially) regulated data, a *data-handling* surface
  distinct from the integrity controls above. **AC:** the spec **classifies each slot**
  (`public` / `internal` / `sensitive` / `regulated`, or an adopter's repo-local equivalent),
  gives **redaction guidance** for examples and promoted notes (so a `sensitive`/`regulated`
  fact is not copied verbatim into a shared example or a promoted note), and states
  **retention/export expectations** for `_state/` and harness-backed stores. **A regulated- or
  secret-bearing artifact surfaces to the human / `discovery-threat-reviewer` lens before
  being written to a shared repo-backed sidecar** — the same surface-don't-degrade-silently
  posture as the security-lens-depth AC above. (RFC-0048 § Amendments 2026-06-28 records the
  contract; this spec owns the concrete rules.)
- **Traceability backstop is a reachability check, not just presence.** The RFC leans on
  child-4's lint as the backstop against an under-implemented sidecar, but the spike's
  demonstrator is a *presence* check (flags a node missing an edge), which a
  disconnected-but-locally-edged subtree or a fabricated edge passes. **AC (child-4):** the
  shipped lint performs a **root→leaf reachability** pass, so the backstop can actually
  detect the failure it is invoked against; flagged as a child-4 dependency so this RFC's
  backstop claim is not load-bearing on the weaker presence check.

### The seam with the rest of the operating model

**In plain terms.** Where this loop hands off to the others. It produces a brief; the build loop
(`work-loop`) takes that brief and writes code; the release loop ships it. This section names those
handoff points so nothing falls through the cracks between loops. ("G3" is the hand-off point from
discovery to build.)

- **G3 handoff to `work-loop`** (unchanged): `discovery-loop` emits a brief → `new-spec` →
  `work-loop`. The two loops meet here; different inputs, different verifier, different
  autonomy posture.
- **The self-coverage gate** (RFC-0051) runs as `discovery-loop`'s **pre-G2 phase**, and this loop
  is the **primary home of the full seven-module design-convergence instantiation** — discovery
  carries its own co-scoped copy of all seven modules, right-sized by this loop's own progressive
  mode, conforming to RFC-0051's cross-loop seam (goal + resolve-vs-surface + a non-skippable
  coverage record); wired here. Unlike `work-loop` (which adopts only the net-new slice because the
  rest already lives in its loop), discovery runs the full battery: this is the altitude it was
  built for.
- **The traceability lint** (child-4) consumes the **traceability slot** this RFC defines;
  the cascade-invalidation transition (D3) walks the same edges. The lint is authoritative
  when the matrix is present and derives from on-disk artifacts when the sidecar is absent
  (RFC-0048's child-4 amendment), so the loop and the standalone lint share one edge model.
- **The backlog bridge** (note 08): the decision brief decomposes into an ordered,
  dependency-aware backlog; `loop-cohort` orders it; `work-loop` pulls one item at a time.

### Folding in traditional requirements capture (enterprise input)

**In plain terms.** Many enterprises still do classic requirements work — a BRD, a PRD, an SRS/FRD,
use cases, a requirements-traceability matrix (RTM) — and often **refine requirements at several
levels at different times** (business → system → functional), not in one upfront pass. This loop does
**not** replace that and adds **no "requirements" pillar of its own**; it *maps* those artifacts onto
the artifacts it already produces, ingests them as input, and can emit in their format for sign-off.

| Traditional artifact | Maps to in this loop |
| --- | --- |
| **BRD** (the *why*; business objectives; success metrics) | a product-vision / strategy **`intent`** + the outcomes/metrics fields |
| **PRD** (product requirements, each traceable to a BRD outcome) | capability / feature **`intent`** slots + the **decision brief** |
| **FRD / FRS** ("the system shall…", functional behaviour) | the **journey + service-blueprint + screen-flow** slots, then the **spec ACs** (post-G3) |
| **SRS** (functional + NFR + use cases, system level) | the convergence outputs + the **architecture lens** + the spec |
| **Non-functional requirements** (perf, security, reliability, compliance) | the **discovery reviewers** (`discovery-threat-reviewer` / `discovery-reliability-reviewer`) + the architecture lens + spec ACs |
| **Use cases** | journey steps / screen flows |
| **Requirements Traceability Matrix (RTM)** | the **traceability slot** — a near-direct mapping; the loop already produces outcome→…→component traceability, which *is* an RTM, with the traceability lint as its completeness check |
| **IEEE 29148 quality attributes** (unambiguous, complete, consistent, testable, traceable) | what the **self-coverage gate + traceability lint + discovery reviewers** already enforce |

Three integration directions, **reuse-first**:

- **Requirements as input (ingest).** An existing BRD/PRD/SRS *seeds* the loop instead of being
  authored from scratch: **`receive-brief`** (core) + **`frame-intent`** brownfield current-state
  inputs ingest it at G0/G1.5; the loop then **validates and enriches** it — `frame-domain` grounds
  it, the lenses add the journey/architecture a requirements doc usually lacks, `de-risk-intent`
  surfaces the assumptions it states as fact, and the self-coverage gate covers
  completeness / ambiguity / scenario-variation. *Net-new: at most a thin `receive-brief` extension*
  that recognizes the requirements-doc shapes — **not** a new skill.
- **Refinement at various levels / different times.** Enterprises that refine business → system →
  functional over time map directly onto the **recursive plan-tree** (Decision 1): each level is a
  node at its altitude, refined when it's reached and **resumable** later — the loop is built for
  exactly this staggered, multi-level refinement, not a single upfront capture.
- **Requirements as output (emit for sign-off).** Where governance *requires* a formal BRD/SRS/RTM
  with sign-off, the loop **projects** its decision brief + traceability matrix + spec ACs into that
  format — a **formatting/projection adapter** (the converters / md-to-office path, RFC-0036), not a
  discovery skill; the decision-log + the § Security & integrity controls supply the auditable
  sign-off trail.

**Recommendation.** Do **not** add a requirements writing / validation / enrichment pillar — the loop
already authors the equivalents, and the self-coverage gate + traceability lint already validate them
against the IEEE-29148-style quality attributes. Fold traditional requirements in via (1) this
**crosswalk** (shipped as guidance in the `discovery-loop` skill), (2) **`receive-brief` / `frame-intent`
ingest** (a thin extension at most), (3) the **traceability slot as the RTM**, and (4) a **projection
adapter** to emit the enterprise format for sign-off. The implementing spec owns (1)–(2); (4) rides
the converters work. (This is a reuse-first *integration* recommendation, deliberately **not** a new
decision — no new pillar is warranted.)

## Options considered

**In plain terms.** The choice is *how much machinery* we ship to deliver the coordinator — from
nothing, to plain instructions (recommended), to a full coordinator engine, to one giant pack. The
table below walks that range; the recommended option is plain instructions, and each rejected option
says why.

**Axis: how much new machinery the coordinator is delivered as** — the same axis RFC-0048's
Options table uses for the whole initiative ("nothing → prose doctrine → new tool → new
engine → monolith"), here narrowed to the coordinator. It exhausts the space because any
coordinator must sit somewhere on it; prior art grounds each point.

| Option | Shape | Verdict |
| --- | --- | --- |
| **A. Do nothing** — leave the coordinator a noun (RFC-0048's diagnosis: "a noun, not a design") | none | Cost of delay: every operating-model step assumes an unspecified orchestrator; the gate ladder stays un-runnable; the connectedness claim stays an assertion. Rejected. |
| **B. Doctrine + agent-def + skill + sidecar schema, reviewers-as-content, no engine** ★ | the RFC-0041 / RFC-0049 idiom, one altitude up (with its own design-time reviewer roster — RFC-0048's table, not `core`'s code reviewers reused) | **Recommended.** Fits Principle 3; **spike-confirmed** (Decision 1); the contract is harness-neutral; `discovery-loop` is useful at the floor and progressively enhanced. |
| **C. A coordinator runtime / engine** (a scheduler + convergence solver + message bus) | MetaGPT / ChatDev / CrewAI manager-routing shape | Rejected for two distinct reasons: (i) Principle 3 forbids shipping runtime infrastructure; (ii) *separately*, manager-routing/chat-negotiation multi-agent measures 41–86% failure (MAST). The spike showed none of it is needed — the loop runs as content + a lint. Rejected; the harness (omnigent) supplies the runner without us shipping it. |
| **D. Fold the coordinator into `work-loop`** (one loop for discovery + build) | a single mega-loop | Conflates two loops with different inputs, verifiers, and autonomy postures (RFC-0048 D8's "must not be conflated"); the upstream has no local verifier, the downstream does. Un-right-sizable. Rejected. |

Prior art grounds the axis: RFC-0041 chose the B-shape ("no executable tooling, no new
reviewer, no new runtime") for the infra loop and was Accepted; RFC-0049 chose it again for
the *downstream* outer loop (`release-lead` + `release-loop` + the harness); MetaGPT
/ ChatDev / CrewAI are C-shape and MAST measures their failure cost; the charter forbids C.

## Risks & what would make this wrong

**Pre-mortem.**
- *The single-example spike over-generalizes* — the worked example happened to be
  convergence-friendly. **Mitigation:** the example was taken verbatim from note 02 (authored
  before the spike) and the two failure modes were *injected deliberately* to test the
  transitions rather than narrate past them; still, it is one example walked once (Threats,
  spike report). Two **paper** further walks now exist — a household-EA
  ([note 11](0053-notes/11-second-example-divergence-and-provisional-spine.md)) and a science/hardware
  self-driving-lab ([note 12](0053-notes/12-third-example-science-hardware-divergence.md), genuinely
  structurally different) — which surfaced Decision 6; a **live on-`omnigent` run** of a second
  example is still owed at spec time.
- *The cap transition is modelled, not run* — O12's stall-surfaces-to-human path was not
  exercised because the happy path converged early. **Mitigation:** the transition is a
  counter-compare grounded in `work-loop`'s cap; a spec-time test should force a cap hit —
  specifically the **concentration-bound + pause-at-bound-resume** path (the recursion-specific
  behaviour the flat-cap counter-compare does not cover), not just the flat cap. The RFC states this
  honestly rather than claiming "ran".
- *Recursive tree-walking is controller-in-context scheduling whose depth-reliability is unproven* —
  the no-engine claim shows the plan-tree is *data*, but choosing the next node, per-branch budget
  accounting, and descend-vs-surface are work the **controller does in-context**, and the single solo
  example does not evidence it **at depth**. **Mitigation:** it is a *defensible bet on a shallow
  tree*, gated conservatively by D4's depth/breadth bounds; the second-example spec run should walk a
  genuinely recursive (≥2-level) tree, and the RFC states this as a risk-acceptance, not a settled
  win.
- *The sidecar schema drifts from child-4's lint / RFC-0049's reuse* — three efforts touch
  the same typed state. **Mitigation:** the producing `discovery-loop` skill carries the one
  schema *definition* (Decision 2); child-4's lint and RFC-0049's release loop *consume the
  produced instances by convention + a `schema_version` stamp*, not a shared definition; the
  edge model is the one ADR-0022 + the child-4 amendment already fixed.
- *Lens-team mode reintroduces MAST thrash* — parallel lens-agents could negotiate.
  **Mitigation:** the topology forbids agent-to-agent chat *structurally* — all coordination
  is controller + blackboard; the prototype's ripple settled with zero negotiation. The
  guardrail is *how* they coordinate, not *how many* there are.
- *The contract is too thin and an adopter under-implements the sidecar* → the connectedness
  check silently passes on a partial matrix. **Mitigation:** the traceability lint (child-4)
  is the mechanical backstop, authoritative-when-present and artifact-derived when absent —
  but only if child-4's lint does a **root→leaf reachability** pass, not the demonstrator's
  presence check (named as a child-4 AC in § Security & integrity contract).
- *A consent gate is auto-advanced with a forged `ratified-by: human` row*, or the
  decision-log is rewritten — the value/accountability act RFC-0048 D1 reserves for the human
  is bypassed, and the "audit trail" is repudiable. **Mitigation:** the verdict
  write-authority + append-only-attested-decision-log ACs (§ Security & integrity contract);
  the RFC no longer claims the bare schema *is* an audit trail.
- *A poisoned lens-agent writes the blackboard* — flips a slot to `ratified`, fabricates a
  traceability edge that hides an orphan (making the lint wrongly report converged), or
  amplifies a cascade-invalidation to burn the budget. **Mitigation:** the lens-write
  integrity AC (lens proposes, controller promotes; edges advisory until validated; untrusted
  input is data not instructions) + the cascade circuit-breaker AC.
- *Security is silently skipped on a security-relevant product* because the security lens
  pack isn't installed and the loop degrades quietly. **Mitigation:** the non-degradable
  security-lens AC (a security-boundary crossing with no lens installed surfaces to the
  human, mirroring the RFC-0025 risk-trigger posture).

**Key assumptions (falsifiable).**
- *The convergence loop is single-context-followable without a runtime.* If a real
  multi-module discovery needs a scheduler the controller can't be, the no-engine framing
  fails. (Believed false — **demonstrated** for the worked example; the residual risk is
  scale, addressed by lens-team mode, which is still controller + blackboard.)
- *A typed sidecar of plain files is a sufficient connectedness verifier.* If "everything
  holds together" needs richer state than a blackboard + queue + edge set + log, the schema
  under-serves. (Believed sufficient — the lint over it caught the injected defects.)
- *Cascade-invalidation by traceability edges bounds a rejection correctly.* If rejections
  routinely invalidate slots the edges don't reach, the blast radius is mis-scoped.
  (Believed adequate — the edges *are* the dependency model; a slot not reachable from the
  rejected node genuinely does not depend on it.)

**Drawbacks.** A new agent def + a new skill + a carried sidecar schema to maintain (in the
`discovery-loop` skill, not `core`), plus the
design-artifact reviewer modes (RFC-0048 O5) — real surface, justified because the
coordinator is the spine the whole operating model needs. The sidecar adds a typed-state
discipline an adopter must keep current (the same cost any blackboard carries). The
contract is harness-neutral but *demonstrated* on one harness's storage form (omnigent
worktree files); a different harness must map the slots to its store.

## Evidence & prior art

**In plain terms.** Why we believe this works: a hand-run prototype walked the loop's **spine** using
only plain files + one small checker (no engine); the D1–D6 extensions are confirmed in *shape*
(modelled, not yet run). Plus prior art from inside the repo and from published research on
multi-agent systems and self-driving labs.

**Spike / de-risk result — the load-bearing evidence.** The riskiest assumption is the
coordinator's **no-engine / Principle-3 fit** (RFC-0048's own framing: demonstrated for
RFC-0048's D1–D6, *hypothesized* for the coordinator). The prototype ([`0053-notes/`](0053-notes/))
ran `discovery-loop` against the worked example on the form omnigent stores and **supported
the framing on that one example**: walking G0→G2 as one reasoning context, with over-scope
and an unbacked security-sensitive screen injected, every transition was a plain-file edit,
and the only executable was a ~60-line lint (`check_sidecar.py`, child-4's shape) which —
*reproducibly* — flagged 2 dangling service leaves pre-recovery and reported CONVERGED after
recovery + ripple. Each note-09 paper resolution mapped to a confirmed (O2/O3/O4/O5/O7/O11/
A1/A2 + the ripple) or honestly-qualified (O12 modelled-not-run; O6's "no invalidating edit"
clause stays a judgment; **and O5's "live lenses" ran as `core`'s code-reviewers-in-a-mode — *not* the
bespoke `discovery-threat-reviewer` / `discovery-reliability-reviewer` roster D5 now specifies, so that
required floor is specified-not-demonstrated and the second-example run must exercise the actual
discovery reviewers**) result — see [`0053-notes/01-spike-report.md`](0053-notes/01-spike-report.md)
for the table and the Threats-to-validity (one example, single operator, cap not hit live).
**Conclusion:** the no-engine framing is **demonstrated on one worked example plus a
reproducible connectedness lint** — stronger than RFC-0048's bare hypothesis, weaker than a
replicated multi-example result; the assumption survives, with the residual scale risk named
in Risks and a **live** second-example run owed at spec time (two *paper* further walks — notes 11
and 12 — already exist and surfaced Decision 6).

**Repo precedent.** RFC-0048 D7/D8 + [`0048-notes/09`](0048-notes/09-gap-resolutions.md) (the
paper resolutions this confirms) and [`02`](0048-notes/02-worked-example-flow-trace.md) (the
worked example); RFC-0041 + ADR-0031 (the doctrine + reference-library + reuse, no-engine
idiom); RFC-0049 (the sibling downstream loop shipped as `release-lead` agent + skill +
harness — the exact pattern this establishes upstream); RFC-0051 (the self-coverage gate —
`discovery-loop` is the primary home of the full seven-module design-convergence instantiation, carried as its own co-scoped copy); RFC-0050 (the `experience` lens);
`work-loop`'s supervisor mode + `loop-cohort` (doctrine + a scheduler-*script*, not a
service — the precedent that a scheduler can be a lint); RFC-0025 (the iteration cap +
light/full); RFC-0040 (the three-tier layout the sidecar paths obey); RFC-0019's
`lint-brief-coverage.py` (the coverage lint child-4 generalizes); ADR-0022 (the cross-repo
reference-by-version the traceability slot reuses); `docs/specs/traceability-lint/` (child-4,
the lint that consumes the slot).

**External prior art** (fetched and confirmed). **`omnigent`** ([repo](https://github.com/omnigent-ai/omnigent),
fetched 2026-06-26) — confirmed present: an open-source meta-harness with a runner/server
control plane, **policy gates enforced outside the prompt** (spend caps, tool-call limits,
approval-before-shell), **git-worktrees as the shared store**, declarative **YAML agent
defs**, three-level (server/agent/session) governance with **human-in-the-loop pauses**, and
**cost policies** with hard caps + soft thresholds. Its docs describe **no state-sidecar /
general-blackboard capability beyond worktrees** (silence, matching RFC-0048's "documented
alpha gaps (no general blackboard beyond worktrees)" framing) — exactly the gap this
contract fills, and the reason the spike prototyped the sidecar in omnigent's storage form
rather than relying on a native one. The MAST
(41–86% multi-agent failure; arXiv:2503.13657), MetaGPT (arXiv:2308.00352), ChatDev
(arXiv:2307.07924), and LangGraph-checkpointer groundings were fetched and confirmed in
RFC-0048's notes and are not re-litigated here.

**Promoted research.** [`0053-notes/`](0053-notes/) holds the spike report + the prototype
artifacts (the four sidecar slots, two traceability snapshots, the demonstrator lint, the
loop trace), plus two further dogfood walks that surfaced **Decision 6** — the household-EA
divergence + provisional-spine record
([note 11](0053-notes/11-second-example-divergence-and-provisional-spine.md)) and the
science/hardware self-driving-lab stress test
([note 12](0053-notes/12-third-example-science-hardware-divergence.md)), plus the recursion &
resource-management research backing Decisions 1 and 4
([note 13](0053-notes/13-recursion-and-resource-management-research.md)), and the
coordination-topology & scale research backing Decision 5
([note 14](0053-notes/14-coordination-topology-and-scale-research.md)). Per the RFC-0048 D9
series-execution standard, this effort appends its own
resolve-vs-surface sample reads to [`0048-notes/09`](0048-notes/09-gap-resolutions.md) and
reconciles its drift back into RFC-0048 in the same change (see Follow-on artifacts).

## Open questions

**No open questions remain.** The divergence design call surfaced by the skill-coverage pressure
test is **promoted to Decision 6** (the exploratory scaffold). The two
mechanics/validation-rigor questions this RFC originally surfaced are resolved per their
recommended defaults (they were never genuine value/scope/conflict calls — the parent
pre-decided those in D7/D8 + note 09; per the note-09 sample, a child whose parent settled the
value calls *resolves*, it does not re-litigate). Recorded with where each landed:

1. **Validation rigor — resolved.** The implementing spec **must** run **one
   structurally-different second example** that **forces a cap hit** (exercising the
   modelled-not-run O12 stall path) — this is a spec gate. A full live on-`omnigent`
   end-to-end run is a **nice-to-have, not a spec gate**, because the contract is
   harness-neutral by design and the sidecar was already prototyped in omnigent's storage
   form. Folded into § Evidence and the Follow-on spec bullet.
2. **Sidecar schema home — resolved.** The schema *definition* is a **`references/` file
   carried in the producing `discovery-loop` skill** (`product-engineering`, user scope; the
   `security-checklists/references/` shape), **not** a self-discovered skill, **not**
   duplicated prose in `work-loop`, and **not** a repo-scope `core` doctrine file. There is no
   shared cross-pack schema layer: child-4's lint, RFC-0049, and `work-loop` read produced
   `_state/` instances by convention + a `schema_version` stamp rather than importing the
   definition. Folded into Decision 2 (§ *Schema home*); revised per RFC-0048 § Amendments
   2026-06-26.
3. **Divergence + validation scaffold — promoted to a decision (no longer open).** Originally
   surfaced here as an open design call (the all-convergent loop has no divergence stage, and
   *converged ≠ validated*); the dogfood second examples
   ([note 11](0053-notes/11-second-example-divergence-and-provisional-spine.md),
   [note 12](0053-notes/12-third-example-science-hardware-divergence.md)) reproduced the failure and
   informed a concrete resolution, so it is now **Decision 6** (the exploratory scaffold: divergence
   → convergence → provisional-spine-with-validation-hooks), with its reuse-first skill/agent
   inventory specified there.

(The outer-cap default values are *decided* in Decision 4 — tunable defaults, recommended 12
rounds + the adopter's omnigent `cost_budget` — so they were never an open question here.)

## Follow-on artifacts

Filled in on acceptance.

- **ADR:** record "the upstream coordinator is `discovery-lead` (agent) + `discovery-loop`
  (skill) + a carried sidecar-schema contract (in the skill, not `core`) — no new runtime
  engine, spike-confirmed; the sidecar is the connectedness verifier" (the sibling of
  RFC-0041's ADR-0031 / RFC-0049's coordinator ADR).
- **Spec:** `docs/specs/coordinator-contract/` (or `discovery-loop/`) — the `discovery-lead`
  agent def + the `discovery-loop` skill (the gate state machine, the rejection/recovery +
  cascade-invalidation transition, the cap), **AC0 the carried sidecar-schema `references/`
  file** (in the skill, not a `core` doctrine file — RFC-0048 § Amendments 2026-06-26),
  **`product-engineering`'s own user-scope design reviewers** (not a mode-edit to `core`'s
  code reviewers), the second-example validation run
  (forcing the O12 cap-stall path), the **§ Security & integrity contract ACs** (verdict
  write-authority; append-only-attested decision log; non-degradable security lens on a
  boundary; lens-write integrity; cascade circuit-breaker; `reversibility-class`
  enumeration), and the G3 / self-coverage-gate / traceability-lint (incl. its root→leaf
  reachability AC) / backlog seams, **and the spec→discovery `Discovery:` up-edge (DRIFT-G —
  next bullet)**.
- **Spec→discovery up-edge (DRIFT-G) — folded in here.** RFC-0053's implementing spec **owns**
  the `new-spec` `Discovery:` up-edge header + the discovery-artifact `type:` markers (a
  spec-format addition in `docs/CONVENTIONS.md` § 4 + the `new-spec` skill, **not** operating-model
  doctrine). `discovery-loop` is the **consumer** of that up-edge (the brief/spec→discovery edge
  the traceability lint walks at G3), so its implementing spec is the right home for the producer.
  Producer-before-consumer: `new-spec` emits the header + markers **first**, and only then is
  child-4's traceability lint wired **fail-closed (`--strict`)** at the G2/convergence gate — the
  `--strict` flip is therefore also sequenced here, downstream of the header landing (until then
  the lint stays warn-only; specs without the header are warnings, not failures). This **resolves
  RFC-0048 acceptance blocker #4** and discharges the previously generic "spec-metadata / `new-spec`
  follow-on owner" (RFC-0048 § Amendments 2026-06-29; rollout-table + reconciliation-state rows
  now name RFC-0053's implementing spec).
- **`discovery-loop` ↔ self-coverage gate:** wire RFC-0051's gate as the pre-G2 phase (the
  seam RFC-0051 specified, this RFC's consumer).
- **Loop-skill doctrine (not a CONVENTIONS edit):** the two-loop split (discovery vs delivery) +
  the surfacing predicate's stall clause are carried in the **`discovery-loop` skill doctrine**
  (`product-engineering`), as this loop's share of the operating model — not a CONVENTIONS
  operating-model section (RFC-0048 § Amendments 2026-06-29, *operating-model doctrine relocated
  into the loop skills*).
- **Adoption & user guides (a release gate, not optional).** This RFC introduces a lot of new
  concepts (the coordinator contract; divergence → convergence → validation; *converged ≠ validated*;
  the recursive plan-tree; the requirements crosswalk; two new skills), so **building the pack is not
  enough — users must be able to adopt it.** The implementing spec **must author the Diátaxis guide
  set** (via the `new-guide` skill, under `docs/guides/product-engineering/…`) as an **acceptance
  criterion**, before the capability counts as shipped:
  - **Explanation** — what the discovery loop is and why: the coordinator contract, the
    divergence → convergence → validation arc, *converged ≠ validated*, the no-engine model, recursion.
  - **How-to** — run a discovery end-to-end (the one-prompt + targeted-prompt forms in § Usage);
    recurse into a sub-idea; and **fold in existing requirements** (the BRD/PRD/SRS/RTM crosswalk —
    how to seed the loop with a requirements doc and emit the enterprise format for sign-off).
  - **Tutorial** — a fully walked example (promote a note-11 / note-12-style walk into a learner's path).
  - **Reference** — the sidecar slots, the plan-tree template, and the skill / agent roster.
  The adoption risk (many new concepts) is as real as the build risk, so the guides are **gated, not
  follow-on-someday**; pair them with the changelog entry below.
- **Changelog:** `docs/product/changelog.md` `[Unreleased]` entry for the new
  `discovery-lead` / `discovery-loop` capability.
- **Pack version:** bump `product-engineering` (new agent + skill + the carried
  sidecar-schema `references/` file + the **plan-tree template asset** (Decision 2) + the discovery
  design reviewers + the **two D6 skills `explore-options` and `plan-validation`** + the
  `de-risk-intent` / `decompose-intent` extensions); `core` is **not** bumped for the schema (it no longer carries it — § Amendments
  2026-06-26); add `discovery-lead` / `discovery-loop` to the catalogue/marketplace manifest at
  spec time.
- **Foundation reconciliation (done in this PR):** RFC-0048 D7/D8 marked
  **spike-confirmed**; the loop-scoped-reviewer-roster change recorded as a tracked RFC-0048
  amendment (the CHARTER ceiling stays a `work-loop`/code-review cap); the note-09 sample-bank
  appended with this child's resolve-vs-surface reads (per the D9 series-execution standard).
  See the Amendments section of RFC-0048.
