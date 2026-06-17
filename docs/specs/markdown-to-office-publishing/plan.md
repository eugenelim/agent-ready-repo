# Plan: markdown-to-office-publishing

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Add three independent skills under `packs/converters/.apm/skills/`, then bump
the pack and wire CI and docs. Each skill is a self-contained PR-sized unit:
`SKILL.md` (lean) + `references/` (the fill-point model and mapping detail) +
`scripts/render.py` (the deterministic renderer with `--check` / `inspect` /
`render` verbs) + `scripts/test_*.py` (the TDD suite) + `evals/evals.json`.

The three skills share a **conceptual** shape — Tier-1 detect, inspect-then-map,
deterministic render — but **no code** (RFC-0036 Open Q1, confirmed: independent
in v1). The risk gradient runs pptx → docx → xlsx, so build in that order: pptx
is fill-ready by construction (layouts already carry placeholders), docx adds
the pre-tagged-template requirement and the run-fragmentation caveat, and xlsx
adds the named-range requirement plus the load-and-resave chart-loss trap. The
riskiest design point — what happens when a user-provided template has no
fill-points — is settled per format in the spec (guide-the-user for docx/xlsx;
exempt for pptx).

The three skill tasks are mutually independent (`Depends on: none`, all-added
files, disjoint directories) and could fan out; the bump/CI/docs tasks depend on
all three. The testing story: per-skill TDD units (manifest enumeration, content
mapping, `--check` probe) plus one end-to-end integration test per format that
re-opens the produced file, all CI-gated by explicit per-path lines.

## Constraints

- **RFC-0036** (Accepted) — every decision here traces to it: template-fill not
  convert (decision 2), three per-format skills (decision 3), detect→confirm→
  elicit→opt-out template flow (decision 4), Tier-1 (decision 5), all-three-in-v1
  with PDF / visual-QA as non-goals (decision 6), docs as a follow-on (decision 7).
- **RFC-0007** — the `converters` pack: user-scope-default, ships no `seeds/`, no
  hooks; these additions inherit that shape.
- **`docs/guides/_shared/how-to/author-a-skill.md`** — the 3-tier dependency
  model (Tier-1 here) and the progressive-disclosure skill structure.
- **`tools/lint-skill-spec.py`** — frontmatter + body-cap contract every
  `SKILL.md` must pass.

## Construction tests

Most construction tests live under **Tasks** below (per-task `Tests:`
subsections). Cross-cutting only:

**Integration tests:** one end-to-end render per format (T1/T2/T3 each own
theirs) — invoke `scripts/render.py` as documented against a fixture template
committed under the skill's `scripts/` test fixtures, then re-open the produced
file with the same library and assert the mapped values are present.
**Manual verification:** activation evals per skill (`evals/evals.json`),
graded by reading the assertions; not automated.

## Design (LLD)

Shape: **mixed**. Stack: stdlib Python ≥3.11 deterministic scripts + the three
PyPI render libraries; structure mirrors the existing converters skills
(`file-to-markdown`, `markdown-to-html`, `mermaid-renderer`).

### Design decisions

- **Template-fill over convert** — only template-fill preserves a user-owned
  brand (RFC-0036 Axis A). Traces to: AC "fills a user-provided template" · no
  `contracts/`.
- **Three independent script sets, no shared engine** — RFC-0036 Open Q1, v1
  default; extract a helper only if real duplication appears. Traces to: spec
  Boundaries (Ask first: shared office engine).
- **Library default for the template-less fallback** — not a shipped scaffold,
  which would edge toward an opinionated default brand (a named non-goal).
  Traces to: AC "template-less using the library default".
- **`render.py` carries verbs (`--check` / `inspect` / `render`)** rather than
  three scripts — one file per skill, the deterministic-renderer idiom intact.
  Traces to: AC "Tier-1 `--check`" + AC "inspect verb".

### Interfaces & contracts

The script CLI is the skill's interface (no formal `contracts/` file). Per
skill, `scripts/render.py`:

- `--check` → import-probe the library; exit `0` present / `2` absent (print the
  `pip install` line on absence).
- `inspect <template>` → print the fill-point manifest (stdout markers:
  `FILLPOINTS:` lines; docx variables / pptx `idx:type:name` / xlsx named ranges
  + tables).
- `render <markdown> --template <tpl> [--output <path>]` (omit `--template` for
  the opt-out library-default path) → write the Office file; stdout markers
  `OUTPUT: <path>`, `FILLED: <n>`, `WARNING: <msg>`.

Markers mirror `file-to-markdown`/`markdown-to-html` so the agent parses output
the same way across the pack. Traces to: AC "deterministic-renderer contract".

### Data & schema

- **Fill-point manifest** — the inspect output: docx = the declared-variable set
  from `get_undeclared_template_variables()`; pptx = a list of `(layout, idx,
  type, name)`; xlsx = `(name → ref)` for `defined_names` + `(table → range)`.
- **Content model** — the intermediate the map step builds from the Markdown AST:
  `{scalars: {...}, sections: [...], lists: [...], tables: [...]}`, projected onto
  the manifest. Pure data; no persistence. Traces to: AC "inspect verb" + AC
  "map step".

### Failure, edge cases & resilience

- Library absent → `--check` exits `2`, fail clean (Tier-1).
- docx/xlsx template with **no** fill-points → emit the guide-the-user message,
  do not silently convert. pptx exempt.
- xlsx workbook carrying charts/shapes → inject into data ranges only; never
  load-and-resave (openpyxl drops those objects). Documented + asserted.
- docx run-fragmentation → guidance to author each tag in one uniform run;
  autoescape on for user content.
- Template-less opt-out → library-default document, communicated up front.
- **Output-path confinement** → canonicalize `--output`, verify it resolves
  under the caller's working directory, refuse symlink-escaping template/input
  paths. Guards a model-influenced output path; local control, not template
  trust. Traces to: AC "confines the output write".
- **Template trust posture (consciously re-decided, not inherited)** →
  user-supplied templates are **trusted-author** input, matching the converters
  pack's local-files-trusted stance (`file-to-markdown/scripts/convert.py:40`
  disables its bomb guard). Consequence: **SSTI** via a malicious template
  author (the `.docx` carries the Jinja2 source) and **XXE / zip-bomb** on a
  crafted archive are accepted, out-of-scope risks for v1, documented per
  `SKILL.md`. Cheap hardening that holds regardless — docx `autoescape=True` and
  output-path confinement above — is still enforced. Traces to: AC "states the
  template trust posture" + spec Assumptions (Security).

### Dependencies & integration

Three new PyPI deps, one per skill, all Tier-1 (user-installed, never bundled):
`docxtpl` (LGPL-2.1; `markdown-to-docx`), `python-pptx` (MIT;
`markdown-to-pptx`), `openpyxl` (MIT; `markdown-to-xlsx`). Recorded in each
skill's `## Prerequisites`. No new runtime dependency enters the catalogue's own
packaging — the libraries live only in the user's environment. Each
`## Prerequisites` names the **exact canonical PyPI package** (typosquat guard —
`docxtpl` is a real but lower-profile single-maintainer package) with a
**minimum-version floor** — the implementing PR pins a concrete, verified
known-good floor per library (docxtpl above the `get_undeclared_template_variables()`
breakage; all three above any advisory current at authoring time) and records it
in the AC, not just here — and the `SKILL.md` notes these Tier-1 deps install
**outside the repo's SCA** (`pip-audit`/CodeQL never scan them) so the user owns
keeping them current. This outside-SCA posture is the accepted state (the user
confirmed Tier-1); a CI `pip-audit` over the T4-installed libraries is left as a
follow-on, not part of this scope. Traces to: AC "Tier-1" + AC "exact canonical
PyPI package" + spec Assumptions (licenses).

## Tasks

### T1: `markdown-to-pptx` skill renders a fixture deck from a template

**Depends on:** none
**Touches:** packs/converters/.apm/skills/markdown-to-pptx/**

**Tests:**
- Unit: `inspect` over a fixture `.pptx` returns the layout/placeholder manifest
  keyed by `idx` (not list position) — verifies AC "inspect verb" (pptx).
- Unit: `map` projects front-matter → title placeholder, one H1/H2 section → one
  slide, a list → bullet rows, a Markdown table → a `TABLE`-type placeholder —
  verifies AC "map step".
- Unit: `--check` exits `0` when `pptx` imports, `2` when monkeypatched absent —
  verifies AC "Tier-1 `--check`".
- Unit: the `..`-traversal, symlink-escape, and sibling-prefix (`workdir-evil`
  vs root `workdir`) `--output`/`--template` cases are all rejected — verifies
  AC "confines the output write".
- Integration (manual-QA mode): `render` against the fixture template writes a
  `.pptx`; re-open with `python-pptx` and assert the mapped text/table values
  are present — verifies AC "end-to-end integration test per format".

**Approach:**
- Author `SKILL.md` (lean, ≤~150 lines): `## Prerequisites` (Tier-1 `pip install
  python-pptx>=<floor>`, exact canonical package, outside-SCA note), the
  deterministic-renderer contract, the detect→confirm→elicit→opt-out template
  flow, the trusted-author template-trust posture note, and the activation
  vocabulary in `description`. Keep `description` a **single-line quoted scalar
  under 1024 chars with no unquoted `: `** (lint-skill-spec.py).
- Author `scripts/render.py` with `--check` / `inspect` / `render` verbs; confine
  the `--output` write under CWD; placeholder access by `idx`, re-fetch the
  placeholder object after any insert (it is replaced).
- `references/fill-points.md` — the pptx placeholder model + mapping table.
- `evals/evals.json` — activation + don't-hand-write-pptx assertions.

**Done when:** the four tests above are green and `render.py render` produces a
fixture `.pptx` whose re-opened content matches the Markdown.

### T2: `markdown-to-docx` skill fills a pre-tagged Word template

**Depends on:** none
**Touches:** packs/converters/.apm/skills/markdown-to-docx/**

**Tests:**
- Unit: `inspect` over a fixture tagged `.docx` returns
  `get_undeclared_template_variables()` — verifies AC "inspect verb" (docx).
- Unit: `map` projects front-matter → `{{ var }}` scalars, a list → a `{%p for
  %}` loop context, a Markdown table → a `{%tr for %}` row context — verifies AC
  "map step".
- Unit: an **untagged** `.docx` yields the guide-the-user message, not a silent
  convert — verifies AC "no-fill-points guidance".
- Unit: `--check` exits `0`/`2` on `docxtpl` present/absent — verifies AC
  "Tier-1 `--check`".
- Unit: a context value containing `{{`/XML metacharacters renders **escaped,
  not interpolated** (proves `autoescape=True` is passed at `render()`) —
  verifies AC "passes `autoescape=True`".
- Unit: the `..`-traversal, symlink-escape, and sibling-prefix (`workdir-evil`)
  `--output`/`--template` cases are all rejected — verifies AC "confines the
  output write".
- Integration (manual-QA mode): `render` against the tagged fixture writes a
  `.docx`; re-open with `python-docx` and assert the rendered values are present.

**Approach:**
- `SKILL.md` (Tier-1 `pip install docxtpl>=<floor>`, exact package, outside-SCA
  note); document the run-fragmentation guidance, the trusted-author trust
  posture (SSTI-via-malicious-template is accepted out-of-scope), and the
  activation vocabulary as a single-line quoted scalar.
- `scripts/render.py` with the three verbs; render via `docxtpl`
  `render(context, autoescape=True)` (autoescape is **off** by default); confine
  the `--output` write under CWD.
- `references/fill-points.md` — the docx Jinja-tag model + how to add tags in
  Word.
- `evals/evals.json`.

**Done when:** the five tests are green and a tagged fixture renders to a `.docx`
whose re-opened content matches the Markdown.

### T3: `markdown-to-xlsx` skill fills named ranges without dropping charts

**Depends on:** none
**Touches:** packs/converters/.apm/skills/markdown-to-xlsx/**

**Tests:**
- Unit: `inspect` over a fixture `.xlsx` returns `defined_names` + worksheet
  `tables` — verifies AC "inspect verb" (xlsx).
- Unit: `map` projects front-matter → single-cell named ranges, a Markdown table
  → a Table data region — verifies AC "map step".
- Unit: a workbook with **no** named ranges yields the guide-the-user message —
  verifies AC "no-fill-points guidance".
- Unit: rendering injects into data ranges only; a fixture workbook carrying a
  chart still has the chart after render (the path never load-and-resaves the
  chart object) — verifies AC "xlsx injects into data ranges only".
- Unit: `--check` exits `0`/`2` on `openpyxl` present/absent.
- Unit: the `..`-traversal, symlink-escape, and sibling-prefix (`workdir-evil`)
  `--output`/`--template` cases are all rejected — verifies AC "confines the
  output write".
- Integration (manual-QA mode): `render` writes an `.xlsx`; re-open with
  `openpyxl` and assert the named-range/table values are present.

**Approach:**
- `SKILL.md` (Tier-1 `pip install openpyxl>=<floor>`, exact package, outside-SCA
  note); document the chart-loss caveat, the trusted-author trust posture, and
  the activation vocabulary as a single-line quoted scalar.
- `scripts/render.py` with the three verbs; write only to named-range/table
  cells; confine the `--output` write under CWD.
- `references/fill-points.md` — the named-range/table model + how to define them.
- `evals/evals.json`.

**Done when:** the six tests are green and a fixture workbook renders to an
`.xlsx` whose re-opened content matches the Markdown and whose chart survives.

### T4: pack bump, README/description refresh, CI wiring, and marketplace refresh

**Depends on:** T1, T2, T3
**Touches:** packs/converters/pack.toml, packs/converters/.claude-plugin/plugin.json, packs/converters/README.md, .github/workflows/build-check.yml, .claude-plugin/marketplace.json

**Tests:**
- Goal-based: `make lint-packs` and `make build` are green; `git diff` shows
  `.claude-plugin/marketplace.json` bumped to `0.2.0` with the updated
  description.
- Goal-based: `grep` confirms three new `python -m pytest` lines (one per skill
  `scripts/`, each preceded by the `pip install` of its library) in
  `build-check.yml`, and the "converters evals.json carry-over disposition" step
  enumerates the three new skills.
- Goal-based: `packs/converters/README.md` lists all three new skills; the
  `description` in `pack.toml`/`plugin.json` names the Markdown→Office direction.
- Manual QA (recorded): an activation grading pass over the three skills'
  `evals/evals.json` — confirm "make this a PowerPoint/Word doc/spreadsheet"
  fires exactly the right skill — with the result recorded durably in
  `docs/specs/markdown-to-office-publishing/notes/activation-grading.md` (not
  only the PR description, which rots after merge), verifying the spec's
  activation Testing-Strategy line.

**Approach:**
- Bump `version` `0.1.2 → 0.2.0` in `pack.toml` and `plugin.json`; leave
  `[pack.adapter-contract]` at `0.8`.
- Update the `description` in `pack.toml` + `plugin.json` and the skill list in
  `packs/converters/README.md` to reflect the outward Markdown→Office direction
  (the `description` propagates into `marketplace.json`).
- Run `make build` to refresh `.claude-plugin/marketplace.json`.
- Add three explicit per-path pytest steps in `build-check.yml` (mirror the
  atlassian/credential-brokers wiring at lines 166-184), each `pip install`ing
  its library first (mirror the atlassian `httpx` install at line 177).
- Extend the converters evals carry-over CI step (~line 285) to include
  `markdown-to-docx markdown-to-pptx markdown-to-xlsx`.

**Done when:** CI is green with the three new suites running, `marketplace.json`
reflects `0.2.0` with the new description, the README lists the skills, and the
activation grading pass is recorded.

### T5: user docs — how-to, reference extension, changelog

**Depends on:** T1, T2, T3
**Touches:** docs/guides/converters/how-to/publish-markdown-to-office.md, docs/guides/converters/reference/converter-skills.md, docs/product/changelog.md

**Tests:**
- Goal-based: the new how-to and the reference edits exist and pass any docs
  link-check; the changelog has an `[Unreleased]` entry naming the three skills.

**Approach:**
- Author `docs/guides/converters/how-to/publish-markdown-to-office.md` (Diátaxis
  how-to) via `new-guide`, leading with the natural-language prompt per skill.
- Extend `docs/guides/converters/reference/converter-skills.md` with the three
  new skills.
- Add the `docs/product/changelog.md` `[Unreleased]` entry.

**Done when:** docs land and link-check is green.

## Rollout

- **Delivery:** additive — three new skills in an existing user-scope pack. No
  flag, no migration. Reversible by removing the skill directories and reverting
  the bump.
- **Infrastructure:** none.
- **External-system integration:** none — the three libraries install into the
  *user's* environment at first use (Tier-1), not into the catalogue.
- **Deployment sequencing:** the pack bump + `marketplace.json` refresh (T4) must
  land with the skills so the published catalogue advertises the new version;
  docs (T5) can land in the same PR.

## Risks

- **Fixture templates in the repo.** The integration tests need committed
  fixture `.docx`/`.pptx`/`.xlsx` templates with fill-points. Keep them tiny and
  document how they were authored, so a reviewer can regenerate them.
- **`docxtpl` version sensitivity.** `get_undeclared_template_variables()` has
  had version-specific breakage (e.g. an AttributeError reported on 0.15.1); pin
  a known-good floor in `## Prerequisites` and the test environment.
- **CI dep-install cost.** The three suites need `docxtpl`/`python-pptx`/
  `openpyxl` installed in CI; add the `pip install` to the per-path steps (mirror
  the atlassian `httpx` install at build-check.yml:177).

## Changelog

- 2026-06-17: initial plan — three independent skills (pptx → docx → xlsx),
  Tier-1, library-default template-less fallback, TDD units + per-format
  integration test, pack bump to 0.2.0, CI wiring, docs follow-on. Resolves
  RFC-0036 Open Q1 (independent script sets), Q2 (minor bump, contract 0.8), and
  Q3 (library-default fallback).
- 2026-06-17: spec-stage adversarial + security review additions — pack
  README/`description` refresh folded into T4 (was drifting silently); recorded
  activation grading pass; output-path confinement AC + tests; docx
  `autoescape=True` split into its own AC + escaping test; explicit trusted-author
  template trust posture (SSTI / XXE / zip-bomb scoped as accepted out-of-scope
  risk, consistent with the converters local-files-trusted stance);
  canonical-package + version-floor + outside-SCA dependency posture; single-line
  scalar `description` lint note on T1–T3.
