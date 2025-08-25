"""
State Management Visualization Demo
Shows how the Manager Agent manages workflow state and coordinates all agents
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any

class StateManagementDemo:
    """Demonstrates state management and coordination"""
    
    def __init__(self):
        self.workflow_states = {}
        self.state_transitions = []
        self.agent_coordination = {}
        
    def create_workflow_state(self, workflow_id: str, document_type: str):
        """Create initial workflow state"""
        state = {
            "workflow_id": workflow_id,
            "document_type": document_type,
            "status": "created",
            "stage": "initialization",
            "agents_involved": [],
            "current_agent": None,
            "agent_results": {},
            "anomalies": [],
            "confidence_scores": {},
            "risk_assessment": "pending",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "state_version": 1
        }
        
        self.workflow_states[workflow_id] = state
        self.record_state_transition(workflow_id, "created", "initialization")
        
        print(f"🎯 Created workflow state for {workflow_id}")
        return state
    
    def record_state_transition(self, workflow_id: str, new_status: str, new_stage: str):
        """Record state transitions for audit trail"""
        transition = {
            "workflow_id": workflow_id,
            "timestamp": datetime.now().isoformat(),
            "status": new_status,
            "stage": new_stage,
            "state_snapshot": self.workflow_states[workflow_id].copy()
        }
        
        self.state_transitions.append(transition)
    
    def assign_agent(self, workflow_id: str, agent_id: str, task_type: str):
        """Assign a task to an agent and update state"""
        if workflow_id not in self.workflow_states:
            print(f"❌ Workflow {workflow_id} not found")
            return
        
        workflow = self.workflow_states[workflow_id]
        
        # Update workflow state
        workflow["current_agent"] = agent_id
        workflow["stage"] = f"{agent_id}_processing"
        workflow["status"] = "agent_processing"
        workflow["agents_involved"].append(agent_id)
        workflow["last_updated"] = datetime.now().isoformat()
        workflow["state_version"] += 1
        
        # Record coordination
        self.agent_coordination[f"{workflow_id}_{agent_id}"] = {
            "workflow_id": workflow_id,
            "agent_id": agent_id,
            "task_type": task_type,
            "assigned_at": datetime.now().isoformat(),
            "status": "assigned"
        }
        
        self.record_state_transition(workflow_id, "agent_processing", f"{agent_id}_processing")
        
        print(f"🤖 Assigned {agent_id} to {workflow_id} for {task_type}")
    
    def update_agent_result(self, workflow_id: str, agent_id: str, result: Dict[str, Any]):
        """Update workflow state with agent results"""
        if workflow_id not in self.workflow_states:
            return
        
        workflow = self.workflow_states[workflow_id]
        
        # Update agent results
        workflow["agent_results"][agent_id] = result
        workflow["confidence_scores"][agent_id] = result.get("confidence_score", 0.0)
        
        # Update coordination status
        coord_key = f"{workflow_id}_{agent_id}"
        if coord_key in self.agent_coordination:
            self.agent_coordination[coord_key]["status"] = "completed"
            self.agent_coordination[coord_key]["completed_at"] = datetime.now().isoformat()
            self.agent_coordination[coord_key]["result"] = result
        
        # Check if all required agents have completed
        if self._check_workflow_ready_for_next_stage(workflow_id):
            self._advance_workflow_stage(workflow_id)
        
        workflow["last_updated"] = datetime.now().isoformat()
        workflow["state_version"] += 1
        
        print(f"✅ Updated {workflow_id} with results from {agent_id}")
    
    def _check_workflow_ready_for_next_stage(self, workflow_id: str) -> bool:
        """Check if workflow is ready to advance to next stage"""
        workflow = self.workflow_states[workflow_id]
        current_stage = workflow["stage"]
        
        if "extraction_agent_processing" in current_stage:
            # Check if extraction is complete
            return "extraction_agent" in workflow["agent_results"]
        
        elif "validation_processing" in current_stage:
            # Check if all validation agents are complete
            required_agents = ["contract_agent", "msa_agent", "master_data_agent"]
            return all(agent in workflow["agent_results"] for agent in required_agents)
        
        elif "quality_review_agent_processing" in current_stage:
            # Check if quality review is complete
            return "quality_review_agent" in workflow["agent_results"]
        
        return False
    
    def _advance_workflow_stage(self, workflow_id: str):
        """Advance workflow to next stage"""
        workflow = self.workflow_states[workflow_id]
        
        if "extraction_agent_processing" in workflow["stage"]:
            # Move to validation stage
            workflow["stage"] = "validation_processing"
            workflow["status"] = "validation_in_progress"
            workflow["current_agent"] = "validation_coordinator"
            
            # Assign validation agents
            self._assign_validation_agents(workflow_id)
            
        elif "validation_processing" in workflow["stage"]:
            # Move to quality review
            workflow["stage"] = "quality_review_processing"
            workflow["status"] = "quality_review_in_progress"
            workflow["current_agent"] = "quality_review_agent"
            
            # Assign quality review
            self.assign_agent(workflow_id, "quality_review_agent", "quality_review")
            
        elif "quality_review_agent_processing" in workflow["stage"]:
            # Move to decision stage
            workflow["stage"] = "decision_processing"
            workflow["status"] = "decision_in_progress"
            workflow["current_agent"] = "manager_agent"
            
            # Make final decision
            self._make_final_decision(workflow_id)
        
        self.record_state_transition(workflow_id, workflow["status"], workflow["stage"])
        print(f"🔄 Advanced {workflow_id} to stage: {workflow['stage']}")
    
    def _assign_validation_agents(self, workflow_id: str):
        """Assign workflow to validation agents"""
        validation_agents = ["contract_agent", "msa_agent", "master_data_agent"]
        
        for agent in validation_agents:
            self.assign_agent(workflow_id, agent, "validation")
    
    def _make_final_decision(self, workflow_id: str):
        """Make final decision based on all agent results"""
        workflow = self.workflow_states[workflow_id]
        
        # Calculate overall confidence
        confidence_scores = list(workflow["confidence_scores"].values())
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Assess anomalies
        all_anomalies = []
        for agent_result in workflow["agent_results"].values():
            if "anomalies" in agent_result:
                all_anomalies.extend(agent_result["anomalies"])
        
        # Determine decision
        if overall_confidence >= 0.9 and len(all_anomalies) == 0:
            decision = "APPROVE"
            reasoning = "High confidence, no anomalies"
        elif overall_confidence >= 0.8 and len(all_anomalies) <= 1:
            decision = "APPROVE"
            reasoning = "Good confidence, minor anomalies"
        elif overall_confidence >= 0.7 and len(all_anomalies) <= 2:
            decision = "HUMAN_REVIEW"
            reasoning = "Moderate confidence, requires review"
        else:
            decision = "REJECT"
            reasoning = "Low confidence or too many anomalies"
        
        # Update workflow state
        workflow["stage"] = "completed"
        workflow["status"] = "decision_completed"
        workflow["current_agent"] = None
        workflow["final_decision"] = {
            "decision": decision,
            "reasoning": reasoning,
            "confidence": overall_confidence,
            "anomaly_count": len(all_anomalies),
            "timestamp": datetime.now().isoformat()
        }
        workflow["anomalies"] = all_anomalies
        workflow["last_updated"] = datetime.now().isoformat()
        workflow["state_version"] += 1
        
        self.record_state_transition(workflow_id, "decision_completed", "completed")
        
        print(f"🎯 Final decision for {workflow_id}: {decision}")
    
    def show_state_transitions(self, workflow_id: str):
        """Show state transition history for a workflow"""
        if workflow_id not in self.workflow_states:
            print(f"❌ Workflow {workflow_id} not found")
            return
        
        workflow = self.workflow_states[workflow_id]
        transitions = [t for t in self.state_transitions if t["workflow_id"] == workflow_id]
        
        print(f"\n📊 State Transition History for {workflow_id}")
        print(f"📄 Document Type: {workflow['document_type']}")
        print("=" * 80)
        
        for i, transition in enumerate(transitions):
            print(f"{i+1:2d}. {transition['timestamp'][11:19]} | "
                  f"Status: {transition['status']:20} | "
                  f"Stage: {transition['stage']:25} | "
                  f"Version: {transition['state_snapshot']['state_version']}")
        
        print(f"\n🎯 Final Status: {workflow['status']}")
        if 'final_decision' in workflow:
            decision = workflow['final_decision']
            print(f"📋 Decision: {decision['decision']}")
            print(f"💭 Reasoning: {decision['reasoning']}")
            print(f"🎯 Confidence: {decision['confidence']:.3f}")
            print(f"🚨 Anomalies: {decision['anomaly_count']}")
    
    def show_agent_coordination(self):
        """Show agent coordination matrix"""
        print(f"\n🤖 Agent Coordination Matrix")
        print("=" * 80)
        
        # Group by workflow
        workflow_coordinations = {}
        for coord_key, coord_data in self.agent_coordination.items():
            workflow_id = coord_data["workflow_id"]
            if workflow_id not in workflow_coordinations:
                workflow_coordinations[workflow_id] = []
            workflow_coordinations[workflow_id].append(coord_data)
        
        for workflow_id, coordinations in workflow_coordinations.items():
            print(f"\n📋 Workflow: {workflow_id}")
            for coord in coordinations:
                status_icon = "✅" if coord["status"] == "completed" else "🔄"
                print(f"  {status_icon} {coord['agent_id']:20} | "
                      f"{coord['task_type']:15} | "
                      f"{coord['status']:10} | "
                      f"{coord['assigned_at'][11:19]}")
    
    def show_current_states(self):
        """Show current state of all workflows"""
        print(f"\n📊 Current Workflow States")
        print("=" * 80)
        
        for workflow_id, workflow in self.workflow_states.items():
            print(f"\n🎯 {workflow_id}")
            print(f"  📄 Type: {workflow['document_type']}")
            print(f"  📊 Status: {workflow['status']}")
            print(f"  🔄 Stage: {workflow['stage']}")
            print(f"  🤖 Current Agent: {workflow['current_agent'] or 'None'}")
            print(f"  👥 Agents Involved: {', '.join(workflow['agents_involved'])}")
            print(f"  📈 State Version: {workflow['state_version']}")
            print(f"  🕒 Last Updated: {workflow['last_updated'][11:19]}")
            
            if workflow['agent_results']:
                print(f"  ✅ Completed Agents: {len(workflow['agent_results'])}")
                for agent_id, result in workflow['agent_results'].items():
                    confidence = result.get('confidence_score', 0)
                    print(f"    • {agent_id}: {confidence:.3f}")
    
    def export_state_data(self, filename: str = "workflow_states.json"):
        """Export all state data to JSON file"""
        export_data = {
            "workflow_states": self.workflow_states,
            "state_transitions": self.state_transitions,
            "agent_coordination": self.agent_coordination,
            "export_timestamp": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"💾 Exported state data to {filename}")

def run_state_management_demo():
    """Run the complete state management demonstration"""
    print("🎬 STATE MANAGEMENT & COORDINATION DEMONSTRATION")
    print("=" * 80)
    print("This demo shows how the Manager Agent manages workflow state")
    print("and coordinates all 9 agents throughout the process.")
    print("=" * 80)
    
    demo = StateManagementDemo()
    
    # Create sample workflows
    workflows = [
        ("WF-INV-001", "invoice"),
        ("WF-CON-001", "contract"),
        ("WF-MSA-001", "msa")
    ]
    
    for workflow_id, doc_type in workflows:
        print(f"\n{'='*60}")
        print(f"🚀 Processing {doc_type.upper()}: {workflow_id}")
        print(f"{'='*60}")
        
        # Create workflow state
        demo.create_workflow_state(workflow_id, doc_type)
        
        # Simulate workflow execution
        demo.assign_agent(workflow_id, "extraction_agent", "extraction")
        
        # Simulate extraction completion
        extraction_result = {
            "confidence_score": 0.95,
            "extracted_fields": ["invoice_number", "amount", "vendor", "date"],
            "anomalies": []
        }
        demo.update_agent_result(workflow_id, "extraction_agent", extraction_result)
        
        # Simulate validation agents
        validation_agents = ["contract_agent", "msa_agent", "master_data_agent"]
        for agent in validation_agents:
            demo.assign_agent(workflow_id, agent, "validation")
            
            # Simulate validation completion
            validation_result = {
                "confidence_score": 0.88 + (hash(agent) % 100) / 1000,
                "validation_details": f"{agent} validation completed",
                "anomalies": []
            }
            demo.update_agent_result(workflow_id, agent, validation_result)
        
        # Quality review will be automatically assigned and completed
        quality_result = {
            "confidence_score": 0.92,
            "quality_details": "Quality review completed",
            "anomalies": []
        }
        demo.update_agent_result(workflow_id, "quality_review_agent", quality_result)
        
        # Show state transitions for this workflow
        demo.show_state_transitions(workflow_id)
        
        time.sleep(1)
    
    # Show overall system status
    demo.show_current_states()
    demo.show_agent_coordination()
    
    # Export data
    demo.export_state_data()
    
    print(f"\n🎉 STATE MANAGEMENT DEMONSTRATION COMPLETED!")
    print(f"✅ Successfully demonstrated state management and coordination")
    print(f"🤖 All agents coordinated through centralized state management")
    print(f"📊 Full audit trail of state transitions maintained")
    print(f"🔄 Real-time state updates throughout the process")

if __name__ == "__main__":
    run_state_management_demo()
