/**
 * Parse an approved journey transcript into speaker turns.
 *
 * `goodOutputDescription` is a YAML block scalar written in light Markdown: each
 * turn opens with a `**Speaker:**` label and may soft-wrap onto following lines,
 * and a turn may contain inline `` `code` ``. It used to be interpolated straight
 * into a `<p>`, which Astro escapes — so the asterisks and backticks shipped as
 * visible characters and HTML whitespace collapsing flattened every turn into one
 * run-on paragraph, destroying the who-said-what-in-what-order structure that is
 * the whole point of a transcript.
 *
 * This returns structure instead of a string so the template can render real
 * elements. Nothing here emits markup, so there is no `set:html` and no injection
 * surface, and no Markdown dependency is added.
 */

/** One span of a turn: literal text, or a fragment that was backtick-quoted. */
export interface TranscriptPart {
  kind: 'text' | 'code';
  value: string;
}

/** One labelled turn. `speaker` is empty for text preceding any label. */
export interface TranscriptTurn {
  speaker: string;
  parts: TranscriptPart[];
}

/** `**Speaker:**` at the start of a line, capturing the speaker and the rest. */
const SPEAKER_LINE = /^\*\*(.+?):\*\*\s*(.*)$/;

/** Split a turn's text on backtick pairs. An unpaired backtick stays literal. */
function splitInlineCode(text: string): TranscriptPart[] {
  const parts: TranscriptPart[] = [];
  let rest = text;
  while (rest.length > 0) {
    const open = rest.indexOf('`');
    if (open === -1) break;
    const close = rest.indexOf('`', open + 1);
    if (close === -1) break;
    if (open > 0) parts.push({ kind: 'text', value: rest.slice(0, open) });
    parts.push({ kind: 'code', value: rest.slice(open + 1, close) });
    rest = rest.slice(close + 1);
  }
  if (rest.length > 0) parts.push({ kind: 'text', value: rest });
  return parts;
}

export function parseTranscript(raw: string): TranscriptTurn[] {
  const turns: TranscriptTurn[] = [];
  let speaker: string | null = null;
  let buffer: string[] = [];

  const flush = (): void => {
    if (speaker === null && buffer.length === 0) return;
    // Lines within a turn are soft wraps of one utterance, so they rejoin with a
    // single space rather than a line break.
    const text = buffer.join(' ').replace(/\s+/g, ' ').trim();
    if (speaker === null && text === '') return;
    turns.push({ speaker: speaker ?? '', parts: splitInlineCode(text) });
  };

  for (const line of raw.split('\n')) {
    const match = SPEAKER_LINE.exec(line.trim());
    if (match) {
      flush();
      speaker = match[1];
      buffer = match[2] ? [match[2]] : [];
      continue;
    }
    if (line.trim() === '') continue;
    buffer.push(line.trim());
  }
  flush();
  return turns;
}
