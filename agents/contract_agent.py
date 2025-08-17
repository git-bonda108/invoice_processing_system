"""
Contract Agent - Processes contracts and validates terms
"""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

from .base_agent import BaseAgent, AgentStatus
from utils.message_queue import Message, MessageType, MessagePriority
from utils.document_processor import DocumentProcessor, ExtractionResult, DocumentProcessingResult
from config.settings import DATA_DIR

class ContractAgent(BaseAgent):
    """Agent specialized in contract processing and validation"""
    
    def __init__(self, agent_id: str, message_queue):
        super().__init__(agent_id, message_queue)
        self.document_processor = DocumentProcessor()
        
        # Agent-specific configuration
        self.config.update({
            'confidence_threshold': 0.85,
            'max_processing_time': 90,
            'validate_contract_terms': True,
            'check_po_correlations': True,
            'amount_variance_threshold': 0.10,  # 10% variance allowed for contracts
            'date_range_validation': True,
            'require_signatures': False  # Not applicable for JSON data
        })
        
        # Cache for cross-referencing with invoices
        self.processed_invoices = {}
        
        self.logger.info(f"Contract Agent {agent_id} initialized")
    
    def process_message(self, message: Message) -> Dict[str, Any]:
        """Process incoming messages"""
        try:
            if message.msg_type == MessageType.TASK_ASSIGNMENT:
                return self._handle_contract_task(message)
            elif message.msg_type == MessageType.DATA_REQUEST:
                return self._handle_data_request(message)
            elif message.msg_type == MessageType.DATA_RESPONSE:
                return self._handle_data_response(message)
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
    
    def _handle_contract_task(self, message: Message) -> Dict[str, Any]:
        """Handle contract processing tasks"""
        task_data = message.content
        
        if 'file_path' in task_data:
            # Process file
            file_path = Path(task_data['file_path'])
            return self.process_contract_file(file_path)
        elif 'document_data' in task_data:
            # Process document data directly
            document_data = task_data['document_data']
            return self.process_contract_data(document_data)
        else:
            return {
                'status': 'error',
                'message': 'Missing file_path or document_data in task'
            }
    
    def _handle_data_request(self, message: Message) -> Dict[str, Any]:
        """Handle data requests from other agents"""
        request_data = message.content
        request_type = request_data.get('request_type')
        
        if request_type == 'contract_summary':
            return self._get_contract_summary(request_data.get('contract_id'))
        elif request_type == 'po_correlation':
            return self._get_po_correlation(request_data.get('po_number'))
        elif request_type == 'contract_stats':
            return self._get_contract_statistics()
        else:
            return {
                'status': 'error',
                'message': f'Unknown request type: {request_type}'
            }
    
    def _handle_data_response(self, message: Message) -> Dict[str, Any]:
        """Handle data responses from other agents"""
        # Store invoice data for cross-referencing
        response_data = message.content
        if response_data.get('document_type') == 'invoice':
            invoice_id = response_data.get('document_id')
            if invoice_id:
                self.processed_invoices[invoice_id] = response_data
        
        return {'status': 'acknowledged'}
    
    def process_contract_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a contract file"""
        self.status = AgentStatus.PROCESSING
        start_time = datetime.now()
        
        try:
            # Use document processor for basic processing
            result = self.document_processor.process_document(file_path, 'contract')
            
            # Enhanced contract-specific processing
            enhanced_result = self._enhance_contract_processing(result, file_path)
            
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics.total_processing_time += processing_time
            
            if enhanced_result['status'] == 'success':
                self.metrics.tasks_completed += 1
            else:
                self.metrics.tasks_failed += 1
            
            self.status = AgentStatus.IDLE
            return enhanced_result
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Contract processing failed for {file_path}: {e}")
            self.metrics.tasks_failed += 1
            
            return {
                'status': 'error',
                'message': str(e),
                'file_path': str(file_path),
                'agent_id': self.agent_id
            }
    
    def process_contract_data(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process contract data directly"""
        self.status = AgentStatus.PROCESSING
        start_time = datetime.now()
        
        try:
            # Extract key contract fields
            extracted_fields = self._extract_contract_fields(document_data)
            
            # Validate extracted data
            validation_results = self._validate_contract_data(extracted_fields, document_data)
            
            # Detect anomalies
            anomalies = self._detect_contract_anomalies(extracted_fields, document_data)
            
            # Perform cross-reference validation
            cross_ref_anomalies = self._cross_reference_validation(extracted_fields, document_data)
            anomalies.extend(cross_ref_anomalies)
            
            # Calculate confidence and status
            overall_confidence = self._calculate_confidence(extracted_fields)
            status = self._determine_status(validation_results, anomalies)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Update metrics
            self.metrics.total_processing_time += processing_time
            if status == 'success':
                self.metrics.tasks_completed += 1
            else:
                self.metrics.tasks_failed += 1
            
            self.status = AgentStatus.IDLE
            
            return {
                'status': status,
                'document_type': 'contract',
                'document_id': document_data.get('contract_number', 'unknown'),
                'extracted_fields': [field.__dict__ for field in extracted_fields],
                'validation_results': validation_results,
                'anomalies': anomalies,
                'overall_confidence': overall_confidence,
                'processing_time': processing_time,
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Contract data processing failed: {e}")
            self.metrics.tasks_failed += 1
            
            return {
                'status': 'error',
                'message': str(e),
                'agent_id': self.agent_id
            }
    
    def _enhance_contract_processing(self, base_result: DocumentProcessingResult, 
                                    file_path: Path) -> Dict[str, Any]:
        """Enhance basic document processing with contract-specific logic"""
        
        # Load the original document for additional processing
        document = self.document_processor.load_document(file_path)
        
        # Additional contract-specific extractions
        enhanced_fields = []
        enhanced_fields.extend(base_result.extracted_fields)
        
        # Extract additional contract-specific fields
        additional_fields = [
            ('contract_type', str),
            ('effective_date', str),
            ('expiration_date', str),
            ('renewal_terms', str),
            ('termination_clause', str),
            ('governing_law', str),
            ('dispute_resolution', str)
        ]
        
        for field_name, field_type in additional_fields:
            if field_name in document:
                result = self.document_processor.extract_field(
                    document, field_name, field_type
                )
                enhanced_fields.append(result)
        
        # Enhanced anomaly detection
        enhanced_anomalies = list(base_result.anomalies)
        enhanced_anomalies.extend(self._detect_advanced_contract_anomalies(document, enhanced_fields))
        
        # Contract-specific validations
        contract_validations = self._validate_contract_terms(document, enhanced_fields)
        
        return {
            'status': base_result.status,
            'document_type': base_result.document_type,
            'document_id': base_result.document_id,
            'extracted_fields': [field.__dict__ for field in enhanced_fields],
            'anomalies': enhanced_anomalies,
            'contract_validations': contract_validations,
            'overall_confidence': self._calculate_confidence(enhanced_fields),
            'processing_time': base_result.processing_time,
            'agent_id': self.agent_id,
            'file_path': str(file_path)
        }
    
    def _extract_contract_fields(self, document: Dict[str, Any]) -> List[ExtractionResult]:
        """Extract key fields from contract document"""
        fields = []
        
        # Define contract field mappings
        field_mappings = [
            ('contract_number', str, ['contract_number']),
            ('contract_date', str, ['contract_date', 'execution_date']),
            ('effective_date', str, ['effective_date', 'start_date']),
            ('expiration_date', str, ['expiration_date', 'end_date']),
            ('contract_value', float, ['contract_value', 'total_value', 'amount']),
            ('purchase_order_number', str, ['purchase_order_number', 'po_number']),
            ('parties.party_a.name', str, ['parties.party_a.name']),
            ('parties.party_a.address', str, ['parties.party_a.address']),
            ('parties.party_b.name', str, ['parties.party_b.name']),
            ('parties.party_b.address', str, ['parties.party_b.address']),
            ('payment_terms', str, ['payment_terms']),
            ('contract_type', str, ['contract_type', 'type']),
            ('governing_law', str, ['governing_law']),
            ('currency', str, ['currency'])
        ]
        
        for field_name, field_type, possible_paths in field_mappings:
            result = None
            
            # Try each possible path
            for path in possible_paths:
                result = self.document_processor.extract_field(document, path, field_type)
                if result.value is not None:
                    result.field_name = field_name  # Standardize field name
                    break
            
            if result:
                fields.append(result)
        
        return fields
    
    def _validate_contract_data(self, extracted_fields: List[ExtractionResult], 
                               document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate extracted contract data"""
        validation_results = []
        
        # Get field values for easy access
        field_values = {field.field_name: field.value for field in extracted_fields}
        
        # Validate required fields
        required_fields = [
            'contract_number', 'contract_date', 'contract_value',
            'parties.party_a.name', 'parties.party_b.name'
        ]
        
        for field in required_fields:
            if field not in field_values or field_values[field] is None:
                validation_results.append({
                    'field': field,
                    'is_valid': False,
                    'severity': 'critical',
                    'message': f'Required field {field} is missing or null'
                })
            else:
                validation_results.append({
                    'field': field,
                    'is_valid': True,
                    'severity': 'info',
                    'message': f'Required field {field} is present'
                })
        
        # Validate contract value
        if 'contract_value' in field_values and field_values['contract_value']:
            amount_valid, amount_value, amount_message = self.document_processor.validate_amount(
                field_values['contract_value']
            )
            validation_results.append({
                'field': 'contract_value',
                'is_valid': amount_valid,
                'severity': 'high' if not amount_valid else 'info',
                'message': amount_message or f'Contract value validation: ${amount_value:,.2f}',
                'validated_value': amount_value
            })
        
        # Validate dates
        date_fields = ['contract_date', 'effective_date', 'expiration_date']
        validated_dates = {}
        
        for date_field in date_fields:
            if date_field in field_values and field_values[date_field]:
                date_valid, date_value, date_message = self.document_processor.validate_date(
                    field_values[date_field]
                )
                validation_results.append({
                    'field': date_field,
                    'is_valid': date_valid,
                    'severity': 'high' if not date_valid else 'info',
                    'message': date_message or f'{date_field} validation: {date_value}',
                    'validated_value': date_value.isoformat() if date_value else None
                })
                
                if date_valid:
                    validated_dates[date_field] = date_value
        
        # Validate date relationships
        if 'effective_date' in validated_dates and 'expiration_date' in validated_dates:
            if validated_dates['expiration_date'] <= validated_dates['effective_date']:
                validation_results.append({
                    'field': 'date_relationship',
                    'is_valid': False,
                    'severity': 'high',
                    'message': 'Expiration date must be after effective date',
                    'effective_date': validated_dates['effective_date'].isoformat(),
                    'expiration_date': validated_dates['expiration_date'].isoformat()
                })
        
        # Validate PO number presence (should be present in contracts)
        if self.config.get('check_po_correlations', True):
            po_number = field_values.get('purchase_order_number')
            if not po_number:
                validation_results.append({
                    'field': 'purchase_order_number',
                    'is_valid': False,
                    'severity': 'high',
                    'message': 'Contract missing purchase order number',
                    'expected': True,
                    'actual': None
                })
        
        return validation_results
    
    def _detect_contract_anomalies(self, extracted_fields: List[ExtractionResult], 
                                  document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect contract-specific anomalies"""
        anomalies = []
        field_values = {field.field_name: field.value for field in extracted_fields}
        
        # Check for unusual contract values
        contract_value = field_values.get('contract_value')
        if contract_value:
            try:
                value_float = float(contract_value)
                
                # Very high contract values
                if value_float > 1000000:  # Over 1M
                    anomalies.append({
                        'type': 'high_contract_value',
                        'severity': 'medium',
                        'description': f'High contract value: ${value_float:,.2f}',
                        'field': 'contract_value',
                        'amount': value_float,
                        'threshold': 1000000
                    })
                
                # Very low contract values
                if value_float < 1000:  # Under 1K
                    anomalies.append({
                        'type': 'low_contract_value',
                        'severity': 'low',
                        'description': f'Low contract value: ${value_float:,.2f}',
                        'field': 'contract_value',
                        'amount': value_float,
                        'threshold': 1000
                    })
                    
            except (ValueError, TypeError):
                pass
        
        # Check for short contract terms
        effective_date = field_values.get('effective_date')
        expiration_date = field_values.get('expiration_date')
        
        if effective_date and expiration_date:
            try:
                eff_date_valid, eff_date, _ = self.document_processor.validate_date(effective_date)
                exp_date_valid, exp_date, _ = self.document_processor.validate_date(expiration_date)
                
                if eff_date_valid and exp_date_valid:
                    contract_duration = (exp_date - eff_date).days
                    
                    if contract_duration < 30:  # Less than 30 days
                        anomalies.append({
                            'type': 'short_contract_term',
                            'severity': 'medium',
                            'description': f'Very short contract term: {contract_duration} days',
                            'duration_days': contract_duration,
                            'effective_date': eff_date.isoformat(),
                            'expiration_date': exp_date.isoformat()
                        })
                    elif contract_duration > 3650:  # More than 10 years
                        anomalies.append({
                            'type': 'long_contract_term',
                            'severity': 'low',
                            'description': f'Very long contract term: {contract_duration} days ({contract_duration/365:.1f} years)',
                            'duration_days': contract_duration,
                            'duration_years': contract_duration / 365
                        })
                        
            except Exception:
                pass
        
        # Check for missing critical contract terms
        critical_terms = ['payment_terms', 'governing_law']
        for term in critical_terms:
            if term not in field_values or not field_values[term]:
                anomalies.append({
                    'type': 'missing_contract_term',
                    'severity': 'medium',
                    'description': f'Missing critical contract term: {term}',
                    'field': term,
                    'expected': True,
                    'actual': None
                })
        
        # Check for low confidence extractions
        for field in extracted_fields:
            if field.confidence < self.config.get('confidence_threshold', 0.85):
                anomalies.append({
                    'type': 'low_confidence_extraction',
                    'severity': 'medium',
                    'description': f'Low confidence extraction for {field.field_name}',
                    'field': field.field_name,
                    'confidence': field.confidence,
                    'threshold': self.config.get('confidence_threshold', 0.85),
                    'value': field.value
                })
        
        return anomalies
    
    def _detect_advanced_contract_anomalies(self, document: Dict[str, Any], 
                                           fields: List[ExtractionResult]) -> List[Dict[str, Any]]:
        """Detect advanced contract anomalies"""
        anomalies = []
        
        # Check for party name consistency
        party_a_name = None
        party_b_name = None
        
        for field in fields:
            if field.field_name == 'parties.party_a.name' and field.value:
                party_a_name = field.value
            elif field.field_name == 'parties.party_b.name' and field.value:
                party_b_name = field.value
        
        if party_a_name and party_b_name:
            # Check if parties are the same (unusual)
            if party_a_name.lower() == party_b_name.lower():
                anomalies.append({
                    'type': 'identical_parties',
                    'severity': 'high',
                    'description': 'Contract parties have identical names',
                    'party_a': party_a_name,
                    'party_b': party_b_name
                })
        
        # Check for contract type consistency
        contract_type = document.get('contract_type', '').lower()
        contract_value = document.get('contract_value', 0)
        
        if contract_type and contract_value:
            try:
                value_float = float(contract_value)
                
                # Service contracts with very high values might be unusual
                if 'service' in contract_type and value_float > 500000:
                    anomalies.append({
                        'type': 'high_value_service_contract',
                        'severity': 'low',
                        'description': f'High value service contract: ${value_float:,.2f}',
                        'contract_type': contract_type,
                        'contract_value': value_float
                    })
                    
            except (ValueError, TypeError):
                pass
        
        return anomalies
    
    def _validate_contract_terms(self, document: Dict[str, Any], 
                                fields: List[ExtractionResult]) -> List[Dict[str, Any]]:
        """Validate specific contract terms"""
        validations = []
        
        # Check payment terms format
        payment_terms = document.get('payment_terms', '')
        if payment_terms:
            # Common payment terms patterns
            valid_patterns = ['net 30', 'net 45', 'net 60', 'due on receipt', 'advance payment']
            
            is_valid_pattern = any(pattern in payment_terms.lower() for pattern in valid_patterns)
            
            validations.append({
                'term': 'payment_terms',
                'is_valid': is_valid_pattern,
                'value': payment_terms,
                'message': 'Payment terms follow standard format' if is_valid_pattern else 'Non-standard payment terms format',
                'severity': 'low' if not is_valid_pattern else 'info'
            })
        
        # Check governing law
        governing_law = document.get('governing_law', '')
        if governing_law:
            # Should contain state or country reference
            has_jurisdiction = any(keyword in governing_law.lower() 
                                 for keyword in ['state', 'country', 'law', 'jurisdiction'])
            
            validations.append({
                'term': 'governing_law',
                'is_valid': has_jurisdiction,
                'value': governing_law,
                'message': 'Governing law specifies jurisdiction' if has_jurisdiction else 'Governing law lacks clear jurisdiction',
                'severity': 'medium' if not has_jurisdiction else 'info'
            })
        
        return validations
    
    def _cross_reference_validation(self, extracted_fields: List[ExtractionResult], 
                                   document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform cross-reference validation with invoices and master data"""
        anomalies = []
        field_values = {field.field_name: field.value for field in extracted_fields}
        
        # Check PO number correlation with invoices
        po_number = field_values.get('purchase_order_number')
        if po_number:
            # Look for matching invoices with same PO number
            matching_invoices = []
            for invoice_id, invoice_data in self.processed_invoices.items():
                invoice_fields = invoice_data.get('extracted_fields', [])
                for field in invoice_fields:
                    if (field.get('field_name') == 'buyers_order_number' and 
                        field.get('value') == po_number):
                        matching_invoices.append(invoice_id)
                        break
            
            if not matching_invoices:
                anomalies.append({
                    'type': 'no_matching_invoices',
                    'severity': 'medium',
                    'description': f'No invoices found with matching PO number: {po_number}',
                    'po_number': po_number,
                    'expected_invoices': True,
                    'found_invoices': False
                })
            else:
                # Check amount correlation
                contract_value = field_values.get('contract_value')
                if contract_value:
                    try:
                        contract_amount = float(contract_value)
                        
                        # Sum invoice amounts for this PO
                        total_invoice_amount = 0
                        for invoice_id in matching_invoices:
                            invoice_data = self.processed_invoices[invoice_id]
                            invoice_fields = invoice_data.get('extracted_fields', [])
                            for field in invoice_fields:
                                if field.get('field_name') == 'total_amount':
                                    try:
                                        total_invoice_amount += float(field.get('value', 0))
                                    except (ValueError, TypeError):
                                        pass
                        
                        # Check for significant variance
                        if total_invoice_amount > 0:
                            variance = abs(contract_amount - total_invoice_amount) / contract_amount
                            threshold = self.config.get('amount_variance_threshold', 0.10)
                            
                            if variance > threshold:
                                anomalies.append({
                                    'type': 'amount_variance',
                                    'severity': 'medium',
                                    'description': f'Contract amount variance with invoices: {variance:.2%}',
                                    'contract_amount': contract_amount,
                                    'invoice_total': total_invoice_amount,
                                    'variance_percentage': variance,
                                    'threshold': threshold,
                                    'po_number': po_number
                                })
                                
                    except (ValueError, TypeError):
                        pass
        
        return anomalies
    
    def _calculate_confidence(self, extracted_fields: List[ExtractionResult]) -> float:
        """Calculate overall confidence score"""
        if not extracted_fields:
            return 0.0
        
        total_confidence = sum(field.confidence for field in extracted_fields)
        return total_confidence / len(extracted_fields)
    
    def _determine_status(self, validation_results: List[Dict[str, Any]], 
                         anomalies: List[Dict[str, Any]]) -> str:
        """Determine overall processing status"""
        
        # Check for critical errors
        critical_errors = [v for v in validation_results if not v['is_valid'] and v['severity'] == 'critical']
        critical_anomalies = [a for a in anomalies if a['severity'] == 'critical']
        
        if critical_errors or critical_anomalies:
            return 'error'
        
        # Check for warnings
        warnings = [v for v in validation_results if not v['is_valid'] and v['severity'] in ['high', 'medium']]
        warning_anomalies = [a for a in anomalies if a['severity'] in ['high', 'medium']]
        
        if warnings or warning_anomalies:
            return 'warning'
        
        return 'success'
    
    def _get_contract_summary(self, contract_id: str) -> Dict[str, Any]:
        """Get summary of processed contract"""
        return {
            'status': 'info',
            'message': f'Contract summary for {contract_id} not implemented yet'
        }
    
    def _get_po_correlation(self, po_number: str) -> Dict[str, Any]:
        """Get PO correlation information"""
        matching_invoices = []
        for invoice_id, invoice_data in self.processed_invoices.items():
            invoice_fields = invoice_data.get('extracted_fields', [])
            for field in invoice_fields:
                if (field.get('field_name') == 'buyers_order_number' and 
                    field.get('value') == po_number):
                    matching_invoices.append(invoice_id)
                    break
        
        return {
            'status': 'success',
            'po_number': po_number,
            'matching_invoices': matching_invoices,
            'correlation_count': len(matching_invoices)
        }
    
    def _get_contract_statistics(self) -> Dict[str, Any]:
        """Get contract processing statistics"""
        return {
            'status': 'success',
            'statistics': {
                'total_processed': self.metrics.tasks_completed + self.metrics.tasks_failed,
                'successful': self.metrics.tasks_completed,
                'failed': self.metrics.tasks_failed,
                'average_processing_time': (
                    self.metrics.total_processing_time / max(1, self.metrics.tasks_completed + self.metrics.tasks_failed)
                ),
                'confidence_threshold': self.config.get('confidence_threshold', 0.85),
                'cached_invoices': len(self.processed_invoices),
                'agent_id': self.agent_id
            }
        }
    
    def process_batch_contracts(self, contract_directory: Path) -> Dict[str, Any]:
        """Process a batch of contracts"""
        self.status = AgentStatus.PROCESSING
        start_time = datetime.now()
        
        results = []
        contract_files = list(contract_directory.glob("*.json"))
        
        self.logger.info(f"Processing batch of {len(contract_files)} contracts")
        
        for contract_file in contract_files:
            try:
                result = self.process_contract_file(contract_file)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to process {contract_file}: {e}")
                results.append({
                    'status': 'error',
                    'file_path': str(contract_file),
                    'message': str(e)
                })
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Calculate batch statistics
        successful = len([r for r in results if r.get('status') == 'success'])
        warnings = len([r for r in results if r.get('status') == 'warning'])
        errors = len([r for r in results if r.get('status') == 'error'])
        
        self.status = AgentStatus.IDLE
        
        return {
            'status': 'success',
            'batch_summary': {
                'total_processed': len(results),
                'successful': successful,
                'warnings': warnings,
                'errors': errors,
                'processing_time': processing_time,
                'average_time_per_contract': processing_time / len(results) if results else 0
            },
            'individual_results': results,
            'agent_id': self.agent_id
        }