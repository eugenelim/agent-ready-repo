// @vitest-environment node
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { describe, expect, it } from 'vitest';
import CopyButton from '../components/primitives/CopyButton.astro';

async function render(props: Record<string, unknown>): Promise<string> {
  const container = await AstroContainer.create();
  return container.renderToString(CopyButton, { props });
}

describe('CopyButton', () => {
  it('renders as a <button> element', async () => {
    const html = await render({ content: 'hello' });
    const dom = new JSDOM(html);
    const btn = dom.window.document.querySelector('button.copy-btn');
    expect(btn).not.toBeNull();
  });

  it('has an accessible name (aria-label)', async () => {
    const html = await render({ content: 'cmd', label: 'Copy command' });
    const dom = new JSDOM(html);
    const btn = dom.window.document.querySelector('button.copy-btn');
    expect(btn?.getAttribute('aria-label')).toBe('Copy command');
  });

  it('includes a live-region element for success announcement', async () => {
    const html = await render({ content: 'cmd' });
    const dom = new JSDOM(html);
    const live = dom.window.document.querySelector('[aria-live="polite"]');
    expect(live).not.toBeNull();
  });

  it('stores content in data-copy-content attribute', async () => {
    const html = await render({ content: 'npm install vitest' });
    const dom = new JSDOM(html);
    const btn = dom.window.document.querySelector('button.copy-btn') as Element;
    expect(btn.getAttribute('data-copy-content')).toBe('npm install vitest');
  });
});
