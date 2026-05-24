#!/usr/bin/env node
/**
 * render.js — Markdown → self-contained styled HTML.
 *
 * Uses `marked` for parsing and `highlight.js` for code blocks.
 * Wraps mermaid fenced blocks for the runtime CDN renderer, detects
 * callout patterns (Note / Tip / Warning / Important / Stop), builds
 * sidebar nav and print TOC from h2/h3 headings, and stamps it all
 * into scripts/template.html.
 *
 * Usage:
 *   node scripts/render.js <input.md>
 *     [--output <file.html>]
 *     [--title <title>]      # default: first H1, or filename
 *     [--subtitle <text>]    # optional header subtitle
 *     [--theme navy|green|teal|amber|rose]   # default: navy
 *     [--no-mermaid]         # skip the Mermaid CDN script
 */

const fs = require('fs');
const path = require('path');

let marked, hljs;
try {
  marked = require('marked');
  hljs = require('highlight.js');
} catch (e) {
  // Resolve the skill directory so the install hint matches the user's
  // actual layout (works whether the skill is checked out under
  // dropkit/skills/... or copied into ~/.claude/skills/markdown-to-html/).
  const skillDir = path.dirname(__dirname);
  console.error(
    'error: missing dependency `marked` or `highlight.js`. Install with:\n' +
    `  (cd "${skillDir}" && npm install)`
  );
  process.exit(1);
}

// --- theme palettes -------------------------------------------------------

const THEMES = {
  navy:  { dark: '#0f1f3d', mid: '#1a3a6b', light: '#e8f0fb' },
  green: { dark: '#14532d', mid: '#166534', light: '#dcfce7' },
  teal:  { dark: '#134e4a', mid: '#115e59', light: '#ccfbf1' },
  amber: { dark: '#78350f', mid: '#92400e', light: '#fef3c7' },
  rose:  { dark: '#881337', mid: '#9f1239', light: '#ffe4e6' },
};

// --- arg parsing ----------------------------------------------------------

function parseArgs(argv) {
  const args = { theme: 'navy', mermaid: true };
  const takesValue = new Set(['--output', '--title', '--subtitle', '--theme']);
  let i = 0;
  while (i < argv.length) {
    const a = argv[i];
    if (takesValue.has(a)) {
      const v = argv[i + 1];
      if (v === undefined || v.startsWith('-')) {
        console.error(`error: ${a} requires a value`);
        process.exit(1);
      }
      if (a === '--output')        args.output = v;
      else if (a === '--title')    args.title = v;
      else if (a === '--subtitle') args.subtitle = v;
      else if (a === '--theme')    args.theme = v;
      i += 2;
      continue;
    }
    if (a === '--no-mermaid') { args.mermaid = false; i++; continue; }
    if (a === '-h' || a === '--help') { args.help = true; i++; continue; }
    if (a.startsWith('-')) {
      console.error(`error: unknown flag ${a}`);
      process.exit(1);
    }
    if (!args.input) { args.input = a; i++; continue; }
    console.error(`error: unexpected positional argument ${a}`);
    process.exit(1);
  }
  return args;
}

const HELP = `Usage: node scripts/render.js <input.md> [options]

Options:
  --output FILE       Output HTML path (default: input with .html extension)
  --title TEXT        Page title (default: first H1, or input filename)
  --subtitle TEXT     Header subtitle
  --theme NAME        Color theme: navy (default), green, teal, amber, rose
  --no-mermaid        Skip Mermaid CDN script (no diagrams in source)
  -h, --help          Show this help`;

// --- callout post-processing ---------------------------------------------

const CALLOUT_KINDS = ['Note', 'Tip', 'Warning', 'Important', 'Stop'];

function applyCallouts(html) {
  // Wrap paragraphs that begin with a known bold lead-in
  // ("**Note:** ...") in a styled callout box. The lead-in stays
  // visible inside the box.
  const re = new RegExp(
    `<p><strong>(${CALLOUT_KINDS.join('|')}):</strong>([\\s\\S]*?)</p>`,
    'g'
  );
  return html.replace(re, (_m, kind, body) => {
    const cls = `callout callout-${kind.toLowerCase()}`;
    return `<div class="${cls}"><p><strong>${kind}:</strong>${body}</p></div>`;
  });
}

// --- table-wrap post-processing ------------------------------------------

function wrapTables(html) {
  // Marked emits bare <table>; wrap each in a horizontal-scroll div.
  return html.replace(
    /<table>([\s\S]*?)<\/table>/g,
    '<div class="table-wrap"><table>$1</table></div>'
  );
}

// --- nav / TOC extraction ------------------------------------------------

function stripTags(s) { return s.replace(/<[^>]+>/g, ''); }
function decodeEntities(s) {
  return s.replace(/&amp;/g, '&').replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>').replace(/&quot;/g, '"');
}

function extractHeadings(html) {
  const re = /<(h2|h3)[^>]*\sid="([^"]+)"[^>]*>([\s\S]*?)<\/\1>/g;
  const out = [];
  let m;
  while ((m = re.exec(html)) !== null) {
    out.push({
      tag: m[1],
      id: m[2],
      text: decodeEntities(stripTags(m[3])).trim(),
    });
  }
  return out;
}

function buildSidebar(headings) {
  if (!headings.length) {
    return '<p style="color:var(--muted);font-size:0.85rem">(no sections)</p>';
  }
  return headings.map(h =>
    `<a class="nav-link ${h.tag}" href="#${h.id}">${escapeHtml(h.text)}</a>`
  ).join('\n      ');
}

function buildHeaderNav(headings) {
  // Top-level (h2) only, max 5 entries, no links if empty.
  const top = headings.filter(h => h.tag === 'h2').slice(0, 5);
  return top.map(h => `<a href="#${h.id}">${escapeHtml(h.text)}</a>`).join(' ');
}

// --- title detection ------------------------------------------------------

function detectTitle(html, fallback) {
  const m = /<h1[^>]*>([\s\S]*?)<\/h1>/.exec(html);
  if (m) return decodeEntities(stripTags(m[1])).trim();
  return fallback;
}

class Slugger {
  constructor() { this.seen = {}; }
  slug(text) {
    const base = text.toLowerCase()
      .replace(/<[^>]+>/g, '')
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
    let s = base || 'section';
    if (this.seen[s] !== undefined) {
      this.seen[s]++;
      s = `${s}-${this.seen[s]}`;
    } else {
      this.seen[s] = 0;
    }
    return s;
  }
}

// Replace a {{key}} placeholder in a template using function-form
// String#replace so the value can contain $&, $$, $', $` etc. without
// being interpreted as a back-reference pattern.
function stamp(template, key, value) {
  const re = new RegExp('\\{\\{' + key + '\\}\\}', 'g');
  return template.replace(re, () => value);
}

// --- main ----------------------------------------------------------------

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.input) {
    console.log(HELP);
    process.exit(args.help ? 0 : 1);
  }

  const inputPath = path.resolve(args.input);
  if (!fs.existsSync(inputPath)) {
    console.error(`error: input not found: ${inputPath}`);
    process.exit(1);
  }
  if (!THEMES[args.theme]) {
    console.error(`error: unknown --theme '${args.theme}'. Choices: ${Object.keys(THEMES).join(', ')}`);
    process.exit(1);
  }

  const md = fs.readFileSync(inputPath, 'utf-8');
  const outputPath = args.output
    ? path.resolve(args.output)
    : inputPath.replace(/\.(md|markdown)$/i, '.html');

  // Configure marked (v18+ token-object renderer API).
  // Custom renderer for code (mermaid pass-through, hljs highlighting) and
  // headings (stable ids for sidebar / print TOC anchors).
  const renderer = new marked.Renderer();

  renderer.code = function ({ text, lang }) {
    const language = (lang || '').trim().split(/\s+/)[0];
    if (language === 'mermaid') {
      return `<div class="mermaid-wrap"><div class="mermaid">${text}</div></div>\n`;
    }
    if (language && hljs.getLanguage(language)) {
      const highlighted = hljs.highlight(text, { language }).value;
      return `<pre><code class="hljs language-${language}">${highlighted}</code></pre>\n`;
    }
    const auto = hljs.highlightAuto(text).value;
    return `<pre><code class="hljs">${auto}</code></pre>\n`;
  };

  // Stable slug ids for h1/h2/h3.
  const slugger = new Slugger();

  renderer.heading = function ({ tokens, depth }) {
    const inner = this.parser.parseInline(tokens);
    const id = slugger.slug(stripTags(inner));
    return `<h${depth} id="${id}">${inner}</h${depth}>\n`;
  };

  marked.setOptions({ renderer, gfm: true, breaks: false });

  // Render
  let html = marked.parse(md);
  html = applyCallouts(html);
  html = wrapTables(html);

  // Extract nav targets from rendered HTML
  const headings = extractHeadings(html);
  const sidebar = buildSidebar(headings);
  const headerNav = buildHeaderNav(headings);

  const title = args.title || detectTitle(html, path.basename(inputPath));
  const subtitle = args.subtitle
    ? `<span class="subtitle">${escapeHtml(args.subtitle)}</span>`
    : '';

  const hasMermaid = args.mermaid && /<div class="mermaid">/.test(html);
  const mermaidScript = hasMermaid
    ? '<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>'
    : '';
  const mermaidInit = hasMermaid
    ? `mermaid.initialize({ startOnLoad: true, theme: 'base', themeVariables: { primaryColor: '${THEMES[args.theme].mid}', primaryTextColor: '#ffffff', primaryBorderColor: '${THEMES[args.theme].dark}', lineColor: '#64748b', fontFamily: 'inherit' } });`
    : '';

  // Stamp template — use function-form replace (via stamp()) so values
  // containing $&, $$, $', $` are not mis-interpreted as backref tokens.
  // The rendered markdown body is the obvious risk: code blocks easily
  // contain those sequences.
  const templatePath = path.join(__dirname, 'template.html');
  const template = fs.readFileSync(templatePath, 'utf-8');
  const palette = THEMES[args.theme];
  const filled = [
    ['title',            escapeHtml(title)],
    ['header_subtitle',  subtitle],
    ['header_nav',       headerNav],
    ['sidebar',          sidebar],
    ['content',          html],
    ['footer',           `<span>${escapeHtml(path.basename(inputPath))}</span>`],
    ['accent_dark',      palette.dark],
    ['accent_mid',       palette.mid],
    ['accent_light',     palette.light],
    ['mermaid_script',   mermaidScript],
    ['mermaid_init',     mermaidInit],
  ].reduce((tpl, [k, v]) => stamp(tpl, k, v), template);

  fs.writeFileSync(outputPath, filled, 'utf-8');
  process.stdout.write(`OUTPUT: ${outputPath}\n`);
  process.stdout.write(`SECTIONS: ${headings.length}\n`);
  process.stdout.write(`MERMAID: ${hasMermaid ? 'yes' : 'no'}\n`);
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

main();
