# Verification ledger: the readiness bridge reads work-loop's dispatch output

## Owner approvals of wording (AC-0027)

| Target | Wording | Approval |
| --- | --- | --- |
| `docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md` § Errata (AC-0022) | the 2026-10-29 entry ending the 2026-10-12 D3 exception as written and admitting `dispatch.py`'s output | eugenelim (owner), 2026-10-29T15:19-05:00 |
| `docs/rfc/0108-skill-html-view-standard.md` § Errata (AC-0023) | the 2026-10-29 entry: D3's bridge reads `work-loop`'s argless `dispatch.py` output | eugenelim (owner), 2026-10-29T15:19-05:00 |
| `docs/rfc/0106-stop-registering-derivable-work.md` § Errata (AC-0024) | the 2026-10-29 spec registration stop entry, item (2), the readiness bridge's first-ready mark | eugenelim (owner), 2026-10-29T15:19-05:00 |

## Evidence runs (T6)

Every run below ran against `d7f440ad7b3bddd63aed788039bd42d5da473554` (`git rev-parse HEAD`; clean tree) on 29 October 2026, between 18:48 and 19:05 US Central. Machine: Apple M5 Pro, 15 logical CPUs, 24 GiB, macOS (Darwin 25.5.0), Python 3 with the standard library only for the exports; load average (1, 5 and 15 minutes) was 27, 21, 18 at 18:48 and 10, 14, 16 by 18:58. Scratch files lived under the ignored `.context/rb/`; exports were written to a `/tmp` directory, because the export refuses a destination inside the repository.

### AC-0016: this repository's dispatch output

Inputs: `python3 packs/core/.apm/skills/work-loop/scripts/dispatch.py --root .` (exit 0, 16,792 bytes) and `python3 packs/core/.apm/skills/workspace-status/scripts/workspace_status.py status --root .` (exit 0, 54,456 bytes).

| Stdout of | SHA-256 |
| --- | --- |
| `dispatch.py --root .` | `96d8f586fcb5315e3187f56734d8832eb35397b7119541c25f47a69c6c9f3a7f` |
| `workspace-status status` | `66b8b5417974a1341e8b2aab48107a724d8719299780d1e6a5a50a3f3a262a01` |

`export --root . --readiness - --destination <tmp>` with the dispatch bytes: exit 0, `ok`, 788,414 bytes, `readiness` `{"checked": true, "reason": null}`. The script below (SHA-256 `140ca8c374f10e3069797247015e1ec2a13641d1be4c370d4ddb57e99cfe4273`; it imports nothing from the navigator) read the same bytes and the export's loaded records (804):

| | active | ready | blocked | start |
| --- | --- | --- | --- | --- |
| Script, by the spec's terms | 5 | 0 | 0 | `ask`, `id` null, `held` false, `active_count` 5 |
| Export's `readiness` | 5 | 0 | 0 | the same |

The script printed `MATCH`. The decision in the bytes is `ask` over the five active specs, so no row is marked. The same export command with the `workspace-status status` bytes returned `ok` with `readiness` `{"checked": false, "reason": "wrong_schema"}`. Result: pass.

```python
"""Count dispatch.py output by the spec's terms; imports nothing from the navigator.

Usage: count.py <export.html> <dispatch-output-file>
Prints the counts and start the spec's terms give, then the export's own readiness
projection, then MATCH or DIFFER.
"""
import json
import re
import sys

html = open(sys.argv[1], encoding="utf-8").read()
block = re.search(r'<script type="application/json" id="intent-data">(.*?)</script>', html, re.S)
payload = json.loads(block.group(1))
loaded = {n["path"]: n["id"] for n in payload["nodes"] if n.get("path")}

d = json.load(open(sys.argv[2], encoding="utf-8"))
active, ready, blocked = d["active"], d["ready"], d["blocked"]
if len(active) == 1:
    rule, chosen = "resume", active[0]["path"]
elif len(active) > 1:
    rule, chosen = "ask", None
elif len(ready) == 1:
    rule, chosen = "start", ready[0]["path"]
elif len(ready) > 1:
    rule, chosen = "ask", None
else:
    rule, chosen = "none", None
assert d["decision"]["action"] == rule, (d["decision"]["action"], rule)
ident = loaded.get(chosen) if chosen else None
mine = {
    "active": sum(1 for e in active if e["path"] in loaded),
    "ready": sum(1 for e in ready if e["path"] in loaded),
    "blocked": len({e["path"] for e in blocked if e["path"] in loaded}),
    "start": {"rule": rule, "id": ident, "held": False, "active_count": len(active)},
}
r = payload["readiness"]
theirs = {"active": len(r["active"]), "ready": len(r["ready"]), "blocked": len(r["blocked"]),
          "start": r["start"]}
print("script:", json.dumps(mine))
print("export:", json.dumps(theirs), "checked", r.get("checked"), "reason", r.get("reason"))
print("loaded_records", len(loaded), "MATCH" if mine == theirs else "DIFFER")
```

### AC-0017: scale and the largest input

**Scale.** `.context/browser-venv/bin/python packs/core/tests/skills/navigate-intents/view_bench.py --source . --counts 1 10 25 50 --readiness .context/rb/dispatch.json`, with the `dispatch.json` of AC-0016 (SHA-256 `96d8f586...3f7f`, 16,792 bytes), exit 0, about 9 minutes. Thresholds are the export spec's criterion 0066: at most 104,857,600 bytes, startup at most 3,000 ms, search at most 300 ms, heap at most 1,024 MiB.

| Copies | Outstanding available | Default rows | File bytes | Startup ms | Search ms | Heap MiB | Meets all | Readiness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | yes | 0 | 807,821 | 26 | 30 | 6 | yes | checked, reason null |
| 10 | no (`resource_limit`, files) | 0 | 5,641,173 | 66 | 64 | 12 | yes | checked, reason null |
| 25 | no (`resource_limit`, files) | 0 | 13,867,357 | 107 | 57 | 27 | yes | checked, reason null |
| 50 | no (`resource_limit`, files) | 0 | 27,577,660 | 178 | 55 | 54 | yes | checked, reason null |

Every corpus meets every threshold. `default rows` is the benchmark's own count for its default question and stays 0 here; AC-0018 below counts the "What can I work on next?" rows. `outstanding` is unavailable from 10 copies up, as in the export's own benchmark.

**Largest input.** The script below (SHA-256 `ad6cb84c7deda50970aef8d533ad67aa2b4e63b8c4615505f7888e458d2c6fc1`) wrote `max.json`, exactly 4,194,304 bytes (SHA-256 `71cfbaee12fb94e9030ede3d567df00aa69086048f1c70b2edc1a0e479ff4497`): 15,251 blocked items over this repository's 606 `docs/specs/*/spec.md` paths, each with one `unsatisfied_dependency` finding, `active` and `ready` empty, the argless decision `none`, padded with JSON whitespace. Three timed `export --root . --readiness -` runs (load average 9.7 to 9.8 at the start of each) all exited 0 with `ok` and `readiness` `{"checked": true, "reason": null}`, writing 887,319 bytes whose `readiness` holds 606 blocked records, `start` `none`:

| Run | Seconds | Within 5 s |
| --- | --- | --- |
| 1 | 1.98 | yes |
| 2 | 1.44 | yes |
| 3 | 1.55 | yes |
| no-flag baseline | 1.47 | yes |

Result: pass.

```python
"""Write a 4,194,304-byte readiness input: blocked items naming loaded paths.

Usage: gen_max.py <repo root> <out file>
One blocked item per docs/specs/*/spec.md path (repeated until the size is reached),
each with one finding; active and ready are empty and the decision is the argless none.
The tail is padded with spaces (JSON whitespace) to exactly 4,194,304 bytes.
"""
import json, pathlib, sys

root, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
paths = sorted(p.relative_to(root).as_posix() for p in root.glob("docs/specs/*/spec.md"))
LIMIT = 4_194_304
finding = {"code": "unsatisfied_dependency", "path": None, "dispatchable": False,
           "next_action": "Complete or explicitly revise the dependency."}

def item(path):
    return {"path": path, "slug": path.split("/")[2], "status": "Implementing", "findings": [finding]}

head = '{"schema_version": 1, "ready": [], "active": [], "blocked": ['
tail = '], "findings": [], "decision": {"action": "none", "path": null, "candidates": [], "findings": []}}'
parts, size, i = [], len(head) + len(tail), 0
while True:
    text = json.dumps(item(paths[i % len(paths)]))
    add = len(text) + (2 if parts else 0)
    if size + add > LIMIT:
        break
    parts.append(text); size += add; i += 1
body = head + ", ".join(parts) + tail
body += " " * (LIMIT - len(body.encode()))
out.write_bytes(body.encode())
print(len(parts), "entries", len(paths), "distinct paths", out.stat().st_size, "bytes")
```

### AC-0018: the real export in headless Chromium

The AC-0016 export (`export --root . --readiness -` with the dispatch bytes), opened in headless Chromium through `.context/browser-venv/bin/python` (Playwright), viewport 1280 by 900, with no page errors.

| Question | Rows | Rail count | Expected |
| --- | --- | --- | --- |
| "What can I work on next?" | 5, each with the Active mark, under the heading "Active" | 5 | `readiness` holds 5 records (5 active, 0 ready, 0 blocked) |
| "What is broken?" | 0 ("Nothing is broken.") | 0 | 0 workspace broken entries, because `readiness.blocked` holds no finding |

The line below the list header reads "work-loop with no spec named asks which of the 5 active items to resume, so none is marked." This repository has no blocked or ready item at this commit, so the "What is broken?" count is 0 and the criterion's every-workspace-broken-entry clause holds for an empty set; the 4 MiB export of AC-0017 (606 blocked records) was not opened in the browser. Result: pass.

### AC-0029: the full browser run

`.context/browser-venv/bin/python -m pytest packs/core/tests/skills/navigate-intents/view_browser_checks.py -q -rs -n 4 -p no:cacheprovider` at `d7f440ad7`: 509 passed, none skipped, in 339.87 s. The `test-corpus.yml` dispatch half of AC-0029 is not recorded here.

### AC-0011: the hostile workspace.toml through dispatch

A copy of the `mixed` fixture with `fixtures/hostile_workspace/workspace.toml` as its `workspace.toml`. `dispatch.py --root <copy>` exited 0. Its stdout holds 0 of the 10 hostile strings (`</script><script>`, `<img src=x`, `onerror`, `javascript:`, `"><svg`, `alert(1)`, U+2028, U+2029, U+202E, U+200F), counted both raw and JSON-escaped. `export --root <copy> --readiness -` with those bytes returned `ok`, 173,281 bytes, `readiness` `{"checked": true, "reason": null}`, and none of the 10 strings appears outside the data block. Result: pass.
