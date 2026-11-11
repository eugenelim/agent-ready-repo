"""Count a status output's readiness by the spec's terms, without the shipped module.

Usage: python ac0043_independent_count.py <export.html> <status-output-file> [<more files> ...]

``export.html`` supplies the loaded records (its data block's ``nodes``).  Each further
file is judged as a status input: accepted (and counted) or refused with a reason.  The
rules are written from the spec's terms (Status input, Entry, Finding, Ready, active and
blocked entry, Checked lists, Loaded record) and its criteria on the projection and the
argless work-loop mark.  This file imports nothing from the navigator.

Prints one JSON line per file, then ``accepted=<n> refused=<n>``.  When the export's own
readiness member is checked, the first accepted file's counts are compared with it.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

LIMIT = 4_194_304
CODE = re.compile(r"[a-z][a-z0-9_]{0,63}")
FATAL = {"invalid_workspace", "configuration_mismatch", "unsafe_path"}
LISTS = ("ready", "active", "blocked")


class Refused(Exception):
    """Carries the reason a status input is not accepted."""


def strict_json(raw: bytes) -> dict:
    """Parse bytes as one JSON object.

    Refuses repeats, NaN, Infinity, a byte-order mark and bad UTF-8.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("not_json") from None

    def pairs(items):
        names = [k for k, _ in items]
        if len(names) != len(set(names)):
            raise ValueError("repeat")
        return dict(items)

    def constant(name):
        raise ValueError(name)

    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, RecursionError):
        raise Refused("not_json") from None
    if not isinstance(value, dict):
        raise Refused("not_json")
    return value


def check_finding(f) -> None:
    ok = (isinstance(f, dict) and isinstance(f.get("code"), str) and CODE.fullmatch(f["code"])
          and isinstance(f.get("dispatchable"), bool) and isinstance(f.get("next_action"), str)
          and len(f["next_action"]) <= 500
          and not any(0xD800 <= ord(c) <= 0xDFFF for c in f["next_action"]))
    if not ok:
        raise Refused("wrong_schema")


def check_entry(e) -> None:
    if not (isinstance(e, dict) and isinstance(e.get("path"), str)
            and isinstance(e.get("dispatchable"), bool) and isinstance(e.get("findings"), list)):
        raise Refused("wrong_schema")
    for f in e["findings"]:
        check_finding(f)


def all_findings(canon: dict) -> list:
    return canon["findings"] + [f for k in LISTS for e in canon[k] for f in e["findings"]]


def judge(raw: bytes) -> dict:
    """Return the checked lists of an accepted status input, or raise Refused."""
    if len(raw) > LIMIT:
        raise Refused("too_large")
    if raw.strip(b" \t\n\r") == b"":
        raise Refused("empty")
    top = strict_json(raw)
    if top.get("workspace_present") is False:
        raise Refused("no_workspace")
    canon = top.get("canonical")
    sv = top.get("schema_version")
    valid = (top.get("workspace_present") is True and type(sv) is int and sv == 1
             and top.get("mode") == "status" and top.get("workspace_root") == "."
             and isinstance(canon, dict) and canon.get("performed") is True
             and all(isinstance(canon.get(k), list) for k in (*LISTS, "findings")))
    if not valid:
        raise Refused("wrong_schema")
    for e in canon["ready"] + canon["active"] + canon["blocked"]:
        check_entry(e)
    for f in canon["findings"]:
        check_finding(f)
    # Ready: dispatchable, no finding.  Active: no finding.  Blocked: not dispatchable, a finding.
    if not all(e["dispatchable"] and not e["findings"] for e in canon["ready"]):
        raise Refused("wrong_schema")
    if not all(not e["findings"] for e in canon["active"]):
        raise Refused("wrong_schema")
    if not all(not e["dispatchable"] and e["findings"] for e in canon["blocked"]):
        raise Refused("wrong_schema")
    seen: dict[str, str] = {}
    for kind in LISTS:
        for e in canon[kind]:
            if seen.setdefault(e["path"], kind) != kind:
                raise Refused("wrong_schema")
    if any(f["code"] in FATAL for f in all_findings(canon)):
        raise Refused("bad_workspace")
    return canon


def count(canon: dict, loaded: dict[str, str]) -> dict:
    """Counts over loaded records, plus the argless work-loop mark decided before any drop."""
    active = [e for e in canon["active"] if e["path"] in loaded]
    ready = [e for e in canon["ready"] if e["path"] in loaded]
    blocked: dict[str, list[str]] = {}
    for e in canon["blocked"]:
        if e["path"] in loaded:
            codes = blocked.setdefault(e["path"], [])
            for f in e["findings"]:
                if f["code"] not in codes:
                    codes.append(f["code"])
    n_active = len(canon["active"])
    if n_active == 1:
        rule, chosen = "resume", canon["active"][0]
    elif n_active > 1:
        rule, chosen = "ask", None
    elif canon["ready"]:
        rule, chosen = "start", canon["ready"][0]
    else:
        rule, chosen = "none", None
    ident, held = None, False
    if chosen is not None:
        held = any(f.get("path") == chosen["path"] for f in all_findings(canon))
        if chosen["path"] in loaded and not held:
            ident = loaded[chosen["path"]]
    return {"active": len(active), "ready": len(ready), "blocked": len(blocked),
            "codes": sum(len(c) for c in blocked.values()),
            "start": {"rule": rule, "id": ident, "held": held, "active_count": n_active}}


def loaded_records(export_html: str) -> tuple[dict[str, str], dict]:
    pattern = r'<script type="application/json" id="intent-data">(.*?)</script>'
    block = re.search(pattern, export_html, re.S)
    if block is None:
        raise SystemExit("no data block")
    payload = json.loads(block.group(1))
    return {n["path"]: n["id"] for n in payload["nodes"] if n.get("path")}, payload


def main(argv: list[str]) -> int:
    loaded, payload = loaded_records(pathlib.Path(argv[0]).read_text(encoding="utf-8"))
    accepted = refused = 0
    first = None
    for name in argv[1:]:
        raw = pathlib.Path(name).read_bytes()
        record: dict = {"file": pathlib.Path(name).name, "sha256": hashlib.sha256(raw).hexdigest(),
                        "bytes": len(raw)}
        try:
            result = count(judge(raw), loaded)
        except Refused as exc:
            refused += 1
            record["refused"] = str(exc)
        else:
            accepted += 1
            record["accepted"] = result
            first = first or result
        print(json.dumps(record))
    print(f"accepted={accepted} refused={refused} loaded_records={len(loaded)}")
    member = payload.get("readiness", {})
    if member.get("checked") is True and first is not None:
        theirs = {"active": len(member["active"]), "ready": len(member["ready"]),
                  "blocked": len(member["blocked"]),
                  "codes": sum(len(b["findings"]) for b in member["blocked"]),
                  "start": member["start"]}
        print("MATCH" if theirs == first else f"DIFFER export={json.dumps(theirs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
