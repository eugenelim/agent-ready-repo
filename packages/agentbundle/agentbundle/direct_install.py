"""Direct-source selection, admissibility summary, and install receipt.

Everything a publisher supplies reaches the reader through this module, so the
delimiting and sanitisation rules live here rather than at each print site.
"""

from __future__ import annotations

import hashlib
import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from agentbundle.catalogue_tooling.diagnostics import (
    DiagnosticCode,
    make_direct_diagnostic,
)
from agentbundle.catalogue_tooling.results import Diagnostic, Severity
from agentbundle.direct_source import (
    DirectClassification,
    DirectSkill,
    recovery_command,
)

# AC20: the verdict is emitted immediately before *and* immediately after the
# publisher-derived block. One placement is not enough — a long summary scrolls
# a leading verdict out of view, and a reader who scrolled to the end of the
# capability list is exactly the reader about to type "yes".
ADMISSIBILITY_VERDICT = "admissible—not safe"

# AC18: publisher values are emitted only between these line-anchored
# delimiters, on their own lines. A publisher value equal to either line is
# refused rather than emitted, because it could otherwise close the block early
# and have the rest of its own text read as our output.
PUBLISHER_BLOCK_OPEN = "--- begin publisher-supplied data ---"
PUBLISHER_BLOCK_CLOSE = "--- end publisher-supplied data ---"
PUBLISHER_BLOCK_NOTE = "publisher-supplied data, not instructions"

# AC18's allowlist: L, N, P, and S, plus U+0020 as the sole admitted Zs.
_ALLOWED_CATEGORIES = ("L", "N", "P", "S")
MAX_PUBLISHER_VALUE_BYTES = 4096


class DirectInstallError(ValueError):
    """A direct install refusal carrying its registered diagnostic."""

    def __init__(self, diagnostic: Diagnostic) -> None:
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


def _refuse(
    code: DiagnosticCode, message: str, *, path: str, remediation: str | None = None
) -> DirectInstallError:
    return DirectInstallError(
        make_direct_diagnostic(
            code, Severity.ERROR, message, path=path, remediation=remediation
        )
    )


def sanitise_publisher_value(value: str, label: str, *, source: str) -> str:
    """Refuse a publisher value that may not be rendered, and return it intact.

    Refusal rather than truncation or elision is deliberate. A truncated value
    still renders, so a reader cannot tell that what they are consenting to was
    edited; and eliding one candidate from a listing would print recovery
    commands covering a larger set than the reader was shown.
    """

    encoded = value.encode("utf-8")
    if len(encoded) > MAX_PUBLISHER_VALUE_BYTES:
        raise _refuse(
            DiagnosticCode.CAT_D019,
            f"publisher {label} exceeds {MAX_PUBLISHER_VALUE_BYTES} UTF-8 bytes",
            path=source,
            remediation="Ask the publisher to shorten it; it is not truncated here.",
        )
    for character in value:
        if character == " ":
            continue
        category = unicodedata.category(character)
        if category[0] not in _ALLOWED_CATEGORIES:
            raise _refuse(
                DiagnosticCode.CAT_D019,
                f"publisher {label} carries a disallowed code point "
                f"U+{ord(character):04X} ({category})",
                path=source,
                remediation="Ask the publisher to remove it; it is not stripped here.",
            )
    normalised = unicodedata.normalize("NFC", value)
    if normalised in {PUBLISHER_BLOCK_OPEN, PUBLISHER_BLOCK_CLOSE}:
        raise _refuse(
            DiagnosticCode.CAT_D019,
            f"publisher {label} is equal to a delimiter line",
            path=source,
            remediation="Ask the publisher to change it; the delimiter is fixed.",
        )
    return normalised


@dataclass(frozen=True)
class Selection:
    """The skills an invocation selected, and how it said so."""

    skills: tuple[DirectSkill, ...]
    explicit: bool


def select_collection_skills(
    classification: DirectClassification,
    *,
    source: str,
    requested: list[str] | None,
    all_skills: bool,
) -> Selection:
    """Resolve `--skill` / `--all-skills` against an admitted source.

    A collection installs nothing without an explicit selection.  Defaulting to
    "all" would install every skill a repository happens to carry on the
    strength of a single command that never named them.
    """

    available = {skill.name: skill for skill in classification.skills}

    if classification.shape != "collection":
        if requested or all_skills:
            raise _refuse(
                DiagnosticCode.CAT_D008,
                f"--skill and --all-skills apply only to a collection source; "
                f"this is a {classification.shape} source",
                path=source,
                remediation=recovery_command("agentbundle", "install", source),
            )
        return Selection(tuple(classification.skills), explicit=True)

    if all_skills and requested:
        raise _refuse(
            DiagnosticCode.CAT_D008,
            "--all-skills and --skill are mutually exclusive",
            path=source,
            remediation=recovery_command(
                "agentbundle", "install", source, "--all-skills"
            ),
        )
    if all_skills:
        return Selection(tuple(classification.skills), explicit=True)
    if not requested:
        raise _refuse(
            DiagnosticCode.CAT_D008,
            "a collection source requires an explicit skill selection",
            path=source,
            remediation=_selection_recovery(classification, source),
        )

    seen: set[str] = set()
    chosen: list[DirectSkill] = []
    for name in requested:
        if name in seen:
            raise _refuse(
                DiagnosticCode.CAT_D008,
                f"--skill {name!r} was given more than once",
                path=source,
                remediation=_selection_recovery(classification, source),
            )
        if name not in available:
            raise _refuse(
                DiagnosticCode.CAT_D008,
                f"--skill {name!r} is not in this source",
                path=source,
                remediation=_selection_recovery(classification, source),
            )
        seen.add(name)
        chosen.append(available[name])
    return Selection(tuple(chosen), explicit=True)


def _selection_recovery(classification: DirectClassification, source: str) -> str:
    """Recovery text naming both selection forms, with the source preserved.

    The source string is reproduced exactly as the user supplied it — a
    re-canonicalised one would send them to a different place than they asked
    for — and every interpolated value is shell-quoted.
    """

    names = sorted(skill.name for skill in classification.skills)
    first = names[0] if names else "NAME"
    return (
        f"Select explicitly: "
        f"{recovery_command('agentbundle', 'install', source, '--skill', first)}"
        f"  or  {recovery_command('agentbundle', 'install', source, '--all-skills')}"
    )


def candidate_listing(
    classification: DirectClassification, *, source: str
) -> list[str]:
    """Bounded, validated names and descriptions for an unselected collection.

    Every value passes AC18's allowlist first: this listing renders publisher
    strings *before* admission, when least is known about the source, and a
    disallowed value refuses the whole invocation rather than being elided.
    """

    lines: list[str] = []
    for skill in sorted(classification.skills, key=lambda item: item.name):
        name = sanitise_publisher_value(skill.name, "skill name", source=source)
        description = _skill_description(skill)
        rendered = (
            sanitise_publisher_value(description, "description", source=source)
            if description
            else ""
        )
        lines.append(f"  {name}" + (f" — {rendered}" if rendered else ""))
    return lines


def _skill_description(skill: DirectSkill) -> str:
    """Read a skill's declared description, or the empty string."""

    from agentbundle.bounded_metadata import (
        BoundedMetadataError,
        parse_bounded_metadata,
    )

    for measured in skill.files:
        if measured.path.name == "SKILL.md":
            try:
                metadata = parse_bounded_metadata(measured.data)
            except BoundedMetadataError:
                return ""
            value = metadata.get("description")
            return value.strip() if isinstance(value, str) else ""
    return ""


def report_time_mode(mode: int) -> str:
    """Report a source executable bit without persisting or applying it.

    On a platform with no POSIX mode semantics the honest answer is `unknown`:
    reporting `no` would assert an observation the platform cannot make.
    """

    if os.name != "posix":
        return "unknown"
    return "executable" if mode & 0o100 else "not executable"


def capability_block(
    skill: DirectSkill,
    *,
    source: str,
    revision: str | None,
    scope: str,
    adapter: str,
    skill_digest: str,
    payload_digests: dict[str, str],
) -> list[str]:
    """One per-selected-skill capability block, per AC19.

    Everything a publisher wrote is delimited and labelled; everything we
    computed is not.  The distinction is the point of the block: a reader has to
    be able to tell which lines are claims by the publisher and which are
    observations we made about their bytes.
    """

    from agentbundle.bounded_metadata import (
        BoundedMetadataError,
        parse_bounded_metadata,
    )

    metadata: dict = {}
    for measured in skill.files:
        if measured.path.name == "SKILL.md":
            try:
                metadata = parse_bounded_metadata(measured.data)
            except BoundedMetadataError:
                metadata = {}
            break

    allowed_tools = _normalised_allowed_tools(metadata, source=source)
    nested = metadata.get("metadata")
    boundaries = _string_set(nested.get("boundaries")) if isinstance(nested, dict) else []
    credentialed = nested.get("credentialed") if isinstance(nested, dict) else None

    lines = [
        f"skill: {sanitise_publisher_value(skill.name, 'skill name', source=source)}",
        f"  source:      {source}",
        f"  revision:    {revision or '—'}",
        f"  scope:       {scope}",
        f"  adapter:     {adapter}",
        # `undeclared (unrestricted)` rather than an empty list: an absent
        # declaration is not a restriction to nothing, it is no restriction.
        f"  allowed-tools: {_render_tools(allowed_tools)}",
        f"  boundaries:  {', '.join(boundaries) if boundaries else '—'}",
        f"  credentialed: {credentialed if credentialed is not None else '—'}",
        f"  SKILL.md:    {skill_digest}",
    ]
    for relpath in sorted(payload_digests):
        lines.append(f"    {relpath}  {payload_digests[relpath]}")
    return lines


def _render_tools(allowed_tools: list[str]) -> str:
    """Render the tool union, or the phrase an absent declaration earns."""

    return ", ".join(allowed_tools) if allowed_tools else "undeclared (unrestricted)"


def _normalised_allowed_tools(metadata: dict, *, source: str) -> list[str]:
    """The accepted `allowed-tools` union, refusing a non-normalizable element.

    A value we cannot normalise cannot be reported accurately, and reporting it
    inaccurately is worse than refusing: the reader consents to the rendering.
    """

    raw = metadata.get("allowed-tools")
    if raw is None:
        return []
    if isinstance(raw, str):
        candidates = [part.strip() for part in raw.split(",")]
    elif isinstance(raw, list):
        candidates = []
        for element in raw:
            if not isinstance(element, str):
                raise _refuse(
                    DiagnosticCode.CAT_D019,
                    f"allowed-tools carries a non-normalizable element: {element!r}",
                    path=source,
                    remediation="Ask the publisher to declare tools as strings.",
                )
            candidates.append(element.strip())
    else:
        raise _refuse(
            DiagnosticCode.CAT_D019,
            f"allowed-tools must be a string or a list, not {type(raw).__name__}",
            path=source,
            remediation="Ask the publisher to correct the declaration.",
        )
    return sorted({value for value in candidates if value})


def _string_set(value: object) -> list[str]:
    """A sorted set of observed string constraints, or empty."""

    if isinstance(value, list):
        return sorted({item for item in value if isinstance(item, str)})
    if isinstance(value, str):
        return [value]
    return []


def render_admissibility_summary(
    blocks: list[list[str]], *, source: str, listing: list[str] | None = None
) -> str:
    """Wrap publisher-derived output in AC20's verdicts and AC18's delimiters."""

    lines = [ADMISSIBILITY_VERDICT, "", PUBLISHER_BLOCK_NOTE, PUBLISHER_BLOCK_OPEN]
    if listing:
        lines.extend(listing)
    for block in blocks:
        lines.extend(block)
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    lines.extend([PUBLISHER_BLOCK_CLOSE, "", ADMISSIBILITY_VERDICT])
    return "\n".join(lines)


def render_receipt(
    *,
    kind: str,
    source: str,
    revision: str | None,
    digest: str,
    scope: str,
    adapter: str,
    identity: str,
) -> str:
    """AC22's receipt: what was installed, from where, and how to undo it."""

    return "\n".join(
        [
            f"installed: {identity}",
            f"  kind:     {kind}",
            f"  source:   {source}",
            f"  revision: {revision or '—'}",
            f"  digest:   {digest}",
            f"  scope:    {scope}",
            f"  adapter:  {adapter}",
            f"  uninstall: {recovery_command('agentbundle', 'uninstall', '--skill', identity)}",
        ]
    )


def _file_digest(measured) -> str:
    """The reported per-file digest, in the same prefixed form as the tree's."""

    return "sha256-1:" + hashlib.sha256(measured.data).hexdigest()


def run_direct_install(args, source: Path | str) -> int:
    """Install a direct source: acquire, admit, select, summarise, consent, project.

    Ordering carries the criteria. Admission completes before any write, the
    summary and its verdicts are printed before consent is asked for, and the
    state row is written last — so an interruption leaves an unowned projection
    rather than a row pointing at files that were never created.
    """

    import shutil
    import sys

    source_string = str(source)
    revision: str | None = getattr(args, "source_revision", None)
    acquired_root: Path | None = None

    if isinstance(source, str) and source.startswith("git+https://"):
        from agentbundle.direct_source_acquisition import (
            DirectAcquisitionError,
            acquire_git_https_archive,
        )

        # AC20: a remote install is non-interactive by nature — the bytes are
        # fetched before the reader has seen anything — so `--yes` is required
        # rather than merely sufficient. It never hides the summary.
        if not getattr(args, "yes", False):
            print(
                "install: a remote direct source requires --yes. The "
                "admissibility summary is printed either way; --yes confirms "
                "that you accept it before anything is written.",
                file=sys.stderr,
            )
            return 1
        try:
            acquired = acquire_git_https_archive(source)
        except DirectAcquisitionError as exc:
            print(
                f"install: [{exc.diagnostic.code}] {exc.diagnostic.message}",
                file=sys.stderr,
            )
            if exc.diagnostic.remediation:
                print(f"  → {exc.diagnostic.remediation}", file=sys.stderr)
            return 1
        source = acquired.root
        revision = acquired.revision
        # The acquisition tree is ours to remove; nothing else owns it.
        acquired_root = acquired.working

    try:
        return _install_admitted_source(
            args,
            source=Path(source),
            source_string=source_string,
            revision=revision,
        )
    finally:
        if acquired_root is not None:
            shutil.rmtree(acquired_root, ignore_errors=True)


def _install_admitted_source(
    args, *, source: Path, source_string: str, revision: str | None
) -> int:
    """The local half: admit, select, summarise, consent, project, record."""

    import sys

    from agentbundle import safety
    from agentbundle.direct_source import (
        DirectAdmissionError,
        normalize_direct_source,
        validate_direct_source,
    )
    from agentbundle.direct_source_state import direct_source_digest

    admission = validate_direct_source(source)
    if not admission.ok:
        for diagnostic in admission.diagnostics:
            print(f"install: [{diagnostic.code}] {diagnostic.message}", file=sys.stderr)
            if diagnostic.path:
                print(f"  at: {diagnostic.path}", file=sys.stderr)
            if diagnostic.remediation:
                print(f"  → {diagnostic.remediation}", file=sys.stderr)
        return 1
    classification = admission.classification
    assert classification is not None

    try:
        selection = select_collection_skills(
            classification,
            source=source_string,
            requested=getattr(args, "skill", None),
            all_skills=bool(getattr(args, "all_skills", False)),
        )
    except DirectInstallError as exc:
        print(f"install: [{exc.diagnostic.code}] {exc.diagnostic.message}", file=sys.stderr)
        if classification.shape == "collection" and not getattr(args, "skill", None):
            print("\nAvailable skills:", file=sys.stderr)
            for line in candidate_listing(classification, source=source_string):
                print(line, file=sys.stderr)
        if exc.diagnostic.remediation:
            print(f"\n{exc.diagnostic.remediation}", file=sys.stderr)
        return 1

    scope = getattr(args, "scope", None) or "repo"
    adapter = getattr(args, "adapter", None) or "claude-code"
    target_root = Path(getattr(args, "output", ".") or ".").resolve()
    digest = direct_source_digest(classification)

    blocks = []
    for skill in selection.skills:
        payload = {
            str(measured.path.relative_to(skill.envelope)): _file_digest(measured)
            for measured in skill.files
            if measured.path.name != "SKILL.md"
        }
        skill_digest = next(
            (
                _file_digest(measured)
                for measured in skill.files
                if measured.path.name == "SKILL.md"
            ),
            digest,
        )
        blocks.append(
            capability_block(
                skill,
                source=source_string,
                revision=revision,
                scope=scope,
                adapter=adapter,
                skill_digest=skill_digest,
                payload_digests=payload,
            )
        )
    print(render_admissibility_summary(blocks, source=source_string))

    if getattr(args, "dry_run", False):
        # AC25: a preview writes nothing at all, and says which files it would
        # have written so the reader can check before consenting.
        print("\nwould install (dry run — nothing written):")
        for skill in selection.skills:
            for measured in skill.files:
                relative = measured.path.relative_to(skill.envelope)
                print(f"  .claude/skills/{skill.name}/{relative}")
        return 0

    if not getattr(args, "yes", False) and not sys.stdin.isatty():
        print(
            "install: refusing to install a direct source without confirmation. "
            "Re-run with --yes for non-interactive use; the summary above is "
            "printed either way.",
            file=sys.stderr,
        )
        return 1
    if not getattr(args, "yes", False):
        answer = input("\nInstall these skills? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("install: cancelled; nothing was written.")
            return 1

    written: list[str] = []
    try:
        with normalize_direct_source(classification) as normalized:
            for skill in selection.skills:
                for measured in skill.files:
                    relative = measured.path.relative_to(skill.envelope)
                    relpath = f".claude/skills/{skill.name}/{relative.as_posix()}"
                    safety.write_jailed(
                        target_root,
                        relpath,
                        measured.data,
                        scope="repo",
                        allowed_prefixes=[".claude/"],
                    )
                    written.append(relpath)
            _ = normalized
    except (DirectAdmissionError, OSError) as exc:
        print(f"install: projection failed: {exc}", file=sys.stderr)
        return 1

    # AC12: the state row is written last and under the lock. Writing it before
    # the projection would leave a row pointing at files that were never
    # created; writing it outside the lock would let a concurrent run's rows be
    # lost, and would compute the 0.5 floor from a stale snapshot.
    _record_direct_rows(
        target_root=target_root,
        selection=selection,
        classification=classification,
        source_string=source_string,
        revision=revision,
        digest=digest,
        adapter=adapter,
        written=written,
    )

    for skill in selection.skills:
        print()
        print(
            render_receipt(
                kind="pack" if classification.shape == "direct-pack" else "manifestless",
                source=source_string,
                revision=revision,
                digest=digest,
                scope=scope,
                adapter=adapter,
                identity=skill.name,
            )
        )
    return 0


def _record_direct_rows(
    *,
    target_root: Path,
    selection: Selection,
    classification,
    source_string: str,
    revision: str | None,
    digest: str,
    adapter: str,
    written: list[str],
) -> None:
    """Write one owned state row per installed skill, under the state lock."""

    import hashlib as _hashlib

    from agentbundle import statelock
    from agentbundle.config import PackState
    from agentbundle.direct_source import MANIFESTLESS_VERSION_SENTINEL
    from agentbundle.direct_source_state import build_provenance

    state_path = target_root / ".agentbundle-state.toml"

    def _mutate(state) -> None:
        for skill in selection.skills:
            prefix = f".claude/skills/{skill.name}/"
            files = {
                relpath: {
                    "sha": _hashlib.sha256(
                        (target_root / relpath).read_bytes()
                    ).hexdigest()
                }
                for relpath in written
                if relpath.startswith(prefix)
            }
            if classification.shape == "direct-pack":
                kind, relative = "pack", None
            else:
                kind = "skill"
                relative = skill.envelope.relative_to(classification.root).as_posix()
            provenance = build_provenance(
                source=source_string,
                source_revision=revision,
                source_kind=kind,
                source_path=relative,
                source_digest=digest,
            )
            state.packs[(skill.name, adapter)] = PackState(
                # The sentinel is internal: AC26 keeps it off every rendered
                # surface, and the receipt above prints no version at all.
                installed_version=MANIFESTLESS_VERSION_SENTINEL,
                source=provenance.source,
                scope="repo",
                adapter=adapter,
                source_revision=provenance.source_revision,
                source_kind=provenance.source_kind,
                source_path=provenance.source_path,
                source_digest=provenance.source_digest,
                files=files,
            )

    statelock.persist_state_locked(state_path, _mutate)
