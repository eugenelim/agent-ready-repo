import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';

const packs = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/packs' }),
  schema: z.object({
    name: z.string(),
    scope: z.enum(['user', 'repo']),
    // Whether the pack's `allowed-scopes` admits "user" — NOT the same as
    // `scope`, which mirrors `default-scope`. The Claude-plugin route installs
    // at user scope, so only a user-capable pack may be offered there.
    // Required with no default: omitting it must fail the build, not silently
    // advertise the public install route. Kept honest against pack.toml by
    // tools/lint-site-scope-parity.py.
    pluginInstallable: z.boolean(),
    tagline: z.string(),
    skills: z.array(z.string()),
    installCommand: z.string(),
    docsUrl: z.string(),
    journeyUrl: z.string().optional(),
  }),
});

const journeys = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/journeys' }),
  schema: z.object({
    pack: z.string(),
    scope: z.enum(['user', 'repo']),
    tagline: z.string(),
    prerequisitePacks: z.array(z.string()).default([]),
    whatChanges: z.string().optional(),
    // Compact above-the-fold contract (journey-template-revamp). Required —
    // every journey carries one, enforced here and by lint-journey-contract.py.
    contract: z.object({
      useItWhen: z.string(),
      youProvide: z.string(),
      youReceive: z.string(),
      yourDecisions: z.array(z.string()),
    }),
    skills: z.array(
      z.object({
        name: z.string(),
        description: z.string(),
        humanTouches: z.number().int().min(0),
      })
    ),
    humanGates: z.array(
      z.object({
        id: z.string(),
        globalGate: z.string().nullable(),
        label: z.string(),
        trigger: z.string(),
        duration: z.string(),
        whatToCheck: z.array(z.string()),
        whatGoodLooksLike: z.string(),
        whatBadLooksLike: z.string(),
        consequence: z.string(),
      })
    ),
    typicalSession: z.object({
      agentTurns: z.string(),
      humanTouches: z.number().int(),
      wallClockMinutes: z.string(),
    }),
    docsUrl: z.string(),
    packUrl: z.string(),
    relatedJourneys: z.array(z.string()).default([]),
    goodOutputDescription: z.string().optional(),
    // Phase 2B: pack-local JOURNEY.md additions (optional for legacy compatibility)
    journey_id: z.string().optional(),
    start_state: z.string().optional(),
    end_state: z.string().optional(),
    generated: z.boolean().optional(),
  }),
});

export const collections = { packs, journeys };
