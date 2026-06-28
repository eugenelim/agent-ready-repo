# RFC-0055: RFC amendment & errata convention

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental (optional: trial running, results pending — see the Experiment / validation section) -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-27
- **Date closed:** 2026-06-28
- **Decision weight:** standard <!-- light | standard | heavy — additive, reversible convention that codifies an existing de-facto practice; the follow-on spec changes a shipped governance-extras interface (the new-rfc skill + template), but this RFC touches no security/charter boundary and reverses no frozen decision. -->
- **Related:** RFC-0048 (worked precedent, PR #430 / commit 159853b1); RFC-0016 (doc-drift mechanical gate); ADR convention (`docs/CONVENTIONS.md` §2, supersede-in-place)

## Reviewer brief

- **Decision:** how RFCs should carry post-publication corrections, so the current authoritative state is separable from the audit trail of superseded ones.
- **Recommended outcome:** accept.
- **Change if accepted:**
  - Define a correction convention in the **`new-rfc` skill** (`SKILL.md` + `assets/rfc.md`) — the portable, adopter-shipped source of truth.
  - Name two sections keyed to lifecycle — **Errata** (Frozen RFCs) / **Amendments** (in-flight Open RFCs) — with an **optional, threshold-gated** two-layer structure (current-state table + audit trail).
  - Append-only logs; superseded entries are never deleted; the current-state table wins where they disagree.
- **Affected surface:** `governance-extras` pack — `new-rfc` skill `SKILL.md` and `assets/rfc.md`. Optionally the repo-only how-to guide. **No `CONVENTIONS.md` change.**
- **Stakes:** reversible. The convention is additive; existing RFCs are untouched (forward-only).
- **Review focus:** (1) the Errata/Amendments naming split keyed to lifecycle class; (2) the decision to make the **skill** the source of truth rather than `CONVENTIONS.md`, for pack-portability.
- **Not in scope:** migrating the existing correction sections (24 across 23 RFCs); a mechanical lint enforcing the structure; any `CONVENTIONS.md` edit.

## The ask

- **Recommendation (BLUF):** Adopt a single, lifecycle-keyed convention for how an RFC records corrections after it is published — **Errata** for Frozen RFCs, **Amendments** for in-flight ones — with an optional two-layer shape (an authoritative *current-state* table over a dated *audit trail*) that separates "what the rules are now" from "how we got here." House it in the `new-rfc` skill so it travels with the pack.

- **Why now (SCQA):**
  - *Situation:* RFCs are frozen once Accepted — bodies are immutable — yet they still need corrections after publication (a spec finds a gap, a later RFC reframes a decision).
  - *Complication:* there is **no written convention** for this. `CONVENTIONS.md` has zero amendment/errata mentions and the template has no scaffold, so a de-facto practice grew ad-hoc: 23 RFCs carry correction sections under two interchangeable headings — 16 `Errata` (every one on an Accepted RFC) and 8 `Amendments` (7 of them *also* on Accepted RFCs, doing errata's job), with RFC-0001 carrying both — and long logs garble — a reader must walk the whole chronological list and mentally diff superseded entries to learn the present rules. RFC-0048 hit exactly this and PR #430 fixed it ad-hoc.
  - *Question:* what is the standard shape for RFC corrections, and where does it live so it ships to adopters rather than coupling to a repo-local doc?

- **Decisions requested:**

  | ID | Question | Recommendation | Why | Decide by | Reviewer action |
  | --- | --- | --- | --- | --- | --- |
  | D1 | What are the section names, and what selects them? | Two names keyed to lifecycle class: **Errata** (Frozen) / **Amendments** (in-flight Open) | Mirrors the Document-lifecycle table; authors already apply `Errata` to frozen RFCs 16/16; fixes the reverse drift | this review | Confirm the split + naming |
  | D2 | How does a reader find the present contract when corrections accumulate? | **Optional, threshold-gated** two-layer: authoritative *current-state* table + dated *audit trail*; table wins | PR #430 precedent; IETF/Rust both separate "current truth" from the immutable log | this review | Confirm the two-layer shape + the threshold |
  | D3 | What happens to a correction that a later one overrides? | Append-only — newest entry + current-state table win; **no per-entry ritual**. In-place reword optional for in-flight Amendments. Whole-RFC replacement is out of scope — recorded as an Errata entry naming the superseding RFC (RFC-0012→0052 precedent) | Frozen bodies can't be edited anyway; this convention governs in-RFC corrections only | this review | Confirm append-only + the out-of-scope boundary |
  | D4 | Where does the convention's substance live? | The **`new-rfc` skill** (`SKILL.md` + `assets/rfc.md`) is the sole source of truth; **no `CONVENTIONS.md` change** | The skill ships with `governance-extras`; `CONVENTIONS.md` ships with `core` — housing it there would couple a governance-extras feature to a core doc and leave the skill non-self-contained | this review | Confirm skill-as-source-of-truth + zero CONVENTIONS touch |
  | D5 | Do we retrofit the existing sections (24 across 23 RFCs)? | **Forward-only** — convention applies to new corrections; no migration in scope | A big-bang diff against frozen history is churn for cosmetics; open-RFC retrofit is handled separately | this review | Confirm forward-only |

## Problem & goals

**Diagnosis.** Frozen RFCs need a way to record corrections *without* editing their immutable bodies, and there is no convention for it. The vacuum produced three concrete failures, all visible in the repo today:

1. **Two headings, one job.** `Errata` (16 RFCs, all Accepted) and `Amendments` (8 RFCs) do the same work — Approver-signed post-acceptance corrections — interchangeably. Seven of the eight `Amendments` RFCs (0001, 0002, 0003, 0004, 0006, 0023, 0041) are Accepted/Frozen and their entries read as errata ("post-acceptance, Approver-signed, no reversal, additive only"); RFC-0001 carries **both** sections at once. A reader can't tell from the heading whether the text below is immutable.
2. **Logs garble over time.** A chronological correction log accumulates entries that silently override earlier ones. After a few rounds the present rules are only recoverable by reading the whole log and diffing it by hand. RFC-0048 reached this state.
3. **No scaffold, no portability.** The template offers nothing, so each author reinvents the shape; and there is nowhere the convention lives that *travels with the RFC tooling* to adopters.

**Goals.**

- One unambiguous convention for recording RFC corrections, keyed to whether the RFC is Frozen or in-flight.
- A reader can find the *current* authoritative rules without walking the audit trail.
- The convention ships with the `new-rfc` skill, so adopters get it wherever `governance-extras` is installed.
- Scale the ceremony to the need — a single one-line erratum stays a one-liner.

**Non-goals.**

- **A uniform retrofit of existing RFCs.** Consistency across the back catalogue could reasonably have been a goal; it is deliberately dropped (D5) — the value doesn't justify a large diff against frozen history.
- **Mechanical enforcement.** A lint could check the structure; deliberately not pursued (the structure is optional and judgment-based — see Open questions).
- **A `CONVENTIONS.md` change.** Could reasonably have housed the rule; deliberately not, for pack-portability (D4).
- **Reworking the frozen-immutability rule itself.** This convention operates *within* it, not on it.

## Proposal

### D1 — Two sections, keyed to lifecycle class

A published RFC records corrections in one of two sections, chosen by the RFC's lifecycle class (the existing Document-lifecycle table, `CONVENTIONS.md` §Document lifecycle):

- **`## Errata`** — for a **Frozen** RFC (Accepted or Rejected). The body is immutable; corrections are appended here, Approver-signed. This is the common case (most corrections are found after acceptance).
- **`## Amendments`** — for an **in-flight** RFC (Open / Governance class) that needs to track reconciliations *while still being worked* without rewriting its body. The rare case (RFC-0048 is the live example).

The heading therefore signals whether the text beneath it is immutable. The two never coexist in one RFC going forward (existing dual-section RFCs — only RFC-0001 — are left as-is per D5): an Open RFC carrying `Amendments` renames the section to `Errata` if and when it is Accepted (a status-driven edit the Frozen rule already permits).

### D2 — Optional, threshold-gated two-layer structure

When corrections accumulate, the section splits into two layers (the PR #430 shape):

```
## Errata        (or ## Amendments)

### Current state
<authoritative table of the corrections in force — "read this, not the log">

### History / audit trail
<dated entries explaining how each correction was reached>
```

- The **current-state** layer is the authoritative present contract. Where it disagrees with a historical entry, the current-state layer wins.
- The structure is **optional and threshold-gated**: it appears only once a section holds **more than one entry, or any entry supersedes another**. A single one-line erratum stays a plain dated bullet — no table.

### D3 — Append-only; supersession handling

- Correction sections are **append-only**. A later entry supersedes an earlier one simply by being later; the **newest entry plus the current-state table** carry present truth. Earlier entries are never deleted — they are the audit trail.
- **No per-entry ritual is required.** On a Frozen RFC's `Errata`, prior entries cannot be reworded anyway (immutable). On an in-flight `Amendments`, an author *may* optionally reword a stale entry in place with a `*(Superseded: …)*` tag (as PR #430 did, since RFC-0048's body is still mutable) — permitted, not required.
- **Whole-RFC replacement is out of scope.** When an entire RFC (not one correction within it) is superseded by a later one, the live practice is an **Errata entry naming the superseding RFC** — e.g. RFC-0012 carries an erratum recording that its Alternative #7 was superseded by RFC-0052. (The Document-lifecycle table also contemplates an `Accepted → Superseded` status for frozen `rfc/*`, but the RFC status vocabulary doesn't enumerate it and no RFC uses it, so the errata-entry form is the operative one.) This convention governs corrections *within* an RFC; it neither defines nor changes the whole-RFC-supersession mechanism.

### D4 — The skill is the source of truth (no CONVENTIONS change)

The convention's substance lives in the **`new-rfc` skill**, which ships with `governance-extras`:

- **`SKILL.md`** — the procedure: when to use Errata vs Amendments, the two-layer structure and its threshold, append-only and supersession rules.
- **`assets/rfc.md`** — an optional, clearly-conditional scaffold (a commented block with a "delete unless this RFC is accumulating corrections" instruction), so it travels into every RFC an adopter drafts without being cargo-culted into empty sections.

`CONVENTIONS.md` is **not** edited. It is seeded by `core`; housing a `governance-extras` feature there would couple the two packs and leave the skill non-self-contained for adopters who install the RFC tooling but adapt their own conventions doc. The repo-only how-to guide (`docs/guides/governance-extras/how-to/new-rfc.md`) *may* gain a short note as a dogfood enhancement, but it does not ship and is not part of the portable convention.

### D5 — Forward-only

The convention applies to **new** corrections. The existing sections (24 across 23 RFCs) are left as-is; no migration is in scope. (Bringing the still-open RFCs into line is handled separately, outside this RFC.)

## Options considered

The load-bearing choice is **where the convention's source of truth lives** — the axis is *which shipped artifact carries it*, which exhausts the homes a pack convention can have: a core-seeded doc, the skill that implements it, or nowhere (status quo). The sub-shapes (naming, structure) are covered in Proposal/Decisions; this section enumerates the source-of-truth axis plus do-nothing.

| Option | Source of truth | Ships to adopters with the tooling? | Trade-off | Verdict |
| --- | --- | --- | --- | --- |
| **A. Skill-as-source** | `SKILL.md` + `assets/rfc.md` (`governance-extras`) | **Yes** — self-contained | CONVENTIONS' frozen-immutability rule doesn't spell out *how* to correct; the skill fills it | ★ recommended |
| B. CONVENTIONS paragraph | `CONVENTIONS.md` §RFC (`core` seed) | No — couples a governance-extras feature to a core doc; skill not self-contained | Familiar home (the brief's original ask), but fails portability | rejected |
| C. Both (paragraph + skill) | `CONVENTIONS.md` § + skill/template | Partially — the § rides `core`, not the tooling | The repo's *prevailing* house pattern, but couples the two packs here (see below) | rejected for this case |
| D. Do-nothing | None (ad-hoc) | n/a | Zero effort; reverse-drift on the Amendments side and log-garble both keep accreting | rejected |

- **Prior art — and why A departs from it.** The repo's *prevailing* pattern is in fact **C**: every same-pack doc type pairs a `CONVENTIONS.md` § with an `assets/` template + skill, and the § is the pinned source the template/reviewer/work-loop measure against (e.g. `new-spec`'s "Spec metadata contract", `CONVENTIONS.md` §Spec metadata contract). C works there because the convention and its tooling live in the **same layer** (`core`). This convention is the case C *can't* serve cleanly: its tooling (`new-rfc`) ships in `governance-extras` while `CONVENTIONS.md` ships in `core`, so a C-shaped § would put a governance-extras feature in a core doc and leave the skill non-self-contained for adopters who install the RFC tooling but adapt their own conventions. A is the deliberate departure the cross-pack boundary forces — not the house default.
- **Prior art for the structure (home-independent):** IETF keeps verified errata as a **separate layer** from the immutable RFC, classified and status-tracked; Rust keeps the RFC as a "design snapshot, not source of truth," amending only minor changes in place "with a note added." Both separate *current authoritative state* from *the log* — the D2 shape.
- **Do-nothing cost:** the frozen→Errata case is *already* self-correcting (authors file it 16/16 right with no rule), so do-nothing's cost is bounded, not runaway — but the two genuine gaps stay open: reverse-drift on the Amendments side (8 `Amendments`, 7 of them on frozen RFCs) and log-garble on long-lived RFCs (the next garbled log is the next long RFC). The recommendation rests on those two gaps, not on an overstated heading-drift trend.

## Risks & what would make this wrong

- **Pre-mortem — the naming split confuses authors.** If "is my RFC frozen or in-flight right now?" were ambiguous, authors would file corrections under the wrong heading. *Mitigation / why unlikely:* the lifecycle boundary is crisp (Accepted/Rejected = Frozen; Open = in-flight), and the census shows authors *already* partition the frozen case correctly without any written rule (Errata 16/16 on Accepted). The convention mostly writes down an existing instinct.
- **Pre-mortem — the optional scaffold gets cargo-culted.** An optional template block can get filled in on brand-new RFCs with nothing to amend. *Mitigation:* ship it as a commented, clearly-conditional block with a delete-unless-needed instruction, not a live empty section.
- **Pre-mortem — two sources drift.** Avoided by construction: D4 puts the source of truth in exactly one place (the skill), with no `CONVENTIONS.md` copy.
- **Key assumptions (falsifiable):**
  - *The Errata/Amendments lifecycle split is natural, not imposed.* Falsified if authors routinely misfile against lifecycle class — but the existing 16/16 Errata-on-frozen record is the counter-evidence.
  - *Most corrections are post-acceptance.* Falsified if in-flight `Amendments` turn out common — but only 1 of 24 sections is on an Open RFC today.
  - *The skill is a sufficient home.* Falsified if adopters reason about RFC corrections from `CONVENTIONS.md` without ever reading the skill — but they can't author an RFC without the skill in the first place.
- **Drawbacks:** transitional inconsistency — under forward-only (D5) the repo carries mixed styles until sections are opportunistically migrated. Accepted deliberately, as the cost of not diffing frozen history for cosmetics.

## Evidence & prior art

- **Spike / de-risk result (riskiest assumption: the two-name split is natural, not pedantry).** Census of every correction section against RFC status: **`Errata` appears on Accepted RFCs 16/16 with zero misfiles** — authors already partition the frozen case correctly *without* a written rule, so the boundary is intuitive. The only disorder is the reverse (`Amendments` over-applied to 7 Frozen RFCs, one of them — RFC-0001 — alongside `Errata`) — precisely the drift a written rule removes. Assumption survives, strengthened.
- **Repo precedent.**
  - Document-lifecycle table (`CONVENTIONS.md` §Document lifecycle) — Frozen (`accepted/rejected rfc/*`) vs Governance (`open rfc/*`); "Status fields can change… bodies cannot." The naming split keys off this.
  - ADR supersession (`CONVENTIONS.md` §2) — supersede-in-place, old text stays, status flips to `Superseded by`. Direct precedent for D3's whole-RFC carve-out.
  - De-facto Errata practice across the 16 Accepted RFCs that carry one (e.g. 0013, 0035, 0044), several sharing near-identical "Accepted… appended here, Approver-signed" boilerplate — the convention codifies what's already happening.
  - **PR #430 / RFC-0048** (commit 159853b1) — the worked two-layer precedent this RFC generalizes: a "Current reconciliation state" table over an "Amendment history / audit trail," current-state wins, superseded wording tagged in place.
- **External prior art** (web search available; both fetched and confirmed):
  - [IETF RFC errata system](https://errata.rfc-editor.org/) — corrections to published (immutable) RFCs live in a **separate** errata layer, classified (Editorial / Technical) and status-tracked (Verified / Held for Document Update / Rejected). Grounds the separate-audit-layer shape and the current-state-vs-log split.
  - [Rust RFC book](https://rust-lang.github.io/rfcs/introduction.html) — once accepted, RFCs are **not** kept current; only "very minor changes" are amended in place "with a note added," substantial changes become new RFCs; the RFC is "a design snapshot," the repo is the source of truth. Grounds amend-in-place-with-a-note (D1/D3) and current-state-wins (D2).

## Open questions

- **Should the structure eventually get a mechanical lint?** Recommended default: **no** — the structure is optional and judgment-based (the table is threshold-gated; "erratum vs amendment" is a lifecycle call, not a regex), so a lint risks false positives and over-enforcement. Revisit only if drift recurs after the convention beds in. · Owner: eugenelim · Decide-by: one release cycle after the implementing spec ships.

## Follow-on artifacts

<!-- Filled in on acceptance. -->

- **Spec:** `docs/specs/<feature>/` — implement the convention in the `new-rfc` skill (`SKILL.md` procedure + `assets/rfc.md` optional scaffold), plus the optional repo-only how-to note. User-visible skill-behavior change → carries a `docs/product/changelog.md` entry; `governance-extras` pack version bump.
- **No ADR** — no architectural decision beyond what this RFC records.
- **No `CONVENTIONS.md` change** (D4).
