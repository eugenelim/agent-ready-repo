# Spec: Retrofit the open RFC cluster to the current RFC format

- **Status:** Shipped
- **Mode:** full (governance-surface risk trigger — edits the `docs/rfc/` governance corpus)
- **Author:** eugenelim
- **Date:** 2026-06-28

## Objective

Bring the five **Open** RFCs authored 2026-06-25/26 — RFC-0048, RFC-0049,
RFC-0050, RFC-0051, RFC-0053 — up to the RFC template format that landed
**after** they were written (commits `ee54a5d1`, `bd84d0d4`, `f924dab5`, all
2026-06-27/28), so they are as scannable for a reviewer as the RFCs authored
under the new template (RFC-0054/0055/0056). This is a **meaning-preserving
readability retrofit**, explicitly sanctioned by RFC-0055 D5 ("open-RFC retrofit
is handled separately").

The three format additions per RFC:

1. **`Decision weight` header field** (`light | standard | heavy` + a one-line
   rationale comment), inserted before `- **Related:**`.
2. **`## Reviewer brief` section** — the fixed scannable grid (Decision /
   Recommended outcome / Change if accepted / Affected surface / Stakes / Review
   focus / Not in scope), inserted before `## The ask`.
3. **`Decisions requested` → table form** (`| ID | Question | Recommendation |
   Why | Decide by | Reviewer action |`), replacing the numbered list while the
   cascading per-decision detail stays in `## Proposal`.

Then verify, via the work-loop's reviewers, that each retrofit preserved meaning
and that the RFCs remain internally consistent with each other and with the
specs/plans already created (frame-domain, traceability-lint, release-loop). Fix
any genuine gap in those underlying specs/plans that the review surfaces.

## Acceptance criteria

- [x] **AC1** — Each of the 5 open RFCs carries a `- **Decision weight:**` line
  with a tier and a rationale comment, in the template-mandated header position.
- [x] **AC2** — Each of the 5 open RFCs has a `## Reviewer brief` section before
  `## The ask`, with the seven fixed lines, none of which restates the BLUF
  verbatim.
- [x] **AC3** — Each of the 5 open RFCs renders `Decisions requested` as the
  six-column table; every decision in the prior numbered list maps to exactly
  one row (no decision dropped, none invented), and the per-decision detail is
  retained in `## Proposal`.
- [x] **AC4** — No substantive content changed: the recommendation, decision
  set, non-goals, risks, and follow-ons of each RFC are unchanged in meaning
  (diff is additive front-matter + a list→table transform). Verified by
  `adversarial-reviewer` reporting no meaning-drift Blocker.
- [x] **AC5** — RFC-0048's existing `## Amendments` section is confirmed to
  already conform to the new two-layer Errata/Amendments convention (it does);
  no change forced there.
- [x] **AC6** — A `design-reviewer` (or `adversarial-reviewer`) pass over the
  retrofitted cluster surfaces no Blocker. Any gap it raises that traces to an
  underlying spec/plan (frame-domain / traceability-lint / release-loop) is
  either fixed in this PR or recorded with a one-line reason.
- [x] **AC7** — ADR-0038 (the one cluster-related ADR, per Approver direction)
  carries the new ADR-format additions — a `## Decision summary`, a structured
  `**Revisit if:**` line in Consequences (mirrored in the summary), and a
  `Mode / Signal / Owner` Confirmation — with no change to the decision, drivers,
  consequences, or alternatives in meaning.

## Boundaries

- **Related ADRs — scoped by Approver direction to this cluster's own open
  items.** The new ADR format (Decision summary / structured `Revisit if:` /
  `Mode·Signal·Owner` Confirmation) is forward-only and frozen ADRs are normally
  immutable, but the Approver (eugenelim) ruled this cluster's related ADRs to be
  **open items** and authorized a **readability-only** retrofit (no semantic
  change). **ADR-0038** (rename `design-craft → experience`) is the one ADR
  created as a follow-on *of this cluster* (Date 2026-06-25; Related →
  RFC-0048/RFC-0050) — it is retrofitted. The other ADRs the RFCs merely *cite*
  (ADR-0022, ADR-0023, ADR-0024, ADR-0031, …) are frozen decisions from unrelated
  prior tracks, not this cluster's open items, and are **left untouched**
  (genuinely forward-only).
- **No status changes.** RFC-0048 stays Open with its acceptance blockers; the
  others stay Open. The retrofit is presentation only.
- **No re-opening of decided substance.** The retrofit does not re-litigate any
  decision, non-goal, or risk; it re-presents them.

## Testing strategy

This is a docs change; the "gates" are mechanical + judgmental review, not a
test suite:

- **Mechanical:** `git diff` confirms each RFC's diff is additive (new header
  line + new section + list→table) with no deletions of substantive prose;
  `python .claude/skills/work-loop/scripts/lint-spec-status.py --root .` stays
  green for this spec.
- **Judgmental:** `adversarial-reviewer` against this spec + the diff (meaning
  preservation, AC4), then a `design-reviewer` pass over the retrofitted RFCs as
  artifacts (internal consistency, gaps pointing at the underlying specs).

## Assumptions

- The five Open RFCs are the complete "open cluster"; RFCs 0054/0055/0056 were
  authored under the new template and need no retrofit (verified: they already
  carry Decision weight + Reviewer brief + Decisions table).
- RFC-0055 D5's "open-RFC retrofit is handled separately" authorizes this work;
  the forward-only rule binds frozen artifacts, not in-flight Open ones.
