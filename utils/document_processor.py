"""
Document Processing Utilities for Invoice Processing System
"""
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass

@dataclass
class ExtractionResult:
    """Result of field extraction with confidence score"""
    field_name: str
    value: Any
    confidence: float
    source_location: str = ""
    validation_status: str = "unknown"  # valid, invalid, warning
    notes: str = ""

@dataclass
class DocumentProcessingResult:
    """Complete document processing result"""
    document_type: str
    document_id: str
    extracted_fields: List[ExtractionResult]
    anomalies: List[Dict[str, Any]]
    processing_time: float
    overall_confidence: float
    status: str  # success, warning, error

class DocumentProcessor:
    """Shared document processing utilities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common patterns for field extraction
        self.patterns = {
            'invoice_number': [
                r'INV[-_]?\d{4}[-_]?\d{4}',
                r'INVOICE[-_]?\d+',
                r'INV[-_]?\d+'
            ],
            'po_number': [
                r'PO[-_]?\d+',
                r'PURCHASE[-_]?ORDER[-_]?\d+',
                r'P\.O\.[-_]?\d+'
            ],
            'amount': [
                r'\$[\d,]+\.?\d*',
                r'USD\s*[\d,]+\.?\d*',
                r'[\d,]+\.?\d*\s*USD'
            ],
            'date': [
                r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
                r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
                r'\d{1,2}[-/]\d{1,2}[-/]\d{2}'
            ]
        }
    
    def load_document(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a JSON document"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                document = json.load(f)
            
            self.logger.info(f"Successfully loaded document: {file_path}")
            return document
            
        except Exception as e:
            self.logger.error(f"Error loading document {file_path}: {e}")
            raise
    
    def extract_field(self, document: Dict[str, Any], field_path: str, 
                     expected_type: type = str, patterns: List[str] = None) -> ExtractionResult:
        """Extract a field from document with confidence scoring"""
        
        # Navigate nested dictionary path
        keys = field_path.split('.')
        value = document
        source_location = field_path
        
        try:
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    # Field not found at expected location
                    return ExtractionResult(
                        field_name=field_path,
                        value=None,
                        confidence=0.0,
                        source_location=source_location,
                        validation_status="invalid",
                        notes=f"Field not found at path: {field_path}"
                    )
            
            # Validate type
            if not isinstance(value, expected_type):
                if expected_type == float and isinstance(value, (int, str)):
                    try:
                        value = float(str(value).replace(',', '').replace('$', ''))
                    except ValueError:
                        return ExtractionResult(
                            field_name=field_path,
                            value=value,
                            confidence=0.3,
                            source_location=source_location,
                            validation_status="warning",
                            notes=f"Type conversion failed for {expected_type.__name__}"
                        )
            
            # Pattern validation if provided
            confidence = 1.0
            validation_status = "valid"
            notes = ""
            
            if patterns and isinstance(value, str):
                pattern_match = False
                for pattern in patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        pattern_match = True
                        break
                
                if not pattern_match:
                    confidence = 0.7
                    validation_status = "warning"
                    notes = "Value doesn't match expected patterns"
            
            return ExtractionResult(
                field_name=field_path,
                value=value,
                confidence=confidence,
                source_location=source_location,
                validation_status=validation_status,
                notes=notes
            )
            
        except Exception as e:
            return ExtractionResult(
                field_name=field_path,
                value=None,
                confidence=0.0,
                source_location=source_location,
                validation_status="error",
                notes=f"Extraction error: {str(e)}"
            )
    
    def validate_date(self, date_str: str, date_format: str = None) -> Tuple[bool, datetime, str]:
        """Validate and parse date string"""
        if not date_str:
            return False, None, "Empty date string"
        
        # Common date formats to try
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%m-%d-%Y',
            '%d-%m-%Y'
        ]
        
        if date_format:
            formats.insert(0, date_format)
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return True, parsed_date, ""
            except ValueError:
                continue
        
        return False, None, f"Unable to parse date: {date_str}"
    
    def validate_amount(self, amount: Any) -> Tuple[bool, float, str]:
        """Validate and normalize amount"""
        if amount is None:
            return False, 0.0, "Amount is None"
        
        try:
            if isinstance(amount, str):
                # Remove currency symbols and commas
                clean_amount = re.sub(r'[^\d.-]', '', amount)
                amount_float = float(clean_amount)
            elif isinstance(amount, (int, float)):
                amount_float = float(amount)
            else:
                return False, 0.0, f"Invalid amount type: {type(amount)}"
            
            if amount_float < 0:
                return False, amount_float, "Negative amount"
            
            if amount_float > 10000000:  # 10M limit
                return False, amount_float, "Amount exceeds reasonable limit"
            
            return True, amount_float, ""
            
        except (ValueError, TypeError) as e:
            return False, 0.0, f"Amount validation error: {str(e)}"
    
    def detect_anomalies(self, document: Dict[str, Any], 
                        extracted_fields: List[ExtractionResult],
                        document_type: str) -> List[Dict[str, Any]]:
        """Detect anomalies in document"""
        anomalies = []
        
        # Check for missing required fields based on document type
        required_fields = self.get_required_fields(document_type)
        
        extracted_field_names = {field.field_name for field in extracted_fields}
        
        for required_field in required_fields:
            if required_field not in extracted_field_names:
                anomalies.append({
                    'type': 'missing_field',
                    'severity': 'high',
                    'field': required_field,
                    'description': f'Required field {required_field} is missing',
                    'document_type': document_type
                })
        
        # Check for low confidence extractions
        for field in extracted_fields:
            if field.confidence < 0.5:
                anomalies.append({
                    'type': 'low_confidence',
                    'severity': 'medium',
                    'field': field.field_name,
                    'confidence': field.confidence,
                    'description': f'Low confidence extraction for {field.field_name}',
                    'notes': field.notes
                })
        
        # Document-specific anomaly checks
        if document_type == 'invoice':
            anomalies.extend(self._detect_invoice_anomalies(document, extracted_fields))
        elif document_type == 'contract':
            anomalies.extend(self._detect_contract_anomalies(document, extracted_fields))
        elif document_type == 'msa':
            anomalies.extend(self._detect_msa_anomalies(document, extracted_fields))
        elif document_type == 'lease':
            anomalies.extend(self._detect_lease_anomalies(document, extracted_fields))
        elif document_type == 'fixed_asset':
            anomalies.extend(self._detect_fixed_asset_anomalies(document, extracted_fields))
        
        return anomalies
    
    def get_required_fields(self, document_type: str) -> List[str]:
        """Get required fields for document type"""
        field_requirements = {
            'invoice': [
                'invoice_number', 'invoice_date', 'total_amount',
                'buyers_order_number', 'vendor.name', 'buyer.name'
            ],
            'contract': [
                'contract_number', 'contract_date', 'contract_value',
                'purchase_order_number', 'parties.party_a.name', 'parties.party_b.name'
            ],
            'msa': [
                'msa_number', 'effective_date', 'parties.client.name',
                'parties.service_provider.name'
            ],
            'lease': [
                'lease_number', 'lease_start_date', 'leased_asset.asset_id',
                'lessor.name', 'lessee.name', 'financial_terms.monthly_payment'
            ],
            'fixed_asset': [
                'agreement_number', 'acquisition_date', 'asset_details.asset_id',
                'buyer.name', 'seller.name', 'financial_details.purchase_price'
            ]
        }
        
        return field_requirements.get(document_type, [])
    
    def _detect_invoice_anomalies(self, document: Dict[str, Any], 
                                 fields: List[ExtractionResult]) -> List[Dict[str, Any]]:
        """Detect invoice-specific anomalies"""
        anomalies = []
        
        # Check for missing PO number (should be present in invoices)
        po_field = next((f for f in fields if 'order_number' in f.field_name.lower()), None)
        if not po_field or not po_field.value:
            anomalies.append({
                'type': 'missing_po_number',
                'severity': 'high',
                'description': 'Invoice missing purchase order number',
                'expected': True,
                'document_type': 'invoice'
            })
        
        # Check for unreasonable amounts
        amount_field = next((f for f in fields if 'amount' in f.field_name.lower()), None)
        if amount_field and amount_field.value:
            try:
                amount = float(amount_field.value)
                if amount > 1000000:  # Over 1M
                    anomalies.append({
                        'type': 'high_amount',
                        'severity': 'medium',
                        'amount': amount,
                        'description': f'Unusually high invoice amount: ${amount:,.2f}',
                        'document_type': 'invoice'
                    })
            except (ValueError, TypeError):
                pass
        
        return anomalies
    
    def _detect_contract_anomalies(self, document: Dict[str, Any], 
                                  fields: List[ExtractionResult]) -> List[Dict[str, Any]]:
        """Detect contract-specific anomalies"""
        anomalies = []
        
        # Check for missing PO number (should be present in contracts)
        po_field = next((f for f in fields if 'purchase_order' in f.field_name.lower()), None)
        if not po_field or not po_field.value:
            anomalies.append({
                'type': 'missing_po_number',
                'severity': 'high',
                'description': 'Contract missing purchase order number',
                'expected': True,
                'document_type': 'contract'
            })
        
        return anomalies
    
    def _detect_msa_anomalies(self, document: Dict[str, Any], 
                             fields: List[ExtractionResult]) -> List[Dict[str, Any]]:
        """Detect MSA-specific anomalies"""
        anomalies = []
        
        # Check for unexpected PO number (MSAs should NOT have PO numbers)
        po_fields = [f for f in fields if 'po' in f.field_name.lower() or 'purchase_order' in f.field_name.lower()]
        if po_fields and any(f.value for f in po_fields):
            anomalies.append({
                'type': 'unexpected_po_number',
                'severity': 'medium',
                'description': 'MSA contains purchase order number (unexpected)',
                'expected': False,
                'document_type': 'msa'
            })
        
        return anomalies
    
    def _detect_lease_anomalies(self, document: Dict[str, Any], 
                               fields: List[ExtractionResult]) -> List[Dict[str, Any]]:
        """Detect lease-specific anomalies"""
        anomalies = []
        
        # Check for unexpected PO number (leases should NOT have PO numbers)
        po_fields = [f for f in fields if 'po' in f.field_name.lower() or 'purchase_order' in f.field_name.lower()]
        if po_fields and any(f.value for f in po_fields):
            anomalies.append({
                'type': 'unexpected_po_number',
                'severity': 'medium',
                'description': 'Lease agreement contains purchase order number (unexpected)',
                'expected': False,
                'document_type': 'lease'
            })
        
        return anomalies
    
    def _detect_fixed_asset_anomalies(self, document: Dict[str, Any], 
                                     fields: List[ExtractionResult]) -> List[Dict[str, Any]]:
        """Detect fixed asset-specific anomalies"""
        anomalies = []
        
        # Check for asset depreciation consistency
        asset_details = document.get('financial_details', {})
        if asset_details:
            purchase_price = asset_details.get('purchase_price', 0)
            salvage_value = asset_details.get('salvage_value', 0)
            useful_life = asset_details.get('useful_life_years', 0)
            
            if salvage_value > purchase_price:
                anomalies.append({
                    'type': 'invalid_depreciation',
                    'severity': 'high',
                    'description': 'Salvage value exceeds purchase price',
                    'purchase_price': purchase_price,
                    'salvage_value': salvage_value,
                    'document_type': 'fixed_asset'
                })
        
        return anomalies
    
    def calculate_overall_confidence(self, extracted_fields: List[ExtractionResult]) -> float:
        """Calculate overall confidence score for document processing"""
        if not extracted_fields:
            return 0.0
        
        total_confidence = sum(field.confidence for field in extracted_fields)
        return total_confidence / len(extracted_fields)
    
    def process_document(self, file_path: Path, document_type: str) -> DocumentProcessingResult:
        """Complete document processing workflow"""
        start_time = datetime.now()
        
        try:
            # Load document
            document = self.load_document(file_path)
            
            # Extract required fields
            required_fields = self.get_required_fields(document_type)
            extracted_fields = []
            
            for field_path in required_fields:
                if 'amount' in field_path.lower() or 'price' in field_path.lower() or 'payment' in field_path.lower():
                    expected_type = float
                else:
                    expected_type = str
                
                result = self.extract_field(document, field_path, expected_type)
                extracted_fields.append(result)
            
            # Detect anomalies
            anomalies = self.detect_anomalies(document, extracted_fields, document_type)
            
            # Calculate metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            overall_confidence = self.calculate_overall_confidence(extracted_fields)
            
            # Determine status
            error_fields = [f for f in extracted_fields if f.validation_status == "error"]
            if error_fields:
                status = "error"
            elif anomalies:
                status = "warning"
            else:
                status = "success"
            
            # Get document ID
            document_id = self._extract_document_id(document, document_type)
            
            return DocumentProcessingResult(
                document_type=document_type,
                document_id=document_id,
                extracted_fields=extracted_fields,
                anomalies=anomalies,
                processing_time=processing_time,
                overall_confidence=overall_confidence,
                status=status
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Document processing failed for {file_path}: {e}")
            
            return DocumentProcessingResult(
                document_type=document_type,
                document_id=str(file_path.name),
                extracted_fields=[],
                anomalies=[{
                    'type': 'processing_error',
                    'severity': 'critical',
                    'description': f'Document processing failed: {str(e)}',
                    'document_type': document_type
                }],
                processing_time=processing_time,
                overall_confidence=0.0,
                status="error"
            )
    
    def _extract_document_id(self, document: Dict[str, Any], document_type: str) -> str:
        """Extract document identifier"""
        id_fields = {
            'invoice': ['invoice_number'],
            'contract': ['contract_number'],
            'msa': ['msa_number'],
            'lease': ['lease_number'],
            'fixed_asset': ['agreement_number']
        }
        
        fields_to_check = id_fields.get(document_type, ['id', 'number'])
        
        for field in fields_to_check:
            if field in document:
                return str(document[field])
        
        return f"unknown_{document_type}"