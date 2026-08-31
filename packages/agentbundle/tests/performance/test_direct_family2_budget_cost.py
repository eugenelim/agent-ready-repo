"""AC36: the Family-2 budgets' cost ceiling, measured at their limits.

The harness exercises the real admission entry point and imports the production
bound constants rather than restating them, so a bound change moves this
measurement instead of silently invalidating it.

History worth keeping: this harness was deleted once, after it reported 44.2s
against a 5s ceiling and the criterion was retired as unattainable. The
measurement was real but it was measuring a defect — two loops re-scanned every
path for every envelope, which is 500,000 exception-driven `relative_to` calls
at the limits. With both linearised the same shape measures under two seconds.
A cost measurement is a measurement of the implementation, not of the bound.
"""

from __future__ import annotations

import os
import platform
import statistics
import sys
import time
import tracemalloc
import warnings
from pathlib import Path

import pytest
from agentbundle.direct_source import (
    DIRECT_MAX_DEPTH,
    DIRECT_MAX_ENTRIES,
    DIRECT_MAX_FILES,
    DIRECT_MAX_SELECTED_SKILLS,
    DIRECT_MAX_TOTAL_BYTES,
    admit_direct_source,
)

# AC36's ceiling. Wall-clock and resident, at the mutually satisfiable limits.
CEILING_SECONDS = 5.0
CEILING_MIB = 256.0
RUNS = 5
# Above this, a wall-clock figure measures the machine rather than the code.
LOAD_PER_CORE_CEILING = 2.0


def _build_reference_source(root: Path) -> None:
    """The reference configuration AC36 defines.

    Depth is measured per envelope, so 500 envelopes cannot each reach depth 12
    inside the entry budget. AC36 therefore puts the depth limit on *one*
    envelope and keeps the rest shallow, and it is that allocation the ceiling
    is measured against — not a per-envelope maximum applied to every envelope.

    Filler is ASCII. An earlier version used `os.urandom`, which made `SKILL.md`
    invalid UTF-8, so the harness measured a refusal and reported it as an
    admission cost.
    """

    # Sized against the files that CARRY payload, not against every file. Half
    # the 1,000 are tiny `SKILL.md` envelopes, so dividing the budget by 1,000
    # left the reference configuration at 50.05% of the total-bytes bound while
    # AC36 asks for the budgets "at their limits". The harness asserted only the
    # file count, so nothing noticed.
    files_per_skill = DIRECT_MAX_FILES // DIRECT_MAX_SELECTED_SKILLS
    payload_files = DIRECT_MAX_FILES - DIRECT_MAX_SELECTED_SKILLS
    envelope_overhead = DIRECT_MAX_SELECTED_SKILLS * 32
    per_file = (DIRECT_MAX_TOTAL_BYTES - envelope_overhead) // payload_files
    payload = "x" * per_file

    for index in range(DIRECT_MAX_SELECTED_SKILLS):
        envelope = root / "skills" / f"s{index:04d}"
        (envelope / "scripts").mkdir(parents=True)
        (envelope / "SKILL.md").write_text(
            f"---\nname: s{index:04d}\n---\n# s{index:04d}\n", encoding="utf-8"
        )
        # s0000 gives up one shallow payload so the deep file below fits inside
        # the file budget rather than pushing the shape one over it.
        shallow = files_per_skill - 1 - (1 if index == 0 else 0)
        for which in range(shallow):
            (envelope / "scripts" / f"f{which}.txt").write_text(payload, encoding="utf-8")

    # One envelope carries the depth allocation, per AC36's reference
    # configuration: `skills/s0000/scripts/d0/.../deep.txt` is DIRECT_MAX_DEPTH
    # segments below its envelope.
    deep = root / "skills" / "s0000" / "scripts"
    for level in range(DIRECT_MAX_DEPTH - 2):
        deep = deep / f"d{level}"
    deep.mkdir(parents=True)
    (deep / "deep.txt").write_text(payload, encoding="utf-8")


def test_family2_budget_cost_stays_inside_the_ac36_ceiling(tmp_path: Path):
    root = tmp_path / "reference"
    _build_reference_source(root)

    durations: list[float] = []
    cpu_durations: list[float] = []
    peak_mib = 0.0
    classification = None
    for _ in range(RUNS):
        tracemalloc.start()
        cpu_started = time.process_time()
        started = time.monotonic()
        classification = admit_direct_source(root)
        durations.append(time.monotonic() - started)
        cpu_durations.append(time.process_time() - cpu_started)
        peak_mib = max(peak_mib, tracemalloc.get_traced_memory()[1] / (1024 * 1024))
        tracemalloc.stop()

    assert classification is not None
    median = statistics.median(durations)
    cpu_median = statistics.median(cpu_durations)
    load_per_core = os.getloadavg()[0] / (os.cpu_count() or 1)

    # Recorded on every run, pass or fail: a ceiling with no published
    # measurement cannot be re-checked by whoever inherits it.
    warnings.warn(
        f"AC36 Family-2 budget cost | env={platform.system()}/{platform.machine()} "
        f"python={sys.version.split()[0]} | budgets entries={DIRECT_MAX_ENTRIES} "
        f"files={DIRECT_MAX_FILES} skills={DIRECT_MAX_SELECTED_SKILLS} "
        f"total={DIRECT_MAX_TOTAL_BYTES} | collected={classification.files} "
        f"bytes={classification.total_bytes} | wall-clock median {median:.2f}s "
        f"range {min(durations):.2f}-{max(durations):.2f}s over {RUNS} runs | "
        f"cpu median {cpu_median:.2f}s | admission peak {peak_mib:.1f} MiB | "
        f"load/core {load_per_core:.1f} | ceiling {CEILING_SECONDS}s / {CEILING_MIB} MiB",
        UserWarning,
        stacklevel=2,
    )

    assert classification.files == DIRECT_MAX_FILES, (
        "the reference configuration must sit at the file budget, not below it"
    )
    # AC36 measures "with the mutually satisfiable Family-2 budgets at their
    # limits", so the byte budget has to be near its bound too — not just the
    # file count.
    assert classification.total_bytes >= DIRECT_MAX_TOTAL_BYTES * 0.95, (
        f"the reference configuration sits at "
        f"{classification.total_bytes / DIRECT_MAX_TOTAL_BYTES:.0%} of the "
        f"total-bytes budget; AC36 measures at the limits"
    )
    # CPU time is asserted unconditionally: it is the cost this code actually
    # incurs, and no amount of contention inflates it.
    assert cpu_median <= CEILING_SECONDS, (
        f"AC36 ceiling exceeded on CPU time: median {cpu_median:.2f}s > "
        f"{CEILING_SECONDS}s (range {min(cpu_durations):.2f}-{max(cpu_durations):.2f}s)"
    )

    # Wall-clock is AC36's stated measure, but it is only meaningful on an
    # uncontended machine. AC36 says the CI runner is the only reproducible
    # reference and a developer-machine figure is indicative only, so on a
    # loaded box the number is recorded and not asserted — the same shape
    # measured 5.34s at load 88 and 1.23s at load 4 on one machine, and
    # failing on a peer session's load would teach a reader to ignore this.
    # Memory belongs beside CPU, not behind the wall-clock gate: `tracemalloc`
    # peak is not load-sensitive. It previously sat AFTER the skip, so on a
    # loaded machine the 256 MiB half of the ceiling was never asserted — while
    # the skip text said it had been.
    assert peak_mib <= CEILING_MIB, (
        f"AC36 memory ceiling exceeded: {peak_mib:.1f} MiB > {CEILING_MIB} MiB"
    )

    if load_per_core > LOAD_PER_CORE_CEILING:
        pytest.skip(
            f"wall-clock not asserted: load/core {load_per_core:.1f} exceeds "
            f"{LOAD_PER_CORE_CEILING}. CPU ({cpu_median:.2f}s) and memory "
            f"({peak_mib:.1f} MiB) were asserted unconditionally."
        )
    assert median <= CEILING_SECONDS, (
        f"AC36 ceiling exceeded: median {median:.2f}s > {CEILING_SECONDS}s "
        f"(range {min(durations):.2f}-{max(durations):.2f}s)"
    )
