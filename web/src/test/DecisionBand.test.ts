// @vitest-environment node
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { describe, expect, it } from 'vitest';
import DecisionBand from '../components/primitives/DecisionBand.astro';

async function render(props: Record<string, unknown>): Promise<string> {
  const container = await AstroContainer.create();
  return container.renderToString(DecisionBand, { props });
}

describe('DecisionBand', () => {
  it('primary action is the first focusable element inside the band', async () => {
    const html = await render({
      summary: 'Merge branch?',
      consequence: 'This will merge 12 commits into main.',
      primaryAction: { label: 'Merge now', href: '#merge' },
      secondaryAction: { label: 'Cancel', href: '#cancel' },
    });
    const dom = new JSDOM(html);
    const actions = dom.window.document.querySelectorAll('.decision-band__action');
    expect(actions[0]?.textContent?.trim()).toContain('Merge now');
  });

  it('renders summary, consequence, and primary action', async () => {
    const html = await render({
      summary: 'Deploy to production',
      consequence: 'Affects 50,000 users.',
      primaryAction: { label: 'Deploy', href: '#deploy' },
    });
    expect(html).toContain('Deploy to production');
    expect(html).toContain('Affects 50,000 users.');
    expect(html).toContain('Deploy');
  });

  it('renders optional scope text when provided', async () => {
    const html = await render({
      summary: 'Overwrite config',
      consequence: 'Config will be replaced.',
      primaryAction: { label: 'Overwrite', href: '#' },
      scope: 'Read-only fields are unchanged',
    });
    expect(html).toContain('Read-only fields are unchanged');
  });
});
