# Verified findings and gates

> Every Quarto claim with source and confidence; the gates and their results.
> Part of [binder publishing architecture](README.md).

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

## Pre-implementation verification gates

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
| **V2b** | Q27 — no network access *at read time*, from the published tree | **RUN, FAILED** 2026-08-06 | The rendered HTML carries zero absolute `src=`/`href=` references — but the stock Bootstrap CSS contains `@import url("https://fonts.googleapis.com/…Source+Sans+Pro…")`, so a reader's browser phones out. **This is a design requirement, not a gate failure to accept:** the shipped `binder.scss` must override the theme's font stack with a system-font stack, and V2b asserts **zero** `https://` references anywhere in `_output/` — CSS included. A binder for an air-gapped review board or a privacy-sensitive client cannot fetch a typeface from a third party. |
| **V5** | Q25 — shortcode expansion in `title` / `book.title` metadata | **NOT RUN** | Render the fixture with a `book.title` containing a literal `{{< env HOME >}}`, injected by the test to bypass the validator, and assert the value does not appear in the output. No fallback needed — the emitted-string validator (D36) rejects this input on every real path; V5 tells us whether the validator is the only thing standing between a title and an environment variable. |
| **V6** | Whether an agent's process working directory is the skill directory | **NOT RUN** | Invoke `python scripts/binder.py check` from a live session on each adapter and record the CWD. Until it returns, content-root resolution is specified defensively both ways — see *What "repository scope" means outside Git*. |

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
