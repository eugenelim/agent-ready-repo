#!/usr/bin/env python3
"""ADR shape lint: check every decision record in a directory.

Usage:  lint-adr-shape.py <dir>

Checks each .md candidate in <dir> (every *.md entry excluding README.md)
against the fifteen check classes in the spec.  Exits 1 when any finding is
reported or when any candidate is not in the read bucket.  Exits 0 only when
there are no findings and every candidate was read successfully.

The fifteen check classes (spec AC table):
  ADR-S001  Status — value in the allowed token set
  ADR-S002  Date — YYYY-MM-DD, not the template placeholder
  ADR-S003  Areas — present and non-empty
  ADR-S004  Areas — arity cap (at most 3)
  ADR-S005  Areas — per-token shape [a-z0-9_-]+, no repeated token
  ADR-S006  Reversibility — value in {high, low}
  ADR-S007  Four supersession fields — present, none or well-formed entries
  ADR-S008  Supersedes ∩ Supersedes in part — no shared ordinal
  ADR-S009  Cited D-ID — exists in the record the entry names
  ADR-S010  Supersession entry — has its mirrored counterpart
  ADR-S011  ## Decision — D-IDs dense from D1, no gap or duplicate
  ADR-S012  **Revisit if:** in ## Consequences — present and non-empty
  ADR-S013  ## Confirmation (present) — Mode, Signal, Owner present and non-empty
  ADR-S014  ## Alternatives considered (present) — non-empty
  ADR-S015  Correction section heading — exactly ## Errata

Value domains are owned by RFC-0102 §§ 1-3, 5; this file implements them.
"""
from __future__ import annotations

import importlib.util
import os
import re
import stat
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path

# ── Helper loading ──────────────────────────────────────────────────────────────
# Loaded by path so scripts/ is never put on sys.path (packs/AGENTS.md :29-33).
# Pattern follows check-spec-status.py:69-114 and index-records.py:44-97.

SCRIPT_DIR: Path = Path(__file__).resolve().parent


class _HelperUnavailable(RuntimeError):
    """_record_paths.py could not be loaded; every operation must refuse."""


_helper_module: types.ModuleType | None = None


def _load_helper() -> types.ModuleType:
    """Load the sibling _record_paths.py by path, once per process.

    Refuses for every failure mode: missing path, non-regular file, None
    spec/loader, exec_module raising, and a module missing a required entry
    point.  A silent fallback would ship a broken control undetected.
    """
    global _helper_module
    if _helper_module is not None:
        return _helper_module
    path = SCRIPT_DIR / "_record_paths.py"
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise _HelperUnavailable(
            f"cannot load {path}: {exc}. Restore or re-run `make build-self`."
        ) from exc
    if not stat.S_ISREG(info.st_mode):
        raise _HelperUnavailable(
            f"cannot load {path}: not a regular file. "
            "Restore or re-run `make build-self`."
        )
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(
            "new_adr_lint_record_paths", str(path)
        )
        if spec is None or spec.loader is None:
            raise _HelperUnavailable(
                f"cannot load {path}: no import spec. "
                "Restore or re-run `make build-self`."
            )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except _HelperUnavailable:
        raise
    except BaseException as exc:
        raise _HelperUnavailable(
            f"cannot load {path}: {type(exc).__name__}: {exc}. "
            "Restore or re-run `make build-self`."
        ) from exc
    finally:
        sys.dont_write_bytecode = previous
    for name in ("list_candidate_entries", "classify_entry", "read_confined", "EntryRefused"):
        if not hasattr(module, name):
            raise _HelperUnavailable(
                f"cannot load {path}: missing entry point {name!r}. "
                "Restore or re-run `make build-self`."
            )
    _helper_module = module
    return module


# ── Value domains (RFC-0102 §§ 1-3) ────────────────────────────────────────────

_STATUS_TOKENS: frozenset[str] = frozenset(
    {"Proposed", "Accepted", "Rejected", "Deprecated", "Superseded"}
)
_REVERSIBILITY_TOKENS: frozenset[str] = frozenset({"high", "low"})
_AREAS_TOKEN_RE = re.compile(r"^[a-z0-9_-]+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATE_PLACEHOLDER = "YYYY-MM-DD"   # template sentinel — fail if unchanged

# Supersession field field-name classifiers
_FULL_SUPERS_FIELDS = frozenset({"Supersedes", "Superseded by"})
_PART_SUPERS_FIELDS = frozenset({"Supersedes in part", "Superseded in part"})
_ALL_SUPERS_FIELDS = _FULL_SUPERS_FIELDS | _PART_SUPERS_FIELDS

# Correction section: the only valid heading and the alternatives ADR-S015 catches
_ERRATA_HEADING = "## Errata"
# ADR-S015's subject is "a correction section", so a heading the matcher does
# not recognise is one the class cannot check at all — such a section evades
# the append-only rule entirely rather than being reported for its spelling.
# The matcher therefore covers the correction-log nouns, not only the two
# variants RFC-0102 § 5 observed, with an optional parenthetical or dated
# suffix.
#
# The heading must be the noun ALONE. A first attempt matched the stem plus
# any trailing words and immediately misfired on a real record — ADR-0105's
# `## Corrected transition table`, which is a content section holding a
# corrected table, not a correction log.
#
# BLIND SPOT, stated rather than implied: a correction log headed with none of
# these nouns (say `## Notes`) is still invisible. Recognition by enumeration
# cannot be completed; this names what it misses instead of implying coverage.
# Python refuses int() on very long digit strings; a record-controlled D-ID
# must be rejected as malformed rather than allowed to raise mid-scan.
_D_ID_MAX_DIGITS = 6

_CORRECTION_RE = re.compile(
    r"^## (?:Errata|Erratum|Amendment|Amendments|Correction|Corrections)"
    r"\s*(?:\([^)]*\))?$",
    re.IGNORECASE,
)

# Metadata field: optional "- " bullet; key in **Key:** bold
_META_FIELD_RE = re.compile(
    r"^(?:- )?\*\*"
    r"(Status|Date|Areas|Reversibility"
    r"|Supersedes|Supersedes in part|Superseded by|Superseded in part"
    r"|Decision-makers|Consulted|Informed|Related)"
    r":\*\*\s*(.*?)(?:\s*<!--.*?-->)?\s*$"
)

# Confirmation sub-fields; Mode may carry an "(Dn)" override per RFC-0102 § 2
_CONF_FIELD_RE = re.compile(
    r"^(?:- )?\*\*(Mode|Signal|Owner)(?:\s+\([^)]+\))?:\*\*"
    r"\s*(.*?)(?:\s*<!--.*?-->)?\s*$"
)

# Revisit if in ## Consequences (only checked inside that section)
_REVISIT_RE = re.compile(
    r"^(?:- )?\*\*Revisit if:\*\*\s*(.*?)(?:\s*<!--.*?-->)?\s*$"
)

# D-ID definition in ## Decision: "- **D<n>:**" list item (RFC-0102 :191-200)
# Only this form defines a D-ID; "**D<n>...**" elsewhere is a restatement.
_D_DEF_RE = re.compile(r"^- \*\*D(\d+):\*\*")


# ── Record data model ────────────────────────────────────────────────────────────

@dataclass
class _Record:
    path: Path
    ordinal: str | None = None       # 4-digit string from filename, e.g. "0001"
    status: str | None = None
    date: str | None = None
    areas: str | None = None         # raw comma-separated value
    reversibility: str | None = None
    supersedes: str | None = None
    supersedes_in_part: str | None = None
    superseded_by: str | None = None
    superseded_in_part: str | None = None
    d_ids: list[int] = field(default_factory=list)   # defined D-IDs, in parse order
    oversized_d_ids: list[str] = field(default_factory=list)  # reported, not converted
    has_consequences: bool = False
    revisit_if: str | None = None    # effective Revisit if value
    has_confirmation: bool = False
    conf_mode: str | None = None
    conf_signal: str | None = None
    conf_owner: str | None = None
    has_alternatives: bool = False
    alternatives_nonempty: bool = False
    correction_heading: str | None = None  # actual heading text if present


# ── Parsing ─────────────────────────────────────────────────────────────────────

def _strip_comment(s: str) -> str:
    """Strip a trailing <!-- … --> HTML comment and surrounding whitespace."""
    return re.sub(r"\s*<!--.*?-->\s*$", "", s).strip()


def _read_field_value(lines: list[str], i: int, same_line: str) -> str:
    """Return the effective value for the field whose key is on line i.

    If same_line is non-empty, return it.  Otherwise look for a block value
    in one of two corpus-attested forms (AC-0008):

    Form 1 — indented continuation lines immediately following:
        - **Signal:**
          - item a
          - item b

    Form 2 — blank line then unindented list:
        **Revisit if:**

        - item a
        - item b

    Returns the collected text, or '' when neither form applies.
    """
    if same_line:
        return same_line
    # Form 1: next line starts with whitespace
    if i + 1 < len(lines) and lines[i + 1] and lines[i + 1][0] in " \t":
        parts: list[str] = []
        j = i + 1
        while j < len(lines) and lines[j] and lines[j][0] in " \t":
            parts.append(lines[j].strip())
            j += 1
        return " ".join(parts)
    # Form 2: blank line followed by "- " list items
    if i + 1 < len(lines) and lines[i + 1] == "":
        j = i + 2
        parts = []
        while j < len(lines) and lines[j].startswith("- "):
            parts.append(lines[j])
            j += 1
        if parts:
            return "\n".join(parts)
    return ""


def _parse(path: Path, text: str) -> _Record:
    """Parse a decision-record text body into a _Record."""
    rec = _Record(path=path)

    m = re.match(r"^(\d+)-", path.name)
    if m:
        rec.ordinal = m.group(1)

    lines = text.splitlines()
    section: str | None = None   # current ## heading text (None = preamble)
    in_meta = True                  # still in the pre-section metadata block

    for i, line in enumerate(lines):
        # Section headings
        if line.startswith("## "):
            heading = line[3:].strip()
            section = heading
            in_meta = False

            if heading == "Consequences":
                rec.has_consequences = True
            elif heading == "Confirmation":
                rec.has_confirmation = True
            elif heading == "Alternatives considered":
                rec.has_alternatives = True

            # Correction section detection (ADR-S015)
            if _CORRECTION_RE.match(line):
                rec.correction_heading = line.strip()
            continue

        # ── Metadata fields (before the first ## heading) ─────────────────────
        if in_meta:
            m2 = _META_FIELD_RE.match(line)
            if m2:
                key = m2.group(1)
                raw = _strip_comment(m2.group(2))
                val = _strip_comment(_read_field_value(lines, i, raw))

                if key == "Status":
                    rec.status = val or None
                elif key == "Date":
                    rec.date = val or None
                elif key == "Areas":
                    rec.areas = val or None
                elif key == "Reversibility":
                    rec.reversibility = val or None
                elif key == "Supersedes":
                    rec.supersedes = val or None
                elif key == "Supersedes in part":
                    rec.supersedes_in_part = val or None
                elif key == "Superseded by":
                    rec.superseded_by = val or None
                elif key == "Superseded in part":
                    rec.superseded_in_part = val or None

        # ── ## Decision: D-ID definitions ────────────────────────────────────
        if section == "Decision":
            m3 = _D_DEF_RE.match(line)
            if m3:
                digits = m3.group(1)
                # Bound before converting. AC-0005 makes read/refused/
                # unreadable exhaustive "including a classification that
                # raised"; an unbounded int() on a record-controlled digit run
                # raises ValueError above Python's conversion limit, which
                # aborts the scan with the record in no bucket at all.
                if len(digits) > _D_ID_MAX_DIGITS:
                    rec.oversized_d_ids.append(digits[:_D_ID_MAX_DIGITS] + "…")
                else:
                    rec.d_ids.append(int(digits))

        # ── ## Consequences: Revisit if ───────────────────────────────────────
        if section == "Consequences":
            m4 = _REVISIT_RE.match(line)
            if m4:
                raw = _strip_comment(m4.group(1))
                val = _strip_comment(_read_field_value(lines, i, raw))
                rec.revisit_if = val or None

        # ── ## Confirmation: Mode, Signal, Owner ─────────────────────────────
        if section == "Confirmation":
            m5 = _CONF_FIELD_RE.match(line)
            if m5:
                key = m5.group(1)
                raw = _strip_comment(m5.group(2))
                val = _strip_comment(_read_field_value(lines, i, raw))
                if key == "Mode":
                    rec.conf_mode = val or None
                elif key == "Signal":
                    rec.conf_signal = val or None
                elif key == "Owner":
                    rec.conf_owner = val or None

        # ── ## Alternatives considered: non-empty detection ───────────────────
        if section == "Alternatives considered":
            stripped = line.strip()
            # Any non-empty, non-heading line counts as content
            if stripped and not stripped.startswith("##"):
                rec.alternatives_nonempty = True

    return rec


# ── Supersession grammar helpers ─────────────────────────────────────────────────

def _parse_entry_list(raw: str | None) -> list[str]:
    """Return stripped entries from a supersession field value.

    Returns [] for None, empty, or the 'none' sentinel.  Entries are split
    on ';' (RFC-0102 § 3: ';' separates entries, ',' separates D-IDs).
    """
    if not raw or raw.strip().lower() == "none":
        return []
    return [e.strip() for e in raw.split(";") if e.strip()]


def _entry_ordinal(entry: str) -> str | None:
    """Return 'ADR-NNNN' from a supersession entry, or None."""
    m = re.match(r"^(ADR-\d{4})\b", entry)
    return m.group(1) if m else None


def _entry_d_ids(entry: str) -> list[str]:
    """Return D-IDs from a partial-supersession entry ('ADR-NNNN D1, D2')."""
    # Format: ADR-NNNN D1[, D2, ...]
    m = re.match(r"^ADR-\d{4}\s+(D\d+(?:,\s*D\d+)*)$", entry)
    if not m:
        return []
    return [d.strip() for d in m.group(1).split(",")]


def _is_well_formed_full(entry: str) -> bool:
    """True when entry is exactly 'ADR-NNNN'."""
    return bool(re.match(r"^ADR-\d{4}$", entry))


def _is_well_formed_partial(entry: str) -> bool:
    """True when entry is 'ADR-NNNN' or 'ADR-NNNN D1[, D2...]'."""
    return bool(re.match(r"^ADR-\d{4}(?:\s+D\d+(?:,\s*D\d+)*)?$", entry))


# ── Per-record checks (ADR-S001 to ADR-S008, ADR-S011 to ADR-S015) ─────────────

Finding = tuple[str, str, str]   # (record_path_str, code, message)


def _check_record(rec: _Record) -> list[Finding]:
    """Run per-record checks. Returns a list of (path, code, message) triples."""
    out: list[Finding] = []
    p = str(rec.path)

    def add(code: str, msg: str) -> None:
        out.append((p, code, msg))

    # ADR-S001 — Status value
    if rec.status is None:
        add("ADR-S001", "Status field is absent or empty")
    elif rec.status not in _STATUS_TOKENS:
        tokens = ", ".join(sorted(_STATUS_TOKENS))
        add("ADR-S001", f"Status {rec.status!r} is not in {{{tokens}}}")

    # ADR-S002 — Date shape and not the placeholder
    if rec.date is None:
        add("ADR-S002", "Date field is absent or empty")
    elif rec.date == _DATE_PLACEHOLDER:
        add("ADR-S002", "Date is still the template placeholder 'YYYY-MM-DD'")
    elif not _DATE_RE.match(rec.date):
        add("ADR-S002", f"Date {rec.date!r} does not match YYYY-MM-DD")

    # ADR-S003 — Areas present and non-empty
    if not rec.areas:
        add("ADR-S003", "Areas field is absent or empty")

    # ADR-S004 — Areas arity cap
    if rec.areas:
        tokens = [t.strip() for t in rec.areas.split(",") if t.strip()]
        if len(tokens) > 3:
            add("ADR-S004", f"Areas has {len(tokens)} tokens; at most 3 are allowed")

        # ADR-S005 — per-token shape and no repeated token
        bad = [t for t in tokens if not _AREAS_TOKEN_RE.match(t)]
        if bad:
            add("ADR-S005",
                "Areas token(s) with invalid shape (must match [a-z0-9_-]+): "
                + repr(bad))
        seen: set[str] = set()
        dups: list[str] = []
        for t in tokens:
            if t in seen:
                dups.append(t)
            seen.add(t)
        if dups:
            add("ADR-S005", f"Areas contains repeated token(s): {dups!r}")

    # ADR-S006 — Reversibility token
    if rec.reversibility is None:
        add("ADR-S006", "Reversibility field is absent or empty")
    elif rec.reversibility not in _REVERSIBILITY_TOKENS:
        add("ADR-S006",
            f"Reversibility {rec.reversibility!r} is not in {{'high', 'low'}}")

    # ADR-S007 — four supersession fields present and well-formed
    for fname, fval, is_partial in (
        ("Supersedes", rec.supersedes, False),
        ("Supersedes in part", rec.supersedes_in_part, True),
        ("Superseded by", rec.superseded_by, False),
        ("Superseded in part", rec.superseded_in_part, True),
    ):
        if fval is None:
            add("ADR-S007", f"Supersession field '{fname}' is absent")
            continue
        if fval.strip().lower() == "none":
            continue   # sentinel — always valid
        for entry in _parse_entry_list(fval):
            if is_partial:
                if not _is_well_formed_partial(entry):
                    add("ADR-S007",
                        f"'{fname}' entry {entry!r} is not well-formed "
                        "(expected 'ADR-NNNN' or 'ADR-NNNN D1[, D2...]')")
            else:
                if not _is_well_formed_full(entry):
                    add("ADR-S007",
                        f"'{fname}' entry {entry!r} is not well-formed "
                        "(expected 'ADR-NNNN')")

    # ADR-S008 — no ordinal in both Supersedes and Supersedes in part
    sup_ordinals = {
        _entry_ordinal(e)
        for e in _parse_entry_list(rec.supersedes)
        if _entry_ordinal(e)
    }
    sip_ordinals = {
        _entry_ordinal(e)
        for e in _parse_entry_list(rec.supersedes_in_part)
        if _entry_ordinal(e)
    }
    shared = sup_ordinals & sip_ordinals
    if shared:
        add("ADR-S008",
            f"Ordinal(s) appear in both 'Supersedes' and 'Supersedes in part': "
            f"{sorted(shared)!r}; choose one cardinality per target")

    # ADR-S011 — ## Decision D-IDs dense from D1, no gap or duplicate
    if rec.d_ids:
        d_list = rec.d_ids
        # Check duplicates first (sorted unique comparison would miss them)
        seen_d: set[int] = set()
        d_dups: list[int] = []
        for n in d_list:
            if n in seen_d:
                d_dups.append(n)
            seen_d.add(n)
        sorted_unique = sorted(seen_d)
        expected = list(range(1, len(sorted_unique) + 1))
        if d_dups:
            add("ADR-S011", f"Duplicate Decision D-ID(s): {d_dups!r}")
        if sorted_unique != expected:
            add("ADR-S011",
                f"Decision D-IDs {sorted_unique!r} are not dense from D1 "
                f"(expected {expected!r})")

    # Reported outside the `if rec.d_ids:` block above: when every D-ID in a
    # record is oversized, `d_ids` is empty and that block never runs, so the
    # finding this exists to raise would be dropped by the guard.
    if rec.oversized_d_ids:
        add("ADR-S011",
            f"Decision D-ID(s) with more than {_D_ID_MAX_DIGITS} digits: "
            f"{rec.oversized_d_ids!r}")

    # ADR-S012 — non-empty Revisit if. Unconditional, unlike ADR-S013: the
    # spec's class table makes S013's subject "a PRESENT ## Confirmation" and
    # leaves S012's unqualified, so renaming or dropping the section must not
    # retire the check with it.
    if not rec.revisit_if:
        if rec.has_consequences:
            add("ADR-S012",
                "Consequences section has no non-empty '**Revisit if:**' line")
        else:
            add("ADR-S012",
                "no '**Revisit if:**' line (no '## Consequences' section "
                "either — the line is required regardless)")

    # ADR-S013 — ## Confirmation (when present): Mode, Signal, Owner non-empty
    if rec.has_confirmation:
        for fname, fval in (
            ("Mode", rec.conf_mode),
            ("Signal", rec.conf_signal),
            ("Owner", rec.conf_owner),
        ):
            if not fval:
                add("ADR-S013",
                    f"Confirmation section has absent or empty '{fname}'")

    # ADR-S014 — ## Alternatives considered (when present) non-empty
    if rec.has_alternatives and not rec.alternatives_nonempty:
        add("ADR-S014",
            "Alternatives considered section is present but has no content")

    # ADR-S015 — correction section heading exactly ## Errata
    if rec.correction_heading and rec.correction_heading != _ERRATA_HEADING:
        add("ADR-S015",
            f"Correction section heading is {rec.correction_heading!r}; "
            "must be exactly '## Errata'")

    return out


# ── Cross-record checks (ADR-S009, ADR-S010) ───────────────────────────────────

def _check_cross(records: dict[str, _Record]) -> list[Finding]:
    """Run cross-record checks (ADR-S009 and ADR-S010).

    Builds a map of ordinal-keyed records and verifies that every supersession
    entry has its mirrored counterpart, and that every cited D-ID exists in the
    named record.  A broken pair is reported on both records (AC-0004).
    """
    findings: list[Finding] = []
    seen: set[Finding] = set()

    def add(path: str, code: str, msg: str) -> None:
        f: Finding = (path, code, msg)
        if f not in seen:
            seen.add(f)
            findings.append(f)

    for rec in records.values():
        this_key = f"ADR-{rec.ordinal}" if rec.ordinal else None
        p = str(rec.path)

        # ADR-S009 — a cited D-ID is defined by the SUPERSEDED record.
        # RFC-0102 :229: "In both halves the D-IDs belong to the superseded
        # record."  Which record that is depends on the field's direction, and
        # resolving both to the named record reports a false positive on every
        # correct `Superseded in part` entry — three of them in this corpus,
        # each naming a D-ID its own record defines.
        for fname, fval in (
            ("Supersedes in part", rec.supersedes_in_part),
            ("Superseded in part", rec.superseded_in_part),
        ):
            for entry in _parse_entry_list(fval):
                target_key = _entry_ordinal(entry)
                if not target_key:
                    continue
                cited_d_ids = _entry_d_ids(entry)
                if not cited_d_ids:
                    continue
                if fname == "Supersedes in part":
                    # This record supersedes the named one: the named record
                    # is the superseded one, so it owns the D-IDs.
                    owner_key, owner = target_key, records.get(target_key)
                else:
                    # This record is superseded by the named one: this record
                    # is the superseded one, so it owns the D-IDs.
                    owner_key, owner = this_key, rec
                if owner is None:
                    continue   # ADR-S010 will report the missing record
                defined = {f"D{n}" for n in owner.d_ids}
                for did in cited_d_ids:
                    if did not in defined:
                        add(p, "ADR-S009",
                            f"'{fname}' entry {entry!r} cites {did} "
                            f"which is not defined in {owner_key}")

        # ADR-S010 — supersession mirroring (both sides)
        # Supersedes: ADR-X  ↔  ADR-X Superseded by: this
        for entry in _parse_entry_list(rec.supersedes):
            target_key = _entry_ordinal(entry)
            if not target_key:
                continue
            target = records.get(target_key)
            if target is None:
                add(p, "ADR-S010",
                    f"Supersedes: {target_key} but {target_key} "
                    "is not in this directory")
                continue
            target_sub = {
                _entry_ordinal(e)
                for e in _parse_entry_list(target.superseded_by)
            }
            if this_key not in target_sub:
                add(p, "ADR-S010",
                    f"Supersedes: {target_key} but {target_key} "
                    f"has no 'Superseded by: {this_key}'")
                add(str(target.path), "ADR-S010",
                    f"Missing 'Superseded by: {this_key}' "
                    f"mirroring {this_key}'s 'Supersedes: {target_key}'")

        # Superseded by: ADR-X  ↔  ADR-X Supersedes: this
        for entry in _parse_entry_list(rec.superseded_by):
            target_key = _entry_ordinal(entry)
            if not target_key:
                continue
            target = records.get(target_key)
            if target is None:
                add(p, "ADR-S010",
                    f"Superseded by: {target_key} but {target_key} "
                    "is not in this directory")
                continue
            target_sub = {
                _entry_ordinal(e)
                for e in _parse_entry_list(target.supersedes)
            }
            if this_key not in target_sub:
                add(p, "ADR-S010",
                    f"Superseded by: {target_key} but {target_key} "
                    f"has no 'Supersedes: {this_key}'")

        # Supersedes in part: ADR-X D1  ↔  ADR-X Superseded in part: this D1
        for entry in _parse_entry_list(rec.supersedes_in_part):
            target_key = _entry_ordinal(entry)
            if not target_key:
                continue
            target = records.get(target_key)
            if target is None:
                add(p, "ADR-S010",
                    f"Supersedes in part: {entry!r} but {target_key} "
                    "is not in this directory")
                continue
            # Build map of this_key → entry in target's Superseded in part
            target_sip: dict[str, str] = {}
            for te in _parse_entry_list(target.superseded_in_part):
                tk = _entry_ordinal(te)
                if tk:
                    target_sip[tk] = te
            if this_key not in target_sip:
                add(p, "ADR-S010",
                    f"Supersedes in part: {entry!r} but {target_key} "
                    f"has no 'Superseded in part: {this_key} ...' entry")
                add(str(target.path), "ADR-S010",
                    f"Missing 'Superseded in part: {this_key} ...' "
                    f"mirroring {this_key}'s 'Supersedes in part: {entry}'")
            elif set(_entry_d_ids(entry)) != set(
                    _entry_d_ids(target_sip[this_key])):
                # A present counterpart naming different D-IDs is not a mirror.
                # Both halves cite D-IDs defined by the superseded record, so
                # the two sets must be equal, not merely both non-empty.
                add(p, "ADR-S010",
                    f"Supersedes in part: {entry!r} but {target_key}'s "
                    f"counterpart {target_sip[this_key]!r} names different "
                    "D-IDs")
                add(str(target.path), "ADR-S010",
                    f"Superseded in part: {target_sip[this_key]!r} but "
                    f"{this_key}'s counterpart {entry!r} names different "
                    "D-IDs")

        # Superseded in part: ADR-X D1  ↔  ADR-X Supersedes in part: this D1
        for entry in _parse_entry_list(rec.superseded_in_part):
            target_key = _entry_ordinal(entry)
            if not target_key:
                continue
            target = records.get(target_key)
            if target is None:
                add(p, "ADR-S010",
                    f"Superseded in part: {entry!r} but {target_key} "
                    "is not in this directory")
                continue
            target_sup: dict[str, str] = {}
            for te in _parse_entry_list(target.supersedes_in_part):
                tk = _entry_ordinal(te)
                if tk:
                    target_sup[tk] = te
            if this_key not in target_sup:
                add(p, "ADR-S010",
                    f"Superseded in part: {entry!r} but {target_key} "
                    f"has no 'Supersedes in part: {this_key} ...' entry")
                # Attribute to both records, as the forward branch does: a
                # broken pair is a defect in the pair, and reporting one side
                # only makes the finding depend on which record was scanned.
                add(str(target.path), "ADR-S010",
                    f"Missing 'Supersedes in part: {this_key} ...' "
                    f"mirroring {this_key}'s 'Superseded in part: {entry}'")

    return findings


# ── Entry-level scan ─────────────────────────────────────────────────────────────

def _is_candidate(name: str) -> bool:
    """True when this filename is a lint candidate (*.md excluding README.md)."""
    return name.endswith(".md") and name != "README.md"


# ── Main ────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:  # noqa: C901
    """Entry point. Returns 0 on clean scan, 1 otherwise."""
    # Reconfigure streams to UTF-8 before the first print (packs/AGENTS.md).
    # `errors` is load-bearing, not decoration: a directory entry's name is
    # arbitrary bytes on Linux, and Python surfaces undecodable ones as
    # surrogates.  Under the default strict handler, naming such an entry
    # raises UnicodeEncodeError from the print itself — so the scan aborts on
    # the very path that exists to report it, accounting for no entry at all
    # and failing AC-0005's partition and AC-0031's controlled non-zero exit.
    # Guard the call: a redirected StringIO (used in tests) has no reconfigure.
    for _stream in (sys.stdout, sys.stderr):
        _r = getattr(_stream, "reconfigure", None)
        if _r is not None:
            _r(encoding="utf-8", errors="backslashreplace")

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print(
            f"usage: {Path(sys.argv[0]).name} <dir>",
            file=sys.stderr,
        )
        return 1

    # Load helper (errors already printed at module scope if it failed)
    try:
        helper = _load_helper()
    except _HelperUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    list_candidates = helper.list_candidate_entries
    classify = helper.classify_entry
    read_confined = helper.read_confined
    EntryRefused = helper.EntryRefused

    supplied = Path(argv[0])

    # AC-0003: absent directory
    if not supplied.exists():
        print(f"error: directory {str(supplied)!r} is absent")
        return 1

    if not supplied.is_dir():
        print(f"error: {str(supplied)!r} is not a directory")
        return 1

    # Enumerate candidates
    try:
        all_entries = list_candidates(supplied)
    except EntryRefused as exc:
        print(f"error: {exc}")
        return 1
    except OSError as exc:
        print(f"error: cannot list {supplied}: {exc}")
        return 1

    candidates = [e for e in all_entries if _is_candidate(e.name)]

    # AC-0003: empty candidate listing
    if not candidates:
        print(f"error: directory {str(supplied)!r} holds no decision record")
        return 1

    # Scan: classify and read each candidate
    root = supplied.resolve()
    read_bucket: list[_Record] = []
    refused_count = 0
    unreadable_count = 0

    # AC-0005 requires every candidate to land in EXACTLY ONE outcome. The
    # summary counts alone cannot show that: an entry counted twice while
    # another is dropped leaves the sum intact, and a read entry otherwise
    # emits nothing to attribute. This opt-in ledger makes per-entry
    # membership observable so the partition can be asserted as a bijection.
    # An environment variable rather than a flag, because the gate step's
    # argv is pinned and an undefined flag on a blocking control is its own
    # hazard.
    ledger = os.environ.get("ADR_SHAPE_ENTRY_LEDGER") == "1"

    def account(name: str, bucket: str) -> None:
        if ledger:
            print(f"entry: {name} -> {bucket}", file=sys.stderr)

    for entry in candidates:
        # Join against the resolved root, not `entry.path`: os.scandir echoes
        # back whatever the caller supplied, so a relative argument such as the
        # gate chain's `docs/adr` yields a relative entry path, and
        # `read_confined`'s `relative_to(root)` then refuses every record.
        entry_path = root / entry.name
        try:
            kind = classify(entry)
        except OSError as exc:
            print(f"warning: cannot classify {entry.name}: {exc}",
                  file=sys.stderr)
            unreadable_count += 1
            account(entry.name, "unreadable")
            continue

        if kind != "regular":
            # symlink, directory, other — all refused
            print(f"warning: {entry.name}: refused ({kind})",
                  file=sys.stderr)
            refused_count += 1
            account(entry.name, "refused")
            continue

        try:
            # Pass the identity observed at listing time: without it the
            # read verifies only its own stat/open pair and would happily
            # read a file substituted after `classify` called it regular.
            raw_bytes = read_confined(root, entry_path, expect=entry.identity)
        except EntryRefused as exc:
            print(f"warning: {entry.name}: refused: {exc}",
                  file=sys.stderr)
            refused_count += 1
            account(entry.name, "refused")
            continue
        except OSError as exc:
            print(f"warning: {entry.name}: unreadable: {exc}",
                  file=sys.stderr)
            unreadable_count += 1
            account(entry.name, "unreadable")
            continue

        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            print(f"warning: {entry.name}: unreadable (not UTF-8): {exc}",
                  file=sys.stderr)
            unreadable_count += 1
            account(entry.name, "unreadable")
            continue

        rec = _parse(entry_path, text)
        read_bucket.append(rec)
        account(entry.name, "read")

    # Build record map (ordinal → record) for cross-record checks
    records: dict[str, _Record] = {}
    for rec in read_bucket:
        if rec.ordinal:
            key = f"ADR-{rec.ordinal}"
            records[key] = rec

    # Run per-record checks
    all_findings: list[Finding] = []
    for rec in read_bucket:
        all_findings.extend(_check_record(rec))

    # Run cross-record checks
    all_findings.extend(_check_cross(records))

    # Output
    for path_str, code, msg in all_findings:
        print(f"{path_str}: {code}: {msg}")

    # Scan summary (three distinct labels, AC-0006)
    print(
        f"read: {len(read_bucket)}"
        f"  refused: {refused_count}"
        f"  unreadable: {unreadable_count}"
    )

    # Exit contract (AC-0002 + AC-0031)
    if all_findings or refused_count or unreadable_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
