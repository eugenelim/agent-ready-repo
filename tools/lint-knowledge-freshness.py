#!/usr/bin/env python3
"""Recompute every pinned source digest in `docs/knowledge/topics/`.

A v1 knowledge topic may pin the bytes of the repository file it was learned
from: `owning_source` and each entry of `supporting_sources` can carry a
`digest` of kind `sha256-bytes-v1`. Nothing recomputes those pins. A topic's
`freshness.state` is *derived from its `lifecycle`* by the writer
(`active` -> `fresh`), so the stored state cannot go stale however far the
cited file has moved. The only live check in the shipped store is
`read_freshness_source`, and it is narrower three ways at once: one topic per
call, on demand inside `--enquire`, and `owning_source` only — a drifted
`supporting_sources` pin is invisible to it.

This is the repo-wide recomputation that closes that gap. It is deliberately
repo-only and lives in `tools/`, never in `tools/hooks/pre-pr.py`, which is
projected to adopters and must not call a script absent from their tree.

**Not yet wired into any gate chain.** Adding a required pull-request step is a
governance-surface change and is specified separately. Running this today over
the real corpus exits 1: 42 of 69 pinned sources are stale across 29 of 100
topics. `--max-stale N` tolerates a declared baseline so the wiring change can
ratchet it down rather than repairing all 42 first.

Two refusals are deliberately *not* subject to `--max-stale`, because a
baseline is a statement about known drift and neither of these is drift:

  * An **unresolved** pin — the cited path is gone, is not a confined
    single-link regular file, or cannot be read. The topic cites something that
    is not there, which is worse than citing it inaccurately.
  * A **zero-pin** run — no pinned source was examined at all. Without this,
    a wrong `--root`, a renamed directory, or an emptied corpus would report a
    clean exit having checked nothing, which is the failure mode this corpus
    records under "an empty-set assertion needs a positive control".

A malformed topic file is a hard error, never a silent skip. "Malformed" means
exactly what the knowledge store means by it, because the checker does not read
the corpus itself: it asks the store's own reader, `_bounded_topic_records`,
loaded from the canonical `packs/core/.apm/skills/project-knowledge/` source.
That reader owns every rule about what a topic corpus is — the recursive walk
over nested topic keys, the key-to-path match, strict JSON with duplicate keys
and non-finite numbers refused, `validate_topic`, size and count budgets, and
confinement against symlinked directories. Three review rounds each found one
more of those rules missing from a checker that re-implemented them, so the
checker now holds none of them.

The reader refuses the whole corpus at the first bad file and its refusal
names no path. The checker then names the file on a best-effort basis by
re-checking each topic with the store's own per-file reader and path rule; the
refusal itself is the store's decision, and naming only explains it. Anything
the reader raises counts as a refusal — not only `KnowledgeStoreError` —
because the store's validator crashes with `TypeError` on some shapes, and a
crash must still produce the diagnostic and, under `--json`, the JSON error
object.

That dependency is on a private function. A store refactor that renames or
reshapes it makes this checker refuse every run, which fails closed rather
than reporting a clean corpus.

Of the two digest kinds the schema admits only `sha256-bytes-v1` is
recomputed. A `git-blob-v1` pin is schema-valid and reported as unresolved
under its own reason — not as unknown, and not as unreadable — so a topic that
adopts it fails visibly until this checker learns to verify it. No topic uses
it today.

Exit 0 when every pin verifies, or when the stale count is within
`--max-stale` and nothing is unresolved. Exit 1 otherwise.

**Why this does not sit on `tools/lint_harness.py`.** That driver is the right
home for a single-rule lint and `tools/AGENTS.md` asks new lints to use it, but
it owns the exit status as `1` whenever the walk produced any violation. Here a
violation and a failure are not the same event: a stale pin inside `--max-stale`
is reported and still exits 0, while an unresolved pin exits 1 whatever the
baseline says. Those three statuses over two violation classes are the whole
point of the check, and expressing them through `RuleAbort` would hide the
baseline rule inside control flow. The paired self-test does use the shared
`tools/selftest_harness.py` accumulator, which fits without reinterpretation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple

SOURCE_ROOT = Path(__file__).resolve().parent.parent
TOPICS_RELATIVE = Path("docs/knowledge/topics")
PINNED_DIGEST_KIND = "sha256-bytes-v1"
STORE_SOURCE = (
    SOURCE_ROOT
    / "packs"
    / "core"
    / ".apm"
    / "skills"
    / "project-knowledge"
    / "scripts"
    / "knowledge_store.py"
)
# A pinned source is repository prose or code. The largest file any topic cites
# today is well under this; the bound exists so an unexpectedly huge cited file
# is reported rather than read into memory.
MAX_SOURCE_BYTES = 8 * 1024 * 1024


class Stale(NamedTuple):
    """A pin whose cited file exists but no longer matches the pinned bytes."""

    topic_key: str
    role: str
    path: str
    pinned_sha256: str
    actual_sha256: str
    pinned_bytes: int
    actual_bytes: int


class Unresolved(NamedTuple):
    """A pin whose cited file could not be read as a confined regular file."""

    topic_key: str
    role: str
    path: str
    reason: str


def _file_safety() -> ModuleType:
    """Load the repository's blessed file-safety code from a source checkout."""
    source = (
        SOURCE_ROOT
        / "packages"
        / "agentbundle"
        / "agentbundle"
        / "catalogue_tooling"
        / "file_safety.py"
    )
    spec = importlib.util.spec_from_file_location("_knowledge_freshness_safety", source)
    if spec is None or spec.loader is None:
        raise ValueError("file-safety-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _knowledge_store() -> ModuleType:
    """Load the store whose `validate_topic` defines what a malformed topic is."""
    spec = importlib.util.spec_from_file_location("_knowledge_freshness_store", STORE_SOURCE)
    if spec is None or spec.loader is None:
        raise ValueError("knowledge-store-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pinned_sources(topic: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Return every `(role, source)` pin in a topic `validate_topic` accepted.

    `role` names where the pin sits so a diagnostic can distinguish a drifted
    `owning_source` from a drifted `supporting_sources[2]`; the two are
    different claims about the topic and only the first is reachable from the
    shipped `read_freshness_source`. The store's reader guarantees every source
    here carries a path and a digest, so nothing is filtered out.
    """
    pairs: list[tuple[str, dict[str, Any]]] = []
    if topic["owning_source"] is not None:
        pairs.append(("owning_source", topic["owning_source"]))
    for index, source in enumerate(topic["supporting_sources"]):
        pairs.append((f"supporting_sources[{index}]", source))
    return pairs


def _refusal_detail(exc: Exception) -> str:
    """Render a store refusal as `Type: reason` without assuming its shape."""
    diagnostic = getattr(exc, "diagnostic", None)
    if isinstance(diagnostic, dict) and diagnostic.get("reason_code"):
        return f"{type(exc).__name__}: {diagnostic['reason_code']}"
    return f"{type(exc).__name__}: {exc}"


def _name_refused_file(store: ModuleType, topics_dir: Path) -> str | None:
    """Return the first topic file the store refuses on its own, if one exists.

    Diagnostic only. The refusal was already decided by the store's corpus
    reader; this names a culprit so the reader of the error knows where to
    look. It uses the store's per-file reader and its key-to-path rule, and
    returns None when the refusal is corpus-wide (a budget, or a symlinked
    directory) rather than attributable to one file.
    """
    for path in sorted(topics_dir.rglob("*.json")):
        try:
            topic, _raw = store._read_topic_record(path)
            if path != topics_dir / store._topic_relative_path(topic["topic_key"]):
                return f"{path.relative_to(topics_dir)} (topic_key does not match its path)"
        except Exception as exc:  # any refusal or crash names this file
            return f"{path.relative_to(topics_dir)} ({_refusal_detail(exc)})"
    return None


def _load_corpus(root: Path, store: ModuleType) -> list[dict[str, Any]]:
    """Return every topic the store's reader accepts, or raise a named ValueError."""
    knowledge_root = root / TOPICS_RELATIVE.parent
    topics_dir = root / TOPICS_RELATIVE
    try:
        records = store._bounded_topic_records(knowledge_root)
    except Exception as exc:  # see the module docstring: a crash is a refusal too
        culprit = _name_refused_file(store, topics_dir)
        where = f" at {culprit}" if culprit else ""
        raise ValueError(
            f"malformed topic corpus — refused by the store's reader{where} "
            f"[{_refusal_detail(exc)}]"
        ) from exc
    return [topic for _path, topic, _raw in records]


def verify(root: Path) -> tuple[list[Stale], list[Unresolved], int, int]:
    """Recompute every pin under *root*, returning findings and the counts.

    Returns `(stale, unresolved, pins_examined, topics_seen)`. `pins_examined`
    is what makes a vacuous run detectable: a clean result is only meaningful
    beside the number of pins it actually hashed.
    """
    safety = _file_safety()
    store = _knowledge_store()
    if not (root / TOPICS_RELATIVE).is_dir():
        raise ValueError(f"no topics directory at {TOPICS_RELATIVE}")

    stale: list[Stale] = []
    unresolved: list[Unresolved] = []
    pins_examined = 0
    topics_seen = 0

    for topic in _load_corpus(root, store):
        topics_seen += 1
        key = topic["topic_key"]
        for role, source in pinned_sources(topic):
            digest = source["digest"]
            cited = source["path"]
            if digest["kind"] != PINNED_DIGEST_KIND:
                reason = (
                    f"digest kind {digest['kind']!r} is schema-valid but this "
                    f"checker recomputes only {PINNED_DIGEST_KIND!r}"
                )
                unresolved.append(Unresolved(key, role, cited, reason))
                continue
            pins_examined += 1
            try:
                data = safety.read_confined_regular_file(
                    root, root / cited, max_bytes=MAX_SOURCE_BYTES
                )
            except safety.UnsafeContentError as exc:
                # The helper's refusal type, BoundExceeded included. Anything
                # else is a defect in this checker and must not be reported as
                # a property of the topic.
                unresolved.append(Unresolved(key, role, cited, str(exc)))
                continue
            actual_sha = hashlib.sha256(data).hexdigest()
            if actual_sha != digest["sha256"] or len(data) != digest["byte_length"]:
                stale.append(
                    Stale(
                        key,
                        role,
                        cited,
                        digest["sha256"],
                        actual_sha,
                        digest["byte_length"],
                        len(data),
                    )
                )

    return stale, unresolved, pins_examined, topics_seen


def _report(
    stale: list[Stale],
    unresolved: list[Unresolved],
    pins_examined: int,
    topics_seen: int,
    max_stale: int,
) -> int:
    """Print the human report and return the exit code."""
    label = "knowledge freshness"
    for item in unresolved:
        print(
            f"{label}: ✖ {item.topic_key} {item.role} cites {item.path} — {item.reason}",
            file=sys.stderr,
        )
    for item in stale:
        print(
            f"{label}: ✖ {item.topic_key} {item.role} pin is stale for {item.path} "
            f"(pinned {item.pinned_sha256[:12]}… {item.pinned_bytes}B, "
            f"actual {item.actual_sha256[:12]}… {item.actual_bytes}B)",
            file=sys.stderr,
        )

    if pins_examined == 0:
        print(
            f"{label}: ✖ examined 0 pinned sources across {topics_seen} topic(s) — "
            f"nothing was checked, so a clean result would mean nothing. Check "
            f"--root and that {TOPICS_RELATIVE} holds the topic corpus.",
            file=sys.stderr,
        )
        return 1

    topics_affected = len({item.topic_key for item in (*stale, *unresolved)})
    if unresolved:
        print(
            f"{label}: {len(unresolved)} pin(s) cannot be verified. "
            f"--max-stale does not cover an unresolved pin: a baseline records "
            f"known drift, and an unverifiable pin is not drift.",
            file=sys.stderr,
        )
        return 1
    if len(stale) > max_stale:
        print(
            f"{label}: {len(stale)} stale pin(s) of {pins_examined} examined, across "
            f"{topics_affected} of {topics_seen} topic(s) — above the declared "
            f"--max-stale {max_stale}. Re-pin the topic through "
            f"`project-knowledge --distill`; do not hand-edit a topic file.",
            file=sys.stderr,
        )
        return 1

    print(
        f"{label}: ✓ {pins_examined} pinned source(s) across {topics_seen} topic(s); "
        f"{len(stale)} stale, within --max-stale {max_stale}."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, recompute every pin, and return the process exit status."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        default=str(SOURCE_ROOT),
        help="repository root holding docs/knowledge/topics/ (default: this checkout)",
    )
    parser.add_argument(
        "--max-stale",
        type=int,
        default=0,
        help="tolerated number of stale pins; unresolved pins are never tolerated",
    )
    parser.add_argument("--json", action="store_true", help="emit the findings as JSON")
    args = parser.parse_args(argv)

    if args.max_stale < 0:
        print("knowledge freshness: ✖ --max-stale cannot be negative", file=sys.stderr)
        return 1

    root = Path(args.root).resolve()
    try:
        stale, unresolved, pins_examined, topics_seen = verify(root)
    except ValueError as exc:
        if args.json:
            # Keep the JSON contract total: a consumer reading stdout gets an
            # object on every path, not an empty stream beside exit 1.
            print(json.dumps({"error": str(exc), "exit_code": 1}, indent=2, sort_keys=True))
        print(f"knowledge freshness: ✖ {exc}", file=sys.stderr)
        return 1

    if args.json:
        exit_code = 1
        if pins_examined and not unresolved and len(stale) <= args.max_stale:
            exit_code = 0
        print(
            json.dumps(
                {
                    "pins_examined": pins_examined,
                    "topics_seen": topics_seen,
                    "max_stale": args.max_stale,
                    "stale": [item._asdict() for item in stale],
                    "unresolved": [item._asdict() for item in unresolved],
                    "exit_code": exit_code,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return exit_code

    return _report(stale, unresolved, pins_examined, topics_seen, args.max_stale)


if __name__ == "__main__":
    sys.exit(main())
