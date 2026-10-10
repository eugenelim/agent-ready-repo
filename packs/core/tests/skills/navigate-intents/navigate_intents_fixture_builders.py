"""Fixture builders for navigate-intents tests.

Builds the non-committed test cases (AC-0042 confinement cases, AC-0009
unsafe_input and input_too_large) in a temporary directory at test time.

All cases are built by copying the mixed/ committed corpus into tmp_path, then
applying a transformation that creates the specific condition under test.
"""

from __future__ import annotations

import os
import pathlib
import shutil

# Path to the committed mixed/ corpus, resolved relative to this file.
_HERE = pathlib.Path(__file__).resolve().parent
_MIXED = _HERE / "fixtures" / "mixed"

# A minimal valid intent preamble used to create single-file corpora.
_MINIMAL_INTENT = """\
# Feature: Placeholder

- **Slug:** `placeholder`
- **Status:** Draft
- **Level:** feature
- **Owner:** placeholder-owner

## Outcome

Placeholder intent for fixture builders.
"""

# A minimal brief preamble.
_MINIMAL_BRIEF = """\
# Brief: Placeholder brief

- **Slug:** `placeholder-brief`
- **Received:** 2026-01-01
- **Owner:** placeholder-owner
- **Status:** Draft
- **Parent intent:** none

## Outcome

Placeholder brief for fixture builders.
"""


def _copy_mixed(dest: pathlib.Path) -> None:
    """Copy the committed mixed/ corpus into dest."""
    shutil.copytree(str(_MIXED), str(dest), dirs_exist_ok=True)


def _intents_dir(root: pathlib.Path) -> pathlib.Path:
    return root / "docs" / "product" / "intents"


def _briefs_dir(root: pathlib.Path) -> pathlib.Path:
    return root / "docs" / "product" / "briefs"


def _write_intent(root: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = _intents_dir(root) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# AC-0042 confinement cases
# ---------------------------------------------------------------------------


def build_symlinked_file_corpus(tmp_path: pathlib.Path) -> pathlib.Path:
    """Corpus with one symlinked intent file.

    A symlinked file directly under docs/product/intents/ must cause the
    derivation to fail with unsafe_input.
    """
    root = tmp_path / "symlinked_file"
    _copy_mixed(root)
    real = _intents_dir(root) / "CAP-0001-alpha-cap.md"
    link = _intents_dir(root) / "FEAT-0099-symlink.md"
    link.symlink_to(real)
    return root


def build_symlinked_dir_corpus(tmp_path: pathlib.Path) -> pathlib.Path:
    """Corpus where docs/product/intents/ is reached via a symlinked directory.

    A file under a symlinked directory must cause the derivation to fail with
    unsafe_input.
    """
    root = tmp_path / "symlinked_dir"
    real_intents = tmp_path / "_real_intents"
    real_intents.mkdir(parents=True)
    # Write a valid intent in the real dir.
    intent_file = real_intents / "CAP-0001-alpha-cap.md"
    intent_file.write_text(_MINIMAL_INTENT, encoding="utf-8")
    # Create the outer corpus structure.
    (root / "docs" / "product").mkdir(parents=True)
    (root / "docs" / "product" / "briefs").mkdir()
    (root / "docs" / "specs").mkdir()
    # Symlink the intents directory itself.
    (root / "docs" / "product" / "intents").symlink_to(real_intents)
    return root


def build_fifo_corpus(tmp_path: pathlib.Path) -> pathlib.Path:
    """Corpus with a FIFO (named pipe) among the intent files.

    A FIFO directly under docs/product/intents/ must cause the derivation to
    fail with unsafe_input.
    """
    root = tmp_path / "fifo"
    _copy_mixed(root)
    fifo_path = _intents_dir(root) / "FEAT-0099-fifo.md"
    os.mkfifo(str(fifo_path))
    return root


def build_hardlink_corpus(tmp_path: pathlib.Path) -> pathlib.Path:
    """Corpus with an intent file that has two hard links (nlink > 1).

    A file with more than one hard link must cause the derivation to fail with
    unsafe_input.
    """
    root = tmp_path / "hardlink"
    _copy_mixed(root)
    original = _intents_dir(root) / "CAP-0001-alpha-cap.md"
    # Create a second hard link to the same inode.
    second_link = tmp_path / "second_link_target.md"
    os.link(str(original), str(second_link))
    return root


def build_swap_corpus(tmp_path: pathlib.Path) -> pathlib.Path:
    """Corpus that simulates a file swap between stat and open (TOCTOU).

    This is the hardest case to test in a unit context. We approximate it by
    creating a regular corpus and a non-regular replacement (a FIFO) with the
    same name, then replacing the regular file with the FIFO after the corpus
    is set up. The test must call the derivation in a way that it reads the FIFO
    rather than the regular file, proving that the stat-then-open sequence is
    not vulnerable to a race.

    In practice T2's implementation must re-verify the file type after opening
    it; this fixture proves the corpus is structurally valid before the swap
    so the failure is attributable to the swap.

    Returns a dict with 'root' (the corpus root) and 'swap' (a callable that
    performs the swap). The test calls swap() before invoking the derivation.
    """
    root = tmp_path / "swap"
    _copy_mixed(root)
    target = _intents_dir(root) / "CAP-0001-alpha-cap.md"
    fifo_staging = tmp_path / "swap_staging_fifo.md"
    os.mkfifo(str(fifo_staging))

    def do_swap() -> None:
        """Replace the regular file with the FIFO atomically."""
        target.unlink()
        pathlib.Path(str(fifo_staging)).rename(str(target))

    return root, do_swap  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# AC-0009 integrity cases
# ---------------------------------------------------------------------------


def build_input_too_large_corpus(tmp_path: pathlib.Path) -> pathlib.Path:
    """Corpus with one intent file exceeding 1,000,000 bytes.

    Must cause the derivation to fail with input_too_large.
    """
    root = tmp_path / "input_too_large"
    _copy_mixed(root)
    large = _intents_dir(root) / "FEAT-0099-large.md"
    # Write a valid UTF-8 intent whose body pushes it over 1 MB.
    header = (
        "# Feature: Large\n\n"
        "- **Slug:** `large-intent`\n"
        "- **Status:** Draft\n"
        "- **Level:** feature\n\n"
        "## Outcome\n\n"
    )
    padding = "x" * (1_000_001 - len(header.encode("utf-8")))
    large.write_text(header + padding, encoding="utf-8")
    return root


def build_unsafe_input_corpus(tmp_path: pathlib.Path) -> pathlib.Path:
    """Corpus with a symlinked file, triggering unsafe_input before size checks.

    This reuses build_symlinked_file_corpus because a symlink causes unsafe_input
    which is checked before input_too_large in AC-0009's order.
    """
    return build_symlinked_file_corpus(tmp_path)


def build_unsafe_nested_spec_corpus(tmp_path: pathlib.Path) -> pathlib.Path:
    """Corpus with a symlink nested inside a spec directory.

    A symlink at docs/specs/<name>/notes/link.md is not an admitted spec.md
    file, so it must NOT cause unsafe_input for the whole derivation
    (AC-0009, AC-0042).  The derivation must succeed; the valid spec.md
    in the same directory is still admitted.
    """
    root = tmp_path / "unsafe_nested_spec"
    _copy_mixed(root)
    notes_dir = root / "docs" / "specs" / "bravo-spec" / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    # Create a symlink inside the spec subdirectory.
    real_target = notes_dir.parent / "spec.md"
    (notes_dir / "link.md").symlink_to(real_target)
    return root
