"""Direct-source selection, admissibility summary, and install receipt.

Everything a publisher supplies reaches the reader through this module, so the
delimiting and sanitisation rules live here rather than at each print site.
"""

from __future__ import annotations

import hashlib
import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from agentbundle.bounded_metadata import BoundedMetadataError
from agentbundle.catalogue_tooling.diagnostics import (
    DiagnosticCode,
    escape_rendered_value,
    is_default_ignorable,
    make_direct_diagnostic,
)
from agentbundle.catalogue_tooling.results import Diagnostic, Severity
from agentbundle.direct_source import (
    DirectClassification,
    DirectSkill,
    forget_remote_root_identity,
    recovery_command,
)
from agentbundle.direct_source_state import DirectStateError, relative_repo_source
from agentbundle.safety import PathJailError

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

# The ignorable set and the escaper live with the diagnostic constructor, so
# every rendered surface gets them whether or not it remembers to ask.
escape_path_value = escape_rendered_value


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
        # The ignorable set is consulted as well as the category, because AC18
        # says "reject every Default_Ignorable_Code_Point REGARDLESS of
        # category": U+115F, U+1160, U+3164, and U+FFA0 are all `Lo` and would
        # otherwise pass while rendering as nothing. The set was embedded
        # naming exactly those four and then never consulted here.
        if category[0] not in _ALLOWED_CATEGORIES or is_default_ignorable(character):
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


def skill_metadata(skill: DirectSkill) -> dict:
    """Parse a skill's frontmatter once, for every reader that needs it.

    Two call sites each scanned `skill.files` for `SKILL.md`, parsed it, and
    swallowed a parse failure into a *different* empty default — so the listing
    and the capability block could disagree about the same skill.
    """

    from agentbundle.bounded_metadata import (
        BoundedMetadataError,
        parse_bounded_metadata,
    )

    for measured in skill.files:
        if measured.path.name == "SKILL.md":
            try:
                return parse_bounded_metadata(measured.data)
            except BoundedMetadataError:
                return {}
    return {}


def _skill_description(skill: DirectSkill) -> str:
    """Read a skill's declared description, or the empty string."""

    value = skill_metadata(skill).get("description")
    return value.strip() if isinstance(value, str) else ""


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
    payload_digests: dict[str, tuple[str, str]],
) -> list[str]:
    """One per-selected-skill capability block, per AC19.

    Everything a publisher wrote is delimited and labelled; everything we
    computed is not.  The distinction is the point of the block: a reader has to
    be able to tell which lines are claims by the publisher and which are
    observations we made about their bytes.
    """

    metadata = skill_metadata(skill)

    allowed_tools = _normalised_allowed_tools(metadata, source=source)
    nested = metadata.get("metadata")
    boundaries = _string_set(nested.get("boundaries")) if isinstance(nested, dict) else []
    credentialed = nested.get("credentialed") if isinstance(nested, dict) else None

    # Every value below that a publisher controls goes through the allowlist,
    # and every path-shaped one through the escaper. Sanitising only `name` —
    # as this did — let a publisher put a raw ANSI sequence in `boundaries` and
    # repaint the whole block, including both verdicts and the delimiter lines,
    # immediately before the install prompt. The block is the consent surface;
    # forging it is the one thing it must not permit.
    def _publisher(value: object, label: str) -> str:
        return sanitise_publisher_value(str(value), label, source=source)

    safe_tools = [_publisher(tool, "allowed-tools") for tool in allowed_tools]

    lines = [
        f"skill: {_publisher(skill.name, 'skill name')}",
        f"  source:      {escape_path_value(source)}",
        f"  revision:    {escape_path_value(revision) if revision else '—'}",
        f"  scope:       {scope}",
        f"  adapter:     {adapter}",
        # `undeclared (unrestricted)` rather than an empty list: an absent
        # declaration is not a restriction to nothing, it is no restriction.
        f"  allowed-tools: {_render_tools(safe_tools)}",
        f"  boundaries:  "
        f"{', '.join(_publisher(b, 'boundaries') for b in boundaries) if boundaries else '—'}",
        f"  credentialed: "
        f"{_publisher(credentialed, 'credentialed') if credentialed is not None else '—'}",
        f"  SKILL.md:    {skill_digest}",
    ]
    for relpath in sorted(payload_digests):
        digest, mode = payload_digests[relpath]
        lines.append(f"    {escape_path_value(relpath)}  {digest}  {mode}")
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


def publisher_block(lines: list[str]) -> list[str]:
    """Wrap publisher-supplied lines in AC18's note and delimiters.

    One emitter. The consent summary and the refusal path each built the note
    and the two delimiters themselves, so AC18's single rule had two
    implementations that could drift apart in either direction — and the
    summary additionally took a `listing` parameter no production call passed.
    """

    return [PUBLISHER_BLOCK_NOTE, PUBLISHER_BLOCK_OPEN, *lines, PUBLISHER_BLOCK_CLOSE]


def render_admissibility_summary(blocks: list[list[str]], *, source: str) -> str:
    """Wrap publisher-derived output in AC20's verdicts and AC18's delimiters."""

    body: list[str] = []
    for block in blocks:
        body.extend(block)
        body.append("")
    while body and body[-1] == "":
        body.pop()
    return "\n".join(
        [ADMISSIBILITY_VERDICT, "", *publisher_block(body), "", ADMISSIBILITY_VERDICT]
    )


def render_receipt(
    *,
    kind: str,
    source: str,
    revision: str | None,
    digest: str,
    scope: str,
    adapter: str,
    identity: str,
    removal_hint: str,
    state_hint: str,
) -> str:
    """AC22's receipt: what was installed, from where, and how to undo it."""

    return "\n".join(
        [
            f"installed: {escape_path_value(identity)}",
            f"  kind:     {kind}",
            f"  source:   {escape_path_value(source)}",
            f"  revision: {escape_path_value(revision) if revision else '—'}",
            f"  digest:   {digest}",
            f"  scope:    {scope}",
            f"  adapter:  {adapter}",
            # NOT `agentbundle uninstall --skill <identity>`: that command
            # does not exist yet — `uninstall` accepts `--pack` only — so the
            # receipt was promising a usage error. AC28 says to promise an
            # uninstall receipt command only when the row exists; the command
            # has to exist too. Until the direct lifecycle surface lands, the
            # honest instruction is the manual removal AC28 already specifies.
            # The state filename is scope-dependent: user scope keeps its rows
            # in `.agentbundle/state.toml`, not the repo-scope name this line
            # used to hard-code. A receipt naming a file the adopter does not
            # have sends them looking for the wrong one.
            f"  remove:   delete {escape_path_value(removal_hint)} and its "
            f"row from {escape_path_value(state_hint)}",
        ]
    )


def _file_digest(measured) -> str:
    """The reported per-file digest, in the same prefixed form as the tree's."""

    from agentbundle.direct_source_state import DIGEST_PREFIX

    return DIGEST_PREFIX + hashlib.sha256(measured.data).hexdigest()


def resolve_skill_target(adapter: str, source: str) -> str:
    """The adapter's own `direct-directory` skill target, from the contract.

    Read from `contracts/adapter.toml` rather than hard-coded, because each
    adapter declares its own directory — `.claude/skills/`, `.agents/skills/`,
    `.kiro/skills/` — and writing every install under `.claude/` while the
    receipt printed the requested adapter made the consent artifact false and
    left the row invisible to the sweep that was supposed to protect it.
    """

    from agentbundle.commands.validate import _load_adapter_contract

    contract = _load_adapter_contract()
    declared = contract.get("adapter", {}).get(adapter)
    if declared is None:
        raise _refuse(
            DiagnosticCode.CAT_D008,
            f"unknown adapter: {adapter}",
            path=source,
            remediation="Run `agentbundle list-targets` for the adapters this build ships.",
        )
    for entry in declared.get("projection", []):
        if entry.get("primitive") == "skill" and entry.get("mode") == "direct-directory":
            return entry["target-path"].rstrip("/")
    raise _refuse(
        DiagnosticCode.CAT_D008,
        f"adapter {adapter!r} declares no direct-directory skill target",
        path=source,
        remediation="Choose an adapter that projects skills, or omit --adapter.",
    )


def _print_refusal(diagnostic) -> None:
    """Print a registered refusal with its path and recovery, on stderr."""

    import sys

    print(f"install: [{diagnostic.code}] {diagnostic.message}", file=sys.stderr)
    if diagnostic.path:
        print(f"  at: {escape_path_value(diagnostic.path)}", file=sys.stderr)
    if diagnostic.remediation:
        print(f"  \u2192 {diagnostic.remediation}", file=sys.stderr)


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
        # `--dry-run` is exempt: it writes nothing, and it is the only way to
        # read the admissibility summary for a remote source before consenting
        # to install it. Requiring --yes for it would leave the reader choosing
        # blind — and would make the refusal message below false, since it
        # points at exactly this.
        if not getattr(args, "yes", False) and not getattr(args, "dry_run", False):
            # The message must not claim a summary it does not produce: the
            # refusal happens before acquisition, so no admission has run and
            # there is nothing to summarise yet. Saying otherwise sends the
            # reader looking for output that was never written.
            print(
                "install: a remote direct source requires --yes. Fetching the "
                "archive is itself an action, so consent is given up front; "
                "the admissibility summary is then printed before anything is "
                "written, and --dry-run shows it without installing.",
                file=sys.stderr,
            )
            return 1
        try:
            acquired = acquire_git_https_archive(source)
        except DirectAcquisitionError as exc:
            _print_refusal(exc.diagnostic)
            return 1
        from agentbundle.direct_source import declare_remote_root_identity
        from agentbundle.direct_source_acquisition import parse_direct_source

        source = acquired.root
        revision = acquired.revision
        # A remote root-single would otherwise take its identity from the
        # archive's `<repo>-<ref>` wrapper directory, which changes on every
        # upgrade. The repository name is what stays the same.
        declare_remote_root_identity(
            acquired.root, parse_direct_source(source_string).repository
        )
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
            forget_remote_root_identity(acquired_root)


def _install_admitted_source(
    args, *, source: Path, source_string: str, revision: str | None
) -> int:
    """The local half: admit, select, summarise, consent, project, record."""

    import sys

    from agentbundle.direct_source import (
        validate_direct_source,
    )

    admission = validate_direct_source(source)
    if not admission.ok:
        for diagnostic in admission.diagnostics:
            _print_refusal(diagnostic)
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
        # The listing is built OUTSIDE this handler on purpose. It renders
        # publisher values, so it can raise its own refusal — and computed here
        # that refusal would escape the handler as a traceback, replacing an
        # exit-1 refusal with a stack trace that also prints internal paths.
        listing: list[str] | None = None
        listing_refusal: DirectInstallError | None = None
        if classification.shape == "collection" and not getattr(args, "skill", None):
            try:
                listing = candidate_listing(classification, source=source_string)
            except DirectInstallError as inner:
                listing_refusal = inner
        if listing_refusal is not None:
            # AC18: a disallowed candidate value refuses the whole invocation
            # rather than being elided, because a partial listing would print
            # `--all-skills` recovery covering more than the reader was shown.
            _print_refusal(listing_refusal.diagnostic)
            return 1
        _print_refusal(exc.diagnostic)
        if listing:
            # AC18: publisher values appear only inside the delimiters, emitted
            # by the one helper the consent summary also uses.
            print("\n" + "\n".join(publisher_block(listing)), file=sys.stderr)
        if exc.diagnostic.remediation:
            print(f"\n{exc.diagnostic.remediation}", file=sys.stderr)
        return 1

    scope = getattr(args, "scope", None) or "repo"
    adapter = getattr(args, "adapter", None) or "claude-code"
    target_root = Path(getattr(args, "output", ".") or ".")
    try:
        return _summarise_and_project(
            args,
            classification=classification,
            selection=selection,
            source_string=source_string,
            revision=revision,
            scope=scope,
            adapter=adapter,
            target_root=target_root,
        )
    except (DirectInstallError, DirectStateError, PathJailError, BoundedMetadataError) as exc:
        # Everything below admission still touches publisher-controlled bytes:
        # frontmatter values, payload filenames, and path segments. Each of
        # these carries a registered refusal or a message; none of them may
        # reach the adopter as a stack trace, which would also print internal
        # paths on stderr.
        diagnostic = getattr(exc, "diagnostic", None)
        if diagnostic is not None:
            _print_refusal(diagnostic)
        else:
            print(
                f"install: [{DiagnosticCode.CAT_D019.value}] {exc}",
                file=sys.stderr,
            )
        return 1


def _summarise_and_project(
    args,
    *,
    classification,
    selection,
    source_string: str,
    revision: str | None,
    scope: str,
    adapter: str,
    target_root: Path,
) -> int:
    """Render the consent summary, take consent, project, and record."""

    import sys

    from agentbundle import safety
    from agentbundle.commands._common import resolve_state_path
    from agentbundle.direct_source_state import direct_source_digest

    if scope == "local":
        # The catalogue route's local scope requires a git work tree, refuses
        # when targets are already tracked, writes `.agentbundle-local-state.toml`,
        # and registers a git exclude. The direct route wires none of it, so
        # accepting the flag wrote third-party content into a tree the adopter
        # believes leaves no trace, recorded it in the COMMITTED state file, and
        # left it unprotected from the orphan sweep — `installed_skill_names`
        # filters to repo scope. Refusing is honest until that preflight exists.
        raise _refuse(
            DiagnosticCode.CAT_D008,
            "--scope local is not supported for direct sources",
            path=source_string,
            remediation=(
                "Use --scope repo or --scope user. Local scope needs the git "
                "exclude and local-state handling the catalogue route performs, "
                "which the direct route does not yet implement."
            ),
        )
    skill_target = resolve_skill_target(adapter, source_string)
    # User scope installs under the resolved user root, not the repo.
    if scope == "user":
        from agentbundle import scope as scope_mod

        try:
            projection_root = Path(scope_mod.resolve_user_root())
        except scope_mod.UserScopeUnresolvable as exc:
            # Every other direct failure below admission was deliberately turned
            # into a registered exit-1 refusal so internal paths never print.
            # This one was left bare, so a `$HOME` of `/` or an absent home —
            # both documented, both real in corporate sandboxes and containers —
            # reached the adopter as a traceback. The catalogue route handles it.
            raise _refuse(
                DiagnosticCode.CAT_D008,
                f"--scope user cannot be resolved: {exc}",
                path=source_string,
                remediation=(
                    "Use --scope repo with --output, or set AGENTBUNDLE_USER_ROOT "
                    "to the directory that should hold user-scope installs."
                ),
            ) from None
    else:
        # Not canonicalised here: AC39 assigns confinement to `write_jailed`,
        # which resolves inside the helper. A caller-side resolve is exactly
        # the spelling that defeats that rule while looking careful.
        projection_root = target_root
    digest = direct_source_digest(classification)

    blocks = []
    for skill in selection.skills:
        payload = {
            str(measured.path.relative_to(skill.envelope)): (
                _file_digest(measured),
                report_time_mode(measured.mode),
            )
            for measured in skill.files
            if measured.path.name != "SKILL.md"
        }
        skill_digest = next(
            (
                _file_digest(measured)
                for measured in skill.files
                if measured.path.name == "SKILL.md"
            ),
            None,
        )
        if skill_digest is None:
            # Classification makes this unreachable today, which is exactly why
            # it must not fall back: reporting the whole-source digest under a
            # `SKILL.md:` label would be a wrong observation rather than a
            # refusal, and the reader consents to the rendering.
            raise _refuse(
                DiagnosticCode.CAT_D009,
                f"skill envelope has no SKILL.md to digest: {skill.name}",
                path=source_string,
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
    # On stderr, like every refusal. On stdout, `install <source> --yes >
    # install.log` hid the entire verdict-and-delimiter block from view while
    # the install went ahead — the one output that must not be redirectable
    # away from the person consenting.
    print(render_admissibility_summary(blocks, source=source_string), file=sys.stderr)

    if getattr(args, "dry_run", False):
        # AC25: a preview writes nothing at all, and says which files it would
        # have written so the reader can check before consenting.
        print("\nwould install (dry run — nothing written):")
        for skill in selection.skills:
            for measured in skill.files:
                relative = measured.path.relative_to(skill.envelope)
                print(f"  {skill_target}/{skill.name}/{escape_path_value(relative)}")
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

    # Every destination is validated BEFORE the first write. `write_jailed`
    # checks each name as it goes, so a publisher-chosen payload name that fails
    # — `nul.md`, say — aborted the loop midway and left the files already
    # written on disk, with no state row and no receipt: the adopter was told
    # the install failed while an unreviewed SKILL.md was live in their skills
    # directory, invisible to `list-installed` and unreachable by `uninstall`.
    planned: list[tuple[str, bytes]] = []
    for skill in selection.skills:
        for measured in skill.files:
            relative = measured.path.relative_to(skill.envelope)
            relpath = f"{skill_target}/{skill.name}/{relative.as_posix()}"
            for segment in PurePosixPath(relpath).parts:
                safety.assert_portable_name(segment)
            planned.append((relpath, measured.data))

    _refuse_foreign_owner(
        projection_root, selection, skill_target, scope, adapter, source_string, planned
    )

    written: dict[str, bytes] = {}
    try:
        for relpath, projected_bytes in planned:
            safety.write_jailed(
                projection_root,
                relpath,
                projected_bytes,
                scope=scope,
                allowed_prefixes=[f"{skill_target.split('/')[0]}/"],
            )
            written[relpath] = projected_bytes
    except (OSError, PathJailError) as exc:
        # `PathJailError` is a `ValueError`, so an `except OSError` never caught
        # it: the pre-write loop validates only `write_jailed`'s portable-name
        # precondition, while its jail and prefix checks still run per write. A
        # pre-existing symlink in the target tree therefore left the files
        # already written live, unlisted, and unowned — the exact residue this
        # handler exists to report.
        print(f"install: projection failed: {exc}", file=sys.stderr)
        _report_unowned(written)
        return 1

    # AC12: the state row is written last and under the lock. Writing it before
    # the projection would leave a row pointing at files that were never
    # created; writing it outside the lock would let a concurrent run's rows be
    # lost, and would compute the 0.5 floor from a stale snapshot.
    try:
        _record_direct_rows(
            target_root=projection_root,
            skill_target=skill_target,
            scope=scope,
            selection=selection,
            classification=classification,
            source_string=source_string,
            revision=revision,
            digest=digest,
            adapter=adapter,
            written=written,
        )
    except (DirectStateError, OSError, PathJailError) as exc:
        # The projection succeeded and the row did not, so every projected file
        # is now unowned. Previously this unwound to the generic handler, which
        # printed one line and no file list — AC28 asks install to surface an
        # unowned projection, and the files are only knowable here.
        print(f"install: state write failed: {exc}", file=sys.stderr)
        _report_unowned(written)
        return 1

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
                removal_hint=f"{skill_target}/{skill.name}/",
                state_hint=resolve_state_path(scope, Path()).as_posix(),
            )
        )
    return 0


def _record_direct_rows(
    *,
    target_root: Path,
    skill_target: str,
    scope: str,
    selection: Selection,
    classification,
    source_string: str,
    revision: str | None,
    digest: str,
    adapter: str,
    written: dict[str, bytes],
) -> None:
    """Write one owned state row per installed skill, under the state lock."""

    import hashlib as _hashlib

    from agentbundle import statelock
    from agentbundle.commands._common import resolve_state_path
    from agentbundle.config import PackState
    from agentbundle.direct_source import MANIFESTLESS_VERSION_SENTINEL
    from agentbundle.direct_source_state import build_provenance

    state_path = resolve_state_path(scope, target_root)

    def _mutate(state) -> None:
        # Re-asserted INSIDE the lock, against the state re-read there. The
        # pre-write guard read state unlocked, so a concurrent install landing
        # in the window between the two produced exactly the two-rows-one-path
        # corruption that guard exists to prevent — and the window spanned every
        # file write, not an instant.
        owner_keys = {(skill.name, adapter) for skill in selection.skills}
        for relpath in written:
            foreign_rows = sorted(
                key for key in state.owners_of(relpath) if key not in owner_keys
            )
            if foreign_rows:
                claimants = ", ".join(f"{name} ({ad})" for name, ad in foreign_rows)
                raise DirectStateError(
                    f"{relpath} was claimed by {claimants} while this install "
                    f"was writing; no row was recorded"
                )
        for skill in selection.skills:
            # Bucketed by path parts rather than by a string prefix: AC39 bans
            # a hand-rolled prefix check on a path-shaped value, and the digest
            # comes from the bytes already measured rather than a second read
            # of what we just wrote.
            owned = tuple(skill_target.split("/")) + (skill.name,)
            files = {
                relpath: {"sha": _hashlib.sha256(payload).hexdigest()}
                for relpath, payload in written.items()
                if tuple(PurePosixPath(relpath).parts[: len(owned)]) == owned
            }
            if classification.shape == "direct-pack":
                kind, relative = "pack", None
            else:
                kind = "skill"
                relative = skill.envelope.relative_to(classification.root).as_posix()
            stored_source = stored_source_for(source_string, scope, target_root)
            provenance = build_provenance(
                source=stored_source,
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
                scope=scope,
                adapter=adapter,
                source_revision=provenance.source_revision,
                source_kind=provenance.source_kind,
                source_path=provenance.source_path,
                source_digest=provenance.source_digest,
                files=files,
            )

    # Root and relpath given explicitly so the jail is the projection root, not
    # the state file's own parent directory, and the scope rail matches the
    # catalogue route's. The state file is CLI-owned metadata rather than
    # pack-projected content, so the per-adapter prefix check is skipped at the
    # two scopes whose state file is a top-level name no prefix can match;
    # user scope keeps `.agentbundle/`, which its state file is already under
    # and which `write_jailed` requires any user-scope write to declare.
    state_relpath = state_path.relative_to(target_root).as_posix()
    statelock.persist_state_locked(
        state_path,
        _mutate,
        scope=scope,
        allowed_prefixes=None if scope in ("repo", "local") else [".agentbundle/"],
        root=target_root,
        relpath=state_relpath,
    )


def stored_source_for(source_string: str, scope: str, root: Path) -> str:
    """The exact string a direct row stores for this source.

    One function, called at write time AND by the ownership check. They
    computed it separately: the write relativised an in-repository repo-scope
    source while the check compared the raw string, so reinstalling the same
    in-repository source refused as "a different source" — and the remediation
    named `uninstall --skill`, which does not exist. Every fixture put the
    source outside the target, where `relative_to` raises and both sides
    happened to agree.

    AC12: an absolute path in repository state is wrong for every other clone.
    A source outside the repository keeps its verbatim string, because refusing
    it would reject `install /elsewhere/skill --output .` — the ordinary local
    workflow. No caller-side canonicalisation: AC39 assigns that to the
    confinement helpers, and this decides which string to store, not a boundary.
    """

    if scope != "repo" or source_string.startswith("git+https://"):
        return source_string
    try:
        return relative_repo_source(Path(source_string), root)
    except DirectStateError:
        return source_string


def _report_unowned(written: dict[str, bytes]) -> None:
    """Name every file that is live on disk and owned by no state row.

    Called from both failure paths — a projection fault and a state-write
    fault — because either leaves the same residue and the adopter cannot
    discover it any other way: `list-installed` and `uninstall` read the state
    file, and by construction nothing there points at these paths.
    """

    import sys

    if not written:
        return
    print(
        "install: these files were written and are owned by no state row; "
        "remove them manually:",
        file=sys.stderr,
    )
    for relpath in sorted(written):
        print(f"  {escape_path_value(relpath)}", file=sys.stderr)


def _destination_holds_foreign_content(
    root: Path, relpath: str, projected_bytes: bytes, state
) -> bool:
    """True when the file at *relpath* holds content no install put there.

    The row-level guard asks "does a row named like ours claim this skill?".
    That misses the two cases that matter: a catalogue pack's row is keyed on
    the PACK name while the directory it projects carries the SKILL name, and
    an adopter's hand-authored skill has no row at all. Both were overwritten
    silently at exit 0 — publisher content replacing a file the agent already
    trusts, which is the injection path, not merely a bookkeeping error.

    Content, not existence: reinstalling the same source rewrites its own
    bytes, and reinstalling after the publisher moved on rewrites a file whose
    on-disk hash is still the one an install recorded. Only content that
    matches neither is foreign. Confinement failures are not decided here —
    `write_jailed` owns that boundary and refuses on its own terms.
    """

    from agentbundle.catalogue_tooling.file_safety import (
        UnsafeContentError,
        sha256_confined_regular_file,
    )

    try:
        on_disk = sha256_confined_regular_file(root, root / relpath)
    except (OSError, UnsafeContentError):
        return False
    if on_disk == hashlib.sha256(projected_bytes).hexdigest():
        return False
    return on_disk not in state.shas_for(relpath)


def _refuse_foreign_owner(
    projection_root: Path,
    selection: Selection,
    skill_target: str,
    scope: str,
    adapter: str,
    source_string: str,
    planned: list[tuple[str, bytes]],
) -> None:
    """Refuse to overwrite a row or a directory this source does not own.

    The identity is the publisher's envelope directory name, so a direct source
    can collide with an installed pack simply by naming a skill the same thing.
    Without this, the row was replaced wholesale: the pack's other projected
    files became unowned, the next orphan sweep deleted them, and `uninstall`
    could no longer find them — silently, at exit 0. The catalogue route refuses
    an in-place re-install and gates `--force`; this is the direct equivalent.
    """

    from agentbundle.commands._common import resolve_state_path
    from agentbundle.config import ConfigError, load_state

    # Through the shared resolver, not a hard-coded repo-scope filename. At
    # user scope every reader looks in `<user_root>/.agentbundle/state.toml`,
    # so writing `<user_root>/.agentbundle-state.toml` left the projection
    # permanently unowned — exactly the state AC28's sweep guard exists to
    # prevent, and it made "install/list surfaces unowned projections at every
    # scope" false at user scope.
    state_path = resolve_state_path(scope, projection_root)
    try:
        state = load_state(state_path)
    except ConfigError:
        # An unreadable state file cannot prove ownership either way, and the
        # sweep guard already refuses on it. Say so rather than overwriting.
        raise _refuse(
            DiagnosticCode.CAT_D009,
            f"cannot establish ownership: {state_path} could not be read",
            path=source_string,
            remediation="Repair or remove the state file before installing.",
        ) from None

    stored = stored_source_for(source_string, scope, projection_root)
    for skill in selection.skills:
        existing = state.row(skill.name, adapter)
        if existing is None:
            continue
        same_source = (
            existing.source_kind in {"pack", "skill"} and existing.source == stored
        )
        if not same_source:
            raise _refuse(
                DiagnosticCode.CAT_D009,
                f"{skill.name!r} is already installed at {scope} scope for "
                f"{adapter} from a different source",
                path=source_string,
                remediation=(
                    "Uninstall it first, or choose a source whose skill names "
                    "do not collide. Overwriting would orphan the files the "
                    "existing row owns."
                ),
            )

    # Per DESTINATION, not per skill name. `State.owners_of` is the blessed
    # path-level ownership primitive and it answers the question the row-level
    # loop above cannot: which rows, under any name, already claim the exact
    # paths we are about to write.
    owner_keys = {(skill.name, adapter) for skill in selection.skills}
    for relpath, projected_bytes in planned:
        foreign_rows = sorted(
            key for key in state.owners_of(relpath) if key not in owner_keys
        )
        if foreign_rows:
            claimants = ", ".join(f"{name} ({ad})" for name, ad in foreign_rows)
            raise _refuse(
                DiagnosticCode.CAT_D009,
                f"{relpath} is already owned by {claimants}",
                path=relpath,
                remediation=(
                    "Uninstall the owning pack first. Overwriting would leave "
                    "two rows claiming one path with different contents, which "
                    "no later install, upgrade, or uninstall can resolve."
                ),
            )
        if _destination_holds_foreign_content(
            projection_root, relpath, projected_bytes, state
        ):
            raise _refuse(
                DiagnosticCode.CAT_D009,
                f"{relpath} already exists and no install put its content there",
                path=relpath,
                remediation=(
                    "Move or delete the existing file first. It is either "
                    "hand-authored or locally edited, and this source would "
                    "replace it with publisher content silently."
                ),
            )
