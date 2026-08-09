# Plan: frontend-engineering-doctrine-update

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> record why in the changelog.

## Approach

Benchmark the shipped frontend-engineering pack first, using RFC-0071 and the
Digital Experience Contract as the obligation set and canonical pack sources as
evidence. Author only claims the baseline supports. After the journey,
marketing-page job framing, page-contract how-to, and performance reference are
written, extract every final publication claim and reconcile it against shipped
evidence. Unsupported publication claims are removed or narrowed; only genuine
skill-behavior gaps become follow-on work. Then integrate navigation, generated
surfaces, pack metadata, eval coverage, and durable rendered evidence.

## Constraints

- RFC-0071 Area E is the doctrine source; ADR-0057 makes
  `packs/frontend-engineering/` the canonical skill owner.
- `packs/frontend-engineering/JOURNEY.md` is the journey source;
  `web/src/content/journeys/frontend-engineering.md` is generated output.
- `guides/` is adopter-facing and follows Diátaxis plus
  `contracts/guide.schema.json`; author guide prose through the
  `author-product-docs` workflow.
- Non-cosmetic pack changes require synchronized `pack.toml` and plugin-manifest
  versions, a changelog entry, and regenerated catalogue projections.
- No `.apm/` skill or reviewer body change is authorized. The only permitted
  `.apm` edit is the main skill's `evals/eval_queries.json`, required by the pack
  eval convention and limited to benchmark-derived activation/near-miss cases.
- No new dependency or top-level directory is introduced.

## PLAN record

### Assumption trio

- **Files:** Touch only this spec directory, the FE journey/manifest sources,
  FE marketing content, FE guide tree, the main skill's activation eval JSON,
  required indexes/changelog, `workspace.toml` for proven behavior gaps, and
  generator-owned projections.
- **Done tests:** Guide, journey, eval, catalogue, projection, site-build, and
  repository gates pass; `qa.md` records real local-build observations and
  fresh-context review across the four reader journeys.
- **Not changing:** FE skill/reviewer behavior, dependencies, top-level
  structure, the canonical contract field set, or universal numeric asset
  ceilings.

### Declined patterns

- **Skill refactor:** declined because benchmark findings need separate scope and
  approval before adopter behavior changes.
- **Shared budget schema or new helper:** declined because the fixed doctrine is
  small, prose-owned, and has no second machine consumer.
- **Direct generated-file edits:** declined because the journey and marketplace
  already have canonical generators.
- **New guide taxonomy or site component:** declined because the existing
  Diátaxis and pack-page structures carry the required content.
- **New dependency:** declined because repository-native validators and builders
  already provide the required checks.

### Resolve-vs-surface disposition record

- **Resolved in PLAN:** canonical ownership, benchmark-first scope, qualitative
  asset-budget guidance, publication stack, design references, generated-output
  routes, and authorized eval-only `.apm` scope.
- **Surface during EXECUTE:** a benchmark result requiring skill behavior
  changes, a final claim that cannot be narrowed without changing the objective,
  a concurrent pack-version advance, or inability to exercise the real local
  rendered surfaces.
- **Status:** open until DECIDE; every review finding receives an apply or defer
  disposition before closeout.

## Construction tests

**Integration tests:**

- `python3 tools/validate_guides.py`
- `python3 tools/check-guide-index.py`
- `python3 tools/lint-pack-journeys.py`
- `python3 tools/lint-journey-contract.py`
- `python3 tools/build-site.py`
- `agentbundle catalogue lint --root .`
- `agentbundle catalogue lint --root . --deep`
- `agentbundle catalogue verify --root .`
- `FORCE=1 make build-self`
- `SKIP_SAST=1 make build-check`

**Manual verification:**

- Build the web and documentation surfaces in repository-prescribed order and
  inspect the frontend-engineering pack page, journey, page-contract how-to, and
  performance reference at 375px, 768px, and 1280px.
- Run a cold-reader five-second scan on the pack page and task-completion passes
  from pack page to journey, page-contract guidance, and performance guidance.
- Run fresh-context experience review against the established platform-site and
  docs-site directions; resolve all severity-3-or-higher findings.
- Record commands, exit results, routes, per-viewport observations, evidence
  identifiers, session boundary, and reviewer summary in
  `docs/specs/frontend-engineering-doctrine-update/qa.md`.

## Design (LLD)

### Design decisions

- Benchmark before authoring so publication follows shipped truth rather than
  restating roadmap intent. Traces to AC1–AC2.
- Keep performance budgets policy-shaped: fixed CWV thresholds plus
  surface-specific prioritization, with project-specific numeric asset ceilings.
  Traces to AC7.
- Use one canonical journey source and generated web projection. Traces to
  AC4–AC5.

### Component / module decomposition

- `benchmark.md`: internal evidence matrix covering the nine skills and reviewer.
- `packs/frontend-engineering/JOURNEY.md`: shipped, canonical adopter journey.
- `web/src/content/packs/frontend-engineering.md`: marketing entry point and
  jobs-first routing.
- `web/src/content/journeys/frontend-engineering.md`: generated journey surface.
- `guides/frontend-engineering/how-to/page-screen-contract.md`: task guide.
- `guides/frontend-engineering/reference/performance-targets.md`: policy reference.
- `guides/frontend-engineering/README.md`: guide-tree orientation and routing.

Traces to AC1 and AC3–AC10.

### State & control flow

The adopter path is pack page → choose create/retrofit/audit/verify → inspect the
journey → open the relevant task guide or reference → invoke the named skill.
The benchmark precedes publication and gates every capability claim. Build-site
generation copies the canonical journey into the web collection before the web
build. Traces to AC1–AC9.

### Behavior & rules

- The page/screen contract keeps its canonical 12 field names and remains
  proportional to risk and scope.
- CWV targets are fixed; numeric asset ceilings remain project-specific.
- Marketing copy sells the adopter job; guide copy teaches or references the
  task without marketing inflection.
- Generated files are never edited independently of their canonical source.

Traces to AC3–AC9.

### Quality attributes (NFRs)

- Accessibility and responsive behavior are verified on the rendered surfaces,
  not inferred from Markdown or a successful build.
- Cross-surface claims are traceable to benchmark evidence.
- Guide and journey schemas remain machine-readable and navigation-safe.

Traces to AC1, AC9, AC11, and AC12.

## Tasks

### T1: Every doctrine obligation has an initial evidence baseline

**Depends on:** none

**Touches:** docs/specs/frontend-engineering-doctrine-update/benchmark.md

**Verification mode:** goal-based check plus independent manual audit

**Tests:**

- Confirm the matrix names all nine skills from `pack.toml` and the
  `frontend-reviewer` (AC1).
- Confirm every RFC-0071 Area E obligation and relevant Digital Experience
  Contract responsibility has a disposition and canonical evidence path (AC1).
- Confirm the initial matrix does not treat planned publication prose as shipped
  evidence (AC1).

**Approach:**

- Inventory canonical skills, reviewer, evals, and Digital Experience Contract
  reference from the pack.
- Build an obligation-by-evidence matrix in `benchmark.md` with `Pass`, `Gap`, or
  `Not applicable` dispositions.
- Record candidate behavior gaps for final disposition after claim authoring;
  do not mutate `workspace.toml` yet.

**Done when:** an independent reviewer can trace every doctrine obligation to a
shipped source or a clearly labeled candidate behavior gap.

### T2: The pack page and journey route adopters by frontend job

**Depends on:** T1

**Touches:** packs/frontend-engineering/JOURNEY.md, web/src/content/packs/frontend-engineering.md, packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, docs/product/changelog.md

**Generated outputs:** `web/src/content/journeys/frontend-engineering.md` via
`python3 tools/build-site.py --journeys-only`; `.claude-plugin/marketplace.json` via
`FORCE=1 make build-self` during T6.

**Verification mode:** goal-based check plus visual / manual QA

**Tests:**

- Run `python3 tools/build-site.py --journeys-only`; confirm the generated FE
  journey exists and carries `generated: true` (AC4–AC5).
- Run `python3 tools/lint-pack-journeys.py` and
  `python3 tools/lint-journey-contract.py`; confirm the source and generated
  journey contracts pass (AC4–AC5).
- Run `agentbundle catalogue lint --root .`; confirm the journey and synchronized
  manifests satisfy pack contracts (AC4, AC10).
- Cold-read the pack page in five seconds; identify what the pack is, who it
  serves, and all four jobs before the skill inventory (AC3, AC9).

**Approach:**

- Author the canonical journey using the established journey schema and the
  benchmark-supported workflow.
- Rewrite the web pack body into four job-first sections while retaining the
  detailed inventory as secondary content; add `journeyUrl`.
- Recheck the current pack version immediately before applying the required patch
  bump, synchronize both manifests, and add the changelog entry.

**Done when:** the pack page routes by job and the generated journey exposes the
contract-to-evidence workflow with synchronized pack metadata.

### T3: Adopters can write a proportional page/screen contract

**Depends on:** T1

**Touches:** guides/frontend-engineering/how-to/page-screen-contract.md

**Verification mode:** goal-based check plus manual task completion

**Tests:**

- Run `python3 tools/validate_guides.py`; confirm frontmatter is valid (AC6).
- Compare the guide's field table to the canonical skill and confirm all 12 names
  match exactly (AC6).
- Complete the guide cold for one significant surface and one small component;
  confirm it yields a full contract only where warranted (AC6, AC9).

**Approach:**

- Use `author-product-docs` in how-to mode.
- Explain the decision threshold, canonical fields, proportional subsets, and
  worked examples without duplicating broader craft guidance.

**Done when:** a reader can decide whether a contract is needed and produce the
right-sized artifact without opening the skill source.

### T4: Adopters can apply performance targets without invented ceilings

**Depends on:** T1

**Touches:** guides/frontend-engineering/reference/performance-targets.md

**Verification mode:** goal-based check plus manual lookup QA

**Tests:**

- Run `python3 tools/validate_guides.py`; confirm frontmatter is valid (AC7).
- Compare the CWV thresholds and seven category names to the canonical skill;
  confirm exact semantic parity (AC7).
- For each required surface type, locate its priority, measurement guidance, and
  numeric-budget decision rule in one scan; confirm the mobile/desktop field-data
  split is present and no universal byte ceiling is stated (AC7, AC9).

**Approach:**

- Use `author-product-docs` in reference mode.
- Publish a compact CWV table, canonical asset-budget glossary, and surface-type
  matrix that distinguishes priorities without pretending one byte limit fits
  every product.

**Done when:** a reader can retrieve the fixed targets and decide which asset
categories need project-specific ceilings for their surface.

### T5: Every authored publication claim is evidenced or narrowed

**Depends on:** T2, T3, T4

**Touches:** docs/specs/frontend-engineering-doctrine-update/benchmark.md, workspace.toml, packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json, files from T2–T4 only when a claim must be narrowed

**Verification mode:** goal-based check plus independent manual audit

**Tests:**

- Extract claims from the completed marketing page, journey, and two new guides;
  confirm every row in the pre-integration inventory cites shipped evidence
  (AC1–AC2).
- Confirm unsupported publication claims are removed or narrowed, not converted
  into backlog permission to publish them (AC2).
- Confirm every genuine skill-behavior gap has a matching cold-start-sufficient
  backlog entry, or the benchmark records zero behavior gaps (AC2).
- Run this coverage-bucket check before the deep lint; it requires distinct
  retrofit, page/screen-contract, project-specific asset-budget, and
  documentation-authoring cases with the expected activation polarity (AC13):

  ```bash
  python3 -c 'import json,sys; rows=json.load(open("packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json", encoding="utf-8")); required=[("retrofit",True),("page/screen contract",True),("project-specific asset budget",True),("write a guide",False)]; missing=[(term,expected) for term,expected in required if not any(term in row["query"].lower() and row["should_trigger"] is expected for row in rows)]; print("missing eval buckets:", missing); sys.exit(bool(missing))'
  ```
- Run `agentbundle catalogue lint --root . --deep` and confirm the added
  true/false queries are valid and benchmark-derived (AC13).
- Run the following porcelain-`-z` allowlist check; it exits non-zero for any
  tracked or untracked `.apm` path other than the authorized eval file (AC2,
  AC13):

  ```bash
  python3 -c 'import subprocess,sys; allowed={b"packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json"}; raw=subprocess.check_output(["git","status","--porcelain=v1","-z","--","packs/frontend-engineering/.apm"]); paths={row[3:] for row in raw.split(b"\0") if row}; unexpected=paths-allowed; print("unexpected .apm paths:", sorted(p.decode() for p in unexpected)); sys.exit(bool(unexpected))'
  ```

**Approach:**

- Add the pre-integration claim inventory to `benchmark.md` after T2–T4 prose is
  stable.
- Narrow or remove any claim that shipped sources do not support.
- Route only behavior gaps to `workspace.toml [backlog].open`.
- Add focused activation and near-miss cases without modifying skill behavior.

**Done when:** the authored adopter-facing claims are evidence-complete, behavior
gaps are separately tracked, and `.apm` changes match the single-file allowlist.

### T6: Guide navigation and generated projections stay coherent

**Depends on:** T5

**Touches:** guides/frontend-engineering/README.md, docs/specs/frontend-engineering-doctrine-update/benchmark.md, docs/specs/README.md

**Generated outputs:** `web/src/content/journeys/frontend-engineering.md` via
`python3 tools/build-site.py`; `.claude-plugin/marketplace.json` via
`FORCE=1 make build-self`.

**Verification mode:** goal-based check

**Tests:**

- Run `python3 tools/validate_guides.py` and
  `python3 tools/check-guide-index.py` (AC8, AC11).
- Run `python3 tools/build-site.py` and confirm every new internal link resolves
  through the generated inventory (AC5, AC8, AC11).
- Run `FORCE=1 make build-self` and `agentbundle catalogue verify --root .`;
  confirm projections are synchronized (AC10–AC11).
- Re-extract claims after the guide index is written; confirm the final inventory
  covers the marketing page, journey, two new guides, and
  `guides/frontend-engineering/README.md`, with every claim evidenced or narrowed
  (AC1–AC2).

**Approach:**

- Register both guides in the FE guide index using task-oriented descriptions.
- Reconcile the finished guide-index claims into `benchmark.md`; narrow or remove
  any unsupported index claim before generation.
- Generate the web journey and catalogue projections from canonical sources.
- Update the specs index status atomically with the spec lifecycle.

**Done when:** the final claim inventory includes the guide index, all source and
generated navigation surfaces agree, and repository drift checks report no stale
projection.

### T7: Rendered adopter journeys clear the experience and repository gates

**Depends on:** T6

**Touches:** docs/specs/frontend-engineering-doctrine-update/qa.md, editable source files from T2–T6 only when verification finds an in-scope defect

**Verification mode:** visual / manual QA plus goal-based repository gates

**Tests:**

- Build in the order prescribed by `docs-site/AGENTS.md` and inspect the four
  affected pages at 375px, 768px, and 1280px (AC12).
- Verify pack-page → journey → guide transitions, keyboard focus, navigation,
  code-block scrolling, and absence of page-level horizontal scroll (AC8–AC12).
- Run fresh-context experience review with both grounded aesthetic references;
  resolve every severity-3-or-higher finding (AC9, AC12).
- Record all exercised routes, commands and exit results, viewport observations,
  screenshot or DOM-evidence identifiers, reviewer summary, and the explicit
  local-static-session boundary in `qa.md` (AC12).
- Run `SKIP_SAST=1 make build-check` after all generated artifacts are current
  (AC11).

**Approach:**

- Exercise the built marketing and documentation surfaces as an evaluating lead
  and as a task-focused adopting engineer.
- Apply only defects within T2–T6 scope; route broader redesign findings to
  follow-on work.

**Done when:** `qa.md`, rendered evidence, and repository gates demonstrate a
coherent, responsive, accessible path through all four affected reader journeys.

## Rollout

This ships as a reversible static-content and pack patch release with no feature
flag, infrastructure, migration, or external-system dependency. Reverting the
commit restores the prior publication surfaces. Journey generation precedes the
web build; catalogue self-host generation precedes final drift checks.

## Risks

- The benchmark may find a real skill gap. Expanding implementation would bypass
  the plan and publication review; capture it as follow-on work instead.
- Surface-specific performance guidance can be mistaken for universal budgets.
  State explicitly that teams set numeric ceilings from their product context.
- Direct edits to generated journeys or marketplace data can create dual sources
  of truth. Generate them only from canonical inputs.
- A pack version may advance on the base branch while this work is open. Re-read
  both manifests immediately before bumping; never ride another change's version.
- Source-valid Markdown can still render poorly. Rendered multi-viewport review
  remains a shipping gate.

## Changelog

- 2026-08-08: Initial full-mode plan; added a benchmark-first task and routed
  any discovered skill gaps to follow-on work per user confirmation.
