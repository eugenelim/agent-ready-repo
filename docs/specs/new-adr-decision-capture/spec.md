# Spec: new-adr decision-capture polish

Mode: light (no risk trigger fired)

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none (light mode — task list inline below)

> Track 1 of the `new-adr` critique. Skill-prose + behavioral-eval refinements
> that guide the author to isolate the decision before drafting and keep the
> record lean. The format-changing recommendations (a first-screen Decision
> summary block, a structured `Revisit if:` field, a Confirmation
> Mode/Signal/Owner sub-structure) are **out of scope** — they change the ADR
> template that ADR-0027 froze ("MADR-aligned but lean") and are deferred to a
> track-2 RFC.

## Objective

Close the "under-guided" gap in the `new-adr` skill: it asks the right
*validity* questions but doesn't help the author *shape* the decision before
writing, so heavy ADRs carry RFC-residue (long rationale, dense titles, prose
metadata, multiple sub-decisions). Add decision-capture guidance and harden the
behavioral evals — without touching the locked template format.

## Acceptance Criteria

- [x] **AC1 (R1 — decision-frame intake).** The skill gains a "frame the
  decision before drafting" step that **offers, doesn't force** — infers the
  frame when the decision is already crisp, walks a short decision frame when it
  arrives tangled — mirroring `new-rfc`'s established guided-intake shape rather
  than a mandatory questionnaire.
- [x] **AC2 (R3 — short titles).** The skill's title guidance states the title
  *identifies* the decision and does not encode the whole rationale (detail
  belongs in the Decision section), with a matching anti-pattern. Examples stay
  generic (no repo-internal ADR numbers an adopter wouldn't have).
- [x] **AC3 (R4 — one decision wide).** The skill pushes back when one ADR packs
  three or more load-bearing sub-decisions, pointing at an umbrella RFC +
  smaller ADRs, with a matching anti-pattern.
- [x] **AC4 (R5 — pointer-like metadata).** The skill states `Consulted` /
  `Related` are short pointer lists, not prose; explanatory detail goes to
  Context or References.
- [x] **AC5 (R8 — usability evals).** `evals/evals.json` is extended with
  behavioral assertions for the above (short decision-identifying H1;
  pointer-like metadata; one durable decision). No assertion references a
  track-2 field (no Decision summary, no Revisit-if). `eval_queries.json`
  (trigger detection) is unchanged.
- [x] **AC6 (no format change).** `assets/adr.md` gains no new section or field;
  only guidance *comments* may be refined. The frozen ADR-0027 format holds.
- [x] **AC7 (guide sync).** The repo-owned how-to guide
  (`docs/guides/governance-extras/how-to/new-adr.md`) is synced for the
  behaviors that materially change (title brevity, decision-frame, one-decision
  pitfall, pointer-metadata pitfall) so it doesn't contradict the skill.
- [x] **AC8 (changelog).** A `[Unreleased]` entry under governance-extras 0.4.0
  records the user-visible skill change.
- [x] **AC9 (projection clean).** `make build-self` projects the source change
  to `.claude/` + `.agents/` (+ marketplace aggregation) and leaves a clean
  tree; `lint-packs` and `tools/lint-agent-artifacts.py` pass.

## Boundaries

In: `packs/governance-extras/.apm/skills/new-adr/SKILL.md`, its
`evals/evals.json`, guidance comments in `assets/adr.md`, the how-to guide, the
changelog, and the resulting projections. Out: the ADR template's
sections/fields (track-2 RFC), `eval_queries.json`, any other pack, any
governance rule (CONVENTIONS/CHARTER), version bump (rides unreleased 0.4.0).

## Testing Strategy

Goal-based + manual-QA (prose + JSON; no production code). Done when:
`python -c "import json,glob; [json.load(open(f)) for f in glob.glob('packs/governance-extras/.apm/skills/new-adr/evals/*.json')]"` parses;
`lint-packs` and `lint-agent-artifacts.py` pass; `make build-self` leaves a
clean `git status`; and a read-through confirms the skill reads coherently and
the decision-frame mirrors `new-rfc`'s offer-don't-force shape.

## Declined patterns

- Tempted to implement R1's rigid 7-question INTAKE + DECISION FRAME verbatim;
  declining — adapt to `new-rfc`'s "offer, don't force" shape, the established
  house pattern.
- Tempted to add a "Decision summary" first-screen section to hold the title
  detail R3 sheds; declining — that's a frozen-template change (ADR-0027),
  deferred to track 2.
- Tempted to add a separate usability-eval file/harness for R8; declining —
  `evals.json` is already behavioral, so the checks extend existing assertions.
