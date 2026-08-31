"""Direct-source manifest admission.

The direct route intentionally has a narrower manifest profile than a
catalogue pack.  Keep this boundary here rather than encoding it in the shared
schema: the bundled validator does not support conditional schema constructs.
"""

from __future__ import annotations

import contextlib
import json
import shlex
import shutil
import stat
import tempfile
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Any

from agentbundle.bounded_metadata import (
    BoundedMetadataError,
    parse_bounded_metadata,
    parse_bounded_toml,
)
from agentbundle.build.validate import validate
from agentbundle.catalogue_tooling.diagnostics import (
    BUDGET_CODES,
    DiagnosticCode,
    make_direct_diagnostic,
)
from agentbundle.catalogue_tooling.file_safety import (
    BoundExceeded,
    UnsafeContentError,
    read_confined_regular_file,
    walk_confined_regular_files,
)
from agentbundle.catalogue_tooling.results import Diagnostic, Severity
from agentbundle.safety import write_jailed

MANIFESTLESS_VERSION_SENTINEL = "0.0.0"

# Family-2 limits are deliberately module constants.  The corpus fixture and
# AC36 harness import them, so a bound change cannot silently leave either
# evidence source measuring an old value.
DIRECT_MAX_ENTRIES = 2_500
DIRECT_MAX_DEPTH = 12
DIRECT_MAX_FILES = 1_000
DIRECT_MAX_SELECTED_SKILLS = 500
DIRECT_MAX_FILE_BYTES = 1024 * 1024
DIRECT_MAX_TOTAL_BYTES = 25 * 1024 * 1024

_MARKER_KINDS = {
    "catalogue.toml": False,
    "packs": True,
    "pack.toml": False,
    "SKILL.md": False,
    "skills": True,
    ".claude/skills": True,
}
_PAYLOAD_DIRECTORIES = frozenset({"scripts", "references", "assets", "evals"})

_DIRECT_TOP_LEVEL_KEYS = frozenset({"schema", "pack"})
_DIRECT_PACK_KEYS = frozenset(
    {
        "name",
        "version",
        "description",
        "readme",
        "display_name",
        "license",
        "categories",
        "keywords",
        "maintainers",
        "links",
        "metadata",
        "install",
    }
)
_DIRECT_INSTALL_KEYS = frozenset({"default-scope", "allowed-scopes"})


class DirectManifestError(ValueError):
    """Raised when a direct pack manifest is outside the supported profile."""


@dataclass(frozen=True)
class MeasuredFile:
    """A direct file observed once through the confined read primitive."""

    path: Path
    data: bytes
    mode: int


@dataclass(frozen=True)
class DirectSkill:
    """One admitted skill envelope and the files that comprise it."""

    name: str
    envelope: Path
    files: tuple[MeasuredFile, ...]


@dataclass(frozen=True)
class DirectClassification:
    """The direct-source shape selected before normalization or projection."""

    shape: str
    root: Path
    collection_root: Path | None
    skills: tuple[DirectSkill, ...]
    named_files: tuple[MeasuredFile, ...]
    entries: int
    files: int
    total_bytes: int


class DirectAdmissionError(ValueError):
    """A fail-closed direct admission refusal with its stable diagnostic."""

    def __init__(self, diagnostic: Diagnostic) -> None:
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


@dataclass(frozen=True)
class MeasuredPathProbe:
    """A marker probe result containing only classification-safe facts."""

    exists: bool
    is_directory: bool


def probe_measured_path(root: Path, relative: str, *, directory: bool) -> MeasuredPathProbe:
    """Refuse an unsafe fixed marker without exposing its metadata to callers.

    This is the only direct-module marker probe.  It intentionally returns no
    stat result, mode, size, digest, or bytes: admitted file observations flow
    exclusively through ``read_confined_regular_file``.
    """

    path = root / relative
    try:
        inspected = path.lstat()
    except FileNotFoundError:
        return MeasuredPathProbe(exists=False, is_directory=False)
    except OSError as exc:
        raise _refusal(
            DiagnosticCode.CAT_D010,
            f"direct source marker cannot be inspected: {relative}",
        ) from exc
    if stat.S_ISLNK(inspected.st_mode) or _is_reparse_point(inspected):
        raise _refusal(
            DiagnosticCode.CAT_D009,
            f"measured path is link-like: {relative}",
            path=relative,
        )
    actual_directory = stat.S_ISDIR(inspected.st_mode)
    if actual_directory != directory:
        kind = "directory" if directory else "regular file"
        raise _refusal(
            DiagnosticCode.CAT_D009,
            f"measured path must be a {kind}: {relative}",
            path=relative,
        )
    if not directory and not stat.S_ISREG(inspected.st_mode):
        raise _refusal(
            DiagnosticCode.CAT_D009,
            f"measured path must be a regular file: {relative}",
            path=relative,
        )
    try:
        path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise _refusal(
            DiagnosticCode.CAT_D010,
            f"direct source marker changed during admission: {relative}",
        ) from exc
    return MeasuredPathProbe(exists=True, is_directory=actual_directory)


def classify_direct_source(root: Path) -> DirectClassification:
    """Classify and inventory a resolved local direct-source root.

    The caller supplies the resolved source root.  Repository context outside
    the fixed marker set is intentionally never inspected or counted.
    """

    markers = {
        name: probe_measured_path(root, name, directory=directory)
        for name, directory in _MARKER_KINDS.items()
    }
    catalogue = markers["catalogue.toml"].exists
    packs = markers["packs"].exists
    if catalogue and packs:
        raise _refusal(
            DiagnosticCode.CAT_D009,
            "this is a catalogue repository, not a direct source",
            path=str(root),
            remediation=(
                "Install from it as a catalogue: "
                f"{recovery_command('agentbundle', 'install', str(root), '--pack', 'NAME')}"
            ),
        )
    if catalogue or packs:
        raise _refusal(
            DiagnosticCode.CAT_D009,
            "partial catalogue markers are not a direct source",
        )

    collection_root = _select_collection_root(root, markers)
    has_pack = markers["pack.toml"].exists
    has_skill = markers["SKILL.md"].exists
    if has_pack and has_skill:
        raise _refusal(
            DiagnosticCode.CAT_D009,
            "direct source cannot contain both pack.toml and root SKILL.md",
        )
    if has_pack:
        if collection_root is None:
            raise _refusal(
                DiagnosticCode.CAT_D009,
                "direct pack requires a skills collection root",
            )
        return _inventory_collection(root, collection_root, "direct-pack", has_pack=True)
    if collection_root is not None:
        if has_skill:
            raise _refusal(
                DiagnosticCode.CAT_D009,
                "collection root overlaps root SKILL.md",
            )
        return _inventory_collection(root, collection_root, "collection", has_pack=False)
    if has_skill:
        return _inventory_root_skill(root)
    raise _refusal(DiagnosticCode.CAT_D009, "direct source has no supported shape")


# Set by acquisition for a remote source, so a root-single takes the repository
# name rather than the archive's `<repo>-<ref>` wrapper directory. AC1/E17: the
# wrapper encodes the commit, so using it would change the installed identity on
# every upgrade — the instability that argued for the frontmatter name before
# the corpus ruled that out.
_REMOTE_ROOT_IDENTITY: dict[Path, str] = {}


def declare_remote_root_identity(root: Path, identity: str) -> None:
    """Record the stable identity for an acquired remote root-single."""

    _REMOTE_ROOT_IDENTITY[root] = identity


def admit_direct_source(root: Path) -> DirectClassification:
    """Run the shared direct admission entry point used by validate and install."""

    return classify_direct_source(root)


def _select_collection_root(
    root: Path, markers: dict[str, MeasuredPathProbe]
) -> Path | None:
    """Choose the sole E14 collection root or refuse ambiguity."""

    roots = [name for name in ("skills", ".claude/skills") if markers[name].exists]
    if len(roots) > 1:
        raise _refusal(
            DiagnosticCode.CAT_D009,
            "ambiguous collection roots: skills and .claude/skills",
            remediation=(
                "This source offers two collection roots and the choice changes "
                "what is installed. Point at one of them directly."
            ),
        )
    return root / roots[0] if roots else None


def _inventory_collection(
    root: Path, collection_root: Path, shape: str, *, has_pack: bool
) -> DirectClassification:
    """Inventory an E14 collection using one bounded confined traversal."""

    paths, entries = _enumerate(root, collection_root, 0)
    by_envelope: dict[Path, list[Path]] = {}
    for path in paths:
        relative = path.relative_to(collection_root)
        parts = relative.parts
        if len(parts) < 2:
            # A loose file directly under the collection root (README.md,
            # LICENSE, REQUESTS.md) is repository context, not envelope
            # content. Ignore it; refusing here refused whole repositories
            # over one stray file.
            continue
        if parts[-1] == "SKILL.md":
            if len(parts) == 2:
                envelope = collection_root / parts[0]
            elif len(parts) == 3:
                envelope = collection_root / parts[0] / parts[1]
            else:
                raise _refusal(
                    DiagnosticCode.CAT_D009,
                    f"nested skill envelope: {relative}",
                    path=relative.as_posix(),
                )
            by_envelope.setdefault(envelope, []).append(path)

    if not by_envelope:
        raise _refusal(DiagnosticCode.CAT_D009, "collection root has no skill envelopes")
    _enforce_files(len(paths) + int(has_pack))
    _enforce_envelope_depths(root, by_envelope, paths)
    skills = _build_envelopes(root, by_envelope, paths)
    _enforce_selected_skills(len(skills))
    _enforce_unique_skill_names(skills)
    named_files: tuple[MeasuredFile, ...] = ()
    if has_pack:
        named_files = (_read_named(root, root / "pack.toml"),)
        try:
            validate_direct_manifest(parse_bounded_toml(named_files[0].data))
        except (BoundedMetadataError, DirectManifestError) as exc:
            raise _refusal(
                DiagnosticCode.CAT_D009, f"invalid direct pack manifest: {exc}"
            ) from exc
    all_files = tuple(file for skill in skills for file in skill.files) + named_files
    _enforce_total_bytes(all_files)
    total_entries = entries + int(has_pack)
    return DirectClassification(
        shape,
        root,
        collection_root,
        skills,
        named_files,
        total_entries,
        len(all_files),
        _total_bytes(all_files),
    )


def _inventory_root_skill(root: Path) -> DirectClassification:
    """Inventory a root single/local skill without walking repository context."""

    named = _read_named(root, root / "SKILL.md")
    # Root SKILL.md is a named measured file.  It is never enumerated, but it
    # still consumes one shape entry just like a direct-pack root pack.toml.
    entries = 1
    paths: list[Path] = []
    for payload in sorted(_PAYLOAD_DIRECTORIES):
        probe = probe_measured_path(root, payload, directory=True)
        if not probe.exists:
            continue
        found, entries = _enumerate(root, root / payload, entries)
        paths.extend(found)
    _enforce_files(len(paths) + 1)
    _enforce_root_skill_depths(root, paths)
    files = [named] + _read_bounded(root, paths, carried=len(named.data))
    skill = _make_skill(root, root, files)
    _enforce_total_bytes(files)
    return DirectClassification(
        "root-single",
        root,
        None,
        (skill,),
        (named,),
        entries,
        len(files),
        _total_bytes(files),
    )


def _enumerate(root: Path, directory: Path, entries_used: int) -> tuple[list[Path], int]:
    """Enumerate one measured directory with its remaining entry allowance."""

    try:
        walk = walk_confined_regular_files(
            root,
            directory,
            max_entries=DIRECT_MAX_ENTRIES - entries_used,
        )
    except BoundExceeded as exc:
        raise _bound_refusal(exc) from exc
    except UnsafeContentError as exc:
        raise _refusal(DiagnosticCode.CAT_D009, str(exc), path=exc.path) from exc
    # Thread the entries the traversal actually consumed, not the files it
    # returned. A tree of 1,400 directories consumes 1,400 entries and returns
    # no files, so counting files lets two such directories pass a shared
    # 2,500-entry bound with 2,800 entries between them — under-counting, which
    # is the unsafe direction.
    return walk.files, entries_used + walk.entries_seen


def _build_envelopes(
    root: Path, by_envelope: dict[Path, list[Path]], paths: list[Path]
) -> tuple[DirectSkill, ...]:
    """Attach only legal measured files to each collection envelope."""

    # Bucket every path to its owning envelope in ONE pass, by walking each
    # path's own parents. Re-scanning all paths per envelope is quadratic:
    # at the 500-skill and 1,000-file limits that is 500,000 exception-driven
    # `relative_to` calls, which measured 27.7s. Walking parents is bounded by
    # the depth budget instead, and measures 0.05s on the same shape.
    envelope_set = set(by_envelope)
    buckets: dict[Path, list[Path]] = {envelope: [] for envelope in envelope_set}
    for path in paths:
        for parent in path.parents:
            if parent in envelope_set:
                buckets[parent].append(path)
                break

    skills: list[DirectSkill] = []
    # Carried across envelopes, not reset per envelope: the budget is a
    # whole-source bound, so 500 envelopes each just under it would otherwise
    # all be read before the cross-envelope total was ever computed.
    running_total = 0
    for envelope in sorted(envelope_set, key=lambda candidate: candidate.as_posix()):
        payload_paths = sorted(buckets[envelope], key=lambda item: item.as_posix())
        for path in payload_paths:
            relative = path.relative_to(envelope)
            # The envelope is a subtree, not an allowlist of four directories:
            # the Agent Skills spec's own example puts `reference.md` and
            # `examples.md` at the envelope root. Hidden entries still refuse.
            if any(part.startswith(".") for part in relative.parts):
                raise _refusal(
                    DiagnosticCode.CAT_D009,
                    f"hidden entry in skill envelope: {relative}",
                    path=path.relative_to(root).as_posix(),
                )
        files = _read_bounded(root, payload_paths, carried=running_total)
        running_total += sum(len(measured.data) for measured in files)
        skills.append(_make_skill(root, envelope, files))
    assigned = {file.path for skill in skills for file in skill.files}
    for path in paths:
        if path not in assigned:
            raise _refusal(
                DiagnosticCode.CAT_D009,
                f"unowned collection file: {path.relative_to(root)}",
                path=path.relative_to(root).as_posix(),
            )
    return tuple(skills)


def _enforce_envelope_depths(
    root: Path, by_envelope: dict[Path, list[Path]], paths: list[Path]
) -> None:
    """Apply E15 before any payload file is read."""

    # One pass over paths, walking each path's own parents to find its owning
    # envelope, rather than re-scanning every path for every envelope. E15
    # measures depth from the envelope, so the owning envelope is the only one
    # that can produce a verdict for a given path.
    envelope_set = set(by_envelope)
    for path in paths:
        for depth, parent in enumerate(path.parents, start=1):
            if parent in envelope_set:
                if depth > DIRECT_MAX_DEPTH:
                    raise _budget_refusal(
                        "depth",
                        DIRECT_MAX_DEPTH,
                        depth,
                        path.relative_to(root).as_posix(),
                    )
                break


def _enforce_root_skill_depths(root: Path, paths: list[Path]) -> None:
    """Apply E15 to payload paths below a root-single skill envelope."""

    for path in paths:
        observed = len(path.relative_to(root).parts)
        if observed > DIRECT_MAX_DEPTH:
            raise _budget_refusal(
                "depth", DIRECT_MAX_DEPTH, observed, path.relative_to(root).as_posix()
            )


def _within_envelope(path: Path, envelope: Path) -> bool:
    """Return whether a known traversed path belongs below an envelope."""

    try:
        path.relative_to(envelope)
    except ValueError:
        return False
    return True


def _make_skill(root: Path, envelope: Path, files: list[MeasuredFile]) -> DirectSkill:
    """Parse a skill frontmatter record and enforce its envelope depth."""

    skill_file = next((file for file in files if file.path == envelope / "SKILL.md"), None)
    if skill_file is None:
        raise _refusal(
            DiagnosticCode.CAT_D009,
            f"skill envelope is missing SKILL.md: {envelope.relative_to(root)}",
        )
    try:
        metadata = parse_bounded_metadata(skill_file.data)
    except BoundedMetadataError as exc:
        raise _refusal(DiagnosticCode.CAT_D009, f"invalid skill metadata: {exc}") from exc
    # Identity is the envelope DIRECTORY name, never the frontmatter `name`.
    # The Agent Skills spec defines `name` as a display string that defaults to
    # the directory name, so it is optional and may legitimately differ or carry
    # spaces and capitals ("Eventbrite Automation"). Holding it to the slug
    # grammar refused 6% of a 2,545-skill corpus over a label.
    identity = (
        envelope.name
        if envelope != root
        else _REMOTE_ROOT_IDENTITY.get(root, root.name)
    )
    if not _is_direct_identity(identity):
        raise _refusal(
            DiagnosticCode.CAT_D011,
            f"invalid direct identity: {identity}",
            path=identity,
        )
    display = metadata.get("name")
    if display is not None and not isinstance(display, str):
        raise _refusal(
            DiagnosticCode.CAT_D009,
            f"skill display name must be a string: {envelope.name}",
        )
    return DirectSkill(
        identity, envelope, tuple(sorted(files, key=lambda file: file.path.as_posix()))
    )


def _read_named(root: Path, path: Path) -> MeasuredFile:
    """Observe a direct file once, applying the direct per-file byte limit."""

    # Before the read, so the refusal precedes enumeration, digest, and any
    # diagnostic that would otherwise render the offending segment.
    enforce_logical_path(path.relative_to(root).as_posix(), root)
    try:
        data, mode = read_confined_regular_file(
            root, path, max_bytes=DIRECT_MAX_FILE_BYTES, include_mode=True
        )
    except BoundExceeded as exc:
        raise _bound_refusal(exc) from exc
    except UnsafeContentError as exc:
        relative = path.relative_to(root).as_posix()
        raise _refusal(DiagnosticCode.CAT_D009, str(exc), path=relative) from exc
    return MeasuredFile(path, data, mode)


def _enforce_selected_skills(count: int) -> None:
    """Refuse a collection that selects more skills than the shape budget."""

    if count > DIRECT_MAX_SELECTED_SKILLS:
        raise _budget_refusal("selected-skills", DIRECT_MAX_SELECTED_SKILLS, count)


def _enforce_files(count: int) -> None:
    """Apply the shape-wide file budget before direct file reads begin."""

    if count > DIRECT_MAX_FILES:
        raise _budget_refusal("files", DIRECT_MAX_FILES, count)


def _enforce_unique_skill_names(skills: tuple[DirectSkill, ...]) -> None:
    """Refuse duplicate leaf identities before selection or projection."""

    # AC11 compares NFC-normalized, case-folded names rather than raw ones. A
    # case-insensitive filesystem collapses `Alpha` and `alpha` onto one
    # directory, so admitting both installs one skill over the other silently.
    seen: dict[str, DirectSkill] = {}
    for skill in skills:
        folded = unicodedata.normalize("NFC", skill.name).casefold()
        existing = seen.get(folded)
        if existing is not None:
            raise _refusal(
                DiagnosticCode.CAT_D011,
                "duplicate direct identity "
                f"{skill.name}: {existing.envelope} and {skill.envelope}",
            )
        seen[folded] = skill


def _enforce_total_bytes(files: tuple[MeasuredFile, ...] | list[MeasuredFile]) -> None:
    """Apply the cumulative byte budget after every selected file is read."""

    observed = _total_bytes(files)
    if observed > DIRECT_MAX_TOTAL_BYTES:
        raise _budget_refusal("total-bytes", DIRECT_MAX_TOTAL_BYTES, observed)


def _read_bounded(root: Path, paths: list[Path], carried: int = 0) -> list[MeasuredFile]:
    """Read files, refusing as soon as the running total breaks the budget.

    The budget is checked *inside* the loop rather than over the finished list.
    Checked afterwards, a source of 1,000 files at the 1 MiB per-file limit is
    fully materialised — roughly 1 GiB resident — before a 25 MiB budget can
    refuse it, so the bound that exists to cap the cost is paid in full before
    it applies. Checked here, the same source refuses at the 26th file.
    """

    files: list[MeasuredFile] = []
    total = carried
    for path in paths:
        measured = _read_named(root, path)
        total += len(measured.data)
        if total > DIRECT_MAX_TOTAL_BYTES:
            raise _budget_refusal("total-bytes", DIRECT_MAX_TOTAL_BYTES, total)
        files.append(measured)
    return files


def _total_bytes(files: tuple[MeasuredFile, ...] | list[MeasuredFile]) -> int:
    """Return the selected-file byte total without a second filesystem read."""

    return sum(len(file.data) for file in files)


def _bound_refusal(exc: BoundExceeded) -> DirectAdmissionError:
    """Map the helper's typed breach through the direct budget registry."""

    return _budget_refusal(exc.budget, exc.limit, exc.observed)


def _budget_refusal(
    budget: str,
    limit: int,
    observed: int | None,
    path: str | None = None,
) -> DirectAdmissionError:
    """Create one registered diagnostic for a named Family-2 budget breach."""

    code = BUDGET_CODES[budget]
    detail = f"{budget} exceeds limit {limit}"
    if observed is not None:
        detail += f" (observed {observed})"
    return _refusal(code, detail, path=path)


def _refusal(
    code: DiagnosticCode,
    message: str,
    *,
    path: str | None = None,
    remediation: str | None = None,
) -> DirectAdmissionError:
    """Create a direct error using the typed direct diagnostic constructor."""

    return DirectAdmissionError(
        make_direct_diagnostic(
            code, Severity.ERROR, message, path=path, remediation=remediation
        )
    )


def enforce_logical_path(relative: str, root: Path) -> None:
    """Refuse a logical path segment AC14 forbids, before anything reads it.

    Three classes, all checked before enumeration, digest, normalization, or
    diagnostic emission, because each one reaches a sink that cannot render it
    safely:

    - **C0, C1, DEL.** Terminal control and log forgery in any surface that
      prints the path.
    - **Surrogates.** `tarfile` decodes member names with
      `errors="surrogateescape"`, so a lone surrogate survives extraction and
      then raises `UnicodeEncodeError` at the first `.encode("utf-8")` — inside
      the digest, far from the cause.
    - **Non-NFC.** Two spellings of one name digest differently, so the same
      tree can produce two digests depending on the filesystem that stored it.
    """

    for segment in PurePosixPath(relative).parts:
        for character in segment:
            point = ord(character)
            if point < 0x20 or point == 0x7F or 0x80 <= point <= 0x9F:
                raise _refusal(
                    DiagnosticCode.CAT_D018,
                    f"path segment carries a control code point U+{point:04X}",
                    path=str(root),
                    remediation="Ask the publisher to rename the offending file.",
                )
            if 0xD800 <= point <= 0xDFFF:
                raise _refusal(
                    DiagnosticCode.CAT_D018,
                    f"path segment carries a surrogate code point U+{point:04X}",
                    path=str(root),
                    remediation="Ask the publisher to rename the offending file.",
                )
        if unicodedata.normalize("NFC", segment) != segment:
            raise _refusal(
                DiagnosticCode.CAT_D018,
                f"path segment is not NFC-normalized: {segment!r}",
                path=str(root),
                remediation="Ask the publisher to rename the offending file.",
            )


def _is_reparse_point(inspected: object) -> bool:
    """Return the platform reparse-point marker without exporting stat details."""

    attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(inspected, "st_file_attributes", 0) & attribute)


def _is_direct_identity(name: str) -> bool:
    """Validate the manifestless/direct-pack identity grammar locally."""

    if len(name) > 64:
        return False
    return bool(name) and name[0].isascii() and name[0].isalnum() and all(
        character.isascii() and (character.islower() or character.isdigit() or character == "-")
        for character in name
    )


def validate_direct_manifest(
    manifest: dict[str, Any], *, schema: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Validate and return a schema-1, skills-only direct pack manifest.

    Catalogue callers continue to validate against the shared schema directly,
    where an absent ``schema`` means schema major 1.  Direct publishers must
    state that major explicitly so a future major cannot be interpreted under
    this route's narrower rules.
    """

    schema_major = manifest.get("schema")
    if type(schema_major) is not int or schema_major != 1:
        raise DirectManifestError("direct pack.toml must declare schema = 1")

    _reject_unknown(manifest, _DIRECT_TOP_LEVEL_KEYS, "pack.toml")

    pack = manifest.get("pack")
    if not isinstance(pack, dict):
        raise DirectManifestError("direct pack.toml must contain a [pack] table")
    _reject_unknown(pack, _DIRECT_PACK_KEYS, "[pack]")

    install = pack.get("install")
    if install is not None:
        if not isinstance(install, dict):
            raise DirectManifestError("[pack.install] must be a table")
        _reject_unknown(install, _DIRECT_INSTALL_KEYS, "[pack.install]")
        _validate_direct_install_scope(install)

    if pack.get("version") == MANIFESTLESS_VERSION_SENTINEL:
        raise DirectManifestError(
            f"direct pack.toml version must not be {MANIFESTLESS_VERSION_SENTINEL!r}"
        )

    active_schema = schema if schema is not None else _load_pack_schema()
    errors = validate(manifest, active_schema)
    if errors:
        raise DirectManifestError(f"direct pack.toml fails schema validation: {errors[0]}")
    return manifest


def _load_pack_schema() -> dict[str, Any]:
    """Load the bundled shared pack schema for direct admission."""

    return json.loads(
        files("agentbundle").joinpath("_data/pack.schema.json").read_text(
            encoding="utf-8"
        )
    )


def _reject_unknown(
    values: dict[str, Any], allowed: frozenset[str], label: str
) -> None:
    """Refuse fields outside one direct-route manifest table profile."""

    unknown = sorted(set(values) - allowed)
    if unknown:
        raise DirectManifestError(f"{label}: unsupported direct field(s): {unknown}")


def _validate_direct_install_scope(install: dict[str, Any]) -> None:
    """Preserve the local-scope opt-in rule the shared subset cannot express."""

    allowed_scopes = install.get("allowed-scopes")
    if (
        isinstance(allowed_scopes, list)
        and "local" in allowed_scopes
        and "repo" not in allowed_scopes
    ):
        raise DirectManifestError(
            "[pack.install]: local allowed-scope requires repo allowed-scope"
        )


@dataclass(frozen=True)
class DirectNormalization:
    """One bounded canonical pack tree materialised from an admitted source."""

    root: Path
    skills: tuple[str, ...]
    files: int
    total_bytes: int


@contextlib.contextmanager
def normalize_direct_source(
    classification: DirectClassification,
    *,
    parent: Path | None = None,
) -> Iterator[DirectNormalization]:
    """Materialise the canonical `skills/<leaf>/` tree for an admitted source.

    Two properties carry the criteria and are worth stating, because both are
    invisible in the happy path.

    First, every byte written here comes from `MeasuredFile.data` — the bytes
    already read and measured during admission — and never from a second read
    of the source.  A source that is replaced between admission and copy
    therefore cannot change what is installed, which is what makes the digest
    describe the installed tree rather than a tree that briefly existed.  This
    is why no `shutil` copy API appears on the direct route at all.

    Second, the tree is keyed on `skill.name`, the envelope's own directory
    name.  A collection's optional category level disappears by construction
    rather than by a stripping rule, because the category never contributes to
    the destination path.  `_project_direct_directory` projects exactly one
    `skills/` level, so a surviving category would not project.

    The tree is removed on the way out whether the caller succeeds or raises,
    so a refusal downstream leaves nothing behind.
    """

    temporary = Path(tempfile.mkdtemp(prefix="agentbundle-direct-", dir=parent))
    try:
        written = 0
        total = 0
        for skill in classification.skills:
            for measured in skill.files:
                relative = measured.path.relative_to(skill.envelope)
                destination = PurePosixPath("skills") / skill.name / PurePosixPath(
                    *relative.parts
                )
                write_jailed(
                    temporary,
                    str(destination),
                    measured.data,
                    mode=_canonical_mode(measured.mode),
                    allowed_prefixes=["skills/"],
                )
                written += 1
                total += len(measured.data)
        yield DirectNormalization(
            root=temporary,
            skills=tuple(sorted(skill.name for skill in classification.skills)),
            files=written,
            total_bytes=total,
        )
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def _canonical_mode(mode: int) -> int:
    """Reduce a source mode to the two modes the canonical tree may carry.

    Only the owner-executable bit is honoured, and it is honoured as a whole:
    a file is projected 0o755 or 0o644 and nothing else.  Carrying the source
    mode through verbatim would let a direct source install setuid, setgid, or
    group- and world-writable files, none of which a skill needs.
    """

    return 0o755 if mode & stat.S_IXUSR else 0o644


@dataclass(frozen=True)
class DirectAdmission:
    """The result of the one admission entry point both routes call."""

    ok: bool
    classification: DirectClassification | None
    diagnostics: tuple[Diagnostic, ...]


def validate_direct_source(root: Path) -> DirectAdmission:
    """Admit a direct source without raising: the shared validate/install seam.

    AC14 requires validation and install preflight to yield *identical*
    diagnostics.  The cheapest way to guarantee that is for neither to own a
    check: both call this, and it is the only place `admit_direct_source`'s
    refusal is turned into a reportable result.  A second implementation on the
    install side would agree on the day it was written and drift silently
    afterwards, which is precisely the failure AC14 names.
    """

    try:
        classification = admit_direct_source(root)
    except DirectAdmissionError as exc:
        # AC27 requires an offending path on every refusal. A raise site that
        # knows a more specific path supplies it; the rest describe the source
        # as a whole, so the source stands in rather than a null reaching the
        # reader. Before a root exists this is the validated source string,
        # which is what the criterion asks for.
        diagnostic = exc.diagnostic
        if not diagnostic.path:
            diagnostic.path = str(root)
        return DirectAdmission(False, None, (diagnostic,))
    return DirectAdmission(True, classification, ())


def recovery_command(*parts: str) -> str:
    """Build a printed recovery command with every interpolated value quoted.

    AC11 requires shell-quoting for *every* interpolated value — publisher
    strings, source strings, and paths alike — because a recovery command is
    text a reader is invited to paste into a shell.  A publisher-chosen skill
    name containing a space, a quote, or a `;` is otherwise a command the
    adopter runs on the publisher's behalf.
    """

    return " ".join(shlex.quote(part) for part in parts)
