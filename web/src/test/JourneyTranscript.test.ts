import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { parseTranscript } from '../lib/journey-transcript';

const PRIORITY = ['core', 'product-engineering', 'release-engineering'] as const;

/** The approved block scalar, read from the canonical pack source.
 *
 * Built with `node:path` rather than `new URL(..., import.meta.url)`: Vite
 * statically analyses the latter as an asset import and denies it for paths
 * outside its root. Vitest runs with `web/` as cwd. */
function canonicalTranscript(journey: string): string {
  const path = resolve(process.cwd(), '..', 'packs', journey, 'JOURNEY.md');
  const text = readFileSync(path, 'utf8');
  const match = /^goodOutputDescription: \|-\n((?:  .*\n|\n)+)/m.exec(text);
  if (!match) throw new Error(`${journey}: no goodOutputDescription block scalar`);
  return match[1]
    .split('\n')
    .map((line) => (line.startsWith('  ') ? line.slice(2) : line))
    .join('\n');
}

describe('parseTranscript', () => {
  it('splits labelled turns and keeps their order', () => {
    const turns = parseTranscript('**You:** Do the thing.\n**Agent:** Done.');
    expect(turns.map((t) => t.speaker)).toEqual(['You', 'Agent']);
    expect(turns[0].parts).toEqual([{ kind: 'text', value: 'Do the thing.' }]);
  });

  it('rejoins a soft-wrapped turn into one utterance', () => {
    // The wrap is a YAML artefact, not a line break the reader should see.
    const turns = parseTranscript('**You:** Start work on adding\nexport filters.');
    expect(turns).toHaveLength(1);
    expect(turns[0].parts).toEqual([
      { kind: 'text', value: 'Start work on adding export filters.' },
    ]);
  });

  it('extracts inline code as its own part', () => {
    const turns = parseTranscript('**You:** Use `release-loop` now.');
    expect(turns[0].parts).toEqual([
      { kind: 'text', value: 'Use ' },
      { kind: 'code', value: 'release-loop' },
      { kind: 'text', value: ' now.' },
    ]);
  });

  it('leaves an unpaired backtick as literal text rather than dropping copy', () => {
    const turns = parseTranscript('**You:** A stray ` mark.');
    expect(turns[0].parts).toEqual([{ kind: 'text', value: 'A stray ` mark.' }]);
  });

  it('keeps text that precedes any speaker label', () => {
    const turns = parseTranscript('Preamble line.\n**You:** Then this.');
    expect(turns.map((t) => t.speaker)).toEqual(['', 'You']);
    expect(turns[0].parts).toEqual([{ kind: 'text', value: 'Preamble line.' }]);
  });

  it('returns nothing for empty input', () => {
    expect(parseTranscript('')).toEqual([]);
    expect(parseTranscript('\n\n')).toEqual([]);
  });

  describe.each(PRIORITY)('the approved %s transcript', (journey) => {
    const turns = parseTranscript(canonicalTranscript(journey));

    it('parses into labelled turns', () => {
      expect(turns.length).toBeGreaterThan(0);
      // Every turn is attributed; an unlabelled turn would mean the parser lost
      // a speaker and the transcript would stop being verifiable.
      expect(turns.every((t) => t.speaker !== '')).toBe(true);
      expect(new Set(turns.map((t) => t.speaker)).size).toBeGreaterThan(1);
    });

    it('leaves no Markdown character in any rendered part', () => {
      // This is the defect that shipped: `**` and backticks reached the page as
      // visible characters. The parser must consume both.
      for (const turn of turns) {
        expect(turn.speaker).not.toMatch(/[*`]/);
        for (const part of turn.parts) {
          expect(part.value).not.toMatch(/[*`]/);
        }
      }
    });
  });
});
