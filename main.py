from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from datetime import datetime
import json

# Importar módulos personalizados
from core.automation_manager import AutomationManager
from core.web_controller import WebController
from core.excel_manager import ExcelManager
from core.printer_manager import PrinterManager
from core.trace_manager import TraceManager
from api.routes import automation_routes

app = FastAPI(
    title="AutoFarma - Sistema de Automatización",
    description="Sistema de control remoto para automatización de procesos farmacéuticos",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos para el dashboard
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Incluir rutas de la API
app.include_router(automation_routes.router, prefix="/api/v1")

# Instancias globales de los managers
automation_manager = AutomationManager()
trace_manager = TraceManager(automation_manager)  # NUEVO
web_controller = WebController()
excel_manager = ExcelManager()
printer_manager = PrinterManager()

@app.get("/")
async def root():
    return {
        "message": "AutoFarma API funcionando",
        "timestamp": datetime.now().isoformat(),
        "status": "online"
    }

@app.get("/api/v1/health")
async def health_check():
    """Verificar el estado del sistema"""
    return {
        "status": "healthy",
        "services": {
            "automation": automation_manager.is_ready(),
            "web_control": web_controller.is_ready(),
            "excel": excel_manager.is_ready(),
            "printer": printer_manager.is_ready()
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/trace/start")
async def start_trace(trace_config: dict):
    """Iniciar una traza completa"""
    result = trace_manager.start_full_trace(trace_config)
    return result

@app.get("/api/v1/trace/{trace_id}")
async def get_trace_status(trace_id: str):
    """Obtener estado de una traza"""
    status = trace_manager.get_trace_status(trace_id)
    if status:
        return status
    else:
        raise HTTPException(status_code=404, detail="Traza no encontrada")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )