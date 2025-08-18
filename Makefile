# Makefile for Invoice Processing System
# Provides convenient commands for common development tasks

.PHONY: help setup install install-dev clean test run dashboard lint format check-env

# Default target
help:
	@echo "🤖 Invoice Processing System - Development Commands"
	@echo "=================================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup          - Create virtual environment and install dependencies"
	@echo "  install        - Install production dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo ""
	@echo "Application Commands:"
	@echo "  run            - Run the main application"
	@echo "  dashboard      - Launch the Streamlit dashboard directly"
	@echo ""
	@echo "Development Commands:"
	@echo "  test           - Run all tests"
	@echo "  lint           - Run code linting (flake8)"
	@echo "  format         - Format code with black and isort"
	@echo "  check-env      - Check virtual environment status"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  clean          - Clean up temporary files and caches"
	@echo ""
	@echo "💡 Tip: Make sure to activate your virtual environment first!"

# Setup virtual environment and install dependencies
setup:
	@echo "🚀 Setting up development environment..."
	python setup_venv.py

# Install production dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt

# Run the main application
run:
	python main.py

# Launch dashboard directly
dashboard:
	python launch_dashboard.py

# Run tests
test:
	python -m pytest tests/ -v --cov=. --cov-report=html

# Run linting
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Format code
format:
	black . --line-length=100
	isort . --profile=black

# Check virtual environment status
check-env:
	@python -c "import sys; print('✅ Virtual environment active' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '❌ No virtual environment detected')"
	@python -c "import os; print(f'📁 Virtual env path: {os.environ.get(\"VIRTUAL_ENV\", \"Not set\")}')"

# Clean up temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.log" -delete