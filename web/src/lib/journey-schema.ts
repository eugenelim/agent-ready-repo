import { z } from 'astro/zod';

const semanticGateId = z.string().regex(/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/);

export const journeySchema = z.object({
  pack: z.string(),
  scope: z.enum(['user', 'repo']),
  tagline: z.string(),
  prerequisitePacks: z.array(z.string()).default([]),
  whatChanges: z.string().optional(),
  contract: z.object({
    useItWhen: z.string(),
    youProvide: z.string(),
    youReceive: z.string(),
    decisionGateIds: z.array(semanticGateId).optional(),
    yourDecisions: z.array(z.string()).optional(),
  }),
  skills: z.array(z.object({
    name: z.string(),
    description: z.string(),
    humanTouches: z.number().int().min(0),
  })),
  humanGates: z.array(z.object({
    id: z.string(),
    globalGate: z.string().nullable(),
    label: z.string(),
    trigger: z.string(),
    duration: z.string(),
    whatToCheck: z.array(z.string()),
    whatGoodLooksLike: z.string(),
    whatBadLooksLike: z.string(),
    consequence: z.string(),
  })).superRefine((gates, context) => {
    const ids = new Set<string>();
    for (const [index, gate] of gates.entries()) {
      if (ids.has(gate.id)) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: [index, 'id'],
          message: `duplicate human gate ID: ${gate.id}`,
        });
      }
      ids.add(gate.id);
    }
  }),
  typicalSession: z.object({
    agentTurns: z.string(),
    humanTouches: z.number().int(),
    wallClockMinutes: z.string(),
  }),
  docsUrl: z.string(),
  packUrl: z.string(),
  relatedJourneys: z.array(z.string()).default([]),
  eyebrow: z.string().optional(),
  goodOutputDescription: z.string().optional(),
  journey_id: z.string().optional(),
  start_state: z.string().optional(),
  end_state: z.string().optional(),
  generated: z.boolean().optional(),
}).superRefine((journey, context) => {
  const decisionGateIds = journey.contract.decisionGateIds;
  if (journey.generated && !decisionGateIds) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['contract', 'decisionGateIds'],
      message: 'generated journeys require decision gate IDs',
    });
    return;
  }
  // `yourDecisions` deliberately coexists with `decisionGateIds`. The published
  // catalogue contract still requires it, so a generated journey carries both:
  // the IDs drive fragments and ordering, the strings stay the adopter-facing
  // prose. The renderer prefers the IDs, so nothing is displayed twice.
  if (!decisionGateIds) return;

  const gateIds = new Set(journey.humanGates.map((gate) => gate.id));
  const referenced = new Set<string>();
  for (const [index, gate] of journey.humanGates.entries()) {
    if (!semanticGateId.safeParse(gate.id).success) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['humanGates', index, 'id'],
        message: `invalid human gate ID: ${gate.id}`,
      });
    }
  }
  for (const [index, id] of decisionGateIds.entries()) {
    if (referenced.has(id)) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['contract', 'decisionGateIds', index],
        message: `duplicate decision gate ID: ${id}`,
      });
    }
    if (!gateIds.has(id)) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['contract', 'decisionGateIds', index],
        message: `unresolved decision gate ID: ${id}`,
      });
    }
    referenced.add(id);
  }
  for (const gate of journey.humanGates) {
    if (!referenced.has(gate.id)) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['contract', 'decisionGateIds'],
        message: `human gate is not a contract decision: ${gate.id}`,
      });
    }
  }
});
