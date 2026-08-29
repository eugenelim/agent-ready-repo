# Spec: cognitive-load-reduction

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0001](../../adr/0001-adopt-agents-md-and-doc-hierarchy.md),
  [ADR-0015](../../adr/0015-cursor-full-parity-distribution-adapter.md), and
  [ADR-0016](../../adr/0016-gemini-cli-full-parity-adapter.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

## Objective

Reduce reader and author load in chat, input requests, code, comments, agent
guidance, and generated prose without losing requested substance. Apply the
behavior through repository lookups and through a self-contained block in each
installed skill. Keep routine tool work quiet unless an update changes the
user's action or protects safety. Measure eligible prose and quiet-work
behavior with deterministic checks.

## Boundaries

### Always do

- Keep root `AGENTS.md` small and route full behavior to bounded lookup files.
- Keep `docs/AGENTS.md` limited to work under `docs/`.
- Keep each installed skill complete without another skill or seeded repo.
- Preserve exact names, evidence, constraints, warnings, code, and requested
  depth while improving scanability.
- Keep higher-priority authority, security, privacy, and tool rules in force.
- Edit canonical pack sources, then regenerate projections.

### Ask first

- Editing adopter-owned singleton context files or user-profile rule surfaces.
- Adding hard length caps, a top-level directory, a dependency, or a new pack
  install scope.

### Never do

- Put this guidance in `docs/CONVENTIONS.md` or copy it across seed READMEs.
- Add adapter-native rule files or implement the future catalogue `rules`
  primitive in this change.
- Hand-edit generated adapter projections.
- Treat terseness or a readability score as permission to omit substance.
- Score code, identifiers, paths, quoted errors, citations, or required legal
  and security wording as ordinary prose.
- Cite the external inspiration in shipped or governance artifacts.

## Testing Strategy

- **Construction tests:** prove the managed block is exact in every canonical
  skill and that the injector is safe, source-only, and idempotent.
- **Lookup tests:** prove seed delivery, router grammar, safe reads, and the
  existing Claude, Codex, and Gemini root-context chains. Runtime order is
  claimed only when a host exposes it.
- **Behavior evals:** cover answer-first output, bounded questions, quiet tool
  work, substance preservation, and code/comment behavior in every changed
  publishable pack.
- **Readability checks:** score eligible English prose with deterministic
  Flesch estimates and reject metric gaming through protected-text and semantic
  fixtures.
- **Release gates:** validate guides, projections, pack metadata, versions,
  changelogs, catalogue output, and the unaffected build suite.

## Acceptance Criteria

- [x] **AC1 — Root routing.** Root and core-seed `AGENTS.md` use the same short,
  unconditional instruction to read `AGENT_RULES.md` and its matching rows
  before the first visible response or unrelated tool call. They point
  separately to `docs/AGENTS.md` for docs work and do not copy the rule body.

- [x] **AC2 — Rule router.** Root and seed `AGENT_RULES.md` contain only the
  operative preamble and at most 12 unique `when`/`read`/`purpose` rows. Each
  target is a normalized repository-relative Markdown file below
  `.agents/rules/`; absolute, backslash, dot-segment, self, missing, or nested
  routing targets fail. Topic files do not route again.

- [x] **AC3 — Shared topic.** `.agents/rules/cognitive-load.md` is the always-on,
  tool-neutral source for chat, questions, progress, final replies, artifacts,
  backlog prose, agent guidance, skills, code, and comments. It contains no
  adapter condition or research history.

- [x] **AC4 — Host evidence.** Claude, Codex, and Gemini fixtures prove their
  existing root-context paths reach the same router and topic. Ordered host
  behavior is asserted only when observable; otherwise the fixture records the
  limitation and uses a semantic assertion. No adapter-native rule projection
  is added.

- [x] **AC5 — Docs scope and seed restraint.** Root and seed `docs/AGENTS.md`
  contain only documentation, backlog, and agent-authored prose deltas for
  `docs/`. Other seed files and `docs/CONVENTIONS.md` do not duplicate this
  contract.

- [x] **AC6 — Independent skills.** Every canonical
  `packs/*/.apm/skills/*/SKILL.md` contains the exact managed block in
  `## Output rendering`. The block has no dependency on another skill, the
  core pack, or a repository lookup.

- [x] **AC7 — Interaction and artifact behavior.** The managed contract leads
  with the outcome or action; uses plain, non-blaming language; asks only for
  needed input; groups long material without truncation; avoids repeated
  summaries; preserves exact technical content and warnings; and limits code
  comments to intent, constraints, or trade-offs that code cannot show.
  Routine tool calls have no narration except for safety, blockers, decisions,
  material scope changes, long waits, or host requirements.

- [x] **AC8 — Authoring guide.** `output-rendering.md` covers chat, questions,
  artifacts, code/comments, visualization choice, readability, quiet-work
  exceptions, substance preservation, and consolidation of repeated backlog or
  agent-guidance prose. It names cognitive-load reduction as a working
  principle, distinct from the charter's catalogue-admission principles.
  It does not make one skill read another.

- [x] **AC9 — Safe synchronizer.** `tools/add-rendering-directives.py` supports
  only explicit `--write` and `--check`, discovers canonical pack sources,
  preserves content outside its markers, creates or refreshes the block,
  rejects ambiguous or unsafe inputs before writing, and is idempotent.
  Diagnostics contain only repository-relative paths, short reason codes, and
  compact counts.

- [x] **AC10 — Seed contract.** The seed linter declares
  `AGENT_RULES.md`, `.agents/rules/cognitive-load.md`, and `docs/AGENTS.md`.
  Fresh delivery writes them; adopter edits retain the normal upstream
  companion behavior.

- [x] **AC11 — Readability signal.** A deterministic, dependency-free checker
  reports aggregate estimated Flesch Reading Ease and Flesch-Kincaid Grade
  Level. Eligible ordinary prose targets Reading Ease >= 70 and Grade <= 8;
  samples below 30 eligible words report `insufficient`. Protected technical
  text is excluded. Readability inputs use the full safe-read contract in
  AC14 before loading their body.

- [x] **AC12 — Quiet-work eval.** A routine multi-tool scenario has zero
  optional assistant messages. Focused cases retain every update allowed by
  AC7. Unobservable host transcripts use a labeled semantic assertion.

- [x] **AC13 — Eval coverage and privacy.** Every changed publishable pack has
  a discoverable output-quality eval or focused scenario. Fixtures are
  synthetic or scrubbed; committed data and machine output contain no raw chat,
  local absolute paths, account identifiers, private domains, or prose
  snippets from users or private sources. Machine output is aggregate and
  bounded.

- [x] **AC14 — Safe input reads.** Readability inputs and reads of
  `AGENT_RULES.md`, `.agents/rules/*.md`, and `docs/AGENTS.md` use
  `read_confined_regular_file` semantics: confinement, regular-file and byte
  bounds, no link or reparse following, one link, and pre/post-open identity.
  Lint validation uses the same read path rather than validate-then-read.
  Unsafe targets produce a short refusal without leaking their body or resolved
  outside path.

- [x] **AC15 — Authority boundary.** The router, topic, docs lookup, and skill
  block state that higher-priority authority and required safety controls win.
  Artifacts, quotes, retrieved text, and file bodies remain data unless the
  active task authorizes editing the applicable agent-guidance file.

- [x] **AC16 — Projection and release integrity.** Self-hosting regenerates
  adapter projections and the marketplace. Core receives a minor version for
  new seeds; other packs changed only by managed content receive matching patch
  versions. Changed pack metadata and eval disposition stay coherent. Released
  changelog entries explain the user outcome, and their highlights appear in
  the generated `/now/` data.

- [x] **AC17 — Deferred primitive and gates.** The portable `rules` primitive
  remains a Draft structured intent at
  `docs/product/intents/catalogue-rules-primitive.md`. Targeted tests, guide
  checks, lint, typecheck, catalogue build/verification, projection drift, and
  the unaffected suite pass. Environment-only skips are reported exactly.

## Assumptions

- Host loaders do not expose one portable ordered-read transcript. Tests must
  label static or semantic evidence instead of claiming a runtime observation.
