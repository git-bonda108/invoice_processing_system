"""
Master Data Agent - Validates data against master dataset
"""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

from .base_agent import BaseAgent, AgentStatus
from utils.message_queue import Message, MessageType, MessagePriority
from utils.document_processor import DocumentProcessor, ExtractionResult
from config.settings import DATA_DIR

class MasterDataAgent(BaseAgent):
    """Agent responsible for validating data against master dataset"""
    
    def __init__(self, agent_id: str, message_queue):
        super().__init__(agent_id, message_queue)
        self.document_processor = DocumentProcessor()
        self.master_data = {}
        self.load_master_data()
        
        # Agent-specific configuration
        self.config.update({
            'validation_timeout': 30,
            'strict_validation': True,
            'cache_lookups': True,
            'max_validation_errors': 10
        })
        
        self.logger.info(f"Master Data Agent {agent_id} initialized")
    
    def load_master_data(self):
        """Load master data from file"""
        try:
            master_data_path = DATA_DIR / "master_data" / "master_data.json"
            with open(master_data_path, 'r') as f:
                self.master_data = json.load(f)
            
            self.logger.info("Master data loaded successfully")
            self.logger.info(f"Loaded {len(self.master_data.get('vendors', []))} vendors")
            self.logger.info(f"Loaded {len(self.master_data.get('buyers', []))} buyers")
            self.logger.info(f"Loaded {len(self.master_data.get('purchase_orders', []))} purchase orders")
            
        except Exception as e:
            self.logger.error(f"Failed to load master data: {e}")
            self.master_data = {}
    
    def process_message(self, message: Message) -> Dict[str, Any]:
        """Process incoming messages"""
        try:
            if message.msg_type == MessageType.DATA_REQUEST:
                return self._handle_data_request(message)
            elif message.msg_type == MessageType.TASK_ASSIGNMENT:
                return self._handle_validation_task(message)
            else:
                return {
                    'status': 'error',
                    'message': f'Unsupported message type: {message.msg_type}'
                }
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _handle_data_request(self, message: Message) -> Dict[str, Any]:
        """Handle data lookup requests from other agents"""
        request_data = message.content
        request_type = request_data.get('request_type')
        
        if request_type == 'vendor_lookup':
            return self._lookup_vendor(request_data.get('vendor_name'))
        elif request_type == 'buyer_lookup':
            return self._lookup_buyer(request_data.get('buyer_name'))
        elif request_type == 'po_lookup':
            return self._lookup_purchase_order(request_data.get('po_number'))
        elif request_type == 'account_lookup':
            return self._lookup_account(request_data.get('account_code'))
        else:
            return {
                'status': 'error',
                'message': f'Unknown request type: {request_type}'
            }
    
    def _handle_validation_task(self, message: Message) -> Dict[str, Any]:
        """Handle document validation tasks"""
        task_data = message.content
        document_data = task_data.get('document_data')
        document_type = task_data.get('document_type')
        
        if not document_data or not document_type:
            return {
                'status': 'error',
                'message': 'Missing document_data or document_type'
            }
        
        validation_result = self.validate_document(document_data, document_type)
        
        # Update metrics
        if validation_result['status'] == 'success':
            self.metrics.tasks_completed += 1
        else:
            self.metrics.tasks_failed += 1
        
        return validation_result
    
    def validate_document(self, document: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Validate document against master data"""
        self.status = AgentStatus.PROCESSING
        start_time = datetime.now()
        
        try:
            validation_results = []
            anomalies = []
            
            # Validate based on document type
            if document_type == 'invoice':
                validation_results.extend(self._validate_invoice(document))
            elif document_type == 'contract':
                validation_results.extend(self._validate_contract(document))
            elif document_type == 'msa':
                validation_results.extend(self._validate_msa(document))
            elif document_type == 'lease':
                validation_results.extend(self._validate_lease(document))
            elif document_type == 'fixed_asset':
                validation_results.extend(self._validate_fixed_asset(document))
            
            # Collect anomalies from validation results
            for result in validation_results:
                if not result['is_valid']:
                    anomalies.append({
                        'type': 'master_data_validation',
                        'severity': result.get('severity', 'medium'),
                        'field': result['field'],
                        'description': result['message'],
                        'expected_value': result.get('expected_value'),
                        'actual_value': result.get('actual_value')
                    })
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Determine overall status
            critical_errors = [a for a in anomalies if a['severity'] == 'critical']
            if critical_errors:
                status = 'error'
            elif anomalies:
                status = 'warning'
            else:
                status = 'success'
            
            self.status = AgentStatus.IDLE
            
            return {
                'status': status,
                'validation_results': validation_results,
                'anomalies': anomalies,
                'processing_time': processing_time,
                'validated_fields': len(validation_results),
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Validation error: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'agent_id': self.agent_id
            }
    
    def _validate_invoice(self, invoice: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate invoice against master data"""
        results = []
        
        # Validate vendor
        vendor_name = invoice.get('vendor', {}).get('name')
        if vendor_name:
            vendor_result = self._lookup_vendor(vendor_name)
            results.append({
                'field': 'vendor.name',
                'is_valid': vendor_result['status'] == 'found',
                'message': vendor_result.get('message', ''),
                'severity': 'high' if vendor_result['status'] != 'found' else 'info',
                'actual_value': vendor_name,
                'expected_value': vendor_result.get('data', {}).get('name') if vendor_result['status'] == 'found' else None
            })
        
        # Validate buyer
        buyer_name = invoice.get('buyer', {}).get('name')
        if buyer_name:
            buyer_result = self._lookup_buyer(buyer_name)
            results.append({
                'field': 'buyer.name',
                'is_valid': buyer_result['status'] == 'found',
                'message': buyer_result.get('message', ''),
                'severity': 'high' if buyer_result['status'] != 'found' else 'info',
                'actual_value': buyer_name,
                'expected_value': buyer_result.get('data', {}).get('name') if buyer_result['status'] == 'found' else None
            })
        
        # Validate PO number
        po_number = invoice.get('buyers_order_number')
        if po_number:
            po_result = self._lookup_purchase_order(po_number)
            results.append({
                'field': 'buyers_order_number',
                'is_valid': po_result['status'] == 'found',
                'message': po_result.get('message', ''),
                'severity': 'critical' if po_result['status'] != 'found' else 'info',
                'actual_value': po_number,
                'expected_value': po_result.get('data', {}).get('po_number') if po_result['status'] == 'found' else None
            })
            
            # Additional PO validation - check if PO is open
            if po_result['status'] == 'found':
                po_data = po_result['data']
                if po_data.get('status') == 'Closed':
                    results.append({
                        'field': 'buyers_order_number',
                        'is_valid': False,
                        'message': 'Purchase order is closed',
                        'severity': 'high',
                        'actual_value': po_data.get('status'),
                        'expected_value': 'Open'
                    })
        
        return results
    
    def _validate_contract(self, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate contract against master data"""
        results = []
        
        # Validate parties
        party_a = contract.get('parties', {}).get('party_a', {}).get('name')
        party_b = contract.get('parties', {}).get('party_b', {}).get('name')
        
        if party_a:
            # Check if party_a is a known buyer
            buyer_result = self._lookup_buyer(party_a)
            results.append({
                'field': 'parties.party_a.name',
                'is_valid': buyer_result['status'] == 'found',
                'message': f"Party A validation: {buyer_result.get('message', '')}",
                'severity': 'medium' if buyer_result['status'] != 'found' else 'info',
                'actual_value': party_a
            })
        
        if party_b:
            # Check if party_b is a known vendor
            vendor_result = self._lookup_vendor(party_b)
            results.append({
                'field': 'parties.party_b.name',
                'is_valid': vendor_result['status'] == 'found',
                'message': f"Party B validation: {vendor_result.get('message', '')}",
                'severity': 'medium' if vendor_result['status'] != 'found' else 'info',
                'actual_value': party_b
            })
        
        # Validate PO number
        po_number = contract.get('purchase_order_number')
        if po_number:
            po_result = self._lookup_purchase_order(po_number)
            results.append({
                'field': 'purchase_order_number',
                'is_valid': po_result['status'] == 'found',
                'message': po_result.get('message', ''),
                'severity': 'critical' if po_result['status'] != 'found' else 'info',
                'actual_value': po_number
            })
        
        return results
    
    def _validate_msa(self, msa: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate MSA against master data"""
        results = []
        
        # Validate client
        client_name = msa.get('parties', {}).get('client', {}).get('name')
        if client_name:
            buyer_result = self._lookup_buyer(client_name)
            results.append({
                'field': 'parties.client.name',
                'is_valid': buyer_result['status'] == 'found',
                'message': buyer_result.get('message', ''),
                'severity': 'medium' if buyer_result['status'] != 'found' else 'info',
                'actual_value': client_name
            })
        
        # Validate service provider
        provider_name = msa.get('parties', {}).get('service_provider', {}).get('name')
        if provider_name:
            vendor_result = self._lookup_vendor(provider_name)
            results.append({
                'field': 'parties.service_provider.name',
                'is_valid': vendor_result['status'] == 'found',
                'message': vendor_result.get('message', ''),
                'severity': 'medium' if vendor_result['status'] != 'found' else 'info',
                'actual_value': provider_name
            })
        
        # MSA should NOT have PO numbers - this is expected
        po_fields = [key for key in msa.keys() if 'po' in key.lower() or 'purchase_order' in key.lower()]
        if not po_fields:
            results.append({
                'field': 'purchase_order_presence',
                'is_valid': True,
                'message': 'MSA correctly does not contain purchase order numbers',
                'severity': 'info'
            })
        
        return results
    
    def _validate_lease(self, lease: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate lease against master data"""
        results = []
        
        # Validate lessor
        lessor_name = lease.get('lessor', {}).get('name')
        if lessor_name:
            vendor_result = self._lookup_vendor(lessor_name)
            results.append({
                'field': 'lessor.name',
                'is_valid': vendor_result['status'] == 'found',
                'message': vendor_result.get('message', ''),
                'severity': 'medium' if vendor_result['status'] != 'found' else 'info',
                'actual_value': lessor_name
            })
        
        # Validate lessee
        lessee_name = lease.get('lessee', {}).get('name')
        if lessee_name:
            buyer_result = self._lookup_buyer(lessee_name)
            results.append({
                'field': 'lessee.name',
                'is_valid': buyer_result['status'] == 'found',
                'message': buyer_result.get('message', ''),
                'severity': 'medium' if buyer_result['status'] != 'found' else 'info',
                'actual_value': lessee_name
            })
        
        # Lease should NOT have PO numbers - this is expected
        po_fields = [key for key in lease.keys() if 'po' in key.lower() or 'purchase_order' in key.lower()]
        if not po_fields:
            results.append({
                'field': 'purchase_order_presence',
                'is_valid': True,
                'message': 'Lease correctly does not contain purchase order numbers',
                'severity': 'info'
            })
        
        return results
    
    def _validate_fixed_asset(self, asset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate fixed asset against master data"""
        results = []
        
        # Validate buyer
        buyer_name = asset.get('buyer', {}).get('name')
        if buyer_name:
            buyer_result = self._lookup_buyer(buyer_name)
            results.append({
                'field': 'buyer.name',
                'is_valid': buyer_result['status'] == 'found',
                'message': buyer_result.get('message', ''),
                'severity': 'medium' if buyer_result['status'] != 'found' else 'info',
                'actual_value': buyer_name
            })
        
        # Validate seller
        seller_name = asset.get('seller', {}).get('name')
        if seller_name:
            vendor_result = self._lookup_vendor(seller_name)
            results.append({
                'field': 'seller.name',
                'is_valid': vendor_result['status'] == 'found',
                'message': vendor_result.get('message', ''),
                'severity': 'medium' if vendor_result['status'] != 'found' else 'info',
                'actual_value': seller_name
            })
        
        return results
    
    def _lookup_vendor(self, vendor_name: str) -> Dict[str, Any]:
        """Look up vendor in master data"""
        if not vendor_name:
            return {'status': 'error', 'message': 'Empty vendor name'}
        
        vendors = self.master_data.get('vendors', [])
        
        # Exact match first
        for vendor in vendors:
            if vendor.get('name', '').lower() == vendor_name.lower():
                return {
                    'status': 'found',
                    'data': vendor,
                    'message': f'Vendor found: {vendor["name"]}'
                }
        
        # Partial match
        for vendor in vendors:
            if vendor_name.lower() in vendor.get('name', '').lower():
                return {
                    'status': 'partial_match',
                    'data': vendor,
                    'message': f'Partial vendor match: {vendor["name"]}'
                }
        
        return {
            'status': 'not_found',
            'message': f'Vendor not found in master data: {vendor_name}'
        }
    
    def _lookup_buyer(self, buyer_name: str) -> Dict[str, Any]:
        """Look up buyer in master data"""
        if not buyer_name:
            return {'status': 'error', 'message': 'Empty buyer name'}
        
        buyers = self.master_data.get('buyers', [])
        
        # Exact match first
        for buyer in buyers:
            if buyer.get('name', '').lower() == buyer_name.lower():
                return {
                    'status': 'found',
                    'data': buyer,
                    'message': f'Buyer found: {buyer["name"]}'
                }
        
        # Partial match
        for buyer in buyers:
            if buyer_name.lower() in buyer.get('name', '').lower():
                return {
                    'status': 'partial_match',
                    'data': buyer,
                    'message': f'Partial buyer match: {buyer["name"]}'
                }
        
        return {
            'status': 'not_found',
            'message': f'Buyer not found in master data: {buyer_name}'
        }
    
    def _lookup_purchase_order(self, po_number: str) -> Dict[str, Any]:
        """Look up purchase order in master data"""
        if not po_number:
            return {'status': 'error', 'message': 'Empty PO number'}
        
        purchase_orders = self.master_data.get('purchase_orders', [])
        
        for po in purchase_orders:
            if po.get('po_number', '').lower() == po_number.lower():
                return {
                    'status': 'found',
                    'data': po,
                    'message': f'Purchase order found: {po["po_number"]} (Status: {po.get("status", "Unknown")})'
                }
        
        return {
            'status': 'not_found',
            'message': f'Purchase order not found in master data: {po_number}'
        }
    
    def _lookup_account(self, account_code: str) -> Dict[str, Any]:
        """Look up account code in chart of accounts"""
        if not account_code:
            return {'status': 'error', 'message': 'Empty account code'}
        
        accounts = self.master_data.get('chart_of_accounts', [])
        
        for account in accounts:
            if account.get('account_code', '') == account_code:
                return {
                    'status': 'found',
                    'data': account,
                    'message': f'Account found: {account["account_code"]} - {account.get("account_name", "")}'
                }
        
        return {
            'status': 'not_found',
            'message': f'Account code not found: {account_code}'
        }
    
    def get_master_data_summary(self) -> Dict[str, Any]:
        """Get summary of loaded master data"""
        return {
            'vendors_count': len(self.master_data.get('vendors', [])),
            'buyers_count': len(self.master_data.get('buyers', [])),
            'purchase_orders_count': len(self.master_data.get('purchase_orders', [])),
            'accounts_count': len(self.master_data.get('chart_of_accounts', [])),
            'anomaly_patterns': self.master_data.get('anomaly_patterns', {}),
            'last_loaded': datetime.now().isoformat()
        }