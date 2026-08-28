"""Pure source-admission and rendering helpers for repository intents."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol
from urllib.parse import SplitResult, urlsplit, urlunsplit


class NormalizedIntakeLike(Protocol):
    """Validated intake fields used by the intent renderer."""

    content: dict[str, list[str]]
    constraints: dict[str, object]
    source: object


class NormalizedSourceLike(Protocol):
    """Validated normalized source fields used by the intent renderer."""

    mode: str
    locator: str
    revision: str
    tracker_profile: dict[str, str] | None


@dataclass(frozen=True)
class IntentAdmission:
    """A rendered intent and its identity-preserving repository target."""

    target: str
    content: str
    authority_mode: str


class IntentAdmissionError(ValueError):
    """Stable refusal raised before any filesystem effect."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


_TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "minimal-intent.md"
_EMAIL_RE = re.compile(r"\b[^\s/@]+@[^\s/@]+\.[^\s/@]+\b")
_SECRET_RE = re.compile(
    r"(?i)(?:^|[/;])(?:password|passwd|pwd|secret|api[_-]?key|"
    r"access[_-]?token|token)(?:[:=]|/)[^/?#]+"
)
_INSTRUCTION_RE = re.compile(
    r"(?i)\b(?:ignore (?:all |any )?(?:previous|prior) instructions|"
    r"mark (?:this|it) (?:ready|accepted|approved)|dispatch this|"
    r"change (?:the )?(?:rules|scope|tools|permissions|reviewer|verdict)|"
    r"write the raw payload|allowed-tools|system prompt)\b"
)
_PERSONAL_ABSOLUTE_RE = re.compile(
    r"(?i)^(?:/(?:users|home|private)/|[a-z]:[/\\]users[/\\])"
)
_ABSOLUTE_LOCAL_RE = re.compile(r"(?i)^(?:/|[a-z]:[/\\]|\\\\)")
_TRANSFER_MODES = {"chat-only", "personal", "personal-vault", "vault"}


def repository_intent_target(*, slug: str, existing_path: str | None = None) -> str:
    """Preserve an existing intent identity or return the default new target."""

    candidate = existing_path or f"docs/product/intents/{slug}.md"
    if not _is_safe_repository_path(candidate):
        raise IntentAdmissionError("unsafe_repository_destination")
    return candidate


def minimize_source_locator(locator: str) -> str:
    """Minimize one opaque locator without dereferencing or filesystem access."""

    if not isinstance(locator, str) or not locator or any(
        character in locator for character in ("\x00", "\r", "\n")
    ):
        raise IntentAdmissionError("unsafe_source_locator")
    if _PERSONAL_ABSOLUTE_RE.match(locator):
        raise IntentAdmissionError("personal_source_locator")
    if _is_unsafe_local_locator(locator):
        raise IntentAdmissionError("unsafe_source_locator")

    try:
        parsed = urlsplit(locator)
    except ValueError as error:
        raise IntentAdmissionError("unsafe_source_locator") from error

    if parsed.scheme:
        minimized = _minimize_url(parsed)
    else:
        minimized = locator.split("?", 1)[0].split("#", 1)[0]

    minimized = minimized.strip()
    if not minimized or minimized in {"/", "."}:
        raise IntentAdmissionError("source_identity_lost")
    if _EMAIL_RE.search(minimized) or _SECRET_RE.search(minimized):
        raise IntentAdmissionError("sensitive_source_locator")
    if _PERSONAL_ABSOLUTE_RE.match(minimized):
        raise IntentAdmissionError("personal_source_locator")
    return minimized


def render_minimal_intent(
    *,
    intake: NormalizedIntakeLike,
    title: str,
    level: str | None = None,
    authority_transferred: bool = False,
) -> str:
    """Render the minimum repository-intent contract from validated fields."""

    source = intake.source
    mode = _inline(str(getattr(source, "mode", "unknown")))
    if mode in _TRANSFER_MODES and not authority_transferred:
        raise IntentAdmissionError("authority_transfer_required")

    content = intake.content
    outcome = _first(content, "outcomes", "Not yet stated")
    boundary = _items(content, "boundary", "Not yet bounded")
    owner = _items(content, "owner", "Not yet assigned")
    unresolved = _items(content, "unresolved_questions", "None recorded")
    projection = _items(content, "projection", "Not yet selected")
    locator = minimize_source_locator(str(getattr(source, "locator", "")))
    revision = _inline(str(getattr(source, "revision", "unknown")))

    optional_level = f"- **Level:** {_inline(level)}" if level else ""
    optional_sections: list[str] = []
    if content.get("named_gaps"):
        optional_sections.append(
            "## Opportunity\n\n" + _first(content, "named_gaps", "")
        )
    if content.get("assumptions"):
        optional_sections.append(
            "## Assumptions\n\n" + _items(content, "assumptions", "")
        )

    authority = "transferred-to-repository" if mode in _TRANSFER_MODES else mode
    replacements = {
        "<intent title>": _inline(title),
        "<optional level>": optional_level,
        "<bounded outcome>": outcome,
        "<bounded boundary>": boundary,
        "<bounded owner>": owner,
        "<bounded unresolved questions>": unresolved,
        "<bounded projection>": projection,
        "<optional context>": "\n\n".join(optional_sections)
        + ("\n\n" if optional_sections else ""),
        "<source mode>": mode,
        "<safe source locator>": locator,
        "<source revision>": revision,
        "<source authority>": authority,
    }
    template = _TEMPLATE.read_text(encoding="utf-8")
    template_tokens = set(re.findall(r"<[^>\r\n]+>", template))
    if template_tokens != set(replacements):
        raise RuntimeError("minimal intent template contract is incomplete")
    token_pattern = re.compile("|".join(re.escape(token) for token in replacements))
    template = token_pattern.sub(lambda match: replacements[match.group(0)], template)

    if mode == "tracker-origin":
        template += "\n\n" + _render_tracker_source_authority(
            source, locator=locator, revision=revision
        )
    return template


def admit_repository_intent(
    *,
    intake: NormalizedIntakeLike,
    title: str,
    slug: str,
    existing_path: str | None = None,
    destination_confirmed: bool = False,
    authority_transferred: bool = False,
    level: str | None = None,
) -> IntentAdmission:
    """Prepare one admission; callers retain the confined write boundary."""

    mode = str(getattr(intake.source, "mode", "unknown"))
    if mode in _TRANSFER_MODES and not destination_confirmed:
        raise IntentAdmissionError("repository_destination_confirmation_required")
    target = repository_intent_target(slug=slug, existing_path=existing_path)
    rendered = render_minimal_intent(
        intake=intake,
        title=title,
        level=level,
        authority_transferred=authority_transferred,
    )
    return IntentAdmission(target=target, content=rendered, authority_mode=mode)


def _minimize_url(parsed: SplitResult) -> str:
    """Remove URL credentials, query, and fragment while retaining identity."""

    if parsed.scheme.lower() == "file" or not parsed.hostname:
        raise IntentAdmissionError("unsafe_source_locator")
    if parsed.path in {"", "/"} and (parsed.query or parsed.fragment):
        raise IntentAdmissionError("source_identity_lost")
    host = parsed.hostname
    try:
        port = parsed.port
    except ValueError as error:
        raise IntentAdmissionError("unsafe_source_locator") from error
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    netloc = f"{host}:{port}" if port is not None else host
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "/", "", ""))


def _is_unsafe_local_locator(value: str) -> bool:
    """Reject local path shapes lexically without touching the filesystem."""

    return bool(_ABSOLUTE_LOCAL_RE.match(value)) or "\\" in value or any(
        part in {".", ".."} for part in value.split("/")
    )


def _is_safe_repository_path(value: str) -> bool:
    """Apply the lexical half of repository confinement before a real write."""

    if (
        not isinstance(value, str)
        or not value
        or value.startswith("/")
        or "\\" in value
        or re.match(r"^[A-Za-z]:", value)
    ):
        return False
    parts = PurePosixPath(value).parts
    return bool(parts) and all(part not in {"", ".", ".."} for part in parts)


def _first(content: dict[str, list[str]], key: str, fallback: str) -> str:
    values = content.get(key, [])
    return _inline(values[0]) if values else fallback


def _items(content: dict[str, list[str]], key: str, fallback: str) -> str:
    values = content.get(key, [])
    return "\n".join(f"- {_inline(value)}" for value in values) if values else fallback


def _render_tracker_source_authority(
    source: NormalizedSourceLike, *, locator: str, revision: str
) -> str:
    """Render the closed authority fence only for tracker-origin artifacts."""

    return "\n".join(
        (
            "```toml source-authority",
            'contract_version = "source-authority.v1"',
            'mode = "tracker-origin"',
            f"source_ref = {json.dumps(locator, ensure_ascii=False)}",
            f"source_revision = {json.dumps(revision, ensure_ascii=False)}",
            "",
            "[owned_fields]",
            "```",
        )
    )


def _inline(value: str) -> str:
    """Make one untrusted value structurally inert inside Markdown."""

    rendered = re.sub(r"\s+", " ", str(value)).strip()
    if _INSTRUCTION_RE.search(rendered):
        return "[omitted untrusted instruction]"
    rendered = _EMAIL_RE.sub("[redacted-personal-data]", rendered)
    rendered = re.sub(
        r"(?i)\b(password|passwd|pwd|secret|api[_ -]?key|"
        r"access[_ -]?token|token)\s*[:=]\s*\S+",
        lambda match: f"{match.group(1)}=[redacted]",
        rendered,
    )
    if re.match(r"(?:`|~){3,}", rendered):
        rendered = "\\" + rendered
    return rendered
