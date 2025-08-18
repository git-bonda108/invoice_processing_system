#!/usr/bin/env python3
"""
Quick test to verify Phase 1 setup
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def quick_test():
    print("🧪 QUICK PHASE 1 TEST")
    print("=" * 40)
    
    try:
        # Test imports
        print("Testing imports...")
        from config.settings import DATA_DIR, AGENT_CONFIG
        from utils.message_queue import MessageQueue, Message, MessageType
        from agents.base_agent import BaseAgent, AgentStatus
        print("✅ All imports successful")
        
        # Test data directory
        print(f"Data directory: {DATA_DIR}")
        print(f"Data directory exists: {DATA_DIR.exists()}")
        
        # Test sample file
        sample_invoice = DATA_DIR / "invoices" / "invoice_001.json"
        print(f"Sample invoice exists: {sample_invoice.exists()}")
        
        if sample_invoice.exists():
            import json
            with open(sample_invoice, 'r') as f:
                invoice = json.load(f)
            print(f"Sample invoice number: {invoice.get('invoice_number', 'N/A')}")
            print(f"Sample invoice amount: ${invoice.get('total_amount', 0):,.2f}")
        
        # Test message queue
        print("Testing message queue...")
        queue = MessageQueue()
        message = Message(
            msg_type=MessageType.TASK_ASSIGNMENT,
            sender="test",
            recipient="test",
            content={"test": "data"}
        )
        queue.send_message(message)
        received = queue.get_message("test")
        print(f"Message queue test: {'✅ Success' if received else '❌ Failed'}")
        
        print("\n🎉 QUICK TEST PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)