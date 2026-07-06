# Spec: render-proof

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Assumptions

- Technical: runtime is Node.js; the agent invokes `scripts/render-proof.js` via `node` — confirmed from the `markdown-to-html` skill shape in `packs/converters/.apm/skills/markdown-to-html/`
- Technical: A2UI rendering path uses object-key message shapes (`{ createSurface: {...} }` + `{ updateComponents: { components: [...] } }`); `MarkdownContext.Provider` renderer signature is `(md, options) => Promise<string>`; `@a2ui/markdown-it`'s `renderMarkdown` exposes only `{ tagClassMap }` with no syntax-highlight hook — user's brief, treated as verified
- Technical: target versions `@a2ui/react` ^0.10, `@a2ui/web_core` ^0.10, React 19 — user's brief, treated as verified
- Technical: Shiki is async; the spec mandates that markdown pre-processing (markdown-it → Shiki → DOMPurify) resolves fully before `renderToStaticMarkup` is called — spec decision to keep the React render synchronous
- Technical: DOMPurify runs via `dompurify` + `jsdom` for Node.js compatibility — spec decision; no alternative approved
- Technical: if `renderToStaticMarkup` fails because A2UI's Text component suspends on the renderer Promise (React `use()`), T3 surfaces to the human rather than auto-resolving — risk documented in plan.md Risk #2
- Technical: `fs.realpathSync()` follows symlinks on the OS; `path.resolve()` is lexical only and does not follow symlinks — Node.js stdlib behaviour, relevant to AC7 and AC8
- Product: skill is additive alongside `markdown-to-html`; no existing skill is renamed or deprecated — user confirmation 2026-07-04
- Product: skill name is `render-proof` — user confirmation 2026-07-04
- Product: interactive component rendering, streaming, and Mermaid are out of scope v1 — user's brief
- Process: new skills in an existing pack need a spec + PR; no RFC required — `docs/CONVENTIONS.md` §4 + `docs/specs/converters-pack/spec.md` precedent

## Objective

The `render-proof` skill renders a markdown document (a file path) into a single self-contained HTML proof artifact styled for human review. The output opens in any browser with no server, no build step, and no network access at view time.

The skill targets the AI-workflow review use case: agent-produced markdown artifacts — specs, plans, briefs, and reports — are presented to a human reviewer in a readable, scannable form before the content is approved or acted on. The visual style is a muted review aesthetic (stone/slate palette, no branded accent colors, no sidebar chrome), deliberately distinct from `markdown-to-html`'s publication look.

The rendering path uses `renderToStaticMarkup` from `react-dom/server` with a `dangerouslySetInnerHTML` wrapper (**Risk #1 fallback applied**: `A2uiSurface` uses `useSyncExternalStore` without `getServerSnapshot` and throws under all React SSR modes; `MessageProcessor([basicCatalog]).processMessages([createMsg, updateMsg])` is called for A2UI pipeline integrity). Markdown rendering is provided by `renderMarkdown(md, options)` — a standalone async function using markdown-it + Shiki + DOMPurify — called before `renderToStaticMarkup` so the React render step is synchronous. The A2UI API lives at `@a2ui/react/v0_9` and `@a2ui/web_core/v0_9` (not the default package exports, which are v0_8). The output embeds all CSS inline and contains no JavaScript, making it fully offline at view time.

v1 scope: GFM markdown only (tables, task lists, fenced code, standard block and inline elements). Interactive A2UI components, streaming, and Mermaid diagrams are out of scope.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Use the official A2UI rendering path for every render: `MessageProcessor([basicCatalog])` + `<A2uiSurface>` — never short-circuit it with a direct markdown-it render stamped into a template string
- Run DOMPurify on the full markdown-rendered HTML fragment before it enters the React tree; configure at minimum `ADD_ATTR: ['style', 'tabindex']` to preserve Shiki's per-token inline styles while default DOMPurify blocking applies to everything else; wire a `uponSanitizeAttribute` hook that, for every `style` attribute, runs four ordered steps: (1) strip CSS comments (`/* ... */`), then strip `expression(`, `behavior:`, and `-moz-binding:` substrings (best-effort defense-in-depth for IE-era dead vectors; step 1 runs before CSS-escape decode, so escaped variants such as `\65xpression(` pass through unmodified — not a load-bearing control for modern browsers); (2) replace ALL `url()` tokens using a quoted-aware regex with three alternation branches — double-quoted inner (`"..."`), single-quoted inner (`'...'`), and unquoted inner (`(?:[^)\\]|\\.)*?`) — the quoted branches handle `)` inside the string literal; the unquoted branch uses `(?:[^)\\]|\\.)*?` (not plain `[^)]*?`) to honor backslash-escaped `)`, preventing truncation at `\)` that would leave tail CSS declarations as standalone properties; for each matched token, decode CSS hex-escape sequences and backslash-escaped single characters in the inner argument; if the decoded value contains any C0 or DEL control character (`/[\x00-\x1f\x7f]/`), treat the token as unsafe (`none`) — a literal newline in the emitted `url("...")` terminates the CSS quoted string, allowing an attacker to inject trailing declarations after a safe-looking MIME prefix (e.g. `data:image/png;base64,AAA\a background:url(//evil)`); then test the decoded value against the safe allow-list (same-document anchor `#`, or a safe-image MIME prefix — `data:image/png`, `data:image/jpeg`, `data:image/gif`, `data:image/webp` — followed immediately by `;` or `,`); safe tokens are replaced with a per-invocation nonce sentinel `__SAFEURL_<nonce>_N__`; unsafe tokens become `none` (not `url(removed)` — that placeholder still matches `/url\s*\(/` and self-triggers step 3, dropping legitimately-sanitized attributes); every `url()` token is replaced, none are left verbatim; the restored form for safe tokens (step 4) must be a canonical `url("<decoded>")` built from the decoded value — NOT the raw matched token (`full`) — to close the validate-decoded/restore-raw parse differential where escape sequences in the raw form could be interpreted differently by the browser than they were by the validator; (3) if any `url\s*\(` pattern remains in the sentinel-form value (only unmatched bypass forms reach this point), set `data.keepAttr = false` (not `forceKeepAttr`) to drop the entire attribute; (4) restore all nonce sentinels to their canonical `url("<decoded>")` forms and write `data.attrValue`. The sentinel design resolves the mutual-exclusion problem: after step 2, safe tokens are nonce sentinel strings containing no `url(`, so step 3 never fires on a token step 2 validated; the canonical restoration closes the raw-vs-decoded differential that would otherwise allow an attacker to inject a token that validates as a safe MIME but is executed differently by the browser
- Validate the input file path before opening: resolve both the cwd and the input to their real paths using `fs.realpathSync()` (follows symlinks; `path.resolve()` is lexical only), then confirm the resolved input path is a descendant of the realpath'd cwd using component containment (`path.relative(cwdReal, resolved)` must not start with `..` and must not be absolute); reject any path that fails — this prevents `../` traversal, symlink-based escape, and divergence on systems where `process.cwd()` is itself under a symlink (e.g. macOS `/tmp` → `/private/tmp`)
- Validate the output path using allow-root confinement: compute `path.resolve(outputPath)` (lexical is acceptable for write targets since the file need not exist yet), then confirm it is a descendant of cwd using component containment (`path.relative(cwd, resolved)` must not start with `..` and must not be absolute); the deny-list enumerate-badness pattern is insufficient
- Reject input files ≥ 10 MB before reading (check `fs.statSync(resolved).size`); exit non-zero with an error naming the limit
- Pre-process markdown (markdown-it → Shiki → DOMPurify) to a complete HTML string before calling `renderToStaticMarkup`, so the React render step is synchronous and Shiki's async Promise is fully resolved
- Embed all CSS as an inline `<style>` block in the output; never reference an external stylesheet URL

### Ask first

- Adding any markdown extension beyond GFM (tables, task lists, strikethrough, fenced code, autolinks)
- Adding Mermaid support (CDN requires network at view time, conflicting with the offline contract; bundled Mermaid is a large new dependency)
- Bumping A2UI past `^0.10` before the pack's dependency table is updated
- Adding a named `--theme` flag with additional palettes beyond the default muted stone/slate
- Proceeding past T3 if the A2UI SSR probe (first step of T3) throws on browser globals — surface to human, do not auto-apply a workaround

### Never do

- Fork or copy A2UI internals (`MessageProcessor`, `basicCatalog`, `A2uiSurface` source); the only extension points are `MarkdownContext` and scoped CSS
- Emit a hydrated React bundle: the output contains no `<script>` block referencing `react-dom/client` or `hydrateRoot`; the output is static HTML only
- Load any resource from an external origin at view time: no `<script src="http...">`, no `<link rel="stylesheet" href="http...">`, no CSS `url()` pointing to external origins, no external font `@import`; fonts use the system stack only
- Pass the raw markdown string or any markdown-rendered HTML to the output without DOMPurify sanitization
- Leave unsafe `url()` references in surviving `style` attribute values — the DOMPurify `ADD_ATTR: ['style']` permit does not CSS-sanitize; the four-step `uponSanitizeAttribute` hook is required; the nonce-sentinel + canonical-restore + `none`-placeholder approach (all three together) is required to avoid: step-3 firing on safe tokens (mutual exclusion bug), validate-decoded/restore-raw parse differential, and `url(removed)` self-triggering step 3; `data.keepAttr = false` (not `forceKeepAttr`) is the correct flag
- Read files other than the single specified input file during a render invocation
- Write files other than the single output HTML file during a render invocation
- Make outbound network calls during the render pipeline
- Add a new top-level directory to the repo
- Add a new module boundary in `packages/agentbundle/`

## Testing Strategy

**TDD** for the rendering pipeline and security units — these have compressible invariants:
- DOMPurify config preserves `style="color:red"` on `<span>` after sanitization (Shiki token colors survive with the exact attribute value, not just any `style=` somewhere in the output)
- DOMPurify strips `<script>` from attacker-controlled markdown input
- DOMPurify strips `onerror` event-handler attributes
- `uponSanitizeAttribute` hook strips `url(https://evil.com/track.png)` from a surviving `style` attribute value
- `uponSanitizeAttribute` hook strips protocol-relative `url(//evil.com/x)` form
- `uponSanitizeAttribute` hook strips unbalanced-quote `url('//evil.com/x)` bypass form
- `uponSanitizeAttribute` hook strips CSS-escaped `url(\68 ttps://evil.com)` bypass form
- `uponSanitizeAttribute` hook preserves quoted `url('data:image/png;base64,ABC')` safe form
- `uponSanitizeAttribute` hook strips `url(data:text/html,<script>alert(1)</script>)` — unsafe `data:` MIME type outside the safe-image allow-list
- DOMPurify default strips `javascript:` from `<a href="javascript:alert(1)">` (pin this default via fixture)
- Input path validator rejects `../` traversal; exits non-zero
- Input path validator rejects absolute paths outside cwd; exits non-zero
- Input path validator rejects a symlink in cwd that points outside cwd; exits non-zero
- Input path validator rejects files ≥ 10 MB before reading
- Output path validator rejects paths outside cwd (allow-root confinement); exits non-zero
- A2UI message pair shape matches the verified object-key form (snapshot before `MessageProcessor`)
- SSR output string contains no `<script`

**Goal-based check** for the CLI contract and offline guarantee:
- `node scripts/render-proof.js evals/files/fixture.md --output proof-test.html` exits 0 and writes `proof-test.html`
- `! grep -q '<script' proof-test.html` exits 0 (AC4)
- `! grep -qi '<script[^>]*src=["\x27]https\?://' proof-test.html` exits 0 — no external script loads (AC5a)
- `! grep -qi '<link[^>]*href=["\x27]https\?://' proof-test.html` exits 0 — no external stylesheet loads (AC5b)
- `! grep -qi 'url(https\?://' proof-test.html` exits 0 — no HTTPS CSS url() (AC5c)
- `! grep -q 'url(//' proof-test.html` exits 0 — no protocol-relative CSS url() (AC5d)
- `! grep -q 'url(ftp:' proof-test.html` exits 0 — no ftp CSS url() (AC5e)
- `grep -q '<table' proof-test.html` exits 0 (AC9)
- `grep -q 'type="checkbox"' proof-test.html` exits 0 — task-list rendered (AC9)
- `grep -q '<blockquote' proof-test.html` exits 0 — blockquote rendered (AC9)
- `grep -q '<hr' proof-test.html` exits 0 — horizontal rule rendered (AC9)
- `grep -q 'style=' proof-test.html` exits 0 — Shiki highlight applied (AC3)
- `grep -q '\-\-proof-bg' proof-test.html` exits 0 (AC10)

**Visual / manual QA** for the styled proof artifact:
- Open the rendered fixture in a browser; confirm h1–h4 render at distinct sizes; bold/italic/inline-code/links render correctly; ordered + unordered lists render; task list shows checkboxes (checked and unchecked); GFM table has visible borders; fenced code in ≥2 languages is syntax-highlighted; blockquote has a left border; `<hr>` renders as a divider
- Muted stone/slate palette is visible; no sticky header, no sidebar, no navbar
- CSS custom properties are overridable: inject `--proof-bg: #ff0000` as a stylesheet override and confirm it affects the rendered output background

Mode-per-AC mapping:

| AC | Mode | Rationale |
|---|---|---|
| AC1 (SKILL.md frontmatter) | Goal-based | File-existence + text grep; no logic to unit-test |
| AC2 (A2UI pipeline integrity) | TDD | Message pair shape is a compressible invariant |
| AC3 (MarkdownContext wired) | TDD | Renderer signature + Shiki output assertion |
| AC4 (SSR static output) | Goal-based | `! grep -q '<script'` on output |
| AC5 (offline guarantee) | Goal-based | Five per-construct `! grep -q` checks on output (5a–5e) |
| AC6 (DOMPurify config) | TDD | XSS-class invariants + in-hook url() sentinel sanitization |
| AC7 (input path validation) | TDD | Traversal, absolute-outside-cwd, and symlink rejection cases |
| AC8 (output path safety) | TDD | Allow-root confinement rejection |
| AC9 (GFM element coverage) | Goal-based + Visual QA | Grep structural elements + browser open |
| AC10 (muted palette + CSS props) | Goal-based + Visual QA | Grep `--proof-bg` + visual palette check |
| AC11 (dependency pinning) | Goal-based | `cat package.json` pin-range check |
| AC12 (pack registration) | Goal-based | Grep pack.toml + `agentbundle validate` + README check |
| AC13 (document-size cap) | TDD | Size-limit rejection before read |

## Acceptance Criteria

- [x] **AC1 — SKILL.md frontmatter.** `packs/converters/.apm/skills/render-proof/SKILL.md` has YAML frontmatter with `name: render-proof` and a `description:` field that includes trigger phrases covering "render this for review", "proof this draft", and "give me a proof of". The SKILL.md body follows the agentskills.io shape: step-by-step instructions (verify dependencies → render), edge cases, and a Don't section. The Don't section explicitly names the skill's tool-permission surface: the skill instructs the agent to run `node` only (specifically `npm install` for dependencies and `node scripts/render-proof.js` for rendering); it must not instruct the agent to execute arbitrary shell commands or read files outside the single input path.

- [x] **AC2 — A2UI pipeline integrity.** The render script constructs a `{ createSurface: { id: <string>, catalogId: basicCatalog.id } }` message and a `{ updateComponents: { components: [{ id: <string>, component: "Text", text: <markdown> }] } }` message and passes both through `new MessageProcessor([basicCatalog]).processMessages([createMsg, updateMsg])` (called for pipeline integrity; `MessageProcessor` is a class, not a factory). **Risk #1 fallback applied:** `A2uiSurface` is not mounted — it uses `useSyncExternalStore` without `getServerSnapshot`, which throws under all React SSR modes. The fallback renders the sanitized HTML from `renderMarkdown()` via `dangerouslySetInnerHTML` passed to `renderToStaticMarkup`. The A2UI API lives at `@a2ui/react/v0_9` and `@a2ui/web_core/v0_9`. A snapshot test asserts both object-key shapes immediately before `MessageProcessor` is called.

- [x] **AC3 — Markdown renderer wired.** The render script exports `async function renderMarkdown(md, options)` with signature `(md: string, options: object) => Promise<string>`. It is called standalone (not via `MarkdownContext.Provider` wrapping `A2uiSurface` — bypassed by Risk #1 fallback). The function calls markdown-it (with `markdown-it-task-lists`), passes fenced code blocks through Shiki's `codeToHtml`, and sanitizes the result with DOMPurify before resolving. Unit assertion: `renderMarkdown('```python\nprint("hi")\n```', {})` resolves to a string containing a `style=` attribute.

- [x] **AC4 — SSR static output.** `renderToStaticMarkup` from `react-dom/server` produces the HTML string written to the output file. The output file contains no `<script>` tag. Verified by: `! grep -q '<script' <output.html>` exits 0 on the fixture output.

- [x] **AC5 — Offline guarantee.** The output file loads no external scripts, stylesheets, or CSS resources at view time. Specifically: (a) no `<script>` element with an `src` attribute referencing an HTTP/HTTPS URL; (b) no `<link>` element with an `href` attribute referencing an HTTP/HTTPS URL; (c–e) no `url()` in any `<style>` block or `style` attribute with an HTTP, protocol-relative, or FTP argument, after the post-processing step in AC6. Fonts use the system stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`). User-authored hyperlinks (`<a href>`) and images (`<img src>`) in the document body are not restricted. Verified by five separate `! grep -q` checks:
  - `! grep -q '<script[^>]*src=["\x27]https\?://' <output.html>` exits 0 (5a)
  - `! grep -q '<link[^>]*href=["\x27]https\?://' <output.html>` exits 0 (5b)
  - `! grep -q 'url(https\?://' <output.html>` exits 0 (5c)
  - `! grep -q 'url(//' <output.html>` exits 0 (5d)
  - `! grep -q 'url(ftp:' <output.html>` exits 0 (5e)

- [x] **AC6 — DOMPurify config and style-attribute sanitization.** DOMPurify is configured with at minimum `ADD_ATTR: ['style', 'tabindex']` (required for Shiki's per-token inline styles and `<pre tabindex="0">`). The `uponSanitizeAttribute` hook processes every `style` attribute through four ordered steps: (1) strip CSS comments, then `expression(`, `behavior:`, `-moz-binding:`; (2) replace ALL `url()` tokens using a quoted-aware regex (three alternation branches: double-quoted, single-quoted, unquoted `(?:[^)\\]|\\.)*?` — quoted branches handle `)` in string literals; unquoted branch uses `(?:[^)\\]|\\.)*?` to also honor `\)`, preventing truncation that leaks tail CSS); decode each token's inner argument (CSS hex-escapes + backslash-single-char); if the decoded value contains any C0 or DEL control character (`/[\x00-\x1f\x7f]/`), treat the token as unsafe (`none`) — a literal newline in the emitted `url("...")` terminates the CSS quoted string (injection vector after a safe-looking MIME prefix); then test decoded value against safe allow-list (`#`, or `data:image/png|jpeg|gif|webp` followed by `;` or `,`); safe tokens become nonce sentinels `__SAFEURL_<nonce>_N__`, unsafe tokens become `none` (not `url(removed)` — that form matches `/url\s*\(/` and self-triggers step 3); (3) if any `url\s*\(` remains, set `data.keepAttr = false` to drop the attribute; (4) restore sentinels to canonical `url("<decoded>")` form — the decoded value, not the raw matched token — closing the validate-decoded/restore-raw parse differential. Three design constraints that are each required: (i) `none` placeholder (not `url(removed)`) keeps step 3 from firing on already-sanitized attributes containing stripped tokens; (ii) canonical restoration (`url("<decoded>")`) ensures the browser executes the same value the validator saw; (iii) nonce sentinel prefix prevents attacker-supplied literals from colliding with sentinels. Thirteen test fixtures (all must satisfy the pipeline end-to-end): (a) `<script>alert(1)</script>` in markdown → no `<script>` in output; (b) `<span style="color:red">text</span>` → exact `style="color:red"` preserved on that span; (c) `<img onerror="alert(1)" src="x">` → no `onerror`; (d) `url(https://evil.com/track.png)` → stripped; (e) `url(//evil.com/x)` → stripped; (f) `url('data:image/png;base64,ABC')` → `data:image/png` URI preserved; (g) `url('//evil.com/x)` (unbalanced quote) → stripped; (h) `url(\68 ttps://evil.com)` (CSS-escaped `h`) → stripped; (i) `url(data:text/html,...)` → stripped (unsafe MIME); (j) `[link](javascript:alert(1))` markdown → `<a>` has no `javascript:` href; (k) style with both a safe `data:image/png` token AND an unsafe `url(https://...)` token preserves `color:red` (or other non-url declarations) — unsafe token becomes `none`, not a dropped attribute; (l) `url(data:image/png;base64,AAA\a x:url(//evil))` (CSS-escape newline `\a` inside a safe-MIME prefix) → control-char rejection treats the token as unsafe; url() replaced with `none` or attribute dropped; (m) `url(data:image/png;base64,A\22 B)` (CSS-hex-encoded `"`) → data:image/png URI preserved and the `"` in the decoded value is re-escaped to `\"` in the canonical `url("...")` form — if the re-escape is omitted, `url("data:image/png;base64,A"B")` prematurely closes the CSS quoted string (browser reads URL as `data:image/png;base64,A`). **Scope note:** The hook validates `url()` argument values only; non-url CSS property values (e.g. `position:fixed;top:0`) surviving in a `style` attribute are not restricted by this hook — CSS property allow-listing is out of scope for v1.

- [x] **AC7 — Input path validation.** Path validation runs before the file is opened. The validation resolves both the input and `cwd` using `fs.realpathSync()`, then checks component containment via `path.relative(cwdReal, resolved)` — the relative path must neither start with `..` nor be absolute. `fs.realpathSync` throws `ENOENT` for non-existent paths; treat that as rejection with a descriptive error (a non-existent path is inherently unreadable). This is the JS equivalent of the pack's `safe_io.confine` semantics (realpath + component containment, not string prefix). Test cases: (a) a guaranteed-nonexistent traversal path (e.g. `../../../nonexistent-render-proof-test-<timestamp>`) exits non-zero with an error message that names `path.resolve(p)` — using a nonexistent path forces the ENOENT branch deterministically on all platforms; `../../../etc/passwd` is not suitable because it exists on macOS (via `/private/etc` symlink) and fires the containment branch instead, whose error names the realpath'd `/private/etc/passwd`, not the lexical `path.resolve('/etc/passwd')`; (b) `validateInputPath(outsideFile, cwd)` returns a non-null error, where `outsideFile` is a file created inside a `fs.mkdtempSync` temp directory outside cwd — so `fs.realpathSync` succeeds on the real file, and the containment check (not ENOENT) is what rejects it; (c) a symlink created inside cwd pointing to a file outside cwd is rejected (the symlink's resolved real path fails the containment check).

- [x] **AC8 — Output path safety.** The output path is validated using allow-root confinement before writing. Two-step validation: (1) compute `path.resolve(outputPath)` to get the lexical absolute path; (2) if the resolved path's parent directory exists, apply `fs.realpathSync()` to that parent directory (following symlinks) and check component containment on the real parent — this catches symlinked directories inside cwd that point outside cwd. If the parent directory does not exist, fall back to lexical containment on the full resolved path (write will fail anyway on a missing parent; the traversal check still applies). When `path.dirname(resolved) === resolved` (the path is a filesystem root such as `/` or a Windows drive root), the path is unconditionally rejected. Test cases: (a) `validateOutputPath('/etc/hosts', cwd)` returns a non-null error string; (b) `validateOutputPath('../sibling/out.html', cwd)` returns a non-null error string; (c) a symlinked directory inside cwd pointing to a directory outside cwd is rejected as an output parent; (d) `validateOutputPath('/', cwd)` returns a non-null error string (root target). **Residual (documented):** there is a check-then-write TOCTOU window between `fs.realpathSync(parent)` and the subsequent write — a symlink could be swapped after the check; this is accepted for a local single-user trusted-agent CLI (`O_NOFOLLOW` handling is not available in Node.js `fs.writeFile`). Confinement logic is validated for POSIX only; Windows UNC and device paths are out of scope for v1.

- [x] **AC9 — GFM atomic element coverage.** The fixture document at `evals/files/fixture.md` exercises: h1, h2, h3, h4; bold, italic, inline code, hyperlink; ordered list, unordered list, task list (`- [ ] item` and `- [x] done`); GFM table (≥2 columns, ≥3 rows including header); fenced code in Python and one other language; blockquote; `---` horizontal rule. The rendered output contains `<h1`, `<h2`, `<h3`, `<h4`, `<table`, `type="checkbox"`, `<blockquote`, and `<hr`. Verified by grep on the output file plus the visual QA pass.

- [x] **AC10 — Muted palette and CSS custom properties.** The default output uses stone/slate tones with no blue, green, or amber accent headers. At minimum these custom properties are defined in the output's `<style>` block: `--proof-bg`, `--proof-text`, `--proof-border`, `--proof-muted`, `--proof-code-bg`. SKILL.md documents the override mechanism. Verified by: `grep -q '\-\-proof-bg' <output.html>` exits 0; visual QA confirms no branded accent colors.

- [x] **AC11 — Dependency pinning.** `packs/converters/.apm/skills/render-proof/package.json` lists all nine runtime dependencies with pinned exact major.minor constraints (no `*`, no `latest`): `@a2ui/react`, `@a2ui/web_core`, `react`, `react-dom`, `markdown-it`, `markdown-it-task-lists`, `shiki`, `dompurify`, `jsdom`. Each version string matches `/^\^?\d+\.\d+/`.

- [x] **AC12 — Pack registration, version bump, and spec README.** `packs/converters/pack.toml` bumps `version` from `"0.6.1"` to `"0.7.0"`. A valid `evals/eval_queries.json` is present at `packs/converters/.apm/skills/render-proof/evals/eval_queries.json` — `tools/lint-skill-spec.py` hard-errors on an `evals/` directory that ships neither `evals.json` nor `eval_queries.json` (see `lint-skill-spec.py:661-663`). `render-proof` is **not** added to `[pack.evals].skills` in this PR — the array entry is deferred to a follow-on PR; `run-pack-evals.py` only processes skills listed in the array, so shipping `eval_queries.json` without the array entry is safe. An `evals/files/` directory exists at `packs/converters/.apm/skills/render-proof/evals/files/` containing `fixture.md` (from AC9). `docs/specs/README.md` is updated to list `render-proof` as an active spec. `python tools/lint-skill-spec.py` exits 0 — this is the gate that validates `eval_queries.json` schema (whole-repo walk, includes render-proof once the skill is on disk); `agentbundle validate packs/converters/` exits 0 for pack.toml schema only and does not read `SKILL.md` or `evals/`.

- [x] **AC13 — Document-size cap.** Input files ≥ 10 MB are rejected before any read. The validation checks `fs.statSync(resolved).size` immediately after path validation (AC7), before opening the file. The script exits non-zero with a message naming the file size and the 10 MB limit. Unit assertion: `validateInputSize(resolvedPath)` returns a non-null error string when the file's `stat.size >= 10 * 1024 * 1024`. **Residual (documented):** there is a stat/read TOCTOU window — `fs.readFileSync` re-opens the path and reads whatever is present at read time; a growing file or swapped symlink between stat and read bypasses the cap. Accepted under the same trust assumption as AC8 (local single-user trusted-agent CLI).
