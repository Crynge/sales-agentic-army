"""
Base agent class with common functionality
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.status = "initialized"
        self.created_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.tasks_completed = 0
        self.current_task: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task and return result"""
        pass
    
    async def heartbeat(self) -> Dict[str, Any]:
        """Send heartbeat signal"""
        self.last_heartbeat = datetime.utcnow()
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "timestamp": self.last_heartbeat.isoformat(),
        }
    
    def update_status(self, status: str):
        """Update agent status"""
        self.status = status
        logger.debug(f"Agent {self.agent_id} status updated to {status}")
