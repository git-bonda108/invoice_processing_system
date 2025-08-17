"""
Configuration settings for the Agentic AI Invoice Processing System
"""
import os
from pathlib import Path
from typing import Dict, Any

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
TEMP_DIR = PROJECT_ROOT / "temp"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# AI Configuration
AI_CONFIG = {
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
    "default_model": "gpt-4",
    "fallback_model": "claude-3-sonnet-20240229",
    "max_tokens": 4000,
    "temperature": 0.1,
    "timeout": 30
}

# Agent Configuration
AGENT_CONFIG = {
    "extraction_agent": {
        "name": "Invoice Extraction Agent",
        "description": "Extracts and validates invoice data",
        "max_retries": 3,
        "timeout": 60,
        "confidence_threshold": 0.85
    },
    "contract_agent": {
        "name": "Contract Analysis Agent",
        "description": "Analyzes contracts and validates PO references",
        "max_retries": 3,
        "timeout": 90,
        "confidence_threshold": 0.80
    },
    "msa_agent": {
        "name": "MSA Analysis Agent",
        "description": "Analyzes Master Service Agreements",
        "max_retries": 3,
        "timeout": 90,
        "confidence_threshold": 0.80
    },
    "leasing_agent": {
        "name": "Leasing Analysis Agent",
        "description": "Analyzes lease agreements",
        "max_retries": 3,
        "timeout": 90,
        "confidence_threshold": 0.80
    },
    "fixed_assets_agent": {
        "name": "Fixed Assets Analysis Agent",
        "description": "Analyzes fixed asset agreements",
        "max_retries": 3,
        "timeout": 90,
        "confidence_threshold": 0.80
    },
    "master_data_agent": {
        "name": "Master Data Validation Agent",
        "description": "Validates data against master records",
        "max_retries": 3,
        "timeout": 60,
        "confidence_threshold": 0.90
    },
    "manager_agent": {
        "name": "Workflow Manager Agent",
        "description": "Orchestrates the entire workflow",
        "max_retries": 5,
        "timeout": 120,
        "confidence_threshold": 0.95
    },
    "quality_review_agent": {
        "name": "Quality Review Agent",
        "description": "Performs final validation and anomaly detection",
        "max_retries": 3,
        "timeout": 90,
        "confidence_threshold": 0.95
    },
    "learning_agent": {
        "name": "Learning Agent",
        "description": "Handles human feedback and continuous improvement",
        "max_retries": 3,
        "timeout": 60,
        "confidence_threshold": 0.85
    }
}

# Workflow Configuration
WORKFLOW_CONFIG = {
    "max_iterations": 5,
    "batch_size": 10,
    "parallel_processing": True,
    "auto_escalation": True,
    "quality_gates": {
        "extraction": 0.85,
        "validation": 0.80,
        "final": 0.90
    }
}

# UI Configuration
UI_CONFIG = {
    "page_title": "🤖 Agentic AI - Invoice Processing Dashboard",
    "page_icon": "🤖",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "refresh_interval": 2000,  # milliseconds
    "max_messages": 100,
    "auto_refresh": True
}

# Message Queue Configuration
MESSAGE_QUEUE_CONFIG = {
    "max_queue_size": 1000,
    "message_ttl": 3600,  # seconds
    "retry_delay": 5,  # seconds
    "max_retries": 3
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOGS_DIR / "system.log",
    "max_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5
}

# Anomaly Detection Configuration
ANOMALY_CONFIG = {
    "po_mismatch_threshold": 0.8,
    "amount_variance_threshold": 0.15,
    "date_variance_threshold": 30,  # days
    "vendor_mismatch_threshold": 0.9,
    "confidence_weight": 0.6,
    "historical_weight": 0.4
}

# Data Generation Configuration
DATA_GENERATION_CONFIG = {
    "num_invoices": 5,
    "num_contracts": 3,
    "num_msa": 1,
    "num_leases": 3,
    "num_fixed_assets": 3,
    "anomaly_rate": 0.3,  # 30% of documents will have anomalies
    "date_range": {
        "start": "2024-01-01",
        "end": "2024-12-31"
    }
}