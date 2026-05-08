"""
Prometheus metrics collection for observability
"""

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any
import time


class MetricsCollector:
    """Collects and exports Prometheus metrics"""
    
    def __init__(self):
        # Counters
        self.agents_spawned = Counter(
            'agents_spawned_total',
            'Total number of agents spawned',
            ['agent_type']
        )
        self.tasks_completed = Counter(
            'tasks_completed_total',
            'Total number of tasks completed',
            ['agent_type', 'task_type', 'status']
        )
        
        # Gauges
        self.active_agents = Gauge(
            'active_agents',
            'Number of currently active agents',
            ['agent_type']
        )
        self.task_queue_size = Gauge(
            'task_queue_size',
            'Current size of task queue'
        )
        
        # Histograms
        self.task_duration = Histogram(
            'task_duration_seconds',
            'Task execution duration in seconds',
            ['agent_type', 'task_type'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
        )
    
    def record_agent_spawn(self, agent_type: str):
        """Record agent spawn event"""
        self.agents_spawned.labels(agent_type=agent_type).inc()
        self.active_agents.labels(agent_type=agent_type).inc()
    
    def record_task_completion(self, agent_type: str, task_type: str, status: str, duration: float):
        """Record task completion"""
        self.tasks_completed.labels(
            agent_type=agent_type,
            task_type=task_type,
            status=status
        ).inc()
        self.task_duration.labels(
            agent_type=agent_type,
            task_type=task_type
        ).observe(duration)
    
    def record_agent_health(self, health_data: Dict[str, Any]):
        """Record agent health metrics"""
        self.active_agents.labels(agent_type='total').set(health_data.get('running', 0))
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        return generate_latest().decode('utf-8')
