"""
Quality Review Agent - Final validation and reporting
"""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

from .base_agent import BaseAgent, AgentStatus
from utils.message_queue import Message, MessageType, MessagePriority
from utils.document_processor import DocumentProcessor
from config.settings import DATA_DIR

class QualityReviewAgent(BaseAgent):
    """Agent responsible for final validation, reporting, and quality assessment"""
    
    def __init__(self, agent_id: str, message_queue):
        super().__init__(agent_id, message_queue)
        self.document_processor = DocumentProcessor()
        
        # Agent-specific configuration
        self.config.update({
            'confidence_threshold': 0.90,
            'max_processing_time': 120,
            'generate_detailed_reports': True,
            'include_recommendations': True,
            'anomaly_severity_weights': {
                'critical': 10,
                'high': 5,
                'medium': 2,
                'low': 1,
                'info': 0
            },
            'quality_score_thresholds': {
                'excellent': 95,
                'good': 85,
                'acceptable': 70,
                'poor': 50
            }
        })
        
        # Storage for processing results from other agents
        self.processing_results = {}
        self.cross_reference_data = {}
        
        self.logger.info(f"Quality Review Agent {agent_id} initialized")
    
    def process_message(self, message: Message) -> Dict[str, Any]:
        """Process incoming messages"""
        try:
            if message.msg_type == MessageType.TASK_ASSIGNMENT:
                return self._handle_quality_review_task(message)
            elif message.msg_type == MessageType.DATA_RESPONSE:
                return self._handle_agent_results(message)
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
    
    def _handle_quality_review_task(self, message: Message) -> Dict[str, Any]:
        """Handle quality review tasks"""
        task_data = message.content
        task_type = task_data.get('task_type')
        
        if task_type == 'generate_quality_report':
            return self.generate_quality_report(task_data.get('document_batch', []))
        elif task_type == 'cross_validate_documents':
            return self.cross_validate_documents(task_data.get('document_results', []))
        elif task_type == 'anomaly_analysis':
            return self.analyze_anomalies(task_data.get('anomaly_data', []))
        else:
            return {
                'status': 'error',
                'message': f'Unknown quality review task type: {task_type}'
            }
    
    def _handle_agent_results(self, message: Message) -> Dict[str, Any]:
        """Handle processing results from other agents"""
        result_data = message.content
        document_id = result_data.get('document_id', 'unknown')
        agent_id = result_data.get('agent_id', 'unknown')
        
        # Store results for quality analysis
        if document_id not in self.processing_results:
            self.processing_results[document_id] = {}
        
        self.processing_results[document_id][agent_id] = result_data
        
        return {'status': 'acknowledged', 'document_id': document_id}
    
    def _handle_data_request(self, message: Message) -> Dict[str, Any]:
        """Handle data requests"""
        request_data = message.content
        request_type = request_data.get('request_type')
        
        if request_type == 'quality_summary':
            return self._get_quality_summary()
        elif request_type == 'anomaly_report':
            return self._get_anomaly_report()
        elif request_type == 'processing_statistics':
            return self._get_processing_statistics()
        else:
            return {
                'status': 'error',
                'message': f'Unknown request type: {request_type}'
            }
    
    def generate_quality_report(self, document_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        self.status = AgentStatus.PROCESSING
        start_time = datetime.now()
        
        try:
            report = {
                'report_id': f"QR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'generation_time': datetime.now().isoformat(),
                'summary': {},
                'document_analysis': [],
                'cross_validation_results': {},
                'anomaly_analysis': {},
                'recommendations': [],
                'quality_scores': {},
                'agent_performance': {}
            }
            
            # Analyze each document
            total_documents = len(document_results)
            successful_documents = 0
            warning_documents = 0
            error_documents = 0
            
            all_anomalies = []
            confidence_scores = []
            processing_times = []
            
            for doc_result in document_results:
                doc_analysis = self._analyze_document_result(doc_result)
                report['document_analysis'].append(doc_analysis)
                
                # Collect statistics
                status = doc_result.get('status', 'unknown')
                if status == 'success':
                    successful_documents += 1
                elif status == 'warning':
                    warning_documents += 1
                elif status == 'error':
                    error_documents += 1
                
                # Collect anomalies
                anomalies = doc_result.get('anomalies', [])
                all_anomalies.extend(anomalies)
                
                # Collect confidence scores
                confidence = doc_result.get('overall_confidence', 0)
                if confidence > 0:
                    confidence_scores.append(confidence)
                
                # Collect processing times
                proc_time = doc_result.get('processing_time', 0)
                if proc_time > 0:
                    processing_times.append(proc_time)
            
            # Generate summary
            report['summary'] = {
                'total_documents': total_documents,
                'successful': successful_documents,
                'warnings': warning_documents,
                'errors': error_documents,
                'success_rate': (successful_documents / total_documents * 100) if total_documents > 0 else 0,
                'total_anomalies': len(all_anomalies),
                'average_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                'average_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0
            }
            
            # Analyze anomalies
            report['anomaly_analysis'] = self._analyze_anomalies(all_anomalies)
            
            # Cross-validation analysis
            report['cross_validation_results'] = self._perform_cross_validation(document_results)
            
            # Generate quality scores
            report['quality_scores'] = self._calculate_quality_scores(document_results)
            
            # Analyze agent performance
            report['agent_performance'] = self._analyze_agent_performance(document_results)
            
            # Generate recommendations
            report['recommendations'] = self._generate_recommendations(report)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Update metrics
            self.metrics.tasks_completed += 1
            self.metrics.total_processing_time += processing_time
            
            self.status = AgentStatus.IDLE
            
            return {
                'status': 'success',
                'quality_report': report,
                'processing_time': processing_time,
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Quality report generation failed: {e}")
            self.metrics.tasks_failed += 1
            
            return {
                'status': 'error',
                'message': str(e),
                'agent_id': self.agent_id
            }
    
    def _analyze_document_result(self, doc_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual document processing result"""
        analysis = {
            'document_id': doc_result.get('document_id', 'unknown'),
            'document_type': doc_result.get('document_type', 'unknown'),
            'status': doc_result.get('status', 'unknown'),
            'overall_confidence': doc_result.get('overall_confidence', 0),
            'processing_time': doc_result.get('processing_time', 0),
            'field_analysis': {},
            'anomaly_summary': {},
            'quality_score': 0,
            'issues': [],
            'strengths': []
        }
        
        # Analyze extracted fields
        extracted_fields = doc_result.get('extracted_fields', [])
        if extracted_fields:
            field_confidences = []
            low_confidence_fields = []
            
            for field in extracted_fields:
                if isinstance(field, dict):
                    confidence = field.get('confidence', 0)
                    field_confidences.append(confidence)
                    
                    if confidence < 0.8:
                        low_confidence_fields.append({
                            'field': field.get('field_name', 'unknown'),
                            'confidence': confidence,
                            'value': field.get('value')
                        })
            
            analysis['field_analysis'] = {
                'total_fields': len(extracted_fields),
                'average_confidence': sum(field_confidences) / len(field_confidences) if field_confidences else 0,
                'low_confidence_fields': low_confidence_fields
            }
        
        # Analyze anomalies
        anomalies = doc_result.get('anomalies', [])
        if anomalies:
            anomaly_counts = defaultdict(int)
            for anomaly in anomalies:
                severity = anomaly.get('severity', 'unknown')
                anomaly_counts[severity] += 1
            
            analysis['anomaly_summary'] = dict(anomaly_counts)
        
        # Calculate quality score
        analysis['quality_score'] = self._calculate_document_quality_score(doc_result)
        
        # Identify issues and strengths
        analysis['issues'] = self._identify_document_issues(doc_result)
        analysis['strengths'] = self._identify_document_strengths(doc_result)
        
        return analysis
    
    def _analyze_anomalies(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze anomalies across all documents"""
        analysis = {
            'total_anomalies': len(anomalies),
            'by_severity': defaultdict(int),
            'by_type': defaultdict(int),
            'by_document_type': defaultdict(int),
            'critical_issues': [],
            'patterns': [],
            'severity_score': 0
        }
        
        severity_weights = self.config.get('anomaly_severity_weights', {})
        total_weight = 0
        
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'unknown')
            anomaly_type = anomaly.get('type', 'unknown')
            doc_type = anomaly.get('document_type', 'unknown')
            
            analysis['by_severity'][severity] += 1
            analysis['by_type'][anomaly_type] += 1
            analysis['by_document_type'][doc_type] += 1
            
            # Calculate severity score
            weight = severity_weights.get(severity, 1)
            total_weight += weight
            
            # Collect critical issues
            if severity in ['critical', 'high']:
                analysis['critical_issues'].append({
                    'type': anomaly_type,
                    'severity': severity,
                    'description': anomaly.get('description', ''),
                    'document_type': doc_type
                })
        
        analysis['severity_score'] = total_weight
        
        # Identify patterns
        analysis['patterns'] = self._identify_anomaly_patterns(anomalies)
        
        return analysis
    
    def _perform_cross_validation(self, document_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform cross-validation between documents"""
        cross_validation = {
            'po_correlations': {},
            'asset_correlations': {},
            'vendor_buyer_consistency': {},
            'amount_correlations': {},
            'date_consistency': {},
            'issues_found': []
        }
        
        # Group documents by type
        docs_by_type = defaultdict(list)
        for doc in document_results:
            doc_type = doc.get('document_type', 'unknown')
            docs_by_type[doc_type].append(doc)
        
        # Check PO number correlations
        cross_validation['po_correlations'] = self._check_po_correlations(docs_by_type)
        
        # Check asset correlations
        cross_validation['asset_correlations'] = self._check_asset_correlations(docs_by_type)
        
        # Check vendor/buyer consistency
        cross_validation['vendor_buyer_consistency'] = self._check_entity_consistency(docs_by_type)
        
        # Check amount correlations
        cross_validation['amount_correlations'] = self._check_amount_correlations(docs_by_type)
        
        return cross_validation
    
    def _check_po_correlations(self, docs_by_type: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Check PO number correlations between invoices and contracts"""
        correlations = {
            'matched_pos': [],
            'unmatched_invoices': [],
            'unmatched_contracts': [],
            'correlation_rate': 0
        }
        
        # Extract PO numbers from invoices and contracts
        invoice_pos = {}
        contract_pos = {}
        
        for invoice in docs_by_type.get('invoice', []):
            po_number = self._extract_po_number(invoice)
            if po_number:
                invoice_pos[po_number] = invoice.get('document_id', 'unknown')
        
        for contract in docs_by_type.get('contract', []):
            po_number = self._extract_po_number(contract)
            if po_number:
                contract_pos[po_number] = contract.get('document_id', 'unknown')
        
        # Find matches
        matched_pos = set(invoice_pos.keys()).intersection(set(contract_pos.keys()))
        correlations['matched_pos'] = list(matched_pos)
        
        # Find unmatched
        correlations['unmatched_invoices'] = [
            {'po_number': po, 'invoice_id': inv_id} 
            for po, inv_id in invoice_pos.items() if po not in matched_pos
        ]
        
        correlations['unmatched_contracts'] = [
            {'po_number': po, 'contract_id': cont_id} 
            for po, cont_id in contract_pos.items() if po not in matched_pos
        ]
        
        # Calculate correlation rate
        total_pos = len(set(invoice_pos.keys()).union(set(contract_pos.keys())))
        correlations['correlation_rate'] = (len(matched_pos) / total_pos * 100) if total_pos > 0 else 0
        
        return correlations
    
    def _check_asset_correlations(self, docs_by_type: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Check asset correlations between leases and fixed assets"""
        correlations = {
            'matched_assets': [],
            'lease_only_assets': [],
            'asset_only_assets': [],
            'correlation_rate': 0
        }
        
        # Extract asset IDs
        lease_assets = {}
        fixed_assets = {}
        
        for lease in docs_by_type.get('lease', []):
            asset_id = self._extract_asset_id(lease)
            if asset_id:
                lease_assets[asset_id] = lease.get('document_id', 'unknown')
        
        for asset in docs_by_type.get('fixed_asset', []):
            asset_id = self._extract_asset_id(asset)
            if asset_id:
                fixed_assets[asset_id] = asset.get('document_id', 'unknown')
        
        # Find matches (potential lease-to-own scenarios)
        matched_assets = set(lease_assets.keys()).intersection(set(fixed_assets.keys()))
        correlations['matched_assets'] = list(matched_assets)
        
        # Find unmatched
        correlations['lease_only_assets'] = [
            {'asset_id': asset_id, 'lease_id': lease_id} 
            for asset_id, lease_id in lease_assets.items() if asset_id not in matched_assets
        ]
        
        correlations['asset_only_assets'] = [
            {'asset_id': asset_id, 'asset_agreement_id': asset_id} 
            for asset_id, asset_agreement_id in fixed_assets.items() if asset_id not in matched_assets
        ]
        
        # Calculate correlation rate
        total_assets = len(set(lease_assets.keys()).union(set(fixed_assets.keys())))
        correlations['correlation_rate'] = (len(matched_assets) / total_assets * 100) if total_assets > 0 else 0
        
        return correlations
    
    def _check_entity_consistency(self, docs_by_type: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Check vendor/buyer name consistency across documents"""
        consistency = {
            'vendor_variations': defaultdict(list),
            'buyer_variations': defaultdict(list),
            'potential_duplicates': []
        }
        
        # Collect all vendor and buyer names
        all_vendors = []
        all_buyers = []
        
        for doc_type, docs in docs_by_type.items():
            for doc in docs:
                vendor_name = self._extract_vendor_name(doc)
                buyer_name = self._extract_buyer_name(doc)
                
                if vendor_name:
                    all_vendors.append((vendor_name, doc.get('document_id', 'unknown')))
                if buyer_name:
                    all_buyers.append((buyer_name, doc.get('document_id', 'unknown')))
        
        # Check for variations (simple similarity check)
        consistency['vendor_variations'] = self._find_name_variations(all_vendors)
        consistency['buyer_variations'] = self._find_name_variations(all_buyers)
        
        return consistency
    
    def _check_amount_correlations(self, docs_by_type: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Check amount correlations between related documents"""
        correlations = {
            'invoice_contract_variances': [],
            'lease_asset_comparisons': [],
            'unusual_amounts': []
        }
        
        # Compare invoice amounts with contract amounts for same PO
        invoice_amounts = {}
        contract_amounts = {}
        
        for invoice in docs_by_type.get('invoice', []):
            po_number = self._extract_po_number(invoice)
            amount = self._extract_amount(invoice)
            if po_number and amount:
                invoice_amounts[po_number] = amount
        
        for contract in docs_by_type.get('contract', []):
            po_number = self._extract_po_number(contract)
            amount = self._extract_amount(contract)
            if po_number and amount:
                contract_amounts[po_number] = amount
        
        # Find variances
        for po_number in set(invoice_amounts.keys()).intersection(set(contract_amounts.keys())):
            invoice_amt = invoice_amounts[po_number]
            contract_amt = contract_amounts[po_number]
            
            if contract_amt > 0:
                variance = abs(invoice_amt - contract_amt) / contract_amt
                if variance > 0.05:  # 5% variance threshold
                    correlations['invoice_contract_variances'].append({
                        'po_number': po_number,
                        'invoice_amount': invoice_amt,
                        'contract_amount': contract_amt,
                        'variance_percentage': variance * 100
                    })
        
        return correlations
    
    def _calculate_quality_scores(self, document_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality scores for the batch"""
        scores = {
            'overall_score': 0,
            'by_document_type': {},
            'by_agent': {},
            'score_distribution': defaultdict(int)
        }
        
        all_scores = []
        type_scores = defaultdict(list)
        agent_scores = defaultdict(list)
        
        for doc_result in document_results:
            doc_score = self._calculate_document_quality_score(doc_result)
            all_scores.append(doc_score)
            
            doc_type = doc_result.get('document_type', 'unknown')
            type_scores[doc_type].append(doc_score)
            
            agent_id = doc_result.get('agent_id', 'unknown')
            agent_scores[agent_id].append(doc_score)
            
            # Score distribution
            if doc_score >= 95:
                scores['score_distribution']['excellent'] += 1
            elif doc_score >= 85:
                scores['score_distribution']['good'] += 1
            elif doc_score >= 70:
                scores['score_distribution']['acceptable'] += 1
            else:
                scores['score_distribution']['poor'] += 1
        
        # Calculate averages
        scores['overall_score'] = sum(all_scores) / len(all_scores) if all_scores else 0
        
        for doc_type, type_score_list in type_scores.items():
            scores['by_document_type'][doc_type] = sum(type_score_list) / len(type_score_list)
        
        for agent_id, agent_score_list in agent_scores.items():
            scores['by_agent'][agent_id] = sum(agent_score_list) / len(agent_score_list)
        
        return scores
    
    def _calculate_document_quality_score(self, doc_result: Dict[str, Any]) -> float:
        """Calculate quality score for individual document"""
        score = 100.0  # Start with perfect score
        
        # Deduct for status
        status = doc_result.get('status', 'unknown')
        if status == 'error':
            score -= 50
        elif status == 'warning':
            score -= 20
        
        # Deduct for low confidence
        confidence = doc_result.get('overall_confidence', 1.0)
        if confidence < 0.8:
            score -= (0.8 - confidence) * 50
        
        # Deduct for anomalies
        anomalies = doc_result.get('anomalies', [])
        severity_weights = self.config.get('anomaly_severity_weights', {})
        
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'low')
            weight = severity_weights.get(severity, 1)
            score -= weight
        
        # Ensure score doesn't go below 0
        return max(0, score)
    
    def _analyze_agent_performance(self, document_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance of individual agents"""
        performance = {}
        
        agent_stats = defaultdict(lambda: {
            'total_processed': 0,
            'successful': 0,
            'warnings': 0,
            'errors': 0,
            'average_confidence': 0,
            'average_processing_time': 0,
            'anomalies_detected': 0
        })
        
        for doc_result in document_results:
            agent_id = doc_result.get('agent_id', 'unknown')
            status = doc_result.get('status', 'unknown')
            confidence = doc_result.get('overall_confidence', 0)
            processing_time = doc_result.get('processing_time', 0)
            anomalies = len(doc_result.get('anomalies', []))
            
            stats = agent_stats[agent_id]
            stats['total_processed'] += 1
            
            if status == 'success':
                stats['successful'] += 1
            elif status == 'warning':
                stats['warnings'] += 1
            elif status == 'error':
                stats['errors'] += 1
            
            stats['average_confidence'] += confidence
            stats['average_processing_time'] += processing_time
            stats['anomalies_detected'] += anomalies
        
        # Calculate averages
        for agent_id, stats in agent_stats.items():
            if stats['total_processed'] > 0:
                stats['average_confidence'] /= stats['total_processed']
                stats['average_processing_time'] /= stats['total_processed']
                stats['success_rate'] = (stats['successful'] / stats['total_processed']) * 100
            
            performance[agent_id] = dict(stats)
        
        return performance
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on quality analysis"""
        recommendations = []
        
        # Check overall success rate
        success_rate = report['summary'].get('success_rate', 0)
        if success_rate < 90:
            recommendations.append({
                'type': 'process_improvement',
                'priority': 'high',
                'title': 'Improve Processing Success Rate',
                'description': f'Current success rate is {success_rate:.1f}%. Target should be >90%.',
                'suggested_actions': [
                    'Review failed document processing patterns',
                    'Improve field extraction algorithms',
                    'Enhance data validation rules'
                ]
            })
        
        # Check confidence scores
        avg_confidence = report['summary'].get('average_confidence', 0)
        if avg_confidence < 0.85:
            recommendations.append({
                'type': 'confidence_improvement',
                'priority': 'medium',
                'title': 'Improve Extraction Confidence',
                'description': f'Average confidence is {avg_confidence:.2f}. Target should be >0.85.',
                'suggested_actions': [
                    'Review low-confidence field extractions',
                    'Improve pattern matching algorithms',
                    'Add more validation rules'
                ]
            })
        
        # Check anomaly patterns
        anomaly_analysis = report.get('anomaly_analysis', {})
        critical_issues = anomaly_analysis.get('critical_issues', [])
        
        if len(critical_issues) > 0:
            recommendations.append({
                'type': 'anomaly_resolution',
                'priority': 'critical',
                'title': 'Address Critical Anomalies',
                'description': f'Found {len(critical_issues)} critical issues requiring immediate attention.',
                'suggested_actions': [
                    'Review and resolve critical anomalies',
                    'Implement additional validation checks',
                    'Update business rules if needed'
                ]
            })
        
        # Check cross-validation results
        cross_validation = report.get('cross_validation_results', {})
        po_correlations = cross_validation.get('po_correlations', {})
        correlation_rate = po_correlations.get('correlation_rate', 0)
        
        if correlation_rate < 80:
            recommendations.append({
                'type': 'data_consistency',
                'priority': 'medium',
                'title': 'Improve PO Number Correlations',
                'description': f'PO correlation rate is {correlation_rate:.1f}%. Target should be >80%.',
                'suggested_actions': [
                    'Review unmatched PO numbers',
                    'Improve PO number extraction accuracy',
                    'Validate master data completeness'
                ]
            })
        
        return recommendations
    
    def _identify_anomaly_patterns(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify patterns in anomalies"""
        patterns = []
        
        # Group by type and look for patterns
        type_counts = defaultdict(int)
        doc_type_anomalies = defaultdict(list)
        
        for anomaly in anomalies:
            anomaly_type = anomaly.get('type', 'unknown')
            doc_type = anomaly.get('document_type', 'unknown')
            
            type_counts[anomaly_type] += 1
            doc_type_anomalies[doc_type].append(anomaly_type)
        
        # Identify frequent anomaly types
        for anomaly_type, count in type_counts.items():
            if count >= 3:  # Appears in 3+ documents
                patterns.append({
                    'pattern_type': 'frequent_anomaly',
                    'anomaly_type': anomaly_type,
                    'frequency': count,
                    'description': f'Anomaly type "{anomaly_type}" appears frequently ({count} times)'
                })
        
        return patterns
    
    def _identify_document_issues(self, doc_result: Dict[str, Any]) -> List[str]:
        """Identify issues with document processing"""
        issues = []
        
        status = doc_result.get('status', 'unknown')
        if status == 'error':
            issues.append('Document processing failed')
        elif status == 'warning':
            issues.append('Document processing completed with warnings')
        
        confidence = doc_result.get('overall_confidence', 1.0)
        if confidence < 0.7:
            issues.append(f'Low overall confidence: {confidence:.2f}')
        
        anomalies = doc_result.get('anomalies', [])
        critical_anomalies = [a for a in anomalies if a.get('severity') == 'critical']
        if critical_anomalies:
            issues.append(f'{len(critical_anomalies)} critical anomalies detected')
        
        return issues
    
    def _identify_document_strengths(self, doc_result: Dict[str, Any]) -> List[str]:
        """Identify strengths in document processing"""
        strengths = []
        
        status = doc_result.get('status', 'unknown')
        if status == 'success':
            strengths.append('Document processed successfully')
        
        confidence = doc_result.get('overall_confidence', 0)
        if confidence > 0.9:
            strengths.append(f'High confidence extraction: {confidence:.2f}')
        
        processing_time = doc_result.get('processing_time', 0)
        if processing_time < 30:  # Less than 30 seconds
            strengths.append('Fast processing time')
        
        anomalies = doc_result.get('anomalies', [])
        if not anomalies:
            strengths.append('No anomalies detected')
        
        return strengths
    
    # Helper methods for data extraction
    def _extract_po_number(self, doc_result: Dict[str, Any]) -> Optional[str]:
        """Extract PO number from document result"""
        extracted_fields = doc_result.get('extracted_fields', [])
        for field in extracted_fields:
            if isinstance(field, dict):
                field_name = field.get('field_name', '')
                if 'po' in field_name.lower() or 'purchase_order' in field_name.lower():
                    return field.get('value')
        return None
    
    def _extract_asset_id(self, doc_result: Dict[str, Any]) -> Optional[str]:
        """Extract asset ID from document result"""
        extracted_fields = doc_result.get('extracted_fields', [])
        for field in extracted_fields:
            if isinstance(field, dict):
                field_name = field.get('field_name', '')
                if 'asset_id' in field_name.lower():
                    return field.get('value')
        return None
    
    def _extract_vendor_name(self, doc_result: Dict[str, Any]) -> Optional[str]:
        """Extract vendor name from document result"""
        extracted_fields = doc_result.get('extracted_fields', [])
        for field in extracted_fields:
            if isinstance(field, dict):
                field_name = field.get('field_name', '')
                if 'vendor' in field_name.lower() and 'name' in field_name.lower():
                    return field.get('value')
        return None
    
    def _extract_buyer_name(self, doc_result: Dict[str, Any]) -> Optional[str]:
        """Extract buyer name from document result"""
        extracted_fields = doc_result.get('extracted_fields', [])
        for field in extracted_fields:
            if isinstance(field, dict):
                field_name = field.get('field_name', '')
                if 'buyer' in field_name.lower() and 'name' in field_name.lower():
                    return field.get('value')
        return None
    
    def _extract_amount(self, doc_result: Dict[str, Any]) -> Optional[float]:
        """Extract amount from document result"""
        extracted_fields = doc_result.get('extracted_fields', [])
        for field in extracted_fields:
            if isinstance(field, dict):
                field_name = field.get('field_name', '')
                if 'amount' in field_name.lower() or 'value' in field_name.lower():
                    try:
                        return float(field.get('value', 0))
                    except (ValueError, TypeError):
                        pass
        return None
    
    def _find_name_variations(self, names: List[Tuple[str, str]]) -> Dict[str, List[str]]:
        """Find potential name variations"""
        variations = defaultdict(list)
        
        # Simple similarity check (could be enhanced with fuzzy matching)
        for i, (name1, doc1) in enumerate(names):
            for j, (name2, doc2) in enumerate(names[i+1:], i+1):
                if name1.lower() != name2.lower():
                    # Check for partial matches
                    if (name1.lower() in name2.lower() or name2.lower() in name1.lower()) and \
                       abs(len(name1) - len(name2)) <= 5:
                        variations[name1].append(name2)
        
        return dict(variations)
    
    def _get_quality_summary(self) -> Dict[str, Any]:
        """Get quality summary"""
        return {
            'status': 'success',
            'summary': 'Quality summary not implemented yet'
        }
    
    def _get_anomaly_report(self) -> Dict[str, Any]:
        """Get anomaly report"""
        return {
            'status': 'success',
            'report': 'Anomaly report not implemented yet'
        }
    
    def _get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'status': 'success',
            'statistics': {
                'total_processed': self.metrics.tasks_completed + self.metrics.tasks_failed,
                'successful': self.metrics.tasks_completed,
                'failed': self.metrics.tasks_failed,
                'average_processing_time': (
                    self.metrics.total_processing_time / max(1, self.metrics.tasks_completed + self.metrics.tasks_failed)
                ),
                'agent_id': self.agent_id
            }
        }