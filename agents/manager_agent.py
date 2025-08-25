"""
Enhanced Manager Agent for Orchestrating the Multi-Agent Workflow
"""
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base_agent import BaseAgent, AgentStatus
from ..utils.message_queue import (
    MessageType, MessagePriority, create_task_assignment, 
    create_data_request, create_anomaly_alert
)
from ..config.settings import AGENT_CONFIG, WORKFLOW_CONFIG

class ManagerAgent(BaseAgent):
    """Orchestrates the entire multi-agent workflow and manages agent coordination"""
    
    def __init__(self, agent_id: str = "manager_agent"):
        config = AGENT_CONFIG.get("manager_agent", {})
        super().__init__(agent_id, config.get("name", "Workflow Manager Agent"), config)
        
        # Workflow management
        self.workflow_state = {
            "current_phase": "idle",
            "active_tasks": {},
            "completed_tasks": {},
            "failed_tasks": {},
            "workflow_history": [],
            "iteration_count": 0
        }
        
        # Agent registry
        self.registered_agents = {}
        self.agent_status = {}
        self.agent_capabilities = {}
        
        # Task management
        self.task_queue = []
        self.task_assignments = {}
        self.task_results = {}
        
        # Quality gates
        self.quality_gates = WORKFLOW_CONFIG["quality_gates"]
        self.current_quality_score = 0.0
        
        # Collaboration network
        self.collaboration_matrix = {}
        
        self.logger.info(f"Manager Agent initialized with {len(self.quality_gates)} quality gates")
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process workflow management task"""
        start_time = datetime.now()
        
        try:
            self.status = AgentStatus.PROCESSING
            task_type = task_data.get("task_type", "unknown")
            
            self.logger.info(f"Processing workflow task: {task_type}")
            
            if task_type == "start_workflow":
                result = self._start_workflow(task_data)
            elif task_type == "process_documents":
                result = self._process_documents(task_data)
            elif task_type == "quality_review":
                result = self._initiate_quality_review(task_data)
            elif task_type == "handle_feedback":
                result = self._handle_human_feedback(task_data)
            elif task_type == "escalate_issue":
                result = self._escalate_issue(task_data)
            else:
                result = {"error": f"Unknown task type: {task_type}"}
            
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics.record_task_completion(processing_time, result.get("confidence", 0.8))
            
            return result
                
        except Exception as e:
            self.logger.error(f"Error processing workflow task: {e}")
            self.metrics.record_task_failure(str(e))
            self.status = AgentStatus.ERROR
            return {
                "error": str(e),
                "status": "failed",
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
        finally:
            self.status = AgentStatus.IDLE
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate workflow data"""
        validation_result = {
            "is_valid": True,
            "missing_fields": [],
            "validation_errors": [],
            "overall_score": 0.0
        }
        
        # Check required workflow fields
        required_fields = ["workflow_type", "documents", "priority"]
        for field in required_fields:
            if field not in data:
                validation_result["missing_fields"].append(field)
                validation_result["is_valid"] = False
        
        # Validate document structure
        if "documents" in data:
            for doc in data["documents"]:
                if not isinstance(doc, dict) or "document_type" not in doc:
                    validation_result["validation_errors"].append(f"Invalid document structure: {doc}")
                    validation_result["is_valid"] = False
        
        # Calculate validation score
        if validation_result["validation_errors"]:
            validation_result["overall_score"] = 0.5
        elif validation_result["missing_fields"]:
            validation_result["overall_score"] = 0.7
        else:
            validation_result["overall_score"] = 1.0
        
        return validation_result
    
    def detect_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect workflow anomalies"""
        anomalies = []
        
        # Check for workflow conflicts
        if "workflow_type" in data and "documents" in data:
            workflow_type = data["workflow_type"]
            documents = data["documents"]
            
            # Check if document types match workflow type
            if workflow_type == "invoice_processing" and not any(d.get("document_type") == "invoice" for d in documents):
                anomalies.append({
                    "type": "workflow_document_mismatch",
                    "severity": "high",
                    "description": "Invoice processing workflow contains no invoice documents",
                    "workflow_type": workflow_type,
                    "document_types": [d.get("document_type") for d in documents]
                })
        
        # Check for priority conflicts
        if "priority" in data and data["priority"] == "high":
            if "documents" in data and len(data["documents"]) > 10:
                anomalies.append({
                    "type": "high_priority_large_batch",
                    "severity": "medium",
                    "description": "High priority workflow with large document batch",
                    "priority": data["priority"],
                    "document_count": len(data["documents"])
                })
        
        # Check for resource conflicts
        if "documents" in data and len(data["documents"]) > WORKFLOW_CONFIG["batch_size"]:
            anomalies.append({
                "type": "batch_size_exceeded",
                "severity": "medium",
                "description": f"Batch size exceeds configured limit of {WORKFLOW_CONFIG['batch_size']}",
                "actual_size": len(data["documents"]),
                "limit": WORKFLOW_CONFIG["batch_size"]
            })
        
        return anomalies
    
    def register_agent(self, agent_id: str, capabilities: Dict[str, Any]) -> bool:
        """Register an agent with the manager"""
        try:
            self.registered_agents[agent_id] = {
                "registered_at": datetime.now().isoformat(),
                "status": "active",
                "capabilities": capabilities,
                "last_heartbeat": datetime.now().isoformat(),
                "task_count": 0,
                "success_rate": 1.0
            }
            
            self.agent_capabilities[agent_id] = capabilities
            self.agent_status[agent_id] = "active"
            
            # Update collaboration matrix
            self.collaboration_matrix[agent_id] = {
                "can_collaborate_with": [],
                "preferred_partners": [],
                "conflicts": []
            }
            
            self.logger.info(f"Agent registered: {agent_id} with capabilities: {list(capabilities.keys())}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent_id}: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        try:
            if agent_id in self.registered_agents:
                del self.registered_agents[agent_id]
                del self.agent_status[agent_id]
                del self.agent_capabilities[agent_id]
                
                if agent_id in self.collaboration_matrix:
                    del self.collaboration_matrix[agent_id]
                
                self.logger.info(f"Agent unregistered: {agent_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    def _start_workflow(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new workflow"""
        workflow_id = f"WF-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(self.workflow_state['workflow_history'])}"
        
        self.workflow_state["current_phase"] = "initializing"
        self.workflow_state["active_tasks"][workflow_id] = {
            "workflow_id": workflow_id,
            "start_time": datetime.now().isoformat(),
            "task_data": task_data,
            "status": "active",
            "phases": []
        }
        
        # Initialize workflow phases
        workflow_phases = self._define_workflow_phases(task_data)
        self.workflow_state["active_tasks"][workflow_id]["phases"] = workflow_phases
        
        # Start first phase
        self._execute_workflow_phase(workflow_id, workflow_phases[0])
        
        return {
            "workflow_id": workflow_id,
            "status": "started",
            "phases": [phase["name"] for phase in workflow_phases],
            "estimated_duration": self._estimate_workflow_duration(workflow_phases)
        }
    
    def _define_workflow_phases(self, task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Define workflow phases based on task data"""
        workflow_type = task_data.get("workflow_type", "standard")
        
        if workflow_type == "invoice_processing":
            return [
                {
                    "name": "extraction",
                    "agent": "extraction_agent",
                    "description": "Extract invoice data",
                    "quality_gate": self.quality_gates["extraction"],
                    "dependencies": [],
                    "estimated_duration": 30
                },
                {
                    "name": "validation",
                    "agent": "master_data_agent",
                    "description": "Validate against master data",
                    "quality_gate": self.quality_gates["validation"],
                    "dependencies": ["extraction"],
                    "estimated_duration": 45
                },
                {
                    "name": "anomaly_detection",
                    "agent": "quality_review_agent",
                    "description": "Detect and analyze anomalies",
                    "quality_gate": self.quality_gates["final"],
                    "dependencies": ["extraction", "validation"],
                    "estimated_duration": 60
                }
            ]
        else:
            # Standard workflow
            return [
                {
                    "name": "processing",
                    "agent": "extraction_agent",
                    "description": "Process documents",
                    "quality_gate": 0.8,
                    "dependencies": [],
                    "estimated_duration": 60
                },
                {
                    "name": "review",
                    "agent": "quality_review_agent",
                    "description": "Quality review",
                    "quality_gate": 0.9,
                    "dependencies": ["processing"],
                    "estimated_duration": 45
                }
            ]
    
    def _execute_workflow_phase(self, workflow_id: str, phase: Dict[str, Any]) -> bool:
        """Execute a workflow phase"""
        try:
            agent_id = phase["agent"]
            
            if agent_id not in self.registered_agents:
                self.logger.error(f"Agent {agent_id} not registered for phase {phase['name']}")
                return False
            
            # Create task assignment
            task_msg = create_task_assignment(
                sender_id=self.agent_id,
                recipient_id=agent_id,
                task_type=f"workflow_phase_{phase['name']}",
                task_data={
                    "workflow_id": workflow_id,
                    "phase": phase,
                    "task_data": self.workflow_state["active_tasks"][workflow_id]["task_data"]
                }
            )
            
            # Send task
            self.message_queue.send_message(task_msg)
            
            # Update workflow state
            self.workflow_state["active_tasks"][workflow_id]["current_phase"] = phase["name"]
            self.workflow_state["active_tasks"][workflow_id]["phases"][0]["status"] = "executing"
            
            self.logger.info(f"Phase {phase['name']} started for workflow {workflow_id}")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to execute phase {phase['name']}: {e}")
            return False
    
    def _process_documents(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a batch of documents"""
        documents = task_data.get("documents", [])
        workflow_type = task_data.get("workflow_type", "standard")
        
        if not documents:
            return {"error": "No documents provided"}
        
        # Create individual workflows for each document
        workflow_ids = []
        for doc in documents:
            workflow_data = {
                "workflow_type": workflow_type,
                "documents": [doc],
                "priority": task_data.get("priority", "normal")
            }
            
            workflow_result = self._start_workflow({"task_type": "start_workflow", **workflow_data})
            workflow_ids.append(workflow_result["workflow_id"])
        
        return {
            "status": "processing",
            "workflow_ids": workflow_ids,
            "total_documents": len(documents),
            "estimated_completion": self._estimate_batch_completion(workflow_ids)
        }
    
    def _initiate_quality_review(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate quality review process"""
        workflow_id = task_data.get("workflow_id")
        
        if not workflow_id or workflow_id not in self.workflow_state["active_tasks"]:
            return {"error": "Invalid workflow ID"}
        
        # Send quality review request
        review_msg = create_task_assignment(
            sender_id=self.agent_id,
            recipient_id="quality_review_agent",
            task_type="quality_review",
            task_data={
                "workflow_id": workflow_id,
                "workflow_data": self.workflow_state["active_tasks"][workflow_id],
                "quality_gates": self.quality_gates
            }
        )
        
        self.message_queue.send_message(review_msg)
        
        return {
            "status": "quality_review_initiated",
            "workflow_id": workflow_id,
            "review_agent": "quality_review_agent"
        }
    
    def _handle_human_feedback(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle human feedback and initiate learning process"""
        feedback = task_data.get("feedback", {})
        workflow_id = task_data.get("workflow_id")
        
        # Send feedback to learning agent
        learning_msg = create_task_assignment(
            sender_id=self.agent_id,
            recipient_id="learning_agent",
            task_type="process_feedback",
            task_data={
                "feedback": feedback,
                "workflow_id": workflow_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        self.message_queue.send_message(learning_msg)
        
        # Update workflow state
        if workflow_id in self.workflow_state["active_tasks"]:
            self.workflow_state["active_tasks"][workflow_id]["human_feedback"] = feedback
            self.workflow_state["active_tasks"][workflow_id]["status"] = "feedback_processing"
        
        return {
            "status": "feedback_processing",
            "workflow_id": workflow_id,
            "learning_agent": "learning_agent"
        }
    
    def _escalate_issue(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate an issue to higher level"""
        issue = task_data.get("issue", {})
        severity = issue.get("severity", "medium")
        
        # Create escalation alert
        escalation_msg = create_anomaly_alert(
            sender_id=self.agent_id,
            recipient_id="quality_review_agent",
            anomaly_type="escalated_issue",
            anomaly_data=issue,
            severity=severity,
            priority=MessagePriority.HIGH
        )
        
        self.message_queue.send_message(escalation_msg)
        
        # Update workflow state
        if "workflow_id" in issue:
            workflow_id = issue["workflow_id"]
            if workflow_id in self.workflow_state["active_tasks"]:
                self.workflow_state["active_tasks"][workflow_id]["status"] = "escalated"
                self.workflow_state["active_tasks"][workflow_id]["escalation"] = issue
        
        return {
            "status": "issue_escalated",
            "issue_id": issue.get("issue_id", "unknown"),
            "escalation_level": "quality_review_agent"
        }
    
    def _estimate_workflow_duration(self, phases: List[Dict[str, Any]]) -> int:
        """Estimate total workflow duration in seconds"""
        total_duration = 0
        for phase in phases:
            total_duration += phase.get("estimated_duration", 60)
        return total_duration
    
    def _estimate_batch_completion(self, workflow_ids: List[str]) -> str:
        """Estimate batch completion time"""
        # Simple estimation - in production this would be more sophisticated
        estimated_minutes = len(workflow_ids) * 2  # 2 minutes per workflow
        completion_time = datetime.now() + timedelta(minutes=estimated_minutes)
        return completion_time.strftime("%Y-%m-%d %H:%M:%S")
    
    def get_workflow_status(self, workflow_id: str = None) -> Dict[str, Any]:
        """Get workflow status"""
        if workflow_id:
            if workflow_id in self.workflow_state["active_tasks"]:
                return self.workflow_state["active_tasks"][workflow_id]
            elif workflow_id in self.workflow_state["completed_tasks"]:
                return self.workflow_state["completed_tasks"][workflow_id]
            else:
                return {"error": "Workflow not found"}
        else:
        return {
                "current_phase": self.workflow_state["current_phase"],
                "active_workflows": len(self.workflow_state["active_tasks"]),
                "completed_workflows": len(self.workflow_state["completed_tasks"]),
                "failed_workflows": len(self.workflow_state["failed_tasks"]),
                "total_iterations": self.workflow_state["iteration_count"]
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents"""
        return {
            "registered_agents": len(self.registered_agents),
            "agent_details": self.registered_agents,
            "agent_capabilities": self.agent_capabilities,
            "collaboration_matrix": self.collaboration_matrix
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        active_agents = sum(1 for status in self.agent_status.values() if status == "active")
        total_agents = len(self.agent_status)
        
        return {
            "system_status": "healthy" if active_agents == total_agents else "degraded",
            "agent_health": {
                "active": active_agents,
                "total": total_agents,
                "health_percentage": (active_agents / total_agents * 100) if total_agents > 0 else 0
            },
            "workflow_health": {
                "active_workflows": len(self.workflow_state["active_tasks"]),
                "completed_workflows": len(self.workflow_state["completed_tasks"]),
                "failed_workflows": len(self.workflow_state["failed_tasks"])
            },
            "quality_score": self.current_quality_score,
            "last_updated": datetime.now().isoformat()
        }