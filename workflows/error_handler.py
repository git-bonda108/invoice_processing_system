"""
Error Handler - Comprehensive error handling and recovery system
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import traceback
import time
from collections import defaultdict

class ErrorType(Enum):
    """Error classification types"""
    TRANSIENT = "transient"          # Temporary failures (network, resource)
    PERMANENT = "permanent"          # Data format or validation failures
    SYSTEM = "system"               # Infrastructure or configuration issues
    BUSINESS = "business"           # Business rule violations
    TIMEOUT = "timeout"             # Processing timeout errors
    RESOURCE = "resource"           # Resource exhaustion errors
    UNKNOWN = "unknown"             # Unclassified errors

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RecoveryAction(Enum):
    """Recovery action types"""
    RETRY = "retry"
    ESCALATE = "escalate"
    SKIP = "skip"
    ABORT = "abort"
    FALLBACK = "fallback"
    MANUAL = "manual"

@dataclass
class RetryPolicy:
    """Retry policy configuration"""
    max_retries: int
    initial_delay: float
    max_delay: float
    backoff_multiplier: float
    jitter: bool = True

@dataclass
class ErrorContext:
    """Error context information"""
    workflow_id: Optional[str]
    task_id: Optional[str]
    agent_id: Optional[str]
    document_path: Optional[str]
    stage: Optional[str]
    timestamp: datetime
    additional_data: Dict[str, Any]

@dataclass
class ErrorRecord:
    """Complete error record"""
    error_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    exception: Exception
    context: ErrorContext
    recovery_action: RecoveryAction
    retry_count: int
    resolved: bool
    resolution_time: Optional[datetime]
    resolution_method: Optional[str]

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self.logger = logging.getLogger("CircuitBreaker")
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
                self.logger.info("Circuit breaker transitioning to half-open")
            else:
                raise Exception("Circuit breaker is open - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True
        
        return (datetime.now() - self.last_failure_time).total_seconds() > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0
        if self.state == "half-open":
            self.state = "closed"
            self.logger.info("Circuit breaker reset to closed")
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

class ErrorHandler:
    """Comprehensive error handling and recovery system"""
    
    def __init__(self, manager_agent=None):
        self.manager_agent = manager_agent
        self.logger = logging.getLogger("ErrorHandler")
        
        # Error tracking
        self.error_records: Dict[str, ErrorRecord] = {}
        self.error_statistics = defaultdict(int)
        self.recovery_statistics = defaultdict(int)
        
        # Circuit breakers for different services
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Retry policies by error type
        self.retry_policies = {
            ErrorType.TRANSIENT: RetryPolicy(
                max_retries=3,
                initial_delay=1.0,
                max_delay=30.0,
                backoff_multiplier=2.0
            ),
            ErrorType.SYSTEM: RetryPolicy(
                max_retries=2,
                initial_delay=5.0,
                max_delay=60.0,
                backoff_multiplier=2.0
            ),
            ErrorType.TIMEOUT: RetryPolicy(
                max_retries=2,
                initial_delay=2.0,
                max_delay=20.0,
                backoff_multiplier=1.5
            ),
            ErrorType.RESOURCE: RetryPolicy(
                max_retries=3,
                initial_delay=10.0,
                max_delay=120.0,
                backoff_multiplier=2.0
            ),
            ErrorType.PERMANENT: RetryPolicy(
                max_retries=0,
                initial_delay=0.0,
                max_delay=0.0,
                backoff_multiplier=1.0
            ),
            ErrorType.BUSINESS: RetryPolicy(
                max_retries=0,
                initial_delay=0.0,
                max_delay=0.0,
                backoff_multiplier=1.0
            )
        }
        
        # Recovery strategies
        self.recovery_strategies = {
            ErrorType.TRANSIENT: self._handle_transient_error,
            ErrorType.SYSTEM: self._handle_system_error,
            ErrorType.PERMANENT: self._handle_permanent_error,
            ErrorType.BUSINESS: self._handle_business_error,
            ErrorType.TIMEOUT: self._handle_timeout_error,
            ErrorType.RESOURCE: self._handle_resource_error,
            ErrorType.UNKNOWN: self._handle_unknown_error
        }
        
        # Escalation rules
        self.escalation_rules = {
            'high_error_rate': {
                'threshold': 0.2,  # 20% error rate
                'window_minutes': 10,
                'action': 'alert_admin'
            },
            'critical_errors': {
                'threshold': 1,  # Any critical error
                'window_minutes': 1,
                'action': 'immediate_alert'
            },
            'system_errors': {
                'threshold': 3,  # 3 system errors
                'window_minutes': 5,
                'action': 'escalate_to_ops'
            }
        }
        
        self.logger.info("Error Handler initialized")
    
    async def handle_error(self, exception: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Main error handling entry point"""
        try:
            # Generate error ID
            error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.error_records)}"
            
            # Classify error
            error_type = self._classify_error(exception)
            severity = self._determine_severity(exception, error_type, context)
            
            # Determine recovery action
            recovery_action = self._determine_recovery_action(error_type, severity, context)
            
            # Create error record
            error_record = ErrorRecord(
                error_id=error_id,
                error_type=error_type,
                severity=severity,
                exception=exception,
                context=context,
                recovery_action=recovery_action,
                retry_count=0,
                resolved=False,
                resolution_time=None,
                resolution_method=None
            )
            
            # Store error record
            self.error_records[error_id] = error_record
            
            # Update statistics
            self.error_statistics[error_type.value] += 1
            self.error_statistics[f"{severity.value}_severity"] += 1
            
            # Log error
            self._log_error(error_record)
            
            # Execute recovery strategy
            recovery_result = await self._execute_recovery_strategy(error_record)
            
            # Check escalation conditions
            await self._check_escalation_conditions(error_record)
            
            return {
                'error_id': error_id,
                'error_type': error_type.value,
                'severity': severity.value,
                'recovery_action': recovery_action.value,
                'recovery_result': recovery_result,
                'message': str(exception)
            }
            
        except Exception as e:
            self.logger.critical(f"Error handler itself failed: {e}")
            return {
                'error_id': 'HANDLER_FAILURE',
                'error_type': ErrorType.SYSTEM.value,
                'severity': ErrorSeverity.CRITICAL.value,
                'recovery_action': RecoveryAction.ESCALATE.value,
                'message': f'Error handler failure: {str(e)}'
            }
    
    def _classify_error(self, exception: Exception) -> ErrorType:
        """Classify error type based on exception"""
        exception_type = type(exception).__name__
        exception_message = str(exception).lower()
        
        # Network and connection errors
        if any(keyword in exception_type.lower() for keyword in 
               ['connection', 'network', 'socket', 'timeout']):
            return ErrorType.TRANSIENT
        
        # Timeout errors
        if 'timeout' in exception_message or isinstance(exception, asyncio.TimeoutError):
            return ErrorType.TIMEOUT
        
        # Resource errors
        if any(keyword in exception_message for keyword in 
               ['memory', 'disk', 'resource', 'limit', 'quota']):
            return ErrorType.RESOURCE
        
        # Data validation errors
        if any(keyword in exception_type.lower() for keyword in 
               ['value', 'type', 'key', 'attribute', 'validation']):
            return ErrorType.PERMANENT
        
        # System errors
        if any(keyword in exception_type.lower() for keyword in 
               ['system', 'os', 'io', 'permission', 'access']):
            return ErrorType.SYSTEM
        
        # Business logic errors
        if any(keyword in exception_message for keyword in 
               ['business', 'rule', 'policy', 'validation']):
            return ErrorType.BUSINESS
        
        return ErrorType.UNKNOWN
    
    def _determine_severity(self, exception: Exception, error_type: ErrorType, 
                           context: ErrorContext) -> ErrorSeverity:
        """Determine error severity"""
        # Critical severity conditions
        if error_type == ErrorType.SYSTEM and 'critical' in str(exception).lower():
            return ErrorSeverity.CRITICAL
        
        if context.workflow_id and 'critical' in context.additional_data.get('priority', ''):
            return ErrorSeverity.CRITICAL
        
        # High severity conditions
        if error_type in [ErrorType.SYSTEM, ErrorType.RESOURCE]:
            return ErrorSeverity.HIGH
        
        if error_type == ErrorType.BUSINESS and 'compliance' in str(exception).lower():
            return ErrorSeverity.HIGH
        
        # Medium severity conditions
        if error_type in [ErrorType.TIMEOUT, ErrorType.BUSINESS]:
            return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    def _determine_recovery_action(self, error_type: ErrorType, severity: ErrorSeverity, 
                                  context: ErrorContext) -> RecoveryAction:
        """Determine appropriate recovery action"""
        # Critical errors always escalate
        if severity == ErrorSeverity.CRITICAL:
            return RecoveryAction.ESCALATE
        
        # Permanent errors cannot be retried
        if error_type in [ErrorType.PERMANENT, ErrorType.BUSINESS]:
            if severity == ErrorSeverity.HIGH:
                return RecoveryAction.ESCALATE
            else:
                return RecoveryAction.SKIP
        
        # System errors with high severity escalate
        if error_type == ErrorType.SYSTEM and severity == ErrorSeverity.HIGH:
            return RecoveryAction.ESCALATE
        
        # Transient and timeout errors can be retried
        if error_type in [ErrorType.TRANSIENT, ErrorType.TIMEOUT, ErrorType.RESOURCE]:
            return RecoveryAction.RETRY
        
        # Unknown errors get manual review
        if error_type == ErrorType.UNKNOWN:
            return RecoveryAction.MANUAL
        
        return RecoveryAction.RETRY
    
    async def _execute_recovery_strategy(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Execute recovery strategy based on error type"""
        strategy = self.recovery_strategies.get(error_record.error_type)
        if not strategy:
            return await self._handle_unknown_error(error_record)
        
        try:
            result = await strategy(error_record)
            
            # Update recovery statistics
            self.recovery_statistics[error_record.recovery_action.value] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Recovery strategy failed for {error_record.error_id}: {e}")
            return {
                'success': False,
                'action': 'recovery_failed',
                'message': str(e)
            }
    
    async def _handle_transient_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle transient errors with retry logic"""
        policy = self.retry_policies[ErrorType.TRANSIENT]
        
        if error_record.retry_count >= policy.max_retries:
            return {
                'success': False,
                'action': 'max_retries_exceeded',
                'message': f'Max retries ({policy.max_retries}) exceeded'
            }
        
        # Calculate delay with exponential backoff
        delay = min(
            policy.initial_delay * (policy.backoff_multiplier ** error_record.retry_count),
            policy.max_delay
        )
        
        # Add jitter if enabled
        if policy.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
        
        self.logger.info(f"Retrying {error_record.error_id} after {delay:.2f}s (attempt {error_record.retry_count + 1})")
        
        # Wait before retry
        await asyncio.sleep(delay)
        
        error_record.retry_count += 1
        
        return {
            'success': True,
            'action': 'retry_scheduled',
            'delay': delay,
            'attempt': error_record.retry_count
        }
    
    async def _handle_system_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle system errors"""
        # Check if circuit breaker should be activated
        service_name = error_record.context.agent_id or 'unknown_service'
        
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        
        circuit_breaker = self.circuit_breakers[service_name]
        circuit_breaker._on_failure()  # Register failure
        
        # Attempt retry if within limits
        policy = self.retry_policies[ErrorType.SYSTEM]
        
        if error_record.retry_count < policy.max_retries:
            delay = policy.initial_delay * (policy.backoff_multiplier ** error_record.retry_count)
            await asyncio.sleep(delay)
            error_record.retry_count += 1
            
            return {
                'success': True,
                'action': 'retry_with_circuit_breaker',
                'delay': delay,
                'circuit_breaker_state': circuit_breaker.state
            }
        else:
            return {
                'success': False,
                'action': 'escalate_system_error',
                'message': 'System error requires manual intervention'
            }
    
    async def _handle_permanent_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle permanent errors (no retry)"""
        # Log for analysis
        self.logger.warning(f"Permanent error {error_record.error_id}: {error_record.exception}")
        
        # Mark as resolved (cannot be fixed automatically)
        error_record.resolved = True
        error_record.resolution_time = datetime.now()
        error_record.resolution_method = "skipped_permanent_error"
        
        return {
            'success': True,
            'action': 'skip_permanent_error',
            'message': 'Permanent error skipped - requires data correction'
        }
    
    async def _handle_business_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle business rule violations"""
        # Business errors typically require human review
        return {
            'success': False,
            'action': 'require_human_review',
            'message': 'Business rule violation requires human review'
        }
    
    async def _handle_timeout_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle timeout errors"""
        policy = self.retry_policies[ErrorType.TIMEOUT]
        
        if error_record.retry_count < policy.max_retries:
            # Increase timeout for retry
            delay = policy.initial_delay * (policy.backoff_multiplier ** error_record.retry_count)
            await asyncio.sleep(delay)
            error_record.retry_count += 1
            
            return {
                'success': True,
                'action': 'retry_with_extended_timeout',
                'delay': delay,
                'suggested_timeout_multiplier': 1.5
            }
        else:
            return {
                'success': False,
                'action': 'timeout_exceeded',
                'message': 'Task consistently timing out - may require optimization'
            }
    
    async def _handle_resource_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle resource exhaustion errors"""
        # Wait longer for resources to become available
        policy = self.retry_policies[ErrorType.RESOURCE]
        
        if error_record.retry_count < policy.max_retries:
            delay = policy.initial_delay * (policy.backoff_multiplier ** error_record.retry_count)
            await asyncio.sleep(delay)
            error_record.retry_count += 1
            
            return {
                'success': True,
                'action': 'retry_after_resource_wait',
                'delay': delay,
                'message': 'Waiting for resources to become available'
            }
        else:
            return {
                'success': False,
                'action': 'resource_exhaustion',
                'message': 'Persistent resource exhaustion - system scaling may be required'
            }
    
    async def _handle_unknown_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle unknown/unclassified errors"""
        # Conservative approach - single retry then escalate
        if error_record.retry_count == 0:
            await asyncio.sleep(5)  # Short delay
            error_record.retry_count += 1
            
            return {
                'success': True,
                'action': 'single_retry_unknown',
                'message': 'Unknown error - attempting single retry'
            }
        else:
            return {
                'success': False,
                'action': 'escalate_unknown_error',
                'message': 'Unknown error type requires investigation'
            }
    
    async def _check_escalation_conditions(self, error_record: ErrorRecord):
        """Check if error conditions warrant escalation"""
        current_time = datetime.now()
        
        for rule_name, rule_config in self.escalation_rules.items():
            window_start = current_time - timedelta(minutes=rule_config['window_minutes'])
            
            # Get recent errors within window
            recent_errors = [
                record for record in self.error_records.values()
                if record.context.timestamp >= window_start
            ]
            
            should_escalate = False
            
            if rule_name == 'high_error_rate':
                # Calculate error rate
                total_recent = len(recent_errors)
                if total_recent > 10:  # Only check if we have enough data
                    error_rate = total_recent / 10  # Simplified calculation
                    should_escalate = error_rate > rule_config['threshold']
            
            elif rule_name == 'critical_errors':
                critical_errors = [r for r in recent_errors if r.severity == ErrorSeverity.CRITICAL]
                should_escalate = len(critical_errors) >= rule_config['threshold']
            
            elif rule_name == 'system_errors':
                system_errors = [r for r in recent_errors if r.error_type == ErrorType.SYSTEM]
                should_escalate = len(system_errors) >= rule_config['threshold']
            
            if should_escalate:
                await self._escalate_error(rule_name, rule_config, recent_errors)
    
    async def _escalate_error(self, rule_name: str, rule_config: Dict[str, Any], 
                             recent_errors: List[ErrorRecord]):
        """Escalate error condition"""
        escalation_message = f"Escalation triggered by rule '{rule_name}': {len(recent_errors)} recent errors"
        
        self.logger.critical(escalation_message)
        
        # In a real implementation, this would:
        # - Send alerts to administrators
        # - Create tickets in issue tracking system
        # - Trigger automated remediation procedures
        # - Update monitoring dashboards
        
        # For now, just log the escalation
        escalation_data = {
            'rule': rule_name,
            'action': rule_config['action'],
            'error_count': len(recent_errors),
            'error_types': [r.error_type.value for r in recent_errors],
            'severity_levels': [r.severity.value for r in recent_errors]
        }
        
        self.logger.critical(f"ESCALATION: {json.dumps(escalation_data, indent=2)}")
    
    def _log_error(self, error_record: ErrorRecord):
        """Log error with appropriate level"""
        log_message = (
            f"Error {error_record.error_id}: {error_record.error_type.value} "
            f"({error_record.severity.value}) - {error_record.exception}"
        )
        
        if error_record.context.workflow_id:
            log_message += f" [Workflow: {error_record.context.workflow_id}]"
        
        if error_record.context.task_id:
            log_message += f" [Task: {error_record.context.task_id}]"
        
        # Log with appropriate level based on severity
        if error_record.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_record.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_record.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics"""
        total_errors = len(self.error_records)
        resolved_errors = sum(1 for record in self.error_records.values() if record.resolved)
        
        return {
            'total_errors': total_errors,
            'resolved_errors': resolved_errors,
            'resolution_rate': (resolved_errors / total_errors * 100) if total_errors > 0 else 0,
            'error_types': dict(self.error_statistics),
            'recovery_actions': dict(self.recovery_statistics),
            'circuit_breaker_states': {
                name: breaker.state for name, breaker in self.circuit_breakers.items()
            }
        }
    
    def get_recent_errors(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent errors within specified time window"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_errors = [
            asdict(record) for record in self.error_records.values()
            if record.context.timestamp >= cutoff_time
        ]
        
        # Convert datetime objects to strings for JSON serialization
        for error in recent_errors:
            error['context']['timestamp'] = error['context']['timestamp'].isoformat()
            if error['resolution_time']:
                error['resolution_time'] = error['resolution_time'].isoformat()
        
        return recent_errors