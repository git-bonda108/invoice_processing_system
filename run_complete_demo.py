"""
Complete Agentic AI System Demonstration
Runs both workflow orchestration and state management demonstrations
"""

import time
import sys
from pathlib import Path

def run_complete_demo():
    """Run the complete system demonstration"""
    print("🚀 COMPLETE AGENTIC AI SYSTEM DEMONSTRATION")
    print("=" * 100)
    print("This demonstration showcases:")
    print("1. 🤖 Workflow Orchestration - How 9 agents collaborate")
    print("2. 🎯 State Management - How Manager Agent coordinates everything")
    print("3. 📊 Real-time Monitoring - Live status and metrics")
    print("4. 🔄 Agent Collaboration - Autonomous decision making")
    print("=" * 100)
    
    # Run workflow orchestration demo
    print("\n🎬 PART 1: WORKFLOW ORCHESTRATION DEMONSTRATION")
    print("-" * 60)
    
    try:
        from demo_workflow_orchestration import WorkflowDemonstration
        
        demo = WorkflowDemonstration()
        demo.run_demonstration()
        
        print("\n✅ Workflow Orchestration Demo Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Error in workflow orchestration demo: {e}")
        return
    
    # Brief pause between demos
    print("\n" + "=" * 100)
    print("🔄 Transitioning to State Management Demonstration...")
    print("=" * 100)
    time.sleep(3)
    
    # Run state management demo
    print("\n🎬 PART 2: STATE MANAGEMENT & COORDINATION DEMONSTRATION")
    print("-" * 60)
    
    try:
        from demo_state_management import run_state_management_demo
        
        run_state_management_demo()
        
        print("\n✅ State Management Demo Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Error in state management demo: {e}")
        return
    
    # Final summary
    print("\n" + "=" * 100)
    print("🎉 COMPLETE DEMONSTRATION SUCCESSFULLY COMPLETED!")
    print("=" * 100)
    
    print("\n📋 WHAT WAS DEMONSTRATED:")
    print("✅ Multi-Agent Workflow Orchestration")
    print("✅ Autonomous Agent Collaboration")
    print("✅ Centralized State Management")
    print("✅ Real-time Status Tracking")
    print("✅ Anomaly Detection & Risk Assessment")
    print("✅ Human-in-the-Loop Escalation")
    print("✅ Performance Metrics & Analytics")
    print("✅ Full Audit Trail & State History")
    
    print("\n🤖 AGENTS INVOLVED:")
    print("• Extraction Agent - Data extraction & OCR")
    print("• Contract Agent - Contract validation")
    print("• MSA Agent - Master Service Agreement validation")
    print("• Leasing Agent - Lease agreement validation")
    print("• Fixed Assets Agent - Asset tracking")
    print("• Master Data Agent - Data validation")
    print("• Quality Review Agent - Anomaly detection")
    print("• Learning Agent - Feedback processing")
    print("• Manager Agent - Orchestration & state management")
    
    print("\n🎯 KEY BENEFITS DEMONSTRATED:")
    print("• Complete autonomy - Agents work without human intervention")
    print("• Scalable architecture - Handles multiple workflows simultaneously")
    print("• Real-time monitoring - Live status updates throughout")
    print("• Intelligent decision making - AI-powered approval/rejection")
    print("• Human oversight - Escalation when needed")
    print("• Continuous learning - System improves over time")
    
    print("\n💡 READY FOR STAKEHOLDER PRESENTATION!")
    print("This demonstration shows a production-ready Agentic AI system")
    print("that can process invoices, contracts, and other documents")
    print("with full automation and intelligent oversight.")

def check_dependencies():
    """Check if all required files exist"""
    required_files = [
        "demo_workflow_orchestration.py",
        "demo_state_management.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required demonstration files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all demonstration files are present.")
        return False
    
    return True

def main():
    """Main function"""
    print("🔍 Checking system readiness...")
    
    if not check_dependencies():
        print("❌ System not ready for demonstration")
        sys.exit(1)
    
    print("✅ All dependencies found. Starting demonstration...")
    time.sleep(2)
    
    try:
        run_complete_demo()
    except KeyboardInterrupt:
        print("\n\n⏹️ Demonstration interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during demonstration: {e}")
        print("Please check the system and try again.")

if __name__ == "__main__":
    main()
