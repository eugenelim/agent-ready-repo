# Update mode

Enter only after the user explicitly requests an update and the existing skill
root is unambiguous and confined.

1. Establish a behavioral baseline from the existing description, instructions,
   referenced resources, tests, and realistic activation examples.
2. Name requested changes separately from behavior that must be retained.
3. Check callers before moving, renaming, or removing any resource.
4. Make the smallest coherent change. Preserve unknown supported frontmatter
   and unrelated invocation policy.
5. Rerun the baseline plus focused evidence for the new behavior. Compare
   before and after; an unmeasured cleanup is not optimization.

On verification failure, preserve recoverable content and report the failed
contract. Never weaken the baseline merely to make an update pass.

