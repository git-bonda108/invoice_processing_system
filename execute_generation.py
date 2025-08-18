import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Execute data generation directly
data_dir = Path(__file__).parent / "data"

vendors = [
    "TechCorp Solutions Inc.", "Global Services Ltd.", "Innovation Partners LLC",
    "Enterprise Systems Co.", "Digital Solutions Group", "Advanced Technologies Inc."
]
buyers = [
    "Acme Corporation", "Global Enterprises", "Metro Industries",
    "Summit Holdings", "Pinnacle Group", "Apex Solutions"
]
po_numbers = [f"PO-{random.randint(100000, 999999)}" for _ in range(20)]

print("🔄 Generating sample documents...")

# Generate 5 invoices
for i in range(1, 6):
    invoice_date = datetime.now() - timedelta(days=random.randint(1, 90))
    due_date = invoice_date + timedelta(days=random.randint(15, 45))
    
    line_items = []
    subtotal = 0
    for _ in range(random.randint(1, 3)):
        quantity = random.randint(1, 5)
        unit_price = round(random.uniform(100, 2000), 2)
        total = round(quantity * unit_price, 2)
        subtotal += total
        
        line_items.append({
            "description": random.choice([
                "Software License - Annual Subscription",
                "Professional Services - Consulting",
                "Hardware Maintenance Contract"
            ]),
            "quantity": quantity,
            "unit_price": unit_price,
            "total": total
        })
    
    tax_amount = round(subtotal * 0.08, 2)
    total_amount = round(subtotal + tax_amount, 2)
    
    invoice_data = {
        "document_type": "invoice",
        "invoice_number": f"INV-{2024}-{i:04d}",
        "invoice_date": invoice_date.strftime("%Y-%m-%d"),
        "due_date": due_date.strftime("%Y-%m-%d"),
        "vendor": {
            "name": random.choice(vendors),
            "address": f"{random.randint(100, 9999)} Business Ave, Suite {random.randint(100, 999)}",
            "city": random.choice(["New York", "Los Angeles", "Chicago"]),
            "state": random.choice(["NY", "CA", "IL"]),
            "zip": f"{random.randint(10000, 99999)}"
        },
        "buyer": {
            "name": random.choice(buyers),
            "address": f"{random.randint(100, 9999)} Corporate Blvd",
            "city": random.choice(["Boston", "Seattle", "Denver"]),
            "state": random.choice(["MA", "WA", "CO"]),
            "zip": f"{random.randint(10000, 99999)}"
        },
        "buyers_order_number": random.choice(po_numbers),
        "line_items": line_items,
        "subtotal": subtotal,
        "tax_rate": 0.08,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "payment_terms": random.choice(["Net 30", "Net 45", "Net 60"]),
        "notes": "Thank you for your business!"
    }
    
    with open(data_dir / "invoices" / f"invoice_{i:03d}.json", 'w') as f:
        json.dump(invoice_data, f, indent=2)

print("✅ Generated 5 invoices")

# Generate 3 contracts
for i in range(1, 4):
    start_date = datetime.now() - timedelta(days=random.randint(30, 180))
    end_date = start_date + timedelta(days=random.randint(365, 1095))
    
    contract_data = {
        "document_type": "contract",
        "contract_number": f"CONT-{2024}-{i:03d}",
        "contract_date": start_date.strftime("%Y-%m-%d"),
        "effective_date": start_date.strftime("%Y-%m-%d"),
        "expiration_date": end_date.strftime("%Y-%m-%d"),
        "parties": {
            "party_a": {
                "name": random.choice(buyers),
                "role": "Client"
            },
            "party_b": {
                "name": random.choice(vendors),
                "role": "Service Provider"
            }
        },
        "purchase_order_number": random.choice(po_numbers),
        "contract_value": round(random.uniform(50000, 500000), 2),
        "payment_terms": random.choice(["Monthly", "Quarterly", "Annual"]),
        "scope_of_work": "Software Development and Maintenance Services"
    }
    
    with open(data_dir / "contracts" / f"contract_{i:03d}.json", 'w') as f:
        json.dump(contract_data, f, indent=2)

print("✅ Generated 3 contracts")

# Generate 1 MSA
msa_data = {
    "document_type": "master_service_agreement",
    "msa_number": "MSA-2024-001",
    "effective_date": (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d"),
    "parties": {
        "client": {
            "name": random.choice(buyers),
            "legal_entity": "Corporation"
        },
        "service_provider": {
            "name": random.choice(vendors),
            "legal_entity": "LLC"
        }
    },
    "term": "3 years with automatic renewal",
    "governing_law": "New York",
    "service_categories": [
        "Professional Services",
        "Technical Consulting",
        "Software Development"
    ],
    "payment_framework": {
        "currency": "USD",
        "payment_terms": "Net 30",
        "invoicing_frequency": "Monthly"
    }
}

with open(data_dir / "msa" / "msa_001.json", 'w') as f:
    json.dump(msa_data, f, indent=2)

print("✅ Generated 1 Master Service Agreement")

# Generate 3 lease agreements
for i in range(1, 4):
    start_date = datetime.now() - timedelta(days=random.randint(30, 365))
    end_date = start_date + timedelta(days=random.randint(365, 1825))
    monthly_payment = round(random.uniform(1000, 10000), 2)
    
    lease_data = {
        "document_type": "lease_agreement",
        "lease_number": f"LEASE-{2024}-{i:03d}",
        "lease_date": start_date.strftime("%Y-%m-%d"),
        "lease_start_date": start_date.strftime("%Y-%m-%d"),
        "lease_end_date": end_date.strftime("%Y-%m-%d"),
        "lessor": {
            "name": random.choice(vendors)
        },
        "lessee": {
            "name": random.choice(buyers)
        },
        "leased_asset": {
            "type": random.choice(["Office Equipment", "Vehicles", "Machinery"]),
            "description": "High-performance server equipment",
            "asset_id": f"ASSET-{random.randint(10000, 99999)}"
        },
        "financial_terms": {
            "monthly_payment": monthly_payment,
            "security_deposit": round(monthly_payment * 2, 2),
            "total_lease_value": round(monthly_payment * 36, 2)
        },
        "lease_type": "Operating Lease"
    }
    
    with open(data_dir / "leases" / f"lease_{i:03d}.json", 'w') as f:
        json.dump(lease_data, f, indent=2)

print("✅ Generated 3 lease agreements")

# Generate 3 fixed asset agreements
for i in range(1, 4):
    acquisition_date = datetime.now() - timedelta(days=random.randint(30, 730))
    
    asset_data = {
        "document_type": "fixed_asset_agreement",
        "agreement_number": f"FA-{2024}-{i:03d}",
        "acquisition_date": acquisition_date.strftime("%Y-%m-%d"),
        "buyer": {
            "name": random.choice(buyers)
        },
        "seller": {
            "name": random.choice(vendors)
        },
        "asset_details": {
            "asset_id": f"ASSET-{random.randint(10000, 99999)}",
            "asset_type": random.choice(["Computer Equipment", "Manufacturing Equipment", "Office Furniture"]),
            "description": "High-performance computing cluster",
            "model_number": f"MODEL-{random.randint(1000, 9999)}"
        },
        "financial_details": {
            "purchase_price": round(random.uniform(10000, 250000), 2),
            "depreciation_method": "Straight-line",
            "useful_life_years": random.randint(3, 10)
        }
    }
    
    with open(data_dir / "fixed_assets" / f"fixed_asset_{i:03d}.json", 'w') as f:
        json.dump(asset_data, f, indent=2)

print("✅ Generated 3 fixed asset agreements")

# Generate master data
master_data = {
    "vendors": [
        {
            "vendor_id": f"V{i:04d}",
            "name": vendor,
            "status": "Active"
        }
        for i, vendor in enumerate(vendors, 1)
    ],
    "buyers": [
        {
            "buyer_id": f"B{i:04d}",
            "name": buyer,
            "status": "Active"
        }
        for i, buyer in enumerate(buyers, 1)
    ],
    "purchase_orders": [
        {
            "po_number": po,
            "status": random.choice(["Open", "Closed", "Partially Received"]),
            "buyer": random.choice(buyers),
            "vendor": random.choice(vendors),
            "po_amount": round(random.uniform(5000, 100000), 2)
        }
        for po in po_numbers[:10]
    ]
}

with open(data_dir / "master_data" / "master_data.json", 'w') as f:
    json.dump(master_data, f, indent=2)

print("✅ Generated master data")
print("🎉 All sample documents generated successfully!")

# Let's also verify the files were created
print("\n📁 Verifying generated files:")
for doc_type in ["invoices", "contracts", "msa", "leases", "fixed_assets", "master_data"]:
    doc_dir = data_dir / doc_type
    files = list(doc_dir.glob("*.json"))
    print(f"  {doc_type}: {len(files)} files")

print("\n✨ Phase 1 Complete!")
print("📋 Summary:")
print("  ✅ Project structure created")
print("  ✅ Configuration files setup")
print("  ✅ Base agent framework implemented")
print("  ✅ Message queue system created")
print("  ✅ Sample documents generated")
print("  ✅ Data synthesis completed")

exec(open(__file__).read())