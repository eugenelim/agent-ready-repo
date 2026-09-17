# ADR-0116: `creative-direction` writes to `direction/`, retiring `aesthetic/`

- **Status:** Accepted
- **Date:** 2026-09-16
- **Decision-makers:** eugenelim
- **Related:** [`docs/specs/design-output-addressing/spec.md`](../specs/design-output-addressing/spec.md) — the spec this ADR satisfies; [`0116-notes/direction-folder-name-dataset.md`](0116-notes/direction-folder-name-dataset.md) — the reproducible dataset this ADR cites

## Decision summary

- **Decision:** `creative-direction` writes its artifact to
  `<output_dir>/direction/<slug>.md`, and `aesthetic/` is retired. `aesthetic/`
  was published in guide steps but was never written by the skill.
- **Because:** `direction/` is the artifact-kind name under this repository's
  own documented naming grammar; `aesthetic/` is a quality descriptor that
  does not fit that grammar; and the three alternative subfolder names
  (`direction/`, `creative-direction/`, `visual-direction/`) each returned
  zero on GitHub code search, so no external convention constrains the choice
  — the local grammar decides it.
- **Applies to:** the `creative-direction` skill's declared write target and
  every guide step and registry that names its output folder. Adjacent skills
  in the same addressing change (`information-architecture`, `design-principles`,
  `design-system`) are decided by their own acceptance criteria; this ADR covers
  only the `creative-direction` output folder and the retirement of `aesthetic/`.
- **Tradeoff accepted:** an adopter who created files under `aesthetic/` by
  following the guide will not have them discovered by the skill after the
  folder is retired. No migration is provided; the follow-on in `spec.md` records
  this as an acknowledged gap.
- **Revisit if:** GitHub code search returns results for `design/direction/` in
  volume sufficient to indicate a conflicting external convention, or a skill
  rename makes `direction/` ambiguous with another skill's output.

## Context

Nineteen guide steps in `guides/experience-design/how-to/` publish a
`**Where it lands:**` path. Eight of those steps name a path that no skill
writes. `creative-direction` is one of the three skills that do write, but
whose write step names no `output_dir`-rooted location. The guide step for
`creative-direction` published `<output_dir>/aesthetic/<slug>.md` — a path the
skill itself never stated.

The `docs/specs/design-output-addressing/spec.md` acceptance criterion requires
that the ADR recording `direction/` cite a dataset carrying the queries,
sampling frame, and inclusion rule needed to reproduce its sample. That dataset
is [`0116-notes/direction-folder-name-dataset.md`](0116-notes/direction-folder-name-dataset.md).

Three alternative subfolder names were evaluated: `aesthetic/` (retiring),
`creative-direction/` (the skill's own name), and `visual-direction/` (a
descriptor of the output's content). The decision is decided against all three
by evidence rather than preference.

**`aesthetic/` is a quality descriptor, not an artifact-kind name.** The
repository's naming grammar, stated explicitly in `docs/design/README.md`, is
"Artifact-kind first, then slug". `aesthetic/` describes how a surface should
feel; it does not name what the artifact is. Under the grammar, the artifact
kind for a creative direction document is `direction/`. This is not a proposed
name: `docs/design/direction/` already exists in this repository with two files
(Finding LV-1 in the dataset).

**`creative-direction/` and `visual-direction/` have no external precedent and
embed the wrong abstraction layer.** GitHub code search returned zero results
for `path:design/direction`, `path:design/creative-direction`, and
`path:design/visual-direction` across all indexed public repositories
(Finding 1 in the dataset; reproducible). The zero result means no external
convention favours any of these three names, so the local grammar is the
deciding criterion. Of the three, only `direction/` fits the grammar: the other
two embed either the skill's own name or the output's subjective quality rather
than its artifact kind.

**`aesthetic/` was never written by the skill.** The `creative-direction`
SKILL.md step 6 copies a template into the user's repository but names no
destination path. `aesthetic/` appeared only in the guide step
(`establish-design-intent.md`) and in DESIGN.md and JOURNEY.md registries.
No grep over the skill's own files finds the string `aesthetic/` (Finding LV-3
in the dataset). Retiring `aesthetic/` therefore removes a false promise in the
guides rather than relocating a live write.

## Decision drivers

1. **Fit the local naming grammar.** `docs/design/README.md` states
   "Artifact-kind first, then slug". The grammar decides the name when no
   external convention exists.
2. **No external convention constrains the choice.** All three candidate names
   returned zero on GitHub code search (dataset Finding 1). An unconstrained
   choice should go to the grammar, not preference.
3. **The live tree already uses the name.** `docs/design/direction/` exists and
   holds two repository artifacts. Recording a name the repository already
   chose in practice rather than inventing one is lower risk.
4. **Retire the false promise.** `aesthetic/` was guide-published but skill-absent.
   The retirement closes a stated discrepancy rather than creating a new one.

## Consequences

**Positive:**
- The guide step, the skill declaration, and the registry all name the same
  folder after the full addressing change lands.
- `direction/` is findable from `docs/design/README.md`'s grammar without
  reading any skill file.
- The repository's own live tree at `docs/design/direction/` is consistent with
  the declared output location.

**Negative:**
- Any adopter who created files under `aesthetic/` by following the guide has
  files no skill will look for after the retirement. No migration is provided.
  This is recorded as a known gap in the follow-ons section of `spec.md` rather
  than a blocking condition, because `aesthetic/` was never written by any skill
  and so the loss is of files created outside the skill's authorship.
- The `docs/design/direction/` directory currently holds two files with
  `type: design-system` (see `spec.md` follow-ons). The containment module's
  `type:` mismatch check will surface a collision on the first run against this
  repository's own tree.

**Revisit if:** GitHub code search returns results for `design/direction/` in
sufficient volume to indicate an established conflicting convention, or a
skill rename makes `direction/` ambiguous.

## Alternatives considered

- **Keep `aesthetic/`** — rejected because `aesthetic/` is a quality descriptor,
  not an artifact-kind name, and it was never written by the skill. Keeping it
  formalises a false promise rather than retiring one.
- **Use `creative-direction/`** — rejected because it embeds the skill name
  rather than the artifact kind, contrary to the local grammar, and returned zero
  on GitHub code search (no external convention to inherit).
- **Use `visual-direction/`** — rejected for the same reasons: a quality
  descriptor that embeds the output's character rather than its kind, and zero
  external precedent.
- **Invent a new name not surveyed** — no alternative was identified that is
  both consistent with the local grammar and better than `direction/`. The
  grammar produces one natural artifact-kind name for a document that records
  creative direction.

## Confirmation

- **Mode:** lint/CI
- **Signal:** the `design-output-addressing` spec's acceptance criterion asserts
  that the ADR cites a dataset carrying queries, sampling frame, and inclusion
  rule. The verification gate for that criterion runs against this file and
  [`0116-notes/direction-folder-name-dataset.md`](0116-notes/direction-folder-name-dataset.md).
  The declaration test in `packs/experience-design/tests/` asserts the
  `**Writes:**` line carries the declared `direction/<slug>.md` target.
- **Owner:** the spec author.

## References

- [`0116-notes/direction-folder-name-dataset.md`](0116-notes/direction-folder-name-dataset.md)
  — the reproducible dataset: queries, sampling frame, inclusion rule, and
  locally verifiable findings that back the evidence claims in this ADR.
- [`docs/specs/design-output-addressing/spec.md`](../specs/design-output-addressing/spec.md)
  — the spec criterion this ADR satisfies (Durable Outputs row: "Decision
  rationale") and the follow-ons that record acknowledged gaps.
- [`docs/design/README.md`](../design/README.md) — states the naming grammar
  "Artifact-kind first, then slug" this decision applies.
