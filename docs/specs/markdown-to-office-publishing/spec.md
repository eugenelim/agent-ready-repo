# Spec: markdown-to-office-publishing

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0036, RFC-0007 (the `converters` pack)
- **Brief:** none
- **Contract:** none <!-- the skills expose a script CLI (argv + stdout markers) documented in each SKILL.md and the plan's LLD; it is not one of the formal contracts/<type>/ surfaces (openapi/asyncapi/proto/graphql/jsonschema). -->
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An agent that has produced a polished Markdown artifact — a report, a deck
outline, a tabular summary — can hand a stakeholder that artifact as a
**distribution-ready, on-brand** Office file. Three skills in the `converters`
pack do this: `markdown-to-docx` (Word), `markdown-to-pptx` (PowerPoint), and
`markdown-to-xlsx` (Excel). Each **fills a user-provided, branded template** at
its existing fill-points rather than converting Markdown into a fresh document,
so a designer's cover page, placed logo, corporate slide master, and named cell
regions survive intact. The user owns the brand: the skill detects a template on
disk, confirms or elicits one, and proceeds template-less only on the user's
explicit opt-out — it never invents a brand and never silently converts. Each
skill is Tier-1 on its library (`docxtpl` / `python-pptx` / `openpyxl`): it
declares the dependency, detects it, and fails clean with the exact install
line, mirroring `file-to-markdown`. This completes the pack's Office round-trip,
which until now ran only inward (Office → Markdown).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Apply the **Tier-1 detect-and-stop** contract: declare the library in
  `## Prerequisites` with the exact `pip install` line, detect it via an
  import-probe `--check` verb that exits `0` (present) / `2` (absent), and on
  absence print the install line and stop.
- Keep the **deterministic-renderer idiom**: the script renders; the agent only
  assembles the content model and invokes the script. The agent is not the
  renderer.
- Follow **inspect-then-map**: enumerate the template's fill-points into a
  manifest *before* mapping any content onto them.
- Treat the **user's template as the sole source of branding**; when the user
  opts out of a template, communicate the unbranded result up front before
  producing it.
- **Confine the output write**: canonicalize the `--output` path and verify it
  resolves under the caller's working directory before writing; refuse a
  `--template`/input path that resolves (through symlinks) outside it. The agent
  assembles the output path from model-influenced content, so this is a local
  control, not template-trust.

### Ask first

- Extracting any **shared "office engine"** helper module across the three
  skills — v1 ships three independent script sets; a shared module needs
  sign-off (RFC-0036 Open Q1).
- Bumping the pack's **`[pack.adapter-contract]` level** — it stays `0.8`
  unless a primitive *shape* changes (RFC-0036 Open Q2).
- Adding a **fourth format**, PDF export, or a slide visual-QA loop — all named
  non-goals / follow-ons.

### Never do

- **No new top-level directory and no new pack** — the three skills live in the
  existing `packs/converters/.apm/skills/` tree.
- **No bundled corporate brand or default template asset** — an absent template
  is the user's explicit choice, never a shipped default.
- **No convert-from-Markdown path** (Pandoc / Quarto `--reference-doc`) as the
  implementation — template-fill only.
- **No auto-install** of `docxtpl` / `python-pptx` / `openpyxl` (that is Tier-2
  behavior; banned here).
- **Never manipulate, recreate, or resize the chart/shape objects (or a
  table/named-range's extent) in an `openpyxl` workbook** — inject into data
  ranges only. Filling named ranges/tables inherently requires a
  load-and-resave; the realizable rule is to touch only data cells and never the
  drawing objects. `openpyxl` preserves the charts/images it can parse on that
  resave, but its tutorial warns it drops *shapes it cannot read* — refines the
  frozen RFC-0036's "never load-and-resave" / "drops charts" wording; see
  [RFC-0036 § Errata](../../rfc/0036-markdown-to-office-publishing.md#errata).

## Testing Strategy

- **Fill-point manifest enumeration** (docx undeclared variables; pptx
  placeholder `idx`/type/name map; xlsx named ranges + tables): **TDD** — a pure
  read over a fixture template with a compressible expected manifest.
- **Markdown → content-model mapping** (front-matter → scalars; H1/H2 →
  sections / slides / sheets; lists → loops / rows; tables → row-loops / table
  placeholder / data region): **TDD** — a pure transform, fixture in / model
  out.
- **Tier-1 `--check` probe** (exit `0` present / `2` absent): **goal-based
  check** — run the verb and assert the exit code; also covered by a unit test
  that monkeypatches the import.
- **End-to-end render per format**: **manual QA, exercised by an integration
  test** — invoke the skill's script as documented against a fixture template,
  then **re-open the produced `.docx`/`.pptx`/`.xlsx` and assert the filled
  values are present**. This satisfies the work-loop's "exercise the real built
  artifact" rule; asserting on the written file, not on internal model state, is
  mandatory.
- **Activation** (the right skill fires on natural phrasing): **manual QA via
  `evals/evals.json`** behavioral assertions per skill, **graded in a recorded
  manual pass at T4** (not merely a file that exists) — activation is the
  load-bearing risk of the three-skills decision (RFC-0036 §177), so the
  disambiguation of `markdown-to-docx`/`-pptx`/`-xlsx` descriptions is checked
  and the result recorded.
- **Output-path confinement** (write stays under the caller's working
  directory; symlink-escaping template/input paths refused): **TDD** — a unit
  test asserting an escaping `--output`/`--template` is rejected.
- **docx autoescape** (user content is escaped, not interpolated, in the
  Jinja-rendered docx): **TDD** — render a context containing `{{`/XML
  metacharacters and assert the output is escaped.
- **Pack lints, build, and marketplace refresh**: **goal-based check** — run
  `lint-packs`, `make build`, and assert `marketplace.json` reflects the new
  version.

## Acceptance Criteria

- [x] Three skills exist — `packs/converters/.apm/skills/{markdown-to-docx,markdown-to-pptx,markdown-to-xlsx}/` — each with a lean `SKILL.md` (detail in `references/`, the renderer in `scripts/`) that passes `tools/lint-skill-spec.py` and `tools/lint-agent-artifacts.py`.
- [x] Each `SKILL.md` `description` seeds the RFC-0036 activation vocabulary — both the noun keywords and the **imperative trigger phrasings** RFC-0036 §2 names (the load-bearing activation surface per §177): `markdown-to-docx` ("Word document", "report", "memo", "statement of work", "branded .docx", "turn this Markdown into a Word doc"); `markdown-to-pptx` ("PowerPoint", "slide deck", "presentation", "turn this into slides", "branded .pptx"); `markdown-to-xlsx` ("Excel", "spreadsheet", "workbook", "export this table to Excel", "fill the .xlsx template").
- [x] Each skill is **Tier-1**: `## Prerequisites` declares its library and the exact `pip install` line; the script's `--check` verb import-probes the library and exits `0` (present) / `2` (absent); on absence it prints the install line and stops; no code path auto-installs.
- [x] Each `SKILL.md` documents the **deterministic-renderer** contract — the script's argv shape and its stdout markers — and instructs the agent to assemble the content model and invoke the script, not to hand-write the Office file.
- [x] Each script's **inspect** verb emits a fill-point manifest: docx via `get_undeclared_template_variables()`; pptx by iterating `slide_layouts` → `placeholders` (idx, type, name); xlsx by iterating `defined_names` and worksheet `tables`.
- [x] Each script's **map** step projects the Markdown artifact onto the manifest per the RFC-0036 mapping table (front-matter → scalars; H1/H2 → sections/slides/sheets; lists → loops/rows; tables → row-loops/table-placeholder/data-region).
- [x] **Template flow** holds for all three: detect a template on disk → confirm the found one or elicit one → on explicit user opt-out, proceed **template-less using the library default** (a bare `docxtpl`/`python-pptx`/`openpyxl` document), communicated up front; the opt-out is never silent and no scaffold asset is shipped.
- [x] **No-fill-points guidance** for docx/xlsx: given an untagged `.docx` or a workbook with no named ranges, the skill explains how to add fill-points (insert Jinja tags in Word / define named ranges) rather than silently converting. `.pptx` is exempt — its layouts already carry placeholders.
- [x] `markdown-to-xlsx` injects into **data ranges only** and never manipulates or resizes chart/shape objects or a table/named-range extent; the shape-loss caveat (`openpyxl` preserves charts/images it can parse on the unavoidable resave but may drop shapes it cannot read) is documented in its `SKILL.md`. Refines RFC-0036's literal "never load-and-resave" wording — see [RFC-0036 § Errata](../../rfc/0036-markdown-to-office-publishing.md#errata).
- [x] `markdown-to-docx` documents the `docxtpl` run-fragmentation guidance — author each tag in one uniform run.
- [x] `markdown-to-docx` passes `autoescape=True` at the `docxtpl` `render()` call (autoescape is **off** by default in docxtpl), verified by a unit test that a context value containing `{{`/XML metacharacters renders escaped, not interpolated.
- [x] Each script **confines the output write**: it fully resolves `--output` with `Path.resolve()` / `realpath` (following symlinks) and verifies the resolved path is the working-directory root or has it among `.parents` — a path-**component** containment check, **not** a string-prefix check (so `workdir-evil` is rejected against root `workdir`) — refusing a `--template`/input path that resolves outside the root. Verified by unit tests covering the `..`-traversal, symlink-escape, and sibling-prefix (`workdir-evil`) cases.
- [x] Each `SKILL.md` states the **template trust posture explicitly** — user-supplied templates are treated as trusted-author input (consistent with the converters pack's local-files-trusted stance) — and notes that SSTI via a malicious template author and XXE / zip-bomb on a crafted Office archive are accepted, out-of-scope risks for trusted-author templates.
- [x] Each `## Prerequisites` `pip install` line names the **exact canonical PyPI package** (`docxtpl` / `python-pptx` / `openpyxl`) with a minimum-version floor (justified by the docxtpl `get_undeclared_template_variables()` breakage history and any known advisory at authoring time), and notes that these Tier-1 libraries install into the user's environment **outside the repo's SCA** so the user is responsible for keeping them current.
- [x] Each skill's **TDD unit suite** (`scripts/test_*.py`) covers manifest enumeration, Markdown→model mapping, and the `--check` probe, and is **CI-gated** by an explicit per-path `python -m pytest` line in `.github/workflows/build-check.yml` (atlassian/credential-brokers precedent).
- [x] An **end-to-end integration test per format** renders a fixture template via the documented script invocation and re-opens the produced file to assert the filled values are present.
- [x] Each skill ships `evals/evals.json` (canonical `skill_name` + `evals` keys) with activation and don't-render-by-hand assertions; the converters evals carry-over CI check (`build-check.yml`, "converters evals.json carry-over disposition") is extended to enumerate the three new skills.
- [x] The pack version is bumped `0.1.2 → 0.2.0` in both `packs/converters/pack.toml` and `packs/converters/.claude-plugin/plugin.json`; `[pack.adapter-contract]` stays `0.8`; `make build` refreshes the top-level `.claude-plugin/marketplace.json` to the new version; `lint-packs` and `make build` are green.
- [x] The pack's user-facing surfaces are updated to reflect the Markdown→Office direction: `packs/converters/README.md`'s skill list adds the three skills, and the `description` in `pack.toml` + `plugin.json` (which propagates into `marketplace.json`) names the outward direction — not just the current inward-only wording.
- [x] User docs land in the implementing PR: a new `docs/guides/converters/how-to/publish-markdown-to-office.md`, an extension to `docs/guides/converters/reference/converter-skills.md`, and a `docs/product/changelog.md` `[Unreleased]` entry.

## Assumptions

- Technical: Runtime is Python ≥3.11; deterministic render scripts are `.py` (source: `packages/agentbundle/pyproject.toml:9`; existing converters `scripts/`).
- Technical: `python-pptx` and `openpyxl` are MIT-licensed; `docxtpl` is **LGPL-2.1-only** — not "permissive" as RFC-0036's at-a-glance table states — but Tier-1 use (the user pip-installs it; the catalogue never bundles or redistributes it) imposes no license obligation on the catalogue (source: [python-pptx LICENSE](https://github.com/scanny/python-pptx/blob/master/LICENSE); [docxtpl PyPI](https://libraries.io/pypi/docxtpl), web lookup 2026-06-17).
- Technical: Tier-1 detection for a pip *library* is an import-probe, not `shutil.which` (source: `docs/guides/_shared/how-to/author-a-skill.md:131`).
- Technical: SKILL.md frontmatter is `name` + `description` (+ optional); body cap warns >500 / errors >1000 lines (source: `tools/lint-skill-spec.py`).
- Technical: a skill `scripts/` pytest suite is CI-gated only via an explicit per-path line (source: `.github/workflows/build-check.yml:166-184`); converters ships no script tests today.
- Process: RFC-0036 is Accepted; the spec follows it and an ADR is unnecessary (the RFC is the record) (source: RFC-0036 § Follow-on artifacts).
- Process: `converters` is user-scope-default → not projected into this repo's working tree, but a pack bump drifts top-level `marketplace.json`, which `make build` refreshes (source: RFC-0036 decision 6; repo convention).
- Product: the template-less fallback uses the **library default**, not a shipped neutral scaffold (source: user confirmation 2026-06-17).
- Process: the deterministic scripts carry TDD unit suites CI-wired by explicit per-path lines, *in addition to* behavioral `evals/evals.json` (source: user confirmation 2026-06-17).
- Product: v1 ships **three independent script sets**, no shared "office engine" (source: RFC-0036 Open Q1 default; user confirmation 2026-06-17).
- Security: user-supplied templates are **trusted-author input** — consistent with the converters pack's existing local-files-trusted stance (`packs/converters/.apm/skills/file-to-markdown/scripts/convert.py` disables its decompression-bomb guard for local files); SSTI-via-malicious-template and XXE / zip-bomb on crafted archives are accepted out-of-scope risks, documented per skill. Output-path confinement and docx autoescape are still enforced because they guard against model-influenced paths and accidental interpolation regardless of template trust (source: security-reviewer spec-stage pass 2026-06-17).
