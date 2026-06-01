# RFC-0020: Reference-architecture foundation — the repo's golden-path anchor that LLDs conform to

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-01
- **Date closed:** 2026-06-01
- **Related:** RFC-0019 (the LLD reads `reference.md` when present — Decision 9, the consumer); RFC-0021 (greenfield inception — its foundation step authors `reference.md`); RFCs 0001–0003 (the pack-catalogue model that opt-in stack packs extend); `docs/CONVENTIONS.md` §"document hierarchy"; the `adapt-to-project` skill (Class-3 discovery, extended here for harvest); `docs/CHARTER.md` §Principles.

## The ask

- **Recommendation (BLUF):** Add a **normative** reference-architecture document — named **`reference.md`** — at `docs/architecture/reference.md`: the repo's *golden path* (stack, internal frameworks, component catalogue, stereotypes, cross-cutting standards) that the agent treats as **steering** — persistent, always-applied context every design conforms to, the architecture-altitude companion to `AGENTS.md`'s conventions-steering — kept distinct from the **descriptive** `overview.md` (the code map). **Instantiate it on demand from a template** (the `new-spec`→`spec.md`/`plan.md` pattern — a template in a skill asset), **not** as a pre-placed core seed, so there's no shipped file for an add-on pack to collide with. Populate it by **repo context** — greenfield authoring (RFC-0021), brownfield **harvest** (extend `adapt-to-project` Class-3, fed by repo detection), or an opt-in **stack pack** (pre-bake). Use arc42 vocabulary for its sections.

- **Why now (SCQA):**
  - *Situation.* RFC-0019 gives every feature a low-level design that should conform to a *shared* architecture; its Decision 9 has the LLD read `reference.md` when present.
  - *Complication.* We ship a **descriptive** code map (`overview.md`, in the spirit of matklad's `ARCHITECTURE.md`) but **no normative foundation** for the LLD to read — so the LLD falls back to re-deriving the stack every time, and there is no home for the org's golden path.
  - *Question.* Where does the golden path live, how is it distributed, and how is it populated across greenfield/brownfield/enterprise — without baking any one tech stack into universal core?

- **Decisions requested:**
  1. **Artifact + name** — add a normative doc distinct from `overview.md`, named **`reference.md`** (`foundation.md` considered and rejected as less industry-recognizable). *Recommended.* Decide-by 2026-06-13.
  2. **Sections** — use **arc42** vocabulary (Constraints · Solution strategy · Building-block view/component catalogue · Crosscutting concepts/standards), not invented headings. *Recommended; see Options.* Decide-by 2026-06-13.
  3. **Distribution** — `reference.md` is **generated on demand from a template asset** (like `spec.md`/`plan.md`), **not** a pre-placed core seed — this avoids a *guaranteed* core-vs-stack-pack seed collision. (`overview.md` stays a core seed: it has no competing producer.) *Recommended.* Decide-by 2026-06-13.
  4. **Population** — by repo context: greenfield authoring (RFC-0021) · brownfield harvest (`adapt-to-project`, fed by detection) · stack-pack pre-bake. *Recommended.* Decide-by 2026-06-13.
  5. **Harvest** — extend `adapt-to-project` Class-3 discovery to propose a draft `reference.md` from existing code, rather than a new harvester skill. *Recommended.* Decide-by 2026-06-13.
  6. **Stack specifics** — pre-baked by **opt-in stack packs** (each a follow-on), never baked into core. *Recommended.* Decide-by 2026-06-13.

## Problem & goals

`docs/architecture/overview.md` answers *"where is the thing that does X"* — matklad's rule for `ARCHITECTURE.md` is to *"only specify things that are unlikely to frequently change"* ([matklad](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html)). That is **descriptive**. What's missing is the **normative** counterpart: the golden path a design must *conform to* — the stack, the internal framework building blocks, the component stereotypes, the cross-cutting standards (security, observability, resilience defaults). This is the altitude enterprise architecture draws between the framework and its application: *"Enterprise Architecture establishes the overarching strategic framework and guidelines, while Solution Architecture interprets and applies these directives"* ([Ardoq](https://www.ardoq.com/knowledge-hub/enterprise-architecture-vs-solution-architecture)). Without a normative anchor, RFC-0019's LLD has nothing org-specific to conform to and re-derives the stack each time.

### Goals

- A single **normative** anchor (`reference.md`) the LLD conforms to and references by name, **instantiated on demand from a template** (the `spec.md`/`plan.md` pattern), so every adopter can generate the skeleton with no pre-placed seed to collide against.
- **Greenfield, brownfield, and enterprise** each reach a populated foundation — authored (0021), harvested (adapt-to-project), or pre-baked (stack pack).
- Keep **core stack-neutral**; let opt-in **stack packs** carry the stack specifics.
- Reuse existing machinery — the template-asset instantiation pattern (the `spec.md`/`plan.md` precedent), `adapt-to-project` discovery, the pack catalogue — rather than building new mechanisms.

### Non-goals

- **A vendor/cloud "reference architecture" blueprint.** This is the *repo's own* golden path, not an AWS-style solution template.
- **Replacing `overview.md` or the ADR log.** `overview.md` stays the descriptive map; ADRs stay the decision audit trail; `reference.md` is the normative foundation between them.
- **Baking a stack into core.** Stack specifics live only in opt-in packs or the populated instance.
- **Authoring specific stack packs here.** This RFC defines the *contract* a stack pack fills; individual packs (React, Spring, …) are follow-on specs.
- **Changing the spec/plan templates.** Reading `reference.md` is RFC-0019's Decision 9; this RFC ships the doc + how it's populated, not a spec/plan change.
- **A runtime service registry / infra inventory.** The foundation documents the design golden path, not live infrastructure state.

## Proposal

### The artifact, named and distributed (Decisions 1, 2, 3)

`docs/architecture/reference.md` — normative, durable, low-churn. **Generated on demand from a template, not pre-seeded.** The arc42-section skeleton lives as a **skill asset** (the `new-spec`→`spec.md`/`plan.md` pattern: a template instantiated per use, never shipped as a pre-placed doc); whichever population path runs instantiates it into `docs/architecture/reference.md`. This is the deliberate fix for a **guaranteed-collision** problem: if core *seeded* `reference.md`, every stack pack that ships its own would collide — the bundler errors on differing-content seed collision at self-host and forces a `.upstream` dance at install. Because nothing is pre-placed, the population path that runs is the **sole producer** and there is nothing to collide against. The *template* (not a seeded file) is the shared contract a stack pack pre-bakes and a harvest writes into. `overview.md` is different — it stays a core seed because it has exactly one producer ever (the adopter mapping their own code) and no pack competes to provide it.

Sections use **arc42** vocabulary — four of arc42's twelve sections — so the structure is recognizable rather than bespoke:

- **Constraints** (arc42 §2) — fixed technical/organizational constraints every design honors.
- **Solution strategy** (arc42 §4) — the stack and fundamental technology choices.
- **Building-block view / component catalogue** (arc42 §5) — the reusable internal components and framework building blocks an LLD composes from, named so an LLD can reference them.
- **Crosscutting concepts / standards** (arc42 §8) — the org's defaults for security, observability, resilience, error handling, accessibility.

`overview.md` (descriptive map) and `reference.md` (normative golden path) are siblings under `docs/architecture/`; RFC-0019's LLD reads `reference.md` when present and degrades to detection + elicitation when absent.

**`reference.md` is steering, not just a doc (learned from cc-sdd/Kiro and OpenSpec).** Kiro/cc-sdd carry a *steering* concept — persistent project context the agent applies on every task — and OpenSpec keeps source-of-truth specs every change reconciles against. `reference.md` is that, at the architecture altitude: not a reference an LLD optionally consults, but the **always-applied golden path** a design *conforms to* (and a reviewer checks conformance against). This sharpens the consumer relationship in RFC-0019 Decision 9 from "reads if present" to "conforms to the steering when present" — the same posture `AGENTS.md` already holds for conventions. It also bounds scope: steering is *durable golden-path*, not per-feature design (that stays in the plan) and not live infra state.

### Populating it, by repo context (Decisions 4, 5, 6)

Three population paths, one per repo context; **detection feeds the harvest** (it is not a standalone path):

1. **Greenfield → authoring (RFC-0021).** The inception flow's foundation step authors `reference.md` (stack chosen with recorded rationale) — spec-kit's "constitution first" ([spec-kit](https://github.com/github/spec-kit)).
2. **Brownfield → harvest (extend `adapt-to-project` Class-3).** Detect the stack + reusable components + recurring patterns from existing code and **propose a draft** `reference.md` the adopter confirms/edits — a discovery output written under the existing path-jail (the Class-3 "Contract relocation" propose-and-confirm shape), not a new skill.
3. **Enterprise → stack pack (opt-in pre-bake).** A stack pack ships pre-baked `reference.md` content — its component catalogue, stereotypes, standards — plus optional stack-specific LLD guidance. This keeps core stack-neutral, exactly as `atlassian` (Jira-specific) and `converters` (format-specific) already do.

   **Delivery (grounded in the bundler's actual behavior).** Because core does **not** pre-place `reference.md`, the population path that runs is the **sole producer** — a stack pack ships its filled `reference.md` as an ordinary seed with **nothing to collide against**. The only collision case is *two* producers for one repo (two stack packs, or a stack pack atop an adopter's existing `reference.md`): the bundler has **no pack-override field** and errors on differing-content seed collision at self-host (`self_host.py` `_project_seeds`) / writes a `.upstream` companion at install (`commands/_common.py`), so that narrower case routes through the **`.upstream` + `adapt-to-project` merge** (the path adopter customization and copier-style updates already use). A stack pack **never** ships `overview.md`. The stack-pack-contract spec (follow-on) defines this; no new override field is introduced.

The pattern is **detect → curate → LLD-reads** (brownfield) and **author → LLD-reads** (greenfield): the foundation is curated once and read thereafter, not re-derived per spec.

## Options considered

Each requested decision's option space, MECE along a stated axis. A literal do-nothing row appears for Decisions 1, 3, and 4 (the axes that admit it); Decisions 2, 5, 6 carry a weakest-leverage option instead of a literal do-nothing, since their axes presuppose the artifact and a population path exist. The global do-nothing (no foundation at all) is Decision 1's last row.

### Decision 1 — Artifact locus + name — *axis: where the normative golden path lives*

| Option | Trade-off |
| --- | --- |
| **New `reference.md`** ★ | Clean descriptive/normative split; one durable doc; industry-recognizable name |
| `foundation.md` (same doc, different name) | Avoids the vendor-blueprint reading of "reference architecture" — but less recognizable; kept as the fallback if that reading proves common |
| Fold into `overview.md` | One file — but conflates "where things are" with "what to conform to"; violates matklad's descriptive-only rule |
| Put it in `CHARTER.md` / `CONVENTIONS.md` | Reuses a doc — but CHARTER is product mission, CONVENTIONS is process; neither is the technical golden path |
| Do-nothing | No new doc — but the LLD has no anchor and re-derives the stack each time |

### Decision 2 — Section vocabulary — *axis: how the doc is structured*

| Option | Trade-off |
| --- | --- |
| **arc42 (4 of 12 sections)** ★ | Recognized template; the four normative sections (§2/§4/§5/§8) map exactly to constraints/stack/components/standards | 
| C4 model | Strong for diagrams/views, but it's a visualization model, not a normative-standards vocabulary |
| Invented headings | Tailored — but bespoke, unrecognizable, and re-litigated per repo |
| Reuse `overview.md`'s headings | Consistent with the map — but those are descriptive-codemap headings, wrong for normative standards |

### Decision 3 — Distribution — *axis: how the skeleton reaches the adopter*

| Option | Trade-off |
| --- | --- |
| **Template instantiated on demand** ★ (skill asset, the `spec.md`/`plan.md` pattern) | One sole producer per repo; **nothing pre-placed to collide with**; the template is still the shared contract |
| Core pack document seed (parallel to `overview.md`) | Discoverable — but **guarantees a collision** with every stack pack that ships its own `reference.md` (build errors / install companions). Rejected for that reason — this is the flaw the user flagged |
| Non-core pack | Keeps core lean — but a core-only adopter wouldn't get the template, and the foundation is baseline |
| Adopter authors from scratch (do-nothing) | Zero shipped surface — but every adopter reinvents the arc42 structure |

### Decision 4 — Population — *axis: how the foundation gets filled, by repo context*

| Option | Trade-off |
| --- | --- |
| **By repo context (author / harvest / pre-bake)** ★ | Covers greenfield + brownfield + enterprise; detection feeds harvest | 
| Harvest only | Fails greenfield (nothing to harvest) |
| Authoring only | Ignores existing code; high manual cost on brownfield |
| Do-nothing | Foundation is never populated; the template is never instantiated |

### Decision 5 — Harvest mechanism — *axis: what writes the brownfield draft*

| Option | Trade-off |
| --- | --- |
| **Extend `adapt-to-project` Class-3** ★ | Reuses the discovery engine + path-jail + propose-and-confirm; harvest *is* discovery | 
| New harvester skill | Duplicates discovery; another skill to maintain |
| Manual only | No leverage; defeats the brownfield goal |

### Decision 6 — Stack specifics — *axis: who carries the stack*

| Option | Trade-off |
| --- | --- |
| **Opt-in stack packs** ★ | Core stays universal (Principle 1); precedented by `atlassian`/`converters` | 
| Bake into core | Violates universality; rots for non-matching adopters |
| Adopter-authored only | Works, but every org re-authors the same React/Spring golden path from scratch |

## Risks & what would make this wrong

- **Pre-mortem.**
  - *The foundation rots — written once, never maintained, and the LLD conforms to a lie.* Mitigation: it's normative and low-churn by design; give it a named owner and a verification cadence matched to its volatility (general documentation practice).
  - *Harvest mis-infers the architecture.* Mitigation: harvest only *proposes a draft*; the adopter curates before it's authoritative — the confirm gate `adapt-to-project` already uses.
  - *An instantiated-but-unfilled `reference.md` invites cargo-cult half-filling.* Mitigation: the template carries guidance that it's filled when there are real architecture decisions (the throwaway gate of RFC-0021); a thin repo simply never instantiates it.
  - *"Reference architecture" is read as a vendor blueprint.* Mitigation: the Non-goal states it's the repo's own golden path; `foundation.md` is the Decision-1 fallback name.
  - *Two producers target `reference.md` (e.g. two stack packs).* Mitigation: core pre-places nothing, so the common case has a sole producer and no collision; the two-producer case routes through the `.upstream` companion + `adapt-to-project` merge (the bundler has no override field and errors on raw seed collision). This is exactly why Decision 3 rejects a core seed — pre-seeding would make the collision *universal* rather than this narrow two-producer case. Stack packs never ship `overview.md`.
- **Key assumptions (falsifiable).**
  1. A *normative* foundation (distinct from the descriptive map) is reached often enough to earn a first-class template-instantiated doc (Principle 4) — rather than teams being served by `overview.md` + ADRs alone.
  2. arc42's four chosen sections are universal enough to hold any adopter's golden path without privileging a stack or domain.
- **Drawbacks.** A new template asset to own; an `adapt-to-project` extension to build and test; a stack-pack contract to specify; one CONVENTIONS hierarchy-diagram edit. **Blast radius is bounded to the architecture-doc surface** — it adds a template asset + extends one skill + one convention line; it does **not** touch the core `spec.md`/`plan.md` templates (that's RFC-0019). The foundation is **consumed** by RFC-0019's LLD (Decision 9), so it is not inert.

## Evidence & prior art

- **Spike / de-risk result.** *Riskiest assumption:* that the descriptive/normative split is real and not redundant with `overview.md`. *Check:* matklad's `ARCHITECTURE.md` is explicitly descriptive (codemap; "only specify things unlikely to change"); arc42 carries normative content in *separate* sections (§2/§4/§5/§8); spec-kit's **constitution** is a normative anchor authored before code. Three independent traditions draw the same line — **the split is real**, `overview.md` ≠ `reference.md`. Holds. The *frequency* question (Assumption 1) is the Approver's product call, mitigated by reusing the seed + discovery machinery so cost-if-rare is low.
- **Repo precedent.** `new-spec`'s `spec.md`/`plan.md` (templates in a skill asset, instantiated on demand — the distribution precedent `reference.md` follows, **not** pre-seeded); `docs/architecture/overview.md` (descriptive map, a core seed — but it has no competing producer, hence safe to seed, *unlike* `reference.md`); `docs/adr/` (decision log); `adapt-to-project` Class-3 discovery + path-jail + propose-and-confirm (the harvest host); RFCs 0001–0003 (the pack-catalogue model stack packs extend); `packs/atlassian` and `packs/converters` (opt-in, deliberately non-universal packs — the stack-pack precedent). RFC-0019 Decision 9 is the consumer that reads this foundation.
- **External prior art.** [arc42 template](https://arc42.org/overview) — the four normative sections this adopts; [matklad — ARCHITECTURE.md](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html) — descriptive codemap (Redis/rust-analyzer/Tauri); [GitHub spec-kit](https://github.com/github/spec-kit) — the constitution as a normative anchor; [Ardoq — EA vs SA](https://www.ardoq.com/knowledge-hub/enterprise-architecture-vs-solution-architecture) — the framework-vs-application *altitude* (cited only for that distinction; the page does not define "reference architecture"). The "named owner + verification cadence" is general documentation practice `[synthesis]`, not a single-source claim.

## Open questions

1. **Harvest trigger** — run at install vs on-demand via `adapt-to-project`. *Recommended default:* on-demand (the adapt flow already gates dirty-state and confirmation). Owner: eugenelim · decide-by 2026-06-20.
2. **Stack-pack naming convention** — how stack packs are named/namespaced in the catalogue. *Recommended default:* defer to the first stack-pack spec; not load-bearing here. Owner: eugenelim · decide-by 2026-06-20.

## Follow-on artifacts

Filled in on acceptance:

- ADR-NNNN: record the reference-architecture-foundation decision (normative `reference.md` distinct from descriptive `overview.md`; template-instantiated-on-demand distribution, **not** a pre-placed seed; population by repo context; `adapt-to-project` harvest).
- Spec: `docs/specs/reference-architecture/` — the `reference.md` **template asset** (arc42 sections, instantiated on demand like `spec.md`/`plan.md` — **not** a pre-placed seed), the `adapt-to-project` Class-3 harvest extension, and the stack-pack contract (what a pack pre-bakes and how it delivers).
- Spec(s): the first **stack pack(s)** (e.g. a frontend and a backend pack) — downstream, each clearing the charter bars on its own.
- Convention change: `docs/CONVENTIONS.md` — amend the document-hierarchy diagram to add `reference.md` under `architecture/`, distinguished from `overview.md`.
- **User guides (in *this* catalogue repo, `docs/guides/`, via `new-guide`)** — authored as part of "done"; this repo ships a guide on **`reference.md` and how to use it**:
  - *Tutorial* — **"Create and use your `reference.md`"**: establish it (greenfield via `init-project` / brownfield via harvest / stack-pack pre-bake), then *use* it — how a design conforms to it, how to reference its components and stereotypes by name, and how the LLD (RFC-0019, Decision 9) reads it as steering.
  - *How-to* — "Establish your repo's reference architecture" (greenfield author / brownfield harvest / stack-pack pre-bake).
  - *Explanation* — "Foundation vs. map": why `reference.md` (normative steering) and `overview.md` (descriptive) are separate, and why `reference.md` is template-instantiated rather than seeded.
  - *Reference* — the `reference.md` arc42 sections and the stack-pack contract.
