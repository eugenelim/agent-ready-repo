"""Direct provenance rows and the content-only install digest.

The digest is the value lifecycle comparison rests on, so its preimage is
defined here in one place and never recomputed elsewhere.
"""

from __future__ import annotations

import hashlib
import struct
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from agentbundle.direct_source import DirectClassification

# The version prefix is part of the stored value. A different prefix is a
# different algorithm, and AC13 refuses to compare across them rather than
# recomputing — recomputation would silently re-baseline a digest that was
# meant to detect exactly that change.
DIGEST_PREFIX = "sha256-1:"
# A capability-acceptance pin is not a content digest; separate prefixes stop
# one being accepted where the other is meant.
PIN_PREFIX = "cappin-1:"

# `pack` is a direct pack; `skill` is a manifestless skill, whose display label
# is `manifestless`. The display mapping lives here so the stored value and the
# rendered label cannot drift apart.
SOURCE_KIND_DISPLAY = {"pack": "pack", "skill": "manifestless"}


class DirectStateError(ValueError):
    """A direct provenance value that cannot be stored or compared."""


@dataclass(frozen=True)
class DirectProvenance:
    """The direct fields of one installed row, in AC12's serialization order."""

    source: str
    source_revision: str | None
    source_kind: str
    source_path: str | None
    source_digest: str


def direct_content_digest(entries: Iterable[tuple[str, bytes]]) -> str:
    """Digest sorted path/content entries per RFC-0098 E2.

    Each entry feeds SHA-256 a u64be path-byte length, the path bytes, a u64be
    content length, and the exact content bytes.  The length prefixes are what
    make the encoding unambiguous: without them the entries ``("ab", b"c")``
    and ``("a", b"bc")`` produce the same byte stream, so two different trees
    would share a digest.

    Entries sort by *encoded path bytes* rather than by string, so the ordering
    does not depend on the locale or on Python's collation.  No execute byte
    participates: mode availability differs by platform and would manufacture
    phantom updates for a tree whose content never changed.
    """

    digest = hashlib.sha256()
    seen: set[bytes] = set()
    for path, content in sorted(entries, key=lambda entry: entry[0].encode("utf-8")):
        if unicodedata.normalize("NFC", path) != path:
            raise DirectStateError(
                f"digest preimage path is not NFC-normalized: {path!r}"
            )
        encoded = path.encode("utf-8")
        if encoded in seen:
            raise DirectStateError(f"duplicate digest preimage path: {path!r}")
        seen.add(encoded)
        digest.update(struct.pack(">Q", len(encoded)))
        digest.update(encoded)
        digest.update(struct.pack(">Q", len(content)))
        digest.update(content)
    return f"{DIGEST_PREFIX}{digest.hexdigest()}"


def digest_preimage_entries(
    classification: DirectClassification,
) -> list[tuple[str, bytes]]:
    """Build the preimage entries for an admitted source.

    Every path is the **full relative path from the source root**, never the
    leaf-normalized identity.  Two envelopes that share a leaf name — which a
    category-grouped collection permits — would otherwise collapse onto one
    preimage entry and digest as though one of them did not exist.
    """

    root = classification.root
    # Keyed by path rather than appended, because the two sources overlap: a
    # root-single shape reports its `SKILL.md` as both a skill file and a named
    # file, and the same bytes must contribute one preimage entry, not two.
    # Overlap with *different* bytes would mean the inventory disagreed with
    # itself, so that is a refusal rather than a silent last-writer-wins.
    entries: dict[str, bytes] = {}

    def _add(measured) -> None:
        relative = str(PurePosixPath(*measured.path.relative_to(root).parts))
        existing = entries.get(relative)
        if existing is not None and existing != measured.data:
            raise DirectStateError(
                f"inventory reports two different contents for {relative!r}"
            )
        entries[relative] = measured.data

    for skill in classification.skills:
        for measured in skill.files:
            _add(measured)
    for named in classification.named_files:
        _add(named)
    return sorted(entries.items())


def direct_source_digest(classification: DirectClassification) -> str:
    """The stored `source-digest` for an admitted direct source."""

    return direct_content_digest(digest_preimage_entries(classification))


def comparable_digest(stored: str) -> str:
    """Return *stored* if this build can compare it, else refuse.

    AC13 forbids recomputing or rewriting a digest written under another
    algorithm version.  Refusing and directing the reader to reinstall keeps
    the stored value meaning what it meant when it was written.
    """

    if not stored.startswith(DIGEST_PREFIX):
        raise DirectStateError(
            f"cannot compare a {stored.split(':', 1)[0]!r} digest; this build "
            f"speaks {DIGEST_PREFIX.rstrip(':')!r}. Reinstall the skill to "
            f"re-record it."
        )
    body = stored[len(DIGEST_PREFIX) :]
    if len(body) != 64 or any(character not in "0123456789abcdef" for character in body):
        raise DirectStateError(f"malformed digest body: {body!r}")
    return stored


def build_provenance(
    *,
    source: str,
    source_revision: str | None,
    source_kind: str,
    source_path: str | None,
    source_digest: str,
) -> DirectProvenance:
    """Validate and assemble one direct row's provenance.

    Identity deliberately excludes revision and digest: a skill that is
    upgraded is the same installed thing at a new revision, not a new row.
    """

    if source_kind not in SOURCE_KIND_DISPLAY:
        raise DirectStateError(f"unknown direct source kind: {source_kind!r}")
    if not source:
        raise DirectStateError("a direct row requires a canonical source")
    if source_kind == "pack":
        if source_path is not None:
            raise DirectStateError("a direct pack has no source-path")
    else:
        if not source_path:
            raise DirectStateError("a manifestless row requires a source-path")
        candidate = PurePosixPath(source_path)
        if candidate.is_absolute() or any(
            part in {"", ".", ".."} for part in candidate.parts
        ):
            raise DirectStateError(f"source-path must be relative POSIX: {source_path!r}")
        if "\\" in source_path:
            raise DirectStateError(f"source-path must be POSIX: {source_path!r}")
    return DirectProvenance(
        source=source,
        source_revision=source_revision,
        source_kind=source_kind,
        source_path=source_path,
        source_digest=comparable_digest(source_digest),
    )


def relative_repo_source(source: Path, repo_root: Path) -> str:
    """Store a repo-scope in-repository source relatively, or refuse it.

    An absolute path stored in repository state breaks for every other clone,
    so an in-repository source is stored relative to the root and one outside
    the repository is refused rather than silently absolutised.
    """

    try:
        relative = source.relative_to(repo_root)
    except ValueError as exc:
        raise DirectStateError(
            f"repo-scope direct sources must live inside the repository: {source}"
        ) from exc
    return str(PurePosixPath(*relative.parts))


# AC30's comparison surface. Named explicitly rather than derived, because a
# derived set silently stops covering a field the moment one is added.
CAPABILITY_FIELDS = (
    "allowed_tools",
    "skill_digest",
    "skill_identities",
    "payload_digests",
    "boundaries",
    "credentialed",
)
PAYLOAD_DIRECTORIES = ("assets", "evals", "references", "scripts")
# `undeclared (unrestricted)` is a state, not an absence: it is named in the
# computed addition set so a declared-to-undeclared move is visible as the
# widening it is.
UNDECLARED_TOOLS = "undeclared (unrestricted)"


@dataclass(frozen=True)
class Capabilities:
    """The comparable capability surface of one installed or candidate skill."""

    allowed_tools: frozenset[str] | None
    skill_digest: str
    skill_identities: frozenset[str]
    payload_digests: dict[str, str]
    boundaries: frozenset[str]
    credentialed: object | None


@dataclass(frozen=True)
class CapabilityDelta:
    """Every named difference between two capability surfaces."""

    differences: tuple[str, ...]
    unknown: bool = False

    @property
    def requires_reconsent(self) -> bool:
        """Drift or any named difference forces re-consent."""

        return self.unknown or bool(self.differences)


def compare_capabilities(
    old: Capabilities | None, new: Capabilities
) -> CapabilityDelta:
    """Name every capability difference; confirm nothing implicitly.

    ``old`` is ``None`` when the installed projection could not be round-tripped
    losslessly.  That is *not* "no change": it is `unknown` drift, which refuses
    even with the acceptance flag and directs the reader to reinstall, because a
    comparison against data we could not read would silently approve anything.
    """

    if old is None:
        return CapabilityDelta((), unknown=True)

    differences: list[str] = []

    old_tools = old.allowed_tools
    new_tools = new.allowed_tools
    if old_tools != new_tools:
        added = _tool_display(new_tools) - _tool_display(old_tools)
        removed = _tool_display(old_tools) - _tool_display(new_tools)
        # Only what actually moved is named; an unchanged tool is never listed,
        # so a reader can act on the line rather than re-diffing it.
        if added:
            differences.append(f"allowed-tools added: {', '.join(sorted(added))}")
        if removed:
            differences.append(f"allowed-tools removed: {', '.join(sorted(removed))}")

    if old.skill_digest != new.skill_digest:
        differences.append("SKILL.md digest changed")

    added_skills = new.skill_identities - old.skill_identities
    removed_skills = old.skill_identities - new.skill_identities
    if added_skills:
        differences.append(f"skills added: {', '.join(sorted(added_skills))}")
    if removed_skills:
        differences.append(f"skills removed: {', '.join(sorted(removed_skills))}")

    for relpath in sorted(set(old.payload_digests) | set(new.payload_digests)):
        before = old.payload_digests.get(relpath)
        after = new.payload_digests.get(relpath)
        if before == after:
            continue
        if before is None:
            differences.append(f"payload added: {relpath}")
        elif after is None:
            differences.append(f"payload removed: {relpath}")
        else:
            differences.append(f"payload digest changed: {relpath}")

    if old.boundaries != new.boundaries:
        widened = new.boundaries - old.boundaries
        narrowed = old.boundaries - new.boundaries
        # Both directions are reported: a narrowed boundary set still changes
        # what the skill claims about itself.
        if widened:
            differences.append(f"boundaries added: {', '.join(sorted(widened))}")
        if narrowed:
            differences.append(f"boundaries removed: {', '.join(sorted(narrowed))}")

    if _normalised_credentialed(old.credentialed) != _normalised_credentialed(
        new.credentialed
    ):
        differences.append(
            f"credentialed: {_normalised_credentialed(old.credentialed)} → "
            f"{_normalised_credentialed(new.credentialed)}"
        )

    return CapabilityDelta(tuple(differences))


def _tool_display(tools: frozenset[str] | None) -> frozenset[str]:
    """Render an absent declaration as the named unrestricted state."""

    return frozenset({UNDECLARED_TOOLS}) if tools is None else tools


def _normalised_credentialed(value: object | None) -> str:
    """Normalize `metadata.credentialed`, including its absence."""

    if value is None:
        return "undeclared"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def accept_capability_pin(delta: CapabilityDelta, supplied: str, computed: str) -> None:
    """Validate `--accept-new-capabilities=<pin>` against the recomputed pin.

    The pin is what ties acceptance to the exact set of changes that was shown.
    Without it, a flag typed after reading one refusal would accept whatever the
    source happens to contain at the moment the second command runs.
    """

    if delta.unknown:
        raise DirectStateError(
            "capability drift is unknown: the installed projection could not be "
            "read back losslessly. Reinstall the skill rather than accepting "
            "changes that cannot be computed."
        )
    if supplied != computed:
        raise DirectStateError(
            f"the supplied capability pin {supplied!r} does not match the "
            f"recomputed pin {computed!r}. Re-run the upgrade and accept the "
            f"pin it prints."
        )


def capability_pin(delta: CapabilityDelta) -> str:
    """A stable pin over the exact difference set that was displayed."""

    # Its own prefix. Reusing the digest's would let `comparable_digest`
    # accept a capability pin as a valid `source-digest`, and the two values
    # attest to different things.
    joined = "\n".join(delta.differences)
    return f"{PIN_PREFIX}{hashlib.sha256(joined.encode('utf-8')).hexdigest()}"
