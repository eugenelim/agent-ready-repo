"""Atomic worktree claims with separate decision and lifetime ownership locks.

Advisory claim locks are reliable only on local filesystems. Do not use their
liveness observation over a network filesystem with different lock semantics.

The run-slot default is memory-bound, not core-bound. Measured pytest processes
used 47--128 MB resident memory while a unit suite spent 178.9 seconds wall time
for 56.4 seconds CPU time (32%), so runs mostly wait and CPU count is the wrong
denominator. This host exhausted swap (26 of 27.6 GB) at load 135; a core-derived
default of five was that failing state. Two concurrent runs bounds memory pressure.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import hashlib
import importlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence

if __package__:
    from . import managed_child
    from .worktree_hygiene import Candidate, _path_component_reason, lease_refusal_lines
else:
    import managed_child
    from worktree_hygiene import Candidate, _path_component_reason, lease_refusal_lines


LEASE_DIRECTORY = "agent-ready-repo-worktree-leases"
LEASE_DIRECTORY_MODE = 0o700
LEASE_RETRY_LIMIT = 20
LEASE_RETRY_DELAY_SECONDS = 0.05
DEFAULT_MAX_CONCURRENT_RUNS = 2
# Downward-only memory clamp. Calibrated to the single measurement point
# available: this reference host has 32 GiB and is judged safe at 2 concurrent
# heavy runs, so 12 GiB per run leaves usable-memory headroom. Below that a machine gets
# fewer, never more.
MEMORY_PER_CONCURRENT_RUN_BYTES = 12 * 1024**3
# Age backstop for the ADMISSION roles only. An undeterminable probe counts as
# live, which for `activity`/`exclusive` is the right conservative answer -- but a
# run slot or waiter ticket that can never be reclaimed wedges every gate in every
# worktree, and no legitimate waiter outlives its own wait budget. The worktree
# claim roles keep the not-live-only policy, which is what stops a long run from
# having its own claim pruned mid-flight.
RUN_CLAIM_MAX_AGE_SECONDS = 6 * 60 * 60
DEFAULT_RUN_SLOT_WAIT_SECONDS = 5400
MINIMUM_RUN_SLOT_DECISION_LOCK_SECONDS = 30
MAX_CONCURRENT_RUNS_ENV = "WORKTREE_HYGIENE_MAX_CONCURRENT_RUNS"
RUN_SLOT_WAIT_SECONDS_ENV = "WORKTREE_HYGIENE_RUN_SLOT_WAIT_SECONDS"
RUN_SLOT_NESTING_MARKER_ENV = "WORKTREE_HYGIENE_RUN_SLOT_CLAIM"


class CoordinationLeaseError(RuntimeError):
    """Base error for cooperative claim operations."""


class ClaimStoreUnavailable(CoordinationLeaseError):
    """The store cannot safely support a coordination decision."""


class CoordinationLockContention(ClaimStoreUnavailable):
    """The coordination lock stayed held by a live peer for the whole budget.

    A subclass of `ClaimStoreUnavailable` so that every caller which already
    tolerates an unusable store -- notably claim release, which may only warn --
    keeps its behaviour unchanged. The wrapper, however, must distinguish the two:
    a lock held by a live peer is genuine contention, and treating it as an unusable
    store made the limiter switch itself off under exactly the load it exists for.
    Order matters at the catch sites: this clause must precede its base class.
    """


class ClaimContentionError(CoordinationLeaseError):
    """A peer's claim lock is live or could not be inspected."""

    def __init__(self, message: str, *, claims: tuple[ClaimRecord, ...] = ()) -> None:
        super().__init__(message)
        self.claims = claims


class RunSlotConfigurationError(CoordinationLeaseError):
    """A run-slot environment budget is malformed or outside its valid range."""


class RunSlotAdmissionRefused(CoordinationLeaseError):
    """No run slot became available before the caller's configured wait budget."""

    def __init__(self, holder_pids: tuple[int, ...]) -> None:
        self.holder_pids = holder_pids
        named_holders = ", ".join(str(pid) for pid in holder_pids) or "unknown"
        super().__init__(
            "run slot admission refused after wait budget; holding process ids: "
            f"{named_holders}"
        )


class Liveness(Enum):
    """The result of observing a claim's lifetime ownership lock."""

    LIVE = "live"
    NOT_LIVE = "not-live"
    UNDETERMINABLE = "undeterminable"


class ReclaimPolicy(Enum):
    """Named policy seam also used by the shipped port lease in layer 3."""

    PORT_LEASE = "not-live-or-aged"
    WORKTREE_CLAIM = "not-live-only"


class ClaimRole(Enum):
    """The cooperative worktree claim roles."""

    ACTIVITY = "activity"
    EXCLUSIVE = "exclusive"
    RUN_SLOT = "run-slot"
    RUN_TICKET = "run-ticket"


@dataclass(frozen=True)
class ClaimRecord:
    """A claim's untrusted payload and authoritative lock observation."""

    role: ClaimRole
    path: Path
    token: str | None
    pid: int | None
    worktree: Path | None
    created_at: float
    liveness: Liveness


@dataclass(frozen=True)
class WorktreeClaims:
    """Claims present for one worktree, for reporting without mutation."""

    activity: tuple[ClaimRecord, ...]
    exclusive: ClaimRecord | None


@dataclass
class WorktreeClaim:
    """A caller-owned claim whose descriptor holds its ownership lock for life."""

    role: ClaimRole
    path: Path
    token: str
    lease_dir: Path
    descriptor: int | None

    def release(self) -> None:
        """Remove only this token's claim, then release its lifetime lock."""
        try:
            with coordination_lock(self.lease_dir, "coordination.lock"):
                record = _read_record(self.path, self.role, None)
                if record.token == self.token:
                    with contextlib.suppress(FileNotFoundError):
                        self.path.unlink()
        finally:
            if self.descriptor is not None:
                _unlock_and_close(self.descriptor)
                self.descriptor = None


@dataclass
class RunSlotClaim:
    """An admitted run slot, or a live parent slot inherited by a nested run."""

    path: Path | None
    token: str
    lease_dir: Path
    descriptor: int | None
    pid: int | None
    nested: bool = False

    @property
    def nesting_marker(self) -> str:
        """Return the marker that lets a direct child identify this live slot."""
        return self.token

    @property
    def inherited_pid(self) -> int | None:
        """Name the parent holder only for a nested receipt's visible report."""
        return self.pid if self.nested else None

    def release(self) -> None:
        """Release an owned slot; a nested receipt never releases its parent's slot."""
        if self.nested:
            return
        try:
            if self.path is None:
                return
            with coordination_lock(self.lease_dir, "coordination.lock"):
                record = _read_record(self.path, ClaimRole.RUN_SLOT, None)
                if record.token == self.token:
                    with contextlib.suppress(FileNotFoundError):
                        self.path.unlink()
        finally:
            if self.descriptor is not None:
                _unlock_and_close(self.descriptor)
                self.descriptor = None


def _is_junction(path: Path) -> bool:
    """Return the optional Windows junction predicate."""
    check = getattr(path, "is_junction", None)
    return bool(callable(check) and check())


def _confined_existing(path: Path, root: Path) -> bool:
    """Reuse hygiene's component walk for an existing path under ``root``."""
    try:
        path.relative_to(root)
        candidate = Candidate(path=path, category="lease", bytes=0, is_dir=path.is_dir())
        return path.resolve().is_relative_to(root.resolve()) and not _path_component_reason(
            candidate, root, os.path.ismount
        )
    except (OSError, ValueError):
        return False


def _confined_new(path: Path, root: Path) -> bool:
    """Check a new composed child by validating its existing parent, not itself."""
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return path.parent == root and _confined_existing(root, root)


def _safe_lease_directory(path: Path) -> bool:
    """Return whether ``path`` is an existing real directory, not a link."""
    try:
        mode = path.lstat().st_mode
    except OSError:
        return False
    return stat.S_ISDIR(mode) and not stat.S_ISLNK(mode) and not _is_junction(path)


def prepare_lease_directory(common_dir: Path) -> Path:
    """Create a ``0700`` store, rejecting linked or escaping directory paths."""
    try:
        common = common_dir.resolve(strict=True)
        if common_dir.is_symlink() or _is_junction(common_dir):
            raise ClaimStoreUnavailable("Git common directory is a link or junction")
        lease_dir = common / LEASE_DIRECTORY
        if lease_dir.exists() and (lease_dir.is_symlink() or _is_junction(lease_dir)):
            raise ClaimStoreUnavailable("lease directory is a link or junction")
        lease_dir.mkdir(mode=LEASE_DIRECTORY_MODE, parents=True, exist_ok=True)
        if not _confined_existing(lease_dir, common):
            raise ClaimStoreUnavailable("lease directory escapes Git common directory")
        mode = lease_dir.lstat().st_mode
        if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode) or _is_junction(lease_dir):
            raise ClaimStoreUnavailable("lease directory is not a safe directory")
        return lease_dir
    except ClaimStoreUnavailable:
        raise
    except OSError as error:
        raise ClaimStoreUnavailable("claim store cannot be prepared") from error


def read_lease_directory(common_dir: Path) -> Path | None:
    """Return an existing safe store without creating one for a status read."""
    try:
        common = common_dir.resolve(strict=True)
        if common_dir.is_symlink() or _is_junction(common_dir):
            raise ClaimStoreUnavailable("Git common directory is a link or junction")
        lease_dir = common / LEASE_DIRECTORY
        if not lease_dir.exists():
            return None
        if lease_dir.is_symlink() or _is_junction(lease_dir):
            raise ClaimStoreUnavailable("lease directory is a link or junction")
        if not _confined_existing(lease_dir, common):
            raise ClaimStoreUnavailable("lease directory escapes Git common directory")
        mode = lease_dir.lstat().st_mode
        if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode) or _is_junction(lease_dir):
            raise ClaimStoreUnavailable("lease directory is not a safe directory")
        return lease_dir
    except ClaimStoreUnavailable:
        raise
    except OSError as error:
        raise ClaimStoreUnavailable("claim store cannot be read") from error


def _lock_functions(descriptor: int) -> tuple[Any, Any]:
    """Return non-blocking exclusive acquire/release functions for one descriptor."""
    if os.name == "nt":
        module: Any = importlib.import_module("msvcrt")
        return (
            lambda: module.locking(descriptor, module.LK_NBLCK, 1),
            lambda: module.locking(descriptor, module.LK_UNLCK, 1),
        )
    module = importlib.import_module("fcntl")
    return (
        lambda: module.flock(descriptor, module.LOCK_EX | module.LOCK_NB),
        lambda: module.flock(descriptor, module.LOCK_UN),
    )


def _unlock_and_close(descriptor: int) -> None:
    """Best-effort end of a claim lock's lifetime."""
    with contextlib.suppress(OSError):
        os.lseek(descriptor, 0, os.SEEK_SET)
        _lock_functions(descriptor)[1]()
    with contextlib.suppress(OSError):
        os.close(descriptor)


def release_claim_lock(descriptor: int) -> None:
    """End a descriptor-backed ownership lock retained by a published candidate."""
    _unlock_and_close(descriptor)


@contextmanager
def coordination_lock(
    lease_dir: Path,
    name: str,
    *,
    acquisition_budget_seconds: float | None = None,
) -> Iterator[None]:
    """Hold the short-lived shared decision lock around read-and-publish."""
    if Path(name).name != name or not name.endswith(".lock"):
        raise ClaimStoreUnavailable("coordination lock name is not safe")
    root = lease_dir.resolve()
    if lease_dir.is_symlink() or _is_junction(lease_dir) or not _confined_existing(root, root):
        raise ClaimStoreUnavailable("coordination lock directory is unsafe")
    path = root / name
    if not _confined_new(path, root):
        raise ClaimStoreUnavailable("coordination lock path escapes lease directory")
    if acquisition_budget_seconds is not None and acquisition_budget_seconds < 0:
        raise ValueError("acquisition_budget_seconds must not be negative")
    deadline = (
        None
        if acquisition_budget_seconds is None
        else time.monotonic() + acquisition_budget_seconds
    )
    try:
        with path.open("a+b") as handle:
            acquire, release = _lock_functions(handle.fileno())
            while True:
                try:
                    handle.seek(0)
                    acquire()
                    break
                except OSError as error:
                    if deadline is None:
                        if LEASE_RETRY_LIMIT <= 1:
                            raise CoordinationLockContention(
                                "could not acquire coordination lock"
                            ) from error
                        # Existing non-admission callers retain their bounded retry
                        # behaviour; admissions pass their scaled time budget below.
                        deadline = time.monotonic() + (
                            LEASE_RETRY_LIMIT - 1
                        ) * LEASE_RETRY_DELAY_SECONDS
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise CoordinationLockContention(
                            "could not acquire coordination lock"
                        ) from error
                    time.sleep(min(LEASE_RETRY_DELAY_SECONDS, remaining))
            try:
                yield
            finally:
                with contextlib.suppress(OSError):
                    handle.seek(0)
                    release()
    except ClaimStoreUnavailable:
        raise
    except OSError as error:
        raise ClaimStoreUnavailable("claim store cannot lock") from error


def publish_claim_candidate(lease_dir: Path, path: Path, payload: str) -> int:
    """Publish a claim atomically while retaining its long-lived ownership lock."""
    if not _safe_lease_directory(lease_dir) or not _confined_new(path, lease_dir):
        raise ClaimStoreUnavailable("claim path escapes lease directory")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".claim-", dir=lease_dir)
    temporary = Path(temporary_name)
    try:
        os.write(descriptor, payload.encode("utf-8"))
        os.lseek(descriptor, 0, os.SEEK_SET)
        _lock_functions(descriptor)[0]()
        os.link(temporary, path)
        return descriptor
    except FileExistsError:
        # A claim already exists at this path: contention, which callers resolve by
        # probing the incumbent. It must stay distinguishable from a store fault.
        _unlock_and_close(descriptor)
        raise
    except OSError as error:
        # A filesystem that cannot hard-link, a full disk, or a locking failure is an
        # unusable store, not a caller error. Raised raw it escaped every fail-open
        # handler and crashed the wrapper on a platform AC9 promises to run on.
        _unlock_and_close(descriptor)
        raise ClaimStoreUnavailable("claim store cannot publish a claim") from error
    except BaseException:
        _unlock_and_close(descriptor)
        raise
    finally:
        with contextlib.suppress(OSError):
            temporary.unlink()


def _probe_claim_lock(path: Path) -> Liveness:
    """Observe a claim lock without retaining a probe lock after the observation."""
    try:
        descriptor = os.open(path, os.O_RDWR)
    except OSError:
        return Liveness.UNDETERMINABLE
    try:
        acquire, release = _lock_functions(descriptor)
        try:
            os.lseek(descriptor, 0, os.SEEK_SET)
            acquire()
        except OSError as error:
            if getattr(error, "errno", None) in {
                errno.EACCES,
                errno.EAGAIN,
                errno.EWOULDBLOCK,
                errno.EDEADLK,
            }:
                return Liveness.LIVE
            return Liveness.UNDETERMINABLE
        try:
            os.lseek(descriptor, 0, os.SEEK_SET)
            release()
        except OSError:
            return Liveness.UNDETERMINABLE
        return Liveness.NOT_LIVE
    finally:
        with contextlib.suppress(OSError):
            os.close(descriptor)


def worktree_key(worktree: Path) -> str:
    """Return a SHA-256 filename key of resolved worktree path bytes."""
    return hashlib.sha256(os.fsencode(str(worktree.resolve()))).hexdigest()


def reclaimable(
    liveness: Liveness,
    age_seconds: float,
    policy: ReclaimPolicy,
    *,
    max_age_seconds: float = 24 * 60 * 60,
) -> bool:
    """Apply named reclaim policy; a live worktree lock is never aged out."""
    if policy is ReclaimPolicy.PORT_LEASE:
        return liveness is Liveness.NOT_LIVE or age_seconds > max_age_seconds
    return liveness is Liveness.NOT_LIVE


def pid_is_alive(pid: int) -> bool:
    """Return whether a process identity can still be observed as alive.

    Port leases deliberately retain this PID-based policy for their bounded
    aged-reclaim behaviour. Worktree claims instead use ``_probe_claim_lock``.
    """
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def lease_age_seconds(path: Path, payload: dict[str, object] | None) -> float:
    """Return payload age, falling back to the lease file modification time."""
    created_at = payload.get("created_at") if payload is not None else None
    try:
        if isinstance(created_at, (int, float, str)):
            created = float(created_at)
        else:
            created = path.stat().st_mtime
    except (OSError, TypeError, ValueError):
        return 0.0
    return max(0.0, time.time() - created)


def port_lease_reclaimable(path: Path, *, max_age_seconds: float) -> bool | None:
    """Apply the shipped PID-based, age-bounded port-lease reclaim policy."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        owner = int(payload["pid"])
    except (KeyError, OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError):
        return True if lease_age_seconds(path, None) > max_age_seconds else None
    liveness = Liveness.LIVE if pid_is_alive(owner) else Liveness.NOT_LIVE
    return reclaimable(
        liveness,
        lease_age_seconds(path, payload),
        ReclaimPolicy.PORT_LEASE,
        max_age_seconds=max_age_seconds,
    )


def _read_record(path: Path, role: ClaimRole, expected_worktree: Path | None) -> ClaimRecord:
    """Read untrusted metadata; the claim lock, not payload, establishes liveness.

    ``pid`` is retained only to name a holder in a refusal message. It is never
    used to infer liveness, so PID reuse cannot impersonate a claim holder.
    """
    now = time.time()
    observed = _probe_claim_lock(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        pid = int(raw["pid"])
        worktree = Path(str(raw["worktree"])).resolve()
        created_at = float(raw["created_at"])
        token = str(raw["token"])
        if pid <= 0 or pid > (1 << 31) - 1 or not token:
            raise ValueError("invalid identity")
        if expected_worktree is not None and worktree != expected_worktree:
            raise ValueError("worktree mismatch")
        # Clamp BOTH directions. Clamping only the future left a backdated
        # `created_at` unbounded, and the admission queue orders waiters by exactly
        # this field -- so a ticket claiming 0.0 was permanently the oldest waiter
        # and starved every real one, with zero slots occupied. The file's own
        # creation time is a floor a writer cannot forge downward.
        try:
            floor = path.stat().st_ctime
        except OSError:
            floor = now
        stamped = min(max(created_at, floor), now)
        return ClaimRecord(role, path, token, pid, worktree, stamped, observed)
    except (KeyError, OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError):
        return ClaimRecord(role, path, None, None, None, now, observed)


def _claim_paths(lease_dir: Path, worktree: Path, role: ClaimRole) -> tuple[Path, ...]:
    """Return each confined digest-keyed path for a worktree role."""
    key = worktree_key(worktree)
    if role is ClaimRole.ACTIVITY:
        pattern = f"{role.value}-{key}-*.lease"
    elif role is ClaimRole.EXCLUSIVE:
        pattern = f"{role.value}-{key}.lease"
    else:
        pattern = f"{role.value}-*.lease"
    try:
        paths = tuple(lease_dir.glob(pattern))
    except OSError as error:
        raise ClaimStoreUnavailable("claim store cannot list claims") from error
    if any(not _confined_existing(path, lease_dir) for path in paths):
        raise ClaimStoreUnavailable("claim path escapes lease directory")
    return paths


def _positive_whole_number(environ: Mapping[str, str], name: str, default: int) -> int:
    """Read a required-positive integer without accepting coercions or fallback."""
    raw = environ.get(name)
    if raw is None:
        return default
    if not raw.isascii() or not raw.isdecimal():
        raise RunSlotConfigurationError(
            f"{name} has invalid value {raw!r}; expected a whole number at least 1"
        )
    value = int(raw)
    if value < 1:
        raise RunSlotConfigurationError(
            f"{name} has invalid value {raw!r}; expected a whole number at least 1"
        )
    return value


def _physical_memory_bytes() -> int | None:
    """Return total physical memory, or ``None`` where it cannot be established.

    Pure stdlib and deliberately fail-open: a platform without ``sysconf``
    (Windows) yields ``None`` and therefore no clamp at all, because the lease
    must never be able to fail a CI job -- and `build-check-windows.yml` runs a
    wrapped target on a platform this cannot measure.
    """
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, OSError, ValueError):
        return None
    if pages <= 0 or page_size <= 0:
        return None
    return pages * page_size


def memory_clamped_run_limit(requested: int, memory_bytes: int | None) -> int:
    """Clamp a DEFAULT limit down to what physical memory supports, never up.

    Only ever reduces: the documented constant stays the ceiling, so no machine
    gains concurrency from derivation. Raising it remains a deliberate
    environment override, which is why this is applied to the default alone.

    Deriving from cores would have been wrong here and the numbers say so. A run
    is mostly WAITING -- a unit suite measured 178.9s wall against 56.4s CPU --
    so on this 10-core, 32 GiB host `cpu_count() // 2` gives 5, which is
    precisely the concurrency that exhausted swap at load 135, and `RAM / 2GiB`
    gives 16. The measured clamp uses 12 GiB per run so usable-memory reporting
    leaves the 32 GiB reference configuration at two runs.
    """
    if memory_bytes is None:
        return requested
    supported = memory_bytes // MEMORY_PER_CONCURRENT_RUN_BYTES
    return max(1, min(requested, supported))


def run_slot_budgets(environ: Mapping[str, str] | None = None) -> tuple[int, int]:
    """Return the strict environment-derived concurrent-run and wait budgets."""
    values = os.environ if environ is None else environ
    explicit = values.get(MAX_CONCURRENT_RUNS_ENV)
    limit = _positive_whole_number(values, MAX_CONCURRENT_RUNS_ENV, DEFAULT_MAX_CONCURRENT_RUNS)
    if explicit is None:
        # An explicit override is the operator's decision about their own hardware
        # and is left alone; clamping it would break the only way to raise the
        # limit deliberately.
        limit = memory_clamped_run_limit(limit, _physical_memory_bytes())
    return (
        limit,
        _positive_whole_number(
            values, RUN_SLOT_WAIT_SECONDS_ENV, DEFAULT_RUN_SLOT_WAIT_SECONDS
        ),
    )


def run_slot_decision_lock_budget(wait_seconds: int) -> float:
    """Return the admission decision-lock budget derived from its wait budget."""
    return max(MINIMUM_RUN_SLOT_DECISION_LOCK_SECONDS, wait_seconds / 20)


def _run_claim_path(lease_dir: Path, role: ClaimRole, token: str) -> Path:
    """Build one confined run-slot or run-ticket path from an opaque UUID token."""
    if role not in {ClaimRole.RUN_SLOT, ClaimRole.RUN_TICKET}:
        raise ValueError("run claim role is required")
    if len(token) != 32 or any(character not in "0123456789abcdef" for character in token):
        raise ClaimStoreUnavailable("run claim token is unsafe")
    path = lease_dir / f"{role.value}-{token}.lease"
    if not _confined_new(path, lease_dir):
        raise ClaimStoreUnavailable("run claim path escapes lease directory")
    return path


def _run_ticket_registration_path(lease_dir: Path, token: str) -> Path:
    """Return the persistent, lock-backed position record for one waiter.

    The removable ticket is the admission signal. This separate record preserves
    the filesystem-derived registration time if an operator removes that ticket,
    without trusting a caller-provided timestamp on re-registration.
    """
    if len(token) != 32 or any(character not in "0123456789abcdef" for character in token):
        raise ClaimStoreUnavailable("run claim token is unsafe")
    path = lease_dir / f"run-registration-{token}.lease"
    if not _confined_new(path, lease_dir):
        raise ClaimStoreUnavailable("run registration path escapes lease directory")
    return path


def _run_claim_payload(token: str, common_dir: Path) -> str:
    """Encode non-authoritative holder metadata for a slot or waiter ticket."""
    return json.dumps(
        {
            "pid": os.getpid(),
            "worktree": str(common_dir),
            "created_at": time.time(),
            "token": token,
        }
    )


def _ticket_position(
    lease_dir: Path, ticket: ClaimRecord, common_dir: Path
) -> float:
    """Return an unforgeable initial position for a current ticket.

    A registration record is retained only by its owning waiter's held lock and
    has a filesystem-derived timestamp. A manually written ticket has no valid
    registration record, so it receives its own file-derived timestamp instead.
    """
    if ticket.token is None:
        return ticket.created_at
    try:
        registration_path = _run_ticket_registration_path(lease_dir, ticket.token)
    except ClaimStoreUnavailable:
        return ticket.created_at
    if not registration_path.exists():
        return ticket.created_at
    registration = _read_record(registration_path, ClaimRole.RUN_TICKET, common_dir)
    if registration.token != ticket.token or registration.liveness is not Liveness.LIVE:
        return ticket.created_at
    return registration.created_at


def _live_run_claims(
    lease_dir: Path, role: ClaimRole, common_dir: Path
) -> tuple[ClaimRecord, ...]:
    """Prune dead or expired run records; retain live holders within the backstop.

    The configured slot cap is deliberately soft across an admission expiry. An
    expired owner may still be live, so reclaiming its record can over-admit by
    the number of expired slots. That bounded memory pressure is recoverable;
    leaving an unreclaimable slot would permanently wedge every gate.

    Unlike the worktree claim roles, an admission record is reclaimed once it
    passes ``RUN_CLAIM_MAX_AGE_SECONDS`` even when its owner is still live or its
    liveness is undeterminable.
    Without that, a single unreadable `run-slot-*.lease` occupies the limit forever
    and a single unreadable `run-ticket-*.lease` is permanently the oldest waiter --
    starving admission with zero slots occupied. Both are reachable with no
    attacker: an unmapped ``flock`` errno on a network-mounted common directory
    makes every probe undeterminable.
    """
    retained: list[ClaimRecord] = []
    now = time.time()
    for record in _prune_not_live(
        _claim_paths(lease_dir, common_dir, role), role, common_dir
    ):
        # An invalid or unreadable payload receives `now` from `_read_record` so
        # it cannot be ordered or identified. Its file timestamp is still an
        # observable, non-resetting age backstop; otherwise every scan makes an
        # undeterminable admission record look new and wedges the queue forever.
        record_age = (
            now - record.created_at
            if record.token is not None
            else lease_age_seconds(record.path, None)
        )
        if record_age > RUN_CLAIM_MAX_AGE_SECONDS:
            with contextlib.suppress(OSError):
                record.path.unlink()
            continue
        retained.append(record)
    return tuple(retained)


def _prune_run_registrations(lease_dir: Path, common_dir: Path) -> None:
    """Reclaim dead or aged waiter-position records without counting them as slots."""
    try:
        paths = tuple(lease_dir.glob("run-registration-*.lease"))
    except OSError as error:
        raise ClaimStoreUnavailable("claim store cannot list registrations") from error
    if any(not _confined_existing(path, lease_dir) for path in paths):
        raise ClaimStoreUnavailable("registration path escapes lease directory")
    now = time.time()
    for path in paths:
        record = _read_record(path, ClaimRole.RUN_TICKET, common_dir)
        # An observably-live registration is never aged out. Age reclaims records whose
        # owner died without releasing, and a held lock proves that did not happen; the
        # age clause therefore applies only when liveness is unproven. Unlinking a live
        # waiter's record erased its queue position, and its next publication took a
        # fresh timestamp that let younger waiters overtake it -- reachable whenever the
        # wait budget is overridden past the age budget.
        aged = now - record.created_at > RUN_CLAIM_MAX_AGE_SECONDS
        if record.liveness is Liveness.NOT_LIVE or (
            aged and record.liveness is not Liveness.LIVE
        ):
            with contextlib.suppress(OSError):
                path.unlink()


def _marker_slot(
    lease_dir: Path, common_dir: Path, marker: str | None
) -> ClaimRecord | None:
    """Return the live in-scope slot named by a nesting marker, if any."""
    if marker is None:
        return None
    try:
        path = _run_claim_path(lease_dir, ClaimRole.RUN_SLOT, marker)
    except ClaimStoreUnavailable:
        return None
    if not path.exists():
        return None
    record = _read_record(path, ClaimRole.RUN_SLOT, common_dir)
    if record.token == marker and record.liveness is Liveness.LIVE:
        return record
    return None


def _release_ticket(
    lease_dir: Path,
    token: str,
    descriptor: int | None,
    registration_descriptor: int,
    decision_lock_budget: float,
) -> None:
    """Remove a waiter ticket and its persistent position record on exit."""
    try:
        with coordination_lock(
            lease_dir,
            "coordination.lock",
            acquisition_budget_seconds=decision_lock_budget,
        ):
            path = _run_claim_path(lease_dir, ClaimRole.RUN_TICKET, token)
            record = _read_record(path, ClaimRole.RUN_TICKET, None)
            if record.token == token:
                with contextlib.suppress(FileNotFoundError):
                    path.unlink()
            registration_path = _run_ticket_registration_path(lease_dir, token)
            registration = _read_record(registration_path, ClaimRole.RUN_TICKET, None)
            if registration.token == token:
                with contextlib.suppress(FileNotFoundError):
                    registration_path.unlink()
    finally:
        if descriptor is not None:
            _unlock_and_close(descriptor)
        _unlock_and_close(registration_descriptor)


def acquire_run_slot(
    common_dir: Path,
    *,
    environ: Mapping[str, str] | None = None,
    on_wait: Callable[[tuple[int, ...]], None] | None = None,
) -> RunSlotClaim:
    """Fairly acquire one common-directory-wide run slot or raise on timeout.

    Ticket pruning, oldest-ticket selection, slot pruning, and slot publication
    happen under one decision lock. A ticket's persistent registration record
    retains its filesystem-derived original position if its removable ticket is
    released, so a recycled PID cannot impersonate it or move it backwards.
    """
    limit, wait_seconds = run_slot_budgets(environ)
    decision_lock_budget = run_slot_decision_lock_budget(wait_seconds)
    values = os.environ if environ is None else environ
    lease_dir = prepare_lease_directory(common_dir)
    scope = common_dir.resolve()
    with coordination_lock(
        lease_dir,
        "coordination.lock",
        acquisition_budget_seconds=decision_lock_budget,
    ):
        inherited = _marker_slot(lease_dir, scope, values.get(RUN_SLOT_NESTING_MARKER_ENV))
        if inherited is not None:
            return RunSlotClaim(
                None,
                inherited.token or "",
                lease_dir,
                None,
                inherited.pid,
                nested=True,
            )

    deadline = time.monotonic() + wait_seconds
    ticket_token: str | None = None
    ticket_descriptor: int | None = None
    registration_descriptor: int | None = None
    holders: tuple[int, ...] = ()
    next_heartbeat: float | None = None
    try:
        while True:
            with coordination_lock(
                lease_dir,
                "coordination.lock",
                acquisition_budget_seconds=decision_lock_budget,
            ):
                if ticket_token is None:
                    ticket_token = uuid.uuid4().hex
                    registration_path = _run_ticket_registration_path(lease_dir, ticket_token)
                    registration_descriptor = publish_claim_candidate(
                        lease_dir,
                        registration_path,
                        _run_claim_payload(ticket_token, scope),
                    )
                ticket_path = _run_claim_path(lease_dir, ClaimRole.RUN_TICKET, ticket_token)
                if not ticket_path.exists():
                    if ticket_descriptor is not None:
                        _unlock_and_close(ticket_descriptor)
                    ticket_descriptor = publish_claim_candidate(
                        lease_dir, ticket_path, _run_claim_payload(ticket_token, scope)
                    )

                _prune_run_registrations(lease_dir, scope)
                tickets = _live_run_claims(lease_dir, ClaimRole.RUN_TICKET, scope)
                slots = _live_run_claims(lease_dir, ClaimRole.RUN_SLOT, scope)
                oldest = min(
                    tickets,
                    key=lambda record: (
                        _ticket_position(lease_dir, record, scope),
                        record.token or "",
                    ),
                    default=None,
                )
                holders = tuple(sorted({record.pid for record in slots if record.pid is not None}))
                if oldest is not None and oldest.token == ticket_token and len(slots) < limit:
                    token = uuid.uuid4().hex
                    path = _run_claim_path(lease_dir, ClaimRole.RUN_SLOT, token)
                    descriptor = publish_claim_candidate(
                        lease_dir, path, _run_claim_payload(token, scope)
                    )
                    ticket_path = _run_claim_path(
                        lease_dir, ClaimRole.RUN_TICKET, ticket_token
                    )
                    with contextlib.suppress(FileNotFoundError):
                        ticket_path.unlink()
                    _unlock_and_close(ticket_descriptor)
                    ticket_descriptor = None
                    registration_path = _run_ticket_registration_path(lease_dir, ticket_token)
                    with contextlib.suppress(FileNotFoundError):
                        registration_path.unlink()
                    _unlock_and_close(registration_descriptor)
                    registration_descriptor = None
                    return RunSlotClaim(path, token, lease_dir, descriptor, os.getpid())
            now = time.monotonic()
            if on_wait is not None and (next_heartbeat is None or now >= next_heartbeat):
                on_wait(holders)
                next_heartbeat = now + 60
            if now >= deadline:
                raise RunSlotAdmissionRefused(holders)
            time.sleep(min(LEASE_RETRY_DELAY_SECONDS, max(0.0, deadline - now)))
    finally:
        if (
            ticket_token is not None
            and registration_descriptor is not None
        ):
            _release_ticket(
                lease_dir,
                ticket_token,
                ticket_descriptor,
                registration_descriptor,
                decision_lock_budget,
            )


def read_claims(common_dir: Path, worktree: Path, *, create: bool = True) -> WorktreeClaims:
    """Read claims for reporting; uninspectable locks conservatively count as live."""
    lease_dir = prepare_lease_directory(common_dir) if create else read_lease_directory(common_dir)
    if lease_dir is None:
        return WorktreeClaims((), None)
    resolved = worktree.resolve()
    activity_paths = _claim_paths(lease_dir, resolved, ClaimRole.ACTIVITY)
    activity = tuple(
        _read_record(path, ClaimRole.ACTIVITY, resolved) for path in activity_paths
    )
    paths = _claim_paths(lease_dir, resolved, ClaimRole.EXCLUSIVE)
    exclusive = _read_record(paths[0], ClaimRole.EXCLUSIVE, resolved) if paths else None
    return WorktreeClaims(activity, exclusive)


def read_run_slots(common_dir: Path) -> tuple[ClaimRecord, ...]:
    """Read run-slot occupancy without creating, pruning, or changing the store."""
    lease_dir = read_lease_directory(common_dir)
    if lease_dir is None:
        return ()
    scope = common_dir.resolve()
    return tuple(
        _read_record(path, ClaimRole.RUN_SLOT, scope)
        for path in _claim_paths(lease_dir, scope, ClaimRole.RUN_SLOT)
    )


def _prune_not_live(
    paths: tuple[Path, ...], role: ClaimRole, worktree: Path
) -> tuple[ClaimRecord, ...]:
    """Reclaim only paths whose long-lived ownership lock is definitely free."""
    retained: list[ClaimRecord] = []
    for path in paths:
        record = _read_record(path, role, worktree)
        if reclaimable(
            record.liveness,
            time.time() - record.created_at,
            ReclaimPolicy.WORKTREE_CLAIM,
        ):
            with contextlib.suppress(FileNotFoundError):
                path.unlink()
        else:
            retained.append(record)
    return tuple(retained)


def _acquire(
    common_dir: Path,
    worktree: Path,
    role: ClaimRole,
    wait_seconds: float | None,
) -> WorktreeClaim:
    """Atomically observe the other role then publish and lock this claim."""
    if wait_seconds is not None and wait_seconds < 0:
        raise ValueError("wait_seconds must not be negative")
    deadline = None if wait_seconds is None else time.monotonic() + wait_seconds
    lease_dir = prepare_lease_directory(common_dir)
    resolved = worktree.resolve()
    # Bounds the reclaim-then-retry path so a peer repeatedly re-creating the claim
    # cannot turn this into a hot loop holding the decision lock.
    reclaim_attempts = 0
    while True:
        with coordination_lock(lease_dir, "coordination.lock"):
            other = ClaimRole.EXCLUSIVE if role is ClaimRole.ACTIVITY else ClaimRole.ACTIVITY
            other_claims = _prune_not_live(
                _claim_paths(lease_dir, resolved, other), other, resolved
            )
            if not other_claims:
                token = uuid.uuid4().hex
                key = worktree_key(resolved)
                filename = (
                    f"{role.value}-{key}-{token}.lease"
                    if role is ClaimRole.ACTIVITY
                    else f"{role.value}-{key}.lease"
                )
                path = lease_dir / filename
                payload = json.dumps(
                    {
                        "pid": os.getpid(),
                        "worktree": str(resolved),
                        "created_at": time.time(),
                        "token": token,
                    }
                )
                try:
                    descriptor = publish_claim_candidate(lease_dir, path, payload)
                except FileExistsError as error:
                    # `_prune_not_live` returns the RETAINED (still-live) records, so a
                    # non-empty result means a live owner holds this role and we must
                    # refuse -- while an empty result means we just reclaimed a claim
                    # whose owner is gone, and the publish should be retried.
                    #
                    # This condition was inverted, and the inversion produced both of
                    # the failures that found it: a SIGKILLed holder's claim file
                    # raised contention instead of being reclaimed (the exact wedge
                    # this lock-based design exists to prevent), and a genuinely live
                    # holder fell through to `continue` and span forever instead of
                    # refusing.
                    if _prune_not_live((path,), role, resolved):
                        raise ClaimContentionError(
                            f"live {role.value} claim prevents acquisition"
                        ) from error
                    reclaim_attempts += 1
                    if reclaim_attempts >= LEASE_RETRY_LIMIT:
                        raise ClaimContentionError(
                            f"{role.value} claim for {resolved.name} could not be "
                            "published after repeated reclamation"
                        ) from error
                    continue
                return WorktreeClaim(role, path, token, lease_dir, descriptor)
            if role is ClaimRole.EXCLUSIVE or deadline is None or time.monotonic() >= deadline:
                raise ClaimContentionError(
                    f"live {other.value} claim prevents {role.value} claim",
                    claims=other_claims,
                )
        time.sleep(LEASE_RETRY_DELAY_SECONDS)


def acquire_activity(common_dir: Path, worktree: Path, *, wait_seconds: float) -> WorktreeClaim:
    """Wait only for an exclusive claim, then publish an activity claim."""
    return _acquire(common_dir, worktree, ClaimRole.ACTIVITY, wait_seconds)


def acquire_exclusive(common_dir: Path, worktree: Path) -> WorktreeClaim:
    """Immediately refuse if any activity claim's ownership lock is live."""
    return _acquire(common_dir, worktree, ClaimRole.EXCLUSIVE, None)


def git_common_dir(repository: Path) -> Path:
    """Resolve the Git common directory that scopes cooperative run slots."""
    try:
        result = subprocess.run(
            ("git", "rev-parse", "--git-common-dir"),
            cwd=repository,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise ClaimStoreUnavailable("git is required to locate the claim store") from error
    if result.returncode != 0:
        detail = result.stderr.strip() or "not inside a Git worktree"
        raise ClaimStoreUnavailable(f"could not resolve Git common directory: {detail}")
    path = Path(result.stdout.strip())
    return path.resolve() if path.is_absolute() else (repository / path).resolve()


def _holder_names(claims: Sequence[ClaimRecord]) -> str:
    """Render only process ids, worktree base names, and claim identifiers.

    A live claim whose payload was refused as untrusted has no pid to name, and
    "pid unknown" left the operator with nothing to act on while the release command
    correctly refused it as live. The claim's own identifier is named instead: it is a
    base name rather than a path, so it stays inside AC7's disclosure limit, and it is
    what an operating-system tool needs to find the process holding the lock.
    """
    names = []
    for claim in claims:
        worktree = claim.worktree.name if claim.worktree is not None else "unknown"
        if claim.pid is None:
            names.append(f"an unidentified holder of claim {claim.path.name}")
        else:
            names.append(f"pid {claim.pid} in {worktree}")
    return ", ".join(names) or "unknown holder"


def _queue_notice(holder_pids: tuple[int, ...]) -> None:
    """Expose admission queue progress at once and at least once a minute."""
    holders = ", ".join(str(pid) for pid in holder_pids) or "unknown"
    print(f"with-lease queued behind process ids: {holders}", file=sys.stderr, flush=True)


def with_lease(
    command: Sequence[str],
    *,
    repository: Path,
    environ: Mapping[str, str] | None = None,
) -> int:
    """Run one verbatim child while holding an activity claim and a run slot."""
    if not command:
        raise ValueError("with-lease requires a command after --")
    values = dict(os.environ if environ is None else environ)
    worktree = repository.resolve()
    # ONE call site, deliberately. An early `return managed_child.run_child(...)` on
    # the lease-unavailable path made two, and the structural check that exactly one
    # child runner is reachable cannot distinguish a second CALL from a second
    # IMPLEMENTATION -- so the guard fired and it was right to. Fall through instead.
    common: Path | None = None
    try:
        common = git_common_dir(repository)
    except ClaimStoreUnavailable as error:
        print(
            f"WARNING: worktree lease unavailable; running child unleased: {error}",
            file=sys.stderr,
            flush=True,
        )
    activity: WorktreeClaim | None = None
    slot: RunSlotClaim | None = None
    try:
        try:
            if common is not None:
                # The admission slot is taken first, and activity only once a slot is
                # held. Activity is what `clean --apply` refuses on, and the slot wait
                # is the long one: acquiring activity first made a merely queued run
                # block cleanup for the whole wait budget with no child in existence,
                # against AC7's "for exactly one child's lifetime". Cleanup takes no
                # slot, so this order introduces no cycle.
                slot = acquire_run_slot(common, environ=values, on_wait=_queue_notice)
                # The operator's wait budget governs both waits. Hardcoding the
                # default here meant a configured budget shortened the admission wait
                # and silently left a ninety-minute wait on a live exclusive claim.
                _limit, wait_seconds = run_slot_budgets(values)
                activity = acquire_activity(common, worktree, wait_seconds=wait_seconds)
        except RunSlotConfigurationError:
            raise
        except ClaimContentionError:
            raise
        except RunSlotAdmissionRefused:
            raise
        except CoordinationLockContention:
            # Must precede the base clause: a lock held by a live peer is contention,
            # and running unleased here is the limiter disabling itself under load.
            raise
        except ClaimStoreUnavailable as error:
            print(
                f"WARNING: worktree lease unavailable; running child unleased: {error}",
                file=sys.stderr,
                flush=True,
            )
        if slot is not None:
            values[RUN_SLOT_NESTING_MARKER_ENV] = slot.nesting_marker
            if slot.nested:
                # AC8's receipt: an inert limiter must be visible. The inherited pid is
                # named; the marker never is, because echoing it publishes a bypass.
                inherited = slot.inherited_pid
                holder = "an unidentified holder" if inherited is None else f"pid {inherited}"
                print(
                    "worktree lease: nested run — the concurrency limiter is inert "
                    f"here; this run inherited the slot held by {holder}",
                    file=sys.stderr,
                    flush=True,
                )
        return managed_child.run_child(tuple(command), values, worktree)
    finally:
        # Teardown cannot rewrite a real child outcome. A failed release is still
        # visible only as a warning, and a partially-acquired wrapper is unwound.
        # Released in reverse acquisition order.
        for claim in (activity, slot):
            if claim is None:
                continue
            try:
                claim.release()
            except (ClaimStoreUnavailable, OSError) as error:
                print(
                    f"WARNING: worktree lease release failed: {error}",
                    file=sys.stderr,
                    flush=True,
                )


def _releasable_claim_path(lease_dir: Path, identifier: str) -> tuple[Path, ClaimRole]:
    """Resolve a status-emitted worktree-claim identifier without path traversal."""
    name = Path(identifier).name
    if name != identifier or not name.endswith(".lease"):
        raise ValueError("claim identifier must be a lease filename emitted by lease-status")
    if name.startswith("activity-"):
        role = ClaimRole.ACTIVITY
    elif name.startswith("exclusive-"):
        role = ClaimRole.EXCLUSIVE
    else:
        raise ValueError("only worktree activity or exclusive claims are releasable")
    path = lease_dir / name
    if not _confined_new(path, lease_dir):
        raise ClaimStoreUnavailable("claim identifier escapes lease directory")
    return path, role


def release_claim(common_dir: Path, identifier: str) -> None:
    """Release a free or uninspectable worktree claim; never a live lock holder."""
    lease_dir = read_lease_directory(common_dir)
    if lease_dir is None:
        raise FileNotFoundError(identifier)
    path, _role = _releasable_claim_path(lease_dir, identifier)
    with coordination_lock(lease_dir, "coordination.lock"):
        if not path.exists():
            raise FileNotFoundError(identifier)
        record = _read_record(path, _role, None)
        if record.liveness is Liveness.LIVE:
            raise ClaimContentionError("claim lock is observably held", claims=(record,))
        path.unlink()


def _status_lines(common_dir: Path, worktree: Path) -> list[str]:
    """Report only existing claim state, without creating or pruning any records."""
    claims = read_claims(common_dir, worktree, create=False)
    slots = read_run_slots(common_dir)
    records = (*claims.activity, *((claims.exclusive,) if claims.exclusive else ()))
    lines = ["lease-status: claims"]
    if not records:
        lines.append("  none")
    for record in records:
        identifier = record.path.name
        pid = record.pid if record.pid is not None else "unknown"
        worktree_name = record.worktree.name if record.worktree is not None else "unknown"
        lines.append(
            f"  {identifier}: {record.role.value}, {record.liveness.value}, "
            f"pid {pid} in {worktree_name}; release-claim --apply --claim {identifier}"
        )
    lines.append(f"lease-status: run-slot occupancy {len(slots)}")
    for record in slots:
        pid = record.pid if record.pid is not None else "unknown"
        lines.append(f"  pid {pid}: {record.liveness.value}")
    return lines


def _parser() -> argparse.ArgumentParser:
    """Build the command-line surface for cooperative lease participants."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    wrapped = subparsers.add_parser("with-lease", help="run one command under a lease")
    wrapped.add_argument("child", nargs=argparse.REMAINDER)
    subparsers.add_parser("lease-status", help="report claims without mutation")
    release = subparsers.add_parser("release-claim", help="recover one unsafe claim")
    release.add_argument("--apply", action="store_true", help="perform the recovery")
    release.add_argument("--claim", required=True, help="identifier printed by lease-status")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run a lease participant command and preserve the reserved refusal shape."""
    args = _parser().parse_args(argv)
    repository = Path.cwd().resolve()
    try:
        if args.command == "with-lease":
            child = args.child[1:] if args.child[:1] == ["--"] else args.child
            if not child:
                print(
                    "\n".join(
                        lease_refusal_lines("with-lease", "no command was supplied after --")
                    ),
                    file=sys.stderr,
                )
                return 75
            return with_lease(child, repository=repository)
        common = git_common_dir(repository)
        if args.command == "lease-status":
            print("\n".join(_status_lines(common, repository)))
            return 0
        if not args.apply:
            print(
                "\n".join(
                    lease_refusal_lines("release-claim", "--apply was not supplied")
                ),
                file=sys.stderr,
            )
            return 75
        release_claim(common, args.claim)
        print(
            f"release-claim: released {args.claim}; this is an override of a claim "
            "that may be live"
        )
        return 0
    except RunSlotConfigurationError as error:
        print("\n".join(lease_refusal_lines("with-lease", str(error))), file=sys.stderr)
        return 75
    except (ClaimContentionError, RunSlotAdmissionRefused) as error:
        detail = str(error)
        if isinstance(error, ClaimContentionError) and error.claims:
            detail = f"{detail}; held by {_holder_names(error.claims)}"
        print("\n".join(lease_refusal_lines(args.command, detail)), file=sys.stderr)
        return 75
    except ClaimStoreUnavailable as error:
        if args.command == "with-lease":
            # Common-directory discovery itself cannot be bypassed safely enough to
            # spawn in an unknown scope; acquisition failures inside with_lease warn.
            print("\n".join(lease_refusal_lines("with-lease", str(error))), file=sys.stderr)
            return 75
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (FileNotFoundError, ValueError) as error:
        print("\n".join(lease_refusal_lines(args.command, str(error))), file=sys.stderr)
        return 75
    except managed_child.ManagedChildError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
