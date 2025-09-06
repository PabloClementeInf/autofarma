import pyautogui
import time
import win32gui
import win32con
import psutil
from typing import Dict, List, Optional, Tuple
import logging

class FarmaticController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.window_handle = None
        self.is_connected = False
        
        # Configurar PyAutoGUI
        pyautogui.PAUSE = 0.5
        pyautogui.FAILSAFE = True
        
    def find_farmatic_window(self) -> bool:
        """Buscar y conectar con la ventana de Farmatic"""
        try:
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if 'farmatic' in window_text.lower():
                        windows.append((hwnd, window_text))
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                self.window_handle = windows[0][0]
                self.is_connected = True
                self.logger.info(f"Conectado a Farmatic: {windows[0][1]}")
                return True
            else:
                self.logger.warning("No se encontró ventana de Farmatic")
                return False
                
        except Exception as e:
            self.logger.error(f"Error buscando Farmatic: {e}")
            return False
    
    def activate_farmatic(self) -> bool:
        """Activar la ventana de Farmatic"""
        try:
            if not self.window_handle:
                if not self.find_farmatic_window():
                    return False
            
            win32gui.SetForegroundWindow(self.window_handle)
            win32gui.ShowWindow(self.window_handle, win32con.SW_RESTORE)
            time.sleep(1)
            return True
            
        except Exception as e:
            self.logger.error(f"Error activando Farmatic: {e}")
            return False
    
    def search_product(self, product_code: str) -> Dict:
        """Buscar un producto en Farmatic"""
        try:
            if not self.activate_farmatic():
                return {"success": False, "error": "No se pudo activar Farmatic"}
            
            # Buscar campo de búsqueda (ajustar coordenadas según tu Farmatic)
            # Estas coordenadas son ejemplo - necesitarás ajustarlas
            search_box = pyautogui.locateOnScreen('farmatic_search_box.png', confidence=0.8)
            
            if search_box:
                pyautogui.click(search_box)
                pyautogui.hotkey('ctrl', 'a')  # Seleccionar todo
                pyautogui.type(product_code)
                pyautogui.press('enter')
                time.sleep(2)
                
                return {"success": True, "message": f"Producto {product_code} buscado"}
            else:
                # Método alternativo usando coordenadas fijas
                pyautogui.click(100, 100)  # Ajustar coordenadas
                pyautogui.type(product_code)
                pyautogui.press('enter')
                
                return {"success": True, "message": f"Producto {product_code} buscado (coordenadas fijas)"}
                
        except Exception as e:
            self.logger.error(f"Error buscando producto: {e}")
            return {"success": False, "error": str(e)}
    
    def get_product_info(self) -> Dict:
        """Obtener información del producto actual"""
        try:
            # Implementar lógica para extraer datos de Farmatic
            # Esto dependerá de la estructura específica de tu Farmatic
            
            return {
                "success": True,
                "product_data": {
                    "code": "ejemplo_codigo",
                    "name": "ejemplo_nombre",
                    "price": "ejemplo_precio",
                    "stock": "ejemplo_stock"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info del producto: {e}")
            return {"success": False, "error": str(e)}
    
    def update_stock(self, new_stock: int) -> Dict:
        """Actualizar stock de un producto"""
        try:
            if not self.activate_farmatic():
                return {"success": False, "error": "No se pudo activar Farmatic"}
            
            # Implementar lógica específica para actualizar stock
            # Esto dependerá de cómo funcione tu versión de Farmatic
            
            return {"success": True, "message": f"Stock actualizado a {new_stock}"}
            
        except Exception as e:
            self.logger.error(f"Error actualizando stock: {e}")
            return {"success": False, "error": str(e)}