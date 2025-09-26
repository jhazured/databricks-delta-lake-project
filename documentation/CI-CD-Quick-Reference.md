# CI/CD Quick Reference

## 🚀 Workflow Overview

**Single File**: `.github/workflows/ci.yml`  
**Trigger**: Push, PR, Schedule, Manual  
**Jobs**: 10 comprehensive jobs covering all aspects

## 📋 Job Summary

| Job | Purpose | Dependencies | Runs On |
|-----|---------|--------------|---------|
| `code-quality` | Linting, formatting, type checking | None | All triggers |
| `test` | Unit tests (Python 3.9-3.11, Java 11-17) | code-quality | All triggers |
| `security` | Vulnerability scanning | None | All triggers |
| `docker-tests` | Container build & test | code-quality | All triggers |
| `kubernetes-validation` | K8s manifest validation | docker-tests | All triggers |
| `terraform-validation` | Infrastructure validation | None | All triggers |
| `performance` | Benchmark testing | None | Push to main only |
| `build` | Package creation | All test jobs | All triggers |
| `deploy` | Databricks deployment | build, performance | Push to main OR manual |
| `test-summary` | Results overview | All jobs | Always |

## ⚡ Quick Commands

### Local Development
```bash
# Format code
black utils/ scripts/ api/
isort utils/ scripts/ api/

# Run linting
flake8 utils/ scripts/ api/ --max-line-length=88

# Run tests
pytest testing/unit/ -v

# Type checking
mypy utils/ scripts/ api/ --ignore-missing-imports
```

### Manual Deployment
1. Go to GitHub Actions tab
2. Select "Databricks Delta Lake CI/CD Pipeline"
3. Click "Run workflow"
4. Choose environment: `dev`, `staging`, `prod`, `trial`
5. Click "Run workflow"

## 🔧 Environment Variables

```yaml
PYTHON_VERSION: '3.11'    # Default Python version
JAVA_VERSION: '11'        # Default Java version
```

## 🔐 Required Secrets

```
DATABRICKS_HOST          # Databricks workspace URL
DATABRICKS_TOKEN         # Personal access token
DATABRICKS_CLUSTER_ID    # Target cluster ID
DATABRICKS_DEPLOYMENT_JOB_ID  # Deployment job ID
```

## 📊 Test Matrix

| Python | Java | Status |
|--------|------|--------|
| 3.9    | 11   | ✅     |
| 3.10   | 11   | ✅     |
| 3.11   | 11   | ✅     |
| 3.11   | 17   | ✅     |

## 🐳 Docker Targets

- `development`: Dev environment with all tools
- `production`: Optimized production image
- `api`: FastAPI service container
- `data-processing`: Data pipeline container

## 🚨 Common Issues & Fixes

### Code Quality Failures
```bash
# Fix formatting
black utils/ scripts/ api/
isort utils/ scripts/ api/

# Fix linting
flake8 utils/ scripts/ api/ --max-line-length=88
```

### Test Failures
- Check test logs for specific errors
- Verify test data and mocks
- Update tests for API changes

### Security Issues
- Review vulnerability reports
- Update dependencies if needed
- Address security findings

### Terraform Errors
```bash
# Fix formatting
terraform fmt -recursive infrastructure/terraform/

# Validate syntax
terraform validate infrastructure/terraform/
```

## 📈 Monitoring

### Key Metrics
- Workflow execution time
- Test pass/fail rates
- Security vulnerability trends
- Deployment success rates

### GitHub Actions URL
```
https://github.com/jhazured/databricks-delta-lake-project/actions
```

## 🎯 Best Practices

### Before Pushing
1. Run local tests: `pytest`
2. Check formatting: `black --check .`
3. Verify linting: `flake8 .`
4. Test Docker builds locally

### Code Review
- Check CI/CD status
- Review test coverage
- Verify security scans
- Validate infrastructure changes

### Deployment
- Test in dev environment first
- Monitor deployment logs
- Verify functionality post-deployment
- Update documentation

## 🔄 Workflow Triggers

| Trigger | Condition | Actions |
|---------|-----------|---------|
| **Push to main** | Code changes | Full pipeline + deployment |
| **Push to develop** | Code changes | Full pipeline (no deployment) |
| **Pull Request** | PR to main | Validation + testing |
| **Schedule** | Daily 2 AM UTC | Security scans only |
| **Manual** | Workflow dispatch | Deploy to chosen environment |

## 📝 Quick Links

- **Full Documentation**: [CI-CD-Workflow-Documentation.md](./CI-CD-Workflow-Documentation.md)
- **Pipeline Diagram**: [CI-CD-Pipeline-Diagram.txt](./CI-CD-Pipeline-Diagram.txt)
- **GitHub Actions**: https://github.com/jhazured/databricks-delta-lake-project/actions
- **Project Setup**: [TRIAL-SETUP-GUIDE.md](./TRIAL-SETUP-GUIDE.md)

---

*Quick reference for the Databricks Delta Lake CI/CD pipeline*