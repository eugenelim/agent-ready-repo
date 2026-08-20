import { afterEach, describe, expect, it, vi } from 'vitest';

async function previewPort(value: string | undefined): Promise<number> {
  vi.resetModules();
  if (value === undefined) {
    vi.stubEnv('ARR_PREVIEW_PORT', undefined);
  } else {
    vi.stubEnv('ARR_PREVIEW_PORT', value);
  }
  return (await import('./e2e/site-base')).PREVIEW_PORT;
}

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe('PREVIEW_PORT', () => {
  it('defaults to 4321 when ARR_PREVIEW_PORT is unset', async () => {
    expect(await previewPort(undefined)).toBe(4321);
  });

  it('defaults to 4321 when ARR_PREVIEW_PORT is empty', async () => {
    expect(await previewPort('')).toBe(4321);
  });

  it('honours a valid ARR_PREVIEW_PORT override', async () => {
    expect(await previewPort('49152')).toBe(49152);
  });

  it.each(['not-a-number', '1.5', '0', '-1', '65536'])(
    'rejects invalid ARR_PREVIEW_PORT %j',
    async (value) => {
      await expect(previewPort(value)).rejects.toThrow(
        `ARR_PREVIEW_PORT must be an integer from 1 to 65535; received ${JSON.stringify(value)}`,
      );
    },
  );
});
