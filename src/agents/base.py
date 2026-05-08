"""
Advanced Agent Base Class with Memory, Observability, and Error Handling
Enterprise-grade foundation for all sales agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
from pydantic import BaseModel, Field
import structlog
import asyncio
from datetime import datetime
import uuid
from enum import Enum
import json

logger = structlog.get_logger(__name__)


class AgentStatus(str, Enum):
    """Agent lifecycle states"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    TERMINATED = "terminated"


class TaskPriority(int, Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 3
    NORMAL = 5
    LOW = 7
    BACKGROUND = 10


class TaskResult(BaseModel):
    """Standardized task execution result"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Base configuration for all agents"""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    max_concurrent_tasks: int = 5
    task_timeout_seconds: int = 300
    retry_attempts: int = 3
    memory_enabled: bool = True
    tracing_enabled: bool = True
    log_level: str = "INFO"
    custom_config: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """
    Enterprise base class for all sales agents.
    
    Provides:
    - Lifecycle management
    - Memory integration
    - Observability (metrics, tracing, logging)
    - Error handling with retries
    - Task queue management
    - Health monitoring
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id = config.agent_id
        self.status = AgentStatus.INITIALIZING
        self.current_task: Optional[Dict[str, Any]] = None
        self.tasks_completed: int = 0
        self.tasks_failed: int = 0
        self.created_at: datetime = datetime.utcnow()
        self.last_heartbeat: datetime = datetime.utcnow()
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._memory = None
        self._tracer = None
        
        logger.info(
            "Agent initializing",
            agent_id=self.agent_id,
            agent_type=self.__class__.__name__,
        )
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        Execute a single task. Must be implemented by subclasses.
        
        Args:
            task: Task dictionary with type, payload, and metadata
            
        Returns:
            TaskResult with success status and data
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        pass
    
    async def initialize(self) -> None:
        """Initialize agent resources (memory, connections, etc.)"""
        try:
            # Initialize memory if enabled
            if self.config.memory_enabled:
                await self._init_memory()
            
            # Initialize tracing if enabled
            if self.config.tracing_enabled:
                await self._init_tracing()
            
            self.status = AgentStatus.IDLE
            self._running = True
            
            logger.info("Agent initialized successfully", agent_id=self.agent_id)
        except Exception as e:
            logger.exception("Failed to initialize agent", error=str(e))
            self.status = AgentStatus.ERROR
            raise
    
    async def _init_memory(self) -> None:
        """Initialize vector memory store"""
        try:
            from ..memory.vector_store import VectorMemoryManager
            self._memory = VectorMemoryManager(agent_id=self.agent_id)
            await self._memory.initialize()
            logger.debug("Memory initialized", agent_id=self.agent_id)
        except Exception as e:
            logger.warning("Memory initialization failed, continuing without", error=str(e))
            self._memory = None
    
    async def _init_tracing(self) -> None:
        """Initialize distributed tracing"""
        try:
            from opentelemetry import trace
            tracer_provider = trace.get_tracer_provider()
            self._tracer = tracer_provider.get_tracer(f"agent.{self.__class__.__name__}")
        except Exception as e:
            logger.warning("Tracing initialization failed", error=str(e))
            self._tracer = None
    
    async def process_task(self, task: Dict[str, Any]) -> TaskResult:
        """
        Process a task with error handling, retries, and metrics.
        
        Args:
            task: Task to process
            
        Returns:
            TaskResult with execution outcome
        """
        start_time = datetime.utcnow()
        self.status = AgentStatus.PROCESSING
        self.current_task = task
        self.last_heartbeat = datetime.utcnow()
        
        task_type = task.get("type", "unknown")
        task_id = task.get("id", str(uuid.uuid4()))
        
        span_context = None
        if self._tracer:
            with self._tracer.start_as_current_span(f"task.{task_type}") as span:
                span.set_attribute("task.id", task_id)
                span.set_attribute("agent.id", self.agent_id)
                span_context = span
        
        try:
            logger.debug(
                "Executing task",
                task_id=task_id,
                task_type=task_type,
                agent_id=self.agent_id,
            )
            
            # Execute with retry logic
            result = await self._execute_with_retry(task)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if result.success:
                self.tasks_completed += 1
                logger.info(
                    "Task completed successfully",
                    task_id=task_id,
                    execution_time_ms=execution_time,
                )
                
                # Store in memory if enabled
                if self._memory:
                    await self._memory.store_task_result(task, result)
            else:
                self.tasks_failed += 1
                logger.warning(
                    "Task failed",
                    task_id=task_id,
                    error=result.error,
                )
            
            result.execution_time_ms = execution_time
            return result
            
        except Exception as e:
            self.tasks_failed += 1
            logger.exception(
                "Task execution failed",
                task_id=task_id,
                error=str(e),
            )
            
            return TaskResult(
                success=False,
                error=str(e),
                metadata={"task_id": task_id, "agent_id": self.agent_id},
            )
        finally:
            self.status = AgentStatus.IDLE
            self.current_task = None
            self.last_heartbeat = datetime.utcnow()
    
    async def _execute_with_retry(self, task: Dict[str, Any]) -> TaskResult:
        """Execute task with exponential backoff retry"""
        last_error = None
        
        for attempt in range(self.config.retry_attempts + 1):
            try:
                result = await self.execute(task)
                if result.success:
                    return result
                last_error = result.error
            except Exception as e:
                last_error = str(e)
            
            if attempt < self.config.retry_attempts:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(
                    "Retrying task",
                    attempt=attempt + 1,
                    wait_time=wait_time,
                    error=last_error,
                )
                await asyncio.sleep(wait_time)
        
        return TaskResult(
            success=False,
            error=f"Failed after {self.config.retry_attempts + 1} attempts: {last_error}",
            metadata={"task": task},
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Return current health status"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "status": self.status.value,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "uptime_seconds": (datetime.utcnow() - self.created_at).total_seconds(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "memory_enabled": self._memory is not None,
            "queue_size": self._task_queue.qsize(),
        }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the agent"""
        logger.info("Shutting down agent", agent_id=self.agent_id)
        self._running = False
        self.status = AgentStatus.TERMINATED
        
        # Cleanup resources
        if self._memory:
            await self._memory.close()
        
        logger.info("Agent shutdown complete", agent_id=self.agent_id)
    
    async def enqueue_task(self, task: Dict[str, Any]) -> None:
        """Add task to internal queue"""
        await self._task_queue.put(task)
        logger.debug("Task enqueued", task_id=task.get("id"), agent_id=self.agent_id)
    
    async def dequeue_task(self) -> Optional[Dict[str, Any]]:
        """Get next task from queue"""
        try:
            task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
            return task
        except asyncio.TimeoutError:
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return agent statistics"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "status": self.status.value,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": self.tasks_completed / max(1, self.tasks_completed + self.tasks_failed),
            "created_at": self.created_at.isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.created_at).total_seconds(),
        }
