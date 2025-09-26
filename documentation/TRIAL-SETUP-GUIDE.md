# Databricks Trial Setup Guide

## 🆓 Getting Started with Databricks Trial

### **Step 1: Sign Up for Trial**

1. **Go to**: [https://www.databricks.com/try-databricks](https://www.databricks.com/try-databricks)
2. **Choose your cloud provider**:
   - **AWS** (recommended for this project)
   - **Azure** 
   - **GCP**
3. **Fill out the form** with your details
4. **Verify your email**
5. **Wait for workspace creation** (usually 5-10 minutes)

### **Step 2: Get Your Workspace Information**

After your workspace is created, you'll need:

1. **Workspace URL**: `https://adb-1234567890123456.7.azuredatabricks.net`
2. **Access Token**: 
   - Go to User Settings → Developer → Access Tokens
   - Generate New Token
   - Copy and save it securely

### **Step 3: Configure Your Project**

#### **Option A: Use Trial Terraform Configuration**

```bash
# Navigate to your project
cd /home/jhark/workspace/databricks-delta-lake-project

# Create trial configuration
cp infrastructure/terraform/trial.tf infrastructure/terraform/main.tf

# Create terraform.tfvars file
cat > infrastructure/terraform/terraform.tfvars << EOF
databricks_host = "https://your-workspace-url.databricks.com"
databricks_token = "your-access-token"
trial_user_email = "your-email@example.com"
EOF
```

#### **Option B: Manual Setup (No Terraform)**

If you prefer to set up manually:

1. **Create a cluster**:
   - Go to Compute → Create Cluster
   - Name: `delta-lake-trial-cluster`
   - Runtime: `13.3.x-scala2.12`
   - Node Type: `i3.xlarge`
   - Workers: `0` (single node)
   - Auto-termination: `30 minutes`

2. **Install libraries**:
   - delta-spark==2.4.0
   - pandas==2.0.3
   - pyspark==3.4.0
   - mlflow==2.5.0

## 🚀 **Trial-Optimized Project Structure**

### **What to Focus On (Trial Priorities)**

#### **1. Core Data Processing (High Priority)**
```
data/
├── bronze/           # Raw data ingestion
├── silver/           # Data cleaning
└── gold/             # Business logic
```

#### **2. Basic ML Pipeline (Medium Priority)**
```
ml/
├── experiments/      # ML experiments
├── feature_store/    # Feature management
└── model_registry/   # Model tracking
```

#### **3. Simple Monitoring (Low Priority)**
```
monitoring/
├── metrics/          # Basic metrics
└── logs/             # Simple logging
```

### **What to Skip (Trial Limitations)**

- ❌ **Complex Infrastructure**: Multi-cloud, VPC, etc.
- ❌ **Advanced Security**: RBAC, encryption, etc.
- ❌ **High Availability**: Multi-region, disaster recovery
- ❌ **Enterprise Features**: Unity Catalog (if not available)

## 💰 **Trial Cost Management**

### **Cost Optimization Tips**

1. **Use Single-Node Clusters**:
   ```python
   # In your notebooks
   spark.conf.set("spark.databricks.cluster.profile", "singleNode")
   ```

2. **Auto-Terminate Clusters**:
   - Set auto-termination to 30 minutes
   - Manually terminate when done

3. **Use Smaller Node Types**:
   - `i3.xlarge` instead of `i3.2xlarge`
   - `m5.large` for lighter workloads

4. **Optimize Storage**:
   - Use Delta Lake for efficiency
   - Compress data when possible

### **Trial Limits to Watch**

| Resource | Trial Limit | Optimization |
|----------|-------------|--------------|
| **Compute Hours** | ~50-100 hours | Use single-node clusters |
| **Storage** | ~100GB | Use Delta Lake compression |
| **Concurrent Clusters** | 2-3 | Terminate unused clusters |
| **API Calls** | Limited | Cache results locally |

## 🧪 **Trial Development Workflow**

### **1. Daily Development**

```bash
# Morning: Start your cluster
# Work on your project
# Evening: Terminate cluster to save credits
```

### **2. Project Development Phases**

#### **Phase 1: Basic Setup (Week 1)**
- [ ] Set up trial workspace
- [ ] Create basic cluster
- [ ] Test Delta Lake functionality
- [ ] Create sample data pipeline

#### **Phase 2: Data Processing (Week 2)**
- [ ] Implement bronze layer
- [ ] Build silver layer transformations
- [ ] Create gold layer aggregations
- [ ] Test end-to-end pipeline

#### **Phase 3: ML Features (Week 3)**
- [ ] Set up MLflow experiments
- [ ] Build feature store
- [ ] Create model training pipeline
- [ ] Test model deployment

#### **Phase 4: Integration (Week 4)**
- [ ] Connect to external data sources
- [ ] Build monitoring dashboards
- [ ] Create API endpoints
- [ ] Document your work

## 🔧 **Trial-Specific Configurations**

### **Environment Variables**

Create `config/environments/trial.env`:

```bash
# Trial Environment Configuration
ENVIRONMENT=trial
DATABRICKS_HOST=https://your-workspace-url.databricks.com
DATABRICKS_TOKEN=your-access-token

# Trial-optimized settings
CLUSTER_NODE_TYPE=i3.xlarge
CLUSTER_WORKERS=0
AUTO_TERMINATION_MINUTES=30
SPARK_VERSION=13.3.x-scala2.12

# Data settings
DATA_PATH=/tmp/delta-lake-trial
SAMPLE_DATA_SIZE=1000
```

### **Trial Python Utilities**

Create `utils/trial_helpers.py`:

```python
import os
from pyspark.sql import SparkSession

def get_trial_spark_session():
    """Get optimized Spark session for trial"""
    return SparkSession.builder \
        .appName("DeltaLakeTrial") \
        .config("spark.databricks.delta.preview.enabled", "true") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.databricks.cluster.profile", "singleNode") \
        .getOrCreate()

def optimize_for_trial(df):
    """Optimize DataFrame for trial environment"""
    return df.coalesce(1)  # Single partition for trial
```

## 📊 **Trial Success Metrics**

### **What to Achieve in Trial**

1. **Technical Goals**:
   - [ ] Working Delta Lake pipeline
   - [ ] Basic ML model training
   - [ ] Data quality monitoring
   - [ ] Simple API endpoints

2. **Learning Goals**:
   - [ ] Understand Databricks workflow
   - [ ] Learn Delta Lake features
   - [ ] Practice MLOps concepts
   - [ ] Experience enterprise data platform

3. **Business Goals**:
   - [ ] Prove concept viability
   - [ ] Estimate full implementation costs
   - [ ] Identify technical challenges
   - [ ] Plan production architecture

## 🚀 **Transitioning from Trial to Production**

### **When Trial Ends**

1. **Evaluate Results**:
   - What worked well?
   - What needs improvement?
   - What are the costs?

2. **Plan Production**:
   - Choose cloud provider
   - Estimate infrastructure costs
   - Plan team training
   - Design production architecture

3. **Migrate Code**:
   - Update configurations
   - Add production features
   - Implement security
   - Set up monitoring

### **Trial to Production Checklist**

- [ ] **Code Migration**: Move notebooks and scripts
- [ ] **Data Migration**: Export/import sample data
- [ ] **Configuration Update**: Update environment settings
- [ ] **Infrastructure Setup**: Deploy production infrastructure
- [ ] **Team Training**: Train team on production setup
- [ ] **Monitoring Setup**: Implement production monitoring

## 🆘 **Trial Troubleshooting**

### **Common Issues**

1. **Cluster Won't Start**:
   - Check node type availability
   - Verify permissions
   - Try different region

2. **Out of Credits**:
   - Use smaller node types
   - Reduce auto-termination time
   - Contact support for extension

3. **Unity Catalog Not Available**:
   - Use default `main` catalog
   - Create schemas in `main`
   - Plan for production upgrade

### **Getting Help**

- **Databricks Community**: [community.databricks.com](https://community.databricks.com)
- **Documentation**: [docs.databricks.com](https://docs.databricks.com)
- **Support**: Available in trial workspace

---

**Remember**: The trial is perfect for learning and prototyping. Use it to build a solid foundation that you can then scale to production! 🚀
