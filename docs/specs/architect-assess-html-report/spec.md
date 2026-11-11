# Spec: architect-assess HTML report

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs/specs/architect-assessment/spec.md`](../architect-assessment/spec.md) — the saved `assessment.md` stays the source of truth and its section order is unchanged; this feature renders it and adds no analysis.
- **Brief:** none
- **Discovery:** none
- **Depends on:** spec:architect-assess-orientation-sections
- **Contract:** none — a local script and an output file; no API, event, or RPC contract.
- **Shape:** service — one stdlib script with a confined read and write, a skill mode that calls it, and the guidance around it.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`, `What
> Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working material.

## Outcome

A maintainer who asks `architect-assess` for an HTML report gets one self-contained file they can open offline, with the orientation sections in their saved order inside the current-state section, a sources-checked table beside each, and heat and evidence-class shading that makes the report scannable. The file runs no script and makes no network request, so text taken from the assessed repository cannot execute in the reader's browser.

## What Changes

- A stdlib-only renderer that turns `<effort-dir>/assessment.md` into `<effort-dir>/assessment.html` — `packs/architect/.apm/skills/architect-assess/scripts/render_html.py`.
- A co-located copy of the blessed confinement helper, loaded by path, with a byte-identity pin — `scripts/file_safety.py`.
- An HTML output mode in the skill and a reference that says when it runs and how its write is approved — `SKILL.md`, `references/html-report.md`, `references/output-layout.md`.
- Diagrams in the report appear as labeled source blocks; drawing them is a separate decision recorded in `notes/diagram-rendering-decision.md`.
- One eval case, the guide pages, and the release surface — `evals/evals.json`, `guides/architect/`, `pack.toml`, `plugin.json`, a changelog fragment.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Users need the mode, its offline guarantee, and its notice described | `guides/architect/reference/architecture-assessment.md`, `guides/architect/how-to/assess-a-repository.md` | eugenelim | page diff | pages name the mode and the script |
| Maintainer procedure | The pack design record counts one helper | `packs/architect/DESIGN.md` | eugenelim | diff naming the second script | record matches the shipped scripts |
| Decision rationale | Diagram drawing is deferred with measured facts | `notes/diagram-rendering-decision.md` | eugenelim | file | the next slice cites it |
| Release history | A pack change ships by version bump | `pack.toml`, `plugin.json`, changelog fragment | eugenelim | parity test, fragment validates | bump above fetched main, `Highlights` decided |

## Agent Rules

### Always do

- Treat every byte of `assessment.md` as untrusted, including text the model wrote after reading the repository.
- Cite `references/output-layout.md` for destination and write approval rather than restating it.

### Ask first

- Any `<script>` element in the output, which belongs to the diagram-rendering decision. Exception: with `--diagrams`, which `docs/specs/architect-assess-html-diagrams/spec.md` owns.
- Raising the source-size cap or the page-size cap.

### Never do

- Load script, style, font, or image from a network location. Exception: with `--diagrams`, which `docs/specs/architect-assess-html-diagrams/spec.md` owns.
- Add a third-party dependency, a vendored third-party asset, or a subprocess call. The co-located helper copy is pack-owned code, not a vendored asset. Exception: with `--diagrams`, which `docs/specs/architect-assess-html-diagrams/spec.md` owns.
- Edit another skill to make this mode work.

## Testing Strategy

- Resource bounds (time on hostile inputs, peak memory on one unterminated link target): TDD with a time bound and a `tracemalloc` bound.
- Escaping, links, structure, banners, gate, shading, CSP, source blocks, size caps (source and page): TDD, because each is a pure input-to-output rule with a hostile-corpus oracle.
- Confinement, imports, UTF-8, helper identity: goal-based check, a test that exercises a symlinked path, hides `agentbundle` in-process, parses the script's imports and calls, and compares the helper copy byte for byte. Tests load the script under a module name unique to its pack and skill.
- Real-browser rendering: manual QA, because only a browser applies the CSP and the styling.
- Skill routing and the eval: goal-based check through the contract tests and one eval case.

## Acceptance Criteria

- [x] `render_html.py <effort-dir>` reads `<effort-dir>/assessment.md`, writes exactly one file, `<effort-dir>/assessment.html`, and exits 0.
- [x] When `<effort-dir>/assessment.html` already exists as a regular file of at most 16 MiB, the renderer replaces it with the new render.
- [x] When an existing `<effort-dir>/assessment.html` is larger than 16 MiB, the renderer exits 3 and leaves it unchanged.
- [x] A fixture report's headings, bullet lists, tables, fenced code, bold, and inline code appear as `<h2>`, `<ul>`, `<table>`, `<pre>`, `<strong>`, and `<code>` elements.
- [x] A Markdown link whose target begins `https:`, `http:`, or `#` after trimming and lowercasing, and to which none of the exclusions below applies, is emitted as an `<a href>` element.
- [x] A Markdown link with a whitespace character inside its target, after trimming leading and trailing whitespace, is emitted as text with no `<a>` element.
- [x] A Markdown link with a character of Unicode general category Cc or Cf in its text or its target is emitted as text with no `<a>` element.
- [x] A Markdown link whose target nests parentheses two or more levels deep is emitted as text with no `<a>` element.
- [x] A Markdown link whose target, trimmed and lowercased, begins with any other scheme or with no scheme is emitted as text with no `<a>` element.
- [x] Every value that comes from the report or from the effort-directory path appears in the output only as escaped text, including values placed in `<title>` and in the metadata block.
- [x] A raw `<script>`, an `<img onerror>`, and a `"` attribute breakout in the source each appear in the output as escaped text.
- [x] Every element in the parsed output is one of the elements that [`architect-assess-html-report-style`](../architect-assess-html-report-style/spec.md) lists, and that spec owns the list.
- [x] Every attribute in the parsed output is one of the attributes that [`architect-assess-html-report-style`](../architect-assess-html-report-style/spec.md) lists, and that spec owns the list.
- [x] The body of the output's `<style>` element contains neither `@import` nor `url(`.
- [x] The output has exactly two `meta` elements, `meta charset` first and the `Content-Security-Policy` meta second, both before the `title` and `style` elements.
- [x] The CSP's `default-src`, `base-uri`, and `form-action` are `'none'`.
- [x] The CSP's `style-src` is `'sha256-<digest>'` and the digest equals the base64 encoding of the sha256 of the UTF-8 bytes of the single `<style>` body in the same file.
- [x] A report with an `Overall architecture`, `Architecture by subsystem`, or `Physical architecture` subsection whose last block is not a `Sources checked:` label followed by a table with the header cells `Source`, `Locator`, `Evidence class`, `Limit` makes the renderer exit 2, print that subsection's canonical heading on stderr, and write no file.
- [x] A subsection whose `Sources checked` table has no data row makes the renderer exit 2, print the canonical heading on stderr, and write no file.
- [x] A subsection that begins `not assessed` and ends with a `Sources checked` table with at least one data row renders and exits 0.
- [x] A report with none of the three subsections renders and exits 0.
- [x] Each `Sources checked` row's evidence class, compared case-insensitively after trimming, renders as an element with class `ev-observed`, `ev-inferred`, `ev-reported`, or `ev-unknown`.
- [x] A `Sources checked` row whose evidence class is outside those four makes the renderer exit 2, state the reason on stderr, and write no file.
- [x] Each cell under the heat map headers `Consequence`, `Pressure`, `Concentration / coupling`, `Verification weakness`, and `Ops/data/security exposure`, with text `low`, `medium`, `high`, or `unknown` compared case-insensitively after trimming, carries class `heat-low`, `heat-medium`, `heat-high`, or `heat-unknown`.
- [x] A heat map cell under any other header, including `Confidence`, carries no `heat-` class.
- [x] Unless the `## Assessment charter` section, outside any fenced block, holds exactly one `Checkpoints:` line and its value is exactly `confirmed`, an element with class `banner-unconfirmed` containing `Map and hotspot set not user-confirmed` precedes the first section.
- [x] When that line is present once with the value `confirmed`, the output contains no `banner-unconfirmed` element, even if the same line appears elsewhere in the report.
- [x] A `Checkpoints: confirmed` line placed only outside the charter section does not suppress the banner.
- [x] Each Mermaid fence appears as a `<pre>` under the visible label `Diagram source (not rendered)`, with its text escaped. Exception: with `--diagrams`, which `docs/specs/architect-assess-html-diagrams/spec.md` owns.
- [x] Every report carries an element with class `notice-untrusted` containing `Unverified: built from repository text and model analysis; not redacted`.
- [x] Every report records the name of the effort directory, the generation date in ISO 8601 `YYYY-MM-DD` UTC, and the value of the script's `RENDERER_VERSION` constant.
- [x] The renderer's exit code is 0, 2, or 3 on every path, and a missing source, a missing or non-directory effort path, and any unexpected exception exit 3 while a wrong argument count exits 2.
- [x] On every path, stdout and stderr carry only tokens from a fixed set in the script and never text taken from the source or the path.
- [x] A rendered page larger than 16 MiB of UTF-8 bytes, measured before the write, makes the renderer exit 2, print a fixed token on stderr, and write no file.
- [x] A source that is not valid UTF-8 makes the renderer exit 2 and write no file.
- [x] A regular source larger than 2 MiB of raw bytes read makes the renderer exit 2 and write no file.
- [x] A source that fails confinement exits 3 whatever its size.
- [x] Given a symlinked `assessment.md`, a symlinked `assessment.html`, or a symlink in any component of the effort directory path exactly as supplied, the renderer exits 3 and writes nothing.
- [x] Before reading or writing, the renderer checks that `os.open`, `os.stat`, and `os.rename` are in `os.supports_dir_fd`, `os.stat` is in `os.supports_follow_symlinks`, and `os.O_DIRECTORY` and `os.O_NOFOLLOW` exist; when any check fails it exits 3 naming that reason and writes nothing.
- [x] `scripts/file_safety.py` equals `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py` byte for byte.
- [x] The renderer reads, writes, and succeeds with `agentbundle` not importable.
- [x] Every import in `render_html.py` is one of `argparse`, `base64`, `datetime`, `hashlib`, `html`, `importlib.util`, `os`, `pathlib`, `re`, `stat`, `sys`, `typing`, `unicodedata`, and the file calls no `os` attribute named `system`, `popen`, `fork`, `posix_spawn`, or beginning `spawn` or `exec`.
- [x] On a 400 KB source made of one line holding an unterminated `[a](` followed by text with no closing parenthesis and no newline, `render` peaks under 16 MiB of `tracemalloc` memory.
- [x] `render` completes in under 3 seconds on each of these hostile inputs: a heading line followed by 300,000 spaces and a letter; one line of 300,000 `[`; one line of 60,000 repetitions of `[a](`; a table header, a separator row, and 300,000 spaces; 30,000 identical `## a` headings; a list item followed by 500,000 indented continuation lines.
- [x] The script sets stdout and stderr to UTF-8 before its first print.
- [x] `SKILL.md` names the HTML mode and `scripts/render_html.py`, states that it runs only on a user request, and states that with no saved `assessment.md` it offers to save one first and runs nothing.
- [x] `references/html-report.md` states that the renderer takes the resolved effort-directory path, and that hosts without descriptor walking, Windows included, get exit 3 and no report.
- [x] `references/html-report.md` lists every exit 2 reason: a wrong argument count, an orientation subsection without a usable table, an evidence class outside the set, a source over 2 MiB, a source that is not UTF-8, and a rendered page over 16 MiB. Exception: with `--diagrams`, which `docs/specs/architect-assess-html-diagrams/spec.md` owns.
- [x] `evals/evals.json` contains a case whose prompt asks for an HTML report and whose assertion checks the output contains a `Sources checked` table.
- [x] `guides/architect/reference/architecture-assessment.md` and `guides/architect/how-to/assess-a-repository.md` each name the HTML mode.
- [x] `packs/architect/DESIGN.md` states that the pack ships a second standard-library script and names it.
- [x] `pack.toml` and `.claude-plugin/plugin.json` carry the same version, one patch above the version on fetched main.
- [x] `tools/changelog.py validate` passes with the new fragment present.
- [x] Opened in a real browser, a sample report shows shaded heat cells and evidence badges, and a hostile sample shows its planted markup as visible text with no script run. Exception: with `--diagrams`, which `docs/specs/architect-assess-html-diagrams/spec.md` owns.

## Terminal Intent

`code` — add the renderer, its helper copy, the skill mode, evals, guides, and the release surface.

## Follow-ons

- eugenelim: [`notes/diagram-rendering-decision.md`](notes/diagram-rendering-decision.md) — decide how diagrams are drawn in the browser; a later spec carries the choice.

## Assumptions

- Technical: a source under the 2 MiB cap can render past 16 MiB — a 2 MiB table row of single pipe characters under a one-column header renders to about 18 MiB (settled by: measurement; the page-cap criterion bounds it).
- Product: a report saved before the `Checkpoints:` field existed shows the unconfirmed banner `Map and hotspot set not user-confirmed` — whether that is acceptable (settled by: the owner).

## Changelog

<!-- Approvals only. -->

- 2026-10-30: spec approved by eugenelim
- 2026-10-30: spec approved by eugenelim (amended link, output-size, resource-bound, and exit-code criteria)
