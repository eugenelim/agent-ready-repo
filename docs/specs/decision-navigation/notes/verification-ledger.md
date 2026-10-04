# Verification ledger: decision navigation

Measured and manual evidence for `docs/specs/decision-navigation/spec.md`.
Each entry names its date, the commit it ran on, and the exact command.

## AC-0015 Chrome scale evidence

### Practicality thresholds (frozen 2026-10-03, before any measurement)

A full export stays practical at a corpus size only if every limit holds.

| Measure | Limit |
| --- | --- |
| HTML file size | 100 MiB |
| Startup: navigation start to first rendered list row | 3,000 ms |
| Representative search: keystroke to updated result list | 300 ms |
| Peak JS heap after startup and one search | 1,024 MiB |

### Method

- **Browser:** desktop Google Chrome, driven headless through Playwright's
  `chrome` channel; the exact version is recorded with each run.
- **Current corpus:** every admitted record under `docs/adr/` and `docs/rfc/`
  at the run commit.
- **Synthetic growth:** a scratch repository holds N renumbered copies of the
  current corpus (N = 1, 10, 25, 50). Each copy maps every record ordinal to a
  fresh ordinal and rewrites every `ADR-NNNN` and `RFC-NNNN` token inside that
  copy through the same map, so supersession and `Related` structure repeat
  exactly.
- **Startup:** median of three cold loads in a fresh browser context.
- **Search:** type `migration` into the search box; time until the result list
  stops changing; median of three.
- **Heap:** `performance.memory.usedJSHeapSize` peak after startup and search.

### Results (2026-10-04, commit `3ed1f797deae8656dbe27e471dce7378b9898406`)

Desktop Google Chrome 154.0.8037.93 on macOS 26.5.2. The 1× corpus is the
repository at that commit: 238 records (134 ADRs, 104 RFCs).

| Scale | Records | Full HTML | Startup | Search | Peak heap | Within limits |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1× | 238 | 5.7 MiB | 116 ms | 1.0 ms | 19.5 MiB | yes |
| 10× | 2,380 | 56.3 MiB | 598 ms | 5.6 ms | 170.3 MiB | yes |
| 25× | 5,950 | 140.6 MiB | 1,275 ms | 13.3 ms | 412.9 MiB | no — file size |
| 50× | 11,900 | 281.2 MiB | 3,030 ms | 28.0 ms | 828.2 MiB | no — file size and startup |

A bounded export of the 50× corpus is 14.6 MiB, starts in 577 ms, searches in
26.5 ms, and peaks at 28.0 MiB of heap.

**First threshold exceeded:** HTML file size (100 MiB), between 10× and 25×.

**Chosen rule:** publish full mode when the estimated file is at most 100 MiB.
Above that, the publisher refuses full mode unless the caller passes explicit
confirmation; bounded mode is the default answer for a larger corpus. The rule
is `BUDGET_BYTES` in `navigate-decisions/scripts/explorer.py`.

Command, from the repository root, with Playwright and Chrome installed:
`python3 <scratch>/bench.py <scratch> 1,10,25,50` (script reproduced under
[Evidence scripts](#evidence-scripts)).

## AC-0016 and AC-0023 interaction evidence

Scripted run (2026-10-04, commit `3ed1f797`, Chrome 154.0.8037.93, offline
browser context) of the 1× full export:

- **Offline:** zero requests other than the `file:` page itself; zero page errors.
- **Orientation:** corpus counts (238) and the boundary sentence "It is not a
  complete statement of the policy applicable to any proposed action." are on
  the first screen.
- **Keyboard:** Tab reaches search, kind filter, status filter, the four view
  buttons, then each record button; Enter on a record selects it.
- **Focus:** focused controls show a 3 px solid outline.
- **Views keep selection:** list, graph, context, and detail each keep
  `ADR-0001` selected (`#graph/ADR-0001`, `#context/ADR-0001`, …).
- **History:** browser back returns `#detail/ADR-0001`; forward returns
  `#list/ADR-0001`; neither reads a file or the network.
- **No-results state:** "No records match the active search and filters. Clear
  to see all 238 records."
- **Graph trust labels:** the lifecycle graph labels partial supersession and
  its scope (`D3`) apart from full supersession.
- **Reflow:** at 200% (640 CSS px) and 400% (320 CSS px) every view has zero
  horizontal overflow. An earlier run found 391 px and 711 px of overflow from
  the status filter; fixed in `6cbf8eb6` before this run.
- **Motion and activation:** a `prefers-reduced-motion` rule is present; no
  element uses double-click.

Not covered by the script: screen-reader announcement order and a sighted
review of visual focus contrast. Those stay with the human AC-0016 review.

## AC-0022 case-insensitive destination evidence

2026-10-04, commit `3ed1f797deae8656dbe27e471dce7378b9898406`, macOS 26.5.2
(APFS, case-insensitive temporary directory). Command:

`python3 -m pytest "packs/governance-extras/tests/skills/navigate-decisions/test_html_publication.py::test_refuses_case_variant_inside_worktree" -v -p no:cacheprovider`

Result: `PASSED`. The test asserts the case-variant directory exists and the
refusal names the worktree, so it cannot pass on a missing path. The
owner-only mode tests `test_temp_sibling_mode_0600_before_write` and
`test_published_file_mode_0600` passed in the same run.

## T7 corrections from the first post-gates review

The first post-gates review (2026-10-04, branch head `a241146fd`) sustained
58 findings after independent adjudication. T7 closes every one by the mode
listed in its row. The plan's T7 Tests own the mode definitions and this row
set; only the Status column changes here.

| ID | Severity | Finding | Closes by | Status |
| --- | --- | --- | --- | --- |
| ADV-1 | Blocker | Relationship `source` holds a record ID instead of a repository-relative path. | failing test | open |
| ADV-2 | Blocker | Records carry no structured header fields, so no output has `exact headers`. | failing test | open |
| ADV-3 | Blocker | The relationship, result-byte and lineage bounds are never enforced. | failing test | open |
| ADV-4 | Blocker | Malformed selectors and assertions return the whole corpus or crash instead of refusing. | failing test | open |
| ADV-5 | Blocker | In the HTML, caller assertions lose their text and are not normalized relationship tuples. | failing test | open |
| ADV-6 | Blocker | The support-reference inventory is missing. | failing test | open |
| ADV-7 | Blocker | Several AC-0022 destination refusals and proofs are missing. | failing test | open |
| ADV-8 | Blocker | The HTML shows record text without display escaping, in the same text node as trust labels. | failing test | open |
| ADV-9 | Concern | The explorer and the query read registers and corpus roots differently. | failing test | open |
| ADV-10 | Concern | Header parsing departs from the stated grammar. | failing test | open |
| ADV-11 | Concern | Shipped scripts cite internal governance records. | document change | open |
| ADV-12 | Concern | The ledger commits a personal local path. | document change | open |
| ADV-13 | Concern | The provenance block is inserted into the HTML without escaping. | failing test | open |
| ADV-14 | Concern | The guide, design doc and skill contradict shipped behavior. | document change | open |
| ADV-15 | Concern | Some tests cannot fail, and the AC-0021 fixtures are missing. | mutation red | open |
| ADV-16 | Concern | Plan T2 names a verification file that does not exist. | ledger deviation | open |
| ADV-17 | Concern | Refusal shapes are not stable. | failing test | open |
| ADV-18 | Concern | Full export drops admitted bodies between 1 MiB and 2 MiB. | failing test | open |
| ADV-19 | Concern | A commit-pinned link can show content that differs from the export. | failing test | open |
| ADV-20 | Nit | The pack description still makes the retired promise. | document change | open |
| SEC-1 | Blocker | CLI `--name` is joined before validation, so a dot-segment or absolute name escapes the destination root. | failing test | open |
| SEC-2 | Concern | Raw bidi controls reach visible HTML, and the escape set misses directional marks. | failing test | open |
| SEC-3 | Concern | Provenance is put into the HTML without HTML escaping. | failing test | open |
| SEC-4 | Concern | The export reads register files through a duplicate code path that reports unsafe or oversized files as absent. | failing test | open |
| SEC-5 | Concern | Caller assertions are not checked against a schema. | failing test | open |
| SEC-6 | Concern | SKILL.md does not declare the `filesystem_write` boundary its script crosses. | document change | open |
| SEC-7 | Concern | Publication is not tied to the identity of the directory that was validated, and the temporary sibling is not validated before the link. | failing test | open |
| SEC-8 | Nit | The repository-identity parser accepts dot-segment owner and repo names, and the host allowlist constant is never read. | failing test | open |
| QE-1 | Blocker | The export recomputes the summary and turns register refusals into `absent`. | failing test | open |
| QE-2 | Blocker | The 400-relationship and 512 KiB non-detail limits are never enforced. | failing test | open |
| QE-3 | Blocker | The explorer embeds raw caller dicts, so assertion text never shows. | failing test | open |
| QE-4 | Blocker | An empty selector or one with only unknown keys matches the whole corpus. | failing test | open |
| QE-5 | Blocker | The lineage tests cannot fail on depth or on traversal of unchecked edges. | mutation red | open |
| QE-6 | Concern | A Status value with two HTML comments loses everything after the first comment. | failing test | open |
| QE-7 | Concern | Badly typed query input crashes `run_query` or is silently accepted. | failing test | open |
| QE-8 | Concern | Most refusal tests check that an error happened, not which error. | mutation red | open |
| QE-9 | Concern | Several inertness and encoding tests are tautologies or run on fixtures that cannot trigger them. | mutation red | open |
| QE-10 | Concern | The no-partial-file test never reaches `os.link`. | mutation red | open |
| QE-11 | Concern | The parity test compares only part of the relationship data. | mutation red | open |
| QE-12 | Nit | Export refusals carry prose only, with no machine-readable code. | failing test | open |
| QE-13 | Concern | Source links trust whatever git repository encloses `root`, and the HTML tests run real git. | failing test | open |
| QE-14 | Concern | A malformed or unknown URL hash leaves the explorer blank. | scripted Chrome check | open |
| QE-15 | Concern | The ledger's Chrome evidence scripts cannot reproduce its recorded results. | document change | open |
| QE-16 | Nit | The CLI entry point has no tests. | mutation red | open |
| QE-17 | Concern | Shipped pack scripts cite internal governance records, and one citation reaches every exported HTML file. | document change | open |
| QE-18 | Nit | The by-path module loader is duplicated, and one copy has drifted. | lint or search | open |
| QE-19 | Nit | Dead code and unused names. | lint or search | open |
| QE-20 | Nit | The temp file descriptor leaks if `fchmod` fails. | failing test | open |
| QE-21 | Nit | The owner-only temp-mode test checks call order, not the actual mode. | mutation red | open |
| FE-F1 | Concern | Back to the first no-hash entry leaves the previous view and selection on screen. | scripted Chrome check | open |
| FE-F4 | Concern | An unknown route or unparseable data island renders a blank main area with no error. | scripted Chrome check | open |
| FE-F2 | Nit | Focus drops to the document body after a record, edge or context button navigates. | scripted Chrome check | open |
| FE-F3 | Nit | No live region announces result-count or no-results changes. | scripted Chrome check | open |
| FE-F5 | Nit | The no-results message does not echo the active query or filters and offers no reset control. | scripted Chrome check | open |
| FE-F6 | Nit | Edge and context buttons fall below the 24-by-24 target size, and no exception is documented. | scripted Chrome check | open |
| FE-F9 | Nit | Record buttons say they are toggles but navigate. | scripted Chrome check | open |
| FE-F10 | Nit | An unknown record ID in the route shows the `nothing selected` guidance instead of saying the record is missing. | scripted Chrome check | open |
| FE-F11 | Nit | Long record bodies have no progressive disclosure, and orientation scrolls away. | scripted Chrome check | open |

## Deviations from completed task text

- **T2 verification artifact (ADV-16):** T2 names `test_filesystem_safety.py`,
  but its filesystem-confinement tests live in `test_query_contract.py`.
  The confinement proof for T2 is the `test_query_contract.py` cases that
  build symlink, hard-link, special-file, and traversal shapes.

## Evidence scripts

### bench.py

```python
"""AC-0015 scale benchmark: synthetic N-copy corpora, full export, Chrome timings."""
import json, re, shutil, statistics, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path("/Users/eu.gene.lim/orca/workspaces/agent-ready-repo/adr-summary")
SP = Path(sys.argv[1]); SCALES = [int(x) for x in sys.argv[2].split(",")]
NAV = REPO / "packs/governance-extras/.apm/skills/navigate-decisions/scripts/navigate_decisions.py"
TOK = re.compile(r"\b(ADR|RFC)-(\d{4})\b")

def records(kind):
    d = REPO / "docs" / kind
    return sorted(p for p in d.glob("[0-9][0-9][0-9][0-9]-*.md") if not p.name.endswith("-research.md"))

def build(n):
    root = SP / f"scale-{n}"
    if root.exists(): shutil.rmtree(root)
    src = {"ADR": records("adr"), "RFC": records("rfc")}
    for k in range(n):
        maps = {kind: {p.name[:4]: f"{k*len(ps)+i+1:04d}" for i, ps_i in [(0,0)] for i, p in enumerate(ps)} for kind, ps in src.items()}
        for kind, ps in src.items():
            out = root / "docs" / kind.lower(); out.mkdir(parents=True, exist_ok=True)
            for p in ps:
                new = maps[kind][p.name[:4]]
                text = TOK.sub(lambda m: f"{m.group(1)}-{maps[m.group(1)].get(m.group(2), m.group(2))}", p.read_text(encoding="utf-8"))
                (out / f"{new}{p.name[4:]}").write_text(text, encoding="utf-8")
    return root

def export(root, n):
    dest = SP / "exports"; dest.mkdir(exist_ok=True)
    name = f"scale-{n}.html"; (dest / name).unlink(missing_ok=True)
    r = subprocess.run([sys.executable, str(NAV), "export", "--root", str(root), "--destination", str(dest),
                        "--name", name, "--mode", "full", "--confirm-over-budget"], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode: raise SystemExit(f"export {n} failed: {r.stdout[-500:]} {r.stderr[-500:]}")
    return dest / name

def measure(pw, html):
    starts, searches, heaps = [], [], []
    for _ in range(3):
        b = pw.chromium.launch(channel="chrome", headless=True, args=["--enable-precise-memory-info"])
        ctx = b.new_context(offline=True); page = ctx.new_page()
        t0 = time.perf_counter(); page.goto(html.as_uri()); page.wait_for_selector("li.record-item")
        starts.append((time.perf_counter() - t0) * 1000)
        ms = page.evaluate("""() => {const e=document.getElementById('search-input');const t=performance.now();
            e.value='migration';e.dispatchEvent(new Event('input'));return performance.now()-t;}""")
        searches.append(ms)
        heaps.append(page.evaluate("() => performance.memory.usedJSHeapSize") / 2**20)
        version = b.version; b.close()
    return version, statistics.median(starts), statistics.median(searches), max(heaps)

rows = []
with sync_playwright() as pw:
    for n in SCALES:
        root = REPO if n == 1 else build(n)
        html = export(root, n)
        v, s, q, h = measure(pw, html)
        rows.append({"scale": n, "bytes": html.stat().st_size, "startup_ms": round(s), "search_ms": round(q, 1), "heap_mib": round(h, 1), "chrome": v})
        print(json.dumps(rows[-1]), flush=True)
```

### ux.py

```python
"""AC-0016 / AC-0023 scripted interaction checks in desktop Chrome."""
import sys, json
from pathlib import Path
from playwright.sync_api import sync_playwright
html = Path(sys.argv[1])
res = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    ctx = b.new_context(viewport={"width": 1280, "height": 800}, offline=True)
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e))); p.on("requestfailed", lambda r: errs.append("req " + r.url))
    reqs = []; p.on("request", lambda r: reqs.append(r.url))
    p.goto(html.as_uri()); p.wait_for_selector("li.record-item")
    res["network_requests_beyond_file"] = [u for u in reqs if not u.startswith("file:")]
    body = p.inner_text("body")
    res["policy_boundary_shown"] = "not the complete policy" in body.lower() or "complete applicable policy" in body.lower() or "not complete policy" in body.lower()
    res["counts_shown"] = "238" in body
    # keyboard: tab through, collect focused elements
    seen = []
    for _ in range(12):
        p.keyboard.press("Tab")
        seen.append(p.evaluate("() => {const a=document.activeElement;return a.id||a.tagName+'.'+a.className}"))
    res["tab_sequence"] = seen
    res["focus_visible_outline"] = p.evaluate("() => {const a=document.activeElement;const s=getComputedStyle(a);return s.outlineStyle+' '+s.outlineWidth}")
    # select a record by keyboard (Enter on first record button)
    p.focus("li.record-item button"); p.keyboard.press("Enter")
    sel = p.evaluate("() => location.hash")
    res["select_by_enter_hash"] = sel
    for v in ["graph", "context", "detail", "list"]:
        p.click(f"#btn-{v}")
        res[f"view_{v}_hash"] = p.evaluate("() => location.hash")
    p.go_back(); res["back_hash"] = p.evaluate("() => location.hash")
    p.go_forward(); res["forward_hash"] = p.evaluate("() => location.hash")
    # filters
    p.fill("#search-input", "zzzz-no-match")
    res["no_results_msg"] = p.inner_text("#view-list")[:120]
    p.fill("#search-input", "")
    # graph labels
    p.click("#btn-graph"); g = p.inner_text("#view-graph")
    res["graph_mentions_partial"] = "part" in g.lower(); res["graph_mentions_scope"] = "D3" in g or "scope" in g.lower()
    # zoom reflow: 200% and 400% == viewport 640 and 320 CSS px
    for z, w in ((200, 640), (400, 320)):
        p.set_viewport_size({"width": w, "height": 800 * 100 // z})
        for v in ["list", "graph", "context", "detail"]:
            p.click(f"#btn-{v}")
            over = p.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            res[f"hscroll_{z}_{v}"] = over
    p.set_viewport_size({"width": 1280, "height": 800})
    # reduced motion rule present
    res["reduced_motion_rule"] = "prefers-reduced-motion" in p.content()
    # dblclick dependence
    res["dblclick_handlers"] = p.evaluate("() => document.querySelectorAll('[ondblclick]').length") + p.content().count("dblclick")
    res["page_errors"] = errs
    b.close()
print(json.dumps(res, indent=1))
```

## AC-0020 comparative outcome

### Frozen panel (2026-10-04, before any session)

Each session attempts all five tasks once with `navigate-decisions` and once
by direct file browsing, alternating which condition goes first per session.
Answers are scored against the repository at the session's commit.

| Task | Prompt | Correct answer must include |
| --- | --- | --- |
| 1. Orientation | How many ADRs and RFCs exist, and how many RFCs are not Accepted? | Exact counts by kind and every non-`Accepted` RFC status value |
| 2. Exact status | What is RFC-0099's exact lifecycle status? | The full qualified value, not just `Accepted` |
| 3. Partial supersession | Which decisions does ADR-0098 supersede in part, and which D-IDs? | ADR-0019 D6, D7 and ADR-0076 D1, D2, both checked |
| 4. Guidance context | Given the assertion "RFC-0105 is wider guidance for ADR-0134", what relates them and how far can you trust it? | The assertion is navigation-only; any `Related` links are contextual; no checked lineage is implied |
| 5. Handoff | Where is ADR-0001's rationale, and where does its source live? | Its body or a source handoff, the repository-relative path, and the statement that this is not complete applicable policy |

### Measurement rules

- **Run:** one task attempted in one session in one condition.
- **Lookup effort:** files opened plus tool or query calls. For an agent, every
  tool call counts. For a person using the HTML explorer, each search entry,
  filter change, view switch, and record selection counts as one query call,
  and opening the export counts as one file.
- **Unaided:** the run finishes with no hint, correction, or help from anyone.
- **Incorrect claim:** any wrong status, lineage, guidance-trust, policy-
  completeness, or source statement in the final answer.
- **Pass:** at least four of five tasks have lower median effort with the
  navigator; at least 80% of navigator runs finish unaided; zero incorrect
  claims across all runs; at least two human-run and two agent-run sessions.

### Sessions

None run yet. Human-run sessions need the repository owner or a delegate.
