/**
 * Every control that styles a hover state also styles a press state, and every
 * press state uses the one idiom.
 *
 * WHAT THIS PINS. Before 2026-09-23 the surface had no `:active` rule at all:
 * pressing a control produced nothing a resting pointer had not already
 * produced. The direction sheet rules out the usual remedies — Containment is
 * `[ruled]`, Material `[flat]`, Ornament `[none]`, so no transform, no scale
 * and no shadow is available — which leaves a shift of the control's ground.
 * One idiom, applied to every control, because a surface whose controls each
 * press differently is worse than one that does not press at all.
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
  unreachableComponents,
  expectedGroundToken,
  pressGroundColor,
  textUnderPress,
  textWithoutHover,
  hoverGround,
  resolveColor,
  contrast,
  TEXT_FLOOR,
  PRESS_TOKENS,
} from './press-state-selectors';

describe('press state', () => {
  it('reports the components it excluded as unreachable', () => {
    // Not an assertion that the set is empty — it is not, and a component with
    // no importer is a real thing this repository contains. It is an assertion
    // that the exclusion is VISIBLE: a silent exclusion is how a derived set
    // shrinks without anyone noticing, which is the failure this whole guard
    // exists to prevent one level up.
    const excluded = unreachableComponents();
    // eslint-disable-next-line no-console
    if (excluded.length) console.info(`press-state: excluded as unreachable — ${excluded.join(', ')}`);
    // A component becomes reachable by being imported; if every component were
    // excluded the guard would be checking nothing, so bound it well below that.
    expect(excluded.length).toBeLessThan(5);
  });

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
        (p) => p !== 'background-color' && p !== 'color' && p !== 'transition'
      );
      if (extra.length) {
        offenders.push(
          `  ${rule.file} ${selector}\n    also moves ${extra.join(', ')}; a press moves the ground, and ink only for the floor`
        );
      }

      const ground = pressGroundColor(expectedGroundToken(control, rules));
      // BOTH paths, not just the hovered one. A press co-occurs with hover for a
      // pointer, but a touch tap, a keyboard activation and a press-and-drag-off
      // all apply :active with no :hover, and the ink differs between them.
      // Asking only about the hover path scored `.decision-chip` at 10.03:1 on a
      // label it only has while hovered; unhovered it measures 1.30:1.
      const inks = [textUnderPress(control, rules), textWithoutHover(control, rules)]
        .filter((c): c is string => c !== null);
      // Unknown ink is inherited from a carrier the stylesheet does not name.
      // The browser measurement reads those for real; this guard does not guess.
      if (!ground || !inks.length) continue;

      const worst = Math.min(...inks.map((ink) => contrast(ink, ground)));
      const restText = inks.find((ink) => contrast(ink, ground) === worst)!;
      const needsRaise = worst < TEXT_FLOOR;
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
            `(worst path is ${restText} on ${ground}, already ${worst.toFixed(2)}:1)`
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

  it('moves the ground somewhere the hover has not already been', () => {
    // The whole point of the change, and the one property nothing asserted:
    // `--ds-border` and `--ds-surface-pressed` both resolve to record-200, so
    // two controls whose hover already set --ds-border rendered no press at
    // all. Both layers passed them -- this one because it only checked that a
    // press rule existed and used the right token, and the browser one because
    // it had navigated off the page before reaching them.
    const rules = allRules();
    const byPressSelector = new Map(hoverControls(rules).map((c) => [`${c.file}::${c.pressSelector}`, c]));
    const offenders: string[] = [];

    for (const rule of pressRules(rules)) {
      const selector = rule.selectors.find((s) => s.includes(':active')) ?? rule.selectors[0];
      const control = byPressSelector.get(`${rule.file}::${selector}`);
      if (!control) continue;
      const hover = hoverGround(control, rules);
      const press = resolveColor(rule.declarations['background-color']);
      if (hover && press && hover === press) {
        offenders.push(
          `  ${rule.file} ${selector}\n    press ground ${press} is the colour its hover already set; ` +
            `the control does not change when pressed`
        );
      }
    }
    expect(offenders, `press grounds that duplicate their hover:\n\n${offenders.join('\n\n')}`).toEqual([]);
  });

  it('keeps its label legible when pressed without being hovered', () => {
    // Touch, keyboard activation and press-and-drag-off all apply :active with
    // no :hover. A press rule that moves the ground and borrows its ink from
    // the hover rule is legible on the pointer path only.
    const rules = allRules();
    const byPressSelector = new Map(hoverControls(rules).map((c) => [`${c.file}::${c.pressSelector}`, c]));
    const offenders: string[] = [];

    for (const rule of pressRules(rules)) {
      const selector = rule.selectors.find((s) => s.includes(':active')) ?? rule.selectors[0];
      const control = byPressSelector.get(`${rule.file}::${selector}`);
      if (!control) continue;
      const ground = resolveColor(rule.declarations['background-color']);
      // The press rule's own colour wins on both paths; otherwise the rest colour.
      const text = resolveColor(rule.declarations.color) ?? textWithoutHover(control, rules);
      if (!ground || !text) continue;
      const ratio = contrast(text, ground);
      if (ratio < TEXT_FLOOR) {
        offenders.push(
          `  ${rule.file} ${selector}\n    unhovered press: ${text} on ${ground} is ` +
            `${ratio.toFixed(2)}:1, under ${TEXT_FLOOR}:1. The press rule must carry the ink it needs ` +
            `rather than borrow it from :hover.`
        );
      }
    }
    expect(offenders, `illegible when pressed without hover:\n\n${offenders.join('\n\n')}`).toEqual([]);
  });

  it('only ever uses `transition` to make a press instant', () => {
    // `transition` is admitted in a press rule for one purpose. Seven controls
    // inherit a 120-200ms ease on the property the press moves, and a click is
    // commonly shorter than that, so the ground never reached full value before
    // release. Anything other than `none` here would be a press that animates
    // in, which the direction's `[still]` motion row does not want and which
    // the browser measurement reds anyway.
    const offenders = pressRules()
      .filter((r) => 'transition' in r.declarations && r.declarations.transition.trim() !== 'none')
      .map((r) => `  ${r.file} ${r.selectors.join(', ')}\n    transition: ${r.declarations.transition}`);
    expect(offenders, `press rules that animate:\n\n${offenders.join('\n\n')}`).toEqual([]);
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
