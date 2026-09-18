#!/usr/bin/env python3
"""Check that a loop contract's items line up: identifiers, references, coverage.

Scope is deliberately narrow. This decides *item alignment* inside one spec
directory and owns no lifecycle question -- status vocabulary, ship transitions,
deferral anchors and contract traceability belong to the spec-status lint, and
duplicating them here would put two homes on one obligation.

The rules, all mechanical:

  1. every acceptance criterion carries a well-formed identifier
  2. identifiers are unique within the spec directory
  3. no identifier appears in the retired list
  4. every criterion-class reference in spec.md and plan.md resolves
  5. every criterion is named by at least one task *entry*
  6. every criterion appears in exactly one verification group
  7. a verification item's identifier is its own, not derived from what it serves
  8. no task entry leaves a code span open, which is how a multi-site edit
     truncates a closing condition without making it look truncated
  9. no criterion was reworded while the assertion blocks naming it stayed put
     -- a criterion whose assertion did not follow it. Its base revision
     defaults to the merge-base with the default branch; `--since` names one
     explicitly and `--no-since` declines it.
  10. each populated Design (LLD) sub-section in a participating plan names an
      owning task
  11. each task named by an Owned by field is defined in that plan

Rule 5 is scoped to task entries -- a task's 'Tests:' and 'Done when:'
blocks -- and not to the whole document. The weaker form, "does this identifier
appear anywhere in plan.md", passes on a mention in prose, in a changelog, or in
another task's rationale, so a criterion with no implementing bullet anywhere
reads as covered.

Forward-only by construction: a spec whose criteria carry no identifiers is
skipped entirely, so introducing this check does not fail a corpus authored
before the convention existed.

Exit codes: '0' no failing findings -- which includes a run where a reporting
rule flagged something, since those are printed as "reported, not failing" and
never set the status; '1' at least one failing finding; '2' the check could not
run, which is a spec directory outside the invocation root, or any usage error
argparse rejects -- an empty '--since', '--since' with '--no-since', an unknown
flag; a directory with no 'spec.md' is a finding, not a refusal.

Rule 9 is the reporting rule. It over-reports by construction, so a non-zero
exit on it would fail a build for a prose edit. It resolves its own base
revision rather than waiting to be given one: a rule whose input is optional is
a rule that does not run, and its no-input line prints beside a zero finding
count where the summary reads as a pass.

The summary's 'partial (rules with no input: ...)' clause lists plan-gated
rules and rule 9 when they had no input, grouped by spec; its count is of
specs, not of rules. Rule 4 is deliberately absent even when it is half-applied -- see
PLAN_GATED -- so the clause is not the complete account of what did not run.
Any entry in it is an un-run rule, never a clean result. Rule 9's entry states
which input it lacked; rules 5, 7 and 8 name themselves only, because a
plan-gated rule has one way to have no input.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Every distinct finding this checker can emit, keyed by rule. The catalogue is
# here rather than in the suite so the two cannot drift: every message below is
# formatted from these fragments, so a rule's wording has one home. A rule whose
# fragment no test observes is a rule with no red case, so its suite is green for
# a reason unrelated to whether the rule works -- which is what the shipped
# finding-coverage check reports when it is run over this file.
FINDING_KINDS = {
    "unlabelled": "criterion carries no identifier",
    "duplicate": "is assigned twice",
    "retired": "is retired and must not be reused",
    "malformed": "malformed identifier",
    "unresolved": "resolves to no criterion",
    "no-task-entry": "is named by no task entry",
    "group-count": "appears in",
    "derived-item": "mirrors",
    "unconfined": "refusing path outside root",
    "capped": "more finding(s) in",
    "no-spec": "no spec.md",
    "broken-entry": "entry has an unterminated code span",
    "stale-assertion": "was reworded with no changed assertion in",
    "unowned-design": "has no Owned by task ID",
    "undefined-owner": "names an undefined task ID",
    "predating-owner": "predates the Owned by field",
}

# Findings are listed up to this many, then grouped by spec with an exact
# remainder. Uncapped, thirty bad specs produced 211 lines and 18KB -- and a
# checker's output lives in its caller's context for the rest of a session, so
# an error path that floods is a worse failure than the one it reports. The
# counts stay exact and `--verbose` restores the full list, following the
# repository's own convention for its spec-status lint.
FINDING_CAP = 20

# The rules that report no input when plan.md is absent. Rule 4 is deliberately
# not here: it reads both texts and still decides the spec half, so it is
# partially applied rather than unapplied, and listing it would claim a rule ran
# on nothing when half of it ran. A rule that silently runs on nothing is the
# partial-read-as-clean failure this module exists to detect in other artifacts.
PLAN_GATED = (
    "no-task-entry",
    "derived-item",
    "broken-entry",
    "unowned-design",
    "undefined-owner",
)

CRITERION = re.compile(r"^- \[[ x]\] \*\*(AC-\d{4})\.\*\* ", re.M)
CRITERION_LINE = re.compile(r"- \[[ x]\] \*\*(AC-\d{4})\.\*\* ")
UNLABELLED = re.compile(r"^- \[[ x]\] (?!\*\*(?:AC|VI)-\d{4}\.\*\*)", re.M)
CRITERION_REF = re.compile(r"\bAC-\d{4}\b")
ITEM_REF = re.compile(r"\bVI-\d{4}\b")
MALFORMED = re.compile(r"\b(?:AC|VI)-(?!\d{4}\b)[A-Za-z0-9]+\b")
# A task body ends at the next task *or the next level-two heading*. Running it
# to end-of-file makes the last task's body swallow every section after it --
# Rollout, Risks, the Changelog -- so a criterion named in the changelog is
# credited to a task entry. That is the mention-anywhere form rule 5 exists to
# eliminate, reappearing inside rule 5.
TASK = re.compile(r"^### (T\d+[a-z]?)\b(.*?)(?=^### T\d+[a-z]?\b|^## |\Z)", re.M | re.S)
# A field block ends at the next *field label* -- bold, capitalised, colon --
# not at any bold capital. A bold identifier such as `**XX-0000.**` opens a case
# bullet, not a field, and treating it as a boundary truncated a task's Tests
# block at its first bullet.
ENTRY = re.compile(r"\*\*(?:Tests|Done when):\*\*(.*?)(?=\n\*\*[A-Z][A-Za-z ]*:\*\*|\Z)", re.S)
# Fenced blocks carry backticks whose count says nothing about the prose around
# them, so they come out before a span is matched.
FENCE = re.compile(r"^```.*?^```", re.M | re.S)
# What a revision may look like. Deliberately narrower than git's own grammar:
# this is a rejection filter on caller input, not a parser, so anything it does
# not recognise is refused rather than guessed at.
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/@^~-]{0,200}")
# A run of three or more written inline is a fence *token* quoted in prose, not a
# span delimiter: markup with no matching run of equal length renders it
# literally. Removing it before matching is what separates "this entry is
# broken" from "this entry mentions a fence".
INLINE_FENCE = re.compile(r"`{3,}")
RUN = re.compile(r"`+")
GROUP_ITEM = re.compile(r"^- \*\*(.+?)\*\*", re.M | re.S)
RETIRED_HEADING = re.compile(r"^## Retired identifiers\s*$", re.M)
RETIRED_ENTRY = re.compile(r"^[-*]\s+`?((?:AC|VI)-\d{4})`?\s*$", re.M)
LLD_SUBSECTION = re.compile(r"^### (.+?)\n(.*?)(?=^### |\Z)", re.M | re.S)
# The template documents this field inside an HTML comment; an authored plan
# writes it as plain text. One declaration, two renderings, one pattern.
OWNED_BY = re.compile(
    r"^(?:Owned by:[ \t]*(?P<plain>[^<>\n]*?)"
    r"|<!--[ \t]*Owned by:[ \t]*(?P<wrapped>.*?)[ \t]*-->)[ \t]*$",
    re.M,
)
OWNED_TASK = re.compile(r"\bT\d+[a-z]?\b")


def _section(text: str, heading: str) -> str:
    """Return the body under a level-two heading, or "" when it is absent."""
    match = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def retired(spec: str) -> set[str]:
    """Identifiers recorded as retired.

    An absent heading is an empty list, not a finding: omitting it while nothing
    has been retired is the convention, so absence is the normal state.
    """
    # No heading check: `_section` returns "" for an absent heading and the entry
    # pattern finds nothing in it, so a guard here changes no outcome for any
    # input and no case can distinguish it.
    return set(RETIRED_ENTRY.findall(_section(spec, "Retired identifiers")))


def verification_groups(spec: str) -> dict[str, int]:
    """Count the Testing Strategy groups each criterion appears in.

    A group is a list item whose leading bold segment names its criteria in
    parentheses. Reading the whole section instead would count a criterion named
    in a group's explanatory prose as a second group.
    """
    counts: dict[str, int] = {}
    for lead in GROUP_ITEM.findall(_section(spec, "Testing Strategy")):
        for ident in set(CRITERION_REF.findall(lead)):
            counts[ident] = counts.get(ident, 0) + 1
    return counts


def task_entries(plan: str) -> dict[str, list[str]]:
    """Map each criterion to the tasks whose entries name it.

    Only ``Tests:`` and ``Done when:`` blocks count. ``Approach:`` is an
    instruction no completion gate reads, and prose elsewhere is not a claim that
    any task verifies the criterion.
    """
    named: dict[str, list[str]] = {}
    for task, body in TASK.findall(plan):
        scope = "".join(ENTRY.findall(body))
        for ident in set(CRITERION_REF.findall(scope)):
            named.setdefault(ident, []).append(task)
    return named


def design_ownership(plan: str) -> tuple[bool, list[tuple[str, str, list[str]]]]:
    """Return whether the plan uses ``Owned by:``, and each LLD field's IDs.

    A plan opts in when any Design (LLD) sub-section carries the field, even
    when that field is empty. Empty sub-sections do not need an owner, but once
    a plan opts in every sub-section with body text does.
    """
    ownership: list[tuple[str, str, list[str]]] = []
    participating = False
    for title, body in LLD_SUBSECTION.findall(_section(plan, "Design (LLD)")):
        fields = [plain or wrapped
                  for plain, wrapped in OWNED_BY.findall(body)]
        participating = participating or bool(fields)
        ownership.append((title, body, OWNED_TASK.findall("\n".join(fields))))
    return participating, ownership


def design_ownership_findings(rel: str, plan: str) -> tuple[list[str], list[str]]:
    """Rules 10 and 11, as failing findings and reported-not-failing notes.

    Split out because both the labelled and unlabelled paths run it: ownership
    is decided from the plan alone and never from the spec's criteria, so
    gating it on the criterion grammar would silence it for most of a corpus.
    """
    if not plan:
        return [], []
    participating, sections = design_ownership(plan)
    if not participating:
        return [], [f"{rel}/plan.md: {FINDING_KINDS['predating-owner']}"]
    findings: list[str] = []
    defined_tasks = {task for task, _ in TASK.findall(plan)}
    for title, body, owners in sections:
        if body.strip() and not owners:
            findings.append(f"{rel}/plan.md: {title} {FINDING_KINDS['unowned-design']}")
        for task in owners:
            if task not in defined_tasks:
                findings.append(
                    f"{rel}/plan.md: {title} {task} "
                    f"{FINDING_KINDS['undefined-owner']}"
                )
    return findings, []


def unterminated(entry: str) -> bool:
    """True when a code span in this entry is opened and never closed.

    Backtick *runs* are matched the way the markup delimits a span -- a span
    opens on a run of N and closes on the next run of exactly N -- rather than
    counted. A run of three written inline in prose ("a fenced ```python
    example") is the common case and is *not* a broken span: with no matching
    run of the same length the markup leaves it literal, so it renders exactly
    as written. Counting backticks reports it, and so did matching runs until an
    inline fence token was removed first.
    """
    return _spans_open(INLINE_FENCE.sub("", FENCE.sub("", entry)))


def _spans_open(text: str) -> bool:
    open_len = None
    for run in RUN.findall(text):
        if open_len is None:
            open_len = len(run)
        elif len(run) == open_len:
            open_len = None
    return open_len is not None


def _rel(path: Path, root: Path | None) -> str:
    """A path as the caller's repository sees it, never as this host does."""
    try:
        return path.relative_to(root).as_posix() if root else path.as_posix()
    except ValueError:
        return path.as_posix()


def _read_confined(path: Path, root: Path | None) -> str | None:
    """Read a regular file proven to sit inside the invocation root, or None.

    Canonicalise first and re-check containment on the resolved path: `..`
    rejection and `~` expansion do not stop an in-boundary symlink pointing out,
    which is the escape the repository's own security rule names. A link, a
    reparse point or anything that is not a regular file is refused rather than
    followed, because this tool is handed paths by a caller.
    """
    try:
        real = path.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if root is not None:
        base = root.resolve()
        if real != base and base not in real.parents:
            return None
    if path.is_symlink() or not real.is_file():
        return None
    try:
        return real.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


# Tried in order against the working tree. A remote-tracking ref is preferred
# over a local one because it is the ref the change will be reviewed against:
# a local `main` left unpulled has an older tip, so the merge-base against it
# is older too and rule 9 reads commits that landed since as part of this
# change. `origin/HEAD` is first because it names the remote's own default
# rather than guessing at its spelling. A tag beats a branch of the same name
# here, silently; no one prefix disambiguates a list that includes
# `origin/HEAD`, which is not under `refs/heads/`.
_DEFAULT_BASE_REFS = ("origin/HEAD", "origin/main", "origin/master", "main", "master")

# `GIT_DIR` and its companions take precedence over `-C`, so under a git hook,
# `rebase --exec` or `bisect run` an inherited environment answers for a
# repository the caller never named -- `--show-toplevel` can report `--root`
# while `HEAD` comes from elsewhere, which defeats the bound below by telling
# it what it wants to hear. Dropped rather than overridden: there is no value
# for these that means "use `-C`".
#
# The criterion for membership is narrow, and it is *not* "every GIT_* name":
# a variable belongs here only if it can change WHICH repository or WHICH refs
# answer, because that is the only thing the `--root` bound is protecting. The
# object-location variables fail that test -- `GIT_OBJECT_DIRECTORY` and
# `GIT_ALTERNATE_OBJECT_DIRECTORIES` change where objects are read from, not
# whose history is being read, so dropping them buys nothing against this
# threat and actively breaks git's own push-quarantine environment, where a
# `pre-receive` or `update` hook reaches the pushed objects only through the
# alternates. Scrubbing them there made a resolvable HEAD report
# "no commit on HEAD" -- a cause that is not the observed state, which is the
# defect this module reports in other artifacts.
_GIT_DISCOVERY_ENV = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_NAMESPACE",
)


def _git_env() -> dict[str, str]:
    """The ambient environment with git's discovery overrides removed."""
    return {k: v for k, v in os.environ.items() if k not in _GIT_DISCOVERY_ENV}


def _default_since(root: Path) -> tuple[str | None, str]:
    """Merge-base with the default branch, plus why it could not be resolved.

    Returns ``(object_id, reason)``; exactly one is empty. A caller that does
    not supply ``--since`` still gets rule 9, because a rule whose input is
    optional is a rule that does not run: its no-input line prints alongside a
    zero finding count and the summary reads as a pass.

    The reason names the state actually observed, never a state inferred from
    the absence of another. Reporting "no default branch" for a branch that
    resolved but had no merge-base would be the same defect this rule exists to
    report: a no-input line whose stated cause sends the reader to repair
    something that is not broken. Every return below therefore carries the
    state it observed, and a new one owes a reason of its own.

    Bounded to ``root``. `git -C` discovers the *enclosing* repository, so a
    spec tree nested inside an unrelated checkout would otherwise resolve a
    base from that checkout and run rule 9 against history the caller never
    pointed at, with nothing in the output saying which repository answered.
    Under an explicit ``--since`` that base is at least caller-chosen; as a
    default it is not, so a root that is not itself a repository declines
    rather than borrows one.
    """
    class _Unavailable(Exception):
        """git did not answer: not started, or started and never finished.

        Distinct from git answering "no", which is a return value.
        """

    def _git(*args: str) -> str | None:
        """Stdout, or None when git ran and declined. None is not "empty".

        Failing to invoke git raises instead of returning None, because the two
        are different states and the caller must not report one as the other.
        """
        try:
            done = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True, text=True, check=False, timeout=30,
                env=_git_env(),
            )
        except (OSError, subprocess.SubprocessError) as exc:   # includes timeout
            raise _Unavailable from exc
        return done.stdout.strip() if done.returncode == 0 else None

    try:
        # `--show-toplevel` is the confinement check: it answers with the
        # discovered repository's root, which is only `root` when `root` is
        # that repository rather than a directory sitting inside one.
        if not root.is_dir():
            # A guard, not a reported state: with a file as `--root` the spec
            # glob is empty and nothing prints this, and an explicit spec_dir
            # under it exits 2 on confinement first. It exists so git is never
            # asked about a file, and is asserted by calling this function
            # directly rather than through the summary.
            return None, "root is not a directory"
        toplevel = _git("rev-parse", "--show-toplevel")
        if toplevel is None:
            # `--show-toplevel` fails both outside a repository and inside a
            # bare one, which are different states. `--is-inside-work-tree`
            # separates them: it answers `false` from a bare repository and
            # fails outside one altogether. Other git refusals -- dubious
            # ownership under `safe.directory`, say -- land on whichever of
            # these two they resolve to; telling those apart needs stderr,
            # which is not read here, so no attempt is made to name them.
            if _git("rev-parse", "--is-inside-work-tree") is not None:
                return None, "repository has no work tree"
            return None, "no git repository"
        if Path(toplevel).resolve() != root.resolve():
            return None, "root is not a repository root"
        head = _git("rev-parse", "--verify", "--quiet", "HEAD^{commit}")
        if head is None:
            return None, "no commit on HEAD"
        unrelated: list[str] = []
        for candidate in _DEFAULT_BASE_REFS:
            # The verified object id is what reaches `merge-base`, so a ref
            # that moves between the two calls cannot change the answer.
            resolved = _git("rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}")
            if resolved is None:
                continue
            base = _git("merge-base", head, resolved)
            if base:
                return base, ""
            unrelated.append(candidate)
    except _Unavailable:
        return None, "git could not be consulted"
    if unrelated:
        return None, f"no merge-base with {', '.join(unrelated)}"
    return None, f"no default branch among {', '.join(_DEFAULT_BASE_REFS)}"


def _changed_lines(root: Path, ref: str, path: Path) -> set[int] | None:
    """New-file line numbers touched since ``ref``, or None when git cannot say.

    None is not an empty set. An unresolvable ref, a tree with no history and a
    missing git binary all mean "unknown", and reporting them as "nothing
    changed" would turn every one of them into a silent clean pass.
    """
    # A caller-supplied revision is data, never an option. `--` separates the
    # pathspec from revisions but not revisions from flags, so a ref beginning
    # with a dash would be read by git as one; `--end-of-options` is the only
    # separator that closes the option list itself.
    if not _REF.fullmatch(ref):
        return None
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "diff", "-U0", "--end-of-options",
             ref, "--", str(path)],
            capture_output=True, text=True, check=False, timeout=30,
            env=_git_env(),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    touched: set[int] = set()
    for hunk in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", done.stdout, re.M):
        start = int(hunk.group(1))
        touched.update(range(start, start + int(hunk.group(2) or 1)))
    return touched


def criterion_spans(spec: str) -> list[str | None]:
    """One entry per 1-indexed spec line, naming the criterion it falls under."""
    spans: list[str | None] = [None]      # index 0 unused; spans[n] is line n
    current: str | None = None
    for line in spec.splitlines():
        found = CRITERION_LINE.match(line)
        if found:
            current = found.group(1)
        elif line.startswith("## "):
            current = None
        spans.append(current)
    return spans


def _entry_lines(plan: str) -> set[int]:
    """The 1-indexed lines inside a task's ``Tests:`` or ``Done when:`` block.

    An assertion only ever lives in one of those two blocks. Crediting a change
    anywhere in the document reproduces the mention-anywhere defect rule 5 was
    scoped to eliminate: a changelog bullet naming a criterion silenced this
    rule for eight of them on the contract it was written for.
    """
    inside: set[int] = set()
    for task in TASK.finditer(plan):
        body, base = task.group(2), plan[: task.start(2)].count("\n") + 1
        for entry in ENTRY.finditer(body):
            first = base + body[: entry.start()].count("\n")
            inside.update(range(first, first + entry.group(0).count("\n") + 1))
    return inside


def _plan_owners(plan: str, changed: set[int]) -> set[str]:
    """Which criteria the changed assertion lines belong to.

    A changed line is credited to the criteria named by the bullet it sits
    under, not only to the criteria spelled on the line itself. An added
    constraint is normally written beneath the bullet that already names the
    identifier, so reading the line alone reports a criterion whose assertion
    did in fact follow -- the false alarm this rule cannot afford, since its
    whole value is that it never cries wolf. The scope is the assertion blocks,
    for the reason ``_entry_lines`` records.
    """
    owners: set[str] = set()
    current: set[str] = set()
    entries = _entry_lines(plan)
    for number, line in enumerate(plan.splitlines(), 1):
        stripped = line.lstrip()
        # Only a line-initial field label is a boundary. An *indented* bold
        # label is a constraint written inside a bullet -- exactly where a new
        # assertion lands -- and treating it as a boundary drops the bullet's
        # identifier, which is the same distinction the ENTRY pattern above
        # already had to make.
        if stripped.startswith("- ") or re.match(r"\*\*[A-Z][A-Za-z ]*:\*\*", line) \
                or line.startswith(("#", "|")):
            current = set(CRITERION_REF.findall(line))
        elif not stripped:
            current = set()
        if number in changed and number in entries:
            owners.update(current or CRITERION_REF.findall(line))
    return owners


def stale_assertions(spec_dir: Path, root: Path, ref: str,
                     spec: str, plan: str) -> list[str] | None:
    """Criteria reworded since ``ref`` whose plan lines did not change with them.

    The plan side reads only the task entries that carry assertions. Reading any
    line naming the identifier lets a changelog bullet or a rationale count as
    the assertion following, which is the mention-anywhere form rule 5 is scoped
    to eliminate; narrowing the scope also raised this rule's recall, because the
    wide form had been crediting exactly those non-assertion mentions.
    """
    spec_changed = _changed_lines(root, ref, spec_dir / "spec.md")
    plan_changed = _changed_lines(root, ref, spec_dir / "plan.md")
    if spec_changed is None or plan_changed is None:
        return None
    spans = criterion_spans(spec)
    reworded = {spans[n] for n in spec_changed if n < len(spans) and spans[n]}
    followed = _plan_owners(plan, plan_changed)
    return sorted(reworded - followed)


def check(spec_dir: Path, root: Path | None = None,
          since: str | None = None,
          no_since_reason: str = "no --since",
          ) -> tuple[list[str], bool, list[str], list[str]]:
    """Return failing findings, whether the check ran, rules with no input, and
    findings that report without failing.

    ``no_since_reason`` labels rule 9's no-input line when ``since`` is absent.
    `main` resolves the default base once per run and passes the reason here, so
    a run that could not resolve one says which, rather than reading as a caller
    who chose not to ask.

    The second value distinguishes "no findings" from "not applicable"; the third
    distinguishes "no findings" from "some rules had no input". A caller that
    cannot tell those apart reads a partial check as a clean one, which is the
    failure this module exists to detect in other artifacts.
    """
    spec_path, plan_path = spec_dir / "spec.md", spec_dir / "plan.md"
    if not spec_path.is_file():
        # Root-relative like every other finding: an absolute host path is wrong
        # in a review, a commit message and an issue alike.
        try:
            where = spec_dir.relative_to(root).as_posix() if root else spec_dir.as_posix()
        except ValueError:
            where = spec_dir.as_posix()
        return [f"{where}: {FINDING_KINDS['no-spec']}"], False, [], []
    spec = _read_confined(spec_path, root)
    plan = _read_confined(plan_path, root) if plan_path.is_file() else ""
    # A refused spec.md ends the directory: every rule reads it. A refused
    # plan.md does not -- rules 1, 2, 3 and 6 decide their whole subject from
    # spec.md alone, and returning one refusal for the directory reported them
    # as neither run nor input-less, which is the partial-read-as-clean failure
    # this module exists to detect in other artifacts. So the refusal is its own
    # finding and the plan-reading rules go on the no-input list, exactly as an
    # absent plan.md already does.
    if spec is None:
        return ([f"{_rel(spec_dir, root)}/spec.md: {FINDING_KINDS['unconfined']}"],
                False, [], [])
    plan_refusal = plan is None
    if plan_refusal:
        plan = ""

    criteria = CRITERION.findall(spec)
    if not criteria:
        # Forward-only: unlabelled specs are skipped by the criterion rules,
        # which have nothing to map. The ownership rules read the plan alone,
        # so they still run -- returning here left them unreachable for every
        # spec predating the identifier grammar, which is most of the corpus.
        owned, owned_reported = design_ownership_findings(_rel(spec_dir, root), plan)
        # `ran` stays False: the criterion rules did not run, and the summary's
        # checked-versus-skipped count is what tells a caller that. Ownership
        # findings still surface, because they were decided from the plan.
        ownership_rules = ["unowned-design", "undefined-owner"]
        return owned, False, [] if plan else ownership_rules, owned_reported

    findings: list[str] = []
    if plan_refusal:
        findings.append(f"{_rel(spec_dir, root)}/plan.md: {FINDING_KINDS['unconfined']}")
    reported: list[str] = []
    # Relative to the invocation root, not an absolute host path: a finding is
    # pasted into a review, a commit message and an issue, and an absolute path
    # is wrong in all three.
    try:
        rel = spec_dir.relative_to(root).as_posix() if root else spec_dir.as_posix()
    except ValueError:
        rel = spec_dir.as_posix()

    seen: set[str] = set()
    for ident in criteria:                                        # rules 1-3
        if ident in seen:
            findings.append(f"{rel}/spec.md: {ident} {FINDING_KINDS['duplicate']}")
        seen.add(ident)
    for ident in sorted(seen & retired(spec)):
        findings.append(f"{rel}/spec.md: {ident} {FINDING_KINDS['retired']}")
    # Scoped to the section, not the document. A spec legitimately carries
    # checkboxes elsewhere -- a rollout step, a migration list -- and scanning
    # the whole file reported those as unlabelled criteria and failed a valid
    # spec. Line numbers are offset back to the file so the finding is locatable.
    section = _section(spec, "Acceptance Criteria")
    offset = spec[: spec.find(section)].count("\n") if section else 0
    for lineno, line in enumerate(section.splitlines(), 1):
        if UNLABELLED.match(line + "\n"):
            findings.append(
                f"{rel}/spec.md:{lineno + offset}: {FINDING_KINDS['unlabelled']}"
            )

    # Rule 4 resolves against live criteria *and* the retired list. Without the
    # second half, retiring a criterion -- the one operation the retired list
    # exists for -- reports the retired identifier as unresolved and fails a
    # correctly retired spec.
    resolvable = seen | retired(spec)
    for name, text in (("spec.md", spec), ("plan.md", plan)):     # rules 1 and 4
        for bad in sorted(set(MALFORMED.findall(text))):
            findings.append(f"{rel}/{name}: {FINDING_KINDS['malformed']} {bad}")
        for ref in sorted(set(CRITERION_REF.findall(text)) - resolvable):
            findings.append(f"{rel}/{name}: {ref} {FINDING_KINDS['unresolved']}")

    unapplied: list[str] = [] if plan else list(PLAN_GATED)
    if plan:                                                      # rule 5
        named = task_entries(plan)
        mentioned = set(CRITERION_REF.findall(plan))
        for ident in criteria:
            if ident not in named:
                hint = (" (mentioned in plan, but not in a task entry)"
                        if ident in mentioned else "")
                findings.append(f"{rel}/plan.md: {ident} {FINDING_KINDS['no-task-entry']}{hint}")

        owned, owned_reported = design_ownership_findings(rel, plan)
        findings.extend(owned)
        reported.extend(owned_reported)

    groups = verification_groups(spec)                            # rule 6
    for ident in criteria:
        count = groups.get(ident, 0)
        if count != 1:
            where = "no verification group" if count == 0 else f"{count} verification groups"
            findings.append(f"{rel}/spec.md: {ident} {FINDING_KINDS['group-count']} {where}")

    if plan:                                                      # rule 8
        for task, body in TASK.findall(plan):
            for entry in ENTRY.findall(body):
                if unterminated(entry):
                    findings.append(
                        f"{rel}/plan.md: {task} {FINDING_KINDS['broken-entry']}"
                    )
                    break     # one finding per task; a broken entry usually breaks one clause

    # Rule 9's no-input line always names its cause. Resolving a base by default
    # makes `since` almost always set, so the diff-unreadable and no-plan paths
    # below are now the reachable ones; leaving either bare would report an
    # un-run rule without saying what to supply, which is the shape this rule
    # exists to report in other artifacts. The diff-unreadable path is reached
    # by `--since` naming a revision git cannot diff -- covered by the
    # unresolvable-ref case in the suite, which drives exactly this branch.
    if since and plan:                                            # rule 9
        stale = stale_assertions(spec_dir, root or spec_dir, since, spec, plan)
        if stale is None:
            unapplied.append(f"stale-assertion (git could not diff since {since})")
        else:
            for ident in stale:
                # Reported, never failing. This rule over-reports by construction
                # -- a criterion trimmed with its obligation unchanged needs no
                # new assertion and is reported anyway -- so exiting non-zero on
                # it would fail a build for a prose edit.
                reported.append(
                    f"{rel}/plan.md: {ident} {FINDING_KINDS['stale-assertion']} plan.md "
                    f"since {since}"
                )
    elif since:
        unapplied.append("stale-assertion (no plan.md)")
    else:
        unapplied.append(f"stale-assertion ({no_since_reason})")

    for item in sorted(set(ITEM_REF.findall(plan))):              # rule 7
        digits = item.split("-")[1]
        if f"AC-{digits}" in seen:
            findings.append(
                f"{rel}/plan.md: {item} {FINDING_KINDS['derived-item']} AC-{digits}; "
                f"a verification "
                f"item's identifier is its own, never derived from what it serves"
            )
    return findings, True, unapplied, reported


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(),
                        help="repository root every path is resolved and confined to")
    parser.add_argument("--verbose", action="store_true",
                        help="list every finding instead of capping the listing")
    # Mutually exclusive: naming a base and refusing one are contradictory, and
    # silently letting one win would make the rule's input depend on argument
    # order rather than on what the caller asked for.
    base = parser.add_mutually_exclusive_group()
    base.add_argument("--since", metavar="REF",
                      help="base revision for the reworded-criterion rule; "
                           "defaults to the merge-base with the default branch, "
                           "and is skipped when neither that nor this revision "
                           "can be resolved")
    base.add_argument("--no-since", action="store_true",
                      help="do not resolve a default base revision; leaves the "
                           "reworded-criterion rule on the no-input list")
    parser.add_argument("spec_dir", nargs="*", type=Path)
    args = parser.parse_args(argv)

    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    root = args.root.resolve()
    targets = [d.resolve() for d in args.spec_dir] or sorted(
        p.parent for p in (root / "docs" / "specs").glob("*/spec.md")
    )

    # Resolved once, before the loop: every target shares one working tree, so
    # a per-target call would re-answer the same question N times.
    if args.no_since:
        since, no_since_reason = None, "--no-since"
    elif args.since is not None:
        # An empty `--since` is the `--since "$BASE"` form with `BASE` unset.
        # Reporting it as "no --since" would name a state the caller was not
        # in; resolving a default would silently substitute a base they did
        # not choose. Refusing is the only answer that is true.
        if not args.since.strip():
            parser.error("--since was given an empty revision")
        since, no_since_reason = args.since, "no --since"
    else:
        since, no_since_reason = _default_since(root)

    findings, ran, skipped, absent, partial, reported = [], 0, 0, 0, [], []
    for target in targets:
        if root not in target.parents and target != root:
            print(f"lint-contract-item-alignment: {FINDING_KINDS['unconfined']}: {target}")
            return 2
        found, applied, unapplied, noted = check(target, root, since, no_since_reason)
        findings.extend(found)
        reported.extend(noted)
        ran += applied
        # A directory with no spec.md is its own state. Folding it into
        # "skipped as unlabelled" reports one state under another's label, which
        # is the partial-read-as-clean conflation this module exists to detect.
        if any(f.endswith(FINDING_KINDS["no-spec"]) for f in found):
            absent += 1
        else:
            skipped += not applied
        if unapplied:
            partial.append(f"{target.name}: {', '.join(unapplied)}")

    shown = findings if (args.verbose or len(findings) <= FINDING_CAP) else findings[:FINDING_CAP]
    for finding in shown:
        print(f"lint-contract-item-alignment: {finding}")
    if len(shown) < len(findings):
        # Grouped by spec rather than truncated mid-list: the reader needs to
        # know which specs are affected, which a flat cut-off hides.
        from collections import Counter
        rest = Counter(f.split(":", 1)[0] for f in findings[FINDING_CAP:])
        for spec, count in rest.most_common(10):
            print(f"lint-contract-item-alignment: {count} {FINDING_KINDS['capped']} {spec}")
        if len(rest) > 10:
            print(f"lint-contract-item-alignment: and {len(rest) - 10} further spec(s)")
        print(f"lint-contract-item-alignment: {len(findings) - len(shown)} finding(s) "
              f"not listed; re-run with --verbose for the full list")
    # Bounded like the failing list, and for the same reason: this rule
    # over-reports by design over a default target set of every spec, so an
    # uncapped channel floods the reader with the cheaper findings.
    shown_notes = reported if (args.verbose or len(reported) <= FINDING_CAP) \
        else reported[:FINDING_CAP]
    for note in shown_notes:
        print(f"lint-contract-item-alignment: reported, not failing: {note}")
    if len(shown_notes) < len(reported):
        print(f"lint-contract-item-alignment: {len(reported) - len(shown_notes)} "
              f"further reported, not failing; re-run with --verbose")
    summary = (f"lint-contract-item-alignment: {len(findings)} finding(s); "
               f"{ran} spec(s) checked, {skipped} skipped as unlabelled")
    if absent:
        summary += f", {absent} with no spec.md"
    if reported:
        summary += f", {len(reported)} reported without failing"
    if partial:
        summary += f", {len(partial)} partial (rules with no input: {'; '.join(partial)})"
    print(summary + ".")
    # Only the failing rules set the exit code. A caller can therefore tell a
    # contract that breaks a rule from one a reporting rule merely flagged.
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
