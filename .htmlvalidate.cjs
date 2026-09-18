/**
 * html-validate configuration for the emitted marketing site (`build/`, built
 * from `web/`). CommonJS rather than JSON so every exception can carry its
 * reason next to the entry: the rule set is the one place where "why is this
 * allowed?" must be answerable without archaeology, and JSON has no comments.
 *
 * Canonical invocation:
 *   npx html-validate --preset standard,a11y --max-warnings 0 'build/**\/*.html'
 *
 * `build/docs/` (the docs-site Starlight output, a separate surface) is held
 * out by `.htmlvalidateignore`, not by anything here.
 *
 * `extends` below is NOT redundant with that `--preset` flag, and removing it
 * silently guts the run. Once ANY `.htmlvalidate.*` file resolves for a target,
 * html-validate uses that file as the base configuration and the CLI `--preset`
 * is never applied. A config that sets only `rules` therefore inherits NO
 * preset: `aria-label-misuse`, `prefer-native-element` and `no-implicit-button-
 * type` all stop reporting and the run goes green while checking almost
 * nothing. Verified by probe, 2026-09-18. Keep these two lists in step with the
 * documented command.
 */
module.exports = {
  // Stop the loader walking above the repository into the developer's home
  // directory, where a stray config would make results differ per machine.
  root: true,

  extends: ['html-validate:standard', 'html-validate:a11y'],

  rules: {
    /*
     * no-redundant-role — exempt the role keyword "list", and nothing else.
     *
     * What it protects: list semantics in Safari with VoiceOver.
     * `web/src/styles/base.css` applies `list-style: none` to every `ul`/`ol`
     * as a global reset. Safari removes list semantics from a list styled that
     * way — VoiceOver stops announcing "list, N items" and stops announcing
     * each item's position within it. Restating the implicit role explicitly
     * (`<ul role="list">`) puts both back. The role is redundant against the
     * HTML specification and load-bearing against the browser that ships, and
     * the browser is what a reader actually uses.
     *
     * Why this is calibration and not a waiver: `exclude` matches the ROLE
     * VALUE. The rule still errors on `role="button"` on a `<button>`,
     * `role="navigation"` on a `<nav>`, `role="main"` on a `<main>`,
     * `role="region"` on a named `<section>`, `role="listitem"` on an `<li>`,
     * and every other redundant role. It caught a genuine `role="region"` on
     * `<section>` in `WriteConfirmation.astro` on the first run after this
     * entry was added, which was then fixed rather than exempted.
     *
     * Known limit, stated rather than hidden: keying on the role value also
     * exempts `role="list"` on an element that is not a `ul`/`ol` — say
     * `<menu role="list">`. That gap is covered by
     * `web/src/test/list-semantics.test.ts`; see the entry below, which
     * amends what this paragraph used to claim.
     *
     * Remove this entry when Safari preserves list semantics under
     * `list-style: none`, or when `base.css` stops suppressing markers
     * globally.
     */
    'no-redundant-role': ['error', { exclude: ['list'] }],

    /*
     * prefer-native-element — exempt the role keyword "list", and nothing else.
     *
     * WHY, and it is a limitation of the rule rather than of the markup: the
     * rule holds ONE native element per role in a fixed mapping, and for
     * "list" that element is `ul`. HTML has two list elements. So the moment
     * an `<ol>` carries the Safari workaround above, this rule reports
     * "Prefer to use the native <ul> element" on markup that is already the
     * correct native element — seven times across the built site on
     * 2026-09-18, every one of them an `<ol role="list">`.
     *
     * The three ways out, and why this is the one taken:
     *   - Drop the role from the `<ol>`s. Rejected: Safari drops list
     *     semantics from an `<ol>` styled `list-style: none` exactly as it
     *     does from a `<ul>`, and on an ordered list what is lost is position
     *     in a sequence, which is the more load-bearing of the two.
     *   - Re-point the mapping at `ol`. Rejected: it moves the false report
     *     onto every `<ul>`, which is most of them.
     *   - Exempt the keyword and replace the check locally. Taken.
     *
     * WHAT REPLACES THE CHECK. This exemption costs the one thing the entry
     * above used to lean on: `prefer-native-element` catching a list role on
     * a generic element, `<div role="list">`. That paragraph has been amended
     * rather than left standing, because a stale "something else covers it"
     * is worse than no claim. The cover is now
     * `web/src/test/list-semantics.test.ts`, which asserts that every
     * `role="list"` in `web/src` sits on a `ul` or an `ol` — strictly
     * stronger than the linter here, because it admits both native list
     * elements and this rule can only name one.
     *
     * Retire this entry together with the one above and that test; all three
     * rest on the same premise, and one of them going alone leaves either a
     * false report or an unguarded gap.
     */
    'prefer-native-element': ['error', { exclude: ['list'] }],
  },
};
