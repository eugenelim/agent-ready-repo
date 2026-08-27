"""Parser and input validation for the OKF authoring compiler."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import tomllib
import unicodedata
from collections.abc import Callable, Iterable, Mapping
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from yaml.tokens import (
    BlockEndToken,
    BlockMappingStartToken,
    BlockSequenceStartToken,
    FlowMappingEndToken,
    FlowMappingStartToken,
    FlowSequenceEndToken,
    FlowSequenceStartToken,
)

SUPPORTED_PROFILE = "agentbundle-okf/v1"
PROFILE_OKF_VERSION = {SUPPORTED_PROFILE: "0.2"}
DIAGNOSTIC_ORDER = {
    "OKF001": 1,
    "OKF002": 2,
    "OKF003": 3,
    "OKF004": 4,
    "OKF005": 5,
    "OKF006": 6,
    "OKF007": 7,
    "OKF008": 8,
    "OKF009": 9,
    "OKF010": 10,
    "OKF011": 11,
    "OKF012": 12,
}
DEFAULT_LIMITS = {
    "file_count": 4096,
    "concept_count": 2000,
    "total_bytes": 32 * 1024 * 1024,
    "directory_depth": 16,
    "markdown_bytes": 2 * 1024 * 1024,
    "frontmatter_bytes": 64 * 1024,
}
PACK_TOML_MAX_BYTES = 64 * 1024
PRIOR_MANIFEST_MAX_BYTES = 4 * 1024 * 1024
MANAGED_OUTPUT_MAX_BYTES = 32 * 1024 * 1024
PRIOR_MANIFEST_INTEGER_MAX_DIGITS = 128
INDEX_DISPLAY_INPUT_MAX_CHARS = 200
_SAFE_DIR_FD_SUPPORTED = all(
    function in os.supports_dir_fd
    for function in (os.open, os.mkdir, os.rename, os.stat, os.unlink)
)
_WINDOWS_DEVICE = re.compile(r"^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)", re.IGNORECASE)
# The shapes GFM turns into a link with no delimiter around them. `ftp://` is one
# of them on cmark-gfm — the renderer this metadata is actually read through —
# even though micromark leaves it inert, so verifying against one renderer alone
# is not enough. A bare address is another, so matching `mailto:` alone left the
# common case open.
_REMOTE_SCHEME = re.compile(r"(?:(?:https?|ftp)://|www\.|mailto:)", re.IGNORECASE)
# Anchored on `@`, deliberately. Leading with the local part
# (`[A-Za-z0-9._%+-]+@`) made `re.search` retry at every offset and backtrack the
# greedy class looking for an `@` that is not there: 16 000 dotted characters cost
# 2.7s and the frontmatter cap is 65 536 bytes, so one value was ~44s of CPU. A
# one-character lookbehind does the same job in one linear pass, and every
# repetition is bounded.
#
# The final label must end in a letter, which is what cmark-gfm actually
# linkifies: it links `x@y.z` and `a_b@c-d.io` but leaves `Rev@1.2`,
# `Deploy@v1.2` and `tag@10.0.0.1` inert. Matching more than the renderer does
# would refuse a legal version string such as `Rev@1.2` and fail the compile.
_REMOTE_ADDRESS = re.compile(
    r"(?<=[A-Za-z0-9._%+-])@(?:[A-Za-z0-9_-]{1,63}\.){1,8}[A-Za-z0-9_-]{0,62}[A-Za-z]\b"
)
_UNSAFE_METADATA_KEYS = {
    "attester",
    "executor",
    "runtime",
    "script",
    "scripts",
}
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
MANAGED_INDEX_MARKER = "<!-- agentbundle-managed: profile=agentbundle-okf/v1 kind=okf-index -->"
ROUTER_HANDOFF_MARKER = "<!-- agentbundle-okf: router-handoff=author-owned -->"
ASSET_ROOT = Path(__file__).resolve().parent.parent / "assets"
# A path acts as syntax two ways inside a CommonMark link destination: it can
# break out structurally, or it can form a character reference the renderer
# resolves. Both classes are encoded; everything else, including non-ASCII, is
# left literal so the destination stays the path a reader can open.
_LINK_DESTINATION_UNSAFE = re.compile(
    r"""[\x00-\x20\x7f-\x9f\u2028\u2029"#%&'();<>\\^`{|}]"""
)


def _control_class_escapes() -> dict[str, str]:
    """Escape every C0 control, DEL, C1 control, and U+2028/U+2029.

    Covering the class rather than listing its members is deliberate. An
    enumeration named seven separators and still omitted three that
    ``str.splitlines()`` breaks on, so one entry could read as two to a
    plain-text reader while the list looked complete. The destination encoder
    covers the same range, so both legs of a rendered line agree.
    """
    friendly = {"\t": r"\t", "\n": r"\n", "\r": r"\r"}
    table = {
        chr(code_point): friendly.get(chr(code_point), f"\\x{code_point:02x}")
        for code_point in (*range(0x20), 0x7F, *range(0x80, 0xA0))
    }
    table["\u2028"] = r"\u2028"
    table["\u2029"] = r"\u2029"
    return table


_INDEX_DISPLAY_ESCAPES = str.maketrans(
    {
        "\\": r"\\",
        # C0 controls, DEL, C1 controls, and the Unicode line and paragraph
        # separators. Any of these lets one entry look like several, and a few
        # act below Markdown entirely: an escape sequence repaints a terminal,
        # and a NUL truncates a null-terminating reader.
        **_control_class_escapes(),
        # Link and autolink structure.
        "[": r"\[",
        "]": r"\]",
        "(": r"\(",
        ")": r"\)",
        "<": r"\<",
        ">": r"\>",
        # Code-span and emphasis delimiters. A backtick pair spanning two fields
        # swallows the entry's own destination; `*` and `_` distort the entry.
        "`": r"\`",
        "*": r"\*",
        "_": r"\_",
    }
)

# GFM linkifies a bare `www.` host and a `scheme://` URL with no surrounding
# Markdown at all, so a display value can render as a live link without
# containing a single delimiter. Escaping the one punctuation mark each trigger
# requires renders the same text and leaves the link inert.
#
# Escaping is only used for the triggers where it is *proven* to work. Checked
# against cmark-gfm, the renderer this output is read through, and micromark:
# `www\.`, `http\://`, `https\://` and `ftp\://` are all defused on both.
#
# A bare `a@b.tld` address is deliberately NOT here. cmark-gfm resolves character
# escapes into text before its autolink pass scans, so `a\@b.tld` still renders a
# live `mailto:` link — the escape is inert against the extension, and
# `a&#64;b.tld` bypasses it the same way. Escaping it would be theatre and would
# corrupt an ordinary `a@b` for nothing, so the address shape is refused instead:
# in frontmatter by `OKF009`, and in a path component by the path gate.
_AUTOLINK_TRIGGERS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(www)(\.)", re.IGNORECASE), r"\1\\\2"),
    (re.compile(r"(https?|ftp|mailto)(:)", re.IGNORECASE), r"\1\\\2"),
)


@dataclass(frozen=True)
class Diagnostic:
    """Stable parse diagnostic."""

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class Concept:
    """Parsed OKF concept discovery record."""

    path: str
    metadata: Mapping[str, Any]
    body: str


@dataclass(frozen=True)
class ValidationResult:
    """Result returned before any render/apply work is allowed."""

    diagnostics: tuple[Diagnostic, ...]
    okf_version: str | None
    concepts: tuple[Concept, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


@dataclass(frozen=True)
class RenderResult:
    """Pure render output for a selected OKF bundle."""

    diagnostics: tuple[Diagnostic, ...]
    files: Mapping[str, bytes]
    review_candidates: Mapping[str, str]


@dataclass(frozen=True)
class CompileResult:
    """Process-level compile/apply result."""

    exit_code: int
    diagnostics: tuple[Diagnostic, ...]
    stdout: str = ""
    stderr: str = ""


class _BoundedReadError(ValueError):
    """A file exceeded its explicit descriptor-read byte budget."""


def validate_okf_bundle(
    bundle_root: Path,
    *,
    profile: str,
    declared_paths: Iterable[str] = (),
    resource_overrides: Mapping[str, int] | None = None,
    on_ready_to_generate: Callable[[], None] | None = None,
    reparse_markers: Iterable[Path] = (),
    resolution_failures: Iterable[Path] = (),
    before_open: Callable[[Path], None] | None = None,
) -> ValidationResult:
    """Validate an OKF bundle's parser/input-safety contract."""

    expected_version = PROFILE_OKF_VERSION.get(profile)
    diagnostics: list[Diagnostic] = []
    if expected_version is None:
        diagnostics.append(_diagnostic("OKF001", ".", "unsupported OKF profile"))

    root = bundle_root.resolve(strict=False)
    reparse_paths = {_normalize_host_path(path) for path in reparse_markers}
    resolution_failure_paths = {_normalize_host_path(path) for path in resolution_failures}
    limits = DEFAULT_LIMITS | dict(resource_overrides or {})

    declared_path_list = list(declared_paths)
    for declared in declared_path_list:
        if not _is_safe_relative_path(declared):
            diagnostics.append(_diagnostic("OKF004", declared, "unsafe declared path"))

    records = _scan_regular_files(
        root,
        limits=limits,
        reparse_paths=reparse_paths,
        resolution_failure_paths=resolution_failure_paths,
        before_open=before_open,
    )
    diagnostics.extend(records.diagnostics)
    diagnostics.extend(_resource_diagnostics(records.files, limits))
    if any(item.code == "OKF005" for item in diagnostics):
        return ValidationResult(
            diagnostics=tuple(_sort_diagnostics(diagnostics)),
            okf_version=None,
            concepts=(),
        )

    index_record = next(
        (record for record in records.files if record.relative_path == "index.md"),
        None,
    )
    okf_version: str | None = None
    if index_record is None:
        diagnostics.append(_diagnostic("OKF011", "index.md", "root index is missing"))
    else:
        metadata = _parse_frontmatter(index_record)
        diagnostics.extend(metadata.diagnostics)
        okf_version = metadata.data.get("okf_version") if isinstance(metadata.data, dict) else None
        if not isinstance(okf_version, str) or okf_version != expected_version:
            diagnostics.append(
                _diagnostic("OKF002", "index.md", "root OKF version conflicts with active profile")
            )

    concepts: list[Concept] = []
    for record in records.files:
        if (
            not record.relative_path.startswith("concepts/")
            or not record.relative_path.endswith(".md")
        ):
            continue
        parsed = _parse_frontmatter(record)
        diagnostics.extend(parsed.diagnostics)
        if parsed.diagnostics:
            continue
        if not isinstance(parsed.data, dict):
            diagnostics.append(
                _diagnostic("OKF003", record.relative_path, "frontmatter must be an object")
            )
            continue
        diagnostics.extend(_metadata_diagnostics(record.relative_path, parsed.data))
        if parsed.data.get("status") not in (None, "Active", "Deprecated"):
            diagnostics.append(
                _diagnostic(
                    "OKF003",
                    record.relative_path,
                    "unsupported concept lifecycle status",
                )
            )
        concepts.append(Concept(path=record.relative_path, metadata=parsed.data, body=parsed.body))

    diagnostics.extend(
        _collision_diagnostics(
            [record.relative_path for record in records.files] + declared_path_list
        )
    )
    sorted_diagnostics = _sort_diagnostics(diagnostics)
    if sorted_diagnostics:
        return ValidationResult(
            diagnostics=tuple(sorted_diagnostics),
            okf_version=okf_version,
            concepts=tuple(concepts),
        )

    if on_ready_to_generate is not None:
        on_ready_to_generate()
    return ValidationResult(diagnostics=(), okf_version=okf_version, concepts=tuple(concepts))


def render_okf_bundle(
    bundle_root: Path,
    *,
    bundle_id: str,
    router_skill: str,
    projected_concepts: Mapping[str, str],
    provider_capability: Mapping[str, Any] | None = None,
) -> RenderResult:
    """Render deterministic router, procedure Skills, references, and manifest bytes."""

    validation = validate_okf_bundle(bundle_root, profile=SUPPORTED_PROFILE)
    if validation.diagnostics:
        return RenderResult(diagnostics=validation.diagnostics, files={}, review_candidates={})

    root = bundle_root.resolve(strict=False)
    records = _scan_regular_files(
        root,
        limits=DEFAULT_LIMITS,
        reparse_paths=set(),
        resolution_failure_paths=set(),
        before_open=None,
    )
    record_map = {record.relative_path: record for record in records.files}
    parsed = _parsed_records(records.files)
    diagnostics: list[Diagnostic] = []
    files: dict[str, bytes] = {}
    review_candidates: dict[str, str] = {}

    for concept in parsed.values():
        extension = concept.metadata.get("x-agentbundle")
        if extension is not None:
            diagnostics.extend(_agentbundle_extension_diagnostics(concept.path, extension))
    if diagnostics:
        return RenderResult(
            diagnostics=tuple(_sort_diagnostics(diagnostics)),
            files={},
            review_candidates={},
        )

    source_digest = _tree_digest({record.relative_path: record.data for record in records.files})
    indexes = _render_indexes(bundle_id, parsed)
    for relative_path, data in indexes.items():
        files[f"references/okf/{relative_path}"] = data

    for record in records.files:
        if record.relative_path in indexes:
            continue
        files[f"references/okf/{record.relative_path}"] = record.data

    router_template = (ASSET_ROOT / "router-wrapper.md").read_text(encoding="utf-8")
    router_description, provider_metadata = _provider_router_metadata(
        bundle_id,
        provider_capability,
    )
    files["SKILL.md"] = router_template.format(
        router_skill=router_skill,
        bundle_id=bundle_id,
        source_digest=source_digest,
        router_description=router_description,
        provider_metadata=provider_metadata,
    ).encode("utf-8")

    for concept_path, reviewed_digest in sorted(projected_concepts.items()):
        concept = parsed.get(concept_path)
        if concept is None or concept.metadata.get("status") == "Deprecated":
            diagnostics.append(
                _diagnostic("OKF007", concept_path, "projected concept is ineligible")
            )
            continue
        if concept.metadata.get("type") != "Playbook":
            diagnostics.append(
                _diagnostic("OKF007", concept_path, "projected concept must be a Playbook")
            )
            continue
        skill = _skill_projection(concept.metadata)
        if skill is None:
            diagnostics.append(_diagnostic("OKF007", concept_path, "missing x-agentbundle skill"))
            continue
        include_diagnostics = _include_diagnostics(record_map, tuple(skill.get("include", ())))
        if include_diagnostics:
            diagnostics.extend(include_diagnostics)
            continue
        instruction_section = skill["instruction-section"]
        instruction = _extract_instruction_section(concept.body, instruction_section)
        if instruction is None:
            diagnostics.append(
                _diagnostic("OKF007", concept_path, "instruction section is invalid")
            )
            continue
        candidate = _review_projection_digest_from_records(
            record_map,
            concept_path=concept_path,
            skill_name=skill["name"],
            activation_description=skill["description"],
            instruction_section=instruction_section,
            includes=tuple(skill.get("include", ())),
        )
        review_candidates[concept_path] = candidate
        if candidate != reviewed_digest:
            diagnostics.append(_diagnostic("OKF008", concept_path, "review digest mismatch"))
            continue
        diagnostics.extend(
            _accumulate_output_items(
                files,
                _render_procedure_skill(
                    record_map,
                    bundle_id=bundle_id,
                    concept_path=concept_path,
                    concept=concept,
                    skill=skill,
                    instruction_body=instruction,
                    review_digest=reviewed_digest,
                ),
            )
        )

    if diagnostics:
        return RenderResult(
            diagnostics=tuple(_sort_diagnostics(diagnostics)),
            files={},
            review_candidates=review_candidates,
        )

    manifest = _render_manifest(
        bundle_id=bundle_id,
        router_skill=router_skill,
        files=files,
        source_digest=source_digest,
    )
    files[".okf-generated.json"] = manifest
    return RenderResult(
        diagnostics=(),
        files=dict(sorted(files.items())),
        review_candidates=review_candidates,
    )


def compile_pack(
    root: Path,
    pack: str,
    *,
    check: bool,
    fail_after_operations: int | None = None,
) -> CompileResult:
    """Compile one pack's declared OKF bundles and optionally apply generated output."""

    catalogue = root.resolve(strict=False)
    packs_dir = catalogue / "packs"
    if not _is_pack_name(pack):
        return _compile_result(1, [_diagnostic("OKF001", f"packs/{pack}", "invalid pack name")])
    pack_path = packs_dir / pack
    if not pack_path.exists():
        return _compile_result(1, [_diagnostic("OKF001", f"packs/{pack}", "pack not found")])
    pack_boundary = _directory_boundary_diagnostic(
        packs_dir.resolve(strict=False),
        pack_path,
        f"packs/{pack}",
    )
    if pack_boundary is not None:
        return _compile_result(1, [pack_boundary])
    pack_dir = pack_path.resolve(strict=False)
    if pack_dir.parent != packs_dir.resolve(strict=False):
        return _compile_result(1, [_diagnostic("OKF001", f"packs/{pack}", "invalid pack path")])

    try:
        pack_bytes = _read_confined_regular_file(
            pack_dir,
            pack_dir / "pack.toml",
            max_bytes=PACK_TOML_MAX_BYTES,
        )
        okf = tomllib.loads(pack_bytes.decode("utf-8"))["pack"]["metadata"]["okf"]
    except (
        KeyError,
        IndexError,
        OSError,
        UnicodeDecodeError,
        ValueError,
        tomllib.TOMLDecodeError,
    ) as exc:
        return _compile_result(1, [_diagnostic("OKF001", f"packs/{pack}/pack.toml", str(exc))])

    profile_diagnostics = _pack_profile_diagnostics(okf, f"packs/{pack}/pack.toml")
    if profile_diagnostics:
        return _compile_result(1, profile_diagnostics)

    outputs: dict[str, bytes] = {}
    manifest_records: list[Mapping[str, Any]] = []
    router_skills: list[str] = []
    for bundle in sorted(
        okf["bundles"],
        key=lambda item: (
            _sort_path(item["id"]),
            _sort_path(item["path"]),
            _sort_path(item["router-skill"]),
        ),
    ):
        projected = {
            item["path"]: item["reviewed-projection-digest"]
            for item in bundle.get("projected-concepts", ())
        }
        render_args = {
            "bundle_id": bundle["id"],
            "router_skill": bundle["router-skill"],
            "projected_concepts": projected,
            "provider_capability": bundle.get("provider"),
        }
        bundle_root = pack_dir / bundle["path"]
        bundle_boundary = _bundle_root_boundary_diagnostic(
            pack_dir,
            bundle["path"],
        )
        if bundle_boundary is not None:
            return _compile_result(1, [bundle_boundary])
        first = render_okf_bundle(bundle_root, **render_args)
        second = render_okf_bundle(bundle_root, **render_args)
        if first.diagnostics:
            return _compile_result(1, first.diagnostics)
        if first.files != second.files:
            return _compile_result(
                2,
                [_diagnostic("OKF012", f"packs/{pack}", "repeated compile differed")],
            )

        bundle_outputs, output_diagnostics = _pack_outputs(
            first.files,
            router_skill=bundle["router-skill"],
        )
        if output_diagnostics:
            return _compile_result(1, output_diagnostics)
        bundle_manifest = json.loads(
            _pack_manifest(
                first.files[".okf-generated.json"],
                router_skill=bundle["router-skill"],
            )
        )
        collisions = [
            _diagnostic("OKF006", _display_path(pack_dir, relative_path), "output collision")
            for relative_path in bundle_outputs
            if relative_path in outputs
        ]
        if collisions:
            return _compile_result(1, collisions[:1])
        outputs.update(bundle_outputs)
        manifest_records.extend(bundle_manifest["managed"])
        router_skills.append(bundle["router-skill"])

    outputs[".okf-generated.json"] = _combined_pack_manifest(
        manifest_records,
        router_skills=router_skills,
    )
    prior_manifest, load_diagnostic = _load_prior_manifest(pack_dir)
    if load_diagnostic is not None:
        return _compile_result(1, [load_diagnostic])
    manifest_diagnostics = _prior_manifest_diagnostics(pack_dir, prior_manifest)
    if manifest_diagnostics:
        return _compile_result(1, manifest_diagnostics)

    handoff_paths = _router_handoff_paths(pack_dir, outputs, prior_manifest)
    if check:
        drift = _check_drift(pack_dir, outputs, prior_manifest, handoff_paths)
        if drift:
            return _compile_result(2, drift)
        return CompileResult(
            exit_code=0,
            diagnostics=(),
            stdout=f"OKF000 check clean packs/{pack}\n",
        )

    ownership = _ownership_diagnostics(pack_dir, outputs, prior_manifest, handoff_paths)
    if ownership:
        return _compile_result(1, ownership)
    apply_diagnostic = _apply_outputs_transactionally(
        pack_dir,
        outputs,
        prior_manifest,
        handoff_paths=handoff_paths,
        fail_after_operations=fail_after_operations,
    )
    if apply_diagnostic is not None:
        return _compile_result(1, [apply_diagnostic])
    return CompileResult(exit_code=0, diagnostics=(), stdout=f"OKF000 wrote packs/{pack}\n")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize strict canonical JSON for digests and manifests."""

    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def review_projection_digest(
    bundle_root: Path,
    *,
    concept_path: str,
    skill_name: str,
    activation_description: str,
    instruction_section: str,
    includes: tuple[str, ...],
) -> str:
    """Compute the reviewed projection digest for one concept Skill."""

    root = bundle_root.resolve(strict=False)
    scan = _scan_regular_files(
        root,
        limits=DEFAULT_LIMITS,
        reparse_paths=set(),
        resolution_failure_paths=set(),
        before_open=None,
    )
    if scan.diagnostics:
        raise ValueError(scan.diagnostics[0].message)
    records = {record.relative_path: record for record in scan.files}
    return _review_projection_digest_from_records(
        records,
        concept_path=concept_path,
        skill_name=skill_name,
        activation_description=activation_description,
        instruction_section=instruction_section,
        includes=includes,
    )


def _review_projection_digest_from_records(
    records: Mapping[str, _FileRecord],
    *,
    concept_path: str,
    skill_name: str,
    activation_description: str,
    instruction_section: str,
    includes: tuple[str, ...],
) -> str:
    concept_record = records.get(concept_path)
    if concept_record is None:
        raise ValueError(f"missing concept: {concept_path}")
    parsed = _parse_frontmatter(concept_record)
    instruction = _extract_instruction_section(parsed.body, instruction_section)
    if instruction is None:
        raise ValueError(f"invalid instruction section: {instruction_section}")
    include_entries = [
        {
            "path": include,
            "sha256": _bytes_digest(records[include].data),
        }
        for include in includes
    ]
    metadata = parsed.data if isinstance(parsed.data, Mapping) else {}
    tuple_value = {
        "activation_description": activation_description,
        "boundaries": metadata.get("boundaries", []),
        "compatibility": metadata.get("compatibility", ""),
        "concept_path": unicodedata.normalize("NFC", concept_path),
        "includes": include_entries,
        "instruction_section": instruction_section,
        "instruction_sha256": _bytes_digest(instruction.encode("utf-8")),
        "license": metadata.get("license", ""),
        "profile": SUPPORTED_PROFILE,
        "skill_name": skill_name,
        "template_sha256": _bytes_digest((ASSET_ROOT / "procedure-wrapper.md").read_bytes()),
    }
    return _bytes_digest(canonical_json_bytes(tuple_value))


@dataclass(frozen=True)
class _FileRecord:
    path: Path
    relative_path: str
    data: bytes
    mode: int


@dataclass(frozen=True)
class _ScanResult:
    files: tuple[_FileRecord, ...]
    diagnostics: tuple[Diagnostic, ...]


@dataclass(frozen=True)
class _ParsedFrontmatter:
    data: Any
    body: str
    diagnostics: tuple[Diagnostic, ...]


def _parsed_records(records: Iterable[_FileRecord]) -> dict[str, Concept]:
    parsed: dict[str, Concept] = {}
    for record in records:
        if (
            not record.relative_path.startswith("concepts/")
            or not record.relative_path.endswith(".md")
        ):
            continue
        frontmatter = _parse_frontmatter(record)
        if isinstance(frontmatter.data, Mapping):
            parsed[record.relative_path] = Concept(
                path=record.relative_path,
                metadata=frontmatter.data,
                body=frontmatter.body,
            )
    return parsed


def _utf8_safe(text: str) -> str:
    r"""Return `text` with any unpaired surrogate rendered as visible `\uXXXX`.

    Scope is the **index display** leg only. `yaml.safe_load` accepts a `\uD800`
    escape and hands back a lone surrogate, which would otherwise raise
    `UnicodeEncodeError` when the rendered index is encoded — a traceback
    carrying no `OKF0xx` line, breaking the diagnostic contract this compiler
    promises. Applying this to `title`/`status`/`type` closes that leg.

    The other two non-encodable legs are closed at their own gates rather than
    here: `_is_safe_relative_path` refuses a path that cannot be encoded, so it
    never reaches the directory scan or `_sort_path`, and `_metadata_diagnostics`
    refuses a non-encodable frontmatter value before it reaches the manifest and
    digest path. Both reuse existing diagnostic codes. The call in
    `_index_link_destination` remains defence in depth for a value arriving from
    elsewhere.

    `backslashreplace` rather than `replace`: it keeps the value legible and
    matches this compiler's existing convention of rendering `\r` and `\n`
    visibly instead of dropping them. The emitted backslash is then escaped by
    the display table, so the result stays inert. Substitution is deterministic,
    so a repeated compile still matches and `OKF012` cannot fire on it.
    """
    return text.encode("utf-8", "backslashreplace").decode("utf-8")


def _index_display_value(value: object) -> str:
    """Return bounded text escaped for a Markdown index display field.

    Order is load-bearing: cap the raw value, then normalize, then escape, then
    neutralize autolinks. Capping first keeps the bound on *input* characters as
    specified, and keeps both later expansions atomic — normalizing before the
    slice would let it cut a generated `\\uXXXX` sequence in half, and escaping
    before the slice would let it cut an escape pair. A surrogate is a single code
    point, so slicing the raw value cannot split one.

    Neutralizing last is a **fidelity** choice, not a safety one. Neutralizing
    first would still be safe — the table would double the added backslash to
    `\\\\`, which renders as a literal backslash between `www` and `.`, and both
    renderers require adjacency, so the trigger is dead either way. What
    neutralizing first costs is a visible backslash in the rendered text.
    """
    bounded = _utf8_safe(str(value)[:INDEX_DISPLAY_INPUT_MAX_CHARS])
    escaped = bounded.translate(_INDEX_DISPLAY_ESCAPES)
    for trigger, replacement in _AUTOLINK_TRIGGERS:
        escaped = trigger.sub(replacement, escaped)
    return escaped


def _index_link_destination(path: str) -> str:
    """Return a deterministic Markdown-safe destination for a source-relative path.

    The encoded set is the authority; this list is not a summary of it. Three
    classes are encoded:

    - *Structural* — C0/C1 controls, space, the Unicode line and paragraph
      separators, and ``" ( ) < > \\ | ``. These break or escape a CommonMark
      destination. The separators are covered here as well as in the display
      table so both legs of one rendered line agree on where it ends.
    - *Reference-forming* — ``&``, ``#``, ``;`` and ``%``. A renderer resolves
      character references *inside* a destination, which is what let a concept
      named ``..&#x2F;..&#x2F;SKILL.md`` render an attacker-chosen ``href``;
      ``%`` is encoded so an emitted escape can never be read as a literal one.
    - *RFC-3986-excluded* — ``'``, ``^``, ``` ` ```, ``{`` and ``}``. These are
      not security-relevant here: ``[t](don't.md)`` already produced a working
      ``href``. They are encoded for URL validity, and that trades literal
      fidelity for it — a legitimately named ``don't-panic.md`` is cited as
      ``don%27t-panic.md``.

    Letters, digits, ``- . _ ~``, ``/`` as the separator, ``! $ + , = @ [ ]``,
    and ``: * ?`` are left literal, as is all non-ASCII. Encoding the whole path
    instead was tried and rejected: it turned a legitimately named ``café.md``
    into ``caf%C3%A9.md``, a path no reader can open, for no security gain.

    ``:``, ``*`` and ``?`` staying literal is safe only because
    `_is_safe_relative_path` rejects all three in a path component. Without that
    gate a concept named ``javascript:alert(1).md`` would yield a live scheme URL
    for any renderer that does not sanitize schemes. Relaxing the gate therefore
    requires encoding them here; a test asserts the refusal so the two cannot
    drift.
    """
    return _LINK_DESTINATION_UNSAFE.sub(
        lambda match: "".join(f"%{byte:02X}" for byte in match.group().encode("utf-8")),
        _utf8_safe(path),
    )


def _render_indexes(bundle_id: str, concepts: Mapping[str, Concept]) -> dict[str, bytes]:
    active_concepts = {
        path: concept
        for path, concept in concepts.items()
        if concept.metadata.get("status") in (None, "Active", "Deprecated")
        and not concept.metadata.get("stale")
    }
    by_directory: dict[str, list[Concept]] = {}
    for path, concept in active_concepts.items():
        directory = str(PurePosixPath(path).parent)
        by_directory.setdefault("" if directory == "." else directory, []).append(concept)

    indexes: dict[str, bytes] = {}
    root_entries: list[tuple[str, str]] = []
    for directory, directory_concepts in sorted(by_directory.items()):
        if not directory:
            continue
        entries = []
        for concept in sorted(directory_concepts, key=lambda item: _sort_path(item.path)):
            title = _index_display_value(concept.metadata.get("title") or concept.path)
            status = _index_display_value(concept.metadata.get("status") or "Active")
            concept_type = _index_display_value(concept.metadata.get("type") or "Concept")
            filename = PurePosixPath(concept.path).name
            destination = _index_link_destination(filename)
            entries.append(f"- [{title}]({destination}) - {status} {concept_type}\n")
        if entries:
            name = PurePosixPath(directory).name
            heading = _index_display_value(name)
            indexes[f"{directory}/index.md"] = (
                f"{MANAGED_INDEX_MARKER}\n"
                f"# OKF index: {heading}\n\n"
                + "".join(entries)
            ).encode("utf-8")
            directory_text = _index_display_value(directory)
            directory_target = _index_link_destination(f"{directory}/index.md")
            root_entries.append(
                (
                    directory,
                    f"- [{directory_text}]({directory_target}) - {len(entries)} concepts\n",
                )
            )

    indexes["index.md"] = (
        "---\n"
        f'okf_version: "{PROFILE_OKF_VERSION[SUPPORTED_PROFILE]}"\n'
        "---\n"
        f"{MANAGED_INDEX_MARKER}\n"
        f"# OKF index: {bundle_id}\n\n"
        + "".join(
            entry
            for _, entry in sorted(root_entries, key=lambda item: _sort_path(item[0]))
        )
    ).encode("utf-8")
    return dict(sorted(indexes.items(), key=lambda item: _sort_path(item[0])))



def _skill_projection(metadata: Mapping[str, Any]) -> Mapping[str, Any] | None:
    extension = metadata.get("x-agentbundle")
    if not isinstance(extension, Mapping):
        return None
    if extension.get("profile") != SUPPORTED_PROFILE:
        return None
    skill = extension.get("skill")
    if not isinstance(skill, Mapping):
        return None
    required = ("name", "description", "instruction-section")
    if any(not isinstance(skill.get(key), str) or not skill.get(key) for key in required):
        return None
    include = skill.get("include", ())
    if include is None:
        include = ()
    if not isinstance(include, list) or not all(isinstance(item, str) for item in include):
        return None
    return {
        "name": skill["name"],
        "description": skill["description"],
        "instruction-section": skill["instruction-section"],
        "include": tuple(include),
    }


def _extract_instruction_section(body: str, identifier: str) -> str | None:
    if identifier != unicodedata.normalize("NFC", identifier) or identifier.strip() != identifier:
        return None
    lines = body.replace("\r\n", "\n").replace("\r", "\n").splitlines(keepends=True)
    matches: list[tuple[int, int]] = []
    in_fence = False
    fence_marker = ""
    fence_length = 0
    for index, line in enumerate(lines):
        stripped = line.rstrip("\n")
        fence = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence:
            marker = fence.group(1)
            char = marker[0]
            if not in_fence:
                in_fence = True
                fence_marker = char
                fence_length = len(marker)
            elif char == fence_marker and len(marker) >= fence_length:
                in_fence = False
            continue
        if in_fence:
            continue
        if stripped == f"## {identifier}":
            matches.append((index, index + 1))
    if len(matches) != 1:
        return None

    heading_index, start = matches[0]
    end = len(lines)
    in_fence = False
    fence_marker = ""
    fence_length = 0
    for index in range(heading_index + 1, len(lines)):
        stripped = lines[index].rstrip("\n")
        fence = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence:
            marker = fence.group(1)
            char = marker[0]
            if not in_fence:
                in_fence = True
                fence_marker = char
                fence_length = len(marker)
            elif char == fence_marker and len(marker) >= fence_length:
                in_fence = False
            continue
        if not in_fence and stripped.startswith(("# ", "## ")):
            end = index
            break
    section = "".join(lines[start:end]).strip()
    if not section:
        return None
    return section + "\n"


def _render_procedure_skill(
    records: Mapping[str, _FileRecord],
    *,
    bundle_id: str,
    concept_path: str,
    concept: Concept,
    skill: Mapping[str, Any],
    instruction_body: str,
    review_digest: str,
) -> list[tuple[str, bytes]]:
    source_digest = _bytes_digest(records[concept_path].data)
    include_list = "\n".join(
        f"- `references/{Path(include).name}`" for include in skill.get("include", ())
    )
    if not include_list:
        include_list = "- No copied includes."
    template = (ASSET_ROOT / "procedure-wrapper.md").read_text(encoding="utf-8")
    skill_name = str(skill["name"])
    files = [
        (
            f"skills/{skill_name}/SKILL.md",
            template.format(
                skill_name=skill_name,
                description=skill["description"],
                bundle_id=bundle_id,
                concept_path=concept_path,
                source_digest=source_digest,
                review_digest=review_digest,
                instruction_body=instruction_body.rstrip(),
                include_list=include_list,
            ).encode("utf-8"),
        )
    ]
    for include in skill.get("include", ()):
        files.append(
            (
                f"skills/{skill_name}/references/{Path(include).name}",
                records[include].data,
            )
        )
    return files


def _render_manifest(
    *,
    bundle_id: str,
    router_skill: str,
    files: Mapping[str, bytes],
    source_digest: str,
) -> bytes:
    managed = [
        {
            "digest": _bytes_digest(files["SKILL.md"]),
            "kind": "okf-router",
            "marker": "generated-by: compile-okf agentbundle-okf/v1",
            "output_path": "SKILL.md",
            "source_digest": source_digest,
            "source_path": f"okf/{bundle_id}",
        }
    ]
    index_items = [
        (path, data)
        for path, data in sorted(files.items(), key=lambda item: _sort_path(item[0]))
        if path.startswith("references/okf/") and path.endswith("index.md")
    ]
    procedure_items = [
        (path, data)
        for path, data in sorted(files.items(), key=lambda item: _sort_path(item[0]))
        if path.startswith("skills/") and path.endswith("/SKILL.md")
    ]
    reference_items = [
        (path, data)
        for path, data in sorted(files.items(), key=lambda item: _sort_path(item[0]))
        if path.startswith("references/okf/") and not path.endswith("index.md")
    ]
    procedure_reference_items = [
        (path, data)
        for path, data in sorted(files.items(), key=lambda item: _sort_path(item[0]))
        if path.startswith("skills/") and not path.endswith("/SKILL.md")
    ]
    for path, data in index_items[:1]:
        managed.append(
            {
                "digest": _bytes_digest(data),
                "kind": "okf-index",
                "marker": MANAGED_INDEX_MARKER,
                "output_path": path,
                "source_digest": source_digest,
                "source_path": f"okf/{bundle_id}/{path.removeprefix('references/okf/')}",
            }
        )
    for path, data in procedure_items:
        managed.append(
            {
                "digest": _bytes_digest(data),
                "kind": "okf-procedure-skill",
                "marker": "generated-by: compile-okf agentbundle-okf/v1",
                "output_path": path,
                "source_digest": source_digest,
                "source_path": f"okf/{bundle_id}",
            }
        )
    for path, data in index_items[1:]:
        managed.append(
            {
                "digest": _bytes_digest(data),
                "kind": "okf-index",
                "marker": MANAGED_INDEX_MARKER,
                "output_path": path,
                "source_digest": source_digest,
                "source_path": f"okf/{bundle_id}/{path.removeprefix('references/okf/')}",
            }
        )
    for path, data in reference_items:
        managed.append(
            {
                "digest": _bytes_digest(data),
                "kind": "okf-reference",
                "marker": "generated-by: compile-okf agentbundle-okf/v1",
                "output_path": path,
                "source_digest": _bytes_digest(data),
                "source_path": f"okf/{bundle_id}/{path.removeprefix('references/okf/')}",
            }
        )
    for path, data in procedure_reference_items:
        managed.append(
            {
                "digest": _bytes_digest(data),
                "kind": "okf-reference",
                "marker": "generated-by: compile-okf agentbundle-okf/v1",
                "output_path": path,
                "source_digest": _bytes_digest(data),
                "source_path": f"okf/{bundle_id}",
            }
        )
    return canonical_json_bytes(
        {
            "managed": managed,
            "profile": SUPPORTED_PROFILE,
            "router_skill": router_skill,
        }
    )


def _pack_outputs(
    rendered: Mapping[str, bytes],
    *,
    router_skill: str,
) -> tuple[dict[str, bytes], tuple[Diagnostic, ...]]:
    outputs: dict[str, bytes] = {}
    translated: list[tuple[str, bytes]] = []
    for path, data in rendered.items():
        if path == ".okf-generated.json":
            continue
        if path == "SKILL.md":
            translated.append((f".apm/skills/{router_skill}/SKILL.md", data))
        elif path.startswith("references/"):
            translated.append((f".apm/skills/{router_skill}/{path}", data))
        elif path.startswith("skills/"):
            translated.append((".apm/" + path, data))
    diagnostics = _accumulate_output_items(outputs, translated)
    return (
        dict(sorted(outputs.items(), key=lambda item: _sort_path(item[0]))),
        tuple(_sort_diagnostics(diagnostics)),
    )


def _accumulate_output_items(
    outputs: dict[str, bytes],
    items: Iterable[tuple[str, bytes]],
) -> list[Diagnostic]:
    """Add generated outputs without allowing exact or portable path collisions."""

    keys = {_output_collision_key(path) for path in outputs}
    diagnostics: list[Diagnostic] = []
    for path, data in items:
        key = _output_collision_key(path)
        if key in keys:
            diagnostics.append(_diagnostic("OKF006", path, "output collision"))
            continue
        keys.add(key)
        outputs[path] = data
    return diagnostics


def _output_collision_key(path: str) -> str:
    return unicodedata.normalize("NFC", path).casefold()


def _pack_manifest(rendered_manifest: bytes, *, router_skill: str) -> bytes:
    source_manifest = json.loads(rendered_manifest)
    managed = []
    for record in source_manifest.get("managed", ()):
        if not isinstance(record, Mapping):
            continue
        output_path = record.get("output_path")
        if not isinstance(output_path, str):
            continue
        translated = dict(record)
        translated["output_path"] = _pack_manifest_output_path(
            output_path,
            router_skill=router_skill,
        )
        managed.append(translated)
    return canonical_json_bytes(
        {
            "managed": sorted(managed, key=lambda item: _sort_path(item["output_path"])),
            "profile": source_manifest.get("profile", SUPPORTED_PROFILE),
            "router_skill": router_skill,
        }
    )


def _combined_pack_manifest(
    records: Iterable[Mapping[str, Any]],
    *,
    router_skills: list[str],
) -> bytes:
    payload: dict[str, Any] = {
        "managed": sorted(records, key=lambda item: _sort_path(str(item["output_path"]))),
        "profile": SUPPORTED_PROFILE,
    }
    if len(router_skills) == 1:
        payload["router_skill"] = router_skills[0]
    else:
        payload["router_skills"] = sorted(router_skills, key=_sort_path)
    return canonical_json_bytes(payload)


def _pack_manifest_output_path(path: str, *, router_skill: str) -> str:
    if path == "SKILL.md":
        return f".apm/skills/{router_skill}/SKILL.md"
    if path.startswith("references/"):
        return f".apm/skills/{router_skill}/{path}"
    if path.startswith("skills/"):
        return ".apm/" + path
    return path


def _load_prior_manifest(
    pack_dir: Path,
) -> tuple[Mapping[str, Any] | None, Diagnostic | None]:
    manifest_path = pack_dir / ".okf-generated.json"
    if not _path_lexists(manifest_path):
        return None, None
    try:
        payload = json.loads(
            _read_confined_regular_file(
                pack_dir,
                manifest_path,
                max_bytes=PRIOR_MANIFEST_MAX_BYTES,
            ).decode("utf-8"),
            parse_constant=_reject_json_constant,
            parse_float=_parse_strict_json_float,
            parse_int=_parse_bounded_json_int,
        )
    except (json.JSONDecodeError, OSError, UnicodeDecodeError, ValueError):
        return None, _diagnostic(
            "OKF010",
            _display_path(pack_dir, ".okf-generated.json"),
            "invalid or unsafe manifest",
        )
    if not isinstance(payload, Mapping):
        return None, _diagnostic(
            "OKF010",
            _display_path(pack_dir, ".okf-generated.json"),
            "invalid manifest",
        )
    return payload, None


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _parse_strict_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("non-finite JSON number is not allowed")
    return parsed


def _parse_bounded_json_int(value: str) -> int:
    digits = value.removeprefix("-")
    if len(digits) > PRIOR_MANIFEST_INTEGER_MAX_DIGITS:
        raise ValueError("JSON integer exceeds the manifest digit limit")
    return int(value)


def _manifest_records(manifest: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if not manifest:
        return {}
    records = manifest.get("managed", ())
    if not isinstance(records, list):
        return {}
    return {
        record["output_path"]: record
        for record in records
        if isinstance(record, Mapping) and isinstance(record.get("output_path"), str)
    }


def _prior_manifest_diagnostics(
    pack_dir: Path,
    manifest: Mapping[str, Any] | None,
) -> list[Diagnostic]:
    if manifest is None:
        return []
    records = manifest.get("managed", ())
    if not isinstance(records, list):
        return [
            _diagnostic(
                "OKF010",
                _display_path(pack_dir, ".okf-generated.json"),
                "invalid manifest",
            )
        ]

    diagnostics: list[Diagnostic] = []
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, Mapping):
            diagnostics.append(
                _diagnostic(
                    "OKF010",
                    _display_path(pack_dir, ".okf-generated.json"),
                    "invalid manifest",
                )
            )
            continue
        relative_path = record.get("output_path")
        if not isinstance(relative_path, str) or not _is_managed_output_path(relative_path):
            diagnostics.append(
                _diagnostic(
                    "OKF010",
                    _display_path(pack_dir, str(relative_path)),
                    "unsafe managed path",
                )
            )
            continue
        if relative_path in seen:
            diagnostics.append(
                _diagnostic(
                    "OKF010",
                    _display_path(pack_dir, relative_path),
                    "duplicate managed path",
                )
            )
            continue
        seen.add(relative_path)
        if not _is_sha256(record.get("digest")) or not _is_sha256(record.get("source_digest")):
            diagnostics.append(
                _diagnostic(
                    "OKF010",
                    _display_path(pack_dir, relative_path),
                    "invalid managed digest",
                )
            )
        path = pack_dir / relative_path
        if path.exists() and not path.is_file():
            diagnostics.append(
                _diagnostic(
                    "OKF010",
                    _display_path(pack_dir, relative_path),
                    "managed output is not a file",
                )
            )
    return diagnostics


def _router_handoff_paths(
    pack_dir: Path,
    outputs: Mapping[str, bytes],
    prior_manifest: Mapping[str, Any] | None,
) -> set[str]:
    """Return a former generated router that a renamed projection cedes to its author.

    A renamed router skill is the one safe transition from a generated router to
    a hand-authored one. The old router body becomes user-owned; every other
    prior generated file remains subject to the normal ownership and cleanup
    rules. This is derived solely from generic manifest fields, never from a
    caller, pack, or knowledge-domain name.
    """
    if prior_manifest is None:
        return set()
    rendered_manifest = outputs.get(".okf-generated.json")
    if rendered_manifest is None:
        return set()
    try:
        current_manifest = json.loads(rendered_manifest)
    except (TypeError, ValueError, json.JSONDecodeError):
        return set()
    prior_routers = _router_paths_by_source(prior_manifest)
    current_routers = _router_paths_by_source(current_manifest)
    handoffs: set[str] = set()
    for source_path, former_router in prior_routers.items():
        # A source that is no longer declared has been REMOVED, not renamed.
        # `.get()` returning None must not read as "the router changed", or
        # deleting a bundle would cede its managed output to the author instead
        # of cleaning it up. Handoff requires the source still present AND its
        # router actually different.
        current_router = current_routers.get(source_path)
        if current_router is None or current_router == former_router:
            continue
        prior_record = _manifest_records(prior_manifest).get(former_router)
        if prior_record is None or not _path_lexists(pack_dir / former_router):
            continue
        try:
            actual = _read_confined_regular_file(
                pack_dir,
                pack_dir / former_router,
                max_bytes=MANAGED_OUTPUT_MAX_BYTES,
            )
        except (OSError, ValueError):
            continue
        if ROUTER_HANDOFF_MARKER in actual.decode("utf-8", errors="replace") and (
            "generated-by: compile-okf agentbundle-okf/v1" not in actual.decode(
                "utf-8", errors="replace"
            )
        ):
            handoffs.add(former_router)
    return handoffs


def _router_paths_by_source(manifest: Mapping[str, Any]) -> dict[str, str]:
    """Map each generated router source path to its managed Skill output."""
    return {
        str(record["source_path"]): output_path
        for output_path, record in _manifest_records(manifest).items()
        if record.get("kind") == "okf-router"
        and isinstance(record.get("source_path"), str)
        and output_path.startswith(".apm/skills/")
        and output_path.endswith("/SKILL.md")
    }


def _check_drift(
    pack_dir: Path,
    outputs: Mapping[str, bytes],
    prior_manifest: Mapping[str, Any] | None,
    handoff_paths: set[str],
) -> list[Diagnostic]:
    for relative_path in _manifest_records(prior_manifest):
        if relative_path in outputs:
            continue
        if relative_path in handoff_paths:
            continue
        path = pack_dir / relative_path
        if not _path_lexists(path):
            continue
        boundary = _managed_output_path_diagnostic(
            pack_dir,
            relative_path,
            require_existing_file=True,
        )
        if boundary is not None:
            return [boundary]
        return [_diagnostic("OKF011", _display_path(pack_dir, relative_path), "stale output")]
    for relative_path, expected in sorted(outputs.items(), key=lambda item: _sort_path(item[0])):
        if relative_path == ".okf-generated.json" and not _path_lexists(
            pack_dir / relative_path
        ):
            return [_diagnostic("OKF011", _display_path(pack_dir, relative_path), "output drift")]
        path = pack_dir / relative_path
        exists = _path_lexists(path)
        boundary = _managed_output_path_diagnostic(
            pack_dir,
            relative_path,
            require_existing_file=exists,
        )
        if boundary is not None:
            return [_diagnostic("OKF011", boundary.path, "output drift")]
        if not exists:
            return [_diagnostic("OKF011", _display_path(pack_dir, relative_path), "output drift")]
        try:
            actual = _read_confined_regular_file(
                pack_dir,
                path,
                max_bytes=MANAGED_OUTPUT_MAX_BYTES,
            )
        except (OSError, ValueError):
            return [_diagnostic("OKF011", _display_path(pack_dir, relative_path), "output drift")]
        if actual != expected:
            return [_diagnostic("OKF011", _display_path(pack_dir, relative_path), "output drift")]
    return []


def _ownership_diagnostics(
    pack_dir: Path,
    outputs: Mapping[str, bytes],
    prior_manifest: Mapping[str, Any] | None,
    handoff_paths: set[str],
) -> list[Diagnostic]:
    records = _manifest_records(prior_manifest)
    directory_diagnostics = _managed_skill_directory_diagnostics(
        pack_dir, outputs, records, handoff_paths
    )
    if directory_diagnostics:
        return directory_diagnostics
    for relative_path in sorted(outputs, key=_sort_path):
        if relative_path == ".okf-generated.json":
            continue
        path = pack_dir / relative_path
        boundary = _managed_output_path_diagnostic(
            pack_dir,
            relative_path,
            require_existing_file=_path_lexists(path),
        )
        if boundary is not None:
            return [boundary]
        if not _path_lexists(path):
            continue
        record = records.get(relative_path)
        if record is None:
            return [
                _diagnostic("OKF010", _display_path(pack_dir, relative_path), "ownership conflict")
            ]
        try:
            data = _read_confined_regular_file(
                pack_dir,
                path,
                max_bytes=MANAGED_OUTPUT_MAX_BYTES,
            )
        except (OSError, ValueError):
            return [
                _diagnostic("OKF010", _display_path(pack_dir, relative_path), "ownership conflict")
            ]
        if _bytes_digest(data) != record.get("digest") or not _record_marker_matches(record, data):
            return [
                _diagnostic("OKF010", _display_path(pack_dir, relative_path), "ownership conflict")
            ]
    for relative_path, record in records.items():
        if relative_path in outputs:
            continue
        if relative_path in handoff_paths:
            continue
        path = pack_dir / relative_path
        boundary = _managed_output_path_diagnostic(
            pack_dir,
            relative_path,
            require_existing_file=_path_lexists(path),
        )
        if boundary is not None:
            return [boundary]
        if not _path_lexists(path):
            continue
        try:
            data = _read_confined_regular_file(
                pack_dir,
                path,
                max_bytes=MANAGED_OUTPUT_MAX_BYTES,
            )
        except (OSError, ValueError):
            return [
                _diagnostic("OKF010", _display_path(pack_dir, relative_path), "ownership conflict")
            ]
        if _bytes_digest(data) != record.get("digest") or not _record_marker_matches(record, data):
            return [
                _diagnostic("OKF010", _display_path(pack_dir, relative_path), "ownership conflict")
            ]
    return []


def _managed_skill_directory_diagnostics(
    pack_dir: Path,
    outputs: Mapping[str, bytes],
    records: Mapping[str, Mapping[str, Any]],
    handoff_paths: set[str],
) -> list[Diagnostic]:
    directories = {
        directory
        for directory in (_skill_directory(path) for path in records)
        if directory is not None
    }
    directories.update(
        directory
        for directory in (
            _skill_directory(path)
            for path in outputs
            if path != ".okf-generated.json"
        )
        if directory is not None and directory in {_skill_directory(path) for path in records}
    )
    ceded_directories = {
        directory for directory in (_skill_directory(path) for path in handoff_paths)
        if directory is not None
    }
    for relative_dir in sorted(ceded_directories, key=_sort_path):
        directory = pack_dir / relative_dir
        if not _path_lexists(directory):
            continue
        inventory, inventory_diagnostics = _inventory_paths_no_reparse(directory)
        if inventory_diagnostics:
            return [
                _diagnostic(
                    "OKF010", _display_path(pack_dir, relative_dir), "ownership conflict"
                )
            ]
        for descendant_path, info in inventory:
            relative_path = descendant_path.relative_to(pack_dir).as_posix()
            if stat.S_ISDIR(info.st_mode):
                continue
            if (
                relative_path.startswith(f"{relative_dir}/references/okf/")
                and relative_path not in records
            ):
                return [
                    _diagnostic(
                        "OKF010", _display_path(pack_dir, relative_path), "ownership conflict"
                    )
                ]
    directories.difference_update(ceded_directories)
    for relative_dir in sorted(directories, key=_sort_path):
        directory = pack_dir / relative_dir
        if not _path_lexists(directory):
            continue
        if not _is_real_directory(directory):
            return [
                _diagnostic("OKF010", _display_path(pack_dir, relative_dir), "ownership conflict")
            ]
        actual: set[str] = set()
        inventory, inventory_diagnostics = _inventory_paths_no_reparse(directory)
        if inventory_diagnostics:
            return [
                _diagnostic(
                    "OKF010",
                    _display_path(pack_dir, relative_dir),
                    "ownership conflict",
                )
            ]
        for descendant_path, info in inventory:
            relative_path = descendant_path.relative_to(pack_dir).as_posix()
            if stat.S_ISLNK(info.st_mode) or _is_reparse_stat(info):
                return [
                    _diagnostic(
                        "OKF010",
                        _display_path(pack_dir, relative_path),
                        "ownership conflict",
                    )
                ]
            if stat.S_ISDIR(info.st_mode):
                continue
            if not stat.S_ISREG(info.st_mode):
                return [
                    _diagnostic(
                        "OKF010",
                        _display_path(pack_dir, relative_path),
                        "ownership conflict",
                    )
                ]
            actual.add(relative_path)
        expected = {
            path
            for path, record in records.items()
            if (
                _skill_directory(path) == relative_dir
                and isinstance(record, Mapping)
                and path not in handoff_paths
            )
        }
        if actual - handoff_paths != expected:
            return [
                _diagnostic("OKF010", _display_path(pack_dir, relative_dir), "ownership conflict")
            ]
        for managed_path in sorted(expected, key=_sort_path):
            boundary = _managed_output_path_diagnostic(
                pack_dir,
                managed_path,
                require_existing_file=True,
            )
            if boundary is not None:
                return [boundary]
            try:
                data = _read_confined_regular_file(
                    pack_dir,
                    pack_dir / managed_path,
                    max_bytes=MANAGED_OUTPUT_MAX_BYTES,
                )
            except (OSError, ValueError):
                return [
                    _diagnostic(
                        "OKF010",
                        _display_path(pack_dir, managed_path),
                        "ownership conflict",
                    )
                ]
            record = records[managed_path]
            if _bytes_digest(data) != record.get("digest") or not _record_marker_matches(
                record, data
            ):
                return [
                    _diagnostic(
                        "OKF010",
                        _display_path(pack_dir, managed_path),
                        "ownership conflict",
                    )
                ]
    return []


def _apply_outputs_transactionally(
    pack_dir: Path,
    outputs: Mapping[str, bytes],
    prior_manifest: Mapping[str, Any] | None,
    *,
    handoff_paths: set[str],
    fail_after_operations: int | None,
) -> Diagnostic | None:
    """Apply managed writes with complete rollback after any apply failure."""

    if not _supports_safe_dir_fd():
        return _diagnostic(
            "OKF010",
            _display_path(pack_dir, "."),
            "safe managed output writes are unavailable on this platform",
        )

    stale_paths = {
        path
        for path in _manifest_records(prior_manifest)
        if path not in outputs and path not in handoff_paths
    }
    affected_paths = set(outputs) | stale_paths
    original: dict[str, bytes | None] = {}
    for relative_path in sorted(affected_paths, key=_sort_path):
        path = pack_dir / relative_path
        if not _path_lexists(path):
            original[relative_path] = None
            continue
        diagnostic = _managed_output_path_diagnostic(
            pack_dir,
            relative_path,
            require_existing_file=True,
        )
        if diagnostic is not None:
            return diagnostic
        try:
            original[relative_path] = _read_confined_regular_file(
                pack_dir,
                path,
                max_bytes=MANAGED_OUTPUT_MAX_BYTES,
            )
        except (OSError, ValueError):
            return _diagnostic(
                "OKF010",
                _display_path(pack_dir, relative_path),
                "ownership conflict",
            )

    if fail_after_operations is not None and fail_after_operations <= 0:
        return _diagnostic("OKF010", _display_path(pack_dir, "."), "injected apply failure")

    operations = 0
    try:
        for relative_path in sorted(stale_paths, key=_sort_path, reverse=True):
            path = pack_dir / relative_path
            if _path_lexists(path):
                _unlink_confined(pack_dir, relative_path)
                _prune_empty_parents(path.parent, pack_dir)
                operations += 1
                if fail_after_operations == operations:
                    raise OSError("injected apply failure")

        for relative_path, data in sorted(outputs.items(), key=lambda item: _sort_path(item[0])):
            prewrite = _managed_output_path_diagnostic(
                pack_dir,
                relative_path,
                require_existing_file=False,
            )
            if prewrite is not None:
                raise OSError("managed output path changed before write")
            _atomic_write_confined(pack_dir, relative_path, data)
            operations += 1
            if fail_after_operations == operations:
                raise OSError("injected apply failure")
    except (OSError, ValueError):
        try:
            _restore_managed_outputs(pack_dir, original)
        except (OSError, ValueError):
            return _diagnostic(
                "OKF010",
                _display_path(pack_dir, "."),
                "apply failed and rollback was incomplete",
            )
        return _diagnostic(
            "OKF010",
            _display_path(pack_dir, "."),
            "apply failed and was rolled back",
        )
    return None


def _restore_managed_outputs(
    pack_dir: Path,
    original: Mapping[str, bytes | None],
) -> None:
    for relative_path in sorted(original, key=_sort_path, reverse=True):
        if original[relative_path] is not None:
            continue
        path = pack_dir / relative_path
        if _path_lexists(path):
            _unlink_confined(pack_dir, relative_path)
            _prune_empty_parents(path.parent, pack_dir)
    for relative_path, data in sorted(original.items(), key=lambda item: _sort_path(item[0])):
        if data is None:
            continue
        _atomic_write_confined(pack_dir, relative_path, data)


def _atomic_write_confined(pack_dir: Path, relative_path: str, data: bytes) -> None:
    """Atomically publish bytes without following the final path or its parents."""

    if _supports_safe_dir_fd():
        _atomic_write_confined_dir_fd(pack_dir, relative_path, data)
        return
    raise ValueError("safe managed output writes are unavailable on this platform")


def _atomic_write_confined_dir_fd(
    pack_dir: Path,
    relative_path: str,
    data: bytes,
) -> None:
    parent_fd, parent_path = _open_confined_parent_fd(
        pack_dir,
        relative_path,
        create=True,
    )
    leaf = relative_path.rsplit("/", 1)[-1]
    temporary = f".{leaf}.agentbundle-okf-tmp"
    descriptor = -1
    try:
        _reject_unsafe_leaf_fd(parent_fd, leaf, allow_missing=True)
        _reject_unsafe_leaf_fd(parent_fd, temporary, allow_missing=True, require_missing=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(temporary, flags, 0o600, dir_fd=parent_fd)
        _write_all(descriptor, data)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        if not _directory_descriptor_matches_path(parent_fd, parent_path):
            raise ValueError("managed output parent changed before publish")
        os.rename(
            temporary,
            leaf,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        if not _directory_descriptor_matches_path(parent_fd, parent_path):
            raise ValueError("managed output parent changed during publish")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        with suppress(FileNotFoundError):
            os.unlink(temporary, dir_fd=parent_fd)
        os.close(parent_fd)


def _unlink_confined(pack_dir: Path, relative_path: str) -> None:
    if not _supports_safe_dir_fd():
        raise ValueError("safe managed output removal is unavailable on this platform")
    parent_fd, parent_path = _open_confined_parent_fd(
        pack_dir,
        relative_path,
        create=False,
    )
    try:
        _reject_unsafe_leaf_fd(parent_fd, relative_path.rsplit("/", 1)[-1])
        if not _directory_descriptor_matches_path(parent_fd, parent_path):
            raise ValueError("managed output parent changed before removal")
        os.unlink(relative_path.rsplit("/", 1)[-1], dir_fd=parent_fd)
        if not _directory_descriptor_matches_path(parent_fd, parent_path):
            raise ValueError("managed output parent changed during removal")
    finally:
        os.close(parent_fd)


def _open_confined_parent_fd(
    pack_dir: Path,
    relative_path: str,
    *,
    create: bool,
) -> tuple[int, Path]:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    root_before = pack_dir.lstat()
    descriptor = os.open(pack_dir, flags)
    root_after = os.fstat(descriptor)
    if (
        _is_reparse_stat(root_before)
        or _is_reparse_stat(root_after)
        or (root_before.st_dev, root_before.st_ino)
        != (root_after.st_dev, root_after.st_ino)
    ):
        os.close(descriptor)
        raise ValueError("pack root changed while opening")
    current_path = pack_dir
    try:
        for part in relative_path.split("/")[:-1]:
            current_path = current_path / part
            try:
                child = os.open(part, flags, dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, mode=0o755, dir_fd=descriptor)
                child = os.open(part, flags, dir_fd=descriptor)
            info = os.fstat(child)
            if not stat.S_ISDIR(info.st_mode) or _is_reparse_stat(info):
                os.close(child)
                raise ValueError("managed output parent is unsafe")
            os.close(descriptor)
            descriptor = child
        if not _directory_descriptor_matches_path(descriptor, current_path):
            raise ValueError("managed output parent changed while opening")
        return descriptor, current_path
    except BaseException:
        os.close(descriptor)
        raise


def _directory_descriptor_matches_path(descriptor: int, path: Path) -> bool:
    try:
        before = path.lstat()
        after = os.fstat(descriptor)
    except OSError:
        return False
    return (
        stat.S_ISDIR(before.st_mode)
        and not stat.S_ISLNK(before.st_mode)
        and not _is_reparse_stat(before)
        and not _is_reparse_stat(after)
        and (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
    )


def _reject_unsafe_leaf_fd(
    parent_fd: int,
    leaf: str,
    *,
    allow_missing: bool = False,
    require_missing: bool = False,
) -> None:
    try:
        info = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        if allow_missing:
            return
        raise
    if require_missing:
        raise ValueError("managed temporary output already exists")
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or _is_reparse_stat(info):
        raise ValueError("managed output leaf is unsafe")


def _write_all(descriptor: int, data: bytes) -> None:
    view = memoryview(data)
    written = 0
    while written < len(view):
        count = os.write(descriptor, view[written:])
        if count <= 0:
            raise OSError("managed output write did not make progress")
        written += count


def _supports_safe_dir_fd() -> bool:
    return _SAFE_DIR_FD_SUPPORTED


def _prune_empty_parents(parent: Path, pack_dir: Path) -> None:
    while parent != pack_dir and _is_real_directory(parent) and not any(parent.iterdir()):
        parent.rmdir()
        parent = parent.parent


def _is_managed_output_path(path: str) -> bool:
    return _is_safe_relative_path(path) and path.startswith(".apm/skills/")


def _directory_boundary_diagnostic(
    base: Path,
    path: Path,
    display_path: str,
) -> Diagnostic | None:
    try:
        info = path.lstat()
    except OSError:
        return _diagnostic("OKF004", display_path, "path resolution failed")
    if (
        stat.S_ISLNK(info.st_mode)
        or _is_reparse_stat(info)
        or not stat.S_ISDIR(info.st_mode)
    ):
        return _diagnostic("OKF004", display_path, "directory boundary is unsafe")
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return _diagnostic("OKF004", display_path, "path resolution failed")
    if not _is_within(resolved, base):
        return _diagnostic("OKF004", display_path, "directory escapes pack boundary")
    return None


def _bundle_root_boundary_diagnostic(pack_dir: Path, bundle_path: str) -> Diagnostic | None:
    current = pack_dir
    for part in bundle_path.split("/"):
        current = current / part
        diagnostic = _directory_boundary_diagnostic(
            pack_dir,
            current,
            _display_path(pack_dir, str(current.relative_to(pack_dir))),
        )
        if diagnostic is not None:
            return diagnostic
    return None


def _managed_output_path_diagnostic(
    pack_dir: Path,
    relative_path: str,
    *,
    require_existing_file: bool,
) -> Diagnostic | None:
    if relative_path != ".okf-generated.json" and not _is_managed_output_path(relative_path):
        return _diagnostic("OKF010", _display_path(pack_dir, relative_path), "unsafe managed path")
    current = pack_dir
    for part in relative_path.split("/")[:-1]:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            return _diagnostic(
                "OKF010",
                _display_path(pack_dir, str(current.relative_to(pack_dir))),
                "ownership conflict",
            )
        if (
            stat.S_ISLNK(info.st_mode)
            or _is_reparse_stat(info)
            or not stat.S_ISDIR(info.st_mode)
        ):
            return _diagnostic(
                "OKF010",
                _display_path(pack_dir, str(current.relative_to(pack_dir))),
                "ownership conflict",
            )
        if not _is_within(current.resolve(strict=True), pack_dir):
            return _diagnostic(
                "OKF010",
                _display_path(pack_dir, str(current.relative_to(pack_dir))),
                "ownership conflict",
            )
    target = pack_dir / relative_path
    try:
        info = target.lstat()
    except FileNotFoundError:
        return None
    except OSError:
        return _diagnostic("OKF010", _display_path(pack_dir, relative_path), "ownership conflict")
    if stat.S_ISLNK(info.st_mode) or _is_reparse_stat(info):
        return _diagnostic("OKF010", _display_path(pack_dir, relative_path), "ownership conflict")
    if require_existing_file and not stat.S_ISREG(info.st_mode):
        return _diagnostic("OKF010", _display_path(pack_dir, relative_path), "ownership conflict")
    try:
        resolved = target.resolve(strict=True)
    except OSError:
        return _diagnostic("OKF010", _display_path(pack_dir, relative_path), "ownership conflict")
    if not _is_within(resolved, pack_dir):
        return _diagnostic("OKF010", _display_path(pack_dir, relative_path), "ownership conflict")
    return None


def _is_real_directory(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    return (
        stat.S_ISDIR(info.st_mode)
        and not stat.S_ISLNK(info.st_mode)
        and not _is_reparse_stat(info)
    )


def _is_reparse_stat(info: os.stat_result) -> bool:
    return bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _path_lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _is_within(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def _skill_directory(path: str) -> str | None:
    parts = path.split("/")
    if len(parts) < 3 or parts[:2] != [".apm", "skills"] or not parts[2]:
        return None
    return "/".join(parts[:3])


def _record_marker_matches(record: Mapping[str, Any], data: bytes) -> bool:
    marker = record.get("marker")
    kind = record.get("kind")
    output_path = record.get("output_path")
    if kind == "okf-index":
        return marker == MANAGED_INDEX_MARKER and MANAGED_INDEX_MARKER.encode("utf-8") in data
    if isinstance(output_path, str) and output_path.endswith("/SKILL.md"):
        return (
            marker == "generated-by: compile-okf agentbundle-okf/v1"
            and b"generated-by: compile-okf agentbundle-okf/v1" in data
        )
    return True


def _compile_result(exit_code: int, diagnostics: Iterable[Diagnostic]) -> CompileResult:
    sorted_diagnostics = tuple(_sort_diagnostics(diagnostics))
    stderr = "".join(f"{item.code} {item.path} {item.message}\n" for item in sorted_diagnostics)
    return CompileResult(exit_code=exit_code, diagnostics=sorted_diagnostics, stderr=stderr)


def _display_path(pack_dir: Path, relative_path: str) -> str:
    return f"packs/{pack_dir.name}/{relative_path}"


def _read_record(root: Path, relative_path: str) -> _FileRecord:
    path = root / relative_path
    return _FileRecord(
        path=path,
        relative_path=relative_path,
        data=path.read_bytes(),
        mode=path.lstat().st_mode,
    )


def _tree_digest(files: Mapping[str, bytes]) -> str:
    payload = [
        {"path": path, "sha256": _bytes_digest(data)}
        for path, data in sorted(files.items(), key=lambda item: _sort_path(item[0]))
    ]
    return _bytes_digest(canonical_json_bytes(payload))


def _bytes_digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


review_projection_digest.bytes_digest = _bytes_digest  # type: ignore[attr-defined]


def _sort_path(path: str) -> bytes:
    return unicodedata.normalize("NFC", path).encode("utf-8")


def _scan_regular_files(
    root: Path,
    *,
    limits: Mapping[str, int],
    reparse_paths: set[str],
    resolution_failure_paths: set[str],
    before_open: Callable[[Path], None] | None,
) -> _ScanResult:
    diagnostics: list[Diagnostic] = []
    records: list[_FileRecord] = []
    reported_hardlink_inodes: set[tuple[int, int]] = set()
    allocated_bytes = 0
    total_limit_reported = False
    file_limit_reported = False

    inventory, inventory_diagnostics = _inventory_paths_no_reparse(root)
    diagnostics.extend(inventory_diagnostics)
    for path, initial in inventory:
        relative_path = _relative_path(root, path)
        host_key = _normalize_host_path(path)

        if host_key in resolution_failure_paths:
            diagnostics.append(_diagnostic("OKF004", relative_path, "path resolution failed"))
            continue
        if host_key in reparse_paths or _is_reparse_stat(initial):
            diagnostics.append(
                _diagnostic("OKF004", relative_path, "reparse point input is not allowed")
            )
            continue
        if stat.S_ISDIR(initial.st_mode):
            continue
        if stat.S_ISLNK(initial.st_mode) or not stat.S_ISREG(initial.st_mode):
            diagnostics.append(
                _diagnostic("OKF004", relative_path, "input must be a regular file")
            )
            continue
        if not _is_safe_relative_path(relative_path):
            diagnostics.append(_diagnostic("OKF004", relative_path, "unsafe path"))
            continue
        inode = (initial.st_dev, initial.st_ino)
        if initial.st_nlink != 1:
            if inode not in reported_hardlink_inodes:
                diagnostics.append(
                    _diagnostic("OKF004", relative_path, "multiply linked regular file")
                )
                reported_hardlink_inodes.add(inode)
            continue
        per_file_limit = (
            limits["markdown_bytes"]
            if relative_path.endswith(".md")
            else limits["total_bytes"]
        )
        if initial.st_size > per_file_limit:
            if not file_limit_reported:
                diagnostics.append(
                    _diagnostic("OKF005", relative_path, "file exceeds bounded read limit")
                )
                file_limit_reported = True
            continue
        if allocated_bytes + initial.st_size > limits["total_bytes"]:
            if not total_limit_reported:
                diagnostics.append(
                    _diagnostic("OKF005", relative_path, "bundle exceeds bounded read limit")
                )
                total_limit_reported = True
            continue
        if before_open is not None:
            before_open(path)
        try:
            data, current = _read_regular_file_no_follow(
                path,
                initial,
                max_bytes=per_file_limit,
            )
        except _BoundedReadError:
            diagnostics.append(
                _diagnostic("OKF005", relative_path, "file exceeds bounded read limit")
            )
            continue
        except (OSError, ValueError):
            diagnostics.append(
                _diagnostic("OKF004", relative_path, "input changed between inspection and open")
            )
            continue
        allocated_bytes += len(data)
        records.append(
            _FileRecord(
                path=path,
                relative_path=relative_path,
                data=data,
                mode=current.st_mode,
            )
        )

    return _ScanResult(
        files=tuple(sorted(records, key=lambda record: record.relative_path.encode("utf-8"))),
        diagnostics=tuple(diagnostics),
    )


def _inventory_paths_no_reparse(
    root: Path,
) -> tuple[list[tuple[Path, os.stat_result]], list[Diagnostic]]:
    """Inventory without descending through symlink or Windows reparse directories."""

    pending = [root]
    entries: list[tuple[Path, os.stat_result]] = []
    diagnostics: list[Diagnostic] = []
    while pending:
        directory = pending.pop()
        try:
            children = sorted(
                (Path(entry.path) for entry in os.scandir(directory)),
                key=lambda item: item.as_posix(),
            )
        except OSError:
            relative = "." if directory == root else _relative_path(root, directory)
            diagnostics.append(_diagnostic("OKF004", relative, "path resolution failed"))
            continue
        for path in children:
            try:
                info = path.lstat()
            except OSError:
                diagnostics.append(
                    _diagnostic("OKF004", _relative_path(root, path), "path resolution failed")
                )
                continue
            entries.append((path, info))
            if (
                stat.S_ISDIR(info.st_mode)
                and not stat.S_ISLNK(info.st_mode)
                and not _is_reparse_stat(info)
            ):
                pending.append(path)
    return sorted(entries, key=lambda item: item[0].as_posix()), diagnostics


def _read_regular_file_no_follow(
    path: Path,
    before: os.stat_result,
    *,
    max_bytes: int,
) -> tuple[bytes, os.stat_result]:
    """Read a single-link regular file through a verified descriptor."""

    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        after = os.fstat(descriptor)
        if not stat.S_ISREG(after.st_mode) or after.st_nlink != 1:
            raise ValueError("input is not a single-link regular file")
        if _is_reparse_stat(after) or after.st_size > max_bytes:
            raise _BoundedReadError("input exceeds bounded read contract")
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise ValueError("input changed while opening")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            data = handle.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise _BoundedReadError("input grew beyond bounded read contract")
            return data, after
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _read_confined_regular_file(
    root: Path,
    path: Path,
    *,
    max_bytes: int,
) -> bytes:
    """Read one confined, single-link regular file through a verified descriptor."""

    try:
        before = path.lstat()
    except OSError as exc:
        raise ValueError("file cannot be inspected") from exc
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
        or _is_reparse_stat(before)
        or before.st_size > max_bytes
    ):
        raise ValueError("file is not a single-link regular file")
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ValueError("file escapes its declared root") from exc
    data, _ = _read_regular_file_no_follow(path, before, max_bytes=max_bytes)
    return data


def _parse_frontmatter(record: _FileRecord) -> _ParsedFrontmatter:
    diagnostics: list[Diagnostic] = []
    text = record.data.decode("utf-8", errors="strict")
    if not text.startswith("---\n"):
        return _ParsedFrontmatter(data={}, body=text, diagnostics=())

    frontmatter_start = 4
    if text.startswith("---\n", frontmatter_start):
        end = frontmatter_start
        body_start = frontmatter_start + 4
    else:
        end = text.find("\n---\n", frontmatter_start)
        body_start = end + 5
    if end == -1:
        diagnostics.append(
            _diagnostic("OKF003", record.relative_path, "frontmatter is not closed")
        )
        return _ParsedFrontmatter(data={}, body="", diagnostics=tuple(diagnostics))

    raw_frontmatter = text[4:end]
    frontmatter_bytes = raw_frontmatter.encode("utf-8")
    if len(frontmatter_bytes) > DEFAULT_LIMITS["frontmatter_bytes"]:
        diagnostics.append(
            _diagnostic("OKF005", record.relative_path, "frontmatter exceeds size limit")
        )
        return _ParsedFrontmatter(data={}, body="", diagnostics=tuple(diagnostics))
    if _contains_forbidden_yaml_syntax(raw_frontmatter):
        diagnostics.append(
            _diagnostic("OKF003", record.relative_path, "YAML tags and aliases are not allowed")
        )
        return _ParsedFrontmatter(data={}, body="", diagnostics=tuple(diagnostics))

    try:
        too_deep = _yaml_structure_too_deep(raw_frontmatter, max_depth=20)
    except (yaml.YAMLError, RecursionError):
        diagnostics.append(
            _diagnostic("OKF003", record.relative_path, "malformed YAML frontmatter")
        )
        return _ParsedFrontmatter(data={}, body="", diagnostics=tuple(diagnostics))
    if too_deep:
        diagnostics.append(
            _diagnostic("OKF003", record.relative_path, "frontmatter contains unsupported values")
        )
        return _ParsedFrontmatter(data={}, body="", diagnostics=tuple(diagnostics))

    try:
        data = yaml.safe_load(raw_frontmatter) or {}
    except (yaml.YAMLError, RecursionError):
        diagnostics.append(
            _diagnostic("OKF003", record.relative_path, "malformed YAML frontmatter")
        )
        return _ParsedFrontmatter(data={}, body="", diagnostics=tuple(diagnostics))
    if _too_deep(data, max_depth=20) or _contains_non_finite_number(data):
        diagnostics.append(
            _diagnostic("OKF003", record.relative_path, "frontmatter contains unsupported values")
        )
    return _ParsedFrontmatter(data=data, body=text[body_start:], diagnostics=tuple(diagnostics))


def _yaml_structure_too_deep(raw: str, *, max_depth: int) -> bool:
    """Bound YAML collection depth before composing Python objects."""

    starts = (
        BlockMappingStartToken,
        BlockSequenceStartToken,
        FlowMappingStartToken,
        FlowSequenceStartToken,
    )
    ends = (BlockEndToken, FlowMappingEndToken, FlowSequenceEndToken)
    depth = 0
    for token in yaml.scan(raw):
        if isinstance(token, starts):
            depth += 1
            if depth > max_depth:
                return True
        elif isinstance(token, ends):
            depth = max(0, depth - 1)
    return False


def _metadata_diagnostics(path: str, metadata: Mapping[str, Any]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for key, value in metadata.items():
        if key in _UNSAFE_METADATA_KEYS:
            diagnostics.append(
                _diagnostic("OKF009", path, "execution metadata is inert and not accepted here")
            )
            continue
        if not _is_utf8_encodable(value):
            # `yaml.safe_load` accepts a `\uD800` escape, and values such as
            # `license`, `boundaries` and an `x-agentbundle` skill `description`
            # reach strict encodes on the manifest and digest path. Without this
            # the process aborts on an uncaught UnicodeEncodeError with no
            # diagnostic; a value that cannot be encoded is malformed, which is
            # what `OKF003` already covers.
            diagnostics.append(
                _diagnostic("OKF003", path, "frontmatter value is not encodable as UTF-8")
            )
            continue
        if _contains_remote_reference(value):
            diagnostics.append(
                _diagnostic("OKF009", path, "remote retrieval metadata is not allowed")
            )
    return diagnostics



def _pack_profile_diagnostics(profile: Any, path: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(profile, Mapping):
        return [_diagnostic("OKF001", path, "invalid OKF pack profile")]
    if set(profile) != {"profile", "bundles"}:
        diagnostics.append(_diagnostic("OKF001", path, "invalid OKF pack profile properties"))
    if profile.get("profile") != SUPPORTED_PROFILE:
        diagnostics.append(_diagnostic("OKF001", path, "unsupported OKF profile"))
    bundles = profile.get("bundles")
    if not isinstance(bundles, list) or not 1 <= len(bundles) <= 128:
        diagnostics.append(_diagnostic("OKF001", path, "invalid OKF bundle list"))
        return diagnostics

    seen_bundles: set[tuple[str, str, str]] = set()
    seen_ids: set[str] = set()
    for index, bundle in enumerate(bundles):
        bundle_path = f"{path}:bundles[{index}]"
        if not isinstance(bundle, Mapping):
            diagnostics.append(_diagnostic("OKF001", bundle_path, "invalid OKF bundle"))
            continue
        allowed = {"id", "path", "router-skill", "projected-concepts", "provider"}
        if not {"id", "path", "router-skill"}.issubset(bundle) or not set(bundle) <= allowed:
            diagnostics.append(_diagnostic("OKF001", bundle_path, "invalid OKF bundle properties"))
        bundle_id = bundle.get("id")
        source_path = bundle.get("path")
        router_skill = bundle.get("router-skill")
        if not _is_slug(bundle_id):
            diagnostics.append(_diagnostic("OKF001", bundle_path, "invalid OKF bundle id"))
        elif bundle_id in seen_ids:
            diagnostics.append(_diagnostic("OKF001", bundle_path, "duplicate OKF bundle id"))
        else:
            seen_ids.add(bundle_id)
        if not isinstance(source_path, str) or not _is_okf_directory(source_path):
            diagnostics.append(_diagnostic("OKF001", bundle_path, "invalid OKF bundle path"))
        if not _is_slug(router_skill):
            diagnostics.append(_diagnostic("OKF001", bundle_path, "invalid OKF router skill"))
        diagnostics.extend(
            _provider_capability_diagnostics(bundle.get("provider"), bundle_path)
        )
        if (
            isinstance(bundle_id, str)
            and isinstance(source_path, str)
            and isinstance(router_skill, str)
        ):
            bundle_identity = (bundle_id, source_path, router_skill)
            if bundle_identity in seen_bundles:
                diagnostics.append(_diagnostic("OKF001", bundle_path, "duplicate OKF bundle"))
            seen_bundles.add(bundle_identity)
        projected = bundle.get("projected-concepts", [])
        if projected is None:
            projected = []
        if not isinstance(projected, list) or len(projected) > 2000:
            diagnostics.append(_diagnostic("OKF001", bundle_path, "invalid projected concepts"))
            continue
        seen_projected: set[tuple[str, str]] = set()
        for projected_index, item in enumerate(projected):
            projected_path = f"{bundle_path}:projected-concepts[{projected_index}]"
            if not isinstance(item, Mapping):
                diagnostics.append(
                    _diagnostic("OKF001", projected_path, "invalid projected concept")
                )
                continue
            if set(item) != {"path", "reviewed-projection-digest"}:
                diagnostics.append(
                    _diagnostic("OKF001", projected_path, "invalid projected concept properties")
                )
            concept_path = item.get("path")
            digest = item.get("reviewed-projection-digest")
            if not isinstance(concept_path, str) or not _is_bundle_file(concept_path):
                diagnostics.append(
                    _diagnostic("OKF001", projected_path, "invalid projected concept path")
                )
            if not _is_sha256(digest):
                diagnostics.append(
                    _diagnostic("OKF001", projected_path, "invalid review digest")
                )
            if isinstance(concept_path, str) and isinstance(digest, str):
                projection_identity = (concept_path, digest)
                if projection_identity in seen_projected:
                    diagnostics.append(
                        _diagnostic("OKF001", projected_path, "duplicate projected concept")
                    )
                seen_projected.add(projection_identity)
    return diagnostics


def _provider_capability_diagnostics(provider: Any, bundle_path: str) -> list[Diagnostic]:
    """Validate optional independent-provider discovery metadata."""

    if provider is None:
        return []
    provider_path = f"{bundle_path}:provider"
    if not isinstance(provider, Mapping):
        return [_diagnostic("OKF001", provider_path, "invalid provider capability")]
    required = {
        "contract-version",
        "domain",
        "purpose",
        "task-kinds",
        "invocation",
        "ownership-manifest",
    }
    diagnostics: list[Diagnostic] = []
    if set(provider) != required:
        diagnostics.append(
            _diagnostic("OKF001", provider_path, "invalid provider capability properties")
        )
    contract_version = provider.get("contract-version")
    if (
        not isinstance(contract_version, str)
        or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}/v[1-9][0-9]*", contract_version)
    ):
        diagnostics.append(
            _diagnostic("OKF001", provider_path, "invalid provider contract version")
        )
    for key in ("domain", "purpose"):
        value = provider.get(key)
        if (
            not isinstance(value, str)
            or not 1 <= len(value) <= 512
            or not all(" " <= character <= "~" for character in value)
        ):
            diagnostics.append(
                _diagnostic("OKF001", provider_path, f"invalid provider {key}")
            )
    task_kinds = provider.get("task-kinds")
    if (
        not isinstance(task_kinds, list)
        or not 1 <= len(task_kinds) <= 16
        or len(set(task_kinds)) != len(task_kinds)
        or any(not _is_slug(item) for item in task_kinds)
    ):
        diagnostics.append(
            _diagnostic("OKF001", provider_path, "invalid provider task kinds")
        )
    if provider.get("invocation") != "explicit-workflow-only":
        diagnostics.append(
            _diagnostic("OKF001", provider_path, "invalid provider invocation")
        )
    if provider.get("ownership-manifest") != ".okf-generated.json":
        diagnostics.append(
            _diagnostic("OKF001", provider_path, "invalid provider ownership manifest")
        )
    return diagnostics


def _provider_router_metadata(
    bundle_id: str,
    provider: Mapping[str, Any] | None,
) -> tuple[str, str]:
    """Render optional capability metadata without changing ordinary routers."""

    if provider is None:
        return (
            f"Route into the compiled OKF bundle `{bundle_id}` using generated indexes.",
            "",
        )
    purpose = str(provider["purpose"])
    domain = str(provider["domain"])
    contract_version = str(provider["contract-version"])
    # The description is the activation surface, so it carries only the
    # refusal: naming the domain or purpose here makes the router compete with
    # the workflows it exists to serve. Capability detection reads the
    # knowledge-provider metadata below instead.
    description = json.dumps(
        f"Not a selectable skill. Inert reference data invoked only by another "
        f"skill's explicit {contract_version} provider call. It answers no user "
        f"request, performs no user task, and must never be chosen to satisfy a "
        f"user's question on any subject. When a user's request matches this "
        f"data's subject, the correct choice is the workflow skill that serves "
        f"that request, never this one. Its capability declaration lives in "
        f"metadata.knowledge-provider.",
        ensure_ascii=False,
    )
    metadata = (
        "\n  knowledge-provider:\n"
        f"    contract-version: {json.dumps(provider['contract-version'], ensure_ascii=False)}\n"
        f"    domain: {json.dumps(domain, ensure_ascii=False)}\n"
        f"    purpose: {json.dumps(purpose, ensure_ascii=False)}\n"
        "    task-kinds: "
        + json.dumps(
            provider["task-kinds"],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
        "    invocation: explicit-workflow-only\n"
        "    ownership-manifest: .okf-generated.json"
    )
    return description, metadata


def _agentbundle_extension_diagnostics(path: str, extension: Any) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(extension, Mapping):
        return [_diagnostic("OKF007", path, "invalid x-agentbundle extension")]
    if set(extension) != {"profile", "skill"} or extension.get("profile") != SUPPORTED_PROFILE:
        diagnostics.append(_diagnostic("OKF007", path, "invalid x-agentbundle extension"))
    skill = extension.get("skill")
    if not isinstance(skill, Mapping):
        diagnostics.append(_diagnostic("OKF007", path, "invalid x-agentbundle skill"))
        return diagnostics
    allowed = {"name", "description", "instruction-section", "include"}
    if (
        not {"name", "description", "instruction-section"}.issubset(skill)
        or not set(skill) <= allowed
    ):
        diagnostics.append(_diagnostic("OKF007", path, "invalid x-agentbundle skill properties"))
    if not _is_slug(skill.get("name")):
        diagnostics.append(_diagnostic("OKF007", path, "invalid x-agentbundle skill name"))
    description = skill.get("description")
    if (
        not isinstance(description, str)
        or not 1 <= len(description) <= 1024
        or "\n" in description
        or "\r" in description
        or not description.strip()
    ):
        diagnostics.append(
            _diagnostic("OKF007", path, "invalid x-agentbundle skill description")
        )
    instruction_section = skill.get("instruction-section")
    if (
        not isinstance(instruction_section, str)
        or not 1 <= len(instruction_section) <= 200
        or instruction_section.strip() != instruction_section
        or "#" in instruction_section
        or "\n" in instruction_section
        or "\r" in instruction_section
        or not instruction_section.strip()
    ):
        diagnostics.append(
            _diagnostic("OKF007", path, "invalid x-agentbundle instruction section")
        )
    includes = skill.get("include", [])
    if includes is None:
        includes = []
    if not isinstance(includes, list) or len(includes) > 64:
        diagnostics.append(_diagnostic("OKF007", path, "invalid x-agentbundle includes"))
        return diagnostics
    seen: set[str] = set()
    for include in includes:
        if not isinstance(include, str) or not _is_bundle_file(include):
            diagnostics.append(_diagnostic("OKF007", path, "invalid x-agentbundle include"))
            continue
        if include in seen:
            diagnostics.append(_diagnostic("OKF007", path, "duplicate x-agentbundle include"))
        seen.add(include)
    return diagnostics


def _include_diagnostics(
    records: Mapping[str, _FileRecord],
    includes: tuple[str, ...],
) -> list[Diagnostic]:
    return [
        _diagnostic("OKF004", include, "include is missing or not a regular file")
        for include in includes
        if include not in records
    ]


def _resource_diagnostics(
    records: tuple[_FileRecord, ...],
    limits: Mapping[str, int],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    concept_records = [
        record
        for record in records
        if record.relative_path != "index.md" and record.relative_path.endswith(".md")
    ]
    total_bytes = sum(len(record.data) for record in records)
    max_depth = max(
        (len(Path(record.relative_path).parent.parts) for record in records),
        default=0,
    )
    checks = [
        ("file_count", len(records)),
        ("concept_count", len(concept_records)),
        ("total_bytes", total_bytes),
        ("directory_depth", max_depth),
    ]
    for name, value in checks:
        if value > limits[name]:
            diagnostics.append(_diagnostic("OKF005", ".", f"{name} exceeds resource limit"))

    for record in concept_records:
        if len(record.data) > limits["markdown_bytes"]:
            diagnostics.append(
                _diagnostic("OKF005", record.relative_path, "Markdown file exceeds size limit")
            )
        frontmatter = _frontmatter_bytes(record.data)
        if frontmatter is not None and len(frontmatter) > limits["frontmatter_bytes"]:
            diagnostics.append(
                _diagnostic("OKF005", record.relative_path, "frontmatter exceeds size limit")
            )
    return diagnostics


def _frontmatter_bytes(data: bytes) -> bytes | None:
    if not data.startswith(b"---\n"):
        return None
    end = data.find(b"\n---\n", 4)
    if end == -1:
        return None
    return data[4:end]


def _collision_diagnostics(paths: Iterable[str]) -> list[Diagnostic]:
    seen: dict[str, str] = {}
    diagnostics: list[Diagnostic] = []
    for path in paths:
        normalized = unicodedata.normalize("NFC", path).casefold()
        previous = seen.get(normalized)
        if previous is not None and previous != path:
            diagnostics.append(_diagnostic("OKF004", path, f"path collides with {previous}"))
        else:
            seen[normalized] = path
    return diagnostics


def _is_safe_relative_path(path: str) -> bool:
    if not path or path.startswith("/") or "\\" in path or "//" in path or path.endswith("/"):
        return False
    # A name the filesystem yields as surrogate-escaped bytes is not encodable, and
    # every downstream sink here encodes strictly. Rejecting it at the gate keeps it
    # out of the scan and the sort, so it fails with this function's existing
    # `OKF004` instead of aborting the process on an uncaught UnicodeEncodeError.
    try:
        path.encode("utf-8")
    except UnicodeEncodeError:
        return False
    if re.match(r"^[A-Za-z]:", path):
        return False
    parts = path.split("/")
    for part in parts:
        if (
            part in ("", ".", "..")
            or any(ord(char) < 32 or ord(char) == 127 for char in part)
            or any(char in '<>:"|?*' for char in part)
            or part.endswith((".", " "))
            or _WINDOWS_DEVICE.match(part)
            # A path component becomes display text in a generated heading, where
            # an address shape renders a live `mailto:` link. Unlike `www.` and
            # `scheme://`, escaping cannot defuse it — cmark-gfm resolves the
            # escape before its autolink pass — so this is the only place the
            # trigger can be stopped.
            or _REMOTE_ADDRESS.search(part)
        ):
            return False
    return True


def _is_slug(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 64 and bool(_SLUG.fullmatch(value))


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256.fullmatch(value))


def _is_bundle_file(path: str) -> bool:
    return 1 <= len(path) <= 1000 and _is_safe_relative_path(path)


def _is_okf_directory(path: str) -> bool:
    return 5 <= len(path) <= 1000 and path.startswith("okf/") and _is_safe_relative_path(path)


def _is_pack_name(pack: str) -> bool:
    return "/" not in pack and "\\" not in pack and _is_safe_relative_path(pack)


def _contains_forbidden_yaml_syntax(raw_frontmatter: str) -> bool:
    for line in raw_frontmatter.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if re.search(r"(^|[:\[,]\s*)![^\s,}\]]+", stripped):
            return True
        if re.search(r"(^|[\s\[{,])&[A-Za-z0-9_-]+", stripped):
            return True
        if re.search(r"(^|[\s\[{,])\*[A-Za-z0-9_-]+", stripped):
            return True
    return False


def _too_deep(value: Any, *, max_depth: int, depth: int = 0) -> bool:
    if depth > max_depth:
        return True
    if isinstance(value, Mapping):
        return any(
            _too_deep(item, max_depth=max_depth, depth=depth + 1)
            for item in value.values()
        )
    if isinstance(value, list):
        return any(_too_deep(item, max_depth=max_depth, depth=depth + 1) for item in value)
    return False


def _contains_non_finite_number(value: Any) -> bool:
    if isinstance(value, float) and not math.isfinite(value):
        return True
    if isinstance(value, Mapping):
        return any(_contains_non_finite_number(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_non_finite_number(item) for item in value)
    return False


def _is_utf8_encodable(value: Any) -> bool:
    """Return whether every string inside `value` survives a strict UTF-8 encode."""
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            return False
        return True
    if isinstance(value, Mapping):
        return all(
            _is_utf8_encodable(key) and _is_utf8_encodable(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return all(_is_utf8_encodable(item) for item in value)
    return True


def _contains_remote_reference(value: Any) -> bool:
    """Return whether `value` carries a remote reference anywhere inside it.

    Frontmatter is display and governance metadata. This compiler never fetches a
    URL or dereferences a remote resource, so a URL here is never dereferenced and
    has no function the format supports. What it can do is survive display escaping into
    a compiler-owned index that an agent treats as authoritative, where a GFM
    extended autolink turns it into a live link. Matching anywhere rather than at
    the start closes that, and covers `www.` and `mailto:` because GFM linkifies
    those too.

    Concept **bodies** are deliberately not scanned. An organization-specific
    corpus legitimately points a reader at an internal app or runbook for manual
    follow-up, and the body is where such a pointer belongs: it reaches the agent
    on descent, is never fetched, and renders as authored.
    """
    if isinstance(value, str):
        return bool(_REMOTE_SCHEME.search(value) or _REMOTE_ADDRESS.search(value))
    if isinstance(value, Mapping):
        return any(_contains_remote_reference(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_remote_reference(item) for item in value)
    return False


def _relative_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _normalize_host_path(path: Path) -> str:
    return path.resolve(strict=False).as_posix()


def _diagnostic(code: str, path: str, message: str) -> Diagnostic:
    """Build a diagnostic whose path is safe for every downstream sink.

    Normalizing here rather than at each gate is what makes the refusal total. A
    path that is not valid UTF-8 reaches this constructor carrying surrogates,
    and `_sort_diagnostics` then does a strict `encode("utf-8")` on it — so
    refusing such a path at its own gate still ended in a `UnicodeEncodeError`
    with no `OKF0xx` line, one layer past the gate. Every diagnostic is built
    here, so one call closes every sink. It is a no-op for an ASCII path.
    """
    normalized_path = _utf8_safe(path.replace("\\", "/"))
    return Diagnostic(code=code, path=normalized_path, message=message)


def _sort_diagnostics(diagnostics: Iterable[Diagnostic]) -> list[Diagnostic]:
    return sorted(
        diagnostics,
        key=lambda item: (
            DIAGNOSTIC_ORDER[item.code],
            unicodedata.normalize("NFC", item.path).encode("utf-8"),
            item.message,
        ),
    )
