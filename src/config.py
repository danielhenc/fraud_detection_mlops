"""
Configuración centralizada para la API de detección de fraude.
Variables de entorno y configuraciones para diferentes entornos.
"""
import os
from typing import Optional

class Config:
    """Configuración base de la aplicación."""
    
    # Configuración del servidor
    API_PORT: int = int(os.environ.get("PORT", 8000))
    API_HOST: str = os.environ.get("HOST", "0.0.0.0")
    
    # Configuración del entorno
    ENV: str = os.environ.get("ENV", "development")
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"
    
    # Rutas de archivos
    MODEL_PATH: str = os.environ.get("MODEL_PATH", "models/fraud_model.joblib")
    METADATA_PATH: str = os.environ.get("METADATA_PATH", "models/model_metadata.json")
    DATA_PATH: str = os.environ.get("DATA_PATH", "data/fraud_data_processed.csv")
    LOGS_DIR: str = os.environ.get("LOGS_DIR", "logs")
    
    # Configuración del model watcher
    ENABLE_MODEL_WATCHER: bool = os.environ.get("ENABLE_MODEL_WATCHER", "true").lower() == "true"
    WATCHER_INTERVAL: int = int(os.environ.get("WATCHER_INTERVAL", 30))
    
    # Configuración de la API
    API_TITLE: str = "Fraud Detection API"
    API_DESCRIPTION: str = "API para detección de fraude en transacciones bancarias"
    API_VERSION: str = "1.0.0"
    
    # Configuración de CORS (si es necesario)
    ALLOWED_ORIGINS: list = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    
    # Configuración de logging
    @property
    def log_config(self) -> dict:
        """Configuración de logging basada en el entorno."""
        if self.ENV == "production":
            return {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    },
                    "json": {
                        "format": '{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
                    },
                },
                "handlers": {
                    "default": {
                        "formatter": "json" if self.ENV == "production" else "default",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    },
                },
                "root": {
                    "level": self.LOG_LEVEL,
                    "handlers": ["default"],
                },
            }
        else:
            return {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    },
                },
                "handlers": {
                    "default": {
                        "formatter": "default",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    },
                },
                "root": {
                    "level": self.LOG_LEVEL,
                    "handlers": ["default"],
                },
            }
    
    @classmethod
    def is_production(cls) -> bool:
        """Verifica si estamos en entorno de producción."""
        return cls().ENV.lower() == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """Verifica si estamos en entorno de desarrollo."""
        return cls().ENV.lower() == "development"

# Instancia global de configuración
config = Config()