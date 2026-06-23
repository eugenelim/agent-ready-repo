# Plan: research-typed-artifacts

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

This is a **naming-convention change to existing skill bodies and docs** — no
code, no new files of substance, no dependency. The shape of the change: define
the canonical type vocabulary + topic-slug rule once in the `research` SKILL.md
(the lifecycle anchor), apply the slug-prefix rule to the other six
artifact-producing skills, then sweep every live consumer's `research.md`
reference to the typed scheme + alias note. The riskiest part is the **shipped
research-pack spec amendment** (frozen-doc tension): handled per the spec's AC7
resolution, mirroring the 2026-05-28 applied-mode amendment exactly. Verification
is overwhelmingly goal-based (grep against bodies and docs), with one manual-QA
end-to-end `/research` run to prove the artifact a user invokes actually lands
under the new name.

This spec lands **first**; `research-project-mode` depends on the bare-name
convention this establishes (a project folder namespaces the topic, so inner
files drop the `<topic-slug>-` prefix — only meaningful once the episodic prefix
rule exists).

## Constraints

- **RFC-0039 Decision 2** — fixes the type vocabulary and the
  topic-named-episodic / bare-named-in-folder split.
- **ADR-0029** — episodic output named by topic + type; `research.md` legacy
  alias.
- **RFC-0038** — forward-only migration: emit only the new name; retain the old
  as a documented alias for one release; no dual-write, no permanent alias.
- **CONVENTIONS § 4** — the spec-section intro (lines ~265-270: a shipped spec is
  reference material updated alongside behaviour changes) wins over the general
  document-lifecycle table's frozen-body rule (line ~103) for the AC7 resolution;
  plus the spec metadata contract (status, `- [ ]`/`- [x]` notation, deferral
  anchors).
- **Charter Principle 3** — prompt-only; the filename is produced by the agent
  following the skill body, never by code.

## Construction tests

Most tests live per-task below. Cross-cutting:

- **Integration:** none beyond per-task greps — the artifacts are independent
  skill bodies and docs; there is no integration seam.
- **Manual verification:** one standard-mode `/research` run (T6) exercised
  end-to-end, output filename recorded in the PR description (AC5).

## Design (LLD)

Shape: `data` — the change defines a file-naming scheme.

### Design decisions

- **Vocabulary lives once, in the `research` SKILL.md**; the other six skills
  reference the slug rule and name their own `<type>` stem. Rationale: single
  source of truth for the type table; avoids six drifting copies. Traces to: AC1,
  AC2 · contracts: none.
- **Alias is a documentation note, not a dual-write.** `research.md` is named as
  the prior stem for `survey`; the skill emits only `<topic-slug>-survey.md`.
  Rationale: RFC-0038 forward-only; a generated artifact has no persistent reader
  that needs the old file to exist. Traces to: AC3 · contracts: none.

### Data & schema

- **Episodic filename grammar:** `<topic-slug>-<type>.md` where `<topic-slug>` is
  short kebab-case derived from the question and `<type>` ∈ {`fact-check`,
  `survey`, `counterpoints`, `comparison-matrix`, `shortlist`, `blueprint`,
  `hypotheses`, plus the existing scoping/archaeology stems `perspectives`,
  `outline`, `sources`, `archaeology`}. Quick mode: no file. Traces to: AC1, AC2.

## Tasks

### T1: `research` SKILL.md carries the vocabulary, slug rule, and alias note

**Depends on:** none

**Tests:**
- `rg -F` for each of the seven type stems (`fact-check`, `survey`,
  `counterpoints`, `comparison-matrix`, `shortlist`, `blueprint`, `hypotheses`)
  against `packs/research/.apm/skills/research/SKILL.md` returns ≥1 hit each
  (AC1).
- `rg -F '<topic-slug>-' packs/research/.apm/skills/research/SKILL.md` ≥1 hit
  (AC2).
- `rg -i 'legacy alias|formerly|deprecated' …/research/SKILL.md` returns a hit on
  a line that also names `research.md` (AC3).
- Quick mode still documented as inline / artifact-free (AC6).

**Approach:**
- Add a "Typed, topic-named artifacts" section to the `research` SKILL.md body
  with the RFC-0039 Decision 2 table and the topic-slug derivation rule.
- Add the one-release `research.md` legacy-alias note.
- Update the skill `description:` frontmatter where it names `research.md` as the
  standard/applied output, to the typed name (quoted-YAML safe per the Kiro
  parser caveat).

**Done when:** all four greps above pass and the skill reads coherently in
present tense.

### T2: the six other artifact-producing skills apply the slug-prefix rule

**Depends on:** T1

**Tests:**
- `rg -F '<topic-slug>-'` against each of `devils-advocate`,
  `compare-hypotheses`, `identify-perspectives`, `build-outline`, `source-map`,
  `decision-archaeology` SKILL.md returns ≥1 hit (AC2).
- `devils-advocate` SKILL.md names `<topic-slug>-counterpoints.md`;
  `compare-hypotheses` names `<topic-slug>-hypotheses.md` (the deep-mode and
  adjudication rows of the vocabulary).

**Approach:**
- In each skill body, change the persisted-output name from the bare stem to
  `<topic-slug>-<stem>.md`, referencing the slug rule defined in `research`
  SKILL.md. Two groups (per spec AC2): **RFC-fixed** stems `counterpoints.md`
  (`devils-advocate`) and `hypotheses.md` (`compare-hypotheses`); **spec-generalized**
  stems `perspectives.md`, `outline.md`, `sources.md`, `archaeology.md`
  (`identify-perspectives` / `build-outline` / `source-map` /
  `decision-archaeology`) — prefix-only, recorded as the spec-level generalization
  of the RFC's "across episodic modes" intent.
- Preserve each skill's pipeline-vs-standalone wording (e.g. `devils-advocate`
  targeting `<topic-slug>-survey.md`).

**Done when:** the six greps pass and each skill's input/output references are
internally consistent.

### T3: live docs + confidence-schema reference migrated

**Depends on:** T1

**Tests:**
- In `confidence-schema.md` and the five docs
  (`research-first-session`, `research-pack` reference, `research-pipelines`,
  `run-a-full-inception`, `research-pack/plan.md`), every residual `research.md`
  occurrence sits on a line carrying an alias marker (`legacy`/`alias`/`formerly`/
  `deprecated`) — reviewer-confirmed (AC4).
- The reference guide's artifact list shows the typed names.

**Approach:**
- Sweep each doc; replace current-output `research.md` references with the typed
  name; where a sentence is explicitly about the rename, keep `research.md` as a
  named alias.
- Re-run the tutorial's artifact-presence narrative against the typed names.

**Done when:** the grep-plus-reviewer check passes for all six files.

### T4: shipped research-pack spec + plan amended (frozen-doc resolution)

**Depends on:** T1

**Tests:**
- `rg -F 'research.md' docs/specs/research-pack/spec.md` — every remaining hit is
  an alias reference; the spec `## Changelog` has a `2026-` entry naming the
  typed rename (AC7).
- `docs/specs/research-pack/plan.md` references migrated likewise.

**Approach:**
- Update the `research.md`-pinning ACs (AC13, AC14, AC18, AC22, AC26, AC27 and
  the verification greps that name `research.md`) to the typed scheme + alias
  note.
- Add a dated `## Changelog` amendment entry to `research-pack/spec.md` recording
  the rename and citing RFC-0039 + this spec, in the shape of the 2026-05-28
  applied-mode amendment entry.

**Done when:** both greps pass and the amendment entry reads in the established
changelog voice.

### T5: pack version bump + changelog entry

**Depends on:** none

**Tests:**
- `packs/research/pack.toml` `version = "0.3.0"`; `plugin.json` version matches
  (goal-based grep).
- `docs/product/changelog.md` `[Unreleased]` carries an `### Changed` entry for
  the typed-artifact rename naming the `research.md` one-release alias.

**Approach:**
- Bump `packs/research/pack.toml` and the pack's `.claude-plugin/plugin.json`
  version 0.2.0 → 0.3.0.
- Add the changelog `[Unreleased]` entry (user-visible: outputs renamed; old name
  is a one-release alias).
- Update the PyPI/README long-description if it enumerates the artifact name.

**Done when:** versions match and the changelog entry is present.

### T6: observable end-to-end run

**Depends on:** T1, T2

**Tests:**
- Manual QA: a standard-mode `/research` invocation produces
  `<topic-slug>-survey.md` and no `research.md` (AC5).

**Approach:**
- Run one real `/research` standard-mode probe; record the prompt, the produced
  filename, and the absence of `research.md` in the PR description.

**Done when:** the PR description carries the recorded observation.

## Rollout

- **Delivery:** big-bang within one release; reversible (prose revert). The only
  irreversible-ish element is adopter muscle memory — mitigated by the
  one-release `research.md` alias note.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** this spec ships before `research-project-mode`
  (which depends on the naming convention). No intra-spec ordering beyond the
  `Depends on:` graph above.

## Risks

- **Residual stale `research.md` reference slips the sweep** — mitigated by the
  AC4 grep-plus-reviewer check over the enumerated nine consumers.
- **The shipped-spec amendment is contested** as a frozen-body edit — mitigated
  by citing the specific CONVENTIONS rule and the applied-mode precedent in AC7;
  the alternative (leave-as-history) is the named fallback if a reviewer rejects
  the amendment.

## Changelog

- 2026-06-22: initial plan.
