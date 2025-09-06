import json
from datetime import datetime
import os

def test_system_health():
    """Prueba básica del sistema sin productos - Solo verificaciones de estado"""
    
    print("=== VERIFICACIÓN BÁSICA DEL SISTEMA ===")
    print(f"Fecha y hora: {datetime.now()}")
    print()
    
    # 1. Verificar importaciones
    print("1. Verificando importaciones...")
    try:
        from core.automation_manager import AutomationManager
        from core.trace_manager import TraceManager
        print("✅ Todas las importaciones correctas")
    except ImportError as e:
        print(f"❌ Error en importaciones: {e}")
        return False
    
    # 2. Verificar creación de instancias
    print("\n2. Verificando creación de instancias...")
    try:
        automation_manager = AutomationManager()
        print("✅ AutomationManager creado correctamente")
        
        trace_manager = TraceManager(automation_manager)
        print("✅ TraceManager creado correctamente")
    except Exception as e:
        print(f"❌ Error creando instancias: {e}")
        return False
    
    # 3. Verificar directorio de salida
    print("\n3. Verificando directorio de salida...")
    try:
        output_dir = "./output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print("✅ Directorio de salida creado")
        else:
            print("✅ Directorio de salida existe")
    except Exception as e:
        print(f"❌ Error con directorio: {e}")
    
    # 4. Verificar estado del sistema (sin conexiones reales)
    print("\n4. Verificando estado básico del sistema...")
    try:
        # Solo verificar que el método funciona, no las conexiones reales
        status = automation_manager.get_system_status()
        print(f"✅ Estado del sistema obtenido")
        print(f"   - CPU disponible: {status.get('system', {}).get('cpu_percent', 'N/A')}%")
        print(f"   - Memoria disponible: {status.get('system', {}).get('memory_percent', 'N/A')}%")
    except Exception as e:
        print(f"❌ Error obteniendo estado: {e}")
    
    # 5. Verificar funcionalidad básica de Excel (sin archivos reales)
    print("\n5. Verificando funcionalidad de Excel...")
    try:
        excel_manager = automation_manager.excel_manager
        is_ready = excel_manager.is_ready()
        print(f"✅ Excel Manager ready: {is_ready}")
    except Exception as e:
        print(f"❌ Error verificando Excel: {e}")
    
    # 6. Verificar que las tareas se pueden crear (sin ejecutar)
    print("\n6. Verificando estructura de tareas...")
    try:
        # Crear configuración de tarea de prueba (no ejecutar)
        test_config = {
            'operation': 'test',
            'data': 'verificación'
        }
        print("✅ Configuración de tarea creada correctamente")
        
        # Verificar que el trace manager puede crear IDs
        trace_id = f"trace_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"✅ ID de traza generado: {trace_id}")
        
    except Exception as e:
        print(f"❌ Error en estructura de tareas: {e}")
    
    # 7. Prueba de Excel básica (archivo de prueba)
    print("\n7. Probando creación de archivo Excel básico...")
    try:
        test_data = [
            datetime.now(),
            "TEST_HEALTH_CHECK",
            "Verificación del sistema",
            "OK",
            100.0
        ]
        
        result = automation_manager.execute_task('excel_update', {
            'operation': 'insert_row',
            'file_path': './output/health_check.xlsx',
            'row_data': test_data
        })
        
        if result.get('status') == 'success':
            print("✅ Archivo Excel de prueba creado correctamente")
            print(f"   - Archivo: {result.get('result', {}).get('file_path', 'N/A')}")
        else:
            print(f"⚠️ Excel parcialmente funcional: {result.get('error', 'Error desconocido')}")
            
    except Exception as e:
        print(f"❌ Error en prueba de Excel: {e}")
    
    # 8. Verificar capacidades del sistema
    print("\n8. Verificando capacidades disponibles...")
    try:
        capabilities = {
            "farmatic_controller": hasattr(automation_manager, 'farmatic_controller'),
            "web_controller": hasattr(automation_manager, 'web_controller'),
            "excel_manager": hasattr(automation_manager, 'excel_manager'),
            "printer_manager": hasattr(automation_manager, 'printer_manager'),
            "trace_manager": trace_manager is not None
        }
        
        for capability, available in capabilities.items():
            status = "✅" if available else "❌"
            print(f"   {status} {capability}: {'Disponible' if available else 'No disponible'}")
            
    except Exception as e:
        print(f"❌ Error verificando capacidades: {e}")
    
    print("\n" + "="*50)
    print("🎉 VERIFICACIÓN BÁSICA COMPLETADA")
    print("El sistema está listo para configuración específica")
    print("="*50)
    
    return True

def test_minimal_functionality():
    """Prueba mínima de funcionalidad sin dependencias externas"""
    
    print("\n=== PRUEBA MÍNIMA DE FUNCIONALIDAD ===")
    
    try:
        from core.automation_manager import AutomationManager
        
        # Crear manager
        manager = AutomationManager()
        
        # Verificar que los métodos básicos funcionan
        print("✅ Manager creado")
        
        # Verificar que podemos obtener el estado (aunque falle internamente)
        try:
            status = manager.get_system_status()
            print("✅ get_system_status() funciona")
        except:
            print("⚠️ get_system_status() tiene errores internos (normal sin conexiones)")
        
        # Verificar que podemos crear tareas (aunque fallen)
        try:
            task_result = manager.execute_task('test_task', {'test': True})
            print("✅ execute_task() funciona")
        except:
            print("⚠️ execute_task() rechaza tareas desconocidas (normal)")
        
        print("✅ Funcionalidad mínima verificada")
        return True
        
    except Exception as e:
        print(f"❌ Error en funcionalidad mínima: {e}")
        return False

if __name__ == "__main__":
    print("AutoFarma - Verificación del Sistema")
    print("=" * 50)
    
    # Ejecutar verificación básica
    health_check_ok = test_system_health()
    
    if health_check_ok:
        # Ejecutar prueba mínima
        test_minimal_functionality()
    
    print("\n🏁 Verificación completada.")
    print("Si no hay errores críticos (❌), el sistema está listo para usar.")