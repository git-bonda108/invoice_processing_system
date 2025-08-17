"""Agents module for Invoice Processing System"""
from .base_agent import BaseAgent, AgentStatus, AgentMetrics
from .master_data_agent import MasterDataAgent
from .extraction_agent import ExtractionAgent
from .contract_agent import ContractAgent
from .msa_agent import MSAAgent
from .leasing_agent import LeasingAgent
from .fixed_assets_agent import FixedAssetsAgent
from .quality_review_agent import QualityReviewAgent
from .manager_agent import ManagerAgent, WorkflowStatus, TaskStatus, ProcessingTask, WorkflowExecution

# Phase 4 - New Agentic AI Agents
from .learning_agent import LearningAgent, ConversationContext, FeedbackRecord, LearningInsight
from .conversation_manager import ConversationManager, ConversationSession, AgentInteraction
from .enhanced_manager_agent import EnhancedManagerAgent, CriticalAnalysis, QualityChallenge

__all__ = [
    'BaseAgent',
    'AgentStatus', 
    'AgentMetrics',
    'MasterDataAgent',
    'ExtractionAgent',
    'ContractAgent',
    'MSAAgent',
    'LeasingAgent',
    'FixedAssetsAgent',
    'QualityReviewAgent',
    'ManagerAgent',
    'WorkflowStatus',
    'TaskStatus',
    'ProcessingTask',
    'WorkflowExecution',
    # Phase 4 additions
    'LearningAgent',
    'ConversationContext',
    'FeedbackRecord',
    'LearningInsight',
    'ConversationManager',
    'ConversationSession',
    'AgentInteraction',
    'EnhancedManagerAgent',
    'CriticalAnalysis',
    'QualityChallenge'
]