"""
Agent lifecycle management and orchestration
"""

import uuid
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class AgentManager:
    """Manages agent lifecycle, spawning, and task assignment"""
    
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.agent_types = self._register_agent_types()
        self._lock = asyncio.Lock()
    
    def _register_agent_types(self) -> Dict[str, str]:
        """Register available agent types"""
        return {
            "lead_finder": "LeadFinderAgent",
            "email_crafter": "EmailCrafterAgent",
            "scheduler": "SchedulerAgent",
            "negotiator": "NegotiatorAgent",
            "closer": "ClosingSpecialistAgent",
            "sentiment_analyst": "SentimentAnalystAgent",
            "competitor_tracker": "CompetitorTrackerAgent",
            "followup_manager": "FollowUpManagerAgent",
            "crm_sync": "CRMSyncAgent",
            "report_generator": "ReportGeneratorAgent",
        }
    
    async def spawn(self, agent_type: str, config: Dict[str, Any], priority: int = 5) -> str:
        """Spawn a new agent instance"""
        if agent_type not in self.agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(self.agent_types.keys())}")
        
        agent_id = str(uuid.uuid4())
        
        async with self._lock:
            self.agents[agent_id] = {
                "id": agent_id,
                "type": agent_type,
                "class_name": self.agent_types[agent_type],
                "config": config,
                "priority": priority,
                "status": "running",
                "created_at": datetime.utcnow(),
                "last_heartbeat": datetime.utcnow(),
                "tasks_completed": 0,
                "current_task": None,
            }
        
        logger.info("Agent spawned", agent_id=agent_id, agent_type=agent_type)
        return agent_id
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent"""
        async with self._lock:
            agent = self.agents.get(agent_id)
            if not agent:
                return None
            
            return {
                "agent_id": agent["id"],
                "agent_type": agent["type"],
                "status": agent["status"],
                "current_task": agent["current_task"],
                "tasks_completed": agent["tasks_completed"],
                "last_heartbeat": agent["last_heartbeat"].isoformat(),
            }
    
    async def terminate(self, agent_id: str) -> bool:
        """Terminate a running agent"""
        async with self._lock:
            if agent_id not in self.agents:
                return False
            
            del self.agents[agent_id]
            logger.info("Agent terminated", agent_id=agent_id)
            return True
    
    async def assign_task(self, agent_id: str, task_type: str, payload: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
        """Assign a task to an agent"""
        async with self._lock:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent = self.agents[agent_id]
            if agent["status"] != "running":
                raise ValueError(f"Agent {agent_id} is not running")
            
            task_id = str(uuid.uuid4())
            agent["current_task"] = {
                "task_id": task_id,
                "task_type": task_type,
                "payload": payload,
                "assigned_at": datetime.utcnow(),
                "timeout": timeout,
            }
        
        # Simulate task execution (in real implementation, this would send to message queue)
        estimated_time = 30  # seconds
        
        return {
            "task_id": task_id,
            "estimated_time": estimated_time,
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents"""
        async with self._lock:
            total = len(self.agents)
            running = sum(1 for a in self.agents.values() if a["status"] == "running")
            
            return {
                "total_agents": total,
                "running": running,
                "idle": total - running,
                "health": "healthy" if running == total else "degraded",
            }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cluster statistics"""
        async with self._lock:
            by_type = {}
            for agent in self.agents.values():
                agent_type = agent["type"]
                if agent_type not in by_type:
                    by_type[agent_type] = {"count": 0, "tasks_completed": 0}
                by_type[agent_type]["count"] += 1
                by_type[agent_type]["tasks_completed"] += agent["tasks_completed"]
            
            return {
                "total_agents": len(self.agents),
                "by_type": by_type,
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def shutdown(self):
        """Gracefully shutdown all agents"""
        async with self._lock:
            for agent_id in list(self.agents.keys()):
                logger.info("Shutting down agent", agent_id=agent_id)
                del self.agents[agent_id]
