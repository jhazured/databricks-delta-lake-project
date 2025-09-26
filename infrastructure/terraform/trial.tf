# Databricks Trial Configuration
# Simplified setup for trial/development environment

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }
}

# =============================================================================
# VARIABLES FOR TRIAL
# =============================================================================

variable "databricks_host" {
  description = "Databricks workspace host (e.g., https://adb-1234567890123456.7.azuredatabricks.net)"
  type        = string
}

variable "databricks_token" {
  description = "Databricks access token"
  type        = string
  sensitive   = true
}

variable "trial_user_email" {
  description = "Your email for trial workspace"
  type        = string
}

# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================

provider "databricks" {
  host  = var.databricks_host
  token = var.databricks_token
}

# =============================================================================
# TRIAL-FRIENDLY CLUSTER
# =============================================================================

resource "databricks_cluster" "trial_cluster" {
  cluster_name            = "delta-lake-trial-cluster"
  spark_version           = "13.3.x-scala2.12"
  node_type_id            = "i3.xlarge"  # Single node for trial
  driver_node_type_id     = "i3.xlarge"
  num_workers             = 0  # Single node cluster for trial
  autotermination_minutes = 30  # Auto-terminate to save credits
  
  # Trial-optimized configuration
  spark_conf = {
    "spark.databricks.delta.preview.enabled"           = "true"
    "spark.databricks.delta.merge.enableLowShuffle"    = "true"
    "spark.sql.adaptive.enabled"                       = "true"
    "spark.sql.adaptive.coalescePartitions.enabled"    = "true"
    "spark.databricks.cluster.profile"                 = "singleNode"
  }
  
  # Essential libraries for trial
  library {
    pypi {
      package = "delta-spark==2.4.0"
    }
  }
  
  library {
    pypi {
      package = "pandas==2.0.3"
    }
  }
  
  library {
    pypi {
      package = "pyspark==3.4.0"
    }
  }
  
  library {
    pypi {
      package = "mlflow==2.5.0"
    }
  }
  
  tags = {
    Environment = "trial"
    Purpose     = "development"
    Owner       = var.trial_user_email
  }
}

# =============================================================================
# BASIC SCHEMAS (if Unity Catalog is available)
# =============================================================================

# Try to create schemas, but don't fail if Unity Catalog isn't available
resource "databricks_schema" "bronze" {
  count        = var.databricks_host != "" ? 1 : 0
  catalog_name = "main"  # Use default catalog
  name         = "bronze"
  comment      = "Bronze layer for raw data"
}

resource "databricks_schema" "silver" {
  count        = var.databricks_host != "" ? 1 : 0
  catalog_name = "main"
  name         = "silver"
  comment      = "Silver layer for cleaned data"
}

resource "databricks_schema" "gold" {
  count        = var.databricks_host != "" ? 1 : 0
  catalog_name = "main"
  name         = "gold"
  comment      = "Gold layer for business data"
}

# =============================================================================
# TRIAL WORKFLOW
# =============================================================================

resource "databricks_job" "trial_pipeline" {
  name = "delta-lake-trial-pipeline"
  
  # Use existing cluster to save credits
  existing_cluster_id = databricks_cluster.trial_cluster.id
  
  # Simple notebook task for trial
  notebook_task {
    notebook_path = "/Workspace/Shared/delta_lake_trial_pipeline"
  }
  
  # Run once per day to save credits
  schedule {
    quartz_cron_expression = "0 0 * * * ?"
    timezone_id           = "UTC"
  }
  
  tags = {
    Environment = "trial"
    Purpose     = "learning"
  }
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "cluster_id" {
  description = "ID of the trial cluster"
  value       = databricks_cluster.trial_cluster.id
}

output "workspace_url" {
  description = "URL of the Databricks workspace"
  value       = var.databricks_host
}

output "cluster_url" {
  description = "Direct URL to the cluster"
  value       = "${var.databricks_host}/#/setting/clusters/${databricks_cluster.trial_cluster.id}/configuration"
}
