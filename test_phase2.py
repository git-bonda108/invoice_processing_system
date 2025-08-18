#!/usr/bin/env python3
"""
Phase 2 Comprehensive Testing Script
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_agent_imports():
    """Test all agent imports"""
    print("🧪 TESTING AGENT IMPORTS")
    print("-" * 40)
    
    try:
        # Test individual agent imports
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
        
        # Test document processor import
        from utils.document_processor import DocumentProcessor, ExtractionResult, DocumentProcessingResult
        print("✅ DocumentProcessor imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_document_processor():
    """Test document processor functionality"""
    print("\n🧪 TESTING DOCUMENT PROCESSOR")
    print("-" * 40)
    
    try:
        from utils.document_processor import DocumentProcessor
        from config.settings import DATA_DIR
        
        processor = DocumentProcessor()
        print("✅ DocumentProcessor created")
        
        # Test loading a sample invoice
        invoice_path = DATA_DIR / "invoices" / "invoice_001.json"
        if invoice_path.exists():
            document = processor.load_document(invoice_path)
            print(f"✅ Document loaded: {document.get('invoice_number', 'unknown')}")
            
            # Test field extraction
            result = processor.extract_field(document, 'invoice_number', str)
            print(f"✅ Field extraction: {result.field_name} = {result.value} (confidence: {result.confidence})")
            
            # Test document processing
            processing_result = processor.process_document(invoice_path, 'invoice')
            print(f"✅ Document processing: {processing_result.status} with {len(processing_result.anomalies)} anomalies")
            
        else:
            print("❌ Sample invoice not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Document processor error: {e}")
        return False

def test_master_data_agent():
    """Test master data agent"""
    print("\n🧪 TESTING MASTER DATA AGENT")
    print("-" * 40)
    
    try:
        from agents.master_data_agent import MasterDataAgent
        from utils.message_queue import MessageQueue, Message, MessageType
        
        # Create message queue and agent
        queue = MessageQueue()
        agent = MasterDataAgent("master_data_test", queue)
        print("✅ MasterDataAgent created")
        
        # Test master data loading
        summary = agent.get_master_data_summary()
        print(f"✅ Master data loaded: {summary['vendors_count']} vendors, {summary['buyers_count']} buyers")
        
        # Test vendor lookup
        vendor_result = agent._lookup_vendor("TechCorp Solutions Inc.")
        print(f"✅ Vendor lookup: {vendor_result['status']} - {vendor_result.get('message', '')}")
        
        # Test PO lookup
        po_result = agent._lookup_purchase_order("PO-123456")
        print(f"✅ PO lookup: {po_result['status']} - {po_result.get('message', '')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Master data agent error: {e}")
        return False

def test_extraction_agent():
    """Test extraction agent"""
    print("\n🧪 TESTING EXTRACTION AGENT")
    print("-" * 40)
    
    try:
        from agents.extraction_agent import ExtractionAgent
        from utils.message_queue import MessageQueue
        from config.settings import DATA_DIR
        
        # Create message queue and agent
        queue = MessageQueue()
        agent = ExtractionAgent("extraction_test", queue)
        print("✅ ExtractionAgent created")
        
        # Test invoice processing
        invoice_path = DATA_DIR / "invoices" / "invoice_001.json"
        if invoice_path.exists():
            result = agent.process_invoice_file(invoice_path)
            print(f"✅ Invoice processing: {result['status']} with confidence {result.get('overall_confidence', 0):.2f}")
            print(f"   Extracted {len(result.get('extracted_fields', []))} fields")
            print(f"   Found {len(result.get('anomalies', []))} anomalies")
        else:
            print("❌ Sample invoice not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Extraction agent error: {e}")
        return False

def test_contract_agent():
    """Test contract agent"""
    print("\n🧪 TESTING CONTRACT AGENT")
    print("-" * 40)
    
    try:
        from agents.contract_agent import ContractAgent
        from utils.message_queue import MessageQueue
        from config.settings import DATA_DIR
        
        # Create message queue and agent
        queue = MessageQueue()
        agent = ContractAgent("contract_test", queue)
        print("✅ ContractAgent created")
        
        # Test contract processing
        contract_path = DATA_DIR / "contracts" / "contract_001.json"
        if contract_path.exists():
            result = agent.process_contract_file(contract_path)
            print(f"✅ Contract processing: {result['status']} with confidence {result.get('overall_confidence', 0):.2f}")
            print(f"   Extracted {len(result.get('extracted_fields', []))} fields")
            print(f"   Found {len(result.get('anomalies', []))} anomalies")
        else:
            print("❌ Sample contract not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Contract agent error: {e}")
        return False

def test_msa_agent():
    """Test MSA agent"""
    print("\n🧪 TESTING MSA AGENT")
    print("-" * 40)
    
    try:
        from agents.msa_agent import MSAAgent
        from utils.message_queue import MessageQueue
        from config.settings import DATA_DIR
        
        # Create message queue and agent
        queue = MessageQueue()
        agent = MSAAgent("msa_test", queue)
        print("✅ MSAAgent created")
        
        # Test MSA processing
        msa_path = DATA_DIR / "msa" / "msa_001.json"
        if msa_path.exists():
            result = agent.process_msa_file(msa_path)
            print(f"✅ MSA processing: {result['status']} with confidence {result.get('overall_confidence', 0):.2f}")
            print(f"   Extracted {len(result.get('extracted_fields', []))} fields")
            print(f"   Found {len(result.get('anomalies', []))} anomalies")
            
            # Check for expected behavior (no PO numbers)
            anomalies = result.get('anomalies', [])
            po_anomalies = [a for a in anomalies if 'po' in a.get('type', '').lower()]
            if not po_anomalies:
                print("✅ MSA correctly has no PO-related anomalies (expected)")
            
        else:
            print("❌ Sample MSA not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ MSA agent error: {e}")
        return False

def test_leasing_agent():
    """Test leasing agent"""
    print("\n🧪 TESTING LEASING AGENT")
    print("-" * 40)
    
    try:
        from agents.leasing_agent import LeasingAgent
        from utils.message_queue import MessageQueue
        from config.settings import DATA_DIR
        
        # Create message queue and agent
        queue = MessageQueue()
        agent = LeasingAgent("leasing_test", queue)
        print("✅ LeasingAgent created")
        
        # Test lease processing
        lease_path = DATA_DIR / "leases" / "lease_001.json"
        if lease_path.exists():
            result = agent.process_lease_file(lease_path)
            print(f"✅ Lease processing: {result['status']} with confidence {result.get('overall_confidence', 0):.2f}")
            print(f"   Extracted {len(result.get('extracted_fields', []))} fields")
            print(f"   Found {len(result.get('anomalies', []))} anomalies")
            
            # Check asset correlations
            correlations = result.get('asset_correlations', {})
            if correlations.get('found_correlations'):
                print(f"✅ Found asset correlations: {correlations['found_correlations']}")
            
        else:
            print("❌ Sample lease not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Leasing agent error: {e}")
        return False

def test_fixed_assets_agent():
    """Test fixed assets agent"""
    print("\n🧪 TESTING FIXED ASSETS AGENT")
    print("-" * 40)
    
    try:
        from agents.fixed_assets_agent import FixedAssetsAgent
        from utils.message_queue import MessageQueue
        from config.settings import DATA_DIR
        
        # Create message queue and agent
        queue = MessageQueue()
        agent = FixedAssetsAgent("fixed_assets_test", queue)
        print("✅ FixedAssetsAgent created")
        
        # Test asset processing
        asset_path = DATA_DIR / "fixed_assets" / "fixed_asset_001.json"
        if asset_path.exists():
            result = agent.process_asset_file(asset_path)
            print(f"✅ Asset processing: {result['status']} with confidence {result.get('overall_confidence', 0):.2f}")
            print(f"   Extracted {len(result.get('extracted_fields', []))} fields")
            print(f"   Found {len(result.get('anomalies', []))} anomalies")
            
            # Check depreciation analysis
            depreciation = result.get('depreciation_analysis', {})
            if depreciation.get('is_valid'):
                print(f"✅ Depreciation analysis: {depreciation.get('method', 'unknown')} method")
            
        else:
            print("❌ Sample asset not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Fixed assets agent error: {e}")
        return False

def test_quality_review_agent():
    """Test quality review agent"""
    print("\n🧪 TESTING QUALITY REVIEW AGENT")
    print("-" * 40)
    
    try:
        from agents.quality_review_agent import QualityReviewAgent
        from utils.message_queue import MessageQueue
        
        # Create message queue and agent
        queue = MessageQueue()
        agent = QualityReviewAgent("quality_review_test", queue)
        print("✅ QualityReviewAgent created")
        
        # Create mock document results for testing
        mock_results = [
            {
                'document_id': 'INV-001',
                'document_type': 'invoice',
                'status': 'success',
                'overall_confidence': 0.95,
                'processing_time': 2.5,
                'extracted_fields': [
                    {'field_name': 'invoice_number', 'value': 'INV-001', 'confidence': 0.98},
                    {'field_name': 'total_amount', 'value': 1000.0, 'confidence': 0.92}
                ],
                'anomalies': [],
                'agent_id': 'extraction_agent'
            },
            {
                'document_id': 'CONT-001',
                'document_type': 'contract',
                'status': 'warning',
                'overall_confidence': 0.82,
                'processing_time': 3.1,
                'extracted_fields': [
                    {'field_name': 'contract_number', 'value': 'CONT-001', 'confidence': 0.85},
                    {'field_name': 'contract_value', 'value': 1050.0, 'confidence': 0.79}
                ],
                'anomalies': [
                    {'type': 'amount_variance', 'severity': 'medium', 'description': 'Amount variance detected'}
                ],
                'agent_id': 'contract_agent'
            }
        ]
        
        # Test quality report generation
        result = agent.generate_quality_report(mock_results)
        print(f"✅ Quality report generated: {result['status']}")
        
        if result['status'] == 'success':
            report = result['quality_report']
            print(f"   Summary: {report['summary']['success_rate']:.1f}% success rate")
            print(f"   Quality score: {report['quality_scores']['overall_score']:.1f}")
            print(f"   Recommendations: {len(report['recommendations'])} items")
        
        return True
        
    except Exception as e:
        print(f"❌ Quality review agent error: {e}")
        return False

def test_agent_communication():
    """Test inter-agent communication"""
    print("\n🧪 TESTING AGENT COMMUNICATION")
    print("-" * 40)
    
    try:
        from agents.master_data_agent import MasterDataAgent
        from agents.extraction_agent import ExtractionAgent
        from utils.message_queue import MessageQueue, Message, MessageType
        
        # Create shared message queue
        queue = MessageQueue()
        
        # Create agents
        master_agent = MasterDataAgent("master_data", queue)
        extraction_agent = ExtractionAgent("extraction", queue)
        
        print("✅ Agents created with shared message queue")
        
        # Test message sending
        test_message = Message(
            msg_type=MessageType.DATA_REQUEST,
            sender="extraction",
            recipient="master_data",
            content={
                'request_type': 'vendor_lookup',
                'vendor_name': 'TechCorp Solutions Inc.'
            }
        )
        
        queue.send_message(test_message)
        print("✅ Message sent to queue")
        
        # Test message receiving
        received_message = queue.get_message("master_data")
        if received_message:
            print("✅ Message received by master data agent")
            
            # Process the message
            response = master_agent.process_message(received_message)
            print(f"✅ Message processed: {response.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent communication error: {e}")
        return False

def test_anomaly_detection():
    """Test anomaly detection across agents"""
    print("\n🧪 TESTING ANOMALY DETECTION")
    print("-" * 40)
    
    try:
        from agents.extraction_agent import ExtractionAgent
        from agents.msa_agent import MSAAgent
        from utils.message_queue import MessageQueue
        from config.settings import DATA_DIR
        
        queue = MessageQueue()
        
        # Test invoice anomaly detection
        extraction_agent = ExtractionAgent("extraction", queue)
        invoice_path = DATA_DIR / "invoices" / "invoice_001.json"
        
        if invoice_path.exists():
            result = extraction_agent.process_invoice_file(invoice_path)
            anomalies = result.get('anomalies', [])
            print(f"✅ Invoice anomaly detection: {len(anomalies)} anomalies found")
            
            for anomaly in anomalies[:3]:  # Show first 3
                print(f"   - {anomaly.get('type', 'unknown')}: {anomaly.get('description', '')}")
        
        # Test MSA anomaly detection (should detect absence of PO numbers as expected)
        msa_agent = MSAAgent("msa", queue)
        msa_path = DATA_DIR / "msa" / "msa_001.json"
        
        if msa_path.exists():
            result = msa_agent.process_msa_file(msa_path)
            anomalies = result.get('anomalies', [])
            print(f"✅ MSA anomaly detection: {len(anomalies)} anomalies found")
            
            # Check for expected behavior validation
            validations = result.get('validation_results', [])
            po_validations = [v for v in validations if 'po' in v.get('field', '').lower()]
            if po_validations:
                print("✅ MSA correctly validates PO number absence")
        
        return True
        
    except Exception as e:
        print(f"❌ Anomaly detection error: {e}")
        return False

def run_comprehensive_tests():
    """Run all Phase 2 tests"""
    print("=" * 60)
    print("🧪 PHASE 2 COMPREHENSIVE TESTING")
    print("=" * 60)
    
    tests = [
        ("Agent Imports", test_agent_imports),
        ("Document Processor", test_document_processor),
        ("Master Data Agent", test_master_data_agent),
        ("Extraction Agent", test_extraction_agent),
        ("Contract Agent", test_contract_agent),
        ("MSA Agent", test_msa_agent),
        ("Leasing Agent", test_leasing_agent),
        ("Fixed Assets Agent", test_fixed_assets_agent),
        ("Quality Review Agent", test_quality_review_agent),
        ("Agent Communication", test_agent_communication),
        ("Anomaly Detection", test_anomaly_detection)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PHASE 2 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 OVERALL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL PHASE 2 TESTS PASSED - READY FOR PHASE 3!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED - REVIEW REQUIRED")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)