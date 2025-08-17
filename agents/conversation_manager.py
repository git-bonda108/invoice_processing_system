"""
Conversation Manager - Coordinates human-agent interactions
"""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict
import asyncio

from .base_agent import BaseAgent, AgentStatus
from utils.message_queue import Message, MessageType, MessagePriority
from utils.ai_client import ai_client
from config.settings import DATA_DIR

@dataclass
class ConversationSession:
    """Active conversation session"""
    session_id: str
    user_id: str
    started_at: datetime
    last_activity: datetime
    active_agents: List[str]
    conversation_context: Dict[str, Any]
    message_history: List[Dict[str, Any]]
    current_topic: str
    user_preferences: Dict[str, Any]

@dataclass
class AgentInteraction:
    """Agent interaction record"""
    interaction_id: str
    session_id: str
    agent_id: str
    user_query: str
    agent_response: str
    confidence: float
    timestamp: datetime
    user_satisfaction: Optional[int] = None
    follow_up_needed: bool = False

class ConversationManager(BaseAgent):
    """Manages conversations between humans and agents"""
    
    def __init__(self, agent_id: str, message_queue):
        super().__init__(agent_id, message_queue)
        
        # Conversation management configuration
        self.config.update({
            'session_timeout': 3600,  # 1 hour
            'max_concurrent_sessions': 50,
            'response_timeout': 30,  # seconds
            'enable_multi_agent_conversations': True,
            'conversation_logging': True,
            'proactive_assistance': True
        })
        
        # Active sessions
        self.active_sessions: Dict[str, ConversationSession] = {}
        self.interaction_history: Dict[str, AgentInteraction] = {}
        
        # Agent routing and capabilities
        self.agent_routing = {
            'invoice': ['extraction', 'master_data'],
            'contract': ['contract', 'master_data'],
            'msa': ['msa', 'master_data'],
            'lease': ['leasing', 'fixed_assets'],
            'asset': ['fixed_assets', 'leasing'],
            'quality': ['quality_review'],
            'general': ['learning']
        }
        
        # Conversation flows
        self.conversation_flows = {
            'document_processing': [
                'upload_document',
                'classify_document',
                'assign_agent',
                'process_document',
                'review_results',
                'provide_feedback'
            ],
            'anomaly_investigation': [
                'identify_anomaly',
                'explain_anomaly',
                'suggest_resolution',
                'implement_fix',
                'verify_resolution'
            ],
            'system_inquiry': [
                'understand_question',
                'route_to_expert',
                'provide_answer',
                'offer_follow_up'
            ]
        }
        
        # Response templates
        self.response_templates = {
            'welcome': "Welcome to the Agentic AI Invoice Processing System! I'm your Conversation Manager. How can I help you today?",
            'agent_introduction': "Let me connect you with the right expert for your question.",
            'processing_update': "I'll keep you updated on the processing progress.",
            'error_handling': "I understand there's an issue. Let me get the right agent to help resolve this.",
            'feedback_acknowledgment': "Thank you for your feedback! I'll make sure it's incorporated into our learning system."
        }
        
        self.logger.info(f"Conversation Manager {agent_id} initialized")
    
    def start_session(self, user_id: str, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start a new conversation session"""
        try:
            session_id = f"SESSION_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            
            session = ConversationSession(
                session_id=session_id,
                user_id=user_id,
                started_at=datetime.now(),
                last_activity=datetime.now(),
                active_agents=[],
                conversation_context=initial_context or {},
                message_history=[],
                current_topic='general',
                user_preferences={}
            )
            
            self.active_sessions[session_id] = session
            
            # Add welcome message
            welcome_message = {
                'sender': 'conversation_manager',
                'message': self.response_templates['welcome'],
                'timestamp': datetime.now().isoformat(),
                'suggestions': self._get_initial_suggestions()
            }
            
            session.message_history.append(welcome_message)
            
            return {
                'status': 'success',
                'session_id': session_id,
                'welcome_message': welcome_message,
                'available_topics': list(self.agent_routing.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Error starting session: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def process_user_input(self, session_id: str, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user input and coordinate agent responses"""
        try:
            if session_id not in self.active_sessions:
                return {
                    'status': 'error',
                    'message': 'Session not found. Please start a new conversation.'
                }
            
            session = self.active_sessions[session_id]
            session.last_activity = datetime.now()
            
            # Add user message to history
            user_message = {
                'sender': 'user',
                'message': user_input,
                'timestamp': datetime.now().isoformat(),
                'context': context or {}
            }
            session.message_history.append(user_message)
            
            # Analyze user intent and route to appropriate agent
            routing_decision = self._analyze_and_route(user_input, session, context)
            
            # Get response from appropriate agent(s)
            response = self._coordinate_agent_response(routing_decision, session)
            
            # Add response to history
            session.message_history.append(response)
            
            # Update session context
            self._update_session_context(session, user_input, response)
            
            return {
                'status': 'success',
                'session_id': session_id,
                'response': response,
                'routing_info': routing_decision,
                'session_context': session.conversation_context
            }
            
        except Exception as e:
            self.logger.error(f"Error processing user input: {e}")
            return {
                'status': 'error',
                'message': 'I encountered an error processing your request. Please try again.'
            }
    
    def _analyze_and_route(self, user_input: str, session: ConversationSession, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze user input and determine routing"""
        user_input_lower = user_input.lower()
        
        # Intent analysis
        intent_scores = {}
        
        # Document type detection
        doc_types = {
            'invoice': ['invoice', 'bill', 'payment', 'amount'],
            'contract': ['contract', 'agreement', 'terms', 'legal'],
            'msa': ['msa', 'master service', 'framework', 'service agreement'],
            'lease': ['lease', 'rent', 'rental', 'leasing'],
            'asset': ['asset', 'equipment', 'depreciation', 'fixed asset']
        }
        
        for doc_type, keywords in doc_types.items():
            score = sum(1 for keyword in keywords if keyword in user_input_lower)
            if score > 0:
                intent_scores[doc_type] = score / len(keywords)
        
        # Action detection
        actions = {
            'upload': ['upload', 'process', 'submit', 'analyze'],
            'status': ['status', 'progress', 'how long', 'when'],
            'anomaly': ['anomaly', 'error', 'problem', 'issue', 'wrong'],
            'help': ['help', 'how', 'what', 'explain'],
            'feedback': ['feedback', 'improve', 'suggestion', 'better']
        }
        
        detected_action = 'general'
        max_action_score = 0
        
        for action, keywords in actions.items():
            score = sum(1 for keyword in keywords if keyword in user_input_lower)
            if score > max_action_score:
                max_action_score = score
                detected_action = action
        
        # Determine primary topic
        primary_topic = 'general'
        if intent_scores:
            primary_topic = max(intent_scores.items(), key=lambda x: x[1])[0]
        
        # Get appropriate agents
        target_agents = self.agent_routing.get(primary_topic, ['learning'])
        
        return {
            'primary_topic': primary_topic,
            'detected_action': detected_action,
            'target_agents': target_agents,
            'intent_scores': intent_scores,
            'confidence': max(intent_scores.values()) if intent_scores else 0.5,
            'routing_reason': f"Detected {primary_topic} topic with {detected_action} action"
        }
    
    def _coordinate_agent_response(self, routing_decision: Dict[str, Any], session: ConversationSession) -> Dict[str, Any]:
        """Coordinate response from appropriate agents"""
        target_agents = routing_decision['target_agents']
        primary_topic = routing_decision['primary_topic']
        detected_action = routing_decision['detected_action']
        
        # Get the last user message
        last_user_message = None
        for msg in reversed(session.message_history):
            if msg['sender'] == 'user':
                last_user_message = msg['message']
                break
        
        if not last_user_message:
            return self._generate_error_response("No user message found")
        
        # Generate response based on action and topic
        if detected_action == 'upload':
            response = self._handle_upload_request(primary_topic, last_user_message, session)
        elif detected_action == 'status':
            response = self._handle_status_request(primary_topic, last_user_message, session)
        elif detected_action == 'anomaly':
            response = self._handle_anomaly_request(primary_topic, last_user_message, session)
        elif detected_action == 'help':
            response = self._handle_help_request(primary_topic, last_user_message, session)
        elif detected_action == 'feedback':
            response = self._handle_feedback_request(primary_topic, last_user_message, session)
        else:
            response = self._handle_general_request(primary_topic, last_user_message, session)
        
        # Add agent information
        response['involved_agents'] = target_agents
        response['routing_decision'] = routing_decision
        
        return response
    
    def _handle_upload_request(self, topic: str, message: str, session: ConversationSession) -> Dict[str, Any]:
        """Handle document upload requests"""
        return {
            'sender': 'conversation_manager',
            'message': f"I can help you upload and process {topic} documents. Please use the upload interface to select your files. I'll coordinate with our specialized agents to process them.",
            'timestamp': datetime.now().isoformat(),
            'action_required': 'document_upload',
            'suggested_agents': self.agent_routing.get(topic, ['learning']),
            'next_steps': [
                f"Upload your {topic} document(s)",
                "I'll classify and route them to the right agents",
                "You'll get real-time processing updates",
                "Review results and provide feedback"
            ]
        }
    
    def _handle_status_request(self, topic: str, message: str, session: ConversationSession) -> Dict[str, Any]:
        """Handle status inquiry requests"""
        return {
            'sender': 'conversation_manager',
            'message': f"I can check the processing status for your {topic} documents. Let me get the latest information from our processing agents.",
            'timestamp': datetime.now().isoformat(),
            'action_required': 'status_check',
            'status_info': {
                'checking': True,
                'estimated_time': '30-60 seconds per document',
                'current_queue': 'Low volume - fast processing'
            }
        }
    
    def _handle_anomaly_request(self, topic: str, message: str, session: ConversationSession) -> Dict[str, Any]:
        """Handle anomaly investigation requests"""
        return {
            'sender': 'conversation_manager',
            'message': f"I understand you're asking about anomalies in {topic} processing. Let me connect you with our quality review experts to explain what was detected and how to resolve it.",
            'timestamp': datetime.now().isoformat(),
            'action_required': 'anomaly_investigation',
            'anomaly_types': self._get_common_anomalies(topic),
            'next_steps': [
                "Review detected anomalies",
                "Get expert explanation",
                "Implement suggested fixes",
                "Verify resolution"
            ]
        }
    
    def _handle_help_request(self, topic: str, message: str, session: ConversationSession) -> Dict[str, Any]:
        """Handle help requests"""
        help_content = self._generate_help_content(topic)
        
        return {
            'sender': 'conversation_manager',
            'message': f"I'm here to help you with {topic} processing. Here's what I can assist you with:",
            'timestamp': datetime.now().isoformat(),
            'help_content': help_content,
            'available_agents': self.agent_routing.get(topic, ['learning']),
            'quick_actions': [
                f"Process {topic} documents",
                "Check processing status",
                "Investigate anomalies",
                "Get quality reports"
            ]
        }
    
    def _handle_feedback_request(self, topic: str, message: str, session: ConversationSession) -> Dict[str, Any]:
        """Handle feedback requests"""
        return {
            'sender': 'conversation_manager',
            'message': "Thank you for wanting to provide feedback! Your input helps our learning system improve. I'll connect you with our Learning Agent to process your feedback.",
            'timestamp': datetime.now().isoformat(),
            'action_required': 'feedback_collection',
            'feedback_types': [
                'Processing accuracy',
                'System performance',
                'User interface',
                'Feature requests',
                'General suggestions'
            ]
        }
    
    def _handle_general_request(self, topic: str, message: str, session: ConversationSession) -> Dict[str, Any]:
        """Handle general requests"""
        return {
            'sender': 'conversation_manager',
            'message': f"I can help you with {topic} related questions. Could you be more specific about what you'd like to know or do?",
            'timestamp': datetime.now().isoformat(),
            'suggestions': [
                f"Upload {topic} documents for processing",
                f"Check {topic} processing status",
                f"Learn about {topic} anomaly detection",
                f"Get help with {topic} features"
            ]
        }
    
    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            'sender': 'conversation_manager',
            'message': "I encountered an issue processing your request. Please try rephrasing your question or contact support if the problem persists.",
            'timestamp': datetime.now().isoformat(),
            'error': error_message,
            'suggestions': [
                "Try rephrasing your question",
                "Check if you're asking about a specific document type",
                "Use the help command for guidance"
            ]
        }
    
    def _get_common_anomalies(self, topic: str) -> List[str]:
        """Get common anomalies for document type"""
        anomaly_map = {
            'invoice': ['Missing PO number', 'Unusual amounts', 'Invalid dates', 'Unknown vendor'],
            'contract': ['Amount variance', 'Missing terms', 'Invalid PO correlation'],
            'msa': ['Missing SLA terms', 'Vague pricing', 'Short/long terms'],
            'lease': ['Missing asset info', 'Payment mismatches', 'Asset correlation issues'],
            'asset': ['Invalid depreciation', 'Missing specifications', 'High values']
        }
        return anomaly_map.get(topic, ['Data quality issues', 'Processing errors'])
    
    def _generate_help_content(self, topic: str) -> Dict[str, Any]:
        """Generate help content for topic"""
        return {
            'overview': f"Our {topic} processing system uses specialized AI agents to extract, validate, and analyze your documents.",
            'capabilities': [
                f"Automatic {topic} field extraction",
                f"{topic.title()} anomaly detection",
                f"Quality scoring and validation",
                f"Real-time processing updates"
            ],
            'getting_started': [
                f"Upload your {topic} documents",
                "Wait for automatic processing",
                "Review results and anomalies",
                "Provide feedback for improvement"
            ]
        }
    
    def _update_session_context(self, session: ConversationSession, user_input: str, response: Dict[str, Any]):
        """Update session context based on conversation"""
        # Update current topic
        if 'routing_decision' in response:
            session.current_topic = response['routing_decision']['primary_topic']
        
        # Update active agents
        if 'involved_agents' in response:
            for agent in response['involved_agents']:
                if agent not in session.active_agents:
                    session.active_agents.append(agent)
        
        # Update conversation context
        session.conversation_context.update({
            'last_topic': session.current_topic,
            'last_action': response.get('action_required', 'general'),
            'message_count': len(session.message_history)
        })
    
    def _get_initial_suggestions(self) -> List[str]:
        """Get initial conversation suggestions"""
        return [
            "Upload invoice documents for processing",
            "Check processing status",
            "Learn about anomaly detection",
            "Get help with the system",
            "Provide feedback"
        ]
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of conversation session"""
        if session_id not in self.active_sessions:
            return {
                'status': 'error',
                'message': 'Session not found'
            }
        
        session = self.active_sessions[session_id]
        
        return {
            'status': 'success',
            'session_id': session_id,
            'user_id': session.user_id,
            'duration': (datetime.now() - session.started_at).total_seconds(),
            'message_count': len(session.message_history),
            'topics_discussed': [session.current_topic],
            'active_agents': session.active_agents,
            'last_activity': session.last_activity.isoformat()
        }
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End conversation session"""
        if session_id not in self.active_sessions:
            return {
                'status': 'error',
                'message': 'Session not found'
            }
        
        session = self.active_sessions[session_id]
        
        # Archive session
        session_summary = self.get_session_summary(session_id)
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        return {
            'status': 'success',
            'message': 'Session ended successfully',
            'session_summary': session_summary
        }
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """Get all active sessions"""
        return {
            'status': 'success',
            'active_sessions': len(self.active_sessions),
            'sessions': [
                {
                    'session_id': session_id,
                    'user_id': session.user_id,
                    'current_topic': session.current_topic,
                    'last_activity': session.last_activity.isoformat(),
                    'message_count': len(session.message_history)
                }
                for session_id, session in self.active_sessions.items()
            ]
        }
    
    def process_message(self, message: Message) -> Dict[str, Any]:
        """Process incoming messages"""
        try:
            if message.msg_type == MessageType.TASK_ASSIGNMENT:
                return self._handle_conversation_task(message)
            elif message.msg_type == MessageType.DATA_REQUEST:
                return self._handle_conversation_request(message)
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
    
    def _handle_conversation_task(self, message: Message) -> Dict[str, Any]:
        """Handle conversation management tasks"""
        task_data = message.content
        task_type = task_data.get('task_type')
        
        if task_type == 'start_session':
            return self.start_session(
                task_data.get('user_id'),
                task_data.get('initial_context')
            )
        elif task_type == 'process_input':
            return self.process_user_input(
                task_data.get('session_id'),
                task_data.get('user_input'),
                task_data.get('context')
            )
        elif task_type == 'end_session':
            return self.end_session(task_data.get('session_id'))
        else:
            return {
                'status': 'error',
                'message': f'Unknown conversation task: {task_type}'
            }
    
    def _handle_conversation_request(self, message: Message) -> Dict[str, Any]:
        """Handle conversation requests"""
        request_data = message.content
        request_type = request_data.get('request_type')
        
        if request_type == 'session_summary':
            return self.get_session_summary(request_data.get('session_id'))
        elif request_type == 'active_sessions':
            return self.get_active_sessions()
        else:
            return {
                'status': 'error',
                'message': f'Unknown conversation request: {request_type}'
            }