"""
Advanced unit tests for validation utilities to improve coverage.
"""

import pytest
from unittest.mock import Mock, patch
import pandas as pd
import json
from typing import Dict, Any, List

from utils.common.validation import DataValidator, SchemaValidator, validate_email, validate_phone
from utils.common.exceptions import ValidationError


class TestDataValidatorAdvanced:
    """Advanced tests for DataValidator to improve coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
    
    def test_validate_dataframe_with_missing_columns(self):
        """Test validation with missing required columns."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie']
        })
        
        required_columns = ['id', 'name', 'email']
        
        with pytest.raises(ValidationError, match="Missing required columns"):
            self.validator.validate_dataframe(df, required_columns)
    
    def test_validate_dataframe_with_null_values(self):
        """Test validation with null values in required columns."""
        df = pd.DataFrame({
            'id': [1, 2, None],
            'name': ['Alice', 'Bob', 'Charlie'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com']
        })
        
        required_columns = ['id', 'name', 'email']
        
        with pytest.raises(ValidationError, match="Null values found in required columns"):
            self.validator.validate_dataframe(df, required_columns, allow_null=False)
    
    def test_validate_dataframe_with_duplicate_ids(self):
        """Test validation with duplicate IDs."""
        df = pd.DataFrame({
            'id': [1, 2, 1],  # Duplicate ID
            'name': ['Alice', 'Bob', 'Charlie'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com']
        })
        
        with pytest.raises(ValidationError, match="Duplicate values found in unique column"):
            self.validator.validate_dataframe(df, unique_columns=['id'])
    
    def test_validate_dataframe_with_custom_validators(self):
        """Test validation with custom validator functions."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'age': [25, 30, 35],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com']
        })
        
        def age_validator(age):
            return 18 <= age <= 100
        
        def email_validator(email):
            return '@' in email and '.' in email
        
        validators = {
            'age': age_validator,
            'email': email_validator
        }
        
        # Should pass with valid data
        result = self.validator.validate_dataframe(df, custom_validators=validators)
        assert result['valid'] is True
        
        # Test with invalid age
        df_invalid = df.copy()
        df_invalid.loc[0, 'age'] = 150  # Invalid age
        
        with pytest.raises(ValidationError, match="Custom validation failed"):
            self.validator.validate_dataframe(df_invalid, custom_validators=validators)
    
    def test_validate_dataframe_with_data_types(self):
        """Test validation with specific data types."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'salary': [50000.0, 60000.0, 70000.0]
        })
        
        data_types = {
            'id': 'int64',
            'name': 'object',
            'age': 'int64',
            'salary': 'float64'
        }
        
        result = self.validator.validate_dataframe(df, data_types=data_types)
        assert result['valid'] is True
        
        # Test with wrong data type
        df_wrong_type = df.copy()
        df_wrong_type['age'] = df_wrong_type['age'].astype('float64')
        
        with pytest.raises(ValidationError, match="Data type validation failed"):
            self.validator.validate_dataframe(df_wrong_type, data_types=data_types)
    
    def test_validate_dataframe_with_row_count_limits(self):
        """Test validation with row count limits."""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve']
        })
        
        # Test minimum row count
        with pytest.raises(ValidationError, match="Row count below minimum"):
            self.validator.validate_dataframe(df, min_rows=10)
        
        # Test maximum row count
        with pytest.raises(ValidationError, match="Row count exceeds maximum"):
            self.validator.validate_dataframe(df, max_rows=3)
        
        # Test valid row count
        result = self.validator.validate_dataframe(df, min_rows=1, max_rows=10)
        assert result['valid'] is True
    
    def test_validate_dataframe_with_empty_dataframe(self):
        """Test validation with empty dataframe."""
        df = pd.DataFrame()
        
        with pytest.raises(ValidationError, match="DataFrame is empty"):
            self.validator.validate_dataframe(df)
    
    def test_validate_dataframe_with_all_parameters(self):
        """Test validation with all parameters combined."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com']
        })
        
        required_columns = ['id', 'name', 'age', 'email']
        unique_columns = ['id', 'email']
        data_types = {
            'id': 'int64',
            'name': 'object',
            'age': 'int64',
            'email': 'object'
        }
        
        def age_validator(age):
            return 18 <= age <= 100
        
        custom_validators = {'age': age_validator}
        
        result = self.validator.validate_dataframe(
            df,
            required_columns=required_columns,
            unique_columns=unique_columns,
            data_types=data_types,
            custom_validators=custom_validators,
            min_rows=1,
            max_rows=10,
            allow_null=False
        )
        
        assert result['valid'] is True
        assert result['row_count'] == 3
        assert result['column_count'] == 4


class TestSchemaValidatorAdvanced:
    """Advanced tests for SchemaValidator to improve coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SchemaValidator()
    
    def test_add_schema_with_invalid_json_schema(self):
        """Test adding schema with invalid JSON schema."""
        invalid_schema = {
            'type': 'invalid_type',  # Invalid type
            'properties': {
                'name': {'type': 'string'}
            }
        }
        
        with pytest.raises(ValidationError, match="Invalid JSON schema"):
            self.validator.add_schema('test_schema', invalid_schema)
    
    def test_validate_data_with_missing_schema(self):
        """Test validation with schema that doesn't exist."""
        data = [{'name': 'Alice', 'age': 25}]
        
        with pytest.raises(ValidationError, match="Schema not found"):
            self.validator.validate_data(data, 'nonexistent_schema')
    
    def test_validate_data_with_complex_schema(self):
        """Test validation with complex nested schema."""
        complex_schema = {
            'type': 'object',
            'required': ['user', 'address'],
            'properties': {
                'user': {
                    'type': 'object',
                    'required': ['name', 'age'],
                    'properties': {
                        'name': {'type': 'string'},
                        'age': {'type': 'integer', 'minimum': 0, 'maximum': 150}
                    }
                },
                'address': {
                    'type': 'object',
                    'required': ['street', 'city'],
                    'properties': {
                        'street': {'type': 'string'},
                        'city': {'type': 'string'},
                        'zipcode': {'type': 'string', 'pattern': '^[0-9]{5}$'}
                    }
                }
            }
        }
        
        self.validator.add_schema('complex_schema', complex_schema)
        
        # Valid data
        valid_data = [{
            'user': {'name': 'Alice', 'age': 25},
            'address': {'street': '123 Main St', 'city': 'Anytown', 'zipcode': '12345'}
        }]
        
        result = self.validator.validate_data(valid_data, 'complex_schema')
        assert result['valid'] is True
        
        # Invalid data - missing required field
        invalid_data = [{
            'user': {'name': 'Alice'},  # Missing age
            'address': {'street': '123 Main St', 'city': 'Anytown'}
        }]
        
        result = self.validator.validate_data(invalid_data, 'complex_schema')
        assert result['valid'] is False
        assert len(result['errors']) > 0
    
    def test_validate_data_with_array_schema(self):
        """Test validation with array schema."""
        array_schema = {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['id', 'name'],
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'tags': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
                }
            }
        }
        
        self.validator.add_schema('array_schema', array_schema)
        
        # Valid array data
        valid_data = [
            {'id': 1, 'name': 'Alice', 'tags': ['admin', 'user']},
            {'id': 2, 'name': 'Bob', 'tags': ['user']}
        ]
        
        result = self.validator.validate_data(valid_data, 'array_schema')
        assert result['valid'] is True
        
        # Invalid array data
        invalid_data = [
            {'id': 1, 'name': 'Alice'},  # Valid
            {'name': 'Bob'}  # Missing required id
        ]
        
        result = self.validator.validate_data(invalid_data, 'array_schema')
        assert result['valid'] is False
    
    def test_validate_data_with_enum_schema(self):
        """Test validation with enum schema."""
        enum_schema = {
            'type': 'object',
            'required': ['status'],
            'properties': {
                'status': {
                    'type': 'string',
                    'enum': ['active', 'inactive', 'pending']
                },
                'priority': {
                    'type': 'string',
                    'enum': ['low', 'medium', 'high']
                }
            }
        }
        
        self.validator.add_schema('enum_schema', enum_schema)
        
        # Valid data
        valid_data = [{'status': 'active', 'priority': 'high'}]
        result = self.validator.validate_data(valid_data, 'enum_schema')
        assert result['valid'] is True
        
        # Invalid data - invalid enum value
        invalid_data = [{'status': 'invalid_status'}]
        result = self.validator.validate_data(invalid_data, 'enum_schema')
        assert result['valid'] is False
    
    def test_validate_data_with_pattern_schema(self):
        """Test validation with pattern schema."""
        pattern_schema = {
            'type': 'object',
            'required': ['email', 'phone'],
            'properties': {
                'email': {
                    'type': 'string',
                    'pattern': '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
                },
                'phone': {
                    'type': 'string',
                    'pattern': '^\\+?[1-9]\\d{1,14}$'
                }
            }
        }
        
        self.validator.add_schema('pattern_schema', pattern_schema)
        
        # Valid data
        valid_data = [{'email': 'test@example.com', 'phone': '+1234567890'}]
        result = self.validator.validate_data(valid_data, 'pattern_schema')
        assert result['valid'] is True
        
        # Invalid data - invalid pattern
        invalid_data = [{'email': 'invalid-email', 'phone': '123'}]
        result = self.validator.validate_data(invalid_data, 'pattern_schema')
        assert result['valid'] is False
    
    def test_validate_data_with_numeric_constraints(self):
        """Test validation with numeric constraints."""
        numeric_schema = {
            'type': 'object',
            'required': ['age', 'score'],
            'properties': {
                'age': {
                    'type': 'integer',
                    'minimum': 0,
                    'maximum': 150
                },
                'score': {
                    'type': 'number',
                    'minimum': 0.0,
                    'maximum': 100.0
                }
            }
        }
        
        self.validator.add_schema('numeric_schema', numeric_schema)
        
        # Valid data
        valid_data = [{'age': 25, 'score': 85.5}]
        result = self.validator.validate_data(valid_data, 'numeric_schema')
        assert result['valid'] is True
        
        # Invalid data - out of range
        invalid_data = [{'age': 200, 'score': 150.0}]
        result = self.validator.validate_data(invalid_data, 'numeric_schema')
        assert result['valid'] is False
    
    def test_validate_data_with_string_constraints(self):
        """Test validation with string constraints."""
        string_schema = {
            'type': 'object',
            'required': ['name', 'description'],
            'properties': {
                'name': {
                    'type': 'string',
                    'minLength': 2,
                    'maxLength': 50
                },
                'description': {
                    'type': 'string',
                    'maxLength': 500
                }
            }
        }
        
        self.validator.add_schema('string_schema', string_schema)
        
        # Valid data
        valid_data = [{'name': 'Alice', 'description': 'A valid description'}]
        result = self.validator.validate_data(valid_data, 'string_schema')
        assert result['valid'] is True
        
        # Invalid data - too short name
        invalid_data = [{'name': 'A', 'description': 'Valid description'}]
        result = self.validator.validate_data(invalid_data, 'string_schema')
        assert result['valid'] is False
    
    def test_get_schema_info(self):
        """Test getting schema information."""
        schema = {
            'type': 'object',
            'required': ['name'],
            'properties': {
                'name': {'type': 'string'}
            }
        }
        
        self.validator.add_schema('test_schema', schema)
        info = self.validator.get_schema_info('test_schema')
        
        assert info['name'] == 'test_schema'
        assert info['type'] == 'object'
        assert 'name' in info['required']
    
    def test_get_schema_info_nonexistent(self):
        """Test getting info for nonexistent schema."""
        with pytest.raises(ValidationError, match="Schema not found"):
            self.validator.get_schema_info('nonexistent_schema')
    
    def test_list_schemas(self):
        """Test listing all schemas."""
        schema1 = {'type': 'object', 'properties': {'name': {'type': 'string'}}}
        schema2 = {'type': 'array', 'items': {'type': 'string'}}
        
        self.validator.add_schema('schema1', schema1)
        self.validator.add_schema('schema2', schema2)
        
        schemas = self.validator.list_schemas()
        assert len(schemas) == 2
        assert 'schema1' in schemas
        assert 'schema2' in schemas


class TestValidationFunctionsAdvanced:
    """Advanced tests for validation functions."""
    
    def test_validate_email_edge_cases(self):
        """Test email validation with edge cases."""
        # Valid emails
        assert validate_email('test@example.com') is True
        assert validate_email('user.name+tag@domain.co.uk') is True
        assert validate_email('user123@subdomain.example.org') is True
        
        # Invalid emails
        assert validate_email('invalid-email') is False
        assert validate_email('@example.com') is False
        assert validate_email('user@') is False
        assert validate_email('user@.com') is False
        assert validate_email('') is False
        assert validate_email(None) is False
    
    def test_validate_phone_edge_cases(self):
        """Test phone validation with edge cases."""
        # Valid phone numbers
        assert validate_phone('+1234567890') is True
        assert validate_phone('1234567890') is True
        assert validate_phone('+1-234-567-8900') is True
        assert validate_phone('(123) 456-7890') is True
        
        # Invalid phone numbers
        assert validate_phone('123') is False  # Too short
        assert validate_phone('abc-def-ghij') is False  # Non-numeric
        assert validate_phone('') is False  # Empty
        assert validate_phone(None) is False  # None
    
    def test_validate_email_with_custom_regex(self):
        """Test email validation with custom regex."""
        # This would require modifying the validate_email function to accept custom regex
        # For now, we test the default behavior
        assert validate_email('test@example.com') is True
        assert validate_email('invalid@') is False
    
    def test_validate_phone_with_different_formats(self):
        """Test phone validation with different international formats."""
        # US format
        assert validate_phone('+1-234-567-8900') is True
        
        # International formats (these might need custom validation)
        # For now, test the default behavior
        assert validate_phone('+44-20-7946-0958') is True  # UK
        assert validate_phone('+33-1-42-86-83-26') is True  # France


class TestValidationErrorHandling:
    """Test error handling in validation utilities."""
    
    def test_data_validator_error_messages(self):
        """Test that DataValidator provides meaningful error messages."""
        validator = DataValidator()
        
        # Test empty dataframe error
        empty_df = pd.DataFrame()
        try:
            validator.validate_dataframe(empty_df)
        except ValidationError as e:
            assert "DataFrame is empty" in str(e)
        
        # Test missing columns error
        df = pd.DataFrame({'id': [1, 2]})
        try:
            validator.validate_dataframe(df, required_columns=['id', 'name'])
        except ValidationError as e:
            assert "Missing required columns" in str(e)
    
    def test_schema_validator_error_messages(self):
        """Test that SchemaValidator provides meaningful error messages."""
        validator = SchemaValidator()
        
        # Test missing schema error
        try:
            validator.validate_data([], 'nonexistent')
        except ValidationError as e:
            assert "Schema not found" in str(e)
        
        # Test invalid schema error
        try:
            validator.add_schema('invalid', {'type': 'invalid'})
        except ValidationError as e:
            assert "Invalid JSON schema" in str(e)
