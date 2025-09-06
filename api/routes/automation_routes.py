from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

router = APIRouter()

class TaskRequest(BaseModel):
    task_type: str
    config: Dict[str, Any]
    priority: Optional[int] = 1

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    timestamp: datetime

@router.post("/tasks", response_model=TaskResponse)
async def create_task(task_request: TaskRequest):
    """Crear y ejecutar una nueva tarea"""
    try:
        # Aquí se conectará con el automation_manager real
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            message=f"Tarea {task_request.task_type} creada exitosamente",
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Obtener el estado de una tarea específica"""
    # Placeholder - conectar con automation_manager
    return {
        "task_id": task_id,
        "status": "running",
        "progress": 50,
        "timestamp": datetime.now()
    }

@router.get("/tasks")
async def list_tasks():
    """Listar todas las tareas"""
    return {
        "tasks": [],
        "total": 0,
        "timestamp": datetime.now()
    }