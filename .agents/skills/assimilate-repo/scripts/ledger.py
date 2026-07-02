#!/usr/bin/env python3
"""The resumable assimilation ledger (RFC-0059 D7, ADR-0048).

Two-part user-scope scratch under `~/.agentbundle/catalogue-curation/`:

  * per-run  `<run-id>/ledger.toml`      — append-only, purged on completion.
  * per-source `sources/<hash>/last-synced.toml` — durable, purge-exempt.

`<run-id>` and `<source-hash>` are **deterministic** salted hashes of the source
(a per-installation salt, no per-invocation stamp), so a resumed run and a
sibling git worktree derive the same id and share one ledger. State is keyed on
stable identity, never commit SHAs.

The run-ledger schema **forbids a free-text reason field** (verdict is an enum;
no verbatim source content may drift in) — the inbound-confidentiality ceiling
ADR-0048 also gives the durable marker. Pure-stdlib: `tomllib` reads,
append-serialization writes (append-only fits TOML array-of-tables).

`base_dir` and `salt` are injectable for tests; production defaults to
`~/.agentbundle/catalogue-curation/` and a generated per-installation salt.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tomllib
from datetime import date
from pathlib import Path

VERDICTS = frozenset({"assimilate", "reject", "needs-new-pack"})
STATUSES = frozenset({"pending", "done"})
# The ONLY keys a ledger entry may carry — a free-text 'reason' is rejected.
ENTRY_KEYS = frozenset({"path", "name", "content_hash", "verdict", "status", "destination"})


class LedgerSchemaError(ValueError):
    """An entry violated the ledger schema (bad key, verdict, or status)."""


def default_base() -> Path:
    return Path(os.path.expanduser("~")) / ".agentbundle" / "catalogue-curation"


def _salt(base: Path) -> str:
    """Per-installation salt; generated once and reused."""
    p = base / ".salt"
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    base.mkdir(parents=True, exist_ok=True)
    salt = hashlib.sha256(os.urandom(32)).hexdigest()
    # 0600: the salt only defends run-id unpredictability, but don't leak it to
    # other local users even if the parent dir mode is later loosened.
    fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(salt)
    return salt


def _digest(source: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}\x00{source}".encode()).hexdigest()[:16]


def run_id(source: str, *, base: Path | None = None, salt: str | None = None) -> str:
    base = base or default_base()
    return _digest(source, salt or _salt(base))


def source_hash(source: str, *, base: Path | None = None, salt: str | None = None) -> str:
    base = base or default_base()
    return _digest(source, salt or _salt(base))


def _run_dir(source: str, base: Path, salt: str | None) -> Path:
    return base / _digest(source, salt or _salt(base))


def _toml_escape(v: str) -> str:
    # Escape backslash, quote, and the control chars TOML basic strings forbid,
    # so a crafted field can never break out of `key = "..."` (defense in depth;
    # validate_entry rejects controls outright — this covers content_hashes too).
    return (
        v.replace("\\", "\\\\").replace('"', '\\"')
        .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    )


def validate_entry(entry: dict) -> None:
    extra = set(entry) - ENTRY_KEYS
    if extra:
        raise LedgerSchemaError(f"disallowed ledger key(s) {sorted(extra)} (no free-text fields)")
    missing = {"path", "name", "content_hash", "verdict", "status"} - set(entry)
    if missing:
        raise LedgerSchemaError(f"missing required key(s) {sorted(missing)}")
    if entry["verdict"] not in VERDICTS:
        raise LedgerSchemaError(f"verdict {entry['verdict']!r} not in {sorted(VERDICTS)}")
    if entry["status"] not in STATUSES:
        raise LedgerSchemaError(f"status {entry['status']!r} not in {sorted(STATUSES)}")
    # A control character in any string field would corrupt the append-only TOML
    # (basic strings can't span lines) and brick every later read — reject it.
    for key, val in entry.items():
        if isinstance(val, str) and any(ord(ch) < 0x20 and ch not in "\t" for ch in val):
            raise LedgerSchemaError(f"field {key!r} contains a control character (forbidden)")


def append_entry(source: str, entry: dict, *, base: Path | None = None, salt: str | None = None) -> None:
    """Validate and append one candidate entry to the run ledger (append-only)."""
    base = base or default_base()
    validate_entry(entry)
    d = _run_dir(source, base, salt)
    d.mkdir(parents=True, exist_ok=True)
    led = d / "ledger.toml"
    lines = ["", "[[entry]]"]
    for k in ("path", "name", "content_hash", "verdict", "status", "destination"):
        if k in entry:
            lines.append(f'{k} = "{_toml_escape(str(entry[k]))}"')
    with led.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def read_entries(source: str, *, base: Path | None = None, salt: str | None = None) -> list[dict]:
    base = base or default_base()
    led = _run_dir(source, base, salt) / "ledger.toml"
    if not led.exists():
        return []
    with led.open("rb") as fh:
        return tomllib.load(fh).get("entry", [])


def done_names(source: str, *, base: Path | None = None, salt: str | None = None) -> set[str]:
    """Candidate names already resolved — a re-run/worktree skips these."""
    return {e["name"] for e in read_entries(source, base=base, salt=salt) if e.get("status") == "done"}


# ── durable per-source marker (purge-exempt) ────────────────────────────────
def _marker_path(source: str, base: Path, salt: str | None) -> Path:
    return base / "sources" / _digest(source, salt or _salt(base)) / "last-synced.toml"


def record_sync(source: str, content_hashes: list[str], *, base: Path | None = None,
                salt: str | None = None, today: str | None = None) -> None:
    """Append a dated sync baseline to the durable marker (never overwrites)."""
    base = base or default_base()
    m = _marker_path(source, base, salt)
    m.parent.mkdir(parents=True, exist_ok=True)
    stamp = today or date.today().isoformat()
    hashes = ", ".join(f'"{_toml_escape(h)}"' for h in content_hashes)
    with m.open("a", encoding="utf-8") as fh:
        fh.write(f'\n[[synced]]\ndate = "{stamp}"\nhashes = [{hashes}]\n')


def baseline(source: str, *, base: Path | None = None, salt: str | None = None) -> set[str]:
    """The most-recent synced content-hash set (empty if never synced)."""
    base = base or default_base()
    m = _marker_path(source, base, salt)
    if not m.exists():
        return set()
    with m.open("rb") as fh:
        synced = tomllib.load(fh).get("synced", [])
    return set(synced[-1]["hashes"]) if synced else set()


def classify(content_hash: str, base_set: set[str], known_names: set[str], name: str) -> str:
    """unchanged | changed | new — against the durable baseline."""
    if content_hash in base_set:
        return "unchanged"
    return "changed" if name in known_names else "new"


def purge_run(source: str, *, base: Path | None = None, salt: str | None = None) -> None:
    """Remove the per-run ledger dir on completion; the durable per-source
    marker under sources/ is left intact (purge-exempt)."""
    base = base or default_base()
    d = _run_dir(source, base, salt)
    if d.exists():
        shutil.rmtree(d)
