# Quality implementation review — round 3

## Finding

- **Blocker:** the HTML parser accepted `name` on every element as a fragment
  target. Browser fragment fallback only treats legacy `<a name="…">` as an
  anchor, so an unrelated form field could mask a broken fragment.

## Resolution

All element `id` attributes remain valid targets, while `name` is now accepted
only on `<a>`. A focused form-input fixture proves non-anchor names do not
satisfy fragments.

