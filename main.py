#!/usr/bin/env python3
"""
Main entry point for the Agentic AI Invoice Processing System
"""
import asyncio
import logging
import sys
from pathlib import Path
import subprocess

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import LOGGING_CONFIG
from utils.data_synthesizer import DataSynthesizer

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, LOGGING_CONFIG["level"]),
        format=LOGGING_CONFIG["format"],
        handlers=[
            logging.FileHandler(LOGGING_CONFIG["file"]),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main function"""
    print("🤖 Agentic AI - Invoice Processing & Anomaly Detection System")
    print("=" * 70)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Agentic AI System")
    
    try:
        # Generate sample data
        print("\n📊 Generating sample data...")
        synthesizer = DataSynthesizer()
        data_summary = synthesizer.generate_all_data()
        
        print(f"\n✅ Data generation completed:")
        for data_type, count in data_summary.items():
            print(f"   - {data_type}: {count}")
        
        print(f"\n🚀 System ready! Launching UI...")
        try:
            subprocess.run(["streamlit", "run", "ui/streamlit_app.py"], check=True)
        except FileNotFoundError:
            logger.error("'streamlit' command not found. Please ensure Streamlit is installed and in your PATH.")
            print("❌ Error: 'streamlit' command not found. Please ensure Streamlit is installed.")
            print("You can install it with: pip install streamlit")
            return 1
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to launch Streamlit UI: {e}")
            print(f"❌ Error launching Streamlit UI: {e}")
            return 1
        
    except Exception as e:
        logger.error(f"Failed to start system: {e}")
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())