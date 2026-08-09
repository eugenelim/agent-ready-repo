#!/usr/bin/env python3
"""Differential test: tools/pack_scope.py vs commands/validate.py:_allowed_scopes.

Runs under the gate chain. The mirror exists because `tools/` is stdlib-only;
this is what stops it drifting from the resolver it mirrors. If `agentbundle` is
not importable the differential half skips — but the mirror's own behavioural
cases still run, so the gate never degrades to nothing.
"""

from __future__ import annotations

import importlib.util
import itertools
import sys
import tomllib
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "pack_scope", Path(__file__).parent / "pack_scope.py"
)
mirror = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mirror)

FAILURES: list[str] = []


def _check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL {name}: {detail}")


def _pack(version, scopes, default=None) -> dict:
    src = '[pack]\nname = "p"\nversion = "1.0.0"\n'
    if version is not None:
        src += f'[pack.adapter-contract]\nversion = "{version}"\n'
    body = ""
    if default is not None:
        body += f'default-scope = "{default}"\n'
    if scopes is not None:
        body += "allowed-scopes = [" + ", ".join(f'"{s}"' for s in scopes) + "]\n"
    if body:
        src += "[pack.install]\n" + body
    return tomllib.loads(src)


VERSIONS = [None, "0.1", "0.2", "0.3", "0.17"]
SCOPES = [None, ["repo"], ["user"], ["repo", "user"]]
DEFAULTS = [None, "repo", "user"]


def main() -> int:
    print("test-pack-scope:")

    # The trap the mirror exists to reproduce faithfully.
    _check("contract version gates, not the install table",
           mirror.allowed_scopes(_pack(None, ["repo", "user"])) == ["repo"],
           "a pack with no [pack.adapter-contract] must resolve ['repo']")
    _check("declared contract honours the install table",
           mirror.allowed_scopes(_pack("0.3", ["repo", "user"])) == ["repo", "user"])
    _check("is_user_capable follows allowed_scopes",
           mirror.is_user_capable(_pack("0.3", ["repo", "user"]))
           and not mirror.is_user_capable(_pack("0.3", ["repo"])))

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "agentbundle"))
    try:
        import agentbundle  # noqa: F401 - genuine-absence probe only
    except ModuleNotFoundError as exc:
        print(f"  skip differential half — agentbundle not installed ({exc})")
    else:
        # Deliberately OUTSIDE the except: a moved or renamed
        # `commands.validate` raises ModuleNotFoundError too, so catching it
        # here would skip on the exact drift this gate exists to catch — the
        # same defect one level up from the symbol check below.
        import agentbundle.commands.validate as _validate

        _allowed_scopes = getattr(_validate, "_allowed_scopes", None)
        _allowed_scopes = getattr(_validate, "_allowed_scopes", None)
        if _allowed_scopes is None:
            _check("the canonical resolver is still where the mirror mirrors it from",
                   False,
                   "commands/validate.py:_allowed_scopes is gone — the mirror "
                   "in tools/pack_scope.py now tracks nothing")
            print("test-pack-scope: FAIL (1)", file=sys.stderr)
            return 1
        _check("the canonical resolver is still where the mirror mirrors it from", True)
        mismatches = []
        for version, scopes, default in itertools.product(
            VERSIONS, SCOPES, DEFAULTS
) if True else []:
            meta = _pack(version, scopes, default)
            if mirror.allowed_scopes(meta) != _allowed_scopes(meta):
                mismatches.append(
                    f"version={version!r} scopes={scopes!r} default={default!r}: "
                    f"mirror={mirror.allowed_scopes(meta)!r} "
                    f"canonical={_allowed_scopes(meta)!r}"
                )
        _check(
            f"mirror matches canonical across {len(VERSIONS) * len(SCOPES) * len(DEFAULTS)} cells",
            not mismatches,
            "; ".join(mismatches[:3]),
        )

    if FAILURES:
        print(f"test-pack-scope: FAIL ({len(FAILURES)})", file=sys.stderr)
        return 1
    print("test-pack-scope: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
