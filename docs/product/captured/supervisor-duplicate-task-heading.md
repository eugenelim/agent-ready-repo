# Supervisor duplicate task heading

- **Status:** Open
- **Kind:** defect
- **Detail:** packs/core/.apm/skills/work-loop/scripts/_supervisor_projector.py

## Summary

Refuse or disambiguate a duplicate plan task heading: project_plan keys task identity by task ID, so when two sections share an ID both tasks get the later section's identity and a dependent task lists it twice; nothing refuses the plan
