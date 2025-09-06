from core.automation_manager import AutomationManager
from core.trace_manager import TraceManager
import json

def test_both_systems():
    """Probar tanto el sistema básico como el de trazas"""
    
    print("=== PRUEBA SISTEMA BÁSICO (EXISTENTE) ===")
    
    # Sistema básico existente
    automation_manager = AutomationManager()
    
    # Verificar estado
    status = automation_manager.get_system_status()
    print("Estado del sistema:", json.dumps(status, indent=2, default=str))
    
    # Prueba básica de Excel
    excel_result = automation_manager.execute_task('excel_update', {
        'operation': 'insert_row',
        'file_path': './output/test_basico.xlsx',
        'row_data': ['TEST001', 'Prueba básica', 10.50, 5]
    })
    print("Resultado Excel:", json.dumps(excel_result, indent=2, default=str))
    
    print("\n=== PRUEBA SISTEMA DE TRAZAS (NUEVO) ===")
    
    # Sistema de trazas nuevo
    trace_manager = TraceManager(automation_manager)
    
    # Configuración de traza simple
    trace_config = {
        "order_filters": {"status": "pending"},
        "auto_process": True,
        "max_orders": 2  # Limitar para prueba
    }
    
    # Iniciar traza
    trace_result = trace_manager.start_full_trace(trace_config)
    print("Resultado traza:", json.dumps(trace_result, indent=2, default=str))
    
    print("\n=== AMBOS SISTEMAS FUNCIONAN INDEPENDIENTEMENTE ===")

if __name__ == "__main__":
    test_both_systems()