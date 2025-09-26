"""
Unit tests for common utilities.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open
from utils.common.config import ConfigManager, AppConfig, Environment, load_config
from utils.common.validation import DataValidator, SchemaValidator, validate_email, validate_phone
from utils.common.exceptions import ValidationError, ConfigurationError
from utils.common.logging import setup_logging, StructuredLogger


class TestConfigManager:
    """Test configuration manager."""
    
    def test_config_manager_initialization(self):
        """Test config manager initialization."""
        manager = ConfigManager()
        assert manager.config_path is not None
    
    def test_load_config_from_file(self):
        """Test loading configuration from file."""
        config_data = {
            "environment": "dev",
            "debug": True,
            "log_level": "DEBUG",
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "username": "test_user",
                "password": "test_pass"
            },
            "databricks": {
                "host": "https://test.databricks.com",
                "token": "test_token"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            config = manager.load_config()
            
            assert config.environment == Environment.DEV
            assert config.debug is True
            assert config.log_level == "DEBUG"
            assert config.database.host == "localhost"
            assert config.database.port == 5432
            assert config.databricks.host == "https://test.databricks.com"
        finally:
            os.unlink(temp_path)
    
    def test_config_override_with_env(self):
        """Test configuration override with environment variables."""
        config_data = {
            "environment": "dev",
            "log_level": "INFO",
            "databricks": {
                "host": "https://default.databricks.com",
                "token": "default_token"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            with patch.dict(os.environ, {
                'DATABRICKS_HOST': 'https://env.databricks.com',
                'LOG_LEVEL': 'DEBUG'
            }):
                manager = ConfigManager(temp_path)
                config = manager.load_config()
                
                assert config.databricks.host == "https://env.databricks.com"
                assert config.log_level == "DEBUG"
        finally:
            os.unlink(temp_path)
    
    def test_config_file_not_found(self):
        """Test error when configuration file is not found."""
        manager = ConfigManager("nonexistent.yaml")
        with pytest.raises(FileNotFoundError):
            manager.load_config()


class TestDataValidator:
    """Test data validator."""
    
    def test_data_validator_initialization(self):
        """Test data validator initialization."""
        validator = DataValidator()
        assert validator.validation_rules == {}
        assert validator.custom_validators == {}
    
    def test_add_validation_rule(self):
        """Test adding validation rule."""
        validator = DataValidator()
        
        def test_rule(value):
            if value is None:
                raise ValidationError("Value cannot be None")
        
        validator.add_rule("test_field", test_rule)
        assert "test_field" in validator.validation_rules
        assert len(validator.validation_rules["test_field"]) == 1
    
    def test_validate_data_success(self):
        """Test successful data validation."""
        validator = DataValidator()
        
        def positive_rule(value):
            if value is not None and value <= 0:
                raise ValidationError("Value must be positive")
        
        validator.add_rule("number", positive_rule)
        
        data = {"number": 5}
        errors = validator.validate(data)
        assert len(errors) == 0
        assert validator.is_valid(data) is True
    
    def test_validate_data_failure(self):
        """Test data validation failure."""
        validator = DataValidator()
        
        def positive_rule(value):
            if value is not None and value <= 0:
                raise ValidationError("Value must be positive")
        
        validator.add_rule("number", positive_rule)
        
        data = {"number": -1}
        errors = validator.validate(data)
        assert "number" in errors
        assert len(errors["number"]) == 1
        assert "Value must be positive" in errors["number"][0]
        assert validator.is_valid(data) is False


class TestSchemaValidator:
    """Test schema validator."""
    
    def test_schema_validator_initialization(self):
        """Test schema validator initialization."""
        validator = SchemaValidator()
        assert validator.schemas == {}
    
    def test_add_schema(self):
        """Test adding schema."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        validator.add_schema("person", schema)
        assert "person" in validator.schemas
        assert validator.schemas["person"] == schema
    
    def test_validate_data_against_schema_success(self):
        """Test successful schema validation."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name"]
        }
        
        validator.add_schema("person", schema)
        
        data = [{"name": "John", "age": 30}]
        result = validator.validate_data(data, "person")
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["validated_count"] == 1
    
    def test_validate_data_against_schema_failure(self):
        """Test schema validation failure."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name"]
        }
        
        validator.add_schema("person", schema)
        
        data = [{"age": 30}]  # Missing required field
        result = validator.validate_data(data, "person")
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "Required field 'name' is missing" in result["errors"][0]


class TestValidationFunctions:
    """Test validation functions."""
    
    def test_validate_email_success(self):
        """Test successful email validation."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        
        for email in valid_emails:
            validate_email(email)  # Should not raise exception
    
    def test_validate_email_failure(self):
        """Test email validation failure."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com"
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validate_email(email)
    
    def test_validate_phone_success(self):
        """Test successful phone validation."""
        valid_phones = [
            "+1234567890",
            "123-456-7890",
            "(123) 456-7890",
            "123 456 7890"
        ]
        
        for phone in valid_phones:
            validate_phone(phone)  # Should not raise exception
    
    def test_validate_phone_failure(self):
        """Test phone validation failure."""
        invalid_phones = [
            "123",
            "abc-def-ghij",
            "123-456-789",
            ""
        ]
        
        for phone in invalid_phones:
            with pytest.raises(ValidationError):
                validate_phone(phone)


class TestLogging:
    """Test logging utilities."""
    
    def test_setup_logging(self):
        """Test logging setup."""
        # This test just ensures setup_logging doesn't crash
        setup_logging(level="DEBUG")
        assert True  # If we get here, no exception was raised
    
    def test_structured_logger(self):
        """Test structured logger."""
        logger = StructuredLogger("test")
        
        # Test that logging methods don't crash
        logger.info("Test message", extra_field="extra_value")
        logger.warning("Warning message", warning_type="test")
        logger.error("Error message", error_code="TEST_ERROR")
        logger.debug("Debug message", debug_info="test_debug")
        
        assert True  # If we get here, no exception was raised


class TestExceptions:
    """Test custom exceptions."""
    
    def test_delta_lake_error(self):
        """Test DeltaLakeError."""
        error = ValidationError("Test error", field="test_field", value="test_value")
        
        assert error.message == "Test error"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.field == "test_field"
        assert error.value == "test_value"
        
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "ValidationError"
        assert error_dict["message"] == "Test error"
        assert error_dict["error_code"] == "VALIDATION_ERROR"
        assert error_dict["details"]["field"] == "test_field"
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Config error", config_key="test_key")
        
        assert error.message == "Config error"
        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.config_key == "test_key"
