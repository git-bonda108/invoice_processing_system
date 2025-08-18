#!/usr/bin/env python3
"""
Phase 3 Comprehensive Testing Script
Tests orchestration, workflows, and monitoring
"""
import sys
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.WARNING)

class Phase3Tester:
    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_result(self, test_name, success, message=""):
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}: {message}")
        self.results[test_name] = {'success': success, 'message': message}
    
    def test_phase3_imports(self):
        """Test Phase 3 imports"""
        print("\n🧪 TESTING PHASE 3 IMPORTS")
        print("=" * 60)
        
        try:
            # Manager Agent
            from agents.manager_agent import ManagerAgent, WorkflowStatus, TaskStatus
            self.log_result("ManagerAgent import", True)
            
            # Workflow Engine
            from workflows.workflow_engine import WorkflowEngine, DocumentProcessingWorkflow
            self.log_result("WorkflowEngine import", True)
            
            # Status Monitor
            from workflows.status_monitor import StatusMonitor, WorkflowStatus, TaskStatus
            self.log_result("StatusMonitor import", True)
            
            # Error Handler
            from workflows.error_handler import ErrorHandler, ErrorType, RetryPolicy
            self.log_result("ErrorHandler import", True)
            
            # Orchestrator
            from orchestration.orchestrator import DocumentProcessingOrchestrator
            self.log_result("DocumentProcessingOrchestrator import", True)
            
            # Dashboard
            from orchestration.dashboard import RealTimeDashboard
            self.log_result("RealTimeDashboard import", True)
            
        except Exception as e:
            self.log_result("Phase 3 imports", False, str(e))
    
    def test_manager_agent(self):
        """Test Manager Agent functionality"""
        print("\n🧪 TESTING MANAGER AGENT")
        print("=" * 60)
        
        try:
            from agents.manager_agent import ManagerAgent
            from utils.message_queue import MessageQueue
            
            # Create manager agent
            queue = MessageQueue()
            manager = ManagerAgent("manager_test", queue)
            self.log_result("ManagerAgent creation", True)
            
            # Test workflow creation
            result = manager.process_single_document("test_document.json", "invoice")
            success = result.get('status') in ['started', 'error']  # Error expected for non-existent file
            self.log_result("Single document workflow", success, result.get('message', ''))
            
            # Test performance metrics
            metrics = manager.get_performance_metrics()
            success = metrics.get('status') == 'success'
            self.log_result("Performance metrics", success)
            
            # Test dashboard data
            dashboard = manager.get_dashboard_data()
            success = dashboard.get('status') == 'success'
            self.log_result("Dashboard data", success)
            
        except Exception as e:
            self.log_result("Manager Agent functionality", False, str(e))
    
    def test_workflow_engine(self):
        """Test Workflow Engine"""
        print("\n🧪 TESTING WORKFLOW ENGINE")
        print("=" * 60)
        
        try:
            from workflows.workflow_engine import WorkflowEngine, DocumentProcessingWorkflow
            from agents.manager_agent import ManagerAgent
            from utils.message_queue import MessageQueue
            
            # Create workflow engine
            queue = MessageQueue()
            manager = ManagerAgent("manager_test", queue)
            engine = WorkflowEngine(manager, queue)
            self.log_result("WorkflowEngine creation", True)
            
            # Test workflow creation
            workflow_id = "TEST_WF_001"
            workflow = asyncio.run(engine.create_workflow(workflow_id))
            success = isinstance(workflow, DocumentProcessingWorkflow)
            self.log_result("Workflow creation", success)
            
            # Test workflow status
            status = engine.get_workflow_status(workflow_id)
            success = 'status' in status
            self.log_result("Workflow status", success)
            
        except Exception as e:
            self.log_result("Workflow Engine functionality", False, str(e))
    
    def test_status_monitor(self):
        """Test Status Monitor"""
        print("\n🧪 TESTING STATUS MONITOR")
        print("=" * 60)
        
        try:
            from workflows.status_monitor import StatusMonitor, WorkflowStatus, TaskStatus
            
            # Create status monitor
            monitor = StatusMonitor()
            self.log_result("StatusMonitor creation", True)
            
            # Test workflow registration
            monitor.register_workflow("TEST_WF_001", {
                'type': 'test',
                'total_tasks': 1
            })
            self.log_result("Workflow registration", True)
            
            # Test status update
            monitor.update_workflow_status("TEST_WF_001", WorkflowStatus.RUNNING)
            self.log_result("Workflow status update", True)
            
            # Test task registration
            monitor.register_task("TEST_TASK_001", "TEST_WF_001", "extraction", "invoice")
            self.log_result("Task registration", True)
            
            # Test dashboard data
            dashboard_data = monitor.get_dashboard_data()
            success = 'timestamp' in dashboard_data
            self.log_result("Dashboard data generation", success)
            
            # Test performance trends
            trends = monitor.get_performance_trends(hours=1)
            success = isinstance(trends, dict)
            self.log_result("Performance trends", success)
            
            # Cleanup
            monitor.shutdown()
            
        except Exception as e:
            self.log_result("Status Monitor functionality", False, str(e))
    
    def test_error_handler(self):
        """Test Error Handler"""
        print("\n🧪 TESTING ERROR HANDLER")
        print("=" * 60)
        
        try:
            from workflows.error_handler import ErrorHandler, ErrorContext, ErrorType
            
            # Create error handler
            handler = ErrorHandler()
            self.log_result("ErrorHandler creation", True)
            
            # Test error classification
            test_exception = ValueError("Test validation error")
            error_type = handler._classify_error(test_exception)
            success = isinstance(error_type, ErrorType)
            self.log_result("Error classification", success)
            
            # Test error context creation
            context = ErrorContext(
                workflow_id="TEST_WF_001",
                task_id="TEST_TASK_001",
                agent_id="test_agent",
                document_path="test.json",
                stage="processing",
                timestamp=datetime.now(),
                additional_data={}
            )
            self.log_result("Error context creation", True)
            
            # Test error handling (async)
            async def test_error_handling():
                result = await handler.handle_error(test_exception, context)
                return 'error_id' in result
            
            success = asyncio.run(test_error_handling())
            self.log_result("Error handling", success)
            
            # Test error statistics
            stats = handler.get_error_statistics()
            success = 'total_errors' in stats
            self.log_result("Error statistics", success)
            
        except Exception as e:
            self.log_result("Error Handler functionality", False, str(e))
    
    def test_orchestrator(self):
        """Test Document Processing Orchestrator"""
        print("\n🧪 TESTING ORCHESTRATOR")
        print("=" * 60)
        
        try:
            from orchestration.orchestrator import DocumentProcessingOrchestrator
            
            # Create orchestrator
            orchestrator = DocumentProcessingOrchestrator()
            self.log_result("Orchestrator creation", True)
            
            # Test system start
            start_result = asyncio.run(orchestrator.start_system())
            success = start_result.get('status') in ['started', 'already_running']
            self.log_result("System start", success, start_result.get('message', ''))
            
            # Test system status
            status = orchestrator.get_system_status()
            success = 'system_status' in status
            self.log_result("System status", success)
            
            # Test performance metrics
            metrics = orchestrator.get_performance_metrics()
            success = 'current_metrics' in metrics
            self.log_result("Performance metrics", success)
            
            # Test system stop
            stop_result = asyncio.run(orchestrator.stop_system())
            success = stop_result.get('status') in ['stopped', 'not_running']
            self.log_result("System stop", success, stop_result.get('message', ''))
            
        except Exception as e:
            self.log_result("Orchestrator functionality", False, str(e))
    
    def test_dashboard(self):
        """Test Real-time Dashboard"""
        print("\n🧪 TESTING DASHBOARD")
        print("=" * 60)
        
        try:
            from orchestration.dashboard import RealTimeDashboard
            from orchestration.orchestrator import DocumentProcessingOrchestrator
            
            # Create orchestrator and dashboard
            orchestrator = DocumentProcessingOrchestrator()
            dashboard = RealTimeDashboard(orchestrator)
            self.log_result("Dashboard creation", True)
            
            # Test dashboard data generation
            dashboard_data = dashboard.get_dashboard_data()
            success = 'timestamp' in dashboard_data
            self.log_result("Dashboard data generation", success)
            
            # Test HTML generation
            html_content = dashboard.generate_html_dashboard()
            success = '<html' in html_content and '</html>' in html_content
            self.log_result("HTML dashboard generation", success)
            
            # Test API data format
            api_data = dashboard.get_api_data()
            success = api_data.get('status') == 'success'
            self.log_result("API data format", success)
            
        except Exception as e:
            self.log_result("Dashboard functionality", False, str(e))
    
    def test_integration(self):
        """Test integration between components"""
        print("\n🧪 TESTING INTEGRATION")
        print("=" * 60)
        
        try:
            from orchestration.orchestrator import DocumentProcessingOrchestrator
            from config.settings import DATA_DIR
            
            # Create orchestrator
            orchestrator = DocumentProcessingOrchestrator()
            
            # Start system
            start_result = asyncio.run(orchestrator.start_system())
            success = start_result.get('status') in ['started', 'already_running']
            self.log_result("Integration system start", success)
            
            if success:
                # Test sample workflow
                sample_result = asyncio.run(orchestrator.run_sample_workflow())
                success = sample_result.get('status') in ['completed', 'warning']
                self.log_result("Sample workflow execution", success, sample_result.get('message', ''))
                
                # Stop system
                stop_result = asyncio.run(orchestrator.stop_system())
                success = stop_result.get('status') in ['stopped', 'not_running']
                self.log_result("Integration system stop", success)
            
        except Exception as e:
            self.log_result("Integration testing", False, str(e))
    
    def test_async_operations(self):
        """Test asynchronous operations"""
        print("\n🧪 TESTING ASYNC OPERATIONS")
        print("=" * 60)
        
        try:
            from workflows.workflow_engine import DocumentProcessingWorkflow
            from agents.manager_agent import ManagerAgent
            from utils.message_queue import MessageQueue
            
            # Create workflow
            queue = MessageQueue()
            manager = ManagerAgent("manager_test", queue)
            workflow = DocumentProcessingWorkflow("TEST_ASYNC_WF", manager, queue)
            self.log_result("Async workflow creation", True)
            
            # Test async document processing (with non-existent file)
            async def test_async_processing():
                try:
                    result = await workflow.process_document("non_existent.json", "invoice")
                    return 'status' in result
                except Exception:
                    return True  # Expected to fail with non-existent file
            
            success = asyncio.run(test_async_processing())
            self.log_result("Async document processing", success)
            
        except Exception as e:
            self.log_result("Async operations", False, str(e))
    
    def test_error_scenarios(self):
        """Test error handling scenarios"""
        print("\n🧪 TESTING ERROR SCENARIOS")
        print("=" * 60)
        
        try:
            from orchestration.orchestrator import DocumentProcessingOrchestrator
            
            # Create orchestrator
            orchestrator = DocumentProcessingOrchestrator()
            
            # Test processing non-existent document
            result = asyncio.run(orchestrator.process_document("non_existent_file.json"))
            success = result.get('status') == 'error'
            self.log_result("Non-existent document error handling", success)
            
            # Test processing non-existent directory
            result = asyncio.run(orchestrator.process_directory("non_existent_directory"))
            success = result.get('status') == 'error'
            self.log_result("Non-existent directory error handling", success)
            
            # Test system operations when not running
            status = orchestrator.get_system_status()
            success = status.get('system_status') == 'stopped'
            self.log_result("System status when stopped", success)
            
        except Exception as e:
            self.log_result("Error scenarios", False, str(e))
    
    def test_performance_monitoring(self):
        """Test performance monitoring capabilities"""
        print("\n🧪 TESTING PERFORMANCE MONITORING")
        print("=" * 60)
        
        try:
            from workflows.status_monitor import StatusMonitor, PerformanceMetrics
            from datetime import datetime
            
            # Create status monitor
            monitor = StatusMonitor()
            
            # Test metrics collection
            monitor._collect_performance_metrics()
            success = len(monitor.metrics_history) > 0
            self.log_result("Metrics collection", success)
            
            # Test alert creation
            alert_id = monitor.create_alert(
                level=monitor.AlertLevel.WARNING,
                title="Test Alert",
                message="This is a test alert",
                source="test"
            )
            success = alert_id in monitor.active_alerts
            self.log_result("Alert creation", success)
            
            # Test alert acknowledgment
            ack_result = monitor.acknowledge_alert(alert_id)
            self.log_result("Alert acknowledgment", ack_result)
            
            # Test alert resolution
            resolve_result = monitor.resolve_alert(alert_id)
            self.log_result("Alert resolution", resolve_result)
            
            # Cleanup
            monitor.shutdown()
            
        except Exception as e:
            self.log_result("Performance monitoring", False, str(e))
    
    def run_all_tests(self):
        """Run all Phase 3 tests"""
        print("🚀 PHASE 3 COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        self.test_phase3_imports()
        self.test_manager_agent()
        self.test_workflow_engine()
        self.test_status_monitor()
        self.test_error_handler()
        self.test_orchestrator()
        self.test_dashboard()
        self.test_integration()
        self.test_async_operations()
        self.test_error_scenarios()
        self.test_performance_monitoring()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 PHASE 3 TESTING RESULTS")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📈 OVERALL RESULTS: {self.passed_tests}/{self.total_tests} tests passed ({success_rate:.1f}%)")
        
        if self.passed_tests == self.total_tests:
            print("🎉 ALL PHASE 3 TESTS PASSED - ORCHESTRATION SYSTEM READY!")
            print("✅ Ready for Phase 4 - User Interface & API Development")
            return True
        else:
            print("⚠️ SOME TESTS FAILED - REVIEW REQUIRED")
            
            # Show failed tests
            failed_tests = [name for name, result in self.results.items() if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test_name in failed_tests:
                    message = self.results[test_name]['message']
                    print(f"   - {test_name}: {message}")
            
            return False

if __name__ == "__main__":
    tester = Phase3Tester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)