+++
schema = 1
id = "db7a2911-6acc-4c19-bc7a-32d2dfb6d6fd"
anchor = "core4019--2026-11-05-db7a29116acc4c19bc7a32d2dfb6d6fd"
date = 2026-11-05
[[packages]]
name = "core"
version = "4.0.19"
+++
## Highlights
- The work-loop supervisor can now run one task at a time through a pinned launcher when the policy opts in. `start` accepts `--launcher-sha256` and `--launcher`, copies the named launcher into the run store, and refuses a launcher that is a test fixture. A new blocking verb, `run-concurrent`, spawns that launcher, checks its containment attestation before it releases the worker, reads the one access line it sends at the end, ingests the attempt directory itself, and integrates by exact source.
- `next` names a task in a `run-concurrent` request only when every admission condition holds, and records one closed reason code in the journal and in `status` for each task it keeps on the floor. The shipped `concurrency` policy stays `sequential`, so no run changes.
- A dead `run-concurrent` invocation no longer leaves its launcher running: the next verb records a landed attempt or ends the launcher's process group and issues the task on the floor.
