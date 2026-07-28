// @vitest-environment node
// Container API requires Node's native TextEncoder (jsdom breaks esbuild's invariant).
// DOM assertions use JSDOM directly.
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { describe, expect, it } from 'vitest';
import axe from 'axe-core';
import StatusChip from '../components/primitives/StatusChip.astro';

async function render(props: Record<string, unknown>): Promise<string> {
  const container = await AstroContainer.create();
  return container.renderToString(StatusChip, { props });
}

function query(html: string): Element {
  const dom = new JSDOM(html);
  const chip = dom.window.document.querySelector('.status-chip');
  if (!chip) throw new Error('StatusChip element not found in: ' + html);
  return chip;
}

describe('StatusChip', () => {
  it('renders label as visible text', async () => {
    const html = await render({ label: 'user' });
    expect(html).toContain('user');
  });

  it('carries role="status" and aria-live when live=true', async () => {
    const html = await render({ label: 'uploading', live: true });
    const chip = query(html);
    expect(chip.getAttribute('role')).toBe('status');
    expect(chip.getAttribute('aria-live')).toBe('polite');
  });

  it('omits role and aria-live by default', async () => {
    const html = await render({ label: 'repo' });
    const chip = query(html);
    expect(chip.getAttribute('role')).toBeNull();
    expect(chip.getAttribute('aria-live')).toBeNull();
  });

  it('sets data-state attribute from state prop', async () => {
    const html = await render({ label: 'complete', state: 'success' });
    const chip = query(html);
    expect(chip.getAttribute('data-state')).toBe('success');
  });

  it('omits data-state when state prop is not provided', async () => {
    const html = await render({ label: 'user' });
    const chip = query(html);
    expect(chip.getAttribute('data-state')).toBeNull();
  });

  it('passes axe-core with no violations', async () => {
    const html = await render({ label: 'repo' });
    // Wrap in <main> so axe's `region` rule (landmark scope) is satisfied.
    const dom = new JSDOM(`<main>${html}</main>`);
    const main = dom.window.document.querySelector('main') as Element;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const results = await axe.run(main as any);
    expect(results.violations).toHaveLength(0);
  });
});
