// @vitest-environment node
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { describe, expect, it } from 'vitest';
import TaskSwitcher from '../components/primitives/TaskSwitcher.astro';

async function render(props: Record<string, unknown>): Promise<string> {
  const container = await AstroContainer.create();
  return container.renderToString(TaskSwitcher, { props });
}

const navItems = [
  { id: 'overview', label: 'Overview', href: '/overview' },
  { id: 'details', label: 'Details', href: '/details' },
];

const tabItems = [
  { id: 'tab1', label: 'First' },
  { id: 'tab2', label: 'Second' },
];

describe('TaskSwitcher', () => {
  it('type="nav" renders <nav> with <a> elements', async () => {
    const html = await render({ type: 'nav', items: navItems });
    const dom = new JSDOM(html);
    expect(dom.window.document.querySelector('nav.task-switcher--nav')).not.toBeNull();
    expect(dom.window.document.querySelector('a.task-switcher__item')).not.toBeNull();
    expect(dom.window.document.querySelector('[role="tab"]')).toBeNull();
  });

  it('type="tabs" renders role="tablist" with role="tab" buttons', async () => {
    const html = await render({ type: 'tabs', items: tabItems, activeId: 'tab1' });
    const dom = new JSDOM(html);
    expect(dom.window.document.querySelector('[role="tablist"]')).not.toBeNull();
    const tabs = dom.window.document.querySelectorAll('[role="tab"]');
    expect(tabs.length).toBe(2);
    expect(dom.window.document.querySelector('[role="tabpanel"]')).not.toBeNull();
    expect(dom.window.document.querySelector('nav')).toBeNull();
  });

  it('active tab has aria-selected="true"', async () => {
    const html = await render({ type: 'tabs', items: tabItems, activeId: 'tab1' });
    const dom = new JSDOM(html);
    const activeTab = dom.window.document.querySelector('[aria-selected="true"]');
    expect(activeTab).not.toBeNull();
    expect(activeTab?.textContent?.trim()).toBe('First');
  });
});
