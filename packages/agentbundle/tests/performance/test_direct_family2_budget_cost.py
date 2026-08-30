"""AC36 cost-ceiling harness for the direct-source Family-2 budgets.

Measures admission cost with the mutually satisfiable Family-2 budgets at their
limits, using only the blessed confined helpers. No direct-route product code
exists yet; T3 re-points this harness at the real admission entry point, and
imports the production bound constants once they exist rather than restating
them here.

Two measurement notes, both learned the hard way:

* `resource.getrusage(...).ru_maxrss` is a **process-lifetime high-water mark**,
  not a footprint. Reporting it made the same work look like 26 MiB bare, 52 MiB
  under pytest and 111 MiB on CI, and produced an inverted "memory is binding"
  conclusion. This measures the `tracemalloc` peak of the admission region only.
* The per-file byte budget cannot coexist with the total: 1,000 files x 1 MiB is
  1,000 MiB against a 25 MiB total. Per-file is dominated by total/files and is
  measured at that value, which is the real worst case.
"""

from __future__ import annotations

import hashlib
import os
import platform
import statistics
import time
import tracemalloc
import warnings
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.file_safety import (
    list_confined_regular_files,
    read_confined_regular_file,
)

# E11/E16 measured-envelope budgets. T3 replaces these with imports of the
# production constants so an approved raise cannot leave the ceiling verified
# against a superseded budget.
MAX_ENTRIES = 2_500
MAX_FILES = 1_000
MAX_SKILLS = 500
MAX_DEPTH = 12
MAX_TOTAL_BYTES = 25 * 1024 * 1024

CEILING_SECONDS = 5.0
CEILING_PEAK_MIB = 256

RUNS = 5


def _build_worst_case(root: Path) -> Path:
    """A source at every mutually satisfiable Family-2 limit at once."""
    skills = root / "skills"
    skills.mkdir()
    per_file = MAX_TOTAL_BYTES // MAX_FILES
    blob = os.urandom(per_file)

    for index in range(MAX_SKILLS):
        envelope = skills / f"s{index}"
        envelope.mkdir()
        (envelope / "SKILL.md").write_bytes(blob)

    # One envelope driven to the depth limit. MAX_DEPTH counts path components
    # below the envelope, of which `scripts/` and the file itself are two.
    deep = skills / "s0" / "scripts"
    for level in range(MAX_DEPTH - 2):
        deep = deep / f"l{level}"
    deep.mkdir(parents=True)
    for index in range(MAX_FILES - MAX_SKILLS):
        (deep / f"f{index}.md").write_bytes(blob)

    seen = MAX_SKILLS * 2 + (MAX_FILES - MAX_SKILLS) + (MAX_DEPTH - 1)
    for index in range(max(MAX_ENTRIES - seen, 0)):
        (skills / f"pad{index}").mkdir()
    return skills


def _assert_built_at_the_limits(root: Path, skills: Path) -> None:
    """An under-built tree would ship a silently weaker measurement."""
    entries = sum(1 for _ in skills.rglob("*"))
    files = list_confined_regular_files(root, skills, max_entries=MAX_ENTRIES)
    envelopes = [child for child in skills.iterdir() if (child / "SKILL.md").exists()]
    depth = max(
        len(path.relative_to(skills / path.relative_to(skills).parts[0]).parts)
        for path in files
    )
    total = sum(path.stat().st_size for path in files)

    assert entries == MAX_ENTRIES, f"entries {entries} != {MAX_ENTRIES}"
    assert len(files) == MAX_FILES, f"files {len(files)} != {MAX_FILES}"
    assert len(envelopes) == MAX_SKILLS, f"skills {len(envelopes)} != {MAX_SKILLS}"
    assert depth == MAX_DEPTH, f"depth-from-envelope {depth} != {MAX_DEPTH}"
    assert total > MAX_TOTAL_BYTES * 0.99, f"total bytes {total} under budget"


def _measure(root: Path, skills: Path, *, profile: bool) -> tuple[float, float, int]:
    """Return (seconds, peak MiB, files collected).

    `tracemalloc` roughly 6x's the wall-clock of this allocation-heavy loop, so
    timing and memory are measured in separate passes: an instrument must not
    contaminate the dimension it is not measuring. `peak` is 0.0 when profiling
    is off.
    """
    if profile:
        tracemalloc.start()
    started = time.perf_counter()
    files = list_confined_regular_files(root, skills, max_entries=MAX_ENTRIES)
    digest = hashlib.sha256()
    for path in files:
        # `include_mode=True` matches the direct route's contract (AC15), so the
        # per-file fstat cost sits inside the measurement.
        data, _mode = read_confined_regular_file(
            root, path, max_bytes=1024 * 1024, include_mode=True
        )
        digest.update(data)
    elapsed = time.perf_counter() - started
    peak_mib = 0.0
    if profile:
        peak_mib = tracemalloc.get_traced_memory()[1] / (1024 * 1024)
        tracemalloc.stop()
    return elapsed, peak_mib, len(files)


@pytest.mark.skipif(os.name != "posix", reason="POSIX-only measurement harness")
def test_family2_budget_cost_stays_inside_the_ac36_ceiling(tmp_path: Path) -> None:
    skills = _build_worst_case(tmp_path)
    _assert_built_at_the_limits(tmp_path, skills)

    timings: list[float] = []
    collected = 0
    for _ in range(RUNS):
        elapsed, _peak, collected = _measure(tmp_path, skills, profile=False)
        timings.append(elapsed)
    # One separate profiled pass: tracemalloc distorts timing, not allocation.
    _elapsed, peak, _collected = _measure(tmp_path, skills, profile=True)

    median = statistics.median(timings)
    report = (
        "AC36 Family-2 budget cost"
        f" | env={platform.system()}/{platform.machine()}"
        f" cpus={os.cpu_count()} python={platform.python_version()}"
        f" | budgets entries={MAX_ENTRIES} files={MAX_FILES} skills={MAX_SKILLS}"
        f" depth={MAX_DEPTH} total={MAX_TOTAL_BYTES // (1024 * 1024)}MiB"
        f" per-file={MAX_TOTAL_BYTES // MAX_FILES}B (total/files)"
        f" | collected={collected}"
        f" | wall-clock median {median:.2f}s"
        f" range {min(timings):.2f}-{max(timings):.2f}s over {RUNS} runs"
        f" | admission-region peak {peak:.1f} MiB"
        f" | ceiling {CEILING_SECONDS}s / {CEILING_PEAK_MIB} MiB"
    )
    # pytest captures stdout for a passing test; AC36 requires the figure be
    # readable from the CI run itself.
    warnings.warn(report, stacklevel=2)

    assert collected == MAX_FILES
    assert median <= CEILING_SECONDS, (
        f"AC36 ceiling exceeded: median {median:.2f}s > {CEILING_SECONDS}s "
        f"(range {min(timings):.2f}-{max(timings):.2f}s)"
    )
    assert peak <= CEILING_PEAK_MIB
