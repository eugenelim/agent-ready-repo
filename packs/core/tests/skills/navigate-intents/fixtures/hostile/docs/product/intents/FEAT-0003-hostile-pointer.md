# Feature: Hostile pointer

- **Slug:** `hostile-pointer`
- **Status:** javascript:alert(1)
- **Level:** feature‏
- **Owner:** placeholder-owner
- **Parent intent:** javascript:alert(1)
- **Depends on:** intent:hostile-child, ✕ dangling waits for retired_target

## Outcome

Intent whose parent pointer is a javascript: value (refused, unparseable).
