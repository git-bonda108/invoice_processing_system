"""
Enhanced Manager Agent - Critical validator and devil's advocate
"""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics

from .base_agent import BaseAgent, AgentStatus
from utils.message_queue import Message, MessageType, MessagePriority
from utils.ai_client import ai_client
from config.settings import DATA_DIR

@dataclass
class CriticalAnalysis:
    """Critical analysis of processing results"""
    analysis_id: str
    document_id: str
    agent_id: str
    processing_result: Dict[str, Any]
    critical_issues: List[Dict[str, Any]]
    confidence_assessment: float
    quality_score: float
    recommendations: List[str]
    approval_status: str  # approved, rejected, needs_review
    manager_comments: List[str]
    timestamp: datetime

@dataclass
class QualityChallenge:
    """Quality challenge raised by manager"""
    challenge_id: str
    target_agent: str
    issue_type: str
    description: str
    evidence: Dict[str, Any]
    severity: str  # critical, high, medium, low
    response_required: bool
    deadline: datetime
    status: str  # open, responded, resolved, escalated

class EnhancedManagerAgent(BaseAgent):
    """Enhanced Manager Agent with critical analysis and devil's advocate capabilities"""
    
    def __init__(self, agent_id: str, message_queue):
        super().__init__(agent_id, message_queue)
        
        # Enhanced manager configuration
        self.config.update({
            'critical_analysis_enabled': True,
            'quality_threshold': 0.85,
            'confidence_threshold': 0.90,
            'anomaly_tolerance': 3,
            'challenge_frequency': 0.2,  # Challenge 20% of results
            'devil_advocate_mode': True,
            'strict_validation': True
        })
        
        # Critical analysis tracking
        self.critical_analyses: Dict[str, CriticalAnalysis] = {}
        self.quality_challenges: Dict[str, QualityChallenge] = {}
        self.agent_performance_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Quality standards and expectations
        self.quality_standards = {
            'invoice': {
                'required_fields': ['invoice_number', 'total_amount', 'vendor', 'date'],
                'confidence_minimum': 0.90,
                'anomaly_maximum': 2,
                'processing_time_maximum': 60
            },
            'contract': {
                'required_fields': ['contract_number', 'parties', 'terms', 'value'],
                'confidence_minimum': 0.85,
                'anomaly_maximum': 3,
                'processing_time_maximum': 90
            },
            'msa': {
                'required_fields': ['msa_number', 'parties', 'service_scope', 'term'],
                'confidence_minimum': 0.80,
                'anomaly_maximum': 2,
                'processing_time_maximum': 120
            },
            'lease': {
                'required_fields': ['lease_number', 'parties', 'asset', 'terms'],
                'confidence_minimum': 0.85,
                'anomaly_maximum': 2,
                'processing_time_maximum': 75
            },
            'fixed_asset': {
                'required_fields': ['asset_id', 'description', 'value', 'depreciation'],
                'confidence_minimum': 0.88,
                'anomaly_maximum': 2,
                'processing_time_maximum': 90
            }
        }
        
        # Critical questioning templates
        self.critical_questions = {
            'confidence': [
                "Why is the confidence score only {confidence}? What factors reduced it?",
                "Can you justify this confidence level given the document quality?",
                "What additional validation could improve this confidence score?"
            ],
            'anomalies': [
                "You detected {count} anomalies. Are you sure you didn't miss any?",
                "These anomalies seem significant. How do they impact the overall result?",
                "Have you considered the business implications of these anomalies?"
            ],
            'processing_time': [
                "Processing took {time} seconds. Why was it slower than expected?",
                "Can you explain the performance bottleneck in your processing?",
                "How can we optimize this processing time for similar documents?"
            ],
            'field_extraction': [
                "You extracted {count} fields. Are you confident all critical fields were captured?",
                "What about edge cases? Did you handle unusual field formats?",
                "How do you validate the accuracy of extracted field values?"
            ]
        }
        
        # Manager personality traits
        self.manager_traits = {
            'skeptical': True,
            'detail_oriented': True,
            'quality_focused': True,
            'direct_communication': True,
            'continuous_improvement': True
        }
        
        self.logger.info(f"Enhanced Manager Agent {agent_id} initialized with critical analysis capabilities")
    
    def process_message(self, message: Message) -> Dict[str, Any]:
        """Process messages with critical analysis"""
        try:
            if message.msg_type == MessageType.DATA_RESPONSE:
                return self._handle_agent_result(message)
            elif message.msg_type == MessageType.TASK_ASSIGNMENT:
                return self._handle_management_task(message)
            elif message.msg_type == MessageType.STATUS_UPDATE:
                return self._handle_status_update(message)
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
    
    def _handle_agent_result(self, message: Message) -> Dict[str, Any]:
        """Handle and critically analyze agent results"""
        result_data = message.content
        agent_id = message.sender
        
        # Perform critical analysis
        analysis = self._perform_critical_analysis(result_data, agent_id)
        
        # Store analysis
        self.critical_analyses[analysis.analysis_id] = analysis
        
        # Update agent performance history
        self._update_agent_performance(agent_id, result_data, analysis)
        
        # Generate manager response
        response = self._generate_manager_response(analysis)
        
        # Decide if challenge is needed
        if self._should_challenge_result(analysis):
            challenge = self._create_quality_challenge(analysis)
            response['quality_challenge'] = asdict(challenge)
        
        return response
    
    def _perform_critical_analysis(self, result_data: Dict[str, Any], agent_id: str) -> CriticalAnalysis:
        """Perform comprehensive critical analysis of agent results"""
        analysis_id = f"ANALYSIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{agent_id}"
        document_id = result_data.get('document_id', 'unknown')
        document_type = result_data.get('document_type', 'unknown')
        
        # Get quality standards for document type
        standards = self.quality_standards.get(document_type, {})
        
        # Analyze critical issues
        critical_issues = []
        
        # 1. Confidence Analysis
        confidence = result_data.get('overall_confidence', 0.0)
        min_confidence = standards.get('confidence_minimum', 0.85)
        
        if confidence < min_confidence:
            critical_issues.append({
                'type': 'low_confidence',
                'severity': 'high',
                'description': f"Confidence {confidence:.2f} below minimum {min_confidence:.2f}",
                'impact': 'Result reliability questionable'
            })
        
        # 2. Anomaly Analysis
        anomalies = result_data.get('anomalies', [])
        max_anomalies = standards.get('anomaly_maximum', 3)
        
        if len(anomalies) > max_anomalies:
            critical_issues.append({
                'type': 'excessive_anomalies',
                'severity': 'medium',
                'description': f"Found {len(anomalies)} anomalies, expected max {max_anomalies}",
                'impact': 'Document quality concerns'
            })
        
        # 3. Field Extraction Analysis
        extracted_fields = result_data.get('extracted_fields', [])
        required_fields = standards.get('required_fields', [])
        
        missing_fields = []
        for field in required_fields:
            if not any(f.get('field_name') == field for f in extracted_fields):
                missing_fields.append(field)
        
        if missing_fields:
            critical_issues.append({
                'type': 'missing_required_fields',
                'severity': 'critical',
                'description': f"Missing required fields: {', '.join(missing_fields)}",
                'impact': 'Incomplete processing result'
            })
        
        # 4. Processing Time Analysis
        processing_time = result_data.get('processing_time', 0)
        max_time = standards.get('processing_time_maximum', 120)
        
        if processing_time > max_time:
            critical_issues.append({
                'type': 'slow_processing',
                'severity': 'low',
                'description': f"Processing took {processing_time}s, expected max {max_time}s",
                'impact': 'Performance below expectations'
            })
        
        # 5. Business Logic Validation
        business_issues = self._validate_business_logic(result_data, document_type)
        critical_issues.extend(business_issues)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(result_data, critical_issues, standards)
        
        # Generate manager comments
        manager_comments = self._generate_critical_comments(result_data, critical_issues, agent_id)
        
        # Determine approval status
        approval_status = self._determine_approval_status(quality_score, critical_issues)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(critical_issues, result_data, agent_id)
        
        return CriticalAnalysis(
            analysis_id=analysis_id,
            document_id=document_id,
            agent_id=agent_id,
            processing_result=result_data,
            critical_issues=critical_issues,
            confidence_assessment=confidence,
            quality_score=quality_score,
            recommendations=recommendations,
            approval_status=approval_status,
            manager_comments=manager_comments,
            timestamp=datetime.now()
        )
    
    def _validate_business_logic(self, result_data: Dict[str, Any], document_type: str) -> List[Dict[str, Any]]:
        """Validate business logic specific to document type"""
        issues = []
        
        if document_type == 'invoice':
            # Invoice-specific validation
            po_number = None
            for field in result_data.get('extracted_fields', []):
                if 'po' in field.get('field_name', '').lower():
                    po_number = field.get('value')
                    break
            
            if not po_number:
                issues.append({
                    'type': 'missing_po_number',
                    'severity': 'high',
                    'description': 'Invoice missing PO number - required for processing',
                    'impact': 'Cannot correlate with purchase orders'
                })
        
        elif document_type == 'msa':
            # MSA should NOT have PO numbers
            po_found = any('po' in field.get('field_name', '').lower() 
                          for field in result_data.get('extracted_fields', []))
            
            if po_found:
                issues.append({
                    'type': 'unexpected_po_number',
                    'severity': 'medium',
                    'description': 'MSA contains PO number - unusual for framework agreements',
                    'impact': 'May indicate document misclassification'
                })
        
        elif document_type == 'lease':
            # Lease should have asset correlation
            asset_correlations = result_data.get('asset_correlations', {})
            if not asset_correlations.get('found_correlations'):
                issues.append({
                    'type': 'no_asset_correlation',
                    'severity': 'medium',
                    'description': 'Lease document has no asset correlations',
                    'impact': 'Cannot track lease-to-own scenarios'
                })
        
        return issues
    
    def _calculate_quality_score(self, result_data: Dict[str, Any], critical_issues: List[Dict[str, Any]], standards: Dict[str, Any]) -> float:
        """Calculate overall quality score"""
        base_score = 100.0
        
        # Deduct points for issues
        for issue in critical_issues:
            severity = issue.get('severity', 'low')
            if severity == 'critical':
                base_score -= 25
            elif severity == 'high':
                base_score -= 15
            elif severity == 'medium':
                base_score -= 10
            elif severity == 'low':
                base_score -= 5
        
        # Bonus for high confidence
        confidence = result_data.get('overall_confidence', 0.0)
        if confidence > 0.95:
            base_score += 5
        
        # Bonus for fast processing
        processing_time = result_data.get('processing_time', 0)
        max_time = standards.get('processing_time_maximum', 120)
        if processing_time < max_time * 0.5:  # Less than 50% of max time
            base_score += 3
        
        return max(0.0, min(100.0, base_score))
    
    def _generate_critical_comments(self, result_data: Dict[str, Any], critical_issues: List[Dict[str, Any]], agent_id: str) -> List[str]:
        """Generate critical manager comments"""
        comments = []
        
        # Opening comment
        quality_score = self._calculate_quality_score(result_data, critical_issues, {})
        if quality_score < 70:
            comments.append(f"Agent {agent_id}: This result is below acceptable quality standards. Significant improvement needed.")
        elif quality_score < 85:
            comments.append(f"Agent {agent_id}: Result quality is marginal. Several issues need attention.")
        else:
            comments.append(f"Agent {agent_id}: Acceptable result, but let's discuss some observations.")
        
        # Issue-specific comments
        for issue in critical_issues:
            if issue['severity'] == 'critical':
                comments.append(f"CRITICAL ISSUE: {issue['description']} - This must be resolved immediately.")
            elif issue['severity'] == 'high':
                comments.append(f"HIGH PRIORITY: {issue['description']} - Explain your approach here.")
            elif issue['severity'] == 'medium':
                comments.append(f"CONCERN: {issue['description']} - How can we improve this?")
        
        # Performance comments
        confidence = result_data.get('overall_confidence', 0.0)
        if confidence < 0.85:
            comments.append(f"Confidence of {confidence:.2f} is concerning. What factors contributed to this low confidence?")
        
        processing_time = result_data.get('processing_time', 0)
        if processing_time > 60:
            comments.append(f"Processing time of {processing_time}s seems excessive. Can you optimize your approach?")
        
        # Challenge questions
        if len(critical_issues) == 0 and quality_score > 90:
            comments.append("Good result, but I'm being thorough: Are you absolutely certain you didn't miss any subtle anomalies?")
        
        return comments
    
    def _determine_approval_status(self, quality_score: float, critical_issues: List[Dict[str, Any]]) -> str:
        """Determine approval status based on analysis"""
        critical_count = sum(1 for issue in critical_issues if issue['severity'] == 'critical')
        high_count = sum(1 for issue in critical_issues if issue['severity'] == 'high')
        
        if critical_count > 0:
            return 'rejected'
        elif high_count > 2 or quality_score < 70:
            return 'needs_review'
        elif quality_score < 85:
            return 'conditional_approval'
        else:
            return 'approved'
    
    def _generate_recommendations(self, critical_issues: List[Dict[str, Any]], result_data: Dict[str, Any], agent_id: str) -> List[str]:
        """Generate specific recommendations for improvement"""
        recommendations = []
        
        # Issue-based recommendations
        for issue in critical_issues:
            issue_type = issue['type']
            
            if issue_type == 'low_confidence':
                recommendations.append("Implement additional validation checks to improve confidence scoring")
                recommendations.append("Review extraction algorithms for better accuracy")
            
            elif issue_type == 'excessive_anomalies':
                recommendations.append("Enhance anomaly detection to reduce false positives")
                recommendations.append("Implement anomaly severity classification")
            
            elif issue_type == 'missing_required_fields':
                recommendations.append("Strengthen field extraction patterns for required fields")
                recommendations.append("Implement fallback extraction methods")
            
            elif issue_type == 'slow_processing':
                recommendations.append("Optimize processing algorithms for better performance")
                recommendations.append("Consider parallel processing for complex documents")
        
        # General recommendations
        if len(critical_issues) > 3:
            recommendations.append("Consider comprehensive review of processing approach")
        
        if result_data.get('overall_confidence', 0) < 0.90:
            recommendations.append("Implement confidence boosting techniques")
        
        return recommendations
    
    def _should_challenge_result(self, analysis: CriticalAnalysis) -> bool:
        """Determine if result should be challenged"""
        if not self.config.get('devil_advocate_mode', True):
            return False
        
        # Always challenge if quality is poor
        if analysis.quality_score < 70:
            return True
        
        # Challenge based on frequency setting
        import random
        challenge_freq = self.config.get('challenge_frequency', 0.2)
        
        if random.random() < challenge_freq:
            return True
        
        # Challenge if there are critical issues
        critical_issues = [issue for issue in analysis.critical_issues if issue['severity'] == 'critical']
        if critical_issues:
            return True
        
        return False
    
    def _create_quality_challenge(self, analysis: CriticalAnalysis) -> QualityChallenge:
        """Create a quality challenge for the agent"""
        challenge_id = f"CHALLENGE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{analysis.agent_id}"
        
        # Determine challenge type and description
        if analysis.quality_score < 70:
            issue_type = 'quality_standards'
            description = f"Your processing result scored {analysis.quality_score:.1f}/100, which is below our quality standards. Justify this result or reprocess."
            severity = 'high'
        elif analysis.critical_issues:
            issue_type = 'critical_issues'
            critical_issue = analysis.critical_issues[0]  # Focus on first critical issue
            description = f"Critical issue detected: {critical_issue['description']}. Explain your approach and how you'll address this."
            severity = critical_issue['severity']
        else:
            issue_type = 'devil_advocate'
            description = "I'm challenging this result as part of quality assurance. Walk me through your processing logic and convince me this is the best possible result."
            severity = 'medium'
        
        challenge = QualityChallenge(
            challenge_id=challenge_id,
            target_agent=analysis.agent_id,
            issue_type=issue_type,
            description=description,
            evidence={
                'quality_score': analysis.quality_score,
                'critical_issues': analysis.critical_issues,
                'confidence': analysis.confidence_assessment
            },
            severity=severity,
            response_required=True,
            deadline=datetime.now() + timedelta(hours=1),
            status='open'
        )
        
        self.quality_challenges[challenge_id] = challenge
        return challenge
    
    def _generate_manager_response(self, analysis: CriticalAnalysis) -> Dict[str, Any]:
        """Generate manager response to agent result"""
        return {
            'status': 'analyzed',
            'analysis_id': analysis.analysis_id,
            'approval_status': analysis.approval_status,
            'quality_score': analysis.quality_score,
            'critical_issues_count': len(analysis.critical_issues),
            'manager_comments': analysis.manager_comments,
            'recommendations': analysis.recommendations,
            'requires_improvement': analysis.approval_status in ['rejected', 'needs_review'],
            'timestamp': analysis.timestamp.isoformat()
        }
    
    def _update_agent_performance(self, agent_id: str, result_data: Dict[str, Any], analysis: CriticalAnalysis):
        """Update agent performance history"""
        performance_record = {
            'timestamp': datetime.now().isoformat(),
            'quality_score': analysis.quality_score,
            'confidence': result_data.get('overall_confidence', 0.0),
            'processing_time': result_data.get('processing_time', 0),
            'critical_issues_count': len(analysis.critical_issues),
            'approval_status': analysis.approval_status
        }
        
        self.agent_performance_history[agent_id].append(performance_record)
        
        # Keep only last 100 records per agent
        if len(self.agent_performance_history[agent_id]) > 100:
            self.agent_performance_history[agent_id] = self.agent_performance_history[agent_id][-100:]
    
    def get_agent_performance_report(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive performance report for agent"""
        if agent_id not in self.agent_performance_history:
            return {
                'status': 'error',
                'message': f'No performance history for agent {agent_id}'
            }
        
        history = self.agent_performance_history[agent_id]
        
        if not history:
            return {
                'status': 'error',
                'message': f'No performance data available for agent {agent_id}'
            }
        
        # Calculate statistics
        quality_scores = [record['quality_score'] for record in history]
        confidences = [record['confidence'] for record in history]
        processing_times = [record['processing_time'] for record in history]
        
        return {
            'status': 'success',
            'agent_id': agent_id,
            'performance_summary': {
                'total_processed': len(history),
                'average_quality_score': statistics.mean(quality_scores),
                'average_confidence': statistics.mean(confidences),
                'average_processing_time': statistics.mean(processing_times),
                'approval_rate': sum(1 for r in history if r['approval_status'] == 'approved') / len(history) * 100
            },
            'recent_trend': {
                'last_10_quality': statistics.mean(quality_scores[-10:]) if len(quality_scores) >= 10 else statistics.mean(quality_scores),
                'improving': len(quality_scores) >= 2 and quality_scores[-1] > quality_scores[-2]
            },
            'manager_assessment': self._generate_performance_assessment(agent_id, history)
        }
    
    def _generate_performance_assessment(self, agent_id: str, history: List[Dict[str, Any]]) -> str:
        """Generate manager's assessment of agent performance"""
        if not history:
            return "No performance data available for assessment."
        
        recent_quality = statistics.mean([r['quality_score'] for r in history[-10:]])
        overall_quality = statistics.mean([r['quality_score'] for r in history])
        approval_rate = sum(1 for r in history if r['approval_status'] == 'approved') / len(history) * 100
        
        if recent_quality >= 90 and approval_rate >= 90:
            return f"Agent {agent_id} is performing excellently. Consistent high-quality results with minimal issues."
        elif recent_quality >= 80 and approval_rate >= 80:
            return f"Agent {agent_id} shows good performance but has room for improvement. Focus on consistency."
        elif recent_quality >= 70:
            return f"Agent {agent_id} performance is acceptable but concerning. Requires attention and improvement."
        else:
            return f"Agent {agent_id} performance is below standards. Immediate intervention required."
    
    def _handle_management_task(self, message: Message) -> Dict[str, Any]:
        """Handle management-specific tasks"""
        task_data = message.content
        task_type = task_data.get('task_type')
        
        if task_type == 'performance_review':
            return self.get_agent_performance_report(task_data.get('agent_id'))
        elif task_type == 'quality_challenge_response':
            return self._handle_challenge_response(task_data)
        else:
            return {
                'status': 'error',
                'message': f'Unknown management task: {task_type}'
            }
    
    def _handle_challenge_response(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle response to quality challenge"""
        challenge_id = task_data.get('challenge_id')
        response_text = task_data.get('response')
        
        if challenge_id not in self.quality_challenges:
            return {
                'status': 'error',
                'message': 'Challenge not found'
            }
        
        challenge = self.quality_challenges[challenge_id]
        challenge.status = 'responded'
        
        # Evaluate response (simplified)
        manager_evaluation = self._evaluate_challenge_response(challenge, response_text)
        
        return {
            'status': 'success',
            'challenge_id': challenge_id,
            'manager_evaluation': manager_evaluation,
            'next_steps': manager_evaluation.get('next_steps', [])
        }
    
    def _evaluate_challenge_response(self, challenge: QualityChallenge, response: str) -> Dict[str, Any]:
        """Evaluate agent's response to quality challenge"""
        # Simplified evaluation logic
        response_lower = response.lower()
        
        quality_indicators = ['improve', 'optimize', 'enhance', 'fix', 'address']
        explanation_indicators = ['because', 'due to', 'caused by', 'reason']
        
        has_quality_focus = any(indicator in response_lower for indicator in quality_indicators)
        has_explanation = any(indicator in response_lower for indicator in explanation_indicators)
        
        if has_quality_focus and has_explanation and len(response) > 100:
            evaluation = "Satisfactory response. Agent shows understanding and commitment to improvement."
            next_steps = ["Monitor next processing results", "Verify improvements implemented"]
            challenge.status = 'resolved'
        elif has_explanation:
            evaluation = "Partial response. Agent provided explanation but lacks improvement commitment."
            next_steps = ["Request specific improvement plan", "Schedule follow-up review"]
        else:
            evaluation = "Inadequate response. Agent needs to provide better explanation and improvement plan."
            next_steps = ["Escalate to senior management", "Consider agent retraining"]
            challenge.status = 'escalated'
        
        return {
            'evaluation': evaluation,
            'next_steps': next_steps,
            'challenge_resolved': challenge.status == 'resolved'
        }
    
    def _handle_status_update(self, message: Message) -> Dict[str, Any]:
        """Handle status updates from agents"""
        return {
            'status': 'acknowledged',
            'message': 'Status update received and logged'
        }
    
    def get_management_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive management dashboard"""
        return {
            'status': 'success',
            'dashboard_data': {
                'total_analyses': len(self.critical_analyses),
                'active_challenges': len([c for c in self.quality_challenges.values() if c.status == 'open']),
                'agent_count': len(self.agent_performance_history),
                'overall_quality_trend': self._calculate_overall_quality_trend(),
                'top_performing_agents': self._get_top_performing_agents(),
                'agents_needing_attention': self._get_agents_needing_attention(),
                'recent_critical_issues': self._get_recent_critical_issues()
            }
        }
    
    def _calculate_overall_quality_trend(self) -> Dict[str, Any]:
        """Calculate overall quality trend across all agents"""
        all_scores = []
        for agent_history in self.agent_performance_history.values():
            all_scores.extend([record['quality_score'] for record in agent_history])
        
        if not all_scores:
            return {'trend': 'no_data', 'average': 0}
        
        recent_scores = all_scores[-50:] if len(all_scores) >= 50 else all_scores
        overall_average = statistics.mean(all_scores)
        recent_average = statistics.mean(recent_scores)
        
        trend = 'improving' if recent_average > overall_average else 'declining' if recent_average < overall_average else 'stable'
        
        return {
            'trend': trend,
            'overall_average': overall_average,
            'recent_average': recent_average,
            'total_processed': len(all_scores)
        }
    
    def _get_top_performing_agents(self) -> List[Dict[str, Any]]:
        """Get top performing agents"""
        agent_averages = []
        
        for agent_id, history in self.agent_performance_history.items():
            if history:
                avg_quality = statistics.mean([r['quality_score'] for r in history])
                approval_rate = sum(1 for r in history if r['approval_status'] == 'approved') / len(history) * 100
                
                agent_averages.append({
                    'agent_id': agent_id,
                    'average_quality': avg_quality,
                    'approval_rate': approval_rate,
                    'total_processed': len(history)
                })
        
        # Sort by quality score
        agent_averages.sort(key=lambda x: x['average_quality'], reverse=True)
        
        return agent_averages[:5]  # Top 5
    
    def _get_agents_needing_attention(self) -> List[Dict[str, Any]]:
        """Get agents that need attention"""
        agents_needing_attention = []
        
        for agent_id, history in self.agent_performance_history.items():
            if history:
                recent_quality = statistics.mean([r['quality_score'] for r in history[-10:]])
                approval_rate = sum(1 for r in history[-10:] if r['approval_status'] == 'approved') / min(10, len(history)) * 100
                
                if recent_quality < 80 or approval_rate < 80:
                    agents_needing_attention.append({
                        'agent_id': agent_id,
                        'recent_quality': recent_quality,
                        'approval_rate': approval_rate,
                        'issues': 'Low quality scores' if recent_quality < 80 else 'Low approval rate'
                    })
        
        return agents_needing_attention
    
    def _get_recent_critical_issues(self) -> List[Dict[str, Any]]:
        """Get recent critical issues across all analyses"""
        recent_issues = []
        
        # Get analyses from last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for analysis in self.critical_analyses.values():
            if analysis.timestamp >= cutoff_time:
                critical_issues = [issue for issue in analysis.critical_issues if issue['severity'] == 'critical']
                for issue in critical_issues:
                    recent_issues.append({
                        'agent_id': analysis.agent_id,
                        'document_id': analysis.document_id,
                        'issue_type': issue['type'],
                        'description': issue['description'],
                        'timestamp': analysis.timestamp.isoformat()
                    })
        
        return recent_issues[-10:]  # Last 10 critical issues