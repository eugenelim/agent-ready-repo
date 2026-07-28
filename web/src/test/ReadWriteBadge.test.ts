// @vitest-environment node
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { describe, expect, it } from 'vitest';
import ReadWriteBadge from '../components/primitives/ReadWriteBadge.astro';

async function render(props: Record<string, unknown>): Promise<string> {
  const container = await AstroContainer.create();
  return container.renderToString(ReadWriteBadge, { props });
}

const modes = [
  { mode: 'read-only',       expectedText: 'Read only' },
  { mode: 'draft',           expectedText: 'Draft' },
  { mode: 'proposed-write',  expectedText: 'Review before writing' },
  { mode: 'confirmed-write', expectedText: 'Writing confirmed' },
  { mode: 'publish',         expectedText: 'Publishing now' },
  { mode: 'destructive',     expectedText: 'Destructive' },
] as const;

describe('ReadWriteBadge', () => {
  it.each(modes)('$mode renders visible consequence text containing "$expectedText"', async ({ mode, expectedText }) => {
    const html = await render({ mode });
    expect(html).toContain(expectedText);
  });

  it('destructive mode uses danger state token', async () => {
    const html = await render({ mode: 'destructive' });
    const dom = new JSDOM(html);
    const chip = dom.window.document.querySelector('[data-state="destructive"]');
    expect(chip).not.toBeNull();
  });

  it('data-mode attribute matches the mode prop', async () => {
    const html = await render({ mode: 'proposed-write' });
    const dom = new JSDOM(html);
    const badge = dom.window.document.querySelector('[data-mode="proposed-write"]');
    expect(badge).not.toBeNull();
  });
});
