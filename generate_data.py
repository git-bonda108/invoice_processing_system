#!/usr/bin/env python3
"""
Script to generate sample documents for the Invoice Processing System
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to the project directory
os.chdir(project_root)

from utils.data_synthesizer import DataSynthesizer
from config.settings import DATA_DIR

def main():
    """Generate all sample documents"""
    print("🚀 Starting document generation...")
    print(f"📁 Data directory: {DATA_DIR}")
    
    # Create data synthesizer
    synthesizer = DataSynthesizer(DATA_DIR)
    
    # Generate all documents
    synthesizer.generate_all_documents()
    
    print("\n📊 Document generation summary:")
    print("  ✅ 5 Invoice documents")
    print("  ✅ 3 Contract documents") 
    print("  ✅ 1 Master Service Agreement")
    print("  ✅ 3 Lease agreements")
    print("  ✅ 3 Fixed asset agreements")
    print("  ✅ 1 Master data file")
    print("\n🎉 All documents generated successfully!")
    print("\n📝 Next steps:")
    print("  1. Review generated documents in the data/ directory")
    print("  2. Run the main application: python main.py")
    print("  3. Access the Streamlit UI for processing")

if __name__ == "__main__":
    main()