"""
Integration tests for Databricks functionality with mocked services.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.utils.databricks.connection import DatabricksConnection, DatabricksConfig
from scripts.data_processing.bronze_layer import BronzeLayerProcessor, SampleDataGenerator
from src.utils.common.validation import SchemaValidator


class TestDatabricksIntegration:
    """Integration tests for Databricks components."""

    def test_databricks_connection_initialization(self) -> None:
        """Test Databricks connection initialization with mocked API."""
        config = DatabricksConfig(
            host='https://test.databricks.com',
            token='test-token'
        )
        
        with patch('requests.Session') as mock_session:
            mock_response = Mock()
            mock_response.json.return_value = {'clusters': []}
            mock_response.raise_for_status.return_value = None
            mock_session.return_value.get.return_value = mock_response
            
            conn = DatabricksConnection(config)
            assert conn.config.host == 'https://test.databricks.com'
            assert conn.config.token == 'test-token'

    def test_databricks_cluster_operations(self) -> None:
        """Test cluster operations with mocked Databricks API."""
        config = DatabricksConfig(
            host='https://test.databricks.com',
            token='test-token'
        )
        
        with patch('requests.Session') as mock_session:
            # Mock successful cluster list response
            mock_response = Mock()
            mock_response.json.return_value = {
                'clusters': [
                    {
                        'cluster_id': 'test-cluster-123',
                        'cluster_name': 'test-cluster',
                        'state': 'RUNNING'
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_session.return_value.get.return_value = mock_response
            
            conn = DatabricksConnection(config)
            clusters = conn.get_clusters()
            
            assert len(clusters) == 1
            assert clusters[0]['cluster_id'] == 'test-cluster-123'
            assert clusters[0]['state'] == 'RUNNING'

    def test_databricks_job_operations(self) -> None:
        """Test job operations with mocked Databricks API."""
        config = DatabricksConfig(
            host='https://test.databricks.com',
            token='test-token'
        )
        
        with patch('requests.Session') as mock_session:
            # Mock successful job list response
            mock_response = Mock()
            mock_response.json.return_value = {
                'jobs': [
                    {
                        'job_id': 123,
                        'settings': {
                            'name': 'test-job',
                            'existing_cluster_id': 'test-cluster-123'
                        }
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_session.return_value.get.return_value = mock_response
            
            conn = DatabricksConnection(config)
            jobs = conn.get_jobs()
            
            assert len(jobs) == 1
            assert jobs[0]['job_id'] == 123
            assert jobs[0]['settings']['name'] == 'test-job'

    def test_data_processing_pipeline_integration(self) -> None:
        """Test end-to-end data processing pipeline."""
        # Initialize components
        processor = BronzeLayerProcessor()
        generator = SampleDataGenerator()
        validator = SchemaValidator()
        
        # Define schema
        bronze_schema = {
            'type': 'object',
            'required': ['id', 'name', 'email', 'registration_date', 'status', 'source'],
            'properties': {
                'id': {'type': 'string'},
                'name': {'type': 'string'},
                'email': {'type': 'string'},
                'phone': {'type': 'string'},
                'registration_date': {'type': 'string'},
                'status': {'type': 'string'},
                'source': {'type': 'string'}
            }
        }
        
        validator.add_schema('bronze_customers', bronze_schema)
        
        # Generate sample data
        sample_data = generator.generate_customer_data(10)
        assert len(sample_data) == 10
        
        # Validate data against schema
        validation_result = validator.validate_data(sample_data, 'bronze_customers')
        assert validation_result['valid'] is True
        assert validation_result['validated_count'] == 10
        
        # Process data through bronze layer
        processed_df = processor.process_raw_data(sample_data, 'test_source')
        assert len(processed_df) == 10
        
        # Check that bronze layer metadata was added
        assert '_bronze_ingestion_timestamp' in processed_df.columns
        assert '_bronze_source' in processed_df.columns
        assert all(processed_df['_bronze_source'] == 'test_source')

    def test_schema_validation_integration(self) -> None:
        """Test schema validation across different data layers."""
        validator = SchemaValidator()
        
        # Define schemas for different layers
        bronze_schema = {
            'type': 'object',
            'required': ['id', 'name', 'email', 'source'],
            'properties': {
                'id': {'type': 'string'},
                'name': {'type': 'string'},
                'email': {'type': 'string'},
                'source': {'type': 'string'}
            }
        }
        
        silver_schema = {
            'type': 'object',
            'required': ['customer_id', 'customer_name', 'email_domain', 'data_quality_score'],
            'properties': {
                'customer_id': {'type': 'string'},
                'customer_name': {'type': 'string'},
                'email_domain': {'type': 'string'},
                'data_quality_score': {'type': 'number'}
            }
        }
        
        gold_schema = {
            'type': 'object',
            'required': ['customer_id', 'customer_segment', 'lifetime_value'],
            'properties': {
                'customer_id': {'type': 'string'},
                'customer_segment': {'type': 'string'},
                'lifetime_value': {'type': 'number'}
            }
        }
        
        # Add schemas
        validator.add_schema('bronze_customers', bronze_schema)
        validator.add_schema('silver_customers', silver_schema)
        validator.add_schema('gold_customers', gold_schema)
        
        # Test bronze layer data
        bronze_data = [
            {
                'id': 'cust_001',
                'name': 'John Doe',
                'email': 'john@example.com',
                'source': 'api'
            }
        ]
        
        bronze_result = validator.validate_data(bronze_data, 'bronze_customers')
        assert bronze_result['valid'] is True
        
        # Test silver layer data
        silver_data = [
            {
                'customer_id': 'cust_001',
                'customer_name': 'John Doe',
                'email_domain': 'example.com',
                'data_quality_score': 0.95
            }
        ]
        
        silver_result = validator.validate_data(silver_data, 'silver_customers')
        assert silver_result['valid'] is True
        
        # Test gold layer data
        gold_data = [
            {
                'customer_id': 'cust_001',
                'customer_segment': 'premium',
                'lifetime_value': 1500.0
            }
        ]
        
        gold_result = validator.validate_data(gold_data, 'gold_customers')
        assert gold_result['valid'] is True

    def test_error_handling_integration(self) -> None:
        """Test error handling across the pipeline."""
        # Test invalid schema validation
        validator = SchemaValidator()
        invalid_schema = {
            'type': 'object',
            'required': ['id', 'name'],
            'properties': {
                'id': {'type': 'string'},
                'name': {'type': 'string'}
            }
        }
        
        validator.add_schema('test_schema', invalid_schema)
        
        # Data missing required field
        invalid_data = [
            {
                'id': 'test_001'
                # Missing 'name' field
            }
        ]
        
        result = validator.validate_data(invalid_data, 'test_schema')
        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_performance_integration(self) -> None:
        """Test performance characteristics of the pipeline."""
        processor = BronzeLayerProcessor()
        generator = SampleDataGenerator()
        
        # Generate larger dataset
        large_dataset = generator.generate_customer_data(1000)
        
        # Process and measure time
        import time
        start_time = time.time()
        processed_df = processor.process_raw_data(large_dataset, 'performance_test')
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should process 1000 records in reasonable time (< 5 seconds)
        assert processing_time < 5.0
        assert len(processed_df) == 1000


@pytest.fixture
def mock_databricks_config() -> Dict[str, Any]:
    """Fixture providing mock Databricks configuration."""
    return {
        'host': 'https://test.databricks.com',
        'token': 'test-token',
        'workspace_id': 'test-workspace'
    }


@pytest.fixture
def sample_customer_data() -> list:
    """Fixture providing sample customer data."""
    generator = SampleDataGenerator()
    return generator.generate_customer_data(5)


def test_integration_with_fixtures(mock_databricks_config: Dict[str, Any], sample_customer_data: list) -> None:
    """Test integration using pytest fixtures."""
    # Test configuration
    assert mock_databricks_config['host'] == 'https://test.databricks.com'
    assert mock_databricks_config['token'] == 'test-token'
    
    # Test sample data
    assert len(sample_customer_data) == 5
    assert all('id' in record for record in sample_customer_data)
    assert all('name' in record for record in sample_customer_data)
    
    # Test processing with fixtures
    processor = BronzeLayerProcessor()
    processed_df = processor.process_raw_data(sample_customer_data, 'fixture_test')
    
    assert len(processed_df) == 5
    assert '_bronze_ingestion_timestamp' in processed_df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
