# Pre existing credbroker wheel build local

- **Status:** Open
- **Kind:** defect

`tests/roster/test_portable_catalogue_authentication_packaging.py` fails on some local machines: 1 failed and 6 errors, each "credbroker wheel build failed (exit 1): metadata-generation-failed". The same file fails identically on a clean `origin/main` worktree on the same machine, so the cause is the local build environment, not a change under test. Every other roster test passes there. Making the wheel build self-contained or skipping with a named reason when the build backend is unavailable would remove the local false failure.
