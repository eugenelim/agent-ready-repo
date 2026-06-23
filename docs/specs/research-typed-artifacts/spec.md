# Spec: research-typed-artifacts

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0039, ADR-0029, RFC-0038 (forward-only migration + legacy retention)
- **Brief:** none
- **Contract:** none (the artifact-naming scheme is a prompt-only convention carried in the skill bodies; no `contracts/<type>/` file)
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A researcher who runs the `research` pack episodically gets outputs **named by
their topic and research type** — `<topic-slug>-<type>.md` (e.g.
`oauth-pkce-survey.md`, `db-engines-comparison-matrix.md`) — instead of a single
generic `research.md` that collides across investigations and says nothing about
what the file *is*. Two investigations in one working directory no longer
overwrite each other, and a file's name alone tells the reader whether it is a
survey, a fact-check, a comparison matrix, a shortlist, a structural blueprint, a
hypothesis adjudication, or an adversarial counterpoint set. Quick mode is
unchanged — it stays inline with no file, by design. The former name `research.md`
is documented as a recognised legacy alias for one release so existing references
and muscle memory resolve to the new scheme without dangling.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Name every **persisted episodic artifact** `<topic-slug>-<type>.md`, where
  `<type>` is drawn from the canonical type vocabulary in `## Acceptance
  Criteria` (AC1) and `<topic-slug>` is a short kebab-case slug derived from the
  research question.
- Keep **quick mode inline** — no file, unchanged from current behaviour.
- Carry the **topic-slug derivation rule** and the **type vocabulary** in the
  body of each artifact-producing skill that the change touches, so the naming is
  reproducible by any agent following the skill.
- Update the legacy alias note and every live consumer reference **in the same
  PR** as the skill-body change (no doc drift).

### Ask first

- Adding a **new artifact type** to the vocabulary beyond the eight RFC-0039
  Decision 2 fixes, or renaming an artifact stem the migration set does not name.
- Changing **quick mode** to produce a file (the RFC keeps it inline; the
  `>5-fetch abort-or-upgrade` rail is the persisting signal).
- Any change to the **research-pack shipped spec** beyond updating its
  `research.md` references to the typed scheme (the frozen-spec resolution below).

### Never do

- **No new dependency**, **no new top-level directory**, **no new module
  boundary** — this is a naming-convention change to existing skill bodies and
  docs only.
- **No runtime engine, script, or code that generates the filename** — the name
  is produced by the agent following the skill body (Charter Principle 3,
  prompt-only). Any existing `scripts/` under the pack stay retrieval helpers,
  not name generators.
- **No dual-write** — the skills emit *only* the typed name; `research.md` is a
  documented alias, never a second file written alongside (RFC-0038
  forward-only).
- **No permanent alias** — the `research.md` alias note is retained for exactly
  one release, then removed (RFC-0038 one-release retention).

## Testing Strategy

- **Type vocabulary, slug rule, alias note, consumer migration (AC1–AC4, AC6):**
  goal-based check — `rg -F` greps against the skill bodies and docs assert the
  typed names, the slug rule, the alias note, and the absence of stale
  `research.md` output references in live consumers. Naming is prose in a skill
  body, so a structural grep is the right altitude; there is no logic to unit-test.
- **One observable episodic run (AC5):** visual / manual QA — a real `/research`
  standard-mode invocation through its documented happy path produces a
  `<topic-slug>-survey.md` file (and no `research.md`), recorded in the
  implementing PR description. A passing grep alone does not satisfy this: the
  artifact a user invokes must be exercised end-to-end.
- **Shipped-spec amendment (AC7):** goal-based check — the research-pack spec's
  `research.md` references resolve to the typed scheme and its changelog carries
  the dated amendment entry; verified by grep.

## Acceptance Criteria

- [x] **AC1 — Canonical type vocabulary documented.** The `research` skill body
  documents the canonical episodic artifact-type table, mapping research
  mode/shape to filename type exactly as RFC-0039 Decision 2 fixes it: quick →
  *inline, no file*; fact-check → `fact-check`; standard/applied survey →
  `survey`; deep → `survey` + `counterpoints`; comparison/decision →
  `comparison-matrix`; ranked candidates → `shortlist`; spatial/structural →
  `blueprint`; hypothesis adjudication → `hypotheses`. That is **seven distinct
  type stems across eight mode/shape rows** — `survey` covers both standard/applied
  and deep, so it appears twice; quick produces no file. Verification: `rg -F` for
  each of the seven type stems (`fact-check`, `survey`, `counterpoints`,
  `comparison-matrix`, `shortlist`, `blueprint`, `hypotheses`) against the
  `research` SKILL.md returns ≥1 hit each.

- [x] **AC2 — Topic-slug prefix rule documented and applied across episodic
  artifacts.** Each artifact-producing skill that persists an episodic file
  documents that its output is named `<topic-slug>-<type>.md`, with `<topic-slug>`
  a short (~2–5 word) kebab-case slug derived from the research question (e.g.
  "OAuth PKCE for SPAs" → `oauth-pkce`). The rule applies to two groups:
  - **RFC-fixed stems** (the AC1 vocabulary, enumerated in RFC-0039 Decision 2):
    `research`/survey, `devils-advocate`/counterpoints, `compare-hypotheses`/hypotheses.
  - **Spec-level generalization** of the RFC's "name artifacts by topic + type
    *across episodic modes*" intent (RFC-0039 § Goals) to the scoping/archaeology
    skills whose stems the Decision 2 table does **not** enumerate:
    `identify-perspectives`/perspectives, `build-outline`/outline,
    `source-map`/sources, `decision-archaeology`/archaeology. These keep their
    existing type-descriptive stem and gain only the `<topic-slug>-` prefix; the
    generalization is recorded here (not a silent extension) and is consistent
    with the Boundaries `Ask first` on renaming un-named stems.

  Verification: each of the seven artifact-producing SKILL.md files contains the
  literal token `<topic-slug>-` (`rg -F '<topic-slug>-'` returns ≥1 hit per file).

- [x] **AC3 — `research.md` documented as a one-release legacy alias.** The
  `research` SKILL.md states that `research.md` is the prior name for the survey
  artifact, retained as a recognised alias for one release (RFC-0038
  forward-only), and that the skill emits only the typed name. Verification:
  `rg -i 'legacy alias|formerly|deprecated' packs/research/.apm/skills/research/SKILL.md`
  returns ≥1 hit on a line that also names `research.md`.

- [x] **AC4 — No live consumer asserts `research.md` as a current output.** After
  migration, the nine live consumers (3 skill bodies —
  `research`/`devils-advocate`/`build-outline` SKILL.md — plus 1 reference doc
  `research/references/confidence-schema.md`; and 5 docs:
  `docs/guides/research/{tutorials/research-first-session,reference/research-pack,how-to/research-pipelines}.md`,
  `docs/guides/_shared/how-to/run-a-full-inception.md`,
  `docs/specs/research-pack/plan.md`) reference `research.md` only as the named
  legacy alias, never as the current output artifact. Verification: a reviewer
  reads each residual `research.md` occurrence in those files and confirms it
  sits on a line that also carries an alias/deprecation marker (`legacy`,
  `alias`, `formerly`, `deprecated`).

- [x] **AC5 — One observable episodic run produces a typed artifact.** A real
  standard-mode `/research` invocation through its documented happy path writes a
  `<topic-slug>-survey.md` file to the working directory and writes **no**
  `research.md`. Verification: manual QA — the implementing PR description records
  the probe prompt, the produced filename, and the absence of `research.md`
  (self-report from the model is not sufficient; the file on disk is the signal).

- [x] **AC6 — Quick mode unchanged.** Quick mode produces no artifact file of any
  name (the AC12 guarantee in the research-pack spec is preserved). Verification:
  `rg` confirms the `research` SKILL.md still documents quick mode as inline /
  artifact-free; the manual-QA quick probe in the research-pack spec's existing AC
  still holds (no file matching any episodic type stem appears).

- [x] **AC7 — Shipped research-pack spec amended, not left stale.** The frozen
  `docs/specs/research-pack/spec.md` has its `research.md`-pinning acceptance
  criteria and verification greps updated to the typed scheme (with the alias
  note), recorded by a dated entry in that spec's `## Changelog`. Resolution
  rationale: two CONVENTIONS rules are in tension — the document-lifecycle table
  (`docs/CONVENTIONS.md` line ~103) classes a shipped spec as *Frozen* ("bodies
  cannot" change), while the § 4 spec-section intro (lines ~265-270) says that
  after a feature ships its spec "is reference material that should be updated
  alongside behavior changes." The **more specific spec-section rule wins** over
  the general lifecycle table, and the applied-mode amendment (2026-05-28, which
  added AC26–AC29 to the already-shipped research-pack spec) is the standing
  precedent for post-ship amendment; the leave-as-history alternative (record the
  rename only in this new spec) is the named fallback if a reviewer rejects
  amending the frozen body. Verification: `rg -F 'research.md'
  docs/specs/research-pack/spec.md` — every remaining hit is an alias reference;
  the changelog contains a `2026-` entry naming the typed-artifacts rename.

## Assumptions

- Technical: research-pack skills live at
  `packs/research/.apm/skills/<name>/SKILL.md` (source: directory listing
  2026-06-22).
- Technical: the `research` pack is at version 0.2.0 and this change is a minor
  bump to 0.3.0 (source: `packs/research/pack.toml`).
- Technical: adding skill-body prose does not change the adapter contract (pinned
  at 0.12); the contract governs how primitives project, not their naming
  (source: `packs/research/pack.toml` `[pack.adapter-contract]`; RFC-0039 §
  Repo precedent names only a pack version bump).
- Technical: exactly 10 consumers reference the output artifact `research.md` — 9
  live + 1 shipped spec (source: repo grep 2026-06-22, matching RFC-0039 §
  Decision 2 migration).
- Process: the frozen-spec tension is resolved by amending the shipped spec —
  applying the more specific § 4 spec-section rule ("after a feature ships its
  spec is reference material updated alongside behavior changes", lines ~265-270)
  over the general document-lifecycle table's frozen-body rule (line ~103), with
  the applied-mode amendment as precedent and leave-as-history as the named
  fallback (source: `docs/CONVENTIONS.md` lines ~103 vs ~265-270; research-pack
  spec changelog; user confirmation 2026-06-22).
- Product: this serves researchers running episodic research who keep multiple
  investigations in one directory, and is the precondition for project mode's
  bare-name-inside-folder rule (source: RFC-0039 § Decision 2 / Follow-on
  artifacts).
