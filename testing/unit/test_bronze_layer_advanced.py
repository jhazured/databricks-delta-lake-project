"""
Advanced unit tests for bronze layer processor to improve coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime
import uuid

from scripts.data_processing.bronze_layer import BronzeLayerProcessor, SampleDataGenerator
from utils.common.exceptions import ValidationError


class TestBronzeLayerProcessorAdvanced:
    """Advanced tests for BronzeLayerProcessor to improve coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = BronzeLayerProcessor()
    
    def test_process_raw_data_with_empty_list(self):
        """Test processing empty raw data list."""
        result = self.processor.process_raw_data([], 'test_source')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert '_bronze_ingestion_timestamp' in result.columns
        assert '_bronze_source' in result.columns
        assert '_bronze_batch_id' in result.columns
    
    def test_process_raw_data_with_invalid_data(self):
        """Test processing invalid raw data."""
        invalid_data = [
            {'id': 1, 'name': 'Alice'},  # Missing required fields
            {'invalid': 'data'},  # Completely invalid structure
            None,  # None value
            'invalid_string'  # Wrong type
        ]
        
        with pytest.raises(ValidationError):
            self.processor.process_raw_data(invalid_data, 'test_source')
    
    def test_process_raw_data_with_mixed_valid_invalid(self):
        """Test processing data with mix of valid and invalid records."""
        mixed_data = [
            {'id': '1', 'name': 'Alice', 'email': 'alice@test.com', 'phone': '123-456-7890'},
            {'id': '2', 'name': 'Bob'},  # Missing required fields
            {'id': '3', 'name': 'Charlie', 'email': 'charlie@test.com', 'phone': '987-654-3210'}
        ]
        
        # Should raise validation error due to invalid record
        with pytest.raises(ValidationError):
            self.processor.process_raw_data(mixed_data, 'test_source')
    
    def test_process_raw_data_with_duplicate_ids(self):
        """Test processing data with duplicate IDs."""
        duplicate_data = [
            {'id': '1', 'name': 'Alice', 'email': 'alice@test.com', 'phone': '123-456-7890'},
            {'id': '1', 'name': 'Alice Duplicate', 'email': 'alice2@test.com', 'phone': '123-456-7891'}
        ]
        
        result = self.processor.process_raw_data(duplicate_data, 'test_source')
        
        # Should process both records (duplicates allowed in bronze layer)
        assert len(result) == 2
        assert result['id'].tolist() == ['1', '1']
    
    def test_process_raw_data_with_special_characters(self):
        """Test processing data with special characters and unicode."""
        special_data = [
            {
                'id': '1',
                'name': 'José María',
                'email': 'josé@test.com',
                'phone': '+1-234-567-8900',
                'notes': 'Special chars: @#$%^&*()'
            }
        ]
        
        result = self.processor.process_raw_data(special_data, 'test_source')
        
        assert len(result) == 1
        assert result.iloc[0]['name'] == 'José María'
        assert result.iloc[0]['notes'] == 'Special chars: @#$%^&*()'
    
    def test_process_raw_data_with_large_dataset(self):
        """Test processing large dataset."""
        large_data = []
        for i in range(1000):
            large_data.append({
                'id': str(i),
                'name': f'User {i}',
                'email': f'user{i}@test.com',
                'phone': f'555-{i:04d}'
            })
        
        result = self.processor.process_raw_data(large_data, 'test_source')
        
        assert len(result) == 1000
        assert result['_bronze_source'].iloc[0] == 'test_source'
        assert result['_bronze_record_count'].iloc[0] == 1000
    
    def test_process_raw_data_with_optional_fields(self):
        """Test processing data with optional fields."""
        data_with_optionals = [
            {
                'id': '1',
                'name': 'Alice',
                'email': 'alice@test.com',
                'phone': '123-456-7890',
                'address': '123 Main St',
                'city': 'Anytown',
                'country': 'USA',
                'age': 25,
                'is_active': True
            }
        ]
        
        result = self.processor.process_raw_data(data_with_optionals, 'test_source')
        
        assert len(result) == 1
        assert result.iloc[0]['address'] == '123 Main St'
        assert result.iloc[0]['age'] == 25
        assert result.iloc[0]['is_active'] is True
    
    def test_process_raw_data_with_nested_data(self):
        """Test processing data with nested structures."""
        nested_data = [
            {
                'id': '1',
                'name': 'Alice',
                'email': 'alice@test.com',
                'phone': '123-456-7890',
                'preferences': {
                    'theme': 'dark',
                    'notifications': True
                },
                'tags': ['vip', 'premium']
            }
        ]
        
        result = self.processor.process_raw_data(nested_data, 'test_source')
        
        assert len(result) == 1
        # Nested data should be serialized to string
        assert isinstance(result.iloc[0]['preferences'], str)
        assert isinstance(result.iloc[0]['tags'], str)
    
    def test_process_raw_data_with_different_data_types(self):
        """Test processing data with various data types."""
        mixed_types_data = [
            {
                'id': '1',
                'name': 'Alice',
                'email': 'alice@test.com',
                'phone': '123-456-7890',
                'age': 25,
                'salary': 50000.50,
                'is_active': True,
                'last_login': '2024-01-01T10:00:00Z',
                'score': None
            }
        ]
        
        result = self.processor.process_raw_data(mixed_types_data, 'test_source')
        
        assert len(result) == 1
        assert result.iloc[0]['age'] == 25
        assert result.iloc[0]['salary'] == 50000.50
        assert result.iloc[0]['is_active'] is True
        assert pd.isna(result.iloc[0]['score'])
    
    def test_validate_raw_data_with_custom_rules(self):
        """Test validation with custom business rules."""
        # This would require extending the processor to accept custom validation rules
        # For now, test the default validation
        valid_data = [
            {'id': '1', 'name': 'Alice', 'email': 'alice@test.com', 'phone': '123-456-7890'}
        ]
        
        result = self.processor.process_raw_data(valid_data, 'test_source')
        assert len(result) == 1
    
    def test_process_raw_data_with_timestamp_handling(self):
        """Test timestamp handling in processed data."""
        data = [
            {'id': '1', 'name': 'Alice', 'email': 'alice@test.com', 'phone': '123-456-7890'}
        ]
        
        with patch('scripts.data_processing.bronze_layer.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            result = self.processor.process_raw_data(data, 'test_source')
            
            assert result['_bronze_ingestion_timestamp'].iloc[0] == datetime(2024, 1, 1, 12, 0, 0)
    
    def test_process_raw_data_with_batch_id_generation(self):
        """Test batch ID generation."""
        data = [
            {'id': '1', 'name': 'Alice', 'email': 'alice@test.com', 'phone': '123-456-7890'}
        ]
        
        with patch('scripts.data_processing.bronze_layer.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            result = self.processor.process_raw_data(data, 'test_source')
            
            expected_batch_id = "batch_20240101_120000"
            assert result['_bronze_batch_id'].iloc[0] == expected_batch_id
    
    def test_process_raw_data_with_different_sources(self):
        """Test processing data from different sources."""
        data = [
            {'id': '1', 'name': 'Alice', 'email': 'alice@test.com', 'phone': '123-456-7890'}
        ]
        
        # Test different source names
        sources = ['api', 'file_upload', 'streaming', 'manual_entry']
        
        for source in sources:
            result = self.processor.process_raw_data(data, source)
            assert result['_bronze_source'].iloc[0] == source
    
    def test_process_raw_data_error_handling(self):
        """Test error handling in data processing."""
        # Test with completely invalid data structure
        invalid_data = "not a list"
        
        with pytest.raises(ValidationError):
            self.processor.process_raw_data(invalid_data, 'test_source')
        
        # Test with None data
        with pytest.raises(ValidationError):
            self.processor.process_raw_data(None, 'test_source')
    
    def test_process_raw_data_with_missing_required_fields(self):
        """Test processing data missing required fields."""
        incomplete_data = [
            {'id': '1', 'name': 'Alice'},  # Missing email and phone
            {'email': 'bob@test.com', 'phone': '123-456-7890'},  # Missing id and name
        ]
        
        with pytest.raises(ValidationError):
            self.processor.process_raw_data(incomplete_data, 'test_source')
    
    def test_process_raw_data_with_extra_fields(self):
        """Test processing data with extra fields not in schema."""
        extra_fields_data = [
            {
                'id': '1',
                'name': 'Alice',
                'email': 'alice@test.com',
                'phone': '123-456-7890',
                'extra_field1': 'extra_value1',
                'extra_field2': 42,
                'extra_field3': {'nested': 'data'}
            }
        ]
        
        result = self.processor.process_raw_data(extra_fields_data, 'test_source')
        
        # Extra fields should be preserved
        assert len(result) == 1
        assert result.iloc[0]['extra_field1'] == 'extra_value1'
        assert result.iloc[0]['extra_field2'] == 42
        assert isinstance(result.iloc[0]['extra_field3'], str)  # Nested data serialized


class TestSampleDataGeneratorAdvanced:
    """Advanced tests for SampleDataGenerator to improve coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = SampleDataGenerator()
    
    def test_generate_customer_data_with_zero_count(self):
        """Test generating zero customer records."""
        result = self.generator.generate_customer_data(0)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_generate_customer_data_with_negative_count(self):
        """Test generating negative number of customer records."""
        with pytest.raises(ValueError, match="Count must be non-negative"):
            self.generator.generate_customer_data(-1)
    
    def test_generate_customer_data_with_large_count(self):
        """Test generating large number of customer records."""
        result = self.generator.generate_customer_data(1000)
        
        assert len(result) == 1000
        assert all(isinstance(record, dict) for record in result)
        assert all('id' in record for record in result)
        assert all('name' in record for record in result)
        assert all('email' in record for record in result)
    
    def test_generate_customer_data_uniqueness(self):
        """Test that generated customer data has unique IDs."""
        result = self.generator.generate_customer_data(100)
        
        ids = [record['id'] for record in result]
        assert len(set(ids)) == len(ids)  # All IDs should be unique
    
    def test_generate_customer_data_with_custom_seed(self):
        """Test generating data with custom seed for reproducibility."""
        # Generate data with same seed twice
        result1 = self.generator.generate_customer_data(10, seed=42)
        result2 = self.generator.generate_customer_data(10, seed=42)
        
        # Should be identical
        assert result1 == result2
        
        # Generate with different seed
        result3 = self.generator.generate_customer_data(10, seed=123)
        assert result1 != result3
    
    def test_generate_customer_data_with_custom_parameters(self):
        """Test generating data with custom parameters."""
        custom_params = {
            'name_prefix': 'TestUser',
            'email_domain': 'custom.com',
            'phone_prefix': '999'
        }
        
        result = self.generator.generate_customer_data(5, **custom_params)
        
        assert len(result) == 5
        assert all(record['name'].startswith('TestUser') for record in result)
        assert all('custom.com' in record['email'] for record in result)
        assert all(record['phone'].startswith('999') for record in result)
    
    def test_generate_customer_data_field_validation(self):
        """Test that generated data has valid field formats."""
        result = self.generator.generate_customer_data(10)
        
        for record in result:
            # Check email format
            assert '@' in record['email']
            assert '.' in record['email'].split('@')[1]
            
            # Check phone format (basic validation)
            assert len(record['phone']) >= 10
            
            # Check name is not empty
            assert len(record['name']) > 0
            
            # Check ID is not empty
            assert len(record['id']) > 0
    
    def test_generate_customer_data_with_optional_fields(self):
        """Test generating data with optional fields."""
        result = self.generator.generate_customer_data(5, include_optional=True)
        
        assert len(result) == 5
        # Check that some records have optional fields
        optional_fields = ['address', 'city', 'country', 'age']
        has_optional = any(
            any(field in record for field in optional_fields)
            for record in result
        )
        assert has_optional
    
    def test_generate_customer_data_without_optional_fields(self):
        """Test generating data without optional fields."""
        result = self.generator.generate_customer_data(5, include_optional=False)
        
        assert len(result) == 5
        # Check that no records have optional fields
        optional_fields = ['address', 'city', 'country', 'age']
        for record in result:
            for field in optional_fields:
                assert field not in record
    
    def test_generate_customer_data_with_custom_field_values(self):
        """Test generating data with custom field values."""
        custom_values = {
            'status': 'active',
            'region': 'US'
        }
        
        result = self.generator.generate_customer_data(5, custom_fields=custom_values)
        
        assert len(result) == 5
        for record in result:
            assert record['status'] == 'active'
            assert record['region'] == 'US'
    
    def test_generate_customer_data_with_invalid_parameters(self):
        """Test generating data with invalid parameters."""
        # Test with invalid count type
        with pytest.raises(TypeError):
            self.generator.generate_customer_data('invalid')
        
        # Test with invalid seed type
        with pytest.raises(TypeError):
            self.generator.generate_customer_data(5, seed='invalid')
    
    def test_generate_customer_data_performance(self):
        """Test performance of data generation."""
        import time
        
        start_time = time.time()
        result = self.generator.generate_customer_data(1000)
        end_time = time.time()
        
        # Should generate 1000 records in reasonable time (< 1 second)
        assert end_time - start_time < 1.0
        assert len(result) == 1000
    
    def test_generate_customer_data_with_special_characters(self):
        """Test generating data with special characters in names."""
        result = self.generator.generate_customer_data(10, include_special_chars=True)
        
        # Check that some names contain special characters
        has_special_chars = any(
            any(char in record['name'] for char in ['-', "'", '.', ' '])
            for record in result
        )
        assert has_special_chars
    
    def test_generate_customer_data_with_different_locales(self):
        """Test generating data with different locale settings."""
        result = self.generator.generate_customer_data(10, locale='en_US')
        
        assert len(result) == 10
        # All names should be in English format
        for record in result:
            assert isinstance(record['name'], str)
            assert len(record['name']) > 0
