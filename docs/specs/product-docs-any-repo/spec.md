# Spec: product documentation for any repository

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0060
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0010-product-documentation-page-design.md
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.

## Outcome

A team documenting any code-backed product — a library, CLI, HTTP API, app,
service, plugin, or agent-context pack — can ask `author-product-docs` to create,
revise, retrofit, audit, or verify its documentation, and the skill grounds the
work in that product's own surface and in the reader's whole journey from
discovery to upgrade. Success is a page set where each stage of that journey has
the artifact that answers the reader's question there, each page checked against
what the product ships.

## What Changes

- `author-product-docs` procedure, description, and anti-patterns describe any repository, and the skill owns writing release notes, changelogs, migration guides, and contributing guides; agent-context packs become one surface among several — `packs/product-documentation/.apm/skills/author-product-docs/SKILL.md`
- New reference that maps each product surface to the repository evidence that reveals it, the canonical sources to read, the reference artifacts it needs, and the check that verifies them — `references/surface-discovery.md`
- New reference that defines the documentation journey stages, the reader question and artifact for each, and the stage-by-stage gap report used by audit and retrofit — `references/docs-journey.md`
- Page contracts gain the journey artifacts Diátaxis leaves out (README, quickstart, installation, troubleshooting, changelog and release notes, migration guide, contributing guide, docs landing page); the pack README becomes a README variant — `references/page-contracts.md`
- Artifact model, ownership, conversation-first, and rendered-verification references drop this catalogue's paths and describe destination discovery and surface-specific checks — `references/`
- Evals gain non-pack queries and fixtures — `evals/`
- Pack README, journey, manifest copy, guides, and web pack card describe the generalized skill; the three overlapping how-to guides become two with distinct tasks (improve an existing doc set; document one shipped feature), and the getting-started tutorial teaches documenting a repository with the skill — `packs/product-documentation/`, `guides/product-documentation/`, `web/src/content/packs/product-documentation.md`
- Stale `new-guide` pointers name `author-product-docs` — `packs/experience-design/` (information-architecture), `packs/product-engineering/` (ux-writing, DESIGN.md)
- Patch releases for the three packs, with changelog entries — `pack.toml`, `.claude-plugin/plugin.json`, `docs/product/changelog.md`
- Research grounding — `docs/product/research/product-docs-authoring-survey.md`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | The skill's behavior and the pack's promise change for every adopter | `packs/product-documentation/README.md`, `JOURNEY.md`, `guides/product-documentation/`, `web/src/content/packs/product-documentation.md` | product-documentation maintainers | Rewritten pages; `tools/validate_guides.py` passes | Pages describe any-repository use and link only to existing files |
| Current product truth | The skill is the product | `packs/product-documentation/.apm/skills/author-product-docs/` | product-documentation maintainers | Pack tests and evals | Pack tests green; self-host projection matches |
| Release history | Three packs ship patch releases | `docs/product/changelog.md` | release pipeline | Three `##` entries with Highlights disposition | Entries present and versions match manifests |
| Reusable learning | Research grounds the guidance | `docs/product/research/product-docs-authoring-survey.md` | product-documentation maintainers | The survey | Cited from the plan |
| Decision rationale | none — ADR-0060 already records why Diátaxis is a page contract and not a directory layout; this change applies it, and no new decision is made | — | — | — | — |
| Current architecture | none — no module, boundary, or engine changes | — | — | — | — |

## Agent Rules

### Always do

- Read the source of every behavior a page or skill claim describes before writing the claim.
- Name cross-pack skills by skill name with an "if installed" guard; never add a manifest dependency for them.
- Run self-host after every `.apm/` edit and commit the regenerated projections with it.

### Ask first

- Adding a new skill, command, agent, or hook to any pack.
- Changing a guide's URL slug or deleting a guide file other than `how-to/use-author-product-docs.md`, which this spec merges.
- Changing any test outside `packs/product-documentation/tests/`.

### Never do

- Add a pack dependency, a new top-level directory, or a new Python module.
- Cite this catalogue's paths, records, or acceptance criteria in shipped `.apm/` content.
- Bump `product-documentation` to a minor or major version; the compatibility pack pins `^0.1`.
- Edit generated projections (`.claude/`, `.agents/`, `docs-site/`, `web/` build output) by hand.

## Testing Strategy

- **Shipped skill content rules (AC1–AC8):** TDD. Pack-local tests in `packs/product-documentation/tests/pack/` read the skill files and fail when a surface, stage, page contract, handoff, or forbidden path regresses. Red first against today's skill, which fails every one.
- **Evals (AC9, AC10, AC19):** goal-based. A pack test parses the eval JSON and counts non-pack queries and fixtures.
- **Real invocation (AC11):** manual QA. A fresh agent loads the projected skill and runs it against a small non-pack fixture repository; the recorded output is the evidence. A unit check cannot show whether the procedure produces the right surface and gap report.
- **Cross-pack pointers, pack docs, versions, release record (AC12–AC17, AC20–AC22):** goal-based. Search, guide validation, JSON and manifest reads.
- **Whole catalogue (AC18):** goal-based. The repository gates named in the criterion.
- **Advisory content rules:** the FAQ rule, the `llms.txt` rule, the first-runnable-action rule, and the `surface` and `journey stage` documentation-contract fields are design in the plan's `Behavior & rules`. Content pins in the pack tests catch their removal; no criterion gates their wording.

## Acceptance Criteria

Surface terms (library, CLI, API, app, service) match case-insensitively as whole words, plurals allowed.

- [x] AC1: No file among `SKILL.md` and `references/*.md` of `author-product-docs` contains any of the strings `agent-ready-repo`, `guides/<pack>`, `docs/guides/`, `web/src/content`, or `docs-site/`.
- [x] AC2: The `description` field of `author-product-docs` names each of library, CLI, API, app, and service.
- [ ] AC3: `references/surface-discovery.md` has one `##` section for each of these 8 surfaces:
  1. Library or SDK
  2. CLI
  3. HTTP or RPC API
  4. App (web, desktop, or mobile)
  5. Service
  6. Plugin or extension
  7. Framework or extension points
  8. Agent-context pack
- [ ] AC4: Each of the 8 surface sections in `references/surface-discovery.md` carries the four labels `Evidence:`, `Canonical sources:`, `Reference artifact:`, and `Verification:`.
- [x] AC5: `references/docs-journey.md` has one row for each of these 9 stages, each row naming a reader question and the artifact that answers it: discover and evaluate; install; first success; daily tasks; look up; understand; troubleshoot; upgrade; contribute.
- [x] AC6: The audit and retrofit procedure in `SKILL.md` requires a report row for every journey stage, each marked `covered`, `partial`, `missing`, or `not applicable` with a file reference or reason.
- [x] AC7: `references/page-contracts.md` has each of these 8 exact headings, and the section under each has the four parts "First screen must answer", "Required content", "Move lower or link out", and "Anti-patterns to refuse": `## README`; `## Quickstart`; `## Installation guide`; `## Troubleshooting`; `## Changelog and release notes`; `## Migration guide`; `## Contributing guide`; `## Docs landing page`.
- [x] AC8: `SKILL.md` names each of `information-architecture`, `journey-mapping`, `design-review`, `content-design`, and `ux-writing`, and every line naming one of them carries an "if installed" guard.
- [x] AC9: `evals/eval_queries.json` keeps at least 8 positive and 8 negative queries, and at least 4 positive queries name a CLI, library, API, or app surface without the word "pack".
- [x] AC10: `evals/evals.json` has a case with id `cli-readme-audit` and a case with id `library-journey-gap-audit`, and every path in each case's `files` list exists under `evals/files/` and contains no `pack.toml` reference.
- [x] AC11: A fresh agent running the projected skill against a fixture CLI repository with no `pack.toml` identifies the surface as a CLI, opens the argument-parser source file before it returns its report, and returns a journey gap report with a row per stage; the transcript, including that file read ahead of the report, is recorded in the verification ledger.
- [x] AC12: A search for `new-guide` over `packs/experience-design/.apm/`, `packs/product-engineering/.apm/`, and `packs/product-engineering/DESIGN.md` returns no match, and each match it returned at the merge base now names `author-product-docs`.
- [x] AC13: `guides/product-documentation/how-to/` contains exactly `author-product-docs.md` and `write-a-guide.md`.
- [x] AC14: No guide declares an alias for the removed `how-to/use-author-product-docs` route, so `python3 tools/validate_guides.py` reports 0 warnings.
- [x] AC15: No page under `guides/product-documentation/` names `validate_guides.py` or `build-site.py`.
- [x] AC16: For each of `product-documentation`, `experience-design`, and `product-engineering`, the version in `pack.toml` equals the version in `.claude-plugin/plugin.json`, and it is the merge-base version with only the patch number raised.
- [x] AC17: `docs/product/changelog.md` has a `##` entry `[<pack>][<version>]` for each of the three packs at its AC16 version.
- [x] AC18: Each of these commands exits 0: `make lint-ruff lint-mypy`; `python3 tools/validate_guides.py guides/`; `agentbundle catalogue lint --root . --deep`; `agentbundle catalogue verify --root .`; `python3 -m pytest packs/product-documentation/tests packs/experience-design/tests packs/product-engineering/tests tests/roster/test_product_documentation_pack.py tests/roster/test_shipped_pack_manifests.py -q`; and `agentbundle catalogue self-host --root . --write` followed by `git status --porcelain` prints nothing.
- [x] AC19: In `evals/eval_queries.json`, "Write release notes for the 2.0 release" is `should_trigger: true`.
- [x] AC20: `packs/product-engineering/.apm/skills/ux-writing/evals/eval_queries.json` has a `should_trigger: false` query asking for a troubleshooting page, in addition to its existing documentation negative.
- [x] AC21: The `description` in `packs/product-documentation/pack.toml`, the `description` in its `.claude-plugin/plugin.json`, the first paragraph of `packs/product-documentation/README.md`, and the body of `web/src/content/packs/product-documentation.md` each name at least one of library, CLI, API, app, or service.
- [x] AC22: No file outside `docs/specs/` links to `use-author-product-docs.md`, and every relative Markdown link in `packs/product-documentation/README.md`, `packs/product-documentation/JOURNEY.md`, `guides/product-documentation/**`, `guides/README.md`, and `docs/guides/how-to/author-product-documentation.md` resolves to an existing file.
- [ ] AC23: The audit procedure in `SKILL.md` requires one journey gap report per user-facing surface or audience when a repository has more than one, and names the site configuration's navigation as the docs index when a docs site exists.
- [ ] AC24: `SKILL.md` forbids running project code, builds, or installs from a repository the user has not said to trust, and directs the agent to check against source and say so instead.

## Follow-ons

- product-documentation maintainers: `docs/product/intents/FEAT-0010-product-documentation-page-design.md` — close the intent through `close-work` once this spec ships.

## Assumptions

- Product: no corpus of real non-pack repositories was scored — whether repository signals identify a surface reliably across heterogeneous repositories stays ungrounded beyond the fixture in AC11 (FEAT-0010's riskiest assumption).
