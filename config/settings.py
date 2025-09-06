import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Configuración del servidor
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Configuración de base de datos
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./autofarma.db")
    
    # Configuración de Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Configuración de seguridad
    SECRET_KEY = os.getenv("SECRET_KEY", "tu-clave-secreta-muy-segura")
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Configuración de automatización
    SELENIUM_TIMEOUT = 10
    PYAUTOGUI_PAUSE = 0.5
    
    # Configuración de Excel
    EXCEL_OUTPUT_DIR = os.getenv("EXCEL_OUTPUT_DIR", "./output")
    
    # Configuración de impresora
    DEFAULT_PRINTER = os.getenv("DEFAULT_PRINTER", None)

settings = Settings()