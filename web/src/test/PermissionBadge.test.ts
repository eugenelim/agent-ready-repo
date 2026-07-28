// @vitest-environment node
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { describe, expect, it } from 'vitest';
import PermissionBadge from '../components/primitives/PermissionBadge.astro';

async function render(props: Record<string, unknown>): Promise<string> {
  const container = await AstroContainer.create();
  return container.renderToString(PermissionBadge, { props });
}

describe('PermissionBadge', () => {
  it('missing state is semantically distinct from granted', async () => {
    const grantedHtml = await render({ access: 'granted', permission: 'read:files' });
    const missingHtml = await render({ access: 'missing', permission: 'read:files' });
    const grantedDom = new JSDOM(grantedHtml);
    const missingDom = new JSDOM(missingHtml);
    const grantedState = grantedDom.window.document.querySelector('[data-access="granted"]');
    const missingState = missingDom.window.document.querySelector('[data-access="missing"]');
    expect(grantedState).not.toBeNull();
    expect(missingState).not.toBeNull();
    expect(grantedHtml).toContain('granted');
    expect(missingHtml).toContain('required');
  });

  it('permission name is visible in the output', async () => {
    const html = await render({ access: 'missing', permission: 'write:issues' });
    expect(html).toContain('write:issues');
  });

  it('does not expose raw credentials in output', async () => {
    // Permission name is shown; but the component must not render anything that
    // looks like a secret (e.g. a token, password, or private key).
    const html = await render({ access: 'granted', permission: 'read:repos' });
    expect(html).not.toMatch(/ghp_[a-zA-Z0-9]+/);  // GitHub PAT pattern
    expect(html).not.toMatch(/token[:\s="']+[a-zA-Z0-9_-]{10,}/i);
  });
});
