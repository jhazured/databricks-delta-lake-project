"""
Advanced unit tests for configuration utilities to improve coverage.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
import os
import tempfile
from typing import Dict, Any

from utils.common.config import ConfigManager, AppConfig, Environment, load_config
from utils.common.exceptions import ConfigurationError


class TestConfigManagerAdvanced:
    """Advanced tests for ConfigManager to improve coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
    
    def test_load_config_from_nonexistent_file(self):
        """Test loading config from nonexistent file."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            self.config_manager.load_config("nonexistent_config.yaml")
    
    def test_load_config_with_invalid_yaml(self):
        """Test loading config with invalid YAML."""
        invalid_yaml = """
        invalid: yaml: content: [unclosed
        """
        
        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with pytest.raises(ConfigurationError, match="Invalid YAML format"):
                self.config_manager.load_config("invalid.yaml")
    
    def test_load_config_with_missing_required_fields(self):
        """Test loading config with missing required fields."""
        incomplete_yaml = """
        database:
          host: localhost
          # Missing port and name
        """
        
        with patch("builtins.open", mock_open(read_data=incomplete_yaml)):
            with pytest.raises(ConfigurationError, match="Missing required configuration"):
                self.config_manager.load_config("incomplete.yaml")
    
    def test_load_config_with_invalid_environment(self):
        """Test loading config with invalid environment."""
        config_yaml = """
        environments:
          invalid_env:
            database:
              host: localhost
              port: 5432
              name: testdb
        """
        
        with patch("builtins.open", mock_open(read_data=config_yaml)):
            with pytest.raises(ConfigurationError, match="Invalid environment"):
                self.config_manager.load_config("config.yaml", environment="nonexistent")
    
    def test_load_config_with_environment_variables(self):
        """Test loading config with environment variable substitution."""
        config_yaml = """
        database:
          host: ${DB_HOST:localhost}
          port: ${DB_PORT:5432}
          name: ${DB_NAME:testdb}
          password: ${DB_PASSWORD}
        """
        
        with patch("builtins.open", mock_open(read_data=config_yaml)):
            with patch.dict(os.environ, {
                'DB_HOST': 'prod-server',
                'DB_PORT': '3306',
                'DB_NAME': 'production',
                'DB_PASSWORD': 'secret123'
            }):
                config = self.config_manager.load_config("config.yaml")
                
                assert config['database']['host'] == 'prod-server'
                assert config['database']['port'] == '3306'
                assert config['database']['name'] == 'production'
                assert config['database']['password'] == 'secret123'
    
    def test_load_config_with_missing_environment_variable(self):
        """Test loading config with missing required environment variable."""
        config_yaml = """
        database:
          password: ${DB_PASSWORD}
        """
        
        with patch("builtins.open", mock_open(read_data=config_yaml)):
            with pytest.raises(ConfigurationError, match="Environment variable not found"):
                self.config_manager.load_config("config.yaml")
    
    def test_load_config_with_nested_environment_variables(self):
        """Test loading config with nested environment variable substitution."""
        config_yaml = """
        services:
          api:
            url: ${API_BASE_URL}/v1
            timeout: ${API_TIMEOUT:30}
          database:
            connection_string: postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
        """
        
        with patch("builtins.open", mock_open(read_data=config_yaml)):
            with patch.dict(os.environ, {
                'API_BASE_URL': 'https://api.example.com',
                'DB_USER': 'user',
                'DB_PASSWORD': 'pass',
                'DB_HOST': 'localhost',
                'DB_PORT': '5432',
                'DB_NAME': 'testdb'
            }):
                config = self.config_manager.load_config("config.yaml")
                
                assert config['services']['api']['url'] == 'https://api.example.com/v1'
                assert config['services']['api']['timeout'] == '30'
                assert config['services']['database']['connection_string'] == 'postgresql://user:pass@localhost:5432/testdb'
    
    def test_validate_config_with_invalid_structure(self):
        """Test config validation with invalid structure."""
        invalid_config = {
            'database': {
                'host': 'localhost',
                'port': 'invalid_port'  # Should be integer
            }
        }
        
        with pytest.raises(ConfigurationError, match="Configuration validation failed"):
            self.config_manager.validate_config(invalid_config)
    
    def test_validate_config_with_missing_required_sections(self):
        """Test config validation with missing required sections."""
        incomplete_config = {
            'database': {
                'host': 'localhost',
                'port': 5432
            }
            # Missing 'api' section
        }
        
        required_sections = ['database', 'api']
        
        with pytest.raises(ConfigurationError, match="Missing required configuration section"):
            self.config_manager.validate_config(incomplete_config, required_sections)
    
    def test_get_config_value_with_nested_path(self):
        """Test getting config value with nested path."""
        config = {
            'services': {
                'api': {
                    'endpoints': {
                        'users': '/api/v1/users',
                        'products': '/api/v1/products'
                    }
                }
            }
        }
        
        self.config_manager.config = config
        
        # Test valid nested path
        value = self.config_manager.get_config_value('services.api.endpoints.users')
        assert value == '/api/v1/users'
        
        # Test invalid nested path
        with pytest.raises(ConfigurationError, match="Configuration path not found"):
            self.config_manager.get_config_value('services.api.nonexistent')
    
    def test_get_config_value_with_default(self):
        """Test getting config value with default."""
        config = {
            'database': {
                'host': 'localhost'
            }
        }
        
        self.config_manager.config = config
        
        # Test with existing value
        value = self.config_manager.get_config_value('database.host', default='default-host')
        assert value == 'localhost'
        
        # Test with missing value and default
        value = self.config_manager.get_config_value('database.port', default=5432)
        assert value == 5432
    
    def test_set_config_value_with_nested_path(self):
        """Test setting config value with nested path."""
        config = {}
        self.config_manager.config = config
        
        # Set nested value
        self.config_manager.set_config_value('services.api.timeout', 30)
        
        assert self.config_manager.config['services']['api']['timeout'] == 30
    
    def test_merge_configs(self):
        """Test merging multiple configs."""
        base_config = {
            'database': {
                'host': 'localhost',
                'port': 5432
            },
            'api': {
                'timeout': 30
            }
        }
        
        override_config = {
            'database': {
                'host': 'prod-server',
                'name': 'production'
            },
            'logging': {
                'level': 'INFO'
            }
        }
        
        merged = self.config_manager.merge_configs(base_config, override_config)
        
        assert merged['database']['host'] == 'prod-server'  # Overridden
        assert merged['database']['port'] == 5432  # From base
        assert merged['database']['name'] == 'production'  # From override
        assert merged['api']['timeout'] == 30  # From base
        assert merged['logging']['level'] == 'INFO'  # From override
    
    def test_merge_configs_with_deep_merge(self):
        """Test deep merging of nested configs."""
        base_config = {
            'services': {
                'api': {
                    'timeout': 30,
                    'retries': 3
                }
            }
        }
        
        override_config = {
            'services': {
                'api': {
                    'timeout': 60
                },
                'database': {
                    'host': 'localhost'
                }
            }
        }
        
        merged = self.config_manager.merge_configs(base_config, override_config, deep=True)
        
        assert merged['services']['api']['timeout'] == 60  # Overridden
        assert merged['services']['api']['retries'] == 3  # From base
        assert merged['services']['database']['host'] == 'localhost'  # From override
    
    def test_save_config_to_file(self):
        """Test saving config to file."""
        config = {
            'database': {
                'host': 'localhost',
                'port': 5432
            }
        }
        
        with patch("builtins.open", mock_open()) as mock_file:
            self.config_manager.save_config(config, "output.yaml")
            
            mock_file.assert_called_once_with("output.yaml", 'w')
            # Verify YAML was written
            mock_file().write.assert_called()
    
    def test_save_config_with_invalid_data(self):
        """Test saving config with invalid data."""
        invalid_config = {
            'database': {
                'host': object()  # Non-serializable object
            }
        }
        
        with pytest.raises(ConfigurationError, match="Failed to save configuration"):
            self.config_manager.save_config(invalid_config, "output.yaml")
    
    def test_reload_config(self):
        """Test reloading configuration."""
        initial_config = {'database': {'host': 'localhost'}}
        updated_config = {'database': {'host': 'updated-host'}}
        
        self.config_manager.config = initial_config
        
        with patch.object(self.config_manager, 'load_config', return_value=updated_config):
            self.config_manager.reload_config("config.yaml")
            
            assert self.config_manager.config == updated_config
    
    def test_get_all_config_paths(self):
        """Test getting all configuration paths."""
        config = {
            'database': {
                'host': 'localhost',
                'port': 5432
            },
            'api': {
                'timeout': 30,
                'endpoints': {
                    'users': '/users',
                    'products': '/products'
                }
            }
        }
        
        self.config_manager.config = config
        paths = self.config_manager.get_all_config_paths()
        
        expected_paths = [
            'database.host',
            'database.port',
            'api.timeout',
            'api.endpoints.users',
            'api.endpoints.products'
        ]
        
        assert set(paths) == set(expected_paths)
    
    def test_config_manager_with_custom_validators(self):
        """Test config manager with custom validators."""
        def custom_validator(config):
            if 'custom_field' not in config:
                raise ConfigurationError("Custom field is required")
        
        config_manager = ConfigManager(validators=[custom_validator])
        
        # Test with valid config
        valid_config = {'custom_field': 'value'}
        config_manager.validate_config(valid_config)
        
        # Test with invalid config
        invalid_config = {'other_field': 'value'}
        with pytest.raises(ConfigurationError, match="Custom field is required"):
            config_manager.validate_config(invalid_config)


class TestAppConfigAdvanced:
    """Advanced tests for AppConfig to improve coverage."""
    
    def test_app_config_initialization_with_invalid_environment(self):
        """Test AppConfig initialization with invalid environment."""
        with pytest.raises(ValueError, match="Invalid environment"):
            AppConfig(environment="invalid_env")
    
    def test_app_config_with_custom_config_path(self):
        """Test AppConfig with custom config path."""
        with patch.object(ConfigManager, 'load_config') as mock_load:
            mock_load.return_value = {'database': {'host': 'localhost'}}
            
            config = AppConfig(config_path="custom_config.yaml")
            
            mock_load.assert_called_once_with("custom_config.yaml", environment="development")
    
    def test_app_config_property_access(self):
        """Test AppConfig property access."""
        config_data = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'testdb'
            },
            'api': {
                'timeout': 30,
                'base_url': 'https://api.example.com'
            }
        }
        
        with patch.object(ConfigManager, 'load_config', return_value=config_data):
            config = AppConfig()
            
            assert config.database_host == 'localhost'
            assert config.database_port == 5432
            assert config.database_name == 'testdb'
            assert config.api_timeout == 30
            assert config.api_base_url == 'https://api.example.com'
    
    def test_app_config_property_access_missing(self):
        """Test AppConfig property access with missing properties."""
        config_data = {'database': {'host': 'localhost'}}
        
        with patch.object(ConfigManager, 'load_config', return_value=config_data):
            config = AppConfig()
            
            with pytest.raises(AttributeError):
                _ = config.nonexistent_property
    
    def test_app_config_environment_specific_config(self):
        """Test AppConfig with environment-specific configuration."""
        config_data = {
            'environments': {
                'development': {
                    'database': {'host': 'dev-db'}
                },
                'production': {
                    'database': {'host': 'prod-db'}
                }
            }
        }
        
        with patch.object(ConfigManager, 'load_config', return_value=config_data):
            # Test development environment
            dev_config = AppConfig(environment="development")
            assert dev_config.database_host == 'dev-db'
            
            # Test production environment
            prod_config = AppConfig(environment="production")
            assert prod_config.database_host == 'prod-db'


class TestEnvironmentAdvanced:
    """Advanced tests for Environment enum."""
    
    def test_environment_values(self):
        """Test Environment enum values."""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TESTING.value == "testing"
    
    def test_environment_from_string(self):
        """Test creating Environment from string."""
        assert Environment.from_string("development") == Environment.DEVELOPMENT
        assert Environment.from_string("staging") == Environment.STAGING
        assert Environment.from_string("production") == Environment.PRODUCTION
        assert Environment.from_string("testing") == Environment.TESTING
    
    def test_environment_from_invalid_string(self):
        """Test creating Environment from invalid string."""
        with pytest.raises(ValueError, match="Invalid environment"):
            Environment.from_string("invalid")
    
    def test_environment_is_production(self):
        """Test Environment.is_production method."""
        assert Environment.PRODUCTION.is_production() is True
        assert Environment.DEVELOPMENT.is_production() is False
        assert Environment.STAGING.is_production() is False
        assert Environment.TESTING.is_production() is False
    
    def test_environment_is_development(self):
        """Test Environment.is_development method."""
        assert Environment.DEVELOPMENT.is_development() is True
        assert Environment.PRODUCTION.is_development() is False
        assert Environment.STAGING.is_development() is False
        assert Environment.TESTING.is_development() is False


class TestLoadConfigFunctionAdvanced:
    """Advanced tests for load_config function."""
    
    def test_load_config_with_default_path(self):
        """Test load_config with default path."""
        with patch.object(ConfigManager, 'load_config') as mock_load:
            mock_load.return_value = {'database': {'host': 'localhost'}}
            
            config = load_config()
            
            mock_load.assert_called_once()
    
    def test_load_config_with_custom_path(self):
        """Test load_config with custom path."""
        with patch.object(ConfigManager, 'load_config') as mock_load:
            mock_load.return_value = {'database': {'host': 'localhost'}}
            
            config = load_config("custom.yaml")
            
            mock_load.assert_called_once_with("custom.yaml", environment="development")
    
    def test_load_config_with_environment(self):
        """Test load_config with specific environment."""
        with patch.object(ConfigManager, 'load_config') as mock_load:
            mock_load.return_value = {'database': {'host': 'localhost'}}
            
            config = load_config("config.yaml", "production")
            
            mock_load.assert_called_once_with("config.yaml", environment="production")
    
    def test_load_config_with_error_handling(self):
        """Test load_config with error handling."""
        with patch.object(ConfigManager, 'load_config') as mock_load:
            mock_load.side_effect = ConfigurationError("Config error")
            
            with pytest.raises(ConfigurationError, match="Config error"):
                load_config("config.yaml")
    
    def test_load_config_with_validation(self):
        """Test load_config with validation."""
        config_data = {'database': {'host': 'localhost'}}
        
        with patch.object(ConfigManager, 'load_config', return_value=config_data):
            with patch.object(ConfigManager, 'validate_config') as mock_validate:
                config = load_config("config.yaml", validate=True)
                
                mock_validate.assert_called_once_with(config_data)
