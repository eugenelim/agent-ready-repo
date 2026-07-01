# Spec: research-methodology-shape

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0057, RFC-0039, ADR-0029
- **Brief:** none
- **Discovery:** none
- **Contract:** none — prompt-only shape; no API surface, no `contracts/` file

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Acceptance gate — cleared.** RFC-0057 is **Accepted** (2026-06-30). This
> spec is Approved: the design is ratified and the implementing PR (skill edits,
> the six-section template, reciprocal fencing, the README nudge, the pack bump)
> may proceed.

## Objective

A user asking *"what's the best way to do X, end to end, for my situation"* — run
a data-migration workbench, progress a training plan, bring AI-SDLC
modernization to a delivery stream, train this dog breed — gets a **`methodology`
output shape** from the `research` pack: a staged, contingency-adapted,
maturity-aware, evidence-graded description of how the activity is done, not a
claim-organized survey they must re-shape by hand into a sequence. Success is:
the pack routes process-shaped questions to a `methodology` artifact on **both**
its surfaces — one-shot (episodic `/research`) and sustained (project mode) — the
artifact is slide-ready for `markdown-to-pptx` with no reshaping, and it is
fenced cleanly against the two neighbouring "process" skills (`frame-domain`,
`map-internal-process`). The change is **prompt-only** (Charter Principle 3):
no code, no new dependency, no runtime engine. It also closes the standing
research-pack TODO — the retrieval subagents' web-tool permission nudge — folded
in as the next research-pack touch.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Add the shape as a **row/value in the existing vocabularies**, following the
  precedent of the shapes already present (`comparison-matrix`, `shortlist`,
  `blueprint`, `hypotheses`) — filename and structure produced by the agent
  following the skill, never by a script.
- Keep the artifact **authored for `markdown-to-pptx`**: sections at `H1`,
  stages at `H2`, all finer detail as bullet lists.
- Distinguish the **two field names by surface**: the episodic side gains a
  `<type>` stem (`methodology`); the project side gains a `shape:` frontmatter
  value (`methodology`). These are distinct fields — do not invent a new
  `shape`-named episodic field.
- Name the **honest overlap** with `map-internal-process` (SIPOC scope frame +
  process-discovery spine are shared) and rest the boundary on source+direction
  plus the three non-shared disciplines.
- Bump `packs/research` (minor) in **both** `pack.toml` and
  `.claude-plugin/plugin.json`, and add a `[Unreleased]` changelog entry.

### Ask first

- Any change to the **depth axis** (quick/standard/applied/deep) — this spec
  extends the shape/type set only and reverses nothing in RFC-0039/ADR-0029.
- Graduating `methodology` to its own standalone skill or skill-family
  (RFC-0057 Open Question 2 — decided **no for v1**; revisit is post-ship).
- Authoring the follow-on **ADR** (that shapes/types are the extension point for
  new output topologies) — anticipated but out of this spec's scope.

### Never do

- **No runtime engine, index, daemon, or counter** — the shape is prompt-only,
  exactly like every existing shape.
- **No hard dependency** from `research` on `converters` — `markdown-to-pptx` is
  named as a consumer by reference only; a repo without the converters pack
  still gets the artifact.
- **No `H3` for sub-steps** in the artifact — `markdown-to-pptx` maps only
  `H1`/`H2` to slides and renders the literal `###` text into the parent slide
  body; sub-steps are always bullets.
- **No agentbundle-managed permission grants** — the web-tools fix is an
  install/adapt-time *note*, not projector machinery (`permissions.allow` is a
  shared, user-co-authored key the bundle cannot own).
- **No migration** — the change is purely additive; no existing artifact is
  renamed and no consumer changes.

## Testing Strategy

The implementation is **prompt/docs-only** (skill bodies, a reference template,
the README, pack metadata, the changelog). Verification is therefore
**goal-based** for the structural facts and **manual/dogfood** for the shape's
distinctness:

- **Goal-based check** (the ship gate for the implementing PR): each vocabulary
  edit, the new reference file, the reciprocal disambiguation edits, the version
  bump, and the changelog entry are verified by `grep`/file-existence one-liners,
  plus the pack gate `lint-packs` + `validate` + `build` + `pytest`
  (`packs/research` is a user-scope-default pack, not in this repo's self-host
  projection — see plan Constraints).
- **Manual QA / dogfood** (post-ship validation, **not** a gate for the
  implementing PR): RFC-0057's predeclared experiment — run the shape on 2–3
  real topics and confirm each artifact carries §3 contingency and §4 maturity
  content a same-topic `applied` survey lacks. This validates the riskiest
  assumption after ship; it does not reopen the decision to build the shape.

No TDD-mode tasks: there is no compressible code invariant — the shape is prose
the agent produces by following the skill.

## Acceptance Criteria

<!-- All open at authoring time; the implementing PR checks them. -->

**Verification mode per criterion:** every AC below (D1–D6, Open Question 1,
Web-tools nudge, Ship mechanics) is **goal-based** — checked by the `grep` /
file-existence one-liner named in the matching plan task, plus the pack gate. The
sole **manual/dogfood** check is RFC-0057's shape-distinctness experiment, which
is **post-ship validation, not an AC** (see Testing Strategy).

### D1 — the episodic `methodology` shape

- [ ] `packs/research/.apm/skills/research/SKILL.md` "Type vocabulary" table
  gains a `process / methodology / lifecycle` row mapping to
  `<topic-slug>-methodology.md`.
- [ ] The `research` skill body documents the shape's trigger phrasing — *"the
  best way to do / run / build / train X"*, *"the process / lifecycle / playbook
  for X"*, *"how do you go about X end to end"*.
- [ ] The filename is produced by the agent following the skill — no script, no
  code added (Charter Principle 3): a `grep` shows no new executable added to the
  research pack for this shape.

### D2 — the six-section artifact template

- [ ] A new reference
  `packs/research/.apm/skills/research/references/methodology-shape-template.md`
  exists, encoding the six sections, each grounded 1:1 in its discipline: §1
  Scope frame (SIPOC) · §2 Stage spine (process discovery + hierarchical task
  decomposition) · §3 Contingency branches (situational method engineering) · §4
  Maturity ladder (Dreyfus) · §5 Failure modes (cognitive task analysis) · §6
  Evidence & confidence (GRADE, inherited unchanged).
- [ ] The template is authored heading-per-section (`H1`) and heading-per-stage
  (`H2`), with sub-steps as bullet lists and **no `H3`**.
- [ ] §3 (contingency) and §4 (maturity) are marked **mandatory** with worked
  exemplars; the template states a methodology artifact missing them is a survey
  with headings and is flagged incomplete.
- [ ] The template carries at least one **worked exemplar** of the full
  six-section artifact.
- [ ] The template is named distinctly from the existing
  `references/methodologies.md` (which catalogues the pack's *research-method*
  disciplines and is **not** edited), and the `research` skill body points at the
  new template.

### D3 — defaults to `applied` depth

- [ ] The methodology shape defaults to **`applied`** depth, and the skill body
  states scholarly domains override to `standard`/`deep` via the ordinary depth
  cues.
- [ ] The shape **does not touch the depth-cue vocabulary or the mode
  machinery** — a diff confirms the `research` skill's Modes / Cue-precedence
  blocks and the closed cue tuples in
  `test_research_retrievers_conformance.py` are unchanged (RFC-0039/ADR-0029
  two-axis invariant).

### D4 — fenced against the two neighbours

- [ ] The methodology shape's trigger prose carries explicit **"do NOT use"**
  pointers to `frame-domain` (product/MVP grounding) and `map-internal-process`
  (an org's own operations).
- [ ] Reciprocal disambiguation lines are added to the `frame-domain` and
  `map-internal-process` skills pointing back to the methodology shape.
- [ ] The boundary is documented as resting on **source + direction**
  (world best-practice, outside-in, any domain vs *your own* operations,
  inside-out) plus the three non-shared disciplines (contingency §3, maturity §4,
  failure-modes §5); the honest SIPOC + process-discovery overlap with
  `map-internal-process` is named, not hidden.
- [ ] The **`frame-domain`-wraps-`research` interaction** is fenced: because
  `frame-domain` internally invokes `research` in `applied` mode to ground its
  real-world-activity half, the methodology shape **does not fire on that wrapped
  call** — the wrapped invocation stays an `applied` survey. The methodology
  shape's trigger prose and the `frame-domain` reciprocal pointer both state this,
  so `frame-domain`'s grounding pass is never silently reshaped into a
  methodology artifact.

### D5 — structure-only PowerPoint handoff

- [ ] The methodology skill body names `markdown-to-pptx` as the natural slide
  consumer **by reference only** — no import, no `requires`, no version pin;
  `research` gains no dependency on `converters`.
- [ ] The artifact structure keeps sections at `H1` and stages at `H2` with
  finer detail as bullets, so the handoff is a one-prompt operation.

### D6 — both surfaces

- [ ] `packs/research/.apm/skills/research-project-start/SKILL.md` gains
  `methodology` in **both** the `shape:` frontmatter vocabulary and the
  `overview.md` schema comment that documents it (today both read
  `survey | comparison | decision | structural | adjudication`) — the two must
  not drift.
- [ ] `packs/research/.apm/skills/research-project-synthesize/SKILL.md` gains a
  branch: a `methodology` shape writes `methodology.md` (bare-named inside the
  project folder, per the existing convention) alongside the `<topic-slug>-brief.md`
  governance handoff.
- [ ] The change is purely additive: no existing artifact is renamed, no existing
  consumer changes (**migration: none**).

### Open Question 1 — maturity ladder for one-off deliverables

- [ ] The template resolves RFC-0057 Open Question 1 with **reframe, never omit
  silently**: when skill-progression does not apply (a one-off deliverable), §4
  is authored as an adoption/capability-maturity axis (crawl → walk → run of the
  deliverable) so the "journey" section/slide always exists.

### Web-tools install nudge (folded-in TODO)

> This concern is folded into this spec at the **operator's explicit request**
> (it is the standing "next research-pack touch" the TODO waited for). It rides
> along under the same pack; the implementing PR lists it under `Bundled fixes:`
> with a one-line reason. It is distinct from the methodology shape (different
> subagents, `README.md` vs skill bodies).

- [ ] The research pack's `README.md` carries a one-line note that names
  **`WebSearch`** and **`WebFetch`**, the two retrieval subagents
  (`evidence-retriever`, `source-extractor`), and **Claude Code** as the scope,
  telling adopters to grant those two tools before the subagents can do live web
  retrieval. The note is guidance only — no projector, no permission-grant
  machinery, no edit to `permissions.allow`. *(This AC checks the note's content;
  the correctness of the Claude-Code-only scoping rests on the adapter finding
  captured in [`notes/adapter-web-tools-scope.md`](notes/adapter-web-tools-scope.md)
  and recorded in Assumptions.)*

### Ship mechanics

- [ ] `packs/research` version is bumped **minor** (`0.5.1` → `0.6.0`) in **both**
  `pack.toml` and `.claude-plugin/plugin.json`.
- [ ] `docs/product/changelog.md` `[Unreleased]` carries an entry describing the
  new methodology shape (user-visible skill capability).
- [ ] The version bump's drift into top-level `marketplace.json` is reconciled,
  and the pack gate is green — `lint-packs` + `validate` + `build` + `pytest`
  pass and `build-check` is clean.

## Assumptions

<!-- Audit trail for the assumption-surfacing checkpoint at spec time. -->

- Technical: `methodology` is a **shape** (output topology), not a **depth
  "mode"**; it extends RFC-0039/ADR-0029's two-axis model and reverses nothing.
  (source: RFC-0057 D1; ADR-0029)
- Technical: the episodic `<type>` stem and the project `shape:` value are
  **distinct fields**; there is no `shape`-named episodic field today. (source:
  RFC-0057 §D1 terminology note; `research/SKILL.md` § Typed, topic-named
  artifacts + `research-project-start/SKILL.md` `overview.md` schema, read
  2026-06-30)
- Technical: `markdown-to-pptx` maps `H1`/`H2` → one slide, list items → bullets,
  a table → a slide table, and renders a literal `###` into the parent slide
  body — so sub-steps must be bullets, never `H3`. (source:
  `packs/converters/.apm/skills/markdown-to-pptx/SKILL.md`, read 2026-06-30)
- Technical: no test pins the project `shape:` vocabulary or the episodic `<type>`
  set; the conformance test
  (`packages/agentbundle/tests/unit/test_research_retrievers_conformance.py`)
  single-sources only the *mode* cue tuples, which this shape does not touch.
  (source: repo grep, 2026-06-30)
- Process: `packs/research` is a **user-scope-default pack not in this repo's
  self-host projection**; the pack gate is `lint-packs` + `validate` + `build` +
  `pytest`, and a version bump also drifts top-level `marketplace.json` (all-packs
  aggregation from `plugin.json`), which the implementing PR must reconcile.
  (source: project memory — self-host pack scope + non-projected pack bump; to be
  re-confirmed by the implementer against the local build)
- Product: the web-tools permission gap is **Claude-Code-specific**. A parallel
  adapter investigation confirmed that only Claude Code gates the retrieval
  subagents' `WebFetch`/`WebSearch` behind an allow-list a non-interactive
  subagent cannot satisfy; Copilot resolves both to its built-in `web` tool,
  and Cursor / Gemini / Codex / Kiro preserve or name-map the tools at build
  time with no install-time allow-list step. So the README nudge is scoped to
  Claude Code, and the fix is a guidance-note, not bundle-managed grants.
  (source: project memory — research-pack web-tools install nudge + subagent
  web-tools finding; adapter investigation 2026-06-30, evidence in the plan's
  T5 + Changelog)
- Product: RFC-0057 Open Question 1 is resolved at spec time per its recommended
  default (reframe, never omit); Open Question 2 (graduate to a skill) stays a
  post-ship review, out of scope here. (source: RFC-0057 Open questions)
