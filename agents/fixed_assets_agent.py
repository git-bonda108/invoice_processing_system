"""
Fixed Assets Agent - Processes fixed asset agreements and correlations
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

class FixedAssetsAgent(BaseAgent):
    """Agent specialized in fixed asset agreement processing and depreciation analysis"""
    
    def __init__(self, agent_id: str, message_queue):
        super().__init__(agent_id, message_queue)
        self.document_processor = DocumentProcessor()
        
        # Agent-specific configuration
        self.config.update({
            'confidence_threshold': 0.85,
            'max_processing_time': 85,
            'validate_depreciation': True,
            'check_lease_correlations': True,
            'validate_asset_specifications': True,
            'min_asset_value': 1000,  # Minimum value to be considered fixed asset
            'max_useful_life_years': 50,  # Maximum reasonable useful life
            'depreciation_methods': ['straight-line', 'declining balance', 'units of production', 'sum of years digits']
        })
        
        # Cache for lease correlations
        self.processed_leases = {}
        
        self.logger.info(f"Fixed Assets Agent {agent_id} initialized")
    
    def process_message(self, message: Message) -> Dict[str, Any]:
        """Process incoming messages"""
        try:
            if message.msg_type == MessageType.TASK_ASSIGNMENT:
                return self._handle_asset_task(message)
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
    
    def _handle_asset_task(self, message: Message) -> Dict[str, Any]:
        """Handle fixed asset processing tasks"""
        task_data = message.content
        
        if 'file_path' in task_data:
            # Process file
            file_path = Path(task_data['file_path'])
            return self.process_asset_file(file_path)
        elif 'document_data' in task_data:
            # Process document data directly
            document_data = task_data['document_data']
            return self.process_asset_data(document_data)
        else:
            return {
                'status': 'error',
                'message': 'Missing file_path or document_data in task'
            }
    
    def _handle_data_request(self, message: Message) -> Dict[str, Any]:
        """Handle data requests from other agents"""
        request_data = message.content
        request_type = request_data.get('request_type')
        
        if request_type == 'asset_summary':
            return self._get_asset_summary(request_data.get('asset_id'))
        elif request_type == 'depreciation_schedule':
            return self._get_depreciation_schedule(request_data.get('asset_id'))
        elif request_type == 'lease_correlation':
            return self._get_lease_correlation(request_data.get('asset_id'))
        elif request_type == 'asset_stats':
            return self._get_asset_statistics()
        else:
            return {
                'status': 'error',
                'message': f'Unknown request type: {request_type}'
            }
    
    def _handle_data_response(self, message: Message) -> Dict[str, Any]:
        """Handle data responses from other agents"""
        # Store lease data for correlation
        response_data = message.content
        if response_data.get('document_type') == 'lease':
            asset_id = self._extract_asset_id_from_response(response_data)
            if asset_id:
                self.processed_leases[asset_id] = response_data
        
        return {'status': 'acknowledged'}
    
    def process_asset_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a fixed asset file"""
        self.status = AgentStatus.PROCESSING
        start_time = datetime.now()
        
        try:
            # Use document processor for basic processing
            result = self.document_processor.process_document(file_path, 'fixed_asset')
            
            # Enhanced asset-specific processing
            enhanced_result = self._enhance_asset_processing(result, file_path)
            
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
            self.logger.error(f"Asset processing failed for {file_path}: {e}")
            self.metrics.tasks_failed += 1
            
            return {
                'status': 'error',
                'message': str(e),
                'file_path': str(file_path),
                'agent_id': self.agent_id
            }
    
    def process_asset_data(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process fixed asset data directly"""
        self.status = AgentStatus.PROCESSING
        start_time = datetime.now()
        
        try:
            # Extract key asset fields
            extracted_fields = self._extract_asset_fields(document_data)
            
            # Validate extracted data
            validation_results = self._validate_asset_data(extracted_fields, document_data)
            
            # Detect anomalies
            anomalies = self._detect_asset_anomalies(extracted_fields, document_data)
            
            # Validate depreciation calculations
            depreciation_analysis = self._analyze_depreciation(extracted_fields, document_data)
            
            # Check lease correlations
            lease_correlations = self._check_lease_correlations(extracted_fields, document_data)
            
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
                'document_type': 'fixed_asset',
                'document_id': document_data.get('agreement_number', 'unknown'),
                'extracted_fields': [field.__dict__ for field in extracted_fields],
                'validation_results': validation_results,
                'anomalies': anomalies,
                'depreciation_analysis': depreciation_analysis,
                'lease_correlations': lease_correlations,
                'overall_confidence': overall_confidence,
                'processing_time': processing_time,
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Asset data processing failed: {e}")
            self.metrics.tasks_failed += 1
            
            return {
                'status': 'error',
                'message': str(e),
                'agent_id': self.agent_id
            }
    
    def _enhance_asset_processing(self, base_result: DocumentProcessingResult, 
                                 file_path: Path) -> Dict[str, Any]:
        """Enhance basic document processing with asset-specific logic"""
        
        # Load the original document for additional processing
        document = self.document_processor.load_document(file_path)
        
        # Additional asset-specific extractions
        enhanced_fields = []
        enhanced_fields.extend(base_result.extracted_fields)
        
        # Extract additional asset-specific fields
        additional_fields = [
            ('asset_category', str),
            ('installation_date', str),
            ('warranty_expiration', str),
            ('maintenance_schedule', str),
            ('location', str),
            ('responsible_department', str),
            ('insurance_value', float),
            ('disposal_method', str)
        ]
        
        for field_name, field_type in additional_fields:
            if field_name in document:
                result = self.document_processor.extract_field(
                    document, field_name, field_type
                )
                enhanced_fields.append(result)
        
        # Enhanced anomaly detection
        enhanced_anomalies = list(base_result.anomalies)
        enhanced_anomalies.extend(self._detect_advanced_asset_anomalies(document, enhanced_fields))
        
        # Depreciation analysis
        depreciation_analysis = self._analyze_depreciation(enhanced_fields, document)
        
        # Lease correlation analysis
        lease_correlations = self._check_lease_correlations(enhanced_fields, document)
        
        return {
            'status': base_result.status,
            'document_type': base_result.document_type,
            'document_id': base_result.document_id,
            'extracted_fields': [field.__dict__ for field in enhanced_fields],
            'anomalies': enhanced_anomalies,
            'depreciation_analysis': depreciation_analysis,
            'lease_correlations': lease_correlations,
            'overall_confidence': self._calculate_confidence(enhanced_fields),
            'processing_time': base_result.processing_time,
            'agent_id': self.agent_id,
            'file_path': str(file_path)
        }
    
    def _extract_asset_fields(self, document: Dict[str, Any]) -> List[ExtractionResult]:
        """Extract key fields from fixed asset document"""
        fields = []
        
        # Define asset field mappings
        field_mappings = [
            ('agreement_number', str, ['agreement_number', 'asset_agreement_number']),
            ('acquisition_date', str, ['acquisition_date', 'purchase_date']),
            ('asset_details.asset_id', str, ['asset_details.asset_id']),
            ('asset_details.asset_type', str, ['asset_details.asset_type']),
            ('asset_details.description', str, ['asset_details.description']),
            ('asset_details.model_number', str, ['asset_details.model_number']),
            ('asset_details.serial_number', str, ['asset_details.serial_number']),
            ('asset_details.manufacturer', str, ['asset_details.manufacturer']),
            ('buyer.name', str, ['buyer.name']),
            ('buyer.address', str, ['buyer.address']),
            ('seller.name', str, ['seller.name']),
            ('seller.address', str, ['seller.address']),
            ('financial_details.purchase_price', float, ['financial_details.purchase_price']),
            ('financial_details.depreciation_method', str, ['financial_details.depreciation_method']),
            ('financial_details.useful_life_years', int, ['financial_details.useful_life_years']),
            ('financial_details.salvage_value', float, ['financial_details.salvage_value']),
            ('warranty_terms.warranty_period', str, ['warranty_terms.warranty_period']),
            ('warranty_terms.warranty_provider', str, ['warranty_terms.warranty_provider']),
            ('delivery_terms.delivery_date', str, ['delivery_terms.delivery_date']),
            ('delivery_terms.installation_included', bool, ['delivery_terms.installation_included'])
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
    
    def _validate_asset_data(self, extracted_fields: List[ExtractionResult], 
                            document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate extracted asset data"""
        validation_results = []
        
        # Get field values for easy access
        field_values = {field.field_name: field.value for field in extracted_fields}
        
        # Validate required fields
        required_fields = [
            'agreement_number', 'acquisition_date', 'asset_details.asset_id',
            'asset_details.description', 'buyer.name', 'seller.name',
            'financial_details.purchase_price'
        ]
        
        for field in required_fields:
            if field not in field_values or field_values[field] is None:
                validation_results.append({
                    'field': field,
                    'is_valid': False,
                    'severity': 'critical',
                    'message': f'Required asset field {field} is missing or null'
                })
            else:
                validation_results.append({
                    'field': field,
                    'is_valid': True,
                    'severity': 'info',
                    'message': f'Required asset field {field} is present'
                })
        
        # Validate financial amounts
        financial_fields = [
            'financial_details.purchase_price', 
            'financial_details.salvage_value'
        ]
        
        for field in financial_fields:
            if field in field_values and field_values[field] is not None:
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
        
        # Validate asset value threshold
        purchase_price = field_values.get('financial_details.purchase_price')
        if purchase_price:
            try:
                price_float = float(purchase_price)
                min_value = self.config.get('min_asset_value', 1000)
                
                if price_float < min_value:
                    validation_results.append({
                        'field': 'financial_details.purchase_price',
                        'is_valid': False,
                        'severity': 'medium',
                        'message': f'Asset value ${price_float:,.2f} below fixed asset threshold ${min_value:,.2f}',
                        'asset_value': price_float,
                        'threshold': min_value
                    })
                    
            except (ValueError, TypeError):
                pass
        
        # Validate useful life
        useful_life = field_values.get('financial_details.useful_life_years')
        if useful_life:
            try:
                life_int = int(useful_life)
                max_life = self.config.get('max_useful_life_years', 50)
                
                if life_int <= 0:
                    validation_results.append({
                        'field': 'financial_details.useful_life_years',
                        'is_valid': False,
                        'severity': 'high',
                        'message': 'Useful life must be positive',
                        'useful_life': life_int
                    })
                elif life_int > max_life:
                    validation_results.append({
                        'field': 'financial_details.useful_life_years',
                        'is_valid': False,
                        'severity': 'medium',
                        'message': f'Useful life {life_int} years exceeds reasonable maximum {max_life} years',
                        'useful_life': life_int,
                        'max_allowed': max_life
                    })
                    
            except (ValueError, TypeError):
                pass
        
        # Validate depreciation method
        depreciation_method = field_values.get('financial_details.depreciation_method')
        if depreciation_method:
            valid_methods = self.config.get('depreciation_methods', [])
            method_lower = depreciation_method.lower()
            
            is_valid_method = any(method.lower() in method_lower for method in valid_methods)
            
            validation_results.append({
                'field': 'financial_details.depreciation_method',
                'is_valid': is_valid_method,
                'severity': 'medium' if not is_valid_method else 'info',
                'message': f'Depreciation method "{depreciation_method}" {"is valid" if is_valid_method else "may not be standard"}',
                'method': depreciation_method,
                'valid_methods': valid_methods
            })
        
        # Validate dates
        date_fields = ['acquisition_date', 'delivery_terms.delivery_date']
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
        
        return validation_results
    
    def _detect_asset_anomalies(self, extracted_fields: List[ExtractionResult], 
                               document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect asset-specific anomalies"""
        anomalies = []
        field_values = {field.field_name: field.value for field in extracted_fields}
        
        # Check for missing asset specifications
        spec_fields = ['asset_details.model_number', 'asset_details.serial_number', 'asset_details.manufacturer']
        missing_specs = []
        
        for spec_field in spec_fields:
            if spec_field not in field_values or not field_values[spec_field]:
                missing_specs.append(spec_field)
        
        if missing_specs:
            anomalies.append({
                'type': 'missing_asset_specifications',
                'severity': 'medium',
                'description': f'Missing asset specifications: {", ".join(missing_specs)}',
                'missing_fields': missing_specs,
                'expected_fields': spec_fields
            })
        
        # Check depreciation logic
        purchase_price = field_values.get('financial_details.purchase_price')
        salvage_value = field_values.get('financial_details.salvage_value')
        
        if purchase_price and salvage_value:
            try:
                price_float = float(purchase_price)
                salvage_float = float(salvage_value)
                
                if salvage_float > price_float:
                    anomalies.append({
                        'type': 'invalid_salvage_value',
                        'severity': 'high',
                        'description': f'Salvage value ${salvage_float:,.2f} exceeds purchase price ${price_float:,.2f}',
                        'purchase_price': price_float,
                        'salvage_value': salvage_float
                    })
                elif salvage_float > (price_float * 0.5):  # Salvage > 50% of purchase price
                    anomalies.append({
                        'type': 'high_salvage_value',
                        'severity': 'medium',
                        'description': f'High salvage value: {(salvage_float/price_float)*100:.1f}% of purchase price',
                        'purchase_price': price_float,
                        'salvage_value': salvage_float,
                        'salvage_percentage': (salvage_float/price_float)*100
                    })
                    
            except (ValueError, TypeError):
                pass
        
        # Check for very high asset values
        if purchase_price:
            try:
                price_float = float(purchase_price)
                
                if price_float > 1000000:  # Over 1M
                    anomalies.append({
                        'type': 'high_value_asset',
                        'severity': 'medium',
                        'description': f'High value asset: ${price_float:,.2f}',
                        'purchase_price': price_float,
                        'threshold': 1000000
                    })
                    
            except (ValueError, TypeError):
                pass
        
        # Check warranty terms
        warranty_period = field_values.get('warranty_terms.warranty_period')
        if not warranty_period:
            anomalies.append({
                'type': 'missing_warranty_terms',
                'severity': 'low',
                'description': 'Asset missing warranty terms',
                'field': 'warranty_terms.warranty_period',
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
    
    def _detect_advanced_asset_anomalies(self, document: Dict[str, Any], 
                                        fields: List[ExtractionResult]) -> List[Dict[str, Any]]:
        """Detect advanced asset anomalies"""
        anomalies = []
        
        # Check for asset type consistency
        asset_type = document.get('asset_details', {}).get('asset_type', '').lower()
        description = document.get('asset_details', {}).get('description', '').lower()
        
        if asset_type and description:
            # Check if description matches asset type
            type_keywords = {
                'computer': ['computer', 'laptop', 'server', 'workstation'],
                'vehicle': ['car', 'truck', 'van', 'vehicle'],
                'equipment': ['equipment', 'machine', 'tool'],
                'furniture': ['desk', 'chair', 'table', 'furniture']
            }
            
            expected_keywords = type_keywords.get(asset_type, [])
            if expected_keywords and not any(keyword in description for keyword in expected_keywords):
                anomalies.append({
                    'type': 'asset_type_description_mismatch',
                    'severity': 'low',
                    'description': f'Asset type "{asset_type}" may not match description "{description[:50]}..."',
                    'asset_type': asset_type,
                    'description_snippet': description[:100],
                    'expected_keywords': expected_keywords
                })
        
        # Check delivery vs acquisition date consistency
        acquisition_date = document.get('acquisition_date')
        delivery_date = document.get('delivery_terms', {}).get('delivery_date')
        
        if acquisition_date and delivery_date:
            try:
                acq_valid, acq_date, _ = self.document_processor.validate_date(acquisition_date)
                del_valid, del_date, _ = self.document_processor.validate_date(delivery_date)
                
                if acq_valid and del_valid:
                    if del_date < acq_date:
                        anomalies.append({
                            'type': 'delivery_before_acquisition',
                            'severity': 'medium',
                            'description': 'Delivery date is before acquisition date',
                            'acquisition_date': acq_date.isoformat(),
                            'delivery_date': del_date.isoformat()
                        })
                    elif (del_date - acq_date).days > 90:  # More than 3 months
                        anomalies.append({
                            'type': 'long_delivery_delay',
                            'severity': 'low',
                            'description': f'Long delay between acquisition and delivery: {(del_date - acq_date).days} days',
                            'acquisition_date': acq_date.isoformat(),
                            'delivery_date': del_date.isoformat(),
                            'delay_days': (del_date - acq_date).days
                        })
                        
            except Exception:
                pass
        
        return anomalies
    
    def _analyze_depreciation(self, extracted_fields: List[ExtractionResult], 
                             document: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze depreciation calculations and schedules"""
        analysis = {
            'is_valid': True,
            'method': None,
            'annual_depreciation': 0,
            'depreciation_rate': 0,
            'years_to_fully_depreciate': 0,
            'issues': []
        }
        
        field_values = {field.field_name: field.value for field in extracted_fields}
        
        # Get depreciation parameters
        purchase_price = field_values.get('financial_details.purchase_price')
        salvage_value = field_values.get('financial_details.salvage_value', 0)
        useful_life = field_values.get('financial_details.useful_life_years')
        method = field_values.get('financial_details.depreciation_method', '').lower()
        
        if not purchase_price or not useful_life:
            analysis['is_valid'] = False
            analysis['issues'].append('Missing required depreciation parameters')
            return analysis
        
        try:
            price_float = float(purchase_price)
            salvage_float = float(salvage_value) if salvage_value else 0
            life_int = int(useful_life)
            
            analysis['method'] = method
            
            # Calculate based on method
            if 'straight' in method or 'linear' in method:
                # Straight-line depreciation
                depreciable_amount = price_float - salvage_float
                annual_depreciation = depreciable_amount / life_int
                analysis['annual_depreciation'] = annual_depreciation
                analysis['depreciation_rate'] = (annual_depreciation / price_float) * 100
                analysis['years_to_fully_depreciate'] = life_int
                
            elif 'declining' in method or 'double' in method:
                # Declining balance (assume double declining)
                rate = (2 / life_int) * 100
                analysis['depreciation_rate'] = rate
                analysis['annual_depreciation'] = price_float * (rate / 100)  # First year
                analysis['years_to_fully_depreciate'] = life_int
                
            elif 'units' in method or 'production' in method:
                # Units of production - can't calculate without production data
                analysis['issues'].append('Units of production method requires production data for calculation')
                
            else:
                analysis['issues'].append(f'Unknown depreciation method: {method}')
            
            # Validate calculations
            if analysis['annual_depreciation'] > price_float:
                analysis['issues'].append('Annual depreciation exceeds asset cost')
                analysis['is_valid'] = False
            
            if analysis['depreciation_rate'] > 100:
                analysis['issues'].append('Depreciation rate exceeds 100%')
                analysis['is_valid'] = False
                
        except (ValueError, TypeError) as e:
            analysis['is_valid'] = False
            analysis['issues'].append(f'Calculation error: {str(e)}')
        
        return analysis
    
    def _check_lease_correlations(self, extracted_fields: List[ExtractionResult], 
                                 document: Dict[str, Any]) -> Dict[str, Any]:
        """Check for correlations with lease agreements"""
        correlations = {
            'found_correlations': [],
            'potential_lease_to_own': False,
            'correlation_details': []
        }
        
        # Get asset ID
        asset_id = None
        for field in extracted_fields:
            if field.field_name == 'asset_details.asset_id' and field.value:
                asset_id = field.value
                break
        
        if not asset_id:
            return correlations
        
        # Check against processed leases
        if asset_id in self.processed_leases:
            lease_data = self.processed_leases[asset_id]
            correlations['found_correlations'].append(asset_id)
            correlations['potential_lease_to_own'] = True
            
            # Extract details for comparison
            asset_price = document.get('financial_details', {}).get('purchase_price', 0)
            
            # Try to extract lease details from stored data
            lease_monthly = 0
            lease_total = 0
            lease_fields = lease_data.get('extracted_fields', [])
            
            for field in lease_fields:
                if field.get('field_name') == 'financial_terms.monthly_payment':
                    try:
                        lease_monthly = float(field.get('value', 0))
                    except (ValueError, TypeError):
                        pass
                elif field.get('field_name') == 'financial_terms.total_lease_value':
                    try:
                        lease_total = float(field.get('value', 0))
                    except (ValueError, TypeError):
                        pass
            
            correlations['correlation_details'].append({
                'asset_id': asset_id,
                'asset_purchase_price': asset_price,
                'lease_monthly_payment': lease_monthly,
                'lease_total_value': lease_total,
                'correlation_type': 'lease_to_own'
            })
        
        return correlations
    
    def _extract_asset_id_from_response(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Extract asset ID from lease agent response"""
        extracted_fields = response_data.get('extracted_fields', [])
        for field in extracted_fields:
            if field.get('field_name') == 'leased_asset.asset_id':
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
    
    def _get_asset_summary(self, asset_id: str) -> Dict[str, Any]:
        """Get summary of processed asset"""
        return {
            'status': 'info',
            'message': f'Asset summary for {asset_id} not implemented yet'
        }
    
    def _get_depreciation_schedule(self, asset_id: str) -> Dict[str, Any]:
        """Get depreciation schedule for asset"""
        return {
            'status': 'info',
            'message': f'Depreciation schedule for asset {asset_id} not implemented yet'
        }
    
    def _get_lease_correlation(self, asset_id: str) -> Dict[str, Any]:
        """Get lease correlation information"""
        if asset_id in self.processed_leases:
            return {
                'status': 'found',
                'asset_id': asset_id,
                'correlation_type': 'lease_to_own',
                'lease_data': self.processed_leases[asset_id]
            }
        else:
            return {
                'status': 'not_found',
                'asset_id': asset_id,
                'message': 'No correlation found with lease agreements'
            }
    
    def _get_asset_statistics(self) -> Dict[str, Any]:
        """Get asset processing statistics"""
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
                'lease_correlations_found': len(self.processed_leases),
                'agent_id': self.agent_id
            }
        }