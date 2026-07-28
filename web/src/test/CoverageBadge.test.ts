// @vitest-environment node
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { describe, expect, it } from 'vitest';
import CoverageBadge from '../components/primitives/CoverageBadge.astro';

async function render(props: Record<string, unknown>): Promise<string> {
  const container = await AstroContainer.create();
  return container.renderToString(CoverageBadge, { props });
}

const states = [
  { coverage: 'complete',          expectedText: 'Complete result' },
  { coverage: 'filtered',          expectedText: 'Filtered result' },
  { coverage: 'partial',           expectedText: 'Partial result' },
  { coverage: 'capped',            expectedText: 'Capped result' },
  { coverage: 'permission-limited',expectedText: 'Permission-limited result' },
] as const;

describe('CoverageBadge', () => {
  it.each(states)('$coverage renders visible explanation text', async ({ coverage, expectedText }) => {
    const html = await render({ coverage });
    expect(html).toContain(expectedText);
  });

  it('permission-limited carries an accessible description', async () => {
    const html = await render({ coverage: 'permission-limited' });
    const dom = new JSDOM(html);
    // Either the label text or aria-label attribute carries the explanation
    const hasDescription =
      html.includes('access restrictions') ||
      !!dom.window.document.querySelector('[aria-label*="access restrictions"]');
    expect(hasDescription).toBe(true);
  });

  it('detail prop overrides default explanation', async () => {
    const html = await render({ coverage: 'filtered', detail: 'Filtered to last 7 days' });
    expect(html).toContain('Filtered to last 7 days');
  });
});
