"""Shared helpers for this package's unit suite.

Not a fixture module in the usual sense -- `await_released_workers` is a
plain function, imported explicitly by the test modules that need it. It
lives here because `TestAcquisitionBound` (`test_config.py`) and the
`acquisition-timeout` arm of `test_every_refusal_escapes_a_hostile_path`
(`test_two_scope_config.py`) both release an abandonable worker through the
same `threading.Event` idiom and both need the same proof that the release
actually finished the worker, not just unblocked it.
"""

from __future__ import annotations

import threading
import time


def await_released_workers(
    before: set[threading.Thread], timeout: float = 5.0
) -> None:
    """Join every thread started since `before`, so a released worker has
    actually finished before the caller's test case ends.

    `release.set()` unblocks a substituted blocking call, but the daemon
    worker thread `_run_bounded` started keeps running until it returns --
    a case that ends right after `release.set()` can still have that worker
    alive inside `os.open`/`os.fstat`/`os.read`/`os.close`. Threads present
    before the call are excluded so this only waits on the worker(s) the
    calling case itself started, not on threads other tests or the
    interpreter already had running.
    """
    deadline = time.monotonic() + timeout
    for thread in threading.enumerate():
        if thread in before:
            continue
        thread.join(max(deadline - time.monotonic(), 0))
        assert not thread.is_alive(), (
            f"worker thread {thread.name!r} was still running after being "
            "released -- releasing a blocking call does not by itself "
            "establish that the worker it unblocked has finished"
        )
