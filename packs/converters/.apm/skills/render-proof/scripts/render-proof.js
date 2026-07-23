'use strict';

const path = require('path');
const fs = require('fs');

// ─── Helpers ──────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ─── CSS sanitization helpers (module scope — exported for testability) ────────

function decodeCSS(s) {
  return s
    .replace(/\\([0-9a-fA-F]{1,6})\s?/g, (_, h) => {
      const cp = parseInt(h, 16);
      return cp === 0 ? '�' : String.fromCodePoint(cp);
    })
    .replace(/\\(.)/g, '$1');
}

const SAFE_DELIMITED = ['data:image/png', 'data:image/jpeg', 'data:image/gif', 'data:image/webp'];

function isSafeMime(decoded) {
  if (/[\x00-\x1f\x7f]/.test(decoded)) return false; // C0/DEL: CSS string-terminating, injection vector
  if (decoded === '#' || decoded.startsWith('#')) return true;
  return SAFE_DELIMITED.some(m =>
    decoded === m || decoded.startsWith(m + ';') || decoded.startsWith(m + ',')
  );
}

function sanitizeStyle(attrValue) {
  const nonce = Math.random().toString(36).slice(2);
  let val = attrValue;
  // Step 1: CSS comments; IE-era eval vectors (best-effort; runs before decode —
  // escaped variants like \65xpression( pass through unmodified)
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
  // Step 3: backstop — any url( remaining means an unmatched bypass form
  if (/url\s*\(/i.test(val)) return null; // signal: drop attribute via keepAttr = false
  // Step 4: restore canonical safe forms
  restored.forEach((s, i) => { val = val.replace(`__SAFEURL_${nonce}_${i}__`, s); });
  return val;
}

// ─── buildMessages ────────────────────────────────────────────────────────────
// Returns the createSurface + updateComponents message pair in object-key shape.
// catalogId is included in createSurface because MessageProcessor requires it.

function buildMessages(markdownString) {
  const { basicCatalog } = require('@a2ui/react/v0_9');
  const createMsg = { createSurface: { id: 'proof-surface', catalogId: basicCatalog.id } };
  const updateMsg = {
    updateComponents: {
      components: [{ id: 'proof-text', component: 'Text', text: markdownString }]
    }
  };
  return [createMsg, updateMsg];
}

// ─── renderMarkdown ───────────────────────────────────────────────────────────

async function renderMarkdown(md, options) {
  const markdownIt = require('markdown-it');
  const taskLists = require('markdown-it-task-lists');
  const { JSDOM } = require('jsdom');
  const createDOMPurify = require('dompurify');

  const mdi = markdownIt({ html: true, linkify: true });
  mdi.use(taskLists);

  // Build Shiki highlighter with a fixed set of bundled languages; unknown langs
  // are caught per-token in the fence rule and fall back to plain <pre><code>
  let highlighter = null;
  try {
    const { createHighlighter } = require('shiki');
    highlighter = await createHighlighter({
      themes: ['github-dark'],
      langs: [
        'python', 'javascript', 'typescript', 'bash', 'sh', 'shell',
        'json', 'html', 'css', 'yaml', 'markdown', 'sql',
        'java', 'go', 'rust', 'cpp', 'c', 'ruby', 'php', 'text'
      ],
    });
  } catch (_e) {
    // Highlighter creation failed — fence rule falls back to plain code blocks
  }

  // Override fence rule for syntax highlighting
  mdi.renderer.rules.fence = (tokens, idx) => {
    const token = tokens[idx];
    const lang = (token.info || '').trim().split(/\s+/)[0];
    const code = token.content;
    if (lang === 'mermaid') {
      return `<div class="mermaid-wrap"><pre class="mermaid-source">${mdi.utils.escapeHtml(code)}</pre></div>`;
    }
    if (highlighter) {
      try {
        return highlighter.codeToHtml(code, { lang: lang || 'text', theme: 'github-dark' });
      } catch (_e) {
        // Unknown language — fall back to plain escaped code block
      }
    }
    return `<pre><code>${mdi.utils.escapeHtml(code)}</code></pre>`;
  };

  let html = mdi.render(md);

  // DOMPurify sanitization — require jsdom window BEFORE createDOMPurify
  const { window } = new JSDOM('');
  const purify = createDOMPurify(window);

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

  return Promise.resolve(clean);
}

// ─── CSS ──────────────────────────────────────────────────────────────────────

// Design language: white paper, hard hairlines, mono labels, Fraunces italic h1 accent,
// zero radius. System-font fallbacks preserve offline capability; add a Google Fonts
// @import for 'Fraunces' and 'JetBrains Mono' at the top to get the full PPT-proof look.
const PROOF_CSS = `
:root {
  --ink:      #000000;
  --paper:    #ffffff;
  --paper-warm: #fafafa;
  --rule:     #d8d8d8;
  --muted:    #555555;
  --code-bg:  #1e1e1e;
  --mono: 'JetBrains Mono', ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace;
  --serif: 'Fraunces', Georgia, 'Times New Roman', serif;
  --sans: 'Inter Tight', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
}
* { box-sizing: border-box; }
body.proof-body {
  background: var(--paper);
  color: var(--ink);
  font-family: var(--sans);
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  padding: 32px 24px;
}
main.proof-main { max-width: 72ch; margin: 0 auto; }
h1 {
  font-family: var(--serif);
  font-style: italic;
  font-size: 2rem;
  font-weight: 400;
  margin-top: 0;
  margin-bottom: 0.5rem;
  border-bottom: 3px solid var(--ink);
  padding-bottom: 0.4rem;
}
h2 {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  border-bottom: 1px solid var(--rule);
  padding-bottom: 0.3rem;
  margin-top: 2rem;
}
h3 { font-size: 1rem; font-weight: 700; margin-top: 1.5rem; }
h4 {
  font-family: var(--mono);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--muted);
  margin-top: 1.25rem;
}
p { margin: 0.75rem 0; }
a { color: inherit; text-decoration: underline; text-underline-offset: 2px; }
code:not(pre code) {
  font-family: var(--mono);
  font-size: 0.85em;
  background: var(--paper-warm);
  border: 1px solid var(--rule);
  padding: 0.1em 0.35em;
}
pre {
  overflow-x: auto;
  margin: 1rem 0;
  border: 1px solid var(--rule);
}
pre code {
  display: block;
  padding: 1rem;
  font-family: var(--mono);
  font-size: 0.8rem;
}
.shiki { background: var(--code-bg) !important; border: none; overflow-x: auto; }
.shiki code { padding: 1rem; display: block; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
th {
  background: var(--paper-warm);
  padding: 5px 12px;
  text-align: left;
  border: 1px solid var(--rule);
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}
td { padding: 6px 12px; border: 1px solid var(--rule); vertical-align: top; }
tr:nth-child(even) td { background: var(--paper-warm); }
blockquote {
  border-left: 3px solid var(--rule);
  color: var(--muted);
  margin: 1rem 0;
  padding: 0.5rem 1rem;
}
hr { border: none; border-top: 1px solid var(--rule); margin: 2rem 0; }
input[type="checkbox"] { pointer-events: none; }
ol, ul { padding-left: 1.5rem; }
li { margin: 0.25rem 0; }
.mermaid-wrap {
  margin: 1.5rem 0;
  border: 1px solid var(--rule);
  overflow: hidden;
}
.mermaid-source {
  background: var(--paper-warm);
  border: none;
  margin: 0;
  color: var(--muted);
  font-size: 0.75rem;
}
.mermaid-canvas {
  padding: 1.5rem;
  text-align: center;
}
.mermaid-canvas svg { max-width: 100%; height: auto; }
.mermaid-error {
  padding: 0.75rem 1rem;
  font-family: var(--mono);
  font-size: 0.75rem;
  color: #b91c1c;
  background: #fef2f2;
  border-top: 1px solid #fecaca;
}
@media print {
  @page { margin: 2cm; }
  body.proof-body { background: var(--paper); color: var(--ink); padding: 0; }
  main.proof-main { max-width: 100%; margin: 0; }
  pre, .shiki { background: var(--paper-warm) !important; border: 1px solid var(--rule); overflow-x: visible; }
  pre code, .shiki code { white-space: pre-wrap; overflow-wrap: break-word; color: var(--ink); }
  .shiki span[style] { color: inherit !important; background: none !important; }
  h2, h3, h4 { break-after: avoid; }
  pre, blockquote, table, figure { break-inside: avoid; }
  a { color: var(--ink); text-decoration: none; }
  a[href^="http"]::after { content: " (" attr(href) ")"; font-size: 0.8em; color: var(--muted); }
  .mermaid-wrap { break-inside: avoid; }
  .mermaid-canvas { padding: 1rem 0; }
  .mermaid-source { display: none !important; }
}
`;

// ─── renderProof ──────────────────────────────────────────────────────────────
// Risk #1 fallback: A2uiSurface uses useSyncExternalStore without getServerSnapshot,
// which throws under all React SSR rendering modes. The fallback wraps the
// DOMPurify-sanitized markdown HTML in a dangerouslySetInnerHTML div and passes it
// through renderToStaticMarkup, preserving all security guarantees.
// MessageProcessor is still instantiated and exercised for pipeline integrity.

async function renderProof(md, opts) {
  const React = require('react');
  const { renderToStaticMarkup } = require('react-dom/server');
  const { basicCatalog } = require('@a2ui/react/v0_9');
  const { MessageProcessor } = require('@a2ui/web_core/v0_9');

  // Pre-render markdown to sanitized HTML
  const preRendered = await renderMarkdown(md, opts || {});
  const hasMermaid = preRendered.includes('class="mermaid-source"');

  // Build and exercise the MessageProcessor pipeline (Risk #1 fallback:
  // A2uiSurface SSR throws; rendering falls back to dangerouslySetInnerHTML)
  const [createMsg, updateMsg] = buildMessages(md);
  try {
    const proc = new MessageProcessor([basicCatalog]);
    proc.processMessages([createMsg, updateMsg]);
  } catch (_e) {
    // Pipeline exercise is best-effort; render proceeds via fallback
  }

  // Fallback render: dangerouslySetInnerHTML passes preRendered through renderToStaticMarkup
  const wrapped = renderToStaticMarkup(
    React.createElement('div', { dangerouslySetInnerHTML: { __html: preRendered } }) // nosemgrep: typescript.react.security.audit.react-dangerouslysetinnerhtml.react-dangerouslysetinnerhtml
  );
  // Strip outer <div>...</div> wrapper (5 chars prefix, 6 chars suffix)
  const innerHtml = wrapped.slice(5, -6);

  // Extract title from first h1 (strip tags)
  const titleMatch = innerHtml.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
  const title = titleMatch
    ? titleMatch[1].replace(/<[^>]+>/g, '').trim()
    : 'Proof';

  const mermaidRuntime = hasMermaid ? `
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11.16.0/dist/mermaid.min.js" integrity="sha384-T/0lMUdJpd2S1ZHtRiofG3htU3xPCrFVeAQ1UUE2TJwlEJSV5NUwn30kP28n238E" crossorigin="anonymous"></script>
  <script>
  mermaid.initialize({
    startOnLoad: false, theme: 'neutral', securityLevel: 'antiscript',
    flowchart:     { useMaxWidth: true, htmlLabels: true },
    sequence:      { useMaxWidth: true },
    gantt:         { useMaxWidth: true },
    er:            { useMaxWidth: true },
    pie:           { useMaxWidth: true },
    gitGraph:      { useMaxWidth: true },
    quadrantChart: { useMaxWidth: true },
    xyChart:       { useMaxWidth: true },
    block:         { useMaxWidth: true },
    timeline:      { useMaxWidth: true },
    mindmap:       { useMaxWidth: true },
    packet:        { useMaxWidth: true },
    requirement:   { useMaxWidth: true },
    kanban:        { useMaxWidth: true },
    class:         { useMaxWidth: true },
    state:         { useMaxWidth: true },
    journey:       { useMaxWidth: true },
  });
  (function () {
    async function renderAll() {
      var sources = document.querySelectorAll('.mermaid-source');
      for (var i = 0; i < sources.length; i++) {
        var pre = sources[i];
        var wrap = pre.parentElement;
        var code = pre.textContent || '';
        try {
          var res = await mermaid.render('proof-mmd-' + i, code);
          var cv = document.createElement('div');
          cv.className = 'mermaid-canvas';
          cv.innerHTML = res.svg;
          var svgEl = cv.querySelector('svg');
          if (svgEl) { svgEl.removeAttribute('width'); svgEl.removeAttribute('height'); svgEl.style.maxWidth = '100%'; }
          wrap.insertBefore(cv, pre);
          pre.style.display = 'none';
        } catch (e) {
          var errDiv = document.createElement('div');
          errDiv.className = 'mermaid-error';
          errDiv.textContent = 'Parse error: ' + (e.message || String(e));
          wrap.appendChild(errDiv);
        }
      }
    }
    if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', renderAll); }
    else { renderAll(); }
  })();
  </script>` : '';

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(title)}</title>
  <style>${PROOF_CSS}</style>
</head>
<body class="proof-body">
  <main class="proof-main">${innerHtml}</main>${mermaidRuntime}
</body>
</html>`;

  return { html };
}

// ─── Path validation ──────────────────────────────────────────────────────────

function validateInputPath(p, cwd) {
  let cwdReal;
  try {
    cwdReal = fs.realpathSync(cwd);
  } catch (_e) {
    return 'working directory is unavailable: ' + cwd;
  }

  let resolved;
  try {
    resolved = fs.realpathSync(path.resolve(p));
  } catch (e) {
    if (e.code === 'ENOENT') {
      return 'file not found: ' + path.resolve(p);
    }
    return 'cannot resolve path: ' + path.resolve(p) + ' (' + e.message + ')';
  }

  const rel = path.relative(cwdReal, resolved);
  if (rel.startsWith('..') || path.isAbsolute(rel)) {
    return 'path is outside the working directory: ' + resolved;
  }
  return null;
}

function validateOutputPath(p, cwd) {
  let cwdReal;
  try {
    cwdReal = fs.realpathSync(cwd);
  } catch (_e) {
    return 'working directory is unavailable: ' + cwd;
  }

  const resolved = path.resolve(p);

  // Reject filesystem root (path.dirname('/') === '/' on POSIX)
  if (path.dirname(resolved) === resolved) {
    return 'output path is a filesystem root: ' + resolved;
  }

  const parent = path.dirname(resolved);
  let ref;
  if (fs.existsSync(parent)) {
    try {
      // Residual TOCTOU: a symlink could be swapped after this check;
      // accepted under local single-user trusted-agent trust model
      ref = fs.realpathSync(parent);
    } catch (_e) {
      ref = parent;
    }
  } else {
    ref = resolved;
  }

  const rel = path.relative(cwdReal, ref);
  if (rel.startsWith('..') || path.isAbsolute(rel)) {
    return 'output path is outside the working directory: ' + resolved;
  }
  return null;
}

function validateInputSize(resolvedPath) {
  const { size } = fs.statSync(resolvedPath);
  if (size >= 10 * 1024 * 1024) {
    return (
      'file is too large: ' +
      (size / 1024 / 1024).toFixed(1) +
      ' MB (limit: 10 MB): ' +
      resolvedPath
    );
  }
  return null;
}

// ─── parseArgs ────────────────────────────────────────────────────────────────

function parseArgs(argv) {
  let input = null;
  let output = null;
  let help = false;

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--help' || arg === '-h') {
      help = true;
    } else if (arg === '--output') {
      output = argv[++i];
    } else if (!arg.startsWith('-')) {
      input = arg;
    } else {
      process.stderr.write('Unknown flag: ' + arg + '\n');
      process.exit(1);
    }
  }

  if (!help && !input) {
    process.stderr.write(
      'Error: input file required\n' +
      'Usage: node scripts/render-proof.js <input.md> [--output <file.html>]\n'
    );
    process.exit(1);
  }

  if (!output && input) {
    output = input.replace(/\.(md|markdown)$/i, '.html');
    if (output === input) output = input + '.html';
  }

  return { input, output, help };
}

// ─── main ─────────────────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    process.stdout.write(
      'Usage: node scripts/render-proof.js <input.md> [--output <file.html>]\n'
    );
    process.exit(0);
  }

  const cwd = process.cwd();

  const inputErr = validateInputPath(args.input, cwd);
  if (inputErr) { process.stderr.write(inputErr + '\n'); process.exit(1); }

  let resolved;
  try {
    resolved = fs.realpathSync(path.resolve(args.input));
  } catch (e) {
    process.stderr.write('Cannot read file: ' + args.input + '\n');
    process.exit(1);
  }

  const sizeErr = validateInputSize(resolved);
  if (sizeErr) { process.stderr.write(sizeErr + '\n'); process.exit(1); }

  const outputErr = validateOutputPath(args.output, cwd);
  if (outputErr) { process.stderr.write(outputErr + '\n'); process.exit(1); }

  const md = fs.readFileSync(resolved, 'utf8');
  const { html } = await renderProof(md, {});

  const outPath = path.resolve(args.output);
  const outDir = path.dirname(outPath);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }
  fs.writeFileSync(outPath, html, 'utf8');
  process.stdout.write('OUTPUT: ' + outPath + '\n');
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  decodeCSS,
  isSafeMime,
  sanitizeStyle,
  buildMessages,
  renderMarkdown,
  renderProof,
  validateInputPath,
  validateOutputPath,
  validateInputSize,
  parseArgs,
};

if (require.main === module) {
  main().catch(e => {
    process.stderr.write(String(e) + '\n');
    process.exit(1);
  });
}
