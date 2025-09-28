# API Documentation

## Overview

The Databricks Delta Lake project provides a RESTful API built with FastAPI for accessing data and machine learning models. The API is designed to be scalable, secure, and easy to use.

## Base URL

```
Production: https://api.databricks-delta-lake.com
Development: http://localhost:8000
```

## Authentication

All API endpoints require authentication using Databricks Personal Access Tokens.

### Headers
```
Authorization: Bearer <your-databricks-token>
Content-Type: application/json
```

## Endpoints

### Health Check

#### GET /health
Check the health status of the API service.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "environment": "production"
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Service is unhealthy

### Data Access

#### GET /api/data/{table_name}
Retrieve data from specified Delta Lake table.

**Parameters:**
- `table_name` (path): Name of the Delta Lake table
- `limit` (query, optional): Maximum number of records to return (default: 100)
- `offset` (query, optional): Number of records to skip (default: 0)
- `columns` (query, optional): Comma-separated list of columns to return

**Example Request:**
```bash
curl -H "Authorization: Bearer <token>" \
     "https://api.databricks-delta-lake.com/api/data/sales_data?limit=50&columns=id,amount,date"
```

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "amount": 1500.00,
      "date": "2024-01-15"
    }
  ],
  "metadata": {
    "total_records": 1000,
    "returned_records": 50,
    "offset": 0,
    "table_name": "sales_data"
  }
}
```

**Status Codes:**
- `200 OK`: Data retrieved successfully
- `404 Not Found`: Table not found
- `403 Forbidden`: Insufficient permissions
- `500 Internal Server Error`: Server error

#### POST /api/data/{table_name}/query
Execute custom SQL query on specified table.

**Request Body:**
```json
{
  "query": "SELECT * FROM sales_data WHERE amount > 1000",
  "limit": 100
}
```

**Response:**
```json
{
  "data": [...],
  "metadata": {
    "query": "SELECT * FROM sales_data WHERE amount > 1000",
    "execution_time_ms": 150,
    "record_count": 25
  }
}
```

### Machine Learning

#### POST /api/ml/predict
Make predictions using deployed ML models.

**Request Body:**
```json
{
  "model_name": "sales_forecast",
  "features": {
    "historical_sales": [1000, 1200, 1100],
    "seasonality": "Q1",
    "market_conditions": "stable"
  }
}
```

**Response:**
```json
{
  "prediction": 1250.50,
  "confidence": 0.85,
  "model_version": "v1.2.0",
  "prediction_interval": {
    "lower": 1100.00,
    "upper": 1400.00
  }
}
```

**Status Codes:**
- `200 OK`: Prediction successful
- `400 Bad Request`: Invalid input data
- `404 Not Found`: Model not found
- `500 Internal Server Error`: Model prediction error

#### GET /api/ml/models
List available ML models.

**Response:**
```json
{
  "models": [
    {
      "name": "sales_forecast",
      "version": "v1.2.0",
      "status": "active",
      "created_at": "2024-01-10T08:00:00Z",
      "accuracy": 0.92
    }
  ]
}
```

### Data Pipeline Management

#### POST /api/pipelines/{pipeline_name}/run
Trigger data pipeline execution.

**Request Body:**
```json
{
  "parameters": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }
}
```

**Response:**
```json
{
  "run_id": "run_12345",
  "status": "started",
  "started_at": "2024-01-15T10:30:00Z"
}
```

#### GET /api/pipelines/{pipeline_name}/runs/{run_id}
Get pipeline run status.

**Response:**
```json
{
  "run_id": "run_12345",
  "status": "completed",
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:35:00Z",
  "duration_seconds": 300,
  "records_processed": 10000
}
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "limit",
      "issue": "Value must be between 1 and 1000"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_12345"
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Invalid input parameters
- `AUTHENTICATION_ERROR`: Invalid or missing authentication
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Authenticated users**: 1000 requests per hour
- **Unauthenticated users**: 100 requests per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

## SDK Examples

### Python SDK
```python
from databricks_delta_lake_client import APIClient

# Initialize client
client = APIClient(
    base_url="https://api.databricks-delta-lake.com",
    token="your-databricks-token"
)

# Get data
data = client.get_data("sales_data", limit=100)

# Make prediction
prediction = client.predict(
    model_name="sales_forecast",
    features={"historical_sales": [1000, 1200, 1100]}
)
```

### JavaScript SDK
```javascript
import { APIClient } from '@databricks/delta-lake-client';

// Initialize client
const client = new APIClient({
  baseURL: 'https://api.databricks-delta-lake.com',
  token: 'your-databricks-token'
});

// Get data
const data = await client.getData('sales_data', { limit: 100 });

// Make prediction
const prediction = await client.predict('sales_forecast', {
  features: { historical_sales: [1000, 1200, 1100] }
});
```

## Webhooks

### Pipeline Completion Webhook
```json
{
  "event": "pipeline.completed",
  "data": {
    "pipeline_name": "daily_etl",
    "run_id": "run_12345",
    "status": "success",
    "completed_at": "2024-01-15T10:35:00Z"
  }
}
```

### Model Deployment Webhook
```json
{
  "event": "model.deployed",
  "data": {
    "model_name": "sales_forecast",
    "version": "v1.3.0",
    "deployed_at": "2024-01-15T10:30:00Z"
  }
}
```

## API Versioning

The API uses URL-based versioning:
- Current version: `v1`
- Future versions: `v2`, `v3`, etc.

Example: `https://api.databricks-delta-lake.com/v1/api/data/sales_data`

## OpenAPI Specification

The complete OpenAPI specification is available at:
```
https://api.databricks-delta-lake.com/docs
```

## Support

For API support and questions:
- **Documentation**: Check this documentation
- **Issues**: Create GitHub issue
- **Contact**: team@databricks-delta-lake.com

---

*API documentation version: 1.0*
*Last updated: 2024-01-15*
