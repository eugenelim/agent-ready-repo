# Supervisor common config residue

- **Status:** Open
- **Kind:** defect
- **Detail:** packs/core/.apm/skills/work-loop/scripts/_supervisor_attempt.py

## Summary

Stop a foreign write to the shared Git config from refusing an attempt: the attempt manifest treats `<common-dir>/config` as protected Git control state, so another session's `git branch` or branch-tracking write into a linked worktree's shared `.git/config` during an attempt refuses it with `attempt-residue: common:config`
