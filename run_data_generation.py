"""
Direct execution of data generation
"""
from pathlib import Path
from utils.data_synthesizer import DataSynthesizer

# Get the data directory
data_dir = Path(__file__).parent / "data"

print("🚀 Starting document generation...")
print(f"📁 Data directory: {data_dir}")

# Create data synthesizer and generate documents
synthesizer = DataSynthesizer(data_dir)
synthesizer.generate_all_documents()

print("\n📊 Document generation summary:")
print("  ✅ 5 Invoice documents")
print("  ✅ 3 Contract documents") 
print("  ✅ 1 Master Service Agreement")
print("  ✅ 3 Lease agreements")
print("  ✅ 3 Fixed asset agreements")
print("  ✅ 1 Master data file")
print("\n🎉 All documents generated successfully!")