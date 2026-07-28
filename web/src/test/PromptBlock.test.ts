// @vitest-environment node
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { describe, expect, it } from 'vitest';
import PromptBlock from '../components/primitives/PromptBlock.astro';

async function render(props: Record<string, unknown>): Promise<string> {
  const container = await AstroContainer.create();
  return container.renderToString(PromptBlock, { props });
}

describe('PromptBlock', () => {
  it('renders speaker label when provided', async () => {
    const html = await render({ speaker: 'Claude', prompt: 'List all open issues' });
    expect(html).toContain('Claude');
  });

  it('renders the prompt text', async () => {
    const html = await render({ prompt: 'Summarize this PR' });
    expect(html).toContain('Summarize this PR');
  });

  it('has an amber left border (accent class marker)', async () => {
    const html = await render({ prompt: 'test' });
    const dom = new JSDOM(html);
    const block = dom.window.document.querySelector('.prompt-block');
    expect(block).not.toBeNull();
  });

  it('renders ReadWriteBadge when mode is provided', async () => {
    const html = await render({ prompt: 'test', mode: 'proposed-write' });
    expect(html).toContain('Review before writing');
  });

  it('uses <aside> element (not <div> or <section>) for semantic distinction', async () => {
    const html = await render({ prompt: 'test' });
    const dom = new JSDOM(html);
    expect(dom.window.document.querySelector('aside.prompt-block')).not.toBeNull();
  });
});
