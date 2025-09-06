from core.automation_manager import AutomationManager
from core.trace_manager import TraceManager
import json

def test_complete_trace():
    """Prueba del sistema de traza completo"""
    
    # Crear instancias
    automation_manager = AutomationManager()
    trace_manager = TraceManager(automation_manager)
    
    # Configuración de la traza
    trace_config = {
        "order_filters": {
            "date_from": "2024-01-01",
            "status": "pending"
        },
        "auto_process": True,
        "max_orders": 10  # Limitar para prueba
    }
    
    print("=== INICIANDO TRAZA COMPLETA ===")
    
    # Iniciar traza
    result = trace_manager.start_full_trace(trace_config)
    print(json.dumps(result, indent=2, default=str))
    
    if result["success"]:
        trace_id = result["trace_id"]
        
        # Monitorear progreso
        while True:
            status = trace_manager.get_trace_status(trace_id)
            print(f"\nEstado actual: {status['status']}")
            print(f"Pedidos procesados: {len(status.get('processed_orders', []))}")
            print(f"Fallos: {len(status.get('failed_orders', []))}")
            print(f"Intervención humana: {len(status.get('human_intervention_required', []))}")
            
            if status["status"] in ["completed", "failed"]:
                break
            
            # Esperar antes de verificar de nuevo
            import time
            time.sleep(5)
    
    print("=== TRAZA COMPLETADA ===")

if __name__ == "__main__":
    test_complete_trace()