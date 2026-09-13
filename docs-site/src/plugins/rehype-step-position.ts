import { visit } from 'unist-util-visit';

/**
 * Style a guidebook step's opening position line.
 *
 * Every step opens with `**Step 3 of 5 — Establish design intent**`. It is the
 * first thing on the page and the reader's only in-body orientation, and it
 * rendered as an ordinary bold paragraph — indistinguishable from the fifteen
 * other bold labels below it.
 *
 * Detected at build time rather than authored as markup, because `guides/`
 * renders on GitHub too, where it must stay a plain bold line. The source is
 * the same declaration the sidebar numbering and the right-hand rail read, so
 * all three derive from one statement.
 *
 * Splits it into the position and the title so the stylesheet can treat them
 * differently: the position is an eyebrow, the title is the heading a reader
 * arriving from search needs to see.
 */

interface HastNode {
  type: string;
  tagName?: string;
  value?: string;
  properties?: Record<string, unknown>;
  children?: HastNode[];
}

const POSITION = /^Step (\d+) of (\d+) — (.+)$/;

export function rehypeStepPosition() {
  return (tree: HastNode): void => {
    let done = false;
    visit(tree, 'element', (node: HastNode) => {
      // First match only: a later paragraph quoting the same form is prose.
      if (done || node.tagName !== 'p') return;
      const only = (node.children ?? []).filter(
        (child) => child.type !== 'text' || (child.value ?? '').trim() !== '',
      );
      if (only.length !== 1 || only[0].tagName !== 'strong') return;
      const text = (only[0].children ?? [])
        .map((child) => (child.type === 'text' ? (child.value ?? '') : ''))
        .join('');
      const match = POSITION.exec(text.trim());
      if (!match) return;
      done = true;
      const [, step, steps, title] = match;
      node.properties = { ...(node.properties ?? {}), className: ['step-position'] };
      node.children = [
        {
          type: 'element',
          tagName: 'span',
          properties: { className: ['step-position__count'] },
          children: [{ type: 'text', value: `Step ${step} of ${steps}` }],
        },
        {
          type: 'element',
          tagName: 'span',
          properties: { className: ['step-position__title'] },
          children: [{ type: 'text', value: title }],
        },
      ];
    });
  };
}
