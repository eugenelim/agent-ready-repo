#!/usr/bin/env python3
"""Posture test for `.github/workflows/pages.yml`'s deploy-blocking gates.

# STUB: AC7 — red stub materialised at PLAN per CONVENTIONS § Stub → EXECUTE handoff.

Why a SECOND workflow parser, when `tools/test-build-check-workflow.py` exists and
its own plan said to reuse it: that file is `build-check.yml`-shaped end to end — a
hard-coded `WORKFLOW`, an aggregator/`gate-*` job model, a pinned aggregator step
roster — and `pages.yml` has a different job model (`build` → `deploy`, no
aggregator, path-filtered). `tools/lint-ci-parity.py` also scopes `pages.yml`
explicitly out. Generalising the build-check parser would mean parameterising the
job model it asserts, which is most of the file. The two workflows are genuinely
different shapes, so this is a second parser by decision rather than by drift.

What this pins, and what it deliberately does not:

- `pages.yml` is NOT a required merge context. Branch protection requires
  `make build-check`, `gate-main`, `gate-sast` and `gate-export-boundary`. A gate
  here blocks the Pages **deployment**, not the merge. That residual is stated in
  the spec, not papered over: the plugin suite cannot become a required merge
  context, because the only required workflow carries no Node and must carry no
  `paths:` filter.
- The `paths:` filters and the ordering are the load-bearing half. A step that runs
  after `Upload Pages artifact` does not block the upload it is supposed to guard,
  and a filter that stops covering `docs-site/**` means an edit to the plugin
  triggers no run at all.

Every assertion is proven by seeded DELETION or REORDERING rather than by presence:
the step, the filters and the ordering all already exist in part, so a presence
assertion could not detect a removal. `--self-test` runs that matrix on every
invocation, and refuses any assertion family with no mutation — the discipline
`tools/test-build-check-workflow.py` established.

Pure stdlib, matching its sibling: this runs in a required job, and a test that can
fail on a missing import is a test someone import-guards under pressure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pages.yml"

BUILD_JOB = "build"
# The focused plugin suite. One entry point, so the workflow and `package.json`
# cannot drift into two spellings.
PLUGIN_TEST_CMD = "npm run test:plugins --prefix docs-site"
# It must sit after the deps install (the suite imports the plugin's declared
# runtime dependency) and before the artifact upload (so a failure blocks deploy).
AFTER_STEP = "Install docs-site dependencies"
BEFORE_STEP = "Upload Pages artifact"
# Filters AC7 names. `docs-site/**` covers both the plugin and the docs package
# manifest; the workflow's own path is what makes an edit disabling the gate
# trigger a run.
REQUIRED_PATHS = ("docs-site/**", ".github/workflows/pages.yml")
# What `test:plugins` must actually BE. An explicit path fails closed when the suite
# moves; a glob exits 0 with `tests 0`, and so does `true`.
PLUGIN_SUITE = "docs-site/src/plugins/rehype-scrollable-tables.test.ts"
EXPECTED_PLUGIN_SCRIPT = "node --test src/plugins/rehype-scrollable-tables.test.ts"
PACKAGE_JSON = "docs-site/package.json"


def script_is_pinned(script: str) -> bool:
    """Is `scripts["test:plugins"]` the exact explicit-path invocation?

    Kept PURE and separate from `audit()`: the workflow-text mutation matrix cannot
    flip a value read from `docs-site/package.json`, so asserting it inside `audit()`
    would be a decorative check the coverage rule exists to reject. The self-test
    proves this predicate with crafted inputs; `main()` applies it to the real tree.

    The invocation spelling in the workflow is not the gate. Nothing else reads the
    manifest, so replacing the script with `true`, or with the glob it used to be,
    left the workflow posture, lint-ci-parity and `make test` all green having run
    zero tests — `node --test` exits 0 on a zero-test run.
    """
    return script == EXPECTED_PLUGIN_SCRIPT


def _plugin_script() -> str:
    """`scripts["test:plugins"]` from the docs package manifest, or ""."""
    import json
    p = REPO_ROOT / PACKAGE_JSON
    if not p.is_file():
        return ""
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("scripts", {}).get(
            "test:plugins", "")
    except (ValueError, OSError):
        return ""


def _strip_comments(text: str) -> str:
    """Drop whole-line and trailing `#` comments outside quotes.

    A control asserted from a comment is not asserted: an early draft of the
    sibling file was demonstrated green with every required token supplied by
    YAML comments.
    """
    out = []
    for line in text.splitlines():
        quote = None
        cut = len(line)
        for i, ch in enumerate(line):
            if quote:
                if ch == quote:
                    quote = None
            elif ch in "\"'":
                quote = ch
            elif ch == "#":
                cut = i
                break
        out.append(line[:cut].rstrip())
    return "\n".join(out)


def _job_block(text: str, job_id: str) -> str:
    m = re.search(rf"^  {re.escape(job_id)}:\s*$", text, re.M)
    if not m:
        return ""
    nxt = re.search(r"^  [A-Za-z0-9_-]+:\s*$", text[m.end():], re.M)
    return text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]


def _steps(block: str) -> list[str]:
    """Step chunks, in file order.

    The empty case is explicit: with no step markers `idxs[1:] + [len(block)]` is
    one element long against a zero-length `idxs`, so a strict zip raises rather
    than silently yielding nothing — and "no steps found" is exactly the state the
    reindent mutation produces, so it has to be handled, not crashed on.
    """
    idxs = [m.start() for m in re.finditer(r"^      - ", block, re.M)]
    if not idxs:
        return []
    return [block[a:b] for a, b in zip(idxs, idxs[1:] + [len(block)], strict=True)]


def _step_name(step: str) -> str:
    m = re.search(r"^\s*-?\s*name:\s*(.+?)\s*$", step, re.M)
    return m.group(1).strip("\"'") if m else ""


def _run_body(step: str) -> str:
    r"""Everything after this step's `run:` key.

    `re.M` matters as much as `re.S`: a step chunk starts with `- name:`, so without
    multiline anchoring `^\s*run:` never matches and this returns "" for every step —
    which silently emptied the owner search and made the gate assertion look absent.
    """
    m = re.search(r"^\s*run:\s*(\|-?|>-?|)\s*\n?(.*)", step, re.M | re.S)
    return m.group(2) if m else ""


def _has_key(step: str, key: str) -> bool:
    # Quote-tolerant, like the sibling file's `_key_re`: `'if':` and `"if":` are the
    # same key to YAML and to Actions.
    return re.search(rf"^\s*['\"]?{re.escape(key)}['\"]?\s*:", step, re.M) is not None


def _on_block(text: str) -> str:
    m = re.search(r"^on:\s*$", text, re.M)
    if not m:
        return ""
    nxt = re.search(r"^[A-Za-z]", text[m.end():], re.M)
    return text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]


def _trigger_paths(on_blk: str) -> dict[str, list[str]]:
    """Map each trigger to its `paths:` values.

    `paths-ignore:` is deliberately NOT accepted as a substitute: it inverts the
    filter, so the same path list that should make the gate run makes it never run.
    A trigger carrying only `paths-ignore:` therefore reports an empty list and fails
    the membership check.
    """
    out: dict[str, list[str]] = {}
    for m in re.finditer(r"^  ([A-Za-z_]+):\s*$", on_blk, re.M):
        name = m.group(1)
        nxt = re.search(r"^  [A-Za-z_]+:\s*$", on_blk[m.end():], re.M)
        body = on_blk[m.end():m.end() + nxt.start()] if nxt else on_blk[m.end():]
        vals: list[str] = []
        inline = re.search(r"^    paths:\s*\[(.+)\]\s*$", body, re.M)
        if inline:
            out[name] = [v.strip().strip("'\"") for v in inline.group(1).split(",")]
            continue
        pm = re.search(r"^    paths:\s*$", body, re.M)
        if pm:
            tail = body[pm.end():]
            stop = re.search(r"^    [A-Za-z_-]+:", tail, re.M)
            seq = tail[:stop.start()] if stop else tail
            vals = [v.strip().strip("'\"") for v in re.findall(r"^      - (.+)$", seq, re.M)]
        out[name] = vals
    return out


def audit(text: str, evaluated: list[str] | None = None) -> list[str]:
    bad: list[str] = []

    def check(label: str, ok: bool) -> None:
        if evaluated is not None:
            evaluated.append(label)
        if not ok:
            bad.append(label)

    text = _strip_comments(text)
    block = _job_block(text, BUILD_JOB)
    check("build-job-present", bool(block))

    steps = _steps(block)
    names = [_step_name(s) for s in steps]
    check("steps-parsed", len(steps) > 0)

    # The gate itself, matched on its command rather than its name, so renaming the
    # step cannot silently drop it — and by STATEMENT EQUALITY, not containment.
    # Containment was the first draft and it accepted `… || true`, `… ; true`,
    # `… || echo skipped`, a `CI=false` assignment prefix, a body whose first line is
    # `set +e`, and `echo '<the command>'` — which never executes it at all. The
    # sibling parser closed this exact class; this one has one fixed statement, so
    # equality is both available and correct.
    owners = [i for i, s in enumerate(steps)
              if [ln.strip() for ln in _run_body(s).splitlines() if ln.strip()]
              == [PLUGIN_TEST_CMD]]
    check("plugin-test-present", len(owners) == 1)

    if owners:
        i = owners[0]
        step = steps[i]
        # Neutering forms, the same set its sibling pins: an advisory step, a
        # conditional step, and a redirected working directory each leave the
        # command textually present while it gates nothing.
        check("plugin-test-no-continue-on-error", not _has_key(step, "continue-on-error"))
        check("plugin-test-no-if", not _has_key(step, "if"))
        check("plugin-test-no-cwd", not _has_key(step, "working-directory"))
        # A custom `shell:` replaces the interpreter entirely — `shell: cat {0}`
        # leaves the run body byte-identical, so statement equality still passes
        # while the suite never executes.
        check("plugin-test-no-shell", not _has_key(step, "shell"))
        # Ordering is the half that decides whether failure blocks the upload.
        after = names.index(AFTER_STEP) if AFTER_STEP in names else -1
        before = names.index(BEFORE_STEP) if BEFORE_STEP in names else -1
        check("plugin-test-after-install", after != -1 and i > after)
        check("plugin-test-before-upload", before != -1 and i < before)

    # AC7's "blocks … deployment" half. Intra-`build` ordering is necessary but not
    # sufficient: if `deploy` stops depending on `build`, or `build` itself is made
    # advisory or conditional, a failing plugin test stops blocking the deploy while
    # every step-level assertion above stays green. All three were measured green
    # before these checks existed.
    deploy = _job_block(text, "deploy")
    check("deploy-job-present", bool(deploy))
    # Membership, not first-element anchoring: `needs: [other, build]` and the
    # block-sequence form are both legitimate and previously reported a false
    # violation.
    _needs = re.search(r"^\s*needs:\s*(.*(?:\n\s+- .*)*)", deploy, re.M)
    check("deploy-needs-build",
          bool(_needs) and "build" in re.findall(r"[A-Za-z0-9_-]+", _needs.group(1)))
    # Scanned over the WHOLE job block. An earlier draft captured only the keys
    # before the first blank line — about 5 of this job's 90 lines — so appending
    # `    if: ${{ false }}` AFTER the steps list is valid YAML that defeated both
    # checks while `audit()` returned []. Its two mutations passed only because they
    # inserted at the one offset the window covered, which made the self-test's
    # family-coverage claim false assurance for the exact fail-open these close.
    # Job-level keys are 4-space indented; step keys are 8, so `^    ` cannot match
    # a step key.
    check("build-job-not-advisory",
          not re.search(r"^    ['\"]?continue-on-error['\"]?\s*:", block, re.M))
    check("build-job-not-conditional",
          not re.search(r"^    ['\"]?if['\"]?\s*:", block, re.M))

    on_blk = _on_block(text)
    check("on-block-present", bool(on_blk))
    # Parsed PER TRIGGER, not counted. An occurrence count over the whole `on:` block
    # was satisfied by listing a path twice under `push` while deleting it from
    # `pull_request`, and by flipping both keys to `paths-ignore:` — which inverts the
    # filter so a `docs-site/**` edit runs the gate NEVER. Both measured green.
    triggers = _trigger_paths(on_blk)
    # Only the path-filtered triggers are required to carry the list. `workflow_dispatch`
    # is a manual trigger with no `paths:` and legitimately must not have one — an
    # earlier draft demanded paths from EVERY trigger and so failed on the clean file.
    filtered = ("push", "pull_request")
    check("triggers-parsed", all(k in triggers for k in filtered))
    for want in REQUIRED_PATHS:
        check(f"path-filter[{want}]",
              all(want in triggers.get(k, []) for k in filtered))

    return bad


def _baseline() -> str:
    if WORKFLOW.is_file():
        return WORKFLOW.read_text(encoding="utf-8")
    raise SystemExit(f"missing {WORKFLOW} — the self-test cannot prove anything")


_MUTATIONS: list[tuple[str, str, object]] = [
    ("drop-plugin-test-step", "plugin-test-present",
     lambda t: re.sub(r"      - name: [^\n]*\n        run: " + re.escape(PLUGIN_TEST_CMD) + r"\n",
                      "", t)),
    ("advisory-plugin-test", "plugin-test-no-continue-on-error",
     lambda t: t.replace(f"        run: {PLUGIN_TEST_CMD}\n",
                         f"        continue-on-error: true\n        run: {PLUGIN_TEST_CMD}\n")),
    ("conditional-plugin-test", "plugin-test-no-if",
     lambda t: t.replace(f"        run: {PLUGIN_TEST_CMD}\n",
                         f"        if: ${{{{ false }}}}\n        run: {PLUGIN_TEST_CMD}\n")),
    ("cwd-plugin-test", "plugin-test-no-cwd",
     lambda t: t.replace(f"        run: {PLUGIN_TEST_CMD}\n",
                         f"        working-directory: tools\n        run: {PLUGIN_TEST_CMD}\n")),
    # Moved after the upload: the command still runs, and still fails, but the
    # artifact it was supposed to guard has already been published.
    ("plugin-test-after-upload", "plugin-test-before-upload",
     lambda t: _relocate_gate(t, BEFORE_STEP, after=True)),
    ("plugin-test-before-install", "plugin-test-after-install",
     lambda t: _relocate_gate(t, AFTER_STEP, after=False)),
    # Structural families. Without these three the parser could stop seeing the
    # workflow at all and every assertion above would pass vacuously — the
    # fail-open shape its sibling was repeatedly bitten by.
    ("rename-build-job", "build-job-present",
     lambda t: t.replace("\n  build:\n", "\n  build2:\n", 1)),
    # Reindent EVERY step in the build job, not one: the step scan then finds
    # nothing, which is the fail-open shape where every per-step assertion above
    # would otherwise pass vacuously.
    ("reindent-steps", "steps-parsed",
     lambda t: t.replace("\n      - ", "\n    - ")),
    ("rename-on-key", "on-block-present",
     lambda t: t.replace("on:\n", "'on':\n", 1)),
    ("shell-override-gate", "plugin-test-no-shell",
     lambda t: t.replace(f"        run: {PLUGIN_TEST_CMD}",
                         f"        shell: cat {{0}}\n        run: {PLUGIN_TEST_CMD}")),
    ("post-steps-job-if", "build-job-not-conditional",
     lambda t: t.replace("\n  deploy:", "\n    if: ${{ false }}\n\n  deploy:", 1)),
    ("post-steps-job-advisory", "build-job-not-advisory",
     lambda t: t.replace("\n  deploy:", "\n    continue-on-error: true\n\n  deploy:", 1)),
    ("discard-exit-status", "plugin-test-present",
     lambda t: t.replace(f"        run: {PLUGIN_TEST_CMD}",
                         f"        run: {PLUGIN_TEST_CMD} || true")),
    ("echo-only-gate", "plugin-test-present",
     lambda t: t.replace(f"        run: {PLUGIN_TEST_CMD}",
                         f"        run: echo '{PLUGIN_TEST_CMD}'")),
    ("assignment-prefix-gate", "plugin-test-present",
     lambda t: t.replace(f"        run: {PLUGIN_TEST_CMD}",
                         f"        run: CI=false {PLUGIN_TEST_CMD}")),
    ("drop-deploy-needs", "deploy-needs-build",
     lambda t: t.replace("    needs: build\n", "", 1)),
    ("rename-deploy-job", "deploy-job-present",
     lambda t: t.replace("\n  deploy:\n", "\n  deploy2:\n", 1)),
    ("advisory-build-job", "build-job-not-advisory",
     lambda t: t.replace("  build:\n", "  build:\n    continue-on-error: true\n", 1)),
    ("conditional-build-job", "build-job-not-conditional",
     lambda t: t.replace("  build:\n", "  build:\n    if: ${{ false }}\n", 1)),
    ("flip-to-paths-ignore", "path-filter[docs-site/**]",
     lambda t: t.replace("    paths:\n", "    paths-ignore:\n")),
    ("drop-filter-from-one-trigger", "path-filter[docs-site/**]",
     lambda t: t.replace("      - 'docs-site/**'\n", "", 1)),
    ("rename-a-trigger", "triggers-parsed",
     lambda t: t.replace("\n  pull_request:\n", "\n  pull_request_target:\n", 1)),
    ("drop-docs-site-filter", "path-filter[docs-site/**]",
     lambda t: t.replace("      - 'docs-site/**'\n", "", 1)),
    ("drop-workflow-self-filter", "path-filter[.github/workflows/pages.yml]",
     lambda t: t.replace("      - '.github/workflows/pages.yml'\n", "", 1)),
]


def _extract_gate_step(text: str) -> tuple[str, str]:
    """Pull the plugin-test step chunk out of `text`. Returns (chunk, remainder)."""
    # Find the chunk that actually carries the command, not merely the first step.
    for m in re.finditer(r"^      - name: [^\n]*\n(?:        [^\n]*\n)*", text, re.M):
        if PLUGIN_TEST_CMD in m.group(0):
            return m.group(0), text[:m.start()] + text[m.end():]
    return "", text


def _relocate_gate(text: str, anchor_name: str, *, after: bool) -> str:
    """Move the plugin-test step immediately before/after the named step.

    Ordering is the half of AC7 that decides whether a failure blocks the upload, so
    both directions are mutated: placed before the deps install it cannot run, and
    placed after the upload it cannot block it.
    """
    chunk, rest = _extract_gate_step(text)
    if not chunk:
        return text
    anchor = f"      - name: {anchor_name}\n"
    if anchor not in rest:
        return text
    i = rest.index(anchor)
    if after:
        nxt = rest.find("      - ", i + len(anchor))
        # Clamp to the end of the BUILD job. `Upload Pages artifact` is its last
        # step, so an unclamped search runs past the job boundary and drops the
        # chunk into `deploy:` — where the job-scoped audit cannot see it, and the
        # mutation would trip "step absent" instead of "step out of order".
        job_end = rest.find("\n  deploy:")
        limit = job_end + 1 if job_end != -1 else len(rest)
        at = nxt if nxt != -1 and nxt < limit else limit
    else:
        at = i
    return rest[:at] + chunk + rest[at:]


def _family(label: str) -> str:
    return re.sub(r"\[.*\]$", "[*]", label)


def self_test() -> int:
    failures: list[str] = []
    good = _baseline()
    evaluated: list[str] = []
    base = audit(good, evaluated)
    if base:
        failures.append(f"baseline should be clean, got {base}")
    for mut_id, expected, transform in _MUTATIONS:
        mutated = transform(good)  # type: ignore[operator]
        if mutated == good:
            failures.append(f"{mut_id}: transform was a no-op — proves nothing")
            continue
        got = audit(mutated)
        if expected not in got:
            failures.append(f"{mut_id}: expected {expected!r}, got {got}")
    # The real-tree predicate, proved with crafted inputs rather than left asserted.
    for bad_script in ("true", "node --test src/plugins/*.test.ts", "", "echo ok"):
        if script_is_pinned(bad_script):
            failures.append(f"script_is_pinned accepted {bad_script!r}")
    if not script_is_pinned(EXPECTED_PLUGIN_SCRIPT):
        failures.append("script_is_pinned rejected the expected invocation")

    covered = {_family(e) for _, e, _ in _MUTATIONS}
    uncovered = sorted({_family(i) for i in evaluated} - covered)
    if uncovered:
        failures.append(f"assertion families evaluated but unmutated: {uncovered}")
    if failures:
        print(f"✖ self-test: {len(failures)} problem(s):", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"✓ self-test: baseline clean; {len(_MUTATIONS)} mutations each caught; "
          f"every one of {len(covered)} assertion families has ≥1 mutation")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    # The matrix runs on every invocation, not behind an opt-in flag: an earlier
    # sibling draft wired `--self-test` nowhere, so every assertion it claimed to
    # prove was decorative.
    if self_test() != 0:
        return 1
    if not WORKFLOW.is_file():
        print(f"✖ {WORKFLOW} not found", file=sys.stderr)
        return 1
    violations = audit(WORKFLOW.read_text(encoding="utf-8"))
    # Real-tree checks, outside the workflow-text domain (see script_is_pinned).
    if not script_is_pinned(_plugin_script()):
        violations.append(
            f"plugin-script-pinned ({PACKAGE_JSON} scripts['test:plugins'] must be "
            f"{EXPECTED_PLUGIN_SCRIPT!r}, got {_plugin_script()!r})")
    if not (REPO_ROOT / PLUGIN_SUITE).is_file():
        violations.append(f"plugin-suite-file-exists ({PLUGIN_SUITE} is missing)")
    if violations:
        print(f"✖ {len(violations)} posture violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1
    print("✓ pages.yml posture OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
