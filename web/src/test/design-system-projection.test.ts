/**
 * §1 of `src/design-system.md` is a projection of `src/styles/tokens.css`.
 *
 * The section held about forty hand-typed hex and rgba literals. The
 * paper-first palette change made every one of them wrong in the same commit,
 * and the document sat that way long enough to grow a header warning readers
 * not to trust its own tables. Nothing failed, because nothing was checking.
 *
 * This is what checks. `scripts/generate-design-system.mjs` rewrites §1 from
 * `tokens.css`; the test below runs the same projection and compares it with
 * what is committed. Editing §1 by hand, or changing a token without
 * regenerating, turns this red.
 *
 * WHY A TEST AND NOT A GITIGNORED ARTEFACT. The other projections in this
 * repository (`web/src/lib/*.generated.json`) are gitignored and rebuilt by an
 * npm `pre*` hook, because only the build reads them. This document is read by
 * people in the repository with no build in front of them, so it stays
 * committed and the guarantee is enforced from the other end.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import {
  projectDocument,
  renderSection,
  TOKENS_CSS,
  DESIGN_SYSTEM_MD,
} from '../../scripts/generate-design-system.mjs';

const css = () => readFileSync(TOKENS_CSS, 'utf8');
const md = () => readFileSync(DESIGN_SYSTEM_MD, 'utf8');

describe('design-system.md §1 is projected from tokens.css', () => {
  it('matches what the generator would write', () => {
    expect(
      projectDocument(md(), css()),
      'design-system.md §1 has drifted from tokens.css. ' +
        'Run: node scripts/generate-design-system.mjs'
    ).toBe(md());
  });

  it('is idempotent — regenerating a generated document changes nothing', () => {
    // Without this, a generator that appends or re-wraps on each run would
    // pass the comparison above only on the run that produced the file.
    const once = projectDocument(md(), css());
    expect(projectDocument(once, css())).toBe(once);
  });

  it('resolves a token through its var() chain, not to a scoped override', () => {
    // The defect this pins: `:where(.section--dark, .footer)` at the foot of
    // tokens.css re-points `--ds-focus-ring` to the off-white dark-ground
    // ring. An earlier draft of the generator read that as the token's
    // definition and printed the PAPER ring as #dcd8ce — 1.31:1 on paper, and
    // the exact failure the re-derivation in tokens.css exists to prevent.
    const section = renderSection(css());
    expect(section).toContain('| `--ds-focus-ring` | `--ds-on-surface` | `#14120f` |');
    // and the override is still reported, under its real carrier, apart from
    // the definition tables.
    expect(section).toContain('`:where(.section--dark, .footer)`');
  });

  it('carries no hex literal that tokens.css does not declare', () => {
    // A cheap, independent read on the same property: every hex printed in §1
    // must appear in tokens.css. It catches a literal typed into the
    // generator itself, which the byte comparison above cannot.
    const source = css().toLowerCase();
    const section = renderSection(css()).toLowerCase();
    const stray = [...new Set(section.match(/#[0-9a-f]{6}\b/g) ?? [])].filter(
      (hex) => !source.includes(hex)
    );
    expect(stray, `hex values in §1 with no declaration in tokens.css: ${stray}`).toEqual([]);
  });

  it('no longer tells the reader its own tables are wrong', () => {
    // The header's standing staleness warning was the honest thing to do while
    // §1 was hand-typed. Leaving it after generating the section would be the
    // opposite: a document that disclaims a guarantee it now has.
    expect(md()).not.toMatch(/STILL STALE/);
  });
});
