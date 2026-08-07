# Z5 / Z6 / V6 — executed 2026-08-07

Environment: `zensical==0.0.53` in a clean venv, Python 3.13.13, macOS/arm64
(Darwin 25.5.0). Chromium via Playwright. Fixture: `make_fixture.py` in this
directory — the real emitted `zensical.toml` transcribed from
`zensical-adapter.md` § *Generated `zensical.toml`* (scalar `font = false`, closed
extension allowlist, nested `nav`, `custom_dir = "theme"`), five chapters + cover
+ appendix, vendored `mermaid.min.js` (mermaid@11 → 11.16.1, sha256
`18327bef70d96fb505fe7287d9f6a7362ebf07ff6576ddfaffb1a06f3e1a2954`) injected via
`main.html` `{% block extrahead %}`.

---

## Z5 — no outbound request during the build. PASSED.

**Method, in three layers, each with a control.**

1. *Python-level tracer* (`tracehome/sitecustomize.py`, injected via `PYTHONPATH`
   so the real `python -m zensical build` argv is preserved) wrapping
   `getaddrinfo`, `create_connection`, `socket.connect`, `socket.connect_ex`,
   `urllib.request.urlopen`, `http.client.HTTPConnection.request`.
   **Self-test:** a known `urlopen` produced 9 trace hits. **Build: 0 hits.**
2. *Kernel-level attempt detector* — `sandbox-exec` with
   `(deny network-outbound (with send-signal SIGKILL))`, so any outbound
   operation from **any** code path, Python or native, kills the process.
   **Controls:** trivial python survives (exit 0, no false positive); an
   IP-literal `create_connection` is killed (exit 137); a DNS-based `urlopen` is
   killed (exit 137). **Build: exit 0, cold cache and warm cache.**
3. *Completion + output equality* — `(deny network*)` build vs network-allowed
   build: both exit 0, and `diff -r` over the two `site/` trees is **identical**,
   so nothing fetched differentiates the output. `--clean` also exits 0.

Sandbox isolation itself was validated four ways before being trusted: DNS
resolution blocked, IP-literal `connect` blocked with `EPERM`, unsandboxed
control succeeds, local file IO still permitted.

**Result.** `zensical build` makes **no outbound network request** during a
build. Not "succeeds offline" — no attempt is made at all, from any code path.

**Adjacent findings from the same run.**

- `zensical` ships a compiled `zensical.abi3.so`, which a Python-source grep
  cannot see into. It links `_socket`, `_getaddrinfo`, `_recv` from libSystem, so
  network *capability* is present — consistent with the `serve` dev-server verb,
  which needs a listening socket. Layer 2 covers this: capability present, no use
  during `build`. No hardcoded remote URL strings and no telemetry, update-check,
  or analytics code in the package.
- `zensical/extensions/macros.py:777` shells out to **`git log` / `git rev-parse`
  via `subprocess.check_output`**. The extension registers as `macros`
  (`zensical.extensions.macros`), which is **outside the design's closed
  allowlist**, so it is inert — and this is independent support for the allowlist
  being closed rather than additive.
- Installed dependency set matches `zensical-adapter.md` exactly: `click`,
  `deepmerge`, `jinja2`, `markdown`, `pygments`, `pymdown-extensions`, `pyyaml`,
  `tomli`.
- Z1c, Z1e, Z4b, Z4c, Z4d, Z4e all re-confirmed incidentally.
  `importlib.metadata.version("zensical")` → `0.0.53`. `site/` and `.cache/`
  landed beside the config file. With `font = false`, the only `https://` in
  `*.html` is the `zensical.org` attribution anchor; in `*.css`, two Font Awesome
  licence comments; no `fonts.googleapis`/`gstatic` anywhere; the only static
  off-host subresource-shaped match is `href="https://zensical.org/"`, a link.
  `search.json` 3.4 KB, asset refs document-relative.

---

## Z6 — vendored Mermaid renders with egress blocked. PASSED on rendering,
## FAILED on the accessible name.

**Method.** Three headless-Chromium runs over the built fixture from `file://`,
requests logged, all non-`file://` requests aborted in the blocked runs. The
bundle moves the SVG into a **closed** shadow root, so the DOM is read through
CDP `DOM.getDocument(pierce=True)` walking every `shadowRoots` entry, and the
accessible name is read from `Accessibility.getFullAXTree`, not inferred from
attributes.

| Run | Vendored | Egress | unpkg requests | Diagram SVGs | Accessible name |
|---|---|---|---|---|---|
| positive control | no | allowed | **2** (`mermaid@11` → `11.16.1`) | 2 rendered | empty |
| degraded | no | blocked | 1 attempted, `net::ERR_FAILED` | 0 | **present** |
| **gate** | **yes** | **blocked** | **0** | **2 rendered** | **empty** |

**What passed.** In the gate run the diagrams render as real SVGs —
`role="graphics-document document"`, `aria-roledescription="flowchart-v2"`,
laid-out heights 423 px and 73 px — with **zero remote requests of any kind**.
The vendored file lands in `<head>` (`../assets/javascripts/mermaid.min.js`)
ahead of the bundle in `<body>`, so Z2d/Z3d hold at runtime, and the guard is
suppressed because mermaid@11's last line is
`globalThis["mermaid"] = globalThis.__esbuild_esm_mermaid_nm["mermaid"].default`.
The mechanism `zensical-adapter.md` § *Vendoring Mermaid* specifies **works**.

**What failed.** The accessible name does **not** survive into the rendered SVG.
The bundle's mount does `e.replaceWith(r)` where `r = A("div",{class:"mermaid"})`
— a **fresh div carrying only `class`**. Measured live: `div attrs:
{"class":"mermaid"}` for every diagram, and `div.shadowRoot === null` from page
JS, confirming `attachShadow({mode:"closed"})`. So **every attribute on the
`<pre>` is discarded at render time** — `aria-label`, `role`, and any `data-*`.
`rollout.md` § *Accessibility smoke checks* hopes "the rendered SVG carries the
name through"; it does not.

The degraded run makes the failure precise and worse than a simple absence: the
name is present in the AX tree (`('image', 'Diagram 3.2: ledger write path')`)
**only when the diagram fails to render**. Under the specified mechanism, a named
diagram and a rendered diagram are mutually exclusive.

**Two suppressing mechanisms verified, in the Z4 fallback style.**

- **Route A — `accTitle:` / `accDescr:` inside the Mermaid source.** Works:
  the SVG carries `<title id="chart-title-__mermaid_0">Diagram 3.1 ledger write
  path</title>` and a `<desc>`, and the AX tree reports
  `('graphics-document', 'Diagram 3.1 ledger write path')`. Cost: the adapter
  must write into the fence body, which contradicts *Mermaid fences are
  untouched*.
- **Route C — a `<figure role="group" aria-label="…">` wrapper with a
  `<figcaption>`.** ~~Works and is the better fit~~ — **SUPERSEDED, see Route D
  below.** Adversarial review caught that a build-time wrapper inserts lines around
  every diagram, breaking the single-integer `line-offset`, and that it names a
  container rather than the graphic. Works, and rejected: `replaceWith` replaces only the
  `<pre>`, so the wrapper survives intact — measured
  `role='group' name='Diagram 3.1: ledger write path'` with the diagram rendered
  (height 423) and zero remote requests. Verified in the clean form, with no
  `markdown="span"` and **no `md_in_html` in the allowlist**, so it costs the
  extension set nothing. **Fence body untouched.**
- **Route B — `attr_list` on the fence, the specified form — fails.**

**Also found.** The static check in `rollout.md` asserts the name lives "in its
`attr_list` attributes" on the `<pre>`. Producing that requires the *brace* fence
form `` ```{.mermaid aria-label="…"} `` — verified to emit
`<pre class="mermaid" aria-label="…" role="img">` — which is itself a
transformation of the authored fence. So even the static half of the check
conflicts with *Mermaid fences are untouched*.

**Degradation confirmed benign.** With the bundle unreachable, the reader sees
the diagram's own source as visible preformatted text (measured:
`flowchart TD\n A[Client] --> B[API gateway]\n …`), because `Zs(e)` strips the
`mermaid` class before awaiting the loader and never reaches the replacement.

**One operational note.** The vendored file is copied verbatim into
`site/assets/javascripts/`, merging with Zensical's own asset directory and
adding **3.5 MB** to every published binder.

---

## V6 — is an agent's process working directory the skill directory? NO.

**claude-code, measured with the `mermaid-renderer` skill actively loaded.** Its
own documented Step 1, run verbatim:

```
$ python scripts/render_mermaid.py --check
python: can't open file '<project-root>/scripts/render_mermaid.py': [Errno 2] …
exit=2
```

`os.getcwd()` during the same active invocation is the **project root**, not the
skill directory; `cwd == scriptdir` is `False` both for a script in `/tmp` and for
a probe placed inside the installed skill directory itself. The same script
invoked through the absolute base directory the harness supplies in the
skill-load preamble (`Base directory for this skill: …`) succeeds: `OK: mmdc is
on PATH`, exit 0.

**codex, measured from a live `codex exec` session.** The session header prints
`workdir: <project-root>`, each command is run as `/bin/zsh -lc … in
<project-root>`, and `pwd` returns the project root.

**Coverage, stated honestly.** Measured: `claude-code`, `codex`. Not measured
here: `copilot`, `cursor`, `gemini` (not installed), `kiro-ide` / `kiro-cli`
(`/usr/local/bin/kiro` is the IDE launcher — no headless agent CLI). Both
measured adapters answer identically, and the mechanism is the same in each: the
agent runs shell commands with the CWD of the session's project root.

**Consequence for the design.** The premise behind the defensive specification —
that the CWD may be the skill directory, beneath the installed pack — is **false
on both adapters measured**. The CWD is the content root. So rules 2–4 of
content-root resolution are not skipped in practice, rule 4 does the work, and
`--root` is **not** effectively required on the agent surface.

**Two findings the gate surfaced beyond its own question.**

- The bare-relative convention shipped by `converters` (`python
  scripts/render_mermaid.py`, `node scripts/render.js`) is **broken on the
  claude-code agent surface**. `workspace-status` gets it right with an explicit
  `'<skill-dir>/scripts/…'` plus `--root .` — which is also independent evidence
  that CWD is expected to be the content root.
- **Exit-code collision.** `python: can't open file` exits **2**, and
  `mermaid-renderer`'s SKILL.md reads exit 2 as "`mmdc` is not installed → tell
  the user to `npm install`". A wrong script path therefore masquerades as a
  missing dependency. `binder.py` uses exit **2** for *renderer not installed*
  and has the same collision available to it.


---

## Route D — the adopted mechanism (added after the adversarial pass)

Routes A–C above were the first three measured. **The one D46 actually adopts is a
fourth**, arrived at because the adversarial review rejected Route C on grounds the
browser runs could not see: a build-time wrapper inserts lines per diagram, and the
scalar `line-offset` is what lets this adapter have no `line-map` at all.

**Mechanism.** The compiler annotates the fence's *opening delimiter* —
` ```{.mermaid data-a11y-name="Diagram 3.1"} ` — a same-line rewrite, so no line is
added and the fence **body** is untouched. The pack's theme then prepends
`accTitle:` / `accDescr:` lines into the fence's Mermaid source before the bundle
mounts it, so **Mermaid generates the `<title>`/`<desc>` itself, inside the SVG**.

**Measured, egress blocked, `notes/harness/z6_a11y_probe.py` against the
`notes/harness/main.html.a11y-shim` theme:**

```
role='graphics-document'  name='Diagram 3.1 — ledger write path (RFC-0091)'
                          desc='Client calls the API gateway, which writes through the ledger service to Postgres.'
<title id="chart-title-__mermaid_0">Diagram 3.1 — ledger write path (RFC-0091)
<desc  id="chart-desc-__mermaid_0">Client calls the API gateway, …
div heights: [423]      remote requests: []      page errors: []
```

**Ordering, re-measured to isolate the observer (Z6i).** The first run registered a
`MutationObserver` *and* a `DOMContentLoaded` sweep, so a pass could not be
attributed to either. Re-run with the sweep **removed** and with a **sixty-edge
fence** alongside a two-line one, so the result is not an artifact of a diagram small
enough to arrive in one parse chunk:

```
role='graphics-document'  name='Diagram 3.1 long fence'
                          desc='A sixty-edge chain, long enough to span a parse chunk.'
role='graphics-document'  name='Diagram 3.2 short fence'
div heights: [6313, 73]   remote requests: []      page errors: []
```

**Z6h / Z6i — the injection channel, and what the control actually is (measured,
and the first answer was wrong).**

An unescaped `attr_list` value is an HTML-injection channel. With a raw label of
`Diagram & "3.1" <script>x</script> %%{init:{"theme":"dark"}}%%`:

```
emitted: <pre class="mermaid" data-a11y-name="Diagram &amp; " 3.1"="3.1"" <script>
grep -c "<script>x</script>" index.html  ->  1        # live script in the page
```

**The first conclusion drawn from this was that escaping double-encodes and an ASCII
allowlist was therefore required. That was wrong, and re-measuring showed it.** With a
single HTML-escape, the value round-trips *exactly* — see
`run-outputs-d46-2026-08-07.md`:

```
esc  : Ledger &amp; payments &quot;3.1&quot; — l&#x27;architecture réseau
AX   : "Ledger & payments \"3.1\" — l'architecture réseau"
```

So escaping is necessary **and sufficient** for the HTML hop, and an allowlist would
have mangled `Réseau : l'architecture 漢字` for nothing.

**What escaping does not cover is the value's real sink: Mermaid source.** The theme
lifts it into an `accTitle:` line, so Mermaid evaluates it. Measured with escaping
applied throughout:

```
'Diagram 3.1 — Réseau : l'architecture 漢字'      ->  round-trips exactly
'Diagram 3.2 with <b>angle</b> brackets'          ->  survives intact (no truncation)
'Diagram 3.3 %%{init:{"theme":"dark"}}%% payload' ->  'Diagram 3.3 payload'   # directive CONSUMED
'Diagram 3.4 first\nflowchart LR…'                ->  no graphics-document    # diagram DESTROYED
```

The directive case is the serious one: `%%{init:}%%` is the construct the adapter's
rule table rejects in *authored* fence bodies, arriving through a channel the scanner
never inspects. So the control is **HTML-escape, plus reject on `%%{` or a newline** —
rejected rather than stripped, because in a compiler-owned string either is a bug.

**Z6l / Z6m — what this rests on.** The bundle requests the floating `mermaid@11`
tag (11.16.1 here), and the mechanism depends on two upstream behaviours that are not
stability promises: Mermaid's `accTitle`/`accDescr` grammar, and the bundle mounting
after parse. Either changing breaks the *name* while the diagram keeps rendering —
the Z6e shape — which is why Z6 carries regression duty.
