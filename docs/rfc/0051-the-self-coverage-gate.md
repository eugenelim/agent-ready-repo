# RFC-0051: the self-coverage gate — a non-skippable coverage library both loop controllers run

- **Status:** Open <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-25
- **Date closed:**
- **Related:** [RFC-0048](0048-autonomous-product-team-operating-model.md) (the foundation — this is **child 3**, Decision 5; the provisional foundation this drift-aligns back to) · [RFC-0041](0041-infra-aware-work-loop.md) + ADR-0031 (the `operational-safety` reference-library + reuse-the-reviewer precedent this RFC mirrors exactly — *no new runtime, no new reviewer*) · RFC-0025 (`work-loop` light/full mode + risk triggers — the right-sizing model this reuses) · `operational-safety` + `security-checklists` skills (the controller-loaded progressive-disclosure shape) · `work-loop` skill (the consuming controller; PLAN trio + declined-pattern register + REVIEW adversarial pass + the done-checklist refusal items this gate joins) · RFC-0048 D8 (`discovery-loop` / `discovery-lead` — the *second* controller, not built yet) · promoted research in RFC-0048's [`0048-notes/03`](0048-notes/03-autonomy-and-gate-economics.md) (the floor-raiser table) and [`0048-notes/09`](0048-notes/09-gap-resolutions.md) (the resolve-vs-surface sample-bank this graduates)

## The ask

**Recommendation (BLUF).** Build the self-coverage gate the way RFC-0041 built
`operational-safety`: a **`core` reference library + loop doctrine — no new runtime,
no new reviewer**. It holds seven step-modules (domain-grounding table · pre-mortem ·
taxonomy walk · saturation declaration · fresh-context adversarial pass ·
scenario-variation · resolve-vs-surface) plus the **living sample-bank** graduated out of
[`0048-notes/09`](0048-notes/09-gap-resolutions.md). It is **non-skippable** — but by a
different mechanism than `operational-safety`: it runs in the **loop controller's own
context** as a named gate phase whose coverage record the done/converged checklist refuses
to pass without, *not* inlined into a subagent brief. `work-loop` is the first consumer;
`discovery-loop` becomes the second when RFC-0048 D8 ships it.

**Why now (SCQA).** *Situation:* RFC-0048 decided the operating model and named the
self-coverage gate (Decision 5) as the floor-raiser that fixes the knowing-doing gap —
the agent failing to apply knowledge it already had, so errors compound unwatched between
human gates ([`0048-notes/03`](0048-notes/03-autonomy-and-gate-economics.md)). *Complication:*
RFC-0048 *decided* the gate and its packaging but **built nothing** — and the parent is
explicit that a self-discovered skill is the wrong vehicle (the agent could skip it at its
discretion, defeating the whole point), while `operational-safety`'s exact loading
mechanism (inline into a *subagent* brief) does not transfer, because this gate runs in the
*controller's own* reasoning context, where there is no brief to inline into. *Question:*
how do we ship a gate that is genuinely non-skippable, harness-neutrally, without a runtime
lock and without a fourth reviewer?

**Decisions requested.**

1. **Build it as a `core` reference library + loop doctrine, the `operational-safety`
   shape — never a self-discovered skill.** A skill-packaged `references/<step>.md` set
   (so depth scales without bloating any prose), whose loading is *controller-driven*. ·
   *why:* it is the precedent RFC-0048 D5 named and RFC-0041/ADR-0031 already accepted. ·
   decide-by: RFC accept · default: adopt.
2. **Make it non-skippable by the controller-gate + checklist-refusal mechanism, stated
   honestly as doctrine + a mechanical record, not a runtime lock.** The consuming loop's
   SKILL.md names the gate a required phase; the done/converged checklist refuses to
   declare done without the **coverage record** artifact and with any fresh-context finding
   unresolved — joining the existing refusal items (reviewer-clean, doc-drift invariants)
   at `work-loop` SKILL.md:675-713. On harnesses that enforce gates outside the prompt
   (omnigent), the same gate becomes structural; harness-neutrally it is doctrine + the
   coverage-record check. · *why:* this is the one design question RFC-0048 left to the
   child, and the honest answer is the same posture `operational-safety` already ships. ·
   decide-by: RFC accept · default: adopt.
3. **Decompose into seven step-modules + the living sample-bank**, routed by mode and by
   the axes the design crosses (not a flat march). · *why:* the operational-safety module
   shape keeps each step lean and lets light mode load only the core. · decide-by: RFC
   accept · default: adopt.
4. **No new reviewer — the fresh-context adversarial step reuses the existing
   `adversarial-reviewer` (and `devils-advocate` for the research/design case) dispatched
   in a fresh context.** · *why:* the CHARTER three-reviewer ceiling; the parent's "no new
   reviewer"; the existing fresh-context dispatch already exists in `work-loop`'s REVIEW. ·
   decide-by: RFC accept · default: adopt.
5. **Right-size light/full, mirroring `work-loop`.** Light mode loads the always-on core
   (domain-grounding + resolve-vs-surface + a single bounded fresh-context pass; a
   surviving Blocker escalates to full); full mode loads all seven — running
   scenario-variation across the axes in play and the fresh-context pass iterated to clean.
   · *why:* the gate must not become ceremony on a one-line change; reuse
   RFC-0025's right-sizing rather than invent a second knob. · decide-by: RFC accept ·
   default: adopt.
6. **Graduate the resolve-vs-surface sample-bank into the library as a living, append-only
   reference**, seeded from [`0048-notes/09`](0048-notes/09-gap-resolutions.md). Until
   RFC-0048 is Accepted, appends continue in note 09; on acceptance the bank's durable home
   is this library. · *why:* the lens hits the right call only ~half the time without an
   externalized scaffold (note 09); the bank *is* that scaffold, and it applies repo-wide,
   not just to this RFC. · decide-by: RFC accept · default: adopt.

## Problem & goals

**Diagnosis.** RFC-0048 Decision 5 decided *that* the self-coverage gate exists and *what*
it must contain, and resolved its packaging in principle — "a reference library + doctrine
(the `operational-safety` shape) in `core`, loaded by both loop controllers, right-sized
light/full — *not* a self-discovered skill." What it did **not** do — because it builds
nothing — is settle the one mechanism that makes the principle real: **how a gate is
non-skippable when it runs in the controller's own context.** `operational-safety` earns
its non-skippability cheaply: its consumer is a *subagent* whose `tools:` has no Skill
tool, so the orchestrator inlines the modules into the subagent's brief as prompt text and
the subagent never has to find the library (`operational-safety` SKILL.md:21-48). The
self-coverage gate has no such consumer — it runs in the **loop controller**, the main
agent that has *already loaded* `work-loop` (or, later, `discovery-loop`). There is no
brief to inline into, and the same "skill discovery is model-invoked, so it can be skipped"
hazard the parent flagged applies to the controller too. The gate therefore needs its own
non-skippability mechanism, and that mechanism is this RFC's load-bearing design work.

The failure this prevents is concrete and measured: agents exhibit *myopic greedy
commitment* — chain-of-thought locks in early decisions and builds on them confidently;
the agent's own critique runs in the same anchored context and won't catch it
([`0048-notes/03`](0048-notes/03-autonomy-and-gate-economics.md), citing arXiv:2601.22311).
Every token spent after a wrong high-altitude commitment is wasted, and the agent won't
know. The gate raises the floor *between* the human gates so fewer errors compound
unwatched — but only if it actually runs, every time, which is what "non-skippable" has to
deliver.

**Goals.**
- Ship the gate as the RFC-0041 idiom — **doctrine + a `core` reference library + reuse of
  the existing reviewers** — so it is a *habit*, not a runtime (CHARTER Principle 3).
- Make it **genuinely non-skippable** harness-neutrally, with an honest account of where
  that is doctrine-plus-a-mechanical-check versus structurally enforced.
- Keep each step **lean and load-only-what-applies**, so the gate is proportionate (a
  one-line change pulls the core; a multi-discipline convergence pulls all seven).
- Give the **resolve-vs-surface lens** its durable, living home, so the calibration that
  lives in one RFC note becomes the repo-wide scaffold the parent intended.

**Non-goals** (could-have-been goals, deliberately dropped).
- *A self-discovered skill.* Explicitly rejected by RFC-0048 D5; a trigger-matched skill is
  skippable at the agent's discretion, which defeats a *gate*.
- *A fourth reviewer agent.* The CHARTER caps reviewers at three; the fresh-context step
  reuses `adversarial-reviewer` / `devils-advocate` (Decision 4).
- *An executable gate runtime / lock.* A program that structurally blocks the agent from
  writing past the gate is runtime infrastructure (Principle 3) and harness-specific; we
  ship the doctrine such a harness enforces, not the harness.
- *Building `discovery-loop`.* The second controller is RFC-0048 D8's child; this RFC wires
  the **first** consumer (`work-loop`) and specifies the seam the second will use.
- *The Domain Framing + Scope Boundary typed artifacts and the traceability lint* (RFC-0048 D4/D6, sibling
  children). The domain-grounding step *consumes* a Domain Framing where one exists and
  degrades to in-gate grounding where it does not; it does not define that artifact.

## Proposal

Cascaded under the requested decisions.

**Decision 1 — a `core` reference library + loop doctrine.** A new `core` skill —
proposed name **`self-coverage`** (OQ1) — structurally identical to `operational-safety`:
a lean SKILL.md (the universal method + a Module index that is the routing authority) over
`references/<step>.md` modules carrying the depth. No executable code ships; the artifact
is prose + a routing table, exactly as RFC-0041 Decision 1 framed `operational-safety`.
This clears Principle 3 by the same argument the repo already accepted: a depth library a
controller reasons from is a habit, not infrastructure.

**Decision 2 — the non-skippability mechanism (load-bearing).** The gate is non-skippable
by three layers, named honestly from strongest-available to the harness-neutral floor:

1. **A named, required gate phase in the consuming loop's doctrine.** `work-loop`'s SKILL.md
   (and later `discovery-loop`'s) names the self-coverage gate as a phase the loop *runs*,
   not a skill it *may discover* — the plan-mode lesson that a gate works when it is a hard
   state, not an instruction ([`0048-notes/03`](0048-notes/03-autonomy-and-gate-economics.md):82-90).
   The controller loads the library directly because it is *already running the loop that
   mandates the gate*; there is no discretionary "is this skill relevant?" judgment of the
   kind the parent warned about.
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

**Decision 3 — the seven step-modules + the living sample-bank.** Each step is a
`references/<step>.md` module; the SKILL.md Module index routes by **mode** (which steps
light vs full loads) and, for scenario-variation, by **which axes the design crosses** —
never a flat march. The seven, with the failure each guards and its grounding:

| Module | The step | Blocks declaring covered if… | Grounded in |
|---|---|---|---|
| `domain-grounding` | a domain-grounding table — one row per load-bearing domain claim, each grounded in a referent (a Domain Framing where RFC-0048 D4 supplies one; else in-gate `research`) | any cell empty or "assumed" | note 03 table (WHO-checklist −36% complications); RFC-0048 D4 |
| `pre-mortem` | prospective hindsight — assume it shipped and failed; enumerate failure modes, each tagged to a design element | < N scenarios, or any untagged | note 03 (+30% failure ID); Klein prospective hindsight |
| `taxonomy-walk` | an external dimension register walked one paragraph each (a substantive paragraph, never yes/no) | any dimension blank | note 03 (recall→recognition; external scaffolds beat free recall) |
| `saturation-declaration` | a grounded-theory stop rule — declare convergence only when a full pass surfaces no new open question and no invalidating edit | declaration absent | note 03; `research-project-check`'s stop-signal (RFC-0048 O6) |
| `fresh-context-adversarial` | dispatch `adversarial-reviewer` (or `devils-advocate`) in a **fresh context** so the reviewer is not anchored to what was just produced | any finding unresolved | note 03 (plan-mode fresh-context lesson); reuse, no new reviewer |
| `scenario-variation` | re-run the design against a varied **domain / stakes-level / scale / platform / harness** — orthogonal-axis modelling, loaded only for the axes in play | a crossed axis left unvaried | RFC-0048 D5 (catches stakes- and conflict-class gaps without the human) |
| `resolve-vs-surface` | a pass over every open item — solve referent-groundable items and cite the referent; surface only value-origination / irreversible-risk / value-conflict (or a referent that genuinely failed) | any open item neither resolved-with-referent nor surfaced-with-reason | RFC-0048 D5; note 09 sample-bank |

The first five are note 03's original floor-raiser table; scenario-variation and
resolve-vs-surface are RFC-0048 D5's two additions. The **living sample-bank**
(`references/resolve-vs-surface-sample-bank.md`) is the calibration the `resolve-vs-surface`
module points to — see Decision 6.

**Decision 4 — no new reviewer.** The `fresh-context-adversarial` module *invokes* the
existing reviewers; it adds none. For a build/spec/implementation artifact that is
`adversarial-reviewer`; for a research or design artifact it is `devils-advocate`
([`0048-notes/06`](0048-notes/06-pack-delta-and-orchestration.md):61). The novelty is not a
new agent but a *named obligation* to run the existing one in a separated context, which
`work-loop`'s REVIEW already does — the gate formalizes and names it as one of its seven
steps rather than duplicating it.

**Decision 5 — right-size light/full.** The gate reuses `work-loop`'s existing light/full
distinction (RFC-0025) rather than inventing a second knob:

- **Light mode** loads the **always-on core**: `domain-grounding` + `resolve-vs-surface` +
  a **single bounded** `fresh-context-adversarial` pass. A surfaced Blocker that survives
  one re-review **escalates to full mode** — the exact bounded-pass rule `work-loop` light
  mode already uses (SKILL.md:94-97).
- **Full mode** loads **all seven**: the core plus `pre-mortem`, `taxonomy-walk`,
  `saturation-declaration`, and `scenario-variation` across the axes the design crosses,
  with the `fresh-context-adversarial` pass **iterated to clean** (not bounded).

This keeps the gate proportionate — a one-line change in light mode runs three cheap steps;
a multi-discipline convergence in full mode runs the full battery — and it inherits
right-sizing from the loop instead of re-deciding it.

**Decision 6 — the living sample-bank.** The resolve-vs-surface sample-bank currently lives
in [`0048-notes/09`](0048-notes/09-gap-resolutions.md) as a "living artifact — expectation
set for the whole series." RFC-0048 D5 and note 09 both state it **graduates** into this
library on acceptance, because the lens applies repo-wide, not just to RFC-0048. This RFC
specifies the graduated home: `references/resolve-vs-surface-sample-bank.md`, seeded with
note 09's starting reads, append-only (a sample that stops holding earns a *new* entry
citing the old, never an edit — the `docs/knowledge/patterns.jsonl` discipline,
CONVENTIONS.md:803-832). Every series effort appends its own reads, so the bank accretes
calibration and the ~half-the-time hit rate climbs (note 09).

*Migration & the projection seam.* The bank ships **as pack content**, so an adopter's
installed copy is theirs to append to in place. For **this** repo (which self-hosts the
pack), appends go to the source under `packs/core/.apm/skills/self-coverage/references/`
and reach the projected `.claude/` copy via `make build-self` — the same source-edit-then-
rebuild discipline every pack-content change follows here. Until RFC-0048 is **Accepted**,
appends continue in note 09 (its pre-graduation home); the graduation move itself is a
follow-on of *this* RFC's implementing spec. The build-self/projection mechanics are a
spec-time detail, not an open design question (OQ2 records the recommended default).

*The seam with `work-loop` (Principle 2 — no duplication).* The library does **not**
re-implement REVIEW. An inventory diff against `work-loop` today: the `fresh-context-
adversarial` step *is* the existing REVIEW adversarial pass (named, not duplicated); the
`pre-mortem` and the open-item disposition have partial hooks in PLAN's assumption trio and
declined-pattern register; `domain-grounding`, `taxonomy-walk`, `saturation-declaration`,
and `scenario-variation` are **net-new surface** the loop does not carry today. So the
library supplies depth for steps the loop already gestures at and adds the missing steps —
the same inventory-diff argument RFC-0041 used to clear Principle 2 for `operational-safety`.

*Consumers & sequencing.* `work-loop` is the **first** consumer: the gate runs at its
REVIEW→DECIDE boundary as the pre-done coverage pass. `discovery-loop` (RFC-0048 D8, not
built) becomes the **second**: it runs the gate as its pre-convergence (pre-G2) gate, which
is where [`0048-notes/05`](0048-notes/05-judgment-decomposition-and-phases.md):51 places it.
Shipping the library now with `work-loop` wired, and the `discovery-loop` seam specified for
its child to consume, satisfies RFC-0048 D5's "loaded by both loop controllers" with honest
sequencing — the library exists and is consumed the moment each controller does.

## Options considered

**Axis: what artifact form is the gate, and how is it enforced non-skippably?** This axis
exhausts the space because any answer must name both a *form* (prose doctrine / skill /
reviewer / runtime) and an *enforcement* (discretionary / mechanical-record / structural).
Options are MECE along it; prior art grounds each.

| Option | Form · enforcement | Verdict |
|---|---|---|
| **A. Do nothing** — leave the steps as scattered prose in `work-loop` | none · discretionary | Cost of delay: the knowing-doing gap (note 03) recurs on every product; the steps stay unnamed, unrouted, and skippable by omission. Rejected. |
| **B. Self-discovered skill** the agent invokes when it judges it relevant | skill · discretionary | A trigger-matched skill is skippable at the agent's discretion under anchoring — which defeats a *gate*. **Explicitly rejected by RFC-0048 D5.** Rejected. |
| **C. Controller-loaded reference library + loop doctrine** ★ | library + doctrine · mechanical-record (+ structural where the harness offers it) | **Recommended.** The `operational-safety` / RFC-0041 idiom; clears Principles 1–3; non-skippable via the done-checklist refusal the loop already enforces. |
| **D. A fourth reviewer agent** dedicated to coverage | new agent · discretionary | Fails the CHARTER three-reviewer ceiling; the fresh-context step already reuses the existing reviewers. Rejected. |
| **E. Executable gate runtime / lock** that structurally blocks writing past the gate | runtime · structural | The strongest enforcement, but it is runtime infrastructure (Principle 3) and harness-specific (the RFC-0041 P4 harness-neutrality posture). We ship the doctrine such a harness enforces, not the harness. Rejected as the *shipped* form; folded into Option C's layer 3 where the harness provides it. |

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
- *The library duplicates `work-loop`'s REVIEW* and reviewers get two overlapping
  obligations. **Mitigation:** the inventory diff (Decision 6) keeps the fresh-context step
  *the same* pass REVIEW already runs; the net-new steps are non-overlapping.
- *Light mode loads too little and a real coverage gap ships under "light".*
  **Mitigation:** the bounded-pass escalation (a surviving Blocker routes to full mode)
  is the same safety valve `work-loop` light mode already trusts; and any risk trigger
  (RFC-0025) puts the work in full mode before the gate runs at all.
- *The sample-bank rots or sprawls.* **Mitigation:** append-only with supersede-by-new-
  entry (the patterns.jsonl discipline); a sample that stops holding is cited, not edited,
  so the calibration history stays honest.

**Key assumptions (falsifiable).**
- *A coverage record is a sufficient mechanical hook to make the gate non-skippable
  harness-neutrally.* If controllers routinely declare done without one and nothing
  detects it, layer 2 is weaker than claimed and the gate needs the lint that
  `lint-spec-status.py` is for doc-drift. (Believed sufficient; the done-checklist already
  enforces comparable refusal items.)
- *Both controllers can run the same seven steps.* If the discovery convergence and the
  build done-declaration need materially different step sets, "one library, two consumers"
  splits. (Believed false; the steps are altitude-neutral — grounding, pre-mortem,
  saturation, and resolve-vs-surface apply to a spec done-declaration as much as a
  convergence, which is why RFC-0048 names *both* controllers.)
- *Right-sizing by `work-loop`'s light/full is the right granularity.* If the gate needs a
  finer dial than two modes, this under-serves it. (Believed adequate; the per-axis routing
  of `scenario-variation` already adds a second dimension within full mode.)

**Drawbacks.** A third controller-loaded reference library to maintain alongside
`operational-safety` and `security-checklists` — real surface-area cost, justified because
the gate is universal (it runs on *every* full-mode loop, not only infra/security ones).
Added prose in `work-loop`'s REVIEW/DECIDE and the done-checklist. A living sample-bank that
needs curation discipline to stay a scaffold rather than a junk drawer.

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

1. **Skill name — `self-coverage`?** · *recommended default:* `self-coverage` (mirrors the
   parent's "self-coverage gate" naming; sibling library names are `operational-safety` /
   `security-checklists`, so a noun-phrase fits). · owner: eugenelim · decide-by: RFC accept.
2. **Sample-bank projection mechanics** — appends to a *projected* pack reference file
   require source-edit-then-`make build-self` here, and live in the adopter's installed
   copy for them. · *recommended default:* ship as pack content (the graduated home),
   appends-via-rebuild here, leave the exact build-self wiring to the implementing spec. ·
   owner: eugenelim · decide-by: spec authoring.

## Follow-on artifacts

Filled in on acceptance.

- **ADR:** record "the self-coverage gate is a controller-loaded, non-skippable `core`
  reference library enforced by a coverage-record checklist refusal — no new reviewer, no
  new runtime" (the sibling of ADR-0031 for `operational-safety`).
- **Spec:** `docs/specs/self-coverage-gate/` — the `self-coverage` skill (SKILL.md + the
  seven `references/<step>.md` modules + the seeded `resolve-vs-surface-sample-bank.md`),
  the Module index routing (mode + axis), the `work-loop` REVIEW/DECIDE wiring + the
  done-checklist refusal item, and the sample-bank graduation move (note 09 → library) with
  its build-self projection wiring.
- **`discovery-loop` seam:** consumed by RFC-0048 D8's child (the gate as `discovery-loop`'s
  pre-convergence G2 gate); specified here, wired there.
- **CONVENTIONS touch:** name the self-coverage gate in the operating-model section
  (RFC-0048's CONVENTIONS slice), as the floor-raiser both loops run.
- **Changelog:** `docs/product/changelog.md` `[Unreleased]` entry for the `work-loop`
  behavior change.
- **Pack version:** bump `core` (new skill + `work-loop` edits); add `self-coverage` to the
  catalogue/marketplace manifest at spec time.
- **Foundation reconciliation:** no drift surfaced against RFC-0048 D5 — no amendment
  required. (Recorded per the D9 series-execution obligation.)
