# Verification ledger: intent-view-handover-prompt

Every test and measurement result above § Review dispositions ran against code commit `ee06ef520afe4f2262604260af3219800522435e`, or a tree whose `packs/core/`, `.claude/` and `.agents/` content is identical to it apart from core's version field. That field moved from 3.1.10 to 3.1.9 in `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` (commit `1fae79643`), because a roster test requires exactly the next patch above the default branch's 3.1.8; no recorded result reads it. Every other commit after `ee06ef520` changes only documentation and coordination files: this ledger, `notes/screens/`, one guide sentence, the changelog fragment, the spec's and plan's status lines and checked criteria, and the `workspace.toml` entry. This list is a summary; `git log --stat ee06ef520..HEAD` is the complete record, and `git diff ee06ef520 HEAD -- packs/core .claude .agents` shows only the two version lines. Run on 2026-10-19.

## Scripted browser suite (all of `view_browser_checks.py`)

Command: `uv run --no-project -q --with pytest --with playwright --with pyyaml python -m pytest packs/core/tests/skills/navigate-intents/view_browser_checks.py -q -rs`

Result: 322 passed, 0 skipped, 158.73 s (0:02:38). Open intermittent failures, recorded rather than explained: two earlier full runs of the same tree each failed. One failure was a `#key summary` click timeout in the shared `_busy` helper, which the shipped access-matrix tests also use. The other was this feature's own wait for the `.copy-status` line in the refused-copy case of `test_handover_ac_0016_session_start_access_criteria_hold_with_a_prompt_picked`, where the line stayed hidden. The cause is not established; a re-render of the detail zone landing after the click, or machine load, are the open candidates. Since then, at `c6abc01b3` (code-identical to `ee06ef520`): three runs of the 71 prompt, copy and handover tests (`-k "handover or prompt or copy"`) passed 71 of 71 each (47, 46 and 46 s), and a further full run passed 322 of 322 with none skipped in 154 s.

Collected suites (`packs/core/tests/skills/navigate-intents/` and `packs/core/tests/pack/`): 939 passed, 4 skipped, 27.14 s. The browser file is not collected by that glob.

## AC-0019: scale bench

Command: `uv run --no-project -q --with playwright python packs/core/tests/skills/navigate-intents/view_bench.py --source . --counts 1 10 25 50`

| copies | outstanding available | default rows | file bytes | startup ms | search ms | heap MiB | meets all |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | yes | 31 | 730,539 | 10 | 12 | 5 | yes |
| 10 | no (resource_limit, limit files) | 0 | 5,101,578 | 32 | 36 | 10 | yes |
| 25 | no (resource_limit, limit files) | 0 | 12,552,683 | 66 | 44 | 23 | yes |
| 50 | no (resource_limit, limit files) | 0 | 24,971,187 | 100 | 44 | 55 | yes |

Pass: `meets_all` is true at every count, under the bench's own thresholds.

## AC-0020: real export of this repository

Command: `python3 packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py export --root <repo> --destination <tmp dir outside the repo> --name repo.html`, then the script below (kept outside the repository; run `uv run --no-project -q --with playwright python real_export_copy_check.py <repo root> <empty dir outside the repo>`). It opens the file in headless Chromium with clipboard read and write granted, picks one record per prompt rule by browse route, clicks "Copy prompt", waits for the button to read "Copied", reads the clipboard, and asserts it equals the spec's template with that record's payload path.

Export: `status: ok`, 710,890 bytes.

| Rule | Record | Copied prompt (equals template + payload path) |
| --- | --- | --- |
| 3 | `spec:intent-view-handover-prompt` | Use the work-loop skill to continue building `docs/specs/intent-view-handover-prompt/spec.md`. |
| 4 | `spec:graph-well-formed-authoring` | Use the work-loop skill to implement `docs/specs/graph-well-formed-authoring/spec.md`. |
| 5 | `spec:bounded-remote-create-action` | Use the new-spec skill to finish the spec at `docs/specs/bounded-remote-create-action/spec.md`. |
| 6 | `brief:acceptance-centered-work-loop` | Use the author-delivery-brief skill in continue mode on `docs/product/briefs/acceptance-centered-work-loop.md`. |
| 7 | `intent:tracker-native-value-before-adoption` | Use the intent skill to decompose `docs/product/intents/FEAT-0014-tracker-native-value-before-adoption.md`. |
| 9 | `intent:intent-delivery-traceability` | Use the close-work skill to check whether `docs/product/intents/FEAT-0003-intent-delivery-traceability.md` can close. |
| 10 | `capability:workspace-coordination-reorganization` | Use the intent skill to keep shaping `docs/product/intents/CAP-0003-workspace-coordination-reorganization.md`. |

Script source:

```python
"""Usage: python real_export_copy_check.py <repo root> <dest dir outside the repo>

Exports the repository, then for one record per prompt rule picks it by browse route,
clicks "Copy prompt", reads the clipboard and asserts it equals the spec's template.
"""
import json, pathlib, re, subprocess, sys
from playwright.sync_api import sync_playwright

root, dest = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
script = root / "packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py"
done = subprocess.run(
    [sys.executable, str(script), "export", "--root", str(root), "--destination", str(dest), "--name", "repo.html"],
    capture_output=True, text=True, check=True,
)
print(done.stdout.strip()[:200])
html = (dest / "repo.html")
payload = json.loads(re.search(r'<script type="application/json"[^>]*>(.*?)</script>', html.read_text(), re.S).group(1))
TEMPLATES = {
    3: "Use the work-loop skill to continue building `{}`.",
    4: "Use the work-loop skill to implement `{}`.",
    5: "Use the new-spec skill to finish the spec at `{}`.",
    6: "Use the author-delivery-brief skill in continue mode on `{}`.",
    7: "Use the intent skill to decompose `{}`.",
    9: "Use the close-work skill to check whether `{}` can close.",
    10: "Use the intent skill to keep shaping `{}`.",
}
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(permissions=["clipboard-read", "clipboard-write"], viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(html.as_uri())
    seen: dict[int, tuple[str, str]] = {}
    for node in payload["nodes"]:
        page.evaluate("f => { location.hash = f; }", "q=browse&node=" + node["id"])
        page.wait_for_function("() => document.querySelector('#detail-body .state-line') !== null")
        if page.locator("#detail-body code.prompt").count() != 1:
            continue
        shown = page.locator("#detail-body code.prompt").text_content()
        for rule, template in TEMPLATES.items():
            if rule not in seen and shown == template.format(node["path"]):
                page.locator("#detail-body .prompt-block > button").click()
                page.wait_for_function("() => document.querySelector('#detail-body .prompt-block > button').textContent === 'Copied'")
                got = page.evaluate("navigator.clipboard.readText()")
                assert got == shown == template.format(node["path"]), (node["id"], got)
                seen[rule] = (node["id"], got)
        if len(seen) == len(TEMPLATES):
            break
    browser.close()
for rule in sorted(seen):
    print(rule, *seen[rule])
assert set(seen) == set(TEMPLATES), sorted(set(TEMPLATES) - set(seen))
print("all", len(seen), "rules passed")
```

Rules the corpus did not hold: none; all seven prompt rules were present and all seven assertions passed.

## AC-0021 input: screenshots

Sixteen PNGs in `screens/`, named `<state>-<width>-<theme>.png`. Each is a true Playwright viewport (width 320 at height 900, or width 2560 at height 1400; not a cropped window) with the detail zone's "Next step" scrolled into view. The script below (run `uv run --no-project -q --with playwright --with pytest --with pyyaml python screenshots.py <repo root> <out dir>`) produced them over exports of the `mixed` fixture, the long-path corpus, and a data-block rewrite of `mixed`.

- `prompt-shown`: `mixed`, `spec:bravo-spec` picked.
- `path-refused`: the long-path corpus (mixed plus an Implementing spec in `long-` followed by 115 `a`), that spec picked.
- `hostile-path`: `mixed` with `spec:bravo-spec`'s payload path rewritten to `docs/specs/brav`o-spec/spec.md` (a safe path with a backtick inserted).
- `copy-refused`: `mixed`, `spec:bravo-spec` picked, "Copy prompt" clicked in a context without clipboard permission; the prompt shows selected and the status line shows.

| SHA-256 | File |
| --- | --- |
| `014a8ae7d917276829584462f6462f17567d31b828e0dc0eff433921f1acc829` | `screens/copy-refused-2560-dark.png` |
| `8a1f38a48e32b9857089fd113b6cf0f78b881af6d61c6ad4316ffd33e24ec1ec` | `screens/copy-refused-2560-light.png` |
| `bed0f944e82e768f56b61ec106bc22632f37e1e8d01f781a9dc61da4a514ad56` | `screens/copy-refused-320-dark.png` |
| `4177b7c4f41fb0777a4d7ab172b337a4a1f771a3d975b17b781c6638ce6d3ab4` | `screens/copy-refused-320-light.png` |
| `5136e5b8f8b1517f50db99a2d1efb332db800d79d31b0b4fa5b935d5d1f52f61` | `screens/hostile-path-2560-dark.png` |
| `9ad1367467bc0d2f24cd537236d2c6166997461fc59329af6abb30807240e267` | `screens/hostile-path-2560-light.png` |
| `e2fee25a015ebd952d0592626b2a5c5f1a06e75ada9a2bdfaf5ad41d961a6fe3` | `screens/hostile-path-320-dark.png` |
| `ecddaf94b05af5748cb7ef6a518399612efa9e6044442251ef2d4f9ba0c8cbcf` | `screens/hostile-path-320-light.png` |
| `ff9e7e092ac25637531be3180e2ed9580dc5bd156bc163fb5163d792b4d4c78a` | `screens/path-refused-2560-dark.png` |
| `b9a99bfa2275249f58f615489b915ee3f06104bb32bf63264602958656330a2a` | `screens/path-refused-2560-light.png` |
| `626c45842f8186da6a9307566e7073a4dc92483b7fc0eaff7fab8996be45c71d` | `screens/path-refused-320-dark.png` |
| `9cc800a6164ee230f1ad832eba76087ece9ccc5b4bee6bc336d564fed1cf43cf` | `screens/path-refused-320-light.png` |
| `c10daa6928e00d2d73f3496a48b8d4faa1e5ed86f43458539d4a6cf62866c0a8` | `screens/prompt-shown-2560-dark.png` |
| `f86b8bcf708fd3d51b9c3147447ca821df953a37cda2906903d6a08233abf5fd` | `screens/prompt-shown-2560-light.png` |
| `8e5db32723d6f32857effbe0aee3c8e9b0faaf9817758a1aadb7c940987c104e` | `screens/prompt-shown-320-dark.png` |
| `638a3b469c9301db9c208ddfdb76acdb78f518fe9774620270e44f0e16d72fc9` | `screens/prompt-shown-320-light.png` |

Screenshot script source:

```python
"""Usage: python screenshots.py <repo root> <out dir>

Takes the sixteen AC-0021 screenshots, reusing the browser suite's own corpus helpers.
"""
import hashlib, importlib.util, pathlib, sys, tempfile
from playwright.sync_api import sync_playwright

root, out = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
tests = root / "packs/core/tests/skills/navigate-intents"
sys.path.insert(0, str(tests))
spec = importlib.util.spec_from_file_location("vbc_screens", tests / "view_browser_checks.py")
vbc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vbc)
out.mkdir(parents=True, exist_ok=True)
tmp = pathlib.Path(tempfile.mkdtemp())
mixed = vbc._export(vbc._FIXTURES / "mixed", tmp / "o", "mixed.html")
long_root = vbc._long_path_corpus(tmp)
long_export = vbc._export(long_root, tmp / "o", "long.html")
long_node = next(n["id"] for n in vbc.payload_of(long_export)["nodes"] if "long-" + "a" * 115 in (n.get("path") or ""))
hostile = vbc._with_paths(mixed, tmp / "hostile.html", {"spec:bravo-spec": "docs/specs/brav`o-spec/spec.md"})
STATES = {
    "prompt-shown": (mixed, "spec:bravo-spec", False),
    "path-refused": (long_export, long_node, False),
    "hostile-path": (hostile, "spec:bravo-spec", False),
    "copy-refused": (mixed, "spec:bravo-spec", True),
}
SIZES = {320: 900, 2560: 1400}
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for state, (export, node, click) in STATES.items():
        for width, height in SIZES.items():
            for theme in ("light", "dark"):
                ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme=theme)
                page = ctx.new_page()
                page.goto(export.as_uri() + "#q=browse&node=" + node.replace(":", "%3A"))
                page.wait_for_function("() => document.querySelector('#detail-body .state-line') !== null")
                if click:
                    page.locator("#detail-body .prompt-block > button").click()
                    page.wait_for_selector("#detail-body .copy-status", state="visible")
                page.locator("#detail-body .next-step").scroll_into_view_if_needed()
                page.screenshot(path=str(out / f"{state}-{width}-{theme}.png"))
                ctx.close()
    browser.close()
for png in sorted(out.glob("*.png")):
    print(hashlib.sha256(png.read_bytes()).hexdigest(), png.name)
```

## Review dispositions

The table gives each review round's result and the commit it reviewed. A report with findings, or with a `## Not checked` footer, was adjudicated by `finding-adjudicator`, and its counts are after adjudication. A footer-free clean report, and a report holding only Nits that this change did not act on, skipped adjudication under the work-loop review gateway; such a Nit is deferred by the author, not by an adjudicator.

| Round | Commit reviewed | Code tree |
| --- | --- | --- |
| 1 | `4ddd94863` | `5289d7454` (before the repair) |
| 2 | `c6abc01b3` | identical to `ee06ef520` |
| 3 | `2d5b0b864` | identical to `ee06ef520` |
| 4 | `b4bae7330` | identical to `ee06ef520` |
| 5 | `1b060b93d` | identical to `ee06ef520` apart from core's version field |
| 6 | the commit adding this row | identical to `ee06ef520` apart from core's version field |

| Reviewer | Round 1 | Round 2 | Rounds 3 to 5 |
| --- | --- | --- | --- |
| `adversarial-reviewer` | adjudicated: 1 Blocker, 1 Concern, 4 Nits; 2 refuted | adjudicated: 1 Concern, 1 Nit | round 3 adjudicated: 1 Concern; round 4 adjudicated: 1 Blocker, 2 Concerns, 1 Nit; round 5 adjudicated: 1 Blocker (AC-0021 screen coverage), 2 Nits — all on this ledger and repaired; round 6 reviews the repair |
| `security-reviewer` | clean with a footer; adjudicated clean | clean with a footer; adjudicated clean | not re-run: later commits change documentation, coordination files and core's version field only, and cross no security boundary |
| `quality-engineer` | adjudicated: 1 Blocker; 5 refuted | clean, not adjudicated | not re-run |
| `experience-reviewer` (AC-0021 gate) | adjudicated: 1 Minor; 5 refuted (opened all 16 screens at `4ddd94863`) | 1 Nit only, not adjudicated; deferred by the author (opened 9 of 16 screens) | round 3 at `1b060b93d` opened all 16 screens and confirmed every hash against this ledger: adjudicated clean; its 2 Minors and 2 Nits refuted (AC-0003 fixes the refusal wording; the hostile-path display is a synthetic payload rewrite) |
| Visual-polish pass (general-purpose) | adjudicated: clean; 7 refuted (opened all 16 screens at `4ddd94863`) | round 2 at `1b060b93d` opened all 16 screens: adjudicated clean; its 2 Minors (the notice type size, kept on purpose) and 1 Nit (a 3px inset) refuted as preferences | — |
| `frontend-reviewer` stand-in (general-purpose; the role is not installed) | adjudicated: 1 Concern, 1 Nit; 1 refuted | clean, not adjudicated | not re-run |

What the sustained findings changed:
- The AC-0008 probes hit exactly 100 and 101 characters in a segment, and exactly 200 and 201 characters in a path, with a literal outcome each.
- A refused copy resets the button to "Copy prompt", and a successful copy hides the failure line. The live region is cleared and rewritten on the next tick, so a repeated outcome is announced again.
- The refusal and copy-failure lines use the view's `notice` treatment.
- The AC-0015 check compares all four edges.
- The guide's "Copied" and no-prompt sentences match the code and the next-step rules.
- This ledger states the commit behind each result and records the open intermittent failure above.

## Mutation check of the path rule

Base: commit `b4bae7330`, whose code tree is identical to `ee06ef520`. Each mutation edited `packs/core/.apm/skills/navigate-intents/scripts/view_src/handover.js` in the working tree only, and the file was restored before the next step.

Command: `PYTHONPATH=packages/agentbundle:packages/credbroker uv run --no-project -q --with pytest --with pyyaml --with-requirements tools/requirements.txt python -m pytest packs/core/tests/skills/navigate-intents/test_export_html.py::test_handover_prompt_matches_the_safe_path_rule -q`

| Mutation | Result |
| --- | --- |
| `PATH_SEGMENT` widened from `{0,99}` to `{0,100}` | 1 failed |
| ` \|\| path.length > PATH_MAX_LENGTH` removed from the length check | 1 failed |
| File restored | 1 passed |

## AC-0021

The adjudicated round-1 experience review leaves 1 Minor and no Major or Blocker. That Minor was repaired. The round-2 experience review opened 9 of the 16 repaired screens and holds 1 Nit and no Major or Blocker; the round-3 review opened all 16, confirmed their hashes, and is clean after adjudication. The author defers that Nit: the copy-failure notice keeps the smaller muted meta text while the refusal notice uses body text, because the copy line is a short status tied to its button and the refusal line replaces the prompt.

## CI dispatches

Dispatched on 2026-10-19 at commit `480a46c25`, whose code tree is the final code: `git diff 480a46c25 HEAD -- packs/core .claude .agents` prints nothing.

| Workflow | Run id | Result |
| --- | --- | --- |
| `test-corpus.yml` (`make test`, 4 shards; holds the collected AC-0008 and AC-0009 tests) | 39287153607 | success |
| `test-roster.yml` | 39287157793 | success |
| `pack-javascript.yml` | 39287162011 | success |

An earlier dispatch at `b4bae7330` (runs 39284589634 and 39284593272) failed one test, `test_pack_delivery_contract_is_complete_and_version_increased`. That test requires core's version to be exactly the next patch above the default branch's 3.1.8. Commit `1fae79643` moved core from 3.1.10 to 3.1.9, and the runs above pass.
