from core.automation_manager import AutomationManager
import json

def test_basic_functionality():
    """Prueba básica del sistema"""
    
    # Crear instancia del manager
    manager = AutomationManager()
    
    # 1. Verificar estado del sistema
    print("=== ESTADO DEL SISTEMA ===")
    status = manager.get_system_status()
    print(json.dumps(status, indent=2, default=str))
    
    # 2. Prueba de búsqueda en Farmatic (ajustar código de producto real)
    print("\n=== PRUEBA FARMATIC ===")
    farmatic_config = {
        'product_code': '12345'  # Cambiar por código real
    }
    
    result = manager.execute_task('farmatic_search', farmatic_config)
    print(json.dumps(result, indent=2, default=str))
    
    # 3. Prueba de Excel básica
    print("\n=== PRUEBA EXCEL ===")
    excel_config = {
        'operation': 'insert_row',
        'file_path': './output/test_productos.xlsx',
        'row_data': ['12345', 'Producto Test', 25.50, 10, 'Test']
    }
    
    result = manager.execute_task('excel_update', excel_config)
    print(json.dumps(result, indent=2, default=str))
    
    # 4. Prueba de impresora (verificar disponibilidad)
    print("\n=== PRUEBA IMPRESORA ===")
    print("Impresoras disponibles:", manager.printer_manager.get_available_printers())

if __name__ == "__main__":
    test_basic_functionality()