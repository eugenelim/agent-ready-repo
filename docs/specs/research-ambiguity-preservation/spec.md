# Spec: research-ambiguity-preservation

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none (lean light-mode spec; task list below)
- **Constrained by:** none
- **Brief:** none
- **Contract:** none
- **Shape:** docs/prose (skill content)

> Mode: light (no risk trigger fired) — prose-only, additive edits to four
> existing research-pack skills; no new module, layer, dependency, or breaking
> interface change. The four output schemas gain *additive* sections; no
> existing schema field or downstream contract changes.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The research pack's standing bias is to **collapse every contested or
under-determined question to one rated answer**: `/research` tags each finding
with a single confidence level, `/devils-advocate`'s only verdict is a
confidence *downgrade*, `/identify-perspectives` enumerates camps then hands
them to `/compare-hypotheses` to pick a winner, and `/decision-archaeology`
records a rejection as a settled verdict. None of these has a first-class way
to **preserve and characterize irreducible ambiguity** — the cases where the
honest output is "both positions hold, under different conditions," "this is a
gap we cannot fill, not a weak finding," or "this rejection was conditional and
the condition has changed."

This spec adds that missing axis to four skills, each addition distinct from
what the pack already encodes (triangulation, GRADE confidence, ACH, NPOV
camps, chronology + rationale chains):

1. **identify-perspectives — tension map.** For each *preserved* disagreement
   (one that does not resolve to a single right camp), record the conditions
   under which each position holds and what a forced resolution would destroy.
   Distinct from the camp enumeration (per-camp claims/voices): the tension map
   is a *relational* layer that marks which disagreements are irreducible and
   why, so a reader — or a future `/compare-hypotheses` pass — can refuse to
   flatten them. (Wiring `/compare-hypotheses` to honor the marking is a
   deliberate follow-on, out of this PR's four-skill scope; today the marking
   is the record, not yet an enforced gate.)

2. **devils-advocate — do-not-resolve verdict.** A verdict, distinct from the
   existing confidence-downgrade, for productive/irreducible tensions: both
   sides are well-evidenced and the disagreement is in the world, not in our
   knowledge, so lowering confidence would falsely imply more evidence resolves
   it. The skill routes substantive evidence-against to *either* a downgrade
   *or* do-not-resolve.

3. **research — known-unknowns / unknowables gap section.** A first-class
   artifact section cataloguing questions a complete answer requires but the
   evidence cannot supply, split into *known-unknowns* (answerable in
   principle, evidence not yet available) and *unknowables* (not answerable
   from available evidence even in principle). Distinct from rating a weak
   *finding* `[uncertain]`: a known-unknown is a *non-finding* — rating it
   would dress "we don't know" up as a weak claim.

4. **decision-archaeology — revival check.** For each rejected alternative,
   evaluate whether its *original rejection rationale still holds today*; when
   the constraint that killed it has changed, flag it as a revival candidate.
   Distinct from the alternatives-considered record (the historical what/why):
   the revival check is a forward-looking audit of that record against present
   constraints.

## Acceptance Criteria

- [x] **AC1** `identify-perspectives/SKILL.md` adds a tension-map procedure
  step and a `## Tension map` section in the `perspectives.md` output schema,
  recording per preserved disagreement: the conditions under which each
  position holds, and what forced resolution would destroy. Prose states it is
  distinct from (not a relabel of) the camp enumeration.
- [x] **AC2** `devils-advocate/SKILL.md` adds a do-not-resolve verdict as a
  third routing outcome (alongside the existing rating-downgrade), with prose
  that distinguishes irreducible/productive tension from evidential weakness,
  and a corresponding entry in the `counterpoints.md` schema.
- [x] **AC3** `research/SKILL.md` adds a known-unknowns / unknowables gap
  section as a pipeline step and a `## Known unknowns` artifact section, with
  prose that distinguishes a gap (non-finding) from an `[uncertain]`-rated
  finding, and the known-unknown vs. unknowable split.
- [x] **AC4** `decision-archaeology/SKILL.md` adds a revival-check procedure
  step and a `## Revival candidates` schema section flagging rejected
  alternatives whose original rejection rationale no longer holds, distinct
  from the alternatives-considered record.
- [x] **AC5** The optional build-outline "era axis" is evaluated and
  **declined** (recorded in the PR's declined-pattern register): era-dependence
  is already covered by research's recency rule + `stale prior art` factor and
  by AC1's tension-map conditions field; it fails the non-duplication bar.
- [x] **AC6** Each addition is universal (no domain coupling), additive (no
  existing schema field or downstream contract removed/changed), and framed as
  a standing habit (a procedure step, not an aside).
- [x] **AC8** The pack's in-repo guides are kept in sync with the changed
  frontmatter and `counterpoints.md` verdict shape: `docs/guides/research/`
  reference (the three changed verbatim frontmatter descriptions), the
  tutorial (`counterpoints.md` walkthrough + example), and the how-to
  (pipeline artifact list) no longer describe `/devils-advocate` as
  downgrade-only or omit the new sections. (Doc-drift invariant; surfaced by
  adversarial review.)
- [x] **AC7** `packs/research/pack.toml` + `plugin.json` version bumped;
  `make build` run so `marketplace.json` reflects the bump; changelog
  `[Unreleased]` entry added; `git status` clean; `tools/lint-agent-artifacts.py`
  green; adversarial-reviewer clean.

## Tasks

1. identify-perspectives: tension-map step + schema section (AC1).
2. devils-advocate: do-not-resolve verdict + schema entry (AC2).
3. research: known-unknowns/unknowables gap step + artifact section (AC3).
4. decision-archaeology: revival check step + schema section (AC4).
5. Version bump (pack.toml + plugin.json), `make build`, changelog entry (AC7).
