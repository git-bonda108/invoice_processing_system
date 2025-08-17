"""
Enhanced Base Agent Class for the Agentic AI Invoice Processing System
"""
import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..utils.message_queue import (
    MessageQueue, Message, MessageType, MessagePriority, MessageStatus,
    create_message, create_task_assignment, create_data_request, create_anomaly_alert
)

class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    STOPPED = "stopped"
    LEARNING = "learning"
    VALIDATING = "validating"

@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_processing_time: float = 0.0
    total_processing_time: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    anomalies_detected: int = 0
    confidence_scores: List[float] = None
    last_task_time: Optional[datetime] = None
    error_count: int = 0
    learning_iterations: int = 0
    
    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = []
    
    def add_confidence_score(self, score: float) -> None:
        """Add a confidence score and update average"""
        self.confidence_scores.append(score)
        if len(self.confidence_scores) > 100:  # Keep last 100 scores
            self.confidence_scores.pop(0)
        
        self.average_processing_time = sum(self.confidence_scores) / len(self.confidence_scores)
    
    def record_task_completion(self, processing_time: float, confidence: float) -> None:
        """Record task completion metrics"""
        self.tasks_completed += 1
        self.total_processing_time += processing_time
        self.average_processing_time = self.total_processing_time / self.tasks_completed
        self.add_confidence_score(confidence)
        self.last_task_time = datetime.now()
    
    def record_task_failure(self, error: str) -> None:
        """Record task failure metrics"""
        self.tasks_failed += 1
        self.error_count += 1
        self.last_task_time = datetime.now()

class BaseAgent(ABC):
    """Enhanced base class for all agents in the system"""
    
    def __init__(self, agent_id: str, name: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.name = name
        self.config = config
        self.status = AgentStatus.IDLE
        self.metrics = AgentMetrics()
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # Threading and autonomy
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.autonomous = True
        self.decision_threshold = config.get("confidence_threshold", 0.8)
        
        # Message handling
        self.message_queue = message_queue
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.setup_message_handlers()
        
        # Create agent queue
        self.message_queue.create_queue(self.agent_id)
        
        # Agent-specific data
        self.current_task: Optional[Dict[str, Any]] = None
        self.task_history: List[Dict[str, Any]] = []
        self.knowledge_base: Dict[str, Any] = {}
        self.learning_data: List[Dict[str, Any]] = []
        
        # Workflow state
        self.workflow_state: Dict[str, Any] = {}
        self.collaboration_partners: List[str] = []
        self.escalation_path: List[str] = []
        
        # Performance tracking
        self.start_time = datetime.now()
        self.performance_history: List[Dict[str, Any]] = []
        
        self.logger.info(f"Agent {self.name} ({self.agent_id}) initialized with config: {config}")
    
    def setup_message_handlers(self) -> None:
        """Setup message type handlers - to be overridden by subclasses"""
        self.message_handlers = {
            MessageType.TASK_ASSIGNMENT: self.handle_task_assignment,
            MessageType.DATA_REQUEST: self.handle_data_request,
            MessageType.DATA_RESPONSE: self.handle_data_response,
            MessageType.VALIDATION_REQUEST: self.handle_validation_request,
            MessageType.VALIDATION_RESPONSE: self.handle_validation_response,
            MessageType.ANOMALY_ALERT: self.handle_anomaly_alert,
            MessageType.HUMAN_FEEDBACK: self.handle_human_feedback,
            MessageType.WORKFLOW_UPDATE: self.handle_workflow_update,
            MessageType.QUALITY_REVIEW: self.handle_quality_review,
            MessageType.LEARNING_UPDATE: self.handle_learning_update,
            MessageType.SYSTEM_NOTIFICATION: self.handle_system_notification,
            MessageType.ERROR: self.handle_error_message,
            MessageType.HEARTBEAT: self.handle_heartbeat
        }
    
    def start(self) -> None:
        """Start the agent"""
        if not self.running:
            self.running = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            self.logger.info(f"Agent {self.name} started")
    
    def stop(self) -> None:
        """Stop the agent"""
        if self.running:
            self.running = False
            self.stop_event.set()
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5.0)
            self.logger.info(f"Agent {self.name} stopped")
    
    def _run(self) -> None:
        """Main agent loop"""
        self.logger.info(f"Agent {self.name} main loop started")
        
        while self.running and not self.stop_event.is_set():
            try:
                # Process incoming messages
                message = self.message_queue.receive_message(self.agent_id, timeout=1.0)
                if message:
                    self._process_message(message)
                
                # Autonomous decision making
                if self.autonomous and self.status == AgentStatus.IDLE:
                    self._autonomous_decision_making()
                
                # Performance monitoring
                self._update_performance_metrics()
                
                # Send heartbeat
                if time.time() % 30 < 1:  # Every 30 seconds
                    self._send_heartbeat()
                
            except Exception as e:
                self.logger.error(f"Error in agent main loop: {e}")
                self.status = AgentStatus.ERROR
                time.sleep(1)
        
        self.logger.info(f"Agent {self.name} main loop stopped")
    
    def _process_message(self, message: Message) -> None:
        """Process incoming message"""
        try:
            message_type = message.message_type
            handler = self.message_handlers.get(message_type)
            
            if handler:
                self.logger.debug(f"Processing {message_type.value} message: {message.message_id}")
                handler(message)
                self.message_queue.mark_completed(message.message_id)
            else:
                self.logger.warning(f"No handler for message type: {message_type.value}")
                self.message_queue.mark_failed(message.message_id, "No handler available")
                
        except Exception as e:
            self.logger.error(f"Error processing message {message.message_id}: {e}")
            self.message_queue.mark_failed(message.message_id, str(e))
    
    def _autonomous_decision_making(self) -> None:
        """Autonomous decision making logic - to be overridden by subclasses"""
        pass
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics"""
        current_time = datetime.now()
        uptime = (current_time - self.start_time).total_seconds()
        
        performance_data = {
            "timestamp": current_time.isoformat(),
            "uptime": uptime,
            "status": self.status.value,
            "queue_size": self.message_queue.get_queue_status(self.agent_id).get("size", 0),
            "memory_usage": self._get_memory_usage(),
            "cpu_usage": self._get_cpu_usage()
        }
        
        self.performance_history.append(performance_data)
        
        # Keep only last 1000 performance records
        if len(self.performance_history) > 1000:
            self.performance_history.pop(0)
    
    def _send_heartbeat(self) -> None:
        """Send heartbeat message"""
        heartbeat_msg = create_message(
            message_type=MessageType.HEARTBEAT,
            sender_id=self.agent_id,
            payload={
                "status": self.status.value,
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "tasks_completed": self.metrics.tasks_completed,
                    "tasks_failed": self.metrics.tasks_failed,
                    "uptime": (datetime.now() - self.start_time).total_seconds()
                }
            },
            priority=MessagePriority.LOW
        )
        
        self.message_queue.send_message(heartbeat_msg)
    
    def _get_memory_usage(self) -> float:
        """Get memory usage - simplified implementation"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get CPU usage - simplified implementation"""
        try:
            import psutil
            process = psutil.Process()
            return process.cpu_percent()
        except ImportError:
            return 0.0
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def detect_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in data - to be implemented by subclasses"""
        pass
    
    # Message handler methods - can be overridden by subclasses
    def handle_task_assignment(self, message: Message) -> None:
        """Handle task assignment message"""
        try:
            task_data = message.payload.get("task_data", {})
            self.current_task = task_data
            self.status = AgentStatus.PROCESSING
            
            self.logger.info(f"Task assigned: {message.payload.get('task_type', 'Unknown')}")
            
            # Process task
            result = self.process_task(task_data)
            
            # Send response
            response_msg = create_message(
                message_type=MessageType.DATA_RESPONSE,
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                payload={
                    "task_id": message.payload.get("task_type"),
                    "result": result,
                    "confidence": result.get("confidence", 0.0),
                    "processing_time": result.get("processing_time", 0.0)
                }
            )
            
            self.message_queue.send_message(response_msg)
            self.status = AgentStatus.IDLE
            
        except Exception as e:
            self.logger.error(f"Error handling task assignment: {e}")
            self.status = AgentStatus.ERROR
            self.metrics.record_task_failure(str(e))
    
    def handle_data_request(self, message: Message) -> None:
        """Handle data request message"""
        try:
            data_type = message.payload.get("data_type", "")
            query_params = message.payload.get("query_params", {})
            
            # Get requested data
            data = self._get_requested_data(data_type, query_params)
            
            # Send response
            response_msg = create_message(
                message_type=MessageType.DATA_RESPONSE,
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                payload={
                    "data_type": data_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            self.message_queue.send_message(response_msg)
            
        except Exception as e:
            self.logger.error(f"Error handling data request: {e}")
            error_msg = create_message(
                message_type=MessageType.ERROR,
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                payload={"error": str(e)}
            )
            self.message_queue.send_message(error_msg)
    
    def handle_data_response(self, message: Message) -> None:
        """Handle data response message"""
        try:
            data = message.payload.get("data", {})
            self._process_received_data(data)
        except Exception as e:
            self.logger.error(f"Error handling data response: {e}")
    
    def handle_validation_request(self, message: Message) -> None:
        """Handle validation request message"""
        try:
            data = message.payload.get("data", {})
            validation_result = self.validate_data(data)
            
            response_msg = create_message(
                message_type=MessageType.VALIDATION_RESPONSE,
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                payload={
                    "validation_result": validation_result,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            self.message_queue.send_message(response_msg)
            
        except Exception as e:
            self.logger.error(f"Error handling validation request: {e}")
    
    def handle_validation_response(self, message: Message) -> None:
        """Handle validation response message"""
        try:
            validation_result = message.payload.get("validation_result", {})
            self._process_validation_result(validation_result)
        except Exception as e:
            self.logger.error(f"Error handling validation response: {e}")
    
    def handle_anomaly_alert(self, message: Message) -> None:
        """Handle anomaly alert message"""
        try:
            anomaly_data = message.payload.get("anomaly_data", {})
            self._process_anomaly_alert(anomaly_data)
            self.metrics.anomalies_detected += 1
        except Exception as e:
            self.logger.error(f"Error handling anomaly alert: {e}")
    
    def handle_human_feedback(self, message: Message) -> None:
        """Handle human feedback message"""
        try:
            feedback_data = message.payload.get("feedback", {})
            self._process_human_feedback(feedback_data)
            self.metrics.learning_iterations += 1
        except Exception as e:
            self.logger.error(f"Error handling human feedback: {e}")
    
    def handle_workflow_update(self, message: Message) -> None:
        """Handle workflow update message"""
        try:
            workflow_data = message.payload.get("workflow", {})
            self._update_workflow_state(workflow_data)
        except Exception as e:
            self.logger.error(f"Error handling workflow update: {e}")
    
    def handle_quality_review(self, message: Message) -> None:
        """Handle quality review message"""
        try:
            review_data = message.payload.get("review", {})
            self._process_quality_review(review_data)
        except Exception as e:
            self.logger.error(f"Error handling quality review: {e}")
    
    def handle_learning_update(self, message: Message) -> None:
        """Handle learning update message"""
        try:
            learning_data = message.payload.get("learning", {})
            self._process_learning_update(learning_data)
        except Exception as e:
            self.logger.error(f"Error handling learning update: {e}")
    
    def handle_system_notification(self, message: Message) -> None:
        """Handle system notification message"""
        try:
            notification_data = message.payload.get("notification", {})
            self._process_system_notification(notification_data)
        except Exception as e:
            self.logger.error(f"Error handling system notification: {e}")
    
    def handle_error_message(self, message: Message) -> None:
        """Handle error message"""
        try:
            error_data = message.payload.get("error", {})
            self._process_error_message(error_data)
        except Exception as e:
            self.logger.error(f"Error handling error message: {e}")
    
    def handle_heartbeat(self, message: Message) -> None:
        """Handle heartbeat message"""
        try:
            # Process heartbeat if needed
            pass
        except Exception as e:
            self.logger.error(f"Error handling heartbeat: {e}")
    
    # Helper methods for subclasses
    def _get_requested_data(self, data_type: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get requested data - to be overridden by subclasses"""
        return {"data_type": data_type, "status": "not_implemented"}
    
    def _process_received_data(self, data: Dict[str, Any]) -> None:
        """Process received data - to be overridden by subclasses"""
        pass
    
    def _process_validation_result(self, validation_result: Dict[str, Any]) -> None:
        """Process validation result - to be overridden by subclasses"""
        pass
    
    def _process_anomaly_alert(self, anomaly_data: Dict[str, Any]) -> None:
        """Process anomaly alert - to be overridden by subclasses"""
        pass
    
    def _process_human_feedback(self, feedback_data: Dict[str, Any]) -> None:
        """Process human feedback - to be overridden by subclasses"""
        pass
    
    def _update_workflow_state(self, workflow_data: Dict[str, Any]) -> None:
        """Update workflow state - to be overridden by subclasses"""
        pass
    
    def _process_quality_review(self, review_data: Dict[str, Any]) -> None:
        """Process quality review - to be overridden by subclasses"""
        pass
    
    def _process_learning_update(self, learning_data: Dict[str, Any]) -> None:
        """Process learning update - to be overridden by subclasses"""
        pass
    
    def _process_system_notification(self, notification_data: Dict[str, Any]) -> None:
        """Process system notification - to be overridden by subclasses"""
        pass
    
    def _process_error_message(self, error_data: Dict[str, Any]) -> None:
        """Process error message - to be overridden by subclasses"""
        pass
    
    # Public methods for external interaction
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "average_processing_time": self.metrics.average_processing_time,
                "anomalies_detected": self.metrics.anomalies_detected,
                "learning_iterations": self.metrics.learning_iterations
            },
            "queue_status": self.message_queue.get_queue_status(self.agent_id),
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "autonomous": self.autonomous,
            "decision_threshold": self.decision_threshold
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update agent configuration"""
        self.config.update(new_config)
        self.decision_threshold = new_config.get("confidence_threshold", self.decision_threshold)
        self.logger.info(f"Configuration updated: {new_config}")
    
    def add_collaboration_partner(self, partner_id: str) -> None:
        """Add a collaboration partner"""
        if partner_id not in self.collaboration_partners:
            self.collaboration_partners.append(partner_id)
            self.logger.info(f"Added collaboration partner: {partner_id}")
    
    def remove_collaboration_partner(self, partner_id: str) -> None:
        """Remove a collaboration partner"""
        if partner_id in self.collaboration_partners:
            self.collaboration_partners.remove(partner_id)
            self.logger.info(f"Removed collaboration partner: {partner_id}")
    
    def set_escalation_path(self, escalation_path: List[str]) -> None:
        """Set escalation path for this agent"""
        self.escalation_path = escalation_path
        self.logger.info(f"Escalation path set: {escalation_path}")
    
    def escalate_issue(self, issue_data: Dict[str, Any]) -> None:
        """Escalate an issue to the next level"""
        if self.escalation_path:
            next_level = self.escalation_path[0]
            escalation_msg = create_message(
                message_type=MessageType.ERROR,
                sender_id=self.agent_id,
                recipient_id=next_level,
                payload={
                    "escalation_type": "agent_issue",
                    "issue_data": issue_data,
                    "escalated_from": self.agent_id,
                    "timestamp": datetime.now().isoformat()
                },
                priority=MessagePriority.HIGH
            )
            
            self.message_queue.send_message(escalation_msg)
            self.logger.info(f"Issue escalated to: {next_level}")
        else:
            self.logger.warning("No escalation path configured")
    
    def learn_from_feedback(self, feedback_data: Dict[str, Any]) -> None:
        """Learn from feedback data"""
        self.learning_data.append({
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback_data,
            "agent_state": self.get_status()
        })
        
        # Keep only last 1000 learning records
        if len(self.learning_data) > 1000:
            self.learning_data.pop(0)
        
        self.metrics.learning_iterations += 1
        self.logger.info("Learning data updated from feedback")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            "agent_info": self.get_status(),
            "performance_history": self.performance_history[-100:],  # Last 100 records
            "learning_data_summary": {
                "total_records": len(self.learning_data),
                "recent_feedback": self.learning_data[-10:] if self.learning_data else []
            },
            "collaboration_summary": {
                "partners": self.collaboration_partners,
                "escalation_path": self.escalation_path
            }
        }