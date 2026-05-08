"""
FastAPI orchestrator for Sales Agentic Army
Manages agent lifecycle, task distribution, and health monitoring
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
import structlog
import asyncio
from datetime import datetime

from .agent_manager import AgentManager
from .metrics import MetricsCollector
from ..memory.vector_store import VectorMemoryManager

logger = structlog.get_logger(__name__)


class AgentSpawnRequest(BaseModel):
    agent_type: str = Field(..., description="Type of agent to spawn")
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")
    priority: int = Field(default=5, ge=1, le=10, description="Priority level 1-10")


class TaskAssignmentRequest(BaseModel):
    agent_id: str
    task_type: str
    payload: Dict[str, Any]
    timeout_seconds: Optional[int] = 300


class AgentStatusResponse(BaseModel):
    agent_id: str
    agent_type: str
    status: str
    current_task: Optional[str]
    tasks_completed: int
    last_heartbeat: datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Sales Agentic Army Orchestrator")
    app.state.agent_manager = AgentManager()
    app.state.metrics = MetricsCollector()
    app.state.memory_manager = VectorMemoryManager()
    
    # Start background health checker
    asyncio.create_task(health_check_loop(app))
    
    yield
    
    # Shutdown
    logger.info("Shutting down orchestrator")
    await app.state.agent_manager.shutdown()


async def health_check_loop(app: FastAPI):
    """Background health monitoring loop"""
    while True:
        try:
            await asyncio.sleep(30)
            manager = app.state.agent_manager
            health = await manager.health_check()
            app.state.metrics.record_agent_health(health)
        except Exception as e:
            logger.error("Health check failed", error=str(e))


app = FastAPI(
    title="Sales Agentic Army Orchestrator",
    description="Enterprise-grade multi-agent orchestration system for autonomous sales",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint"""
    metrics = app.state.metrics
    return metrics.export_prometheus()


@app.post("/agents/spawn", response_model=Dict[str, str])
async def spawn_agent(request: AgentSpawnRequest):
    """Spawn a new agent instance"""
    try:
        manager = app.state.agent_manager
        agent_id = await manager.spawn(
            agent_type=request.agent_type,
            config=request.config,
            priority=request.priority,
        )
        
        logger.info("Agent spawned", agent_id=agent_id, agent_type=request.agent_type)
        
        return {
            "agent_id": agent_id,
            "status": "running",
            "message": f"Agent {request.agent_type} spawned successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to spawn agent")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/agents/{agent_id}", response_model=AgentStatusResponse)
async def get_agent_status(agent_id: str):
    """Get status of a specific agent"""
    manager = app.state.agent_manager
    status = await manager.get_agent_status(agent_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return status


@app.delete("/agents/{agent_id}")
async def terminate_agent(agent_id: str):
    """Terminate a running agent"""
    manager = app.state.agent_manager
    success = await manager.terminate(agent_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"message": f"Agent {agent_id} terminated successfully"}


@app.post("/tasks/assign")
async def assign_task(request: TaskAssignmentRequest, background_tasks: BackgroundTasks):
    """Assign a task to an agent"""
    manager = app.state.agent_manager
    
    try:
        result = await manager.assign_task(
            agent_id=request.agent_id,
            task_type=request.task_type,
            payload=request.payload,
            timeout=request.timeout_seconds,
        )
        
        return {
            "task_id": result["task_id"],
            "status": "queued",
            "estimated_completion": result["estimated_time"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.websocket("/ws/agents")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send agent statistics
            stats = await app.state.agent_manager.get_statistics()
            await websocket.send_json(stats)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")


@app.get("/cluster/statistics")
async def get_cluster_statistics():
    """Get comprehensive cluster statistics"""
    manager = app.state.agent_manager
    return await manager.get_statistics()
