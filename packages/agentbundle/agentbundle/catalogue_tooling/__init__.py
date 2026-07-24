"""agentbundle.catalogue_tooling — portable catalogue engine.

This package provides the configuration schema, result types, and command
stubs for the agentbundle catalogue * and agentbundle lint packs CLI surface.

Wave 2-4 specs fill the command logic; this package establishes the stable
contract layer between all modules.
"""

from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

__all__ = ["CatalogueConfigError", "load_catalogue_config"]
