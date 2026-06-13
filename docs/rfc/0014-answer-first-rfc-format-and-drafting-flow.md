# RFC-0014: Answer-first RFC format + research-and-de-risk drafting flow for `new-rfc`

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn -->
- **Author:** eugenelim
- **Approver:** @eugenelim
- **Date opened:** 2026-05-28
- **Date closed:** 2026-05-28
- **Related:** `new-rfc` skill (`packs/governance-extras/.apm/skills/new-rfc/`), `docs/CONVENTIONS.md` §3, `new-spec` (assumption checkpoint it borrows from), `adversarial-reviewer` agent.

## The ask

- **Recommendation (BLUF):** Reorganise the RFC template to lead with **"The ask"** (answer-first), and upgrade the `new-rfc` drafting flow so the agent **research-resolves, de-risks, and self-reviews** a draft *before* a human sees it — **reusing existing repo machinery** (`adversarial-reviewer`, `work-loop`'s trio, the existing research gate) rather than adding new subsystems. The body goes from today's 8 H2 sections to 9 (8 required + 1 optional Experiment/validation) — reorganised, with a single optional addition; the net-new *required* surface is one header field (`Approver`) and a `Non-goals` subsection.
- **Why now (SCQA):**
  - *Situation* — we have 13 RFCs and a `new-rfc` skill that already gates a research phase before drafting.
  - *Complication* — four recurring failures: (1) the decision a reviewer must make is buried inside "Proposal", tangled with design detail; (2) open questions pile up unowned (RFC `0005` carries **11**, `0010` **8**, `0008`/`0003` **5**); (3) drafts miss obvious things, so the reviewer does the catching; (4) prior-art research is done as one shallow up-front sweep, so a multi-decision RFC enumerates its option/scenario space incompletely and unbacked — "only 3 categories", invented rather than researched, with each subpoint not independently grounded.
  - *Question* — how should the template and flow change so a reviewer can **steer and decide fast**, and the agent stops handing over un-researched uncertainty?
- **Decisions requested:**
  1. **Adopt the answer-first template** (top-of-doc "The ask" = BLUF + SCQA + numbered decisions; new `Approver` field; explicit **Non-goals**; sections reorganised — see *Proposal*)? — *Recommended: yes.* *Decide-by: this review.*
  2. **Upgrade the drafting flow** — decompose into subpoints and research each, enumerating each option/scenario space MECE along a stated axis (≥2 incl. do-nothing; exhaustiveness argued, not round-numbered) and grounded in prior art, Self-Ask on research-resolvable questions, spike the riskiest assumption, cap + own open questions (~≤3), and a pre-handoff gate: a **citation-integrity protocol** + a **verify-before-you-assert** check + a self-scored YES/NO completeness checklist + a **mandatory** `adversarial-reviewer` dispatch in fresh context? — *Recommended: yes; `adversarial-reviewer` is mandatory (resolved this review).* *Decide-by: this review.*
  3. **Add an *optional* "Experiment / validation" framing section + optional `Experimental` status**, routing experiment *results* to a linked spike note (not the RFC body) — rather than a separate experiment doc type or a full "mode select"? — *Recommended: yes (optional section, not a mode).* *Decide-by: this review.*

  (This RFC changes a convention, so per `CONVENTIONS.md` §3 it requires explicit Approver sign-off — there is no silent-default adoption.)

## Problem & goals

**Diagnosis.** The current template orders sections `Summary → Motivation → Proposal → Alternatives → Drawbacks → Prior art → Unresolved questions`. The *decision being asked of the reviewer* is never isolated; it lives inside "Proposal." The skill's research phase produces recommendations but routes rejected/deferred ones straight into "Unresolved questions" carrying only a "lean" — codifying the very pattern that exhausts reviewers. There is no mechanical pre-handoff pass to catch obvious misses, and a same-model self-check does not substitute for one (see *Evidence*).

**Goals.**
- A reviewer can find *what they're being asked to approve*, in plain language, in the first screen.
- The agent resolves what it can research itself, de-risks its own riskiest assumption, and hands over a short, owned set of genuinely open decisions — not homework.
- A different-lens pass catches obvious omissions before a human reads the draft.
- The template gets *lighter for small, reversible RFCs*, not heavier.

**Non-goals** (could-have-been-goals we deliberately drop):
- *Not* retrofitting the 13 existing RFCs — they are Frozen history per `CONVENTIONS.md` §3.
- *Not* building a new reviewer subsystem — we reuse `adversarial-reviewer`.
- *Not* a separate "experiment doc type" or a research-skill-style multi-mode selector — rejected as over-engineering (see Option C).
- *Not* changing when an RFC is opened vs. an ADR/spec (`CONVENTIONS.md` §3 is unchanged).

## Proposal

### Template (`assets/rfc.md`) — answer-first spine, build-up body

Reorganised from today's 8 sections into 9 (8 required + 1 optional Experiment/validation); the new structure is:

```
# RFC-NNNN: <title>
- Status / Author / Approver / Date opened / Date closed / Related
## The ask              — Recommendation (BLUF) · Why now (SCQA) · Decisions requested (numbered, each with recommended option + decide-by/default)
## Problem & goals      — diagnosis · goals · Non-goals
## Proposal             — the design; cascading detail per requested decision
## Options considered   — enumeration collectively exhaustive (MECE) along a stated axis, each option grounded in prior art (not invented); ≥2 genuinely distinct incl. do-nothing (+ cost of delay); trade-offs stated up front; starred-recommended table encouraged
## Risks & what would make this wrong — pre-mortem (assume it shipped and failed) · falsifiable key assumptions · drawbacks
## Evidence & prior art — spike/de-risk result (or why none needed) · repo precedent · external prior art
## [Experiment / validation]  — OPTIONAL: hypothesis · what we measure · success/failure criteria. Results link out to a spike note, not here.
## Open questions       — ~≤3, each with recommended default · owner · decide-by. Research-resolvable ones must already be answered in the body.
## Follow-on artifacts
```

Right-sizing: for a small, reversible change most sections collapse to one-liners — authors right-size to the stakes (we considered a formal `Decision type`/door field to license this and dropped it as ceremony; plain guidance carries the same weight without new required surface).

### Drafting flow (`SKILL.md`)

Enhances the existing gated procedure; new steps in **bold**:

1. Find ordinal, copy template *(unchanged)*.
2. **Research + de-risk checkpoint** (replaces today's single up-front sweep — a complex RFC is a tree, not one blob):
   - **Decompose first.** Break the proposal into its decisions/subpoints (the numbered *Decisions requested*). The research unit is the subpoint, not the RFC.
   - **Research each subpoint independently.** Repo + external sweep *per subpoint* — one shallow pass over the whole RFC is the failure this replaces.
   - **Enumerate each option/scenario space to be collectively exhaustive (MECE)** along a stated axis, and **ground every option in prior art** (check how others have taxonomised it) rather than inventing categories. A small round count (e.g. exactly 3) with no exhaustiveness argument or sources is a smell to challenge, not a finish line. Include do-nothing.
   - **Self-Ask** to resolve research-answerable sub-questions so they never reach the human; **spike the riskiest assumption** or state why none is needed.
   - **Cite as you go** — when a sweep (or a research subagent) surfaces a source, fetch it and confirm it resolves *and* contains the borrowed claim before that claim enters the draft.
   - **Recommend** per decision (default + reasoning + owner + decide-by), capping open questions at ~3. Emit per-subpoint findings in chat; wait for steer *(gate — unchanged mechanism)*.
3. Draft the body answer-first.
4. **Pre-handoff gate**, before status → Open — *each item below is executed and its result recorded, never self-certified*:
   - **Citation-integrity protocol.** Every reference is fetched; it must both (a) resolve and (b) actually contain the specific claim or statistic it is cited for. A link that loads is **not** enough — the borrowed claim has to be in the source. Citations surfaced by a research subagent get the same treatment; never pass one through unverified. If a claim can't be confirmed, downgrade or drop it — don't ship it on trust. The rule is symmetric: *challenge* a citation the same way — by fetching it — never by judging whether an identifier "looks real".
   - **Verify-before-you-assert.** Every checkable claim the RFC makes about *itself* — section/field counts, "lighter/not heavier", "readable in the first screen", "the gate passed" — is checked against the artifact, not asserted.
   - **Per-subpoint backing.** Is *each* decision/subpoint independently backed by repo + external research — not just the headline? Is every option/scenario enumeration **collectively exhaustive (MECE)** along a stated axis and **grounded in prior art**, not invented? (A small round count with no exhaustiveness argument is a smell.)
   - **Completeness checklist (YES/NO).** Approver named? every decision carries a recommendation? do-nothing present? ≤3 owned open questions? no item is simultaneously a decided default *and* an open question? all internal cross-references resolve?
   - **Different-lens review.** Dispatch **`adversarial-reviewer`** (fresh context) — **mandatory**, re-run until it reports clean; `security-reviewer` if the RFC touches a security boundary.
5. Status → Open; update `docs/rfc/README.md` *(unchanged)*.

Anti-patterns the skill refuses (kept lean): writing the body before the checkpoint clears; bare unresolved questions with no recommended default; empty prior art when web search was available; **passing any citation — especially one surfaced by a subagent — into the draft without fetching the source and confirming the borrowed claim is in it** (link-resolves is not enough; the single most-documented LLM-drafting failure — see *Evidence*); **asserting any self-claim or a "gate passed" status without having run the check**; **a single shallow up-front sweep standing in for per-subpoint research on a multi-decision RFC, or enumerating an option/scenario space by inventing a small round number of categories (e.g. exactly 3) with no exhaustiveness argument or prior-art grounding**.

### Migration

No data migration. Edit point is the **pack source** `packs/governance-extras/.apm/skills/new-rfc/{SKILL.md,assets/rfc.md}` then `make build-self` (the `.claude/skills/new-rfc/` copy is generated). Update `docs/guides/governance-extras/how-to/new-rfc.md` to match. This RFC is itself written in the proposed template as the dogfood.

## Options considered

*Axis: how much net-new subsystem surface the change introduces. These three options exhaust that axis — none (A) / reuse what already exists (B) / a new doc-type + mode-selector + new mechanisms (C) — so it is genuinely MECE, not a round number.*

- **Option A — do nothing.** Keep the current template and flow. *Cost of delay:* the four failures above recur on every RFC; reviewer time keeps being spent catching omissions and chasing unowned questions. Rejected.
- **Option B — answer-first template + upgraded flow, reusing existing machinery (recommended).** Targets all four failures directly (the fourth — shallow research — via the decompose-per-subpoint model); net-new surface is small because `adversarial-reviewer` and the `work-loop` trio already exist. Trade-off: slightly more structure up front; mitigated by right-sizing small RFCs to one-liners.
- **Option C — heavyweight variant.** A separate "experiment doc type" + research-skill-style mode selector + generator expert personas + ACH matrices / best-of-N by default. Rejected: the persona and same-session-self-critique mechanisms are *contradicted* by the evidence (see below), and a separate experiment doc type is heavier than the conventional optional-section + linked-spike-note pattern. This is the cargo-cult path.
- **Experiment sub-decision (decision 3) options:** (a) optional framing section + linked results + optional status *(recommended)*; (b) separate experiment/spike doc type; (c) full mode-select like the `research` skill. (b) and (c) are rejected as over-engineering for a lightweight repo — convention routes *results* out of the proposal regardless (see *Evidence*).

## Risks & what would make this wrong

**Pre-mortem — assume this shipped and the result was bad. Why?**
- The mandatory `adversarial-reviewer` dispatch made drafting slow/heavy → *mitigation:* it runs once, on a finished draft, and `work-loop` already normalises this gate cost; reserve `security-reviewer` for boundary-touching RFCs only.
- The citation-integrity protocol felt like drag → *mitigation:* it only covers claims that actually enter the draft, and it's the same fetch the research sweep already performs — the protocol just forbids skipping it. It is not optional: it's the fix for the single most-documented LLM-drafting failure.
- Per-subpoint research multiplied drafting cost without improving completeness → *mitigation:* it scales with the number of decisions, so a simple/single-decision RFC still does one sweep; the decomposition only bites when there genuinely are multiple subpoints to back.
- The template *felt* heavier despite the near-same section count → *mitigation:* "Experiment" is optional and small RFCs right-size to one-liners; watch the next 2–3 real RFCs and cut what reads as ceremony (the `Decision type` field was already cut on that test).

**Key assumptions (falsifiable):**
- *Reviewers find the decision faster with "The ask" on top.* Falsifiable by the next few RFCs — if reviewers still hunt for the decision, the spine failed.
- *`adversarial-reviewer` (same underlying model, fresh context) catches enough.* The evidence supports fresh-context review but notes a different *model* would be strictly better; if it misses obvious things anyway, we revisit.
- *The capped/owned open-questions rule reduces the pile-up without dropping real ambiguity.* Falsifiable: if RFCs start hiding genuine uncertainty to hit the cap, loosen it.
- *Decomposing and researching per-subpoint produces more-complete, better-grounded option spaces than one up-front sweep.* Falsifiable: if per-subpoint research just multiplies cost without improving completeness, collapse it back toward a single sweep for simple RFCs.

**Drawbacks.** More up-front structure; one more gate in the flow; the citation-integrity protocol adds a verification step to every cited claim.

## Evidence & prior art

**Spike / dogfood result.** This RFC is written in the proposed template *and* run through the proposed pre-handoff gate, so the de-risking experiment tests both halves.
- *Answer-first:* the three requested decisions are readable in the first screen, which the old `Summary`-first shape did not achieve. (A reviewer's read remains the real test.)
- *Pre-handoff gate, actually exercised:* dispatching `adversarial-reviewer` flagged the load-bearing Cross-Context Review citation as a claim to verify. Fetching the source confirmed [arXiv 2603.12123](https://arxiv.org/abs/2603.12123) (submitted 2026-03-12) is real and that its F1 figures (28.6% vs 24.6%, p=0.008) match what the RFC cites — so the citation stands, *because* it was fetched, not assumed. The same passes surfaced a governance contradiction (silent-default adoption vs. `CONVENTIONS.md` §3) and a decision/open-question overlap, both fixed.
- *Why the protocol says "fetch", not "judge plausibility".* A later review pass re-flagged the same citation as fabricated — by reasoning from the arXiv ID convention (and miscounting the month) **without fetching it**. That was a false positive, and it is itself the assert-without-verifying failure decision 2 targets: a real source was nearly rejected on a plausibility hunch. The protocol therefore requires *fetching and confirming the claim is in the source* — for both writing a citation and challenging one — never reasoning about whether an identifier "looks real".
- *The gate improved the skill, not just this draft.* The recurring **shape** of the findings across review rounds — an unverified borrowed citation, a self-claimed section count wrong twice, a "gate passed" status asserted before the gate ran — was itself the signal: all three are the same root failure, *asserting a checkable claim without checking it*. That pattern is why decision 2 now mandates a **citation-integrity protocol** and a **verify-before-you-assert** step, rather than the original one-line "don't invent references." Reading the adversarial pattern for a missing *skill behavior* (not just patching this doc) is the intended use of the gate.

**Format survey (where the well-regarded formats place the decision).** Primary templates confirmed:

| Element | Rust RFC | Google | Amazon PR-FAQ | Squarespace/Uber | ADR/MADR | This proposal |
|---|---|---|---|---|---|---|
| Decision up top | Summary | thin TL;DR | press-release-first | — | Decision section | **"The ask" + named decisions** |
| Named approver | ✗ (FCP) | DRI | ✗ | **Approvers** | Status | **Approver field** |
| Non-goals | ✗ | ✅ | implicit | ✅ | ✗ | **✅** |
| Alternatives + do-nothing | ✅ | ✅ | implicit | ✅ | MADR options | **✅ + cost of delay** |
| Capped/owned open Qs | scoped by *timing* | ✗ | ✗ | "Yes, if" conditions | ✗ | **cap + owner + default** |

Sources: [Rust RFC template](https://raw.githubusercontent.com/rust-lang/rfcs/master/0000-template.md), [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/), [Amazon Working Backwards PR-FAQ](https://workingbackwards.com/resources/working-backwards-pr-faq/), [Squarespace "Yes, if"](https://engineering.squarespace.com/blog/2019/the-power-of-yes-if), [ADR (Nygard)](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions) / [MADR](https://adr.github.io/adr-templates/). The decision-doc + BLUF tradition ("90% of briefing memos should have clear recommendations") supports the named-recommendation pattern: [Animalz](https://www.animalz.co/blog/bottom-line-up-front). Minto/SCQA underpins answer-first: [CFI](https://corporatefinanceinstitute.com/resources/career/scqa/). Google's caution — keep the TL;DR thin and build the body up so answer-first doesn't hide uncertainty — is why we retain the build-up body and the "what would make this wrong" section.

**What produces a non-stupid proposal (the flow upgrade).**
- *Personas don't help correctness on the generator, and can hurt:* [Zheng et al. 2024](https://arxiv.org/pdf/2311.10054), [Wharton/Mollick *Playing Pretend*](https://gail.wharton.upenn.edu/research-and-insights/playing-pretend-expert-personas/). → we do **not** add a generator persona.
- *Same-session "critique yourself" degrades reasoning:* [Huang et al., ICLR 2024](https://arxiv.org/abs/2310.01798); fresh-context / different-lens review beats it (error-detection F1 28.6% vs 24.6%, gap grows with severity): [Cross-Context Review](https://arxiv.org/html/2603.12123). → we dispatch `adversarial-reviewer` in a fresh context.
- *Enumerate exhaustively, research per-subpoint, don't invent:* about half of organizational decisions fail, and failure is ~4× likelier when the first idea is embraced over investigating alternatives ([Nutt 1999](https://cebma.org/assets/Uploads/Nutt-1999-gecomprimeerd.pdf); [summary](https://news.osu.edu/half-of-business-decisions-fail-because-of-managements-blunders-new-study-finds/)); the pyramid principle requires every level to carry its own support rather than one blob ([Minto/SCQA](https://strategyu.co/pyramid-principle-partone/)); collectively-exhaustive (MECE) enumeration is its companion principle; decompose into sub-questions and answer each rather than one shallow pass ([Self-Ask](https://learnprompting.org/docs/advanced/few_shot/self_ask)). A complex RFC's subpoints each need researching and backing — an invented, round-number taxonomy handed off as complete is an under-modelled-space failure.
- *De-risk your own riskiest assumption with a spike* instead of handing over an untested guess: [SAFe Spikes](https://framework.scaledagile.com/spikes), Hunt & Thomas (tracer bullets).
- *Pre-mortem* surfaces failure modes the author missed: [Klein, HBR 2007](https://www.gary-klein.com/premortem).
- *Reversible vs irreversible sets the rigor budget:* [Amazon 2016 letter](https://www.aboutamazon.com/news/company-news/2016-letter-to-shareholders); Mike Cvet treats door-type as an RFC-review question: [Goals and Failure Modes for RFCs](https://medium.com/better-programming/goals-and-failure-modes-for-rfcs-and-technical-design-documents-c4ee1d1da6ff). We apply this as plain right-sizing *guidance* (small reversible RFCs stay light), not a structural field — the formal `Decision type` field was pressure-tested and cut as ceremony (see *Risks*).
- *Anti-fabrication is the opposite of overkill:* an AI ADR pipeline found the model "frequently invented non-existent APIs, webpages, or product features"; its #1 guardrail is "references MUST exist — check each link is valid": [Equal Experts](https://www.equalexperts.com/blog/our-thinking/accelerating-architectural-decision-records-adrs-with-generative-ai/). Matches this repo's "grep to verify a function exists before importing it."
- *Cap clarifications then commit:* GitHub Spec-Kit caps to ≤3 `[NEEDS CLARIFICATION]` markers then makes informed guesses: [Spec-Kit](https://github.com/github/spec-kit).

**Where experiments belong (decision 3).** Across Rust (eRFC / experimental feature gates), IETF (Experimental status), Python ([PEP 411](https://peps.python.org/pep-0411/) provisional), Google (link to prototypes), and XP spikes ([James Shore](https://www.jamesshore.com/v2/books/aoad1/spike_solutions), [SAFe](https://framework.scaledagile.com/spikes)), the consistent convention is: the proposal *frames* an experiment (hypothesis + success criteria, often via a lifecycle status), but **results are captured downstream** — a separate spike note, a follow-up RFC, or a superseding ADR — never amended back as a lab notebook. Google warns explicitly against proposal bloat. Hence decision 3: an *optional framing section + optional `Experimental` status*, results linked out — not a separate doc type or mode.

**Repo precedent.** `CONVENTIONS.md` §3 governs when to open an RFC and names `assets/rfc.md` as the template (so this change is correctly an RFC, not a quiet PR); §"living vs frozen" makes open RFCs editable and accepted ones immutable. `new-spec` already uses an assumption checkpoint this flow mirrors. The `work-loop` trio already covers "surface assumptions"; "limit the diff" already encodes scope/YAGNI — the flow reuses these rather than duplicating them.

## Open questions

*All resolved at acceptance (2026-05-28):*
- **A separate ADR?** No — this RFC plus the skill diff are the durable record; no ADR unless a future RFC contests the direction.
- The `adversarial-reviewer` dispatch is **mandatory** (folded into decision 2).
- The formal `Decision type` field was **cut as ceremony** (folded into the template + *Risks*).

## Follow-on artifacts

On acceptance:
- Edit `packs/governance-extras/.apm/skills/new-rfc/SKILL.md` (flow) and `assets/rfc.md` (template); `make build-self`; verify both lint surfaces (`lint-packs` source + `tools/lint-agent-artifacts.py` projection).
- Rewrite `docs/guides/governance-extras/how-to/new-rfc.md` against the new spine — its Step 2/Step 3 walk-through is written against the *old* section names (Motivation / Alternatives / Prior art / Unresolved questions) and needs substantive rewriting, not a section-name swap. It is a Living doc, so this drift must close in the same change.
- No ADR (decided at acceptance — see *Open questions*).
- Working research notes were kept in the workspace scratch dir (`.context/rfc-format-research/`: `research.md`, `research-better-proposals.md`, `pressure-test-and-proposal.md`) during drafting; that dir is gitignored and **not** durable. The durable evidence is the inline citations in *Evidence & prior art* above, which stand alone.
