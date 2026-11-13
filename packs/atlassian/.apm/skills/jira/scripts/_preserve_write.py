"""Preserve-first tracker writes: plan, digest, dispositions, route guard, storage.

Pure pieces shared by the Jira and Jira Align clients and CLIs. Standard library
only. The two skills each ship a byte-identical copy of this file because an
installed skill cannot import from another skill; a parity test keeps them equal.

Model in one paragraph: ``build_plan`` freezes target, flavor, base URL, write
method, notify setting and each field's current/proposed/disposition and hashes
them. ``verify_plan`` recomputes the hash from the contents and compares it to the
approved digest. A ``VerifiedPlan`` authorizes exactly one request, the plan's
``resolved_write``. ``guard_request`` is what a client's request chokepoint calls
for every non-GET request: it lets a closed allowlist through and demands a
verified plan for everything else. ``prepare_write`` re-checks staleness and lossy
replaces, and ``write_prior_then_call`` saves the prior-value record before the
caller's write callback runs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import stat
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar
from urllib.parse import parse_qsl, unquote, urlsplit

__all__ = [
    "APPEND_LABEL",
    "CONTRACT_VERSION",
    "DISPOSITIONS",
    "FLAVOR_ALIGN",
    "FLAVOR_CLOUD",
    "FLAVOR_SERVER",
    "GUARD_EXIT_CODE",
    "LOSSY_EXEMPT_NODE_TYPES",
    "ROUTE_ALLOWED",
    "ROUTE_GUARDED",
    "FieldPlan",
    "GuardRefused",
    "LossReport",
    "Plan",
    "ResolvedWrite",
    "VerifiedPlan",
    "api_prefix_for",
    "append_value",
    "assert_transition_body_allowed",
    "build_plan",
    "build_prior_record",
    "build_undo_plan",
    "build_write_body",
    "check_unchanged",
    "classify_route",
    "compute_digest",
    "digest_line",
    "encode_text",
    "guard_request",
    "instance_slug",
    "load_plan",
    "load_record",
    "lossy_report",
    "may_follow_redirect",
    "normalize_base_url",
    "plan_to_obj",
    "prepare_write",
    "render_preview",
    "resolve_field_value",
    "resolved_write",
    "state_root",
    "verify_plan",
    "write_plan_file",
    "write_prior_then_call",
]

T = TypeVar("T")

CONTRACT_VERSION = 1
GUARD_EXIT_CODE = 10

FLAVOR_CLOUD = "cloud"
FLAVOR_SERVER = "server"
FLAVOR_ALIGN = "align"
_FLAVORS = (FLAVOR_CLOUD, FLAVOR_SERVER, FLAVOR_ALIGN)

DISPOSITIONS = ("keep", "append", "replace")
APPEND_LABEL = "Appended text:"

LOSSY_EXEMPT_NODE_TYPES = frozenset(
    {"paragraph", "heading", "bulletList", "orderedList", "listItem",
     "codeBlock", "text", "hardBreak"}
)

ROUTE_ALLOWED = "allowed"
ROUTE_GUARDED = "guarded"

_READ_METHODS = frozenset({"GET", "HEAD"})
_OVERRIDE_HEADERS = frozenset(
    {"x-http-method-override", "x-http-method", "x-method-override"}
)

JIRA_KEY = r"[A-Z][A-Z0-9]{0,9}-[1-9][0-9]{0,11}"
ALIGN_RESOURCE = r"[A-Za-z][A-Za-z0-9]{0,63}"
NUMERIC_ID = r"[1-9][0-9]{0,11}"
_JIRA_KEY_RE = re.compile(JIRA_KEY)
_ALIGN_TARGET_RE = re.compile(f"{ALIGN_RESOURCE}/{NUMERIC_ID}")
_ISSUE_REF_RE = re.compile(f"{JIRA_KEY}|{NUMERIC_ID}")
_RESOURCE_RE = re.compile(ALIGN_RESOURCE)
_ID_RE = re.compile(NUMERIC_ID)
_DIGEST_RE = re.compile(r"[0-9a-f]{64}")

_PLAN_KEYS = frozenset(
    {"contract_version", "target", "flavor", "base_url", "method", "notify",
     "fields", "digest"}
)
_FIELD_KEYS = frozenset({"current", "proposed", "disposition"})
_RECORD_KEYS = frozenset({"identifier", "plan_digest", "entries"})
_RECORD_KEYS_ALIGN = _RECORD_KEYS | {"record"}
_ENTRY_KEYS = frozenset({"field", "old", "written"})

_MAX_FILE_BYTES = 8 * 1024 * 1024
_MAX_NAME_CLASH = 1000


class GuardRefused(Exception):  # noqa: N818 - the spec names this class
    """A write was refused by the preserve-first guard; the CLI exits ``GUARD_EXIT_CODE``.

    The message is encoded so tracker-sourced characters in it are visible (AC4).
    """

    def __init__(self, message: str) -> None:
        super().__init__(encode_text(message, keep_newline=False))


# --- output encoding (AC4, AC5) ------------------------------------------------


def encode_text(text: str, *, keep_newline: bool = True) -> str:
    """Return ``text`` with Cc (except a line-ending newline), Cf, Cs, Zl, Zp and ESC visible.

    With ``keep_newline=False`` the newline is encoded too, so the result is one line.
    """

    out: list[str] = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch == "\n" and keep_newline:
            out.append(ch)
        elif cat == "Cc" or ch == "\x1b":
            out.append(f"\\x{ord(ch):02x}" if ord(ch) < 0x100 else f"\\u{ord(ch):04x}")
        elif cat in ("Cf", "Cs", "Zl", "Zp"):
            out.append(f"\\u{ord(ch):04x}" if ord(ch) <= 0xFFFF else f"\\U{ord(ch):08x}")
        else:
            out.append(ch)
    return "".join(out)


def _render_value(value: Any) -> str:
    """Render a JSON value for the preview; strings show as-is, others as sorted JSON."""

    if isinstance(value, str):
        return encode_text(value)
    return encode_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _indent(text: str, prefix: str = "    | ") -> str:
    """Prefix every line so tracker text can never start a line with ``digest:``."""

    return "\n".join(prefix + line for line in text.split("\n"))


def _adf_text(node: Any) -> str:
    """Text content of an ADF node, depth first; a node with no text shows as ``[type]``."""

    parts: list[str] = []
    stack: list[Any] = [node]
    while stack:
        item = stack.pop()
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("text"), str):
            parts.append(item["text"])
        content = item.get("content")
        if isinstance(content, list):
            stack.extend(reversed(content))
    text = "".join(parts)
    kind = node.get("type") if isinstance(node, dict) else None
    return text if text else f"[{kind}]"


def _render_after_write(flavor: str, current: Any, written: Any) -> str:
    """Render an appended value. Cloud: one ``  `` (existing) or ``+ `` (added) line per node.

    ``written`` is what the write path sends, so the preview cannot drift from it.
    """

    if flavor != FLAVOR_CLOUD:
        return _render_value(written)
    existing = len(current.get("content", [])) if isinstance(current, dict) else 0
    lines: list[str] = []
    for index, node in enumerate(written.get("content", [])):
        mark = "  " if index < existing else "+ "
        for line in encode_text(_adf_text(node)).split("\n"):
            lines.append(mark + line)
    return "\n".join(lines) or "(empty)"


def digest_line(digest: str) -> str:
    """Return the single ``digest: <hex>`` line (AC5)."""

    if not _DIGEST_RE.fullmatch(digest):
        raise GuardRefused("digest is not a 64-character lowercase hex string")
    return f"digest: {digest}"


# --- URLs, origins, slug --------------------------------------------------------


def _origin_parts(url: str) -> tuple[str, str, int, str]:
    """Return (scheme, host, effective port, context path) for an http(s) URL."""

    try:
        parts = urlsplit(url)
        port = parts.port
        host = parts.hostname
    except ValueError as exc:
        raise GuardRefused("base URL is not a valid URL") from exc
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https") or not host:
        raise GuardRefused("base URL must be an http or https URL with a host")
    if parts.username is not None or parts.password is not None:
        raise GuardRefused("base URL must not carry credentials")
    if parts.query or parts.fragment:
        raise GuardRefused("base URL must not carry a query or fragment")
    effective = port if port is not None else (443 if scheme == "https" else 80)
    return scheme, host.lower(), effective, parts.path.rstrip("/")


def normalize_base_url(url: str) -> str:
    """Return ``scheme://host[:port]/path`` lowercased, default port dropped, no trailing slash."""

    scheme, host, port, path = _origin_parts(url)
    shown = f"[{host}]" if ":" in host else host
    default = 443 if scheme == "https" else 80
    netloc = shown if port == default else f"{shown}:{port}"
    return f"{scheme}://{netloc}{path}"


def instance_slug(base_url: str) -> str:
    """Return the folder name for an instance: host plus a hash of scheme, host, port, path.

    Holds only letters, digits, dot and hyphen; never empty or dots-only (AC16).
    """

    scheme, host, port, path = _origin_parts(base_url)
    digest = hashlib.sha256(f"{scheme}://{host}:{port}{path}".encode()).hexdigest()[:12]
    safe_host = re.sub(r"[^A-Za-z0-9.-]", "-", host)[:63]
    return f"{safe_host}-{digest}"


def api_prefix_for(flavor: str) -> str:
    """Return the REST prefix a flavor's plan writes under."""

    if flavor == FLAVOR_CLOUD:
        return "/rest/api/3"
    if flavor == FLAVOR_SERVER:
        return "/rest/api/2"
    if flavor == FLAVOR_ALIGN:
        return "/rest/align/api/2"
    raise GuardRefused("unknown flavor")


# --- plan model (AC3) -------------------------------------------------------------


@dataclass(frozen=True)
class FieldPlan:
    """One named field: its value now, the proposed value, and the disposition."""

    current: Any
    proposed: Any
    disposition: str


@dataclass(frozen=True)
class Plan:
    """A preview of one record's write. ``digest`` is the stored value, not trusted."""

    target: str
    flavor: str
    base_url: str
    method: str
    notify: bool
    fields: Mapping[str, FieldPlan]
    digest: str
    contract_version: int = CONTRACT_VERSION

    def recomputed_digest(self) -> str:
        """Recompute the digest from this plan's contents."""

        return compute_digest(
            target=self.target, flavor=self.flavor, base_url=self.base_url,
            method=self.method, notify=self.notify, fields=self.fields,
        )


def compute_digest(
    *,
    target: str,
    flavor: str,
    base_url: str,
    method: str,
    notify: bool,
    fields: Mapping[str, FieldPlan],
) -> str:
    """SHA-256 of canonical JSON over target, flavor, base URL, method, notify, fields."""

    payload = {
        "target": target,
        "flavor": flavor,
        "base_url": base_url,
        "method": method,
        "notify": notify,
        "fields": {
            name: {"current": f.current, "proposed": f.proposed, "disposition": f.disposition}
            for name, f in fields.items()
        },
    }
    blob = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )
    return hashlib.sha256(blob.encode("ascii")).hexdigest()


def _is_text_value(flavor: str, value: Any) -> bool:
    """True when ``value`` is a text field value for the flavor (ADF doc, or string)."""

    if value is None:
        return True
    if flavor == FLAVOR_CLOUD:
        return isinstance(value, dict) and value.get("type") == "doc"
    return isinstance(value, str)


def _check_method(flavor: str, method: str) -> None:
    allowed = ("PUT", "PATCH") if flavor == FLAVOR_ALIGN else ("PUT",)
    if method not in allowed:
        raise GuardRefused(f"method {method} is not allowed for flavor {flavor}")


def _check_target(flavor: str, target: str) -> None:
    pattern = _ALIGN_TARGET_RE if flavor == FLAVOR_ALIGN else _JIRA_KEY_RE
    if not pattern.fullmatch(target):
        raise GuardRefused("target is outside the identifier alphabet")


def _check_field_plan(flavor: str, name: str, fp: FieldPlan) -> None:
    if not name or len(name) > 128 or encode_text(name, keep_newline=False) != name:
        raise GuardRefused("field name is empty, too long, or holds control characters")
    if fp.disposition not in DISPOSITIONS:
        raise GuardRefused(f"field {name}: disposition must be keep, append or replace")
    if fp.disposition == "append" and not (
        _is_text_value(flavor, fp.current) and _is_text_value(flavor, fp.proposed)
    ):
        raise GuardRefused(f"field {name}: append is defined for text fields only")


def build_plan(
    *,
    target: str,
    flavor: str,
    base_url: str,
    method: str,
    notify: bool,
    fields: Mapping[str, Mapping[str, Any]],
) -> Plan:
    """Build a plan; ``fields`` maps name to ``{current, proposed, disposition}``.

    Raises ``GuardRefused`` for an unknown flavor, method, target or disposition, and
    for ``append`` on a non-text field (AC29).
    """

    if flavor not in _FLAVORS:
        raise GuardRefused("unknown flavor")
    _check_method(flavor, method)
    _check_target(flavor, target)
    if not isinstance(notify, bool):
        raise GuardRefused("notify must be a boolean")
    if not fields:
        raise GuardRefused("a plan needs at least one named field")
    plan_fields: dict[str, FieldPlan] = {}
    for name, spec in fields.items():
        fp = FieldPlan(spec.get("current"), spec.get("proposed"), str(spec.get("disposition")))
        _check_field_plan(flavor, name, fp)
        plan_fields[name] = fp
    base = normalize_base_url(base_url)
    digest = compute_digest(
        target=target, flavor=flavor, base_url=base, method=method, notify=notify,
        fields=plan_fields,
    )
    return Plan(target, flavor, base, method, notify, plan_fields, digest)


def plan_to_obj(plan: Plan) -> dict[str, Any]:
    """Return the JSON-ready plan file object (the closed plan field set)."""

    return {
        "contract_version": plan.contract_version,
        "target": plan.target,
        "flavor": plan.flavor,
        "base_url": plan.base_url,
        "method": plan.method,
        "notify": plan.notify,
        "fields": {
            n: {"current": f.current, "proposed": f.proposed, "disposition": f.disposition}
            for n, f in plan.fields.items()
        },
        "digest": plan.digest,
    }


# --- dispositions: append, replace, lossy (AC23-AC29) ------------------------------


def _adf_paragraph(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


def append_value(flavor: str, current: Any, proposed: Any) -> Any:
    """Return ``current`` with a labelled block holding ``proposed`` added at the end.

    Cloud: a labelled paragraph plus the proposed nodes after the last existing node of
    ``doc.content``; existing nodes are untouched. Server/DC and Jira Align: the original
    string, then a blank line, the label, and the proposed text; the original is a
    byte-exact prefix. Non-text values raise ``GuardRefused`` (AC29).
    """

    if not (_is_text_value(flavor, current) and _is_text_value(flavor, proposed)):
        raise GuardRefused("append is defined for text fields only")
    if flavor == FLAVOR_CLOUD:
        empty: dict[str, Any] = {"type": "doc", "version": 1, "content": []}
        doc: dict[str, Any] = copy.deepcopy(current) if current else empty
        nodes: list[Any] = copy.deepcopy(proposed.get("content", [])) if proposed else []
        doc["content"] = [*doc.get("content", []), _adf_paragraph(APPEND_LABEL), *nodes]
        return doc
    base = current or ""
    block = f"{APPEND_LABEL}\n{proposed or ''}"
    return f"{base}\n\n{block}" if base else block


def resolve_field_value(flavor: str, fp: FieldPlan) -> Any:
    """Return the value a ``replace`` or ``append`` field writes; ``keep`` has none."""

    if fp.disposition == "replace":
        return fp.proposed
    if fp.disposition == "append":
        return append_value(flavor, fp.current, fp.proposed)
    raise GuardRefused("a keep field has no write value")


@dataclass(frozen=True)
class LossReport:
    """ADF node and mark types a replace drops, and whether they block it (AC26-AC28)."""

    node_types: tuple[str, ...] = ()
    mark_types: tuple[str, ...] = ()

    @property
    def blocking_nodes(self) -> tuple[str, ...]:
        """Dropped node types outside the exempt set."""

        return tuple(t for t in self.node_types if t not in LOSSY_EXEMPT_NODE_TYPES)

    @property
    def blocking(self) -> bool:
        """True when the drop needs ``--allow-lossy``: any non-exempt node or any mark."""

        return bool(self.blocking_nodes or self.mark_types)


def _adf_types(doc: Any) -> tuple[set[str], set[str]]:
    """Collect node types and mark types in an ADF tree (iterative, no recursion limit)."""

    nodes: set[str] = set()
    marks: set[str] = set()
    stack: list[Any] = [doc]
    while stack:
        item = stack.pop()
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("type"), str):
            nodes.add(item["type"])
        for mark in item.get("marks") or []:
            if isinstance(mark, dict) and isinstance(mark.get("type"), str):
                marks.add(mark["type"])
        content = item.get("content")
        if isinstance(content, list):
            stack.extend(content)
    return nodes, marks


def lossy_report(current: Any, proposed: Any) -> LossReport:
    """Report every ADF node type and mark type present in ``current`` but not ``proposed``."""

    cur_nodes, cur_marks = _adf_types(current)
    new_nodes, new_marks = _adf_types(proposed)
    return LossReport(
        tuple(sorted(cur_nodes - new_nodes)), tuple(sorted(cur_marks - new_marks))
    )


# --- write body and resolved write (AC8-AC10) -------------------------------------------


def build_write_body(plan: Plan) -> dict[str, Any]:
    """Return the request body: resolved replace/append values only, keep fields omitted.

    Jira: ``{"fields": {...}}``. Jira Align: the field map itself.
    """

    values = {
        name: resolve_field_value(plan.flavor, f)
        for name, f in plan.fields.items()
        if f.disposition != "keep"
    }
    return values if plan.flavor == FLAVOR_ALIGN else {"fields": values}


@dataclass(frozen=True)
class ResolvedWrite:
    """The single request a verified plan authorizes."""

    method: str
    url: str
    body: dict[str, Any]


def resolved_write(plan: Plan) -> ResolvedWrite:
    """Return the plan's write: method, absolute URL, and body."""

    if plan.flavor == FLAVOR_ALIGN:
        path = f"{api_prefix_for(plan.flavor)}/{plan.target}"
        query = ""
    else:
        path = f"{api_prefix_for(plan.flavor)}/issue/{plan.target}"
        query = "" if plan.notify else "?notifyUsers=false"
    return ResolvedWrite(plan.method, f"{plan.base_url}{path}{query}", build_write_body(plan))


class VerifiedPlan:
    """A plan whose recomputed digest equals the approved digest. Make one with ``verify_plan``."""

    _key = object()

    def __init__(self, plan: Plan, key: object) -> None:
        if key is not VerifiedPlan._key:
            raise GuardRefused("a verified plan comes only from verify_plan")
        self.plan = plan
        self.write = resolved_write(plan)

    def authorizes(self, method: str, url: str, body: Any) -> bool:
        """True only for the one request equal to the plan's method, URL and body (AC8)."""

        want = self.write
        if method.upper() != want.method:
            return False
        if _canonical_url(url, self.plan.base_url) != _canonical_url(want.url, self.plan.base_url):
            return False
        return _canonical_json(body) == _canonical_json(want.body)


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError):
        return "\x00unserializable"


def verify_plan(plan: Plan, approved_digest: str) -> VerifiedPlan:
    """Recompute the digest from contents; refuse unless stored, recomputed and approved agree.

    An edited plan whose stored digest was left alone fails here (AC6, AC7).
    """

    recomputed = plan.recomputed_digest()
    if not (recomputed == approved_digest == plan.digest):
        raise GuardRefused(
            "plan digest does not match the approved digest; rerun plan-update and approve again"
        )
    return VerifiedPlan(plan, VerifiedPlan._key)


# --- stale check, lossy check, prepare (AC11, AC26, AC27) ---------------------------------


def check_unchanged(plan: Plan, current_by_field: Mapping[str, Any]) -> None:
    """Refuse when any named field's value now differs from the plan's recorded current.

    Values compare by canonical JSON (the form the digest hashes), so ``1``, ``true`` and
    ``1.0`` are three different values.
    """

    drifted = [
        n for n, f in plan.fields.items()
        if _canonical_json(current_by_field.get(n)) != _canonical_json(f.current)
    ]
    if drifted:
        raise GuardRefused(
            "fields changed since the preview: " + ", ".join(sorted(drifted))
            + "; rerun plan-update (a small race remains between this check and the write)"
        )


def prepare_write(
    verified: VerifiedPlan, current_by_field: Mapping[str, Any], *, allow_lossy: bool = False
) -> ResolvedWrite:
    """Run the stale and lossy checks and return the write the plan authorizes.

    Raises ``GuardRefused`` for a stale field, a lossy ``replace`` without ``allow_lossy``,
    or a plan that writes no field.
    """

    plan = verified.plan
    check_unchanged(plan, current_by_field)
    if all(f.disposition == "keep" for f in plan.fields.values()):
        raise GuardRefused("plan keeps every field; nothing to write")
    if plan.flavor == FLAVOR_CLOUD and not allow_lossy:
        for name, f in plan.fields.items():
            if f.disposition != "replace":
                continue
            report = lossy_report(f.current, f.proposed)
            if report.blocking:
                dropped = ", ".join([*report.blocking_nodes, *report.mark_types])
                raise GuardRefused(
                    f"field {name}: replace would drop {dropped}; pass --allow-lossy to proceed"
                )
    return verified.write


# --- route matcher and guard (AC30-AC35) -----------------------------------------------------


def may_follow_redirect(method: str) -> bool:
    """Only reads follow a redirect; a non-GET request never does (AC34)."""

    return method.upper() in _READ_METHODS


def assert_transition_body_allowed(body: Any) -> None:
    """Refuse a transition body that carries ``fields`` or ``update`` (AC32).

    Clients call this before the transition name lookup sends anything.
    """

    if isinstance(body, Mapping) and ("fields" in body or "update" in body):
        raise GuardRefused("a transition with field content is always refused; use plan-update")


def _resolve_path_segments(raw_path: str) -> list[str]:
    """Decode percent-encoding and return segments; refuse smuggling forms."""

    layer = raw_path
    for _ in range(4):
        low = layer.lower()
        if "%2f" in low or "%5c" in low:
            raise GuardRefused("request path holds an encoded separator")
        decoded = unquote(layer)
        if decoded == layer:
            break
        layer = decoded
    else:
        raise GuardRefused("request path is encoded too deeply")
    if ".." in layer or ";" in layer or "\\" in layer:
        raise GuardRefused("request path holds '..', ';' or a backslash")
    if any(unicodedata.category(c) in ("Cc", "Cf") for c in layer):
        raise GuardRefused("request path holds control characters")
    return layer.split("/")[1:] if layer.startswith("/") else layer.split("/")


def _split_target(target: str, base_url: str) -> tuple[list[str], str]:
    """Return (path segments below the base context path, canonical query) for a target.

    An absolute target must share scheme, host and port with the base URL.
    """

    scheme, host, port, base_path = _origin_parts(base_url)
    try:
        parts = urlsplit(target)
        t_port = parts.port
    except ValueError as exc:
        raise GuardRefused("request URL is not valid") from exc
    path = parts.path
    if parts.scheme or parts.netloc:
        t_scheme = parts.scheme.lower() or scheme
        t_port = t_port if t_port is not None else (443 if t_scheme == "https" else 80)
        t_host = (parts.hostname or "").lower()
        if (t_scheme, t_host, t_port) != (scheme, host, port) or "@" in parts.netloc:
            raise GuardRefused("request origin differs from the configured base URL")
        segments = _resolve_path_segments(path)
        base_segments = [s for s in base_path.split("/") if s]
        if segments[: len(base_segments)] != base_segments:
            raise GuardRefused("request path is outside the configured base URL")
        segments = segments[len(base_segments):]
    else:
        segments = _resolve_path_segments(path if path.startswith("/") else "/" + path)
    return segments, _canonical_query(parts.query)


def _canonical_query(query: str) -> str:
    return "&".join(f"{k}={v}" for k, v in sorted(parse_qsl(query, keep_blank_values=True)))


def _canonical_url(url: str, base_url: str) -> str:
    """Canonical absolute form of ``url`` (relative to ``base_url`` when not absolute)."""

    segments, query = _split_target(url, base_url)
    return f"{normalize_base_url(base_url)}/{'/'.join(segments)}?{query}"


def _allowlisted(
    client: str, method: str, segments: list[str], api_prefix: str, body: Any, confirmed: bool
) -> bool:
    """Match method and path (and for transition, body) against the closed allowlist."""

    prefix = [s for s in api_prefix.split("/") if s]
    if segments[: len(prefix)] != prefix:
        return False
    rest = segments[len(prefix):]
    if client == "jira-align":
        if method == "POST":
            return len(rest) == 1 and bool(_RESOURCE_RE.fullmatch(rest[0]))
        return (
            method == "DELETE" and confirmed and len(rest) == 2
            and bool(_RESOURCE_RE.fullmatch(rest[0])) and bool(_ID_RE.fullmatch(rest[1]))
        )
    if method == "DELETE":
        return (
            confirmed and len(rest) == 2 and rest[0] == "issue"
            and bool(_ISSUE_REF_RE.fullmatch(rest[1]))
        )
    if method != "POST":
        return False
    if rest in (["issue"], ["search", "jql"], ["search"]):
        return True
    if len(rest) == 3 and rest[0] == "issue" and _ISSUE_REF_RE.fullmatch(rest[1]):
        if rest[2] in ("comment", "attachments"):
            return True
        if rest[2] == "transitions":
            return isinstance(body, Mapping) and not ("fields" in body or "update" in body)
    return False


def classify_route(
    *,
    client: str,
    method: str,
    target: str,
    base_url: str,
    api_prefix: str,
    headers: Mapping[str, str] | None = None,
    body: Any = None,
    confirmed_delete: bool = False,
) -> str:
    """Return ``ROUTE_ALLOWED`` or ``ROUTE_GUARDED`` for a non-GET request.

    ``client`` is ``"jira"`` or ``"jira-align"``; ``target`` is a path or absolute URL.
    Raises ``GuardRefused`` for a method-override header, another origin, or a path that
    holds ``..``, ``;`` or an encoded separator after decoding (AC30, AC33).
    """

    if client not in ("jira", "jira-align"):
        raise GuardRefused("unknown client")
    for name in headers or {}:
        if str(name).lower() in _OVERRIDE_HEADERS:
            raise GuardRefused("method-override headers are refused")
    segments, _ = _split_target(target, base_url)
    ok = _allowlisted(client, method.upper(), segments, api_prefix, body, confirmed_delete)
    return ROUTE_ALLOWED if ok else ROUTE_GUARDED


def guard_request(
    *,
    client: str,
    method: str,
    target: str,
    base_url: str,
    api_prefix: str,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, Any] | None = None,
    body: Any = None,
    confirmed_delete: bool = False,
    verified_plan: VerifiedPlan | None = None,
) -> None:
    """Raise ``GuardRefused`` unless the request is a read, allowlisted, or the plan's write.

    Call from the client's request chokepoint after the auth and intake-policy checks.
    """

    if method.upper() in _READ_METHODS:
        return
    route = classify_route(
        client=client, method=method, target=target, base_url=base_url,
        api_prefix=api_prefix, headers=headers, body=body, confirmed_delete=confirmed_delete,
    )
    if route == ROUTE_ALLOWED:
        return
    if verified_plan is None:
        raise GuardRefused("write refused: no verified plan; run plan-update and approve it first")
    url = target
    if params:
        url = f"{target}{'&' if '?' in target else '?'}" + "&".join(
            f"{k}={v}" for k, v in params.items()
        )
    if not verified_plan.authorizes(method, url, body):
        raise GuardRefused("write refused: request differs from the verified plan's write")


# --- file storage (AC15-AC19) ---------------------------------------------------------------


def _agentbundle_dir() -> Path:
    return Path.home() / ".agentbundle"


def state_root() -> Path:
    """Return ``~/.agentbundle/tracker-write-back`` (home resolved like the credential store)."""

    return _agentbundle_dir() / "tracker-write-back"


def _is_link(st: os.stat_result) -> bool:
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & reparse)


def _check_folder(path: Path, *, private: bool) -> None:
    """Refuse a link, a non-folder, or (when ``private``) a folder others can reach."""

    st = os.lstat(path)
    if _is_link(st):
        raise GuardRefused("a symlink or reparse point sits in the tracker-write-back path")
    if not stat.S_ISDIR(st.st_mode):
        raise GuardRefused("a tracker-write-back path component is not a folder")
    if private and hasattr(os, "getuid"):
        if st.st_uid != os.getuid():
            raise GuardRefused("a tracker-write-back folder is not owned by the current user")
        if st.st_mode & 0o077:
            raise GuardRefused("a tracker-write-back folder grants group or other access")


def _ensure_private_dir(path: Path) -> None:
    """Create or check every folder from ``~/.agentbundle`` down to ``path``."""

    top = _agentbundle_dir()
    root = state_root()
    try:
        rel = path.relative_to(top)
    except ValueError as exc:
        raise GuardRefused("path is outside ~/.agentbundle") from exc
    chain = [top]
    for part in rel.parts:
        chain.append(chain[-1] / part)
    for folder in chain:
        private = folder == root or root in folder.parents
        try:
            try:
                _check_folder(folder, private=private)
            except FileNotFoundError:
                folder.mkdir(mode=0o700)
                if private:
                    folder.chmod(0o700)
                _check_folder(folder, private=private)
        except OSError as exc:
            raise GuardRefused(f"cannot prepare folder: {exc.strerror}") from exc


def preflight_folders(base_url: str, plan_path: str | Path | None = None) -> None:
    """Check every existing folder from ``tracker-write-back`` down, before any request.

    Covers the state root, the instance folder, its ``plans`` folder and its ``prior``
    folder, plus (when ``plan_path`` is given: a plan or a prior-value record) each folder
    from the root down to that file's own folder: each must be a real folder owned by the
    current user with no group or other access. A folder that does not exist yet is
    created, and checked, by the write path.
    """

    top = _agentbundle_dir()
    try:
        _check_folder(top, private=False)
    except OSError as exc:
        raise GuardRefused(f"cannot inspect folder: {exc.strerror}") from exc
    folders = [
        state_root().joinpath(*part)
        for part in ((), (instance_slug(base_url),), (instance_slug(base_url), "plans"),
                     (instance_slug(base_url), "prior"))
    ]
    if plan_path is not None:
        absolute = Path(os.path.normpath(Path.cwd() / plan_path))
        folders += [f for f in reversed(absolute.parents) if state_root() in (f, *f.parents)]
    for folder in folders:
        try:
            _check_folder(folder, private=True)
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise GuardRefused(f"cannot inspect folder: {exc.strerror}") from exc


def _assert_confined(path: Path) -> Path:
    """Return the absolute path if it is under the root with no link below ``~/.agentbundle``."""

    absolute = Path(os.path.normpath(Path.cwd() / path))
    root = state_root()
    top = _agentbundle_dir()
    if root not in absolute.parents:
        raise GuardRefused("file is outside ~/.agentbundle/tracker-write-back/")
    walker = top
    for part in absolute.relative_to(top).parts:
        try:
            if _is_link(os.lstat(walker)):
                raise GuardRefused("a symlink or reparse point sits in the file path")
        except OSError as exc:
            raise GuardRefused("file path cannot be inspected") from exc
        walker = walker / part
    try:
        if _is_link(os.lstat(absolute)):
            raise GuardRefused("a symlink or reparse point sits in the file path")
    except OSError as exc:
        raise GuardRefused("file cannot be inspected") from exc
    if root.resolve() not in absolute.resolve().parents:
        raise GuardRefused("file resolves outside ~/.agentbundle/tracker-write-back/")
    return absolute


def _create_exclusive(directory: Path, stem: str, suffix: str, text: str) -> Path:
    """Create ``stem[-n]suffix`` exclusively at mode 0600; a name clash gets a unique suffix."""

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_BINARY", 0)
    data = text.encode("utf-8")
    for n in range(_MAX_NAME_CLASH):
        path = directory / (f"{stem}{suffix}" if n == 0 else f"{stem}-{n}{suffix}")
        try:
            fd = os.open(path, flags, 0o600)
        except FileExistsError:
            continue
        except OSError as exc:
            raise GuardRefused(f"cannot create file: {exc.strerror}") from exc
        try:
            with os.fdopen(fd, "wb") as handle:
                if hasattr(os, "fchmod"):
                    os.fchmod(handle.fileno(), 0o600)
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            path.unlink(missing_ok=True)
            raise GuardRefused(f"cannot write file: {exc.strerror}") from exc
        return path
    raise GuardRefused("too many files with the same name")


def _safe_stem(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9.-]", "-", text)


def write_plan_file(plan: Plan) -> Path:
    """Write the plan under ``<root>/<instance-slug>/plans/`` and return its path.

    Name is ``<target>-<digest prefix>[-n].json``; creation is exclusive at mode 0600.
    """

    directory = state_root() / instance_slug(plan.base_url) / "plans"
    _ensure_private_dir(directory)
    stem = f"{_safe_stem(plan.target)}-{plan.digest[:12]}"
    return _create_exclusive(directory, stem, ".json", json.dumps(plan_to_obj(plan), indent=2))


def build_prior_record(
    *,
    identifier: str,
    plan_digest: str,
    entries: Sequence[tuple[str, Any, Any]],
    record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a prior-value record from (field, old, written) triples.

    ``identifier`` is the Jira key, or ``resource/id`` for Jira Align, where ``record``
    is the full record as read (AC14, AC41).
    """

    obj: dict[str, Any] = {
        "identifier": identifier,
        "plan_digest": plan_digest,
        "entries": [{"field": f, "old": old, "written": new} for f, old, new in entries],
    }
    if record is not None:
        obj["record"] = dict(record)
    return obj


def write_prior_then_call(
    base_url: str,
    record: Mapping[str, Any],
    write: Callable[[], T],
    *,
    announce: Callable[[Path], None] | None = None,
) -> tuple[Path, T]:
    """Save the prior-value record, announce its path, then run ``write``.

    The record is on disk before ``write`` runs; if it cannot be written, ``GuardRefused``
    is raised and ``write`` never runs (AC12, AC13, AC22). Returns (record path, result).
    """

    identifier = record.get("identifier")
    if not isinstance(identifier, str):
        raise GuardRefused("record has no identifier")
    directory = state_root() / instance_slug(base_url) / "prior"
    _ensure_private_dir(directory)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    path = _create_exclusive(
        directory, f"{stamp}-{_safe_stem(identifier)}", ".json", json.dumps(record, indent=2)
    )
    if announce is not None:
        announce(path)
    return path, write()


# --- loaders (AC20) ----------------------------------------------------------------------------


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise GuardRefused("file holds a duplicate key")
        out[key] = value
    return out


def _reject_constant(name: str) -> Any:
    raise GuardRefused("file holds a non-finite number")


def _reject_nonfinite(value: Any) -> None:
    """Reject non-finite floats anywhere in parsed JSON, including numeric overflow."""
    if isinstance(value, float) and not math.isfinite(value):
        raise GuardRefused("file holds a non-finite number")
    if isinstance(value, dict):
        for child in value.values():
            _reject_nonfinite(child)
    elif isinstance(value, list):
        for child in value:
            _reject_nonfinite(child)


def _read_json(path: Path) -> Any:
    """Read a confined regular file and parse it as strict JSON."""

    confined = _assert_confined(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(confined, flags)
        with os.fdopen(fd, "rb") as handle:
            st = os.fstat(handle.fileno())
            if not stat.S_ISREG(st.st_mode) or st.st_size > _MAX_FILE_BYTES:
                raise GuardRefused("file is not a regular file of acceptable size")
            raw = handle.read(_MAX_FILE_BYTES + 1)
        obj = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicates,
            parse_constant=_reject_constant,
        )
        _reject_nonfinite(obj)
        return obj
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        if isinstance(exc, GuardRefused):
            raise
        raise GuardRefused("file cannot be read as JSON") from exc


def load_plan(path: str | Path, *, base_url: str) -> Plan:
    """Load a plan file: confined, closed field set, typed, identifier alphabet, base URL match.

    Raises ``GuardRefused`` on any violation. The stored digest is not trusted here;
    ``verify_plan`` recomputes it.
    """

    obj = _read_json(Path(path))
    if not isinstance(obj, dict) or set(obj) != _PLAN_KEYS:
        raise GuardRefused("plan file fields differ from the closed plan field set")
    version = obj["contract_version"]
    if type(version) is not int or version != CONTRACT_VERSION:
        raise GuardRefused("plan contract_version is not supported")
    flavor, target, method = obj["flavor"], obj["target"], obj["method"]
    if not all(isinstance(v, str) for v in (flavor, target, method, obj["base_url"])):
        raise GuardRefused("plan flavor, target, method and base_url must be strings")
    if flavor not in _FLAVORS:
        raise GuardRefused("plan flavor is unknown")
    _check_method(flavor, method)
    _check_target(flavor, target)
    if normalize_base_url(obj["base_url"]) != normalize_base_url(base_url):
        raise GuardRefused("plan base_url differs from the configured base URL")
    if type(obj["notify"]) is not bool:
        raise GuardRefused("plan notify must be a boolean")
    if not isinstance(obj["digest"], str) or not _DIGEST_RE.fullmatch(obj["digest"]):
        raise GuardRefused("plan digest is not a 64-character lowercase hex string")
    raw_fields = obj["fields"]
    if not isinstance(raw_fields, dict) or not raw_fields:
        raise GuardRefused("plan fields must be a non-empty object")
    fields: dict[str, FieldPlan] = {}
    for name, spec in raw_fields.items():
        if not isinstance(spec, dict) or set(spec) != _FIELD_KEYS:
            raise GuardRefused("a plan field differs from the closed field entry set")
        if not isinstance(spec["disposition"], str):
            raise GuardRefused("a plan field disposition must be a string")
        fp = FieldPlan(spec["current"], spec["proposed"], spec["disposition"])
        _check_field_plan(flavor, name, fp)
        fields[name] = fp
    return Plan(
        target, flavor, normalize_base_url(obj["base_url"]), method, obj["notify"], fields,
        obj["digest"], version,
    )


def _valid_identifier(identifier: str) -> bool:
    return bool(_JIRA_KEY_RE.fullmatch(identifier) or _ALIGN_TARGET_RE.fullmatch(identifier))


def load_record(path: str | Path) -> dict[str, Any]:
    """Load a prior-value record: confined, closed field set, typed, identifier alphabet."""

    obj = _read_json(Path(path))
    if not isinstance(obj, dict):
        raise GuardRefused("record file is not an object")
    ident = obj.get("identifier")
    if not isinstance(ident, str) or not _valid_identifier(ident):
        raise GuardRefused("record identifier is outside the identifier alphabet")
    allowed = _RECORD_KEYS_ALIGN if _ALIGN_TARGET_RE.fullmatch(ident) else _RECORD_KEYS
    if not _RECORD_KEYS <= set(obj) <= allowed:
        raise GuardRefused("record fields differ from the closed record field set")
    if not isinstance(obj["plan_digest"], str) or not _DIGEST_RE.fullmatch(obj["plan_digest"]):
        raise GuardRefused("record plan_digest is not a 64-character lowercase hex string")
    if "record" in obj and not isinstance(obj["record"], dict):
        raise GuardRefused("record full-record copy must be an object")
    entries = obj["entries"]
    if not isinstance(entries, list) or not entries:
        raise GuardRefused("record entries must be a non-empty list")
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != _ENTRY_KEYS:
            raise GuardRefused("a record entry differs from the closed entry set")
        if not isinstance(entry["field"], str) or not entry["field"]:
            raise GuardRefused("a record entry field name must be a non-empty string")
    return obj


def build_undo_plan(
    record: Mapping[str, Any],
    *,
    flavor: str,
    base_url: str,
    method: str,
    notify: bool,
) -> Plan:
    """Turn a loaded record into a plan replacing each field with its saved old value.

    The plan's current value is the record's written value, so the stale check refuses
    the undo when the remote no longer equals what was written (AC43, AC44).
    """

    fields = {
        e["field"]: {"current": e["written"], "proposed": e["old"], "disposition": "replace"}
        for e in record["entries"]
    }
    return build_plan(
        target=record["identifier"], flavor=flavor, base_url=base_url, method=method,
        notify=notify, fields=fields,
    )


# --- preview (AC2, AC4, AC5) ---------------------------------------------------


def render_preview(plan: Plan) -> str:
    """Render the read-only preview; ends with the single ``digest:`` line.

    Tracker text is encoded and indented, so only the final line starts with ``digest:``.
    """

    lines = [
        f"target: {encode_text(plan.target, keep_newline=False)}",
        f"flavor: {plan.flavor}",
        f"base_url: {encode_text(plan.base_url, keep_newline=False)}",
        f"method: {plan.method}",
        f"notify: {str(plan.notify).lower()}",
    ]
    for name, f in plan.fields.items():
        lines.append(f"field: {encode_text(name, keep_newline=False)}")
        lines.append(f"  disposition: {f.disposition}")
        lines.append("  current:")
        lines.append(_indent(_render_value(f.current)))
        lines.append("  proposed:")
        lines.append(_indent(_render_value(f.proposed)))
        if f.disposition == "append":
            written = resolve_field_value(plan.flavor, f)
            lines.append("  after write (lines marked + are added; others already exist):"
                         if plan.flavor == FLAVOR_CLOUD else
                         "  after write (existing text, then the label and added text):")
            lines.append(_indent(_render_after_write(plan.flavor, f.current, written)))
        is_adf = isinstance(f.current, dict) or isinstance(f.proposed, dict)
        if f.disposition == "replace" and plan.flavor == FLAVOR_CLOUD and is_adf:
            report = lossy_report(f.current, f.proposed)
            nodes = ", ".join(encode_text(t, keep_newline=False) for t in report.node_types)
            marks = ", ".join(encode_text(t, keep_newline=False) for t in report.mark_types)
            lines.append(f"  drops node types: {nodes or 'none'}")
            lines.append(f"  drops mark types: {marks or 'none'}")
            if report.blocking:
                lines.append("  lossy: needs --allow-lossy")
    lines.append(digest_line(plan.digest))
    return "\n".join(lines)
