#!/usr/bin/env python3
"""
Quick Phase 2 Import and Basic Functionality Test
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all Phase 2 imports"""
    print("🧪 TESTING PHASE 2 IMPORTS")
    print("=" * 50)
    
    try:
        # Test document processor
        from utils.document_processor import DocumentProcessor, ExtractionResult, DocumentProcessingResult
        print("✅ DocumentProcessor imports successful")
        
        # Test all agents
        from agents.master_data_agent import MasterDataAgent
        print("✅ MasterDataAgent import successful")
        
        from agents.extraction_agent import ExtractionAgent
        print("✅ ExtractionAgent import successful")
        
        from agents.contract_agent import ContractAgent
        print("✅ ContractAgent import successful")
        
        from agents.msa_agent import MSAAgent
        print("✅ MSAAgent import successful")
        
        from agents.leasing_agent import LeasingAgent
        print("✅ LeasingAgent import successful")
        
        from agents.fixed_assets_agent import FixedAssetsAgent
        print("✅ FixedAssetsAgent import successful")
        
        from agents.quality_review_agent import QualityReviewAgent
        print("✅ QualityReviewAgent import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality of key components"""
    print("\n🧪 TESTING BASIC FUNCTIONALITY")
    print("=" * 50)
    
    try:
        from utils.document_processor import DocumentProcessor
        from utils.message_queue import MessageQueue
        from agents.master_data_agent import MasterDataAgent
        from config.settings import DATA_DIR
        
        # Test document processor
        processor = DocumentProcessor()
        print("✅ DocumentProcessor created")
        
        # Test message queue
        queue = MessageQueue()
        print("✅ MessageQueue created")
        
        # Test agent creation
        agent = MasterDataAgent("test_agent", queue)
        print("✅ MasterDataAgent created")
        
        # Test master data loading
        summary = agent.get_master_data_summary()
        print(f"✅ Master data loaded: {summary['vendors_count']} vendors, {summary['buyers_count']} buyers")
        
        # Test document loading
        invoice_path = DATA_DIR / "invoices" / "invoice_001.json"
        if invoice_path.exists():
            document = processor.load_document(invoice_path)
            print(f"✅ Document loaded: {document.get('invoice_number', 'unknown')}")
        else:
            print("❌ Sample invoice not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sample_processing():
    """Test processing of sample documents"""
    print("\n🧪 TESTING SAMPLE DOCUMENT PROCESSING")
    print("=" * 50)
    
    try:
        from agents.extraction_agent import ExtractionAgent
        from agents.master_data_agent import MasterDataAgent
        from utils.message_queue import MessageQueue
        from config.settings import DATA_DIR
        
        # Create agents
        queue = MessageQueue()
        extraction_agent = ExtractionAgent("extraction", queue)
        master_agent = MasterDataAgent("master", queue)
        
        # Test invoice processing
        invoice_path = DATA_DIR / "invoices" / "invoice_001.json"
        if invoice_path.exists():
            result = extraction_agent.process_invoice_file(invoice_path)
            print(f"✅ Invoice processed: {result['status']} (confidence: {result.get('overall_confidence', 0):.2f})")
            print(f"   Fields extracted: {len(result.get('extracted_fields', []))}")
            print(f"   Anomalies found: {len(result.get('anomalies', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Processing error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 PHASE 2 QUICK VALIDATION TEST")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Sample Processing", test_sample_processing)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 QUICK TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 PHASE 2 QUICK TEST PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED - DETAILED REVIEW NEEDED")