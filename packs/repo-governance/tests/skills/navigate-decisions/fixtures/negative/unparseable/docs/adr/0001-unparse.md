# ADR-0001: Unparseable entries test

- **Status:** Accepted
- **Supersedes:** none
- **Supersedes in part:** ADR-0002 D3a; ADR-0003 D01
- **Superseded by:** none
- **Superseded in part:** none

## Context

The "Supersedes in part" field contains two unparseable entries separated by ";":
  - "ADR-0002 D3a": the D-ID "D3a" contains a non-digit character (a), making
    the entire entry unparseable.
  - "ADR-0003 D01": the D-ID "D01" has a leading zero (two digits starting with
    0), making the entire entry unparseable.

Each unparseable entry becomes its own unresolved relationship with target=null,
scope=[], and the entry text as raw_value. They are never merged, even if they
named the same target. Two unparseable entries in one field produce two distinct
unresolved relationship objects.

## Decision

- **D1:** Each unparseable entry is its own unresolved relationship.
