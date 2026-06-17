# RFC-0036: Markdown → Office publishing skills for the `converters` pack

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-17
- **Date closed:** 2026-06-17
- **Related:** RFC-0007 (`converters` — first user-scope pack; the home) · RFC-0004 (install-scope per pack — the user-scope dimension `converters` uses) · `file-to-markdown` (the inverse direction — Office→Markdown; the Tier-1 pip detect-and-stop precedent) · `markdown-to-html` (the deterministic-script "you are not the renderer" idiom) · `mermaid-renderer` (the Tier-1 `--check` reference) · `docs/guides/_shared/how-to/author-a-skill.md` (the 3-tier dependency model) · `docs/CHARTER.md` (the four principles)

---

## The ask

**Recommendation (BLUF).** Add **three skills to the existing `converters` pack** — `markdown-to-docx`, `markdown-to-pptx`, `markdown-to-xlsx` — that **fill a user-provided, branded Office template** (Word / PowerPoint / Excel) from a Markdown artifact to publish a distribution-ready document. Use the **template-fill** approach (inject content into a pre-branded file at its fill-points), **not** convert-from-Markdown, because only template-fill preserves a corporate brand intact. Each skill is **Tier-1** on its library (`docxtpl` / `python-pptx` / `openpyxl`): declare, detect, fail clean — mirroring `file-to-markdown`. RFC now; the skills are built as a follow-on spec once accepted.

**Why now (SCQA).**
- *Situation.* The `converters` pack already turns Office documents *into* Markdown (`file-to-markdown`, via Docling) and Markdown into styled HTML (`markdown-to-html`). Agents routinely produce Markdown artifacts — reports, specs, summaries, decks-as-outlines.
- *Complication.* There is no path from a Markdown artifact back out to a **branded** `.docx` / `.pptx` / `.xlsx` for distribution. The round-trip is half-built: content goes in, but nothing comes out in the format a stakeholder expects to receive. Ad-hoc Pandoc conversion exists but cannot honour a designed cover page, a placed logo, or a corporate master.
- *Question.* Should the catalogue carry Markdown→Office publishing as skills, in a shape that preserves a brand the user owns and fits the pack's existing dependency and authoring discipline?

**Decisions requested** (each: recommended option · decide-by = on circulation close):

1. **Add the skills at all** → *yes, in `converters`* (vs do-nothing / a new dedicated Office pack / fold into `core`).
2. **Approach** → *template-fill* (inject into a pre-branded file), **not** convert-from-Markdown (Pandoc/Quarto reference-doc).
3. **Granularity** → *three per-format skills* (`markdown-to-docx`, `markdown-to-pptx`, `markdown-to-xlsx`), not one unified skill.
4. **Template handling** → *detect a template on disk → confirm the detected one (or elicit one if none found) → the user may explicitly confirm "no template" as a fallback (proceed template-less)*; each skill **inspects** the provided template to emit a fill-point manifest, then **maps** Markdown onto it.
5. **Dependency tier** → *Tier 1* (declare/detect/fail-clean) on `docxtpl` / `python-pptx` / `openpyxl`, mirroring `file-to-markdown`.
6. **Scope** → *all three formats in v1*; PDF export and a slide visual-QA loop are **non-goals** (named follow-ons).
7. **User docs** → *update the `converters` guide* (a new how-to + the reference page) and the changelog, as a **follow-on** at implementation (the skills don't exist yet).

---

## Problem & goals

**Problem (diagnosis).** An agent that has produced a polished Markdown artifact has no supported way to hand a stakeholder the artifact in the Office format they expect *and* on the organisation's brand. The two existing escape hatches both fail the real requirement:

- **Convert-from-Markdown** (Pandoc/Quarto with a `--reference-doc`) maps Markdown to *named styles* and copies headers/footers, but the converter owns the output structure — it cannot place content into a designed cover page, a positioned logo block, or a corporate slide master. Pandoc has no variable/placeholder substitution into a designed `.docx` at all; a feature request (#5268, closed) documents the gap.
- **Hand-coding** each document with the low-level library is enormously expensive to maintain and re-derives the brand in code.

The expensive failure is an off-brand or structurally-flat deliverable that a person then has to reformat by hand — which defeats the point of generating it.

**Goals.**
- A path from a Markdown artifact to a **distribution-ready** `.docx` / `.pptx` / `.xlsx` that **preserves a brand the user owns**, for all three formats.
- The **user supplies the template**; the skill never invents a brand. When no template is on hand, the skill asks; the user may consciously opt out of branding.
- Fits the `converters` pack's existing discipline: the **3-tier dependency model** (Tier 1 here) and the **deterministic-script idiom** ("you are not the renderer; the script is").
- Activation-optimised so the right skill fires on natural phrasing ("turn this into a PowerPoint", "make a branded Word report", "export to an Excel spreadsheet").

**Non-goals** (could-have-been goals, deliberately dropped).
- **Not** convert-from-Markdown (Pandoc/Quarto). Considered and rejected as the *primary* approach (Options, Axis A); it stays a legitimate lighter alternative for the brand-indifferent case, but this RFC does not ship it.
- **Not** PDF export. "Publish for distribution" is satisfied by the Office file; PDF needs LibreOffice headless — a heavy system dependency with documented font-substitution fidelity caveats — and is a named follow-on, not v1.
- **Not** a slide **visual-QA loop** (render → image → inspect for overflow/branding). Valuable, but it pulls in LibreOffice + a PDF rasteriser; follow-on.
- **Not** a bundled default brand / template library. The skill ships no corporate template; an absent template is the user's explicit choice, not a silent default.
- **Not** authoring the template. Producing the branded template (and, for Word/Excel, placing its fill-points) is the user's job; the skill inspects and guides, it does not design.

---

## Proposal

### At a glance

| Dimension | Decision |
|---|---|
| **Home** | Three skills added to the existing **`converters`** pack (user-scope-default, `allowed-scopes = ["user","repo"]`). Completes the pack's Office round-trip. |
| **Skills** | `markdown-to-docx` · `markdown-to-pptx` · `markdown-to-xlsx` (3 skills). |
| **Approach** | **Template-fill**: inject Markdown-derived content into a pre-branded file at its fill-points. |
| **Libraries** | `docxtpl` (.docx) · `python-pptx` (.pptx) · `openpyxl` (.xlsx). All PyPI, permissive licences. |
| **Dependency tier** | **Tier 1** — declare in `## Prerequisites`, detect via an import-probe `--check`, print the `pip install` line and stop. No auto-install. |
| **Template flow** | Detect on disk → confirm / elicit → optional explicit "no template" fallback. Inspect-then-map. |
| **Render idiom** | Deterministic script renders; the agent assembles the content model and invokes the script. |
| **Out of scope** | PDF export; slide visual-QA loop; bundled brand templates (all named follow-ons / non-goals). |

### 1. Approach — template-fill, not convert (decisions 2)

Two paradigms exist, and the choice governs everything else. **Convert** (Pandoc/Quarto) lets the converter own the output structure; the template supplies only named styles. **Template-fill** lets the *branded file* own layout and branding; the tool injects content at the file's fill-points, so a designer's cover page, logo placement, and master slides survive intact. For a *distribution-ready, on-brand* deliverable, template-fill is the only approach that preserves a brand the user owns. Convert remains a legitimate lighter option when the brand is modest (Axis A) — but it is explicitly not what v1 ships.

### 2. Three per-format skills (decision 3)

The three formats use **three different libraries with three different fill-point models** (below) and are reached for by **different natural phrasings**. Splitting them gives the sharpest activation — "turn this into a PowerPoint" should trigger exactly one skill, not a unified skill that then branches — and matches the pack's existing one-skill-per-job idiom (`file-to-markdown`, `markdown-to-html`, `mermaid-renderer`, `msg-to-markdown`). Anthropic's authoring guidance is explicit that the **`description` field carries discovery** ("Claude uses it to choose the right Skill … Be specific and include key terms"), so the names stay consistent with the pack's `markdown-to-<target>` convention while each **description** seeds the trigger vocabulary:

- `markdown-to-docx` — "Word document", "report", "memo", "statement of work", "branded .docx", "turn this Markdown into a Word doc".
- `markdown-to-pptx` — "PowerPoint", "slide deck", "presentation", "turn this into slides", "branded .pptx".
- `markdown-to-xlsx` — "Excel", "spreadsheet", "workbook", "export this table to Excel", "fill the .xlsx template".

### 3. Template handling — detect → confirm/elicit → optional opt-out (decision 4)

A user-provided template is the source of truth for branding, but the skill must not assume one is at hand, nor silently proceed without one. The flow:

1. **Detect on disk.** Look for a template the user named, or a conventional candidate in the working directory (a `.docx`/`.pptx`/`.xlsx` matching the target format).
2. **Confirm or elicit.** If a candidate is found, confirm it with the user before using it. If none is found, ask the user to provide one.
3. **Optional opt-out fallback.** The user may explicitly confirm "no template" — the skill then proceeds **template-less** (an unbranded document; exact shape per Open question 3), clearly communicated, rather than hard-blocking. This is a conscious choice, never a silent default.

### 4. The fill-point model and the Markdown→template mapping (decision 4, cont. — the load-bearing mechanic)

**Do we expect placeholder sections to be listed in the template?** Yes — and the mechanism differs per format. This is the single design point that, if mishandled, sinks the skill. Each library's contract is primary-sourced:

| Format | Fill-points are… | Must pre-exist in the template? | How the skill enumerates them |
|---|---|---|---|
| **.docx** (`docxtpl`) | Jinja2 tags authored in Word (`{{ var }}`, `{%p for %}`, `{%tr for %}`, `{%tc %}`, `{%r %}`) | **Yes** — docxtpl renders tags that are already in the document; it cannot inject tags into an untagged file | `tpl.get_undeclared_template_variables()` → the declared variable set |
| **.pptx** (`python-pptx`) | Layout placeholders, addressed by `placeholder_format.idx` (dict-like keying, **not** list position) | **Effectively no** — every slide layout already exposes placeholders, inherited onto added slides; you map onto existing ones | iterate `prs.slide_layouts` → `layout.placeholders` (idx, type, name) |
| **.xlsx** (`openpyxl`) | Named ranges and/or Excel Tables | **Yes** — they must be defined in the workbook beforehand | iterate `wb.defined_names` and `ws.tables` |

So the skill follows an **inspect-then-map** contract:

1. **Inspect** the provided template and emit a **fill-point manifest** (the declared variables / placeholder-idx map / named ranges).
2. **Map** the Markdown artifact onto that manifest:
   - **YAML front-matter → scalars** (title, author, date) → `{{ var }}` tags / single-cell named ranges / title placeholders.
   - **H1/H2 sections** → docx paragraph blocks / **one `.pptx` slide per section** (layout chosen per section) / an `.xlsx` sheet or table anchor.
   - **Lists** → docx `{%p for %}` loops / bullet rows / table rows.
   - **Markdown tables** → docx `{%tr for %}` row loops / a `.pptx` `TABLE`-type placeholder / an `.xlsx` Table data region.
3. **Guide-the-user fallback for docx/xlsx:** if a provided template has **no** fill-points (an untagged `.docx`, a workbook with no named ranges), the skill explains how to add them (insert Jinja tags in Word / define named ranges) rather than silently converting. `.pptx` needs no pre-tagging — its layouts already carry placeholders.

`python-pptx` has **no Markdown awareness**, so the parse-and-map step (Markdown AST → runs) is owned by the skill's deterministic script; the agent assembles the content model, the script renders. This keeps the pack's "you are not the renderer" idiom.

### 5. Dependency tier — Tier 1 (decision 5)

`docxtpl`, `python-pptx`, and `openpyxl` are PyPI libraries. The closest sibling — `file-to-markdown`, also pip-based, also Office-documents — is **Tier 1**: it declares the dependency in `## Prerequisites`, detects it (import-probe), prints the `pip install` line, and **stops** rather than installing. These three skills follow the same pattern: a `--check` verb that probes the import and exits `0` (present) / non-zero (absent). No auto-install (that would be Tier 2; reserved, not used). This matches Anthropic's "avoid assuming tools are installed — list required packages and verify they're available."

### 6. Packaging & registration (follow-on shape)

The three skills are pure additions to `converters/.apm/skills/`. A skills addition is a feature, so the pack version bumps (`pack.toml` + `.claude-plugin/plugin.json`); `converters` is user-scope-default, so it is not projected into this repo's working tree but **must** refresh in the top-level `marketplace.json` (the build does this). Each skill follows progressive disclosure — a lean `SKILL.md`, detail in `references/`, the renderer in `scripts/`. No `seeds/`, no hooks (the pack's user-scope refusal rails pass by construction).

---

## Options considered

**Axis A — approach** (MECE along *where layout & branding authority lives*; prior art: Pandoc/Quarto reference-doc vs the python template-fill libraries):

| Option | Prior art | Trade-off |
|---|---|---|
| Convert-from-Markdown (Pandoc/Quarto `--reference-doc`) | Pandoc, Quarto | Cheap, CI-friendly; **converter owns structure** → cannot honour a designed cover page / placed logo / slide master; no placeholder substitution into a designed docx (#5268). Loses the brand requirement. |
| **Template-fill** ★ | `docxtpl`, `python-pptx`, `openpyxl` | Branded file owns layout; injects at fill-points → brand survives intact. Cost: a structured content model + per-template fill-point wiring. |
| Hybrid (convert body + post-process headers/cover) | documented production pipelines | Highest fidelity for the hardest cases; far more moving parts (Pandoc + a filter + a post-processor). Over-built for v1. |

**Axis B — home** (MECE along *where it lives, including not-at-all*):

| Option | Prior art | Trade-off |
|---|---|---|
| Do-nothing (stay ad hoc) | status quo | Zero cost; the Office round-trip stays half-built, every agent re-invents brittle Pandoc invocations, no branded path. Cost of delay: recurring off-brand deliverables. |
| **Three skills in `converters`** ★ | RFC-0007; `file-to-markdown` is the inverse direction | Completes the pack's Office round-trip; reuses its dependency + authoring discipline; one familiar pack to install. |
| New dedicated Office pack | per-domain packs | A whole pack for three sibling skills is heavier than warranted and fragments the converters story. |
| Fold into `core` | `core` universal layer | Forces Office tooling onto every repo; fails opt-in and "substantive-not-duplicative" for non-Office projects. |

**Axis C — granularity** (MECE along *number of activation units*):

| Option | Verdict |
|---|---|
| One unified `markdown-to-office` skill | Rejected — one description must carry three formats' triggers; branches internally; weaker activation. |
| **Three per-format skills** ★ | Sharpest activation; three genuinely different libraries/fill-models; matches the pack's one-skill-per-job idiom. |
| Three skills + a shared "office engine" module | Premature abstraction for v1 — extract a shared helper only if real duplication appears (Open question 1). |

**Axis D — template provisioning** (MECE along *who supplies the template and what happens when it's absent*):

| Option | Trade-off |
|---|---|
| Require a pre-tagged template, hard-block if absent | Safest for brand fidelity but brittle — blocks a user who has no template yet and just wants output. |
| Bundle a default brand template | Convenient but ships an opinionated brand the skill has no business owning; off-brand-by-default. Rejected (and a non-goal). |
| **Detect on disk → confirm/elicit → explicit no-template opt-out** ★ | Uses the user's brand when present; asks when unsure; lets the user consciously go unbranded. No silent default. |

**Axis E — dependency tier** (MECE along the 3-tier model in `author-a-skill.md`): **Tier 1 — declare/detect/fail-clean** ★ [mirrors `file-to-markdown`; pip libs; no surprise installs] · Tier 2 — gated idempotent install [allowed but heavier than the closest sibling warrants] · Tier 3 — banned [N/A].

---

## Risks & what would make this wrong

**Pre-mortem (top failure modes + mitigations).**
- *A user-provided template isn't fill-ready* (an untagged `.docx`, a workbook with no named ranges) — the skill has nothing to fill. **This is the riskiest assumption — spiked below.** → Inspect-then-map (decision 4): the skill detects the absence of fill-points and *guides the user to add them* rather than failing opaquely or silently converting. `.pptx` is exempt (layouts carry placeholders).
- *`python-pptx` has no Markdown ingestion* → ad-hoc, inconsistent slide text. → The deterministic script owns the Markdown-AST→runs mapping; the agent only assembles the content model.
- *`openpyxl` drops charts/images on load-and-save* (documented). → Inject values into the **data ranges** the template's charts read; never load-and-resave the chart objects. Document this in the skill.
- *`docxtpl` run-fragmentation / XML-escaping pitfalls* → corrupted output. → Skill guidance: author each tag in one uniform run; enable autoescape for user content.
- *The template-less fallback produces an ugly unbranded doc the user didn't expect* → The fallback is reached **only** on explicit user opt-out, and the unbranded result is communicated up front.
- *Scope creep into PDF/visual-QA* → Hard non-goals; named follow-ons.
- *Tier-1 friction* (user must `pip install` before first run) → Accepted; identical to `file-to-markdown`, and the `--check` verb makes the missing-dependency message actionable.

**Key assumptions (falsifiable).**
- *Template-fill preserves a real corporate brand where convert cannot.* Falsifiable if a reference-doc Pandoc run on a genuine corporate template proves indistinguishable — research and the libraries' design say otherwise.
- *Fill-points must pre-exist for `.docx` and `.xlsx`; `.pptx` layouts already carry them.* Primary-sourced and confirmed (Evidence). Falsifiable only if the libraries change their model.
- *Three skills beat one for activation.* A judgment call; the observable falsifier is wrong-skill-fired / mis-activation reports (the wrong format skill triggers, or none does on a clear "make this a PowerPoint" prompt) — absent that signal it stays an unmeasured judgment call.
- *Tier 1 is the right tier.* Falsifiable if the install friction proves a real adoption barrier and a gated Tier-2 install is wanted.

**Drawbacks (not "none").** Three skills is three SKILL.md surfaces, three reference sets, and three dependencies to track in `converters` (which today carries none of these three libraries). The template-fill approach pushes real work onto the user — they must own a template and, for Word/Excel, place its fill-points — which is a steeper on-ramp than "paste Markdown, get a styled HTML page" (`markdown-to-html`). And the skills are only as good as the template they're handed; a badly-built template yields a badly-filled document, and the skill can guide but not fix that.

---

## Evidence & prior art

**Spike / de-risk (riskiest assumption: is a user-provided template fill-ready?).** No code spike was needed — the three libraries' contracts settle it definitively from primary docs, and the consequence is designed into decision 4:
- `docxtpl`: tags must be authored into the `.docx` in Word beforehand; the library cannot inject them. The declared set is enumerable (`get_undeclared_template_variables()`). → docx needs a pre-tagged template; the skill inspects for tags and guides if none.
- `python-pptx`: placeholders are addressed by `idx` (dict-like keying, not position) and every layout already exposes them; adding a table/chart/picture *replaces* the placeholder element, invalidating the original reference. → pptx is fill-ready by construction; the skill enumerates layouts/placeholders, and uses the returned object after each insert.
- `openpyxl`: named ranges / Excel Tables must be defined in the workbook beforehand; and `openpyxl` does **not** read all items, so shapes/charts are lost on a load-and-resave. → xlsx needs pre-defined ranges; the skill injects into data ranges only.
**Spike verdict:** the fill-readiness gap is real for docx/xlsx and absent for pptx; the inspect-then-map + guide-the-user design closes it. This is why decision 4 is the load-bearing mechanic, not an afterthought.

**Repo precedent.**
- RFC-0007 (`converters`) — the pack this extends; first user-scope pack; ships no `seeds/`, no hooks (the refusal rails this addition passes by construction).
- `file-to-markdown` — the **inverse** direction (Office→Markdown via Docling); the **Tier-1 pip detect-and-stop** precedent these skills mirror; adding the forward direction completes the round-trip.
- `markdown-to-html` — the deterministic-renderer idiom ("you are not the renderer; the script is") and the closest "Markdown in, formatted artifact out" sibling.
- `mermaid-renderer` — the Tier-1 reference (`## Prerequisites` + a `--check` verb + an explicit don't-auto-install rule).
- `docs/guides/_shared/how-to/author-a-skill.md` — the 3-tier dependency model decision 5 applies; the `stdlib > pip > npm` preference (these are pip).
- `docs/CHARTER.md` — the four principles; the skills clear them (universal task; substantive, not duplicative; a habit; reached for whenever a branded deliverable is produced).

**External prior art** (✓ = fetched and confirmed by the author).
- ✓ **docxtpl docs** — "as you are still editing the document with microsoft word, you insert jinja2-like tags directly in the document"; documents `render(context)` and `get_undeclared_template_variables()`. Grounds the docx fill-point model and enumeration. ([docxtpl](https://docxtpl.readthedocs.io/en/stable/))
- ✓ **python-pptx — Working with placeholders** — "Item access on the placeholders collection is like that of a dictionary rather than a list … the lookup is on idx values, not position"; a reference becomes invalid after `insert_picture()` because the element is replaced; an example "assumes a starting presentation … having a table placeholder with idx 10," i.e. the template must already contain the placeholder. Grounds the pptx fill-point model. ([python-pptx](https://python-pptx.readthedocs.io/en/latest/user/placeholders-using.html))
- ✓ **openpyxl tutorial** — "openpyxl does currently not read all possible items in an Excel file so shapes will be lost from existing files if they are opened and saved with the same name." Grounds the inject-into-data-ranges-only mitigation. ([openpyxl](https://openpyxl.readthedocs.io/en/stable/tutorial.html))
- ✓ **Anthropic — Agent Skills authoring best practices** — "Avoid assuming tools are installed … List required packages in your SKILL.md and verify they're available"; the Claude API "has no network access and no runtime package installation"; the `description` "is critical for skill selection … Be specific and include key terms"; covers DOCX (docx-js/OOXML) and Excel skill patterns. Grounds decisions 3 (activation via description) and 5 (Tier-1 declare/verify). ([best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices))
- ✓ **Anthropic — Equipping agents with Agent Skills** — a skill is "a directory containing a SKILL.md file" with required `name`/`description` frontmatter; progressive disclosure loads bundled files only when needed; ships a public PDF document skill (`anthropics/skills/document-skills/pdf`). Grounds the skill packaging shape. ([engineering blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills))
- ✓ **Pandoc issue #5268 — "docx full template support"** — the reporter notes the reference doc carries styles (and, in practice, headers) but requests **variable substitution** for docx generation; the request (opened Feb 2019) documents that placeholder substitution into a designed docx is **not** native to Pandoc. (Issue is closed; cited for the documented gap, not its status.) Grounds the convert-loses-branding finding in Axis A. ([#5268](https://github.com/jgm/pandoc/issues/5268))

---

## Open questions

1. **Shared "office engine" vs three independent script sets.** The three skills share a content-model parse step but diverge sharply at render. *Default:* independent per-skill scripts in v1; extract a shared helper only if real duplication appears (the `author-a-skill` "inline until a second caller appears" rule). *Owner:* eugenelim. *Decide-by:* spec authoring.
2. **`converters` version bump + adapter-contract level.** Adding skills is a feature → a `pack.toml` + `plugin.json` version bump and a `marketplace.json` refresh; the `[pack.adapter-contract]` level (currently `0.8`) stays unless a primitive shape changes. *Default:* minor bump, contract unchanged. *Owner:* eugenelim. *Decide-by:* spec authoring.
3. **Exact template-less fallback output.** When the user opts out of a template, what does the unbranded result look like — the library default, or a minimal neutral scaffold the skill ships as an asset? *Default:* genuinely open between the library default and a minimal neutral scaffold — resolve at spec authoring; no bundled corporate brand either way. *Owner:* eugenelim. *Decide-by:* spec authoring.

---

## Follow-on artifacts

Filled in on acceptance:
- **Spec:** `docs/specs/markdown-to-office-publishing/` (via `new-spec`) — the three skills, each with a lean `SKILL.md` + `references/` + a deterministic render `scripts/` entry; the `## Prerequisites` Tier-1 `--check` verb; the detect→confirm→elicit→opt-out template flow; the inspect-then-map fill-point manifest + Markdown mapping; the `converters` version bump + `marketplace.json` refresh; activation-tuned names/descriptions.
- **User docs (decision 7):** a new `docs/guides/converters/how-to/publish-markdown-to-office.md`, an extension to `docs/guides/converters/reference/converter-skills.md`, and a `docs/product/changelog.md` `[Unreleased]` entry — authored in the implementing PR alongside the skills.
- **Possible ADR** — only if the template-fill-over-convert choice warrants a durable architectural record beyond this RFC; likely unnecessary (this RFC is the record).

## Errata

Post-acceptance corrections recorded against this frozen RFC (the original
decisions stand; these refine imprecise wording surfaced during
implementation).

- **E1 — `openpyxl` chart/shape preservation (2026-06-17, implementing PR; Approver: eugenelim).**
  The Risks/library-notes wording (this RFC's "*openpyxl drops charts/images on
  load-and-save*" / "**never load-and-resave the chart objects**") diverges from
  observed behavior: `openpyxl` 3.1.x **preserves** the charts and images it can
  parse through a load-and-resave, and the loss its own tutorial documents is of
  **shapes it cannot read**. Filling named ranges / Excel Tables *inherently*
  requires a `load_workbook` + `save`, so a literal "never load-and-resave" rule
  is unrealizable. The **decision is unchanged** — *inject into data ranges only;
  never manipulate, recreate, or resize chart/shape objects or a range's extent*
  — which is exactly what `markdown-to-xlsx` implements and what preserves a
  chart that reads a filled range. The implementing spec's Boundary and AC carry
  the corrected wording and the `SKILL.md` documents the accurate
  shape-loss caveat. No change to the proposal's mitigation intent.
