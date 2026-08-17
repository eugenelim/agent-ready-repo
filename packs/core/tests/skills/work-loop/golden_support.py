"""Shared support for the pre-change golden fixtures (spec/work-loop-in-process-guards T0).

Two tests compared moved code against itself in an earlier draft of this spec —
the digest check and the message-preservation check — which is the antipattern
recorded in `docs/knowledge/topics/
a-test-that-moves-with-the-code-cannot-catch-the-code-being-wrong.json`. Both are
now golden fixtures captured from the tree *before* the guard extraction, and this
module is the single home of the pieces both the generator and the tests need.

Two invariants live here, and nowhere else:

1. `normalize()` — the canonical normalization. CLI messages interpolate resolved
   absolute paths, live 64-hex digests, and run-id UUIDs, so a literal captured in
   one `tmp_path` can never equal a replay in another. Capture and comparison both
   call this, so the comparison stays an equality rather than degrading to a
   substring match — the weak assertion the goldens exist to replace.

2. `CHANGE_REASONS` — the closed set of reasons a row's verdict is *allowed* to
   differ from the pre-change capture. A row may carry an `after` value only if it
   declares one of these, which keeps the exception list machine-readable instead
   of restated in prose in three places.

The corpus lives under `fixtures/corpus/<NNN>-<slug>/{spec.md,plan.md}` rather than
as flat renamed files, because `sha256_canonical_contract` selects its
normalization from the *filename* (`ac_section_only=(path.name != "plan.md")`) —
flattening to `001-foo.md` would silently hash every plan as if it were a spec.

`tools/lint-pack-test-boundary.py` forbids a pack test from reading above its own
pack, which is the other reason the corpus is copied in rather than referenced in
`docs/specs/`.
"""

from __future__ import annotations

import re
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CORPUS = FIXTURES / "corpus"
GOLDEN_DIGESTS = FIXTURES / "golden_digests.json"
GOLDEN_CLI_STREAMS = FIXTURES / "golden_cli_streams.json"

# Closed set. A row carrying `after` MUST declare exactly one of these; a row
# without `after` MUST declare none. The test asserts both directions, so adding
# an `after` to a row silently is not possible.
CHANGE_REASONS = frozenset({
    # AC16: numeric state fields are validated as non-negative ints instead of
    # being coerced by int(), so some values that pass today refuse afterwards.
    "numeric-coercion",
    # AC9: check-spec-status --file narrows to a single dot-free path component.
    "file-narrowing",
    # AC15(3): routing spec.md/plan.md through the bounded reader adds O_NOFOLLOW,
    # O_NONBLOCK, S_ISREG and an 8 MiB cap, so a symlinked, non-regular or
    # over-cap artifact newly refuses.
    "artifact-integrity",
})

_SHA256_RE = re.compile(r"\b[0-9a-f]{64}\b")
_SHA1_RE = re.compile(r"\b[0-9a-f]{40}\b")
_UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
)
# Any absolute path under a temp root, longest-match first so a nested spec dir
# does not leave a dangling prefix behind.
_TMPPATH_RE = re.compile(r"(?:/private)?/(?:tmp|var)/[^\s'\"]*")


def _indexed_sub(pattern: re.Pattern[str], label: str, text: str) -> str:
    """Replace each DISTINCT match with `<label_N>`, numbered by first appearance.

    Deliberately not a flat token. A run-id mismatch reads
    `stored='<a>', expected='<b>'`, and collapsing both to one token would make it
    byte-identical to a message where they matched — so the golden would stop
    proving the two differ. Indexing keeps the distinction while staying stable,
    because the numbering is derived from the string itself.
    """
    seen: dict[str, str] = {}

    def repl(m: re.Match[str]) -> str:
        value = m.group(0)
        if value not in seen:
            seen[value] = f"<{label}_{len(seen) + 1}>"
        return seen[value]

    return pattern.sub(repl, text)


def normalize(text: str, *, spec_dir: Path | None = None) -> str:
    """Canonical normalization applied identically at capture and compare time.

    Order matters: the explicit `spec_dir` substitution runs first so the generic
    temp-path pattern cannot swallow it and produce `<TMP>` where `<SPEC_DIR>`
    belongs. SHA-256 before SHA-1 so a 64-hex run is never split into a 40-hex
    prefix plus tail.

    Idempotent by construction — every emitted token contains `<`, `>` and `_`,
    which none of the patterns match — and `test_golden_fixtures.py` asserts it,
    because a non-idempotent normalizer would mask a real difference on the second
    pass.
    """
    if spec_dir is not None:
        # Longest form first: a resolved path may contain the unresolved one.
        for form in sorted({str(spec_dir), str(Path(spec_dir).resolve())}, key=len, reverse=True):
            text = text.replace(form, "<SPEC_DIR>")
    text = _indexed_sub(_SHA256_RE, "SHA256", text)
    text = _indexed_sub(_SHA1_RE, "SHA1", text)
    text = _indexed_sub(_UUID_RE, "RUN_ID", text)
    text = _TMPPATH_RE.sub("<TMP>", text)
    return text.strip()


def corpus_entries() -> list[Path]:
    """Every corpus artifact, sorted, with `spec.md`/`plan.md` names preserved."""
    if not CORPUS.is_dir():
        return []
    return sorted(
        p for p in CORPUS.glob("*/*.md") if p.name in ("spec.md", "plan.md")
    )


def corpus_key(path: Path) -> str:
    """Fixture-relative key: `<NNN>-<slug>/<spec|plan>.md`, never a live path."""
    return f"{path.parent.name}/{path.name}"
