# Mutation proof — the print guard fails when the rule is removed

- **Status:** Accepted — measured 2026-08-25
- **Owner:** eugenelim
- **Discharges:** `spec.md` AC4
- **Guard under test:** `web/src/test/e2e/site-quality-gate.spec.ts`
  § `docs footer navigation is suppressed in print`

A guard that has not been shown to fail is not evidence. This records both states,
with the rebuild between them, because the gate serves `build/` — mutating the
source without rebuilding proves nothing and reports green.

## Method

The mutation removes the `@media print` block from
`docs-site/src/components/Footer.astro`, leaving everything else — including the
comment above it — untouched. The removal is asserted before it is applied: the
script fails closed if its anchor no longer matches, so a stale anchor cannot
silently report a pass.

Between states, the full build runs in its mandated order:

```
python3 tools/build-site.py
npm run build --prefix web
npm run build --prefix docs-site
```

## State 1 — rule removed, site rebuilt: guard FAILS

Emitted CSS check first, confirming the mutation reached the artifact:

```
$ grep -c '@media print{.docs-site-footer__groups' build/docs/_astro/common.*.css
0
```

Guard output:

```
  2 failed
    [chromium] › site-quality-gate.spec.ts:833:5 › docs footer navigation is suppressed in print
      › / footer groups print:none screen:grid @717
    [chromium] › site-quality-gate.spec.ts:833:5 › docs footer navigation is suppressed in print
      › /guides/core/how-to/start-a-project/ footer groups print:none screen:grid @717

  > 854 |       expect(inPrint, `${route}: footer groups must not print`).toBe('none');
```

Both routes fail, on the print assertion, reporting the defect this spec fixes.
The screen assertion passes in this state — which is the point of asserting both:
a fix that hid the groups everywhere would fail there instead.

## State 2 — rule restored, site rebuilt: guard PASSES

```
$ grep -o '@media print{[^}]*docs-site-footer__groups[^}]*}' build/docs/_astro/*.css
build/docs/_astro/common.tNuIgDna.css:@media print{.docs-site-footer__groups:where(.astro-jo6i4kqk){display:none}
```

Full gate, unfiltered:

```
$ npm run test:e2e:gate --prefix web
  ✓ 182 › docs footer navigation is suppressed in print › /guides/core/how-to/start-a-project/ …
  ✓ 181 › docs footer navigation is suppressed in print › / footer groups print:none screen:grid @717

  182 passed (1.2m)
```

180 pre-existing cases plus the two new ones. The 60-case matrix is unchanged.

## What this proves, and what it does not

**Proves:** the guard discriminates on the rule it names. Remove the rule and it
goes red on the print assertion specifically, not on setup, navigation, or the
screen assertion.

**Does not prove:** that no other change could make it green — a mutation proof is
a lower bound on a guard's sensitivity, not a completeness argument. It also says
nothing about page-break quality or about which other chrome paints, neither of
which this spec measures.
