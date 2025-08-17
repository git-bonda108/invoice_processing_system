"""
Data Synthesizer for Generating Realistic Invoice and Document Data
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid

from config.settings import DATA_DIR, DATA_GENERATION_CONFIG

class DataSynthesizer:
    """Generates realistic synthetic data for testing the agentic system"""
    
    def __init__(self):
        self.vendors = [
            {
                "name": "SAI ENTERPRISES",
                "address": "17-A, POCKET-B SIDDHARTHA EXTENSION NEW DELHI-110014",
                "gstin": "07AGTPP2498Q1Z4",
                "state": "Delhi",
                "state_code": "07",
                "phone": "+91-11-45678901",
                "email": "sai.enterprises@gmail.com"
            },
            {
                "name": "TECH SOLUTIONS INDIA",
                "address": "45, TECH PARK, ELECTRONIC CITY, BANGALORE-560100",
                "gstin": "29AABCT1234M1Z5",
                "state": "Karnataka",
                "state_code": "29",
                "phone": "+91-80-23456789",
                "email": "info@techsolutions.in"
            },
            {
                "name": "GLOBAL SUPPLIERS CORP",
                "address": "123, BUSINESS DISTRICT, MUMBAI-400001",
                "gstin": "27AABCS5678N1Z6",
                "state": "Maharashtra",
                "state_code": "27",
                "phone": "+91-22-34567890",
                "email": "contact@globalsuppliers.com"
            },
            {
                "name": "INNOVATION TECHNOLOGIES",
                "address": "78, INNOVATION HUB, HYDERABAD-500032",
                "gstin": "36AABCI9012O1Z7",
                "state": "Telangana",
                "state_code": "36",
                "phone": "+91-40-45678901",
                "email": "hello@innovationtech.com"
            },
            {
                "name": "QUALITY PRODUCTS LTD",
                "address": "56, QUALITY STREET, CHENNAI-600001",
                "gstin": "33AABCQ3456P1Z8",
                "state": "Tamil Nadu",
                "state_code": "33",
                "phone": "+91-44-56789012",
                "email": "sales@qualityproducts.com"
            }
        ]
        
        self.buyers = [
            {
                "name": "HP INDIA SALES PRIVATE LIMITED",
                "address": "COMMERZ, 5TH FLOOR NORTH SIDE, INTERNATIONAL, BUSINESS PARK, OBEROI GARDEN CITY, OFF WESTERN EXPRESS HIGHWAY, GOREGAON, (EAST), MUMBAI 400 063, MAHARASHTRA",
                "gstin": "27AAACC9862F1ZI",
                "pan": "AAACC9882F",
                "state": "Maharashtra",
                "state_code": "27"
            },
            {
                "name": "BANK OF AMERICA",
                "address": "N.A FIRST & 2ND FLOOR, DLF CENTRE, SANSAD MARG, NEW DELHI-110001",
                "gstin": "07AAACB1537G1Z3",
                "pan": "AAACB1537G",
                "state": "Delhi",
                "state_code": "07"
            },
            {
                "name": "MICROSOFT INDIA",
                "address": "MICROSOFT INDIA, DLF CYBERCITY, DLF PHASE 2, GURGAON-122002, HARYANA",
                "gstin": "06AABCM7890Q1Z9",
                "pan": "AABCM7890Q",
                "state": "Haryana",
                "state_code": "06"
            },
            {
                "name": "AMAZON INDIA",
                "address": "AMAZON INDIA, AMAZON DEVELOPMENT CENTRE, BANGALORE-560001, KARNATAKA",
                "gstin": "29AABCA1234R1Z0",
                "pan": "AABCA1234R",
                "state": "Karnataka",
                "state_code": "29"
            },
            {
                "name": "GOOGLE INDIA",
                "address": "GOOGLE INDIA, GOOGLEPLEX, BANGALORE-560001, KARNATAKA",
                "gstin": "29AABCG5678S1Z1",
                "pan": "AABCG5678S",
                "state": "Karnataka",
                "state_code": "29"
            }
        ]
        
        self.product_categories = [
            {
                "name": "HP TONER CARTRIDGE BLACK W9190MC",
                "hsn": "84439959",
                "category": "Office Supplies",
                "base_price_range": (5000, 8000)
            },
            {
                "name": "LAPTOP COMPUTER DELL LATITUDE 5520",
                "hsn": "84713000",
                "category": "Electronics",
                "base_price_range": (45000, 75000)
            },
            {
                "name": "SOFTWARE LICENSE - MICROSOFT OFFICE 365",
                "hsn": "85249900",
                "category": "Software",
                "base_price_range": (8000, 15000)
            },
            {
                "name": "NETWORK SWITCH CISCO CATALYST 2960",
                "hsn": "85176200",
                "category": "Networking",
                "base_price_range": (25000, 45000)
            },
            {
                "name": "PRINTER HP LASERJET PRO M404N",
                "hsn": "84433200",
                "category": "Office Equipment",
                "base_price_range": (12000, 25000)
            }
        ]
        
        self.logger = None  # Will be set if logging is needed
    
    def generate_invoices(self, count: int = 5, include_anomalies: bool = True) -> List[Dict[str, Any]]:
        """Generate synthetic invoice data"""
        invoices = []
        
        for i in range(count):
            # Decide if this invoice should have anomalies
            has_anomalies = include_anomalies and random.random() < DATA_GENERATION_CONFIG["anomaly_rate"]
            
            invoice = self._generate_single_invoice(i + 1, has_anomalies)
            invoices.append(invoice)
        
        return invoices
    
    def _generate_single_invoice(self, index: int, has_anomalies: bool = False) -> Dict[str, Any]:
        """Generate a single invoice with optional anomalies"""
        vendor = random.choice(self.vendors)
        buyer = random.choice(self.buyers)
        product = random.choice(self.product_categories)
        
        # Generate invoice date (within last 6 months)
        invoice_date = datetime.now() - timedelta(days=random.randint(1, 180))
        due_date = invoice_date + timedelta(days=random.choice([15, 30, 45, 60]))
        
        # Generate order date (before invoice date)
        order_date = invoice_date - timedelta(days=random.randint(1, 30))
        
        # Generate quantities and amounts
        quantity = random.randint(1, 10)
        base_price = random.uniform(*product["base_price_range"])
        unit_price = round(base_price, 2)
        subtotal = round(quantity * unit_price, 2)
        
        # Calculate tax (IGST for inter-state, CGST+SGST for intra-state)
        if vendor["state_code"] != buyer["state_code"]:
            tax_rate = 0.18  # IGST
            tax_amount = round(subtotal * tax_rate, 2)
            tax_details = [{"type": "IGST", "rate": tax_rate, "amount": tax_amount}]
        else:
            tax_rate = 0.09  # CGST + SGST
            cgst_amount = round(subtotal * tax_rate, 2)
            sgst_amount = round(subtotal * tax_rate, 2)
            tax_amount = cgst_amount + sgst_amount
            tax_details = [
                {"type": "CGST", "rate": tax_rate, "amount": cgst_amount},
                {"type": "SGST", "rate": tax_rate, "amount": sgst_amount}
            ]
        
        total_amount = subtotal + tax_amount
        
        # Generate invoice number
        invoice_number = f"{vendor['name'][:3].upper()}{invoice_date.strftime('%y')}-{invoice_date.strftime('%m')}/{index:03d}"
        
        # Generate PO number
        po_number = f"{buyer['name'][:3].upper()}{order_date.strftime('%y%m')}{random.randint(1000, 9999)}"
        
        # Generate IRN and acknowledgment details
        irn = f"{uuid.uuid4().hex[:32]}-{random.randint(1000, 9999)}"
        ack_no = f"{random.randint(100000000000000, 999999999999999)}"
        
        invoice_data = {
            "document_type": "invoice",
            "invoice_number": invoice_number,
            "invoice_date": invoice_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "irn": irn,
            "ack_no": ack_no,
            "ack_date": invoice_date.strftime("%d-%b-%y"),
            "vendor": vendor,
            "buyer": buyer,
            "buyers_order_number": po_number,
            "buyers_order_date": order_date.strftime("%Y-%m-%d"),
            "payment_terms": f"{random.choice([15, 30, 45, 60])} Days",
            "dispatch_details": {
                "doc_no": "DELIVERED",
                "date": invoice_date.strftime("%Y-%m-%d"),
                "through": random.choice(["BY HAND", "COURIER", "TRANSPORT"]),
                "destination": buyer["address"].split(",")[-2].strip()
            },
            "line_items": [
                {
                    "description": product["name"],
                    "hsn_sac": product["hsn"],
                    "quantity": quantity,
                    "unit": "Nos",
                    "rate": unit_price,
                    "amount": subtotal
                }
            ],
            "subtotal": subtotal,
            "tax_details": tax_details,
            "total_amount": total_amount,
            "amount_in_words": self._number_to_words(total_amount),
            "warranty": "WARRANTY BY THE PRINCIPAL COMPANY ONLY"
        }
        
        # Introduce anomalies if requested
        if has_anomalies:
            invoice_data = self._introduce_anomalies(invoice_data)
        
        return invoice_data
    
    def _introduce_anomalies(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Introduce realistic anomalies into the invoice"""
        anomaly_type = random.choice([
            "missing_po", "invalid_amount", "future_date", "vendor_buyer_same",
            "missing_tax", "duplicate_invoice", "invalid_gstin"
        ])
        
        if anomaly_type == "missing_po":
            invoice["buyers_order_number"] = None
            invoice["buyers_order_date"] = None
        
        elif anomaly_type == "invalid_amount":
            invoice["total_amount"] = -1000  # Negative amount
        
        elif anomaly_type == "future_date":
            invoice["invoice_date"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        elif anomaly_type == "vendor_buyer_same":
            invoice["buyer"] = invoice["vendor"]
        
        elif anomaly_type == "missing_tax":
            invoice["tax_details"] = []
            invoice["total_amount"] = invoice["subtotal"]
        
        elif anomaly_type == "duplicate_invoice":
            # Use same invoice number as another invoice
            pass  # Will be handled during generation
        
        elif anomaly_type == "invalid_gstin":
            invoice["vendor"]["gstin"] = "INVALID_GSTIN"
        
        return invoice
    
    def generate_contracts(self, count: int = 3) -> List[Dict[str, Any]]:
        """Generate synthetic contract data"""
        contracts = []
        
        for i in range(count):
            contract = self._generate_single_contract(i + 1)
            contracts.append(contract)
        
        return contracts
    
    def _generate_single_contract(self, index: int) -> Dict[str, Any]:
        """Generate a single contract"""
        vendor = random.choice(self.vendors)
        buyer = random.choice(self.buyers)
        
        start_date = datetime.now() - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=random.randint(365, 1825))  # 1-5 years
        
        contract_value = random.uniform(100000, 5000000)
        
        contract_type = random.choice(["Service Agreement", "Supply Contract", "Support Contract", "License Agreement"])
        contract_data = {
            "document_type": "contract",
            "contract_number": f"CON-{start_date.strftime('%Y')}-{index:03d}",
            "contract_type": contract_type,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "vendor": vendor,
            "buyer": buyer,
            "contract_value": round(contract_value, 2),
            "currency": "INR",
            "payment_terms": random.choice(["Net 30", "Net 45", "Net 60"]),
            "po_references": [
                f"PO-{buyer['name'][:3].upper()}{random.randint(100000, 999999)}"
                for _ in range(random.randint(1, 3))
            ],
            "scope_of_work": f"Comprehensive {contract_type.lower()} for {buyer['name']}",
            "terms_and_conditions": [
                "Payment within specified terms",
                "Quality standards must be maintained",
                "Confidentiality agreement applies",
                "Force majeure clause included"
            ],
            "status": random.choice(["Active", "Pending", "Completed", "Terminated"])
        }
        
        return contract_data
    
    def generate_msa(self, count: int = 1) -> List[Dict[str, Any]]:
        """Generate Master Service Agreement data"""
        msas = []
        
        for i in range(count):
            msa = self._generate_single_msa(i + 1)
            msas.append(msa)
        
        return msas
    
    def _generate_single_msa(self, index: int) -> Dict[str, Any]:
        """Generate a single MSA"""
        vendor = random.choice(self.vendors)
        buyer = random.choice(self.buyers)
        
        start_date = datetime.now() - timedelta(days=random.randint(100, 730))
        end_date = start_date + timedelta(days=random.randint(1825, 3650))  # 5-10 years
        
        msa_data = {
            "document_type": "msa",
            "msa_number": f"MSA-{start_date.strftime('%Y')}-{index:03d}",
            "agreement_type": "Master Services Agreement",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "vendor": vendor,
            "buyer": buyer,
            "agreement_value": None,  # MSA typically doesn't have fixed value
            "currency": "INR",
            "payment_terms": "As per individual SOWs",
            "po_references": [],  # MSA typically doesn't have POs
            "scope_of_work": "Framework agreement for various services",
            "terms_and_conditions": [
                "Master agreement governing all future SOWs",
                "Standard terms and conditions apply",
                "Individual SOWs will reference this MSA",
                "Pricing and terms subject to SOW-specific agreements"
            ],
            "status": "Active",
            "framework_agreement": True,
            "individual_sows": [
                f"SOW-{start_date.strftime('%Y')}-{random.randint(1, 10):02d}"
                for _ in range(random.randint(3, 8))
            ]
        }
        
        return msa_data
    
    def generate_leases(self, count: int = 3) -> List[Dict[str, Any]]:
        """Generate synthetic lease agreement data"""
        leases = []
        
        for i in range(count):
            lease = self._generate_single_lease(i + 1)
            leases.append(lease)
        
        return leases
    
    def _generate_single_lease(self, index: int) -> Dict[str, Any]:
        """Generate a single lease agreement"""
        lessor = random.choice(self.vendors)
        lessee = random.choice(self.buyers)
        
        start_date = datetime.now() - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=random.randint(730, 1825))  # 2-5 years
        
        monthly_rent = random.uniform(50000, 500000)
        security_deposit = monthly_rent * random.randint(2, 6)
        
        lease_type = random.choice(["Office Space", "Equipment", "Vehicle", "Software"])
        lease_data = {
            "document_type": "lease",
            "lease_number": f"LEASE-{start_date.strftime('%Y')}-{index:03d}",
            "lease_type": lease_type,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "lessor": lessor,
            "lessee": lessee,
            "monthly_rent": round(monthly_rent, 2),
            "security_deposit": round(security_deposit, 2),
            "currency": "INR",
            "payment_terms": "Monthly in advance",
            "po_references": [
                f"PO-{lessee['name'][:3].upper()}{random.randint(100000, 999999)}"
                for _ in range(random.randint(1, 2))
            ],
            "leased_item": {
                "description": f"{lease_type} at {lessor['address']}",
                "specifications": "As per attached specifications",
                "condition": "Good working condition"
            },
            "terms_and_conditions": [
                "Monthly rent due on 1st of each month",
                "Security deposit refundable upon lease termination",
                "Maintenance responsibility as per agreement",
                "Early termination penalties apply"
            ],
            "status": random.choice(["Active", "Pending", "Expired", "Terminated"])
        }
        
        return lease_data
    
    def generate_fixed_assets(self, count: int = 3) -> List[Dict[str, Any]]:
        """Generate synthetic fixed asset agreement data"""
        assets = []
        
        for i in range(count):
            asset = self._generate_single_fixed_asset(i + 1)
            assets.append(asset)
        
        return assets
    
    def _generate_single_fixed_asset(self, index: int) -> Dict[str, Any]:
        """Generate a single fixed asset agreement"""
        vendor = random.choice(self.vendors)
        buyer = random.choice(self.buyers)
        
        purchase_date = datetime.now() - timedelta(days=random.randint(30, 1095))  # Up to 3 years ago
        warranty_end = purchase_date + timedelta(days=random.randint(365, 1095))  # 1-3 years warranty
        
        asset_value = random.uniform(50000, 2000000)
        
        asset_type = random.choice(["Computer Equipment", "Office Furniture", "Machinery", "Vehicles", "Software"])
        asset_data = {
            "document_type": "fixed_asset",
            "asset_number": f"FA-{purchase_date.strftime('%Y')}-{index:03d}",
            "asset_type": asset_type,
            "purchase_date": purchase_date.strftime("%Y-%m-%d"),
            "warranty_end": warranty_end.strftime("%Y-%m-%d"),
            "vendor": vendor,
            "buyer": buyer,
            "asset_value": round(asset_value, 2),
            "currency": "INR",
            "payment_terms": random.choice(["Net 30", "Net 45", "Immediate"]),
            "po_references": [
                f"PO-{buyer['name'][:3].upper()}{random.randint(100000, 999999)}"
                for _ in range(random.randint(1, 2))
            ],
            "asset_details": {
                "description": f"{asset_type} from {vendor['name']}",
                "model": f"MODEL-{random.randint(1000, 9999)}",
                "serial_number": f"SN-{uuid.uuid4().hex[:8].upper()}",
                "location": buyer["address"]
            },
            "depreciation": {
                "method": "Straight Line",
                "useful_life": random.randint(3, 10),
                "annual_depreciation": round(asset_value / random.randint(3, 10), 2)
            },
            "status": random.choice(["Active", "Under Maintenance", "Retired", "Sold"])
        }
        
        return asset_data
    
    def generate_master_data(self) -> Dict[str, Any]:
        """Generate master data for validation"""
        master_data = {
            "document_type": "master_data",
            "generated_at": datetime.now().isoformat(),
            "vendors": self.vendors,
            "buyers": self.buyers,
            "product_categories": self.product_categories,
            "gst_rates": {
                "0%": ["Essential goods", "Agricultural products"],
                "5%": ["Transportation", "Basic services"],
                "12%": ["Processed foods", "Some services"],
                "18%": ["Electronics", "Most services", "Manufactured goods"],
                "28%": ["Luxury items", "Automobiles", "Some services"]
            },
            "validation_rules": {
                "invoice_number_format": r"^[A-Z]{3}\d{2}-\d{2}/\d{3}$",
                "gstin_format": r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$",
                "pan_format": r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$",
                "amount_range": {"min": 0.01, "max": 10000000},
                "date_range": {"past_days": 365, "future_days": 30}
            },
            "anomaly_patterns": [
                "Missing PO numbers in invoices",
                "Vendor-buyer mismatches",
                "Invalid GSTIN formats",
                "Future invoice dates",
                "Negative amounts",
                "Missing tax calculations"
            ]
        }
        
        return master_data
    
    def _number_to_words(self, number: float) -> str:
        """Convert number to words (simplified version)"""
        if number == 0:
            return "Zero"
        
        # This is a simplified version - in production you'd want a more robust solution
        if number < 1000:
            return f"INR {number:.2f}"
        elif number < 100000:
            return f"INR {number/1000:.1f} Thousand"
        elif number < 10000000:
            return f"INR {number/100000:.1f} Lakh"
        else:
            return f"INR {number/10000000:.1f} Crore"
    
    def save_data(self, data: List[Dict[str, Any]], data_type: str, directory: Path = None) -> None:
        """Save generated data to files"""
        if directory is None:
            directory = DATA_DIR / data_type
        
        directory.mkdir(exist_ok=True)
        
        for i, item in enumerate(data):
            filename = f"{data_type}_{i+1:03d}.json"
            filepath = directory / filename
            
            with open(filepath, 'w') as f:
                json.dump(item, f, indent=2, default=str)
    
    def generate_all_data(self) -> Dict[str, Any]:
        """Generate all types of data"""
        print("Generating synthetic data...")
        
        # Generate invoices
        invoices = self.generate_invoices(DATA_GENERATION_CONFIG["num_invoices"])
        self.save_data(invoices, "invoices")
        print(f"Generated {len(invoices)} invoices")
        
        # Generate contracts
        contracts = self.generate_contracts(DATA_GENERATION_CONFIG["num_contracts"])
        self.save_data(contracts, "contracts")
        print(f"Generated {len(contracts)} contracts")
        
        # Generate MSA
        msas = self.generate_msa(DATA_GENERATION_CONFIG["num_msa"])
        self.save_data(msas, "msa")
        print(f"Generated {len(msas)} MSA documents")
        
        # Generate leases
        leases = self.generate_leases(DATA_GENERATION_CONFIG["num_leases"])
        self.save_data(leases, "leases")
        print(f"Generated {len(leases)} lease agreements")
        
        # Generate fixed assets
        fixed_assets = self.generate_fixed_assets(DATA_GENERATION_CONFIG["num_fixed_assets"])
        self.save_data(fixed_assets, "fixed_assets")
        print(f"Generated {len(fixed_assets)} fixed asset agreements")
        
        # Generate master data
        master_data = self.generate_master_data()
        master_file = DATA_DIR / "master_data" / "master_data.json"
        master_file.parent.mkdir(exist_ok=True)
        with open(master_file, 'w') as f:
            json.dump(master_data, f, indent=2, default=str)
        print("Generated master data")
        
        return {
            "invoices": len(invoices),
            "contracts": len(contracts),
            "msa": len(msas),
            "leases": len(leases),
            "fixed_assets": len(fixed_assets),
            "master_data": 1
        }