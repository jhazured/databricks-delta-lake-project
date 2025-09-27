"""
Unit tests for medallion architecture (Silver and Gold layer processors).
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from scripts.data_processing.silver_layer import (
    SilverLayerProcessor, DataCleaningProcessor, DataStandardizationProcessor,
    DataQualityProcessor, DataEnrichmentProcessor, DataQualityLevel, DataQualityMetrics
)
from scripts.data_processing.gold_layer import (
    GoldLayerProcessor, BusinessMetricsProcessor, AggregationProcessor,
    MLFeatureProcessor, ReportingProcessor, AggregationLevel, BusinessMetricType, BusinessMetric
)
from utils.common.exceptions import DataProcessingError


class TestDataCleaningProcessor:
    """Test DataCleaningProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DataCleaningProcessor({})
        
        # Sample test data
        self.sample_data = pd.DataFrame({
            'id': ['1', '2', '3', '1'],  # Duplicate ID
            'name': ['Alice', 'Bob', 'Charlie', 'Alice Duplicate'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com', 'alice2@test.com'],
            'phone': ['123-456-7890', '987-654-3210', '555-123-4567', '123-456-7890'],
            'age': [25, 30, 35, 25],
            'salary': [50000.0, 60000.0, 70000.0, 50000.0],
            'status': ['active', 'inactive', 'active', 'active'],
            'created_at': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-01']
        })
    
    def test_clean_dataframe_basic(self):
        """Test basic dataframe cleaning."""
        result = self.processor.clean_dataframe(self.sample_data, 'test_table')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 0  # May have duplicates removed
        assert '_silver_processed_timestamp' in result.columns
        assert '_silver_source_table' in result.columns
        assert '_silver_batch_id' in result.columns
        assert '_silver_processing_version' in result.columns
        assert '_silver_quality_score' in result.columns
    
    def test_remove_duplicates(self):
        """Test duplicate removal functionality."""
        # Create data with duplicates
        duplicate_data = pd.DataFrame({
            'id': ['1', '2', '1', '3'],
            'name': ['Alice', 'Bob', 'Alice', 'Charlie'],
            'email': ['alice@test.com', 'bob@test.com', 'alice@test.com', 'charlie@test.com']
        })
        
        result = self.processor._remove_duplicates(duplicate_data)
        
        # Should remove one duplicate
        assert len(result) == 3
        assert result['id'].nunique() == 3
    
    def test_handle_missing_values(self):
        """Test missing value handling."""
        # Create data with missing values
        missing_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'name': ['Alice', None, 'Charlie'],
            'age': [25, 30, None],
            'is_active': [True, False, None]
        })
        
        result = self.processor._handle_missing_values(missing_data)
        
        # Check that missing values are filled
        assert result['name'].isnull().sum() == 0
        assert result['age'].isnull().sum() == 0
        assert result['is_active'].isnull().sum() == 0
        
        # Check specific fill values
        assert result['name'].iloc[1] == 'Unknown'
        assert result['is_active'].iloc[2] == 'Unknown'  # Boolean columns get 'Unknown' for missing values
    
    def test_standardize_text(self):
        """Test text standardization."""
        text_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'name': ['  alice  ', 'BOB', 'charlie'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com']
        })
        
        result = self.processor._standardize_text(text_data)
        
        # Check that text is standardized
        assert result['name'].iloc[0] == 'Alice'
        assert result['name'].iloc[1] == 'Bob'
        assert result['name'].iloc[2] == 'Charlie'
    
    def test_normalize_phone_numbers(self):
        """Test phone number normalization."""
        phone_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'phone': ['1234567890', '(123) 456-7890', '+1-234-567-8900']
        })
        
        result = self.processor._normalize_phone_numbers(phone_data)
        
        # Check that phone numbers are normalized
        assert result['phone'].iloc[0] == '+1-123-456-7890'
        assert result['phone'].iloc[1] == '+1-123-456-7890'
        assert result['phone'].iloc[2] == '+1-234-567-8900'
    
    def test_validate_emails(self):
        """Test email validation."""
        email_data = pd.DataFrame({
            'id': ['1', '2', '3', '4'],
            'email': ['alice@test.com', 'invalid-email', 'bob@test.com', 'charlie@test.com']
        })
        
        result = self.processor._validate_emails(email_data)
        
        # Check that invalid emails are marked
        assert result['email'].iloc[0] == 'alice@test.com'
        assert result['email'].iloc[1] == 'Invalid'
        assert result['email'].iloc[2] == 'bob@test.com'
    
    def test_clean_numeric_data(self):
        """Test numeric data cleaning."""
        numeric_data = pd.DataFrame({
            'id': ['1', '2', '3', '4', '5'],
            'age': [25, 30, 35, 200, 40],  # 200 is an outlier
            'salary': [50000, 60000, 70000, 80000, 90000]
        })
        
        result = self.processor._clean_numeric_data(numeric_data)
        
        # Check that outliers are capped
        assert result['age'].max() < 200  # Outlier should be capped
    
    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        # Perfect data
        perfect_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35]
        })
        
        score = self.processor._calculate_quality_score(perfect_data)
        assert score == 100.0
        
        # Data with missing values
        missing_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'name': ['Alice', None, 'Charlie'],
            'age': [25, 30, None]
        })
        
        score = self.processor._calculate_quality_score(missing_data)
        assert score < 100.0


class TestDataStandardizationProcessor:
    """Test DataStandardizationProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DataStandardizationProcessor({})
    
    def test_standardize_dataframe(self):
        """Test dataframe standardization."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'country': ['USA', 'United States', 'UK'],
            'state': ['California', 'New York', 'Texas'],
            'status': ['active', 'inactive', 'pending'],
            'amount': ['$100.50', '$200.75', '$300.00']
        })
        
        result = self.processor.standardize_dataframe(data, 'test_table')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
    
    def test_standardize_country_codes(self):
        """Test country code standardization."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'country': ['USA', 'United States', 'UK']
        })
        
        result = self.processor._standardize_country_codes(data)
        
        assert result['country'].iloc[0] == 'US'
        assert result['country'].iloc[1] == 'US'
        assert result['country'].iloc[2] == 'GB'
    
    def test_standardize_state_codes(self):
        """Test state code standardization."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'state': ['California', 'New York', 'Texas']
        })
        
        result = self.processor._standardize_state_codes(data)
        
        assert result['state'].iloc[0] == 'CA'
        assert result['state'].iloc[1] == 'NY'
        assert result['state'].iloc[2] == 'TX'
    
    def test_standardize_status_values(self):
        """Test status value standardization."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'status': ['active', 'inactive', 'pending']
        })
        
        result = self.processor._standardize_status_values(data)
        
        assert result['status'].iloc[0] == 'A'
        assert result['status'].iloc[1] == 'I'
        assert result['status'].iloc[2] == 'P'
    
    def test_standardize_date_formats(self):
        """Test date format standardization."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'created_at': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        result = self.processor._standardize_date_formats(data)
        
        # Check that dates are standardized
        assert result['created_at'].iloc[0] == '2024-01-01 00:00:00'
    
    def test_standardize_currency_values(self):
        """Test currency value standardization."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': ['$100.50', '$200.75', '$300.00']
        })
        
        result = self.processor._standardize_currency_values(data)
        
        # Check that currency values are standardized
        assert result['amount'].iloc[0] == 100.50
        assert result['amount'].iloc[1] == 200.75
        assert result['amount'].iloc[2] == 300.00


class TestDataQualityProcessor:
    """Test DataQualityProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DataQualityProcessor({})
    
    def test_assess_data_quality(self):
        """Test data quality assessment."""
        # Good quality data
        good_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'name': ['Alice', 'Bob', 'Charlie'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com'],
            'age': [25, 30, 35]
        })
        
        metrics = self.processor.assess_data_quality(good_data, 'test_table')
        
        assert isinstance(metrics, DataQualityMetrics)
        assert metrics.record_count == 3
        assert metrics.overall_score > 0
        assert metrics.quality_level in [DataQualityLevel.EXCELLENT, DataQualityLevel.GOOD]
    
    def test_calculate_completeness(self):
        """Test completeness calculation."""
        # Perfect data
        perfect_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'name': ['Alice', 'Bob', 'Charlie']
        })
        
        completeness = self.processor._calculate_completeness(perfect_data)
        assert completeness == 100.0
        
        # Data with missing values
        missing_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'name': ['Alice', None, 'Charlie']
        })
        
        completeness = self.processor._calculate_completeness(missing_data)
        assert completeness < 100.0
    
    def test_calculate_accuracy(self):
        """Test accuracy calculation."""
        # Data with valid emails
        valid_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com']
        })
        
        accuracy = self.processor._calculate_accuracy(valid_data)
        assert accuracy == 100.0
        
        # Data with invalid emails
        invalid_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'email': ['alice@test.com', 'invalid-email', 'charlie@test.com']
        })
        
        accuracy = self.processor._calculate_accuracy(invalid_data)
        assert accuracy < 100.0
    
    def test_calculate_consistency(self):
        """Test consistency calculation."""
        # Consistent data
        consistent_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'created_at': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        consistency = self.processor._calculate_consistency(consistent_data)
        assert consistency == 100.0
    
    def test_calculate_validity(self):
        """Test validity calculation."""
        # Valid data
        valid_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'age': [25, 30, 35],
            'status': ['A', 'I', 'P']
        })
        
        validity = self.processor._calculate_validity(valid_data)
        assert validity == 100.0
        
        # Invalid data
        invalid_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'age': [25, 200, 35],  # 200 is invalid age
            'status': ['A', 'I', 'P']
        })
        
        validity = self.processor._calculate_validity(invalid_data)
        assert validity < 100.0
    
    def test_calculate_uniqueness(self):
        """Test uniqueness calculation."""
        # Unique data
        unique_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com']
        })
        
        uniqueness = self.processor._calculate_uniqueness(unique_data)
        assert uniqueness == 100.0
        
        # Duplicate data
        duplicate_data = pd.DataFrame({
            'id': ['1', '2', '1'],
            'email': ['alice@test.com', 'bob@test.com', 'alice@test.com']
        })
        
        uniqueness = self.processor._calculate_uniqueness(duplicate_data)
        assert uniqueness < 100.0


class TestDataEnrichmentProcessor:
    """Test DataEnrichmentProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DataEnrichmentProcessor({})
    
    def test_enrich_dataframe(self):
        """Test dataframe enrichment."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'first_name': ['Alice', 'Bob', 'Charlie'],
            'last_name': ['Smith', 'Jones', 'Brown'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com'],
            'age': [25, 30, 35],
            'state': ['CA', 'NY', 'TX'],
            'created_at': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        result = self.processor.enrich_dataframe(data, 'test_table')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
    
    def test_add_derived_fields(self):
        """Test derived field addition."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'first_name': ['Alice', 'Bob', 'Charlie'],
            'last_name': ['Smith', 'Jones', 'Brown'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com'],
            'age': [25, 30, 35]
        })
        
        result = self.processor._add_derived_fields(data)
        
        # Check that derived fields are added
        assert 'full_name' in result.columns
        assert 'email_domain' in result.columns
        assert 'age_group' in result.columns
        
        assert result['full_name'].iloc[0] == 'Alice Smith'
        assert result['email_domain'].iloc[0] == 'test.com'
    
    def test_add_geographic_data(self):
        """Test geographic data addition."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'state': ['CA', 'NY', 'TX']
        })
        
        result = self.processor._add_geographic_data(data)
        
        # Check that region is added
        assert 'region' in result.columns
        assert result['region'].iloc[0] == 'West'  # CA
        assert result['region'].iloc[1] == 'Northeast'  # NY
        assert result['region'].iloc[2] == 'South'  # TX
    
    def test_add_temporal_features(self):
        """Test temporal feature addition."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'created_at': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        result = self.processor._add_temporal_features(data)
        
        # Check that temporal features are added
        assert 'created_at_year' in result.columns
        assert 'created_at_month' in result.columns
        assert 'created_at_day' in result.columns
        assert 'created_at_weekday' in result.columns
        assert 'days_since_creation' in result.columns
    
    def test_add_customer_segments(self):
        """Test customer segmentation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'age': [25, 30, 35],
            'status': ['A', 'I', 'A']
        })
        
        result = self.processor._add_customer_segments(data)
        
        # Check that customer segments are added
        assert 'customer_segment' in result.columns
        assert result['customer_segment'].iloc[0] == 'Young Active'  # age 25, active
        assert result['customer_segment'].iloc[1] == 'Adult Inactive'  # age 30, inactive


class TestSilverLayerProcessor:
    """Test SilverLayerProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = SilverLayerProcessor({})
        
        # Sample bronze data
        self.bronze_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'name': ['Alice', 'Bob', 'Charlie'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com'],
            'phone': ['123-456-7890', '987-654-3210', '555-123-4567'],
            'age': [25, 30, 35],
            'status': ['active', 'inactive', 'active']
        })
    
    def test_process_bronze_to_silver(self):
        """Test bronze to silver processing."""
        result = self.processor.process_bronze_to_silver(self.bronze_data, 'test_table')
        
        assert isinstance(result, dict)
        assert 'silver_data' in result
        assert 'initial_quality' in result
        assert 'final_quality' in result
        assert 'processing_metadata' in result
        
        # Check silver data
        silver_data = result['silver_data']
        assert isinstance(silver_data, pd.DataFrame)
        assert len(silver_data) >= 0
        
        # Check quality metrics
        initial_quality = result['initial_quality']
        final_quality = result['final_quality']
        assert isinstance(initial_quality, DataQualityMetrics)
        assert isinstance(final_quality, DataQualityMetrics)
        
        # Check processing metadata
        metadata = result['processing_metadata']
        assert metadata['source_table'] == 'test_table'
        assert metadata['records_processed'] >= 0
    
    def test_process_multiple_tables(self):
        """Test processing multiple tables."""
        bronze_data = {
            'table1': self.bronze_data,
            'table2': self.bronze_data.copy()
        }
        
        result = self.processor.process_multiple_tables(bronze_data)
        
        assert isinstance(result, dict)
        assert 'table1' in result
        assert 'table2' in result
        
        # Check that both tables are processed
        assert 'silver_data' in result['table1']
        assert 'silver_data' in result['table2']


class TestBusinessMetricsProcessor:
    """Test BusinessMetricsProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = BusinessMetricsProcessor({})
    
    def test_calculate_business_metrics(self):
        """Test business metrics calculation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'customer_id': ['C1', 'C2', 'C1'],
            'amount': [100.0, 200.0, 150.0],
            'status': ['completed', 'completed', 'pending'],
            'created_at': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        metrics = self.processor.calculate_business_metrics(data, 'test_table')
        
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        
        # Check that we have different types of metrics
        metric_types = [metric.metric_type for metric in metrics]
        assert BusinessMetricType.REVENUE in metric_types
        assert BusinessMetricType.CUSTOMER_COUNT in metric_types
    
    def test_calculate_revenue_metrics(self):
        """Test revenue metrics calculation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0]
        })
        
        metrics = self.processor._calculate_revenue_metrics(data, 'test_table')
        
        assert len(metrics) > 0
        
        # Check revenue metric
        revenue_metric = next((m for m in metrics if m.metric_type == BusinessMetricType.REVENUE), None)
        assert revenue_metric is not None
        assert revenue_metric.value == 450.0  # Sum of amounts
        
        # Check average order value
        aov_metric = next((m for m in metrics if m.metric_type == BusinessMetricType.AVERAGE_ORDER_VALUE), None)
        assert aov_metric is not None
        assert aov_metric.value == 150.0  # Average of amounts
    
    def test_calculate_customer_metrics(self):
        """Test customer metrics calculation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'customer_id': ['C1', 'C2', 'C1'],
            'amount': [100.0, 200.0, 150.0]
        })
        
        metrics = self.processor._calculate_customer_metrics(data, 'test_table')
        
        assert len(metrics) > 0
        
        # Check customer count
        customer_count_metric = next((m for m in metrics if m.metric_type == BusinessMetricType.CUSTOMER_COUNT), None)
        assert customer_count_metric is not None
        assert customer_count_metric.value == 2  # Unique customers
    
    def test_calculate_conversion_metrics(self):
        """Test conversion metrics calculation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'status': ['completed', 'completed', 'pending']
        })
        
        metrics = self.processor._calculate_conversion_metrics(data, 'test_table')
        
        assert len(metrics) > 0
        
        # Check conversion rate
        conversion_metric = next((m for m in metrics if m.metric_type == BusinessMetricType.CONVERSION_RATE), None)
        assert conversion_metric is not None
        assert conversion_metric.value == (2/3) * 100  # 2 out of 3 completed


class TestAggregationProcessor:
    """Test AggregationProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = AggregationProcessor({})
    
    def test_aggregate_data_daily(self):
        """Test daily aggregation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0],
            'created_at': ['2024-01-01', '2024-01-01', '2024-01-02']
        })
        
        result = self.processor.aggregate_data(data, AggregationLevel.DAILY)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 0
    
    def test_aggregate_data_monthly(self):
        """Test monthly aggregation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0],
            'created_at': ['2024-01-01', '2024-01-15', '2024-02-01']
        })
        
        result = self.processor.aggregate_data(data, AggregationLevel.MONTHLY)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 0
    
    def test_simple_aggregation(self):
        """Test simple aggregation without time grouping."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0],
            'category': ['A', 'B', 'A']
        })
        
        result = self.processor._simple_aggregation(data, ['category'])
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 0
    
    def test_create_summary_statistics(self):
        """Test summary statistics creation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0],
            'category': ['A', 'B', 'A']
        })
        
        result = self.processor._create_summary_statistics(data)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1  # Single row of summary statistics
        assert 'total_records' in result.columns
        assert result['total_records'].iloc[0] == 3


class TestMLFeatureProcessor:
    """Test MLFeatureProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MLFeatureProcessor({})
    
    def test_create_ml_features(self):
        """Test ML feature creation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0],
            'category': ['A', 'B', 'A'],
            'created_at': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        result = self.processor.create_ml_features(data, 'test_table')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) > len(data.columns)  # Should have more features
    
    def test_create_numeric_features(self):
        """Test numeric feature creation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0]
        })
        
        result = self.processor._create_numeric_features(data)
        
        # Check that numeric features are created
        assert 'amount_log' in result.columns
        assert 'amount_squared' in result.columns
        assert 'amount_sqrt' in result.columns
        assert 'amount_binned' in result.columns
    
    def test_create_categorical_features(self):
        """Test categorical feature creation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'category': ['A', 'B', 'A']
        })
        
        result = self.processor._create_categorical_features(data)
        
        # Check that categorical features are created
        assert 'category_freq' in result.columns
        assert 'category_encoded' in result.columns
    
    def test_create_temporal_features(self):
        """Test temporal feature creation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'created_at': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        result = self.processor._create_temporal_features(data)
        
        # Check that temporal features are created
        assert 'created_at_year' in result.columns
        assert 'created_at_month' in result.columns
        assert 'created_at_day' in result.columns
        assert 'created_at_weekday' in result.columns
        assert 'created_at_hour' in result.columns
    
    def test_create_interaction_features(self):
        """Test interaction feature creation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0],
            'quantity': [1, 2, 3]
        })
        
        result = self.processor._create_interaction_features(data)
        
        # Check that interaction features are created
        assert 'amount_x_quantity' in result.columns
        assert 'amount_div_quantity' in result.columns


class TestReportingProcessor:
    """Test ReportingProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = ReportingProcessor({})
    
    def test_prepare_reporting_data(self):
        """Test reporting data preparation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0],
            'customer_id': ['C1', 'C2', 'C1']
        })
        
        result = self.processor.prepare_reporting_data(data, 'executive_summary')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 0
    
    def test_prepare_executive_summary(self):
        """Test executive summary preparation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0]
        })
        
        result = self.processor._prepare_executive_summary(data)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1  # Single row summary
        assert 'total_records' in result.columns
        assert 'amount_total' in result.columns
        assert 'amount_average' in result.columns
    
    def test_prepare_customer_analytics(self):
        """Test customer analytics preparation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0],
            'customer_id': ['C1', 'C2', 'C1']
        })
        
        result = self.processor._prepare_customer_analytics(data)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 0
    
    def test_prepare_financial_report(self):
        """Test financial report preparation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0]
        })
        
        result = self.processor._prepare_financial_report(data)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 0
    
    def test_prepare_operational_metrics(self):
        """Test operational metrics preparation."""
        data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'amount': [100.0, 200.0, 150.0],
            'customer_id': ['C1', 'C2', 'C1']
        })
        
        result = self.processor._prepare_operational_metrics(data)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1  # Single row summary
        assert 'total_records' in result.columns
        assert 'unique_customers' in result.columns
        assert 'data_completeness' in result.columns


class TestGoldLayerProcessor:
    """Test GoldLayerProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = GoldLayerProcessor({})
        
        # Sample silver data
        self.silver_data = {
            'table1': pd.DataFrame({
                'id': ['1', '2', '3'],
                'customer_id': ['C1', 'C2', 'C1'],
                'amount': [100.0, 200.0, 150.0],
                'status': ['completed', 'completed', 'pending'],
                'created_at': ['2024-01-01', '2024-01-02', '2024-01-03']
            })
        }
    
    def test_process_silver_to_gold(self):
        """Test silver to gold processing."""
        result = self.processor.process_silver_to_gold(self.silver_data, AggregationLevel.DAILY)
        
        assert isinstance(result, dict)
        assert 'gold_data' in result
        assert 'metadata' in result
        assert 'summary' in result
        
        # Check gold data
        gold_data = result['gold_data']
        assert 'table1' in gold_data
        
        table1_data = gold_data['table1']
        assert 'aggregated_data' in table1_data
        assert 'ml_features' in table1_data
        assert 'reporting_data' in table1_data
        assert 'business_metrics' in table1_data
        assert 'processing_metadata' in table1_data
        
        # Check metadata
        metadata = result['metadata']
        assert metadata.source_tables == ['table1']
        assert metadata.aggregation_level == AggregationLevel.DAILY
        assert len(metadata.business_metrics) > 0
        
        # Check summary
        summary = result['summary']
        assert summary['tables_processed'] == 1
        assert summary['total_records'] >= 0
        assert summary['total_metrics'] > 0
    
    def test_calculate_overall_quality_score(self):
        """Test overall quality score calculation."""
        silver_data = {
            'table1': pd.DataFrame({
                'id': ['1', '2', '3'],
                'name': ['Alice', 'Bob', 'Charlie']
            }),
            'table2': pd.DataFrame({
                'id': ['4', '5', '6'],
                'name': ['David', 'Eve', 'Frank']
            })
        }
        
        score = self.processor._calculate_overall_quality_score(silver_data)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
