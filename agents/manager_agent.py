"""
Manager Agent - Orchestrates workflow execution and manages system state
Coordinates all other agents and makes final decisions on document processing
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class DecisionOutcome(Enum):
    """Decision outcomes for document processing"""
    APPROVE = "approve"
    REJECT = "reject"
    HUMAN_REVIEW = "human_review"
    ESCALATE = "escalate"

@dataclass
class AgentPerformance:
    """Agent performance metrics"""
    agent_id: str
    tasks_completed: int
    success_rate: float
    average_processing_time: float
    last_activity: datetime
    status: str

@dataclass
class WorkflowDecision:
    """Workflow decision data"""
    workflow_id: str
    decision: DecisionOutcome
    confidence: float
    reasoning: str
    anomalies: List[Dict[str, Any]]
    risk_level: str
    timestamp: datetime

class ManagerAgent(BaseAgent):
    """Manager Agent - Orchestrates the entire workflow and manages system state"""
    
    def __init__(self, agent_id: str = "manager_agent"):
        super().__init__(agent_id, "Manager Agent")
        
        # State management
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        self.agent_performance: Dict[str, AgentPerformance] = {}
        
        # Decision thresholds
        self.confidence_threshold = 0.8
        self.risk_threshold = 0.7
        self.anomaly_threshold = 3
        
        # Performance tracking
        self.decisions_made = 0
        self.correct_decisions = 0
        self.system_uptime = datetime.now()
        
        # Register message handlers
        self.setup_message_handlers()
    
    def setup_message_handlers(self):
        """Setup message handlers for different types of messages"""
        self.message_handlers = {
            "workflow_start": self.handle_workflow_start,
            "agent_result": self.handle_agent_result,
            "quality_review": self.handle_quality_review,
            "human_feedback": self.handle_human_feedback,
            "system_health": self.handle_system_health,
            "agent_status": self.handle_agent_status
        }
    
    async def handle_workflow_start(self, message: Dict[str, Any]):
        """Handle workflow start message"""
        workflow_id = message.get("workflow_id")
        document_data = message.get("document_data", {})
        
        logger.info(f"Starting workflow {workflow_id}")
        
        # Create workflow state
        workflow_state = {
            "workflow_id": workflow_id,
            "document_id": document_data.get("document_id"),
            "document_type": document_data.get("document_type"),
            "status": "started",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_stage": "extraction",
            "agent_results": {},
            "anomalies": [],
            "confidence_scores": {},
            "risk_assessment": "low"
        }
        
        self.active_workflows[workflow_id] = workflow_state
        
        # Assign to Extraction Agent
        await self.assign_to_agent(workflow_id, "extraction_agent", {
            "task_type": "extract_data",
            "document_data": document_data
        })
        
        logger.info(f"Workflow {workflow_id} assigned to Extraction Agent")
    
    async def handle_agent_result(self, message: Dict[str, Any]):
        """Handle results from other agents"""
        workflow_id = message.get("workflow_id")
        agent_id = message.get("agent_id")
        result_data = message.get("result_data", {})
        
        if workflow_id not in self.active_workflows:
            logger.warning(f"Received result for unknown workflow {workflow_id}")
            return
        
        workflow = self.active_workflows[workflow_id]
        workflow["agent_results"][agent_id] = result_data
        workflow["updated_at"] = datetime.now().isoformat()
        
        # Update confidence scores
        if "confidence_score" in result_data:
            workflow["confidence_scores"][agent_id] = result_data["confidence_score"]
        
        # Check if all required agents have completed
        if self._check_workflow_completion(workflow_id):
            await self._advance_workflow(workflow_id)
        
        logger.info(f"Updated workflow {workflow_id} with results from {agent_id}")
    
    async def handle_quality_review(self, message: Dict[str, Any]):
        """Handle quality review results"""
        workflow_id = message.get("workflow_id")
        quality_data = message.get("quality_data", {})
        
        if workflow_id not in self.active_workflows:
            return
        
        workflow = self.active_workflows[workflow_id]
        workflow["quality_review"] = quality_data
        workflow["anomalies"] = quality_data.get("anomalies", [])
        workflow["updated_at"] = datetime.now().isoformat()
        
        # Make final decision
        decision = await self._make_workflow_decision(workflow_id)
        
        # Execute decision
        await self._execute_decision(workflow_id, decision)
        
        logger.info(f"Quality review completed for workflow {workflow_id}, decision: {decision.decision.value}")
    
    async def handle_human_feedback(self, message: Dict[str, Any]):
        """Handle human feedback and learning"""
        workflow_id = message.get("workflow_id")
        feedback_data = message.get("feedback_data", {})
        
        if workflow_id not in self.active_workflows:
            return
        
        workflow = self.active_workflows[workflow_id]
        workflow["human_feedback"] = feedback_data
        workflow["updated_at"] = datetime.now().isoformat()
        
        # Process feedback through Learning Agent
        await self._process_feedback(workflow_id, feedback_data)
        
        # Update decision based on feedback
        updated_decision = await self._reevaluate_decision(workflow_id)
        await self._execute_decision(workflow_id, updated_decision)
        
        logger.info(f"Human feedback processed for workflow {workflow_id}")
    
    async def handle_system_health(self, message: Dict[str, Any]):
        """Handle system health updates"""
        health_data = message.get("health_data", {})
        
        # Update agent performance metrics
        for agent_id, metrics in health_data.get("agent_metrics", {}).items():
            if agent_id in self.agent_performance:
                self.agent_performance[agent_id].tasks_completed = metrics.get("tasks_completed", 0)
                self.agent_performance[agent_id].success_rate = metrics.get("success_rate", 0.0)
                self.agent_performance[agent_id].last_activity = datetime.now()
        
        # Check system health
        overall_health = self._assess_system_health()
        
        if overall_health < 0.8:
            logger.warning(f"System health degraded: {overall_health}")
            await self._initiate_health_recovery()
    
    async def handle_agent_status(self, message: Dict[str, Any]):
        """Handle agent status updates"""
        agent_id = message.get("agent_id")
        status_data = message.get("status_data", {})
        
        if agent_id not in self.agent_performance:
            # Create new agent performance record
            self.agent_performance[agent_id] = AgentPerformance(
                agent_id=agent_id,
                tasks_completed=0,
                success_rate=1.0,
                average_processing_time=0.0,
                last_activity=datetime.now(),
                status="active"
            )
        
        # Update agent status
        self.agent_performance[agent_id].status = status_data.get("status", "active")
        self.agent_performance[agent_id].last_activity = datetime.now()
        
        logger.info(f"Updated status for agent {agent_id}: {status_data.get('status')}")
    
    def _check_workflow_completion(self, workflow_id: str) -> bool:
        """Check if all required agents have completed their tasks"""
        workflow = self.active_workflows[workflow_id]
        document_type = workflow.get("document_type")
        
        # Define required agents for each document type
        required_agents = {
            "invoice": ["extraction_agent", "contract_agent", "msa_agent", "master_data_agent"],
            "contract": ["extraction_agent", "master_data_agent"],
            "msa": ["extraction_agent", "master_data_agent"],
            "lease": ["extraction_agent", "master_data_agent"],
            "fixed_asset": ["extraction_agent", "master_data_agent"]
        }
        
        required = required_agents.get(document_type, ["extraction_agent"])
        
        # Check if all required agents have completed
        for agent_id in required:
            if agent_id not in workflow["agent_results"]:
                return False
        
        return True
    
    async def _advance_workflow(self, workflow_id: str):
        """Advance workflow to next stage"""
        workflow = self.active_workflows[workflow_id]
        
        if workflow["current_stage"] == "extraction":
            # Move to validation stage
            workflow["current_stage"] = "validation"
            workflow["status"] = "validation_in_progress"
            
            # Assign to validation agents
            await self._assign_validation_agents(workflow_id)
            
        elif workflow["current_stage"] == "validation":
            # Move to quality review
            workflow["current_stage"] = "quality_review"
            workflow["status"] = "quality_review_in_progress"
            
            # Assign to Quality Review Agent
            await self.assign_to_agent(workflow_id, "quality_review_agent", {
                "task_type": "quality_review",
                "workflow_data": workflow
            })
        
        workflow["updated_at"] = datetime.now().isoformat()
        logger.info(f"Advanced workflow {workflow_id} to stage: {workflow['current_stage']}")
    
    async def _assign_validation_agents(self, workflow_id: str):
        """Assign workflow to validation agents"""
        workflow = self.active_workflows[workflow_id]
        document_type = workflow.get("document_type")
        
        # Define validation agents for each document type
        validation_agents = {
            "invoice": ["contract_agent", "msa_agent", "master_data_agent"],
            "contract": ["master_data_agent"],
            "msa": ["master_data_agent"],
            "lease": ["master_data_agent"],
            "fixed_asset": ["master_data_agent"]
        }
        
        agents = validation_agents.get(document_type, [])
        
        # Assign to each validation agent
        for agent_id in agents:
            await self.assign_to_agent(workflow_id, agent_id, {
                "task_type": "validate_document",
                "workflow_data": workflow
            })
    
    async def _make_workflow_decision(self, workflow_id: str) -> WorkflowDecision:
        """Make final decision on workflow"""
        workflow = self.active_workflows[workflow_id]
        
        # Calculate overall confidence
        confidence_scores = list(workflow["confidence_scores"].values())
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Assess risk based on anomalies
        anomalies = workflow.get("anomalies", [])
        risk_level = self._assess_risk_level(anomalies)
        
        # Make decision based on confidence and risk
        if overall_confidence >= self.confidence_threshold and risk_level == "low":
            decision = DecisionOutcome.APPROVE
            reasoning = "High confidence, low risk - automatic approval"
        elif overall_confidence >= self.confidence_threshold and risk_level in ["medium", "high"]:
            decision = DecisionOutcome.HUMAN_REVIEW
            reasoning = f"High confidence but {risk_level} risk - requires human review"
        elif len(anomalies) > self.anomaly_threshold:
            decision = DecisionOutcome.REJECT
            reasoning = f"Too many anomalies ({len(anomalies)}) - automatic rejection"
        else:
            decision = DecisionOutcome.HUMAN_REVIEW
            reasoning = f"Low confidence ({overall_confidence:.2f}) - requires human review"
        
        decision_obj = WorkflowDecision(
            workflow_id=workflow_id,
            decision=decision,
            confidence=overall_confidence,
            reasoning=reasoning,
            anomalies=anomalies,
            risk_level=risk_level,
            timestamp=datetime.now()
        )
        
        self.decisions_made += 1
        
        return decision_obj
    
    def _assess_risk_level(self, anomalies: List[Dict[str, Any]]) -> str:
        """Assess risk level based on anomalies"""
        if not anomalies:
            return "low"
        
        # Count high and critical severity anomalies
        high_critical_count = sum(
            1 for anomaly in anomalies 
            if anomaly.get("severity") in ["high", "critical"]
        )
        
        if high_critical_count >= 3:
            return "critical"
        elif high_critical_count >= 1:
            return "high"
        elif len(anomalies) >= 3:
            return "medium"
        else:
            return "low"
    
    async def _execute_decision(self, workflow_id: str, decision: WorkflowDecision):
        """Execute the workflow decision"""
        workflow = self.active_workflows[workflow_id]
        
        if decision.decision == DecisionOutcome.APPROVE:
            workflow["status"] = "approved"
            workflow["final_decision"] = decision.to_dict()
            await self._complete_workflow(workflow_id, "approved")
            
        elif decision.decision == DecisionOutcome.REJECT:
            workflow["status"] = "rejected"
            workflow["final_decision"] = decision.to_dict()
            await self._complete_workflow(workflow_id, "rejected")
            
        elif decision.decision == DecisionOutcome.HUMAN_REVIEW:
            workflow["status"] = "human_review_required"
            workflow["pending_decision"] = decision.to_dict()
            await self._escalate_to_human_review(workflow_id, decision)
        
        workflow["updated_at"] = datetime.now().isoformat()
        logger.info(f"Executed decision for workflow {workflow_id}: {decision.decision.value}")
    
    async def _escalate_to_human_review(self, workflow_id: str, decision: WorkflowDecision):
        """Escalate workflow to human review"""
        # Send notification to UI
        notification = {
            "type": "human_review_required",
            "workflow_id": workflow_id,
            "decision_data": decision.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        # This would be sent through the message queue to the UI
        logger.info(f"Escalated workflow {workflow_id} to human review")
    
    async def _process_feedback(self, workflow_id: str, feedback_data: Dict[str, Any]):
        """Process human feedback through Learning Agent"""
        # Send feedback to Learning Agent
        learning_message = {
            "type": "process_feedback",
            "workflow_id": workflow_id,
            "feedback_data": feedback_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # This would be sent through the message queue to the Learning Agent
        logger.info(f"Processing feedback for workflow {workflow_id}")
    
    async def _reevaluate_decision(self, workflow_id: str) -> WorkflowDecision:
        """Reevaluate decision based on human feedback"""
        workflow = self.active_workflows[workflow_id]
        feedback = workflow.get("human_feedback", {})
        
        # Adjust confidence based on feedback
        feedback_score = feedback.get("feedback_score", 0.5)
        original_confidence = workflow.get("confidence_scores", {}).get("extraction_agent", 0.0)
        
        # Adjust confidence based on feedback
        adjusted_confidence = (original_confidence + feedback_score) / 2
        
        # Make new decision
        if adjusted_confidence >= self.confidence_threshold:
            decision = DecisionOutcome.APPROVE
            reasoning = "Approved based on human feedback and adjusted confidence"
        else:
            decision = DecisionOutcome.REJECT
            reasoning = "Rejected based on human feedback and low confidence"
        
        return WorkflowDecision(
            workflow_id=workflow_id,
            decision=decision,
            confidence=adjusted_confidence,
            reasoning=reasoning,
            anomalies=workflow.get("anomalies", []),
            risk_level=self._assess_risk_level(workflow.get("anomalies", [])),
            timestamp=datetime.now()
        )
    
    async def _complete_workflow(self, workflow_id: str, final_status: str):
        """Complete workflow and move to history"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow["status"] = final_status
            workflow["completed_at"] = datetime.now().isoformat()
            
            # Move to history
            self.workflow_history.append(workflow)
            del self.active_workflows[workflow_id]
            
            logger.info(f"Completed workflow {workflow_id} with status: {final_status}")
    
    def _assess_system_health(self) -> float:
        """Assess overall system health"""
        if not self.agent_performance:
            return 1.0
        
        # Calculate average success rate
        success_rates = [agent.success_rate for agent in self.agent_performance.values()]
        avg_success_rate = sum(success_rates) / len(success_rates)
        
        # Calculate agent availability
        active_agents = sum(1 for agent in self.agent_performance.values() if agent.status == "active")
        total_agents = len(self.agent_performance)
        availability_rate = active_agents / total_agents if total_agents > 0 else 0
        
        # Overall health is average of success rate and availability
        overall_health = (avg_success_rate + availability_rate) / 2
        
        return overall_health
    
    async def _initiate_health_recovery(self):
        """Initiate system health recovery procedures"""
        logger.warning("Initiating system health recovery procedures")
        
        # Check for failed agents
        failed_agents = [
            agent_id for agent_id, agent in self.agent_performance.items()
            if agent.status == "failed" or agent.status == "inactive"
        ]
        
        # Attempt to restart failed agents
        for agent_id in failed_agents:
            await self._restart_agent(agent_id)
    
    async def _restart_agent(self, agent_id: str):
        """Restart a failed agent"""
        logger.info(f"Attempting to restart agent {agent_id}")
        
        # Send restart command to agent
        restart_message = {
            "type": "restart_agent",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # This would be sent through the message queue
        logger.info(f"Sent restart command to agent {agent_id}")
    
    async def assign_to_agent(self, workflow_id: str, agent_id: str, task_data: Dict[str, Any]):
        """Assign a task to a specific agent"""
        task_message = {
            "type": "task_assignment",
            "workflow_id": workflow_id,
            "agent_id": agent_id,
            "task_data": task_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # This would be sent through the message queue to the target agent
        logger.info(f"Assigned task to agent {agent_id} for workflow {workflow_id}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "manager_status": "active",
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len(self.workflow_history),
            "decisions_made": self.decisions_made,
            "system_uptime": (datetime.now() - self.system_uptime).total_seconds(),
            "system_health": self._assess_system_health(),
            "agent_performance": {
                agent_id: {
                    "status": agent.status,
                    "tasks_completed": agent.tasks_completed,
                    "success_rate": agent.success_rate,
                    "last_activity": agent.last_activity.isoformat()
                }
                for agent_id, agent in self.agent_performance.items()
            }
        }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific workflow"""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        return None
    
    def get_all_workflows(self) -> Dict[str, Any]:
        """Get all workflow information"""
        return {
            "active_workflows": self.active_workflows,
            "workflow_history": self.workflow_history
        }