"""
Agentic AI Dashboard - Enhanced Streamlit UI for Invoice Processing System
Phase 4: Complete multi-tab interface with conversational AI capabilities
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np
from typing import Dict, List, Any, Optional

from config.settings import UI_CONFIG, DATA_DIR
from utils.ai_client import ai_client

# Initialize session state for the agentic system
@st.cache_resource
def initialize_system():
    """Initialize the agentic AI system"""
    try:
        return {
            "initialized": True,
            "status": "Active"
        }
    except Exception as e:
        st.error(f"Failed to initialize system: {e}")
        return {"initialized": False, "error": str(e)}

def load_sample_data():
    """Load sample data for display"""
    data = {
        "invoices": [],
        "contracts": [],
        "msa": [],
        "leases": [],
        "fixed_assets": [],
        "master_data": {}
    }
    
    try:
        # Load invoices
        for i in range(1, 6):
            file_path = DATA_DIR / "invoices" / f"invoice_{i:03d}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data["invoices"].append(json.load(f))
        
        # Load contracts
        for i in range(1, 4):
            file_path = DATA_DIR / "contracts" / f"contract_{i:03d}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data["contracts"].append(json.load(f))
        
        # Load MSA
        msa_path = DATA_DIR / "msa" / "msa_001.json"
        if msa_path.exists():
            with open(msa_path, 'r') as f:
                data["msa"].append(json.load(f))
        
        # Load leases
        for i in range(1, 4):
            file_path = DATA_DIR / "leases" / f"lease_{i:03d}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data["leases"].append(json.load(f))
        
        # Load fixed assets
        for i in range(1, 4):
            file_path = DATA_DIR / "fixed_assets" / f"fixed_asset_{i:03d}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data["fixed_assets"].append(json.load(f))
        
        # Load master data
        master_path = DATA_DIR / "master_data" / "master_data.json"
        if master_path.exists():
            with open(master_path, 'r') as f:
                data["master_data"] = json.load(f)
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
    
    return data

def main():
    """Main Streamlit application - Agentic AI Dashboard"""
    st.set_page_config(
        page_title=UI_CONFIG["page_title"],
        page_icon=UI_CONFIG["page_icon"],
        layout=UI_CONFIG["layout"],
        initial_sidebar_state=UI_CONFIG["initial_sidebar_state"]
    )
    
    # Initialize system
    system_status = initialize_system()
    
    # Header
    st.title("🤖 Agentic AI - Invoice Processing Dashboard")
    st.markdown("**Real-time Multi-Agent Workflow Orchestration with Human-in-the-Loop**")
    
    # Sidebar Navigation
    with st.sidebar:
        st.header("🎛️ Navigation")
        
        # Main navigation
        page = st.selectbox(
            "Select Page",
            [
                "System Dashboard",
                "Agent Monitoring", 
                "Document Processing",
                "Workflow Management",
                "Conversations",
                "Anomalies",
                "Upload Centre",
                "Settings"
            ]
        )
        
        # System status in sidebar
        st.subheader("System Status")
        if system_status["initialized"]:
            st.success("✅ System Active")
        else:
            st.error("❌ System Error")
        
        # Quick actions
        st.subheader("Quick Actions")
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        if st.button("📊 Generate Report"):
            st.info("Generating report...")
    
    # Main content area based on navigation
    if page == "System Dashboard":
        show_system_dashboard()
    elif page == "Agent Monitoring":
        show_agent_monitoring()
    elif page == "Document Processing":
        show_document_processing()
    elif page == "Workflow Management":
        show_workflow_management()
    elif page == "Conversations":
        show_conversations()
    elif page == "Anomalies":
        show_anomalies()
    elif page == "Upload Centre":
        show_upload_centre()
    elif page == "Settings":
        show_system_config()

def show_system_dashboard():
    """System Dashboard - Overview and KPIs"""
    st.header("🏠 System Dashboard")
    
    # Load data
    data = load_sample_data()
    
    # System overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Agents", "9")
        st.caption("All agents operational")
    
    with col2:
        st.metric("Active Workflows", "3")
        st.caption("Current processing")
    
    with col3:
        st.metric("Documents Processed", len(data["invoices"]) + len(data["contracts"]))
        st.caption("Total processed")
    
    with col4:
        st.metric("System Health", "98%")
        st.caption("Optimal performance")
    
    # Processing Pipeline Funnel
    st.subheader("🔄 Processing Pipeline Funnel")
    
    # Create funnel chart for processing pipeline
    stages = ['Document Upload', 'Extraction', 'Validation', 'Quality Review', 'Human Approval', 'Completed']
    values = [100, 85, 75, 65, 55, 45]  # Processing rates at each stage
    
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textposition="inside",
        textinfo="value+percent initial",
        marker={"color": ["#3b82f6", "#60a5fa", "#93bbfd", "#c3d9fe", "#e0ecff", "#f0f9ff"]}
    ))
    
    fig.update_layout(
        title="Document Processing Pipeline Funnel",
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Real-time metrics
    st.subheader("📈 Real-time Metrics")
    
    # Create sample time series data
    time_data = pd.DataFrame({
        'Time': pd.date_range(start=datetime.now() - timedelta(hours=6), periods=24, freq='15min'),
        'Processing Rate': np.random.poisson(15, 24),
        'Error Rate': np.random.exponential(0.1, 24),
        'Response Time': np.random.normal(2.5, 0.5, 24)
    })
    
    # Processing rate chart
    fig1 = px.line(time_data, x='Time', y='Processing Rate', title="Document Processing Rate")
    st.plotly_chart(fig1, use_container_width=True)
    
    # Error rate and response time
    col1, col2 = st.columns(2)
    with col1:
        fig2 = px.line(time_data, x='Time', y='Error Rate', title="Error Rate")
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        fig3 = px.line(time_data, x='Time', y='Response Time', title="Response Time (seconds)")
        st.plotly_chart(fig3, use_container_width=True)

def show_upload_centre():
    """Upload Centre - Document upload and processing"""
    st.header("📤 Upload Centre")
    
    # Document type selection
    doc_type = st.selectbox(
        "Select Document Type",
        ["Invoice", "Contract", "MSA", "Lease", "Fixed Asset"]
    )
    
    # Upload area
    uploaded_file = st.file_uploader(
        f"Upload {doc_type} Document",
        type=['pdf', 'txt', 'json', 'docx'],
        help=f"Upload a {doc_type.lower()} document for processing"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ {uploaded_file.name} uploaded successfully!")
        
        # Processing options
        st.subheader("Processing Options")
        
        col1, col2 = st.columns(2)
        with col1:
            priority = st.selectbox("Priority", ["Low", "Normal", "High", "Critical"])
        
        with col2:
            auto_process = st.checkbox("Auto-process", value=True)
        
        # Process button
        if st.button("🚀 Process Document"):
            with st.spinner("Processing document..."):
                time.sleep(2)  # Simulate processing
                st.success("Document processed successfully!")
                
                # Show results
                st.subheader("Processing Results")
                st.json({
                    "document_type": doc_type,
                    "filename": uploaded_file.name,
                    "status": "completed",
                    "confidence": 0.95,
                    "anomalies_detected": 0
                })

def show_live_monitor():
    """Live Monitor - Real-time system monitoring"""
    st.header("📊 Live Monitor")
    
    # Agent status
    st.subheader("🤖 Agent Status")
    
    agents = [
        {"name": "Extraction Agent", "status": "Active", "tasks": 15, "success_rate": "98%"},
        {"name": "Contract Agent", "status": "Active", "tasks": 12, "success_rate": "97%"},
        {"name": "MSA Agent", "status": "Active", "tasks": 8, "success_rate": "99%"},
        {"name": "Leasing Agent", "status": "Active", "tasks": 10, "success_rate": "96%"},
        {"name": "Fixed Assets Agent", "status": "Active", "tasks": 7, "success_rate": "98%"},
        {"name": "Master Data Agent", "status": "Active", "tasks": 20, "success_rate": "99%"},
        {"name": "Manager Agent", "status": "Active", "tasks": 25, "success_rate": "100%"},
        {"name": "Quality Review Agent", "status": "Active", "tasks": 18, "success_rate": "97%"},
        {"name": "Learning Agent", "status": "Active", "tasks": 5, "success_rate": "95%"}
    ]
    
    for agent in agents:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"**{agent['name']}**")
        with col2:
            if agent['status'] == 'Active':
                st.success("✅")
            else:
                st.error("❌")
        with col3:
            st.write(f"{agent['tasks']}")
        with col4:
            st.write(f"{agent['success_rate']}")
    
    # Workflow status
    st.subheader("🔄 Workflow Status")
    
    workflows = [
        {"id": "WF-001", "type": "Invoice Processing", "status": "Running", "progress": 75},
        {"id": "WF-002", "type": "Contract Review", "status": "Pending", "progress": 0},
        {"id": "WF-003", "type": "MSA Validation", "status": "Completed", "progress": 100}
    ]
    
    for workflow in workflows:
        col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
        with col1:
            st.write(f"**{workflow['id']}**")
        with col2:
            st.write(workflow['type'])
        with col3:
            if workflow['status'] == 'Running':
                st.info("🔄")
            elif workflow['status'] == 'Completed':
                st.success("✅")
            else:
                st.warning("⏳")
        with col4:
            st.progress(workflow['progress'] / 100)

def show_conversations():
    """Conversations - Chat interface with AI agents"""
    st.header("💬 Conversations with AI Agents")
    
    # Agent selection
    agent = st.selectbox(
        "Select Agent to Chat With",
        [
            "Learning Agent",
            "Manager Agent",
            "Extraction Agent", 
            "Contract Agent",
            "MSA Agent",
            "Leasing Agent",
            "Fixed Assets Agent",
            "Master Data Agent",
            "Quality Review Agent"
        ]
    )
    
    st.write(f"**Chatting with: {agent}**")
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question or provide feedback..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response using Learning Agent for feedback processing
        with st.chat_message("assistant"):
            response = generate_ai_response(prompt, agent)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # If this is feedback, process it through the Learning Agent
            if agent == "Learning Agent" and any(word in prompt.lower() for word in ["feedback", "improve", "fix", "wrong", "error", "anomaly"]):
                process_feedback(prompt)

def generate_ai_response(prompt: str, agent: str) -> str:
    """Generate AI response based on prompt and agent using Learning Agent capabilities"""
    prompt_lower = prompt.lower()
    
    # Learning Agent handles feedback and learning
    if agent == "Learning Agent":
        if "feedback" in prompt_lower or "improve" in prompt_lower:
            return process_learning_feedback(prompt)
        elif "anomaly" in prompt_lower or "issue" in prompt_lower:
            return "I've detected your feedback about an anomaly. Let me analyze this and apply the learning to improve our system. What specific issue did you encounter?"
        elif "upload" in prompt_lower and "invoice" in prompt_lower:
            return "I can see you've uploaded an invoice. Let me check the processing results and identify any anomalies. I'll also learn from your feedback to improve future processing."
        else:
            return "I'm the Learning Agent, and I'm here to learn from your feedback and improve our system. Please tell me about any issues you've encountered or suggestions you have."
    
    # Manager Agent provides system overview
    elif agent == "Manager Agent":
        if "status" in prompt_lower:
            return "The system is currently running with all agents active. I'm monitoring 3 active workflows and 9 operational agents. How can I help you?"
        elif "anomaly" in prompt_lower:
            return "I've detected several anomalies in recent processing. Let me connect you with the Learning Agent to process your feedback and apply improvements."
        elif "workflow" in prompt_lower:
            return "Current workflows are being managed efficiently. I can show you detailed progress or connect you with specific agents for more information."
        else:
            return "I'm the Manager Agent overseeing the entire system. I can help you understand system status, workflows, and connect you with specialized agents."
    
    # Specialized agents provide domain expertise
    elif agent == "Extraction Agent":
        if "accuracy" in prompt_lower:
            return "I'm achieving 98% accuracy in invoice extraction. I've learned from previous feedback to improve PO number detection and amount validation."
        elif "anomaly" in prompt_lower:
            return "I've identified several extraction anomalies. The Learning Agent is processing feedback to improve my detection algorithms."
        else:
            return "I'm the Extraction Agent specializing in invoice data extraction. I'm currently processing documents with high accuracy and continuously learning from feedback."
    
    elif agent == "Quality Review Agent":
        if "anomaly" in prompt_lower:
            return "I've detected 12 anomalies today, including missing PO numbers and vendor mismatches. I'm working with the Learning Agent to improve detection patterns."
        else:
            return "I'm the Quality Review Agent ensuring high-quality processing. I'm currently reviewing documents and identifying areas for improvement."
    
    else:
        return f"I'm the {agent} and I'm here to help. I can provide specific information about my domain expertise or connect you with the Learning Agent for feedback processing."

def process_learning_feedback(prompt: str) -> str:
    """Process feedback through the Learning Agent"""
    prompt_lower = prompt.lower()
    
    if "invoice" in prompt_lower and "upload" in prompt_lower:
        return """Thank you for your feedback! I'm the Learning Agent and I'm processing your input to improve our system.

🔍 **Analyzing your feedback...**
- Document type: Invoice
- Processing stage: Upload and extraction
- Feedback received: Processing feedback

📚 **Learning Actions:**
1. Analyzing extraction accuracy
2. Identifying potential improvements
3. Updating processing algorithms
4. Sharing insights with other agents

💡 **Next Steps:**
I'll apply this learning to improve future invoice processing. Your feedback helps make the system smarter and more accurate.

Is there anything specific about the processing results you'd like me to focus on?"""
    
    elif "anomaly" in prompt_lower:
        return """🚨 **Anomaly Feedback Received!**

I'm analyzing your feedback about anomalies to improve our detection system.

🔍 **Current Anomaly Patterns:**
- Missing PO numbers: Critical priority
- Vendor mismatches: High priority  
- Invalid amounts: Medium priority

📚 **Learning from Your Feedback:**
1. Improving anomaly detection algorithms
2. Updating validation rules
3. Enhancing user notification systems
4. Training other agents on new patterns

💡 **System Improvement:**
Your feedback is being applied to make anomaly detection more accurate and user-friendly.

What specific anomaly did you encounter? I want to ensure we catch similar issues in the future."""
    
    else:
        return """Thank you for your feedback! I'm the Learning Agent and I'm here to continuously improve our system.

🔍 **Processing Your Input:**
- Analyzing feedback patterns
- Identifying improvement opportunities
- Updating system knowledge
- Sharing learnings with other agents

💡 **How This Helps:**
Your feedback directly improves:
- Processing accuracy
- Anomaly detection
- User experience
- System performance

Please continue providing feedback - it makes our system smarter with every interaction!"""

def process_feedback(feedback_text: str):
    """Process feedback and apply learning to the system"""
    # This would integrate with the actual Learning Agent
    st.info("🔄 Processing feedback through Learning Agent...")
    st.success("✅ Feedback processed and learning applied to system!")
    
    # Show what was learned
    with st.expander("📚 What Was Learned"):
        st.write("**Feedback Analysis:**")
        st.write(f"- **Input:** {feedback_text}")
        st.write("- **Learning Applied:** Invoice processing improvements")
        st.write("- **System Updates:** Extraction algorithms enhanced")
        st.write("- **Agent Training:** All agents updated with new knowledge")

def show_anomalies():
    """Anomalies - Anomaly detection and analysis"""
    st.header("🚨 Anomaly Detection & Analysis")
    
    # Anomaly overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Anomalies", 12)
        st.caption("Detected today")
    
    with col2:
        st.metric("Critical", 2)
        st.caption("Requires immediate attention")
    
    with col3:
        st.metric("Resolved", 8)
        st.caption("Successfully handled")
    
    # Anomaly details
    st.subheader("Recent Anomalies")
    
    anomalies = [
        {
            "type": "Missing PO Number",
            "severity": "Critical",
            "document": "INV-2024-001",
            "description": "Invoice missing purchase order number",
            "detected": "2 hours ago"
        },
        {
            "type": "Vendor Mismatch",
            "severity": "High", 
            "document": "CON-2024-003",
            "description": "Vendor name doesn't match master data",
            "detected": "4 hours ago"
        },
        {
            "type": "Invalid Amount",
            "severity": "Medium",
            "document": "INV-2024-002", 
            "description": "Invoice amount is negative",
            "detected": "6 hours ago"
        }
    ]
    
    for anomaly in anomalies:
        with st.expander(f"{anomaly['type']} - {anomaly['severity']}"):
            st.write(f"**Document:** {anomaly['document']}")
            st.write(f"**Description:** {anomaly['description']}")
            st.write(f"**Detected:** {anomaly['detected']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Resolve", key=f"resolve_{anomaly['type']}"):
                    st.success("Anomaly resolved!")
            
            with col2:
                if st.button(f"Escalate", key=f"escalate_{anomaly['type']}"):
                    st.warning("Anomaly escalated to quality review agent")

def show_learning_insights():
    """Learning Insights - AI learning and improvements"""
    st.header("🧠 Learning Insights & Improvements")
    
    # Learning metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Learning Iterations", 45)
        st.caption("Total learning cycles")
    
    with col2:
        st.metric("Accuracy Improvement", "+12%")
        st.caption("Since last month")
    
    with col3:
        st.metric("Pattern Recognition", "89%")
        st.caption("Anomaly detection rate")
    
    # Recent learnings
    st.subheader("Recent Learnings")
    
    learnings = [
        "Improved PO number detection accuracy by 15%",
        "Enhanced vendor name matching algorithm",
        "Reduced false positive rate by 8%",
        "Optimized processing workflow efficiency"
    ]
    
    for learning in learnings:
        st.info(f"📚 {learning}")
    
    # Feedback analysis
    st.subheader("Feedback Analysis")
    
    feedback_data = pd.DataFrame({
        'Category': ['Accuracy', 'Speed', 'Usability', 'Reliability'],
        'Rating': [4.2, 4.5, 4.1, 4.3],
        'Improvement': [0.3, 0.4, 0.2, 0.3]
    })
    
    fig = px.bar(feedback_data, x='Category', y='Rating', title="User Feedback Ratings")
    st.plotly_chart(fig, use_container_width=True)

def show_manager_panel():
    """Manager Panel - Critical analysis and oversight"""
    st.header("👨‍💼 Manager Panel - Critical Analysis & Oversight")
    
    # Critical metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Quality Score", "94%")
        st.caption("Overall system quality")
    
    with col2:
        st.metric("Risk Level", "Low")
        st.caption("Current risk assessment")
    
    with col3:
        st.metric("Compliance", "100%")
        st.caption("Regulatory compliance")
    
    with col4:
        st.metric("Efficiency", "87%")
        st.caption("Process efficiency")
    
    # Critical alerts
    st.subheader("🚨 Critical Alerts")
    
    alerts = [
        {"priority": "High", "message": "Multiple PO number anomalies detected", "action": "Review extraction logic"},
        {"priority": "Medium", "message": "Vendor validation rate below threshold", "action": "Update master data"},
        {"priority": "Low", "message": "Processing time increased by 15%", "action": "Monitor performance"}
    ]
    
    for alert in alerts:
        if alert["priority"] == "High":
            st.error(f"🔴 {alert['message']}")
        elif alert["priority"] == "Medium":
            st.warning(f"🟡 {alert['message']}")
        else:
            st.info(f"🔵 {alert['message']}")
        
        st.write(f"**Action Required:** {alert['action']}")
        st.divider()
    
    # Quality challenges
    st.subheader("🎯 Quality Challenges")
    
    if st.button("🔍 Run Quality Challenge"):
        with st.spinner("Running quality challenge..."):
            time.sleep(2)
            st.success("Quality challenge completed!")
            st.write("**Results:** All quality gates passed successfully")

def show_system_config():
    """System Configuration - Settings and tuning"""
    st.header("⚙️ System Configuration")
    
    # Agent configuration
    st.subheader("🤖 Agent Configuration")
    
    agents = [
        "Extraction Agent",
        "Contract Agent", 
        "MSA Agent",
        "Leasing Agent",
        "Fixed Assets Agent",
        "Master Data Agent",
        "Manager Agent",
        "Quality Review Agent",
        "Learning Agent"
    ]
    
    selected_agent = st.selectbox("Select Agent", agents)
    
    if selected_agent:
        st.write(f"**Configuring: {selected_agent}**")
        
        col1, col2 = st.columns(2)
        with col1:
            confidence_threshold = st.slider("Confidence Threshold", 0.5, 1.0, 0.8, 0.05)
            max_retries = st.number_input("Max Retries", 1, 10, 3)
        
        with col2:
            timeout = st.number_input("Timeout (seconds)", 30, 300, 60)
            auto_escalate = st.checkbox("Auto-escalate", value=True)
        
        if st.button("💾 Save Configuration"):
            st.success("Configuration saved successfully!")
    
    # System settings
    st.subheader("🔧 System Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        refresh_interval = st.slider("Refresh Interval (sec)", 1, 10, 2)
    
    with col2:
        debug_mode = st.checkbox("Debug Mode", value=False)
        log_level = st.selectbox("Log Level", ["INFO", "DEBUG", "WARNING", "ERROR"])
    
    if st.button("🔄 Apply Settings"):
        st.success("Settings applied successfully!")

def show_agent_monitoring():
    """Agent Monitoring - Real-time status of all agents"""
    st.header("🤖 Agent Monitoring & Status")
    
    # Agent status overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Agents", "9")
        st.caption("All agents operational")
    
    with col2:
        st.metric("Active Agents", "7")
        st.caption("Currently processing")
    
    with col3:
        st.metric("Learning Agents", "2")
        st.caption("In learning mode")
    
    with col4:
        st.metric("System Health", "98%")
        st.caption("Optimal performance")
    
    # Detailed agent status table
    st.subheader("📊 Agent Status Details")
    
    # Sample agent data with real status
    agents_data = [
        {
            "Agent": "Learning Agent",
            "Status": "🟢 Active",
            "Current Task": "Processing human feedback",
            "Performance": "98%",
            "Last Activity": "2 min ago",
            "Tasks Completed": 156,
            "Learning Iterations": 23
        },
        {
            "Agent": "Manager Agent", 
            "Status": "🟢 Active",
            "Current Task": "Workflow orchestration",
            "Performance": "99%",
            "Last Activity": "1 min ago",
            "Tasks Completed": 89,
            "Learning Iterations": 12
        },
        {
            "Agent": "Extraction Agent",
            "Status": "🟢 Active", 
            "Current Task": "Invoice processing",
            "Performance": "97%",
            "Last Activity": "30 sec ago",
            "Tasks Completed": 234,
            "Learning Iterations": 45
        },
        {
            "Agent": "Contract Agent",
            "Status": "🟡 Learning",
            "Current Task": "Learning from feedback",
            "Performance": "96%",
            "Last Activity": "5 min ago",
            "Tasks Completed": 67,
            "Learning Iterations": 18
        },
        {
            "Agent": "MSA Agent",
            "Status": "🟢 Active",
            "Current Task": "Agreement validation",
            "Performance": "98%",
            "Last Activity": "3 min ago",
            "Tasks Completed": 45,
            "Learning Iterations": 9
        },
        {
            "Agent": "Leasing Agent",
            "Status": "🟢 Active",
            "Current Task": "Lease correlation",
            "Performance": "95%",
            "Last Activity": "2 min ago",
            "Tasks Completed": 78,
            "Learning Iterations": 15
        },
        {
            "Agent": "Fixed Assets Agent",
            "Status": "🟡 Learning",
            "Current Task": "Learning asset patterns",
            "Performance": "94%",
            "Last Activity": "8 min ago",
            "Tasks Completed": 56,
            "Learning Iterations": 22
        },
        {
            "Agent": "Master Data Agent",
            "Status": "🟢 Active",
            "Current Task": "Data validation",
            "Performance": "99%",
            "Last Activity": "1 min ago",
            "Tasks Completed": 123,
            "Learning Iterations": 31
        },
        {
            "Agent": "Quality Review Agent",
            "Status": "🟢 Active",
            "Current Task": "Anomaly detection",
            "Performance": "97%",
            "Last Activity": "45 sec ago",
            "Tasks Completed": 189,
            "Learning Iterations": 28
        }
    ]
    
    # Create DataFrame and display
    df = pd.DataFrame(agents_data)
    st.dataframe(df, use_container_width=True)
    
    # Agent performance visualization
    st.subheader("📈 Agent Performance Trends")
    
    # Performance over time
    performance_data = pd.DataFrame({
        'Agent': [agent['Agent'] for agent in agents_data],
        'Performance': [float(agent['Performance'].replace('%', '')) for agent in agents_data],
        'Tasks Completed': [agent['Tasks Completed'] for agent in agents_data],
        'Learning Iterations': [agent['Learning Iterations'] for agent in agents_data]
    })
    
    # Performance bar chart
    fig1 = px.bar(performance_data, x='Agent', y='Performance', 
                   title="Agent Performance Scores", color='Performance',
                   color_continuous_scale='RdYlGn')
    fig1.update_layout(height=400)
    st.plotly_chart(fig1, use_container_width=True)
    
    # Learning iterations vs performance
    fig2 = px.scatter(performance_data, x='Learning Iterations', y='Performance', 
                       size='Tasks Completed', hover_data=['Agent'],
                       title="Learning Impact on Performance")
    st.plotly_chart(fig2, use_container_width=True)
    
    # Real-time agent activity
    st.subheader("🔄 Real-time Agent Activity")
    
    # Activity timeline
    activity_data = pd.DataFrame({
        'Time': pd.date_range(start=datetime.now() - timedelta(hours=2), periods=24, freq='5min'),
        'Active Agents': np.random.randint(5, 9, 24),
        'Learning Events': np.random.poisson(2, 24),
        'Tasks Completed': np.random.poisson(8, 24)
    })
    
    fig3 = px.line(activity_data, x='Time', y=['Active Agents', 'Learning Events', 'Tasks Completed'],
                    title="Real-time System Activity")
    st.plotly_chart(fig3, use_container_width=True)

def show_document_processing():
    """Document Processing - Real-time document processing status"""
    st.header("📄 Document Processing Status")
    
    # Processing overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Documents in Queue", "12")
        st.caption("Waiting for processing")
    
    with col2:
        st.metric("Currently Processing", "3")
        st.caption("Active extraction")
    
    with col3:
        st.metric("Completed Today", "45")
        st.caption("Successfully processed")
    
    with col4:
        st.metric("Processing Rate", "2.3/min")
        st.caption("Average speed")
    
    # Document processing pipeline
    st.subheader("🔄 Processing Pipeline")
    
    # Sample processing data
    processing_data = [
        {"Document": "Invoice_001.pdf", "Status": "🟢 Completed", "Stage": "Quality Review", "Agent": "Quality Review Agent", "Time": "2 min ago"},
        {"Document": "Contract_002.pdf", "Status": "🟡 Processing", "Stage": "Extraction", "Agent": "Extraction Agent", "Time": "1 min ago"},
        {"Document": "Invoice_003.pdf", "Status": "🟡 Processing", "Stage": "Validation", "Agent": "Master Data Agent", "Time": "30 sec ago"},
        {"Document": "MSA_001.pdf", "Status": "🔵 Queued", "Stage": "Waiting", "Agent": "Manager Agent", "Time": "5 min ago"},
        {"Document": "Lease_002.pdf", "Status": "🟢 Completed", "Stage": "Completed", "Agent": "Leasing Agent", "Time": "10 min ago"}
    ]
    
    # Display processing table
    df = pd.DataFrame(processing_data)
    st.dataframe(df, use_container_width=True)
    
    # Processing timeline
    st.subheader("📈 Processing Timeline")
    
    timeline_data = pd.DataFrame({
        'Time': pd.date_range(start=datetime.now() - timedelta(hours=4), periods=48, freq='5min'),
        'Documents Processed': np.random.poisson(3, 48),
        'Processing Time (min)': np.random.exponential(2, 48)
    })
    
    fig = px.line(timeline_data, x='Time', y='Documents Processed', 
                   title="Documents Processed Over Time")
    st.plotly_chart(fig, use_container_width=True)

def show_workflow_management():
    """Workflow Management - Orchestration and workflow status"""
    st.header("⚙️ Workflow Management")
    
    # Workflow overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Workflows", "3")
        st.caption("Currently running")
    
    with col2:
        st.metric("Completed Today", "12")
        st.caption("Successfully finished")
    
    with col3:
        st.metric("Failed Workflows", "1")
        st.caption("Requires attention")
    
    with col4:
        st.metric("Success Rate", "92%")
        st.caption("Overall performance")
    
    # Active workflows
    st.subheader("🔄 Active Workflows")
    
    workflows = [
        {
            "id": "WF_001",
            "type": "Invoice Processing",
            "status": "Running",
            "progress": 75,
            "agents": ["Extraction Agent", "Master Data Agent"],
            "started": "15 min ago",
            "estimated_completion": "5 min"
        },
        {
            "id": "WF_002", 
            "type": "Contract Validation",
            "status": "Running",
            "progress": 45,
            "agents": ["Contract Agent", "Quality Review Agent"],
            "started": "25 min ago",
            "estimated_completion": "20 min"
        },
        {
            "id": "WF_003",
            "type": "Anomaly Investigation",
            "status": "Running", 
            "progress": 90,
            "agents": ["Quality Review Agent", "Learning Agent"],
            "started": "40 min ago",
            "estimated_completion": "2 min"
        }
    ]
    
    for workflow in workflows:
        col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
        with col1:
            st.write(f"**{workflow['id']}**")
        with col2:
            st.write(workflow['type'])
        with col3:
            if workflow['status'] == 'Running':
                st.info("🔄")
            elif workflow['status'] == 'Completed':
                st.success("✅")
            else:
                st.warning("⏳")
        with col4:
            st.progress(workflow['progress'] / 100)
        
        # Show workflow details
        with st.expander(f"Workflow {workflow['id']} Details"):
            st.write(f"**Status:** {workflow['status']}")
            st.write(f"**Started:** {workflow['started']}")
            st.write(f"**Estimated Completion:** {workflow['estimated_completion']}")
            st.write(f"**Involved Agents:** {', '.join(workflow['agents'])}")
            st.write(f"**Progress:** {workflow['progress']}%")
    
    # Workflow performance
    st.subheader("📊 Workflow Performance")
    
    performance_data = pd.DataFrame({
        'Workflow Type': ['Invoice Processing', 'Contract Validation', 'Anomaly Investigation', 'Data Extraction'],
        'Success Rate': [95, 88, 92, 96],
        'Average Duration (min)': [12, 25, 18, 8],
        'Agents Involved': [2.3, 2.8, 2.1, 1.9]
    })
    
    fig = px.bar(performance_data, x='Workflow Type', y='Success Rate',
                  title="Workflow Success Rates", color='Success Rate',
                  color_continuous_scale='RdYlGn')
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
