"""
MSA Agent - Processes Master Service Agreements
"""
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta

from .base_agent import BaseAgent, AgentStatus
from utils.message_queue import Message, MessageType, MessagePriority
from utils.document_processor import DocumentProcessor, ExtractionResult, DocumentProcessingResult
from config.settings import DATA_DIR

class MSAAgent(BaseAgent):
    """Agent specialized in Master Service Agreement processing"""
    
    def __init__(self, agent_id: str, message_queue):
        super().__init__(agent_id, message_queue)
        self.document_processor = DocumentProcessor()
        
        # Agent-specific configuration
        self.config.update({
            'confidence_threshold': 0.80,
            'max_processing_time': 75,
            'validate_framework_terms': True,
            'expect_no_po_numbers': True,  # MSAs should NOT have PO numbers
            'validate_service_scope': True,
            'check_renewal_terms': True,
            'validate_sla_terms': True
        })
        
        self.logger.info(f"MSA Agent {agent_id} initialized")
    
    def process_message(self, message: Message) -> Dict[str, Any]:
        """Process incoming messages"""
        try:
            if message.msg_type == MessageType.TASK_ASSIGNMENT:
                return self._handle_msa_task(message)
            elif message.msg_type == MessageType.DATA_REQUEST:
                return self._handle_data_request(message)
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
    
    def _handle_msa_task(self, message: Message) -> Dict[str, Any]:
        """Handle MSA processing tasks"""
        task_data = message.content
        
        if 'file_path' in task_data:
            # Process file
            file_path = Path(task_data['file_path'])
            return self.process_msa_file(file_path)
        elif 'document_data' in task_data:
            # Process document data directly
            document_data = task_data['document_data']
            return self.process_msa_data(document_data)
        else:
            return {
                'status': 'error',
                'message': 'Missing file_path or document_data in task'
            }
    
    def _handle_data_request(self, message: Message) -> Dict[str, Any]:
        """Handle data requests from other agents"""
        request_data = message.content
        request_type = request_data.get('request_type')
        
        if request_type == 'msa_summary':
            return self._get_msa_summary(request_data.get('msa_id'))
        elif request_type == 'framework_terms':
            return self._get_framework_terms(request_data.get('msa_id'))
        elif request_type == 'msa_stats':
            return self._get_msa_statistics()
        else:
            return {
                'status': 'error',
                'message': f'Unknown request type: {request_type}'
            }
    
    def process_msa_file(self, file_path: Path) -> Dict[str, Any]:
        """Process an MSA file"""
        self.status = AgentStatus.PROCESSING
        start_time = datetime.now()
        
        try:
            # Use document processor for basic processing
            result = self.document_processor.process_document(file_path, 'msa')
            
            # Enhanced MSA-specific processing
            enhanced_result = self._enhance_msa_processing(result, file_path)
            
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
            self.logger.error(f"MSA processing failed for {file_path}: {e}")
            self.metrics.tasks_failed += 1
            
            return {
                'status': 'error',
                'message': str(e),
                'file_path': str(file_path),
                'agent_id': self.agent_id
            }
    
    def process_msa_data(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process MSA data directly"""
        self.status = AgentStatus.PROCESSING
        start_time = datetime.now()
        
        try:
            # Extract key MSA fields
            extracted_fields = self._extract_msa_fields(document_data)
            
            # Validate extracted data
            validation_results = self._validate_msa_data(extracted_fields, document_data)
            
            # Detect anomalies (including expected ones)
            anomalies = self._detect_msa_anomalies(extracted_fields, document_data)
            
            # Validate framework terms
            framework_validations = self._validate_framework_terms(document_data)
            
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
                'document_type': 'msa',
                'document_id': document_data.get('msa_number', 'unknown'),
                'extracted_fields': [field.__dict__ for field in extracted_fields],
                'validation_results': validation_results,
                'framework_validations': framework_validations,
                'anomalies': anomalies,
                'overall_confidence': overall_confidence,
                'processing_time': processing_time,
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"MSA data processing failed: {e}")
            self.metrics.tasks_failed += 1
            
            return {
                'status': 'error',
                'message': str(e),
                'agent_id': self.agent_id
            }
    
    def _enhance_msa_processing(self, base_result: DocumentProcessingResult, 
                               file_path: Path) -> Dict[str, Any]:
        """Enhance basic document processing with MSA-specific logic"""
        
        # Load the original document for additional processing
        document = self.document_processor.load_document(file_path)
        
        # Additional MSA-specific extractions
        enhanced_fields = []
        enhanced_fields.extend(base_result.extracted_fields)
        
        # Extract additional MSA-specific fields
        additional_fields = [
            ('service_scope', str),
            ('sla_terms', dict),
            ('renewal_terms', str),
            ('termination_conditions', str),
            ('pricing_model', str),
            ('performance_metrics', dict),
            ('confidentiality_terms', str),
            ('intellectual_property', str)
        ]
        
        for field_name, field_type in additional_fields:
            if field_name in document:
                result = self.document_processor.extract_field(
                    document, field_name, field_type
                )
                enhanced_fields.append(result)
        
        # Enhanced anomaly detection
        enhanced_anomalies = list(base_result.anomalies)
        enhanced_anomalies.extend(self._detect_advanced_msa_anomalies(document, enhanced_fields))
        
        # MSA-specific validations
        framework_validations = self._validate_framework_terms(document)
        
        return {
            'status': base_result.status,
            'document_type': base_result.document_type,
            'document_id': base_result.document_id,
            'extracted_fields': [field.__dict__ for field in enhanced_fields],
            'anomalies': enhanced_anomalies,
            'framework_validations': framework_validations,
            'overall_confidence': self._calculate_confidence(enhanced_fields),
            'processing_time': base_result.processing_time,
            'agent_id': self.agent_id,
            'file_path': str(file_path)
        }
    
    def _extract_msa_fields(self, document: Dict[str, Any]) -> List[ExtractionResult]:
        """Extract key fields from MSA document"""
        fields = []
        
        # Define MSA field mappings
        field_mappings = [
            ('msa_number', str, ['msa_number', 'agreement_number']),
            ('effective_date', str, ['effective_date', 'start_date']),
            ('expiration_date', str, ['expiration_date', 'end_date', 'term_end']),
            ('parties.client.name', str, ['parties.client.name']),
            ('parties.client.address', str, ['parties.client.address']),
            ('parties.service_provider.name', str, ['parties.service_provider.name']),
            ('parties.service_provider.address', str, ['parties.service_provider.address']),
            ('service_scope', str, ['service_scope', 'scope_of_services']),
            ('pricing_model', str, ['pricing_model', 'pricing_structure']),
            ('renewal_terms', str, ['renewal_terms', 'auto_renewal']),
            ('termination_notice', str, ['termination_notice', 'notice_period']),
            ('governing_law', str, ['governing_law']),
            ('confidentiality_period', str, ['confidentiality_period']),
            ('sla_terms', dict, ['sla_terms', 'service_level_agreement'])
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
    
    def _validate_msa_data(self, extracted_fields: List[ExtractionResult], 
                          document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate extracted MSA data"""
        validation_results = []
        
        # Get field values for easy access
        field_values = {field.field_name: field.value for field in extracted_fields}
        
        # Validate required fields for MSA
        required_fields = [
            'msa_number', 'effective_date', 'parties.client.name', 
            'parties.service_provider.name', 'service_scope'
        ]
        
        for field in required_fields:
            if field not in field_values or field_values[field] is None:
                validation_results.append({
                    'field': field,
                    'is_valid': False,
                    'severity': 'critical',
                    'message': f'Required MSA field {field} is missing or null'
                })
            else:
                validation_results.append({
                    'field': field,
                    'is_valid': True,
                    'severity': 'info',
                    'message': f'Required MSA field {field} is present'
                })
        
        # Validate dates
        date_fields = ['effective_date', 'expiration_date']
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
                    'message': 'MSA expiration date must be after effective date',
                    'effective_date': validated_dates['effective_date'].isoformat(),
                    'expiration_date': validated_dates['expiration_date'].isoformat()
                })
        
        # Validate that MSA does NOT have PO numbers (expected behavior)
        if self.config.get('expect_no_po_numbers', True):
            po_fields = [key for key in document.keys() if 'po' in key.lower() or 'purchase_order' in key.lower()]
            if not po_fields:
                validation_results.append({
                    'field': 'po_number_absence',
                    'is_valid': True,
                    'severity': 'info',
                    'message': 'MSA correctly does not contain purchase order numbers (expected behavior)',
                    'expected_behavior': True
                })
            else:
                validation_results.append({
                    'field': 'unexpected_po_presence',
                    'is_valid': False,
                    'severity': 'medium',
                    'message': f'MSA unexpectedly contains PO-related fields: {po_fields}',
                    'unexpected_fields': po_fields
                })
        
        return validation_results
    
    def _detect_msa_anomalies(self, extracted_fields: List[ExtractionResult], 
                             document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect MSA-specific anomalies"""
        anomalies = []
        field_values = {field.field_name: field.value for field in extracted_fields}
        
        # Check for MSA term length
        effective_date = field_values.get('effective_date')
        expiration_date = field_values.get('expiration_date')
        
        if effective_date and expiration_date:
            try:
                eff_date_valid, eff_date, _ = self.document_processor.validate_date(effective_date)
                exp_date_valid, exp_date, _ = self.document_processor.validate_date(expiration_date)
                
                if eff_date_valid and exp_date_valid:
                    msa_duration = (exp_date - eff_date).days
                    
                    # MSAs are typically long-term agreements
                    if msa_duration < 365:  # Less than 1 year
                        anomalies.append({
                            'type': 'short_msa_term',
                            'severity': 'medium',
                            'description': f'Short MSA term: {msa_duration} days (MSAs typically span 1+ years)',
                            'duration_days': msa_duration,
                            'duration_years': msa_duration / 365,
                            'effective_date': eff_date.isoformat(),
                            'expiration_date': exp_date.isoformat()
                        })
                    elif msa_duration > 1825:  # More than 5 years
                        anomalies.append({
                            'type': 'long_msa_term',
                            'severity': 'low',
                            'description': f'Very long MSA term: {msa_duration} days ({msa_duration/365:.1f} years)',
                            'duration_days': msa_duration,
                            'duration_years': msa_duration / 365
                        })
                        
            except Exception:
                pass
        
        # Check for missing critical MSA components
        critical_msa_terms = ['service_scope', 'sla_terms', 'pricing_model']
        for term in critical_msa_terms:
            if term not in field_values or not field_values[term]:
                anomalies.append({
                    'type': 'missing_msa_component',
                    'severity': 'medium',
                    'description': f'Missing critical MSA component: {term}',
                    'field': term,
                    'expected': True,
                    'actual': None
                })
        
        # Check for vague service scope
        service_scope = field_values.get('service_scope', '')
        if service_scope and len(service_scope) < 50:  # Very short service scope
            anomalies.append({
                'type': 'vague_service_scope',
                'severity': 'medium',
                'description': f'Service scope seems too brief: {len(service_scope)} characters',
                'service_scope_length': len(service_scope),
                'service_scope': service_scope[:100] + '...' if len(service_scope) > 100 else service_scope
            })
        
        # Check for missing renewal terms (important for MSAs)
        renewal_terms = field_values.get('renewal_terms')
        if not renewal_terms:
            anomalies.append({
                'type': 'missing_renewal_terms',
                'severity': 'medium',
                'description': 'MSA missing renewal terms (important for framework agreements)',
                'field': 'renewal_terms',
                'expected': True,
                'actual': None
            })
        
        # Check for low confidence extractions
        for field in extracted_fields:
            if field.confidence < self.config.get('confidence_threshold', 0.80):
                anomalies.append({
                    'type': 'low_confidence_extraction',
                    'severity': 'medium',
                    'description': f'Low confidence extraction for {field.field_name}',
                    'field': field.field_name,
                    'confidence': field.confidence,
                    'threshold': self.config.get('confidence_threshold', 0.80),
                    'value': field.value
                })
        
        return anomalies
    
    def _detect_advanced_msa_anomalies(self, document: Dict[str, Any], 
                                      fields: List[ExtractionResult]) -> List[Dict[str, Any]]:
        """Detect advanced MSA anomalies"""
        anomalies = []
        
        # Check for SLA completeness
        sla_terms = document.get('sla_terms', {})
        if sla_terms:
            expected_sla_components = ['availability', 'response_time', 'resolution_time', 'performance_metrics']
            missing_components = []
            
            for component in expected_sla_components:
                if component not in sla_terms:
                    missing_components.append(component)
            
            if missing_components:
                anomalies.append({
                    'type': 'incomplete_sla',
                    'severity': 'medium',
                    'description': f'SLA missing components: {", ".join(missing_components)}',
                    'missing_components': missing_components,
                    'expected_components': expected_sla_components
                })
        else:
            anomalies.append({
                'type': 'missing_sla',
                'severity': 'high',
                'description': 'MSA missing Service Level Agreement terms',
                'field': 'sla_terms',
                'expected': True,
                'actual': None
            })
        
        # Check pricing model clarity
        pricing_model = document.get('pricing_model', '')
        if pricing_model:
            # Check if pricing model is specific enough
            vague_terms = ['tbd', 'to be determined', 'negotiable', 'varies']
            if any(term in pricing_model.lower() for term in vague_terms):
                anomalies.append({
                    'type': 'vague_pricing_model',
                    'severity': 'medium',
                    'description': 'Pricing model contains vague terms',
                    'pricing_model': pricing_model,
                    'vague_terms_found': [term for term in vague_terms if term in pricing_model.lower()]
                })
        
        # Check for confidentiality terms
        confidentiality_terms = document.get('confidentiality_terms', '')
        if not confidentiality_terms:
            anomalies.append({
                'type': 'missing_confidentiality',
                'severity': 'medium',
                'description': 'MSA missing confidentiality terms (important for service agreements)',
                'field': 'confidentiality_terms',
                'expected': True,
                'actual': None
            })
        
        return anomalies
    
    def _validate_framework_terms(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate MSA framework-specific terms"""
        validations = []
        
        # Validate service scope structure
        service_scope = document.get('service_scope', '')
        if service_scope:
            # Check if service scope includes key elements
            key_elements = ['deliverables', 'responsibilities', 'exclusions', 'assumptions']
            found_elements = [elem for elem in key_elements if elem in service_scope.lower()]
            
            validations.append({
                'term': 'service_scope_completeness',
                'is_valid': len(found_elements) >= 2,  # At least 2 key elements
                'value': f"{len(found_elements)}/{len(key_elements)} key elements found",
                'found_elements': found_elements,
                'missing_elements': [elem for elem in key_elements if elem not in found_elements],
                'message': f'Service scope contains {len(found_elements)} of {len(key_elements)} key elements',
                'severity': 'medium' if len(found_elements) < 2 else 'info'
            })
        
        # Validate termination notice period
        termination_notice = document.get('termination_notice', '')
        if termination_notice:
            # Extract notice period (look for numbers followed by days/months)
            import re
            notice_match = re.search(r'(\d+)\s*(day|month|week)', termination_notice.lower())
            
            if notice_match:
                period_num = int(notice_match.group(1))
                period_unit = notice_match.group(2)
                
                # Convert to days for comparison
                if period_unit == 'month':
                    period_days = period_num * 30
                elif period_unit == 'week':
                    period_days = period_num * 7
                else:
                    period_days = period_num
                
                # MSAs typically require 30-90 days notice
                is_reasonable = 30 <= period_days <= 90
                
                validations.append({
                    'term': 'termination_notice_period',
                    'is_valid': is_reasonable,
                    'value': termination_notice,
                    'period_days': period_days,
                    'message': f'Termination notice period: {period_days} days' + 
                              (' (reasonable for MSA)' if is_reasonable else ' (may be too short/long for MSA)'),
                    'severity': 'low' if not is_reasonable else 'info'
                })
        
        # Validate renewal terms structure
        renewal_terms = document.get('renewal_terms', '')
        if renewal_terms:
            # Check for auto-renewal indicators
            auto_renewal_indicators = ['automatic', 'auto-renew', 'automatically renew']
            has_auto_renewal = any(indicator in renewal_terms.lower() for indicator in auto_renewal_indicators)
            
            validations.append({
                'term': 'renewal_mechanism',
                'is_valid': True,  # Having any renewal terms is good
                'value': renewal_terms,
                'has_auto_renewal': has_auto_renewal,
                'message': f'Renewal terms specified' + (' with auto-renewal' if has_auto_renewal else ' (manual renewal)'),
                'severity': 'info'
            })
        
        return validations
    
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
    
    def _get_msa_summary(self, msa_id: str) -> Dict[str, Any]:
        """Get summary of processed MSA"""
        return {
            'status': 'info',
            'message': f'MSA summary for {msa_id} not implemented yet'
        }
    
    def _get_framework_terms(self, msa_id: str) -> Dict[str, Any]:
        """Get framework terms for MSA"""
        return {
            'status': 'info',
            'message': f'Framework terms for MSA {msa_id} not implemented yet'
        }
    
    def _get_msa_statistics(self) -> Dict[str, Any]:
        """Get MSA processing statistics"""
        return {
            'status': 'success',
            'statistics': {
                'total_processed': self.metrics.tasks_completed + self.metrics.tasks_failed,
                'successful': self.metrics.tasks_completed,
                'failed': self.metrics.tasks_failed,
                'average_processing_time': (
                    self.metrics.total_processing_time / max(1, self.metrics.tasks_completed + self.metrics.tasks_failed)
                ),
                'confidence_threshold': self.config.get('confidence_threshold', 0.80),
                'agent_id': self.agent_id
            }
        }