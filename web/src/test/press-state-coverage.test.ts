/**
 * Every control that styles a hover state also styles a press state, and every
 * press state uses the one idiom.
 *
 * WHAT THIS PINS. Before 2026-09-23 the surface had no `:active` rule at all:
 * pressing a control produced nothing a resting pointer had not already
 * produced. The direction sheet rules out the usual remedies — Containment is
 * `[ruled]`, Material `[flat]`, Ornament `[none]`, so no transform, no scale
 * and no shadow is available — which leaves a shift of the control's ground.
 * One idiom, applied to every control, because 31 controls with three press
 * behaviours would be worse than none.
 *
 * WHAT IT DELIBERATELY DOES NOT DO. It names no selector and asserts no count.
 * The set comes from `press-state-selectors.ts`, which reads the `.astro`
 * sources on every run. A count here would be a fourth instance of the defect
 * that produced "0 of 28" in the backlog and two CI failures during the
 * retrofit.
 */
import { describe, it, expect } from 'vitest';
import {
  allRules,
  hoverControls,
  pressRules,
  selectorsByFile,
  expectedGroundToken,
  pressGroundColor,
  textUnderPress,
  resolveColor,
  contrast,
  TEXT_FLOOR,
  PRESS_TOKENS,
} from './press-state-selectors';

describe('press state', () => {
  it('derives a non-empty control set from the sources', () => {
    // Without this, every assertion below passes vacuously the day the parser
    // stops matching — a guard that covers nothing reports the same green as
    // a guard that covers everything.
    expect(hoverControls().length).toBeGreaterThan(0);
  });

  it('gives every hover-styled control a press state', () => {
    const byFile = selectorsByFile();
    const missing = hoverControls()
      .filter((c) => !byFile.get(c.file)?.has(c.pressSelector))
      .map((c) => `  ${c.file}\n    has ${c.hoverSelector}\n    needs ${c.pressSelector}`);

    expect(
      missing,
      `${missing.length} control(s) style a hover state with no press state.\n` +
        `Add the :active rule beside the :hover rule, setting one ground\n` +
        `property to one of ${PRESS_TOKENS.join(', ')}.\n\n${missing.join('\n\n')}`
    ).toEqual([]);
  });

  it('moves the ground, through the token its own carrier implies', () => {
    // AC3a. Which ground a control takes is COMPUTED from the control -- an ink
    // hover ground takes the ink press, an on-dark label means a dark-band
    // carrier, everything else is paper. An earlier draft classified by a list
    // of class names and got `.decision-chip` wrong: its hover inverts it to an
    // ink fill, so the paper ground would have put #f7f5f0 text on #ddd8cd at
    // 1.30:1. A list cannot notice that; the carrier can.
    const rules = allRules();
    const byPressSelector = new Map(hoverControls(rules).map((c) => [`${c.file}::${c.pressSelector}`, c]));
    const offenders: string[] = [];

    for (const rule of pressRules(rules)) {
      const selector = rule.selectors.find((s) => s.includes(':active')) ?? rule.selectors[0];
      const control = byPressSelector.get(`${rule.file}::${selector}`);
      if (!control) continue; // a press rule with no hover sibling is not this test's subject

      const ground = rule.declarations['background-color'];
      if (!ground) {
        offenders.push(`  ${rule.file} ${selector}\n    sets no ground; a press is a ground shift`);
        continue;
      }
      const expected = expectedGroundToken(control, rules);
      if (!ground.includes(`var(${expected})`)) {
        offenders.push(
          `  ${rule.file} ${selector}\n    takes ${ground}; its carrier implies var(${expected})`
        );
      }
    }
    expect(offenders, `press rules off the derived idiom:\n\n${offenders.join('\n\n')}`).toEqual([]);
  });

  it('raises the ink only where the floor requires it, and far enough', () => {
    // AC3, as amended 2026-09-23. The ground shift is the idiom; an ink raise is
    // permitted only where the new ground would otherwise drop the label below
    // WCAG 1.4.3's 4.5:1. Both halves are asserted: an unnecessary raise is drift
    // away from the one idiom, and a raise that does not clear the floor is the
    // defect the exception exists to prevent.
    const rules = allRules();
    const byPressSelector = new Map(hoverControls(rules).map((c) => [`${c.file}::${c.pressSelector}`, c]));
    const offenders: string[] = [];

    for (const rule of pressRules(rules)) {
      const selector = rule.selectors.find((s) => s.includes(':active')) ?? rule.selectors[0];
      const control = byPressSelector.get(`${rule.file}::${selector}`);
      if (!control) continue;

      const extra = Object.keys(rule.declarations).filter(
        (p) => p !== 'background-color' && p !== 'color'
      );
      if (extra.length) {
        offenders.push(
          `  ${rule.file} ${selector}\n    also moves ${extra.join(', ')}; a press moves the ground, and ink only for the floor`
        );
      }

      const ground = pressGroundColor(expectedGroundToken(control, rules));
      const restText = textUnderPress(control, rules);
      // Unknown text is inherited from a carrier the stylesheet does not name.
      // The browser measurement reads those for real; this guard does not guess.
      if (!ground || !restText) continue;

      const needsRaise = contrast(restText, ground) < TEXT_FLOOR;
      const raised = resolveColor(rule.declarations.color);

      if (needsRaise && !raised) {
        offenders.push(
          `  ${rule.file} ${selector}\n    ${restText} on ${ground} is ` +
            `${contrast(restText, ground).toFixed(2)}:1, under ${TEXT_FLOOR}:1, and the rule raises no ink`
        );
      }
      if (!needsRaise && rule.declarations.color) {
        offenders.push(
          `  ${rule.file} ${selector}\n    raises ink the floor does not require ` +
            `(${restText} on ${ground} is already ${contrast(restText, ground).toFixed(2)}:1)`
        );
      }
      if (raised && contrast(raised, ground) < TEXT_FLOOR) {
        offenders.push(
          `  ${rule.file} ${selector}\n    raises ink to ${raised}, still only ` +
            `${contrast(raised, ground).toFixed(2)}:1 on ${ground}`
        );
      }
    }
    expect(offenders, `press contrast:\n\n${offenders.join('\n\n')}`).toEqual([]);
  });

  it('never reaches the clearance mark', () => {
    // `--ds-clearance` means a refusal, a hold or a block. It has exactly two
    // consumers and both are HELD. A press is not a refusal, and the moment a
    // third consumer appears the token means "state, and also this" — which is
    // precisely how the amber accent failed before the register palette.
    const reaching = pressRules()
      .filter((r) => Object.values(r.declarations).some((v) => v.includes('--ds-clearance')))
      .map((r) => `  ${r.file} ${r.selectors.join(', ')}`);
    expect(reaching, `a press rule reaches the mark:\n${reaching.join('\n')}`).toEqual([]);
  });

  it('uses no elevation, transform or scale anywhere in a press rule', () => {
    // The direction sheet's Material row is `[flat]` and its Ornament row is
    // `[none]`. These are the properties a press state normally reaches for.
    const forbidden = /\b(transform|box-shadow|scale|translate|filter)\b/;
    const offenders = pressRules()
      .filter((r) => Object.keys(r.declarations).some((p) => forbidden.test(p)))
      .map((r) => `  ${r.file} ${r.selectors.join(', ')}`);
    expect(offenders, `press rule uses elevation or motion:\n${offenders.join('\n')}`).toEqual([]);
  });
});

describe('the derivation itself', () => {
  it('excludes a state lock by rule shape, not by name', () => {
    // A rule that lists both `X` and `X:hover` applies whether or not a
    // pointer is present, so it is not a hover affordance and needs no press
    // state. This asserts the exclusion is reachable — if the shape stops
    // occurring the guard simply covers more, which is safe; if it stops being
    // RECOGNISED, this reds rather than demanding a press rule for a lock.
    const locks = allRules().filter((r) =>
      r.selectors.some(
        (s) => /:hover\b/.test(s) && r.selectors.includes(s.replace(/:hover\b/g, '').trim())
      )
    );
    const derived = new Set(hoverControls().map((c) => `${c.file}::${c.hoverSelector}`));
    for (const lock of locks) {
      for (const s of lock.selectors.filter((x) => /:hover\b/.test(x))) {
        expect(derived.has(`${lock.file}::${s}`)).toBe(false);
      }
    }
  });
});
