# `record-attempt` can time out under shared-machine load

This note is the canonical artifact for the open defect previously tracked as
`pre-existing-record-attempt-lock-contention-under-load` in `workspace.toml`.

## Observation

During the `stasis-stop-retirement` run,
`test_concurrent_record_attempt_no_lost_update` lost 2 of 8 concurrent
`record-attempt` calls to state-lock acquisition timeouts while the full
work-loop suite shared a loaded machine. The same test passed 9 of 9 isolated
runs. Neither the test nor the state-lock implementation was in that run's
diff.

The evidence does not yet distinguish a production timeout that is too short
from contention created by the test harness. Treating either explanation as
settled would hide the other failure mode.

## Completion contract

Reproduce the timeout under controlled load, establish whether the limit or the
harness is the cause, and repair that cause without weakening the no-lost-update
assertion. Keep isolated behavior green and record the loaded-run evidence used
to set any new bound.
