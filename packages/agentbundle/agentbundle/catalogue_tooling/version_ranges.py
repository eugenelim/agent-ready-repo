"""Small, dependency-free parser for the catalogue dependency range contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering

_VERSION_RE = re.compile(
    r"^(0|[1-9]\d*)"
    r"(?:\.(0|[1-9]\d*))?"
    r"(?:\.(0|[1-9]\d*))?"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
_ATOM_RE = re.compile(r"^(\^|~|>=|<=|>|<|=)?(.+)$")


@total_ordering
@dataclass(frozen=True, eq=False)
class _Version:
    """Comparable semantic version with missing minor/patch normalized to zero."""

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...]
    components: int

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _Version):
            return NotImplemented
        return (
            self.major,
            self.minor,
            self.patch,
            self.prerelease,
        ) == (
            other.major,
            other.minor,
            other.patch,
            other.prerelease,
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, _Version):
            return NotImplemented
        release = (self.major, self.minor, self.patch)
        other_release = (other.major, other.minor, other.patch)
        if release != other_release:
            return release < other_release
        if not self.prerelease:
            return False
        if not other.prerelease:
            return True
        for left, right in zip(self.prerelease, other.prerelease, strict=False):
            if left == right:
                continue
            left_numeric = left.isdigit()
            right_numeric = right.isdigit()
            if left_numeric and right_numeric:
                left_number = left.lstrip("0") or "0"
                right_number = right.lstrip("0") or "0"
                if len(left_number) != len(right_number):
                    return len(left_number) < len(right_number)
                return left_number < right_number
            if left_numeric != right_numeric:
                return left_numeric
            return left < right
        return len(self.prerelease) < len(other.prerelease)


def _parse_version(value: object) -> _Version | None:
    if not isinstance(value, str):
        return None
    match = _VERSION_RE.fullmatch(value.strip())
    if match is None:
        return None
    try:
        components = 1 + int(match.group(2) is not None) + int(match.group(3) is not None)
        prerelease = tuple(match.group(4).split(".")) if match.group(4) else ()
        return _Version(
            int(match.group(1)),
            int(match.group(2) or 0),
            int(match.group(3) or 0),
            prerelease,
            components,
        )
    except (ValueError, OverflowError):
        return None


def _compare(candidate: _Version, operator: str, boundary: _Version) -> bool:
    if operator in ("", "="):
        return candidate == boundary
    if operator == ">=":
        return candidate >= boundary
    if operator == ">":
        return candidate > boundary
    if operator == "<=":
        return candidate <= boundary
    if operator == "<":
        return candidate < boundary
    if operator == "^":
        if boundary.major:
            upper = _Version(boundary.major + 1, 0, 0, (), 3)
        elif boundary.minor:
            upper = _Version(0, boundary.minor + 1, 0, (), 3)
        else:
            upper = _Version(0, 0, boundary.patch + 1, (), 3)
        return candidate >= boundary and candidate < upper
    if operator == "~":
        if boundary.components == 1:
            upper = _Version(boundary.major + 1, 0, 0, (), 3)
        else:
            upper = _Version(boundary.major, boundary.minor + 1, 0, (), 3)
        return candidate >= boundary and candidate < upper
    return False


def _parse_atoms(expression: object) -> list[tuple[str, _Version]] | None:
    if not isinstance(expression, str) or not expression.strip():
        return None
    atoms: list[tuple[str, _Version]] = []
    for raw_atom in expression.split():
        match = _ATOM_RE.fullmatch(raw_atom)
        if match is None:
            return None
        operator = match.group(1) or ""
        version = _parse_version(match.group(2))
        if version is None:
            return None
        atoms.append((operator, version))
    if len(atoms) > 1 and any(operator in ("", "^", "~", "=") for operator, _ in atoms):
        return None
    return atoms


def parse_version_range(expression: object) -> bool:
    """Return whether *expression* uses the supported dependency range grammar."""
    return _parse_atoms(expression) is not None


def version_satisfies(version: object, expression: object) -> bool | None:
    """Return range satisfaction, or ``None`` when either input is malformed."""
    candidate = _parse_version(version)
    atoms = _parse_atoms(expression)
    if candidate is None or atoms is None:
        return None
    return all(_compare(candidate, operator, boundary) for operator, boundary in atoms)
