#!/usr/bin/env python3
"""The browser gate's spec allowlist, plus the site files' must-stay-in-relation values.

`site-browser-quality-gate` AC11: required CI must leave the tracked tree clean,
and two of the e2e specs write PNGs into tracked `docs/specs/**/notes/screenshots/`.

A further resident class — alongside the AC1/AC2 matrix contract, the
unbound-helper-identifier check and the tap-target audit arithmetic below — is a
value that tracked site files must keep in a fixed relation, where nothing else
would notice them diverging: the `base` the docs config must derive from the
marketing one, and the `@astrojs/markdown-remark` version that
`docs-site/package.json`, the lockfile and astro's optional peer must agree on.
They live here because this module runs from `gate-main`, a required context;
`pages.yml` is not one, so a pin gate placed there could not block the merge that
broke it.

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
        "on demand only. The tools/test*.py runner discipline does not reach it: "
        "that scope covers tools/test*.py, and no runner there can discharge an "
        "e2e spec.",
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


MARKDOWN_REMARK = "@astrojs/markdown-remark"
EXACT_VERSION = re.compile(r"\d+\.\d+\.\d+")
CARET_RANGE = re.compile(r"\^(\d+)\.(\d+)\.(\d+)")


def _docs_site_versions() -> dict[str, str | None]:
    """Every recorded copy of the `@astrojs/markdown-remark` version, and astro's.

    Missing values come back as ``None`` rather than raising. The drift shape this
    guards has already occurred in the exact form of an ABSENT key — at #1036's
    head 6990d3d7, `docs-site/package.json` declared no `@astrojs/markdown-remark`
    at all — and a `KeyError` traceback would replace the remediation text the
    assertions exist to deliver.

    `@astrojs/mdx` is a fifth recorder and is deliberately absent: it requires
    `@astrojs/markdown-remark` through its own `dependencies`, not a peer, so an
    mdx divergence nests a private copy under `@astrojs/mdx/node_modules/` and
    leaves the ROOT slot — the only placement `astro.config.ts` can import from —
    untouched. Comparing it would fail on a difference that cannot break this
    build. Do not add it back without re-deriving that argument.
    """
    site = REPO_ROOT / "docs-site"
    manifest = json.loads((site / "package.json").read_text(encoding="utf-8"))
    packages = json.loads((site / "package-lock.json").read_text(encoding="utf-8"))
    packages = packages.get("packages", {})
    deps = manifest.get("dependencies", {})
    root = packages.get("", {}).get("dependencies", {})
    astro = packages.get("node_modules/astro", {})
    starlight = packages.get("node_modules/@astrojs/starlight", {})
    return {
        "manifest_pin": deps.get(MARKDOWN_REMARK),
        "lock_root_pin": root.get(MARKDOWN_REMARK),
        "installed": packages.get(f"node_modules/{MARKDOWN_REMARK}", {}).get("version"),
        "astro_peer": astro.get("peerDependencies", {}).get(MARKDOWN_REMARK),
        "manifest_astro": deps.get("astro"),
        "installed_astro": astro.get("version"),
        "starlight_peer": starlight.get("peerDependencies", {}).get(MARKDOWN_REMARK),
        "starlight_version": starlight.get("version"),
    }


def test_the_markdown_remark_pin_equals_astros_optional_peer() -> None:
    """One `@astrojs/markdown-remark` version, agreed by all four files recording it.

    astro declares it an *optional* peer at an exact version, so npm neither
    installs it nor complains when the two drift — but `astro.config.ts` needs it
    resolvable at the root, and a mismatched copy is a resolution failure at build
    time, not an install-time warning. The duty to move both together was prose in
    `docs-site/AGENTS.md` that no gate read.

    Read from the lockfile rather than `node_modules/astro/package.json`: this
    module runs in `gate-main`, which installs no Node, and a check that skips
    itself in the job most PRs actually run is not a check.

    All four recorded copies are compared, not just the manifest against the peer.
    `npm ci` would refuse a lockfile that disagrees with the manifest — but `npm
    ci` runs in `build`, which is not a required context, and that is the same
    argument that puts this test here rather than in `node_modules`. It cannot be
    used to justify reading the lockfile and then to excuse trusting it.
    """
    v = _docs_site_versions()

    # The two absences mean opposite things and need opposite first moves.
    assert v["manifest_pin"] is not None, (
        f"docs-site/package.json declares no `{MARKDOWN_REMARK}`. The declaration "
        "is what makes root placement a requirement rather than a hoisting "
        "accident (docs-site/AGENTS.md § Action-changing traps) — restore it, or "
        "delete this test with a reason if the duty genuinely ended."
    )
    assert v["astro_peer"] is not None, (
        f"astro {v['installed_astro']} no longer declares `{MARKDOWN_REMARK}` as a "
        "peer. This is the arrival docs-site/AGENTS.md predicts, and it is NOT a "
        "signal to delete this test: run `npm run build --prefix docs-site` and "
        "check whether astro.config.ts's markdown configuration still validates "
        "before concluding anything about the duty."
    )

    # Exact equality is the whole contract. A range on any of the three means the
    # premise changed, and "make them equal" would be the wrong instruction.
    for key, what in (
        ("manifest_pin", "the markdown-remark pin"),
        ("astro_peer", "astro's declared peer"),
        ("manifest_astro", "the astro pin"),
    ):
        assert EXACT_VERSION.fullmatch(v[key] or ""), (
            f"{what} is {v[key]!r}, not an exact version. This test asserts exact "
            "equality because astro declared an exact optional peer; a range means "
            "that premise no longer holds and the check needs re-deriving, not "
            "loosening."
        )

    # The peer range is evidence about the pinned astro only if the lockfile still
    # describes that astro.
    assert v["installed_astro"] == v["manifest_astro"], (
        f"docs-site/package.json pins astro {v['manifest_astro']!r} but the lockfile "
        f"resolves {v['installed_astro']!r} — regenerate docs-site/package-lock.json"
    )

    agreed = {
        "docs-site/package.json": v["manifest_pin"],
        "package-lock.json root dependencies": v["lock_root_pin"],
        "package-lock.json resolved version": v["installed"],
        f"astro {v['installed_astro']} optional peer": v["astro_peer"],
    }
    assert len(set(agreed.values())) == 1, (
        f"the four recorded `{MARKDOWN_REMARK}` versions disagree: "
        + ", ".join(f"{where} = {ver!r}" for where, ver in agreed.items())
        + " — they move together, or `astro build` fails to resolve the package "
        "astro.config.ts imports"
    )


def test_starlight_also_accepts_the_markdown_remark_pin() -> None:
    """astro is not the only optional-peer consumer; Starlight is the other.

    Starlight declares a *range* where astro declares an exact version, so a
    Starlight bump can move its floor while astro stays put — leaving the pin
    equal to astro's peer, this site's other guard green, and Starlight's
    requirement unsatisfied. Checking only astro would miss it.

    Caret satisfaction is computed here rather than pulled from a semver library:
    this module is stdlib-only by construction, it runs in a required job, and a
    test that can fail on a missing import is one someone import-guards under
    pressure. Any range shape other than a caret on a non-zero major fails loudly
    instead of being approximated.
    """
    v = _docs_site_versions()
    # Guard the early return: "Starlight is installed and stopped declaring the
    # peer" is the only world that may pass vacuously. A missing Starlight entry,
    # or a changed key shape, would otherwise retire this check silently.
    assert v["starlight_version"] is not None, (
        "docs-site/package-lock.json records no `node_modules/@astrojs/starlight` "
        "— either Starlight is gone, in which case delete this test, or the "
        "lockfile's key shape changed and this check is reading the wrong place."
    )
    spec = v["starlight_peer"]
    if spec is None:
        return  # Starlight stopped declaring it; astro's exact peer is the contract.

    caret = CARET_RANGE.fullmatch(spec)
    assert caret, (
        f"Starlight {v['starlight_version']} declares `{MARKDOWN_REMARK}` as "
        f"{spec!r}, which is not the `^X.Y.Z` shape this check understands — "
        "re-derive the comparison rather than widening it to pass."
    )
    floor = tuple(int(g) for g in caret.groups())
    assert floor[0] != 0, (
        f"Starlight's range {spec!r} is a caret on major 0, where caret semantics "
        "pin the minor instead of the major — re-derive this comparison."
    )
    pin = v["manifest_pin"] or ""
    assert EXACT_VERSION.fullmatch(pin), f"the pin is {pin!r}, not an exact version"
    got = tuple(int(part) for part in pin.split("."))
    assert got[0] == floor[0] and got >= floor, (
        f"docs-site pins `{MARKDOWN_REMARK}` {pin!r}, which does not satisfy "
        f"Starlight {v['starlight_version']}'s declared range {spec!r} — a "
        "Starlight bump moved the floor and the pin has to follow it too, not "
        "only astro's exact peer"
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


# --- Tap-target audit arithmetic -------------------------------------------------
#
# The audit states its candidate count in prose, in three group headings, and in a
# classification table, and an earlier revision left two of those disagreeing. The
# document used to promise in prose that the number lived in one place; a promise is
# not a check. These two tests are the check: every group heading must match the rows
# beneath it, the table cells must match the headings, and the total must be their
# sum. Reclassify one candidate and exactly one edit keeps this green.

TAP_TARGET_AUDIT = (
    REPO_ROOT / "docs" / "specs" / "site-browser-quality-gate" / "notes" /
    "docs-tap-target-audit.md"
)
_GROUP_RE = re.compile(r"^### (?P<name>.+?) — (?P<count>\d+) candidates\s*$")
_TOTAL_RE = re.compile(r"^\|\s*\*\*Total classified\*\*\s*\|\s*(?P<total>\d+)\s*\|")
# The prose figure in § Evidence availability: "resolve to **56 distinct candidates**".
_PROSE_TOTAL_RE = re.compile(r"\*\*(?P<total>\d+) distinct\s+candidates\*\*")
# `| Inline-content exception (SC 2.5.8, Inline) | 29 | Measured 2026-08-18 |`
_CELL_RE = re.compile(r"^\|\s*(?P<name>[^|*]+?)\s*\|\s*(?P<count>\d+)\s*\|\s*\S")


def _cell_name(name: str) -> str:
    """Cell labels carry a criterion reference the group headings do not."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()


def _classification_cells(text: str) -> list[tuple[str, int]]:
    """Every cell, in order, duplicates included.

    A dict silently kept the last row for a repeated name, so inserting a second
    `Spacing exception` cell reading 99 left every assertion green while the visible
    column summed to 140 against a total of 56.
    """
    cells: list[tuple[str, int]] = []
    # Scoped to the one section, because the file holds other `| name | 0 | ... |`
    # tables — the AC5 defect register among them — and an unscoped parse pulled four
    # of its rows in as classifications.
    in_section = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_section = line.strip() == CLASSIFICATION_HEADING
            continue
        if not in_section or not line.startswith("|"):
            continue
        # The separator, the header row and the total row are not classifications.
        if _SEPARATOR_RE.match(line) or _HEADER_ROW_RE.match(line) or _TOTAL_RE.match(line):
            continue
        match = _CELL_RE.match(line)
        # Unmatched table rows FAIL rather than being skipped. The previous form
        # excluded any row whose first cell began with a backtick, so a cell written
        # `| \`Spacing exception\` (…) | 99 |` was silently dropped from the sum while
        # reading 99 on the page.
        assert match, (
            f"{TAP_TARGET_AUDIT.name}: unparsed row in {CLASSIFICATION_HEADING!r}: "
            f"{line.strip()!r}"
        )
        cells.append((_cell_name(match.group("name")), int(match.group("count"))))
    return cells


CLASSIFICATION_HEADING = "## Final shaping classification and exemption table"
_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|\s*$")
_HEADER_ROW_RE = re.compile(r"^\|\s*Classification\s*\|")

# Classes the audit carries at zero: real criterion outcomes with no evidence group
# of their own. Enumerated, so a cell that is neither a group nor one of these is a
# parse error rather than something the checks quietly skip.
ZERO_CLASSES = frozenset(
    {
        "Demonstrated non-exempt failure",
        "User-agent/framework-controlled exception",
        "Equivalent-control exception",
        "Essential exception",
    }
)


def _audit_groups() -> dict[str, tuple[int, int]]:
    """Map group name -> (count claimed in its heading, rows actually beneath it)."""
    groups: dict[str, tuple[int, int]] = {}
    current: str | None = None
    for line in TAP_TARGET_AUDIT.read_text(encoding="utf-8").splitlines():
        match = _GROUP_RE.match(line)
        if match:
            current = match.group("name")
            groups[current] = (int(match.group("count")), 0)
            continue
        if line.startswith("## "):
            current = None
            continue
        if current and line.startswith("| `"):
            claimed, rows = groups[current]
            groups[current] = (claimed, rows + 1)
    return groups


def test_every_group_heading_matches_the_rows_beneath_it() -> None:
    groups = _audit_groups()
    assert groups, f"no `### ... — N candidates` groups parsed from {TAP_TARGET_AUDIT.name}"
    for name, (claimed, rows) in groups.items():
        assert claimed == rows, (
            f"{TAP_TARGET_AUDIT.name}: group '{name}' heading claims {claimed} "
            f"candidates but {rows} evidence rows follow it"
        )


def test_the_classification_total_is_the_sum_of_its_group_cells() -> None:
    text = TAP_TARGET_AUDIT.read_text(encoding="utf-8")
    groups = _audit_groups()
    totals = [
        int(m.group("total")) for m in (_TOTAL_RE.match(ln) for ln in text.splitlines()) if m
    ]
    assert len(totals) == 1, (
        f"{TAP_TARGET_AUDIT.name}: expected exactly one **Total classified** cell "
        f"carrying a number, found {len(totals)}"
    )
    expected = sum(claimed for claimed, _ in groups.values())
    assert totals[0] == expected, (
        f"{TAP_TARGET_AUDIT.name}: **Total classified** says {totals[0]} but the "
        f"group headings sum to {expected}"
    )
    # And against the cells themselves, which is what a reader adds up. Comparing
    # only to the headings left the table's own arithmetic unguarded: a zero class
    # edited off zero, or a duplicated row, changed the visible column and nothing
    # failed.
    cell_total = sum(count for _name, count in _classification_cells(text))
    assert cell_total == totals[0], (
        f"{TAP_TARGET_AUDIT.name}: the classification cells sum to {cell_total} but "
        f"**Total classified** says {totals[0]}"
    )


def test_the_prose_candidate_count_matches_the_classification_total() -> None:
    """The one copy of the total that nothing read.

    Deleting a whole group — heading, evidence rows and cell — and lowering the total
    row to match left all other assertions green while the prose still claimed the old
    figure, so candidates could leave the record with the document self-contradicting.
    """
    text = TAP_TARGET_AUDIT.read_text(encoding="utf-8")
    prose = _PROSE_TOTAL_RE.findall(text)
    assert len(prose) == 1, (
        f"{TAP_TARGET_AUDIT.name}: expected exactly one '**N distinct candidates**' "
        f"prose figure, found {len(prose)}"
    )
    totals = [
        int(m.group("total")) for m in (_TOTAL_RE.match(ln) for ln in text.splitlines()) if m
    ]
    assert len(totals) == 1, f"{TAP_TARGET_AUDIT.name}: expected one total cell"
    assert int(prose[0]) == totals[0], (
        f"{TAP_TARGET_AUDIT.name}: prose says {prose[0]} distinct candidates but "
        f"**Total classified** says {totals[0]}"
    )


def test_each_classification_cell_matches_its_own_group_heading() -> None:
    """Bound BY NAME, not by membership.

    An earlier form asserted only that the number appeared somewhere in a cell, so
    swapping the two Spacing cells — misattributing hover-revealed against plain —
    left every assertion green, and a group that fell to 0 was satisfied by the
    unrelated `| 0 |` rows already in the table.
    """
    text = TAP_TARGET_AUDIT.read_text(encoding="utf-8")
    cells = _classification_cells(text)
    assert cells, f"no classification-table cells parsed from {TAP_TARGET_AUDIT.name}"
    names = [name for name, _count in cells]
    assert len(names) == len(set(names)), (
        f"{TAP_TARGET_AUDIT.name}: duplicated classification cell(s): "
        f"{sorted({n for n in names if names.count(n) > 1})}"
    )
    by_name = dict(cells)
    # Heading names go through the same normalization as cell names, so a heading
    # that gains a criterion parenthetical reports a mismatch rather than 'no cell'.
    groups = {_cell_name(name): claimed for name, (claimed, _rows) in _audit_groups().items()}
    for name, claimed in groups.items():
        assert name in by_name, (
            f"{TAP_TARGET_AUDIT.name}: group '{name}' has no classification-table "
            f"cell of its own (cells found: {sorted(by_name)})"
        )
        assert by_name[name] == claimed, (
            f"{TAP_TARGET_AUDIT.name}: group '{name}' heading claims {claimed} but "
            f"its classification cell says {by_name[name]}"
        )
    for name, count in cells:
        if name in groups:
            continue
        assert name in ZERO_CLASSES, (
            f"{TAP_TARGET_AUDIT.name}: classification cell '{name}' matches no group "
            f"heading and is not an enumerated zero class"
        )
        assert count == 0, (
            f"{TAP_TARGET_AUDIT.name}: '{name}' carries no evidence group, so its "
            f"cell must be 0, not {count}"
        )
    # Presence, not just permission: membership alone let a criterion class be
    # DELETED from the record with every assertion still green. AC7 and AC8 rest on
    # `Demonstrated non-exempt failure` being present and zero, not on it being absent.
    missing = ZERO_CLASSES - set(by_name)
    assert not missing, (
        f"{TAP_TARGET_AUDIT.name}: classification table is missing required zero "
        f"class(es): {sorted(missing)}"
    )
