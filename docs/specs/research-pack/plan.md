# Plan: research-pack

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this document is allowed to change as you learn. When it changes substantially (a different approach, not just a re-ordering), note why in the changelog at the bottom.

## Approach

Build the pack in one PR, mirroring the `converters-pack` precedent. Two-phase shape: scaffolding (pack.toml, plugin.json, directory structure) lands first; then each of the seven skills as its own task with construction tests for body shape, frontmatter compliance, and methodology references; then the two subagents; then the retriever convention with flat-layout examples; then the methodology and confidence-schema references; finally the integration test. The riskiest tasks are `/research` (the mode dispatcher is the broadest behavior surface and carries the description-match heuristic AC11 depends on) and the retriever convention (the contract must be thin enough to not invent infrastructure but thick enough that a user can actually plug a retriever in).

Construction tests for skill bodies are mostly grep-and-lint shaped — they verify that methodology is *documented*, not that it *runs*. Behavioral verification of `/research` modes (AC11–AC16) and the depth-via-prompt cue pattern on the other six skills (AC21) lives in manual QA and grep-checks because description-match heuristics are only observable in invocation.

The flat directory layout (no nested subdirectories under `references/`; one level under `scripts/`) is non-negotiable per the agentskills.io spec recommendation and the convergent in-pack precedent. Construction tests verify the layout.

## Constraints

- [RFC-0004](../../rfc/0004-install-scope-per-pack.md) — user-scope dimension; pack must pass all three user-scope refusal rails (seeds, hooks, markers).
- [RFC-0011](../../rfc/0011-pack-allowed-adapters.md) — per-pack `allowed-adapters` declaration; `["claude-code", "kiro", "codex"]` matches the user-scope-pack precedent.
- [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md) — install-scope precedence (CLI flag > pack `default-scope` > built-in `repo`).
- `docs/CONVENTIONS.md § Model selection` — every subagent declares `model:` explicitly; `lint-agent-artifacts.py` enforces.
- agentskills.io specification — one-level-deep file references; `references/` flat; `scripts/` nesting permitted but unused here.
- The seven convergent methodologies (STORM, PRISMA, ACH, Wikipedia V/RS/NPOV, OSINT, GIJN, GRADE) — informing skill bodies, documented in `references/methodologies.md`. Not constraints; auditable rationale.
- Compatible-with-not-constrained-by: [RFC-0006](../../rfc/0006-skill-secrets-storage.md) (shipped) for the env-broker shape used by `perplexity-retriever.py`; forward-compatible with [RFC-0013](../../rfc/0013-credential-broker-contract.md) (Draft).

## Construction tests

Most construction tests live under per-task `Tests:` subsections below. Cross-cutting:

- **Integration test (AC10, T12).** `packages/agentbundle/tests/integration/test_install_research_user_scope.py` — fixture-`$HOME` install/uninstall state machine; spans every projected primitive.
- **Layout test (AC8).** `find packs/research/.apm/skills/*/references packs/research/.apm/skills/*/scripts -mindepth 2 -type d` returns zero results; runs in CI alongside the existing scrub / Rail C greps.
- **Manual verification matrix (AC11–AC16, AC21).** A small recorded session per mode + pipeline, exercising:
  - Casual prompt → `quick` mode → inline answer, no artifact.
  - Explicit "with citations" prompt → `standard` mode → `research.md` with GRADE.
  - Explicit "go deep" prompt → `deep` mode → `research.md` + `counterpoints.md`.
  - Sequential decision-pipeline invocation → four artifacts.
  - Archaeology-shaped prompt → `archaeology.md`.
  - Depth cue ("comprehensively") on a non-`/research` skill → behavior shift confirmed.

## Tasks

### T1: Pack scaffolding

**Depends on:** none

**Tests:**
- `agentbundle validate packs/research/` exits zero (AC1, AC2, AC6).
- File-presence: `pack.toml`, `.claude-plugin/plugin.json`, `.apm/skills/`, `.apm/agents/`.
- `rg --hidden '<adapt:>' packs/research/` exits non-zero (zero hits — AC6).
- Content-portability grep returns zero against the scaffold (AC5).

**Approach:**
- Mode: goal-based check.
- Create `packs/research/pack.toml` with the AC1 declarations.
- Create `packs/research/.claude-plugin/plugin.json` with name/version/description.
- Create empty `packs/research/.apm/skills/` and `packs/research/.apm/agents/` directories (placeholder `.gitkeep` if needed).

**Done when:** `agentbundle validate packs/research/` exits zero against the scaffold-only pack.

### T2: `/research` skill body with mode dispatcher

**Depends on:** T1

> Note: T2 originally specified the three-mode parameter `quick | standard | deep`. The same-day applied-mode amendment (see T19 below and the spec's `2026-05-28 post-clean amendment` changelog entry) supersedes that — the canonical mode parameter is `quick | standard | applied | deep`. T19 amends what T2 produced; on a fresh end-to-end re-run, treat T2's three-mode tests and approach as superseded by T19.

**Tests:**
- SKILL.md frontmatter has top-level `name = "research"` and `description` matching both casual and deep cues per AC11.
- Body documents `mode: quick | standard | deep` with `quick` as default.
- Body documents the retriever enumeration step (AC7); the Retrievers section's interface description is documented INLINE (literally names the three JSON keys and three shape values per AC7's pinned greps). T10 lands the actual `scripts/*-retriever.py` files and adds a cross-link to them inside this section as part of its scope.
- Body documents the moderator unused-snippet pass (AC19).
- Body documents the citation-forcing rule (AC18).
- Body has a section titled `Retrievers` (AC7 grep) containing a code-fenced JSON-shape block with the three keys as quoted JSON strings (`"content"`, `"citations"`, `"shape"`) and the three enum values as quoted strings (`"raw"`, `"synthesized"`, `"meta"`). Verified by six separate `rg -F` invocations per AC7 — one per quoted token, since `-F` accepts only one pattern per call.
- `lint-agent-artifacts.py packs/research/.apm/skills/research/` returns zero.
- Content-portability grep against this file returns zero.

**Approach:**
- Mode: goal-based check (TDD-like for the grep-driven gates).
- Author `packs/research/.apm/skills/research/SKILL.md`.
- Top-level frontmatter: `name`, `description` (write the description to bias `quick` on casual phrasings and `standard`/`deep` on explicit ones — AC11 success criterion).
- Body sections: When to invoke, Modes (quick / standard / deep, with the cap on quick), Methodology, Retrievers (the extension convention; references the three surfaces and the script-retriever interface), Citations and confidence, Moderator pass.

**Done when:** All listed greps return their expected counts and lint is clean.

### T3: `/source-map` skill

**Depends on:** T1

**Tests:**
- SKILL.md frontmatter compliant.
- Body documents STORM perspective-discovery methodology ("don't ask the LM directly who's authoritative").
- Body documents the source taxonomy (authority type + recency + primacy).
- Body documents the `sources.md` output schema.
- Body documents depth-via-prompt cues (AC21).
- Lint clean; content-portability grep clean.

**Approach:**
- Mode: goal-based check.
- Author `packs/research/.apm/skills/source-map/SKILL.md`.
- Methodology section names the STORM finding by reference; primacy taxonomy enumerated; depth-cue section documents adopter language for lighter/heavier behavior.

**Done when:** All greps return their expected counts and lint is clean.

### T4: `/identify-perspectives` skill

**Depends on:** T1

**Tests:**
- SKILL.md frontmatter compliant.
- Body documents perspective-enumeration methodology (cites Wikipedia NPOV + ACH competing-hypotheses).
- Body documents the `perspectives.md` output schema (named camps + representative voices).
- Body documents depth-via-prompt cues (AC21).
- Lint clean; content-portability grep clean.

**Approach:**
- Mode: goal-based check.
- Author `packs/research/.apm/skills/identify-perspectives/SKILL.md`.

**Done when:** All greps return their expected counts and lint is clean.

### T5: `/build-outline` skill

**Depends on:** T1

**Tests:**
- SKILL.md frontmatter compliant.
- Body documents topic-decomposition methodology (cites STORM outline stage + PRISMA PICO framework).
- Body documents the `outline.md` output schema (sub-questions + brief rationale).
- Body documents depth-via-prompt cues (AC21).
- Lint clean; content-portability grep clean.

**Approach:**
- Mode: goal-based check.
- Author `packs/research/.apm/skills/build-outline/SKILL.md`.

**Done when:** All greps return their expected counts and lint is clean.

### T6: `/devils-advocate` skill

**Depends on:** T1

**Tests:**
- SKILL.md frontmatter compliant.
- Body documents the counter-evidence methodology (cites ACH evidence-against column + GIJN journalism "what does the other side say").
- Body documents integration with `/research` deep mode AND standalone invocation.
- Body documents the `counterpoints.md` output schema (linking back to source artifact; proposing rating downgrades).
- Body documents the moderator unused-snippet pass (AC19).
- Body documents depth-via-prompt cues (AC21).
- Lint clean; content-portability grep clean.

**Approach:**
- Mode: goal-based check.
- Author `packs/research/.apm/skills/devils-advocate/SKILL.md`.
- Methodology: main session reasons about counter-positions; dispatches scoped retrievals to `evidence-retriever`; synthesizes rebuttals.

**Done when:** All greps return their expected counts and lint is clean.

### T7: `/compare-hypotheses` skill

**Depends on:** T1

**Tests:**
- SKILL.md frontmatter compliant.
- Body documents the ACH matrix methodology (hypotheses × evidence-for/against).
- Body documents per-hypothesis parallel retrieval (the +81% parallelizable-task case from the multi-agent literature; main session enumerates hypotheses; N parallel `evidence-retriever` dispatches one-per-hypothesis).
- Body documents the `hypotheses.md` matrix output schema.
- Body documents depth-via-prompt cues (AC21).
- Lint clean; content-portability grep clean.

**Approach:**
- Mode: goal-based check.
- Author `packs/research/.apm/skills/compare-hypotheses/SKILL.md`.

**Done when:** All greps return their expected counts and lint is clean.

### T8: `/decision-archaeology` skill

**Depends on:** T1

**Tests:**
- SKILL.md frontmatter compliant.
- Body documents the rationale-reconstruction methodology (time-ordered sources; chronology + rationale chain + alternatives considered).
- Body documents the self-contained orchestration (does not invoke `/source-map`).
- Body documents the `archaeology.md` output schema.
- Body documents depth-via-prompt cues (AC21).
- Lint clean; content-portability grep clean.

**Approach:**
- Mode: goal-based check.
- Author `packs/research/.apm/skills/decision-archaeology/SKILL.md`.

**Done when:** All greps return their expected counts and lint is clean.

### T9: Two retrieval subagents

**Depends on:** T1

**Tests:**
- `packs/research/.apm/agents/evidence-retriever.md` exists; frontmatter has `name`, `description`, `tools = "Read, Grep, Glob, WebFetch, WebSearch"`, `model = "sonnet"`.
- `packs/research/.apm/agents/source-extractor.md` exists; same frontmatter shape.
- Body of each contains the AC17 sentence: "return synthesis with citations only; do not return raw fetched HTML or untruncated source text" (or normalized equivalent — grep tolerant).
- `lint-agent-artifacts.py packs/research/.apm/agents/` returns zero.
- Content-portability grep against both files returns zero.

**Approach:**
- Mode: goal-based check.
- Author the two subagent files.
- Tools: read-only set plus the two web tools.
- Model: `sonnet` (retrieval is bounded; cost beats capability — mirrors `implementer`'s rationale per CONVENTIONS § Model selection).

**Done when:** Both files lint clean and grep clean.

### T10: Retriever convention + example retrievers (flat layout)

**Depends on:** T2

**Tests:**
- `packs/research/.apm/skills/research/scripts/arxiv-retriever.py` exists at the flat path (no nested subdir).
- `packs/research/.apm/skills/research/scripts/perplexity-retriever.py` exists at the flat path; declares `metadata.auth: env` in a module-level docstring or comment header; reads `PERPLEXITY_API_KEY` from `os.environ`.
- `packs/research/.apm/skills/research/references/retriever-interface.md` exists at the flat path; documents the interface contract per AC7+AC8 (input `query: str`; output `{"content": str, "citations": list[{url, title, primacy}], "shape": "raw" | "synthesized" | "meta"}`).
- Stub conformance check: each `.py` script can be imported and exposes a `retrieve(query: str) -> dict` function signature.
- `/research`'s SKILL.md "Retrievers" section references the two `scripts/*.py` and `references/retriever-interface.md` (cross-link).
- Layout grep: `find packs/research/.apm/skills/*/references packs/research/.apm/skills/*/scripts -mindepth 2 -type d` returns no results (covers both `references/` and `scripts/` per AC8 + Boundaries Never-do).

**Approach:**
- Mode: goal-based check + small TDD probe for the conformance import.
- Author `references/retriever-interface.md` documenting all three surfaces (built-in, MCP, scripts) and the script interface contract.
- Author `scripts/arxiv-retriever.py` wrapping `http://export.arxiv.org/api/query?...` (public, no auth, returns `shape: raw`).
- Author `scripts/perplexity-retriever.py` calling Perplexity Sonar API with `Authorization: Bearer ${PERPLEXITY_API_KEY}` (returns `shape: synthesized`).
- Document the MCP path with one-sentence guidance on when to reach for which mechanism (MCP for shared/team/auth-multi-process; scripts for personal/lightweight/already-credentialed-CLI wrappers).

**Done when:** All files exist at the flat paths; conformance check passes; cross-links resolve; layout grep clean.

### T11: Methodology and confidence-schema references

**Depends on:** T2

**Tests:**
- `packs/research/.apm/skills/research/references/methodologies.md` exists at the flat path.
- Grep confirms all seven discipline names: `STORM`, `PRISMA`, `ACH`, `Wikipedia`, `OSINT`, `GIJN`, `GRADE`.
- Each gets at least one paragraph naming the discipline's contribution to the skill bodies.
- `packs/research/.apm/skills/research/references/confidence-schema.md` exists at the flat path.
- Names the four levels (`high` / `moderate` / `low` / `uncertain`) and the downgrade-factor set (single source / no peer review / vendor-blogged / contested-in-field / heterogeneity / indirectness).
- Contains one worked example of `/devils-advocate` downgrading a finding from `high` to `moderate`.

**Approach:**
- Mode: goal-based check.
- Author both reference files at the flat path.

**Done when:** All greps return expected counts; worked example present; layout flat.

### T12: Integration test (TDD)

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11

**Tests:**
- `pytest packages/agentbundle/tests/integration/test_install_research_user_scope.py` passes.
- Test matches the `test_install_converters_user_scope.py` shape (TestCase + temp `$HOME` + in-process `install.run` + projected-paths assertion + `uninstall.run` + cleanup).
- Asserts seven skill directories at `self.home / ".claude" / "skills" / <skill>` and two agent files at `self.home / ".claude" / "agents" / <agent>.md`.
- HOME-resolution guard fires before state-file assertions.
- State `schema-version` matches `agentbundle.config.STATE_SCHEMA_VERSION`.
- `len(state.packs["research"].files) >= 7` (one file-tracking entry per shipped skill, matching the converters precedent in `docs/specs/converters-pack/spec.md` AC6a).

**Approach:**
- Mode: TDD.
- Red: test file does not exist before write; an empty stub TestCase asserts `assertEqual(1, 2)` to confirm runner picks it up.
- Green: replace stub with the canonical sibling-test pattern; run; iterate until green.
- Refactor: extract a `_ResearchScopeInstallBase` only if a second test in this file emerges (don't pre-extract per `AGENTS.md § Keeping changes minimal`).

**Done when:** Test passes locally; the existing CI pytest job (added in `converters-pack` PR per its AC6b) picks up the new file automatically.

### T13: Verify `docs/specs/README.md` Active specs row

**Depends on:** none

> Note: this task lands in the same PR as the spec body itself. The row was added during spec drafting (governance hygiene; the spec is incomplete without the catalogue entry). T13 catches a real failure mode — the `Constrained by` column converged late in adversarial review (RFC-0009 + RFC-0012 added in pass 1); without this gate the row could drift from the spec's final `Constrained by:` header and the catalogue index would lie about what the spec actually depends on.

**Tests:**
- The Active specs table contains a `research-pack/` row with Status (Draft), Constrained by (RFC-0004, RFC-0009, RFC-0011, RFC-0012, ADR-0002), and Notes columns populated.
- Grep: `rg 'research-pack' docs/specs/README.md` returns at least one hit in the Active specs table.
- Constrained-by column lists all five citations (matches spec.md's `Constrained by:` header).

**Approach:**
- Mode: goal-based check.
- Confirm `docs/specs/README.md`'s Active specs table row is present (added during spec drafting); update Constrained-by column to match the spec's final list if it drifted during adversarial review.

**Done when:** Table contains the row; grep confirms; Constrained-by column matches the spec.

### T14: Diátaxis tutorial guide

**Depends on:** T2

**Tests:**
- `docs/guides/research/tutorials/research-first-session.md` exists.
- AC22 goal-based verifications pass: `rg -F 'agentbundle install research'`, three per-mode greps (`quick`, `standard`, `deep`), two artifact-name greps (`research.md`, `counterpoints.md`), code-fence count ≥6, `wc -l ≥ 50` — each as a separate invocation per AC22.
- AC22 manual-QA verification: recorded walkthrough timing note appended to the implementing PR's description, confirming the ≤15-minute target landed (mode declared explicitly here to match the spec's Testing Strategy "Goal-based + manual QA" row).

**Approach:**
- Mode: goal-based check + manual QA (≤15-minute walkthrough timing).
- Author via the `new-guide` skill with quadrant `tutorials`.
- Lead the adopter through install → quick → standard → deep with one transcript excerpt per mode; do not enumerate (that's AC24's job).
- Link out to AC24 for reference details and AC25 for the why.

**Done when:** AC22 goal-based verifications pass AND a walkthrough timing note is captured in the PR description.

### T15: Diátaxis how-to guide

**Depends on:** T2, T3, T4, T5, T6, T7, T8

**Tests:**
- `docs/guides/research/how-to/research-pipelines.md` exists.
- AC23 verifications pass: three pipeline-name greps + seven artifact-filename greps.

**Approach:**
- Mode: goal-based check.
- Author via the `new-guide` skill with quadrant `how-to`.
- Three recipes: survey / decision / archaeology pipelines. Each names the invocation sequence, expected artifacts, one degraded-mode example.
- Task-shaped; assumes adopter knows the pack exists and wants to *do* something specific.

**Done when:** AC23 verifications pass.

### T16: Diátaxis reference guide

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11

**Tests:**
- `docs/guides/research/reference/research-pack.md` exists.
- AC24 verifications pass: seven skill names + two subagent names + four confidence levels + three retriever shapes + eight cue tokens, all enforced as separate `rg -F` invocations.

**Approach:**
- Mode: goal-based check.
- Author via the `new-guide` skill with quadrant `reference`.
- Information-oriented, complete, dry. Skill `name` + `description` reproduced verbatim from the pack's SKILL.md files (single-source — if the SKILL.md description changes, the reference is regenerated). Sectioned by primitive type.
- No narrative; that's AC25's job.

**Done when:** AC24 verifications pass.

### T17: Diátaxis explanation guide

**Depends on:** T11

**Tests:**
- `docs/guides/research/explanation/research-methodology.md` exists.
- AC25 verifications pass: seven methodology-name greps + five named architectural-choice greps.

**Approach:**
- Mode: goal-based check.
- Author via the `new-guide` skill with quadrant `explanation`.
- Understanding-oriented, narrative. Tells the story of the seven convergent disciplines and the architectural choices (mode-on-research, retrieval-only subagents, flat layout, citation-forcing, moderator pass).
- Links out to the pack's own `references/methodologies.md` for canonical summaries rather than restating them.

**Done when:** AC25 verifications pass.

## Rollout

The pack ships in one PR. After merge:

1. The pack appears in `.claude-plugin/marketplace.json` (auto-aggregated by the build pipeline).
2. Adopters can run `agentbundle install research --scope user` from any project.
3. The seven skills land in their `~/.claude/skills/`; both subagents in `~/.claude/agents/`.
4. Existing repo-scope behavior unchanged; only user-scope adopters opt in.

No staged rollout; no feature flag. Marketplace addition; non-installing users are unaffected.

## Risks

- **Mode-misfire on `/research`.** Risk: LLM upcasts to deep mode on casual prompts. Mitigation: SKILL.md description tightly worded with `quick` as default; "explicit signal required" rule documented in Always do; AC11 manual QA verifies on a deliberately casual prompt.
- **Depth-cue misread on the other six skills.** Risk: adopters expect formal modes after seeing `/research`; LLM ignores depth cues. Mitigation: each non-`/research` SKILL.md documents the cue convention explicitly (AC21); promotion to formal modes deferred until misfire evidence emerges (per Ask-first rail).
- **Retriever convention complexity.** Risk: documented interface too thin (users can't write retrievers) or too thick (we invent infrastructure). Mitigation: ship two working examples (arXiv unauth + Perplexity env-broker) at the flat-layout paths; MCP path documented as the heavyweight alternative.
- **Content-portability bug.** Risk: a skill body accidentally references casablanca vocabulary, breaking the user-scope falsifiable test. Mitigation: AC5 grep runs pre-merge and in CI.
- **Subagent context-handoff failure.** Risk: the two retrieval subagents drop citations on handoff back to main session (the multi-agent telephone-game effect). Mitigation: AC17 grep verifies each subagent body explicitly instructs "return synthesis with citations only"; methodology in skill bodies treats subagents as retrieval-only, with reasoning in main session.
- **Methodology drift over time.** Risk: skill bodies bit-rot away from the seven convergent disciplines. Mitigation: `references/methodologies.md` is the auditable source; AC20 grep gates against rot.
- **Layout drift.** Risk: a future change adds nested subdirectories under `references/`. Mitigation: AC8's `find -mindepth 2 -type d` check runs in CI; **Never do** documents the rule.
- **Forward-compat with RFC-0013 broker contract.** Risk: `perplexity-retriever.py` declares `metadata.auth: env` today (RFC-0006 shape, shipped); when RFC-0013 ships its full broker contract, the declaration may need updating. Mitigation: env-broker is the most stable of the four broker shapes; updating one example file is a thin follow-up if RFC-0013 alters the env declaration grammar.

### T19: `/research` SKILL.md body — applied mode dispatcher

**Depends on:** T2 (mode dispatcher landed in original PR)

**Tests:**
- `mode: quick | standard | applied | deep` literal in body (AC11 amendment + AC26 first grep).
- Description frontmatter biases applied-mode cues per AC11 — at least one of AC28's closed four-cue set (`applied patterns for`, `best practice for`, `prior art on`, `grey literature`) appears in the description; AC28's positive `/research`-SKILL.md greps still demand each cue appears at least once *somewhere* in the file (which the body's Applied-mode section satisfies), but the description's role is to bias the dispatcher and a single phrase is enough for that. Floor pinned at 1 to match T22's conformance test floor.
- Body has an `Applied mode` section (heading `### Applied mode` under `## Modes` parent) that names all four AC29 discipline frames (`prior art`, `best practice`, `case studies`, `anti-patterns`) within the section body; documents practitioner-independence (`same vendor`, `same employer`); documents recency (`>5-year` or `stale prior art`). Section-scoped via flag-based awk per AC29 verification — `prior art` and `best practice` would otherwise auto-satisfy via AC28 cue documentation elsewhere in the file, so the AC29 greps run against the awk-extracted section only.
- Body documents the discipline marker convention — `> Discipline: applied (practitioner-pattern survey)` — that applied-mode `research.md` emits as its first non-heading line (AC26 second grep, full-string literal).
- Body documents the cue-precedence rule (applied cues scored before standard/deep cues) explicitly so the dispatcher reads consistently (AC11 amendment). Verified by `rg -iE 'precedence|applied cues.*before|score.*applied.*first|before standard|applied.*ahead of' packs/research/.apm/skills/research/SKILL.md` returning ≥1 hit per AC11's body-grep clause.
- Body cross-links to `references/confidence-schema.md` for the mode-aware overlay (AC27), section-scoped: `awk '/^### Applied mode/{f=1;next} f && /^#{1,3} /{f=0} f' packs/research/.apm/skills/research/SKILL.md | rg -F 'references/confidence-schema.md'` returns ≥1 hit (the cross-link lives inside the Applied-mode body section, not just anywhere in the file — mirrors AC29's awk-extract pattern).
- `lint-agent-artifacts.py packs/research/.apm/skills/research/` returns zero.
- Content-portability grep clean.
- The frontmatter description has no unquoted `: ` (colon-space) sequence — the description is YAML-quoted (`description: "..."`) or, if unquoted, contains no `: ` inside the value. Kiro's frontmatter parser fail-silently drops the entry on unquoted colon-space (#8329; documented in the user-global memory `reference_kiro_frontmatter_parser`); the existing description is already quoted from iter-1 review pass 1 of the original PR, but the T19 amendment editing must preserve quoting. Verification: `python3 -c "import yaml,sys; meta=next(yaml.safe_load_all(open('packs/research/.apm/skills/research/SKILL.md')));assert 'description' in meta;print(meta['description'][:80])"` returns the description without parser errors.

**Approach:**
- Mode: goal-based check.
- Amend the frontmatter description to include at least one applied-cue phrase (e.g., `applied patterns for`). The current description is well under the agentskills.io 1024-char cap, so all existing casual cues (`look up`, `find out`, `quick check`) and the existing escalation cues stay verbatim — the conformance test `test_casual_cue_tokens_present` asserts all three casual cues are present (looping, not "any one of"), and the amendment must not break that gate. Keep the description YAML-quoted (the iter-1 pass-1 amendment to the original PR added quoting to refuse the `: ` parser bug — that quoting must remain). Adding two or three cues is fine; the floor is 1 to match T22's `test_applied_cue_tokens_present` "any one of" assertion.
- Add a new `### Applied mode` section under `## Modes`. Body explicitly:
  - Names all four AC29 discipline frames within the section: `prior art`, `best practice`, `case studies`, `anti-patterns` — covering positive shapes (prior art / best practice) and failure-mode shapes (case studies / anti-patterns).
  - Documents the source taxonomy bias (blogs, conference talks, vendor case studies, community threads, podcasts, Substack — practitioner grey literature).
  - Documents the practitioner-independence rule (three sources from the same vendor / employer count as one).
  - Documents the recency rule (>5-year-old patterns in fast-moving domains are suspect under the `stale prior art` downgrade factor).
  - Documents the discipline marker — the produced `research.md`'s first non-heading line is `> Discipline: applied (practitioner-pattern survey)` (canonical-form byte-for-byte literal per AC26).
  - Documents the cue-precedence rule (applied cues scored before standard/deep cues) per AC11.
  - Cross-links to `references/confidence-schema.md` for the mode-aware overlay.

**Done when:** All greps return their expected counts and lint is clean.

### T20: `confidence-schema.md` mode-aware overlay

**Depends on:** T11 (base schema landed)

**Tests:**
- New section titled exactly `## Applied-mode overlay` present (AC27 first grep — single canonical form; em-dash variant not accepted).
- Names two new factors as headings or as bold-tagged definitions: `survivorship bias`, `stale prior art` (AC27 second and third greps).
- Acknowledges `no peer review` is dropped for applied mode but still in the base schema (AC27 fourth grep — `no peer review` still appears in the doc).
- Contains one worked example of `/devils-advocate` proposing a rating change using `survivorship bias` or `stale prior art` against an applied-mode `research.md` (AC27 fifth grep — `devils-advocate` or `adversarial`).

**Approach:**
- Mode: goal-based check.
- Append `## Applied-mode overlay` section after the existing worked example. Body:
  - Restates that applied mode uses the same `high` / `moderate` / `low` / `uncertain` levels and the same step-down arithmetic (one factor → one level down).
  - Drops `no peer review` for applied invocations (with the discipline-marker as the rule-set selector).
  - Adds `survivorship bias` — only successes blog; failure stories underweighted.
  - Adds `stale prior art` — a pattern from >5 years ago in a fast-moving domain may have been superseded.
  - Worked example: a finding rated `[high]` in applied-mode `research.md` downgraded to `[moderate]` by `/devils-advocate` flagging `survivorship bias` after retrieving practitioner post-mortems on failed adopters.

**Done when:** All AC27 greps return expected counts; worked example present.

### T21: Reference + explanation + tutorial guide touches

**Depends on:** T19, T20

**Tests:**
- Reference guide mode table includes `applied` row with default? = no, artifact = `research.md` + discipline marker, retrievers, triangulation rule (AC24 mode-greps enforce the four mode tokens including `applied`; AC28 cue-greps enforce the four applied-cue phrases inside the reference guide).
- Reference guide enumerates the closed applied-cue set (AC28 greps).
- Explanation guide mentions the applied-mode rationale as a sixth architectural choice (or extends the mode-on-research section to acknowledge the discipline-axis extension). Manual edit; no separate spec grep added (AC25's existing five-choice grep continues to pass).
- Tutorial guide adds a short mention of applied mode in the modes table (optional sentence in the "Where to go next" section).

**Approach:**
- Mode: goal-based check.
- Reference guide:
  - Extend the `/research` mode parameter table with the `applied` row.
  - Add the applied-cue set to the Depth cue vocabulary section (or a parallel "Applied cues" section if the depth-cue framing doesn't fit).
- Explanation guide:
  - Extend the mode-on-research architectural-choice section to acknowledge that the discipline axis (academic vs practitioner) was the second use-case feedback shape that motivated extending the flat mode parameter; cross-reference AC27's overlay as the mechanism.
- Tutorial guide:
  - One-line mention of applied mode in the mode table or a new "what about practitioner patterns?" footnote.

**Done when:** AC28 reference greps pass; explanation + tutorial edits land coherently.

### T22: Conformance test extension — split escalation regression into two tests

**Depends on:** T19

**Tests:**
- `test_research_retrievers_conformance.py::ResearchSkillDescriptionRegression` splits `test_escalation_cue_tokens_present` into two parallel "any one of" tests:
  - `test_standard_or_deep_cue_tokens_present` — keeps the existing 4-tuple (`research with citations`, `evidence-grounded`, `go deep`, `comprehensively`). Each invocation must find at least one.
  - `test_applied_cue_tokens_present` — NEW. Asserts at least one of the four applied cues (`applied patterns for`, `best practice for`, `prior art on`, `grey literature`) appears in the description.
- Both tests must pass — splitting closes the gap where a single combined tuple would silently accept a description carrying *only* applied cues and dropping all standard/deep escalation cues.
- `test_casual_cue_tokens_present` is unchanged (already loops on `look up`, `find out`, `quick check`).

**Approach:**
- Mode: TDD (each new test fails until the corresponding cue side is present in the description).
- Add `test_applied_cue_tokens_present` mirroring the existing `test_escalation_cue_tokens_present` shape but with the applied-cue tuple; rename the existing method to `test_standard_or_deep_cue_tokens_present` to keep the contract explicit.

**Done when:** Both split tests pass with the T19 amended description; either test fails locally if the corresponding cue side loses every token.

### T23: docs/specs/README.md row + post-amendment gates + review

**Depends on:** T19, T20, T21, T22

**Tests:**
- `docs/specs/README.md` Active-specs row for `research-pack` updated: description mentions `mode: quick | standard | applied | deep`; the architectural-choice note for applied mode is one sentence in the description column.
- `make pre-pr` passes.
- `make build-self` does not produce drift (the marketplace.json description is set on the pack — re-run if pack.toml description changed; pack.toml is unchanged in this amendment, so build-self should be a no-op).
- Integration test `test_install_research_user_scope.py` still passes (no new files projected; applied mode is body-level).
- Adversarial-reviewer returns `Clean — ready to commit.` after gates.

**Approach:**
- Mode: goal-based check + adversarial review.
- Update the README row; run `make pre-pr`; spot-check integration test; dispatch adversarial-reviewer with the diff scope (the spec/plan amendments + the body/overlay/guide edits + the conformance test extension).

**Done when:** Catalogue row in sync; gates green; reviewer clean.

## Changelog

- 2026-05-28: initial plan drafted alongside spec.
- 2026-05-28: post-adversarial-review pass 2: T12 file-tracking floor relaxed from `>= 9` to `>= 7` (sync with spec AC10 amendment); T10 + cross-cutting layout test extended find expression to also cover `scripts/` per AC8; T2 Tests bullet clarified inline interface-description vs T10's cross-link scope; T13 reframed with explicit failure mode (Constrained-by drift catch).
- 2026-05-28: post-adversarial-review pass 3 (mechanical fixes only): T2 Tests bullet sync'd to spec AC7's pass-3 quoted-JSON-key form (six separate `rg -F` invocations expected at construction time).
- 2026-05-28: post-clean amendment — added T14 (Diátaxis tutorial), T15 (how-to), T16 (reference), T17 (explanation) paired with spec AC22–AC25. Tasks land in the same PR; dependencies wire each guide to the skill bodies it documents.
- 2026-05-28: amendment-review pass (mechanical fixes only): T14 Tests bullet extended with explicit artifact-name greps + code-fence count + manual-QA timing-note dimension (matching the spec's Testing Strategy row for AC22).
- 2026-05-28: post-clean amendment — added T19 (`/research` body, applied mode dispatcher), T20 (`confidence-schema.md` applied-mode overlay), T21 (reference / explanation / tutorial guide touches), T22 (conformance test extension), T23 (catalogue row + gates) paired with spec AC26–AC29. Tasks land in the same PR (the still-open #173) since they extend the still-shipping `/research` skill body and its references; stacking would split a single primitive's contract across two reviews. The integration test is unchanged — applied mode is body-level (no new file projected).
