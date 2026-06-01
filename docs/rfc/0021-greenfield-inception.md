# RFC-0021: Greenfield inception — the idea→repo front-door (research → foundation → walking skeleton)

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-01
- **Date closed:** 2026-06-01
- **Related:** RFC-0019 (brief intake + LLD — 0021 produces the first brief and feeds the build loop); RFC-0020 (reference-architecture foundation — 0021's foundation step authors it); the `adapt-to-project` skill (the *brownfield* counterpart front-door); applied-mode prior-art survey at `0021-greenfield-inception-research.md`.

## The ask

- **Recommendation (BLUF):** Add the **greenfield front-door** the methodology lacks: the **`init-project`** inception flow that turns an *idea* into a structured repo — apply a **value gate** over a **fed-in discovery shape** (the `research` pack's output, a provided PRD, or `receive-brief` — `init-project` *consumes* discovery, it does not perform it), make the **foundation** decision (an ADR + `reference.md` per RFC-0020), and produce a **walking skeleton** (a thin, kept, end-to-end slice that validates the foundation) — then hand off to the `brief → spec → work-loop` build. It is gated: throwaway/single-file repos skip it (yolo stays fine); it fires only when there are **real stack/structure decisions**. It composes existing skills (brief, foundation, ADR, spec) rather than reinventing an autonomous generator.

- **Why now (SCQA):**
  - *Situation.* The methodology has a brownfield front-door (`adapt-to-project`), a downstream loop (brief → foundation → spec → LLD → build), and the foundation (RFC-0020).
  - *Complication.* A **brand-new repo has no front-door**. Adopters research an idea, then *yolo* a throwaway prototype and retrofit structure — losing the research rationale and shipping no foundation. spec-kit proves the opposite emphasis (`specify init` is greenfield-first; brownfield is its open gap); we are the mirror, and greenfield is *ours*.
  - *Question.* How does an idea become a structured repo with a justified foundation and a validated skeleton — without forcing inception ceremony onto throwaways, and without building an autonomous code generator?

- **Decisions requested:**
  1. **Front-door locus** — a **new greenfield inception flow** (the **`init-project`** skill), not an extension of `adapt-to-project` (which is brownfield by definition). *Recommended.* Decide-by 2026-06-13.
  2. **Flow shape** — value gate over **fed-in discovery** → foundation (ADR + `reference.md`) → walking skeleton → hand off to `brief → spec → work-loop`. *Recommended.* Decide-by 2026-06-13.
  3. **Trigger gate** — throwaway/single-script repos skip it; it fires only for repos with real tech-stack/structure/tooling decisions. *Recommended.* Decide-by 2026-06-13.
  4. **Generation engine** — **compose existing single-purpose skills** + a walking skeleton; *decline* the autonomous multi-agent "software company" paradigm (BMAD/MetaGPT/ChatDev-style) as the engine, while borrowing its structured-document handoff. *Recommended.* Decide-by 2026-06-13.

## Problem & goals

The current greenfield path is the **yolo-prototype-then-cleanup** anti-pattern: build a throwaway to "figure it out," then retrofit structure once it sort-of works. The prior art's principled replacement is the **walking skeleton / tracer bullet / steel thread** — *"a tiny implementation that performs a small end-to-end function… links the main architectural components"* to validate the architecture early ([Henrico Dolfing](https://www.henricodolfing.com/2018/04/start-your-project-with-walking-skeleton.html), [Rubick — steel threads](https://www.rubick.com/steel-threads/)) — wrapped in a structured **inception** that decides direction, stack, and the value proposition before code ([Lean Inception, Fowler](https://martinfowler.com/articles/lean-inception/)).

### Goals

- Give a brand-new repo a front-door: **idea → structured repo** with a justified foundation, replacing yolo-then-cleanup.
- Apply a **value gate** over **fed-in discovery** (*"if you can't explain the business value, pause"*) so the stack decision is reasoned and recorded (ADR), not improvised — discovery itself is produced upstream (the `research` pack), not by `init-project`.
- Produce a **walking skeleton** — thin, kept, end-to-end — instead of a throwaway prototype.
- **Compose** the existing artifacts (brief, foundation, spec) — the inception flow orchestrates, it doesn't reinvent.
- Stay out of the way for throwaways (the trigger gate).

### Non-goals

- **An autonomous code generator.** We decline the multi-agent "AI software company" engine (Decision 4); the human stays in the loop and the existing skills do the work.
- **A repo/code scaffolder like `create-next-app`.** The flow produces the *foundation + a thin skeleton*, not a fully-generated app from a stack template.
- **Replacing `adapt-to-project`.** That remains the brownfield front-door; this is its greenfield twin, not a merge.
- **Forcing ceremony on throwaways.** The trigger gate keeps single-scripts on the yolo path.
- **Performing discovery/research itself.** Discovery (market/technical research, prior art, competitive landscape) is **fed in as a shape** — from the `research` pack (applied mode), a provided PRD, or `receive-brief` — and `init-project` consumes it. Owning the research phase is out of scope; that's the research pack's job (scoped-handoff principle).

## Proposal

`init-project`, a guided greenfield flow:

1. **Trigger gate (Decision 3).** Real stack/structure/tooling decisions ahead? If no (a script, a spike, a throwaway) → scaffold directly, skip the flow. If yes → continue.
2. **Frame + value gate.** Take the **fed-in discovery shape** — `research`-pack output (applied mode), a provided PRD, or `receive-brief`'s brief — and from it articulate business value + MVP. Gate: if the value can't be stated plainly, pause and send discovery back upstream. **Output: the first `brief`** (RFC-0019 artifact, greenfield variant). `init-project` *consumes* discovery; it does not run it.
3. **Foundation decision.** Choose the stack/architecture with recorded rationale — **an ADR** (what/why/alternatives/re-evaluation date) **and `reference.md`** (RFC-0020, greenfield-authoring path). This is the greenfield population source RFC-0020 names.
4. **Walking skeleton.** Author a single spec for a thin end-to-end slice that links the main architectural components, and build it through `work-loop`. It is *kept and minimal*, not thrown away — validating the foundation with "small integration pain all along the way."
5. **Hand off.** From here the normal `brief → spec → LLD → work-loop` loop runs, with `reference.md` in place for every LLD to conform to.

**Fluid, not waterfall (learned from OpenSpec).** These are *phases of attention*, not gates — any artifact is revisitable as understanding firms up (the walking skeleton routinely sends you back to amend the foundation). The order is the default path, not a one-way ratchet. **Scoped handoffs (learned from BMAD):** each step passes the *next* step only the artifacts it needs — inception → the brief; foundation → the brief + ADRs; skeleton → the brief slice + `reference.md` — not the whole accreted history.

## How the three RFCs hold together

Two front-doors feed one shared downstream; the foundation is the spine:

```
GREENFIELD front-door ── RFC-0021 ──┐   (idea → inception → foundation → walking skeleton)
                                     ├──►  brief ──►  reference.md ──►  spec ──►  LLD ──►  work-loop build
BROWNFIELD front-door ── adapt-to-project ┘  (RFC-0019)   (RFC-0020)   (0019)  (0019, conforms
                          + RFC-0020 harvest                                     to reference.md)
```

The **seams** that let the three land independently and in any order:

- **0021 produces 0019's and 0020's artifacts.** Inception emits the first **brief** (0019); the foundation step authors **`reference.md`** (0020). 0021 is an *orchestrator* of the other two plus the walking skeleton — it adds no artifact type of its own.
- **0019 ↔ 0020 by presence-check.** RFC-0019's LLD (Decision 9) **reads `reference.md` when present, else derives + elicits** — so 0019 ships standalone, and the day a `reference.md` exists (via 0021 greenfield, 0020 harvest, or a stack pack) the LLD conforms to it automatically.
- **0020's population maps to repo context.** Greenfield → **0021's** foundation step; brownfield → **`adapt-to-project` harvest** (repo **detection** feeds it); enterprise → **stack packs**. No vague "authoring".
- **Each is independently valuable.** 0019 alone gives brief-intake + LLD. 0020 alone gives a foundation `adapt-to-project` can harvest. 0021 needs 0019+0020 to land first (it composes them) — the only ordering constraint, and a soft one.

## Options considered

Each decision's option space, MECE along a stated axis, do-nothing included where the axis admits it.

### Decision 1 — Front-door locus — *axis: where greenfield init lives*

| Option | Trade-off |
| --- | --- |
| **New greenfield inception flow** ★ | The clean greenfield twin of `adapt-to-project`; symmetric and discoverable |
| Extend `adapt-to-project` | Wrong by definition — that skill adapts *existing* content; greenfield has none |
| Template-repo only (`Use this template`) | Zero logic, but no research/value gate, no foundation, no skeleton |
| Do-nothing (yolo) | No build cost; the yolo-then-cleanup anti-pattern persists |

### Decision 2 — Flow shape — *axis: how idea becomes structured repo*

| Option | Trade-off |
| --- | --- |
| **Inception → foundation → walking skeleton → handoff** ★ | Grounded in Lean Inception + walking skeleton + constitution-first; each step has a home artifact |
| Foundation-first, no inception | Skips the value gate — stack chosen before the problem is understood |
| Skeleton-first, no foundation | Validates integration but bakes in unrecorded stack decisions |

### Decision 3 — Trigger gate — *axis: when the flow fires*

| Option | Trade-off |
| --- | --- |
| **Gate on "real decisions"** ★ | Throwaways stay yolo; ceremony only where it pays — matches "right-size to stakes" |
| Always run | Inception on a weekend script is friction that drives people off the path |
| Never (manual) | No guidance; back to yolo-then-cleanup |

### Decision 4 — Generation engine — *axis: how much the system auto-generates*

| Option | Trade-off | Prior art |
| --- | --- | --- |
| **Compose existing skills + walking skeleton** ★ | Boring, maintainable, human-in-loop; no new agent framework | our skills + walking skeleton |
| Autonomous multi-agent "software company" | Impressive idea→repo demos — but uneven production quality, heavy framework, survivorship-biased | BMAD, MetaGPT, ChatDev |
| Pure stack scaffolder | Fast code, but no reasoned foundation or value gate | cookiecutter / `create-*` |
| Do-nothing | — | — |

**BMAD corroborates this chain** — its greenfield flow *reportedly* runs analyst → project-brief → PM → PRD → architect (per secondary sources; the homepage confirms only "Idea→Foundation" + named agents), the same brief→foundation→spec progression as our trilogy — so the *structure* is independently corroborated. We **borrow** two concrete things from it: the agent-orchestrated **structured-document handoff**, and BMAD's **scoped-context** discipline — *each step receives only the artifacts it needs* (the spec author gets the brief slice + `reference.md`, not the whole history). We **decline** the autonomous-agent-company *engine* (AP2: survivorship-bias-flagged). OpenSpec's delta-specs and Intent's living-specs separately corroborate RFC-0019's proposal-first decomposition and auto-rollup coverage.

## Risks & what would make this wrong

- **Pre-mortem.**
  - *Inception becomes ceremony people skip.* Mitigation: the trigger gate (Decision 3) — it fires only for real decisions; throwaways stay on yolo.
  - *The "walking skeleton" becomes the throwaway it was meant to replace.* Mitigation: it's authored as a real spec through `work-loop`, kept and minimal — held to the same contract as any feature, not a sketch.
  - *Multi-agent envy* — pressure to make it an autonomous generator. Mitigation: Decision 4 declines it explicitly, with the survivorship-bias evidence.
- **Key assumptions (falsifiable).**
  1. Greenfield-with-real-decisions happens often enough among adopters to earn a front-door (Principle 4); if most new repos are throwaways, the gate sends them to yolo and this rarely fires.
  2. Composing existing skills + a walking skeleton genuinely beats yolo-then-cleanup in practice — the steel-thread claim holds for agent-built repos, not just human teams.
- **Drawbacks.** A new orchestrating skill to maintain; a soft ordering dependency on RFC-0019 + RFC-0020 landing first. Lower blast radius than 0019 (no core-template change) — it adds a skill and composes existing artifacts.

## Evidence & prior art

- **Spike / de-risk result.** *Riskiest assumption:* that a structured greenfield flow beats yolo. *Check (prior art, applied survey):* the walking skeleton / tracer bullet / steel thread is the cross-industry, decades-stable answer to exactly this — validate the architecture with a thin end-to-end slice rather than a throwaway — and Lean Inception is the established value-gated kickoff. Both are slow-moving (no recency penalty). The *agent-built-repo* generalization (Assumption 2) is the part not yet proven and is the Approver's call. See `0021-greenfield-inception-research.md`.
- **Repo precedent.** `adapt-to-project` (the brownfield twin this mirrors); RFC-0019 (brief, the inception output) and RFC-0020 (foundation, the foundation step); the `research` pack (applied mode, used in inception); `docs/adr/` (the foundation-decision log).
- **External prior art** (applied-mode survey, confidence-rated in `0021-greenfield-inception-research.md`): walking skeleton / steel thread ([Dolfing](https://www.henricodolfing.com/2018/04/start-your-project-with-walking-skeleton.html), [Rubick](https://www.rubick.com/steel-threads/)); [Lean Inception (Fowler)](https://martinfowler.com/articles/lean-inception/); spec-kit greenfield-first vs our brownfield-first ([spec-kit](https://github.com/github/spec-kit)). The spec-driven / agentic landscape we situate against: **[BMAD-METHOD](https://docs.bmad-method.org/)** — agent-orchestrated idea→foundation (analyst→brief→PM→PRD→architect per secondary sources); the closest cousin, whose *structure* we borrow and whose autonomous *engine* we decline alongside [MetaGPT (arXiv 2308.00352)](https://arxiv.org/abs/2308.00352) and ChatDev. **[OpenSpec](https://github.com/Fission-AI/OpenSpec)** — proposal-first + delta specs (corroborates RFC-0019). **[cc-sdd](https://github.com/gotalab/cc-sdd)** — Kiro-style discovery→spec→design→tasks→impl harness on Claude Code; its *discovery* is a **distinct upstream phase**, reinforcing our boundary that discovery is fed *in*, not owned by `init-project`. **Intent** (Augment Code) — living specs (corroborates 0019's auto-rollup). The throwaway-vs-structured gate is practitioner guidance, `[moderate]`.

## Open questions

1. **Walking skeleton in-scope vs handoff** — does `init-project` author+build the skeleton, or stop at the foundation and hand the skeleton to the normal loop? *Recommended default:* author the spec, hand the *build* to `work-loop` (`init-project` orchestrates, work-loop executes). Owner: eugenelim · decide-by 2026-06-20.

## Follow-on artifacts

Filled in on acceptance:

- ADR-NNNN: record the greenfield-front-door decision (new flow, not `adapt-to-project`; compose-not-autogenerate).
- Spec: `docs/specs/greenfield-inception/` — the `init-project` skill (trigger gate → inception → foundation → walking skeleton → handoff), composing `research` / brief / `reference.md` / spec / `work-loop`.
- Convention change: `docs/CONVENTIONS.md` — document the two front-doors (greenfield inception / brownfield adapt) and where each enters the loop.
- **User guides (in *this* catalogue repo, `docs/guides/`, via `new-guide`)** — authored as part of "done":
  - *Tutorial* — "From idea to a walking skeleton: start a new project."
  - *How-to* — "Decide and record your foundation during inception."
  - *Explanation* — "Why a walking skeleton beats a throwaway prototype."
