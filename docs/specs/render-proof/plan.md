# Plan: render-proof

- **Spec:** [`spec.md`](spec.md)
- **Status:** Shipped

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

A single PR adds the `render-proof` skill directory to `packs/converters/.apm/skills/`, wires it into `pack.toml`, and bumps the pack to 0.7.0. The work is net-new: no existing file is modified beyond `pack.toml` and `docs/specs/README.md`.

The riskiest part is the A2UI SSR boundary: `@a2ui/react` ^0.10 must be importable and renderable in a Node.js process via `renderToStaticMarkup` without browser-global crashes. T3 begins with a required probe; if it throws, the task surfaces to the human before any further A2UI integration proceeds.

Work order: scaffold the directory structure (T1) → implement the markdown renderer in complete isolation, testable without A2UI (T2) → wire the A2UI pipeline and SSR emit (T3) → add the proof stylesheet and HTML wrapper (T4) → implement input/output security in parallel with T2–T4 (T5) → register with the pack and write the evals fixture (T6, last, requires T4 and T5).

## Constraints

- A2UI extension points are `MarkdownContext` and scoped CSS only — no forking of internals (spec § Never do)
- Output is `renderToStaticMarkup`-produced static HTML with no `<script>` tags (spec AC4)
- DOMPurify sanitizes all markdown-rendered HTML; `style` and `tabindex` are explicitly added via `ADD_ATTR` for Shiki (spec AC6); `ADD_ATTR` augments DOMPurify's defaults — `ALLOWED_ATTR` would replace them entirely and break the sanitizer
- Input path validation uses `fs.realpathSync()` on **both** the input and `cwd` + component containment via `path.relative(cwdReal, resolved)` before any file read (spec AC7); `path.resolve()` is lexical only; un-realpath'd `cwd` diverges from realpath'd targets on macOS `/tmp` → `/private/tmp` (fail-closed availability bug)
- Output path safety uses allow-root confinement: lexical `path.resolve()` for the target, `fs.realpathSync` on the existing parent directory, realpath'd cwd (`fs.realpathSync(cwd)`) for both sides of containment, component containment (spec AC8); deny-list and un-realpath'd cwd are both insufficient
- Input files ≥ 10 MB are rejected before reading (spec AC13)
- Nine npm runtime packages, all pinned with `^MAJOR.MINOR`; pack version bumps to 0.7.0; `render-proof` is **not** added to `[pack.evals].skills` in this PR (deferred to a follow-on PR that ships `eval_queries.json`) (spec AC12)

## Construction tests

**Cross-cutting integration (run after T5 is merged, before T6 begins):**

```bash
cd packs/converters/.apm/skills/render-proof
node scripts/render-proof.js evals/files/fixture.md --output proof-test.html
! grep -q '<script'                              proof-test.html  # no JS (AC4)
! grep -qi '<script[^>]*src=["\x27]https\?://' proof-test.html  # no external script loads (AC5a)
! grep -qi '<link[^>]*href=["\x27]https\?://'  proof-test.html  # no external stylesheet loads (AC5b)
! grep -qi 'url(https\?://'                     proof-test.html  # no HTTPS CSS url() (AC5c)
! grep -q 'url(//'                              proof-test.html  # no protocol-relative CSS url() (AC5d)
! grep -q 'url(ftp:'                            proof-test.html  # no ftp CSS url() (AC5e)
grep -q '<table'                                proof-test.html  # GFM table present (AC9)
grep -q 'type="checkbox"'                       proof-test.html  # task-list rendered (AC9)
grep -q '<blockquote'                           proof-test.html  # blockquote rendered (AC9)
grep -q '<hr'                                   proof-test.html  # horizontal rule rendered (AC9)
grep -q 'style='                               proof-test.html  # Shiki highlight applied (AC3)
grep -q '\-\-proof-bg'                         proof-test.html  # CSS custom props (AC10)
```

All twelve assertions exit 0 together (the render invocation above is setup, not a counted assertion). This is the gate before T6.

**Manual QA (after T6):** Open `proof-test.html` in a browser and confirm the visual checklist from the spec's Testing Strategy (palette, layout, all GFM atomic elements, syntax-highlighted code). This file is within cwd so `validateOutputPath` accepts it; the render command is `node scripts/render-proof.js evals/files/fixture.md --output proof-test.html`.

## Design (LLD)

### Dependencies & integration

Nine npm runtime packages, all pinned with `^MAJOR.MINOR`:

| Package | Version | Role |
|---|---|---|
| `@a2ui/react` | ^0.10 | `A2uiSurface`, `MarkdownContext` |
| `@a2ui/web_core` | ^0.10 | `MessageProcessor`, `basicCatalog` |
| `react` | ^19.0 | React runtime (peer of @a2ui/react) |
| `react-dom` | ^19.0 | `renderToStaticMarkup` from `react-dom/server` |
| `markdown-it` | ^14.0 | GFM parsing; custom `fence` rule for Shiki |
| `markdown-it-task-lists` | ^2.0 | Task-list (`- [ ]` / `- [x]`) rendering — markdown-it core emits literal `[ ]` text without this plugin |
| `shiki` | ^1.0 | Async per-token syntax highlighting |
| `dompurify` | ^3.0 | HTML sanitization (XSS defense) |
| `jsdom` | ^25.0 | DOM environment for DOMPurify in Node.js |

`@a2ui/markdown-it` is intentionally absent — its `renderMarkdown` has no syntax-highlight hook (verified constraint). The custom renderer in this skill replaces it.

The skill's `node_modules/` is gitignored (the repo-root `.gitignore` already covers `node_modules/`; verify with `git check-ignore` during T1).

### Interfaces & contracts

The agent invocation surface (CLI):

```
node scripts/render-proof.js <input.md> [--output <file.html>]
```

| Arg | Required | Behaviour |
|---|---|---|
| `<input.md>` | yes | Path-validated before open; resolved from cwd |
| `--output <file.html>` | no | Default: input filename with `.html` extension; must be within cwd |
| `--help` / `-h` | no | Prints usage; exits 0 |

stdout on success: `OUTPUT: <resolved-path>\n`
stderr on error: descriptive message naming the rejection reason
exit 0 on success; non-zero on any error

No API contract file — this is a Node.js CLI tool, not a service endpoint.

### Failure, edge cases & resilience

| Scenario | Response |
|---|---|
| A2UI import throws on browser globals | T3 probe catches it; task surfaces to human (Ask first boundary); do not auto-apply a workaround |
| `renderToStaticMarkup` suspends on renderer Promise | T3 surfaces to human; fallback is `renderToReadableStream` (React 19 async SSR) if A2UI Text uses `use(promise)` |
| Malformed markdown | markdown-it is lenient; output may look unexpected but never crashes |
| Unknown code-fence language | Shiki's `codeToHtml` is wrapped in try/catch; falls back to `<pre><code>` with HTML-escaped source |
| Input file ≥ 10 MB | Rejected before read; exits non-zero naming the size and the 10 MB limit (AC13) |
| Raw `<script>` in markdown body | DOMPurify strips it before the output is written |
| `style` attr with `url(https://...)` | Post-processor strips the url() reference after DOMPurify (AC6 + AC5c) |
| `../` traversal in input path | Rejected before file read; exits non-zero with the canonicalized path named (AC7) |
| Absolute path outside cwd | Rejected before file read; exits non-zero (AC7) |
| Symlink in cwd pointing outside | `fs.realpathSync()` follows the symlink; rejected by component containment (AC7) |
| Output path outside cwd | Rejected by allow-root confinement before write (AC8) |
| `npm install` not run | Node throws `MODULE_NOT_FOUND` for `@a2ui/react`; SKILL.md Step 1 guides the agent to run `npm install` first |

### Quality attributes (NFRs)

- **No JavaScript in output** (AC4): portability — the HTML opens in air-gapped environments, email preview panes, and PDF exporters
- **No externally-loaded resources** (AC5): view-time privacy — no CDN beaconing, no external tracking; five-check coverage (scripts, stylesheets, CSS url() HTTPS, CSS url() protocol-relative, CSS url() ftp:)
- **XSS safety** (AC6): output is safe even when the input markdown contains attacker-controlled HTML — relevant for agent-generated content from untrusted pipelines; `ADD_ATTR` (not `ALLOWED_ATTR`) augments the sanitizer's defaults rather than replacing them
- **Path confinement** (AC7, AC8): symlink-aware (`fs.realpathSync`) input confinement + allow-root output confinement limits blast radius if the skill is invoked with a manipulated argument; JS equivalent of `safe_io.confine` semantics
- **Size cap** (AC13): prevents Shiki OOM on unbounded input

## Tasks

### T1: Scaffold skill directory, SKILL.md, and package.json

**Depends on:** none

**Tests:**
- `ls packs/converters/.apm/skills/render-proof/SKILL.md` exits 0
- SKILL.md frontmatter: `name: render-proof`; description contains "render this for review", "proof this draft", "give me a proof of" (AC1)
- SKILL.md Don't section names the tool-permission surface: `node` execution only, no arbitrary shell commands (AC1)
- `package.json` lists all 9 deps with `^MAJOR.MINOR` pins; no `*`, no `latest` (AC11)
- `evals/files/fixture.md` exists with the full GFM fixture content — mechanically verified by:
  - `grep -q '| Column A |' evals/files/fixture.md` — GFM table present
  - `grep -q '- \[ \]' evals/files/fixture.md` — unchecked task list item present
  - `grep -q '- \[x\]' evals/files/fixture.md` — checked task list item present
  - `grep -q '^\`\`\`python' evals/files/fixture.md` — Python code fence present
  - `grep -q '^\`\`\`bash' evals/files/fixture.md` — second language code fence present
  - `grep -q '^> ' evals/files/fixture.md` — blockquote present
  - `grep -q '^---' evals/files/fixture.md` — horizontal rule present
  - `grep -q '^#### ' evals/files/fixture.md` — h4 present (deepest heading level)
- `ls packs/converters/.apm/skills/render-proof/evals/eval_queries.json` exits 0 — required by `tools/lint-skill-spec.py:661-663` when `evals/` is present
- `node -e "const d=JSON.parse(require('fs').readFileSync('evals/eval_queries.json','utf8'));if(!Array.isArray(d))throw new Error('not array');d.forEach((e,i)=>{if(typeof e.query!=='string'||!e.query)throw new Error('element '+i+' missing query');if(typeof e.should_trigger!=='boolean')throw new Error('element '+i+' should_trigger must be boolean');})"` exits 0 (valid JSON array; each element has non-empty-string `query` and boolean `should_trigger`, per `lint-skill-spec.py:556-567`)

**Approach:**
- Create `packs/converters/.apm/skills/render-proof/` with subdirectories `scripts/` and `evals/files/`
- Write `evals/files/fixture.md` with the **full GFM fixture** (same content as the T6 spec — h1–h4, bold/italic/inline-code, ordered+unordered+task lists, GFM table ≥3 rows, Python+bash fenced code, blockquote, `---` rule); T6 will reference this file, not overwrite it with different content
- Write `SKILL.md` with YAML frontmatter (`name: render-proof`, `description:` with trigger phrases) and body covering: Step 1 (verify npm deps: `node -e "require('@a2ui/react')"`, install if absent), Step 2 (invoke `node scripts/render-proof.js <input.md> [--output OUT.html]`), stdout surface, edge cases (unknown lang, size cap, raw HTML in input), Don't section (don't run on untrusted input without reviewing the DOMPurify note; don't pass `--output` to a path outside cwd; tool surface is `node` only — no arbitrary shell commands)
- Write `evals/eval_queries.json` — a JSON array of `{query, should_trigger}` objects with at least 3 trigger queries (e.g. "render this markdown for review", "proof this draft") and 3 non-trigger queries (e.g. "convert this Markdown to a PDF"); required by `tools/lint-skill-spec.py` when `evals/` is present; decoupled from the `[pack.evals].skills` array entry, which is deferred
- Write `package.json` with the 9 pinned runtime dependencies; no devDependencies (construction tests use Node's built-in `assert`)
- Confirm `node_modules/` is covered by the repo-root `.gitignore` (`git check-ignore evals/files/node_modules`); add a note to SKILL.md if not

**Done when:** All assertions pass on a manual check; `SKILL.md` opens correctly and reads like the existing `markdown-to-html/SKILL.md` in style and length.

---

### T2: Custom markdown renderer (markdown-it + Shiki + DOMPurify)

**Depends on:** T1

**Tests (TDD — write red stubs before any implementation):**

```javascript
// test/renderer.test.js — run with: node test/renderer.test.js
// Note: plan fixture letters (a)–(o) cover both AC6 and non-AC6 checks; AC6 fixtures start at plan (c).
// The inline AC6x tags are the binding AC reference: plan (a)=GFM bold, (b)=Shiki AC3.
const assert = require('assert');
const { renderMarkdown, sanitizeStyle } = require('../scripts/render-proof.js');

async function run() {
  // (a) GFM bold
  const bold = await renderMarkdown('**bold**', {});
  assert(bold.includes('<strong>') || bold.includes('bold'), 'bold failed');

  // (b) Shiki highlight applied (AC3)
  const code = await renderMarkdown('```python\nprint("hi")\n```', {});
  assert(code.includes('style='), 'Shiki style attr missing');

  // (c) script stripped (AC6a)
  const xss = await renderMarkdown('<script>alert(1)</script>', {});
  assert(!xss.includes('<script'), 'script not stripped');

  // (d) style attr preserved on span — assert the exact value, not just any style= (AC6b)
  const styled = await renderMarkdown('<span style="color:red">text</span>', {});
  assert(styled.includes('style="color:red"'), 'style="color:red" not preserved on span');

  // (e) onerror stripped (AC6c)
  const onerr = await renderMarkdown('<img onerror="alert(1)" src="x">', {});
  assert(!onerr.includes('onerror'), 'onerror not stripped');

  // (f) HTTPS url() stripped by post-processor — end-to-end through full pipeline (AC6d)
  const cssExfil = await renderMarkdown('<span style="background:url(https://evil.com/t.png)">x</span>', {});
  assert(!cssExfil.includes('url(https://evil.com'), 'HTTPS CSS url() exfil not stripped');

  // (g) protocol-relative url() stripped (AC6e)
  const protoRel = await renderMarkdown('<span style="background:url(//evil.com/x)">x</span>', {});
  assert(!protoRel.includes('url(//evil.com'), 'protocol-relative CSS url() not stripped');

  // (h) quoted data: URI preserved — hook must not strip quoted safe forms (AC6f)
  const dataUri = await renderMarkdown('<span style="background:url(\'data:image/png;base64,ABC\')">x</span>', {});
  assert(dataUri.includes('data:image/png'), 'quoted data: URI was incorrectly stripped');

  // (i) unbalanced-quote bypass stripped — url('//evil.com/x) without closing quote (AC6g)
  const unbalanced = await renderMarkdown('<span style="background:url(\'//evil.com/x)">x</span>', {});
  assert(!unbalanced.includes('url(\'//evil.com'), 'unbalanced-quote url() bypass not stripped');

  // (j) CSS-escape bypass stripped — url(\68 ttps://evil.com) hex-escapes first char (AC6h)
  // Assert BOTH the raw escaped form AND the decoded form — a broken impl that decodes but doesn't strip
  // would remove the raw bytes but still emit the live exfil URL
  const cssEsc = await renderMarkdown('<span style="background:url(\\68 ttps://evil.com)">x</span>', {});
  assert(!cssEsc.includes('\\68 ttps://evil.com') && !cssEsc.includes('evil.com'), 'CSS-escape url() bypass not stripped (check both raw and decoded form)');

  // (k) mixed safe+unsafe: safe data: URI preserved, adjacent color:red preserved, unsafe url() stripped (AC6k)
  // Input has THREE tokens in one attribute: non-url (color:red), safe url (data:image/png), unsafe url (https://evil)
  const mixed = await renderMarkdown('<span style="color:red;list-style:url(\'data:image/png;base64,ABC\');background:url(https://evil.com/t.png)">x</span>', {});
  assert(
    mixed.includes('color:red') && mixed.includes('data:image/png') && !mixed.includes('url(https://evil.com'),
    'fixture k: color:red or safe data: URI lost, or unsafe url() not stripped'
  );

  // (l) unsafe data: MIME type stripped — data:text/html not in safe-image allow-list (AC6i)
  const unsafeMime = await renderMarkdown('<span style="background:url(data:text/html,<script>alert(1)</script>)">x</span>', {});
  assert(!unsafeMime.includes('url(data:text/html'), 'unsafe data:text/html not stripped');

  // (m) javascript: href stripped by DOMPurify default URI scheme (AC6j)
  // Use raw HTML anchor (html: true) — markdown-it validateLink already blocks the md-link syntax,
  // outputting javascript: as literal paragraph text (not an anchor); raw HTML tests DOMPurify's
  // actual scheme sanitization path.
  const jsHref = await renderMarkdown('<a href="javascript:alert(1)">click</a>', {});
  assert(!jsHref.includes('javascript:'), 'javascript: href not stripped by DOMPurify default');

  // (n) unknown lang fallback — no throw
  const unk = await renderMarkdown('```unknownlang\ncode\n```', {});
  assert(unk.includes('<pre'), 'unknown-lang fallback missing pre');

  // (o) control-char breakout: CSS-escape \a (newline) inside safe-MIME prefix → treated as unsafe (AC6l)
  // url(data:image/png;base64,AAA\a x:url(//evil)) decodes \a to literal newline;
  // isSafeMime rejects the decoded value (contains C0 control char); token becomes none
  const ctrlChar = await renderMarkdown('<span style="background:url(data:image/png;base64,AAA\\a x:url(//evil))">x</span>', {});
  assert(!ctrlChar.includes('url(//evil'), 'fixture o: control-char breakout not stripped — external url() survived isSafeMime C0 check');

  // Direct sanitizeStyle test: re-escape invariant — CSS-hex-encoded " must produce url("...\"...") (AC6m)
  // hex \22 decodes to literal "; broken form url("A"B") prematurely closes the CSS quoted string
  // Direct sanitizeStyle — raw CSS return value makes it possible to assert the exact url("...\"...") form
  // without jsdom HTML-encoding of "; renderMarkdown would only expose the HTML-encoded &quot; form
  const reEscapeResult = sanitizeStyle('background:url(data:image/png;base64,A\\22 B)');
  assert(reEscapeResult !== null, 'canonical-restore re-escape: safe data: URI dropped (AC6m)');
  assert(reEscapeResult.includes('url("data:image/png;base64,A\\"B")'),
    'canonical-restore re-escape: " in decoded value (\\22) not re-escaped to \\" — broken url("A"B") prematurely closes the CSS quoted string (AC6m)');

  // Direct sanitizeStyle test: unclosed url( bypasses quoted-aware regex → step-3 backstop → null (keepAttr=false path) (AC6 step 3)
  assert(sanitizeStyle('background:url(unclosed') === null, 'sanitizeStyle must return null for unclosed url( — verifies keepAttr=false step-3 path');

  // Direct sanitizeStyle test: escaped ) in unquoted url() — without fix ([^)]*?) truncates at \),
  // leaving trailing CSS as a standalone declaration; with fix (((?:[^)\\]|\\.)*?)) the full arg
  // is captured. Verify: broken regex leaves "); z-index:9999" AFTER url() close; fixed regex does not.
  const escapedParenResult = sanitizeStyle('background:url(data:image/png;base64,A\\); z-index:9999)');
  assert(escapedParenResult !== null && !escapedParenResult.includes('"); z-index:9999'),
    'sanitizeStyle: escaped \\) in unquoted url() — z-index leaked as standalone declaration after url() close (unquoted branch regex not fixed)');

  console.log('All renderer tests pass');
}
run().catch(e => { console.error(e); process.exit(1); });
```

**Approach:**
- Define `decodeCSS(s)`, `isSafeMime(decoded)`, and `sanitizeStyle(attrValue)` at **module scope** above `renderMarkdown` — they must be accessible to the `uponSanitizeAttribute` hook wired inside `renderMarkdown`, and exported for direct testability. Export all three alongside `renderMarkdown` and `buildMessages` in `module.exports` at the end of the file. Nesting these inside `renderMarkdown` would make them non-exportable and break the T2 import.
- In `scripts/render-proof.js`, implement and export `async function renderMarkdown(md, options)`:
  1. Instantiate `markdown-it({ html: true, linkify: true })` and register the task-list plugin: `md.use(require('markdown-it-task-lists'))` — markdown-it ^14 core emits literal `[ ] item` text without this plugin and will fail the AC9 `type="checkbox"` gate
  2. Override the `fence` rule: wrap `shiki.codeToHtml(code, { lang, theme: 'github-dark' })` in try/catch; on unknown-language error, fall back to `` `<pre><code>` + md.utils.escapeHtml(code) + `</code></pre>` ``
  3. Render full markdown: `let html = md.render(markdownString)`
  4. Create a `jsdom` window, wire the `uponSanitizeAttribute` hook, then sanitize:
     ```js
     // NOTE: SAFE_DELIMITED, isSafeMime, decodeCSS, sanitizeStyle are defined at MODULE SCOPE
     // (not inside renderMarkdown) and exported — see the module-scope bullet above.
     // They are shown inline here as an implementation reference only.
     //
     // Require jsdom window before dompurify; dompurify ^3 CJS probes global window on some builds:
     const { JSDOM } = require('jsdom');
     const { window } = new JSDOM('');
     const createDOMPurify = require('dompurify');
     const purify = createDOMPurify(window);
     const SAFE_DELIMITED = ['data:image/png', 'data:image/jpeg', 'data:image/gif', 'data:image/webp'];
     function isSafeMime(decoded) {
       if (/[\x00-\x1f\x7f]/.test(decoded)) return false; // C0/DEL: CSS string-terminating, injection vector
       if (decoded === '#' || decoded.startsWith('#')) return true;
       return SAFE_DELIMITED.some(m =>
         decoded === m || decoded.startsWith(m + ';') || decoded.startsWith(m + ',')
       );
     }
     function decodeCSS(s) {
       return s
         .replace(/\\([0-9a-fA-F]{1,6})\s?/g, (_, h) => {
           const cp = parseInt(h, 16);
           return cp === 0 ? '�' : String.fromCodePoint(cp);
         })
         .replace(/\\(.)/g, '$1'); // backslash-escaped non-hex char (e.g. \h → h)
     }
     function sanitizeStyle(attrValue) {
       const nonce = Math.random().toString(36).slice(2);
       let val = attrValue;
       // Step 1: CSS comments; IE-era eval vectors (best-effort; runs before decode — escaped variants like \65xpression( pass through)
       val = val.replace(/\/\*[\s\S]*?\*\//g, '')
                .replace(/expression\s*\(/gi, 'removed(')
                .replace(/behavior\s*:/gi, 'removed:')
                .replace(/-moz-binding\s*:/gi, 'removed:');
       // Step 2: quoted-aware regex — three branches (double-quoted / single-quoted / unquoted)
       // Unquoted branch ((?:[^)\\]|\\.)*?) honors \) via the \\. alternative — prevents
       // truncation at a CSS-backslash-escaped ) that would leave trailing CSS as standalone declarations
       const URL_RE = /url\s*\(\s*(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)'|((?:[^)\\]|\\.)*?))\s*\)/gi;
       const restored = [];
       val = val.replace(URL_RE, (full, dq, sq, uq) => {
         const raw = dq !== undefined ? dq : (sq !== undefined ? sq : (uq || ''));
         const decoded = decodeCSS(raw.trim());
         if (isSafeMime(decoded)) {
           const idx = restored.length;
           // Canonical restoration: url("<decoded>") — NOT raw full — closes decode/restore differential
           const safe = `url("${decoded.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}")`;
           restored.push(safe);
           return `__SAFEURL_${nonce}_${idx}__`;
         }
         return 'none'; // NOT url(removed) — that form still matches /url\s*\(/ and trips step 3
       });
       // Step 3: backstop — url( remaining means an unmatched bypass form
       if (/url\s*\(/i.test(val)) return null; // signal: drop attribute
       // Step 4: restore canonical safe forms
       restored.forEach((s, i) => { val = val.replace(`__SAFEURL_${nonce}_${i}__`, s); });
       return val;
     }
     purify.addHook('uponSanitizeAttribute', (node, data) => {
       if (data.attrName !== 'style') return;
       const result = sanitizeStyle(data.attrValue);
       if (result === null) { data.keepAttr = false; return; } // keepAttr=false, NOT forceKeepAttr
       data.attrValue = result;
     });
     const clean = purify.sanitize(html, {
       ADD_ATTR: ['style', 'tabindex'],
       FORBID_TAGS: ['script', 'iframe', 'object', 'form'],
       FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus']
     });
     ```
     Key design decisions: (a) three-branch `URL_RE` uses `(?:[^)\\]|\\.)*?` for the unquoted branch — honors `\)` via the `\\.` alternative, so `url(data:image/png;base64,A\); position:fixed)` captures the full argument and doesn't leave trailing CSS as standalone declarations; (b) canonical `url("<decoded>")` restoration closes the validate-decoded/restore-raw differential — the browser executes the same value the validator saw; (c) `none` placeholder means step 3 never fires on a correctly-sanitized attribute; (d) per-invocation `nonce` prevents attacker-supplied `__SAFEURL_N__` literals from colliding with sentinels.
  5. Return `Promise.resolve(clean)`
- Commit `test/renderer.test.js` alongside the implementation — the security invariants (c–i) are durable

**Done when:** `node test/renderer.test.js` exits 0 with "All renderer tests pass" (fifteen lettered renderer fixtures: a–o, plus three direct `sanitizeStyle` assertions: unclosed-url step-3 keepAttr=false path, escaped-`)` unquoted-branch capture, re-escape `\22`→`\"` canonical-form invariant).

---

### T3: A2UI pipeline and SSR wrapper

**Depends on:** T2

**Tests (TDD):**

```javascript
// test/pipeline.test.js — run with: node test/pipeline.test.js
const assert = require('assert');

async function run() {
  // Probe A2UI v0_9 import — the API lives at sub-exports, not the default package exports (v0_8)
  const a2ui = require('@a2ui/react/v0_9');      // (a) no throw = pass
  const core = require('@a2ui/web_core/v0_9');   // (b) no throw = pass
  assert(typeof a2ui.A2uiSurface !== 'undefined', 'A2uiSurface not exported from @a2ui/react/v0_9');
  assert(typeof a2ui.MarkdownContext !== 'undefined', 'MarkdownContext not exported from @a2ui/react/v0_9');
  assert(typeof core.MessageProcessor === 'function', 'MessageProcessor not a function in @a2ui/web_core/v0_9');

  // Snapshot: message pair shapes (AC2) — must test production-built objects, not test-local literals
  // Export buildMessages(markdownString) from render-proof.js and assert its output shape here
  const { buildMessages } = require('../scripts/render-proof.js');
  const [prodCreate, prodUpdate] = buildMessages('# Hello');
  assert(Object.keys(prodCreate)[0] === 'createSurface', 'createSurface object-key shape wrong');
  assert(typeof prodCreate.createSurface.id === 'string', 'createSurface.id not a string');
  assert(Object.keys(prodUpdate)[0] === 'updateComponents', 'updateComponents object-key shape wrong');
  const comp = prodUpdate.updateComponents.components[0];
  assert(comp.component === 'Text', 'component type not Text');
  assert(typeof comp.text === 'string', 'component text not a string');
  assert(comp.text === '# Hello', 'component text must be the input markdown string');

  console.log('All pipeline tests pass');
}
run().catch(e => {
  if (e.message && e.message.includes('browser')) {
    console.error('SURFACE: A2UI SSR incompatible — browser globals at import time. Surface to human.');
  } else {
    console.error(e);
  }
  process.exit(1);
});
```

**Approach:**
- **Probe first** (before any further work): `node -e "require('@a2ui/react'); require('@a2ui/web_core')"` after `npm install`; if this throws referencing `window` / `document` / `navigator`, **surface to human** and stop — do not apply a silent shim
- After a clean probe, in `scripts/render-proof.js`:
  1. Import `{ A2uiSurface, MarkdownContext }` from `@a2ui/react`; import `{ MessageProcessor, basicCatalog }` from `@a2ui/web_core`; import `{ renderToStaticMarkup }` from `react-dom/server`; import React
  2. Extract and export `function buildMessages(markdownString)` that returns `[createMsg, updateMsg]` — this is the production function T3's AC2 test imports. The SSR path calls `buildMessages` rather than building the pair inline. Build message pair and process:
     ```js
     const createMsg = { createSurface: { id: 'proof-surface' } };
     const updateMsg = { updateComponents: { components: [{ id: 'proof-text', component: 'Text', text: markdownString }] } };
     const state = MessageProcessor([basicCatalog])(createMsg, updateMsg);
     ```
  3. Pre-resolve the renderer to avoid Suspense:
     ```js
     const preRendered = await renderMarkdown(markdownString, {});
     const resolver = (_md, _opts) => Promise.resolve(preRendered);
     ```
  4. Render to static HTML:
     ```js
     const innerHtml = renderToStaticMarkup(
       React.createElement(MarkdownContext.Provider, { value: resolver },
         React.createElement(A2uiSurface, { state }))
     );
     ```
  5. If `renderToStaticMarkup` throws a Suspense-related error (message includes "Suspense" or "use()"), **surface to human** with a clear message noting the fallback option (`renderToReadableStream`)

**Done when:** `node test/pipeline.test.js` exits 0; the A2UI import probe passes; `buildMessages` AC2 shape assertions pass. (`renderProof` is a T4 deliverable — its existence and SSR output are verified by T4's smoke test.)

---

### T4: Proof stylesheet and HTML wrapper

**Depends on:** T3

**Tests:**
- T4 renders via the `renderProof()` function directly (not the CLI — `parseArgs`/`validateInputPath`/`validateOutputPath` are T5's exports and must not be required here):
  ```javascript
  // quick inline smoke — run with: node -e "$(cat ...)" or inline in a test script
  const { renderProof } = require('./scripts/render-proof.js');
  const fs = require('fs');
  (async () => {
    const md = fs.readFileSync('evals/files/fixture.md', 'utf8');
    const { html } = await renderProof(md, {});
    fs.writeFileSync('proof-t4.html', html);
    if (html.length === 0) throw new Error('SSR output empty (AC4)');
    if (html.includes('<script')) throw new Error('SSR output contains script tag (AC4)');
    if (!html.includes('--proof-bg')) throw new Error('--proof-bg missing');
    if (html.includes('url(https://')) throw new Error('external url() present');
    console.log('T4 smoke pass');
  })().catch(e => { console.error(e); process.exit(1); });
  ```
- Visual QA: open `proof-t4.html` in browser; stone/slate muted palette; no header/sidebar; dark code blocks

**Approach:**
- Write the CSS as a template literal in `render-proof.js`, scoped under `.proof-body`:

  ```css
  :root {
    --proof-bg:       #fafaf9;  /* stone-50 */
    --proof-text:     #1c1917;  /* stone-900 */
    --proof-border:   #e7e5e4;  /* stone-200 */
    --proof-muted:    #78716c;  /* stone-500 */
    --proof-code-bg:  #24292e;  /* github-dark panel */
  }
  .proof-body { background: var(--proof-bg); color: var(--proof-text); ... }
  ```

- Type scale: `h1` 1.8rem/800, `h2` 1.4rem/700 with `border-bottom: 1px solid var(--proof-border)`, `h3` 1.15rem/600, `h4` 0.9rem/600 uppercase; `body` 1rem/1.7; `max-width: 72ch` centred on `<main>`
- Tables: `border-collapse: collapse`, `th` stone-200 background, `td` stone-100 alternating rows, rounded wrapper div
- Inline code: stone-100 background, stone-800 text, 3px/5px padding, 4px radius, monospace
- Pre/code: `var(--proof-code-bg)` background, `border-radius: 8px`, `overflow-x: auto`; Shiki provides per-token colors via `style=`
- Blockquote: `border-left: 3px solid var(--proof-border)`, stone-500 text, stone-50 background, left padding 1rem
- `<hr>`: stone-200, 1px solid
- Task-list checkboxes: `pointer-events: none` (read-only in a proof)
- System font stack; no external `@import`; no `url()` references to external origins in any CSS rule

- Wrap `renderToStaticMarkup` output:
  ```html
  <!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{css}</style>
  </head>
  <body class="proof-body">
    <main class="proof-main">{innerHtml}</main>
  </body>
  </html>
  ```
  Title: first `<h1>` text extracted via regex, or the input filename.

- Implement and export `async function renderProof(md, opts)` returning `{ html: string }` — combines the T3 SSR pipeline (renderMarkdown → buildMessages → renderToStaticMarkup) with the T4 HTML wrapper into one exportable function; does NOT write files or print output (file writing and stdout are handled by `main()` in T5, keeping T3/T4 tests free of path-validation and I/O side effects)

**Done when:** The `renderProof()` smoke script exits 0 and writes `proof-t4.html` (the T4 test itself calls `fs.writeFileSync`); visual QA passes (palette and layout match the spec's muted-review aesthetic). The full CLI path (including path confinement and argument parsing) is verified in T5+T6.

---

### T5: Input/output handling and security gates

**Depends on:** T1
*(Can be developed in parallel with T2–T4; merged into the same branch after T4)*

**Tests (TDD):**

```javascript
// test/security.test.js — run with: node test/security.test.js
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { validateInputPath, validateOutputPath, validateInputSize, parseArgs } = require('../scripts/render-proof.js');

const cwd = process.cwd();
// Isolated temp root for all test fixtures — avoids fixed-name collisions in shared os.tmpdir()
const testTmp = fs.mkdtempSync(path.join(os.tmpdir(), 'rp-sec-test-'));
try {

// AC7a — use a guaranteed-nonexistent traversal path (timestamped) to force the ENOENT branch
// deterministically on all platforms; '/etc/passwd' exists on macOS (symlinked via /private/etc)
// and would fire the containment branch instead, whose realpath'd error string (/private/etc/passwd)
// does not contain the lexical path.resolve(p) (/etc/passwd)
const traversalTarget = '../../../nonexistent-render-proof-test-' + Date.now();
const errA = validateInputPath(traversalTarget, cwd);
assert(errA !== null, 'traversal not rejected');
assert(errA.includes(path.resolve(traversalTarget)), 'ENOENT error must name the resolved path');

// AC7b — existing path outside cwd exercises the containment check (not ENOENT)
const outsideFile = path.join(testTmp, 'outside-probe.md');
fs.writeFileSync(outsideFile, '');
const errB = validateInputPath(outsideFile, cwd);
assert(errB !== null, 'existing path outside cwd not rejected by containment');
assert(errB.includes(fs.realpathSync(path.resolve(outsideFile))), 'containment error must name the resolved path — AC7a path-naming requirement applies to both ENOENT and containment branches (on Linux CI, /etc/passwd exists so the containment branch fires, not ENOENT)');

// AC7 — valid relative path accepted; fixture.md exists (full GFM content written in T1)
const ok = validateInputPath('evals/files/fixture.md', cwd);
assert(ok === null, 'valid path rejected: ' + ok);

// AC7c — symlink in cwd pointing outside is rejected
const symlinkTarget = path.join(testTmp, 'secret.md');
fs.writeFileSync(symlinkTarget, 'secret');
const symlinkPath = path.join(cwd, 'test-symlink-input-escape.md');
try {
  if (fs.existsSync(symlinkPath)) fs.unlinkSync(symlinkPath);
  fs.symlinkSync(symlinkTarget, symlinkPath);
  const errSym = validateInputPath('test-symlink-input-escape.md', cwd);
  assert(errSym !== null, 'input symlink escape not rejected');
} finally {
  if (fs.existsSync(symlinkPath)) fs.unlinkSync(symlinkPath);
}

// AC8 — output outside cwd rejected (allow-root confinement)
const errC = validateOutputPath('/etc/hosts', cwd);
assert(errC !== null, '/etc/hosts not rejected');
const errD = validateOutputPath('../sibling/out.html', cwd);
assert(errD !== null, '../sibling output not rejected');

// AC8d — root target unconditionally rejected
const errRoot = validateOutputPath('/', cwd);
assert(errRoot !== null, 'root / not rejected');

// AC8 — valid output within cwd accepted
const okOut = validateOutputPath('out/proof.html', cwd);
assert(okOut === null, 'valid output rejected: ' + okOut);

// AC8c — symlinked output directory inside cwd pointing outside is rejected
const outDirTarget = path.join(testTmp, 'outside-outdir');
fs.mkdirSync(outDirTarget);
const symlinkDirPath = path.join(cwd, 'test-symlink-outdir');
try {
  if (fs.existsSync(symlinkDirPath)) fs.unlinkSync(symlinkDirPath);
  fs.symlinkSync(outDirTarget, symlinkDirPath);
  const errSymOut = validateOutputPath('test-symlink-outdir/proof.html', cwd);
  assert(errSymOut !== null, 'output symlink-dir escape not rejected');
} finally {
  if (fs.existsSync(symlinkDirPath)) fs.unlinkSync(symlinkDirPath);
}

// AC13 — size cap; exactly 10 MB is at the limit and must be rejected
const sizeFile = path.join(testTmp, 'rp-size-test.md');
fs.writeFileSync(sizeFile, Buffer.alloc(10 * 1024 * 1024));
const errSize = validateInputSize(sizeFile);
assert(errSize !== null, '10 MB file not rejected');

// cwd-symlink divergence test (guards the fs.realpathSync(cwd) fix)
// Must be INSIDE the try so testTmp still exists; uses an actual symlink as cwd
// so reverting fs.realpathSync(cwd) to bare cwd would cause the test to fail on all platforms
const realCwdDir = path.join(testTmp, 'real-cwd');
fs.mkdirSync(realCwdDir);
const symlinkCwd = path.join(testTmp, 'symlink-cwd');
fs.symlinkSync(realCwdDir, symlinkCwd);  // symlink-cwd → real-cwd
const innerFile = path.join(realCwdDir, 'inner.md');
fs.writeFileSync(innerFile, '');
// validateInputPath must accept innerFile when cwd = symlinkCwd (symlink to realCwdDir)
// Without fs.realpathSync(cwd), symlinkCwd ≠ realpath(innerFile)'s parent → false rejection
const errCwdSym = validateInputPath(innerFile, symlinkCwd);
assert(errCwdSym === null, 'file inside symlinked cwd should be accepted when both sides are realpath-resolved: ' + errCwdSym);

} finally {
  fs.rmSync(testTmp, { recursive: true, force: true });
}

// parseArgs — defaults
const args = parseArgs(['fixture.md']);
assert(args.input === 'fixture.md', 'input wrong');
assert(args.output === 'fixture.html', 'output default wrong');

// parseArgs — explicit output
const args2 = parseArgs(['fixture.md', '--output', 'out/proof.html']);
assert(args2.output === 'out/proof.html', 'explicit output wrong');

console.log('All security tests pass');
```

**Approach:**
- Implement and export `validateInputPath(p, cwd)`:
  - Use `fs.realpathSync(path.resolve(p))` to follow symlinks and canonicalize the target
  - Compute `const cwdReal = fs.realpathSync(cwd)` to get the realpath'd root (matches `safe_io.confine`'s `root.resolve()` — on macOS `process.cwd()` under `/tmp` diverges from the realpath `/private/tmp`, causing false rejections if only one side is resolved)
  - Check component containment: `const rel = path.relative(cwdReal, resolved); return (!rel.startsWith('..') && !path.isAbsolute(rel)) ? null : errorString` where `errorString` **must include `resolved`** — AC7a requires the error to name the rejected path, and on systems where `/etc/passwd` exists (Linux CI), `fs.realpathSync` succeeds and the containment branch fires rather than ENOENT; requiring the resolved path in both branches makes the AC7a assertion cwd-independent
  - This implements the same semantics as the pack's `safe_io.confine` (realpath on both sides + component containment, not string prefix)
  - If `fs.realpathSync` throws `ENOENT` (file not found), return a rejection error string containing `path.resolve(p)` — ENOENT paths are unreadable regardless of containment; naming the pre-realpath resolved form satisfies AC7a even when realpath cannot succeed

- Implement and export `validateOutputPath(p, cwd)`:
  - Compute `const cwdReal = fs.realpathSync(cwd)` (same realpath'd root as `validateInputPath`, avoids macOS `/tmp`→`/private/tmp` divergence)
  - Compute `const resolved = path.resolve(p)` (lexical; the file need not exist yet)
  - If `path.dirname(resolved) === resolved`, unconditionally return a rejection error (filesystem root — `/` on Unix, drive root on Windows)
  - If `path.dirname(resolved)` exists (check with `fs.existsSync`): apply `fs.realpathSync` to the parent directory and run component containment on the real parent — this catches symlinked output directories inside cwd that point outside cwd; note there is a residual check-then-write TOCTOU window (a symlink could be swapped after the check), which cannot be fully closed without O_NOFOLLOW-style handling; document this limit in a comment
  - Otherwise (parent directory does not exist): run component containment on the lexical `resolved` path (write will fail anyway; traversal check still applies)
  - `const ref = (parentExists ? realpathParent : resolved); const rel = path.relative(cwdReal, ref); return (!rel.startsWith('..') && !path.isAbsolute(rel)) ? null : errorString`
  - Default output is `input.replace(/\.(md|markdown)$/i, '.html')` — within cwd when input is within cwd

- Implement and export `validateInputSize(resolvedPath)`:
  - `const { size } = fs.statSync(resolvedPath)`
  - Return null if `size < 10 * 1024 * 1024`; return error string naming size and limit otherwise

- Implement and export `parseArgs(argv)`:
  - `--output FILE`, `--help`/`-h`
  - Default output: `input.replace(/\.(md|markdown)$/i, '.html')`
  - Unknown flags → exit 1 with usage

- In `main()`, compute `const resolved = fs.realpathSync(path.resolve(args.input))` once and pass the same `resolved` to both `validateInputPath` and `validateInputSize`; this avoids a TOCTOU window between containment check and size check. Validate input path → size → output path before any I/O; exit 1 with stderr message on any rejection.
- Wrap the `cwdReal = fs.realpathSync(cwd)` computation in a try/catch in both `validateInputPath` and `validateOutputPath`; if it throws ENOENT (deleted cwd or dangling symlink), return a descriptive rejection string "working directory is unavailable" — the process fails closed with a clean message rather than an unhandled crash.

**Done when:** `node test/security.test.js` exits 0 with "All security tests pass"; `node scripts/render-proof.js --help` prints usage and exits 0.

---

### T6: Pack registration, evals fixture, spec README, and version bump

**Depends on:** T4, T5

**Tests (goal-based):**
- `grep 'version = "0.7.0"' packs/converters/pack.toml` exits 0 (AC12)
- `! grep -E '^skills =.*render-proof' packs/converters/pack.toml` exits 0 — confirm render-proof NOT in `[pack.evals].skills` (AC12)
- `grep 'render-proof' docs/specs/README.md` exits 0 — spec listed as active (AC12)
- `ls packs/converters/.apm/skills/render-proof/evals/files/fixture.md` exits 0 (AC9)
- Cross-cutting integration test (all twelve checks from Construction tests section) exits 0
- `python tools/lint-skill-spec.py` exits 0 — validates `eval_queries.json` schema (AC12; `agentbundle validate` does not read `SKILL.md` or `evals/`)
- `agentbundle validate packs/converters/` exits 0

**Approach:**
- Edit `packs/converters/pack.toml`: bump `version = "0.7.0"` only; do **not** add `"render-proof"` to `[pack.evals].skills` — the array entry is deferred to a follow-on PR where the queries can be reviewed; `run-pack-evals.py` only processes skills listed in the array so shipping `eval_queries.json` without the array entry is safe
- Update `docs/specs/README.md`: add `render-proof` to the active spec list
- The full GFM fixture at `evals/files/fixture.md` was written in T1 — T6 does not rewrite it; verify it exists and has content
- Run `python tools/lint-skill-spec.py` and confirm exit 0
- Run `agentbundle validate packs/converters/` and confirm exit 0
- Run the cross-cutting integration test

**Done when:** All six assertions pass; integration test exits clean; `agentbundle validate` exits 0.

## Rollout

Single PR — no feature flag, no gradual rollout. The skill is a new directory; no existing file under `packs/converters/.apm/skills/` is modified. The pack version bump (0.6.1 → 0.7.0) is the marketplace release signal; no agentbundle PyPI publish is triggered (converters is a marketplace pack, not a PyPI package; the separate marketplace.json bump PR is the publication step).

## Risks

1. **A2UI SSR incompatibility — RESOLVED (fallback applied).** `A2uiSurface` uses `useSyncExternalStore` without `getServerSnapshot` and throws under all React SSR modes (`renderToStaticMarkup` and `renderToReadableStream`): "Missing getServerSnapshot, which is required for server-rendered content." T3 confirmed the incompatibility. Fallback applied: DOMPurify-sanitized `renderMarkdown()` output passed to `dangerouslySetInnerHTML={{ __html: preRendered }}` via `renderToStaticMarkup` on a `<div>` wrapper, bypassing `A2uiSurface`. `MessageProcessor` is still called for pipeline integrity. All DOMPurify + `uponSanitizeAttribute` hook security guarantees are identical to the primary path. A2UI API at `@a2ui/react/v0_9` and `@a2ui/web_core/v0_9` (not default package exports).

2. **Async Shiki + synchronous `renderToStaticMarkup`.** If A2UI's `Text` component uses React 19's `use(promise)` to call the MarkdownContext renderer, `renderToStaticMarkup` may throw a Suspense-related error even when the Promise is pre-resolved. Mitigation: the pre-resolve closure (`Promise.resolve(alreadyRenderedHtml)`) should eliminate the Suspense boundary. If it does not, the fallback is `renderToReadableStream` + async stream collection — update plan.md changelog if this path is taken.

3. **jsdom footprint.** `jsdom` adds ~3 MB to the skill's `node_modules/`. No mitigation in v1; documented in SKILL.md under Dependencies.

4. **Shiki 1.x API.** Shiki 1.x (`codeToHtml(code, { lang, theme })`) is the target API. If `npm install` resolves an older cached Shiki 0.x (which used `highlight(code, lang)`), the call shape differs. Mitigation: `"shiki": "^1.0"` in `package.json` (matching the dep table) forces npm to resolve ^1 in the local `node_modules/`, independent of any global cache.

## Changelog

- 2026-07-06: implementation — Risk #1 confirmed: `A2uiSurface` uses `useSyncExternalStore` without `getServerSnapshot`; throws in both `renderToStaticMarkup` and `renderToReadableStream`; fallback applied (`dangerouslySetInnerHTML` + standalone `renderMarkdown()`). A2UI API at `@a2ui/react/v0_9` + `@a2ui/web_core/v0_9` (default exports are v0_8, missing `A2uiSurface`/`MessageProcessor`). `MessageProcessor` is a class (`new MessageProcessor()`), not a factory; `createSurface` message requires `catalogId: basicCatalog.id`. T3 test updated to v0_9 imports. Fixture (m) updated to raw HTML anchor — markdown-it `validateLink` blocks `javascript:` in link syntax; raw `<a href="...">` tests DOMPurify directly. Spec AC2/AC3/Objective and Risks #1 updated; all ACs checked; pack.toml bumped 0.6.1 → 0.7.0.
- 2026-07-04: initial plan
- 2026-07-04: rev 2 — applied adversarial + security review fixes: `ADD_ATTR` not `ALLOWED_ATTR` (was wrong in constraints); `fs.realpathSync()` + component containment for input path (replaces string-prefix + `path.resolve()`); allow-root confinement for output (replaces deny-list); added AC13 size cap; removed `render-proof` from `[pack.evals].skills` (deferred); added `docs/specs/README.md` to T6; redesigned AC5 offline checks (three `! grep -q` not one `grep -vq`); tightened AC6(d) test to assert exact `style="color:red"` on the specific span; added url() post-processing step to T2 and symlink test to T5
- 2026-07-04: rev 3 — applied second-pass review fixes: url() post-processor changed from `https?://` deny-list to allow-list (preserving `data:` and `#` forms only); added AC6(e) protocol-relative `url(//)` test; added AC5d protocol-relative grep check; AC8 updated to `fs.realpathSync` on parent directory for symlink-aware output confinement; AC8c symlinked-output-dir test added to T5; T5 happy-path assertion now uses a temp file created by the test (fixture.md exists as T1 stub but test creates its own to be explicit); AC7b uses `os.tmpdir()` existing path to exercise containment branch; AC7 error assertion tightened to require canonical path in message; T6 grep fixed to `! grep -E '^skills =.*render-proof'`; repo-root `.gitignore` attribution corrected
- 2026-07-04: rev 4 — applied third-pass review fixes:
  - url() post-processor changed to replace-function (not lookahead regex) to correctly handle quoted data: and # forms
  - AC6(f) test added for quoted data: URI preservation
  - AC5e/ftp: grep check added (five per-construct, not three)
  - T5 tests refactored to single mkdtempSync root (eliminates fixed-name collision risk in shared os.tmpdir())
  - AC8(d) root-target test added; AC8 validateOutputPath updated with root-target and parent-realpath logic
  - AC7a assertion tightened to require path.resolve(p) in ENOENT error; ENOENT error string requirement documented in approach
  - Full GFM fixture moved from T6 to T1 (Blocker: cross-cutting gate ran before fixture existed)
  - T4 "Done when" changed to use renderProof() smoke script (Blocker: was referencing proof-test.html that no T4 task produced); `/tmp` output paths changed to cwd-relative `proof-test.html` throughout
  - T1 fixture assertions made mechanical (8 specific grep checks)
  - AC9 checkbox/blockquote/hr greps added to 12-check cross-cutting gate
  - Stray docs/specs/markdown-proof-renderer/ deleted
- 2026-07-04: rev 5 — applied fourth-pass review fixes:
  - url() strip changed from replace-function to uponSanitizeAttribute DOMPurify hook with CSS-escape decoding (handles unbalanced-quote and CSS-escape bypass forms that regex post-processors miss)
  - T2 tests: AC6(g) unbalanced-quote and AC6(h) CSS-escape bypass fixtures added
  - T5/main() single-resolved-path note added (TOCTOU prevention)
  - T6 check count corrected to twelve
- 2026-07-04: rev 6 — applied fifth-pass review fixes:
  - data: allow-list narrowed to safe-MIME image types only (data:image/png|jpeg|gif|webp); data:text/html and other unsafe MIME types now stripped (Security Blocker 1)
  - hook step 1 added: strip expression(, behavior:, -moz-binding: (historic CSS-eval vectors; Security Blocker 2)
  - hook step 3 added: drop entire style attribute if any url( remains after rewriting (defense-in-depth; Security Blocker 3)
  - T2 tests: AC6(i) data:text/html fixture added
  - validateInputPath and validateOutputPath: cwd realpath-resolved (fs.realpathSync(cwd)) to match safe_io.confine and avoid macOS /tmp divergence (Security Concern 4)
  - Output TOCTOU: residual race noted in comment (Security Concern 5)
  - T3 tests: AC2 shape assertions added for createMsg/updateMsg object-key form (Adversarial Concern 1)
  - Risk #1 fallback: DOMPurify sanitization guarantee re-stated for the fallback path (Security Nit 10)
  - AC5 greps: -i flag added for case-insensitive match (Security Nit 9)
  - Spec Testing Strategy: 9 → 13 checks (added checkbox/blockquote/hr/--output); output filename aligned to proof-test.html (Adversarial Concerns 3-4)
  - AC6 in spec updated: nine fixtures, CSS-escape decode and step sequence described, unsafe data: MIME treatment explicit (Adversarial Concern 2)
- 2026-07-04: rev 8 — applied seventh-pass review fixes:
  - Hook: quoted-aware regex with three branches (dq/sq/uq) — prevents truncation on ) inside quoted url() args (Security Blocker 2)
  - Hook: canonical url("<decoded>") restoration replaces raw `full` — closes validate-decoded/restore-raw parse differential (Security Blocker 1)
  - Hook: `none` placeholder replaces `url(removed)` — prevents unsafe-token placeholder self-triggering step 3 backstop (Security Concern 4)
  - Hook: per-invocation nonce sentinel prefix (Security Concern 3 / Adversarial Nit 5)
  - Hook: refactored into exported sanitizeStyle() for testability
  - T2: fixture (k) added — mixed safe+unsafe url() tokens preserves adjacent non-url declarations (AC6k)
  - T3 Approach: explicit buildMessages() export step added (Adversarial Blocker 1)
  - T5: cwd-symlink test moved inside try block (Adversarial Blocker 2 — was running after testTmp deleted)
  - T5: cwd-symlink test uses actual fs.symlinkSync for cwd — no-op Linux guard fixed (Adversarial Concern 3)
  - AC6 mode-per-AC rationale updated: "url() post-processing" → "in-hook url() sentinel sanitization" (Adversarial Concern 4)
  - AC6: eleven fixtures (added k for mixed-token adjacent preservation)
- 2026-07-06: rev 17 — applied sixteenth-pass review fix:
  - T3 test: fully removed `renderProof` import and typeof check — existence check had same forward-dependency as the call (renderProof is T4, T4 Depends on T3); T3 test is now import probe + buildMessages only (Adversarial Blocker 1)
  - T3 "Done when": removed "renderProof confirmed exported" clause
- 2026-07-06: rev 16 — applied fifteenth-pass review fix:
  - T3/T4 task-DAG forward dependency: T3's test called `renderProof` (a T4 export) — moved `html.length > 0` and `!html.includes('<script')` AC4 assertions to T4's smoke; T3 retains only import probe + `buildMessages` + typeof-check (Adversarial Concern 1)
- 2026-07-06: rev 15 — applied fourteenth-pass review fixes:
  - Spec `Status: Draft` → `Approved` — spec is execution-ready after 14 passes; leaving it Draft signals the contract is still being drafted (Adversarial Concern 1)
  - T4 Approach: "implement and export `async function renderProof(md, opts)` returning `{ html: string }`" made explicit — previously only described in a note, asymmetric with T2/T5 explicit export directives (Adversarial Nit 2)
- 2026-07-06: rev 14 — applied thirteenth-pass review fixes:
  - Lint invocation fixed: `python tools/lint-skill-spec.py` (no path arg) — tool walks the whole repo via env var `LINT_ROOT`; a path argument is silently ignored (Adversarial Blocker 1)
  - Fixture (p) replaced with direct `sanitizeStyle` re-escape assertion: `reEscapeResult.includes('url("data:image/png;base64,A\\"B")')` pins the `"` → `\"` re-escape invariant directly on raw CSS string; `includes('data:image/png')` was too weak (Adversarial Blocker 2)
  - Spec AC6: added fixture (m) (CSS-hex `"` → `\"` re-escape); updated "Twelve" → "Thirteen" (Adversarial Concern 3)
  - T2 Done-when: corrected to "fifteen lettered fixtures (a–o) plus three direct sanitizeStyle assertions" (Adversarial Concern 4)
- 2026-07-06: rev 13 — applied twelfth-pass review fixes:
  - Spec AC7a: test case (a) updated from `../../../etc/passwd` to timestamped-nonexistent path — macOS `/etc/passwd` exists via `/private/etc` symlink and fires containment branch (emits `/private/etc/passwd`), not ENOENT; spec and plan now agree (Adversarial Concern 3)
  - Spec AC12: added `python tools/lint-skill-spec.py` as the eval_queries.json verification gate; clarified `agentbundle validate` covers pack.toml schema only (Adversarial Concern 1)
  - Spec AC13: added stat/read TOCTOU residual note (accepted under same trust assumption as AC8) (Security Concern 2)
  - T1: extended `node -e` assertion to check `query` non-empty string and `should_trigger` boolean per `lint-skill-spec.py:556-567` (Adversarial Concern 2)
  - T2: added fixture (p) — CSS-hex-encoded double-quote in safe data: URI pins the canonical-restore re-escape invariant; updated "Done when" to sixteen fixtures (Security Concern 1)
  - T6: added `python tools/lint-skill-spec.py` to tests and approach; corrected T6 approach note about run-pack-evals.py
- 2026-07-06: rev 12 — applied eleventh-pass review fixes:
  - T1 + AC12: ship `evals/eval_queries.json` — `tools/lint-skill-spec.py:661-663` hard-errors on `evals/` with no `evals.json` or `eval_queries.json`; AC12 reasoning corrected (Adversarial Blocker 1)
  - T5 errA: replace `'../../../etc/passwd'` with timestamped nonexistent path — macOS `/etc` is a symlink so realpath succeeds and the containment branch (not ENOENT) fires, emitting `/private/etc/passwd` which doesn't contain the lexical `path.resolve(p)` (Adversarial Concern 2)
  - T2 fixture (g): label corrected from `(AC6e,g)` to `(AC6e)` — AC6g is the unbalanced-quote form, covered by fixture (i) (Adversarial Nit 3)
  - AC6: added scope note — hook validates `url()` arguments only; non-url CSS property values not restricted (Security Concern 2)
  - AC8: added documented TOCTOU residual + POSIX-only scope for confinement logic (Security Concern 3)
- 2026-07-06: rev 11 — applied tenth-pass review fixes:
  - Spec Always-do + AC6: unquoted URL branch updated from `[^)]*` to `(?:[^)\\]|\\.)*?` — honors `\)` to prevent truncation attacks that leak tail CSS declarations (Security Blocker)
  - T5 Approach: containment error must include `resolved` — AC7a path-naming requirement applies to both ENOENT and containment branches; on Linux CI `/etc/passwd` exists so containment fires, not ENOENT (Adversarial Concern 4)
  - T5 Test: added AC7b assertion `errB.includes(fs.realpathSync(path.resolve(outsideFile)))` to verify containment branch names the rejected path (Adversarial Concern 4)
  - T4 Approach + T3 Test: `renderProof(md, opts)` returns `{ html }` only; file writing handled by `main()` (Adversarial Concern 5)
- 2026-07-06: rev 10 — applied ninth-pass review fixes:
  - `markdown-it-task-lists@^2` added as 9th runtime dep — markdown-it core does not emit `type="checkbox"` natively; AC9 cross-cutting gate would fail without it (Adversarial Blocker 1)
  - T2 Approach: added module-scope bullet — `sanitizeStyle/isSafeMime/decodeCSS` must be at module scope and exported; step-4 code block now has NOTE comment clarifying this (Adversarial Blocker 2)
  - `isSafeMime`: added `if (/[\x00-\x1f\x7f]/.test(decoded)) return false` as first check — CSS-escape `\a` inside a safe-MIME prefix decodes to a literal newline that terminates the CSS quoted string, allowing injection after a safe-looking prefix (Security Blocker 1)
  - T2 fixture (o) added: `url(data:image/png;base64,AAA\a x:url(//evil))` → control-char rejection (AC6l, Security Blocker 1)
  - Step 4 code block: DOMPurify import order fixed — require jsdom window before `createDOMPurify(window)`; added NOTE that functions are shown inline for reference but belong at module scope (Adversarial Concern 3)
  - Step 1 comment updated: IE-era keyword stripping is best-effort; runs before CSS-escape decode (Security Concern 2)
  - Step numbering fixed: step 6 → step 5 (Adversarial Nit 4)
  - Test comment added: plan fixture (a)–(o) vs spec AC6 (a)–(l) label drift noted; AC6x tags are binding (Adversarial Nit 5)
  - Dependency count updated throughout: 8 → 9
- 2026-07-06: rev 9 — applied eighth-pass review fixes:
  - T2 fixture (k): assertion changed from `||` to `&&` — requires color:red preserved AND safe data:image/png preserved AND unsafe url() stripped (not just one of them) (Adversarial Blocker 1)
  - T2 fixture (k): input updated to include a safe `data:image/png;base64,ABC` url() token alongside the unsafe `url(https://evil.com)` token so the `&&` assertion is exercisable (Adversarial Blocker 2)
  - T2: duplicate `(l)` label fixed — second `(l)` (javascript: href, AC6j) relabeled `(m)`; old `(m)` (unknown lang) relabeled `(n)` (Adversarial Concerns 3+4)
  - T2: added direct `sanitizeStyle` test: `sanitizeStyle('background:url(unclosed')` must return null, exercising the step-3 keepAttr=false path (Security Concern 3)
  - T2: import changed to `{ renderMarkdown, sanitizeStyle }` to expose sanitizeStyle for direct testability
- 2026-07-04: rev 7 — applied sixth-pass review fixes:
  - Hook redesigned with sentinel approach: step 2 replaces ALL url() tokens (safe → __SAFEURL_N__, unsafe → url(removed)); step 3 only sees unmatched bypass forms; step 4 restores sentinels — resolves step-2/step-3 mutual exclusion (Security Blocker 2, Adversarial Blocker 1)
  - data.keepAttr = false (not forceKeepAttr) — forceKeepAttr = false is a no-op (Adversarial Blocker 2)
  - SAFE_MIME matching delimiter-anchored: requires ';' or ',' after prefix, not any longer string (Security Concern 1)
  - CSS escape decode extended to non-hex backslash escapes (\\(.)) and null codepoint → U+FFFD (Security Concern 3)
  - CSS comments stripped before step-1 keyword checks (Security Concern 4 / expression() comment-splitting)
  - fs.realpathSync(cwd) wrapped in try/catch → clean failure message (Security Concern 5)
  - AC6(j) fixture: javascript: href stripped by DOMPurify default; T2 test (l) added (Security Concern 6)
  - AC6 Testing Strategy: missing protocol-relative fixture (e) bullet added (Adversarial Concern 3)
  - AC7 body: path.relative(cwdReal, resolved) (Adversarial Concern 4)
  - Plan Constraint for output path updated to match approach (Adversarial Concern 5)
  - T5: cwd-symlink divergence test added (Adversarial Concern 6)
  - T3: AC2 asserts production-built buildMessages() output, not test-local literals (Adversarial Concern 7)
  - Construction test count note clarified: 12 assertions + 1 setup invocation (Adversarial Nit 8)
