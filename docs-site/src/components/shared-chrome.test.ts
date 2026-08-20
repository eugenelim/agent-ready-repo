import assert from 'node:assert/strict';
import { test } from 'node:test';
import { docsChromeCurrent, docsChromeHref } from './shared-chrome.ts';

test('resolves docs chrome from declared kind rather than target hostname shape', () => {
  assert.equal(
    docsChromeHref(
      { id: 'declared-external', label: 'External', target: 'not-a-url', kind: 'external' },
      '/agent-ready-repo'
    ),
    'not-a-url'
  );
  assert.equal(
    docsChromeHref(
      { id: 'docs', label: 'Docs', target: '/docs/', kind: 'internal' },
      '/agent-ready-repo'
    ),
    '/agent-ready-repo/docs/'
  );
});

test('marks docs root as page and nested docs as location without fragment state', () => {
  const docs = { id: 'docs', label: 'Docs', target: '/docs/', kind: 'internal' } as const;
  const fragment = { id: 'how-it-works', label: 'How it works', target: '/#three-loops', kind: 'internal' } as const;
  assert.equal(docsChromeCurrent(docs, '/docs/'), 'page');
  assert.equal(docsChromeCurrent(docs, '/docs/getting-started/install/'), 'location');
  assert.equal(docsChromeCurrent(fragment, '/'), undefined);
});
