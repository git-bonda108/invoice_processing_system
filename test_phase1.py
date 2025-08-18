#!/usr/bin/env python3
"""
Phase 1 Comprehensive Testing Script
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all module imports"""
    print("🧪 TESTING MODULE IMPORTS")
    print("-" * 40)
    
    try:
        # Test config imports
        from config.settings import AGENT_CONFIG, MESSAGE_QUEUE_CONFIG, DATA_DIR
        print("✅ Config imports successful")
        
        # Test utils imports
        from utils.message_queue import MessageQueue, Message, MessageType
        from utils.data_synthesizer import DataSynthesizer
        print("✅ Utils imports successful")
        
        # Test agents imports
        from agents.base_agent import BaseAgent, AgentStatus
        print("✅ Agents imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_configuration():
    """Test configuration system"""
    print("\n🧪 TESTING CONFIGURATION SYSTEM")
    print("-" * 40)
    
    try:
        from config.settings import (
            AGENT_CONFIG, MESSAGE_QUEUE_CONFIG, ANOMALY_CONFIG,
            LOGGING_CONFIG, UI_CONFIG, DATA_DIR, LOGS_DIR
        )
        
        # Test agent config
        assert 'default_timeout' in AGENT_CONFIG
        assert 'max_retries' in AGENT_CONFIG
        print("✅ Agent configuration valid")
        
        # Test message queue config
        assert 'max_queue_size' in MESSAGE_QUEUE_CONFIG
        assert 'message_timeout' in MESSAGE_QUEUE_CONFIG
        print("✅ Message queue configuration valid")
        
        # Test data directories
        assert DATA_DIR.exists()
        print(f"✅ Data directory exists: {DATA_DIR}")
        
        # Test logs directory creation
        LOGS_DIR.mkdir(exist_ok=True)
        assert LOGS_DIR.exists()
        print(f"✅ Logs directory exists: {LOGS_DIR}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_message_queue():
    """Test message queue system"""
    print("\n🧪 TESTING MESSAGE QUEUE SYSTEM")
    print("-" * 40)
    
    try:
        from utils.message_queue import MessageQueue, Message, MessageType
        
        # Create message queue
        queue = MessageQueue()
        print("✅ Message queue created")
        
        # Test message creation
        message = Message(
            msg_type=MessageType.TASK_ASSIGNMENT,
            sender="test_sender",
            recipient="test_recipient",
            content={"task": "test_task"},
            priority=1
        )
        print("✅ Message created successfully")
        
        # Test message sending
        queue.send_message(message)
        print("✅ Message sent successfully")
        
        # Test message receiving
        received = queue.get_message("test_recipient")
        assert received is not None
        assert received.content["task"] == "test_task"
        print("✅ Message received successfully")
        
        # Test subscription
        queue.subscribe("test_agent", MessageType.STATUS_UPDATE)
        subscribers = queue.get_subscribers(MessageType.STATUS_UPDATE)
        assert "test_agent" in subscribers
        print("✅ Subscription system working")
        
        return True
        
    except Exception as e:
        print(f"❌ Message queue error: {e}")
        return False

def test_base_agent():
    """Test base agent functionality"""
    print("\n🧪 TESTING BASE AGENT SYSTEM")
    print("-" * 40)
    
    try:
        from agents.base_agent import BaseAgent, AgentStatus
        from utils.message_queue import MessageQueue
        
        # Create message queue
        queue = MessageQueue()
        
        # Create test agent
        class TestAgent(BaseAgent):
            def process_message(self, message):
                return {"status": "processed", "content": message.content}
        
        agent = TestAgent("test_agent", queue)
        print("✅ Test agent created")
        
        # Test agent status
        assert agent.status == AgentStatus.IDLE
        print("✅ Agent status initialized correctly")
        
        # Test agent metrics
        metrics = agent.get_metrics()
        assert "tasks_completed" in metrics
        assert "tasks_failed" in metrics
        print("✅ Agent metrics system working")
        
        # Test agent configuration
        agent.update_config({"test_param": "test_value"})
        assert agent.config["test_param"] == "test_value"
        print("✅ Agent configuration system working")
        
        return True
        
    except Exception as e:
        print(f"❌ Base agent error: {e}")
        return False

def test_data_synthesizer():
    """Test data synthesis system"""
    print("\n🧪 TESTING DATA SYNTHESIZER")
    print("-" * 40)
    
    try:
        from utils.data_synthesizer import DataSynthesizer
        
        # Create synthesizer
        synthesizer = DataSynthesizer()
        print("✅ Data synthesizer created")
        
        # Test invoice generation
        invoice = synthesizer.generate_invoice()
        assert "invoice_number" in invoice
        assert "total_amount" in invoice
        assert "buyers_order_number" in invoice
        print("✅ Invoice generation working")
        
        # Test contract generation
        contract = synthesizer.generate_contract()
        assert "contract_number" in contract
        assert "contract_value" in contract
        assert "purchase_order_number" in contract
        print("✅ Contract generation working")
        
        # Test MSA generation
        msa = synthesizer.generate_msa()
        assert "msa_number" in msa
        assert "purchase_order_number" not in msa  # MSA should not have PO
        print("✅ MSA generation working (correctly excludes PO)")
        
        return True
        
    except Exception as e:
        print(f"❌ Data synthesizer error: {e}")
        return False

def test_sample_data():
    """Test generated sample data"""
    print("\n🧪 TESTING SAMPLE DATA")
    print("-" * 40)
    
    try:
        from config.settings import DATA_DIR
        
        # Test data structure
        data_counts = {
            "invoices": 5,
            "contracts": 3,
            "msa": 1,
            "leases": 3,
            "fixed_assets": 3,
            "master_data": 1
        }
        
        total_files = 0
        for dir_name, expected in data_counts.items():
            dir_path = DATA_DIR / dir_name
            json_files = list(dir_path.glob("*.json"))
            actual = len(json_files)
            total_files += actual
            
            if actual == expected:
                print(f"✅ {dir_name}: {actual}/{expected} files")
            else:
                print(f"❌ {dir_name}: {actual}/{expected} files")
                return False
        
        print(f"✅ Total sample files: {total_files}")
        
        # Test data quality
        # Check invoice structure
        invoice_path = DATA_DIR / "invoices" / "invoice_001.json"
        with open(invoice_path, 'r') as f:
            invoice = json.load(f)
            
        required_fields = [
            "invoice_number", "invoice_date", "total_amount", 
            "buyers_order_number", "vendor", "buyer"
        ]
        
        for field in required_fields:
            assert field in invoice, f"Missing field: {field}"
        
        print("✅ Invoice data structure valid")
        
        # Check master data structure
        master_path = DATA_DIR / "master_data" / "master_data.json"
        with open(master_path, 'r') as f:
            master_data = json.load(f)
        
        required_sections = ["vendors", "buyers", "purchase_orders", "chart_of_accounts"]
        for section in required_sections:
            assert section in master_data, f"Missing section: {section}"
        
        print("✅ Master data structure valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Sample data error: {e}")
        return False

def test_anomaly_detection_setup():
    """Test anomaly detection framework setup"""
    print("\n🧪 TESTING ANOMALY DETECTION SETUP")
    print("-" * 40)
    
    try:
        from config.settings import DATA_DIR
        
        # Load master data
        master_path = DATA_DIR / "master_data" / "master_data.json"
        with open(master_path, 'r') as f:
            master_data = json.load(f)
        
        # Test anomaly patterns
        anomaly_patterns = master_data.get("anomaly_patterns", {})
        assert "expected_po_presence" in anomaly_patterns
        print("✅ Anomaly patterns configured")
        
        # Test PO presence expectations
        po_expectations = anomaly_patterns["expected_po_presence"]
        assert po_expectations["invoices"] == True
        assert po_expectations["contracts"] == True
        assert po_expectations["msa"] == False
        assert po_expectations["leases"] == False
        print("✅ PO presence expectations correct")
        
        # Verify MSA doesn't have PO (expected anomaly)
        msa_path = DATA_DIR / "msa" / "msa_001.json"
        with open(msa_path, 'r') as f:
            msa = json.load(f)
        
        has_po = any(key for key in msa.keys() if 'po' in key.lower() or 'purchase_order' in key.lower())
        assert not has_po, "MSA should not contain PO numbers"
        print("✅ MSA correctly lacks PO numbers (expected)")
        
        # Verify leases don't have PO (expected anomaly)
        lease_path = DATA_DIR / "leases" / "lease_001.json"
        with open(lease_path, 'r') as f:
            lease = json.load(f)
        
        has_po = any(key for key in lease.keys() if 'po' in key.lower() or 'purchase_order' in key.lower())
        assert not has_po, "Lease should not contain PO numbers"
        print("✅ Leases correctly lack PO numbers (expected)")
        
        # Test asset correlations
        lease_assets = set()
        for i in range(1, 4):
            lease_path = DATA_DIR / "leases" / f"lease_{i:03d}.json"
            with open(lease_path, 'r') as f:
                lease = json.load(f)
                asset_id = lease.get('leased_asset', {}).get('asset_id')
                if asset_id:
                    lease_assets.add(asset_id)
        
        fixed_assets = set()
        for i in range(1, 4):
            asset_path = DATA_DIR / "fixed_assets" / f"fixed_asset_{i:03d}.json"
            with open(asset_path, 'r') as f:
                asset = json.load(f)
                asset_id = asset.get('asset_details', {}).get('asset_id')
                if asset_id:
                    fixed_assets.add(asset_id)
        
        matching_assets = lease_assets.intersection(fixed_assets)
        assert len(matching_assets) > 0, "Should have matching asset IDs for lease-to-own scenarios"
        print(f"✅ Found {len(matching_assets)} matching asset IDs (lease-to-own scenarios)")
        
        return True
        
    except Exception as e:
        print(f"❌ Anomaly detection setup error: {e}")
        return False

def test_ui_compatibility():
    """Test UI system compatibility"""
    print("\n🧪 TESTING UI SYSTEM COMPATIBILITY")
    print("-" * 40)
    
    try:
        # Test if streamlit imports work
        import streamlit as st
        print("✅ Streamlit import successful")
        
        # Test pandas for data display
        import pandas as pd
        print("✅ Pandas import successful")
        
        # Test UI configuration
        from config.settings import UI_CONFIG
        assert "page_title" in UI_CONFIG
        assert "page_icon" in UI_CONFIG
        print("✅ UI configuration valid")
        
        # Test data loading function (simulate)
        from config.settings import DATA_DIR
        
        # Simulate loading data for UI
        sample_data = {}
        
        # Load invoices
        invoices = []
        for i in range(1, 6):
            file_path = DATA_DIR / "invoices" / f"invoice_{i:03d}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    invoices.append(json.load(f))
        
        sample_data["invoices"] = invoices
        assert len(sample_data["invoices"]) == 5
        print("✅ UI data loading simulation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ UI compatibility error: {e}")
        return False

def run_comprehensive_tests():
    """Run all Phase 1 tests"""
    print("=" * 60)
    print("🧪 PHASE 1 COMPREHENSIVE TESTING")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration System", test_configuration),
        ("Message Queue System", test_message_queue),
        ("Base Agent System", test_base_agent),
        ("Data Synthesizer", test_data_synthesizer),
        ("Sample Data", test_sample_data),
        ("Anomaly Detection Setup", test_anomaly_detection_setup),
        ("UI Compatibility", test_ui_compatibility)
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
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 OVERALL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - PHASE 1 READY FOR PRODUCTION!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED - REVIEW REQUIRED")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)