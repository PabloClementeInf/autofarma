import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

class TraceStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_HUMAN_INTERVENTION = "requires_human_intervention"

class TraceStep(Enum):
    GET_ORDER_LIST = "get_order_list"
    EXTRACT_EAN = "extract_ean"
    CHECK_BINARY_DASHBOARD = "check_binary_dashboard"
    CHECK_OWN_STOCK = "check_own_stock"
    CHECK_STOCK_LEVEL = "check_stock_level"
    CHECK_CN_EXISTS = "check_cn_exists"
    SEARCH_DISTRIBUTORS = "search_distributors"
    REGISTER_PRODUCT_FARMATIC = "register_product_farmatic"
    ADD_PROMOFARMA_WALLET = "add_promofarma_wallet"
    CHECK_PROMOFARMA_RESULT = "check_promofarma_result"
    REGISTER_NEW_PRODUCT = "register_new_product"
    SELECT_BEST_MARGIN = "select_best_margin"
    ASSIGN_SUPPLIER = "assign_supplier"
    RELOAD_AND_SEND = "reload_and_send"
    EXCEL_UPDATE = "excel_update"
    PRINT_DOCUMENTS = "print_documents"

class TraceManager:
    def __init__(self, automation_manager):
        self.logger = logging.getLogger(__name__)
        self.automation_manager = automation_manager
        self.active_traces = {}
        self.completed_traces = []
        self.supplier_priorities = {}  # Se cargará desde configuración
        
    def start_full_trace(self, config: Dict) -> Dict:
        """Iniciar una traza completa desde lista de pedidos"""
        trace_id = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            trace_data = {
                "trace_id": trace_id,
                "status": TraceStatus.IN_PROGRESS,
                "start_time": datetime.now(),
                "current_step": TraceStep.GET_ORDER_LIST,
                "orders": [],
                "processed_orders": [],
                "failed_orders": [],
                "human_intervention_required": [],
                "config": config
            }
            
            self.active_traces[trace_id] = trace_data
            
            # Iniciar procesamiento
            result = self._process_trace(trace_id)
            
            return {
                "success": True,
                "trace_id": trace_id,
                "initial_result": result
            }
            
        except Exception as e:
            self.logger.error(f"Error iniciando traza: {e}")
            return {"success": False, "error": str(e)}
    
    def _process_trace(self, trace_id: str) -> Dict:
        """Procesar una traza completa"""
        trace_data = self.active_traces[trace_id]
        
        try:
            # Paso 1: Obtener lista de pedidos
            orders_result = self._get_order_list(trace_data)
            if not orders_result["success"]:
                return orders_result
            
            trace_data["orders"] = orders_result["orders"]
            
            # Procesar cada pedido
            for order in trace_data["orders"]:
                order_result = self._process_single_order(trace_data, order)
                
                if order_result["status"] == "completed":
                    trace_data["processed_orders"].append(order_result)
                elif order_result["status"] == "failed":
                    trace_data["failed_orders"].append(order_result)
                elif order_result["status"] == "requires_human_intervention":
                    trace_data["human_intervention_required"].append(order_result)
            
            # Finalizar traza
            trace_data["status"] = TraceStatus.COMPLETED
            trace_data["end_time"] = datetime.now()
            
            return {
                "success": True,
                "processed": len(trace_data["processed_orders"]),
                "failed": len(trace_data["failed_orders"]),
                "human_intervention": len(trace_data["human_intervention_required"])
            }
            
        except Exception as e:
            trace_data["status"] = TraceStatus.FAILED
            trace_data["error"] = str(e)
            self.logger.error(f"Error procesando traza {trace_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _process_single_order(self, trace_data: Dict, order: Dict) -> Dict:
        """Procesar un pedido individual siguiendo la traza completa"""
        order_id = order.get("id", "unknown")
        quantity = order.get("quantity", 0)
        
        try:
            # Paso 1: Extraer EAN del pedido
            ean = self._extract_ean_from_order(order)
            if not ean:
                return {"status": "failed", "error": "No se pudo extraer EAN", "order": order}
            
            # Paso 2: Consultar Binary Dashboard
            binary_result = self._check_binary_dashboard(ean)
            if not binary_result["success"]:
                return {"status": "failed", "error": "Error consultando Binary", "order": order}
            
            product_info = binary_result["product_info"]
            
            # Paso 3: ¿Está en stock propio?
            if product_info.get("own_stock", 0) > 0:
                # Paso 4: ¿Es mayor que 1?
                if product_info["own_stock"] > 1:
                    # Stock suficiente - ir directo a gestión e imprimir
                    return self._complete_order_processing(order, product_info, "own_stock")
                
                # Paso 5: ¿Es igual a 1?
                elif product_info["own_stock"] == 1:
                    # Alerta de factor humano
                    self._log_human_factor_alert(order, product_info)
                    return {"status": "requires_human_intervention", "reason": "stock_level_1", "order": order, "product_info": product_info}
            
            # Paso 6: No está en stock propio - ¿Tiene CN?
            cn = product_info.get("cn")
            if not cn:
                # No tiene CN - ir a Actibios y comprar
                return self._process_actibios_purchase(order, product_info)
            
            # Paso 7: Tiene CN - buscar en distribuidores
            distributor_results = self._search_distributors_with_cn(cn)
            
            # Paso 8: ¿Tiene resultado en distribuidores?
            if not distributor_results.get("has_results", False):
                # No encontrado - dar de alta producto
                registration_result = self._register_new_product_complete(product_info)
                if not registration_result["success"]:
                    return {"status": "failed", "error": "Error registrando producto", "order": order}
            
            # Paso 9: Ir a Farmatic y meter CN en cartera Promofarma
            farmatic_result = self._add_to_promofarma_wallet(cn)
            if not farmatic_result["success"]:
                return {"status": "failed", "error": "Error añadiendo a cartera Promofarma", "order": order}
            
            # Paso 10: ¿Cartera Promofarma devuelve resultado?
            promofarma_result = self._check_promofarma_result(cn)
            if not promofarma_result["success"]:
                # Dar de alta producto y reintentar
                registration_result = self._register_new_product_complete(product_info)
                if registration_result["success"]:
                    promofarma_result = self._check_promofarma_result(cn)
            
            if not promofarma_result["success"]:
                return {"status": "failed", "error": "No se pudo obtener resultado de Promofarma", "order": order}
            
            # Paso 11: Seleccionar mejor margen según prioridad
            best_supplier = self._select_best_margin_supplier(promofarma_result["suppliers"])
            
            # Paso 12: Asignar proveedor, recargar y enviar
            final_result = self._assign_supplier_and_complete(order, best_supplier)
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error procesando pedido {order_id}: {e}")
            return {"status": "failed", "error": str(e), "order": order}
    
    def _get_order_list(self, trace_data: Dict) -> Dict:
        """Obtener lista de pedidos desde Farmatic"""
        try:
            # Configurar búsqueda de pedidos en Farmatic
            farmatic_config = {
                "action": "get_order_list",
                "filters": trace_data["config"].get("order_filters", {})
            }
            
            # Ejecutar búsqueda en Farmatic
            result = self.automation_manager.farmatic_controller.get_order_list(farmatic_config)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_ean_from_order(self, order: Dict) -> Optional[str]:
        """Extraer EAN del pedido"""
        # Implementar lógica para extraer EAN según estructura del pedido
        return order.get("ean") or order.get("barcode")
    
    def _check_binary_dashboard(self, ean: str) -> Dict:
        """Consultar Binary Dashboard"""
        try:
            # Configurar consulta a Binary Dashboard
            dashboard_config = {
                "action": "product_lookup",
                "ean": ean,
                "fields": ["own_stock", "cn", "description", "iva", "laboratory", "family"]
            }
            
            # Ejecutar consulta
            result = self.automation_manager.web_controller.query_binary_dashboard(dashboard_config)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _search_distributors_with_cn(self, cn: str) -> Dict:
        """Buscar en distribuidores usando CN"""
        try:
            distributors = ["cofares", "alliance", "hefame", "bidafarma"]
            results = {}
            
            for distributor in distributors:
                dist_result = self.automation_manager.web_controller.search_by_cn(distributor, cn)
                results[distributor] = dist_result
            
            # Verificar si algún distribuidor tiene resultados
            has_results = any(result.get("success") and result.get("found") for result in results.values())
            
            return {
                "success": True,
                "has_results": has_results,
                "distributor_results": results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _register_new_product_complete(self, product_info: Dict) -> Dict:
        """Dar de alta producto completo en Binary"""
        try:
            registration_data = {
                "cn": product_info.get("cn"),
                "description": product_info.get("description"),
                "iva": product_info.get("iva"),
                "laboratory": product_info.get("laboratory"),
                "family": product_info.get("family"),
                "synonym_ean": product_info.get("ean")
            }
            
            result = self.automation_manager.web_controller.register_product_binary(registration_data)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _add_to_promofarma_wallet(self, cn: str) -> Dict:
        """Añadir CN a cartera Promofarma en Farmatic"""
        try:
            config = {
                "action": "add_to_wallet",
                "wallet_type": "promofarma",
                "cn": cn
            }
            
            result = self.automation_manager.farmatic_controller.manage_wallet(config)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _check_promofarma_result(self, cn: str) -> Dict:
        """Verificar resultado en cartera Promofarma"""
        try:
            config = {
                "action": "check_wallet_result",
                "wallet_type": "promofarma",
                "cn": cn
            }
            
            result = self.automation_manager.farmatic_controller.check_wallet_result(config)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _select_best_margin_supplier(self, suppliers: List[Dict]) -> Dict:
        """Seleccionar mejor margen según prioridades"""
        if not suppliers:
            return None
        
        # Ordenar por prioridad y margen
        sorted_suppliers = sorted(
            suppliers,
            key=lambda x: (
                self.supplier_priorities.get(x.get("name", ""), 999),
                -x.get("margin", 0)
            )
        )
        
        return sorted_suppliers[0]
    
    def _assign_supplier_and_complete(self, order: Dict, supplier: Dict) -> Dict:
        """Asignar proveedor, recargar y completar pedido"""
        try:
            # Asignar proveedor
            assignment_result = self.automation_manager.farmatic_controller.assign_supplier(
                order["id"], supplier
            )
            
            if not assignment_result["success"]:
                return {"status": "failed", "error": "Error asignando proveedor", "order": order}
            
            # Recargar y enviar
            reload_result = self.automation_manager.farmatic_controller.reload_and_send(order["id"])
            
            if not reload_result["success"]:
                return {"status": "failed", "error": "Error recargando y enviando", "order": order}
            
            # Completar con gestión Excel e impresión
            return self._complete_order_processing(order, supplier, "assigned_supplier")
            
        except Exception as e:
            return {"status": "failed", "error": str(e), "order": order}
    
    def _complete_order_processing(self, order: Dict, product_info: Dict, completion_type: str) -> Dict:
        """Completar procesamiento: Excel e impresión"""
        try:
            # Actualizar Excel
            excel_data = self._compile_order_data_for_excel(order, product_info, completion_type)
            excel_result = self.automation_manager.excel_manager.insert_row_data(
                "./output/pedidos_procesados.xlsx",
                excel_data
            )
            
            # Imprimir documentos
            print_result = self._print_order_documents(order, product_info)
            
            return {
                "status": "completed",
                "completion_type": completion_type,
                "order": order,
                "excel_result": excel_result,
                "print_result": print_result
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e), "order": order}
    
    def _process_actibios_purchase(self, order: Dict, product_info: Dict) -> Dict:
        """Procesar compra en Actibios para productos sin CN"""
        try:
            purchase_result = self.automation_manager.web_controller.purchase_actibios(
                product_info.get("ean"), order.get("quantity", 1)
            )
            
            if purchase_result["success"]:
                return self._complete_order_processing(order, product_info, "actibios_purchase")
            else:
                return {"status": "failed", "error": "Error en compra Actibios", "order": order}
                
        except Exception as e:
            return {"status": "failed", "error": str(e), "order": order}
    
    def _log_human_factor_alert(self, order: Dict, product_info: Dict):
        """Registrar alerta de factor humano"""
        alert_data = {
            "timestamp": datetime.now(),
            "order_id": order.get("id"),
            "product_code": product_info.get("cn") or product_info.get("ean"),
            "reason": "stock_level_1",
            "stock_level": product_info.get("own_stock"),
            "message": f"Producto con stock = 1 requiere intervención humana"
        }
        
        # Log a archivo
        with open("./logs/human_factor_alerts.log", "a", encoding="utf-8") as f:
            f.write(f"{alert_data}\n")
        
        self.logger.warning(f"Alerta factor humano: {alert_data}")
    
    def _compile_order_data_for_excel(self, order: Dict, product_info: Dict, completion_type: str) -> List:
        """Compilar datos del pedido para Excel"""
        return [
            datetime.now(),
            order.get("id", ""),
            order.get("quantity", 0),
            product_info.get("ean", ""),
            product_info.get("cn", ""),
            product_info.get("description", ""),
            completion_type,
            product_info.get("final_supplier", ""),
            product_info.get("final_price", ""),
            "Procesado automáticamente"
        ]
    
    def _print_order_documents(self, order: Dict, product_info: Dict) -> Dict:
        """Imprimir documentos del pedido"""
        try:
            # Preparar datos para etiqueta
            label_data = {
                "code": product_info.get("cn") or product_info.get("ean"),
                "name": product_info.get("description", ""),
                "quantity": order.get("quantity", 1),
                "supplier": product_info.get("final_supplier", ""),
                "date": datetime.now().strftime("%d/%m/%Y")
            }
            
            # Imprimir etiqueta
            print_result = self.automation_manager.printer_manager.print_promofarma_label(label_data)
            
            return print_result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_trace_status(self, trace_id: str) -> Optional[Dict]:
        """Obtener estado de una traza"""
        return self.active_traces.get(trace_id)
    
    def get_all_active_traces(self) -> Dict:
        """Obtener todas las trazas activas"""
        return self.active_traces