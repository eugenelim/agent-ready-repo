import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';
import { journeySchema } from './lib/journey-schema';

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
  schema: journeySchema,
});

export const collections = { packs, journeys };
