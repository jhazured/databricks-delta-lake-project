#!/bin/bash
# Script to run the exact same checks as GitHub Actions CI

echo "🔍 Running CI-style data quality checks..."

# Activate virtual environment
source venv/bin/activate

echo "📋 1. Syntax error checks (flake8 E9,F63,F7,F82)"
python -m flake8 utils/ scripts/ api/ --count --select=E9,F63,F7,F82 --show-source --statistics

echo "📋 2. Code complexity and style (flake8)"
python -m flake8 utils/ scripts/ api/ --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

echo "📋 3. Code formatting (black)"
python -m black --check utils/ scripts/ api/

echo "📋 4. Import sorting (isort)"
python -m isort --check-only utils/ scripts/ api/

echo "📋 5. Type checking (mypy)"
python -m mypy utils/ scripts/ api/

echo "📋 6. Code analysis (pylint)"
python -m pylint utils/ scripts/ api/ --disable=C0114,C0116,W1203,C0103,W0707,C0209,W0718,R0903,R1705,R0902,R0914,W1514,W0612,R0801 --score=y --fail-under=8.0

echo "📋 7. Documentation style (pydocstyle)"
python -m pydocstyle utils/ scripts/ api/ --count

echo "📋 8. Dead code detection (vulture)"
python -m vulture utils/ scripts/ api/ --min-confidence 70 --exclude api/main.py

echo "📋 9. Code complexity (radon)"
python -m radon cc utils/ scripts/ api/ --min B --show-complexity

echo "✅ All CI checks completed!"
