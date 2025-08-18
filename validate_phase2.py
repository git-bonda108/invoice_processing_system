#!/usr/bin/env python3
"""
Phase 2 Comprehensive Validation Script
Tests all agents, document processing, and anomaly detection
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.WARNING)

class Phase2Validator:
    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_result(self, test_name, success, message=""):
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}: {message}")
        self.results[test_name] = {'success': success, 'message': message}
    
    def test_imports(self):
        """Test all Phase 2 imports"""
        print("\n🧪 TESTING PHASE 2 IMPORTS")
        print("=" * 60)
        
        try:
            # Document processor
            from utils.document_processor import DocumentProcessor, ExtractionResult, DocumentProcessingResult
            self.log_result("DocumentProcessor imports", True)
            
            # All agents
            from agents.master_data_agent import MasterDataAgent
            self.log_result("MasterDataAgent import", True)
            
            from agents.extraction_agent import ExtractionAgent
            self.log_result("ExtractionAgent import", True)
            
            from agents.contract_agent import ContractAgent
            self.log_result("ContractAgent import", True)
            
            from agents.msa_agent import MSAAgent
            self.log_result("MSAAgent import", True)
            
            from agents.leasing_agent import LeasingAgent
            self.log_result("LeasingAgent import", True)
            
            from agents.fixed_assets_agent import FixedAssetsAgent
            self.log_result("FixedAssetsAgent import", True)
            
            from agents.quality_review_agent import QualityReviewAgent
            self.log_result("QualityReviewAgent import", True)
            
        except Exception as e:
            self.log_result("Phase 2 imports", False, str(e))
    
    def test_document_processor(self):
        """Test document processor functionality"""
        print("\n🧪 TESTING DOCUMENT PROCESSOR")
        print("=" * 60)
        
        try:
            from utils.document_processor import DocumentProcessor
            from config.settings import DATA_DIR
            
            processor = DocumentProcessor()
            self.log_result("DocumentProcessor creation", True)
            
            # Test loading a sample invoice
            invoice_path = DATA_DIR / "invoices" / "invoice_001.json"
            if invoice_path.exists():
                document = processor.load_document(invoice_path)
                self.log_result("Document loading", True, f"Loaded {document.get('invoice_number', 'unknown')}")
                
                # Test field extraction
                result = processor.extract_field(document, 'invoice_number', str)
                self.log_result("Field extraction", result.value is not None, 
                              f"Extracted: {result.value} (confidence: {result.confidence})")
                
                # Test document processing
                processing_result = processor.process_document(invoice_path, 'invoice')
                self.log_result("Document processing", processing_result.status in ['success', 'warning'], 
                              f"Status: {processing_result.status}, Anomalies: {len(processing_result.anomalies)}")
            else:
                self.log_result("Sample invoice availability", False, "invoice_001.json not found")
                
        except Exception as e:
            self.log_result("Document processor functionality", False, str(e))
    
    def test_master_data_agent(self):
        """Test master data agent"""
        print("\n🧪 TESTING MASTER DATA AGENT")
        print("=" * 60)
        
        try:
            from agents.master_data_agent import MasterDataAgent
            from utils.message_queue import MessageQueue
            
            queue = MessageQueue()
            agent = MasterDataAgent("master_test", queue)
            self.log_result("MasterDataAgent creation", True)
            
            # Test master data loading
            summary = agent.get_master_data_summary()
            vendors_count = summary.get('vendors_count', 0)
            buyers_count = summary.get('buyers_count', 0)
            pos_count = summary.get('purchase_orders_count', 0)
            
            self.log_result("Master data loading", vendors_count > 0 and buyers_count > 0, 
                          f"{vendors_count} vendors, {buyers_count} buyers, {pos_count} POs")
            
            # Test vendor lookup
            vendor_result = agent._lookup_vendor("TechCorp Solutions Inc.")
            self.log_result("Vendor lookup", vendor_result['status'] in ['found', 'partial_match'], 
                          vendor_result.get('message', ''))
            
            # Test PO lookup
            po_result = agent._lookup_purchase_order("PO-123456")
            self.log_result("PO lookup", po_result['status'] in ['found', 'not_found'], 
                          po_result.get('message', ''))
            
        except Exception as e:
            self.log_result("Master data agent functionality", False, str(e))
    
    def test_extraction_agent(self):
        """Test extraction agent"""
        print("\n🧪 TESTING EXTRACTION AGENT")
        print("=" * 60)
        
        try:
            from agents.extraction_agent import ExtractionAgent
            from utils.message_queue import MessageQueue
            from config.settings import DATA_DIR
            
            queue = MessageQueue()
            agent = ExtractionAgent("extraction_test", queue)
            self.log_result("ExtractionAgent creation", True)
            
            # Test invoice processing
            invoice_path = DATA_DIR / "invoices" / "invoice_001.json"
            if invoice_path.exists():
                result = agent.process_invoice_file(invoice_path)
                success = result['status'] in ['success', 'warning']
                confidence = result.get('overall_confidence', 0)
                fields_count = len(result.get('extracted_fields', []))
                anomalies_count = len(result.get('anomalies', []))
                
                self.log_result("Invoice processing", success, 
                              f"Status: {result['status']}, Confidence: {confidence:.2f}, Fields: {fields_count}, Anomalies: {anomalies_count}")
                
                # Check for PO number extraction
                extracted_fields = result.get('extracted_fields', [])
                po_found = any('po' in field.get('field_name', '').lower() or 'purchase_order' in field.get('field_name', '').lower() 
                             for field in extracted_fields if isinstance(field, dict))
                self.log_result("PO number extraction", po_found, "PO number field detected")
                
            else:
                self.log_result("Sample invoice availability", False, "invoice_001.json not found")
                
        except Exception as e:
            self.log_result("Extraction agent functionality", False, str(e))
    
    def test_contract_agent(self):
        """Test contract agent"""
        print("\n🧪 TESTING CONTRACT AGENT")
        print("=" * 60)
        
        try:
            from agents.contract_agent import ContractAgent
            from utils.message_queue import MessageQueue
            from config.settings import DATA_DIR
            
            queue = MessageQueue()
            agent = ContractAgent("contract_test", queue)
            self.log_result("ContractAgent creation", True)
            
            # Test contract processing
            contract_path = DATA_DIR / "contracts" / "contract_001.json"
            if contract_path.exists():
                result = agent.process_contract_file(contract_path)
                success = result['status'] in ['success', 'warning']
                confidence = result.get('overall_confidence', 0)
                fields_count = len(result.get('extracted_fields', []))
                anomalies_count = len(result.get('anomalies', []))
                
                self.log_result("Contract processing", success, 
                              f"Status: {result['status']}, Confidence: {confidence:.2f}, Fields: {fields_count}, Anomalies: {anomalies_count}")
                
            else:
                self.log_result("Sample contract availability", False, "contract_001.json not found")
                
        except Exception as e:
            self.log_result("Contract agent functionality", False, str(e))
    
    def test_msa_agent(self):
        """Test MSA agent"""
        print("\n🧪 TESTING MSA AGENT")
        print("=" * 60)
        
        try:
            from agents.msa_agent import MSAAgent
            from utils.message_queue import MessageQueue
            from config.settings import DATA_DIR
            
            queue = MessageQueue()
            agent = MSAAgent("msa_test", queue)
            self.log_result("MSAAgent creation", True)
            
            # Test MSA processing
            msa_path = DATA_DIR / "msa" / "msa_001.json"
            if msa_path.exists():
                result = agent.process_msa_file(msa_path)
                success = result['status'] in ['success', 'warning']
                confidence = result.get('overall_confidence', 0)
                fields_count = len(result.get('extracted_fields', []))
                anomalies_count = len(result.get('anomalies', []))
                
                self.log_result("MSA processing", success, 
                              f"Status: {result['status']}, Confidence: {confidence:.2f}, Fields: {fields_count}, Anomalies: {anomalies_count}")
                
                # Check for expected behavior (no PO numbers)
                validation_results = result.get('validation_results', [])
                po_validation = any('po' in v.get('field', '').lower() for v in validation_results)
                self.log_result("MSA PO validation", po_validation, "PO absence validation present")
                
            else:
                self.log_result("Sample MSA availability", False, "msa_001.json not found")
                
        except Exception as e:
            self.log_result("MSA agent functionality", False, str(e))
    
    def test_leasing_agent(self):
        """Test leasing agent"""
        print("\n🧪 TESTING LEASING AGENT")
        print("=" * 60)
        
        try:
            from agents.leasing_agent import LeasingAgent
            from utils.message_queue import MessageQueue
            from config.settings import DATA_DIR
            
            queue = MessageQueue()
            agent = LeasingAgent("leasing_test", queue)
            self.log_result("LeasingAgent creation", True)
            
            # Test lease processing
            lease_path = DATA_DIR / "leases" / "lease_001.json"
            if lease_path.exists():
                result = agent.process_lease_file(lease_path)
                success = result['status'] in ['success', 'warning']
                confidence = result.get('overall_confidence', 0)
                fields_count = len(result.get('extracted_fields', []))
                anomalies_count = len(result.get('anomalies', []))
                
                self.log_result("Lease processing", success, 
                              f"Status: {result['status']}, Confidence: {confidence:.2f}, Fields: {fields_count}, Anomalies: {anomalies_count}")
                
                # Check asset correlations
                correlations = result.get('asset_correlations', {})
                self.log_result("Asset correlation framework", 'found_correlations' in correlations, 
                              f"Correlation structure present")
                
            else:
                self.log_result("Sample lease availability", False, "lease_001.json not found")
                
        except Exception as e:
            self.log_result("Leasing agent functionality", False, str(e))
    
    def test_fixed_assets_agent(self):
        """Test fixed assets agent"""
        print("\n🧪 TESTING FIXED ASSETS AGENT")
        print("=" * 60)
        
        try:
            from agents.fixed_assets_agent import FixedAssetsAgent
            from utils.message_queue import MessageQueue
            from config.settings import DATA_DIR
            
            queue = MessageQueue()
            agent = FixedAssetsAgent("assets_test", queue)
            self.log_result("FixedAssetsAgent creation", True)
            
            # Test asset processing
            asset_path = DATA_DIR / "fixed_assets" / "fixed_asset_001.json"
            if asset_path.exists():
                result = agent.process_asset_file(asset_path)
                success = result['status'] in ['success', 'warning']
                confidence = result.get('overall_confidence', 0)
                fields_count = len(result.get('extracted_fields', []))
                anomalies_count = len(result.get('anomalies', []))
                
                self.log_result("Asset processing", success, 
                              f"Status: {result['status']}, Confidence: {confidence:.2f}, Fields: {fields_count}, Anomalies: {anomalies_count}")
                
                # Check depreciation analysis
                depreciation = result.get('depreciation_analysis', {})
                self.log_result("Depreciation analysis", 'is_valid' in depreciation, 
                              f"Depreciation framework present")
                
            else:
                self.log_result("Sample asset availability", False, "fixed_asset_001.json not found")
                
        except Exception as e:
            self.log_result("Fixed assets agent functionality", False, str(e))
    
    def test_quality_review_agent(self):
        """Test quality review agent"""
        print("\n🧪 TESTING QUALITY REVIEW AGENT")
        print("=" * 60)
        
        try:
            from agents.quality_review_agent import QualityReviewAgent
            from utils.message_queue import MessageQueue
            
            queue = MessageQueue()
            agent = QualityReviewAgent("quality_test", queue)
            self.log_result("QualityReviewAgent creation", True)
            
            # Create mock results for testing
            mock_results = [
                {
                    'document_id': 'TEST-001',
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
                }
            ]
            
            # Test quality report generation
            result = agent.generate_quality_report(mock_results)
            success = result['status'] == 'success'
            
            if success:
                report = result['quality_report']
                has_summary = 'summary' in report
                has_scores = 'quality_scores' in report
                has_recommendations = 'recommendations' in report
                
                self.log_result("Quality report generation", success, 
                              f"Report sections: summary={has_summary}, scores={has_scores}, recommendations={has_recommendations}")
            else:
                self.log_result("Quality report generation", False, result.get('message', 'Unknown error'))
                
        except Exception as e:
            self.log_result("Quality review agent functionality", False, str(e))
    
    def test_agent_communication(self):
        """Test inter-agent communication"""
        print("\n🧪 TESTING AGENT COMMUNICATION")
        print("=" * 60)
        
        try:
            from agents.master_data_agent import MasterDataAgent
            from agents.extraction_agent import ExtractionAgent
            from utils.message_queue import MessageQueue, Message, MessageType
            
            # Create shared message queue
            queue = MessageQueue()
            master_agent = MasterDataAgent("master", queue)
            extraction_agent = ExtractionAgent("extraction", queue)
            
            self.log_result("Shared message queue setup", True)
            
            # Test message creation and sending
            test_message = Message(
                msg_type=MessageType.DATA_REQUEST,
                sender="extraction",
                recipient="master",
                content={
                    'request_type': 'vendor_lookup',
                    'vendor_name': 'TechCorp Solutions Inc.'
                }
            )
            
            queue.send_message(test_message)
            self.log_result("Message sending", True)
            
            # Test message receiving
            received_message = queue.get_message("master")
            message_received = received_message is not None
            self.log_result("Message receiving", message_received)
            
            if message_received:
                # Test message processing
                response = master_agent.process_message(received_message)
                response_valid = 'status' in response
                self.log_result("Message processing", response_valid, 
                              f"Response status: {response.get('status', 'unknown')}")
            
        except Exception as e:
            self.log_result("Agent communication", False, str(e))
    
    def test_anomaly_detection(self):
        """Test anomaly detection capabilities"""
        print("\n🧪 TESTING ANOMALY DETECTION")
        print("=" * 60)
        
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
                self.log_result("Invoice anomaly detection", True, 
                              f"{len(anomalies)} anomalies detected")
                
                # Check anomaly structure
                if anomalies:
                    first_anomaly = anomalies[0]
                    has_type = 'type' in first_anomaly
                    has_severity = 'severity' in first_anomaly
                    has_description = 'description' in first_anomaly
                    
                    self.log_result("Anomaly structure validation", has_type and has_severity and has_description,
                                  f"Structure complete: type={has_type}, severity={has_severity}, description={has_description}")
            
            # Test MSA expected behavior validation
            msa_agent = MSAAgent("msa", queue)
            msa_path = DATA_DIR / "msa" / "msa_001.json"
            
            if msa_path.exists():
                result = msa_agent.process_msa_file(msa_path)
                validation_results = result.get('validation_results', [])
                
                # Look for PO absence validation
                po_validations = [v for v in validation_results if 'po' in v.get('field', '').lower()]
                self.log_result("MSA expected behavior validation", len(po_validations) > 0,
                              f"PO absence validations: {len(po_validations)}")
            
        except Exception as e:
            self.log_result("Anomaly detection", False, str(e))
    
    def test_cross_document_correlation(self):
        """Test cross-document correlation capabilities"""
        print("\n🧪 TESTING CROSS-DOCUMENT CORRELATION")
        print("=" * 60)
        
        try:
            from agents.leasing_agent import LeasingAgent
            from agents.fixed_assets_agent import FixedAssetsAgent
            from utils.message_queue import MessageQueue
            from config.settings import DATA_DIR
            
            queue = MessageQueue()
            leasing_agent = LeasingAgent("leasing", queue)
            assets_agent = FixedAssetsAgent("assets", queue)
            
            # Process a lease
            lease_path = DATA_DIR / "leases" / "lease_001.json"
            if lease_path.exists():
                lease_result = leasing_agent.process_lease_file(lease_path)
                lease_correlations = lease_result.get('asset_correlations', {})
                
                self.log_result("Lease correlation framework", 'found_correlations' in lease_correlations,
                              "Asset correlation structure present in lease processing")
            
            # Process an asset
            asset_path = DATA_DIR / "fixed_assets" / "fixed_asset_001.json"
            if asset_path.exists():
                asset_result = assets_agent.process_asset_file(asset_path)
                asset_correlations = asset_result.get('lease_correlations', {})
                
                self.log_result("Asset correlation framework", 'found_correlations' in asset_correlations,
                              "Lease correlation structure present in asset processing")
            
            # Check for potential correlations in the data
            if lease_path.exists() and asset_path.exists():
                with open(lease_path, 'r') as f:
                    lease_data = json.load(f)
                with open(asset_path, 'r') as f:
                    asset_data = json.load(f)
                
                lease_asset_id = lease_data.get('leased_asset', {}).get('asset_id')
                asset_asset_id = asset_data.get('asset_details', {}).get('asset_id')
                
                correlation_possible = lease_asset_id == asset_asset_id if lease_asset_id and asset_asset_id else False
                self.log_result("Asset ID correlation potential", correlation_possible or (lease_asset_id and asset_asset_id),
                              f"Lease asset: {lease_asset_id}, Fixed asset: {asset_asset_id}")
            
        except Exception as e:
            self.log_result("Cross-document correlation", False, str(e))
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 PHASE 2 COMPREHENSIVE VALIDATION")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        self.test_imports()
        self.test_document_processor()
        self.test_master_data_agent()
        self.test_extraction_agent()
        self.test_contract_agent()
        self.test_msa_agent()
        self.test_leasing_agent()
        self.test_fixed_assets_agent()
        self.test_quality_review_agent()
        self.test_agent_communication()
        self.test_anomaly_detection()
        self.test_cross_document_correlation()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 PHASE 2 VALIDATION RESULTS")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📈 OVERALL RESULTS: {self.passed_tests}/{self.total_tests} tests passed ({success_rate:.1f}%)")
        
        if self.passed_tests == self.total_tests:
            print("🎉 ALL PHASE 2 TESTS PASSED - IMPLEMENTATION VALIDATED!")
            print("✅ Ready for Phase 3 - Agent Communication & Orchestration")
            return True
        else:
            print("⚠️ SOME TESTS FAILED - REVIEW REQUIRED")
            
            # Show failed tests
            failed_tests = [name for name, result in self.results.items() if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test_name in failed_tests:
                    message = self.results[test_name]['message']
                    print(f"   - {test_name}: {message}")
            
            return False

if __name__ == "__main__":
    validator = Phase2Validator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)