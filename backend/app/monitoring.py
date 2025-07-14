import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_monitoring.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class AgentMetrics:
    """Metrics for individual agent performance."""
    agent_name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    provider_used: Optional[str] = None
    tool_calls: int = 0
    
    @property
    def duration(self) -> float:
        """Calculate execution duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

@dataclass
class TaskMetrics:
    """Metrics for complete task execution."""
    task_id: str
    task_description: str
    start_time: float
    end_time: Optional[float] = None
    total_agents: int = 0
    successful_agents: int = 0
    failed_agents: int = 0
    total_duration: float = 0.0
    total_tokens: int = 0
    providers_used: Optional[list[str]] = None
    tools_used: Optional[list[str]] = None
    
    def __post_init__(self):
        if self.providers_used is None:
            object.__setattr__(self, 'providers_used', [])
        if self.tools_used is None:
            object.__setattr__(self, 'tools_used', [])
    
    @property
    def duration(self) -> float:
        """Calculate execution duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

class MonitoringSystem:
    """
    Monitoring system for tracking agent performance, API usage, and system metrics.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_tasks: Dict[str, TaskMetrics] = {}
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.api_usage: Dict[str, int] = defaultdict(int)
        self.tool_usage: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def start_task(self, task_id: str, task_description: str) -> str:
        """Start monitoring a new task."""
        with self._lock:
            task_metrics = TaskMetrics(
                task_id=task_id,
                task_description=task_description,
                start_time=time.time()
            )
            self.active_tasks[task_id] = task_metrics
            self.logger.info(f"Started task: {task_id} - {task_description}")
            return task_id
    
    def end_task(self, task_id: str, success: bool = True) -> None:
        """End monitoring for a task."""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.end_time = time.time()
                task.total_duration = task.duration
                
                # Calculate totals
                task.total_agents = len([m for m in self.agent_metrics.values() if m.agent_name.startswith(task_id)])
                task.successful_agents = len([m for m in self.agent_metrics.values() if m.agent_name.startswith(task_id) and m.success])
                task.failed_agents = task.total_agents - task.successful_agents
                
                # Get unique providers and tools used
                task.providers_used = list(set([m.provider_used for m in self.agent_metrics.values() if m.agent_name.startswith(task_id) and m.provider_used]))
                
                self.logger.info(f"Completed task: {task_id} - Duration: {task.total_duration:.2f}s - Success: {success}")
                
                # Log task summary
                self._log_task_summary(task)
    
    def start_agent(self, task_id: str, agent_name: str) -> str:
        """Start monitoring an agent execution."""
        with self._lock:
            agent_id = f"{task_id}_{agent_name}_{int(time.time())}"
            metrics = AgentMetrics(
                agent_name=agent_name,
                start_time=time.time()
            )
            self.agent_metrics[agent_id] = metrics
            self.logger.info(f"Started agent: {agent_name} for task: {task_id}")
            return agent_id
    
    def end_agent(self, agent_id: str, success: bool = True, error_message: Optional[str] = None, 
                  provider_used: Optional[str] = None, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """End monitoring for an agent."""
        with self._lock:
            if agent_id in self.agent_metrics:
                metrics = self.agent_metrics[agent_id]
                metrics.end_time = time.time()
                metrics.success = success
                metrics.error_message = error_message
                metrics.provider_used = provider_used
                metrics.input_tokens = input_tokens
                metrics.output_tokens = output_tokens
                
                # Update API usage
                if provider_used:
                    self.api_usage[provider_used] += 1
                
                # Update error counts
                if not success:
                    self.error_counts[metrics.agent_name] += 1
                
                self.logger.info(f"Completed agent: {metrics.agent_name} - Duration: {metrics.duration:.2f}s - Success: {success}")
    
    def record_tool_usage(self, tool_name: str) -> None:
        """Record tool usage."""
        with self._lock:
            self.tool_usage[tool_name] += 1
    
    def record_llm_call(self, provider: str, input_tokens: int, output_tokens: int) -> None:
        """Record LLM API call."""
        with self._lock:
            self.api_usage[provider] += 1
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics."""
        with self._lock:
            total_tasks = len(self.active_tasks)
            total_agents = len(self.agent_metrics)
            successful_agents = len([m for m in self.agent_metrics.values() if m.success])
            
            return {
                "active_tasks": total_tasks,
                "total_agents_executed": total_agents,
                "successful_agents": successful_agents,
                "success_rate": (successful_agents / total_agents * 100) if total_agents > 0 else 0,
                "api_usage": dict(self.api_usage),
                "tool_usage": dict(self.tool_usage),
                "error_counts": dict(self.error_counts),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_task_metrics(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific task."""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                return asdict(task)
            return None
    
    def _log_task_summary(self, task: TaskMetrics) -> None:
        """Log a summary of task execution."""
        summary = {
            "task_id": task.task_id,
            "description": task.task_description,
            "duration": f"{task.total_duration:.2f}s",
            "agents": {
                "total": task.total_agents,
                "successful": task.successful_agents,
                "failed": task.failed_agents
            },
            "providers_used": task.providers_used,
            "success_rate": f"{(task.successful_agents / task.total_agents * 100):.1f}%" if task.total_agents > 0 else "0%"
        }
        
        self.logger.info(f"Task Summary: {json.dumps(summary, indent=2)}")

monitoring = MonitoringSystem() 