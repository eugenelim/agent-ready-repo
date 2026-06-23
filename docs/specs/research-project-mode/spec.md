# Spec: research-project-mode

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0039, ADR-0029, RFC-0035 (adopter-editable config precedent), RFC-0034 (config-file-at-known-path precedent)
- **Brief:** none
- **Contract:** none (project mode is a prompt-only skill discipline + a folder convention + an adopter-created `research-layout.toml`; no `contracts/<type>/` file)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A researcher running a sustained, multi-week investigation gets a **stateful
research project** the `research` pack previously had nowhere to put. Project mode
is the *lifecycle* axis, orthogonal to the existing *depth* axis (quick / standard
/ applied / deep): where episodic research is one-shot, a project accumulates a
corpus over days or weeks across three explicit layers — a raw `sources/` layer
that is never overwritten, a **digest** middle layer (a constructed-column
`synthesis-matrix.md` plus analytic `memos.md`) the pack previously lacked, and a
typed synthesis. A four-skill family drives the lifecycle: `research-project-start`
scaffolds the folder and records the question and a (possibly empty) working
hypothesis; `research-project-digest` clusters sources into emergent matrix
columns and writes memos; `research-project-synthesize` reads the digest and emits
both the project's own typed verdict and a single-file, self-contained
`<topic-slug>-brief.md` that governance can lift whole into an RFC; and
`research-project-check` is a passive stop-signal that reads the matrix by eye and
reports whether the corpus has stopped changing the structure (theoretical
saturation), never advancing a phase on its own.

The whole project is a **prompt-only habit, not infrastructure** (Charter
Principle 3): `phase` is a frontmatter string the agent reads and writes, the
stop-signal is in-prompt judgment, and there is no engine, index, daemon, counter,
or derived metric anywhere. The project lives in **scratch / out-of-repo by
default** (Charter Principle 1, config-driven) — a code repo commits the
*decision* (the brief), never the corpus.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Scaffold the **three-layer folder** at `research-project-start`: `overview.md`
  (question · working-hypothesis, may be empty · shape · `phase` · stop-signal
  state), `sources/` (raw, never overwritten), and the digest + synthesis files
  as the project advances.
- Resolve the project parent by **reading the adopter-created
  `research-layout.toml` first**, then falling back to the in-body **scratch /
  out-of-repo default**, then **eliciting** if neither resolves — never the
  committed repo tree.
- Keep working files **bare-named inside the folder** (the folder namespaces the
  topic), with the **single exception of `<topic-slug>-brief.md`**, which is
  topic-named because it travels out of the folder.
- At `research-project-synthesize`, emit **both** the typed synthesis (`<type>.md`)
  **and** the `<topic-slug>-brief.md` governance handoff; surface a warning when
  the matrix is empty (digest was skipped).
- Keep `research-project-check` **passive**: read the matrix/memos and report a
  qualitative saturation judgment plus a recommendation; let the human decide.

### Ask first

- Pointing the layout at a **durable vault or the committed repo tree** (the
  default is scratch; a vault is the deliberate, configured exception for product
  research).
- Adding a **fifth project skill** or promoting an existing episodic skill into
  the project family beyond the four named here.
- Having `research-project-check` write anything other than an optional
  `verdict_status` into `overview.md` (the one permitted light state write; see
  AC6).
- Editing `docs/CONVENTIONS.md` beyond the single RFC-0039-Decision-7-authorized
  `NNNN-notes/` companion line (AC12); any broader convention change routes
  through `update-conventions` / an RFC.

### Never do

- **No runtime engine, daemon, index, counter, or derived metric** — anywhere in
  the four skills. `phase` is a frontmatter string; the stop-signal is in-prompt
  judgment over the matrix. (Charter Principle 3.)
- **No `research-project-check` phase advance** — it never auto-progresses the
  lifecycle; the human decides.
- **No committing the corpus to the code repo tree** (`docs/`, repo root) — the
  default is scratch / out-of-repo; only the distilled brief is promoted.
- **No hard hypothesis gate** — the working hypothesis may start empty and is
  revised over the project's life (no refuse-without-a-claim).
- **No new dependency, no new top-level directory, no new module boundary** — the
  four skills install into the existing `research` pack alongside its seven
  current skills.
- **No fixed-pillar digest schema** — matrix columns are constructed from the
  material, not pre-set.

## Testing Strategy

- **Skill-body contracts (AC1–AC4, AC6–AC13):** goal-based check — `rg` greps
  against the four new SKILL.md bodies assert the folder layout, the
  config-resolution order, the prompt-only constraints (no engine/counter), the
  passive `-check` rules, the additive provenance axes, the soft-hypothesis rule,
  the reuse mapping, and the trigger phrasing. These are prose contracts in skill
  bodies; structural grep is the right altitude.
- **One observable smoke project (AC5, AC14):** visual / manual QA — a real run
  of `start → (drop 2–3 synthetic source files) → digest → synthesize` over a
  tiny corpus produces the folder, a non-empty `synthesis-matrix.md`, a typed
  synthesis, and a `<topic-slug>-brief.md` that is answer-first and
  self-contained. Recorded in the implementing PR description. A passing grep does
  not substitute for exercising the skills a user invokes.
- **RFC `NNNN-notes/` companion convention (AC12):** goal-based check — the
  convention is documented where the RFC/spec layout conventions live.

## Acceptance Criteria

- [x] **AC1 — `research-project-start` scaffolds the three-layer folder.** The
  skill creates `<parent>/<YYYY-MM-DD>-<topic-slug>/` containing `overview.md`
  (with `question`, `working_hypothesis` — may be empty —, `shape`, `phase:
  capture`, and stop-signal state) and an empty `sources/` directory.
  Verification: `rg` against `research-project-start` SKILL.md names `overview.md`,
  `sources/`, the `phase: capture` initial state, and the `<YYYY-MM-DD>-<topic-slug>`
  folder grammar.

- [x] **AC2 — The digest middle layer is specified.** `research-project-digest`
  reads `sources/*.md`, clusters contributions into **emergent columns** in
  `synthesis-matrix.md` (rows = sources, columns constructed from the material),
  and writes analytic `memos.md`. Verification: `rg` against
  `research-project-digest` SKILL.md names `synthesis-matrix.md`, `memos.md`,
  `sources/`, and the emergent/constructed-column rule (and explicitly *not* a
  fixed pillar set).

- [x] **AC3 — `research-project-synthesize` emits the typed verdict and the
  brief.** The skill reads `synthesis-matrix.md` + `memos.md`, writes the typed
  synthesis `<type>.md` into the folder, and writes `<topic-slug>-brief.md`;
  applies ≥3-source triangulation; surfaces a warning when `synthesis-matrix.md`
  is empty. Verification: `rg` against the SKILL.md names both outputs, the
  matrix/memos inputs, the triangulation rail, and the empty-matrix warning.

- [x] **AC4 — `<topic-slug>-brief.md` is the self-contained governance handoff.**
  The brief is answer-first (BLUF on top), self-contained (no cross-links to other
  project files; safe to copy out of the folder), cited + per-finding
  confidence-tagged, and carries a `## Known unknowns` section — mapping 1:1 onto
  an RFC's *Evidence & prior art*. Verification: `rg` against
  `research-project-synthesize` SKILL.md documents each of the four properties and
  the `## Known unknowns` section; the AC5 smoke brief exhibits them.

- [x] **AC5 — One observable smoke project produces the folder and a valid
  brief.** A real `start → digest → synthesize` run over 2–3 synthetic source
  files produces the folder, a non-empty `synthesis-matrix.md` with constructed
  columns, a typed synthesis file, and a `<topic-slug>-brief.md` that is
  answer-first and contains no cross-links to other project files. Verification:
  manual QA — the PR description records the produced tree and confirms the brief
  is self-contained (self-report is not sufficient; the files are the signal).

- [x] **AC6 — `research-project-check` is passive.** The skill reads the
  matrix/memos by eye and reports a qualitative saturation judgment (is the corpus
  still changing the matrix structure; are recent sources adding columns or just
  confirming; are load-bearing claims corroborated) plus a recommendation. It
  **never advances `phase`**. It **may** optionally write `verdict_status` into
  `overview.md` (the single permitted light state write; RFC-0039 open question 1,
  resolved: allow the status write, never a phase advance). Verification: `rg`
  against `research-project-check` SKILL.md documents the read-by-eye judgment, the
  no-auto-phase-advance rule, and the bounded `verdict_status`-only write; and
  documents that there is no counter/metric/score.

- [x] **AC7 — Config-driven layout, scratch by default.** The default layout
  (parent, filenames, schema) ships **inside the `research-project-start` skill
  body**; the parent defaults to a **scratch / out-of-repo** location
  (gitignored `.context/research/` or a user-level path), never the committed repo
  tree. An adopter overrides it via an **adopter-created** `research-layout.toml`
  at a documented known path, read at `research-project-start`; if no override
  exists, the scratch default is used or elicited. Verification: `rg` against the
  SKILL.md documents the read-`research-layout.toml`-then-default-then-elicit
  order, the scratch default, the never-commit-the-corpus rule, and the
  adopter-created (not shipped-into-a-projected-path) nature of the override.

- [x] **AC8 — Prompt-only; no engine creeps in.** None of the four new skills
  ships executable code, a script, a daemon, an index, a counter, or a derived
  metric that manages corpus state or computes saturation; `phase` and
  `verdict_status` are frontmatter strings the agent reads/writes. Verification:
  the four new skill directories contain no `scripts/` that generate state or
  compute saturation (`find packs/research/.apm/skills/research-project-* \( -name
  '*.py' -o -name '*.sh' \)` returns nothing state-generating); `rg` confirms each
  body frames `phase`/stop-signal as prompt-driven.

- [x] **AC9 — Additive provenance grading.** Per-source frontmatter in `sources/`
  gains two **optional, independent** axes — `reliability` (source track-record)
  and `credibility` (corroboration of the specific claim), modelled on the
  Admiralty/NATO scale — that *inform* the existing rail without replacing it. The
  claim-level rail stays **GRADE confidence + ≥3-source triangulation**; wiki-kit
  v1's binary Two-Source Rule is folded into triangulation, not shipped
  separately. Verification: `rg` against the project skill bodies names
  `reliability` and `credibility` as optional source axes and reaffirms GRADE +
  triangulation as the claim-level rail.

- [x] **AC10 — Soft, revisable working hypothesis.** `overview.md`'s
  `working_hypothesis` may be empty at start and is formed/revised in `memos.md`
  as evidence accumulates; there is no refuse-without-a-claim gate. Verification:
  `rg` against `research-project-start` + `research-project-digest` SKILL.md
  documents the may-be-empty start and the revise-in-memos path, and the absence
  of a hard hypothesis gate.

- [x] **AC11 — Existing skills reused as phase operations, not rewritten.** The
  project skill bodies reference the seven existing skills in their phase roles:
  `research` (per-source episodic retrieval), `source-map` (populates `sources/`),
  `build-outline` (seeds initial matrix columns), `identify-perspectives`
  (perspective columns for contested topics), `compare-hypotheses` (**is**
  `hypotheses.md` for the adjudication shape), `devils-advocate` (run at
  synthesis), `decision-archaeology` (stays standalone). Verification: `rg`
  confirms the reuse mapping is documented in the project skill bodies; **and**
  `git diff --stat origin/main` over the seven existing SKILL.md files is empty —
  because `research-typed-artifacts` ships first (separate PR), its topic-slug
  rename is already on `main` at this spec's review time, so this PR adds **no**
  change to the seven existing skills (the negative — no project-phase logic
  injected — is checked against `origin/main`, not merely asserted).

- [x] **AC12 — RFC `NNNN-notes/` companion convention documented.** The
  convention that an RFC may carry an `NNNN-notes/` companion folder for promoted
  research (mirroring `docs/specs/<feature>/notes/`) is documented where the RFC /
  spec layout conventions live (`docs/CONVENTIONS.md`). This is a CONVENTIONS body
  edit, which normally routes through `update-conventions` / an RFC — it lands in
  this spec PR **because RFC-0039 Decision 7 explicitly authorizes it** (the
  Approved RFC names the companion convention); the named fallback is to split it
  into a follow-up `update-conventions` PR if a reviewer rejects the in-spec edit.
  Verification: `rg -F 'notes/'` against `docs/CONVENTIONS.md` in the RFC section
  names the companion convention.

- [x] **AC13 — Project mode triggers only on explicit phrasing.** The four
  project skills' `description:` frontmatter triggers on explicit "start a
  research project" / project-lifecycle phrasing; the depth axis (`/research`)
  stays the default front door and is not displaced. Verification: `rg` against
  each project SKILL.md `description:` shows project-lifecycle trigger phrasing;
  the `research` skill's trigger surface is unchanged by this spec.

- [x] **AC14 — Pack version bump + changelog.** `packs/research/pack.toml` and the
  pack's `plugin.json` are bumped to the next minor after `research-typed-artifacts`
  (0.4.0), and `docs/product/changelog.md` `[Unreleased]` carries an `### Added`
  entry for project mode. Verification: goal-based grep on the version and the
  changelog entry.

## Assumptions

- Technical: research-pack skills live at
  `packs/research/.apm/skills/<name>/SKILL.md`; the four new skills install there
  (source: directory listing 2026-06-22).
- Technical: adding four prompt-only skills does not change the adapter contract
  (pinned 0.12); skills are body-level primitives already supported (source:
  `packs/research/pack.toml`; RFC-0039 § Repo precedent names only a pack version
  bump).
- Technical: `research-layout.toml` is adopter-created at a known path and read at
  start — not shipped into a projected path — to sidestep the self-host drift gate
  (source: RFC-0039 § Decision 5; RFC-0035 `references/sso-config.toml`
  precedent).
- Technical: `.context/` is per-workspace and gitignored, so a scratch corpus does
  not survive the workspace; high-stakes reasoning trails are archived to a
  durable-but-separate home and linked from the brief (source: RFC-0039 §
  Decision 5 audit-trail caveat).
- Process: RFC-0039 + ADR-0029 are Accepted; this spec depends on
  `research-typed-artifacts` (the bare-name-inside-folder rule needs the episodic
  prefix rule) (source: RFC-0039 § Follow-on artifacts).
- Process: RFC-0039 open question 1 (whether `-check` may write `verdict_status`)
  is resolved here — allow the light status write, never a phase advance (source:
  RFC-0039 § Open questions recommended default; user confirmation 2026-06-22).
- Product: project mode serves sustained multi-source decisions (RFCs/ADRs/specs)
  whose durable value is the distilled brief, and product-research vaults via the
  opt-in durable-layout config (source: RFC-0039 § Problem & goals / Decision 5).
