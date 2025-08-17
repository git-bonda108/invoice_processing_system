"""
Real-time Dashboard - Web-based monitoring interface
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import asyncio

class RealTimeDashboard:
    """Real-time web dashboard for system monitoring"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger("RealTimeDashboard")
        
        # Dashboard configuration
        self.config = {
            'refresh_interval': 5,  # seconds
            'max_recent_items': 50,
            'enable_real_time_updates': True,
            'chart_data_points': 100
        }
        
        # Dashboard state
        self.dashboard_data = {}
        self.last_update = None
        
        self.logger.info("Real-time Dashboard initialized")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            current_time = datetime.now()
            
            # Get system status
            system_status = self.orchestrator.get_system_status()
            
            # Get performance metrics
            performance_metrics = self.orchestrator.get_performance_metrics()
            
            # Build dashboard data
            dashboard_data = {
                'timestamp': current_time.isoformat(),
                'system_overview': self._build_system_overview(system_status),
                'workflow_status': self._build_workflow_status(system_status),
                'agent_status': self._build_agent_status(system_status),
                'performance_charts': self._build_performance_charts(performance_metrics),
                'recent_activities': self._build_recent_activities(system_status),
                'alerts_summary': self._build_alerts_summary(system_status),
                'resource_utilization': self._build_resource_utilization(),
                'processing_queue': self._build_processing_queue(system_status)
            }
            
            self.dashboard_data = dashboard_data
            self.last_update = current_time
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error building dashboard data: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _build_system_overview(self, system_status: Dict[str, Any]) -> Dict[str, Any]:
        """Build system overview section"""
        performance = system_status.get('performance_metrics', {})
        dashboard_data = system_status.get('dashboard_data', {})
        
        # Calculate key metrics
        total_workflows = performance.get('successful_workflows', 0) + performance.get('failed_workflows', 0)
        success_rate = (performance.get('successful_workflows', 0) / total_workflows * 100) if total_workflows > 0 else 0
        
        return {
            'system_status': system_status.get('system_status', 'unknown'),
            'uptime': self._format_uptime(system_status.get('uptime_seconds', 0)),
            'total_documents_processed': performance.get('total_documents_processed', 0),
            'success_rate': round(success_rate, 1),
            'active_workflows': dashboard_data.get('workflows', {}).get('active', 0),
            'active_tasks': dashboard_data.get('tasks', {}).get('active', 0),
            'throughput_per_hour': dashboard_data.get('performance', {}).get('throughput_per_hour', 0),
            'average_processing_time': dashboard_data.get('performance', {}).get('average_workflow_time', 0)
        }
    
    def _build_workflow_status(self, system_status: Dict[str, Any]) -> Dict[str, Any]:
        """Build workflow status section"""
        dashboard_data = system_status.get('dashboard_data', {})
        workflows = dashboard_data.get('workflows', {})
        
        return {
            'active_workflows': workflows.get('active', 0),
            'completed_workflows': workflows.get('completed', 0),
            'failed_workflows': workflows.get('failed', 0),
            'success_rate': workflows.get('success_rate', 0),
            'recent_workflows': dashboard_data.get('recent_workflows', [])[-10:]  # Last 10
        }
    
    def _build_agent_status(self, system_status: Dict[str, Any]) -> Dict[str, Any]:
        """Build agent status section"""
        agent_statuses = system_status.get('agent_statuses', {})
        
        agent_summary = []
        for agent_name, status in agent_statuses.items():
            total_tasks = status.get('tasks_completed', 0) + status.get('tasks_failed', 0)
            efficiency = (status.get('tasks_completed', 0) / total_tasks * 100) if total_tasks > 0 else 0
            
            agent_summary.append({
                'name': agent_name,
                'status': status.get('status', 'unknown'),
                'tasks_completed': status.get('tasks_completed', 0),
                'tasks_failed': status.get('tasks_failed', 0),
                'efficiency': round(efficiency, 1),
                'avg_processing_time': status.get('total_processing_time', 0) / max(1, status.get('tasks_completed', 1))
            })
        
        return {
            'agents': agent_summary,
            'total_agents': len(agent_statuses),
            'active_agents': sum(1 for status in agent_statuses.values() if status.get('status') == 'idle')
        }
    
    def _build_performance_charts(self, performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Build performance charts data"""
        trends = performance_metrics.get('performance_trends', {})
        
        # Prepare chart data
        charts = {
            'throughput_chart': {
                'title': 'Documents Processed Per Hour',
                'data': trends.get('trends', {}).get('throughput', {}).get('values', []),
                'timestamps': trends.get('timestamps', [])
            },
            'processing_time_chart': {
                'title': 'Average Processing Time (seconds)',
                'data': trends.get('trends', {}).get('processing_time', {}).get('values', []),
                'timestamps': trends.get('timestamps', [])
            },
            'workflow_activity_chart': {
                'title': 'Active Workflows',
                'data': trends.get('trends', {}).get('active_workflows', {}).get('values', []),
                'timestamps': trends.get('timestamps', [])
            }
        }
        
        return charts
    
    def _build_recent_activities(self, system_status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build recent activities list"""
        activities = []
        
        # Get recent workflows
        dashboard_data = system_status.get('dashboard_data', {})
        recent_workflows = dashboard_data.get('recent_workflows', [])
        
        for workflow in recent_workflows[-10:]:  # Last 10 workflows
            activities.append({
                'type': 'workflow',
                'action': f"Workflow {workflow.get('status', 'unknown')}",
                'description': f"Workflow {workflow.get('workflow_id', 'unknown')} processed {workflow.get('total_documents', 0)} documents",
                'timestamp': workflow.get('completed_at', workflow.get('created_at', '')),
                'status': workflow.get('status', 'unknown')
            })
        
        # Get recent alerts
        alerts = dashboard_data.get('alerts', {}).get('recent', [])
        for alert in alerts:
            activities.append({
                'type': 'alert',
                'action': f"{alert.get('level', 'info').title()} Alert",
                'description': alert.get('title', 'Unknown alert'),
                'timestamp': alert.get('timestamp', ''),
                'status': alert.get('level', 'info')
            })
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return activities[:20]  # Return top 20 activities
    
    def _build_alerts_summary(self, system_status: Dict[str, Any]) -> Dict[str, Any]:
        """Build alerts summary"""
        dashboard_data = system_status.get('dashboard_data', {})
        alerts = dashboard_data.get('alerts', {})
        
        return {
            'total_active_alerts': alerts.get('total_active', 0),
            'alerts_by_level': alerts.get('by_level', {}),
            'recent_alerts': alerts.get('recent', [])
        }
    
    def _build_resource_utilization(self) -> Dict[str, Any]:
        """Build resource utilization section"""
        # In a real implementation, this would get actual system metrics
        return {
            'cpu_usage': 45.2,  # Percentage
            'memory_usage': 62.8,  # Percentage
            'disk_usage': 34.1,  # Percentage
            'network_io': 12.5,  # MB/s
            'queue_size': 0,
            'thread_pool_utilization': 23.4  # Percentage
        }
    
    def _build_processing_queue(self, system_status: Dict[str, Any]) -> Dict[str, Any]:
        """Build processing queue information"""
        dashboard_data = system_status.get('dashboard_data', {})
        tasks = dashboard_data.get('tasks', {})
        
        return {
            'queue_size': tasks.get('queue_size', 0),
            'active_tasks': tasks.get('active', 0),
            'estimated_wait_time': self._calculate_estimated_wait_time(tasks.get('queue_size', 0)),
            'queue_by_document_type': self._get_queue_by_document_type()
        }
    
    def _format_uptime(self, uptime_seconds: float) -> str:
        """Format uptime in human-readable format"""
        if uptime_seconds < 60:
            return f"{int(uptime_seconds)}s"
        elif uptime_seconds < 3600:
            minutes = int(uptime_seconds / 60)
            seconds = int(uptime_seconds % 60)
            return f"{minutes}m {seconds}s"
        elif uptime_seconds < 86400:
            hours = int(uptime_seconds / 3600)
            minutes = int((uptime_seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
        else:
            days = int(uptime_seconds / 86400)
            hours = int((uptime_seconds % 86400) / 3600)
            return f"{days}d {hours}h"
    
    def _calculate_estimated_wait_time(self, queue_size: int) -> str:
        """Calculate estimated wait time for queued items"""
        if queue_size == 0:
            return "0s"
        
        # Assume average processing time of 30 seconds per document
        avg_processing_time = 30
        estimated_seconds = queue_size * avg_processing_time
        
        if estimated_seconds < 60:
            return f"{estimated_seconds}s"
        elif estimated_seconds < 3600:
            return f"{int(estimated_seconds / 60)}m"
        else:
            return f"{int(estimated_seconds / 3600)}h {int((estimated_seconds % 3600) / 60)}m"
    
    def _get_queue_by_document_type(self) -> Dict[str, int]:
        """Get queue breakdown by document type"""
        # In a real implementation, this would query the actual queue
        return {
            'invoice': 0,
            'contract': 0,
            'msa': 0,
            'lease': 0,
            'fixed_asset': 0
        }
    
    def generate_html_dashboard(self) -> str:
        """Generate HTML dashboard"""
        dashboard_data = self.get_dashboard_data()
        
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Invoice Processing System - Dashboard</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .dashboard {
                    max-width: 1400px;
                    margin: 0 auto;
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    text-align: center;
                }
                .metrics-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 20px;
                }
                .metric-card {
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }
                .metric-value {
                    font-size: 2em;
                    font-weight: bold;
                    color: #333;
                }
                .metric-label {
                    color: #666;
                    margin-top: 5px;
                }
                .status-good { color: #28a745; }
                .status-warning { color: #ffc107; }
                .status-error { color: #dc3545; }
                .content-grid {
                    display: grid;
                    grid-template-columns: 2fr 1fr;
                    gap: 20px;
                }
                .panel {
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .panel h3 {
                    margin-top: 0;
                    color: #333;
                    border-bottom: 2px solid #eee;
                    padding-bottom: 10px;
                }
                .agent-list {
                    list-style: none;
                    padding: 0;
                }
                .agent-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                }
                .agent-name {
                    font-weight: bold;
                }
                .agent-status {
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.8em;
                    text-transform: uppercase;
                }
                .status-idle { background: #d4edda; color: #155724; }
                .status-processing { background: #fff3cd; color: #856404; }
                .status-error { background: #f8d7da; color: #721c24; }
                .activity-list {
                    max-height: 400px;
                    overflow-y: auto;
                }
                .activity-item {
                    padding: 10px;
                    border-left: 4px solid #ddd;
                    margin-bottom: 10px;
                    background: #f8f9fa;
                }
                .activity-workflow { border-left-color: #007bff; }
                .activity-alert { border-left-color: #ffc107; }
                .activity-error { border-left-color: #dc3545; }
                .timestamp {
                    font-size: 0.8em;
                    color: #666;
                }
                .refresh-info {
                    text-align: center;
                    color: #666;
                    margin-top: 20px;
                    font-size: 0.9em;
                }
            </style>
            <script>
                // Auto-refresh every 30 seconds
                setTimeout(function() {
                    location.reload();
                }, 30000);
            </script>
        </head>
        <body>
            <div class="dashboard">
                <div class="header">
                    <h1>Invoice Processing System Dashboard</h1>
                    <p>Real-time monitoring and system status</p>
                    <p>Last updated: {timestamp}</p>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value status-{system_status_class}">{system_status}</div>
                        <div class="metric-label">System Status</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{uptime}</div>
                        <div class="metric-label">Uptime</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{total_documents}</div>
                        <div class="metric-label">Documents Processed</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{success_rate}%</div>
                        <div class="metric-label">Success Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{active_workflows}</div>
                        <div class="metric-label">Active Workflows</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{throughput}</div>
                        <div class="metric-label">Docs/Hour</div>
                    </div>
                </div>
                
                <div class="content-grid">
                    <div class="panel">
                        <h3>Agent Status</h3>
                        <ul class="agent-list">
                            {agent_status_html}
                        </ul>
                    </div>
                    
                    <div class="panel">
                        <h3>Recent Activities</h3>
                        <div class="activity-list">
                            {recent_activities_html}
                        </div>
                    </div>
                </div>
                
                <div class="refresh-info">
                    Dashboard auto-refreshes every 30 seconds
                </div>
            </div>
        </body>
        </html>
        """
        
        # Extract data for template
        system_overview = dashboard_data.get('system_overview', {})
        agent_status = dashboard_data.get('agent_status', {})
        recent_activities = dashboard_data.get('recent_activities', [])
        
        # Determine system status class
        system_status = system_overview.get('system_status', 'unknown')
        system_status_class = 'good' if system_status == 'running' else 'error'
        
        # Generate agent status HTML
        agent_status_html = ""
        for agent in agent_status.get('agents', []):
            status_class = f"status-{agent.get('status', 'unknown')}"
            agent_status_html += f"""
            <li class="agent-item">
                <div>
                    <div class="agent-name">{agent.get('name', 'Unknown')}</div>
                    <div>Tasks: {agent.get('tasks_completed', 0)} | Efficiency: {agent.get('efficiency', 0)}%</div>
                </div>
                <span class="agent-status {status_class}">{agent.get('status', 'unknown')}</span>
            </li>
            """
        
        # Generate recent activities HTML
        recent_activities_html = ""
        for activity in recent_activities[:10]:
            activity_class = f"activity-{activity.get('type', 'unknown')}"
            recent_activities_html += f"""
            <div class="activity-item {activity_class}">
                <div><strong>{activity.get('action', 'Unknown Action')}</strong></div>
                <div>{activity.get('description', 'No description')}</div>
                <div class="timestamp">{activity.get('timestamp', 'Unknown time')}</div>
            </div>
            """
        
        # Fill template
        html_content = html_template.format(
            timestamp=dashboard_data.get('timestamp', 'Unknown'),
            system_status=system_status.title(),
            system_status_class=system_status_class,
            uptime=system_overview.get('uptime', '0s'),
            total_documents=system_overview.get('total_documents_processed', 0),
            success_rate=system_overview.get('success_rate', 0),
            active_workflows=system_overview.get('active_workflows', 0),
            throughput=round(system_overview.get('throughput_per_hour', 0), 1),
            agent_status_html=agent_status_html,
            recent_activities_html=recent_activities_html
        )
        
        return html_content
    
    def save_dashboard_html(self, file_path: str = "dashboard.html") -> str:
        """Save dashboard as HTML file"""
        try:
            html_content = self.generate_html_dashboard()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Dashboard saved to {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Error saving dashboard HTML: {e}")
            raise
    
    def get_api_data(self) -> Dict[str, Any]:
        """Get dashboard data in API format"""
        return {
            'status': 'success',
            'data': self.get_dashboard_data(),
            'metadata': {
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'refresh_interval': self.config['refresh_interval'],
                'version': '1.0.0'
            }
        }