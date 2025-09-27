"""
Silver Layer Data Processing

This module implements the silver layer of the medallion architecture,
focusing on data cleaning, standardization, and quality improvement.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from utils.common.exceptions import DataProcessingError
from utils.common.validation import DataValidator, SchemaValidator


class DataQualityLevel(Enum):
    """Data quality levels for silver layer processing."""

    EXCELLENT = "excellent"  # 95-100%
    GOOD = "good"  # 85-94%
    FAIR = "fair"  # 70-84%
    POOR = "poor"  # <70%


@dataclass
class DataQualityMetrics:
    """Data quality metrics for silver layer processing."""

    completeness: float
    accuracy: float
    consistency: float
    validity: float
    uniqueness: float
    overall_score: float
    quality_level: DataQualityLevel
    record_count: int
    processed_count: int
    error_count: int


class DataCleaningProcessor:
    """Handles data cleaning operations for silver layer."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the data cleaning processor.

        Args:
            config: Configuration dictionary for cleaning rules
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Default cleaning rules
        self.cleaning_rules = {
            "remove_duplicates": True,
            "handle_missing_values": True,
            "standardize_text": True,
            "normalize_phone_numbers": True,
            "validate_emails": True,
            "clean_numeric_data": True,
            "remove_special_characters": False,
        }

        # Update with custom config
        self.cleaning_rules.update(self.config.get("cleaning_rules", {}))

    def clean_dataframe(self, df: pd.DataFrame, source_table: str) -> pd.DataFrame:
        """Clean a dataframe according to configured rules.

        Args:
            df: Input dataframe to clean
            source_table: Name of the source table for logging

        Returns:
            Cleaned dataframe

        Raises:
            DataProcessingError: If cleaning fails
        """
        try:
            self.logger.info(
                f"Starting data cleaning for {source_table} with {len(df)} records"
            )

            original_count = len(df)
            cleaned_df = df.copy()

            # Apply cleaning rules
            if self.cleaning_rules["remove_duplicates"]:
                cleaned_df = self._remove_duplicates(cleaned_df)

            if self.cleaning_rules["handle_missing_values"]:
                cleaned_df = self._handle_missing_values(cleaned_df)

            if self.cleaning_rules["standardize_text"]:
                cleaned_df = self._standardize_text(cleaned_df)

            if self.cleaning_rules["normalize_phone_numbers"]:
                cleaned_df = self._normalize_phone_numbers(cleaned_df)

            if self.cleaning_rules["validate_emails"]:
                cleaned_df = self._validate_emails(cleaned_df)

            if self.cleaning_rules["clean_numeric_data"]:
                cleaned_df = self._clean_numeric_data(cleaned_df)

            # Add silver layer metadata
            cleaned_df = self._add_silver_metadata(cleaned_df, source_table)

            final_count = len(cleaned_df)
            self.logger.info(
                f"Data cleaning completed: {original_count} -> {final_count} records"
            )

            return cleaned_df

        except Exception as e:
            self.logger.error("Data cleaning failed for %s: %s", source_table, str(e))
            raise DataProcessingError("Data cleaning failed: %s" % str(e))

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate records based on business keys."""
        # Define business keys for deduplication
        business_keys = ["id", "email", "phone"]
        available_keys = [key for key in business_keys if key in df.columns]

        if available_keys:
            # Keep first occurrence of duplicates
            df_cleaned = df.drop_duplicates(subset=available_keys, keep="first")
            removed_count = len(df) - len(df_cleaned)
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} duplicate records")
            return df_cleaned

        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values according to data type and business rules."""
        df_cleaned = df.copy()

        for column in df_cleaned.columns:
            if df_cleaned[column].dtype == "object":  # String columns
                # Fill missing strings with 'Unknown'
                df_cleaned[column] = df_cleaned[column].fillna("Unknown")
            elif df_cleaned[column].dtype in ["int64", "float64"]:  # Numeric columns
                # Fill missing numbers with median
                median_value = df_cleaned[column].median()
                df_cleaned[column] = df_cleaned[column].fillna(median_value)
            elif df_cleaned[column].dtype == "bool":  # Boolean columns
                # Fill missing booleans with False
                df_cleaned[column] = df_cleaned[column].fillna(False)
            elif (
                df_cleaned[column].dtype == "object"
                and df_cleaned[column].isin([True, False, None]).any()
            ):
                # Handle boolean-like object columns
                df_cleaned[column] = df_cleaned[column].fillna(False)

        return df_cleaned

    def _standardize_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize text data (trim whitespace, title case, etc.)."""
        df_cleaned = df.copy()

        text_columns = df_cleaned.select_dtypes(include=["object"]).columns

        for column in text_columns:
            if column not in ["id", "email", "phone"]:  # Skip ID fields
                # Trim whitespace and convert to title case
                df_cleaned[column] = (
                    df_cleaned[column].astype(str).str.strip().str.title()
                )

        return df_cleaned

    def _normalize_phone_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize phone numbers to standard format."""
        if "phone" not in df.columns:
            return df

        df_cleaned = df.copy()

        def normalize_phone(phone):
            if pd.isna(phone) or phone == "Unknown":
                return phone

            # Remove all non-digit characters
            digits = re.sub(r"\D", "", str(phone))

            # Format as +1-XXX-XXX-XXXX for US numbers
            if len(digits) == 10:
                return f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == "1":
                return f"+1-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
            else:
                return f"+{digits}"  # International format

        df_cleaned["phone"] = df_cleaned["phone"].apply(normalize_phone)
        return df_cleaned

    def _validate_emails(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean email addresses."""
        if "email" not in df.columns:
            return df

        df_cleaned = df.copy()

        def validate_email(email):
            if pd.isna(email) or email == "Unknown":
                return email

            email = str(email).strip().lower()

            # Basic email validation regex
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

            if re.match(email_pattern, email):
                return email
            else:
                return "Invalid"  # Mark invalid emails

        df_cleaned["email"] = df_cleaned["email"].apply(validate_email)
        return df_cleaned

    def _clean_numeric_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate numeric data."""
        df_cleaned = df.copy()

        numeric_columns = df_cleaned.select_dtypes(include=[np.number]).columns

        for column in numeric_columns:
            # Remove outliers using IQR method
            Q1 = df_cleaned[column].quantile(0.25)
            Q3 = df_cleaned[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            # Cap outliers instead of removing them
            df_cleaned[column] = df_cleaned[column].clip(
                lower=lower_bound, upper=upper_bound
            )

        return df_cleaned

    def _add_silver_metadata(self, df: pd.DataFrame, source_table: str) -> pd.DataFrame:
        """Add silver layer metadata columns."""
        df_cleaned = df.copy()

        # Add silver layer metadata
        df_cleaned["_silver_processed_timestamp"] = datetime.now(timezone.utc)
        df_cleaned["_silver_source_table"] = source_table
        df_cleaned["_silver_batch_id"] = self._generate_batch_id()
        df_cleaned["_silver_processing_version"] = "1.0"
        df_cleaned["_silver_quality_score"] = self._calculate_quality_score(df_cleaned)

        return df_cleaned

    def _generate_batch_id(self) -> str:
        """Generate a unique batch ID for silver processing."""
        return f"silver_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    def _calculate_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate a simple quality score for the dataframe."""
        if len(df) == 0:
            return 0.0

        # Calculate completeness score
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        completeness = (
            (total_cells - null_cells) / total_cells if total_cells > 0 else 0
        )

        # Simple quality score based on completeness
        return round(completeness * 100, 2)


class DataStandardizationProcessor:
    """Handles data standardization operations for silver layer."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the data standardization processor.

        Args:
            config: Configuration dictionary for standardization rules
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Standardization mappings
        self.standardization_mappings = {
            "country_codes": {
                "USA": "US",
                "United States": "US",
                "America": "US",
                "UK": "GB",
                "United Kingdom": "GB",
                "England": "GB",
                "Canada": "CA",
                "Australia": "AU",
            },
            "state_codes": {
                "California": "CA",
                "New York": "NY",
                "Texas": "TX",
                "Florida": "FL",
                "Illinois": "IL",
                "Pennsylvania": "PA",
            },
            "status_mapping": {
                "active": "A",
                "inactive": "I",
                "pending": "P",
                "suspended": "S",
                "cancelled": "C",
            },
        }

        # Update with custom mappings
        self.standardization_mappings.update(self.config.get("mappings", {}))

    def standardize_dataframe(
        self, df: pd.DataFrame, source_table: str
    ) -> pd.DataFrame:
        """Standardize a dataframe according to configured mappings.

        Args:
            df: Input dataframe to standardize
            source_table: Name of the source table for logging

        Returns:
            Standardized dataframe
        """
        try:
            self.logger.info(f"Starting data standardization for {source_table}")

            standardized_df = df.copy()

            # Apply standardization rules
            standardized_df = self._standardize_country_codes(standardized_df)
            standardized_df = self._standardize_state_codes(standardized_df)
            standardized_df = self._standardize_status_values(standardized_df)
            standardized_df = self._standardize_date_formats(standardized_df)
            standardized_df = self._standardize_currency_values(standardized_df)

            self.logger.info(f"Data standardization completed for {source_table}")
            return standardized_df

        except Exception as e:
            self.logger.error(
                "Data standardization failed for %s: %s", source_table, str(e)
            )
            raise DataProcessingError("Data standardization failed: %s" % str(e))

    def _standardize_country_codes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize country codes to ISO format."""
        if "country" not in df.columns:
            return df

        df_std = df.copy()
        country_mapping = self.standardization_mappings["country_codes"]

        df_std["country"] = df_std["country"].replace(country_mapping)
        return df_std

    def _standardize_state_codes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize state codes to 2-letter format."""
        if "state" not in df.columns:
            return df

        df_std = df.copy()
        state_mapping = self.standardization_mappings["state_codes"]

        df_std["state"] = df_std["state"].replace(state_mapping)
        return df_std

    def _standardize_status_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize status values to single character codes."""
        if "status" not in df.columns:
            return df

        df_std = df.copy()
        status_mapping = self.standardization_mappings["status_mapping"]

        df_std["status"] = df_std["status"].replace(status_mapping)
        return df_std

    def _standardize_date_formats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize date formats to ISO format."""
        date_columns = ["created_at", "updated_at", "registration_date", "last_login"]

        df_std = df.copy()

        for column in date_columns:
            if column in df_std.columns:
                try:
                    df_std[column] = pd.to_datetime(df_std[column], errors="coerce")
                    df_std[column] = df_std[column].dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    self.logger.warning(
                        f"Failed to standardize date column {column}: {str(e)}"
                    )

        return df_std

    def _standardize_currency_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize currency values to decimal format."""
        currency_columns = ["amount", "price", "salary", "revenue"]

        df_std = df.copy()

        for column in currency_columns:
            if column in df_std.columns:
                try:
                    # Remove currency symbols and convert to float
                    df_std[column] = (
                        df_std[column]
                        .astype(str)
                        .str.replace(r"[^\d.-]", "", regex=True)
                    )
                    df_std[column] = pd.to_numeric(df_std[column], errors="coerce")
                    df_std[column] = df_std[column].round(
                        2
                    )  # Round to 2 decimal places
                except Exception as e:
                    self.logger.warning(
                        f"Failed to standardize currency column {column}: {str(e)}"
                    )

        return df_std


class DataQualityProcessor:
    """Handles data quality assessment and improvement for silver layer."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the data quality processor.

        Args:
            config: Configuration dictionary for quality rules
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.validator = DataValidator()
        self.schema_validator = SchemaValidator()

    def assess_data_quality(
        self, df: pd.DataFrame, source_table: str
    ) -> DataQualityMetrics:
        """Assess data quality metrics for a dataframe.

        Args:
            df: Input dataframe to assess
            source_table: Name of the source table

        Returns:
            DataQualityMetrics object with quality scores
        """
        try:
            self.logger.info(f"Assessing data quality for {source_table}")

            record_count = len(df)

            # Calculate individual quality metrics
            completeness = self._calculate_completeness(df)
            accuracy = self._calculate_accuracy(df)
            consistency = self._calculate_consistency(df)
            validity = self._calculate_validity(df)
            uniqueness = self._calculate_uniqueness(df)

            # Calculate overall score
            overall_score = (
                completeness + accuracy + consistency + validity + uniqueness
            ) / 5

            # Determine quality level
            if overall_score >= 95:
                quality_level = DataQualityLevel.EXCELLENT
            elif overall_score >= 85:
                quality_level = DataQualityLevel.GOOD
            elif overall_score >= 70:
                quality_level = DataQualityLevel.FAIR
            else:
                quality_level = DataQualityLevel.POOR

            metrics = DataQualityMetrics(
                completeness=completeness,
                accuracy=accuracy,
                consistency=consistency,
                validity=validity,
                uniqueness=uniqueness,
                overall_score=overall_score,
                quality_level=quality_level,
                record_count=record_count,
                processed_count=record_count,  # Will be updated during processing
                error_count=0,  # Will be updated during processing
            )

            self.logger.info(
                f"Data quality assessment completed: {quality_level.value} ({overall_score:.1f}%)"
            )
            return metrics

        except Exception as e:
            self.logger.error(
                "Data quality assessment failed for %s: %s", source_table, str(e)
            )
            raise DataProcessingError("Data quality assessment failed: %s" % str(e))

    def _calculate_completeness(self, df: pd.DataFrame) -> float:
        """Calculate completeness score (percentage of non-null values)."""
        if len(df) == 0:
            return 0.0

        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        completeness = (total_cells - null_cells) / total_cells
        return round(completeness * 100, 2)

    def _calculate_accuracy(self, df: pd.DataFrame) -> float:
        """Calculate accuracy score based on data format validation."""
        if len(df) == 0:
            return 0.0

        accuracy_score = 100.0  # Start with perfect score

        # Check email format accuracy
        if "email" in df.columns:
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            valid_emails = (
                df["email"].astype(str).str.match(email_pattern, na=False).sum()
            )
            email_accuracy = (valid_emails / len(df)) * 100
            accuracy_score = min(accuracy_score, email_accuracy)

        # Check phone format accuracy
        if "phone" in df.columns:
            phone_pattern = r"^\+?[1-9]\d{1,14}$"
            valid_phones = (
                df["phone"].astype(str).str.match(phone_pattern, na=False).sum()
            )
            phone_accuracy = (valid_phones / len(df)) * 100
            accuracy_score = min(accuracy_score, phone_accuracy)

        return round(accuracy_score, 2)

    def _calculate_consistency(self, df: pd.DataFrame) -> float:
        """Calculate consistency score based on data format consistency."""
        if len(df) == 0:
            return 0.0

        consistency_score = 100.0

        # Check date format consistency
        date_columns = ["created_at", "updated_at", "registration_date"]
        for column in date_columns:
            if column in df.columns:
                try:
                    pd.to_datetime(df[column], errors="raise")
                except BaseException:
                    consistency_score -= 20  # Penalize inconsistent date formats

        # Check numeric format consistency
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for column in numeric_columns:
            if df[column].dtype == "object":  # Should be numeric but stored as string
                consistency_score -= 10

        return max(0, round(consistency_score, 2))

    def _calculate_validity(self, df: pd.DataFrame) -> float:
        """Calculate validity score based on business rule validation."""
        if len(df) == 0:
            return 0.0

        validity_score = 100.0

        # Check age validity
        if "age" in df.columns:
            invalid_ages = ((df["age"] < 0) | (df["age"] > 150)).sum()
            age_validity = ((len(df) - invalid_ages) / len(df)) * 100
            validity_score = min(validity_score, age_validity)

        # Check status validity
        if "status" in df.columns:
            valid_statuses = [
                "A",
                "I",
                "P",
                "S",
                "C",
            ]  # Active, Inactive, Pending, Suspended, Cancelled
            invalid_statuses = (~df["status"].isin(valid_statuses)).sum()
            status_validity = ((len(df) - invalid_statuses) / len(df)) * 100
            validity_score = min(validity_score, status_validity)

        return round(validity_score, 2)

    def _calculate_uniqueness(self, df: pd.DataFrame) -> float:
        """Calculate uniqueness score based on duplicate detection."""
        if len(df) == 0:
            return 0.0

        # Check for duplicates based on business keys
        business_keys = ["id", "email"]
        available_keys = [key for key in business_keys if key in df.columns]

        if available_keys:
            duplicates = df.duplicated(subset=available_keys).sum()
            uniqueness = ((len(df) - duplicates) / len(df)) * 100
        else:
            uniqueness = 100.0  # No business keys to check

        return round(uniqueness, 2)


class DataEnrichmentProcessor:
    """Handles data enrichment operations for silver layer."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the data enrichment processor.

        Args:
            config: Configuration dictionary for enrichment rules
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    def enrich_dataframe(self, df: pd.DataFrame, source_table: str) -> pd.DataFrame:
        """Enrich a dataframe with additional derived fields.

        Args:
            df: Input dataframe to enrich
            source_table: Name of the source table

        Returns:
            Enriched dataframe
        """
        try:
            self.logger.info(f"Starting data enrichment for {source_table}")

            enriched_df = df.copy()

            # Add derived fields
            enriched_df = self._add_derived_fields(enriched_df)
            enriched_df = self._add_geographic_data(enriched_df)
            enriched_df = self._add_temporal_features(enriched_df)
            enriched_df = self._add_customer_segments(enriched_df)

            self.logger.info(f"Data enrichment completed for {source_table}")
            return enriched_df

        except Exception as e:
            self.logger.error("Data enrichment failed for %s: %s", source_table, str(e))
            raise DataProcessingError("Data enrichment failed: %s" % str(e))

    def _add_derived_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived fields based on existing data."""
        enriched_df = df.copy()

        # Add full name if first and last names exist
        if "first_name" in df.columns and "last_name" in df.columns:
            enriched_df["full_name"] = df["first_name"] + " " + df["last_name"]

        # Add email domain
        if "email" in df.columns:
            enriched_df["email_domain"] = df["email"].str.split("@").str[1]

        # Add age group
        if "age" in df.columns:
            enriched_df["age_group"] = pd.cut(
                df["age"],
                bins=[0, 18, 25, 35, 50, 65, 100],
                labels=[
                    "Minor",
                    "Young Adult",
                    "Adult",
                    "Middle Age",
                    "Senior",
                    "Elderly",
                ],
            )

        return enriched_df

    def _add_geographic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add geographic enrichment data."""
        enriched_df = df.copy()

        # Add region based on state
        if "state" in df.columns:
            region_mapping = {
                "CA": "West",
                "OR": "West",
                "WA": "West",
                "NV": "West",
                "AZ": "West",
                "NY": "Northeast",
                "MA": "Northeast",
                "CT": "Northeast",
                "NJ": "Northeast",
                "TX": "South",
                "FL": "South",
                "GA": "South",
                "NC": "South",
                "VA": "South",
                "IL": "Midwest",
                "OH": "Midwest",
                "MI": "Midwest",
                "WI": "Midwest",
            }
            enriched_df["region"] = df["state"].map(region_mapping).fillna("Other")

        return enriched_df

    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add temporal features based on date columns."""
        enriched_df = df.copy()

        date_columns = ["created_at", "updated_at", "registration_date"]

        for column in date_columns:
            if column in df.columns:
                try:
                    dates = pd.to_datetime(df[column], errors="coerce")

                    # Add year, month, day
                    enriched_df[f"{column}_year"] = dates.dt.year
                    enriched_df[f"{column}_month"] = dates.dt.month
                    enriched_df[f"{column}_day"] = dates.dt.day
                    enriched_df[f"{column}_weekday"] = dates.dt.day_name()

                    # Add time since creation
                    if column == "created_at":
                        now = datetime.now(timezone.utc)
                        # Ensure dates are timezone-aware
                        if dates.dt.tz is None:
                            dates = dates.dt.tz_localize("UTC")
                        else:
                            dates = dates.dt.tz_convert("UTC")
                        enriched_df["days_since_creation"] = (now - dates).dt.days

                except Exception as e:
                    self.logger.warning(
                        f"Failed to add temporal features for {column}: {str(e)}"
                    )

        return enriched_df

    def _add_customer_segments(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add customer segmentation based on available data."""
        enriched_df = df.copy()

        # Simple customer segmentation based on age and activity
        if "age" in df.columns and "status" in df.columns:

            def segment_customer(row):
                age = row["age"]
                status = row["status"]

                if status == "A":  # Active
                    if age < 30:
                        return "Young Active"
                    elif age < 50:
                        return "Adult Active"
                    else:
                        return "Mature Active"
                else:  # Inactive
                    if age < 30:
                        return "Young Inactive"
                    elif age < 50:
                        return "Adult Inactive"
                    else:
                        return "Mature Inactive"

            enriched_df["customer_segment"] = df.apply(segment_customer, axis=1)

        return enriched_df


class SilverLayerProcessor:
    """Main processor for silver layer data transformation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the silver layer processor.

        Args:
            config: Configuration dictionary for processing rules
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize sub-processors
        self.cleaning_processor = DataCleaningProcessor(config.get("cleaning", {}))
        self.standardization_processor = DataStandardizationProcessor(
            config.get("standardization", {})
        )
        self.quality_processor = DataQualityProcessor(config.get("quality", {}))
        self.enrichment_processor = DataEnrichmentProcessor(
            config.get("enrichment", {})
        )

    def process_bronze_to_silver(
        self, bronze_df: pd.DataFrame, source_table: str
    ) -> Dict[str, Any]:
        """Process bronze layer data to silver layer.

        Args:
            bronze_df: Bronze layer dataframe
            source_table: Name of the source table

        Returns:
            Dictionary containing processed data and metadata
        """
        try:
            self.logger.info(f"Starting silver layer processing for {source_table}")

            # Step 1: Assess initial data quality
            initial_quality = self.quality_processor.assess_data_quality(
                bronze_df, source_table
            )

            # Step 2: Clean the data
            cleaned_df = self.cleaning_processor.clean_dataframe(
                bronze_df, source_table
            )

            # Step 3: Standardize the data
            standardized_df = self.standardization_processor.standardize_dataframe(
                cleaned_df, source_table
            )

            # Step 4: Enrich the data
            enriched_df = self.enrichment_processor.enrich_dataframe(
                standardized_df, source_table
            )

            # Step 5: Assess final data quality
            final_quality = self.quality_processor.assess_data_quality(
                enriched_df, source_table
            )

            # Prepare result
            result = {
                "silver_data": enriched_df,
                "initial_quality": initial_quality,
                "final_quality": final_quality,
                "processing_metadata": {
                    "source_table": source_table,
                    "processing_timestamp": datetime.now(timezone.utc),
                    "processing_version": "1.0",
                    "records_processed": len(enriched_df),
                    "quality_improvement": final_quality.overall_score
                    - initial_quality.overall_score,
                },
            }

            self.logger.info(f"Silver layer processing completed for {source_table}")
            self.logger.info(
                f"Quality improvement: {result['processing_metadata']['quality_improvement']:.1f}%"
            )

            return result

        except Exception as e:
            self.logger.error(
                "Silver layer processing failed for %s: %s", source_table, str(e)
            )
            raise DataProcessingError("Silver layer processing failed: %s" % str(e))

    def process_multiple_tables(
        self, bronze_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Process multiple bronze tables to silver layer.

        Args:
            bronze_data: Dictionary of table names to dataframes

        Returns:
            Dictionary containing all processed silver data and metadata
        """
        results = {}

        for table_name, df in bronze_data.items():
            try:
                results[table_name] = self.process_bronze_to_silver(df, table_name)
            except Exception as e:
                self.logger.error("Failed to process table %s: %s", table_name, str(e))
                results[table_name] = {
                    "error": str(e),
                    "silver_data": pd.DataFrame(),
                    "processing_metadata": {
                        "source_table": table_name,
                        "processing_timestamp": datetime.now(timezone.utc),
                        "status": "failed",
                    },
                }

        return results
