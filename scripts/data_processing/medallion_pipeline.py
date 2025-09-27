"""
Complete Medallion Architecture Pipeline

This script demonstrates the complete medallion architecture implementation,
processing data through Bronze, Silver, and Gold layers.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from scripts.data_processing.bronze_layer import (
    BronzeLayerProcessor,
    SampleDataGenerator,
)
from scripts.data_processing.gold_layer import AggregationLevel, GoldLayerProcessor
from scripts.data_processing.silver_layer import SilverLayerProcessor
from utils.common.exceptions import DataProcessingError


class MedallionPipeline:
    """Complete medallion architecture pipeline implementation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the medallion pipeline.

        Args:
            config: Configuration dictionary for the pipeline
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize processors
        self.bronze_processor = BronzeLayerProcessor()
        self.silver_processor = SilverLayerProcessor(self.config.get("silver", {}))
        self.gold_processor = GoldLayerProcessor(self.config.get("gold", {}))
        self.data_generator = SampleDataGenerator()

        # Pipeline configuration
        self.pipeline_config = {
            "bronze_tables": ["customers", "orders", "products"],
            "aggregation_level": AggregationLevel.DAILY,
            "output_format": "parquet",
            "enable_quality_checks": True,
            "enable_ml_features": True,
            "enable_reporting": True,
        }

        # Update with custom config
        self.pipeline_config.update(self.config.get("pipeline", {}))

    def run_complete_pipeline(self, sample_data_size: int = 1000) -> Dict[str, Any]:
        """Run the complete medallion architecture pipeline.

        Args:
            sample_data_size: Number of sample records to generate

        Returns:
            Dictionary containing all pipeline results and metadata
        """
        try:
            self.logger.info("Starting complete medallion architecture pipeline")
            pipeline_start_time = datetime.now(timezone.utc)

            # Step 1: Generate sample data (Bronze Layer)
            self.logger.info("Step 1: Generating sample data (Bronze Layer)")
            bronze_data = self._generate_bronze_data(sample_data_size)

            # Step 2: Process Bronze to Silver
            self.logger.info("Step 2: Processing Bronze to Silver Layer")
            silver_results = self._process_bronze_to_silver(bronze_data)

            # Step 3: Process Silver to Gold
            self.logger.info("Step 3: Processing Silver to Gold Layer")
            gold_results = self._process_silver_to_gold(silver_results)

            # Step 4: Generate pipeline summary
            self.logger.info("Step 4: Generating pipeline summary")
            pipeline_summary = self._generate_pipeline_summary(
                bronze_data, silver_results, gold_results, pipeline_start_time
            )

            # Step 5: Save results (optional)
            if self.config.get("save_results", False):
                self.logger.info("Step 5: Saving pipeline results")
                self._save_pipeline_results(bronze_data, silver_results, gold_results)

            self.logger.info(
                "Complete medallion architecture pipeline finished successfully"
            )

            return {
                "bronze_data": bronze_data,
                "silver_results": silver_results,
                "gold_results": gold_results,
                "pipeline_summary": pipeline_summary,
                "status": "success",
                "processing_time": (
                    datetime.now(timezone.utc) - pipeline_start_time
                ).total_seconds(),
            }

        except Exception as e:
            self.logger.error("Pipeline failed: %s", str(e))
            raise DataProcessingError("Medallion pipeline failed: %s" % str(e))

    def _generate_bronze_data(self, sample_size: int) -> Dict[str, pd.DataFrame]:
        """Generate sample bronze layer data."""
        bronze_data = {}

        for table_name in self.pipeline_config["bronze_tables"]:
            self.logger.info(f"Generating {sample_size} records for {table_name}")

            if table_name == "customers":
                # Generate customer data
                customer_data = self.data_generator.generate_customer_data(sample_size)

                # Convert to DataFrame and add some business-specific fields
                df = pd.DataFrame(customer_data)
                df["customer_id"] = df["id"]
                df["registration_date"] = pd.date_range(
                    start="2023-01-01", periods=len(df), freq="1H"
                ).strftime("%Y-%m-%d %H:%M:%S")
                df["last_login"] = pd.date_range(
                    start="2024-01-01", periods=len(df), freq="2H"
                ).strftime("%Y-%m-%d %H:%M:%S")
                df["status"] = np.random.choice(
                    ["A", "I", "P"], len(df), p=[0.7, 0.2, 0.1]
                )
                df["loyalty_tier"] = np.random.choice(
                    ["Bronze", "Silver", "Gold", "Platinum"],
                    len(df),
                    p=[0.4, 0.3, 0.2, 0.1],
                )

                bronze_data[table_name] = df

            elif table_name == "orders":
                # Generate order data
                order_data = []
                for i in range(sample_size):
                    order_data.append(
                        {
                            "order_id": f"ORD_{i + 1:06d}",
                            "customer_id": f"CUST_{np.random.randint(1, sample_size // 2):06d}",
                            "product_id": f"PROD_{np.random.randint(1, 100):06d}",
                            "order_date": pd.Timestamp.now()
                            - pd.Timedelta(days=np.random.randint(0, 365)),
                            "amount": round(np.random.uniform(10, 1000), 2),
                            "quantity": np.random.randint(1, 10),
                            "status": np.random.choice(
                                ["completed", "pending", "cancelled"],
                                p=[0.8, 0.15, 0.05],
                            ),
                            "payment_method": np.random.choice(
                                ["credit_card", "debit_card", "paypal", "cash"],
                                p=[0.4, 0.3, 0.2, 0.1],
                            ),
                            "shipping_address": (
                                f"{np.random.randint(100, 9999)} Main St, City, State "
                                f"{np.random.randint(10000, 99999)}"
                            ),
                        }
                    )

                bronze_data[table_name] = pd.DataFrame(order_data)

            elif table_name == "products":
                # Generate product data
                product_data = []
                categories = [
                    "Electronics",
                    "Clothing",
                    "Books",
                    "Home & Garden",
                    "Sports",
                    "Beauty",
                ]

                for i in range(100):  # 100 products
                    product_data.append(
                        {
                            "product_id": f"PROD_{i + 1:06d}",
                            "product_name": f"Product {i + 1}",
                            "category": np.random.choice(categories),
                            "price": round(np.random.uniform(5, 500), 2),
                            "cost": round(np.random.uniform(2, 250), 2),
                            "inventory_count": np.random.randint(0, 1000),
                            "supplier_id": f"SUPP_{np.random.randint(1, 20):03d}",
                            "created_date": pd.Timestamp.now()
                            - pd.Timedelta(days=np.random.randint(0, 1095)),
                            "is_active": np.random.choice([True, False], p=[0.9, 0.1]),
                        }
                    )

                bronze_data[table_name] = pd.DataFrame(product_data)

        self.logger.info(f"Generated bronze data for {len(bronze_data)} tables")
        return bronze_data

    def _process_bronze_to_silver(
        self, bronze_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Process bronze data to silver layer."""
        silver_results = {}

        for table_name, df in bronze_data.items():
            self.logger.info(f"Processing {table_name} from bronze to silver")

            try:
                # Process bronze to silver
                result = self.silver_processor.process_bronze_to_silver(df, table_name)
                silver_results[table_name] = result

                # Log quality improvement
                initial_quality = result["initial_quality"].overall_score
                final_quality = result["final_quality"].overall_score
                improvement = final_quality - initial_quality

                self.logger.info(
                    f"{table_name} quality: {initial_quality:.1f}% -> {final_quality:.1f}% "
                    f"(+{improvement:.1f}%)"
                )

            except Exception as e:
                self.logger.error("Failed to process %s: %s", table_name, str(e))
                silver_results[table_name] = {
                    "error": str(e),
                    "silver_data": pd.DataFrame(),
                    "processing_metadata": {"status": "failed"},
                }

        return silver_results

    def _process_silver_to_gold(self, silver_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process silver data to gold layer."""
        # Extract silver data
        silver_data = {}
        for table_name, result in silver_results.items():
            if "silver_data" in result and not result["silver_data"].empty:
                silver_data[table_name] = result["silver_data"]

        if not silver_data:
            self.logger.warning("No valid silver data to process")
            return {}

        self.logger.info(f"Processing {len(silver_data)} tables from silver to gold")

        # Process silver to gold
        gold_results = self.gold_processor.process_silver_to_gold(
            silver_data, self.pipeline_config["aggregation_level"]
        )

        return gold_results

    def _generate_pipeline_summary(
        self,
        bronze_data: Dict[str, pd.DataFrame],
        silver_results: Dict[str, Any],
        gold_results: Dict[str, Any],
        start_time: datetime,
    ) -> Dict[str, Any]:
        """Generate comprehensive pipeline summary."""
        processing_time = datetime.now(timezone.utc) - start_time

        # Bronze layer summary
        bronze_summary = {
            "tables_processed": len(bronze_data),
            "total_records": sum(len(df) for df in bronze_data.values()),
            "tables": {name: len(df) for name, df in bronze_data.items()},
        }

        # Silver layer summary
        silver_summary = {
            "tables_processed": len(silver_results),
            "successful_tables": sum(
                1 for result in silver_results.values() if "error" not in result
            ),
            "failed_tables": sum(
                1 for result in silver_results.values() if "error" in result
            ),
            "quality_improvements": {},
        }

        for table_name, result in silver_results.items():
            if "initial_quality" in result and "final_quality" in result:
                initial = result["initial_quality"].overall_score
                final = result["final_quality"].overall_score
                silver_summary["quality_improvements"][table_name] = {
                    "initial": initial,
                    "final": final,
                    "improvement": final - initial,
                }

        # Gold layer summary
        gold_summary = {
            "tables_processed": len(gold_results.get("gold_data", {})),
            "total_records": gold_results.get("summary", {}).get("total_records", 0),
            "total_metrics": gold_results.get("summary", {}).get("total_metrics", 0),
            "aggregation_level": gold_results.get("summary", {}).get(
                "aggregation_level", "unknown"
            ),
        }

        # Overall pipeline summary
        pipeline_summary = {
            "pipeline_status": "success",
            "processing_time_seconds": processing_time.total_seconds(),
            "processing_time_formatted": str(processing_time),
            "bronze_layer": bronze_summary,
            "silver_layer": silver_summary,
            "gold_layer": gold_summary,
            "data_quality_overview": self._generate_quality_overview(silver_results),
            "business_metrics_summary": self._generate_business_metrics_summary(
                gold_results
            ),
            "pipeline_configuration": self.pipeline_config,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return pipeline_summary

    def _generate_quality_overview(
        self, silver_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate data quality overview."""
        quality_overview = {
            "overall_quality_score": 0.0,
            "quality_distribution": {"excellent": 0, "good": 0, "fair": 0, "poor": 0},
            "table_quality_scores": {},
        }

        total_score = 0
        table_count = 0

        for table_name, result in silver_results.items():
            if "final_quality" in result:
                quality = result["final_quality"]
                score = quality.overall_score
                level = quality.quality_level.value

                quality_overview["table_quality_scores"][table_name] = {
                    "score": score,
                    "level": level,
                    "completeness": quality.completeness,
                    "accuracy": quality.accuracy,
                    "consistency": quality.consistency,
                    "validity": quality.validity,
                    "uniqueness": quality.uniqueness,
                }

                quality_overview["quality_distribution"][level] += 1
                total_score += score
                table_count += 1

        if table_count > 0:
            quality_overview["overall_quality_score"] = round(
                total_score / table_count, 2
            )

        return quality_overview

    def _generate_business_metrics_summary(
        self, gold_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate business metrics summary."""
        if "metadata" not in gold_results:
            return {}

        metadata = gold_results["metadata"]
        metrics = metadata.business_metrics

        metrics_summary = {
            "total_metrics": len(metrics),
            "metrics_by_type": {},
            "top_metrics": [],
        }

        # Group metrics by type
        for metric in metrics:
            metric_type = metric.metric_type.value
            if metric_type not in metrics_summary["metrics_by_type"]:
                metrics_summary["metrics_by_type"][metric_type] = []
            metrics_summary["metrics_by_type"][metric_type].append(metric.value)

        # Calculate averages for each metric type
        for metric_type, values in metrics_summary["metrics_by_type"].items():
            metrics_summary["metrics_by_type"][metric_type] = {
                "count": len(values),
                "average": round(sum(values) / len(values), 2),
                "total": round(sum(values), 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
            }

        # Get top metrics by value
        sorted_metrics = sorted(metrics, key=lambda x: x.value, reverse=True)
        metrics_summary["top_metrics"] = [
            {
                "type": metric.metric_type.value,
                "value": metric.value,
                "dimension": metric.dimension,
                "calculation_date": (
                    metric.calculation_date.isoformat()
                    if metric.calculation_date
                    else None
                ),
            }
            for metric in sorted_metrics[:10]
        ]

        return metrics_summary

    def _save_pipeline_results(
        self,
        bronze_data: Dict[str, pd.DataFrame],
        silver_results: Dict[str, Any],
        gold_results: Dict[str, Any],
    ) -> None:
        """Save pipeline results to files."""
        output_dir = Path(self.config.get("output_directory", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # Save bronze data
        bronze_dir = output_dir / "bronze" / timestamp
        bronze_dir.mkdir(parents=True, exist_ok=True)

        for table_name, df in bronze_data.items():
            file_path = bronze_dir / f"{table_name}.parquet"
            df.to_parquet(file_path, index=False)
            self.logger.info(f"Saved bronze data: {file_path}")

        # Save silver data
        silver_dir = output_dir / "silver" / timestamp
        silver_dir.mkdir(parents=True, exist_ok=True)

        for table_name, result in silver_results.items():
            if "silver_data" in result and not result["silver_data"].empty:
                file_path = silver_dir / f"{table_name}.parquet"
                result["silver_data"].to_parquet(file_path, index=False)
                self.logger.info(f"Saved silver data: {file_path}")

        # Save gold data
        gold_dir = output_dir / "gold" / timestamp
        gold_dir.mkdir(parents=True, exist_ok=True)

        if "gold_data" in gold_results:
            for table_name, result in gold_results["gold_data"].items():
                table_dir = gold_dir / table_name
                table_dir.mkdir(exist_ok=True)

                # Save aggregated data
                if "aggregated_data" in result:
                    file_path = table_dir / "aggregated_data.parquet"
                    result["aggregated_data"].to_parquet(file_path, index=False)

                # Save ML features
                if "ml_features" in result:
                    file_path = table_dir / "ml_features.parquet"
                    result["ml_features"].to_parquet(file_path, index=False)

                # Save reporting data
                if "reporting_data" in result:
                    reporting_dir = table_dir / "reporting"
                    reporting_dir.mkdir(exist_ok=True)

                    for report_type, report_df in result["reporting_data"].items():
                        if not report_df.empty:
                            file_path = reporting_dir / f"{report_type}.parquet"
                            report_df.to_parquet(file_path, index=False)

        # Save pipeline summary
        summary_file = output_dir / f"pipeline_summary_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(
                gold_results.get("pipeline_summary", {}), f, indent=2, default=str
            )

        self.logger.info(f"Pipeline results saved to: {output_dir}")


def main():
    """Main function to run the medallion pipeline."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Pipeline configuration
    config = {
        "pipeline": {
            "bronze_tables": ["customers", "orders", "products"],
            "aggregation_level": AggregationLevel.DAILY,
            "enable_quality_checks": True,
            "enable_ml_features": True,
            "enable_reporting": True,
        },
        "silver": {
            "cleaning": {
                "cleaning_rules": {
                    "remove_duplicates": True,
                    "handle_missing_values": True,
                    "standardize_text": True,
                    "normalize_phone_numbers": True,
                    "validate_emails": True,
                }
            }
        },
        "gold": {
            "metrics": {
                "business_rules": {
                    "revenue_columns": ["amount", "price", "total"],
                    "customer_id_columns": ["customer_id", "user_id"],
                    "date_columns": ["created_at", "order_date", "registration_date"],
                }
            }
        },
        "save_results": True,
        "output_directory": "output/medallion_pipeline",
    }

    # Initialize and run pipeline
    pipeline = MedallionPipeline(config)

    try:
        results = pipeline.run_complete_pipeline(sample_data_size=1000)

        print("\n" + "=" * 80)
        print("🎉 MEDALLION ARCHITECTURE PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        # Print summary
        summary = results["pipeline_summary"]
        print("\n📊 PIPELINE SUMMARY:")
        print(f"   Processing Time: {summary['processing_time_formatted']}")
        print(f"   Bronze Tables: {summary['bronze_layer']['tables_processed']}")
        print(f"   Silver Tables: {summary['silver_layer']['tables_processed']}")
        print(f"   Gold Tables: {summary['gold_layer']['tables_processed']}")
        print(f"   Total Records: {summary['bronze_layer']['total_records']:,}")
        print(f"   Business Metrics: {summary['gold_layer']['total_metrics']}")

        # Print quality overview
        quality = summary["data_quality_overview"]
        print("\n📈 DATA QUALITY OVERVIEW:")
        print(f"   Overall Quality Score: {quality['overall_quality_score']:.1f}%")
        print("   Quality Distribution:")
        for level, count in quality["quality_distribution"].items():
            print(f"     {level.title()}: {count} tables")

        # Print business metrics
        metrics = summary["business_metrics_summary"]
        if metrics:
            print("\n💰 BUSINESS METRICS SUMMARY:")
            for metric_type, stats in metrics["metrics_by_type"].items():
                print(
                    f"   {metric_type.replace('_', ' ').title()}: {stats['average']:.2f} (avg)"
                )

        print(f"\n✅ All results saved to: {config['output_directory']}")
        print("=" * 80)

    except Exception as e:
        print("\n❌ Pipeline failed: %s" % str(e))
        raise


if __name__ == "__main__":
    main()
