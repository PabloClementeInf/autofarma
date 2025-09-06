import win32print
import win32ui
import win32con
import win32api
from PIL import Image, ImageDraw, ImageFont
import os
import logging
from typing import Dict, List, Optional

class PrinterManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_printer = None
        self.setup_default_printer()
        
    def setup_default_printer(self):
        """Configurar impresora por defecto"""
        try:
            self.default_printer = win32print.GetDefaultPrinter()
            self.logger.info(f"Impresora por defecto: {self.default_printer}")
        except Exception as e:
            self.logger.error(f"Error obteniendo impresora por defecto: {e}")
    
    def is_ready(self) -> bool:
        """Verificar si el manager está listo"""
        return self.default_printer is not None
    
    def get_available_printers(self) -> List[str]:
        """Obtener lista de impresoras disponibles"""
        try:
            printers = []
            for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL):
                printers.append(printer[2])
            return printers
        except Exception as e:
            self.logger.error(f"Error obteniendo impresoras: {e}")
            return []
    
    def print_promofarma_label(self, label_data: Dict, printer_name: str = None) -> Dict:
        """Imprimir etiqueta de Promofarma"""
        try:
            if not printer_name:
                printer_name = self.default_printer
            
            # Crear imagen de etiqueta
            label_image = self._create_label_image(label_data)
            
            # Imprimir imagen
            result = self._print_image(label_image, printer_name, "Etiqueta_Promofarma")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error imprimiendo etiqueta Promofarma: {e}")
            return {"success": False, "error": str(e)}
    
    def print_albaran(self, albaran_data: Dict, printer_name: str = None) -> Dict:
        """Imprimir albarán"""
        try:
            if not printer_name:
                printer_name = self.default_printer
            
            # Crear documento de albarán
            albaran_content = self._create_albaran_content(albaran_data)
            
            # Imprimir documento
            result = self._print_text_document(albaran_content, printer_name, "Albaran")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error imprimiendo albarán: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_label_image(self, label_data: Dict) -> Image.Image:
        """Crear imagen de etiqueta"""
        # Configuración de etiqueta (ajustar según necesidades)
        width, height = 400, 200
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            # Fuente (usar fuente del sistema)
            font_large = ImageFont.truetype("arial.ttf", 16)
            font_medium = ImageFont.truetype("arial.ttf", 12)
            font_small = ImageFont.truetype("arial.ttf", 10)
        except:
            # Fallback a fuente por defecto
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Dibujar contenido de etiqueta
        y_position = 10
        
        # Código del producto
        if 'code' in label_data:
            draw.text((10, y_position), f"Código: {label_data['code']}", fill='black', font=font_large)
            y_position += 25
        
        # Nombre del producto
        if 'name' in label_data:
            draw.text((10, y_position), f"Producto: {label_data['name'][:30]}", fill='black', font=font_medium)
            y_position += 20
        
        # Precio
        if 'price' in label_data:
            draw.text((10, y_position), f"Precio: {label_data['price']} €", fill='black', font=font_medium)
            y_position += 20
        
        # Fecha
        if 'date' in label_data:
            draw.text((10, y_position), f"Fecha: {label_data['date']}", fill='black', font=font_small)
        
        return img
    
    def _create_albaran_content(self, albaran_data: Dict) -> str:
        """Crear contenido del albarán"""
        content = []
        content.append("=" * 50)
        content.append("ALBARÁN DE ENTREGA")
        content.append("=" * 50)
        content.append("")
        
        # Información del albarán
        if 'number' in albaran_data:
            content.append(f"Número de Albarán: {albaran_data['number']}")
        
        if 'date' in albaran_data:
            content.append(f"Fecha: {albaran_data['date']}")
        
        if 'supplier' in albaran_data:
            content.append(f"Proveedor: {albaran_data['supplier']}")
        
        content.append("")
        content.append("-" * 50)
        content.append("PRODUCTOS")
        content.append("-" * 50)
        
        # Productos
        if 'products' in albaran_data:
            for product in albaran_data['products']:
                line = f"{product.get('code', '')} - {product.get('name', '')[:20]} - Cant: {product.get('quantity', 0)}"
                content.append(line)
        
        content.append("")
        content.append("=" * 50)
        
        return "\n".join(content)
    
    def _print_image(self, image: Image.Image, printer_name: str, job_name: str) -> Dict:
        """Imprimir imagen"""
        try:
            # Guardar imagen temporalmente
            temp_file = f"temp_label_{job_name}.bmp"
            image.save(temp_file, "BMP")
            
            # Imprimir usando win32api
            win32api.ShellExecute(0, "print", temp_file, f'/d:"{printer_name}"', ".", 0)
            
            # Limpiar archivo temporal
            try:
                os.remove(temp_file)
            except:
                pass
            
            return {"success": True, "message": f"Etiqueta impresa en {printer_name}"}
            
        except Exception as e:
            self.logger.error(f"Error imprimiendo imagen: {e}")
            return {"success": False, "error": str(e)}
    
    def _print_text_document(self, content: str, printer_name: str, job_name: str) -> Dict:
        """Imprimir documento de texto"""
        try:
            # Crear archivo temporal
            temp_file = f"temp_{job_name}.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Imprimir archivo
            win32api.ShellExecute(0, "print", temp_file, f'/d:"{printer_name}"', ".", 0)
            
            # Limpiar archivo temporal
            try:
                os.remove(temp_file)
            except:
                pass
            
            return {"success": True, "message": f"Documento impreso en {printer_name}"}
            
        except Exception as e:
            self.logger.error(f"Error imprimiendo documento: {e}")
            return {"success": False, "error": str(e)}