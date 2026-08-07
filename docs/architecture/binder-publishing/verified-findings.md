# Verified findings and gates

> Every renderer claim with source and confidence; the gates and their results.
> Part of [binder publishing architecture](README.md).

**Two renderers appear here, and only one of them is live.** Z1–Z6 are the
**Zensical** gates — the v1 renderer under D-B — and they, with the
renderer-independent V6, are the ones a spec author builds against. Q1–Q28 are **Quarto** findings, retained because a future
PDF or EPUB adapter would go through Quarto and would be built against them.
Where the two disagree about a behaviour, they are not in conflict: they describe
different renderers.

---

## Zensical findings and the Z-gates

Run against `zensical==0.0.53` in a clean virtualenv on macOS/arm64 — **Z1–Z4 on
2026-08-06, Z5 and Z6 on 2026-08-07** — using the same discipline V1 established:
**a real fixture and the real emitted `zensical.toml`**, not a hand-written config
the pack never emits. The fixture is a five-chapter binder with a nested `nav`, a
`custom_dir` theme, a generated cover, fresh per-file frontmatter, a portable
` ```mermaid ` fence with a `<br/>` node label, a class diagram using `<|--`, a
literal `{{< env … >}}`, a `${HOME}`, an admonition, and a cross-document `.md`
link. The Z5/Z6 run extended it with the vendored `mermaid.min.js` delivered
through `main.html`'s `{% block extrahead %}`, which is what Z6 needed a browser
for.

`[high]` throughout means direct execution against that fixture.

> **The emitted config is transcribed, not generated, and that is the one soft
> spot in this evidence.** `binder.py` does not exist yet, so "the real emitted
> `zensical.toml`" means the block in
> [`zensical-adapter.md`](zensical-adapter.md#generated-zensicaltoml) transcribed
> byte-faithfully. It is still far better than a config invented for the test, but
> the gates become genuinely airtight only once the adapter emits the file and CI
> runs them against it.

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

### Z5 — telemetry: does `zensical build` reach the network?

> **No — and the stronger form of no.** Not "the build survives offline": **no
> outbound operation is attempted on any path this build exercises**, native or
> Python. Z5a states the scope precisely and it is the row to quote.

| # | Finding | Confidence |
|---|---|---|
| Z5a | **No code path exercised by a build of the emitted config attempts an outbound request.** Measured with `sandbox-exec` denying `network-outbound` **and sending `SIGKILL` on any attempt**, so an attempt is fatal rather than merely failed: the build exits **0** on both a cold and a warm cache. A kernel-level detector was chosen precisely because a Python-level one cannot see the compiled extension. Stated that way deliberately — the instrument is indifferent to *which* code path attempts egress, but it can only speak for the paths this fixture executes, so it is evidence about `build` on the emitted config, not a proof that no fetching code exists in the package. | **High — VERIFIED** |
| Z5b | **The isolation was validated before it was trusted, four ways** — DNS resolution blocked, IP-literal `connect` refused with `EPERM`, the same request succeeding unsandboxed, and local file IO still permitted. And the kill-on-egress profile was validated three ways: a trivial process survives (no false positive), an IP-literal `create_connection` is killed, a DNS-based `urlopen` is killed. **A gate whose negative control was never run proves nothing**, which is the discipline Z4a's failure argues for. | **High — VERIFIED** |
| Z5c | **A Python-level tracer over `getaddrinfo`, `create_connection`, `socket.connect`, `socket.connect_ex`, `urllib.request.urlopen`, and `http.client.HTTPConnection.request` logged zero calls during the build** — injected via `PYTHONPATH` so the real `python -m zensical build` argv was preserved. Its self-test logged 9 hits for a known request, so the zero is a measurement rather than a broken probe. | **High — VERIFIED** |
| Z5d | **The output is byte-identical with and without network access.** `diff -r` over the two `site/` trees from a network-allowed build and a network-denied build reports no difference, so nothing fetched contributes to the artifact. `--clean` also exits 0 under denial. | **High — VERIFIED** |
| Z5e | **`zensical` ships a compiled `zensical.abi3.so`, and it does link `_socket`, `_getaddrinfo`, and `_recv` from libSystem** — so network *capability* is present and a source-only grep would have missed it. The capability is consistent with the `serve` verb, which needs a listening socket; `serve` is never invoked. There are no hardcoded remote URL strings in the extension and no telemetry, analytics, or update-check code in the Python sources; **the extension itself is covered by Z5a rather than by inspection**, which is the honest split given that this row's whole point is that a source grep cannot see into it. **Z5a is what covers this**, and it is the reason the gate needed a kernel-level instrument rather than a library-level one. | **High — VERIFIED** |
| Z5f | **`zensical/extensions/macros.py` shells out to `git log` and `git rev-parse` via `subprocess.check_output`.** It registers as the `macros` extension, which is **outside the closed allowlist**, so it is inert under the emitted config — independent support for the allowlist being a replacement (Z2b) rather than an addition. Not a network finding, and recorded here because a `git` subprocess in the renderer is exactly the kind of thing the design's *no path to poison* argument should be checked against. | **High — VERIFIED** |
| Z5g | **The installed dependency set matches the design's list exactly** — `click`, `deepmerge`, `jinja2`, `markdown`, `pygments`, `pymdown-extensions`, `pyyaml`, `tomli`. `importlib.metadata.version("zensical")` returned `0.0.53`, re-confirming Z1c. | **High — VERIFIED** |

### Z6 — does vendored Mermaid render in a real browser with egress blocked?

> **Rendering: yes. The accessible name: no.** The vendoring mechanism
> [`zensical-adapter.md`](zensical-adapter.md) specifies works exactly as
> specified. The *accessibility* claim built on top of it does not, and the way it
> fails is worse than a plain absence.

Three headless-Chromium runs over the built fixture from `file://`, every
non-`file://` request logged and aborted in the blocked runs. The positive control
ran **first**, so both detectors were shown to work before the gate run was
trusted:

| Run | Vendored | Egress | unpkg | Diagrams | Accessible name |
|---|---|---|---|---|---|
| positive control | no | allowed | **2 requests** | 2 rendered | empty |
| degraded | no | blocked | 1 attempt, `net::ERR_FAILED` | 0 | **present** |
| **gate** | **yes** | **blocked** | **none** | **2 rendered** | **empty** |

| # | Finding | Confidence |
|---|---|---|
| Z6a | **The vendored bundle renders the diagrams with egress blocked, and issues no request of any kind.** The gate run produced two real SVGs — `role="graphics-document document"`, `aria-roledescription="flowchart-v2"`, laid out at 423 px and 73 px — with **zero remote requests**, unpkg or otherwise. Z3c/Z3d were verified by source and by emitted HTML; this is the browser confirming them. | **High — VERIFIED** |
| Z6b | **The guard is suppressed because mermaid's own distribution defines the global.** `mermaid@11`'s last line is `globalThis["mermaid"] = globalThis.__esbuild_esm_mermaid_nm["mermaid"].default`, so a plain `<script src>` satisfies `typeof mermaid == "undefined"` → false. Worth stating because the file's *first* line assigns into an esbuild namespace, and a reader checking only that would conclude vendoring cannot work. | **High — VERIFIED** |
| Z6c | **`extrahead` places the vendored script in `<head>` and the theme bundle loads from `<body>`** — verified in the built page, so the ordering Z3d established by inspection holds at runtime. | **High — VERIFIED** |
| Z6d | **The accessible name does NOT survive into the rendered SVG, and `attr_list` on the fence is the wrong mechanism.** The bundle mounts a diagram with `e.replaceWith(r)` where `r = A("div",{class:"mermaid"})` — **a fresh `div` carrying only `class`** — so every attribute on the `<pre>` is discarded. Measured live: `div attrs: {"class":"mermaid"}` for every diagram. The SVG then lands in `attachShadow({mode:"closed"})`, confirmed by `div.shadowRoot === null` from page script. | **High — VERIFIED** |
| Z6e | **The failure inverts, which is why it would have shipped.** In the degraded run the name **is** in the accessibility tree — `('image', 'Diagram 3.2: ledger write path')` — because the `<pre>` is still there. Under the specified mechanism **a named diagram and a rendered diagram are mutually exclusive**: the check passes exactly when the feature is broken. A CI assertion written against the static HTML would have stayed green forever. | **High — VERIFIED** |
| Z6f | **Three replacement routes were measured, and the adopted one names the graphic itself at zero line cost.** The compiler emits `data-a11y-name` / `data-a11y-desc` on the fence's opening delimiter via `attr_list`, and the pack's theme lifts them into the Mermaid source as `accTitle:` / `accDescr:` before the bundle mounts. Measured: `role='graphics-document'` with **name** `'Diagram 3.1 — ledger write path (RFC-0091)'` **and description** `'Client calls the API gateway, …'`, real `<title>`/`<desc>` inside the shadow SVG, diagram rendered, **zero remote requests**. This is D46. | **High — VERIFIED** |
| Z6g | **Both rejected routes work and both cost something the adopted one does not.** *Injecting `accTitle:` into the staged fence body* names the graphic identically but writes into the body, which is the transformation this adapter does not do. *A `<figure role="group" aria-label>` wrapper* survives `replaceWith` and was measured naming a region (`role='group'` with the right name, diagram rendered) — but it names a **container, not the graphic**, has no `accDescr` equivalent, needs a duplicate literal in the `<figcaption>`, and **inserts lines around every diagram**, which breaks the single-integer `line-offset` the whole per-file transformation rests on. | **High — VERIFIED** |
| Z6h | **An unescaped `attr_list` value is an HTML-injection channel; escaping closes it completely.** A value containing `"` **terminates the attribute** and the remainder becomes markup — a label of `Diagram & "3.1" <script>x</script>` emitted a **live `<script>x</script>`** into the published page. HTML-escaping the value (`&`, `<`, `>`, `"`, `'`) closes it and **round-trips exactly**: `Ledger & payments "3.1" — l'architecture réseau` reached the accessible name character-for-character, ampersand, quotes, em dash, apostrophe and accents intact. | **High — VERIFIED** |
| Z6i | **The hazard that escaping does *not* close is the value's real sink: Mermaid source.** The theme lifts the value into an `accTitle:` line, so the value is evaluated by Mermaid, not only by an HTML parser. Measured with escaping applied throughout: international text is safe — `Diagram 3.1 — Réseau : l'architecture 漢字` round-trips exactly, and so does `<b>angle</b>`, which does **not** truncate. But **`%%{init:{"theme":"dark"}}%%` was consumed as a Mermaid directive** — stripped from the accessible name and processed by the renderer, which is precisely the construct the scanner rejects in *authored* fence bodies. And **an embedded newline destroyed the diagram** — that fence produced no `graphics-document` at all while its siblings rendered. So the control is escape-for-HTML **plus reject-for-Mermaid** on `%%{` and newlines, and **an ASCII allowlist is the wrong control** — it would mangle `Réseau` and drop 漢字 to nothing for no gain, in the one kind of string that exists to be read aloud. | **High — VERIFIED** |
| Z6j | **The theme step has no ordering race, and its failure mode is a missing name rather than a missing diagram.** A `MutationObserver` registered in `<head>` processes each `pre.mermaid` as the parser inserts it — strictly before `DOMContentLoaded`, so strictly before any mount. **Re-measured with the `DOMContentLoaded` fallback removed**, so the result is attributable to the observer alone and not to a belt-and-braces pair, and on a **sixty-edge fence** as well as a two-line one, so it is not an artifact of a diagram small enough to arrive in a single parse chunk. Both named, both rendered, no page errors, zero remote requests. With the step absent the diagram still renders, unnamed (Z6a is that case). | **High — VERIFIED** |
| Z6k | **The graceful degradation is confirmed, not merely hoped.** With the bundle unreachable the reader sees the diagram's own source as visible preformatted text — measured `flowchart TD\n    A[Client] --> B[API gateway]\n …` — because the mount strips the `mermaid` class before awaiting the loader and never reaches the replacement. | **High — VERIFIED** |
| Z6l | **The vendored file is copied verbatim into `site/assets/javascripts/`, merging with Zensical's own asset directory, and adds 3.5 MB to every published binder.** A consequence of Z2d's "the theme directory is a publication surface", now measured. Not a defect — it is the price of offline Mermaid — but it belongs in the size expectations rather than being discovered by an adopter. | **High — VERIFIED** |
| Z6m | **The version the bundle asks for is the floating `mermaid@11` tag**, which resolved to 11.16.1 during this run. An unpinned input, recorded as a risk rather than a cost: the guard-suppression mechanism (Z6b) is a property of the esbuild distribution, not of a patch version, but the pack should vendor a pinned version with a recorded digest. | **High — VERIFIED** |
| Z6n | **D46 rests on two upstream behaviours that are neither documented contracts nor stability promises, and they are named here rather than left implicit.** (i) Mermaid's `accTitle:` / `accDescr:` directives and the `<title>`/`<desc>` they generate; (ii) the theme bundle mounting diagrams *after* parse, which is what lets a `<head>`-registered observer precede it. Both are verified against `zensical==0.0.53` and `mermaid@11.16.1`, both sit under an alpha pin, and **a change in either breaks the accessible name while leaving the diagram rendering perfectly** — the Z6e failure shape again. This is the specific reason Z6 has regression duty rather than retiring green. | **High — VERIFIED** as behaviour; **explicitly not** a stability guarantee |

### The findings that changed the design

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

**Z6d is the most instructive of the corrected controls, because it is the only one
that was wrong about a *runtime*.** Z1c and Z4a were both wrong about a
*configuration surface* — the design read a key's shape and inferred its behaviour.
Z6d is a different mistake: the design reasoned about the HTML the compiler emits
and never asked what the client-side bundle does to it. It replaces the element the
attributes are on. And Z6e is the part that earns the gate its cost — the mechanism
fails in the direction that *passes* a static check, so the only instrument that
could have caught it is the browser this gate finally ran.

**Z6h and Z6i have the widest reach, and neither was what the gate went looking
for.** Chasing a replacement for Z6d turned up that unescaped `attr_list` values
terminate on a quote, so any compiler-emitted attribute is an HTML-injection channel
— and `attr_list` is how this design emits `data-ordinal` (D44) and its badge and
marker spans too. **The first control drafted for it was wrong, and re-measuring is
what caught that**: escaping was dismissed as double-encoding and an ASCII allowlist
specified instead, when in fact a single escape round-trips the value exactly,
accents and CJK included, and the allowlist would have silently mangled the one class
of string that exists to be read aloud. The hazard escaping genuinely cannot reach is
the *second* hop — the value becomes a line of Mermaid source — where `%%{init:}%%`
is consumed as a **directive**, arriving through a channel the scanner never
inspects. Escape for HTML, reject for Mermaid. **A control asserted from the shape of
a pipeline rather than run through it: the Q26 class of error, committed while
documenting a gate whose whole subject is that class of error.**

### Z-gate status

| Gate | Claim | Status | Result |
|---|---|---|---|
| **Z1** | Invocation contract, version probe, exit codes, output location | **PASSED** 2026-08-06 | Argv, `--strict` necessity, and exit codes settled. **Corrected the design:** `zensical.__version__` does not exist (Z1c). |
| **Z2** | The emitted config — nav, `custom_dir`, `features`, `markdown_extensions` | **PASSED** 2026-08-06 | All four accepted as specified. **Settled the open question:** extensions replace, not merge (Z2b). **Surfaced Z2g and Z2h.** |
| **Z3** | Mermaid from the portable fence, and whether it is bundled | **PASSED with a finding** 2026-08-06 | Fence read directly; **Mermaid is not bundled** (Z3b). Vendoring mechanism verified (Z3c/Z3d). |
| **Z4** | Offline hardening | **RUN, FAILED, then FIXED** 2026-08-06 | The specified font form is wrong (Z4a); the correct one is verified (Z4b). V2b restated (Z4d). |
| **Z5** | Telemetry — does `zensical build` make any outbound request during the build? | **PASSED** 2026-08-07 | **No attempt is made at all**, not merely "the build survives offline": exits 0 with `SIGKILL` armed on any outbound operation, cold and warm cache, and the output is byte-identical to a network-allowed build (Z5a, Z5d). Isolation validated by seven controls before the result was accepted (Z5b). No fallback was needed. **Surfaced Z5e** (the compiled extension links network symbols — capability present, unused) **and Z5f** (`macros` shells to `git`, and is outside the allowlist). |
| **Z6** | Vendored Mermaid actually renders a diagram in a browser with egress blocked | **PASSED on rendering; FALSIFIED the accessible-name claim** 2026-08-07 | The vendoring mechanism works: two diagrams render from the vendored copy with **zero remote requests** (Z6a–Z6c), and the degradation fallback is confirmed benign rather than assumed (Z6j). **Corrected the design:** attributes on the `<pre>` are destroyed at render time, so the specified `attr_list` accessible name never reaches the SVG (Z6d) — and it survives only when the diagram *fails* (Z6e). A replacement that names the graphic itself, adds no lines, and leaves the fence body untouched is verified and adopted as **D46** (Z6f, Z6i), with the two rejected routes and their costs recorded (Z6g). **Surfaced Z6h** — `attr_list` values terminate on a quote, which is an injection channel wider than this gate's subject. |
| **V6** | Whether an agent's process working directory is the skill directory | **ANSWERED — no** 2026-08-07 | **It is the session's project root, which is the content root.** Measured on `claude-code` — the shipped `mermaid-renderer` skill's own documented `python scripts/render_mermaid.py --check` **fails** with the skill actively loaded, while the same script via the harness-supplied absolute base directory succeeds — and on `codex`, whose session header prints `workdir: <project-root>` and whose `pwd` returns it. **Unmeasured: `copilot`, `cursor`, `gemini`** (not installed) **and `kiro-ide` / `kiro-cli`** (the `kiro` binary is the IDE launcher; no headless agent CLI). So rules 2–4 are not skipped in practice, rule 4 does the work, and **`--root` is no longer effectively required** — see [`invocation.md`](invocation.md) and [`overview.md`](overview.md). The self-realpath guard is retained for the unmeasured adapters. |

**Regression duty.** Z1–Z6 become CI assertions in
`tests/skills/publish-binder/integration/` once implemented, on every PR — they
need a 12.2 MB pip install, not a 236 MB toolchain, so there is no path filter to
argue about. **Z5 and Z6 need more than the others, and Z5's instrument does not
port.** Z5 was measured with `sandbox-exec`, which is macOS-only — a Linux runner
needs a network namespace or a seccomp filter instead, **and its own negative
control**, because a denial mechanism that silently fails open turns this gate into
a green light. Z6 needs a headless browser, the one dependency the design otherwise
avoids. Both are worth it, and Z6e is the argument: the mechanism it caught fails in
the direction a static assertion reads as green.

**What the executed Z5/Z6 run cost, since the gates were nearly deferred to
implementation.** Under two hours, and it closed the last renderer question,
falsified a specified accessibility control, and replaced it with a verified
mechanism. The alternative was discovering Z6d when a reader with a screen reader
opened a published binder.

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
> *concern* survives as **Z4**, restated; V2's own concern survives as **Z5**, run
> and closed; V6 (agent CWD) is renderer-independent and was answered on
> 2026-08-07. The rest is kept as the record a PDF adapter inherits.

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
| **V4** | Q24 — the printed rung-1 command installs a working `quarto` | **RETIRED by D-B** (was PARTIAL — macOS passed 2026-08-06) | `python -m pip install --no-deps --user quarto-cli==1.10.18` produced `~/.local/bin/quarto` reporting `1.10.18`. **Still to run:** a PEP 668 externally-managed interpreter, and Windows. Fallback unchanged: surface the interpreter's own message, never add `--break-system-packages`, fall through to rung 2. **The residue is retired, not outstanding:** the PEP 668 and Windows runs would have gated a *Quarto* install command that no longer exists on any code path. A future PDF adapter inherits both the finding and the unrun cases. |
| **V2** | Q19 — no network access *during* render | **NOT RUN against Quarto; SUPERSEDED by Z5** | Never run against `quarto render`, and it will not be — D-B retired the renderer. The question itself was renderer-independent, moved to **Z5**, and answered there on 2026-08-07. Recorded this way for the same reason V2b is: a row reading only `NOT RUN` invites a reader to think the concern is still open. |
| **V2b** | Q27 — no network access *at read time*, from the published tree | **RUN, FAILED** 2026-08-06 | The rendered HTML carries zero absolute `src=`/`href=` references — but the stock Bootstrap CSS contains `@import url("https://fonts.googleapis.com/…Source+Sans+Pro…")`, so a reader's browser phones out. **This is a design requirement, not a gate failure to accept:** a binder for an air-gapped review board or a privacy-sensitive client cannot fetch a typeface from a third party. **Superseded by Z4** under Zensical, which found the same class of leak, a different suppression key, and that the "zero `https://` anywhere" form of the assertion is unsatisfiable (Z4d). |
| **V5** | Q25 — shortcode expansion in `title` / `book.title` metadata | **NOT RUN** | Render the fixture with a `book.title` containing a literal `{{< env HOME >}}`, injected by the test to bypass the validator, and assert the value does not appear in the output. No fallback needed — the emitted-string validator (D36) rejects this input on every real path; V5 tells us whether the validator is the only thing standing between a title and an environment variable. |
| **V6** | Whether an agent's process working directory is the skill directory | **MOVED, then ANSWERED** 2026-08-07 — see the Z-gate status table above | Renderer-independent, so it did not retire with Quarto. Listed with the live gates rather than under this section's "not live design" heading, and answered there. |

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
