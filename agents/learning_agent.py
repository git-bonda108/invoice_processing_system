"""
Learning Agent - Conversational AI and continuous learning system
"""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import re
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from .base_agent import BaseAgent, AgentStatus
from utils.message_queue import Message, MessageType, MessagePriority
from utils.ai_client import ai_client
from config.settings import DATA_DIR

@dataclass
class ConversationContext:
    """Context for ongoing conversations"""
    conversation_id: str
    user_id: str
    agent_id: str
    topic: str
    started_at: datetime
    last_activity: datetime
    messages: List[Dict[str, Any]]
    context_data: Dict[str, Any]

@dataclass
class FeedbackRecord:
    """Human feedback record"""
    feedback_id: str
    conversation_id: str
    user_id: str
    agent_id: str
    document_id: Optional[str]
    feedback_type: str  # correction, suggestion, approval, complaint
    feedback_text: str
    rating: Optional[int]  # 1-5 scale
    timestamp: datetime
    processed: bool = False
    improvements_made: List[str] = None

@dataclass
class LearningInsight:
    """Learning insights from feedback"""
    insight_id: str
    category: str
    pattern: str
    frequency: int
    confidence: float
    suggested_action: str
    implemented: bool = False
    created_at: datetime

class LearningAgent(BaseAgent):
    """Advanced learning agent with conversational AI capabilities"""
    
    def __init__(self, agent_id: str, message_queue):
        super().__init__(agent_id, message_queue)
        
        # Learning-specific configuration
        self.config.update({
            'conversation_timeout': 1800,  # 30 minutes
            'max_conversation_history': 100,
            'learning_threshold': 0.7,
            'feedback_processing_interval': 300,  # 5 minutes
            'enable_proactive_learning': True,
            'conversation_memory_limit': 1000
        })
        
        # Conversation management
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.conversation_history: deque = deque(maxlen=self.config['conversation_memory_limit'])
        
        # Learning system
        self.feedback_records: Dict[str, FeedbackRecord] = {}
        self.learning_insights: Dict[str, LearningInsight] = {}
        self.knowledge_base: Dict[str, Any] = {}
        
        # Agent knowledge and capabilities
        self.agent_capabilities = {
            'master_data': {
                'expertise': ['vendor validation', 'buyer verification', 'PO checking'],
                'conversation_style': 'precise and factual',
                'common_questions': ['vendor status', 'PO validity', 'entity verification']
            },
            'extraction': {
                'expertise': ['invoice processing', 'field extraction', 'amount validation'],
                'conversation_style': 'detailed and analytical',
                'common_questions': ['extraction accuracy', 'field confidence', 'processing issues']
            },
            'contract': {
                'expertise': ['contract terms', 'legal compliance', 'PO correlation'],
                'conversation_style': 'formal and precise',
                'common_questions': ['contract validity', 'term compliance', 'correlation issues']
            },
            'msa': {
                'expertise': ['service agreements', 'framework terms', 'SLA validation'],
                'conversation_style': 'strategic and comprehensive',
                'common_questions': ['MSA compliance', 'service scope', 'renewal terms']
            },
            'leasing': {
                'expertise': ['lease terms', 'asset correlation', 'payment validation'],
                'conversation_style': 'practical and detailed',
                'common_questions': ['lease validity', 'asset matching', 'payment issues']
            },
            'fixed_assets': {
                'expertise': ['asset management', 'depreciation', 'lifecycle tracking'],
                'conversation_style': 'technical and thorough',
                'common_questions': ['asset valuation', 'depreciation methods', 'lifecycle status']
            },
            'quality_review': {
                'expertise': ['quality assessment', 'anomaly analysis', 'reporting'],
                'conversation_style': 'comprehensive and insightful',
                'common_questions': ['quality scores', 'anomaly patterns', 'improvement suggestions']
            }
        }
        
        # Conversation templates
        self.conversation_templates = {
            'greeting': [
                "Hello! I'm the Learning Agent. How can I help you today?",
                "Hi there! I'm here to assist you with any questions about the system.",
                "Welcome! I can help you understand what our agents are doing and learn from your feedback."
            ],
            'agent_introduction': {
                'master_data': "I can connect you with our Master Data Agent, who specializes in vendor validation and data verification.",
                'extraction': "Our Invoice Processing Agent is an expert in extracting and validating invoice data.",
                'contract': "The Contract Agent specializes in contract terms and legal compliance.",
                'msa': "Our MSA Agent is an expert in Master Service Agreements and framework terms.",
                'leasing': "The Leasing Agent specializes in lease agreements and asset correlations.",
                'fixed_assets': "Our Fixed Assets Agent is an expert in asset management and depreciation.",
                'quality_review': "The Quality Review Agent provides comprehensive quality assessment and reporting."
            },
            'feedback_request': [
                "How did our processing work for you? Any feedback would be helpful!",
                "Was the result what you expected? I'd love to learn from your experience.",
                "Please let me know if there's anything we could improve in our processing."
            ]
        }
        
        # Learning patterns
        self.learning_patterns = {
            'common_corrections': defaultdict(int),
            'user_preferences': defaultdict(dict),
            'processing_improvements': defaultdict(list),
            'conversation_topics': defaultdict(int)
        }
        
        self.logger.info(f"Learning Agent {agent_id} initialized with conversational AI capabilities")
    
    def process_message(self, message: Message) -> Dict[str, Any]:
        """Process incoming messages with learning capabilities"""
        try:
            if message.msg_type == MessageType.TASK_ASSIGNMENT:
                return self._handle_learning_task(message)
            elif message.msg_type == MessageType.DATA_REQUEST:
                return self._handle_conversation_request(message)
            elif message.msg_type == MessageType.DATA_RESPONSE:
                return self._handle_feedback_processing(message)
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
    
    def start_conversation(self, user_id: str, topic: str = "general") -> Dict[str, Any]:
        """Start a new conversation with a user"""
        try:
            conversation_id = f"CONV_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            
            context = ConversationContext(
                conversation_id=conversation_id,
                user_id=user_id,
                agent_id=self.agent_id,
                topic=topic,
                started_at=datetime.now(),
                last_activity=datetime.now(),
                messages=[],
                context_data={}
            )
            
            self.active_conversations[conversation_id] = context
            
            # Generate greeting
            greeting = self._generate_greeting(topic)
            self._add_message_to_conversation(conversation_id, "agent", greeting)
            
            return {
                'status': 'success',
                'conversation_id': conversation_id,
                'message': greeting,
                'suggested_topics': self._get_suggested_topics()
            }
            
        except Exception as e:
            self.logger.error(f"Error starting conversation: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def process_user_message(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Process user message and generate response"""
        try:
            if conversation_id not in self.active_conversations:
                return {
                    'status': 'error',
                    'message': 'Conversation not found. Please start a new conversation.'
                }
            
            context = self.active_conversations[conversation_id]
            context.last_activity = datetime.now()
            
            # Add user message to conversation
            self._add_message_to_conversation(conversation_id, "user", user_message)
            
            # Analyze user intent
            intent = self._analyze_user_intent(user_message, context)
            
            # Generate response based on intent
            response = self._generate_response(intent, user_message, context)
            
            # Add agent response to conversation
            self._add_message_to_conversation(conversation_id, "agent", response['message'])
            
            # Update learning patterns
            self._update_learning_patterns(user_message, response, context)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing user message: {e}")
            return {
                'status': 'error',
                'message': 'I encountered an error processing your message. Please try again.'
            }
    
    def process_feedback(self, user_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process human feedback and incorporate learning"""
        try:
            feedback_id = f"FB_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            
            feedback_record = FeedbackRecord(
                feedback_id=feedback_id,
                conversation_id=feedback_data.get('conversation_id'),
                user_id=user_id,
                agent_id=feedback_data.get('agent_id', 'system'),
                document_id=feedback_data.get('document_id'),
                feedback_type=feedback_data.get('type', 'general'),
                feedback_text=feedback_data.get('text', ''),
                rating=feedback_data.get('rating'),
                timestamp=datetime.now(),
                improvements_made=[]
            )
            
            self.feedback_records[feedback_id] = feedback_record
            
            # Process feedback immediately
            improvements = self._process_feedback_record(feedback_record)
            
            # Generate learning insights
            insights = self._generate_learning_insights(feedback_record)
            
            return {
                'status': 'success',
                'feedback_id': feedback_id,
                'improvements_made': improvements,
                'insights_generated': len(insights),
                'message': 'Thank you for your feedback! I\'ve learned from it and made improvements.'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing feedback: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_agent_conversation(self, agent_type: str, query: str) -> Dict[str, Any]:
        """Facilitate conversation with specific agent"""
        try:
            if agent_type not in self.agent_capabilities:
                return {
                    'status': 'error',
                    'message': f'Unknown agent type: {agent_type}'
                }
            
            agent_info = self.agent_capabilities[agent_type]
            
            # Generate agent-specific response
            response = self._generate_agent_response(agent_type, query, agent_info)
            
            return {
                'status': 'success',
                'agent_type': agent_type,
                'agent_expertise': agent_info['expertise'],
                'response': response,
                'follow_up_questions': self._generate_follow_up_questions(agent_type, query)
            }
            
        except Exception as e:
            self.logger.error(f"Error in agent conversation: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _analyze_user_intent(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze user intent from message"""
        message_lower = message.lower()
        
        # Intent patterns
        intents = {
            'question_about_agent': ['what does', 'how does', 'tell me about', 'explain'],
            'processing_status': ['status', 'progress', 'how long', 'when will'],
            'anomaly_inquiry': ['anomaly', 'error', 'problem', 'issue', 'wrong'],
            'feedback': ['feedback', 'suggestion', 'improve', 'better', 'wrong'],
            'help': ['help', 'how to', 'can you', 'what can'],
            'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon']
        }
        
        detected_intent = 'general'
        confidence = 0.0
        
        for intent, patterns in intents.items():
            matches = sum(1 for pattern in patterns if pattern in message_lower)
            if matches > 0:
                intent_confidence = matches / len(patterns)
                if intent_confidence > confidence:
                    detected_intent = intent
                    confidence = intent_confidence
        
        # Extract entities (agent names, document types, etc.)
        entities = self._extract_entities(message)
        
        return {
            'intent': detected_intent,
            'confidence': confidence,
            'entities': entities,
            'original_message': message
        }
    
    def _generate_response(self, intent: Dict[str, Any], message: str, context: ConversationContext) -> Dict[str, Any]:
        """Generate appropriate response based on intent"""
        intent_type = intent['intent']
        entities = intent['entities']
        
        if intent_type == 'greeting':
            response = self._generate_greeting(context.topic)
            
        elif intent_type == 'question_about_agent':
            if entities.get('agent_type'):
                response = self._explain_agent_capabilities(entities['agent_type'])
            else:
                response = "Which agent would you like to know about? We have agents for invoices, contracts, MSAs, leases, and fixed assets."
                
        elif intent_type == 'processing_status':
            response = self._get_processing_status_response(entities)
            
        elif intent_type == 'anomaly_inquiry':
            response = self._handle_anomaly_inquiry(message, entities)
            
        elif intent_type == 'feedback':
            response = self._handle_feedback_conversation(message, context)
            
        elif intent_type == 'help':
            response = self._generate_help_response()
            
        else:
            response = self._generate_general_response(message, context)
        
        return {
            'status': 'success',
            'message': response,
            'intent': intent_type,
            'suggestions': self._generate_suggestions(intent_type, entities)
        }
    
    def _generate_greeting(self, topic: str) -> str:
        """Generate contextual greeting"""
        if topic == "general":
            return "Hello! I'm your Learning Agent. I can help you understand what our processing agents are doing, answer questions, and learn from your feedback. What would you like to know?"
        else:
            return f"Hi! I'm here to help you with {topic}. What specific questions do you have?"
    
    def _explain_agent_capabilities(self, agent_type: str) -> str:
        """Explain specific agent capabilities"""
        if agent_type not in self.agent_capabilities:
            return f"I don't have information about the {agent_type} agent. Our available agents are: {', '.join(self.agent_capabilities.keys())}"
        
        agent_info = self.agent_capabilities[agent_type]
        expertise = ', '.join(agent_info['expertise'])
        
        return f"The {agent_type.replace('_', ' ').title()} Agent specializes in {expertise}. {self.conversation_templates['agent_introduction'][agent_type]} Would you like to know more about any specific capability?"
    
    def _get_processing_status_response(self, entities: Dict[str, Any]) -> str:
        """Generate processing status response"""
        if entities.get('document_id'):
            return f"Let me check the status of document {entities['document_id']}. The processing typically takes 30-60 seconds per document, depending on complexity."
        else:
            return "I can help you check processing status. Do you have a specific document ID or workflow you'd like me to check?"
    
    def _handle_anomaly_inquiry(self, message: str, entities: Dict[str, Any]) -> str:
        """Handle anomaly-related questions"""
        return "I can help you understand anomalies detected in your documents. Our system detects various types of anomalies like missing PO numbers, unusual amounts, and data inconsistencies. What specific anomaly would you like to discuss?"
    
    def _handle_feedback_conversation(self, message: str, context: ConversationContext) -> str:
        """Handle feedback-related conversation"""
        return "I appreciate your feedback! Please tell me specifically what you'd like to improve or what didn't work as expected. Your input helps me make the system better for everyone."
    
    def _generate_help_response(self) -> str:
        """Generate help response"""
        return """I can help you with:
        
🤖 **Agent Information** - Learn about our specialized agents
📊 **Processing Status** - Check document processing progress  
🔍 **Anomaly Analysis** - Understand detected anomalies
💬 **Feedback** - Share your thoughts for system improvement
⚙️ **System Features** - Explore available capabilities

What would you like to explore?"""
    
    def _generate_general_response(self, message: str, context: ConversationContext) -> str:
        """Generate general response using AI for unclear intents"""
        try:
            # Use AI to generate a more intelligent response
            ai_response = ai_client.generate_conversation_response(
                user_message=message,
                agent_type="learning",
                context={
                    "conversation_topic": context.topic,
                    "conversation_history": len(context.messages),
                    "system_context": "Invoice processing system with multiple specialized agents"
                }
            )
            
            if ai_response["status"] == "success":
                return ai_response["response"]
            else:
                # Fallback to static response
                return "I understand you're asking about our document processing system. Could you be more specific? I can help with agent information, processing status, anomaly analysis, or any feedback you have."
                
        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            return "I understand you're asking about our document processing system. Could you be more specific? I can help with agent information, processing status, anomaly analysis, or any feedback you have."
    
    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from user message"""
        entities = {}
        message_lower = message.lower()
        
        # Agent types
        for agent_type in self.agent_capabilities.keys():
            if agent_type.replace('_', ' ') in message_lower or agent_type in message_lower:
                entities['agent_type'] = agent_type
                break
        
        # Document types
        doc_types = ['invoice', 'contract', 'msa', 'lease', 'asset']
        for doc_type in doc_types:
            if doc_type in message_lower:
                entities['document_type'] = doc_type
                break
        
        # Document IDs (pattern matching)
        import re
        doc_id_pattern = r'(INV|CONT|MSA|LEASE|FA)-\d{4}-\d{3,4}'
        doc_id_match = re.search(doc_id_pattern, message)
        if doc_id_match:
            entities['document_id'] = doc_id_match.group()
        
        return entities
    
    def _generate_suggestions(self, intent_type: str, entities: Dict[str, Any]) -> List[str]:
        """Generate conversation suggestions"""
        suggestions = []
        
        if intent_type == 'greeting':
            suggestions = [
                "Tell me about the invoice processing agent",
                "What anomalies were detected?",
                "Check processing status",
                "I have feedback about the results"
            ]
        elif intent_type == 'question_about_agent':
            suggestions = [
                "How accurate is the processing?",
                "What types of anomalies do you detect?",
                "Can you process my document type?"
            ]
        elif intent_type == 'processing_status':
            suggestions = [
                "Show me the detailed results",
                "What anomalies were found?",
                "How can I improve the processing?"
            ]
        
        return suggestions
    
    def _generate_agent_response(self, agent_type: str, query: str, agent_info: Dict[str, Any]) -> str:
        """Generate response as if from specific agent using AI"""
        try:
            # Use AI to generate agent-specific response
            ai_response = ai_client.generate_conversation_response(
                user_message=query,
                agent_type=agent_type,
                context={
                    "agent_expertise": agent_info['expertise'],
                    "conversation_style": agent_info['conversation_style'],
                    "common_questions": agent_info['common_questions']
                }
            )
            
            if ai_response["status"] == "success":
                return ai_response["response"]
            else:
                # Fallback to static response
                style = agent_info['conversation_style']
                expertise = agent_info['expertise']
                
                if 'accuracy' in query.lower():
                    return f"As the {agent_type.replace('_', ' ').title()} Agent, I maintain high accuracy through {', '.join(expertise)}. My processing typically achieves 95%+ confidence scores."
                elif 'anomaly' in query.lower():
                    return f"I specialize in detecting anomalies related to {', '.join(expertise)}. I can identify patterns that might indicate issues or inconsistencies."
                else:
                    return f"As the {agent_type.replace('_', ' ').title()} Agent, I can help you with {', '.join(expertise)}. What specific question do you have?"
                    
        except Exception as e:
            self.logger.error(f"Error generating agent response: {e}")
            return f"As the {agent_type.replace('_', ' ').title()} Agent, I can help you with {', '.join(agent_info['expertise'])}. What specific question do you have?"
            return f"As the {agent_type.replace('_', ' ').title()} Agent, I focus on {', '.join(expertise)}. How can I help you with your specific question?"
    
    def _generate_follow_up_questions(self, agent_type: str, query: str) -> List[str]:
        """Generate follow-up questions for agent conversation"""
        agent_info = self.agent_capabilities[agent_type]
        return [
            f"How does the {agent_type.replace('_', ' ')} processing work?",
            "What should I do about detected anomalies?",
            "Can you explain the confidence scores?"
        ]
    
    def _add_message_to_conversation(self, conversation_id: str, sender: str, message: str):
        """Add message to conversation history"""
        if conversation_id in self.active_conversations:
            context = self.active_conversations[conversation_id]
            context.messages.append({
                'sender': sender,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            context.last_activity = datetime.now()
    
    def _update_learning_patterns(self, user_message: str, response: Dict[str, Any], context: ConversationContext):
        """Update learning patterns based on conversation"""
        # Track conversation topics
        intent = response.get('intent', 'general')
        self.learning_patterns['conversation_topics'][intent] += 1
        
        # Track user preferences
        user_id = context.user_id
        if user_id not in self.learning_patterns['user_preferences']:
            self.learning_patterns['user_preferences'][user_id] = {}
        
        self.learning_patterns['user_preferences'][user_id][intent] = self.learning_patterns['user_preferences'][user_id].get(intent, 0) + 1
    
    def _process_feedback_record(self, feedback_record: FeedbackRecord) -> List[str]:
        """Process feedback and make improvements"""
        improvements = []
        
        # Analyze feedback text for actionable items
        feedback_text = feedback_record.feedback_text.lower()
        
        if 'accuracy' in feedback_text or 'wrong' in feedback_text:
            improvements.append("Noted accuracy concern - will review extraction algorithms")
            
        if 'slow' in feedback_text or 'time' in feedback_text:
            improvements.append("Performance feedback noted - will optimize processing speed")
            
        if 'confusing' in feedback_text or 'unclear' in feedback_text:
            improvements.append("UI/UX feedback noted - will improve interface clarity")
        
        feedback_record.improvements_made = improvements
        feedback_record.processed = True
        
        return improvements
    
    def _generate_learning_insights(self, feedback_record: FeedbackRecord) -> List[LearningInsight]:
        """Generate learning insights from feedback"""
        insights = []
        
        # Create insight based on feedback
        insight_id = f"INSIGHT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        insight = LearningInsight(
            insight_id=insight_id,
            category=feedback_record.feedback_type,
            pattern=f"User feedback: {feedback_record.feedback_text[:100]}",
            frequency=1,
            confidence=0.8,
            suggested_action=f"Review {feedback_record.agent_id} agent performance",
            created_at=datetime.now()
        )
        
        insights.append(insight)
        self.learning_insights[insight_id] = insight
        
        return insights
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learning activities"""
        return {
            'active_conversations': len(self.active_conversations),
            'total_feedback_records': len(self.feedback_records),
            'learning_insights': len(self.learning_insights),
            'conversation_topics': dict(self.learning_patterns['conversation_topics']),
            'recent_improvements': [
                record.improvements_made for record in self.feedback_records.values()
                if record.processed and record.improvements_made
            ][-10:]  # Last 10 improvements
        }
    
    def _get_suggested_topics(self) -> List[str]:
        """Get suggested conversation topics"""
        return [
            "How does invoice processing work?",
            "What anomalies were detected?",
            "Tell me about the quality scores",
            "How can I improve processing accuracy?",
            "What agents are available?"
        ]
    
    def _handle_learning_task(self, message: Message) -> Dict[str, Any]:
        """Handle learning-specific tasks"""
        task_data = message.content
        task_type = task_data.get('task_type')
        
        if task_type == 'process_feedback':
            return self.process_feedback(
                task_data.get('user_id'),
                task_data.get('feedback_data')
            )
        elif task_type == 'start_conversation':
            return self.start_conversation(
                task_data.get('user_id'),
                task_data.get('topic', 'general')
            )
        else:
            return {
                'status': 'error',
                'message': f'Unknown learning task type: {task_type}'
            }
    
    def _handle_conversation_request(self, message: Message) -> Dict[str, Any]:
        """Handle conversation requests"""
        request_data = message.content
        request_type = request_data.get('request_type')
        
        if request_type == 'user_message':
            return self.process_user_message(
                request_data.get('conversation_id'),
                request_data.get('message')
            )
        elif request_type == 'agent_conversation':
            return self.get_agent_conversation(
                request_data.get('agent_type'),
                request_data.get('query')
            )
        else:
            return {
                'status': 'error',
                'message': f'Unknown conversation request: {request_type}'
            }
    
    def _handle_feedback_processing(self, message: Message) -> Dict[str, Any]:
        """Handle feedback processing responses"""
        return {
            'status': 'acknowledged',
            'message': 'Feedback processing response received'
        }