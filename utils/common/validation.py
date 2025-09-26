"""
Data validation utilities.
"""

import json
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd

from .exceptions import ValidationError


class DataValidator:
    """Data validation utility class."""

    def __init__(self) -> None:
        """Initialize data validator."""
        self.validation_rules: Dict[str, List[Callable]] = {}
        self.custom_validators: Dict[str, Callable] = {}

    def add_rule(self, field_name: str, validator: Callable) -> None:
        """
        Add validation rule for a field.

        Args:
            field_name: Name of the field to validate
            validator: Validation function
        """
        if field_name not in self.validation_rules:
            self.validation_rules[field_name] = []
        self.validation_rules[field_name].append(validator)

    def validate(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate data against all rules.

        Args:
            data: Data to validate

        Returns:
            Dictionary of validation errors by field
        """
        errors: Dict[str, List[str]] = {}

        for field_name, validators in self.validation_rules.items():
            field_errors = []
            value = data.get(field_name)

            for validator in validators:
                try:
                    validator(value)
                except ValidationError as e:
                    field_errors.append(e.message)
                except Exception as e:
                    field_errors.append(f"Validation error: {str(e)}")

            if field_errors:
                errors[field_name] = field_errors

        return errors

    def is_valid(self, data: Dict[str, Any]) -> bool:
        """
        Check if data is valid.

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        errors = self.validate(data)
        return len(errors) == 0


class SchemaValidator:
    """Schema validation utility class."""

    def __init__(self) -> None:
        """Initialize schema validator."""
        self.schemas: Dict[str, Dict[str, Any]] = {}

    def add_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """
        Add schema definition.

        Args:
            name: Schema name
            schema: Schema definition
        """
        self.schemas[name] = schema

    def validate_data(
        self, data: Union[Dict, List[Dict]], schema_name: str
    ) -> Dict[str, Any]:
        """
        Validate data against schema.

        Args:
            data: Data to validate
            schema_name: Name of the schema to validate against

        Returns:
            Validation result with errors and warnings
        """
        if schema_name not in self.schemas:
            raise ValidationError(f"Schema '{schema_name}' not found")

        schema = self.schemas[schema_name]
        result: Dict[str, Any] = {"valid": True, "errors": [], "warnings": [], "validated_count": 0}

        data_list: List[Dict[str, Any]]
        if isinstance(data, dict):
            data_list = [data]
        else:
            data_list = data

        for i, record in enumerate(data_list):
            record_errors = self._validate_record(record, schema)
            if record_errors:
                result["valid"] = False
                result["errors"].extend(
                    [f"Record {i}: {error}" for error in record_errors]
                )
            else:
                result["validated_count"] += 1

        return result

    def _validate_record(
        self, record: Dict[str, Any], schema: Dict[str, Any]
    ) -> List[str]:
        """Validate a single record against schema."""
        errors = []

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in record or record[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate field types and constraints
        properties = schema.get("properties", {})
        for field, value in record.items():
            if field in properties:
                field_schema = properties[field]
                field_errors = self._validate_field(value, field_schema, field)
                errors.extend(field_errors)

        return errors

    def _validate_field(
        self, value: Any, field_schema: Dict[str, Any], field_name: str
    ) -> List[str]:
        """Validate a single field against its schema."""
        errors = []

        # Type validation
        expected_type = field_schema.get("type")
        if expected_type and not self._check_type(value, expected_type):
            errors.append(f"Field '{field_name}' must be of type {expected_type}")
            return errors  # Skip other validations if type is wrong

        # String validations
        if expected_type == "string":
            string_errors = self._validate_string(value, field_schema, field_name)
            errors.extend(string_errors)

        # Number validations
        elif expected_type in ["number", "integer"]:
            number_errors = self._validate_number(value, field_schema, field_name)
            errors.extend(number_errors)

        # Array validations
        elif expected_type == "array":
            array_errors = self._validate_array(value, field_schema, field_name)
            errors.extend(array_errors)

        # Object validations
        elif expected_type == "object":
            object_errors = self._validate_object(value, field_schema, field_name)
            errors.extend(object_errors)

        return errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        if value is None:
            return True  # None is allowed for optional fields

        type_mapping: Dict[str, Any] = {
            "string": str,
            "integer": int,
            "number": (int, float, Decimal),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type is not None:
            return isinstance(value, expected_python_type)

        return False

    def _validate_string(
        self, value: str, field_schema: Dict[str, Any], field_name: str
    ) -> List[str]:
        """Validate string field."""
        errors = []

        # Min/max length
        min_length = field_schema.get("minLength")
        max_length = field_schema.get("maxLength")

        if min_length is not None and len(value) < min_length:
            errors.append(
                f"Field '{field_name}' must be at least {min_length} characters"
            )

        if max_length is not None and len(value) > max_length:
            errors.append(
                f"Field '{field_name}' must be at most {max_length} characters"
            )

        # Pattern validation
        pattern = field_schema.get("pattern")
        if pattern and not re.match(pattern, value):
            errors.append(f"Field '{field_name}' does not match required pattern")

        # Enum validation
        enum_values = field_schema.get("enum")
        if enum_values and value not in enum_values:
            errors.append(f"Field '{field_name}' must be one of: {enum_values}")

        return errors

    def _validate_number(
        self,
        value: Union[int, float, Decimal],
        field_schema: Dict[str, Any],
        field_name: str,
    ) -> List[str]:
        """Validate number field."""
        errors = []

        # Min/max values
        minimum = field_schema.get("minimum")
        maximum = field_schema.get("maximum")

        if minimum is not None and value < minimum:
            errors.append(f"Field '{field_name}' must be at least {minimum}")

        if maximum is not None and value > maximum:
            errors.append(f"Field '{field_name}' must be at most {maximum}")

        return errors

    def _validate_array(
        self, value: List[Any], field_schema: Dict[str, Any], field_name: str
    ) -> List[str]:
        """Validate array field."""
        errors = []

        # Min/max items
        min_items = field_schema.get("minItems")
        max_items = field_schema.get("maxItems")

        if min_items is not None and len(value) < min_items:
            errors.append(f"Field '{field_name}' must have at least {min_items} items")

        if max_items is not None and len(value) > max_items:
            errors.append(f"Field '{field_name}' must have at most {max_items} items")

        # Item validation
        items_schema = field_schema.get("items")
        if items_schema:
            for i, item in enumerate(value):
                item_errors = self._validate_field(
                    item, items_schema, f"{field_name}[{i}]"
                )
                errors.extend(item_errors)

        return errors

    def _validate_object(
        self, value: Dict[str, Any], field_schema: Dict[str, Any], field_name: str
    ) -> List[str]:
        """Validate object field."""
        errors = []

        # Properties validation
        properties = field_schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            if prop_name in value:
                prop_errors = self._validate_field(
                    value[prop_name], prop_schema, f"{field_name}.{prop_name}"
                )
                errors.extend(prop_errors)

        return errors


# Common validation functions
def validate_email(value: Any) -> None:
    """Validate email format."""
    if value is None:
        return

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, str(value)):
        raise ValidationError("Invalid email format", value=value)


def validate_phone(value: Any) -> None:
    """Validate phone number format."""
    if value is None:
        return

    phone_pattern = r"^\+?[\d\s\-\(\)]{10,}$"
    if not re.match(phone_pattern, str(value)):
        raise ValidationError("Invalid phone number format", value=value)


def validate_date(value: Any) -> None:
    """Validate date format."""
    if value is None:
        return

    if isinstance(value, str):
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValidationError(
                "Invalid date format. Expected YYYY-MM-DD", value=value
            )
    elif not isinstance(value, (date, datetime)):
        raise ValidationError("Value must be a date or datetime", value=value)


def validate_positive_number(value: Any) -> None:
    """Validate positive number."""
    if value is None:
        return

    try:
        num = float(value)
        if num <= 0:
            raise ValidationError("Value must be positive", value=value)
    except (ValueError, TypeError):
        raise ValidationError("Value must be a number", value=value)


def validate_not_empty(value: Any) -> None:
    """Validate that value is not empty."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError("Value cannot be empty", value=value)


def validate_json(value: Any) -> None:
    """Validate JSON format."""
    if value is None:
        return

    if isinstance(value, str):
        try:
            json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON format", value=value)
    elif not isinstance(value, (dict, list)):
        raise ValidationError("Value must be valid JSON", value=value)
