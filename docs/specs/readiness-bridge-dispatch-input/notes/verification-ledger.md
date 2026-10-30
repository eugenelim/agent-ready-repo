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

### Design review screenshots (AC-0030)

Thirty-two PNGs in `screens/`, named `<state>-<width>-<theme>.png`, taken at commit `b575c1908` with `.context/browser-venv/bin/python .context/rbd-shots/screenshots.py <repo root> <out dir>` (script SHA-256 `9455af39ed26bae7dccbb5ff62920598d4c2ddf264103f4137adbc8e69b6d26c`, below). Each is a true viewport capture in headless Chromium: widths 320 (height 900), 1280 (900), 1680 (1000) and 2560 (1400), each with `color_scheme` light and dark, over real exports of the `mixed` fixture made with `export --readiness -`.

- `checked-start`: one ready item (bravo-spec) and one blocked item (golf-new, codes `unsatisfied_dependency` and `missing_plan`).
- `checked-ask`: `_NAMED_STATUS["ask_ready"]`, two ready items, so `active_count` is 0 and the note reads "asks which ready item to start, so none is marked."
- `check-failed`: the stdout shape of `workspace-status status` piped in, giving `wrong_schema` and the "Readiness could not be checked" notice.
- `broken-findings`: the `checked-start` input, opened at `#q=broken`.

The `experience-reviewer` pass and each finding's disposition are not recorded here yet.

| SHA-256 | File |
| --- | --- |
| `205697e1dc8d9ff8e9dc724a58e16d41cdeefb159dc90391d9dcca7112c9f5f1` | `screens/broken-findings-1280-dark.png` |
| `c5bd2714995458e19ffc74e07e6106e1c785fc7b2be4171a19567e6f373f5de4` | `screens/broken-findings-1280-light.png` |
| `e0cb5eed9369230b3d207f124471783dd02281fb805d424284d8ce9f76721b3b` | `screens/broken-findings-1680-dark.png` |
| `00e1c12665894a930d5fe1775fe2e97662ff3ca072463dd69b9676e61a74e51c` | `screens/broken-findings-1680-light.png` |
| `c2543a42aa7905861b1a30af937626c3b5ab85ad5c87e44455fa03190ab4a6c5` | `screens/broken-findings-2560-dark.png` |
| `148f1188c69e95b87e0374f6d5d60d5c7de986a2d55c218675069a3d9a4a879c` | `screens/broken-findings-2560-light.png` |
| `7eb10fa12625ab359d255c6d843d8dce3dd2ad266b49e4750dab0be68e0ab6cc` | `screens/broken-findings-320-dark.png` |
| `6c02b7406e224d92d496403ade79802374b9df52749c6162366134bc673cccea` | `screens/broken-findings-320-light.png` |
| `d707e41067accebb6dcfa86bf539487a25b6598864eb5275556a91d0e8d1c379` | `screens/check-failed-1280-dark.png` |
| `96de58f0452098089a670a90f1bfde52c4345210151fb5d4d67f9a7be069d91d` | `screens/check-failed-1280-light.png` |
| `9871ae0c00ea11cc8b0659ed3ed61339a6a8908d96d83b8c0561f552d4eef0d2` | `screens/check-failed-1680-dark.png` |
| `bbd5b00b98f0cddf3754845ba4c072d46ed98ac000d9ca4b483225fd18d8a1a2` | `screens/check-failed-1680-light.png` |
| `fd64075f3eb03e8e0d11212b5acf5651dceb0c67a7d743841ee53d5f3e5c114f` | `screens/check-failed-2560-dark.png` |
| `f88bbb272701a5faaf197c9886b7b7ac617993ac4f50f78019b81cb112e648ec` | `screens/check-failed-2560-light.png` |
| `a3b761514ec54c479fb4818bed36ac8f0a0805313b1d3133372fd1cb05fa8596` | `screens/check-failed-320-dark.png` |
| `6cd754f98330ef124752fa20ca0c8334ce7db53ad88b66891b4c3cd43a7d635d` | `screens/check-failed-320-light.png` |
| `22e6c78d40cee8c3456b931c1080196053e62ce84b6555e059a8746c46aa1ae3` | `screens/checked-ask-1280-dark.png` |
| `40d2a2f4d5230b4e08111de9b8f7e1c4b528dd0e2163cba540e2a921545892b7` | `screens/checked-ask-1280-light.png` |
| `91ba38c7f23889f37abd22009b3dd6fbe0d4bd5a5918c16606b7008fb7f09957` | `screens/checked-ask-1680-dark.png` |
| `871a9d7cecda3e59e826b77c31126897b7b48568f3b9125baa5d3be40da3a3f6` | `screens/checked-ask-1680-light.png` |
| `8dc5302b3a6194bb9df77973e99161138f126672a540e18e9967075a51af1647` | `screens/checked-ask-2560-dark.png` |
| `bc1a38c1ad483f3a74f9300db720183e6b3f9e483d6c6556cb287debca287a42` | `screens/checked-ask-2560-light.png` |
| `47ae7c7ca2637a50dc4402237ccc43e673b223e12c7f8dee9b820b46c4dfeb47` | `screens/checked-ask-320-dark.png` |
| `05866b4a0c760f65cd853601e06ed6c000a28cf3fb05594fa4ea0de8aa86fdac` | `screens/checked-ask-320-light.png` |
| `596d97fbd7435705f5a62eeddfab3f2952e0aa3e81bcb5811c56c878dc354152` | `screens/checked-start-1280-dark.png` |
| `ee2b8599c6356bb953a51fc0c1ed56e4ed304ec386ccf50972fb8312e670f414` | `screens/checked-start-1280-light.png` |
| `b519934b17e47c7671e70c5bf822008bfbf4735338e583aaba41dbb77dcc40b3` | `screens/checked-start-1680-dark.png` |
| `57c9d453ee3a54998ad2483d15860b70bbcf303f1c751f7ede05ed460823817f` | `screens/checked-start-1680-light.png` |
| `bb45182dbe703f9b5d69fd1aa652a3bd015895da90cad5346527dce3285c3d4b` | `screens/checked-start-2560-dark.png` |
| `b5c79e4245d57dff2cbfa6d1d3cfeab7d74e1984c130cb2baad168c4627f13fe` | `screens/checked-start-2560-light.png` |
| `b83cfda66164bcd3feddfe013ddc169e6dc04030173f54f28f378094c43964ac` | `screens/checked-start-320-dark.png` |
| `4cc837ecedf299dc5018b7f55776f57f964bd6e301f8264bb11a71a6dcedf6c3` | `screens/checked-start-320-light.png` |

Script:

```python
"""Usage: python screenshots.py <repo root> <out dir>

AC-0030: 4 states x widths 320/1280/1680/2560 x light/dark = 32 PNGs over real exports of the
`mixed` fixture made with `export --readiness -`.  Base inputs come from the `_r_*` builders in
view_browser_checks.py.  Prints each file's SHA-256.
"""
import hashlib, json, pathlib, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright

root, out = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
sys.path.insert(0, str(root / "packs/core/tests/skills/navigate-intents"))
import view_browser_checks as v  # noqa: E402

script = root / "packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py"
fixture = root / "packs/core/tests/skills/navigate-intents/fixtures/mixed"
# workspace-status `status` stdout: not this spec's input, so the check fails with wrong_schema.
WS_STATUS = json.dumps({
    "schema_version": 1, "mode": "status", "workspace_present": True, "workspace_root": ".",
    "canonical": {"performed": True, "bounded": True, "findings": [],
                  "ready": [], "active": [], "blocked": []},
}).encode()
start = v._r_status(ready=[v._r_entry(v._R_BRAVO)],
                    blocked=[v._r_blocked(v._R_GOLF, "unsatisfied_dependency", "missing_plan")])
INPUTS = {
    "checked-start": (v._r_bytes(start), "#q=next"),
    "checked-ask": (v._r_bytes(v._NAMED_STATUS["ask_ready"]), "#q=next"),
    "check-failed": (WS_STATUS, "#q=next"),
    "broken-findings": (v._r_bytes(start), "#q=broken"),
}
WIDTHS = {320: 900, 1280: 900, 1680: 1000, 2560: 1400}
READY = "() => performance.getEntriesByName('view-ready').length > 0"
out.mkdir(parents=True, exist_ok=True)
tmp = pathlib.Path(tempfile.mkdtemp())
pages = {}
for state, (data, _f) in INPUTS.items():
    proc = subprocess.run(
        [sys.executable, str(script), "export", "--root", str(fixture), "--destination", str(tmp),
         "--name", f"{state}.html", "--readiness", "-"], input=data, capture_output=True, check=True)
    result = json.loads(proc.stdout)
    assert result["status"] == "ok", result
    pages[state] = pathlib.Path(result["path"])
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for state, (_d, fragment) in INPUTS.items():
        for width, height in WIDTHS.items():
            for theme in ("light", "dark"):
                ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme=theme)
                page = ctx.new_page()
                page.goto(pages[state].as_uri() + fragment)
                page.wait_for_function(READY)
                page.screenshot(path=str(out / f"{state}-{width}-{theme}.png"))
                ctx.close()
    browser.close()
for png in sorted(out.glob("*.png")):
    print(hashlib.sha256(png.read_bytes()).hexdigest(), png.name)
```

### Re-capture with reduced motion

Re-captured 2026-10-29 at code commit `9262782c7` with the same script plus `reduced_motion="reduce"` on each browser context, so the detail fade cannot be caught partway (experience-reviewer Minor 1). These SHA-256 values replace the list above:

```
f2a21c4c36c4bdcd2332e1ce7ed32744d8e402ba25b7749b30e51a0026e8726a broken-findings-1280-dark.png
98cda9ebcf82513ade0231ac1b4bcebd65053003ceaed159c52615a091402a44 broken-findings-1280-light.png
715876be05b1d6d6cfdd9d6044fffdbacdb79a7eda5fe723ded1ed4fed302e1e broken-findings-1680-dark.png
23330a7ad03f487e132c936476ab61f15d09d52b382c12a388accf98a76dd5b3 broken-findings-1680-light.png
50049f4b49abdfbc5d1feb654378104e314b0beb000d183f70d0236f06bf9e3a broken-findings-2560-dark.png
c54bf1e45c01666d8027774131aaf76ccf673b661b24f2a258748e71f56937b3 broken-findings-2560-light.png
2d7ef59580663a7bb298c2897e427376ee874ca7c24f0a69bee8072001ff478e broken-findings-320-dark.png
a7dec8f014cf5d4d05937c28f8f25aafae46432d204d2139dfc0310926fe0f59 broken-findings-320-light.png
1bdd626e3e2f877cb0cbb7b15007de03c651d57b012cb5366e2f644f06e05b62 check-failed-1280-dark.png
4d7cb32e003e0900033820b4122caef957d66c099847a1408674a4dbc0bc65ba check-failed-1280-light.png
07a1543ed97aec16335e791483a75cc95f4afa7630d602cd8e663028ccd86c82 check-failed-1680-dark.png
95fb5343232c6c06b405ad0e94534983c2300e50c7cf98ae3262db815781079b check-failed-1680-light.png
3e350459ec0efc1375fb4587d5356874c196bdd95f77f3b32f19e04e0d15a6a6 check-failed-2560-dark.png
5516424849b48fafeca8067267b31036b4b15a85775a807cdfa0733f48ea58bd check-failed-2560-light.png
492a444a86e52421c290cc846145c4d7041db0c377a12696fb5340b78971b461 check-failed-320-dark.png
40440d56ebb3128665e1280724ffa94708f660376fb7a35a240bcbe11cb408ac check-failed-320-light.png
89fbf43100e8839d65d0f344f955797b8e5e58bb309042b3e09463d0fc7a71e2 checked-ask-1280-dark.png
6bc6ee94189c6842cf0c24092ffe0467919dc718e833936ccb39fd5cbc70add3 checked-ask-1280-light.png
dbc3b65d1947d11ec000f69cfb90eab582b70e65e93dfd09bcd6328b4af99bd6 checked-ask-1680-dark.png
fdc4264b66270520fcaeaa637f5bea79a09ad8d1d1800adae9b78ca4e0034e92 checked-ask-1680-light.png
1d53026bebfea9eab8af2fd47ee3f5471943e37f44790cad17076298ffeb2e15 checked-ask-2560-dark.png
98ca50e76dace239a76dc948018aa6609c359f80807ec83423154fedec6df8d7 checked-ask-2560-light.png
c5fbb20930ed43a5c1820b26f809e8312a445c72bf3ffb3d5b9991347f0bd0a5 checked-ask-320-dark.png
f5757f7d471c9582f6daa4a857d8ced6a973feb7d0c169a05533be08cc6ab02b checked-ask-320-light.png
28419a7dda705a82066768ddb83bc657bbce914c6b2ee612345a19403111963d checked-start-1280-dark.png
2cf8a60ea1685e2be37b304b031b4b6951c74a4407c84e08ff45d04ba073d03e checked-start-1280-light.png
d2b30631e87b8e082bc3dbdefb2a941e42af2856fce5c28a055f69edfd75c045 checked-start-1680-dark.png
77278f31b72c00b844ca49ba3a87943bbae409998508be9a33f2358085a6e867 checked-start-1680-light.png
a3ae7f0cbecf57c1efad730c0b2f83aab4499ee005d620cfce097cc498e013ca checked-start-2560-dark.png
2e5c289eb6498de9695f4fe95e5a0c4059cd7ca2896137cf23e7d639d2ceda14 checked-start-2560-light.png
7f869bc6b706540b8d158800a69d992deda10b41ee08be75e52858121cbf3ccd checked-start-320-dark.png
174125523fa1c7367d7e7fc312863ac7d60e43b2556df3de1193c6129151211e checked-start-320-light.png
```

## Design review result (AC-0030)

An `experience-reviewer` pass over the 32 screenshots, against RFC-0108 D1 rules 1 to 10 as corrected and the `skill-html-views` direction's ranked goals, returned no Blocker and no Major finding: 3 Minors and 4 Advisories. After adjudication every finding is refuted, so none remains:

| Finding | Severity | Disposition |
| --- | --- | --- |
| E1, detail placeholder captured mid-fade | Minor | Refuted: the screenshots were re-captured with reduced motion (SHA-256 values above) and the placeholder is settled |
| E2, start tag shares the meta style with the owner line | Minor | Refuted: the owner line is the cell `intent-view-record-owners` AC-0008 requires; a styling preference with no named rule |
| E3, rows carry a second owner line | Minor | Refuted: moving the owner cell would break `intent-view-record-owners` AC-0008, which this spec does not change |
| E4, first answer sits low at 320 px | Advisory | Refuted: the first screen at 320 px holds the list header, the note and the first row (D1 rule 1) |
| E5, two broken rows look alike | Advisory | Refuted: one entry per workspace finding, each with its own code (AC-0015) |
| E6, failure notice apart from the lead line | Advisory | Refuted: the notice sits above the list as AC-0014 states |
| E7, empty band at 2560 px | Advisory | Refuted: all four widths were captured; no D1 rule is broken |

Records: `.context/reviews/f020b46e-afb2-45b9-89ba-5e179f11f89e/1-post-gates-experience-reviewer-raw.md` and `-adjudication.md`.
