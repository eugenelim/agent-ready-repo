import { describe, expect, it } from 'vitest';
import axe from 'axe-core';

describe('test infrastructure', () => {
  it('trivial assertion passes', () => {
    expect('test-infra').toBe('test-infra');
  });

  it('axe-core detects a missing input label', async () => {
    document.body.innerHTML = '<input type="text" id="no-label" />';
    const results = await axe.run(document.body);
    const labelViolation = results.violations.find(v => v.id === 'label');
    expect(labelViolation).toBeDefined();
  });
});
