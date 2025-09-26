"""
Bronze layer data processing pipeline.
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from utils.common.logging import get_logger, log_performance
from utils.common.exceptions import DataProcessingError
from utils.common.validation import DataValidator, validate_not_empty, validate_date


class BronzeLayerProcessor:
    """Bronze layer data processor."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize bronze layer processor.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        self.validator = DataValidator()
        self._setup_validation_rules()

    def _setup_validation_rules(self):
        """Set up validation rules for bronze layer data."""
        # Add common validation rules
        self.validator.add_rule("id", validate_not_empty)
        self.validator.add_rule("timestamp", validate_date)
        self.validator.add_rule("source", validate_not_empty)

    @log_performance(get_logger(__name__))
    def process_raw_data(self, data: List[Dict[str, Any]], source: str) -> pd.DataFrame:
        """
        Process raw data into bronze layer format.

        Args:
            data: Raw data to process
            source: Data source identifier

        Returns:
            Processed DataFrame
        """
        try:
            self.logger.info(f"Processing {len(data)} records from source: {source}")

            # Validate data
            validation_errors = []
            for i, record in enumerate(data):
                errors = self.validator.validate(record)
                if errors:
                    validation_errors.extend([f"Record {i}: {error}" for error in errors.values()])

            if validation_errors:
                self.logger.warning(f"Validation errors found: {validation_errors}")

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Add bronze layer metadata
            df = self._add_bronze_metadata(df, source)

            # Data quality checks
            quality_metrics = self._calculate_quality_metrics(df)
            self.logger.info(f"Data quality metrics: {quality_metrics}")

            return df

        except Exception as e:
            raise DataProcessingError(
                f"Failed to process raw data from {source}: {str(e)}",
                stage="bronze_layer",
                data_source=source
            )

    def _add_bronze_metadata(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """
        Add bronze layer metadata to DataFrame.

        Args:
            df: Input DataFrame
            source: Data source identifier

        Returns:
            DataFrame with bronze layer metadata
        """
        # Add processing metadata
        df['_bronze_ingestion_timestamp'] = datetime.utcnow()
        df['_bronze_source'] = source
        df['_bronze_batch_id'] = self._generate_batch_id()
        df['_bronze_record_count'] = len(df)

        return df

    def _generate_batch_id(self) -> str:
        """Generate unique batch ID."""
        return f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    def _calculate_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate data quality metrics.

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary of quality metrics
        """
        metrics = {
            "total_records": len(df),
            "total_columns": len(df.columns),
            "null_counts": df.isnull().sum().to_dict(),
            "duplicate_count": df.duplicated().sum(),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024
        }

        # Calculate completeness percentage
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        metrics["completeness_percentage"] = ((total_cells - null_cells) / total_cells) * 100

        return metrics

    def save_bronze_data(self, df: pd.DataFrame, table_name: str, output_path: str) -> str:
        """
        Save bronze layer data to storage.

        Args:
            df: DataFrame to save
            table_name: Name of the table
            output_path: Output path for the data

        Returns:
            Path where data was saved
        """
        try:
            output_path = Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)

            # Save as Parquet for efficient storage
            file_path = output_path / f"{table_name}_bronze.parquet"
            df.to_parquet(file_path, index=False)

            self.logger.info(f"Saved bronze data to: {file_path}")
            return str(file_path)

        except Exception as e:
            raise DataProcessingError(
                f"Failed to save bronze data: {str(e)}",
                stage="bronze_save",
                data_source=table_name
            )

    def load_bronze_data(self, file_path: str) -> pd.DataFrame:
        """
        Load bronze layer data from storage.

        Args:
            file_path: Path to the bronze data file

        Returns:
            Loaded DataFrame
        """
        try:
            df = pd.read_parquet(file_path)
            self.logger.info(f"Loaded bronze data from: {file_path}")
            return df

        except Exception as e:
            raise DataProcessingError(
                f"Failed to load bronze data: {str(e)}",
                stage="bronze_load",
                data_source=file_path
            )


class SampleDataGenerator:
    """Generate sample data for testing."""

    @staticmethod
    def generate_customer_data(count: int = 1000) -> List[Dict[str, Any]]:
        """
        Generate sample customer data.

        Args:
            count: Number of records to generate

        Returns:
            List of customer records
        """
        import random
        from datetime import datetime, timedelta

        data = []
        for i in range(count):
            record = {
                "id": f"cust_{i:06d}",
                "name": f"Customer {i}",
                "email": f"customer{i}@example.com",
                "phone": f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                "address": f"{random.randint(1, 9999)} Main St, City {i % 100}",
                "registration_date": (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
                "status": random.choice(["active", "inactive", "pending"]),
                "source": "sample_generator"
            }
            data.append(record)

        return data

    @staticmethod
    def generate_transaction_data(count: int = 5000) -> List[Dict[str, Any]]:
        """
        Generate sample transaction data.

        Args:
            count: Number of records to generate

        Returns:
            List of transaction records
        """
        import random
        from datetime import datetime, timedelta

        data = []
        for i in range(count):
            record = {
                "id": f"txn_{i:08d}",
                "customer_id": f"cust_{random.randint(0, 999):06d}",
                "amount": round(random.uniform(10.0, 1000.0), 2),
                "currency": random.choice(["USD", "EUR", "GBP"]),
                "transaction_date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S"),
                "category": random.choice(["food", "transport", "entertainment", "shopping", "utilities"]),
                "status": random.choice(["completed", "pending", "failed"]),
                "source": "sample_generator"
            }
            data.append(record)

        return data


def main():
    """Main function for bronze layer processing."""
    logger = get_logger(__name__)
    logger.info("Starting bronze layer processing")

    # Initialize processor
    processor = BronzeLayerProcessor()

    # Generate sample data
    sample_generator = SampleDataGenerator()

    # Process customer data
    logger.info("Processing customer data")
    customer_data = sample_generator.generate_customer_data(1000)
    customer_df = processor.process_raw_data(customer_data, "customer_api")

    # Save customer data
    customer_path = processor.save_bronze_data(
        customer_df,
        "customers",
        "data/bronze/customers"
    )

    # Process transaction data
    logger.info("Processing transaction data")
    transaction_data = sample_generator.generate_transaction_data(5000)
    transaction_df = processor.process_raw_data(transaction_data, "transaction_api")

    # Save transaction data
    transaction_path = processor.save_bronze_data(
        transaction_df,
        "transactions",
        "data/bronze/transactions"
    )

    logger.info(f"Bronze layer processing completed. Files saved to:")
    logger.info(f"  - Customers: {customer_path}")
    logger.info(f"  - Transactions: {transaction_path}")


if __name__ == "__main__":
    main()
