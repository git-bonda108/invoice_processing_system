"""
Agentic AI Dashboard - Cloud-Ready Version for Streamlit Cloud
"""
import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np
from typing import Dict, List, Any, Optional
import os

# Page configuration
st.set_page_config(
    page_title="🤖 Agentic AI - Invoice Processing Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'workflow_status' not in st.session_state:
    st.session_state.workflow_status = {}
if 'agent_status' not in st.session_state:
    st.session_state.agent_status = {}

def load_sample_data():
    """Load sample data for display"""
    # For cloud deployment, we'll use sample data
    sample_invoices = [
        {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-10-15",
            "total_amount": 12960.00,
            "buyers_order_number": "PO-123456",
            "vendor_name": "TechCorp Solutions Inc.",
            "buyer_name": "Acme Corporation"
        },
        {
            "invoice_number": "INV-2024-002",
            "invoice_date": "2024-10-16",
            "total_amount": 8500.00,
            "buyers_order_number": "PO-123457",
            "vendor_name": "Innovation Systems Ltd.",
            "buyer_name": "Acme Corporation"
        },
        {
            "invoice_number": "INV-2024-003",
            "invoice_date": "2024-10-17",
            "total_amount": 15600.00,
            "buyers_order_number": "PO-123458",
            "vendor_name": "Global Tech Solutions",
            "buyer_name": "Acme Corporation"
        }
    ]
    
    sample_contracts = [
        {
            "contract_number": "CON-2024-001",
            "contract_type": "Service Agreement",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "contract_value": 150000.00,
            "po_references": ["PO-123456", "PO-123457"]
        },
        {
            "contract_number": "CON-2024-002",
            "contract_type": "Supply Contract",
            "start_date": "2024-02-01",
            "end_date": "2024-12-31",
            "contract_value": 75000.00,
            "po_references": ["PO-123458"]
        }
    ]
    
    return {
        "invoices": sample_invoices,
        "contracts": sample_contracts,
        "msa": [{"name": "Master Service Agreement 2024"}],
        "leases": [{"name": "Office Space Lease"}],
        "fixed_assets": [{"name": "Computer Equipment"}],
        "master_data": {"vendors": 15, "buyers": 8}
    }

def main():
    """Main Streamlit application"""
    
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
                "🏠 System Dashboard",
                "📤 Upload Centre", 
                "📊 Live Monitor",
                "💬 Conversations",
                "🚨 Anomalies",
                "🧠 Learning Insights",
                "👨‍💼 Manager Panel",
                "⚙️ System Config"
            ]
        )
        
        # System status in sidebar
        st.subheader("System Status")
        st.success("✅ System Active")
        
        # Quick actions
        st.subheader("Quick Actions")
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        if st.button("📊 Generate Report"):
            st.info("Generating report...")
    
    # Main content area based on navigation
    if page == "🏠 System Dashboard":
        show_system_dashboard()
    elif page == "📤 Upload Centre":
        show_upload_centre()
    elif page == "📊 Live Monitor":
        show_live_monitor()
    elif page == "💬 Conversations":
        show_conversations()
    elif page == "🚨 Anomalies":
        show_anomalies()
    elif page == "🧠 Learning Insights":
        show_learning_insights()
    elif page == "👨‍💼 Manager Panel":
        show_manager_panel()
    elif page == "⚙️ System Config":
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
        {"name": "Learning Agent", "status": "status": "Active", "tasks": 5, "success_rate": "95%"}
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
            "Manager Agent",
            "Extraction Agent", 
            "Contract Agent",
            "MSA Agent",
            "Leasing Agent",
            "Fixed Assets Agent",
            "Master Data Agent",
            "Quality Review Agent",
            "Learning Agent"
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
        
        # Generate AI response
        with st.chat_message("assistant"):
            response = generate_ai_response(prompt, agent)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

def generate_ai_response(prompt: str, agent: str) -> str:
    """Generate AI response based on prompt and agent"""
    prompt_lower = prompt.lower()
    
    if "status" in prompt_lower:
        return f"The {agent} is currently active and processing tasks. How can I help you?"
    
    elif "anomaly" in prompt_lower:
        return f"I can help you with anomaly detection. The {agent} has identified several patterns. What specific information do you need?"
    
    elif "workflow" in prompt_lower:
        return f"Current workflows are being managed by the {agent}. Would you like me to show you the detailed status?"
    
    else:
        return f"I understand your question. As the {agent}, I can help you with various tasks. Could you please be more specific?"

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

if __name__ == "__main__":
    main()
