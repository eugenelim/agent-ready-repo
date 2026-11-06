#!/usr/bin/env python3
# agentbundle-fixture-launcher:not-a-host
"""TEST FIXTURE: a launcher that simulates a host able to attest containment and reads.

This file is a test fixture, not a host. It enforces nothing: it speaks the launcher
protocol the supervisor expects so the supervisor's own checks can be driven. It carries
the fixture marker above, so the supervisor refuses it unless a test enables its in-process
seam, and it must never be installed, built, or reachable outside the test corpus.

A test copies this file with ``SCRIPT`` replaced by the behaviour to simulate (see
``launcher_support.make_launcher``). Keys, all optional:

* ``log``: a directory the fixture writes ``recv.log`` (raw lines received), ``env.json``
  (argv, environment, working directory, open descriptors) and ``events.log`` into;
* ``reads``: the declared reads it echoes as its allowlist and attests as read;
* ``write``: ``{path: text | null}``, files it creates (null deletes) in the attempt directory;
* ``fifo`` / ``links``: a FIFO path and ``{path: target}`` links it creates there;
* ``containment``: overrides merged into the containment attestation; ``containment_drop``:
  keys removed from it; ``denied_drop``: denial names removed; ``containment_raw``: text sent
  in place of the line; ``containment_pad``: bytes of padding that make the line too long;
  ``silent``: never send the containment line;
* ``access`` / ``access_drop``: the same for the access attestation; ``access_raw``;
  ``access_pad``; ``access_extra``: a second line; ``token``: a token to send instead;
  ``envelope_binding``: overrides for the envelope's binding; ``denied_reads``; ``complete``;
  ``processes_ended``;
* ``binding_override`` / ``access_binding_override``: fields replaced in the attested binding;
  ``tamper_glob``: files it rewrites before attesting (a worker acting as the same user);
* ``per_task``: ``{task id prefix: overrides}``, merged over the script for the attempt whose
  task id starts with the prefix; ``wait_for``: a path the attempt waits for before its access
  line; ``touch``: a path it creates after sending the access line (together they finish
  attempts in a chosen order);
* ``on_abort``: ``"exit"`` (default) or ``"ignore"``; ``hold``: wait on the gate file before
  the access line; ``never_access``: never send it; ``child``: leave a sleeping child in the
  process group; ``release_wait``: ``"never"`` sends access without waiting for release.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT = None  # SCRIPT-SLOT

DENIALS = [
    "git-common-dir", "shared-refs", "run-store", "work-trees", "sibling-trees", "sibling-ipc",
]


def note(name, text):
    log = SCRIPT.get("log")
    if log:
        with (Path(log) / name).open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")


def emit(text):
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def read():
    raw = sys.stdin.buffer.readline()
    if not raw:
        return None
    note("recv.log", raw.decode("utf-8", "replace").rstrip("\n"))
    return json.loads(raw)


def wait_gate():
    gate = SCRIPT.get("gate")
    while gate and not Path(gate).exists():
        time.sleep(0.02)


def main():
    global SCRIPT
    if SCRIPT.get("log"):
        fds = []
        for fd in range(3, 256):
            try:
                os.fstat(fd)
            except OSError:
                continue
            fds.append(fd)
        target = Path(SCRIPT["log"]) / "env.json"
        with target.with_suffix(".tmp").open("w", encoding="utf-8") as handle:
            json.dump(
                {"argv": sys.argv, "env": dict(os.environ), "cwd": os.path.realpath("."),
                 "cwd_listing": [p.name for p in Path().iterdir()], "extra_fds": fds,
                 "pgid": os.getpgrp(), "pid": os.getpid()},
                handle,
            )
        target.with_suffix(".tmp").replace(target)
    for pattern in SCRIPT.get("tamper_glob", []):
        for path in Path("/").glob(pattern.lstrip("/")):
            path.chmod(0o700)
            path.write_bytes(b"tampered")
    message = read()
    if message is None:
        return 0
    own = message.get("request", {}).get("task", {}).get("task_id")
    for prefix, overrides in SCRIPT.get("per_task", {}).items():
        if own and own.startswith(prefix):
            SCRIPT = {**SCRIPT, **overrides}
    binding, attempt_dir = message["binding"], message["attempt_dir"]
    grant = message["grant"]
    allowlist = grant["product_read_proof_mode"] == "allowlist"
    reads = SCRIPT.get("reads", [])
    attestation = {
        "schema_version": 1,
        "host_mechanism": "fixture-os-sandbox",
        "principal_or_sandbox": "fixture",
        "roots": [attempt_dir],
        "limits": {},
        "read_enforcement": "allowlist" if allowlist else "trace",
        "network": {"allowed": False},
        "children": {"allowed": True},
        "binding": {**binding, **SCRIPT.get("binding_override", {})},
        "write_roots": [attempt_dir],
        "denied": [d for d in DENIALS if d not in SCRIPT.get("denied_drop", [])],
    }
    if allowlist:
        attestation["read_allowlist"] = list(reads)
    attestation.update(SCRIPT.get("containment", {}))
    for key in SCRIPT.get("containment_drop", []):
        attestation.pop(key, None)
    if not SCRIPT.get("silent"):
        if "containment_raw" in SCRIPT:
            emit(SCRIPT["containment_raw"])
        else:
            envelope = {"schema_version": 1, "type": "containment", "binding": binding,
                        "attestation": attestation}
            if SCRIPT.get("containment_pad"):
                envelope["pad"] = "x" * SCRIPT["containment_pad"]
            emit(json.dumps(envelope))
    if SCRIPT.get("child"):
        subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(120)"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    if SCRIPT.get("release_wait") == "never":
        reply = {"type": "release", "release_token": "0" * 64}
    else:
        reply = read()
    if reply is None:
        return 0
    if reply["type"] == "abort":
        if SCRIPT.get("on_abort") == "ignore":
            while True:
                time.sleep(0.05)
        return 0
    token = SCRIPT.get("token") or reply["release_token"]
    note("events.log", "released")
    # The simulated worker: writes only what the script says, inside the attempt directory.
    for rel, text in SCRIPT.get("write", {}).items():
        path = Path(attempt_dir) / rel
        if text is None:
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    if SCRIPT.get("fifo"):
        os.mkfifo(Path(attempt_dir) / SCRIPT["fifo"])
    for rel, target in SCRIPT.get("links", {}).items():
        path = Path(attempt_dir) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)
    if SCRIPT.get("hold"):
        wait_gate()
    waiting = SCRIPT.get("wait_for")
    deadline = time.time() + 60
    while waiting and not Path(waiting).exists() and time.time() < deadline:
        time.sleep(0.02)
    if SCRIPT.get("never_access"):
        while True:
            time.sleep(0.05)
    writes = [
        {"path": p, "kind": "delete" if t is None else "write"}
        for p, t in SCRIPT.get("write", {}).items()
    ]
    writes += [{"path": p, "kind": "write"} for p in SCRIPT.get("links", {})]
    access = {
        "schema_version": 1,
        "binding": {**binding, **SCRIPT.get("access_binding_override", {})},
        "release_token": token,
        "mode": "allowlist" if allowlist else "trace",
        "complete": SCRIPT.get("complete", True),
        "processes_ended": SCRIPT.get("processes_ended", True),
        "reads": SCRIPT.get("access_reads", [{"path": p, "kind": "file"} for p in reads]),
        "writes": SCRIPT.get("access_writes", writes),
        "denied_reads": SCRIPT.get("denied_reads", []),
    }
    access.update(SCRIPT.get("access", {}))
    for key in SCRIPT.get("access_drop", []):
        access.pop(key, None)
    outer = dict(binding)
    outer.update(SCRIPT.get("envelope_binding", {}))
    if "access_raw" in SCRIPT:
        emit(SCRIPT["access_raw"])
    else:
        envelope = {"schema_version": 1, "type": "access", "binding": outer, "attestation": access}
        if SCRIPT.get("access_pad"):
            envelope["pad"] = "x" * SCRIPT["access_pad"]
        emit(json.dumps(envelope))
    if SCRIPT.get("access_extra"):
        emit(SCRIPT["access_extra"])
    if SCRIPT.get("touch"):
        Path(SCRIPT["touch"]).write_text("done", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
