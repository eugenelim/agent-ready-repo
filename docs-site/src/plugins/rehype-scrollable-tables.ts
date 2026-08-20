import { visit } from 'unist-util-visit';

/**
 * Wrap every markdown table in a keyboard-focusable scroll region.
 *
 * A table wider than the prose column scrolls horizontally, and a scroll
 * container that cannot take focus is unreachable by keyboard — axe reports it
 * as `scrollable-region-focusable` (serious). Wrapping at build time keeps the
 * fix out of the runtime: no client JS is involved.
 *
 * Starlight's own base rule makes the `<table>` itself `display: block;
 * overflow: auto`, so the paired CSS in `starlight.css` hands the scroll to
 * this wrapper and returns the table to `display: table`.
 *
 * Extracted from `astro.config.ts` to keep the config declarative. Two layers of
 * coverage, both load-bearing: the focused hast-fixture suite beside this file
 * (`npm run test:plugins --prefix docs-site`) pins the edge cases and makes each
 * accessibility attribute mutation-sensitive, and the built-output assertion in
 * `web/src/test/rendered-output.test.ts` checks every table on every generated
 * page — which a fixture cannot. Neither replaces the other.
 */

interface HastNode {
  type: string;
  tagName?: string;
  properties?: Record<string, unknown>;
  children?: HastNode[];
}

/** True when `node` is the wrapper this plugin emits. */
function isWrapper(node: HastNode | undefined): boolean {
  if (!node || node.type !== 'element' || node.tagName !== 'div') return false;
  const className = node.properties?.className;
  return Array.isArray(className) && className.includes('table-scroll');
}

/**
 * The nearest preceding heading, used to name the region — so a screen-reader
 * landmark list distinguishes the six regions on a reference page instead of
 * reading "Table (scrollable)" six times.
 */
function headingFor(siblings: HastNode[], index: number): string | null {
  for (let i = index - 1; i >= 0; i -= 1) {
    const node = siblings[i];
    if (node?.type !== 'element') continue;
    if (!/^h[1-6]$/.test(node.tagName ?? '')) continue;
    const text = collectText(node).trim();
    if (text) return text;
  }
  return null;
}

function collectText(node: HastNode): string {
  if (node.type === 'text') return (node as unknown as { value: string }).value ?? '';
  return (node.children ?? []).map(collectText).join('');
}

export function rehypeScrollableTables() {
  return (tree: HastNode) => {
    // Per-page tally so sibling tables under one heading get distinct accessible
    // names. Identical `role="region"` labels are their own axe finding
    // (`landmark-unique`), and several reference guides carry four tables under
    // a single heading.
    const used = new Map<string, number>();

    visit(tree, 'element', (node: HastNode, index: number | undefined, parent: HastNode | undefined) => {
      if (node.tagName !== 'table') return;
      // `index == null` covers both null and undefined — unist-util-visit's
      // typings return undefined for a root-level node, and `=== null` alone
      // would let that through and write to `children[undefined]`.
      if (!parent || index == null || !parent.children) return;
      if (isWrapper(parent)) return;

      const heading = headingFor(parent.children, index);
      const base = heading ? `Table: ${heading}` : 'Table';
      const seen = (used.get(base) ?? 0) + 1;
      used.set(base, seen);
      const label = `${base}${seen > 1 ? ` (${seen})` : ''} (scrollable)`;

      parent.children[index] = {
        type: 'element',
        tagName: 'div',
        properties: {
          className: ['table-scroll'],
          tabIndex: 0,
          role: 'region',
          'aria-label': label,
        },
        children: [node],
      };
    });
  };
}
