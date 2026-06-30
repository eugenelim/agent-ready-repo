# RFC-0051: the self-coverage gate — non-skippable coverage doctrine, realized loop-appropriately (full in `discovery-loop`, a thin slice in `work-loop`)

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-25
- **Date closed:** 2026-06-29
- **Decision weight:** standard <!-- light | standard | heavy — additive loop doctrine: each controller carries the gate in its own skill at its own scope; no new pack, no cross-pack coupling, no new runtime, no new reviewer. It adds one refusal item to `work-loop`'s done-checklist (an additive doctrine change, not a checklist rewrite). It does *amend* one in-flight foundation decision (RFC-0048 D5's "a `core` library loaded by both controllers" packaging), recorded as a tracked amendment to that Open RFC, not a reversal of a frozen decision — so it stays below the governance-boundary line, the same standard-weight framing the analogous additive RFC-0055 convention used. -->
- **Related:** [RFC-0048](0048-autonomous-product-team-operating-model.md) (the foundation — this is **child 3**, Decision 5; the provisional foundation this drift-aligns back to) · [RFC-0041](0041-infra-aware-work-loop.md) + ADR-0031 (the `operational-safety` reference-library + reuse-the-reviewer precedent this RFC mirrors on *form* and *reuse* — *no new runtime, no new reviewer* — diverging only on *locus*: per-loop co-scoped copies, not one shared library, because this gate's consumers straddle the repo/user scope boundary) · [ADR-0042](../adr/0042-agent-additions-keyed-to-loop-and-work-type.md) (the reviewer-selection authority Decision 4 follows — agent additions keyed to loop and work type, superseding ADR-0023) · RFC-0025 (`work-loop` light/full mode + risk triggers — the right-sizing model this reuses) · `operational-safety` + `security-checklists` skills (the controller-loaded progressive-disclosure shape) · `work-loop` skill (the consuming controller; PLAN trio + declined-pattern register + REVIEW adversarial pass + the done-checklist refusal items this gate joins) · RFC-0048 D8 (`discovery-loop` / `discovery-lead` — the *second* controller, not built yet) · promoted research in RFC-0048's [`0048-notes/03`](0048-notes/03-autonomy-and-gate-economics.md) (the floor-raiser table) and [`0048-notes/09`](0048-notes/09-gap-resolutions.md) (the resolve-vs-surface sample-bank this seeds into a per-loop bank)

## Reviewer brief

- **Decision:** whether to (1) **own the cross-loop self-coverage goal + seam** here, and (2) realize it per loop with a **loop-appropriate share** — the **full seven-module design-convergence gate for `discovery-loop`** (its native altitude), and only the **net-new slice for `work-loop`**, because `work-loop`'s existing structure (REVIEW, Surface + DECIDE, the assumption trio + declined-pattern register) and its **already-progressive spec time** (light/full, RFC-0025) cover most of the gate. Per-loop co-scoped; no shared library; no cross-pack coupling; no new runtime; no new reviewer; non-skippable.
- **Recommended outcome:** accept.
- **Change if accepted:**
  - Establish the **goal** (raise autonomy between human gates via resolve-vs-surface) and the **cross-loop seam** (the resolve-vs-surface disposition + a non-skippable coverage record) as the invariant every loop conforms to.
  - **For `work-loop` — a thin edit, not a new gate.** Most of the gate already lives there (§ Inventory). Name its existing passes as the gate's steps (REVIEW *is* fresh-context-adversarial; the assumption trio + declined-pattern register *are* the pre-mortem hook; Surface + DECIDE *are* the resolve-vs-surface bones), and add only the **net-new**: a resolve-vs-surface **disposition record** and a **conditional domain-grounding** check, both at spec time / DECIDE under the **light/full progressive mode `work-loop` already activates at spec time**. Do **not** bolt the heavy design-convergence modules (the ones the § Inventory marks "not adopted") onto the build loop, and do **not** add a second right-sizing knob. One done-checklist refusal item (the disposition record).
  - **For `discovery-loop`** (RFC-0048 D8 / RFC-0053, not built) — adopt the **full seven-module gate** as its pre-convergence (G2) gate, in its own skill at user scope, right-sized by its own progressive mode. This is the **primary home** of the full design-convergence instantiation: the altitude where myopic-greedy commitment is the live risk and a design artifact exists to ground.
  - Make it **non-skippable** via a controller-gate phase + a done/converged-checklist refusal (doctrine + a mechanical coverage record), not a runtime lock — co-scoped with each controller so it is present wherever the controller runs.
- **Affected surface:** the `work-loop` skill — a **thin** SKILL.md edit (name the existing passes; add the disposition record + conditional domain-grounding at spec time / DECIDE; one checklist-refusal item) — **no new heavy reference modules under `work-loop`**; the cross-loop seam + the **full seven-module instantiation specified for `discovery-loop` to carry**; reuse of `adversarial-reviewer` / `devils-advocate`; a tracked amendment + refinement to RFC-0048 D5.
- **Stakes:** reversible — additive doctrine; no runtime, no new reviewer, no new pack; the `work-loop` edit degrades to the prior done-checklist if reverted.
- **Review focus:** (1) the non-skippable mechanism is genuinely non-skippable yet harness-neutral (controller-gate + checklist-refusal, never a self-discovered skill); (2) the **`work-loop` adoption is honestly scoped to net-new** — it names what already applies and attaches the thin remainder to the spec time that is *already* progressive, rather than bolting a convergence battery onto the build loop; (3) **`discovery-loop`, not `work-loop`, is the primary consumer of the full seven** — confirm the altitude is right; (4) per-loop co-scoping (not a shared `core` library) keeps `core` and `product-engineering` standalone.
- **Not in scope:** a new reviewer agent of any kind — and specifically no fourth *core-loop* lens (ADR-0042; the gate reuses each loop's work-type-keyed roster); a runtime lock; a shared cross-pack library or a dependency between `core` and `product-engineering`; a new standalone skill/pack for the gate; **the heavy design-convergence modules as new `work-loop` surface** (they are `discovery-loop`'s); a second right-sizing knob (reuse each loop's existing progressive mode); semantic scope-creep detection (RFC-0048 D6 / O10).

## The ask

**What self-coverage is (the goal).** Self-coverage is not a fixed checklist — it is a *goal*:
let each AI loop **proceed more autonomously by substituting rigorous checklists for what would
otherwise be surfaced to a human**. The discipline at its core is **resolve-vs-surface** — resolve
autonomously everything a referent or checklist can resolve; surface to the human only the
irreducible (value origination, irreversible risk, value conflict). The remaining steps are the
*vigorous checklist content* that makes more autonomous resolution safe (grounding, pre-mortem,
taxonomy, saturation, fresh-context review, scenario-variation). Every loop with a human handoff
realizes this goal — **with checklists appropriate to its own work**. This RFC owns the goal, the
**seam** (the goal + the resolve-vs-surface disposition + the non-skippable coverage record that
every loop's instantiation conforms to), and the **design-convergence instantiation** — the seven
modules below. It specifies the **full seven-module gate for `discovery-loop`** to carry as its
pre-convergence gate (wired by [RFC-0053](0053-the-discovery-loop.md)), and wires the **goal + seam
into `work-loop` as a thin, loop-appropriate slice** — because most of the gate already lives in
`work-loop` and its spec time is already progressive (§ Inventory). `release-loop` realizes the same
goal + seam through a deploy-appropriate *composite* ([RFC-0049](0049-the-release-loop-and-company-os.md)).
See *Consumers & sequencing*.

**Recommendation (BLUF).** Own the self-coverage **goal + cross-loop seam** here, and realize it
per loop as **per-loop controller doctrine** (each loop carries its own copy at its own scope —
no shared library, no cross-pack coupling, no new runtime, no new reviewer) with a
**loop-appropriate share**:

- **`discovery-loop`** is the **primary consumer of the full seven-module design-convergence gate**
  (domain-grounding · pre-mortem · taxonomy-walk · saturation-declaration · fresh-context-adversarial
  · scenario-variation · resolve-vs-surface), carried as progressive-disclosure reference modules
  under its own skill and run as its pre-convergence (G2) gate. That altitude — a design artifact
  being converged, myopic-greedy commitment as the live risk — is where the battery earns its place.
- **`work-loop`** adopts the **same goal + seam with a thin slice, not the full gate**. Most of the
  gate already lives in `work-loop`, and its spec time is **already progressive** (light/full,
  RFC-0025): REVIEW *is* fresh-context-adversarial, Surface + DECIDE *are* the resolve-vs-surface
  bones, the assumption trio + declined-pattern register *are* the pre-mortem hook, and the light/full
  knob already right-sizes how much spec convergence runs. The only net-new is a resolve-vs-surface
  **disposition record** and a **conditional domain-grounding** check, attached at spec time / DECIDE
  under that existing progressive mode — never a convergence battery bolted onto the build loop, never
  a second knob.

It is **non-skippable** because it runs in the **loop controller's own context** as a named gate
phase (or, for `work-loop`, as named existing phases plus one done-checklist refusal item), *not* a
skill the controller may discover. Co-scoping guarantees it is present wherever each controller runs.

**Why per-loop and not a shared `core` library.** RFC-0048 D5 framed this as "a reference
library in `core`, loaded by both loop controllers." That packaging does not survive the scope
split the operating model itself draws: `work-loop` is repo-scope (it lives in `core`), but
`discovery-loop` is **user-scope and possibly pre-repo** (RFC-0048's operating-model section — a
PM/designer environment). A repo-scope `core` library is simply absent when discovery runs
outside a `core`-installed repo, and a *non-skippable* gate whose depth can be absent is a
contradiction — it would have to detect-and-degrade, the very move RFC-0048 reserves for the
discovery *reviewers'* depth (`security-checklists` / `operational-safety` "when present, else a
baseline") and which is self-defeating for the floor-raiser itself. The fix is **not** to
relocate one shared copy to a broader scope: a whole new pack for one markdown gate is overkill,
and coupling `core` to `product-engineering` (either direction) couples two packs that should
each stand alone. The honest fix is to see that, *unlike* `operational-safety`, this gate runs in
the **controller's own context** and therefore needs no external shareable skill at all. Each
loop carries the method as its own doctrine; "loaded by both controllers" means **both loops run
the same method**, not both read one file. RFC-0048 D5 is amended to say so (§ Follow-on
artifacts → foundation reconciliation; recorded at RFC-0048 § Amendments).

**Why now (SCQA).** *Situation:* RFC-0048 decided the operating model and named the
self-coverage gate (Decision 5) as the floor-raiser that fixes the knowing-doing gap —
the agent failing to apply knowledge it already had, so errors compound unwatched between
human gates ([`0048-notes/03`](0048-notes/03-autonomy-and-gate-economics.md)). *Complication:*
RFC-0048 *decided* the gate and named its packaging — "a reference library in `core`, loaded by
both controllers" — but **built nothing**, and that packaging does not survive contact with the
operating model's own scope split: the second controller (`discovery-loop`) is user-scope and
possibly pre-repo, where a repo-scope `core` library is absent. The parent is also explicit that a
self-discovered skill is the wrong vehicle (the agent could skip it at its discretion, defeating
the whole point), and `operational-safety`'s loading mechanism (inline into a *subagent* brief)
does not transfer either, because this gate runs in the *controller's own* reasoning context,
where there is no brief to inline into. *Question:* how do we ship a gate that is genuinely
non-skippable, harness-neutrally, **available wherever either controller runs**, without a runtime
lock, without a fourth reviewer, and without coupling two packs that should stand alone?

**Decisions requested.**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Ship it as **per-loop controller doctrine with a loop-appropriate share** — each loop carries its own copy at its own scope (no shared library, no cross-pack coupling, never a self-discovered skill); **`discovery-loop` carries the full seven-module gate**, **`work-loop` adopts only the net-new slice** atop the passes it already runs? | Adopt (**amends + refines RFC-0048 D5**) | Dissolves the scope-coupling a shared `core` library hits when `discovery-loop` runs user-scope/pre-repo; keeps each pack standalone; most of the gate already lives in `work-loop`, so the full battery is `discovery-loop`'s, not the build loop's | RFC accept | Confirm the per-loop shape, the work-loop/discovery share, and the amendment to D5 |
| D2 | Make it non-skippable by a controller-gate + checklist-refusal mechanism — doctrine + a mechanical coverage record, not a runtime lock — enforced per loop? | Adopt | The one design question RFC-0048 left to the child; co-scoping guarantees the gate is present wherever the controller runs (no cross-scope absence to degrade around) | RFC accept | Confirm the non-skippable mechanism is genuine yet harness-neutral |
| D3 | Decompose the **design-convergence instantiation** into seven progressive-disclosure step-modules + a per-loop sample-bank — **adopted in full by `discovery-loop`**, while **`work-loop` adopts only the net-new slice** (the resolve-vs-surface disposition record + conditional domain-grounding) atop the passes it already runs, under its existing progressive spec time? | Adopt | The module shape keeps each step lean; the full battery is design-convergence work that fits `discovery-loop`'s altitude, not every loop | RFC accept | Confirm the seven-module decomposition + the work-loop/discovery split |
| D4 | No new reviewer — the fresh-context adversarial step dispatches **the reviewer(s) the loop and work type warrant, selected per [ADR-0042](../adr/0042-agent-additions-keyed-to-loop-and-work-type.md) from each loop's existing roster**, in a fresh context — not a fixed reviewer? | Adopt | ADR-0042 (supersedes ADR-0023): reviewers are keyed to loop + work type, not a global pair; this gate reuses each loop's roster and adds no agent — and no fourth *core-loop* lens (the cap ADR-0042 carries forward) | RFC accept | Confirm no new reviewer and no fourth core-loop lens; selection follows ADR-0042 |
| D5 | Right-size by reusing each loop's **existing** progressive mode — `work-loop`'s light/full spec time (RFC-0025) and `discovery-loop`'s own — rather than inventing a second knob? (`work-loop` *already* activates progressive mode at spec time; the gate just uses it.) | Adopt | The gate must not become ceremony; the right-sizing knob already exists at spec time, so reuse it | RFC accept | Confirm right-sizing reuses the existing per-loop progressive mode |
| D6 | Seed a **per-loop** resolve-vs-surface sample-bank — append-only within each loop's own scope, not a shared cross-scope bank? | Adopt | The lens hits the right call only ~half the time without an externalized scaffold; per-loop keeps the bank co-scoped with its controller and avoids cross-pack coupling | RFC accept | Confirm the per-loop sample-bank |

## Problem & goals

**Diagnosis.** RFC-0048 Decision 5 decided *that* the self-coverage gate exists and *what*
it must contain, and proposed its packaging — "a reference library + doctrine
(the `operational-safety` shape) in `core`, loaded by both loop controllers, right-sized
light/full — *not* a self-discovered skill." What it did **not** do — because it builds
nothing — is settle two things that make the principle real, and on the second the proposed
packaging is wrong.

*First: how a gate is non-skippable when it runs in the controller's own context.*
`operational-safety` earns its non-skippability cheaply: its consumer is a *subagent* whose
`tools:` has no Skill tool, so the orchestrator inlines the modules into the subagent's brief as
prompt text and the subagent never has to find the library (`operational-safety` SKILL.md:21-48).
The self-coverage gate has no such consumer — it runs in the **loop controller**, the main agent
that has *already loaded* `work-loop` (or, later, `discovery-loop`). There is no brief to inline
into, and the same "skill discovery is model-invoked, so it can be skipped" hazard the parent
flagged applies to the controller too. The gate therefore needs its own non-skippability
mechanism (Decision 2).

*Second: where the depth lives — and the parent's answer (`core`) does not survive the operating
model's own scope split.* `work-loop` is repo-scope (it lives in `core`); `discovery-loop` is
**user-scope and possibly pre-repo** (RFC-0048's operating-model section — "a PM/designer
environment, possibly pre-repo"). A repo-scope `core` library is reachable by `work-loop` but
**absent** when `discovery-loop` runs outside a `core`-installed repo. A *non-skippable* gate
whose depth can be absent is a contradiction: it would have to detect-and-degrade — exactly the
posture RFC-0048 reserves for the discovery *reviewers'* depth ("`core`'s depth libraries are
optional detect-and-degrade enhancers"), and exactly the posture that is self-defeating for the
floor-raiser itself. Relocating one shared copy to a broader scope does not fix it cleanly: a new
pack for one markdown gate is overkill, and a `core`↔`product-engineering` dependency couples two
packs that should each stand alone. The resolution is that this gate, unlike `operational-safety`,
runs in the controller's own context and so needs no shared external skill — **each loop carries
its own co-scoped copy** (Decision 1). That makes the depth *guaranteed present wherever the
controller runs*, which is the property a shared `core` library could never give the user-scope
`discovery-loop`.

The failure this prevents is concrete and measured: agents exhibit *myopic greedy
commitment* — chain-of-thought locks in early decisions and builds on them confidently;
the agent's own critique runs in the same anchored context and won't catch it
([`0048-notes/03`](0048-notes/03-autonomy-and-gate-economics.md), citing arXiv:2601.22311).
Every token spent after a wrong high-altitude commitment is wasted, and the agent won't
know. The gate raises the floor *between* the human gates so fewer errors compound
unwatched — but only if it actually runs, every time, which is what "non-skippable" has to
deliver.

**Goals.**
- Ship the gate as the RFC-0041 idiom — **doctrine + reference modules carried by the loop +
  reuse of the existing reviewers** — so it is a *habit*, not a runtime (CHARTER Principle 3).
- Make it **genuinely non-skippable** harness-neutrally, and **guaranteed present wherever the
  controller runs** (co-scoped, never detect-and-degrade), with an honest account of where that
  is doctrine-plus-a-mechanical-check versus structurally enforced.
- Keep each loop's pack **standalone** — the gate must not couple `core` to
  `product-engineering`; each carries its own copy, so either installs without the other.
- Keep each step **lean and load-only-what-applies** via progressive disclosure, so the gate is
  proportionate (in `discovery-loop`, a light pass pulls the core; a multi-discipline convergence
  pulls all seven) and the loop's SKILL.md stays lean.
- Give the **resolve-vs-surface lens** a durable home **per loop**, so the calibration that lives
  in one RFC note becomes a living scaffold each loop accretes in its own scope.

**Non-goals** (could-have-been goals, deliberately dropped).
- *A shared cross-pack library, or a dependency between `core` and `product-engineering`.* Each
  loop carries its own copy; neither pack depends on the other. This **amends** RFC-0048 D5's "one
  library in `core`, loaded by both controllers" (§ Follow-on artifacts → foundation
  reconciliation).
- *A new standalone `self-coverage` skill or pack.* The gate is doctrine + reference modules under
  the consuming loop's own skill — a whole pack for one markdown gate is overkill.
- *A self-discovered skill.* Explicitly rejected by RFC-0048 D5; a trigger-matched skill is
  skippable at the agent's discretion, which defeats a *gate*.
- *A new reviewer agent — of any kind.* Per [ADR-0042](../adr/0042-agent-additions-keyed-to-loop-and-work-type.md)
  the core `work-loop` code-review gate stays capped at its three lenses (no fourth core-loop lens, a
  charter question this RFC does not raise), and this gate adds no agent in any loop: the
  fresh-context step reuses each loop's existing, work-type-keyed roster (Decision 4).
- *An executable gate runtime / lock.* A program that structurally blocks the agent from
  writing past the gate is runtime infrastructure (Principle 3) and harness-specific; we
  ship the doctrine such a harness enforces, not the harness.
- *Building `discovery-loop`.* The full gate's primary home is RFC-0048 D8's child (wired by
  RFC-0053); this RFC wires the **thin `work-loop` slice** and specifies the cross-loop seam (goal +
  resolve-vs-surface + the non-skippable record) plus the **full seven-module design-convergence
  instantiation** that `discovery-loop` will carry in its own copy.
- *The Domain Framing + Scope Boundary typed artifacts and the traceability lint* (RFC-0048 D4/D6, sibling
  children). The domain-grounding step *consumes* a Domain Framing where one exists and
  degrades to in-gate grounding where it does not; it does not define that artifact.

## Proposal

Cascaded under the requested decisions.

**Decision 1 — per-loop controller doctrine, not a shared library.** The gate ships as a
**named phase in the consuming loop's own SKILL.md** plus **progressive-disclosure reference
modules under that skill** — `references/self-coverage/<step>.md` under `work-loop` today, and
under `discovery-loop` when RFC-0048 D8 builds it. The gate phase carries a lean Module index
(the universal method + the routing authority) over the modules that hold the depth. No new
standalone skill, no new pack, and **no dependency between `core` and `product-engineering`** —
each loop carries its own copy and either pack installs without the other. No executable code
ships; the artifact is prose + a routing table, exactly as RFC-0041 Decision 1 framed
`operational-safety`. This clears Principle 3 the same way (a depth library a controller reasons
from is a habit, not infrastructure) and goes further on Principle 1: because the gate runs in the
**controller's own context** — not a subagent brief — it needs no external shareable skill to
inline from; the loop that already loaded its own SKILL.md simply reads its own reference modules
on demand.

*Why not the shared `core` library RFC-0048 D5 named.* A repo-scope `core` library is absent when
`discovery-loop` runs user-scope/pre-repo (the operating-model section's "PM/designer environment,
possibly pre-repo"). Relocating one copy to a broader scope means either a whole new pack for one
markdown gate (overkill) or coupling two packs that should stand alone. Per-loop doctrine
dissolves the problem: "loaded by both controllers" becomes "both loops run the same method," and
the depth is guaranteed present wherever each controller runs. (Amends RFC-0048 D5 — § Follow-on
artifacts → foundation reconciliation.)

**Decision 2 — the non-skippability mechanism (load-bearing).** The gate is non-skippable
by three layers, named honestly from strongest-available to the harness-neutral floor:

1. **A named, required gate phase in the consuming loop's doctrine.** `work-loop`'s SKILL.md
   (and later `discovery-loop`'s) names the self-coverage gate as a phase the loop *runs*,
   not a skill it *may discover* — the plan-mode lesson that a gate works when it is a hard
   state, not an instruction ([`0048-notes/03`](0048-notes/03-autonomy-and-gate-economics.md):82-90).
   The controller reads its own reference modules directly because it is *already running the loop
   that mandates the gate*, and those modules are co-located under that very skill; there is no
   discretionary "is this skill relevant?" judgment of the kind the parent warned about, and — the
   property a shared `core` library could not give — **no cross-scope absence to degrade around**,
   because the gate is co-scoped with its controller and ships with it.
2. **A coverage-record refusal in the done/converged checklist.** The gate emits a
   **coverage record** (the domain-grounding table, the pre-mortem scenarios tagged to the
   design, the taxonomy-walk paragraphs, the saturation declaration, the fresh-context
   findings and their resolutions, the scenario-variation reads, and the resolve-vs-surface
   disposition of every open item). `work-loop`'s end-of-session checklist (SKILL.md:675-713)
   gains one refusal item: *do not declare done until the coverage record exists and every
   fresh-context finding is resolved* — the same shape as the existing reviewer-clean and
   doc-drift-invariant refusals. This is the harness-neutral teeth: a mechanical artifact
   whose absence is detectable, joining refusal items the loop already enforces.
3. **Structural enforcement where the harness offers it.** On a harness that enforces gates
   outside the prompt (omnigent's policy gates; a Claude-Code plan-mode-style read-only
   state), the same gate phase is registered as a structural checkpoint the agent cannot
   write past — the strongest form, and the one note 03 holds up as the aspiration. We do
   not *depend* on it (the harness-neutrality posture — RFC-0041 P4, which named Claude
   Code primitives as accelerant, never dependency).

Layer 3 is the ideal, layer 1+2 is the floor, and the RFC is explicit that harness-neutrally
the gate is doctrine + a mechanical coverage-record check — strong, not absolute. That
honesty is the same posture `operational-safety` ships under ("if the delegated gate is
absent, do not silently skip — reason it best-effort and flag the gap").

**Decision 3 — the seven step-modules + the per-loop sample-bank, progressively disclosed.**
These seven define the **full design-convergence gate `discovery-loop` carries**; **`work-loop`
adopts only the net-new subset** (the resolve-vs-surface disposition record + conditional
domain-grounding — see § Inventory). Each step is a `references/self-coverage/<step>.md` module
**under the consuming loop's skill**;
the gate phase's Module index in that loop's SKILL.md routes by **mode** (which steps light vs
full loads) and, for scenario-variation, by **which axes the design crosses** — progressive
disclosure, loaded on demand, never a flat march and never all inlined into the SKILL.md. The
seven, with the failure each guards and its grounding:

| Module | The step | Blocks declaring covered if… | Grounded in |
|---|---|---|---|
| `domain-grounding` | a domain-grounding table — one row per load-bearing domain claim, each grounded in a referent (a Domain Framing where RFC-0048 D4 supplies one; else in-gate `research`) | any cell empty or "assumed" | note 03 table (WHO-checklist −36% complications); RFC-0048 D4 |
| `pre-mortem` | prospective hindsight — assume it shipped and failed; enumerate failure modes, each tagged to a design element | < N scenarios, or any untagged | note 03 (+30% failure ID); Klein prospective hindsight |
| `taxonomy-walk` | an external dimension register walked one paragraph each (a substantive paragraph, never yes/no) | any dimension blank | note 03 (recall→recognition; external scaffolds beat free recall) |
| `saturation-declaration` | a grounded-theory stop rule — declare convergence only when a full pass surfaces no new open question and no invalidating edit | declaration absent | note 03; `research-project-check`'s stop-signal (RFC-0048 O6) |
| `fresh-context-adversarial` | dispatch the **work-type-appropriate reviewer(s)** (ADR-0042 — `adversarial-reviewer` for code, `design-reviewer` / `devils-advocate` for a design/research artifact, the discovery roster in `discovery-loop`) in a **fresh context** so the reviewer is not anchored to what was just produced | any finding unresolved | note 03 (plan-mode fresh-context lesson); reuse per ADR-0042, no new reviewer |
| `scenario-variation` | re-run the design against a varied **domain / stakes-level / scale / platform / harness** — orthogonal-axis modelling, loaded only for the axes in play | a crossed axis left unvaried | RFC-0048 D5 (catches stakes- and conflict-class gaps without the human) |
| `resolve-vs-surface` | a pass over every open item — solve referent-groundable items and cite the referent; surface only value-origination / irreversible-risk / value-conflict (or a referent that genuinely failed) | any open item neither resolved-with-referent nor surfaced-with-reason | RFC-0048 D5; note 09 sample-bank |

The first five are note 03's original floor-raiser table; scenario-variation and
resolve-vs-surface are RFC-0048 D5's two additions. The **per-loop sample-bank**
(`references/self-coverage/resolve-vs-surface-sample-bank.md` under the consuming loop's skill) is
the calibration the `resolve-vs-surface` module points to — see Decision 6.

**Decision 4 — no new reviewer; selection follows ADR-0042.** The `fresh-context-adversarial`
module *invokes* whichever reviewer(s) the **loop and work type** warrant and **adds none** — the
selection rule is [ADR-0042](../adr/0042-agent-additions-keyed-to-loop-and-work-type.md) (agent
additions keyed to loop and work type, superseding ADR-0023's narrower three-lens framing), not a
fixed reviewer. In the `work-loop` code-review gate that is the core lenses the diff warrants
(`adversarial-reviewer` always; `security-reviewer` / `quality-engineer` as the work crosses their
boundary, exactly as REVIEW already routes them) — and the gate adds **no fourth core-loop lens**,
the cap ADR-0042 carries forward. In `discovery-loop` it is that loop's own design-time roster
(`discovery-threat-reviewer`, `discovery-reliability-reviewer`, the reused `design-reviewer`, and
the `experience-reviewer` — RFC-0048 §lens-team roster, RFC-0050 D7); for a research or design
artifact, `design-reviewer` / `devils-advocate`
([`0048-notes/06`](0048-notes/06-pack-delta-and-orchestration.md)). The novelty is not a new
agent but a *named obligation* to run the work-appropriate reviewer in a separated context, which
`work-loop`'s REVIEW already does — the gate formalizes and names it rather than duplicating it.

**Decision 5 — right-size by each loop's existing progressive mode (no second knob).** The gate
reuses each loop's **own** light/full distinction rather than inventing one:

- **`work-loop`** already activates a light/full progressive mode **at spec time** (RFC-0025):
  full mode authors a full `new-spec`, light mode a lean inline spec. Its self-coverage share —
  the resolve-vs-surface **disposition record** plus a **conditional domain-grounding** check —
  attaches to that spec time and is governed by the same knob; it is small in both modes by
  construction, so there is nothing extra to right-size. The existing light-mode **bounded**
  `adversarial-reviewer` pass (escalate-to-full on a surviving Blocker — SKILL.md:94-97) is the
  fresh-context step it already runs.
- **`discovery-loop`** reuses its **own** progressive mode for the full seven: light loads the
  always-on core (`domain-grounding` + `resolve-vs-surface` + a single bounded
  `fresh-context-adversarial` pass); full loads all seven — `pre-mortem`, `taxonomy-walk`,
  `saturation-declaration`, and `scenario-variation` across the axes the design crosses, with the
  `fresh-context-adversarial` pass **iterated to clean** (not bounded).

This keeps the gate proportionate and inherits right-sizing from each loop instead of re-deciding
it — and, for `work-loop`, confirms the point that drove this RFC's framing: the progressive knob
already exists at spec time, so the gate plugs into it rather than adding one.

**Decision 6 — a per-loop sample-bank.** The resolve-vs-surface sample-bank currently lives
in [`0048-notes/09`](0048-notes/09-gap-resolutions.md) as a "living artifact — expectation
set for the whole series." It is the calibration the `resolve-vs-surface` module points to —
without it the lens hits the right call only ~half the time (note 09). This RFC homes it
**per loop**: each controller seeds and accretes its own bank under its own skill
(`references/self-coverage/resolve-vs-surface-sample-bank.md` — under `work-loop` in `core`/repo
today; under `discovery-loop` when D8 builds it), append-only within that loop (a sample that
stops holding earns a *new* entry citing the old, never an edit — the
`docs/knowledge/patterns.jsonl` discipline, CONVENTIONS.md:803-832).

A per-loop bank is the consequence of per-loop doctrine: with no shared cross-scope file there is
no shared bank to append to, and a build-track done-declaration and a discovery-track convergence
accrete genuinely different reads anyway. RFC-0048 D5 / note 09's "the bank **graduates** into the
shared library" therefore becomes "it **seeds the `work-loop` bank** now; the discovery bank is
seeded when its loop is built" — recorded as a foundation reconciliation (§ Follow-on artifacts).

*Migration & the projection seam.* The `work-loop` bank ships **as pack content**, so an adopter's
installed copy is theirs to append to in place. For **this** repo (which self-hosts the pack),
appends go to the source under `packs/core/.apm/skills/work-loop/references/self-coverage/` and
reach the projected `.claude/` copy via `make build-self` — the same source-edit-then-rebuild
discipline every pack-content change follows here. Until RFC-0048 is **Accepted**, appends continue
in note 09 (its pre-seeding home); the seeding move itself is a follow-on of *this* RFC's
implementing spec. The build-self/projection mechanics are a spec-time detail, not an open design
question (OQ2 records the recommended default).

*Inventory — what `work-loop` already covers, what's net-new, and what it does **not** adopt
(Principle 2 — no duplication).* The gate does **not** re-implement REVIEW, and it does **not** bolt
a design-convergence battery onto the build loop. The load-bearing fact: `work-loop` **already has a
progressive spec time** — its PLAN phase authors the spec (full mode → `new-spec`; light mode → a
lean inline spec), and the light/full knob (RFC-0025) already right-sizes how much spec ceremony
runs. So the gate needs **no new right-sizing knob**, and any convergence depth `work-loop` wants
attaches to **full-mode spec time**, already gated — never to EXECUTE, never to every loop. The
honest per-module inventory:

| Module | In `work-loop` today | `work-loop` adopts | `discovery-loop` adopts |
|---|---|---|---|
| `fresh-context-adversarial` | **already applies** — *is* the REVIEW pass (and the pre-EXECUTE spec/plan pass at spec time) | name it; add nothing | full |
| `resolve-vs-surface` | **bones present** — the `Surface` verb + DECIDE's apply/defer routing ("every Concern/Nit resolves into one of the two") | **net-new: the disposition *record*** (the artifact, not the routing) | full |
| `pre-mortem` | **hook present** — PLAN's assumption trio + declined-pattern register | keep the hook; not a separate module | full prospective-hindsight |
| `domain-grounding` | partly served by the EXECUTE contract-grounding gate (API contracts, not domain claims) | **net-new but conditional** — fires when the build rests on an ungrounded load-bearing domain claim; degrades to "the spec already grounds this" | full |
| `taxonomy-walk` | — | **not adopted** — design-convergence; if full-mode spec time wants it, pull it under the existing light/full knob, not a new gate | full |
| `saturation-declaration` | terminates on gates + review + caps, not "no new open question" | **not adopted** — a design-convergence stop rule, same disposition | full |
| `scenario-variation` | — | **not adopted** — design-convergence, same disposition | full (axes the design crosses) |

So `work-loop`'s adoption is **thin**: name the passes it already runs, and add two net-new items at
spec time / DECIDE — the resolve-vs-surface **disposition record** and a **conditional
domain-grounding** check — both governed by the progressive mode it already carries. The full
seven-module design-convergence gate is **`discovery-loop`'s**, at its native altitude (next). This
is the same inventory-diff argument RFC-0041 used to clear Principle 2 for `operational-safety`,
applied honestly: supply only what the loop lacks.

*Consumers & sequencing — three loops, a goal realized loop-appropriately.* Self-coverage is a
**goal** every loop with a human handoff realizes (§ The ask → *What self-coverage is*). The seven
modules are its instantiation for **generative design-convergence** work, where myopic-greedy
commitment is the live risk and a design artifact exists to ground — that altitude is
**`discovery-loop`'s**, not the build loop's. So:

- **`discovery-loop`** (RFC-0048 D8, not built) is the **primary consumer of the full seven-module
  gate**: it runs all seven as its pre-convergence (pre-G2) gate — where
  [`0048-notes/05`](0048-notes/05-judgment-decomposition-and-phases.md):51 places it — carrying its
  **own** copy under its own skill in `product-engineering`, right-sized by its own progressive mode.
  This is where the design-convergence battery earns its place. Wired by
  **[RFC-0053](0053-the-discovery-loop.md)** (the discovery-loop RFC), which consumes this RFC's seam
  and the seven-module instantiation specified here.
- **`work-loop`** (in `core`, repo-scope) realizes the **same goal + seam with a thin,
  loop-appropriate share** — it does **not** carry the full seven. Most of the gate already lives in
  `work-loop` (§ Inventory): REVIEW *is* fresh-context-adversarial, Surface + DECIDE *are* the
  resolve-vs-surface bones, the assumption trio + declined-pattern register *are* the pre-mortem hook,
  and its **light/full progressive spec time already right-sizes** how much convergence runs. The
  net-new is two items at spec time / DECIDE: the resolve-vs-surface **disposition record** and a
  **conditional domain-grounding** check. Wired **here** as a thin edit.
- **`release-loop`** ([RFC-0049](0049-the-release-loop-and-company-os.md)) realizes the **same goal
  and the same seam** (resolve-vs-surface + the non-skippable coverage record) through a
  **different, deploy-appropriate instantiation** — a *composite*, not a single checklist. No one
  reference library covers it: `operational-safety` is the **reliability** lens only; the release
  loop's gates also span **security** (`security-reviewer` / `security-checklists`) and **change
  quality** (`quality-engineer`), with the **automated convergence policy** (canary + e2e coverage
  + flake — RFC-0049 D6) as the stop-rule and the **minimum-regret carve** (RFC-0049 D2) as the
  resolve-vs-surface disposition. Self-coverage's contribution here is the **meta-discipline that
  composes them** — run every loop-appropriate checklist rigorously and apply resolve-vs-surface
  *across* them so the carve surfaces only the irreducible (raising deploy autonomy). It does
  **not** carry the seven design-convergence modules — there is no design artifact to ground and it
  converges empirically on telemetry. RFC-0049 names that instantiation; this RFC owns the goal +
  seam it conforms to.

This RFC specifies the **seam** — the goal + the resolve-vs-surface disposition + the non-skippable
mechanism — as the cross-loop invariant each loop implements in its own co-scoped copy, plus the
**full seven-module design-convergence instantiation** that `discovery-loop` carries; it does
**not** ship a file any other loop imports. That satisfies RFC-0048 D5's "every loop controller
runs it" the honest way: each loop runs the same *goal* through a **loop-appropriate** instantiation
— the full seven where the altitude warrants it (`discovery-loop`), a thin slice where the loop
already covers the rest (`work-loop`) — neither pack depending on the other.

## Options considered

**Axis 1: what artifact form is the gate, and how is it enforced non-skippably?** This axis
exhausts the space because any answer must name both a *form* (prose doctrine / skill /
reviewer / runtime) and an *enforcement* (discretionary / mechanical-record / structural).
Options are MECE along it; prior art grounds each.

| Option | Form · enforcement | Verdict |
|---|---|---|
| **A. Do nothing** — leave the steps as scattered prose in `work-loop` | none · discretionary | Cost of delay: the knowing-doing gap (note 03) recurs on every product; the steps stay unnamed, unrouted, and skippable by omission. Rejected. |
| **B. Self-discovered skill** the agent invokes when it judges it relevant | skill · discretionary | A trigger-matched skill is skippable at the agent's discretion under anchoring — which defeats a *gate*. **Explicitly rejected by RFC-0048 D5.** Rejected. |
| **C. Controller doctrine + progressive-disclosure reference modules** ★ | controller-co-located reference modules + doctrine · mechanical-record (+ structural where the harness offers it) | **Recommended.** The `operational-safety` / RFC-0041 idiom for *form and reuse* — but the modules sit under the consuming loop's own skill, not in a shareable standalone library (Principle 1: the controller reads its own context, never an external skill). Clears Principles 1–3; non-skippable via the done-checklist refusal the loop already enforces. (Locus settled by Axis 2 → per-loop.) |
| **D. A new reviewer agent** dedicated to coverage | new agent · discretionary | Fails [ADR-0042](../adr/0042-agent-additions-keyed-to-loop-and-work-type.md): in the core loop it would be a fourth *core-loop* lens (a charter question the ADR does not pre-authorize), and in any loop it adds no value an existing work-type-keyed reviewer in a fresh context doesn't already give. The fresh-context step reuses them. Rejected. |
| **E. Executable gate runtime / lock** that structurally blocks writing past the gate | runtime · structural | The strongest enforcement, but it is runtime infrastructure (Principle 3) and harness-specific (the RFC-0041 P4 harness-neutrality posture). We ship the doctrine such a harness enforces, not the harness. Rejected as the *shipped* form; folded into Option C's layer 3 where the harness provides it. |

**Axis 2 (within C): where does the depth live, given two controllers in different scopes?**
`work-loop` is repo-scope (`core`); `discovery-loop` is user-scope/pre-repo
(`product-engineering`). Any answer must place the depth somewhere reachable by *both*, and a
*non-skippable* gate forbids "absent → degrade." This axis is MECE over *one shared copy* vs
*one copy per loop*.

| Option | Locus | Verdict |
|---|---|---|
| **C1. One shared copy in `core`** (RFC-0048 D5's stated packaging) | repo-scope, shared | Absent when `discovery-loop` runs user-scope/pre-repo; the gate would have to detect-and-degrade, which is self-defeating for the floor-raiser. **Rejected — this RFC amends D5.** |
| **C2. One shared copy in a new pack** at the broader (user) scope | user-scope, shared | Reachable by both, but a whole pack (pack.toml, evals, guide, marketplace entry, version) for one markdown gate is overkill, and it forces a `core`↔new-pack dependency that couples packs which should stand alone. Rejected. |
| **C3. One copy per loop, each under its own skill at its own scope** ★ | co-scoped, per-loop | **Recommended.** Guaranteed present wherever each controller runs; zero cross-pack coupling; "loaded by both" = "both realize the same goal with a loop-appropriate share." The duplication cost is bounded — today only `work-loop` exists and it carries only the thin slice, while the future discovery copy carries the full seven (the depths are *intended* to differ). The standing cross-copy invariant is the cross-loop **seam** (all loops — goal + resolve-vs-surface + the non-skippable record); the full **seven-module instantiation** is `discovery-loop`'s, not a shared obligation (see Risks). |

Prior art for the recommended shape: `operational-safety` and `security-checklists`
in-repo (controller-loaded progressive-disclosure libraries the loop already inlines);
RFC-0041 chose exactly this library-over-engine shape for infra `work-loop` and was
Accepted; plan-mode (the capability-constraint-not-instruction gate, note 03) grounds
Option C's layer 3.

## Risks & what would make this wrong

**Pre-mortem.**
- *The gate degrades to checkbox ceremony* — the exact taxonomy-gate smell note 03 names.
  **Mitigation:** every module requires a *substantive paragraph per dimension*, not a
  yes/no; the coverage-record refusal keys on content, and the `taxonomy-walk` module says
  so in its block.
- *The controller skips the gate anyway* because layer 1+2 is doctrine, not a hard lock.
  **Mitigation:** the coverage-record refusal is mechanical (the artifact is absent or it
  is not), joining refusal items the loop already honors; and where the harness offers
  layer 3, the gate is structural. The residual risk is real and stated — it is the same
  residual every doctrine-not-runtime decision in this repo carries.
- *The gate duplicates `work-loop`'s REVIEW* and reviewers get two overlapping
  obligations. **Mitigation:** the inventory diff (Decision 6) keeps the fresh-context step
  *the same* pass REVIEW already runs; the net-new steps are non-overlapping.
- *The two loops' per-loop copies drift apart.* Per-loop doctrine means `work-loop` and (future)
  `discovery-loop` each carry the method, so the prose can diverge. **Mitigation:** today there is
  exactly one copy — `discovery-loop` is unbuilt — so the drift is hypothetical until D8; and when
  D8 builds the second, divergence is *intended and by design* — `work-loop` carries only the thin
  net-new slice while `discovery-loop` carries the full seven, so the depths are meant to differ.
  The one cross-copy invariant specified *here* is the cross-loop **seam** (the goal,
  resolve-vs-surface, the non-skippable coverage record) that *all* loops conform to; the full
  **seven-module instantiation** is owned here as `discovery-loop`'s to implement against, not a
  shape `work-loop` must also match. So the goal stays aligned even though the files — and their
  depths — are separate. This is cheaper than the cross-pack coupling a single shared file would
  force, and the alternative (one shared copy) was rejected outright on the scope split (Options
  C1/C2).
- *Light mode loads too little and a real coverage gap ships under "light".*
  **Mitigation:** the bounded-pass escalation (a surviving Blocker routes to full mode)
  is the same safety valve `work-loop` light mode already trusts; and any risk trigger
  (RFC-0025) puts the work in full mode before the gate runs at all.
- *A per-loop sample-bank rots, sprawls, or fragments the calibration.* **Mitigation:**
  append-only with supersede-by-new-entry (the patterns.jsonl discipline); a sample that stops
  holding is cited, not edited, so the calibration history stays honest. Fragmentation across two
  banks is acceptable: each loop's reads are the calibration *that loop* needs, and a shared bank
  was rejected on the scope split regardless.

**Key assumptions (falsifiable).**
- *A coverage record is a sufficient mechanical hook to make the gate non-skippable
  harness-neutrally.* If controllers routinely declare done without one and nothing
  detects it, layer 2 is weaker than claimed and the gate needs the lint that
  `lint-spec-status.py` is for doc-drift. (Believed sufficient; the done-checklist already
  enforces comparable refusal items.)
- *The cross-loop seam is general enough for every loop, and the net-new slice `work-loop` adopts
  is genuinely the only part not already covered there.* The seam (goal + resolve-vs-surface + the
  non-skippable record) must hold for design, build, *and* deploy work, or "every loop realizes the
  same goal" is hollow. And the inventory claim must be right: if a module marked "already applies"
  or "not adopted" for `work-loop` turns out to leave a real coverage gap on build work, the thin
  slice is too thin. (Believed true; resolve-vs-surface and the coverage record are altitude- and
  work-type-neutral — they apply to a deploy carve as much as a spec done-declaration — and the
  inventory is conservative: it credits `work-loop` only for passes it demonstrably runs today and
  routes everything genuinely new through its already-progressive spec time. If the slice proves too
  thin, the fix is to promote one more module into `work-loop`'s spec-time adoption — cheaper under
  per-loop copies than under one shared file.)
- *Right-sizing by `work-loop`'s light/full is the right granularity.* If the gate needs a
  finer dial than two modes, this under-serves it. (Believed adequate; the per-axis routing
  of `scenario-variation` already adds a second dimension within full mode.)

**Drawbacks.** `work-loop`'s cost is small but real: added prose in its REVIEW/DECIDE naming the
existing passes as the gate's steps, the two net-new spec-time/DECIDE checks (the disposition
record + conditional domain-grounding), one done-checklist refusal item, and a seeded
`resolve-vs-surface-sample-bank.md` to curate — **no heavy reference-module set under `work-loop`**.
The heavy surface-area cost — a `references/self-coverage/` module library to maintain alongside
`operational-safety` and `security-checklists` — lands on **`discovery-loop`** when it is built,
where the full battery earns its place. That second copy is duplication, but it is the price of zero
cross-pack coupling and is bounded by specifying the shared invariants here as a seam (and the
copies' depths are *intended* to differ — thin in `work-loop`, full in `discovery-loop`). Each
loop's sample-bank needs curation discipline to stay a scaffold rather than a junk drawer.

## Evidence & prior art

**Spike / de-risk result.** The riskiest assumption — that a non-skippable gate can be
enforced *harness-neutrally without a runtime* — was checked in-repo, no code spike needed.
`work-loop`'s end-of-session checklist (SKILL.md:675-713) **already** enforces non-skippable
refusal items by doctrine plus a mechanical record: it refuses to declare done until the
reviewers returned `Clean`, until the doc-drift invariants hold (enforced by
`lint-spec-status.py`), and until `git status` is clean. None of those is a runtime lock;
all are mechanical-artifact checks the loop honors. The coverage record is the same shape —
an artifact whose absence the checklist catches. **Conclusion:** the no-runtime,
mechanical-record enforcement is *demonstrated* in the repo today; this RFC adds one more
refusal item of an already-accepted kind. The assumption survives.

**Repo precedent.** RFC-0041 + ADR-0031 (the `operational-safety` reference-library shape,
consumed by an existing reviewer, no new runtime/reviewer — the exact idiom);
`operational-safety` and `security-checklists` SKILL.md (the controller-loaded, table-routed,
never-self-discovered loading model, and the "if the gate is absent, flag don't silently
skip" honesty); `work-loop` SKILL.md (the consuming controller — the PLAN assumption trio +
declined-pattern register, the REVIEW adversarial pass the fresh-context step reuses, the
light-mode bounded pass at 94-97, and the done-checklist refusal items at 675-713 the
coverage record joins); RFC-0025 (the light/full right-sizing this reuses);
`docs/knowledge/patterns.jsonl` + CONVENTIONS.md:803-832 (the append-only,
supersede-by-new-entry living-doctrine discipline the sample-bank adopts);
`research-project-check`'s stop-signal (the saturation rule, RFC-0048 O6).

**External prior art** (fetched and confirmed in RFC-0048's notes; not re-litigated here):
the floor-raiser table's groundings — Klein's prospective hindsight / pre-mortem (+30%
failure identification), the WHO surgical checklist (−36% complications) as the
recall→recognition / external-scaffold evidence, grounded-theory saturation as the stop
rule, and Claude Code plan mode as the capability-constraint-not-instruction gate — all in
[`0048-notes/03`](0048-notes/03-autonomy-and-gate-economics.md). The myopic-greedy-commitment
mechanism (arXiv:2601.22311) and the self-critique-anchoring limit (Reflexion
arXiv:2303.11366; Self-Refine arXiv:2303.17651) are the reason the gate's adversarial step
must run in a *fresh* context.

**Promoted research.** This RFC adds no new corpus; it builds on RFC-0048's
[`0048-notes/`](0048-notes/) — specifically note 03 (the floor-raiser table and the
gate-economics argument) and note 09 (the resolve-vs-surface lens and its sample-bank). Per
the RFC-0048 D9 series-execution standard, this effort appends its own resolve-vs-surface
sample reads to note 09 in the same change.

## Open questions

Two, each with a recommended default — neither a genuine value/scope/conflict call (both
are referent-grounded; they are recorded here only because they are confirm-at-accept
naming/mechanics details, not because the research is unfinished).

1. **Gate-phase / reference-dir naming.** · *recommended default:* "the self-coverage gate" for
   the phase (mirrors the parent's naming), and `references/self-coverage/<step>.md` under the
   consuming loop's skill for the modules (mirrors the existing `operational-safety` /
   `security-checklists` reference-dir shape). · owner: eugenelim · decide-by: RFC accept.
2. **Sample-bank projection mechanics** — appends to a *projected* pack reference file
   require source-edit-then-`make build-self` here, and live in the adopter's installed
   copy for them. · *recommended default:* ship the `work-loop` bank as pack content under
   `packs/core/.apm/skills/work-loop/references/self-coverage/`, appends-via-rebuild here, leave
   the exact build-self wiring to the implementing spec. · owner: eugenelim · decide-by: spec
   authoring.

## Follow-on artifacts

Filled in on acceptance.

- **ADR:** record "the self-coverage gate is **per-loop controller doctrine with a loop-appropriate
  share** — each loop carries its own copy at its own scope (no shared library, no cross-pack
  coupling, no new reviewer, no new runtime); **`discovery-loop` carries the full seven-module
  design-convergence gate**, while **`work-loop` adopts only the net-new slice** (a resolve-vs-surface
  disposition record + conditional domain-grounding) atop the passes it already runs and under its
  existing progressive spec time" (the sibling of ADR-0031 for `operational-safety`; **amends +
  refines** RFC-0048 D5's "one `core` library loaded by both controllers").
- **Spec:** `docs/specs/self-coverage-gate/` — **a thin `work-loop` edit**: name its existing passes
  as the gate's steps, add the resolve-vs-surface **disposition record** and a **conditional
  domain-grounding** check at spec time / DECIDE under the existing light/full mode, add **one**
  done-checklist refusal item (the disposition record), and seed the `work-loop`
  `resolve-vs-surface-sample-bank.md` (note 09 → the `work-loop` bank) with its build-self projection
  wiring. **No heavy design-convergence reference modules ship under `work-loop`** — the full
  seven-module instantiation is specified here for **`discovery-loop`** to carry (next), not built in
  `core`.
- **`discovery-loop` seam (the full gate's home):** consumed by RFC-0048 D8's child (RFC-0053),
  which carries its **own** copy of the **full seven-module gate** (phase + modules + its own
  sample-bank) in `product-engineering` at user scope, right-sized by its own progressive mode,
  implementing the seam + the seven-module instantiation specified here (the gate as
  `discovery-loop`'s pre-convergence G2 gate) — *not* a file it imports from `core`.
- **No CONVENTIONS touch — the gate is skill-resident.** The self-coverage gate is named and
  defined entirely within the consuming loop's own skill (`work-loop`'s SKILL.md + its
  `references/self-coverage/`), as per-loop co-scoped doctrine (Decision 1). The `core` pack
  ships the gate **without any edit to `docs/CONVENTIONS.md`**: the operating model's doctrine
  lives in the loop skills that run it, not in a CONVENTIONS operating-model section. CONVENTIONS
  keeps only its existing role — the spec-metadata format contract (§ 4) and the "how we do
  non-trivial work" pointer to `work-loop` — neither of which this RFC touches. (RFC-0048
  § Amendments 2026-06-29 relocates the operating-model doctrine from a planned CONVENTIONS
  section into the loop skills; this RFC's skill-resident packaging is the `work-loop` instance.)
- **Changelog:** `docs/product/changelog.md` `[Unreleased]` entry for the `work-loop`
  behavior change.
- **Pack version:** bump `core` (the thin `work-loop` SKILL.md edits + the seeded
  `resolve-vs-surface-sample-bank.md`; **no heavy reference modules** under `work-loop`). No new
  skill, no new pack, no marketplace addition — the gate lives under the existing `work-loop` skill.
- **Foundation reconciliation:** **amends + refines RFC-0048 D5.** *(Packaging)* D5's "a reference
  library in `core`, loaded by both loop controllers" does not survive the operating model's own
  scope split — `discovery-loop` is user-scope/pre-repo where a repo-scope `core` library is absent —
  so it is reconciled to **per-loop co-scoped doctrine** (each loop carries its own copy; no shared
  library; no `core`↔`product-engineering` coupling). *(Share)* D5's "both design/build loops run the
  seven-module gate" is **refined**: `discovery-loop` carries the **full** seven (its native
  design-convergence altitude), while `work-loop` adopts only the **net-new slice** because its
  existing structure and already-progressive spec time cover the rest — so "loaded by both
  controllers" = "both loops realize the same goal, each with a loop-appropriate share." Recorded at
  [RFC-0048 § Amendments](0048-autonomous-product-team-operating-model.md#amendments-foundation-reconciliations)
  (2026-06-29) per the D9 series-execution obligation.
