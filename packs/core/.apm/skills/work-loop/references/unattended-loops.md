# Unattended (AFK) loops

Use the agent's native unattended facility; do not hand-roll a loop around the CLI.

Use only when **all** hold: completion criterion is fully mechanical (tests pass,
checklist ticked, benchmark hit); task slices into single-context-window items;
verification is reliable (flaky tests → slot machine); you've already run the
in-session loop at least once on something similar.

Wrong tool when "done" is fuzzy, task needs human judgment mid-flight, or touches a
sensitive surface (auth, secrets, data deletion). Set hard caps (iteration, spend)
before starting; review every commit after.
