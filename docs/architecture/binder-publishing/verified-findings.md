# Renderer constraints and future-adapter evidence

> Build constraints established for the Zensical adapter and retained Quarto
> evidence for a possible future PDF or EPUB adapter.
> Part of [binder publishing architecture](README.md).

## Zensical adapter constraints

D-B selects Zensical for v1. The constraints below define the adapter contract
under that decision.

### Invocation and staging

- Invoke Zensical as `[sys.executable, "-m", "zensical", "build", "-f",
  "<stage>/zensical.toml", "--strict"]`. Do not use a shell string or any
  caller-supplied argv element.
- Probe the renderer with `importlib.metadata.version("zensical")`. Do not read
  `zensical.__version__`.
- `site_dir` and `docs_dir` are relative to the generated config. Keep both
  beneath the staging project and distinct. Zensical writes `site/` and `.cache/`
  there.
- Strip ANSI SGR sequences before parsing staged-file diagnostics. Map their
  line/column values through the adapter plan.
- Assert that every emitted `nav` target exists before invoking the renderer.
  Zensical otherwise renders a dead link without a strict-build failure.

### Config and offline assets

- Emit the complete `markdown_extensions` allowlist. Zensical replaces its
  scaffold extension set rather than merging it.
- Use a pack-owned `custom_dir` and `main.html` `extrahead` block for vendored
  Mermaid. `extra_javascript` loads after the theme bundle and is not safe for
  this ordering.
- Treat the theme directory as a publication surface. Only pack-owned assets may
  enter it.
- Disable remote fonts with `[project.theme] font = false`. Do not emit
  `[project.theme.font] text = false, code = false`.
- The offline assertion is zero remote subresource references, not zero
  `https://` strings. Local search and document-relative assets must work from
  `file://`.
- The build path must not make an outbound request. CI needs a kernel-level Linux
  egress detector with a negative control; a Python tracer is supplementary only.

### Markdown and Mermaid

- Preserve portable ` ```mermaid ` fence bodies byte-for-byte. Reject Mermaid
  directives, click/callback forms, and unsupported node-label syntax. `<br/>`,
  `<|--`, `<|..`, and `<-->` remain valid label content.
- Vendor a pinned, digest-recorded `mermaid.min.js` before the theme bundle. The
  renderer bundle otherwise fetches Mermaid at reader time.
- Zensical emits no chapter or appendix numbering. Emit the compiler ordinal as
  `data-ordinal`; D44 keeps it out of title and search-index text.
- D46 emits accessible-name attributes on the opening fence delimiter. HTML-escape
  values and reject `%%{` and newlines before the theme lifts them into Mermaid
  `accTitle:` and `accDescr:` source. Do not inject lines into the fence body.
- Browser tests must confirm that a rendered SVG carries the accessible name and
  description. A static check of the pre-render `<pre>` is invalid because the
  bundle replaces that element.

## Regression evidence

The Zensical adapter regression suite covers strict invocation, version probing,
staging paths, complete config emission, missing-nav refusal, offline assets,
network-denied build, vendored Mermaid rendering, and D46 browser accessibility.
`rollout.md` defines the required unit, integration, browser, and egress tests.

## Retained Quarto evidence

This section gates nothing today. It is retained for a possible future PDF or
EPUB adapter using Quarto.

- Quarto requires executable-style Mermaid fences; portable GitHub fences need a
  staging transform.
- Mermaid can render with `engine: markdown` and execution disabled.
- Shortcodes remain active independently of execution. A future adapter must
  neutralize them before rendering. D36 also rejects shortcode syntax in emitted
  strings that bypass the source-body scanner.
- Quarto automatic appendix and figure behavior differs from the Zensical
  adapter; do not reuse Zensical ordinal assumptions.
- `from: markdown-raw_html` destroys Quarto Mermaid output. Fenced divs and
  attributed spans survive the relevant reader toggles.
- The stock Quarto theme imports Google Fonts at read time.
- `<br/>` in Mermaid labels survives; replacing it with a literal newline loses
  the break.
- Quarto dependency installation, render-time network behavior, and metadata
  shortcode expansion require fresh verification before an adapter depends on
  them.
