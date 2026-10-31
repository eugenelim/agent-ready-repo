# Plan: architect-assess HTML report

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing
- **Repository anchors:** script shape, optional `file_safety` import, and stdlib confined-read fallback in `packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py`; loading a co-located `file_safety.py` by path in `packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py`; CSP meta precedent in `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py`; skill tests in `packs/architect/tests/skills/architect-assess/`; release steps in `packs/AGENTS.md` and `packs/AGENTS.local.md`. Deviation: no script is emitted, so the script-hash CSP the precedent uses becomes `script-src` falling to `default-src 'none'`.

> **Plan contract:** `Touches`, `Tests` and `Done when` are what a completion gate
> reads; `Design`, `Approach` and `Risks` are working material.

## Approach

A stdlib script reads the confined `assessment.md`, converts a bounded Markdown subset to HTML, and writes `assessment.html` beside it. Everything outside the subset, and every Mermaid fence, becomes escaped text. One inline `<style>` block carries all styling through classes, and its sha256 is the only entry in `style-src`. Provenance is enforced by a refusal rather than a convention. The riskiest part is the hand-written Markdown subset, so T1 builds it test-first against a hostile corpus.

## Constraints

- AGENTS.md: use the blessed confinement helpers; cut before adding; no new dependency without a record.
- `packs/AGENTS.md`: a script that writes to stderr sets UTF-8 on both streams before its first print; a pack change bumps `pack.toml` and `plugin.json` together.
- The spec's `Never do` list: no network load, no vendored asset, no subprocess, no edits to sibling skills.

## Construction tests

**Integration tests:** one end-to-end test renders a fixture report holding all three orientation subsections, a heat map, a Mermaid fence, and the hostile corpus, then asserts structure, escaping, CSP, and banner together.
**Manual verification:** T5.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Guide pages, `DESIGN.md` | T4 | page diff | grep for the mode and script |
| Diagram decision note | already written | file | later spec cites it |
| Release surface | T4 | parity test, fragment | `validate` green |

## Design (LLD)

### Design decisions

- Markdown subset: headings, paragraphs, bullet and numbered lists, tables, fenced code, bold, inline code, links. A hand-written parser keeps the script stdlib-only; a Markdown library would be a new dependency. Unsupported syntax renders as escaped text, never fails. Traces to: structure, escaping, and link criteria. Owned by: T1.
- Classes carry every style, so the CSP needs no `unsafe-inline` and the output has no `style=` attribute. Heat and evidence shading are class-based. Traces to: CSP and shading criteria. Owned by: T1.
- The provenance gate matches the three subsection headings case-insensitively; an unassessed subsection begins `not assessed` and is still gated on its `Sources checked` table. Traces to: gate criteria. Owned by: T1.
- Confinement is one path: a pack-owned `scripts/file_safety.py`, byte-identical to the blessed helper and pinned by a test, loaded by path under a module name unique to this skill, as `architect-design`'s `check_document_architecture.py` does. The renderer imports nothing from `agentbundle` and the helper's own `agentbundle` import is not used. Before the helper runs, the renderer rejects a symlink in any component of the supplied path as supplied (the helper opens the root with `O_NOFOLLOW`, which sees only the last component) and checks the capability predicate, which is the helper's plus `os.rename`; the renderer refuses on hosts the helper would degrade to a path-checked parent. The effort directory is the confinement root and the single argument names it; tests use resolved base directories. A rerun replaces an existing regular `assessment.html` by reading its digest through the helper and writing with that digest as `expect_sha256`; a symlinked destination is refused by the component check and the helper. `BoundExceeded` from the helper's size check maps to exit 2, and every other `UnsafeContentError` to exit 3. A top-level handler turns any other exception into exit 3 with a fixed token. Owned by: T2.
- The matched `Sources checked` table is the label line `Sources checked:` followed by a table whose header cells are exactly the four names, and it must be the last block before the next heading at level 3 or above; at least one data row is required. Owned by: T1.
- The banner check reads only the lines of the `## Assessment charter` section outside fenced blocks. Owned by: T1.
- Heat classes attach by header text to five named columns, never by position or to `Confidence`. Owned by: T1.
- The CSP meta is the second element of `<head>`, after `meta charset` and before `title` and `style`. Owned by: T1.
- Evidence-class and heat values compare case-insensitively after trimming; output classes are lowercase.
- Exit codes: 0 success, 2 refused report, 3 confinement failure; reasons go to stderr. Owned by: T1, T2.
- Output lands where `references/output-layout.md` already says, under its write approval; opening a browser is a separate user request. Owned by: T3.

## Tasks

### T1 — Renderer core

Depends on: none
Verification mode: TDD
Touches: `scripts/render_html.py`, `packs/architect/tests/skills/architect-assess/test_render_html.py`, `packs/architect/tests/skills/architect-assess/testdata/`
Tests: drive the real entry point over fixture reports. Cover exactly one file written with exit 0, structure elements, link allowlist both ways, the hostile corpus, the element and attribute allow-lists (including `href` scheme case and whitespace), the style-body check for `@import` and `url(`, escaping of title, metadata, and the effort-directory name, CSP directives, order, and the style digest, the provenance gate over the real template's empty tables, the zero-row refusal, the not-assessed form with a row, canonical heading tokens on stderr, a report with no subsections, a rerun over an existing output, fixed-token stderr that never echoes source text, invalid UTF-8, evidence classes and the out-of-set refusal, heat classes, the banner when the line is absent, duplicated, `confirmed`, any other value, and planted only outside the charter, heat classes on the five columns and none on `Confidence`, Mermaid source blocks, the notice and metadata, the 2 MiB cap.
Done when: the T1 tests pass.

### T2 — Confinement, imports, UTF-8

Depends on: T1
Verification mode: goal-based
Touches: `scripts/render_html.py`, `scripts/file_safety.py`, the test file
Tests: hide `agentbundle` and assert the render still succeeds; symlinked source, symlinked output, and a symlink in a directory component each exit 3 with no file; a check that both streams are UTF-8 before the first print; a monkeypatched capability predicate with each of the six checks failing exits 3 with the named reason on stderr; an oversized regular source exits 2 and an oversized symlinked source exits 3; the helper copy equals the agentbundle original byte for byte; the AST test covers the import allow-list and the banned `os` attributes; the exit code set is only 0, 2, and 3, including a missing source, a missing effort directory, a wrong argument count, and a forced unexpected exception; stdout and stderr hold only fixed tokens. Tests load the script under a unique module name and hide `agentbundle` in-process.
Done when: the T2 tests pass.

### T3 — Skill wiring and eval

Depends on: T1
Verification mode: goal-based
Touches: `SKILL.md`, `references/html-report.md`, `references/output-layout.md`, `evals/evals.json`, `test_skill_contract.py`
Tests: contract test that `SKILL.md` names the mode and `scripts/render_html.py`, says it runs on a user request, and says that with no saved `assessment.md` it offers to save first and runs nothing; `references/html-report.md` states the resolved-path and no-descriptor-walking behavior; the eval case exists and asserts a `Sources checked` table.
Done when: the contract tests pass.

### T4 — Guides, design record, release

Depends on: T2, T3
Verification mode: goal-based
Touches: `guides/architect/reference/architecture-assessment.md`, `guides/architect/how-to/assess-a-repository.md`, `packs/architect/DESIGN.md`, `packs/architect/pack.toml`, `packs/architect/.claude-plugin/plugin.json`, a `tools/changelog.py new` fragment
Tests: grep for the mode and script in the reference guide, the how-to page, and `DESIGN.md`; version parity and one patch above fetched main; `tools/changelog.py validate`.
Done when: `FORCE=1 make build-self` leaves only the expected projection diff and `make lint-ruff lint-mypy` passes.

### T5 — Browser QA

Depends on: T4
Verification mode: manual QA
Touches: `docs/specs/architect-assess-html-report/notes/verification-ledger.md`
Tests: render the sample and hostile reports, open each in a real browser, and record what shows: shaded heat cells, evidence badges, the notice, the banner, and the hostile markup as visible text with no script run.
Done when: the observations are in the ledger.

## Review

The change renders untrusted text as HTML and adds a confined write, so the work-loop's security-reviewer fires at REVIEW on T1 and T2 and must be clean before T4 releases.

## Risks

- The hand-written Markdown subset can miss an author habit; the fallback is escaped text, so the worst case is plain-looking output.

## Changelog

- 2026-10-30: plan approved by eugenelim
