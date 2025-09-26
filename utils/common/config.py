"""
Configuration management utilities.
"""

import os
import yaml
import json
from typing import Any, Dict, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class Environment(Enum):
    """Environment types."""
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
    TRIAL = "trial"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: str = "require"
    connection_timeout: int = 30


@dataclass
class DatabricksConfig:
    """Databricks configuration."""
    host: str
    token: str
    cluster_id: Optional[str] = None
    workspace_id: Optional[str] = None
    catalog: str = "main"
    schema: str = "default"


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enabled: bool = True
    metrics_endpoint: str = "http://localhost:9090"
    logs_endpoint: str = "http://localhost:9200"
    alerting_enabled: bool = True
    retention_days: int = 30


@dataclass
class SecurityConfig:
    """Security configuration."""
    encryption_enabled: bool = True
    audit_logging: bool = True
    access_control: bool = True
    data_classification: bool = True


@dataclass
class AppConfig:
    """Main application configuration."""
    environment: Environment
    debug: bool = False
    log_level: str = "INFO"
    database: DatabaseConfig
    databricks: DatabricksConfig
    monitoring: MonitoringConfig
    security: SecurityConfig

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class ConfigManager:
    """Configuration manager for the application."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config: Optional[AppConfig] = None

    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        env = os.getenv("ENVIRONMENT", "dev")
        return f"config/environments/{env}.yaml"

    def load_config(self) -> AppConfig:
        """
        Load configuration from file and environment variables.

        Returns:
            Application configuration
        """
        if self._config is not None:
            return self._config

        # Load from file
        config_data = self._load_from_file()

        # Override with environment variables
        config_data = self._override_with_env(config_data)

        # Create configuration object
        self._config = self._create_config(config_data)

        return self._config

    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                return yaml.safe_load(f)
            elif self.config_path.endswith('.json'):
                return json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {self.config_path}")

    def _override_with_env(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration with environment variables."""
        env_mappings = {
            "DATABRICKS_HOST": ["databricks", "host"],
            "DATABRICKS_TOKEN": ["databricks", "token"],
            "DATABRICKS_CLUSTER_ID": ["databricks", "cluster_id"],
            "DATABASE_HOST": ["database", "host"],
            "DATABASE_PORT": ["database", "port"],
            "DATABASE_NAME": ["database", "database"],
            "DATABASE_USERNAME": ["database", "username"],
            "DATABASE_PASSWORD": ["database", "password"],
            "LOG_LEVEL": ["log_level"],
            "DEBUG": ["debug"],
        }

        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(config_data, config_path, env_value)

        return config_data

    def _set_nested_value(self, data: Dict[str, Any], path: list, value: Any) -> None:
        """Set nested dictionary value."""
        current = data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Convert string values to appropriate types
        if isinstance(value, str):
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)

        current[path[-1]] = value

    def _create_config(self, config_data: Dict[str, Any]) -> AppConfig:
        """Create configuration object from data."""
        # Set environment
        env_str = config_data.get("environment", "dev")
        environment = Environment(env_str)

        # Create database config
        db_data = config_data.get("database", {})
        database = DatabaseConfig(
            host=db_data.get("host", "localhost"),
            port=db_data.get("port", 5432),
            database=db_data.get("database", "delta_lake"),
            username=db_data.get("username", "user"),
            password=db_data.get("password", "password")
        )

        # Create Databricks config
        dbx_data = config_data.get("databricks", {})
        databricks = DatabricksConfig(
            host=dbx_data.get("host", ""),
            token=dbx_data.get("token", ""),
            cluster_id=dbx_data.get("cluster_id"),
            catalog=dbx_data.get("catalog", "main"),
            schema=dbx_data.get("schema", "default")
        )

        # Create monitoring config
        mon_data = config_data.get("monitoring", {})
        monitoring = MonitoringConfig(
            enabled=mon_data.get("enabled", True),
            metrics_endpoint=mon_data.get("metrics_endpoint", "http://localhost:9090"),
            logs_endpoint=mon_data.get("logs_endpoint", "http://localhost:9200"),
            alerting_enabled=mon_data.get("alerting_enabled", True),
            retention_days=mon_data.get("retention_days", 30)
        )

        # Create security config
        sec_data = config_data.get("security", {})
        security = SecurityConfig(
            encryption_enabled=sec_data.get("encryption_enabled", True),
            audit_logging=sec_data.get("audit_logging", True),
            access_control=sec_data.get("access_control", True),
            data_classification=sec_data.get("data_classification", True)
        )

        return AppConfig(
            environment=environment,
            debug=config_data.get("debug", False),
            log_level=config_data.get("log_level", "INFO"),
            database=database,
            databricks=databricks,
            monitoring=monitoring,
            security=security
        )

    def save_config(self, config: AppConfig, path: Optional[str] = None) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to save
            path: Optional path to save to
        """
        save_path = path or self.config_path

        with open(save_path, 'w') as f:
            if save_path.endswith('.yaml') or save_path.endswith('.yml'):
                yaml.dump(config.to_dict(), f, default_flow_style=False, indent=2)
            elif save_path.endswith('.json'):
                json.dump(config.to_dict(), f, indent=2)
            else:
                raise ValueError(f"Unsupported configuration file format: {save_path}")


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Load configuration using ConfigManager.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Application configuration
    """
    manager = ConfigManager(config_path)
    return manager.load_config()


# Global configuration instance
_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get global configuration instance.

    Returns:
        Application configuration
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance


def reload_config() -> AppConfig:
    """
    Reload configuration from file.

    Returns:
        Reloaded application configuration
    """
    global _config_instance
    _config_instance = load_config()
    return _config_instance
