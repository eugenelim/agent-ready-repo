# Verified findings and gates

> Every renderer claim with source and confidence; the gates and their results.
> Part of [binder publishing architecture](README.md).

**Two renderers appear here, and only one of them is live.** Z1–Z4 are the
**Zensical** gates — the v1 renderer under D-B — and they are the ones a spec
author builds against. Q1–Q28 are **Quarto** findings, retained because a future
PDF or EPUB adapter would go through Quarto and would be built against them.
Where the two disagree about a behaviour, they are not in conflict: they describe
different renderers.

---

## Zensical findings and the Z-gates

Run **2026-08-06** against `zensical==0.0.53` in a clean virtualenv on
macOS/arm64, using the same discipline V1 established: **a real fixture and the
real emitted `zensical.toml`**, not a hand-written config the pack never emits.
The fixture is a five-chapter binder with a nested `nav`, a `custom_dir` theme, a
generated cover, fresh per-file frontmatter, a portable ` ```mermaid ` fence with
a `<br/>` node label, a class diagram using `<|--`, a literal `{{< env … >}}`, a
`${HOME}`, an admonition, and a cross-document `.md` link.

`[high]` throughout means direct execution against that fixture.

### Z1 — invocation, version probe, and where output lands

| # | Finding | Confidence |
|---|---|---|
| Z1a | **`zensical build` takes no positional directory.** Its only path input is `-f/--config-file PATH`; the other flags are `-c/--clean` and `-s/--strict`. The argv is therefore `[sys.executable, "-m", "zensical", "build", "-f", "<stage>/zensical.toml", "--strict"]` — list-form, no shell, no caller-supplied element. | **High — VERIFIED** |
| Z1b | **`--strict` is required, not optional.** Without it a build that emits warnings still **exits 0**. Verified exit codes: `--strict` with issues → **1**; `--strict` clean → **0**; no `--strict` with issues → **0**. A compiler that reported success on a warned build would publish a binder with dead links. | **High — VERIFIED** |
| Z1c | **`zensical.__version__` does not exist.** The module exposes `build`, `serve`, and `version` — and `zensical.version` is a *built-in function*, not a string, so a naive probe stringifies a function object rather than failing. The version probe is `importlib.metadata.version("zensical")`, which returns `"0.0.53"`. `python -m zensical --version` also prints it. | **High — VERIFIED** |
| Z1d | **`site_dir` and `docs_dir` are configurable and default to `site` and `docs`**, and Zensical itself rejects either resolving outside the project root, or the two being equal. Output is `site/`, not `_output/`. | **High — VERIFIED** (`zensical/config.py`) |
| Z1e | **Output and cache land relative to the config file's directory, not the process CWD.** Building `-f cachetest/zensical.toml` from a parent directory wrote `cachetest/site/` and `cachetest/.cache/`. `.cache/` is an undeclared write the design had not accounted for; it is inside the staging directory and therefore inside the workspace. | **High — VERIFIED** |
| Z1f | **`NO_COLOR=1` is not honoured** — diagnostics still carry ANSI SGR sequences. The adapter must strip them before parsing or re-emitting. Diagnostics are reported as `<staged-file>.md:LINE:COL`, which is exactly the anchor the `line-offset` mapping needs. | **High — VERIFIED** |

### Z2 — the config surface the adapter emits

| # | Finding | Confidence |
|---|---|---|
| Z2a | **The nested `nav` form is correct.** `{ "Part I — Evidence" = [ {…}, {…} ] }` renders as a titled sidebar group containing its children. The generator is told the structure and derives none of it. | **High — VERIFIED** |
| Z2b | **`markdown_extensions` REPLACES the scaffold set — it does not merge.** With the closed allowlist emitted, `pymdownx.tilde`, `pymdownx.caret`, `pymdownx.details`, `pymdownx.emoji`, `pymdownx.keys`, and `pymdownx.arithmatex` were all inert and their syntax rendered as literal text. This is the answer the design needed: **excluding `arithmatex` and `emoji` genuinely removes the MathJax and twemoji references**, rather than leaving a default in place underneath. | **High — VERIFIED** |
| Z2c | **Quoted dotted keys are accepted.** `"pymdownx.superfences" = { … }` parses to the extension named `pymdownx.superfences`. The scaffold's unquoted `pymdownx.superfences = { … }` is a TOML *dotted key* producing a nested table; both forms reach the same extension, and the quoted form is what the adapter emits because it is unambiguous. | **High — VERIFIED** |
| Z2d | **`custom_dir` works, and a `main.html` extending `base.html` can inject into `{% block extrahead %}`** — which lands in `<head>`, ahead of the bundle. Non-template files in the custom directory are **copied verbatim into `site/`**; template files are consumed. So the theme directory is a publication surface and only pack-owned assets may go in it. | **High — VERIFIED** |
| Z2e | **The `features` strings are accepted as given**, and `navigation.footer` does produce prev/next. | **High — VERIFIED** |
| Z2f | **`pymdownx.snippets` is commented out in the scaffold, not active.** An earlier claim that it was one of three defaults the allowlist removes was wrong about this one; `arithmatex` and `emoji` *are* scaffold defaults, `snippets` is not. Excluding it is still correct — it reads arbitrary files from disk — but it is a precaution, not a removal. | **High — VERIFIED** |
| Z2g | **A `nav` entry naming a file that does not exist produces no warning, even under `--strict`, and renders a dead sidebar link.** A missing chapter is silently navigable. **The adapter must assert every `nav` target exists on disk before invoking** — Zensical will not tell it. | **High — VERIFIED** |
| Z2h | **Zensical numbers nothing.** No chapter numbers, no appendix lettering, no `.unnumbered` equivalent. Q17's automatic appendix lettering is a *Quarto* behaviour with no counterpart here, so **`numbered` is compiler-emitted** — see [`binder-recipe.md`](binder-recipe.md). | **High — VERIFIED** |

### Z3 — Mermaid, and whether it is bundled

> **The answer is no.** The vendored `mermaid.min.js` and its delivery problem
> both stand.

| # | Finding | Confidence |
|---|---|---|
| Z3a | **The portable ` ```mermaid ` fence is read directly** and emitted as `<pre class="mermaid"><code>…</code></pre>`. No transformation, no line-count change, no cell-option injection. This is what deletes the Quarto staging transform. | **High — VERIFIED** |
| Z3b | **Mermaid itself is NOT bundled.** The theme bundle contains `it("https://unpkg.com/mermaid@11/dist/mermaid.min.js")` and fetches it **from the reader's browser at read time** whenever a `.mermaid` element mounts. A binder with a single diagram phones out to unpkg. | **High — VERIFIED** |
| Z3c | **Vendoring is supported, by a guard in the bundle itself:** `typeof mermaid == "undefined" || mermaid instanceof Element ? fetch(unpkg) : skip`. If a global `mermaid` is already defined, **no request is made.** So shipping `mermaid.min.js` in the pack's theme assets and defining the global before the bundle runs suppresses the fetch. | **High — VERIFIED** (source inspection of the emitted bundle) |
| Z3d | **`extra_javascript` is emitted *after* the bundle**, so using it for the vendored file is an execution-order race. **`custom_dir` + `{% block extrahead %}` is the deterministic form** — verified to place the script in `<head>`, before the bundle. This is why the adapter vendors through the theme rather than through `extra_javascript`. | **High — VERIFIED** |
| Z3e | **`<br/>` in a node label survives**, entity-escaped inside the `<pre>` and decoded by the browser as text content — the same mechanism Q28 recorded under Quarto. `<\|--`, `<\|..`, and `<-->` pass through unharmed. The label allowlist in [`security-profile.md`](security-profile.md) is verified under both renderers. | **High — VERIFIED** |
| Z3f | **`{{< env AWS_SECRET_ACCESS_KEY >}}` and `${HOME}` pass through as literal escaped text.** Confirms the Q11 attack surface does not exist here. | **High — VERIFIED** |

### Z4 — offline hardening, and V2b restated

| # | Finding | Confidence |
|---|---|---|
| Z4a | **`[project.theme.font] text = false, code = false` DOES NOT suppress Google Fonts — it emits a request for a typeface named `False`.** The rendered head carried `https://fonts.googleapis.com/css?family=False:300,300i,…%7CFalse:400,…`. The design specified this form and it is wrong. | **High — VERIFIED** |
| Z4b | **The correct form is scalar `font = false` on the theme table.** `base.html` guards the block with `{% if config.theme.font != false %}`. With `[project.theme] font = false`, both the `fonts.googleapis.com` stylesheet and the `fonts.gstatic.com` preconnect disappear. | **High — VERIFIED** |
| Z4c | **With `font = false` and the closed extension allowlist, the only `https://` strings left in the built HTML are one `zensical.org` attribution `<a href>`** — a link, not a fetch — **and two Font Awesome licence-comment URLs in the CSS.** Neither issues a request. | **High — VERIFIED** |
| Z4d | **V2b as previously written is unsatisfiable.** "Zero `https://` references anywhere in `_output/`, CSS included" cannot pass against a licence comment and an attribution anchor. Restated below as zero remote **subresource** references, which is the property that actually matters and is testable. | **High — VERIFIED** |
| Z4e | **Search is local and offline** — `site/search.json`, 1.7 KB for the fixture — and every asset reference is document-relative (`./assets/…`, `../assets/…`), so a published binder opens from `file://` with no server. | **High — VERIFIED** |

### The four findings that changed the design

**Z3b deletes a simplification that had been assumed.** The renderer-choice spike
recorded Mermaid as "renders from the portable fence" and stopped there; it did
not ask *where the JavaScript comes from*. It comes from unpkg, at read time, in
the reader's browser. The vendored `mermaid.min.js` stays, and Z3c/Z3d turn "we
will vendor it somehow" into a specified mechanism with a verified guard.

**Z4a is a specified control that does not work.** The design named a font-
suppression form, called it "required, not optional", and it emits a broken
request instead. This is the Q26 class of finding exactly: a control asserted from
the shape of a configuration surface rather than from running it.

**Z2b is the good news.** The closed extension allowlist behaves the way the
design needed — replacement, not merge — so the two CDN-bearing extensions are
genuinely gone rather than shadowed.

**Z2g is a gap in the renderer, not in the design, and the adapter has to cover
it.** A nav entry pointing at a file that was never staged is silently rendered as
a working-looking sidebar link. The adapter asserts nav-target existence itself.

### Z-gate status

| Gate | Claim | Status | Result |
|---|---|---|---|
| **Z1** | Invocation contract, version probe, exit codes, output location | **PASSED** 2026-08-06 | Argv, `--strict` necessity, and exit codes settled. **Corrected the design:** `zensical.__version__` does not exist (Z1c). |
| **Z2** | The emitted config — nav, `custom_dir`, `features`, `markdown_extensions` | **PASSED** 2026-08-06 | All four accepted as specified. **Settled the open question:** extensions replace, not merge (Z2b). **Surfaced Z2g and Z2h.** |
| **Z3** | Mermaid from the portable fence, and whether it is bundled | **PASSED with a finding** 2026-08-06 | Fence read directly; **Mermaid is not bundled** (Z3b). Vendoring mechanism verified (Z3c/Z3d). |
| **Z4** | Offline hardening | **RUN, FAILED, then FIXED** 2026-08-06 | The specified font form is wrong (Z4a); the correct one is verified (Z4b). V2b restated (Z4d). |
| **Z5** | Telemetry — does `zensical build` make any outbound request during the build? | **NOT RUN** | Requires a network-isolated runner. Same shape as V2 was for Quarto. Fallback: document any fetch and name its suppressing key. |
| **Z6** | Vendored Mermaid actually renders a diagram in a browser with egress blocked | **NOT RUN** | Z3c/Z3d verify the guard and the injection point by source and by emitted HTML; that a real browser then renders the diagram needs a headless run. Fallback: if the guard misbehaves, the diagram degrades to a readable `<pre>` of its own source rather than disappearing. |
| **V6** | Whether an agent's process working directory is the skill directory | **NOT RUN** | **Renderer-independent, and the one pre-D-B gate still live.** Invoke `python scripts/binder.py check` from a live session on each adapter and record the CWD. Until it returns, content-root resolution is specified defensively both ways and `--root` is effectively required on the agent surface — see [`invocation.md`](invocation.md) and [`overview.md`](overview.md). |

**Regression duty.** Z1–Z4 become CI assertions in
`tests/skills/publish-binder/integration/` once implemented, on every PR — they
need a 12.2 MB pip install, not a 236 MB toolchain, so there is no path filter to
argue about.

---

## Retained Quarto findings — evidence for a future PDF adapter

> **Not live design.** Everything below describes Quarto, which D-B removed from
> v1. It is retained because Q5, Q10a, Q11, Q17, Q18, Q26, Q27, and Q28 are
> hard-won by direct execution and are exactly what a future PDF or EPUB adapter
> would be built against. Read it as history, not as specification.

## Verified Quarto findings

Every claim below was checked against an official primary source on
**2026-08-06**. Confidence is stated per claim. Claims that could not be verified
are marked **UNVERIFIED**, are never load-bearing on their own, and each has a
gate in *Pre-implementation verification gates*.

| # | Finding | Confidence | Source |
|---|---|---|---|
| Q1 | Current stable release is **1.10.18** (2026-07-24). 1.11.x exists but is pre-release. | High | GitHub releases API, `quarto-dev/quarto-cli` |
| Q2 | Book projects use `project: type: book` with `book: chapters: […]`; `part:` nests `chapters:` and accepts either a `.qmd` file or a bare string title; `appendices:` is a sibling key. | High | quarto.org/docs/books/book-structure.html |
| Q3 | **`index.qmd` is required** — "because Quarto books also produce a website in HTML format". | High | ibid. |
| Q4 | You can link to unnumbered chapters but **cannot cross-reference** figures or tables inside them. | High | ibid. |
| Q5 | Mermaid requires the executable-cell fence `` ```{mermaid} ``. The portable GitHub fence `` ```mermaid `` is **not** recognized as a diagram. | High | quarto.org/docs/authoring/diagrams.html |
| Q6 | Diagram cell options use `%%\|` comments immediately after the opening fence; `%%\| label: fig-x` + `%%\| fig-cap: "…"` give figure numbering and `@fig-x` cross-references. | High | ibid. |
| Q7 | HTML output renders Mermaid via bundled JavaScript. PDF/DOCX render via PNG through Chrome/Edge. `mermaid-format` ∈ `{js, png, svg}`. | High | ibid. |
| Q8 | Diagram code is hidden by default; `%%\| echo: true` shows it. | High | ibid. |
| Q9 | `engine: markdown` specifies that **no execution engine is used**. Engine selection is otherwise driven by the presence of `{r}` / `{python}` / other executable blocks. | High | quarto.org/docs/computations/execution-options.html |
| Q10 | *"Engine extensions do not allow control over the cell language handlers for diagrams like mermaid and dot."* | High **as quoted** | quarto.org/docs/extensions/engine.html |
| Q10a | Mermaid **does** render under `engine: markdown` **and** `execute: enabled: false`: the diagram cell handler runs independently of the execution engine, emitting a numbered figure (`Figure 2.1`) wrapping `<pre class="mermaid mermaid-js">`. | **High — VERIFIED**, gate V1 executed 2026-08-06 | Quarto 1.10.18 rendering the real generated `_quarto.yml` (book project, both keys set) |
| Q11 | Body-level shortcodes are processed independently of execution: `{{< include >}}`, **`{{< env >}}`**, `{{< meta >}}`, `{{< var >}}`, `{{< embed >}}`, `{{< contents >}}`, and others. | High | quarto.org/docs/authoring/shortcodes.html |
| Q12 | HTML format accepts `include-in-header`, `include-before-body`, `include-after-body`, `css`, `theme`, `filters`, and `from` (with per-extension pandoc toggles). | High | quarto.org/docs/reference/formats/html.html |
| Q13 | The official PyPI package `quarto-cli` (1.10.18) is **sdist-only, 4.6 KB**. Its `setup.py` performs an unauthenticated `urllib.request.urlretrieve` of the platform release tarball from GitHub with **no checksum or signature verification**, and declares runtime dependencies `jupyter`, `nbclient`, `wheel`. Console script `quarto` shells to the bundled binary. | High | PyPI JSON API + inspection of `quarto_cli-1.10.18.tar.gz` |
| Q14 | No `@quarto/cli` npm package exists. | High | npm registry |
| Q15 | The Homebrew cask installs `quarto-1.10.18-macos.pkg` — a macOS package requiring administrator authorization. | High | formulae.brew.sh cask API |
| Q16 | Release assets are large: **236 MB** macOS tarball, ~140 MB Linux/Windows. Every asset carries a published SHA-256 (in `quarto-<ver>-checksums.txt` and in the GitHub API asset `digest` field). | High | GitHub releases API |
| Q17 | An **unnumbered book chapter** is produced by the `.unnumbered` class on its main heading — *"If you want a chapter to be unnumbered simply add the `.unnumbered` class to its main heading"*, e.g. `# Preface {.unnumbered}`. Appendices are auto-numbered uppercase-alpha with an inserted prefix. | High | quarto.org/docs/books/book-structure.html |
| Q18 | A shortcode is **escaped by extra braces** — *"Escape the shortcode reference with extra braces like this: `{{{< var version >}}}`"*. A `shortcodes=false` attribute on a code block also prevents processing. | High | quarto.org/docs/extensions/shortcodes.html |
| Q19 | Whether `quarto render` performs network access for a pure-Markdown HTML book with bundled Mermaid | **UNVERIFIED** — gate **V2** | — |
| Q20 | Fenced divs and attributed spans **do** survive `-raw_attribute` and `-raw_html`: `::: {.callout-note}` renders as `callout-note` and `[x]{.badge}` as `<span class="badge">` with every `from:` variant tested. The structural inference was correct — `raw_attribute` governs `` ```{=format} `` only. | **High — VERIFIED**, gate V3 executed 2026-08-06 | as Q10a |
| Q21 | `pip install` supports `--no-deps`, `--user`, and `--require-hashes`. | High | `python -m pip install --help`, pip as shipped with Python 3.13 |
| Q22 | **`uv tool install` has no `--no-deps` flag** (uv 0.11.33). It offers `--excludes <requirements-file>`, `--constraints`, and `--overrides`; dependency exclusion therefore requires a requirements file rather than a bare flag. `pipx` uses `--pip-args`. | High for `uv` (`uv tool install --help`, uv 0.11.33); the `pipx` form is **unverified** and is therefore never printed as an exact command — see rung 3 | — |
| Q23 | The `quarto-cli==1.10.18` sdist's SHA-256 is `20b8b672384ce9bf8a05fcc9e23f1e1f3ad6b9cb7657a476756da8f427101571`, and **pip reads `--hash` only from a requirements file** — `pip install --require-hashes <spec>` on the command line fails with "Hashes are required in --require-hashes mode". | High | obtained by running `python -m pip install --require-hashes 'quarto-cli==1.10.18' --dry-run`, which prints the hash in its error |
| Q24 | `python -m pip install --no-deps --user quarto-cli==1.10.18` installs a working Quarto on macOS and places the console script at `~/.local/bin/quarto`, reporting `1.10.18`. Behaviour on a **PEP 668 externally-managed interpreter** and on Windows remains **UNVERIFIED** — gate **V4** covers those two. | Medium — macOS verified 2026-08-06; other platforms gated | direct execution |
| Q26 | **`from: markdown-raw_html` breaks Mermaid.** Quarto's diagram handler emits its output *as raw HTML*, so disabling `raw_html` at the pandoc reader causes the emitted `<pre class="mermaid">` to be escaped and rendered as literal text inside an otherwise-correct figure. Isolated by bisection: `from: markdown-raw_attribute-raw_tex` → diagram renders; `from: markdown-raw_html` → diagram destroyed. Callouts and spans are unaffected either way. | **High — VERIFIED** 2026-08-06 | direct execution; see *The `from:` string, corrected by gate* |
| Q27 | **The stock Bootstrap theme imports Google Fonts at read time.** `site_libs/bootstrap/bootstrap-*.min.css` in a rendered book contains `@import url("https://fonts.googleapis.com/css2?family=Source+Sans+Pro…")`. Bootstrap's icon font is local; the typeface is not. The published HTML itself carries **zero** absolute `src=`/`href=` references. | **High — VERIFIED** 2026-08-06 | grep over a rendered `_output/` tree |
| Q28 | **`<br/>` inside a Mermaid node label survives and renders** under the corrected `from: markdown-raw_attribute-raw_tex`: pandoc entity-escapes it in the HTML source, the browser decodes it back as the `<pre>`'s text content, and Mermaid renders a line break. A **literal newline** inside a quoted label collapses to a space, and a backtick markdown-string label is passed through verbatim — so rewriting `<br/>` to `\n` would *silently lose* the break rather than preserve it. | **High — VERIFIED** 2026-08-06 | direct execution, three-label fixture |
| Q25 | Whether Quarto expands shortcodes (`{{< … >}}`) inside `title` / `book.title` metadata, as opposed to document bodies | **UNVERIFIED** — gate **V5**. Not relied upon: the emitted-string validator rejects the syntax regardless, so the control holds whichever way V5 resolves | — |

### The three findings that changed the design

**Q5 makes staging mandatory.** If Quarto accepted GitHub-style fences, a design
that copied sources verbatim would be viable. It does not, so every source file
must be transformed. Once transformation is unavoidable, it costs nothing extra
to make transformation the security boundary — which is why the scanner lives in
staging rather than in a pre-flight validator.

**Q11 destroys the comfortable assumption.** The brief warns *"Do not claim that
disabling Quarto execution alone neutralizes all unsafe input,"* and it is
correct. `{{< env >}}` renders an environment variable's value into the output
HTML — an AI-authored or externally supplied Markdown file containing
`{{< env AWS_SECRET_ACCESS_KEY >}}` exfiltrates a secret into a published
document with execution fully disabled. `{{< include ../../../.ssh/id_rsa >}}`
reads outside the content root. Neither is an execution-engine concern, and the
documentation offers no global disable switch. **Shortcode neutralization must
therefore be performed by this pack.** This single finding is the strongest
argument in the design for owning a staging scanner rather than delegating trust
to renderer configuration.

**Q10a is an inference, and the headline feature rests on it.** The natural worry
with `engine: markdown` is that switching execution off also switches Mermaid
off, forcing a choice between security and diagrams. Q10 makes that unlikely —
diagram cell handlers are described as outside the engine-extension surface — but
Q10 is a statement about the extension API, not about the `engine` or `execute`
YAML keys, and it says nothing at all about `execute: enabled: false`. Mermaid is
a v1 goal and is part of why Quarto was chosen over MkDocs, so **the inference is
gated (V1) rather than assumed**, with a named fallback.

---

## Pre-implementation verification gates — Quarto

> **Historical.** V1–V6 gated *Quarto* claims. D-B retired the renderer, and with
> it V2 (render-time network), V4 (the install-command platform matrix), and V5
> (shortcode expansion in metadata) — none of which has a subject any more. V2b's
> *concern* survives as **Z4**, restated; V6 (agent CWD) is renderer-independent
> and is still open. The rest is kept as the record a PDF adapter inherits.

**Three of these have been run, not deferred.** V1, V3, and V4-on-macOS were
executed against Quarto 1.10.18 on 2026-08-06, because a renderer decision resting
on an inference the author had marked UNVERIFIED is a decision the RFC cannot
ratify. Running them cost under an hour and **changed the design** — see Q26.

**One fixture, several assertions.** Testing each claim in isolation would verify
configurations the pack never emits. The gates run against **the real generated
`_quarto.yml`** — a book project with `engine: markdown`, `execute: enabled:
false`, the emitted `from:` string, the shipped theme, a `{mermaid}` cell, a
callout div, and an attributed span — because the interaction of the reader
toggles with diagram-cell output is precisely what no Q-row covered, and it is
precisely what broke.

| Gate | Claim | Status | Result / fallback |
|---|---|---|---|
| **V1** | Q10a — Mermaid renders with `engine: markdown` **and** `execute: enabled: false` | **PASSED** 2026-08-06 | The diagram handler runs independently of the execution engine, producing a numbered figure. Both keys stay. **The run also surfaced Q26** — the `-raw_html` reader toggle destroys the emitted diagram — which is the finding that changed the design. |
| **V1b** | The **exact v1 Mermaid emission** — `%%\| label:` with no `fig-cap:` | **PASSED** 2026-08-06 | Renders as a numbered figure (`Figure 2.1`) with class `quarto-uncaptioned` and no crossref warning. This corrected the design: numbering does **not** require a caption, as an earlier draft claimed. |
| **V1c** | Q28 — `<br/>` in a Mermaid node label | **PASSED** 2026-08-06 | Survives and renders; a literal-newline rewrite does not. Drove the label allowlist. |
| **V3** | Q20 — fenced divs and attributed spans survive the reader toggles | **PASSED** 2026-08-06 | `callout-note` and `<span class="badge">` render under every `from:` variant tested. Badges and editorial markers use callouts and fenced divs as planned; the plain-label fallback is not needed. |
| **V4** | Q24 — the printed rung-1 command installs a working `quarto` | **PARTIAL** — macOS passed 2026-08-06 | `python -m pip install --no-deps --user quarto-cli==1.10.18` produced `~/.local/bin/quarto` reporting `1.10.18`. **Still to run:** a PEP 668 externally-managed interpreter, and Windows. Fallback unchanged: surface the interpreter's own message, never add `--break-system-packages`, fall through to rung 2. |
| **V2** | Q19 — no network access *during* render | **NOT RUN** | Requires a network-isolated runner. Fallback: document the specific fetch and name the suppressing configuration key if one exists. |
| **V2b** | Q27 — no network access *at read time*, from the published tree | **RUN, FAILED** 2026-08-06 | The rendered HTML carries zero absolute `src=`/`href=` references — but the stock Bootstrap CSS contains `@import url("https://fonts.googleapis.com/…Source+Sans+Pro…")`, so a reader's browser phones out. **This is a design requirement, not a gate failure to accept:** a binder for an air-gapped review board or a privacy-sensitive client cannot fetch a typeface from a third party. **Superseded by Z4** under Zensical, which found the same class of leak, a different suppression key, and that the "zero `https://` anywhere" form of the assertion is unsatisfiable (Z4d). |
| **V5** | Q25 — shortcode expansion in `title` / `book.title` metadata | **NOT RUN** | Render the fixture with a `book.title` containing a literal `{{< env HOME >}}`, injected by the test to bypass the validator, and assert the value does not appear in the output. No fallback needed — the emitted-string validator (D36) rejects this input on every real path; V5 tells us whether the validator is the only thing standing between a title and an environment variable. |
| **V6** | Whether an agent's process working directory is the skill directory | **MOVED** — see the Z-gate status table above | Renderer-independent, so it did not retire with Quarto. Listed with the live gates rather than under this section's "not live design" heading. |

**What the executed gates changed.** V1 was expected to confirm a fact and instead
produced Q26, which removed a security layer the design had claimed and forced the
`from:` string to change. V2b was expected to be a formality and instead found that
the default theme leaks a read-time request to a third party. Both are the kind of
finding that surfaces two days into implementation if the gates are treated as
paperwork — which is the argument for running them before the RFC rather than
after.

**Regression duty.** All gates remain CI assertions in
`tests/skills/publish-binder/integration/` after they pass; settling a question and
guarding it are different jobs. See *CI provisioning* for which run on a path
filter.

---
