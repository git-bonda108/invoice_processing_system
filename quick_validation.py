#!/usr/bin/env python3
"""
Quick Phase 2 Validation - Check Implementation Status
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_file_structure():
    """Check if all Phase 2 files exist"""
    print("📁 CHECKING FILE STRUCTURE")
    print("=" * 40)
    
    required_files = [
        "agents/master_data_agent.py",
        "agents/extraction_agent.py", 
        "agents/contract_agent.py",
        "agents/msa_agent.py",
        "agents/leasing_agent.py",
        "agents/fixed_assets_agent.py",
        "agents/quality_review_agent.py",
        "utils/document_processor.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist

def test_basic_imports():
    """Test basic imports"""
    print("\n🧪 TESTING BASIC IMPORTS")
    print("=" * 40)
    
    try:
        from utils.document_processor import DocumentProcessor
        print("✅ DocumentProcessor import successful")
        
        from agents.master_data_agent import MasterDataAgent
        print("✅ MasterDataAgent import successful")
        
        from agents.extraction_agent import ExtractionAgent
        print("✅ ExtractionAgent import successful")
        
        from agents.quality_review_agent import QualityReviewAgent
        print("✅ QualityReviewAgent import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_sample_data():
    """Check sample data availability"""
    print("\n📄 CHECKING SAMPLE DATA")
    print("=" * 40)
    
    from config.settings import DATA_DIR
    
    data_types = ["invoices", "contracts", "msa", "leases", "fixed_assets", "master_data"]
    all_data_present = True
    
    for data_type in data_types:
        data_dir = DATA_DIR / data_type
        if data_dir.exists():
            files = list(data_dir.glob("*.json"))
            print(f"✅ {data_type}: {len(files)} files")
        else:
            print(f"❌ {data_type}: directory not found")
            all_data_present = False
    
    return all_data_present

def test_basic_functionality():
    """Test basic functionality"""
    print("\n⚙️ TESTING BASIC FUNCTIONALITY")
    print("=" * 40)
    
    try:
        from utils.document_processor import DocumentProcessor
        from utils.message_queue import MessageQueue
        from agents.master_data_agent import MasterDataAgent
        
        # Test document processor
        processor = DocumentProcessor()
        print("✅ DocumentProcessor created")
        
        # Test message queue
        queue = MessageQueue()
        print("✅ MessageQueue created")
        
        # Test agent creation
        agent = MasterDataAgent("test", queue)
        print("✅ MasterDataAgent created")
        
        # Test master data loading
        summary = agent.get_master_data_summary()
        vendors = summary.get('vendors_count', 0)
        buyers = summary.get('buyers_count', 0)
        print(f"✅ Master data: {vendors} vendors, {buyers} buyers")
        
        return True
    except Exception as e:
        print(f"❌ Functionality error: {e}")
        return False

def main():
    print("🚀 PHASE 2 QUICK VALIDATION")
    print("=" * 50)
    
    tests = [
        ("File Structure", check_file_structure),
        ("Basic Imports", test_basic_imports),
        ("Sample Data", test_sample_data),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 PHASE 2 VALIDATION SUCCESSFUL!")
        print("✅ Ready for comprehensive testing")
        return True
    else:
        print("⚠️ SOME ISSUES FOUND - REVIEW NEEDED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)