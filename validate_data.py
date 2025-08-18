#!/usr/bin/env python3
"""
Data validation script for Phase 1
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import DATA_DIR

def validate_invoices():
    """Validate invoice data"""
    print("📄 VALIDATING INVOICES")
    print("-" * 30)
    
    total_amount = 0
    po_numbers = set()
    
    for i in range(1, 6):
        file_path = DATA_DIR / "invoices" / f"invoice_{i:03d}.json"
        
        if not file_path.exists():
            print(f"❌ Missing: {file_path}")
            return False
        
        with open(file_path, 'r') as f:
            invoice = json.load(f)
        
        # Validate required fields
        required_fields = [
            "invoice_number", "invoice_date", "total_amount",
            "buyers_order_number", "vendor", "buyer"
        ]
        
        for field in required_fields:
            if field not in invoice:
                print(f"❌ {file_path}: Missing field '{field}'")
                return False
        
        total_amount += invoice["total_amount"]
        po_numbers.add(invoice["buyers_order_number"])
        
        print(f"✅ {invoice['invoice_number']}: ${invoice['total_amount']:,.2f} - PO: {invoice['buyers_order_number']}")
    
    print(f"📊 Total invoice amount: ${total_amount:,.2f}")
    print(f"📋 Unique PO numbers: {len(po_numbers)}")
    return True

def validate_contracts():
    """Validate contract data"""
    print("\n📝 VALIDATING CONTRACTS")
    print("-" * 30)
    
    total_value = 0
    po_numbers = set()
    
    for i in range(1, 4):
        file_path = DATA_DIR / "contracts" / f"contract_{i:03d}.json"
        
        if not file_path.exists():
            print(f"❌ Missing: {file_path}")
            return False
        
        with open(file_path, 'r') as f:
            contract = json.load(f)
        
        # Validate required fields
        required_fields = [
            "contract_number", "contract_date", "contract_value",
            "purchase_order_number", "parties"
        ]
        
        for field in required_fields:
            if field not in contract:
                print(f"❌ {file_path}: Missing field '{field}'")
                return False
        
        total_value += contract["contract_value"]
        po_numbers.add(contract["purchase_order_number"])
        
        print(f"✅ {contract['contract_number']}: ${contract['contract_value']:,.2f} - PO: {contract['purchase_order_number']}")
    
    print(f"📊 Total contract value: ${total_value:,.2f}")
    print(f"📋 Unique PO numbers: {len(po_numbers)}")
    return True

def validate_msa():
    """Validate MSA data"""
    print("\n📋 VALIDATING MSA")
    print("-" * 30)
    
    file_path = DATA_DIR / "msa" / "msa_001.json"
    
    if not file_path.exists():
        print(f"❌ Missing: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        msa = json.load(f)
    
    # Validate required fields
    required_fields = ["msa_number", "effective_date", "parties"]
    
    for field in required_fields:
        if field not in msa:
            print(f"❌ {file_path}: Missing field '{field}'")
            return False
    
    # Verify NO PO number (expected behavior)
    po_fields = [key for key in msa.keys() if 'po' in key.lower() or 'purchase_order' in key.lower()]
    if po_fields:
        print(f"⚠️ MSA contains PO fields: {po_fields} (unexpected)")
        return False
    
    print(f"✅ {msa['msa_number']}: Framework agreement (No PO - Expected)")
    return True

def validate_leases():
    """Validate lease data"""
    print("\n🏢 VALIDATING LEASES")
    print("-" * 30)
    
    asset_ids = set()
    
    for i in range(1, 4):
        file_path = DATA_DIR / "leases" / f"lease_{i:03d}.json"
        
        if not file_path.exists():
            print(f"❌ Missing: {file_path}")
            return False
        
        with open(file_path, 'r') as f:
            lease = json.load(f)
        
        # Validate required fields
        required_fields = [
            "lease_number", "lease_start_date", "leased_asset",
            "lessor", "lessee", "financial_terms"
        ]
        
        for field in required_fields:
            if field not in lease:
                print(f"❌ {file_path}: Missing field '{field}'")
                return False
        
        # Verify NO PO number (expected behavior)
        po_fields = [key for key in lease.keys() if 'po' in key.lower() or 'purchase_order' in key.lower()]
        if po_fields:
            print(f"⚠️ Lease contains PO fields: {po_fields} (unexpected)")
            return False
        
        asset_id = lease["leased_asset"]["asset_id"]
        asset_ids.add(asset_id)
        monthly = lease["financial_terms"]["monthly_payment"]
        
        print(f"✅ {lease['lease_number']}: {asset_id} - ${monthly:,.2f}/month (No PO - Expected)")
    
    print(f"📊 Unique asset IDs: {len(asset_ids)}")
    return True

def validate_fixed_assets():
    """Validate fixed asset data"""
    print("\n🏭 VALIDATING FIXED ASSETS")
    print("-" * 30)
    
    asset_ids = set()
    
    for i in range(1, 4):
        file_path = DATA_DIR / "fixed_assets" / f"fixed_asset_{i:03d}.json"
        
        if not file_path.exists():
            print(f"❌ Missing: {file_path}")
            return False
        
        with open(file_path, 'r') as f:
            asset = json.load(f)
        
        # Validate required fields
        required_fields = [
            "agreement_number", "acquisition_date", "asset_details",
            "buyer", "seller", "financial_details"
        ]
        
        for field in required_fields:
            if field not in asset:
                print(f"❌ {file_path}: Missing field '{field}'")
                return False
        
        asset_id = asset["asset_details"]["asset_id"]
        asset_ids.add(asset_id)
        price = asset["financial_details"]["purchase_price"]
        
        print(f"✅ {asset['agreement_number']}: {asset_id} - ${price:,.2f}")
    
    print(f"📊 Unique asset IDs: {len(asset_ids)}")
    return True

def validate_master_data():
    """Validate master data"""
    print("\n🗃️ VALIDATING MASTER DATA")
    print("-" * 30)
    
    file_path = DATA_DIR / "master_data" / "master_data.json"
    
    if not file_path.exists():
        print(f"❌ Missing: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        master_data = json.load(f)
    
    # Validate required sections
    required_sections = ["vendors", "buyers", "purchase_orders", "chart_of_accounts", "anomaly_patterns"]
    
    for section in required_sections:
        if section not in master_data:
            print(f"❌ Missing section: {section}")
            return False
    
    print(f"✅ Vendors: {len(master_data['vendors'])} entries")
    print(f"✅ Buyers: {len(master_data['buyers'])} entries")
    print(f"✅ Purchase Orders: {len(master_data['purchase_orders'])} entries")
    print(f"✅ Chart of Accounts: {len(master_data['chart_of_accounts'])} entries")
    print(f"✅ Anomaly Patterns: Configured")
    
    return True

def validate_cross_references():
    """Validate cross-references between documents"""
    print("\n🔗 VALIDATING CROSS-REFERENCES")
    print("-" * 30)
    
    # Load all data
    invoices = []
    for i in range(1, 6):
        file_path = DATA_DIR / "invoices" / f"invoice_{i:03d}.json"
        with open(file_path, 'r') as f:
            invoices.append(json.load(f))
    
    contracts = []
    for i in range(1, 4):
        file_path = DATA_DIR / "contracts" / f"contract_{i:03d}.json"
        with open(file_path, 'r') as f:
            contracts.append(json.load(f))
    
    leases = []
    for i in range(1, 4):
        file_path = DATA_DIR / "leases" / f"lease_{i:03d}.json"
        with open(file_path, 'r') as f:
            leases.append(json.load(f))
    
    fixed_assets = []
    for i in range(1, 4):
        file_path = DATA_DIR / "fixed_assets" / f"fixed_asset_{i:03d}.json"
        with open(file_path, 'r') as f:
            fixed_assets.append(json.load(f))
    
    # Check PO number correlations
    invoice_pos = {inv["buyers_order_number"] for inv in invoices}
    contract_pos = {cont["purchase_order_number"] for cont in contracts}
    
    matching_pos = invoice_pos.intersection(contract_pos)
    print(f"✅ Matching PO numbers (Invoice-Contract): {len(matching_pos)}")
    
    # Check asset correlations
    lease_assets = {lease["leased_asset"]["asset_id"] for lease in leases}
    fixed_asset_ids = {asset["asset_details"]["asset_id"] for asset in fixed_assets}
    
    matching_assets = lease_assets.intersection(fixed_asset_ids)
    print(f"✅ Matching asset IDs (Lease-Fixed Asset): {len(matching_assets)}")
    
    if len(matching_assets) > 0:
        print(f"   Asset IDs: {', '.join(matching_assets)}")
    
    return True

def main():
    """Main validation function"""
    print("=" * 60)
    print("🔍 PHASE 1 DATA VALIDATION")
    print("=" * 60)
    
    validations = [
        ("Invoices", validate_invoices),
        ("Contracts", validate_contracts),
        ("MSA", validate_msa),
        ("Leases", validate_leases),
        ("Fixed Assets", validate_fixed_assets),
        ("Master Data", validate_master_data),
        ("Cross-References", validate_cross_references)
    ]
    
    results = []
    
    for name, func in validations:
        try:
            result = func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} validation failed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ VALID" if result else "❌ INVALID"
        print(f"{status} {name}")
    
    print(f"\n📈 OVERALL VALIDATION: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 ALL DATA VALID - READY FOR PHASE 2!")
        return True
    else:
        print("⚠️ DATA ISSUES FOUND - REVIEW REQUIRED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)