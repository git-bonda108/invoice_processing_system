"""
Enhanced Message Queue System for Multi-Agent Communication
NO SLICE OPERATIONS - COMPLETELY SAFE
"""
import json
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Set
from uuid import uuid4

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Message types for agent communication"""
    TASK_ASSIGNMENT = "task_assignment"
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"
    VALIDATION_REQUEST = "validation_request"
    VALIDATION_RESPONSE = "validation_response"
    ANOMALY_ALERT = "anomaly_alert"
    HUMAN_FEEDBACK = "human_feedback"
    WORKFLOW_UPDATE = "workflow_update"
    QUALITY_REVIEW = "quality_review"
    LEARNING_UPDATE = "learning_update"
    SYSTEM_NOTIFICATION = "system_notification"
    ERROR = "error"
    HEARTBEAT = "heartbeat"

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class MessageStatus(Enum):
    """Message processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

@dataclass
class Message:
    """Message structure for agent communication"""
    message_id: str = field(default_factory=lambda: str(uuid4()))
    message_type: MessageType = MessageType.SYSTEM_NOTIFICATION
    priority: MessagePriority = MessagePriority.NORMAL
    sender_id: str = ""
    recipient_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: int = 3600  # Time to live in seconds
    status: MessageStatus = MessageStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if message has expired"""
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl)
    
    def can_retry(self) -> bool:
        """Check if message can be retried"""
        return self.retry_count < self.max_retries and not self.is_expired()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "payload": self.payload,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            message_id=data.get("message_id", str(uuid4())),
            message_type=MessageType(data.get("message_type", "system_notification")),
            priority=MessagePriority(data.get("priority", 2)),
            sender_id=data.get("sender_id", ""),
            recipient_id=data.get("recipient_id", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            ttl=data.get("ttl", 3600),
            status=MessageStatus(data.get("status", "pending")),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {})
        )

class MessageQueue:
    """Enhanced message queue for multi-agent communication"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_size))
        self.global_queue: deque = deque(maxlen=max_size)
        self.message_history: List[Message] = []
        self.subscribers: Dict[str, Set[Callable]] = defaultdict(set)
        self.processing_messages: Set[str] = set()
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_processed": 0,
            "messages_failed": 0,
            "messages_expired": 0,
            "queues_created": 0
        }
        
        # Threading
        self.lock = threading.RLock()
        self.cleanup_thread = None
        self.running = False
        
        # Start cleanup thread
        self.start_cleanup_thread()
    
    def create_queue(self, queue_id: str) -> None:
        """Create a new message queue"""
        with self.lock:
            if queue_id not in self.queues:
                self.queues[queue_id] = deque(maxlen=self.max_size)
                self.stats["queues_created"] += 1
    
    def subscribe(self, queue_id: str, callback: Callable) -> None:
        """Subscribe to a queue for notifications"""
        with self.lock:
            self.subscribers[queue_id].add(callback)
    
    def unsubscribe(self, queue_id: str, callback: Callable) -> None:
        """Unsubscribe from a queue"""
        with self.lock:
            if queue_id in self.subscribers:
                self.subscribers[queue_id].discard(callback)
    
    def send_message(self, message: Message) -> bool:
        """Send a message to the appropriate queue"""
        try:
            with self.lock:
                # Add to global queue
                self.global_queue.append(message)
                
                # Add to recipient queue if specified
                if message.recipient_id:
                    self.queues[message.recipient_id].append(message)
                
                # Add to sender queue for tracking
                if message.sender_id:
                    self.queues[message.sender_id].append(message)
                
                self.stats["messages_sent"] += 1
                
                # Notify subscribers
                self._notify_subscribers(message)
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.stats["messages_failed"] += 1
            return False
    
    def receive_message(self, queue_id: str, timeout: float = 1.0) -> Optional[Message]:
        """Receive a message from a specific queue"""
        try:
            with self.lock:
                queue = self.queues[queue_id]
                
                if not queue:
                    return None
                
                # Get highest priority message
                message = self._get_highest_priority_message(queue)
                if message:
                    self.processing_messages.add(message.message_id)
                    self.stats["messages_received"] += 1
                    return message
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to receive message from {queue_id}: {e}")
            return None
    
    def mark_message_completed(self, message_id: str) -> None:
        """Mark a message as completed"""
        with self.lock:
            if message_id in self.processing_messages:
                self.processing_messages.discard(message_id)
                self.stats["messages_processed"] += 1
    
    def mark_message_failed(self, message_id: str, error: str) -> None:
        """Mark a message as failed"""
        with self.lock:
            if message_id in self.processing_messages:
                self.processing_messages.discard(message_id)
                
                # Update message status
                for queue in self.queues.values():
                    for msg in queue:
                        if msg.message_id == message_id:
                            msg.status = MessageStatus.FAILED
                            msg.metadata["error"] = error
                            break
                
                self.stats["messages_failed"] += 1
    
    def get_queue_status(self, queue_id: str) -> Dict[str, Any]:
        """Get status of a specific queue"""
        with self.lock:
            if queue_id not in self.queues:
                return {"error": "Queue not found"}
            
            queue = self.queues[queue_id]
            return {
                "queue_id": queue_id,
                "total_messages": len(queue),
                "pending": len([m for m in queue if m.status == MessageStatus.PENDING]),
                "processing": len([m for m in queue if m.status == MessageStatus.PROCESSING]),
                "completed": len([m for m in queue if m.status == MessageStatus.COMPLETED]),
                "failed": len([m for m in queue if m.status == MessageStatus.FAILED])
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        with self.lock:
            return {
                "total_queues": len(self.queues),
                "global_queue_size": len(self.global_queue),
                "total_history": len(self.message_history),
                "processing_messages": len(self.processing_messages),
                "stats": self.stats.copy()
            }
    
    def _get_highest_priority_message(self, queue: deque) -> Optional[Message]:
        """Get the highest priority message from a queue"""
        try:
            # Get pending messages that haven't expired
            pending_messages = [msg for msg in queue if msg.status == MessageStatus.PENDING and not msg.is_expired()]
            
            if not pending_messages:
                return None
            
            # Sort by priority (highest first) and timestamp (oldest first)
            sorted_messages = sorted(pending_messages, key=lambda x: (x.priority.value, x.timestamp))
            return sorted_messages[0] if sorted_messages else None
            
        except Exception as e:
            logger.error(f"Error getting highest priority message: {e}")
            return None
    
    def _notify_subscribers(self, message: Message) -> None:
        """Notify subscribers about a new message"""
        try:
            # Notify both sender and recipient subscribers
            for queue_id in [message.sender_id, message.recipient_id]:
                if queue_id and queue_id in self.subscribers:
                    for callback in self.subscribers[queue_id]:
                        try:
                            callback(message)
                        except Exception as e:
                            logger.error(f"Error in subscriber callback: {e}")
        except Exception as e:
            logger.error(f"Error notifying subscribers: {e}")
    
    def _cleanup_expired_messages(self) -> None:
        """Clean up expired messages periodically - NO SLICE OPERATIONS"""
        while True:
            try:
                time.sleep(60)  # Check every minute
                
                with self.lock:
                    expired_count = 0
                    
                    # Clean up expired messages from all queues - SAFE OPERATIONS ONLY
                    for queue_id, queue in self.queues.items():
                        try:
                            original_size = len(queue)
                            # Create new list without expired messages
                            valid_messages = [msg for msg in queue if not msg.is_expired()]
                            # Clear and repopulate safely
                            queue.clear()
                            for msg in valid_messages:
                                queue.append(msg)
                            expired_count += original_size - len(queue)
                        except Exception as queue_error:
                            logger.warning(f"Error cleaning queue {queue_id}: {queue_error}")
                            continue
                    
                    # Clean up expired messages from global queue - SAFE OPERATIONS ONLY
                    try:
                        original_size = len(self.global_queue)
                        # Remove expired messages one by one
                        expired_messages = [msg for msg in self.global_queue if msg.is_expired()]
                        for msg in expired_messages:
                            try:
                                self.global_queue.remove(msg)
                            except ValueError:
                                pass  # Message already removed
                        expired_count += len(expired_messages)
                    except Exception as global_error:
                        logger.warning(f"Error cleaning global queue: {global_error}")
                    
                    # Clean up expired messages from history - SAFE OPERATIONS ONLY
                    try:
                        original_size = len(self.message_history)
                        # Create new history without expired messages
                        self.message_history = [msg for msg in self.message_history if not msg.is_expired()]
                        expired_count += original_size - len(self.message_history)
                    except Exception as history_error:
                        logger.warning(f"Error cleaning history: {history_error}")
                    
                    if expired_count > 0:
                        self.stats["messages_expired"] += expired_count
                        logger.info(f"Cleaned up {expired_count} expired messages")
                        
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")
                time.sleep(10)  # Wait before retrying
    
    def start_cleanup_thread(self) -> None:
        """Start the cleanup thread"""
        if not self.running:
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_expired_messages, daemon=True)
            self.cleanup_thread.start()
    
    def stop_cleanup_thread(self) -> None:
        """Stop the cleanup thread"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)

# Global message queue instance
message_queue = MessageQueue()

# Utility functions for creating common message types
def create_message(
    message_type: MessageType,
    sender_id: str,
    recipient_id: str = "",
    payload: Dict[str, Any] = None,
    priority: MessagePriority = MessagePriority.NORMAL,
    ttl: int = 3600
) -> Message:
    """Create a new message with common parameters"""
    return Message(
        message_type=message_type,
        sender_id=sender_id,
        recipient_id=recipient_id,
        payload=payload or {},
        priority=priority,
        ttl=ttl
    )

def create_task_assignment(
    sender_id: str,
    recipient_id: str,
    task_type: str,
    task_data: Dict[str, Any],
    priority: MessagePriority = MessagePriority.HIGH
) -> Message:
    """Create a task assignment message"""
    return create_message(
        message_type=MessageType.TASK_ASSIGNMENT,
        sender_id=sender_id,
        recipient_id=recipient_id,
        payload={
            "task_type": task_type,
            "task_data": task_data,
            "assigned_at": datetime.now().isoformat()
        },
        priority=priority
    )

def create_data_request(
    sender_id: str,
    recipient_id: str,
    data_type: str,
    query_params: Dict[str, Any],
    priority: MessagePriority = MessagePriority.NORMAL
) -> Message:
    """Create a data request message"""
    return create_message(
        message_type=MessageType.DATA_REQUEST,
        sender_id=sender_id,
        recipient_id=recipient_id,
        payload={
            "data_type": data_type,
            "query_params": query_params,
            "requested_at": datetime.now().isoformat()
        },
        priority=priority
    )

def create_anomaly_alert(
    sender_id: str,
    recipient_id: str,
    anomaly_type: str,
    anomaly_data: Dict[str, Any],
    severity: str = "medium",
    priority: MessagePriority = MessagePriority.HIGH
) -> Message:
    """Create an anomaly alert message"""
    return create_message(
        message_type=MessageType.ANOMALY_ALERT,
        sender_id=sender_id,
        recipient_id=recipient_id,
        payload={
            "anomaly_type": anomaly_type,
            "anomaly_data": anomaly_data,
            "severity": severity,
            "detected_at": datetime.now().isoformat()
        },
        priority=priority
    )
