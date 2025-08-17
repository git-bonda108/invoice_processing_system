"""
Status Monitor - Real-time workflow and task monitoring
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
import time

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskStatus(Enum):
    """Individual task status"""
    QUEUED = "queued"
    ASSIGNED = "assigned"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    timestamp: datetime
    active_workflows: int
    active_tasks: int
    completed_workflows: int
    failed_workflows: int
    average_processing_time: float
    throughput_per_hour: float
    memory_usage: float
    cpu_usage: float
    queue_size: int

@dataclass
class Alert:
    """System alert"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    acknowledged: bool = False
    resolved: bool = False

@dataclass
class TaskMetrics:
    """Individual task metrics"""
    task_id: str
    workflow_id: str
    status: TaskStatus
    agent_type: str
    document_type: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_time: Optional[float]
    confidence_score: Optional[float]
    anomaly_count: int
    retry_count: int

class StatusMonitor:
    """Real-time status monitoring and reporting system"""
    
    def __init__(self, max_history_size: int = 1000):
        self.logger = logging.getLogger("StatusMonitor")
        
        # Current status tracking
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.active_tasks: Dict[str, TaskMetrics] = {}
        self.completed_workflows: Dict[str, Dict[str, Any]] = {}
        self.failed_workflows: Dict[str, Dict[str, Any]] = {}
        
        # Performance metrics history
        self.max_history_size = max_history_size
        self.metrics_history: deque = deque(maxlen=max_history_size)
        self.task_metrics_history: deque = deque(maxlen=max_history_size)
        
        # Alerts system
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=max_history_size)
        
        # Configuration
        self.config = {
            'metrics_collection_interval': 30,  # seconds
            'alert_thresholds': {
                'max_processing_time': 300,  # 5 minutes
                'max_queue_size': 100,
                'max_failure_rate': 0.1,  # 10%
                'max_memory_usage': 0.8,  # 80%
                'max_cpu_usage': 0.9  # 90%
            },
            'enable_auto_alerts': True,
            'enable_performance_tracking': True
        }
        
        # Statistics
        self.statistics = {
            'total_workflows_processed': 0,
            'total_tasks_processed': 0,
            'total_processing_time': 0.0,
            'average_workflow_time': 0.0,
            'average_task_time': 0.0,
            'success_rate': 0.0,
            'uptime_start': datetime.now()
        }
        
        # Start monitoring thread
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("Status Monitor initialized")
    
    def register_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]):
        """Register a new workflow for monitoring"""
        workflow_info = {
            'workflow_id': workflow_id,
            'status': WorkflowStatus.PENDING,
            'created_at': datetime.now(),
            'started_at': None,
            'completed_at': None,
            'total_tasks': workflow_data.get('total_tasks', 0),
            'completed_tasks': 0,
            'failed_tasks': 0,
            'current_stage': 'initialization',
            'progress': 0.0,
            'processing_time': 0.0,
            'metadata': workflow_data
        }
        
        self.active_workflows[workflow_id] = workflow_info
        self.logger.info(f"Registered workflow {workflow_id} for monitoring")
    
    def update_workflow_status(self, workflow_id: str, status: WorkflowStatus, 
                              stage: str = None, progress: float = None):
        """Update workflow status"""
        if workflow_id not in self.active_workflows:
            self.logger.warning(f"Workflow {workflow_id} not found for status update")
            return
        
        workflow = self.active_workflows[workflow_id]
        old_status = workflow['status']
        workflow['status'] = status
        
        if stage:
            workflow['current_stage'] = stage
        
        if progress is not None:
            workflow['progress'] = progress
        
        # Handle status transitions
        if old_status == WorkflowStatus.PENDING and status == WorkflowStatus.RUNNING:
            workflow['started_at'] = datetime.now()
        elif status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            workflow['completed_at'] = datetime.now()
            if workflow['started_at']:
                workflow['processing_time'] = (
                    workflow['completed_at'] - workflow['started_at']
                ).total_seconds()
            
            # Move to appropriate completed list
            if status == WorkflowStatus.COMPLETED:
                self.completed_workflows[workflow_id] = workflow
                self.statistics['total_workflows_processed'] += 1
            elif status == WorkflowStatus.FAILED:
                self.failed_workflows[workflow_id] = workflow
            
            # Remove from active workflows
            del self.active_workflows[workflow_id]
            
            # Update statistics
            self._update_workflow_statistics(workflow)
        
        self.logger.debug(f"Updated workflow {workflow_id} status: {old_status.value} -> {status.value}")
    
    def register_task(self, task_id: str, workflow_id: str, agent_type: str, 
                     document_type: str):
        """Register a new task for monitoring"""
        task_metrics = TaskMetrics(
            task_id=task_id,
            workflow_id=workflow_id,
            status=TaskStatus.QUEUED,
            agent_type=agent_type,
            document_type=document_type,
            started_at=None,
            completed_at=None,
            processing_time=None,
            confidence_score=None,
            anomaly_count=0,
            retry_count=0
        )
        
        self.active_tasks[task_id] = task_metrics
        self.logger.debug(f"Registered task {task_id} for monitoring")
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          result: Dict[str, Any] = None):
        """Update task status and metrics"""
        if task_id not in self.active_tasks:
            self.logger.warning(f"Task {task_id} not found for status update")
            return
        
        task = self.active_tasks[task_id]
        old_status = task.status
        task.status = status
        
        # Handle status transitions
        if old_status == TaskStatus.QUEUED and status == TaskStatus.PROCESSING:
            task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()
            if task.started_at:
                task.processing_time = (
                    task.completed_at - task.started_at
                ).total_seconds()
            
            # Extract metrics from result
            if result:
                task.confidence_score = result.get('overall_confidence')
                task.anomaly_count = len(result.get('anomalies', []))
            
            # Move to history and remove from active
            self.task_metrics_history.append(asdict(task))
            del self.active_tasks[task_id]
            
            # Update workflow task counts
            workflow_id = task.workflow_id
            if workflow_id in self.active_workflows:
                workflow = self.active_workflows[workflow_id]
                if status == TaskStatus.COMPLETED:
                    workflow['completed_tasks'] += 1
                elif status == TaskStatus.FAILED:
                    workflow['failed_tasks'] += 1
                
                # Update workflow progress
                total_tasks = workflow['total_tasks']
                if total_tasks > 0:
                    completed = workflow['completed_tasks'] + workflow['failed_tasks']
                    workflow['progress'] = (completed / total_tasks) * 100
            
            # Update statistics
            self._update_task_statistics(task)
        elif status == TaskStatus.RETRYING:
            task.retry_count += 1
        
        self.logger.debug(f"Updated task {task_id} status: {old_status.value} -> {status.value}")
    
    def create_alert(self, level: AlertLevel, title: str, message: str, 
                    source: str = "system") -> str:
        """Create a new alert"""
        alert_id = f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.active_alerts)}"
        
        alert = Alert(
            alert_id=alert_id,
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source=source
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(asdict(alert))
        
        self.logger.warning(f"Created {level.value} alert: {title}")
        return alert_id
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.logger.info(f"Alert {alert_id} acknowledged")
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.acknowledged = True
            
            # Move to history and remove from active
            del self.active_alerts[alert_id]
            
            self.logger.info(f"Alert {alert_id} resolved")
            return True
        return False
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        current_time = datetime.now()
        uptime = (current_time - self.statistics['uptime_start']).total_seconds()
        
        # Calculate current metrics
        active_workflow_count = len(self.active_workflows)
        active_task_count = len(self.active_tasks)
        completed_workflow_count = len(self.completed_workflows)
        failed_workflow_count = len(self.failed_workflows)
        
        # Calculate success rate
        total_completed = completed_workflow_count + failed_workflow_count
        success_rate = (completed_workflow_count / total_completed * 100) if total_completed > 0 else 0
        
        # Get recent performance metrics
        recent_metrics = list(self.metrics_history)[-10:] if self.metrics_history else []
        
        # Get active alerts by level
        alerts_by_level = defaultdict(int)
        for alert in self.active_alerts.values():
            alerts_by_level[alert.level.value] += 1
        
        return {
            'timestamp': current_time.isoformat(),
            'uptime_seconds': uptime,
            'system_status': self._get_system_status(),
            'workflows': {
                'active': active_workflow_count,
                'completed': completed_workflow_count,
                'failed': failed_workflow_count,
                'success_rate': success_rate
            },
            'tasks': {
                'active': active_task_count,
                'queue_size': sum(1 for task in self.active_tasks.values() 
                                if task.status == TaskStatus.QUEUED)
            },
            'performance': {
                'average_workflow_time': self.statistics['average_workflow_time'],
                'average_task_time': self.statistics['average_task_time'],
                'throughput_per_hour': self._calculate_throughput()
            },
            'alerts': {
                'total_active': len(self.active_alerts),
                'by_level': dict(alerts_by_level),
                'recent': [asdict(alert) for alert in list(self.alert_history)[-5:]]
            },
            'recent_metrics': recent_metrics
        }
    
    def get_workflow_details(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific workflow"""
        # Check active workflows
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id].copy()
            workflow['status'] = workflow['status'].value
            
            # Get associated tasks
            workflow_tasks = [
                asdict(task) for task in self.active_tasks.values()
                if task.workflow_id == workflow_id
            ]
            workflow['active_tasks'] = workflow_tasks
            
            return workflow
        
        # Check completed workflows
        elif workflow_id in self.completed_workflows:
            workflow = self.completed_workflows[workflow_id].copy()
            workflow['status'] = workflow['status'].value
            
            # Get task history for this workflow
            workflow_tasks = [
                task for task in self.task_metrics_history
                if task['workflow_id'] == workflow_id
            ]
            workflow['task_history'] = workflow_tasks
            
            return workflow
        
        # Check failed workflows
        elif workflow_id in self.failed_workflows:
            workflow = self.failed_workflows[workflow_id].copy()
            workflow['status'] = workflow['status'].value
            return workflow
        
        return None
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter metrics within time period
        recent_metrics = [
            metric for metric in self.metrics_history
            if metric.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {'message': 'No metrics available for specified time period'}
        
        # Calculate trends
        timestamps = [m.timestamp for m in recent_metrics]
        throughputs = [m.throughput_per_hour for m in recent_metrics]
        processing_times = [m.average_processing_time for m in recent_metrics]
        active_workflows = [m.active_workflows for m in recent_metrics]
        
        return {
            'time_period_hours': hours,
            'data_points': len(recent_metrics),
            'trends': {
                'throughput': {
                    'values': throughputs,
                    'average': sum(throughputs) / len(throughputs),
                    'min': min(throughputs),
                    'max': max(throughputs)
                },
                'processing_time': {
                    'values': processing_times,
                    'average': sum(processing_times) / len(processing_times),
                    'min': min(processing_times),
                    'max': max(processing_times)
                },
                'active_workflows': {
                    'values': active_workflows,
                    'average': sum(active_workflows) / len(active_workflows),
                    'min': min(active_workflows),
                    'max': max(active_workflows)
                }
            },
            'timestamps': [t.isoformat() for t in timestamps]
        }
    
    def _monitoring_loop(self):
        """Main monitoring loop running in background thread"""
        while self.monitoring_active:
            try:
                if self.config.get('enable_performance_tracking', True):
                    self._collect_performance_metrics()
                
                if self.config.get('enable_auto_alerts', True):
                    self._check_alert_conditions()
                
                # Sleep until next collection interval
                time.sleep(self.config.get('metrics_collection_interval', 30))
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Short sleep before retrying
    
    def _collect_performance_metrics(self):
        """Collect current performance metrics"""
        current_time = datetime.now()
        
        # Calculate current metrics
        metrics = PerformanceMetrics(
            timestamp=current_time,
            active_workflows=len(self.active_workflows),
            active_tasks=len(self.active_tasks),
            completed_workflows=len(self.completed_workflows),
            failed_workflows=len(self.failed_workflows),
            average_processing_time=self.statistics['average_workflow_time'],
            throughput_per_hour=self._calculate_throughput(),
            memory_usage=self._get_memory_usage(),
            cpu_usage=self._get_cpu_usage(),
            queue_size=sum(1 for task in self.active_tasks.values() 
                          if task.status == TaskStatus.QUEUED)
        )
        
        self.metrics_history.append(metrics)
    
    def _check_alert_conditions(self):
        """Check for conditions that should trigger alerts"""
        thresholds = self.config['alert_thresholds']
        
        # Check queue size
        queue_size = sum(1 for task in self.active_tasks.values() 
                        if task.status == TaskStatus.QUEUED)
        if queue_size > thresholds['max_queue_size']:
            self.create_alert(
                AlertLevel.WARNING,
                "High Queue Size",
                f"Task queue size ({queue_size}) exceeds threshold ({thresholds['max_queue_size']})",
                "queue_monitor"
            )
        
        # Check failure rate
        total_workflows = len(self.completed_workflows) + len(self.failed_workflows)
        if total_workflows > 0:
            failure_rate = len(self.failed_workflows) / total_workflows
            if failure_rate > thresholds['max_failure_rate']:
                self.create_alert(
                    AlertLevel.ERROR,
                    "High Failure Rate",
                    f"Workflow failure rate ({failure_rate:.2%}) exceeds threshold ({thresholds['max_failure_rate']:.2%})",
                    "failure_monitor"
                )
        
        # Check for long-running tasks
        current_time = datetime.now()
        for task in self.active_tasks.values():
            if (task.status == TaskStatus.PROCESSING and 
                task.started_at and 
                (current_time - task.started_at).total_seconds() > thresholds['max_processing_time']):
                
                self.create_alert(
                    AlertLevel.WARNING,
                    "Long Running Task",
                    f"Task {task.task_id} has been processing for over {thresholds['max_processing_time']} seconds",
                    "task_monitor"
                )
    
    def _update_workflow_statistics(self, workflow: Dict[str, Any]):
        """Update workflow statistics"""
        if workflow['processing_time']:
            total_time = self.statistics['total_processing_time']
            total_workflows = self.statistics['total_workflows_processed']
            
            self.statistics['total_processing_time'] += workflow['processing_time']
            self.statistics['average_workflow_time'] = (
                self.statistics['total_processing_time'] / max(1, total_workflows)
            )
        
        # Update success rate
        total_completed = len(self.completed_workflows) + len(self.failed_workflows)
        if total_completed > 0:
            self.statistics['success_rate'] = (
                len(self.completed_workflows) / total_completed * 100
            )
    
    def _update_task_statistics(self, task: TaskMetrics):
        """Update task statistics"""
        if task.processing_time:
            # Update average task time (simplified calculation)
            current_avg = self.statistics['average_task_time']
            total_tasks = self.statistics['total_tasks_processed'] + 1
            
            self.statistics['average_task_time'] = (
                (current_avg * (total_tasks - 1) + task.processing_time) / total_tasks
            )
            self.statistics['total_tasks_processed'] = total_tasks
    
    def _calculate_throughput(self) -> float:
        """Calculate current throughput (documents per hour)"""
        if not self.metrics_history:
            return 0.0
        
        # Use recent metrics to calculate throughput
        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 data points
        if len(recent_metrics) < 2:
            return 0.0
        
        # Calculate average throughput from recent metrics
        throughputs = [m.throughput_per_hour for m in recent_metrics if m.throughput_per_hour > 0]
        return sum(throughputs) / len(throughputs) if throughputs else 0.0
    
    def _get_system_status(self) -> str:
        """Get overall system status"""
        critical_alerts = sum(1 for alert in self.active_alerts.values() 
                            if alert.level == AlertLevel.CRITICAL)
        error_alerts = sum(1 for alert in self.active_alerts.values() 
                         if alert.level == AlertLevel.ERROR)
        
        if critical_alerts > 0:
            return "critical"
        elif error_alerts > 0:
            return "error"
        elif len(self.active_alerts) > 0:
            return "warning"
        else:
            return "healthy"
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        # Placeholder - would integrate with actual system monitoring
        return 0.45  # 45%
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        # Placeholder - would integrate with actual system monitoring
        return 0.32  # 32%
    
    def shutdown(self):
        """Shutdown the monitoring system"""
        self.monitoring_active = False
        if self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Status Monitor shutdown complete")