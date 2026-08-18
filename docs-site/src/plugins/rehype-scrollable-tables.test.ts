// STUB: AC5/AC6 — red stub materialised at PLAN per CONVENTIONS § Stub → EXECUTE handoff.
//
// Behavioural coverage for `rehypeScrollableTables`, run by Node's built-in test
// runner under the `engines` floor `docs-site/package.json` declares. No test
// dependency is added: `node:test` and `node:assert` are built in, and the plugin's
// only import (`unist-util-visit`) is already a declared runtime dependency.
//
// The import carries an explicit `.ts` extension. `astro.config.ts` imports this
// plugin extensionless, which Vite resolves and Node does not — copying that form
// here yields ERR_MODULE_NOT_FOUND.
//
// These are hast fixtures, not rendered pages. The emitted-output assertion in
// `web/src/test/rendered-output.test.ts` remains the integration layer: it checks
// every table on every generated page, which a fixture cannot. This file exists to
// make the transform's edge cases cheap to assert and its accessibility attributes
// mutation-sensitive — the built-output test cannot tell you *why* a wrapper is
// missing, only that one is.

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { rehypeScrollableTables } from './rehype-scrollable-tables.ts';

interface Node {
  type: string;
  tagName?: string;
  properties?: Record<string, unknown>;
  children?: Node[];
  value?: string;
}

const el = (tagName: string, children: Node[] = [], properties: Record<string, unknown> = {}): Node =>
  ({ type: 'element', tagName, properties, children });
const text = (value: string): Node => ({ type: 'text', value });
const table = (): Node => el('table', [el('tbody', [el('tr', [el('td', [text('cell')])])])]);
const root = (children: Node[]): Node => ({ type: 'root', children });

/** Run the transform on a tree, in place, and hand the tree back. */
function transform(tree: Node): Node {
  rehypeScrollableTables()(tree);
  return tree;
}

const wrapper = (node: Node | undefined) => {
  assert.ok(node, 'expected a node');
  assert.equal(node.type, 'element');
  assert.equal(node.tagName, 'div');
  return node;
};

// --------------------------------------------------------------------------
// Wrapping — the base contract (AC5, AC6)
// --------------------------------------------------------------------------

test('wraps an unwrapped table in one focusable labelled region', () => {
  const tree = transform(root([table()]));
  const div = wrapper(tree.children?.[0]);
  // Each attribute asserted separately so a mutation to any one of them fails a
  // named case rather than collapsing into a single "wrapper wrong" failure.
  assert.deepEqual(div.properties?.className, ['table-scroll']);
  assert.equal(div.properties?.tabIndex, 0);
  assert.equal(div.properties?.role, 'region');
  assert.equal(div.properties?.['aria-label'], 'Table (scrollable)');
  assert.equal(div.children?.length, 1);
  assert.equal(div.children?.[0]?.tagName, 'table');
});

test('wraps a table nested inside a blockquote', () => {
  // The non-root, non-wrapper parent case. `headingFor` also has to work across
  // that container boundary rather than only at root level.
  const tree = transform(root([el('blockquote', [table()])]));
  const quote = tree.children?.[0];
  const div = wrapper(quote?.children?.[0]);
  assert.deepEqual(div.properties?.className, ['table-scroll']);
  assert.equal(div.children?.[0]?.tagName, 'table');
});

test('wraps a table nested inside an aside', () => {
  const tree = transform(root([el('aside', [table()])]));
  const div = wrapper(tree.children?.[0]?.children?.[0]);
  assert.equal(div.properties?.role, 'region');
});

// --------------------------------------------------------------------------
// Idempotence and the leave-alone cases (AC5, AC6)
// --------------------------------------------------------------------------

test('leaves an existing wrapper unchanged', () => {
  const existing = el('div', [table()], { className: ['table-scroll'], tabIndex: 0, role: 'region', 'aria-label': 'kept (scrollable)' });
  const tree = transform(root([existing]));
  const div = wrapper(tree.children?.[0]);
  assert.equal(div.properties?.['aria-label'], 'kept (scrollable)', 'label must not be regenerated');
  assert.equal(div.children?.[0]?.tagName, 'table', 'must not nest a second wrapper');
});

test('running the transform twice is a no-op the second time', () => {
  const tree = transform(root([table()]));
  const once = JSON.stringify(tree);
  transform(tree);
  assert.equal(JSON.stringify(tree), once, 'second pass must change nothing');
});

test('leaves a root-level table with no parent or index unchanged', () => {
  // `visit` reaches a root node with BOTH parent and index undefined, so the guard's
  // `!parent` and `index == null` clauses are individually redundant here: deleting
  // either one alone leaves this test green (measured), because the other still
  // returns early. So this case is covered but no single-clause mutation of that
  // guard is observable — stated rather than papered over with a fixture that cannot
  // exist. The third clause, `!parent.children`, is unreachable from outside at all:
  // `visit` only reaches a node *via* `parent.children`.
  //
  // AC6's five named mutations — wrapper class, tabIndex, role, accessible label,
  // idempotence — are each independently caught; this guard is not among them.
  const tree = transform(table());
  assert.equal(tree.tagName, 'table', 'the table itself must survive untouched');
  assert.equal(tree.children?.[0]?.tagName, 'tbody');
});

// --------------------------------------------------------------------------
// Labelling (AC5, AC6)
// --------------------------------------------------------------------------

test('derives the label from the nearest preceding heading', () => {
  const tree = transform(root([el('h2', [text('Exit codes')]), table()]));
  const div = wrapper(tree.children?.[1]);
  assert.equal(div.properties?.['aria-label'], 'Table: Exit codes (scrollable)');
});

test('derives the label from nested heading text, not just direct children', () => {
  const tree = transform(root([
    el('h3', [el('code', [text('make ci')]), text(' targets')]),
    table(),
  ]));
  const div = wrapper(tree.children?.[1]);
  assert.equal(div.properties?.['aria-label'], 'Table: make ci targets (scrollable)');
});

test('skips a blank heading and uses the nearest non-empty one', () => {
  const tree = transform(root([el('h2', [text('Real')]), el('h3', []), table()]));
  const div = wrapper(tree.children?.[2]);
  assert.equal(div.properties?.['aria-label'], 'Table: Real (scrollable)');
});

test('disambiguates repeated labels under one heading', () => {
  const tree = transform(root([el('h2', [text('Fields')]), table(), table(), table()]));
  const labels = (tree.children ?? []).slice(1).map((n) => n.properties?.['aria-label']);
  assert.deepEqual(labels, [
    'Table: Fields (scrollable)',
    'Table: Fields (2) (scrollable)',
    'Table: Fields (3) (scrollable)',
  ], 'identical region labels are their own axe finding (landmark-unique)');
});

test('resets the label counter for each transformed document', () => {
  // The counter lives inside the returned transformer, so a fresh document starts
  // at one. If it were module-level, the second document would begin at (2) — and
  // every page after the first would carry wrong labels.
  const plugin = rehypeScrollableTables();
  const first = root([el('h2', [text('Fields')]), table()]);
  const second = root([el('h2', [text('Fields')]), table()]);
  plugin(first);
  plugin(second);
  assert.equal(first.children?.[1]?.properties?.['aria-label'], 'Table: Fields (scrollable)');
  assert.equal(second.children?.[1]?.properties?.['aria-label'], 'Table: Fields (scrollable)',
    'a new document must not inherit the previous document\'s tally');
});
