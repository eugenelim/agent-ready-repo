// @vitest-environment node
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { describe, expect, it } from 'vitest';
import WriteConfirmation from '../components/primitives/WriteConfirmation.astro';

async function render(props: Record<string, unknown>): Promise<string> {
  const container = await AstroContainer.create();
  return container.renderToString(WriteConfirmation, { props });
}

const baseProps = {
  objects: ['Record A', 'Record B'],
  fields: [{ label: 'Status', value: 'Active' }, { label: 'Owner', value: 'User X' }],
  writeCount: 2,
  consequence: 'This will update both records immediately.',
  onConfirm: '/confirm',
  onCancel: '/cancel',
};

describe('WriteConfirmation', () => {
  it('renders as a region landmark', async () => {
    const html = await render(baseProps);
    const dom = new JSDOM(html);
    const region = dom.window.document.querySelector('[role="region"]');
    expect(region).not.toBeNull();
  });

  it('cancel link appears before confirm link in the DOM', async () => {
    const html = await render(baseProps);
    const dom = new JSDOM(html);
    const links = Array.from(dom.window.document.querySelectorAll('a'));
    const cancelIdx = links.findIndex((a) => a.classList.contains('write-confirmation__cancel'));
    const confirmIdx = links.findIndex((a) => a.classList.contains('write-confirmation__confirm'));
    expect(cancelIdx).toBeGreaterThanOrEqual(0);
    expect(confirmIdx).toBeGreaterThanOrEqual(0);
    expect(cancelIdx).toBeLessThan(confirmIdx);
  });

  it('displays the write count', async () => {
    const html = await render(baseProps);
    expect(html).toContain('2 writes');
  });

  it('displays the consequence text', async () => {
    const html = await render(baseProps);
    expect(html).toContain('This will update both records immediately.');
  });

  it('renders object names in the objects list', async () => {
    const html = await render(baseProps);
    expect(html).toContain('Record A');
    expect(html).toContain('Record B');
  });

  it('renders protected fields section when protectedFields provided', async () => {
    const html = await render({ ...baseProps, protectedFields: ['ID', 'CreatedAt'] });
    const dom = new JSDOM(html);
    expect(dom.window.document.querySelector('.write-confirmation__protected')).not.toBeNull();
    expect(html).toContain('ID');
    expect(html).toContain('CreatedAt');
  });

  it('shows writeCount=1 without plural s', async () => {
    const html = await render({ ...baseProps, writeCount: 1 });
    expect(html).toContain('1 write');
    expect(html).not.toContain('1 writes');
  });
});
