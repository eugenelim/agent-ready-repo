Use the queue design. It keeps each job in order and makes failed work safe to try again.

The plan adds one queue and one worker. It does not change the public API.

All 18 contract tests pass in 4 seconds. No next step is needed.
