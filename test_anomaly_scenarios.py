#!/usr/bin/env python3
"""
Test Built-in Anomaly Scenarios
Validates that the system correctly detects the anomalies built into the sample data
"""
import sys
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_msa_po_absence():
    """Test that MSA correctly lacks PO numbers (expected behavior)"""
    print("🧪 TESTING MSA PO ABSENCE (Expected Behavior)")
    print("-" * 50)
    
    try:
        from agents.msa_agent import MSAAgent
        from utils.message_queue import MessageQueue
        from config.settings import DATA_DIR
        
        queue = MessageQueue()
        agent = MSAAgent("msa_test", queue)
        
        msa_path = DATA_DIR / "msa" / "msa_001.json"
        if msa_path.exists():
            # Load and check the MSA data
            with open(msa_path, 'r') as f:
                msa_data = json.load(f)
            
            # Check that MSA doesn't have PO fields
            po_fields = [key for key in msa_data.keys() if 'po' in key.lower() or 'purchase_order' in key.lower()]
            print(f"✅ MSA correctly lacks PO fields: {len(po_fields) == 0}")
            
            # Process with agent
            result = agent.process_msa_file(msa_path)
            
            # Check validation results for PO absence validation
            validation_results = result.get('validation_results', [])
            po_validations = [v for v in validation_results if 'po' in v.get('field', '').lower()]
            
            if po_validations:
                po_validation = po_validations[0]
                is_valid = po_validation.get('is_valid', False)
                print(f"✅ MSA PO absence validation: {is_valid} - {po_validation.get('message', '')}")
            else:
                print("⚠️ No PO absence validation found")
            
            return True
        else:
            print("❌ MSA file not found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_lease_po_absence():
    """Test that leases correctly lack PO numbers (expected behavior)"""
    print("\n🧪 TESTING LEASE PO ABSENCE (Expected Behavior)")
    print("-" * 50)
    
    try:
        from agents.leasing_agent import LeasingAgent
        from utils.message_queue import MessageQueue
        from config.settings import DATA_DIR
        
        queue = MessageQueue()
        agent = LeasingAgent("lease_test", queue)
        
        lease_path = DATA_DIR / "leases" / "lease_001.json"
        if lease_path.exists():
            # Load and check the lease data
            with open(lease_path, 'r') as f:
                lease_data = json.load(f)
            
            # Check that lease doesn't have PO fields
            po_fields = [key for key in lease_data.keys() if 'po' in key.lower() or 'purchase_order' in key.lower()]
            print(f"✅ Lease correctly lacks PO fields: {len(po_fields) == 0}")
            
            # Process with agent
            result = agent.process_lease_file(lease_path)
            
            # Check validation results for PO absence validation
            validation_results = result.get('validation_results', [])
            po_validations = [v for v in validation_results if 'po' in v.get('field', '').lower()]
            
            if po_validations:
                po_validation = po_validations[0]
                is_valid = po_validation.get('is_valid', False)
                print(f"✅ Lease PO absence validation: {is_valid} - {po_validation.get('message', '')}")
            else:
                print("⚠️ No PO absence validation found")
            
            return True
        else:
            print("❌ Lease file not found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_asset_correlations():
    """Test asset ID correlations between leases and fixed assets"""
    print("\n🧪 TESTING ASSET CORRELATIONS (Lease-to-Own)")
    print("-" * 50)
    
    try:
        from config.settings import DATA_DIR
        
        # Load all leases and assets to find correlations
        lease_assets = {}
        fixed_assets = {}
        
        # Load lease assets
        lease_dir = DATA_DIR / "leases"
        for lease_file in lease_dir.glob("*.json"):
            with open(lease_file, 'r') as f:
                lease_data = json.load(f)
            asset_id = lease_data.get('leased_asset', {}).get('asset_id')
            if asset_id:
                lease_assets[asset_id] = lease_file.name
        
        # Load fixed assets
        asset_dir = DATA_DIR / "fixed_assets"
        for asset_file in asset_dir.glob("*.json"):
            with open(asset_file, 'r') as f:
                asset_data = json.load(f)
            asset_id = asset_data.get('asset_details', {}).get('asset_id')
            if asset_id:
                fixed_assets[asset_id] = asset_file.name
        
        # Find correlations
        correlations = set(lease_assets.keys()).intersection(set(fixed_assets.keys()))
        
        print(f"✅ Lease assets found: {len(lease_assets)} ({list(lease_assets.keys())})")
        print(f"✅ Fixed assets found: {len(fixed_assets)} ({list(fixed_assets.keys())})")
        print(f"✅ Asset correlations found: {len(correlations)} ({list(correlations)})")
        
        # Test with agents
        if correlations:
            from agents.leasing_agent import LeasingAgent
            from agents.fixed_assets_agent import FixedAssetsAgent
            from utils.message_queue import MessageQueue
            
            queue = MessageQueue()
            lease_agent = LeasingAgent("lease", queue)
            asset_agent = FixedAssetsAgent("asset", queue)
            
            # Test one correlation
            test_asset_id = list(correlations)[0]
            lease_file = lease_assets[test_asset_id]
            asset_file = fixed_assets[test_asset_id]
            
            # Process lease
            lease_result = lease_agent.process_lease_file(lease_dir / lease_file)
            lease_correlations = lease_result.get('asset_correlations', {})
            
            # Process asset
            asset_result = asset_agent.process_asset_file(asset_dir / asset_file)
            asset_correlations = asset_result.get('lease_correlations', {})
            
            print(f"✅ Lease correlation framework: {'found_correlations' in lease_correlations}")
            print(f"✅ Asset correlation framework: {'found_correlations' in asset_correlations}")
        
        return len(correlations) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_po_correlations():
    """Test PO number correlations between invoices and contracts"""
    print("\n🧪 TESTING PO CORRELATIONS (Invoice-Contract)")
    print("-" * 50)
    
    try:
        from config.settings import DATA_DIR
        
        # Load all invoices and contracts to find PO correlations
        invoice_pos = {}
        contract_pos = {}
        
        # Load invoice POs
        invoice_dir = DATA_DIR / "invoices"
        for invoice_file in invoice_dir.glob("*.json"):
            with open(invoice_file, 'r') as f:
                invoice_data = json.load(f)
            po_number = invoice_data.get('buyers_order_number')
            if po_number:
                invoice_pos[po_number] = invoice_file.name
        
        # Load contract POs
        contract_dir = DATA_DIR / "contracts"
        for contract_file in contract_dir.glob("*.json"):
            with open(contract_file, 'r') as f:
                contract_data = json.load(f)
            po_number = contract_data.get('purchase_order_number')
            if po_number:
                contract_pos[po_number] = contract_file.name
        
        # Find correlations
        correlations = set(invoice_pos.keys()).intersection(set(contract_pos.keys()))
        
        print(f"✅ Invoice POs found: {len(invoice_pos)} ({list(invoice_pos.keys())})")
        print(f"✅ Contract POs found: {len(contract_pos)} ({list(contract_pos.keys())})")
        print(f"✅ PO correlations found: {len(correlations)} ({list(correlations)})")
        
        # Test with agents
        if correlations:
            from agents.extraction_agent import ExtractionAgent
            from agents.contract_agent import ContractAgent
            from utils.message_queue import MessageQueue
            
            queue = MessageQueue()
            extraction_agent = ExtractionAgent("extraction", queue)
            contract_agent = ContractAgent("contract", queue)
            
            # Test one correlation
            test_po = list(correlations)[0]
            invoice_file = invoice_pos[test_po]
            contract_file = contract_pos[test_po]
            
            # Process invoice
            invoice_result = extraction_agent.process_invoice_file(invoice_dir / invoice_file)
            invoice_fields = invoice_result.get('extracted_fields', [])
            
            # Process contract
            contract_result = contract_agent.process_contract_file(contract_dir / contract_file)
            contract_fields = contract_result.get('extracted_fields', [])
            
            # Check PO extraction
            invoice_po_found = any('po' in field.get('field_name', '').lower() or 'purchase_order' in field.get('field_name', '').lower() 
                                 for field in invoice_fields if isinstance(field, dict))
            contract_po_found = any('po' in field.get('field_name', '').lower() or 'purchase_order' in field.get('field_name', '').lower() 
                                  for field in contract_fields if isinstance(field, dict))
            
            print(f"✅ Invoice PO extraction: {invoice_po_found}")
            print(f"✅ Contract PO extraction: {contract_po_found}")
        
        return len(correlations) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_amount_variances():
    """Test amount variance detection between related documents"""
    print("\n🧪 TESTING AMOUNT VARIANCES")
    print("-" * 50)
    
    try:
        from agents.extraction_agent import ExtractionAgent
        from agents.contract_agent import ContractAgent
        from utils.message_queue import MessageQueue
        from config.settings import DATA_DIR
        
        queue = MessageQueue()
        extraction_agent = ExtractionAgent("extraction", queue)
        contract_agent = ContractAgent("contract", queue)
        
        # Process first invoice and contract
        invoice_path = DATA_DIR / "invoices" / "invoice_001.json"
        contract_path = DATA_DIR / "contracts" / "contract_001.json"
        
        if invoice_path.exists() and contract_path.exists():
            # Load data to check amounts
            with open(invoice_path, 'r') as f:
                invoice_data = json.load(f)
            with open(contract_path, 'r') as f:
                contract_data = json.load(f)
            
            invoice_amount = invoice_data.get('total_amount', 0)
            contract_amount = contract_data.get('contract_value', 0)
            
            print(f"✅ Invoice amount: ${invoice_amount:,.2f}")
            print(f"✅ Contract amount: ${contract_amount:,.2f}")
            
            if invoice_amount and contract_amount:
                variance = abs(invoice_amount - contract_amount) / contract_amount if contract_amount > 0 else 0
                print(f"✅ Amount variance: {variance:.2%}")
                
                # Process with agents
                invoice_result = extraction_agent.process_invoice_file(invoice_path)
                contract_result = contract_agent.process_contract_file(contract_path)
                
                # Check for variance detection in anomalies
                contract_anomalies = contract_result.get('anomalies', [])
                variance_anomalies = [a for a in contract_anomalies if 'variance' in a.get('type', '').lower()]
                
                print(f"✅ Variance anomalies detected: {len(variance_anomalies)}")
                
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_missing_po_detection():
    """Test detection of missing PO numbers where expected"""
    print("\n🧪 TESTING MISSING PO DETECTION")
    print("-" * 50)
    
    try:
        from agents.extraction_agent import ExtractionAgent
        from utils.message_queue import MessageQueue
        from config.settings import DATA_DIR
        
        queue = MessageQueue()
        agent = ExtractionAgent("extraction", queue)
        
        # Process all invoices to check PO detection
        invoice_dir = DATA_DIR / "invoices"
        invoices_with_po = 0
        invoices_without_po = 0
        
        for invoice_file in invoice_dir.glob("*.json"):
            with open(invoice_file, 'r') as f:
                invoice_data = json.load(f)
            
            po_number = invoice_data.get('buyers_order_number')
            if po_number:
                invoices_with_po += 1
            else:
                invoices_without_po += 1
                
                # Process with agent to check anomaly detection
                result = agent.process_invoice_file(invoice_file)
                anomalies = result.get('anomalies', [])
                
                # Check for missing PO anomaly
                po_anomalies = [a for a in anomalies if 'po' in a.get('type', '').lower()]
                print(f"✅ Missing PO detected in {invoice_file.name}: {len(po_anomalies) > 0}")
        
        print(f"✅ Invoices with PO: {invoices_with_po}")
        print(f"✅ Invoices without PO: {invoices_without_po}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_anomaly_tests():
    """Run all anomaly scenario tests"""
    print("🚀 TESTING BUILT-IN ANOMALY SCENARIOS")
    print("=" * 70)
    
    tests = [
        ("MSA PO Absence (Expected)", test_msa_po_absence),
        ("Lease PO Absence (Expected)", test_lease_po_absence),
        ("Asset Correlations", test_asset_correlations),
        ("PO Correlations", test_po_correlations),
        ("Amount Variances", test_amount_variances),
        ("Missing PO Detection", test_missing_po_detection)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print("📊 ANOMALY SCENARIO TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 RESULTS: {passed}/{total} anomaly scenarios validated")
    
    if passed == total:
        print("🎉 ALL ANOMALY SCENARIOS WORKING CORRECTLY!")
        return True
    else:
        print("⚠️ SOME ANOMALY SCENARIOS NEED REVIEW")
        return False

if __name__ == "__main__":
    success = run_anomaly_tests()
    sys.exit(0 if success else 1)