// @vitest-environment node
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import axe from 'axe-core';
import { JSDOM } from 'jsdom';
import { describe, expect, it } from 'vitest';

// STUB: AC2, AC5, AC6, AC7, AC9 — production surfaces are absent until T2/T3.
import WorkIndex from '../components/work/WorkIndex.astro';
import SiteNav from '../components/layout/SiteNav.astro';
import { loadWorkIndex, validateWorkIndexProjection } from '../lib/work-index';

const markupPayload = '<script>globalThis.compromised = true</script>';

const populated = {
  schemaVersion: 1,
  counts: { active: 1, ready: 1, attention: 1, briefs: 1, shaping: 1, backlog: 1 },
  initiatives: [{
    slug: 'ini-002',
    name: markupPayload,
    milestone: 'P5',
    active: [{
      path: 'docs/specs/active/spec.md',
      summary: 'Continue active work',
      dispatchable: false,
      findings: [],
    }],
    ready: [{
      path: 'docs/specs/example/spec.md',
      summary: markupPayload,
      dispatchable: true,
      findings: [],
    }],
    attention: [{
      path: 'docs/specs/attention/spec.md',
      summary: 'Resolve blocked work',
      dispatchable: false,
      findings: [{
        code: 'unsatisfied_dependency',
        nextAction: 'Complete the declared predecessor.',
      }],
    }],
  }],
  briefs: [{ path: 'docs/product/briefs/adoption-wave.md', initiative: 'ini-002' }],
  shaping: [{ slug: 'adoption-surface', type: 'shape', initiative: 'ini-002' }],
  backlog: [{ slug: 'follow-up', summary: 'Investigate follow-up' }],
};

describe('work-index projection', () => {
  it('preserves status and only finding-supplied next actions', () => {
    const result = validateWorkIndexProjection(populated);
    expect(result.counts).toEqual({
      active: 1,
      ready: 1,
      attention: 1,
      briefs: 1,
      shaping: 1,
      backlog: 1,
    });
    expect(result.initiatives[0].active[0]).not.toHaveProperty('nextAction');
    expect(result.initiatives[0].ready[0].dispatchable).toBe(true);
    expect(result.initiatives[0].ready[0]).not.toHaveProperty('nextAction');
    expect(result.initiatives[0].attention[0].findings[0].nextAction).toBe(
      'Complete the declared predecessor.'
    );
  });

  it('fails closed on an unsupported or malformed projection', () => {
    expect(() => validateWorkIndexProjection({ ...populated, schemaVersion: 2 })).toThrow(
      /unsupported schema version/
    );
    expect(() => validateWorkIndexProjection({ ...populated, initiatives: null })).toThrow(
      /malformed/
    );
  });

  it('aborts without rendering an empty projection when the exporter fails', () => {
    const failure = {
      stderr: Buffer.from(
        'work-index export failed: canonical-blocked-work-item-is-malformed\n'
      ),
      privateDetail: 'secret details at /Users/example/private/workspace',
    };

    expect.assertions(4);
    try {
      loadWorkIndex(() => {
        throw failure;
      });
    } catch (error) {
      expect(error).toBeInstanceOf(Error);
      expect((error as Error).message).toBe(
        'Work-index build failed: canonical-blocked-work-item-is-malformed.'
      );
      expect((error as Error).stack).toBe((error as Error).message);
      expect(String(error)).not.toMatch(/Traceback|\/Users\/|secret details/i);
    }
  });

  it('leaves cold-start margin around the exporter-owned status timeout', () => {
    let parentTimeout = 0;
    const result = loadWorkIndex((_file, _args, options) => {
      parentTimeout = options.timeout;
      return JSON.stringify({
        schema_version: 1,
        counts: { active: 0, ready: 0, attention: 0, briefs: 0, shaping: 0, backlog: 0 },
        initiatives: [],
        briefs: [],
        shaping: [],
        backlog: [],
      });
    });

    expect(result.counts.active).toBe(0);
    expect(parentTimeout).toBeGreaterThanOrEqual(60_000);
  });
});

describe('WorkIndex', () => {
  it('renders all populated buckets in delivery-first order', async () => {
    const container = await AstroContainer.create();
    const html = await container.renderToString(WorkIndex, { props: { data: populated } });
    const text = new JSDOM(html).window.document.body.textContent ?? '';
    const deliveryLabels = ['Active work', 'Ready work', 'Needs attention'];

    expect(text).toContain('Continue active work');
    expect(text).toContain('P5');
    expect(text).toContain('Resolve blocked work');
    expect(text).toContain('unsatisfied_dependency');
    expect(text).toContain('Complete the declared predecessor.');
    expect(text).toContain('Ready briefs');
    expect(text).toContain('adoption-wave');
    expect(
      [...new JSDOM(html).window.document.querySelectorAll('strong')]
        .map(element => element.textContent)
    ).toContain('adoption-wave');
    expect(text).toContain('Shaping');
    expect(text).toContain('adoption-surface');
    expect(text).toContain('Backlog');
    expect(text).toContain('Investigate follow-up');
    expect(text).toMatch(/Active work\s*1/);
    expect(text).toMatch(/Ready work\s*1/);
    expect(text).toMatch(/Needs attention\s*1/);
    expect(text).toMatch(/Ready briefs\s*1/);
    expect(text).toMatch(/Shaping\s*1/);
    expect(text).toMatch(/Backlog\s*1/);
    expect(deliveryLabels.map(label => text.indexOf(label))).toEqual(
      [...deliveryLabels].map(label => text.indexOf(label)).sort((a, b) => a - b)
    );
  });

  it('renders repository markup payloads as inert visible text', async () => {
    const container = await AstroContainer.create();
    const html = await container.renderToString(WorkIndex, { props: { data: populated } });
    const dom = new JSDOM(html);

    expect(dom.window.document.querySelector('script')).toBeNull();
    expect(dom.window.document.body.textContent).toContain(markupPayload);
  });

  it('uses semantic landmarks and passes the automated accessibility floor', async () => {
    const container = await AstroContainer.create();
    const html = await container.renderToString(WorkIndex, { props: { data: populated } });
    const dom = new JSDOM(`<main>${html}</main>`);
    const main = dom.window.document.querySelector('main') as Element;
    const results = await axe.run(main as any);

    expect(dom.window.document.querySelector('h1')?.textContent).toContain('Work index');
    expect(dom.window.document.querySelectorAll('section').length).toBeGreaterThan(3);
    expect(results.violations).toHaveLength(0);
  });

  it('renders a valid empty state without Project creation guidance', async () => {
    const container = await AstroContainer.create();
    const data = {
      ...populated,
      counts: { active: 0, ready: 0, attention: 0, briefs: 0, shaping: 0, backlog: 0 },
      initiatives: [],
      briefs: [],
      shaping: [],
      backlog: [],
    };
    const html = await container.renderToString(WorkIndex, { props: { data } });

    expect(html).toContain('work-intake');
    expect(html).toContain('workspace-status');
    expect(html).not.toMatch(/create a project/i);
  });
});

describe('SiteNav work entry', () => {
  it('renders one base-aware Work link in both desktop and mobile paths', async () => {
    const container = await AstroContainer.create();
    const html = await container.renderToString(SiteNav);
    const document = new JSDOM(html).window.document;
    const desktop = document.querySelectorAll('.nav__links a[href$="/work/"]');
    const mobile = document.querySelectorAll('.nav__drawer a[href$="/work/"]');

    expect(desktop).toHaveLength(1);
    expect(mobile).toHaveLength(1);
    expect(desktop[0].textContent).toBe('Work');
    expect(mobile[0].textContent).toBe('Work');
  });
});
