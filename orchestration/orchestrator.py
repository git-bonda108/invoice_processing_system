"""
Document Processing Orchestrator - Main orchestration system
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

# Import all agents
from agents.manager_agent import ManagerAgent
from agents.master_data_agent import MasterDataAgent
from agents.extraction_agent import ExtractionAgent
from agents.contract_agent import ContractAgent
from agents.msa_agent import MSAAgent
from agents.leasing_agent import LeasingAgent
from agents.fixed_assets_agent import FixedAssetsAgent
from agents.quality_review_agent import QualityReviewAgent

# Import workflow components
from workflows.workflow_engine import WorkflowEngine, DocumentProcessingWorkflow
from workflows.status_monitor import StatusMonitor, WorkflowStatus, TaskStatus
from workflows.error_handler import ErrorHandler, ErrorContext

# Import utilities
from utils.message_queue import MessageQueue, Message, MessageType
from config.settings import DATA_DIR

class DocumentProcessingOrchestrator:
    """Main orchestration system for document processing"""
    
    def __init__(self):
        self.logger = logging.getLogger("DocumentProcessingOrchestrator")
        
        # Initialize message queue
        self.message_queue = MessageQueue()
        
        # Initialize monitoring and error handling
        self.status_monitor = StatusMonitor()
        self.error_handler = ErrorHandler()
        
        # Initialize agents
        self.agents = {}
        self._initialize_agents()
        
        # Initialize workflow engine
        self.workflow_engine = WorkflowEngine(
            self.agents['manager'], 
            self.message_queue
        )
        
        # System state
        self.is_running = False
        self.startup_time = None
        
        # Performance tracking
        self.performance_metrics = {
            'total_documents_processed': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'average_processing_time': 0.0,
            'system_uptime': 0.0
        }
        
        self.logger.info("Document Processing Orchestrator initialized")
    
    def _initialize_agents(self):
        """Initialize all processing agents"""
        try:
            # Create all agents with the shared message queue
            self.agents = {
                'manager': ManagerAgent('manager_001', self.message_queue),
                'master_data': MasterDataAgent('master_data_001', self.message_queue),
                'extraction': ExtractionAgent('extraction_001', self.message_queue),
                'contract': ContractAgent('contract_001', self.message_queue),
                'msa': MSAAgent('msa_001', self.message_queue),
                'leasing': LeasingAgent('leasing_001', self.message_queue),
                'fixed_assets': FixedAssetsAgent('fixed_assets_001', self.message_queue),
                'quality_review': QualityReviewAgent('quality_review_001', self.message_queue)
            }
            
            self.logger.info(f"Initialized {len(self.agents)} agents")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
    
    async def start_system(self) -> Dict[str, Any]:
        """Start the orchestration system"""
        try:
            if self.is_running:
                return {
                    'status': 'already_running',
                    'message': 'System is already running'
                }
            
            self.startup_time = datetime.now()
            self.is_running = True
            
            # Start all agents
            for agent_name, agent in self.agents.items():
                agent.start()
                self.logger.info(f"Started agent: {agent_name}")
            
            # Start message processing
            self._start_message_processing()
            
            self.logger.info("Document Processing Orchestrator started successfully")
            
            return {
                'status': 'started',
                'startup_time': self.startup_time.isoformat(),
                'agents_started': len(self.agents),
                'message': 'System started successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start system: {e}")
            self.is_running = False
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def stop_system(self) -> Dict[str, Any]:
        """Stop the orchestration system"""
        try:
            if not self.is_running:
                return {
                    'status': 'not_running',
                    'message': 'System is not running'
                }
            
            self.is_running = False
            
            # Stop all agents
            for agent_name, agent in self.agents.items():
                agent.stop()
                self.logger.info(f"Stopped agent: {agent_name}")
            
            # Stop monitoring
            self.status_monitor.shutdown()
            
            # Calculate uptime
            if self.startup_time:
                uptime = (datetime.now() - self.startup_time).total_seconds()
                self.performance_metrics['system_uptime'] = uptime
            
            self.logger.info("Document Processing Orchestrator stopped")
            
            return {
                'status': 'stopped',
                'uptime_seconds': self.performance_metrics['system_uptime'],
                'message': 'System stopped successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to stop system: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def process_document(self, document_path: str, document_type: str = None) -> Dict[str, Any]:
        """Process a single document"""
        try:
            if not self.is_running:
                return {
                    'status': 'error',
                    'message': 'System is not running'
                }
            
            # Validate document exists
            if not Path(document_path).exists():
                return {
                    'status': 'error',
                    'message': f'Document not found: {document_path}'
                }
            
            # Create workflow
            workflow_id = f"WF_SINGLE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            workflow = await self.workflow_engine.create_workflow(workflow_id)
            
            # Register workflow with status monitor
            self.status_monitor.register_workflow(workflow_id, {
                'type': 'single_document',
                'document_path': document_path,
                'document_type': document_type,
                'total_tasks': 1
            })
            
            # Execute workflow
            result = await self.workflow_engine.execute_workflow(workflow_id, [document_path])
            
            # Update performance metrics
            self.performance_metrics['total_documents_processed'] += 1
            if result.get('status') == 'completed':
                self.performance_metrics['successful_workflows'] += 1
            else:
                self.performance_metrics['failed_workflows'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing document {document_path}: {e}")
            
            # Handle error through error handler
            error_context = ErrorContext(
                workflow_id=None,
                task_id=None,
                agent_id='orchestrator',
                document_path=document_path,
                stage='document_processing',
                timestamp=datetime.now(),
                additional_data={'document_type': document_type}
            )
            
            await self.error_handler.handle_error(e, error_context)
            
            return {
                'status': 'error',
                'message': str(e),
                'document_path': document_path
            }
    
    async def process_batch(self, document_paths: List[str], batch_id: str = None) -> Dict[str, Any]:
        """Process a batch of documents"""
        try:
            if not self.is_running:
                return {
                    'status': 'error',
                    'message': 'System is not running'
                }
            
            # Validate all documents exist
            missing_docs = [path for path in document_paths if not Path(path).exists()]
            if missing_docs:
                return {
                    'status': 'error',
                    'message': f'Documents not found: {missing_docs}'
                }
            
            # Create workflow
            workflow_id = f"WF_BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if not batch_id:
                batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            workflow = await self.workflow_engine.create_workflow(workflow_id)
            
            # Register workflow with status monitor
            self.status_monitor.register_workflow(workflow_id, {
                'type': 'batch_processing',
                'batch_id': batch_id,
                'document_paths': document_paths,
                'total_tasks': len(document_paths)
            })
            
            # Execute workflow
            result = await self.workflow_engine.execute_workflow(workflow_id, document_paths)
            
            # Update performance metrics
            self.performance_metrics['total_documents_processed'] += len(document_paths)
            if result.get('status') == 'completed':
                self.performance_metrics['successful_workflows'] += 1
            else:
                self.performance_metrics['failed_workflows'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")
            
            # Handle error through error handler
            error_context = ErrorContext(
                workflow_id=None,
                task_id=None,
                agent_id='orchestrator',
                document_path=None,
                stage='batch_processing',
                timestamp=datetime.now(),
                additional_data={
                    'batch_id': batch_id,
                    'document_count': len(document_paths)
                }
            )
            
            await self.error_handler.handle_error(e, error_context)
            
            return {
                'status': 'error',
                'message': str(e),
                'batch_id': batch_id
            }
    
    async def process_directory(self, directory_path: str, file_pattern: str = "*.json") -> Dict[str, Any]:
        """Process all documents in a directory"""
        try:
            directory = Path(directory_path)
            if not directory.exists() or not directory.is_dir():
                return {
                    'status': 'error',
                    'message': f'Directory not found: {directory_path}'
                }
            
            # Find all matching files
            document_paths = list(directory.glob(file_pattern))
            document_paths = [str(path) for path in document_paths]
            
            if not document_paths:
                return {
                    'status': 'warning',
                    'message': f'No files found matching pattern {file_pattern} in {directory_path}'
                }
            
            # Process as batch
            batch_id = f"DIR_{directory.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return await self.process_batch(document_paths, batch_id)
            
        except Exception as e:
            self.logger.error(f"Error processing directory {directory_path}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'directory_path': directory_path
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Get dashboard data from status monitor
            dashboard_data = self.status_monitor.get_dashboard_data()
            
            # Get error statistics
            error_stats = self.error_handler.get_error_statistics()
            
            # Calculate uptime
            uptime_seconds = 0
            if self.startup_time:
                uptime_seconds = (datetime.now() - self.startup_time).total_seconds()
            
            # Get agent statuses
            agent_statuses = {}
            for agent_name, agent in self.agents.items():
                agent_statuses[agent_name] = {
                    'status': agent.status.value,
                    'tasks_completed': agent.metrics.tasks_completed,
                    'tasks_failed': agent.metrics.tasks_failed,
                    'total_processing_time': agent.metrics.total_processing_time
                }
            
            return {
                'system_status': 'running' if self.is_running else 'stopped',
                'uptime_seconds': uptime_seconds,
                'startup_time': self.startup_time.isoformat() if self.startup_time else None,
                'performance_metrics': self.performance_metrics,
                'dashboard_data': dashboard_data,
                'error_statistics': error_stats,
                'agent_statuses': agent_statuses,
                'workflow_engine_status': {
                    'active_workflows': len(self.workflow_engine.active_workflows),
                    'completed_workflows': len(self.workflow_engine.completed_workflows)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a specific workflow"""
        try:
            # Get status from workflow engine
            workflow_status = self.workflow_engine.get_workflow_status(workflow_id)
            
            # Get detailed status from status monitor
            workflow_details = self.status_monitor.get_workflow_details(workflow_id)
            
            return {
                'workflow_id': workflow_id,
                'engine_status': workflow_status,
                'detailed_status': workflow_details
            }
            
        except Exception as e:
            self.logger.error(f"Error getting workflow status for {workflow_id}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'workflow_id': workflow_id
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        try:
            # Get trends from status monitor
            trends = self.status_monitor.get_performance_trends(hours=24)
            
            # Calculate additional metrics
            total_workflows = self.performance_metrics['successful_workflows'] + self.performance_metrics['failed_workflows']
            success_rate = (self.performance_metrics['successful_workflows'] / total_workflows * 100) if total_workflows > 0 else 0
            
            return {
                'current_metrics': self.performance_metrics,
                'success_rate': success_rate,
                'performance_trends': trends,
                'agent_performance': {
                    agent_name: {
                        'efficiency': agent.metrics.tasks_completed / max(1, agent.metrics.tasks_completed + agent.metrics.tasks_failed) * 100,
                        'average_processing_time': agent.metrics.total_processing_time / max(1, agent.metrics.tasks_completed)
                    }
                    for agent_name, agent in self.agents.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _start_message_processing(self):
        """Start background message processing"""
        def process_messages():
            while self.is_running:
                try:
                    # Process messages for each agent
                    for agent_name, agent in self.agents.items():
                        messages = self.message_queue.get_messages(agent.agent_id)
                        for message in messages:
                            try:
                                response = agent.process_message(message)
                                # Handle response if needed
                            except Exception as e:
                                self.logger.error(f"Error processing message for {agent_name}: {e}")
                    
                    # Small delay to prevent busy waiting
                    import time
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.error(f"Error in message processing loop: {e}")
        
        # Start message processing in background thread
        message_thread = threading.Thread(target=process_messages, daemon=True)
        message_thread.start()
        
        self.logger.info("Message processing started")
    
    async def run_sample_workflow(self) -> Dict[str, Any]:
        """Run a sample workflow with test data"""
        try:
            # Find sample documents
            sample_docs = []
            
            # Look for sample documents in data directory
            for doc_type in ['invoices', 'contracts', 'msa', 'leases', 'fixed_assets']:
                doc_dir = DATA_DIR / doc_type
                if doc_dir.exists():
                    docs = list(doc_dir.glob('*.json'))[:2]  # Take first 2 of each type
                    sample_docs.extend([str(doc) for doc in docs])
            
            if not sample_docs:
                return {
                    'status': 'warning',
                    'message': 'No sample documents found'
                }
            
            self.logger.info(f"Running sample workflow with {len(sample_docs)} documents")
            
            # Process as batch
            result = await self.process_batch(sample_docs, "SAMPLE_WORKFLOW")
            
            return {
                'status': 'completed',
                'sample_workflow_result': result,
                'documents_processed': len(sample_docs),
                'document_paths': sample_docs
            }
            
        except Exception as e:
            self.logger.error(f"Error running sample workflow: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }