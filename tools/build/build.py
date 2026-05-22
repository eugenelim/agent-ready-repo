#!/usr/bin/env python3
"""Thin shim — call `python -m agentbundle.build` instead of importing logic here."""
from agentbundle.build import main
raise SystemExit(main())
