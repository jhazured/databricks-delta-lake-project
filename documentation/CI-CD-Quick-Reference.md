# CI/CD Quick Reference Guide

## 🚀 Quick Start

### What Happens When You Push Code

1. **Push to `main`** → Full pipeline (test, build, deploy)
2. **Push to `develop`** → Test and build only
3. **Pull Request** → Test and build only
4. **Daily at 2 AM** → Security scan only

## 📋 Required Setup

### GitHub Secrets (for deployment)
```
DATABRICKS_TOKEN     # Your Databricks personal access token
DATABRICKS_HOST      # Your Databricks workspace URL  
DATABRICKS_CLUSTER_ID # Target cluster ID
```

**Setup**: Repository Settings → Secrets and variables → Actions

## 🧪 Writing Tests

### Test Structure
```
testing/
├── unit/           # Fast, isolated tests
├── integration/    # Database/external service tests  
├── performance/    # Benchmark tests
├── security/       # Security-focused tests
└── e2e/           # End-to-end tests
```

### Test Markers
```python
@pytest.mark.unit
def test_basic_function():
    pass

@pytest.mark.integration  
def test_database_connection():
    pass

@pytest.mark.slow
def test_large_dataset():
    pass

@pytest.mark.performance
def test_benchmark():
    pass
```

### Test Naming
- Files: `test_*.py` or `*_test.py`
- Functions: `test_*`
- Classes: `Test*`

## 🔍 Code Quality Standards

### Linting (flake8)
- Max line length: 88 characters
- Max complexity: 10
- Critical errors: E9, F63, F7, F82

### Formatting (black)
```bash
black scripts/ utils/  # Format code
black --check scripts/ utils/  # Check formatting
```

### Import Sorting (isort)
```bash
isort scripts/ utils/  # Sort imports
isort --check-only scripts/ utils/  # Check sorting
```

### Type Checking (mypy)
```bash
mypy scripts/ utils/ --ignore-missing-imports
```

## 🛡️ Security

### Daily Security Scans
- **Safety**: Dependency vulnerability check
- **Bandit**: Code security analysis
- **Reports**: Available in Actions artifacts

### Manual Security Check
```bash
pip install safety bandit
safety check
bandit -r scripts/ utils/
```

## 📊 Performance Testing

### Benchmark Tests
```python
import pytest

@pytest.mark.performance
def test_processing_speed(benchmark):
    result = benchmark(process_data, large_dataset)
    assert result is not None
```

### Performance Baselines
- Stored in `testing/performance/`
- Compared against previous runs
- Alerts on significant regressions

## 🏗️ Building

### Local Build
```bash
pip install build
python -m build
```

### Package Validation
```bash
pip install twine
twine check dist/*
```

## 🚀 Deployment

### Automatic Deployment
- Triggers on `main` branch pushes
- Requires all tests to pass
- Uses production environment protection

### Manual Deployment
```bash
pip install databricks-cli
databricks configure --token
databricks fs cp dist/*.whl dbfs:/FileStore/jars/
```

## 📈 Monitoring

### View Results
1. Go to repository → **Actions** tab
2. Click on workflow run
3. Check individual job logs
4. Download artifacts

### Key Metrics
- **Test Coverage**: Uploaded to Codecov
- **Build Time**: Visible in Actions interface
- **Security Reports**: Available as artifacts
- **Performance Baselines**: Stored in artifacts

## 🐛 Troubleshooting

### Common Issues

#### Tests Not Running
- Check file naming: `test_*.py`
- Verify test directory structure
- Check pytest configuration

#### Security Scan Failures
- Update vulnerable dependencies
- Fix Bandit security issues
- Review security reports

#### Build Failures
- Check `pyproject.toml` syntax
- Verify all dependencies listed
- Review build logs

#### Deployment Failures
- Verify GitHub secrets are set
- Check Databricks connectivity
- Ensure cluster is running

### Debug Commands
```bash
# Run tests locally
pytest testing/unit/ -v

# Check code quality
flake8 scripts/ utils/
black --check scripts/ utils/
isort --check-only scripts/ utils/
mypy scripts/ utils/

# Security check
safety check
bandit -r scripts/ utils/

# Build package
python -m build
```

## ⚡ Performance Tips

### Faster Builds
- Dependencies are cached automatically
- Matrix testing runs in parallel
- Use appropriate test markers

### Cost Optimization
- Matrix testing: 6 jobs per push
- Security scans: Daily (5-10 min)
- Performance tests: Main branch only

### Estimated Costs
- **Public repo**: Free
- **Private repo**: ~$0-20/month (typical usage)

## 📚 Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Databricks CLI Docs](https://docs.databricks.com/dev-tools/cli/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [MyPy Type Checker](https://mypy.readthedocs.io/)

## 🆘 Getting Help

1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Check project README
4. Create an issue in the repository

---

*Last updated: 2024-01-XX*
