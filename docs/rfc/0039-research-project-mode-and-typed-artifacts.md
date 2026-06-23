# RFC-0039: Research project mode + typed, topic-named artifacts

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental (optional: trial running, results pending — see the Experiment / validation section) -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-22
- **Date closed:** 2026-06-22
- **Related:** RFC-0034 (`profiles/<name>.toml` config precedent), RFC-0035 (`references/sso-config.toml` adopter-editable config), RFC-0038 (forward-only migration + `Rejected` status), `packs/research` (the pack this extends); prior art: llm-wiki-kit v1 research layer ([github.com/eugenelim/llm-wiki-kit](https://github.com/eugenelim/llm-wiki-kit), commit `98bfef5` — external repo, un-pinnable from here)

## The ask

**Recommendation (BLUF):** Extend the `research` pack along a second axis. Today it scales by *depth* (quick → standard → applied → deep), all one-shot. Add an orthogonal **project** mode for sustained, multi-week investigations: a stateful folder with three explicit layers (raw capture → a working/digest layer the pack currently lacks → a typed synthesis), driven by a small family of phase skills. In the same change, **name episodic outputs by topic + research type** instead of the generic `research.md`.

**Why now (SCQA):**
- *Situation:* the `research` pack does evidence-grounded research well for one-shot questions — a single `research.md` with GRADE confidence and ≥3-source triangulation.
- *Complication:* a sustained investigation (continually gather sources, manage a growing corpus, extract, synthesize, form and revise a hypothesis toward a verdict) is a **different kind of object** with a lifecycle, not "more research." Every established research discipline manages it with distinct named artifacts and a digest layer between raw and synthesis; we have neither. And one generic `research.md` collides across investigations and hides what each artifact *is*.
- *Question:* should the pack grow a project mode + a typed artifact taxonomy, and how should the sustained-project state be structured so it stays a *habit* (Charter Principle 3) rather than runtime infrastructure?

**Decisions requested:**
1. **Project mode ships as a 4-skill family** (`research-project-start` / `-digest` / `-synthesize` / `-check`), not a `mode:` flag on `/research`. · *why:* phases have distinct triggers and carry a state machine a mode-param can't. · decide-by: this review (default: yes).
2. **Episodic outputs are named `<topic-slug>-<type>.md`** (e.g. `oauth-pkce-survey.md`); quick mode stays inline with no file; `research.md` kept as a one-release forward-only legacy alias (per RFC-0038). · decide-by: this review (default: yes).
3. **The middle/digest layer uses emergent columns** (`synthesis-matrix.md` + `memos.md`), not fixed pillars. · decide-by: this review (default: yes).
4. **The working hypothesis may start empty and is revised over the project's life** — replacing wiki-kit v1's hard "refuse without a central claim" gate. · decide-by: this review (default: yes).
5. **The target layout is config-driven, defaulting to scratch / out-of-repo** (not the repo tree) via an adopter-editable `research-layout.toml`; the durable-vault path is opt-in for product research. · decide-by: this review (default: yes).
6. **Provenance grading is additive**: keep GRADE + ≥3-source triangulation as the claim-level rail; add optional per-source reliability+credibility axes; fold wiki-kit's Two-Source Rule into triangulation. · decide-by: this review (default: yes).
7. **Synthesize emits a single-file research `<topic-slug>-brief.md`** — a self-contained, answer-first, cited distillation sized to lift whole into an RFC's *Evidence & prior art* — alongside the typed synthesis artifact. · *why:* governance consumes one file, not a folder of sources+matrix+memos. · decide-by: this review (default: yes).

## Problem & goals

The pack treats all research as a one-shot transaction: ask → retrieve → synthesize `research.md` → done. Two problems follow.

**1. No support for a sustained project.** A multi-week investigation needs a corpus that grows over time, a raw layer that is never overwritten, a place to *digest* sources so growth stays tractable (you reason over the digest, not by re-reading 30 sources), a working hypothesis that is tracked and revised, and a stop signal. The four-discipline survey ([`0039-notes/survey-managing-research-projects.md`](0039-notes/survey-managing-research-projects.md)) found these are exactly the things a one-shot lookup lacks — and that every discipline inserts a **middle layer** (a concept/synthesis matrix, analytic memos, or an evidence×hypothesis matrix) between raw capture and synthesis. The pack jumps `sources → research.md` in one hop, so there is nowhere for a long investigation to *live*.

**2. One generic artifact name.** Every file is `research.md`. Two investigations in one directory collide; the name says nothing about whether the file is a comparison, a ranked shortlist, a hypothesis adjudication, or a prior-art survey. The disciplines surveyed each name artifacts by *type and stage* (PRISMA names ~12; ACH names five) — never one generic doc.

**Goals.**
- Add a **project** mode: a stateful, multi-file research project with a capture → digest → synthesize → feedback lifecycle and a passive stop-signal.
- Introduce the missing **middle layer** (emergent-column synthesis matrix + analytic memos).
- **Name artifacts by topic + type** across episodic modes; keep quick inline.
- Make the project **layout config-driven** so the pack stays adopter-neutral and a vault (e.g. llm-wiki-kit) can supply its own convention.
- **Preserve** the pack's existing strengths (GRADE + triangulation, applied grey-lit overlay, mode-graded depth, parallel retrievers) and **reuse** existing lifecycle skills as the phase operations rather than rewriting them.

**Non-goals.**
- *A runtime engine or daemon.* The project mode is skill-driven file operations, not a service (see De-risk).
- *Fixed-pillar ontology.* We deliberately drop wiki-kit v1's fixed entities/attributes/mental-model/verdict columns in favour of emergent ones (decision 3).
- *Mandating one storage layout.* We ship a default but do not hardcode it (decision 5).
- *A hard hypothesis gate.* We deliberately do not require a central claim up front (decision 4).
- *Output-quality grading of the synthesis.* Confidence rating already exists per finding; scoring the *artifact* is out.

## Proposal

### Two orthogonal axes

`research` gains a second axis. **Depth** (quick/standard/applied/deep) stays as-is for one-shot work. **Lifecycle** is new: *episodic* (one-shot, today's behaviour) vs *project* (sustained, stateful). The two are independent — a project's individual captures still use episodic retrieval under the hood.

### Decision 1 — project mode = a 4-skill family

Mirroring the disciplines' phase operations (and wiki-kit v1's four skills), project mode ships as:

- **`research-project-start`** — scaffold the project folder; record the question and (optional) working hypothesis; set `phase: capture`.
- **`research-project-digest`** — read `sources/*.md`, cluster contributions into **emergent columns** in `synthesis-matrix.md`, write analytic `memos.md`; the grounded-theory "coding" step.
- **`research-project-synthesize`** — read the matrix + memos, produce the typed synthesis artifact (`<type>.md`), apply triangulation, and emit the single-file **`<topic-slug>-brief.md`** handoff (Decision 7).
- **`research-project-check`** — **passive** stop-signal: the agent *reads* the matrix and memos by eye and reports a qualitative judgment — is the corpus still changing the matrix structure (theoretical saturation), are recent sources adding columns or just confirming, are the load-bearing claims corroborated — plus a recommendation. This is in-prompt judgment, not a computed metric or a derived score; there is no counter, no engine. Never auto-progresses a phase; the human decides.

A `mode:` flag is rejected because it cannot carry a state machine and would overload `/research`'s clean episodic surface.

### Decision 2 — typed, topic-named artifacts

| Mode / shape | Artifact |
|---|---|
| quick | inline, **no file** |
| fact-check | `<topic-slug>-fact-check.md` |
| standard / applied survey | `<topic-slug>-survey.md` |
| deep | `<topic-slug>-survey.md` + `<topic-slug>-counterpoints.md` |
| comparison / decision | `<topic-slug>-comparison-matrix.md` |
| ranked candidates | `<topic-slug>-shortlist.md` |
| spatial / structural | `<topic-slug>-blueprint.md` |
| hypothesis adjudication | `<topic-slug>-hypotheses.md` (this *is* `compare-hypotheses`) |

Inside a **project** folder the directory already namespaces the topic, so inner files stay bare (`<type>.md`) — **except `<topic-slug>-brief.md`**, which is topic-named because it travels out of the folder (Decision 7). Quick mode produces no file by design — if a quick check needs persisting, that is the signal it should have been `standard`/`applied` (the existing >5-fetch abort-or-upgrade rail enforces this).

**Migration.** A repo-wide grep, filtered to genuine references to the pack's *output artifact* (excluding `*-research.md` filename collisions like `0021-greenfield-inception-research.md`, `.context/` scratch notes, and the RFC index), finds **10 consumers**:
- *Live skill bodies (4)* — `research`, `devils-advocate`, `build-outline` SKILL.md + `research/references/confidence-schema.md`.
- *Live docs (5)* — 3 guides under `docs/guides/research/` (`how-to/research-pipelines`, `reference/research-pack`, `tutorials/research-first-session`) + `docs/guides/_shared/how-to/run-a-full-inception.md` + `docs/specs/research-pack/plan.md`.
- *Shipped spec (1)* — `docs/specs/research-pack/spec.md` is **Shipped → Frozen** per the CONVENTIONS lifecycle table; its ACs pin `research.md` as the output contract. There is a genuine tension here: CONVENTIONS § 4 ("update reference material alongside behaviour changes") vs the lifecycle table's frozen-body rule. The implementing spec must resolve it explicitly — either a spec amendment, or recording the rename in the new spec and leaving the shipped one as history.

Because **no frozen ADR/RFC body** references the output artifact (those matches were filename or scratch-path collisions), the alias is a **one-release forward-only** retention per RFC-0038 — not permanent. The implementing spec updates the 9 live consumers to the typed names, handles the shipped spec per the tension above, and documents `research.md` as the deprecated alias for one release.

### Decision 3 — the middle layer (emergent columns)

```
<configured-parent>/<YYYY-MM-DD>-<topic-slug>/
  overview.md          # question · working-hypothesis (may be empty) · shape · phase · stop-signal state
  sources/<source>.md  # raw layer — one file per source; graded provenance; never overwritten
  synthesis-matrix.md  # MIDDLE LAYER — rows = sources, columns EMERGE from the material (Webster & Watson; grounded-theory coding)
  memos.md             # analytic memos — where the working hypothesis forms and is revised
  <type>.md                 # synthesised output, named by type
  <topic-slug>-brief.md     # single-file, self-contained, cited distillation — the RFC/governance handoff (Decision 7)
  feedback.md               # real-world test (only after phase = feedback)
```

The whole folder is the *working* state and lives in **scratch / out-of-repo** by default (Decision 5). Inner working files stay bare (the folder namespaces the topic), with **one deliberate exception: `<topic-slug>-brief.md`** — it is the only file designed to *leave* the folder, so it must carry the topic to stay unambiguous when it lands next to other briefs or inside an RFC (Decision 7).

Columns are not pre-set (no fixed pillars); they are **constructed as sources are digested** and the matrix is revised as new categories appear. ("Emergent" is the grounded-theory term of art; we follow Braun & Clarke's correction that categories are actively *generated/constructed* by the analyst, not passively *discovered*.) This is the discipline that guards against "forcing data into preconceived categories."

### Decision 4 — soft, revisable hypothesis

`overview.md` carries a `working_hypothesis` that may be empty at `research-project-start`. It is formed and revised in `memos.md` as evidence accumulates (grounded theory's bottom-up path; ACH/ICD-203's "analytic line" — state whether the judgment changed and why). This replaces wiki-kit v1's hard refuse-without-a-claim gate, which is correct only for the hypothesis-first path and wrong for emergent investigations.

### Decision 5 — config-driven layout, scratch by default

**Where a research project lives depends on what the research *is*** — and the default must serve the common case:

- **Research that serves a repo decision** (an RFC/ADR/spec) is *process residue*: a high-volume, fast-staling corpus whose durable value is the distilled conclusion, not the scaffolding. It belongs in **scratch / out-of-repo** — a gitignored `.context/research/` or a user-level path — **never the committed repo tree** (not `docs/`, not the repo root). Committing the corpus bloats every diff and clone, rots in place, and accumulates the collector's-fallacy debris the disciplines warn against. This is the **default**.
- **Research that is a product** (a standing knowledge base, a vault) is durable and lives in its **own repo/vault**, opt-in via config.

So the default parent is a scratch location; pointing it at a durable vault is the deliberate, configured exception. The **default** layout (parent, filenames, schema) ships *inside* the `research-project-start` skill body — the pack's source of truth, projected like every other skill. The **override** is an *adopter-owned* `research-layout.toml` the adopter creates at a known path, read at `research-project-start`. Keeping the override adopter-created — not a file we ship into a projected path — sidesteps the self-host drift gate (CONVENTIONS §projection: projected paths are regenerated and direct edits are bounced). If no override exists, the default scratch parent is used, or **elicited** at start. Exact path + precedence are pinned in the project-mode spec; RFC-0035's `references/sso-config.toml` is the adopter-editable-config precedent.

**The audit-trail caveat.** Because the corpus is scratch (and `.context/` is per-workspace and ephemeral), nothing there survives the workspace. For high-stakes or contested decisions where the *reasoning trail* must be reconstructable later (the `decision-archaeology` case), the corpus is archived to a durable-but-separate home and **linked from `<topic-slug>-brief.md`** — the code repo still commits only the decision, never the corpus.

### Decision 6 — additive provenance grading

Per-source frontmatter in `sources/` gains two optional independent axes — **reliability** (source track-record) and **credibility** (corroboration of the specific claim) — modelled on the Admiralty/NATO scale. These *inform* the existing rail; they do not replace it. The claim-level rail stays GRADE confidence + ≥3-source triangulation. wiki-kit v1's binary Two-Source Rule is folded into triangulation (which already subsumes it), not shipped as a separate weaker rule.

### Decision 7 — the single-file research brief (the governance handoff)

Governance consumes **one file, not a folder.** An RFC's *Evidence & prior art* wants a self-contained, citable distillation it can lift whole — not a `sources/` + `synthesis-matrix.md` + `memos.md` tree full of `[[wikilinks]]` that dangle once detached. So `research-project-synthesize` emits **`<topic-slug>-brief.md`**: the **promotion artifact**, distinct from the typed synthesis (`<type>.md`) which is the project's own internal verdict.

`<topic-slug>-brief.md` is:
- **Answer-first** — BLUF conclusion on top (mirrors the RFC's own format).
- **Self-contained** — every claim it needs is inline; no cross-links to other project files; safe to copy out of the scratch folder.
- **Cited + confidence-tagged** — each load-bearing finding carries its citations and GRADE confidence, and a `## Known unknowns` section — so it maps 1:1 onto an RFC's evidence section.
- **A distillation, not a copy** — it is the matrix/memos/sources *compressed* to the decision-relevant core. This very RFC's durable note, [`0039-notes/survey-managing-research-projects.md`](0039-notes/survey-managing-research-projects.md) — the promoted survey behind this proposal — *is* this format in practice.

The episodic modes already produce this shape — `<topic-slug>-survey.md` is a one-file brief. Decision 7 makes project mode emit the same handoff so the scratch→RFC promotion (Decision 5) has a defined output to carry. **It also establishes that an RFC may carry a `NNNN-notes/` companion** for promoted research, mirroring the `docs/specs/<feature>/notes/` convention (CONVENTIONS §spec layout).

### Design note — existing skills map onto phases, unchanged

The pack has **seven** existing skills; the project phases reuse them rather than rewrite them. Mapping all seven:

| Existing skill | Role in project mode |
|---|---|
| `research` | the per-source episodic retrieval each capture uses under the hood |
| `source-map` | populates `sources/` (curation) during capture |
| `build-outline` | seeds the initial matrix columns at first digest |
| `identify-perspectives` | for contested topics, enumerates camps before/early in capture so the matrix has perspective columns from the start; otherwise stays standalone |
| `compare-hypotheses` | **is** `hypotheses.md` / the ACH matrix when the shape is hypothesis adjudication |
| `devils-advocate` | run at synthesis to drive the `challenged` verdict-status |
| `decision-archaeology` | stays standalone (rationale reconstruction is not a project phase) |

**Principle-2 (substantive, not duplicative) — why four *new* skills, not a flag on existing ones.** Each new skill must add what no existing skill does:
- `research-project-start` — scaffolds project state (folder, `overview.md`, soft hypothesis). No existing skill manages state; clears Principle 2.
- `research-project-digest` — builds the synthesis matrix + memos (the middle layer). This is the capability the pack entirely lacks today; clearly novel.
- `research-project-synthesize` — a **thin orchestrator**: it reuses the existing synthesis + `compare-hypotheses`/`devils-advocate` skills, but adds the project-state dimension (read matrix/memos, emit a *typed* artifact into the layout, mark phase). The novel part is the orchestration + layout, not re-doing synthesis.
- `research-project-check` — the saturation/stop-signal over a *growing corpus*. This is distinct from `devils-advocate` (which attacks a finished claim for counter-evidence); `-check` asks "has the corpus stopped changing the structure" — a corpus-management question no existing skill answers.

Honest concession: `-synthesize` and `-check` are the thinnest of the four. The spec should confirm they earn standalone-skill status over a `project:` flag threaded through existing skills; the case rests on their carrying phase-state transitions, which a stateless flag cannot.

## Options considered

**Axis: how much structure a sustained project gets** — from none to a managed multi-layer corpus. The options below are points on that single axis (increasing structure), which makes them collinear and collectively exhaustive: you either add no structure (do-nothing), one unstructured file, a flat set of files, a managed folder, or you push the structure out to a separate tool.

| Option | Structure level | Prior art | Trade-off |
|---|---|---|---|
| **Do nothing** | none — episodic only; long projects improvised | status quo | zero cost now; but collector's-fallacy / browsing-without-a-claim go unguarded and artifacts collide |
| **One fat file** | minimal — a single growing `research.md` per project | naive note-taking | no new skills; but no raw/synthesis separation — the anti-pattern every discipline rejects |
| **Flat typed files, no folder** | low — `<topic>-sources.md`, `<topic>-matrix.md` side by side, no enclosing project | episodic mode extended | reuses the naming scheme; but no project boundary, no phase/state, growth still untracked |
| **★ Folder + 3 layers + phase skills** | full — the proposal | PRISMA artifact set; Zettelkasten tiers; grounded-theory memos; ACH matrix; wiki-kit v1 | matches the cross-discipline convergence; cost is new skills + a folder convention |
| **Defer to an external tool/vault** | externalised — tell users to run llm-wiki-kit or Obsidian | wiki-kit itself | no pack work; but abandons portability (Principle 1) and the pack's evidence rail (GRADE/triangulation) |

The proposal sits one rung above "flat typed files" because the project boundary, phase-state, and stop-signal — the things a growing corpus needs — require an enclosing folder + `overview.md` to live in; flat files give the naming win but not the lifecycle. Do-nothing's cost of delay: the pack remains unable to support its highest-value use case (multi-source decisions), and every long investigation re-improvises structure.

**Sub-axis: middle-layer columns (fixed vs emergent).** Fixed pillars (wiki-kit v1) are fast and opinionated but procrustean — they assume every topic decomposes into entities/attributes/mental-model/verdict, which causal and prior-art questions do not. Emergent columns (Webster & Watson concept matrix; grounded-theory coding) fit the material at the cost of less up-front structure. Chosen: emergent (decision 3).

## Risks & what would make this wrong

**Pre-mortem.**
- *The middle layer goes unused* — agents skip `digest` and jump to synthesis, recreating the one-hop problem. *Mitigation:* `research-project-synthesize` reads the matrix/memos as inputs; an empty matrix surfaces a warning.
- *Project mode is too heavy for small jobs* — users invoke it when episodic would do. *Mitigation:* the depth axis stays the default front door; project mode triggers only on explicit "start a research project" phrasing.
- *Config-driven layout fragments adopters* — every vault invents a layout, breaking portability. *Mitigation:* ship one strong default; config is an override, not a requirement.
- *Topic-prefixed names collide or get unwieldy* — long slugs, or two artifacts on one topic. *Mitigation:* `<topic>-<type>` disambiguates by type; project folders namespace by date+slug.

**Key assumptions (falsifiable).**
- *A sustained project can be a skill discipline, not infrastructure* — falsified if it needs a runtime engine/index to be usable (see De-risk; prior art says no).
- *Emergent columns beat fixed pillars in practice* — falsified if agents produce incoherent matrices without a fixed scaffold (the survey flags this as the #1 thing to validate empirically).
- *The middle layer earns its keep* — falsified if digest adds ceremony without making synthesis better on real projects.

**Drawbacks.** Four new skills enlarge the pack's surface (against the catalogue's bias toward few, sharp primitives). A folder convention is more to learn than a single file. Emergent columns ask more judgment of the agent than a fixed template. These are real costs accepted for the capability.

## Evidence & prior art

**Spike / de-risk result.** *Riskiest assumption:* that a stateful project + emergent middle layer is a skill discipline, not runtime infra — otherwise it fails Charter Principle 3 ("a habit, not infrastructure"). *Result: confirmed by prior art.* llm-wiki-kit v1's four phase skills (`research-start`/`-sieve`/`-synthesize`/`-verdict-check`, read at commit `98bfef5`) implement the entire lifecycle as pure prompt-driven file reads/writes — `research-sieve` reads `sources/*.md` and writes pillar pages with **no code engine**; the agent following the skill is the executor. The folder is an artifact convention like our own spec/plan loop, not a service. The one place this design goes past wiki-kit is the `phase:` field and the `-check` stop-signal — but both stay prompt-only: `phase` is a frontmatter string the agent reads/writes, and `-check` is the agent reading the matrix by eye (no counter, no derived metric — see its description), so neither introduces an engine. The config-driven layout (decision 5) keeps Charter Principle 1 (universal) satisfied. No further spike needed.

**Repo precedent.**
- `packs/research/pack.toml` (v0.2.0) — the pack this extends; a version bump is required. Methodology already grounds on STORM/PRISMA/ACH/GRADE, so the disciplines cited here are in-family.
- RFC-0035 — adopter-editable `references/sso-config.toml` precedent for decision 5.
- RFC-0034 — `profiles/<name>.toml` config-file-at-known-path precedent.
- RFC-0038 — forward-only migration + legacy-retention pattern for decision 2's alias.
- `compare-hypotheses` skill — already an ACH evidence matrix; `hypotheses.md` is this skill, not a new artifact.

**External prior art.** Full verified survey, promoted to this RFC's durable note [`0039-notes/survey-managing-research-projects.md`](0039-notes/survey-managing-research-projects.md) (citations fetched and confirmed by four `evidence-retriever` subagents). The load-bearing finding: a three-layer split (raw → working/digest → synthesis) with distinct named artifacts is **convergent across four independent disciplines** —
- *Systematic review* (PRISMA 2020, [PMC8007028](https://pmc.ncbi.nlm.nih.gov/articles/PMC8007028/); Cochrane Handbook): protocol → search log → extraction table → **synthesis matrix** → review. Webster & Watson (2002) concept matrix (rows=sources, columns=concepts) grounds emergent columns.
- *PKM* (Zettelkasten fleeting/literature/permanent tiers; [zettelkasten.de Collector's Fallacy](https://zettelkasten.de/posts/collectors-fallacy/)): names the browsing-without-synthesis failure mode the project mode guards.
- *Qualitative research* (grounded theory; Braun & Clarke 2022, [PMC9879167](https://pmc.ncbi.nlm.nih.gov/articles/PMC9879167/)): the emergent-coding + analytic-memo layer, theoretical saturation as the stop signal, and the "forcing data into preconceived categories" anti-pattern that motivates emergent over fixed columns.
- *Intelligence analysis* (Heuer, ACH; NATO AJP-2.1 Admiralty code): the evidence×hypothesis matrix, refutation logic, and the two-axis source grading behind decision 6.

The direct tooling prior art is **llm-wiki-kit v1** itself (`98bfef5`): this RFC adapts its folder + phase model, replacing fixed pillars with emergent columns and the hard hypothesis gate with a soft, revisable one.

**Commercial-tool prior art — Perplexity.** The same three-layer shape is productised at mass-market scale by Perplexity, which both validates the design's endpoints and sharpens where ours differs:

| Perplexity feature | Maps to | What it confirms |
|---|---|---|
| **Spaces** — topic-scoped containers holding many threads, a per-Space custom prompt, and a **file knowledge base** (50 files/Space on Pro, referenced across threads without re-upload) | the **project folder** + `sources/` + `overview.md`'s instructions/hypothesis | a persistent, topic-scoped container that accumulates sources is a recognised pattern, not a novelty |
| **Focus modes** (Web / Academic / Social / Video / Math / Writing — source-set scoping) + iterative **threads** + **Deep Research** (multi-pass, Feb 2025) | the **depth × discipline axis** (our `applied`≈grey-lit, `standard`≈Academic) + the capture loop + `deep` mode | scoping search by *discipline* and iterating in a topic thread is the established research-loop shape |
| **Pages / "Convert to Page"** — turn a raw research thread into a structured, sectioned, cited report | the **synthesize step** → a typed artifact | the raw-capture → structured-synthesis boundary is worth productising as an explicit action |

The **gaps** in Perplexity sharpen our differentiation: it goes thread → Page in one hop with **no middle/digest layer and no tracked working hypothesis** (the same one-hop gap this RFC closes); its Pages are **public-only, non-exportable**, and the conversion **does not even draw on the Space's knowledge base** — whereas our synthesis is a local, private, exportable Markdown artifact that reads the actual `sources/` + matrix. Citations: [Pages launch, TechCrunch 2024-05-30](https://techcrunch.com/2024/05/30/perplexity-ais-new-feature-will-turn-your-searches-into-sharable-pages/) (verified); [Spaces / per-Space prompts, TestingCatalog](https://www.testingcatalog.com/perplexity-redefines-collections-with-spaces-allowing-default-model-settings/) (verified — note file-KB was "planned" at that Oct-2024 date); [Space file knowledge base + 50-file limit, DataStudios 2025](https://www.datastudios.org/post/perplexity-ai-file-upload-support-limits-formats-and-usage-in-2025) (verified). Perplexity's own help-center pages could not be fetched directly (perplexity.ai blocks automated retrieval), so the above rests on fetchable secondary coverage.

## Experiment / validation

The emergent-vs-fixed-columns choice (Decision 3) is **decided** — ship emergent — but is the one design call without empirical backing yet. This validates the decision post-ship; it does not reopen it.

- **Hypothesis:** agents produce coherent, useful synthesis matrices with constructed (emergent) columns and do not need a fixed-pillar scaffold to stay coherent.
- **What we measure:** across the first 2–3 real projects run through project mode, whether `synthesis-matrix.md` columns stay coherent and whether digest needs human column-seeding to be usable.
- **Success / failure:** success = matrices usable without falling back to fixed pillars; failure (→ revisit Decision 3 via a superseding ADR) = agents need a fixed scaffold for coherence. Results in a linked spike note, not pasted here.

## Open questions

1. **Should `research-project-check` ever lightly write `verdict_status` into `overview.md`** (a small state write) or stay purely conversational? Recommended default: allow the light status write, never a phase advance. · owner: eugenelim · decide-by: project-mode spec.

## Follow-on artifacts

Filled in on acceptance. Anticipated:
- **ADR**: record the two-axis (depth × lifecycle) model and the emergent-column-over-fixed-pillar choice.
- **Spec**: `docs/specs/research-typed-artifacts/` — episodic rename-by-type + legacy alias (smaller, lands first).
- **Spec**: `docs/specs/research-project-mode/` — the 4-skill family, folder layout, middle layer, scratch-default config-driven layout (Decision 5), the `<topic-slug>-brief.md` handoff format (Decision 7), additive provenance grading.
- **Pack bump**: `packs/research` minor version; `docs/product/changelog.md` `[Unreleased]` entry.
