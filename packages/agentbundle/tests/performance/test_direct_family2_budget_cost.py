"""AC36 cost-ceiling harness for the direct-source Family-2 budgets.

Measures admission cost with **every** Family-2 budget simultaneously at its
limit, using only the blessed confined helpers -- no direct-route product code
exists yet, and this harness deliberately does not anticipate it.

AC36 names the CI runner as the only reproducible reference, so this emits the
environment it observed at run time rather than trusting any recorded machine.
A developer-machine figure is indicative only.
"""

from __future__ import annotations

import hashlib
import os
import platform
import resource
import statistics
import sys
import time
import warnings
from pathlib import Path

from agentbundle.catalogue_tooling.file_safety import (
    list_confined_regular_files,
    read_confined_regular_file,
)

# E11/E16 measured-envelope budgets, all applied simultaneously.
MAX_ENTRIES = 2_500
MAX_FILES = 1_000
MAX_SKILLS = 500
MAX_DEPTH = 12
MAX_TOTAL_BYTES = 25 * 1024 * 1024

# AC36 ceiling.
CEILING_SECONDS = 5.0
CEILING_RSS_MIB = 256

RUNS = 5


def _build_worst_case(root: Path) -> Path:
    """A source sitting at every Family-2 limit at once."""
    skills = root / "skills"
    skills.mkdir()
    per_file = MAX_TOTAL_BYTES // MAX_FILES
    blob = os.urandom(per_file)

    for index in range(MAX_SKILLS):
        envelope = skills / f"s{index}"
        envelope.mkdir()
        (envelope / "SKILL.md").write_bytes(blob)

    # Drive one envelope to the depth limit, measured from the envelope.
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


def _measure(root: Path, skills: Path) -> tuple[float, int]:
    started = time.perf_counter()
    files = list_confined_regular_files(root, skills, max_entries=MAX_ENTRIES)
    digest = hashlib.sha256()
    for path in files:
        read = read_confined_regular_file(root, path, max_bytes=1024 * 1024)
        data = read[0] if isinstance(read, tuple) else read
        digest.update(data.encode() if isinstance(data, str) else data)
    elapsed = time.perf_counter() - started
    return elapsed, len(files)


def test_family2_budget_cost_stays_inside_the_ac36_ceiling(tmp_path: Path) -> None:
    skills = _build_worst_case(tmp_path)

    timings: list[float] = []
    collected = 0
    for _ in range(RUNS):
        elapsed, collected = _measure(tmp_path, skills)
        timings.append(elapsed)

    rss_mib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)
    if sys.platform.startswith("linux"):  # ru_maxrss is KiB on Linux, bytes on macOS
        rss_mib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

    median = statistics.median(timings)
    # AC36: emit the observed environment rather than pinning a machine.
    report = (
        "AC36 Family-2 budget cost"
        f" | env={platform.system()}/{platform.machine()}"
        f" cpus={os.cpu_count()} python={platform.python_version()}"
        f" | budgets entries={MAX_ENTRIES} files={MAX_FILES} skills={MAX_SKILLS}"
        f" depth={MAX_DEPTH} total={MAX_TOTAL_BYTES // (1024 * 1024)}MiB"
        f" | collected={collected}"
        f" | wall-clock median {median:.2f}s"
        f" range {min(timings):.2f}-{max(timings):.2f}s over {RUNS} runs"
        f" | peak RSS {rss_mib:.0f} MiB"
        f" | ceiling {CEILING_SECONDS}s / {CEILING_RSS_MIB} MiB"
    )
    # pytest captures stdout for a passing test, so the measurement is emitted as
    # a warning: AC36 requires the figure be readable from the CI run itself.
    warnings.warn(report, stacklevel=2)

    assert collected == MAX_FILES
    assert median <= CEILING_SECONDS, (
        f"AC36 ceiling exceeded: median {median:.2f}s > {CEILING_SECONDS}s "
        f"(range {min(timings):.2f}-{max(timings):.2f}s)"
    )
    assert rss_mib <= CEILING_RSS_MIB
