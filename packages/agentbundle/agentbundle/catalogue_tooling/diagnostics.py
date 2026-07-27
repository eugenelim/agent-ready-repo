"""Stable diagnostic codes for catalogue_tooling commands."""

from __future__ import annotations

import enum


class DiagnosticCode(str, enum.Enum):
    UNKNOWN = "UNKNOWN"

    # Lint codes — CAT-L001 through CAT-L027
    CAT_L001 = "CAT-L001"   # catalogue.toml present but invalid per config.py
    CAT_L002 = "CAT-L002"   # Required catalogue marker missing (packs dir or marketplace.json)
    CAT_L003 = "CAT-L003"   # Duplicate pack identity across packs dir
    CAT_L004 = "CAT-L004"   # Pack directory name differs from [pack].name in pack.toml
    CAT_L005 = "CAT-L005"   # pack.toml not parseable as TOML
    CAT_L006 = "CAT-L006"   # pack.toml fails pack.schema.json validation (WARN if schema absent)
    CAT_L007 = "CAT-L007"   # plugin.json not parseable as JSON
    CAT_L008 = "CAT-L008"   # plugin.json fails plugin schema validation
    CAT_L009 = "CAT-L009"   # pack.toml and plugin.json name or version mismatch
    CAT_L010 = "CAT-L010"   # Skill directory missing SKILL.md
    CAT_L011 = "CAT-L011"   # Skill frontmatter missing required key or invalid value
    CAT_L012 = "CAT-L012"   # Agent metadata file missing required frontmatter
    CAT_L013 = "CAT-L013"   # Command metadata structure invalid
    CAT_L014 = "CAT-L014"   # Hook or hook-wiring file structure invalid
    CAT_L015 = "CAT-L015"   # Profile schema invalid or references unknown primitive
    CAT_L016 = "CAT-L016"   # Source-relative path escapes pack root
    CAT_L017 = "CAT-L017"   # Case-insensitive path collision within pack
    CAT_L018 = "CAT-L018"   # Primitive name not unique within pack
    CAT_L019 = "CAT-L019"   # Declared adapter name not in adapter contract
    CAT_L020 = "CAT-L020"   # Allowed scope value not in permitted set
    CAT_L021 = "CAT-L021"   # Configured path escapes catalogue root
    CAT_L022 = "CAT-L022"   # Symlink in shippable pack content (WARN)
    CAT_L023 = "CAT-L023"   # Windows-poisonous path name
    CAT_L024 = "CAT-L024"   # Primitive name does not match required pattern
    CAT_L025 = "CAT-L025"   # Primitive name exceeds max length
    CAT_L026 = "CAT-L026"   # Primitive description exceeds max length
    CAT_L027 = "CAT-L027"   # Multiline metadata form not supported
    CAT_L028 = "CAT-L028"   # Install profile invariant violation (scope, deps, order)
    CAT_L029 = "CAT-L029"   # Catalogue seeds lint failure (blocklist, placeholder, patterns.jsonl)
    CAT_L030 = "CAT-L030"   # First-value contract violation (Level A/B fields, writes-to-repo, tutorial)
    CAT_L031 = "CAT-L031"   # Credentialed-skill convention violation (D1/D2/D2b/D3/broker-specific)
