"""
Leasing Agent - Processes lease agreements and asset correlations
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

class LeasingAgent(BaseAgent):
    """Agent specialized in lease agreement processing and asset correlation"""
    
    def __init__(self, agent_id: str, message_queue):
        super().__init__(agent_id, message_queue)
        self.document_processor = DocumentProcessor()
        
        # Agent-specific configuration
        self.config.update({
            'confidence_threshold': 0.82,
            'max_processing_time': 80,
            'validate_lease_terms': True,
            'expect_no_po_numbers': True,  # Leases should NOT have PO numbers
            'check_asset_correlations': True,
            'validate_payment_schedules': True,
            'lease_term_min_months': 1,
            'lease_term_max_months': 120,  # 10 years max
            'monthly_payment_threshold': 50000  # Flag very high monthly payments
        })
        
        # Cache for asset correlations
        self.processed_assets = {}
        
        self.logger.info(f"Leasing Agent {agent_id} initialized")
    
    def process_message(self, message: Message) -> Dict[str, Any]:
        """Process incoming messages"""
        try:
            if message.msg_type == MessageType.TASK_ASSIGNMENT:
                return self._handle_lease_task(message)
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
    
    def _handle_lease_task(self, message: Message) -> Dict[str, Any]:
        """Handle lease processing tasks"""
        task_data = message.content
        
        if 'file_path' in task_data:
            # Process file
            file_path = Path(task_data['file_path'])
            return self.process_lease_file(file_path)
        elif 'document_data' in task_data:
            # Process document data directly
            document_data = task_data['document_data']
            return self.process_lease_data(document_data)
        else:
            return {
                'status': 'error',
                'message': 'Missing file_path or document_data in task'
            }
    
    def _handle_data_request(self, message: Message) -> Dict[str, Any]:
        """Handle data requests from other agents"""
        request_data = message.content
        request_type = request_data.get('request_type')
        
        if request_type == 'lease_summary':
            return self._get_lease_summary(request_data.get('lease_id'))
        elif request_type == 'asset_correlation':
            return self._get_asset_correlation(request_data.get('asset_id'))
        elif request_type == 'lease_stats':
            return self._get_lease_statistics()
        else:
            return {
                'status': 'error',
                'message': f'Unknown request type: {request_type}'
            }
    
    def _handle_data_response(self, message: Message) -> Dict[str, Any]:
        """Handle data responses from other agents"""
        # Store asset data for correlation
        response_data = message.content
        if response_data.get('document_type') == 'fixed_asset':
            asset_id = self._extract_asset_id_from_response(response_data)
            if asset_id:
                self.processed_assets[asset_id] = response_data
        
        return {'status': 'acknowledged'}
    
    def process_lease_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a lease file"""
        self.status = AgentStatus.PROCESSING
        start_time = datetime.now()
        
        try:
            # Use document processor for basic processing
            result = self.document_processor.process_document(file_path, 'lease')
            
            # Enhanced lease-specific processing
            enhanced_result = self._enhance_lease_processing(result, file_path)
            
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
            self.logger.error(f"Lease processing failed for {file_path}: {e}")
            self.metrics.tasks_failed += 1
            
            return {
                'status': 'error',
                'message': str(e),
                'file_path': str(file_path),
                'agent_id': self.agent_id
            }
    
    def process_lease_data(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process lease data directly"""
        self.status = AgentStatus.PROCESSING
        start_time = datetime.now()
        
        try:
            # Extract key lease fields
            extracted_fields = self._extract_lease_fields(document_data)
            
            # Validate extracted data
            validation_results = self._validate_lease_data(extracted_fields, document_data)
            
            # Detect anomalies
            anomalies = self._detect_lease_anomalies(extracted_fields, document_data)
            
            # Check asset correlations
            asset_correlations = self._check_asset_correlations(extracted_fields, document_data)
            
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
                'document_type': 'lease',
                'document_id': document_data.get('lease_number', 'unknown'),
                'extracted_fields': [field.__dict__ for field in extracted_fields],
                'validation_results': validation_results,
                'anomalies': anomalies,
                'asset_correlations': asset_correlations,
                'overall_confidence': overall_confidence,
                'processing_time': processing_time,
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Lease data processing failed: {e}")
            self.metrics.tasks_failed += 1
            
            return {
                'status': 'error',
                'message': str(e),
                'agent_id': self.agent_id
            }
    
    def _enhance_lease_processing(self, base_result: DocumentProcessingResult, 
                                 file_path: Path) -> Dict[str, Any]:
        """Enhance basic document processing with lease-specific logic"""
        
        # Load the original document for additional processing
        document = self.document_processor.load_document(file_path)
        
        # Additional lease-specific extractions
        enhanced_fields = []
        enhanced_fields.extend(base_result.extracted_fields)
        
        # Extract additional lease-specific fields
        additional_fields = [
            ('lease_type', str),
            ('security_deposit', float),
            ('maintenance_responsibility', str),
            ('insurance_requirements', str),
            ('early_termination_clause', str),
            ('purchase_option', dict),
            ('mileage_restrictions', str),  # For vehicle leases
            ('wear_and_tear_policy', str)
        ]
        
        for field_name, field_type in additional_fields:
            if field_name in document:
                result = self.document_processor.extract_field(
                    document, field_name, field_type
                )
                enhanced_fields.append(result)
        
        # Enhanced anomaly detection
        enhanced_anomalies = list(base_result.anomalies)
        enhanced_anomalies.extend(self._detect_advanced_lease_anomalies(document, enhanced_fields))
        
        # Asset correlation analysis
        asset_correlations = self._check_asset_correlations(enhanced_fields, document)
        
        return {
            'status': base_result.status,
            'document_type': base_result.document_type,
            'document_id': base_result.document_id,
            'extracted_fields': [field.__dict__ for field in enhanced_fields],
            'anomalies': enhanced_anomalies,
            'asset_correlations': asset_correlations,
            'overall_confidence': self._calculate_confidence(enhanced_fields),
            'processing_time': base_result.processing_time,
            'agent_id': self.agent_id,
            'file_path': str(file_path)
        }
    
    def _extract_lease_fields(self, document: Dict[str, Any]) -> List[ExtractionResult]:
        """Extract key fields from lease document"""
        fields = []
        
        # Define lease field mappings
        field_mappings = [
            ('lease_number', str, ['lease_number', 'agreement_number']),
            ('lease_start_date', str, ['lease_start_date', 'commencement_date']),
            ('lease_end_date', str, ['lease_end_date', 'expiration_date']),
            ('leased_asset.asset_id', str, ['leased_asset.asset_id']),
            ('leased_asset.description', str, ['leased_asset.description']),
            ('leased_asset.asset_type', str, ['leased_asset.asset_type']),
            ('lessor.name', str, ['lessor.name']),
            ('lessor.address', str, ['lessor.address']),
            ('lessee.name', str, ['lessee.name']),
            ('lessee.address', str, ['lessee.address']),
            ('financial_terms.monthly_payment', float, ['financial_terms.monthly_payment']),
            ('financial_terms.total_lease_value', float, ['financial_terms.total_lease_value']),
            ('financial_terms.security_deposit', float, ['financial_terms.security_deposit']),
            ('lease_term_months', int, ['lease_term_months', 'term_months']),
            ('lease_type', str, ['lease_type', 'type']),
            ('purchase_option', dict, ['purchase_option']),
            ('maintenance_responsibility', str, ['maintenance_responsibility']),
            ('insurance_requirements', str, ['insurance_requirements'])
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
    
    def _validate_lease_data(self, extracted_fields: List[ExtractionResult], 
                            document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate extracted lease data"""
        validation_results = []
        
        # Get field values for easy access
        field_values = {field.field_name: field.value for field in extracted_fields}
        
        # Validate required fields
        required_fields = [
            'lease_number', 'lease_start_date', 'leased_asset.asset_id',
            'lessor.name', 'lessee.name', 'financial_terms.monthly_payment'
        ]
        
        for field in required_fields:
            if field not in field_values or field_values[field] is None:
                validation_results.append({
                    'field': field,
                    'is_valid': False,
                    'severity': 'critical',
                    'message': f'Required lease field {field} is missing or null'
                })
            else:
                validation_results.append({
                    'field': field,
                    'is_valid': True,
                    'severity': 'info',
                    'message': f'Required lease field {field} is present'
                })
        
        # Validate financial amounts
        financial_fields = ['financial_terms.monthly_payment', 'financial_terms.total_lease_value', 'financial_terms.security_deposit']
        
        for field in financial_fields:
            if field in field_values and field_values[field]:
                amount_valid, amount_value, amount_message = self.document_processor.validate_amount(
                    field_values[field]
                )
                validation_results.append({
                    'field': field,
                    'is_valid': amount_valid,
                    'severity': 'high' if not amount_valid else 'info',
                    'message': amount_message or f'{field} validation: ${amount_value:,.2f}',
                    'validated_value': amount_value
                })
        
        # Validate dates
        date_fields = ['lease_start_date', 'lease_end_date']
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
        
        # Validate date relationships and lease term
        if 'lease_start_date' in validated_dates and 'lease_end_date' in validated_dates:
            start_date = validated_dates['lease_start_date']
            end_date = validated_dates['lease_end_date']
            
            if end_date <= start_date:
                validation_results.append({
                    'field': 'date_relationship',
                    'is_valid': False,
                    'severity': 'high',
                    'message': 'Lease end date must be after start date',
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                })
            else:
                # Calculate lease term in months
                lease_duration_days = (end_date - start_date).days
                lease_duration_months = lease_duration_days / 30.44  # Average days per month
                
                min_months = self.config.get('lease_term_min_months', 1)
                max_months = self.config.get('lease_term_max_months', 120)
                
                if lease_duration_months < min_months or lease_duration_months > max_months:
                    validation_results.append({
                        'field': 'lease_term',
                        'is_valid': False,
                        'severity': 'medium',
                        'message': f'Lease term {lease_duration_months:.1f} months outside normal range ({min_months}-{max_months} months)',
                        'lease_duration_months': lease_duration_months,
                        'min_allowed': min_months,
                        'max_allowed': max_months
                    })
        
        # Validate that lease does NOT have PO numbers (expected behavior)
        if self.config.get('expect_no_po_numbers', True):
            po_fields = [key for key in document.keys() if 'po' in key.lower() or 'purchase_order' in key.lower()]
            if not po_fields:
                validation_results.append({
                    'field': 'po_number_absence',
                    'is_valid': True,
                    'severity': 'info',
                    'message': 'Lease correctly does not contain purchase order numbers (expected behavior)',
                    'expected_behavior': True
                })
            else:
                validation_results.append({
                    'field': 'unexpected_po_presence',
                    'is_valid': False,
                    'severity': 'medium',
                    'message': f'Lease unexpectedly contains PO-related fields: {po_fields}',
                    'unexpected_fields': po_fields
                })
        
        return validation_results
    
    def _detect_lease_anomalies(self, extracted_fields: List[ExtractionResult], 
                               document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect lease-specific anomalies"""
        anomalies = []
        field_values = {field.field_name: field.value for field in extracted_fields}
        
        # Check for unusually high monthly payments
        monthly_payment = field_values.get('financial_terms.monthly_payment')
        if monthly_payment:
            try:
                payment_float = float(monthly_payment)
                threshold = self.config.get('monthly_payment_threshold', 50000)
                
                if payment_float > threshold:
                    anomalies.append({
                        'type': 'high_monthly_payment',
                        'severity': 'medium',
                        'description': f'Very high monthly lease payment: ${payment_float:,.2f}',
                        'monthly_payment': payment_float,
                        'threshold': threshold
                    })
                elif payment_float < 100:  # Very low payment
                    anomalies.append({
                        'type': 'low_monthly_payment',
                        'severity': 'low',
                        'description': f'Very low monthly lease payment: ${payment_float:,.2f}',
                        'monthly_payment': payment_float
                    })
                    
            except (ValueError, TypeError):
                pass
        
        # Check for missing asset information
        asset_id = field_values.get('leased_asset.asset_id')
        asset_description = field_values.get('leased_asset.description')
        
        if not asset_id:
            anomalies.append({
                'type': 'missing_asset_id',
                'severity': 'high',
                'description': 'Lease missing asset ID (critical for asset tracking)',
                'field': 'leased_asset.asset_id',
                'expected': True,
                'actual': None
            })
        
        if not asset_description or len(asset_description) < 10:
            anomalies.append({
                'type': 'insufficient_asset_description',
                'severity': 'medium',
                'description': f'Asset description too brief: "{asset_description}"',
                'field': 'leased_asset.description',
                'description_length': len(asset_description) if asset_description else 0
            })
        
        # Check for missing critical lease terms
        critical_terms = ['maintenance_responsibility', 'insurance_requirements']
        for term in critical_terms:
            if term not in field_values or not field_values[term]:
                anomalies.append({
                    'type': 'missing_lease_term',
                    'severity': 'medium',
                    'description': f'Missing critical lease term: {term}',
                    'field': term,
                    'expected': True,
                    'actual': None
                })
        
        # Check payment vs total value consistency
        monthly_payment = field_values.get('financial_terms.monthly_payment')
        total_value = field_values.get('financial_terms.total_lease_value')
        lease_term = field_values.get('lease_term_months')
        
        if monthly_payment and total_value and lease_term:
            try:
                monthly_float = float(monthly_payment)
                total_float = float(total_value)
                term_int = int(lease_term)
                
                calculated_total = monthly_float * term_int
                variance = abs(calculated_total - total_float) / total_float if total_float > 0 else 0
                
                if variance > 0.05:  # 5% variance threshold
                    anomalies.append({
                        'type': 'payment_total_mismatch',
                        'severity': 'medium',
                        'description': f'Monthly payment total ({calculated_total:,.2f}) doesn\'t match stated total ({total_float:,.2f})',
                        'calculated_total': calculated_total,
                        'stated_total': total_float,
                        'variance_percentage': variance,
                        'monthly_payment': monthly_float,
                        'lease_term_months': term_int
                    })
                    
            except (ValueError, TypeError):
                pass
        
        # Check for low confidence extractions
        for field in extracted_fields:
            if field.confidence < self.config.get('confidence_threshold', 0.82):
                anomalies.append({
                    'type': 'low_confidence_extraction',
                    'severity': 'medium',
                    'description': f'Low confidence extraction for {field.field_name}',
                    'field': field.field_name,
                    'confidence': field.confidence,
                    'threshold': self.config.get('confidence_threshold', 0.82),
                    'value': field.value
                })
        
        return anomalies
    
    def _detect_advanced_lease_anomalies(self, document: Dict[str, Any], 
                                        fields: List[ExtractionResult]) -> List[Dict[str, Any]]:
        """Detect advanced lease anomalies"""
        anomalies = []
        
        # Check for lease-to-own indicators
        purchase_option = document.get('purchase_option', {})
        if purchase_option:
            # If there's a purchase option, check if it's reasonable
            purchase_price = purchase_option.get('purchase_price', 0)
            if purchase_price:
                try:
                    purchase_float = float(purchase_price)
                    
                    # Get total lease payments
                    monthly_payment = document.get('financial_terms', {}).get('monthly_payment', 0)
                    lease_term = document.get('lease_term_months', 0)
                    
                    if monthly_payment and lease_term:
                        total_payments = float(monthly_payment) * int(lease_term)
                        
                        # If purchase price is very low compared to total payments, might be lease-to-own
                        if purchase_float < (total_payments * 0.1):  # Less than 10% of total payments
                            anomalies.append({
                                'type': 'potential_lease_to_own',
                                'severity': 'info',
                                'description': f'Low purchase option price suggests lease-to-own: ${purchase_float:,.2f}',
                                'purchase_price': purchase_float,
                                'total_lease_payments': total_payments,
                                'purchase_to_payment_ratio': purchase_float / total_payments
                            })
                            
                except (ValueError, TypeError):
                    pass
        
        # Check for asset type consistency
        asset_type = document.get('leased_asset', {}).get('asset_type', '').lower()
        lease_type = document.get('lease_type', '').lower()
        
        if asset_type and lease_type:
            # Check for logical consistency
            if 'vehicle' in asset_type and 'equipment' in lease_type:
                anomalies.append({
                    'type': 'asset_lease_type_mismatch',
                    'severity': 'low',
                    'description': f'Asset type "{asset_type}" may not match lease type "{lease_type}"',
                    'asset_type': asset_type,
                    'lease_type': lease_type
                })
        
        return anomalies
    
    def _check_asset_correlations(self, extracted_fields: List[ExtractionResult], 
                                 document: Dict[str, Any]) -> Dict[str, Any]:
        """Check for correlations with fixed asset agreements"""
        correlations = {
            'found_correlations': [],
            'potential_lease_to_own': False,
            'correlation_details': []
        }
        
        # Get asset ID from lease
        asset_id = None
        for field in extracted_fields:
            if field.field_name == 'leased_asset.asset_id' and field.value:
                asset_id = field.value
                break
        
        if not asset_id:
            return correlations
        
        # Check against processed fixed assets
        if asset_id in self.processed_assets:
            asset_data = self.processed_assets[asset_id]
            correlations['found_correlations'].append(asset_id)
            correlations['potential_lease_to_own'] = True
            
            # Extract details for comparison
            lease_monthly = document.get('financial_terms', {}).get('monthly_payment', 0)
            lease_total = document.get('financial_terms', {}).get('total_lease_value', 0)
            
            # Try to extract asset purchase price from the stored data
            asset_price = 0
            asset_fields = asset_data.get('extracted_fields', [])
            for field in asset_fields:
                if field.get('field_name') == 'financial_details.purchase_price':
                    try:
                        asset_price = float(field.get('value', 0))
                    except (ValueError, TypeError):
                        pass
                    break
            
            correlations['correlation_details'].append({
                'asset_id': asset_id,
                'lease_monthly_payment': lease_monthly,
                'lease_total_value': lease_total,
                'asset_purchase_price': asset_price,
                'correlation_type': 'lease_to_own' if asset_price > 0 else 'asset_match'
            })
        
        return correlations
    
    def _extract_asset_id_from_response(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Extract asset ID from fixed asset agent response"""
        extracted_fields = response_data.get('extracted_fields', [])
        for field in extracted_fields:
            if field.get('field_name') == 'asset_details.asset_id':
                return field.get('value')
        return None
    
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
    
    def _get_lease_summary(self, lease_id: str) -> Dict[str, Any]:
        """Get summary of processed lease"""
        return {
            'status': 'info',
            'message': f'Lease summary for {lease_id} not implemented yet'
        }
    
    def _get_asset_correlation(self, asset_id: str) -> Dict[str, Any]:
        """Get asset correlation information"""
        if asset_id in self.processed_assets:
            return {
                'status': 'found',
                'asset_id': asset_id,
                'correlation_type': 'lease_to_own',
                'asset_data': self.processed_assets[asset_id]
            }
        else:
            return {
                'status': 'not_found',
                'asset_id': asset_id,
                'message': 'No correlation found with fixed asset agreements'
            }
    
    def _get_lease_statistics(self) -> Dict[str, Any]:
        """Get lease processing statistics"""
        return {
            'status': 'success',
            'statistics': {
                'total_processed': self.metrics.tasks_completed + self.metrics.tasks_failed,
                'successful': self.metrics.tasks_completed,
                'failed': self.metrics.tasks_failed,
                'average_processing_time': (
                    self.metrics.total_processing_time / max(1, self.metrics.tasks_completed + self.metrics.tasks_failed)
                ),
                'confidence_threshold': self.config.get('confidence_threshold', 0.82),
                'asset_correlations_found': len(self.processed_assets),
                'agent_id': self.agent_id
            }
        }