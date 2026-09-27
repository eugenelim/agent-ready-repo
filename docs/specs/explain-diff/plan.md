# Plan: Explain diff

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `docs/CHARTER.md` (Core scope); `guides/_shared/how-to/author-a-skill.md` (skill layout, independence, scripts, evals, and build path); `guides/_shared/reference/catalogue-authoring-standards.md` (canonical-source and projection rules); `packs/converters/.apm/skills/render-proof/SKILL.md` and its security tests (nearest offline-HTML workflow); `packs/core/.apm/skills/intake-intent/scripts/intent_renderer.py` and its tests (nearest standard-library renderer)

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> execution observations belong in `notes/verification-ledger.md`.

## Approach

Keep one canonical Core skill and replace the structured page renderer with a
guarded HTML publisher. The model authors the complete semantic document and
responsive CSS so the explanation can develop a work-specific visual language.
The publisher validates a static capability subset, injects the only executable
code—a fixed quiz runtime—and retains the completed confinement, permission,
atomic-write, and no-overwrite boundaries.

## Constraints

- The canonical source lives under `packs/core/.apm/`; generated platform projections are changed only through the repository build path.
- The runtime skill depends on no other pack, package manager, external
  executable, network service, font, asset host, or browser runtime.
- Python 3.11 and its standard library are the publisher's implementation floor,
  matching the Core pack manifest.
- The model owns document structure and CSS but supplies no script or active or
  external capability. The publisher owns validation, CSP, the quiz runtime,
  output confinement, and publication.
- Consistency comes from shared teaching roles, evidence labels, offline rules,
  navigation, accessibility, and quiz semantics—not a shared template, design
  system, archetype list, or block vocabulary.
- No repository design-handoff manifest is present. The skill therefore carries
  its own portable design floor and does not depend on a design pack.
- Git metadata remains read-only in this environment; implementation and verification do not stage, commit, fetch, or update refs.

## Construction tests

**Integration tests:** Publish representative model-authored pages for an
architecture boundary, data flow, and fail-closed lifecycle. Parse the outputs
with the standard library and verify distinct semantic structures and CSS bytes
alongside common landmarks, role links, CSP, quiz behavior, accessibility hooks,
and absence of active or external surfaces. Run the catalogue build/verify path
to prove the source skill projects cleanly.

**Manual verification:** Open the representative artifact only when a browser
runtime is actually exposed. At desktop width, 320 and 390 CSS pixels, 200%
zoom, keyboard-only input, and reduced-motion mode, verify reading order,
reflow, focus, native-control states, quiz feedback, and that all content
remains available. If the runtime is absent, record `skipped-no-browser` and do
not substitute a claim based on source inspection.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Core entry-point documentation | T10 | README diff and documentation check | `close-work` confirms the shipped README names the skill. |
| Canonical skill and publisher | T8–T10 | Targeted pytest, skill lint, eval fixtures | `close-work` confirms canonical source and supported projections agree. |
| Publisher regression suite | T8, T9, T10 | Targeted pytest and end-to-end publication results | `close-work` confirms the suite remains in the Core pack test tree. |
| Release and inventory records | T4, T10 | Source-manifest diff plus catalogue build and verification output | `close-work` confirms source manifest versions and the no-drift check match. |

## Amended design (LLD)

### Design decisions

- Give the model the browser's native authoring language: semantic HTML and CSS.
  Do not insert a new page-description language between the model's teaching
  idea and the artifact. Traces to: AC-0001, AC-0014. Owned by: T8–T10.
- Treat model-authored markup as untrusted executable-adjacent input. Validate a
  capable static subset and reject rather than sanitize anything outside it.
  Traces to: AC-0003–AC-0008. Owned by: T8, T9.
- Forbid model-authored JavaScript. Inject one byte-fixed quiz runtime after
  validation and authorize only its hash in the injected CSP. The model may
  style the runtime's documented state attributes. Traces to: AC-0008, AC-0009.
  Owned by: T8, T9.
- Keep browser opening outside the publisher and preserve explicit user
  acceptance. Traces to: AC-0012. Owned by: T10.

### Authoring and validation contract

- The draft is UTF-8 HTML, capped at 1,048,576 bytes before decoding. It contains
  exact `<!-- EXPLAIN_DIFF_CSP -->` and `<!-- EXPLAIN_DIFF_RUNTIME -->`
  placeholder comments and no supplied `script` or CSP.
  The parser requires the CSP marker as the first meaningful `head` child and
  the runtime marker as the final meaningful `body` child, with neither inside a
  teaching region, `pre`, or `code`.
- A documented element allowlist admits semantic document, navigation, text,
  code, table, disclosure, and quiz controls. A documented attribute allowlist
  admits semantics, accessibility, fragment navigation, native control values,
  and the publisher's `data-*` quiz contract. Event attributes, inline styles,
  external URL attributes, forms, SVG, images, media, frames, plugins, and active
  metadata are absent.
- Style blocks remain model-authored. The validator removes CSS comments for
  inspection, rejects backslash escapes and resource/execution functions or
  at-rules, and requires narrow-layout, focus-visible, reduced-motion, and code
  whitespace rules. It never parses prose or code-block text as CSS.
- Document checks cover one `html[lang]`, `head`, title, body, main, and H1;
  sequential heading levels; unique IDs; resolved fragment links; four marked
  teaching roles; a table of contents; and five complete quiz fieldsets with
  non-empty question-specific teaching rationales.
- Sensitive-output checks run on decoded draft text before output resolution.
  They fail closed on high-confidence credential forms, email addresses,
  user-home paths, and unexplained high-entropy tokens, emit only the matched
  category, and never echo the literal. Skill guidance owns broader semantic
  minimization and generic replacement before the draft is written.
- Publication constructs the final bytes in memory, replacing each placeholder
  once, then uses the completed confined, exclusive, owner-scoped atomic write
  path. The publisher prints only the final absolute path on success.

### Components and flow

- `SKILL.md` owns activation, evidence tracing, direct page composition,
  reviewer fast-path and source-grounding requirements, publisher invocation,
  post-checks, and browser handoff.
- `references/html-authoring.md` owns the portable design floor, safe HTML/CSS
  capability contract, quiz markup, placeholders, and pre-publication checklist.
- `scripts/publish_explanation.py` owns parsing, validation, trusted injection,
  confinement, and atomic publication.
- Tests own executable boundary proof; evals own activation, mixed-audience
  handling, source traceability, and realistic workflow behavior.

Flow: inspect the change → choose a teaching concept → compose complete HTML →
validate static capabilities and teaching/accessibility floors → inject CSP and
quiz runtime → publish atomically → report path → optionally offer browser open.

### Failure and quality rules

- Validation finishes before destination resolution. Refusals name a field or
  capability class without echoing the full draft or a traceback.
- CSS checks fail closed on obfuscation or resource-bearing syntax. Unsupported
  visual ideas are redesigned with semantic HTML and allowed CSS, never waved
  through.
- The final CSP denies all by default and opens inline styles plus exactly the
  fixed runtime hash. It explicitly denies connections, images, fonts, media,
  workers, frames, objects, base URLs, and form actions.
- The publisher proves structural and capability invariants. Only real browser
  QA may claim the page is attractive, reflows correctly, or behaves correctly
  under keyboard and zoom gestures.

## Historical design (completed tasks T1–T7)

The following design records the completed structured-renderer implementation
preserved by the controlled amendment. It no longer governs T8–T10 or the final
shipped interface.

### Design decisions

- Use a clean-room implementation of the referenced workflow idea because the source gist declares no license. Preserve the workflow's useful concepts, not its prose or code. Traces to: AC-0001–AC-0014. Owned by: T1–T4.
- Keep browser opening outside the renderer. The skill adapts to the adopter's exposed capabilities, while the renderer remains deterministic and headless. Traces to: AC-0002, AC-0013. Owned by: T3.
- Use a single static-document template with a hash-authorized inline quiz script. There are no remote or runtime-resolved assets. Traces to: AC-0006, AC-0007, AC-0011. Owned by: T2.
- Keep one renderer-owned document shell but let structured presentation data choose a closed explainer archetype, visual mode, density, and per-section layout. This preserves deterministic security while avoiding one universal text-led composition. Traces to: AC-0017–AC-0019. Owned by: T5–T7.

Owned by: T1, T2, T3, T4

### Data & schema

- The amended input is version 2. It is a JSON object with `version`, `title`, `summary`, `source`, `assumptions`, `presentation`, `sections`, and `quiz`; unknown keys fail closed at every object level and `version` is exactly the JSON integer `2`. Version 1 is rejected rather than defaulted because it was only a pre-amendment development contract and has no released compatibility promise. T5 migrates the existing fixtures without deleting or weakening their behavioral assertions. Traces to: AC-0001, AC-0003–AC-0006, AC-0018. Owned by: T5, T6.
- `presentation` is a required closed object with `archetype`, `visual_mode`, `density`, and `rationale`. Archetypes are `execution-trace`, `data-flow`, `state-transition`, `before-after`, `architecture-map`, `api-contract`, `annotated-code`, and `narrative`; visual modes are `paper`, `schematic`, and `terminal`; density is `focused`, `balanced`, or `detailed`. These values select renderer-owned classes and tokens only. Traces to: AC-0017, AC-0019. Owned by: T5, T6.
- `source` contains `label`, `revision`, and `notes`. Each note is a closed object with `kind` (`observed`, `inference`, or `unknown`), `text`, and a list of repository-relative `locations`; the renderer groups these kinds with explicit labels. Traces to: AC-0001, AC-0004, AC-0008. Owned by: T1, T2.
- `sections` contains exactly the roles `background`, `intuition`, and `code`; the renderer supplies the final Quiz section from `quiz`. Each section adds a `layout` enum and follows a closed compatibility matrix: `narrative` accepts 1–8 blocks of any documented type; `split` accepts exactly 2 blocks; `grid` accepts 2–6 blocks; `spotlight` accepts exactly 1 block and that block must be `diagram`, `timeline`, `annotated-code`, `comparison`, `flow`, or `table`. Its closed-union blocks retain `paragraph`, `code`, `callout`, `flow`, `comparison`, and `table`, and add `diagram`, `timeline`, and `annotated-code`. Traces to: AC-0001, AC-0004, AC-0008, AC-0018. Owned by: T5, T6.
- `diagram.kind` is one of `data-flow`, `state-transition`, `architecture`, or `dependency`. A diagram contains 2–12 nodes with unique non-empty IDs, labels, descriptions, and optional groups, plus 1–20 edges. Edge identity is the exact `(from, to, label)` tuple and must be unique; both endpoints must name nodes; self-edges are allowed. A `timeline` contains 2–12 ordered events with titles, descriptions, and optional evidence labels. `annotated-code` contains a language, 1–200 whitespace-preserving code lines, and 1–12 annotations. Annotation bounds are exact JSON integers, not booleans or floats, use one-based inclusive indexing, and satisfy `1 <= start <= end <= line_count`; overlaps are allowed. Traces to: AC-0006, AC-0008, AC-0018, AC-0019. Owned by: T5, T6.
- Each non-narrative archetype requires at least one compatible anchor anywhere in the three sections: `execution-trace` requires `flow`, `timeline`, or `annotated-code`; `data-flow` requires a `data-flow` diagram; `state-transition` requires a `state-transition` diagram or timeline; `before-after` requires a comparison; `architecture-map` requires an `architecture` diagram; `api-contract` requires a table or dependency diagram; and `annotated-code` requires an annotated-code block. `narrative` adds no anchor requirement but the skill may select it only when its recorded evidence does not establish a more specific relationship. Traces to: AC-0017–AC-0019. Owned by: T5–T7.
- `quiz` contains exactly five questions. Each question contains an ID, prompt, four options with IDs and text, one `correct_option_id`, and textual feedback. Traces to: AC-0004, AC-0010, AC-0011. Owned by: T1, T2.
- The file byte-size gate runs before decoding and JSON parsing. JSON parsing rejects non-finite values. Schema validation completes before output resolution or creation. Traces to: AC-0004, AC-0005, AC-0012. Owned by: T1, T2.

Owned by: T1, T2

### Interfaces & contracts

- CLI: `python scripts/render_explanation.py --input-root ROOT --input RELATIVE_JSON [--output-root ROOT --output-name SAFE_NAME]`. The default output root is the operating system's temporary directory. Success prints one absolute HTML path on standard output and exits zero. Validation or I/O refusal writes one concise error to standard error, exits non-zero, and leaves no partial artifact. Traces to: AC-0003–AC-0005, AC-0012. Owned by: T1, T2.
- Input resolution canonicalizes the declared root and candidate, rejects a non-regular file or symlink, and verifies that the resolved candidate remains under the root. Explicit output uses a resolved existing directory plus a single filename segment; it rejects separators, absolute paths, symlinks, and an existing destination. Traces to: AC-0012. Owned by: T1, T2.
- The renderer writes a sibling temporary file with exclusive creation and owner-scoped permissions, flushes and closes it, then atomically replaces the absent destination without broadening permissions. A failure removes only that renderer-owned temporary file. Traces to: AC-0003, AC-0004, AC-0012, AC-0016. Owned by: T2.

Owned by: T1, T2

### Component / module decomposition

- `SKILL.md` owns activation, repository tracing, structured-document authoring, renderer invocation, verification, and adopter-specific browser handoff.
- `references/document-schema.md` owns the complete author-facing JSON shape and one safe representative input.
- `scripts/render_explanation.py` owns validation, deterministic ordering, HTML generation, confinement, and atomic output.
- `evals/` owns activation and workflow-behavior examples; `packs/core/tests/skills/explain-diff/` owns executable renderer proof.

Traces to: AC-0001–AC-0014. Owned by: T1–T4.

Owned by: T1, T2, T3, T4

### State & control flow

1. The skill resolves the requested local change and inspects the smallest relevant surrounding code and tests.
2. It identifies the dominant explanatory model, records an evidence-grounded archetype rationale, chooses bounded composition settings, and authors the version-2 structured document while explicitly marking assumptions and unknowns.
3. The renderer validates input bytes, parses strict JSON, validates presentation enums, layouts, graphs, annotations, and the rest of the closed schema, resolves a confined destination, renders in memory, and atomically writes the artifact.
4. The skill runs deterministic structural checks and returns the exact path.
5. If a browser capability is exposed, the skill offers to open the file and waits for acceptance. Otherwise it gives a local-file-open instruction.

Traces to: AC-0001–AC-0005, AC-0012, AC-0013. Owned by: T1–T3.

Owned by: T1, T2, T3

### Behavior & rules

- Every input string passes through context-appropriate HTML escaping. User content never reaches element names, attribute names, raw style, raw script, `href`, `src`, or event-handler attributes. Traces to: AC-0006, AC-0007. Owned by: T1, T2.
- Flow diagrams render as semantic ordered steps with CSS connectors; comparisons render as paired labeled regions; tables use captions, column headers, and cells; callouts use labeled regions; code uses `pre > code` and preserves whitespace. Traces to: AC-0008. Owned by: T2.
- Archetypes set renderer-owned page classes and a visible explanation-model label; visual modes and density select only predefined tokens. Section layouts create materially different narrative, split, grid, and spotlight compositions. Diagrams render labeled node-and-relation structures, timelines render ordered events, and annotated code renders line-addressable code with linked explanatory notes. Traces to: AC-0017–AC-0019. Owned by: T6.
- Quiz option order derives from SHA-256 over canonical JSON plus the question ID. Correct positions rotate across four slots and repeat one slot selected by the artifact digest, so all four positions appear while output remains byte-stable. Traces to: AC-0010. Owned by: T1, T2.
- Quiz choices are native buttons in fieldsets. The supplied script sets textual feedback in a polite live region and adds state attributes used by CSS; correctness is never conveyed by color alone. Traces to: AC-0011. Owned by: T2.

Owned by: T1, T2

### Failure, edge cases & resilience

- Validation is fail-closed and precedes file creation. Errors name the rejected field or path class without echoing full untrusted payloads or stack traces. Traces to: AC-0004, AC-0005, AC-0012. Owned by: T1, T2.
- Empty strings where content is required, duplicate IDs, dangling flow edges, ragged tables, invalid quiz answers, non-finite numbers, excessive input bytes, and unknown keys or types are rejected. Traces to: AC-0004, AC-0005, AC-0008, AC-0010. Owned by: T1, T2.
- Unknown presentation values, unsupported section-layout and block combinations, duplicate diagram node IDs, dangling diagram edges, oversized visual collections, and annotated-code ranges outside the supplied code are rejected before output resolution. Traces to: AC-0004, AC-0018, AC-0019. Owned by: T5, T6.
- Existing destinations are never overwritten. Temporary cleanup targets only the file created by the current process. POSIX writes request and verify mode `0600`; non-POSIX writes inherit the selected directory's access controls and perform no broadening operation. Traces to: AC-0012, AC-0016. Owned by: T1, T2.

Owned by: T1, T2

### Quality attributes (NFRs)

- Security: the Content Security Policy is `default-src 'none'`; the exact bundled quiz script is admitted with a SHA-256 source expression; styles are local; navigation and form submission are disabled; input cannot create active content. Traces to: AC-0006, AC-0007. Owned by: T1, T2.
- Accessibility: semantic landmarks and headings, native controls, visible `:focus-visible`, textual live feedback, 44-by-44 CSS-pixel minimum controls where controls are presented, reduced-motion handling, and zoom/reflow rules support WCAG 2.2 AA intent. Traces to: AC-0008, AC-0009, AC-0011. Owned by: T2.
- Readability: the default content lane uses `max-inline-size: 75ch`, line height between 1.4 and 1.6, a sticky table of contents only when space permits, and a single-column narrow layout. Traces to: AC-0008, AC-0009. Owned by: T2.
- Privacy and operations: the artifact has no telemetry, storage, cookies, service worker, remote requests, or runtime logs. Traces to: AC-0002, AC-0007. Owned by: T2, T3.

Owned by: T1, T2, T3

### Dependencies & integration

- Runtime dependencies are Python 3.11 standard-library modules only. The renderer imports no repository package, other skill, package-manager dependency, or browser API. Traces to: AC-0002. Owned by: T2.
- Repository integration uses the existing Core manifest, plugin manifest, README entry-point table, eval allowlist, security metadata, and build pipeline. Generated projections are verification output, never hand-edited destinations. Traces to: AC-0014, AC-0015. Owned by: T3, T4.

Owned by: T2, T3, T4

## Tasks

The T1–T3 and T5–T7 records below describe the superseded structured-renderer
delivery and remain here as history. Their verification evidence is retained in
`notes/verification-ledger.md`; they are not part of the fresh model-owned-design
cohort created after the approved reset.

#### Historical T1: Renderer contract tests fail for the absent implementation

**Depends on:** none

**Touches:** `packs/core/tests/skills/explain-diff/**`

**Tests:**

- Verification mode: **TDD**. Verification artifact: `packs/core/tests/skills/explain-diff/test_render_explanation.py`.
- Materialize the following approved stub family unchanged at that path. Every listed function carries `stub: true`: `test_renderer_escapes_markup_and_writes_offline_html` (AC-0003), `test_renderer_rejects_unknown_fields` (AC-0004), `test_renderer_checks_size_before_json` (AC-0005), `test_renderer_escapes_every_text_sink` (AC-0006), `test_renderer_has_offline_csp` (AC-0007), `test_renderer_emits_semantic_blocks` (AC-0008), `test_renderer_is_deterministic_and_balances_answers` (AC-0010), `test_renderer_refuses_overwrite` (AC-0012), and `test_renderer_uses_owner_scoped_permissions` (AC-0016).

```python
import json
import subprocess
import sys
from pathlib import Path


CORE_ROOT = Path(__file__).resolve().parents[3]
RENDERER = CORE_ROOT / ".apm/skills/explain-diff/scripts/render_explanation.py"


# STUB: AC-0003
def test_renderer_escapes_markup_and_writes_offline_html(tmp_path: Path) -> None:
    """A valid structured document renders without promoting text to markup."""
    questions = [
        {
            "id": f"q{index}",
            "prompt": f"Question {index}?",
            "options": [
                {"id": f"q{index}-a", "text": "Alpha"},
                {"id": f"q{index}-b", "text": "Beta"},
                {"id": f"q{index}-c", "text": "Gamma"},
                {"id": f"q{index}-d", "text": "Delta"},
            ],
            "correct_option_id": f"q{index}-a",
            "feedback": "Review the explanation.",
        }
        for index in range(1, 6)
    ]
    document = {
        "version": 1,
        "title": "Escaping </script>",
        "summary": "<script>alert(1)</script>",
        "source": {
            "label": "local diff",
            "revision": "working tree",
            "notes": [
                {"kind": "observed", "text": "The changed branch returns a value.", "locations": ["src/example.py"]}
            ],
        },
        "assumptions": [],
        "sections": [
            {"id": "background", "title": "Background", "blocks": [{"type": "paragraph", "text": "Context"}]},
            {"id": "intuition", "title": "Intuition", "blocks": [{"type": "paragraph", "text": "Model"}]},
            {"id": "code", "title": "Code", "blocks": [{"type": "code", "language": "text", "code": "<img src=x onerror=alert(1)>"}]},
        ],
        "quiz": questions,
    }
    input_path = tmp_path / "document.json"
    input_path.write_text(json.dumps(document), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(RENDERER),
            "--input-root",
            str(tmp_path),
            "--input",
            input_path.name,
            "--output-root",
            str(tmp_path),
            "--output-name",
            "explanation.html",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    output_path = Path(completed.stdout.strip())
    rendered = output_path.read_text(encoding="utf-8")
    assert output_path == tmp_path / "explanation.html"
    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered
    assert "https://" not in rendered
    assert "http://" not in rendered


def _valid_document() -> dict[str, object]:
    """Return the smallest complete version-1 renderer document."""
    return {
        "version": 1,
        "title": "A change",
        "summary": "How it works",
        "source": {
            "label": "local diff",
            "revision": "working tree",
            "notes": [
                {"kind": "observed", "text": "The branch returns a value.", "locations": ["src/example.py"]}
            ],
        },
        "assumptions": [],
        "sections": [
            {"id": "background", "title": "Background", "blocks": [{"type": "paragraph", "text": "Context"}]},
            {"id": "intuition", "title": "Intuition", "blocks": [{"type": "paragraph", "text": "Model"}]},
            {"id": "code", "title": "Code", "blocks": [{"type": "code", "language": "text", "code": "return value"}]},
        ],
        "quiz": [
            {
                "id": f"q{index}",
                "prompt": f"Question {index}?",
                "options": [
                    {"id": f"q{index}-a", "text": "Alpha"},
                    {"id": f"q{index}-b", "text": "Beta"},
                    {"id": f"q{index}-c", "text": "Gamma"},
                    {"id": f"q{index}-d", "text": "Delta"},
                ],
                "correct_option_id": f"q{index}-a",
                "feedback": "Review the explanation.",
            }
            for index in range(1, 6)
        ],
    }


def _run_renderer(tmp_path: Path, document: dict[str, object], output_name: str = "explanation.html") -> subprocess.CompletedProcess[str]:
    """Invoke the public CLI with a JSON document under the declared root."""
    input_path = tmp_path / "document.json"
    input_path.write_text(json.dumps(document), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(RENDERER),
            "--input-root",
            str(tmp_path),
            "--input",
            input_path.name,
            "--output-root",
            str(tmp_path),
            "--output-name",
            output_name,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


# STUB: AC-0004
def test_renderer_rejects_unknown_fields(tmp_path: Path) -> None:
    """An unknown key fails closed before an output file exists."""
    document = _valid_document()
    document["raw_html"] = "<b>unsafe</b>"

    completed = _run_renderer(tmp_path, document)

    assert completed.returncode != 0
    assert "unknown field" in completed.stderr.lower()
    assert not (tmp_path / "explanation.html").exists()


# STUB: AC-0005
def test_renderer_checks_size_before_json(tmp_path: Path) -> None:
    """The byte ceiling fires before malformed JSON can be parsed."""
    input_path = tmp_path / "document.json"
    input_path.write_bytes(b"{" + b" " * 1_048_576)

    completed = subprocess.run(
        [sys.executable, str(RENDERER), "--input-root", str(tmp_path), "--input", input_path.name],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "1,048,576 bytes" in completed.stderr
    assert "json" not in completed.stderr.lower()


# STUB: AC-0006
def test_renderer_escapes_every_text_sink(tmp_path: Path) -> None:
    """Hostile text remains text in headings, prose, source notes, and code."""
    document = _valid_document()
    hostile = "</script><img src=x onerror=alert(1)>"
    document["title"] = hostile
    document["summary"] = hostile
    document["source"]["notes"][0]["text"] = hostile  # type: ignore[index]
    document["sections"][2]["blocks"][0]["code"] = hostile  # type: ignore[index]

    completed = _run_renderer(tmp_path, document)
    assert completed.returncode == 0, completed.stderr
    rendered = (tmp_path / "explanation.html").read_text(encoding="utf-8")
    assert hostile not in rendered
    assert rendered.count("&lt;/script&gt;") >= 4
    assert "onerror=" not in rendered.replace("&lt;img src=x onerror=alert(1)&gt;", "")


# STUB: AC-0007
def test_renderer_has_offline_csp(tmp_path: Path) -> None:
    """The artifact admits no external fetch surface and hashes its script."""
    completed = _run_renderer(tmp_path, _valid_document())
    assert completed.returncode == 0, completed.stderr
    rendered = (tmp_path / "explanation.html").read_text(encoding="utf-8")
    assert "default-src 'none'" in rendered
    assert "script-src 'sha256-" in rendered
    assert "http://" not in rendered
    assert "https://" not in rendered


# STUB: AC-0008
def test_renderer_emits_semantic_blocks(tmp_path: Path) -> None:
    """Every closed-union block has a semantic HTML representation."""
    document = _valid_document()
    document["sections"][1]["blocks"] = [  # type: ignore[index]
        {"type": "callout", "label": "Why", "text": "Reason"},
        {"type": "flow", "steps": [{"title": "Read", "text": "Input"}, {"title": "Write", "text": "Output"}]},
        {"type": "comparison", "left": {"label": "Before", "items": ["Old"]}, "right": {"label": "After", "items": ["New"]}},
        {"type": "table", "caption": "Map", "columns": ["Input", "Output"], "rows": [["A", "B"]]},
    ]

    completed = _run_renderer(tmp_path, document)
    assert completed.returncode == 0, completed.stderr
    rendered = (tmp_path / "explanation.html").read_text(encoding="utf-8")
    for token in ("<main", "<nav", "<aside", "<ol", "<table", "<caption", "<pre><code"):
        assert token in rendered


# STUB: AC-0010
def test_renderer_is_deterministic_and_balances_answers(tmp_path: Path) -> None:
    """Equivalent invocations are byte-stable and use every answer position."""
    first = _run_renderer(tmp_path, _valid_document(), "first.html")
    second = _run_renderer(tmp_path, _valid_document(), "second.html")
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    first_bytes = (tmp_path / "first.html").read_bytes()
    second_bytes = (tmp_path / "second.html").read_bytes()
    assert first_bytes == second_bytes
    rendered = first_bytes.decode("utf-8")
    positions = [rendered.count(f'data-correct-position="{index}"') for index in range(4)]
    assert sorted(positions) == [1, 1, 1, 2]


# STUB: AC-0012
def test_renderer_refuses_overwrite(tmp_path: Path) -> None:
    """An existing destination is preserved byte-for-byte."""
    output_path = tmp_path / "explanation.html"
    output_path.write_text("sentinel", encoding="utf-8")

    completed = _run_renderer(tmp_path, _valid_document())

    assert completed.returncode != 0
    assert "already exists" in completed.stderr.lower()
    assert output_path.read_text(encoding="utf-8") == "sentinel"


# STUB: AC-0016
def test_renderer_uses_owner_scoped_permissions(tmp_path: Path) -> None:
    """POSIX publication keeps the renderer-created file at mode 0600."""
    import os
    import stat

    completed = _run_renderer(tmp_path, _valid_document())
    assert completed.returncode == 0, completed.stderr
    if os.name == "posix":
        assert stat.S_IMODE((tmp_path / "explanation.html").stat().st_mode) == 0o600
```

- `no stub (visual / manual QA)` for AC-0009 and AC-0011: the discovery predicate is an exposed browser runtime able to set viewport, zoom, reduced motion, and keyboard input; the proof obligation is the recorded manual matrix in `## Construction tests`. Deterministic landmark, native-button, live-region, and focus-style checks remain construction tests but do not substitute for the rendered-page gesture.
- Complete the stub family with edge cases for all AC-0004 rejection members, the accepted side of AC-0005, input traversal and symlink escape under AC-0012, temporary-file cleanup, and non-POSIX no-broadening behavior under AC-0016 before refactoring.
- Stub validation: the exact nine-function family compiled and all nine tests earned their intended absent-renderer red in separate ignored scratch directories on 2026-09-25. The scratch directories remain because this managed profile denies directory removal; no cleanup retry was attempted.

**Done when:** The exact stub family compiles and earns the intended red before production code exists; the visual/manual obligations carry their legal no-stub record.

#### Historical T2: The renderer passes its contract and security suite

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/explain-diff/scripts/**`, `packs/core/.apm/skills/explain-diff/references/document-schema.md`, `packs/core/tests/skills/explain-diff/**`

**Tests:**

- Verification mode: **TDD**. Verification artifact: `packs/core/tests/skills/explain-diff/test_render_explanation.py`, seeded by T1's approved stub family.
- Run the targeted pytest suite from T1 and require all accepted, refusal, escaping, confinement, deterministic-output, semantic-structure, permission, and cleanup cases to pass (AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0010, AC-0012, AC-0016). Structural assertions for native quiz controls, live regions, and focus styles are construction evidence only; they do not satisfy AC-0009 or AC-0011.
- Render the representative structured document twice into separate temporary roots and require byte-identical outputs.
- On this managed local profile, confirm the post-assertion `os.rmdir` restriction once, then run the unaffected cases with exact `--deselect` node IDs for `test_cli_renders_valid_document`, `test_renderer_refuses_overwrite`, `test_renderer_rejects_path_escape`, and `test_atomic_write_cleans_owned_temporary_file`; the full suite, including those four cleanup-sensitive filesystem cases, remains required in CI/a supported profile.

**Approach:** Implement validation and pure rendering functions before the CLI and filesystem adapter so each boundary has a small test seam; construct the full HTML string before opening an output file.

**Done when:** The targeted renderer suite passes in a supported profile, the exact local deselection run passes here after the single recorded cleanup failure, and the non-browser evidence satisfies AC-0003 through AC-0008, AC-0010, AC-0012, and AC-0016 without a network or non-standard-library import. AC-0009 and AC-0011 remain open for T4's browser/manual record or its explicit `skipped-no-browser` limitation.

#### Historical T3: The Core skill guides the full explanation and adopter-specific handoff

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/explain-diff/SKILL.md`, `packs/core/.apm/skills/explain-diff/evals/**`, `packs/core/README.md`, `packs/core/pack.toml`

**Tests:**

- Verification mode: **goal-based check**. Verification artifacts: skill activation/output evals, Core README entry, source scan, and catalogue lint. `no stub (goal-based)` because these outcomes are repository inventory and agent-workflow assertions rather than a callable logic seam.
- Add eval queries that distinguish explanation requests from correctness review, generic document conversion, and product UI implementation; require activation only for the explanation cases.
- Add workflow eval assertions for source tracing, structured-only renderer input, no cross-pack dependency, exact-path reporting, and the two browser-handoff branches.
- Run skill and catalogue lint over the canonical Core source, including exact security metadata and credential-free status.

**Done when:** The canonical skill satisfies AC-0001, AC-0002, AC-0013, and AC-0015, and the Core README and eval inventory expose the same promise.

#### Historical T5: Adaptive explanation contract tests fail before implementation

**Depends on:** T2, T3

**Touches:** `packs/core/tests/skills/explain-diff/test_render_explanation.py`

**Tests:**

- Verification mode: **TDD**. Extend the existing renderer suite before changing the renderer or schema.
- Migrate the existing valid fixture factory from version 1 to required version 2 presentation and layout fields, preserve every prior behavioral assertion, and add an explicit test that version 1 is rejected. The accepted-input cases are expected to red until T6 implements version 2; record the exact red set rather than weakening earlier checks.
- Add focused tests for closed presentation enums; the exact layout cardinalities and spotlight visual-only rule; all eight archetype contracts, including negative missing/mismatched-anchor cases for every non-narrative archetype and a valid anchor-free narrative case; all four section layouts; materially distinct composition for at least three archetypes; semantic diagram/timeline/annotated-code output; 2–12 diagram nodes, 1–20 unique edges, endpoint integrity and allowed self-edges; 2–12 timeline events; 1–200 code lines; 1–12 annotations; exact-integer one-based inclusive annotation ranges; and inert hostile text in every new sink (AC-0004, AC-0006, AC-0008, AC-0017–AC-0019).
- Use one valid representative document for each of the eight archetypes. The distinct-composition assertion must compare semantic classes and structures across at least three of them, not merely an archetype label or color token.
- Mutation-proof the meaningful assertions by temporarily collapsing archetype classes to one composition, bypassing graph endpoint validation, and bypassing exact annotation-range validation; each mutation must red the test naming that invariant, then be restored through edits.

**Done when:** The migrated and new adaptive tests compile, the expected version-2 and adaptive cases earn implementation-absent reds, the exact version-1 rejection and existing refusal/security tests retain their intended assertions, and no earlier filesystem or escaping assertion is deleted or relaxed.

#### Historical T6: The renderer safely composes adaptive visual explainers

**Depends on:** T5

**Touches:** `packs/core/.apm/skills/explain-diff/scripts/render_explanation.py`, `packs/core/.apm/skills/explain-diff/references/document-schema.md`, `packs/core/tests/skills/explain-diff/test_render_explanation.py`

**Tests:**

- Verification mode: **TDD** against T5's tests plus the complete existing renderer suite.
- Keep validation before output resolution. Enforce exact presentation and layout enums, per-block closed keys, collection ceilings, diagram identity and endpoint integrity, and annotated-code line bounds.
- Render archetype, visual-mode, density, and layout choices only as fixed renderer-owned class names. Escape every model-authored label, description, group, event, annotation, and code line through the existing text or attribute sinks.
- Render diagrams as semantic node and relationship regions, timelines as ordered events, and annotated code as a line-numbered code region paired with notes whose accessible labels name their line ranges. Preserve useful reading order when CSS is absent.
- Keep the page self-contained, CSP-constrained, deterministic, responsive, keyboard-usable, and owner-scoped on disk.

**Done when:** The complete renderer suite passes, all eight archetype fixtures satisfy their anchor contracts, at least three produce meaningfully different semantic compositions, every new validation mutation is caught, and identical adaptive input remains byte-identical across renders.

#### Historical T7: The skill plans a fitting explainer instead of defaulting to prose

**Depends on:** T6

**Touches:** `packs/core/.apm/skills/explain-diff/SKILL.md`, `packs/core/.apm/skills/explain-diff/references/**`, `packs/core/.apm/skills/explain-diff/evals/**`, `packs/core/tests/pack/test_work_intake_surface.py`, `docs/specs/explain-diff/notes/verification-ledger.md`

**Tests:**

- Verification mode: **goal-based check** plus one real end-to-end renderer invocation.
- Add a compact archetype-selection matrix grounded in the observed change shape. Require the model to select and justify its archetype before writing content, choose layouts and visuals that serve that model, and avoid diagrams when the trace does not establish the relationships.
- Pin the canonical and projected `allowed-tools` declaration to exactly `Read Write Bash`. The packaged skill receives no existing-file mutation, agent, network, credential, or GUI authority; the browser branch remains an adopter-exposed, user-accepted optional capability with manual local-file instructions as the fallback (AC-0020).
- Add one positive selection case for every archetype: algorithm execution trace, transformation data flow, stateful lifecycle transition, focused before/after refactor, component architecture map, API contract, line-addressable annotated code, and a small change whose evidence genuinely warrants narrative fallback. Assertions require fitting selections, evidence-grounded rationales, structured-only output, and no dependency on another pack.
- Render at least three representative structured documents through the canonical bundled renderer and record their exact output paths and structural distinctions. Browser opening remains adopter-specific and requires acceptance.

**Done when:** AC-0017 is covered by workflow evals, AC-0018 and AC-0019 are exercised end to end, the standalone runtime promise remains true, and T4 can regenerate matching projections from the amended canonical source.

### T8: Model-authored HTML publisher contract tests fail first

**Depends on:** none; the superseded renderer evidence is retained as historical
context, not as a task in this fresh cohort

**Touches:** `packs/core/tests/skills/explain-diff/test_publish_explanation.py`

**Tests:**

- Verification mode: **TDD**. Replace the superseded structured-renderer test
  surface with publisher tests before production changes.
- Add accepted cases for a minimal document and three independent full lessons.
  Add refusals for size and UTF-8 errors, missing or duplicate document regions
  and placeholders, heading/ID/fragment defects, disallowed tags and attributes,
  supplied scripts/CSP, malformed quiz controls, and each forbidden CSS family.
- Add misplaced-marker cases for teaching regions, `pre`/`code`, late head, and
  non-final body positions. Add sensitive-literal fixtures for credential
  prefixes, bearer values, email addresses, user-home paths, and high-entropy
  tokens; assert that neither output nor refusal text repeats the literal.
- Preserve the completed filesystem invariants: confined input and output,
  symlink and traversal refusal, no overwrite, owner-scoped permissions, atomic
  cleanup, concise failures, and no file creation before validation.
- Assert the final CSP, exact runtime bytes and hash, self-contained output,
  textual quiz feedback contract, and that three representative pages retain
  different CSS and semantic signatures after publication.
- Mutation-proof the active-content boundary, CSS escape refusal, runtime-byte
  identity, and validation-before-output-order assertions.

Materialize this approved stub family unchanged at the verification artifact.
Every test below carries `stub: true`; helper functions are support code, not
separate stubs. `EXPECTED_RUNTIME` is the byte-fixed runtime T9 must inject.

```python
import base64
import hashlib
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest


CORE_ROOT = Path(__file__).resolve().parents[3]
PUBLISHER = CORE_ROOT / ".apm/skills/explain-diff/scripts/publish_explanation.py"
EXPECTED_RUNTIME = """(()=>{for(const q of document.querySelectorAll('[data-quiz-question]')){const b=q.querySelector('[data-quiz-check]'),f=q.querySelector('[data-quiz-feedback]');b.addEventListener('click',()=>{const s=q.querySelector('input[type=\"radio\"]:checked'),ok=!!s&&s.dataset.correct==='true';q.dataset.state=s?(ok?'correct':'incorrect'):'unanswered';f.textContent=s?(ok?'Correct.':'Not yet. Review the explanation and try again.'):'Choose an answer first.';});}})();"""


def _quiz() -> str:
    """Return five complete native-control quiz questions."""
    questions = []
    for number in range(1, 6):
        option_items = []
        for letter in "abcd":
            correct = ' data-correct="true"' if letter == "a" else ""
            option_items.append(
                f'<label><input type="radio" name="q{number}" value="{letter}"'
                f'{correct}> Option {letter.upper()}</label>'
            )
        options = "".join(option_items)
        questions.append(
            f'<fieldset data-quiz-question><legend>Question {number}?</legend>'
            f'{options}<button type="button" data-quiz-check>Check answer</button>'
            '<p data-quiz-feedback aria-live="polite"></p></fieldset>'
        )
    return "".join(questions)


def _page(*, marker: str = "architecture", css: str = "") -> str:
    """Return a minimal valid, independently styled explanation draft."""
    return f"""<!doctype html>
<html lang="en"><head><!-- EXPLAIN_DIFF_CSP -->
<title>{marker} lesson</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; overflow-wrap: anywhere; }}
pre {{ white-space: pre; overflow: auto; }}
a:focus-visible, button:focus-visible, input:focus-visible {{ outline: 3px solid currentColor; }}
@media (max-width: 40rem) {{ main {{ display: block; }} }}
@media (prefers-reduced-motion: reduce) {{ * {{ scroll-behavior: auto !important; }} }}
{css}
</style></head><body>
<a href="#main">Skip to explanation</a>
<header><h1>{marker} change</h1></header>
<nav aria-label="Lesson"><a href="#background">Background</a><a href="#intuition">Intuition</a><a href="#code">Code</a><a href="#quiz">Quiz</a></nav>
<main id="main">
<section id="background" data-explain-role="background"><h2>Background</h2><p data-evidence="observed">Observed behavior.</p></section>
<article id="intuition" data-explain-role="intuition"><h2>Intuition</h2><p data-evidence="inference">A bounded inference.</p></article>
<section id="code" data-explain-role="code"><h2>Code</h2><pre><code>return value
</code></pre></section>
<section id="quiz" data-explain-role="quiz"><h2>Quiz</h2>{_quiz()}</section>
</main><!-- EXPLAIN_DIFF_RUNTIME --></body></html>"""


def _run(
    tmp_path: Path,
    draft: str | bytes,
    *,
    input_name: str = "draft.html",
    output_name: str = "lesson.html",
) -> subprocess.CompletedProcess[str]:
    """Invoke the public publisher CLI inside one approved root."""
    input_path = tmp_path / input_name
    data = draft.encode("utf-8") if isinstance(draft, str) else draft
    input_path.write_bytes(data)
    return _invoke(tmp_path, input_name, output_name)


def _invoke(
    tmp_path: Path, input_name: str, output_name: str = "lesson.html"
) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI without pre-resolving an untrusted input locator."""
    return subprocess.run(
        [
            sys.executable,
            str(PUBLISHER),
            "--input-root",
            str(tmp_path),
            "--input",
            input_name,
            "--output-root",
            str(tmp_path),
            "--output-name",
            output_name,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


# STUB: AC-0003, AC-0007, AC-0008
def test_publisher_injects_only_the_fixed_runtime_and_matching_csp(tmp_path: Path) -> None:
    """A valid draft preserves its design and receives only trusted runtime bytes."""
    completed = _run(tmp_path, _page(css=".architecture { display: grid; }"))
    assert completed.returncode == 0, completed.stderr
    output_path = Path(completed.stdout.strip())
    rendered = output_path.read_text(encoding="utf-8")
    digest = base64.b64encode(hashlib.sha256(EXPECTED_RUNTIME.encode()).digest()).decode()
    assert output_path == tmp_path / "lesson.html"
    assert f"<script>{EXPECTED_RUNTIME}</script>" in rendered
    assert f"script-src 'sha256-{digest}'" in rendered
    assert "default-src 'none'" in rendered
    assert "EXPLAIN_DIFF_" not in rendered
    assert ".architecture { display: grid; }" in rendered


# STUB: AC-0003
@pytest.mark.parametrize(
    ("draft", "message"),
    [(b"{" + b" " * 1_048_576, "1,048,576 bytes"), (b"\xff", "UTF-8")],
)
def test_publisher_rejects_size_and_encoding_before_output(
    tmp_path: Path, draft: bytes, message: str
) -> None:
    """Byte and decoding limits fail through the concise refusal channel."""
    completed = _run(tmp_path, draft)
    assert completed.returncode != 0
    assert message in completed.stderr
    assert not (tmp_path / "lesson.html").exists()


# STUB: AC-0004, AC-0005
@pytest.mark.parametrize(
    "mutate",
    [
        lambda page: page.replace("<!doctype html>", ""),
        lambda page: page.replace('<html lang="en">', "<html>"),
        lambda page: page.replace("<h1>architecture change</h1>", ""),
        lambda page: page.replace('id="background"', 'id="code"'),
        lambda page: page.replace('href="#background"', 'href="#missing"'),
        lambda page: page.replace('data-explain-role="intuition"', 'data-explain-role="background"'),
        lambda page: page.replace("<h2>Code</h2>", "<h4>Code</h4>"),
        lambda page: page.replace("<pre><code>", "<pre><span>"),
    ],
)
def test_publisher_rejects_broken_document_and_teaching_structure(
    tmp_path: Path, mutate: object
) -> None:
    """Document, heading, ID, fragment, code, role, and TOC defects fail closed."""
    completed = _run(tmp_path, mutate(_page()))  # type: ignore[operator]
    assert completed.returncode != 0
    assert "invalid document" in completed.stderr.lower()
    assert not (tmp_path / "lesson.html").exists()


# STUB: AC-0006
@pytest.mark.parametrize(
    "injection",
    [
        "<script>alert(1)</script>",
        '<p onclick="alert(1)">event</p>',
        '<p style="color:red">style</p>',
        '<a href="https://example.invalid">external</a>',
        '<form action="#"><input></form>',
        '<svg><use href="#x"></use></svg>',
        '<img src="data:image/png;base64,AA==" alt="x">',
        '<meta http-equiv="Content-Security-Policy" content="default-src *">',
    ],
)
def test_publisher_rejects_active_or_external_html(tmp_path: Path, injection: str) -> None:
    """Untrusted markup cannot add executable or request-bearing capability."""
    completed = _run(tmp_path, _page().replace("</main>", f"{injection}</main>"))
    assert completed.returncode != 0
    assert "disallowed html" in completed.stderr.lower()
    assert not (tmp_path / "lesson.html").exists()


# STUB: AC-0007
@pytest.mark.parametrize(
    "css",
    [
        r".x { color: r\65 d; }",
        ".x { background: url(x); }",
        "@import 'x';",
        "@font-face { font-family: x; src: local(x); }",
        ".x { background: image-set('x' 1x); }",
        ".x { width: expression(alert(1)); }",
        ".x { -moz-binding: url(x); }",
    ],
)
def test_publisher_rejects_forbidden_css_capabilities(tmp_path: Path, css: str) -> None:
    """CSS obfuscation, resource loading, and legacy execution fail closed."""
    completed = _run(tmp_path, _page(css=css))
    assert completed.returncode != 0
    assert "disallowed css" in completed.stderr.lower()
    assert not (tmp_path / "lesson.html").exists()


# STUB: AC-0008
@pytest.mark.parametrize(
    "draft",
    [
        _page().replace("<!-- EXPLAIN_DIFF_CSP -->", ""),
        _page().replace("<!-- EXPLAIN_DIFF_RUNTIME -->", ""),
        _page().replace("<!-- EXPLAIN_DIFF_CSP -->", "<title>x</title><!-- EXPLAIN_DIFF_CSP -->"),
        _page().replace("<!-- EXPLAIN_DIFF_RUNTIME -->", "<!-- EXPLAIN_DIFF_RUNTIME --><p>late</p>"),
        _page().replace("<pre><code>", "<pre><code><!-- EXPLAIN_DIFF_RUNTIME -->"),
    ],
)
def test_publisher_rejects_missing_duplicate_or_misplaced_markers(
    tmp_path: Path, draft: str
) -> None:
    """Trusted injection seams have one exact structural location."""
    completed = _run(tmp_path, draft)
    assert completed.returncode != 0
    assert "placeholder" in completed.stderr.lower()
    assert not (tmp_path / "lesson.html").exists()


# STUB: AC-0009, AC-0010
def test_publisher_rejects_malformed_quiz_and_missing_css_floors(tmp_path: Path) -> None:
    """Native controls, feedback, responsive, focus, motion, and code floors are required."""
    bad_quiz = _page().replace('aria-live="polite"', 'aria-live="off"', 1)
    bad_css = _page().replace(":focus-visible", ":focus")
    for draft in (bad_quiz, bad_css):
        completed = _run(tmp_path, draft, output_name=f"lesson-{len(draft)}.html")
        assert completed.returncode != 0
        assert "required" in completed.stderr.lower()


# STUB: AC-0011
def test_publisher_default_output_is_dated_collision_resistant_and_owner_only(
    tmp_path: Path,
) -> None:
    """Omitting destination flags publishes two distinct files under OS temp."""
    input_path = tmp_path / "draft.html"
    input_path.write_text(_page(), encoding="utf-8")
    environment = os.environ.copy()
    environment["TMPDIR"] = str(tmp_path)
    outputs = []
    for _ in range(2):
        completed = subprocess.run(
            [
                sys.executable,
                str(PUBLISHER),
                "--input-root",
                str(tmp_path),
                "--input",
                input_path.name,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        assert completed.returncode == 0, completed.stderr
        output_path = Path(completed.stdout.strip())
        assert output_path.is_absolute()
        assert output_path.parent.resolve() == tmp_path.resolve()
        assert re.fullmatch(r"explain-diff-\d{4}-\d{2}-\d{2}-[a-f0-9]+\.html", output_path.name)
        if os.name == "posix":
            assert stat.S_IMODE(output_path.stat().st_mode) == 0o600
        outputs.append(output_path)
    assert outputs[0] != outputs[1]


# STUB: AC-0011
def test_publisher_rejects_unconfined_symlinked_and_nonregular_input(
    tmp_path: Path,
) -> None:
    """Every input locator is confined and regular before draft bytes are read."""
    outside = tmp_path.parent / f"{tmp_path.name}-outside.html"
    outside.write_text(_page(), encoding="utf-8")
    directory = tmp_path / "directory"
    directory.mkdir()
    symlink = tmp_path / "linked.html"
    symlink.symlink_to(outside)
    attempts = (
        "../" + outside.name,
        str(outside.resolve()),
        symlink.name,
        directory.name,
    )
    for index, input_name in enumerate(attempts):
        output_name = f"unconfined-{index}.html"
        completed = _invoke(tmp_path, input_name, output_name)
        assert completed.returncode != 0
        assert "input" in completed.stderr.lower()
        assert not (tmp_path / output_name).exists()


# STUB: AC-0011
def test_publisher_confines_and_atomically_publishes_owner_only(tmp_path: Path) -> None:
    """Traversal and overwrite fail; accepted POSIX output remains mode 0600."""
    escaped = _run(tmp_path, _page(), output_name="../escape.html")
    assert escaped.returncode != 0
    existing = tmp_path / "lesson.html"
    existing.write_text("sentinel", encoding="utf-8")
    refused = _run(tmp_path, _page())
    assert refused.returncode != 0
    assert existing.read_text(encoding="utf-8") == "sentinel"
    existing.unlink()
    accepted = _run(tmp_path, _page())
    assert accepted.returncode == 0, accepted.stderr
    if os.name == "posix":
        assert stat.S_IMODE(existing.stat().st_mode) == 0o600
    assert not list(tmp_path.glob(".explain-diff-*.tmp"))


# STUB: AC-0014
def test_publisher_preserves_three_independent_page_designs(tmp_path: Path) -> None:
    """Publication does not collapse different authored structures or CSS."""
    drafts = [
        _page(marker="architecture", css=".architecture-map { display: grid; }"),
        _page(marker="data flow", css=".signal-path { display: flex; }"),
        _page(marker="fail closed", css=".decision-state { border-inline-start: 1rem solid; }"),
    ]
    rendered = []
    for index, draft in enumerate(drafts):
        completed = _run(tmp_path, draft, output_name=f"lesson-{index}.html")
        assert completed.returncode == 0, completed.stderr
        rendered.append((tmp_path / f"lesson-{index}.html").read_text(encoding="utf-8"))
    assert len({hashlib.sha256(page.encode()).digest() for page in rendered}) == 3
    assert all(token in page for token, page in zip(
        ("architecture-map", "signal-path", "decision-state"), rendered, strict=True
    ))


# STUB: AC-0015
@pytest.mark.parametrize(
    ("literal", "category"),
    [
        ("Bearer abcdefghijklmnopqrstuvwxyz012345", "credential"),
        ("person@example.invalid", "email"),
        ("/Users/private-user/project", "user-home path"),
        ("x7Qm9P2vL4nR8sT1uW3yZ6aB0cD5eF7g", "high-entropy token"),
    ],
)
def test_publisher_refuses_sensitive_literals_without_echo(
    tmp_path: Path, literal: str, category: str
) -> None:
    """Sensitive values fail before output resolution and never enter errors."""
    completed = _run(tmp_path, _page().replace("Observed behavior.", literal))
    assert completed.returncode != 0
    assert category in completed.stderr.lower()
    assert literal not in completed.stderr
    assert not (tmp_path / "lesson.html").exists()
```

Stub registry: `test_publisher_injects_only_the_fixed_runtime_and_matching_csp`
(AC-0003/7/8), `test_publisher_rejects_size_and_encoding_before_output`
(AC-0003), `test_publisher_rejects_broken_document_and_teaching_structure`
(AC-0004/5), `test_publisher_rejects_active_or_external_html` (AC-0006),
`test_publisher_rejects_forbidden_css_capabilities` (AC-0007),
`test_publisher_rejects_missing_duplicate_or_misplaced_markers` (AC-0008),
`test_publisher_rejects_malformed_quiz_and_missing_css_floors` (AC-0009/10),
`test_publisher_default_output_is_dated_collision_resistant_and_owner_only`
(AC-0011),
`test_publisher_rejects_unconfined_symlinked_and_nonregular_input` (AC-0011),
`test_publisher_confines_and_atomically_publishes_owner_only` (AC-0011),
`test_publisher_preserves_three_independent_page_designs` (AC-0014), and
`test_publisher_refuses_sensitive_literals_without_echo` (AC-0015) all have
`stub: true`. Stub validation on 2026-09-26: the exact block compiled and all 40
collected cases earned their intended implementation-absent red from the
ignored scratch copy at `/private/tmp/explain-diff-t8-stub/`. Accepted paths
failed because the publisher entry point does not exist; refusal paths failed
because the absent entry point did not emit the required stable category. T8
must materialize the block at the verification artifact unchanged and record
the collected/pass/fail counts and node IDs in `notes/verification-ledger.md`
before T9 begins.

**Done when:** the suite compiles and earns implementation-absent reds without
weakening the completed publication and trust-boundary checks.

### T9: The guarded publisher preserves model-owned design

**Depends on:** T8

**Touches:** `packs/core/.apm/skills/explain-diff/scripts/**`,
`packs/core/.apm/skills/explain-diff/references/**`,
`packs/core/tests/skills/explain-diff/**`

**Tests:**

- Verification mode: **TDD** against T8's complete suite.
- Implement `publish_explanation.py` with pure parse/validate/inject functions
  ahead of the CLI and filesystem adapter. Use only Python 3.11 standard-library
  modules.
- Validate the exact authoring contract before resolving output. Reject unknown
  or active capabilities instead of rewriting them. Inject the fixed quiz
  runtime and its CSP hash only after the draft passes.
- Run bounded sensitive-literal detection before output resolution and report
  only a stable category. Keep semantic minimization in the skill rather than
  pretending the publisher can infer every private fact from arbitrary prose.
- Reuse the proven confinement and atomic-publication behavior, retaining owner
  mode, collision-resistant defaults, and concise UTF-8 error output.
- Delete the superseded JSON schema, archetype guide, and deterministic renderer
  only after the new suite owns their still-required safety guarantees.

**Done when:** the publisher suite passes, the meaningful mutations red their
named tests, and three differently designed fixtures survive publication without
converging on a shared shell, CSS system, or structure.

### T10: The skill composes pages directly and keeps a consistent floor

**Depends on:** T9

**Touches:** `packs/core/.apm/skills/explain-diff/SKILL.md`,
`packs/core/.apm/skills/explain-diff/references/html-authoring.md`,
`packs/core/.apm/skills/explain-diff/evals/**`, `packs/core/README.md`,
`packs/core/tests/pack/test_work_intake_surface.py`,
`docs/specs/explain-diff/notes/verification-ledger.md`

**Tests:**

- Verification mode: **goal-based check** plus real end-to-end publisher
  invocations. The public artifact is the published HTML path and bytes.
- Remove required archetype selection and JSON authoring. Ask the model to name
  the page's teaching concept, audience, central visual, and reading sequence,
  then author the complete document under the portable contract.
- Require three distinct workflow cases—architecture boundary, data flow, and
  fail-closed lifecycle—to use work-specific structure, CSS, visual treatment,
  typography, palette, density, and explanatory controls. Do not assert exact
  copy, class names, or a fixed layout, and do not let any fixture become a
  default house theme.
- Preserve evidence labels, four teaching roles, five-question quiz, source
  whitespace, accessibility and responsive floors, independence, least-authority
  metadata, exact-path reporting, and adopter-specific browser consent.
- Keep inline code and long paths wrappable while source and diagram blocks
  preserve whitespace in contained scrollers. Keep table words readable and
  scroll the table region when needed. Require fallback-tolerant typography and
  neutral, text-distinct quiz feedback whose incorrect state never inherits the
  success treatment. Treat print styling as an audience choice, not a light-theme
  mandate.
- Add workflow evals that replace credential-shaped values, email addresses,
  private hostnames, personal names, and user-home paths with generic
  placeholders while retaining the code path or data-flow shape being taught.
- Exercise the public publisher on all three fixtures and record their paths and
  structural distinctions. Browser inspection remains bounded by the exposed
  tool surface.

**Done when:** AC-0001, AC-0002, AC-0010, AC-0012–AC-0015 are covered by
workflow evidence and real publisher output, and T4 can regenerate matching
projections.

### T4: Published Core projections carry the amended skill

**Depends on:** T10

**Touches:** `packs/core/.claude-plugin/plugin.json`, canonical build inputs named
by T10; the build owns generated projection changes

**Tests:**

- Verification modes: **goal-based check** for manifests, build, projection
  parity, and gates; **visual / manual QA** for generated pages. Verification
  artifacts: command exits, targeted pytest results, source/projection hashes,
  and `notes/verification-ledger.md`. `no stub (goal-based/manual QA)` because
  build commands and user gestures are the contract surfaces.
- Retain the already selected Core `2.27.0` source and plugin versions; this is
  the same unreleased primitive, not a second release.
- Run the normal self-host projection, catalogue verification where the managed
  profile supports cleanup, and local gates `make lint-ruff lint-mypy`.
- Run the targeted publisher and Core pack-surface suites after projection.
- Record `skipped-no-browser` for the manual matrix when no runtime is exposed;
  do not convert source inspection into a visual claim.

**Done when:** AC-0012 and AC-0013 pass, generated outputs match canonical
source, local gates are green, and the verification ledger states the exact
visual-QA boundary.

## Rollout

The amended change remains the same next-minor Core pack release through the
existing catalogue build. It adds no infrastructure, migration, external
service, feature flag, dependency, or irreversible data change. Rollback is
removal of the new canonical skill plus matching manifest, documentation, eval,
test, and generated-projection entries in a later repository change.

## Risks

- Model-authored HTML could acquire active capabilities through an overlooked
  element, attribute, CSS escape, or publisher injection seam; a positive
  allowlist, explicit CSS refusals, no model scripts, CSP, and mutation-tested
  adversarial fixtures address that risk.
- A generic activation description could collide with document converters or code review; negative evals and the exact description keep the boundary on teaching how a code change works.
- Browser behavior differs by adopter; keeping it outside the renderer and requiring capability detection prevents a false universal promise.
- Generated projections could drift from canonical source; the standard build and catalogue verification own that risk.
- More visual freedom could encourage fabricated relationships or inaccessible
  composition; bounded evidence tracing, a portable authoring checklist, semantic
  role and quiz contracts, and manual-QA truthfulness keep design freedom tied to
  the change without reintroducing a page schema.

## Changelog

- 2026-09-25: spec approved by repository maintainer
- 2026-09-25: plan approved by repository maintainer
- 2026-09-25: controlled amendment opened by the scope owner to replace the fixed text-led composition with adaptive structured explainers; authority and reason are recorded in `notes/adaptive-explainer-amendment.md`
- 2026-09-25: amended adaptive-explainer spec approved by repository maintainer
- 2026-09-25: amended adaptive-explainer plan approved by repository maintainer
- 2026-09-26: controlled amendment opened after comparative manual QA showed
  that both the JSON contract and shared renderer suppressed work-specific page
  design; authority and evidence are recorded in
  `notes/model-owned-design-amendment.md`
- 2026-09-26: amended model-owned-design spec approved by repository maintainer
- 2026-09-26: amended model-owned-design plan approved by repository maintainer
