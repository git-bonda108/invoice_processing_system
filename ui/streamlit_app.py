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
            file_path = Path("data/invoices") / f"invoice_{i:03d}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data["invoices"].append(json.load(f))
        
        # Load contracts
        for i in range(1, 4):
            file_path = Path("data/contracts") / f"contract_{i:03d}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data["contracts"].append(json.load(f))
        
        # Load MSA
        msa_path = Path("data/msa") / "msa_001.json"
        if msa_path.exists():
            with open(msa_path, 'r') as f:
                data["msa"].append(json.load(f))
        
        # Load leases
        for i in range(1, 4):
            file_path = Path("data/leases") / f"lease_{i:03d}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data["leases"].append(json.load(f))
        
        # Load fixed assets
        for i in range(1, 4):
            file_path = Path("data/fixed_assets") / f"fixed_asset_{i:03d}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data["fixed_assets"].append(json.load(f))
        
        # Load master data
        master_path = Path("data/master_data") / "master_data.json"
        if master_path.exists():
            with open(master_path, 'r') as f:
                data["master_data"] = json.load(f)
                
    except Exception as e:
        st.error(f"Error loading data: {e}")
    
    return data

def show_system_dashboard():
    """System Dashboard - Main overview"""
    st.header("🏠 System Dashboard")
    
    # System status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🤖 Active Agents", "9", "All Operational")
    
    with col2:
        st.metric("📊 Processing Rate", "25+", "invoices/min")
    
    with col3:
        st.metric("🎯 Success Rate", "98.5%", "accuracy")
    
    with col4:
        st.metric("⚡ Response Time", "2.3s", "average")
    
    # Processing pipeline funnel
    st.subheader("📊 Document Processing Pipeline")
    
    fig = go.Figure(go.Funnel(
        y=["Uploaded", "Extracted", "Validated", "Reviewed", "Approved"],
        x=[100, 95, 92, 89, 87],
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
    
    # Display agent status in a table
    agent_df = pd.DataFrame(agents)
    st.dataframe(agent_df, use_container_width=True)
    
    # Real-time workflow
    st.subheader("🔄 Live Workflow")
    
    # Simulate real-time updates
    if st.button("🔄 Refresh Status"):
        st.rerun()
    
    # Show sample workflow
    workflow_data = [
        {"Document": "INV-2024-001", "Stage": "Extraction", "Agent": "Extraction Agent", "Status": "Completed"},
        {"Document": "INV-2024-002", "Stage": "Contract Validation", "Agent": "Contract Agent", "Status": "In Progress"},
        {"Document": "CON-2024-001", "Stage": "MSA Review", "Agent": "MSA Agent", "Status": "Pending"},
        {"Document": "LEASE-2024-001", "Stage": "Lease Validation", "Agent": "Leasing Agent", "Status": "Completed"}
    ]
    
    workflow_df = pd.DataFrame(workflow_data)
    st.dataframe(workflow_df, use_container_width=True)

def show_conversations():
    """Conversations - Human-in-the-loop interactions"""
    st.header("💬 Conversations")
    
    # Chat interface
    st.subheader("🤖 AI Agent Chat")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about invoice processing, anomalies, or system status..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            response = generate_ai_response(prompt)
            st.markdown(response)
        
        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

def generate_ai_response(prompt: str) -> str:
    """Generate AI response based on user prompt"""
    prompt_lower = prompt.lower()
    
    if "invoice" in prompt_lower:
        return "I can help you with invoice processing! Our Extraction Agent automatically extracts key information like invoice numbers, amounts, PO numbers, and vendor details. What specific aspect would you like to know more about?"
    
    elif "anomaly" in prompt_lower or "error" in prompt_lower:
        return "Anomaly detection is one of our core strengths! Our Quality Review Agent cross-references data across all agents to identify discrepancies like missing POs, vendor mismatches, or amount variances. Would you like me to show you some examples?"
    
    elif "agent" in prompt_lower:
        return "We have 9 specialized agents working together: Extraction, Contract, MSA, Leasing, Fixed Assets, Master Data, Manager, Quality Review, and Learning. Each agent is an expert in their domain and works autonomously. Which agent would you like to learn more about?"
    
    elif "status" in prompt_lower:
        return "All 9 agents are currently active and operational! Our system is processing documents at 25+ per minute with 98.5% accuracy. You can check the Live Monitor tab for real-time status updates."
    
    else:
        return "I'm here to help with your invoice processing and anomaly detection system! You can ask me about invoices, anomalies, agents, system status, or any other aspect of our AI-powered workflow."

def show_analytics():
    """Analytics - Performance and insights"""
    st.header("📊 Analytics & Insights")
    
    # Performance metrics
    st.subheader("🎯 Performance Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Documents", "1,247", "+12% from last week")
    
    with col2:
        st.metric("Anomalies Detected", "23", "-5% from last week")
    
    with col3:
        st.metric("Processing Time", "2.3s", "-0.5s from last week")
    
    # Anomaly breakdown
    st.subheader("🚨 Anomaly Breakdown")
    
    anomaly_data = {
        "Type": ["Missing PO", "Vendor Mismatch", "Amount Variance", "Date Issues", "Contract Mismatch"],
        "Count": [8, 5, 4, 3, 3],
        "Risk Level": ["High", "Critical", "Medium", "Low", "High"]
    }
    
    anomaly_df = pd.DataFrame(anomaly_data)
    st.dataframe(anomaly_df, use_container_width=True)
    
    # Anomaly chart
    fig = px.bar(anomaly_df, x="Type", y="Count", color="Risk Level", 
                 title="Anomaly Types and Risk Levels")
    st.plotly_chart(fig, use_container_width=True)

def main():
    """Main Streamlit application - Agentic AI Dashboard"""
    st.set_page_config(
        page_title="🤖 Agentic AI - Invoice Processing Dashboard",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize system
    system_status = initialize_system()
    
    if not system_status["initialized"]:
        st.error("Failed to initialize system")
        return
    
    # Sidebar navigation
    st.sidebar.title("🤖 Agentic AI System")
    st.sidebar.markdown("---")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["🏠 System Dashboard", "📤 Upload Centre", "📊 Live Monitor", "💬 Conversations", "📊 Analytics"]
    )
    
    # Load sample data
    data = load_sample_data()
    
    # Display selected page
    if page == "🏠 System Dashboard":
        show_system_dashboard()
    elif page == "📤 Upload Centre":
        show_upload_centre()
    elif page == "📊 Live Monitor":
        show_live_monitor()
    elif page == "💬 Conversations":
        show_conversations()
    elif page == "📊 Analytics":
        show_analytics()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**System Status:** 🟢 Active")
    st.sidebar.markdown("**Last Updated:** " + datetime.now().strftime("%H:%M:%S"))

if __name__ == "__main__":
    main()
