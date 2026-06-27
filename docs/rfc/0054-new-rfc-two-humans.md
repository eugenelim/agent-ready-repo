# RFC-0054: Right-size `new-rfc` for its two humans

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** @eugenelim
- **Date opened:** 2026-06-27
- **Date closed:** 2026-06-27
- **Decision weight:** heavy <!-- light | standard | heavy — proposed by Decision 1 of this RFC; set heavy here because it reverses a frozen-decision in RFC-0014 and changes a shipped, adopter-facing interface (see Reviewer brief → Stakes). Dogfooding the field this RFC proposes. -->
- **Related:** RFC-0014 (the frozen template + flow this revises), RFC-0025 (`work-loop` light/full router — the borrowed model), the `new-rfc` skill (`packs/governance-extras/.apm/skills/new-rfc/`), the shipped B-narrow spec (`docs/specs/new-rfc-readability/spec.md`).

## Reviewer brief

<!-- First-screen orientation — this is the section this RFC proposes (Decision 2). It is dogfooded here. -->

- **Decision:** Should `new-rfc` adopt four human-consumption changes that each revise or reverse a frozen RFC-0014 decision?
- **Recommended outcome:** **Accept** all four.
- **Change if accepted:** (1) a `Decision weight: light | standard | heavy` header field that right-sizes research depth and the pre-handoff gate; (2) this `## Reviewer brief` section; (3) "The ask" decisions rendered as a table; (4) a guided shape/intake phase before research.
- **Affected surface:** the shipped `new-rfc` skill + `assets/rfc.md` template (`governance-extras` pack), its how-to guide, and its Tier-4 eval. No code; no contract; no CONVENTIONS edit.
- **Stakes:** **costly-to-reverse** — this is a published, adopter-installed governance interface, and it reverses a decision RFC-0014 froze on the record. Not a one-way door (the template is forward-only and these are additive), but not cheap to walk back once adopters' RFCs use the new shape.
- **Review focus:** the honesty of the RFC-0014 reversal (Decision 1) — is the cut being *re-argued from evidence*, or quietly reintroduced? And whether changes 2–3 add reviewer-facing density rather than author-facing ceremony.
- **Not in scope:** the B-narrow changes already shipped in PR #423 (body-as-argument split, REVIEW READINESS handoff, short titles); editing RFC-0014 (frozen — this supersedes-in-part); any CONVENTIONS §3 change.

## The ask

- **Recommendation (BLUF):** Adopt four changes to `new-rfc` that make it serve its **two humans** — the *author* invoking it (changes 1, 4) and the *reviewer* consuming the output (changes 2, 3). Each revises or reverses a decision RFC-0014 froze, so it needs RFC governance, not a spec. The implementation (skill + template edits) is a follow-on spec after this is decided.
- **Why now (SCQA):**
  - *Situation* — RFC-0014 (2026-05-28) set `new-rfc`'s answer-first spine and research→draft→gate flow, and **explicitly cut a structural right-sizing field as ceremony**, betting that plain guidance would carry the same weight. It invited the test: "watch the next 2–3 real RFCs and cut what reads as ceremony."
  - *Complication* — ~40 RFCs have been opened since. Sampling the **21 most recent (0034–0053)**, the bet has not held: the survey ([`0054-notes/`](0054-notes/survey-rfcs-since-0014.md)) shows **1 of those 21** achieved lightness (and only by hand-improvising a bespoke section set); a field rename still cost 130 lines of full spine; decisions are routinely un-scannable on the first screen (RFC-0040 buries nine; RFC-0048's first decision is a 15-line block); and the index's own title cells have become paragraph-length abstracts. Meanwhile RFC-0025 *shipped* the light/full router for `work-loop`, demonstrating the model RFC-0014 feared as ceremony is not.
  - *Question* — should `new-rfc` adopt a depth-tier weight field, a reviewer-orientation block, a decisions table, and a guided intake step — and in doing so, reverse RFC-0014's recorded cut on the strength of the accumulated evidence?

**Decisions requested** (dogfooding the table this RFC proposes — Decision 3):

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Add a `Decision weight: light \| standard \| heavy` header field that scales research depth + pre-handoff gate, **reversing RFC-0014's cut of a structural right-sizing field**? | **Yes** | RFC-0014's plain-guidance bet was falsifiable and failed (1/21 went light); `work-loop`'s shipped light/full router proves the model isn't ceremony. | this review | Confirm the reversal is argued from evidence, not reintroduced silently. |
| D2 | Add a top-of-doc `## Reviewer brief` orientation section (revising RFC-0014 decision 1, the spine)? | **Yes** | Decisions are un-scannable on the first screen today; a fixed orientation grid is the reviewer's entry point. | this review | Confirm it earns its surface vs. "The ask" (de-dup, don't duplicate). |
| D3 | Render "The ask" decisions as a table (`ID · Question · Recommendation · Why · Decide by · Reviewer action`) instead of numbered prose (revising decision 1)? | **Yes** | Prose buries multi-decision asks (RFC-0040: 9; RFC-0048: 4-in-1); RFC-0038 already ships a starred *options* table as precedent. | this review | Confirm the table reduces density rather than adding ceremony (the new-adr objection). |
| D4 | Add a guided **shape/intake** phase before research — ask framing questions when intent is vague, infer and proceed when it's specified (revising RFC-0014 decision 2, the flow)? | **Yes** | Offer-don't-force, modeled on `frame-intent`/`receive-brief`/Shape Up; the research gate stays unchanged downstream. | this review | Confirm it's an *offer*, never a forced questionnaire. |

(This RFC changes a convention-adjacent shipped interface, so per `CONVENTIONS.md` §3 it requires explicit Approver sign-off — no silent-default adoption.)

## Problem & goals

**Diagnosis.** `new-rfc` was built (RFC-0014) for one reader — a reviewer who needs the decision on top — and one writer — an agent that must research before drafting. It does both jobs at a single weight. Two failures follow, and the second was predicted by RFC-0014 itself:

1. **Every RFC reads foundation-sized.** RFC-0014 cut a structural right-sizing field, betting plain guidance ("small reversible changes collapse to one-liners") would do the same job. The survey shows it did not: of the 21 most recent RFCs (0034–0053), 1 went light — by hand-improvising a bespoke section set; the rest carry the full spine regardless of stakes (see [`0054-notes/`](0054-notes/survey-rfcs-since-0014.md), Q3). A field rename cost 130 lines.
2. **The reviewer's entry is buried.** The decision a reviewer must make is a dense prose paragraph mixing question, recommendation, rationale, and date — un-scannable on the first screen (notes Q2). The index's own title column has degraded into paragraph-length abstracts (notes Q1, Exhibit 0). The short-title rule shipped in B-narrow is necessary but, the survey shows, not sufficient.

The unifying frame: `new-rfc` serves **two humans**, and currently optimizes for neither. The *author* (changes 1, 4) needs the ceremony to scale to the stakes and a way in when the idea is still vague. The *reviewer* (changes 2, 3) needs orientation and scannable decisions on the first screen.

**Goals.**
- Ceremony scales to stakes: a light RFC is *licensed* to collapse, a heavy one carries its full apparatus — and a reader can tell which from the header.
- A reviewer gets fixed first-screen orientation and a scannable decisions grid, on every RFC.
- An author with a vague idea gets a guided way in; an author with a sharp ask is not slowed by a questionnaire.
- Net author-facing surface does **not** grow for light RFCs — it shrinks.

**Non-goals** (could-have-been-goals deliberately dropped):
- *Not* editing RFC-0014 — it is Accepted and Frozen; this supersedes-in-part on the record.
- *Not* re-doing the B-narrow changes already shipped in PR #423.
- *Not* a CONVENTIONS §3 change — when to open an RFC is unchanged; only the skill + template move.
- *Not* a separate "mini-RFC" template or doc type (Uber/Casper two-track) — one template that right-sizes, not two to choose between.
- *Not* a new lint, hook, or engine — the changes are prose + template, read by the skill body, consistent with RFC-0014/0025's "no new subsystem" posture.

## Proposal

### D1 — `Decision weight: light | standard | heavy` (the reversal, argued)

A new optional header field. Its job is **not** to classify the door (reversible vs irreversible — the framing RFC-0014 cut); it is to **right-size and signal** how much research and gate ceremony the RFC carries, borrowing `work-loop`'s light/full mental model wholesale:

- **light** — reversible, narrow, single-pack-internal. One research sweep suffices; sections collapse to one-liners; pre-handoff gate = completeness checklist + one adversarial pass. (Citation-integrity still applies to any claim that does enter.)
- **standard** — the default and the omitted-field meaning. Full per-subpoint research + full gate, exactly as RFC-0014 specifies today.
- **heavy** — reverses a frozen ADR/RFC, crosses a governance/charter/security boundary, or is a one-way door. Full research + full gate + a mandatory de-risk spike + explicit Approver sign-off (no silent default). *(This RFC is `heavy`.)*

The skill picks a default weight from the same risk triggers `work-loop` uses (`packs/core/.apm/skills/work-loop/SKILL.md:61-76`) and lets the author override. The exact per-tier gate-trim table is left to the implementing spec (see Open questions).

**Confronting RFC-0014 directly.** RFC-0014 considered and cut a structural right-sizing/door field "as ceremony" (`0014:60`, `0014:140`, `0014:153`), on the explicit reasoning that "plain guidance carries the same weight without new required surface." This RFC reverses that core judgment — not by asserting the field is needed, but because RFC-0014 made a *falsifiable bet and invited the re-test*, and the test came back negative (notes Q3). Two things changed since 2026-05-28 that the original cut could not weigh: (a) the accumulated evidence that plain guidance did not produce right-sizing, and (b) RFC-0025 shipping the light/full router for `work-loop`, which is the existence proof that a weight signal need not be ceremony. The naming shift (door-*type* → depth-*weight*) is deliberate: a door classifier answers "how reversible?"; a weight tier answers "how much apparatus?" — and it is the latter that licenses the collapse RFC-0014 wanted but did not achieve.

### D2 — `## Reviewer brief` (the reviewer's entry)

A short, fixed orientation grid immediately under the header (dogfooded at the top of this RFC): Decision (one sentence) · Recommended outcome (accept/reject/amend) · Change if accepted (≤3 bullets) · Affected surface · Stakes (reversible/costly/one-way) · Review focus · Not in scope. It is the reviewer's first screen, every time, regardless of how the author wrote "The ask".

This **revises RFC-0014 decision 1** (the spine adds a section) and **inverts** the deliberately chat-only placement of the REVIEW READINESS block (`new-rfc/SKILL.md:187-203`): REVIEW READINESS proves the *gate* ran (author→reviewer handoff, chat); the Reviewer brief orients the *reviewer's read* (in-body, durable). They are different artifacts for different moments; the RFC keeps both and de-duplicates against "The ask" (which keeps BLUF + SCQA + the decisions table).

This also reverses a *more recent* decision than RFC-0014: B-narrow (PR #423) consciously kept the readiness summary in chat, "not written into the RFC body or template — closing the back door to a reviewer-brief surface RFC-0014 deferred" (`docs/specs/new-rfc-readability/spec.md:104`). That was the right call for the *gate-proof* artifact, which belongs at the handoff moment. The Reviewer brief is a different artifact — durable first-screen orientation the reviewer returns to while reading — so an in-body grid is the right reversal now, not a walk-back of B-narrow's reasoning about the readiness summary.

### D3 — decisions as a table

Render "The ask" → Decisions requested as a table: `| ID | Question | Recommendation | Why | Decide by | Reviewer action |` (dogfooded above). It replaces the numbered-prose list RFC-0014 specifies (`assets/rfc.md:22-23`) — **revising decision 1**. The `Reviewer action` column is new and load-bearing: it tells the reviewer what *they* must do per decision (confirm X, rule on Y), which prose asks omit. Precedent: RFC-0038 already ships a starred *options* table (`0038:90-94`); this extends the blessed-table pattern from options to decisions.

### D4 — guided shape/intake before research

A new step *before* the research gate (the gate itself is unchanged). When the author's intent is **vague**, the skill asks a small set of framing questions (what outcome · what's in/out · what's the bet) and synthesizes a proposal frame for confirmation before researching. When the ask is **already well-specified**, it infers the frame and proceeds — offer, don't force. This **revises RFC-0014 decision 2** (the flow gains a pre-research rung). The mechanic is lifted from `frame-intent`'s infer→confirm→ask-only-if-ambiguous ladder (`frame-intent/SKILL.md:32-38,63-68`) and `receive-brief`'s elicit-don't-force (`receive-brief/SKILL.md:48-63`).

### Migration

No data migration; forward-only. Edit point is the pack source `packs/governance-extras/.apm/skills/new-rfc/{SKILL.md,assets/rfc.md}` then `make build-self`; the how-to guide and Tier-4 eval update in the same implementing PR. Existing RFCs are Frozen history and are not retrofitted.

## Options considered

*Axis: where the **right-sizing + reviewer-orientation** logic lives. These four exhaust it — nowhere (A) / a structural depth signal in the existing template (B) / a reversibility classifier (C) / two separate templates (D).*

- **Option A — do nothing (keep RFC-0014's plain guidance).** *Cost of delay:* the two failures recur on every RFC; reviewers keep hunting for the decision and every RFC keeps reading foundation-sized. Rejected — this is precisely the state the survey measured as failing.
- **Option B — depth-weight field + reviewer brief + decisions table + guided intake, in the one template (recommended).** Targets both humans directly; reuses `work-loop`'s shipped router and `frame-intent`'s intake ladder, so net-new subsystem surface is zero. Trade-off: adds template surface — mitigated because the weight field *licenses* light RFCs to shed more than the brief/table add, so light RFCs get smaller, not larger.
- **Option C — reversibility door-type field (the RFC-0014 framing).** A `reversible | costly | one-way` classifier. Rejected for the same reason RFC-0014 cut it: classifying the door does not, by itself, license the collapse — it answers "how reversible?" not "how much apparatus?". The Stakes line in the Reviewer brief (D2) captures reversibility where it is actually useful to a reviewer, without a routing field.
- **Option D — two templates (mini-RFC vs full), Uber/Casper two-track.** Rejected: a chooser adds a decision before the RFC even starts and fragments the index; one template that right-sizes by a header field is lighter than two to pick between. (Casper's "lightweight RFCs vs 15-page TDRs" supports *that* tiering exists; it does not require *separate templates* to achieve it.)

## Risks & what would make this wrong

**Pre-mortem — assume this shipped and the result was bad. Why?**
- *The weight field became the ceremony RFC-0014 cut* → mitigation: it is optional, defaults to `standard` when omitted (so a light RFC that ignores it is unchanged), and its only job is to *subtract* on light RFCs. If authors set it and nothing collapses, it failed — which is the falsifiable assumption below.
- *The Reviewer brief just duplicated "The ask"* → mitigation: the brief is a fixed scannable grid (orientation); "The ask" keeps BLUF + SCQA + the decisions table (argument). The implementing spec must de-duplicate, not stack two BLUFs.
- *The decisions table tripped the same "ceremony" objection new-adr raised against MADR-full's tables* → mitigation: new-adr rejected per-*option* pros/cons tables for *alternatives*; this is a per-*decision* table for the *ask*, where density is the disease, not the cure. RFC-0040's nine prose decisions are the exhibit.
- *Guided intake became a forced questionnaire* → mitigation: it is explicitly offer-don't-force and infers silently on a well-specified ask; the implementing spec makes "proceed without asking when scoped" the default path.

**Key assumptions (falsifiable):**
- *A weight field makes light RFCs actually lighter.* Falsifiable by the next few light RFCs — if `weight: light` is set and sections still don't collapse, the field is ceremony and should be cut (the same test RFC-0014 set itself, now applied to its reversal).
- *A fixed Reviewer brief speeds the reviewer's first read.* Falsifiable: if reviewers still hunt past it into the body, the grid's fields are wrong.
- *Authors will set the weight honestly.* Falsifiable: if everything defaults to `standard`/`heavy`, the tiering collapses and the field is dead surface.

**Drawbacks.** More template surface for standard/heavy RFCs; one more pre-research rung in the flow; a second top-of-doc block (Reviewer brief) that must be kept from drifting against "The ask".

## Evidence & prior art

**Spike / de-risk result.** Riskiest assumption: a weight field + reviewer brief + table won't simply re-become the ceremony RFC-0014 cut. Analytical dogfood, grounded in the real survey: scored against the proposed shape, RFC-0048's 9-subdecision block becomes a scannable table, and RFC-0038 collapses to `weight: light` with a 3-line brief — net surface drops for light RFCs and rises in clarity for heavy ones. This RFC is itself written in the proposed shape (Reviewer brief, weight field, decisions table) as the live dogfood, exactly as RFC-0014 was written in its own proposed template. Honest limit: this is an analytical dogfood, not an A/B with live reviewers — the same "watch the next few RFCs" posture RFC-0014 took, carried as the first falsifiable assumption above.

**Repo precedent.**
- `work-loop` light/full router + risk triggers (`packs/core/.apm/skills/work-loop/SKILL.md:53-83`), shipped via RFC-0025 — the existence proof for D1 that a weight tier is not ceremony.
- research-pack mode tiers quick/standard/applied/deep (`packs/research/.apm/skills/research/SKILL.md:21-28`) — depth-by-tier prior art.
- de-risk-intent reversibility triage — "sets the default … does not lock it" (`de-risk-intent/SKILL.md:39-43`) — the soft-router shape D1 borrows.
- RFC-0038 starred options table (`0038:90-94`) and the template's "starred-recommended table encouraged" (`assets/rfc.md:61`) — table precedent for D3 (extended from options to decisions).
- `new-rfc` REVIEW READINESS chat-only block (`new-rfc/SKILL.md:187-203`) and "The ask" BLUF (`assets/rfc.md:14-25`) — the surfaces D2 must de-duplicate against.
- `frame-intent` intake ladder (`frame-intent/SKILL.md:32-38,63-68`); `receive-brief` elicit-don't-force (`receive-brief/SKILL.md:48-63,86-88`); `new-spec` assumption checkpoint (`new-spec/SKILL.md:29-34`) — the model for D4.
- The full 21-RFC survey backing the problem statement lives in [`0054-notes/survey-rfcs-since-0014.md`](0054-notes/survey-rfcs-since-0014.md); summarized in Problem & goals rather than pasted here.

**External prior art.**
- *Shaping precedes the formal write-up* (fetched and confirmed verbatim against the public page). Basecamp Shape Up, ["Principles of Shaping"](https://basecamp.com/shapeup/1.1-chapter-02) — "First we figure out how much time the raw idea is worth and how to define the problem. This gives us the basic boundaries to shape into," and shaping work "is rough … at a higher level of abstraction" before the pitch is packaged. Supports D4's shape-before-research rung.
- *Tiered design-doc weight exists in practice.* Casper, ["RFCs: Lightweight Technical Designs"](https://medium.com/caspertechteam/rfcs-lightweight-technical-designs-a508d93ccd34) — by its title and thesis, a deliberately lightweight RFC as a tier distinct from a heavyweight technical-design review. Corroborates (does not carry) D1's tiering and informs the rejection of Option D — separate templates aren't required to tier weight. *Verification caveat:* the article sits behind Medium's login wall; the title-level thesis is confirmable but the page body is not cleanly re-fetchable from here, so no specific in-body quote is relied upon. D1's load-bearing support is the in-repo evidence (the `work-loop`/RFC-0025 router and the survey), not this citation.
- *Reversibility sets the rigor budget* — carried forward from RFC-0014's already-verified citations (Amazon's 2016 shareholder letter; Mike Cvet on door-type as an RFC-review question, `0014:140`); not re-presented as freshly fetched. This RFC applies the *weight* framing rather than the door classifier RFC-0014 derived from these.

*Citation-integrity note:* a web-search summary repeatedly attributed a "two-track / proportionate-effort" claim to a Pragmatic Engineer article; direct fetches did not contain it, so it is **not** cited here.

## Open questions

*At acceptance (2026-06-27) both recommended defaults are adopted as the direction; their final form is settled in the implementing spec.*

- **Does `## Reviewer brief` sit above or fold into `## The ask`?** *Recommended default:* sit above as a distinct orientation grid, with "The ask" de-duplicated to BLUF + SCQA + the decisions table. *Owner:* @eugenelim. *Decide-by:* the implementing spec.
- **The exact weight → research-depth + gate-trim mapping.** *Recommended default:* the spec defines the per-tier table, mirroring `work-loop`'s light/full trims; this RFC fixes the principle (three tiers, default `standard`, risk-trigger-derived), not the table. *Owner:* @eugenelim. *Decide-by:* the implementing spec.

## Follow-on artifacts

On acceptance:
- **Spec:** `docs/specs/new-rfc-two-humans/` — the skill + template implementation: edit `packs/governance-extras/.apm/skills/new-rfc/{SKILL.md,assets/rfc.md}`, `make build-self`, run both lint surfaces (`lint-packs` + `tools/lint-agent-artifacts.py`), sync `docs/guides/governance-extras/how-to/new-rfc.md`, update the Tier-4 eval (`evals/evals.json`) with the new human-usability criteria, add a `docs/product/changelog.md` `[Unreleased]` entry, and bump `governance-extras` (`0.3.2 → 0.4.0` — new template/skill surface).
- **ADR:** only if a future RFC contests the direction; this RFC + the skill diff are the durable record otherwise (mirroring RFC-0014's choice).
- No CONVENTIONS §3 edit — see Non-goals.
