# ADR-0033: The intent `Level` is reopened to an open recognized set (`product-vision › product-strategy › capability › feature`) and decoupled from `Scale` — a refinement of ADR-0019, prompt-only

- **Status:** Accepted <!-- Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-23
- **Decision-makers:** eugenelim
- **Consulted:** RFC-0043 (the accepted decision this records, incl. its no-engine-change spike result and the D1–D6 decision set); the spec-stage adversarial + design review of this ADR and the implementing spec
- **Supersedes:** none
- **Related:** ADR-0019 (the recursive level-tagged `intent` ontology this **refines** — its part 1 `Level` enum, not its whole; ADR-0019 stays Accepted and its parts 2–3 stand) · RFC-0043 (the accepted decision this ADR records) · RFC-0030 (the `product-engineering` pack's founding RFC, whose steel-thread already named a "vision/intent root" this ships) · RFC-0019 (`receive-brief`, the level-agnostic universal receiver this does not touch) · core `init-project` (the greenfield front door the seam connects to) · `docs/specs/product-rung/` (the implementing spec these decisions are confirmed against)

## Context

RFC-0030 / ADR-0019 (both Accepted 2026-06-13) shipped the `product-engineering` pack: product shaping as a **recursive, level-tagged `intent` tree** whose leaf is a shippable spec/slice, with `Level` **open by design** ("the levels disagree across tools… reifying the pyramid encodes the story=spec falsehood" — ADR-0019, *Alternatives*, rejecting fixed SAFe ladders). The v1 implementation, however, has two coupled defects that trace to one over-narrowing:

- **The ladder tops out at `capability`.** The shipped `Level` enum is `capability | feature` (`intent-template.md:11`), and `intent-model.md` defines `capability` as *architectural span* with an *architectural/adoption* de-risk kind. A greenfield **product concept** — a bet about whether a product should exist at all, for whom, through what wedge — is neither a feature nor an architectural span. That altitude has no rung, even though ADR-0019 intended `Level` to be open.
- **`Level` is welded to `Scale`.** `scale-intake.md:29` stamps `app → feature` / `business-unit → capability`, and `frame-intent` step 3 nudges hard ("At `app` Scale most intents are `feature`-level"). So "one repo" is treated as proof you already know your feature. Scale (how many repos) and Level (altitude of the bet) are orthogonal; fusing them mis-routes every single-repo product concept.

The consequence, observed in practice (n=1, the reporting user): a product concept fed to `frame-intent` either collapses to a single feature intent (altitude lost) or fans out into **multiple feature intents with no shared parent** — sibling bets that each silently re-assume the product should exist, whose "does anyone want this" question is tested piecemeal (validation theatre) or not at all.

Constraints in force when deciding:

- **CHARTER Principle 3 (a habit, not infrastructure).** The pack ships prompt-only doctrine the agent reasons from — markdown, file-per-artifact — never a runtime engine, hook, or executable tooling. This forecloses importing a heavyweight product-ops toolkit's machinery (a large fixed-type ontology, write-time hooks, mandatory phase-gates, a multi-section handoff packet).
- **CHARTER Principle 2 (no duplication).** A capability belongs in exactly one place; a parallel `vision.md` / `strategy.md` artifact type that forks the one recursive `intent` is rejected.
- **ADR-0019's "one recursive artifact at every level" model.** A capability intent, a feature intent, and a PRD are the *same artifact* at different `Level`s. Any product rung must be the same shape one level higher, not a new type.
- **ADR-0019's "no fixed ladder."** `Level` is open by design; a closed, N-deep `product→strategy→capability→feature→story` ladder is the SAFe shape ADR-0019 already rejected.
- **The pack's altitude:** name the bet and the question it forces; reuse the existing recursion, de-risk, and decomposition mechanisms rather than adding new ones.

RFC-0043 settled *whether* and *how* to close these gaps (decisions D1–D6), with the riskiest assumption — that this is enum + prompt work needing **no engine change** — confirmed by a spike against the shipped pack (the recursion already produces "the next level down" at any level; the Scale→Level edit is a stamp→suggestion change that does **not** sever Scale's load-bearing leaf-projection role; the `market-existence` bet reuses `kill-condition.md`'s pre-PMF qualitative bar). This ADR records the load-bearing, expensive-to-reverse calls — the *artifact-model commitment*, the *open-field shape*, the *Level/Scale decoupling*, the *distinct de-risk kind*, and the *cross-pack seam* — so a future maintainer doesn't re-litigate them. The mechanical detail (the exact field-set bullets, the prompt wording, the tracker-projection rows, the sibling-spawn trip text) is spec-level and lives in the implementing spec, not here.

## Decision

> We **refine ADR-0019's intent ontology**: `Level` is an **open** field carrying a **recognized set** — `product-vision` › `product-strategy` › `capability` › `feature` — and is **decoupled from `Scale`**, whose Level role becomes a *suggested starting altitude* rather than a silent stamp (its leaf-projection role is preserved). The two product rungs are **higher `Level`s of the same recursive `intent` artifact** (not a new type), the product-existence bet is a **distinct de-risk kind** (`market-existence` = market desirability + viability, not the feature-level `desirability` token reused), and core's `init-project` gains `intent` / `frame-intent` as a **fourth recognized discovery source, by reference only**. The mechanism is **prompt-only — no engine, hook, new skill, or new artifact type.**

**D1–D4 below refine ADR-0019's part 1** (the `Level` enum and its Scale coupling); **D5 is a net-new cross-pack decision** that ADR-0019 did not address (it never mentions `init-project`) — so this ADR is a refinement *and* a new structural call, and the scope claim is split rather than overloaded. ADR-0019's part 2 (a brief is a feature-level intent projected onto one repo; `receive-brief` stays in `core`, level-agnostic, no `level:` field) and part 3 (contracts mature by SDLC stage) **stand untouched**; ADR-0019 remains **Accepted** with a `Refined by: ADR-0033` back-pointer added to its header (a metadata-only edit; its body stays immutable). ADRs are immutable, so this realignment is recorded as a new ADR rather than a body edit.

Five sub-decisions, each expensive to reverse. (These are this ADR's grouping of the load-bearing calls; they map to RFC-0043's Proposal decisions **D1–D4 + D6**. RFC-0043's D5 — the seeded field sets — is mechanical and lives in the implementing spec, not here.)

- **D1 — Artifact model: a new rung is a higher `Level` of the same recursive `intent` (the option choice).** `product-vision` and `product-strategy` are the existing `intent` artifact at a higher altitude — they reuse the recursion (`recursive-decomposition.md`), the per-intent de-risk loop, and the decomposition boundary, and require no new file type, layout, discovery wiring, or hook. This is the call that keeps the pack inside ADR-0019's "same artifact at every level" model and away from the heavyweight-toolkit mass a parallel artifact type accretes.
- **D2 — `Level` is open with a recognized set (reopen, don't re-narrow).** The field stays string-valued and open (an adopter may name an intervening altitude); the recognized set `product-vision › product-strategy › capability › feature` names the altitudes the skills prompt for and the templates seed. This **realigns the implementation with ADR-0019's "open by design" decision** rather than reversing it — the v1 `capability | feature` enum over-narrowed an intentionally open ontology. Lint cannot enforce a closed set; that is the accepted cost of an open field.
- **D3 — `Level` is decoupled from `Scale` (the root-cause fix).** `Scale` carries two roles in `scale-intake.md`: it sets the *default Level* **and** the *leaf-projection* (`app` → a same-repo brief; `business-unit` → a per-component slice). This decision changes **only the first** — the Scale→Level *stamp* becomes a *suggested starting altitude* (`app` greenfield concept → offer `product-vision`; `app` known feature → `feature`; `business-unit` → `product-strategy` or `capability`), overridable in one word. The Scale→leaf-projection role is **preserved unchanged** — it is load-bearing for `app` vs `business-unit` leaf shape (ADR-0019 part 2) and severing it would break the brief projection.
- **D4 — The product-existence bet is a distinct de-risk kind, `market-existence`, never the `desirability` token reused.** `de-risk-intent` maps the dominant assumption kind to the intent's level (`capability → architectural/adoption`; `feature → desirability`). The product rungs add one row: `product-vision` / `product-strategy` → **`market-existence`** = will-anyone-want-this-at-all (market desirability) **+** can-this-be-a-business (viability) — closing the Cagan/SVPG viability risk the pack does not cover today. It is **categorically distinct** from `feature → desirability` ("do users want *this feature*"); giving both the same token is exactly the conflation that produces validation theatre, so the kinds get **different tokens** and the prose says so. It reuses `kill-condition.md`'s existing pre-PMF **qualitative-bar** machinery — no new de-risk mechanism — and is tested **once at the top**, not re-litigated N times across sibling features.
- **D5 — The `init-project` seam is a by-reference cross-pack edge (recorded here because it is structural).** Core's `init-project` stage 2 ("value gate") consumes fed-in discovery from three named sources (`research`, a PRD, a `receive-brief` brief) and never names `frame-intent`. The decision adds `intent` / `frame-intent` as a **fourth recognized discovery source** and documents that `frame → de-risk → decompose` hands its leaf into `init-project`. `init-project` composes **by reference, never by import**, and **performs no discovery itself**; the seam respects both — it names one more upstream discovery *shape* `init-project` *receives*, importing nothing from `product-engineering`. Because this adds a named cross-pack reference (a structural change under `docs/CONVENTIONS.md`'s risk triggers), it is recorded in this ADR and the spec, not merely a changelog line.

Boundaries on the decision:

- **No new artifact type, file layout, hook, engine, or skill.** The change is an enum widening, prompt edits, two seeded level-conditional field blocks, one de-risk-kind row, tracker-projection rows, and one by-reference seam doc — prose only, consistent with Principle 3 and the rest of the pack.
- **Neither rung is mandatory; either is authorable directly; skipping is allowed but observable.** A feature-first repo never sees the rungs. A *sibling-spawn detector* (qualitative: the intent won't reduce to a single shippable slice) **offers** to frame the product parent — it never blocks. A *retroactive-parent* affordance reconstructs and back-links a parent via the existing `Parent intent:` field, at an **inferred** altitude (architectural slices of one buildable thing → `capability`; independent value bets that together make one product → `product-vision`/`product-strategy`), named and user-correctable.
- **The fixed `product→strategy→capability→feature→story` ladder is rejected** — it is the closed SAFe ladder ADR-0019 already rejected and RFC-0043 lists as a non-goal. Two *seeded* rungs over an *open* field is the middle that prior art supports and the charter tolerates.
- **One merged product rung is rejected** — it would lose the well-attested vision (the existence bet) vs. strategy (the path) distinction.
- **`receive-brief`'s level-agnostic contract and Scale's leaf-projection role are out of scope** — both are ADR-0019 part 2 and are preserved.

## Decision drivers

- **The shipped v1 over-narrowed an intentionally-open ontology (ADR-0019).** Drives D2 — reopen `Level` to a recognized set rather than inventing a new mechanism.
- **The Scale→Level weld is the root cause of the observed misroute.** Drives D3 — decouple the stamp into a suggestion while preserving leaf-projection.
- **CHARTER Principle 3 (habit, not infrastructure).** Rules out the heavyweight product-ops toolkit's hooks / phase-gates / fixed-type ontology; drives D1's prose-only, same-artifact choice.
- **CHARTER Principle 2 (no duplication) + ADR-0019's one-recursive-artifact model.** Rule out a parallel `vision.md` / `strategy.md` type; drive D1.
- **The Cagan/SVPG four-risks viability gap.** The pack covers value + feasibility but not viability; drives D4's distinct `market-existence` kind.
- **RFC-0030's steel-thread already named a "vision/intent root" above outcome** that v1 collapsed. This decision ships the root that founding RFC anticipated, rather than adding a novel concept.
- **The no-engine-change spike** (RFC-0043 Evidence). Confirms the whole change is enum + prompt + field-set work; nothing here needs a code or recursion change.

## Consequences

**Positive:**

- The product altitude gets a home **inside the one recursive `intent` model** — no new artifact type, layout, discovery wiring, or hook — so a greenfield product concept stops misrouting to a feature intent, and the existence bet is anchored and de-risked **once at the top** instead of piecemeal across orphaned siblings.
- **Reuses what already ships**: the recursion, `de-risk-intent`'s kill-condition loop (including the pre-PMF qualitative bar), and `decompose-intent`'s upward-feedback / `Parent intent:` edge. The change is additive and the migration is empty — existing `capability`/`feature` intents stay valid, since the recognized set is a superset.
- **Scale and Level become orthogonal**, so an `app`-Scale (one-repo) greenfield concept can legitimately start at a product altitude, while Scale keeps doing the one job it must (leaf-projection shape).
- **Closes the greenfield seam** between the product loop and core's repo front door without coupling code — `init-project` receives one more discovery shape by reference.

**Negative:**

- **Two more recognized levels widen the surface** every `product-engineering` skill reasons about (frame, de-risk, decompose, tracker-projection, the guide). More prose to keep coherent.
- **An open `Level` field trades enum-tidiness for flexibility** — lint cannot enforce a closed set, so a typo'd or off-ladder `Level` is caught by a reviewer, not a gate.
- **The `init-project` seam couples a `core` doc to a `product-engineering` concept by name** (not by import) — a small narrative coupling that a pure-engineering adopter who never installs the product pack reads as a dangling reference to an optional upstream.

**Neutral / to revisit:**

- **Adopter demand is n=1** (the reporting user). The design's optionality makes it a low-cost bet even if uptake is thin; revisit on post-ship feedback (RFC-0043 OQ3).
- **Tracker-projection rows for the two rungs** are settled at spec time to the higher/intervening-tier default (Jira Align Theme/Strategy tier; Linear → Initiative/label; `none` → markdown) (RFC-0043 OQ1).
- **Whether vision and strategy blur in practice** — if adopters can't tell them apart, the open field lets a user collapse to one rung; that is the escape hatch, and the signal to revisit the two-rung split (RFC-0043 risk).

## Confirmation

- The implementing spec (`docs/specs/product-rung/`) encodes the decision as acceptance criteria — the open `Level` + recognized set, the Scale→Level suggestion (with leaf-projection preserved), the two seeded field blocks, the `market-existence` de-risk kind, the sibling-spawn + retroactive-parent behaviors, the tracker-projection rows, and the by-reference `init-project` seam — so conformance is checkable against the spec at the implementing PR.
- **Enforcement is deliberately review-time, not a standing CI gate.** An open `Level` field cannot be machine-checked against a closed set, and the prose-only, no-new-mechanism shape is exactly the bar that keeps the pack a habit not infrastructure (Principle 3). Conformance is confirmed at the implementing PR (the spec's ACs) and thereafter by the reviewer passes' standing doctrine — matching ADR-0030/0031/0032's precedent of accepting a prose-enforced, reviewer-held residual.

## Alternatives considered

- **A. Do nothing — tell users to stamp `Level: capability` by hand.** Rejected against the **over-narrowing** and **root-cause** drivers: `capability` is *architectural span* with the wrong de-risk kind, the Scale→Level stamp still misroutes, and orphaned siblings persist. Every greenfield product concept keeps misrouting.
- **B. Overload `capability` to also mean product altitude.** Rejected: it conflates architectural-span and product-existence — two different de-risk kinds — and still leaves no vision-vs-strategy distinction.
- **C. New rung(s), same recursive `intent` (chosen).** The only option that closes the altitude gap *and* the Scale↔Level coupling while staying inside the one-recursive-`intent`, prompt-only model.
- **D. A new parallel artifact type (`vision.md` / `strategy.md`).** Rejected against **Principle 2 and ADR-0019's one-recursive-artifact model** — it breaks the "same artifact at every level" shape, needs new layout / discovery / decompose wiring, and trends toward the heavyweight-toolkit mass Principle 3 forecloses.
- **One merged product rung** (sub-axis under C). Rejected: loses the vision (existence bet) vs. strategy (the path) distinction that is well attested across the prior art (Cagan; the surveyed toolkits).
- **An N-deep fixed product ladder** (sub-axis under C). Rejected: it is precisely the fixed SAFe ladder **ADR-0019 already rejected** and RFC-0043 lists as a non-goal; this sub-axis defers to that rejection rather than re-deciding it.
- **Reuse the `desirability` token for the product-existence bet** (sub-axis under D4). Rejected: naming the feature-level and product-level bets identically is the conflation that produces validation theatre; the product-existence bet asks "is there a product here at all," not "do users want *this feature*."

## References

- RFC-0043 — A product rung two altitudes above capability, Level decoupled from Scale (the accepted decision this ADR records; decisions D1–D6, the no-engine-change spike, the OQ defaults, and the promoted survey).
- ADR-0019 — Product shaping is a recursive level-tagged `intent` tree (the ontology this refines; its part 1 `Level` enum is reopened/decoupled, parts 2–3 stand, status stays Accepted).
- RFC-0030 — the `product-engineering` pack's founding RFC, whose steel-thread named the "vision/intent root" this ships.
- core `init-project/SKILL.md` — the greenfield front door whose stage-2 discovery sources the seam extends, by reference.
- `docs/specs/product-rung/` — the implementing spec these decisions are confirmed against.
- `docs/rfc/0043-notes/survey-product-rung.md` — the promoted applied-mode survey (findings F1–F5, citations) grounding the field sets and the `market-existence` kind.
- CHARTER Principles 2 and 3 — the no-duplication and habit-not-infrastructure bars this decision clears.
