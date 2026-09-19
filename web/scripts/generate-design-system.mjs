/**
 * Generate §1 "Color tokens" of `web/src/design-system.md` from
 * `web/src/styles/tokens.css`.
 *
 * WHY THIS EXISTS
 *
 * §1 held about forty hex and rgba literals, hand-typed. The palette changed
 * on 2026-09-18 and every one of them became wrong in the same instant. The
 * document's own first line already said "all values are derived from
 * tokens.css — the implementation authority", and its header carried a
 * standing warning not to trust its own tables. A reference whose header tells
 * you not to read it is not a reference.
 *
 * Re-typing the forty literals would have restored it until the next palette
 * change and no further, so §1 is a PROJECTION now: every cell below is read
 * out of `tokens.css`, and the section is regenerated rather than edited.
 *
 * HOW IT DIFFERS FROM THE OTHER PROJECTIONS, deliberately. The renderer inputs
 * `tools/build-site.py --renderer-inputs` writes (`web/src/lib/*.generated.json`)
 * are gitignored and rebuilt by an npm `pre*` hook, because only the build
 * reads them. `design-system.md` is read by people, in the repository, without
 * a build — so it stays committed, and the guarantee is enforced from the
 * other end: `src/test/design-system-projection.test.ts` fails when the
 * committed §1 differs from what this script would write. Drift cannot be
 * committed quietly; it can only be committed by also editing the generator or
 * deleting the test, both of which are visible in review.
 *
 * USAGE
 *   node scripts/generate-design-system.mjs           # rewrite §1 in place
 *   node scripts/generate-design-system.mjs --check   # exit 1 if it would change
 *
 * SCOPE. §1 only — the colour tokens. §2 (typography) and §3 (spacing, radius,
 * motion, z-index) are untouched: they were not the stale tables, and widening
 * a generator past the defect it was written for is how a generator acquires
 * cases nobody checks.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
export const TOKENS_CSS = join(HERE, '../src/styles/tokens.css');
export const DESIGN_SYSTEM_MD = join(HERE, '../src/design-system.md');

const SECTION_START = '## 1. Color tokens';
const SECTION_END = '## 2. Typography';

/**
 * A `--token: value;` declaration, with whatever the author wrote about it.
 *
 * `group` is the `/* ── … ── *​/` banner the declaration sits under. Those
 * banners are the section structure tokens.css already has, so the generated
 * document inherits the source's own organisation instead of inventing one
 * that can disagree with it.
 */
function parseTokens(css) {
  const tokens = [];
  const overrides = [];
  let group = null;

  // Brace tracking runs on a COMMENT-STRIPPED copy, and the copy keeps every
  // newline so line numbers and the raw-line scan below stay in step. Two
  // things made a naive tracker wrong here, and both are in this file:
  //   - one-line rules. `@media (min-width: 768px) { :root { ... } }` is
  //     written with the inner rule opened and closed on ONE line. A tracker
  //     that returns after seeing `{` never sees the matching `}`, so depth
  //     ratchets up and the selector sticks. That is not a hypothetical: it
  //     made `:where(.section--dark, .footer)` at the foot of the file parse
  //     as a `:root` DEFINITION, which overwrote `--ds-focus-ring` and
  //     printed the paper ring as #dcd8ce — 1.31:1 on paper, the precise
  //     failure tokens.css re-derives the ring to prevent. The generated
  //     table stated the defect as the design.
  //   - at-rules. `@media` is pushed like any block so its brace balances,
  //     but a `:root` nested inside it is still a definition of the token
  //     for that media query, not the base one.
  const stripped = css.replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '));
  const strippedLines = stripped.split('\n');
  const stack = [];

  css.split('\n').forEach((raw, i) => {
    const banner = raw.match(/\/\*\s*──\s*(.+?)(?:\s*──+.*)?$/);
    if (banner) {
      // Keep only the first clause: several banners continue into a paragraph
      // of reasoning, which belongs in tokens.css and not in a table heading.
      group = banner[1]
        .replace(/\s*[─*/]+\s*$/, '')
        .split(/\.\s/)[0]
        .trim()
        .replace(/[.,:;]+$/, '');
    }

    // The rule in force where this line STARTS.
    const selector = stack.length > 0 ? stack[stack.length - 1] : null;

    const decl = raw.match(/^\s*(--[\w-]+)\s*:\s*([^;]+);\s*(?:\/\*\s*(.*?)\s*\*\/)?/);
    if (decl) {
      const record = {
        name: decl[1],
        raw: decl[2].trim(),
        note: (decl[3] ?? '').trim(),
        group,
        selector,
      };
      if (selector === ':root') tokens.push(record);
      else overrides.push(record);
    }

    // Then advance the stack across every brace on the line, in order.
    let pre = '';
    for (const ch of strippedLines[i] ?? '') {
      if (ch === '{') {
        stack.push(pre.trim());
        pre = '';
      } else if (ch === '}') {
        stack.pop();
        pre = '';
      } else if (ch === ';') {
        pre = '';
      } else {
        pre += ch;
      }
    }
  });

  return { tokens, overrides };
}

/** Follow `var(--x)` to the literal it ends at. */
function resolve(name, byName, seen = new Set()) {
  const t = byName.get(name);
  if (!t || seen.has(name)) return null;
  seen.add(name);
  const ref = t.raw.match(/^var\(\s*(--[\w-]+)\s*\)$/);
  return ref ? resolve(ref[1], byName, seen) : t.raw;
}

const isColour = (v) => v !== null && /^(#[0-9a-fA-F]{3,8}|rgba?\()/.test(v);

/** A trailing comment, trimmed to one clause so it fits a table cell. */
function cell(note) {
  if (!note) return '—';
  const first = note.split(/\.\s|\s+—\s+See\b/)[0].trim().replace(/\|/g, '\\|');
  return first.length > 96 ? `${first.slice(0, 93)}…` : first;
}

export function renderSection(css) {
  const { tokens, overrides } = parseTokens(css);
  const byName = new Map(tokens.map((t) => [t.name, t]));
  const colours = tokens.filter((t) => isColour(resolve(t.name, byName)));

  const lines = [];
  lines.push(SECTION_START, '');
  lines.push(
    '<!-- GENERATED FROM web/src/styles/tokens.css — DO NOT EDIT BY HAND.',
    '     Regenerate:  node scripts/generate-design-system.mjs',
    '     Guarded by:  src/test/design-system-projection.test.ts',
    '',
    '     Every value, mapping and note below is read out of tokens.css. Change',
    '     a token there and regenerate; editing this section instead produces',
    '     exactly the drift that made these tables wrong for a whole palette',
    '     change. Reasoning about a token belongs in tokens.css beside it, where',
    '     this generator can carry it forward. -->',
    ''
  );
  lines.push(
    'Three-tier architecture: **Tier 1 primitives** (`--prim-*`) define raw scale values.',
    '**Tier 2 semantics** (`--ds-*`) map primitives to roles. **Component CSS** references',
    'semantic tokens only — never primitives directly.',
    '',
    `This section lists the ${colours.length} colour-valued tokens in \`tokens.css\`.`,
    'Non-colour tokens are in §2 and §3.',
    ''
  );

  const tier1 = colours.filter((t) => t.name.startsWith('--prim-'));
  const tier2 = colours.filter((t) => !t.name.startsWith('--prim-'));

  lines.push('### Tier 1 — Primitive color scale', '');
  for (const group of [...new Set(tier1.map((t) => t.group))]) {
    const rows = tier1.filter((t) => t.group === group);
    if (group && [...new Set(tier1.map((t) => t.group))].length > 1) {
      lines.push(`**${group}**`, '');
    }
    lines.push('| Token | Value | Note (from `tokens.css`) |', '| --- | --- | --- |');
    for (const t of rows) lines.push(`| \`${t.name}\` | \`${t.raw}\` | ${cell(t.note)} |`);
    lines.push('');
  }

  lines.push('### Tier 2 — Semantic color tokens', '');
  lines.push(
    'A semantic token names a ROLE. "Maps to" is what `tokens.css` declares;',
    '"Resolves to" is the literal that mapping ends at, followed through every',
    '`var()` hop — so a re-pointed primitive shows up here without anyone',
    'retyping a hex.',
    ''
  );
  for (const group of [...new Set(tier2.map((t) => t.group))]) {
    const rows = tier2.filter((t) => t.group === group);
    if (group) lines.push(`**${group}**`, '');
    lines.push(
      '| Token | Maps to | Resolves to | Note (from `tokens.css`) |',
      '| --- | --- | --- | --- |'
    );
    for (const t of rows) {
      const ref = t.raw.match(/^var\(\s*(--[\w-]+)\s*\)$/);
      lines.push(
        `| \`${t.name}\` | ${ref ? `\`${ref[1]}\`` : '—'} | \`${resolve(t.name, byName)}\` | ${cell(t.note)} |`
      );
    }
    lines.push('');
  }

  // Scoped re-pointings. These are NOT definitions and are listed apart from
  // the tables above so a reader cannot mistake an override for the token's
  // value. The prose this replaces named eleven carriers; the real list had
  // been down to two for a while, which is the same drift in a different
  // grammar, so the carriers are read from the selector rather than retold.
  const colourOverrides = overrides.filter((o) => isColour(resolve(o.name, byName)) ||
    /^var\(/.test(o.raw));
  if (colourOverrides.length > 0) {
    lines.push('### Scoped overrides', '');
    lines.push(
      'A token re-pointed for one carrier, in a rule that is not `:root`. The',
      'value above is what the token is everywhere else.',
      ''
    );
    lines.push('| Token | Carrier (selector) | Maps to |', '| --- | --- | --- |');
    for (const o of colourOverrides) {
      const ref = o.raw.match(/^var\(\s*(--[\w-]+)\s*\)$/);
      lines.push(`| \`${o.name}\` | \`${o.selector}\` | ${ref ? `\`${ref[1]}\`` : `\`${o.raw}\``} |`);
    }
    lines.push('');
  }

  return `${lines.join('\n')}\n`;
}

export function projectDocument(md, css) {
  const start = md.indexOf(SECTION_START);
  const end = md.indexOf(SECTION_END);
  if (start === -1 || end === -1 || end < start) {
    throw new Error(
      `design-system.md: cannot find "${SECTION_START}" .. "${SECTION_END}". ` +
        'The generator projects exactly that span; renaming either heading ' +
        'must be done here too.'
    );
  }
  return md.slice(0, start) + renderSection(css) + md.slice(end);
}

// Entry point. Importing this module runs nothing.
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const md = readFileSync(DESIGN_SYSTEM_MD, 'utf8');
  const next = projectDocument(md, readFileSync(TOKENS_CSS, 'utf8'));
  if (process.argv.includes('--check')) {
    if (next !== md) {
      console.error(
        'design-system.md §1 is out of date with tokens.css.\n' +
          'Run: node scripts/generate-design-system.mjs'
      );
      process.exit(1);
    }
    console.log('design-system.md §1 matches tokens.css.');
  } else {
    writeFileSync(DESIGN_SYSTEM_MD, next);
    console.log(`Wrote §1 of ${DESIGN_SYSTEM_MD} from tokens.css.`);
  }
}
