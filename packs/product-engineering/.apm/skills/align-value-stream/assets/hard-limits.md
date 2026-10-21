## Hard limits

- **No atomic cross-repo commit.** A change that spans repos lands as separate commits, so the team sequences them and tolerates a window where the repos disagree.
- **No shared release train.** Each component repo ships on its own schedule, so the team cannot assume two components release together.
- **The rollup is a snapshot, not a live feed.** It shows each component as of its last update, so the team checks the component's own repo when the date matters.
