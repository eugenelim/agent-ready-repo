import { visit } from 'unist-util-visit';

/**
 * Tag each turn of a guidebook chat exchange with its speaker.
 *
 * A guidebook step shows what the reader types and what the agent replies. Both
 * are blockquotes, so before this they rendered as one undifferentiated slab
 * with the same left rule — a reader scanning the page could not see the turn
 * boundary, which is the only thing that makes the block a conversation rather
 * than a quotation.
 *
 * CSS cannot select on text, and the source has to stay plain Markdown because
 * `guides/` renders on GitHub as well as here. So the speaker is detected at
 * build time from the `**You:**` / `**Agent:**` lead the step contract already
 * requires, and becomes a class the stylesheet can reach.
 *
 * Marks the blockquote `chat-exchange` and each paragraph `chat-turn` plus
 * `chat-turn--you` or `chat-turn--agent`. A blockquote with no recognised lead
 * is left exactly as it was: ordinary quotations must not pick up chat styling.
 */

interface HastNode {
  type: string;
  tagName?: string;
  value?: string;
  properties?: Record<string, unknown>;
  children?: HastNode[];
}

/** The speaker a paragraph opens with, or null when it names none. */
function speaker(paragraph: HastNode): 'you' | 'agent' | null {
  const first = paragraph.children?.find((child) => child.type === 'element');
  if (!first || first.tagName !== 'strong') return null;
  const label = (first.children ?? [])
    .map((child) => (child.type === 'text' ? child.value ?? '' : ''))
    .join('')
    .trim()
    .replace(/:$/, '')
    .toLowerCase();
  if (label === 'you') return 'you';
  if (label === 'agent') return 'agent';
  return null;
}

function addClass(node: HastNode, ...names: string[]): void {
  const properties = (node.properties ??= {});
  const existing = properties.className;
  const classes = Array.isArray(existing) ? [...existing] : existing ? [String(existing)] : [];
  for (const name of names) if (!classes.includes(name)) classes.push(name);
  properties.className = classes;
}

export function rehypeChatTurns() {
  return (tree: HastNode): void => {
    visit(tree, 'element', (node: HastNode) => {
      if (node.tagName !== 'blockquote') return;
      const paragraphs = (node.children ?? []).filter(
        (child) => child.type === 'element' && child.tagName === 'p',
      );
      const turns = paragraphs.map((paragraph) => ({ paragraph, who: speaker(paragraph) }));
      // At least one recognised speaker, or this is an ordinary quotation.
      if (!turns.some((turn) => turn.who)) return;
      addClass(node, 'chat-exchange');
      for (const { paragraph, who } of turns) {
        if (who) addClass(paragraph, 'chat-turn', `chat-turn--${who}`);
      }
    });
  };
}
