"""Gold Layer Data Processing.

This module implements the gold layer of the medallion architecture,
focusing on business logic, aggregations, and report-ready data preparation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from utils.common.exceptions import DataProcessingError


class AggregationLevel(Enum):
    """Aggregation levels for gold layer processing."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BusinessMetricType(Enum):
    """Types of business metrics."""

    REVENUE = "revenue"
    CUSTOMER_COUNT = "customer_count"
    CONVERSION_RATE = "conversion_rate"
    RETENTION_RATE = "retention_rate"
    CHURN_RATE = "churn_rate"
    AVERAGE_ORDER_VALUE = "average_order_value"
    CUSTOMER_LIFETIME_VALUE = "customer_lifetime_value"


@dataclass
class BusinessMetric:
    """Business metric definition."""

    metric_type: BusinessMetricType
    value: float
    aggregation_level: AggregationLevel
    dimension: Optional[str] = None
    dimension_value: Optional[str] = None
    calculation_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GoldLayerMetadata:
    """Metadata for gold layer processing."""

    processing_timestamp: datetime
    source_tables: List[str]
    aggregation_level: AggregationLevel
    business_metrics: List[BusinessMetric]
    record_count: int
    processing_version: str
    quality_score: float


class BusinessMetricsProcessor:
    """Handles business metric calculations for gold layer."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the business metrics processor.

        Args:
            config: Configuration dictionary for metric calculations
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Business rules for metric calculations
        self.business_rules = {
            "revenue_columns": ["amount", "price", "total", "revenue"],
            "customer_id_columns": ["customer_id", "user_id", "id"],
            "date_columns": [
                "created_at",
                "updated_at",
                "transaction_date",
                "order_date",
            ],
            "status_columns": ["status", "order_status", "payment_status"],
        }

        # Update with custom rules
        self.business_rules.update(self.config.get("business_rules", {}))

    def calculate_business_metrics(
        self, df: pd.DataFrame, table_name: str
    ) -> List[BusinessMetric]:
        """Calculate business metrics from silver layer data.

        Args:
            df: Silver layer dataframe
            table_name: Name of the source table

        Returns:
            List of calculated business metrics
        """
        try:
            self.logger.info(f"Calculating business metrics for {table_name}")

            metrics = []

            # Calculate different types of metrics
            metrics.extend(self._calculate_revenue_metrics(df, table_name))
            metrics.extend(self._calculate_customer_metrics(df, table_name))
            metrics.extend(self._calculate_conversion_metrics(df, table_name))
            metrics.extend(self._calculate_retention_metrics(df, table_name))
            metrics.extend(self._calculate_churn_metrics(df, table_name))

            self.logger.info(
                f"Calculated {len(metrics)} business metrics for {table_name}"
            )
            return metrics

        except Exception as e:
            self.logger.error(
                "Business metrics calculation failed for %s: %s", table_name, str(e)
            )
            raise DataProcessingError(
                "Business metrics calculation failed: %s" % str(e)
            )

    def _calculate_revenue_metrics(
        self, df: pd.DataFrame, table_name: str
    ) -> List[BusinessMetric]:
        """Calculate revenue-related metrics."""
        metrics = []

        # Find revenue column
        revenue_column = self._find_column(df, self.business_rules["revenue_columns"])

        if revenue_column:
            # Total revenue
            total_revenue = df[revenue_column].sum()
            metrics.append(
                BusinessMetric(
                    metric_type=BusinessMetricType.REVENUE,
                    value=total_revenue,
                    aggregation_level=AggregationLevel.DAILY,
                    calculation_date=datetime.now(timezone.utc),
                    metadata={"column": revenue_column, "table": table_name},
                )
            )

            # Average order value
            avg_order_value = df[revenue_column].mean()
            metrics.append(
                BusinessMetric(
                    metric_type=BusinessMetricType.AVERAGE_ORDER_VALUE,
                    value=avg_order_value,
                    aggregation_level=AggregationLevel.DAILY,
                    calculation_date=datetime.now(timezone.utc),
                    metadata={"column": revenue_column, "table": table_name},
                )
            )

        return metrics

    def _calculate_customer_metrics(
        self, df: pd.DataFrame, table_name: str
    ) -> List[BusinessMetric]:
        """Calculate customer-related metrics."""
        metrics = []

        # Find customer ID column
        customer_id_column = self._find_column(
            df, self.business_rules["customer_id_columns"]
        )

        if customer_id_column:
            # Total customer count
            unique_customers = df[customer_id_column].nunique()
            metrics.append(
                BusinessMetric(
                    metric_type=BusinessMetricType.CUSTOMER_COUNT,
                    value=unique_customers,
                    aggregation_level=AggregationLevel.DAILY,
                    calculation_date=datetime.now(timezone.utc),
                    metadata={"column": customer_id_column, "table": table_name},
                )
            )

            # Customer lifetime value (if revenue data available)
            revenue_column = self._find_column(
                df, self.business_rules["revenue_columns"]
            )
            if revenue_column:
                customer_revenue = df.groupby(customer_id_column)[revenue_column].sum()
                avg_clv = customer_revenue.mean()
                metrics.append(
                    BusinessMetric(
                        metric_type=BusinessMetricType.CUSTOMER_LIFETIME_VALUE,
                        value=avg_clv,
                        aggregation_level=AggregationLevel.DAILY,
                        calculation_date=datetime.now(timezone.utc),
                        metadata={"column": revenue_column, "table": table_name},
                    )
                )

        return metrics

    def _calculate_conversion_metrics(
        self, df: pd.DataFrame, table_name: str
    ) -> List[BusinessMetric]:
        """Calculate conversion-related metrics."""
        metrics = []

        # Find status column
        status_column = self._find_column(df, self.business_rules["status_columns"])

        if status_column:
            # Calculate conversion rate based on status
            total_records = len(df)
            successful_records = df[
                df[status_column].isin(["completed", "success", "active", "A"])
            ].shape[0]

            if total_records > 0:
                conversion_rate = (successful_records / total_records) * 100
                metrics.append(
                    BusinessMetric(
                        metric_type=BusinessMetricType.CONVERSION_RATE,
                        value=conversion_rate,
                        aggregation_level=AggregationLevel.DAILY,
                        calculation_date=datetime.now(timezone.utc),
                        metadata={"column": status_column, "table": table_name},
                    )
                )

        return metrics

    def _calculate_retention_metrics(
        self, df: pd.DataFrame, table_name: str
    ) -> List[BusinessMetric]:
        """Calculate retention-related metrics."""
        metrics = []

        # Find date and customer ID columns
        date_column = self._find_column(df, self.business_rules["date_columns"])
        customer_id_column = self._find_column(
            df, self.business_rules["customer_id_columns"]
        )

        if date_column and customer_id_column:
            try:
                # Convert date column to datetime
                df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

                # Calculate retention rate (simplified)
                # This is a basic implementation - in practice, you'd need historical
                # data
                current_date = datetime.now(timezone.utc)
                thirty_days_ago = current_date - timedelta(days=30)

                recent_customers = df[df[date_column] >= thirty_days_ago][
                    customer_id_column
                ].nunique()
                total_customers = df[customer_id_column].nunique()

                if total_customers > 0:
                    retention_rate = (recent_customers / total_customers) * 100
                    metrics.append(
                        BusinessMetric(
                            metric_type=BusinessMetricType.RETENTION_RATE,
                            value=retention_rate,
                            aggregation_level=AggregationLevel.DAILY,
                            calculation_date=datetime.now(timezone.utc),
                            metadata={"column": date_column, "table": table_name},
                        )
                    )
            except Exception as e:
                self.logger.warning(f"Failed to calculate retention metrics: {str(e)}")

        return metrics

    def _calculate_churn_metrics(
        self, df: pd.DataFrame, table_name: str
    ) -> List[BusinessMetric]:
        """Calculate churn-related metrics."""
        metrics = []

        # Find date and customer ID columns
        date_column = self._find_column(df, self.business_rules["date_columns"])
        customer_id_column = self._find_column(
            df, self.business_rules["customer_id_columns"]
        )

        if date_column and customer_id_column:
            try:
                # Convert date column to datetime
                df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

                # Calculate churn rate (simplified)
                current_date = datetime.now(timezone.utc)
                thirty_days_ago = current_date - timedelta(days=30)

                active_customers = df[df[date_column] >= thirty_days_ago][
                    customer_id_column
                ].nunique()
                total_customers = df[customer_id_column].nunique()

                if total_customers > 0:
                    churn_rate = (
                        (total_customers - active_customers) / total_customers
                    ) * 100
                    metrics.append(
                        BusinessMetric(
                            metric_type=BusinessMetricType.CHURN_RATE,
                            value=churn_rate,
                            aggregation_level=AggregationLevel.DAILY,
                            calculation_date=datetime.now(timezone.utc),
                            metadata={"column": date_column, "table": table_name},
                        )
                    )
            except Exception as e:
                self.logger.warning(f"Failed to calculate churn metrics: {str(e)}")

        return metrics

    def _find_column(
        self, df: pd.DataFrame, possible_names: List[str]
    ) -> Optional[str]:
        """Find a column by trying multiple possible names."""
        for name in possible_names:
            if name in df.columns:
                return name
        return None


class AggregationProcessor:
    """Handles data aggregation operations for gold layer."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the aggregation processor.

        Args:
            config: Configuration dictionary for aggregation rules
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    def aggregate_data(
        self,
        df: pd.DataFrame,
        aggregation_level: AggregationLevel,
        group_by_columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Aggregate data based on specified level and grouping.

        Args:
            df: Input dataframe to aggregate
            aggregation_level: Level of aggregation (daily, weekly, etc.)
            group_by_columns: Columns to group by

        Returns:
            Aggregated dataframe
        """
        try:
            self.logger.info(
                f"Starting data aggregation at {aggregation_level.value} level"
            )

            # Find date column for time-based aggregation
            date_column = self._find_date_column(df)

            if date_column is None:
                self.logger.warning(
                    "No date column found, performing simple aggregation"
                )
                return self._simple_aggregation(df, group_by_columns)

            # Convert date column to datetime
            df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

            # Create time-based grouping
            time_group = self._create_time_group(df[date_column], aggregation_level)
            df["time_group"] = time_group

            # Prepare grouping columns
            group_columns = ["time_group"]
            if group_by_columns:
                group_columns.extend(group_by_columns)

            # Perform aggregation
            aggregated_df = self._perform_aggregation(df, group_columns)

            self.logger.info(
                f"Data aggregation completed: {len(df)} -> {len(aggregated_df)} records"
            )
            return aggregated_df

        except Exception as e:
            self.logger.error("Data aggregation failed: %s", str(e))
            raise DataProcessingError("Data aggregation failed: %s" % str(e))

    def _find_date_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the primary date column in the dataframe."""
        date_columns = [
            "created_at",
            "updated_at",
            "transaction_date",
            "order_date",
            "date",
        ]

        for column in date_columns:
            if column in df.columns:
                return column

        # Look for columns with 'date' in the name
        for column in df.columns:
            if "date" in column.lower():
                return column

        return None

    def _create_time_group(
        self, date_series: pd.Series, aggregation_level: AggregationLevel
    ) -> pd.Series:
        """Create time-based grouping for aggregation."""
        if aggregation_level == AggregationLevel.DAILY:
            result = date_series.dt.date
        elif aggregation_level == AggregationLevel.WEEKLY:
            result = date_series.dt.to_period("W").dt.start_time.dt.date
        elif aggregation_level == AggregationLevel.MONTHLY:
            result = date_series.dt.to_period("M").dt.start_time.dt.date
        elif aggregation_level == AggregationLevel.QUARTERLY:
            result = date_series.dt.to_period("Q").dt.start_time.dt.date
        else:  # AggregationLevel.YEARLY
            result = date_series.dt.to_period("Y").dt.start_time.dt.date

        # Convert to Series with proper typing
        return pd.Series(result, index=date_series.index, dtype="object")

    def _simple_aggregation(
        self, df: pd.DataFrame, group_by_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Perform simple aggregation without time grouping."""
        if group_by_columns is None:
            group_by_columns = []

        # If no grouping columns, return summary statistics
        if not group_by_columns:
            return self._create_summary_statistics(df)

        # Group by specified columns
        grouped = df.groupby(group_by_columns)

        # Define aggregation functions
        agg_functions = {}

        # Numeric columns - sum, mean, count
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            agg_functions[col] = ["sum", "mean", "count"]

        # Categorical columns - mode, count
        categorical_columns = df.select_dtypes(include=["object"]).columns
        for col in categorical_columns:
            if col not in group_by_columns:
                agg_functions[col] = ["count"]

        # Perform aggregation
        aggregated = grouped.agg(agg_functions)  # type: ignore[arg-type]

        # Flatten column names
        aggregated.columns = ["_".join(col).strip() for col in aggregated.columns]
        aggregated = aggregated.reset_index()

        return aggregated

    def _perform_aggregation(
        self, df: pd.DataFrame, group_columns: List[str]
    ) -> pd.DataFrame:
        """Perform the actual aggregation."""
        grouped = df.groupby(group_columns)

        # Define aggregation functions
        agg_functions = {}

        # Numeric columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col not in group_columns:
                agg_functions[col] = ["sum", "mean", "count", "min", "max"]

        # Categorical columns
        categorical_columns = df.select_dtypes(include=["object"]).columns
        for col in categorical_columns:
            if col not in group_columns:
                agg_functions[col] = ["count", "nunique"]

        # Perform aggregation
        aggregated = grouped.agg(agg_functions)  # type: ignore[arg-type]

        # Flatten column names
        aggregated.columns = ["_".join(col).strip() for col in aggregated.columns]
        aggregated = aggregated.reset_index()

        return aggregated

    def _create_summary_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create summary statistics for the entire dataset."""
        summary = {
            "total_records": len(df),
            "processing_timestamp": datetime.now(timezone.utc),
        }

        # Add numeric column statistics
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            summary[f"{col}_sum"] = df[col].sum()
            summary[f"{col}_mean"] = df[col].mean()
            summary[f"{col}_min"] = df[col].min()
            summary[f"{col}_max"] = df[col].max()
            summary[f"{col}_std"] = df[col].std()

        # Add categorical column statistics
        categorical_columns = df.select_dtypes(include=["object"]).columns
        for col in categorical_columns:
            summary[f"{col}_unique_count"] = df[col].nunique()
            summary[f"{col}_most_common"] = (
                df[col].mode().iloc[0] if not df[col].mode().empty else None
            )

        return pd.DataFrame([summary])


class MLFeatureProcessor:
    """Handles ML feature engineering for gold layer."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the ML feature processor.

        Args:
            config: Configuration dictionary for feature engineering
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    def create_ml_features(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Create ML-ready features from silver layer data.

        Args:
            df: Silver layer dataframe
            table_name: Name of the source table

        Returns:
            Dataframe with ML features
        """
        try:
            self.logger.info(f"Creating ML features for {table_name}")

            features_df = df.copy()

            # Create different types of features
            features_df = self._create_numeric_features(features_df)
            features_df = self._create_categorical_features(features_df)
            features_df = self._create_temporal_features(features_df)
            features_df = self._create_interaction_features(features_df)
            features_df = self._create_aggregated_features(features_df)

            self.logger.info(
                f"Created {len(features_df.columns)} features for {table_name}"
            )
            return features_df

        except Exception as e:
            self.logger.error(
                "ML feature creation failed for %s: %s", table_name, str(e)
            )
            raise DataProcessingError("ML feature creation failed: %s" % str(e))

    def _create_numeric_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create numeric features from existing numeric columns."""
        features_df = df.copy()
        new_features = {}

        numeric_columns = df.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            # Log transformation
            if (df[col] > 0).all():
                new_features[f"{col}_log"] = np.log1p(df[col])

            # Square transformation
            new_features[f"{col}_squared"] = df[col] ** 2

            # Square root transformation
            if (df[col] >= 0).all():
                new_features[f"{col}_sqrt"] = np.sqrt(df[col])

            # Binning
            new_features[f"{col}_binned"] = pd.cut(df[col], bins=5, labels=False)

        # Add all new features at once to avoid fragmentation
        if new_features:
            new_features_df = pd.DataFrame(new_features, index=df.index)
            features_df = pd.concat([features_df, new_features_df], axis=1)

        return features_df

    def _create_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create categorical features from existing categorical columns."""
        features_df = df.copy()

        categorical_columns = df.select_dtypes(include=["object"]).columns

        for col in categorical_columns:
            # One-hot encoding for low cardinality columns
            if df[col].nunique() <= 10:
                dummies = pd.get_dummies(df[col], prefix=col)
                features_df = pd.concat([features_df, dummies], axis=1)

            # Frequency encoding
            freq_map = df[col].value_counts().to_dict()
            features_df[f"{col}_freq"] = df[col].map(freq_map)

            # Target encoding (simplified - would need target variable in practice)
            # For now, just create a placeholder
            features_df[f"{col}_encoded"] = pd.Categorical(df[col]).codes

        return features_df

    def _create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create temporal features from date columns."""
        features_df = df.copy()

        date_columns = ["created_at", "updated_at", "registration_date", "last_login"]

        for col in date_columns:
            if col in df.columns:
                try:
                    dates = pd.to_datetime(df[col], errors="coerce")

                    # Basic temporal features
                    features_df[f"{col}_year"] = dates.dt.year
                    features_df[f"{col}_month"] = dates.dt.month
                    features_df[f"{col}_day"] = dates.dt.day
                    features_df[f"{col}_weekday"] = dates.dt.weekday
                    features_df[f"{col}_hour"] = dates.dt.hour

                    # Cyclical features
                    features_df[f"{col}_month_sin"] = np.sin(
                        2 * np.pi * dates.dt.month / 12
                    )
                    features_df[f"{col}_month_cos"] = np.cos(
                        2 * np.pi * dates.dt.month / 12
                    )
                    features_df[f"{col}_day_sin"] = np.sin(
                        2 * np.pi * dates.dt.day / 31
                    )
                    features_df[f"{col}_day_cos"] = np.cos(
                        2 * np.pi * dates.dt.day / 31
                    )

                    # Time since features
                    now = pd.Timestamp.now(tz="UTC")
                    # Ensure dates are timezone-aware
                    if dates.dt.tz is None:
                        dates = dates.dt.tz_localize("UTC")
                    else:
                        dates = dates.dt.tz_convert("UTC")
                    # Calculate time differences using pandas operations
                    time_diff = now - dates
                    features_df[f"{col}_days_since"] = time_diff.dt.days
                    features_df[f"{col}_hours_since"] = (
                        time_diff.dt.total_seconds() / 3600
                    )

                except Exception as e:
                    self.logger.warning(
                        f"Failed to create temporal features for {col}: {str(e)}"
                    )

        return features_df

    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features between columns."""
        features_df = df.copy()

        # Create interaction features between numeric columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns

        if len(numeric_columns) >= 2:
            # Multiply first two numeric columns
            col1, col2 = numeric_columns[0], numeric_columns[1]
            features_df[f"{col1}_x_{col2}"] = df[col1] * df[col2]

            # Ratio of first two numeric columns
            if (df[col2] != 0).all():
                features_df[f"{col1}_div_{col2}"] = df[col1] / df[col2]

        return features_df

    def _create_aggregated_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create aggregated features."""
        features_df = df.copy()

        # Find customer ID column for customer-level aggregations
        customer_id_columns = ["customer_id", "user_id", "id"]
        customer_id_col = None

        for col in customer_id_columns:
            if col in df.columns:
                customer_id_col = col
                break

        if customer_id_col:
            # Customer-level aggregations
            customer_stats = df.groupby(customer_id_col).agg(
                {
                    col: ["count", "sum", "mean", "std"]
                    for col in df.select_dtypes(include=[np.number]).columns
                }
            )

            # Flatten column names
            customer_stats.columns = [
                "_".join(col).strip() for col in customer_stats.columns
            ]
            customer_stats = customer_stats.reset_index()

            # Merge back to original dataframe
            features_df = features_df.merge(
                customer_stats,
                on=customer_id_col,
                how="left",
                suffixes=("", "_customer"),
            )

        return features_df


class ReportingProcessor:
    """Handles report-ready data preparation for gold layer."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the reporting processor.

        Args:
            config: Configuration dictionary for reporting rules
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    def prepare_reporting_data(
        self, df: pd.DataFrame, report_type: str
    ) -> pd.DataFrame:
        """Prepare data for specific report types.

        Args:
            df: Input dataframe
            report_type: Type of report to prepare

        Returns:
            Report-ready dataframe
        """
        try:
            self.logger.info(f"Preparing {report_type} reporting data")

            if report_type == "executive_summary":
                return self._prepare_executive_summary(df)
            elif report_type == "customer_analytics":
                return self._prepare_customer_analytics(df)
            elif report_type == "financial_report":
                return self._prepare_financial_report(df)
            elif report_type == "operational_metrics":
                return self._prepare_operational_metrics(df)
            else:
                self.logger.warning(f"Unknown report type: {report_type}")
                return df

        except Exception as e:
            self.logger.error(
                "Report preparation failed for %s: %s", report_type, str(e)
            )
            raise DataProcessingError("Report preparation failed: %s" % str(e))

    def _prepare_executive_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare executive summary report data."""
        summary_data = {
            "total_records": len(df),
            "processing_date": datetime.now(timezone.utc),
            "data_quality_score": self._calculate_overall_quality_score(df),
        }

        # Add key metrics
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            summary_data[f"{col}_total"] = df[col].sum()
            summary_data[f"{col}_average"] = df[col].mean()

        return pd.DataFrame([summary_data])

    def _prepare_customer_analytics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare customer analytics report data."""
        # Find customer ID column
        customer_id_columns = ["customer_id", "user_id", "id"]
        customer_id_col = None

        for col in customer_id_columns:
            if col in df.columns:
                customer_id_col = col
                break

        if customer_id_col:
            # Customer-level aggregations
            customer_analytics = df.groupby(customer_id_col).agg(
                {
                    col: ["count", "sum", "mean"]
                    for col in df.select_dtypes(include=[np.number]).columns
                }
            )

            # Flatten column names
            customer_analytics.columns = [
                "_".join(col).strip() for col in customer_analytics.columns
            ]
            customer_analytics = customer_analytics.reset_index()

            return customer_analytics
        else:
            return df

    def _prepare_financial_report(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare financial report data."""
        # Find financial columns
        financial_columns = ["amount", "price", "total", "revenue", "cost", "profit"]
        available_financial_cols = [
            col for col in financial_columns if col in df.columns
        ]

        if available_financial_cols:
            financial_data = df[available_financial_cols].describe()
            financial_data["metric"] = financial_data.index
            financial_data = financial_data.reset_index(drop=True)

            return financial_data
        else:
            return df

    def _prepare_operational_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare operational metrics report data."""
        operational_data = {
            "total_records": len(df),
            "unique_customers": (
                df["customer_id"].nunique() if "customer_id" in df.columns else 0
            ),
            "processing_timestamp": datetime.now(timezone.utc),
            "data_completeness": (
                1 - df.isnull().sum().sum() / (len(df) * len(df.columns))
            )
            * 100,
        }

        return pd.DataFrame([operational_data])

    def _calculate_overall_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate overall data quality score."""
        if len(df) == 0:
            return 0.0

        # Simple quality score based on completeness
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        completeness = (
            (total_cells - null_cells) / total_cells if total_cells > 0 else 0
        )

        return round(completeness * 100, 2)


class GoldLayerProcessor:
    """Main processor for gold layer data transformation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the gold layer processor.

        Args:
            config: Configuration dictionary for processing rules
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize sub-processors
        self.metrics_processor = BusinessMetricsProcessor(
            self.config.get("metrics", {})
        )
        self.aggregation_processor = AggregationProcessor(
            self.config.get("aggregation", {})
        )
        self.feature_processor = MLFeatureProcessor(self.config.get("features", {}))
        self.reporting_processor = ReportingProcessor(self.config.get("reporting", {}))

    def process_silver_to_gold(
        self,
        silver_data: Dict[str, pd.DataFrame],
        aggregation_level: AggregationLevel = AggregationLevel.DAILY,
    ) -> Dict[str, Any]:
        """Process silver layer data to gold layer.

        Args:
            silver_data: Dictionary of silver layer dataframes
            aggregation_level: Level of aggregation to perform

        Returns:
            Dictionary containing processed gold data and metadata
        """
        try:
            self.logger.info(
                f"Starting gold layer processing with "
                f"{aggregation_level.value} aggregation"
            )

            gold_results = {}
            all_metrics = []
            source_tables = list(silver_data.keys())

            for table_name, df in silver_data.items():
                self.logger.info(f"Processing table: {table_name}")

                # Step 1: Calculate business metrics
                business_metrics = self.metrics_processor.calculate_business_metrics(
                    df, table_name
                )
                all_metrics.extend(business_metrics)

                # Step 2: Aggregate data
                aggregated_df = self.aggregation_processor.aggregate_data(
                    df, aggregation_level
                )

                # Step 3: Create ML features
                features_df = self.feature_processor.create_ml_features(
                    aggregated_df, table_name
                )

                # Step 4: Prepare reporting data
                reporting_data = {}
                for report_type in [
                    "executive_summary",
                    "customer_analytics",
                    "financial_report",
                    "operational_metrics",
                ]:
                    try:
                        reporting_data[report_type] = (
                            self.reporting_processor.prepare_reporting_data(
                                features_df, report_type
                            )
                        )
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to prepare {report_type} for {table_name}: "
                            f"{str(e)}"
                        )
                        reporting_data[report_type] = pd.DataFrame()

                # Store results
                gold_results[table_name] = {
                    "aggregated_data": aggregated_df,
                    "ml_features": features_df,
                    "reporting_data": reporting_data,
                    "business_metrics": business_metrics,
                    "processing_metadata": {
                        "table_name": table_name,
                        "aggregation_level": aggregation_level.value,
                        "processing_timestamp": datetime.now(timezone.utc),
                        "record_count": len(features_df),
                        "feature_count": len(features_df.columns),
                    },
                }

            # Create overall metadata
            total_records = 0
            for result in gold_results.values():
                if isinstance(result, dict):
                    processing_metadata = result.get("processing_metadata", {})
                    if isinstance(processing_metadata, dict):
                        total_records += processing_metadata.get("record_count", 0)
            overall_quality_score = self._calculate_overall_quality_score(silver_data)

            metadata = GoldLayerMetadata(
                processing_timestamp=datetime.now(timezone.utc),
                source_tables=source_tables,
                aggregation_level=aggregation_level,
                business_metrics=all_metrics,
                record_count=total_records,
                processing_version="1.0",
                quality_score=overall_quality_score,
            )

            result = {
                "gold_data": gold_results,
                "metadata": metadata,
                "summary": {
                    "tables_processed": len(source_tables),
                    "total_records": total_records,
                    "total_metrics": len(all_metrics),
                    "aggregation_level": aggregation_level.value,
                    "processing_time": datetime.now(timezone.utc),
                },
            }

            self.logger.info(
                f"Gold layer processing completed: {len(source_tables)} tables, "
                f"{total_records} records"
            )
            return result

        except Exception as e:
            self.logger.error("Gold layer processing failed: %s", str(e))
            raise DataProcessingError("Gold layer processing failed: %s" % str(e))

    def _calculate_overall_quality_score(
        self, silver_data: Dict[str, pd.DataFrame]
    ) -> float:
        """Calculate overall quality score across all silver data."""
        if not silver_data:
            return 0.0

        total_records = sum(len(df) for df in silver_data.values())
        if total_records == 0:
            return 0.0

        weighted_quality = 0.0

        for table_name, df in silver_data.items():
            if len(df) > 0:
                # Simple quality score based on completeness
                total_cells = len(df) * len(df.columns)
                null_cells = df.isnull().sum().sum()
                completeness = (
                    (total_cells - null_cells) / total_cells if total_cells > 0 else 0
                )

                # Weight by record count
                weight = len(df) / total_records
                weighted_quality += completeness * weight * 100

        return round(weighted_quality, 2)
