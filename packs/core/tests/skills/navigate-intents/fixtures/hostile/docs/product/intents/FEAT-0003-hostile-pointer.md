# Feature: Hostile pointer

- **Slug:** `hostile-pointer`
- **Status:** javascript:alert(1)
- **Level:** feature‏
- **Owner:** <img src=x onerror=alert(1)>
- **Parent intent:** javascript:alert(1)
- **Depends on:** intent:hostile-child, ✕ dangling waits for retired_target

## Outcome

Intent whose parent pointer is a javascript: value (refused, unparseable).
