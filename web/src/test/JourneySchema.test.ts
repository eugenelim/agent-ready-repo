import { describe, expect, it } from 'vitest';
import { journeySchema } from '../lib/journey-schema';

const gate = {
  id: 'approve-plan',
  globalGate: null,
  label: 'Approve the plan',
  trigger: 'After planning',
  duration: '5 minutes',
  whatToCheck: ['The plan is complete.'],
  whatGoodLooksLike: 'A complete plan.',
  whatBadLooksLike: 'An incomplete plan.',
  consequence: 'The work does not proceed.',
};

const generatedJourney = {
  pack: 'example-pack',
  scope: 'repo' as const,
  tagline: 'Example journey.',
  prerequisitePacks: [],
  contract: {
    useItWhen: 'You need an example.',
    youProvide: 'An example.',
    youReceive: 'An example result.',
    decisionGateIds: ['approve-plan'],
  },
  skills: [],
  humanGates: [gate],
  typicalSession: {
    agentTurns: '1',
    humanTouches: 1,
    wallClockMinutes: '5',
  },
  docsUrl: '/docs/guides/example/',
  packUrl: '/packs/example-pack/',
  generated: true,
};

describe('generated journey identity contracts', () => {
  it('rejects a pack-sourced journey that omits decision gate IDs', () => {
    const { decisionGateIds: _omitted, ...legacyContract } = generatedJourney.contract;

    const result = journeySchema.safeParse({
      ...generatedJourney,
      contract: legacyContract,
    });

    expect(result.success).toBe(false);
    if (result.success) throw new Error('generated journey without IDs unexpectedly validated');
    expect(result.error.issues).toContainEqual(expect.objectContaining({
      path: ['contract', 'decisionGateIds'],
      message: 'generated journeys require decision gate IDs',
    }));
  });

  it('carries youType through so the page can render what to type', () => {
    const result = journeySchema.safeParse({
      ...generatedJourney,
      contract: { ...generatedJourney.contract, youType: 'Start the example.' },
    });

    expect(result.success).toBe(true);
    if (!result.success) throw new Error('journey with youType unexpectedly failed');
    expect(result.data.contract.youType).toBe('Start the example.');
  });

  it('rejects a whitespace-only youType, matching journey_validator.py', () => {
    // A "what to type" row with nothing to type is worse than no row. The
    // Python validator rejects this with strip(); Zod must agree, or the two
    // gates disagree on the same journey.
    const result = journeySchema.safeParse({
      ...generatedJourney,
      contract: { ...generatedJourney.contract, youType: '   ' },
    });

    expect(result.success).toBe(false);
  });

  it('still parses a journey that declares no youType', () => {
    const result = journeySchema.safeParse(generatedJourney);

    expect(result.success).toBe(true);
    if (!result.success) throw new Error('journey without youType unexpectedly failed');
    expect(result.data.contract.youType).toBeUndefined();
  });

  it('permits a hand-authored display-only legacy journey', () => {
    const { decisionGateIds: _semanticIds, ...legacyContract } = generatedJourney.contract;

    const result = journeySchema.safeParse({
      ...generatedJourney,
      generated: undefined,
      contract: { ...legacyContract, yourDecisions: ['Approve the plan'] },
      humanGates: [{ ...gate, id: 'G-plan' }],
    });

    expect(result.success).toBe(true);
  });
});
