# Plan: architect-assess HTML report draws diagrams on request

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** the renderer and its tests in `packs/architect/.apm/skills/architect-assess/scripts/render_html.py` and `packs/architect/tests/skills/architect-assess/test_render_html.py`; the stylesheet asset loader `load_stylesheet` and the `ASSET_NAMES` and `FORBIDDEN_ASSET_TEXT` constants, which the script asset follows; the exact-version CDN precedent in `docs/specs/cdn-sri-mermaid/spec.md`; the measured facts and options in `docs/specs/architect-assess-html-report/notes/diagram-rendering-decision.md`; the heat rules in `scripts/report_assets/report.css` and the token file `docs/design/tokens/skill-html-views.md`; the byte-identity roster tests in `tests/roster/test_architect_assess_*.py`.

> **Plan contract:** `Touches`, `Tests` and `Done when` are what a completion gate
> reads; `Design`, `Approach` and `Risks` are working material.

## Approach

First change the heat glyphs and divider, which is a stylesheet edit. Then add the flag and the script asset: the renderer reads `diagrams.js` through the confinement helper, hashes it, marks the eligible fences, adds the two script elements and the extended policy, and shows the privacy note. Then the ADR, docs, eval, and release surface. A real-browser pass closes the work, because drawing, the policy, and the offline fallback only show there.

A spike on 2026-10-31 in Microsoft Edge fixed the main design choice. Mermaid 11.16.0 loaded from the pinned URL with its integrity hash renders under `default-src 'none'` and a one-hash `style-src` only when the script moves each SVG's `<style>` text into a constructable stylesheet before insertion. Left in place, that `<style>` is blocked and nodes render black at the wrong size.

## Constraints

- AGENTS.md: record a new dependency in an ADR before adding it; reuse the repository's solution first.
- The parent specs' security rules stay in force; the lists widen only as the acceptance criteria name, and only when the flag is present.
- `packs/AGENTS.md`: a non-cosmetic pack update also updates the pack's eval harness; a pack change bumps `pack.toml` and `plugin.json` together; shipped pack content cites no internal records.

## Construction tests

**Integration tests:** one test renders the sample fixture with and without the flag and checks the scripts, policy, note, drawing markers, and that the default page is byte-identical to the current output apart from the heat rules.
**Manual verification:** T4.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| ADR and dependency record | T3 | the ADR | version, URL, hash, opt-in, CSP, revisit trigger |
| Parent spec exceptions | T3 | diff | each affected criterion cites this spec |
| Decision note | T3 | diff | states the chosen option |
| Reference, skill, guide, eval | T3 | grep, eval JSON test | name the flag, host, and offline default |
| Token file heat table | T1 | diff | shows glyphs and divider |
| Verification ledger | T4 | the ledger | observations and review results |
| Release surface | T3 | parity test, fragment | `validate` green |

## Design (LLD)

### Design decisions

- The flag is the second command-line argument, `--diagrams`, and nothing else is accepted; the default output stays free of scripts and network references.
- The pinned version, URL, and hash are three constants in `render_html.py`; the policy uses the exact URL, never a host-only source.
- The inline script is the bytes of `report_assets/diagrams.js`, read through the confinement helper, hashed with SHA-256 for the policy, refused if it holds `</script` or `<!--`.
- The renderer decides eligibility, in Python, where it is testable: a fence of at most 65,536 bytes with no `%%{`, no frontmatter `config:` key, and no `click` line with `call`, `callback` or `href` is marked `diagram-drawn`. The script draws only marked blocks.
- The script initializes Mermaid with `securityLevel: 'strict'`, `startOnLoad: false`, and a theme chosen by `prefers-color-scheme`. For each marked block it renders the fence text, parses the returned SVG with `DOMParser`, moves every `<style>` into a `CSSStyleSheet` added to `document.adoptedStyleSheets`, then inserts the SVG above the source block. A render error or a missing `mermaid` global leaves the source and shows `Diagram not drawn`.
- Heat glyphs become ◔ ◑ ◕ and `?`; `heat-medium` and `heat-high` take `border-bottom-color: var(--c-bg)` so neighbouring cells keep a divider while the row rule would otherwise vanish into the `high` fill.

## Tasks

### T1 — Heat glyphs and divider

Depends on: none
Verification mode: TDD
Touches: `scripts/report_assets/report.css`, the test file, `docs/design/tokens/skill-html-views.md`
Tests: the four glyph escapes and empty alternative text; no glyph in the evidence or state sets; `border-bottom-color` on medium and high and no other `border` or `outline` property on any heat selector; contrast unchanged; the token file heat table.
Done when: the T1 tests pass.

### T2 — Flag, script asset, eligibility, policy

Depends on: T1
Verification mode: TDD
Touches: `scripts/render_html.py`, `scripts/report_assets/diagrams.js`, the test file
Tests: argument handling and the usage token; no script and the old policy without the flag; with the flag, two scripts in order with the exact attributes, the policy's `script-src` and the other directives, the note, the drawing marker and the unsafe label for each failing case, the asset loader's refusals (missing, oversize, symlink, non-regular, forbidden text), page-size caps, and escaping of fence text in both modes.
Done when: the T2 tests pass.

### T3 — ADR, docs, eval, release

Depends on: T2
Verification mode: goal-based
Touches: a new ADR in `docs/adr/`, `docs/specs/architect-assess-html-report/spec.md`, `docs/specs/architect-assess-html-report-style/spec.md`, `docs/specs/architect-assess-html-report/notes/diagram-rendering-decision.md`, `references/html-report.md`, `SKILL.md`, `guides/architect/reference/architecture-assessment.md`, `evals/evals.json`, `pack.toml`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` if it carries the version, a changelog fragment, a roster test pinning the constants to the ADR
Tests: the roster parity test; grep for the flag, host, and offline default in the three docs; the eval case; the contract test for the new reference text.
Done when: the T3 tests pass, `FORCE=1 make build-self` leaves only the expected projection diff, and the lint gate passes.

### T4 — Browser QA and design review

Depends on: T3
Verification mode: manual QA
Touches: `docs/specs/architect-assess-html-diagrams/notes/verification-ledger.md`
Tests: render the fixture with `--diagrams` and open it in a real browser in light and dark; read drawn flowchart and sequence diagram; plant a hostile fence and an `onerror` label; alter the integrity value; block the network; fetch the pinned file and compare its SHA-384 with the constant; read the heat map; run `design-review` and `experience-reviewer` over the screenshots and adjudicate.
Done when: the observations and review results are in the ledger.

## Review

The change adds a third-party script to a generated page, so the security-reviewer fires on the spec and at REVIEW on T2 and T3, the frontend-reviewer on the script and markup, and the experience-reviewer on the rendered result.

## Risks

- The CDN could be unreachable or the file removed; the page degrades to source blocks with a note.
- A future Mermaid version could change how it emits styles; the pin and the QA pass catch that when the pin moves.
- Constructable stylesheets are missing in older browsers; those readers see source blocks only.

## Changelog

<!-- Approvals only. -->
