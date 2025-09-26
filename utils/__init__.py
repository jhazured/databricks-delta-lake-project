"""
Databricks Delta Lake Project - Utility Modules

This package contains utility modules for the enterprise data platform.
"""

__version__ = "1.0.0"
__author__ = "Data Engineering Team"

# Common utilities
from .common.logging import setup_logging
from .common.config import load_config
from .common.validation import validate_schema, validate_data_quality
from .common.exceptions import DeltaLakeError, ValidationError, ConfigurationError

# Databricks utilities
from .databricks.connection import DatabricksConnection, get_databricks_connection

__all__ = [
    # Version info
    "__version__",
    "__author__",
    # Common utilities
    "setup_logging",
    "load_config", 
    "validate_schema",
    "validate_data_quality",
    "DeltaLakeError",
    "ValidationError",
    "ConfigurationError",
    # Databricks utilities
    "DatabricksConnection",
    "get_databricks_connection",
]
