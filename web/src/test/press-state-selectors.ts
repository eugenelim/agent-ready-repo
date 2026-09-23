/**
 * Derive the surface's interactive controls from its own stylesheets.
 *
 * WHY THIS IS DERIVED AND NOT LISTED.
 *
 * The finding this exists to close was recorded as "0 of 28 interactive
 * classes distinguish :active from :hover". There were never 28 — the figure
 * was stale when it was written, and a later re-count said 33, which was also
 * wrong because it counted comments and test files. Two CI failures on this
 * surface during the 2026-09-18 retrofit came from hardcoded lists that went
 * stale the same way.
 *
 * So nothing here names a selector or a count. The set is computed from the
 * `.astro` sources on every run: add a control with a hover style tomorrow and
 * it is covered tomorrow, with no edit to this file or to its consumers.
 *
 * Both the static guard (`press-state-coverage.test.ts`) and the browser
 * measurement (`e2e/press-state.spec.ts`) import this one derivation, so the
 * two cannot disagree about what the set is.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, relative, resolve } from 'node:path';

/** The three tokens a press rule may reference. Nothing else is the idiom. */
export const PRESS_TOKENS = [
  '--ds-cta-primary-bg-active',
  '--ds-surface-pressed',
  '--ds-surface-pressed-dk',
] as const;

export interface Rule {
  /** Every selector in the rule's selector list, whitespace-normalised. */
  selectors: string[];
  /** The rule's declarations, as `property` → `value`. */
  declarations: Record<string, string>;
  /** Repository-relative path of the file the rule was found in. */
  file: string;
}

export interface Control {
  /** The hover selector exactly as written, e.g. `.nav__link:hover`. */
  hoverSelector: string;
  /** The press selector that must exist for it, e.g. `.nav__link:active`. */
  pressSelector: string;
  /** The element a pointer presses — the one carrying `:hover`. */
  pressTarget: string;
  /** The element whose computed style changes. Usually the same; for a rule
   *  like `.role-record__link:hover .role-record__name` it is the descendant. */
  measureTarget: string;
  file: string;
}

/**
 * Split a hover selector into the element a pointer acts on and the element
 * that restyles. They differ whenever a rule reaches a descendant, which two
 * catalogue record links do.
 */
function targets(hoverSelector: string): { pressTarget: string; measureTarget: string } {
  const at = hoverSelector.indexOf(':hover');
  const head = hoverSelector.slice(0, at);
  const tail = hoverSelector.slice(at + ':hover'.length);
  const pressTarget = head.trim();
  const measureTarget = `${head}${tail}`.replace(/:hover\b/g, '').replace(/\s+/g, ' ').trim();
  return { pressTarget, measureTarget };
}

/** `web/src`, resolved from this file rather than from the working directory:
 *  vitest and playwright run from different roots. */
const SRC = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function astroFiles(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      // `test/` holds fixtures and specs that quote selectors as data; a
      // quoted selector is not a rule on the surface.
      if (name !== 'test' && name !== 'node_modules') astroFiles(full, out);
    } else if (name.endsWith('.astro')) {
      out.push(full);
    }
  }
  return out;
}

/**
 * Parse flat rule blocks out of one file's `<style>` content.
 *
 * Comments are stripped first: a `:hover` inside an explanatory comment is
 * prose, and several components in this repository explain their hover
 * treatment at length directly above the rule.
 */
function parseRules(css: string, file: string): Rule[] {
  const stripped = css.replace(/\/\*[\s\S]*?\*\//g, '');
  const rules: Rule[] = [];
  // Flat `selector-list { declarations }` blocks. Nested at-rule bodies are
  // reached because their inner rules match this shape too.
  for (const m of stripped.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const selectors = m[1]
      .split(',')
      .map((s) => s.replace(/\s+/g, ' ').trim())
      .filter(Boolean);
    if (!selectors.length) continue;
    // An at-rule preamble (`@media (...)`) is not a selector list.
    if (selectors.some((s) => s.startsWith('@'))) continue;
    const declarations: Record<string, string> = {};
    for (const decl of m[2].split(';')) {
      const i = decl.indexOf(':');
      if (i === -1) continue;
      declarations[decl.slice(0, i).trim()] = decl.slice(i + 1).trim();
    }
    rules.push({ selectors, declarations, file });
  }
  return rules;
}

/** Every rule in every non-test `.astro` file under `web/src`. */
export function allRules(): Rule[] {
  const rules: Rule[] = [];
  for (const path of astroFiles(SRC)) {
    const file = relative(SRC, path);
    for (const m of readFileSync(path, 'utf8').matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)) {
      rules.push(...parseRules(m[1], file));
    }
  }
  return rules;
}

/**
 * A hover selector whose rule also carries the same selector WITHOUT `:hover`
 * is a state lock, not a hover affordance: the declarations apply whether or
 * not a pointer is there, and `:hover` is present only to out-rank a competing
 * rule. `.install-copy-btn--success` is the case on this surface — the button
 * holds its confirmed look while the pointer is still on it.
 *
 * This is decided by the shape of the rule, never by matching a class name, so
 * a second state lock added later is admitted without editing this file.
 */
function isStateLock(rule: Rule, hoverSelector: string): boolean {
  const withoutHover = hoverSelector.replace(/:hover\b/g, '').replace(/\s+/g, ' ').trim();
  return rule.selectors.some((s) => s !== hoverSelector && s === withoutHover);
}

/**
 * Every control that styles a hover state, paired with the press selector that
 * must exist for it. Derived, never listed.
 */
export function hoverControls(rules: Rule[] = allRules()): Control[] {
  const controls: Control[] = [];
  const seen = new Set<string>();
  for (const rule of rules) {
    for (const selector of rule.selectors) {
      if (!/:hover\b/.test(selector)) continue;
      if (isStateLock(rule, selector)) continue;
      const key = `${rule.file}::${selector}`;
      if (seen.has(key)) continue;
      seen.add(key);
      controls.push({
        hoverSelector: selector,
        pressSelector: selector.replace(/:hover\b/g, ':active'),
        ...targets(selector),
        file: rule.file,
      });
    }
  }
  return controls;
}

/** Every selector that appears on a rule, keyed by file. */
export function selectorsByFile(rules: Rule[] = allRules()): Map<string, Set<string>> {
  const map = new Map<string, Set<string>>();
  for (const rule of rules) {
    if (!map.has(rule.file)) map.set(rule.file, new Set());
    const set = map.get(rule.file)!;
    for (const s of rule.selectors) set.add(s);
  }
  return map;
}

/** Every rule whose selector list contains an `:active` selector. */
export function pressRules(rules: Rule[] = allRules()): Rule[] {
  return rules.filter((r) => r.selectors.some((s) => /:active\b/.test(s)));
}

/* ── Colour resolution ─────────────────────────────────────────────────────
 * The guard has to answer "would this ground drop that text below 4.5:1?".
 * That needs real colours, so the token graph is resolved here rather than
 * restated as a table someone has to keep in step with `tokens.css`.
 */

const TOKENS_CSS = resolve(SRC, 'styles/tokens.css');

/** `--token` → its declared value, first declaration wins (the `:root` base). */
function tokenTable(): Map<string, string> {
  const css = readFileSync(TOKENS_CSS, 'utf8').replace(/\/\*[\s\S]*?\*\//g, '');
  const table = new Map<string, string>();
  for (const m of css.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
    if (!table.has(m[1])) table.set(m[1], m[2].trim());
  }
  return table;
}
const TOKENS = tokenTable();

/**
 * Follow a `var()` chain to a literal colour. Returns null for a value that is
 * not a colour, or a chain that leaves the token graph — a null is "unknown",
 * and every caller treats unknown as "do not claim this is safe".
 */
export function resolveColor(value: string | undefined, depth = 0): string | null {
  if (!value || depth > 8) return null;
  const v = value.trim();
  const m = /^var\(\s*(--[\w-]+)\s*(?:,\s*([\s\S]+))?\)$/.exec(v);
  if (m) {
    const direct = TOKENS.has(m[1]) ? resolveColor(TOKENS.get(m[1]), depth + 1) : null;
    // A fallback is what renders when the custom property is not set on the
    // carrier, which is the normal case for a parameterised component.
    return direct ?? (m[2] ? resolveColor(m[2], depth + 1) : null);
  }
  if (/^#[0-9a-f]{6}$/i.test(v)) return v.toLowerCase();
  if (/^#[0-9a-f]{3}$/i.test(v)) return `#${v[1]}${v[1]}${v[2]}${v[2]}${v[3]}${v[3]}`.toLowerCase();
  return null;
}

function channel(c: number): number {
  const s = c / 255;
  return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
}

/** WCAG relative luminance. */
export function luminance(hex: string): number {
  const h = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map((i) => channel(parseInt(h.slice(i, i + 2), 16)));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** WCAG contrast ratio. */
export function contrast(a: string, b: string): number {
  const [x, y] = [luminance(a), luminance(b)];
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}

/** WCAG 1.4.3 Contrast (Minimum), normal text. */
export const TEXT_FLOOR = 4.5;

/** A ground this dark carries light text, so a press must continue into ink. */
const INK_GROUND_MAX_LUMINANCE = 0.15;

/**
 * The value a selector ends up with for one property.
 *
 * Resolution is per PROPERTY, not per rule. Taking the last matching rule
 * instead hides a declaration behind any later rule for the same selector that
 * does not set it — and every responsive component here has one, because a
 * `@media` block re-states the selector to change its layout. That read makes
 * `.write-confirmation__confirm` look like it declares no colour, which would
 * have skipped the contrast check on one of the two controls this guard exists
 * to catch.
 */
function declaredValue(
  rules: Rule[],
  file: string,
  selector: string,
  property: string
): string | undefined {
  let value: string | undefined;
  for (const rule of rules) {
    if (rule.file !== file || !rule.selectors.includes(selector)) continue;
    if (property in rule.declarations) value = rule.declarations[property];
  }
  return value;
}

/**
 * The colour the control's text actually is while held. A press co-occurs with
 * hover for pointer input, so the hover rule's colour is what a pressed label
 * renders in — reading the rest colour instead would clear controls that hover
 * has already darkened and fail ones it has not.
 */
export function textUnderPress(control: Control, rules: Rule[]): string | null {
  const base = control.hoverSelector.replace(/:hover\b/g, '').trim();
  return (
    resolveColor(declaredValue(rules, control.file, control.hoverSelector, 'color')) ??
    resolveColor(declaredValue(rules, control.file, base, 'color'))
  );
}

/**
 * The press token a control's own carrier implies — derived from the control,
 * never from a list of class names. A list is what produced "0 of 28" in the
 * backlog and what mis-classified `.decision-chip`, whose hover inverts it to
 * an ink fill and whose light text would have landed on a light ground at
 * 1.30:1.
 */
export function expectedGroundToken(control: Control, rules: Rule[]): (typeof PRESS_TOKENS)[number] {
  const base = control.hoverSelector.replace(/:hover\b/g, '').trim();
  const hoverGround = resolveColor(
    declaredValue(rules, control.file, control.hoverSelector, 'background-color')
  );
  if (hoverGround && luminance(hoverGround) <= INK_GROUND_MAX_LUMINANCE) {
    return '--ds-cta-primary-bg-active';
  }
  // No ink ground of its own: the carrier is read off the text instead. A
  // control whose label is an on-dark ink is sitting on the one dark band.
  const text = textUnderPress(control, rules) ?? resolveColor(
    declaredValue(rules, control.file, base, 'color')
  );
  if (text && luminance(text) > 0.5) return '--ds-surface-pressed-dk';
  return '--ds-surface-pressed';
}

/** The literal colour a press token resolves to. */
export function pressGroundColor(token: string): string | null {
  return resolveColor(`var(${token})`);
}
