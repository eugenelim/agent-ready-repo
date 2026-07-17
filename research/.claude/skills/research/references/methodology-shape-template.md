# Methodology shape — artifact template

The authoring template for the **`methodology` output shape** — the artifact a
`/research` run (or a project-mode `methodology` shape) produces when the
question is *process-shaped*: *"the best way to do / run / build / train X, end
to end, for my situation."* It answers with a **staged, contingency-adapted,
maturity-aware, evidence-graded description of how the activity is done** — not a
claim-organized survey the reader must re-sequence by hand.

This template is a **reference the agent authors from**, not a script: the
filename (`<topic-slug>-methodology.md` episodically, bare `methodology.md`
inside a project folder) and the prose are produced by the agent following this
body (Charter Principle 3). It is named distinctly from
[`methodologies.md`](methodologies.md), which catalogues the pack's own
*research-method* disciplines (STORM, PRISMA, ACH, …) and is a different
document — do not confuse or edit that one.

**Depth.** The methodology shape defaults to **`applied`** depth (it is a
practitioner "how is this really done" question, so the grey-literature overlay
applies). Scholarly domains override to `standard` / `deep` via the ordinary
depth cues — the shape does not change the depth axis, it selects an output
topology on top of it.

## The six sections, each grounded 1:1 in a discipline

| § | Section | Grounding discipline | Mandatory? |
|---|---|---|---|
| 1 | Scope frame | SIPOC (Suppliers · Inputs · Process · Outputs · Customers) | yes |
| 2 | Stage spine | process discovery + hierarchical task decomposition | yes |
| 3 | Contingency branches | situational method engineering | **yes — the differentiator** |
| 4 | Maturity ladder | Dreyfus model of skill acquisition | **yes — the differentiator** |
| 5 | Failure modes | cognitive task analysis | yes |
| 6 | Evidence & confidence | GRADE (inherited unchanged from `/research`) | yes |

**§3 and §4 are mandatory and are the entire differentiator.** They plus the
direction axis (world best-practice, outside-in — see the fencing note in
`SKILL.md`) are what separate a methodology artifact from an `applied` survey
and from `map-internal-process`. **A methodology artifact missing §3 or §4 is a
survey with headings, and is flagged incomplete** — do not ship it. The other
four sections a good survey might also carry; §3 and §4 are the ones that make
the artifact a *method*, not a reading list.

## Slide-ready by construction (`markdown-to-pptx` handoff)

The artifact is authored so it drops into `markdown-to-pptx` with **no
reshaping** — named as a consumer *by reference only*; `research` gains no
dependency on `converters`, and a repo without the converters pack still gets a
perfectly good markdown artifact.

- **Sections are `H1`** (`#`) — one slide each.
- **Stages inside §2 are `H2`** (`##`) — one slide each.
- **All finer detail is a bullet list.** Sub-steps are bullets, never headings.
- **Never author an `H3`.** `markdown-to-pptx` maps only `H1`/`H2` to slides and
  renders a literal `###` line into the parent slide's body as text — so an
  `H3` sub-step silently becomes body noise. Sub-steps are always bullets.

---

**PART A — the skeleton.** Copy these six `H1` sections. Within §2, each stage is
an `H2`. Everything finer is a bullet. The bracketed lines are authoring notes,
not artifact content — replace them.

# 1. Scope frame

- **Discipline: SIPOC.** Bound the activity before describing it, so the reader
  knows exactly what is and isn't in view.
- **Suppliers** — who/what provides the inputs.
- **Inputs** — what the activity consumes to start.
- **Process** — the one-line name of the activity (the thing the rest of the
  artifact stages).
- **Outputs** — what "done" produces.
- **Customers** — who consumes the outputs / for whom "done" is done.
- **In / out of scope** — one line naming the tempting-adjacent activity this
  method does *not* cover, so scope creep is visible.

# 2. Stage spine

- **Discipline: process discovery + hierarchical task decomposition.** The
  end-to-end sequence, decomposed one level (stages → their sub-steps as
  bullets). Order matters: this is the spine a reader follows start to finish.
- Author each stage as an `H2` below. Keep stages to the natural few; put the
  finer steps as bullets under each. Never descend to an `H3`.

## Stage 1 — <name>

- <sub-step> · <sub-step> · what this stage produces that the next consumes.

## Stage 2 — <name>

- <sub-step> · <sub-step> · the handoff to the next stage.

## Stage N — <name>

- <sub-step> · <sub-step> · the terminal output (ties back to §1 Outputs).

# 3. Contingency branches

- **Discipline: situational method engineering — MANDATORY.** The stage spine
  above is the *default* path; real situations fork it. This section names the
  **situational factors** that change the method and, for each, **how the spine
  adapts**. This is a differentiator: a survey lists options; a methodology tells
  you *which* path *your* situation takes.
- Author as **`if <situation> → <how the spine changes>`** branches, each tied to
  a stage in §2. At least the load-bearing two or three; a `comprehensively`
  artifact chases the second-order forks too.
- **Incomplete without this section.** A methodology with no contingency branches
  has quietly assumed one situation fits everyone — flag it and add them.

# 4. Maturity ladder

- **Discipline: Dreyfus model of skill acquisition — MANDATORY.** How the
  *doer's* competence changes what "doing it well" means — novice → advanced
  beginner → competent → proficient → expert — so the reader can locate
  themselves and know what the next rung requires.
- Author one bullet per rung: what the doer at that rung does, and the shift that
  moves them up.
- **Reframe, never omit silently (RFC-0057 Open Question 1).** When
  skill-progression does not apply — a **one-off deliverable** with no repeating
  practitioner — author §4 instead as an **adoption / capability-maturity axis**:
  **crawl → walk → run** of the *deliverable or the practice* (a first
  crawl-grade version, a walk-grade hardened one, a run-grade optimized one). The
  "journey" section/slide **always exists**; only its axis changes. Never drop the
  section — a methodology with no maturity axis has flattened the difference
  between a first attempt and a mastered one.

# 5. Failure modes

- **Discipline: cognitive task analysis.** The non-obvious ways the activity goes
  wrong — the mistakes experts have internalized and novices repeat. Surface the
  *tacit* knowledge, not the obvious warnings.
- One bullet per failure mode: **what goes wrong · why it's easy to miss · the
  guard**.

# 6. Evidence & confidence

- **Discipline: GRADE (inherited unchanged from `/research`).** Every
  load-bearing claim in the artifact carries a confidence tag from the closed set
  `[high]` / `[moderate]` / `[low]` / `[uncertain]`, with the downgrade factor
  named. Applied-mode overlay factors (`survivorship bias`, `stale prior art`)
  apply, since best-practice claims are the ones most often vendor-blogged.
- Close with a **`## Known unknowns`** block, exactly as a `/research` survey
  does — known-unknowns (answerable in principle; name the evidence that would
  close them) and unknowables (no evidence settles them). A method is honest
  about the parts of the activity the evidence can't yet ground.

---

**PART B — a worked exemplar.** A full six-section artifact for one topic, so the
shape is concrete. Topic: **run a legacy-system data migration, end to end.**

# 1. Scope frame

- **Suppliers:** source-system DBAs; the business owners of the data domain.
- **Inputs:** the legacy schema + data; the target schema; a downtime budget.
- **Process:** migrate a legacy datastore's data into a new system, verified.
- **Outputs:** migrated data that reconciles against source; a cutover record.
- **Customers:** the applications and reports that read the target system.
- **In / out of scope:** *in* — schema mapping, ETL build, cutover, reconciliation.
  *Out* — application rewrite on top of the new store (a separate effort).

# 2. Stage spine

## Stage 1 — Profile the source

- Row counts, null rates, encodings, orphaned keys, real-vs-declared types.
- Produces the *actual* shape of the data (not the schema's claim) that mapping
  depends on. [moderate] — profiling tools agree the declared schema routinely
  lies; downgrade: `survivorship bias` (clean-migration write-ups over-represent).

## Stage 2 — Map source → target

- Field-by-field mapping; encode the transforms; decide defaults for absent data.
- Produces the mapping spec Stage 3 builds from.

## Stage 3 — Build and dry-run the ETL

- Implement extract/transform/load against a *copy*; run it end to end; measure
  duration against the downtime budget.
- Produces a repeatable, timed ETL and a first reconciliation report.

## Stage 4 — Cut over

- Freeze writes on source, run the final ETL, repoint consumers, unfreeze.
- Produces the live target system; the freeze window is the risk peak.

## Stage 5 — Reconcile and decommission

- Reconcile target against source (counts, checksums, spot business rules);
  keep source read-only until confidence holds; then decommission.
- Produces the verified end state (ties back to §1 Outputs).

# 3. Contingency branches

- **if downtime budget ≈ zero → the big-bang cutover in Stage 4 forks to a
  phased/trickle migration** with dual-write and a sync window, trading a longer
  overall timeline for a near-zero freeze. [high].
- **if source and target engines differ (heterogeneous) → Stage 2 mapping
  expands** to cover type-system and dialect gaps (e.g. no native boolean,
  different date/timezone semantics); a homogeneous move skips most of this. [high].
- **if data volume exceeds a single-window ETL → Stage 3 forks to incremental
  batching** with a change-data-capture tail to catch writes during the run. [moderate].

# 4. Maturity ladder

- **Novice:** runs the ETL once, checks it "looks right," cuts over on the happy
  path. Moves up by getting burned on a silent data-loss they didn't reconcile.
- **Advanced beginner:** adds a reconciliation step, but reconciles counts only.
  Moves up by learning that counts match while values are corrupted.
- **Competent:** reconciles counts *and* content, dry-runs against a copy, times
  the window. Moves up by planning rollback before the freeze, not during it.
- **Proficient:** designs for reversibility — keeps source authoritative until
  reconciliation holds, rehearses cutover. Moves up by anticipating the
  situational forks (§3) rather than discovering them mid-cutover.
- **Expert:** treats the migration as a reversible, observable pipeline; knows
  from the source profile (§1/Stage 1) which forks this migration will take
  before writing the mapping.
- *(One-off reframe, if this migration is a single never-repeated event: read the
  ladder as **crawl** = a scripted one-shot ETL with count reconciliation; **walk**
  = dry-run + content reconciliation + a rollback path; **run** = phased cutover
  with dual-write and CDC.)*

# 5. Failure modes

- **Silent truncation on type-narrowing** · easy to miss because row counts still
  match · guard: content-level reconciliation, not count-only (see §4 advanced-
  beginner rung). [high].
- **Encoding loss (UTF-8 → Latin-1 mojibake)** · easy to miss because ASCII rows
  pass and only accented/CJK data corrupts · guard: profile encodings in Stage 1
  and spot-check non-ASCII rows in reconciliation. [high].
- **Referential integrity broken at cutover** · easy to miss because each table
  migrates cleanly in isolation · guard: migrate and reconcile by aggregate root,
  not table-by-table. [moderate].

# 6. Evidence & confidence

- Confidence tags above follow the closed GRADE set; applied-mode overlay
  (`survivorship bias`, `stale prior art`) applies because clean-migration
  case studies over-represent successes.

## Known unknowns

- **Known-unknown:** the actual freeze-window duration for *this* dataset. Would
  be closed by: the Stage 3 dry-run against a production-sized copy.
- **Unknowable:** whether an undocumented downstream consumer reads the source
  directly. Why not: no inventory records ad-hoc readers; only cutover surfaces them.

---

**Before shipping any methodology artifact, confirm §3 and §4 are present and
substantive.** If either is missing or is a single hand-wave, the artifact has
collapsed into a survey with headings — the failure this shape exists to prevent.
Add the contingency branches and the maturity/adoption axis, or do not ship it as
a `methodology`.
