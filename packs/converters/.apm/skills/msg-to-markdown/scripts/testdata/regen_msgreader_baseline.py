#!/usr/bin/env python3
"""Regenerate `msgreader_baseline.json` — the AC3 independent-reader oracle.

Writes the `msg_fixtures.corpus()` `.msg` fixtures, reads each with the mature
Node `msgreader` package (a *different* implementation from this skill's
olefile+MAPI reader), and records the fields both readers can be compared on
(subject, recipient emails, attachment names). `test_parity.py` asserts this
skill's extraction equals both the fixtures' authored ground truth AND this
committed capture — a genuinely independent codebase agreeing on the same bytes.

Prerequisites: Node.js and the `msgreader` npm package resolvable (e.g.
`npm i msgreader` then run with `NODE_PATH=<node_modules> python3 <this>`).
`@nicecode/msg-reader` is a 404 phantom on npm; `msgreader` is the working reader.

Usage:
    NODE_PATH=/path/to/node_modules python3 regen_msgreader_baseline.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
sys.path.insert(0, str(SCRIPTS))

import msg_fixtures as fx  # noqa: E402

_NODE = r"""
const fs = require('fs'), path = require('path');
const R = require('msgreader').default || require('msgreader');
const dir = process.argv[1];
const names = JSON.parse(fs.readFileSync(path.join(dir, 'names.json')));
const out = {};
for (const n of names) {
  const m = new R(fs.readFileSync(path.join(dir, n + '.msg'))).getFileData();
  out[n] = {
    subject: m.subject || null,
    recipientEmails: (m.recipients || []).map(r => r.email).filter(Boolean).sort(),
    attachmentNames: (m.attachments || []).map(a => a.fileName || a.name).filter(Boolean).sort(),
  };
}
process.stdout.write(JSON.stringify(out, null, 2) + "\n");
"""


def main() -> int:
    d = Path(tempfile.mkdtemp())
    names = []
    for name, spec, _truth in fx.corpus():
        safe = name.replace(" ", "_")
        fx.write_msg(str(d / (safe + ".msg")), spec)
        names.append(safe)
    (d / "names.json").write_text(json.dumps(names))

    proc = subprocess.run(["node", "-e", _NODE, str(d)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        sys.stderr.write("\nEnsure Node + the `msgreader` package are available "
                         "(npm i msgreader; NODE_PATH=<node_modules>).\n")
        return 1
    (HERE / "msgreader_baseline.json").write_text(proc.stdout)
    print(f"wrote {HERE / 'msgreader_baseline.json'} for {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
