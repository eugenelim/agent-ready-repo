import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { inflateSync } from 'node:zlib';

import { describe, expect, it } from 'vitest';

// Pins web/public/social.png — the Open Graph card on every page — to the
// palette in web/src/styles/tokens.css.
//
// The card is a COMMITTED BINARY. `npm run social --prefix web` regenerates it
// from the tokens, but nothing forces anyone to run it, and for two months the
// committed asset carried a withdrawn amber accent that no gate could see. A
// named script makes regeneration possible; it does not make drift impossible.
// This does: both sides below are derived at test time — the expected colour is
// parsed out of tokens.css, the actual colour is decoded out of the PNG — so
// moving the palette without regenerating the card turns this suite red.
//
// Nothing here may be hardcoded. A literal `#0e1311` on either side would
// reproduce the exact defect the test exists to catch: a private copy of the
// palette that stops tracking the tokens.

// Resolved as plain strings, not URL objects: the suite runs in vitest's jsdom
// environment, where the global `URL` is jsdom's implementation from another
// realm, and `readFileSync` rejects it with "The URL must be of scheme file".
const here = dirname(fileURLToPath(import.meta.url));
const tokensPath = resolve(here, '../styles/tokens.css');
const socialPath = resolve(here, '../../public/social.png');

// ── tokens.css ─────────────────────────────────────────────────────────────

/**
 * Parse every `--name: value;` declaration out of tokens.css and resolve
 * `var(--other)` references transitively, so a semantic token yields a literal.
 *
 * Mirrors the generator's own reader (web/scripts/generate-social.mjs). It is
 * re-implemented rather than imported because that module launches a headless
 * browser and writes the PNG at import time — importing it from a unit test
 * would rebuild the very artifact under test, which is a control that cannot
 * fail.
 *
 * @param css - contents of tokens.css
 * @returns token name (with leading `--`) -> literal value
 */
function readTokens(css: string): Map<string, string> {
  const raw = new Map<string, string>();
  // Strip comments first: tokens.css quotes hexes in prose, which would poison
  // the scan (`--prim-record-500` is described next to a contrast measurement).
  const stripped = css.replace(/\/\*[\s\S]*?\*\//g, '');
  for (const [, name, value] of stripped.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
    if (!raw.has(name)) raw.set(name, value.trim());
  }
  const resolved = new Map<string, string>();
  const resolve = (name: string, depth = 0): string => {
    const cached = resolved.get(name);
    if (cached !== undefined) return cached;
    const value = raw.get(name);
    if (value === undefined) throw new Error(`tokens.css has no ${name}`);
    if (depth > 10) throw new Error(`token reference cycle at ${name}`);
    const out = value.replace(/var\((--[\w-]+)\)/g, (_, ref: string) => resolve(ref, depth + 1));
    resolved.set(name, out);
    return out;
  };
  for (const name of raw.keys()) resolve(name);
  return resolved;
}

/**
 * Convert a `#rgb` or `#rrggbb` literal to 8-bit channels.
 *
 * Deliberately narrow: it throws on `rgb()`, `oklch()` or a bare colour name
 * rather than guessing. If the ground token is ever restated in another syntax
 * this test must be updated on purpose, not silently pass on a wrong parse.
 *
 * @param value - a CSS hex colour literal
 * @returns the red, green and blue channels, 0-255
 */
function parseHex(value: string): [number, number, number] {
  const match = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(value.trim());
  if (match === null) throw new Error(`not a hex colour literal: ${JSON.stringify(value)}`);
  const digits = match[1].length === 3 ? match[1].replace(/./g, (d) => d + d) : match[1];
  return [
    parseInt(digits.slice(0, 2), 16),
    parseInt(digits.slice(2, 4), 16),
    parseInt(digits.slice(4, 6), 16),
  ];
}

// ── PNG ────────────────────────────────────────────────────────────────────

// Decoded in-process from `node:zlib`, which is built in.
//
// `sharp` IS resolvable in node_modules today, and was rejected: it is an
// OPTIONAL transitive dependency of astro, not a declared dependency of this
// package, so a `--no-optional` or unsupported-platform install drops it and
// this suite would break for reasons unrelated to the card. Adding `pngjs`
// instead would mean a new entry in web/package.json, which per AGENTS.md is a
// dependency decision, not a test. social.png is 8-bit non-interlaced
// truecolour, which is the tractable corner of the PNG spec: inflate the IDATs
// and reverse five scanline filters.

interface Decoded {
  width: number;
  height: number;
  /** Row-major RGB triples, 3 bytes per pixel, alpha (if any) dropped. */
  rgb: Uint8Array;
}

/**
 * Decode an 8-bit, non-interlaced, truecolour PNG to raw RGB.
 *
 * Every shape assumption is asserted rather than assumed. If the generator
 * ever emits a palette, 16-bit or interlaced PNG, this throws with the actual
 * header values — a loud failure, never a quiet misread of the pixels.
 *
 * @param buffer - the complete PNG file
 * @returns the image dimensions and its un-filtered RGB samples
 */
function decodePng(buffer: Buffer): Decoded {
  const signature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  if (!buffer.subarray(0, 8).equals(signature)) throw new Error('not a PNG: bad signature');

  let width = 0;
  let height = 0;
  let colourType = -1;
  const idat: Buffer[] = [];

  for (let offset = 8; offset + 8 <= buffer.length; ) {
    const length = buffer.readUInt32BE(offset);
    const type = buffer.toString('ascii', offset + 4, offset + 8);
    const data = buffer.subarray(offset + 8, offset + 8 + length);
    offset += 12 + length; // length + type + data + CRC
    if (type === 'IHDR') {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      const bitDepth = data[8];
      colourType = data[9];
      const interlace = data[12];
      if (bitDepth !== 8 || (colourType !== 2 && colourType !== 6) || interlace !== 0) {
        throw new Error(
          `unsupported PNG: bitDepth=${bitDepth} colourType=${colourType} interlace=${interlace}; ` +
            'this decoder handles 8-bit non-interlaced truecolour (2) or truecolour+alpha (6) only',
        );
      }
    } else if (type === 'IDAT') {
      idat.push(Buffer.from(data));
    } else if (type === 'IEND') {
      break;
    }
  }
  if (idat.length === 0) throw new Error('PNG has no IDAT chunks');

  const bpp = colourType === 6 ? 4 : 3; // bytes per pixel
  const stride = width * bpp;
  const raw = inflateSync(Buffer.concat(idat));
  if (raw.length < height * (stride + 1)) {
    throw new Error(`inflated ${raw.length} bytes, need ${height * (stride + 1)}`);
  }

  // Reverse the per-scanline filters (PNG spec §9.2). `prior` is the already
  // un-filtered row above; `line` becomes un-filtered in place.
  const out = Buffer.alloc(height * stride);
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)];
    const line = out.subarray(y * stride, (y + 1) * stride);
    raw.copy(line, 0, y * (stride + 1) + 1, (y + 1) * (stride + 1));
    const prior = y === 0 ? null : out.subarray((y - 1) * stride, y * stride);
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? line[x - bpp] : 0; // left
      const b = prior === null ? 0 : prior[x]; // above
      const c = prior === null || x < bpp ? 0 : prior[x - bpp]; // upper-left
      let add = 0;
      if (filter === 0) add = 0;
      else if (filter === 1) add = a;
      else if (filter === 2) add = b;
      else if (filter === 3) add = (a + b) >> 1;
      else if (filter === 4) {
        const p = a + b - c;
        const pa = Math.abs(p - a);
        const pb = Math.abs(p - b);
        const pc = Math.abs(p - c);
        add = pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
      } else throw new Error(`unknown PNG filter type ${filter} on row ${y}`);
      line[x] = (line[x] + add) & 0xff;
    }
  }

  if (bpp === 3) return { width, height, rgb: new Uint8Array(out) };
  const rgb = new Uint8Array(width * height * 3);
  for (let i = 0, j = 0; i < out.length; i += 4, j += 3) {
    rgb[j] = out[i];
    rgb[j + 1] = out[i + 1];
    rgb[j + 2] = out[i + 2];
  }
  return { width, height, rgb };
}

/** @returns `#rrggbb` for the given 8-bit channels. */
const hex = (r: number, g: number, b: number): string =>
  `#${[r, g, b].map((c) => c.toString(16).padStart(2, '0')).join('')}`;

// ── the assertions ─────────────────────────────────────────────────────────

const tokens = readTokens(readFileSync(tokensPath, 'utf8'));
const heroBg = tokens.get('--ds-hero-bg');
const image = decodePng(readFileSync(socialPath));

// The single per-pixel RGB channel spread (max channel − min channel) allowed
// anywhere on the card.
//
// The card carries no MARK by design: a ground, text and a rule, and never the
// one chromatic mark, which means a refusal or a hold and a social card
// reports neither. "No mark" is not "no spread", though: the neutrals have a
// hue. This bound therefore comes from the palette, not from a literal.
//
// A literal is how this assertion failed: it read 8, derived from a sentence
// that said "the ground token is a green-black, #0e1311, whose own spread is
// 5". The paper-first retrofit made the neutrals warm, every one of those
// numbers went stale at once, and the bound reported a palette change as
// though it were a stray accent pixel. Deriving it from the same five tokens
// the generator paints with means the bound moves when the palette does, and
// only a colour the palette does not contain can breach it.
const CARD_TOKENS = [
  '--ds-hero-bg',        // ground
  '--ds-hero-fg',        // heading
  '--ds-hero-fg-2',      // body
  '--ds-hero-fg-muted',  // eyebrow
  '--prim-record-50',    // rule
] as const;

/** @returns max channel − min channel for a resolved `#rrggbb` token. */
function channelSpread(name: string): number {
  const value = tokens.get(name);
  if (!value) throw new Error(`social-card: tokens.css has no ${name}`);
  const [r, g, b] = parseHex(value);
  return Math.max(r, g, b) - Math.min(r, g, b);
}

const PALETTE_SPREAD = Math.max(...CARD_TOKENS.map(channelSpread));
// An antialiased edge blends two palette colours, and a blend's spread never
// exceeds the larger of the two, so the only headroom the bound needs is for
// 8-bit rounding in the blend itself.
const BLEND_ROUNDING = 2;
const MAX_CHANNEL_SPREAD = PALETTE_SPREAD + BLEND_ROUNDING;

describe('social.png tracks tokens.css', () => {
  it('decodes as the 1200x630 Open Graph card', () => {
    // Guards the decode itself. Every assertion below reads these pixels, so a
    // decoder that silently produced garbage would make the rest meaningless.
    expect({ width: image.width, height: image.height }).toEqual({ width: 1200, height: 630 });
    expect(image.rgb.length).toBe(1200 * 630 * 3);
  });

  it('resolves --ds-hero-bg out of tokens.css to a hex literal', () => {
    // `--ds-hero-bg` is a semantic token pointing at a primitive, so this also
    // proves the `var()` chain resolved. Without it, a broken parse would
    // surface as an opaque throw inside the colour case instead of here.
    // An unresolved token would still be the string `var(--prim-ink-950)`, so
    // requiring a hex literal here is what proves the chain was followed.
    expect(heroBg).toMatch(/^#[0-9a-f]{3}([0-9a-f]{3})?$/i);
  });

  it('has --ds-hero-bg as its dominant colour', () => {
    const counts = new Map<number, number>();
    for (let i = 0; i < image.rgb.length; i += 3) {
      const key = (image.rgb[i] << 16) | (image.rgb[i + 1] << 8) | image.rgb[i + 2];
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    let dominant = -1;
    let best = -1;
    for (const [key, count] of counts) {
      if (count > best) {
        best = count;
        dominant = key;
      }
    }
    const actual = hex((dominant >> 16) & 0xff, (dominant >> 8) & 0xff, dominant & 0xff);
    const [r, g, b] = parseHex(heroBg as string);
    const share = ((best / (image.width * image.height)) * 100).toFixed(1);

    // The context goes in the assertion MESSAGE, not into the compared values:
    // padding both sides of `toEqual` with identical strings would add prose to
    // the diff without adding anything that can fail.
    expect(
      actual,
      `web/public/social.png's dominant colour is ${actual} (${share}% of pixels) but ` +
        `--ds-hero-bg in web/src/styles/tokens.css resolves to ${hex(r, g, b)}. ` +
        'The committed card has drifted from the palette — regenerate it: npm run social --prefix web',
    ).toBe(hex(r, g, b));
  });

  it('leaves the bound far enough below the mark to still catch it', () => {
    // A derived bound can be widened by widening the palette. This is the
    // check that says how far that may go: the mark must stay several times
    // outside the bound, or the spread assertion below stops being able to
    // fail for the reason it exists.
    const markSpread = Math.min(channelSpread('--ds-clearance'), channelSpread('--ds-clearance-dk'));
    expect(
      MAX_CHANNEL_SPREAD,
      `the card's palette spread is ${PALETTE_SPREAD}, giving a bound of ${MAX_CHANNEL_SPREAD}, ` +
        `but the mark's own spread is only ${markSpread}. The neutrals have warmed far enough ` +
        'that a stray mark pixel could pass the spread assertion.',
    ).toBeLessThan(markSpread / 3);
  });

  it('carries no chroma: every pixel is within the achromatic spread', () => {
    // Reports the WORST pixel and a census of offenders, not just the first
    // one. A single miscoloured logo pixel and a wholesale palette change are
    // different bugs, and the failure message should tell them apart.
    let worst = { spread: -1, colour: '', x: -1, y: -1 };
    let offenders = 0;
    for (let i = 0; i < image.rgb.length; i += 3) {
      const r = image.rgb[i];
      const g = image.rgb[i + 1];
      const b = image.rgb[i + 2];
      const spread = Math.max(r, g, b) - Math.min(r, g, b);
      if (spread > MAX_CHANNEL_SPREAD) offenders++;
      if (spread > worst.spread) {
        const pixel = i / 3;
        worst = { spread, colour: hex(r, g, b), x: pixel % image.width, y: Math.floor(pixel / image.width) };
      }
    }
    // One assertion, because `offenders === 0` already implies the max spread
    // is within bounds; a second check on `worst.spread` could never fail
    // independently. The detail rides in the message.
    expect(
      offenders,
      `${offenders} pixel(s) in web/public/social.png exceed an RGB channel spread of ` +
        `${MAX_CHANNEL_SPREAD}. Worst: ${worst.colour} at (${worst.x}, ${worst.y}), spread ` +
        `${worst.spread}. The card's palette spans ${PALETTE_SPREAD}, so this is a colour the ` +
        'palette does not contain — regenerate it: ' +
        'npm run social --prefix web',
    ).toBe(0);
  });
});
