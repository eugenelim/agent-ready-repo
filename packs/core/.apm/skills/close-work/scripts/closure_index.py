#!/usr/bin/env python3
"""Per-decision in-memory descendant index for the closure eligibility check.

Module-private construction: only the closure check's entry point may call
``_build_descendant_closure``. A test enumerates its callers (AC-0026, T4).

**Nothing in this module writes to disk or to environment variables.** The
returned dict is built inside the caller's frame and garbage-collected when
that frame ends (AC-0023). No state persists across decisions (AC-0021).

**Each call to the entry point re-reads all inputs.** No descendant set,
index, or verdict is cached between calls (AC-0021). A second decision over the
same tree after a status mutation sees the new value because every artifact file
is re-opened from scratch.

**The entry point refuses when HEAD is not current against the merge target**
(AC-0022). A ``_freshness_checker`` seam (default: git-based) is called first
and returns one of three values: ``True`` (fresh — proceed), ``False`` (stale —
refuse with ``stale-base``), or ``None`` (indeterminate — refuse with
``freshness-indeterminate``). Indeterminate cases include git being unavailable,
a subprocess timeout, and *root* not being a git repository. They resolve
**closed** — a closure decision authorises a terminal write, so "unable to
determine" is not the same as "determined fresh" and is treated as a blocker.
The one case that resolves fresh without checking staleness is when no tracking
branch is configured: there is nothing to be stale against.

**Each artifact file is opened at most once per decision** (AC-0024). A
visited set tracks physically opened paths; a field cache stores preamble
fields so that subsequent membership checks use the cache rather than
re-reading the file. The diamond case — one file encountered as a candidate
in two separate collection scans — is handled by returning cached fields on
the second encounter without calling the reader.

**Discovery is driven exclusively by the ``Decomposed:`` terminus at each
level** (AC-0025). A terminus names one of three collections: ``children``
maps to the intents directory, ``brief`` maps to the briefs directory (plus
the specs directory for that brief's specs), and ``spec`` maps to the specs
directory. No other directory is enumerated. A collection-directory cache
ensures dir_lister is called at most once per directory per decision.

**Reads per decision are bounded by the summed size of the named
collections** (AC-0037). Because each artifact in each named collection is
physically read at most once, the reader call count cannot exceed the total
file count across the collections the termini name.

**``Discovery:`` targets are confined to the repository root** (trust
boundary). The default reader uses the co-located ``file_safety.py``
projection of the blessed ``agentbundle.catalogue_tooling.file_safety``
helper, which calls ``read_confined_regular_file`` and raises
``UnsafeContentError`` (a ``ValueError`` subclass) on any escape — a
``..`` segment, an absolute path that lands outside the root, or a symlink
— before the target file is opened.  ``_get_fields`` catches both
``OSError`` and ``ValueError`` and treats either as an unreadable artifact,
so a confined violation contributes no descendant edge and does not crash
the decision.  An injected ``_reader`` seam (test use only) bypasses this
check; the seam is trusted because tests control their own filesystem.

Projection note: ``TERMINUS_VOCABULARY`` is a local projection of
``intent_shape.DECOMPOSITION_TERMINI``. A cross-skill relative import is
forbidden by the catalogue authoring standards; the upstream is stated as a
comment and the parity check that keeps them in sync lives in T4's caller-
enumeration test.
"""

from __future__ import annotations

import importlib.util
import os
import re
import stat as _stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

# ── Blessed file-safety helper ────────────────────────────────────────────────

_SCRIPT_DIR = Path(__file__).resolve().parent
_file_safety_module: Any | None = None


def _get_file_safety() -> Any:
    """Load the co-located file_safety.py projection at most once.

    Follows the same loader discipline as ``close_work.py`` § ``file_safety()``:
    ``lstat`` confirms it is a regular (non-symlink) file before loading, and
    the required symbols are asserted after exec.
    """
    global _file_safety_module
    if _file_safety_module is not None:
        return _file_safety_module

    path = _SCRIPT_DIR / "file_safety.py"
    try:
        st = os.lstat(path)
    except OSError as exc:  # pragma: no cover
        raise ImportError(f"required helper unavailable: {path.name}") from exc
    if not _stat.S_ISREG(st.st_mode) or _stat.S_ISLNK(st.st_mode):  # pragma: no cover
        raise ImportError(f"required helper is not a regular file: {path.name}")

    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(
            "_closure_index_file_safety", path
        )
        if spec is None or spec.loader is None:  # pragma: no cover
            raise ImportError(f"required helper cannot be loaded: {path.name}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    except BaseException:  # pragma: no cover
        sys.modules.pop("_closure_index_file_safety", None)
        raise
    finally:
        sys.dont_write_bytecode = prev

    _required = {"UnsafeContentError", "read_confined_regular_file"}
    missing = _required - set(vars(mod))
    if missing:  # pragma: no cover
        sys.modules.pop("_closure_index_file_safety", None)
        raise ImportError(
            f"required helper is incomplete: {path.name}: {', '.join(sorted(missing))}"
        )
    _file_safety_module = mod
    return mod


# ── Terminus vocabulary (projection of intent_shape.DECOMPOSITION_TERMINI) ────
# Upstream: packs/core/.apm/skills/work-intake/scripts/intent_shape.py
# :: DECOMPOSITION_TERMINI
# Cross-skill imports are banned; T4's caller-enumeration test asserts the
# construction is reached only through the approved entry point.

TERMINUS_VOCABULARY: tuple[str, ...] = (
    "children",
    "brief",
    "spec",
    "direct-light",
    "closed-empty",
)

# ── Reference-kind vocabulary (projection of intent_shape.OUTCOME_CO_OWNER_KINDS)
# A ``Parent intent:`` value is a **typed** reference — ``<kind>:<slug>`` — and
# the kind names the parent's altitude, not the child's. Matching ``intent:``
# alone reads 5 of the 49 declared parent edges in this repository and misses
# every ``capability:``, ``outcome:`` and ``opportunity:`` edge. The shipped
# home is the same one that validates ``Outcome co-owner:``, which uses this
# identical grammar.

REFERENCE_KIND_VOCABULARY: tuple[str, ...] = (
    "outcome",
    "opportunity",
    "capability",
    "intent",
)

REFERENCE_KIND_UPSTREAM_SLUG = "work-intake/scripts/intent_shape.py"
REFERENCE_KIND_UPSTREAM_SECTION = "OUTCOME_CO_OWNER_KINDS, vocabulary membership"


def reference_kind_parity_disagreements(upstream_kinds: Iterable[str]) -> list[str]:
    """Kinds where this projection and the upstream vocabulary disagree.

    Reported in both directions. A kind upstream adds and this projection
    lacks is the live risk: every parent edge carrying it becomes invisible to
    the walk, the ancestor reports an empty descendant set, and the verdict is
    a refusal that looks like a legitimate C2 answer.
    """
    upstream = frozenset(upstream_kinds)
    disagreements: list[str] = []
    for kind in REFERENCE_KIND_VOCABULARY:
        if kind not in upstream:
            disagreements.append(kind)
    for kind in sorted(upstream):
        if kind not in REFERENCE_KIND_VOCABULARY:
            disagreements.append(kind)
    return disagreements


def read_stated_outcome(text: str) -> str:
    """Return the ancestor's declared outcome, collapsed to one line.

    Reads the ``## Outcome`` section. This is body text, not a preamble
    field, and it is read deliberately: it is shown to a human and gates no
    verdict. The no-body-gating rule constrains what a *transition* may be
    decided on, and nothing here decides one.

    Returns ``""`` when no outcome section exists, so the caller can state the
    absence rather than omit the field.
    """
    lines = text.splitlines()
    out: list[str] = []
    inside = False
    for line in lines:
        if line.startswith("## "):
            if inside:
                break
            inside = line.strip().lower() == "## outcome"
            continue
        if inside and line.strip():
            out.append(line.strip().lstrip("-").strip())
    return " ".join(out).strip()


def _is_parent_edge(value: str, parent_slug: str) -> bool:
    """True when a ``Parent intent:`` value points at ``parent_slug``.

    Accepts any kind in the shipped vocabulary. The kind is the parent's
    altitude and is not knowable from the child, so it is not constrained
    here beyond membership.
    """
    return any(value == f"{kind}:{parent_slug}" for kind in REFERENCE_KIND_VOCABULARY)


# Termini that name artifact collections and therefore trigger collection reads.
_COLLECTION_TERMINI: frozenset[str] = frozenset({"children", "brief", "spec"})

# The pin that keeps the projection above honest. It is declared here rather
# than beside the status pins in ``closure_terminality`` because a projection
# and its parity check drift apart when they live in different files, and this
# vocabulary is read from this module.
TERMINUS_UPSTREAM_SLUG = "work-intake/scripts/intent_shape.py"
TERMINUS_UPSTREAM_SECTION = "DECOMPOSITION_TERMINI, vocabulary membership"


def terminus_parity_disagreements(upstream_termini: Iterable[str]) -> list[str]:
    """Termini where this projection and the upstream vocabulary disagree.

    Reported in both directions: a terminus upstream adds and this projection
    lacks is as much a defect as one this projection invents. The first is the
    live risk — the cross-product coverage table is generated from
    ``TERMINUS_VOCABULARY``, so a terminus missing here produces no test case
    at all and reaches no verdict with the whole suite green. Without this
    check that table only proves it agrees with itself.
    """
    upstream = frozenset(upstream_termini)
    disagreements: list[str] = []
    for terminus in TERMINUS_VOCABULARY:
        if terminus not in upstream:
            disagreements.append(terminus)
    for terminus in sorted(upstream):
        if terminus not in TERMINUS_VOCABULARY:
            disagreements.append(terminus)
    return disagreements


# ── Artifact record ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DescendantRecord:
    """One artifact in the descendant closure of a single decision.

    ``slug``: declared identity (``Slug:`` preamble field).
    ``kind``: one of ``"intent"``, ``"brief"``, or ``"spec"``.
    ``status``: ``Status:`` field value; empty string when absent.
    ``terminus``: the artifact's own ``Decomposed:`` terminus, or ``""``
        when absent or the value is ``no``.
    """

    slug: str
    kind: str
    status: str
    terminus: str


# ── Injectable seam types ─────────────────────────────────────────────────────

Reader = Callable[[Path], str]
DirLister = Callable[[Path], Iterable[Path]]
FreshnessChecker = Callable[[], "bool | None"]
WorkspaceLookup = Callable[[str], "tuple[str, str] | None"]
"""Callable: ancestor slug → ``(entry_path, collection)`` or ``None`` (AC-0031).

Returns the ``workspace.toml`` registration for the closing intent so the
packet can name the entry the human must clear alongside the status write.
Returns ``None`` when the intent has no registration.
"""

DispositionLookup = Callable[[str], "str | None"]
"""Callable: ancestor slug → disposition-row name or ``None`` (AC-0034/0035).

Returns the name of the matching product-bet disposition row (e.g.
``"cool-30-days"``), or ``None`` when no eligibility clause reaches the artifact.
"""

SnapshotProvider = Callable[[Path], "dict[str, Any]"]
"""Callable: repository root → validated delivery snapshot dict.

Raises ``ValueError`` on any failure (resolver unavailable, bad schema, etc.).
The stable code ``delivery-resolver-unavailable`` is the only user-visible output.
"""

# ── Delivery resolver constants ───────────────────────────────────────────────

_RESOLVER_TIMEOUT: int = 60  # subprocess wall-clock budget in seconds
_MAX_SNAPSHOT_BYTES: int = 16_777_216  # 16 MiB; mirrors resolver MAX_JSON_BYTES

_DELIVERY_DIAGNOSTIC_CODES: frozenset[str] = frozenset({
    "delivery-target-missing",
    "delivery-projection-mismatch",
    "delivery-relation-ambiguous",
    "delivery-reference-malformed",
})

_SNAPSHOT_REQUIRED_KEYS: frozenset[str] = frozenset({
    "schema_version",
    "complete",
    "relations",
    "classifications",
    "provenance",
    "diagnostics",
})


class _ClosureDeliveryRefusal(Exception):
    """Raised inside _build_descendant_closure when delivery resolution fails.

    Caught by check_ancestor_closure, which converts it to a ClosureRefuse.
    Carrying the stable reason string keeps the conversion trivial.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


# ── Field-parsing helpers (no cross-skill import) ────────────────────────────

_COMMENT_SUFFIX = re.compile(r"\s*<!--.*?-->\s*$", re.DOTALL)
_FIELD_LINE = re.compile(r"^- \*\*([^*:]+):\*\*\s*(.*)$")
_HEADING_PREFIX = "## "
_DECOMPOSED_TERMINUS = re.compile(r"^\d{4}-\d{2}-\d{2}\s+(\S+)")


def _normalize(raw: str) -> str:
    """Strip trailing HTML comment then surrounding backticks; order is the contract."""
    value = raw.strip()
    value = _COMMENT_SUFFIX.sub("", value).strip()
    if len(value) >= 2 and value[0] == "`" and value[-1] == "`":
        value = value[1:-1].strip()
    return value


def _preamble(text: str) -> dict[str, str]:
    """Return first-occurrence preamble fields as ``{name: normalized_value}``."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith(_HEADING_PREFIX):
            break
        m = _FIELD_LINE.match(line)
        if m:
            name = m.group(1).strip()
            if name not in fields:
                fields[name] = _normalize(m.group(2))
    return fields


def _terminus_from_decomposed(value: str) -> str:
    """Extract the terminus token from a ``Decomposed:`` value, or ``""``."""
    if not value or value == "no":
        return ""
    m = _DECOMPOSED_TERMINUS.match(value)
    return m.group(1) if m else ""


# ── Collection directory helpers ──────────────────────────────────────────────


def _intents_dir(root: Path) -> Path:
    """``docs/product/intents/`` relative to root."""
    return root / "docs" / "product" / "intents"


def _briefs_dir(root: Path) -> Path:
    """``docs/product/briefs/`` relative to root."""
    return root / "docs" / "product" / "briefs"


def _specs_dir(root: Path) -> Path:
    """``docs/specs/`` relative to root."""
    return root / "docs" / "specs"


def _is_intents_rel_path(target: str) -> bool:
    """Return True when *target* is a safe repository-relative intent path.

    Accepts only ``docs/product/intents/<file>.md`` with no ``..`` segments,
    no leading ``/``, and no nested subdirectories inside ``intents/``.
    This is the form the delivery-resolver stores for bare-path and
    backtick-path Discovery: values that name a non-feature intent.
    """
    if not target.startswith("docs/product/intents/"):
        return False
    if not target.endswith(".md"):
        return False
    # Remaining segment must be a plain filename (no further slashes).
    tail = target[len("docs/product/intents/"):]
    return not ("/" in tail or ".." in tail or not tail)


# ── Default implementations of the injectable seams ──────────────────────────


def _make_confined_reader(root: Path) -> Reader:
    """Return a reader that confines all reads to within *root*.

    Uses ``read_confined_regular_file`` from the co-located ``file_safety.py``
    projection.  Raises ``UnsafeContentError`` (a ``ValueError`` subclass) when
    the path escapes *root* via ``..`` segments, absolute references, or symlinks.
    ``_get_fields`` catches both ``OSError`` and ``ValueError``; either results
    in an empty artifact rather than a crash.
    """
    fs = _get_file_safety()

    def _reader(p: Path) -> str:
        raw: bytes = fs.read_confined_regular_file(root, p)
        return raw.decode("utf-8", errors="replace")

    return _reader


def _default_dir_lister(d: Path) -> Iterable[Path]:
    """Return artifact files for a collection directory.

    - Intents and briefs: flat ``.md`` files in the directory.
    - Specs: ``spec.md`` files one level under the directory, one per
      feature subdirectory.
    Files whose names start with ``_`` are excluded (internal artefacts).
    """
    if not d.is_dir():
        return []
    results: list[Path] = []
    for child in sorted(d.iterdir()):
        if child.name.startswith("_"):
            continue
        if child.is_file() and child.suffix == ".md":
            results.append(child)
        elif child.is_dir():
            spec_file = child / "spec.md"
            if spec_file.is_file():
                results.append(spec_file)
    return results


# ── Default freshness checker ─────────────────────────────────────────────────


def _make_default_freshness_checker(root: Path) -> FreshnessChecker:
    """Return a checker that verifies HEAD is current against the merge target.

    The returned callable has three outcomes (``bool | None``):

    - ``True``  — **fresh**: either no tracking branch is configured (nothing to
      be stale against), or the tracking branch is an ancestor of HEAD.
    - ``False`` — **stale**: the tracking branch has commits that HEAD does not
      contain; HEAD needs a fast-forward or rebase before this closing edge.
    - ``None``  — **indeterminate**: could not determine staleness because ``git``
      is unavailable (``FileNotFoundError``), the subprocess timed out, or
      *root* is not a git repository.

    Indeterminate resolves **closed** (the entry point refuses with
    ``freshness-indeterminate``).  A closure decision authorises a terminal write;
    "unable to determine" is not the same as "determined fresh", and the spec's
    risk rule ("every ambiguous case resolves toward refuse") applies here as
    much as it does to an unrecognised descendant status.

    The one case that resolves ``True`` without performing a staleness check is
    "no tracking branch configured" — that is a legitimate state, not an error.

    Implementation: three ``git`` subprocess calls with ``cwd=root``.

    1. ``git rev-parse --git-dir`` — confirms *root* is inside a git repository.
       A non-zero exit means it is not; returns ``None`` (indeterminate).
    2. ``git rev-parse --abbrev-ref @{u}`` — detects whether a tracking branch
       is configured.  A non-zero exit means no upstream; returns ``True``.
    3. ``git merge-base --is-ancestor @{u} HEAD`` — exit 0 means the upstream is
       an ancestor of HEAD (fresh); non-zero means stale.

    ``subprocess`` is imported inside the closure to keep the module-level import
    set minimal (this path is not exercised in every call).

    This is an independent implementation of the HEAD-vs-merge-target condition.
    ``work-loop`` ships ``check-base-freshness.py`` for its own callers; a
    cross-skill relative import is banned by the catalogue authoring standards and
    copying between ``scripts/`` directories is explicitly prohibited. The
    condition itself has no shipped vocabulary home and needs no parity pin.
    """

    def _check() -> bool | None:
        import subprocess  # stdlib; imported here to keep module-level imports minimal

        try:
            # Step 1: confirm root is inside a git repository.
            git_dir = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                cwd=root,
                timeout=10,
            )
            if git_dir.returncode != 0:
                # root is not a git repository → indeterminate.
                return None

            # Step 2: check whether a tracking branch is configured.
            upstream = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "@{u}"],
                capture_output=True,
                cwd=root,
                timeout=10,
            )
            if upstream.returncode != 0:
                # No tracking branch → nothing to be stale against → fresh.
                return True

            # Step 3: check whether HEAD is at or ahead of the tracking branch.
            check = subprocess.run(
                ["git", "merge-base", "--is-ancestor", "@{u}", "HEAD"],
                capture_output=True,
                cwd=root,
                timeout=10,
            )
            # Exit 0 → upstream is ancestor of HEAD → fresh.
            # Non-zero → HEAD is behind the tracking branch → stale.
            return check.returncode == 0

        except FileNotFoundError:
            # git is not available in the environment → indeterminate.
            return None
        except Exception:
            # Timeout or other unexpected runtime error → indeterminate.
            return None

    return _check


# ── Delivery resolver invocation ──────────────────────────────────────────────


def _parse_and_validate_snapshot(text: str) -> dict[str, Any]:
    """Parse and strictly validate a snapshot JSON text.

    Returns the snapshot dict on success.
    Raises ``ValueError`` on any structural or schema violation, including
    NaN/Infinity in the payload, wrong schema_version, incomplete flag, or
    missing/extra keys.
    """
    import json as _json

    try:
        data = _json.loads(text)
    except (ValueError, _json.JSONDecodeError):
        raise ValueError("delivery-resolver-unavailable: bad JSON") from None

    # Reject NaN/Infinity by round-tripping through a strict encoder.
    try:
        _json.dumps(data, allow_nan=False)
    except (ValueError, TypeError):
        raise ValueError("delivery-resolver-unavailable: NaN/Infinity in payload") from None

    if not isinstance(data, dict):
        raise ValueError("delivery-resolver-unavailable: top-level not a dict")
    if set(data.keys()) != _SNAPSHOT_REQUIRED_KEYS:
        raise ValueError("delivery-resolver-unavailable: wrong keys")
    if data["schema_version"] != 1:
        raise ValueError("delivery-resolver-unavailable: unsupported schema_version")
    if data["complete"] is not True:
        raise ValueError("delivery-resolver-unavailable: incomplete snapshot")
    for _k in ("relations", "classifications", "provenance", "diagnostics"):
        if not isinstance(data[_k], list):
            raise ValueError(f"delivery-resolver-unavailable: {_k} not a list")
    return data


def _run_resolver(root: Path) -> dict[str, Any]:
    """Run the projected resolver subprocess and return a validated snapshot.

    Raises ``ValueError`` on any failure: missing file, non-zero exit, timeout,
    OSError, oversize stdout, bad UTF-8, bad JSON, wrong schema, or incomplete
    result. The error message always begins with 'delivery-resolver-unavailable'
    and never includes captured stderr, tracebacks, or absolute paths.
    """
    import subprocess  # stdlib; imported here for minimal module-level deps

    resolver_path = root / ".agentbundle" / "bin" / "intent_delivery_relations.py"
    try:
        _st = resolver_path.lstat()
    except OSError:
        raise ValueError("delivery-resolver-unavailable: resolver not found") from None
    if not _stat.S_ISREG(_st.st_mode) or _stat.S_ISLNK(_st.st_mode):
        raise ValueError("delivery-resolver-unavailable: resolver not a regular file")

    try:
        proc = subprocess.run(
            [sys.executable, str(resolver_path), "--root", str(root)],
            capture_output=True,
            timeout=_RESOLVER_TIMEOUT,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        raise ValueError("delivery-resolver-unavailable: subprocess timed out") from None
    except OSError:
        raise ValueError("delivery-resolver-unavailable: subprocess OSError") from None

    if proc.returncode != 0:
        raise ValueError("delivery-resolver-unavailable: non-zero exit")

    stdout: bytes = proc.stdout
    if len(stdout) > _MAX_SNAPSHOT_BYTES:
        raise ValueError("delivery-resolver-unavailable: stdout exceeds size limit")

    try:
        text = stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise ValueError("delivery-resolver-unavailable: stdout not valid UTF-8") from None

    return _parse_and_validate_snapshot(text)


# ── Packet-building helpers ───────────────────────────────────────────────────


def _descendant_locator(record: DescendantRecord) -> str:
    """Return a canonical repository-relative path for a descendant artifact.

    Used as the evidence locator in ``EligiblePacket.per_descendant_verdicts``.
    The path follows the collection convention (slug.md for intents and briefs,
    slug/spec.md for specs) even when the actual filename carries an ordinal
    prefix — the slug is the canonical identity, and the locator is a pointer
    sufficient for a human to find the file.
    """
    if record.kind == "intent":
        return f"docs/product/intents/{record.slug}.md"
    if record.kind == "brief":
        return f"docs/product/briefs/{record.slug}.md"
    if record.kind == "spec":
        return f"docs/specs/{record.slug}/spec.md"
    return f"{record.kind}:{record.slug}"


def _current_date() -> str:
    """Return today's date as an ISO-8601 string.

    Injectable in tests via ``_decision_date`` on ``check_ancestor_closure``.
    """
    from datetime import date as _date

    return _date.today().isoformat()


def _build_eligible_packet(
    ancestor_slug: str,
    ancestor_terminus: str,
    descendants: dict[str, DescendantRecord],
    basis: str,
    decider: str,
    decision_date: str,
    ancestor_fields: dict[str, str],
    workspace_lookup: WorkspaceLookup | None,
    disposition_lookup: DispositionLookup | None,
) -> EligiblePacket:
    """Build the evidence packet for an eligible verdict (AC-0027).

    Pure: derives all fields from already-resolved inputs.  No I/O.
    Called only when ``check_ancestor_closure`` sees a ``ClosureEligible``
    result and a non-empty ``_decider`` was supplied.
    """
    # Full Decomposed: value from ancestor fields (e.g. "2026-09-19 children").
    # Fall back to the terminus token when the full value was not supplied.
    ratified_decomposed = ancestor_fields.get("Decomposed", ancestor_terminus)

    # Outcome co-owner: from ancestor fields; None when absent (AC-0028).
    raw_co_owner = ancestor_fields.get("Outcome co-owner", "").strip()
    outcome_co_owner: str | None = raw_co_owner if raw_co_owner else None

    # Per-descendant verdicts: (slug, status, evidence_locator), sorted by slug.
    per_descendant: tuple[tuple[str, str, str], ...] = tuple(
        (r.slug, r.status, _descendant_locator(r))
        for r in sorted(descendants.values(), key=lambda r: r.slug)
    )

    # Workspace registration: (entry_path, collection) or None (AC-0031).
    workspace_reg: tuple[str, str] | None = (
        workspace_lookup(ancestor_slug) if workspace_lookup is not None else None
    )

    # Disposition row: matching row name or None (AC-0034/0035).
    disposition: str | None = (
        disposition_lookup(ancestor_slug) if disposition_lookup is not None else None
    )

    # The ancestor's own promise. Without it a decider can see that the tree
    # finished and still not know whether finishing it delivered anything
    # (AC-0038). A stated absence beats a silent omission: the decider cannot
    # otherwise tell a missing field from an intent that promised nothing.
    stated_outcome = ancestor_fields.get("__outcome__", "").strip() or (
        "not stated: the ancestor declares no outcome section this check could read"
    )

    # Resolved against declared, separately (AC-0039). Terminality is silent
    # about a child that was never created, so completeness cannot be read off
    # it. ``declared`` is unknown unless the ancestor states it, and an
    # unknown denominator is said rather than guessed.
    declared_raw = ancestor_fields.get("__declared_children__", "").strip()
    ratified_child_count = (
        f"{len(descendants)} of {declared_raw}"
        if declared_raw
        else f"{len(descendants)} resolved; declared count not stated by the ancestor"
    )

    # Stated confidence: name the known gaps so the decider can judge (AC-0027).
    # The co-owner caveat is conditional (AC-0040). Firing it when no co-owner
    # is declared sends the decider hunting a risk the packet already ruled
    # out two fields below.
    caveats = []
    if outcome_co_owner is not None:
        caveats.append(
            "Peer closure state not verified: the declared Outcome co-owner is "
            "named but its current status is outside the boundary this check "
            "may read."
        )
    caveats.append(
        "The ancestor's own cited claims were not independently re-validated."
    )
    stated_confidence = " ".join(caveats)

    return EligiblePacket(
        decision_date=decision_date,
        decider=decider,
        stated_outcome=stated_outcome,
        ratified_decomposed=ratified_decomposed,
        ratified_child_count=ratified_child_count,
        verification_basis=basis,
        per_descendant_verdicts=per_descendant,
        stated_confidence=stated_confidence,
        outcome_co_owner=outcome_co_owner,
        workspace_registration=workspace_reg,
        disposition_row=disposition,
    )


# ── The per-decision index builder ────────────────────────────────────────────


def _build_descendant_closure(
    ancestor_slug: str,
    ancestor_terminus: str,
    root: Path,
    *,
    _reader: Reader | None = None,
    _dir_lister: DirLister | None = None,
    _snapshot_provider: SnapshotProvider | None = None,
) -> dict[str, DescendantRecord]:
    """Build the full descendant closure for one decision.

    Returns ``slug → DescendantRecord`` for every artifact in the closure.
    Each call builds a fresh index; nothing is cached between calls (AC-0021).

    ``_reader``, ``_dir_lister``, and ``_snapshot_provider`` are test seams.
    Production callers pass none of these and the defaults run against the
    real filesystem and the projected resolver.

    **AC-0024**: each artifact is physically opened at most once. The
    ``visited`` set prevents the reader from being called twice for the same
    path. When a path is encountered again (e.g. in a second collection scan),
    the cached fields are returned without calling the reader.

    **AC-0025**: dir_lister is called only for collection directories named by
    the termini encountered along the closure. Delivery termini (``spec`` and
    ``brief``) read only the specific files named in the canonical snapshot,
    never enumerating an entire collection. No other directory is listed.
    The ``dir_cache`` prevents a second dir_lister call for the same directory.

    **AC-0037**: because each file is read at most once and only named
    collections are enumerated, the total reader call count cannot exceed the
    summed file count across those collections.

    **AC-0023**: no file is written and no environment variable is set. The
    returned dict is the sole output; its lifetime is the caller's frame.

    Raises ``_ClosureDeliveryRefusal`` when a delivery terminus is encountered
    but the canonical snapshot cannot be obtained or names a delivery diagnostic
    for the feature intent being resolved.
    """
    # Default reader is root-confined via file_safety.py (trust boundary).
    # An injected _reader bypasses confinement and is trusted for test use.
    reader: Reader = _reader if _reader is not None else _make_confined_reader(root)
    dir_lister: DirLister = _dir_lister if _dir_lister is not None else _default_dir_lister

    # Per-decision state — all local, none persisted.
    visited: set[Path] = set()  # resolved paths physically opened (AC-0024)
    field_cache: dict[Path, dict[str, str]] = {}  # preamble fields per opened path
    dir_cache: dict[Path, list[Path]] = {}  # collection dir → file list (AC-0025)
    result: dict[str, DescendantRecord] = {}

    # Lazy delivery snapshot — fetched at most once, on first delivery terminus.
    _snapshot_cache: list[dict[str, Any]] = []

    def _get_snapshot() -> dict[str, Any]:
        """Fetch and cache the delivery snapshot for this decision."""
        if not _snapshot_cache:
            provider = _snapshot_provider if _snapshot_provider is not None else _run_resolver
            try:
                snap = provider(root)
            except Exception as _exc:
                raise _ClosureDeliveryRefusal("delivery-resolver-unavailable") from _exc
            _snapshot_cache.append(snap)
        return _snapshot_cache[0]

    def _list_dir(d: Path) -> list[Path]:
        """List a collection directory at most once; subsequent calls use the cache."""
        key = d.resolve()
        if key not in dir_cache:
            dir_cache[key] = list(dir_lister(d))
        return dir_cache[key]

    def _get_fields(path: Path) -> dict[str, str]:
        """Return preamble fields for a path, reading it at most once (AC-0024).

        If the path is already in ``visited``, returns cached fields without
        calling the reader. This is the mechanism that prevents double-opens
        in the diamond case: a file encountered as a candidate in two separate
        collection scans is physically read only on the first encounter.
        """
        key = path.resolve()
        if key not in visited:
            visited.add(key)
            try:
                text = reader(path)
            except (OSError, ValueError):
                # OSError: file missing or unreadable.
                # ValueError: covers UnsafeContentError from the confined reader
                # (path escapes root, symlink, or absolute reference outside root).
                # Either case: treat as an empty artifact; contributes no edge.
                text = ""
            field_cache[key] = _preamble(text)
        return field_cache.get(key, {})

    def _add_descendant(slug: str, kind: str, fields: dict[str, str]) -> None:
        """Add an artifact to the result and enqueue further descent if needed."""
        if slug in result:
            return  # already found (handles diamond: same slug via two paths)
        status = fields.get("Status", "")
        raw_decomposed = fields.get("Decomposed", "")
        terminus = _terminus_from_decomposed(raw_decomposed)
        result[slug] = DescendantRecord(
            slug=slug, kind=kind, status=status, terminus=terminus
        )
        if terminus in _COLLECTION_TERMINI:
            queue.append((slug, terminus))

    queue: list[tuple[str, str]] = [(ancestor_slug, ancestor_terminus)]

    while queue:
        parent_slug, terminus = queue.pop(0)

        if terminus not in _COLLECTION_TERMINI:
            continue

        if terminus == "children":
            # Invert ``Parent intent: <kind>:<parent_slug>`` over the intents
            # collection. This is NOT feature delivery; it stays local.
            for path in _list_dir(_intents_dir(root)):
                fields = _get_fields(path)
                slug = fields.get("Slug", "")
                if not slug:
                    continue
                if _is_parent_edge(fields.get("Parent intent", ""), parent_slug):
                    _add_descendant(slug, "intent", fields)

        elif terminus == "brief":
            # Coordinated delivery: look up the canonical snapshot for
            # coordinated-delivery relations whose intent is this feature.
            # The snapshot owns brief-and-spec membership; close-work reads
            # only each artifact's Status/Decomposed for closure evaluation.
            snap = _get_snapshot()
            feat_id = f"intent:{parent_slug}"
            # Check for delivery diagnostics that block closure.
            for _diag in snap.get("diagnostics", []):
                if (
                    _diag.get("subject") == feat_id
                    and _diag.get("code") in _DELIVERY_DIAGNOSTIC_CODES
                ):
                    raise _ClosureDeliveryRefusal(
                        f"delivery-diagnostic: {_diag['code']}"
                    )
            seen_brief_slugs: set[str] = set()
            for rel in snap.get("relations", []):
                if (
                    rel.get("type") == "coordinated-delivery"
                    and rel.get("intent") == feat_id
                ):
                    brief_ref = rel.get("brief", "")
                    spec_ref = rel.get("spec", "")

                    if brief_ref.startswith("brief:"):
                        brief_slug_val = brief_ref[len("brief:"):]
                        if brief_slug_val not in seen_brief_slugs:
                            seen_brief_slugs.add(brief_slug_val)
                            brief_path = _briefs_dir(root) / f"{brief_slug_val}.md"
                            b_fields = _get_fields(brief_path)
                            b_status = b_fields.get("Status", "")
                            if brief_slug_val not in result:
                                result[brief_slug_val] = DescendantRecord(
                                    slug=brief_slug_val,
                                    kind="brief",
                                    status=b_status,
                                    terminus="",
                                )

                    if spec_ref.startswith("spec:"):
                        spec_slug_val = spec_ref[len("spec:"):]
                        spec_path = _specs_dir(root) / spec_slug_val / "spec.md"
                        s_fields = _get_fields(spec_path)
                        _add_descendant(spec_slug_val, "spec", s_fields)

        elif terminus == "spec":
            # Direct delivery: look up the canonical snapshot for direct-delivery
            # relations with route 'spec' whose intent is this feature.
            # The snapshot owns spec membership; close-work reads only each
            # spec's Status/Decomposed for closure evaluation.
            snap = _get_snapshot()
            feat_id = f"intent:{parent_slug}"
            # Check for delivery diagnostics that block closure.
            for _diag in snap.get("diagnostics", []):
                if (
                    _diag.get("subject") == feat_id
                    and _diag.get("code") in _DELIVERY_DIAGNOSTIC_CODES
                ):
                    raise _ClosureDeliveryRefusal(
                        f"delivery-diagnostic: {_diag['code']}"
                    )
            for rel in snap.get("relations", []):
                if (
                    rel.get("type") == "direct-delivery"
                    and rel.get("route") == "spec"
                    and rel.get("intent") == feat_id
                ):
                    spec_ref = rel.get("spec", "")
                    if spec_ref.startswith("spec:"):
                        spec_slug_val = spec_ref[len("spec:"):]
                        spec_path = _specs_dir(root) / spec_slug_val / "spec.md"
                        s_fields = _get_fields(spec_path)
                        _add_descendant(spec_slug_val, "spec", s_fields)

    return result


# ── Closure verdict types ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class ClosureRefuse:
    """A precondition for evaluating the ancestor is unmet.

    ``ancestor_slug``: the slug of the ancestor being evaluated.
    ``reason``: a short phrase naming the unmet precondition and its remedy.
    """

    ancestor_slug: str
    reason: str


@dataclass(frozen=True)
class ClosureNotEligible:
    """At least one descendant in the ancestor's closure is live.

    ``ancestor_slug``: the slug of the ancestor being evaluated.
    ``live_descendants``: every live descendant as a ``(slug, status)`` pair,
        sorted lexicographically by slug. Named so that the verdict is
        self-contained — a human reading it does not need to re-query the index.
    """

    ancestor_slug: str
    live_descendants: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class EligiblePacket:
    """Evidence packet presented to the human decider on an eligible verdict (AC-0027).

    Eight required fields carry the decision context needed to confirm the
    closure. Self-sufficiency is the property that matters and it is stronger
    than "the decider consulted nothing": a decider who declines consults
    nothing too. A six-field version of this packet was put to a decider on a
    real eligible closure and returned *cannot decide* — it established that
    the tree was finished and never said what the intent promised, so there
    was no way to judge whether finishing the tree delivered it.

    ``stated_outcome`` and ``ratified_child_count`` are the two fields that
    answered that. The second is deliberately separate from the terminality
    basis: "every descendant is terminal" is silent about a descendant that
    was never created, so a completeness claim cannot be read off a
    terminality claim.

    Two optional fields report co-ownership and workspace-registration obligations.
    One optional field reports the product-bet disposition lookup.
    """

    decision_date: str
    """ISO-8601 date of this closure decision (e.g. ``"2026-09-27"``)."""

    decider: str
    """Identity of the decider performing the closure (non-empty)."""

    stated_outcome: str
    """The ancestor's own outcome, or a stated absence.

    Read from its declared outcome section. Never silently omitted: a decider
    cannot tell a missing field from an intent that promised nothing.
    """

    ratified_decomposed: str
    """Ancestor's full ``Decomposed:`` value (e.g. ``"2026-09-19 children"``)."""

    ratified_child_count: str
    """Descendants resolved against descendants declared, as ``"N of M"``.

    Reported separately from the terminality basis, and the two numbers are
    reported separately from each other, so a tree missing a ratified child
    is visible rather than inferred.
    """

    verification_basis: str
    """Basis on which the outcome was verified (non-empty)."""

    per_descendant_verdicts: tuple[tuple[str, str, str], ...]
    """One triple ``(slug, status, evidence_locator)`` per descendant in the
    closure, sorted lexicographically by slug.  Empty for non-collection
    termini (``closed-empty``, ``direct-light``).  The locator is a
    repository-relative path to the artifact file."""

    stated_confidence: str
    """What was NOT checked.  Names the known gaps in the evidence so the
    decider can judge whether those gaps matter for this specific decision."""

    outcome_co_owner: str | None = None
    """Typed peer pointer from ``Outcome co-owner:``, or ``None`` (AC-0028).
    The peer's current status is outside the boundary this check may read;
    naming it here is the whole obligation — the verdict is not gated on it."""

    workspace_registration: tuple[str, str] | None = None
    """``(entry_path, collection)`` naming the ``workspace.toml`` registration
    the decider must clear alongside the status write, or ``None`` when absent
    (AC-0031).  Leaving a non-``Draft`` closed intent in ``backlog.open``
    is permanently non-dispatchable."""

    disposition_row: str | None = None
    """Product-bet disposition row (e.g. ``"cool-30-days"``), or ``None`` when
    no eligibility clause reaches this artifact (AC-0034, AC-0035)."""


@dataclass(frozen=True)
class ClosureEligible:
    """All preconditions are met and the full descendant closure is terminal.

    ``ancestor_slug``: the slug of the ancestor being evaluated.
    ``basis``: a short phrase naming the ground for eligibility.
    ``packet``: the six-field evidence packet (AC-0027), or ``None`` when the
        caller did not supply packet-building parameters.  Callers that only
        need the verdict type do not need to supply these parameters; the
        packet is built only when ``_decider`` is passed to
        ``check_ancestor_closure``.
    """

    ancestor_slug: str
    basis: str
    packet: EligiblePacket | None = None


# Every reachable code path through the check returns exactly one of these.
ClosureVerdict = ClosureRefuse | ClosureNotEligible | ClosureEligible


# ── Closure terminality loader ────────────────────────────────────────────────

_closure_terminality_module: Any | None = None


def _get_closure_terminality() -> Any:
    """Load the co-located closure_terminality.py projection at most once.

    Follows the same loader discipline as ``_get_file_safety()``:
    ``lstat`` confirms it is a regular (non-symlink) file before loading, and
    the required symbols are asserted after exec.
    """
    global _closure_terminality_module
    if _closure_terminality_module is not None:
        return _closure_terminality_module

    path = _SCRIPT_DIR / "closure_terminality.py"
    try:
        st = os.lstat(path)
    except OSError as exc:  # pragma: no cover
        raise ImportError(f"required helper unavailable: {path.name}") from exc
    if not _stat.S_ISREG(st.st_mode) or _stat.S_ISLNK(st.st_mode):  # pragma: no cover
        raise ImportError(f"required helper is not a regular file: {path.name}")

    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(
            "_closure_index_terminality", path
        )
        if spec is None or spec.loader is None:  # pragma: no cover
            raise ImportError(f"required helper cannot be loaded: {path.name}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    except BaseException:  # pragma: no cover
        sys.modules.pop("_closure_index_terminality", None)
        raise
    finally:
        sys.dont_write_bytecode = prev

    _required = {"is_intent_terminal", "is_brief_terminal", "is_spec_terminal"}
    missing = _required - set(vars(mod))
    if missing:  # pragma: no cover
        sys.modules.pop("_closure_index_terminality", None)
        raise ImportError(
            f"required helper is incomplete: {path.name}: {', '.join(sorted(missing))}"
        )
    _closure_terminality_module = mod
    return mod


# ── Terminality routing ───────────────────────────────────────────────────────


def _is_descendant_terminal(record: DescendantRecord, ct: Any) -> bool:
    """True when the descendant's status ends its lifecycle.

    Routes to the kind-specific predicate from the terminality projection.
    An unknown kind resolves as live (safe direction: not-eligible is preferred
    over a false eligible that would authorise a terminal write).
    """
    if record.kind == "intent":
        return bool(ct.is_intent_terminal(record.status))
    if record.kind == "brief":
        return bool(ct.is_brief_terminal(record.status))
    if record.kind == "spec":
        return bool(ct.is_spec_terminal(record.status))
    return False  # unknown kind: conservative


# ── Pure classifier ───────────────────────────────────────────────────────────


def _classify_ancestor(
    ancestor_slug: str,
    ancestor_status: str,
    ancestor_terminus: str,
    descendants: dict[str, DescendantRecord],
    ct: Any,
) -> ClosureVerdict:
    """Classify one intent ancestor's closure eligibility.

    Pure: no I/O. All inputs are pre-resolved by the caller.
    ``ct`` is the loaded ``closure_terminality`` module.

    Refusal grounds outrank not-eligible and eligible (AC-0018). The order
    of the refusal checks below therefore matters: each one is checked before
    any non-refusal verdict is considered.
    """
    # AC-0009: already terminal → refuse (naming the closed status).
    if ct.is_intent_terminal(ancestor_status):
        return ClosureRefuse(
            ancestor_slug,
            f"already-closed: status is {ancestor_status!r}",
        )
    # AC-0008: not yet Accepted → refuse (naming the unreached precondition).
    if ancestor_status != "Accepted":
        return ClosureRefuse(
            ancestor_slug,
            f"not-accepted: status is {ancestor_status!r}; Accepted is required before closure",
        )
    # AC-0010: Decomposed absent or 'no' → refuse (naming the absent ratified delivery set).
    if not ancestor_terminus:
        return ClosureRefuse(
            ancestor_slug,
            "no-decomposed: Decomposed field absent or 'no'; a ratified delivery set is required",
        )

    # Non-collection termini: closed-empty and direct-light.

    if ancestor_terminus == "closed-empty":
        # AC-0012: terminus says empty but descendants found → refuse.
        if descendants:
            return ClosureRefuse(
                ancestor_slug,
                f"closed-empty-has-descendants: {sorted(descendants.keys())}",
            )
        # AC-0014: closed-empty with no descendants → eligible.
        return ClosureEligible(ancestor_slug, "closed-empty")

    if ancestor_terminus == "direct-light":
        # AC-0013: terminus says no artifact children but descendants found → refuse.
        if descendants:
            return ClosureRefuse(
                ancestor_slug,
                f"direct-light-has-descendants: {sorted(descendants.keys())}",
            )
        # AC-0015: direct-light with no descendants → eligible.
        return ClosureEligible(ancestor_slug, "direct-light")

    # Collection termini: children, brief, spec (and any unknown terminus that
    # _build_descendant_closure could not expand — it returns empty for those).

    # AC-0011: terminus expects artifact children but set is empty → refuse.
    if not descendants:
        return ClosureRefuse(
            ancestor_slug,
            f"empty-descendant-set: terminus {ancestor_terminus!r} expects artifact children",
        )

    # AC-0017: at least one live descendant → not-eligible, naming all of them.
    live = sorted(
        (r.slug, r.status)
        for r in descendants.values()
        if not _is_descendant_terminal(r, ct)
    )
    if live:
        return ClosureNotEligible(ancestor_slug, tuple(live))

    # AC-0016: all descendants terminal → eligible.
    return ClosureEligible(
        ancestor_slug,
        f"all-descendants-terminal: terminus {ancestor_terminus!r}",
    )


# ── Ancestor chain resolver ───────────────────────────────────────────────────


def resolve_intent_ancestors(
    slug: str,
    kind: str,
    fields: dict[str, str],
    root: Path,
    *,
    _reader: Reader | None = None,
    _dir_lister: DirLister | None = None,
    _snapshot_provider: SnapshotProvider | None = None,
) -> list[tuple[str, str, str]]:
    """Resolve the intent ancestor chain of a transitioning artifact.

    Returns ``[(ancestor_slug, ancestor_status, ancestor_terminus), ...]``, one
    tuple per intent ancestor found, walking upward until no declared up-edge
    remains. A brief is walked through but never returned as an ancestor.

    Up-edges by artifact kind:

    - ``spec``: feature-delivery relations from the canonical snapshot (both
      direct-delivery and coordinated-delivery name the feature intent directly).
      Non-feature Discovery: references are preserved via snapshot provenance
      records. This is the only implementation; no local file inversion remains.
    - ``brief``: ``Parent intent:``.
    - ``intent``: ``Parent intent:``.

    The intent→intent ``Parent intent:`` upward walk remains local (not feature
    delivery) and uses the existing confined reader.

    Raises ``_ClosureDeliveryRefusal`` with reason
    ``delivery-resolver-unavailable`` when a spec's snapshot cannot be obtained;
    the caller reports that code rather than treating the chain as empty.

    Called from close-work's closeout procedure alongside
    ``check_ancestor_closure`` to fire the check on every intent ancestor of
    the transitioning artifact.
    """
    reader: Reader = _reader if _reader is not None else _make_confined_reader(root)
    dir_lister: DirLister = (
        _dir_lister if _dir_lister is not None else _default_dir_lister
    )

    ancestors: list[tuple[str, str, str]] = []
    visited_slugs: set[str] = {slug}

    intents_dir = _intents_dir(root)

    def _scan_for_slug(
        collection_dir: Path, target_slug: str
    ) -> dict[str, str] | None:
        """Scan a collection directory for an artifact with a matching ``Slug:``."""
        for path in dir_lister(collection_dir):
            try:
                text = reader(path)
                f = _preamble(text)
                if f.get("Slug") == target_slug:
                    return f
            except (OSError, ValueError):
                continue
        return None

    def _add_intent_and_recurse(
        intent_slug: str, intent_fields: dict[str, str]
    ) -> None:
        """Add an intent ancestor and walk upward via its ``Parent intent:``.

        The upward walk (intent → intent) stays local: it is not feature delivery.
        Only ``intent:`` typed parent edges are followed (not capability/outcome/
        opportunity) so that the walk correctly traverses the real parent chain.
        """
        if intent_slug in visited_slugs:
            return
        visited_slugs.add(intent_slug)
        status = intent_fields.get("Status", "")
        terminus = _terminus_from_decomposed(intent_fields.get("Decomposed", ""))
        ancestors.append((intent_slug, status, terminus))
        # Walk upward from this intent to find further ancestors (local, non-delivery).
        parent_val = intent_fields.get("Parent intent", "")
        if parent_val.startswith("intent:"):
            parent_slug = parent_val[len("intent:"):]
            parent_fields = _scan_for_slug(intents_dir, parent_slug)
            if parent_fields:
                _add_intent_and_recurse(parent_slug, parent_fields)

    if kind == "spec":
        # The spec→feature step is feature-delivery parsing; derive it from the
        # canonical snapshot. Both direct-delivery and coordinated-delivery
        # relations carry the feature intent identifier directly.
        provider = _snapshot_provider if _snapshot_provider is not None else _run_resolver
        try:
            snap = provider(root)
        except Exception as _exc:
            # Resolver failure is not a no-delivery signal.  Surface it so
            # the caller receives delivery-resolver-unavailable.
            raise _ClosureDeliveryRefusal("delivery-resolver-unavailable") from _exc

        if snap is not None:
            spec_id = f"spec:{slug}"
            seen_feature_slugs: set[str] = set()

            # Feature ancestors via delivery relations.
            for rel in snap.get("relations", []):
                if rel.get("spec") == spec_id and rel.get("type") in (
                    "direct-delivery",
                    "coordinated-delivery",
                ):
                    intent_ref = rel.get("intent", "")
                    if intent_ref.startswith("intent:"):
                        feat_slug = intent_ref[len("intent:"):]
                        if feat_slug not in seen_feature_slugs and feat_slug not in visited_slugs:
                            seen_feature_slugs.add(feat_slug)
                            feat_fields = _scan_for_slug(intents_dir, feat_slug)
                            if feat_fields:
                                _add_intent_and_recurse(feat_slug, feat_fields)

            # Non-feature Discovery: references from contextual-provenance records.
            # A spec whose Discovery: names a non-feature intent contributes that
            # intent as an ancestor via the provenance record (field "Discovery").
            for prov in snap.get("provenance", []):
                if prov.get("subject") == spec_id and prov.get("field") == "Discovery":
                    target = prov.get("target", "")
                    # Resolve "intent:<slug>" provenance targets to a slug.
                    if target.startswith("intent:"):
                        prov_slug = target[len("intent:"):]
                        if prov_slug not in seen_feature_slugs and prov_slug not in visited_slugs:
                            seen_feature_slugs.add(prov_slug)
                            prov_fields = _scan_for_slug(intents_dir, prov_slug)
                            if prov_fields:
                                _add_intent_and_recurse(prov_slug, prov_fields)
                    elif _is_intents_rel_path(target):
                        # Path-form target: bare or backtick Discovery: values
                        # that name a non-feature intent (resolver normalizes
                        # backticks to bare path before storing in provenance).
                        # Read the file through the confined reader to get Slug.
                        target_path = root / target
                        try:
                            text = reader(target_path)
                            path_fields = _preamble(text)
                            path_slug = path_fields.get("Slug", "")
                        except (OSError, ValueError):
                            path_slug = ""
                        if (
                            path_slug
                            and path_slug not in seen_feature_slugs
                            and path_slug not in visited_slugs
                        ):
                            seen_feature_slugs.add(path_slug)
                            _add_intent_and_recurse(path_slug, path_fields)

    elif kind in ("brief", "intent"):
        # Parent intent: route — local, not feature delivery.
        parent_val = fields.get("Parent intent", "")
        if parent_val.startswith("intent:"):
            parent_slug = parent_val[len("intent:"):]
            parent_fields = _scan_for_slug(intents_dir, parent_slug)
            if parent_fields:
                _add_intent_and_recurse(parent_slug, parent_fields)

    return ancestors


# ── Production entry point ────────────────────────────────────────────────────


def check_ancestor_closure(
    ancestor_slug: str,
    ancestor_status: str,
    ancestor_terminus: str,
    root: Path,
    *,
    _reader: Reader | None = None,
    _dir_lister: DirLister | None = None,
    _freshness_checker: FreshnessChecker | None = None,
    _snapshot_provider: SnapshotProvider | None = None,
    # Packet-building parameters (AC-0027, AC-0028, AC-0031, AC-0034, AC-0035).
    # All are optional; callers that omit _decider receive a verdict with
    # packet=None, preserving full backward compatibility.
    _decider: str | None = None,
    _decision_date: str | None = None,
    _ancestor_fields: dict[str, str] | None = None,
    _workspace_lookup: WorkspaceLookup | None = None,
    _disposition_lookup: DispositionLookup | None = None,
) -> ClosureVerdict:
    """Evaluate whether one intent ancestor is closure-eligible.

    Called from close-work's closeout procedure on each intent ancestor of a
    transitioning artifact. Returns one of three verdict types (AC-0004):

    - ``ClosureRefuse``: a precondition is unmet; names the missing precondition.
    - ``ClosureNotEligible``: at least one descendant is live; names all of them.
    - ``ClosureEligible``: all preconditions met and all descendants terminal.
      When ``_decider`` is supplied, ``ClosureEligible.packet`` carries the
      six-field evidence packet (AC-0027).

    This is the **only** function permitted to call ``_build_descendant_closure``
    (AC-0026). The caller-enumeration test in ``test_closure_entry.py`` asserts
    this invariant and fails when a second caller is added.

    **AC-0022** — the first action is the freshness check. ``_freshness_checker``
    is a test seam; the production default is ``_make_default_freshness_checker(root)``,
    which calls ``git`` with three subprocess steps.  The checker returns
    ``bool | None``:

    - ``True``  — fresh; proceed.
    - ``False`` — stale; refuse with ``stale-base``.
    - ``None``  — indeterminate (git unavailable, timeout, or root is not a git
      repository); refuse with ``freshness-indeterminate``.

    Tests inject ``lambda: True``, ``lambda: False``, or ``lambda: None`` to
    drive each arm without a live git repository.

    **AC-0021** — every input is re-resolved on each call. No descendant set,
    index, or verdict is reused across calls. ``_build_descendant_closure`` builds
    a new in-memory dict each time; the dict is local to this call's frame.

    **AC-0027 / AC-0028 / AC-0031 / AC-0034 / AC-0035** — when ``_decider``
    is supplied and the verdict is ``ClosureEligible``, ``_build_eligible_packet``
    is called with the resolved descendants and the caller-supplied context.
    ``_ancestor_fields`` carries the ancestor's full preamble fields so the packet
    can include the ratified ``Decomposed:`` value and any ``Outcome co-owner:``.
    ``_workspace_lookup`` and ``_disposition_lookup`` are test seams; the production
    caller supplies its own implementations.
    """
    # AC-0022: refuse immediately on stale or indeterminate freshness.
    checker: FreshnessChecker = (
        _freshness_checker
        if _freshness_checker is not None
        else _make_default_freshness_checker(root)
    )
    freshness_result: bool | None = checker()
    if freshness_result is None:
        return ClosureRefuse(
            ancestor_slug,
            "freshness-indeterminate: could not determine whether HEAD is current "
            "(git unavailable, timed out, or root is not a git repository); "
            "verify the base manually and re-run",
        )
    if not freshness_result:
        return ClosureRefuse(
            ancestor_slug,
            "stale-base: HEAD is not current against the merge target; "
            "surface and merge before running the closure check",
        )

    ct = _get_closure_terminality()

    # The ancestor's own promise reaches the packet through ``_ancestor_fields``
    # under the key ``__outcome__``. It is *supplied*, not scanned for: the
    # caller performing the closeout already has the ancestor open, and adding
    # a scan here would read artifacts the read bounds do not admit. Use
    # ``read_stated_outcome`` on the ancestor's text to produce it. When it is
    # absent the packet states the absence rather than dropping the field.
    ancestor_fields: dict[str, str] = dict(_ancestor_fields or {})

    try:
        descendants = _build_descendant_closure(
            ancestor_slug,
            ancestor_terminus,
            root,
            _reader=_reader,
            _dir_lister=_dir_lister,
            _snapshot_provider=_snapshot_provider,
        )
    except _ClosureDeliveryRefusal as _ref:
        return ClosureRefuse(ancestor_slug, _ref.reason)

    verdict: ClosureVerdict = _classify_ancestor(
        ancestor_slug, ancestor_status, ancestor_terminus, descendants, ct
    )

    # Build the evidence packet when eligible and a decider was supplied (AC-0027).
    if isinstance(verdict, ClosureEligible) and _decider:
        packet = _build_eligible_packet(
            ancestor_slug=ancestor_slug,
            ancestor_terminus=ancestor_terminus,
            descendants=descendants,
            basis=verdict.basis,
            decider=_decider,
            decision_date=_decision_date or _current_date(),
            ancestor_fields=ancestor_fields,
            workspace_lookup=_workspace_lookup,
            disposition_lookup=_disposition_lookup,
        )
        verdict = ClosureEligible(
            ancestor_slug=ancestor_slug,
            basis=verdict.basis,
            packet=packet,
        )

    return verdict


# ── Closure record helpers ────────────────────────────────────────────────────


def build_fulfilled_value(date: str, decider: str, evidence: str) -> str:
    """Build a ``Fulfilled:`` field value satisfying the shipped value rule.

    The shipped rule (``intent_shape._check_dated_evidence``) requires an
    ISO-8601 calendar date, a single space, then non-empty evidence text.
    This function produces ``"{date} {decider}: {evidence}"``, which satisfies
    that rule when *date* is a valid ISO-8601 date and *decider* and *evidence*
    are both non-empty.

    AC-0032: verify by round-tripping through that rule, not by matching a
    string — the rule is the authority, not this function's output format.

    Raises ``ValueError`` when any argument is empty.
    """
    if not date:
        raise ValueError("date must be non-empty")
    if not decider:
        raise ValueError("decider must be non-empty")
    if not evidence:
        raise ValueError("evidence must be non-empty")
    return f"{date} {decider}: {evidence}"


def write_closure_record(
    path: Path,
    fulfilled_value: str,
    *,
    _confirmed: bool | None,
    _writer: Callable[[Path, str], None] | None = None,
) -> bool:
    """Write a closure record if and only if the human confirmed.

    This function is the confirmation seam for the closure status write (AC-0030).
    ``check_ancestor_closure`` never calls it (AC-0029) — the check is read-only
    and produces only a verdict and packet; all mutation happens after the human
    answers.

    Returns ``False`` without writing when ``_confirmed`` is ``False`` (human
    declined) or ``None`` (human has not yet answered).  Both cases leave no
    ``Status:`` write on the filesystem — this is what AC-0030 asserts, and it
    is a different predicate from AC-0029 (which asserts the check itself never
    writes).  A write-raising filesystem double cannot observe ordering, so
    AC-0030 drives this seam directly.

    ``_writer(path, fulfilled_value)`` performs the actual file modification.
    This module does not write to disk by design; the production caller supplies
    a writer from ``close-work``'s existing confirmation machinery.

    Returns ``True`` if the record was written, ``False`` otherwise.
    """
    if _confirmed is not True:
        return False
    if _writer is None:
        return False
    _writer(path, fulfilled_value)
    return True
