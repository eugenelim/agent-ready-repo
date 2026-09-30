#!/usr/bin/env python3
"""Publish one model-authored explain-diff HTML draft after static validation."""

from __future__ import annotations

import argparse
import base64
import contextlib
import datetime as dt
import hashlib
import os
import re
import secrets
import stat
import sys
import tempfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path, PurePath

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

MAX_INPUT_BYTES = 1_048_576
CSP_MARKER = "EXPLAIN_DIFF_CSP"
RUNTIME_MARKER = "EXPLAIN_DIFF_RUNTIME"
QUIZ_RUNTIME = (
    "(()=>{for(const q of document.querySelectorAll('[data-quiz-question]')){"
    "const b=q.querySelector('[data-quiz-check]'),"
    "f=q.querySelector('[data-quiz-feedback]'),r=q.dataset.quizRationale;"
    "b.addEventListener('click',()=>{"
    "const s=q.querySelector('input[type=\"radio\"]:checked'),"
    "ok=!!s&&s.dataset.correct==='true';"
    "q.dataset.state=s?(ok?'correct':'incorrect'):'unanswered';"
    "f.textContent=s?(ok?'Correct. ':'Not yet. ')+r:"
    "'Choose an answer first.';});}})();"
)
ROLES = {"background", "intuition", "code", "quiz"}
EVIDENCE = {"observed", "inference", "unknown"}
VOID_TAGS = {"br", "hr", "input", "meta", "wbr"}
ALLOWED_TAGS = {
    "html",
    "head",
    "title",
    "meta",
    "style",
    "body",
    "a",
    "header",
    "footer",
    "nav",
    "main",
    "section",
    "article",
    "aside",
    "div",
    "span",
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "pre",
    "code",
    "blockquote",
    "ul",
    "ol",
    "li",
    "dl",
    "dt",
    "dd",
    "table",
    "caption",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "th",
    "td",
    "details",
    "summary",
    "strong",
    "em",
    "small",
    "mark",
    "kbd",
    "samp",
    "fieldset",
    "legend",
    "label",
    "input",
    "button",
    "br",
    "hr",
    "time",
}
GLOBAL_ATTRS = {
    "id",
    "class",
    "aria-label",
    "aria-labelledby",
    "aria-describedby",
    "aria-live",
    "aria-current",
    "role",
    "data-explain-role",
    "data-evidence",
}
TAG_ATTRS = {
    "html": {"lang"},
    "meta": {"charset", "name", "content"},
    "a": {"href"},
    "th": {"scope", "colspan", "rowspan"},
    "td": {"colspan", "rowspan"},
    "time": {"datetime"},
    "input": {"type", "name", "value", "data-correct"},
    "button": {"type", "data-quiz-check"},
    "fieldset": {"data-quiz-question", "data-quiz-rationale"},
    "p": {"data-quiz-feedback"},
    "pre": {"tabindex"},
}
DISALLOWED_TAGS = {
    "script",
    "form",
    "svg",
    "img",
    "picture",
    "source",
    "video",
    "audio",
    "canvas",
    "iframe",
    "object",
    "embed",
    "base",
    "link",
}
SENSITIVE_PATTERNS = (
    (
        "credential",
        re.compile(
            r"\b(?:bearer|token|api[_-]?key|password|secret)\s+[-._~+/=A-Za-z0-9]{12,}",
            re.I,
        ),
    ),
    (
        "credential",
        re.compile(
            r"\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|"
            r"secret|client[_-]?secret)\b\s*(?::|=)\s*[\"']?[-._~+/=A-Za-z0-9]{12,}",
            re.I,
        ),
    ),
    ("credential", re.compile(r"\b(?:ghp|sk|xox[baprs])_[A-Za-z0-9_=-]{16,}\b", re.I)),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("user-home path", re.compile(r"(?<![A-Za-z0-9._-])/(?:Users|home)/[^/\s\"'<>]+/[^\s\"'<>]*")),
)
HIGH_ENTROPY = re.compile(r"\b[A-Za-z0-9+/=_-]{32,}\b")
FORBIDDEN_CSS = re.compile(
    r"\\|url\s*\(|@import\b|@font-face\b|image-set\s*\(|expression\s*\(|-moz-binding\b",
    re.I,
)
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_IS_POSIX = os.name == "posix"


class PublishError(ValueError):
    """A concise publisher refusal safe to show without a traceback."""


@dataclass(frozen=True)
class OutputTarget:
    """A resolved final HTML path."""

    root: Path
    path: Path


@dataclass
class QuizState:
    """Native quiz controls observed in one fieldset."""

    legends: int = 0
    radios: int = 0
    correct: int = 0
    checks: int = 0
    feedback: int = 0
    has_rationale: bool = False
    label_depth: int = 0
    radio_names: set[str] = field(default_factory=set)


class DraftParser(HTMLParser):
    """Collect enough structure to enforce the static publishing contract."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.ids: set[str] = set()
        self.duplicate_id = False
        self.fragment_links: list[str] = []
        self.tags: dict[str, int] = {}
        self.title_text: list[str] = []
        self.in_title = False
        self.style_text: list[str] = []
        self.in_style = False
        self.html_attrs: dict[str, str] = {}
        self.headings: list[int] = []
        self.roles: list[tuple[str, str | None]] = []
        self.toc_links: set[str] = set()
        self.inside_nav = 0
        self.invalid_html = False
        self.disallowed_html = False
        self.marker_errors: list[str] = []
        self.csp_markers = 0
        self.runtime_markers = 0
        self.head_meaningful: list[str] = []
        self.body_meaningful: list[str] = []
        self.in_head = 0
        self.in_body = 0
        self.in_pre = 0
        self.in_code = 0
        self.pre_has_code_stack: list[bool] = []
        self.code_in_pre = 0
        self.quiz_stack: list[QuizState] = []
        self.quizzes: list[QuizState] = []

    def handle_decl(self, decl: str) -> None:
        if decl.lower() != "doctype html":
            self.invalid_html = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_names = [name.lower() for name, _value in attrs]
        if len(attr_names) != len(set(attr_names)):
            self.disallowed_html = True
        attrs_dict = {
            name: value
            for name, (_original, value) in zip(attr_names, attrs, strict=True)
        }
        self._meaningful_element(tag)
        if tag in DISALLOWED_TAGS:
            self.disallowed_html = True
        if tag not in ALLOWED_TAGS:
            self.disallowed_html = True
        self.tags[tag] = self.tags.get(tag, 0) + 1
        self._validate_attrs(tag, attrs_dict)
        if tag == "html":
            self.html_attrs = {name: value or "" for name, value in attrs_dict.items()}
        if tag == "head":
            self.in_head += 1
        elif tag == "body":
            self.in_body += 1
        elif tag == "title":
            self.in_title = True
        elif tag == "style":
            self.in_style = True
        elif tag == "nav":
            self.inside_nav += 1
        elif tag == "pre":
            self.in_pre += 1
            self.pre_has_code_stack.append(False)
        elif tag == "code":
            if self.in_pre:
                self.pre_has_code_stack[-1] = True
                self.code_in_pre += 1
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.headings.append(int(tag[1]))
        element_id = attrs_dict.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_id = True
            self.ids.add(element_id)
        role = attrs_dict.get("data-explain-role")
        if role is not None:
            self.roles.append((role, element_id))
        if (
            tag == "a"
            and self.inside_nav
            and (href := attrs_dict.get("href"))
            and href.startswith("#")
        ):
            self.toc_links.add(href[1:])
        self._track_quiz_start(tag, attrs_dict)
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        elif tag == "style":
            self.in_style = False
        elif tag == "nav":
            self.inside_nav = max(0, self.inside_nav - 1)
        elif tag == "pre":
            self.in_pre = max(0, self.in_pre - 1)
            if not self.pre_has_code_stack.pop() if self.pre_has_code_stack else True:
                self.invalid_html = True
        elif tag == "code" and self.code_in_pre:
            self.code_in_pre -= 1
        elif tag == "head":
            self.in_head = max(0, self.in_head - 1)
        elif tag == "body":
            self.in_body = max(0, self.in_body - 1)
        self._track_quiz_end(tag)
        if tag in self.stack:
            while self.stack:
                popped = self.stack.pop()
                if popped == tag:
                    break

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if self.in_head and data.strip():
            self.head_meaningful.append("text")
        if self.in_body and data.strip():
            self.body_meaningful.append("text")
        if self.in_title:
            self.title_text.append(data)
        if self.in_style:
            self.style_text.append(data)

    def handle_comment(self, data: str) -> None:
        stripped = data.strip()
        if stripped == CSP_MARKER:
            self.csp_markers += 1
            self.head_meaningful.append(CSP_MARKER)
            self._reject_marker_context()
            if not self.in_head:
                self.marker_errors.append("placeholder")
        elif stripped == RUNTIME_MARKER:
            self.runtime_markers += 1
            self.body_meaningful.append(RUNTIME_MARKER)
            self._reject_marker_context()
            if not self.in_body:
                self.marker_errors.append("placeholder")
        elif self.in_head and stripped:
            self.head_meaningful.append("comment")
        elif self.in_body and stripped:
            self.body_meaningful.append("comment")

    def _meaningful_element(self, tag: str) -> None:
        if tag in {"head", "body"}:
            return
        if self.in_head:
            self.head_meaningful.append(tag)
        if self.in_body:
            self.body_meaningful.append(tag)

    def _validate_attrs(self, tag: str, attrs: dict[str, str | None]) -> None:
        for name, value in attrs.items():
            if name.startswith("on") or name == "style":
                self.disallowed_html = True
            if name not in GLOBAL_ATTRS and name not in TAG_ATTRS.get(tag, set()):
                self.disallowed_html = True
            if value is None:
                value = ""
            if name == "href":
                if not value.startswith("#") or len(value) == 1:
                    self.disallowed_html = True
                else:
                    self.fragment_links.append(value[1:])
            elif name in {"src", "action", "poster"}:
                self.disallowed_html = True
            elif (
                (name == "data-explain-role" and value not in ROLES)
                or (name == "data-evidence" and value not in EVIDENCE)
                or (name == "aria-live" and value not in {"polite", "assertive", "off"})
                or (tag == "input" and name == "type" and value != "radio")
                or (tag == "button" and name == "type" and value != "button")
                or (name == "data-correct" and value != "true")
            ):
                self.invalid_html = True

    def _reject_marker_context(self) -> None:
        if self.in_pre or self.in_code or any(
            tag in {"main", "section", "article"} for tag in self.stack
        ):
            self.marker_errors.append("placeholder")

    def _track_quiz_start(self, tag: str, attrs: dict[str, str | None]) -> None:
        if tag == "fieldset" and "data-quiz-question" in attrs:
            rationale = attrs.get("data-quiz-rationale")
            self.quiz_stack.append(
                QuizState(has_rationale=bool(rationale and rationale.strip()))
            )
            return
        if not self.quiz_stack:
            return
        quiz = self.quiz_stack[-1]
        if tag == "legend":
            quiz.legends += 1
        elif tag == "label":
            quiz.label_depth += 1
        elif tag == "input" and attrs.get("type") == "radio":
            if quiz.label_depth < 1:
                self.invalid_html = True
            quiz.radios += 1
            name = attrs.get("name")
            if name is None or not name.strip():
                self.invalid_html = True
            else:
                quiz.radio_names.add(name)
            if attrs.get("data-correct") == "true":
                quiz.correct += 1
        elif tag == "button" and "data-quiz-check" in attrs and attrs.get("type") == "button":
            quiz.checks += 1
        elif tag == "p" and "data-quiz-feedback" in attrs and attrs.get("aria-live") == "polite":
            quiz.feedback += 1

    def _track_quiz_end(self, tag: str) -> None:
        if not self.quiz_stack:
            return
        quiz = self.quiz_stack[-1]
        if tag == "label":
            quiz.label_depth = max(0, quiz.label_depth - 1)
        elif tag == "fieldset":
            self.quizzes.append(self.quiz_stack.pop())


def main(argv: list[str] | None = None) -> int:
    """Run the publisher CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-root")
    parser.add_argument("--output-name")
    args = parser.parse_args(argv)

    try:
        input_path = _resolve_input(Path(args.input_root), args.input)
        draft = _load_draft(input_path)
        _validate_draft(draft)
        target = _resolve_output(args.output_root, args.output_name)
        final = _inject_trusted_bytes(draft)
        _publish_atomically(target, final.encode("utf-8"))
    except PublishError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"error: {error.strerror or error}", file=sys.stderr)
        return 2

    print(str(target.path))
    return 0


def _load_draft(path: Path) -> str:
    size = path.stat().st_size
    if size > MAX_INPUT_BYTES:
        raise PublishError("input exceeds 1,048,576 bytes")
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PublishError("input must be UTF-8") from error


def _validate_draft(draft: str) -> None:
    _reject_sensitive_literals(draft)
    if not draft.lstrip().lower().startswith("<!doctype html>"):
        raise PublishError("invalid document: missing HTML5 doctype")
    if (
        draft.count(f"<!-- {CSP_MARKER} -->") != 1
        or draft.count(f"<!-- {RUNTIME_MARKER} -->") != 1
    ):
        raise PublishError("placeholder must appear exactly once")
    parser = DraftParser()
    try:
        parser.feed(draft)
        parser.close()
    except Exception as error:
        raise PublishError("invalid document: malformed HTML") from error
    if parser.disallowed_html:
        raise PublishError("disallowed HTML capability")
    if parser.marker_errors or parser.csp_markers != 1 or parser.runtime_markers != 1:
        raise PublishError("placeholder is missing or misplaced")
    if not parser.head_meaningful or parser.head_meaningful[0] != CSP_MARKER:
        raise PublishError("placeholder must be the first meaningful head child")
    if not parser.body_meaningful or parser.body_meaningful[-1] != RUNTIME_MARKER:
        raise PublishError("placeholder must be the final meaningful body child")
    _validate_document_structure(parser)
    _validate_css("".join(parser.style_text))
    _validate_quiz(parser)


def _validate_document_structure(parser: DraftParser) -> None:
    if parser.invalid_html:
        raise PublishError("invalid document structure")
    if (
        parser.tags.get("html") != 1
        or parser.tags.get("head") != 1
        or parser.tags.get("body") != 1
    ):
        raise PublishError("invalid document: expected one html, head, and body")
    if "lang" not in parser.html_attrs or not parser.html_attrs["lang"].strip():
        raise PublishError("invalid document: html lang is required")
    if parser.tags.get("main") != 1 or parser.tags.get("h1") != 1:
        raise PublishError("invalid document: expected one main and h1")
    if not "".join(parser.title_text).strip():
        raise PublishError("invalid document: title is required")
    if parser.duplicate_id:
        raise PublishError("invalid document: ids must be unique")
    if any(link not in parser.ids for link in parser.fragment_links):
        raise PublishError("invalid document: fragment link target is missing")
    if not parser.headings or parser.headings[0] != 1:
        raise PublishError("invalid document: heading order must start at h1")
    for previous, current in zip(parser.headings, parser.headings[1:], strict=False):
        if current - previous > 1:
            raise PublishError("invalid document: heading levels must not skip")
    role_names = [role for role, _element_id in parser.roles]
    if set(role_names) != ROLES or len(role_names) != 4:
        raise PublishError("invalid document: teaching roles are required")
    role_ids = {element_id for _role, element_id in parser.roles if element_id}
    if len(role_ids) != 4 or not role_ids.issubset(parser.toc_links):
        raise PublishError("invalid document: table of contents must link teaching roles")
    if parser.tags.get("pre", 0) and parser.code_in_pre < 0:
        raise PublishError("invalid document: code blocks must use pre > code")


def _validate_css(css: str) -> None:
    inspected = CSS_COMMENT.sub("", css)
    if FORBIDDEN_CSS.search(inspected):
        raise PublishError("disallowed CSS capability")
    lowered = inspected.lower()
    required = (
        ":focus-visible",
        "prefers-reduced-motion",
        "max-width",
        "pre",
        "white-space",
    )
    if not all(token in lowered for token in required):
        raise PublishError("required CSS floor is missing")
    if not re.search(r"white-space\s*:\s*pre\b", lowered):
        raise PublishError("required CSS floor is missing")


def _validate_quiz(parser: DraftParser) -> None:
    if len(parser.quizzes) != 5:
        raise PublishError("required quiz must contain five questions")
    for quiz in parser.quizzes:
        if (
            quiz.legends != 1
            or quiz.radios != 4
            or quiz.correct != 1
            or quiz.checks != 1
            or quiz.feedback != 1
            or not quiz.has_rationale
            or len(quiz.radio_names) != 1
        ):
            raise PublishError("required quiz controls are incomplete")
    names = [next(iter(quiz.radio_names)) for quiz in parser.quizzes]
    if len(set(names)) != len(names):
        raise PublishError("required quiz radio groups must be distinct")


def _reject_sensitive_literals(text: str) -> None:
    for category, pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            raise PublishError(f"sensitive {category} is not allowed")
    for match in HIGH_ENTROPY.finditer(text):
        token = match.group(0)
        if _looks_high_entropy(token):
            raise PublishError("sensitive high-entropy token is not allowed")


def _looks_high_entropy(token: str) -> bool:
    classes = sum(
        (
            any(char.islower() for char in token),
            any(char.isupper() for char in token),
            any(char.isdigit() for char in token),
            any(char in "+/=_-" for char in token),
        )
    )
    return classes >= 3 and len(set(token)) >= 16


def _inject_trusted_bytes(draft: str) -> str:
    script_hash = base64.b64encode(
        hashlib.sha256(QUIZ_RUNTIME.encode("utf-8")).digest()
    ).decode("ascii")
    csp = (
        "default-src 'none'; "
        "base-uri 'none'; "
        "form-action 'none'; "
        "object-src 'none'; "
        "frame-src 'none'; "
        "img-src 'none'; "
        "connect-src 'none'; "
        "font-src 'none'; "
        "media-src 'none'; "
        "worker-src 'none'; "
        "style-src 'unsafe-inline'; "
        f"script-src 'sha256-{script_hash}'"
    )
    csp_meta = f'<meta http-equiv="Content-Security-Policy" content="{csp}">'
    rendered = draft.replace(f"<!-- {CSP_MARKER} -->", csp_meta, 1)
    return rendered.replace(f"<!-- {RUNTIME_MARKER} -->", f"<script>{QUIZ_RUNTIME}</script>", 1)


def _resolve_input(root: Path, relative: str) -> Path:
    """Resolve an input path under a declared root without following a leaf symlink."""

    root = root.resolve(strict=True)
    if not root.is_dir():
        raise PublishError("input root must be a directory")
    if _unsafe_relative(relative):
        raise PublishError("input path must be a safe relative path")
    candidate = root / relative
    try:
        metadata = candidate.lstat()
    except FileNotFoundError as error:
        raise PublishError("input file does not exist") from error
    if stat.S_ISLNK(metadata.st_mode):
        raise PublishError("input path must not be a symlink")
    if not stat.S_ISREG(metadata.st_mode):
        raise PublishError("input path must be a regular file")
    resolved = candidate.resolve(strict=True)
    if not _is_relative_to(resolved, root):
        raise PublishError("input path escapes input root")
    return resolved


def _resolve_output(output_root: str | None, output_name: str | None) -> OutputTarget:
    """Resolve a destination directory and one safe output filename."""

    if output_root:
        root = Path(output_root).resolve(strict=True)
    else:
        root = Path(tempfile.gettempdir()).resolve(strict=True)
    if not root.is_dir():
        raise PublishError("output root must be an existing directory")
    if output_name is None:
        today = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
        output_name = f"explain-diff-{today}-{secrets.token_hex(8)}.html"
    if _unsafe_filename(output_name):
        raise PublishError("output name must be a single safe filename")
    target = root / output_name
    if target.exists() or target.is_symlink():
        raise PublishError("output file already exists")
    if target.parent.resolve(strict=True) != root:
        raise PublishError("output path escapes output root")
    return OutputTarget(root=root, path=target)


def _publish_atomically(target: OutputTarget, content: bytes) -> None:
    """Publish bytes through an owner-scoped sibling temporary file."""

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".explain-diff-",
        suffix=".tmp",
        dir=target.root,
    )
    temporary = Path(temporary_name)
    published = False
    try:
        if _IS_POSIX:
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if _IS_POSIX and stat.S_IMODE(temporary.stat().st_mode) != 0o600:
            raise PublishError("temporary file permissions are not owner-scoped")
        os.link(temporary, target.path)
        published = True
    except FileExistsError as error:
        raise PublishError("output file already exists") from error
    finally:
        with contextlib.suppress(OSError):
            temporary.unlink()
    if published and _IS_POSIX and stat.S_IMODE(target.path.stat().st_mode) != 0o600:
        with contextlib.suppress(OSError):
            target.path.unlink()
        raise PublishError("output file permissions are not owner-scoped")


def _unsafe_relative(value: str) -> bool:
    path = PurePath(value)
    return (
        not value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    )


def _unsafe_filename(value: str) -> bool:
    path = PurePath(value)
    return (
        not value
        or path.is_absolute()
        or len(path.parts) != 1
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
    )


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
