"""Custom exceptions for the Delta Lake project."""

from typing import Any, Dict, Optional


class DeltaLakeError(Exception):
    """Base exception for Delta Lake project."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize Delta Lake error.

        Args:
            message: Error message
            error_code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class ValidationError(DeltaLakeError):
    """Exception raised for data validation errors."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
    ):
        """Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
            value: Value that failed validation
        """
        super().__init__(message, error_code="VALIDATION_ERROR")
        self.field = field
        self.value = value
        self.details.update(
            {"field": field, "value": str(value) if value is not None else None}
        )


class ConfigurationError(DeltaLakeError):
    """Exception raised for configuration errors."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        """Initialize configuration error.

        Args:
            message: Error message
            config_key: Configuration key that caused the error
        """
        super().__init__(message, error_code="CONFIGURATION_ERROR")
        self.config_key = config_key
        self.details.update({"config_key": config_key})


class DataProcessingError(DeltaLakeError):
    """Exception raised for data processing errors."""

    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        data_source: Optional[str] = None,
    ):
        """Initialize data processing error.

        Args:
            message: Error message
            stage: Processing stage where error occurred
            data_source: Data source that caused the error
        """
        super().__init__(message, error_code="DATA_PROCESSING_ERROR")
        self.stage = stage
        self.data_source = data_source
        self.details.update({"stage": stage, "data_source": data_source})


class MLModelError(DeltaLakeError):
    """Exception raised for ML model errors."""

    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
    ):
        """Initialize ML model error.

        Args:
            message: Error message
            model_name: Name of the model that caused the error
            model_version: Version of the model that caused the error
        """
        super().__init__(message, error_code="ML_MODEL_ERROR")
        self.model_name = model_name
        self.model_version = model_version
        self.details.update({"model_name": model_name, "model_version": model_version})


class APIError(DeltaLakeError):
    """Exception raised for API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        endpoint: Optional[str] = None,
    ):
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            endpoint: API endpoint that caused the error
        """
        super().__init__(message, error_code="API_ERROR")
        self.status_code = status_code
        self.endpoint = endpoint
        self.details.update({"status_code": status_code, "endpoint": endpoint})


class SecurityError(DeltaLakeError):
    """Exception raised for security-related errors."""

    def __init__(
        self,
        message: str,
        security_event: Optional[str] = None,
        user: Optional[str] = None,
    ):
        """Initialize security error.

        Args:
            message: Error message
            security_event: Type of security event
            user: User associated with the security event
        """
        super().__init__(message, error_code="SECURITY_ERROR")
        self.security_event = security_event
        self.user = user
        self.details.update({"security_event": security_event, "user": user})


class InfrastructureError(DeltaLakeError):
    """Exception raised for infrastructure errors."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_name: Optional[str] = None,
    ):
        """Initialize infrastructure error.

        Args:
            message: Error message
            resource_type: Type of infrastructure resource
            resource_name: Name of the infrastructure resource
        """
        super().__init__(message, error_code="INFRASTRUCTURE_ERROR")
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.details.update(
            {"resource_type": resource_type, "resource_name": resource_name}
        )


class MonitoringError(DeltaLakeError):
    """Exception raised for monitoring errors."""

    def __init__(
        self,
        message: str,
        metric_name: Optional[str] = None,
        alert_type: Optional[str] = None,
    ):
        """Initialize monitoring error.

        Args:
            message: Error message
            metric_name: Name of the metric that caused the error
            alert_type: Type of alert that caused the error
        """
        super().__init__(message, error_code="MONITORING_ERROR")
        self.metric_name = metric_name
        self.alert_type = alert_type
        self.details.update({"metric_name": metric_name, "alert_type": alert_type})
