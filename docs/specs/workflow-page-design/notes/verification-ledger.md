# Verification ledger

## 2026-09-26 — managed-profile limitation

Scope: T3 source tests and T4 rendered verification.

`make site-link-check` cannot complete in this managed session because the web build tries to remove `web/node_modules/.vite/deps` and the active permission profile returns:

```text
EPERM: operation not permitted, rmdir '.../web/node_modules/.vite/deps'
```

The implementing agent retried the site-link command once and made one direct `rmdir` attempt; both received the same policy denial. Do not retry or mutate this cache in this profile.

This is an environment limitation, not passing evidence for the source change. The full site build, rendered-link check, and Playwright checks remain required in a supported profile. Unaffected documentation linters, source checks, and Python lint/type checks still run locally. The browser handoff covers the rendered routes and viewport matrix.

The standalone docs build also reached Astro content sync and build setup, then received the same denial while Astro tried to remove `docs-site/.astro/.prerender/.vite/`. It was not retried. A TypeScript probe was unavailable because this checkout has no local `tsc`; `npx` attempted a registry download and failed against the enterprise certificate chain. No dependency was installed.

Unaffected checks passed:

- `python3 tools/validate_guides.py`: 230 checked, 6 exempt.
- `python3 tools/check-guide-index.py`: all 21 active packs present.
- `python3 tools/lint-guide-titles.py`: 236 files.
- `python3 tools/lint-guidebook-steps.py guides/core`: one guidebook directory.
- `make lint-ruff lint-mypy`: Ruff clean; mypy clean across 149 source files.

Additional unaffected checks passed:

- `python3 .agents/skills/new-spec/scripts/lint-contract-item-alignment.py --no-since docs/specs/workflow-page-design`: 0 findings; one expected partial rule, `stale-assertion (--no-since)`.
- `git diff --check`: clean.

## 2026-09-26 — rendered-verification handoff

Scope: T4 browser and built-site evidence for AC-0011, AC-0012, AC-0014, and AC-0015.

Codex cannot produce final rendered evidence in this managed profile because the canonical build path reaches generated-cache cleanup operations that the active policy denies. The supported-browser handoff is `.context/claude-rendered-verification-prompt.md`; it instructs a Chromium-capable profile to:

- run the canonical docs/link/source gates;
- serve `build/` so the `/agent-ready-repo` base path resolves;
- inspect `/agent-ready-repo/docs/` and `/agent-ready-repo/docs/guides/core/how-to/start-or-remember-work/` in light and dark themes at `480x600`, `480x900`, `1024x600`, and `1024x900`;
- record an at-rest `scrollY = 0` capture plus a scrolled capture or `page-scrollable: no` for each route, theme, and viewport;
- run the `375x812` overflow, focus, contrast, accessibility, primary-link, modified-link, and anchor checks; and
- replace `.context/claude-rendered-verification-result.md` with the concise evidence report.

The handoff is verification-only. It tells the verifier not to change source unless it finds and reports a concrete defect, and then only to apply the smallest source fix and rerun affected checks.

## 2026-09-26 — exact Playwright gate follow-up

The first exact `docs-wayfinding.spec.ts` run passed all four 375px accessibility cases and failed both 1440×900 theme cases because the homepage deck occupied two lines; the contract expects fewer than 1.5 lines. The deck was shortened to `Shape an idea or build a known change. The final decision stays human.` and the matching test assertion was updated. A fresh site build and exact-suite rerun are required after this source fix.

The rebuilt site then passed its link gate, and the corrected exact-suite launch passed all four mobile cases. Both desktop cases showed the first supporting card ending about 97px below the 900px viewport. The captured page showed repeated explanatory copy inside the two primary cards. The home introduction and primary-card descriptions were shortened, preserving the two decisions while removing that duplication. A fresh build and exact-suite rerun remain required.

Final rerun:

- `make site-link-check`: 266 docs pages built; 96,524 links across 495 pages clean.
- `npm exec playwright test docs-wayfinding.spec.ts` from `web/`: 6 passed in 16.8s, covering both 1440×900 themes and both routes in both themes at 375×812.
- No remaining execution-gate finding.

Post-gates adversarial review found two cleanup issues. The homepage rendered-output test still pinned the deleted phrase `Use this when`, and its closed-set selector included global site chrome. The stale prose checks were removed; the link selector now covers hero and article-content links while excluding generated heading permalinks. `npm test --prefix web -- rendered-output.test.ts` then passed all 65 tests in 88.57s. Root-level Playwright artifacts from a mis-launched run were untracked and were deleted; only empty policy-protected directories remain, which Git does not track.
