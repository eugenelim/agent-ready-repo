import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

// Mermaid renders in the browser, so no server-rendered artifact carries the
// diagram's layout or its sanitization posture, and nothing else in the
// repository can observe either. The one published fence —
// getting-started/three-loops — is therefore guarded here, at the only place
// the render configuration is stated.
//
// mermaid 12 made ELK the default layout engine. Rendering that fence under
// 12.0.0 with the options below, varying only `layout`, reports `elk` and a
// 344.92x1263 viewBox unstated against `dagre` and 339.81x1300 stated. These
// assertions are what make dropping the statement loud instead of silent.
//
// `look` and `theme` are deliberately NOT asserted. 12.0.0's release notes
// announce `neo` and `redux-color` as new defaults, but the same measurement
// reports `look: 'classic'` and `theme: 'default'` still in effect, so either
// assertion would pin the library's own default and fail for a reason that has
// nothing to do with this diagram.
const source = readFileSync(
  fileURLToPath(new URL('./Footer.astro', import.meta.url)),
  'utf8'
);

/**
 * `source` with every comment replaced by equivalent whitespace, and string
 * literals left intact.
 *
 * Blanking rather than deleting keeps offsets stable, so a failure still points
 * at the right place. This exists because an earlier version of this file
 * matched against raw text and two reviewers demonstrated the same defect: a
 * maintainer who deletes a key and leaves a note saying which key they deleted
 * satisfied every assertion here. A guard that its own explanatory comment can
 * satisfy is not a guard, and the comment block above names these exact keys.
 */
function withoutComments(text: string): string {
  let out = '';
  let i = 0;
  while (i < text.length) {
    const two = text.slice(i, i + 2);
    if (two === '//') {
      const end = text.indexOf('\n', i);
      const stop = end === -1 ? text.length : end;
      out += ' '.repeat(stop - i);
      i = stop;
      continue;
    }
    if (two === '/*') {
      const end = text.indexOf('*/', i + 2);
      const stop = end === -1 ? text.length : end + 2;
      out += text.slice(i, stop).replace(/[^\n]/g, ' ');
      i = stop;
      continue;
    }
    const ch = text[i];
    if (ch === '"' || ch === "'" || ch === '`') {
      // Copy the literal verbatim, so a brace or a `//` inside it is not read
      // as structure, and so an asserted value is still matchable.
      out += ch;
      i += 1;
      while (i < text.length && text[i] !== ch) {
        if (text[i] === '\\') {
          out += text.slice(i, i + 2);
          i += 2;
          continue;
        }
        out += text[i];
        i += 1;
      }
      out += text[i] ?? '';
      i += 1;
      continue;
    }
    out += ch;
    i += 1;
  }
  return out;
}

const CALL = 'mermaid.initialize(';

/**
 * The options object of the one `mermaid.initialize({ … })` call, taken from
 * comment-free source.
 *
 * Asserts the call is unique: mermaid applies the last `initialize` it is
 * given, so a second call anywhere in this file could override every key
 * guarded below while these assertions still passed.
 */
function initializeOptions(): string {
  const code = withoutComments(source);
  const sites: number[] = [];
  for (let at = code.indexOf(CALL); at !== -1; at = code.indexOf(CALL, at + 1)) {
    sites.push(at);
  }
  assert.equal(
    sites.length,
    1,
    `Footer.astro must contain exactly one ${CALL}…) call; found ${sites.length}. ` +
      'mermaid applies the last configuration it is given, so a second call ' +
      'would decide the diagram and leave the assertions below guarding nothing.'
  );
  const open = sites[0] + CALL.length;
  let depth = 0;
  for (let i = open; i < code.length; i += 1) {
    const ch = code[i];
    if (ch === '"' || ch === "'" || ch === '`') {
      i += 1;
      while (i < code.length && code[i] !== ch) i += code[i] === '\\' ? 2 : 1;
      continue;
    }
    if (ch === '{') depth += 1;
    else if (ch === '}') {
      depth -= 1;
      if (depth === 0) return code.slice(open, i + 1);
    }
  }
  return assert.fail('mermaid.initialize({ … }) is unbalanced in Footer.astro');
}

test('mermaid render config states the layout engine', () => {
  assert.match(
    initializeOptions(),
    /\blayout:\s*'dagre'/,
    "mermaid.initialize must state layout: 'dagre'. Unstated, mermaid 12.0.0 " +
      'lays the published getting-started/three-loops flowchart out with ELK ' +
      'instead of dagre — measured as a 344.92x1263 viewBox against ' +
      "339.81x1300 — and no gate reads a rendered diagram's geometry."
  );
});

test('mermaid render config keeps strict security level', () => {
  assert.match(
    initializeOptions(),
    /\bsecurityLevel:\s*'strict'/,
    "mermaid.initialize must keep securityLevel: 'strict'. The fence is " +
      'repository-authored markdown that remarkMermaid encodes into a ' +
      '`data-mermaid` attribute at build time, and the rendered SVG is assigned ' +
      'with innerHTML — so this is the control that keeps a fence from emitting ' +
      'markup and handlers, not a live untrusted-input boundary.'
  );
});
