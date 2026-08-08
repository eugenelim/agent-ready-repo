# Guard sweep and the `self_host_windows.py` decision

Closes AC12 and AC13 of [`../spec.md`](../spec.md). Written during T2.

## AC12 — sweep for other substring-shaped path guards

**Result: `self_host.py` was the only one.**

The failure mode being hunted: a security or safety decision made by testing
whether one *string* appears inside a path, rather than by testing path
*components*. It breaks silently whenever a directory is inserted between the
two parts being matched — which is exactly what RFC-0082's relocation did to
`"tests/fixtures/" in packs_dir.as_posix()`, turning a destructive-write refusal
into a pass-through with no test going red.

Scope swept: `packages/agentbundle/agentbundle/**` (shipped engine code),
excluding test trees.

Patterns searched: string membership against `as_posix()` / `str(path)`;
`"…/" in <path>` forms; and `startswith` / `endswith` against path-shaped
literals, which fail the same way when a prefix is not anchored.

| Site | Form | Verdict |
| --- | --- | --- |
| `build/self_host.py:1611` | `"tests/fixtures/" in packs_dir.as_posix()` | **The defect.** Rewritten to component matching in T2. |
| `https_catalogue.py:418` | `".." in name.split("/") or name.startswith("/")` | Safe — already splits into components. |
| `catalogue_tooling/package.py:154` | `entry.startswith("packs/")` + `".." in parts` | Safe — anchored prefix plus a component check. |
| `scaffold.py:166` | `rel.startswith("/")` | Safe — tests for absoluteness, not for a path segment. |
| `commands/install.py:3857` | `relpath.startswith("tools/hooks/")` | Safe — anchored at the root of a relative path. |
| `commands/upgrade.py:1695` | `relpath.startswith("/")` | Safe — normalisation, not a guard. |

Two of these — `https_catalogue.py` and `package.py` — already use the component
form. The repo's prevailing pattern was correct; `self_host.py` was the outlier,
and it survived because nothing exercised the shape it got wrong.

**What made it dangerous rather than merely wrong:** the guard fails *open*, and
its covering test passed a hardcoded literal that matched under the old shape.
So the control would have died silently with a green suite. That is why AC7
required the covering test to drive a real path, and why T2 added a case for the
relocated shape specifically.

## AC13 — `catalogue_tooling/self_host_windows.py` stays

RFC-0082 open question 2 asks whether this module belongs inside the export
boundary. It is a test runner: it shells out to `pytest` against named suites,
and it ships in the wheel, the zipapp, and the vendored copy. RFC-0082's
recommended default was to relocate it.

**Decision: it stays, and its invocation paths were updated in place by T1.**

Two reasons, in order of weight:

1. **It is the Windows build-check leg.** `build-check-windows.yml` drives
   `agentbundle catalogue self-host --check --windows`, which is this module.
   Relocating it out of the package means the shipped CLI can no longer reach it,
   so the leg needs a different entry point — a change to what the engine
   *exposes*, not to where its tests live. That is a different decision from the
   one this spec is making.
2. **Its ownership is the carve-out spec's question.** Under ADR-0075's taxonomy
   it is tools-owned or engine-owned depending on whether you read it as a runner
   or as engine behaviour, and that judgement belongs with the other ~100
   modules being classified, not decided in isolation here.

**The cost of deferring, stated plainly:** the wheel, zipapp, and vendored copy
each still ship a runner that points at `tests/build_pipeline/` — a tree those
artifacts deliberately do not contain. Running it from an installed artifact
fails. That was already true before this spec (it pointed at
`agentbundle/build/tests/`, equally absent), so this defers a pre-existing
oddity rather than introducing one. The carve-out spec should close it.
