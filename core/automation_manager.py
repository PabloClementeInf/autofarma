import logging
import psutil
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Importar los controladores especializados
from .farmatic_controller import FarmaticController
from .web_controller import WebController
from .excel_manager import ExcelManager
from .printer_manager import PrinterManager

class AutomationManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running_tasks = {}
        self.task_history = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Inicializar controladores especializados
        self.farmatic_controller = FarmaticController()
        self.web_controller = WebController()
        self.excel_manager = ExcelManager()
        self.printer_manager = PrinterManager()
        
        # Estado de conexiones
        self.connections_status = {
            "farmatic": False,
            "web_browser": False,
            "excel": False,
            "printer": False
        }
        
    def is_ready(self) -> bool:
        """Verificar si el manager está listo"""
        try:
            # Verificar recursos del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Verificar controladores
            controllers_ready = (
                self.farmatic_controller is not None and
                self.web_controller.is_ready() and
                self.excel_manager.is_ready() and
                self.printer_manager.is_ready()
            )
            
            return cpu_percent < 90 and memory.percent < 90 and controllers_ready
            
        except Exception as e:
            self.logger.error(f"Error verificando estado: {e}")
            return False
    
    def get_system_status(self) -> Dict:
        """Obtener estado completo del sistema"""
        try:
            # Estado del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Estado de controladores
            self.connections_status.update({
                "farmatic": self.farmatic_controller.find_farmatic_window(),
                "web_browser": self.web_controller.is_ready(),
                "excel": self.excel_manager.is_ready(),
                "printer": self.printer_manager.is_ready()
            })
            
            return {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "available_memory_gb": round(memory.available / (1024**3), 2)
                },
                "connections": self.connections_status,
                "running_tasks": len(self.get_running_tasks()),
                "total_tasks_today": len([t for t in self.task_history 
                                        if t.get('start_time', datetime.min).date() == datetime.now().date()])
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado del sistema: {e}")
            return {"error": str(e)}
    
    def execute_task(self, task_type: str, task_config: Dict) -> Dict:
        """Ejecutar una tarea de automatización"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            self.running_tasks[task_id] = {
                "type": task_type,
                "config": task_config,
                "status": "running",
                "start_time": datetime.now(),
                "progress": 0
            }
            
            # Ejecutar según el tipo de tarea
            if task_type == "farmatic_search":
                result = self._execute_farmatic_search(task_config)
            elif task_type == "web_data_collection":
                result = self._execute_web_data_collection(task_config)
            elif task_type == "excel_update":
                result = self._execute_excel_update(task_config)
            elif task_type == "print_labels":
                result = self._execute_print_labels(task_config)
            elif task_type == "full_workflow":
                result = self._execute_full_workflow(task_config)
            elif task_type == "inventory_sync":
                result = self._execute_inventory_sync(task_config)
            else:
                raise ValueError(f"Tipo de tarea no soportado: {task_type}")
            
            self.running_tasks[task_id]["status"] = "completed"
            self.running_tasks[task_id]["result"] = result
            self.running_tasks[task_id]["end_time"] = datetime.now()
            
            # Agregar a historial
            self.task_history.append(self.running_tasks[task_id].copy())
            
            return {
                "task_id": task_id,
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Error ejecutando tarea {task_id}: {e}")
            self.running_tasks[task_id]["status"] = "failed"
            self.running_tasks[task_id]["error"] = str(e)
            self.running_tasks[task_id]["end_time"] = datetime.now()
            
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }
    
    def _execute_farmatic_search(self, config: Dict) -> Dict:
        """Buscar producto en Farmatic"""
        product_code = config.get('product_code')
        if not product_code:
            raise ValueError("Código de producto requerido")
        
        # Buscar producto en Farmatic
        search_result = self.farmatic_controller.search_product(product_code)
        if not search_result.get('success'):
            return search_result
        
        # Obtener información del producto
        product_info = self.farmatic_controller.get_product_info()
        
        return {
            "search_result": search_result,
            "product_info": product_info
        }
    
    def _execute_web_data_collection(self, config: Dict) -> Dict:
        """Recopilar datos de distribuidores web"""
        product_code = config.get('product_code')
        distributors = config.get('distributors', ['promofarma'])
        credentials = config.get('credentials', {})
        
        results = {}
        
        for distributor in distributors:
            try:
                if distributor == 'promofarma':
                    # Login si hay credenciales
                    if 'promofarma' in credentials:
                        creds = credentials['promofarma']
                        login_result = self.web_controller.login_promofarma(
                            creds['username'], creds['password']
                        )
                        if not login_result.get('success'):
                            results[distributor] = {"error": "Login fallido"}
                            continue
                    
                    # Buscar producto
                    search_result = self.web_controller.search_promofarma(product_code)
                    results[distributor] = search_result
                    
                elif distributor == 'cofares':
                    if 'cofares' in credentials:
                        creds = credentials['cofares']
                        login_result = self.web_controller.login_cofares(
                            creds['username'], creds['password']
                        )
                        if not login_result.get('success'):
                            results[distributor] = {"error": "Login fallido"}
                            continue
                    
                    data_result = self.web_controller.get_cofares_data(product_code)
                    results[distributor] = data_result
                    
                # Agregar más distribuidores según necesidad
                elif distributor == 'alliance':
                    results[distributor] = self.web_controller.process_alliance(product_code)
                elif distributor == 'hefame':
                    results[distributor] = self.web_controller.process_hefame(product_code)
                elif distributor == 'bidafarma':
                    results[distributor] = self.web_controller.process_bidafarma(product_code)
                elif distributor == 'actibios':
                    quantity = config.get('purchase_quantity', 1)
                    results[distributor] = self.web_controller.purchase_actibios(product_code, quantity)
                    
            except Exception as e:
                results[distributor] = {"error": str(e)}
        
        return {"distributor_data": results}
    
    def _execute_excel_update(self, config: Dict) -> Dict:
        """Actualizar datos en Excel"""
        operation = config.get('operation', 'insert_row')
        
        if operation == 'insert_row':
            file_path = config.get('file_path')
            row_data = config.get('row_data')
            sheet_name = config.get('sheet_name')
            
            return self.excel_manager.insert_row_data(file_path, row_data, sheet_name)
            
        elif operation == 'create_report':
            data = config.get('data')
            report_name = config.get('report_name')
            
            return self.excel_manager.create_pharmacy_report(data, report_name)
            
        elif operation == 'update_inventory':
            product_updates = config.get('product_updates')
            
            return self.excel_manager.update_inventory_excel(product_updates)
        
        else:
            raise ValueError(f"Operación Excel no soportada: {operation}")
    
    def _execute_print_labels(self, config: Dict) -> Dict:
        """Imprimir etiquetas"""
        print_type = config.get('print_type', 'label')
        printer_name = config.get('printer_name')
        
        if print_type == 'label':
            label_data = config.get('label_data')
            return self.printer_manager.print_promofarma_label(label_data, printer_name)
            
        elif print_type == 'albaran':
            albaran_data = config.get('albaran_data')
            return self.printer_manager.print_albaran(albaran_data, printer_name)
        
        else:
            raise ValueError(f"Tipo de impresión no soportado: {print_type}")
    
    def _execute_full_workflow(self, config: Dict) -> Dict:
        """Ejecutar workflow completo: Farmatic -> Web -> Excel -> Print"""
        product_code = config.get('product_code')
        workflow_steps = config.get('steps', ['farmatic', 'web', 'excel'])
        
        workflow_results = {}
        
        # Paso 1: Buscar en Farmatic
        if 'farmatic' in workflow_steps:
            farmatic_result = self._execute_farmatic_search({'product_code': product_code})
            workflow_results['farmatic'] = farmatic_result
        
        # Paso 2: Recopilar datos web
        if 'web' in workflow_steps:
            web_config = {
                'product_code': product_code,
                'distributors': config.get('distributors', ['promofarma']),
                'credentials': config.get('credentials', {})
            }
            web_result = self._execute_web_data_collection(web_config)
            workflow_results['web'] = web_result
        
        # Paso 3: Actualizar Excel
        if 'excel' in workflow_steps:
            # Compilar datos para Excel
            excel_data = self._compile_workflow_data(workflow_results, product_code)
            excel_config = {
                'operation': 'insert_row',
                'file_path': config.get('excel_file', './output/productos_consultados.xlsx'),
                'row_data': excel_data
            }
            excel_result = self._execute_excel_update(excel_config)
            workflow_results['excel'] = excel_result
        
        # Paso 4: Imprimir si es necesario
        if 'print' in workflow_steps and config.get('print_data'):
            print_config = {
                'print_type': 'label',
                'label_data': config.get('print_data')
            }
            print_result = self._execute_print_labels(print_config)
            workflow_results['print'] = print_result
        
        return {"workflow_results": workflow_results}
    
    def _execute_inventory_sync(self, config: Dict) -> Dict:
        """Sincronizar inventario entre Farmatic y distribuidores"""
        products = config.get('products', [])
        distributors = config.get('distributors', ['promofarma'])
        
        sync_results = []
        
        for product_code in products:
            try:
                # Obtener datos de Farmatic
                farmatic_data = self._execute_farmatic_search({'product_code': product_code})
                
                # Obtener datos de distribuidores
                web_data = self._execute_web_data_collection({
                    'product_code': product_code,
                    'distributors': distributors,
                    'credentials': config.get('credentials', {})
                })
                
                # Compilar resultado
                sync_results.append({
                    'product_code': product_code,
                    'farmatic_data': farmatic_data,
                    'distributor_data': web_data,
                    'timestamp': datetime.now()
                })
                
            except Exception as e:
                sync_results.append({
                    'product_code': product_code,
                    'error': str(e),
                    'timestamp': datetime.now()
                })
        
        # Guardar resultados en Excel
        excel_config = {
            'operation': 'create_report',
            'data': sync_results,
            'report_name': f"sincronizacion_inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
        excel_result = self._execute_excel_update(excel_config)
        
        return {
            "sync_results": sync_results,
            "excel_report": excel_result
        }
    
    def _compile_workflow_data(self, workflow_results: Dict, product_code: str) -> List:
        """Compilar datos del workflow para Excel"""
        row_data = [
            datetime.now(),  # Fecha
            product_code,    # Código producto
        ]
        
        # Datos de Farmatic
        farmatic_info = workflow_results.get('farmatic', {}).get('product_info', {})
        row_data.extend([
            farmatic_info.get('name', ''),
            farmatic_info.get('price', ''),
            farmatic_info.get('stock', '')
        ])
        
        # Datos de distribuidores
        web_data = workflow_results.get('web', {}).get('distributor_data', {})
        for distributor in ['promofarma', 'cofares', 'alliance']:
            dist_data = web_data.get(distributor, {})
            if 'product_info' in dist_data:
                row_data.append(dist_data['product_info'].get('price', ''))
            else:
                row_data.append('')
        
        return row_data
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Obtener el estado de una tarea"""
        return self.running_tasks.get(task_id)
    
    def get_running_tasks(self) -> Dict:
        """Obtener todas las tareas en ejecución"""
        return {
            task_id: task_info 
            for task_id, task_info in self.running_tasks.items() 
            if task_info["status"] == "running"
        }
    
    def cancel_task(self, task_id: str) -> Dict:
        """Cancelar una tarea en ejecución"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id]["status"] = "cancelled"
            self.running_tasks[task_id]["end_time"] = datetime.now()
            return {"success": True, "message": f"Tarea {task_id} cancelada"}
        else:
            return {"success": False, "error": "Tarea no encontrada"}
    
    def cleanup_completed_tasks(self, max_history: int = 100):
        """Limpiar tareas completadas del historial"""
        # Mantener solo las tareas más recientes
        if len(self.task_history) > max_history:
            self.task_history = self.task_history[-max_history:]
        
        # Limpiar tareas completadas de running_tasks
        completed_tasks = [
            task_id for task_id, task_info in self.running_tasks.items()
            if task_info["status"] in ["completed", "failed", "cancelled"]
        ]
        
        for task_id in completed_tasks:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]