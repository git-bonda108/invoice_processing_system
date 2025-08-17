"""
Workflow Engine - Document processing workflow orchestration
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from utils.message_queue import Message, MessageType, MessagePriority
from config.settings import DATA_DIR

class WorkflowStage(Enum):
    """Workflow processing stages"""
    INGESTION = "ingestion"
    CLASSIFICATION = "classification"
    AGENT_ASSIGNMENT = "agent_assignment"
    PROCESSING = "processing"
    CROSS_VALIDATION = "cross_validation"
    QUALITY_REVIEW = "quality_review"
    REPORTING = "reporting"
    COMPLETED = "completed"

class WorkflowPriority(Enum):
    """Workflow execution priority"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class WorkflowStep:
    """Individual workflow step"""
    step_id: str
    stage: WorkflowStage
    description: str
    required: bool = True
    timeout: int = 300  # seconds
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DocumentProcessingWorkflow:
    """End-to-end document processing workflow"""
    
    def __init__(self, workflow_id: str, manager_agent, message_queue):
        self.workflow_id = workflow_id
        self.manager_agent = manager_agent
        self.message_queue = message_queue
        self.logger = logging.getLogger(f"Workflow-{workflow_id}")
        
        # Workflow configuration
        self.config = {
            'enable_parallel_processing': True,
            'enable_cross_validation': True,
            'enable_quality_review': True,
            'timeout_per_stage': 300,
            'max_retries': 3,
            'retry_delay': 5
        }
        
        # Workflow stages definition
        self.stages = [
            WorkflowStage.INGESTION,
            WorkflowStage.CLASSIFICATION,
            WorkflowStage.AGENT_ASSIGNMENT,
            WorkflowStage.PROCESSING,
            WorkflowStage.CROSS_VALIDATION,
            WorkflowStage.QUALITY_REVIEW,
            WorkflowStage.REPORTING
        ]
        
        # Stage handlers
        self.stage_handlers = {
            WorkflowStage.INGESTION: self._handle_ingestion,
            WorkflowStage.CLASSIFICATION: self._handle_classification,
            WorkflowStage.AGENT_ASSIGNMENT: self._handle_agent_assignment,
            WorkflowStage.PROCESSING: self._handle_processing,
            WorkflowStage.CROSS_VALIDATION: self._handle_cross_validation,
            WorkflowStage.QUALITY_REVIEW: self._handle_quality_review,
            WorkflowStage.REPORTING: self._handle_reporting
        }
        
        # Workflow state
        self.current_stage = WorkflowStage.INGESTION
        self.workflow_steps: List[WorkflowStep] = []
        self.documents: List[Dict[str, Any]] = []
        self.processing_results: List[Dict[str, Any]] = []
        self.cross_validation_results: Dict[str, Any] = {}
        self.quality_report: Dict[str, Any] = {}
        self.final_report: Dict[str, Any] = {}
        
        # Performance tracking
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.total_processing_time: float = 0.0
        
        self.logger.info(f"Document processing workflow {workflow_id} initialized")
    
    async def process_document(self, document_path: str, document_type: str = None) -> Dict[str, Any]:
        """Process single document through complete workflow"""
        try:
            self.started_at = datetime.now()
            
            # Initialize workflow steps
            self._initialize_workflow_steps([document_path])
            
            # Add document to processing list
            document_info = {
                'path': document_path,
                'type': document_type,
                'metadata': await self._extract_document_metadata(document_path)
            }
            self.documents.append(document_info)
            
            # Execute workflow stages
            for stage in self.stages:
                self.current_stage = stage
                success = await self._execute_stage(stage)
                
                if not success:
                    return {
                        'status': 'failed',
                        'workflow_id': self.workflow_id,
                        'failed_stage': stage.value,
                        'message': f'Workflow failed at stage: {stage.value}'
                    }
            
            # Complete workflow
            self.completed_at = datetime.now()
            self.total_processing_time = (self.completed_at - self.started_at).total_seconds()
            
            return {
                'status': 'completed',
                'workflow_id': self.workflow_id,
                'processing_time': self.total_processing_time,
                'results': self.processing_results,
                'quality_report': self.quality_report,
                'final_report': self.final_report
            }
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {
                'status': 'error',
                'workflow_id': self.workflow_id,
                'message': str(e)
            }
    
    async def process_batch(self, document_paths: List[str]) -> Dict[str, Any]:
        """Process batch of documents with parallel execution"""
        try:
            self.started_at = datetime.now()
            
            # Initialize workflow steps
            self._initialize_workflow_steps(document_paths)
            
            # Add documents to processing list
            for doc_path in document_paths:
                document_info = {
                    'path': doc_path,
                    'type': None,  # Will be classified
                    'metadata': await self._extract_document_metadata(doc_path)
                }
                self.documents.append(document_info)
            
            # Execute workflow stages
            for stage in self.stages:
                self.current_stage = stage
                success = await self._execute_stage(stage)
                
                if not success:
                    return {
                        'status': 'failed',
                        'workflow_id': self.workflow_id,
                        'failed_stage': stage.value,
                        'message': f'Batch workflow failed at stage: {stage.value}'
                    }
            
            # Complete workflow
            self.completed_at = datetime.now()
            self.total_processing_time = (self.completed_at - self.started_at).total_seconds()
            
            return {
                'status': 'completed',
                'workflow_id': self.workflow_id,
                'total_documents': len(document_paths),
                'processing_time': self.total_processing_time,
                'results': self.processing_results,
                'cross_validation': self.cross_validation_results,
                'quality_report': self.quality_report,
                'final_report': self.final_report
            }
            
        except Exception as e:
            self.logger.error(f"Batch workflow execution failed: {e}")
            return {
                'status': 'error',
                'workflow_id': self.workflow_id,
                'message': str(e)
            }
    
    def _initialize_workflow_steps(self, document_paths: List[str]):
        """Initialize workflow steps for processing"""
        self.workflow_steps = []
        
        for i, stage in enumerate(self.stages):
            step = WorkflowStep(
                step_id=f"{self.workflow_id}_STEP_{i+1:02d}",
                stage=stage,
                description=f"Execute {stage.value} stage",
                timeout=self.config.get('timeout_per_stage', 300),
                max_retries=self.config.get('max_retries', 3)
            )
            self.workflow_steps.append(step)
    
    async def _execute_stage(self, stage: WorkflowStage) -> bool:
        """Execute a workflow stage"""
        step = next((s for s in self.workflow_steps if s.stage == stage), None)
        if not step:
            self.logger.error(f"No step found for stage {stage.value}")
            return False
        
        try:
            step.status = "running"
            step.started_at = datetime.now()
            
            self.logger.info(f"Executing stage: {stage.value}")
            
            # Get stage handler
            handler = self.stage_handlers.get(stage)
            if not handler:
                raise ValueError(f"No handler found for stage {stage.value}")
            
            # Execute stage with timeout
            result = await asyncio.wait_for(
                handler(),
                timeout=step.timeout
            )
            
            step.status = "completed"
            step.completed_at = datetime.now()
            step.result = result
            
            return result.get('success', False)
            
        except asyncio.TimeoutError:
            step.status = "timeout"
            step.error = f"Stage {stage.value} timed out after {step.timeout} seconds"
            self.logger.error(step.error)
            return False
            
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            self.logger.error(f"Stage {stage.value} failed: {e}")
            
            # Retry logic
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                self.logger.info(f"Retrying stage {stage.value} (attempt {step.retry_count})")
                
                # Wait before retry
                await asyncio.sleep(self.config.get('retry_delay', 5) * step.retry_count)
                
                # Retry the stage
                return await self._execute_stage(stage)
            
            return False
    
    async def _handle_ingestion(self) -> Dict[str, Any]:
        """Handle document ingestion stage"""
        try:
            ingested_documents = []
            
            for document in self.documents:
                # Validate document exists and is readable
                doc_path = Path(document['path'])
                if not doc_path.exists():
                    raise FileNotFoundError(f"Document not found: {document['path']}")
                
                # Load document content
                with open(doc_path, 'r') as f:
                    content = json.load(f)
                
                document['content'] = content
                document['size'] = doc_path.stat().st_size
                document['ingested_at'] = datetime.now()
                
                ingested_documents.append(document)
            
            self.logger.info(f"Ingested {len(ingested_documents)} documents")
            
            return {
                'success': True,
                'ingested_count': len(ingested_documents),
                'documents': ingested_documents
            }
            
        except Exception as e:
            self.logger.error(f"Document ingestion failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_classification(self) -> Dict[str, Any]:
        """Handle document classification stage"""
        try:
            classified_documents = []
            
            for document in self.documents:
                if not document.get('type'):
                    # Classify based on content
                    content = document.get('content', {})
                    doc_type = content.get('document_type', 'unknown')
                    
                    # Enhanced classification logic
                    if doc_type == 'unknown':
                        doc_type = self._classify_by_content(content)
                    
                    document['type'] = doc_type
                    document['classified_at'] = datetime.now()
                
                classified_documents.append(document)
            
            self.logger.info(f"Classified {len(classified_documents)} documents")
            
            return {
                'success': True,
                'classified_count': len(classified_documents),
                'document_types': [doc['type'] for doc in classified_documents]
            }
            
        except Exception as e:
            self.logger.error(f"Document classification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_agent_assignment(self) -> Dict[str, Any]:
        """Handle agent assignment stage"""
        try:
            assignments = []
            
            for document in self.documents:
                doc_type = document.get('type', 'unknown')
                agent_type = self._get_agent_type_for_document(doc_type)
                
                assignment = {
                    'document_path': document['path'],
                    'document_type': doc_type,
                    'agent_type': agent_type,
                    'assigned_at': datetime.now()
                }
                assignments.append(assignment)
            
            self.logger.info(f"Assigned {len(assignments)} documents to agents")
            
            return {
                'success': True,
                'assignments': assignments
            }
            
        except Exception as e:
            self.logger.error(f"Agent assignment failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_processing(self) -> Dict[str, Any]:
        """Handle document processing stage"""
        try:
            processing_results = []
            
            # Get assignments from previous stage
            assignment_step = next(
                (s for s in self.workflow_steps if s.stage == WorkflowStage.AGENT_ASSIGNMENT),
                None
            )
            
            if not assignment_step or not assignment_step.result:
                raise ValueError("No agent assignments found")
            
            assignments = assignment_step.result.get('assignments', [])
            
            # Process documents (parallel if enabled)
            if self.config.get('enable_parallel_processing', True) and len(assignments) > 1:
                results = await self._process_documents_parallel(assignments)
            else:
                results = await self._process_documents_sequential(assignments)
            
            processing_results.extend(results)
            self.processing_results = processing_results
            
            self.logger.info(f"Processed {len(processing_results)} documents")
            
            return {
                'success': True,
                'processed_count': len(processing_results),
                'results': processing_results
            }
            
        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_cross_validation(self) -> Dict[str, Any]:
        """Handle cross-validation stage"""
        try:
            if not self.config.get('enable_cross_validation', True):
                return {'success': True, 'skipped': True}
            
            # Perform cross-document validation
            validation_results = await self._perform_cross_validation(self.processing_results)
            self.cross_validation_results = validation_results
            
            self.logger.info("Cross-validation completed")
            
            return {
                'success': True,
                'validation_results': validation_results
            }
            
        except Exception as e:
            self.logger.error(f"Cross-validation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_quality_review(self) -> Dict[str, Any]:
        """Handle quality review stage"""
        try:
            if not self.config.get('enable_quality_review', True):
                return {'success': True, 'skipped': True}
            
            # Generate quality report
            quality_report = await self._generate_quality_report(
                self.processing_results,
                self.cross_validation_results
            )
            self.quality_report = quality_report
            
            self.logger.info("Quality review completed")
            
            return {
                'success': True,
                'quality_report': quality_report
            }
            
        except Exception as e:
            self.logger.error(f"Quality review failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_reporting(self) -> Dict[str, Any]:
        """Handle final reporting stage"""
        try:
            # Generate comprehensive final report
            final_report = {
                'workflow_id': self.workflow_id,
                'execution_summary': {
                    'total_documents': len(self.documents),
                    'processing_time': self.total_processing_time,
                    'started_at': self.started_at.isoformat() if self.started_at else None,
                    'completed_at': datetime.now().isoformat()
                },
                'document_results': self.processing_results,
                'cross_validation': self.cross_validation_results,
                'quality_assessment': self.quality_report,
                'workflow_steps': [asdict(step) for step in self.workflow_steps]
            }
            
            self.final_report = final_report
            
            self.logger.info("Final report generated")
            
            return {
                'success': True,
                'final_report': final_report
            }
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _extract_document_metadata(self, document_path: str) -> Dict[str, Any]:
        """Extract metadata from document"""
        try:
            doc_path = Path(document_path)
            stat = doc_path.stat()
            
            return {
                'filename': doc_path.name,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'extension': doc_path.suffix
            }
        except Exception as e:
            self.logger.warning(f"Failed to extract metadata for {document_path}: {e}")
            return {}
    
    def _classify_by_content(self, content: Dict[str, Any]) -> str:
        """Classify document by analyzing content"""
        # Simple classification logic
        if 'invoice_number' in content:
            return 'invoice'
        elif 'contract_number' in content:
            return 'contract'
        elif 'msa_number' in content:
            return 'msa'
        elif 'lease_number' in content:
            return 'lease'
        elif 'agreement_number' in content and 'asset_details' in content:
            return 'fixed_asset'
        else:
            return 'unknown'
    
    def _get_agent_type_for_document(self, document_type: str) -> str:
        """Get appropriate agent type for document type"""
        agent_mapping = {
            'invoice': 'extraction',
            'contract': 'contract',
            'msa': 'msa',
            'lease': 'leasing',
            'fixed_asset': 'fixed_assets'
        }
        return agent_mapping.get(document_type, 'extraction')
    
    async def _process_documents_parallel(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process documents in parallel"""
        tasks = []
        for assignment in assignments:
            task = asyncio.create_task(self._process_single_document(assignment))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        successful_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Document processing failed: {result}")
            else:
                successful_results.append(result)
        
        return successful_results
    
    async def _process_documents_sequential(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process documents sequentially"""
        results = []
        for assignment in assignments:
            try:
                result = await self._process_single_document(assignment)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Document processing failed: {e}")
        
        return results
    
    async def _process_single_document(self, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single document"""
        # This would integrate with the actual agent processing
        # For now, return a mock result
        return {
            'document_path': assignment['document_path'],
            'document_type': assignment['document_type'],
            'agent_type': assignment['agent_type'],
            'status': 'success',
            'processing_time': 2.5,
            'confidence': 0.95,
            'extracted_fields': [],
            'anomalies': []
        }
    
    async def _perform_cross_validation(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform cross-document validation"""
        # Mock cross-validation logic
        return {
            'po_correlations': {'matched': 2, 'unmatched': 1},
            'asset_correlations': {'matched': 1, 'unmatched': 0},
            'amount_variances': []
        }
    
    async def _generate_quality_report(self, results: List[Dict[str, Any]], 
                                     cross_validation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quality assessment report"""
        # Mock quality report generation
        return {
            'overall_score': 92.5,
            'document_scores': [95.0, 90.0, 92.5],
            'anomaly_summary': {'total': 3, 'critical': 0, 'high': 1, 'medium': 2},
            'recommendations': ['Review medium-severity anomalies']
        }

class WorkflowEngine:
    """Workflow engine for managing document processing workflows"""
    
    def __init__(self, manager_agent, message_queue):
        self.manager_agent = manager_agent
        self.message_queue = message_queue
        self.logger = logging.getLogger("WorkflowEngine")
        
        # Active workflows
        self.active_workflows: Dict[str, DocumentProcessingWorkflow] = {}
        self.completed_workflows: Dict[str, DocumentProcessingWorkflow] = {}
        
        # Configuration
        self.config = {
            'max_concurrent_workflows': 10,
            'default_timeout': 1800,  # 30 minutes
            'enable_monitoring': True
        }
        
        self.logger.info("Workflow Engine initialized")
    
    async def create_workflow(self, workflow_id: str) -> DocumentProcessingWorkflow:
        """Create a new workflow instance"""
        if workflow_id in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} already exists")
        
        workflow = DocumentProcessingWorkflow(workflow_id, self.manager_agent, self.message_queue)
        self.active_workflows[workflow_id] = workflow
        
        self.logger.info(f"Created workflow {workflow_id}")
        return workflow
    
    async def execute_workflow(self, workflow_id: str, document_paths: List[str]) -> Dict[str, Any]:
        """Execute a workflow"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.active_workflows[workflow_id]
        
        try:
            if len(document_paths) == 1:
                result = await workflow.process_document(document_paths[0])
            else:
                result = await workflow.process_batch(document_paths)
            
            # Move to completed workflows
            self.completed_workflows[workflow_id] = workflow
            del self.active_workflows[workflow_id]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} execution failed: {e}")
            return {
                'status': 'error',
                'workflow_id': workflow_id,
                'message': str(e)
            }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            return {
                'status': 'active',
                'current_stage': workflow.current_stage.value,
                'progress': self._calculate_progress(workflow)
            }
        elif workflow_id in self.completed_workflows:
            workflow = self.completed_workflows[workflow_id]
            return {
                'status': 'completed',
                'total_time': workflow.total_processing_time,
                'results': len(workflow.processing_results)
            }
        else:
            return {
                'status': 'not_found',
                'message': f'Workflow {workflow_id} not found'
            }
    
    def _calculate_progress(self, workflow: DocumentProcessingWorkflow) -> float:
        """Calculate workflow progress percentage"""
        total_stages = len(workflow.stages)
        completed_stages = sum(1 for step in workflow.workflow_steps if step.status == "completed")
        return (completed_stages / total_stages) * 100 if total_stages > 0 else 0.0