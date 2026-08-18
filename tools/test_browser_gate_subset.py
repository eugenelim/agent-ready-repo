#!/usr/bin/env python3
"""The browser gate's spec allowlist, checked against the filesystem.

`site-browser-quality-gate` AC11: required CI must leave the tracked tree clean,
and two of the e2e specs write PNGs into tracked `docs/specs/**/notes/screenshots/`.

Scope is deliberately narrow. `pages.yml` posture — that the gate step exists by
statement equality, is not advisory/conditional/redirected, runs after both builds
and before the artifact upload, and that the path filters cover its inputs — is
owned by `tools/test-pages-workflow.py`, whose mutation self-test forces each of
those assertions to be able to fail. A first draft of this file asserted them with
`in` containment and was measured green against `|| true`, job-level
`continue-on-error`, deleting a path filter from one trigger, and flipping `paths:`
to `paths-ignore:`. Only what the workflow-text matrix cannot reach lives here.

Run: `python3 -m pytest tools/test_browser_gate_subset.py`
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
E2E_DIR = REPO_ROOT / "web" / "src" / "test" / "e2e"
PACKAGE_JSON = REPO_ROOT / "web" / "package.json"
GATE_SCRIPT = "test:e2e:gate"

# Exclusions as reviewable DATA, not as a derived rule. Deriving "excluded because
# it writes" forced every future read-only spec into required CI or forced a
# maintainer to edit the assertion to say why — there was nowhere to record an
# exemption. A reason string is reviewable in a diff; an edited assertion is not.
# Two categories, because they carry different obligations. A write-based exclusion
# must STAY true — if a spec stops writing, its exemption is stale and it belongs
# back in the gate — while a scope-based one is a judgement only a human can re-make.
EXCLUDED_WRITERS: dict[str, str] = {
    "screenshots.spec.ts":
        "writes fixture PNGs into tracked docs/specs/site-ui-primitives/**; AC11 "
        "keeps screenshot capture optional and outside required CI",
    "docs-asides.spec.ts":
        "writes recovery PNGs into tracked "
        "docs/specs/guide-typed-asides-conversion/notes/screenshots/",
}

EXCLUDED_BY_SCOPE: dict[str, str] = {
    "docs-wayfinding.spec.ts":
        "created by and documented in spec/docs-wayfinding-cluster, not owned by "
        "this gate. Its layout-fit assertions (the deck must render on one line, "
        "the title must be <= 48px, elements must sit inside 1440x900) were written "
        "against local font rendering; making them deploy-blocking on a Linux "
        "runner couples the deploy to font-fallback metrics. The docs routes it "
        "covers are already in this gate's matrix at all five widths in both themes "
        "for overflow, axe, fragments and skip-link order. RESIDUAL, stated plainly: "
        "no Makefile line, workflow or package script invokes this file, so it runs "
        "on demand only. This is the same orphan class as the "
        "tools-test-runner-boundary backlog slug, but that slug's scope is "
        "tools/test*.py, so closing it will NOT discharge this file. No register "
        "entry covers orphaned e2e specs today; said here rather than pointed at a "
        "slug that cannot resolve it.",
}

EXCLUDED: dict[str, str] = {**EXCLUDED_WRITERS, **EXCLUDED_BY_SCOPE}

# A call that puts bytes on disk. Matches call syntax, not the bare noun, so a
# comment mentioning screenshots does not count.
_WRITE_CALL_RE = re.compile(
    r"\.screenshot\s*\(|mkdirSync\s*\(|writeFileSync\s*\(|writeFile\s*\("
)


def _subset_files() -> list[str]:
    scripts = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))["scripts"]
    assert GATE_SCRIPT in scripts, f"web/package.json has no {GATE_SCRIPT!r} script"
    return [tok for tok in scripts[GATE_SCRIPT].split() if tok.endswith(".spec.ts")]


def _writes(path: Path) -> bool:
    return _WRITE_CALL_RE.search(path.read_text(encoding="utf-8")) is not None


def test_the_gate_script_names_only_existing_spec_files() -> None:
    files = _subset_files()
    assert files, "the gate script names no spec files"
    missing = [n for n in files if not (E2E_DIR / n).is_file()]
    assert not missing, f"gate script names specs that do not exist: {missing}"


def test_no_spec_in_the_required_subset_writes_files() -> None:
    """AC11: required CI writes no tracked files."""
    writers = [n for n in _subset_files() if _writes(E2E_DIR / n)]
    assert not writers, (
        "these specs write files and must not be in the required subset: "
        f"{writers} — move them to EXCLUDED with a reason, or stop them writing"
    )


def test_the_subset_and_the_exclusions_together_cover_every_spec() -> None:
    """Neither list may silently drop a spec.

    Without this, deleting a spec from the gate script reads as tidying rather than
    as removing deploy-blocking coverage.
    """
    on_disk = {p.name for p in E2E_DIR.glob("*.spec.ts")}
    accounted = set(_subset_files()) | set(EXCLUDED)
    unaccounted = sorted(on_disk - accounted)
    assert not unaccounted, (
        f"e2e specs in neither the gate script nor EXCLUDED: {unaccounted} — add "
        f"each to {GATE_SCRIPT} or to EXCLUDED with a reason"
    )
    stale = sorted(accounted - on_disk)
    assert not stale, f"named but absent from disk: {stale}"


def test_every_write_based_exclusion_is_still_justified_by_a_write() -> None:
    """A write-based exemption must stay true, not just stay written down.

    If a spec stops writing files, its exemption is stale and it belongs back in the
    gate — otherwise the exclusion list becomes a place to park inconvenient tests.
    Scope-based exclusions are exempt from this: their justification is a judgement,
    not a property of the file.
    """
    unjustified = [n for n in EXCLUDED_WRITERS if not _writes(E2E_DIR / n)]
    assert not unjustified, (
        f"these specs no longer write files, so their write-based exclusion is "
        f"stale: {unjustified} — move them into {GATE_SCRIPT}, or into "
        "EXCLUDED_BY_SCOPE with a reason"
    )


def test_every_exclusion_carries_a_reason() -> None:
    """An exclusion with an empty reason is an unreviewable exemption."""
    empty = [n for n, why in EXCLUDED.items() if len(why.strip()) < 20]
    assert not empty, f"exclusions without a substantive reason: {empty}"


def test_the_docs_base_agrees_with_the_docs_site_config() -> None:
    """`site-base.ts` derives DOCS_BASE; the docs renderer configures it.

    They agree today by spelling. Nothing failed if one moved, and a docs base
    change would 404 the 20 docs matrix cases plus two other specs with a bare
    "HTTP status" message and no test predicting it — the exact failure
    `site-base.ts` exists to prevent for the marketing base.
    """
    web_base = re.search(
        r"^\s*base:\s*['\"]([^'\"]+)['\"]",
        (REPO_ROOT / "web" / "astro.config.ts").read_text(encoding="utf-8"),
        re.M,
    )
    docs_base = re.search(
        r"^\s*base:\s*['\"]([^'\"]+)['\"]",
        (REPO_ROOT / "docs-site" / "astro.config.ts").read_text(encoding="utf-8"),
        re.M,
    )
    assert web_base and docs_base, "could not read `base` from both astro configs"
    expected = f"{web_base.group(1).rstrip('/')}/docs"
    assert docs_base.group(1).rstrip("/") == expected, (
        f"docs-site base is {docs_base.group(1)!r} but site-base.ts derives "
        f"{expected!r} from the marketing base — update site-base.ts to read the "
        "docs config, or realign the two"
    )


# ── AC1/AC2's matrix contract ────────────────────────────────────────────────
# The route/width/theme sets ARE the contract. Deleting a marketing route removes
# five cases while every remaining test passes and CI stays green, so the sets and
# the resulting case count are pinned here.
EXPECTED_MARKETING_ROUTES = (
    "/", "/catalogue/", "/packs/core/", "/journeys/", "/journeys/core/",
    "/journeys/product-engineering/", "/journeys/release-engineering/", "/now/",
)
EXPECTED_DOCS_ROUTES = ("/", "/guides/core/how-to/start-a-project/")
EXPECTED_WIDTHS = (360, 375, 390, 414, 1440)
EXPECTED_THEMES = ("light", "dark")
MATRIX_SPEC = REPO_ROOT / "web" / "src" / "test" / "e2e" / "site-quality-gate.spec.ts"


def _array_literal(name: str, text: str) -> list[str]:
    block = re.search(rf"const {name} = \[(.*?)\] as const", text, re.S)
    assert block, f"could not find `const {name} = [...] as const`"
    return re.findall(r"'([^']+)'", block.group(1))


def test_the_matrix_covers_exactly_the_approved_route_sets() -> None:
    text = MATRIX_SPEC.read_text(encoding="utf-8")
    assert tuple(_array_literal("MARKETING_ROUTES", text)) == EXPECTED_MARKETING_ROUTES
    assert tuple(_array_literal("DOCS_ROUTES", text)) == EXPECTED_DOCS_ROUTES


def test_the_widths_and_themes_are_the_approved_sets() -> None:
    text = (REPO_ROOT / "web" / "src" / "test" / "e2e" / "quality-assertions.ts").read_text(
        encoding="utf-8"
    )
    widths = re.search(r"export const WIDTHS = \[([^\]]+)\]", text)
    themes = re.search(r"export const THEMES = \[([^\]]+)\]", text)
    assert widths and themes, "WIDTHS/THEMES not found"
    assert tuple(int(x) for x in re.findall(r"\d+", widths.group(1))) == EXPECTED_WIDTHS
    assert tuple(re.findall(r"'([^']+)'", themes.group(1))) == EXPECTED_THEMES


def test_the_approved_matrix_is_exactly_sixty_cases() -> None:
    """8 marketing x 5 widths + 2 docs x 5 widths x 2 themes = 60 (AC1, AC2)."""
    marketing = len(EXPECTED_MARKETING_ROUTES) * len(EXPECTED_WIDTHS)
    docs = len(EXPECTED_DOCS_ROUTES) * len(EXPECTED_WIDTHS) * len(EXPECTED_THEMES)
    assert marketing == 40, marketing
    assert docs == 20, docs
    assert marketing + docs == 60


# ── Unbound helper identifiers ───────────────────────────────────────────────
# The defect this closes shipped once: `site-quality-gate.spec.ts` CALLED
# `expectVisibleFocusIndicator` without importing it. Playwright transpiles TS but
# does not typecheck, `vitest.config.ts` includes only `src/test/**/*.test.ts` so
# e2e specs are never checked there, and `astro check` needs a dependency this spec
# may not add. The identifier sat inside a branch that only runs when journey chips
# exist, so it would have thrown `ReferenceError` the moment
# journey-page-completion landed — turning six "passing-when-present" cases into
# six errors.
#
# Narrow on purpose: this is not a typechecker. It asserts one property — every
# helper name a spec uses is imported by that spec — which is exactly the class that
# escaped.
HELPERS_MODULE = E2E_DIR / "quality-assertions.ts"
BASE_MODULE = E2E_DIR / "site-base.ts"


def _exported_names(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return set(
        re.findall(r"^export (?:async function|function|const) (\w+)", text, re.M)
    )


def _imported_names(text: str, module: str) -> set[str]:
    block = re.search(
        rf"import\s*\{{([^}}]*)\}}\s*from\s*'\./{re.escape(module)}'", text, re.S
    )
    if not block:
        return set()
    return {
        part.strip().split(" as ")[-1].strip()
        for part in block.group(1).split(",")
        if part.strip() and not part.strip().startswith("type ")
    }


def test_every_helper_a_spec_uses_is_imported_by_that_spec() -> None:
    # Asserted per module, not on the union. Unioning let an export-style change in
    # one file (a bottom `export { … }` block, a default export) empty its half while
    # the other kept the assert green — measured: the guard then passed having checked
    # zero helper names.
    helpers = _exported_names(HELPERS_MODULE)
    base = _exported_names(BASE_MODULE)
    assert helpers, f"no exported names parsed from {HELPERS_MODULE.name}"
    assert base, f"no exported names parsed from {BASE_MODULE.name}"
    exported = helpers | base

    problems: list[str] = []
    for spec in sorted(E2E_DIR.glob("*.spec.ts")):
        text = spec.read_text(encoding="utf-8")
        imported = _imported_names(text, "quality-assertions") | _imported_names(
            text, "site-base"
        )
        # Strip the import block itself before looking for uses, so an imported name
        # does not count as its own use.
        body = re.sub(r"import\s*\{[^}]*\}\s*from\s*'[^']*';", "", text, flags=re.S)
        for name in exported:
            if re.search(rf"\b{re.escape(name)}\s*\(", body) and name not in imported:
                problems.append(f"{spec.name} calls {name}() without importing it")
    assert not problems, "\n".join(problems)
