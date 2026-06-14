# Spec: retcon + context-poisoning doc-writing disciplines

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** inline (light mode — no separate plan.md)

Mode: light (no risk trigger fired — additive drafting guidance to two skills'
prose; no structural, interface-contract, security, or dependency change).

## Objective

Two related doc-writing disciplines are taught by our spec/guide authoring
skills so that an agent reading a spec or guide can trust the document as a
description of what is true *now*:

- **(a) Retcon writing.** `new-spec` and `new-guide` instruct authors to write
  spec/guide bodies in the present tense, as if the feature already exists and
  always worked this way — no future-tense ("will be implemented"), no
  "previously X, now Y" history, no deprecation timelines, no version-stamped
  history in the body. Decision history still lives in ADRs and the changelog;
  this is about the body being a clean present-tense description. The plan
  (`plan.md`) is exempt — it is an explicitly living strategy doc with its own
  changelog.
- **(b) Context poisoning.** `new-spec` names the failure mode that the
  single-source-of-truth / drift-is-a-bug discipline prevents: an agent that
  loads a stale, duplicated, or self-contradicting doc makes a confident, wrong
  decision from it. The concept is defined in exactly one canonical place.

## Acceptance Criteria

- [x] `new-spec` SKILL.md teaches retcon writing as drafting guidance: present
      tense, as-built, with the four named bans (future tense, previously-X-now-Y,
      deprecation timelines, version-stamped history) and the rationale (mixed
      tenses make a reading agent guess wrong about what's current; history lives
      in ADRs/changelog).
- [x] `new-spec`'s bundled `assets/spec.md` template carries a concise
      present-tense reminder scoped to the spec body; `plan.md` is left unchanged
      (it keeps its changelog and is exempt).
- [x] `new-guide` SKILL.md teaches the same retcon discipline in guide-flavored
      terms, and the shared `references/clear-prose.md` checklist gains a
      matching "don't narrate product history" item.
- [x] `new-spec` names **context poisoning** as a short named concept in exactly
      one canonical place — its drift-is-a-bug / one-canonical-home rationale —
      and links the two halves of the defense (one-canonical-home + retcon)
      rather than restating either.
- [x] No new glossary file is created; the concept is not restated in three
      places.
- [x] `packs/core` bumped to 0.4.7 (pack.toml + plugin.json);
      `packs/user-guide-diataxis` bumped 0.1.3 → 0.1.4 (pack.toml + plugin.json);
      changelog `[Unreleased]` gains an entry.
- [x] `make build-self` + `make build` run clean; `git status` clean; gates +
      `tools/lint-agent-artifacts.py` pass; adversarial-reviewer returns clean.

## Tasks

1. Edit `new-spec` SKILL.md — add retcon failure-mode bullet (step 4) + expand
   step 8 with the context-poisoning named concept tying to retcon + the
   AGENTS.md source-of-truth map.
2. Edit `new-spec` `assets/spec.md` template — add present-tense body reminder.
3. Edit `new-guide` SKILL.md (step 4 voice anti-patterns) + `clear-prose.md`.
4. Bump versions (both packs) + changelog entry.
5. Build (`build-self` + `build`), verify gates + lint-agent-artifacts + clean
   tree, adversarial pass.

## Declined-pattern register

- Tempted to create a new `docs/guides/reference/glossary.md` for context
  poisoning; declining — no glossary exists, guides are by-pack, core ships
  self-contained, and a core→glossary link would dangle for core-only adopters.
  The canonical home is `new-spec`'s rationale inline.
- Tempted to add the retcon reminder to all four guide templates; declining —
  it is a cross-quadrant prose rule, so it lives once in `clear-prose.md`
  (the shared prose reference every quadrant reads) + the `new-guide` SKILL,
  not duplicated four times.
- Tempted to add retcon to `plan.md`; declining — the plan is a living doc with
  its own changelog, so present-tense-as-built does not apply to it.
