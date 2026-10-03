## Blockers

**1. `[reason]` Sustained reviewer text is promoted into repairer instructions outside the untrusted-data frame.** `.context/experiments/codex-headless-sol-loop-confirmation-r1/tools/t13_prompts.py:381-386`; `.context/experiments/codex-headless-sol-loop-confirmation-r1/tools/t13_waves.py:669-682`. A prior worker that controls a sustained finding can place instruction-shaped text in `repair_requirement`, and the controller copies it verbatim into a repair prompt as "part of your instructions", bypassing AC-0024 framing and giving model output instruction authority across agents. Fix: worker-authored finding fields must remain framed data or be transformed into controller-owned repair requirements under a fixed validation contract that excludes control text.

## Concerns

**2. `[reason]` AC-0024's crossover gate is a denylist but is reported as an authority proof.** `.context/experiments/codex-headless-sol-loop-confirmation-r1/tools/t13_frames.py:37-54`; `.context/experiments/codex-headless-sol-loop-confirmation-r1/tools/t13_frames.py:136-145`. A framed body can express prompt-injection or hidden-file-reading pressure without matching any listed pattern and still pass `verify_launch`, so the launch binding proves only digest integrity plus a partial text scan, not that framed text cannot alter tools, paths, hidden-material handling, or schema authority. Fix: do not treat the denylist as a security decision; the launch must enforce containment mechanically, and any text scan must be scoped as telemetry or fail closed only under a documented conservative rule.

**3. `[reason]` The T14 answer-key protection is still a prose precondition, not launch control.** `.context/codex-headless-sol-loop-confirmation-result.json:1931-1956`; `.context/experiments/codex-headless-sol-loop-confirmation-r1/tools/t13_runner.py:138-160`. A future provider worker launched with the current pattern receives read-only access rooted at the repository while the restricted answer-key files remain under that root unless a later human/controller step remembers and enforces the handoff precondition. Fix: before any T14 or T15 spawn, the launch path must mechanically prove the restricted files are outside the effective worker root or refuse before process start.

## Not checked

- Did not run SAST, SCA, secret scanning, or empty-catch lint; this was a read-only reasoning pass, and the target sits under ignored `.context` artifacts.
- Did not execute controller-authored Python, launch model processes, replay payloads, or test sandbox behavior dynamically.
- Did not inspect deployed enterprise policy, credentials, browser profiles, or denied protected paths.
