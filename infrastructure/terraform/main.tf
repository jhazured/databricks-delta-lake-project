# Databricks Delta Lake Project - Infrastructure as Code
# This Terraform configuration sets up the complete infrastructure for the data lake platform

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    # Configure backend in terraform.tfvars
    # bucket = "your-terraform-state-bucket"
    # key    = "logistics-platform/terraform.tfstate"
    # region = "us-west-2"
  }
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "delta-lake-project"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "databricks_host" {
  description = "Databricks workspace host"
  type        = string
}

variable "databricks_token" {
  description = "Databricks access token"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "delta-lake-project"
    Environment = "dev"
    ManagedBy   = "terraform"
    Owner       = "data-engineering-team"
  }
}

# =============================================================================
# PROVIDERS
# =============================================================================

provider "aws" {
  region = var.region

  default_tags {
    tags = var.tags
  }
}

provider "databricks" {
  host  = var.databricks_host
  token = var.databricks_token
}

# =============================================================================
# DATA SOURCES
# =============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# =============================================================================
# S3 BUCKET FOR DATA LAKE
# =============================================================================

resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-${var.environment}-data-lake-${random_string.bucket_suffix.result}"

  tags = merge(var.tags, {
    Name = "Delta Lake Data Lake"
    Type = "data-lake"
  })
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "data_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }
  }
}

# =============================================================================
# IAM ROLE FOR DATABRICKS
# =============================================================================

resource "aws_iam_role" "databricks_role" {
  name = "${var.project_name}-${var.environment}-databricks-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_policy" "databricks_policy" {
  name = "${var.project_name}-${var.environment}-databricks-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "databricks_policy" {
  role       = aws_iam_role.databricks_role.name
  policy_arn = aws_iam_policy.databricks_policy.arn
}

# =============================================================================
# DATABRICKS WORKSPACE CONFIGURATION
# =============================================================================

resource "databricks_catalog" "data_catalog" {
  name    = "${var.project_name}_${var.environment}_catalog"
  comment = "Delta Lake data catalog for ${var.environment} environment"

  properties = {
    purpose = "data-analytics"
  }
}

resource "databricks_schema" "bronze" {
  catalog_name = databricks_catalog.data_catalog.name
  name         = "bronze"
  comment      = "Bronze layer for raw data ingestion"
}

resource "databricks_schema" "silver" {
  catalog_name = databricks_catalog.data_catalog.name
  name         = "silver"
  comment      = "Silver layer for cleaned and standardized data"
}

resource "databricks_schema" "gold" {
  catalog_name = databricks_catalog.data_catalog.name
  name         = "gold"
  comment      = "Gold layer for business-ready data marts"
}

resource "databricks_schema" "features" {
  catalog_name = databricks_catalog.data_catalog.name
  name         = "features"
  comment      = "ML Feature Store"
}

resource "databricks_schema" "models" {
  catalog_name = databricks_catalog.data_catalog.name
  name         = "models"
  comment      = "ML model registry and metadata"
}

# =============================================================================
# DATABRICKS CLUSTER
# =============================================================================

resource "databricks_cluster" "data_cluster" {
  cluster_name            = "${var.project_name}-${var.environment}-cluster"
  spark_version           = "13.3.x-scala2.12"
  node_type_id            = "i3.xlarge"
  driver_node_type_id     = "i3.xlarge"
  num_workers             = var.environment == "prod" ? 4 : 2
  autotermination_minutes = var.environment == "prod" ? 0 : 30
  enable_elastic_disk     = true
  data_security_mode      = "SINGLE_USER"
  runtime_engine          = "STANDARD"

  aws_attributes {
    zone_id              = "us-west-2a"
    instance_profile_arn = aws_iam_role.databricks_role.arn
    ebs_volume_type      = "gp3"
    ebs_volume_size      = 100
    ebs_volume_count     = 1
  }

  spark_conf = {
    "spark.databricks.delta.preview.enabled"        = "true"
    "spark.databricks.delta.merge.enableLowShuffle" = "true"
    "spark.sql.adaptive.enabled"                    = "true"
    "spark.sql.adaptive.coalescePartitions.enabled" = "true"
  }

  library {
    pypi {
      package = "mlflow==2.5.0"
    }
  }

  library {
    pypi {
      package = "scikit-learn==1.3.0"
    }
  }

  library {
    pypi {
      package = "pandas==2.0.3"
    }
  }

  library {
    pypi {
      package = "numpy==1.24.3"
    }
  }
}

# =============================================================================
# DATABRICKS WORKFLOWS
# =============================================================================

resource "databricks_job" "bronze_to_silver" {
  name = "${var.project_name}-${var.environment}-bronze-to-silver"

  task {
    task_key = "bronze_to_silver_task"

    new_cluster {
      num_workers   = 2
      spark_version = "13.3.x-scala2.12"
      node_type_id  = "i3.xlarge"

      aws_attributes {
        zone_id              = "us-west-2a"
        instance_profile_arn = aws_iam_role.databricks_role.arn
      }
    }

    notebook_task {
      notebook_path = "/workflows/delta_live_tables/silver_layer_transformations"
    }
  }

  schedule {
    quartz_cron_expression = "0 0 * * * ?"
    timezone_id            = "UTC"
  }
}

resource "databricks_job" "silver_to_gold" {
  name = "${var.project_name}-${var.environment}-silver-to-gold"

  task {
    task_key = "silver_to_gold_task"

    new_cluster {
      num_workers   = 2
      spark_version = "13.3.x-scala2.12"
      node_type_id  = "i3.xlarge"

      aws_attributes {
        zone_id              = "us-west-2a"
        instance_profile_arn = aws_iam_role.databricks_role.arn
      }
    }

    notebook_task {
      notebook_path = "/workflows/delta_live_tables/gold_layer_transformations"
    }
  }

  schedule {
    quartz_cron_expression = "0 1 * * * ?"
    timezone_id            = "UTC"
  }

  depends_on = [databricks_job.bronze_to_silver]
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "s3_bucket_name" {
  description = "Name of the S3 bucket for data lake"
  value       = aws_s3_bucket.data_lake.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for data lake"
  value       = aws_s3_bucket.data_lake.arn
}

output "iam_role_arn" {
  description = "ARN of the IAM role for Databricks"
  value       = aws_iam_role.databricks_role.arn
}

output "databricks_catalog_name" {
  description = "Name of the Databricks catalog"
  value       = databricks_catalog.data_catalog.name
}

output "databricks_cluster_id" {
  description = "ID of the Databricks cluster"
  value       = databricks_cluster.data_cluster.id
}

output "databricks_workspace_url" {
  description = "URL of the Databricks workspace"
  value       = var.databricks_host
}
